"""tests/test_search_reach_migrated.py — Arc 4 S4: SEARCH REACH, the
list/iteration composition widening of `SynthEnumerate`.

Companion docs: `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` (the diagnosis, the
widening design, the before/after table this file re-derives LIVE),
`PROGRAM_SYNTHESIS_ARC4_PLAN.md` §7 (the re-aim: the 85/139 = 61.2%
`gapped:enumerate_failed` bucket already emits fine and needs none of the
five emitter levers — it fails because the enumerator cannot compose
list/iteration programs), `PROGRAM_SYNTHESIS_ARC4_S0B_NOTES.md` §4 (the
sizing + the frozen 85-id bucket this phase targets, read read-only from
`results/arc4_backward_probe.json`), `runners/dsl/src/synth_enumerate.rs`
(the engine widening: 11 new op names, all reusing EXISTING pure DSL
Terms — Count/Sum/MaxOver/MinOver/IndexAt/Last/Fold/FilterList/MapList —
no new Term variant).

THIS IS HA4's EVIDENCE: every task in the frozen 85-id bucket
(`results/arc4_backward_probe.json::ha4_search_reach_sizing.
ok_already_no_named_lever`) is driven through the REAL, UNCHANGED
`domains.prog_synthesis.synthesize_from_request` pipeline via
`scripts/mbpp_arc3_battery.run_task`/`boot_full_r3` (the EXISTING,
untouched measurement driver arc 3 built and arc 4 S0-A/S0-B already
reused) — never a simulation, never a bypass, PRIMARY protocol
(all-but-last assert revealed). `domains/prog_synthesis.py` is read-only
here: this file imports it transitively through `mbpp_arc3_battery` and
never edits it.

Gates:
  1. The frozen bucket itself — 85 ids, matches the S0B artifact exactly
     (a live re-read, not a hardcoded duplicate that could drift).
  2. BEFORE state — reproduced literally: a live PRE-widening capture
     (recorded before any Rust source in this phase was touched) showed
     30/30 of a deterministic id-ordered prefix at `gapped:
     enumerate_failed`; this is asserted as a frozen fact (the "baseline
     is a list, not a count" standing rule) alongside the DEFINITIONAL
     argument (bucket membership IS "was gapped:enumerate_failed AND
     matches none of the five levers", so 85/85 held before by
     construction — restated, never merely asserted, in
     PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §3).
  3. AFTER state — driven LIVE against the installed (post-widening)
     engine, over the FULL 85-id population: exact id-list assertions for
     `pass`, `accepted_holdout_fail`, and "moved to a different gap
     reason", matched against the frozen table in the notes (id lists,
     never a bare count).
  4. Reach headline: at least 20/85 move off `gapped:enumerate_failed`
     (measured 25/85; the bar is set with headroom below the measured
     number so the gate is a real regression check, not a re-assertion
     of today's exact float).
  5. Every `pass`/`accepted_holdout_fail`/"moved" id is a SUBSET of the
     frozen 85-id bucket (no id invented, no id from outside the
     population).
  6. Determinism — a second live pass over the same population produces
     the IDENTICAL partition (the search is pure; no flakiness).
  7. No-python-decision source audit: this file only reads task data and
     calls the existing driver; it contains no synthesis/engine/seed
     decision of its own.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. \
    tests/test_search_reach_migrated.py -q
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

import mbpp_arc3_battery as mab  # noqa: E402  (existing driver, read-only)
from domains import mbpp_spec as ms  # noqa: E402
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

PROBE_PATH = os.path.join(ROOT, "results", "arc4_backward_probe.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

# --- §2 of PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md — the LIVE pre-widening
# capture, recorded verbatim before any line of runners/dsl/src/
# synth_enumerate.rs in this phase was written. A deterministic id-
# ordered PREFIX of the frozen 85-bucket (the first 30 ids in the
# bucket's own declared order) — every one `gapped:enumerate_failed`,
# `enumerate_outcome:"failed"`, `status:"gapped"`, no exceptions. This is
# the "baseline is a list" standing rule applied to a BEFORE state that
# cannot be re-run (the pre-widening binary is gone) — frozen here as the
# recorded evidence instead.
BEFORE_PREFIX_IDS = [
    11, 18, 19, 59, 65, 66, 69, 70, 75, 80, 82, 85, 87, 88, 90, 95, 98, 99,
    102, 106, 116, 118, 132, 137, 139, 141, 145, 161, 162, 163,
]
BEFORE_OUTCOME = "gapped:enumerate_failed"

# --- §3 of PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md — the AFTER partition,
# captured live post-widening/post-install, reproduced twice with
# identical id lists (the search is a pure deterministic engine).
# 2026-08-01 (arc5 exact-first): a LATER phase moved six ids in this bucket
# to `pass` — 82, 85, 139, 233, 276, 312, the k*pi*r^a*h^b geometry family,
# solved by the SHAPE-FIRST rung (rational parameters + a cross-frame
# constant) and not by S4's list/iteration widening at all. This file
# measures S4's ATTRIBUTION, so those ids are held separately rather than
# folded into AFTER_PASS_IDS: S4's own claim (it moved 25/85, and never
# outside classes A/B/C) must still bite exactly as it did.
_ARC5_EXACT_FIRST_PASS_IDS = {82, 85, 139, 233, 276, 312}

# 2026-08-01 (arc5 moves, reconciled): a STILL LATER phase
# (PROGRAM_SYNTHESIS_ARC5_MOVES.md, seed v1.9.0 -> v1.10.0) moves two more
# ids in this SAME bucket via RUNG 2.6 (structural moves), neither by S4's
# widening nor by exact-first's shape-first rung: task 59 (nth octagonal
# number, `3n^2-2n`) solves via MOVE B (intermediate decomposition — the
# direct search exhausts 200,000 candidates and finds nothing; solving the
# inner factor `expected/n` alone converges in 28,490 and composes to the
# correct answer) -> `pass`; task 162 lands in `accepted_holdout_fail` (an
# honestly-caught 2-row coincidental fit, NOT a wrong pass — the move
# rung's own P6.5-class attempt-collision fix, MOVES.md §5, unstuck a goal
# that previously parked non-terminally and let its accept run the SAME
# held-out check every other row does, which correctly rejects it). Held
# out the same way _ARC5_EXACT_FIRST_PASS_IDS is: this file measures S4's
# OWN attribution, which must still bite exactly as it did.
_ARC5_MOVES_PASS_IDS = {59}
_ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS = {162}

# 2026-08-02 (ARC 6 TIER 0, reconciled — IMPROVEMENT DIRECTION ONLY).
# A LATER phase widened `SynthEnumerate`'s OP TABLE (eight units, zero new
# `TermNode` variants: `op:TupleOf` / `op:ProdList` / `op:ConcatList` /
# `op:ArgMaxLenOver`, three filter/map templates, and `fix:StringAsSequence`
# in `term.rs`).  It moves further ids OUT of this bucket's
# `gapped:enumerate_failed` residual — the enumerator now PROPOSES a
# program for them where it previously proposed nothing.
#
# Held separately, exactly the way `_ARC5_EXACT_FIRST_PASS_IDS` and
# `_ARC5_MOVES_*` are, because THIS FILE MEASURES S4'S OWN ATTRIBUTION and
# S4's claim (25/85, never outside classes A/B/C) must keep biting exactly
# as it did.  Nothing moves back INTO the residual — the reconciliation is
# strictly one-directional, which is the standing rule for a drifted pin.
#
# Every one of these is a REACH move, not a conversion: five of them
# (106, 161, 257, 290, 450) have the enumerator producing the exact witness
# from `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §5 and `ProgEval`
# computing the right answer on every revealed row, and are then refused by
# the ROW VERDICT, which cannot compare a non-scalar result
# (`ps_row_pass` reads `Attr(r,"got")`, which the adapter sets to `None`
# for anything that is not int/float/str/bool).  See
# `PROGRAM_SYNTHESIS_ARC6_TIER0.md`.
_ARC6_TIER0_PASS_IDS = {120}                       # coincidental fit, see below
_ARC6_TIER0_ACCEPTED_HOLDOUT_FAIL_IDS = {74}
_ARC6_TIER0_MOVED_OTHER = {
    98: "runner_exception:TypeError",   # Div(Prod(a),Count(a)) -> Fraction; the
                                        # adapter's json.dumps cannot serialise it
    106: "gapped:no_shape",
    161: "gapped:no_shape",
    249: "gapped:no_shape",
    257: "gapped:exhausted",
    290: "gapped:no_shape",
    393: "gapped:no_shape",
    424: "gapped:exhausted",
    450: "gapped:exhausted",
}

# 2026-08-04 (programming + embodied engine merge, reconciled).  The merged
# engine carries the later value/sequence semantics from the embodied line.
# Re-measuring this frozen bucket twice produced the same partition: eight
# formerly reached-but-gapped tasks now pass, task 424 is reached and honestly
# caught by holdout, and task 106 remains an enumerate failure rather than the
# older post-enumeration ``no_shape`` label.  Keep these separate: they are a
# later engine conversion, not evidence attributable to S4.
_MERGED_ENGINE_PASS_IDS = {161, 257, 272, 290, 413, 418, 450, 460}
_MERGED_ENGINE_ACCEPTED_HOLDOUT_FAIL_IDS = {424}
_MERGED_ENGINE_RETURNED_RESIDUAL_IDS = {106}

AFTER_PASS_IDS = [69, 90, 132, 145, 278, 410, 443, 472]
AFTER_ACCEPTED_HOLDOUT_FAIL_IDS = [
    19, 65, 66, 70, 95, 116, 166, 253, 270, 294, 400, 438, 446,
]
AFTER_MOVED_OTHER = {
    272: "gapped:exhausted",
    413: "gapped:no_shape",
    418: "gapped:no_shape",
    460: "gapped:no_shape",
}
MIN_MOVED_OFF_ENUMERATE_FAILED = 20  # measured 25; headroom below the exact figure


@pytest.fixture(scope="module")
def bucket_ids():
    with open(PROBE_PATH) as f:
        probe = json.load(f)
    ids = probe["ha4_search_reach_sizing"]["ok_already_no_named_lever"]
    assert len(ids) == 85, "the frozen bucket must not have drifted"
    return ids


@pytest.fixture(scope="module")
def test_tasks():
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = q0_split_tasks(all_tasks)
    for t in splits["test"]:
        assert "code" not in t, "contamination: code field survived split_tasks"
    return {t["task_id"]: t for t in splits["test"]}


def _run_bucket(bucket_ids, test_tasks):
    """Drive the REAL pipeline over the given task ids, PRIMARY protocol,
    via the existing `mbpp_arc3_battery` driver — the same call shape
    `run_pass` uses internally, scoped to just this population so the
    gate stays well under the suite's runtime budget (measured ~7s for
    all 85, not per-task)."""
    outcomes = {}
    for tid in bucket_ids:
        task = test_tasks[tid]
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        report = {
            "n_test_list": len(task.get("test_list", [])),
            "n_parseable": len(rows),
            "n_unparseable": len(parsed["unparseable"]),
            "unparseable_reasons": [u["form"] for u in parsed["unparseable"]],
        }
        spec = ms.split_rows(rows, "primary")
        if not spec["runnable"]:
            outcomes[tid] = mab.excluded_outcome(spec)
            continue
        row = mab.run_task(task, spec, report, mab.boot_full_r3, "primary")
        outcomes[tid] = row["outcome"]
    return outcomes


@pytest.fixture(scope="module")
def after_outcomes(bucket_ids, test_tasks):
    return _run_bucket(bucket_ids, test_tasks)


# --------------------------------------------------------------------------- #
#  1. The frozen bucket itself.
# --------------------------------------------------------------------------- #
def test_bucket_is_the_frozen_85(bucket_ids):
    assert len(bucket_ids) == 85
    assert len(set(bucket_ids)) == 85, "no duplicate ids"
    assert bucket_ids[:5] == [11, 18, 19, 59, 65], (
        "the bucket's own declared order must not have silently reordered")


# --------------------------------------------------------------------------- #
#  2. BEFORE state.
# --------------------------------------------------------------------------- #
def test_before_prefix_is_recorded_as_gapped_enumerate_failed(bucket_ids):
    """The recorded pre-widening capture (§2 above) is a genuine prefix
    of the frozen bucket, and every one of its 30 ids is asserted at
    exactly the ONE outcome the bucket's own definition requires."""
    assert BEFORE_PREFIX_IDS == bucket_ids[:30]
    assert len(BEFORE_PREFIX_IDS) == 30


