---
name: gam-ops
description: >-
  Operational runbook and command suite for Google Apps Manager (GAM 7) to administer,
  automate, and audit Google Workspace (Google Drive, Docs, Sheets, Gmail, Google Calendar,
  Admin Users, Groups, Licenses, and Security) for example.com.
  Use whenever managing Google Workspace accounts, listing/transferring Drive files,
  managing email settings/signatures, auditing permissions, or running Google API batch automations.
---

# GAM Operations Skill (Google Apps Manager)

Skill operacional especializada para gestão, auditoria e automação do ecossistema **Google Workspace** via **GAM 7.48.12** no domínio `example.com`.

---

## 1. Contexto e Ambiente de Execução

- **Binário GAM**: `C:\GAM7\gam.exe` (invocável diretamente via `gam` no terminal)
- **Configuração & Chaves**: `C:\Users\AXION\.gam/`
  - `gam.cfg` (configuração do cliente)
  - `oauth2.txt` (token OAuth2 do Super Admin `Operator@example.com`)
  - `oauth2service.json` (credenciais da Service Account `gam-project-w1te0@gam-project-w1te0.iam.gserviceaccount.com`)
  - `client_secrets.json` (credenciais do app GCP `gam-project-w1te0`)
- **Delegação de Domínio (DwD)**: 42 escopos autorizados para manipulação de Drive, Gmail, Docs, Calendar, Admin Directory, Meet, Chat, etc.

---

## 2. Estrutura de Referências e Manuais

Para instruções aprofundadas e sintaxe completa de cada módulo, consulte os arquivos de referência:

| Módulo | Arquivo de Referência | Descrição |
| :--- | :--- | :--- |
| **Usuários & Grupos** | [users-and-groups.md](./references/01-users-and-groups.md) | Criação, suspensão, redefinição de senhas, 2FA, aliases, OUs e grupos |
| **Drive, Docs & Sheets** | [drive-docs-sheets.md](./references/02-drive-docs-sheets.md) | Listagem, busca, upload/download, transferências, ACLs e Shared Drives |
| **Gmail & Mensageria** | [gmail-and-messaging.md](./references/03-gmail-and-messaging.md) | Filtros, assinaturas, encaminhamentos, labels, delegação de caixa e busca |
| **Calendar & Meet** | [calendar-and-meet.md](./references/04-calendar-and-meet.md) | Gestão de eventos, calendários de recursos, permissões de agenda e Meet |
| **Segurança & Auditoria** | [security-and-audit.md](./references/05-security-and-audit.md) | Auditoria de tokens terceiros, logs de atividades, cotas e relatórios |
| **Cheatsheet de Sintaxe** | [gam-syntax-cheatsheet.md](./references/06-gam-syntax-cheatsheet.md) | Tabela rápida de sintaxe, flags de batch, CSV piping e queries |

---

## 3. Fluxos de Trabalho Mais Frequentes (Runbooks Rápidos)

### 3.1 Consultar e Auditar o Domínio
```powershell
# Informações gerais da assinatura e domínio
gam info domain

# Listar todos os usuários com dados detalhados
gam print users allfields

# Listar todos os Shared Drives (Drives Compartilhados)
gam print teamdrives
```

### 3.2 Gestão de Usuários
```powershell
# Detalhes de uma conta específica
gam info user <email>

# Criar um novo usuário
gam create user <novo_email> firstname "Nome" lastname "Sobrenome" password "SenhaForte123!"

# Adicionar alias de e-mail (ex: suporte@, contato@)
gam create alias <alias_email> user <email_destino>

# Suspender ou reativar usuário
gam update user <email> suspended on
gam update user <email> suspended off
```

### 3.3 Google Drive & Transferência de Arquivos
```powershell
# Resumo de arquivos do usuário por tipo
gam user <email> show filecount

# Listar arquivos com ID, nome, tipo e data de modificação
gam user <email> print filelist query "'me' in owners" id title mimetype modifiedDate

# Baixar um arquivo específico pelo ID
gam user <email> get drivefile id <FILE_ID> targetfolder "C:\workspace\downloads"

# Transferir a propriedade de todo o Drive de um usuário para outro
gam create datatransfer <email_antigo> gdrive <email_novo>
```

### 3.4 Gmail & Configurações de Mensageria
```powershell
# Definir assinatura de e-mail HTML padronizada
gam user <email> signature html "<b>Nome</b><br>AXION Enterprise"

# Criar encaminhamento automático
gam user <email> forward <destino@email.com>

# Listar filtros de e-mail do usuário
gam user <email> print filters
```

---

## 4. Utilitários e Scripts de Automação

A skill inclui scripts utilitários prontos para automação em Python:
- **`scripts/export_gam_inventory.py`**: Gera relatórios JSON e Markdown consolidados do inventário corporativo.
- **`scripts/audit_external_shares.py`**: Identifica todos os arquivos do Drive compartilhados publicamente ou externamente.

Execute os scripts a partir de `C:\workspace`:
```powershell
python scripts/export_gam_inventory.py
```
