---
name: tailwind-shadcn-ux
description: >-
  Operational design system and UI/UX skill using Tailwind CSS v4, Radix UI primitives,
  and Shadcn UI patterns. Use whenever developing, styling, or refactoring user interfaces,
  design tokens, dark/light themes, accessible modal dialogs, buttons, forms, and micro-interactions.
---

# Tailwind CSS v4 & Shadcn UI Design System Skill

Skill operacional para arquitetura de interface, design tokens e componentes acessíveis seguindo o padrão moderno de design engineering da **AXION Enterprise**.

---

## 1. Diretrizes de Design & Tokens

- **Framework**: Tailwind CSS v4 com variáveis CSS em `:root` e `.dark`.
- **Cores Semânticas**:
  - `background` / `foreground`
  - `card` / `card-foreground`
  - `primary` / `primary-foreground`
  - `muted` / `muted-foreground`
  - `accent` / `accent-foreground`
  - `destructive` / `destructive-foreground`
  - `border`, `input`, `ring`
- **Acessibilidade**: Contraste WCAG AAA, foco visível (`focus-visible:ring-2 focus-visible:ring-offset-2`), atributos ARIA nativos (`aria-expanded`, `aria-label`).

---

## 2. Padrões de Componentes Essenciais

### 2.1 Botão com Loading State & Microinterações
```tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isLoading || disabled}
        {...props}
      >
        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"
```

### 2.2 Utilitário de Interpolação de Classes (`cn`)
```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

## 3. Heurísticas de UX Aplicadas

1. **Skeleton Loaders**: Nunca deixe a tela vazia sem feedback visual. Utilize componentes `<Skeleton className="h-12 w-full rounded-md" />` enquanto dados são carregados.
2. **Optimistic Updates**: Em mutações rápidas (ex: curtir, favoritar, alternar status), atualize a interface imediatamente antes da resposta do servidor e reverta em caso de erro.
3. **Empty States Educativos**: Telas sem dados devem sempre guiar o usuário com um ícone, título descritivo e botão de ação primária (CTA).
