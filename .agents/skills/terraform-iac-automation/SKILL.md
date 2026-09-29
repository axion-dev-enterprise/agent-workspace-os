---
name: terraform-iac-automation
description: >-
  Operational engineering skill for declarative Infrastructure as Code with Terraform, HashiCorp HCL, remote state locking, blast radius control, and modular cloud provisioning.
---

# Terraform Infrastructure as Code (IaC) Engineering Skill

Guia operacional para arquitetura, estruturação modular, locking de estado remoto e execução segura de automações com Terraform e OpenTofu.

---

## 1. Topologia de Arquitetura de Módulos

Estruture qualquer raiz de projeto Terraform conforme o layout padronizado:
```
infra/
├── versions.tf          # Versão mínima do Terraform e providers pinados
├── backend.tf           # Configuração de estado remoto com locking
├── variables.tf         # Definições com tipo, validação e descrição
├── outputs.tf           # Valores expostos (com 'sensitive = true' se credenciais)
├── main.tf              # Composição principal e invocação de módulos
└── modules/             # Módulos reutilizáveis
    ├── vpc/
    └── database/
```

### 1.1 Pinagem de Versões (`versions.tf`)
Sempre fixe limites estritos para evitar breaking changes automáticas em CI:
```hcl
terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40.0"
    }
  }
}
```

---

## 2. Remote State & Locking

Nunca persista `terraform.tfstate` no disco local ou em controle de versão Git.

### 2.1 Backend S3 + DynamoDB / Cloudflare R2
```hcl
terraform {
  backend "s3" {
    bucket         = "enterprise-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

---

## 3. Blast Radius Control & Lifecycle

### 3.1 Prevenção de Destruição Acidental
Em recursos com estado persistente crítico (bancos de dados, buckets de dados históricos, discos de armazenamento), declare obrigatoriamente:
```hcl
resource "aws_db_instance" "primary" {
  identifier        = "prod-primary-db"
  allocated_storage = 50
  engine            = "postgres"
  # ...

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [allocated_storage]
  }
}
```

### 3.2 Create Before Destroy
Para recursos de rede ou certificados TLS onde downtime durante substituição causaria indisponibilidade:
```hcl
lifecycle {
  create_before_destroy = true
}
```

---

## 4. Pipeline de Execução & CLI Runbook

Siga estritamente o ciclo de 4 etapas para qualquer mutação de infraestrutura:

```powershell
# 1. Formatação e validação de sintaxe
terraform fmt -check -recursive
terraform validate

# 2. Geração do plano binário determinístico
terraform plan -out=tfplan.binary

# 3. Inspeção humana/agêntica do plano
terraform show -no-color tfplan.binary

# 4. Aplicação estrita do arquivo de plano (elimina race condition entre plan e apply)
terraform apply tfplan.binary
Remove-Item tfplan.binary
```

---

## 5. Ferramental Integrado

Audite o diretório de infraestrutura antes de commits com o linter embutido:
```powershell
python .agents/skills/terraform-iac-automation/scripts/terraform_hygiene_guard.py <pasta-do-projeto>
```
O linter valida:
- Credenciais e tokens estáticos hardcoded em arquivos `.tf`.
- Ausência de `prevent_destroy = true` em recursos críticos (RDS, S3, SQL).
- Variáveis sem tipo ou descrição explícita.
