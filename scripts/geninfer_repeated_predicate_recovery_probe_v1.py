#!/usr/bin/env python3
"""Repeated-predicate assignment × perturbation evaluator factorial."""
import hashlib, json, platform, subprocess, sys
from pathlib import Path
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_PREREG_20260926.md"
OUT=ROOT/"evaluation/reports/substrate_geninfer_repeated_predicate_recovery_v1_20260926.json"
MATRIX=[1,1,0,2]; POINTS=[(0,0),(1,0),(2,0),(0,2)]
GROUPS={"adjacent_01":(0,1),"opposite_03":(0,3),"adjacent_12":(1,2)}
PERTURBATIONS={"positive":(0,0),"uniform_1":(1,1),"uniform_2":(2,2),"unequal_1_2":(1,2),"unequal_1_3":(1,3)}
FIELDS=("explained","matrix","residual_dims","transforms","dims","checked")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sample(group, perturb, rep):
    p0=GROUPS[group]; shifts=PERTURBATIONS[perturb]; a,b,c,d=MATRIX
    base=[]; goal=[]
    for i,(r,q) in enumerate(POINTS):
        pred="p0" if i in p0 else "p1"
        base.append([pred,r,q,"red"])
        goal.append([pred,a*r+b*q+(shifts[p0.index(i)] if i in p0 else 0),c*r+d*q,"red"])
    sub=_native.Substrate(); sub.add_node("ShapeSignature",{"name":group,"signature":json.dumps(base),"kind":"faculty","faculty":group,"dim_types":["pred","coord:r","coord:c","val"]})
    term={"type":"GenInfer","goal":{"type":"Lit","value":goal},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
    obs={f:sub.evaluate({**term,"field":f},{}) for f in FIELDS}
    return {"group":group,"perturbation":perturb,"repetition":rep,"base":base,"goal":goal,"observation":obs}
def main():
    rows=[sample(g,p,r) for g in GROUPS for p in PERTURBATIONS for r in range(1,6)]
    paths=["scripts/geninfer_repeated_predicate_recovery_probe_v1.py","scripts/analyze_geninfer_repeated_predicate_recovery_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
    payload={"schema_version":1,"protocol":"SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_V1","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"inputs":{"matrix":MATRIX,"points":[list(x) for x in POINTS],"groups":GROUPS,"perturbations":PERTURBATIONS,"repetitions":5,"fields":FIELDS},"samples":rows,"source_sha256":{p:sha(ROOT/p) for p in paths},"native":{"path":str(Path(_native.__file__).resolve()),"sha256":sha(Path(_native.__file__).resolve())},"claim_boundary":"controlled small 2-D repeated-predicate recovery study; not natural-noise or full-seed learning evidence"}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"n":len(rows)},indent=2))
if __name__=="__main__": main()
