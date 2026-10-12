#!/usr/bin/env python3
"""Audit frame-scope arguments in the authored shape-decode ladder seed.

This is a static source audit, not a runtime locality or tractability test.
It records whether each helper Term in shape_decode_loop.json carries a graph
frame scope. ShapeDecode's `codebook_scope` is reported separately because it
selects names, not `scope_id` values.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "seeds" / "shape_decode_loop.json"
OUT = ROOT / "evaluation" / "reports" / "shape_decode_seed_scope_audit_v1_20261005.json"
HELPERS = ("ShapeDecode", "TransformDecode", "DimInfer", "GenInfer")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> int:
    seed = json.loads(SEED.read_text())
    rows = []
    total = Counter()
    per_rule = defaultdict(Counter)
    for rule in seed.get("rules", []):
        name = rule.get("name", "<unnamed>")
        for obj in walk(rule):
            helper = obj.get("type")
            if helper not in HELPERS:
                continue
            row = {
                "rule": name,
                "helper": helper,
                "frame_scope_argument": "scope" in obj,
                "name_scope_argument": "codebook_scope" in obj if helper == "ShapeDecode" else False,
                "parsed_codebook_cache_path_eligible": (
                    helper == "ShapeDecode" and "codebook_scope" in obj
                ),
            }
            rows.append(row)
            total[(helper, "frame_scoped" if row["frame_scope_argument"] else "global")] += 1
            per_rule[name][helper] += 1

    helper_summary = {}
    for helper in HELPERS:
        helper_summary[helper] = {
            "term_occurrences": sum(v for (h, _), v in total.items() if h == helper),
            "frame_scoped_occurrences": total[(helper, "frame_scoped")],
            "global_occurrences": total[(helper, "global")],
            "name_scoped_occurrences": sum(
                1 for row in rows if row["helper"] == helper and row["name_scope_argument"]
            ),
            "parsed_codebook_cache_path_eligible_occurrences": sum(
                1 for row in rows if row["helper"] == helper
                and row["parsed_codebook_cache_path_eligible"]
            ),
        }

    result = {
        "schema": "ShapeDecodeSeedScopeAuditV1",
        "run_id": "shape-decode-seed-scope-audit-v1-20261005",
        "seed_path": str(SEED.relative_to(ROOT)),
        "seed_sha256": sha256(SEED),
        "runner_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "seed_rule_count": len(seed.get("rules", [])),
        "helper_summary": helper_summary,
        "cache_applicability": {
            "eligible_shape_decode_occurrences": helper_summary["ShapeDecode"][
                "parsed_codebook_cache_path_eligible_occurrences"
            ],
            "global_shape_decode_occurrences": helper_summary["ShapeDecode"]["global_occurrences"],
            "cache_gate_source": "runners/dsl/src/shape_decode.rs::eval_shape_decode requires scope_idx.is_some() and the cache switch to be enabled",
            "interpretation": "Eligibility is syntactic for this seed. It does not imply the scoped call executes or repeats within one EvalCtx.",
        },
        "occurrences": rows,
        "claim_boundary": (
            "Static evidence about authored Term arguments in this seed only. "
            "It does not establish runtime codebook-node scope attributes, "
            "natural frame validity, or helper cost."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "rule_count": result["seed_rule_count"], "helper_summary": helper_summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
