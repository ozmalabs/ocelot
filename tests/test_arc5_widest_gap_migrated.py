"""tests/test_arc5_widest_gap_migrated.py — Arc 5 widest-gap criterion gate.

Companion to `scripts/arc5_widest_gap_probe.py` (the measurement driver)
and `results/arc5_widest_gap.json` (the artifact this gate re-derives
every aggregate from). See `PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md` for the
narrative.

Gates:
  1. Artifact schema — top-level + br_10/reopened_12/residual_36/
     intent_vs_gap_head_to_head keys present.
  2. HELD-OUT ISOLATION GATE — none of the SEARCH-side functions (grammar/
     applicability/relaxation/gap functions) mention the literal substring
     "held_out" in their own source (mechanical audit, re-run live
     independent of the artifact's own recorded copy).
  3. >=3 pinned LIVE re-verifications: (a) br_10 selects a permutation
     relaxation with gap>0 and converts; (b) a refuted-permutation case is
     correctly refused (hand-built fixture, no augmentation applied); (c)
     the wide-probe distinctness mechanism actually separates two
     behaviourally-different-but-revealed-agreeing candidates (the
     mechanism the whole gap computation depends on).
  4. Determinism — the artifact's own twin-run hash holds, and is
     independently reproduced by a fresh two-pass computation here.
  5. Selection-vs-verification discipline — `converted`/`false_selection`
     are derived ONLY from `held_out_verify`, never from `gap` alone; the
     `eligible`/selection sort key never reads a held-out field (source
     audit).
  6. intent_vs_gap_head_to_head arithmetic — precision/recall recomputed
     from the artifact's own tp/fp/fn id lists, and the population size
     matches the union of applicable ids across br_10/reopened_12/
     residual_36.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_arc5_widest_gap_migrated.py
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest  # noqa: E402

import substrate_rs as srs  # noqa: E402
import arc5_widest_gap_probe as probe  # noqa: E402

OUT_PATH = os.path.join(ROOT, "results", "arc5_widest_gap.json")


@pytest.fixture(scope="module")
def artifact():
    with open(OUT_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  1. Schema.
# --------------------------------------------------------------------------- #
def test_top_level_schema(artifact):
    for key in ("_README", "measured_at", "provenance", "grammar", "br_10",
               "reopened_12", "residual_36", "intent_vs_gap_head_to_head",
               "held_out_isolation_audit", "determinism", "environment",
               "elapsed_seconds"):
        assert key in artifact, key
    assert artifact["provenance"]["modifies_synthesis_engine_seed_or_spec_code"] is False


def test_task_row_schema(artifact):
    for key in ("task_id", "params", "n_revealed", "applicability", "intent_evidence"):
        assert key in artifact["br_10"], key
    ie = artifact["br_10"]["intent_evidence"]
    for key in ("declared_arity", "used_arity", "arity_gap", "arity_gap_flags_trap",
               "name_arity_hint", "name_arity_agrees"):
        assert key in ie, key


def test_summary_schema(artifact):
    for pop in ("reopened_12", "residual_36"):
        summary = artifact[pop]["summary"]
        for key in ("n_tasks", "n_applicable", "applicable_ids",
                   "inapplicable_ids_and_reasons", "selected_ids", "converted_ids",
                   "false_selection_ids", "n_relaxation_instances_considered",
                   "n_relaxation_instances_refuted", "refutation_rate",
                   "gap_as_sole_weight"):
            assert key in summary, "%s.%s" % (pop, key)
        gsw = summary["gap_as_sole_weight"]
        for key in ("n_selected", "gap_argmax_correct_ids", "gap_argmax_wrong_ids",
                   "gap_selection_accuracy", "oracle_ceiling_ids", "oracle_ceiling_rate",
                   "wrong_selection_characterization"):
            assert key in gsw, "%s.gap_as_sole_weight.%s" % (pop, key)


def test_intent_vs_gap_schema(artifact):
    h2h = artifact["intent_vs_gap_head_to_head"]
    for key in ("_caveat", "ground_truth", "n_applicable", "n_ground_truth_positive",
               "arity_gap_predictor", "gap_score_predictor", "per_task",
               "confound_note", "arity_gap_fp_d3_cross_check"):
        assert key in h2h, key
    for predictor in ("arity_gap_predictor", "gap_score_predictor"):
        p = h2h[predictor]
        for key in ("tp_ids", "fp_ids", "fn_ids", "tn_ids", "precision", "recall"):
            assert key in p, "%s.%s" % (predictor, key)


# --------------------------------------------------------------------------- #
#  2. Held-out isolation.
# --------------------------------------------------------------------------- #
def test_search_functions_never_reference_held_out():
    audit = probe._held_out_isolation_audit()
    assert audit["any_hit"] is False, audit["hits"]
    # the audit itself must actually be checking something real.
    assert len(audit["functions_checked"]) >= 10


def test_artifact_isolation_audit_matches_live():
    with open(OUT_PATH) as f:
        artifact = json.load(f)
    live = probe._held_out_isolation_audit()
    assert artifact["held_out_isolation_audit"] == live


def test_verify_against_held_out_is_the_sole_sanctioned_reader():
    """Every SEARCH-side function is clean (previous test); this confirms
    `verify_against_held_out` is the ONE function in the module that DOES
    read held-out data (by construction, not accident), that it is never
    called from within `gap_for_relaxation` (the scoring function), and
    that the SELECTION logic itself (the `eligible` filter + its sort
    key) never mentions held-out data -- selection is retrospectively
    SCORED against held-out (for characterisation) both before and after
    it runs, but never DRIVEN by it."""
    src = inspect.getsource(probe.verify_against_held_out)
    assert "held_out_rows" in src
    gap_src = inspect.getsource(probe.gap_for_relaxation)
    assert "held_out" not in gap_src
    run_task_src = inspect.getsource(probe.run_task)
    eligible_block = run_task_src.split("eligible = [")[1].split("row[\"selected_gap\"]")[0]
    assert "held_out" not in eligible_block


# --------------------------------------------------------------------------- #
#  3. Pinned live re-verifications.
# --------------------------------------------------------------------------- #
def test_live_br10_selects_a_permutation_relaxation_and_converts():
    s = srs.Substrate()
    with open(probe.BATTERY_PATH) as f:
        battery = json.load(f)
    br10 = next(t for t in battery["tasks"] if t["id"] == "br_10_top_of_three")
    revealed = [{"inputs": r["inputs"], "expected": r["expected"]} for r in br10["example_rows"]]
    held_out = [{"inputs": r["inputs"], "expected": r["expected"]} for r in br10["held_out_rows"]]
    witness = [{"inputs": {"a": 100, "b": 3, "c": 47}, "expected": 100}]
    trap_ir = {"type": "Max", "items": [{"type": "Var", "name": "a"},
                                        {"type": "Var", "name": "b"}]}
    row = probe.run_task(s, "br_10_top_of_three", ["a", "b", "c"], revealed, held_out,
                         witness_rows=witness, accepted_ir=trap_ir,
                         prompt=br10["request_text"], func_name="top_of_three")
    assert row["applicability"]["applicable"] is True
    assert row["selected_relaxation"] is not None
    assert row["selected_relaxation"].startswith("sym_")
    assert row["selected_gap"] >= 1
    assert row["converted"] is True
    assert row["held_out_verify"]["all_ok"] is True
    assert row["held_out_verify"]["witness_all_ok"] is True
    # the un-hand-picked headline: S3 (or a subgroup that suffices) is
    # among the NON-REFUTED, gap-scored candidates -- never hand-selected.
    names = {r["name"] for r in row["relaxations"] if r.get("gap_computed")}
    assert "sym_full_S3" in names
    assert row["intent_evidence"]["arity_gap"] == 1
    assert row["intent_evidence"]["arity_gap_flags_trap"] is True


def test_live_refuted_permutation_is_never_applied():
    """A hand-built fixture where two revealed rows ARE a permutation pair
    with DIFFERENT outputs -- must be refuted, and must contribute NO
    augmented rows / no gap score."""
    params = ["a", "b"]
    revealed = [{"inputs": {"a": 1, "b": 2}, "expected": 10},
               {"inputs": {"a": 2, "b": 1}, "expected": 20}]  # same multiset, diff output
    relax = probe.relax_permutation(params, revealed, None)
    assert relax["refuted"] is True
    assert relax["augmented_rows"] == []


def test_live_wide_probe_separates_behaviourally_distinct_candidates():
    """The mechanism the whole gap computation rests on: two candidates
    that AGREE on the sparse revealed rows but DISAGREE elsewhere must
    land in different signature groups once probed on the wider grid."""
    s = srs.Substrate()
    params = ["a", "b", "c"]
    revealed = [{"inputs": {"a": 1, "b": 9, "c": 3}, "expected": 9},
               {"inputs": {"a": 7, "b": 2, "c": 5}, "expected": 7},
               {"inputs": {"a": 4, "b": 4, "c": 4}, "expected": 4}]
    max_ab = {"type": "Max", "items": [{"type": "Var", "name": "a"},
                                       {"type": "Var", "name": "b"}]}
    max_abc = {"type": "Max", "items": [
        {"type": "Max", "items": [{"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]},
        {"type": "Var", "name": "c"}]}
    for expr in (max_ab, max_abc):
        for row in revealed:
            got = probe.eval_expr(s, expr, row["inputs"])
            assert probe.numeric_agree(got, row["expected"])
    wide_probe = probe.wide_probe_points(params, revealed)
    n, groups = probe.count_distinct(s, [(max_ab, 3), (max_abc, 5)], wide_probe)
    assert n == 2, "Max(a,b) and Max(a,Max(b,c)) must be DISTINCT over the wide probe"


# --------------------------------------------------------------------------- #
#  4. Determinism.
# --------------------------------------------------------------------------- #
def test_determinism_field_present_and_true(artifact):
    assert artifact["determinism"]["twin_run_sha256_match"] is True


def test_determinism_fresh_reproduces(artifact):
    def _strip_clock(r):
        r = dict(r)
        r["measured_at"] = None
        r["elapsed_seconds"] = None
        return r

    run1 = probe.run_all()
    run2 = probe.run_all()
    h1 = hashlib.sha256(probe._canon(_strip_clock(run1)).encode()).hexdigest()
    h2 = hashlib.sha256(probe._canon(_strip_clock(run2)).encode()).hexdigest()
    assert h1 == h2
    assert h1 == artifact["determinism"]["sha256"]


# --------------------------------------------------------------------------- #
#  5. Selection-vs-verification discipline.
# --------------------------------------------------------------------------- #
def test_selection_never_reads_held_out_fields(artifact):
    run_task_src = inspect.getsource(probe.run_task)
    eligible_block = run_task_src.split("eligible = [")[1].split("row[\"selected_gap\"]")[0]
    assert "held_out" not in eligible_block


def test_converted_implies_held_out_ok(artifact):
    for pop in ("reopened_12", "residual_36"):
        for row in artifact[pop]["rows"]:
            if row.get("converted"):
                assert row["held_out_verify"]["all_ok"] is True
    if artifact["br_10"].get("converted"):
        assert artifact["br_10"]["held_out_verify"]["all_ok"] is True


def test_false_selection_implies_held_out_failed(artifact):
    for pop in ("reopened_12", "residual_36"):
        for row in artifact[pop]["rows"]:
            if row.get("false_selection"):
                assert row["held_out_verify"]["all_ok"] is False


# --------------------------------------------------------------------------- #
#  6. intent_vs_gap_head_to_head arithmetic.
# --------------------------------------------------------------------------- #
def test_head_to_head_population_matches_applicable_union(artifact):
    h2h = artifact["intent_vs_gap_head_to_head"]
    applicable_ids = set()
    if artifact["br_10"]["applicability"]["applicable"]:
        applicable_ids.add(artifact["br_10"]["task_id"])
    for pop in ("reopened_12", "residual_36"):
        applicable_ids.update(artifact[pop]["summary"]["applicable_ids"])
    assert h2h["n_applicable"] == len(applicable_ids)
    assert {r["task_id"] for r in h2h["per_task"]} == applicable_ids


def test_head_to_head_precision_recall_recomputed(artifact):
    for predictor in ("arity_gap_predictor", "gap_score_predictor"):
        p = artifact["intent_vs_gap_head_to_head"][predictor]
        tp, fp, fn = len(p["tp_ids"]), len(p["fp_ids"]), len(p["fn_ids"])
        if tp or fp:
            assert abs(p["precision"] - tp / (tp + fp)) < 1e-9
        else:
            assert p["precision"] is None
        if tp or fn:
            assert abs(p["recall"] - tp / (tp + fn)) < 1e-9
        else:
            assert p["recall"] is None


def test_arity_gap_false_positives_are_v0_empty_not_engine_noise(artifact):
    """Characterisation gate for the reframe's ask: every arity_gap false
    positive in THIS measurement's population has n_matched_revealed_only
    == 0 (gap-score's own version-space search never even found a
    candidate), so the raw precision comparison is confounded by grammar
    coverage, not a clean head-to-head on cases both predictors actually
    attempted."""
    h2h = artifact["intent_vs_gap_head_to_head"]
    fp_ids = set(h2h["arity_gap_predictor"]["fp_ids"])
    cross = {row["task_id"]: row for row in h2h["arity_gap_fp_d3_cross_check"]}
    assert fp_ids == set(cross)
    for tid, row in cross.items():
        assert row["n_matched_revealed_only"] == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