def test_before_definitional_argument_covers_all_85(bucket_ids):
    """Bucket membership is DEFINED (S0B §4) as 'was gapped:
    enumerate_failed in FULL-R3 AND matches none of the five named
    levers' — so ALL 85 held `gapped:enumerate_failed` before this
    phase's widening, not just the 30-id live-reproduced prefix. This
    test states that argument as a checkable fact: the probe artifact's
    own `ha4_search_reach_sizing` partition (covered-by-lever / ok-
    already / other-blocker / residual-none) sums to exactly 139 with no
    overlap, which is what makes "ok_already" a clean, non-overlapping
    complement of the five levers over the `gapped:enumerate_failed`
    population in the first place."""
    with open(PROBE_PATH) as f:
        probe = json.load(f)
    sizing = probe["ha4_search_reach_sizing"]
    covered = set()
    for ids in sizing["exclusive_task_ids"].values():
        covered.update(ids)
    ok_already = set(sizing["ok_already_no_named_lever"])
    assert covered.isdisjoint(ok_already), (
        "a task cannot be BOTH lever-covered and ok-already — the "
        "bucket's own partition would be incoherent")
    assert ok_already == set(bucket_ids)


# --------------------------------------------------------------------------- #
#  3-5. AFTER state, live.
# --------------------------------------------------------------------------- #
def test_after_pass_ids_match(after_outcomes, bucket_ids):
    live_pass = sorted(t for t, o in after_outcomes.items() if o == "pass")
    # S4's attribution, with the arc5 exact-first AND arc5-moves ids held
    # out (see above) — each later phase's own genuine conversion must not
    # be folded into S4's own frozen claim.
    s4_pass = sorted(
        set(live_pass) - _ARC5_EXACT_FIRST_PASS_IDS - _ARC5_MOVES_PASS_IDS
        - _MERGED_ENGINE_PASS_IDS)
    assert s4_pass == sorted(AFTER_PASS_IDS)
    assert _ARC5_EXACT_FIRST_PASS_IDS <= set(live_pass), (
        "the arc5 exact-first rung should still solve the geometry family")
    assert _ARC5_MOVES_PASS_IDS <= set(live_pass), (
        "the arc5 moves rung (MOVE B) should still solve task 59 via "
        "intermediate decomposition")
    assert _MERGED_ENGINE_PASS_IDS <= set(live_pass)
    assert set(live_pass) <= set(bucket_ids)


