# Referência Operacional: Gmail, Mensageria & Configurações de Caixa

Guia de comandos GAM para automação e padronização do Gmail corporativo.

---

## 1. Assinaturas de E-mail (Signatures)

```powershell
# Definir assinatura HTML para um usuário
gam user <email> signature html "<b>Lead Engineer</b><br>Enterprise Organization<br>https://example.com"

# Aplicar assinatura padrão para todos os usuários do domínio
gam all users signature html "<b>Enterprise Team</b><br>example.com"

# Exibir assinatura atual de um usuário
gam user <email> print signature
```

---

## 2. Filtros e Encaminhamentos

### 2.1 Encaminhamento Automático (Forwarding)
```powershell
# Adicionar endereço de encaminhamento e ativar
gam user <email> add forwardingaddress support@example.com
gam user <email> forward on to support@example.com keep

# Desativar encaminhamento automático
gam user <email> forward off
```

### 2.2 Criação de Filtros
```powershell
# Listar todos os filtros existentes
gam user <email> print filters

# Criar filtro para marcar e rotular mensagens de um remetente específico
gam user <email> filter from "financeiro@banco.com" label "Bancos" markread

# Criar filtro para aplicar estrela ou não enviar para spam
gam user <email> filter from "@clienteimportante.com" star neverspam
```

---

## 3. Resposta Automática de Ausência (Vacation Responder)

```powershell
# Ativar resposta automática com assunto e corpo
gam user <email> vacation on subject "Ausente do Escritório" message "Estou em atendimento externo e responderei assim que possível."

# Desativar resposta automática
gam user <email> vacation off
```

---

## 4. Delegação de Acesso à Caixa de Entrada (Delegates)

```powershell
# Conceder permissão de leitura/envio da caixa para um colega sem compartilhar senha
gam user <email_dono> delegate to <email_assistente>

# Listar delegados de um usuário
gam user <email> print delegates

# Remover delegação de acesso
gam user <email_dono> delete delegate <email_assistente>
```

---

## 5. Auditoria e Busca de Mensagens

```powershell
# Verificar contagem de mensagens e espaço utilizado
gam user <email> show mailbox

# Buscar e deletar mensagens maliciosas (phishing) em massa em todas as caixas
gam all users delete messages query "from:phishing@dominio-malicioso.com" doit
```
