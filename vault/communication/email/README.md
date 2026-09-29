# Agent Email Vault & Credenciais ✉️

## 1. Finalidade
Permitir que agentes recebam mensagens de tarefas e enviem relatórios/alertas via e-mail.

## 2. Como Configurar no Gmail
1. Acesse [Google App Passwords](https://myaccount.google.com/apppasswords).
2. Gere uma senha de app para **E-mail**.
3. Cole a senha de 16 caracteres em `AGENT_EMAIL_PASSWORD`.

## 3. Serviços que Consomem Este Módulo
- `services/agent-email/agent_email_client.py`
- Tarefa agendada `AXION-Agent-Email-Poll`
