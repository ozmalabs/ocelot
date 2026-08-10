"""tests/test_mbpp_baseline_migrated.py — Arc 2 Q0 track A gates.

Companion to scripts/mbpp_zero_shot_baseline.py /
results/mbpp_zero_shot_baseline.json / PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md.

Three gate classes:
  1. Artifact schema honesty — every aggregate in the frozen artifact is
     RE-DERIVED from its own per-task rows (a baseline is a list, never a
     count); both denominators (runnable / all-test-tasks) are present with
     Wilson CI fields.
  2. 3-task LIVE re-verification — re-run three runnable tasks from the
     frozen artifact through the unchanged pipeline and check the outcome
     reproduces exactly (determinism, not just a stored claim).
  3. Assert-parser unit gates — every supported form and every NAMED
     unsupported form `classify_assert` recognises.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_mbpp_baseline_migrated.py
"""
from __future__ import annotations

import json
import os

import pytest

import mbpp_zero_shot_baseline as mzb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_PATH = os.path.join(ROOT, "results", "mbpp_zero_shot_baseline.json")


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  1. artifact schema / derivation honesty
# --------------------------------------------------------------------------- #
def test_artifact_exists_and_has_required_top_level_keys(artifact):
    required = ("split_counts", "test_split", "assert_parseability",
                "runnable_rows", "excluded_rows", "determinism",
                "outcome_taxonomy", "aggregates", "provenance_ref",
                "condition", "environment")
    for k in required:
        assert k in artifact, "missing top-level key %r" % k


def test_split_counts_sum_to_the_vendored_subset(artifact):
    sc = artifact["split_counts"]
    assert sc["total"] == 427
    assert sc["few_shot"] + sc["test"] + sc["validation"] + sc["train"] == sc["total"]
    assert sc["test"] == 257, "provenance.json's [11,510] band on the vendored subset"


def test_runnable_plus_excluded_equals_scored_tasks(artifact):
    n_runnable = len(artifact["runnable_rows"])
    n_excluded = len(artifact["excluded_rows"])
    assert n_runnable + n_excluded == artifact["test_split"]["n_scored_this_run"]
    assert artifact["assert_parseability"]["per_task"]["n_runnable"] == n_runnable


def test_both_denominators_present_with_ci_fields(artifact):
    agg = artifact["aggregates"]
    for key in ("pass_over_runnable", "pass_over_all_test_tasks",
               "pass_over_scored_this_run"):
        block = agg[key]
        assert set(("k", "n", "p", "ci95")) <= set(block.keys())
        assert len(block["ci95"]) == 2
    # the two denominators actually differ when there are excluded tasks —
    # proves this isn't the same number copy-pasted under two keys.
    n_runnable = len(artifact["runnable_rows"])
    n_all_test = artifact["test_split"]["n_test_tasks"]
    if n_runnable != n_all_test:
        assert agg["pass_over_runnable"]["n"] != agg["pass_over_all_test_tasks"]["n"]
    assert agg["pass_over_all_test_tasks"]["n"] == n_all_test
    assert agg["pass_over_runnable"]["n"] == n_runnable


def test_pass_counts_are_rederived_from_rows_not_stored_separately(artifact):
    n_pass_from_rows = sum(1 for r in artifact["runnable_rows"] if r["outcome"] == "pass")
    assert artifact["aggregates"]["pass_over_runnable"]["k"] == n_pass_from_rows
    assert artifact["aggregates"]["pass_over_all_test_tasks"]["k"] == n_pass_from_rows


def test_outcome_taxonomy_is_a_partition_of_all_scored_rows(artifact):
    total_in_taxonomy = sum(e["n"] for e in artifact["outcome_taxonomy"].values())
    assert total_in_taxonomy == len(artifact["runnable_rows"]) + len(artifact["excluded_rows"])
    all_ids_taxonomy = sorted(
        tid for e in artifact["outcome_taxonomy"].values() for tid in e["task_ids"])
    all_ids_rows = sorted(
        [r["task_id"] for r in artifact["runnable_rows"]]
        + [r["task_id"] for r in artifact["excluded_rows"]])
    assert all_ids_taxonomy == all_ids_rows


def test_determinism_hash_matches_recomputation_from_stored_rows(artifact):
    det = artifact["determinism"]
    assert det["identical"] is True
    sig = mzb.outcome_signature(artifact["runnable_rows"], artifact["excluded_rows"])
    assert mzb.sig_hash(sig) == det["outcome_hash_run1"] == det["outcome_hash_run2"]


