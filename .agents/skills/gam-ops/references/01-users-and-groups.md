# Referência Operacional: Usuários, Contas, OUs e Grupos

Guia prático para administração de contas e identidades no Google Workspace com o GAM.

---

## 1. Gestão de Contas de Usuários

### 1.1 Consultar Usuários
```powershell
# Listar todos os usuários (apenas emails)
gam print users

# Listar usuários com todos os campos (nome, status, criação, último login, 2FA)
gam print users allfields

# Exibir detalhes completos de um usuário específico
gam info user <email>
```

### 1.2 Criação e Atualização de Contas
```powershell
# Criar usuário com senha temporária exigindo troca no primeiro login
gam create user newuser@example.com firstname "Nome" lastname "Sobrenome" password "SenhaForte123!" changepassword on

# Atualizar nome de usuário
gam update user <email> firstname "NovoNome" lastname "NovoSobrenome"

# Redefinir senha de um usuário
gam update user <email> password "NovaSenhaSegura456!" changepassword on
```

### 1.3 Suspensão e Desativação (Offboarding)
```powershell
# Suspender conta (bloqueia login imediato sem deletar dados)
gam update user <email> suspended on

# Reativar conta suspensa
gam update user <email> suspended off

# Deletar usuário permanentemente
gam delete user <email>
```

---

## 2. Aliases de E-mail

```powershell
# Criar alias (ex: suporte@ apontando para equipe ou pessoa)
gam create alias support@example.com user admin@example.com

# Listar aliases de um usuário
gam info user <email>

# Remover alias
gam delete alias support@example.com
```

---

## 3. Grupos de Distribuição & Listas

```powershell
# Listar todos os grupos do domínio
gam print groups

# Criar novo grupo
gam create group finance@example.com name "Setor Financeiro" description "Grupo de comunicação financeira"

# Adicionar membro ao grupo
gam update group finance@example.com add member user admin@example.com

# Adicionar gerente ou proprietário ao grupo
gam update group finance@example.com add manager user admin@example.com

# Listar membros de um grupo
gam print group-members group finance@example.com
```

---

## 4. Unidades Organizacionais (OUs)

```powershell
# Listar todas as OUs
gam print orgs

# Criar nova Unidade Organizacional
gam create org "Engenharia" parent "/"

# Mover usuário para uma OU específica
gam update org "Engenharia" add users dev@example.com
```
