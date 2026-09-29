---
name: prometheus-grafana-metrics
description: >-
  Operational engineering skill for metrics exposition with Prometheus client, PromQL queries, cardinality management, Golden Signals (RED/USE), and Grafana alert routing.
---

# Prometheus & Grafana Observability Engineering Skill

Guia operacional para instrumentação de métricas em serviços de alta performance, elaboração de consultas PromQL resilientes, prevenção de explosão de cardinalidade e alertas acionáveis.

---

## 1. Golden Signals & Metodologias Canônicas

### 1.1 Método RED (Para Microserviços e APIs HTTP/gRPC)
1. **Rate (Taxa)**: Número de requisições por segundo.
   ```promql
   sum(rate(http_requests_total{job="api-gateway"}[2m])) by (method, route)
   ```
2. **Errors (Erros)**: Taxa de falhas do servidor (5xx).
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[2m])) / sum(rate(http_requests_total[2m])) * 100
   ```
3. **Duration (Duração/Latência)**: Distribuição percentil em histogramas.
   ```promql
   # Percentil 95 (P95)
   histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, route))
   ```

### 1.2 Método USE (Para Infraestrutura e Servidores)
1. **Utilization**: Percentual de tempo em que o recurso esteve ocupado (`100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)`).
2. **Saturation**: Fila de espera ou memória swap (`node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes`).
3. **Errors**: Contadores de pacotes dropados em rede ou falhas de I/O em disco.

---

## 2. Tipos Canônicos de Métricas

- **Counter**: Valor monotonicamente crescente (ex: `http_requests_total`, `tasks_completed_total`). Nunca decresce, exceto no reinício do processo.
- **Gauge**: Instantâneo de valor instantâneo (ex: `active_connections`, `memory_bytes_in_use`, `bullmq_queue_waiting_jobs`). Pode subir e descer livremente.
- **Histogram**: Amostragem de observações particionadas em baldes (`le`). Sempre use sufixo de unidade no nome (`_seconds`, `_bytes`).

---

## 3. Prevenção de Explosão de Cardinalidade (Anti-Pattern Crítico)

> **Regra de Ouro**: A cardinalidade de uma métrica é a multiplicação do número de valores únicos de todos os seus labels.
> `10 métodos × 20 rotas × 5 status = 1.000 séries temporais (Saudável)`
> `10 métodos × 100.000 user_ids = 1.000.000 séries (Crash Imediato do TSDB)`

- **Proibido em Labels**:
  - IDs de usuários (`user_id`), e-mails, números de CPF/telefone.
  - IDs de pedidos ou transações (`order_id`, `payment_id`).
  - Tokens, UUIDs arbitrários, hashes de commit ou timestamps.
- **Permitido em Labels**:
  - Códigos de status HTTP canônicos (`200`, `400`, `500`).
  - Métodos HTTP (`GET`, `POST`, `PUT`, `DELETE`).
  - Padrões de rotas parametrizadas (`/users/:id`, NUNCA `/users/12345`).
  - Nomes de serviços ou ambientes (`prod`, `staging`).

---

## 4. Alertas Acionáveis no Alertmanager

Configure alertas focados em sintomas reais de usuários, não ruídos transitórios:
```yaml
groups:
  - name: api_slo_alerts
    rules:
      - alert: HighHttp5xxErrorRate
        expr: (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taxa de erro HTTP 5xx acima de 5% no serviço {{ $labels.job }}"
          runbook_url: "https://docs.example.com/runbooks/http-5xx"
```

---

## 5. Ferramental Integrado

Audite o código-fonte de novos serviços ou endpoints ao vivo contra etiquetas de alta cardinalidade:
```powershell
# Escanear código-fonte
python .agents/skills/prometheus-grafana-metrics/scripts/metrics_cardinality_guard.py scan-code services/

# Checar endpoint de métricas exposto
python .agents/skills/prometheus-grafana-metrics/scripts/metrics_cardinality_guard.py check-endpoint http://localhost:9090/metrics
```
