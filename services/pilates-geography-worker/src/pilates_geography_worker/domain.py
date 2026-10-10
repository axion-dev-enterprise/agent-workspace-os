"""Tipos centrais do domínio, sem dependência do schema do app."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class CoverageState(StrEnum):
    UNMAPPED = "unmapped"
    VERIFIED_NO_SUBDIVISIONS = "verified_no_subdivisions"
    MAPPED_PENDING_REVIEW = "mapped_pending_review"
    MAPPED_APPROVED = "mapped_approved"


class ReviewState(StrEnum):
    PENDING = "pending_review"
    APPROVED = "approved"


class ZoneKind(StrEnum):
    CITYWIDE = "citywide"
    RECOGNIZED_ZONE = "recognized_zone"


class AdministrativeAreaKind(StrEnum):
    DISTRICT = "district"
    SUBDISTRICT = "subdistrict"


@dataclass(frozen=True, slots=True)
class Municipality:
    ibge_code: str
    name: str
    state_code: str
    state_name: str
    population: int | None = None
    population_reference_year: int | None = None
    population_reference_date: date | None = None

    def __post_init__(self) -> None:
        if not self.ibge_code.isdigit() or len(self.ibge_code) != 7:
            raise ValueError("ibge_code precisa conter os 7 dígitos oficiais")
        if not self.name.strip() or not self.state_code.strip():
            raise ValueError("município e UF são obrigatórios")
        if self.population is not None and self.population < 0:
            raise ValueError("population não pode ser negativa")
        if self.population is not None and self.population_reference_year is None:
            raise ValueError("população exige ano de referência")


@dataclass(frozen=True, slots=True)
class AdministrativeArea:
    """Divisão oficial de referência; não equivale a zona comercial do app."""

    ibge_code: str
    municipality_ibge_code: str
    name: str
    kind: AdministrativeAreaKind
    parent_ibge_code: str | None = None

    def __post_init__(self) -> None:
        expected_length = 9 if self.kind is AdministrativeAreaKind.DISTRICT else 11
        if len(self.ibge_code) != expected_length or not self.ibge_code.isdigit():
            raise ValueError("código da divisão administrativa inválido")
        if len(self.municipality_ibge_code) != 7 or not self.municipality_ibge_code.isdigit():
            raise ValueError("divisão administrativa precisa de município IBGE válido")
        if not self.name.strip():
            raise ValueError("divisão administrativa precisa de nome")
        if self.kind is AdministrativeAreaKind.DISTRICT and self.parent_ibge_code:
            raise ValueError("distrito não pode apontar para distrito pai")
        if self.kind is AdministrativeAreaKind.DISTRICT and not self.ibge_code.startswith(
            self.municipality_ibge_code
        ):
            raise ValueError("código do distrito não corresponde ao município")
        if self.kind is AdministrativeAreaKind.SUBDISTRICT and (
            self.parent_ibge_code is None
            or len(self.parent_ibge_code) != 9
            or not self.parent_ibge_code.isdigit()
        ):
            raise ValueError("subdistrito precisa apontar para distrito IBGE válido")
        if self.kind is AdministrativeAreaKind.SUBDISTRICT and not self.ibge_code.startswith(
            self.parent_ibge_code or ""
        ):
            raise ValueError("código do subdistrito não corresponde ao distrito pai")


@dataclass(frozen=True, slots=True)
class Evidence:
    publisher: str
    source_url: str
    collected_at: datetime
    locator: str
    excerpt: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.publisher, self.source_url, self.locator, self.excerpt)):
            raise ValueError("evidência precisa identificar fonte, localizador e trecho")
        if not self.source_url.startswith(("https://", "http://")):
            raise ValueError("source_url precisa ser HTTP(S)")


@dataclass(frozen=True, slots=True)
class MunicipalityCoverage:
    municipality_ibge_code: str
    state: CoverageState
    evidence: tuple[Evidence, ...] = ()
    reviewer: str | None = None
    reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.municipality_ibge_code.isdigit() or len(self.municipality_ibge_code) != 7:
            raise ValueError("cobertura precisa apontar para código IBGE válido")
        if self.state is CoverageState.VERIFIED_NO_SUBDIVISIONS:
            if not self.evidence or not (self.reviewer and self.reviewed_at):
                raise ValueError("ausência de subdivisões exige evidência e revisão humana")
        if self.state is CoverageState.MAPPED_APPROVED and not (self.reviewer and self.reviewed_at):
            raise ValueError("cobertura aprovada exige revisor e data")


@dataclass(frozen=True, slots=True)
class ZoneCandidate:
    municipality_ibge_code: str
    stable_source_id: str
    name: str
    kind: ZoneKind
    evidence: tuple[Evidence, ...]
    review_state: ReviewState = ReviewState.PENDING
    reviewer: str | None = None
    reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.municipality_ibge_code.isdigit() or len(self.municipality_ibge_code) != 7:
            raise ValueError("candidato precisa apontar para código IBGE válido")
        if not self.stable_source_id.strip() or not self.name.strip():
            raise ValueError("candidato precisa de ID estável e nome")
        if not self.evidence:
            raise ValueError("candidato de zona exige ao menos uma evidência")
        if self.review_state is ReviewState.APPROVED and not (self.reviewer and self.reviewed_at):
            raise ValueError("zona aprovada exige revisor e data de aprovação")
