---
name: nestjs-modular-backend
description: >-
  Operational skill for building enterprise-grade modular backends with NestJS, TypeScript, dependency injection, guards, interceptors, and Swagger.
---

# NestJS Modular Backend Engineering Skill

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
