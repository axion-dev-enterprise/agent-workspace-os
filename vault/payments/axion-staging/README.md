# AXION Staging — Credenciais de Teste (payments/axion-staging)

## 1. Finalidade

Credenciais **sintéticas** geradas por agente para habilitar a validação do
staging integrado AXION Flow + AXION Pay. Nenhuma credencial de produção
reside neste diretório e nenhuma destas chaves pode processar pagamento real
(flags `PAYMENTS_ENABLED`, `STRIPE_ENABLED`, `STRIPE_BILLING_ENABLED`,
`OPEN_FINANCE_ENABLED`, `NUBANK_WEB_ENABLED` e `ENABLE_BANK_RECONCILIATION`
estão fixadas em `"false"` no stack de staging).

| Variável | Consumidor | Injetada em |
| --- | --- | --- |
| `AXION_PAY_STAGING_TEST_API_KEY` | Suíte E2E (curl/Playwright) contra `POST /v1/charges`, `/v1/sandbox/validate` etc. | `/opt/axion/apps/axion-pay-staging/.env.staging` como segunda entrada de `AXION_API_KEYS` (`<segredo>:staging-e2e:charges:read,charges:write,sandbox:read`) |
| `AXION_FLOW_STAGING_WEBHOOK_SECRET` | Assinatura HMAC-SHA256 de envelopes sintéticos em `POST /api/v1/webhooks/axion-pay` | `/opt/axion/apps/agents-platform-staging/.env` como `AXION_PAY_WEBHOOK_SECRET`, com `AXION_BILLING_WEBHOOK_ENABLED=true` |

## 2. Como injetar

Ambas as variáveis são publicadas como secrets do GitHub Actions do repositório
`axion-dev-enterprise/axion-flow` (`PAY_STAGING_TEST_KEY` e
`FLOW_STAGING_WEBHOOK_SECRET`) e aplicadas exclusivamente pelo workflow manual
`staging-ops.yml`, que executa via SSH na VPS já governada. Os valores nunca
aparecem em logs (o GitHub mascara secrets) e nunca são escritos em
documentação, commits ou console.

```powershell
$dir = 'C:/workspace/vault/payments/axion-staging'
$pay  = (Select-String -Path "$dir/.env" -Pattern '^AXION_PAY_STAGING_TEST_API_KEY=').Line -replace '^AXION_PAY_STAGING_TEST_API_KEY=',''
$flow = (Select-String -Path "$dir/.env" -Pattern '^AXION_FLOW_STAGING_WEBHOOK_SECRET=').Line -replace '^AXION_FLOW_STAGING_WEBHOOK_SECRET=',''
gh secret set PAY_STAGING_TEST_KEY        --repo axion-dev-enterprise/axion-flow --body $pay
gh secret set FLOW_STAGING_WEBHOOK_SECRET --repo axion-dev-enterprise/axion-flow --body $flow
```

## 3. Como gerar / rotacionar

Geração local determinística por CSPRNG (32 bytes, base64url sem padding):

```powershell
function New-StagingSecret([int]$n = 32) {
  $b = New-Object byte[] $n
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $rng.GetBytes($b); $rng.Dispose()
  [Convert]::ToBase64String($b).Replace('+','-').Replace('/','_').TrimEnd('=')
}
'axp_stg_' + (New-StagingSecret)   # API key do Pay (>= 24 caracteres exigidos por parseApiKeys)
'whsec_'   + (New-StagingSecret)   # segredo HMAC do webhook do Flow
```

Rotacionar: gerar novos valores, atualizar este `.env`, re-executar os dois
`gh secret set` acima e disparar `staging-ops.yml` com `target=all`. A rotação
não afeta produção, pois nenhuma destas chaves existe fora do staging.

## 4. Revogação

1. Disparar `staging-ops.yml` com `target=pay-key` após remover a entrada do
   secret `PAY_STAGING_TEST_KEY` (o workflow remove entradas órfãs).
2. Para o webhook: reverter `AXION_BILLING_WEBHOOK_ENABLED` para `false` e
   remover `AXION_PAY_WEBHOOK_SECRET` do `.env` do staging do Flow.
3. Executar `python scripts/vault_loader.py audit` e apagar este diretório.

## 5. Auditoria

```powershell
python scripts/vault_loader.py audit
```

Os valores devem aparecer apenas mascarados. Nenhum valor em texto plano pode
ser copiado para logs diários, documentação ou mensagens.
