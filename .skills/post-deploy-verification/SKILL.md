---
name: post-deploy-verification
description: Verificação empírica e factual de URLs públicas após o deploy. Inspeciona HTTP status, DOM HTML real e ausência de telas de login ou mocks.
---

# Post-Deploy Verification Skill

## Quando Usar
Sempre e obrigatoriamente após realizar um deploy em ambiente de preview, staging ou produção.

## Procedimento de Verificação
1. **Nunca confiar apenas no status HTTP 200**: Telas de erro, login SSO ou páginas de estacionamento de domínio também retornam 200.
2. **Inspecionar o Corpo do HTML**:
   ```bash
   curl -s -L https://{{PRIMARY_DOMAIN}} | grep -i "<title>"
   ```
3. **Verificar Renderização dos Componentes Chave**:
   - Confirmar a presença de elementos estruturais da aplicação (`id="root"`, `id="app"`, tags de navegação).
   - Confirmar ausência de formulários de login de terceiros ou alertas de manutenção.
4. **Registrar Evidência Factual**: Anexar o snippet do HTML verificado no relatório diário.
