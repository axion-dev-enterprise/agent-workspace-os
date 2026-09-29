---
name: generative-agent-memory-reflection
description: Implementa a arquitetura de memória com reflexão e planejamento hierárquico do paper "Generative Agents" para construir agentes LLM com continuidade de estado e comportamento coerente em interações longas. Utiliza retrieval ponderado por relevância, recência e importância sobre um stream de memórias, combinado com um loop de reflexão que sintetiza observações em insights de ordem superior. Aplica-se a sistemas multi-agente, simulações interativas e agentes com memória de longo prazo.
---

## 1. Visão Geral e Casos de Uso

### Origem Técnica

O paper **"Generative Agents: Interactive Simulacra of Human Behavior"** (Park et al., 2023) propõe uma arquitetura de agentes generativos que simula comportamento humano realista usando LLMs. A inovação central está em três pilares integrados:

1. **Memory Stream**: um log cronológico de observações (eventos, diálogos, percepções) com timestamps, que serve como fonte primária de experiência do agente.
2. **Reflexão Periódica**: um mecanismo que sintetiza observações recentes em insights de ordem superior (abstrações, inferências, planos revisados), armazenados no mesmo stream com tipo distinto.
3. **Planejamento Hierárquico**: decomposição de objetivos de alto nível em planos e ações de baixo nível, com revisão contínua baseada no estado atual da memória.

O **retrieval de memória** é calculado como uma combinação linear de três scores:

```
score(m) = α · relevância(m, query) + β · recência(m) + γ · importância(m)
```

- **Relevância**: similaridade semântica entre a memória e a query atual (embedding cosine).
- **Recência**: decaimento exponencial baseado no tempo decorrido desde o evento.
- **Importância**: escala 1–10 atribuída pelo LLM à relevância do evento para o agente.

### Casos de Uso

| Caso | Descrição |
|------|-----------|
| **Simulação multi-agente** | Ambientes com N agentes que interagem, possuem personalidades distintas e memória compartilhada/privada. |
| **Assistente com continuidade** | Chatbot que mantém coerência de personalidade, contexto e preferências ao longo de semanas/meses. |
| **Agente de suporte técnico** | Agente que lembra de incidentes anteriores, padrões de falha e resoluções aplicadas. |
| **NPCs em jogos/simulações** | Personagens com memória de interações passadas e comportamento plausível. |
| **Agente de pesquisa** | Agente que acumula observações, reflete sobre padrões e gera hipóteses ao longo de sessões. |

### Arquitetura de Referência

```
┌─────────────────────────────────────────────────────────┐
│                    GENERATIVE AGENT                      │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │  Perception   │──▶│ Memory Stream │◀──│ Reflection  │  │
│  │  (Observações)│   │  (Eventos +   │   │   Loop      │  │
│  └──────────────┘   │  Insights)    │   │ (Síntese)   │  │
│                      └──────┬───────┘   └──────▲──────┘  │
│                             │                   │        │
│                      ┌──────▼───────┐           │        │
│                      │   Retrieval  │───────────┘        │
│                      │ (rel × rec × │                    │
│                      │  importance) │                    │
│                      └──────┬───────┘                    │
│                             │                            │
│                      ┌──────▼───────┐   ┌─────────────┐  │
│                      │   Planning   │──▶│  Action     │  │
│                      │ (Hierárquico)│   │  Execution  │  │
│                      └──────────────┘   └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Guardrails de Engenharia e Boas Práticas (Windows / PowerShell / Paths)

### 2.1 Estrutura de Diretórios

```
axion-generative-agent/
├── src/
│   ├── __init__.py
│   ├── memory_stream.py
│   ├── reflection.py
│   ├── retrieval.py
│   ├── planning.py
│   ├── agent.py
│   └── config.py
├── tests/
│   ├── test_memory_stream.py
│   ├── test_retrieval.py
│   ├── test_reflection.py
│   └── test_agent.py
├── data/
│   └── memory_store.json
├── requirements.txt
├── pyproject.toml
└── SKILL.md
```

### 2.2 Paths e Encoding (Windows)

| Regra | Detalhe |
|-------|---------|
| **Path separators** | Use sempre `pathlib.Path` — nunca concatene strings com `\\` ou `/`. |
| **Encoding** | Todo arquivo de I/O deve declarar `encoding="utf-8"` explicitamente. |
| **PowerShell** | Use `$env:PYTHONIOENCODING="utf-8"` antes de executar scripts que imprimem Unicode. |
| **Shell** | Use `python -m pytest` em vez de `pytest` para garantir o ambiente correto. |
| **Virtual env** | `python -m venv .venv` → `.venv\Scripts\Activate.ps1` (Windows) ou `source .venv/bin/activate` (Unix). |

### 2.3 Guardrails de Engenharia

1. **Idempotência do Memory Stream**: cada memória deve ter um `id` determinístico (UUID v5 baseado em conteúdo + timestamp) para evitar duplicatas em re-execuções.

2. **Limites de Memória**: o stream deve ter um limite configurável (`max_memories`, default 10.000). Quando excedido, aplicar **evicção por importância** (descartar as de menor score composto), nunca por FIFO cego.

3. **Reflexão não-bloqueante**: o loop de reflexão deve rodar em thread separada ou ser chamado de forma assíncrona para não bloquear o loop principal de percepção/ação.

4. **Determinismo de Retrieval**: os pesos α, β, γ devem ser configuráveis e versionados. Alterações de peso invalidam caches de retrieval.

5. **Persistência**: o memory stream deve ser serializável/deserializável com JSON ou SQLite. Nunca manter estado apenas em memória RAM.

6. **Segurança de Prompt**: as memórias recuperadas são injetadas no prompt do LLM. Sanitizar conteúdo de memórias de terceiros para prevenir prompt injection.

7. **Observabilidade**: cada retrieval e reflexão deve emitir log estruturado (JSON) com scores, memórias selecionadas e duração.

### 2.4 Exemplo de Configuração Segura

```python
# src/config.py
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class AgentConfig:
    # Retrieval weights (must sum to 1.0)
    alpha_relevance: float = 0.40   # α
    beta_recency: float = 0.30      # β
    gamma_importance: float = 0.30  # γ

    # Recency half-life in hours
    recency_half_life_hours: float = 24.0

    # Memory stream limits
    max_memories: int = 10_000
    eviction_batch_size: int = 100

    # Reflection trigger
    reflection_threshold: int = 100  # trigger after N new observations
    reflection_max_insights: int = 5

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"

    # Data paths (pathlib-safe)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    memory_store_path: Path = field(
        default_factory=lambda: Path("data") / "memory_store.json"
    )

    def __post_init__(self):
        total = self.alpha_relevance + self.beta_recency + self.gamma_importance
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Retrieval weights must sum to 1.0, got {total:.6f}"
            )
        if self.max_memories <= 0:
            raise ValueError("max_memories must be positive")
        if self.recency_half_life_hours <= 0:
            raise ValueError("recency_half_life_hours must be positive")
