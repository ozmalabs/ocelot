"""tests/test_arc5_shape_probe_migrated.py — Arc 5 shape-constraint ceiling gate.

Companion to `scripts/arc5_shape_constraint_probe.py` (the measurement
driver) and `results/arc5_shape_constraint_probe.json` (the artifact this
gate re-derives every aggregate from). See `PROGRAM_SYNTHESIS_ARC5_SHAPE_
PROBE.md` for the narrative.

Gates:
  1. Artifact schema — top-level + Q1-Q4 keys present.
  2. Population continuity — the_26 / genuine_defect_ids / residual_36 in
     the artifact match a FRESH re-read of the same frozen source files
     (never hand-typed twice differently).
  3. HELD-OUT ISOLATION GATE — none of the SEARCH-side functions
     (check_total_dependence / check_argument_symmetry /
     check_arity_from_prompt / check_monotonicity_precondition /
     run_exclude_probe) mention the literal substring "held_out" in their
     own source (mechanical audit, re-run live independent of the
     artifact's own recorded copy).
  4. >=3 pinned LIVE re-verifications: Q1 recognition count + one named
     false-positive hit; Q3(b) exclude-probe on a fixed id (found=False);
     Q4 transfer probe on a fixed goal (honest wall, transferred=None).
  5. Determinism — the artifact's own twin-run hash match holds, and is
     independently reproduced by a fresh two-pass computation here.
  6. CONSTRAINT-vs-PROPOSAL discipline — `pruning_succeeded_ids` (the
     headline Q3(b) number) is derived ONLY from entries where BOTH
     `probe.found` is True AND `verify_against_held_out.all_held_out_ok`
     is True (never `found` alone) — re-derived from `entries` and
     compared to the artifact's own field.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_arc5_shape_probe_migrated.py
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

import arc5_shape_constraint_probe as probe  # noqa: E402

OUT_PATH = os.path.join(ROOT, "results", "arc5_shape_constraint_probe.json")


@pytest.fixture(scope="module")
def artifact():
    with open(OUT_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  1. Schema.
# --------------------------------------------------------------------------- #
def test_top_level_schema(artifact):
    for key in ("_README", "measured_at", "provenance", "population",
               "q1_recognition_coverage", "q2_constraint_yield",
               "q3_would_it_convert", "q4_analogical_transfer",
               "determinism", "environment", "elapsed_seconds"):
        assert key in artifact, key
    assert artifact["provenance"]["modifies_synthesis_engine_seed_or_spec_code"] is False


def test_q1_schema(artifact):
    q1 = artifact["q1_recognition_coverage"]
    for key in ("n_tasks", "n_recognised", "recognition_rate", "shape_counts",
               "recognised_rows", "vocabulary_size", "algorithmic_keywords_held",
               "vocabulary_note", "analogical_dial_note"):
        assert key in q1, key
    assert q1["n_tasks"] == 257
    # every recognised row carries its mechanical keyword audit.
    for row in q1["recognised_rows"]:
        assert "matched_keywords" in row and row["matched_keywords"]
        assert "matched_keyword_is_algorithmic" in row


def test_q2_schema(artifact):
    cat = artifact["q2_constraint_yield"]["catalogue"]
    for name in ("total_dependence", "argument_symmetry", "arity_from_prompt",
                "monotonicity_idempotence_boundedness"):
        assert name in cat, name
    assert cat["total_dependence"]["overlap_with_D3_D4"].startswith("EXACT")
    # the NEW-mass field must be a subset of violated_ids, never a superset.
    sym = cat["argument_symmetry"]
    assert set(sym["new_mass_beyond_total_dependence"]) <= set(sym["violated_ids"])


def test_q3_schema(artifact):
    q3 = artifact["q3_would_it_convert"]
    assert "a_principled_rejection" in q3
    assert "b_empirical_pruning" in q3
    b = q3["b_empirical_pruning"]
    for key in ("population_tested", "n_population", "n_search_found_something",
               "n_found_and_verified_correct_on_held_out", "pruning_succeeded_ids",
               "entries", "mechanism_explanation",
               "held_out_isolation_audit_of_search_functions"):
        assert key in b, key


def test_q4_schema(artifact):
    q4 = artifact["q4_analogical_transfer"]
    assert q4["n_held_mechanisms"] == 2
    assert q4["held_mechanisms_are_algorithmic"] is False
    assert q4["math_shapes_are_algorithmic"] is False
    assert "live_transfer_probes" in q4


# --------------------------------------------------------------------------- #
#  2. Population continuity against frozen sources.
# --------------------------------------------------------------------------- #
def test_the_26_matches_frozen_arc4_endgame(artifact):
    with open(probe.S5_ENDGAME_PATH) as f:
        d = json.load(f)
    h = d["ha2_verdict_discrimination"]
    no_s = set(h["no_structural_accepted_holdout_fail_ids"])
    full = set(h["full_a4_accepted_holdout_fail_ids"])
    ids = sorted(no_s - full)
    assert ids == artifact["population"]["the_26"]["all_26"]
    assert sorted(probe.RETRIEVAL_SOURCED_14 + probe.REOPENED_12) == ids


def test_residual_36_matches_frozen_structural_verdicts(artifact):
    with open(probe.STRUCTURAL_PATH) as f:
        d = json.load(f)
    assert d["new_honest_residual_ids"] == artifact["population"]["residual_36"]
    assert len(d["new_honest_residual_ids"]) == 36


def test_traps_and_pass_counts_match_frozen_r3(artifact):
    ahf, passed = probe.load_r3_populations()
    assert len(ahf) == 76 == artifact["population"]["n_traps_76"]
    assert len(passed) == 21 == artifact["population"]["n_pass_21"]


def test_the_26_and_residual_36_are_disjoint(artifact):
    a = set(artifact["population"]["the_26"]["all_26"])
    b = set(artifact["population"]["residual_36"])
    assert not (a & b), "the 26 (S6-caught) and the 36 (honest residual) must be disjoint subsets of the 76"
    assert (a | b) <= set(probe.load_r3_populations()[0])


# --------------------------------------------------------------------------- #
#  3. HELD-OUT ISOLATION GATE.
# --------------------------------------------------------------------------- #
def test_search_functions_never_reference_held_out():
    audit = probe._held_out_isolation_audit_search_fns()
    assert not audit["any_hit"], audit["hits"]
    assert audit["functions_checked"] == sorted([
        "check_total_dependence", "check_argument_symmetry",
        "check_arity_from_prompt", "check_monotonicity_precondition",
        "run_exclude_probe",
    ])


def test_verify_function_is_the_only_one_reading_held_out():
    """The converse of the isolation gate: exactly ONE function in this
    module is allowed to read held-out data (measurement-only, sanctioned
    by `domains/mbpp_spec.py`'s own contamination_rule), and its result is
    never threaded back into a search call — `run_exclude_probe` never
    calls it, `q3_would_it_convert` calls it strictly AFTER the search
    result is already final."""
    src = inspect.getsource(probe.verify_found_program_against_held_out)
    assert "held_out" in src or "held-out" in src.lower()
    assert "held_out" not in inspect.getsource(probe.run_exclude_probe)


def test_artifact_own_recorded_audit_matches_live(artifact):
    live = probe._held_out_isolation_audit_search_fns()
    recorded = artifact["q3_would_it_convert"]["b_empirical_pruning"][
        "held_out_isolation_audit_of_search_functions"]
    assert live == recorded


# --------------------------------------------------------------------------- #
#  4. >=3 pinned LIVE re-verifications.
# --------------------------------------------------------------------------- #
def test_live_q1_recognition_count_and_named_false_positive():
    tasks_by_id = probe.load_test_tasks()
    q1 = probe.q1_recognition_coverage(tasks_by_id)
    assert q1["n_recognised"] == 23
    by_id = {r["task_id"]: r for r in q1["recognised_rows"]}
    # task 11 ("remove first and last occurrence...") fires spatial_dynamics
    # via the substring 'move' inside 'remove' -- pinned as the canonical
    # named false-positive, mechanically confirmed via matched_keywords.
    assert 11 in by_id
    assert by_id[11]["recognised_shape"] == "spatial_dynamics"
    assert any(kw.endswith(":move") for kw in by_id[11]["matched_keywords"])
    assert by_id[11]["matched_keyword_is_algorithmic"] is False
    # zero genuine algorithmic true positives anywhere in the population.
    assert q1["n_algorithmic_true_positive"] == 0
    assert q1["algorithmic_keywords_held"] == []


def test_live_exclude_probe_on_task_14_finds_nothing():
    """Task 14 (volume of a triangular prism): the accepted trap ignores
    `a` entirely; the true relation (a*b*c/2) reproduces the SAME two
    revealed-row outputs (240, 6) as the trap, so excluding the trap's own
    signature also excludes the true relation — found:False, live."""
    tasks_by_id = probe.load_test_tasks()
    ahf, _ = probe.load_r3_populations()
    ir = ahf[14]["ir"]
    revealed = probe.afa._revealed_rows_for_task(14, tasks_by_id)
    out = probe.run_exclude_probe(14, ir, revealed)
    assert out["found"] is False


def test_live_transfer_probe_on_top_of_three_is_honest_wall():
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.reflective_faculty import retrieve_and_transfer_mechanism
    wa = WorldAdapter()
    for seed in ("shape_vocabulary", "seven_meta_shape_subsystems",
                "relation_vocabulary", "mechanism_index"):
        try:
            wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
        except Exception:
            pass
    goal = [["find", "the", "LARGEST", "of", "THREE", "NUMBERS"],
           ["compare", "NUMBER", "with", "NUMBER"]]
    rt = retrieve_and_transfer_mechanism(wa, goal)
    assert rt["meta_shape"] is None
    assert rt["retrieved"] == []
    assert rt["transferred"] is None


# --------------------------------------------------------------------------- #
#  5. Determinism.
# --------------------------------------------------------------------------- #
def test_determinism_twin_run_recorded_in_artifact(artifact):
    assert artifact["determinism"]["twin_run_sha256_match"] is True


def test_determinism_fresh_two_pass_reproduces_live():
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


# --------------------------------------------------------------------------- #
#  6. CONSTRAINT-vs-PROPOSAL discipline on the headline Q3(b) number.
# --------------------------------------------------------------------------- #
def test_pruning_succeeded_ids_requires_found_and_held_out_verified(artifact):
    b = artifact["q3_would_it_convert"]["b_empirical_pruning"]
    rederived = [e["task_id"] for e in b["entries"]
                if e["probe"].get("found")
                and e.get("verify_against_held_out", {}).get("all_held_out_ok")]
    assert rederived == b["pruning_succeeded_ids"]


def test_found_is_not_conflated_with_correct(artifact):
    """The sharp discipline this whole probe measures: SOME entries have
    probe.found=True (the search DID return a candidate once the trap's
    signature was excluded), but EVERY one of those is verified WRONG on
    held-out — found is a PROPOSAL, not a CONSTRAINT verdict, and this test
    pins that the artifact never conflates the two."""
    b = artifact["q3_would_it_convert"]["b_empirical_pruning"]
    found_entries = [e for e in b["entries"] if e["probe"].get("found")]
    assert found_entries, "expected at least one found=True entry to exercise this gate"
    for e in found_entries:
        v = e.get("verify_against_held_out")
        assert v is not None, e["task_id"]
        assert v["all_held_out_ok"] is False, (
            e["task_id"], "if this ever flips True, Q3(b)'s headline changes "
            "and PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md must be revisited")
    assert b["pruning_succeeded_ids"] == []
    assert b["n_found_and_verified_correct_on_held_out"] == 0


def test_the_26_are_all_principled_by_construction(artifact):
    """Self-consistency, not a new discovery: 'the 26' IS the population
    S6/S2's own structural detectors caught, so 26/26 must show a
    principled-rejection reason here — this test guards against that tautology
    being silently broken, not against it being silently claimed as news."""
    a = artifact["q3_would_it_convert"]["a_principled_rejection"]["the_26"]
    assert a["n_principled_reject"] == a["n_population"] == 26


def test_residual_36_gains_zero_principled_rejections_from_the_new_catalogue(artifact):
    """The sharper, non-tautological finding: applying the NEW catalogue
    (argument symmetry, on top of the existing D1-D7 union) to the honest-
    residual 36 adds NOTHING — confirmed here against the live artifact."""
    a = artifact["q3_would_it_convert"]["a_principled_rejection"]["residual_36"]
    assert a["n_principled_reject"] == 0


def test_argument_symmetry_adds_zero_new_mass_over_total_dependence(artifact):
    sym = artifact["q2_constraint_yield"]["catalogue"]["argument_symmetry"]
    assert sym["n_new_mass"] == 0
    assert sym["new_mass_beyond_total_dependence"] == []
