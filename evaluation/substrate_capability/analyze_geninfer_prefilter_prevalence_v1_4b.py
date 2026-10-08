#!/usr/bin/env python3
"""Independent analysis of the GenInfer prefilter v1.4b prevalence capture.

Recomputes every gate from raw records (not from the runner's summary) and
checks provenance against the files on disk.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/geninfer_prefilter_prevalence_v1_4b_20261006.json"
OUT = ROOT / "evaluation/reports/geninfer_prefilter_prevalence_v1_4b_analysis_20261006.json"
NATIVE_SHA = "c0b4011c0d1dccde9d2e365c593982345a0aa74c8e50be27720ee280ba30b0ae"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    recs = raw["records"]
    checks = {}
    checks["native_hash_matches_lock"] = raw["native"]["sha256"] == NATIVE_SHA
    checks["sources_stable_during_capture"] = bool(raw["sources_stable"])
    checks["protocol_hash_current"] = raw["protocol_sha256"] == sha(ROOT / raw["protocol"])
    checks["amendment_hash_current"] = raw["amendment_sha256"] == sha(ROOT / raw["amendment"])
    expected_jobs = 300 * 3 + 6 + 10 + 4
    checks["job_count"] = len(recs) == expected_jobs
    parity = [r for r in recs if r["parity"] is not None]
    checks["G4_real_data_parity_all"] = all(r["parity"] for r in parity) and len(parity) >= 900
    checks["G5_panel_fallback_fixtures_parity"] = all(
        r["parity"] is True for r in recs if r["source"] == "v1_panel_training_input") and \
        sum(r["source"] == "v1_panel_training_input" for r in recs) == 4
    mism = sum(v for r in recs for k, v in r["counters"].items() if k.endswith("fallback_reason:validation_mismatch"))
    checks["G6_zero_validation_mismatch"] = mism == 0
    # Off-arm skips are exactly the cap rule.
    checks["off_arm_skip_rule"] = all(
        (r["off_ns"] is None) == (r["enumerator_matrix_bound"] > 3_000_000 and r["source"] != "v1_panel_training_input")
        for r in recs)
    # Counter conservation per record: each attempted stage resolves exactly once.
    def conserve(c):
        a = c.get("gen_infer_prefilter_attempts", 0)
        if a == 0:
            return True
        ok = a == c.get("gen_infer_prefilter_solved", 0) + c.get("gen_infer_prefilter_proven_no_fit", 0) + c.get("gen_infer_prefilter_fallback", 0)
        rf = c.get("gen_infer_row_factorized_attempts", 0)
        ok &= rf == c.get("gen_infer_prefilter_fallback", 0)
        ok &= rf == c.get("gen_infer_row_factorized_solved", 0) + c.get("gen_infer_row_factorized_no_candidate", 0) + c.get("gen_infer_row_factorized_fallback", 0)
        co = c.get("gen_infer_correspondence_attempts", 0)
        ok &= co == c.get("gen_infer_row_factorized_fallback", 0)
        ok &= co == c.get("gen_infer_correspondence_found", 0) + c.get("gen_infer_correspondence_no_candidate", 0) + c.get("gen_infer_correspondence_fallback", 0)
        return ok
    checks["stage_counter_conservation"] = all(conserve(r["counters"]) for r in recs)

    paths = defaultdict(Counter)
    for r in recs:
        paths[f"{r['source']}:{r['schema']}"][r["path"]] += 1
    enumerator = sum(r["path"].startswith("enumerator_fallback") for r in recs)

    timing = {}
    for key in sorted({f"{r['source']}:{r['schema']}" for r in recs}):
        rs = [r for r in recs if f"{r['source']}:{r['schema']}" == key]
        on = [min(r["on_ns"]) / 1e6 for r in rs]
        off = [min(r["off_ns"]) / 1e6 for r in rs if r["off_ns"]]
        ratios = [min(r["off_ns"]) / max(min(r["on_ns"]), 1) for r in rs if r["off_ns"]]
        timing[key] = {"n": len(rs), "on_ms_median": statistics.median(on), "on_ms_max": max(on),
                       "off_ms_median": statistics.median(off) if off else None,
                       "off_over_on_median": statistics.median(ratios) if ratios else None}
    scale = sorted(((int(r["schema"].removeprefix("sdloop_size")), r["kind"], r["n_base"], r["bound"],
                     min(r["on_ns"]) / 1e6, (min(r["off_ns"]) / 1e6) if r["off_ns"] else None,
                     r["counters"].get("gen_infer_correspondence_hypotheses"), r["counters"].get("gen_infer_correspondence_validations"),
                     r["matrix_on"]) for r in recs if r["source"] == "sdloop_vision_scale"))
    explained = Counter((r["source"], r["schema"], tuple(r["matrix_on"]), r["residual_dims_on"]) for r in recs if r["explained_on"])
    nondegenerate = sum(n for (src, _s, m, _d), n in explained.items() if any(m) and src == "omniglot")
    static = raw["static_summary"]
    report = {"schema": "GenInferPrefilterPrevalenceV1_4bAnalysis", "raw": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
              "checks": checks, "all_pass": all(checks.values()), "parity_checked": len(parity),
              "enumerator_fallbacks": enumerator, "path_counts": {k: dict(v) for k, v in sorted(paths.items())},
              "timing": timing, "sdloop_scale": [dict(zip(["size", "pair", "n_base", "bound", "on_ms", "off_ms", "hypotheses", "validations", "matrix"], s)) for s in scale],
              "explained": [{"source": k[0], "schema": k[1], "matrix": list(k[2]), "residual_dims": k[3], "count": n} for k, n in explained.most_common()],
              "omniglot_nondegenerate_explained": nondegenerate, "static_summary": static}
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": report["all_pass"], "checks": checks, "enumerator_fallbacks": enumerator,
                      "omniglot_nondegenerate_explained": nondegenerate}, indent=1))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
