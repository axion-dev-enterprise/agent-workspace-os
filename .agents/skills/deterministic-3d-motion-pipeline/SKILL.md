---
name: deterministic-3d-motion-pipeline
description: >-
  Arquitetura de produção para geração determinística de motion graphics e filmes 3D nativos.
  Cobre renderização headless via ModernGL/OpenGL (sem browser ou nuvem), síntese sonora
  procedural em NumPy (sem samples externos), streaming de frames brutos via pipe FFmpeg
  (H.264 BT.709 + AAC) e companion preview em HTML5/CSS 3D.
---

# Deterministic 3D Motion Pipeline — Manual Operacional de Arquitetura

Esta skill estabelece a arquitetura canônica para criação, animação, sonorização e renderização determinística de motion graphics institucionais e comerciais de alta fidelidade, operando de forma 100% autônoma no host local sem dependência de navegadores, serviços de nuvem ou licenças de terceiros.

---

## 1. Topologia da Arquitetura

O pipeline é composto por quatro camadas desacopladas que garantem reprodutibilidade exata (pixel-perfect e sample-accurate):

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DETERMINISTIC 3D MOTION PIPELINE                     │
└────────────────────────────────────────────────────────────────────────┘
        │                                                │
        ▼                                                ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     CAMADA 1: MOTOR 3D        │        │   CAMADA 2: SÍNTESE SONORA    │
│  • ModernGL Standalone Context │        │  • Síntese Aditiva em NumPy   │
│  • Instanced Beveled Geometry │        │  • Deterministic PRNG Seed    │
│  • GGX Metallic & Environment │        │  • Harmonic Pitch Math (MIDI) │
│  • PCF Shadow Map (2048px)    │        │  • Analytical Sin² Envelopes  │
│  • 4x MSAA + ACES Tone Map    │        │  • Peak Ceiling (-1.5 dBFS)   │
└───────────────────────────────┘        └───────────────────────────────┘
        │ (Raw RGB bytes pipe)                           │ (Stereo PCM WAV)
        └───────────────────────┬────────────────────────┘
                                ▼
        ┌────────────────────────────────────────────────┐
        │        CAMADA 3: STREAMING ENCODER             │
        │  • FFmpeg Stdin Pipe (Zero-Disk Intermediate)  │
        │  • H.264 BT.709 yuv420p + AAC Stereo Mux      │
        │  • FastStart Header para Web/Mobile Streaming  │
        └────────────────────────────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │            CAMADA 4: ARTEFATOS                 │
        │  • MP4 Master Final (Vertical 9:16 ou 16:9)    │
        │  • Keyframes PNG de Inspeção                   │
        │  • JSON Manifest de Auditoria Técnica          │
        │  • HTML5/CSS 3D Companion de Preview Ágil      │
        └────────────────────────────────────────────────┘
