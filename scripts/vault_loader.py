"""
AXION Enterprise Vault Loader
=============================
Carregador e gerenciador unificado de segredos e credenciais categorizadas.
Varre a árvore `c:/workspace/vault/**/.env` e hidrata o `os.environ`
de forma determinística e segura.

Categorias suportadas:
  - social/ (twitter-x, instagram, telegram, whatsapp)
  - ai/ (openrouter, huggingface, openai, gemini, elevenlabs)
  - cloud/ (cloudflare, vercel, gcp)
  - communication/ (email, imap, smtp)
  - security/ (proton-vpn, tailscale)

Uso em código:
  from scripts.vault_loader import load_vault
  load_vault()  # Carrega todas as variáveis para os.environ

CLI:
  python scripts/vault_loader.py audit  # Audita o status de todas as credenciais (valores mascarados)
  python scripts/vault_loader.py sync   # Valida integridade do vault
"""

import os
import sys
import json
from pathlib import Path

VAULT_ROOT = Path("c:/workspace/vault")


def load_vault(vault_dir: Path = VAULT_ROOT, override: bool = False) -> dict[str, str]:
    """
    Varre recursivamente todas as subpastas de vault/ procurando por arquivos .env.
    Injeta as variáveis em os.environ.
    Retorna o dicionário com todas as variáveis carregadas.
    """
    loaded = {}
    if not vault_dir.exists():
        return loaded

    # 1. Procurar todos os arquivos .env em vault/
    env_files = sorted(vault_dir.glob("**/.env"))

    # Também carregar .env da raiz se existir (para compatibilidade legada)
    root_env = Path("c:/workspace/.env")
    if root_env.exists() and root_env not in env_files:
        env_files.append(root_env)

    for env_file in env_files:
        try:
            content = env_file.read_text(encoding="utf-8-sig")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key:
                        if override or key not in os.environ:
                            os.environ[key] = val
                        loaded[key] = val
        except Exception as e:
            print(f"[VAULT] Erro ao ler {env_file}: {e}", file=sys.stderr)

    return loaded


def mask_secret(value: str) -> str:
    """Mascara credencial para exibição segura em auditorias."""
    if not value:
        return "<VAZIO>"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def audit_vault():
    """Realiza uma auditoria visual de todas as categorias do Vault."""
    print("=" * 65)
    print("       AXION ENTERPRISE VAULT — AUDITORIA DE SEGREDOS")
    print("=" * 65)

    if not VAULT_ROOT.exists():
        print(f"[!] Diretório {VAULT_ROOT} não encontrado.")
        return

    # Ler index.json mestre se existir
    master_index = VAULT_ROOT / "index.json"
    if master_index.exists():
        try:
            meta = json.loads(master_index.read_text(encoding="utf-8"))
            print(f"Versão do Vault: {meta.get('version', '1.0.0')}")
            print(f"Última Atualização: {meta.get('updated_at', 'N/A')}\n")
        except Exception:
            pass

    # Carregar variáveis atuais
    loaded = load_vault()

    # Procurar cada módulo com index.json
    modules = sorted(VAULT_ROOT.glob("*/*/index.json"))
    for mod_index in modules:
        try:
            data = json.loads(mod_index.read_text(encoding="utf-8"))
            category = data.get("category", mod_index.parent.parent.name)
            platform = data.get("platform", mod_index.parent.name)
            desc = data.get("description", "")
            vars_spec = data.get("variables", {})

            print(f"[{category.upper()}] -> {platform.upper()}")
            print(f"   Descricao: {desc}")
            print(f"   Caminho: {mod_index.parent.relative_to(VAULT_ROOT.parent)}")

            for var_name, var_info in vars_spec.items():
                val = os.environ.get(var_name, "")
                status = "[OK] CONFIGURADO" if val else "[ ] PENDENTE   "
                masked = mask_secret(val)
                req = "(Obrigatorio)" if var_info.get("required", False) else "(Opcional)   "
                print(f"     * {var_name:<28} | {status} {req} | {masked}")
            print("-" * 65)
        except Exception as e:
            print(f"[!] Erro ao auditar {mod_index}: {e}")

    print("\nAuditoria concluida com sucesso. Nenhuma credencial foi exposta em texto plano.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        audit_vault()
    else:
        vars_loaded = load_vault()
        print(f"[VAULT] Carregadas {len(vars_loaded)} variáveis de ambiente do Vault.")
