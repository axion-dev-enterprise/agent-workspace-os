# Guia Canônico de Produção 3D Determinística & Motion Graphics

> **Status**: Ativo & Operacional  
> **Escopo**: Geração offline de filmes 3D nativos (ModernGL/OpenGL), síntese sonora procedural (NumPy), streaming para FFmpeg e animações companion em CSS 3D.  
> **Skill Associada**: [`deterministic-3d-motion-pipeline`](file:///C:/workspace/.agents/skills/deterministic-3d-motion-pipeline/SKILL.md)  
> **Pacote Monorepo**: [`packages/motion-engine/`](file:///C:/workspace/packages/motion-engine/)

---

## 1. Visão Geral e Filosofia Arquitetural

Este ecossistema permite que agentes e engenheiros produzam vídeos institucionais, motion graphics e peças audiovisuais comerciais de alto padrão com **zero dependência de navegadores, serviços de nuvem ou assinaturas externas de IA generativa de vídeo**.

### Princípios Fundamentais:
1. **Determinismo Absoluto**: Duas renderizações com a mesma semente matemática geram exatamente os mesmos bytes de vídeo e amostras de áudio (*pixel-perfect* e *sample-accurate*).
2. **Zero-Disk Intermediate**: Proibido despejar sequências de imagens PNG no disco antes de encodificar. Os quadros brutos em RGB24 são canalizados diretamente da memória RAM para o stdin do FFmpeg via pipe IPC de alta vazão.
3. **Áudio Procedural Matemático**: Síntese sonora gerada por equações trigonométricas analíticas em NumPy (sem depender de bibliotecas de samples pré-gravados sujeitas a direitos autorais).
4. **Governança de Recursos**: Execução limpa em hardware local com suporte acelerado por OpenGL 3.3 Core Profile e codecs industriais (H.264 BT.709 yuv420p + AAC estéreo).

---

## 2. Framework de Roteiros e Storyboard A/V

Para comerciais e vídeos de marca em formatos de alta retenção (15s a 30s nos formatos **9:16 vertical** para Reels/Shorts/Stories e **16:9 widescreen** para YouTube/Webinars), a estrutura canônica é o roteiro **Áudio/Visual (A/V)** em 4 atos matemáticos.

### 2.1 Template A/V — 15 Segundos (Alta Retenção / Tech Commercial)

| Janela Temporal | Ato | Ação Visual 3D (Câmera & Geometria) | Design Sonoro Procedural | Tipografia Sincronizada |
| :--- | :--- | :--- | :--- | :--- |
| **0.0s – 2.8s** | **The Hook** | Travelling descendente em alta aceleração. Um grid infinito de laser emerge na base enquanto partículas convergem para o centro. | *Sub-bass drop* com decaimento exponencial (120 Hz $\to$ 35 Hz) + transiente tátil. | *"O futuro não espera."* |
| **2.8s – 7.8s** | **The Mechanism** | Blocos chanfrados instanciados orbitam suavemente e se atraem magneticamente, formando um núcleo monolítico com reflexos metálicos. | Acordes menores aditivos (C-minor) gerados analiticamente + modulação estéreo suave. | *"Conectar. Criar. Evoluir."* |
| **7.8s – 11.8s** | **The Scale** | Zoom out dramático revelando a expansão modular da infraestrutura (skyline estilizado ou malha de servidores). | *Cinematic riser* com varredura exponencial de frequência gerando tensão acústica. | *"Do conceito à escala."* |
| **11.8s – 15.0s** | **Brand Lockup** | Geometria converge para a insígnia da marca. Passagem de luz rasante de estúdio (rim light) destacando as bordas chanfradas e tipografia final. | Impacto percussivo metálico via síntese FM seguido de cauda de reverb suave e fade out. | **AXION**<br>`CONSTRUA O PRÓXIMO` |

### 2.2 Template A/V — 30 Segundos (Product Narrative & Features)

- **0.0s – 5.0s (Problema / Tensão)**: Ambiente monocromático de baixa luminosidade com pulso rítmico lento. Metáfora visual de complexidade e atrito.
- **5.0s – 13.0s (Solução Modular)**: Quebra do monólito em componentes especializados. Transição de cores frias para tons ciano/azul elétrico. Câmera orbita a 60° com profundidade de campo.
- **13.0s – 22.0s (Performance & Integração)**: Demonstração cinemática dos 3 pilares de valor em cascata rápida (3 segundos cada pilar com corte seco ou aceleração quíntica).
- **22.0s – 30.0s (Ecossistema & Chamada)**: Visão macro do produto integrado, logotipo em destaque com reflexo metálico PBR, tagline e link/QR Code de conversão.

---

## 3. Presets de Shaders & Estéticas Visuais

### 3.1 Estética Obsidian & Titanium (Padrão Corporativo Big Tech)
- **Cores de Base**: Tons profundos `#060910`, `#0c1424` e acentos em `#38a3ff` / `#b3dcff`.
- **Materiais**: Sombreamento metálico GGX (Trowbridge-Reitz) com rugosidade controlada ($\alpha \in [0.18, 0.28]$) para criar reflexos nítidos sem granulado de ruído.
- **Iluminação**:
  - *Key Light*: Luz direcional posicionada em $(4.0, 7.0, 5.0)$ com sombra suave calculada por amostragem PCF 3×3 em mapa de profundidade de 2048px.
  - *Rim Light*: Luz de contraste posterior posicionada em $(-3.0, 2.0, -4.0)$ em tom ciano para recortar silhuetas no fundo escuro.
  - *Reflexão de Estúdio*: Emissão procedural de softbox horizontal calculada via senoide no shader de ambiente.

### 3.2 Estética Kinetic Wireframe & Cyber-Grid
- Geometria renderizada em modo híbrido (sólido translúcido + arestas acentuadas via coordenadas baricêntricas).
- Atenuação por distância (*distance fog*): $\text{cor}_{\text{final}} = \text{lerp}(\text{cor}, \text{cor}_{\text{fundo}}, 1.0 - e^{-\text{profundidade} \cdot \kappa})$.

---

## 4. Síntese Sonora Procedural — Fórmulas e Implementação em NumPy

### 4.1 Sub-Bass Drop
Gera peso acústico físico no primeiro quadro do vídeo:
$$f(t) = f_{\text{end}} + (f_{\text{start}} - f_{\text{end}}) \cdot e^{-k \cdot t}$$
```python
def generate_sub_bass(duration=2.5, sr=48000, f_start=130.0, f_end=35.0, decay=3.8):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    freq = f_end + (f_start - f_end) * np.exp(-decay * t)
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    env = np.sin(np.clip(t / 0.04, 0, 1) * np.pi / 2.0) ** 2 * np.exp(-1.5 * t)
    return np.sin(phase) * env
```

### 4.2 Cinematic Tension Riser
Constrói energia acústica crescente sincronizada com a aceleração visual:
$$s(t) = \sin\left(2\pi \cdot f_0 \cdot \left(\frac{f_{\text{max}}}{f_0}\right)^{\frac{t}{T}} \cdot t\right) \cdot \left(\frac{t}{T}\right)^2$$
```python
def generate_riser(duration=3.5, sr=48000, f_start=80.0, f_end=880.0):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    freq = f_start * (f_end / f_start) ** (t / duration)
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    env = (t / duration) ** 2.2
    return np.sin(phase) * env
```

### 4.3 Transient Metálico via Síntese FM
Simula o clique tátil de encaixe de peças ou ativação de interfaces:
$$x(t) = \sin\left(2\pi f_c t + I(t) \cdot \sin(2\pi f_m t)\right) \cdot e^{-\frac{t}{\tau}}$$
- Portadora $f_c = 1400\text{ Hz}$, Moduladora $f_m = 420\text{ Hz}$, Índice $I(t) = 3.5 \cdot e^{-t / 0.02}$, Constante de decaimento $\tau = 0.04\text{ s}$.

### 4.4 Proteção de Picos & Exportação PCM
- O áudio composto é analisado em amplitude absoluta. Picos devem ser mantidos estritamente abaixo de $-1.5\text{ dBFS}$ ($\approx 0.841$) antes da quantização para PCM 16-bits para evitar qualquer distorção de recorte (*clipping* inter-amostra) durante a compressão AAC do FFmpeg.

---

## 5. Streaming Pipe para FFmpeg (Sem Arquivos Temporários)

Para garantir máxima performance de I/O e evitar consumo desnecessário de escrita no SSD:
1. O processo pai em Python instancia o subprocesso FFmpeg com `stdin=subprocess.PIPE`.
2. O loop de renderização lê o buffer de pixels da GPU (`fbo.read(components=3)`) e envia os bytes diretamente para `proc.stdin.write(raw_bytes)`.
3. Flags de encoding recomendadas:
   `-vf vflip -c:v libx264 -preset medium -crf 17 -threads 3 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart`

---

## 6. Governança e Validação (PEV)

1. **Pre-flight**: Inspecionar GPU e contexto com `--preview` gerando 5 keyframes em menos de 2 segundos.
2. **Execute**: Executar a renderização integral com barra de progresso no console.
3. **Verify**:
   - Inspecionar a saída gerada com comandos nativos do PowerShell (`Get-Item`, `ffprobe.exe` ou `ffmpeg.exe -i`).
   - Validar que o relatório `render-report.json` documenta resolução, taxa de quadros, duração e tempo total de processamento.

---

## 7. Ferramentas e Recursos de Expansão (v1.1)

O ecossistema conta com bibliotecas científicas de ponta integradas no monorepo (`packages/motion-engine`):

| Biblioteca | Módulo no Pacote | Funcionalidade Principal |
| :--- | :--- | :--- |
| **`Trimesh`** | `motion_engine.geometry` | Criação de primitivas procedurais (`icosphere`, `torus`, `cylinder`, `capsule`), cálculo de normais e importação de modelos externos (`.glb`, `.gltf`, `.obj`). |
| **`OpenSimplex`** | `motion_engine.noise` | Geração de ruído procedural 2D/3D/4D e *fractional Brownian motion* (fBm) para deformação orgânica de vértices e superfícies fluidas. |
| **`SciPy`** | `motion_engine.dsp` | Filtros IIR Butterworth (varreduras dinâmicas de frequência) e convolução de reverb estéreo para simulação acústica espacial. |
| **`SoundFile`** | `motion_engine.audio` | I/O de áudio em ponto flutuante de 32-bits e múltiplos formatos de exportação. |
| **`ImageIO`** | Pipeline de Suporte | Manipulação de sequências de quadros, conversão e exportação rápida de GIFs animados. |

