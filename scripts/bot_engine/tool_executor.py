#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Tool Execution Engine on the PC — AXION Enterprise
Provides full autonomous access to Windows OS, PowerShell, workspace files,
telemetry sentinels, backups, and task injection without external dependencies.
"""

import os
import sys
import json
import time
import subprocess
import shutil
import ctypes
import re
import threading
import urllib.request
import urllib.error
import html
from pathlib import Path


# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bot_engine import task_queue

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def _normalize_command_for_windows(cmd: str) -> tuple[str, dict]:
    """
    Normalizes arbitrary shell commands (often written by LLMs in Linux/bash syntax)
    for 100% reliable execution on Windows PowerShell.
    
    1. Injects PATH with Git usr/bin (giving native ls, grep, awk, sed, which, cat, touch, head, tail, etc.)
    2. Translates 'export VAR=val' to '$env:VAR = "val"'
    3. Translates 'source <file>' to '. <file>'
    4. Translates bash '&&' chaining to PowerShell conditional execution '; if ($?) { ... }'
    5. Translates bash '||' chaining to PowerShell conditional execution '; if (-not $?) { ... }'
    6. Unaliases PowerShell conflicting cmdlets (ls, rm, cp, mv, curl, wget, cat, diff, sort)
    7. Suppresses CLIXML progress stream and ensures UTF-8 output encoding
    """
    env = os.environ.copy()
    git_usr = r"C:\Program Files\Git\usr\bin"
    git_cmd = r"C:\Program Files\Git\cmd"
    current_path = env.get("PATH", "")
    to_add = [p for p in [git_usr, git_cmd] if os.path.exists(p) and p.lower() not in current_path.lower()]
    if to_add:
        env["PATH"] = ";".join(to_add) + ";" + current_path

    env["PYTHONIOENCODING"] = "utf-8"
    env["LANG"] = "en_US.UTF-8"
    # Anti-hang & non-interactive execution flags
    env["CI"] = "1"
    env["CONTINUOUS_INTEGRATION"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["PIP_NO_INPUT"] = "1"
    env["npm_config_yes"] = "true"
    env["MPLBACKEND"] = "Agg"

    lines = []
    for line in cmd.split("\n"):
        line = re.sub(r'\bexport\s+([A-Za-z_][A-Za-z0-9_]*)=([^\s;&|]+)', r'$env:\1 = "\2"', line)
        line = re.sub(r'^\s*source\s+', r'. ', line)
        lines.append(line)
    transformed = "\n".join(lines)

    if " && " in transformed:
        parts = transformed.split(" && ")
        transformed = parts[0]
        for p in parts[1:]:
            transformed += f"; if ($?) {{ {p}"
        transformed += " }" * (len(parts) - 1)

    if " || " in transformed:
        parts = transformed.split(" || ")
        transformed = parts[0]
        for p in parts[1:]:
            transformed += f"; if (-not $?) {{ {p}"
        transformed += " }" * (len(parts) - 1)

    preamble = (
        "$ProgressPreference = 'SilentlyContinue'; "
        "try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}; "
        "$OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Remove-Item alias:curl, alias:wget, alias:ls, alias:cat, alias:rm, alias:cp, alias:mv, alias:diff, alias:sort -ErrorAction SilentlyContinue; "
        "if (-not (Get-Command which -ErrorAction SilentlyContinue)) { function which { param([string]$n) (Get-Command $n -ErrorAction SilentlyContinue).Source } }; "
        "if (-not (Get-Command touch -ErrorAction SilentlyContinue)) { function touch { param([string]$p) if (-not (Test-Path $p)) { New-Item -ItemType File -Path $p -Force | Out-Null } else { (Get-Item $p).LastWriteTime = Get-Date } } }; "
    )

    full_ps = preamble + "\n" + transformed
    return full_ps, env


# Global tracking for active background processes
_RUNNING_PROCESSES = {}  # pid -> {proc, stdout_lines, stderr_lines, io_lock, start_t, cmd, cwd, threads}
_PROCESSES_LOCK = threading.Lock()

def _diagnose_error(returncode: int, out: str, err: str) -> str | None:
    """Diagnoses common command failures on Windows"""
    if returncode == 0:
        return None
    lower_err = (err + " " + out).lower()
    if any(k in lower_err for k in ["commandnotfoundexception", "não é reconhecido", "not recognized", "is not recognized"]):
        return "Comando não encontrado no PATH. Verifique o nome do utilitário ou se o pacote/módulo correspondente foi instalado."
    elif any(k in lower_err for k in ["unauthorizedaccessexception", "acesso negado", "access is denied", "permission denied", "sharing violation"]):
        return "Acesso negado. O arquivo ou recurso pode estar bloqueado por outro processo em execução ou requerer privilégios elevados."
    elif any(k in lower_err for k in ["itemnotfoundexception", "caminho não encontrado", "cannot find the path", "path not found", "filenotfounderror"]):
        return "Caminho não encontrado. Verifique se o arquivo ou diretório pai existe. Lembre-se de utilizar barras normais (/) no Windows."
    elif any(k in lower_err for k in ["port already in use", "address already in use", "only one usage of each socket address", "endereço já em uso"]):
        return "A porta de rede já está em uso por outro processo. Use a ferramenta 'free_port' para encerrar o processo anterior."
    elif any(k in lower_err for k in ["parsererror", "invalidendofline", "token '&&'", "token '||'"]):
        return "Erro de sintaxe do PowerShell. Evite operadores bash crus como && e ||."
    return None


CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008

def _get_silent_windows_execution_kwargs(detached: bool = False) -> dict:
    """
    Returns subprocess kwargs ensuring that on Windows NO console window,
    PowerShell prompt, or command prompt flashes or steals focus from the user.
    Uses CREATE_NO_WINDOW and STARTUPINFO SW_HIDE.
    """
    kwargs = {}
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = si
        flags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        if detached:
            flags |= DETACHED_PROCESS
        kwargs["creationflags"] = flags
    return kwargs


def exec_command(cmd: str, timeout: int = 35, cwd: str = None) -> dict:
    """
    Executes any shell or PowerShell command on the PC safely with UTF-8 encoding and Linux compatibility.
    Does NOT hard-kill on timeout: if command is still running after checkpoint timeout,
    keeps the process active in background and returns running=True with PID and partial logs
    for the LLM to inspect and decide whether to wait or kill.
    """
    work_dir = Path(cwd) if cwd else WORKSPACE_ROOT
    start_t = time.time()

    if cmd.startswith("cmd.exe ") or (cmd.startswith("python ") and not any(c in cmd for c in ["&&", "||", "|", ">", "<", ";"])):
        shell_cmd = cmd
        use_shell = True
        env = os.environ.copy()
        env["CI"] = "1"
        env["CONTINUOUS_INTEGRATION"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["PIP_NO_INPUT"] = "1"
        env["npm_config_yes"] = "true"
        env["MPLBACKEND"] = "Agg"
        git_usr = r"C:\Program Files\Git\usr\bin"
        if os.path.exists(git_usr) and git_usr.lower() not in env.get("PATH", "").lower():
            env["PATH"] = git_usr + ";" + env.get("PATH", "")
    else:
        full_script, env = _normalize_command_for_windows(cmd)
        shell_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full_script]
        use_shell = False

    try:
        proc = subprocess.Popen(
            shell_cmd,
            shell=use_shell,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            **_get_silent_windows_execution_kwargs()
        )

        stdout_lines = []
        stderr_lines = []
        io_lock = threading.Lock()

        def _reader(stream, storage):
            try:
                for line in iter(stream.readline, ''):
                    with io_lock:
                        storage.append(line)
            except Exception:
                pass
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        t_out = threading.Thread(target=_reader, args=(proc.stdout, stdout_lines), daemon=True)
        t_err = threading.Thread(target=_reader, args=(proc.stderr, stderr_lines), daemon=True)
        t_out.start()
        t_err.start()

        # Cooperative polling until completion or checkpoint timeout
        checkpoint_window = max(5, timeout)
        deadline = time.time() + checkpoint_window
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.3)

        if proc.poll() is None:
            # Process exceeded initial checkpoint!
            # DO NOT KILL. Register in _RUNNING_PROCESSES and return partial state to LLM
            with _PROCESSES_LOCK:
                _RUNNING_PROCESSES[proc.pid] = {
                    "proc": proc,
                    "stdout_lines": stdout_lines,
                    "stderr_lines": stderr_lines,
                    "io_lock": io_lock,
                    "start_t": start_t,
                    "cmd": cmd,
                    "cwd": str(work_dir),
                    "threads": [t_out, t_err]
                }

            with io_lock:
                tail_out = "".join(stdout_lines[-30:]).strip().lstrip('\ufeff')
                tail_err = "".join(stderr_lines[-30:]).strip().lstrip('\ufeff')

            partial_log = tail_out
            if tail_err:
                partial_log += f"\n[STDERR]:\n{tail_err}"
            if not partial_log:
                partial_log = "(processo ativo em background, aguardando saída no buffer...)"

            elapsed = round(time.time() - start_t, 2)
            return {
                "success": False,
                "running": True,
                "pid": proc.pid,
                "cmd": cmd[:120],
                "elapsed_seconds": elapsed,
                "status": "in_progress",
                "partial_output": partial_log,
                "requires_decision": True,
                "diagnosis": (
                    f"O comando atingiu o checkpoint de verificação ({timeout}s) mas continua executando ativamente (PID {proc.pid}). "
                    "NENHUM processo foi morto. Inspecione os logs parciais acima: "
                    "Se o processo estiver evoluindo normalmente, chame 'wait_command' para continuar aguardando. "
                    "Se estiver travado ou em loop, chame 'kill_command' para encerrar e decidir reiniciar."
                )
            }

        # Process finished within checkpoint window
        t_out.join(timeout=2)
        t_err.join(timeout=2)
        with io_lock:
            out = "".join(stdout_lines).strip().lstrip('\ufeff')
            err = "".join(stderr_lines).strip().lstrip('\ufeff')

        elapsed = round(time.time() - start_t, 2)
        returncode = proc.returncode

        # Strip CLIXML progress noise from stderr if any leaked
        if err and "#< CLIXML" in err:
            err = re.sub(r'#< CLIXML[\s\S]*?</Objs>', '', err).strip()

        diagnosis = _diagnose_error(returncode, out, err)

        return {
            "success": returncode == 0,
            "running": False,
            "returncode": returncode,
            "elapsed_seconds": elapsed,
            "output": out if out else "(nenhuma saída padrão gerada)",
            "error": err if err else None,
            "diagnosis": diagnosis,
        }
    except Exception as e:
        return {
            "success": False,
            "running": False,
            "returncode": -1,
            "elapsed_seconds": round(time.time() - start_t, 2),
            "output": "",
            "error": str(e),
            "diagnosis": f"Exceção interna ao disparar processo: {str(e)}"
        }


def wait_command(pid: int, wait_seconds: int = 30) -> dict:
    """
    Continues monitoring an existing background process, returning updated logs or final output.
    Does NOT kill on expiration; returns running=True for the LLM to decide.
    """
    with _PROCESSES_LOCK:
        proc_entry = _RUNNING_PROCESSES.get(pid)

    if not proc_entry:
        return {
            "success": False,
            "running": False,
            "error": f"Nenhum processo em execução encontrado com PID {pid}. O processo pode já ter sido encerrado.",
            "diagnosis": "Verifique se o PID informado está correto ou se o comando já foi concluído anteriormente."
        }

    proc = proc_entry["proc"]
    io_lock = proc_entry["io_lock"]
    stdout_lines = proc_entry["stdout_lines"]
    stderr_lines = proc_entry["stderr_lines"]
    start_t = proc_entry["start_t"]
    cmd = proc_entry.get("cmd", "")

    deadline = time.time() + max(3, wait_seconds)
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.3)

    if proc.poll() is None:
        # Still running after wait_seconds
        total_elapsed = round(time.time() - start_t, 2)
        with io_lock:
            tail_out = "".join(stdout_lines[-30:]).strip().lstrip('\ufeff')
            tail_err = "".join(stderr_lines[-30:]).strip().lstrip('\ufeff')

        partial_log = tail_out
        if tail_err:
            partial_log += f"\n[STDERR]:\n{tail_err}"
        if not partial_log:
            partial_log = "(processo ativo em background, aguardando saída no buffer...)"

        return {
            "success": False,
            "running": True,
            "pid": pid,
            "cmd": cmd[:120],
            "elapsed_seconds": total_elapsed,
            "status": "in_progress",
            "partial_output": partial_log,
            "requires_decision": True,
            "message": f"Processo PID {pid} continua ativo após aguardar mais {wait_seconds}s (total: {total_elapsed}s).",
            "diagnosis": (
                "O processo continua executando ativamente. Analise os logs recentes: "
                "Se estiver progredindo normalmente, chame 'wait_command' novamente. "
                "Se estiver travado, chame 'kill_command' para encerrar e decidir reiniciar."
            )
        }

    # Completed!
    with _PROCESSES_LOCK:
        _RUNNING_PROCESSES.pop(pid, None)

    for th in proc_entry.get("threads", []):
        th.join(timeout=2)

    with io_lock:
        out = "".join(stdout_lines).strip().lstrip('\ufeff')
        err = "".join(stderr_lines).strip().lstrip('\ufeff')

    if err and "#< CLIXML" in err:
        err = re.sub(r'#< CLIXML[\s\S]*?</Objs>', '', err).strip()

    returncode = proc.returncode
    total_elapsed = round(time.time() - start_t, 2)
    diagnosis = _diagnose_error(returncode, out, err)

    # Detect Vercel or HTTP URLs in the output if any
    detected_url = None
    alias_match = re.search(r'Aliased\s+(https://[a-zA-Z0-9\-\.]+\.vercel\.app)', out + " " + err)
    if alias_match:
        detected_url = alias_match.group(1).strip()
    else:
        url_match = re.search(r'https://[a-zA-Z0-9\-\.]+\.vercel\.app[^\s]*', out + " " + err)
        if url_match:
            detected_url = url_match.group(0).strip().rstrip(".")

    res = {
        "success": returncode == 0,
        "running": False,
        "pid": pid,
        "returncode": returncode,
        "elapsed_seconds": total_elapsed,
        "output": out if out else "(nenhuma saída padrão gerada)",
        "error": err if err else None,
        "diagnosis": diagnosis
    }
    if detected_url:
        res["url"] = detected_url

    return res


def kill_command(pid: int) -> dict:
    """
    Terminates a running background process and its entire process tree safely using taskkill.
    Cleans up from internal process tracking.
    """
    with _PROCESSES_LOCK:
        proc_entry = _RUNNING_PROCESSES.pop(pid, None)

    proc = proc_entry["proc"] if proc_entry else None

    # Terminate process tree via taskkill
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            **_get_silent_windows_execution_kwargs()
        )
    except Exception:
        pass

    if proc:
        try:
            proc.kill()
        except Exception:
            pass

    return {
        "success": True,
        "killed": True,
        "pid": pid,
        "message": f"Processo PID {pid} e processos filhos foram encerrados com sucesso. Você pode reiniciar a tarefa com novos parâmetros ou outra abordagem.",
        "diagnosis": "O processo foi abortado conforme solicitado. Avalie as causas do bloqueio nos logs anteriores antes de reiniciar."
    }


def check_command_status(pid: int) -> dict:
    """
    Instant non-blocking status and log check for a running background process.
    """
    with _PROCESSES_LOCK:
        proc_entry = _RUNNING_PROCESSES.get(pid)

    if not proc_entry:
        return {
            "success": False,
            "running": False,
            "pid": pid,
            "message": f"Nenhum processo ativo com PID {pid} encontrado."
        }

    proc = proc_entry["proc"]
    is_running = proc.poll() is None
    io_lock = proc_entry["io_lock"]
    stdout_lines = proc_entry["stdout_lines"]
    stderr_lines = proc_entry["stderr_lines"]
    start_t = proc_entry["start_t"]

    with io_lock:
        tail_out = "".join(stdout_lines[-30:]).strip().lstrip('\ufeff')
        tail_err = "".join(stderr_lines[-30:]).strip().lstrip('\ufeff')

    log = tail_out
    if tail_err:
        log += f"\n[STDERR]:\n{tail_err}"

    return {
        "success": True,
        "running": is_running,
        "pid": pid,
        "elapsed_seconds": round(time.time() - start_t, 2),
        "partial_output": log or "(sem saída até o momento)",
        "returncode": proc.returncode if not is_running else None
    }



def read_file(file_path: str, max_lines: int = 150) -> dict:
    """Reads content of a file from disk"""
    p = Path(file_path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / file_path

    if not p.exists():
        return {"success": False, "error": f"Arquivo não encontrado: {p}"}

    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            return {
                "success": True,
                "path": str(p),
                "lines_read": len(lines),
                "content": content
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_file(file_path: str, content: str) -> dict:
    """Writes or overwrites content to a file"""
    p = Path(file_path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / file_path

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "path": str(p),
            "bytes_written": len(content.encode("utf-8"))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def replace_in_file(file_path: str, target_content: str, replacement_content: str) -> dict:
    """Surgically replaces a specific block of text in a file without rewriting the entire file"""
    p = Path(file_path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / file_path

    if not p.exists():
        return {"success": False, "error": f"Arquivo não encontrado: {p}"}

    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        if target_content not in content:
            return {
                "success": False,
                "error": "Conteúdo alvo (target_content) não encontrado no arquivo.",
                "diagnosis": "Certifique-se de passar o trecho exato de código existente, incluindo indentação e espaços."
            }
        new_content = content.replace(target_content, replacement_content, 1)
        p.write_text(new_content, encoding="utf-8")
        return {
            "success": True,
            "path": str(p),
            "bytes_written": len(new_content.encode("utf-8")),
            "message": "Substituição cirúrgica concluída com sucesso."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_in_files(query: str, dir_path: str = None, file_pattern: str = "*", max_matches: int = 30) -> dict:
    """Searches for text or regex pattern across files recursively without relying on shell grep/findstr"""
    root = Path(dir_path) if dir_path else WORKSPACE_ROOT
    if not root.is_absolute():
        root = WORKSPACE_ROOT / dir_path

    if not root.exists():
        return {"success": False, "error": f"Diretório não encontrado: {root}"}

    EXCLUDED_DIRS = {".git", "node_modules", "memory", "temp", "tmp", ".gemini", ".vercel", "__pycache__", ".venv"}
    matches = []
    try:
        regex = re.compile(query, re.IGNORECASE)
        for p in root.rglob(file_pattern):
            if any(part in EXCLUDED_DIRS for part in p.parts):
                continue
            if p.is_file() and p.stat().st_size < 1_500_000:
                try:
                    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines, 1):
                        if regex.search(line):
                            matches.append({
                                "file": str(p.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                                "line": idx,
                                "text": line.strip()[:160]
                            })
                            if len(matches) >= max_matches:
                                break
                except Exception:
                    pass
            if len(matches) >= max_matches:
                break
        return {
            "success": True,
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def free_port(port: int) -> dict:
    """Finds and terminates any process listening on the specified local TCP port"""
    try:
        cmd = f"netstat -ano | findstr :{port}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, **_get_silent_windows_execution_kwargs())
        killed = []
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 4:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, **_get_silent_windows_execution_kwargs())
                    killed.append(int(pid))
        return {
            "success": True,
            "port": port,
            "killed_pids": list(set(killed)),
            "message": f"Porta {port} liberada (processos encerrados: {killed})" if killed else f"Nenhum processo estava ocupando a porta {port}."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_directory(path: str = None, max_items: int = 40) -> dict:
    """Lists files and folders in a directory"""
    p = Path(path) if path else WORKSPACE_ROOT
    if not p.is_absolute():
        p = WORKSPACE_ROOT / path

    if not p.exists():
        return {"success": False, "error": f"Caminho não encontrado: {p}"}

    try:
        items = []
        for entry in list(p.iterdir())[:max_items]:
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else None
            })
        return {
            "success": True,
            "path": str(p),
            "total_items": len(items),
            "items": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_top_ram_processes(limit: int = 3) -> list[dict]:
    """Returns top N processes grouped by RAM usage in MB using native tasklist"""
    try:
        import csv
        out = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True, timeout=4, **_get_silent_windows_execution_kwargs())
        proc_map = {}
        for row in csv.reader(out.strip().splitlines()):
            if len(row) > 4 and ' K' in row[4]:
                pname = row[0]
                kb_str = row[4].replace('.', '').replace(',', '').replace(' K', '').strip()
                kb = int(kb_str) if kb_str.isdigit() else 0
                proc_map[pname] = proc_map.get(pname, 0) + kb
        sorted_procs = sorted(proc_map.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"name": p, "memory_mb": round(kb / 1024, 1)} for p, kb in sorted_procs]
    except Exception:
        return []


def get_system_telemetry() -> dict:
    """Gets real-time OS stats (CPU, RAM, Disks, Tailscale) natively"""
    # RAM via Windows Kernel32
    ram_info = {"total_gb": 12.0, "free_gb": 6.0, "used_gb": 6.0, "percent_used": 50, "top_processes": []}
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            tot = round(stat.ullTotalPhys / (1024**3), 2)
            fre = round(stat.ullAvailPhys / (1024**3), 2)
            usd = round(max(0.0, tot - fre), 2)
            pct = stat.dwMemoryLoad
            top_procs = get_top_ram_processes(3) if pct >= 80 else []
            ram_info = {
                "total_gb": tot,
                "free_gb": fre,
                "used_gb": usd,
                "percent_used": pct,
                "top_processes": top_procs
            }
    except Exception:
        pass

    # Disk usage
    c_disk = shutil.disk_usage("C:\\")
    e_disk = shutil.disk_usage("E:\\") if os.path.exists("E:\\") else None

    # Probe Tailscale status
    tailscale_info = "UNKNOWN"
    try:
        res = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=5, **_get_silent_windows_execution_kwargs())
        if res.returncode == 0:
            lines = [l.strip() for l in res.stdout.split("\n") if l.strip()]
            tailscale_info = f"{len(lines)} nós na rede"
    except Exception:
        tailscale_info = "Disponível (CLI)"

    c_info = {
        "total_gb": round(c_disk.total / (1024**3), 2),
        "free_gb": round(c_disk.free / (1024**3), 2),
        "percent_free": round((c_disk.free / c_disk.total) * 100, 1),
        "free_pct": round((c_disk.free / c_disk.total) * 100, 1)
    }
    e_info = {
        "exists": e_disk is not None,
        "total_gb": round(e_disk.total / (1024**3), 2) if e_disk else 0,
        "free_gb": round(e_disk.free / (1024**3), 2) if e_disk else 0,
        "percent_free": round((e_disk.free / e_disk.total) * 100, 1) if e_disk else 0,
        "free_pct": round((e_disk.free / e_disk.total) * 100, 1) if e_disk else 0
    }
    ram_info["used_pct"] = ram_info.get("percent_used", 0)

    # Extract node count from Tailscale summary if possible
    m = re.search(r'(\d+)', tailscale_info)
    node_count = int(m.group(1)) if m else "?"

    return {
        "success": True,
        "ram": ram_info,
        "c_drive": c_info,
        "disk_c": c_info,
        "e_backup_drive": e_info,
        "disk_e": e_info,
        "tailscale": {"node_count": node_count, "summary": tailscale_info},
        "tailscale_summary": tailscale_info
    }

def run_health_check() -> dict:
    """Executes the health monitor & auto-fix script"""
    script_path = WORKSPACE_ROOT / "scripts" / "health_monitor_autofix.py"
    return exec_command(f"python {script_path}", timeout=45)

def run_ssl_sentinel() -> dict:
    """Executes the SSL domain sentinel script"""
    script_path = WORKSPACE_ROOT / "scripts" / "ssl_domain_sentinel.py"
    return exec_command(f"python {script_path}", timeout=45)

def run_backup(backup_type: str = "smart") -> dict:
    """Spawns the backup script in a detached background process (non-blocking).
    Returns immediately — backup runs async and logs to memory/backup_run.log.
    """
    if backup_type == "prune":
        script_path = WORKSPACE_ROOT / "scripts" / "backup_rotation_prune.py"
    else:
        script_path = WORKSPACE_ROOT / "scripts" / "enterprise_smart_backup.py"

    log_path = WORKSPACE_ROOT / "memory" / "telegram" / "backup_run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not script_path.exists():
        return {"success": False, "error": f"Script não encontrado: {script_path}"}

    try:
        log_file = open(log_path, "w", encoding="utf-8")
        proc = subprocess.Popen(
            ["python", str(script_path)],
            stdout=log_file,
            stderr=log_file,
            cwd=str(WORKSPACE_ROOT),
            close_fds=True,
            **_get_silent_windows_execution_kwargs(detached=True)
        )
        return {
            "success": True,
            "async": True,
            "pid": proc.pid,
            "message": (
                f"✅ Backup '{backup_type}' iniciado em background (PID {proc.pid}).\n"
                f"A execução ocorre de forma assíncrona — use 'Ler log de backup' para acompanhar."
            ),
            "log_file": str(log_path),
        }
    except Exception as e:
        # Fallback: run synchronously with higher timeout
        return exec_command(f"python {script_path}", timeout=300)


def vercel_deploy(project_name: str, html_content: str = "", project_dir: str = "") -> dict:
    """Creates a project with HTML content and deploys it to Vercel, returning the live URL.
    
    Args:
        project_name: Name of the project (e.g. 'alice-garden')
        html_content: Full HTML content for index.html (if empty, uses existing dir)
        project_dir: Absolute path to project dir (if not provided, creates under C:\\workspace)
    """
    import re as _re
    
    # Determine project directory
    if project_dir:
        proj = Path(project_dir)
    else:
        proj = WORKSPACE_ROOT / project_name
    
    proj.mkdir(parents=True, exist_ok=True)
    
    # Write index.html if content provided
    if html_content:
        idx = proj / "index.html"
        idx.write_text(html_content, encoding="utf-8")
    
    # Write minimal vercel.json if it doesn't exist
    vercel_json = proj / "vercel.json"
    if not vercel_json.exists():
        vercel_json.write_text(json.dumps({"version": 2}, indent=2), encoding="utf-8")
    
    # Run vercel deploy (cwd is already set to proj, avoid invalid '&&' in Windows PowerShell)
    deploy_cmd = 'vercel --prod --yes --no-color'
    result = exec_command(deploy_cmd, timeout=40, cwd=str(proj))

    # If deploy is still in progress at checkpoint, propagate running state
    if result.get("running"):
        return {
            "success": False,
            "running": True,
            "pid": result.get("pid"),
            "project_dir": str(proj),
            "project_name": project_name,
            "elapsed_seconds": result.get("elapsed_seconds"),
            "partial_output": result.get("partial_output", ""),
            "status": "in_progress",
            "requires_decision": True,
            "diagnosis": (
                f"O deploy no Vercel está em andamento ativo (PID {result.get('pid')}). O processo NÃO foi cancelado. "
                "Inspecione os logs parciais acima: chame 'wait_command' informando o PID para continuar aguardando a finalização."
            )
        }

    # Disable Vercel Team SSO deployment protection so deployment is publicly accessible
    exec_command(f'vercel project protection disable {project_name} --sso', timeout=20, cwd=str(proj))

    # Extract URL from output (prioritize Aliased URL if available)
    url = None
    output = result.get("output", "") + (result.get("error") or "")

    alias_match = _re.search(r'Aliased\s+(https://[a-zA-Z0-9\-\.]+\.vercel\.app)', output)
    if alias_match:
        url = alias_match.group(1).strip()
    else:
        url_match = _re.search(r'https://[a-zA-Z0-9\-\.]+\.vercel\.app[^\s]*', output)
        if url_match:
            url = url_match.group(0).strip().rstrip(".")

    return {
        "success": result.get("success", False) or (url is not None),
        "url": url,
        "project_dir": str(proj),
        "project_name": project_name,
        "vercel_output": output[:2000],
        "error": result.get("error") if not url else None
    }



def manage_workspace_task(action: str, **kwargs) -> dict:
    """Manages tasks in canonical workspace memory"""
    if action == "inject":
        instruction = kwargs.get("instruction", "")
        title = kwargs.get("title")
        priority = kwargs.get("priority", "normal")
        source = kwargs.get("source", "telegram")
        return {"success": True, "task": task_queue.inject_task(instruction, title, priority, source)}
    elif action == "list":
        status = kwargs.get("status")
        return {"success": True, "tasks": task_queue.list_tasks(status=status)}
    elif action == "execute":
        task_id = kwargs.get("task_id", "")
        return {"success": True, "task": task_queue.execute_task(task_id)}
    elif action == "delete":
        task_id = kwargs.get("task_id", "")
        return {"success": task_queue.delete_task(task_id)}
    else:
        return {"success": False, "error": f"Ação desconhecida: {action}"}

def read_backup_log(lines: int = 50) -> dict:
    """Reads the tail of the async backup run log to check progress/completion."""
    log_path = WORKSPACE_ROOT / "memory" / "telegram" / "backup_run.log"
    if not log_path.exists():
        return {"success": False, "error": "Nenhum log de backup encontrado. Execute run_backup primeiro."}
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        tail = "".join(all_lines[-lines:])
        total = len(all_lines)
        # Detect completion signals in the log
        completed = any(k in tail.lower() for k in ["backup concluído", "completed", "sucesso", "✅", "done", "finished"])
        failed = any(k in tail.lower() for k in ["error", "erro", "failed", "exception", "traceback"])
        return {
            "success": True,
            "log_path": str(log_path),
            "total_lines": total,
            "tail": tail,
            "backup_completed": completed,
            "backup_failed": failed,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_content_intelligence() -> dict:
    """Lê o último relatório do Content Intelligence Monitor (GitHub Trending, Hacker News, RSS Feeds)."""
    digest_path = WORKSPACE_ROOT / "memory" / "intelligence" / "daily_digest.jsonl"
    if not digest_path.exists():
        return {"success": False, "error": "Nenhum digest de inteligência encontrado. Execute o monitor primeiro."}
    try:
        last = None
        with open(digest_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        last = json.loads(line)
                    except Exception:
                        pass
        if not last:
            return {"success": False, "error": "Arquivo de digest está vazio."}
        return {"success": True, "intelligence": last}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_social_intelligence(platform: str = "all", query: str = "", limit: int = 5) -> dict:
    """Retorna os últimos hits e posts de redes sociais (Twitter/X e Instagram) com filtro opcional."""
    results = {}
    tw_path = WORKSPACE_ROOT / "memory" / "intelligence" / "twitter_hits.jsonl"
    ig_path = WORKSPACE_ROOT / "memory" / "intelligence" / "instagram_hits.jsonl"

    if platform.lower() in ["all", "twitter", "x"] and tw_path.exists():
        tw_items = []
        try:
            with open(tw_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            tw_items.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
        if query:
            q = query.lower()
            tw_items = [t for t in tw_items if q in t.get("text", "").lower() or q in t.get("username", "").lower()]
        results["twitter"] = tw_items[-limit:]

    if platform.lower() in ["all", "instagram", "ig"] and ig_path.exists():
        ig_items = []
        try:
            with open(ig_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            ig_items.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
        if query:
            q = query.lower()
            ig_items = [p for p in ig_items if q in p.get("caption", "").lower() or q in p.get("profile", "").lower()]
        results["instagram"] = ig_items[-limit:]

    return {"success": True, "data": results}


# Registry of tools callable by the AI agent
TOOL_DEFINITIONS = {
    "exec_command": {
        "description": "Executa qualquer comando de shell/PowerShell/CMD no PC local (C:\\workspace)",
        "parameters": {"cmd": "string (comando a ser executado)", "timeout": "int opcional (padrão 60)"}
    },
    "read_file": {
        "description": "Lê o conteúdo de um arquivo do disco",
        "parameters": {"file_path": "string (caminho relativo ou absoluto)"}
    },
    "write_file": {
        "description": "Escreve ou sobrescreve conteúdo em um arquivo local",
        "parameters": {"file_path": "string", "content": "string"}
    },
    "replace_in_file": {
        "description": "Substitui cirurgicamente um bloco exato de texto dentro de um arquivo, sem precisar reescrever o arquivo inteiro. Altamente recomendado para edições pontuais.",
        "parameters": {
            "file_path": "string (caminho do arquivo)",
            "target_content": "string (trecho exato de código existente a ser substituído)",
            "replacement_content": "string (novo código que substituirá o trecho)"
        }
    },
    "search_in_files": {
        "description": "Busca rápida recursiva por texto ou regex em arquivos do projeto sem depender de grep/findstr.",
        "parameters": {
            "query": "string (texto ou regex a pesquisar)",
            "dir_path": "string opcional (diretório base, padrão C:\\workspace)",
            "file_pattern": "string opcional (ex: '*.py', '*.ts', '*.json', padrão '*')",
            "max_matches": "int opcional (padrão 30)"
        }
    },
    "free_port": {
        "description": "Localiza e encerra qualquer processo que esteja prendendo uma porta TCP local no Windows.",
        "parameters": {"port": "int (número da porta, ex: 3000, 8080)"}
    },
    "list_directory": {
        "description": "Lista pastas e arquivos de um diretório",
        "parameters": {"path": "string opcional (padrão C:\\workspace)"}
    },
    "get_system_telemetry": {
        "description": "Obtém métricas em tempo real do PC (memória RAM, discos C: e E:, Tailscale)",
        "parameters": {}
    },
    "run_health_check": {
        "description": "Executa a verificação completa de saúde dos servidores, rede Tailnet e endpoints",
        "parameters": {}
    },
    "run_ssl_sentinel": {
        "description": "Audita os 16 certificados SSL e domínios da AXION",
        "parameters": {}
    },
    "run_backup": {
        "description": "Dispara o backup inteligente ASSINCRONAMENTE em background (retorna imediatamente com PID). O backup roda sem bloquear. Use 'read_backup_log' para verificar o progresso depois.",
        "parameters": {"backup_type": "string ('smart' ou 'prune')"}
    },
    "read_backup_log": {
        "description": "Lê as últimas linhas do log do backup que está rodando em background. Use após run_backup para confirmar se concluiu com sucesso.",
        "parameters": {"lines": "int opcional (padrão 50)"}
    },
    "manage_workspace_task": {
        "description": "Injeta, lista ou executa tarefas na fila do workspace (active_tasks.json)",
        "parameters": {
            "action": "'inject' | 'list' | 'execute' | 'delete'",
            "instruction": "string (instrução da tarefa ao injetar)",
            "title": "string opcional",
            "priority": "'low' | 'normal' | 'high' | 'critical'",
            "task_id": "string (para execute ou delete)"
        }
    },
    "vercel_deploy": {
        "description": "Cria um projeto web com HTML e faz deploy no Vercel, retornando a URL pública. Use SEMPRE quando o usuário pedir para hospedar/publicar/deploiar um site.",
        "parameters": {
            "project_name": "string (nome do projeto, ex: 'alice-garden')",
            "html_content": "string (conteúdo HTML completo do index.html — inclua TODO o HTML aqui)",
            "project_dir": "string opcional (caminho absoluto do projeto se já existir)"
        }
    },
    "get_content_intelligence": {
        "description": "Retorna o último relatório do Content Intelligence Monitor com novidades de tecnologia, GitHub Trending, Hacker News e RSS do ecossistema AXION.",
        "parameters": {}
    },
    "get_social_intelligence": {
        "description": "Consulta os últimos tweets (Twitter/X) e posts do Instagram monitorados pelo agente, com suporte a busca por palavra-chave ou perfil de tecnologia (cloudflare, vercel, etc.).",
        "parameters": {
            "platform": "string opcional ('all', 'twitter', 'instagram')",
            "query": "string opcional (termo de busca)",
            "limit": "int opcional (padrão 5)"
        }
    },
    "run_ai_intelligence_pipeline": {
        "description": "Executa o pipeline de IA e agentes: descobre perfis relevantes (Motor 1), analisa e valida insights técnicos (Motor 2), gera skills/MCPs canônicos (Motor 3) e executa testes locais (Motor 4).",
        "parameters": {
            "action": "string opcional ('full', 'discover', 'validate', 'build')",
            "target": "string opcional (handle ou tópico)"
        }
    },
    "wait_command": {
        "description": "Acompanha a execução de um processo em background retornado pelo checkpoint (identificado pelo PID). Não mata o processo no timeout: lê novos logs e retorna o status atualizado para a LLM avaliar.",
        "parameters": {
            "pid": "int obrigatório (PID do processo retornado pelo checkpoint anterior)",
            "wait_seconds": "int opcional (segundos para aguardar nesta checagem, padrão 30)"
        }
    },
    "kill_command": {
        "description": "Encerra forçadamente um processo em execução e todos os seus subprocessos filhos usando taskkill. Use quando os logs indicarem travamento, loop infinito ou necessidade de reiniciar a tarefa.",
        "parameters": {
            "pid": "int obrigatório (PID do processo a ser encerrado)"
        }
    },
    "check_command_status": {
        "description": "Verificação instantânea e não-bloqueante dos logs e do status de um processo pelo PID.",
        "parameters": {
            "pid": "int obrigatório (PID do processo)"
        }
    },
    "send_whatsapp_message": {
        "description": "Envia mensagem via WhatsApp com proteção estrita Anti-Ban da Meta. SEMPRE verifica se o número destinatário já enviou mensagem prévia (opt-in) antes de disparar. Mensagens para números virgens que nunca interagiram são bloqueadas para evitar banimento da conta.",
        "parameters": {
            "to": "string obrigatório (número de telefone com DDI e DDD, ex: '5511999999999')",
            "message": "string obrigatório (texto da mensagem)",
            "type": "string opcional ('comercial' ou 'utilidade', padrão 'utilidade')",
            "force": "bool opcional (ignora trava anti-ban apenas sob ordem expressa)"
        }
    },
    "get_whatsapp_status": {
        "description": "Verifica a saúde do canal WhatsApp (Baileys), status de conexão, número ativo, pairing code e contagem de leads/equipe.",
        "parameters": {}
    },
    "list_whatsapp_leads": {
        "description": "Lista os leads comerciais capturados via WhatsApp com status, data de contato e contagem de mensagens.",
        "parameters": {}
    },
    "list_whatsapp_team": {
        "description": "Lista os membros da equipe corporativa cadastrados no WhatsApp por cargo/função.",
        "parameters": {}
    },
    "search_chat_history": {
        "description": "Busca mensagens e conversas anteriores locais por palavra-chave ou termo. Use SEMPRE que precisar consultar o que foi dito ou combinado anteriormente com o operador ou clientes.",
        "parameters": {
            "query": "string obrigatório (termo ou palavra-chave a buscar)",
            "chat_id": "string opcional (ID do chat ou número de telefone para filtrar)",
            "limit": "int opcional (quantidade máxima de mensagens, padrão 10)"
        }
    },
    "read_daily_log": {
        "description": "Lê o registro diário de atividades, eventos e diálogos em memory/daily_logs/. Permite ler as últimas linhas ou filtrar por palavra-chave sem necessidade de comandos complexos de shell.",
        "parameters": {
            "date": "string opcional (formato YYYY-MM-DD, padrão é hoje)",
            "lines": "int opcional (número de linhas finais, padrão 50)",
            "query": "string opcional (filtra apenas linhas contendo esta palavra-chave)"
        }
    },
    "search_knowledge_base": {
        "description": "Consulta a base de conhecimento canônica da AXION Enterprise sobre planos, preços (WhatsApp R$ 0 trial, R$ 97/mês, R$ 50 chip), verticais de desenvolvimento (sites, sistemas, agentes sob demanda), AXION Pay, infraestrutura e governança.",
        "parameters": {
            "query": "string obrigatório (termo de pesquisa ou dúvida sobre produtos, serviços ou regras)",
            "limit": "int opcional (quantidade máxima de trechos, padrão 2)",
            "vertical": "string opcional ('all', 'commercial', 'technical', 'operations', 'governance', padrão 'all')"
        }
    },
    "check_desktop_agent_tasks": {
        "description": "Inspeciona em tempo real tarefas em andamento e concluídas dos agentes desktop (Antigravity, Codex, OpenCode) e emite alertas proativos ao CEO Executive Operator.",
        "parameters": {
            "notify_ceo": "bool opcional (se True, notifica o CEO imediatamente para tarefas recém-finalizadas, padrão True)"
        }
    },
    "request_client_resource_approval": {
        "description": "Solicita aprovação direta ou código OTP/2FA via WhatsApp para o cliente do projeto informado, com cópia carbono para o CEO Executive Operator e registro de auditoria.",
        "parameters": {
            "project_name": "string obrigatório (nome do projeto ou cliente, ex: 'SpaPharma Loja Virtual')",
            "client_phone": "string obrigatório (número de WhatsApp do cliente com DDI e DDD, ex: '5511999998888')",
            "resource_type": "string obrigatório (tipo de recurso, ex: 'OTP SMS', '2FA Authenticator', 'Aprovação de Deploy')",
            "reason": "string obrigatório (motivo detalhado da solicitação para o cliente)",
            "client_name": "string opcional (nome do contato do cliente, padrão 'Cliente')",
            "timeout_minutes": "int opcional (validade em minutos, padrão 15)"
        }
    },
    "check_client_resource_approval": {
        "description": "Verifica o status de uma solicitação de aprovação ou código OTP enviado ao cliente, checando se houve resposta no WhatsApp.",
        "parameters": {
            "approval_id": "string obrigatório (ID da aprovação gerada, ex: 'appr_a1b2c3d4')"
        }
    },
    "submit_client_otp": {
        "description": "Valida e registra manualmente o código OTP ou confirmação informada pelo cliente.",
        "parameters": {
            "approval_id": "string obrigatório (ID da aprovação)",
            "otp_code": "string obrigatório (código ou termo de aprovação)"
        }
    },
    "fetch_url": {
        "description": "Acessa e extrai o conteúdo textual de qualquer URL pública ou link da web (artigos, documentação, status, APIs). Suporta nativamente Google Docs e Google Sheets, extraindo o texto limpo.",
        "parameters": {
            "url": "string obrigatório (URL completa com http:// ou https://)",
            "max_chars": "int opcional (limite de caracteres retornados, padrão 15000)"
        }
    },
    "run_codex_cli": {
        "description": "Executa comandos diretamente na CLI do OpenAI Codex (v0.160.0). Suporta subcomandos como 'exec' (execução headless autônoma de prompts com bypass de confirmação), 'review', 'doctor', 'agents', 'features'. Notifica automaticamente a conclusão no Desktop Watcher.",
        "parameters": {
            "prompt": "string opcional (instrução ou prompt para o agente Codex)",
            "subcommand": "string opcional (subcomando: 'exec' (padrão), 'review', 'doctor', 'agents', 'features')",
            "extra_args": "string opcional (argumentos adicionais de linha de comando, ex: '--model gpt-5.4-mini')",
            "timeout": "int opcional (limite de execução em segundos, padrão 120)"
        }
    },
    "run_antigravity_cli": {
        "description": "Executa comandos diretamente na CLI do Google Antigravity (agy / antigravity v1.2.11). Suporta subcomandos como 'print' (modo headless não-interativo de prompts), 'agents', 'models', 'mcp', 'changelog'. Notifica automaticamente a conclusão no Desktop Watcher.",
        "parameters": {
            "prompt": "string opcional (instrução ou prompt para o Antigravity)",
            "subcommand": "string opcional (subcomando: 'print' (padrão), 'agents', 'models', 'mcp', 'changelog')",
            "extra_args": "string opcional (argumentos adicionais de linha de comando)",
            "timeout": "int opcional (limite de execução em segundos, padrão 120)"
        }
    },
    "run_opencode_cli": {
        "description": "Executa comandos diretamente na CLI do OpenCode (v1.18.34). Suporta subcomandos como 'run' (execução headless autônoma com modelo free e auto-aprovação de permissões), 'models', 'stats', 'session', 'export'. Notifica automaticamente a conclusão no Desktop Watcher.",
        "parameters": {
            "prompt": "string opcional (instrução ou prompt para o OpenCode)",
            "subcommand": "string opcional (subcomando: 'run' (padrão), 'models', 'stats', 'session', 'export')",
            "extra_args": "string opcional (argumentos adicionais de linha de comando)",
            "timeout": "int opcional (limite de execução em segundos, padrão 120)"
        }
    },
    "get_desktop_clis_status": {
        "description": "Retorna o inventário completo, versão instalada, caminhos de binário e contagem de processos em execução das 3 CLIs dos agentes desktop: OpenAI Codex, Google Antigravity e OpenCode.",
        "parameters": {}
    },
    "dispatch_desktop_task": {
        "description": "Orquestra e delega a execução autônoma de uma tarefa de engenharia para o agente desktop ideal (OpenAI Codex, Google Antigravity ou OpenCode), considerando afinidade técnica, modelos neurais, limites de rate limit (429), quotas de uso e failover automático.",
        "parameters": {
            "task_description": "string obrigatório (descrição detalhada e clara da tarefa técnica para o agente desktop)",
            "preferred_agent": "string opcional ('codex', 'antigravity', 'opencode' ou 'auto', padrão 'auto')",
            "timeout": "int opcional (limite de execução em segundos, padrão 180)"
        }
    },
    "get_desktop_orchestrator_status": {
        "description": "Retorna o painel completo de orquestração dos agentes desktop: status operacional, quotas, rate limits ativos, modelos neurais e processos concorrentes.",
        "parameters": {}
    }
}

# Fuzzy synonym mapping for tool names
TOOL_SYNONYMS = {
    "run_codex_cli": "run_codex_cli",
    "codex_cli": "run_codex_cli",
    "codex": "run_codex_cli",
    "run_codex": "run_codex_cli",
    "run_antigravity_cli": "run_antigravity_cli",
    "antigravity_cli": "run_antigravity_cli",
    "agy_cli": "run_antigravity_cli",
    "antigravity": "run_antigravity_cli",
    "agy": "run_antigravity_cli",
    "run_antigravity": "run_antigravity_cli",
    "run_agy": "run_antigravity_cli",
    "run_opencode_cli": "run_opencode_cli",
    "opencode_cli": "run_opencode_cli",
    "opencode": "run_opencode_cli",
    "run_opencode": "run_opencode_cli",
    "get_desktop_clis_status": "get_desktop_clis_status",
    "desktop_clis_status": "get_desktop_clis_status",
    "check_desktop_clis": "get_desktop_clis_status",
    "clis_status": "get_desktop_clis_status",
    "desktop_agents_status": "get_desktop_clis_status",
    "status_clis": "get_desktop_clis_status",
    "fetch_url": "fetch_url",
    "read_url": "fetch_url",
    "get_url": "fetch_url",
    "curl_url": "fetch_url",
    "browse_url": "fetch_url",
    "ler_url": "fetch_url",
    "extrair_url": "fetch_url",
    "run_command": "exec_command",
    "execute_command": "exec_command",
    "terminal": "exec_command",
    "cmd": "exec_command",
    "powershell": "exec_command",
    "bash": "exec_command",
    "shell": "exec_command",
    "cat": "read_file",
    "view_file": "read_file",
    "read": "read_file",
    "create_file": "write_file",
    "save_file": "write_file",
    "write": "write_file",
    "patch_file": "replace_in_file",
    "edit_file": "replace_in_file",
    "modify_file": "replace_in_file",
    "grep": "search_in_files",
    "find_in_files": "search_in_files",
    "grep_code": "search_in_files",
    "ls": "list_directory",
    "dir": "list_directory",
    "list_dir": "list_directory",
    "telemetry": "get_system_telemetry",
    "system_telemetry": "get_system_telemetry",
    "sysinfo": "get_system_telemetry",
    "deploy": "vercel_deploy",
    "deploy_vercel": "vercel_deploy",
    "wait_cmd": "wait_command",
    "wait_process": "wait_command",
    "await_command": "wait_command",
    "kill_process": "kill_command",
    "stop_command": "kill_command",
    "abort_command": "kill_command",
    "cancel_command": "kill_command",
    "status_command": "check_command_status",
    "check_process": "check_command_status",
    "search_chat": "search_chat_history",
    "search_messages": "search_chat_history",
    "chat_history": "search_chat_history",
    "find_chat": "search_chat_history",
    "read_log": "read_daily_log",
    "daily_log": "read_daily_log",
    "get_daily_log": "read_daily_log",
    "desktop_watcher": "check_desktop_agent_tasks",
    "check_desktop_tasks": "check_desktop_agent_tasks",
    "request_otp": "request_client_resource_approval",
    "request_client_otp": "request_client_resource_approval",
    "check_otp": "check_client_resource_approval",
    "check_approval": "check_client_resource_approval",
    "dispatch_desktop_task": "dispatch_desktop_task",
    "dispatch_task": "dispatch_desktop_task",
    "orchestrate_task": "dispatch_desktop_task",
    "delegate_task": "dispatch_desktop_task",
    "run_desktop_agent": "dispatch_desktop_task",
    "solicitar_agente": "dispatch_desktop_task",
    "pedir_agente": "dispatch_desktop_task",
    "get_desktop_orchestrator_status": "get_desktop_orchestrator_status",
    "orchestrator_status": "get_desktop_orchestrator_status",
}

# Fuzzy synonym mapping for parameters
PARAM_SYNONYMS = {
    "dispatch_desktop_task": {"task": "task_description", "prompt": "task_description", "instruction": "task_description", "agent": "preferred_agent", "agente": "preferred_agent"},
    "run_codex_cli": {"instruction": "prompt", "message": "prompt", "p": "prompt", "query": "prompt", "action": "subcommand", "cmd": "subcommand"},
    "run_antigravity_cli": {"instruction": "prompt", "message": "prompt", "p": "prompt", "query": "prompt", "action": "subcommand", "cmd": "subcommand"},
    "run_opencode_cli": {"instruction": "prompt", "message": "prompt", "p": "prompt", "query": "prompt", "action": "subcommand", "cmd": "subcommand"},
    "exec_command": {"command": "cmd", "script": "cmd", "code": "cmd"},
    "read_file": {"path": "file_path", "filename": "file_path", "file": "file_path"},
    "write_file": {"path": "file_path", "filename": "file_path", "file": "file_path", "text": "content", "data": "content", "body": "content"},
    "replace_in_file": {"file": "file_path", "path": "file_path", "target": "target_content", "old": "target_content", "replacement": "replacement_content", "new": "replacement_content"},
    "search_in_files": {"search": "query", "pattern": "query", "text": "query", "dir": "dir_path", "path": "dir_path"},
    "free_port": {"p": "port"},
    "list_directory": {"dir": "path", "directory": "path", "folder": "path"},
    "wait_command": {"seconds": "wait_seconds", "time": "wait_seconds", "timeout": "wait_seconds", "duration": "wait_seconds", "process_id": "pid", "id": "pid"},
    "kill_command": {"process_id": "pid", "id": "pid"},
    "check_command_status": {"process_id": "pid", "id": "pid"},
    "search_chat_history": {"q": "query", "term": "query", "text": "query", "chat": "chat_id"},
    "read_daily_log": {"day": "date", "date_str": "date", "q": "query", "filter": "query"},
    "fetch_url": {"link": "url", "uri": "url", "address": "url", "input": "url", "website": "url"},
}

def execute_tool(tool_name: str, args: dict) -> dict:
    """Dispatches tool execution by name and arguments with fuzzy synonym resolution"""
    canonical_tool = TOOL_SYNONYMS.get(tool_name.lower().strip(), tool_name)
    resolved_args = dict(args)

    # Normalize parameters based on synonyms
    if canonical_tool in PARAM_SYNONYMS:
        synonyms = PARAM_SYNONYMS[canonical_tool]
        for arg_key, val in list(resolved_args.items()):
            if arg_key in synonyms:
                canonical_param = synonyms[arg_key]
                if canonical_param not in resolved_args:
                    resolved_args[canonical_param] = val

    print(f"[tool_executor] Executando tool: '{canonical_tool}' (original: '{tool_name}') com args: {resolved_args}")

    if canonical_tool == "exec_command":
        return exec_command(resolved_args.get("cmd", ""), timeout=int(resolved_args.get("timeout", 35)))
    elif canonical_tool == "wait_command":
        return wait_command(
            pid=int(resolved_args.get("pid", 0)),
            wait_seconds=int(resolved_args.get("wait_seconds", 30))
        )
    elif canonical_tool == "kill_command":
        return kill_command(pid=int(resolved_args.get("pid", 0)))
    elif canonical_tool == "check_command_status":
        return check_command_status(pid=int(resolved_args.get("pid", 0)))
    elif canonical_tool == "read_file":
        return read_file(resolved_args.get("file_path", ""))
    elif canonical_tool == "write_file":
        return write_file(resolved_args.get("file_path", ""), resolved_args.get("content", ""))
    elif canonical_tool == "replace_in_file":
        return replace_in_file(
            file_path=resolved_args.get("file_path", ""),
            target_content=resolved_args.get("target_content", ""),
            replacement_content=resolved_args.get("replacement_content", "")
        )
    elif canonical_tool == "search_in_files":
        return search_in_files(
            query=resolved_args.get("query", ""),
            dir_path=resolved_args.get("dir_path"),
            file_pattern=resolved_args.get("file_pattern", "*"),
            max_matches=int(resolved_args.get("max_matches", 30))
        )
    elif canonical_tool == "free_port":
        return free_port(port=int(resolved_args.get("port", 0)))
    elif canonical_tool == "list_directory":
        return list_directory(resolved_args.get("path"))
    elif canonical_tool == "get_system_telemetry":
        return get_system_telemetry()
    elif canonical_tool == "run_health_check":
        return run_health_check()
    elif canonical_tool == "run_ssl_sentinel":
        return run_ssl_sentinel()
    elif canonical_tool == "run_backup":
        return run_backup(resolved_args.get("backup_type", "smart"))
    elif canonical_tool == "read_backup_log":
        return read_backup_log(lines=int(resolved_args.get("lines", 50)))
    elif canonical_tool == "manage_workspace_task":
        return manage_workspace_task(**resolved_args)
    elif canonical_tool == "vercel_deploy":
        return vercel_deploy(
            project_name=resolved_args.get("project_name", "project"),
            html_content=resolved_args.get("html_content", ""),
            project_dir=resolved_args.get("project_dir", "")
        )
    elif canonical_tool == "get_content_intelligence":
        return get_content_intelligence()
    elif canonical_tool == "get_social_intelligence":
        return get_social_intelligence(
            platform=resolved_args.get("platform", "all"),
            query=resolved_args.get("query", ""),
            limit=int(resolved_args.get("limit", 5))
        )
    elif canonical_tool == "run_ai_intelligence_pipeline":
        return run_ai_intelligence_pipeline(
            action=resolved_args.get("action", "full"),
            target=resolved_args.get("target", "")
        )
    elif canonical_tool == "send_whatsapp_message":
        return send_whatsapp_message(
            to=str(resolved_args.get("to", "")),
            message=str(resolved_args.get("message", "")),
            type=str(resolved_args.get("type", "utilidade")),
            force=bool(resolved_args.get("force", False))
        )
    elif canonical_tool == "get_whatsapp_status":
        return get_whatsapp_status()
    elif canonical_tool == "list_whatsapp_leads":
        return list_whatsapp_leads()
    elif canonical_tool == "list_whatsapp_team":
        return list_whatsapp_team()
    elif canonical_tool == "search_chat_history":
        return search_chat_history(
            query=str(resolved_args.get("query", "")),
            chat_id=resolved_args.get("chat_id"),
            limit=int(resolved_args.get("limit", 10))
        )
    elif canonical_tool == "read_daily_log":
        return read_daily_log(
            date=resolved_args.get("date"),
            lines=int(resolved_args.get("lines", 50)),
            query=resolved_args.get("query")
        )
    elif canonical_tool == "search_knowledge_base":
        return search_knowledge_base(
            query=str(resolved_args.get("query", "")),
            limit=int(resolved_args.get("limit", 2)),
            vertical=str(resolved_args.get("vertical", "all"))
        )
    elif canonical_tool == "check_desktop_agent_tasks":
        return check_desktop_agent_tasks(
            notify_ceo=bool(resolved_args.get("notify_ceo", True))
        )
    elif canonical_tool == "request_client_resource_approval":
        return request_client_resource_approval(
            project_name=str(resolved_args.get("project_name", "")),
            client_phone=str(resolved_args.get("client_phone", "")),
            resource_type=str(resolved_args.get("resource_type", "OTP")),
            reason=str(resolved_args.get("reason", "")),
            client_name=str(resolved_args.get("client_name", "Cliente")),
            timeout_minutes=int(resolved_args.get("timeout_minutes", 15))
        )
    elif canonical_tool == "check_client_resource_approval":
        return check_client_resource_approval(
            approval_id=str(resolved_args.get("approval_id", ""))
        )
    elif canonical_tool == "submit_client_otp":
        return submit_client_otp(
            approval_id=str(resolved_args.get("approval_id", "")),
            otp_code=str(resolved_args.get("otp_code", resolved_args.get("code", "")))
        )
    elif canonical_tool == "fetch_url":
        return fetch_url(
            url=str(resolved_args.get("url", "")),
            max_chars=int(resolved_args.get("max_chars", 15000))
        )
    elif canonical_tool == "run_codex_cli":
        return run_codex_cli(
            prompt=str(resolved_args.get("prompt", "")),
            subcommand=str(resolved_args.get("subcommand", "exec")),
            extra_args=str(resolved_args.get("extra_args", "")),
            timeout=int(resolved_args.get("timeout", 120))
        )
    elif canonical_tool == "run_antigravity_cli":
        return run_antigravity_cli(
            prompt=str(resolved_args.get("prompt", "")),
            subcommand=str(resolved_args.get("subcommand", "print")),
            extra_args=str(resolved_args.get("extra_args", "")),
            timeout=int(resolved_args.get("timeout", 120))
        )
    elif canonical_tool == "run_opencode_cli":
        return run_opencode_cli(
            prompt=str(resolved_args.get("prompt", "")),
            subcommand=str(resolved_args.get("subcommand", "run")),
            extra_args=str(resolved_args.get("extra_args", "")),
            timeout=int(resolved_args.get("timeout", 120))
        )
    elif canonical_tool == "get_desktop_clis_status":
        return get_desktop_clis_status()
    elif canonical_tool == "dispatch_desktop_task":
        return dispatch_desktop_task(
            task_description=str(resolved_args.get("task_description", resolved_args.get("prompt", ""))),
            preferred_agent=str(resolved_args.get("preferred_agent", "auto")),
            timeout=int(resolved_args.get("timeout", 180))
        )
    elif canonical_tool == "get_desktop_orchestrator_status":
        return get_desktop_orchestrator_status()
    else:
        return {"success": False, "error": f"Ferramenta desconhecida: '{tool_name}'"}


def send_whatsapp_message(to: str, message: str, type: str = "utilidade", force: bool = False) -> dict:
    """
    Envia mensagem via WhatsApp com validação obrigatória Anti-Ban da Meta.
    Verifica se o número destinatário já enviou mensagem prévia (opt-in) antes de disparar.
    Disparos para números virgens que nunca interagiram são estritamente bloqueados para proteger o número da empresa.
    """
    try:
        import urllib.request
        import urllib.error
        url = "http://127.0.0.1:4114/whatsapp/send"
        payload = json.dumps({"to": to, "message": message, "type": type, "force": force}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode("utf-8"))
            if res.get("success"):
                try:
                    from . import message_store
                    clean_to = to if "@" in to else f"{to.replace('+', '').strip()}@s.whatsapp.net"
                    message_store.save_message(
                        clean_to, "outgoing", message,
                        metadata={"tool": "send_whatsapp_message", "type": type}
                    )
                except Exception as ms_err:
                    print(f"[tool_executor] Aviso ao salvar WhatsApp no message_store: {ms_err}")
            return res
    except urllib.error.HTTPError as he:
        err_data = he.read().decode("utf-8", errors="ignore")
        try:
            return json.loads(err_data)
        except Exception:
            return {"success": False, "error": f"HTTP {he.code}: {err_data}"}
    except Exception as e:
        return {"success": False, "error": f"Falha ao conectar no WhatsApp bridge (porta 4114): {e}"}


def get_whatsapp_status() -> dict:
    """Verifica o status da conexão WhatsApp, número ativo, pairing code e contadores de leads e equipe."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:4114/status", timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"WhatsApp bridge offline: {e}"}


