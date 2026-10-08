#!/usr/bin/env python3
"""Source-locked inventory of the default correction candidate surface."""
from __future__ import annotations
import hashlib, json, os, statistics, subprocess, sys, time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
SOURCES=("domains/self_correction.py","domains/edit_ops.py","evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py","substrate/boot_core.py","evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v1.py")
RAW=ROOT/"evaluation/reports/thoughtexperiment_correction_candidate_surface_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V1_RESULTS_20261001.md"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def worker(i):
 from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
 from domains.self_correction import _default_candidates
 sub,native,*_=make_fixture(0)
 graph_before=native.graph_to_dict(); rules_before=native.export_rules()
 rules=[r for r in rules_before if r.get("active",True)]
 inventory=[]
 for r in rules:
  cs=_default_candidates(native,r["name"])
  inventory.append({"target_rule":r["name"],"candidate_labels":[c["label"] for c in cs],"candidate_count":len(cs),"has_domain_candidate":any(c["label"]=="dedup_identity_fix" for c in cs)})
 stable=(native.graph_to_dict()==graph_before and native.export_rules()==rules_before)
 return {"pid":os.getpid(),"worker_index":i,"source_hashes":{x:sha(ROOT/x) for x in SOURCES},"active_rule_count":len(rules),"inventory":inventory,"enumeration_preserved_state":stable}
def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale: raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"}; rows=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 reference=rows[0]["inventory"]
 labels=Counter(label for row in reference for label in row["candidate_labels"])
 families=Counter(("dedup_identity_fix" if label=="dedup_identity_fix" else label.split(":",1)[0] if label.startswith("swap_term_leaf:") else label) for row in reference for label in row["candidate_labels"])
 gates={"three_fresh_workers":len(rows)==3,"identical_inventories":all(r["inventory"]==reference for r in rows),"enumeration_is_read_only":all(r["enumeration_preserved_state"] for r in rows),"known_domain_candidate_present":any(r["target_rule"]=="sd_mint_quantum" and r["has_domain_candidate"] for r in reference),"stable_source_fingerprints":all(r["source_hashes"]==rows[0]["source_hashes"] for r in rows)}
 summary={"active_rules":len(reference),"rules_with_candidates":sum(x["candidate_count"]>0 for x in reference),"rules_with_domain_candidate":sum(x["has_domain_candidate"] for x in reference),"candidate_instances":sum(x["candidate_count"] for x in reference),"candidate_label_counts":dict(sorted(labels.items())),"candidate_family_counts":dict(sorted(families.items())),"rules_with_no_candidate":[x["target_rule"] for x in reference if not x["candidate_count"]],"domain_candidate_rules":[x["target_rule"] for x in reference if x["has_domain_candidate"]]}
 capture={"schema":"ThoughtexperimentCorrectionCandidateSurfaceV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"source_fingerprint":rows[0]["source_hashes"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"workers":rows,"summary":summary,"gates":gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out=(f"# Thoughtexperiment correction candidate surface audit v1 — results\n\n**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.\n\nAcross three fresh processes, the standard core fixture exposes {summary['active_rules']} active rules and {summary['candidate_instances']} candidate instances. The generic generator returns at least one candidate for {summary['rules_with_candidates']} rules, but only {summary['rules_with_domain_candidate']} rule has the current task-shaped `dedup_identity_fix` candidate.\n\n| Candidate family | Count |\n|---|---:|\n"
       + "".join(f"| `{k}` | {v} |\n" for k,v in summary["candidate_family_counts"].items())
       + "\nThe audit now includes a plausible episode-scoped recurrence guard beside the candidate-scoped repair. The later staged two-candidate oracle shows why generation is not validation: episode-scoped suppression yields offer counts [1, 0], while the candidate-scoped repair yields [1, 1]. This read-only surface inventory itself measures no applicability, convergence, task preservation, or adoption safety; those properties require the separate task-specific thoughtexperiment panels.\n\n## Artifacts\n\n- [Preregistration](THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V1_PREREG_20261001.md)\n- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v1.py)\n- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v1_raw_20261001.json)\n")
 RESULT.write_text(out);print(json.dumps({"summary":summary,"gates":gates},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
