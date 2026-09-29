"""Motion Engine — Deterministic 3D Motion Graphics & Procedural Audio Engine."""

__version__ = "1.1.0"

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
    export_pcm_wav,
    note_to_freq
)
from .pipeline import (
    FFmpegStreamer,
    find_ffmpeg_binary
)
from .geometry import (
    create_primitive,
    mesh_to_vbo_bytes,
    load_mesh_asset
)
from .noise import (
    ProceduralNoise
)
from .dsp import (
    butter_filter,
    convolution_reverb
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
    "note_to_freq",
    "FFmpegStreamer",
    "find_ffmpeg_binary",
    "create_primitive",
    "mesh_to_vbo_bytes",
    "load_mesh_asset",
    "ProceduralNoise",
    "butter_filter",
    "convolution_reverb"
]
