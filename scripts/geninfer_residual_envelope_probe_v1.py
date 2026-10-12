#!/usr/bin/env python3
"""Characterize supported GenInfer residual decompositions and budget gates."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_geninfer_residual_envelope_v1_20260926.json"
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],"swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
POINTS=[(0,0),(1,0),(2,0),(0,2)];PREDS=["p0","p1","p2","p3"]
FIELDS=["explained","matrix","residual_dims","transforms","dims","checked"];REPS=5
UNIQUE_CONDITIONS=["positive","global_shift_r","two_slot_shifts_max2","two_slot_shifts_max1","global_substitution"]
REPEATED_CONDITIONS=["repeated_predicate_nonuniform_numeric","repeated_predicate_symbolic_conflict"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def construct(matrix,condition):
 a,b,c,d=matrix;base=[[p,r,q,"red"] for p,(r,q) in zip(PREDS,POINTS)]
 goal=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,POINTS)];max_dims=2
 if condition in ("global_shift_r","two_slot_shifts_max2","two_slot_shifts_max1"):
  goal=[[p,r+1,c+(2 if condition.startswith("two_slot") else 0),v] for p,r,c,v in goal]
 if condition=="two_slot_shifts_max1":max_dims=1
 if condition=="global_substitution":goal=[[p,r,c,"blue"] for p,r,c,v in goal]
 return base,goal,max_dims
def repeated_construct(condition):
 m=MAPS["asymmetric_scale_shear"];a,b,c,d=m;preds=["p0","p0","p1","p1"]
 base=[[p,r,q,"red"] for p,(r,q) in zip(preds,POINTS)]
 goal=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(preds,POINTS)]
 if condition=="repeated_predicate_nonuniform_numeric":
  goal[0][1]+=1;goal[1][1]+=2
 else:
  goal[0][3]="blue";goal[1][3]="green"
 return base,goal,2
def main():
 samples=[]
 cases=[(fam,cond,mat,False) for fam,mat in MAPS.items() for cond in UNIQUE_CONDITIONS]
 cases += [("asymmetric_scale_shear",cond,MAPS["asymmetric_scale_shear"],True) for cond in REPEATED_CONDITIONS]
 for family,condition,matrix,repeated in cases:
  base,goal,max_dims=repeated_construct(condition) if repeated else construct(matrix,condition)
  sub=_native.Substrate();sub.add_node("ShapeSignature",{"name":family,"signature":json.dumps(base),"kind":"faculty","faculty":family,"dim_types":["pred","coord:r","coord:c","val"]})
  term={"type":"GenInfer","goal":{"type":"Lit","value":goal},"codebook_type":"ShapeSignature","max_dims":max_dims,"field":"explained"}
  for repetition in range(1,REPS+1):
   observation={field:sub.evaluate({**term,"field":field},{}) for field in FIELDS}
   samples.append({"family":family,"condition":condition,"repetition":repetition,"max_dims":max_dims,"base_relation_count":len(base),"goal_relation_count":len(goal),"base":base,"goal":goal,"observation":observation})
 native=Path(_native.__file__).resolve();paths=["scripts/geninfer_residual_envelope_probe_v1.py","scripts/analyze_substrate_geninfer_residual_envelope_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_RESIDUAL_ENVELOPE_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-geninfer-residual-envelope-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"maps":MAPS,"points":[list(p) for p in POINTS],"unique_predicates":PREDS,"unique_conditions":UNIQUE_CONDITIONS,"repeated_conditions":REPEATED_CONDITIONS,"fields":FIELDS,"repetitions":REPS,"timing":"none; output semantics only"},"samples":samples,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native),"native_extension_sha256":sha(native)},"claim_boundary":"Small 2-D integer-linear evaluator residual envelope; no natural-noise or end-to-end learning claim."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples)},indent=2))
if __name__=="__main__":main()
