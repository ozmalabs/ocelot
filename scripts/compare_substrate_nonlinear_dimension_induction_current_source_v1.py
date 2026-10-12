#!/usr/bin/env python3
"""Descriptive comparison of the current-source nonlinear-induction run to v1.1 rep2."""
import hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_RAW = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep2_20260926.json"
OLD_ANALYSIS = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep2_analysis_20260926.json"
OLD_LOCK = ROOT / "evaluation/substrate_capability/nonlinear_dimension_induction_v1_1_lock_20260926.json"
NEW_RAW = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_1_20260929.json"
NEW_ANALYSIS = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_1_analysis_20260929.json"
NEW_LOCK = ROOT / "evaluation/substrate_capability/nonlinear_dimension_induction_v1_2_1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_current_source_comparison_v1_20260929.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def q(values, p):
    values = sorted(values)
    pos = p * (len(values) - 1)
    lo = int(pos); hi = min(lo + 1, len(values) - 1)
    return values[lo] + (pos - lo) * (values[hi] - values[lo])

def main():
    old = json.loads(OLD_RAW.read_text()); new = json.loads(NEW_RAW.read_text())
    old_a = json.loads(OLD_ANALYSIS.read_text()); new_a = json.loads(NEW_ANALYSIS.read_text())
    old_l = json.loads(OLD_LOCK.read_text()); new_l = json.loads(NEW_LOCK.read_text())
    old_ix = {(x["family"], x["replicate"], x["enabled"]): x for x in old["samples"]}
    new_ix = {(x["family"], x["replicate"], x["enabled"]): x for x in new["samples"]}
    semantic_equal = {}
    timing = {}
    for family in new_l["inputs"]["families"]:
        for enabled in (True, False):
            cells = [(family, r, enabled) for r in range(new_l["inputs"]["repetitions"])]
            semantic_equal[f"{family}:{'induction' if enabled else 'frozen'}"] = all(
                (old_ix[k]["events"][0]["status"], old_ix[k]["events"][1]["status"],
                 old_ix[k]["total_quanta"], old_ix[k]["final_generators"]) ==
                (new_ix[k]["events"][0]["status"], new_ix[k]["events"][1]["status"],
                 new_ix[k]["total_quanta"], new_ix[k]["final_generators"]) for k in cells)
            samples = {}
            for label, data in (("v1_1_rep2", old), ("current_source_v1_2_1", new)):
                vals = [1000 * e["closure_seconds"] for row in data["samples"]
                        if row["family"] == family and row["enabled"] == enabled for e in row["events"]]
                samples[label] = {"n_closures": len(vals), "median_ms": q(vals, .5),
                                  "p90_ms": q(vals, .9), "max_ms": max(vals)}
            timing[f"{family}:{'induction' if enabled else 'frozen'}"] = samples
    checks = {
        "old_and_new_independent_analyses_admitted": old_a.get("admitted") is True and new_a.get("admitted") is True,
        "same_locked_case_schedule": old_l["inputs"]["cases"] == new_l["inputs"]["cases"],
        "60_cell_semantic_outcome_parity": len(old_ix) == len(new_ix) == 60 and all(semantic_equal.values()),
        "current_run_source_native_stable": new.get("source_native_stable") is True,
    }
    out = {"comparison": "v1.1 same-build process replicate 2 vs v1.2.1 current-source fresh replication",
           "checks": checks, "comparison_pass": all(checks.values()),
           "old_lock_sha256": sha(OLD_LOCK), "new_lock_sha256": sha(NEW_LOCK),
           "old_raw_sha256": sha(OLD_RAW), "new_raw_sha256": sha(NEW_RAW),
           "semantic_cell_parity": semantic_equal, "closure_time_ms": timing,
           "interpretation": "The repeated finite fixtures have exact status, quantum-count, and generator-state parity across the two captured source/build states. Timing differences are descriptive same-host observations; the v1.1 run and v1.2.1 run are not independent-environment replications and do not estimate timing uncertainty.",
           "limitations": ["Only three registered transforms, one point geometry, and ten repeats per arm/family.",
                           "No natural-task prevalence or arbitrary nonlinear induction is tested.",
                           "Closure timing is one host and process; do not infer a general complexity bound."]}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "timing_ms": timing}, indent=2))
    if not out["comparison_pass"]: raise SystemExit("current-source comparison integrity failed")

if __name__ == "__main__": main()
