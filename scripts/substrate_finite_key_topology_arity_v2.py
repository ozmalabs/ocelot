#!/usr/bin/env python3
"""Measure finite-key closure across topology and positive match arity."""
from __future__ import annotations
import hashlib,json,random,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/"scripts"),str(ROOT/"runners/dsl/python")]
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
from analyze_mint_termination_fragment import analyze
from substrate_rs import _native
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_PROTOCOL_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/mint_termination_topology_arity_v2_lock_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_topology_arity_v2_20260926.json"
RUN_ID="mint-termination-topology-arity-v2-20260926"
FILES=("scripts/substrate_finite_key_topology_arity_v2.py","scripts/analyze_substrate_finite_key_topology_arity_v2.py","scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py","docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_PROTOCOL_20260926.md","runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/python/substrate_rs/_native.build.json")
SIZES={"path":(16,32,64,128,256),"cycle":(16,32,64,128,256),"out_star":(16,32,64,128,256),"complete":(8,12,16,20)}
ARITIES=(1,2,3);REPEATS=3;SCHEDULE_SEED=20260926

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():return {"sha256":{p:sha(ROOT/p) for p in FILES},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def edges_for(top,n):
 if top=="path":return [(i,i+1) for i in range(n-1)]
 if top=="cycle":return [(i,(i+1)%n) for i in range(n)]
 if top=="out_star":return [(0,j) for j in range(1,n)]
 if top=="complete":return [(i,j) for i in range(n) for j in range(n) if i!=j]
 raise ValueError(top)
def rules_for(arity):
 names=[f"v{i}" for i in range(arity+1)]
 return [{"name":f"finite_key_path_{arity}","match":[[names[i],"link",names[i+1]] for i in range(arity)],"effects":[["add_node_if_absent","witness","Witness",{"tag":"shared"}],["add_edge",names[-1],"derived","witness",{}]]}]
def projection(graph):
 labels={n["id"]:(n["type"],json.dumps(n["attrs"],sort_keys=True,separators=(",",":"))) for n in graph["nodes"]}
 nodes=sorted(labels.values())
 edges=sorted((labels[e["src"]],e["type"],labels[e["tgt"]],json.dumps(e["attrs"],sort_keys=True,separators=(",",":"))) for e in graph["edges"])
 return {"nodes":[list(x) for x in nodes],"edges":[[list(e[0]),e[1],list(e[2]),e[3]] for e in edges]}
def one_run(top,n,arity,audit):
 edges=edges_for(top,n);rules=rules_for(arity)
 spec_edges=[[f"n{i}","link",f"n{j}",{}] for i,j in edges]
 checker=analyze(rules,[f"n{i}" for i in range(n)],spec_edges)
 if not checker["accepted"]:raise RuntimeError(f"checker refusal: {checker['reasons']}")
 sub=_native.Substrate();t=time.perf_counter_ns();nodes=[sub.add_node("Seed",{"idx":i}) for i in range(n)]
 for i,j in edges:sub.add_edge_unchecked(nodes[i],"link",nodes[j])
 sub.add_rule(rules[0]);setup=time.perf_counter_ns()-t
 if audit:
  sub.scale_audit_set_per_rule_enabled(False);sub.scale_audit_set_enabled(False);sub.scale_audit_reset();sub.scale_audit_per_rule_reset()
  sub.scale_audit_set_enabled(True);sub.scale_audit_set_per_rule_enabled(True)
 t=time.perf_counter_ns();cpu0=time.process_time_ns();report=sub.run_rules_report(checker["progress_steps_upper_bound"]+4,False);cpu=time.process_time_ns()-cpu0;wall=time.perf_counter_ns()-t
 if audit:
  per_rule=sub.scale_audit_per_rule_snapshot();aggregate=dict(sub.scale_audit_snapshot())
  sub.scale_audit_set_per_rule_enabled(False);sub.scale_audit_set_enabled(False)
  per_rule=[{"rule_index":i,"metric":k,"count":v} for i,k,v in per_rule]
 else:per_rule=[];aggregate={}
 graph=sub.graph_to_dict();proj=projection(graph)
 return {"status":report["status"],"progress_steps":report["progress_steps"],"passes_completed":report["passes_completed"],"budget_overshoot":report["budget_overshoot"],"bound":checker["progress_steps_upper_bound"],"setup_ns":setup,"closure_wall_ns":wall,"closure_cpu_ns":cpu,"audit":audit,"audit_aggregate":aggregate,"per_rule_counters":per_rule,"node_count":len(graph["nodes"]),"edge_count":len(graph["edges"]),"projection":proj}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return 0
 started=datetime.now(timezone.utc).isoformat();log=start_console_capture(RUN_ID);locked=lock_inputs()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale topology/arity lock")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit(f"native build stale: {stale}")
 design=[(top,n,a,r) for top,sizes in SIZES.items() for n in sizes for a in ARITIES for r in range(1,REPEATS+1)]
 rng=random.Random(SCHEDULE_SEED);schedule=design[:];rng.shuffle(schedule);cells=[];print("topology/arity cells:",len(schedule),"paired runs:",2*len(schedule),flush=True)
 for top,n,arity,rep in schedule:
  arm_order=["plain","audit"];rng.shuffle(arm_order);runs={}
  for arm in arm_order:runs[arm]=one_run(top,n,arity,arm=="audit")
  # Independent oracle uses injective variable assignments on initial link facts; derived edges are output-only.
  e=edges_for(top,n);paths=[]
  def walk(path):
   if len(path)==arity+1:paths.append(tuple(path));return
   for x,y in e:
    if x==path[-1] and y not in path:walk(path+[y])
  for x in range(n):walk([x])
  targets=sorted({p[-1] for p in paths});wit=bool(paths)
  expected_nodes=[["Seed",json.dumps({"idx":i},sort_keys=True,separators=(",",":"))] for i in range(n)]
  if wit:expected_nodes.append(["Witness",json.dumps({"tag":"shared"},sort_keys=True,separators=(",",":"))])
  labels={i:("Seed",json.dumps({"idx":i},sort_keys=True,separators=(",",":"))) for i in range(n)}
  if wit:labels[n]=("Witness",json.dumps({"tag":"shared"},sort_keys=True,separators=(",",":")))
  expected_edges=sorted([[list(labels[i]),"link",list(labels[j]),"{}"] for i,j in e]+[[list(labels[t]),"derived",list(labels[n]),"{}"] for t in targets])
  expected={"nodes":sorted(expected_nodes),"edges":expected_edges}
  checks={}
  for arm,result in runs.items():
   checks[arm]={"fixed_point":result["status"]=="fixed_point","no_budget_overshoot":result["budget_overshoot"]==0,"within_bound":result["progress_steps"]<=result["bound"],"exact_oracle_graph":result["projection"]==expected}
  cells.append({"topology":top,"n":n,"arity":arity,"replicate":rep,"arm_order":arm_order,"expected_match_count":len(paths),"expected_target_count":len(targets),"expected_graph":expected,"plain":runs["plain"],"audit":runs["audit"],"checks":checks,"passed":all(all(x.values()) for x in checks.values())})
 post=lock_inputs();logref=finish_console_capture(log);ok=all(x["passed"] for x in cells) and post==locked
 manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/substrate_finite_key_topology_arity_v2.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=("scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py","runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs"),analysis_files=("scripts/analyze_substrate_finite_key_topology_arity_v2.py",),started_utc=started,exit_status=0 if ok else 1,stdout_stderr_capture=logref)
 result={"schema_version":1,"run_id":RUN_ID,"locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"design":{"sizes":SIZES,"arities":ARITIES,"repeats":REPEATS,"schedule_seed":SCHEDULE_SEED,"cells":len(cells),"arm_order_randomized":True},"cells":cells,"passed_cells":sum(c["passed"] for c in cells),"all_checks_pass":ok,"run_manifest":manifest}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"cells":len(cells),"passed_cells":result["passed_cells"],"all_checks_pass":ok},sort_keys=True));return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())