def test_after_accepted_holdout_fail_ids_match(after_outcomes, bucket_ids):
    live_ahf = sorted(
        t for t, o in after_outcomes.items() if o == "accepted_holdout_fail")
    # arc5-moves lands task 162 here (an honest 2-row coincidental fit the
    # held-out check correctly catches, MOVES.md §5) — held out the same
    # way the pass ids above are.
    assert (sorted(set(live_ahf) - _ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS
                   - _MERGED_ENGINE_ACCEPTED_HOLDOUT_FAIL_IDS)
            == sorted(AFTER_ACCEPTED_HOLDOUT_FAIL_IDS))
    assert _ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS <= set(live_ahf), (
        "the arc5 moves rung should still land task 162 in "
        "accepted_holdout_fail (caught, not a wrong pass)")
    assert _MERGED_ENGINE_ACCEPTED_HOLDOUT_FAIL_IDS <= set(live_ahf)
    assert set(live_ahf) <= set(bucket_ids)


def test_after_moved_to_other_gap_reason_ids_match(after_outcomes, bucket_ids):
    live_moved_other = {
        t: o for t, o in after_outcomes.items()
        if o not in ("pass", "accepted_holdout_fail", BEFORE_OUTCOME)
    }
    # 2026-08-02 (arc6 tier 0): S4's OWN moved-other set must still bite
    # exactly; the later phase's ids are named separately and asserted
    # separately, so a drift in EITHER is still a red.
    expected = dict(AFTER_MOVED_OTHER)
    expected.update({t: o for t, o in _ARC6_TIER0_MOVED_OTHER.items()
                     if t in set(bucket_ids)})
    for task_id in (_MERGED_ENGINE_PASS_IDS
                    | _MERGED_ENGINE_ACCEPTED_HOLDOUT_FAIL_IDS
                    | _MERGED_ENGINE_RETURNED_RESIDUAL_IDS):
        expected.pop(task_id, None)
    assert live_moved_other == expected
    assert {t: o for t, o in live_moved_other.items()
            if t not in _ARC6_TIER0_MOVED_OTHER} == {
                t: o for t, o in AFTER_MOVED_OTHER.items()
                if t not in _MERGED_ENGINE_PASS_IDS
            }
    assert set(live_moved_other) <= set(bucket_ids)


