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

1. **Acesso SSH com Chaves Criptográficas (Ed25519)**: Desativar autenticação por senha (`PasswordAuthentication no`) em `/etc/ssh/sshd_config.d/00-custom.conf`. Operar em porta alta não-padrão (`Port 22022`).
2. **Firewall UFW Ativo & Estrito**:
   - `ufw default deny incoming; ufw default allow outgoing`
   - Permitir apenas tráfego estritamente autorizado: `22022/tcp`, `80/tcp`, `443/tcp`.
3. **Mitigação Ativa com Fail2ban**:
   - Pacote `fail2ban` ativo com jail `sshd` monitorando a porta customizada:
     - `bantime = 2h`, `findtime = 10m`, `maxretry = 3`, `banaction = ufw`.
   - Inclusão mandatória de `ignoreip = 127.0.0.1/8 ::1 100.64.0.0/10` para proteger a Tailnet contra bloqueios acidentais.
4. **Tailnet Mesh VPN (WireGuard Privado)**:
   - Todo nó VPS de produção DEVE estar conectado à Tailnet corporativa (`tailscale up --ssh`).
   - Priorizar conexões administrativas pelo IP privado `100.x.y.z` ou via MagicDNS (`vps-node-01-core`, `vps-node-01-clients`).
5. **Zero Attack Surface em Bancos de Dados**:
   - NUNCA mapear portas de banco de dados (`5432` PostgreSQL, `6379` Redis, etc.) para o host público (`0.0.0.0`).
   - Bancos devem residir exclusivamente dentro de redes bridge isoladas do Docker (`driver: bridge`).
6. **Isolamento de Containers**: Nunca rodar processos de aplicação como `root`. Especificar sempre `USER node` ou usuário restrito no `Dockerfile`.

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
