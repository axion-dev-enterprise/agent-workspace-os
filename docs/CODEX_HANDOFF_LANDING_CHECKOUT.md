# 📋 PROMPT DE ENGENHARIA & HANDOFF PARA O AGENTE CODEX (GPT)
**Projeto:** AXION Enterprise — Autoatendimento IA para WhatsApp  
**Módulos:** Landing Page de Conversão + Integração Checkout Axion-Pay (Trial 30D) + Onboarding WhatsApp (QR/Pairing) + Pixel/CAPI

---

## 🎯 1. CONTEXTO & OBJETIVO DO AGENTE

Você é o engenheiro responsável no workspace `AXION - MAIN` por implementar a esteira completa de aquisição, checkout e onboarding do produto **Autoatendimento com Inteligência Artificial para WhatsApp**.

Sua missão é entregar uma experiência **100% sem atrito**, onde o cliente:
1. Conhece o produto em uma **Landing Page de altíssima conversão**.
2. Seleciona a modalidade de número (**Número Próprio R$ 0** ou **Chip Dedicado R$ 50/mês**).
3. Insere o cartão de crédito no **Axion-Pay** para iniciar os **30 dias de teste grátis** sem cobrança da mensalidade base.
4. Conecta seu WhatsApp em menos de 2 minutos via **QR Code** ou **Pairing Code de 8 dígitos**.
5. Configura seu **Pixel ID do Facebook** e **Token CAPI** para otimizar suas campanhas de tráfego pago.

---

## 💼 2. REGRAS DE NEGÓCIO E PRECIFICAÇÃO (INVIOLÁVEIS)

1. **Trial de 30 Dias:**
   - Todo novo cliente tem direito a **30 dias 100% gratuitos** da plataforma de IA.
   - A ativação do trial **exige cartão de crédito** no checkout para prevenção de abusos e retenção.
   - No plano de Número Próprio, o valor cobrado no ato é **R$ 0,00** (ou validação de R$ 1,00 estornada na hora).
   - A cobrança da mensalidade só ocorre no **31º dia**. O cliente pode cancelar a qualquer momento sem multa.

2. **Modalidades de Número:**
   - **Opção A — Número Próprio da Empresa:** **R$ 0,00 nos primeiros 30 dias** (depois R$ 97,00/mês). O cliente escaneia o QR Code do WhatsApp comercial que ele já possui.
   - **Opção B — Número/Chip Dedicado AXION:** **R$ 50,00/mês** fixos desde o 1º mês referente ao chip e infraestrutura da linha virtual que a AXION fornece.

3. **Diferencial Anti-Meta (Zero Burocracia):**
   - Não usa a API Cloud Oficial da Meta: o cliente **NÃO paga taxas em dólar por conversa** ao Facebook e **NÃO precisa de aprovação de templates**.
   - Conexão direta multi-device (Baileys Bridge) com botões rápidos nativos e respostas em menos de 1 segundo.

4. **Integração de Marketing (Pixel & CAPI):**
   - O sistema possui campos dedicados para **Pixel ID** e **Token CAPI (API de Conversão da Meta)**.
   - O robô classifica as conversas e envia eventos automáticos (`Lead`, `Contact`, `Schedule`) para o Gerenciador de Anúncios.

---

## 🏗️ 3. ARQUITETURA DO PROJETO & DIRETÓRIOS

Trabalhe dentro da estrutura de repositório existente:
- **Landing Page & Onboarding:** `apps/landing/` (HTML5, Tailwind CSS via CDN ou CSS puro, responsivo, dark-mode nativo).
- **Checkout & Gateway:** `apps/axion-pay/` (endpoints REST documentados em `apps/axion-pay/CUSTOM_CHECKOUT_GUIDE.md` e `ROUTES.md`).
- **Bridge WhatsApp:** `scripts/whatsapp_bridge/` (endpoints em `http://127.0.0.1:4114` para geração de QR Code, Pairing Code e status da sessão).

---

## 💻 4. ESPECIFICAÇÕES DOS ENTREGÁVEIS

### Entregável 1: Landing Page de Conversão (`apps/landing/index.html`)
Desenvolva uma página moderna com visual tecnológico dark-mode (paleta: `#0b0f19`, ciano `#38bdf8`, acentos em verde `#10b981` e tipografia Inter/JetBrains Mono).

**Seções Mandatórias:**
1. **Navbar Fixa:** Logo AXION, links de âncora (*Como Funciona*, *Recursos*, *Planos*, *FAQ*) e botão CTA de destaque: `[ Testar 30 Dias Grátis ]`.
2. **Hero Section:**
   - Headline: *"Automatize seu WhatsApp com Inteligência Artificial Humanizada e Venda 24h por Dia"*.
   - Subheadline: *"Respostas em menos de 1 segundo com botões interativos, zero taxas por mensagem da Meta e integração direta com seu Pixel e CAPI."*
   - Simulação interativa animada de um chat de WhatsApp com botões clicáveis.
   - Badge: `🎉 30 DIAS 100% GRATUITOS • SEM CONTRATO • CANCELE QUANDO QUISER`.
3. **Quadro Comparativo (Meta Cloud API vs AXION):**
   - Custo por conversa: *Taxas em dólar* vs *R$ 0,00 Ilimitado*.
   - Burocracia: *Aprovação demorada de mensagens* vs *Liberdade total imediata*.
   - Tráfego Pago: *Setup complexo* vs *Pixel & CAPI em 1 clique*.
