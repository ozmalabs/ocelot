#!/usr/bin/env python3
"""Analyze source-locked edge-matched exact-inference costs."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002.json"
LOCK=ROOT/"evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3_lock_20261002.json"
RUNNER=ROOT/"evaluation/substrate_capability/can_edge_matched_inference_cost_v1_3.py"
OUT=ROOT/"evaluation/reports/can_edge_matched_inference_cost_v1_3_20261002_analysis.json"
def main():
 cap=json.loads(CAP.read_text()); lock=json.loads(LOCK.read_text())
 spec=importlib.util.spec_from_file_location("inference_runner",RUNNER); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
 assert cap["input_lock"]==cap["post_run_input_lock"]==lock==r.input_lock()
 rows=cap["runs"]; assert len(rows)==36 and all(cap["checks"].values())
 cells=[]
 for q in r.WIDTHS:
  for family in r.FAMILIES:
   g=[x for x in rows if x["width"]==q and x["family"]==family]
   med=lambda k: statistics.median(x["timing_ns"][k] for x in g)/1e6
   cells.append({"width":q,"family":family,"replicates":len(g),
    "minfill_width_counts":{str(k):sum(x["minfill_width"]==k for x in g) for k in sorted({x["minfill_width"] for x in g})},
    "median_ms":{"graph_construction":med("graph_construction"),"runtime_extraction":med("runtime_extraction"),
      "minfill_order":med("minfill_order"),"oracle":med("oracle"),"jt_minfill":med("jt_minfill_wall"),
      "jt_certificate":med("jt_certificate_wall")},
    "median_traced_peak_bytes":{"jt_minfill":int(statistics.median(x["traced_peak_bytes"]["jt_minfill"] for x in g)),
      "jt_certificate":int(statistics.median(x["traced_peak_bytes"]["jt_certificate"] for x in g))},
    "median_process_peak_rss_kib":int(statistics.median(x["process_peak_rss_kib"] for x in g)),
    "profile_medians":{"minfill":{"message_entries":int(statistics.median(x["decomposition_profiles"]["minfill"]["message_entries"] for x in g)),
      "bag_assignments":int(statistics.median(x["decomposition_profiles"]["minfill"]["bag_assignments"] for x in g)),
      "estimated_inner_loop_iterations":int(statistics.median(x["decomposition_profiles"]["minfill"]["estimated_inner_loop_iterations"] for x in g)),
      "estimated_local_energy_term_visits":int(statistics.median(x["decomposition_profiles"]["minfill"]["estimated_local_energy_term_visits"] for x in g))},
      "certificate":{"message_entries":int(statistics.median(x["decomposition_profiles"]["certificate"]["message_entries"] for x in g)),
      "bag_assignments":int(statistics.median(x["decomposition_profiles"]["certificate"]["bag_assignments"] for x in g)),
      "estimated_inner_loop_iterations":int(statistics.median(x["decomposition_profiles"]["certificate"]["estimated_inner_loop_iterations"] for x in g)),
      "estimated_local_energy_term_visits":int(statistics.median(x["decomposition_profiles"]["certificate"]["estimated_local_energy_term_visits"] for x in g))}},
    "minfill_false_refusals_at_bound_q":sum(x["minfill_width"]>q for x in g)})
 out={"schema_version":1,"capture_sha256":hashlib.sha256(CAP.read_bytes()).hexdigest(),
  "lock_matches_live_inputs":True,"workers":len(rows),"integrity_gates_pass":all(cap["checks"].values()),"cells":cells,
  "claim_boundary":cap["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":OUT.relative_to(ROOT).as_posix(),"workers":len(rows),"all_gates":out["integrity_gates_pass"]},indent=2))
if __name__=="__main__": main()
