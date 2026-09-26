# Política de Segurança — AXION Enterprise

A segurança do ecossistema de software e dos agentes autônomos é prioridade máxima.

---

## 1. Relato de Vulnerabilidades

Caso identifique qualquer vulnerabilidade de segurança, vazamento de credencial ou brecha operacional:
1. **Não abra uma Issue pública no GitHub.**
2. Envie um e-mail confidencial para a equipe de segurança através do canal de contato oficial configurado em `workspace.config.json` ou notifique diretamente o administrador do workspace.
3. Inclua etapas de reprodução, impacto estimado e prova de conceito responsável.

---

## 2. Diretrizes de Segurança para Agentes Autônomos

1. **Zero Credential Logging**: Segredos jamais devem ser registrados em logs diários ou consoles.
2. **Blast Radius Guard**: Comandos destrutivos exigem autorização humana prévia.
3. **Isolamento de Execução**: Navegadores headless e testes de penetração devem rodar em ambiente isolado.
