#!/usr/bin/env python3
"""
Provisionamento e Hardening do Fail2ban nos Nós VPS Core e Clientes
Configura proteção na porta não-padrão 22022 com ignoreip defensivo.
"""
import sys
import json
import paramiko
from pathlib import Path

key_file = Path("C:/workspace/vault/private/spaceship-ops/vps_ops_ed25519")
if not key_file.exists():
    print(f"[-] Chave privada não encontrada em {key_file}")
    sys.exit(1)

pkey = paramiko.Ed25519Key.from_private_key_file(str(key_file))

nodes = [
    {"name": "vps_core", "host": "209.74.71.36", "port": 22022},
    {"name": "vps_clients", "host": "209.74.86.49", "port": 22022}
]

JAIL_LOCAL_CONFIG = """# ==============================================================================
# AXION ENTERPRISE FAIL2BAN HARDENING CONFIGURATION
# Porta SSH: 22022 | Protecao contra Scanners e Forca Bruta
# ==============================================================================
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
banaction = ufw
banaction_allports = ufw
backend = systemd
ignoreip = 127.0.0.1/8 ::1 100.64.0.0/10 189.62.150.126

[sshd]
enabled  = true
port     = 22022
mode     = aggressive
maxretry = 3
findtime = 10m
bantime  = 2h
"""

for node in nodes:
    print(f"\n{'='*60}")
    print(f"[*] Provisionando Fail2ban no nó {node['name']} ({node['host']}:{node['port']})...")
    print(f"{'='*60}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node["host"], port=node["port"], username="root", pkey=pkey, timeout=15)
        print("  [+] Conexão SSH autenticada com sucesso!")
    except Exception as e:
        print(f"  [-] Falha na conexão com {node['name']}: {e}")
        continue

    def run_cmd(cmd):
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        return out, err

    print("  [1] Instalando pacote fail2ban via apt...")
    out, err = run_cmd("DEBIAN_FRONTEND=noninteractive apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fail2ban")
    print("  -> Instalação finalizada.")

    print("  [2] Gravando /etc/fail2ban/jail.local...")
    sftp = client.open_sftp()
    with sftp.file("/etc/fail2ban/jail.local", "w") as f:
        f.write(JAIL_LOCAL_CONFIG)
    sftp.close()
    print("  -> Configuração jail.local gravada com sucesso.")

    print("  [3] Habilitando e reiniciando o serviço fail2ban...")
    out, err = run_cmd("systemctl enable fail2ban && systemctl restart fail2ban")
    
    print("  [4] Verificando status do serviço e das jails...")
    out_status, _ = run_cmd("systemctl is-active fail2ban; fail2ban-client status; fail2ban-client status sshd")
    print(f"  -> Status:\n{out_status}")

    client.close()

print("\n[+] Hardening do Fail2ban finalizado em todos os nós VPS!")
