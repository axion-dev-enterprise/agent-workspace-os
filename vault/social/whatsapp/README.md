# WhatsApp Vault & Credenciais 💬

## 1. Finalidade
Permitir a comunicação de agentes e bridges com o ecossistema WhatsApp via Baileys multi-device.

## 2. Como Funciona
- O bridge do Baileys armazena os pares de chaves criptográficas em `auth_info_baileys/` (ignorado pelo Git).
- Este arquivo `.env` parametriza o número de telefone e códigos de pareamento se necessário.

## 3. Serviços que Consomem Este Módulo
- `scripts/whatsapp_bridge/`
