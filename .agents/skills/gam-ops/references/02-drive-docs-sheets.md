# Referência Operacional: Google Drive, Docs, Sheets & Shared Drives

Guia completo para gerenciamento de arquivos, pastas, permissões e drives compartilhados.

---

## 1. Listagem e Busca de Arquivos

### 1.1 Consultar Ativos de Usuários
```powershell
# Contagem de arquivos por mimetype
gam user <email> show filecount

# Listar arquivos próprios com ID, título, mimetype e data de modificação
gam user <email> print filelist query "'me' in owners" id title mimetype modifiedDate

# Listar arquivos em uma pasta específica
gam user <email> print filelist query "'<FOLDER_ID>' in parents" id title mimetype
```

### 1.2 Buscar Arquivos por Nome ou Tipo
```powershell
# Buscar documento por termo no título
gam user <email> print filelist query "name contains 'Relatório' and trashed = false" id title

# Buscar apenas planilhas Google Sheets
gam user <email> print filelist query "mimeType = 'application/vnd.google-apps.spreadsheet'" id title
```

---

## 2. Upload, Download e Manipulação de Arquivos

```powershell
# Baixar arquivo pelo ID para uma pasta local
gam user <email> get drivefile id <FILE_ID> targetfolder "C:\workspace\downloads"

# Fazer upload de um arquivo local para o Drive do usuário
gam user <email> add drivefile localfile "C:\workspace\docs\relatorio.pdf" parentid root

# Fazer upload convertendo automaticamente para Google Docs / Sheets
gam user <email> add drivefile localfile "C:\workspace\dados.csv" convert parentid root

# Criar nova pasta no Drive
gam user <email> create drivefile mimetype gfolder drivefilename "Backups_2026" parentid root
```

---

## 3. Gestão de Permissões (ACLs) e Compartilhamento

```powershell
# Exibir permissões de um arquivo
gam user <email> print fileperms id <FILE_ID>

# Conceder acesso de leitor (viewer) a outro usuário
gam user <email> add drivefileacl id <FILE_ID> role reader user colleague@example.com

# Conceder acesso de editor (writer)
gam user <email> add drivefileacl id <FILE_ID> role editor user dev@example.com

# Remover permissão de um usuário
gam user <email> delete drivefileacl id <FILE_ID> <PERMISSION_ID_OU_EMAIL>

# Auditar todos os arquivos compartilhados publicamente ou com 'anyone'
gam user <email> print filelist query "visibility = 'anyoneWithLink' or visibility = 'anyoneCanFind'" id title
```

---

## 4. Shared Drives (Drives Compartilhados / Team Drives)

```powershell
# Listar todos os Shared Drives da organização
gam print teamdrives

# Criar novo Shared Drive
gam create teamdrive "Projetos_Engenharia"

# Adicionar membro com papel de Administrador (organizer)
gam add drivefileacl id <TEAMDRIVE_ID> role organizer user admin@example.com

# Adicionar membro com papel de Colaborador (fileOrganizer)
gam add drivefileacl id <TEAMDRIVE_ID> role fileOrganizer user dev@example.com

# Listar arquivos de um Shared Drive
gam user <email> print filelist teamdriveid <TEAMDRIVE_ID> id title mimetype
```

---

## 5. Transferência de Propriedade (Data Transfer)

```powershell
# Transferir todos os arquivos do Drive de um usuário para outro
gam create datatransfer <email_antigo> gdrive <email_novo>

# Transferir propriedade de um único arquivo
gam user <email_dono> update drivefileacl id <FILE_ID> role owner user <newowner@example.com>
```
