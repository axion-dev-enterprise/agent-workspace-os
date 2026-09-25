#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canonical Skill Generator & Installer — AXION Enterprise
Installs 30 high-utility, production-grade skills into:
1. Workspace: C:\\workspace\\.agents\\skills\\
2. Global: C:\\Users\\AXION\\.gemini\\antigravity\\skills\\
"""

import os
from pathlib import Path

WORKSPACE_SKILLS = Path(r"C:\workspace\.agents\skills")
GLOBAL_SKILLS = Path(os.path.expanduser(r"~\.gemini\antigravity\skills"))

NEW_SKILLS = {
    # --- 1. Backend & APIs ---
    "fastapi-async-api": {
        "domain": "Backend & APIs",
        "scope": "APIs assíncronas em Python com Pydantic v2, dependency injection, background tasks e OpenAPI",
        "description": "Operational skill for building high-performance asynchronous REST APIs with FastAPI, Pydantic v2, async/await, dependency injection, and JWT authentication.",
        "content": """# FastAPI Async API Engineering Skill

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
"""
    },

    "nestjs-modular-backend": {
        "domain": "Backend & APIs",
        "scope": "Arquitetura modular corporativa em TypeScript com NestJS, Guards, Interceptors e DTOs",
        "description": "Operational skill for building enterprise-grade modular backends with NestJS, TypeScript, dependency injection, guards, interceptors, and Swagger.",
        "content": """# NestJS Modular Backend Engineering Skill

Skill operacional para desenvolvimento de backends corporativos escaláveis e modulares com NestJS.

## 1. Princípios de Governança
- **Módulos Isolados**: Cada domínio deve conter seu próprio `Module`, `Controller`, `Service`, `Repository` e `DTOs`.
- **Validação com Class-Validator**: Uso de `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`.
- **Tratamento de Exceções**: Uso de `HttpExceptionFilter` customizado retornando RFC 7807.

## 2. Padrão de Controller e DTO
```typescript
import { Controller, Post, Body, UseGuards, UseInterceptors } from '@nestjs/common';
import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';

export class CreateTenantDto {
  @IsNotEmpty()
  @IsString()
  name: string;

  @IsEmail()
  adminEmail: string;
}

@Controller('tenants')
export class TenantsController {
  constructor(private readonly tenantsService: TenantsService) {}

  @Post()
  async create(@Body() dto: CreateTenantDto) {
    return this.tenantsService.create(dto);
  }
}
```
"""
    },

    "graphql-apollo-federation": {
        "domain": "Backend & APIs",
        "scope": "Design de esquemas GraphQL, resolvers tipados, caching e Apollo Federation em microserviços",
        "description": "Operational skill for designing declarative GraphQL schemas, type-safe resolvers, DataLoader n+1 mitigation, and Apollo Federation subgraphs.",
        "content": """# GraphQL & Apollo Federation Skill

Skill operacional para APIs GraphQL declarativas, seguras contra problemas de N+1 e integradas em federação.

## 1. Boas Práticas
- **DataLoader**: Sempre agrupar e memorizar buscas em lote para evitar problemas de N+1 queries no banco de dados.
- **Complexity Limiter**: Limitar a profundidade e a complexidade das queries recebidas para prevenir ataques de negação de serviço (DoS).
- **Tipagem Estrita**: Gerar tipos TypeScript automaticamente a partir do schema via GraphQL Code Generator.
"""
    },

    "stripe-payments-engine": {
        "domain": "Backend & APIs",
        "scope": "Checkout global, verificação de webhooks, assinaturas recorrentes e split de pagamentos com Stripe",
        "description": "Operational skill for integrating Stripe payments, recurring subscriptions, webhook cryptographic signature verification, customer portal, and idempotency.",
        "content": """# Stripe Payments & Subscriptions Engine Skill

Skill operacional para integração de pagamentos, cobrança recorrente e processamento de webhooks com Stripe.

