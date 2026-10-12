#!/usr/bin/env python3
"""Measure CAN rule install-time ordering with populated versus empty graph."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
BASE_PATH=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1.py"
spec=importlib.util.spec_from_file_location("productive_base",BASE_PATH);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
SEED=BASE.SEED;PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_INSTALL_TIME_JOIN_ORDER_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_can_install_time_join_order_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/can_install_time_join_order_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/can_install_time_join_order_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/can_install_time_join_order_v1_analysis_20261001.json"
PRIOR_RAW=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_workers_20261001.json"
PRIOR_ANALYSIS=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_analysis_20261001.json"
PRIOR_LOCK=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1_lock_20261001.json"
TARGETS=BASE.TARGETS;SIZES=BASE.SIZES;REPS=BASE.REPS
SOURCES=("runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(BASE_PATH.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),str(PRIOR_RAW.relative_to(ROOT)),str(PRIOR_ANALYSIS.relative_to(ROOT)),str(PRIOR_LOCK.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in paths},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def qvalues(n):return BASE.populations(n)
def graph_before_rules(n,q,seed_doc,sparse):
 # Register the vocabulary and productions without installing rules.
 inner=sr.Substrate()._inner;vocab=copy.deepcopy(seed_doc);vocab["rules"]=[];inner.load_seed_manifest(engine_rules_only(vocab))
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":1});concepts=[]
 for i in range(n):
  c=inner.add_node("Concept",{"name":f"c{i}","state":1.0,"external_field":0.0,"identity_field":0.0});concepts.append(c);inner.add_edge(mt,"has_concept",c,{})
 assigned=BASE.pairs(n,q);existing=set()
 for j,(a,b) in enumerate(assigned):
  co=inner.add_node("Coactivation",{"noted_tick":0,"evidence_confirm":0,"evidence_disconfirm":0,"evidence_tick":0,"pair_index":j})
  inner.add_edge(concepts[a],"coactivated_with",co,{});inner.add_edge(co,"coactivation_of",concepts[b],{})
  if j%2==1:inner.add_edge(concepts[a],"causal_influence",concepts[b],{"weight":0.5});existing.add(j)
 rules=[copy.deepcopy(r) for r in seed_doc["rules"] if r.get("name") in TARGETS]
 for r in rules:
  if sparse:r["match"]=[r["match"][2],r["match"][3],r["match"][0],r["match"][1]]
 if len(rules)!=2:raise RuntimeError("target rule set incomplete")
 inner.import_rules(rules)
 exported=inner.export_rules();exported=json.loads(exported) if isinstance(exported,str) else exported
 installed={r["name"]:[list(e) for e in r["match"]] for r in exported if r["name"] in TARGETS}
 active=[r["name"] for r in exported if r.get("active")]
 return inner,assigned,existing,installed,active
def arm(n,q,seed_doc,sparse):
 inner,assigned,existing,installed,active=graph_before_rules(n,q,seed_doc,sparse);before,_,_,_=BASE.graph_facts(inner)
 inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 t=time.perf_counter_ns();progress=int(inner.run_rules(BASE.MAX_STEPS));wall=time.perf_counter_ns()-t
 global_counts={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()};per=[list(x) for x in inner.scale_audit_per_rule_snapshot()];meta=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);terminal=int(inner.run_rules(1))
 after,nodes,edges,g=BASE.graph_facts(inner);coacts={int(x["attrs"].get("pair_index")):x["id"] for x in g["nodes"] if x["type"]=="Coactivation"};byid={x["id"]:x for x in g["nodes"]};cid={x["attrs"].get("name"):x["id"] for x in g["nodes"] if x["type"]=="Concept"};edge_set={(e["src"],e["type"],e["tgt"]) for e in g["edges"]}
 pair_results=[]
 for j,(a,b) in enumerate(assigned):
  co=byid[coacts[j]];pair_results.append({"pair_index":j,"causal_present":(cid[f"c{a}"],"causal_influence",cid[f"c{b}"]) in edge_set,"evidence_tick":co["attrs"].get("evidence_tick"),"confirm":co["attrs"].get("evidence_confirm"),"disconfirm":co["attrs"].get("evidence_disconfirm")})
 return {"sparse_authored":sparse,"active_rules":active,"installed_match_order":installed,"progress":progress,"wall_ns":wall,"terminal_progress":terminal,"before_digest":before,"after_digest":after,"nodes":nodes,"edges":edges,"global":global_counts,"per_rule":per,"rule_metadata":meta,"pair_results":pair_results,"initial_reweight_pairs":len(existing)}
def worker(n,q,rep):
 start=fingerprint();seed=json.loads(SEED.read_text());auth=arm(n,q,seed,False);sparse=arm(n,q,seed,True);end=fingerprint()
 return {"n":n,"q":q,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"graph_first_authored":auth,"graph_first_sparse_authored":sparse}
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
  for q in qvalues(n):
   for rep in range(REPS):
    p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),str(q),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600);r=json.loads(p.stdout);runs.append(r)
    a=r["graph_first_authored"];s=r["graph_first_sparse_authored"]
    print(f"N={n} Q={q} rep={rep} installed={a['installed_match_order'][TARGETS[0]][0][1]}/{s['installed_match_order'][TARGETS[0]][0][1]} cand={a['global'].get('cand_tested')}/{s['global'].get('cand_tested')}",flush=True)
 post=fingerprint();RAW.write_text(json.dumps({"locked_inputs":lock,"post_run_inputs":post,"runs":runs},indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps({"workers":len(runs),"source_stable":post==lock,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
