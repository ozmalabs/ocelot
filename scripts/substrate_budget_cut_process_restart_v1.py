#!/usr/bin/env python3
"""Checkpoint a budget-cut resolver pass, restart, and test guarded recovery."""
import argparse,copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_BUDGET_CUT_PROCESS_RESTART_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_budget_cut_process_restart_v1.py";LOCK=ROOT/"evaluation/substrate_capability/budget_cut_process_restart_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/budget_cut_process_restart_v1_20260928.json";CHECKPOINTS=ROOT/"evaluation/substrate_capability/budget_cut_process_restart_v1_checkpoints";SIZES=(2,64);ARMS=(("reverse","guarded"),("reverse","unguarded"),("normal","guarded"))
SOURCES=("runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_budget_cut_process_restart_v1.py","scripts/analyze_substrate_budget_cut_process_restart_v1.py","docs/research/engine_substrate/SUBSTRATE_BUDGET_CUT_PROCESS_RESTART_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def install(s,order,guard):
 from substrate_rs import Term
 g=s._inner;V=lambda x:Term("Var",name=x);A=lambda x,k:Term("Attr",node=V(x),key=k);src=Term("Neighbours",node=V("t"),edge_type="proposes");mx=Term("MaxOver",source=src,var_name="q",value=A("q","score"));base=[["a","revision","r"],["r","for_target","t"]];R=A("r","revision")
 specs={}
 specs["max"]={"name":"restart_budget_max","match":base+[["r","max","t"]],"where":None,"effects":[["set_attr_if_different","t","max_score",{"__term__":mx.to_dict()}],["set_attr_if_different","t","max_revision",{"__term__":R.to_dict()}]]}
 cnt=Term("Count",source=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score"))))
 specs["count"]={"name":"restart_budget_count","match":base+[["r","count","t"]],"where":Term("Eq",a=A("t","max_revision"),b=R).to_dict() if guard=="guarded" else None,"effects":[["set_attr_if_different","t","top_count",{"__term__":cnt.to_dict()}],["set_attr_if_different","t","count_revision",{"__term__":R.to_dict()}]]}
 winners=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score")));choice=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=winners),key="label"),other=Term("Lit",value=""))
 specs["decision"]={"name":"restart_budget_decision","match":base+[["r","decision","t"]],"where":Term("Eq",a=A("t","count_revision"),b=R).to_dict() if guard=="guarded" else None,"effects":[["set_attr_if_different","t","ambiguous",{"__term__":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict()}],["set_attr_if_different","t","selected_label",{"__term__":choice.to_dict()}],["set_attr_if_different","t","decision_revision",{"__term__":R.to_dict()}]]}
 ready=Term("And",items=[Term("Eq",a=A("t",k),b=R) for k in ("max_revision","count_revision","decision_revision")])
 specs["commit"]={"name":"restart_budget_commit","match":base+[["r","commit","t"]],"where":ready.to_dict(),"effects":[["set_attr_if_different","t","resolved_revision",{"__term__":R.to_dict()}]]}
 consume=Term("And",items=[ready,Term("Eq",a=A("t","resolved_revision"),b=R)])
 specs["consume"]={"name":"restart_budget_consume","match":base,"where":consume.to_dict(),"effects":[["set_attr_if_different","t","consumed_label",{"__term__":A("t","selected_label").to_dict()}],["set_attr_if_different","t","consumed_revision",{"__term__":R.to_dict()}]]}
 order=("max","count","decision","commit","consume") if order=="normal" else ("decision","count","max","commit","consume")
 for key in order:g.add_rule(specs[key])
def snapshot(s,tid):
 d=s.graph_to_dict();attrs={int(x["id"]):x.get("attrs",{}) for x in d["nodes"]};scores={attrs[int(e["tgt"])]["label"]:attrs[int(e["tgt"])]["score"] for e in d["edges"] if e["type"]=="proposes" and int(e["src"])==tid};mx=max(scores.values());tops=sorted(k for k,v in scores.items() if v==mx);return {"graph":d,"target":attrs[tid],"oracle":{"max_score":mx,"top_labels":tops,"top_count":len(tops)},"revision_nodes":sum(x["type"]=="ResolverRevision" for x in d["nodes"])}
def produce(n,order,guard,path):
 from substrate_rs import Substrate
 s=Substrate();g=s._inner;target=g.add_node("ConflictTarget",{"max_score":-1,"top_count":0,"ambiguous":False,"selected_label":"","max_revision":-1,"count_revision":-1,"decision_revision":-1,"resolved_revision":-1});anchor=g.add_node("ResolverAnchor",{});props=[]
 for i in range(n):p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});props.append(p);g.add_edge_unchecked(target,"proposes",p,{})
 install(s,order,guard)
 def event(rev):
  r=g.add_node("ResolverRevision",{"revision":rev});g.add_edge_unchecked(anchor,"revision",r,{});g.add_edge_unchecked(r,"for_target",target,{})
  for stage in ("max","count","decision","commit"):g.add_edge_unchecked(r,stage,target,{})
  return r
 r0=event(0);setup=dict(g.run_rules_report(100000,True));initial=snapshot(s,target.value)
 if setup["status"]!="fixed_point" or initial["target"].get("resolved_revision")!=0:raise RuntimeError("initial revision did not settle")
 g.remove_node(r0);g.set_attr(props[-1],"score",-1);r1=event(1)
 limited,elapsed,metrics=audit(lambda:g.run_rules_report(1,True));state=snapshot(s,target.value)
 bundle={"graph":state["graph"],"grammar":s.grammar_to_json(),"rules":g.export_rules(),"target_id":target.value,"revision_id":r1.value,"n":n,"order":order,"guard":guard,"limited":{"report":dict(limited),"elapsed_ns":elapsed,"metrics":metrics},"target_after_budget_pass":state["target"],"oracle":state["oracle"],"revision_nodes":state["revision_nodes"],"producer_pid":os.getpid()}
 raw=json.dumps(bundle,sort_keys=True,separators=(",",":")).encode()
 with open(path,"wb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {"pid":os.getpid(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"limited":bundle["limited"],"target":state["target"],"oracle":state["oracle"],"revision_nodes":state["revision_nodes"]}
def resume(path):
 from substrate_rs import Substrate,NodeID
 b=json.loads(Path(path).read_text());s=Substrate();g=s._inner;g.graph_from_dict(b["graph"])
 for p in b["grammar"].get("productions",[]):g.add_production_no_mirror(p)
 g.import_rules(b["rules"])
 gp=s.graph_to_dict()==b["graph"];gr=s.grammar_to_json()==b["grammar"]
 def canonical(rows):
  out=[]
  for item in rows:
   x=copy.deepcopy(item);x.pop("content_hash",None);x["match"]=sorted(x.get("match",[]),key=lambda e:tuple(e));out.append(x)
  return out
 rp=canonical(g.export_rules())==canonical(b["rules"])
 report,elapsed,metrics=audit(lambda:g.run_rules_report(100000,True));state=snapshot(s,b["target_id"])
 return {"pid":os.getpid(),"graph_exact":gp,"grammar_exact":gr,"rules_semantic":rp,"resume":{"report":report,"elapsed_ns":elapsed,"metrics":metrics},"target":state["target"],"oracle":state["oracle"],"revision_nodes":state["revision_nodes"],"config":{"order":b["order"],"guard":b["guard"],"n":b["n"]}}
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked:raise RuntimeError("source/native lock mismatch")
 wd=CHECKPOINTS/f"worker_{wid}";wd.mkdir(parents=True,exist_ok=False);cells=[]
 for n in SIZES:
  for order,guard in ARMS:
   path=wd/f"checkpoint_{n}_{order}_{guard}.json";cmd=[sys.executable,str(Path(__file__).resolve()),"--child","produce","--n",str(n),"--order",order,"--guard",guard,"--path",str(path)];cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
   if cp.returncode:raise RuntimeError(f"producer failed: {cp.stderr[-2000:]}")
   prod=json.loads(cp.stdout.strip().splitlines()[-1]);cmd=[sys.executable,str(Path(__file__).resolve()),"--child","resume","--n",str(n),"--order",order,"--guard",guard,"--path",str(path)];rp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
   if rp.returncode:raise RuntimeError(f"resume failed: {rp.stderr[-2000:]}")
   res=json.loads(rp.stdout.strip().splitlines()[-1]);data=path.read_bytes();cpinfo={"path":str(path.relative_to(ROOT)),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"matches_manifest":len(data)==prod["bytes"] and hashlib.sha256(data).hexdigest()==prod["sha256"]};cells.append({"n":n,"order":order,"guard":guard,"producer":prod,"checkpoint":cpinfo,"resume":res})
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":cells}
def child(mode,n,order,guard,path):print(json.dumps(produce(n,order,guard,path) if mode=="produce" else resume(path),sort_keys=True))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");ap.add_argument("--child",choices=("produce","resume"));ap.add_argument("--n",type=int);ap.add_argument("--order",choices=("normal","reverse"));ap.add_argument("--guard",choices=("guarded","unguarded"));ap.add_argument("--path");a=ap.parse_args()
 if a.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"budget_cut_process_restart_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"arms":ARMS},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if a.child:child(a.child,a.n,a.order,a.guard,a.path);return
 if a.worker is not None:print(json.dumps(worker(a.worker),sort_keys=True));return
 if RAW.exists() or CHECKPOINTS.exists():raise SystemExit("refusing to overwrite prior raw/checkpoint artifacts")
 CHECKPOINTS.mkdir(parents=True);lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"budget_cut_process_restart_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
