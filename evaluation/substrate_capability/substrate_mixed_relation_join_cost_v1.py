#!/usr/bin/env python3
"""Measure typed mixed-relation matcher prefixes and install-order regret."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
BASE_PATH=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1.py"
spec=importlib.util.spec_from_file_location("productive_base",BASE_PATH);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
SEED=ROOT/"seeds/can_native_reimplementation.json";PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_MIXED_RELATION_JOIN_COST_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_substrate_mixed_relation_join_cost_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/substrate_mixed_relation_join_cost_v1_workers_20261001.json"
PATTERNS=("path4","star4","cycle4");SPARSE_POSITIONS=(0,1,2,3,"balanced");SIZES=(16,32);REPS=3;MAX_STEPS=1000;RELATIONS=tuple(f"mix_r{i}" for i in range(4))
SOURCES=("runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/persist.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(BASE_PATH.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in paths},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def pattern(name):
 if name=="path4":return [[f"x{i}",RELATIONS[i],f"x{i+1}"] for i in range(4)]
 if name=="star4":return [["x0",RELATIONS[i],f"x{i+1}"] for i in range(4)]
 if name=="cycle4":return [[f"x{i}",RELATIONS[i],f"x{(i+1)%4}"] for i in range(4)]
 raise ValueError(name)
def counts(n,sparse_pos):return [n if sparse_pos==i else 4*n for i in range(4)] if sparse_pos!="balanced" else [4*n]*4
def relation_pairs(n,count):return [(i,(i+offset)%n) for offset in range(1,count//n+1) for i in range(n)]
def arm(n,shape,sparse_pos):
 seed=json.loads(SEED.read_text());v=copy.deepcopy(seed);v["rules"]=[];inner=sr.Substrate()._inner;inner.load_seed_manifest(engine_rules_only(v))
 concepts=[inner.add_node("Concept",{"name":f"c{i}"}) for i in range(n)];g=inner.graph_to_dict();population=counts(n,sparse_pos)
 edge_rows=[]
 for k,(rel,count) in enumerate(zip(RELATIONS,population)):
  for a,b in relation_pairs(n,count):edge_rows.append({"src":int(concepts[a].value),"type":rel,"tgt":int(concepts[b].value),"attrs":{}})
 g["edges"]=edge_rows;inner.graph_from_dict(g)
 rule=copy.deepcopy(next(r for r in seed["rules"] if r.get("name")=="can_native_hebbian_mint"));rule.update({"name":"mixed_relation_join_probe","match":pattern(shape),"where":None,"effects":[],"match_type":"Concept"});inner.import_rules([rule])
 exported=inner.export_rules();exported=json.loads(exported) if isinstance(exported,str) else exported;installed=next(r for r in exported if r["name"]=="mixed_relation_join_probe")["match"];active=[r["name"] for r in exported if r.get("active")]
 before,_,_,_=BASE.graph_facts(inner);inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 t=time.perf_counter_ns();progress=int(inner.run_rules(MAX_STEPS));wall=time.perf_counter_ns()-t
 global_counts={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()};per=[list(x) for x in inner.scale_audit_per_rule_snapshot()];clause=[list(x) for x in inner.scale_audit_match_clause_snapshot()];meta=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);terminal=int(inner.run_rules(1));after,nodes,edges,_=BASE.graph_facts(inner)
 return {"n":n,"pattern":shape,"sparse_position":sparse_pos,"relation_populations":dict(zip(RELATIONS,population)),"installed_match":installed,"active_rules":active,"progress":progress,"terminal_progress":terminal,"before_digest":before,"after_digest":after,"nodes":nodes,"edges":edges,"global":global_counts,"per_rule":per,"clause_candidates":clause,"rule_metadata":meta,"wall_ns":wall}
def worker(n,shape,sparse_pos,rep):
 start=fingerprint();result=arm(n,shape,sparse_pos);end=fingerprint()
 return {"n":n,"pattern":shape,"sparse_position":sparse_pos,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"result":result}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":
  sp=sys.argv[4];sp="balanced" if sp=="balanced" else int(sp);print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sp,int(sys.argv[5])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for shape in PATTERNS:
  for n in SIZES:
   for sparse in SPARSE_POSITIONS:
    for rep in range(REPS):
     p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),shape,str(sparse),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600);row=json.loads(p.stdout);runs.append(row)
     print(f"pattern={shape} N={n} sparse={sparse} order={[x[1] for x in row['result']['installed_match']]} tests={row['result']['global'].get('cand_tested')}",flush=True)
 post=fingerprint();RAW.write_text(json.dumps({"locked_inputs":lock,"post_run_inputs":post,"runs":runs},indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
