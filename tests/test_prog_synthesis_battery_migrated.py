"""test_prog_synthesis_battery_migrated — P6-A gates on the POWERED battery
artifact (results/prog_synthesis_battery.json; PROGRAM_SYNTHESIS_PREREG.md
§8 H6, run under §0's standing rules).

Gates:
  1. STRUCTURE/HONESTY: the artifact is LIST-shaped (per-task rows are the
     baseline; every aggregate — overall, per-stratum, both arms — is
     re-derived from the rows and must match); Wilson CI fields present on
     every proportion and re-derivable; the Newcombe delta re-derives; the
     failure taxonomy accounts for every row.
  2. TASK-SET INTEGRITY + CONTAMINATION GUARD: N >= 120 (the card's floor
     before any documented cut; never below 100), unique ids, strata counts
     match the frozen task file; NO request text is copied from the P4 gate
     fixtures (tests/test_program_synthesis_migrated.py — the mechanism's
     own dev set) nor from the frozen 26-item C-BATTERY.
  3. DETERMINISM EVIDENCE: two MAIN runs recorded identical outcome lists;
     the stored hash re-derives from the stored rows.
  4. C-BATTERY CONTINUITY (prereg §2): the frozen arm is quoted verbatim
     (7/26 from results/code_synthesis_baseline.json) and the live pinned
     re-run has ZERO ok->fail regressions (any flip blocks the phase).
  5. LIVE RE-VERIFICATION (small, deterministic): three pinned battery
     tasks re-run end-to-end through the SAME driver path must reproduce
     their frozen rows (outcome/status/construction/gap_reason/held-out
     verdict), plus the frozen-arm strip flips the spine task exactly as
     frozen (the learned-layer mechanism, re-verified live).

Run (worktree engine discipline):
    pytest tests/test_prog_synthesis_battery_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import hashlib
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

import substrate_rs as srs  # noqa: E402

ARTIFACT = os.path.join(ROOT, "results", "prog_synthesis_battery.json")
TASKS = os.path.join(ROOT, "tests", "fixtures", "prog_synthesis_battery",
                     "tasks.json")
P4_FIXTURE_FILE = os.path.join(ROOT, "tests",
                               "test_program_synthesis_migrated.py")
BASELINE = os.path.join(ROOT, "results", "code_synthesis_baseline.json")

_Z = 1.959963984540054


def _load():
    with open(ARTIFACT) as f:
        return json.load(f)


def _tasks():
    with open(TASKS) as f:
        return json.load(f)


def _wilson(k, n):
    p = k / n
    d = 1 + _Z * _Z / n
    centre = (p + _Z * _Z / (2 * n)) / d
    hw = _Z * math.sqrt(p * (1 - p) / n + _Z * _Z / (4 * n * n)) / d
    return [round(max(0.0, centre - hw), 6), round(min(1.0, centre + hw), 6)]


def _sig(rows):
    return [[r["task_id"], r["outcome"], r["status"], r["construction"],
             r["attempts"], r["gap_reason"]] for r in rows]


def _hash(sig):
    return hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()


# --------------------------------------------------------------------------- #
#  1. structure / honesty — every number derives from the rows
# --------------------------------------------------------------------------- #
def test_rows_are_the_baseline_and_every_aggregate_derives_from_them():
    d = _load()
    n = d["task_set"]["n"]
    for arm in ("main", "frozen"):
        rows = d["arms"][arm]["rows"]
        assert isinstance(rows, list) and len(rows) == n, arm
        agg = d["arms"][arm]["aggregates"]
        # overall re-derivation
        k = sum(1 for r in rows if r["outcome"] == "accepted_holdout_ok")
        assert agg["overall"]["k"] == k and agg["overall"]["n"] == n, arm
        assert agg["overall"]["ci95"] == _wilson(k, n), arm
        assert agg["overall"]["not_recognized"] == sum(
            1 for r in rows if r["outcome"] == "not_recognized")
        # per-stratum re-derivation
        for st, blk in agg["per_stratum"].items():
            sub = [r for r in rows if r["stratum"] == st]
            sk = sum(1 for r in sub
                     if r["outcome"] == "accepted_holdout_ok")
            assert blk["k"] == sk and blk["n"] == len(sub), (arm, st)
            assert blk["ci95"] == _wilson(sk, len(sub)), (arm, st)
        # taxonomy accounts for every row
        tax = d["failure_taxonomy"][arm]
        assert sum(v["n"] for v in tax.values()) == n, arm
        for v in tax.values():
            assert v["n"] == len(v["task_ids"])


def test_delta_has_ci_and_rederives():
    d = _load()
    n = d["task_set"]["n"]
    km = d["arms"]["main"]["aggregates"]["overall"]["k"]
    kf = d["arms"]["frozen"]["aggregates"]["overall"]["k"]
    delta = d["delta_main_minus_frozen"]["overall"]
    assert delta["ci95"][0] is not None and delta["ci95"][1] is not None
    assert delta["delta"] == round(km / n - kf / n, 6)
    # Newcombe re-derivation
    w1, w2 = _wilson(km, n), _wilson(kf, n)
    p1, p2 = km / n, kf / n
    lo = (p1 - p2) - math.sqrt((p1 - w1[0]) ** 2 + (w2[1] - p2) ** 2)
    hi = (p1 - p2) + math.sqrt((w1[1] - p1) ** 2 + (p2 - w2[0]) ** 2)
    assert delta["ci95"] == [round(lo, 6), round(hi, 6)]
    assert delta["three_x_step"] == round(3.0 / n, 6)
    assert "verdict" in delta
    # per-stratum deltas all carry CI fields
    for st, blk in d["delta_main_minus_frozen"]["per_stratum"].items():
        assert len(blk["ci95"]) == 2, st


def test_every_render_validity_proportion_carries_a_ci():
    d = _load()
    pyr = d["render_validity"]["python"]
    for key in ("render_ok", "exec_agree_of_rendered"):
        assert "ci95" in pyr[key] and len(pyr[key]["ci95"]) == 2, key
    # render_ok derives from the accepted MAIN rows
    acc = [r for r in d["arms"]["main"]["rows"]
           if str(r["outcome"]).startswith("accepted")]
    assert pyr["n_accepted"] == len(acc)
    n_ok = sum(1 for r in acc
               if (r.get("python_render") or {}).get("render_ok"))
    assert pyr["render_ok"]["k"] == n_ok
    # toolchain subsample: rule stated, ids listed, aggregates derive
    ts = d["render_validity"]["toolchain_subsample"]
    assert "rule" in ts and isinstance(ts["selected_ids"], list)
    assert len(ts["rows"]) == len(ts["selected_ids"])
    for lang in ("rust", "lua", "llvm_x86"):
        outs = [tr[lang]["outcome"] for tr in ts["rows"]]
        assert ts["aggregates"][lang]["agree"] == outs.count("agree"), lang
        assert ts["aggregates"][lang]["disagree"] == outs.count("disagree")


# --------------------------------------------------------------------------- #
#  2. task set integrity + contamination guard
# --------------------------------------------------------------------------- #
def test_task_set_size_strata_and_unique_ids():
    t = _tasks()
    d = _load()
    ids = [x["id"] for x in t["tasks"]]
    assert len(ids) == len(set(ids)), "duplicate task ids"
    assert t["n"] == len(t["tasks"]) == d["task_set"]["n"]
    assert t["n"] >= 120, ("battery below the card's documented floor; a "
                           "cut must be documented and never go below 100")
    counts: dict = {}
    for x in t["tasks"]:
        counts[x["stratum"]] = counts.get(x["stratum"], 0) + 1
    assert counts == t["strata_counts"] == d["task_set"]["strata_counts"]
    # every task carries example + held-out rows in the pinned shape
    for x in t["tasks"]:
        assert 3 <= len(x["example_rows"]) <= 5, x["id"]
        assert 2 <= len(x["held_out_rows"]) <= 3, x["id"]


def test_no_task_is_copied_from_the_p4_fixtures_or_the_frozen_battery():
    t = _tasks()
    with open(P4_FIXTURE_FILE) as f:
        p4_src = f.read().lower()
    with open(BASELINE) as f:
        frozen_reqs = {i["request"]
                       for i in json.load(f)["write_battery"]["items"]}
    for x in t["tasks"]:
        req = x["request_text"]
        assert req.lower() not in p4_src, (
            "task %s reuses a P4 gate fixture request" % x["id"])
        assert req not in frozen_reqs, (
            "task %s reuses a frozen C-BATTERY request" % x["id"])


# --------------------------------------------------------------------------- #
#  3. determinism evidence
# --------------------------------------------------------------------------- #
def test_two_main_runs_were_identical_and_the_hash_rederives():
    d = _load()
    det = d["determinism"]
    assert det["runs"] == 2 and det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]
    assert _hash(_sig(d["arms"]["main"]["rows"])) == det["outcome_hash_run1"]


# --------------------------------------------------------------------------- #
#  4. C-BATTERY continuity (prereg §2 — a flip blocks the phase)
# --------------------------------------------------------------------------- #
def test_c_battery_continuity_no_ok_to_fail_regression():
    d = _load()
    cb = d["c_battery"]
    with open(BASELINE) as f:
        wb = json.load(f)["write_battery"]
    assert cb["frozen_baseline"]["n"] == wb["n"] == 26
    assert cb["frozen_baseline"]["n_ok"] == wb["n_ok"]
    live = cb["live_pinned_path"]
    assert "error" not in live, live.get("error")
    assert live["n"] == 26
    assert live["regressions_ok_to_fail"] == [], (
        "C-BATTERY regression — blocks the phase: %r"
        % live["regressions_ok_to_fail"])
    # the new-pipeline verbatim pass is documented as structural, not scored
    assert "note" in cb["new_pipeline_verbatim"]
    assert len(cb["new_pipeline_verbatim"]["rows"]) == 26


# --------------------------------------------------------------------------- #
#  5. live re-verification — three pinned tasks reproduce their frozen rows
# --------------------------------------------------------------------------- #
def _engine_live() -> bool:
    s = srs.Substrate()
    for probe in (
            {"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
             "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
             "wild_objects": False},
            {"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
             "env": None, "oracles": None, "fuel": 5, "field": ""}):
        try:
            s._inner.evaluate(probe, {"g": [["p", "x"]]}
                              if probe["type"] == "ShapeDecode" else {})
        except ValueError as e:
            if "UnknownTermType" in str(e):
                return False
    return True


# one covered rung-1 accept, the spine (learned-layer) accept, one honest gap
REVERIFY_IDS = ("ex_01_pick_larger", "la_03_running_sum",
                "ms_10_collatz_next")


@pytest.mark.parametrize("tid", REVERIFY_IDS)
def test_live_reverify_pinned_task_matches_frozen_row(tid):
    if not _engine_live():
        pytest.skip("ShapeDecode/ProgEval not in installed substrate_rs — "
                    "honest skip.")
    import prog_synthesis_battery as b
    d = _load()
    frozen_row = next(r for r in d["arms"]["main"]["rows"]
                      if r["task_id"] == tid)
    task = next(t for t in _tasks()["tasks"] if t["id"] == tid)
    live = b.run_task(task, frozen=False)
    for key in ("outcome", "status", "construction", "gap_reason",
                "enumerate_outcome", "attempts"):
        assert live[key] == frozen_row[key], (tid, key)
    if "holdout" in frozen_row:
        assert live["holdout"]["all_ok"] == frozen_row["holdout"]["all_ok"]


# --------------------------------------------------------------------------- #
#  6. P7-D gates (additive — PROGRAM_SYNTHESIS_P7D.md): the appended arms
#     main_p7 / frozen_p7 / repair_oracle. Everything above is untouched.
# --------------------------------------------------------------------------- #
P7_ARMS = ("main_p7", "frozen_p7", "repair_oracle")
P7_PRIMARY = ("main_p7", "frozen_p7")


def test_p7_arms_rows_are_baseline_and_aggregates_derive():
    d = _load()
    n = d["task_set"]["n"]
    for arm in P7_ARMS:
        rows = d["arms"][arm]["rows"]
        assert isinstance(rows, list) and len(rows) == n, arm
        agg = d["arms"][arm]["aggregates"]
        k = sum(1 for r in rows if r["outcome"] == "accepted_holdout_ok")
        assert agg["overall"]["k"] == k and agg["overall"]["n"] == n, arm
        assert agg["overall"]["ci95"] == _wilson(k, n), arm
        for st, blk in agg["per_stratum"].items():
            sub = [r for r in rows if r["stratum"] == st]
            sk = sum(1 for r in sub
                     if r["outcome"] == "accepted_holdout_ok")
            assert blk["k"] == sk and blk["n"] == len(sub), (arm, st)
            assert blk["ci95"] == _wilson(sk, len(sub)), (arm, st)
        tax = d["failure_taxonomy"][arm]
        assert sum(v["n"] for v in tax.values()) == n, arm
        for v in tax.values():
            assert v["n"] == len(v["task_ids"])
        # twin-run determinism recorded and the hash re-derives
        det = d["determinism_p7"][arm]
        assert det["runs"] == 2 and det["identical"] is True, arm
        assert det["outcome_hash_run1"] == det["outcome_hash_run2"], arm
        assert _hash(_sig(rows)) == det["outcome_hash_run1"], arm
        # zero parks (H7b's standing requirement)
        assert not any(str(r["outcome"]).startswith("stalled")
                       for r in rows), arm


def test_p7_protocol_separation():
    """REPAIR-ORACLE is protocol-distinct: its rows carry the label, the
    primary arms carry 'primary', and no primary aggregate/delta includes
    the oracle arm's counts."""
    d = _load()
    for r in d["arms"]["repair_oracle"]["rows"]:
        assert r["protocol"] == "repair_oracle_feedback", r["task_id"]
    for arm in P7_PRIMARY:
        for r in d["arms"][arm]["rows"]:
            assert r["protocol"] == "primary", (arm, r["task_id"])
    v = d["p7_verdicts"]
    n = d["task_set"]["n"]
    k_main = d["arms"]["main_p7"]["aggregates"]["overall"]["k"]
    k_frozen = d["arms"]["frozen_p7"]["aggregates"]["overall"]["k"]
    k_oracle = d["arms"]["repair_oracle"]["aggregates"]["overall"]["k"]
    # H7c delta derives from the PRIMARY arms exactly
    h7c = v["h7c_learned_content"]["delta_main_p7_minus_frozen_p7"]
    assert h7c["delta"] == round(k_main / n - k_frozen / n, 6)
    # and would NOT re-derive from the oracle arm (the arms measured
    # different k, so a silent substitution is detectable)
    assert k_oracle != k_main
    assert h7c["delta"] != round(k_oracle / n - k_frozen / n, 6)
    # H7a reads the main_p7 stratum block verbatim
    h7a = v["h7a_loop_accumulation"]
    assert h7a["main_p7"] == d["arms"]["main_p7"]["aggregates"][
        "per_stratum"]["loop_accumulation"]
    # oracle findings live under their own labelled key only
    assert "repair_oracle_protocol" in v["h7b_repair"]
    assert "SECONDARY" in v["h7b_repair"]["repair_oracle_protocol"][
        "protocol"]


