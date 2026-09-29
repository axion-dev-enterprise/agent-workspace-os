# Neural Video Generation & Visual Sparse Attention (VSA) Architecture

Este documento descreve a arquitetura técnica de inferência acelerada em modelos de difusão de vídeo condicionados por referência de imagem e áudio (**Ref2VA / MiniMax-H3 / FastVideo**), bem como a análise de viabilidade de hardware e alocação de tensores.

---

## 1. O Problema da Atenção Esparsa em Geração Condicionada (Ref2VA)

Em modelos de texto para vídeo (*Text-to-Video* - T2V), o algoritmo **Visual Sparse Attention (VSA)** divide o volume de vídeo em blocos 3D espaço-temporais (cubos 4×4×4 de 64 tokens) e poda dinamicamente de 75% a 90% dos blocos menos relevantes via projeções de gating aprendidas (`to_gate_compress`), alcançando aceleração de 2.2x a 3.5x.

No entanto, em pipelines **Ref2VA (Reference-to-Video)**, a arquitetura introduz tokens heterogêneos de entrada antes da sequência de vídeo:
1. **Tokens de Prompt de Texto**.
2. **Tokens de Latente de Imagem de Referência (Identidade do Personagem)**.
3. **Tokens de Latente de Áudio de Referência (Sincronia labial e ritmo)**.

### A Solução: Ref2VA VSA Gate Patch
O nó `ComfyUI-Ref2VA-VSA` resolve o problema através de:
- **Multimodal Dense-Exempt Prefix**: Os tokens de referência são mapeados em blocos puros e **isentos de qualquer poda top-k**. Eles permanecem 100% densos durante todo o processo de difusão, preservando a identidade facial e fidelidade do personagem.
- **Top-K Video Pruning**: A esparsidade de 75% é aplicada estritamente sobre os frames de vídeo gerados.
- **Transplante de Gate**: Os pesos de gating aprendidos são aplicados diretamente sobre o checkpoint quantizado `int8` do MiniMax-H3.

---

## 2. Requisitos de Hardware & Orçamento de VRAM

| Pipeline | Atenção | Passos | VRAM Pico | Requisito de GPU | Viabilidade Local |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MiniMax H3 Nativo** | Global Densa | 50 (Euler) | ~22.5 GB | NVIDIA RTX 4090 (24GB) / A5000 | Inviável em GPUs < 24GB |
| **H3 Turbo LoRA** | Global Densa | 4 (Euler) | ~21.0 GB | NVIDIA RTX 3090 / 4090 | Inviável em GPUs < 24GB |
| **Ref2VA VSA (Otimizado)** | **75% Esparsa + Prefixo Denso** | **4 (Euler)** | **~13.5 GB** | **NVIDIA RTX 4090 / 3090** | **Requer CUDA + 16GB+ VRAM** |

### Regra de Ouro para Execução em Agentes:
1. **Sonda Prévia Obrigatória**: Sempre execute `python .agents/skills/agentic-engineering-suite/scripts/system_agent_preflight.py` antes de instanciar ou baixar modelos de difusão.
2. **Prevenção de Esgotamento de Disco e Memória**: Se o host não possuir GPU NVIDIA com suporte a CUDA e no mínimo 16 GB de VRAM livre, **NÃO realize o download de checkpoints pesados (>30 GB)**. Delegue a execução para instâncias de nuvem (RunPod, Modal, Fal.ai ou GCP Cloud GPUs).
