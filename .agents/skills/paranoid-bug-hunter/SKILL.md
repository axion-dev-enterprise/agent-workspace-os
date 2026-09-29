---
name: paranoid-bug-hunter
description: >-
  Operational skill for adversarial bug hunting, paranoid code auditing, edge-case discovery,
  race condition hunting, schema divergence verification, and deep invariant checking across enterprise systems.
---

# Paranoid Bug Hunter -- Manual Operacional de Auditoria Adversaria e Caça a Bugs

Skill operacional canonica para auditoria adversaria, caca sistematica de falhas, diagnostico de bugs ocultos e analise implacavel de invariantes de sistema. Aplica a mentalidade "Assume Everything is Broken" para antecipar desastres em producao antes que eles ocorram.

---

## 1. Filosofia Operacional: O Modo Paranoico

Em sistemas distribuidos e aplicacoes financeiras de missao critica, testes convencionais ("happy path") falham em detectar mais de 80% dos bugs reais. A metodologia **Paranoid Bug Hunter** opera sob 5 premissas fundamentais:

1. **Assuma Concorrencia Hostil:** Qualquer endpoint que consulte saldo ou status sera invocado 50 vezes no mesmo milissegundo. Sem locks explicitos (`FOR UPDATE`), o sistema ira falhar com double-spending.
2. **Assuma Desalinhamento de Contrato:** O backend nunca retorna exatamente o formato que o frontend espera. Campos opcionais serao nulos, arrays serao vazios, datas virao como ISO-8601 ou epoch, e chaves variam entre `snake_case` e `camelCase`.
3. **Assuma Fragilidade de Webhooks:** Provedores de pagamento (Stripe, Asaas, Mercado Pago, bancos PIX) reenviarao webhooks em ordem trocada, duplicados ou com status em caixa baixa (`'paid'` vs `'PAID'`).
4. **Assuma Perda de Estado em Long-Polling:** Intervalos de pooling (`setInterval`) vazarao memoria, continuarao chamando a API apos o teardown do componente ou falharao silenciosamente por expiracao de sessao.
5. **Assuma a Armadilha do Zero:** O numero zero (`0`) e um valor financeiro perfeitamente valido, mas e tratado como falso por operadores logicos classicos (`||`).

---

## 2. As 5 Fases do Ciclo de Caça Paranoica

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ 1. RECONHECIMENTO  │ ──> │ 2. MAPA DE VETORES │ ──> │ 3. HIPOTESE DE     │
│ Scanner estatico & │     │ Mapeamento das 7   │     │    STRESS          │
│ analise de rotas   │     │ fronteiras criticas│     │ Cenarios extremos  │
└────────────────────┘     └────────────────────┘     └─────────┬──────────┘
                                                                │
┌────────────────────┐     ┌────────────────────┐               ▼
│ 6. PORTAO FINAL    │ <── │ 5. CORRECAO        │ <── ┌────────────────────┐
│ Re-scan estatico & │     │    CIRURGICA       │     │ 4. TESTE DE        │
│ build de producao  │     │ Atomic patch & PEV │     │    REPRODUCAO      │
└────────────────────┘     └────────────────────┘     │ Prova empirica     │
                                                      └────────────────────┘
