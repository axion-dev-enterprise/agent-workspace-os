"""Orquestração batch idempotente com escrita externa separada e explícita."""

from collections.abc import Iterable

from .domain import Municipality, ReviewState, ZoneCandidate
from .ports import (
    AppPublisher,
    ApprovedCandidateRepository,
    CandidateSource,
    MunicipalitySource,
    StagingRepository,
)


def refresh_municipality_catalog(
    source: MunicipalitySource, staging: StagingRepository
) -> int:
    """Importa o catálogo oficial para staging; não publica no app."""
    rows = tuple(source.fetch_municipalities())
    _ensure_unique_municipality_codes(rows)
    return staging.upsert_municipalities(rows)


def stage_zone_candidates(
    source: CandidateSource,
    municipalities: Iterable[Municipality],
    staging: StagingRepository,
) -> int:
    """Coleta e armazena candidatos com evidência, sem aprová-los."""
    catalog = tuple(municipalities)
    municipality_codes = {row.ibge_code for row in catalog}
    rows = tuple(source.fetch_candidates(catalog))
    for row in rows:
        if row.municipality_ibge_code not in municipality_codes:
            raise ValueError(f"município ausente do catálogo: {row.municipality_ibge_code}")
        if row.review_state is ReviewState.APPROVED:
            raise ValueError("fontes não podem aprovar candidatos durante a coleta")
    _ensure_unique_candidate_keys(rows)
    return staging.upsert_candidates(rows)


def publish_approved_candidates(
    repository: ApprovedCandidateRepository, publisher: AppPublisher
) -> int:
    """Publica somente itens aprovados por revisor humano no repositório do app."""
    rows = tuple(repository.list_approved_candidates())
    if any(row.review_state is not ReviewState.APPROVED for row in rows):
        raise ValueError("repositório retornou candidato ainda não aprovado")
    if any(not row.reviewer or not row.reviewed_at for row in rows):
        raise ValueError("aprovação sem revisor/data não pode ser publicada")
    return publisher.publish_approved(rows)


def _ensure_unique_municipality_codes(rows: tuple[Municipality, ...]) -> None:
    codes = [row.ibge_code for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("fonte retornou códigos IBGE duplicados")


def _ensure_unique_candidate_keys(rows: tuple[ZoneCandidate, ...]) -> None:
    keys = [(row.municipality_ibge_code, row.stable_source_id) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("fonte retornou IDs de candidato duplicados")