def test_p7_frozen_arms_untouched_by_the_append():
    """Protected control: the frozen MAIN / MAIN-POSTFIX rows still hash to
    their recorded determinism hashes after the P7 append (FROZEN has no
    recorded hash; its aggregate row-derivation is gate 1's)."""
    d = _load()
    assert _hash(_sig(d["arms"]["main"]["rows"])) \
        == d["determinism"]["outcome_hash_run1"]
    assert _hash(_sig(d["arms"]["main_postfix"]["rows"])) \
        == d["determinism_postfix"]["outcome_hash_run1"]


def test_p7_verdicts_rederive_from_the_rows():
    d = _load()
    v = d["p7_verdicts"]
    # H7a: the registered decision rule (prereg: stratum Wilson lower
    # bound > .409, the frozen MAIN-POSTFIX upper) re-applies
    h7a = v["h7a_loop_accumulation"]
    blk = d["arms"]["main_p7"]["aggregates"]["per_stratum"][
        "loop_accumulation"]
    assert h7a["wilson_lower_bound_new"] == blk["ci95"][0]
    assert h7a["ci_separated"] == (blk["ci95"][0] > h7a["registered_bar"])
    assert h7a["verdict"] == ("confirmed_ci_separated" if h7a["ci_separated"]
                              else "registered_null")
    # paired lists are identity lists over the rows, and the STOP-defect
    # check (no ok -> not-ok flip vs MAIN-POSTFIX) re-derives empty
    base = {r["task_id"]: r for r in d["arms"]["main_postfix"]["rows"]}
    regress = [r["task_id"] for r in d["arms"]["main_p7"]["rows"]
               if base[r["task_id"]]["outcome"] == "accepted_holdout_ok"
               and r["outcome"] != "accepted_holdout_ok"]
    assert regress == []
    assert v["stop_defect_regressions_vs_main_postfix"] == regress
    changed = sorted(r["task_id"] for r in d["arms"]["main_p7"]["rows"]
                     if base[r["task_id"]]["outcome"] != r["outcome"])
    assert sorted(v["paired_main_p7_vs_main_postfix"]
                  ["changed_task_ids"]) == changed
    # H7b: oracle conversions re-derive from the oracle rows
    rows_o = d["arms"]["repair_oracle"]["rows"]
    conv = sorted(r["task_id"] for r in rows_o
                  if (r.get("oracle") or {}).get("pre_feedback_outcome")
                  == "accepted_holdout_fail"
                  and r["outcome"] == "accepted_holdout_ok")
    assert v["h7b_repair"]["repair_oracle_protocol"][
        "conversions_fail_to_ok"] == conv


