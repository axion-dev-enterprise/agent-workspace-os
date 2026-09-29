# Twitter / X Vault & Credenciais 🐦

## 1. Finalidade
Permitir que agentes AXION leiam inteligência do X e publiquem posts autônomos.

## 2. Como Obter ou Renovar
1. Acesse o [X Developer Portal](https://developer.x.com/en/portal/dashboard).
2. Selecione seu App em **Projects & Apps**.
3. Na aba **Keys and Tokens**:
   - **Bearer Token**: Clique em *Generate / Regenerate* para leitura.
   - **Consumer Keys (API Key & Secret)**: Para autenticação de usuário.
   - **Authentication Tokens (Access Token & Secret)**: Para publicar tweets em nome do perfil.

## 3. Serviços que Consomem Este Módulo
- `services/agent-social/twitter_x_monitor.py`
- `scripts/content_intelligence_monitor.py`
