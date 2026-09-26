# Motion Render Service — Serviço Dedicado de Renderização 3D & Áudio Procedural

Serviço de alta performance para produção determinística de vídeos 3D, motion graphics e áudio procedural para a marca AXION.

---

## 1. Arquitetura do Serviço

- **Backend**: FastAPI assíncrono escutando estritamente em loopback local (`127.0.0.1:8150`).
- **Motor Gráfico**: ModernGL / OpenGL 3.3 Core Profile com contexto offscreen headless, mapa de sombras PCF 2048px, sombreamento metálico GGX, 4x MSAA e tone mapping ACES.
- **Motor de Áudio**: Síntese analítica procedural com NumPy (sub-drops, risers, clicks FM e batimentos binaurais).
- **Encoder de Vídeo**: FFmpeg subprocess streaming via stdin pipe (Zero-Disk Intermediate).
- **Interface Studio**: Painel web integrado para disparo de renders, inspeção de keyframes e download dos masters gerados.

---

## 2. Inicialização do Serviço

Para iniciar o servidor daemon localmente:

```powershell
python -m uvicorn src.main:app --app-dir C:\workspace\services\motion-render-service --host 127.0.0.1 --port 8150
```

---

## 3. Endpoints da API REST

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/` | Interface gráfica do Motion Studio |
| `GET` | `/health` | Diagnóstico do serviço e detecção de GPU/FFmpeg |
| `GET` | `/scenes` | Lista as cenas e storyboards registrados |
| `POST` | `/preview` | Gera 5 keyframes instantâneos em PNG (< 2s) |
| `POST` | `/render` | Enfileira renderização completa em background |
| `GET` | `/render/status` | Progresso em tempo real da renderização |
| `GET` | `/videos` | Lista todos os arquivos renderizados em `output/` |
| `GET` | `/videos/{filename}` | Download / streaming do arquivo MP4 ou WAV |

---

## 4. Testes Automatizados

```powershell
python -m unittest discover -s C:\workspace\services\motion-render-service\tests
```
