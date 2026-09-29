# Consolidado e Plano de Execução — AXION Flow + AXION Agents

**Status:** proposta de execução; nenhuma mudança de runtime, deploy ou integração externa é autorizada por este documento.  
**Base de evidências:** inspeção de `agents.example.com`, `flow.example.com`, repositório privado `axion-dev-enterprise/axion-flow`, documentação local e handoff comercial.  
**Data:** 2026-09-27

## 1. Síntese executiva

O produto deve operar como uma esteira única, mas com responsabilidades separadas:

```text
Aquisição e conversão                    Operação do cliente
FLOW                                     AGENTS
flow.example.com               agents.example.com
        │                                         │
Landing → qualificação → checkout → provisionamento → tenant isolado
        │                                         │
Meta/CRM/WhatsApp/Billing                  agente, sessão, memória e conectores
```

**FLOW** é a experiência comercial: landing, origem do lead, qualificação, proposta, checkout e ativação do trial. **AGENTS** é a plataforma executiva multi-tenant: identidade federada, aprovação/provisionamento de tenant, agentes, ferramentas auditáveis, memória e canais de atendimento.

O objetivo de negócio é converter um visitante em um tenant operacional com WhatsApp conectado, sem perder rastreabilidade entre campanha, lead, pagamento, aprovação, provisionamento e primeiro valor entregue.

## 2. Estado constatado

| Componente | Evidência atual | Leitura operacional |
| --- | --- | --- |
| `flow.example.com` | HTTP 200; título “AXION FLOW — Sistema Comercial Autônomo 24/7”; frontend Vercel | Superfície comercial existente. A resposta possui cache Vercel com idade elevada; revisar invalidação e versão antes de campanhas. |
| `agents.example.com` | HTTP 200; título “AXION Agents \| Plataforma Executiva”; release identificada em header | Plataforma executiva ativa atrás de Cloudflare. |
| `axion-flow` | Repositório GitHub privado, Python predominante, branch `main` | Fonte candidata para a plataforma e integrações; a última atualização disponível no metadado é 2026-09-09. |
| AXION Pay | Checkout e rotas públicas documentadas localmente | Há uma base de checkout, mas billing recorrente/assinaturas ainda aparecem como gaps documentados. |
| WhatsApp Bridge | Bridge local existente e protocolo Baileys descrito no handoff | Deve ser tratado como canal de risco operacional, com consentimento, limites e isolamento por tenant. |

## 3. Princípios e decisões de arquitetura

1. **Uma fonte de verdade por domínio.** FLOW registra lead e funil; PAY registra pagamento, assinatura e webhook; AGENTS registra tenant, identidade, sessão, conectores e execução.
2. **Provisionamento assíncrono e idempotente.** Pagamento ou aprovação de trial dispara uma solicitação durável com uma chave idempotente. Reentregas de webhook não criam tenants nem cobranças duplicadas.
3. **Tenant antes de conectar o canal.** Uma sessão WhatsApp, dados de campanha, credenciais e memória só existem depois de um `tenant_id` aprovado e isolado.
4. **Pagamento tokenizado.** A landing nunca recebe, armazena ou registra número/CVV de cartão. O gateway deve fornecer campos hospedados/tokenização e a aplicação manipula somente token e estado da transação.
5. **Consentimento e minimização de dados.** Pixel/CAPI e WhatsApp são opcionais, com opt-in explícito, finalidade documentada e possibilidade de revogação.
6. **Nenhuma promessa técnica não verificável.** Evitar alegações absolutas sobre taxas, disponibilidade, entrega ou risco de bloqueio. A mensageria deve ter política de uso, limites de envio e opt-out.

## 4. Fluxo alvo de ponta a ponta

1. Visitante chega ao FLOW com UTMs e, quando aplicável, consentimento de analytics.
2. FLOW cria/atualiza o lead e apresenta a oferta escolhida.
3. O checkout tokenizado cria a intenção de pagamento ou a autorização de trial no PAY.
4. Webhook autenticado do PAY confirma o estado e publica `subscription_or_trial_activated`.
5. O serviço de provisionamento cria ou associa o `tenant_id` no AGENTS, de forma idempotente.
6. AGENTS libera o onboarding autenticado: conexão WhatsApp, modo operacional, dados de empresa e integrações opcionais.
7. A bridge mantém credenciais de sessão exclusivas do tenant e devolve somente estados sanitizados ao frontend.
8. O primeiro evento útil (conexão confirmada ou primeira resposta do agente) é registrado no funil e, se houver consentimento, enviado ao Pixel/CAPI.

## 5. Plano de execução por fases

### Fase 0 — Contratos, ownership e segurança (P0)

**Objetivo:** eliminar ambiguidades antes de alterar produto ou infraestrutura.

- Definir contratos versionados para `Lead`, `CheckoutIntent`, `Subscription`, `TenantProvisionRequest`, `ChannelConnection` e eventos de webhook.
- Definir a máquina de estados: `lead → checkout_pending → trial_active/payment_active → provisioning → onboarding → active`, com estados de falha e compensação.
- Estabelecer ownership: FLOW (funil), PAY (cobrança), AGENTS (tenant/executor) e Bridge (canal).
- Revisar CORS, autenticação de webhook, assinaturas HMAC, rate limits, retenção e logs sem PII/segredos.
- Confirmar jurídica e comercialmente a copy sobre Meta, Baileys, opt-in e cancelamento.

**Aceite:** ADR aprovada; schemas validados; matriz de dados pessoais e eventos; ameaças e rollback definidos.

### Fase 1 — Funil e landing de conversão (P0)

**Objetivo:** converter sem misturar dados de cobrança, sessão do cliente ou segredo no browser.

