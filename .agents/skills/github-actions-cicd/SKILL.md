---
name: github-actions-cicd
description: >-
  Operational engineering skill for designing automated GitHub Actions CI/CD pipelines, dependency caching, OIDC secretless deployments, concurrency management, and supply-chain security.
---

# GitHub Actions CI/CD Engineering Skill

Guia operacional para arquitetura de pipelines automatizados, otimização de tempo de build, governança de privilégios mínimos e entrega contínua com GitHub Actions.

---

## 1. Princípios de Segurança e Privilégios Mínimos

### 1.1 Permissões Explícitas no Top-Level
Nunca deixe permissões implícitas em workflows. Por padrão, restrinja todo o pipeline a leitura e eleve apenas o job necessário:
```yaml
permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write    # Necessário para autenticação OIDC com AWS/GCP/Cloudflare
      pages: write       # Ou pull-requests: write para bots
```

### 1.2 Prevenção contra Script Injection
Nunca interpole variáveis de contexto de eventos não confiáveis (título de issue, corpo de PR, commits) diretamente no bloco `run:`. Passe sempre por variáveis de ambiente intermediárias:
```yaml
# Inseguro (vulnerável a injeção de comandos bash):
# run: echo "PR title: ${{ github.event.pull_request.title }}"

# Seguro:
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  echo "PR title: $PR_TITLE"
```

### 1.3 Fixação de Ações por Commit SHA
Para mitigar comprometimento de supply-chain em ações de terceiros, fixe o hash imutável:
```yaml
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

---

## 2. Otimização de Performance e Caching

### 2.1 Concorrência com Cancelamento em Pull Requests
Evite que commits sucessivos na mesma branch acumulem execuções desnecessárias na fila:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

### 2.2 Cache Determinado de Pacotes
Utilize o cache nativo das ações de setup ou `actions/cache`:
```yaml
# Node.js com pnpm
- uses: pnpm/action-setup@v3
  with:
    version: 9
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'pnpm'

# Python com uv/pip
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'
```

### 2.3 Filtros de Caminho (Path Filters)
Não execute pipelines pesados de compilação ou testes quando apenas documentações ou READMEs forem alterados:
```yaml
on:
  pull_request:
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - '.gitignore'
```

---

## 3. Matrizes de Testes e Deploys OIDC

### 3.1 Exemplo Canônico: Test Matrix Multi-Versão
```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install -e .[test]
      - run: pytest tests/
```

### 3.2 Deploy Secretless via OIDC (Cloudflare/AWS/GCP)
Dispense o uso de chaves permanentes de API (`AWS_ACCESS_KEY_ID` ou `CF_API_TOKEN` com prazo infinito):
```yaml
- name: Authenticate with Cloud Provider via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy-role
    aws-region: us-east-1
```

---

## 4. Ferramental Integrado

Audite workflows locais antes de commitar alterações em `.github/workflows/`:
```powershell
python .agents/skills/github-actions-cicd/scripts/workflow_linter.py <caminho-ou-workflows>
```
O linter valida:
- Ausência de declaração de permissões mínimas no topo.
- Ausência de cancelamento de concorrência em PRs.
- Risco de injeção de comandos bash em blocos `run:`.
- Tags mutáveis (`@master`, `@v1`) em ações de terceiros.
