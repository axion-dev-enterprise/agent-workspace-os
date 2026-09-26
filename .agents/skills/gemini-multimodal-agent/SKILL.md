---
name: gemini-multimodal-agent
description: >-
  Operational skill for building autonomous AI agents and multimodal workflows with Google Gemini models
  (Gemini 1.5 Pro, Flash, Gemini 2.0). Use when implementing deterministic tool calling (Function Calling),
  structured JSON outputs via Pydantic/Schemas, RAG pipelines, audio/video analysis, and vector embeddings.
---

# Google Gemini Multimodal & Agentic Engineering Skill

Skill operacional para desenvolvimento de inteligência artificial autônoma, pipelines de extração multimodal e orquestração de ferramentas com a família **Google Gemini** para a **AXION Enterprise**.

---

## 1. Modelos Recomendados & Casos de Uso

| Modelo | Context Window | Velocidade | Melhor Para |
| :--- | :--- | :--- | :--- |
| **`gemini-2.0-flash`** | 1M tokens | Ultra-rápido | Agentes em tempo real, triagem, roteamento de ferramentas e parsing de dados. |
| **`gemini-1.5-pro`** | 2M tokens | Analítico | Raciocínio profundo, análise de bases de código completas, leitura de vídeos longos e contratos complexos. |
| **`text-embedding-004`** | 2048 dims | Alta precisão | Vetorização semântica de base de conhecimento para sistemas RAG. |

---

## 2. Padrão Determinístico: Function Calling & Structured JSON (Python SDK)

```python
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Inicialização com nova Google GenAI SDK
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

class TaskExtraction(BaseModel):
    title: str = Field(description="Título objetivo da tarefa")
    priority: str = Field(description="HIGH, MEDIUM ou LOW")
    assignee_email: str = Field(description="E-mail do responsável no domínio example.com")
    due_date: str = Field(description="Data limite no formato YYYY-MM-DD")

def extract_structured_action(text_prompt: str) -> TaskExtraction:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=text_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TaskExtraction,
            system_instruction="Você é um orquestrador de operações corporativas da AXION Enterprise."
        ),
    )
    return TaskExtraction.model_validate_json(response.text)
```

---

## 3. Análise Multimodal (Vídeo, Áudio & Documentos)

O Gemini suporta ingestão nativa de mídias sem necessidade de transcrição prévia externa:

```python
# Upload de vídeo ou áudio do Google Meet para análise direta
video_file = client.files.upload(file="reuniao_meet.mp4")

response = client.models.generate_content(
    model="gemini-1.5-pro",
    contents=[
        video_file,
        "Analise a reunião e gere a ata executiva com: 1. Decisões tomadas, 2. Prazos acordados, 3. Itens de bloqueio."
    ]
)
print(response.text)
```
