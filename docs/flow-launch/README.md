# AXION FLOW — Pacote de Preparação para Lançamento

Este conjunto de documentos define como preparar o FLOW para ser uma plataforma de ativação comercial segura, reutilizando seus componentes atuais sem transportar a interface legada do AGENTS. Não descreve uma implementação já concluída.

## Objetivo de lançamento

Converter um visitante que concluiu o checkout e tem entitlement válido em um tenant ativo, com trial/assinatura reconciliável, onboarding retomável e canal WhatsApp opcional, isolado e consentido.

## Documentos

1. [Fundação da plataforma](01-platform-foundation.md) — arquitetura-alvo, domínio, segurança e decisões.
2. [Contratos de API](02-api-contracts.md) — schemas, autenticação, eventos e erros.
3. [Backlog de entrega](03-delivery-backlog.md) — épicos, dependências, arquivos e Definition of Done.
4. [Quality gates de lançamento](04-launch-quality-gates.md) — testes, segurança, piloto e Go/No-Go.
5. [Runbook de cutover de QA](05-legacy-migration-runbook.md) — congelamento, evidência mínima, recriação de fixtures e retirada controlada.
6. [Timeline de execução](06-execution-timeline.md) — alterações realizadas, evidências, limitações e próximos gates.

## Fatos de partida

- O FLOW já possui SSO, tenants, middleware de isolamento e Baileys multi-instância.
- O fluxo existente é administrativo/manual; ele não é ainda um ingresso de billing público idempotente.
- O billing específico `/v1/flow/billing/*` do AXION Pay é legado de QA: não será migrado nem escolhido como contrato novo. Ele será congelado e retirado após o cutover técnico.
- A base atual é composta por testers/QA. Não há migração de clientes, cobranças ou sessões reais: preserva-se apenas evidência redigida e recriam-se fixtures no caminho canônico.
- Os achados bloqueantes estão detalhados em [AXION_FLOW_PLAN_GAP_AUDIT.md](../AXION_FLOW_PLAN_GAP_AUDIT.md).
- A especificação anterior de implementação está em [AXION_FLOW_PROVISIONING_IMPLEMENTATION_PLAN.md](../AXION_FLOW_PROVISIONING_IMPLEMENTATION_PLAN.md).

## Regra de lançamento

Nenhuma fase segue para produção por “parecer pronta”. Cada etapa precisa de evidência recente no staging, dados de teste removidos e aprovação explícita para qualquer cobrança, mensagem, deploy ou alteração de domínio.

## Como usar o pacote

1. Aprovar os ADRs e decisões pendentes em `01`.
2. Congelar os contratos em `02` antes de alterar rotas ou persistência.
3. Executar o backlog de `03` na ordem P0 → P1 → P2.
4. Usar `04` como portão de staging, piloto e produção.
5. Só iniciar o cutover de QA e a retirada do legado após cumprir o runbook `05`.
