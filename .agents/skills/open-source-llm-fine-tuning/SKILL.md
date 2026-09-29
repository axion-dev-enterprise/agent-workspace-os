---
name: open-source-llm-fine-tuning
description: Implementa fine-tuning eficiente de modelos de linguagem abertos usando LoRA/QLoRA e alinhamento direto, reduzindo custo computacional em até 90% comparado ao treinamento full-parameter. Permite treinar adaptadores especializados para modelos locais em hardware consumer (GPU 8-24GB VRAM) com pipelines reprodutíveis em Windows/PowerShell.
---

## 1. Visão Geral e Casos de Uso

### Contexto Técnico Validado

Yann LeCun (Meta AI) destacou repetidamente que o futuro da IA reside em modelos abertos e em técnicas de fine-tuning eficientes que democratizem o acesso à adaptação de LLMs. A técnica de **Low-Rank Adaptation (LoRA)** e sua variante quantizada **QLoRA** (Dettmers et al., 2023) permitem treinar adaptadores de baixo rank sobre pesos congelados de modelos pré-treinados, reduzindo parâmetros treináveis em 10.000x e memória VRAM em até 75%.

### Casos de Uso Práticos

| Caso | Modelo Base | VRAM Mínima | Tempo Estimado |
|------|------------|-------------|----------------|
| Fine-tuning de domínio (jurídico, médico) | Llama-3.1-8B | 12 GB | 2-6h |
| Alinhamento RLHF/DPO simplificado | Mistral-7B | 8 GB | 1-4h |
| Adaptador de estilo/tom de voz | Qwen2.5-7B | 10 GB | 1-3h |
| Classificação especializada | Phi-3-mini-4k | 6 GB | 30min-2h |
| RAG com fine-tuning de instruções | Gemma-2-9B | 16 GB | 3-8h |

### Arquitetura do Pipeline

```
Dataset (JSONL) → Tokenização → LoRA Adapter (r=16, α=32)
    → QLoRA (4-bit NF4) → Treinamento (PEFT + TRL)
    → Valuação (perplexity + eval manual) → Merge/Export
```

---

## 2. Guardrails de Engenharia e Boas Práticas (Windows / PowerShell / Paths)

### 2.1 Pré-requisitos de Ambiente

```powershell
# Verificar Python e GPU antes de iniciar
python --version
# Esperado: Python 3.10+

nvidia-smi
# Esperado: GPU com CUDA 11.8+ e VRAM >= 8GB

# Criar ambiente virtual isolado
python -m venv .venv-axion-finetune
.\.venv-axion-finetune\Scripts\Activate.ps1

# Instalar dependências com versões pinadas (reprodutibilidade)
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cu121
pip install transformers==4.46.3 peft==0.13.2 trl==0.12.1
pip install datasets==3.1.0 accelerate==1.1.1 bitsandbytes==0.44.1
pip install wandb==0.18.7
```

### 2.2 Guardrails Críticos

| # | Guardrail | Risco se Violado | Mitigação |
|---|-----------|-------------------|-----------|
| G1 | **Nunca treinar com pesos não congelados em QLoRA** | OOM imediato, VRAM > 24GB | Verificar `model.is_loaded_in_4bit == True` antes do loop |
| G2 | **Paths Windows com espaços** | Falha silenciosa em `load_dataset` | Usar `pathlib.Path` e sempre `resolve()` |
| G3 | **Seed determinística** | Resultados não reprodutíveis | Fixar `seed=42` em `TrainingArguments` e `set_seed` |
| G4 | **Checkpoint overflow em disco** | C: drive cheio, crash | `save_total_limit=2`, `save_strategy="steps"` |
| G5 | **Dataset com exemplos vazios** | NaN loss, treinamento divergente | Filtrar `len(example["text"]) < 10` no preprocessing |
| G6 | **VRAM insuficiente para batch** | CUDA OOM | Reduzir `per_device_train_batch_size` ou ativar gradient checkpointing |
| G7 | **Merge LoRA sem salvar adapter separado** | Perda irreversível do adapter | Sempre salvar adapter ANTES do merge |

### 2.3 Estrutura de Diretórios Recomendada

```
C:\axion-projects\fine-tuning\
├── .venv-axion-finetune\
├── configs\
│   └── lora_config.yaml
├── data\
│   ├── train.jsonl
│   └── eval.jsonl
├── outputs\
│   ├── checkpoints\
│   └── merged-model\
├── scripts\
│   ├── prepare_dataset.py
│   ├── train_lora.py
│   └── merge_adapter.py
└── logs\
    └── training.log
```

---

## 3. Padrões de Implementação e Código de Exemplo (Python)

### 3.1 Preparação do Dataset (`scripts/prepare_dataset.py`)

