---
name: antigravity-cli
description: >-
  Operational guide and reference for the Google Antigravity CLI (agy).
  Covers interactive TUI sessions (agy), continuing recent conversations (agy -c),
  headless single-turn execution (agy -p), model inspection (agy models),
  MCP server administration (agy mcp list), and CLI maintenance (agy update).
---

# Google Antigravity CLI (`agy`) — Manual Operacional do Agente

Guia canônico e referência de comandos para operação da interface de linha de comando oficial **Google Antigravity CLI** (`agy`).

---

## 1. Tabela Rápida de Comandos Canônicos

| Comando | Descrição Operacional | Modo de Execução |
| :--- | :--- | :--- |
| `agy` | Inicia a sessão interativa no terminal (TUI) | Interativo (Full TUI) |
| `agy -c` | Continua a conversa/sessão mais recente no workspace | Interativo (Resume) |
| `agy -p "<prompt>"` | Executa um prompt direto e sai imediatamente sem entrar na TUI | Headless / Batch |
| `agy models` | Lista todos os modelos de IA disponíveis na plataforma | Consulta / Metadata |
| `agy mcp list` | Lista e inspeciona os servidores Model Context Protocol (MCP) configurados | Governança de Tools |
| `agy update` | Atualiza a CLI `agy` para a versão mais recente disponível | Manutenção / Upgrade |

---

## 2. Detalhamento e Modos de Uso

### 2.1 Iniciar Sessão Interativa (TUI)
```bash
agy
```
- Abre a interface de usuário de terminal (TUI) rica com chat contínuo, rendering markdown e suporte a atalhos.
- Ideal para sessões de desenvolvimento colaborativo, pair programming e exploração interativa.
- Para sair da sessão: utilize `/exit`, `/quit` ou a combinação `Ctrl+D Ctrl+D`.

### 2.2 Continuar a Conversa Mais Recente
```bash
agy -c
```
- Carrega o contexto histórico, arquivos inspecionados e estado cognitivo da última sessão aberta no workspace.
- Evita perda de contexto após reinicializações de terminal ou trocas de janela.

### 2.3 Executar Prompt Direto (Modo Headless / Automação)
```bash
agy -p "listar arquivos modificados"
```
```powershell
# Exemplo em scripts ou esteiras automatizadas
agy -p "auditar dependencias desatualizadas no package.json e gerar relatorio"
```
- Não abre a TUI interativa.
- Envia a instrução diretamente ao agente, executa os passos necessários e cospe a saída para stdout.
- Ideal para integração com scripts PowerShell/Bash, cron jobs, git hooks e tarefas agendadas.

### 2.4 Listar Modelos Disponíveis
```bash
agy models
```
- Exibe o catálogo completo de modelos fundacionais suportados (Gemini 2.0 Flash, Gemini 1.5 Pro, variantes Ultra/Thinking).
- Permite identificar os identificadores de modelo corretos para flags de override (`--model <id>`).

### 2.5 Listar e Gerenciar Servidores MCP
```bash
agy mcp list
```
- Lista todos os servidores do **Model Context Protocol (MCP)** atualmente registrados e conectados.
- Exibe status da conexão, transporte (stdio / sse) e ferramentas expostas ao agente.
- Comandos auxiliares:
  ```bash
  agy mcp list              # Lista servidores ativos e ferramentas
  agy mcp add <nome> <cmd>  # Registra novo servidor MCP
  agy mcp remove <nome>     # Desconecta servidor MCP
  ```

### 2.6 Atualizar a CLI para a Versão Mais Recente
```bash
agy update
```
- Verifica releases oficiais, baixa a versão mais estável e substitui o binário atual mantendo configurações em `~/.gemini/antigravity-cli/settings.json`.

---

## 3. Diretrizes de Uso para Agentes

1. **Automação**: Quando um agente precisar invocar o Antigravity via terminal ou subprocessos em scripts Python/PowerShell, utilize SEMPRE a flag `-p` (`agy -p "instrução"`) para garantir que o processo termine e retorne a saída em vez de prender a execução na TUI.
2. **Preservação de Contexto**: Para restaurar o fluxo de trabalho anterior, recomende ou utilize `agy -c`.
3. **Auditoria de Recursos**: Use `agy models` e `agy mcp list` antes de delegar tarefas para confirmar as capacidades ativas no ambiente.
