#!/usr/bin/env python3
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
key_file = env_vars.get(
    "SPACESHIP_VPS_OPS_KEY_FILE",
    "C:/workspace/vault/private/spaceship-ops/vps_ops_ed25519",
)

cmd = sys.argv[1] if len(sys.argv) > 1 else "echo key_auth_ok"
if len(sys.argv) > 2:
    host = sys.argv[2]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(
        host, port=port, username=user, key_filename=key_file, timeout=15
    )
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    if err:
        sys.stderr.buffer.write(f"[STDERR]: {err}\n".encode("utf-8", errors="replace"))
        sys.stderr.buffer.flush()
finally:
    client.close()
