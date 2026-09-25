---
name: terraform-iac-automation
description: >-
  Operational skill for declarative Infrastructure as Code with Terraform, HashiCorp HCL, remote state locking, and modular cloud provisioning.
---

# Terraform Infrastructure as Code (IaC) Skill

Skill operacional para provisionamento determinístico de nuvem com Terraform.

## 1. Princípios
- **Remote State Locking**: Manter o `terraform.tfstate` em bucket remoto (S3/GCS/Cloudflare R2) com bloqueio via DynamoDB ou nativo para evitar concorrência.
- **Zero Hardcoding**: Variáveis sensíveis e dinâmicas devem ser passadas via `.tfvars` ou variáveis de ambiente `TF_VAR_`.
- **Plano Antes de Aplicar**: Sempre rodar `terraform plan` e inspecionar o diff antes de `terraform apply`.
