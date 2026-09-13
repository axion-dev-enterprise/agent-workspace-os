---
name: zero-test-pollution
description: Diretrizes para garantir zero poluição de dados de teste em bancos relacionais, caches e dashboards de produção.
---

# Zero Test Pollution Skill

## Princípio
Todo teste automatizado, simulação de fluxo ou chamada E2E cria dados efêmeros. Deixar esses dados no ambiente degrada métricas de negócio e polui logs.

## Regras
1. **Teardown Mandatório**: Scripts de teste DEVEM conter blocos de limpeza (`afterAll`, `finally` ou hooks de teardown) que deletam usuários, transações e registros simulados.
2. **Identificadores Isolados**: Dados de teste devem conter prefixos claros (ex: `test_e2e_...`) para facilitar purgas automatizadas caso o teste seja interrompido abruptamente.
3. **Validação Pós-Teste**: Verificar se a contagem de registros na tabela afetada retornou ao valor basal após a execução do teste.
