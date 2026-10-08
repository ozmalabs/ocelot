#!/usr/bin/env python3
"""Controlled coactivation-population and Hebbian match-order work panel."""
from __future__ import annotations
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
from domains.can_native_orchestration import scoped_settle
from domains.engine_provenance import build_is_stale,rust_source_fingerprint
SEED=ROOT/"seeds/can_native_reimplementation.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_COACTIVATION_POPULATION_JOIN_ORDER_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_can_coactivation_population_join_order_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/can_coactivation_population_join_order_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/can_coactivation_population_join_order_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/can_coactivation_population_join_order_v1_20261001.json"
TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
SIZES=(32,64,128);REPS=3
SOURCES=("domains/can_native_orchestration.py","substrate/seed_loader.py","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{x:sha(ROOT/x) for x in paths},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(Path(_native.__file__).resolve()),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT)),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def digest(inner):return hashlib.sha256(json.dumps(inner.graph_to_dict(),sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def population_sizes(n):return (0,n,4*n,n*(n-1)//4,n*(n-1))
def match_order_variant(seed_doc,sparse_first):
 doc=copy.deepcopy(seed_doc)
 for rule in doc["rules"]:
  if rule.get("name") in TARGETS:
   m=rule["match"]
   if len(m)!=4:raise RuntimeError(f"unexpected match width for {rule.get('name')}")
   if sparse_first:rule["match"]=[m[2],m[3],m[0],m[1]]
 return doc
def pair_population(n,q):
 return [(i,(i+offset)%n) for offset in range(1,n) for i in range(n)][:q]
def build(n,q,seed_doc):
 inner=sr.Substrate()._inner;manifest=engine_rules_only(seed_doc);inner.load_seed_manifest(manifest)
 exports=inner.export_rules();exports=json.loads(exports) if isinstance(exports,str) else exports
 for idx,row in enumerate(exports):
  if row["name"] not in TARGETS:inner.remove_rule(idx)
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":0})
 concepts=[]
 for i in range(n):
  c=inner.add_node("Concept",{"name":f"c{i}","state":1.0,"external_field":0.0,"identity_field":0.0});concepts.append(c);inner.add_edge(mt,"has_concept",c,{})
 pairs=pair_population(n,q)
 for j,(a,b) in enumerate(pairs):
  co=inner.add_node("Coactivation",{"noted_tick":1,"evidence_confirm":0,"evidence_disconfirm":0,"evidence_tick":1,"pair_index":j})
  inner.add_edge(concepts[a],"coactivated_with",co,{})
  inner.add_edge(co,"coactivation_of",concepts[b],{})
 # Capture actually installed match order after graph construction.
 rules=inner.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
 installed={r["name"]:[e[1] for e in r["match"]] for r in rules if r["name"] in TARGETS}
 active=[r["name"] for r in rules if r.get("active")]
 return inner,mt,concepts,installed,active
def measured(inner,mt,initial_digest):
 from substrate_rs import _native
 audit=_native.Substrate;audit.scale_audit_set_enabled(False);audit.scale_audit_reset();audit.scale_audit_set_per_rule_enabled(True);audit.scale_audit_per_rule_reset();audit.scale_audit_set_enabled(True)
 try:
  progress=scoped_settle(inner,mt,100000)
  global_counts={str(k):int(v) for k,v in dict(audit.scale_audit_snapshot()).items()}
  per_rule=[list(x) for x in audit.scale_audit_per_rule_snapshot()]
  metadata=[list(x) for x in audit.scale_audit_rule_metadata_snapshot()]
 finally:
  audit.scale_audit_set_enabled(False);audit.scale_audit_set_per_rule_enabled(False)
 terminal=scoped_settle(inner,mt,1)
 return {"progress":int(progress),"terminal_progress":int(terminal),"before_digest":initial_digest,"after_digest":digest(inner),"global":global_counts,"per_rule":per_rule,"rule_metadata":metadata}
def run_order(n,q,seed_doc,sparse_first):
 selected=match_order_variant(seed_doc,sparse_first);inner,mt,concepts,installed,active=build(n,q,selected);before=digest(inner)
 row=measured(inner,mt,before)
 names={int(x[0]):str(x[2]) for x in row["rule_metadata"]}
 by_rule={name:{"candidate_tests":0,"candidate_pairs":0,"term_evaluations":0} for name in TARGETS}
 for index,metric,count in row["per_rule"]:
  name=names.get(int(index))
  if name in by_rule and metric in by_rule[name]:by_rule[name][metric]+=int(count)
 row.update({"installed_match_order":installed,"active_rules":active,"target_work":by_rule,"expected_coactivation_count":q,"sparse_first":sparse_first})
 return row
def worker(n,q,rep):
 before=fingerprint();seed_doc=json.loads(SEED.read_text());base=run_order(n,q,seed_doc,False);sparse=run_order(n,q,seed_doc,True);after=fingerprint()
 return {"n":n,"q":q,"replicate":rep,"pid":os.getpid(),"before":before,"after":after,"base":base,"sparse_first":sparse}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])),sort_keys=True));return
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for n in SIZES:
  for q in population_sizes(n):
   for rep in range(REPS):
    proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),str(q),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    row=json.loads(proc.stdout);runs.append(row);print(f"N={n} Q={q} rep={rep} base={row['base']['global'].get('cand_tested')} sparse={row['sparse_first']['global'].get('cand_tested')}",flush=True)
 post=fingerprint();raw={"protocol":"CAN_COACTIVATION_POPULATION_JOIN_ORDER_V1","locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"worker_count":len(runs),"all_worker_inputs_stable":locked==post,"raw_workers_path":str(RAW.relative_to(ROOT))};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
