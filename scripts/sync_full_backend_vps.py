#!/usr/bin/env python3
"""
Sincronização Completa e Recursiva de Backend do AXION Flow na VPS.
Garante que todos os módulos de services/ e config/ estejam presentes e atualizados.
"""
import os
import sys
import paramiko
from pathlib import Path

vault_env = Path("C:/workspace/vault/cloud/spaceship-vps/.env")
env_vars = {}
if vault_env.exists():
    for line in vault_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env_vars[k.strip()] = v.strip().strip("'\"")

host = env_vars.get("SPESHIP_VPS_CORE_HOST", "209.74.71.36")
port = int(env_vars.get("SPACESHIP_VPS_CORE_PORT", "22022"))
user = env_vars.get("SPACESHIP_VPS_CORE_USER", "root")
pwd = env_vars.get("SPACESHIP_VPS_CORE_PASSWORD", "Pfti49@5-VPS")

print(f"[*] Conectando à VPS {host}:{port}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=pwd, timeout=20)

sftp = client.open_sftp()

def ensure_remote_dir(remote_path):
    dirs = []
    current = remote_path
    while current not in ('/', ''):
        dirs.append(current)
        current = os.path.dirname(current)
    for d in reversed(dirs):
        try:
            sftp.mkdir(d)
        except Exception:
            pass

def upload_dir_recursive(local_dir, remote_dir):
    ensure_remote_dir(remote_dir)
    for root, dirs, files in os.walk(local_dir):
        rel = os.path.relpath(root, local_dir)
        target_root = remote_dir if rel == '.' else os.path.join(remote_dir, rel).replace('\\', '/')
        ensure_remote_dir(target_root)
        for f in files:
            if f.endswith(('.js', '.json', '.env', '.md')):
                local_f = os.path.join(root, f)
                remote_f = os.path.join(target_root, f).replace('\\', '/')
                print(f"  -> Uploading: {remote_f}")
                sftp.put(local_f, remote_f)

print("[*] Sincronizando pasta services/...")
upload_dir_recursive("C:/workspace/services/axion-flow/services", "/opt/axion/services/flow/services")

print("[*] Sincronizando pasta config/...")
upload_dir_recursive("C:/workspace/services/axion-flow/config", "/opt/axion/services/flow/config")

print("[*] Enviando server.js e FlowDashboard.jsx...")
sftp.put("C:/workspace/services/axion-flow/server.js", "/opt/axion/services/flow/server.js")
sftp.put("C:/workspace/services/axion-flow/src/pages/FlowDashboard.jsx", "/opt/axion/services/flow/src/pages/FlowDashboard.jsx")

sftp.close()

print("[*] Copiando arquivos atualizados para dentro do container axion-flow-core...")
cmd = (
    'rm -f /opt/axion/services/flow/data/.db-mutation.lock && '
    'docker cp /opt/axion/services/flow/services/. axion-flow-core:/app/services/ && '
    'docker cp /opt/axion/services/flow/config/. axion-flow-core:/app/config/ && '
    'docker cp /opt/axion/services/flow/server.js axion-flow-core:/app/server.js && '
    'docker restart axion-flow-core'
)
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
sys.stdout.buffer.write(f"OUTPUT:\n{out}\n".encode('utf-8', errors='replace'))
if err:
    sys.stdout.buffer.write(f"ERRORS:\n{err}\n".encode('utf-8', errors='replace'))

# Esperar 3 segundos e checar logs
import time
time.sleep(3)
stdin, stdout, stderr = client.exec_command('docker logs --tail 20 axion-flow-core')
logs = stdout.read().decode('utf-8', errors='replace')
sys.stdout.buffer.write(f"\nLOGS DO CONTAINER APÓS RESTART:\n{logs}\n".encode('utf-8', errors='replace'))

client.close()
print("[+] Sincronização e reinício concluídos com sucesso!")
