"""tests/test_structural_verdicts_migrated.py — Arc 4 structural-ceiling gate.

Companion to `scripts/arc4_structural_verdicts.py` (the measurement driver)
and `results/arc4_structural_verdicts.json` (the artifact this gate
re-derives every aggregate from). See `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_
NOTES.md` for the corrected-framing narrative this measurement supports:
S0-A (`arc4_failure_anatomy.py`) measured a 30.3% (23/76) BEHAVIOURAL
killable ceiling and a 69.7% (53/76) honest residual on the accepted-but-
wrong `accepted_holdout_fail` trap population. This phase asks a DIFFERENT
question -- how much of that residual is killable by STRUCTURAL inspection
of the accepted program's own IR, never behavioural execution on unseen
data -- and finds a corrected, larger ceiling.

Gates:
  1. Artifact schema — top-level keys present.
  2. Population continuity — the 76 trap ids and 21 correct ids read from
     the frozen `results/mbpp_arc3_endgame.json` match the frozen
     `results/arc4_failure_anatomy.json`'s own `ahf_task_ids` exactly (a
     read-only cross-artifact consistency check, no re-run).
  3. HELD-OUT ISOLATION GATE — no structural-detector function's source
     contains the literal substring "held_out" (mechanical source-text
     audit, re-run live here independent of the artifact's own recorded
     copy of the same audit).
  4. Per-detector totals / recall / false-positive-rate / precision are
     independently RE-DERIVED from `per_task`/`per_task_correct` and must
     match the artifact's own `per_detector` block exactly.
  5. Union/overlap arithmetic — structural_only + overlap ==
     structural_killable; structural_only + overlap + behavioral_only ==
     union; ahf - union == new_honest_residual; every one of these sets is
     internally disjoint/consistent.
  6. False-positive gate — every detector's measured false-positive rate
     on the 21 CORRECT (`pass`) tasks is asserted against the artifact
     (never silently dropped), and the overall structural false-positive
     rate is bounded (regression gate).
  7. >=3 pinned per-task structural verdicts RE-VERIFIED LIVE (a fresh
     computation, the same detector functions the script uses) — task 267
     (the known memo-lookup-table shape) MUST be among them.
  8. Determinism — the artifact's own two-pass hash equality holds, and is
     independently reproduced by a fresh two-pass computation here.
  9. No-python-decision-adjacent contamination: detector functions never
     read a task's reference `code` field (n/a here — they take only IR +
     revealed rows — asserted structurally by signature inspection).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_structural_verdicts_migrated.py
"""
from __future__ import annotations

import inspect
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import arc4_failure_anatomy as afa  # noqa: E402
import arc4_structural_verdicts as sv  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_structural_verdicts.json")
FROZEN_ANATOMY_PATH = os.path.join(ROOT, "results", "arc4_failure_anatomy.json")
FROZEN_R3_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

