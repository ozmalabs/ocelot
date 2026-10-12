#!/usr/bin/env python3
"""Positive and selected-null refusal probe for GenInfer."""
from __future__ import annotations
import hashlib, json, platform, random, subprocess, sys, time
from pathlib import Path
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_geninfer_noise_refusal_v1_20260926.json"
POINTS=[(0,0),(1,0),(2,0),(0,2)]; PREDS=["p0","p1","p2","p3"]
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],
      "swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
CONDITIONS=["positive","origin_corrupt","predicate_corrupt","missing_origin","extra_origin"]
REPS=5; SEED=20260926
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cells={}
 for fam,m in MAPS.items():
  base=[[p,r,c,"red"] for p,(r,c) in zip(PREDS,POINTS)]
  a,b,c,d=m; target=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,POINTS)]
  targets={"positive":target,
   "origin_corrupt":[[p,(1 if p=="p0" else r),q,v] for p,r,q,v in target],
   "predicate_corrupt":[["corrupt_p3" if p=="p3" else p,r,q,v] for p,r,q,v in target],
   "missing_origin":target[1:],"extra_origin":target+[["extra",0,0,"red"]]}
  sub=_native.Substrate(); sub.add_node("ShapeSignature",{"name":fam,"signature":json.dumps(base),"kind":"faculty","faculty":fam,"dim_types":["pred","coord:r","coord:c","val"]})
  cells[fam]={"sub":sub,"base":base,"targets":targets}
 first=next(iter(MAPS)); sub=cells[first]["sub"]
 sub.evaluate({"type":"GenInfer","goal":{"type":"Lit","value":cells[first]["targets"]["positive"]},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"},{})
 combos=[(f,c) for f in MAPS for c in CONDITIONS];rng=random.Random(SEED);sched={};samples=[]
 for rep in range(1,REPS+1):
  order=combos.copy();rng.shuffle(order);sched[str(rep)]=[[f,c] for f,c in order]
  for fam,cond in order:
   cell=cells[fam];term={"type":"GenInfer","goal":{"type":"Lit","value":cell["targets"][cond]},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
   start=time.perf_counter(); explained=bool(cell["sub"].evaluate(term,{}));elapsed=time.perf_counter()-start
   matrix=[int(x) for x in cell["sub"].evaluate({**term,"field":"matrix"},{})]
   checked=int(cell["sub"].evaluate({**term,"field":"checked"},{}))
   samples.append({"repetition":rep,"transform_family":fam,"condition":cond,"explained":explained,"matrix":matrix,"checked":checked,"base_relation_count":4,"goal_relation_count":len(cell["targets"][cond]),"elapsed_seconds":elapsed})
 native=Path(_native.__file__).resolve();paths=["scripts/geninfer_noise_refusal_probe_v1.py","scripts/analyze_substrate_geninfer_noise_refusal_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_NOISE_REFUSAL_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-geninfer-noise-refusal-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"transforms":MAPS,"points":[list(x) for x in POINTS],"predicates":PREDS,"conditions":CONDITIONS,"bound":4,"candidate_count_per_call":6560,"repetitions":REPS,"schedule_seed":SEED,"schedule_by_repetition":sched,"warmup":"one untimed positive explained call","timed_call":"GenInfer(field=explained)"},"samples":samples,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native),"native_extension_sha256":sha(native)},"claim_boundary":"Selected positive and four null classes on four small 2-D integer-linear maps; no calibrated natural-noise or false-positive estimate."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples)},indent=2))
if __name__=="__main__":main()
