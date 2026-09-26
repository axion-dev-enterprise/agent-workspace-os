---
name: modern-responsive-architect
description: >-
  Operational skill for modern responsive layout engineering, CSS Grid, Subgrid, Container Queries,
  fluid clamp typography, safe area insets, and dynamic viewport handling (dvh/svh).
  Use whenever fixing mobile layout bugs, adapting dashboards to multiple screen ratios,
  preventing horizontal overflows, and creating mobile-first web experiences.
---

# Modern Responsive Layout Architect Skill

Skill operacional para construção de layouts responsivos determinísticos, eliminação de rolagem horizontal indesejada e suporte perfeito a qualquer resolução de tela para a **Enterprise Organization**.

---

## 1. Regras de Ouro da Responsividade Moderna

1. **Nunca use `100vh` em mobile**: Sempre utilize `100dvh` (*dynamic viewport height*) ou `100svh` para evitar que a barra de endereços do Safari/Chrome mobile corte botões na parte inferior da tela.
2. **Container Queries sobre Media Queries**: Estilize componentes com base no espaço disponível no seu próprio container pai (`@container (min-width: 400px)`), permitindo que o mesmo card funcione tanto na sidebar quanto na área principal.
3. **Tipografia Fluida sem Breakpoints Rígidos**: Use funções `clamp()` para fontes que escalam suavemente entre mobile e desktop:
   `font-size: clamp(1rem, 0.8rem + 1vw, 2.5rem);`
4. **Tratamento de Notches e Ilhas Dinâmicas**:
   Sempre incluir suporte a `env(safe-area-inset-bottom)` e `env(safe-area-inset-top)` em barras de navegação fixas.

---

## 2. Padrões CSS Canônicos

### 2.1 CSS Grid Auto-Fit Fluido (Adeus Media Queries para Grids)
```css
.responsive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 1.5rem;
}
```

### 2.2 Container Queries Modernas no Tailwind CSS
```html
<div class="@container">
  <div class="flex flex-col @md:flex-row items-center gap-4 p-4">
    <img class="w-full @md:w-32 rounded-lg" src="/thumb.jpg" alt="" />
    <div class="flex-1">
      <h3 class="text-base @md:text-xl font-bold">Título Adaptativo</h3>
      <p class="hidden @lg:block text-muted-foreground">Descrição detalhada exibida apenas quando o container for grande.</p>
    </div>
  </div>
</div>
```

### 2.3 Prevenção contra Quebra de Texto Deselegante
```css
h1, h2, h3 {
  text-wrap: balance; /* Evita palavras órfãs em títulos */
}

p {
  text-wrap: pretty; /* Melhora a quebra de linha em parágrafos longos */
}
```
