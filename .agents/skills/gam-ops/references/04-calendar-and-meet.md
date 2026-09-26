# Referência Operacional: Google Calendar & Google Meet

Guia de comandos GAM para gestão de calendários corporativos, eventos e gravações do Google Meet.

---

## 1. Gestão de Calendários de Usuários

```powershell
# Listar calendários do usuário
gam user <email> print calendars

# Compartilhar calendário com outro usuário (leitor / freebusy / editor)
gam user <email> add calendaracl primary role reader user dev@example.com

# Exibir permissões do calendário principal
gam user <email> print calendaracls primary
```

---

## 2. Eventos e Reuniões

```powershell
# Listar eventos futuros do usuário
gam user <email> print events

# Limpar / deletar eventos cancelados
gam user <email> delete events query "summary:'Reunião Cancelada'" doit

# Transferir eventos de calendário de um usuário para outro
gam user <email_origem> transfer calendar primary user <email_destino>
```

---

## 3. Google Meet e Gravações

Os arquivos de gravação e notas do Google Meet são salvos automaticamente na pasta `Meet Recordings` do Google Drive do organizador.

```powershell
# Localizar pasta de gravações do Meet do usuário
gam user <email> print filelist query "name = 'Meet Recordings' and mimeType = 'application/vnd.google-apps.folder'" id title

# Listar todas as gravações de reuniões (.mp4)
gam user <email> print filelist query "mimeType = 'video/mp4' and trashed = false" id title modifiedDate

# Listar todas as notas e atas automáticas geradas pelo Gemini nas reuniões
gam user <email> print filelist query "name contains 'Anotações do Gemini' and mimeType = 'application/vnd.google-apps.document'" id title modifiedDate
```