```

### Fase 1: Reconhecimento Sistematico
Execute o scanner estatico para levantar potenciais armadilhas e anomalias no diretorio de destino:
```bash
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir <target_dir>
```

### Fase 2: Mapeamento dos 7 Vetores Criticos
Identifique quais dos 7 vetores afetam a funcionalidade sob analise (ver Secao 3).

### Fase 3: Formulacao da Hipotese de Stress
Questione os limites:
- O que acontece se a rede cair durante o commit da transacao?
- O que acontece se duas requisicoes simultaneas tentarem debitar a mesma conta?
- O que acontece se o payload recebido contiver `{}` ou campos ausentes?

### Fase 4: Teste de Reproducao Empirico
Antes de tocar no codigo, formule um teste automatizado ou script isolado que falhe comprovadamente devido a hipotese.

### Fase 5: Correcao Cirurgica
Aplique a solucao minima e robusta, evitando alteracoes que introduzam instabilidade colateral.

### Fase 6: Portao de Verificacao (Zero False Positives)
Execute a suite de testes, o scanner estatico e a compilacao completa para confirmar que nao ha regressoes.

---

## 3. Matriz dos 7 Vetores Criticos de Auditoria

### Vetor 1: Concorrencia, Saldos e Ausencia de Row Locks
- **Sintoma:** Queries SQL do tipo `SELECT balance FROM wallets WHERE id = :id` seguidas de `UPDATE wallets SET balance = balance - :amount`.
- **Risco:** Duas requisicoes simultaneas leem o mesmo saldo e ambas executam o debito, levando o saldo ao negativo ou causando perda financeira direta.
- **Solucao Obrigatoria:**
  ```sql
  -- Postgres / MySQL: Row Locking
  SELECT balance FROM wallets WHERE id = :id FOR UPDATE;
  
  -- Ou atualizacao atomica condicional:
  UPDATE wallets 
  SET balance = balance - :amount 
  WHERE id = :id AND balance >= :amount;
  ```

### Vetor 2: Divergencia de Schema e Tipos (API vs Frontend)
- **Sintoma:** Frontend consumindo `sub.merchant.name` quando o backend entrega `sub.merchant_name`, ou consumindo `tx.amount` (reais) quando o backend emite `tx.amountCents` (centavos).
- **Risco:** Falha silenciosa de renderizacao, telas em branco ou exibicao de valores multiplicados/divididos por 100 incorretamente.
- **Solucao Obrigatoria:** Padronizar tipagem compartilhada ou aplicar mapeamento defensivo no adaptador da API:
  ```typescript
  const merchantName = sub?.merchant?.name ?? sub?.merchant_name ?? 'Estabelecimento';
  ```

### Vetor 3: Fronteiras de Autenticacao e Polling Publico
- **Sintoma:** Telas publicas (checkout, pagamento via link, portal de fatura) que executam polling em endpoints autenticados que exigem token Bearer de merchant ou admin.
- **Risco:** Requisicao retorna HTTP 401 Unauthorized, gerando loop infinito de erros no console do navegador e deixando o pagador sem confirmacao de pagamento.
- **Solucao Obrigatoria:** Endpoint publico dedicado e isolado para consulta por token publico ou ID de pagamento:
  ```typescript
  // Public route: /api/v1/public/transactions/:token
  // Protected route: /api/v1/transactions/:id
  ```

### Vetor 4: Invariantes de Negocio e Liquidação Financeira
- **Sintoma:** Liquidacao imediata de vendas de cartao de credito (D+0) sem respeitar o prazo contratual (ex: D+14 ou D+30), ou aplicacao de taxas trocadas entre modalidades (PIX vs Cartao).
- **Risco:** Adiantamento indevido de capital, exposicao a chargebacks e reconciliacao bancaria negativa.
- **Solucao Obrigatoria:** Calcular data de liquidacao (`settledAt`) de acordo com o metodo de pagamento e politica de parcelamento:
  ```typescript
  const settlementDays = paymentMethod === 'PIX' ? 0 : (merchant.settlementDaysCard ?? 14);
  const releaseDate = addDays(new Date(), settlementDays);
  ```

### Vetor 5: Case-Sensitivity, Enums e Armadilha do Zero
- **Sintoma:** Comparacoes estritas de enums como `status === 'ACTIVE'` quando o payload externo ou banco envia minúsculas (`'active'`).
- **Sintoma:** Uso de `amount || 0` ou `fee || 100`.
- **Risco:** Se o valor legitimo for `0`, o operador `||` descarta o zero e adota o fallback indesejado.
- **Solucao Obrigatoria:**
  ```typescript
  // Normalizacao de enum:
  const isActive = (status || '').toUpperCase() === 'ACTIVE';

  // Nullish coalescing seguro:
  const feeCents = rawFee ?? 0;
  ```

### Vetor 6: Idempotencia e Ciclo de Vida de Webhooks
- **Sintoma:** Handler de webhook que processa eventos de `PAYMENT_CONFIRMED` e atualiza a fatura sem verificar se a transacao ja foi cancelada ou reembolsada.
- **Sintoma:** Reutilizacao do mesmo `correlation_id` em renovacoes subsequentes de assinaturas mensais.
- **Risco:** Ressurreicao indevida de pagamentos mortos e colisao de chaves de transacao no gateway adquirente.
- **Solucao Obrigatoria:**
  ```typescript
  if (isTerminalStatus(currentTransaction.status)) {
    return { ack: true, reason: 'Already in terminal state' };
  }
  const renewalCorrelationId = `sub_${sub.id}_cycle_${cycle}_${crypto.randomUUID()}`;
  ```

### Vetor 7: Hardcoded Endpoints, Segredos e Exposição de Rede
- **Sintoma:** Enderecos de IPs de VPS ou bancos de dados escritos diretamente no codigo ou PINs/senhas padrao em texto puro.
- **Risco:** Quebra de portabilidade, violacao do principio Zero Attack Surface e exposicao a vazamentos no Git.
- **Solucao Obrigatoria:**
  ```typescript
  // Zero IP hardcoded: use Zero Trust Hostnames ou variaveis de ambiente
  const gatewayUrl = process.env.PAYMENT_GATEWAY_URL || 'https://gw.example.com';
  ```

---

## 4. O Utilitario CLI Standalone Universal

A skill acompanha o motor de auditoria estatica em `.agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py`, 100% compativel com qualquer codebase (TypeScript, JavaScript, Python, Go, Rust, Java, SQL, PHP) e desacoplado de schemas especificos via perfis modulares.

### Perfis de Auditoria Disponiveis (`--profile`):
- `generic`: Antipadroes universais (falsy zeroes em contadores/limites, timers vazados, falta de try/catch em async, precisao float, enums case-sensitive).
- `security`: Exposicao de rede (IPs fixos), vazamento de credenciais/chaves, SQL injection por concatenacao, headers CORS permissivos (`*`).
- `concurrency`: Concorrencia transacional, falta de lock de linha em recursos escassos, ressurreicao de maquina de estados terminada, colisao de chaves de idempotencia.
- `fintech`: Invariantes financeiras, prazos de liquidacao D+N e unidades monetarias (centavos vs float).
- `all`: Execucao de todos os pacotes de regras (padrao).

### Comandos Canônicos Multi-Stack:
```bash
# 1. Varredura generica em qualquer aplicacao ou biblioteca
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir packages/my-lib --profile generic

