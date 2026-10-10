"""Persistência idempotente do catálogo em SQLite local de revisão/staging."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from .domain import AdministrativeArea, AdministrativeAreaKind, Municipality
from .ibge import (
    IBGE_DISTRICTS_URL,
    IBGE_MUNICIPALITIES_URL,
    IBGE_POPULATION_URL,
    IBGE_SUBDISTRICTS_URL,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS municipalities (
    ibge_code TEXT PRIMARY KEY CHECK(length(ibge_code) = 7),
    name TEXT NOT NULL,
    state_code TEXT NOT NULL,
    state_name TEXT NOT NULL,
    population INTEGER,
    population_reference_year INTEGER,
    population_reference_date TEXT,
    population_source_url TEXT,
    population_collected_at TEXT,
    source_url TEXT NOT NULL,
    collected_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    fetched_count INTEGER NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('succeeded', 'failed')),
    error_message TEXT
);
CREATE TABLE IF NOT EXISTS administrative_areas (
    area_kind TEXT NOT NULL CHECK(area_kind IN ('district', 'subdistrict')),
    ibge_code TEXT NOT NULL,
    municipality_ibge_code TEXT NOT NULL CHECK(length(municipality_ibge_code) = 7),
    parent_ibge_code TEXT,
    name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    PRIMARY KEY (area_kind, ibge_code),
    FOREIGN KEY (municipality_ibge_code) REFERENCES municipalities(ibge_code)
);
CREATE INDEX IF NOT EXISTS idx_municipalities_state_name
    ON municipalities(state_name, name);
CREATE INDEX IF NOT EXISTS idx_areas_municipality_name
    ON administrative_areas(municipality_ibge_code, name);
"""


