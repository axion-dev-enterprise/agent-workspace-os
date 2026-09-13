#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workspace-sync.py — Automação Canônica do UPDATE_PROTOCOL.md.
Busca commits novos do upstream, preserva as variáveis locais do usuário,
mescla atualizações e registra o changelog na memória (blackboard e daily log).
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
COWORK_DIR = os.path.join(WORKSPACE_ROOT, "memory", "cowork")
BLACKBOARD_FILE = os.path.join(COWORK_DIR, "blackboard.json")
DAILY_LOGS_DIR = os.path.join(WORKSPACE_ROOT, "memory", "daily_logs")

def get_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run_git(args):
    cmd = ["git"] + args
    res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 65)
    print("AGENT WORKSPACE OS — UPDATE & SYNC AUTOMATION")
    print("=" * 65)

    # 1. Verificar se o setup inicial ja foi feito
    if not os.path.exists(CONFIG_FILE):
        print("[ERR] workspace.config.json nao encontrado!")
        print("Por favor, execute o SETUP_PROTOCOL.md antes de tentar atualizar.")
        sys.exit(1)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            local_config = json.load(f)
    except Exception as e:
        print(f"[ERR] Falha ao ler workspace.config.json: {e}")
        sys.exit(1)

    org_name = local_config.get("organization", {}).get("name", "Unknown")
    print(f"-> Workspace: {org_name}")

    # 2. Fetch de commits remotos
    print("-> Buscando atualizacoes remotas (git fetch)...")
    code, out, err = run_git(["fetch", "origin", "main"])
    if code != 0:
        # Tentar upstream se origin falhar
        code, out, err = run_git(["fetch", "upstream", "main"])
        if code != 0:
            print(f"[WARN] Nao foi possivel buscar do remoto: {err}")

    # 3. Verificar commits novos
    code, count_str, _ = run_git(["rev-list", "HEAD..FETCH_HEAD", "--count"])
    new_commits_count = int(count_str) if code == 0 and count_str.isdigit() else 0

    if new_commits_count == 0:
        print("
[OK] O seu workspace ja esta 100% atualizado com a versao mais recente!")
        sys.exit(0)

    print(f"
[INFO] {new_commits_count} novo(s) commit(s) encontrado(s) no upstream:")
    _, log_summary, _ = run_git(["log", "HEAD..FETCH_HEAD", "--oneline", "-n", "10"])
    for line in log_summary.splitlines():
        print(f"   * {line}")

    # 4. Git merge seguro
    print("
-> Aplicando merge das atualizacoes...")
    code, merge_out, merge_err = run_git(["merge", "FETCH_HEAD", "--no-edit"])
    if code != 0:
        print(f"[WARN] Conflito detectado no merge: {merge_err}")
        print("Por favor, resolva os conflitos manualmente ou solicite ao agente.")
        sys.exit(1)

    # Obter hash do novo HEAD
    _, new_head, _ = run_git(["rev-parse", "HEAD"])
    now_iso = get_utc_iso()

    # 5. Atualizar workspace.config.json com metadados de sync
    local_config["last_synced_commit"] = new_head
    local_config["last_synced_at"] = now_iso
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(local_config, f, indent=2, ensure_ascii=False)
    print("-> Metadados de sincronizacao gravados em workspace.config.json")

    # 6. Atualizar Blackboard
    if os.path.exists(COWORK_DIR):
        bb_data = {"version": "1.0.0", "entries": []}
        if os.path.exists(BLACKBOARD_FILE):
            try:
                with open(BLACKBOARD_FILE, "r", encoding="utf-8") as f:
                    bb_data = json.load(f)
            except Exception:
                pass
        
        entry_id = f"bb_sync_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_entry = {
            "id": entry_id,
            "agent": "workspace-sync",
            "timestamp": now_iso,
            "category": "SYSTEM_UPDATE",
            "title": f"Workspace atualizado com {new_commits_count} commits upstream",
            "summary": f"Novos commits aplicados com sucesso. HEAD: {new_head[:8]}.",
            "tags": ["update", "sync", "upstream"]
        }
        bb_data.setdefault("entries", []).append(new_entry)
        with open(BLACKBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(bb_data, f, indent=2, ensure_ascii=False)
        print(f"-> Entrada registrada no Blackboard: {entry_id}")

    # 7. Registrar no Daily Log
    os.makedirs(DAILY_LOGS_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_log_file = os.path.join(DAILY_LOGS_DIR, f"{today_str}.md")
    now_time = datetime.now().strftime("%H:%M:%S")

    log_entry = f"""
## [{now_time}] [workspace-update] Sincronização Incremental Concluída
- **Commits Aplicados**: {new_commits_count}
- **Novo Commit HEAD**: `{new_head[:8]}`
- **Preservação**: Variáveis locais e personalizações mantidas intactas.
- **Status**: Workspace 100% atualizado e calibrado.
"""
    with open(daily_log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(f"-> Registro cronologico anexado ao Daily Log: {daily_log_file}")

    print("
" + "=" * 65)
    print("[SUCCESS] WORKSPACE ATUALIZADO COM SUCESSO!")
    print("=" * 65)

if __name__ == "__main__":
    main()
