---
name: grpc-protobuf-microservices
description: >-
  Operational engineering skill for high-throughput inter-service RPC communication using gRPC, Protocol Buffers (proto3), streaming, connection pooling, and strict deadline propagation.
---

# gRPC & Protocol Buffers Microservices Skill

Guia operacional para engenharia de contratos de comunicação de baixa latência, serialização binária com Protocol Buffers e resiliência em redes de microsserviços distribuídos.

---

## 1. Contratos Protobuf (proto3) e Regras de Compatibilidade

### 1.1 Numeração Canônica de Campos
- **Campos 1 a 15**: Ocupam apenas 1 byte na serialização binária do wire format. Reserve para os identificadores mais frequentes de cada requisição.
- **Campos 16 a 2047**: Ocupam 2 bytes. Utilize para atributos secundários.
- **Faixa Reservada (19000 - 19999)**: Reservada para a biblioteca oficial do Protobuf. É proibido utilizar.

### 1.2 Regras Imutáveis de Evolução de Schema
> **Regra de Ouro**: NUNCA renumere ou mude o tipo de um campo já publicado em produção.
Quando remover um campo obsoleto, utilize a cláusula `reserved` para evitar que futuros desenvolvedores reutilizem o número ou nome:
```protobuf
syntax = "proto3";

package enterprise.billing.v1;

message Invoice {
  reserved 4, 8 to 10;
  reserved "legacy_tax_code", "discount_percentage";

  string id = 1;
  string customer_id = 2;
  int64 amount_cents = 3;
  string currency = 5;
}
```

---

## 2. Padrões de Comunicação RPC

```protobuf
service BillingService {
  // 1. Unary RPC (Requisição / Resposta Simples)
  rpc GetInvoice (GetInvoiceRequest) returns (Invoice);

  // 2. Server Streaming (Grandes volumes de logs ou feeds em tempo real)
  rpc StreamTransactions (StreamRequest) returns (stream Transaction);

  // 3. Bidirectional Streaming (Sincronização de dados bidirecional contínua)
  rpc LiveSync (stream SyncChunk) returns (stream SyncAck);
}
```

---

## 3. Conexões HTTP/2 & Deadlines Mandatórios

gRPC utiliza multiplexação sob conexões TCP persistentes com HTTP/2.

### 3.1 Propagação Estrita de Deadlines
Toda chamada gRPC cliente DEVE configurar um timeout/deadline explícito para conter travamento cascata de threads:
```python
import grpc
from enterprise.billing.v1 import billing_pb2_grpc, billing_pb2

channel = grpc.insecure_channel("billing-service.internal:50051")
client = billing_pb2_grpc.BillingServiceStub(channel)

try:
    # Deadline de 3.0 segundos
    response = client.GetInvoice(
        billing_pb2.GetInvoiceRequest(id="inv_9981"),
        timeout=3.0
    )
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        print("[!] RPC Timeout excedido. O serviço upstream demorou para responder.")
```

### 3.2 Keepalive e Detecção de Sockets Zumbis
Configure keepalives HTTP/2 no cliente para evitar que balanceadores intermediários matem silenciosamente conexões ociosas:
```python
channel = grpc.insecure_channel(
    "billing-service.internal:50051",
    options=[
        ("grpc.keepalive_time_ms", 30000),
        ("grpc.keepalive_timeout_ms", 10000),
        ("grpc.keepalive_permit_without_calls", True),
        ("grpc.http2.max_pings_without_data", 0),
    ]
)
```

---

## 4. Ferramental Integrado

Audite arquivos `.proto` com o linter embutido:
```powershell
python .agents/skills/grpc-protobuf-microservices/scripts/proto_contract_linter.py <pasta-proto>
```
O linter valida:
- Números de campo duplicados em uma mesma mensagem.
- Uso de números de campo na faixa reservada da Google (19000-19999).
- Ausência de declaração de namespace (`package`).