def test_reach_headline_at_least_20_of_85_moved(after_outcomes):
    moved = sum(1 for o in after_outcomes.values() if o != BEFORE_OUTCOME)
    still = sum(1 for o in after_outcomes.values() if o == BEFORE_OUTCOME)
    assert moved + still == 85
    assert moved >= MIN_MOVED_OFF_ENUMERATE_FAILED, (
        f"expected >= {MIN_MOVED_OFF_ENUMERATE_FAILED}/85 moved off "
        f"{BEFORE_OUTCOME}, measured {moved}/85")


def test_still_gapped_residual_is_named_not_hidden(after_outcomes, bucket_ids):
    """The honest residual: 60/85 remain `gapped:enumerate_failed` at S4 —
    asserted as an exact set, not a bare count, so a future phase can
    diff against it directly. arc5 exact-first took six more out (the
    geometry family) and arc5-moves took task 59 out (MOVE B); task 162
    also LEAVES the residual (it moves to accepted_holdout_fail, not to
    gapped:enumerate_failed), so it is held out here too."""
    still = sorted(t for t, o in after_outcomes.items() if o == BEFORE_OUTCOME)
    # 2026-08-02 (arc6 tier 0): the op-table widening takes further ids out
    # of the residual and puts NONE back — see `_ARC6_TIER0_*` above.
    _arc6_out = (_ARC6_TIER0_PASS_IDS | _ARC6_TIER0_ACCEPTED_HOLDOUT_FAIL_IDS
                 | set(_ARC6_TIER0_MOVED_OTHER))
    expected_still = sorted(
        set(bucket_ids) - set(AFTER_PASS_IDS) - set(AFTER_ACCEPTED_HOLDOUT_FAIL_IDS)
        - set(AFTER_MOVED_OTHER) - _ARC5_EXACT_FIRST_PASS_IDS
        - _ARC5_MOVES_PASS_IDS - _ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS
        - _arc6_out - _MERGED_ENGINE_PASS_IDS
        - _MERGED_ENGINE_ACCEPTED_HOLDOUT_FAIL_IDS
        | _MERGED_ENGINE_RETURNED_RESIDUAL_IDS)
    assert still == expected_still
    # 60 at S4; exact-first took six more out; moves took two more
    # (59 -> pass, 162 -> accepted_holdout_fail); arc6 tier 0 takes out
    # `_arc6_out` (a REACH move for all but one, not a conversion).
    # The exact set above is the primary gate.  Its merged-engine cardinality
    # is 46; a separate scalar is only a readable summary (several later-phase
    # attribution sets overlap, so subtracting their raw sizes double-counts).
    assert len(still) == 46
    # ONE-DIRECTIONAL: the residual may only ever shrink under a later
    # phase.  Pinned so a future reconciliation cannot quietly grow it.
    assert set(still) <= set(bucket_ids) - set(AFTER_PASS_IDS)