- Consolidar a landing sob o FLOW e remover duplicidade entre páginas/aliases somente após inventário de tráfego.
- Implementar oferta, FAQ honesto, seleção de modalidade e captura de lead com consentimento.
- Fazer checkout embutido exclusivamente por tokenização/campos seguros do PAY.
- Persistir apenas rascunho não sensível no navegador; não persistir cartão, CVV, token de sessão ou CAPI token.

**Aceite:** 360–430 px e desktop; teclado/foco/contraste; validações; estados de loading/erro; nenhum dado de cartão em DOM, storage ou logs; evento de lead deduplicado.

### Fase 2 — Billing, trial e webhooks (P0)

**Objetivo:** conceder trial e cobrar corretamente sem duplicidade.

- Implementar produtos/preços e política explícita: número próprio versus número dedicado.
- Implementar intenção/assinatura e rotinas de cancelamento, falha de cobrança e aviso prévio.
- Assinar, verificar e registrar webhooks com idempotência, correlação e RFC 7807 em erros.
- Criar reconciliação de pagamentos versus tenants provisionados.

**Aceite:** testes para reentrega, ordem invertida, falha parcial e cancelamento; reconciliação sem divergências; nenhuma cobrança criada por refresh do cliente.

### Fase 3 — Provisionamento e onboarding no AGENTS (P0)

**Objetivo:** entregar um tenant seguro e pronto para ativação.

- Expor uma API interna autenticada de provisionamento, não uma rota pública aberta.
- Criar tenant, administrador, limites padrão e storage isolado em transação/compensação.
- Emitir link de onboarding de uso único, expiração curta e associação ao tenant.
- Integrar status de provisionamento ao FLOW para feedback compreensível ao cliente.

**Aceite:** duas chamadas idênticas retornam o mesmo tenant; falha não deixa recursos órfãos; usuário de um tenant não acessa dados ou sessão de outro.

### Fase 4 — WhatsApp e ativação de valor (P1)

**Objetivo:** conectar o canal de forma segura e demonstrar valor rapidamente.

- Implementar QR/pairing apenas na sessão autenticada do tenant.
- Isolar credenciais por tenant, criptografar armazenamento em repouso e não expor QR bruto/logs sensíveis.
- Exibir máquina de estados: aguardando, QR expirado, conectado, desconectado, erro recuperável e suporte necessário.
- Exigir confirmação do cliente antes de qualquer mensagem de teste ou campanha; aplicar limites, supressão e opt-out.

**Aceite:** refresh de QR, recuperação de desconexão, isolamento validado, logs redigidos e nenhuma mensagem enviada sem consentimento/ação explícita.

### Fase 5 — CRM, Meta e observabilidade (P1)

**Objetivo:** medir o funil e operar com confiança.

- Criar event ledger: `lead_created`, `checkout_started`, `trial_activated`, `tenant_provisioned`, `whatsapp_connected`, `first_value`.
- Enviar eventos CAPI somente quando houver opt-in, payload mínimo e deduplicação via `event_id`.
- Criar painéis por etapa, correlação ponta a ponta e alertas para webhook falho, provisionamento parado e desconexão de canal.
- Medir conversão, tempo até ativação, taxa de conexão, falhas de cobrança e retenção de trial.

**Aceite:** evento pode ser rastreado do lead ao tenant; eventos duplicados não alteram métricas; alertas têm runbook e destinatário definido.

### Fase 6 — Piloto controlado e expansão (P1)

**Objetivo:** validar operação real antes de escalar tráfego.

- Rodar com poucos tenants autorizados e segmentos limitados.
- Revisar suporte, cancelamentos, falhas de onboarding, entregabilidade e métricas de ativação.
- Corrigir causas-raiz antes de ampliar campanha ou automação.

**Aceite:** metas de ativação e suporte definidas antes do piloto; nenhuma vulnerabilidade crítica pendente; decisão formal Go/No-Go.

## 6. Pré-mortem e mitigação

| Falha provável | Sinal antecipado | Mitigação |
| --- | --- | --- |
| Cobrança ou tenant duplicado | Webhooks reentregues e tenants repetidos | Chave idempotente, event ledger e reconciliação. |
| Vazamento entre clientes | Consultas sem `tenant_id` ou storage compartilhado | Autorização por tenant, testes de isolamento e storage dedicado. |
| Dados de cartão ou token no frontend/log | Payload, localStorage ou console contendo dado sensível | Tokenização hospedada, redaction e testes de inspeção. |
| QR/sessão WhatsApp instável | Reconexões frequentes e QR expirado | Máquina de estados, retries com backoff, suporte e health check. |
| Campanha gera leads sem ativação | Queda entre checkout, provisionamento e conexão | Métricas por etapa, onboarding guiado e recuperação de abandono. |
| Cache serve uma versão antiga | Header `Age` alto, release divergente | Definir estratégia de cache, versionamento e validação pós-deploy. |

## 7. Portões PEV por mudança

Cada fase deve cumprir: especificação de contrato, pré-voo do ambiente/tenant, mudança atômica, teste automatizado, teste de integração em staging, teardown de dados de teste e relatório com evidências recentes. Deploy, cobrança, disparo de mensagens ou alteração de DNS exigem autorização explícita separada.

## 8. Próximas decisões que exigem definição do operador

1. Qual domínio é a experiência oficial de venda: `flow.example.com` ou uma landing específica?
2. Qual é o provedor e contrato real de cobrança recorrente do AXION Pay?
3. O provisionamento de tenant será automático após pagamento ou sujeito a aprovação manual?
4. Quais modalidades e preços são finais, incluindo a regra do número/chip dedicado?
5. Qual política comercial, consentimento e suporte regerá o uso do WhatsApp?

