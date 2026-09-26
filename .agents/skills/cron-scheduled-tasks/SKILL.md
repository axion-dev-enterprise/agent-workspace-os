---
name: cron-scheduled-tasks
description: >-
  Operational skill for Cron Jobs, Windows Task Scheduler, Linux Systemd Timers, Cloudflare Cron Triggers,
  and GitHub Actions Scheduled Workflows. Use when authoring, deploying, inspecting, automating, or debugging
  periodic background jobs, maintenance routines, self-healing watchdogs, and backup schedules across AXION nodes.
---

# Cron & Scheduled Tasks Skill — Enterprise Organization

Guia canônico e operacional para automação de tarefas periódicas, daemons de monitoramento e rotinas de manutenção em toda a infraestrutura híbrida da **Enterprise Organization** (Windows Workstation, Linux VPS, Cloudflare Edge e GitHub Actions).

---

## 1. Matriz de Plataformas de Agendamento

| Plataforma / Nó | Mecanismo Nativo | Ferramenta / CLI | Caso de Uso Primário |
| :--- | :--- | :--- | :--- |
| **Estação Windows Local** | Windows Task Scheduler | PowerShell (`Register-ScheduledTask`) | Watchdogs de saúde locais, backups para drive E:, sincronizações |
| **Nós Linux VPS (Debian)** | Systemd Timers & Services | `systemctl` / `/etc/systemd/system/` | Manutenção de banco de dados, Docker prune, health checks de containers |
| **Cloudflare Edge** | Cloudflare Cron Triggers | `wrangler.toml` (`[triggers]`) | Limpeza de KV namespaces, rotação de logs de borda, tarefas serverless |
| **GitHub Actions** | Workflow `schedule.cron` | `.github/workflows/*.yml` | Auditoria semanal de repositórios, verificações de segurança, CI periódico |

---

## 2. Windows Task Scheduler (PowerShell)

### 2.1 Padrão Canônico de Registro
```powershell
# 1. Definir a Ação (Executável + Argumentos + Diretório de Trabalho)
$action = New-ScheduledTaskAction `
    -Execute "python.exe" `
    -Argument "C:\workspace\scripts\health_monitor_autofix.py" `
    -WorkingDirectory "C:\workspace"

# 2. Definir o Gatilho (Trigger)
# Exemplo A: A cada 30 minutos indefinidamente
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)

# Exemplo B: Diariamente às 03:00 da manhã
# $trigger = New-ScheduledTaskTrigger -Daily -At "03:00AM"

# 3. Configurações de Resiliência (Baterias, Reinicialização, Catch-up)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# 4. Registrar a Tarefa (Forçar sobrescrita idempotente)
Register-ScheduledTask `
    -TaskName "AXION-Health-Watchdog" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Force
```

### 2.2 Comandos de Gerenciamento & Diagnóstico
```powershell
# Listar tarefas com prefixo AXION
Get-ScheduledTask -TaskName "AXION-*" | Select-Object TaskName, State

# Disparar execução manual imediata
Start-ScheduledTask -TaskName "AXION-Enterprise-Backup"

# Obter histórico do último resultado e horário de execução
Get-ScheduledTaskInfo -TaskName "AXION-Health-Watchdog"

# Remover tarefa agendada
Unregister-ScheduledTask -TaskName "AXION-Antiga" -Confirm:$false
```

---

## 3. Linux Systemd Timers (Debian 12/13 VPS)

O Debian 13 utiliza **Systemd Timers** em substituição ao clássico crontab para maior controle de dependências, cgroups e logs no `journalctl`.

### 3.1 Padrão de Serviço (`/etc/systemd/system/axion-vacuum.service`)
```ini
[Unit]
Description=AXION PostgreSQL Vacuum & Maintenance Service
After=docker.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/opt/hermes
ExecStart=/usr/bin/docker exec hermes-postgres psql -U hermes -d hermes_db -c "VACUUM (ANALYZE);"
StandardOutput=journal
StandardError=journal
```

### 3.2 Padrão de Timer (`/etc/systemd/system/axion-vacuum.timer`)
```ini
[Unit]
Description=Run AXION PostgreSQL Vacuum weekly on Sunday at 02:00 AM

[Timer]
OnCalendar=Sun *-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

### 3.3 Comandos de Ativação no Linux
```bash
# Recarregar daemon do systemd
systemctl daemon-reload

# Habilitar e iniciar o timer
systemctl enable --now axion-vacuum.timer

# Verificar status e próximo disparo
systemctl list-timers --all | grep axion

# Inspecionar logs da última execução
journalctl -u axion-vacuum.service -n 50 --no-pager
```

---

## 4. Cloudflare Cron Triggers (Edge Workers)

### 4.1 Configuração no `wrangler.toml`
```toml
name = "axion-kv-cleanup-worker"
main = "src/index.ts"
compatibility_date = "2026-09-25"

# Executar a cada 6 horas
[triggers]
crons = ["0 */6 * * *"]
```

### 4.2 Handler em TypeScript (`src/index.ts`)
```typescript
export default {
  // Chamada HTTP padrão
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("AXION Scheduled Worker Active");
  },

  // Handler agendado executado pelo Cron Trigger
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    console.log(`[Cron Trigger] Executado em: ${event.cron} às ${new Date(event.scheduledTime).toISOString()}`);
    ctx.waitUntil(cleanupOldTelemetry(env));
  }
};

async function cleanupOldTelemetry(env: Env) {
  // Lógica de purga de chaves expiradas no KV
}
```

---

## 5. Boas Práticas & Prevenção de Falhas

1. **Proteção contra Execução Concorrente (Overlap)**:
   - Scripts de longa duração (backups pesados) devem usar locks de arquivo (`fcntl.flock` no Linux ou Mutex nomeado no Windows via Python).
2. **Timeouts Mandatórios**:
   - Sempre definir `timeout` nos comandos de subprocessos (30 a 60s) para evitar que processos filhos bloqueiem o agendador em loop infinito.
3. **Idempotência**:
   - Assegurar que qualquer tarefa agendada possa ser executada múltiplas vezes consecutivas sem corromper estado ou gerar dados duplicados.
4. **Captura e Redirecionamento de Saída**:
   - Em scripts Python de automação, usar `sys.stdout.reconfigure(line_buffering=True)` e gravar manifestos estruturados em JSON para auditoria.
