---
name: nestjs-modular-backend
description: >-
  Operational engineering skill for building enterprise modular backends with NestJS, TypeScript, dependency injection, DTO validation pipes, RBAC guards, and graceful shutdown hooks.
---

# NestJS Modular Backend Engineering Skill

Guia operacional para arquitetura de microsserviços e monólitos modulares com NestJS, tipagem estrita com TypeScript, injeção de dependências desacoplada e resiliência em contêineres.

---

## 1. Topologia Modular & Encapsulamento

Adote uma estrutura Domain-Driven Design (DDD) onde cada módulo é estritamente autocontido:
```
src/
├── core/                  # Módulo global: logger, interceptors, filtros de exceção
├── shared/                # Módulos transversais: prisma/drizzle service, mailer, redis
└── modules/
    ├── auth/              # Tokens JWT, estratégias passport, guards de permissão
    └── tenants/           # Domínio específico de empresas/tenants
        ├── dto/
        │   ├── create-tenant.dto.ts
        │   └── update-tenant.dto.ts
        ├── tenants.controller.ts
        ├── tenants.service.ts
        ├── tenants.repository.ts
        └── tenants.module.ts
```

> **Regra de Encapsulamento**: Serviços internos de um módulo nunca devem ser importados diretamente por outro módulo. O módulo provedor DEVE explicitamente adicioná-los no array `exports: [...]` de seu `@Module()`.

---

## 2. Bootstrapping Seguro & Lifecycle (`main.ts`)

```typescript
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });

  // 1. Shutdown hooks obrigatórios para Kubernetes/Docker
  app.enableShutdownHooks();

  // 2. Validação rigorosa de DTOs com strip de propriedades não mapeadas
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,              // Remove propriedades desconhecidas do payload
      forbidNonWhitelisted: true,   // Lança 400 Bad Request se houver chaves estranhas
      transform: true,              // Converte payloads primitivos para instâncias de classe
      transformOptions: { enableImplicitConversion: false },
    })
  );

  // 3. Prefixo de versão de API
  app.setGlobalPrefix('api/v1');

  await app.listen(process.env.PORT ?? 3000, '0.0.0.0');
}
bootstrap();
```

---

## 3. DTOs Tipados e Validação Declarativa

Nunca use `any` ou tipos anônimos em `@Body()`:

```typescript
import { IsEmail, IsNotEmpty, IsString, Length, Matches } from 'class-validator';

export class CreateTenantDto {
  @IsNotEmpty({ message: 'Nome da organização é obrigatório' })
  @IsString()
  @Length(3, 80)
  name: string;

  @IsEmail({}, { message: 'E-mail de contato corporativo inválido' })
  adminEmail: string;

  @IsString()
  @Matches(/^[a-z0-9\-]+$/, { message: 'Slug deve conter apenas letras minúsculas, números e hífens' })
  slug: string;
}
```

---

## 4. Guards de Autorização (RBAC)

Implemente autenticação e controle de acesso granular por papéis:

```typescript
import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>('roles', [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    const hasRole = requiredRoles.some((role) => user?.roles?.includes(role));
    if (!hasRole) {
      throw new ForbiddenException('Acesso restrito ao perfil requerido.');
    }
    return true;
  }
}
```

---

## 5. Ferramental Integrado

Audite o código-fonte de projetos NestJS com o linter embutido:
```powershell
python .agents/skills/nestjs-modular-backend/scripts/nest_module_auditor.py <pasta-src>
```
O linter valida:
- Presença de `enableShutdownHooks()` em `main.ts`.
- Configuração estrita de `ValidationPipe`.
- Controladores com `@Body()` sem tipagem ou usando `any`.
