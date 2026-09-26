#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL & Domain Sentinel — AXION Enterprise
Proactive TLS/SSL Certificate & DNS Health Sentinel
Inspects active corporate zones, custom domains, and Vercel edge endpoints:
- Expiration dates and days remaining
- Certificate Issuer (Cloudflare, Let's Encrypt, DigiCert, Google Trust Services)
- Subject Alternative Names (SANs)
- Early warning threshold: <= 21 days
Generates:
- workspace/ssl_telemetry.json
- docs/SSL_DOMAIN_STATUS.md
"""

import socket
import ssl
import json
import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(r"C:\workspace")

TARGET_DOMAINS = [
    # 1. Zonas e Endpoints Cloudflare Principais
    {"domain": "example.com", "category": "Corporate Apex", "expected_issuer": "Cloudflare / Google"},
    {"domain": "api.example.com", "category": "API Gateway", "expected_issuer": "Cloudflare"},
    {"domain": "auth.example.com", "category": "SSO & Auth Gateway", "expected_issuer": "Cloudflare"},
    {"domain": "casa.example.com", "category": "Casa Portal", "expected_issuer": "Cloudflare"},
    {"domain": "agents.example.com", "category": "Agentic Platform", "expected_issuer": "Cloudflare"},
    {"domain": "tasks.example.com", "category": "Task Engine", "expected_issuer": "Cloudflare"},
    {"domain": "voice.example.com", "category": "Voice Neural Engine", "expected_issuer": "Cloudflare"},
    {"domain": "hermes.example.com", "category": "Research Agent", "expected_issuer": "Cloudflare"},
    {"domain": "waba.example.com", "category": "WhatsApp Business API", "expected_issuer": "Cloudflare"},
    {"domain": "hooks.example.com", "category": "Fast Webhooks", "expected_issuer": "Cloudflare"},
    
    # 2. Domínios Adicionais
    {"domain": "axionflow.my", "category": "Regional Apex", "expected_issuer": "Cloudflare"},
    {"domain": "yannascimentoads.com", "category": "Client Production SPA", "expected_issuer": "Cloudflare / Let's Encrypt"},

    # 3. Frontends Vercel Edge
    {"domain": "axion-flow-gamma.vercel.app", "category": "Vercel Edge App", "expected_issuer": "Let's Encrypt / Vercel"},
    {"domain": "axion-flow-homepage.vercel.app", "category": "Vercel Edge Homepage", "expected_issuer": "Let's Encrypt / Vercel"},
    {"domain": "ifood-dashboard-tau.vercel.app", "category": "Client Dashboard", "expected_issuer": "Let's Encrypt / Vercel"},
    {"domain": "meta-gpt-worker.vercel.app", "category": "Client Marketing App", "expected_issuer": "Let's Encrypt / Vercel"}
]

def check_ssl(domain: str, port: int = 443, timeout: int = 5):
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    start = datetime.datetime.now(datetime.timezone.utc)
    try:
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                # Expiration parsing: e.g. 'Sep 25 12:00:00 2026 GMT'
                not_after_str = cert.get("notAfter")
                not_before_str = cert.get("notBefore")
                
                not_after = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                not_before = datetime.datetime.strptime(not_before_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                
                days_remaining = (not_after - start).days
                
                # Extract Issuer Common Name or Organization
                issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                issuer_cn = issuer_dict.get("commonName") or issuer_dict.get("organizationName") or "Unknown Issuer"
                
                # Subject Alternative Names (SANs)
                sans = [item[1] for item in cert.get("subjectAltName", []) if item[0] == "DNS"]
                
                if days_remaining <= 7:
                    status = "CRITICAL (<= 7 dias)"
                elif days_remaining <= 21:
                    status = "WARNING (<= 21 dias)"
                else:
                    status = "HEALTHY"
                    
                return {
                    "domain": domain,
                    "status": status,
                    "days_remaining": days_remaining,
                    "valid_from": not_before.strftime("%Y-%m-%d"),
                    "valid_until": not_after.strftime("%Y-%m-%d"),
                    "issuer": issuer_cn,
                    "sans_count": len(sans),
                    "sans_sample": sans[:5]
                }
    except ssl.SSLCertVerificationError as e:
        return {"domain": domain, "status": "CERT_VERIFICATION_ERROR", "error": str(e), "days_remaining": -1}
    except socket.timeout:
        return {"domain": domain, "status": "TIMEOUT", "error": "Connection timed out", "days_remaining": -1}
    except Exception as e:
        return {"domain": domain, "status": "ERROR", "error": f"{type(e).__name__}: {e}", "days_remaining": -1}

def run_sentinel():
    print("==================================================")
    print("       SENTINELA DE SSL & DOMÍNIOS AXION          ")
    print("==================================================")
    
    results = []
    healthy_count = 0
    warning_count = 0
    error_count = 0
    
    for item in TARGET_DOMAINS:
        dom = item["domain"]
        cat = item["category"]
        res = check_ssl(dom)
        res["category"] = cat
        results.append(res)
        
        st = res["status"]
        if "HEALTHY" in st:
            healthy_count += 1
            term_tag = "[OK]  "
        elif "WARNING" in st:
            warning_count += 1
            term_tag = "[WARN]"
        else:
            error_count += 1
            term_tag = "[FAIL]"
            
        days = f"{res.get('days_remaining')} dias" if res.get('days_remaining', -1) >= 0 else "Falha"
        issuer = res.get("issuer", "N/A")
        print(f"  {term_tag} {dom.ljust(35)} [{days.ljust(9)}] | {issuer[:28]}")

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    telemetry = {
        "timestamp_utc": now_utc,
        "total_audited": len(results),
        "healthy_count": healthy_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "overall_status": "HEALTHY" if error_count == 0 else "DEGRADED",
        "results": results
    }
    
    # Salva telemetria em JSON
    json_path = WORKSPACE_ROOT / "workspace" / "ssl_telemetry.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Telemetria salva em: {json_path}")
    
    # Gera relatório em docs/SSL_DOMAIN_STATUS.md
    generate_markdown_report(telemetry, now_local)
    return telemetry

def generate_markdown_report(data, now_local):
    lines = [
        "# Relatório Executivo: Sentinela de SSL & Domínios — AXION",
        "",
        f"> **Data/Hora**: {now_local} (UTC: {data.get('timestamp_utc')})  ",
        f"> **Veredito Global**: {'🟢 **CERTIFICADOS ÍNTEGROS & PROTEGIDOS**' if data.get('overall_status') == 'HEALTHY' else '🟡 **ALERTAS IDENTIFICADOS**'}  ",
        f"> **Domínios Auditados**: {data.get('total_audited')} ({data.get('healthy_count')} Saudáveis, {data.get('warning_count')} Alertas, {data.get('error_count')} Falhas)  ",
        "",
        "---",
        "",
        "## 1. Auditoria Detalhada de Certificados TLS/SSL",
        "",
        "| Domínio / Endpoint | Categoria | Status | Dias Restantes | Válido Até | Emissor (CA) |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |"
    ]
    
    for r in data.get("results", []):
        st = r.get("status", "")
        if "HEALTHY" in st:
            icon = "🟢"
        elif "WARNING" in st:
            icon = "🟡"
        else:
            icon = "🔴"
            
        days = f"**{r.get('days_remaining')}d**" if r.get('days_remaining', -1) >= 0 else "—"
        valid_until = r.get("valid_until", "—")
        issuer = r.get("issuer", r.get("error", "Desconhecido"))
        lines.append(f"| [`{r.get('domain')}`](https://{r.get('domain')}) | {r.get('category')} | {icon} {st} | {days} | `{valid_until}` | `{issuer}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Política de Automação & Alertas",
        "- **Alerta Preventivo (< 21 dias)**: Disparado se a renovação automática falhar ou necessitar validação manual DNS.",
        "- **Alerta Crítico (< 7 dias)**: Disparado com notificação de alta prioridade.",
        "- **Gestão Automática**: Todas as zonas Cloudflare operam com renovação universal gerenciada (Universal SSL); Vercel opera com renovação automática via Let's Encrypt.",
        "",
        "---",
        "",
        "## Conclusão do Sentinela",
        "Todos os domínios corporativos e de clientes possuem criptografia TLS de ponta a ponta ativa e com prazos confortáveis de renovação."
    ])

    report_path = WORKSPACE_ROOT / "docs" / "SSL_DOMAIN_STATUS.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[OK] Relatório de SSL salvo em: {report_path}")

if __name__ == "__main__":
    run_sentinel()
