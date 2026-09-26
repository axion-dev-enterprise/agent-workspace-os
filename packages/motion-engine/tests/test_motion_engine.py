"""Unit Tests for Motion Engine package."""
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


def test_ease_smoothstep():
    # Bounds check
    assert ease(0.0, 1.0, -0.5) == 0.0
    assert ease(0.0, 1.0, 1.5) == 1.0
    assert ease(0.0, 1.0, 0.5) == 0.5
    # Monotonicity check
    v1 = ease(1.0, 5.0, 2.0)
    v2 = ease(1.0, 5.0, 3.0)
    assert 0.0 < v1 < v2 < 1.0


def test_math3d_matrices():
    # Normal
    n = normal([3.0, 0.0, 4.0])
    assert np.allclose(np.linalg.norm(n), 1.0)
    assert np.allclose(n, [0.6, 0.0, 0.8])

    # LookAt identity / standard test
    view = look_at([0, 0, 5], [0, 0, 0], [0, 1, 0])
    assert view.shape == (4, 4)

    # Perspective
    proj = perspective(16.0 / 9.0, fov=45.0)
    assert proj.shape == (4, 4)
    assert proj[3, 2] == -1.0

    # Instance buffer
    inst = create_instance_buffer([1, 2, 3], [1, 1, 1], [0.5, 0.5, 0.5], 0.2)
    assert len(inst) == 20
    assert inst.dtype == np.float32


def test_procedural_audio_recipes():
    sr = 48000
    # Sub-bass
    bass = sub_bass_drop(duration=0.5, sample_rate=sr)
    assert len(bass) == int(0.5 * sr)
    assert np.max(np.abs(bass)) <= 1.0

    # Riser
    riser = cinematic_riser(duration=0.5, sample_rate=sr)
    assert len(riser) == int(0.5 * sr)

    # Metallic click
    click = metallic_click(duration=0.05, sample_rate=sr)
    assert len(click) == int(0.05 * sr)

    # Ambient drone
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
