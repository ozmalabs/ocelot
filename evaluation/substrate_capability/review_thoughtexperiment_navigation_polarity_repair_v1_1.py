#!/usr/bin/env python3
"""Independent source and semantic review of navigation polarity v1.1."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RAW=ROOT/"evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_raw_20261002.json"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1_lock_20261002.json"
REVIEW=ROOT/"evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_analysis_review_20261002.json"
NATIVE_SOURCES=("runners/dsl/src/py.rs","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/term.rs","runners/dsl/src/persist.rs","runners/dsl/src/grammar.rs","runners/dsl/src/sym.rs","runners/dsl/src/lib.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock","runners/dsl/python/substrate_rs/__init__.py")
PY_SOURCES=("domains/reflective_faculty.py","domains/edit_ops.py","domains/self_correction.py","substrate/boot_core.py","substrate/seed_loader.py","domains/engine_provenance.py")
EXPECTED={"up":"Up","down":"Down","left":"Left","right":"Right"}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def seed_closure():
 from substrate.boot_core import CORE_SEEDS
 from substrate.seed_loader import manifest_for
 pending=[*CORE_SEEDS,"relation_vocabulary","grid_navigation"];seen=set()
 while pending:
  sid=str(pending.pop())
  if sid in seen:continue
  seen.add(sid);pending.extend(str(x) for x in manifest_for(sid).get("depends_on",()))
 return sorted(f"seeds/{sid}.json" for sid in seen)
def source_paths():
 return sorted(set((*NATIVE_SOURCES,*PY_SOURCES,*seed_closure(),
  "evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py",
  "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md",
  "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md",
  "evaluation/substrate_capability/analyze_thoughtexperiment_navigation_polarity_repair_v1_1.py")))
def semantic(rows):
 return [{k:r[k] for k in ("case","expected","actual","pass","closure_work")} for r in rows]
def passes(rows):return sum(bool(x["pass"]) for x in rows)
def normalized_rule(rule):
 copy=dict(rule);copy["name"]="<variant>";return copy
def main():
 from substrate_rs import _native
 from domains.edit_ops import apply_flip_comparison
 capture=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());workers=capture["workers"]
 current={name:sha(ROOT/name) for name in source_paths()}
 current["loaded_native_binary"]=sha(Path(_native.__file__).resolve())
 labels=[c["label"] for c in workers[0]["candidates"]]
 flip=next((c for c in workers[0]["candidates"] if c["label"]=="flip_comparison"),None)
 source_fault_exact=all(apply_flip_comparison(w["source_rule"],"hop_descend_gradient")==w["faulted_rule"] for w in workers)
 gates={
  "three_fresh_distinct_workers":len(workers)==3 and len({w["pid"] for w in workers})==3,
  "pre_post_and_current_sources_match_lock":capture["source_before"]==capture["source_after"]==lock["sources"]==current,
  "worker_source_snapshots_match_lock":all(w["source_before"]==w["source_after"]==lock["sources"] for w in workers),
  "fault_is_exact_source_comparison_flip":source_fault_exact,
  "four_fixed_oracle_states_per_arm":all(len(w["fault_control"])==len(w["original_control"])==len(w["composer"]["outcomes"])==4 for w in workers),
  "faulted_control_fails_all_cases":all(passes(w["fault_control"])==0 and all(r["expected"]==EXPECTED[r["case"]] for r in w["fault_control"]) for w in workers),
  "source_rule_control_passes_all_cases":all(passes(w["original_control"])==4 and all(r["expected"]==EXPECTED[r["case"]] for r in w["original_control"]) for w in workers),
  "composer_receives_flip_symptom":all("flip" in w["composer_input"]["residual_predicates"] for w in workers),
  "graph_composer_builds_flip_for_target":all(w["composer"]["grounded"] and w["composer"]["built"] and w["composer"]["kind"]=="flip_comparison" and w["composer"]["removed_rule"]=="hop_descend_gradient" for w in workers),
  "composed_edit_matches_candidate_surface_flip":all(w["composer"]["rule"] and next(c for c in w["candidates"] if c["label"]=="flip_comparison")["rule"] and normalized_rule(w["composer"]["rule"])==normalized_rule(next(c for c in w["candidates"] if c["label"]=="flip_comparison")["rule"]) for w in workers),
  "composed_edit_passes_all_cases":all(passes(w["composer"]["outcomes"])==4 and all(r["expected"]==EXPECTED[r["case"]] for r in w["composer"]["outcomes"]) for w in workers),
  "candidate_surface_flip_passes_all_cases":all(flip is not None and next(c for c in w["candidates"] if c["label"]=="flip_comparison")["pass_count"]==4 for w in workers),
  "candidate_surface_has_at_least_three_unique_variants":len(labels)>=3 and len(set(labels))==len(labels),
  "candidate_rows_and_order_reconcile_across_workers":all([c["label"] for c in w["candidates"]]==labels and all(len(c["outcomes"])==4 and c["pass_count"]==passes(c["outcomes"]) for c in w["candidates"]) for w in workers),
  "all_semantic_outcomes_replicate":all(semantic(w["composer"]["outcomes"])==semantic(workers[0]["composer"]["outcomes"]) and [semantic(c["outcomes"]) for c in w["candidates"]]==[semantic(c["outcomes"]) for c in workers[0]["candidates"]] for w in workers),
  "target_rule_not_replaced_during_composition":all(w["target_rule_unchanged_during_composition"] for w in workers),
 }
 result={"schema":"ThoughtexperimentNavigationPolarityRepairV1_1CorrectedReview",
  "reviewer_sha256":sha(Path(__file__).resolve()),"initial_analyzer_failed_before_scoring":True,
  "gate_count":len(gates),"passed_gate_count":sum(gates.values()),"gates":gates,
  "summary":{"workers":len(workers),"candidate_count":len(labels),"candidate_labels":labels,
   "composer_passes":[passes(w["composer"]["outcomes"]) for w in workers],
   "fault_control_passes":[passes(w["fault_control"]) for w in workers],
   "original_control_passes":[passes(w["original_control"]) for w in workers],
   "candidate_pass_counts":[{c["label"]:c["pass_count"] for c in w["candidates"]} for w in workers]},
  "source_hashes_current":current}
 REVIEW.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
