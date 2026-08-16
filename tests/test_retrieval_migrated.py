"""test_retrieval_migrated — Arc 3 R1/R2 gates: the exemplar store, ranked
retrieval, and the adaptation ladder (`domains/prog_retrieval.py`,
`seeds/program_synthesis.json` v1.5.0 -> v1.5.1, `seeds/mbpp_exemplars.json`).

Companion docs: `PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R1/R2), `PROGRAM_SYNTHESIS_
ARC3_PREREG.md` / `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md` (the 12-task honest
oracle ceiling this phase's mechanism is measured against),
`PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` (the full write-up, including the
codebook-side universal-screen Attempt-1 REVERSION this file's gate 9 below
still guards against repeating — the CORRECTED, scoped redo landed in
Arc3-R2.5, seed v1.5.1, and is gated separately in `tests/test_screen_
codebook_migrated.py`).

Gates:
  1. store loads clean, idempotent, IR reflected into subgraphs.
  2. contamination — every Exemplar's provenance is "train", every task_id
     in the train range (>= 601); the shared contamination gate passes.
  3. scoring is a fixed formula (mechanical arithmetic) — SELECTION is a
     rule (`pr_select_candidate`): re-running score_exemplars is a no-op;
     top-k is bounded and rank-ordered by score (desc)/task_id (asc tie-
     break), verified live off a real goal.
  4. scope guard: a non-MBPP-shaped request scores ZERO exemplars (the
     descent/repair/battery-suite non-regression mechanism).
  5. the ladder screens before it may accept: a failing candidate never
     touches ps_attempts; a genuine accept consumes exactly ONE.
  6. Occam order: rung (a) exact-pass wins immediately when available,
     never falls to (b)/(c)/(d).
  7. ceiling capture — end-to-end (PRIMARY rows) on all 12 R0 ceiling task
     ids; a paired table (captured vs ceiling) with reasons for misses is
     asserted against the measured, reported numbers (never silently
     re-derived to a different count).
  8. NO-PYTHON-DECISION source audit of domains/prog_retrieval.py.
  9. non-regression: Attempt 1's codebook-side universal screen rules
     (`pr_screen_*`) are CONFIRMED still absent (never resurrected under
     those names) — la_10's known regression scenario reproduces the
     ORIGINAL (pre-Arc3) rungs; the CORRECTED, scoped redo (`ps_screen_*`,
     seed v1.5.1) is confirmed present and gated separately.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_retrieval_migrated.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_retrieval as pr  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402

EXEMPLAR_SEED_PATH = os.path.join(ROOT, "seeds", "mbpp_exemplars.json")
SYNTH_SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

# The 12 R0 oracle-ceiling task ids (PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md §1,
# `results/retrieval_oracle_ceiling.json`'s own `runnable_rows` where
# `best_rung_heldout_honest != "none"`) — pinned here so a future artifact
# edit that silently changes this set is a hard test failure, never a quiet
# re-derivation.
CEILING_TASK_IDS = (105, 106, 115, 138, 238, 242, 284, 394, 405, 406, 412, 414)

# The MEASURED end-to-end outcome of this phase's mechanism on each ceiling
# task (PRIMARY protocol, live `psy.synthesize_from_request` call) — a
# baseline LIST, per the project's own standing rule ("a baseline must be a
# list of ids, never a count"). `exc` marks the ONE pre-existing, unrelated
# residual (task 115's row carries a genuine Python `set` value — `mbpp_
# spec.py`'s own documented limitation, "not JSON-serializable ... until Q1
# lands native DSL Set support" — `ingest_spec` raises before retrieval ever
# runs; not a retrieval defect).
MEASURED_OUTCOMES = {
    105: {"status": "accepted", "rung": "c", "exemplar": 802, "holdout_ok": False},
    106: {"status": "gapped", "rung": "none"},
    115: {"exc": "TypeError"},
    138: {"status": "accepted", "rung": "d", "exemplar": 803, "holdout_ok": True},
    238: {"status": "accepted", "rung": "d", "exemplar": 802, "holdout_ok": False},
    242: {"status": "accepted", "rung": "d", "exemplar": 776, "holdout_ok": False},
    284: {"status": "accepted", "rung": "none", "holdout_ok": False},
    394: {"status": "gapped", "rung": "none"},
    405: {"status": "accepted", "rung": "d", "exemplar": 637, "holdout_ok": False},
    406: {"status": "accepted", "rung": "d", "exemplar": 775, "holdout_ok": True},
    412: {"status": "gapped", "rung": "none"},
    414: {"status": "accepted", "rung": "none", "holdout_ok": False},
}
CAPTURED_TASK_IDS = (138, 406)  # accepted via RETRIEVAL AND holds out True

# 2026-08-01 arc4 S4 reconciliation: task 394's LIVE outcome now diverges
# from the frozen R0/R2 `MEASURED_OUTCOMES` baseline above (status
# "gapped"->"accepted", rung "none"->"d"). Cause: S4 widened SynthEnumerate
# with new list ops (`Last`/`Count`, PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md §2),
# which rung d's generate-and-test hole fill now draws on for exemplar 760's
# masked statement, producing `Last(a) > Count(a)` for "check tuple contains
# no duplicates". This is NOT a genuine capture, unlike la_10/la_20/la_21
# elsewhere in this reconciliation: `Last(a) > Count(a)` is not a correct
# duplicate check at all — verified live, `a=(5, 1, 2)` is a genuinely
# distinct tuple this program wrongly scores False (full proof in
# PROGRAM_SYNTHESIS_ARC4_RECONCILE_NOTES.md). It happens to fit task 394's
# 2 revealed rows AND its 1 held-out row by coincidence — the held-out
# check's known blind spot when only one row is withheld. This drift is
# recorded here, NEVER folded into `MEASURED_OUTCOMES` (which stays
# byte-identical to its own frozen R0/R2 measurement) and deliberately NOT
# added to `CAPTURED_TASK_IDS` — the standing dated-pin rule reconciles a
# drift only in the genuine-improvement direction, and a coincidental false
# positive is not one.
_KNOWN_S4_DRIFT = {
    394: {"status": "accepted", "rung": "d", "exemplar": 760, "holdout_ok": True},
}

# 2026-08-01 (arc4 S2 reconciliation): tasks 242/284/414 are three of S2's
# own measured `structural_killable_ids`
# (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2 / arc4_structural_
# verdicts.json) — their PREVIOUS "measured" outcome above was a wrong,
# holdout-failing accept (`holdout_ok: False` on all three); S2's
# structural-verdict rules now correctly REJECT that wrong candidate before
# it can ever be presented as an accept (`status` "accepted" -> "gapped",
# `gap_reason` "structural_verdict_reject"). This is the SAME direction as
# task 267 in `test_mbpp_baseline_migrated.py`'s `_KNOWN_CONSTRUCTION_DRIFT`
# — a wrong accept becoming an honest rejection is a WIN per
# PROGRAM_SYNTHESIS_ARC4_PREREG.md's own honest-score amendment (§AMENDMENT
# A3), never a regression to tune away. `MEASURED_OUTCOMES` itself stays
# byte-identical to its own frozen measurement moment; this is a REPLACEMENT
# (not a merge) because the shape of what is checkable genuinely changed —
# a gapped task carries no exemplar/holdout_ok the way an accepted one does,
# exactly like the pre-existing gapped rows (106/394-frozen/412) in
# MEASURED_OUTCOMES above never carried those keys either. `rung`/`exemplar`
# are preserved where retrieval still reaches them (242 reached rung d,
# exemplar 776, before the reject) so the retrieval mechanism itself is
# still pinned, just not the (now honestly rejected) final verdict.
_KNOWN_S2_STRUCTURAL_REJECT_DRIFT = {
    242: {"status": "gapped", "rung": "d", "exemplar": 776},
    284: {"status": "gapped", "rung": "none"},
    414: {"status": "gapped", "rung": "none"},
}

# 2026-08-01 (arc6 seam D, reconciled): tasks 105/238/405 are the THIRD
# documented exception, and the SAME KIND as the S2 one directly above — a
# wrong accept becoming an honest, named rejection. Arc6 seam D
# (PROGRAM_SYNTHESIS_ARC6_D.md) added a PROPERTY-REFUTATION rung
# (ps_property_clear / ps_property_reject_gap / ps_property_reject_reopen)
# and a second clause on ps_accept's gate (ps_property_reject == 0.0), so a
# candidate that contradicts a property entailed by the task's OWN prompt is
# refused BEFORE it can be presented as an accept: `status` "accepted" ->
# "gapped", `gap_reason` "property_verdict_reject".
#
# All three already carried `holdout_ok: False` in MEASURED_OUTCOMES above —
# but that flag is NOT what this supersession rests on. Each was
# INDEPENDENTLY re-proven wrong-in-general by a CONSTRUCTED WITNESS (the
# task-92/464 method of `tests/test_reject_informs_repair_migrated.py`):
# the candidate the retrieval ladder actually builds was evaluated through
# the same ProgEval term every verdict path uses, on inputs that are
# neither a revealed row, nor the held-out row, nor the PropertyAtom's own
# witness, and compared against the task's own reference implementation
# (`sanitized-mbpp`'s `code` field). `test_arc6_property_rejected_ceiling_
# candidates_are_wrong_by_construction` below IS that proof, run in-suite —
# never merely asserted here:
#   105 (count true booleans) — candidate returns the first index i with
#       a[i] > a[i-1] else 0; a=[True,True] -> 0, reference 2.
#   238 (count non-empty substrings) — candidate is a literal lookup,
#       `a == "abc" ? 6 : 10`; a="ab" -> 10, reference 3.
#   405 (element exists in a tuple) — candidate returns `b == "r"` and
#       never reads the tuple at all; (("x","y"),"y") -> False, reference
#       True, and (("q",),"r") -> True, reference False (wrong in BOTH
#       directions).
# `rung`/`exemplar` are PRESERVED (105: rung c / exemplar 802; 238: rung d /
# exemplar 802; 405: rung d / exemplar 637 — byte-identical to the frozen
# MEASURED_OUTCOMES rows), so this file's own claim — what the RETRIEVAL
# ladder reaches — is still pinned exactly as measured; only the (now
# honestly refused) final verdict is superseded, and the refusing rung is
# named. MEASURED_OUTCOMES itself stays byte-identical to its frozen R0/R2
# moment, and CAPTURED_TASK_IDS / the headline count are untouched (none of
# the three was ever a capture).
_KNOWN_ARC6_PROPERTY_REJECT_DRIFT = {
    # 2026-08-16 (PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY, a FOURTH
    # supersession on top of this one — task 105 only): the
    # `ps_property_reject_retrieval_enumerate_fallback` rule gives a
    # retrieved_exemplar candidate that fails a held PropertyAtom ONE
    # extra chance via SynthEnumerate, gated on the enumerate candidate
    # ALSO clearing the SAME fired atom before the terminal gap fires.
    # Live-verified: for 105 the enumerate candidate (`Sum(a)` — True==1
    # in Python, so summing a list of booleans counts the True elements)
    # clears `prop_count_true` AND passes the held-out row
    # (holdout_ok=True) — a genuine correction, not a capability lost.
    # 238/405's enumerate candidates ALSO clear the fallback's own
    # attempt but STILL violate their own fired PropertyAtom (independent,
    # per-task probe, PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY_RESULTS.md),
    # so both stay pinned exactly as before -- this rung touches 105 only.
    105: {"status": "accepted", "rung": "c", "exemplar": 802,
          "holdout_ok": True},
    # 2026-08-16: 238's enumerate fallback candidate ALSO violates its own
    # fired PropertyAtom (still genuinely wrong, unlike 105) -- but on the
    # SECOND `compute_structural_facts` pass (over the enumerate
    # candidate) a D1/D2/D3 structural detector ALSO fires and is what
    # actually routes this goal to terminal `gapped` this time (the two
    # verdict families are independent, unordered checks that both run on
    # every verified candidate; whichever's OWN gate rule matches first
    # decides the recorded gap_reason -- status/rung/exemplar are
    # unaffected, this is a diagnostic-label change only, see
    # PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY_RESULTS.md).
    238: {"status": "gapped", "gap_reason": "structural_verdict_reject",
          "rung": "d", "exemplar": 802},
    405: {"status": "gapped", "gap_reason": "property_verdict_reject",
          "rung": "d", "exemplar": 637},
}

# 2026-08-02 (ARC 6 TIER 0, reconciled — IMPROVEMENT DIRECTION).
# A FOURTH documented exception, and the only one so far caused by the
# ENUMERATOR getting stronger rather than a verdict getting stricter.
#
# `MEASURED_OUTCOMES[106]` records `rung: "none"` and this file's own
# `test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing` justified
# pinning task 106 there with the words *"a heterogeneous tuple+list
# concatenation THE DSL HAS NO OP FOR AT ALL"*.  That sentence is now false:
# `op:ConcatList` (arc-6 tier 0 — `Fold` + `Append`, the way `JoinList` was
# already built, ZERO new `TermNode` variants) is exactly that op.
#
# Live, task 106 now reaches the enumerate rung and the enumerator PROPOSES
# the exact witness `fold(a, __acc=b, __item -> append(__acc, __item))`,
# which `ProgEval` evaluates to the right answer on every revealed row.  It
# is then refused by the ROW VERDICT, which cannot compare a non-scalar
# result.  The merged 2026-08-04 engine preserves that real proposal and now
# reports the terminal honestly as `enumerate_failed` rather than the older
# downstream `no_shape` label.  The retrieval record remains `rung: none` in
# this retrieval-scoped driver; the full-R3 search-reach gate separately holds
# the enumerator evidence, so this pin does not falsely attribute that work to
# retrieval.
#
# `MEASURED_OUTCOMES` itself is UNTOUCHED — the frozen table stays frozen and
# the supersession is recorded beside it, exactly as the three drifts above
# are.  See `PROGRAM_SYNTHESIS_ARC6_TIER0.md`.
_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT = {
    106: {"status": "gapped", "gap_reason": "enumerate_failed", "rung": "none"},
}

# 2026-08-14 (BUGFIX_SWEEP2_RESULTS.md item 2 — a FIFTH documented exception,
# and a THIRD reconciliation on top of task 106's own already-superseded
# `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT` entry directly above). Investigated
# live, in a fresh worktree off `main @ c87d065`, after
# `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §6` first flagged
# task 242's drift (2026-08-11) and explicitly left it "not independently
# confirmed correct or incorrect... requiring its own review" — that review
# is this entry. `test_retrieval_migrated.py` is NOT one of the program-
# synthesis "named 9-file suite" files (it is invoked only as a subprocess
# by `test_prog_moves_migrated.py`/`test_exact_first_migrated.py`'s own
# meta-tests), which is why this pin sat stale across two further merged
# rungs (`progsyn-setlit-dictitems`, `progsyn-dictitems-sortby`) without
# being independently re-verified.
#
# Re-running `test_ceiling_task_reproduces_measured_outcome_live` for all 12
# `CEILING_TASK_IDS` live (three repeated runs, byte-identical) found THREE
# mismatches, not one — 106, 115, AND 242 — all downstream of the SAME
# cause chain (arc6/rung1's widened `OP_TABLE` plus the already-merged
# `progsyn-setlit-dictitems` set/frozenset `Lit`-boundary fix), exactly the
# "genuine, all downstream of the SAME widened op-table" class
# `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md §5.2` already named
# for this file's OTHER drifts. None of the three is a wrong-accept
# regression — the direction is the SAME improvement direction every prior
# reconciliation in this file privileges:
#
# - **242** (`count total number of characters in a string`) stays
#   HONESTLY GAPPED both before and after (`_KNOWN_S2_STRUCTURAL_REJECT_
#   DRIFT`'s own `status: "gapped"` is unchanged) — only the MECHANISM that
#   produces the gap moved. Before: the retrieval ladder reached rung `d`
#   (exemplar 776, adapted into a candidate the S2 structural-verdict rung
#   correctly rejected as wrong-in-general). Now: the plain `SynthEnumerate`
#   rung (upstream of retrieval in the Occam ladder) proposes its OWN
#   candidate first — `fold(items, x, acc, init=0, body=acc+1)`, a
#   syntactically-plausible length-count — and that candidate fails its own
#   row verdict (a string is still ATOMIC in this engine,
#   `STRUCTURAL_CEILING.md §3.1`'s S1 finding — `fix:StringAsSequence` has
#   NOT landed — so `Fold` over a string genuinely iterates zero times and
#   cannot reproduce the revealed rows), terminating the WHOLE ladder as
#   `enumerate_failed` before it ever reaches retrieval. Both mechanisms are
#   HONEST failures on a task this engine genuinely cannot yet solve; which
#   one gets there first is exactly the kind of Occam-order reshuffling a
#   primitive-layer widening is expected to cause, not a defect in either
#   rung. `rung`/`exemplar` move to `"none"`/`None` because retrieval
#   genuinely is not reached this time (byte-identical to how 106's own
#   entry above already treats "the ladder reaches something wrong before
#   retrieval fires" as a `rung: "none"` outcome, not an error).
# - **106** (`append the given list to the given tuples`) moves FURTHER,
#   past its own already-recorded `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`
#   supersession above: live it is now `status: "accepted"`, `rung: "b"`,
#   `exemplar: 750`, `holdout_ok: True` — a genuine RETRIEVAL-path accept
#   (`rung` is set ONLY inside `domains/prog_retrieval.py`, never by the
#   plain enumerator, so this is retrieval reaching rung `b`, not a
#   mislabeled enumerate hit).
# - **115** (the `TypeError` set-value case, `MEASURED_OUTCOMES[115] =
#   {"exc": "TypeError"}`) no longer raises at all: the already-merged
#   `progsyn-setlit-dictitems` rung's `Lit` set/frozenset-boundary fix
#   (named but not built as of `STRUCTURAL_CEILING.md §7.4`, landed since)
#   lets `ingest_spec` accept the row and the ladder now reaches
#   `status: "accepted"`, `rung: "a"`, `exemplar: 741`, `holdout_ok: True`.
#
# **Deliberately NOT done, named for the orchestrator instead of asserted
# here**: whether 106's and 115's new `holdout_ok: True` accepts are
# GENUINE captures (vs. task 394's own already-documented precedent, a
# coincidental fit the single held-out row could not catch — verified
# wrong only by a CONSTRUCTED counter-example witness) has not been
# independently checked by that same construction method. This entry pins
# only the LIVE, MEASURED outcome (matching this file's own "a baseline
# must be a list of ids, never a count" discipline); it deliberately does
# NOT add 106/115 to `CAPTURED_TASK_IDS` or touch any MBPP headline number
# — that is a materially bigger claim than a live re-pin and is exactly the
# kind of re-verification `test_task_92_and_464_frozen_passes_were_already_
# coincidental_fits` (`test_reject_informs_repair_migrated.py`) exists to
# do, not this test.
#
# `MEASURED_OUTCOMES` itself is UNTOUCHED — the frozen table stays frozen
# and every supersession is recorded beside it, exactly as every drift
# above already does.
_KNOWN_BUGFIX_SWEEP2_RUNG1_CASCADE_DRIFT = {
    106: {"status": "accepted", "rung": "b", "exemplar": 750, "holdout_ok": True},
    115: {"status": "accepted", "rung": "a", "exemplar": 741, "holdout_ok": True},
    242: {"status": "gapped", "gap_reason": "enumerate_failed", "rung": "none"},
}

# 2026-08-16 (PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5, orchestrator
# reconciliation — a SIXTH documented exception, same "improvement
# direction" class as `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`'s own 106 entry
# above): `MEASURED_OUTCOMES[412]` records `rung: "none"` (task 412 was the
# CURRENT witness for "retrieval finds nothing", per
# `test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing`'s own
# docstring). That rung's own `tmpl:item_mod_eq` FilterList predicate
# family (`item % c == r` / `!= r`, composed entirely from already-shipped
# `Mod`/`Eq`/`Not` -- zero new `TermNode` variants) makes the enumerator
# rung propose `FilterList(a, item, Eq(Mod(item,2),0))` for task 412
# ("remove odd numbers"), which the retrieval ladder's own rung d accepts
# and which passes its held-out row. Live-verified against the merged
# engine: `status: accepted, rung: 'd', exemplar: 775, holdout_ok: True`.
# `MEASURED_OUTCOMES` itself is UNTOUCHED, matching every prior drift
# dict's own discipline -- the supersession is recorded beside it.
# `test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing` itself
# is NOT re-pinned here (task 412 no longer stands for "finds nothing",
# but choosing its replacement witness is real, separate investigative
# work -- finding a new task with a LIVE-confirmed `rung == "none"`, per
# that test's own docstring warning -- left for a follow-on rung, not
# forced through here).
_KNOWN_CEILING_REASSESSMENT_5_DRIFT = {
    412: {"status": "accepted", "rung": "d", "exemplar": 775, "holdout_ok": True},
}


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def _run_task_live(task):
    from mbpp_endgame_battery import holdout_verdict  # noqa: E402 (heavy import)
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    s, ag = boot()
    out = {"task_id": task["task_id"]}
    try:
        r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
    except Exception as e:  # noqa: BLE001 — the pre-existing set-row residual
        out["exc"] = type(e).__name__
        return out
    out["status"] = r["status"]
    # 2026-08-01 (arc6 seam D, reconciled): the terminal REASON is read back
    # too — a mechanical read of what the rules already recorded, added so a
    # drifted pin can assert WHICH rung refused the goal instead of only
    # that it is no longer accepted (see `_KNOWN_ARC6_PROPERTY_REJECT_DRIFT`).
    out["gap_reason"] = r.get("gap_reason")
    out["rung"] = r.get("retrieval", {}).get("rung_reached")
    tid = r.get("retrieval", {}).get("accept_task_id")
    out["exemplar"] = int(tid) if tid is not None else None
    out["attempts"] = r.get("attempts")
    # 2026-08-01 (arc6 seam D, reconciled): the candidate IR is read back
    # whatever the terminal status, so a REFUSED candidate can be put in
    # front of a constructed witness instead of being taken on trust from
    # the rung that refused it.
    out["ir"] = r.get("ir")
    if r["status"] == "accepted" and spec["held_out"]:
        hv = holdout_verdict(r["ir"], spec["held_out"])
        out["holdout_ok"] = hv["all_ok"]
    return out


# ---------------------------------------------------------------------------
# 1) store loads clean, idempotent, IR reflected.
# ---------------------------------------------------------------------------
def test_exemplar_store_loads_clean_and_idempotent():
    manifest = manifest_for("mbpp_exemplars")
    assert manifest["id"] == "mbpp_exemplars"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    # the adapter's own idempotent install (Seed-marker guarded) — called
    # TWICE to prove the second call is a true no-op, the ensure_program_
    # synthesis precedent.
    pr.ensure_exemplar_store(s, s._inner, ag)
    n = len(s.nodes("Exemplar"))
    assert n == 90, "byte-identical to the Arc3-R0/Q3 measured 90/120 train emit rate"
    pr.ensure_exemplar_store(s, s._inner, ag)
    assert len(s.nodes("Exemplar")) == n
    # every Exemplar's IR is reflected into a subgraph exactly once.
    for ex in s.nodes("Exemplar"):
        roots = s.neighbours(ex, "ir_subgraph")
        assert len(roots) == 1


def test_exemplar_store_json_matches_installed_count():
    with open(EXEMPLAR_SEED_PATH) as f:
        d = json.load(f)
    assert len(d["nodes"]) == 90
    assert d["id"] == "mbpp_exemplars"


# ---------------------------------------------------------------------------
# 2) contamination — train-only provenance.
# ---------------------------------------------------------------------------
def test_every_exemplar_is_train_provenance_and_in_range():
    with open(EXEMPLAR_SEED_PATH) as f:
        d = json.load(f)
    for n in d["nodes"]:
        at = n["attrs"]
        assert at["provenance"] == "train"
        assert at["task_id"] >= 601, "canonical MBPP train split is task_id >= 601"


def test_build_script_never_reads_test_split_code_field():
    """AST-scan: scripts/build_exemplar_store.py never subscripts a task
    dict with ["code"] outside build_pool's train-scoped call (mirrors
    `test_retrieval_ceiling_migrated.py`'s own scan of retrieval_oracle_
    ceiling.py — build_exemplar_store reuses `build_pool` verbatim rather
    than reimplementing it, so its own source has ZERO ["code"] reads)."""
    import ast as _ast
    src = Path(ROOT, "scripts", "build_exemplar_store.py").read_text()
    tree = _ast.parse(src)
    hits = [n for n in _ast.walk(tree)
           if isinstance(n, _ast.Subscript)
           and isinstance(n.slice, _ast.Constant) and n.slice.value == "code"]
    assert hits == []


def test_shared_contamination_gate_passes():
    import subprocess
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", os.path.join(ROOT, "runners", "dsl", "python")
                  + ":" + ROOT + ":" + os.path.join(ROOT, "scripts"))
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]


# ---------------------------------------------------------------------------
# 3) scoring is fixed-formula arithmetic; SELECTION is a rule.
# ---------------------------------------------------------------------------
def test_selection_is_a_rule_top_k_rank_ordered_deterministic():
    s, ag = boot()
    m = psy.ingest_spec(s, ag,
                        "Write a python function to count true booleans in "
                        "the given list.",
                        [({"a": [True, False, True]}, 2), ({"a": [False, False]}, 0)])
    s._inner.run_rules(400000)
    g = s.in_neighbours(m, "about_message")[0]
    moved = pr.score_exemplars(s, ag, g)
    assert moved is True
    assert s.node(g)["attrs"].get("pr_scored") == 1.0
    # re-running the verb is a no-op (idempotent, per its own guard).
    assert pr.score_exemplars(s, ag, g) is False
    s._inner.run_rules(400000)
    cands = pr._candidate_pool(s, g)
    assert 1 <= len(cands) <= 5
    # every candidate is a real node id with real IR attached.
    for c in cands:
        assert c["ir"]["type"] == "ProgSeq"
    # determinism: a second, fresh boot picks the SAME candidate set/order.
    s2, ag2 = boot()
    m2 = psy.ingest_spec(s2, ag2,
                         "Write a python function to count true booleans in "
                         "the given list.",
                         [({"a": [True, False, True]}, 2), ({"a": [False, False]}, 0)])
    s2._inner.run_rules(400000)
    g2 = s2.in_neighbours(m2, "about_message")[0]
    pr.score_exemplars(s2, ag2, g2)
    s2._inner.run_rules(400000)
    cands2 = pr._candidate_pool(s2, g2)
    assert [c["task_id"] for c in cands] == [c["task_id"] for c in cands2]


def test_score_exemplars_computed_by_fixed_arithmetic_not_a_decision():
    """score_exemplars never sets `status` — every ScoreLink is a recorded
    FACT; `pr_select_candidate` (a seed rule) is the only thing that ever
    mints a `pr_candidate` edge."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag, "Write a function to count total characters "
                              "in a string.", [({"a": "hi"}, 2)])
    s._inner.run_rules(400000)
    g = s.in_neighbours(m, "about_message")[0]
    pr.score_exemplars(s, ag, g)
    assert s.nodes("ScoreLink"), "at least one candidate scored"
    for sl in s.nodes("ScoreLink"):
        at = s.node(sl)["attrs"]
        assert isinstance(at["score"], float)
    # before any rule ran, ZERO pr_candidate edges exist (selection is a
    # rule, never the verb's own side effect).
    assert s.neighbours(g, "pr_candidate") == []


