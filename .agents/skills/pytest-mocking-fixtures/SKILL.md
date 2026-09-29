---
name: pytest-mocking-fixtures
description: >-
  Operational skill for Python automated testing using pytest, parameterized fixtures,
  monkeypatching, database mocking, and pytest-cov coverage.
---

# Pytest Architecture, Fixtures & Mocking — Master Skill

Skill operacional canonica para garantia de qualidade, testes unitarios e integracao deterministica em Python com **Pytest**, **pytest-asyncio** e **pytest-cov**.

---

## 1. O Ciclo de Vida de Fixtures e Teardown Garantido

> **"ZERO POLUIÇÃO DE ESTADO ENTRE TESTES."**

Toda fixture que alocar recursos (arquivos temporários, conexões de banco de dados, variáveis de ambiente) DEVE utilizar a sintaxe `yield` para garantir o *teardown* mesmo em caso de falha no meio do teste.

### 1.1 Hierarquia de Escopos de Fixture
- **`scope="function"` (Padrão)**: Recriada para cada teste individual. Essencial para transações de banco com rollback, instâncias de clientes HTTP e dados mutáveis.
- **`scope="module"`**: Compartilhada entre todos os testes de um mesmo arquivo `.py`. Ideal para schemas carregados em memória ou fixtures de leitura estática.
- **`scope="session"`**: Executada uma única vez por execução de suíte. Restrita a recursos pesados (ex: inicialização de container Docker de banco via Testcontainers).

### 1.2 Padrão Canônico: Transação com Rollback Automático
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost:5432/test_db")
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    # Teardown garantido: Rollback incondicional para manter o banco limpo
    await session.close()
    await transaction.rollback()
    await connection.close()
```

---

## 2. Testes Parametrizados: Cobertura Massiva de Casos de Borda

Evite duplicar código de teste. Utilize `@pytest.mark.parametrize` para testar matrizes de entrada com inputs válidos, inválidos e extremos:

```python
import pytest
from my_app.services.validator import validate_tax_id

@pytest.mark.parametrize("tax_id,expected_valid,error_type", [
    ("12345678909", True, None),
    ("00000000000", False, "INVALID_DIGIT"),
    ("123", False, "TOO_SHORT"),
    ("", False, "EMPTY"),
    ("1234567890A", False, "NON_NUMERIC"),
])
def test_tax_id_validation_matrix(tax_id: str, expected_valid: bool, error_type: str):
    is_valid, err = validate_tax_id(tax_id)
    assert is_valid == expected_valid
    if not expected_valid:
        assert err == error_type
```

---

## 3. Testes Assíncronos com `pytest-asyncio`

Configuração padrão em `pytest.ini` ou `pyproject.toml`:
```ini
[pytest]
asyncio_mode = auto
```

Em código:
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_async_service_fetch():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/healthz")
        assert response.status_code == 200
```

---

## 4. Mocking e Monkeypatching Resiliente

### 4.1 Mock de Chamadas HTTP Externas com `pytest-httpx` / `respx`
Nunca permita que testes unitários ou de integração façam requisições reais para a internet (Stripe, APIs externas):

```python
import pytest
import respx
import httpx

@respx.mock
async def test_payment_gateway_timeout_retry():
    # Simula 500 na primeira tentativa e 200 na segunda
    route = respx.post("https://api.gateway.com/charges")
    route.side_effect = [
        httpx.Response(500, json={"error": "Internal Server Error"}),
        httpx.Response(200, json={"id": "ch_12345", "status": "paid"}),
    ]

    result = await make_charge_with_retry(amount_cents=5000)
    assert result["status"] == "paid"
    assert route.call_count == 2
```

---

## 5. O Utilitário CLI Standalone (`scripts/pytest_suite_runner.py`)

A skill acompanha ferramenta CLI em Python stdlib com gate de cobertura:

```bash
# Executar suite completa com exibicao resumida e short tracebacks
python .agents/skills/pytest-mocking-fixtures/scripts/pytest_suite_runner.py --dir packages/my-package

# Executar suite exigindo 85% de cobertura de codigo no pacote
python .agents/skills/pytest-mocking-fixtures/scripts/pytest_suite_runner.py --dir packages/my-package --cov my_package --min-cov 85

# Execucao ultra-rapida paralela com pytest-xdist
python .agents/skills/pytest-mocking-fixtures/scripts/pytest_suite_runner.py --dir . --fast
```

---

## 6. Portão de Verificação (Verification Gate)

1. **Zero Test Pollution**: O banco de dados deve permanecer no mesmo estado antes e depois da execução dos testes.
2. **Cobertura Mínima de Código**: A suíte deve atingir pelo menos **80% de cobertura** no pacote auditado via `pytest-cov`.
3. **Sem Flakiness**: Execuções repetidas (3x) da mesma suíte não devem apresentar intermitência.
