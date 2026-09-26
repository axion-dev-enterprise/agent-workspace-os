# Exemplos de Runbooks e Workflows Prontos (GAM)

Casos práticos de uso e scripts sequenciais para operações comuns.

---

## 1. Onboarding de Novo Colaborador

Procedimento sequencial completo para criação e configuração de conta:

```powershell
# 1. Criar o usuário na OU correta
gam create user joao.silva@example.com firstname "João" lastname "Silva" password "AxionStart#2026" changepassword on org "/Engenharia"

# 2. Adicionar aos grupos corporativos essenciais
gam update group dev@example.com add member user joao.silva@example.com

# 3. Dar acesso ao Shared Drive da AXION
gam add drivefileacl id 0AARPf88V8uuyUk9PVA role fileOrganizer user joao.silva@example.com

# 4. Definir assinatura institucional padronizada
gam user joao.silva@example.com signature html "<b>João Silva</b><br>Engenharia de Software | AXION Enterprise<br>https://example.com"
```

---

## 2. Offboarding Seguro de Colaborador (Desligamento)

Procedimento de encerramento seguro mantendo integridade e histórico:

```powershell
# 1. Suspender a conta imediatamente (impede logins e sincronizações)
gam update user ex.colaborador@example.com suspended on

# 2. Resetar tokens de login e sessões ativas
gam user ex.colaborador@example.com signout

# 3. Transferir todos os arquivos do Google Drive para o Super Admin
gam create datatransfer ex.colaborador@example.com gdrive iago@example.com

# 4. Configurar encaminhamento de e-mails para não perder comunicações importantes
gam user ex.colaborador@example.com forward on to iago@example.com keep

# 5. Definir resposta automática avisando sobre o novo canal de contato
gam user ex.colaborador@example.com vacation on subject "Canal Atualizado" message "Este endereço não está mais ativo. Por favor, envie sua mensagem para contato@example.com."
```

---

## 3. Backup Local de Arquivos do Drive

Download programático de relatórios e documentos importantes do Drive para a máquina local:

```powershell
# Baixar documento específico pelo ID
gam user iago@example.com get drivefile id 1RJUYJ09EJYjFVxL4zdLr_jasMjPTuJss targetfolder "C:\workspace\docs\backups"
```