# 2. Auditoria estrita de concorrencia e race conditions em microsservico
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir services/order-service --profile concurrency

# 3. Auditoria de segredos e perimetro de seguranca
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir apps/my-app --profile security --severity HIGH

# 4. Injetar pacote de regras customizadas da organizacao (JSON)
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir . --rules rules/org_rules.json

# 5. Gerar relatorio em Markdown para auditoria de compliance
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir apps/my-app --report docs/AUDIT_REPORT.md

# 6. Saida estruturada em JSON para pipelines de CI/CD
python .agents/skills/paranoid-bug-hunter/scripts/scan_codebase_bugs.py --dir services/api --profile all --json
```

---

## 5. Checklist Pre-Mortem Obrigatório Antes de Concluir Tarefas

Antes de finalizar qualquer investigacao ou fix, o agente deve responder "SIM" com evidencias concretas para as 5 perguntas:
- [ ] **1. Concorrencia:** O codigo foi testado ou protegido contra mutacoes concorrentes simultaneas?
- [ ] **2. Contrato:** O payload retornado foi inspecionado em sua estrutura real (`curl -s -L` ou teste com mock)?
- [ ] **3. Falsy/Null:** Valores como `0`, `false`, `""` e `undefined` foram avaliados isoladamente?
- [ ] **4. Build & Typecheck:** `npm run build` ou `tsc --noEmit` executou com sucesso (0 erros de tipagem)?
- [ ] **5. Testes Unitarios:** Toda a suite relevante rodou e passou com 100% de sucesso?

---

## 6. Documentos de Referência
- [references/bug_taxonomy_and_patterns.md](references/bug_taxonomy_and_patterns.md) -- Catalogo aprofundado de 20 anti-padroes comuns e resolucoes.
- [references/reproduction_test_recipes.md](references/reproduction_test_recipes.md) -- Receitas de testes de reproducao de concorrencia e falhas de contrato.
