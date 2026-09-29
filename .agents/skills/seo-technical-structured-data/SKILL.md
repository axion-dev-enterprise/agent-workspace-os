---
name: seo-technical-structured-data
description: >-
  Operational engineering skill for technical SEO optimization, Schema.org JSON-LD structured data, OpenGraph social cards, canonical links, and search indexing signals.
---

# Technical SEO & Structured Data Engineering Skill

Guia operacional para rastreamento, indexabilidade, otimização de snippet rico (Rich Snippets) no Google e metadados de compartilhamento social.

---

## 1. Schema.org JSON-LD (Rich Snippets)

Sempre injete dados estruturados no formato JSON-LD dentro da tag `<head>` para qualificar a página para carrosséis, avaliações em estrelas e cards de software.

### 1.1 Schema para Aplicações Web (SaaS / Ferramentas)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AXION Cloud Console",
  "operatingSystem": "All",
  "applicationCategory": "BusinessApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "publisher": {
    "@type": "Organization",
    "name": "AXION Enterprise",
    "url": "https://example.com"
  }
}
</script>
```

### 1.2 Schema de Breadcrumbs (Navegação)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://example.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Documentação",
      "item": "https://example.com/docs"
    }
  ]
}
</script>
```

---

## 2. Metadados Canônicos e Prevenção de Conteúdo Duplicado

- **URL Canônica Absoluta**: Evite que variações de tracking (`?utm_source=...` ou `?fbclid=...`) fragmentem a autoridade da página:
  ```html
  <link rel="canonical" href="https://example.com/pricing" />
  ```
- **Robots Meta Directives**:
  ```html
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
  ```

---

## 3. Social Cards (OpenGraph & Twitter Card)

Garante previews profissionais ao colar links no Slack, WhatsApp, Twitter/X e LinkedIn:
```html
<meta property="og:type" content="website" />
<meta property="og:title" content="AXION Enterprise — Autonomous Agent Workspace OS" />
<meta property="og:description" content="Infraestrutura corporativa de alta performance para orquestração de IA autônoma." />
<meta property="og:image" content="https://example.com/og-banner.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
```

---

## 4. Ferramental Integrado

Audite páginas estáticas ou saídas de build SSR com o linter de SEO embutido:
```powershell
python .agents/skills/seo-technical-structured-data/scripts/seo_head_auditor.py <arquivo.html-ou-pasta>
```
O linter valida:
- Ausência ou tamanho impróprio de `<title>` (30-65 chars) e `<meta name="description">` (50-160 chars).
- Ausência de URL canônica ou uso incorreto de caminhos relativos.
- Tags OpenGraph essenciais ausentes.
- Blocos JSON-LD sintaticamente inválidos ou sem `@context`/`@type`.
