"""Motion Engine — Deterministic 3D Motion Graphics & Procedural Audio Engine."""

__version__ = "1.0.0"

from .math3d import (
    ease,
    normal,
    look_at,
    perspective,
    ortho,
    rotation_matrix,
    create_instance_buffer
)
from .audio import (
    ProceduralAudioEngine,
    sub_bass_drop,
    cinematic_riser,
    metallic_click,
    ambient_drone,
    export_pcm_wav
)
from .pipeline import (
    FFmpegStreamer,
    find_ffmpeg_binary
)

__all__ = [
    "ease",
    "normal",
    "look_at",
    "perspective",
    "ortho",
    "rotation_matrix",
    "create_instance_buffer",
    "ProceduralAudioEngine",
    "sub_bass_drop",
    "cinematic_riser",
    "metallic_click",
    "ambient_drone",
    "export_pcm_wav",
    "FFmpegStreamer",
    "find_ffmpeg_binary"
]
