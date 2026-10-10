---
name: task-completion-observability
description: >-
  Diretrizes mandatórias para execução autônoma integral, proibição de tarefas incompletas ou evasivas
  ('se quiser eu faço'), transparência obrigatória de passos e conclusão garantida no ecossistema AXION.
---

# Task Completion & Step Observability Skill — AXION Enterprise

Guia canônico e operacional para garantir que todo agente de IA (WhatsApp, Telegram, Brain Server, CLIs e subagentes) execute demandas até a finalização conclusiva absoluta, proibindo transferências evasivas de responsabilidade e garantindo visibilidade total de cada passo técnico executado.

---

## 1. Princípios Fundamentais (Invioláveis)

### 1.1 Autonomia Compulsória (Zero Halfway Stopping)
- O agente **NUNCA** deve parar na metade de uma tarefa diagnóstica ou operacional.
- Se a primeira tentativa de resolução ou busca não obtiver o resultado esperado (ex: credencial ausente no vault principal ou porta SSH padrão 22 recusada), o agente **TEM O DEVER** de acionar autonomamente os passos subsequentes lógicos no mesmo turno:
  - Verificar histórico de chaves e hosts (`known_hosts`, portas alternativas).
  - Verificar logs locais e arquivos de configuração relacionados.
  - Testar conectividade em portas não padrão ou nós de backup.
  - Inspecionar documentação correlata e repositórios locais.

### 1.2 Proibição Estrita de Respostas Evasivas e Perguntas de Permissão
- É **TERMINANTEMENTE PROIBIDO** responder com perguntas de permissão quando as ferramentas necessárias já estão disponíveis:
  - ❌ *"Se você quiser, posso verificar agora as chaves SSH..."*
  - ❌ *"Quer que eu investigue mais a fundo os logs?"*
  - ❌ *"É só me avisar se devo rodar o diagnóstico..."*
  - ❌ *"Posso verificar se você quiser. É só mandar."*
- **Conduta Correta**: Execute a verificação imediatamente via ferramentas (`<invoke name="...">` / `read_file` / `exec_command` / `fetch_url`), colete os dados factuais e apresente o resultado consolidado e conclusivo ao usuário.

### 1.3 Proibição de Promessas Futuras Sem Execução Imediata
- É proibido responder com mensagens promissórias de ação futura isoladas:
  - ❌ *"Vou investigar o estado do código no workspace..."* (sem chamar ferramentas no mesmo turno).
  - ❌ *"Vou extrair o conteúdo do link enviado..."* (sem chamar `fetch_url`).
- Qualquer promessa de ação deve vir acompanhada da execução direta e simultânea no host.

---

## 2. Padrão Obrigatório de Transparência de Passos (Step Observability)

Toda resposta final de turno operacional ou de diagnóstico deve conter a seção estruturada e factual de passos executados:

```html
<b>📋 Passos de Execução Realizados:</b>
• Passo 1: ✅ <code>ferramenta_1</code> — Resumo objetivo do que foi verificado (0.3s)
• Passo 2: ✅ <code>ferramenta_2</code> — Resumo objetivo da leitura ou teste (0.8s)
• Passo 3: ❌ <code>ferramenta_3</code> — Falha identificada e tratada com fallback (1.2s)
• <b>Status da Tarefa:</b> ✅ <i>Concluída</i>
```

### Regras do Bloco de Passos:
1. **Factual e Concreto**: Indique exatamente qual ferramenta ou ação foi executada e o que foi constatado.
2. **Ícones de Status**: Utilize `✅` para sucesso e `❌` para falhas tratadas.
3. **Status Definitivo da Tarefa**: Finalize sempre com a linha de veredito:
   - `• <b>Status da Tarefa:</b> ✅ <i>Concluída</i>`
   - OU `• <b>Status da Tarefa:</b> ⚠️ <i>Finalizada com impedimento externo comprovado: [motivo factual]</i>`

---

## 3. Resiliência e Conclusão à Prova de Falhas

### O que fazer quando uma ferramenta falha:
1. **Analise o erro**: Use o feedback retornado pela ferramenta para pivotar a abordagem.
2. **Tente caminhos alternativos**: Se o SSH falhar na porta 22, verifique portas mapeadas em `known_hosts` (ex: 22022). Se um arquivo não estiver na raiz, procure em `docs/` ou `memory/`.
3. **Se esgotar todos os caminhos do host**: Apresente o diagnóstico exaustivo de tudo que foi testado, a causa raiz confirmada e as recomendações externas claras (ex: portal web do provedor, redefinição de senha via e-mail).
4. **Nunca termine em branco**: Mesmo sob exceções não tratadas, o sintetizador de emergência deve gerar o relatório do estado atual.
