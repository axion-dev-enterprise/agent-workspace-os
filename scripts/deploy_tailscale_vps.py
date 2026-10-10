#!/usr/bin/env python3
"""
Instalação e Ingresso dos Nós VPS na Tailnet Mesh (Tailscale WireGuard)
Instala o Tailscale oficial no Debian 13 e gera URLs de autorização.
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
    {"name": "vps_core", "host": "209.74.71.36", "port": 22022, "hostname": "vps-node-01-core"},
    {"name": "vps_clients", "host": "209.74.86.49", "port": 22022, "hostname": "vps-node-01-clients"}
]

auth_urls = {}

for node in nodes:
    print(f"\n{'='*60}")
    print(f"[*] Instalando Tailscale no nó {node['name']} ({node['host']}:{node['port']})...")
    print(f"{'='*60}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(node["host"], port=node["port"], username="root", pkey=pkey, timeout=15)
        print("  [+] Conexão SSH autenticada com sucesso!")
    except Exception as e:
        print(f"  [-] Falha na conexão com {node['name']}: {e}")
        continue

    def run_cmd(cmd, timeout=120):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        return out, err

    print("  [1] Executando instalador oficial do Tailscale...")
    out_inst, err_inst = run_cmd("curl -fsSL https://tailscale.com/install.sh | sh")
    print("  -> Instalação finalizada.")

    print("  [2] Habilitando e iniciando daemon tailscaled...")
    run_cmd("systemctl enable --now tailscaled")

    print(f"  [3] Executando tailscale up --ssh --hostname={node['hostname']}...")
    # Executa comando para capturar a auth URL
    cmd_up = f"tailscale up --ssh --hostname={node['hostname']} --accept-routes=false --timeout=10s 2>&1 || true"
    out_up, _ = run_cmd(cmd_up, timeout=20)
    
    url = None
    for line in out_up.splitlines():
        if "https://login.tailscale.com/a/" in line:
            parts = line.split("https://login.tailscale.com/a/")
            url = "https://login.tailscale.com/a/" + parts[1].strip().split()[0]
            break
            
    print(f"  -> Resultado tailscale up:\n{out_up}")
    if url:
        auth_urls[node["name"]] = {"hostname": node["hostname"], "url": url}
        print(f"  [!] URL DE AUTORIZAÇÃO DO NÓ: {url}")
    else:
        # Verifica se já está logado
        out_stat, _ = run_cmd("tailscale status 2>&1")
        print(f"  -> Tailscale Status: {out_stat}")

    client.close()

with open("C:/workspace/reports/tailscale_auth_urls.json", "w", encoding="utf-8") as f:
    json.dump(auth_urls, f, indent=2)

print("\n" + "="*60)
print("[+] Processo de provisionamento do Tailscale finalizado!")
for k, v in auth_urls.items():
    print(f" -> Nó {v['hostname']}: {v['url']}")
print("="*60)
