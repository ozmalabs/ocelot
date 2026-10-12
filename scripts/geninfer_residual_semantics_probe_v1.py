#!/usr/bin/env python3
"""Repeat GenInfer field reads to audit generator/residual decomposition."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_geninfer_residual_semantics_v1_20260926.json"
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],"swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
POINTS=[(0,0),(1,0),(2,0),(0,2)];PREDS=["p0","p1","p2","p3"]
CONDS=["positive","point_corrupt_p1"];FIELDS=["explained","matrix","residual_dims","transforms","dims","checked"];REPS=5
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 samples=[]
 for family,matrix in MAPS.items():
  a,b,c,d=matrix;base=[[p,r,q,"red"] for p,(r,q) in zip(PREDS,POINTS)]
  target=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,POINTS)]
  goals={"positive":target,"point_corrupt_p1":[[p,r+1 if p=="p1" else r,q,v] for p,r,q,v in target]}
  for condition,goal in goals.items():
   sub=_native.Substrate();sub.add_node("ShapeSignature",{"name":family,"signature":json.dumps(base),"kind":"faculty","faculty":family,"dim_types":["pred","coord:r","coord:c","val"]})
   term={"type":"GenInfer","goal":{"type":"Lit","value":goal},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
   for repetition in range(1,REPS+1):
    observation={field:sub.evaluate({**term,"field":field},{}) for field in FIELDS}
    samples.append({"family":family,"condition":condition,"repetition":repetition,"base_relation_count":len(base),"goal_relation_count":len(goal),"observation":observation})
 native=Path(_native.__file__).resolve();paths=["scripts/geninfer_residual_semantics_probe_v1.py","scripts/analyze_substrate_geninfer_residual_semantics_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_RESIDUAL_SEMANTICS_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-geninfer-residual-semantics-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"maps":MAPS,"points":[list(p) for p in POINTS],"predicates":PREDS,"conditions":CONDS,"fields":FIELDS,"repetitions":REPS,"timing":"none; field-semantics audit"},"samples":samples,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native),"native_extension_sha256":sha(native)},"claim_boundary":"Four small 2-D integer-linear maps, one source motif, one coordinate perturbation; direct output decomposition only."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples)},indent=2))
if __name__=="__main__":main()