4. **Cards de Seleção de Modalidade (Pricing):**
   - Card 1: **Usar Meu WhatsApp Atual** — *R$ 0,00 por 30 dias*, depois R$ 97/mês.
   - Card 2: **Quero um Número Novo AXION** — *R$ 50,00/mês* fixos da linha dedicada.
5. **FAQ (Perguntas Frequentes):**
   - *"Meu WhatsApp corre risco de banimento?"* (Explicação dos limites seguros e aquecimento de chip).
   - *"Preciso pagar a Meta?"* (Não, conexão via Baileys multi-device).
   - *"Como funciona o teste de 30 dias?"* (Cadastre o cartão, use livremente por 30 dias; se não gostar, cancele com 1 clique).
6. **Footer Corporativo:** Termos de Uso, Políticas de Privacidade e selos de segurança SSL 256-bit.

---

### Entregável 2: Modal de Checkout Transparente Axion-Pay
Integrado diretamente na Landing Page sem redirecionamentos externos:
- **Campos do Cliente:** Nome Completo, E-mail, WhatsApp (com máscara `(XX) XXXXX-XXXX`), CPF/CNPJ.
- **Campos do Cartão de Crédito:** Número do Cartão, Nome no Cartão, Vencimento (MM/AA), CVV.
- **Resumo do Pedido Dinâmico:**
  - Se Modalidade = Número Próprio: *"Total hoje: R$ 0,00 (Primeira cobrança de R$ 97,00 em 30 dias)"*.
  - Se Modalidade = Chip AXION: *"Total hoje: R$ 50,00 (Taxa da linha telefônica dedicada)"*.
- **Comunicação com Backend:**
  - Chama a API do Axion-Pay para validação do cartão e registro do cliente (`tenant`).
  - Em caso de sucesso, redireciona suavemente para a tela de **Onboarding**.

---

### Entregável 3: Tela de Onboarding & Pareamento (`apps/landing/onboarding.html`)
Após a confirmação do cartão, o cliente cai na tela de ativação da instância:
1. **Passo 1 — Conexão do WhatsApp:**
   - **Aba QR Code:** Exibe o QR Code dinâmico gerado pelo backend do Baileys com indicador de expiração (refresh a cada 20s).
   - **Aba Código de Pareamento (Mobile):** Campo para o cliente digitar o número e receber o código alfanumérico de 8 dígitos (ex: `A7B4-9K2M`) para conectar pelo celular sem precisar de câmera.
   - **Indicador de Status em Tempo Real:** Badge pulsante (`Aguardando Leitura...` -> `Conectado com Sucesso! 🟢`).
2. **Passo 2 — Conexão de Tráfego Pago (Opcional):**
   - Campo para colar o **Pixel ID da Meta**.
   - Campo para colar o **Token da CAPI (Conversions API)**.
   - Tooltip explicativo de onde encontrar esses dados no Gerenciador de Eventos da Meta.
3. **Passo 3 — Mensagem de Teste Instantânea:**
   - Assim que o WhatsApp conecta, o sistema envia uma mensagem de teste para o número do próprio cliente com botões clicáveis, comprovando que o agente já está operando.

---

## ✅ 5. CRITÉRIOS DE ACEITE (TESTES MANDATÓRIOS)

Para considerar a tarefa concluída com nota máxima:
- [ ] **Responsividade:** Layout testado e perfeito em telas mobile (360px a 430px) e desktop (1080p a 4K).
- [ ] **Zero Redirecionamentos:** O checkout roda via modal ou tela embutida, mantendo o usuário no mesmo domínio.
- [ ] **Máscaras e Validações:** Campos de cartão (Luhn algorithm), CPF/CNPJ e telefone com máscaras dinâmicas e validação em tempo real.
- [ ] **Feedback de Estado:** Botões exibem spinners (`Carregando...`, `Processando autorização...`) e tratam mensagens de erro amigáveis caso o cartão seja recusado.
- [ ] **Troca Fluida QR / Pairing:** O usuário consegue alternar facilmente entre escanear o QR Code e digitar o código de 8 dígitos.
- [ ] **Persistência de Dados:** O formulário salva localmente as informações digitadas para não forçar o usuário a redigitar caso ocorra refresh acidental.
- [ ] **Segurança:** Nenhuma credencial privada ou chave mestra é exposta no JavaScript client-side do navegador.

---

## 🚀 6. INSTRUÇÕES DE EXECUÇÃO PASSO A PASSO PARA O CODEX

1. **Passo 1:** Analise os arquivos em `apps/landing/` e utilize os padrões de estilo já presentes no repositório.
2. **Passo 2:** Crie ou atualize `apps/landing/index.html` com a estrutura completa da Landing Page, incluindo a copy comercial persuasiva e o modal de checkout.
3. **Passo 3:** Crie `apps/landing/onboarding.html` com os componentes visuais de conexão do WhatsApp (QR Code / Pairing Code) e os inputs de Pixel/CAPI.
4. **Passo 4:** Implemente o script client-side (`apps/landing/assets/checkout.js` e `onboarding.js`) conectando as chamadas HTTP mockadas/reais com o Axion-Pay e a API do WhatsApp Bridge.
5. **Passo 5:** Valide o resultado no navegador, garantindo que não existam erros de console (`Uncaught TypeError`, links quebrados ou problemas de CORS).
