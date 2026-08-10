"""test_screen_codebook_migrated — Arc3-R2.5 gates: the SCOPED codebook-side
half of the universal execution screen (`seeds/program_synthesis.json`
v1.5.0 -> v1.5.1: `ps_screen_mark`/`ps_screen_reject`/`ps_screen_admit`;
`domains/prog_synthesis.py`: `screen_construction`).

Companion docs: `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` (the Attempt-1 screen
this rung redoes, and the EXACT false-negative — a legitimate PARTIAL-COVER
construction descent depends on — that sank it), `PROGRAM_SYNTHESIS_ARC2_
Q5.md` (the decoy-tax mechanism this screen kills: a chunk/codebook-cued
WRONG COMPLETE construction occupies attempts until exhaustion),
`PROGRAM_SYNTHESIS_ARC3_PREREG.md` §HR2 (the registered bar: cued
`gapped:exhausted` -> ~0; attempts-per-accept non-increasing).

THE DISCRIMINATOR (reused, not invented): a goal is SCREENABLE iff it is
NOT DESCEND_APPLICABLE — the SAME 3-part predicate `ps_descend_mark`/
`ps_enumerate_mark` already embed (a trigger-matching construction covers
part of the request AND (some revealed row carries a LIST input OR some
trigger-matching construction is scalar-fold/branch-shaped) AND the depth
budget allows) — AND it carries at least one revealed example row AND its
INITIAL trigger-matching codebook pool (frozen at mint, `ps_screen_pool0`)
is not smaller than its FULL attempt budget (`ps_screen_engage`, ALSO
frozen at mint — see `ps_propose`'s own seed comment for why a per-round
recomputation against a SHRINKING remaining budget was tried and measurably
wrong, catching a second regression against `test_prog_synthesis_battery_
migrated.py`'s frozen `br_19_pick_or_boost` row). Every partial-cover-
eligible goal (DESCEND_APPLICABLE) is therefore untouched BY CONSTRUCTION,
not by luck, and every goal that already had enough attempt-budget slack to
succeed unscreened is ALSO untouched, by the SAME frozen-at-mint construction.

Gates:
  1. THE DECOY-KILL (the exact HR2 mechanism): a chunk-cued WRONG COMPLETE
     construction pool larger than the attempt budget is killed AT THE
     SCREEN, for free — zero real `ps_attempts` spent on any of them — and
     the goal reaches the enumerator with its FULL budget to spend.
  2. A partial-cover fixture (la_10_count_positives) descends UNSCREENED:
     byte-identical rungs/attempts to the pre-Arc3-R2.5 mechanism, AND
     `screen.kills == 0` (the screen never even engaged).
  3. A RIGHT complete construction, mixed into an over-budget decoy pool,
     PASSES the screen and is accepted spending EXACTLY one real attempt.
  4. Screen-budget honesty: kills + real attempts + excluded bookkeeping
     are internally consistent; no goal ever PARKS on a non-terminal
     status (`screen_running`/`pending`) — every fixture above reaches a
     terminal status (`accepted`/`gapped`).
  5. NO-PYTHON-DECISION source audit of `screen_construction` specifically
     (the ink-suite pattern, scoped to the new verb's own source span).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_screen_codebook_migrated.py
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

from domains import prog_synthesis as psy  # noqa: E402

SYNTH_SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
BATTERY_TASKS_PATH = os.path.join(ROOT, "tests", "fixtures",
                                  "prog_synthesis_battery", "tasks.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                   "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                   "wild_objects": False}, {"g": [["p", "x"]]}) or \
   not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ShapeDecode/ProgEval not present in the installed "
                "substrate_rs binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def run(s, ag, text, examples=()):
    m = psy.ingest_spec(s, ag, text, examples)
    psy.pump(s, ag)
    goals = s.in_neighbours(m, "about_message")
    assert len(goals) == 1, "exactly one goal per request message"
    return psy.read_goal(s, goals[0])


def _teach_chunk(s, name, triggers, wrong_value, arg="a"):
    """A CHUNK-SHAPED decoy (`mode: code_write_stmts`, single ProgReturn
    statement) — the SAME structural shape Q5's own dominant decoy class
    (`ck_*`/`mck_*` mined/diet chunks) carries, never `tmpl_branch`/
    `tmpl_scalar_fold` (those flags are stamped ONLY for `mode: code_write`
    single-EXPRESSION templates — `_normalise_fold_marks`'s own `is_
    code_write` gate — so a chunk can never itself satisfy DESCEND_
    APPLICABLE's Or-clause; this is exactly the class Arc3-R2.5's screen
    targets, per its own comment)."""
    s.add_node("ShapeSignature", {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
        "ground_template": json.dumps({
            "desc": "chunk decoy", "args": [arg], "mode": "code_write_stmts",
            "stmts": [{"type": "ProgReturn",
                      "value": {"type": "Lit", "value": wrong_value}}],
        })})


def _teach_expr(s, name, triggers, term, arg="a"):
    """A plain single-EXPRESSION construction (`mode: code_write`) — used
    for the ONE genuinely CORRECT candidate in gate 3 below. `term` must
    not be an `IfThenElse`/`Fold` (that would stamp `tmpl_branch`/
    `tmpl_scalar_fold` and make the WHOLE goal DESCEND_APPLICABLE via this
    SAME construction, exempting it from screening entirely — arithmetic
    keeps it cleanly outside that class)."""
    s.add_node("ShapeSignature", {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
        "ground_template": json.dumps(
            {"desc": "expr", "term": term, "args": [arg], "mode": "code_write"})})


# ---------------------------------------------------------------------------
# 1) THE DECOY-KILL — the exact HR2 mechanism gate.
# ---------------------------------------------------------------------------
def test_over_budget_chunk_decoy_pool_dies_at_the_screen_and_reaches_enumerate():
    """4 chunk-shaped WRONG decoys (pool0=4) against the goal's fixed
    budget (3): the classic propose/exclude/reproposal mechanism could
    NEVER try all 4 for real without exhausting the budget first (Q5's
    exact `gapped:exhausted` decoy-tax shape) — Arc3-R2.5's screen kills
    every one of them for FREE instead, so the goal reaches the enumerator
    with its FULL budget untouched and finds the (trivial, single-row)
    correct answer at attempt 0."""
    s, ag = boot()
    trigs = [["QUUX", "ALPHA", "BETA", "GAMMA"],
             ["QUUX", "ALPHA", "BETA"],
             ["QUUX", "ALPHA"],
             ["QUUX"]]
    for i, t in enumerate(trigs):
        _teach_chunk(s, "chunk_decoy_%d" % i, t, wrong_value=0)
    r = run(s, ag, "write a function quux_fn that returns the quux alpha "
                   "beta gamma of a number", [({"a": 5}, 5)])
    # every decoy died at the screen — a fact the taxonomy can count.
    assert r["screen"]["kills"] == 4.0
    assert set(r["excluded"]) == {"chunk_decoy_%d" % i for i in range(4)}
    # NOT ONE of them ever reached ps_propose: the codebook rung never
    # fires at all for this goal (screened out before propose could pick).
    assert r["rungs"]["codebook"] is None
    assert r["rungs"]["lattice"] is None
    assert r["rungs"]["descend"] is None
    # THE POINT: attempts stayed at the frozen 0 — the decoy tax cost
    # NOTHING — and the goal reached a TERMINAL status via the enumerator,
    # with its full budget spendable (never parked, never exhausted).
    assert r["attempts"] == 0.0
    assert r["budget"] == 3.0
    assert r["rungs"]["enumerate"] == 1.0
    assert r["enumerate_outcome"] == "ok"
    assert r["status"] == "accepted"
    assert r["gap_reason"] is None
    assert r["counterexamples"] == [], \
        "a screen kill is never a real counterexample"


def test_screen_kill_marks_excluded_nodes_screened_failed():
    """The per-Excluded-node `screened_failed` tag (the taxonomy hook) is
    present on every screen-killed construction and absent from a real
    exclusion — verified directly on the graph, not just via the
    `read_goal` aggregate."""
    s, ag = boot()
    trigs = [["FOX", "GOLF", "HOTEL", "INDIA"],
             ["FOX", "GOLF", "HOTEL"],
             ["FOX", "GOLF"],
             ["FOX"]]
    for i, t in enumerate(trigs):
        _teach_chunk(s, "fox_decoy_%d" % i, t, wrong_value=-1)
    r = run(s, ag, "write a function fox_fn that returns the fox golf "
                   "hotel india of a number", [({"a": 9}, 9)])
    excluded_nodes = list(s.neighbours(r["goal"], "ps_excluded"))
    assert len(excluded_nodes) == 4
    for x in excluded_nodes:
        assert s.node(x)["attrs"].get("screened_failed") == 1.0
    assert r["status"] == "accepted" and r["attempts"] == 0.0


# ---------------------------------------------------------------------------
# 2) partial-cover descends UNSCREENED — byte-identical, by construction.
# ---------------------------------------------------------------------------
def test_partial_cover_construction_descends_unscreened():
    """la_10_count_positives (`count_of_list`, a genuine PARTIAL cover the
    descent rung consumes once a hole is filled in) — the EXACT scenario
    Attempt 1's screen broke (PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md §1):
    `has_list_input` makes this goal DESCEND_APPLICABLE, so
    `ps_screen_mark` never fires for it AT ALL — rungs/attempts reproduce
    the pre-Arc3-R2.5 mechanism byte-for-byte, and the screen's own
    kill-count stays at zero (it never engaged, not merely 'engaged and
    happened to admit everything')."""
    with open(BATTERY_TASKS_PATH) as f:
        tasks = {t["id"]: t for t in json.load(f)["tasks"]}
    t = tasks["la_10_count_positives"]
    ex = [(row["inputs"], row["expected"]) for row in t["example_rows"]]
    s, ag = boot()
    r = run(s, ag, t["request_text"], ex)
    assert r["status"] == "accepted"
    assert r["attempts"] == 1.0
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["descend"] == 1.0
    # the screen was never even asked to judge anything for this goal.
    assert r["screen"]["kills"] == 0.0
    assert r["screen"]["candidate"] is None
    assert r["screen"]["verdict"] is None
    # the accept is real and executable (P7-A's own §2.2 class: this
    # task's derived rows underdetermine the hole, so the accepted program
    # may or may not generalise past the 3 revealed rows —
    # `test_prog_descent_migrated.py::
    # test_weak_derived_rows_are_caught_by_the_outer_verdict_terminally`
    # already documents and owns that residual; THIS gate's only concern
    # is that the screen never touched this goal, not the held-out digit).
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert len(roots) == 1
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": {"items": [2, -4, 6, -8, 10]}, "p": roots[0]})
    assert out["trap"] is None and out["halted"] is True


# ---------------------------------------------------------------------------
# 3) a RIGHT complete construction passes the screen, spends ONE attempt.
# ---------------------------------------------------------------------------
def test_right_construction_mixed_into_overbudget_pool_passes_screen_one_attempt():
    """3 wrong, higher-specificity chunk decoys (pool0=4 with the correct
    one, still > budget=3) PLUS one genuinely correct, lowest-specificity
    expression construction (`Plus(a, a)` — 'double the number'): every
    wrong decoy is screened out for free (in specificity order), and the
    correct one — reached last, since it declares the fewest trigger
    tokens — PASSES the dry-run screen and is handed to ps_propose, which
    spends EXACTLY one real attempt confirming it. attempts-per-accept
    (1.0) is a strict improvement over what the classic mechanism would
    have needed here (3 real failed attempts to exhaust the wrong pool,
    THEN a 4th to find the right one — one past this goal's own budget of
    3, i.e. the classic mechanism would have GAPPED this exact pool)."""
    s, ag = boot()
    wrong_trigs = [["DOUBLIT", "KILO", "LIMA", "MIKE"],
                   ["DOUBLIT", "KILO", "LIMA"],
                   ["DOUBLIT", "KILO"]]
    for i, t in enumerate(wrong_trigs):
        _teach_chunk(s, "doublit_wrong_%d" % i, t, wrong_value=0)
    _teach_expr(s, "doublit_right", ["DOUBLIT"],
               {"type": "Plus", "items": [{"type": "Var", "name": "a"},
                                          {"type": "Var", "name": "a"}]})
    r = run(s, ag, "write a function doublit_fn that returns the doublit "
                   "kilo lima mike of a number",
            [({"a": 3}, 6), ({"a": 5}, 10)])
    assert r["screen"]["kills"] == 3.0
    assert set(x for x in r["excluded"] if x != "doublit_right") == \
        {"doublit_wrong_%d" % i for i in range(3)}
    assert "doublit_right" not in r["excluded"]
    assert r["construction"] == "doublit_right"
    assert r["rungs"]["codebook"] == 1.0
    assert r["status"] == "accepted"
    # THE POINT: exactly one real attempt — the screen-verified winner.
    assert r["attempts"] == 1.0
    assert r["counterexamples"] == []
    roots = s.neighbours(r["program"], "ir_subgraph")
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": {"a": 11}, "p": roots[0]})
    assert out["result"] == 22, "held-out: double(11) == 22"


# ---------------------------------------------------------------------------
# 4) screen-budget honesty — internal bookkeeping, no parks.
# ---------------------------------------------------------------------------
def test_screen_bookkeeping_is_internally_consistent_no_parks():
    """Across every fixture above: kills + real codebook attempts account
    for the FULL excluded set (no double counting, no unaccounted
    exclusions), and every goal reaches a TERMINAL status — never left on
    `pending`/`screen_running` (a park would mean `pump`'s fixpoint gave
    up mid-decision, exactly the P6.5-class defect this project treats as
    a hard regression)."""
    scenarios = []

    s1, ag1 = boot()
    for i, t in enumerate([["N1", "N2", "N3", "N4"], ["N1", "N2", "N3"],
                          ["N1", "N2"], ["N1"]]):
        _teach_chunk(s1, "n_decoy_%d" % i, t, wrong_value=0)
    r1 = run(s1, ag1, "write a function n_fn that returns the n1 n2 n3 n4 "
                     "of a number", [({"a": 8}, 8)])
    scenarios.append((s1, r1, 4))  # 4 real-or-screened exclusions expected

    with open(BATTERY_TASKS_PATH) as f:
        tasks = {t["id"]: t for t in json.load(f)["tasks"]}
    t2 = tasks["la_10_count_positives"]
    ex2 = [(row["inputs"], row["expected"]) for row in t2["example_rows"]]
    s2, ag2 = boot()
    r2 = run(s2, ag2, t2["request_text"], ex2)
    scenarios.append((s2, r2, 1))  # count_of_list itself, excluded once

    for sub, r, expected_excluded in scenarios:
        assert r["status"] in ("accepted", "gapped"), \
            "parked on a non-terminal status: %r" % r["status"]
        assert len(r["excluded"]) == expected_excluded
        real_exclusions = sum(
            1 for x in sub.neighbours(r["goal"], "ps_excluded")
            if sub.node(x)["attrs"].get("screened_failed") != 1.0)
        screen_exclusions = int(r["screen"]["kills"])
        assert real_exclusions + screen_exclusions == expected_excluded
        # a screen kill NEVER inflates ps_attempts.
        assert r["attempts"] <= r["budget"]
        assert float(r["attempts"]).is_integer()


# ---------------------------------------------------------------------------
# 5) NO-PYTHON-DECISION source audit, scoped to screen_construction.
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def _screen_construction_source() -> str:
    src = Path(psy.__file__).read_text()
    start = src.index("def screen_construction(")
    # the next top-level `def ` after screen_construction's own body.
    end = src.index("\ndef ", start + 1)
    return src[start:end]


def test_screen_construction_makes_no_decision_only_records_a_verdict():
    """`screen_construction` is a VERB (the `_enact_advance` sense): it
    dry-runs a candidate and records ONE fact, `ps_screen_verdict` — it
    never sets `status`, never mints an `Excluded`/`ScreenPass` node
    (`ps_screen_reject`/`ps_screen_admit`, seed rules, do that), never
    touches `ps_excluded`/`ps_screen_passed`, and contains no argmin/
    argmax/sort-on-score Python decision. SCREENABLE itself (NOT
    DESCEND_APPLICABLE AND has-examples AND NO_SLACK) is entirely seed
    `where`-clause data (`ps_screen_mark`) this verb never re-derives —
    it is invoked ONLY once the seed rule has already armed it."""
    src = _screen_construction_source()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    assert 'set_attr(g, "status"' not in src
    assert "sub.add_node" not in src
    assert "sub.add_edge" not in src
    assert "DESCEND_APPLICABLE" not in src
    assert "ps_excluded" not in src
    assert "ps_screen_passed" not in src
