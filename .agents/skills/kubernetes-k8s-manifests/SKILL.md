---
name: kubernetes-k8s-manifests
description: >-
  Operational engineering skill for Kubernetes and lightweight K3s cluster operations, writing production-grade manifests (Deployment, Service, Ingress, NetworkPolicy), HPA autoscaling, rolling updates, and PodDisruptionBudgets.
---

# Kubernetes & K3s Manifest Engineering Skill

Guia operacional para arquitetura, validação, hardening e sustentação de workloads em clusters Kubernetes (K8s) e distribuições leves de borda (K3s).

---

## 1. Regras Mandatórias de Workloads em Produção

### 1.1 Disciplina de Recursos (QoS Classes)
- **Requests & Limits Obrigatórios**: Todo container DEVE declarar `resources.requests` e `resources.limits`.
  - CPU: declare requests baseados no perfil mediano P50; limite para conter threads descontroladas.
  - Memória: defina `requests.memory == limits.memory` para obter a classe de qualidade de serviço **Guaranteed QoS**, eliminando o risco de expulsão silenciosa (OOMKill) por nós sobrecarregados.
- **Anti-Pattern Evitado**: Nunca deixe containers sem limites de memória em clusters multi-tenant.

### 1.2 Ciclo de Vida & Probes
- **Startup Probe**: Obrigatória para serviços Java/Node.js/Python com warm-up lento (ex: compilação JIT ou carregamento de modelos de IA). Evita que o pod seja reiniciado prematuramente pelo liveness probe.
- **Readiness Probe**: Verifica se a aplicação está pronta para receber tráfego HTTP/gRPC. Em caso de falha temporária, o pod é removido dos Endpoints do Service sem reinicialização.
- **Liveness Probe**: Verifica se o processo travou em deadlock. Deve usar endpoint ultraleve (`/livez` ou ping de socket), nunca executar consultas pesadas a banco de dados.
- **PreStop Hook & TerminationGracePeriodSeconds**: Envie sinal de drenagem antes de encerrar o pod para concluir requisições em voo:
  ```yaml
  lifecycle:
    preStop:
      exec:
        command: ["/bin/sh", "-c", "sleep 10"]
  terminationGracePeriodSeconds: 45
  ```

### 1.3 Hardening & Security Context
- Imponha privilégios mínimos no nível de Pod e Container:
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
  ```

---

## 2. Estratégias de Deploy & Resiliência

### 2.1 Rolling Updates Zero-Downtime
Configure a política de atualização controlada:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 0
```

### 2.2 PodDisruptionBudget (PDB)
Garante que manutenções do cluster (drenagem de nós, upgrades do K8s) não derrubem o serviço:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: enterprise-api
```

### 2.3 Horizontal Pod Autoscaler (HPA v2)
Escale automaticamente baseado em métricas de CPU e requisições concorrentes:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: enterprise-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 3. Otimizações para K3s (Borda & Nodes Locais)

1. **Storage Local**: Utilize o StorageClass padrão `local-path` para persistência em disco NVMe direto do nó.
2. **Desativação de Componentes Embutidos**: Se estiver usando NGINX Ingress externo ou Cloudflare Tunnel, suba o cluster K3s com flags de isolamento:
   ```bash
   curl -sfL https://get.k3s.io | sh -s - --disable traefik --disable servicelb
   ```
3. **Kubeconfig Local**: Obtenha e configure as credenciais sem permissões excessivas:
   ```powershell
   # Em ambiente Windows com nó remoto
   scp user@node:/etc/rancher/k3s/k3s.yaml $HOME\.kube\config
   # Ajuste o server IP de 127.0.0.1 para o IP do nó
   ```

---

## 4. Ferramental Integrado

Execute a auditoria automatizada de conformidade de manifestos com o script Python embutido:
```powershell
python .agents/skills/kubernetes-k8s-manifests/scripts/k8s_manifest_linter.py <caminho-ou-pasta>
```
O linter valida:
- Ausência de resource requests e limits.
- Sondas ausentes (liveness e readiness).
- Execução como root ou filesystem gravável.
- Tags mutáveis (`:latest` ou imagens sem digest/semver).
