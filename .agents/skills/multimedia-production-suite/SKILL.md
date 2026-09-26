---
name: multimedia-production-suite
description: >-
  Operational creative and multimedia workflow skill for audio, video, and image engineering.
  Covers LosslessCut zero-transcode video cutting, Shotcut multi-track editing, Krita digital painting
  and illustration, GIMP raster image manipulation, and FxSound audio enhancement.
---

# Multimedia Production Suite — Manual Operacional do Agente

Guia canônico e referência de comandos para fluxos de criação, edição, tratamento visual, pós-produção e transcodificação ágil de mídia audiovisual utilizando ferramentas livres e aceleradas por hardware (**LosslessCut**, **Shotcut**, **Krita**, **GIMP** e **FxSound**).

---

## 1. Matriz de Ferramentas e Casos de Uso

| Ferramenta | Especialidade | Motor / Aceleração | Caso de Uso Canônico |
| :--- | :--- | :--- | :--- |
| **LosslessCut** | Corte & União Instantânea | FFmpeg Direct Stream Copy | Aparar vídeos, remover trechos indesejados e unir gravações na velocidade do SSD (sem render) |
| **Shotcut** | Edição de Vídeo Multi-Faixa | MLT Framework / GPU | Montagem de tutoriais, sincronização de áudio/vídeo, transições e exportação em 1080p/4K |
| **Krita** | Pintura Digital & Arte | OpenGL / Direct3D / Canvas | Ilustração, arte conceitual, texturização, desenho vetorial híbrido e storyboard |
| **GIMP** | Edição Raster de Fotos | GEGL Engine | Recorte de fotos, tratamento de camadas, máscaras, remoção de fundo e composição gráfica |
| **FxSound** | Equalização & Áudio | DSP Processing | Aprimoramento de fidelidade acústica, ganho de volume e clareza vocal em tempo real |

---

## 2. Padrões Operacionais e Melhores Práticas

### 2.1 Fluxo Ágil com LosslessCut (Zero-Transcode / Zero Quality Loss)
O LosslessCut opera através de cópia direta de stream (*stream copy*), manipulando pacotes H.264/H.265/AV1 diretamente nos quadros-chave (I-Frames/Keyframes):
* **Velocidade:** Processa arquivos de múltiplos gigabytes em poucos segundos, limitado apenas pela taxa de leitura/gravação do SSD Kingston A400.
* **Preservação de Qualidade:** Não recalcula a taxa de bits nem aplica perda de compressão. O arquivo final mantém rigorosamente o mesmo codec e bitrate do original.
* **Extração de Faixas:** Permite extrair a faixa de áudio original de um vídeo sem reencodificar (ex: `.mp4` para `.aac` ou `.mp3`).

### 2.2 Edição de Vídeo com Shotcut
* **Gestão de Timeline:** Suporte a múltiplas faixas de áudio e vídeo com ajuste automático de framerate.
* **Exportação Otimizada:** Utilizar perfis de exportação compatíveis com os 4 núcleos do Intel Core i5-3470 (x264 *preset* `veryfast` ou `faster`) para manter a exportação rápida sem saturar a memória RAM.

### 2.3 Pintura Digital e Design com Krita
* **Aceleração Gráfica:** Manter a aceleração por GPU (Direct3D 11 via ANGLE ou OpenGL) ativada nas preferências do Krita para garantir rotação, zoom e pinceladas a 60 FPS na AMD Radeon HD 5800.
* **Reserva de Memória:** Como a máquina possui 12 GB de RAM, o limite de alocação de memória do Krita pode ser configurado em até 70% (~8.4 GB), permitindo trabalhar com telas de alta resolução (4K / 300 DPI) com centenas de camadas sem *swap* em disco.

### 2.4 Manipulação Fotográfica com GIMP
* **Edição Não Destrutiva:** Utilizar canais de cor e máscaras de camada para manter a integridade das imagens originais.
* **Exportação Web:** Padronizar imagens para web em formato WebP ou JPEG com amostragem 4:2:0 para menor peso e carregamento ultrarrápido.

---

## 3. Diretrizes de Governança e Armazenamento
* **Organização de Mídias:** Arquivos brutos de gravação (*raw footage*) e projetos intermediários devem ser mantidos no HD secundário `E:\` para não sobrecarregar o SSD de boot `C:\`.
* **Exportação Final:** Os artefatos finais renderizados devem ser movidos para a nuvem segura via *Proton Drive* ou sincronizados via *Rclone*.
* **Purga de Cache:** Esvaziar periodicamente caches temporários de renderização em diretórios descartáveis (`temp/`).
