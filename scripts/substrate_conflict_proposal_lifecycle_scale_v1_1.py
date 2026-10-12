#!/usr/bin/env python3
"""Scale proposal creation, deduplication, and MaxOver resolution to N=64."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_LIFECYCLE_SCALE_V1_1_PREREG_20260928.md"
ANALYZER=ROOT/"scripts/analyze_conflict_proposal_lifecycle_scale_v1_1.py"
LOCK=ROOT/"evaluation/substrate_capability/conflict_proposal_lifecycle_scale_v1_1_lock_20260928.json"
RAW=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_1_20260928.json"
SIZES=(2,4,8,16,32,64)
SOURCE_PATHS=(
 "runners/dsl/src/term.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs",
 "runners/dsl/python/substrate_rs/__init__.py",
 "scripts/substrate_conflict_proposal_lifecycle_scale_v1_1.py",
 "scripts/analyze_conflict_proposal_lifecycle_scale_v1_1.py",
 "docs/research/engine_substrate/SUBSTRATE_CONFLICT_PROPOSAL_LIFECYCLE_SCALE_V1_1_PREREG_20260928.md")


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()


def lock_inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
         "source_sha256":{n:sha(ROOT/n) for n in SOURCE_PATHS},
         "native_extension_path":str(ext),"native_extension_sha256":sha(ext),
         "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}


def audit_call(native,fn):
 audit=native.Substrate
 audit.scale_audit_reset();audit.scale_audit_set_enabled(True)
 start=time.perf_counter_ns(); result=fn(); elapsed=time.perf_counter_ns()-start
 metrics=dict(audit.scale_audit_snapshot());audit.scale_audit_set_enabled(False)
 return result,elapsed,{k:v for k,v in metrics.items() if v}


def one_case(n:int,distribution:str)->dict:
 from substrate_rs import Lit,Substrate,Term,_native
 sub=Substrate();inner=sub._inner
 target=inner.add_node("ConflictTarget",{"name":"target"})
 src=inner.add_node("ConflictTrigger",{});inner.add_edge_unchecked(src,"trigger",target,{})
 scores=list(range(n))
 if distribution=="tied_max":scores[-2:]=[n+10,n+10]
 labels=[f"p{i:03d}" for i in range(n)]
 for i,(label,score) in enumerate(zip(labels,scores)):
  inner.add_rule({"name":f"propose_{label}","match":[["s","trigger","t"]],"where":None,
                  "effects":[["add_node_if_absent",f"proposal_{i}","ConflictProposal",{"label":label,"score":score}],
                             ["add_edge","t","proposes",f"proposal_{i}",{}]]})

 generation,gen_ns,gen_metrics=audit_call(_native,lambda:inner.run_rules_report(100_000,True))
 repeat,repeat_ns,repeat_metrics=audit_call(_native,lambda:inner.run_rules_report(100_000,True))
 qmax=Term("MaxOver",source=Term("Neighbours",node=Term("Var",name="t"),edge_type="proposes"),
            var_name="q",value=Term("Attr",node=Term("Var",name="q"),key="score"))
 where=Term("Eq",a=Term("Attr",node=Term("Var",name="p"),key="score"),b=qmax).to_dict()
 inner.add_rule({"name":"select_max_score","match":[["t","proposes","p"]],"where":where,
                 "effects":[["set_attr_if_different","t","selected",{"__term__":{"type":"Attr","node":{"type":"Var","name":"p"},"key":"label"}}]]})
 resolution,res_ns,res_metrics=audit_call(_native,lambda:inner.run_rules_report(100_000,True))
 graph=inner.graph_to_dict();attrs={int(x["id"]):x.get("attrs",{}) for x in graph.get("nodes",[])}
 proposals=sorted([x.get("attrs",{}).get("label") for x in graph["nodes"] if x["type"]=="ConflictProposal"])
 edge_count=sum(e["type"]=="proposes" and int(e["src"])==target.value for e in graph["edges"])
 return {"n":n,"distribution":distribution,"scores":scores,
         "generation":{"report":dict(generation),"elapsed_ns":gen_ns,"metrics":gen_metrics},
         "idempotent_resettle":{"report":dict(repeat),"elapsed_ns":repeat_ns,"metrics":repeat_metrics},
         "resolution":{"report":dict(resolution),"elapsed_ns":res_ns,"metrics":res_metrics,
                       "selected":attrs.get(target.value,{}).get("selected")},
         "proposal_labels":proposals,"proposal_edge_count":edge_count,
         "graph_node_count":len(graph["nodes"]),"graph_edge_count":len(graph["edges"])}


def worker(wid:int)->dict:
 started=lock_inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=started:raise RuntimeError("source/native lock mismatch")
 cells=[one_case(n,d) for n in SIZES for d in ("unique_max","tied_max")]
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,
         "started_inputs":started,"cells":cells}


def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");args=ap.parse_args()
 if args.write_lock:
  if LOCK.exists():raise SystemExit(f"refusing to overwrite {LOCK}")
  LOCK.parent.mkdir(parents=True,exist_ok=True)
  LOCK.write_text(json.dumps({"lock_id":"conflict_proposal_lifecycle_scale_v1_1_20260928","locked_inputs":lock_inputs(),"workers":3,"sizes":SIZES,"distributions":["unique_max","tied_max"]},indent=2,sort_keys=True)+"\n")
  print(str(LOCK.relative_to(ROOT)));return
 if args.worker is not None:print(json.dumps(worker(args.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit(f"refusing to overwrite {RAW}")
 lock=json.loads(LOCK.read_text())
 if lock_inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  argv=[sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)];cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2500:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 raw={"run_id":"conflict_proposal_lifecycle_scale_v1_1_20260928","locked_inputs":lock["locked_inputs"],
      "protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs,
      "claim_boundary":"Three workers, N=2..64, two score distributions. Counts cover native scale-audit metrics for this explicit candidate-generation and MaxOver resolver fixture; not general induction or asymptotic guarantees."}
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x",encoding="utf-8") as f:f.write(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))


if __name__=="__main__":main()
