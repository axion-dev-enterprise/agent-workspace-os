---
name: react-state-architecture
description: >-
  Operational engineering skill for state management in React applications.
  Covers asynchronous server state with TanStack Query v5 (React Query), synchronous client stores
  with Zustand/Jotai, query key factories, optimistic updates, offline caching, and cross-tab sync.
---

# React State Architecture — Master Skill

Skill operacional canonica para design e governanca do estado de aplicacoes React modernas. Unifica a separacao clara entre **Estado de Servidor Assincrono** (TanStack Query) e **Estado de Cliente Sincrono** (Zustand/Jotai).

---

## 1. O Principio da Separacao de Estado

> **"NUNCA DUPLIQUE DADOS DO SERVIDOR EM STORES DE CLIENTE."**

- **Server State (TanStack Query)**: Dados remotos pertencentes ao banco de dados (perfis, faturas, transacoes, produtos). E assincrono, sujeito a latencia, desatualizacao (*stale*) e cache com revalidacao em background.
- **Client State (Zustand)**: Dados locais efemeros da sessao da interface (tema escuro/claro, modais abertos, abas ativas, rascunhos de formularios). E estritamente sincrono e local.

---

## 2. Server State: TanStack Query v5 Best Practices

### 2.1 O Padrao Query Key Factory Obrigatório
Chaves de busca nunca devem ser strings soltas. Use sempre uma fabrica declarativa:
```typescript
export const paymentKeys = {
  all: ['payments'] as const,
  lists: () => [...paymentKeys.all, 'list'] as const,
  list: (filters: { status?: string; merchantId?: string }) =>
    [...paymentKeys.lists(), filters] as const,
  details: () => [...paymentKeys.all, 'detail'] as const,
  detail: (id: string) => [...paymentKeys.details(), id] as const,
};
```

### 2.2 Mutacao com Atualizacao Otimista (Optimistic UI)
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentKeys } from './paymentKeys';

export function useUpdatePaymentStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/payments/${id}`, { status }),
    onMutate: async ({ id, status }) => {
      // 1. Cancela refetches em andamento
      await queryClient.cancelQueries({ queryKey: paymentKeys.detail(id) });
      // 2. Snapshot do estado anterior
      const previous = queryClient.getQueryData(paymentKeys.detail(id));
      // 3. Aplica mudanca otimista imediata
      queryClient.setQueryData(paymentKeys.detail(id), (old: any) => ({ ...old, status }));
      return { previous };
    },
    onError: (err, newTodo, context) => {
      // 4. Rollback seguro em caso de falha de rede
      queryClient.setQueryData(paymentKeys.detail(newTodo.id), context?.previous);
    },
    onSettled: (data, error, variables) => {
      // 5. Invalida para sincronizacao garantida
      queryClient.invalidateQueries({ queryKey: paymentKeys.detail(variables.id) });
    },
  });
}
```

---

## 3. Client State: Zustand Stores Deterministicas

### 3.1 Store Modular sem Boilerplate com Middleware de Persistencia
```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface UiState {
  isSidebarOpen: boolean;
  activeTab: string;
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      activeTab: 'overview',
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    {
      name: 'axion-ui-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
```

### 3.2 Anti-Padrão: Seletores Globais sem Isolamento
- **Errado**: `const { isSidebarOpen } = useUiStore();` (Re-renderiza o componente em qualquer mutacao da store).
- **Correto**: `const isSidebarOpen = useUiStore((state) => state.isSidebarOpen);` (Seletor atomico, so renderiza quando a propriedade muda).

---

## 4. Portão de Verificação (Verification Gate)

1. Nenhum dado do servidor armazenado em `localStorage` sem chave de TTL ou versao de schema.
2. Toda chamada de API deve estar envelopada em um hook TanStack Query com query keys declarativas.
3. Testes unitarios com `@tanstack/react-query` devem prover um `QueryClient` isolado em `beforeEach()` para evitar vazamento de cache entre suites de teste.