```

---

## 2. Padrões de Cada Camada

### 2.1 Camada 1: Motor Gráfico 3D Headless (ModernGL / OpenGL)
- **Contexto Standalone**: Inicializar via `moderngl.create_context(standalone=True)`. Permite rodar em background, processos agendados ou CLI sem janelas físicas.
- **Geometria Paramétrica**: Utilizar geradores de malha procedurais com chanfros suaves (*beveled cubes*, cilindros filetados, toros) com normais por vértice e tangentes pré-calculadas.
- **Instanciamento em Massa**: Para múltiplos módulos geométricos, empacotar matrizes de transformação $4 \times 4$, cores RGB e coeficientes de rugosidade (*roughness*) em buffers de instâncias VBO (`ctx.buffer(data)` com `per_instance=True`).
- **Pipeline de Iluminação e Sombras**:
  1. *Passo 1 (Shadow Map)*: Render offscreen da profundidade a partir da perspectiva da luz direcional em FBO de 2048×2048 com depth buffer float.
  2. *Passo 2 (Shading GGX & PCF)*: Shading com distribuição GGX/Trowbridge-Reitz, fresnel Schlick, reflexão com mapa de ambiente sintético (*procedural studio HDRI*) e filtragem suave PCF 3×3.
  3. *Passo 3 (Pós-Processamento HDR)*: FBO com textura flutuante `f2`/`f4`, multisampling 4× MSAA blitted, ACES filmic tone mapping, vinheta sutil e aberração cromática controlada.
- **Curvas de Movimento**: Toda cinemática depende estritamente do tempo global $t$. Usar interpolação quintica suave (*smoothstep* de 5ª ordem):
  $$\text{ease}(s, e, t) = x^3 \cdot (x \cdot (6x - 15) + 10) \quad \text{onde } x = \text{clamp}\left(\frac{t - s}{e - s}, 0, 1\right)$$

### 2.2 Camada 2: Síntese Sonora Procedural (Pure NumPy)
- **Seed Determinística**: Inicializar `rng = np.random.default_rng(SEED)` com semente fixa. O áudio resultante é idêntico bit-a-bit em qualquer execução.
- **Afinação Matemática (MIDI para Hertz)**:
  $$f(\text{midi}) = 440 \cdot 2^{\frac{\text{midi} - 69}{12}}$$
- **Envelopes Analíticos**: Usar curvas suaves livres de estalos (*clicks* de fase) com rampas de seno ao quadrado:
  $$\text{env}(t) = \sin^2\left(\frac{t}{\text{attack}} \cdot \frac{\pi}{2}\right) \cdot \sin^2\left(\frac{T - t}{\text{release}} \cdot \frac{\pi}{2}\right)$$
- **Mixagem Estéreo e Espacialização**:
  - Panorâmica de potência constante (*equal-power panning*): $\cos(\theta)$ no canal esquerdo e $\sin(\theta)$ no canal direito.
  - Reflexões estéreo (micro-delay Haas) para sensação de amplitude tridimensional.
  - Teto de ganho (*true peak*): sample peaks rigorosamente contidos abaixo de $-1.5\text{ dBFS}$ antes do encoding PCM 16-bit / 48 kHz.

### 2.3 Camada 3: Streaming Pipe FFmpeg (Zero-Disk Intermediary)
- **Proibição de Sequência PNG em Disco**: É proibido salvar centenas de frames individuais no disco antes de encodificar. O motor gráfico deve escrever os bytes brutos (`rawvideo rgb24`) diretamente no `stdin` do subprocesso FFmpeg:
  ```python
  command = [
      str(FFMPEG), '-hide_banner', '-loglevel', 'warning', '-nostdin', '-y',
      '-f', 'rawvideo', '-pixel_format', 'rgb24',
      '-video_size', f'{width}x{height}', '-framerate', str(FPS),
      '-i', 'pipe:0',
      '-i', str(audio_path),
      '-vf', 'vflip',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
      '-pix_fmt', 'yuv420p',
      '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
      '-c:a', 'aac', '-b:a', '192k',
      '-movflags', '+faststart', '-shortest', str(output_mp4)
  ]
  ```
- **Robustez de Processo**:
  - Tratar exceções garantindo o fechamento de `proc.stdin` e `proc.wait(timeout=10)` em blocos `finally`.
  - Liberar explicitamente o contexto ModernGL (`ctx.release()`).

### 2.4 Camada 4: Companion Preview Web (HTML5 / CSS 3D)
- Sempre fornecer um arquivo [index.html](file:///C:/workspace/temp/axion-motion/index.html) pareado com a estética do filme:
  - Formato vertical nativo (`aspect-ratio: 9 / 16; width: min(100vw, 430px)`).
  - Animação em CSS puro baseada em `@keyframes` espelhando a timeline cronológica do filme.
  - Botão de controle Play/Pause via JavaScript acessível.
  - Suporte estrito a `@media (prefers-reduced-motion: reduce)` exibindo os elementos de marca de forma estável.

---

## 3. Fluxo de Trabalho Operacional (PEV)

1. **Investigação & Pre-flight**:
   - Verificar presença do binário do FFmpeg no sistema.
   - Verificar aceleração OpenGL do host via probe ModernGL rápido.
2. **Execução em Modo Preview**:
   - Rodar sempre a flag `--preview` primeiro.
   - Gera 5 keyframes (`0.8s`, `3.8s`, `6.8s`, `10.4s`, `14.0s`) em menos de 2 segundos.
   - Permite auditar enquadramento de câmera, escala e iluminação sem custo de render integral.
3. **Renderização do Master**:
   - Sintetizar a trilha sonora determinística em WAV.
   - Disparar o render completo via pipe FFmpeg.
   - Gravar relatório técnico `render-report.json` documentando resolução, duração, fps, tempo de render e técnicas.
4. **Verificação Empírica**:
   - Inspecionar a integridade do `.mp4` gerado (tamanho > 0, duração correta).
   - Validar ausência de saturação no áudio `.wav`.

---

## 4. Diretrizes de Governança e Limpeza
- **Arquivos Intermediários**: Logs e frames efêmeros pertencem estritamente a pastas descartáveis em `output/` ou `temp/`.
- **Licenciamento & Soberania**: Zero dependência de serviços externos, CDNs ou APIs pagas de IA generativa de vídeo. A infraestrutura é auto-suficiente no hardware local.
- **Portabilidade**: Shaders em GLSL 330 core / ES 3.0 garantem compatibilidade imediata entre GPUs dedicadas (AMD/NVIDIA/Intel) e drivers WGL/EGL.

---

## 5. Toolkit de Ferramentas Avançadas (`packages/motion-engine`)
- **Geometria & Malhas (`motion_engine.geometry`)**: Primitivas procedurais de alta definição (`create_primitive`) via `Trimesh` e suporte a carregamento de ativos externos (`load_mesh_asset`).
- **Ruído Procedural (`motion_engine.noise`)**: OpenSimplex com síntese multi-escala fBm para deslocamento orgânico e animação contínua de superfícies no espaço 4D ($x, y, z, t$).
- **Processamento de Sinal Digital (`motion_engine.dsp`)**: Filtros IIR Butterworth com varredura de corte via `scipy.signal` e convolução de impulso estéreo para acústica realista de sala.