# ---- live re-verification: two pinned tasks per new arm ------------------- #
_P7_REVERIFY = [
    # main_p7: a descent accept; the one chunk-decoy id (attempts 0->3,
    # still an enumerate accept — the chunk layer's whole battery footprint)
    ("main_p7", "la_20_double_each_total"),
    ("main_p7", "br_19_pick_or_boost"),
    # frozen_p7: the spine task gaps (content stripped); descent still runs
    # on STARTER content (mechanism on, content off)
    ("frozen_p7", "la_03_running_sum"),
    ("frozen_p7", "la_20_double_each_total"),
    # repair_oracle: the one conversion (la_10); br_10 is now a SECOND
    # conversion (see _P7_KNOWN_LIVE_IMPROVEMENT below, 2026-08-01 arc5
    # moves) rather than "a refused localization -> honest gap".
    ("repair_oracle", "la_10_count_positives"),
    ("repair_oracle", "br_10_top_of_three"),
]


# 2026-08-01 (arc2 Q4): br_10_top_of_three under repair_oracle drifted
# gapped -> accepted_holdout_ok live — Q4's exclude-powered enum-retry lane
# genuinely converges it now. The frozen P7-era row stays authoritative for
# its run; the live leg asserts the drift is in the IMPROVEMENT direction
# only (a gapped->pass flip; any other drift still fails).
# 2026-08-01 (arc4 S2) — br_10_top_of_three REMOVED from this set, and the
# removal records a TRUE REGRESSION, not a drift.
#
# Arc-4 Q4 had made this task converge under repair_oracle (gapped ->
# accepted_holdout_ok) via the exclude-powered enum retry. S2's structural
# detectors now reject its candidate BEFORE repair can iterate on it: the
# candidate is `Max(a,b)` for a top-of-THREE spec, which provably ignores
# the declared parameter `c` — D3's exact target shape. The rejection is
# CORRECT (the candidate is defective), but the goal then terminates as
# `gapped` instead of feeding repair, so a genuine pass was lost.
#
# Per PROGRAM_SYNTHESIS_ARC4_PREREG.md §AMENDMENT A3 this belongs on the
# TRUE-REGRESSION list, not the genuine-defect-rejection list: the program
# repair eventually produced was CORRECT on its held-out row. The design
# lesson is named in the S2 notes — a structural rejection should INFORM
# repair (it localises the fault precisely: "ignores parameter c") rather
# than terminate the goal. S2 tried routing rejections through the
# counterexample/exclude lane, hit a real stall, and reverted; closing this
# properly is arc-4's named residual, not a test problem.
#
# The live outcome now matches the FROZEN row ("gapped") again; only the
# gap_reason is more informative, allowed via _P7_KNOWN_GAP_REASON_DRIFT.
#
# 2026-08-01 (arc4 S6) — the mapped VALUE drifts again, to "enumerate_
# failed"; the note is NOT retired, because br_10 still does not converge.
# S6 routes a non-retrieval D3-only rejection (this candidate's own
# construction is never 'retrieved_exemplar') into the STANDING exclude/
# reproposal lane instead of straight to 'gapped' (PROGRAM_SYNTHESIS_
# ARC4_S6_NOTES.md): `Max(a,b)` is excluded and the arc2-Q4 exclude-
# powered enum-retry genuinely fires again — verified live
# (ps_structural_reopen_count == 1.0, an Excluded node named 'lookup
# decoy'-shaped for this construction). But repair informed ONLY by the
# 3 REVEALED rows (never the held-out row the repair_oracle protocol would
# have fed) has no discriminating signal: all three revealed rows already
# agree with `max(a,b)` (that is WHY it was ever accepted), so excluding
# it removes the wrong answer without supplying the missing information
# that would let the search prefer a DIFFERENT, correct generalisation —
# measured directly (`runners/dsl/src/synth_enumerate.rs`'s own engine,
# probed live): an EXHAUSTIVE size<=5 re-search after exclusion finds
# NOTHING (halt_reason 'max_size'), while the SAME engine trivially finds
# `max(a, max(b, c))` when a genuinely discriminating 4th row is present
# (28989 candidates tested, halt_reason 'solved'). The retry therefore
# honestly exhausts its OWN enumerate-round budget and the goal lands on
# `gapped:enumerate_failed` — never `accepted_holdout_fail` — so
# `run_task_p7`'s own `pre["outcome"] != "accepted_holdout_fail"` guard
# short-circuits before oracle feedback is even attempted (oracle.rounds
# stays 0, asserted below). This is architecture, not a gap in this
# phase's own reach: the repair_oracle harness's ONE external-
# counterexample feed is gated on the goal having reached `accepted`
# first, and S2's own correctness guarantee (never accept a candidate a
# detector can prove defective) permanently forecloses that gate for
# EXACTLY the traps whose revealed rows are, by construction,
# insufficient to distinguish the decoy from the fix — see
# PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md §4 for the full root-cause and the
# 26-id disposition table this same mechanism produces on the live MBPP
# population (14 ids move the SAME way; zero convert to `pass`; zero
# regress to a wrong accept).
_P7_KNOWN_GAP_REASON_DRIFT = {}
_P7_KNOWN_GAP_REASON_DRIFT_ALSO_KEYS = {}

