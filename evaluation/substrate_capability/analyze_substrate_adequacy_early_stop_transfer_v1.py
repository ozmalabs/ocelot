#!/usr/bin/env python3
"""Independent replay and aggregate gates for early-stop transfer v1."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/substrate_adequacy_early_stop_transfer_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_early_stop_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_early_stop_transfer_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_early_stop_transfer_v1_analysis_20261002.json"


def main() -> int:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    spec = importlib.util.spec_from_file_location("early_stop_v1", RUNNER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    lock, raw = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    checks = []
    def check(name, ok, detail=None): checks.append({"name": name, "passed": bool(ok), "detail": detail})
    check("live_lock_matches", mod.payload() == lock)
    check("raw_lock_and_post_lock_match", raw.get("lock") == lock and raw.get("post_lock") == lock)
    check("capture_source_stable", raw.get("source_stable") is True)
    rows = raw.get("workers", [])
    identities = {(r["case"], r["policy"], r["budget"], r["repetition"]) for r in rows}
    check("complete_1440_panel", len(rows) == 1440 and len(identities) == 1440, {"rows": len(rows)})
    from substrate_rs import _native
    native = _native.Substrate()
    cases = mod.family_cases()
    errors = []
    for row in rows:
        task = cases[row["case"]]
        if len(row["trace"]) != row["labels_used"] or row["labels_used"] > row["budget"]:
            errors.append((row["case"], row["policy"], row["repetition"], "label-budget")); continue
        seen = set()
        for item in row["trace"]:
            env = item["input"]
            descriptor = json.dumps(env, sort_keys=True, separators=(",", ":"))
            if descriptor in seen or env not in task["domain"]:
                errors.append((row["case"], row["policy"], row["repetition"], "domain-duplicate")); break
            seen.add(descriptor)
            oracle = mod.target_value(task["target_kind"], env)
            pred = float(native.evaluate(task["candidate"], env))
            if oracle != item["oracle_label"] or pred != item["candidate_prediction"] or (pred == oracle) != item["candidate_match"]:
                errors.append((row["case"], row["policy"], row["repetition"], "native-oracle replay")); break
        if row["stop_reason"] == "candidate_residual" and (not row["trace"] or row["trace"][-1]["candidate_match"]):
            errors.append((row["case"], row["policy"], row["repetition"], "invalid early stop"))
        if row["candidate_accepted"] != all(t["candidate_match"] for t in row["trace"]):
            errors.append((row["case"], row["policy"], row["repetition"], "acceptance mismatch"))
    check("independent_native_and_label_replay", not errors, {"errors": errors[:5]})
    group = lambda c,p,k: [r for r in rows if r["case"] == c and r["policy"] == p and r["budget"] == k]
    entropy_broad_rejects = all(sum(r["candidate_accepted"] for r in group(c, "maximum_prediction_entropy", k)) == 0
        for c in ("poly_represented_wrong", "poly_omitted_target", "vector_represented_wrong", "vector_omitted_target") for k in (1,2,4))
    check("entropy_rejects_broad_wrong_candidates_after_early_stop", entropy_broad_rejects)
    entropy_correct = all(sum(r["candidate_accepted"] and r["candidate_heldout_exact"] for r in group(c,"maximum_prediction_entropy",k)) == 30
        for c in ("poly_correct", "vector_correct") for k in (1,2,4))
    check("entropy_accepts_correct_candidates", entropy_correct)
    alias_cases = ("poly_alias_only", "vector_alias_only")
    alias_failure = all(sum(r["candidate_accepted"] and not r["candidate_heldout_exact"] for r in group(c,p,k)) == 30
        for c in alias_cases for p in ("seeded_hash", "maximum_prediction_entropy") for k in (1,2,4))
    check("alias_only_domains_still_false_accept", alias_failure)
    stop_saving = all(all(r["labels_used"] == 1 for r in group(c,"maximum_prediction_entropy",k))
        for c in ("poly_represented_wrong", "poly_omitted_target", "vector_represented_wrong", "vector_omitted_target") for k in (1,2,4))
    check("early_stop_uses_one_label_for_entropy_residuals", stop_saving)
    hash_false = {family: sum(r["candidate_accepted"] for r in rows if r["family"] == family and r["case"].endswith(("represented_wrong","omitted_target")) and r["policy"] == "seeded_hash" and r["budget"] == 1)
                  for family in ("sparse_polynomial","two_variable_arithmetic")}
    entropy_false = {family: sum(r["candidate_accepted"] for r in rows if r["family"] == family and r["case"].endswith(("represented_wrong","omitted_target")) and r["policy"] == "maximum_prediction_entropy" and r["budget"] == 1)
                     for family in hash_false}
    transfer = all(entropy_false[f] < hash_false[f] for f in hash_false)
    check("one_label_reduction_transfers_across_families", transfer, {"hash": hash_false,"entropy": entropy_false})
    summary = {"workers": len(rows), "hash_false_accepts_budget1": hash_false,
               "entropy_false_accepts_budget1": entropy_false,
               "entropy_wrong_candidate_median_labels": {str(k): sorted(r["labels_used"] for r in rows if r["case"].endswith(("represented_wrong","omitted_target")) and r["policy"] == "maximum_prediction_entropy" and r["budget"] == k)[len([r for r in rows if r["case"].endswith(("represented_wrong","omitted_target")) and r["policy"] == "maximum_prediction_entropy" and r["budget"] == k])//2] for k in (1,2,4)},
               "alias_false_accepts": {c: sum(r["candidate_accepted"] for r in rows if r["case"] == c and r["policy"] == "maximum_prediction_entropy" and r["budget"] == 1) for c in alias_cases}}
    result = {"schema":"SubstrateAdequacyEarlyStopTransferV1Analysis", "passed":all(c["passed"] for c in checks),
              "checks":checks, "summary":summary,
              "analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "analysis":str(OUT.relative_to(ROOT))}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
