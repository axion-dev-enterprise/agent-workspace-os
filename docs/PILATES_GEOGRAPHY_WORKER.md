# Worker geográfico do app Pilates

## VPS

- Host: `vps-node-01-aux-br`, Debian 13.7, Hostinger Brasil.
- Administração pela Tailnet: `100.99.201.3`; o SSH público segue bloqueado.
- Código ativo: `/opt/pilates-geography-worker`.
- Conta sem shell de login: `pilates-worker`.
- Staging: `/var/lib/pilates-geography-worker/staging.sqlite3`.
- Systemd: `pilates-geography-worker.service` e timer mensal `pilates-geography-worker.timer`.

## Release ativo na VPS

Em 2026-10-10, o release ativo consultou [IBGE Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome) e gravou 5.571 municípios de 27 UFs. Os códigos IBGE têm sete dígitos e são únicos; `PRAGMA integrity_check` retornou `ok`. O staging armazena proveniência e histórico do snapshot. A unidade termina com sucesso, roda com o usuário dedicado e o timer mensal está habilitado.

Não foram coletadas nem inferidas zonas e nenhum dado foi publicado no app. Ainda faltam fontes locais rastreáveis, regras comerciais confirmadas, repositório/schema do Pilates e revisão humana.

## População

A resposta mais recente de [SIDRA, tabela 6579, variável 9324](https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last?formato=json) foi verificada em 2026-10-10: período 2026, 5.571 códigos únicos.

## Extensão local em preparação

A extensão local foi executada em staging descartável e coletou 5.571 municípios, estimativas populacionais de 2026, 10.751 distritos e 646 subdistritos. Integridade SQLite retornou `ok`, sem violações de chave estrangeira nem áreas órfãs. Ela acrescenta repetição limitada com backoff, registro de falhas, proveniência por origem e gravação transacional com reconciliação de snapshots completos. Ainda precisa ser instalada remotamente; a credencial root não estava disponível no Vault durante o último preflight. Até esse deploy, o banco ativo permanece no estado documentado acima.

Distritos e subdistritos são referências administrativas para curadoria, não zonas comerciais aprovadas. A carga não publica dados no app nem inventa subdivisões de serviço.

## Operação

```bash
systemctl status pilates-geography-worker.service --no-pager
systemctl list-timers pilates-geography-worker.timer --no-pager
journalctl -u pilates-geography-worker.service -n 50 --no-pager
systemctl start pilates-geography-worker.service
```

O código está em `services/pilates-geography-worker/` e é mantido localmente pelo padrão `.gitignore` `services/pilates*`.
