#!/usr/bin/env python3
"""Measure text-to-relation extraction before memory or response stages."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from domains.comprehend_text import comprehend_text
from substrate.world_adapter import WorldAdapter

CASES = ROOT / "evaluation/substrate_capability/text_to_proposition_extraction_v1_cases_20261003.json"
LOCK = ROOT / "evaluation/substrate_capability/text_to_proposition_extraction_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/text_to_proposition_extraction_v1_raw_20261003.json"
REPEATS = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {item["path"]: sha(ROOT / item["path"])
            for item in lock["locked_inputs"]}


def lock_errors(actual: dict[str, str]) -> list[str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return [f"source hash mismatch: {item['path']}"
            for item in lock["locked_inputs"]
            if actual.get(item["path"]) != item["sha256"]]


def surface(value):
    return value.get("surface") if isinstance(value, dict) else value


def run_case(case: dict, replicate: int) -> dict:
    # Fresh empty graph per row isolates the parser and its explicitly held
    # classification rules from episodic memory, answer generation, and turns.
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, case["text"])
    relation = comp.relation or comp.dispatch.get("relation") or {}
    subject = surface(relation.get("subject"))
    predicate = surface(relation.get("predicate"))
    obj = surface(relation.get("object"))
    norm_obj = str(obj).strip(" .!?;,:") if obj is not None else None
    query_target = None
    if comp.dispatch.get("path") == "table":
        spec = comp.dispatch.get("spec")
        query_target = getattr(spec, "know_concept", None)
    elif comp.dispatch.get("path") == "know":
        query_target = comp.dispatch.get("concept")
    return {
        "case_id": case["id"],
        "replicate": replicate,
        "pid": os.getpid(),
        "text": case["text"],
        "expected_value": case.get("expected_value"),
        "expected_polarity": case.get("expected_polarity"),
        "kind": comp.kind,
        "dispatch_path": comp.dispatch.get("path"),
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "normalized_object": norm_obj,
        "relation_focus": relation.get("focus"),
        "relation_polarity": relation.get("polarity"),
        "language_evidence": relation.get("language_evidence"),
        "gaps": comp.gaps,
        "query_target": query_target,
        "value_exact": (norm_obj == case.get("expected_value")
                        if "expected_value" in case else None),
        "polarity_exact": (relation.get("polarity") == case.get("expected_polarity")
                           if "expected_polarity" in case else None),
        "subject_exact": (subject == case.get("expected_subject")
                          if "expected_value" in case else None),
        "predicate_exact": (predicate == "has_secret_code"
                             if "expected_value" in case else None),
        "query_target_exact": (query_target == case.get("expected_query_topic")
                               if "expected_query_topic" in case else None),
        "handoff_stage": "parser_only",
    }


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    before = source_hashes()
    errors = lock_errors(before)
    rows = [run_case(case, rep)
            for case in cases for rep in range(REPEATS)]
    after = source_hashes()
    if before != after:
        errors.append("locked source changed during run")
    if any(row["kind"] != next(c["kind"] for c in cases
                                if c["id"] == row["case_id"])
           for row in rows):
        errors.append("speech-act classification mismatch")
    if len(rows) != len(cases) * REPEATS:
        errors.append("incomplete case capture")
    report = {
        "schema": "text_to_proposition_extraction_v1",
        "passed_integrity": not errors,
        "integrity_errors": errors,
        "repeat_count_per_case": REPEATS,
        "locked_inputs": before,
        "post_run_inputs": after,
        "case_count": len(cases),
        "row_count": len(rows),
        "value_exact_count": sum(row["value_exact"] is True for row in rows),
        "value_scored_count": sum(row["value_exact"] is not None for row in rows),
        "polarity_exact_count": sum(row["polarity_exact"] is True for row in rows),
        "polarity_scored_count": sum(row["polarity_exact"] is not None for row in rows),
        "subject_exact_count": sum(row["subject_exact"] is True for row in rows),
        "predicate_exact_count": sum(row["predicate_exact"] is True for row in rows),
        "complete_proposition_exact_count": sum(
            all(row[key] is True for key in (
                "value_exact", "subject_exact", "predicate_exact", "polarity_exact"))
            for row in rows if row["value_exact"] is not None),
        "query_target_exact_count": sum(row["query_target_exact"] is True for row in rows),
        "query_scored_count": sum(row["query_target_exact"] is not None for row in rows),
        "rows": rows,
        "interpretation": (
            "Direct comprehension-front-end measurement on raw text with an empty graph. "
            "The output relation is compared with a locked target proposition; a recovered "
            "value alone is not counted as a correctly extracted proposition. The query "
            "target is a parser dispatch result, not evidence of memory retrieval."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "passed_integrity", "integrity_errors", "case_count", "row_count",
        "value_exact_count", "value_scored_count", "polarity_exact_count",
        "polarity_scored_count", "subject_exact_count", "predicate_exact_count",
        "query_target_exact_count", "query_scored_count",
        "complete_proposition_exact_count")
        } | {"output": str(OUT)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