# ---------------------------------------------------------------------------
# 4) scope guard — non-MBPP-shaped requests score zero exemplars.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "write a function double_fact that returns double the factorial of n",
    "write a function top_pick that picks the larger of two values.",
    "write a function count_positives that returns the count of positive "
    "numbers in a list.",
])
def test_non_mbpp_shaped_requests_score_zero_exemplars(text):
    assert pr._is_mbpp_shaped(text) is False
    s, ag = boot()
    m = psy.ingest_spec(s, ag, text, [({"n": 1}, 1)])
    s._inner.run_rules(400000)
    g = s.in_neighbours(m, "about_message")[0]
    pr.score_exemplars(s, ag, g)
    assert s.node(g)["attrs"].get("pr_scored") == 1.0
    assert s.neighbours(g, "pr_score") == []


def test_real_mbpp_prompt_is_recognized_shaped():
    assert pr._is_mbpp_shaped(
        "Write a python function to count true booleans in the given list.")


# ---------------------------------------------------------------------------
# 5) the ladder screens before accepting; a genuine accept spends ONE
#    ps_attempts, never more, regardless of how many candidates it tried.
# ---------------------------------------------------------------------------
def test_ladder_accept_spends_exactly_one_attempt():
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    by_id = {t["task_id"]: t for t in tasks}
    out = _run_task_live(by_id[138])
    assert out["status"] == "accepted"
    assert out["attempts"] == 1.0, "screening never touches ps_attempts (HR2)"


