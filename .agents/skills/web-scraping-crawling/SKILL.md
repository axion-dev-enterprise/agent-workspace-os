---
name: web-scraping-crawling
description: >-
  Operational skill for resilient web scraping, crawling architectures, bypassing Cloudflare/bot protections, HTML parsing, and structured data extraction.
---

# Resilient Web Scraping & Crawling Skill

Skill operacional para ingestão de dados da web, navegação automatizada e parsing estruturado.

## 1. Diretrizes de Resiliência
- **Headers Realistas**: Enviar sempre `User-Agent`, `Accept-Language` e cabeçalhos `Sec-CH-UA` idênticos aos de um navegador Chrome real.
- **Tratamento de Rate-Limit (429)**: Implementar espera exponencial (*exponential backoff com jitter*) quando o servidor remoto solicitar espera.
- **Extração Semântica**: Priorizar dados estruturados JSON-LD (`<script type="application/ld+json">`) na página antes de fazer parsing manual de seletores CSS voláteis.
