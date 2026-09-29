---
name: fastapi-async-api
description: >-
  Operational engineering skill for high-performance asynchronous REST APIs with FastAPI,
  Pydantic v2, async/await event-loop discipline, dependency injection, and lifespan resource management.
---

# FastAPI Asynchronous API Engineering — Master Skill

Skill operacional canonica para design, desenvolvimento e governanca de microsservicos e APIs REST assincronas de alta performance em **FastAPI** e **Python 3.11+**.

---

## 1. A Regra de Ouro do Event Loop no FastAPI

> **"NUNCA EXECUTE OPERAÇÕES BLOQUEANTES DENTRO DE `async def`."**

- **Chamadas I/O Assíncronas (`async def`)**: Use estritamente clientes assíncronos não-bloqueantes (`httpx.AsyncClient`, `asyncpg`, `motor`, `redis.asyncio`).
- **Operações Síncronas ou CPU-Bound (`def` simples)**: Se precisar rodar cálculo pesado, criptografia de senha (`bcrypt`), processamento de imagem (`Pillow`) ou SDK síncrono legado, declare a rota como `def` normal. O FastAPI automaticamente delegará sua execução para o *threadpool* interno (`anyio.to_thread`), impedindo o congelamento do *event loop*.
- **Antipadrão Crítico**: Chamar `time.sleep()`, `requests.get()` ou consultas síncronas de banco dentro de um `async def` paralisa todas as requisições concorrentes de todos os usuários da API no mesmo processo!

---

## 2. Gerenciamento Canônico de Ciclo de Vida (`lifespan`)

Substitua os eventos depreciados `@app.on_event("startup")` pelo context manager moderno de `lifespan`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncpg

db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Inicializar pools de conexao, clientes Redis e brokers
    global db_pool
    db_pool = await asyncpg.create_pool(
        dsn="postgresql://user:pass@localhost:5432/production_db",
        min_size=5,
        max_size=20,
        command_timeout=10.0,
    )
    yield
    # SHUTDOWN: Fechamento gracioso de conexoes sem perda de transacoes
    if db_pool:
        await db_pool.close()

app = FastAPI(title="AXION Core Service", version="1.0.0", lifespan=lifespan)
```

---

## 3. Pydantic v2: Tipagem Estrita e Performance

Utilize os padrões modernos do Pydantic v2 para máxima validação e serialização em Rust:

```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Annotated

class UserBase(BaseModel):
    # Forbids unknown fields to prevent mass assignment vulnerabilities
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")

class UserCreate(UserBase):
    password: str = Field(min_length=12, max_length=128)

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. Injeção de Dependências & Transações Atômicas

Isole sessões de banco e autenticação através do sistema de `Depends`:

```python
from fastapi import Depends, HTTPException, status
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@app.post("/v1/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_admin: Annotated[UserResponse, Depends(require_admin_role)]
):
    user = await UserService.create_user(session, payload)
    return user
```

---

## 5. Middleware de Tracing e Correlation ID

Toda requisição deve carregar um cabeçalho `X-Correlation-ID` para rastreamento distribuído ponta a ponta:

```python
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = corr_id
        
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
        return response

app.add_middleware(CorrelationIdMiddleware)
```

---

## 6. O Utilitário CLI Standalone (`scripts/fastapi_inspector.py`)

A skill inclui um auditor para verificar bloqueios de event loop e conformidade de rotas:

```bash
# Auditar codebase em busca de chamadas bloqueantes (time.sleep, requests) dentro de async def
python .agents/skills/fastapi-async-api/scripts/fastapi_inspector.py --dir services/my-api

# Saída estruturada em JSON para pipelines de CI
python .agents/skills/fastapi-async-api/scripts/fastapi_inspector.py --dir services/my-api --json
```

---

## 7. Portão de Verificação (Verification Gate)

1. **Zero Chamadas Bloqueantes**: O script `fastapi_inspector.py` deve retornar 0 violações de bloqueio de event loop.
2. **Health Check Funcional**: O endpoint `/healthz` deve responder `HTTP 200 OK` com verificação de conectividade ativa do banco de dados em menos de 50ms.
3. **Testes Assíncronos**: Suíte de testes unitários executada via `pytest -v` utilizando `httpx.AsyncClient` e fixtures parametrizadas assíncronas.
