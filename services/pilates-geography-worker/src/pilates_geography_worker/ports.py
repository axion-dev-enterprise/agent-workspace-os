"""Interfaces para adaptar fontes e armazenamento após conhecer o app."""

from collections.abc import Iterable
from typing import Protocol

from .domain import Municipality, ZoneCandidate


class MunicipalitySource(Protocol):
    def fetch_municipalities(self) -> Iterable[Municipality]: ...


class CandidateSource(Protocol):
    def fetch_candidates(self, municipalities: Iterable[Municipality]) -> Iterable[ZoneCandidate]: ...


class StagingRepository(Protocol):
    def upsert_municipalities(self, rows: Iterable[Municipality]) -> int: ...

    def upsert_candidates(self, rows: Iterable[ZoneCandidate]) -> int: ...


class ApprovedCandidateRepository(Protocol):
    def list_approved_candidates(self) -> Iterable[ZoneCandidate]: ...


class AppPublisher(Protocol):
    def publish_approved(self, rows: Iterable[ZoneCandidate]) -> int: ...
