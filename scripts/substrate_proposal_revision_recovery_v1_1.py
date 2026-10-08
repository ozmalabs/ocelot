#!/usr/bin/env python3
"""Inject between-stage cuts and measure revision-stamped resolver recovery."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_PROPOSAL_REVISION_RECOVERY_V1_1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_proposal_revision_recovery_v1_1.py";LOCK=ROOT/"evaluation/substrate_capability/proposal_revision_recovery_v1_1_lock_20260928.json";RAW=ROOT/"evaluation/reports/proposal_revision_recovery_v1_1_20260928.json";SIZES=(2,8,32,64);CUTS=(0,1,2,3)
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_proposal_revision_recovery_v1_1.py","scripts/analyze_substrate_proposal_revision_recovery_v1_1.py","docs/research/engine_substrate/SUBSTRATE_PROPOSAL_REVISION_RECOVERY_V1_1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def one(n,cut):
 from substrate_rs import Substrate,Term
 s=Substrate();g=s._inner;t=g.add_node("ConflictTarget",{});anchor=g.add_node("ResolverAnchor",{});ps=[]
 for i in range(n):
  p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":i});ps.append(p);g.add_edge_unchecked(t,"proposes",p,{})
 V=lambda z:Term("Var",name=z);A=lambda z,k:Term("Attr",node=V(z),key=k);src=Term("Neighbours",node=V("t"),edge_type="proposes");maxterm=Term("MaxOver",source=src,var_name="q",value=A("q","score"));base=[["a","revision","r"],["r","for_target","t"]];R=lambda key:A("r",key)
 def add_rule(stage,name,effects,where=None):g.add_rule({"name":name,"match":base+[["r",stage,"t"]],"where":where.to_dict() if where else None,"effects":effects})
 add_rule("max","revision_max",[["set_attr_if_different","t","max_score",{"__term__":maxterm.to_dict()}],["set_attr_if_different","t","max_revision",{"__term__":R("revision").to_dict()}]])
 count=Term("Count",source=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score"))))
 add_rule("count","revision_count",[["set_attr_if_different","t","top_count",{"__term__":count.to_dict()}],["set_attr_if_different","t","count_revision",{"__term__":R("revision").to_dict()}]])
 winners=Term("Filter",source=src,var_name="q",predicate=Term("Eq",a=A("q","score"),b=A("t","max_score")))
 chosen=Term("IfThenElse",cond=Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),then=Term("Attr",node=Term("Pick",source=winners),key="label"),other=Term("Lit",value=""))
 add_rule("decision","revision_decision",[["set_attr_if_different","t","ambiguous",{"__term__":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict()}],["set_attr_if_different","t","selected_label",{"__term__":chosen.to_dict()}],["set_attr_if_different","t","decision_revision",{"__term__":R("revision").to_dict()}]])
 complete=Term("And",items=[Term("Eq",a=A("t","max_revision"),b=R("revision")),Term("Eq",a=A("t","count_revision"),b=R("revision")),Term("Eq",a=A("t","decision_revision"),b=R("revision"))])
 add_rule("commit","revision_commit",[["set_attr_if_different","t","resolved_revision",{"__term__":R("revision").to_dict()}]],complete)
 stage_names=("max","count","decision")
 def runstage(rid,stage):
  g.add_edge_unchecked(rid,stage,t,{})
  report,elapsed,metrics=audit(lambda:g.run_rules_report(100000,True));return {"stage":stage,"report":report,"elapsed_ns":elapsed,"metrics":metrics}
 def state():
  d=g.graph_to_dict();attrs={int(z["id"]):z.get("attrs",{}) for z in d["nodes"]};ta=attrs[t.value];scores={attrs[int(e["tgt"])]["label"]:attrs[int(e["tgt"])]["score"] for e in d["edges"] if e["type"]=="proposes" and int(e["src"])==t.value};mx=max(scores.values());tops=sorted(k for k,v in scores.items() if v==mx);events=sum(z["type"]=="ResolverRevision" for z in d["nodes"]);return {"target":ta,"oracle":{"max_score":mx,"top_labels":tops,"top_count":len(tops)},"revision_nodes":events,"node_count":len(d["nodes"]),"edge_count":len(d["edges"])}
 old=g.add_node("ResolverRevision",{"revision":0});g.add_edge_unchecked(anchor,"revision",old,{});g.add_edge_unchecked(old,"for_target",t,{})
 setup=[runstage(old,z) for z in stage_names];g.add_edge_unchecked(old,"commit",t,{});setup.append({"stage":"commit","report":dict(g.run_rules_report(100000,True)),"elapsed_ns":0,"metrics":{}})
 initial_state=state()
 # Mutate the unique winner down, then replace the old event with a fresh revision.
 g.set_attr(ps[-1],"score",-1);g.remove_node(old);rid=g.add_node("ResolverRevision",{"revision":1});g.add_edge_unchecked(anchor,"revision",rid,{});g.add_edge_unchecked(rid,"for_target",t,{})
 partial=[]
 for name in stage_names[:cut]:partial.append(runstage(rid,name))
 pre_recovery=state()
 stamps={k:pre_recovery["target"].get(k) for k in ("max_revision","count_revision","decision_revision","resolved_revision")}
 expected_by_stage={"max":"max_revision","count":"count_revision","decision":"decision_revision"};resume=[]
 for name in stage_names:
  if stamps[expected_by_stage[name]]!=1:resume.append(runstage(rid,name))
 # Gate the commit rule with all three revision stamps.
 g.add_edge_unchecked(rid,"commit",t,{})
 commit_report,commit_ns,commit_metrics=audit(lambda:g.run_rules_report(100000,True));resume.append({"stage":"commit","report":commit_report,"elapsed_ns":commit_ns,"metrics":commit_metrics})
 final=state()
 return {"n":n,"cut_after_stages":cut,"initial_setup_stages":setup,"initial_state":{k:v for k,v in initial_state.items() if k in ("target","oracle","revision_nodes")},"interrupted_stages":partial,"pre_recovery":{"state":pre_recovery,"stamps":stamps,"advertises_current_commit":stamps["resolved_revision"]==1},"resume_stages":resume,"final_state":final}
def worker(wid):
 lock=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=lock:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":lock,"cells":[one(n,c) for n in SIZES for c in CUTS]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"proposal_revision_recovery_v1_1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"cuts":CUTS},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
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
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"proposal_revision_recovery_v1_1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
