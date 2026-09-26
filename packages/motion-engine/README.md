# Motion Engine — Pacote Canônico de Renderização 3D e Áudio Procedural

Pacote de infraestrutura para geração determinística de vídeo e áudio em Python acelerado por GPU (ModernGL / OpenGL) e síntese numérica (NumPy).

## Arquitetura do Pacote
- `motion_engine.math3d`: Cinemática paramétrica, interpolação quíntica Perlin e projeções 3D.
- `motion_engine.audio`: Síntese sonora procedural pura (sub-drops, risers, clicks FM, drones) e exportação PCM 16-bit WAV.
- `motion_engine.pipeline`: Abstração de streaming sem disco para o FFmpeg com proteção de processos.