```python
"""
AXION Enterprise - Dataset Preparation for LLM Fine-Tuning
Gera dataset JSONL formatado para treinamento com TRL/PEFT.
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SEED = 42
random.seed(SEED)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRAIN_FILE = DATA_DIR / "train.jsonl"
EVAL_FILE = DATA_DIR / "eval.jsonl"


def build_instruction_dataset(
    raw_samples: List[Dict[str, str]],
    eval_ratio: float = 0.1,
    min_length: int = 10,
) -> tuple[List[Dict], List[Dict]]:
    """
    Converte amostras brutas em formato instruction-following.
    Formato esperado de entrada: {"instruction": ..., "input": ..., "output": ...}
    """
    formatted = []
    for sample in raw_samples:
        instruction = sample.get("instruction", "").strip()
        input_text = sample.get("input", "").strip()
        output_text = sample.get("output", "").strip()

        if len(output_text) < min_length:
            continue

        if input_text:
            text = (
                f"### Instrução:\n{instruction}\n\n"
                f"### Entrada:\n{input_text}\n\n"
                f"### Resposta:\n{output_text}"
            )
        else:
            text = (
                f"### Instrução:\n{instruction}\n\n"
                f"### Resposta:\n{output_text}"
            )

        formatted.append({"text": text})

    random.shuffle(formatted)
    split_idx = int(len(formatted) * (1 - eval_ratio))
    return formatted[:split_idx], formatted[split_idx:]


def write_jsonl(data: List[Dict], filepath: Path) -> None:
    """Escreve lista de dicts em arquivo JSONL com encoding UTF-8."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[OK] {len(data)} exemplos escritos em {filepath}")


def main():
    # Exemplo: carregar dados brutos (substituir por sua fonte real)
    raw_samples = [
        {
            "instruction": "Explique o que é LoRA em fine-tuning de LLMs.",
            "input": "",
            "output": (
                "LoRA (Low-Rank Adaptation) é uma técnica que congela os pesos "
                "originais do modelo e adiciona matrizes de decomposição de baixo rank "
                "(A e B) que são treinadas. Isso reduz drasticamente o número de "
                "parâmetros treináveis, permitindo fine-tuning eficiente em GPUs "
                "com pouca memória VRAM."
            ),
        },
        {
            "instruction": "Qual a diferença entre LoRA e QLoRA?",
            "input": "",
            "output": (
                "LoRA treina adaptadores sobre pesos em precisão FP16/BF16. "
                "QLoRA quantiza os pesos base para 4-bit (formato NF4) antes de "
                "aplicar LoRA, reduzindo ainda mais a memória necessária. "
                "QLoRA permite treinar modelos de 65B+ parâmetros em GPUs de 24GB."
            ),
        },
        {
            "instruction": "Resuma os benefícios de modelos abertos.",
            "input": "",
            "output": (
                "Modelos abertos permitem: (1) fine-tuning local sem dependência de APIs "
                "pagas, (2) transparência total sobre arquitetura e pesos, (3) "
                "customização profunda para domínios específicos, (4) controle de "
                "privacidade com dados que nunca saem da infraestrutura local, "
                "e (5) reprodutibilidade científica completa."
            ),
        },
    ]

    train_data, eval_data = build_instruction_dataset(raw_samples, eval_ratio=0.15)
    write_jsonl(train_data, TRAIN_FILE)
    write_jsonl(eval_data, EVAL_FILE)


if __name__ == "__main__":
    main()
```

### 3.2 Treinamento LoRA/QLoRA (`scripts/train_lora.py`)

```python
"""
AXION Enterprise - QLoRA Fine-Tuning Pipeline
Treinamento eficiente de adaptadores LoRA sobre modelos abertos quantizados 4-bit.
"""

import os
import sys
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    set_seed,
)
from trl import SFTTrainer

# ─── Configuração ───────────────────────────────────────────────
SEED = 42
BASE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
OUTPUT_DIR = str(Path(__file__).resolve().parent.parent / "outputs" / "checkpoints")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Parâmetros de treinamento
MAX_SEQ_LENGTH = 1024
NUM_EPOCHS = 3
LEARNING_RATE = 2e-4
PER_DEVICE_BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 8
WARMUP_RATIO = 0.03
LOGGING_STEPS = 10
SAVE_TOTAL_LIMIT = 2

# Parâmetros LoRA
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def verify_gpu() -> None:
    """Verifica disponibilidade de GPU CUDA com VRAM suficiente."""
    if not torch.cuda.is_available():
        print("[ERRO] CUDA não disponível. Este pipeline requer GPU NVIDIA.")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
    print(f"[GPU] {gpu_name} | VRAM: {vram_gb:.1f} GB")

    if vram_gb < 7.0:
        print("[AVISO] VRAM < 7GB. Reduza batch size ou use modelo menor (Phi-3-mini).")


def load_quantization_config() -> BitsAndBytesConfig:
    """Configuração QLoRA: quantização 4-bit NF4 com double quantization."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


def load_model_and_tokenizer():
    """Carrega modelo base quantizado 4-bit e tokenizer."""
    print(f"[LOAD] Carregando modelo: {BASE_MODEL}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=load_quantization_config(),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    # Preparar modelo para treinamento com pesos quantizados
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # Configurar LoRA
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


def load_datasets():
    """Carrega datasets de treino e avaliação."""
    train_path = DATA_DIR / "train.jsonl"
    eval_path = DATA_DIR / "eval.jsonl"

    if not train_path.exists():
        print(f"[ERRO] Dataset de treino não encontrado: {train_path}")
        print("Execute primeiro: python scripts/prepare_dataset.py")
        sys.exit(1)

    train_dataset = load_dataset("json", data_files=str(train_path), split="train")
    eval_dataset = None
    if eval_path.exists():
        eval_dataset = load_dataset("json", data_files=str(eval_path), split="train")

    print(f"[DATA] Train: {len(train_dataset)} | Eval: {len(eval_dataset) if eval_dataset else 0}")
    return train_dataset, eval_dataset


def get_training_arguments() -> TrainingArguments:
    """Argumentos de treinamento otimizados para QLoRA."""
    return TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        per_device_eval_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type="cosine",
        logging_steps=LOGGING_STEPS,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=SAVE_TOTAL_LIMIT,
        eval_strategy="steps",
        eval_steps=100,
        bf16=True,
        tf32=True,
        max_grad_norm=0.3,
        seed=SEED,
        report_to="wandb",
        run_name="axion-qlora-f