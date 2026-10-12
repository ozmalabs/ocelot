#!/usr/bin/env python3
"""Validate reconstructed candidate rankings against native captures and provenance."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_candidate_ranking_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_candidate_ranking_v1_analysis_20260926.json"
CAPTURE=ROOT/"evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json"
LAYOUTS=["original","orthogonal_pairs","paired_square"];MODES=["no_identity","stable_identity"];CONDS=["corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads(SRC.read_text());cases=r["cases"];lookup={(c["layout"],c["mode"],c["condition"]):c for c in cases}
 expected={(l,m,c) for l in LAYOUTS for m in MODES for c in CONDS}
 current=json.loads(CAPTURE.read_text());native_groups={}
 for sample in current["samples"]:
  if sample["condition"] in CONDS:native_groups.setdefault((sample["layout"],sample["mode"],sample["condition"]),[]).append(sample)
 repeat_stable=all(len(v)==5 and all(x["observation"]==v[0]["observation"] for x in v[1:]) for v in native_groups.values()) and len(native_groups)==18
 reconstructed_matches=all(c["reconstructed_fields"]=={k:c["native_fields"][k] for k in ("explained","matrix","residual_dims","transforms","dims","checked")} for c in cases)
 checks={"complete_18_corruption_cells":len(cases)==18 and set(lookup)==expected,
  "input_capture_digest_current":r["input"]["sha256"]==sha(CAPTURE),
  "native_repeat_stability":repeat_stable,
  "reconstructed_winner_matches_every_native_field":reconstructed_matches and all(c["native_fields_match"] for c in cases),
  "search_count_matches_derived_bound":all(c["checked"]==(2*c["B"]+1)**4-1 for c in cases),
  "top_candidates_follow_declared_ranking":all(c["top_candidates"]==sorted(c["top_candidates"],key=lambda x:(x["score"][0],x["score"][1],x["score"][2]))[:10] for c in cases),
  "native_hash_current":sha(Path(r["provenance"]["native_extension_path"]))==r["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in r["provenance"]["source_sha256"].items())}
 selected=[lookup["original","stable_identity",c] for c in CONDS]+[lookup["paired_square","stable_identity","corrupt_p0_r_2"]]
 summary=[{"layout":c["layout"],"condition":c["condition"],"B":c["B"],"candidate_count":c["checked"],"eligible_candidates":c["eligible_candidate_count"],"winner":c["reconstructed_fields"],"winner_score":c["winner_score"],"generator_eligible":c["generating_matrix_eligible"],"generator_score":c["generating_matrix_score"],"top_candidates":c["top_candidates"]} for c in selected]
 compact=[{"layout":c["layout"],"mode":c["mode"],"condition":c["condition"],"B":c["B"],"eligible_candidates":c["eligible_candidate_count"],"winner_matrix":c["reconstructed_fields"]["matrix"],"winner_score":c["winner_score"],"generator_eligible":c["generating_matrix_eligible"],"generator_score":c["generating_matrix_score"]} for c in cases]
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"matched_case_count":sum(bool(c["native_fields_match"]) for c in cases),"case_count":len(cases),"all_case_summary":compact,"selected_stable_identity_cases":summary,"interpretation":"The source-derived reconstruction matches the native winner on every captured corruption cell. In these fixtures, stable IDs can make the generating matrix ineligible under within-predicate residual uniformity; where several candidates remain, the coefficient L1 tie-break can select an alternate over an eligible generating matrix. This validates the enumerated numeric model here but is not a native internal trace or a general proof."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"matched_case_count":result["matched_case_count"],"selected_stable_identity_cases":summary},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
