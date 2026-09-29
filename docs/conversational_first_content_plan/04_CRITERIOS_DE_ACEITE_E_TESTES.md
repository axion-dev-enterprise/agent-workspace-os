# 04 — Critérios de Aceite, Benchmarks e Plano de Testes

---

## 1. Critérios de Aceite Mandatórios

Para homologação do módulo de **Conversational First Content Streaming**:

- [ ] **100% Gerado por IA:** Nenhuma palavra do First Content pode originar-se de regex, templates engessados ou heurísticas estáticas.
- [ ] **Latência do First Content $\le 1.5\text{s}$:** Medida a partir do momento em que a requisição bate no endpoint `/v1/chat` até o disparo do payload para a API do canal.
- [ ] **Aderência ao Contexto:** O texto gerado deve refletir com exatidão os termos e intenção da mensagem enviada pelo usuário.
- [ ] **Não-Bloqueio do ReAct:** O ReAct e as ferramentas continuam sua execução sem serem travadas pelo streaming do First Content.
- [ ] **Resiliência a Falhas de Rede:** Se a conexão SSE sofrer timeout de rede (> 4s), o sistema segue para a execução normal sem travar a requisição nem emitir erros ao usuário.

---

## 2. Cenários de Teste Reais

### Cenário 1: Pergunta Operacional de Infraestrutura (Admin)
- **Entrada:** *"Quais portas estão abertas no host e qual o consumo de RAM?"*
- **First Content Esperado:** *"Vou verificar as portas em escuta no Windows e auditar as métricas de memória RAM e processos agora."*
- **Latência Alvo:** $< 1.0\text{s}$

### Cenário 2: Pergunta Comercial / Lead (WhatsApp)
- **Entrada:** *"Quanto custa para colocar o robô no meu número de WhatsApp?"*
- **First Content Esperado:** *"Vou te passar as condições do nosso teste de 30 dias gratuitos e como funciona o plano com o seu próprio número de WhatsApp."*
- **Latência Alvo:** $< 1.0\text{s}$

### Cenário 3: Pergunta Conceitual / Dúvida Técnica
- **Entrada:** *"Como o Pixel da Meta e a CAPI conversam entre si no agente?"*
- **First Content Esperado:** *"Vou explicar como o agente correlaciona o identificador do lead com a API de Conversões da Meta para disparar eventos em tempo real."*
- **Latência Alvo:** $< 1.1\text{s}$

---

## 3. Protocolo de Validação Automatizada

Criar o script de validação de latência e coerência em `scripts/test_first_content_stream.py`:
1. Disparar 5 requisições com temáticas completamente distintas (infra, comercial, dúvidas conceituais, código e contingência).
2. Medir o TTFT individual de cada requisição.
3. Validar se nenhuma saída repete templates idênticos ou frases mecânicas.
4. Confirmar entrega correta nos logs do PM2.
