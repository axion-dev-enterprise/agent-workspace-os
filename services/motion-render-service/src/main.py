"""FastAPI Daemon & REST API for Motion Render Service."""
from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Optional
import sys

# Add packages/motion-engine and local src to path
SERVICE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path("C:/workspace")
sys.path.insert(0, str(WORKSPACE_ROOT / "packages" / "motion-engine" / "src"))
sys.path.insert(0, str(SERVICE_ROOT / "src"))

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from motion_engine.audio import ProceduralAudioEngine, sub_bass_drop, cinematic_riser, metallic_click, ambient_drone, note_to_freq
from motion_engine.pipeline import find_ffmpeg_binary
from engine import ServiceFilmRenderer
from scenes import SCENE_REGISTRY

app = FastAPI(
    title="AXION Motion Render Service",
    description="High-performance deterministic 3D motion graphics and procedural audio rendering service.",
    version="1.0.0"
)

STATIC_DIR = SERVICE_ROOT / "src" / "static"
OUTPUT_DIR = SERVICE_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory render job state
current_job: dict[str, Any] = {
    "status": "idle",
    "progress": 0.0,
    "current_frame": 0,
    "total_frames": 0,
    "elapsed_seconds": 0.0,
    "last_result": None,
    "error": None
}


class RenderRequest(BaseModel):
    scene_id: str = Field(default="autonomous-core", description="Scene identifier")
    width: int = Field(default=1080, ge=360, le=3840)
    height: int = Field(default=1920, ge=360, le=3840)
    duration: float = Field(default=15.0, ge=1.0, le=60.0)
    fps: int = Field(default=30, ge=24, le=60)
    crf: int = Field(default=17, ge=10, le=28)


class PreviewRequest(BaseModel):
    scene_id: str = Field(default="autonomous-core")
    width: int = Field(default=1080)
    height: int = Field(default=1920)
    timestamps: list[float] = Field(default=[0.8, 3.8, 6.8, 10.4, 14.0])


def synthesize_score_for_scene(output_path: Path, duration: float = 15.0) -> Path:
    sample_rate = 48000
    engine = ProceduralAudioEngine(duration=duration, sample_rate=sample_rate, seed=260926)

    # Ambient Drone
    drone = ambient_drone(duration=duration, sample_rate=sample_rate, base_midi=36.0)
    engine.add_sound(drone, start_time=0.0, gain=0.45)

    # Sub-Bass Drop
    bass = sub_bass_drop(duration=min(3.2, duration), sample_rate=sample_rate, f_start=135.0, f_end=34.0, decay=3.8)
    engine.add_sound(bass, start_time=0.0, gain=0.90)

    # Metallic Clicks
    for t_click, p in [(1.0, -0.4), (2.0, 0.4), (3.0, 0.0)]:
        if t_click < duration:
            click = metallic_click(duration=0.06, sample_rate=sample_rate, fc=2200.0, fm=600.0, mod_index=3.0, tau=0.015)
            engine.add_sound(click, start_time=t_click, gain=0.35, pan=p)

    # Chords
    for start_t, midi_note, pan_pos in [(3.4, 48.0, -0.5), (4.4, 51.0, 0.5), (5.4, 55.0, -0.3), (6.4, 58.0, 0.3), (7.2, 60.0, 0.0)]:
        if start_t < duration:
            freq = note_to_freq(midi_note)
            note_dur = min(3.5, duration - start_t)
            t_arr = np.linspace(0, note_dur, int(note_dur * sample_rate), endpoint=False)
            synth_wave = np.sin(2.0 * np.pi * freq * t_arr) + 0.3 * np.sin(2.0 * np.pi * (freq * 2.0) * t_arr)
            engine.add_sound(synth_wave / 1.3, start_time=start_t, gain=0.40, pan=pan_pos)

    # Riser
    if duration > 8.0:
        riser_len = min(3.9, duration - 8.0)
        riser = cinematic_riser(duration=riser_len, sample_rate=sample_rate, f_start=70.0, f_end=920.0)
        engine.add_sound(riser, start_time=8.0, gain=0.75)

    # Impact
    if duration > 11.9:
        impact = sub_bass_drop(duration=duration - 11.9, sample_rate=sample_rate, f_start=110.0, f_end=30.0, decay=2.5)
        engine.add_sound(impact, start_time=11.9, gain=0.95)

    engine.export(output_path, target_dbfs=-1.5)
    return output_path


