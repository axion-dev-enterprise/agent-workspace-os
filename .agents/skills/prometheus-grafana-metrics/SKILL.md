---
name: prometheus-grafana-metrics
description: >-
  Operational skill for observability, metric exposition with Prometheus client, PromQL queries, Grafana dashboards, and Alertmanager routing.
---

# Prometheus & Grafana Observability Skill

Skill operacional para telemetria, instrumentação de métricas e monitoramento de saúde de sistemas.

## 1. Método RED (Para Serviços Web)
- **Rate**: Quantidade de requisições por segundo (`sum(rate(http_requests_total[1m]))`).
- **Errors**: Quantidade de falhas HTTP 5xx (`sum(rate(http_requests_total{status=~"5.."}[1m]))`).
- **Duration**: Tempo de resposta em percentis P95 e P99 via histogramas.
