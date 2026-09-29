# Cloudflare Vault & Credenciais ☁️

## 1. Finalidade
Permitir o gerenciamento automatizado da malha de DNS, Workers, D1 SQL, R2 Buckets e regras do Zero Trust Tunnel.

## 2. Como Obter ou Rotacionar
1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens).
2. Crie um API Token com o template **Edit Cloudflare Workers** ou permissões customizadas de Zone DNS.

## 3. Serviços que Consomem Este Módulo
- Skill `cloudflare-edge-ops`
- Skill `cloudflare-zero-trust-tunnels`
- `scripts/ssl_domain_sentinel.py`