# 2026-08-01 (arc5 moves, reconciled): br_10_top_of_three under
# repair_oracle drifted a THIRD time — S6's "enumerate_failed" gap (the
# note above, retained for its own history) is now SUPERSEDED by arc5-
# moves' MOVE A (orbit augmentation, PROGRAM_SYNTHESIS_ARC5_MOVES.md):
# RUNG 2.6 finds the correct `Max(a, Max(b, c))` DIRECTLY from the 3
# revealed rows via symmetry, before enumerate ever proposes (or S6's
# reject/reopen ever needs to exclude) the `Max(a,b)` decoy. `br_10_top_
# of_three` moves from `("repair_oracle", ...)`'s `_P7_KNOWN_GAP_REASON_
# DRIFT` entry to `_P7_KNOWN_LIVE_IMPROVEMENT` below — the SAME shape
# `frozen_p7/la_03_running_sum` already uses for "a later, stronger core
# rung legitimately lifts a previously-gapped task", verified against a
# fresh witness (not just the fixture's own held-out rows) in
# tests/test_reject_informs_repair_migrated.py::
# test_br_10_root_caused_non_convergence.
_P7_KNOWN_LIVE_IMPROVEMENT = {
    # 2026-08-01 (arc4 S4): the frozen_p7 arm's la_03_running_sum drifted
    # gapped -> accepted_holdout_ok because S4 gave the ENUMERATOR native
    # list-folding ops. The frozen arm strips learned CONTENT, not core
    # reach, so a stronger core legitimately lifts it. See the retirement
    # note on test_live_reverify_frozen_arm_strips_the_learned_layer.
    ("frozen_p7", "la_03_running_sum"),
    # 2026-08-01 (arc5 moves): br_10_top_of_three, see the note above.
    ("repair_oracle", "br_10_top_of_three"),
}


