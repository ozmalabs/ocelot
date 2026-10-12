#!/usr/bin/env python3
"""Exercise proposal revision recovery through a fresh-process JSON checkpoint."""
import argparse,hashlib,json,os,platform,subprocess,sys,tempfile,time,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_PROPOSAL_REVISION_PROCESS_RESTART_V1_1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_proposal_revision_process_restart_v1_1.py";LOCK=ROOT/"evaluation/substrate_capability/proposal_revision_process_restart_v1_1_lock_20260928.json";RAW=ROOT/"evaluation/reports/proposal_revision_process_restart_v1_1_20260928.json";CHECKPOINTS=ROOT/"evaluation/substrate_capability/proposal_revision_process_restart_v1_1_checkpoints";SIZES=(2,16,64);CUTS=(0,1,2,3)
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","substrate/world_adapter.py","scripts/substrate_proposal_revision_process_restart_v1_1.py","scripts/analyze_substrate_proposal_revision_process_restart_v1_1.py","docs/research/engine_substrate/SUBSTRATE_PROPOSAL_REVISION_PROCESS_RESTART_V1_1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def install_rules(s):
 from substrate_rs import Term
 g=s._inner;V=lambda z:Term("Var",name=z);A=lambda z,k:Term("Attr",node=V(z),key=k);src=Term("Neighbours",node=V("t"),edge_type="proposes");mx=Term("MaxOver",source=src,var_name="q",value=A("q","score"));base=[["a","revision","r"],["r","for_target","t"]];R=lambda k:A("r",k)
 def rule(stage,name,effects,where=None):g.add_rule({"name":name,"match":base+[["r",stage,"t"]],"where":where.to_dict() if where else None,"effects":effects})
 rule("max","restart_max",[["set_attr_if_different","t","max_score",{"__term__":mx.to_dict()}],["set_attr_if_different","t","max_revision",{"__term__":R("revision").to_dict()}]])
 cnt=Term("Count",source=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score"))))
 rule("count","restart_count",[["set_attr_if_different","t","top_count",{"__term__":cnt.to_dict()}],["set_attr_if_different","t","count_revision",{"__term__":R("revision").to_dict()}]])
 winners=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score")));picked=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=winners),key="label"),other=Term("Lit",value=""))
 rule("decision","restart_decision",[["set_attr_if_different","t","ambiguous",{"__term__":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict()}],["set_attr_if_different","t","selected_label",{"__term__":picked.to_dict()}],["set_attr_if_different","t","decision_revision",{"__term__":R("revision").to_dict()}]])
 complete=Term("And",items=[Term("Eq",a=A("t","max_revision"),b=R("revision")),Term("Eq",a=A("t","count_revision"),b=R("revision")),Term("Eq",a=A("t","decision_revision"),b=R("revision"))])
 rule("commit","restart_commit",[["set_attr_if_different","t","resolved_revision",{"__term__":R("revision").to_dict()}]],complete)
 consume=Term("And",items=[complete,Term("Eq",a=A("t","resolved_revision"),b=R("revision"))])
 g.add_rule({"name":"restart_consume_committed","match":base,"where":consume.to_dict(),"effects":[["set_attr_if_different","t","consumed_label",{"__term__":A("t","selected_label").to_dict()}],["set_attr_if_different","t","consumed_revision",{"__term__":R("revision").to_dict()}]]})
def get_state(s,tid):
 d=s.graph_to_dict();attrs={int(x["id"]):x.get("attrs",{}) for x in d["nodes"]};t=attrs[tid];scores={attrs[int(e["tgt"])]["label"]:attrs[int(e["tgt"])]["score"] for e in d["edges"] if e["type"]=="proposes" and int(e["src"])==tid};mx=max(scores.values());tops=sorted(k for k,v in scores.items() if v==mx)
 return {"target":t,"oracle":{"max_score":mx,"top_labels":tops,"top_count":len(tops)},"revision_nodes":sum(x["type"]=="ResolverRevision" for x in d["nodes"]),"graph":d}
def produce(n,cut,path):
 from substrate_rs import Substrate
 s=Substrate();g=s._inner;target=g.add_node("ConflictTarget",{"max_score":None,"top_count":0,"ambiguous":False,"selected_label":"","resolved_revision":-1,"max_revision":-1,"count_revision":-1,"decision_revision":-1});anchor=g.add_node("ResolverAnchor",{})
 ps=[]
 for i in range(n):p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});ps.append(p);g.add_edge_unchecked(target,"proposes",p,{})
 install_rules(s)
 def newrev(rev):
  rid=g.add_node("ResolverRevision",{"revision":rev});g.add_edge_unchecked(anchor,"revision",rid,{});g.add_edge_unchecked(rid,"for_target",target,{});return rid
 def stage(rid,name):g.add_edge_unchecked(rid,name,target,{});return audit(lambda:g.run_rules_report(100000,True))
 r0=newrev(0)
 for x in ("max","count","decision"):stage(r0,x)
 g.add_edge_unchecked(r0,"commit",target,{});g.run_rules_report(100000,True);g.remove_node(r0)
 # Input mutation followed by a fresh revision. The previous winner is lowered.
 g.set_attr(ps[-1],"score",-1);r1=newrev(1);partial=[]
 for name in ("max","count","decision")[:cut]:
  report,elapsed,metrics=stage(r1,name);partial.append({"stage":name,"report":report,"elapsed_ns":elapsed,"metrics":metrics})
 state=get_state(s,target.value)
 bundle={"graph":state["graph"],"grammar":s.grammar_to_json(),"rules":g.export_rules(),"target_id":target.value,"revision_id":r1.value,"cut":cut,"producer_pid":os.getpid(),"expected_graph_state":state["target"],"proposal_oracle":state["oracle"],"partial_stages":partial}
 encoded=json.dumps(bundle,sort_keys=True,separators=(",",":" )).encode()
 with open(path,"wb") as f:f.write(encoded);f.flush();os.fsync(f.fileno())
 return {"pid":os.getpid(),"checkpoint_bytes":len(encoded),"checkpoint_sha256":hashlib.sha256(encoded).hexdigest(),"partial_stage_names":[x["stage"] for x in partial],"partial_stages":partial,"target_before_restart":state["target"],"revision_nodes":state["revision_nodes"]}
