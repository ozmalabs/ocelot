#!/usr/bin/env python3
"""Measure consumer gating against staged and committed proposal revisions."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_COMMITTED_RESULT_CONSUMER_GATE_V1_2_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_committed_result_consumer_gate_v1_2.py";LOCK=ROOT/"evaluation/substrate_capability/committed_result_consumer_gate_v1_2_lock_20260928.json";RAW=ROOT/"evaluation/reports/committed_result_consumer_gate_v1_2_20260928.json";SIZES=(2,8,32,64);DISTS=("unique_max","tied_max")
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_committed_result_consumer_gate_v1_2.py","scripts/analyze_substrate_committed_result_consumer_gate_v1_2.py","docs/research/engine_substrate/SUBSTRATE_COMMITTED_RESULT_CONSUMER_GATE_V1_2_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def cell(n,dist):
 from substrate_rs import Substrate,Term
 s=Substrate();g=s._inner;attrs={"resolved_revision":0,"max_revision":0,"count_revision":0,"decision_revision":0,"selected_label":"stale"};t=g.add_node("ConflictTarget",attrs);a=g.add_node("ResolverAnchor",{});scores=list(range(n))
 if dist=="tied_max":scores[-2:]=[n+5,n+5]
 for i,score in enumerate(scores):p=g.add_node("ConflictProposal",{"label":f"p{i:03d}","score":score});g.add_edge_unchecked(t,"proposes",p,{})
 tops=[i for i,v in enumerate(scores) if v==max(scores)];expected="" if len(tops)>1 else f"p{tops[0]:03d}"
 r=g.add_node("ResolverRevision",{"revision":1});g.add_edge_unchecked(a,"revision",r,{});g.add_edge_unchecked(r,"for_target",t,{})
 V=lambda x:Term("Var",name=x);A=lambda x,k:Term("Attr",node=V(x),key=k);base=[["a","revision","r"],["r","for_target","t"]];rev=A("r","revision")
 all_stamps=Term("And",items=[Term("Eq",a=A("t","max_revision"),b=rev),Term("Eq",a=A("t","count_revision"),b=rev),Term("Eq",a=A("t","decision_revision"),b=rev)])
 commit_where=all_stamps
 g.add_rule({"name":"consume_committed_only","match":base,"where":Term("And",items=[all_stamps,Term("Eq",a=A("t","resolved_revision"),b=rev)]).to_dict(),"effects":[["set_attr_if_different","t","consumed_label",{"__term__":A("t","selected_label").to_dict()}]]})
 g.add_rule({"name":"commit_only_complete_stages","match":base+[["r","commit","t"]],"where":commit_where.to_dict(),"effects":[["set_attr_if_different","t","resolved_revision",{"__term__":rev.to_dict()}]]})
 def projection():
  node=next(z for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value);return node["attrs"]
 g.set_attr(t,"max_revision",1);r1,ns1,m1=audit(lambda:g.run_rules_report(1000,True));state1=projection()
 g.set_attr(t,"count_revision",1);g.set_attr(t,"decision_revision",1);g.set_attr(t,"selected_label",expected);r2,ns2,m2=audit(lambda:g.run_rules_report(1000,True));state2=projection()
 g.add_edge_unchecked(r,"commit",t,{});r3,ns3,m3=audit(lambda:g.run_rules_report(1000,True));state3=projection()
 return {"n":n,"distribution":dist,"expected_consumed":expected,"checkpoints":[{"name":"one_stage_incomplete","report":dict(r1),"elapsed_ns":ns1,"metrics":m1,"attrs":state1},{"name":"stages_complete_uncommitted","report":dict(r2),"elapsed_ns":ns2,"metrics":m2,"attrs":state2},{"name":"committed","report":dict(r3),"elapsed_ns":ns3,"metrics":m3,"attrs":state3}]}
def worker(wid):
 lock=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=lock:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":lock,"cells":[cell(n,d) for n in SIZES for d in DISTS]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"committed_result_consumer_gate_v1_2_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"distributions":DISTS},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
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
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"committed_result_consumer_gate_v1_2_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
