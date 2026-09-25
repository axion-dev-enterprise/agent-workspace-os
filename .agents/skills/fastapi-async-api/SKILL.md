---
name: fastapi-async-api
description: >-
  Operational skill for building high-performance asynchronous REST APIs with FastAPI, Pydantic v2, async/await, dependency injection, and JWT authentication.
---

# FastAPI Async API Engineering Skill

Skill operacional para desenvolvimento de APIs REST assíncronas, escaláveis e com tipagem estrita em Python.

## 1. Padrões de Arquitetura Canônica
- **Pydantic v2**: Utilizar `model_config = ConfigDict(from_attributes=True)` e validações de campo com `Field(...)`.
- **Async I/O**: Rotas de banco e rede devem usar `async def` com drivers assíncronos (`asyncpg`, `httpx`, `motor`). Rotas com CPU bound intenso devem usar rotinas normais `def` em threadpool.
- **Dependency Injection**: Reutilizar conexões de banco e autenticação com `Depends(get_db)` e `Depends(get_current_user)`.

## 2. Exemplo Canônico de Endpoint & Schema
```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Annotated

app = FastAPI(title="AXION Microservice API", version="1.0.0")

class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")

class UserResponse(UserCreate):
    id: str

@app.post("/v1/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    # Processamento determinístico assíncrono
    return UserResponse(id="usr_12345", **payload.model_dump())
```
