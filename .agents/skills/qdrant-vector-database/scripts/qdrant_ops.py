#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qdrant Vector Database Diagnostics & Collection Manager -- AXION Enterprise
Pure Python 3 standard library utility for Qdrant REST API (default port 6333).
Zero external dependencies (no qdrant-client required).

Features:
- Healthcheck and cluster status inspection
- Collection inspection (vectors count, HNSW config, quantization status)
- Benchmark vector search latency
- Trigger collection snapshot backup
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class QdrantCli:
    def __init__(self, host: str = "http://localhost:6333", api_key: Optional[str] = None):
        self.host = host.rstrip("/")
        self.api_key = api_key

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.host}{path}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {"status": "ok"}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                return json.loads(err_body)
            except Exception:
                return {"error": str(e), "status_code": e.code}
        except Exception as e:
            return {"error": str(e)}

    def check_health(self) -> bool:
        start = time.perf_counter()
        res = self._request("GET", "/healthz")
        elapsed_ms = (time.perf_counter() - start) * 1000
        if "error" in res and not res.get("status"):
            print(f"[FAIL] Qdrant connection failed: {res.get('error')}", file=sys.stderr)
            return False
        print(f"[PASS] Qdrant online at {self.host} (Latency: {elapsed_ms:.2f}ms)")
        return True

    def list_collections(self) -> Dict[str, Any]:
        return self._request("GET", "/collections")

    def inspect_collection(self, name: str):
        res = self._request("GET", f"/collections/{name}")
        if "error" in res or res.get("status") != "ok":
            print(f"Error inspecting collection '{name}': {res.get('error') or res}", file=sys.stderr)
            return False

        col = res.get("result", {})
        config = col.get("config", {})
        params = config.get("params", {})
        vectors = params.get("vectors", {})
        hnsw = config.get("hnsw_config", {})
        quant = config.get("quantization_config")

        print(f"Collection Name:     {name}")
        print(f"Status:              {col.get('status')}")
        print(f"Vectors Count:       {col.get('vectors_count', 0)}")
        print(f"Points Count:        {col.get('points_count', 0)}")
        if isinstance(vectors, dict):
            print(f"Vector Dimensions:   {vectors.get('size')}")
            print(f"Distance Metric:     {vectors.get('distance')}")
        print(f"HNSW Config:         m={hnsw.get('m')}, ef_construct={hnsw.get('ef_construct')}")
        print(f"Quantization:        {quant if quant else 'None (Full 32-bit Float)'}")
        return True

    def create_snapshot(self, name: str):
        print(f"[*] Triggering snapshot backup for collection '{name}'...")
        res = self._request("POST", f"/collections/{name}/snapshots")
        if res.get("status") == "ok":
            snap = res.get("result", {})
            print(f"[PASS] Snapshot created: {snap.get('name')} (Size: {snap.get('size', 0)} bytes)")
            return True
        print(f"[FAIL] Snapshot failed: {res}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Qdrant Vector Database Diagnostics & Ops CLI")
    parser.add_argument("--url", default="http://localhost:6333", help="Qdrant URL (default: http://localhost:6333)")
    parser.add_argument("--api-key", help="Qdrant API Key")
    parser.add_argument("--health", action="store_true", help="Check Qdrant health")
    parser.add_argument("--list", action="store_true", help="List all collections")
    parser.add_argument("--inspect", help="Inspect detailed collection parameters")
    parser.add_argument("--snapshot", help="Create a snapshot backup of collection")

    args = parser.parse_args()
    key = args.api_key or os.environ.get("QDRANT_API_KEY")
    cli = QdrantCli(host=args.url, api_key=key)

    if args.health:
        ok = cli.check_health()
        sys.exit(0 if ok else 1)

    if args.list:
        cols = cli.list_collections()
        print(json.dumps(cols, indent=2))
        sys.exit(0)

    if args.inspect:
        ok = cli.inspect_collection(args.inspect)
        sys.exit(0 if ok else 1)

    if args.snapshot:
        ok = cli.create_snapshot(args.snapshot)
        sys.exit(0 if ok else 1)

    # Default action: health check
    ok = cli.check_health()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
