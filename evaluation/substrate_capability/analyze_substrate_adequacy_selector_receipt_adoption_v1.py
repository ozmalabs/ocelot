#!/usr/bin/env python3
"""Independent integrity and outcome audit for selector/receipt adoption."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "evaluation/substrate_capability")]
RUNNER = ROOT / "evaluation/substrate_capability/substrate_adequacy_selector_receipt_adoption_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selector_receipt_adoption_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selector_receipt_adoption_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_adequacy_selector_receipt_adoption_v1_analysis_20261002.json"


def main() -> int:
    spec = importlib.util.spec_from_file_location("selector_adoption_runner", RUNNER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    import substrate_rs
    from domains import independent_adequacy as ia
    from independent_codewrite_oracles import label
    lock, raw = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    checks = []
    def check(name, condition, detail=None): checks.append({"name":name,"passed":bool(condition),"detail":detail})
    check("live_source_lock_matches", mod.lock_payload() == lock)
    check("capture_lock_and_post_lock_match", raw.get("lock") == lock and raw.get("post_lock") == lock)
    check("worker_sources_stable", raw.get("source_stable") is True and all(w["active_after"] == lock["active"] for w in raw.get("workers", [])))
    workers = raw.get("workers", [])
    check("nine_fresh_processes", len(workers) == 9 and len({w["pid"] for w in workers}) == 9)
    check("three_repeats_per_case", all(sum(w["case"] == case for w in workers) == 3 for case in mod.CASES))
    native = substrate_rs._native.Substrate()
    errors = []
    for w in workers:
        case = w["case"]
        candidate_term = w["teach"]["reading"].get("term")
        request, receipt = w["request"], w["receipt"]
        selection = w["selection"]
        if not candidate_term:
            errors.append((case,w["repetition"],"candidate term missing")); continue
        if selection["input"] != request["probes"][0]["inputs"] or len(request["probes"]) != 1:
            errors.append((case,w["repetition"],"selection/request descriptor mismatch"))
        if request["candidate_id"] != w["candidate_id"] or receipt["candidate_id"] != w["candidate_id"] or w["teach"].get("candidate_id") != w["candidate_id"]:
            errors.append((case,w["repetition"],"candidate identity mismatch"))
        if receipt["request_id"] != request["request_id"] or receipt["term_sha256"] != request["term_sha256"]:
            errors.append((case,w["repetition"],"receipt/request mismatch"))
        probe = request["probes"][0]
        truth = label("square", probe["inputs"])
        prediction = native.evaluate(candidate_term, probe["inputs"])
        if w["audit_rows"][0]["labels"][0]["expected"] != truth or prediction != w["selection"]["predictions"][0]:
            errors.append((case,w["repetition"],"oracle or selector prediction mismatch"))
        if receipt["status"] == "accepted" and not ia.verify_accepted_receipt(receipt, w["candidate_id"], candidate_term):
            errors.append((case,w["repetition"],"accepted receipt integrity"))
        if receipt["status"] == "rejected" and not receipt["residuals"]:
            errors.append((case,w["repetition"],"rejected receipt lacks residual"))
        if w["teach"].get("ok") != (receipt["status"] == "accepted"):
            errors.append((case,w["repetition"],"teach/receipt outcome mismatch"))
        if w["epoch_increment"] != len(set(w["state_after"]["shape_ids"])-set(w["state_before"]["shape_ids"])):
            errors.append((case,w["repetition"],"epoch/shape delta mismatch"))
        if case == "wrong_identity_broad" and (receipt["status"] != "rejected" or w["epoch_increment"] != 0 or w["written"]["ok"]):
            errors.append((case,w["repetition"],"broad false candidate not refused"))
        if case == "correct_square" and (receipt["status"] != "accepted" or w["epoch_increment"] != 1 or not w["written"]["ok"] or not all(row["matches"] for row in w["heldout"])):
            errors.append((case,w["repetition"],"correct candidate did not transfer"))
        if case == "wrong_identity_alias" and (receipt["status"] != "accepted" or w["epoch_increment"] != 1 or not w["written"]["ok"] or any(row["matches"] for row in w["heldout"])):
            errors.append((case,w["repetition"],"alias false acceptance not exposed"))
    check("independent_receipt_and_outcome_audit", not errors, {"errors":errors[:8]})
    results = {case:{"receipt_statuses":{status:sum(w["case"]==case and w["receipt"]["status"]==status for w in workers) for status in ("accepted","rejected")},
                     "teach_adoptions":sum(w["case"]==case and w["teach"].get("ok") is True for w in workers),
                     "epoch_increments":[w["epoch_increment"] for w in workers if w["case"]==case],
                     "selected_inputs":[w["selection"]["input"] for w in workers if w["case"]==case],
                     "heldout_exact":sum(w["case"]==case and len(w["heldout"])==4 and all(r["matches"] for r in w["heldout"]) for w in workers)} for case in mod.CASES}
    result={"schema":"SubstrateAdequacySelectorReceiptAdoptionV1Analysis","passed":all(c["passed"] for c in checks),
            "checks":checks,"summary":{"workers":len(workers),"cases":results,
              "median_full_seed_boot_ms":sorted(w["boot_ns"] for w in workers)[len(workers)//2]/1e6},
            "analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"analysis":str(OUT.relative_to(ROOT))}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
