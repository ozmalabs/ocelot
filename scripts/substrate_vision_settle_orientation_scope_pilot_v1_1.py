#!/usr/bin/env python3
"""Paired orientation-response pilot for global/root-scoped settle rules."""
from __future__ import annotations
import copy,hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SEED_DOC=ROOT/"seeds/vision_settle.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_ORIENTATION_SCOPE_PILOT_V1_1_AMENDMENT_20260925.md"
OUT=ROOT/"evaluation/reports/substrate_vision_settle_orientation_scope_pilot_v1_1_20260925.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scoped_doc(doc):
 m=copy.deepcopy(doc); found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get("type")=="NodesOfType" and x.get("node_type")=="SUnit":
    found+=1;return {"type":"Neighbours","node":{"type":"Var","name":"r"},"edge_type":"has_sunit","any_type":False}
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 for r in m.get("rules",[]):
  if r.get("name")=="st_settle":
   r["name"]="st_settle_root_scoped_benchmark";r["where"]=visit(r.get("where"));r["effects"]=visit(r.get("effects"))
 if found!=2:raise RuntimeError(f"expected 2 sources, found {found}")
 return m
def arm(seed,n_side,is_scoped,doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as orig_manifest
 from scripts.settle_lib import build_sheet
 from domains.onoff_world import set_params
 from domains.lateral_world import set_lat_params
 import domains.complex_cells as complex_cells
 if is_scoped:
  replacement=scoped_doc(doc)
  def manifest_for(sid):return replacement if sid=="vision_settle" else orig_manifest(sid)
  boot_core.manifest_for=manifest_for
 try:w,units,n_edges=build_sheet(seed=seed,n_side=n_side,channels="lateral",connectivity=8,settle=1.0,bubble=0.0)
 finally:
  if is_scoped:boot_core.manifest_for=orig_manifest
 s=w.s;root=w.retina
 owned=set(s._inner.neighbours(root,"has_sunit"))
 if owned!=set(units):raise RuntimeError("Retina ownership does not equal built SUnit set")
 set_params(w,oo_eta=0.0,frozen=1.0,homeo=0.0)
 for p in s.nodes("LatParams"):s.set_attr(p,"frozen",1.0)
 # The default adapter tick is checked against full-rescan closure on a matched first frame.
 frame=complex_cells.binarize(complex_cells.grating((w.h,w.w),0.0,0.0,4.0))
 st=float(s.node(root)["attrs"].get("step",0.0))+10.0;s.set_attr(root,"step",st)
 for (r,c),node in w.cells.items():
  on=(r<frame.shape[0] and c<frame.shape[1] and frame[r,c]>0.5)
  s.set_attr(node,"bursting",1.0 if on else 0.0);s.set_attr(node,"last_burst",st if on else -999.0);s.set_attr(node,"state","rested")
 for node in s.nodes("Unit"):s.set_attr(node,"bursting",0.0)
 tick_progress=int(s._inner.tick(200000,False))
 first_report=s._inner.run_rules_report(200000,True)
 first_frame={"default_tick_progress":tick_progress,"full_rescan_report":first_report,
              "full_rescan_max_act":max(float(s.node(u)["attrs"].get("act",0.0)) for u in units),
              "full_rescan_max_rate":max(float(s.node(u)["attrs"].get("rate",0.0)) for u in units)}
 reports=[]
 original_present=complex_cells.present
 def fullscan_present(world,frame,*,dstep=10.0):
  ss=world.s;step=float(ss.node(world.retina)["attrs"].get("step",0.0))+dstep;ss.set_attr(world.retina,"step",step)
  for (rr,cc),node in world.cells.items():
   on=(rr<frame.shape[0] and cc<frame.shape[1] and frame[rr,cc]>0.5)
   ss.set_attr(node,"bursting",1.0 if on else 0.0);ss.set_attr(node,"last_burst",step if on else -999.0);ss.set_attr(node,"state","rested")
  for node in ss.nodes("Unit"):ss.set_attr(node,"bursting",0.0)
  rep=ss._inner.run_rules_report(200000,True);reports.append(rep);return step
 complex_cells.present=fullscan_present
 try:
  start=time.perf_counter();stats=complex_cells.cell_stats(w,units,key="rate",period=4.0,K=4);elapsed=time.perf_counter()-start
 finally:complex_cells.present=original_present
 tuning=np.asarray(stats["tuning"],float);osi=np.asarray(stats["osi"],float)
 return {"seed":seed,"n_side":n_side,"units":len(units),"edges":n_edges,"variant":"root_scoped" if is_scoped else "global","root_type":"Retina","root_membership_count":len(owned),"phase_samples":4,"orientation_count":int(tuning.shape[1]),"elapsed_seconds_diagnostic":elapsed,"probe_closure_reports":reports,"first_frame_path_diagnostic":first_frame,"tuning":tuning.tolist(),"osi_per_unit":osi.tolist(),"mean_osi":float(np.mean(osi)),"alive_per_unit":(tuning>1e-9).sum(axis=1).astype(int).tolist()}
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate_rs import _native
 doc=json.loads(SEED_DOC.read_text());pairs=[]
 for n,seed in ((3,20260925),(4,20260926)):
  pairs.append({"n_side":n,"seed":seed,"arms":[arm(seed,n,False,doc),arm(seed,n,True,doc)]})
 checks={"two_registered_pairs":len(pairs)==2,"root_membership":all(a["root_membership_count"]==a["units"] for p in pairs for a in p["arms"]),"tuning_parity":all(np.max(np.abs(np.array(p["arms"][0]["tuning"])-np.array(p["arms"][1]["tuning"])))<=1e-10 for p in pairs),"osi_parity":all(abs(p["arms"][0]["mean_osi"]-p["arms"][1]["mean_osi"])<=1e-10 for p in pairs)}
 result={"run_id":"vision-settle-orientation-scope-pilot-20260925","pairs":pairs,"checks":checks,"pass":all(checks.values()),"provenance":{"python":sys.version,"platform":platform.platform(),"runner_sha256":sha(Path(__file__)),"protocol_sha256":sha(PROTOCOL),"seed_sha256":sha(SEED_DOC),"native_extension_path":str(Path(_native.__file__).resolve()),"native_extension_sha256":sha(Path(_native.__file__).resolve()),"engine_provenance":engine_provenance(),"source_sha256":{n:sha(ROOT/"runners/dsl/src"/n) for n in ("rewrite.rs","substrate.rs","term.rs","py.rs")}}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"pass":result["pass"],"pairs":[{"n_side":p["n_side"],"seed":p["seed"],"mean_osi":[a["mean_osi"] for a in p["arms"]],"seconds":[a["elapsed_seconds_diagnostic"] for a in p["arms"]]} for p in pairs]},indent=2))
 if not result["pass"]:raise SystemExit("orientation scope pilot did not meet preregistered parity")
if __name__=="__main__":main()
