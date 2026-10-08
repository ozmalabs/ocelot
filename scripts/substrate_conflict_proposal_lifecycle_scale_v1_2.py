#!/usr/bin/env python3
"""Measure graph-native ambiguity-aware proposal resolution through N=64."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_LIFECYCLE_SCALE_V1_2_PREREG_20260928.md"
ANALYZER=ROOT/"scripts/analyze_conflict_proposal_lifecycle_scale_v1_2.py"
LOCK=ROOT/"evaluation/substrate_capability/conflict_proposal_lifecycle_scale_v1_2_lock_20260928.json"
RAW=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_2_20260928.json"
SIZES=(2,4,8,16,32,64)
SOURCE_PATHS=("runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_conflict_proposal_lifecycle_scale_v1_2.py","scripts/analyze_conflict_proposal_lifecycle_scale_v1_2.py","docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_LIFECYCLE_SCALE_V1_2_PREREG_20260928.md")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{n:sha(ROOT/n) for n in SOURCE_PATHS},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audited(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();out=fn();elapsed=time.perf_counter_ns()-t;metrics=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False)
 return out,elapsed,{k:v for k,v in metrics.items() if v}
def one(n,dist):
 from substrate_rs import Substrate,Term
 sub=Substrate();g=sub._inner;t=g.add_node("ConflictTarget",{});s=g.add_node("ConflictTrigger",{});g.add_edge_unchecked(s,"trigger",t,{})
 scores=list(range(n))
 if dist=="tied_max": scores[-2:]=[n+10,n+10]
 for i,score in enumerate(scores):
  g.add_rule({"name":f"propose_{i}","match":[["s","trigger","t"]],"where":None,"effects":[["add_node_if_absent",f"proposal_{i}","ConflictProposal",{"label":f"p{i:03d}","score":score}],["add_edge","t","proposes",f"proposal_{i}",{}]]})
 generation,gns,gm=audited(lambda:g.run_rules_report(100000,True));repeat,rns,rm=audited(lambda:g.run_rules_report(100000,True))
 source=Term("Neighbours",node=Term("Var",name="t"),edge_type="proposes")
 maxv=Term("MaxOver",source=source,var_name="q",value=Term("Attr",node=Term("Var",name="q"),key="score"))
 top_filter=Term("Filter",source=source,var_name="q",predicate=Term("Eq",a=Term("Attr",node=Term("Var",name="q"),key="score"),b=maxv))
 top_count=Term("Count",source=top_filter)
 g.add_rule({"name":"mark_ambiguous","match":[["s","trigger","t"]],"where":Term("Gt",a=top_count,b=Term("Lit",value=1)).to_dict(),"effects":[["set_attr_if_different","t","ambiguous",True]]})
 unique=Term("Eq",a=top_count,b=Term("Lit",value=1));is_max=Term("Eq",a=Term("Attr",node=Term("Var",name="p"),key="score"),b=maxv)
 where=Term("And",items=[unique,is_max])
 g.add_rule({"name":"select_unique_max","match":[["t","proposes","p"]],"where":where.to_dict(),"effects":[["set_attr_if_different","t","selected",{"__term__":Term("Attr",node=Term("Var",name="p"),key="label").to_dict()}]]})
 resolution,rsv,rmx=audited(lambda:g.run_rules_report(100000,True));graph=g.graph_to_dict();attrs=next(x.get("attrs",{}) for x in graph["nodes"] if int(x["id"])==t.value)
 labels=sorted(x.get("attrs",{}).get("label") for x in graph["nodes"] if x["type"]=="ConflictProposal")
 edges=sum(e["type"]=="proposes" and int(e["src"])==t.value for e in graph["edges"])
 return {"n":n,"distribution":dist,"generation":{"report":dict(generation),"elapsed_ns":gns,"metrics":gm},"idempotent_resettle":{"report":dict(repeat),"elapsed_ns":rns,"metrics":rm},"resolution":{"report":dict(resolution),"elapsed_ns":rsv,"metrics":rmx,"selected":attrs.get("selected"),"ambiguous":attrs.get("ambiguous")},"proposal_labels":labels,"proposal_edge_count":edges,"graph_node_count":len(graph["nodes"]),"graph_edge_count":len(graph["edges"])}
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked: raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":[one(n,d) for n in SIZES for d in ("unique_max","tied_max")]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists(): raise SystemExit(f"refusing to overwrite {LOCK}")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"conflict_proposal_lifecycle_scale_v1_2_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"distributions":["unique_max","tied_max"]},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if args.worker is not None: print(json.dumps(worker(args.worker),sort_keys=True));return
 if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]: raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode: raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 raw={"run_id":"conflict_proposal_lifecycle_scale_v1_2_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs,"claim_boundary":"Three workers; N=2..64; unique and tied maxima. Counts are native scale-audit operations for this authored graph-native resolver only."}
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":3,"cells_per_worker":12,"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__": main()
