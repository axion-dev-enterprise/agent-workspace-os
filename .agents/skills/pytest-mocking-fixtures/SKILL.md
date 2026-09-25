---
name: pytest-mocking-fixtures
description: >-
  Operational skill for Python automated testing using pytest, parameterized fixtures, monkeypatching, database mocking, and pytest-cov coverage.
---

# Pytest Unit & Integration Testing Skill

Skill operacional para suítes de testes robustas, rápidas e determinísticas em Python.

## 1. Padrões
- **Fixtures com Escopo**: Use `scope="session"` para recursos caros (como subida de container de teste) e `scope="function"` para estados isolados.
- **Mocking Externo**: Chamadas de rede HTTP externas devem ser sempre mockadas (com `respx` para httpx ou `responses` para requests) para evitar testes intermitentes.
