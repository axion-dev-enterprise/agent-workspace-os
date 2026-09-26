---
name: token-reduction-context-compression
description: >-
  Operational skill for aggressive LLM token reduction, AST code skeletonizing, JSON payload crushing, terminal log pruners, and Ponytail YAGNI minimal code engineering across agent sessions.
---

# Token Reduction & Context Compression Skill

Skill operacional canônica para otimização de custos e preservação de janela de contexto em agentes de IA. Implementa técnicas baseadas nas melhores práticas da comunidade open source (**Headroom**, **Ponytail**, **SkillReducer** e **Concise Mode**).

---

## 1. Os Quatro Pilares de Otimização de Tokens

```
                   ┌────────────────────────────────────────┐
                   │    ENGENHARIA DE REDUÇÃO DE TOKENS     │
                   └──────────────────┬─────────────────────┘
                                      │
       ┌──────────────┬───────────────┴──────────────┬──────────────┐
       ▼              ▼                              ▼              ▼
┌──────────────┐┌──────────────┐              ┌──────────────┐┌──────────────┐
│  Filtragem   ││ Compressão   │              │  Escada      ││ Modo Conciso │
│  de Terminal ││ Estrutural   │              │  Ponytail    ││ de Saída     │
│ (Logs / CLI) ││ (AST & JSON) │              │  (Anti-Bloat)││ (Zero Fluff) │
└──────────────┘└──────────────┘              └──────────────┘└──────────────┘
```

1. **Filtragem de Terminal (CLI Noise)**: Não enviar logs brutos de 2.000 linhas de `npm test`, `git` ou compilação.
2. **Compressão Estrutural (AST & JSON)**: Reduzir payloads JSON e arquivos de código às suas interfaces e assinaturas fundamentais.
3. **Escada de Decisão Ponytail (YAGNI)**: Nunca escrever código novo se a biblioteca padrão ou o projeto já possuírem a solução.
4. **Modo Conciso de Saída (Output Economics)**: Eliminar saudações, preâmbulos e explicações redundantes; focar 100% no resultado técnico, pois tokens de saída são os mais caros.

---

## 2. A Escada de Decisão Ponytail (The Best Code is No Code)

Antes de propor, gerar ou implementar qualquer novo arquivo ou função, o agente **DEVE** percorrer obrigatoriamente a escada YAGNI:

1. **A tarefa realmente precisa ser codificada?** (Eliminar premissas especulativas).
2. **O repositório já possui uma função ou utilitário equivalente?** (Reutilizar código existente).
3. **A biblioteca padrão da linguagem (`stdlib`) resolve de forma nativa?** (Ex: `json`, `pathlib`, `re` em Python; `fetch`, `URL`, `crypto` no Node/Browser).
4. **Um recurso nativo do sistema/HTML/CSS resolve?** (Ex: `<dialog>` em vez de biblioteca de modal externa; `clamp()` em vez de listeners de redimensionamento JS).
5. **Uma dependência já presente no `package.json` ou `requirements.txt` resolve?** (Evitar instalar novos pacotes).
6. **Somente após esgotar os passos acima:** Escrever a menor quantidade possível de código novo e determinístico.

---

## 3. Modo Conciso de Saída (Zero Fluff Directive)

Tokens gerados pelo LLM custam muito mais que tokens lidos. Ao interagir:
- **Proibido**: Preâmbulos conversacionais ("*Com certeza! Ficarei feliz em ajudar com isso...*").
- **Proibido**: Explicações didáticas não solicitadas sobre conceitos elementares de programação.
- **Obrigatório**: Resposta orientada a ação e fatos (Arquivos alterados, testes executados, métricas reais).
- **Preservação Total**: Manter 100% da integridade técnica (blocos de código, caminhos de arquivo clicáveis, comandos exatos e hashes criptográficos).

---

## 4. Utilitários Python Canônicos (Zero Dependências / Stdlib)

Disponíveis diretamente no diretório `scripts/` desta skill:

### 4.1 Compactador de JSON / Payloads (`smart_crusher.py`)
Remove nulos, campos vazios e resume arrays repetitivos com metadados de contagem:
```bash
python .agents/skills/token-reduction-context-compression/scripts/smart_crusher.py data.json
# Ou via pipe:
cat large_response.json | python .agents/skills/token-reduction-context-compression/scripts/smart_crusher.py
```
*Economia média: 60% a 95% de tokens.*

### 4.2 Esqueleto de Código AST (`code_compressor.py`)
Extrai docstrings, imports, classes e assinaturas de funções substituindo os corpos por `...`:
```bash
python .agents/skills/token-reduction-context-compression/scripts/code_compressor.py src/heavy_service.py
```
*Economia média: 70% a 90% de tokens.*

### 4.3 Redutor de Ruído de Logs (`log_compressor.py`)
Filtra outputs de testes e builds, retendo erros, falhas, stack traces e linhas de sumário:
```bash
pytest | python .agents/skills/token-reduction-context-compression/scripts/log_compressor.py
```
*Economia média: 80% a 95% de tokens.*

### 4.4 Agrupador de Busca Ripgrep / Grep (`search_compressor.py`)
Agrupa resultados por arquivo e limita matches por módulo, evitando encher o contexto:
```bash
grep -rn "pattern" . | python .agents/skills/token-reduction-context-compression/scripts/search_compressor.py
```

---

## 5. Boas Práticas Operacionais na Manipulação de Arquivos

1. **Leitura Cirúrgica com Fatiamento (`StartLine` / `EndLine`)**:
   - Nunca ler 1.000 linhas de um arquivo quando você só precisa inspecionar o bloco entre as linhas 120 e 150.
2. **Edição Pontual em vez de Regravação Integral**:
   - Sempre preferir `replace_file_content` para blocos específicos do que `write_to_file` com o arquivo inteiro reescrito.
3. **Limpeza de Sessão**:
   - Evitar manter conversas infladas com dezenas de turnos de depuração encerrada. Iniciar novas tarefas com contexto renovado.
4. **Progressive Disclosure de Skills**:
   - Manter as descrições no frontmatter do `SKILL.md` ultraleves (menos de 30 palavras) para não inflar o *standing context* de inicialização do agente.