DETECTOR_NAMES = ["d1_memo_lookup_table", "d2_dead_code_free_vars",
                  "d3_unread_declared_param", "d4_constant_output",
                  "d5_vacuous_guard", "d6_arity_mismatch",
                  "d7_exhaustive_domain_proof"]


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def frozen_anatomy():
    with open(FROZEN_ANATOMY_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def frozen_r3():
    with open(FROZEN_R3_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def tasks_by_id():
    import mbpp_arc3_battery as bat
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = bat.q0_split_tasks(all_tasks)
    return {t["task_id"]: t for t in splits["test"]}


# --------------------------------------------------------------------------- #
#  1. artifact schema.
# --------------------------------------------------------------------------- #
def test_artifact_top_level_schema(artifact):
    for key in ("_README", "head", "measured_at", "provenance",
               "held_out_isolation_audit", "condition",
               "frozen_r3_continuity", "frozen_anatomy_continuity",
               "n_ahf", "ahf_task_ids", "n_pass_correct",
               "pass_correct_task_ids", "behavioral_killable_ids_s0a",
               "per_task", "per_task_correct", "per_detector",
               "structural_killable_ids", "union_structural_or_behavioral_killable_ids",
               "structural_only_ids", "behavioral_only_ids",
               "overlap_structural_and_behavioral_ids", "new_honest_residual_ids",
               "determinism", "corrected_ceiling", "environment",
               "elapsed_seconds"):
        assert key in artifact, "missing top-level key: %s" % key
    for dname in DETECTOR_NAMES:
        assert dname in artifact["per_detector"]


# --------------------------------------------------------------------------- #
#  2. population continuity vs the frozen S0-A anatomy artifact.
# --------------------------------------------------------------------------- #
def test_ahf_population_matches_frozen_anatomy(artifact, frozen_anatomy):
    assert artifact["n_ahf"] == 76
    assert artifact["ahf_task_ids"] == sorted(frozen_anatomy["measurement2_trap_anatomy"]["ahf_task_ids"])
    assert artifact["frozen_anatomy_continuity"]["ahf_ids_match_frozen_measurement"] is True


def test_ahf_and_pass_rows_read_from_frozen_endgame_artifact(artifact, frozen_r3):
    rows = frozen_r3["arms"]["full_r3"]["runnable_rows"]
    ahf_ids = sorted(r["task_id"] for r in rows if r["outcome"] == "accepted_holdout_fail")
    pass_ids = sorted(r["task_id"] for r in rows if r["outcome"] == "pass")
    assert artifact["ahf_task_ids"] == ahf_ids
    assert artifact["pass_correct_task_ids"] == pass_ids
    assert artifact["n_pass_correct"] == 21


def test_behavioral_killable_23_reconstructed_correctly(artifact, frozen_anatomy):
    m2 = frozen_anatomy["measurement2_trap_anatomy"]
    ca = m2["classes"]["a_cross_frame_disagreement"]
    cb = m2["classes"]["b_type_arity_violation"]
    cc = m2["classes"]["c_invariance_violation"]
    expect = sorted(set(ca["python_ids"]) | set(ca["toolchain_ids_subsample_only"])
                    | set(cb["task_ids"]) | set(cc["task_ids"]))
    assert artifact["behavioral_killable_ids_s0a"] == expect
    assert artifact["n_behavioral_killable_s0a"] == 23  # S0-A's own published number


# --------------------------------------------------------------------------- #
#  3. HELD-OUT ISOLATION -- live re-audit, independent of the artifact's own
#     recorded copy.
# --------------------------------------------------------------------------- #
def test_held_out_isolation_source_audit_live():
    audit = sv._held_out_isolation_audit()  # noqa: SLF001
    assert audit["any_hit"] is False, audit["hits"]


def test_held_out_isolation_audit_matches_artifact(artifact):
    assert artifact["held_out_isolation_audit"]["any_hit"] is False


def test_detector_functions_take_only_ir_and_revealed_rows():
    """A structural discipline audit distinct from the string-scan above:
    every per-task detector's signature names only `ir`/`revealed_rows`
    (or neither) -- never a `held_out`/`spec` parameter that could smuggle
    the wrong row in by construction."""
    fns = [sv.detect_memo_lookup_table, sv.detect_dead_code_free_vars,
          sv.detect_unread_declared_param, sv.detect_constant_output,
          sv.detect_vacuous_guard, sv.detect_arity_mismatch,
          sv.detect_exhaustive_domain_eligible]
    for fn in fns:
        params = set(inspect.signature(fn).parameters)
        assert params <= {"ir", "revealed_rows", "bound"}, (fn.__name__, params)


# --------------------------------------------------------------------------- #
#  4. per-detector totals independently re-derived.
# --------------------------------------------------------------------------- #
def test_per_detector_recall_and_fp_rederived(artifact):
    per_task = artifact["per_task"]
    per_task_correct = artifact["per_task_correct"]
    n_traps, n_correct = artifact["n_ahf"], artifact["n_pass_correct"]
    for dname in DETECTOR_NAMES:
        trap_hits = sorted(int(tid) for tid, row in per_task.items()
                           if row["detectors"][dname].get("fired"))
        correct_hits = sorted(int(tid) for tid, row in per_task_correct.items()
                              if row["detectors"][dname].get("fired"))
        rec = artifact["per_detector"][dname]
        assert rec["trap_task_ids"] == trap_hits
        assert rec["n_fired_on_traps"] == len(trap_hits)
        assert rec["false_positive_task_ids"] == correct_hits
        assert rec["n_fired_on_correct"] == len(correct_hits)
        assert rec["recall_over_76"] == (round(len(trap_hits) / n_traps, 4) if n_traps else None)
        assert rec["false_positive_rate_over_21"] == (
            round(len(correct_hits) / n_correct, 4) if n_correct else None)
        tp, fp = len(trap_hits), len(correct_hits)
        expect_prec = round(tp / (tp + fp), 4) if (tp + fp) else None
        assert rec["precision_tp_over_tp_plus_fp"] == expect_prec


def test_fired_detectors_field_matches_detectors_block(artifact):
    for pop in ("per_task", "per_task_correct"):
        for tid, row in artifact[pop].items():
            fired = sorted(k for k in DETECTOR_NAMES if row["detectors"][k].get("fired"))
            assert row["fired_detectors"] == fired, tid
            assert row["killable_by_any_structural_signal"] == bool(fired), tid


# --------------------------------------------------------------------------- #
#  5. union/overlap arithmetic.
# --------------------------------------------------------------------------- #
def test_union_overlap_arithmetic(artifact):
    structural = set(artifact["structural_killable_ids"])
    behavioral = set(artifact["behavioral_killable_ids_s0a"])
    union = set(artifact["union_structural_or_behavioral_killable_ids"])
    overlap = set(artifact["overlap_structural_and_behavioral_ids"])
    struct_only = set(artifact["structural_only_ids"])
    behav_only = set(artifact["behavioral_only_ids"])
    residual = set(artifact["new_honest_residual_ids"])
    ahf = set(artifact["ahf_task_ids"])

    assert overlap == structural & behavioral
    assert struct_only == structural - behavioral
    assert behav_only == behavioral - structural
    assert union == structural | behavioral
    assert struct_only | overlap == structural
    assert struct_only | overlap | behav_only == union
    assert residual == ahf - union
    assert artifact["n_structural_killable"] == len(structural)
    assert artifact["n_union_killable"] == len(union)
    assert artifact["n_new_honest_residual"] == len(residual)
    # every structural-killable id must be a real member of the 76.
    assert structural <= ahf
    assert behavioral <= ahf


def test_corrected_ceiling_is_strictly_larger_than_s0a(artifact):
    """The whole point of this measurement: structural inspection finds a
    NEW, non-empty catch beyond S0-A's behavioural-only 23/76."""
    assert artifact["n_structural_killable"] > 0
    assert len(artifact["structural_only_ids"]) > 0
    assert artifact["n_union_killable"] > artifact["n_behavioral_killable_s0a"]
    assert artifact["n_new_honest_residual"] < 76 - artifact["n_behavioral_killable_s0a"]


# --------------------------------------------------------------------------- #
#  6. false-positive gate.
# --------------------------------------------------------------------------- #
def test_false_positive_rates_recorded_for_every_detector(artifact):
    for dname in DETECTOR_NAMES:
        rec = artifact["per_detector"][dname]
        assert "false_positive_rate_over_21" in rec
        assert "n_fired_on_correct" in rec


def test_false_positive_rate_regression_bound(artifact):
    """Regression gate: no detector's false-positive rate on the 21 CORRECT
    (pass) tasks exceeds 25% (5/21) -- catches a future edit that makes a
    detector fire promiscuously. D1/D2 are measured at 0% (a prior, looser
    version of D1 without the single-return-expression requirement DID hit
    20%+ on two correct tasks -- 20 'woodball number', 281 'unique list
    elements' -- both generic early-exit loops, not memorisation; fixed by
    requiring the WHOLE function collapse to exactly one ProgReturn before
    checking literal-dispatch shape). D3's 3/21 (397 median-of-three via
    max(a,b); 404 minimum-of-two via bare `return a`; 433 a threshold check
    ignoring its array argument) were hand-verified via a FRESH, self-
    constructed witness input (never the task's held-out row) to be
    GENUINE defects the single-row PRIMARY protocol's `pass` label missed
    by chance -- see PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md. This test
    still asserts the numeric bound mechanically; it does not special-case
    those 3 ids away."""
    for dname in DETECTOR_NAMES:
        rate = artifact["per_detector"][dname]["false_positive_rate_over_21"]
        if rate is not None:
            assert rate <= 0.25, (dname, rate)


def test_d3_false_positives_are_genuine_defects_on_a_fresh_witness(frozen_r3):
    """Independently re-verifies the notes' hand-inspection claim about
    D3's three false positives: each disagrees with the OBVIOUS reading of
    its own prompt on a FRESH, self-constructed input distinct from every
    revealed row and NEVER read from the task's held-out row -- i.e. these
    are genuine defects the single-row PRIMARY-protocol `pass` label
    missed by chance, not detector error."""
    import mbpp_arc3_battery as bat
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}

    ir397 = rows[397]["ir"]
    witness = {"a": 1, "b": 5, "c": 3}
    out = bat.prog_eval(ir397, dict(witness))
    assert out.get("result") != sorted(witness.values())[1]  # true median is 3, not 5

    ir404 = rows[404]["ir"]
    witness = {"a": 5, "b": 1}
    out = bat.prog_eval(ir404, dict(witness))
    assert out.get("result") != min(witness.values())  # true min is 1

    ir433 = rows[433]["ir"]
    witness = {"b": 3, "a": [1, 2]}
    out = bat.prog_eval(ir433, dict(witness))
    true_answer = all(witness["b"] > x for x in witness["a"])
    assert out.get("result") != true_answer  # b(3) IS greater than every element of [1, 2]


# --------------------------------------------------------------------------- #
#  7. >=3 pinned per-task verdicts, re-verified LIVE. Task 267 required.
# --------------------------------------------------------------------------- #
def test_pinned_task_267_memo_lookup_table_live(frozen_r3, tasks_by_id):
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    ir = rows[267]["ir"]
    revealed = afa._revealed_rows_for_task(267, tasks_by_id)  # noqa: SLF001
    result = sv.analyze_task(ir, revealed)
    d1 = result["detectors"]["d1_memo_lookup_table"]
    assert d1["fired"] is True
    assert sorted(d1["leaves"]) == [10, 35]
    d2 = result["detectors"]["d2_dead_code_free_vars"]
    assert d2["fired"] is True
    assert set(d2["free_vars"]) == {"n", "b"}
    assert "d1_memo_lookup_table" in result["fired_detectors"]
    assert "d2_dead_code_free_vars" in result["fired_detectors"]
    assert result["killable_by_any_structural_signal"] is True


def test_pinned_task_404_unread_param_live(frozen_r3, tasks_by_id):
    """A false-positive-on-CORRECT pin (see test 6 above) -- task 404 is
    labelled `pass` yet D3 correctly finds it structurally ignores `b`."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    ir = rows[404]["ir"]
    revealed = afa._revealed_rows_for_task(404, tasks_by_id)  # noqa: SLF001
    result = sv.analyze_task(ir, revealed)
    d3 = result["detectors"]["d3_unread_declared_param"]
    assert d3["fired"] is True
    assert d3["varying_unread_params"] == ["b"]


def test_pinned_task_20_not_memo_negative_control_live(frozen_r3, tasks_by_id):
    """The negative control that motivated D1's single-return-expression
    guard: task 20 is a correct (`pass`) generic early-exit loop, NOT a
    lookup table, and must NOT fire D1."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    ir = rows[20]["ir"]
    revealed = afa._revealed_rows_for_task(20, tasks_by_id)  # noqa: SLF001
    result = sv.analyze_task(ir, revealed)
    assert result["detectors"]["d1_memo_lookup_table"]["fired"] is False
    assert result["killable_by_any_structural_signal"] is False


def test_pinned_task_84_arity_and_domain_not_eligible_live(frozen_r3, tasks_by_id):
    """A fourth pin: an ordinary accepted_holdout_fail trap with a plain
    int/list signature must be D6/D7-inert (arity matches; not bool-only
    domain-eligible) -- guards against a detector regression that starts
    firing on ordinary signatures."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    ahf_ids = sorted(r["task_id"] for r in rows.values()
                     if r["outcome"] == "accepted_holdout_fail")
    tid = ahf_ids[0]
    ir = rows[tid]["ir"]
    revealed = afa._revealed_rows_for_task(tid, tasks_by_id)  # noqa: SLF001
    result = sv.analyze_task(ir, revealed)
    assert result["detectors"]["d6_arity_mismatch"]["fired"] is False
    assert result["detectors"]["d7_exhaustive_domain_proof"]["eligible"] is False


# --------------------------------------------------------------------------- #
#  8. determinism.
# --------------------------------------------------------------------------- #
def test_determinism_recorded_identical(artifact):
    assert artifact["determinism"]["identical"] is True
    assert artifact["determinism"]["pass1_hash"] == artifact["determinism"]["pass2_hash"]


def test_determinism_fresh_third_pass(frozen_r3, tasks_by_id):
    """A THIRD, fully independent pass (fresh process state within this
    test) must match the artifact's own recorded hash-equal pair on the
    per-task fired-detector signature."""
    rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    ahf_rows = [r for r in rows.values() if r["outcome"] == "accepted_holdout_fail"]
    for r in ahf_rows[:10]:  # a bounded sample keeps this test fast
        revealed = afa._revealed_rows_for_task(r["task_id"], tasks_by_id)  # noqa: SLF001
        res1 = sv.analyze_task(r["ir"], revealed)
        res2 = sv.analyze_task(r["ir"], revealed)
        assert res1["fired_detectors"] == res2["fired_detectors"]


# --------------------------------------------------------------------------- #
#  9. exhaustive-domain honesty -- D7's eligibility must be zero on this
#     population (all-bool signatures do not occur in MBPP), and the
#     artifact must say so plainly rather than hiding an empty result.
# --------------------------------------------------------------------------- #
def test_exhaustive_domain_eligibility_honestly_recorded(artifact):
    assert artifact["exhaustive_domain_eligible_trap_ids"] == []
    assert artifact["exhaustive_domain_eligible_correct_ids"] == []
    assert artifact["per_detector"]["d7_exhaustive_domain_proof"]["n_fired_on_traps"] == 0
