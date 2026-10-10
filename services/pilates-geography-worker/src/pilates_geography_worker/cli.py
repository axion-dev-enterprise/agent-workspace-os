"""CLI para importar o catálogo nacional oficial para staging."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from .ibge import (
    IBGE_DISTRICTS_URL,
    IBGE_MUNICIPALITIES_URL,
    IBGE_POPULATION_URL,
    IBGE_SUBDISTRICTS_URL,
    IbgeAdministrativeAreaSource,
    IbgeMunicipalitySource,
    IbgePopulationSource,
)
from .staging import SQLiteStaging


DEFAULT_DATABASE = Path("/var/lib/pilates-geography-worker/staging.sqlite3")


def main() -> int:
    parser = argparse.ArgumentParser(prog="pilates-geography-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    refresh = subparsers.add_parser("refresh-catalog", aliases=["refresh-municipalities"])
    refresh.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()

    started_at = datetime.now(UTC)
    staging = SQLiteStaging(args.database)
    source_urls = (
        IBGE_MUNICIPALITIES_URL,
        IBGE_POPULATION_URL,
        IBGE_DISTRICTS_URL,
        IBGE_SUBDISTRICTS_URL,
    )
    source = IbgeMunicipalitySource()
    population_source = IbgePopulationSource()
    area_source = IbgeAdministrativeAreaSource()
    try:
        municipalities = source.fetch_municipalities()
        population = population_source.fetch_population()
        municipality_codes = {row.ibge_code for row in municipalities}
        if municipality_codes != set(population):
            raise ValueError("catálogo de municípios e população SIDRA têm códigos divergentes")
        areas = area_source.fetch_areas(municipality_codes)
        if (
            source.collected_at is None
            or source.payload_sha256 is None
            or population_source.collected_at is None
            or population_source.payload_sha256 is None
            or population_source.reference_year is None
            or len(area_source.provenance) != 2
        ):
            raise RuntimeError("IBGE não gerou metadados completos de proveniência")
        rows = tuple(
            replace(
                row,
                population=population[row.ibge_code],
                population_reference_year=population_source.reference_year,
            )
            for row in municipalities
        )
        collected_at, digest, count = area_source.provenance[IBGE_DISTRICTS_URL]
        subdistrict_collected_at, subdistrict_digest, subdistrict_count = area_source.provenance[
            IBGE_SUBDISTRICTS_URL
        ]
        completed_at = datetime.now(UTC)
        source_runs = (
            (IBGE_MUNICIPALITIES_URL, started_at, max(completed_at, source.collected_at), len(rows), source.payload_sha256),
            (IBGE_POPULATION_URL, started_at, max(completed_at, population_source.collected_at), len(population), population_source.payload_sha256),
            (IBGE_DISTRICTS_URL, started_at, max(completed_at, collected_at), count, digest),
            (IBGE_SUBDISTRICTS_URL, started_at, max(completed_at, subdistrict_collected_at), subdistrict_count, subdistrict_digest),
        )
        upserted_count, upserted_area_count = staging.upsert_snapshot(
            rows,
            areas,
            source_runs,
            collected_at=source.collected_at,
            population_collected_at=population_source.collected_at,
            area_collected_at={
                IBGE_DISTRICTS_URL: collected_at,
                IBGE_SUBDISTRICTS_URL: subdistrict_collected_at,
            },
        )
    except Exception as error:
        try:
            staging.record_failure(started_at=started_at, source_urls=source_urls, error=error)
        except Exception:
            pass
        print(json.dumps({"status": "failed", "error": f"{type(error).__name__}: {error}"}, ensure_ascii=False), file=sys.stderr)
        return 1

    area_counts = staging.area_counts()
    print(
        json.dumps(
            {
                "status": "succeeded",
                "source_urls": list(source_urls),
                "fetched_count": len(rows),
                "upserted_count": upserted_count,
                "population_reference_year": population_source.reference_year,
                "population_estimate_count": len(population),
                "staged_municipality_count": staging.municipality_count(),
                "administrative_areas_fetched_count": len(areas),
                "administrative_areas_upserted_count": upserted_area_count,
                "staged_administrative_area_counts": area_counts,
                "payload_sha256": {
                    "localities": source.payload_sha256,
                    "population": population_source.payload_sha256,
                    "districts": digest,
                    "subdistricts": subdistrict_digest,
                },
                "database": str(args.database),
                "zones_collected": 0,
                "zones_note": "Distritos e subdistritos são referências administrativas, ainda sem aprovação como zonas do produto.",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0
