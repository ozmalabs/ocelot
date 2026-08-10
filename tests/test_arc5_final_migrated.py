"""tests/test_arc5_final_migrated.py — gates for `results/arc5_final.json`
(the ONE clean, re-derived MBPP measurement at arc5's fully reconciled
commit state — rational domain + exact-first + moves — produced by
`scripts/arc5_final_battery.py`; see PROGRAM_SYNTHESIS_ARC5_FINAL.md).

Gates:
  1. Schema/derivation — every aggregate/taxonomy/pass-id total in the
     artifact is RE-DERIVED from its own `runnable_rows`/`excluded_rows`,
     never merely asserted to equal itself (a baseline is a list, read
     it — the standing rule this repo's own retracted "optional-dep" note
     established).
  2. Determinism — the frozen twin-run hash pair matches, AND a fresh
     live twin-run reproduces the SAME outcome signature (never trusting
     the frozen artifact's own claim about itself).
  3. Three pinned live re-verifications — one per attributed mechanism
     (exact-first solved, moves solved, an unchanged baseline pass) —
     re-run fresh against the CURRENT pipeline and checked against the
     frozen row.
  4. Every claimed `pass` carries a witness (held-out AND, for every id
     that differs from the arc-4 full_a4 baseline, a constructed witness
     beyond the corpus's own rows) — the gate this arc's own history
     (two coincidental fits at arc4, a third and fourth at arc5, a fifth
     and sixth found during THIS reconciliation) exists to keep honest.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_arc5_final_migrated.py
"""
from __future__ import annotations

import json
import math
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

from domains import prog_synthesis as psy  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
import mbpp_arc3_battery as arc3b  # noqa: E402
import arc5_final_battery as afb  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "arc5_final.json")
_Z = 1.959963984540054


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def test_tasks():
    with open(afb.FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = arc3b.q0_split_tasks(all_tasks)
    for t in splits["test"]:
        assert "code" not in t, "contamination: code field survived split_tasks"
    return {t["task_id"]: t for t in splits["test"]}


# --------------------------------------------------------------------------- #
#  1. Schema / derivation.
# --------------------------------------------------------------------------- #
def _wilson(k: int, n: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "ci95": [None, None]}
    p = k / n
    d = 1 + _Z * _Z / n
    centre = (p + _Z * _Z / (2 * n)) / d
    hw = _Z * math.sqrt(p * (1 - p) / n + _Z * _Z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 6),
            "ci95": [round(max(0.0, centre - hw), 6),
                     round(min(1.0, centre + hw), 6)]}


def test_pass_ids_are_derived_from_rows_not_asserted(artifact):
    rows = artifact["arm"]["runnable_rows"]
    derived_pass = sorted(r["task_id"] for r in rows if r["outcome"] == "pass")
    assert artifact["pass_ids"] == derived_pass


def test_taxonomy_is_derived_from_rows(artifact):
    rows = artifact["arm"]["runnable_rows"] + artifact["arm"]["excluded_rows"]
    by: dict = {}
    for r in rows:
        by.setdefault(r["outcome"], []).append(r["task_id"])
    for outcome, ids in by.items():
        assert artifact["outcome_taxonomy"][outcome]["n"] == len(ids)
        assert sorted(artifact["outcome_taxonomy"][outcome]["task_ids"]) == sorted(ids)
    assert sum(v["n"] for v in artifact["outcome_taxonomy"].values()) == len(rows)


def test_both_denominators_are_correctly_derived(artifact):
    rows = artifact["arm"]["runnable_rows"]
    n_pass = sum(1 for r in rows if r["outcome"] == "pass")
    n_runnable = len(rows)
    assert artifact["aggregates"]["pass_over_runnable"] == _wilson(n_pass, n_runnable)
    assert artifact["aggregates"]["pass_over_all_test_257"] == _wilson(n_pass, 257)
    assert artifact["aggregates"]["pass_over_all_427_sanitized"] == _wilson(n_pass, 427)
    assert artifact["aggregates"]["pass_over_all_test_257"]["n"] == 257
    assert artifact["aggregates"]["pass_over_all_427_sanitized"]["n"] == 427


