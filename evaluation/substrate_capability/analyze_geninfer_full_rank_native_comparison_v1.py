#!/usr/bin/env python3
"""Independent gates for the paired native full-rank GenInfer capture."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/geninfer_full_rank_native_comparison_v1.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_NATIVE_COMPARISON_V1_PREREG_20261006.md"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evaluation/reports/geninfer_full_rank_native_comparison_v1_20261006.json"
    payload = json.loads(path.read_text())
    errors = []
    for key, source in (("runner_sha256", RUNNER), ("protocol_sha256", PROTOCOL)):
        if payload.get(key) != sha(source):
            errors.append(f"{key} mismatch")
    indexed = {}
    native_hashes = {"baseline": set(), "solver": set()}
    source_manifests = {}
    for row in payload.get("workers", []):
        key = (row["case"]["id"], row["audit"], row["variant"])
        if key in indexed:
            errors.append(f"duplicate worker {key}")
        indexed[key] = row
        native_hashes[row["variant"]].add(row["native_sha256"])
        if not row.get("source_stable") or row["source_before"] != row["source_after"]:
            errors.append(f"source drift: {key}")
        source_manifests.setdefault(row["variant"], row["source_before"])
        for stage, phase in row["phases"].items():
            if not isinstance(phase.get("wall_ns"), int) or phase["wall_ns"] <= 0:
                errors.append(f"invalid timing: {key}/{stage}")
            if row["audit"]:
                c = phase.get("full_rank_counters", {})
                required = ("gen_infer_full_rank_bases", "gen_infer_full_rank_refusals",
                    "gen_infer_full_rank_attempts", "gen_infer_full_rank_apply_rejects",
                    "gen_infer_full_rank_candidate_rejects", "gen_infer_full_rank_residual_rejects",
                    "gen_infer_full_rank_survivors")
                if any(name not in c for name in required):
                    errors.append(f"missing full-rank counters: {key}/{stage}")
                elif c["gen_infer_full_rank_bases"] != c["gen_infer_full_rank_refusals"] + c["gen_infer_full_rank_attempts"]:
                    errors.append(f"basis conservation failed: {key}/{stage}")
                elif c["gen_infer_full_rank_attempts"] != sum(c[name] for name in (
                    "gen_infer_full_rank_apply_rejects", "gen_infer_full_rank_candidate_rejects",
                    "gen_infer_full_rank_residual_rejects", "gen_infer_full_rank_survivors")):
                    errors.append(f"attempt conservation failed: {key}/{stage}")
    if len(indexed) != len(payload.get("case_spec", [])) * 4:
        errors.append("worker coverage is incomplete")
    if len(native_hashes["baseline"]) != 1 or len(native_hashes["solver"]) != 1 or native_hashes["baseline"] == native_hashes["solver"]:
        errors.append("binary hashes are inconsistent")
    if source_manifests.get("baseline") != source_manifests.get("solver"):
        errors.append("source manifests differ across variants")

    def has_matrix(row, matrix):
        return any(g.get("matrix") == matrix for g in row.get("final_generators", []))

    for case in payload.get("case_spec", []):
        ident, kind, d = case["id"], case["kind"], case["dimension"]
        for audit in (False, True):
            base = indexed.get((ident, audit, "baseline")); solver = indexed.get((ident, audit, "solver"))
            if base is None or solver is None:
                errors.append(f"missing pair {ident}/audit={audit}")
                continue
            matrix = base["expected_matrix"]
            flat = [v for row in matrix for v in row]
            if kind == "positive" and d == 2:
                if base["phases"] != solver["phases"]:
                    # Ignore newly exposed experimental audit counters; compare semantic/time-independent fields.
                    for stage in ("train", "heldout"):
                        for field in ("status", "covered_by", "residual", "receipts", "closure_work", "generators"):
                            if base["phases"][stage].get(field) != solver["phases"][stage].get(field):
                                errors.append(f"2-D parity mismatch {ident}/{stage}/{field}/audit={audit}")
                if not has_matrix(base, flat) or not has_matrix(solver, flat):
                    errors.append(f"2-D positive did not acquire oracle matrix: {ident}")
            elif kind == "positive":
                if has_matrix(base, flat):
                    errors.append(f"baseline unexpectedly acquired higher-dimensional matrix: {ident}")
                if not has_matrix(solver, flat):
                    errors.append(f"solver failed to acquire oracle matrix: {ident}")
                if base["final_generators"] != base["initial_generators"]:
                    errors.append(f"feature-off baseline changed higher-dimensional generator library: {ident}")
                if not base["training_oracle_exact"]:
                    errors.append(f"positive target construction mismatch: {ident}")
                if any(solver["phases"][stage]["status"] != "recognized_transformed" or
                       not solver["phases"][stage]["receipts"] for stage in ("train", "heldout")):
                    errors.append(f"solver did not recognize with receipts: {ident}")
                train_names = {r.get("generator") for r in solver["phases"]["train"]["receipts"]}
                held_names = {r.get("generator") for r in solver["phases"]["heldout"]["receipts"]}
                if not (train_names & held_names):
                    errors.append(f"solver failed held-out generator reuse: {ident}")
            else:
                for stage in ("train", "heldout"):
                    if any(g.get("matrix") == flat for g in solver["phases"][stage]["generators"]):
                        errors.append(f"negative control acquired oracle matrix: {ident}/{stage}")
                    if solver["phases"][stage]["status"] != "minted" or solver["phases"][stage]["receipts"]:
                        errors.append(f"negative control was incorrectly recognized: {ident}/{stage}")
                if solver["final_generators"] != solver["initial_generators"]:
                    errors.append(f"negative control acquired a spurious generator: {ident}")
                if kind == "rank_deficient" and not solver["training_oracle_exact"]:
                    errors.append("rank-deficient control target construction mismatch")
                if kind == "nonlinear" and solver["training_oracle_exact"]:
                    errors.append("nonlinear control became linear")

    report = {"schema": "GenInferFullRankNativeComparisonV1Analysis",
        "capture_sha256": sha(path), "errors": errors, "gates_pass": not errors,
        "captured_analyzer_sha256": payload.get("analyzer_sha256"),
        "posthoc_analyzer_sha256": sha(ANALYZER),
        "analysis_status": "post_capture_corrected_analysis",
        "worker_count": len(payload.get("workers", [])),
        "interpretation_limit": "Authored native fixtures on one host; does not estimate natural full-rank prevalence or support beyond registered dimensions."}
    out = path.with_name(path.stem.replace("_20261006", "_analysis_20261006") + ".json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(out.relative_to(ROOT)), "errors": errors,
                      "gates_pass": not errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