## 1. Regras de Ouro
1. **Idempotência**: Sempre enviar header `Idempotency-Key` em operações de cobrança para prevenir cobranças duplicadas em caso de retry.
2. **Verificação de Webhook**: NUNCA confiar no payload do webhook sem validar a assinatura criptográfica com `stripe.webhooks.constructEvent(payload, sig, endpointSecret)`.
3. **Persistência de Customer ID**: Vincular sempre o `stripeCustomerId` ao registro do usuário no banco local.

## 2. Validador de Webhook Canônico (Node.js)
```typescript
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: "2024-06-20" });

export async function handleStripeWebhook(rawBody: Buffer, signature: string) {
  const event = stripe.webhooks.constructEvent(rawBody, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  switch (event.type) {
    case "checkout.session.completed":
      const session = event.data.object as Stripe.Checkout.Session;
      await activateSubscription(session.customer as string, session.client_reference_id!);
      break;
    case "invoice.payment_failed":
      await notifyPaymentFailed(event.data.object);
      break;
  }
  return { received: true };
}
```
"""
    },

    "grpc-protobuf-microservices": {
        "domain": "Backend & APIs",
        "scope": "Comunicação inter-serviços de alta taxa de transferência com gRPC e Protocol Buffers",
        "description": "Operational skill for high-throughput inter-service RPC communication using gRPC, Protocol Buffers (.proto contracts), streaming, and deadliness.",
        "content": """# gRPC & Protocol Buffers Microservices Skill

Skill operacional para comunicação de baixíssima latência e alta taxa de transferência entre microsserviços.

## 1. Princípios
- **Contratos Claros**: Schemas `.proto` versionados de forma compatível retroativamente (nunca alterar números de campo já publicados).
- **Deadlines**: Toda chamada RPC DEVE definir um timeout/deadline explícito para evitar travamento em cascata.
- **Multiplexação HTTP/2**: Reutilizar canais gRPC criados em vez de criar novas conexões a cada requisição.
"""
    },

    # --- 2. Databases & Caching ---
    "postgresql-advanced-optimization": {
        "domain": "Databases & Caching",
        "scope": "Otimização de PostgreSQL, tuning de índices (B-Tree, GIN, BRIN), EXPLAIN ANALYZE e pooling",
        "description": "Operational skill for PostgreSQL query optimization, index tuning (B-Tree, GIN, BRIN), connection pooling with PgBouncer, and vacuum diagnostics.",
        "content": """# PostgreSQL Advanced Optimization Skill

Skill operacional para tuning de performance, indexação e escalabilidade em bancos de dados relacionais PostgreSQL.

## 1. Diretrizes de Indexação
- **Índices Compostos**: A ordem das colunas no índice deve seguir: `Igualdade -> Range/Comparação -> Ordenação (ORDER BY)`.
- **Índices Parciais**: Quando consultar frequentemente subconjuntos (ex: `WHERE status = 'active'`), crie índices parciais para economizar RAM e disco:
  `CREATE INDEX idx_orders_active ON orders (customer_id) WHERE status = 'active';`
- **Análise com EXPLAIN**: Nunca deduza lentidão sem rodar `EXPLAIN (ANALYZE, BUFFERS) <query>;`. Verifique se há `Seq Scan` em tabelas grandes.
"""
    },

    "redis-caching-queues": {
        "domain": "Databases & Caching",
        "scope": "Cache estratégico, estruturas Redis 7 (Hashes, Sets, Streams), BullMQ e locks distribuídos (Redlock)",
        "description": "Operational skill for high-speed caching strategies, Redis 7 data structures, background job queues with BullMQ, and distributed locks with Redlock.",
        "content": """# Redis Caching & Queue Engineering Skill

Skill operacional para estratégias de cache resiliente, filas de tarefas em segundo plano e bloqueios distribuídos.

