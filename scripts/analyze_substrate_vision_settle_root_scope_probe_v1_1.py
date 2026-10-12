#!/usr/bin/env python3
"""Independent arithmetic and provenance audit for the corrected scope probe."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_vision_settle_root_scope_probe_v1_1_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/vision_settle_root_scope_probe_v1_1_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_vision_settle_root_scope_probe_v1_1_analysis_20260925.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); p=raw["provenance"]
 global_arms=[a["result"] for a in raw["arms"] if a["variant"]=="global"]
 scoped_arms=[a["result"] for a in raw["arms"] if a["variant"]=="root_scoped"]
 exp_global=[[[.5,.5],[0,0]][i] for i in range(2)]
 exp_scoped=[[0,0],[0,0]]
 checks={"hashes_match_lock":lock["hashes"]["runner"]==p["runner_sha256"] and lock["hashes"]["protocol"]==p["protocol_sha256"] and lock["hashes"]["seed"]==p["seed_sha256"] and lock["hashes"]["analyzer"]==sha(Path(__file__)),
 "extension_matches_lock":lock["native_extension_sha256"]==p["native_extension_sha256"],
 "engine_matches_source":p["engine_provenance"]["source_match"] in ("own","shared") and not p["engine_provenance"]["stale_rust"],
 "all_calls_progressed":all(x["progress"]>0 and x["complete"] for x in global_arms+scoped_arms),
 "global_equation":[x["a_act_next"] for x in global_arms]==exp_global,
 "root_scoped_equation":[x["a_act_next"] for x in scoped_arms]==exp_scoped,
 "global_cross_world_coupling":global_arms[0]["a_act_next"]!=global_arms[1]["a_act_next"],
 "root_scoped_invariant":scoped_arms[0]["a_act_next"]==scoped_arms[1]["a_act_next"]}
 result={"run_id":"vision-settle-root-scope-probe-independent-audit-v1.1","raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"analyzer_sha256":sha(Path(__file__)),"checks":checks,"pass":all(checks.values()),"claim_boundary":["Verifies DSL expression and native semantics on two minimal pairs only.","Does not establish full-sheet fidelity, task quality, convergence, or runtime costs.","The v1 preregistered numeric prediction failed; v1.1 corrects it by direct substitution in the authored equation."]}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"pass":result["pass"]},indent=2))
 if not result["pass"]: raise SystemExit("independent audit failed")
if __name__=="__main__": main()