def test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing():
    """2026-08-01 arc4 S4 reconciliation: RE-PINNED from task 394 to task
    106. Task 394 ("check tuple contains no duplicates") used to genuinely
    find nothing at retrieval (rung "none"); S4's widened SynthEnumerate ops
    (`Last`/`Count`, composed for rung-d's generate-and-test hole fill) now
    let rung d retrieve exemplar 760 and fill its masked statement with
    `Last(a) > Count(a)` — this happens to fit task 394's 2 revealed rows
    AND its 1 held-out row, but is NOT a correct duplicate-check (verified:
    it disagrees on e.g. `a=(5, 1, 2)`, a genuinely distinct tuple it scores
    False) — a coincidental fit the single held-out row cannot catch, not a
    genuine retrieval capture (see PROGRAM_SYNTHESIS_ARC4_RECONCILE_NOTES.md
    for the counter-example proof; NOT added to CAPTURED_TASK_IDS below).
    Task 394 can therefore no longer stand for "retrieval finds nothing".
    Task 106 ("append the given list to the given tuples", a heterogeneous
    tuple+list concatenation the DSL has no op for at all) still genuinely
    finds nothing live, confirmed below — including the `attempts == 0.0`
    check this gate's own docstring (HR2: "a failing candidate never touches
    ps_attempts") always implied but never asserted.

    2026-08-02 (ARC 6 TIER 0): RE-PINNED AGAIN, 106 -> 412, for the same
    KIND of reason and in the improvement direction. The justification for
    the 394 -> 106 re-pin was that "the DSL has no op for [tuple+list
    concatenation] AT ALL"; `op:ConcatList` (arc-6 tier 0 — `Fold`+`Append`,
    the `JoinList` precedent, zero new `TermNode` variants) is now exactly
    that op, so 106 reaches rung d and the enumerator proposes the exact
    witness. 106 can therefore no longer stand for "retrieval finds
    nothing" (its new outcome is pinned in
    `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`).

    Task 412 does still genuinely find nothing live — `rung == "none"`,
    `attempts == 0.0`, gap `enumerate_failed` — verified against the same
    engine that produced this reconciliation, and it is what the pin now
    stands on. NOTE for whoever moves it next: a re-pin here is only ever
    valid if the NEW task's `rung == "none"` is confirmed LIVE, never
    inherited from `MEASURED_OUTCOMES`."""
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    by_id = {t["task_id"]: t for t in tasks}
    out = _run_task_live(by_id[412])
    assert out["status"] == "gapped"
    assert out["rung"] == "none"
    assert out["attempts"] == 0.0, "screening never touches ps_attempts (HR2)"


