# PI-Desktop & Local-First Multi-Agent Orchestration Guide

Este documento detalha os conceitos operacionais e contratos de integração para o ambiente **PI-Desktop** (`vastsa/PI-Desktop`) e orquestração de subagentes com persistência de contexto e protocolo MCP.

---

## 1. Visão Geral da Arquitetura do PI-Desktop

O PI-Desktop é uma plataforma desktop *local-first* construída sobre uma arquitetura híbrida:
- **Core de Hospedagem em Rust (`crates/host-core`)**: Gerencia o ciclo de vida dos processos, execução assíncrona, sandboxing e comunicação IPC de baixa latência.
- **Frontend & Interface em Electron + React (`apps/desktop`)**: Interface gráfica modular com painel de sessões, renderização de transcrições com LaTeX (KaTeX), editor de planos e composer de prompts.
- **Camada de Extensibilidade & Plugins (`packages/plugin-devkit`)**: Permite a injeção dinâmica de ferramentas, slots de UI e servidores MCP (*Model Context Protocol*).

---

## 2. Modos Operacionais Canônicos

O ambiente estrutura o trabalho do desenvolvedor em três ritmos complementares:

1. **Modo Agent (Operação de Fluxo Contínuo)**:
   - Utilizado para tarefas rotineiras de engenharia: escrita de código, refatoração cirúrgica, depuração e criação de testes.
   - O agente opera com feedback de terminal e ciclo interativo rápido.

2. **Modo Plan (Revisão Pre-Mortem & Blast Radius)**:
   - Mandatório para alterações arquiteturais e migrações críticas.
   - Bloqueia mutações destrutivas até que o usuário aprove a lista detalhada de arquivos impactados e a estratégia de rollback (alinhado à Regra #9B do AXION).

3. **Modo Goal (Bloqueio de Resultados de Longo Prazo)**:
   - Utilizado para sprints autônomas ou tarefas multi-etapas que demandam persistência de contexto através de múltiplas horas ou reinicializações do sistema.

---

## 3. Protocolo de Ferramentas MCP & Segurança

- **Agnosticismo de Modelos**: Permite alternar instantaneamente entre provedores de nuvem (Anthropic Claude, OpenAI, Google Gemini) e executores locais de código aberto (Ollama, LM Studio, vLLM).
- **Isolamento de Credenciais**: Tokens de API e segredos são armazenados diretamente no keychain nativo do sistema operacional (Windows Credential Manager / macOS Keychain / Linux SecretService), impedindo que chaves sejam salvas em texto puro na raiz do projeto.
- **Executável Portátil para Windows**: O binário `PI-Desktop-Portable-0.15.10.exe` pode ser executado diretamente sem instalação global de dependências de compilação C++/Rust.
