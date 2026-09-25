---
name: web-vitals-performance
description: >-
  Operational skill for optimizing Core Web Vitals (LCP, INP, CLS), bundle size reduction, image optimization, dynamic imports, and Lighthouse audits.
---

# Core Web Vitals & Web Performance Skill

Skill operacional para auditoria e garantia de carregamento instantâneo e nota máxima em Web Vitals.

## 1. Metas Críticas
- **LCP (Largest Contentful Paint)**: < 2.5 segundos. Imagens de herói devem usar `priority` ou `fetchpriority="high"`.
- **INP (Interaction to Next Paint)**: < 200 ms. Evitar travar a main thread com JavaScript pesado; usar `requestIdleCallback` ou web workers.
- **CLS (Cumulative Layout Shift)**: < 0.1. Sempre reservar espaço em disco para imagens, vídeos e anúncios com dimensões explícitas (`aspect-ratio`, `width`, `height`).
