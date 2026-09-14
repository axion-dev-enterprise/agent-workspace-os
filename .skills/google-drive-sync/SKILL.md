---
name: google-drive-sync
description: Operações de sincronização de atas, transcrições de reuniões e documentos do Google Drive para o Agent Workspace OS.
---

# Google Drive Sync

## Visão Geral
Permite que os agentes de IA leiam documentos recentes, transcrições de reuniões do Google Meet e pautas salvas no Google Drive.

## Estrutura de Credenciais
1. Obter arquivo de credenciais da Conta de Serviço no Google Cloud Console.
2. Salvar em `credentials/google_service_account.json` (adicionado ao `.gitignore`).
3. Compartilhar a pasta de trabalho do Google Drive com o email da Conta de Serviço.

## Comandos Operacionais
- **Verificar autenticação**:
  ```bash
  python scripts/google_drive_sync.py --check
  ```
- **Listar arquivos das últimas 24h**:
  ```bash
  python scripts/google_drive_sync.py --list
  ```
- **Sincronizar transcrições para o inbox**:
  ```bash
  python scripts/google_drive_sync.py --sync
  ```
