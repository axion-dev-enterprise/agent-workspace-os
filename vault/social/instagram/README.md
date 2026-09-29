# Instagram Vault & Credenciais 📸

## 1. Finalidade
Permitir que agentes monitorem conteúdo, posts e tendências no Instagram com sessão autenticada.

## 2. Métodos de Conexão
- **Método A (Terminal Interativo)**: Rodar `instaloader --login <usuario>` no PowerShell. A sessão é salva no sistema e lida automaticamente pelo monitor.
- **Método B (.env)**: Preencher `IG_USERNAME` e `IG_PASSWORD` neste diretório.
- **Método C (Cookie)**: Copiar o valor de `sessionid` do DevTools do navegador para `IG_SESSION_COOKIE`.

## 3. Serviços que Consomem Este Módulo
- `services/agent-social/instagram_monitor.py`
- `scripts/content_intelligence_monitor.py`
