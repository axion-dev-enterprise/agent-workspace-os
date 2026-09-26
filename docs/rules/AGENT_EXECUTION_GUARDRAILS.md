# AGENT_EXECUTION_GUARDRAILS.md — Diretrizes de Execução Resiliente para Agentes de IA

> **Status**: Canônico / Mandatório  
> **Referência**: Leitura complementar mandatória da **Regra #19** de [AGENTS.md](../../AGENTS.md).  
> **Objetivo**: Garantir que modelos de linguagem (LLMs) e agentes autônomos operem no host Windows/PowerShell com taxa de erro próxima de zero, prevenindo travamentos, corrupção de arquivos, falhas de sintaxe e retries cegos.

---

## 1. Princípios Fundamentais de Shell & Host (Windows / PowerShell)

### 1.1 Formatação Canônica de Caminhos (Paths)
- **Use SEMPRE barras normais (`/`)**: Em código, JSON, strings e comandos de ferramentas, formate caminhos como `C:/workspace/scripts/bot_engine` em vez de `C:\workspace\...`.
  - *Motivo*: No Python e em parsers JSON, a contrabarra `\` funciona como caractere de escape (`\t` vira tab, `\n` vira newline, `\b` vira backspace), corrompendo caminhos.
- **Paths Canônicos com Espaços**: Se um caminho contiver espaços, envolva-o em aspas duplas explícitas.

### 1.2 Compatibilidade de Sintaxe no PowerShell 5.1
- **Proibição de Operadores Bash Cruos**: O PowerShell 5.1 não suporta nativamente o encadeamento com `&&` e `||` (gerando `ParserError: InvalidEndOfLine`).
  - No shell cru, utilize `; if ($?) { ... }` para `&&` e `; if (-not $?) { ... }` para `||`.
  - O motor do `tool_executor` traduz automaticamente esses operadores, mas scripts manuais devem respeitar a semântica nativa.
- **Declaração de Variáveis de Ambiente**:
  - Proibido usar `export VAR=val`. Use `$env:VAR = "val"`.
  - Proibido usar `source <file>`. Use `. <file>`.
- **Desativação de Aliases Conflitantes**:
  - `curl` e `wget` no PowerShell mapeiam para `Invoke-WebRequest`. Ao chamar via shell, invoque explicitamente `curl.exe` para suportar flags Unix (`-s`, `-I`, `-o`, `-w`).
  - `ls -la`, `rm -rf` falham com o alias do PowerShell. Utilize as ferramentas dedicadas do ecossistema (`read_file`, `write_file`, `list_directory`).

---

## 2. Política Anti-Travamento & Execução Não-Interativa (Headless First)

### 2.1 Flags Não-Interativas Mandatórias
É terminantemente PROIBIDO executar comandos que abram prompts interativos aguardando confirmação no terminal (`[Y/n]`, senhas ou pagers).
Todo comando deve ser parametrizado com flags headless:
- **Git**: `git commit -m "mensagem"` (NUNCA rodar `git commit` sem `-m`, pois abre editor bloqueante).
- **NPM / NPX**: `npm init -y`, `npm install --yes`, `npx --yes`.
- **Pip / Python**: `pip install --no-input ...`, `python -u ...`.
- **Gerenciadores de Pacote**: `winget install ... --accept-source-agreements --accept-package-agreements`.
- **Vercel / Cloud CLI**: `vercel --yes --prod`, `wrangler ... --non-interactive`.

### 2.2 Variáveis de Ambiente Injetadas Automaticamente
Todo subprocesso deve ser executado com as seguintes variáveis anti-hang injetadas:
```text
CI=1
CONTINUOUS_INTEGRATION=1
GIT_TERMINAL_PROMPT=0
PIP_NO_INPUT=1
npm_config_yes=true
PYTHONUNBUFFERED=1
MPLBACKEND=Agg
```

### 2.3 Encerramento Limpo de Árvore de Processos (Anti-Zombie)
Em caso de estouro de timeout em qualquer comando:
- O agente não deve apenas aguardar a thread Python.
- Deve-se forçar a terminação de toda a árvore de processos filhos via `taskkill /F /T /PID <pid>` para evitar que servidores órfãos continuem prendendo portas (ex: `8080`, `3000`).

---

## 3. Preferência por Ferramentas Dedicadas (*Compound Tools*) vs. Shell Cru

A manipulação de arquivos via comandos de terminal (`echo "..." > file`, `cat << 'EOF'`, `Set-Content`) apresenta alta taxa de falha devido ao escape de aspas e caracteres especiais (`$`, `&`, `|`, `<`, `>`).

### 3.1 Regras de Seleção de Ferramentas
1. **Criar ou Sobrescrever Arquivos**: Utilize SEMPRE a ferramenta `write_file` em vez de redirecionamento de shell.
2. **Edição Cirúrgica de Código**: Utilize a ferramenta `replace_in_file` (ou `patch_file`) informando o trecho exato a ser substituído. Nunca reescreva um arquivo inteiro quando for necessário alterar poucas linhas.
3. **Leitura de Código**: Utilize `read_file` com limitação de linhas para economizar tokens de contexto.
4. **Busca no Código-Fonte**: Utilize `search_in_files` em vez de invocar `findstr` ou `grep` via terminal.
5. **Deploy e Hospedagem**: Utilize `vercel_deploy` com payload estruturado em vez de encadear múltiplos comandos de CLI no terminal.

---

## 4. Protocolo de Diagnóstico e Auto-Correção (*Reflexion*)

### 4.1 Proibição de Retentativas Cegas
Se um comando ou ferramenta retornar erro (`returncode != 0` ou `success: false`):
- É expressamente PROIBIDO reexecutar o mesmo comando idêntico sem antes diagnosticar o erro.
- Analise o bloco `[DIAGNÓSTICO AUTOMÁTICO]` injetado pelo `tool_executor`:
  - **`CommandNotFound`**: O executável não está instalado ou fora do PATH. Verifique com `Get-Command` ou utilize alternativas Python/Node.
  - **`AccessDenied / SharingViolation`**: O arquivo ou porta está bloqueado por outro processo. Verifique se há uma instância anterior rodando e encerre-a.
  - **`TimeoutExpired`**: O comando excedeu o tempo limite. Provavelmente ficou preso em prompt interativo ou download lento. Ajuste as flags ou divida a operação.

---

## 5. Tolerância a Variações de Sintaxe (Fuzzy Matching)

Para tolerar pequenas variações na geração do modelo de linguagem:
- O ecossistema suporta sinônimos de ferramentas:
  - `run_command`, `cmd`, `powershell`, `bash`, `terminal` ➔ `exec_command`
  - `cat`, `view_file`, `read` ➔ `read_file`
  - `create_file`, `save_file`, `write` ➔ `write_file`
  - `ls`, `dir` ➔ `list_directory`
- E sinônimos de argumentos:
  - `command`, `script` ➔ `cmd`
  - `path`, `filename` ➔ `file_path`
  - `text`, `body`, `data` ➔ `content`
