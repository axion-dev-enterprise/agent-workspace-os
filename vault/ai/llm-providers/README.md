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
- Agentes autônomos e workers