class SQLiteStaging:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def upsert_municipalities(
        self,
        rows: Iterable[Municipality],
        collected_at: datetime | None = None,
        population_collected_at: datetime | None = None,
    ) -> int:
        collected_at = collected_at or datetime.now(UTC)
        rows = tuple(rows)
        return self.upsert_snapshot(
            rows,
            (),
            (),
            collected_at=collected_at,
            population_collected_at=population_collected_at,
        )[0]

    def upsert_snapshot(
        self,
        municipalities: Iterable[Municipality],
        areas: Iterable[AdministrativeArea],
        source_runs: Iterable[tuple[str, datetime, datetime, int, str]],
        *,
        collected_at: datetime | None = None,
        population_collected_at: datetime | None = None,
        area_collected_at: dict[str, datetime] | None = None,
    ) -> tuple[int, int]:
        municipalities = tuple(municipalities)
        areas = tuple(areas)
        source_runs = tuple(source_runs)
        collected_at = collected_at or datetime.now(UTC)
        area_collected_at = area_collected_at or {}
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            (
                row.ibge_code,
                row.name,
                row.state_code,
                row.state_name,
                row.population,
                row.population_reference_year,
                row.population_reference_date.isoformat()
                if row.population_reference_date
                else None,
                IBGE_POPULATION_URL if row.population is not None else None,
                population_collected_at.isoformat()
                if row.population is not None and population_collected_at
                else None,
                IBGE_MUNICIPALITIES_URL,
                collected_at.isoformat(),
            )
            for row in municipalities
        ]
        area_records = [
            (
                row.kind.value,
                row.ibge_code,
                row.municipality_ibge_code,
                row.parent_ibge_code,
                row.name,
                IBGE_DISTRICTS_URL if row.kind is AdministrativeAreaKind.DISTRICT else IBGE_SUBDISTRICTS_URL,
                area_collected_at.get(
                    IBGE_DISTRICTS_URL
                    if row.kind is AdministrativeAreaKind.DISTRICT
                    else IBGE_SUBDISTRICTS_URL,
                    collected_at,
                ).isoformat(),
            )
            for row in areas
        ]
        with sqlite3.connect(self.database_path, timeout=30) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA)
            run_columns = {column[1] for column in connection.execute("PRAGMA table_info(collection_runs)")}
            if "error_message" not in run_columns:
                connection.execute("ALTER TABLE collection_runs ADD COLUMN error_message TEXT")
            columns = {
                column[1]
                for column in connection.execute("PRAGMA table_info(municipalities)")
            }
            for column in ("population_source_url", "population_collected_at"):
                if column not in columns:
                    connection.execute(f"ALTER TABLE municipalities ADD COLUMN {column} TEXT")
            connection.execute("BEGIN IMMEDIATE")
            required_snapshot_urls = {
                IBGE_MUNICIPALITIES_URL,
                IBGE_POPULATION_URL,
                IBGE_DISTRICTS_URL,
                IBGE_SUBDISTRICTS_URL,
            }
            if required_snapshot_urls.issubset({run[0] for run in source_runs}):
                connection.execute("CREATE TEMP TABLE snapshot_municipality_codes (code TEXT PRIMARY KEY)")
                connection.execute("CREATE TEMP TABLE snapshot_area_codes (kind TEXT, code TEXT, PRIMARY KEY(kind, code))")
                connection.executemany(
                    "INSERT INTO snapshot_municipality_codes(code) VALUES (?)",
                    [(row.ibge_code,) for row in municipalities],
                )
                connection.executemany(
                    "INSERT INTO snapshot_area_codes(kind, code) VALUES (?, ?)",
                    [(row.kind.value, row.ibge_code) for row in areas],
                )
                connection.execute(
                    """DELETE FROM administrative_areas WHERE NOT EXISTS (
                           SELECT 1 FROM snapshot_area_codes s
                           WHERE s.kind = administrative_areas.area_kind
                             AND s.code = administrative_areas.ibge_code
                       )"""
                )
                connection.execute(
                    """DELETE FROM municipalities WHERE NOT EXISTS (
                           SELECT 1 FROM snapshot_municipality_codes s
                           WHERE s.code = municipalities.ibge_code
                       )"""
                )
            connection.executemany(
                """INSERT INTO municipalities (
                       ibge_code, name, state_code, state_name, population,
                       population_reference_year, population_reference_date,
                       population_source_url, population_collected_at,
                       source_url, collected_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(ibge_code) DO UPDATE SET
                       name = excluded.name,
                       state_code = excluded.state_code,
                       state_name = excluded.state_name,
                       population = excluded.population,
                       population_reference_year = excluded.population_reference_year,
                       population_reference_date = excluded.population_reference_date,
                       population_source_url = excluded.population_source_url,
                       population_collected_at = excluded.population_collected_at,
                       source_url = excluded.source_url,
                       collected_at = excluded.collected_at""",
                records,
            )
            connection.executemany(
                """INSERT INTO administrative_areas (
                       area_kind, ibge_code, municipality_ibge_code, parent_ibge_code,
                       name, source_url, collected_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(area_kind, ibge_code) DO UPDATE SET
                       municipality_ibge_code = excluded.municipality_ibge_code,
                       parent_ibge_code = excluded.parent_ibge_code,
                       name = excluded.name,
                       source_url = excluded.source_url,
                       collected_at = excluded.collected_at""",
                area_records,
            )
            connection.executemany(
                """INSERT INTO collection_runs (
                       source_url, started_at, completed_at, fetched_count,
                       payload_sha256, status, error_message
                   ) VALUES (?, ?, ?, ?, ?, 'succeeded', NULL)""",
                [
                    (url, started.isoformat(), completed.isoformat(), count, digest)
                    for url, started, completed, count, digest in source_runs
                ],
            )
            connection.commit()
        return len(records), len(area_records)

    def record_run(
        self,
        *,
        started_at: datetime,
        completed_at: datetime,
        fetched_count: int,
        payload_sha256: str,
        source_url: str,
        status: str = "succeeded",
    ) -> None:
        with sqlite3.connect(self.database_path, timeout=30) as connection:
            connection.executescript(SCHEMA)
            run_columns = {column[1] for column in connection.execute("PRAGMA table_info(collection_runs)")}
            if "error_message" not in run_columns:
                connection.execute("ALTER TABLE collection_runs ADD COLUMN error_message TEXT")
            connection.execute(
                """INSERT INTO collection_runs (
                       source_url, started_at, completed_at, fetched_count,
                       payload_sha256, status, error_message
                   ) VALUES (?, ?, ?, ?, ?, ?, NULL)""",
                (
                    source_url,
                    started_at.isoformat(),
                    completed_at.isoformat(),
                    fetched_count,
                    payload_sha256,
                    status,
                ),
            )

    def municipality_count(self) -> int:
        with sqlite3.connect(self.database_path, timeout=30) as connection:
            connection.executescript(SCHEMA)
            return int(connection.execute("SELECT COUNT(*) FROM municipalities").fetchone()[0])

    def area_counts(self) -> dict[str, int]:
        with sqlite3.connect(self.database_path, timeout=30) as connection:
            connection.executescript(SCHEMA)
            return {
                kind: int(
                    connection.execute(
                        "SELECT COUNT(*) FROM administrative_areas WHERE area_kind = ?", (kind,)
                    ).fetchone()[0]
                )
                for kind in ("district", "subdistrict")
            }

    def record_failure(self, *, started_at: datetime, source_urls: Iterable[str], error: Exception) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        completed_at = datetime.now(UTC)
        message = f"{type(error).__name__}: {str(error)[:240]}"
        with sqlite3.connect(self.database_path, timeout=30) as connection:
            connection.executescript(SCHEMA)
            run_columns = {column[1] for column in connection.execute("PRAGMA table_info(collection_runs)")}
            if "error_message" not in run_columns:
                connection.execute("ALTER TABLE collection_runs ADD COLUMN error_message TEXT")
            connection.executemany(
                """INSERT INTO collection_runs (
                       source_url, started_at, completed_at, fetched_count,
                       payload_sha256, status, error_message
                   ) VALUES (?, ?, ?, 0, '', 'failed', ?)""",
                [
                    (url, started_at.isoformat(), completed_at.isoformat(), message)
                    for url in source_urls
                ],
            )
