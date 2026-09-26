# Cheatsheet de Sintaxe e Operações em Lote GAM

Referência rápida da gramática de comandos, modificadores de lote, redirecionamento e variáveis do GAM.

---

## 1. Modificadores de Destino (Entidades)

| Modificador | Descrição | Exemplo |
| :--- | :--- | :--- |
| `user <email>` | Executa a ação para um único usuário | `gam user iago@example.com ...` |
| `users <lista>` | Executa para uma lista separada por vírgula | `gam users user1@...,user2@... ...` |
| `all users` | Itera por todos os usuários do domínio | `gam all users print signature` |
| `group <email>` | Executa para os membros de um grupo | `gam group dev@... print ...` |
| `ou <path>` | Executa para todos os membros da Unidade Organizacional | `gam ou "/Engenharia" print ...` |
| `csv <arquivo>` | Lê parâmetros de um CSV para automação em lote | `gam csv usuarios.csv gam create user ~Email ...` |

---

## 2. Processamento em Lote com CSV (Batch Loop)

A sintaxe `gam csv <arquivo.csv>` permite iterar em linhas de uma planilha usando o caractere `~` antes do nome da coluna:

```powershell
# Criação de usuários em massa a partir de um CSV com colunas: Email,PrimeiroNome,Sobrenome
gam csv novos_membros.csv gam create user ~Email firstname ~PrimeiroNome lastname ~Sobrenome password "TempPass123!" changepassword on

# Aplicar assinaturas em lote a partir de CSV
gam csv assinaturas.csv gam user ~Email signature html ~AssinaturaHtml
```

---

## 3. Redirecionamento e Exportação de Resultados

O GAM suporta salvar o resultado de qualquer comando diretamente em arquivo ou no próprio Google Drive:

```powershell
# Salvar resultado em CSV local
gam print users allfields > C:\workspace\docs\usuarios_export.csv

# Enviar resultado de um relatório diretamente para uma planilha no Google Drive
gam print users todrive
gam report admin todrive
```

---

## 4. Estrutura de Queries do Google Drive

Ao usar `gam user <email> print filelist query "<query>"`, a query segue a sintaxe da Google Drive API v3:

| Operador / Campo | Exemplo | Descrição |
| :--- | :--- | :--- |
| `name contains '<texto>'` | `query "name contains 'Relatório'"` | Busca textual no nome do arquivo |
| `mimeType = '<tipo>'` | `query "mimeType = 'application/pdf'"` | Filtra por tipo MIME exato |
| `'me' in owners` | `query "'me' in owners"` | Apenas arquivos cujo proprietário seja o usuário |
| `'<ID>' in parents` | `query "'18susTkyoqEe...' in parents"` | Arquivos contidos em uma pasta específica |
| `trashed = false` | `query "trashed = false"` | Exclui arquivos na lixeira |
| `visibility = 'anyoneWithLink'` | `query "visibility = 'anyoneWithLink'"` | Arquivos públicos via link |
| Operadores Lógicos | `and`, `or`, `not` | Combinação de múltiplos critérios |
