#!/usr/bin/env python3
"""Measure Stage A applicability and fallback on authored event-reasoning rules."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_V1_1_AMENDMENT_20260926.md"
BASE_PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_PREREG_20260926.md"
SEED=ROOT/"seeds/event_reasoning.json";LOADER=ROOT/"substrate/seed_loader.py"
SOURCES={k:ROOT/"runners/dsl/src"/v for k,v in {"stage_a":"stage_a.rs","substrate":"substrate.rs","rewrite":"rewrite.rs","graph":"graph.rs"}.items()}
LOCK=ROOT/"evaluation/substrate_capability/event_reasoning_stage_a_envelope_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_1_20260926.json"
SIZES=(1,4,16,64,256);BUDGET=1000
ARM_ORDERS=(("ordinary","compare_only","stage_a_enabled"),("ordinary","stage_a_enabled","compare_only"),("compare_only","ordinary","stage_a_enabled"),("compare_only","stage_a_enabled","ordinary"),("stage_a_enabled","ordinary","compare_only"),("stage_a_enabled","compare_only","ordinary"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"seed_sha256":sha(SEED),"loader_sha256":sha(LOADER),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def arm(n,kind):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 from substrate_rs import _native
 locked=lock_inputs();_native.stage_a_enable(kind=="stage_a_enabled");_native.stage_a_reset();_native.stage_a_compare_enable(kind=="compare_only");_native.stage_a_compare_reset()
 sub=sr.Substrate();inner=sub._inner;manifest=engine_rules_only(json.loads(SEED.read_text()));loaded=inner.load_seed_manifest(manifest)
 entities=[]
 for i in range(n):
  node=inner.add_node("Entity",{"fell":1,"fragile":1,"ordinal":i});entities.append(node);inner.add_edge_unchecked(node,"is_entity",node,{})
 t0,c0=time.perf_counter_ns(),time.process_time_ns();progress=inner.run_rules(BUDGET);wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0
 terminal=inner.run_rules(1);graph=inner.graph_to_dict();nodes={x["id"]:x for x in graph["nodes"]}
 oracle=all(all(nodes[e.value]["attrs"].get(k)==1 for k in ("on_floor","on_floor_inferred","broken","broken_inferred","worthless","worthless_inferred")) for e in entities)
 return {"kind":kind,"loaded_rule_count":loaded["rules"],"graph":graph,"progress":progress,"terminal_probe":terminal,"node_count":len(graph["nodes"]),"edge_count":len(graph["edges"]),"wall_time_ns":wall,"cpu_time_ns":cpu,"oracle_gate":oracle,"stage_a_stats":_native.stage_a_stats(),"stage_a_compare_stats":_native.stage_a_compare_stats(),"inputs_start":locked,"inputs_end":lock_inputs()}
def worker(rep):
 initial=lock_inputs();cells=[]
 for n in SIZES:
  arm_order=ARM_ORDERS[rep]
  results={kind:arm(n,kind) for kind in arm_order}
  ordinary=results["ordinary"];diagnostic=results["compare_only"];candidate=results["stage_a_enabled"]
  eligible=diagnostic["stage_a_compare_stats"]["compared_drains"];excluded=candidate["stage_a_stats"]["excluded_drains"];fallbacks=candidate["stage_a_stats"]["conflict_fallbacks"]
  cells.append({"size":n,"replicate":rep,"arm_order":arm_order,"ordinary":ordinary,"compare_only":diagnostic,"stage_a_enabled":candidate,"eligible_drain_count":eligible,"excluded_drain_count":excluded,"fallback_count":fallbacks,"eligible_drain_share":eligible/(eligible+excluded) if eligible+excluded else None,"fallback_rate":fallbacks/eligible if eligible else None,"exact_graph_parity":ordinary["graph"]==candidate["graph"],"progress_parity":ordinary["progress"]==candidate["progress"] and ordinary["terminal_probe"]==candidate["terminal_probe"]})
 return {"replicate":rep,"pid":os.getpid(),"started_inputs":initial,"finished_inputs":lock_inputs(),"cells":cells}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 started=datetime.now(timezone.utc).isoformat();log_capture=start_console_capture("substrate-event-reasoning-stage-a-envelope-v1-1-20260926")
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 schedule=list(range(len(ARM_ORDERS)));random.Random(20260926).shuffle(schedule);runs=[];worker_streams=[]
 for rep in schedule:
  argv=[sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)]
  proc=subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(proc.stdout))
  worker_streams.append({"replicate":rep,"argv":argv,"relevant_environment":{k:env[k] for k in ("PYTHONPATH","OZMA_NO_LLM","OZMA_SEED_PERSIST_DISABLED") if k in env},"stdout_sha256":hashlib.sha256(proc.stdout.encode()).hexdigest(),"stderr":proc.stderr,"stderr_sha256":hashlib.sha256(proc.stderr.encode()).hexdigest(),"stderr_bytes":len(proc.stderr.encode())})
 post=lock_inputs();cells=[c for r in runs for c in r["cells"]]
 checks={"six_fresh_processes":len({r["pid"] for r in runs})==6,"sources_stable":post==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs) and all(a["inputs_start"]==locked==a["inputs_end"] for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"all_sizes_replicated":all(sum(c["size"]==n for c in cells)==6 for n in SIZES),"all_six_arm_orders_used":{tuple(next(c["arm_order"] for c in cells if c["replicate"]==r)) for r in range(6)}==set(ARM_ORDERS),"all_arms_oracle_and_complete":all(a["oracle_gate"] and a["terminal_probe"]==0 and a["node_count"]==n+5 and a["edge_count"]==n for c in cells for n in (c["size"],) for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"ordinary_and_enabled_exact_parity":all(c["exact_graph_parity"] and c["progress_parity"] for c in cells),"compare_has_admitted_drains":all(c["eligible_drain_count"]>0 and c["compare_only"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["compare_only"]["stage_a_compare_stats"]["unsound_drains"]==0 for c in cells),"no_static_exclusions_or_overlap_fallback":all(c["excluded_drain_count"]==0 and c["fallback_count"]==0 and c["fallback_rate"]==0 for c in cells),"rates_reconcile":all(c["eligible_drain_share"]==1.0 and c["eligible_drain_count"]==c["compare_only"]["stage_a_compare_stats"]["compared_drains"] for c in cells)}
 print("worker stderr byte counts:",[x["stderr_bytes"] for x in worker_streams],flush=True);log_ref=finish_console_capture(log_capture)
 manifest=capture_run_manifest(run_id="substrate-event-reasoning-stage-a-envelope-v1-1-20260926",runner="scripts/substrate_event_reasoning_stage_a_envelope_v1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(BASE_PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=tuple(str(x.relative_to(ROOT)) for x in SOURCES.values())+(str(LOADER.relative_to(ROOT)),),data_files=(str(SEED.relative_to(ROOT)),),analysis_files=("scripts/analyze_substrate_event_reasoning_stage_a_envelope_v1_1.py",),started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=log_ref,child_processes=worker_streams)
 payload={"schema_version":1,"run_id":"substrate-event-reasoning-stage-a-envelope-v1-1-20260926","claim_boundary":"Authored event_reasoning implication rules over independent synthetic entities at sizes 1/4/16/64/256; measures current static admission, runtime fallback, parity and descriptive cost, not workload prevalence or speedup.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"configuration":{"sizes":SIZES,"replicates":6,"arms":["ordinary","compare_only","stage_a_enabled"],"arm_orders":ARM_ORDERS,"budget":BUDGET},"schedule":schedule,"worker_processes":[{"replicate":r["replicate"],"pid":r["pid"],"started_inputs":r["started_inputs"],"finished_inputs":r["finished_inputs"]} for r in runs],"worker_streams":worker_streams,"run_manifest":manifest,"checks":checks,"cells":cells}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("capture validity or semantic gate failed")
if __name__=="__main__":main()
