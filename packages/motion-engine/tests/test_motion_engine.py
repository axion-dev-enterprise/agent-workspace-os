"""Unit Tests for Motion Engine package (v1.1.0)."""
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np

from motion_engine.math3d import (
    ease,
    normal,
    look_at,
    perspective,
    ortho,
    rotation_matrix,
    create_instance_buffer
)
from motion_engine.audio import (
    ProceduralAudioEngine,
    sub_bass_drop,
    cinematic_riser,
    metallic_click,
    ambient_drone,
    export_pcm_wav
)
from motion_engine.pipeline import find_ffmpeg_binary
from motion_engine.geometry import create_primitive, mesh_to_vbo_bytes
from motion_engine.noise import ProceduralNoise
from motion_engine.dsp import butter_filter, convolution_reverb


def test_ease_smoothstep():
    assert ease(0.0, 1.0, -0.5) == 0.0
    assert ease(0.0, 1.0, 1.5) == 1.0
    assert ease(0.0, 1.0, 0.5) == 0.5
    v1 = ease(1.0, 5.0, 2.0)
    v2 = ease(1.0, 5.0, 3.0)
    assert 0.0 < v1 < v2 < 1.0


def test_math3d_matrices():
    n = normal([3.0, 0.0, 4.0])
    assert np.allclose(np.linalg.norm(n), 1.0)
    assert np.allclose(n, [0.6, 0.0, 0.8])

    view = look_at([0, 0, 5], [0, 0, 0], [0, 1, 0])
    assert view.shape == (4, 4)

    proj = perspective(16.0 / 9.0, fov=45.0)
    assert proj.shape == (4, 4)
    assert proj[3, 2] == -1.0

    inst = create_instance_buffer([1, 2, 3], [1, 1, 1], [0.5, 0.5, 0.5], 0.2)
    assert len(inst) == 20
    assert inst.dtype == np.float32


def test_procedural_audio_recipes():
    sr = 48000
    bass = sub_bass_drop(duration=0.5, sample_rate=sr)
    assert len(bass) == int(0.5 * sr)
    assert np.max(np.abs(bass)) <= 1.0

    riser = cinematic_riser(duration=0.5, sample_rate=sr)
    assert len(riser) == int(0.5 * sr)

    click = metallic_click(duration=0.05, sample_rate=sr)
    assert len(click) == int(0.05 * sr)

    drone = ambient_drone(duration=1.0, sample_rate=sr)
    assert drone.shape == (int(1.0 * sr), 2)


def test_audio_engine_composite_export(tmp_path: Path):
    engine = ProceduralAudioEngine(duration=1.0, sample_rate=48000, seed=12345)
    bass = sub_bass_drop(duration=0.5, sample_rate=48000)
    engine.add_sound(bass, start_time=0.0, gain=0.8, pan=-0.5)

    click = metallic_click(duration=0.05, sample_rate=48000)
    engine.add_sound(click, start_time=0.4, gain=0.6, pan=0.5)

    out_file = tmp_path / "test_export.wav"
    engine.export(out_file)

    assert out_file.is_file()
    assert out_file.stat().st_size > 1000


def test_ffmpeg_binary_detection():
    bin_path = find_ffmpeg_binary()
    assert bin_path.is_file()
    assert "ffmpeg" in bin_path.name.lower()


def test_geometry_primitive_generation():
    # Icosphere
    mesh = create_primitive("icosphere", subdivisions=2, radius=1.5)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0

    vbo_bytes = mesh_to_vbo_bytes(mesh)
    assert len(vbo_bytes) > 0
    # Check that byte size matches 6 floats (pos + norm) per vertex in triangles
    expected_floats = len(mesh.faces) * 3 * 6
    assert len(vbo_bytes) == expected_floats * 4

    # Torus
    torus = create_primitive("torus", major_radius=2.0, minor_radius=0.5)
    assert len(torus.vertices) > 0


def test_procedural_noise():
    pnoise = ProceduralNoise(seed=42)
    val2d = pnoise.noise2d(1.5, 2.5)
    assert -1.0 <= val2d <= 1.0

    val_fbm = pnoise.fbm3d(0.5, 0.5, 0.5, octaves=3)
    assert -1.5 <= val_fbm <= 1.5

    # Vertex displacement
    verts = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    disp = pnoise.displace_vertices_3d(verts, time=1.0, freq=1.0, strength=0.2)
    assert disp.shape == verts.shape
    assert not np.allclose(disp, verts)


def test_dsp_filtering_and_reverb():
    sr = 48000
    t = np.linspace(0, 0.5, int(0.5 * sr), endpoint=False)
    # 1000 Hz tone
    raw_tone = np.sin(2.0 * np.pi * 1000.0 * t)

    # Filter with 500 Hz lowpass
    filtered = butter_filter(raw_tone, cutoff_hz=500.0, fs=sr, btype="low")
    assert len(filtered) == len(raw_tone)
    # The 1000 Hz tone should be heavily attenuated
    assert np.max(np.abs(filtered)) < np.max(np.abs(raw_tone)) * 0.3

    # Reverb
    reverbed = convolution_reverb(raw_tone, decay_seconds=0.4, fs=sr, wet_mix=0.3)
    assert reverbed.shape == (len(raw_tone), 2)
