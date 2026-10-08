#!/usr/bin/env python3
"""Independent gates for the GenInfer residual-semantics audit."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_residual_semantics_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_residual_semantics_v1_analysis_20260926.json"
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],"swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
CONDS=["positive","point_corrupt_p1"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(SRC.read_text());samples=raw["samples"];lookup={(s["family"],s["condition"],s["repetition"]):s for s in samples}
 positives=[lookup[f,"positive",r]["observation"] for f in MAPS for r in range(1,6)]
 perturbed=[lookup[f,"point_corrupt_p1",r]["observation"] for f in MAPS for r in range(1,6)]
 expected_shift={"dim":1,"kind":"shift","delta":1,"pred":"p1"}
 checks={
  "complete_balanced_cells":len(samples)==40 and len(lookup)==40 and all((f,c,r) in lookup for f in MAPS for c in CONDS for r in range(1,6)),
  "locked_design_current":raw["protocol"]["maps"]==MAPS and raw["protocol"]["conditions"]==CONDS and raw["protocol"]["repetitions"]==5,
  "positive_matrix_only_outputs":all(o["explained"] is True and o["matrix"]==MAPS[f] and o["residual_dims"]==0 and o["transforms"]==[] and o["dims"]==[] and o["checked"]==6560 for f in MAPS for r in range(1,6) for o in [lookup[f,"positive",r]["observation"]]),
  "perturbations_decomposed_as_single_shift":all(o["explained"] is True and o["matrix"]==MAPS[f] and o["residual_dims"]==1 and o["transforms"]==[expected_shift] and o["dims"]==[1] and o["checked"]==6560 for f in MAPS for r in range(1,6) for o in [lookup[f,"point_corrupt_p1",r]["observation"]]),
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items()),
 }
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"positive_observation_count":len(positives),"perturbed_observation_count":len(perturbed),"semantic_conclusion":"For this fixture, explained=true means the target is decomposed into the recovered matrix plus permitted residual transforms; it does not require matrix-only exact fit."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"semantic_conclusion":result["semantic_conclusion"]},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