## 1. Padrões de Cache
1. **Cache-Aside com TTL**: Todo valor em cache deve ter um TTL (*Time-To-Live*) definido para evitar vazamento de memória.
2. **Prevenção de Cache Stampede**: Usar locking distribuído ou *probabilistic early expiration* quando recomputar caches caros.
3. **Filas Confiáveis**: Utilizar BullMQ com backoff exponencial para retries de envio de e-mails, webhooks e geração de relatórios.
"""
    },

    "prisma-drizzle-orm": {
        "domain": "Databases & Caching",
        "scope": "Migrations automatizadas, consultas seguras com tipagem estrita e edge compatibility em Drizzle e Prisma",
        "description": "Operational skill for modern TypeScript ORMs (Drizzle ORM & Prisma), schema migrations, edge compatibility, and relation queries.",
        "content": """# Modern ORM (Drizzle & Prisma) Skill

Skill operacional para modelagem de banco de dados, migrations determinísticas e consultas tipadas em TypeScript.

## 1. Drizzle ORM (Edge-First & SQL-Like)
- Ideal para Cloudflare Workers (D1), Vercel Edge e ambientes serverless sem overhead de binários.
- Schemas declarativos em TypeScript com zero runtime code generation.

## 2. Prisma (Enterprise & Full-Featured)
- Ideal para servidores dedicados, NestJS e serviços com múltiplos relacionamentos aninhados.
- Sempre rodar `prisma migrate dev` em desenvolvimento e `prisma migrate deploy` na esteira de CI/CD.
"""
    },

    "mongodb-aggregation-pipeline": {
        "domain": "Databases & Caching",
        "scope": "Pipelines de agregação complexos, indexação composta e change streams no MongoDB",
        "description": "Operational skill for MongoDB document modeling, high-performance aggregation pipelines ($match, $group, $lookup), indexing, and change streams.",
        "content": """# MongoDB Aggregation Pipeline Skill

Skill operacional para consultas analíticas de alta performance e modelagem de documentos no MongoDB.

## 1. Otimização de Pipelines
- Sempre coloque o estágio `$match` e `$project` no início do pipeline para reduzir o volume de dados na memória RAM.
- Verifique o uso de índices em agregações com `db.collection.explain("executionStats").aggregate([...])`.
- Evite arrays com crescimento ilimitado dentro de documentos (anti-pattern de documentos de 16MB).
"""
    },

    "qdrant-vector-database": {
        "domain": "Databases & Caching",
        "scope": "Busca vetorial, coleções semânticas, filtragem de payloads e integração com RAG no Qdrant",
        "description": "Operational skill for vector similarity search, Qdrant collections, payload filtering, distance metrics (Cosine/Dot), and RAG retrieval pipelines.",
        "content": """# Qdrant Vector Search Skill

Skill operacional para indexação de embeddings, busca semântica aproximada (HNSW) e recuperação em sistemas RAG.

## 1. Configuração de Coleções
- **Métricas de Distância**: Usar `Cosine` para embeddings normalizados (OpenAI, Gemini text-embedding-004) ou `Dot` para embeddings de alta dimensão.
- **Payload Indexing**: Indexar campos de metadados (`tenant_id`, `created_at`, `category`) para permitir filtros rápidos combinados com a busca vetorial.
"""
    },

    # --- 3. Frontend & Mobile ---
    "nextjs-app-router-rsc": {
        "domain": "Frontend & Mobile",
        "scope": "Arquitetura Next.js 15, React Server Components (RSC), Server Actions, Suspense e streaming",
        "description": "Operational skill for Next.js 15 App Router architecture, React Server Components (RSC), Server Actions, partial prerendering, and streaming.",
        "content": """# Next.js 15 App Router & RSC Skill

Skill operacional para arquitetura de aplicações web modernas com Next.js 15, Server Components e Server Actions.

