# Referência Operacional: Segurança, Auditoria e Conformidade

Guia de comandos GAM para auditoria de acessos, tokens de terceiros, 2FA e relatórios de conformidade.

---

## 1. Auditoria de Tokens OAuth e Aplicativos Conectados

Auditar quais aplicativos externos possuem acesso aos dados corporativos dos usuários:

```powershell
# Listar todos os tokens de aplicativos autorizados por um usuário
gam user <email> print tokens

# Listar tokens autorizados em todo o domínio
gam all users print tokens

# Revogar acesso de um aplicativo específico para um usuário
gam user <email> delete token clientid <CLIENT_ID>
```

---

## 2. Auditoria de Autenticação em 2 Etapas (2FA / 2SV)

```powershell
# Listar status de 2FA de todos os usuários
gam print users isEnforcedIn2Sv isEnrolledIn2Sv

# Gerar códigos de backup de emergência para um usuário bloqueado
gam user <email> print backupcodes
```

---

## 3. Auditoria de Compartilhamento Externo no Drive

Identificar vazamentos ou arquivos com link aberto para a internet:

```powershell
# Buscar arquivos compartilhados com qualquer pessoa na web
gam user <email> print filelist query "visibility = 'anyoneWithLink' or visibility = 'anyoneCanFind'" id title

# Listar todas as permissões concedidas a domínios externos (não @axionenterprise.cloud)
gam user <email> print fileperms id <FILE_ID>
```

---

## 4. Relatórios de Uso e Auditoria de Login

```powershell
# Relatório de logins dos últimos 7 dias
gam report login

# Relatório de atividades de administração (alterações de permissões e senhas)
gam report admin

# Relatório de cota de armazenamento e espaço utilizado no Drive
gam report usage parameters accounts:drive_used_quota_in_mb
```
