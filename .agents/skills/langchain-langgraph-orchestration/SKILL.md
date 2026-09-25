---
name: langchain-langgraph-orchestration
description: >-
  Operational skill for building complex multi-agent architectures with LangGraph, cyclical execution graphs, state persistence, and human-in-the-loop validation.
---

# LangGraph & Multi-Agent Orchestration Skill

Skill operacional para arquitetura de agentes autônomos baseados em grafos de estado.

## 1. Conceitos Chave
- **StateGraph**: O estado da conversa/tarefa é compartilhado entre nós (`Nodes`) através de canais imutáveis.
- **Roteamento Condicional**: Arestas condicionais determinam o próximo passo com base no output do modelo (ex: chamar ferramenta vs responder ao usuário).
- **Checkpointers**: Permite pausar a execução, solicitar aprovação humana (*human-in-the-loop*) e retomar exatamente do mesmo ponto.
