---
name: web-scraping-crawling
description: >-
  Operational engineering skill for resilient web scraping, crawling architectures, rate-limit defense (HTTP 429), anti-bot header emulation, and structured data extraction (JSON-LD, NEXT_DATA).
---

# Resilient Web Scraping & Crawling Engineering Skill

Guia operacional para extração determinística e resiliente de dados públicos da web, mitigação de rate limits e bloqueios, e engenharia reversa de fontes estruturadas.

---

## 1. Hierarquia de Extração de Dados (Do Mais Robusto ao Mais Frágil)

Ao coletar dados de um website, NUNCA comece selecionando classes CSS geradas aleatoriamente (`div.css-19vja`). Siga a ordem canônica:

1. **APIs Internas Ocultas**: Inspecione as requisições XHR/Fetch no DevTools Network. A maioria dos sites modernos carrega JSON puro de endpoints como `/api/products` ou `/graphql`. Consumir esses endpoints diretamente economiza 95% de computação.
2. **Dados Estruturados Embutidos**:
   - Tags Schema.org: `<script type="application/ld+json">`. Contêm catálogo, preços, descrições e avaliações já limpas e normalizadas.
   - Estado de Frameworks SSR: `<script id="__NEXT_DATA__">` (Next.js) ou `window.__INITIAL_STATE__` (Nuxt/Redux). O payload completo do servidor está presente no HTML inicial.
3. **Metatags Semânticas**: OpenGraph (`og:title`, `og:image`), Twitter Cards e meta tags padrão.
4. **Parsing CSS / XPath**: Utilize atributos de teste (`[data-testid="price"]`) ou semântica HTML5 (`<article>`, `<header>`, `<h1>`). Evite classes de Tailwind hashadas (`class="flex_31xa"`).

---

## 2. Emulação de Headers e Defesa Contra Bloqueios

### 2.1 Conjunto de Headers Realistas
Servidores modernos e WAFs bloqueiam requisições sem os cabeçalhos modernos de Client Hints (`Sec-CH-UA`):
```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
```

### 2.2 Tratamento de Rate-Limit (HTTP 429 & 503)
Implemente recuo exponencial com ruído aleatório (*exponential backoff with jitter*):
```python
wait_seconds = min(60.0, (2 ** attempt) + random.uniform(0.5, 1.5))
time.sleep(wait_seconds)
```

---

## 3. Navegação Headless vs HTTP Direto

> **Regra de Ouro**: Sempre esgote as possibilidades via chamadas HTTP diretas antes de subir um navegador headless Chromium/Playwright.

- **HTTP Direto (curl, requests, urllib)**: Rápido (~100-300ms por página), consome 10MB de RAM, suporta alta concorrência.
- **Headless Browser (Playwright, Puppeteer)**: Pesado (~2-5s por página), consome 300-800MB por aba. Reserve estritamente para páginas que exigem execução de JS em Single Page Apps (SPA) ou interação de clique.

---

## 4. Guardrails e OPSEC (Regras #4 e #5A)

1. **Leitura Pública Apenas**: A extração deve limitar-se a dados disponíveis publicamente. É proibido utilizar credenciais roubadas ou contornar autenticações privadas.
2. **Respeito aos Servidores de Destino**: Limite o paralelismo a taxas civilizadas (máximo de 2 a 5 requisições concorrentes por domínio) para não caracterizar sobrecarga maliciosa.

---

## 5. Ferramental Integrado

Extraia metadados e blocos JSON-LD estruturados de qualquer URL com o scraper resiliente embutido:
```powershell
python .agents/skills/web-scraping-crawling/scripts/resilient_scraper.py https://exemplo.com/produto
```
O script:
- Emula headers reais de navegador desktop.
- Trata HTTP 429 com retry automático e jitter.
- Extrai títulos, metatags, JSON-LD Schema.org e blobs `__NEXT_DATA__`.
