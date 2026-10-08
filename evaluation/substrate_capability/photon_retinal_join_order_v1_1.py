#!/usr/bin/env python3
"""Source-locked exhaustive matcher-order study for production retinal rule."""
from __future__ import annotations
import copy,hashlib,itertools,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
SEED=ROOT/"seeds/photon_retina_per_sensor.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/PHOTON_RETINAL_JOIN_ORDER_V1_1_AMENDMENT_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_photon_retinal_join_order_v1_1.py"
LOCK=ROOT/"evaluation/substrate_capability/photon_retinal_join_order_v1_1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/photon_retinal_join_order_v1_1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/photon_retinal_join_order_v1_1_20261001.json"
TARGET="photon_column_synthesizes_retinal_percept"
RELATIONS=("rod_receptor","l_receptor","m_receptor","s_receptor","has_retinal_percept")
PROFILES=("uniform","correlated","rotated");REPS=3;N=12;MAX_STEPS=100
SOURCES=("runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 names=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in names},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def profile_counts(profile):
 counts=[]
 for r in range(4):
  if profile=="uniform":counts.append([2]*N)
  elif profile=="correlated":counts.append([1+(i%4) for i in range(N)])
  elif profile=="rotated":counts.append([1+((i+r)%4) for i in range(N)])
  else:raise RuntimeError(profile)
 return counts
def build(profile,order=None,audit=True):
 inner=sr.Substrate()._inner;counts=profile_counts(profile)
 manifest=json.loads(SEED.read_text());row=next(x for x in manifest["rules"] if x.get("name")==TARGET)
 manifest["rules"]=[];inner.load_seed_manifest(engine_rules_only(manifest))
 activations={"rod_receptor":0.25,"l_receptor":0.75,"m_receptor":0.5,"s_receptor":0.125}
 for i in range(N):
  col=inner.add_node("RetinalColumn",{"fixture_id":f"column:{i}","column_index":i,"column_epoch":1})
  for r,edge_type in enumerate(RELATIONS[:4]):
   for j in range(counts[r][i]):
    receptor=inner.add_node("Photoreceptor",{"fixture_id":f"{edge_type}:{i}:{j}","rod_epoch":1,"activation":activations[edge_type]})
    inner.add_edge(col,edge_type,receptor,{})
  epoch=0 if i==N-1 else 1
  percept=inner.add_node("RetinalPercept",{"fixture_id":f"percept:{i}","percept_index":i,"percept_epoch":epoch,"intensity":0.0,"red_green":0.0,"blue_yellow":0.0,"salience":0.0})
  inner.add_edge(col,"has_retinal_percept",percept,{})
 if order is None:idx=inner.add_rule(copy.deepcopy(row))
 else:
  ordered=copy.deepcopy(row);ordered["match"]=[row["match"][i] for i in order]
  idx=inner.add_rule_preserving_match_order(ordered)
 installed=inner.export_rules();installed=json.loads(installed) if isinstance(installed,str) else installed
 installed_row=next(x for x in installed if x.get("name")==TARGET)
 installed_edges=[x[1] for x in installed_row["match"]]
 if audit:
  inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 before,digest_n,digest_e=graph_facts(inner)
 started=time.perf_counter_ns();progress=int(inner.run_rules(MAX_STEPS));wall=time.perf_counter_ns()-started
 if audit:
  global_counts={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()}
  per_rule=[list(x) for x in inner.scale_audit_per_rule_snapshot()]
  metadata=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
  inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False)
 else:global_counts={};per_rule=[];metadata=[]
 terminal=int(inner.run_rules(1));after,_,_=graph_facts(inner);g=inner.graph_to_dict()
 percepts={x["attrs"]["fixture_id"]:x["attrs"] for x in g["nodes"] if x["type"]=="RetinalPercept"}
 return {"order_indices":list(order) if order is not None else None,"installed_order":installed_edges,"before_digest":before,"after_digest":after,"digest_nodes":digest_n,"digest_edges":digest_e,"progress":progress,"terminal_progress":terminal,"wall_ns":wall,"global":global_counts,"per_rule":per_rule,"rule_metadata":metadata,"percepts":percepts}
def graph_facts(inner):
 g=inner.graph_to_dict();tokens={x["id"]:x["attrs"].get("fixture_id",f"{x['type']}:{x['id']}") for x in g["nodes"]}
 ns=sorted(((x["type"],x["attrs"]) for x in g["nodes"]),key=lambda x:json.dumps(x,sort_keys=True,default=str))
 es=sorted((tokens[e["src"]],e["type"],tokens[e["tgt"]],e.get("attrs",{})) for e in g["edges"])
 raw=json.dumps({"nodes":ns,"edges":es},sort_keys=True,separators=(",",":"),default=str)
 return hashlib.sha256(raw.encode()).hexdigest(),len(ns),len(es)
def worker(profile,rep):
 start=fingerprint();permutations=list(itertools.permutations(range(5)))
 default=build(profile,None,True)
 arms=[build(profile,p,True) for p in permutations]
 best=min(arms,key=lambda a:(int(a["global"].get("cand_tested",0)),tuple(a["order_indices"])))
 default_plain=build(profile,None,False);best_plain=build(profile,tuple(best["order_indices"]),False)
 end=fingerprint()
 return {"profile":profile,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"default":default,"permutations":arms,"best":best,"default_plain":default_plain,"best_plain":best_plain}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for profile in PROFILES:
  for rep in range(REPS):
   p=subprocess.run([sys.executable,str(RUNNER),"--worker",profile,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600)
   row=json.loads(p.stdout);runs.append(row);print(f"profile={profile} rep={rep} default={row['default']['global'].get('cand_tested')} best={row['best']['global'].get('cand_tested')} order={row['best']['installed_order']}",flush=True)
 post=fingerprint();raw={"locked_inputs":lock,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True)
 print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
