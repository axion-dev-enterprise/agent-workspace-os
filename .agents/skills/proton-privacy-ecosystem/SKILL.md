---
name: proton-privacy-ecosystem
description: >-
  Operational privacy and encryption skill for the Proton ecosystem (Proton VPN, Proton Drive,
  Proton Pass, Proton Mail) and client-side cloud encryption with Cryptomator and Rclone.
  Covers WireGuard protocol, Kill Switch, DNS leak protection, zero-knowledge storage, and
  encrypted cloud synchronization workflows.
---

# Proton Privacy Ecosystem & Encrypted Storage — Manual Operacional do Agente

Guia canônico e referência de operações para blindagem de tráfego, anonimato de rede, armazenamento em nuvem com criptografia de ponta a ponta (*zero-knowledge*) e proteção de dados confidenciais utilizando a infraestrutura suíça da **rede Proton** combinada com **Cryptomator** e **Rclone**.

---

## 1. Topologia do Ecossistema Proton & Segurança

| Ferramenta | Camada de Atuação | Padrão Criptográfico | Caso de Uso Canônico |
| :--- | :--- | :--- | :--- |
| **Proton VPN** | Rede & Tráfego | WireGuard / ChaCha20, AES-256 | Tunelamento criptografado, mascaramento de IP, evasão de censura e tráfego anônimo |
| **Proton Drive** | Armazenamento Nuvem | OpenPGP (ECC Curve25519) | Armazenamento de arquivos corporativos confidenciais sem acesso de terceiros |
| **Cryptomator** | Cofre Local / Nuvem | AES-256-GCM / Scrypt | Criptografia de arquivos no dispositivo antes do upload para Google Drive ou OneDrive |
| **Rclone** | Sincronização CLI | Criptografia sob demanda (`rclone crypt`) | Transferência programática automatizada em esteiras de backup e pipelines |

---

## 2. Comandos Canônicos e Procedimentos Operacionais

### 2.1 Instalação e Atualização Automatizada (Winget)
```powershell
# Instalação dos clientes de privacidade e armazenamento seguro
winget install Proton.ProtonVPN --silent --accept-package-agreements --accept-source-agreements
winget install Proton.ProtonDrive --silent --accept-package-agreements --accept-source-agreements
winget install Cryptomator.Cryptomator --silent --accept-package-agreements --accept-source-agreements
winget install Rclone.Rclone --silent --accept-package-agreements --accept-source-agreements
```

### 2.2 Verificação de Status do Proton VPN e Proteção de DNS
Antes de iniciar tarefas confidenciais, auditar a ausência de vazamento de DNS e IP real:
```powershell
# Inspecionar endereço IPv4 e geolocalização pública via endpoint seguro
curl.exe -s -L "https://api.ipify.org"
curl.exe -s -L "https://ipinfo.io/json"
```

### 2.3 Integração Rclone com Armazenamento Criptografado (`rclone crypt`)
Para sincronizar backups corporativos ou dados de inteligência sem exposição:
```bash
# Configuração interativa de remotes seguros
rclone config

# Exemplo de sincronização de diretório local para cofre remoto criptografado
rclone sync "C:/workspace/backups" "secure_remote:enc_backups" --transfers 4 --checkers 8 -P
```

### 2.4 Operação do Cryptomator com Google Drive
1. Inicializar o cliente do **Cryptomator**.
2. Criar um novo cofre apontando o caminho físico para o diretório sincronizado do Google Drive (ex: `G:\Meu Drive\CofreSeguro`).
3. Definir uma senha mestra forte e armazenar a chave de recuperação fora da nuvem.
4. Os arquivos copiados para o drive virtual montado são criptografados em blocos individuais (AES-256) antes que o cliente da nuvem os detecte e sincronize.

---

## 3. Diretrizes de Governança e OPSEC
* **Kill Switch Sempre Ativo:** Nunca operar o Proton VPN em redes não confiáveis sem o recurso *Kill Switch* habilitado. Caso a conexão com o túnel caia, o tráfego deve ser bloqueado na camada de interface física para evitar vazamento do IP real da infraestrutura.
* **Proibição de Registro de Chaves e Senhas:** É expressamente PROIBIDO registrar senhas de cofres Cryptomator ou tokens de sessão Proton em logs do console, arquivos de memória (`memory/cowork/blackboard.json`) ou repositórios Git versionados.
* **Auditoria de DNS Leaks:** Certificar-se de que os adaptadores virtuais do Proton VPN (`ProtonVPN TUN / TAP / WireGuard`) assumem a prioridade de resolução DNS enquanto ativos, impedindo consultas via DNS da operadora local.
