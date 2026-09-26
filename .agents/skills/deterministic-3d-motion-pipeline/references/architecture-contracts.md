# Architecture Contracts — Deterministic 3D Motion Pipeline

Este documento especifica os contratos de código e padrões matemáticos adotados no pipeline determinístico de renderização 3D.

---

## 1. Contrato Matemático de Cinemática & Interpolação

Toda transição cinemática no espaço $3D$ deve ser expressa em função do tempo contínuo $t \in [0, \text{DURATION}]$.

### 1.1 Smoothstep de 5ª Ordem (Perlin Quintic Easing)
Evita descontinuidades de aceleração (curvatura $C^2$ contínua):

```python
import numpy as np

def ease(start: float, end: float, value: float) -> float:
    """Interpolação quintica suave com clamp estrito entre 0 e 1."""
    x = np.clip((value - start) / (end - start), 0.0, 1.0)
    return float(x * x * x * (x * (x * 6 - 15) + 10))
```

### 1.2 Matrizes de Câmera e Transformação (OpenGL Column-Major)
```python
import math
import numpy as np

def normal(v: list[float] | np.ndarray) -> np.ndarray:
    a = np.asarray(v, dtype='f4')
    return a / np.linalg.norm(a)

def look_at(eye: list[float], target: list[float], up=(0.0, 1.0, 0.0)) -> np.ndarray:
    f = normal(np.asarray(target) - eye)
    s = normal(np.cross(f, up))
    u = np.cross(s, f)
    result = np.eye(4, dtype='f4')
    result[:3, :3] = np.array([s, u, -f])
    result[:3, 3] = -result[:3, :3] @ eye
    return result

def perspective(aspect: float, fov=36.0, near=0.1, far=100.0) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov) / 2.0)
    return np.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
        [0, 0, -1, 0]
    ], dtype='f4')
```

---

## 2. Contrato de Sombreamento GLSL

### 2.1 Passagem de Sombras (Shadow Pass)
Buffer offscreen de profundidade em alta resolução ($2048 \times 2048$):
- Projeção ortográfica ajustada ao frustum da cena.
- Front-face culling para eliminação de artefatos de *peter-panning*.

### 2.2 Iluminação GGX com PCF (Percentage-Closer Filtering)
Fragment Shader para materiais metálicos:

```glsl
#version 330 core
in vec3 v_position;
in vec3 v_normal;
in vec3 v_color;
in float v_roughness;
in vec4 v_shadow_pos;

uniform sampler2D u_shadow_map;
uniform vec3 u_light_dir;
uniform vec3 u_eye_pos;

out vec4 frag_color;

float calculate_shadow(vec4 shadow_coord) {
    vec3 proj = shadow_coord.xyz / shadow_coord.w * 0.5 + 0.5;
    if (proj.z > 1.0) return 0.0;
    float current_depth = proj.z;
    float bias = max(0.003 * (1.0 - dot(v_normal, u_light_dir)), 0.0008);
    float shadow = 0.0;
    vec2 texel_size = 1.0 / textureSize(u_shadow_map, 0);
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            float pcf_depth = texture(u_shadow_map, proj.xy + vec2(x, y) * texel_size).r;
            shadow += current_depth - bias > pcf_depth ? 1.0 : 0.0;
        }
    }
    return shadow / 9.0;
}
```

---

## 3. Contrato de Síntese Sonora (Pure NumPy)

- Geração determinística de áudio em matriz NumPy de ponto flutuante `float64` (`sample_count, 2`).
- Conclusão com conversão para PCM inteiro de 16-bits com dither ou teto em $-1.5\text{ dBFS}$:

```python
import numpy as np
import wave
from pathlib import Path

def export_pcm_wav(mix: np.ndarray, sample_rate: int, output_path: Path):
    peak = np.max(np.abs(mix))
    if peak > 0.0:
        target_ceiling = 10.0 ** (-1.5 / 20.0) # -1.5 dBFS
        if peak > target_ceiling:
            mix = mix * (target_ceiling / peak)
    pcm = np.clip(mix * 32767.0, -32768.0, 32767.0).astype(np.int16)
    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
```

---

## 4. Contrato de Streaming para FFmpeg (Sem Arquivos Temporários de Vídeo)

Conexão direta de memória RAM para processo de encoding via pipe:

```python
import subprocess
import os

def spawn_ffmpeg_stream(ffmpeg_bin: str, width: int, height: int, fps: int, audio_path: str, output_path: str):
    cmd = [
        ffmpeg_bin,
        '-hide_banner', '-loglevel', 'warning', '-nostdin', '-y',
        '-f', 'rawvideo', '-pixel_format', 'rgb24',
        '-video_size', f'{width}x{height}',
        '-framerate', str(fps),
        '-i', 'pipe:0',
        '-i', audio_path,
        '-vf', 'vflip',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
        '-pix_fmt', 'yuv420p',
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        '-shortest',
        output_path
    ]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
```
