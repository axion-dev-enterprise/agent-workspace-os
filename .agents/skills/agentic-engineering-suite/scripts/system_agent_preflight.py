#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
system_agent_preflight.py — Hardware, Runtimes and Agent Environment Preflight Auditor
Part of agentic-engineering-suite skill — AXION Enterprise
Zero external dependencies: Runs exclusively on Python 3 standard library.
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_cmd(cmd: List[str]) -> str:
    """Executes a command safely and returns standard output."""
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        return ""


def audit_gpu() -> Dict[str, Any]:
    """Audits GPU vendor, VRAM, and AI inference feasibility."""
    gpu_info = {
        "detected": False,
        "name": "Unknown",
        "vendor": "Unknown",
        "vram_mb": 0,
        "cuda_available": False,
        "neural_inference_tier": "cpu_only",
        "notes": [],
    }

    # Check NVIDIA CLI first
    nvidia_out = run_cmd(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if nvidia_out:
        parts = nvidia_out.split(",")
        gpu_info["detected"] = True
        gpu_info["name"] = parts[0].strip()
        gpu_info["vendor"] = "NVIDIA"
        gpu_info["cuda_available"] = True
        try:
            gpu_info["vram_mb"] = int(parts[1].strip())
        except Exception:
            gpu_info["vram_mb"] = 0

    elif sys.platform == "win32":
        # Windows WMI query for AMD/Intel/NVIDIA
        ps_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
        ps_out = run_cmd(["powershell", "-NoProfile", "-Command", ps_cmd])
        if ps_out:
            try:
                data = json.loads(ps_out)
                if isinstance(data, list):
                    item = data[0]
                else:
                    item = data
                gpu_info["detected"] = True
                gpu_info["name"] = item.get("Name", "Generic Display")
                ram_bytes = item.get("AdapterRAM", 0) or 0
                gpu_info["vram_mb"] = int(ram_bytes // (1024 * 1024))
                if "NVIDIA" in gpu_info["name"].upper():
                    gpu_info["vendor"] = "NVIDIA"
                elif "AMD" in gpu_info["name"].upper() or "RADEON" in gpu_info["name"].upper():
                    gpu_info["vendor"] = "AMD"
                elif "INTEL" in gpu_info["name"].upper():
                    gpu_info["vendor"] = "Intel"
            except Exception:
                pass

    # Evaluate neural tier
    vram = gpu_info["vram_mb"]
    vendor = gpu_info["vendor"]
    if vendor == "NVIDIA" and vram >= 20000:
        gpu_info["neural_inference_tier"] = "tier_1_heavy_neural"
        gpu_info["notes"].append("Capable of running heavy diffusion (MiniMax-H3 VSA, Wan2.1, Flux.1) and 32B+ LLMs locally.")
    elif vendor == "NVIDIA" and vram >= 8000:
        gpu_info["neural_inference_tier"] = "tier_2_medium_neural"
        gpu_info["notes"].append("Capable of running SDXL, Whisper, Qwen-2.5-Coder 7B/14B Q4.")
    elif vram > 0 and vram <= 4096:
        gpu_info["neural_inference_tier"] = "tier_3_light_or_cloud"
        gpu_info["notes"].append(f"VRAM limited ({vram} MB, {vendor}). Heavy neural video (ComfyUI-Ref2VA-VSA requires 24GB VRAM) must be offloaded to cloud GPUs.")
    else:
        gpu_info["neural_inference_tier"] = "tier_3_light_or_cloud"
        gpu_info["notes"].append("No dedicated high-VRAM CUDA GPU detected. Local agent operations should use API providers or lightweight CPU quantization.")

    return gpu_info


def audit_runtimes() -> Dict[str, Any]:
    """Audits local programming runtimes and containerization."""
    runtimes = {}

    # Node
    node_v = run_cmd(["node", "--version"])
    runtimes["node"] = {"installed": bool(node_v), "version": node_v or None}

    # Python
    py_v = run_cmd(["python", "--version"])
    runtimes["python"] = {"installed": bool(py_v), "version": py_v or None}

    # Git
    git_v = run_cmd(["git", "--version"])
    runtimes["git"] = {"installed": bool(git_v), "version": git_v or None}

    # Docker
    docker_v = run_cmd(["docker", "--version"])
    docker_running = False
    if docker_v:
        info_out = run_cmd(["docker", "info"])
        docker_running = bool(info_out and "Server Version" in info_out)
    runtimes["docker"] = {
        "installed": bool(docker_v),
        "version": docker_v or None,
        "daemon_running": docker_running,
    }

    # PNPM / NPM
    pnpm_v = run_cmd(["pnpm", "--version"])
    npm_v = run_cmd(["npm", "--version"])
    runtimes["pnpm"] = {"installed": bool(pnpm_v), "version": pnpm_v or None}
    runtimes["npm"] = {"installed": bool(npm_v), "version": npm_v or None}

    # Rust / Cargo
    cargo_v = run_cmd(["cargo", "--version"])
    runtimes["cargo"] = {"installed": bool(cargo_v), "version": cargo_v or None}

    return runtimes


def audit_agent_tools() -> Dict[str, Any]:
    """Checks presence of agent workspaces and CLI tools."""
    tools = {}
    tools["pi_desktop"] = {
        "source_cloned": os.path.exists(r"C:\workspace\temp\pi-desktop"),
        "portable_exe_available": os.path.exists(r"C:\workspace\temp\pi-desktop\PI-Desktop-Portable-0.15.10.exe"),
    }
    tools["google_maps_scraper"] = {
        "kit_cloned": os.path.exists(r"C:\workspace\temp\google-maps-scraper-kit"),
        "scripts_ready": os.path.exists(r"C:\workspace\temp\google-maps-scraper-kit\scripts\scrape.py"),
    }
    tools["transitions_dev"] = {
        "repo_cloned": os.path.exists(r"C:\workspace\temp\transitions-dev"),
        "cli_ready": os.path.exists(r"C:\workspace\temp\transitions-dev\cli\bin\transitions-dev.mjs"),
    }
    tools["comfyui_ref2va_vsa"] = {
        "repo_cloned": os.path.exists(r"C:\workspace\temp\ComfyUI-Ref2VA-VSA"),
        "nodes_ready": os.path.exists(r"C:\workspace\temp\ComfyUI-Ref2VA-VSA\nodes.py"),
    }
    return tools


def generate_report() -> Dict[str, Any]:
    """Compiles complete preflight audit report."""
    gpu = audit_gpu()
    runtimes = audit_runtimes()
    agent_tools = audit_agent_tools()

    return {
        "status": "PASS",
        "hardware": {"gpu": gpu},
        "runtimes": runtimes,
        "agent_tools": agent_tools,
        "recommendations": gpu["notes"],
    }


def main():
    parser = argparse.ArgumentParser(description="Auditor de Hardware, Runtimes e Ferramentas de Agente")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON estruturado")
    args = parser.parse_args()

    report = generate_report()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("═════════════════════════════════════════════════════════════════════")
    print("      AXION AGENTIC PREFLIGHT & HARDWARE CAPABILITY AUDITOR         ")
    print("═════════════════════════════════════════════════════════════════════")

    # Hardware
    gpu = report["hardware"]["gpu"]
    print(f"\n[GPU/Hardware]")
    print(f"  • Dispositivo : {gpu['name']}")
    print(f"  • VRAM        : {gpu['vram_mb']} MB")
    print(f"  • CUDA        : {'Sim' if gpu['cuda_available'] else 'Não'}")
    print(f"  • Nível Neural: {gpu['neural_inference_tier']}")

    # Runtimes
    print(f"\n[Runtimes & Containers]")
    for name, data in report["runtimes"].items():
        st = "✓ " + data["version"] if data["installed"] else "✗ Ausente"
        if name == "docker" and data["installed"]:
            st += f" (Daemon: {'Ativo' if data['daemon_running'] else 'Inativo'})"
        print(f"  • {name.ljust(8)}: {st}")

    # Cloned Kits
    print(f"\n[Ferramentas de Agente Locais]")
    for tool, data in report["agent_tools"].items():
        ready = any(data.values())
        print(f"  • {tool.ljust(22)}: {'Pronto/Clonado' if ready else 'Pendente'}")

    print("\n[Diretrizes Operacionais]")
    for note in report["recommendations"]:
        print(f"  💡 {note}")
    print("═════════════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
