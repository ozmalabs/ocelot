#!/usr/bin/env python3
"""Paired GenInfer probe with and without stable relation identity fields."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json"
REFERENCE=ROOT/"evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_20260926.json"
MATRIX=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]};PREDS=["p0","p0","p1","p1"];CONDITIONS=["positive","corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"];FIELDS=["explained","matrix","residual_dims","transforms","dims","checked"];REPS=5
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 samples=[];a,b,c,d=MATRIX
 for layout,points in LAYOUTS.items():
  for mode in ("no_identity","stable_identity"):
   base=[]
   for i,(pred,(r,q)) in enumerate(zip(PREDS,points)):
    base.append([pred,r,q,"red"] if mode=="no_identity" else [pred,f"rel{i}",r,q,"red"])
   for condition in CONDITIONS:
    delta=0 if condition=="positive" else int(condition.rsplit("_",1)[1]);goal=[]
    for i,(pred,(r,q)) in enumerate(zip(PREDS,points)):
     x,y=a*r+b*q,c*r+d*q
     if i==0:x+=delta
     goal.append([pred,x,y,"red"] if mode=="no_identity" else [pred,f"rel{i}",x,y,"red"])
    dim_types=["pred","coord:r","coord:c","val"] if mode=="no_identity" else ["pred","id","coord:r","coord:c","val"]
    sub=_native.Substrate();sub.add_node("ShapeSignature",{"name":layout,"signature":json.dumps(base),"kind":"faculty","faculty":layout,"dim_types":dim_types})
    term={"type":"GenInfer","goal":{"type":"Lit","value":goal},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
    for rep in range(1,REPS+1):
     obs={field:sub.evaluate({**term,"field":field},{}) for field in FIELDS}
     samples.append({"layout":layout,"mode":mode,"condition":condition,"repetition":rep,"base":base,"goal":goal,"dim_types":dim_types,"observation":obs})
 native=Path(_native.__file__).resolve();paths=["scripts/geninfer_relation_identity_ablation_probe_v1.py","scripts/analyze_substrate_geninfer_relation_identity_ablation_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_RELATION_IDENTITY_ABLATION_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-geninfer-relation-identity-ablation-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"matrix":MATRIX,"layouts":{k:[list(p) for p in v] for k,v in LAYOUTS.items()},"predicates":PREDS,"conditions":CONDITIONS,"modes":["no_identity","stable_identity"],"fields":FIELDS,"repetitions":REPS,"timing":"none; semantic ablation"},"reference":{"path":str(REFERENCE.relative_to(ROOT)),"sha256":sha(REFERENCE)},"samples":samples,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native),"native_extension_sha256":sha(native)},"claim_boundary":"Paired explicit identity-field ablation on one matrix and three repeated-predicate layouts; identity fields are an authored fixture intervention."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples),"reference_sha256":report["reference"]["sha256"]},indent=2))
if __name__=="__main__":main()
