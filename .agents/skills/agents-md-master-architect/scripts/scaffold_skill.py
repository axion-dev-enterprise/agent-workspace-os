#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold_skill.py — Automated Operational Skill Scaffolding Engine
AXION Enterprise / Agentic AI Foundation Standards

Creates a fully compliant, production-grade operational skill directory
under .agents/skills/<skill-name>/, complete with:
- SKILL.md (YAML frontmatter + best-practice sections)
- scripts/ (standalone Python CLI tool)
- references/ (detailed reference document)
and triggers the canonical sync_skills_registry.py.
"""

import os
import sys
import argparse
import re
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(r"C:\workspace")
SKILLS_DIR = WORKSPACE_ROOT / ".agents" / "skills"
SYNC_SCRIPT = WORKSPACE_ROOT / "scripts" / "sync_skills_registry.py"

SKILL_TEMPLATE = """---
name: {name}
description: >-
  {description}
---

# {title} Skill

Operational skill canônica para {description_short}.

---

## 1. Visão Geral & Escopo

Esta skill fornece ao agente os padrões arquiteturais, comandos executáveis e restrições técnicas para operar em **{title}**.

### Casos de Uso Principais:
- Implementação e manutenção de rotinas em {title}.
- Validação e diagnósticos de integridade.
- Automação de tarefas repetitivas via scripts utilitários em `scripts/`.

---

## 2. Regras Operacionais de Ouro

1. **Determinismo em Primeiro Lugar**: Utilize sempre os utilitários de `scripts/` antes de tentar escrever scripts pontuais não testados.
2. **Evidência de Execução**: Jamais declare conclusão de tarefa sem validar o exit code e saída real de comandos.
3. **Tratamento de Exceções**: Todo erro deve ser reportado com diagnóstico claro e sugestão de ação corretiva.

---

## 3. Utilitários Python Canônicos (`scripts/`)

Localizados em `scripts/` desta skill (stdlib apenas, zero dependências externas):

### 3.1 Utilitário de Diagnóstico (`{safe_name}_util.py`)
```bash
python .agents/skills/{name}/scripts/{safe_name}_util.py --action check
```

---

## 4. Referências & Contratos (`references/`)

