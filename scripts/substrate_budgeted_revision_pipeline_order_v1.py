#!/usr/bin/env python3
"""Probe stale commits under budget cuts, rule order, and revision guards."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_BUDGETED_REVISION_PIPELINE_ORDER_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_budgeted_revision_pipeline_order_v1.py";LOCK=ROOT/"evaluation/substrate_capability/budgeted_revision_pipeline_order_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/budgeted_revision_pipeline_order_v1_20260928.json";SIZES=(2,8,64);ORDERS=("normal","reverse");GUARDS=("unguarded","guarded")
SOURCES=("runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_budgeted_revision_pipeline_order_v1.py","scripts/analyze_substrate_budgeted_revision_pipeline_order_v1.py","docs/research/engine_substrate/SUBSTRATE_BUDGETED_REVISION_PIPELINE_ORDER_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def one(n,order,guard):
 from substrate_rs import Substrate,Term
 s=Substrate();g=s._inner;t=g.add_node("ConflictTarget",{"max_score":-1,"top_count":0,"ambiguous":False,"selected_label":"","max_revision":-1,"count_revision":-1,"decision_revision":-1,"resolved_revision":-1});anchor=g.add_node("ResolverAnchor",{});ps=[]
 for i in range(n):p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});ps.append(p);g.add_edge_unchecked(t,"proposes",p,{})
 V=lambda x:Term("Var",name=x);A=lambda x,k:Term("Attr",node=V(x),key=k);src=Term("Neighbours",node=V("t"),edge_type="proposes");mx=Term("MaxOver",source=src,var_name="q",value=A("q","score"));base=[["a","revision","r"],["r","for_target","t"]];R=A("r","revision")
 specs={}
 specs["max"]={"name":"budget_max","match":base+[["r","max","t"]],"where":None,"effects":[["set_attr_if_different","t","max_score",{"__term__":mx.to_dict()}],["set_attr_if_different","t","max_revision",{"__term__":R.to_dict()}]]}
 count=Term("Count",source=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score"))))
 specs["count"]={"name":"budget_count","match":base+[["r","count","t"]],"where":Term("Eq",a=A("t","max_revision"),b=R).to_dict() if guard=="guarded" else None,"effects":[["set_attr_if_different","t","top_count",{"__term__":count.to_dict()}],["set_attr_if_different","t","count_revision",{"__term__":R.to_dict()}]]}
 winners=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score")));chosen=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=winners),key="label"),other=Term("Lit",value=""))
 specs["decision"]={"name":"budget_decision","match":base+[["r","decision","t"]],"where":Term("Eq",a=A("t","count_revision"),b=R).to_dict() if guard=="guarded" else None,"effects":[["set_attr_if_different","t","ambiguous",{"__term__":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict()}],["set_attr_if_different","t","selected_label",{"__term__":chosen.to_dict()}],["set_attr_if_different","t","decision_revision",{"__term__":R.to_dict()}]]}
 complete=Term("And",items=[Term("Eq",a=A("t",k),b=R) for k in ("max_revision","count_revision","decision_revision")])
 specs["commit"]={"name":"budget_commit","match":base+[["r","commit","t"]],"where":complete.to_dict(),"effects":[["set_attr_if_different","t","resolved_revision",{"__term__":R.to_dict()}]]}
 names=("max","count","decision","commit") if order=="normal" else ("decision","count","max","commit")
 for name in names:g.add_rule(specs[name])
 def revision(rev):
  rid=g.add_node("ResolverRevision",{"revision":rev});g.add_edge_unchecked(anchor,"revision",rid,{});g.add_edge_unchecked(rid,"for_target",t,{})
  for name in ("max","count","decision","commit"):g.add_edge_unchecked(rid,name,t,{})
  return rid
 old=revision(0);full0,_,_=audit(lambda:g.run_rules_report(100000,True));initial=next(z["attrs"] for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value)
 if full0["status"]!="fixed_point" or initial.get("resolved_revision")!=0:raise RuntimeError("revision 0 failed to initialize")
 g.remove_node(old);g.set_attr(ps[-1],"score",-1);revision(1)
 limited,l_ns,l_metrics=audit(lambda:g.run_rules_report(1,True));state1=next(z["attrs"] for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value)
 resumed,r_ns,r_metrics=audit(lambda:g.run_rules_report(100000,True));state2=next(z["attrs"] for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value)
 return {"n":n,"order":order,"guard":guard,"limited":{"report":dict(limited),"elapsed_ns":l_ns,"metrics":l_metrics,"attrs":state1},"resumed":{"report":dict(resumed),"elapsed_ns":r_ns,"metrics":r_metrics,"attrs":state2},"expected":{"max_score":n-2,"top_count":1,"selected_label":f"p{n-2:03d}"}}
def worker(wid):
 lock=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=lock:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":lock,"cells":[one(n,o,g) for n in SIZES for o in ORDERS for g in GUARDS]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");a=ap.parse_args()
 if a.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"budgeted_revision_pipeline_order_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"orders":ORDERS,"guards":GUARDS,"progress_budget":1},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if a.worker is not None:print(json.dumps(worker(a.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit("refusing to overwrite raw capture")
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2000:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"budgeted_revision_pipeline_order_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