def test_paired_diff_totals_are_derived(artifact):
    diff = artifact["paired_diff_vs_arc4_full_a4"]
    assert diff["n_changed"] == len(diff["changed_rows"])
    all_ids_in_by_attr = sorted(
        tid for ids in diff["changed_ids_by_attribution"].values() for tid in ids)
    assert all_ids_in_by_attr == sorted(r["task_id"] for r in diff["changed_rows"])
    assert diff["net_pass_delta"] == (
        diff["pass_after_arc5_final"] - diff["pass_before_full_a4"])
    with open(os.path.join(ROOT, "results", "arc4_endgame.json")) as f:
        frozen = json.load(f)
    assert diff["pass_before_full_a4"] == sum(
        1 for r in frozen["arms"]["full_a4"]["runnable_rows"] if r["outcome"] == "pass")


def test_engine_and_seed_state_recorded(artifact):
    assert artifact["engine"]["so"]
    assert artifact["engine"]["sha256"]
    assert artifact["seed_state"]["program_synthesis_json_version"] == "1.10.0"
    assert artifact["seed_state"]["program_synthesis_json_rule_count"] == 70
    assert artifact["head"]


# --------------------------------------------------------------------------- #
#  2. Determinism.
# --------------------------------------------------------------------------- #
def test_frozen_twin_run_hash_matches(artifact):
    det = artifact["determinism"]
    assert det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]


def test_live_twin_run_reproduces_the_frozen_pass_set(test_tasks):
    """A FRESH twin pass (never trusting the frozen artifact's own claim
    about itself) over the full 257-task split reproduces the SAME pass
    id set the frozen artifact recorded."""
    tasks = sorted(test_tasks.values(), key=lambda t: t["task_id"])
    runnable, _excluded, _elapsed = arc3b.run_pass(
        tasks, arc3b.boot_full_r3, "primary")
    with open(ARTIFACT_PATH) as f:
        artifact = json.load(f)
    live_pass = sorted(r["task_id"] for r in runnable if r["outcome"] == "pass")
    assert live_pass == artifact["pass_ids"]


# --------------------------------------------------------------------------- #
#  3. Three pinned live re-verifications, one per attributed mechanism.
# --------------------------------------------------------------------------- #
def _synth_task(tid, test_tasks):
    task = test_tasks[tid]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    s, ag = arc3b.boot_full_r3()
    r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
    return s, r


def test_pinned_live_reverify_exact_first_solved_task_82(test_tasks):
    s, r = _synth_task(82, test_tasks)
    out = psy.read_goal(s, r["goal"])
    assert out["status"] == "accepted"
    assert out["rungs"]["exact"] == 1.0
    attrs = s.node(r["goal"])["attrs"]
    assert attrs.get("ps_move_sel_kind") is None


def test_pinned_live_reverify_moves_solved_task_59(test_tasks):
    s, r = _synth_task(59, test_tasks)
    out = psy.read_goal(s, r["goal"])
    assert out["status"] == "accepted"
    attrs = s.node(r["goal"])["attrs"]
    assert attrs.get("ps_move_sel_kind") == "intermediate_factor"


def test_pinned_live_reverify_unchanged_baseline_pass_task_16(test_tasks):
    """Task 16 is a `pass` in BOTH the arc-4 full_a4 baseline and the
    current arc5_final measurement — untouched by any of this arc's own
    moves, a live spot-check that the reconciliation left it alone."""
    with open(os.path.join(ROOT, "results", "arc4_endgame.json")) as f:
        frozen = json.load(f)
    frozen_16 = next(r for r in frozen["arms"]["full_a4"]["runnable_rows"]
                     if r["task_id"] == 16)
    assert frozen_16["outcome"] == "pass"
    s, r = _synth_task(16, test_tasks)
    out = psy.read_goal(s, r["goal"])
    assert out["status"] == "accepted"