def run_full_render_job(req: RenderRequest):
    global current_job
    current_job["status"] = "rendering"
    current_job["error"] = None
    current_job["progress"] = 0.0
    start = time.monotonic()

    try:
        ffmpeg_bin = find_ffmpeg_binary()
        audio_path = OUTPUT_DIR / f"{req.scene_id}-score.wav"
        synthesize_score_for_scene(audio_path, req.duration)

        movie_name = f"{req.scene_id}-{int(time.time())}.mp4"
        movie_path = OUTPUT_DIR / movie_name
        log_path = OUTPUT_DIR / "service_encode.log"

        total_frames = round(req.duration * req.fps)
        current_job["total_frames"] = total_frames

        film = ServiceFilmRenderer(req.width, req.height, req.scene_id)

        command = [
            str(ffmpeg_bin),
            "-hide_banner",
            "-loglevel", "warning",
            "-nostdin",
            "-y",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{req.width}x{req.height}",
            "-framerate", str(req.fps),
            "-i", "pipe:0",
            "-i", str(audio_path),
            "-vf", "vflip",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(req.crf),
            "-threads", "3",
            "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-colorspace", "bt709",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(movie_path)
        ]

        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        with log_path.open("wb") as log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log, creationflags=flags)
            try:
                for i in range(total_frames):
                    raw = film.render_frame(i / req.fps)
                    proc.stdin.write(raw)
                    current_job["current_frame"] = i + 1
                    current_job["progress"] = round(((i + 1) / total_frames) * 100.0, 1)
                    current_job["elapsed_seconds"] = round(time.monotonic() - start, 1)

                proc.stdin.close()
                if proc.wait(timeout=120) != 0:
                    raise RuntimeError("FFmpeg encoding failed.")
            finally:
                film.close()

        render_seconds = round(time.monotonic() - start, 2)
        result = {
            "file": movie_name,
            "path": str(movie_path),
            "size_bytes": movie_path.stat().st_size,
            "width": req.width,
            "height": req.height,
            "fps": req.fps,
            "duration": req.duration,
            "render_seconds": render_seconds,
            "completed_at": datetime.now().isoformat()
        }
        current_job["status"] = "completed"
        current_job["last_result"] = result
        (OUTPUT_DIR / "last_render.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    except Exception as e:
        current_job["status"] = "failed"
        current_job["error"] = str(e)


@app.get("/", response_class=HTMLResponse)
def index_studio():
    """Serves the web companion & studio UI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>AXION Motion Render Service is Running.</h2>")


@app.get("/health")
def health_check():
    ffmpeg_detected = False
    try:
        find_ffmpeg_binary()
        ffmpeg_detected = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "motion-render-service",
        "ffmpeg_detected": ffmpeg_detected,
        "available_scenes": list(SCENE_REGISTRY.keys()),
        "output_directory": str(OUTPUT_DIR)
    }


@app.get("/scenes")
def list_scenes():
    return [
        {"id": k, "title": v["title"], "default_duration": v["duration"], "fps": v["fps"]}
        for k, v in SCENE_REGISTRY.items()
    ]


@app.get("/videos")
def list_videos():
    files = []
    for item in OUTPUT_DIR.glob("*.mp4"):
        stat = item.stat()
        files.append({
            "name": item.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


@app.get("/videos/{filename}")
def download_video(filename: str):
    # Prevent path traversal
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")
    media_type = "video/mp4" if safe_name.endswith(".mp4") else "audio/wav"
    return FileResponse(file_path, media_type=media_type, filename=safe_name)


@app.post("/render")
def trigger_render(req: RenderRequest, bg_tasks: BackgroundTasks):
    global current_job
    if current_job["status"] == "rendering":
        raise HTTPException(status_code=409, detail="A render job is already in progress.")

    bg_tasks.add_task(run_full_render_job, req)
    return {"status": "enqueued", "request": req.model_dump()}


@app.get("/render/status")
def render_status():
    return current_job


@app.post("/preview")
def generate_preview_keyframes(req: PreviewRequest):
    film = ServiceFilmRenderer(req.width, req.height, req.scene_id)
    generated = []
    try:
        for t in req.timestamps:
            img = film.save_image(t)
            fname = f"preview-{req.scene_id}-{t:04.1f}.png"
            p = OUTPUT_DIR / fname
            img.save(p)
            generated.append({
                "timestamp": t,
                "file": fname,
                "url": f"/videos/{fname}"
            })
    finally:
        film.close()
    return {"scene_id": req.scene_id, "frames": generated}


if __name__ == "__main__":
    import uvicorn
    # Enforce loopback listening as per Rule #10
    uvicorn.run("main:app", host="127.0.0.1", port=8150, reload=False)