# ---------------------------------------------------------------------------
# 6) Occam order — rung (a) wins immediately when an exact-pass exists.
# ---------------------------------------------------------------------------
def test_occam_order_exact_pass_never_falls_through_to_deeper_rungs():
    """2026-08-01 (arc6 seam D, reconciled). THE MECHANISM CLAIM IS
    UNCHANGED AND STILL CHECKED: the retrieval ladder is Occam-ordered, so
    on task 105 it must settle at rung a/b/c and never silently fall
    through to rung d — that is what `out["rung"]` below still asserts,
    exactly as written.

    What changed FIRST (2026-08-01) was the TERMINAL VERDICT, and only
    that: Seam D's property rung (PROGRAM_SYNTHESIS_ARC6_D.md) refused
    task 105's rung-c candidate before it could be accepted, so `status`
    was `gapped` / `gap_reason` `property_verdict_reject` rather than
    `accepted`.

    2026-08-16 (PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY) — a SECOND
    supersession, and this one closes the "HONEST COVERAGE NOTE" gap this
    docstring used to record: `ps_property_reject_retrieval_enumerate_
    fallback` gives the refused rung-c candidate one independent second
    opinion via SynthEnumerate, gated on ALSO clearing the SAME fired
    PropertyAtom before the terminal gap fires. For 105, `Sum(a)` (True==1
    in Python, so summing a boolean list counts the True elements) clears
    `prop_count_true` AND passes the held-out row — task 105 is genuinely
    `accepted` now, not a coincidental fit papered over. The rung
    assertion below — the thing this fixture actually exists to prove — is
    UNCHANGED: `out["rung"]` still reads whichever rung the RETRIEVAL
    ladder itself reached (`retrieval.accept_task_id`/`rung_reached` are
    never touched by the property/enumerate machinery), so Occam ordering
    is still being checked exactly as written, now over a candidate this
    file can finally call correct."""
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    by_id = {t["task_id"]: t for t in tasks}
    out = _run_task_live(by_id[105])
    assert out["status"] == "accepted"
    assert out["holdout_ok"] is True
    assert out["rung"] == "a" or out["rung"] in ("a", "b", "c"), (
        "task 105 has a genuine rung-a exemplar (798) or a rung-c leaf-edit "
        "reachable within the top-5 ranked pool; it must never silently "
        "fall to rung d while an earlier rung would have fit")
    assert out["rung"] != "d"


