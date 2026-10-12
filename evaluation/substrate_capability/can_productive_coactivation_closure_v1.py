#!/usr/bin/env python3
"""Source-locked productive CAN Hebbian closure over varying coactivation Q."""
from __future__ import annotations
import copy, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
SEED=ROOT/"seeds/can_native_reimplementation.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_PRODUCTIVE_COACTIVATION_CLOSURE_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/"scripts/analyze_can_productive_coactivation_closure_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_20261001.json"
TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
SIZES=(32,64,128);REPS=3;MAX_STEPS=100000
SOURCES=("substrate/seed_loader.py","domains/can_native_orchestration.py","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 names=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in names},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def populations(n):return (0,n,4*n,n*(n-1)//4,n*(n-1))
def variant(seed_doc,sparse):
 doc=copy.deepcopy(seed_doc)
 for rule in doc["rules"]:
  if rule.get("name") in TARGETS and sparse:
   m=rule["match"]
   if len(m)!=4:raise RuntimeError(f"unexpected match width: {rule.get('name')}")
   rule["match"]=[m[2],m[3],m[0],m[1]]
 return doc
def pairs(n,q):return [(i,(i+offset)%n) for offset in range(1,n) for i in range(n)][:q]
def build(n,q,seed_doc):
 inner=sr.Substrate()._inner;inner.load_seed_manifest(engine_rules_only(seed_doc))
 rules=inner.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
 for idx,row in enumerate(rules):
  if row["name"] not in TARGETS:inner.remove_rule(idx)
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":1})
 concepts=[]
 for i in range(n):
  c=inner.add_node("Concept",{"name":f"c{i}","state":1.0,"external_field":0.0,"identity_field":0.0});concepts.append(c);inner.add_edge(mt,"has_concept",c,{})
 assigned=pairs(n,q);existing=set()
 for j,(a,b) in enumerate(assigned):
  co=inner.add_node("Coactivation",{"noted_tick":0,"evidence_confirm":0,"evidence_disconfirm":0,"evidence_tick":0,"pair_index":j})
  inner.add_edge(concepts[a],"coactivated_with",co,{})
  inner.add_edge(co,"coactivation_of",concepts[b],{})
  if j%2==1:
   inner.add_edge(concepts[a],"causal_influence",concepts[b],{"weight":0.5});existing.add(j)
 exported=inner.export_rules();exported=json.loads(exported) if isinstance(exported,str) else exported
 installed={x["name"]:[e[1] for e in x["match"]] for x in exported if x["name"] in TARGETS}
 active=[x["name"] for x in exported if x.get("active")]
 return inner,mt,assigned,existing,installed,active
def graph_facts(inner):
 g=inner.graph_to_dict();nodes={x["id"]:x for x in g["nodes"]};tokens={}
 for i,node in nodes.items():
  typ=node["type"];attrs=node["attrs"]
  if typ=="Concept":token=f"Concept:{attrs.get('name')}"
  elif typ=="Microtheory":token="Microtheory:fixture"
  elif typ=="Coactivation":token=f"Coactivation:{attrs.get('pair_index')}"
  else:token=f"{typ}:{json.dumps(attrs,sort_keys=True,default=str)}"
  tokens[i]=token
 ns=sorted(((tokens[i],node["type"],node["attrs"]) for i,node in nodes.items()),key=lambda x:json.dumps(x,sort_keys=True,default=str))
 es=sorted(((tokens[e["src"]],e["type"],tokens[e["tgt"]],e.get("attrs",{})) for e in g["edges"]),key=lambda x:json.dumps(x,sort_keys=True,default=str))
 raw=json.dumps({"nodes":ns,"edges":es},sort_keys=True,separators=(",",":"),default=str)
 return hashlib.sha256(raw.encode()).hexdigest(),len(ns),len(es),g
def run_arm(n,q,seed_doc,sparse,audit=True):
 inner,mt,assigned,existing,installed,active=build(n,q,variant(seed_doc,sparse))
 before=graph_facts(inner)[0]
 if audit:
  inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 started=time.perf_counter_ns();progress=int(inner.run_rules(MAX_STEPS));wall_ns=time.perf_counter_ns()-started
 if audit:
  global_counts={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()}
  per_rule=[list(x) for x in inner.scale_audit_per_rule_snapshot()]
  metadata=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
  inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False)
 else:global_counts={};per_rule=[];metadata=[]
 terminal=int(inner.run_rules(1));after,nodes,edges,g=graph_facts(inner)
 coacts={int(x["attrs"].get("pair_index")):x["id"] for x in g["nodes"] if x["type"]=="Coactivation"}
 edge_tuples={(e["src"],e["type"],e["tgt"]) for e in g["edges"]}
 activated=[]
 for j,(a,b) in enumerate(assigned):
  aid=concept_id(g,f"c{a}");bid=concept_id(g,f"c{b}")
  activated.append({"pair_index":j,"causal_present":(aid,"causal_influence",bid) in edge_tuples,"evidence_tick":node_by_id(g,coacts[j])["attrs"].get("evidence_tick"),"confirm":node_by_id(g,coacts[j])["attrs"].get("evidence_confirm"),"disconfirm":node_by_id(g,coacts[j])["attrs"].get("evidence_disconfirm")})
 return {"sparse":sparse,"installed_match_order":installed,"active_rules":active,"progress":progress,"wall_ns":wall_ns,"terminal_progress":terminal,"before_digest":before,"after_digest":after,"nodes":nodes,"edges":edges,"global":global_counts,"per_rule":per_rule,"rule_metadata":metadata,"pair_results":activated,"initial_reweight_pairs":len(existing),"expected_pairs":q}
def node_by_id(g,nid):return next(x for x in g["nodes"] if x["id"]==nid)
def concept_id(g,name):return next(x["id"] for x in g["nodes"] if x["type"]=="Concept" and x["attrs"].get("name")==name)
def worker(n,q,rep):
 start=fingerprint();seed=json.loads(SEED.read_text());base=run_arm(n,q,seed,False,True);sparse=run_arm(n,q,seed,True,True)
 base_plain=run_arm(n,q,seed,False,False);sparse_plain=run_arm(n,q,seed,True,False);end=fingerprint()
 return {"n":n,"q":q,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"base":base,"sparse":sparse,"base_plain":base_plain,"sparse_plain":sparse_plain}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for n in SIZES:
  for q in populations(n):
   for rep in range(REPS):
    p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),str(q),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600)
    row=json.loads(p.stdout);runs.append(row);print(f"N={n} Q={q} rep={rep} progress={row['base']['progress']}/{row['sparse']['progress']} tests={row['base']['global'].get('cand_tested')}/{row['sparse']['global'].get('cand_tested')}",flush=True)
 post=fingerprint();raw={"locked_inputs":lock,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
