#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero Trust & Port Exposure Auditor — AXION Enterprise
Executes Phase 1 of the Hybrid Architecture Unification Plan:
- Probes external public IPs vs private Tailnet interfaces
- Maps public attack surface across remaining VPS nodes (axion-vps, debian-2vcpu)
- Correlates with Cloudflare Tunnels and MagicDNS endpoints
- Recommends zero-trust ingress migration and firewall (UFW) rules
Generates:
- memory/infrastructure/ZERO_TRUST_PORT_AUDIT.md
- memory/infrastructure/zero_trust_audit.json
"""

import socket
import json
import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")

TARGET_HOSTS = [
    {
        "name": "primary-gateway-node",
        "public_ip": "198.51.100.1",
        "tailnet_ip": "100.64.0.1",
        "role": "Traefik Ingress Gateway & API Core",
        "probed_ports": [80, 443, 8080, 22, 5432, 6379],
        "assigned_domains": ["api.example.com", "auth.example.com", "casa.example.com", "hooks.example.com"]
    },
    {
        "name": "primary-db-node",
        "public_ip": "198.51.100.2",
        "tailnet_ip": "100.64.0.2",
        "role": "Database, Celery Tasks & Flow Engine",
        "probed_ports": [80, 443, 22, 5432, 6379, 8000],
        "assigned_domains": ["db.example.com", "agents.example.com", "tasks.example.com"]
    }
]

def probe_port(ip: str, port: int, timeout: float = 2.5) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def run_port_audit():
    print("==================================================")
    print("   AUDITORIA ZERO TRUST & SUPERFÍCIE DE ATAQUE    ")
    print("==================================================")
    
    audit_results = []
    
    for host in TARGET_HOSTS:
        hname = host["name"]
        pub_ip = host["public_ip"]
        ts_ip = host["tailnet_ip"]
        
        print(f"\n[*] Auditando {hname}:")
        print(f"    IP Público: {pub_ip} | IP Tailnet: {ts_ip}")
        
        host_audit = {
            "name": hname,
            "role": host["role"],
            "public_ip": pub_ip,
            "tailnet_ip": ts_ip,
            "public_ports": {},
            "tailnet_ports": {},
            "assigned_domains": host["assigned_domains"],
            "exposed_public_ports": []
        }
        
        for port in host["probed_ports"]:
            # Test Public IP
            is_pub_open = probe_port(pub_ip, port)
            host_audit["public_ports"][port] = "OPEN" if is_pub_open else "CLOSED/FILTERED"
            if is_pub_open:
                host_audit["exposed_public_ports"].append(port)
                
            # Test Tailnet IP
            is_ts_open = probe_port(ts_ip, port)
            host_audit["tailnet_ports"][port] = "OPEN" if is_ts_open else "CLOSED/FILTERED"
            
            pub_tag = "[OPEN]  " if is_pub_open else "[CLOSED]"
            ts_tag = "[OPEN]  " if is_ts_open else "[CLOSED]"
            print(f"    Porta {str(port).rjust(5)}: Público={pub_tag} | Tailnet={ts_tag}")
            
        audit_results.append(host_audit)
        
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_data = {
        "audited_at": now_utc,
        "hosts": audit_results,
        "recommendations": [
            "Configurar UFW em axion-vps para permitir apenas tráfego vindo da interface tailscale0 e Cloudflare IP ranges.",
            "Fechar portas administrativas (8080/Traefik Dashboard) na internet pública, tornando acessível apenas via Tailscale MagicDNS ou Cloudflare Zero Trust Access.",
            "Garantir que a porta 5432 (PostgreSQL) permaneça escutando exclusivamente em 127.0.0.1 ou na interface tailscale0.",
            "Consolidar o roteamento de saída para utilizar cloudflared com protocolo quic/http2."
        ]
    }
    
    # Salva JSON
    json_path = WORKSPACE_ROOT / "memory" / "infrastructure" / "zero_trust_audit.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Telemetria salva em: {json_path}")
    
    # Gera Markdown
    generate_markdown_report(report_data, now_local)
    return report_data

def generate_markdown_report(data, now_local):
    lines = [
        "# Auditoria de Superfície de Ataque & Arquitetura Zero Trust",
        "",
        f"> **Data/Hora**: {now_local} (UTC: {data.get('audited_at')})  ",
        "> **Classificação**: Confidencial / Engenharia de Segurança & Redes  ",
        "> **Objetivo**: Fechamento de portas públicas expostas e transição para o *AXION Unified Fabric*  ",
        "",
        "---",
        "",
        "## 1. Mapeamento da Superfície de Ataque Externa (IPs Públicos vs Tailnet)",
        "",
        "| Servidor / Nó | IP Público | Porta | Status Público | Status Tailnet (Privado) | Risco & Ação Recomendada |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |"
    ]
    
    for h in data.get("hosts", []):
        for port, status in h.get("public_ports", {}).items():
            ts_status = h.get("tailnet_ports", {}).get(str(port), h.get("tailnet_ports", {}).get(int(port), "UNKNOWN"))
            
            if status == "OPEN":
                if int(port) in [8080]:
                    risk = "🔴 **ALTO** — Traefik Dashboard exposto sem proteção WAF. Fechar via UFW e rotear por Cloudflare Access."
                elif int(port) in [80, 443]:
                    risk = "🟡 **MÉDIO** — Tráfego web direto. Migrar para Cloudflare Tunnel para fechar portas públicas."
                elif int(port) in [5432, 6379]:
                    risk = "🔴 **CRÍTICO** — Banco exposto. Rejeitar tráfego público e isolar na interface `tailscale0`."
                else:
                    risk = "⚪ Informativo / SSH"
                pub_badge = "🔴 **ABERTA**"
            else:
                pub_badge = "🟢 Fechada / Filtrada"
                risk = "🟢 **SEGURO** — Porta protegida contra varredura pública externa."
                
            ts_badge = "🟢 Aberta (Tailnet)" if ts_status == "OPEN" else "⚪ Inativa"
            lines.append(f"| `{h.get('name')}` | `{h.get('public_ip')}` | `{port}` | {pub_badge} | {ts_badge} | {risk} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Plano Canônico de Execução: Fechamento de Superfície (Zero Public Attack Surface)",
        "",
        "### 2.1 Regras de Firewall UFW Recomendadas para os VPS",
        "Executar nos servidores remotos para restringir todo tráfego de entrada não encapsulado:",
        "```bash",
        "# 1. Definir políticas padrão restritivas",
        "sudo ufw default deny incoming",
        "sudo ufw default allow outgoing",
        "",
        "# 2. Permitir loopback e rede privada WireGuard",
        "sudo ufw allow in on lo",
        "sudo ufw allow in on tailscale0",
        "",
        "# 3. Opcional: Se mantiver HTTP/S direto, permitir apenas ranges oficiais Cloudflare",
        "# curl -s https://www.cloudflare.com/ips-v4 | while read ip; do sudo ufw allow proto tcp from $ip to any port 80,443; done",
        "",
        "# 4. Ativar firewall",
        "sudo ufw --force enable",
        "```",
        "",
        "### 2.2 Roteamento de Dashboards Internos via Cloudflare Access",
        "- **Traefik Dashboard (`100.64.0.1:8080`)**: Configurar túnel `cloudflared` direcionando `admin.example.com` para `http://localhost:8080` com política de login por OTP para `@example.com`.",
        "- **Resultado**: Eliminação total de ataques automatizados de força bruta, port scanners e exploração de CVEs em portas de gerenciamento.",
        "",
        "---",
        "",
        "## Conclusão da Auditoria",
        "O ecossistema dispõe de todos os componentes necessários (Cloudflare Tunnels, MagicDNS e Tailscale Mesh) para operar com zero superfície de ataque pública direta."
    ])

    report_path = WORKSPACE_ROOT / "memory" / "infrastructure" / "ZERO_TRUST_PORT_AUDIT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[OK] Relatório Zero Trust salvo em: {report_path}")

if __name__ == "__main__":
    run_port_audit()
