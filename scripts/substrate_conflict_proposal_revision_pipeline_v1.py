#!/usr/bin/env python3
"""Measure explicit revision-event, ordered closure pipeline for max resolution."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_REVISION_PIPELINE_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_conflict_proposal_revision_pipeline_v1.py";LOCK=ROOT/"evaluation/substrate_capability/conflict_proposal_revision_pipeline_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/conflict_proposal_revision_pipeline_v1_20260928.json";SIZES=(2,8,32,64)
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_conflict_proposal_revision_pipeline_v1.py","scripts/analyze_substrate_conflict_proposal_revision_pipeline_v1.py","docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_REVISION_PIPELINE_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def case(n):
 from substrate_rs import Substrate,Term
 s=Substrate();g=s._inner;t=g.add_node("ConflictTarget",{});anchor=g.add_node("ResolverAnchor",{});proposals={}
 for i in range(n):
  p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});proposals[f"p{i:03d}"]=p;g.add_edge_unchecked(t,"proposes",p,{})
 V=lambda z:Term("Var",name=z);A=lambda z,k:Term("Attr",node=V(z),key=k);source=Term("Neighbours",node=V("t"),edge_type="proposes");max_term=Term("MaxOver",source=source,var_name="q",value=A("q","score"))
 pattern_base=[["a","revision","r"],["r","for_target","t"]]
 def add_rule(stage,name,effects):g.add_rule({"name":name,"match":pattern_base+[["r",stage,"t"]],"where":None,"effects":effects})
 add_rule("compute_max","revision_compute_max",[["set_attr_if_different","t","max_score",{"__term__":max_term.to_dict()}]])
 count_top=Term("Count",source=Term("Filter",source=source,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score"))))
 add_rule("compute_count","revision_compute_count",[["set_attr_if_different","t","top_count",{"__term__":count_top.to_dict()}]])
 winners=Term("Filter",source=source,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score")))
 pick=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=winners),key="label"),other=Term("Lit",value=""))
 add_rule("compute_decision","revision_compute_decision",[["set_attr_if_different","t","ambiguous",{"__term__":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict()}],["set_attr_if_different","t","selected_label",{"__term__":pick.to_dict()}]])
 history=[]
 def revision(rev,action):
  rid=g.add_node("ResolverRevision",{"revision":rev,"action":action});g.add_edge_unchecked(anchor,"revision",rid,{});g.add_edge_unchecked(rid,"for_target",t,{})
  stage_records=[]
  for stage in ("compute_max","compute_count","compute_decision"):
   g.add_edge_unchecked(rid,stage,t,{})
   report,elapsed,metrics=audit(lambda:g.run_rules_report(100000,True))
   stage_records.append({"stage":stage,"report":report,"elapsed_ns":elapsed,"metrics":metrics})
  graph=g.graph_to_dict();attrs={int(z["id"]):z.get("attrs",{}) for z in graph["nodes"]};ta=attrs[t.value];adj=[int(e["tgt"]) for e in graph["edges"] if e["type"]=="proposes" and int(e["src"])==t.value];scoremap={attrs[p]["label"]:attrs[p]["score"] for p in adj};maxscore=max(scoremap.values());tops=sorted(k for k,v in scoremap.items() if v==maxscore)
  history.append({"revision":rev,"action":action,"stages":stage_records,"target":{"max_score":ta.get("max_score"),"top_count":ta.get("top_count"),"ambiguous":ta.get("ambiguous"),"selected_label":ta.get("selected_label")},"oracle":{"max_score":maxscore,"top_labels":tops,"proposal_scores":scoremap}})
 revision(0,"initial")
 high=g.add_node("ConflictProposal",{"label":"p_high","score":n+5});proposals["p_high"]=high;g.add_edge_unchecked(t,"proposes",high,{});revision(1,"add_higher")
 tied=g.add_node("ConflictProposal",{"label":"p_tie","score":n+5});proposals["p_tie"]=tied;g.add_edge_unchecked(t,"proposes",tied,{});revision(2,"add_tie")
 g.remove_edge(t,"proposes",tied);revision(3,"remove_tie")
 g.set_attr(high,"score",-1);revision(4,"lower_higher_score")
 return {"n":n,"revisions":history}
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":[case(n) for n in SIZES]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"conflict_proposal_revision_pipeline_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
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
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"conflict_proposal_revision_pipeline_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