def list_whatsapp_leads() -> dict:
    """Retorna a lista de leads capturados no WhatsApp com status, contagem de mensagens e histórico."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:4114/leads", timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"WhatsApp bridge offline: {e}"}


def list_whatsapp_team() -> dict:
    """Retorna os membros da equipe corporativa cadastrados no WhatsApp por cargo/função."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:4114/team", timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"WhatsApp bridge offline: {e}"}


def search_chat_history(query: str, chat_id: str = None, limit: int = 10) -> dict:
    """Busca mensagens e conversas anteriores locais por palavra-chave ou termo."""
    try:
        from . import message_store
        matches = message_store.search_messages(query=query, chat_id=chat_id, limit=limit)
        clean_matches = []
        for m in matches:
            clean_matches.append({
                "timestamp": m.get("timestamp"),
                "chat_id": m.get("chat_id"),
                "direction": m.get("direction"),
                "text": m.get("text", "")[:300]
            })
        return {
            "success": True,
            "query": query,
            "count": len(clean_matches),
            "results": clean_matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_daily_log(date: str = None, lines: int = 50, query: str = None) -> dict:
    """Lê o log diário consolidado de atividades e diálogos em memory/daily_logs/."""
    try:
        from . import message_store
        res = message_store.read_daily_log_content(date_str=date, lines=lines, query=query)
        return res
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_ai_intelligence_pipeline(action: str = "full", target: str = "") -> dict:
    """Executa o pipeline de IA e agentes: descoberta, validação, criação de skills e testes."""
    try:
        from services.ai_intelligence_pipeline.pipeline_orchestrator import run_full_pipeline
        from services.ai_intelligence_pipeline import profile_discovery_engine, insight_validator_engine
        if action == "discover":
            handles = [target.strip().lstrip("@")] if target else None
            res = profile_discovery_engine.discover_and_evaluate_profiles(candidate_handles=handles)
            return {"success": True, "profiles": res}
        elif action == "validate":
            res = insight_validator_engine.run_insight_validation(max_items=3)
            return {"success": True, "validated_insights": res}
        else:
            res = run_full_pipeline(max_insights_to_validate=2, auto_build_skills=True)
            return {"success": True, "pipeline_summary": res}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_knowledge_base(query: str, limit: int = 2, vertical: str = "all") -> dict:
    """Consulta a base de conhecimento canônica em docs/knowledge via RAG in-memory de ultrabaixa latência (< 3ms)."""
    try:
        from . import knowledge_rag
        results = knowledge_rag.search_knowledge_base(query=query, limit=limit, vertical=vertical)
        return {
            "success": True,
            "query": query,
            "vertical": vertical,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_desktop_agent_tasks(notify_ceo: bool = True) -> dict:
    """Inspeciona tarefas em andamento e concluídas dos agentes desktop (Antigravity, Codex, OpenCode)."""
    try:
        from . import desktop_watcher
        res = desktop_watcher.scan_and_notify_finished_tasks(force_notify=notify_ceo)
        telemetry = desktop_watcher.get_desktop_watcher_status()
        return {
            "success": True,
            "scan_results": res,
            "status": telemetry
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def request_client_resource_approval(
    project_name: str,
    client_phone: str,
    resource_type: str,
    reason: str,
    client_name: str = "Cliente",
    timeout_minutes: int = 15
) -> dict:
    """Solicita aprovação ou código OTP/2FA via WhatsApp para cliente de projeto específico com cópia ao CEO."""
    try:
        from . import client_approval
        return client_approval.request_client_resource_approval(
            project_name=project_name,
            client_phone=client_phone,
            resource_type=resource_type,
            reason=reason,
            client_name=client_name,
            timeout_minutes=timeout_minutes
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_client_resource_approval(approval_id: str) -> dict:
    """Verifica o status de uma aprovação pendente ou código OTP enviado ao cliente."""
    try:
        from . import client_approval
        return client_approval.check_client_approval_status(approval_id=approval_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


def submit_client_otp(approval_id: str, otp_code: str) -> dict:
    """Insere e valida o código OTP/aprovação recebido para liberar a operação em andamento."""
    try:
        from . import client_approval
        return client_approval.submit_approval_code(approval_id=approval_id, code=otp_code)
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_url(url: str, max_chars: int = 15000) -> dict:
    """
    Acessa e extrai o conteúdo textual de qualquer URL pública ou link web.
    Suporta automaticamente:
    - Google Docs (converte para exportação em texto limpo)
    - Google Sheets (converte para CSV)
    - Páginas Web / HTML (remove tags, scripts e estilos)
    - APIs JSON / Arquivos de texto / Markdown
    """
    try:
        clean_url = str(url or "").strip().strip('<>').strip('"').strip("'")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            return {"success": False, "error": f"URL inválida: '{clean_url}'. Deve iniciar com http:// ou https://"}

        # Suporte nativo e automático para Google Docs
        gdoc_match = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', clean_url)
        if gdoc_match:
            doc_id = gdoc_match.group(1)
            clean_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

        # Suporte nativo e automático para Google Sheets
        gsheet_match = re.search(r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)', clean_url)
        if gsheet_match:
            sheet_id = gsheet_match.group(1)
            clean_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        req = urllib.request.Request(
            clean_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AXION-Agent/2.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain,*/*;q=0.8"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw_bytes = resp.read(max_chars * 4)

            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()

            text = raw_bytes.decode(charset, errors="replace")

            if "html" in content_type or "<html" in text.lower():
                text = re.sub(r'<(?:script|style)[^>]*>[\s\S]*?</(?:script|style)>', ' ', text, flags=re.IGNORECASE)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = html.unescape(text)
                text = re.sub(r'[ \t]+', ' ', text)
                text = re.sub(r'\n\s*\n', '\n\n', text).strip()

            truncated = len(text) > max_chars
            final_text = text[:max_chars]

            return {
                "success": True,
                "url": url,
                "resolved_url": clean_url,
                "content": final_text,
                "length": len(final_text),
                "truncated": truncated
            }
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


def run_codex_cli(prompt: str = "", subcommand: str = "exec", extra_args: str = "", timeout: int = 120) -> dict:
    """
    Executa comandos diretamente na CLI do OpenAI Codex (v0.160.0).
    Suporta subcomandos como 'exec' (execução autônoma de prompts), 'review', 'doctor', 'agents', 'features'.
    Registra automaticamente a conclusão da tarefa no sentinela Desktop Watcher.
    """
    clean_subcmd = (subcommand or "exec").strip().lower()
    clean_extra = (extra_args or "").strip()
    clean_prompt = (prompt or "").strip()

    if clean_subcmd in ["exec", "e", "run"]:
        if not clean_prompt:
            return {"success": False, "error": "Prompt obrigatório para o subcomando 'exec' do Codex."}
        escaped_prompt = clean_prompt.replace('"', '\"')
        cmd = f'codex.cmd exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --color never "{escaped_prompt}"'
        if clean_extra:
            cmd += f" {clean_extra}"
    elif clean_subcmd in ["review", "doctor", "agents", "features", "mcp", "update"]:
        cmd = f"codex.cmd {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'
    else:
        cmd = f"codex.cmd {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'

    res = exec_command(cmd, timeout=timeout)
    # Registra no desktop_watcher se terminou com sucesso
    if res.get("success"):
        try:
            from . import desktop_watcher
            t_id = f"codex_cli_{int(time.time())}"
            title = f"Codex CLI [{clean_subcmd}]: {clean_prompt[:50] or clean_subcmd}"
            output_tail = res.get("output", "")[-300:]
            desktop_watcher.record_desktop_task_completion(
                agent="Codex",
                task_id=t_id,
                title=title,
                status="completed",
                result=output_tail or "Codex CLI finalizado com sucesso."
            )
        except Exception as dw_err:
            print(f"[tool_executor] Aviso ao registrar Codex no watcher: {dw_err}")

    return {
        "success": res.get("success", False),
        "agent": "Codex",
        "cli": "codex",
        "subcommand": clean_subcmd,
        "cmd_executed": cmd[:150],
        "output": res.get("output", ""),
        "error": res.get("error"),
        "elapsed_seconds": res.get("elapsed_seconds", 0.0),
        "running": res.get("running", False)
    }


def run_antigravity_cli(prompt: str = "", subcommand: str = "print", extra_args: str = "", timeout: int = 120) -> dict:
    """
    Executa comandos diretamente na CLI do Google Antigravity (agy / antigravity v1.2.11).
    Suporta subcomandos como 'print' (modo headless não-interativo de prompts), 'agents', 'models', 'mcp', 'changelog'.
    Registra automaticamente a conclusão da tarefa no sentinela Desktop Watcher.
    """
    clean_subcmd = (subcommand or "print").strip().lower()
    clean_extra = (extra_args or "").strip()
    clean_prompt = (prompt or "").strip()

    if clean_subcmd in ["print", "p", "prompt", "exec", "run"]:
        if not clean_prompt:
            return {"success": False, "error": "Prompt obrigatório para o modo 'print' do Antigravity CLI."}
        escaped_prompt = clean_prompt.replace('"', '\"')
        cmd = f'agy.exe --print "{escaped_prompt}" --dangerously-skip-permissions'
        if clean_extra:
            cmd += f" {clean_extra}"
    elif clean_subcmd in ["agents", "agent", "models", "mcp", "changelog", "update"]:
        cmd = f"agy.exe {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'
    else:
        cmd = f"agy.exe {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'

    res = exec_command(cmd, timeout=timeout)
    if res.get("success"):
        try:
            from . import desktop_watcher
            t_id = f"agy_cli_{int(time.time())}"
            title = f"Antigravity CLI [{clean_subcmd}]: {clean_prompt[:50] or clean_subcmd}"
            output_tail = res.get("output", "")[-300:]
            desktop_watcher.record_desktop_task_completion(
                agent="Antigravity",
                task_id=t_id,
                title=title,
                status="completed",
                result=output_tail or "Antigravity CLI finalizado com sucesso."
            )
        except Exception as dw_err:
            print(f"[tool_executor] Aviso ao registrar Antigravity no watcher: {dw_err}")

    return {
        "success": res.get("success", False),
        "agent": "Antigravity",
        "cli": "agy",
        "subcommand": clean_subcmd,
        "cmd_executed": cmd[:150],
        "output": res.get("output", ""),
        "error": res.get("error"),
        "elapsed_seconds": res.get("elapsed_seconds", 0.0),
        "running": res.get("running", False)
    }


def run_opencode_cli(prompt: str = "", subcommand: str = "run", extra_args: str = "", timeout: int = 120) -> dict:
    """
    Executa comandos diretamente na CLI do OpenCode (v1.18.34).
    Suporta subcomandos como 'run' (execução headless autônoma com modelo free e auto-aprovação de permissões), 'models', 'stats', 'session', 'export'.
    Registra automaticamente a conclusão da tarefa no sentinela Desktop Watcher.
    """
    clean_subcmd = (subcommand or "run").strip().lower()
    clean_extra = (extra_args or "").strip()
    clean_prompt = (prompt or "").strip()

    if clean_subcmd in ["run", "exec"]:
        if not clean_prompt:
            return {"success": False, "error": "Prompt obrigatório para o comando 'run' do OpenCode."}
        escaped_prompt = clean_prompt.replace('"', '\"')
        cmd = f'$null | opencode.cmd run --auto "{escaped_prompt}"'
        if clean_extra:
            cmd += f" {clean_extra}"
    elif clean_subcmd in ["models", "stats", "session", "providers", "export", "acp", "mcp"]:
        cmd = f"opencode.cmd {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'
    else:
        cmd = f"opencode.cmd {clean_subcmd}"
        if clean_extra:
            cmd += f" {clean_extra}"
        if clean_prompt:
            escaped_prompt = clean_prompt.replace('"', '\"')
            cmd += f' "{escaped_prompt}"'

    res = exec_command(cmd, timeout=timeout)
    if res.get("success"):
        try:
            from . import desktop_watcher
            t_id = f"opencode_cli_{int(time.time())}"
            title = f"OpenCode CLI [{clean_subcmd}]: {clean_prompt[:50] or clean_subcmd}"
            output_tail = res.get("output", "")[-300:]
            desktop_watcher.record_desktop_task_completion(
                agent="OpenCode",
                task_id=t_id,
                title=title,
                status="completed",
                result=output_tail or "OpenCode CLI finalizado com sucesso."
            )
        except Exception as dw_err:
            print(f"[tool_executor] Aviso ao registrar OpenCode no watcher: {dw_err}")

    return {
        "success": res.get("success", False),
        "agent": "OpenCode",
        "cli": "opencode",
        "subcommand": clean_subcmd,
        "cmd_executed": cmd[:150],
        "output": res.get("output", ""),
        "error": res.get("error"),
        "elapsed_seconds": res.get("elapsed_seconds", 0.0),
        "running": res.get("running", False)
    }


_DESKTOP_CLIS_CACHE = {"timestamp": 0.0, "data": None}
_DESKTOP_CLIS_LOCK = threading.Lock()


def get_desktop_clis_status(force_fresh: bool = False) -> dict:
    """
    Retorna o inventário completo, versão instalada, caminhos de binário e processos ativos
    das 3 CLIs dos agentes desktop: OpenAI Codex, Google Antigravity e OpenCode.
    Usa cache TTL de 10 segundos para máxima velocidade operacional.
    """
    global _DESKTOP_CLIS_CACHE
    now = time.time()
    with _DESKTOP_CLIS_LOCK:
        if not force_fresh and _DESKTOP_CLIS_CACHE["data"] and (now - _DESKTOP_CLIS_CACHE["timestamp"] < 10.0):
            return _DESKTOP_CLIS_CACHE["data"]

    clis = {
        "codex": {
            "name": "OpenAI Codex CLI",
            "command": "codex",
            "installed": False,
            "version": None,
            "binary_path": r"C:\Users\AXION\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe",
            "wrapper_path": r"C:\Users\AXION\AppData\Local\agy\bin\codex.cmd",
            "running_processes": 0,
            "ready": False
        },
        "antigravity": {
            "name": "Google Antigravity CLI",
            "command": "agy",
            "aliases": ["agy", "antigravity"],
            "installed": False,
            "version": None,
            "binary_path": r"C:\Users\AXION\AppData\Local\agy\bin\agy.exe",
            "wrapper_path": r"C:\Users\AXION\AppData\Local\agy\bin\antigravity.cmd",
            "running_processes": 0,
            "ready": False
        },
        "opencode": {
            "name": "OpenCode CLI",
            "command": "opencode",
            "installed": False,
            "version": None,
            "binary_path": r"C:\Users\AXION\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64\opencode.cmd",
            "default_model": "opencode/mimo-v2.6-flash-free",
            "running_processes": 0,
            "ready": False
        }
    }

    # Codex version & check
    try:
        r_codex = exec_command("codex.cmd --version", timeout=10)
        if r_codex.get("success"):
            clis["codex"]["installed"] = True
            clis["codex"]["version"] = r_codex.get("output", "").strip()
            clis["codex"]["ready"] = True
    except Exception:
        pass

    # Antigravity version & check
    try:
        r_agy = exec_command("agy.exe --version", timeout=10)
        if r_agy.get("success"):
            clis["antigravity"]["installed"] = True
            clis["antigravity"]["version"] = r_agy.get("output", "").strip()
            clis["antigravity"]["ready"] = True
    except Exception:
        pass

    # OpenCode version & check
    try:
        r_opencode = exec_command("opencode.cmd --version", timeout=10)
        if r_opencode.get("success"):
            clis["opencode"]["installed"] = True
            clis["opencode"]["version"] = r_opencode.get("output", "").strip()
            clis["opencode"]["ready"] = True
    except Exception:
        pass

    # Check active running processes count for each
    try:
        r_proc = exec_command('Get-Process codex*, Antigravity*, OpenCode* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName', timeout=10)
        if r_proc.get("success") and r_proc.get("output"):
            p_names = [p.strip().lower() for p in r_proc.get("output", "").splitlines() if p.strip()]
            clis["codex"]["running_processes"] = sum(1 for p in p_names if "codex" in p)
            clis["antigravity"]["running_processes"] = sum(1 for p in p_names if "antigravity" in p or "agy" in p)
            clis["opencode"]["running_processes"] = sum(1 for p in p_names if "opencode" in p)
    except Exception:
        pass

    summary_lines = [
        "🖥️ *[AXION Desktop CLIs] Inventário e Status Operacional*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"• *OpenAI Codex:* {'✅ ' + str(clis['codex']['version']) if clis['codex']['ready'] else '❌ Não detectado'} (Processos ativos: {clis['codex']['running_processes']})",
        f"• *Google Antigravity (`agy`):* {'✅ ' + str(clis['antigravity']['version']) if clis['antigravity']['ready'] else '❌ Não detectado'} (Processos ativos: {clis['antigravity']['running_processes']})",
        f"• *OpenCode:* {'✅ ' + str(clis['opencode']['version']) if clis['opencode']['ready'] else '❌ Não detectado'} (Modelo: `{clis['opencode']['default_model']}`, Processos ativos: {clis['opencode']['running_processes']})",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "_Todas as 3 CLIs estão disponíveis no PATH e integradas aos agentes WhatsApp e Brain Server._"
    ]

    result = {
        "success": True,
        "clis": clis,
        "summary": "\n".join(summary_lines)
    }
    with _DESKTOP_CLIS_LOCK:
        _DESKTOP_CLIS_CACHE["timestamp"] = time.time()
        _DESKTOP_CLIS_CACHE["data"] = result
    return result


def fetch_email_otp(recipient: str = "dev@example.com", timeout_seconds: int = 40) -> dict:
    """
    Recupera de forma 100% autônoma o código OTP/2FA ou link de ativação mais recente
    recebido via e-mail corporativo (Cloudflare Catch-All Engine) sem intervenção humana.
    """
    try:
        import importlib.util
        from pathlib import Path
        otp_file = Path("c:/workspace/services/agent-email/otp_client.py")
        spec = importlib.util.spec_from_file_location("axion_otp_client", otp_file)
        otp_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(otp_mod)
        res = otp_mod.get_latest_email_otp(recipient=recipient, timeout_seconds=timeout_seconds)
        return {
            "success": res.get("status") == "ok",
            "otp_code": res.get("otp_code"),
            "verification_links": res.get("verification_links", []),
            "from": res.get("from"),
            "to": res.get("to"),
            "subject": res.get("subject"),
            "received_at": res.get("received_at"),
            "details": res
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dispatch_desktop_task(task_description: str, preferred_agent: str = "auto", timeout: int = 180) -> dict:
    """
    Orquestra e delega a execução autônoma de uma tarefa de engenharia para o agente desktop ideal
    (OpenAI Codex, Google Antigravity ou OpenCode), considerando afinidade técnica, modelos neurais,
    limites de rate limit (429), quotas de uso e failover automático.
    """
    try:
        from . import desktop_orchestrator
    except ImportError:
        from bot_engine import desktop_orchestrator

    pref = None if preferred_agent in ["auto", "", None] else preferred_agent
    return desktop_orchestrator.dispatch_task_to_desktop_agent(
        task_description=task_description,
        preferred_agent=pref,
        timeout=timeout
    )


def get_desktop_orchestrator_status() -> dict:
    """
    Retorna o painel completo de orquestração dos agentes desktop: status operacional,
    quotas, rate limits ativos, modelos neurais e processos concorrentes.
    """
    try:
        from . import desktop_orchestrator
    except ImportError:
        from bot_engine import desktop_orchestrator

    return desktop_orchestrator.get_orchestrator_dashboard()


if __name__ == "__main__":
    print("Testing get_system_telemetry:")
    print(get_system_telemetry())
    print("\nTesting list_directory:")
    print(list_directory(max_items=3))