# ---------------------------------------------------------------------------
# 7) ceiling capture — the phase headline.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tid", CEILING_TASK_IDS)
def test_ceiling_task_reproduces_measured_outcome_live(tid):
    """Every one of the 12 R0 ceiling task ids re-verified LIVE against the
    MEASURED_OUTCOMES baseline (never re-derived silently) — this is the
    ceiling-capture table's own data source. 2026-08-01 arc4 S4: task 394 is
    the ONE documented, understood exception (`_KNOWN_S4_DRIFT` above) — its
    live outcome now diverges from the frozen baseline because of a
    coincidental (not genuine) fit; `MEASURED_OUTCOMES` itself, and the
    headline capture count below, are untouched. 2026-08-01 arc4 S2: tasks
    242/284/414 are a SECOND, separate documented exception
    (`_KNOWN_S2_STRUCTURAL_REJECT_DRIFT` above) — their wrong holdout-failing
    accept is now correctly rejected outright; a REPLACEMENT (not merge),
    since a gapped row carries no exemplar/holdout_ok the way an accepted
    one does. 2026-08-01 arc6 seam D: tasks 105/238/405 are a THIRD
    documented exception (`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT` above) — same
    direction as the S2 one, this time refused by the property rung, each
    independently proven wrong-in-general by a constructed witness (the
    dedicated test below)."""
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    by_id = {t["task_id"]: t for t in tasks}
    out = _run_task_live(by_id[tid])
    if tid in _KNOWN_CEILING_REASSESSMENT_5_DRIFT:
        expect = dict(_KNOWN_CEILING_REASSESSMENT_5_DRIFT[tid])
    elif tid in _KNOWN_BUGFIX_SWEEP2_RUNG1_CASCADE_DRIFT:
        expect = dict(_KNOWN_BUGFIX_SWEEP2_RUNG1_CASCADE_DRIFT[tid])
    elif tid in _KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT:
        expect = dict(_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT[tid])
    elif tid in _KNOWN_ARC6_PROPERTY_REJECT_DRIFT:
        expect = dict(_KNOWN_ARC6_PROPERTY_REJECT_DRIFT[tid])
    elif tid in _KNOWN_S2_STRUCTURAL_REJECT_DRIFT:
        expect = dict(_KNOWN_S2_STRUCTURAL_REJECT_DRIFT[tid])
    else:
        expect = dict(MEASURED_OUTCOMES[tid])
        expect.update(_KNOWN_S4_DRIFT.get(tid, {}))
    if "exc" in expect:
        assert out.get("exc") == expect["exc"]
        return
    assert out["status"] == expect["status"]
    if "gap_reason" in expect:
        assert out["gap_reason"] == expect["gap_reason"]
    assert out["rung"] == expect["rung"]
    if "exemplar" in expect:
        assert out["exemplar"] == expect["exemplar"]
    if "holdout_ok" in expect:
        assert out["holdout_ok"] == expect["holdout_ok"]


