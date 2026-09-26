---
name: gcp-cloud-ops
description: >-
  Operational skill for Google Cloud Platform (GCP) infrastructure management via gcloud CLI,
  Cloud Console, and APIs. Use when managing Cloud Run services, Secret Manager, Cloud Storage buckets,
  Artifact Registry, IAM permissions, Service Accounts, and Organization Policies for example.com.
---

# Google Cloud Platform (GCP) Operations Skill

Skill operacional para administração de projetos, serviços serverless, gestão de segredos e políticas organizacionais no Google Cloud Platform para a **AXION Enterprise**.

---

## 1. Projetos & Identificadores Centrais

- **Projeto GAM Primário**: `gam-project-w1te0`
- **Organização**: `example.com`
- **Região Canônica Padrão**: `southamerica-east1` (São Paulo, Brasil) ou `us-central1`

---

## 2. Comandos Essenciais via `gcloud` CLI

### 2.1 Gestão de Projetos e Autenticação
```powershell
# Listar projetos acessíveis pela conta atual
gcloud projects list

# Definir o projeto padrão da sessão
gcloud config set project gam-project-w1te0

# Autenticar nova sessão admin
gcloud auth login iago@example.com
```

### 2.2 Secret Manager (Armazenamento Seguro de Tokens)
```powershell
# Criar um novo segredo
gcloud secrets create AXION_MASTER_KEY --replication-policy="automatic"

# Adicionar versão/valor do segredo
"valor_secreto_aqui" | gcloud secrets versions add AXION_MASTER_KEY --data-file=-

# Acessar valor do segredo
gcloud secrets versions access latest --secret="AXION_MASTER_KEY"
```

### 2.3 Cloud Run (Deploy de Microserviços Serverless)
```powershell
# Listar serviços ativos
gcloud run services list

# Deploy de container a partir do Artifact Registry
gcloud run deploy axion-main-api `
  --image southamerica-east1-docker.pkg.dev/gam-project-w1te0/axion-repo/api:latest `
  --region southamerica-east1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1
```

### 2.4 Cloud Storage (Buckets GCS)
```powershell
# Listar buckets
gcloud storage buckets list

# Fazer upload de diretório sincronizado
gcloud storage rsync -r ./backups gs://axion-enterprise-backups/
```

---

## 3. Gestão de Políticas da Organização (Org Policies)

Como observado na ativação do GAM, a organização possui restrições de segurança que podem requerer regras personalizadas:

* **Upload de chaves privadas**: `constraints/iam.disableServiceAccountKeyUpload`
* **Criação de chaves**: `constraints/iam.disableServiceAccountKeyCreation`

Para desativar uma restrição em um projeto específico:
```powershell
# Regra personalizada com enforce = false no projeto
gcloud org-policies set-policy policy.yaml --project=gam-project-w1te0
```
