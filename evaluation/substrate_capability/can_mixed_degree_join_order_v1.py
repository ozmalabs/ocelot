#!/usr/bin/env python3
"""Measure CAN Hebbian matcher order over uniform and source-skewed Q layouts."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
BASE_PATH=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1.py"
spec=importlib.util.spec_from_file_location("productive_base",BASE_PATH);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
SEED=ROOT/"seeds/can_native_reimplementation.json";PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_MIXED_DEGREE_JOIN_ORDER_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_can_mixed_degree_join_order_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/can_mixed_degree_join_order_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/can_mixed_degree_join_order_v1_workers_20261001.json"
SIZES=(16,32);LAYOUTS=("uniform","source_skewed");REPS=3;MAX_STEPS=1000;TARGET="can_native_hebbian_mint"
SOURCES=("runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 names=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(BASE_PATH.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in names},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def qvalues(n):return (n,4*n,n*(n-1)//4)
def pair_rows(n,q,layout):
 if layout=="uniform":return [(i,(i+o)%n) for o in range(1,n) for i in range(n)][:q]
 return [(i,j) for i in range(n) for j in range(n) if i!=j][:q]
def run_arm(n,q,layout):
 seed=json.loads(SEED.read_text());v=copy.deepcopy(seed);v["rules"]=[];inner=sr.Substrate()._inner;inner.load_seed_manifest(engine_rules_only(v))
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":0});concepts=[]
 for i in range(n):
  c=inner.add_node("Concept",{"name":f"c{i}","state":1.0});concepts.append(c);inner.add_edge(mt,"has_concept",c,{})
 for j,(a,b) in enumerate(pair_rows(n,q,layout)):
  co=inner.add_node("Coactivation",{"pair_index":j,"noted_tick":1,"evidence_tick":1});inner.add_edge(concepts[a],"coactivated_with",co,{});inner.add_edge(co,"coactivation_of",concepts[b],{})
 rule=copy.deepcopy(next(r for r in seed["rules"] if r.get("name")==TARGET));rule["where"]=None;rule["effects"]=[];inner.import_rules([rule])
 exports=inner.export_rules();exports=json.loads(exports) if isinstance(exports,str) else exports;installed=next(r for r in exports if r["name"]==TARGET)["match"];active=[r["name"] for r in exports if r.get("active")]
 before,_,_,_=BASE.graph_facts(inner);inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 t=time.perf_counter_ns();progress=int(inner.run_rules(MAX_STEPS));wall=time.perf_counter_ns()-t
 glob={str(k):int(x) for k,x in dict(inner.scale_audit_snapshot()).items()};per=[list(x) for x in inner.scale_audit_per_rule_snapshot()];clauses=[list(x) for x in inner.scale_audit_match_clause_snapshot()]
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);terminal=int(inner.run_rules(1));after,nodes,edges,_=BASE.graph_facts(inner)
 return {"installed_match":installed,"active_rules":active,"progress":progress,"terminal_progress":terminal,"before_digest":before,"after_digest":after,"nodes":nodes,"edges":edges,"global":glob,"per_rule":per,"clause_candidates":clauses,"wall_ns":wall,"relation_populations":{"has_concept":n,"coactivated_with":q,"coactivation_of":q}}
def worker(n,q,layout,rep):
 start=fingerprint();seed=json.loads(SEED.read_text());res=run_arm(n,q,layout);end=fingerprint()
 return {"n":n,"q":q,"layout":layout,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"result":res}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for n in SIZES:
  for q in qvalues(n):
   for layout in LAYOUTS:
    for rep in range(REPS):
     p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),str(q),layout,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600);row=json.loads(p.stdout);runs.append(row)
     a=row["result"];print(f"N={n} Q={q} layout={layout} rep={rep} order={[e[1] for e in a['installed_match']]} tests={a['global'].get('cand_tested')}",flush=True)
 post=fingerprint();RAW.write_text(json.dumps({"locked_inputs":lock,"post_run_inputs":post,"runs":runs},indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
