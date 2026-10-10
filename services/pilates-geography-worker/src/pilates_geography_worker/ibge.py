"""Adaptador de leitura para o catálogo oficial de municípios do IBGE."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import random
import socket
import time
import urllib.request
from datetime import UTC, datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError

from .domain import AdministrativeArea, AdministrativeAreaKind, Municipality


IBGE_MUNICIPALITIES_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
)
IBGE_DISTRICTS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/distritos?orderBy=nome"
)
IBGE_SUBDISTRICTS_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/subdistritos?orderBy=nome"
)
IBGE_POPULATION_URL = (
    "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last?formato=json"
)
USER_AGENT = "AXION-Pilates-Geography-Worker/0.2 (official public IBGE API client)"
MAX_COMPRESSED_BYTES = 20 * 1024 * 1024
MAX_RESPONSE_BYTES = 80 * 1024 * 1024
MAX_ATTEMPTS = 4
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


def _fetch_json(url: str, timeout_seconds: float) -> tuple[object, bytes]:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                if response.status != 200:
                    raise RuntimeError(f"IBGE respondeu HTTP {response.status}")
                compressed = response.read(MAX_COMPRESSED_BYTES + 1)
                if len(compressed) > MAX_COMPRESSED_BYTES:
                    raise ValueError("resposta comprimida excedeu 20 MiB")
                is_gzip = (
                    response.headers.get("Content-Encoding", "").lower() == "gzip"
                    or compressed.startswith(bytes((0x1F, 0x8B)))
                )
                if is_gzip:
                    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
                        raw = stream.read(MAX_RESPONSE_BYTES + 1)
                else:
                    raw = compressed
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("resposta descompactada excedeu 80 MiB")
            return json.loads(raw), raw
        except HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_HTTP_STATUSES:
                raise RuntimeError(f"IBGE respondeu HTTP {error.code}") from error
            delay = _retry_delay(attempt, error.headers.get("Retry-After"))
        except (URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as error:
            last_error = error
            delay = _retry_delay(attempt, None)
        if attempt + 1 < MAX_ATTEMPTS:
            time.sleep(delay)
    raise RuntimeError(f"falha temporária após {MAX_ATTEMPTS} tentativas: {type(last_error).__name__}") from last_error


def _retry_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(60.0, max(0.0, float(retry_after)))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return min(60.0, max(0.0, (retry_at - datetime.now(UTC)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                pass
    return min(30.0, (2**attempt) + random.uniform(0.25, 0.75))


class IbgeMunicipalitySource:
    """Baixa e valida um snapshot nacional sem consultar geolocalização pessoal."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.collected_at: datetime | None = None
        self.payload_sha256: str | None = None

    def fetch_municipalities(self) -> tuple[Municipality, ...]:
        payload, raw = _fetch_json(IBGE_MUNICIPALITIES_URL, self.timeout_seconds)
        if not isinstance(payload, list) or len(payload) < 5_000:
            raise ValueError("catálogo IBGE inválido ou incompleto")

        municipalities: list[Municipality] = []
        for record in payload:
            try:
                microregion = record.get("microrregiao")
                if isinstance(microregion, dict) and isinstance(
                    microregion.get("mesorregiao"), dict
                ):
                    hierarchy = microregion["mesorregiao"]["UF"]
                else:
                    immediate = record["regiao-imediata"]
                    hierarchy = immediate["regiao-intermediaria"]["UF"]
                municipality = Municipality(
                    ibge_code=str(record["id"]),
                    name=str(record["nome"]).strip(),
                    state_code=str(hierarchy["sigla"]).strip(),
                    state_name=str(hierarchy["nome"]).strip(),
                )
                if len(str(hierarchy["sigla"])) != 2:
                    raise ValueError("sigla de UF inválida")
                municipalities.append(municipality)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("registro do catálogo IBGE fora do formato esperado") from error

        codes = [row.ibge_code for row in municipalities]
        if len(codes) != len(set(codes)):
            raise ValueError("IBGE retornou códigos municipais duplicados")
        if len({row.state_code for row in municipalities}) != 27:
            raise ValueError("catálogo municipal IBGE não cobre as 27 UFs")

        self.collected_at = datetime.now(UTC)
        self.payload_sha256 = hashlib.sha256(raw).hexdigest()
        return tuple(municipalities)


