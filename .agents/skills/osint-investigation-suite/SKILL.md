---
name: osint-investigation-suite
description: >-
  Operational intelligence and reconnaissance skill for Open Source Intelligence (OSINT).
  Covers Sherlock username footprinting, ExifTool forensic metadata extraction, digital footfall
  mapping, passive reconnaissance, metadata stripping, and OPSEC guardrails.
---

# OSINT Investigation Suite — Manual Operacional do Agente

Guia canônico e referência de comandos para investigações defensivas de inteligência de fontes abertas (**OSINT**), reconhecimento passivo, mapeamento de pegada digital de *usernames*, extração e higienização forense de metadados em arquivos de mídia via **Sherlock**, **ExifTool** e utilitários complementares.

---

## 1. Tabela Rápida de Ferramentas e Comandos

| Ferramenta | Comando Canônico | Objetivo Operacional | Saída Típica |
| :--- | :--- | :--- | :--- |
| **Sherlock** | `sherlock <alvo>` | Busca de contas ativas em 400+ plataformas sociais e fóruns | Lista de URLs de perfis ativos |
| **ExifTool (Leitura)** | `exiftool -G -a -s <arquivo>` | Extração exaustiva de todos os metadados (GPS, câmera, timestamps) | Tabela estruturada de tags EXIF/XMP/IPTC |
| **ExifTool (GPS)** | `exiftool -gps* <arquivo>` | Filtragem rápida de dados de geolocalização e altitude | Coordenadas latitude/longitude |
| **ExifTool (Scrubbing)**| `exiftool -all= -overwrite_original <arquivo>` | Higienização forense: purga total de metadados de uma imagem | Arquivo limpo de rastros |
| **theHarvester** | `theHarvester -d <dominio> -b google,bing` | Coleta de e-mails, hosts, IPs e funcionários associados | Inventário de superfície exposta |

---

## 2. Detalhamento e Modos de Uso

### 2.1 Mapeamento de Presença Digital de Nomes de Usuário (Sherlock)
O Sherlock executa consultas assíncronas determinísticas para verificar se um identificador está registrado:

```bash
# Execução direta para um alvo específico
sherlock target_username

# Salvar relatório completo em arquivo texto e formato CSV
sherlock target_username --output target_report.txt --csv

# Executar com timeout restrito para evitar bloqueios de rede
sherlock target_username --timeout 5 --print-found
```

### 2.2 Auditoria e Análise Forense de Metadados (ExifTool)
O ExifTool permite dissecar arquivos binários sem alterar seus dados visuais:

```bash
# Inspecionar todos os metadados com nomes canônicos de tags
exiftool -a -u -g1 image.jpg

# Extrair data de criação original e modelo do sensor
exiftool -DateTimeOriginal -Model -Make image.jpg

# Higienização de documentos/fotos antes de publicação pública (Anti-Leak)
exiftool -all= -overwrite_original document.pdf
```

### 2.3 Investigação de Superfície e Pegada de Infraestrutura
Para mapear domínios corporativos sem gerar tráfego invasivo no alvo:
* Consultas via motores de busca públicos (Dorks / Google Hacking).
* Consulta de certificados SSL/TLS públicos via `crt.sh` para descoberta passiva de subdomínios.
* Consulta de registros WHOIS e blocos ASN via APIs de inteligência pública.

---

## 3. Diretrizes de Governança, OPSEC e Ética
* **Apenas Fontes Públicas e Autorizadas:** As investigações OSINT devem utilizar estritamente dados de acesso público, indexados e autorizados para auditoria e inteligência defensiva.
* **Proibição de Engenharia Social Ativa:** É terminantemente PROIBIDO para qualquer agente interagir com pessoas, criar perfis falsos ou enviar mensagens simuladas sem consentimento explícito e finalidade de teste homologada.
* **Isolamento de Identidade (OPSEC):** Ao coletar dados em plataformas que exigem requisições HTTP sucessivas, utilize VPN (*Proton VPN* / túnel isolado) para proteger o IP de origem contra perfilamento ou bloqueios de taxa (*rate limiting*).
* **Higienização de Relatórios:** Relatórios de inteligência não devem expor dados pessoais sensíveis não pertinentes à finalidade da auditoria técnica.