## 1. Diretrizes Fundamentais
1. **Server por Padrão**: Todos os componentes devem ser React Server Components por padrão. Adicione `"use client"` apenas quando houver `useState`, `useEffect`, ou listeners de eventos no navegador.
2. **Server Actions com Validação**: Server Actions devem sempre validar o payload recebido com Zod e verificar a autenticação da sessão.
3. **Streaming com Suspense**: Isole partes dinâmicas e demoradas da tela com `<Suspense fallback={<Skeleton />}>` para não bloquear a renderização inicial.
"""
    },

    "react-query-tanstack": {
        "domain": "Frontend & Mobile",
        "scope": "Gerenciamento de estado assíncrono, cache inteligente, revalidação e mutações com TanStack Query v5",
        "description": "Operational skill for asynchronous server state management using TanStack Query v5 (React Query), optimistic updates, caching, and prefetching.",
        "content": """# TanStack Query (React Query) v5 Skill

Skill operacional para gerenciamento de estado de servidor no frontend, cache reativo e sincronização em tempo real.

## 1. Padrões
- **Query Keys Declarativas**: Sempre estruture chaves como arrays hierárquicos: `['users', userId, 'profile']`.
- **Mutações Otimistas**: Atualizar a UI imediatamente no `onMutate` com rollback seguro no `onError`.
- **Evitar Over-fetching**: Configurar `staleTime` razoável (ex: 1 a 5 minutos) para dados que mudam com pouca frequência.
"""
    },

    "state-zustand-jotai": {
        "domain": "Frontend & Mobile",
        "scope": "Estado global leve, atômico e determinístico com Zustand e Jotai (sem boilerplate)",
        "description": "Operational skill for lightweight, boilerplate-free state management in React using Zustand and Jotai, persistent storage, and atomic state.",
        "content": """# Modern State Management (Zustand & Jotai) Skill

Skill operacional para gerenciamento de estado de cliente sem o overhead ou boilerplate de Redux.

## 1. Padrão Zustand
- Criar stores modulares e exportar seletores para evitar re-renderizações desnecessárias:
  `const user = useUserStore((state) => state.user);`
- Integrar com `persist` middleware para sincronização automática em `localStorage` quando aplicável.
"""
    },

    "react-native-expo": {
        "domain": "Frontend & Mobile",
        "scope": "Desenvolvimento mobile multiplataforma (iOS e Android) com Expo Router e React Native",
        "description": "Operational skill for cross-platform mobile app development with Expo Router, React Native, native modules, push notifications, and EAS builds.",
        "content": """# React Native & Expo Mobile Skill

Skill operacional para desenvolvimento de aplicativos móveis nativos para iOS e Android com Expo.

## 1. Melhores Práticas
- **Expo Router**: Roteamento baseado em arquivos nativo similar ao Next.js App Router (`app/(tabs)/index.tsx`).
- **Performance de Listas**: Utilizar `@shopify/flash-list` em vez de `FlatList` padrão para renderização de listas longas a 60/120 FPS.
- **Safe Area & Teclado**: Sempre envolver telas em `SafeAreaView` e gerenciar teclado com `KeyboardAvoidingView`.
"""
    },

    "web-vitals-performance": {
        "domain": "Frontend & Mobile",
        "scope": "Otimização de Core Web Vitals (LCP, INP, CLS), auditoria Lighthouse 100/100 e code-splitting",
        "description": "Operational skill for optimizing Core Web Vitals (LCP, INP, CLS), bundle size reduction, image optimization, dynamic imports, and Lighthouse audits.",
        "content": """# Core Web Vitals & Web Performance Skill

Skill operacional para auditoria e garantia de carregamento instantâneo e nota máxima em Web Vitals.

## 1. Metas Críticas
- **LCP (Largest Contentful Paint)**: < 2.5 segundos. Imagens de herói devem usar `priority` ou `fetchpriority="high"`.
- **INP (Interaction to Next Paint)**: < 200 ms. Evitar travar a main thread com JavaScript pesado; usar `requestIdleCallback` ou web workers.
- **CLS (Cumulative Layout Shift)**: < 0.1. Sempre reservar espaço em disco para imagens, vídeos e anúncios com dimensões explícitas (`aspect-ratio`, `width`, `height`).
"""
    },

    # --- 4. DevOps, CI/CD & Observability ---
    "github-actions-cicd": {
        "domain": "DevOps & CI/CD",
        "scope": "Pipelines de CI/CD automatizadas, testes em matriz, builds multi-plataforma e deploy seguro via OIDC",
        "description": "Operational skill for designing automated GitHub Actions CI/CD pipelines, caching dependencies, semantic releases, and OIDC secretless deployments.",
        "content": """# GitHub Actions CI/CD Automation Skill

