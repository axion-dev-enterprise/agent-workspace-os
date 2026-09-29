# Auditoria de Aderência — FLOW vs. Plano de Provisionamento

**Revisão:** código de `axion-dev-enterprise/axion-flow` no commit `e366cd9ace182679f4afc98e74674a084c094c88`.  
**Método:** inspeção estática direcionada de rotas, middleware, armazenamento, provisionamento e Baileys.  
**Escopo:** relatório somente; nenhuma alteração foi aplicada ao repositório FLOW ou à produção.

## Veredito

O FLOW já contém os blocos certos para ser a plataforma de provisionamento — SSO, tenants, onboarding, middleware de isolamento e Baileys multi-instância. Porém, o fluxo atual é **administrativo/manual**, não um fluxo de ativação comercial confiável. O plano não deve ser executado diretamente sobre as rotas existentes sem corrigir os pontos P0 abaixo.

## Achados P0 — bloqueiam trial público e provisionamento por pagamento

### P0-1 — Não existe ingress de billing seguro nem idempotência de provisionamento

**Evidência:** as rotas de criação são administrativas (`server.js:598` e `server.js:778`) e chamam diretamente `provisionTenantDb`. Não há rota de webhook do PAY, verificação HMAC, `Idempotency-Key`, tabela/ledger de evento externo ou máquina de estados de entitlement.

**Impacto:** um webhook repetido, atrasado ou fora de ordem não pode ser reconhecido de forma segura. Reaplicar um evento gera erro de “tenant já existe”, em vez de um ACK idempotente; o trial pode ficar sem reconciliação entre cobrança e acesso.

**Correção requerida:** criar `billing_webhook_service`, persistir o ID do evento antes de executar efeitos, validar assinatura e timestamp, criar uma solicitação de provisionamento assíncrona e retornar `202` para o processamento idempotente.

### P0-2 — Persistência JSON pode declarar sucesso após falha de escrita

**Evidência:** `services/database.js:364-380` captura erro de `writeFileSync`/`renameSync`, apenas registra no console e não relança. `provisionTenantDb` continua e retorna sucesso após `saveDatabase` (`services/database.js:983-997`).

**Impacto:** uma ativação pode responder como bem-sucedida mesmo sem persistir tenant, usuário ou entitlement. Isso inviabiliza uma promessa de cobrança/provisionamento confiável.

**Correção requerida:** fazer falha de persistência propagar ao chamador; usar transação/outbox num banco durável antes de múltiplas réplicas; nunca confirmar webhook enquanto o evento e a transição não estiverem gravados.

### P0-3 — O provisionamento direto não tem lock nem proteção contra corrida entre processos

**Evidência:** o lock por arquivo existe apenas no fluxo de solicitações de conta (`withAccountMutationLock`, `services/database.js:627-644`). `provisionTenantDb` (`874-998`) não usa esse lock e lê/verifica/grava um documento JSON inteiro.

**Impacto:** dois workers ou duas réplicas podem passar pela verificação de inexistência e sobrescrever o estado um do outro. O `rename` atômico protege contra arquivo parcialmente escrito, não contra lost updates.

**Correção requerida:** índice único e transação no storage definitivo; enquanto o JSON existir, lock abrangente de provisionamento e execução de um único worker, com uma chave de idempotência por evento.

### P0-4 — Novo tenant recebe uma allowlist excessiva de ferramentas

**Evidência:** `provisionTenantDb` atribui por padrão `terminal_execute`, `code_file_ops`, `api_request`, `browser_headless`, `spawn_subagent` e outras ferramentas em `services/database.js:949-957`.

**Impacto:** o onboarding comercial cria um tenant com capacidades de infraestrutura que não pertencem ao produto de atendimento. Mesmo que o subagente padrão limite parte desse alcance hoje, a política de tenant já nasce permissiva e pode ser ampliada por mudanças futuras de catálogo.

**Correção requerida:** perfil `customer_onboarding` deny-by-default, inicialmente limitado a atendimento/CRM e à instância WhatsApp daquele tenant. Ferramentas de host, arquivo, browser privilegiado e subagentes ficam fora de tenants comerciais até concessão administrativa granular e auditada.

## Achados P1 — devem ser resolvidos antes de ativar clientes externos

### P1-1 — API WhatsApp permite envio direto sem política comercial

**Evidência:** `POST /api/v1/whatsapp/send` (`server.js:1078-1089`) aceita `phone` e `text`; `sendWhatsAppMessage` envia ao JID e grava o conteúdo integral (`services/baileys_manager.js:515-549`). Não há consentimento, opt-out, rate limit, template/política, aprovação ou chave idempotente nessa rota.

**Impacto:** risco de envio involuntário, duplicado ou incompatível com a política comercial; também amplia risco operacional do Baileys.

**Correção requerida:** separar mensagem de teste de mensagens comerciais, exigir consentimento explícito por ação, validar destinatário, aplicar supressão/opt-out/rate limit e gravar recibo de envio sem texto sensível.

### P1-2 — QR bruto é exposto pela rota de runtime

**Evidência:** o estado guarda `qrRaw` (`services/baileys_manager.js:83-90`, `169-173`) e `GET /api/v1/whatsapp/instances/runtime/:instance_id` retorna o runtime inteiro (`server.js:1051-1054`).