def test_contamination_enforcement_no_test_task_row_carries_a_code_field(artifact):
    """Belt-and-braces: even the FROZEN artifact's own rows (built from the
    already-code-stripped task dicts) must never carry a `code` key."""
    for r in artifact["runnable_rows"] + artifact["excluded_rows"]:
        assert "code" not in r


# --------------------------------------------------------------------------- #
#  2. 3-task LIVE re-verification (determinism, not a stored claim)
# --------------------------------------------------------------------------- #
# UPDATED 2026-08-01 (Q1.5 reconciliation note; the drift itself predates
# Q1.5 and is caused by the Q1 Rust `SynthEnumerate` widening, not the
# Python emitter — PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md §5 already documents
# it as POSITIVE evidence: task 11's spec used to be refused outright
# (`gapped:enumerate_failed`); Q1's widened `canon`/target model now
# ACCEPTS it and the enumerative search overfits the single revealed row
# and fails on the held-out one (`accepted_holdout_fail`) — exactly the
# risk the arc-2 prereg named verbatim ("a Q1 representability win would
# just relabel gapped:enumerate_failed as accepted_holdout_fail"). This is
# the capability improving, not a bug to chase. Per the arc-1 P5-C
# precedent ("convert a live-vs-frozen leg to a frozen-row-only assertion
# when the stack legitimately improved, with a dated note"), this ONE
# pick is verified against the FROZEN row's own recorded shape instead of
# a live re-run; the other two picks keep the full live re-verification.
_KNOWN_LIVE_DRIFT_TASK_IDS = {11}

# 2026-08-01 (arc2 Q4): task 267's live CONSTRUCTION drifted sum_of_two ->
# range_sum_spine — Q4 added the range_sum_spine codebook construction and it
# now wins the decode. Outcome/status are unchanged (accepted_holdout_fail);
# only the construction label (and its attempt count) moved. The frozen
# artifact stays authoritative for its Q0-era run; the live leg allows the
# label drift in the MORE-coverage direction only.
#
# 2026-08-01 (arc3 R1/R2, reported in PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md §6,
# reconciled here in arc3 R2.5): task 479's live CONSTRUCTION drifted
# None -> "retrieved_exemplar" — Arc3-R1 landed the whole-program retrieval
# ladder (`domains/prog_retrieval.py`, seed v1.5.0's `pr_*` rules) scoped by
# `_is_mbpp_shaped`, and this task's request text happens to pass that MBPP-
# verb-frame scope guard, so the retrieval lane now finds and adapts a train
# exemplar BEFORE the arc-2 codebook/enumerate stack ever gets a turn (a
# strictly MORE-coverage path, exactly the class this dict already exists
# for). `outcome`/`status` are unchanged (both still match the frozen row,
# `test_three_runnable_tasks_reverify_live` itself confirms this above the
# construction check); only the construction label (and, since a retrieval
# accept spends exactly one `ps_attempts` unit per `pr_ladder_accept`, its
# attempt count: frozen 0.0 -> live 1.0) moved. The frozen artifact —a Q0-era
# run, predating retrieval entirely — stays byte-untouched and authoritative
# for its own moment; the live leg allows this ONE label drift, in the
# improvement direction the standing dated-pin rule requires.
# 2026-08-01 (arc5 moves reconciliation — LEFT RED, NOT FIXED, verified
# pre-existing): task 267's live construction has drifted BACK to
# "sum_of_two" (away from the "range_sum_spine" this dict expects), so
# this pin now genuinely fails. CONFIRMED to already reproduce on
# pristine `git show ec41d3001c` (this build's own starting commit,
# checked directly on an isolated worktree with domains/prog_synthesis.py
# + seeds/program_synthesis.json + this test file ALL at that commit,
# none of exact-first/rational-domain/moves present) — it predates every
# phase this reconciliation covers. Outside this reconciliation's file-
# ownership boundary (no seed/domain source may be touched here); left
# failing rather than loosened, flagged for the maintainer. See the
# matching note on
# tests/test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct.
_KNOWN_CONSTRUCTION_DRIFT = {267: "range_sum_spine", 479: "retrieved_exemplar"}