# 2026-08-01 (arc6 seam D, reconciled). The CONSTRUCTED WITNESS behind
# `_KNOWN_ARC6_PROPERTY_REJECT_DRIFT` — the task-92/464 method of
# tests/test_reject_informs_repair_migrated.py, applied here so the
# supersession of three pins rests on a proof this suite RUNS, not on the
# frozen `holdout_ok: False` flag and not on the refusing rung's own word.
#
# Every input below is hand-picked to be NEITHER a revealed row, NOR the
# held-out row, NOR the PropertyAtom's own witness env (compare
# PROGRAM_SYNTHESIS_ARC6_D.md §2.1: atoms fire on a=1 / [True,True,False] /
# a=100,b=150 ...), and the expected value comes from the task's OWN
# reference implementation in the fixture (`code`), executed here — not
# from any part of the synthesis pipeline.
# 2026-08-16: task 105 REMOVED (PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY --
# see `_KNOWN_ARC6_PROPERTY_REJECT_DRIFT`'s own updated comment) -- its
# candidate is no longer wrong by construction, it is genuinely correct, so
# a "prove it wrong" witness no longer applies. 238/405 are untouched.
_ARC6_WRONG_BY_CONSTRUCTION = {
    238: ("number_of_substrings", (
        ({"a": "ab"}, 10, 3),
        ({"a": "z"}, 10, 1),
    )),
    405: ("check_tuplex", (
        ({"a": ["x", "y"], "b": "y"}, False, True),
        ({"a": ["q"], "b": "r"}, True, False),
    )),
}


