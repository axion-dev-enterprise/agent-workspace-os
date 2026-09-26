# Padrões de Design para Construção de Skills Operacionais

> **Guia de Engenharia para Agentes Autônomos — AXION Enterprise**  

Este guia detalha como projetar skills que maximizam a precisão do agente, reduzem alucinações e economizam tokens.

---

## 1. Padrão Progressive Disclosure (Revelação Progressiva)

Agentes não devem carregar o conteúdo de 50 skills simultaneamente na memória.
- **Camada 1 (Metadata)**: O agente lê apenas o `name` e a `description` do YAML frontmatter no início da execução (~15 tokens por skill).
- **Camada 2 (Ativação por Demanda)**: Quando o objetivo do usuário necessita daquele domínio, o agente lê o `SKILL.md` completo.
- **Camada 3 (Ferramental Executável)**: O agente executa scripts em `scripts/` e lê referências detalhadas em `references/` sob demanda.

### Como Escrever a `description` no Frontmatter:
- **RUIM**: `"Skill de Docker"` (vago, sem palavras-chave de ação).
- **BOM**: `"Operational skill for Docker container builds, Dockerfile multi-stage optimization, docker-compose production deployments, and volume management."` (específico, acionável, com termos técnicos claros).

---

## 2. Padrão Deterministic Tooling (Substituição de Código Volátil por Scripts Canônicos)

Em vez de permitir que o LLM "invente" um script Python ad-hoc para cada tarefa com risco de erro de sintaxe, o repositório deve fornecer utilitários prontos na pasta `scripts/` da skill.

### Vantagens:
1. **Zero Hallucination**: O script foi testado previamente, funciona em Windows/Linux e possui tratamento robusto de erros.
2. **Economia Massiva de Tokens**: O agente executa `python script.py --param valor` (5 tokens) em vez de escrever 100 linhas de Python (600 tokens).
3. **Auditabilidade**: Logs padronizados e saídas consistentes em JSON.

---

## 3. Padrão Evidence Receipt (Comprovação Empírica)

O agente só pode afirmar que uma tarefa foi concluída com sucesso se apresentar a evidência real obtida da execução da ferramenta ou teste.

### Estrutura do Recibo de Verificação:
- Comando exato executado.
- Código de retorno (`exit code == 0`).
- Trecho da saída comprovando a asserção (ex: `"12 passed in 1.45s"`).