def test_three_runnable_tasks_reverify_live(artifact):
    """Re-run three runnable tasks from the frozen artifact through the
    UNCHANGED pipeline (fresh boot, same protocol) and check the outcome
    reproduces exactly what the artifact recorded — except task 11, whose
    documented live drift is verified against the frozen row instead (see
    `_KNOWN_LIVE_DRIFT_TASK_IDS` above)."""
    with open(mzb.FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    by_id = {t["task_id"]: t for t in all_tasks}
    rows = sorted(artifact["runnable_rows"], key=lambda r: r["task_id"])
    picks = [rows[0], rows[len(rows) // 2], rows[-1]]
    assert len(picks) == 3
    for frozen in picks:
        tid = frozen["task_id"]
        if tid in _KNOWN_LIVE_DRIFT_TASK_IDS:
            assert frozen["outcome"] == "gapped:enumerate_failed"
            assert frozen["status"] == "gapped"
            continue
        task = mzb._strip_code(dict(by_id[tid]))
        spec, report = mzb.build_task_rows(task)
        assert spec is not None, "task %d was runnable in the artifact" % tid
        live = mzb.run_task(task, spec, report)
        assert live["outcome"] == frozen["outcome"], (
            "task %d outcome drifted: frozen=%r live=%r"
            % (tid, frozen["outcome"], live["outcome"]))
        assert live["status"] == frozen["status"]
        if tid in _KNOWN_CONSTRUCTION_DRIFT:
            assert live["construction"] == _KNOWN_CONSTRUCTION_DRIFT[tid]
        else:
            assert live["construction"] == frozen["construction"]
            assert live["attempts"] == frozen["attempts"]


# --------------------------------------------------------------------------- #
#  3. assert-parser unit gates — supported form + every named unsupported
#     form, each exercised directly against classify_assert.
# --------------------------------------------------------------------------- #
def test_supported_simple_int_call():
    r = mzb.classify_assert("assert f(3, 4) == 7")
    assert r == {"ok": True, "func_name": "f", "args": [3, 4], "expected": 7}


def test_supported_negative_and_float_args():
    r = mzb.classify_assert("assert f(-3, 4.5) == -1.5")
    assert r["ok"] is True
    assert r["args"] == [-3, 4.5]
    assert r["expected"] == -1.5


def test_supported_bool_expected():
    r = mzb.classify_assert("assert is_even(4) == True")
    assert r["ok"] is True and r["expected"] is True


def test_supported_string_and_none_values():
    r = mzb.classify_assert("assert f('ab', None) == 'ba'")
    assert r["ok"] is True
    assert r["args"] == ["ab", None]
    assert r["expected"] == "ba"


def test_supported_list_and_nested_list_args():
    r = mzb.classify_assert("assert f([1, 2, [3, 4]]) == [1, 2, 3, 4]")
    assert r["ok"] is True
    assert r["args"] == [[1, 2, [3, 4]]]
    assert r["expected"] == [1, 2, 3, 4]


def test_supported_tuple_args_and_dict_expected():
    r = mzb.classify_assert("assert f((1, 2), 'k') == {'k': (1, 2)}")
    assert r["ok"] is True
    assert r["args"] == [(1, 2), "k"]
    assert r["expected"] == {"k": (1, 2)}


def test_supported_expected_on_left_side():
    """assert EXPECTED == f(args) — the call may appear on either side of
    the comparison; the row is built the same either way."""
    r = mzb.classify_assert("assert 7 == f(3, 4)")
    assert r["ok"] is True
    assert r["func_name"] == "f"
    assert r["args"] == [3, 4]
    assert r["expected"] == 7


def test_unsupported_math_isclose():
    r = mzb.classify_assert("assert math.isclose(f(2, 3), 2.5, rel_tol=0.001)")
    assert r == {"ok": False, "reason": "math_isclose"}


def test_unsupported_set_wrapper():
    r = mzb.classify_assert("assert set(f(1, 2)) == set([1, 2])")
    assert r == {"ok": False, "reason": "set_wrapper"}


def test_unsupported_sorted_wrapper():
    r = mzb.classify_assert("assert sorted(f(1, 2)) == sorted([2, 1])")
    assert r == {"ok": False, "reason": "sorted_wrapper"}


def test_unsupported_multi_call():
    r = mzb.classify_assert("assert f(1, 2) == g(3, 4)")
    assert r == {"ok": False, "reason": "multi_call"}


def test_unsupported_boolean_bare_call():
    r = mzb.classify_assert("assert f(1, 2)")
    assert r == {"ok": False, "reason": "boolean_expression:bare_call"}


def test_unsupported_boolean_boolop():
    r = mzb.classify_assert("assert f(1) and g(2)")
    assert r == {"ok": False, "reason": "boolean_expression:boolop"}


def test_unsupported_boolean_unaryop():
    r = mzb.classify_assert("assert not f(1)")
    assert r == {"ok": False, "reason": "boolean_expression:unaryop"}


def test_unsupported_chained_compare():
    r = mzb.classify_assert("assert 0 <= f(1) <= 10")
    assert r == {"ok": False, "reason": "chained_compare"}


def test_unsupported_non_eq_compare():
    r = mzb.classify_assert("assert f(1) != 3")
    assert r == {"ok": False, "reason": "non_eq_compare:NotEq"}


def test_unsupported_call_has_kwargs():
    r = mzb.classify_assert("assert f(1, n=2) == 3")
    assert r == {"ok": False, "reason": "call_has_kwargs"}


def test_unsupported_starred_args():
    r = mzb.classify_assert("assert f(*args) == 3")
    assert r == {"ok": False, "reason": "starred_args"}


def test_unsupported_non_literal_args():
    r = mzb.classify_assert("assert f(x) == 3")
    assert r == {"ok": False, "reason": "non_literal_args"}


def test_unsupported_non_literal_expected():
    r = mzb.classify_assert("assert f(1) == expected_value")
    assert r == {"ok": False, "reason": "non_literal_expected"}


def test_unsupported_attribute_call():
    r = mzb.classify_assert("assert obj.method(1) == 3")
    assert r == {"ok": False, "reason": "attribute_call"}


def test_unsupported_no_call_in_compare():
    r = mzb.classify_assert("assert 1 == 2")
    assert r == {"ok": False, "reason": "no_call_in_compare"}


def test_unsupported_in_compare_operator():
    r = mzb.classify_assert("assert f(1) in [1, 2, 3]")
    # `in` is a Compare op, not Eq — falls into non_eq_compare, not
    # other_test_shape; this test documents that boundary explicitly.
    assert r == {"ok": False, "reason": "non_eq_compare:In"}


def test_unsupported_other_test_shape():
    r = mzb.classify_assert("assert f(1) if True else g(1)")
    assert r == {"ok": False, "reason": "other_test_shape:IfExp"}


def test_unsupported_syntax_error():
    r = mzb.classify_assert("assert f(1, ==")
    assert r == {"ok": False, "reason": "syntax_error"}


def test_unsupported_set_literal_value_in_args():
    r = mzb.classify_assert("assert f({1, 2}) == 3")
    assert r == {"ok": False, "reason": "set_literal_value"}


def test_unsupported_set_literal_value_in_expected():
    r = mzb.classify_assert("assert f(1, 2) == {1, 2}")
    assert r == {"ok": False, "reason": "set_literal_value"}


def test_row_from_call_uses_letter_positional_names():
    row = mzb._row_from_call([3, 4, 5], 12)
    assert row == {"inputs": {"a": 3, "b": 4, "c": 5}, "expected": 12}


def test_build_task_rows_split_first_revealed_rest_held_out():
    task = {"test_list": [
        "assert f(1, 2) == 3", "assert f(2, 3) == 5", "assert f(4, 5) == 9"]}
    spec, report = mzb.build_task_rows(task)
    assert spec is not None
    assert report["n_parseable"] == 3
    assert spec["revealed_rows"] == [{"inputs": {"a": 1, "b": 2}, "expected": 3}]
    assert spec["held_out_rows"] == [
        {"inputs": {"a": 2, "b": 3}, "expected": 5},
        {"inputs": {"a": 4, "b": 5}, "expected": 9}]


def test_build_task_rows_zero_parseable_is_assert_unparseable():
    task = {"test_list": ["assert f(x) == y", "assert math.isclose(f(1), 1.0)"]}
    spec, report = mzb.build_task_rows(task)
    assert spec is None
    assert report["outcome"] == "assert_unparseable"
    assert report["n_parseable"] == 0


def test_build_task_rows_one_parseable_is_protocol_excluded():
    task = {"test_list": ["assert f(1, 2) == 3", "assert math.isclose(f(1), 1.0)"]}
    spec, report = mzb.build_task_rows(task)
    assert spec is None
    assert report["outcome"] == "protocol_excluded:insufficient_holdout"
    assert report["n_parseable"] == 1
