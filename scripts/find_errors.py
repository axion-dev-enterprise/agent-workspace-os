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

workspace = Path(r"C:\workspace")

print("=" * 80)
print("             VARREDURA EXAUSTIVA DE ERROS NO ECOSSISTEMA AXION")
print("=" * 80)

# 1. Requests com erro
print("\n--- 1. REQUESTS COM ERRO EM memory/brain/requests ---")
req_dir = workspace / "memory" / "brain" / "requests"
error_requests = []
all_requests = []
if req_dir.exists():
    for f in req_dir.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            all_requests.append((f.stat().st_mtime, f.stem, d))
            if d.get("status") == "error":
                error_requests.append((f.stat().st_mtime, f.stem, d))
        except Exception as e:
            print(f"Arquivo corrompido em requests: {f.name}: {e}")

all_requests.sort(key=lambda x: x[0], reverse=True)
error_requests.sort(key=lambda x: x[0], reverse=True)

print(f"Total de requests analisados: {len(all_requests)}")
print(f"Total com status ERROR: {len(error_requests)}")
for mtime, rid, d in error_requests[:10]:
    dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    cid = d.get("chat_id")
    err = d.get("error")
    steps = d.get("steps") or []
    msg = d.get("first_content") or (steps[0].get("description", "") if steps else "")
    print(f"  • [{dt}] {rid} | Chat: {cid} | Err: {err}")

# 2. Últimas linhas dos error.logs do PM2
print("\n--- 2. LOGS DE ERRO DO PM2 ---")
log_paths = [
    ("Brain Server Error Log", workspace / "memory" / "brain" / "pm2_logs" / "error.log"),
    ("Telegram Bot Error Log", workspace / "memory" / "telegram" / "pm2_logs" / "error.log"),
    ("WhatsApp Bridge Error Log", workspace / "scripts" / "whatsapp_bridge" / "memory" / "whatsapp" / "pm2_logs" / "error.log"),
]

for title, lp in log_paths:
    print(f"\n[{title}]: {lp}")
    if lp.exists():
        lines = lp.read_text(encoding="utf-8", errors="replace").splitlines()
        # Filtra linhas rotineiras do watcher
        filtered = [l for l in lines if "[WATCHER SUMMARY" not in l and "[WATCHER] Daemon" not in l]
        print(f"Total de linhas (filtradas): {len(filtered)}")
        for l in filtered[-15:]:
            print("  ERR>", l)
    else:
        print("  Arquivo não existe.")

# 3. Anomalias do Watcher
print("\n--- 3. ANOMALIAS DO WATCHER (Grade D ou F / Erros) ---")
anom_file = workspace / "memory" / "watcher" / "anomalies.jsonl"
if anom_file.exists():
    lines = anom_file.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"Total de anomalias registradas: {len(lines)}")
    for l in lines[-8:]:
        try:
            d = json.loads(l)
            ts = d.get("finished_at", "?")[:19]
            eid = d.get("execution_id")
            score = d.get("total_score")
            term = d.get("terminated_by")
            reason = d.get("goal_check_reason")
            goal = (d.get("goal") or "")[:60].replace("\n", " ")
            print(f"  • [{ts}] {eid} | Score: {score} | Term: {term} | Goal: \"{goal}\"")
            if reason:
                print(f"    Motivo: {reason}")
        except Exception:
            pass

# 4. Out.logs recentes das últimas 2 horas
print("\n--- 4. EVENTOS RECENTES EM OUT.LOGS (Últimas 2 Horas) ---")
now_ts = datetime.now().timestamp()
two_hours_ago = now_ts - 7200

# WhatsApp
wa_out = workspace / "scripts" / "whatsapp_bridge" / "memory" / "whatsapp" / "pm2_logs" / "out.log"
if wa_out.exists():
    print("\n[WhatsApp Bridge - out.log últimas 25 linhas]:")
    for l in wa_out.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]:
        print("  WA>", l)

# Brain
brain_out = workspace / "memory" / "brain" / "pm2_logs" / "out.log"
if brain_out.exists():
    print("\n[Brain Server - out.log últimas 25 linhas]:")
    for l in brain_out.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]:
        print("  BR>", l)

# Telegram
tg_out = workspace / "memory" / "telegram" / "pm2_logs" / "out.log"
if tg_out.exists():
    print("\n[Telegram Bot - out.log últimas 25 linhas]:")
    for l in tg_out.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]:
        print("  TG>", l)

print("\n" + "=" * 80)
print("FIM DA AUDITORIA DE ERROS")
print("=" * 80)
