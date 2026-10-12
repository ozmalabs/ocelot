#!/usr/bin/env python3
"""Compare nested and staged tie-aware proposal resolvers under scale audit."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_RESOLVER_MATERIALIZATION_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_conflict_proposal_resolver_materialization_v1.py";LOCK=ROOT/"evaluation/substrate_capability/conflict_proposal_resolver_materialization_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/conflict_proposal_resolver_materialization_v1_20260928.json";SIZES=(2,4,8,16,32,64)
SOURCES=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_conflict_proposal_resolver_materialization_v1.py","scripts/analyze_conflict_proposal_resolver_materialization_v1.py","docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_RESOLVER_MATERIALIZATION_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return v,dt,{k:v for k,v in m.items() if v}
def run_case(n,dist):
 from substrate_rs import Substrate,Term
 sub=Substrate();g=sub._inner;t=g.add_node("ConflictTarget",{});s=g.add_node("ConflictTrigger",{});g.add_edge_unchecked(s,"trigger",t,{})
 scores=list(range(n))
 if dist=="tied_max":scores[-2:]=[n+10,n+10]
 for i,score in enumerate(scores):g.add_rule({"name":f"propose_{i}","match":[["s","trigger","t"]],"where":None,"effects":[["add_node_if_absent",f"proposal_{i}","ConflictProposal",{"label":f"p{i:03d}","score":score}],["add_edge","t","proposes",f"proposal_{i}",{}]]})
 gen,gn,gm=audit(lambda:g.run_rules_report(100000,True));repeat,rn,rm=audit(lambda:g.run_rules_report(100000,True))
 V=lambda name:Term("Var",name=name);A=lambda name,key:Term("Attr",node=V(name),key=key);source=Term("Neighbours",node=V("t"),edge_type="proposes");maxv=Term("MaxOver",source=source,var_name="q",value=A("q","score"))
 g.add_rule({"name":"cache_max","match":[["s","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","max_score",{"__term__":maxv.to_dict()}]]})
 g.add_rule({"name":"mark_top","match":[["t","proposes","p"]],"where":Term("Eq",a=A("p","score"),b=A("t","max_score")).to_dict(),"effects":[["set_attr_if_different","p","is_top",True]]})
 top=Term("Filter",source=source,var_name="q",predicate=Term("Eq",a=A("q","is_top"),b=Term("Lit",value=True)));count=Term("Count",source=top)
 g.add_rule({"name":"cache_top_count","match":[["s","trigger","t"]],"where":None,"effects":[["set_attr_if_different","t","top_count",{"__term__":count.to_dict()}]]})
 g.add_rule({"name":"mark_ambiguous","match":[["s","trigger","t"]],"where":Term("Gt",a=A("t","top_count"),b=Term("Lit",value=1)).to_dict(),"effects":[["set_attr_if_different","t","ambiguous",True]]})
 choose=Term("And",items=[Term("Eq",a=A("t","top_count"),b=Term("Lit",value=1)),Term("Eq",a=A("p","is_top"),b=Term("Lit",value=True))])
 g.add_rule({"name":"select_unique_max","match":[["t","proposes","p"]],"where":choose.to_dict(),"effects":[["set_attr_if_different","t","selected",{"__term__":A("p","label").to_dict()}]]})
 res,rsv,rmx=audit(lambda:g.run_rules_report(100000,True));graph=g.graph_to_dict();attrs=next(x.get("attrs",{}) for x in graph["nodes"] if int(x["id"])==t.value);labels=sorted(x.get("attrs",{}).get("label") for x in graph["nodes"] if x["type"]=="ConflictProposal")
 return {"n":n,"distribution":dist,"generation":{"report":dict(gen),"elapsed_ns":gn,"metrics":gm},"repeat":{"report":dict(repeat),"elapsed_ns":rn,"metrics":rm},"resolution":{"report":dict(res),"elapsed_ns":rsv,"metrics":rmx,"selected":attrs.get("selected"),"ambiguous":attrs.get("ambiguous"),"max_score":attrs.get("max_score"),"top_count":attrs.get("top_count")},"proposal_labels":labels,"proposal_edge_count":sum(e["type"]=="proposes" and int(e["src"])==t.value for e in graph["edges"])}
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":[run_case(n,d) for n in SIZES for d in ("unique_max","tied_max")]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");a=ap.parse_args()
 if a.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"conflict_proposal_resolver_materialization_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if a.worker is not None:print(json.dumps(worker(a.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit("refusing to overwrite raw capture")
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"conflict_proposal_resolver_materialization_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
