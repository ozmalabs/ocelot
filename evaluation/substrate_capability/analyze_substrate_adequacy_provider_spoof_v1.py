#!/usr/bin/env python3
"""Verify caller-asserted provider spoof outcomes against oracle and receipt."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"evaluation/substrate_capability")]
RUNNER=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_spoof_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_spoof_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/substrate_adequacy_provider_spoof_v1_raw_20261002.json"
OUT=ROOT/"evaluation/reports/substrate_adequacy_provider_spoof_v1_analysis_20261002.json"


def main()->int:
    spec=importlib.util.spec_from_file_location("provider_spoof_runner",RUNNER)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    from domains import independent_adequacy as ia
    from independent_codewrite_oracles import label
    from substrate_rs import _native
    lock,raw=json.loads(LOCK.read_text()),json.loads(RAW.read_text());workers=raw.get("workers",[])
    checks=[]
    def check(name,ok,detail=None):checks.append({"name":name,"passed":bool(ok),"detail":detail})
    check("live_lock_matches",mod.lock_payload()==lock)
    check("capture_lock_and_post_lock",raw.get("lock")==lock and raw.get("post_lock")==lock)
    check("source_stable",raw.get("source_stable") is True and all(w["active_after"]==lock["active"] for w in workers))
    check("six_fresh_processes",len(workers)==6 and len({w["pid"] for w in workers})==6)
    check("matched_request_and_provider",len({w["request"]["request_id"] for w in workers})==1 and
          len({w["candidate_id"] for w in workers})==1 and
          len({w["request"]["probes"][0]["inputs"]["x"] for w in workers})==1 and
          len({w["audit_rows"][0]["labels"][0]["source_id"] for w in workers})==1 and
          len({w["audit_rows"][0]["labels"][0]["oracle_sha256"] for w in workers})==1)
    errors=[]
    native=_native.Substrate()
    for w in workers:
        label_row=w["audit_rows"][0]["labels"][0]
        truth=label("square",w["request"]["probes"][0]["inputs"])
        if label_row["oracle_sha256"]!=hashlib.sha256(mod.ORACLE.read_bytes()).hexdigest():errors.append((w["case"],"oracle hash"))
        if w["true_oracle_label"]!=truth:errors.append((w["case"],"independent oracle replay"))
        if w["receipt"]["request_id"]!=w["request"]["request_id"] or w["receipt"]["candidate_id"]!=w["candidate_id"]:
            errors.append((w["case"],"receipt binding"))
        if w["receipt"]["status"]=="accepted" and not ia.verify_accepted_receipt(w["receipt"],w["candidate_id"],w["term"]):
            errors.append((w["case"],"receipt integrity"))
        if w["case"]=="truthful":
            if label_row["expected"]!=truth or w["receipt"]["status"]!="rejected" or not w["receipt"]["residuals"]:
                errors.append((w["case"],"honest label not rejected"))
            if w["teach"].get("ok") or w["epoch_increment"]!=0 or w["written"]["ok"]:
                errors.append((w["case"],"honest false candidate changed state"))
        else:
            candidate_value=native.evaluate(w["term"],w["request"]["probes"][0]["inputs"])
            if label_row["expected"]==truth or label_row["expected"]!=candidate_value:
                errors.append((w["case"],"spoof label construction"))
            if w["receipt"]["status"]!="accepted" or not w["teach"].get("ok") or w["epoch_increment"]!=1:
                errors.append((w["case"],"spoof was not adopted"))
            if not w["written"]["ok"] or len(w["heldout"])!=4 or any(row["matches"] for row in w["heldout"]):
                errors.append((w["case"],"spoof adoption did not fail heldouts"))
            if "signature" in label_row:
                errors.append((w["case"],"unexpected signature field"))
    check("truth_and_spoof_replay",not errors,{"errors":errors[:8]})
    truthful=[w for w in workers if w["case"]=="truthful"]
    spoofed=[w for w in workers if w["case"]=="spoofed"]
    result={"schema":"SubstrateAdequacyProviderSpoofV1Analysis","passed":all(c["passed"] for c in checks),
        "checks":checks,"summary":{"truthful_rejected":sum(w["receipt"]["status"]=="rejected" for w in truthful),
        "truthful_refused":sum(not w["teach"].get("ok") for w in truthful),
        "spoof_accepted":sum(w["receipt"]["status"]=="accepted" for w in spoofed),
        "spoof_adopted":sum(w["teach"].get("ok") is True for w in spoofed),
        "spoof_heldout_exact":sum(bool(w["heldout"]) and all(r["matches"] for r in w["heldout"]) for w in spoofed),
        "oracle_true":truthful[0]["true_oracle_label"],"forged_claim":spoofed[0]["claimed_expected"],
        "provider_id_reused":truthful[0]["audit_rows"][0]["labels"][0]["source_id"]==spoofed[0]["audit_rows"][0]["labels"][0]["source_id"]},
        "analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"analysis":str(OUT.relative_to(ROOT))}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
