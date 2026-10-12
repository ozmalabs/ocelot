#!/usr/bin/env python3
"""Audit authenticated provider evidence outcomes and full-seed adoption."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"evaluation/substrate_capability")]
RUNNER=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_auth_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_auth_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/substrate_adequacy_provider_auth_v1_raw_20261002.json"
OUT=ROOT/"evaluation/reports/substrate_adequacy_provider_auth_v1_analysis_20261002.json"


def main()->int:
    spec=importlib.util.spec_from_file_location("provider_auth_runner",RUNNER)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    from domains import independent_adequacy as ia
    from domains.adequacy_provider_auth import verify_signed_audit_evidence
    from independent_codewrite_oracles import label as oracle_label
    from substrate_rs import _native
    lock,raw=json.loads(LOCK.read_text()),json.loads(RAW.read_text());workers=raw.get("workers",[])
    checks=[]
    def check(name,ok,detail=None):checks.append({"name":name,"passed":bool(ok),"detail":detail})
    check("live_lock_matches",mod.payload()==lock)
    check("capture_lock_and_post_lock",raw.get("lock")==lock and raw.get("post_lock")==lock)
    check("source_native_seed_stable",raw.get("source_stable") is True and all(w["active_after"]==lock["active"] for w in workers))
    check("twelve_fresh_processes",len(workers)==12 and len({w["pid"] for w in workers})==12)
    check("three_repetitions_per_case",all(sum(w["case"]==c for w in workers)==3 for c in mod.CASES))
    native=_native.Substrate();keys={w["evidence"][0]["labels"][0]["source_id"]:mod.TEST_KEY for w in workers}
    errors=[]
    for w in workers:
        req,rows,receipt=w["request"],w["evidence"],w["receipt"]
        probe=req["probes"][0]
        truth=oracle_label("square",probe["inputs"])
        if w["true_label"]!=truth:errors.append((w["case"],"oracle replay"))
        if receipt["request_id"]!=req["request_id"] or receipt["candidate_id"]!=w["candidate_id"]:errors.append((w["case"],"receipt binding"))
        expected_auth=verify_signed_audit_evidence(req,rows,receipt,keys)
        got_auth=w["teach"].get("provider_auth",{})
        if got_auth.get("ok")!=expected_auth["ok"]:errors.append((w["case"],"auth verifier replay"))
        for control in w["negative_controls"].values():
            if control.get("ok") is not False:errors.append((w["case"],"negative control accepted"))
        if w["epoch_increment"]!=len(set(w["state_after"]["shape_ids"])-set(w["state_before"]["shape_ids"])):
            errors.append((w["case"],"epoch/shape delta"))
        case=w["case"]
        if case=="honest_wrong_candidate":
            if not got_auth.get("ok") or receipt["status"]!="rejected" or w["teach"].get("ok") or w["epoch_increment"]!=0:
                errors.append((case,"honest wrong candidate should authenticate then refuse"))
        elif case=="forged_unsigned":
            if receipt["status"]!="accepted" or got_auth.get("ok") or w["teach"].get("ok") or w["epoch_increment"]!=0:
                errors.append((case,"unsigned spoof passed or mutated state"))
            if rows[0]["labels"][0]["expected"]!=native.evaluate(w["term"],probe["inputs"]):errors.append((case,"forgery is not candidate-matching"))
        elif case=="trusted_incorrect":
            if not got_auth.get("ok") or receipt["status"]!="accepted" or not w["teach"].get("ok") or w["epoch_increment"]!=1:
                errors.append((case,"trusted incorrect evidence did not demonstrate authority limit"))
            if len(w["heldout"])!=4 or any(r["matches"] for r in w["heldout"]):errors.append((case,"false adoption not exposed"))
        elif case=="correct_candidate":
            if not got_auth.get("ok") or receipt["status"]!="accepted" or not w["teach"].get("ok") or w["epoch_increment"]!=1:
                errors.append((case,"correct candidate not adopted"))
            if len(w["heldout"])!=4 or not all(r["matches"] for r in w["heldout"]):errors.append((case,"correct heldout transfer failed"))
    check("signature_and_teach_outcome_replay",not errors,{"errors":errors[:10]})
    result={"schema":"SubstrateAdequacyProviderAuthV1Analysis","passed":all(c["passed"] for c in checks),
      "checks":checks,"summary":{"workers":len(workers),
       "unsigned_forgery_blocked":sum(w["case"]=="forged_unsigned" and not w["teach"].get("ok") for w in workers),
       "trusted_false_labels_adopted":sum(w["case"]=="trusted_incorrect" and w["teach"].get("ok") for w in workers),
       "honest_candidate_residuals_refused":sum(w["case"]=="honest_wrong_candidate" and not w["teach"].get("ok") for w in workers),
       "correct_adoptions":sum(w["case"]=="correct_candidate" and w["teach"].get("ok") for w in workers),
       "negative_controls_rejected":sum(not c["ok"] for w in workers for c in w["negative_controls"].values()),
       "negative_controls_total":sum(len(w["negative_controls"]) for w in workers),
       "median_full_seed_boot_ms":sorted(w["boot_ns"] for w in workers)[len(workers)//2]/1e6},
      "analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"analysis":str(OUT.relative_to(ROOT))}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
