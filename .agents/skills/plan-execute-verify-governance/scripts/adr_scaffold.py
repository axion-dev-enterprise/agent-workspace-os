#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adr_scaffold.py — Architectural Decision Record (ADR) Scaffold Generator
Zero-dependency, Python 3 stdlib only.
Standardizes architectural decision-making by creating structured, versioned records in docs/adr/.
"""

import sys
import os
import re
import argparse
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(r"C:\workspace")
ADR_DIR = WORKSPACE_ROOT / "docs" / "adr"

TEMPLATE = """# {adr_id}: {title}

- **Status**: {status}
- **Data**: {date}
- **Decisores**: {deciders}
- **Escopo**: {scope}

---

## 1. Contexto & Problema
{context}

---

## 2. Direcionadores de Decisão (Decision Drivers)
- [ ] Segurança e Isolamento de Superfície de Ataque
- [ ] Performance e Latência
- [ ] Simplicidade de Operação e Custo
- [ ] Manutenibilidade e Escalabilidade

---

## 3. Alternativas Consideradas

### Opção 1: {title} (Escolhida)
- **Vantagens**: 
  - 
- **Desvantagens**: 
  - 

### Opção 2: [Alternativa Descartada]
- **Motivo da rejeição**: 
  - 

---

## 4. Decisão Adotada
{decision}

### Justificativa:
Explique por que esta opção prevaleceu sobre as alternativas com base nos direcionadores acima.

---

## 5. Consequências & Trade-offs
- **Consequências Positivas**:
  - 
- **Consequências Negativas / Débito Técnico Aceito**:
  - 
- **Plano de Rollback / Contingência**:
  - 
"""

def get_next_adr_id() -> str:
    ADR_DIR.mkdir(parents=True, exist_ok=True)
    existing_files = list(ADR_DIR.glob("*.md"))
    indices = []
    
    for f in existing_files:
        match = re.match(r"^(\d{4})[-_]", f.name)
        if match:
            indices.append(int(match.group(1)))
            
    next_idx = max(indices, default=0) + 1
    return f"{next_idx:04d}"

def scaffold_adr(title: str, deciders: str = "Agente IA & Operador AXION", scope: str = "Workspace / Infraestrutura", status: str = "Accepted") -> Path:
    adr_id = get_next_adr_id()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    
    filename = f"{adr_id}_{slug}.md"
    file_path = ADR_DIR / filename
    
    content = TEMPLATE.format(
        adr_id=f"ADR-{adr_id}",
        title=title,
        status=status,
        date=date_str,
        deciders=deciders,
        scope=scope,
        context="Descreva o contexto do sistema, limitações atuais e a necessidade de decisão arquitetural.",
        decision=f"Decidido implementar: {title} conforme especificações canônicas."
    )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return file_path

def main():
    parser = argparse.ArgumentParser(description="Architectural Decision Record (ADR) Scaffold Generator")
    parser.add_argument("title", help="Title of the architectural decision (e.g., 'Uso de Cloudflare Zero Trust para Backends')")
    parser.add_argument("--scope", "-s", default="Workspace / Infraestrutura", help="Decision scope")
    parser.add_argument("--status", default="Accepted", choices=["Proposed", "Accepted", "Rejected", "Deprecated", "Superseded"])
    parser.add_argument("--deciders", "-d", default="Agente IA & Operador AXION", help="Deciders list")
    
    args = parser.parse_args()
    
    created_path = scaffold_adr(args.title, deciders=args.deciders, scope=args.scope, status=args.status)
    print(f"[ADR CRIADO] {created_path.name}")
    print(f"Caminho canônico: file:///{created_path.as_posix()}")

if __name__ == "__main__":
    main()
