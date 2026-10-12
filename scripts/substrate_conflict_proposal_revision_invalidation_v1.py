#!/usr/bin/env python3
"""Measure refresh correctness across proposal-set and score revisions."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_REVISION_INVALIDATION_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_conflict_proposal_revision_invalidation_v1.py";LOCK=ROOT/"evaluation/substrate_capability/conflict_proposal_revision_invalidation_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/conflict_proposal_revision_invalidation_v1_20260928.json";SIZES=(2,8,32,64)
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_conflict_proposal_revision_invalidation_v1.py","scripts/analyze_substrate_conflict_proposal_revision_invalidation_v1.py","docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_REVISION_INVALIDATION_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audited(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def case(n):
 from substrate_rs import Substrate,Term
 s=Substrate();g=s._inner;t=g.add_node("ConflictTarget",{});x=g.add_node("ConflictTrigger",{});g.add_edge_unchecked(x,"trigger",t,{})
 nodes=[]
 for i in range(n):
  p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});nodes.append(p);g.add_edge_unchecked(t,"proposes",p,{})
 V=lambda z:Term("Var",name=z);A=lambda z,k:Term("Attr",node=V(z),key=k);source=Term("Neighbours",node=V("t"),edge_type="proposes");maxv=Term("MaxOver",source=source,var_name="q",value=A("q","score"))
 g.add_rule({"name":"refresh_max","match":[["x","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","max_score",{"__term__":maxv.to_dict()}]]})
 is_top=Term("Eq",a=A("p","score"),b=A("t","max_score"))
 g.add_rule({"name":"refresh_top_flag","match":[["t","proposes","p"]],"where":None,"effects":[["set_attr_if_different","p","is_top",{"__term__":is_top.to_dict()}]]})
 top_filter=Term("Filter",source=source,var_name="q",predicate=Term("Eq",a=A("q","is_top"),b=Term("Lit",value=True)));count=Term("Count",source=top_filter)
 g.add_rule({"name":"refresh_top_count","match":[["x","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","top_count",{"__term__":count.to_dict()}]]})
 tie=Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1))
 g.add_rule({"name":"refresh_ambiguity","match":[["x","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","ambiguous",{"__term__":tie.to_dict()}]]})
 selected=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=top_filter),key="label"),other=Term("Lit",value=""))
 g.add_rule({"name":"refresh_selection","match":[["x","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","selected_label",{"__term__":selected.to_dict()}]]})
 phases=[]
 def settle(name,expected_scores):
  report,elapsed,metrics=audited(lambda:g.run_rules_report(100000,True));gd=g.graph_to_dict();attrs={int(z["id"]):z.get("attrs",{}) for z in gd["nodes"]};ta=attrs[t.value];adj=[int(e["tgt"]) for e in gd["edges"] if e["type"]=="proposes" and int(e["src"])==t.value];scores={attrs[i]["label"]:attrs[i]["score"] for i in adj};tops=sorted(k for k,v in scores.items() if v==max(scores.values())) if scores else []
  phases.append({"name":name,"report":report,"elapsed_ns":elapsed,"metrics":metrics,"target":{"max_score":ta.get("max_score"),"top_count":ta.get("top_count"),"ambiguous":ta.get("ambiguous"),"selected_label":ta.get("selected_label")},"score_oracle":{"maximum":max(scores.values()) if scores else None,"top_labels":tops,"scores":scores},"top_flags":{attrs[i]["label"]:attrs[i].get("is_top") for i in adj}})
 settle("initial_unique",None)
 high=g.add_node("ConflictProposal",{"label":"p_high","score":n+5});nodes.append(high);g.add_edge_unchecked(t,"proposes",high,{})
 settle("add_higher",None)
 tie_node=g.add_node("ConflictProposal",{"label":"p_tie","score":n+5});g.add_edge_unchecked(t,"proposes",tie_node,{})
 settle("add_tie",None)
 g.remove_edge(t,"proposes",tie_node)
 settle("remove_tie",None)
 g.set_attr(high,"score",-1)
 settle("lower_high_score",None)
 return {"n":n,"phases":phases}
def worker(wid):
 lock=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=lock:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":lock,"cells":[case(n) for n in SIZES]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"conflict_proposal_revision_invalidation_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if args.worker is not None:print(json.dumps(worker(args.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit("refusing to overwrite raw capture")
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"conflict_proposal_revision_invalidation_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
