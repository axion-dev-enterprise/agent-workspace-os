# 🧠 Plano de Implementação: Conversational First Content Streaming
**Arquitetura 100% Orientada à LLM (Zero Heurísticas, Zero Regex, Sem Mapeamentos Estáticos)**

---

## 📌 Visão Executiva

Este plano detalha a reestruturação da comunicação do **Co-piloto Autônomo AXION** para adotar o padrão de interação conversacional moderna (estilo Codex / ChatGPT), eliminando tempos de silêncio perceptíveis e mensagens mecânicas.

### A Regra Fundamental:
> **A inteligência é 100% generativa de ponta a ponta.**  
> É terminantemente proibido utilizar fallbacks determinísticos, heurísticas estáticas, dicionários de intenção ou regex para formular conteúdos. A própria LLM formula a contextualização e abordagem do pedido em tempo real via streaming.

---

## 📂 Estrutura de Documentos do Plano

| Documento | Descrição |
| :--- | :--- |
| **[`01_ARQUITETURA_E_CONCEITO.md`](./01_ARQUITETURA_E_CONCEITO.md)** | Visão geral da arquitetura, fluxo de tokens e comparação de experiência de usuário. |
| **[`02_ESPECIFICACAO_TECNICA.md`](./02_ESPECIFICACAO_TECNICA.md)** | Especificação do leitor SSE de streaming, buffering de sentenças e integração com OpenRouter. |
| **[`03_INTEGRACAO_CANAIS.md`](./03_INTEGRACAO_CANAIS.md)** | Comportamento específico para os canais WhatsApp (resposta antecipada) e Telegram (cabeçalho dinâmico). |
| **[`04_CRITERIOS_DE_ACEITE_E_TESTES.md`](./04_CRITERIOS_DE_ACEITE_E_TESTES.md)** | Métricas de TTFT esperadas, casos de teste reais, resiliência e validação. |

---

## 🎯 Meta de Latência (TTFT)
- **Time To First Token (TTFT):** $\le 500\text{ms}$
- **Disparo do First Content Útil:** $\le 1.2\text{s}$ no WhatsApp e Telegram.
- **Relação com o Contexto:** 100% formulado pela IA baseado no prompt específico do usuário e histórico da sessão.