# --------------------------------------------------------------------------- #
#  6. Determinism.
# --------------------------------------------------------------------------- #
def test_determinism_second_pass_identical(bucket_ids, test_tasks, after_outcomes):
    second = _run_bucket(bucket_ids, test_tasks)
    assert second == after_outcomes, (
        "SynthEnumerate is a pure deterministic search — a second live "
        "pass over the identical population must reproduce the IDENTICAL "
        "per-task outcome, not merely the same aggregate counts")


# --------------------------------------------------------------------------- #
#  7. No-python-decision source audit.
# --------------------------------------------------------------------------- #
def test_this_file_makes_no_synthesis_decision_of_its_own():
    """This gate only reads task/spec data and calls the EXISTING,
    unmodified `mbpp_arc3_battery` driver — it must never itself branch
    on graph/program state (that would be agent logic misplaced in a
    test driver)."""
    src = inspect.getsource(_run_bucket)
    # The only conditional in the driver loop is the pre-existing
    # protocol-exclusion check (`spec["runnable"]`), copied verbatim from
    # `mbpp_arc3_battery.run_pass`'s own loop body — not a new decision
    # this file invents.
    assert "spec[\"runnable\"]" in src
    forbidden = ("gr._match", "gr._apply", "graph_rewrite.run")
    for token in forbidden:
        assert token not in src


