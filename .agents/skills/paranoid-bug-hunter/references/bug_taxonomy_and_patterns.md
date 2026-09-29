# Catalogo Detalhado de Taxonomia de Bugs e Anti-Padroes

Este documento cataloga 20 padroes de vulnerabilidade, falha logica e regressao de sistema frequentemente ignorados em auditorias superficiais.

---

## 1. Concorrencia e Integridade Transacional

### Padrao 1.1: Double-Spending por Leitura Desprotegida de Saldo
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Condicao de corrida entre a leitura e a escrita
  const wallet = await db.wallet.findUnique({ where: { id } });
  if (wallet.balance < amount) throw new Error("Insufficient funds");
  await db.wallet.update({ where: { id }, data: { balance: wallet.balance - amount } });
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Transacao com lock de linha explicito ou decremento condicional
  await db.$transaction(async (tx) => {
    const rows = await tx.$queryRaw`SELECT balance FROM "Wallet" WHERE id = ${id} FOR UPDATE`;
    if (rows[0].balance < amount) throw new Error("Insufficient funds");
    await tx.wallet.update({ where: { id }, data: { balance: { decrement: amount } } });
  });
  ```

### Padrao 1.2: Check-Then-Act em Criacao de Contas ou Registros Unicos
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Duas requisicoes simultaneas checam 'exists' ao mesmo tempo
  const exists = await db.user.findFirst({ where: { taxId } });
  if (!exists) {
    await db.user.create({ data: { taxId, name } });
  }
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Restricao UNIQUE no banco de dados e captura de violacao (P2002 no Prisma)
  try {
    await db.user.create({ data: { taxId, name } });
  } catch (err: any) {
    if (err.code === 'P2002') throw new DuplicateTaxIdError();
    throw err;
  }
  ```

---

## 2. Contratos de API e Divergencia de Tipos

### Padrao 2.1: Objeto Aninhado vs Propriedade Plana (Nested vs Flat)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Se a API retornar merchant_name plano, sub.merchant.name lanca TypeError
  const name = sub.merchant.name;
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Acesso seguro e fallback bidirecional
  const name = sub?.merchant?.name ?? sub?.merchant_name ?? "Estabelecimento Padrao";
  ```

### Padrao 2.2: Desalinhamento de Unidade Monetaria (Reais vs Centavos)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Assume que o backend envia float em reais, cobrando R$ 10.000 em vez de R$ 100
  const display = `R$ ${payment.amount.toFixed(2)}`;
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Inspecionar o sufixo 'Cents' e manipular estritamente como centavos inteiros
  const cents = payment.amountCents ?? Math.round((payment.amount ?? 0) * 100);
  const display = `R$ ${(cents / 100).toFixed(2).replace('.', ',')}`;
  ```

---

## 3. Limites de Autenticacao e Polling Publico

### Padrao 3.1: Polling Publico em Rota Privada
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Checkout deslogado tenta ler /api/v1/admin/transactions/123
  fetch(`/api/v1/admin/transactions/${txId}`); // HTTP 401 Unauthorized em loop
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Token publico ou endpoint anonimo delimitado estritamente por ID de cobranca
  fetch(`/api/v1/public/charge-status?token=${publicCheckoutToken}`);
  ```

### Padrao 3.2: Intervalo de Polling Sem Teardown (Leak de CPU e Socket)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: O timer continua rodando infinitamente apos o usuario sair da pagina
  useEffect(() => {
    setInterval(() => checkStatus(), 3000);
  }, []);
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Teardown obrigatorio e encerramento ao atingir status terminal
  useEffect(() => {
    const timer = setInterval(async () => {
      const finished = await checkStatus();
      if (finished) clearInterval(timer);
    }, 3000);
    return () => clearInterval(timer);
  }, []);
  ```

---

## 4. Invariantes de Negocio e Calculos Financeiros