```

---

## 3. Padrões de Implementação e Código de Exemplo (Python)

### 3.1 Memory Stream — Modelo de Dados

```python
# src/memory_stream.py
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class MemoryType(str, Enum):
    OBSERVATION = "observation"   # raw event / perception
    REFLECTION = "reflection"     # synthesized insight
    PLAN = "plan"                 # planned action


@dataclass
class Memory:
    content: str
    memory_type: MemoryType = MemoryType.OBSERVATION
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    importance: float = 5.0          # 1.0 – 10.0
    agent_id: str = "default"
    metadata: dict = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            # Deterministic UUID v5 from content + timestamp + agent
            ns = uuid.NAMESPACE_URL
            key = f"{self.agent_id}:{self.timestamp.isoformat()}:{self.content}"
            self.id = str(uuid.uuid5(ns, key))
        # Clamp importance
        self.importance = max(1.0, min(10.0, self.importance))

    @property
    def age_hours(self) -> float:
        now = datetime.now(timezone.utc)
        delta = now - self.timestamp
        return delta.total_seconds() / 3600.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["memory_type"] = self.memory_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Memory":
        d = dict(d)
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d["memory_type"] = MemoryType(d["memory_type"])
        return cls(**d)


class MemoryStream:
    """Append-only stream of memories with persistence and eviction."""

    def __init__(self, store_path: Path, max_memories: int = 10_000):
        self._store_path = store_path
        self._max_memories = max_memories
        self._memories: list[Memory] = []
        self._load()

    # ── Persistence ──────────────────────────────────────────

    def _load(self) -> None:
        if self._store_path.exists():
            raw = json.loads(
                self._store_path.read_text(encoding="utf-8")
            )
            self._memories = [Memory.from_dict(m) for m in raw]

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [m.to_dict() for m in self._memories]
        self._store_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Core operations ──────────────────────────────────────

    def append(self, memory: Memory) -> Memory:
        # Deduplicate by id
        existing_ids = {m.id for m in self._memories}
        if memory.id in existing_ids:
            return memory
        self._memories.append(memory)
        self._evict_if_needed()
        self._save()
        return memory

    def add_observation(
        self,
        content: str,
        importance: float = 5.0,
        agent_id: str = "default",
        metadata: Optional[dict] = None,
    ) -> Memory:
        mem = Memory(
            content=content,
            memory_type=MemoryType.OBSERVATION,
            importance=importance,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        return self.append(mem)

    def add_reflection(
        self,
        content: str,
        importance: float = 8.0,
        agent_id: str = "default",
        metadata: Optional[dict] = None,
    ) -> Memory:
        mem = Memory(
            content=content,
            memory_type=MemoryType.REFLECTION,
            importance=importance,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        return self.append(mem)

    @property
    def all_memories(self) -> list[Memory]:
        return list(self._memories)

    @property
    def size(self) -> int:
        return len(self._memories)

    def recent(self, n: int) -> list[Memory]:
        return sorted(
            self._memories, key=lambda m: m.timestamp, reverse=True
        )[:n]

    # ── Eviction ─────────────────────────────────────────────

    def _evict_if_needed(self, batch: int = 100) -> None:
        if len(self._memories) <= self._max_memories:
            return
        # Score = importance × recency (simple composite for eviction)
        def eviction_score(m: Memory) -> float:
            import math
            recency = math.exp(-0.693 * m.age_hours / 24.0)
            return m.importance * recency

        self._memories.sort(key=eviction_score, reverse=True)
        self._memories = self._memories[: self._max_memories]
```

### 3.2 Retrieval — Relevância × Recência × Importância

```python
# src/retrieval.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from memory_stream import Memory, MemoryType


@dataclass
class RetrievalWeights:
    alpha: float = 0.40   # relevance
    beta: float = 0.30    # recency
    gamma: float = 0.30   # importance

    def __post_init__(self):
        total = self.alpha + self.beta + self.gamma
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class MemoryRetriever:
    """
    Retrieves memories using a weighted combination of
    relevance (cosine similarity), recency (exponential decay),
    and importance (1–10 scale).