#!/usr/bin/env python3
"""Independent semantic/source audit for navigation polarity repair v1."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_raw_20261002.json"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1_lock_20261002.json"
ANALYSIS=ROOT/"evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_analysis_20261002.json"
NATIVE_SOURCES=("runners/dsl/src/py.rs","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/term.rs","runners/dsl/src/persist.rs","runners/dsl/src/grammar.rs","runners/dsl/src/sym.rs","runners/dsl/src/lib.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock","runners/dsl/python/substrate_rs/__init__.py")
PY_SOURCES=("domains/reflective_faculty.py","domains/edit_ops.py","domains/self_correction.py","substrate/boot_core.py","substrate/seed_loader.py","domains/engine_provenance.py")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
def normalize_rule(rule):
 x=dict(rule);x["name"]="<variant>";return x
def row_pass(rows):return sum(bool(r["pass"]) for r in rows)
def semantic(rows):
 return [{k:r[k] for k in ("case","expected","actual","pass","closure_work")} for r in rows]
def main():
 capture=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());workers=capture["workers"]
 from substrate_rs import _native
 current={p:sha(ROOT/p) for p in source_paths()};current["loaded_native_binary"]=sha(Path(_native.__file__).resolve())
 pids={w["pid"] for w in workers};base=workers[0]
 labels=[c["label"] for c in base["candidates"]]
 flip=next((c for c in base["candidates"] if c["label"]=="flip_comparison"),None)
 composer=base["composer"]
 expected_cases={"up":"Up","down":"Down","left":"Left","right":"Right"}
 def exact_oracle(rows):
  return len(rows)==4 and all(r["expected"]==expected_cases.get(r["case"]) for r in rows)
 gates={
  "three_distinct_fresh_workers":len(workers)==3 and len(pids)==3,
  "source_lock_matches_before_and_after":capture["source_before"]==capture["source_after"]==lock["sources"],
  "current_sources_and_binary_match_lock":current==lock["sources"],
  "workers_share_same_candidate_and_composer_outcomes":all(
    [c["label"] for c in w["candidates"]]==labels and
    semantic(w["composer"]["outcomes"])==semantic(base["composer"]["outcomes"])
    and [{c["label"]:semantic(c["outcomes"])} for c in w["candidates"]]==
        [{c["label"]:semantic(c["outcomes"])} for c in base["candidates"]]
    for w in workers),
  "each_worker_sources_stable":all(w["source_before"]==w["source_after"]==lock["sources"] for w in workers),
  "faulted_control_fails_all_four":all(row_pass(w["fault_control"])==0 and exact_oracle(w["fault_control"]) for w in workers),
  "original_rule_control_passes_all_four":all(row_pass(w["original_control"])==4 and exact_oracle(w["original_control"]) for w in workers),
  "graph_composer_builds_flip_on_target_rule":all(w["composer"]["grounded"] and w["composer"]["built"] and w["composer"]["kind"]=="flip_comparison" and w["composer"]["removed_rule"]=="hop_descend_gradient" for w in workers),
  "composer_receives_preregistered_flip_symptom":all("flip" in w["composer_input"]["residual_predicates"] for w in workers),
  "composed_edit_matches_flip_surface_candidate":all(
    normalize_rule(w["composer"]["rule"])==normalize_rule(next(c["rule"] for c in w["candidates"] if c["label"]=="flip_comparison"))
    for w in workers),
  "composed_candidate_passes_heldout_oracle":all(row_pass(w["composer"]["outcomes"])==4 and exact_oracle(w["composer"]["outcomes"]) for w in workers),
  "candidate_surface_has_three_or_more_unique_variants":len(labels)>=3 and len(labels)==len(set(labels)),
  "flip_surface_candidate_passes_heldout_oracle":all(next((c for c in w["candidates"] if c["label"]=="flip_comparison" and c["pass_count"]==4),None) is not None for w in workers),
  "composition_does_not_replace_target_rule":all(w["target_rule_unchanged_during_composition"] for w in workers),
  "candidate_labels_and_case_rows_reconcile":all(all(len(c["outcomes"])==4 for c in w["candidates"]) and len(w["candidates"])==len(labels) for w in workers),
 }
 result={"schema":"ThoughtexperimentNavigationPolarityRepairV1_1Analysis","gate_count":len(gates),"passed_gate_count":sum(gates.values()),"gates":gates,
  "summary":{"workers":len(workers),"candidate_count":len(labels),"candidate_labels":labels,
   "task":"faulted hop_descend_gradient, four cardinal held-out states",
   "composer_passes":[row_pass(w["composer"]["outcomes"]) for w in workers],
   "candidate_pass_counts":[{c["label"]:c["pass_count"] for c in w["candidates"]} for w in workers],
   "fault_control_passes":[row_pass(w["fault_control"]) for w in workers],
   "original_control_passes":[row_pass(w["original_control"]) for w in workers]},
  "source_hashes_current":current}
 ANALYSIS.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