@pytest.mark.parametrize("tid", sorted(_ARC6_WRONG_BY_CONSTRUCTION))
def test_arc6_property_rejected_ceiling_candidates_are_wrong_by_construction(tid):
    """Proof — never assertion — that the three candidates the property
    rung now refuses were WRONG IN GENERAL, so `_KNOWN_ARC6_PROPERTY_
    REJECT_DRIFT` is a correction and not a capability this build took
    away. The candidate the live retrieval ladder actually builds is
    evaluated through the same ProgEval term every verdict path uses, on
    inputs it never saw, against the task's own reference implementation."""
    import mbpp_arc3_battery as arc3b  # noqa: E402 (heavy import)
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    by_id = {t["task_id"]: t for t in tasks}
    task = by_id[tid]
    out = _run_task_live(task)
    ir = out["ir"]
    assert ir is not None, (tid, "no candidate IR to put a witness to")
    # the reference implementation, from the fixture itself.
    ns: dict = {}
    exec(task["code"], ns)  # noqa: S102 — the fixture's own reference row
    fname, cases = _ARC6_WRONG_BY_CONSTRUCTION[tid]
    ref = ns[fname]
    for env, expect_got, expect_ref in cases:
        ev = arc3b.prog_eval(ir, env)
        got = ev.get("result")
        args = ([tuple(env["a"]), env["b"]] if tid == 405
                else [list(env["a"])] if tid == 105 else [env["a"]])
        truth = ref(*args)
        assert got == expect_got, (tid, env, got, ev)
        assert truth == expect_ref, (tid, env, truth, "reference drift")
        assert got != truth, (
            tid, env, "this witness no longer refutes the candidate")


def test_ceiling_capture_headline_count():
    """The headline: 2/12 R0 ceiling tasks are genuinely CAPTURED (accepted
    via retrieval AND pass the never-revealed held-out row) — a real,
    measured, honest number, reported with its denominator and reasons for
    every miss in PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md's own table."""
    captured = [tid for tid, o in MEASURED_OUTCOMES.items()
               if o.get("status") == "accepted" and o.get("holdout_ok") is True
               and o.get("rung") not in (None, "none")]
    assert sorted(captured) == sorted(CAPTURED_TASK_IDS)
    assert len(captured) == 2


# ---------------------------------------------------------------------------
# 8) NO-PYTHON-DECISION source audit (the ink-suite / P4-B pattern).
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_prog_retrieval_no_argmin_argmax_or_key_sorted_decisions():
    """domains/prog_retrieval.py never calls .argmin/.argmax or min/max(key=)
    — every SELECTION among goal-visible alternatives (which exemplar to
    retrieve, whether to admit/exclude a screen result) is a seed rule
    (`pr_*`); this module's OWN `best`/`consider` reduction picks the
    NEAR-MISS ANCHOR for the bounded rung-(c)/(d) generate-and-test SEARCH
    (the SynthEnumerate-class engine seam the task brief directs to Python
    here, no Rust primitive existing for it) — the SAME class of bounded,
    deterministic search `run_enumerate` already delegates to Rust for the
    codebook rung; every RESULT the search produces is only ever RECORDED
    as a fact (`pr_rung_reached`/`pr_accept_*`), never used to set `status`
    from this module."""
    src = Path(pr.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)


def test_prog_retrieval_never_sets_goal_status():
    """Every function in domains/prog_retrieval.py records facts; only a
    seed rule ever transitions a Goal's `status` attr."""
    src = Path(pr.__file__).read_text()
    assert 'set_attr(g, "status"' not in src
    assert "'status'" not in src.replace('"status"', "")  # no alt-quote form


