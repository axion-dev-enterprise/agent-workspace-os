---
name: sentry-error-tracking
description: >-
  Operational engineering skill for Sentry SDK instrumentation, frontend/backend error grouping, release tracking, PII sanitization via beforeSend hooks, and distributed tracing.
---

# Sentry Error Monitoring & Distributed Tracing Skill

Guia operacional para instrumentação de observabilidade de erros, agrupamento determinístico de exceções, sanitização estrita de dados sensíveis (PII) e rastreamento de releases em produção.

---

## 1. Diretrizes de Sanitização de PII (Regra #4)

Nunca permita que senhas, tokens de autorização ou dados pessoais alcancem a nuvem do Sentry.

### 1.1 Configuração Segura em TypeScript / Node.js
```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  sendDefaultPii: false, // Desativar para não capturar IPs ou dados de SO inadvertidamente
  tracesSampleRate: 0.1, // Amostragem controlada para evitar custos excessivos
  beforeSend(event, hint) {
    // 1. Sanitizar Headers HTTP sensíveis
    if (event.request?.headers) {
      delete event.request.headers["authorization"];
      delete event.request.headers["cookie"];
      delete event.request.headers["x-api-key"];
    }

    // 2. Sanitizar query params com chaves sensíveis
    if (event.request?.query_string && typeof event.request.query_string === "string") {
      event.request.query_string = event.request.query_string.replace(
        /(token|key|password|secret)=([^&]+)/gi,
        "$1=[FILTERED]"
      );
    }

    return event;
  },
});
```

### 1.2 Configuração Segura em Python / FastAPI
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def filter_sentry_events(event, hint):
    request = event.get("request", {})
    headers = request.get("headers", {})
    for key in ("authorization", "cookie", "x-api-key"):
        if key in headers:
            headers[key] = "[FILTERED]"
    return event

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    send_default_pii=False,
    traces_sample_rate=0.05,
    before_send=filter_sentry_events,
)
```

---

## 2. Rastreamento de Release & Source Maps

### 2.1 Associação de Versões
Vincule sempre a versão do release ao commit Git para identificar com precisão quando um bug foi introduzido:
```bash
export SENTRY_RELEASE=$(git rev-parse HEAD)
```

### 2.2 Upload de Source Maps sem Exposição Pública
Configure o plugin oficial `@sentry/nextjs` ou `@sentry/vite-plugin` no pipeline de CI/CD para:
1. Gerar mapas de código durante o build.
2. Fazer upload para o Sentry via CLI autenticada com token do vault.
3. Excluir imediatamente os arquivos `.map` do diretório final de distribuição antes do deploy em servidores de borda.

---

## 3. Fingerprinting e Agrupamento Customizado

Evite que alertas repetitivos de serviços externos (ex: indisponibilidade transitória de gateways de pagamento) poluam os dashboards de incidentes:

```typescript
if (error instanceof UpstreamGatewayTimeoutError) {
  Sentry.withScope((scope) => {
    scope.setFingerprint(["upstream-gateway-timeout", error.providerName]);
    Sentry.captureException(error);
  });
}
```

---

## 4. Ferramental Integrado

Utilize o utilitário Python embutido para auditar arquivos de configuração do Sentry ou inspecionar a sanitização de payloads:
```powershell
# Auditar arquivo de configuração
python .agents/skills/sentry-error-tracking/scripts/sentry_pii_guard.py check-config sentry.client.config.ts

# Testar sanitização de payload de erro
python .agents/skills/sentry-error-tracking/scripts/sentry_pii_guard.py test-payload event.json
```
