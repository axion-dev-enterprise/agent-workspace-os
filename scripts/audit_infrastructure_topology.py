#!/usr/bin/env python3
"""
Auditoria Canônica de Infraestrutura, Topologia, Segurança & Pre-flight
Host Alvo: VPS Core (209.74.71.36:22022) & VPS Clientes (209.74.86.49:22022)
"""
import os
import sys
import json
import paramiko
from pathlib import Path

vault_env = Path("C:/workspace/vault/cloud/spaceship-vps/.env")
env_vars = {}
if vault_env.exists():
    for line in vault_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip("'\"")

key_file = Path("C:/workspace/vault/private/spaceship-ops/vps_ops_ed25519")
pkey = None
if key_file.exists():
    try:
        pkey = paramiko.Ed25519Key.from_private_key_file(str(key_file))
        print(f"[*] Chave SSH Ed25519 carregada com sucesso de {key_file}")
    except Exception as e:
        print(f"[!] Erro ao carregar Ed25519: {e}")

nodes = [
    {
        "name": "vps_core",
        "label": env_vars.get("SPACESHIP_VPS_CORE_LABEL", "debian-2vcpu-amd-4gb-us-jndcj"),
        "host": env_vars.get("SPACESHIP_VPS_CORE_HOST", "209.74.71.36"),
        "port": int(env_vars.get("SPACESHIP_VPS_CORE_PORT", "22022")),
        "user": env_vars.get("SPACESHIP_VPS_CORE_USER", "root"),
        "pwd": env_vars.get("SPACESHIP_VPS_CORE_PASSWORD", "Pfti49@5-VPS"),
        "tier": "critical-core"
    },
    {
        "name": "vps_clients",
        "label": env_vars.get("SPACESHIP_VPS_CLIENT_LABEL", "debian-1vcpu-amd-2gb-us-tu0v8"),
        "host": env_vars.get("SPACESHIP_VPS_CLIENT_HOST", "209.74.86.49"),
        "port": int(env_vars.get("SPACESHIP_VPS_CLIENT_PORT", "22022")),
        "user": env_vars.get("SPACESHIP_VPS_CLIENT_USER", "root"),
        "pwd": env_vars.get("SPACESHIP_VPS_CLIENT_PASSWORD", "Pfti49@5-VPS"),
        "tier": "clients"
    }
]

audit_results = {}

for node in nodes:
    print(f"\n{'='*60}")
    print(f"[*] Auditando Nó: {node['name']} ({node['host']}:{node['port']}) [{node['tier']}]")
    print(f"{'='*60}")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connected = False
    
    # Tentativa 1: Chave Ed25519
    if pkey:
        try:
            print(f"  -> Conectando via Chave Ed25519...")
            client.connect(node["host"], port=node["port"], username=node["user"], pkey=pkey, timeout=12)
            connected = True
            print("  [+] Conexão autenticada via Chave Ed25519!")
        except Exception as e:
            print(f"  [-] Falha autenticação Ed25519: {e}")
            
    # Tentativa 2: Senha
    if not connected and node.get("pwd"):
        try:
            print(f"  -> Conectando via Senha root...")
            client.connect(node["host"], port=node["port"], username=node["user"], password=node["pwd"], timeout=12)
            connected = True
            print("  [+] Conexão autenticada via Senha!")
        except Exception as e:
            print(f"  [-] Falha autenticação Senha: {e}")
            
    if not connected:
        audit_results[node["name"]] = {"error": "Falha na conexão SSH"}
        continue

    def run(cmd):
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        return out, err

    node_audit = {}

    print("  [1] Identidade, OS e Kernel...")
    out, _ = run("hostname; uname -a; cat /etc/os-release | grep PRETTY_NAME")
    node_audit["host_os"] = out

    print("  [2] Recursos (CPU, RAM, Disco)...")
    out, _ = run("uptime; free -m; df -h /")
    node_audit["resources"] = out

    print("  [3] Tailscale Status & VPN Mesh...")
    out, _ = run("which tailscale; tailscale status 2>&1; tailscale ip -4 2>&1")
    node_audit["tailscale"] = out

    print("  [4] Firewall (UFW & iptables)...")
    out, _ = run("ufw status verbose 2>&1")
    node_audit["ufw"] = out
    out, _ = run("iptables -L -n -v --line-numbers 2>&1 | head -n 40")
    node_audit["iptables"] = out

    print("  [5] Fail2ban Status & Jails Ativas...")
    out, _ = run("which fail2ban-client; fail2ban-client status 2>&1; fail2ban-client status sshd 2>&1")
    node_audit["fail2ban"] = out

    print("  [6] Portas e Escutas de Rede (ss -tulpn)...")
    out, _ = run("ss -tulpn")
    node_audit["network_listeners"] = out

    print("  [7] Containers Docker e Imagens...")
    out, _ = run("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    node_audit["docker"] = out

    print("  [8] Reverse Proxy Nginx & Virtual Hosts...")
    out, _ = run("nginx -v 2>&1; nginx -t 2>&1; systemctl is-active nginx")
    node_audit["nginx"] = out
    out, _ = run("ls -la /etc/nginx/sites-enabled/ 2>&1; cat /etc/nginx/sites-enabled/* 2>&1")
    node_audit["nginx_configs"] = out

    print("  [9] Rotinas Agendadas (Crontab & Timers)...")
    out, _ = run("crontab -l 2>&1; ls -la /etc/cron.* 2>&1; systemctl list-timers --no-pager | head -n 25")
    node_audit["cron_and_timers"] = out

    print("  [10] Hardening SSH (sshd_config)...")
    out, _ = run("grep -E '^(Port|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null")
    node_audit["ssh_hardening"] = out

    client.close()
    audit_results[node["name"]] = node_audit

out_file = Path("C:/workspace/reports/infrastructure_topology_audit.json")
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(audit_results, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n[+] Auditoria completa de todos os nós finalizada com sucesso! Relatório gerado em: {out_file}")
