#!/usr/bin/env python3
"""Recompute and validate the scoped ShapeDecode seed census."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_seed_aperture_reuse_v1_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_SEED_APERTURE_REUSE_V1_PROTOCOL_20261005.md"
OUT = ROOT / "evaluation/reports/shapedecode_seed_aperture_reuse_v1_analysis_20261005.json"
REPEAT_CONTEXTS = {"MaxOver": "value", "Argmax": "value", "Filter": "predicate"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute() -> tuple[dict[str, str], list[dict]]:
    seeds = sorted((ROOT / "seeds").glob("*.json"))
    digests, found = {}, []
    for file in seeds:
        rel = file.relative_to(ROOT).as_posix()
        digests[rel] = sha(file)
        tree = json.loads(file.read_text())

        def descend(node, pointer="", stack=()):
            if isinstance(node, dict):
                kind = node.get("type")
                if kind == "ShapeDecode" and "codebook_scope" in node:
                    contexts = [parent for parent, key in stack
                                if parent in REPEAT_CONTEXTS and REPEAT_CONTEXTS[parent] == key]
                    found.append({"seed": rel, "json_pointer": pointer,
                                  "codebook_type": node.get("codebook_type"),
                                  "repeat_context": contexts[-1] if contexts else "other"})
                next_stack = stack
                if kind:
                    next_stack = (*stack, (kind, None))
                for key, value in node.items():
                    if kind:
                        field_stack = (*stack, (kind, key))
                    else:
                        field_stack = stack
                    descend(value, f"{pointer}/{key}", field_stack)
            elif isinstance(node, list):
                for i, value in enumerate(node):
                    descend(value, f"{pointer}/{i}", stack)

        descend(tree)
    found.sort(key=lambda row: (row["seed"], row["json_pointer"], str(row["codebook_type"])))
    return digests, found


def main() -> int:
    capture = json.loads(CAPTURE.read_text())
    current_hashes, current_rows = recompute()
    counts = Counter(row["repeat_context"] for row in current_rows)
    checks = {
        "seed_hashes_match_current_tree": capture.get("seed_sha256") == current_hashes,
        "occurrence_rows_match_independent_walk": capture.get("occurrences") == current_rows,
        "44_scoped_calls_in_11_seed_files": len(current_rows) == 44 and
            len({row["seed"] for row in current_rows}) == 11,
        "repeated_value_or_predicate_contexts_present": sum(counts[k] for k in ("MaxOver", "Argmax", "Filter")) > 0,
        "protocol_hash_matches": capture.get("protocol_sha256") == sha(PROTOCOL),
    }
    analysis = {"schema": "ShapeDecodeSeedApertureReuseCensusV1Analysis",
                "capture_sha256": sha(CAPTURE), "protocol_sha256": sha(PROTOCOL),
                "checks": checks, "passed": all(checks.values()),
                "recomputed_total": len(current_rows),
                "recomputed_by_context": dict(sorted(counts.items())),
                "interpretation": "Static source inventory only; syntactic repetition contexts do not establish loaded-seed activity or runtime frequency."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(), "passed": analysis["passed"],
                      "checks": sum(checks.values()), "check_count": len(checks),
                      "total": len(current_rows), "by_context": analysis["recomputed_by_context"]}, sort_keys=True))
    return 0 if analysis["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
