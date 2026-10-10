# Worker de geografia para o app de Pilates

Worker batch para manter o catálogo de municípios brasileiros e preparar zonas
locais reconhecíveis para filtros de deslocamento profissional. Este pacote é
independente do app até receber o repositório e o contrato real do Supabase.

## Fluxo

```text
catálogos oficiais, indicadores e fontes locais rastreáveis
        ↓
adaptadores de municípios, população e divisões administrativas
        ↓
validação e normalização por código IBGE
        ↓
staging idempotente + proveniência
        ↓
fila de revisão humana
        ↓ somente registros aprovados
adaptador do schema do app / Supabase
```

Cada execução deve ser reprocessável: município usa o código IBGE como chave;
candidato de zona usa município + identificador estável da fonte + versão da
fonte. O worker não publica candidatos diretamente e não mantém credenciais do
Supabase neste pacote.

## Contratos de domínio

- **Município:** código IBGE, nome oficial, UF e população acompanhada do ano e
  da data de referência. O catálogo completo é ordenado por população para
  orientar a curadoria, sem excluir municípios menores.
- **Zona:** seleção municipal ampla (`citywide`) ou subdivisão reconhecida e
  documentada (`recognized_zone`). A nomenclatura final precisa ser validada
  com o produto e com o app.
- **Cobertura municipal:** `unmapped`, `verified_no_subdivisions`,
  `mapped_pending_review` ou `mapped_approved`. Ausência de dados nunca significa
  que a cidade não tem subdivisões. A revisão de cada candidato de zona tem um
  estado próprio (`pending_review` ou `approved`).
- **Proveniência:** cada candidato carrega fonte, URL, data de coleta e trecho ou
  referência que permita revisão. Não se gera zona por inferência geográfica.

## Regras do produto

1. Não consultar GPS nem localização em tempo real no app.
2. Não tratar bairros nem regiões geográficas do IBGE (macro, micro, imediata ou
   intermediária) como zonas comerciais do produto.
3. Permitir uma cidade inteira quando fizer sentido; subdividir apenas quando
   fontes locais ou revisão humana confirmarem nomes usados no deslocamento.
4. Manter a curadoria em estados explícitos e exigir aprovação humana antes da
   publicação.
5. Para fontes OSM, usar extratos/arquivos apropriados, respeitar atribuição e
   licença; não varrer o Nominatim público para baixar listas sistematicamente.

## Fontes previstas

- [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades):
  identidade oficial de municípios, UF, distritos e subdistritos.
- [API de distritos](https://servicodados.ibge.gov.br/api/v1/localidades/distritos?orderBy=nome)
  e [subdistritos](https://servicodados.ibge.gov.br/api/v1/localidades/subdistritos?orderBy=nome):
  divisões administrativas ligadas aos municípios por códigos IBGE.
- [SIDRA, tabela 6579, variável 9324](https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last?formato=json):
  estimativa populacional mais recente publicada, com período registrado no
  staging.
- Fontes municipais/estaduais e referências locais rastreáveis: evidência para
  nomes e limites de zonas, sempre sujeita à revisão.

Referências: [API de Localidades do IBGE](https://servicodados.ibge.gov.br/api/docs/localidades),
[estimativas populacionais do IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-population.html),
[política do Nominatim](https://operations.osmfoundation.org/policies/nominatim/).

## Estrutura

- `src/pilates_geography_worker/domain.py`: entidades e estados válidos,
  mantendo cobertura municipal separada da aprovação de zonas.
- `src/pilates_geography_worker/ports.py`: contratos para fontes, staging,
  revisão e publicação.
- `src/pilates_geography_worker/pipeline.py`: coordenação sem acoplamento a
  banco, API ou provedor específico.

## Próxima integração

Antes de implementar adaptadores concretos, obter o repositório/schema do app e
confirmar nomes de tabelas, chaves, política de atualização e processo de
aprovação. O primeiro corte deve importar catálogo e população para staging;
depois preparar candidatos de capitais e casos-piloto (por exemplo, São Paulo,
Santo André e São Caetano do Sul) sem publicar rótulos ainda não confirmados.

## Coleta inicial e execução

Os adaptadores consultam o catálogo oficial de municípios, a série mais recente
de estimativas populacionais da tabela 6579 do SIDRA e os catálogos de distritos
e subdistritos do IBGE. Cada divisão é ligada ao município e, no subdistrito,
ao distrito pai por códigos oficiais. A população é associada estritamente pelo
código IBGE; divergência, duplicidade ou referência órfã aborta a carga. Cada
origem mantém URL, horário UTC, contagem e SHA-256 em `collection_runs`; falhas
também ficam registradas sem substituir o snapshot válido anterior. Os endpoints
podem responder com gzip; o adaptador valida o payload, tamanho e unicidade
antes da gravação. Requisições transitórias têm timeout, até quatro tentativas
com recuo exponencial e respeito a `Retry-After`. Os quatro datasets são gravados
em uma transação SQLite; snapshots completos reconciliam remoções somente depois
que todos passaram pelas validações. Se um município não tiver a antiga
microrregião no retorno, a UF é resolvida pela hierarquia região
imediata/intermediária.

Distritos e subdistritos são referências administrativas para curadoria, não
zonas comerciais automaticamente válidas para o Pilates. A aplicação ainda
exige definição de produto, fonte local e revisão humana antes de qualquer
publicação. Nenhuma coleta de zonas comerciais ocorre neste estágio.

```bash
PYTHONPATH=src python -m pilates_geography_worker refresh-catalog \
  --database ./temp/pilates-geography-staging.sqlite3
```

`refresh-municipalities` continua disponível como alias para compatibilidade
com a primeira instalação.

Na VPS, o serviço systemd grava em
`/var/lib/pilates-geography-worker/staging.sqlite3`; o timer agenda atualização
mensal. A execução inicial é disparada separadamente durante a instalação.
Nenhum dado é publicado no app. A coleta de zonas permanece desativada até
existirem fontes municipais/estaduais rastreáveis e confirmação dos nomes e
regras comerciais. Não se consulta GPS, não se varre o Nominatim público e não
se infere bairros ou regiões do IBGE como zonas de produto.

Para conectar o staging ao app, ainda é necessário receber o repositório/schema
do Pilates, política de atualização e processo de aprovação humana. A
credencial do app não deve ser colocada neste worker.