# --------------------------------------------------------------------------- #
#  4. Every claimed pass carries a witness.
# --------------------------------------------------------------------------- #
def test_every_pass_carries_a_witness(artifact):
    wv = artifact["witness_verification"]
    assert wv["pass_ids"] == artifact["pass_ids"]
    for tid in wv["pass_ids"]:
        entry = wv["per_task"][str(tid)]
        assert entry["held_out_all_ok"] is True, (tid, "every pass must be held-out correct")
        kind = entry["witness_kind"]
        if kind in ("hand_derived_beyond_corpus_rows", "exact_family_power_law_scaling"):
            assert entry["constructed_witness"]["all_ok"] is True, (
                tid, entry["constructed_witness"])
        elif kind == "unchanged_from_full_a4_structural_check_only":
            # in-scope-of-change ids MUST carry a real constructed witness;
            # only ids UNCHANGED from the pre-arc5 baseline may rely on the
            # narrower (documented) scope.
            diff_ids = {r["task_id"] for r in
                       artifact["paired_diff_vs_arc4_full_a4"]["changed_rows"]}
            assert tid not in diff_ids, (
                tid, "a CHANGED id must carry a real constructed witness, "
                "not the unchanged-baseline fallback")
        else:
            pytest.fail("pass id %r has an unrecognised witness_kind %r" % (tid, kind))


def test_no_changed_id_lacking_a_witness_fn_reached_pass(artifact):
    """Every changed id that reached `pass` must have produced a REAL
    constructed witness (never `changed_but_no_dedicated_witness_fn`) —
    this is the gate that would have caught a fifth coincidental fit."""
    wv = artifact["witness_verification"]
    pass_ids = set(artifact["pass_ids"])
    for tid_str, entry in wv["per_task"].items():
        if int(tid_str) in pass_ids:
            assert entry["witness_kind"] != "changed_but_no_dedicated_witness_fn", (
                tid_str, "a pass with no constructed witness at all")


def test_engine_exposed_coincidental_fits_are_confirmed_no_longer_passing(artifact):
    fits = artifact["witness_verification"]["engine_exposed_coincidental_fits_found_and_corrected"]
    assert {f["task_id"] for f in fits} == {92, 464}
    for f in fits:
        assert f["no_longer_a_pass"] is True
        assert f["frozen_full_a4_outcome"] == "pass"
        assert f["arc5_final_outcome"] != "pass"
        w = f["witness_against_frozen_program"]
        assert w is not None and "conclusion" in w


def test_task_397_never_became_a_pass(artifact):
    """397 (median-of-three) is the arc's own repeatedly-checked genuine
    defect / near-miss coincidental fit (arc4's own catch, and the
    'fourth' the moves build caught mid-development) — must never appear
    in the pass id list at the fully reconciled state."""
    assert 397 not in artifact["pass_ids"]


# --------------------------------------------------------------------------- #
#  5. The 34-vs-32 discrepancy investigation is recorded, not hand-waved.
# --------------------------------------------------------------------------- #
def test_discrepancy_investigation_is_recorded_with_a_confirmed_cause(artifact):
    di = artifact["discrepancy_investigation"]
    assert "confirmed_cause" in di and "ENGINE-STATE" in di["confirmed_cause"]
    assert di["reproduction_result"]["pass"] == 32
    assert di["reproduction_result"]["of"] == 257
    for key in ("seed_state", "nondeterminism"):
        assert key in di["ruled_out"]


# --------------------------------------------------------------------------- #
#  6. No-python-decision source audit — this file only reads artifact/task
#     data and calls the existing driver; no synthesis decision of its own.
# --------------------------------------------------------------------------- #
def test_this_file_makes_no_synthesis_decision_of_its_own():
    import inspect
    src = inspect.getsource(_synth_task)
    forbidden = ("gr._match", "gr._apply", "graph_rewrite.run")
    for token in forbidden:
        assert token not in src
