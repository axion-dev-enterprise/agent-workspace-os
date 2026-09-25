---
name: nextjs-app-router-rsc
description: >-
  Operational skill for Next.js 15 App Router architecture, React Server Components (RSC), Server Actions, partial prerendering, and streaming.
---

# Next.js 15 App Router & RSC Skill

Skill operacional para arquitetura de aplicações web modernas com Next.js 15, Server Components e Server Actions.

## 1. Diretrizes Fundamentais
1. **Server por Padrão**: Todos os componentes devem ser React Server Components por padrão. Adicione `"use client"` apenas quando houver `useState`, `useEffect`, ou listeners de eventos no navegador.
2. **Server Actions com Validação**: Server Actions devem sempre validar o payload recebido com Zod e verificar a autenticação da sessão.
3. **Streaming com Suspense**: Isole partes dinâmicas e demoradas da tela com `<Suspense fallback={<Skeleton />}>` para não bloquear a renderização inicial.
