#!/usr/bin/env python3
"""Score consumer fail-closed and post-commit wakeup behavior."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/committed_result_consumer_gate_v1_2_20260928.json";OUT=ROOT/"evaluation/reports/committed_result_consumer_gate_v1_2_analysis_20260928.json";SIZES=(2,8,32,64);DISTS=("unique_max","tied_max")
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_cells":all(len(r["cells"])==8 for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   p=f"{r['worker_id']}_{c['n']}_{c['distribution']}";a,b,z=c["checkpoints"]
   g[p+"_rejects_incomplete"]=(a["report"]["status"]=="fixed_point" and a["attrs"].get("resolved_revision")==0 and "consumed_label" not in a["attrs"])
   g[p+"_rejects_uncommitted"]=(b["report"]["status"]=="fixed_point" and b["attrs"].get("max_revision")==b["attrs"].get("count_revision")==b["attrs"].get("decision_revision")==1 and b["attrs"].get("resolved_revision")==0 and "consumed_label" not in b["attrs"])
   g[p+"_commit_gate_and_consumer"]=(z["report"]["status"]=="fixed_point" and z["attrs"].get("resolved_revision")==1 and z["attrs"].get("consumed_label")==c["expected_consumed"])
   cells.append({"n":c["n"],"distribution":c["distribution"],"expected":c["expected_consumed"],"checkpoints":[{"name":x["name"],"attrs":x["attrs"],"progress":x["report"]["progress_steps"],"metrics":{k:v for k,v in x["metrics"].items() if not k.endswith("_ns")},"elapsed_ns":x["elapsed_ns"]} for x in c["checkpoints"]]})
  norm.append(cells)
 def signature(cells):
  return [{"n":c["n"],"distribution":c["distribution"],"expected":c["expected"],"checkpoints":[{k:v for k,v in z.items() if k!="elapsed_ns"} for z in c["checkpoints"]]} for c in cells]
 g["integer_work_counts_replicate"]=signature(norm[0])==signature(norm[1])==signature(norm[2])
 summary=[]
 for c in norm[0]:summary.append({"n":c["n"],"distribution":c["distribution"],"consume_before_commit":c["checkpoints"][0]["attrs"].get("consumed_label"),"consume_while_stages_uncommitted":c["checkpoints"][1]["attrs"].get("consumed_label"),"consume_after_commit":c["checkpoints"][2]["attrs"].get("consumed_label"),"commit_progress":c["checkpoints"][2]["progress"]})
 report={"analysis":"Committed-result consumer gate v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"cells_by_worker":norm,"interpretation":"The authored consumer rule rejects incomplete and complete-but-uncommitted stage fields, then consumes the selected label after the resolved_revision commit changes.","limits":["One authored consumer rule only; no universal enforcement of graph reads.","No persistence, concurrency, or production consumers are exercised.","Empty string represents a committed ambiguous/no-selection result."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