**Impacto:** qualquer sessão autenticada daquele tenant que alcance a rota recebe o segredo bruto de pareamento, além do Data URL necessário à interface.

**Correção requerida:** retornar um DTO explícito, com `status`, `phone`, expiração e Data URL temporário quando autorizado; nunca serializar `qrRaw`, caminho de sessão, objetos de socket ou dados internos.

### P1-3 — “Pairing” atual é QR, não pairing code; instância pode ser criada com defaults perigosos

**Evidência:** `generatePairingQrCode` apenas inicia socket e espera QR (`config/whatsapp_instances.js:68-85`); não há chamada à API de pairing code. `saveWhatsAppInstanceDb` aceita payload pouco validado e cria linha com telefone fictício/`auto_reply` como defaults (`services/database.js:462-506`).

**Impacto:** o requisito de pairing mobile de oito dígitos não está implementado; defaults podem ativar semântica inadequada para um cliente recém-criado.

**Correção requerida:** endpoint específico para pairing code, schema com enum fechado, nenhuma linha inicial fictícia e modo inicial `read_only` até consentimento e configuração concluídos.

### P1-4 — Exclusão de tenant é hard delete incompleto

**Evidência:** `deleteTenantDb` remove somente tenant, conectores, instâncias e usuários (`services/database.js:1000-1016`); a rota administrativa a chama diretamente (`server.js:652-668`). Não há tombstone, aprovação em duas etapas, retenção, outbox, limpeza auditável da sessão Baileys nem cobertura aparente de outros registros por tenant.

**Impacto:** perda irreversível ou estado órfão durante um cancelamento/rollback; incompatível com reconciliação de assinatura e suporte.

**Correção requerida:** substituir por desativação/tombstone, preservar ledger e dados conforme política de retenção, agendar purge auditável e manter rollback sem apagar recursos.

### P1-5 — Possível DOM XSS a partir do nome da empresa

**Evidência:** o onboarding aceita `company` sem escapar HTML (`services/database.js:676-692`) e a UI concatena `tenantConfig?.company` em `innerHTML` sem `escapeHtml` (`public/app.js:736`).

**Impacto:** um nome de empresa contendo marcação pode executar HTML/script no contexto do painel daquele tenant e atingir o cookie/sessão disponível ao navegador.

**Correção requerida:** usar `textContent`/DOM seguro para todos os valores de tenant ou escapar obrigatoriamente antes do sink; validar entradas e incluir teste de regressão com payload HTML.

## Achados P2 — dívida que precisa entrar no roadmap

| Achado | Evidência | Ajuste |
| --- | --- | --- |
| Erros não são uniformemente RFC 7807 | diversas rotas devolvem `{ error: ... }`, por exemplo `server.js:487`, `616`, `1087` | middleware único de Problem Details, com `traceId` e sem mensagem interna. |
| Token de sessão em resposta JSON | troca de tenant devolve `token` em `server.js:688-697`, embora também grave cookie | não retornar token ao JavaScript; usar cookie `HttpOnly`, `Secure`, `SameSite` definido e CSRF para rotas mutáveis. |
| Mensagens completas em JSON central | `logWhatsAppMessageDb` persiste texto e mantém um buffer global de 2.000 mensagens (`services/database.js:520-541`) | criptografia/retencão por tenant, separação de índices e telemetria sem conteúdo. |
| Reconexão sem backoff/limite | `setTimeout(..., 5000)` em `baileys_manager.js:220-223` | backoff exponencial com jitter, contador, estado degradado e alerta. |

## Matriz de aderência ao plano

| Parte do plano | Estado atual | Decisão |
| --- | --- | --- |
| SSO e isolamento de tenant | Parcialmente pronto | Reutilizar, com testes de acesso cruzado. |
| Provisionamento automático por PAY | Ausente | Construir como novo serviço interno, sem reutilizar rota admin diretamente. |
| Trial/assinatura/entitlement | Ausente no FLOW auditado | Integrar via contratos oficiais do PAY. |
| Idempotência e event ledger | Ausente no domínio de billing | Construir antes do piloto. |
| QR por tenant | Parcialmente pronto | Reutilizar após DTO seguro, schema e controles de estado. |
| Pairing code | Ausente | Implementar. |
| Mensagem de teste com consentimento | Ausente | Implementar política e recibos. |
| Migração do AGENTS | Não iniciada | Fazer depois do MVP de ativação, com feature flag e canário. |

## Ordem de correção recomendada

1. Corrigir P0-2, P0-3 e P0-4 como pré-requisito de qualquer tenant comercial.
2. Criar o domínio billing/provisioning idempotente (P0-1) e seus testes de reentrega/ordem invertida.
3. Fechar QR, pairing, política de mensagem e privacidade (P1-1 a P1-3).
4. Substituir hard delete e corrigir XSS (P1-4 e P1-5).
5. Padronizar erros, sessão, retenção e reconexão (P2).

## Limitações da revisão

Esta é uma auditoria estática do commit indicado. Não foram executados testes, deploys, webhooks reais, pareamento, cobrança ou chamadas mutáveis. Portanto, o relatório demonstra riscos no código analisado, não confirma comportamento em produção.