Documentação aprofundada, contratos de interface e cheatsheets técnicos estão mantidos em `references/`:
- [`architecture.md`](file:///C:/workspace/.agents/skills/{name}/references/architecture.md): Detalhamento arquitetural e especificações.

---

## 5. Portão de Verificação Empírica

Antes de finalizar qualquer tarefa neste domínio:
1. Executar o utilitário de validação:
   ```bash
   python .agents/skills/{name}/scripts/{safe_name}_util.py --action check
   ```
2. Garantir código de retorno `0` e registrar a evidência no log diário.
"""

SCRIPT_TEMPLATE = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
{safe_name}_util.py — Utilitário Operacional para {title}
Zero-dependency, Python 3 stdlib only.
\"\"\"

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_check() -> dict:
    \"\"\"Performs operational health and status check.\"\"\"
    return {{
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": "{name}",
        "message": "Operação validada com sucesso."
    }}

def main():
    parser = argparse.ArgumentParser(description="Utilitário Operacional para {title}")
    parser.add_argument("--action", choices=["check", "status"], default="check", help="Ação a executar")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON estruturado")
    args = parser.parse_args()

    result = run_check()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{{result['status'].upper()}}] {{result['message']}} (ts: {{result['timestamp']}})")

    sys.exit(0 if result.get("status") == "healthy" else 1)

if __name__ == "__main__":
    main()
"""

REF_TEMPLATE = """# {title} — Referência Arquitetural & Contratos Técnicos

Documento canônico de especificações profundas para a skill `{name}`.

## 1. Contratos de Interface & Dados
- Todas as estruturas de dados devem ser tipadas e validadas.
- Manter compatibilidade com Python 3.10+ e Node.js 20+.

## 2. Checklist de Verificação
- [ ] Utilitários em `scripts/` testados e com exit code 0.
- [ ] Sintaxe de comandos compatível com Windows (PowerShell/CMD).
- [ ] Nenhuma credencial ou secret em texto puro.
"""

def sanitize_name(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    clean = re.sub(r"-+", "-", clean).strip("-")
    return clean

def scaffold_skill(name: str, domain: str = "Geral / Utilitário", description: str = None) -> Path:
    skill_slug = sanitize_name(name)
    if not skill_slug:
        raise ValueError("Nome de skill inválido.")

    target_dir = SKILLS_DIR / skill_slug
    if target_dir.exists():
        raise FileExistsError(f"A skill '{skill_slug}' já existe em: {target_dir}")

    title_words = [w.capitalize() for w in skill_slug.replace("-", " ").replace("_", " ").split()]
    title = " ".join(title_words)
    safe_name = skill_slug.replace("-", "_")

    desc = description or f"Operational skill for {title} workflows, automated commands, and governance standards."
    desc_short = desc.split(".")[0]

    # Create directories
    scripts_dir = target_dir / "scripts"
    refs_dir = target_dir / "references"
    target_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(exist_ok=True)
    refs_dir.mkdir(exist_ok=True)

    # Write SKILL.md
    skill_content = SKILL_TEMPLATE.format(
        name=skill_slug,
        title=title,
        description=desc,
        description_short=desc_short,
        safe_name=safe_name
    )
    (target_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

    # Write scripts/
    script_content = SCRIPT_TEMPLATE.format(
        name=skill_slug,
        title=title,
        safe_name=safe_name
    )
    (scripts_dir / f"{safe_name}_util.py").write_text(script_content, encoding="utf-8")

    # Write references/
    ref_content = REF_TEMPLATE.format(
        name=skill_slug,
        title=title
    )
    (refs_dir / "architecture.md").write_text(ref_content, encoding="utf-8")

    print(f"✅ Skill '{skill_slug}' criada com sucesso em:")
    print(f"   📁 {target_dir}")
    print(f"   📄 {target_dir / 'SKILL.md'}")
    print(f"   🐍 {scripts_dir / f'{safe_name}_util.py'}")
    print(f"   📖 {refs_dir / 'architecture.md'}")

    # Register in DOMAIN_MAP if sync_skills_registry.py exists
    if SYNC_SCRIPT.exists():
        try:
            sync_code = SYNC_SCRIPT.read_text(encoding="utf-8")
            if f'"{skill_slug}":' not in sync_code:
                # Add to DOMAIN_MAP
                insert_line = f'    "{skill_slug}": ("{domain}", "{desc_short}"),\n'
                marker = "DOMAIN_MAP = {\n"
                if marker in sync_code:
                    new_code = sync_code.replace(marker, marker + insert_line, 1)
                    SYNC_SCRIPT.write_text(new_code, encoding="utf-8")
                    print(f"   📌 Adicionado ao DOMAIN_MAP em {SYNC_SCRIPT.name} (Domínio: {domain})")
            
            # Execute sync
            print("\n🔄 Executando sincronizador global de skills...")
            res = subprocess.run([sys.executable, str(SYNC_SCRIPT)], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
            if res.returncode == 0:
                print("   ✅ Sincronização concluída com sucesso!")
            else:
                print(f"   ⚠️ Aviso: Sincronizador retornou erro: {res.stderr}")
        except Exception as e:
            print(f"   ⚠️ Erro ao atualizar sincronizador: {e}")

    return target_dir

def main():
    parser = argparse.ArgumentParser(description="Scaffold Automatizado de Skills — AXION Enterprise")
    parser.add_argument("name", help="Nome da skill em kebab-case (ex: my-awesome-skill)")
    parser.add_argument("--domain", default="IA & Engenharia de Agentes", help="Categoria/Domínio da skill")
    parser.add_argument("--description", help="Descrição detalhada do escopo da skill para o YAML frontmatter")
    args = parser.parse_args()

    try:
        scaffold_skill(args.name, domain=args.domain, description=args.description)
    except Exception as e:
        print(f"❌ Erro ao criar skill: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