class IbgePopulationSource:
    """Lê a estimativa populacional mais recente publicada na tabela SIDRA 6579."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.collected_at: datetime | None = None
        self.payload_sha256: str | None = None
        self.reference_year: int | None = None

    def fetch_population(self) -> dict[str, int]:
        payload, raw = _fetch_json(IBGE_POPULATION_URL, self.timeout_seconds)
        if not isinstance(payload, list) or len(payload) < 5_001:
            raise ValueError("série populacional SIDRA inválida ou incompleta")
        header = payload[0]
        if not isinstance(header, dict) or header.get("D1C") != "Município (Código)":
            raise ValueError("cabeçalho SIDRA não corresponde ao nível municipal")

        values: dict[str, int] = {}
        years: set[int] = set()
        for record in payload[1:]:
            try:
                code = str(record["D1C"])
                year = int(record["D3C"])
                population = int(record["V"])
                if (
                    len(code) != 7
                    or not code.isdigit()
                    or record["D2C"] != "9324"
                    or population < 0
                ):
                    raise ValueError("código, variável ou população inválida")
                if code in values:
                    raise ValueError("código municipal SIDRA duplicado")
                values[code] = population
                years.add(year)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("registro populacional SIDRA fora do formato esperado") from error

        if len(values) < 5_000 or len(years) != 1:
            raise ValueError("série populacional SIDRA incompleta ou com períodos misturados")
        self.collected_at = datetime.now(UTC)
        self.payload_sha256 = hashlib.sha256(raw).hexdigest()
        self.reference_year = years.pop()
        return values


class IbgeAdministrativeAreaSource:
    """Coleta distritos e subdistritos oficiais sem classificá-los como zonas."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.provenance: dict[str, tuple[datetime, str, int]] = {}

    def fetch_areas(self, municipality_codes: set[str]) -> tuple[AdministrativeArea, ...]:
        districts = self._fetch_level(
            IBGE_DISTRICTS_URL, AdministrativeAreaKind.DISTRICT, municipality_codes
        )
        districts_by_code = {row.ibge_code: row for row in districts}
        subdistricts = self._fetch_level(
            IBGE_SUBDISTRICTS_URL,
            AdministrativeAreaKind.SUBDISTRICT,
            municipality_codes,
            districts_by_code,
        )
        return tuple((*districts, *subdistricts))

    def _fetch_level(
        self,
        url: str,
        kind: AdministrativeAreaKind,
        municipality_codes: set[str],
        districts_by_code: dict[str, AdministrativeArea] | None = None,
    ) -> tuple[AdministrativeArea, ...]:
        payload, raw = _fetch_json(url, self.timeout_seconds)
        minimum = 5_000 if kind is AdministrativeAreaKind.DISTRICT else 300
        if not isinstance(payload, list) or len(payload) < minimum:
            raise ValueError(f"catálogo IBGE de {kind.value} inválido ou incompleto")

        areas: list[AdministrativeArea] = []
        for record in payload:
            try:
                if kind is AdministrativeAreaKind.DISTRICT:
                    municipality = record["municipio"]
                    parent_code = None
                else:
                    district = record["distrito"]
                    municipality = district["municipio"]
                    parent_code = str(district["id"])
                    if districts_by_code is None or parent_code not in districts_by_code:
                        raise ValueError("subdistrito sem distrito correspondente")
                municipality_code = str(municipality["id"])
                area = AdministrativeArea(
                    ibge_code=str(record["id"]),
                    municipality_ibge_code=municipality_code,
                    name=str(record["nome"]).strip(),
                    kind=kind,
                    parent_ibge_code=parent_code,
                )
                if municipality_code not in municipality_codes:
                    raise ValueError("divisão administrativa sem município do catálogo")
                if (
                    kind is AdministrativeAreaKind.SUBDISTRICT
                    and districts_by_code[parent_code].municipality_ibge_code != municipality_code
                ):
                    raise ValueError("subdistrito aponta para distrito de outro município")
                areas.append(area)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"registro IBGE de {kind.value} fora do formato esperado"
                ) from error

        codes = [row.ibge_code for row in areas]
        if len(codes) != len(set(codes)):
            raise ValueError(f"códigos IBGE duplicados em {kind.value}")
        self.provenance[url] = (datetime.now(UTC), hashlib.sha256(raw).hexdigest(), len(areas))
        return tuple(areas)
