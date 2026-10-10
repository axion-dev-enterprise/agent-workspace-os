# Cloudflare Vault & Credenciais ☁️

## 1. Finalidade
Permitir o gerenciamento automatizado da malha de DNS, Workers, D1 SQL, R2 Buckets e regras do Zero Trust Tunnel.

## 2. Como Obter ou Rotacionar
1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens).
2. Crie um API Token com o template **Edit Cloudflare Workers** ou permissões customizadas de Zone DNS.

## 3. Configuração e Rotação
- Armazene `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_ZONE_ID` somente neste `.env`; injete em processos via `scripts.vault_loader.load_vault()`.
- O token precisa das permissões mínimas necessárias ao trabalho aprovado (Zone DNS, Workers e/ou Tunnels); não use token global. Confirme a identidade com `wrangler whoami` antes de qualquer alteração remota.
- Para rotacionar, crie o token no Dashboard, atualize este arquivo sem registrar seu valor em logs/documentos, valide com `python scripts/vault_loader.py audit` e revogue o token antigo após confirmar os consumidores.

## 4. Serviços que Consomem Este Módulo
- Skill `cloudflare-edge-ops`
- Skill `cloudflare-zero-trust-tunnels`
- `scripts/ssl_domain_sentinel.py`
