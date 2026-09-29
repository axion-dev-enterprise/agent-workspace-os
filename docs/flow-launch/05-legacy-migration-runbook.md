# Runbook de Cutover de QA: AGENTS e Billing Legado → FLOW

## Premissa e limite

A base atual contém apenas testers/QA. Este runbook não migra clientes, assinaturas, cobranças, sessões ou dados pessoais reais. O objetivo é cortar para o caminho canônico, recriando fixtures de QA e preservando somente evidência mínima, redigida e aprovada. Ele não autoriza apagar dados agora.

## Fase A — Congelar e registrar evidência

1. Congelar novas features e novas gravações em `/v1/flow/billing/*` e no fluxo legado de AGENTS usando flags reversíveis.
2. Registrar inventário de rotas, jobs, webhooks, flags e dependências externas; não exportar segredos, QR bruto, conteúdo de mensagens ou tokens.
3. Registrar apenas contagens e hashes de manifestos para tenants, instâncias, jobs e eventos de QA.
4. Confirmar que não há cliente, cobrança ou contrato real no escopo; se houver, interromper este runbook e abrir um plano de migração específico.

**Saída:** baseline técnico redigido, flags identificadas e rollback definido.

## Fase B — Criar o caminho canônico

1. Publicar o contrato canônico do AXION Pay no OpenAPI e gerar fixtures de staging assinadas.
2. Criar fixtures sintéticas no FLOW pelo novo checkout → entitlement → worker → onboarding.
3. Exercitar falhas, duplicatas, ordem invertida e recuperação pela outbox.
4. Validar isolamento entre ao menos dois tenants de QA e a fachada segura de WhatsApp.

**Saída:** evidência de staging aprovada sem dependência de `/v1/flow/billing/*` ou da UI AGENTS.

## Fase C — Cutover técnico

1. Direcionar as flags de QA para o novo caminho canônico.
2. Recriar, e não migrar, tenants/trials/assinaturas de teste necessários.
3. Bloquear novas chamadas ao billing legado e deixar suas rotas em modo de compatibilidade reversível para ambientes internos.
4. Observar métricas, filas, erros e isolamento durante a janela definida.

**Saída:** todo cenário de QA relevante usa FLOW e contrato canônico.

## Fase D — Retirada posterior

1. Confirmar ausência de tráfego, referências de código, jobs e webhooks para o legado pelo período de observação aprovado.
2. Arquivar evidências redigidas e o inventário técnico.
3. Propor uma tarefa separada para exclusão de dados/rotas legados, com alvo exato, backup verificável e aprovação explícita. Não incluir esta exclusão no cutover.

## Rollback

- Reverter apenas as feature flags/roteamento para o caminho anterior de QA.
- Preservar a outbox e os recibos para reconciliação; não copiar nem mesclar estados entre legado e canônico.
- Se surgir qualquer indício de dado real, interromper o cutover e escalar para plano de migração de produção.
