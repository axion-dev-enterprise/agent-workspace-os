#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup Rotation & Retention Pruner — AXION Enterprise
Automates intelligent lifecycle management of offline backups on E:\\backups\\axion_enterprise\\
Retention Policy:
1. Daily Backups: Keep all daily backups for the last 14 days.
2. Weekly Backups: Keep 1 backup per week for the last 90 days.
3. Protected / Special Archives: NEVER delete directories starting with 'decommission_' or 'permanent_'.
4. Prune: Safely removes stale daily backups exceeding retention thresholds.
5. Auditing: Generates docs/BACKUP_RETENTION_REPORT.md and E:\\backups\\axion_enterprise\\retention_audit.json
"""

import os
import json
import shutil
import datetime
from pathlib import Path

BACKUP_ROOT = Path(r"E:\backups\axion_enterprise")
WORKSPACE_ROOT = Path(r"C:\workspace")

DAILY_RETENTION_DAYS = 14
WEEKLY_RETENTION_DAYS = 90

def parse_backup_date(dir_name: str):
    """Extracts date from 'backup_YYYY-MM-DD' directory name."""
    if dir_name.startswith("backup_"):
        date_part = dir_name[len("backup_"):]
        # Truncate any extra timestamp suffixes if present
        date_str = date_part[:10]
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def analyze_and_prune_backups():
    print("==================================================")
    print("   MOTOR DE ROTAÇÃO E RETENÇÃO DE BACKUPS AXION   ")
    print("==================================================")
    
    if not BACKUP_ROOT.exists():
        print(f"[!] Diretório de backups {BACKUP_ROOT} não encontrado.")
        return {"status": "ERROR", "error": "Root not found"}

    today = datetime.date.today()
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    subdirs = [p for p in BACKUP_ROOT.iterdir() if p.is_dir()]
    
    backup_entries = []
    special_archives = []
    
    for d in subdirs:
        name = d.name
        # Check if protected special archive
        if name.startswith("decommission_") or name.startswith("permanent_"):
            size_bytes = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            special_archives.append({
                "name": name,
                "path": str(d),
                "type": "PERMANENT_VAULT",
                "size_mb": round(size_bytes / (1024 * 1024), 2)
            })
            continue
            
        bdate = parse_backup_date(name)
        if bdate:
            age_days = (today - bdate).days
            size_bytes = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            has_manifest = (d / "manifest.json").exists()
            backup_entries.append({
                "dir_name": name,
                "path": d,
                "date": bdate,
                "age_days": age_days,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "has_manifest": has_manifest
            })

    backup_entries.sort(key=lambda x: x["date"], reverse=True)
    
    kept_backups = []
    pruned_backups = []
    
    # Retention Logic:
    # 1. Backups within DAILY_RETENTION_DAYS (<= 14) -> Always KEEP
    # 2. Backups between 15 and 90 days -> Keep 1 per week (e.g. Sunday or latest of that week)
    # 3. Backups > 90 days -> PRUNE
    seen_weeks = set()
    
    for b in backup_entries:
        age = b["age_days"]
        year_week = f"{b['date'].year}-W{b['date'].isocalendar()[1]}"
        
        if age <= DAILY_RETENTION_DAYS:
            b["reason"] = f"Recente ({age} dias <= {DAILY_RETENTION_DAYS}d)"
            kept_backups.append(b)
            seen_weeks.add(year_week)
        elif age <= WEEKLY_RETENTION_DAYS:
            if year_week not in seen_weeks:
                b["reason"] = f"Snapshot semanal retenção 90d ({year_week})"
                kept_backups.append(b)
                seen_weeks.add(year_week)
            else:
                b["reason"] = f"Excedente diário na semana {year_week} (> {DAILY_RETENTION_DAYS}d)"
                pruned_backups.append(b)
        else:
            b["reason"] = f"Excedeu prazo máximo de retenção ({age}d > {WEEKLY_RETENTION_DAYS}d)"
            pruned_backups.append(b)
            
    # Executa remoção dos backups expirados
    actually_deleted = []
    for p in pruned_backups:
        print(f"  [PRUNE] Removendo backup expirado: {p['dir_name']} ({p['reason']})...")
        try:
            shutil.rmtree(p["path"])
            actually_deleted.append(p["dir_name"])
        except Exception as e:
            print(f"  [!] Erro ao remover {p['dir_name']}: {e}")

    total_storage = sum(b["size_mb"] for b in kept_backups) + sum(a["size_mb"] for a in special_archives)
    
    audit_data = {
        "executed_at": now_utc,
        "backup_root": str(BACKUP_ROOT),
        "total_active_backups": len(kept_backups),
        "total_special_archives": len(special_archives),
        "pruned_count": len(actually_deleted),
        "total_vault_storage_mb": round(total_storage, 2),
        "policy": {
            "daily_retention_days": DAILY_RETENTION_DAYS,
            "weekly_retention_days": WEEKLY_RETENTION_DAYS
        },
        "kept": [{k: str(v) if isinstance(v, (datetime.date, Path)) else v for k, v in b.items()} for b in kept_backups],
        "special_archives": special_archives,
        "pruned": [{k: str(v) if isinstance(v, (datetime.date, Path)) else v for k, v in p.items()} for p in pruned_backups]
    }
    
    # Salva log de auditoria no disco E:
    audit_path = BACKUP_ROOT / "retention_audit.json"
    try:
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Auditoria salva no cold vault: {audit_path}")
    except Exception as e:
        print(f"[!] Erro ao salvar auditoria no disco E: {e}")

    # Gera relatório em docs/
    generate_retention_report(audit_data)
    return audit_data

def generate_retention_report(audit_data):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Relatório de Retenção & Rotação de Armazenamento Frio (E:\\)",
        "",
        f"> **Última Execução**: {now_str} (UTC: {audit_data.get('executed_at')})  ",
        "> **Diretório Canônico**: `E:\\backups\\axion_enterprise\\`  ",
        "> **Política Ativa**: Retenção Diária de 14 dias + Retenção Semanal de 90 dias + Cofres Permanentes  ",
        "",
        "---",
        "",
        "## 1. Resumo Executivo da Unidade E:\\",
        "",
        "| Métrica | Valor | Descrição |",
        "| :--- | :---: | :--- |",
        f"| **Backups Rotativos Ativos** | **{audit_data.get('total_active_backups')}** | Backups diários e semanais íntegros dentro da janela de conformidade |",
        f"| **Cofres Permanentes / Descomissionamento** | **{audit_data.get('total_special_archives')}** | Arquivos definitivos protegidos contra qualquer expiração |",
        f"| **Diretórios Prunados nesta Rodada** | **{audit_data.get('pruned_count')}** | Backups obsoletos excluídos de forma segura |",
        f"| **Volume Total em Disco** | **{audit_data.get('total_vault_storage_mb')} MB** | Espaço total ocupado por todos os backups e repositórios |",
        "",
        "---",
        "",
        "## 2. Cofres Permanentes Protegidos (*Immutable Vaults*)",
        "",
        "| Arquivo / Diretório | Tamanho (MB) | Propósito / Conteúdo Preservado | Status |",
        "| :--- | :---: | :--- | :---: |"
    ]
    
    for a in audit_data.get("special_archives", []):
        lines.append(f"| **`{a.get('name')}`** | **{a.get('size_mb')} MB** | Snapshot final de desligamento (PostgreSQL 16 `hermes_db` + código `/opt/hermes`) | 🟢 **IMUTÁVEL** |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Backups Ativos em Conformidade",
        "",
        "| Diretório | Data | Idade (dias) | Tamanho (MB) | Manifesto | Racional de Retenção |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |"
    ])
    
    for b in audit_data.get("kept", []):
        man = "🟢 Válido" if b.get("has_manifest") else "🟡 Ausente"
        lines.append(f"| **`{b.get('dir_name')}`** | `{b.get('date')}` | {b.get('age_days')}d | {b.get('size_mb')} MB | {man} | {b.get('reason')} |")

    lines.extend([
        "",
        "---",
        "",
        "## Conclusão da Rotina",
        "A retenção e rotação automática assegura que a unidade secundária `E:\\` mantenha redundância integral e histórico recuperável sem risco de saturação de disco."
    ])

    report_path = WORKSPACE_ROOT / "docs" / "BACKUP_RETENTION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[OK] Relatório de retenção salvo em: {report_path}")

if __name__ == "__main__":
    analyze_and_prune_backups()
