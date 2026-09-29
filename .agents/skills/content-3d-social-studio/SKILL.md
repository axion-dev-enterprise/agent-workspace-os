---
name: content-3d-social-studio
description: >-
  Produces reusable 3D web experiences and social-media creative workflows with Three.js, Canva, Runway, and Windsor.ai. Use for campaign assets, social formats, 3D landing-page motion, or approved publishing and ads operations.
---

# Content 3D & Social Studio Skill

Guia operacional para produção de assets criativos multimídia, experiências web 3D imersivas com Three.js e esteiras de publicação em redes sociais e plataformas de anúncios.

---

## 1. Roteamento de Solicitações Criativas

- **Cenas Web 3D & Modelos GLTF/GLB**: Consulte [Three.js snippets](references/threejs-snippets.md). Priorize cenas delimitadas, responsivas e com fallback acessível em HTML/CSS para navegadores sem aceleração gráfica.
- **Formatos Sociais & Templates**: Consulte [creative templates](references/creative-templates.md). Inicie sempre pelo briefing de campanha e gere entregáveis inspecionáveis antes de qualquer exportação ou consumo de créditos.
- **Automação de Anúncios e Analytics**: Utilize conectores homologados (Meta/Google Ads via Windsor.ai) apenas após autorização explícita e confirmação de IDs de conta pelo usuário.

---

## 2. Regras Operacionais e Guardrails

1. **Briefing Mandatório**: Declare o formato de entrega, plataformas de destino, proporções de tela (`1:1` Feed, `9:16` Stories/Reels, `16:9` Vídeo Horizontal), limites de marca e Call to Action (CTA) antes de gerar o asset.
2. **Ciclo de Vida Three.js & Desalocação**: No React/Three.js, utilize CSS para definir as dimensões de exibição. No desmonte do componente (`unmount`), invoque obrigatoriamente `.dispose()` em geometrias, materiais, texturas e controles para eliminar vazamentos de memória na GPU.
3. **Formatos 3D Canônicos**: Utilize formatos binários `.glb` com compressão Draco/Meshopt. Mantenha os créditos de licença e atribuição acompanhando o projeto.
4. **Respeito a Créditos em IA Generativa**: Antes de acionar geração de imagens ou vídeos (Canva/Runway), confirme o saldo e obtenha aprovação do operador humano, tratando o gasto como ação financeira de mutação externa (Regra #5A).
5. **Prevenção de Emojis em UI (Regra #6)**: NUNCA utilize emojis em botões, topbars ou legendas de interfaces interativas; use exclusivamente ícones vetoriais SVG profissionais.

---

## 3. Matriz de Proporções e Formatos de Exportação

| Plataforma | Finalidade | Aspect Ratio | Resolução Recomendada |
| :--- | :--- | :--- | :--- |
| **Instagram / TikTok** | Reels / Stories | `9:16` | 1080 x 1920 px |
| **Instagram / LinkedIn** | Post no Feed | `1:1` ou `4:5` | 1080 x 1080 px / 1080 x 1350 px |
| **YouTube / Web Desktop** | Vídeo / Hero Banner | `16:9` | 1920 x 1080 px |
| **Twitter / X** | Card de Compartilhamento | `1.91:1` | 1200 x 630 px |

---

## 4. Portão de Qualidade (Quality Gate)

- **Acessibilidade 3D**: Suporte a `@media (prefers-reduced-motion: reduce)` para pausar rotações contínuas de câmera.
- **Performance Mobile**: Limitar a taxa de quadros e complexidade de polígonos em telas de baixa densidade gráfica.
- **Zero Layout Shift**: Espaço em tela estritamente reservado antes do carregamento do canvas WebGL.

---

## 5. Ferramental Integrado

Audite arquivos de código de cenas Three.js e specs com o verificador embutido:
```powershell
python .agents/skills/content-3d-social-studio/scripts/asset_specs_linter.py <pasta-ou-arquivo>
```
O linter verifica:
- Falta de `.dispose()` em objetos WebGL e Three.js.
- Ausência de tratamento para `prefers-reduced-motion`.
