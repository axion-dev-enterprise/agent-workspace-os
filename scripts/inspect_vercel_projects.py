#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Project & Stack Inspector — AXION Enterprise
Probes each production Vercel deployment URL to analyze framework, headers, and UI stack.
"""

import urllib.request
import re
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

PROJECTS = [
    {"name": "landing-page-teste-w-solucoes", "url": "https://landing-page-teste-w-solucoes.vercel.app"},
    {"name": "landing-page-teste", "url": "https://landing-page-teste-woad.vercel.app"},
    {"name": "ifood-dashboard", "url": "https://ifood-dashboard-tau.vercel.app"},
    {"name": "meta-gpt-worker", "url": "https://meta-gpt-worker.vercel.app"},
    {"name": "proxion-hub", "url": "https://proxionmidia.com"},
    {"name": "axion-vps-api-contingencia", "url": "https://axion-vps-api-contingencia.vercel.app"},
    {"name": "axion-flow", "url": "https://axion-flow-gamma.vercel.app"},
    {"name": "axion-flow-homepage", "url": "https://axion-flow-homepage.vercel.app"},
    {"name": "axion-conferencia-pecas", "url": "https://axion-conferencia-pecas.vercel.app"},
    {"name": "growth-accelerator-main", "url": "https://yannascimentoads.com"},
    {"name": "rosireis-atelier", "url": "https://rosireis.com.br"},
    {"name": "vercel-ai-gateway-demo", "url": "https://vercel-ai-gateway-demo-axion777.vercel.app"}
]

def analyze_project(p):
    url = p["url"]
    print(f"[*] Analisando {p['name']} ({url})...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            status = resp.status
            headers = dict(resp.headers)
            html = resp.read().decode("utf-8", "ignore")
            
            # Framework detection
            framework = "HTML / Estático"
            if "/_next/" in html or "x-nextjs-matched-path" in headers or "__NEXT_DATA__" in html:
                framework = "Next.js (React)"
            elif "/assets/" in html and "vite" in html.lower():
                framework = "Vite / React"
            elif "astro" in html.lower():
                framework = "Astro"
            elif "svelte" in html.lower():
                framework = "SvelteKit"
            elif "remix" in html.lower():
                framework = "Remix"
            elif "tailwind" in html.lower() or "tw-" in html:
                framework = "Tailwind CSS / SPA"

            title_m = re.search(r"<title>(.*?)</title>", html, re.I)
            title = title_m.group(1).strip() if title_m else "-"
            
            generator_m = re.search(r'<meta\s+name=["\']generator["\']\s+content=["\'](.*?)["\']', html, re.I)
            if generator_m:
                framework = f"{framework} ({generator_m.group(1)})"

            return {
                "name": p["name"],
                "url": url,
                "status": status,
                "framework": framework,
                "title": title,
                "server": headers.get("Server", "Vercel"),
                "node_version": "24.x"
            }
    except Exception as e:
        return {
            "name": p["name"],
            "url": url,
            "status": "Erro/Inativo",
            "framework": "Desconhecido",
            "title": str(e),
            "server": "Vercel",
            "node_version": "24.x"
        }

def main():
    results = []
    for p in PROJECTS:
        res = analyze_project(p)
        results.append(res)
        print(f"  -> {res['status']} | {res['framework']} | {res['title'][:40]}")
        
    with open(r"C:\workspace\workspace\vercel_stack_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n[OK] Salvo em workspace/vercel_stack_analysis.json")

if __name__ == "__main__":
    main()
