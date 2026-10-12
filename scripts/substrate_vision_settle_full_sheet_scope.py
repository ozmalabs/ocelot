#!/usr/bin/env python3
"""Paired full-build sheet test of global versus root-scoped competition."""
from __future__ import annotations
import copy, hashlib, json, platform, sys, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
SEED_DOC=ROOT/"seeds/vision_settle.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_FULL_SHEET_SCOPING_V1_2_AMENDMENT_20260925.md"
OUT=ROOT/"evaluation/reports/substrate_vision_settle_full_sheet_scope_v1_2_20260925.json"
CAP=10_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def root_source(): return {"type":"Neighbours","node":{"type":"Var","name":"r"},"edge_type":"has_sunit","any_type":False}
def clone_manifest(manifest):
 m=copy.deepcopy(manifest); found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get("type")=="NodesOfType" and x.get("node_type")=="SUnit": found+=1; return root_source()
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list): return [visit(v) for v in x]
  return x
 for rule in m.get("rules",[]):
  if rule.get("name")=="st_settle": rule["name"]="st_settle_root_scoped_benchmark"; rule["where"]=visit(rule.get("where")); rule["effects"]=visit(rule.get("effects"))
 if found!=2: raise RuntimeError(f"expected two global SUnit sources in st_settle, replaced {found}")
 return m

def build_arm(seed,n_side,scoped,doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original_manifest_for
 from scripts.settle_lib import build_sheet
 if scoped:
  scoped_doc=clone_manifest(doc)
  def wrapped(seed_id): return scoped_doc if seed_id=="vision_settle" else original_manifest_for(seed_id)
  boot_core.manifest_for=wrapped
 try: w,units,n_edges=build_sheet(seed=seed,n_side=n_side,channels="degenerate",connectivity=8,settle=1.0,bubble=0.0)
 finally:
  if scoped: boot_core.manifest_for=original_manifest_for
 inner=w.s._inner; root=w.retina
 roots=inner.nodes("Retina")
 if roots!=[root]: raise RuntimeError(f"expected one Retina root {root}, got {roots}")
 owned=set(inner.neighbours(root,"has_sunit"))
 if set(units)!=owned: raise RuntimeError(f"root owns {len(owned)} SUnits, builder returned {len(units)}")
 rules=inner.export_rules()
 settle_name="st_settle_root_scoped_benchmark" if scoped else "st_settle"
 indices={r["name"]:i for i,r in enumerate(rules) if r["name"] in ("st_settle", "st_settle_root_scoped_benchmark", "st_commit")}
 if settle_name not in indices or "st_commit" not in indices: raise RuntimeError(f"settle rule indices missing: {indices}")
 keep={indices[settle_name],indices["st_commit"]}
 removed=sum(bool(inner.remove_rule(i)) for i in range(len(rules)) if i not in keep)
 rng=np.random.Generator(np.random.PCG64(seed+9000)); aff=rng.random(len(units),dtype=np.float64)
 step=float(inner.node(root)["attrs"].get("step",0.0))
 for u,a in zip(units,aff):
  inner.set_attr(u,"aff",float(a)); inner.set_attr(u,"aff_step",step); inner.set_attr(u,"act",0.0); inner.set_attr(u,"act_next",-1.0)
 start=time.perf_counter(); progress=inner.run_rules(CAP)
 elapsed=time.perf_counter()-start
 final=np.array([float(inner.node(u)["attrs"].get("act",0.0)) for u in units])
 aff_live=np.array([float(inner.node(u)["attrs"].get("aff",0.0)) for u in units])
 pred=[]
 for u,a in zip(units,aff_live):
  ns=inner.neighbours(u,"sunit_neighbour")
  local=float(np.mean([float(inner.node(v)["attrs"].get("act",0.0)) for v in ns])) if ns else 0.0
  pred.append(max(float(a)+local-float(np.mean(final)),0.0))
 residual=float(np.max(np.abs(np.asarray(pred)-final)))
 return {"seed":seed,"n_side":n_side,"n_units":len(units),"n_edges":n_edges,"variant":"root_scoped" if scoped else "global","settle_rule":settle_name,"commit_rule":"st_commit","root_type":"Retina","root_membership_count":len(owned),"removed_other_rules":removed,"progress_applications":int(progress),"engine_fixpoint_before_cap":int(progress)<CAP,"equation_max_residual":residual,"wall_seconds_diagnostic":elapsed,"act":final.tolist(),"aff":aff_live.tolist(),"act_sha256":hashlib.sha256(final.tobytes()).hexdigest()}

def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 import substrate_rs as sr
 from substrate_rs import _native
 doc=json.loads(SEED_DOC.read_text()); cases=[]
 for n_side,seed in ((3,11),(3,29),(4,11),(4,29)):
  cases.append({"n_side":n_side,"seed":seed,"arms":[build_arm(seed,n_side,False,doc),build_arm(seed,n_side,True,doc)]})
 result={"run_id":"vision-settle-full-sheet-scope-fidelity-20260925","cases":cases,"checks":{
  "all_cases_numerically_converged":all(a["equation_max_residual"]<=1e-12 for c in cases for a in c["arms"]),
  "paired_shape_equal":all(c["arms"][0]["n_units"]==c["arms"][1]["n_units"] and c["arms"][0]["n_edges"]==c["arms"][1]["n_edges"] for c in cases),
  "single_root_membership":all(a["root_membership_count"]==a["n_units"] for c in cases for a in c["arms"]),
  "paired_terminal_equal":all(c["arms"][0]["act"]==c["arms"][1]["act"] for c in cases),
  "paired_progress_equal":all(c["arms"][0]["progress_applications"]==c["arms"][1]["progress_applications"] for c in cases)},
  "provenance":{"python":sys.version,"platform":platform.platform(),"runner_sha256":sha(Path(__file__)),"protocol_sha256":sha(PROTOCOL),"seed_sha256":sha(SEED_DOC),"native_extension_path":str(Path(_native.__file__).resolve()),"native_extension_sha256":sha(Path(_native.__file__).resolve()),"engine_provenance":engine_provenance(),"source_sha256":{n:sha(ROOT/"runners/dsl/src"/n) for n in ("rewrite.rs","substrate.rs","term.rs","py.rs")}}}
 result["pass"]=all(result["checks"].values())
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":result["checks"],"pass":result["pass"],"cases":[{"n_side":c["n_side"],"seed":c["seed"],"progress":[a["progress_applications"] for a in c["arms"]]} for c in cases]},indent=2))
 if not result["pass"]: raise SystemExit("full sheet scope fidelity gate failed")
if __name__=="__main__": main()