@pytest.mark.parametrize("arm,tid", _P7_REVERIFY)
def test_p7_live_reverify_pinned_task_matches_stored_row(arm, tid):
    if not _engine_live():
        pytest.skip("ShapeDecode/ProgEval not in installed substrate_rs — "
                    "honest skip.")
    import prog_synthesis_battery as b
    d = _load()
    stored = next(r for r in d["arms"][arm]["rows"] if r["task_id"] == tid)
    task = next(t for t in _tasks()["tasks"] if t["id"] == tid)
    live = b.run_task_p7(task, arm)
    if (arm, tid) in _P7_KNOWN_LIVE_IMPROVEMENT:
        assert stored["outcome"] == "gapped", (arm, tid)
        assert live["outcome"] == "accepted_holdout_ok", (
            "expected the Q4 improvement drift, got %r" % live["outcome"])
        return
    # 2026-08-01 (arc4 S2): br_10 gaps at the same TERMINAL as its frozen
    # row but for a MORE INFORMATIVE reason — "structural_verdict_reject"
    # (a candidate was found and rejected because it provably ignores the
    # declared parameter `c`) instead of "no_shape" (nothing was found at
    # all). The outcome/status pins below still bite; only this one label
    # is allowed to move, and only in the explainability-gaining direction.
    _keys = ("outcome", "status", "construction", "gap_reason",
             "enumerate_outcome", "attempts", "protocol")
    if (arm, tid) in _P7_KNOWN_GAP_REASON_DRIFT:
        assert live["outcome"] == stored["outcome"], (arm, tid, "outcome")
        assert live["gap_reason"] == _P7_KNOWN_GAP_REASON_DRIFT[(arm, tid)]
        also = _P7_KNOWN_GAP_REASON_DRIFT_ALSO_KEYS.get((arm, tid), ())
        _keys = tuple(k for k in _keys
                      if k not in ("gap_reason", "construction", "attempts")
                      and k not in also)
    for key in _keys:
        assert live[key] == stored[key], (arm, tid, key)
    if "holdout" in stored:
        assert live["holdout"]["all_ok"] == stored["holdout"]["all_ok"]
    if arm == "repair_oracle" and (arm, tid) in _P7_KNOWN_GAP_REASON_DRIFT:
        # Same 2026-08-01 S2 cause: the candidate is rejected BEFORE accept,
        # so there is no accept for the oracle protocol to refute and zero
        # feedback rounds occur. Asserted explicitly rather than skipped.
        assert (live.get("oracle") or {}).get("rounds") == 0, (arm, tid)
        assert (live.get("oracle") or {}).get("ce_fed") is None, (arm, tid)
    elif arm == "repair_oracle":
        assert (live.get("oracle") or {}).get("rounds") \
            == (stored.get("oracle") or {}).get("rounds"), (arm, tid)


