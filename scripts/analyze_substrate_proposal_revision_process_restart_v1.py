#!/usr/bin/env python3
"""Verify true process restart, checkpoint parity, and resumed oracle results."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/proposal_revision_process_restart_v1_20260928.json";OUT=ROOT/"evaluation/reports/proposal_revision_process_restart_v1_analysis_20260928.json";SIZES=(2,16,64);CUTS=(0,1,2,3)
def simple_stages(stages):return [{"stage":x["stage"],"report":x["report"],"metrics":{k:v for k,v in x["metrics"].items() if not k.endswith("_ns")}} for x in stages]
def main():
 d=json.loads(RAW.read_text());runs=d["runs"];g={"three_workers":len(runs)==3,"locked_inputs_match":all(r["started_inputs"]==d["locked_inputs"] for r in runs),"all_cells":all(len(r["cells"])==12 for r in runs)};norm=[]
 for r in runs:
  cells=[]
  for c in r["cells"]:
   n=c["n"];cut=c["cut"];p=f"{r['worker_id']}_{n}_cut{cut}";prod=c["producer"];res=c["resume"];cp=c["checkpoint"];before=res["state_before_resume"];final=res["final_state"];ta=final["target"];oracle=final["oracle"]
   file=ROOT/cp["path"];data=file.read_bytes() if file.exists() else b""
   g[p+"_distinct_processes"]=(prod["pid"]!=res["pid"])
   g[p+"_checkpoint_manifest"]=(cp["matches_producer_manifest"] and len(data)==cp["bytes"] and hashlib.sha256(data).hexdigest()==cp["sha256"])
   g[p+"_roundtrip_exact"]=(res["graph_roundtrip_exact"] and res["grammar_roundtrip_exact"] and res["rules_roundtrip_exact"])
   g[p+"_precommit_fail_closed"]=(before["target"].get("resolved_revision")==0 and "consumed_label" not in before["target"] and before["revision_nodes"]==1)
   expected=["max","count","decision"][cut:]+["commit"]
   g[p+"_resume_exact_missing_stages"]=[x["stage"] for x in res["resume_stages"]]==expected
   g[p+"_all_resumed_closures_fixed"]=(all(x["report"]["status"]=="fixed_point" for x in res["resume_stages"]) and all(x["report"]["status"]=="fixed_point" for x in prod["partial_stages"]))
   g[p+"_final_oracle_and_commit"]=(ta.get("resolved_revision")==1 and all(ta.get(k)==1 for k in ("max_revision","count_revision","decision_revision")) and ta.get("max_score")==n-2 and ta.get("top_count")==1 and ta.get("ambiguous") is False and ta.get("selected_label")==f"p{n-2:03d}" and ta.get("consumed_label")==f"p{n-2:03d}" and oracle["max_score"]==n-2 and oracle["top_labels"]==[f"p{n-2:03d}"] and final["revision_nodes"]==1)
   cells.append({"n":n,"cut":cut,"producer_pid":prod["pid"],"resume_pid":res["pid"],"checkpoint":cp,"roundtrip":{"graph":res["graph_roundtrip_exact"],"grammar":res["grammar_roundtrip_exact"],"rules":res["rules_roundtrip_exact"]},"pre_resume":before,"partial_stages":simple_stages(prod["partial_stages"]),"partial_stage_names":prod["partial_stage_names"],"resume_stages":simple_stages(res["resume_stages"]),"final_target":ta,"oracle":oracle})
  norm.append(cells)
 # Compare deterministic checkpoint-independent semantic/work projections; remove PIDs, paths, hashes, and elapsed times.
 def sig(cells):
  return [{"n":c["n"],"cut":c["cut"],"roundtrip":c["roundtrip"],"pre_resume":c["pre_resume"],"partial_stage_names":c["partial_stage_names"],"partial_stages":[{k:v for k,v in x.items() if k!="elapsed_ns"} for x in c["partial_stages"]],"resume_stages":[{k:v for k,v in x.items() if k!="elapsed_ns"} for x in c["resume_stages"]],"final_target":c["final_target"],"oracle":c["oracle"]} for c in cells]
 g["integer_work_counts_replicate"]=sig(norm[0])==sig(norm[1])==sig(norm[2])
 summary=[]
 for n in SIZES:
  summary.append({"n":n,"cuts":{str(c["cut"]):{"checkpoint_bytes":c["checkpoint"]["bytes"],"resume_stages":[x["stage"] for x in c["resume_stages"]],"selected":c["final_target"]["selected_label"],"consumer":c["final_target"].get("consumed_label")} for c in norm[0] if c["n"]==n}})
 report={"analysis":"Proposal revision recovery across process restart v1","all_gates_pass":all(g.values()),"gates":g,"summary":summary,"cells_by_worker":norm,"interpretation":"A producer process writes graph, grammar, rule store, IDs, and partial revision state; a distinct process restores exact graph/grammar/rules, resumes missing stages, commits, and awakens the guarded consumer.","limits":["Clean process boundary only; no injected OS kill, power loss, or torn write.","No schema migration, concurrent writer, in-closure failure atomicity, or universal consumer enforcement.","JSON checkpoints are fsync'ed on this local filesystem; no general hardware durability guarantee."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_gates_pass":report["all_gates_pass"],"failed":[k for k,v in g.items() if not v],"summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report["all_gates_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
