#!/usr/bin/env python3
"""Measure GenInfer recovery under repeated-predicate geometry/corruption."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_20260926.json"
MATRIX=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]}
PREDS=["p0","p0","p1","p1"];DELTAS=[1,2,3];FIELDS=["explained","matrix","residual_dims","transforms","dims","checked"];REPS=5
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 samples=[];a,b,c,d=MATRIX
 for layout,points in LAYOUTS.items():
  base=[[p,r,q,"red"] for p,(r,q) in zip(PREDS,points)]
  mapped=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,points)]
  goals={"positive":mapped}
  for delta in DELTAS:
   goal=[row.copy() for row in mapped];goal[0][1]+=delta;goals[f"corrupt_p0_r_{delta}"]=goal
  for condition,goal in goals.items():
   sub=_native.Substrate();sub.add_node("ShapeSignature",{"name":layout,"signature":json.dumps(base),"kind":"faculty","faculty":layout,"dim_types":["pred","coord:r","coord:c","val"]})
   term={"type":"GenInfer","goal":{"type":"Lit","value":goal},"codebook_type":"ShapeSignature","max_dims":2,"field":"explained"}
   for repetition in range(1,REPS+1):
    observation={field:sub.evaluate({**term,"field":field},{}) for field in FIELDS}
    samples.append({"layout":layout,"condition":condition,"corruption_magnitude":0 if condition=="positive" else int(condition.rsplit("_",1)[1]),"repetition":repetition,"base_relation_count":len(base),"goal_relation_count":len(goal),"base":base,"goal":goal,"observation":observation})
 native=Path(_native.__file__).resolve();paths=["scripts/geninfer_repeat_predicate_robustness_probe_v1.py","scripts/analyze_substrate_geninfer_repeat_predicate_robustness_probe_v1.py","docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEAT_PREDICATE_ROBUSTNESS_PREREG_20260926.md","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 report={"schema_version":1,"run_id":"substrate-geninfer-repeat-predicate-robustness-v1-20260926","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"protocol":{"matrix":MATRIX,"layouts":{k:[list(x) for x in v] for k,v in LAYOUTS.items()},"predicates":PREDS,"corruption_magnitudes":DELTAS,"fields":FIELDS,"max_dims":2,"repetitions":REPS,"timing":"none; robustness semantics only"},"samples":samples,"provenance":{"source_sha256":{p:sha(ROOT/p) for p in paths},"native_extension_path":str(native),"native_extension_sha256":sha(native)},"claim_boundary":"Three small repeated-predicate point layouts, one 2-D integer map, and three magnitudes of one localized coordinate corruption."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"samples":len(samples)},indent=2))
if __name__=="__main__":main()