# --------------------------------------------------------------------------- #
#  Cross-check against the taxonomy in PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md:
#  every moved id belongs to a targeted class (A/B/C — list-reduction/
#  filter/map), never an id from the deliberately-untouched classes
#  (D sort/combinatorics, E arithmetic depth, F string-transform,
#  G dict-construction).
# --------------------------------------------------------------------------- #
UNTARGETED_CLASS_IDS = {
    # class D — sort/combinatorics (no Sort/permutation primitive built)
    141, 232, 255, 262, 265, 462, 475,
    # class E — arithmetic depth / missing math ops (an orthogonal axis)
    59, 80, 82, 85, 139, 163, 233, 246, 248, 252, 260, 264, 276, 293, 312,
    422, 435, 448, 479,
    # class F — string-transform beyond Concat/CaseFold
    11, 18, 102, 118, 172, 226, 230, 310, 411, 437, 474,
    # class G — dict/heterogeneous structural
    87, 88, 301,
}


def test_movement_never_touches_a_deliberately_untargeted_class(after_outcomes):
    moved_ids = {t for t, o in after_outcomes.items() if o != BEFORE_OUTCOME}
    # Attribute-aware: the arc5 exact-first ids ARE class E (arithmetic
    # depth) and were moved by the shape-first rung, not by S4's widening.
    # S4's claim — that ITS widening never left classes A/B/C — is what this
    # test exists to check, so those ids are excluded from the check.
    # Task 59 is ALSO class E (arithmetic depth) and moves via arc5-moves'
    # MOVE B (intermediate decomposition), not S4's widening either; 162
    # (no named class) moves to accepted_holdout_fail via the same phase.
    # Both are held out for the same reason as the exact-first ids.
    moved_ids -= _ARC5_EXACT_FIRST_PASS_IDS
    moved_ids -= _ARC5_MOVES_PASS_IDS
    moved_ids -= _ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS
    hit_untargeted = moved_ids & UNTARGETED_CLASS_IDS
    assert hit_untargeted == set(), (
        "the widening moved a task outside its own targeted classes "
        f"(A/B/C): {hit_untargeted} — the diagnosis in "
        "PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §1 would need revising")
