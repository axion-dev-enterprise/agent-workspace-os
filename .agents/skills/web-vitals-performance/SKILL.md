---
name: web-vitals-performance
description: >-
  Operational engineering skill for optimizing Core Web Vitals (LCP, INP, CLS = 0), code-splitting, tree-shaking, font metrics override, and Lighthouse 100/100 performance budgets.
---

# Core Web Vitals & Web Performance Engineering Skill

Guia operacional para auditoria profunda e otimização de performance no front-end moderno. Garante nota máxima no Google Lighthouse, carregamento perceptível instantâneo e layout shifts nulos.

---

## 1. As Três Métricas Centrais (Golden Web Vitals)

### 1.1 Largest Contentful Paint (LCP < 2.5s)
Mede quando o maior bloco visível na viewport (imagem de hero, banner ou título h1 principal) termina de renderizar:
- **Eager Loading para Heros**: O maior elemento da tela NUNCA deve conter `loading="lazy"`. Utilize `priority` (no Next.js) ou `fetchpriority="high"` (em HTML puro).
- **Preload de Imagens Críticas**:
  ```html
  <link rel="preload" as="image" href="/hero.webp" type="image/webp" fetchpriority="high" />
  ```
- **Compressão de Próxima Geração**: Converta todas as imagens estáticas para WebP ou AVIF, reduzindo o payload em 60-80% em relação a JPEG/PNG.

### 1.2 Cumulative Layout Shift (CLS < 0.1, Meta AXION = 0.0)
Mede a instabilidade visual de elementos se movendo na tela durante o carregamento:
- **Reserva Explícita de Espaço**: Todo `<img>`, `<video>` e `<iframe>` DEVE declarar dimensões em atributos ou CSS:
  ```html
  <img src="/logo.webp" width="240" height="60" style="aspect-ratio: 4 / 1;" alt="Logo" />
  ```
- **Skeleton Shimmers Exatos**: Quando exibir skeletons antes de carregar dados via API, o container deve ter a mesma altura e padding do componente final (Regra #7).
- **Font Display sem Shift**: Use `font-display: swap` com fallbacks ajustados por métricas (`size-adjust`, `ascent-override`):
  ```css
  @font-face {
    font-family: 'Inter Fallback';
    src: local('Arial');
    ascent-override: 90%;
    descent-override: 22%;
    size-adjust: 107%;
  }
  ```

### 1.3 Interaction to Next Paint (INP < 200ms)
Mede a responsividade da interface quando o usuário clica ou digita:
- **Quebra de Tarefas Longas (Long Tasks > 50ms)**: Utilize `scheduler.yield()` ou `setTimeout(..., 0)` para ceder a execução à main thread do browser entre cálculos pesados.
- **Transições com `useTransition` no React**: Mantenha a entrada do usuário fluida enquanto renderizações não urgentes acontecem em segundo plano:
  ```tsx
  const [isPending, startTransition] = useTransition();
  function handleFilter(term: string) {
    setSearchInput(term); // Atualização urgente do input
    startTransition(() => {
      setFilteredItems(filterLargeList(term)); // Atualização secundária não-bloqueante
    });
  }
  ```

---

## 2. Otimização de Bundles e Code Splitting

- **Dynamic Imports**: Carregue bibliotecas pesadas (gráficos, editores de markdown, renderizadores 3D) sob demanda apenas quando visíveis na tela:
  ```tsx
  import dynamic from 'next/dynamic';
  const ChartComponent = dynamic(() => import('@/components/AnalyticsChart'), {
    ssr: false,
    loading: () => <div className="h-64 rounded-xl bg-zinc-900 animate-pulse" />,
  });
  ```
- **Proibição de Wildcard Imports**: Nunca faça `import * as icons from 'lucide-react'`. Isso carrega centenas de kilobytes no bundle inicial em vez de incluir apenas o SVG necessário.

---

## 3. Ferramental Integrado

Audite o código-fonte de interfaces antes de deploys para prevenir regressões de CLS, LCP e tamanho de bundle:
```powershell
python .agents/skills/web-vitals-performance/scripts/web_vitals_linter.py <pasta-frontend>
```
O linter valida:
- Imagens sem dimensões explícitas (`width`/`height`/`aspect-ratio`).
- Imagens de herói configuradas incorretamente com `loading="lazy"`.
- Imports corrompendo tree-shaking com pacotes de ícones.
