# Procedural Audio Formulas — Math & NumPy Recipes

Biblioteca canônica de equações e implementações em Python / NumPy para geração de efeitos sonoros e trilhas musicais procedurais sem bibliotecas externas.

---

## 1. Fundamentos Matemáticos do Som Digital

- **Taxa de Amostragem ($f_s$)**: Padrão de estúdio $48.000\text{ Hz}$ ($48\text{ kHz}$).
- **Vetor Temporal**: $t = \frac{n}{f_s}, \quad n \in \{0, 1, \dots, N-1\}$.
- **Fase Instantânea**: $\phi(t) = 2\pi \int_0^t f(\tau) d\tau \approx \frac{2\pi}{f_s} \sum_{k=0}^n f(k)$.
- **Escala de Frequências (MIDI para Hz)**:
  $$f = 440 \cdot 2^{\frac{m - 69}{12}}$$

---

## 2. Receitas Matemáticas de Efeitos Sonoros

### 2.1 Sub-Bass Drop (Impacto Grave Cinemático)
Gera uma rampa exponencial descendente que produz impacto físico em fones e subwoofers:

$$f(t) = f_{\text{end}} + (f_{\text{start}} - f_{\text{end}}) \cdot e^{-k \cdot t}$$

```python
import numpy as np

def sub_bass_drop(duration=2.2, sr=48000, f_start=135.0, f_end=34.0, decay=4.2):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    freq = f_end + (f_start - f_end) * np.exp(-decay * t)
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    # Envelope sem estalos: ataque rápido em sin² e release exponencial
    env = np.sin(np.clip(t / 0.03, 0, 1) * np.pi / 2.0) ** 2 * np.exp(-1.4 * t)
    return np.sin(phase) * env
```

### 2.2 Cinematic Tension Riser (Aceleração e Tensão)
Varredura exponencial ascendente com envelope de potência:

$$f(t) = f_0 \cdot \left(\frac{f_{\text{top}}}{f_0}\right)^{\frac{t}{T}}$$

```python
def cinematic_riser(duration=3.5, sr=48000, f_0=60.0, f_top=960.0):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    freq = f_0 * (f_top / f_0) ** (t / duration)
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    env = (t / duration) ** 2.5
    # Adiciona leve distorção harmônica suave
    signal = np.sin(phase) + 0.3 * np.sin(2.0 * phase)
    return (signal / 1.3) * env
```

### 2.3 Transient Metálico via Síntese FM (Cliques e Encaixes)
Simula contato sólido entre materiais duros:

$$y(t) = \sin\left(2\pi f_c t + I(t) \cdot \sin(2\pi f_m t)\right) \cdot e^{-\frac{t}{\tau}}$$

```python
def metallic_click(duration=0.08, sr=48000, fc=1500.0, fm=420.0, idx=4.0, tau=0.02):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    i_t = idx * np.exp(-t / tau)
    modulator = np.sin(2.0 * np.pi * fm * t)
    carrier = np.sin(2.0 * np.pi * fc * t + i_t * modulator)
    env = np.exp(-t / (tau * 1.5))
    return carrier * env
```

### 2.4 Ambient Drone com Batimento Binaural
Gera atmosfera imersiva e sensação de amplitude espacial:

```python
def ambient_drone(duration=15.0, sr=48000, base_freq=65.41): # C2
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    # Canal esquerdo e direito ligeiramente desafinados em 0.6 Hz
    left = 0.5 * np.sin(2.0 * np.pi * base_freq * t) + 0.25 * np.sin(2.0 * np.pi * (base_freq * 2) * t)
    right = 0.5 * np.sin(2.0 * np.pi * (base_freq + 0.6) * t) + 0.25 * np.sin(2.0 * np.pi * (base_freq * 2 - 0.4) * t)
    
    # Envelopes de entrada e saída suaves
    fade_in = np.sin(np.clip(t / 2.0, 0, 1) * np.pi / 2.0) ** 2
    fade_out = np.sin(np.clip((duration - t) / 3.0, 0, 1) * np.pi / 2.0) ** 2
    env = fade_in * fade_out
    
    return np.column_stack([left * env, right * env])
```

---

## 3. Mixagem e Espacialização Estéreo

### 3.1 Panorâmica de Potência Constante (Equal-Power Panning)
Evita que o som sofra queda de volume de $3\text{ dB}$ ao ser posicionado no centro do panorama estéreo:

```python
def pan_stereo(mono_signal: np.ndarray, pan: float) -> np.ndarray:
    """
    pan: valor entre -1.0 (totalmente à esquerda) e +1.0 (totalmente à direita).
    """
    pan_clamped = np.clip(pan, -1.0, 1.0)
    theta = (pan_clamped + 1.0) * (np.pi / 4.0) # 0 a pi/2
    left_gain = np.cos(theta)
    right_gain = np.sin(theta)
    return np.column_stack([mono_signal * left_gain, mono_signal * right_gain])
```

### 3.2 Teto de Segurança Dinâmico (-1.5 dBFS)
```python
def normalize_ceiling(stereo_mix: np.ndarray, target_dbfs=-1.5) -> np.ndarray:
    peak = np.max(np.abs(stereo_mix))
    if peak <= 0.0:
        return stereo_mix
    ceiling_linear = 10.0 ** (target_dbfs / 20.0)
    if peak > ceiling_linear:
        return stereo_mix * (ceiling_linear / peak)
    return stereo_mix
```
