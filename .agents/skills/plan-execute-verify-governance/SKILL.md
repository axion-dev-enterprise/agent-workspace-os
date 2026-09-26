---
name: plan-execute-verify-governance
description: >-
  Operational skill for Plan-Execute-Verify (PEV) lifecycle, systematic decision-making frameworks, pre-mortem risk audits, and strict verification-before-completion evidence gates.
---

# Plan-Execute-Verify (PEV) & Decision Governance Skill

Skill operacional canônica para elevar a assertividade técnica, governança de pipelines e rigor na tomada de decisões em agentes de IA. Implementa os frameworks de excelência da comunidade (**`obra/superpowers`**, **`GeoAgents`**, **`thinking-skills`** e **ADR Governance**).

---

## 1. A Lei de Ferro da Acertividade (Zero False Positives)

> **"NENHUMA AFIRMAÇÃO DE CONCLUSÃO SEM EVIDÊNCIA DE VERIFICAÇÃO RECENTE."**

É terminantemente proibido ao agente declarar que um bug foi corrigido, um endpoint está no ar ou um teste passou com base em:
- Suposições (*"o código deve funcionar"*);
- Compilação estática bem-sucedida sem teste de execução;
- Testes executados em turnos anteriores antes da última edição de código.

### O Gate Function Mandatório:
1. **IDENTIFICAR**: Selecionar o comando específico que comprova a asserção (ex: `pytest tests/test_auth.py`, `curl -s -L https://api...`).
2. **EXECUTAR**: Rodar o comando completo e fresco via terminal.
3. **LER**: Inspecionar minuciosamente o código de saída (*exit code*), corpo HTTP e `stderr`.
4. **VERIFICAR**: Conferir se as asserções e payloads esperados estão factualmente presentes.
5. **REIVINDICAR**: Somente após o passo 4, emitir a mensagem de conclusão ao usuário com a evidência explícita.

---

## 2. A Máquina de Estados Finita PEV (6 Fases de Execução)

Para tarefas complexas ou que envolvam mutações críticas, o agente opera em 6 fases sequenciais:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 1. ESPECIFICAÇÃO │ ──► │ 2. PRÉ-VOO       │ ──► │ 3. EXECUÇÃO      │
│ Decomposição e   │     │ Whoami, branch,  │     │ Passos atômicos  │
│ critérios claros │     │ portas e estado  │     │ com rollback     │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
┌──────────────────┐     ┌──────────────────┐              ▼
│ 6. RELATÓRIO     │ ◄── │ 5. TEARDOWN      │ ◄── ┌──────────────────┐
│ Diário diário    │     │ Purgar mocks e   │     │ 4. VERIFICAÇÃO   │
│ e blackboard     │     │ dados de teste   │     │ Portão de testes │
└──────────────────┘     └──────────────────┘     │ empíricos        │
                                                  └──────────────────┘
```

---

## 3. Modelos Mentais para Tomada de Decisões de Engenharia

Antes de arquitetar uma solução ou alterar código existente, o agente aplica:

### 3.1 Pre-Mortem & Red Teaming
*Pergunta guia:* **"Imagine que esta alteração foi para produção e causou uma queda crítica. O que quebrou?"**
- Concorrência ou race conditions?
- Ausência de timeout em chamada de rede externa?
- Falta de índice no banco gerando Full Table Scan?
- Vazamento acidental de chave de API em log ou diff?

### 3.2 Chesterton's Fence & Efeitos de Segunda Ordem
*Pergunta guia:* **"Por que este código/configuração foi colocado aqui originalmente?"**
- Nunca remova validações, headers de segurança, retries ou middlewares sem antes diagnosticar sua intenção original.
- Avalie o efeito cascata: a alteração desta rota quebra clientes legados ou webhooks?

### 3.3 Primeiro Princípio & Inversão
- Não copie soluções prontas por analogia sem entender o protocolo subjacente.
- Inversão (*Jacobi*): em vez de apenas buscar o caminho feliz (*happy path*), desenhe primeiro como tratar as falhas (*fail gracefully*).

---

## 4. Utilitários Python Canônicos (Zero Dependências / Stdlib)

Localizados em `scripts/` desta skill:

### 4.1 Portão de Verificação Empírica (`verify_gate.py`)
Executa o comando de teste, avalia exit codes e padrões de texto, gerando recibo criptográfico SHA-256:
```bash
python .agents/skills/plan-execute-verify-governance/scripts/verify_gate.py "pytest tests/" --expect "passed"
```
*Se a verificação falhar, o script encerra com exit code 1, bloqueando avanços prematuros.*

### 4.2 Analisador Pre-Mortem de Risco (`pre_mortem_analyzer.py`)
Inspeciona o diff git recente em busca de credenciais vazadas, violações de Chesterton's Fence, remoção de timeouts e código sem testes:
```bash
python .agents/skills/plan-execute-verify-governance/scripts/pre_mortem_analyzer.py git
```
*Classifica o risco em LOW, MEDIUM, HIGH ou CRITICAL.*

### 4.3 Gerador de ADRs Padronizados (`adr_scaffold.py`)
Cria um registro imutável de decisão arquitetural sob `docs/adr/`:
```bash
python .agents/skills/plan-execute-verify-governance/scripts/adr_scaffold.py "Uso de Redis 7 para Distributed Locks" --scope "Backend"
```

---

## 5. Padrões TDD para Agentes (Red-Green-Refactor)

Ao implementar correções de bugs ou novas funcionalidades:
1. **RED**: Escrever um teste automatizado que reproduza o problema e **assistir o teste falhar**.
2. **GREEN**: Escrever a quantidade mínima de código necessária para o teste passar.
3. **REFACTOR**: Limpar e organizar o código mantendo os testes continuamente verdes.
