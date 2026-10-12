#!/usr/bin/env python3
"""Measure Stage A eligibility/fallback and overhead on the authored CAN envelope."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CAN_STAGE_A_FALLBACK_ENVELOPE_PREREG_20260926.md"
WORKLOAD=ROOT/"scripts/substrate_can_structure_envelope.py"
SEED=ROOT/"seeds/can_native_reimplementation.json"
SOURCES={k:ROOT/"runners/dsl/src"/v for k,v in {"stage_a":"stage_a.rs","substrate":"substrate.rs","rewrite":"rewrite.rs","graph":"graph.rs"}.items()}
LOCK=ROOT/"evaluation/substrate_capability/can_stage_a_fallback_envelope_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_can_stage_a_fallback_envelope_v1_20260926.json"
SIZES=(16,32);TOPOLOGIES=("path","banded2","complete");MODES=("3state",);GRANULARITY=.25;BETA=2.0;BUDGET=100000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"workload_sha256":sha(WORKLOAD),"seed_manifest_sha256":sha(SEED),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def build_arm(w,seed,n,topology,mode,replicate,arm_name):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 from substrate_rs import _native
 start=lock_inputs()
 enabled=arm_name=="stage_a_enabled";comparison=arm_name=="compare_only"
 _native.stage_a_enable(enabled);_native.stage_a_reset();_native.stage_a_compare_enable(comparison);_native.stage_a_compare_reset()
 draw_seed=20260924+n*1000+replicate
 fr=random.Random(draw_seed*53+n);pr=random.Random(draw_seed*31+n)
 fields=[fr.uniform(-1.0,1.0) for _ in range(n)];weights={}
 for a,b in w.make_pairs(n,topology):
  value=round(pr.uniform(-1.0,1.0)/GRANULARITY)*GRANULARITY;weights[a,b]=value;weights[b,a]=value
 seed_doc=json.loads(SEED.read_text())
 inner,concepts=w.build_engine(sr,engine_rules_only,seed_doc,n,mode,fields,weights)
 t0,c0=time.perf_counter_ns(),time.process_time_ns();progress=inner.run_rules(BUDGET);wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0
 states=[float(inner.node(c)["attrs"].get("state",0.0)) for c in concepts]
 terminal=inner.run_rules(1)
 residuals=[]
 for a,state in enumerate(states):
  field=fields[a]+sum(weights.get((a,b),0.0)*states[b] for b in range(n));residuals.append(w.update(mode,field)!=state)
 graph=inner.graph_to_dict()
 return {"arm":arm_name,"seed":draw_seed,"graph":graph,"progress":progress,"terminal_probe":terminal,"final_state":[int(s) for s in states],"independent_fixed_point_residuals":sum(residuals),"budget_complete":progress<BUDGET,"wall_time_ns":wall,"cpu_time_ns":cpu,"stage_a_stats":_native.stage_a_stats(),"stage_a_compare_stats":_native.stage_a_compare_stats(),"inputs_start":start,"inputs_end":lock_inputs()}
def worker(rep):
 import substrate_can_structure_envelope as w
 initial=lock_inputs();cells=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   control=build_arm(w,initial,n,topology,"3state",rep,"ordinary")
   diagnostic=build_arm(w,initial,n,topology,"3state",rep,"compare_only")
   candidate=build_arm(w,initial,n,topology,"3state",rep,"stage_a_enabled")
   eligible=diagnostic["stage_a_compare_stats"]["compared_drains"];excluded=candidate["stage_a_stats"]["excluded_drains"]
   cells.append({"n":n,"topology":topology,"replicate":rep,"ordinary":control,"compare_only":diagnostic,"stage_a_enabled":candidate,"exact_graph_parity":control["graph"]==candidate["graph"],"progress_parity":control["progress"]==candidate["progress"] and control["terminal_probe"]==candidate["terminal_probe"],"eligible_drain_count":eligible,"excluded_drain_count":excluded,"eligibility_share_matched_runs":eligible/(eligible+excluded) if eligible+excluded else None,"fallback_rate_per_derivable_drain":(candidate["stage_a_stats"]["conflict_fallbacks"]/eligible if eligible else None)})
 return {"replicate":rep,"pid":os.getpid(),"started_inputs":initial,"finished_inputs":lock_inputs(),"cells":cells}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 schedule=[0,1,2];random.Random(20260926).shuffle(schedule);runs=[]
 for rep in schedule:
  proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(proc.stdout))
 post=lock_inputs();cells=[c for r in runs for c in r["cells"]]
 checks={"three_fresh_processes":len({r["pid"] for r in runs})==3,"sources_stable":post==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs) and all(a["inputs_start"]==locked==a["inputs_end"] for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"all_six_cells_present":len(cells)==18 and all(sum(c["n"]==n and c["topology"]==t for c in cells)==3 for n in SIZES for t in TOPOLOGIES),"all_arms_complete_fixed_points":all(a["budget_complete"] and a["terminal_probe"]==0 and a["independent_fixed_point_residuals"]==0 for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"stage_a_matches_ordinary":all(c["exact_graph_parity"] and c["progress_parity"] for c in cells),"counts_nonnegative":all(c["eligible_drain_count"]>=0 and c["excluded_drain_count"]>=0 and c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"]>=0 for c in cells),"fallback_rate_valid_or_explicitly_undefined":all((c["fallback_rate_per_derivable_drain"] is None and c["eligible_drain_count"]==0 and c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"]==0) or (c["fallback_rate_per_derivable_drain"] is not None and 0<=c["fallback_rate_per_derivable_drain"]<=1) for c in cells),"compare_only_has_no_semantic_divergence":all(c["compare_only"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["compare_only"]["stage_a_compare_stats"]["unsound_drains"]==0 for c in cells)}
 payload={"schema_version":1,"run_id":"substrate-can-stage-a-fallback-envelope-v1-20260926","claim_boundary":"Authored CAN 3-state update rules on path/banded2/complete topologies at N=16/32; aggregate matched-run fallback rates and descriptive time, not natural workload prevalence or causal speedup.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"configuration":{"sizes":SIZES,"topologies":TOPOLOGIES,"mode":"3state","weight_granularity":GRANULARITY,"replicates":3,"arms":["ordinary","compare_only","stage_a_enabled"],"budget":BUDGET},"schedule":schedule,"worker_processes":[{"replicate":r["replicate"],"pid":r["pid"],"started_inputs":r["started_inputs"],"finished_inputs":r["finished_inputs"]} for r in runs],"checks":checks,"cells":cells}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("capture validity or semantic gate failed")
if __name__=="__main__":main()
