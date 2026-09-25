---
name: grpc-protobuf-microservices
description: >-
  Operational skill for high-throughput inter-service RPC communication using gRPC, Protocol Buffers (.proto contracts), streaming, and deadliness.
---

# gRPC & Protocol Buffers Microservices Skill

Skill operacional para comunicação de baixíssima latência e alta taxa de transferência entre microsserviços.

## 1. Princípios
- **Contratos Claros**: Schemas `.proto` versionados de forma compatível retroativamente (nunca alterar números de campo já publicados).
- **Deadlines**: Toda chamada RPC DEVE definir um timeout/deadline explícito para evitar travamento em cascata.
- **Multiplexação HTTP/2**: Reutilizar canais gRPC criados em vez de criar novas conexões a cada requisição.