Skill operacional para automação de testes, validações de qualidade e entrega contínua com GitHub Actions.

## 1. Boas Práticas
- **Cache de Dependências**: Utilizar `actions/cache` ou `actions/setup-node` com `cache: 'npm'` para acelerar execuções de minutos para segundos.
- **OIDC Secretless**: Utilizar OpenID Connect (OIDC) para autenticar no AWS/GCP/Cloudflare sem precisar armazenar chaves de longa duração nos secrets do repositório.
- **Branch Protection**: Bloquear merges na `main` sem que a suíte de testes e linter aprovem o Pull Request.
"""
    },

    "kubernetes-k8s-manifests": {
        "domain": "DevOps & CI/CD",
        "scope": "Orquestração de pods, deployments, ingress, autoscaling e manifestos K8s/K3s",
        "description": "Operational skill for Kubernetes and lightweight K3s cluster operations, writing manifests (Deployment, Service, Ingress), HPA autoscaling, and helm charts.",
        "content": """# Kubernetes & K3s Orchestration Skill

Skill operacional para orquestração de containers em escala com Kubernetes e K3s.

## 1. Requisitos de Manifesto
- **Resource Requests & Limits**: Todo container DEVE ter `requests` e `limits` explícitos de CPU e memória para evitar *Out-Of-Memory* (OOMKilled) em nós vizinhos.
- **Liveness & Readiness Probes**: Configurar sondas adequadas para reiniciar pods travados e só direcionar tráfego quando a aplicação estiver pronta.
- **SecurityContext**: Forçar `runAsNonRoot: true` e `readOnlyRootFilesystem: true`.
"""
    },

    "terraform-iac-automation": {
        "domain": "DevOps & CI/CD",
        "scope": "Infraestrutura como Código (IaC) com Terraform, módulos reutilizáveis e gestão de estado seguro",
        "description": "Operational skill for declarative Infrastructure as Code with Terraform, HashiCorp HCL, remote state locking, and modular cloud provisioning.",
        "content": """# Terraform Infrastructure as Code (IaC) Skill

Skill operacional para provisionamento determinístico de nuvem com Terraform.

## 1. Princípios
- **Remote State Locking**: Manter o `terraform.tfstate` em bucket remoto (S3/GCS/Cloudflare R2) com bloqueio via DynamoDB ou nativo para evitar concorrência.
- **Zero Hardcoding**: Variáveis sensíveis e dinâmicas devem ser passadas via `.tfvars` ou variáveis de ambiente `TF_VAR_`.
- **Plano Antes de Aplicar**: Sempre rodar `terraform plan` e inspecionar o diff antes de `terraform apply`.
"""
    },

    "prometheus-grafana-metrics": {
        "domain": "DevOps & CI/CD",
        "scope": "Exposição de métricas RED/USE, configuração de painéis no Grafana e alertas em tempo real",
        "description": "Operational skill for observability, metric exposition with Prometheus client, PromQL queries, Grafana dashboards, and Alertmanager routing.",
        "content": """# Prometheus & Grafana Observability Skill

Skill operacional para telemetria, instrumentação de métricas e monitoramento de saúde de sistemas.

