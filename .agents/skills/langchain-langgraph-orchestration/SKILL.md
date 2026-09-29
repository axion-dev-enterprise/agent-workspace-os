---
name: langchain-langgraph-orchestration
description: >-
  Operational engineering skill for building resilient multi-agent architectures with LangGraph, cyclical execution graphs, state persistence, recursion guardrails, and human-in-the-loop checkpoints.
---

# LangGraph Multi-Agent Orchestration Skill

Guia operacional para projeto de sistemas multi-agente determinísticos, grafos cíclicos com roteamento condicional, persistência transacional com checkpointers e validação humana.

---

## 1. Arquitetura de Estado (StateGraph & Reducers)

Todo fluxo no LangGraph deve modelar seu estado compartilhado através de um `TypedDict` rigoroso, utilizando *reducers* explícitos para mensagens acumuladas:

```python
from typing import Annotated, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'operator.add' garante que novas mensagens sejam anexadas à timeline sem sobrescrever o histórico
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_step: str
    requires_approval: bool
    retry_count: int
```

---

## 2. Grafos Cíclicos & Roteamento Condicional

### 2.1 Padrão Agent-Tool Loop
Nunca permita loops infinitos. Estabeleça sempre limites de recursão (`recursion_limit`) e um disjuntor de segurança:

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

workflow = StateGraph(AgentState)

# Definição de Nós
workflow.add_node("agent", call_model_node)
workflow.add_node("tools", ToolNode(tools=[query_db, search_tool]))

# Ponto de entrada
workflow.set_entry_point("agent")

# Roteamento condicional
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if not getattr(last_message, "tool_calls", None):
        return END
    if state.get("retry_count", 0) > 3:
        return "escalate"
    return "tools"

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "escalate": "escalate", END: END}
)

workflow.add_edge("tools", "agent")
```

---

## 3. Checkpointers & Human-in-the-Loop (HITL)

### 3.1 Persistência e Interrupção Controlada
Em produção, utilize `PostgresSaver` ou `RedisSaver` com `thread_id` isolado por sessão/usuário. Interrompa antes de ações mutáveis:

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["tools"] # Pausa o grafo antes de executar ferramentas com efeito externo
)

# Invocação inicial
config = {"configurable": {"thread_id": "session-1029"}, "recursion_limit": 25}
events = app.invoke({"messages": [("user", "Transfira 500 reais para a conta B")]}, config)

# Inspeção do estado pausado
current_state = app.get_state(config)
print("Aguardando confirmação para:", current_state.next)

# Retomada após autorização humana
app.invoke(None, config)
```

---

## 4. Ferramental Integrado

Audite o código-fonte de novos agentes com o analisador topológico embutido:
```powershell
python .agents/skills/langchain-langgraph-orchestration/scripts/graph_state_debugger.py <caminho-do-arquivo.py>
```
O script verifica:
- Presença de ponto de entrada (`set_entry_point`) e nó terminal (`END`).
- Compilação sem checkpointer em fluxos multi-turnos.
- Limites de recursão perigosos que possam causar consumo descontrolado de tokens.
