#!/usr/bin/env python3
"""Source-locked fresh-boot probe for the live self-report route."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_ROUTE_REGRESSION_V1_PREREG_20260927.md"
OUT=ROOT/"evaluation/reports/live_self_report_route_regression_v1_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def worker(rep):
 import substrate_live_self_report_dimension_frame_v1 as frame
 start=frame.lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot=load_all_seeds(a)
 reply=str(a.converse("report your organisation",speech_act="instruction",speaker="alice"))
 m=a._last_turn_inbound;attrs=dict(a.s.node(m)["attrs"])
 goals=[g for g in a.s.nodes("Goal") if m in a.inner.neighbours(g,"comprehends")]
 goal_rows=[]
 for g in goals:
  ga=dict(a.s.node(g)["attrs"]);evs=sorted(a.inner.neighbours(g,"transitioned_by"),key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  goal_rows.append({"id":int(g.value if hasattr(g,"value") else g),"kind":ga.get("kind"),"status":ga.get("lifecycle_status"),"transitions":[a.s.node(e)["attrs"].get("kind") for e in evs]})
 graph=a.s.graph_to_dict();end=frame.lock_inputs()
 return {"replicate":rep,"pid":os.getpid(),"route":attrs.get("communication_route"),"reply":reply,"goal_count":len(goals),"goals":goal_rows,
  "loaded_seed_count":len(boot.get("loaded_seed_ids",[])),"failed_seeds":boot.get("failed",[]),
  "conversation_seeds_loaded":[s for s in boot.get("loaded_seed_ids",[]) if "conversation" in s or "discourse" in s],
  "graph_nodes":len(graph.get("nodes",[])),"graph_edges":len(graph.get("edges",[])),"semantic_graph_sha256":frame.semantic_digest(graph),
  "worker_start_lock":start,"worker_end_lock":end}
def main():
 if sys.argv[1:2]==["--worker"]:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 if sys.argv[1:2]==["--lock"]:
  import substrate_live_self_report_dimension_frame_v1 as frame
  print(json.dumps({"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_lock":frame.lock_inputs()},sort_keys=True,indent=2));return
 import substrate_live_self_report_dimension_frame_v1 as frame
 lock={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_lock":frame.lock_inputs()}
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260927).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout));print(f"completed replicate={rep}",flush=True)
 post=frame.lock_inputs()
 payload={"schema_version":1,"run_id":"live-self-report-route-regression-v1-20260927","protocol_sha256":lock["protocol_sha256"],"runner_sha256":lock["runner_sha256"],"locked_inputs":lock["source_lock"],"post_run_inputs":post,"runs":runs,
  "checks":{"three_distinct_processes":len({x["pid"] for x in runs})==3,"worker_and_driver_sources_stable":post==lock["source_lock"] and all(x["worker_start_lock"]==lock["source_lock"]==x["worker_end_lock"] for x in runs),"same_route_reply_and_lifecycle":len({(x["route"],x["reply"],json.dumps(x["goals"],sort_keys=True)) for x in runs})==1,"route_failure_reproduced":all(x["route"] is None and x["goal_count"]==0 and "no faculty for it yet" in x["reply"] for x in runs),"boot_failure_profile_repeats":len({json.dumps(x["failed_seeds"],sort_keys=True) for x in runs})==1,"semantic_graph_repeats":len({(x["graph_nodes"],x["graph_edges"],x["semantic_graph_sha256"]) for x in runs})==1},
  "environment":{"python":sys.version,"platform":platform.platform()}}
 payload["all_checks_pass"]=all(payload["checks"].values());OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":payload["checks"],"all_checks_pass":payload["all_checks_pass"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("route regression replication gates failed")
if __name__=="__main__":main()
