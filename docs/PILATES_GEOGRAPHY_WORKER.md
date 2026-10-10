# Worker geográfico do app Pilates

## Objetivo e limites

O worker mantém um catálogo oficial de municípios para orientar a curadoria
geográfica do app Pilates. Dados ficam em staging e não são publicados no app
automaticamente. Candidatos de zonas só devem entrar após identificação de uma
fonte municipal/estadual rastreável e confirmação humana das regras comerciais.
Não consultar GPS, inferir zonas a partir de bairros ou divisões regionais do
IBGE, nem varrer o Nominatim público.

## VPS e execução

- Host: `vps-node-01-aux-br` (Hostinger, Brasil), Debian 13.7.
- Endereço de administração: Tailnet `100.99.201.3`; SSH público permanece
  bloqueado pelo firewall.
- Código instalado: `/opt/pilates-geography-worker`.
- Conta de serviço: `pilates-worker` (sem shell de login).
- Staging SQLite: `/var/lib/pilates-geography-worker/staging.sqlite3`.
- Unidade: `pilates-geography-worker.service`; timer mensal
  `pilates-geography-worker.timer`.
- Recursos limitados no systemd: 1 CPU e 512 MiB; diretório gravável restrito ao
  staging.

## Fontes e estado da carga

O release ativo consulta [IBGE Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome)
para código, nome e UF. No primeiro ciclo confirmado, em 2026-10-10, gravou
5.571 municípios de 27 UFs. O banco retornou `integrity_check=ok`; os códigos
tinham sete dígitos e eram únicos. A carga usa upsert pelo código IBGE e guarda
URL e horário da fonte, mais histórico do snapshot.

O timer está habilitado para atualizar mensalmente. A execução permanece
isolada em staging e não tem credenciais nem adaptador do Supabase.

O worker local contém uma extensão para unir a população SIDRA mais recente à
lista por código IBGE. A resposta oficial de
[SIDRA, tabela 6579 e variável 9324](https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last?formato=json)
foi consultada durante esta tarefa e retornou 5.571 códigos únicos no período
2026. Essa extensão ainda não foi instalada na VPS, pois a credencial de acesso
que estava no Vault não estava disponível durante a segunda etapa. Portanto, o
banco ativo ainda não contém estimativas populacionais.

Nenhuma zona foi coletada ou criada nesta etapa. O catálogo municipal não
resolve, por si só, a taxonomia de deslocamento do app.

## Operação

```bash
systemctl status pilates-geography-worker.service --no-pager
systemctl list-timers pilates-geography-worker.timer --no-pager
journalctl -u pilates-geography-worker.service -n 50 --no-pager
```

O código local está sob `services/pilates-geography-worker/`. O padrão
`.gitignore` `services/pilates*` mantém esse pacote somente neste workspace.
Para integrar ao app, ainda são necessários o repositório/schema Pilates, a
política de atualização e o fluxo de aprovação humana.
