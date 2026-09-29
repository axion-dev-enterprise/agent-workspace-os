import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

WORKSPACE = Path(r"C:\workspace")

print("=" * 80)
print("             RELATÓRIO DE ANÁLISE PROFUNDA DE LOGS E TELEMETRIA")
print("=" * 80)

# 1. PM2 LOGS: BRAIN SERVER
print("\n--- [1] PM2: axion-brain-server ---")
brain_out = WORKSPACE / "memory" / "brain" / "pm2_logs" / "out.log"
brain_err = WORKSPACE / "memory" / "brain" / "pm2_logs" / "error.log"

if brain_out.exists():
    lines = brain_out.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"out.log total linhas: {len(lines)}")
    recent_out = lines[-35:]
    print("Últimas 35 linhas de out.log:")
    for l in recent_out:
        print("  ", l)

if brain_err.exists():
    lines = brain_err.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"\nerror.log total linhas: {len(lines)}")
    # Filtra linhas relevantes excluindo repetições normais do watcher daemon
    relevant_err = [l for l in lines if "[WATCHER SUMMARY" not in l and "[WATCHER] Daemon" not in l]
    print(f"Linhas relevantes com possíveis erros/warnings: {len(relevant_err)}")
    for l in relevant_err[-20:]:
        print("  ERR>", l)

# 2. PM2 LOGS: TELEGRAM BOT
print("\n--- [2] PM2: axion-telegram-bot ---")
tg_out = WORKSPACE / "memory" / "telegram" / "pm2_logs" / "out.log"
tg_err = WORKSPACE / "memory" / "telegram" / "pm2_logs" / "error.log"

if tg_out.exists():
    lines = tg_out.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"out.log total linhas: {len(lines)}")
    for l in lines[-25:]:
        print("  ", l)

if tg_err.exists():
    lines = tg_err.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"\nerror.log total linhas: {len(lines)}")
    # Ignora logs antigos de dias atrás
    for l in lines[-15:]:
        print("  ERR>", l)

# 3. PM2 LOGS: WHATSAPP BRIDGE
print("\n--- [3] PM2: axion-whatsapp-bridge ---")
wa_out = WORKSPACE / "scripts" / "whatsapp_bridge" / "memory" / "whatsapp" / "pm2_logs" / "out.log"
wa_err = WORKSPACE / "scripts" / "whatsapp_bridge" / "memory" / "whatsapp" / "pm2_logs" / "error.log"

if wa_out.exists():
    lines = wa_out.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"out.log total linhas: {len(lines)}")
    for l in lines[-35:]:
        print("  ", l)

if wa_err.exists():
    lines = wa_err.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"\nerror.log total linhas: {len(lines)}")
    for l in lines[-20:]:
        print("  ERR>", l)

# 4. WATCHER: EXECUTIONS & STATS
print("\n--- [4] WATCHER TELEMETRY ---")
stats_file = WORKSPACE / "memory" / "watcher" / "watcher_stats.json"
if stats_file.exists():
    try:
        stats = json.loads(stats_file.read_text(encoding='utf-8', errors='replace'))
        print("Estatísticas consolidadas do Watcher:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Erro ao ler watcher_stats:", e)

exec_file = WORKSPACE / "memory" / "watcher" / "executions.jsonl"
if exec_file.exists():
    lines = exec_file.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f"\nTotal de execuções no histórico: {len(lines)}")
    print("Últimas 8 execuções detalhadas:")
    for l in lines[-8:]:
        try:
            d = json.loads(l)
            eid = d.get('execution_id')
            ts = d.get('finished_at', '')[:19]
            score = d.get('total_score', 0)
            grade = d.get('grade', '?')
            term = d.get('terminated_by', '?')
            dur = d.get('duration_seconds', 0)
            goal = d.get('goal', '')[:80].replace('\n', ' ')
            tools = d.get('tools_executed', [])
            scores = d.get('scores', {})
            print(f"  • [{ts}] {eid} | Score: {score:.1f}/10 [{grade}] | Dur: {dur}s | Term: {term}")
            print(f"    Goal: \"{goal}\"")
            print(f"    Tools: {tools} | Subscores: {scores}")
        except Exception as e:
            pass

# 5. REQUESTS DO BRAIN SERVER
print("\n--- [5] ÚLTIMOS REQUESTS DO BRAIN SERVER (memory/brain/requests) ---")
req_dir = WORKSPACE / "memory" / "brain" / "requests"
if req_dir.exists():
    req_files = sorted(req_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    print(f"Total de arquivos de request: {len(req_files)}")
    print("Últimos 6 requests processados:")
    for rf in req_files[:6]:
        try:
            d = json.loads(rf.read_text(encoding='utf-8', errors='replace'))
            rid = rf.stem
            st = d.get('status')
            start = d.get('started_at', '')[:19]
            fin = d.get('finished_at', '')[:19]
            cid = d.get('chat_id')
            err = d.get('error')
            tools = d.get('tools_used', [])
            fc = d.get('first_content', '')[:60].replace('\n', ' ')
            print(f"  • Request {rid} [{st}] | Chat: {cid} | Start: {start} -> Fin: {fin}")
            if fc:
                print(f"    First Content: \"{fc}...\"")
            if tools:
                print(f"    Tools Usadas: {tools}")
            if err:
                print(f"    ERRO REGISTRADO: {err}")
        except Exception as e:
            pass

print("\n" + "=" * 80)
print("FIM DO RELATÓRIO DE ANÁLISE")
print("=" * 80)
