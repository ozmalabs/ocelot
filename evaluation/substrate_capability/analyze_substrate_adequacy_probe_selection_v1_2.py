#!/usr/bin/env python3
"""Independent outcome and integrity audit for probe-selection v1.2."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = ROOT / "evaluation/substrate_capability/substrate_adequacy_probe_selection_v1_2.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_probe_selection_v1_2_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_probe_selection_v1_2_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_probe_selection_v1_2_analysis_20261002.json"


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location("probe_selection_v12", RUNNER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    lock = json.loads(LOCK.read_text()); raw = json.loads(RAW.read_text())
    checks = []
    def check(name, condition, detail=None):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
    current = mod.payload()
    check("lock_matches_live_sources", lock == current)
    check("capture_locks_match", raw.get("lock") == lock and raw.get("post_lock") == lock)
    check("source_stable_flag", raw.get("source_stable") is True)
    rows = raw.get("workers", [])
    check("complete_720_cell_capture", len(rows) == 720 and len({(r["case"], r["policy"], r["budget"], r["repetition"]) for r in rows}) == 720,
          {"rows": len(rows)})
    from substrate_rs import _native
    native = _native.Substrate()
    def oracle(x: int, scale: int) -> float:
        product = 1
        for root in range(1, 13): product *= x - root
        return float(x + scale * product)
    trace_errors = []
    for row in rows:
        case = row["case"]
        scale = 1 if case in ("represented_wrong", "correct_adoption") else 2
        allowed = set(range(1, 13 if case == "finite_alias" else 14))
        if len(row["trace"]) != min(row["budget"], len(allowed)):
            trace_errors.append((case, row["policy"], row["budget"], "budget")); continue
        seen = set()
        for item in row["trace"]:
            env = item["input"]
            x = env.get("x")
            if x not in allowed or x in seen:
                trace_errors.append((case, row["policy"], row["budget"], "domain_or_duplicate")); break
            seen.add(x)
            candidate = float(native.evaluate(mod.cases()[case]["candidate"], env))
            if candidate != item["candidate_prediction"] or oracle(x, scale) != item["oracle_label"] or (candidate == oracle(x, scale)) != item["candidate_match"]:
                trace_errors.append((case, row["policy"], row["budget"], "semantic_replay")); break
    check("independent_native_and_oracle_replay", not trace_errors, {"errors": trace_errors[:5]})
    group = lambda case, policy, budget: [r for r in rows if r["case"] == case and r["policy"] == policy and r["budget"] == budget]
    broad_wrong_gates = all(sum(r["candidate_accepted"] for r in group(case, "maximum_prediction_entropy", k)) == 0
                            for case in ("represented_wrong", "omitted_target") for k in (1, 2, 4))
    check("entropy_rejects_broad_wrong_candidates", broad_wrong_gates)
    useful = all(sum(r["candidate_accepted"] for r in group("correct_adoption", "maximum_prediction_entropy", k)) == 30
                 and sum(r["candidate_heldout_exact"] for r in group("correct_adoption", "maximum_prediction_entropy", k)) == 30
                 for k in (1, 2, 4))
    check("entropy_preserves_correct_candidate", useful)
    aliases = all(sum(r["candidate_accepted"] for r in group("finite_alias", policy, k)) == 30
                  and sum(r["candidate_heldout_exact"] for r in group("finite_alias", policy, k)) == 0
                  for policy in ("seeded_hash", "maximum_prediction_entropy") for k in (1, 2, 4))
    check("alias_only_domain_false_accepts", aliases)
    hash_false = sum(r["candidate_accepted"] for case in ("represented_wrong", "omitted_target")
                     for r in group(case, "seeded_hash", 1))
    entropy_false = sum(r["candidate_accepted"] for case in ("represented_wrong", "omitted_target")
                        for r in group(case, "maximum_prediction_entropy", 1))
    check("entropy_improves_fixed_one_label_false_acceptance", entropy_false < hash_false,
          {"hash_false_accepts": hash_false, "entropy_false_accepts": entropy_false})
    check("broad_entropy_selects_witness_first", all(r["selected"][0] == {"x": 13}
          for r in rows if r["policy"] == "maximum_prediction_entropy" and r["case"] != "finite_alias"))
    result = {"schema": "SubstrateAdequacyProbeSelectionV1_2Analysis", "passed": all(c["passed"] for c in checks),
              "checks": checks, "summary": {"workers": len(rows), "hash_one_label_false_accepts": hash_false,
              "entropy_one_label_false_accepts": entropy_false,
              "entropy_broad_wrong_false_accepts_by_budget": {str(k): sum(r["candidate_accepted"] for case in ("represented_wrong", "omitted_target") for r in group(case, "maximum_prediction_entropy", k)) for k in (1, 2, 4)},
              "entropy_correct_accepts_by_budget": {str(k): sum(r["candidate_accepted"] for r in group("correct_adoption", "maximum_prediction_entropy", k)) for k in (1, 2, 4)},
              "alias_only_false_accepts_per_policy_budget": 30},
              "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "analysis": str(OUT.relative_to(ROOT))}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
