#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB Aggregation Pipeline Optimizer & Static Linter -- AXION Enterprise
Analyzes MongoDB aggregation pipelines for performance bottlenecks, stage ordering,
unbounded array explosions, and memory overflow hazards.

Runs on Python 3 standard library. Zero external dependencies.
"""

import sys
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any

class PipelineLinter:
    def __init__(self, pipeline: List[Dict[str, Any]]):
        self.pipeline = pipeline
        self.issues: List[Dict[str, Any]] = []

    def lint(self) -> List[Dict[str, Any]]:
        self.issues = []
        if not self.pipeline or not isinstance(self.pipeline, list):
            self.issues.append({
                "severity": "CRITICAL",
                "title": "Invalid Pipeline Structure",
                "description": "Pipeline must be a non-empty array of stage objects."
            })
            return self.issues

        stage_names = []
        for idx, stage in enumerate(self.pipeline):
            if not isinstance(stage, dict) or len(stage) == 0:
                continue
            stage_name = list(stage.keys())[0]
            stage_names.append((idx, stage_name, stage[stage_name]))

        # Rule 1: Early $match Check
        first_stage = stage_names[0][1] if stage_names else ""
        if first_stage not in ("$match", "$geoNear"):
            self.issues.append({
                "severity": "HIGH",
                "stage_idx": 0,
                "title": "Pipeline Starts Without $match Filter",
                "description": f"Pipeline starts with '{first_stage}' instead of '$match'. This triggers a full collection scan into RAM.",
                "remediation": "Move '$match' to the very first stage of the pipeline to leverage indexes."
            })

        # Rule 2: $unwind Before Filter
        has_unwind = False
        unwind_idx = -1
        for idx, name, body in stage_names:
            if name == "$unwind":
                has_unwind = True
                unwind_idx = idx
            elif name == "$match" and has_unwind:
                self.issues.append({
                    "severity": "HIGH",
                    "stage_idx": idx,
                    "title": "$match Appears After $unwind",
                    "description": f"Stage {idx} ($match) filters after stage {unwind_idx} ($unwind). Unwinding arrays before filtering multiplies document count exponentially.",
                    "remediation": "Filter array elements or documents before unwinding."
                })

        # Rule 3: $sort without index or late in pipeline
        for idx, name, body in stage_names:
            if name == "$sort":
                if idx > 2:
                    self.issues.append({
                        "severity": "MEDIUM",
                        "stage_idx": idx,
                        "title": "Late $sort Stage (100MB RAM Spill Risk)",
                        "description": f"Stage {idx} ($sort) is placed late in the pipeline. Unless 'allowDiskUse: true' is set, sorting >100MB of intermediate documents will crash the query.",
                        "remediation": "Move '$sort' immediately after '$match' to leverage compound indexes (ESR rule)."
                    })

        # Rule 4: $lookup without pipeline / unindexed join
        for idx, name, body in stage_names:
            if name == "$lookup":
                if isinstance(body, dict) and "pipeline" not in body and "localField" in body:
                    self.issues.append({
                        "severity": "LOW",
                        "stage_idx": idx,
                        "title": "Simple $lookup Join without Projected Pipeline",
                        "description": f"Stage {idx} ($lookup) brings full foreign documents into RAM.",
                        "remediation": "Use sub-pipeline $lookup with '$project' to fetch only necessary fields from the joined collection."
                    })

        return self.issues

def main():
    parser = argparse.ArgumentParser(description="MongoDB Aggregation Pipeline Optimizer")
    parser.add_argument("--file", "-f", help="JSON file containing the aggregation pipeline array")
    parser.add_argument("--json-str", "-j", help="JSON string representing the pipeline")

    args = parser.parse_args()

    pipeline = None
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"Error: File {p} not found.", file=sys.stderr)
            sys.exit(1)
        try:
            pipeline = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error parsing pipeline JSON: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.json_str:
        try:
            pipeline = json.loads(args.json_str)
        except Exception as e:
            print(f"Error parsing pipeline JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default self-test example
        pipeline = [
            {"$unwind": "$items"},
            {"$match": {"status": "completed"}},
            {"$lookup": {"from": "users", "localField": "userId", "foreignField": "_id", "as": "user"}}
        ]
        print("[*] No pipeline specified. Running self-test demo pipeline:\n")

    linter = PipelineLinter(pipeline)
    issues = linter.lint()

    print("================================================================================")
    print("             MONGODB AGGREGATION PIPELINE AUDITOR REPORT                        ")
    print("================================================================================")
    print(f"Stages Analyzed: {len(pipeline)}")
    print(f"Issues Detected: {len(issues)}")
    print("--------------------------------------------------------------------------------")
    if not issues:
        print("[PASS] Pipeline is clean and follows best performance practices.")
    else:
        for idx, issue in enumerate(issues, start=1):
            stage_info = f" (Stage {issue.get('stage_idx')})" if 'stage_idx' in issue else ""
            print(f"[{idx:02d}] [{issue['severity']}] {issue['title']}{stage_info}")
            print(f"     Problem: {issue['description']}")
            if "remediation" in issue:
                print(f"     Fix:     {issue['remediation']}")
            print("--------------------------------------------------------------------------------")
    print("================================================================================")

    sys.exit(1 if any(i["severity"] in ("CRITICAL", "HIGH") for i in issues) else 0)

if __name__ == "__main__":
    main()
