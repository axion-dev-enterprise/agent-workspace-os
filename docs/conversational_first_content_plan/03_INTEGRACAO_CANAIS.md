# 03 — Integração com Canais: WhatsApp & Telegram

---

## 1. Comportamento no WhatsApp

No WhatsApp, a experiência do usuário muda radicalmente:

### Antes:
```
[16:00:00] Usuário: "preciso saber como integrar o pixel do facebook no meu bot"
[16:00:01 a 16:00:15] ... silêncio absoluto / digitando ...
[16:00:16] Bot: "Para integrar o pixel..."
```

### Com o First Content Streaming:
```
[16:00:00] Usuário: "preciso saber como integrar o pixel do facebook no meu bot"
[16:00:01] Bot: "Vou te explicar o passo a passo exato para conectar o Pixel do Facebook e o token da CAPI diretamente no seu fluxo de atendimento da AXION."
[16:00:04] Bot: [Entrega detalhada com tutorial técnico e botões rápidos:
                 🔘 [ 🚀 Ativar 30 Dias Grátis ]
                 🔘 [ 📋 Ver Código de Exemplo CAPI ]
                 🔘 [ 📞 Falar com Yan (Gestor de Tráfego) ]]
```

### Regra de Formatação:
- O First Content deve ser formatado limpo, em Português brasileiro, utilizando o padrão visual de negrito `*texto*` do WhatsApp.

---

## 2. Comportamento no Telegram

No Telegram, a edição dinâmica de mensagens permite transformar o First Content no cabeçalho do balão de progresso vivo:

### Antes:
```
⚙️ Agente iniciado — analisando seu pedido...
🧠 Passo 1: Entendendo o pedido...
⚡ Passo 2: Executando: exec_command
```

### Com o First Content Streaming:
```
💬 "Vou inventariar os serviços ativos no PM2 e verificar o log de erros das últimas 2 horas no Windows."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ Diagnosticando processos do host...
⏳ Inspecionando saídas do terminal...
🎯 Validando integridade da execução...
```

---

## 3. Segregação de Persona (Admin vs Lead)

O prompt de streaming respeita quem está chamando:
1. **Se for Admin (Operator / Equipe):**  
   O First Content foca em diagnóstico técnico, arquitetura, automação e comandos operacionais.
2. **Se for Lead (WhatsApp Comercial):**  
   O First Content foca em acolhimento, entendimento do modelo de negócio do cliente, apresentação das soluções e esclarecimento de dúvidas da oferta (30 dias free, sem taxa da Meta).
