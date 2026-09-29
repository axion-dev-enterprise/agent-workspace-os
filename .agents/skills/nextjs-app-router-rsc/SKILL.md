---
name: nextjs-app-router-rsc
description: >-
  Operational engineering skill for Next.js 15 App Router, React Server Components (RSC),
  Server Actions, dynamic streaming, cache revalidation strategies, and zero-bundle server boundaries.
---

# Next.js 15 App Router & React Server Components — Master Engineering Skill

Skill operacional canonica para arquitetura, desenvolvimento e auditoria de aplicacoes corporativas em **Next.js 15**. Cobre a separacao deterministica entre Server e Client Components, mutacoes seguras via Server Actions, streaming com Suspense, e gestao avancada de cache.

---

## 1. Topologia de Componentes: Server vs. Client Boundaries

### 1.1 O Principio "Server-First" (Zero Client Bundle)
No App Router (`app/`), **todos os componentes sao React Server Components (RSC) por padrao**.
- Componentes de Servidor executam exclusivamente no Node.js/Edge Runtime durante o build ou na requisicao.
- Seu codigo e suas dependencias (Prisma, SQL, bibliotecas de markdown, segredos de ambiente) **nunca** sao enviados ao navegador.
- O resultado e transmitido ao cliente em formato binario estruturado (RSC Payload), garantindo **0 KB de JavaScript adicional** no bundle.

### 1.2 Quando Adicionar `"use client"`?
Adicione a diretiva `'use client'` estritamente no topo de folhas de componente (*leaf components*) que necessitem de:
1. Hooks de estado ou ciclo de vida do React (`useState`, `useEffect`, `useReducer`, `useMemo`, `useCallback`).
2. Ouvintes de eventos do DOM (`onClick`, `onChange`, `onSubmit`, `onKeyDown`).
3. APIs exclusivas do navegador (`window`, `localStorage`, `navigator.geolocation`, `canvas`).
4. Context Providers de cliente (Theme, AuthContext de UI).

> **Regra de Ouro da Fronteira**: Empurre `'use client'` para o ponto mais profundo possivel da arvore. Nunca marque uma pagina (`page.tsx`) ou layout (`layout.tsx`) inteira com `'use client'`.

---

## 2. Server Actions: Mutacoes Seguras e Validacao Estrita

Server Actions sao endpoints RPC assincronos executados no servidor com protecao nativa contra CSRF.

### 2.1 Padrao Canônico de Server Action com Zod e Autenticacao
```typescript
'use server';

import { z } from 'zod';
import { revalidatePath, revalidateTag } from 'next/cache';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';

const CreateInvoiceSchema = z.object({
  customerId: z.string().uuid(),
  amountCents: z.number().int().positive(),
  dueDate: z.string().datetime(),
});

export type ActionResponse<T> =
  | { success: true; data: T }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function createInvoiceAction(
  prevState: any,
  formData: FormData
): Promise<ActionResponse<{ id: string }>> {
  // 1. Verificacao de Autenticacao & Tenant
  const session = await auth();
  if (!session?.userId) {
    return { success: false, error: 'Nao autorizado.' };
  }

  // 2. Validacao de Schema com Zod
  const rawData = Object.fromEntries(formData.entries());
  const parsed = CreateInvoiceSchema.safeParse({
    ...rawData,
    amountCents: Number(rawData.amountCents),
  });

  if (!parsed.success) {
    return {
      success: false,
      error: 'Dados invalidos.',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  // 3. Mutacao no Banco de Dados
  try {
    const invoice = await db.invoice.create({
      data: {
        ...parsed.data,
        merchantId: session.merchantId,
        status: 'PENDING',
      },
    });

    // 4. Revalidacao Granular de Cache
    revalidateTag(`invoices-${session.merchantId}`);
    revalidatePath('/dashboard/invoices');

    return { success: true, data: { id: invoice.id } };
  } catch (err: any) {
    return { success: false, error: 'Falha ao persistir fatura no banco de dados.' };
  }
}
```

---

## 3. Estrategias de Cache e Revalidacao no Next.js 15

Next.js 15 adota `no-store` por padrao para chamadas de `fetch` nao configuradas, eliminando armadilhas de dados obsoletos.

### 3.1 Niveis de Cache
- **Request Memoization**: Desduplicacao automatica de chamadas `fetch` identicas dentro da mesma arvore de renderizacao de uma unica requisicao.
- **Data Cache**: Cache persistente entre requisicoes de multiplos usuarios. Configure via `fetch(url, { next: { revalidate: 3600, tags: ['products'] } })`.
- **Full Route Cache**: Paginas estaticas pre-renderizadas no build (SSG). Tornam-se dinamicas se utilizarem funcoes dinamicas (`cookies()`, `headers()`, `searchParams`).

### 3.2 Cache em Consultas de Banco Diretas com `unstable_cache`
Quando nao utilizar `fetch` (ex: Prisma, Drizzle ou SQL puro), utilize `unstable_cache`:
```typescript
import { unstable_cache } from 'next/cache';
import { db } from '@/lib/db';

export const getMerchantMetrics = (merchantId: string) =>
  unstable_cache(
    async () => {
      return await db.metrics.findUnique({ where: { merchantId } });
    },
    ['merchant-metrics', merchantId],
    {
      revalidate: 60, // 60 segundos
      tags: [`metrics-${merchantId}`],
    }
  )();
```

---

## 4. Streaming com `<Suspense>` e Zero Cumulative Layout Shift (CLS = 0)

Nunca bloqueie a pagina inteira aguardando consultas lentas de analytics ou integracoes de terceiros.

```tsx
import { Suspense } from 'react';
import { MetricsOverview } from './components/MetricsOverview';
import { RecentTransactions } from './components/RecentTransactions';
import { MetricsSkeleton, TransactionsSkeleton } from './components/Skeletons';

export default function DashboardPage() {
  return (
    <div className="space-y-8 p-6">
      <h1 className="text-2xl font-bold">Painel Financeiro</h1>

      {/* Secao 1: Carrega rapido */}
      <Suspense fallback={<MetricsSkeleton />}>
        <MetricsOverview />
      </Suspense>

      {/* Secao 2: Streaming assincrono independente */}
      <Suspense fallback={<TransactionsSkeleton />}>
        <RecentTransactions />
      </Suspense>
    </div>
  );
}
```

---

## 5. Auditor CLI Standalone (`scripts/audit_rsc_boundaries.py`)

A skill inclui um auditor estatico em Python stdlib para inspecionar aplicacoes Next.js:

```bash
# Auditar arvore App Router em busca de vazamento de segredos e 'use client' desnecessario
python .agents/skills/nextjs-app-router-rsc/scripts/audit_rsc_boundaries.py --dir apps/webapp

# Saida estruturada para integracao com pipelines CI/CD
python .agents/skills/nextjs-app-router-rsc/scripts/audit_rsc_boundaries.py --dir apps/webapp --json
```

---

## 6. Portão de Verificação (Verification Gate)

Antes de aprovar qualquer PR ou deploy em Next.js:
1. `npm run build` deve compilar com 0 erros de tipo em TypeScript.
2. Nenhuma rota dinamica que exija autenticacao deve vazar no bundle estatico de SSG (indicado pelo circulo vazio `○` vs lambda `ƒ` no output do build).
3. O script `audit_rsc_boundaries.py` deve retornar 0 violacoes criticas de segredos em arquivos com `'use client'`.