### Padrao 4.1: Falha de Arredondamento IEEE 754 (Float Math)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: 0.1 + 0.2 === 0.30000000000000004
  const netAmount = amount - (amount * feePercent / 100);
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Toda a computacao financeira realizada em centavos inteiros com Math.round
  const feeCents = Math.round((amountCents * feeBps) / 10000);
  const netAmountCents = amountCents - feeCents;
  ```

### Padrao 4.2: Antecipacao Indevida de Liquidacao (D+0 vs D+14)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Libera saldo de cartao imediatamente para saque no mesmo segundo
  await creditMerchantAvailableBalance(tx.merchantId, tx.netAmountCents);
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Pix libera D+0; Cartao de Credito credita saldo pendente com data futura de liberacao
  if (tx.method === 'PIX') {
    await creditAvailableBalance(tx.merchantId, tx.netAmountCents);
  } else {
    await creditPendingSettlement(tx.merchantId, tx.netAmountCents, calculateSettlementDate(tx));
  }
  ```

---

## 5. Case-Sensitivity, Enums e Coalescencia Nula

### Padrao 5.1: Comparacao Estrita Case-Sensitive de Enums Externos
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Se o webhook do banco mandar status 'paid' ou 'canceled', a fita falha
  if (webhookPayload.status === 'PAID') { markAsPaid(); }
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Normalizacao canonica para maiusculas antes da comparacao
  if ((webhookPayload.status || '').toUpperCase() === 'PAID') { markAsPaid(); }
  ```

### Padrao 5.2: Supressao do Zero com Operador OR (||)
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Se a taxa configurada for 0% (promocao de lancamento), ela vira 199 centavos!
  const fee = merchant.configuredFee || 199;
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Nullish coalescing operator (??) preserva zero e falso
  const fee = merchant.configuredFee ?? 199;
  ```

---

## 6. Webhooks e Idempotencia

### Padrao 6.1: Ressurreicao de Fatura Cancelada por Webhook Atrasado
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: Webhook de confirmacao atrasado 3 dias reabre uma cobranca que ja foi cancelada
  async function handleWebhook(event: WebhookEvent) {
    if (event.type === 'PAYMENT_RECEIVED') {
      await db.invoice.update({ where: { id: event.invoiceId }, data: { status: 'PAID' } });
    }
  }
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Verificar maquina de estados finita. Estados terminais sao irreversiveis.
  const invoice = await db.invoice.findUnique({ where: { id: event.invoiceId } });
  if (['CANCELED', 'REFUNDED', 'EXPIRED'].includes(invoice.status)) {
    logger.warn(`Ignorando evento para fatura em estado terminal: ${invoice.status}`);
    return;
  }
  ```

### Padrao 6.2: Reutilizacao de Correlation ID em Renovacoes Recorrentes
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: No mes seguinte, o banco recusa a cobranca com "Duplicate Idempotency Key"
  const chargeId = `sub_${subscription.id}`;
  await paymentGateway.charge({ idempotencyKey: chargeId, amount: subscription.amount });
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Chave de idempotencia composta por ciclo e identificador unico
  const idempotencyKey = `sub_${subscription.id}_cycle_${subscription.billingCycles + 1}_${crypto.randomUUID()}`;
  await paymentGateway.charge({ idempotencyKey, amount: subscription.amount });
  ```

---

## 7. Hardcoded Secrets e Exposicao de Perimetro

### Padrao 7.1: IP Publico de VPS ou Banco em Codigo-Fonte
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: IP exposto publicamente no Git e acoplado a maquina especifica
  const redis = new Redis("redis://195.200.12.34:6379");
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Hostname Zero Trust ou injecao via variavel de ambiente do Vault
  const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");
  ```

### Padrao 7.2: PINs ou Senhas Hardcoded para Teste
- **Anti-padrao:**
  ```typescript
  // QUEBRADO: PIN '1234' deixado como fallback para desenvolvimento em producao
  if (inputPin === (user.pin || "1234")) { authorizeTransfer(); }
  ```
- **Padrao Correto:**
  ```typescript
  // CORRETO: Sem fallback para senhas; rejeitar explicitamente se ausente
  if (!user.pin) throw new UnauthorizedError("PIN nao configurado");
  const isValid = await bcrypt.compare(inputPin, user.pin);
  ```
