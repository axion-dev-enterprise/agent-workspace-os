# Quality Gates, Piloto e Go/No-Go

## 1. Gates por camada

| Camada | Evidência exigida |
| --- | --- |
| Contrato | fixtures validadas para PAY ↔ FLOW; versão e campos obrigatórios. |
| Segurança | assinatura inválida/replay rejeitados; secrets e QR bruto ausentes de respostas/logs. |
| Dados | idempotência, concorrência, rollback por estado e reconciliação aprovados. |
| Tenant | teste negativo de leitura/ação entre dois tenants. |
| UX | mobile 360–430px, desktop, teclado, foco, erro e retomada. |
| Canal | QR expirado, pairing falho, reconexão e opt-out cobertos. |
| Operação | health, alertas, runbook e responsável de incidentes definidos. |

## 2. Cenários obrigatórios de staging

1. A nova superfície canônica de billing está no OpenAPI, incluindo schema, autenticação, idempotência, eventos e exemplos de erro; `/v1/flow/billing/*` não é dependência do novo caminho.
2. Uma assinatura/trial elegível, confirmada pelo contrato selecionado, cria apenas um request/tenant/admin.
3. A mesma entrega recebida três vezes recebe ACK e não cria duplicatas.
4. Um `subscription.canceled` anterior não desfaz uma renovação posterior.
5. Falha entre criação do tenant e emissão do link deixa pedido recuperável, não um tenant invisível.
6. Usuário do tenant A não consulta QR, conexão, mensagem, armazenamento ou dados do tenant B.
7. QR expira; cliente recebe instrução e gera novo QR sem recriar instância.
8. Mensagem de teste sem confirmação é recusada; com confirmação gera um único recibo.
9. Checkout nunca coloca cartão/CVV em DOM, log, analytics ou storage do navegador; para cartão, o frontend usa a configuração pública e os campos seguros do PAY, enquanto o FLOW somente cria a intenção/checkout pelo backend autorizado.

## 3. Métricas do piloto

- conversão: visita → lead → checkout → entitlement → tenant → onboarding → primeiro valor;
- tempo mediano e p95 até provisionamento e conexão;
- taxa de reentrega/erro de webhook;
- taxa de falha/abandono de onboarding por etapa;
- mensagens bloqueadas por consentimento/rate limit;
- incidentes de isolamento, segredos e dados pessoais: meta zero.

## 4. Estratégia de piloto

- Como a base atual é exclusivamente QA, começar com fixtures sintéticas recriadas no caminho canônico, sem migração de usuários, contratos ou sessões legadas.
- Ativar por feature flag: billing ingress, worker, onboarding, QR e mensagem de teste são flags independentes.
- Revisar diariamente eventos pendentes, falhas e tickets antes de ampliar o público.
- Qualquer falha P0 congela novas ativações, preserva dados e inicia reconciliação; não se apaga tenant para “corrigir”.

## 5. Resposta mínima a incidente

| Sinal | Ação imediata | Não fazer |
| --- | --- | --- |
| Webhook duplicado ou fora de ordem | congelar novas ativações se houver efeito duplicado; reconciliar pelo ledger | reenviar manualmente sem ID/correlação. |
| Falha de provisionamento | pausar worker afetado e reprocessar pela outbox após correção | criar tenant manual paralelo. |
| Exposição de QR/segredo | invalidar sessão/chave afetada, preservar evidência redigida e investigar escopo | imprimir o segredo em logs ou chat. |
| Acesso cruzado de tenant | bloquear rota/feature, preservar dados e escalar como incidente crítico | continuar o piloto ou apagar evidências. |
| Envio indevido | suspender outbound do tenant, aplicar supressão e registrar recibo | reenviar a mensagem ou remover o histórico. |

## 6. Checklist de cutover

- [ ] ADRs aprovados e owners operacionais definidos.
- [ ] OpenAPI do AXION Pay e implementação local descrevem a mesma superfície de billing do FLOW, com fixture assinada validada em staging.
- [ ] O legado `/v1/flow/billing/*` está bloqueado para novas gravações e fora do tráfego do cenário de staging.
- [ ] Staging usa credenciais, dados e storage isolados da produção.
- [ ] Feature flags têm estado inicial, owner e procedimento de reversão documentados.
- [ ] Backups/restore dos dados relevantes foram verificados, sem incluir segredos em relatório.
- [ ] Métricas, dashboards e alertas estão recebendo eventos de staging.
- [ ] O piloto canário passou por todas as transições, inclusive cancelamento e recuperação.

## 7. Decisão Go/No-Go

**GO** exige todos os gates, piloto sem P0/P1 aberto, owner operacional e rollback exercitado.  
**NO-GO** se houver pagamento sem reconciliação, evento sem idempotência, acesso cruzado de tenant, exposição de segredo/QR, mensagem sem consentimento ou ausência de evidência recente.
