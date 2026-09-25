#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request
import re
import ssl
import json
import socket

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def probe_http(url):
    print(f"\n--- Probing {url} ---")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
            headers = dict(resp.headers)
            html = resp.read().decode("utf-8", "ignore")
            title_m = re.search(r"<title>(.*?)</title>", html, re.I)
            title = title_m.group(1).strip() if title_m else "Sem título"
            server = headers.get("Server", headers.get("server", "Desconhecido"))
            print(f"Status: {resp.status} | Server: {server} | Título: {title}")
            headings = [h.strip() for h in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.I)[:5]]
            if headings:
                print(f"Headings: {headings}")
            return {"url": url, "status": resp.status, "server": server, "title": title, "headers": headers}
    except Exception as e:
        print(f"Erro em {url}: {e}")
        return {"url": url, "error": str(e)}

def test_ssh_banner(ip, port=22):
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((ip, port))
        banner = s.recv(1024).decode("utf-8", "ignore").strip()
        s.close()
        print(f"SSH Banner ({ip}:{port}): {banner}")
        return banner
    except Exception as e:
        return None

if __name__ == "__main__":
    print("=== Mapeando Serviços Web na Tailnet ===")
    probe_http("http://100.81.231.111")
    probe_http("http://100.95.86.83:8080")
    probe_http("http://100.73.36.87")
    
    print("\n=== Testando Banners SSH ===")
    test_ssh_banner("100.81.231.111", 22)
    test_ssh_banner("100.95.86.83", 22)
    test_ssh_banner("100.73.36.87", 22)