def test_live_reverify_frozen_arm_strips_the_learned_layer():
    """The C-CODEBOOK-FROZEN mechanism — RETIRED AS A LIVE ASSERTION,
    2026-08-01 (arc4 S4), and the reason is a result, not a maintenance
    chore.

    Original premise (verbatim from the pre-S4 docstring): "no spine shape,
    no bigrams -> **the enumerate rung cannot fold a list** -> gapped".
    That premise was a statement about the CORE's reach, and arc-4 S4
    falsified it deliberately: the enumerator gained 11 list/iteration ops
    (Len/SumList/MaxList/FilterList/MapList/...), each composed from
    EXISTING pure DSL Terms, so a content-stripped arm can now fold a list
    natively and `la_03_running_sum` reaches `accepted_holdout_ok`.

    Why this matters beyond the test: the learned layer's ONLY measured
    contribution across arcs 1-3 was the four spine ids (the entire H6 and
    H7c delta), and that contribution existed *because* the core could not
    fold a list. Raising the core's floor did not merely add capability —
    it removed the niche the specialised content occupied. That is the
    core/specialised trade observed directly, and it is recorded in
    PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md rather than papered over.

    The FROZEN ARTIFACT stays authoritative for its own run (asserted
    below); only the live-reverification leg is retired, in the
    improvement direction, per the standing dated-pin rule."""
    d = _load()
    tid = "la_03_running_sum"
    frozen_row = next(r for r in d["arms"]["frozen"]["rows"]
                      if r["task_id"] == tid)
    # The frozen row is unchanged and still records the pre-S4 world.
    assert frozen_row["outcome"] == "gapped"
    assert frozen_row["status"] == "gapped"