# ---------------------------------------------------------------------------
# 9) the codebook-side universal screen: Attempt 1's EXACT design stays
#    dead (never resurrected under its own rule names); the CORRECTED,
#    scoped redo (Arc3-R2.5, seed v1.5.1) lands under different names
#    (`ps_screen_*`, not `pr_screen_*`) and a different (SCREENABLE/
#    NOT-DESCEND_APPLICABLE) discriminator — see
#    PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md for the Attempt-1 revert story
#    this guards against repeating, and `tests/test_screen_codebook_
#    migrated.py` for the corrected redo's own dedicated gates.
# ---------------------------------------------------------------------------
def test_attempt1_codebook_screen_rules_stay_absent_from_the_seed():
    """2026-08-01 arc4 S1 reconciliation: S1 (budget isolation) bumped the
    seed to v1.6.0/58 rules, adding exactly one new rule
    (`ps_isolate_fallthrough`). The literal name/count checks below are
    updated to the real current values, but this gate's actual job is
    guarding an INTENT — "no rule may re-decide a partial-cover candidate's
    correctness the way Attempt-1's codebook screen did" — not just a
    banned-name list, so a future rule that reintroduced screening under an
    unrelated name would slip past a purely literal check. Two intent-level
    guards are added: (1) EVERY rule whose name even mentions "screen" must
    be exactly the 3 CORRECTED `ps_screen_*` ones — a generalisation of the
    banned-list check that would catch a differently-named-but-still-
    screen-shaped rule too, as long as it is honest about being a screen;
    (2) `ps_isolate_fallthrough` itself is checked STRUCTURALLY, not just by
    name: its own seed comment says it is "ISOLATION, not screening: no
    candidate's correctness is judged here" (unlike `ps_screen_reject`/
    `ps_screen_admit`, which each mint an Excluded/ScreenPass node keyed on
    a dry-run EVALUATION of a candidate) — verified by asserting its ONLY
    effect is a status flip (`set_attr`), never an Excluded/ScreenPass mint,
    which is exactly what would make it a screen in disguise."""
    with open(SYNTH_SEED_PATH) as f:
        d = json.load(f)
    names = {r["name"] for r in d["rules"]}
    for banned in ("pr_screen_mark", "pr_screen_none_eligible", "pr_screen_admit",
                  "pr_screen_reject", "pr_screen_exhausted"):
        assert banned not in names
    # Arc3-R2.5 (this phase): the CORRECTED codebook screen lands under
    # its own `ps_screen_*` names (3 new rules: ps_screen_mark,
    # ps_screen_reject, ps_screen_admit), never the Attempt-1 `pr_screen_*`
    # ones banned above.
    for landed in ("ps_screen_mark", "ps_screen_reject", "ps_screen_admit"):
        assert landed in names
    # intent guard (1): no OTHER screen-shaped rule exists under any name.
    screen_named = {n for n in names if "screen" in n.lower()}
    assert screen_named == {"ps_screen_mark", "ps_screen_reject", "ps_screen_admit"}, \
        "a new screen-shaped rule appeared under a name this gate doesn't " \
        "already know — review it against the Attempt-1 regression before " \
        "widening this set"
    # intent guard (2): arc4-S1's new rule is structurally isolation, not
    # screening — it never mints Excluded/ScreenPass (a candidate verdict).
    assert "ps_isolate_fallthrough" in names
    iso = next(r for r in d["rules"] if r["name"] == "ps_isolate_fallthrough")
    eff_kinds = {e[0] for e in iso["effects"]}
    assert eff_kinds == {"set_attr"}, \
        "ps_isolate_fallthrough must only flip status — minting an " \
        "Excluded/ScreenPass node here would mean it is judging a " \
        "candidate's correctness, i.e. it would BE a screen"
    # 2026-08-01 (arc4 S2 reconciliation): S2 landed two new rules
    # (`ps_structural_reject`/`ps_structural_clear`) and bumped the seed
    # 1.6.0 -> 1.7.0, 58 -> 60 rules (PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md
    # §8) — neither name contains "screen", so the intent guard above is
    # unaffected; pure version/count pin update.
    # 2026-08-01 (arc4 S6): v1.7.0/60 -> v1.8.0/63. S6 replaced the single
    # `ps_structural_reject` (straight-to-gapped) with four routed rules
    # (exclusion_gap / exclusion_reopen / repair_gap / repair_reopen) so a
    # structural rejection INFORMS repair instead of terminating the goal.
    # 2026-08-01 (arc5 exact-first): v1.8.0/63 -> v1.9.0/66. Added the
    # SHAPE-FIRST rung (ps_exact_mark/_solved/_failed): a family fit over
    # rational parameters + a cross-frame constant, ahead of enumerate.
    # 2026-08-01 (arc5 moves, reconciled): v1.9.0/66 -> v1.10.0/70. Added
    # RUNG 2.6 (ps_move_mark/_select/_none/_fresh_attempt: orbit
    # augmentation + intermediate decomposition, PROGRAM_SYNTHESIS_ARC5_
    # MOVES.md) — none of the four new names contains "screen", so the
    # intent guard above is unaffected; pure version/count pin update.
    # 2026-08-01 (arc6 seam D, reconciled): v1.10.0/70 -> v1.11.0/73. Added
    # the PROPERTY-REFUTATION rung (ps_property_clear / ps_property_reject_
    # gap / ps_property_reject_reopen, PROGRAM_SYNTHESIS_ARC6_D.md §1) —
    # none of the three new names contains "screen" either, so the intent
    # guard above (attempt-1 codebook SCREEN rules stay absent) still bites
    # exactly as written; pure version/count pin update.
    assert d["version"] == "1.13.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    # 2026-08-16: v1.12.0/73 -> v1.13.0/74, PROGRAM_SYNTHESIS_PROPERTY_
    # REJECT_SURVEY's ps_property_reject_retrieval_enumerate_fallback rule
    # -- its name doesn't contain "screen" either, and it never mints an
    # Excluded/ScreenPass node (its only effects are set_attr, the SAME
    # ps_isolate_fallthrough isolation shape checked above): it admits a
    # goal into the enumerate rung, it does not judge a candidate's
    # correctness itself, so both intent guards are unaffected.
    assert len(d["rules"]) == 74


def test_la10_partial_cover_regression_scenario_reproduces_original_rungs():
    """The EXACT scenario the codebook-side screen (before reversion) broke:
    a partial-cover codebook construction (count_of_list) that does not fit
    every revealed row alone but is descent's correct starting point once a
    hole is filled — ps_propose must still run (rung_codebook==1.0) and
    ps_attempts must be spent, exactly as before Arc3."""
    with open(os.path.join(ROOT, "tests", "fixtures", "prog_synthesis_battery",
                           "tasks.json")) as f:
        tasks = {t["id"]: t for t in json.load(f)["tasks"]}
    t = tasks["la_10_count_positives"]
    ex = [(r["inputs"], r["expected"]) for r in t["example_rows"]]
    s, ag = boot()
    m = psy.ingest_spec(s, ag, t["request_text"], ex)
    psy.pump(s, ag)
    g = s.in_neighbours(m, "about_message")[0]
    r = psy.read_goal(s, g)
    assert r["status"] == "accepted"
    assert r["attempts"] == 1.0
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["descend"] == 1.0
    assert r["construction"] == "count_of_list"