## 1. Método RED (Para Serviços Web)
- **Rate**: Quantidade de requisições por segundo (`sum(rate(http_requests_total[1m]))`).
- **Errors**: Quantidade de falhas HTTP 5xx (`sum(rate(http_requests_total{status=~"5.."}[1m]))`).
- **Duration**: Tempo de resposta em percentis P95 e P99 via histogramas.
"""
    },

    "sentry-error-tracking": {
        "domain": "DevOps & CI/CD",
        "scope": "Monitoramento de erros em tempo real, upload de source maps, session replay e profiling com Sentry",
        "description": "Operational skill for Sentry SDK instrumentation, frontend/backend error grouping, release tracking, source map uploads, and performance profiling.",
        "content": """# Sentry Error Monitoring & Profiling Skill

Skill operacional para rastreamento de bugs em produção com captura de pilha de execução e reprodução de sessões.

## 1. Diretrizes
- **Source Maps**: Sempre enviar source maps durante a esteira de build/CI e nunca expô-los publicamente no bundle de produção.
- **Sanitização de Dados (PII)**: Usar hooks `beforeSend` para remover senhas, dados de cartão ou tokens dos logs enviados ao Sentry.
"""
    },

    # --- 5. AI Engineering & LLM Workflows ---
    "langchain-langgraph-orchestration": {
        "domain": "AI & Agentic Engineering",
        "scope": "Orquestração de agentes cíclicos com estado, LangGraph, roteamento de ferramentas e memória persistente",
        "description": "Operational skill for building complex multi-agent architectures with LangGraph, cyclical execution graphs, state persistence, and human-in-the-loop validation.",
        "content": """# LangGraph & Multi-Agent Orchestration Skill

Skill operacional para arquitetura de agentes autônomos baseados em grafos de estado.

## 1. Conceitos Chave
- **StateGraph**: O estado da conversa/tarefa é compartilhado entre nós (`Nodes`) através de canais imutáveis.
- **Roteamento Condicional**: Arestas condicionais determinam o próximo passo com base no output do modelo (ex: chamar ferramenta vs responder ao usuário).
- **Checkpointers**: Permite pausar a execução, solicitar aprovação humana (*human-in-the-loop*) e retomar exatamente do mesmo ponto.
"""
    },

    "rag-chunking-embeddings": {
        "domain": "AI & Agentic Engineering",
        "scope": "Pipelines de RAG avançado, divisão semântica de texto (chunking), busca híbrida BM25 + Vetorial e re-ranking",
        "description": "Operational skill for advanced Retrieval-Augmented Generation (RAG), semantic document chunking, hybrid search (dense + sparse), and cross-encoder re-ranking.",
        "content": """# Advanced RAG & Retrieval Pipelines Skill

Skill operacional para construção de sistemas de recuperação de conhecimento com alta precisão e baixa alucinação.

## 1. Diretrizes de Sucesso em RAG
1. **Chunking Inteligente**: Não dividir por tamanho fixo cego. Respeite parágrafos, cabeçalhos Markdown e funções de código com sobreposição (*overlap*) de 10-20%.
2. **Busca Híbrida**: Combinar busca por palavras-chave exatas (BM25) com busca vetorial densa (Embeddings) para cobrir termos técnicos e siglas.
3. **Re-Ranking**: Aplicar um modelo de re-ranking (Cohere Rerank ou Cross-Encoder) nos top 20 resultados para enviar apenas os top 5 mais relevantes para o prompt final.
"""
    },

    "prompt-engineering-jailbreak-defense": {
        "domain": "AI & Agentic Engineering",
        "scope": "Engenharia de prompts robusta, defesa contra injeção de prompt (prompt injection) e estruturação de contexto",
        "description": "Operational skill for robust system prompt engineering, delimiter isolation, defending against direct/indirect prompt injections, and few-shot calibration.",
        "content": """# Robust Prompt Engineering & Security Skill

Skill operacional para construção de prompts seguros, imunes a injeções indiretas e calibrados para raciocínio analítico.

