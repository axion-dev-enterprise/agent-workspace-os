# LLM & AI Providers Vault 🧠

## 1. Finalidade
Centralizar as credenciais dos provedores de inteligência artificial que alimentam os agentes e serviços AXION.

## 2. Provedores Suportados
- **OpenRouter**: Roteamento dinâmico para múltiplos modelos (Xiaomi Mimo, Claude, Llama 3, DeepSeek).
- **HuggingFace**: Hub de modelos abertos e datasets.
- **OpenAI / Gemini / Anthropic**: Chaves diretas das APIs proprietárias.

## 3. Serviços que Consomem Este Módulo
- `scripts/brain_server.py`
- `scripts/openai_proxy.py`
- `services/axion-flow` (AXION Flow Platform e tentáculos de agentes via `OPENROUTER_API_KEY_FLOW`)
- Agentes autônomos e workers

## 4. Chaves OpenRouter Segregadas
- `OPENROUTER_API_KEY`: Chave geral/corporativa AXION.
- `OPENROUTER_CLIENTS_API_KEY`: Workloads de clientes isolados (Isabela).
- `OPENROUTER_API_KEY_FLOW`: Chave exclusiva AXION Flow e tentáculos Flow ($50/mês).

## Chave exclusiva de clientes AXION
Modelo Isabela configurado para o pivô: `ISABELA_OPENROUTER_MODEL=xiaomi/mimo-v2.6-pro`.
O modelo foi localizado no catálogo atual com suporte a `response_format`/saída
estruturada. Revalidar disponibilidade e preço antes de trocá-lo.

OPENROUTER_CLIENTS_API_KEY: workloads de clientes, incluindo Isabela. Não sobrescreve OPENROUTER_API_KEY nem deve alimentar serviços internos. Imagens do operador em 7/10 mostram label AXION-CLIENTS e limite US$ 1 diário. A consulta de metadados registrada em apps/isabela-platform/docs/OPENROUTER_CLIENTS.md confirmou HTTP 200 e limite diário; essa evidência se refere ao momento da consulta. Injetar somente backend/worker via vault_loader, sem fallback corporativo. Rotacionar/revogar no painel API Keys OpenRouter e atualizar apenas .env; schema/documentação sem valores. Consumidor: adaptador LLM Isabela, que exige modelo explicitamente configurado.
