"""
AXION AI Intelligence Pipeline
================================
Pipeline autônomo para:
1. Descoberta e Scoring de Perfis Técnicos (OpenRouter + Heurísticas)
2. Análise, Interpretação e Validação de Informações
3. Fábrica Autônoma de Skills & MCPs
4. Executor de Testes Empíricos e Geração de Resultados Úteis
"""

from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = MODULE_DIR.parent.parent