## 1. Defesa Contra Injeção de Prompt
- **Isolamento de Dados Não Confiáveis**: Sempre envolver conteúdo vindo de usuários ou páginas da web em delimitadores estritos (ex: `<user_input>...</user_input>`).
- **Instrução de Imunidade**: Explicitamente declarar que comandos encontrados dentro dos delimitadores devem ser tratados estritamente como texto/dados e nunca executados como ordens.
- **Output Validation**: Validar as saídas com schemas JSON rígidos antes de passar dados para ferramentas de mutação ou banco.
"""
    },

    "whisper-stt-neural-voice": {
        "domain": "AI & Agentic Engineering",
        "scope": "Transcrição de áudio com OpenAI Whisper, diarização de locutores e tratamento de ruído acústico",
        "description": "Operational skill for speech-to-text audio processing using Whisper models, speaker diarization, chunked audio processing, and subtitle generation.",
        "content": """# Whisper Audio & Speech-to-Text Skill

Skill operacional para transcrição automatizada de chamadas, reuniões e notas de voz com Whisper.

## 1. Processamento de Áudio
- **Normalização**: Converter áudio de entrada para 16kHz mono WAV antes da inferência para máxima precisão e velocidade.
- **Divisão em Janelas**: Arquivos maiores que 25MB devem ser divididos em chunks de 30 segundos em pausas de silêncio (usando `pydub` ou `ffmpeg`).
"""
    },

    "elevenlabs-tts-voiceover": {
        "domain": "AI & Agentic Engineering",
        "scope": "Síntese de voz neural ultrarrealista com ElevenLabs API, controle emocional e streaming de áudio",
        "description": "Operational skill for realistic neural voice synthesis using ElevenLabs API, voice cloning, latency-optimized audio streaming, and SSML tags.",
        "content": """# ElevenLabs Neural Voice Synthesis Skill

Skill operacional para geração de locuções hiper-realistas, clones de voz corporativos e streaming de áudio.

## 1. Melhores Práticas
- **Streaming de Baixa Latência**: Usar endpoints de WebSockets ou chunked HTTP para tocar áudio em tempo real enquanto o texto ainda está sendo gerado.
- **Modelos**: Usar `eleven_multilingual_v2` para português com entonação natural e clareza fonética.
"""
    },

    # --- 6. Testing, Automation & Productivity ---
    "playwright-e2e-testing": {
        "domain": "Testing & QA",
        "scope": "Testes end-to-end automatizados com Playwright, regressão visual, gravação de traces e execução headless",
        "description": "Operational skill for cross-browser end-to-end testing with Playwright, Page Object Models, auto-waiting locators, visual regression, and CI execution.",
        "content": """# Playwright End-to-End Testing Skill

Skill operacional para garantia de qualidade e automação de testes em navegadores reais com Playwright.

## 1. Regras Canônicas
1. **Locators com Papéis Semânticos**: Priorize sempre seletores acessíveis: `page.getByRole('button', { name: 'Entrar' })` ou `page.getByLabel('E-mail')`. Evite XPaths frágeis.
2. **Auto-waiting**: Nunca use `page.waitForTimeout(5000)`. O Playwright espera automaticamente que os elementos estejam visíveis e clicáveis.
3. **Traces em Falhas**: Configurar `trace: 'on-first-retry'` para inspecionar screenshots e requisições de rede detalhadas quando um teste quebrar na esteira de CI.
"""
    },

    "pytest-mocking-fixtures": {
        "domain": "Testing & QA",
        "scope": "Testes unitários e de integração em Python com Pytest, fixtures parametrizadas, mocking e cobertura",
        "description": "Operational skill for Python automated testing using pytest, parameterized fixtures, monkeypatching, database mocking, and pytest-cov coverage.",
        "content": """# Pytest Unit & Integration Testing Skill

Skill operacional para suítes de testes robustas, rápidas e determinísticas em Python.

