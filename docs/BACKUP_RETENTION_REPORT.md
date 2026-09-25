# Relatório de Retenção & Rotação de Armazenamento Frio (E:\)

> **Última Execução**: 2026-09-25 02:14:44 (UTC: 2026-09-25T05:14:43.342633+00:00)  
> **Diretório Canônico**: `E:\backups\axion_enterprise\`  
> **Política Ativa**: Retenção Diária de 14 dias + Retenção Semanal de 90 dias + Cofres Permanentes  

---

## 1. Resumo Executivo da Unidade E:\

| Métrica | Valor | Descrição |
| :--- | :---: | :--- |
| **Backups Rotativos Ativos** | **1** | Backups diários e semanais íntegros dentro da janela de conformidade |
| **Cofres Permanentes / Descomissionamento** | **1** | Arquivos definitivos protegidos contra qualquer expiração |
| **Diretórios Prunados nesta Rodada** | **0** | Backups obsoletos excluídos de forma segura |
| **Volume Total em Disco** | **2517.33 MB** | Espaço total ocupado por todos os backups e repositórios |

---

## 2. Cofres Permanentes Protegidos (*Immutable Vaults*)

| Arquivo / Diretório | Tamanho (MB) | Propósito / Conteúdo Preservado | Status |
| :--- | :---: | :--- | :---: |
| **`decommission_juliana_vps_final_archive`** | **2.58 MB** | Snapshot final de desligamento (PostgreSQL 16 `hermes_db` + código `/opt/hermes`) | 🟢 **IMUTÁVEL** |

---

## 3. Backups Ativos em Conformidade

| Diretório | Data | Idade (dias) | Tamanho (MB) | Manifesto | Racional de Retenção |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`backup_2026-09-25`** | `2026-09-25` | 0d | 2514.75 MB | 🟢 Válido | Recente (0 dias <= 14d) |

---

## Conclusão da Rotina
A retenção e rotação automática assegura que a unidade secundária `E:\` mantenha redundância integral e histórico recuperável sem risco de saturação de disco.
