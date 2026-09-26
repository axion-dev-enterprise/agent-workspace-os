---
name: windows-hardware-performance-tuning
description: >-
  Operational engineering skill for Windows kernel, hardware, CPU, RAM, GPU, network driver,
  and I/O performance tuning. Covers Realtek PCIe GbE NDIS 10400 crash resolution, AMD Radeon
  ULPS disablement, FlipQueueSize input lag mitigation, DisablePagingExecutive RAM locking,
  static SSD pagefile sizing, NTFS 8.3 overhead elimination, and MSI Mode DPC latency optimization.
---

# Windows Hardware & System Performance Tuning — Manual Operacional do Agente

Guia canônico e referência operacional para auditoria, diagnóstico de kernel/drivers, resolução de quedas de rede (NDIS), calibração de GPU/CPU, gerenciamento de RAM e otimização de I/O em estações de trabalho e nós de computação Windows 10/11.

---

## 1. Matriz de Diagnóstico & Causa Raiz

| Subsistema | Sintoma Comum | Causa Raiz Típica | Comando / Solução Canônica |
| :--- | :--- | :--- | :--- |
| **Rede (NIC)** | Resets cíclicos a cada ~27s (`NDIS 10400`) | Driver genérico inbox da Microsoft (2015) com bug de ASPM/EEE | Instalar driver oficial Realtek v10.x; desativar EEE, Green Ethernet e Power Saving |
| **GPU (AMD)** | Micro-stutter em transição 2D/3D, telas pretas | `EnableUlps = 1` (Ultra Low Power State) ativo por padrão | Definir `EnableUlps = 0` na chave de classe de vídeo da GPU |
| **Latência de Entrada** | Atraso perceptível de mouse/clique em 3D | Fila de quadros pré-renderizados alta (`FlipQueueSize = 3`) | Fixar `FlipQueueSize = "1"` no registro da GPU |
| **Memória de Vídeo** | Quedas de FPS por "VRAM Choking" | Windows GameDVR alocando buffer oculto de gravação (~200MB) | Desativar `GameDVR_Enabled = 0` e política `AllowGameDVR = 0` |
| **Kernel / RAM** | Micro-congelamentos de interface ao trocar apps | Windows descarregando anel zero (Ring 0) para o disco | Ativar `DisablePagingExecutive = 1` no Memory Management |
| **Armazenamento** | Fragmentação de swap e overhead de resizing | Pagefile dinâmico com tamanho variável | Fixar `PagingFiles = "C:\pagefile.sys 4096 4096"` estático no SSD |
| **Sistema de Arquivos** | Lentidão em repositórios Git e `node_modules` | Criação de nomes curtos MS-DOS legados (8.3) no NTFS | Definir `NtfsDisable8dot3NameCreation = 1` no FileSystem |
| **Áudio / DPC Latency** | Estalidos no som sob carga pesada de CPU/disco | Controlador de áudio em linha de interrupção compartilhada | Ativar MSI Mode (`MSISupported = 1`) no dispositivo de áudio PCI |

---

## 2. Comandos Canônicos de Auditoria e Diagnóstico

### 2.1 Auditoria de Resets de Rede (NDIS Event 10400)
```powershell
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-NDIS'} -MaxEvents 30 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap
```

### 2.2 Auditoria de Driver Assinado e Hardware ID
```powershell
Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceClass -eq 'NET' } |
    Select-Object DeviceName, DriverVersion, DriverDate, DriverProviderName, InfName
```

### 2.3 Auditoria de Parâmetros de Memória e Paging
```powershell
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' |
    Select-Object DisablePagingExecutive, LargeSystemCache, PagingFiles
```

### 2.4 Auditoria de Modo MSI (Message Signaled Interrupts)
```powershell
# Inspecionar chaves MSI de dispositivos PCI
Get-ChildItem -Path "HKLM:\SYSTEM\CurrentControlSet\Enum\PCI\*\*\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties" |
    Get-ItemProperty | Select-Object PSPath, MSISupported
```

---

## 3. Protocolo de Mitigação & Calibração de Hardware

### 3.1 Estabilização do Adaptador de Rede Realtek (Evitar Quedas de Link)
Ao instalar o driver oficial Realtek (`10.x`), as seguintes chaves de hardware devem ser aplicadas na chave do adaptador (`HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}\<Index>`):
* `*EEE` = `"0"` (Energy Efficient Ethernet desativado)
* `*GreenEthernet` = `"0"` (Green Ethernet desativado)
* `*PowerSavingMode` = `"0"` (Power Saving Mode desativado)
* `*ReceiveBuffers` = `"1024"` (Buffer de recepção dobrado)
* `*TransmitBuffers` = `"512"` (Buffer de envio quadruplicado)
* `*RSS` = `"1"` com `*NumRssQueues` = `"4"` (Multiprocessamento por hardware)

### 3.2 Calibração da GPU AMD Radeon (Eliminar Stuttering e VRAM Bleed)
Na chave da GPU (`HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000`):
* `EnableUlps` = `dword:00000000` (Desativa suspensão de barramento PCIe)
* `FlipQueueSize` = `"1"` (Latência de clique mínima)
* `ShaderCache` = `"1"` (Cache persistente de shaders compilados no SSD)
* `DisableDMACopy` = `dword:00000000` (Acelera transferência DMA)

### 3.3 Liberação de VRAM via Desativação de GameDVR
```powershell
Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -Value 0 -Type DWord
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Name 'AppCaptureEnabled' -Value 0 -Type DWord
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR' -Name 'AllowGameDVR' -Value 0 -Type DWord
```

### 3.4 Travamento do Kernel na Memória RAM Física
```powershell
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' -Name 'DisablePagingExecutive' -Value 1 -Type DWord
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' -Name 'PagingFiles' -Value @("C:\pagefile.sys 4096 4096") -Type MultiString
```

### 3.5 Otimização de I/O de Sistema de Arquivos (NTFS)
```powershell
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'NtfsDisable8dot3NameCreation' -Value 1 -Type DWord
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'NtfsMemoryUsage' -Value 2 -Type DWord
```

---

## 4. Guardrails e Regras Rígidas de Segurança
* **Proibido Desativar Pagefile Totalmente:** O Windows NT requer espaço de endereço virtual reservado (*commit limit*); desativar o pagefile causa *Out of Memory* e travamentos de processos. Sempre fixar um tamanho estático no SSD de boot.
* **Proibido Retries Cegos em Falhas de Driver:** Caso um comando `pnputil /add-driver` ou `Set-NetAdapterAdvancedProperty` retorne erro de permissão ou `Access Denied`, identifique imediatamente a integridade do token (Medium vs High UAC) em vez de reexecutar repetidamente.
* **Preservação de TRIM em SSDs:** Nunca desative `DisableDeleteNotify` em discos de estado sólido (SATA ou NVMe).