## 1. Padrões
- **Fixtures com Escopo**: Use `scope="session"` para recursos caros (como subida de container de teste) e `scope="function"` para estados isolados.
- **Mocking Externo**: Chamadas de rede HTTP externas devem ser sempre mockadas (com `respx` para httpx ou `responses` para requests) para evitar testes intermitentes.
"""
    },

    "web-scraping-crawling": {
        "domain": "Automation & Crawling",
        "scope": "Extração de dados resiliente, bypass de anti-bot, Playwright headless, Beautiful Soup e rotação de proxies",
        "description": "Operational skill for resilient web scraping, crawling architectures, bypassing Cloudflare/bot protections, HTML parsing, and structured data extraction.",
        "content": """# Resilient Web Scraping & Crawling Skill

Skill operacional para ingestão de dados da web, navegação automatizada e parsing estruturado.

## 1. Diretrizes de Resiliência
- **Headers Realistas**: Enviar sempre `User-Agent`, `Accept-Language` e cabeçalhos `Sec-CH-UA` idênticos aos de um navegador Chrome real.
- **Tratamento de Rate-Limit (429)**: Implementar espera exponencial (*exponential backoff com jitter*) quando o servidor remoto solicitar espera.
- **Extração Semântica**: Priorizar dados estruturados JSON-LD (`<script type="application/ld+json">`) na página antes de fazer parsing manual de seletores CSS voláteis.
"""
    },

    "seo-technical-structured-data": {
        "domain": "SEO & Performance",
        "scope": "SEO técnico, Schema.org JSON-LD, metatags OpenGraph/Twitter, sitemaps XML e indexação no Google",
        "description": "Operational skill for technical SEO optimization, Schema.org JSON-LD structured data, OpenGraph cards, canonical tags, and search engine indexing.",
        "content": """# Technical SEO & Structured Data Skill

Skill operacional para posicionamento orgânico de ponta e indexação no Google para todas as landing pages e apps da AXION.

## 1. Itens Obrigatórios em Todas as Páginas
1. **JSON-LD Schema**: Incluir esquema `Organization`, `WebSite`, `Product` ou `Article` no `<head>`.
2. **Canonical Tag**: Tag `<link rel="canonical" href="https://dominio.com/pagina" />` explícita para evitar conteúdo duplicado.
3. **OpenGraph & Twitter**: Metatags `og:title`, `og:description`, `og:image` (1200x630px) e `twitter:card`.
"""
    },

    "pdf-generation-puppeteer": {
        "domain": "Document Automation",
        "scope": "Geração de relatórios PDF pixel-perfect a partir de HTML/CSS com Puppeteer/Playwright e print styles",
        "description": "Operational skill for generating pixel-perfect PDF invoices, contracts, and analytics reports from HTML/CSS using headless Chrome print styles.",
        "content": """# Pixel-Perfect PDF Generation Skill

Skill operacional para geração automatizada de relatórios comerciais, contratos e faturas em PDF de alta qualidade.

## 1. Princípios de Estilização para Impressão
- **CSS Paged Media**:
  ```css
  @page {
    size: A4;
    margin: 20mm;
  }
  .page-break {
    page-break-after: always;
  }
  ```
- **Puppeteer Flags**: Executar com `--no-sandbox` e aguardar `networkidle0` para garantir que fontes do Google e imagens estejam 100% carregadas antes do print.
"""
    }
}

def install_skills():
    print(f"[*] Instalando {len(NEW_SKILLS)} novas skills canônicas...")
    
    for name, data in NEW_SKILLS.items():
        # Formata o SKILL.md
        full_content = f"""---
name: {name}
description: >-
  {data['description']}
---

{data['content'].strip()}
"""
        # Salva no workspace
        ws_dir = WORKSPACE_SKILLS / name
        ws_dir.mkdir(parents=True, exist_ok=True)
        (ws_dir / "SKILL.md").write_text(full_content, encoding="utf-8")
        
        # Salva no diretório global do sistema
        gb_dir = GLOBAL_SKILLS / name
        gb_dir.mkdir(parents=True, exist_ok=True)
        (gb_dir / "SKILL.md").write_text(full_content, encoding="utf-8")
        
        print(f"[OK] Instalada: {name}")

if __name__ == "__main__":
    install_skills()
