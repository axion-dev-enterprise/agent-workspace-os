---
name: vps-docker-orchestration
description: >-
  Operational skill for managing remote Linux compute nodes, VPS servers, Docker multi-stage builds,
  Docker Compose orchestration, PM2 process supervisors, systemd service units, and network bridges.
  Use when provisioning VPS nodes, orchestrating backend services, configuring healthchecks,
  and automating deployments for vps-node-01.
---

# VPS Nodes & Docker Orchestration Skill

Skill operacional para administração de nós computacionais remotos (Linux/Ubuntu), orquestração de containers com Docker Compose, automação de deploys e supervisão de processos na infraestrutura **AXION VPS**.

---

## 1. Princípios de Segurança & Hardening de Nós VPS

1. **Acesso SSH com Chaves**: Desativar autenticação por senha (`PasswordAuthentication no`) em `/etc/ssh/sshd_config`.
2. **Firewall UFW Ativo**: Permitir apenas portas essenciais:
   `ufw default deny incoming; ufw allow 22/tcp; ufw allow 80/tcp; ufw allow 443/tcp; ufw enable`
3. **Isolamento de Containers**: Nunca rodar containers Docker como usuário `root`. Especificar sempre `USER node` ou criar usuário sem privilégios no `Dockerfile`.

---

## 2. Padrão Canônico: `docker-compose.yml` de Produção

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000" # Exposto apenas internamente para o reverse proxy
    environment:
      - NODE_ENV=production
      - PORT=3000
    deploy:
      resources:
        limits:
          cpus: "1.5"
          memory: 1024M
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  redis_data:
```

---

## 3. Comandos Operacionais Frequentes no Nó

```bash
# Verificar uso de recursos em tempo real de todos os containers
docker stats --no-stream

# Reiniciar stack com zero downtime após pull
docker compose pull && docker compose up -d --remove-orphans

# Limpeza de imagens antigas e volumes órfãos
docker system prune -af --volumes

# Inspecionar logs de serviço específico
docker compose logs -f --tail=100 api
```

---

## 4. Supervisão com Systemd & PM2

Para microsserviços rodando nativamente fora do Docker:

```bash
# Iniciar e configurar PM2 para iniciar no boot do sistema
pm2 start ecosystem.config.js --env production
pm2 save
pm2 startup systemd
```
