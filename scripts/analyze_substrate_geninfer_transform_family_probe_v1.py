#!/usr/bin/env python3
"""Independent gates and timing summary for the transform-family probe."""
from __future__ import annotations
import hashlib, json, math, random, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"evaluation/reports/substrate_geninfer_transform_family_v1_20260926.json"
OUTPUT=ROOT/"evaluation/reports/substrate_geninfer_transform_family_v1_analysis_20260926.json"
POINTS=[(0,0),(1,0),(2,0),(0,2)]
PREDICATES=["p0","p1","p2","p3"]
TRANSFORMS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],
    "swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def target_for(m):
 a,b,c,d=m;return [(a*r+b*q,c*r+d*q) for r,q in POINTS]
def main():
 raw=json.loads(SOURCE.read_text());groups={name:[] for name in TRANSFORMS}
 for sample in raw["samples"]:groups[sample["transform_family"]].append(sample)
 derived={}
 for name,m in TRANSFORMS.items():
  det=m[0]*m[3]-m[1]*m[2];target=target_for(m)
  base_extent=max(max(r for r,_ in POINTS)-min(r for r,_ in POINTS),max(c for _,c in POINTS)-min(c for _,c in POINTS))
  goal_extent=max(max(r for r,_ in target)-min(r for r,_ in target),max(c for _,c in target)-min(c for _,c in target))
  derived[name]={"determinant":det,"target_coordinates":[list(x) for x in target],
      "base_bound":base_extent,"goal_bound":goal_extent,"search_bound":max(base_extent,goal_extent)}
 rng=random.Random(20260926);expected_schedule={}
 for rep in range(1,6):
  order=list(TRANSFORMS);rng.shuffle(order);expected_schedule[str(rep)]=order
 checks={
  "four_locked_families_present":set(groups)==set(TRANSFORMS),
  "five_samples_per_family":all(len(v)==5 for v in groups.values()),
  "locked_matrices_and_input_current":raw["protocol"]["transforms"]==TRANSFORMS
    and raw["protocol"]["points"]==[list(x) for x in POINTS]
    and raw["protocol"]["predicates"]==PREDICATES,
  "all_transforms_invertible":all(v["determinant"]!=0 for v in derived.values()),
  "four_relation_inputs":all(s["base_relation_count"]==4 and s["goal_relation_count"]==4
    for v in groups.values() for s in v),
  "derived_search_bound_and_candidate_count_fixed":all(v["search_bound"]==4 for v in derived.values())
    and raw["protocol"]["bound"]==4 and raw["protocol"]["candidate_count_per_call"]==6560
    and all(int(raw["candidate_counts"][n])==6560 for n in TRANSFORMS),
  "every_call_recovers_its_exact_matrix":all(s["matrix"]==TRANSFORMS[name]
    for name,values in groups.items() for s in values),
  "finite_positive_timing":all(math.isfinite(float(s["elapsed_seconds"])) and s["elapsed_seconds"]>0
    for values in groups.values() for s in values),
  "balanced_locked_schedule":raw["protocol"]["schedule_by_repetition"]==expected_schedule
    and len(raw["samples"])==20,
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/rel)==digest for rel,digest in raw["provenance"]["source_sha256"].items()),
 }
 by_family={}
 for name,values in groups.items():
  times=[float(x["elapsed_seconds"]) for x in values]
  by_family[name]={"samples":len(times),"median_seconds":statistics.median(times),
      "min_seconds":min(times),"max_seconds":max(times),"candidate_count":6560}
 base=by_family["asymmetric_scale_shear"]["median_seconds"]
 ratios={name:row["median_seconds"]/base for name,row in by_family.items() if name!= "asymmetric_scale_shear"}
 result={"schema_version":1,"source":str(SOURCE.relative_to(ROOT)),"checks":checks,
  "all_checks_pass":all(checks.values()),"derived_transform_bounds":derived,
  "by_transform_family":by_family,"median_time_ratio_vs_asymmetric_scale_shear":ratios,
  "interpretation":"Direct positive recovery and timing across four invertible maps within one 2-D integer-linear class; no general learning claim."}
 OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(OUTPUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,
  "by_transform_family":by_family,"median_time_ratio_vs_asymmetric_scale_shear":ratios},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
