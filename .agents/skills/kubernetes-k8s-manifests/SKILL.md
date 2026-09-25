---
name: kubernetes-k8s-manifests
description: >-
  Operational skill for Kubernetes and lightweight K3s cluster operations, writing manifests (Deployment, Service, Ingress), HPA autoscaling, and helm charts.
---

# Kubernetes & K3s Orchestration Skill

Skill operacional para orquestração de containers em escala com Kubernetes e K3s.

## 1. Requisitos de Manifesto
- **Resource Requests & Limits**: Todo container DEVE ter `requests` e `limits` explícitos de CPU e memória para evitar *Out-Of-Memory* (OOMKilled) em nós vizinhos.
- **Liveness & Readiness Probes**: Configurar sondas adequadas para reiniciar pods travados e só direcionar tráfego quando a aplicação estiver pronta.
- **SecurityContext**: Forçar `runAsNonRoot: true` e `readOnlyRootFilesystem: true`.
