#!/usr/bin/env python3
"""Paired fresh-boot intervention for seed-provider closure selection."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_PREREG_20260927.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_1_AMENDMENT_20260927.md"
OLD=ROOT/"evaluation/substrate_capability/fixtures/boot_all_before_provider_scope_20260927.py"
SCOPE_ONLY=ROOT/"evaluation/substrate_capability/fixtures/boot_all_provider_scope_only_20260927.py"
OUT=ROOT/"evaluation/reports/seed_provider_scope_self_report_intervention_v1_20260927.json"
PROMPT="report your organisation"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock():
 import substrate_live_self_report_dimension_frame_v1 as frame
 return {"source_lock":frame.lock_inputs(),"old_boot_all_sha256":sha(OLD),"provider_scope_only_sha256":sha(SCOPE_ONLY),"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(__file__)}
def worker(condition,rep):
 import substrate_live_self_report_dimension_frame_v1 as frame
 started=frame.lock_inputs();old_sha=sha(OLD)
 module_path=OLD if condition=="old" else SCOPE_ONLY
 spec=importlib.util.spec_from_file_location("substrate.boot_all",module_path)
 module=importlib.util.module_from_spec(spec);sys.modules["substrate.boot_all"]=module;spec.loader.exec_module(module)
 from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();boot=module.load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 import domains.comprehend_text as comprehend
 captured=[];original=comprehend.comprehend_text
 def observe(*args,**kwargs):
  c=original(*args,**kwargs);captured.append(c);return c
 comprehend.comprehend_text=observe
 try:reply=str(a.converse(PROMPT,speech_act="instruction",speaker="alice"))
 finally:comprehend.comprehend_text=original
 c=captured[-1] if captured else None;m=a._last_turn_inbound;attrs=dict(a.s.node(m)["attrs"])
 goals=[g for g in a.s.nodes("Goal") if m in a.inner.neighbours(g,"comprehends")]
 graph=a.s.graph_to_dict();finished=frame.lock_inputs()
 return {"condition":condition,"replicate":rep,"pid":os.getpid(),"old_boot_all_sha256":old_sha,"provider_scope_only_sha256":sha(SCOPE_ONLY),
  "loaded_seed_ids":sorted(boot.get("loaded_seed_ids",[])),"failed_seeds":boot.get("failed",[]),"boot_ns":boot_ns,
  "comprehension":{"kind":getattr(c,"kind",None),"intent":getattr(c,"intent",None),"dispatch":getattr(c,"dispatch",None)},
  "route":attrs.get("communication_route"),"instruction_outcome":attrs.get("instruction_outcome"),"reply":reply,
  "goal_count":len(goals),"goal_statuses":sorted(str(a.s.node(g)["attrs"].get("lifecycle_status")) for g in goals),
  "graph_nodes":len(graph.get("nodes",[])),"graph_edges":len(graph.get("edges",[])),"semantic_graph_sha256":frame.semantic_digest(graph),
  "worker_start_lock":started,"worker_end_lock":finished}
def main():
 import substrate_live_self_report_dimension_frame_v1 as frame
 if sys.argv[1:2]==["--worker"]:
  _,_,cond,rep=sys.argv;print(json.dumps(worker(cond,int(rep)),sort_keys=True,default=str));return
 driver=lock()
 if sys.argv[1:]==["--lock"]:print(json.dumps(driver,indent=2,sort_keys=True));return
 jobs=[(condition,rep) for rep in range(3) for condition in ("old","provider_scope_only")];random.Random(20260927).shuffle(jobs);rows=[]
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 for condition,rep in jobs:
  p=subprocess.run([sys.executable,"-u",str(Path(__file__).resolve()),"--worker",condition,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout));print(f"completed condition={condition} replicate={rep}",flush=True)
 post=lock();payload={"schema_version":1,"run_id":"seed-provider-scope-self-report-intervention-v1-20260927","driver_lock":driver,"post_run_lock":post,"schedule":[list(j) for j in jobs],"runs":rows,"environment":{"python":sys.version,"platform":platform.platform()}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"workers":len(rows),"source_stable":post==driver and all(r["worker_start_lock"]==driver["source_lock"]==r["worker_end_lock"] for r in rows)},indent=2))
if __name__=="__main__":main()