def resume(path):
 from substrate_rs import Substrate,NodeID
 blob=json.loads(Path(path).read_text());s=Substrate();g=s._inner;g.graph_from_dict(blob["graph"])
 for p in blob["grammar"].get("productions",[]):g.add_production_no_mirror(p)
 g.import_rules(blob["rules"])
 graph_parity=s.graph_to_dict()==blob["graph"];grammar_parity=s.grammar_to_json()==blob["grammar"]
 def canonical_rules(rows):
  out=[]
  for item in rows:
   x=copy.deepcopy(item);x.pop("content_hash",None);x["match"]=sorted(x.get("match",[]),key=lambda e:tuple(e));out.append(x)
  return out
 rule_parity=canonical_rules(g.export_rules())==canonical_rules(blob["rules"])
 tid=blob["target_id"];rid=blob["revision_id"];before=get_state(s,tid);attrs=before["target"]
 stages=[];stamp_for={"max":"max_revision","count":"count_revision","decision":"decision_revision"}
 for name in ("max","count","decision"):
  if attrs.get(stamp_for[name])!=1:
   g.add_edge_unchecked(NodeID(rid),name,NodeID(tid),{});report,elapsed,metrics=audit(lambda:g.run_rules_report(100000,True));stages.append({"stage":name,"report":report,"elapsed_ns":elapsed,"metrics":metrics});attrs=get_state(s,tid)["target"]
 g.add_edge_unchecked(NodeID(rid),"commit",NodeID(tid),{});report,elapsed,metrics=audit(lambda:g.run_rules_report(100000,True));stages.append({"stage":"commit","report":report,"elapsed_ns":elapsed,"metrics":metrics})
 final=get_state(s,tid)
 return {"pid":os.getpid(),"graph_roundtrip_exact":graph_parity,"grammar_roundtrip_exact":grammar_parity,"rules_semantic_equivalent":rule_parity,"state_before_resume":{"target":before["target"],"revision_nodes":before["revision_nodes"]},"resume_stages":stages,"final_state":{"target":final["target"],"oracle":final["oracle"],"revision_nodes":final["revision_nodes"]}}
def child(mode,n,cut,path):
 result=produce(n,cut,path) if mode=="produce" else resume(path);print(json.dumps(result,sort_keys=True))
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked:raise RuntimeError("source/native lock mismatch")
 cells=[]
 with tempfile.TemporaryDirectory(prefix=f"proposal_restart_{wid}_") as td:
  worker_dir=CHECKPOINTS/f"worker_{wid}"
  worker_dir.mkdir(parents=True,exist_ok=False)
  for n in SIZES:
   for cut in CUTS:
    path=str(worker_dir/f"checkpoint_{n}_{cut}.json")
    cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--child","produce","--n",str(n),"--cut",str(cut),"--path",path],cwd=ROOT,text=True,capture_output=True)
    if cp.returncode:raise RuntimeError(f"producer failed: {cp.stderr[-2000:]}")
    prod=json.loads(cp.stdout.strip().splitlines()[-1])
    rp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--child","resume","--n",str(n),"--cut",str(cut),"--path",path],cwd=ROOT,text=True,capture_output=True)
    if rp.returncode:raise RuntimeError(f"resume failed: {rp.stderr[-2000:]}")
    res=json.loads(rp.stdout.strip().splitlines()[-1]);content=Path(path).read_bytes();verified={"path":str(Path(path).relative_to(ROOT)),"bytes":len(content),"sha256":hashlib.sha256(content).hexdigest(),"matches_producer_manifest":len(content)==prod["checkpoint_bytes"] and hashlib.sha256(content).hexdigest()==prod["checkpoint_sha256"]};cells.append({"n":n,"cut":cut,"producer":prod,"checkpoint":verified,"resume":res})
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":cells}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");ap.add_argument("--child",choices=("produce","resume"));ap.add_argument("--n",type=int);ap.add_argument("--cut",type=int);ap.add_argument("--path");a=ap.parse_args()
 if a.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"proposal_revision_process_restart_v1_1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"cuts":CUTS},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if a.child:child(a.child,a.n,a.cut,a.path);return
 if a.worker is not None:print(json.dumps(worker(a.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit("refusing to overwrite raw capture")
 if CHECKPOINTS.exists():raise SystemExit("refusing to overwrite checkpoint evidence directory")
 CHECKPOINTS.mkdir(parents=True)
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"proposal_revision_process_restart_v1_1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
