---
name: state-zustand-jotai
description: >-
  Operational skill for lightweight, boilerplate-free state management in React using Zustand and Jotai, persistent storage, and atomic state.
---

# Modern State Management (Zustand & Jotai) Skill

Skill operacional para gerenciamento de estado de cliente sem o overhead ou boilerplate de Redux.

## 1. Padrão Zustand
- Criar stores modulares e exportar seletores para evitar re-renderizações desnecessárias:
  `const user = useUserStore((state) => state.user);`
- Integrar com `persist` middleware para sincronização automática em `localStorage` quando aplicável.
