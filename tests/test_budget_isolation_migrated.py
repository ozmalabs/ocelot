"""test_budget_isolation_migrated — Arc4-S1 gates: BUDGET ISOLATION
(`PROGRAM_SYNTHESIS_ARC4_PLAN.md` §2-S1, `PROGRAM_SYNTHESIS_ARC4_PREREG.md`
§1 HA1, `PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md`).

Every non-search proposal source (codebook propose + retrieval) draws from
its own separate, bounded PROPOSAL lane (`ps_propose_attempts`/
`ps_propose_budget`, seed v1.6.0); the enumerator draws from a RESERVED,
untouchable lane (`ps_enum_reserve_used`/`ps_enum_reserve_budget`) that no
proposal-lane consumption can ever reduce. Exhausting the propose lane no
longer terminally exhausts a goal while a next rung (descent or the
reserved enumerator) is still reachable — `ps_isolate_fallthrough` re-arms
to `pending` instead of `ps_ce_exhausted`/`ps_exhausted` firing, and
`ps_descend_mark`/`ps_enumerate_mark`'s own entry guards no longer depend
on the shared `ps_attempts`/`ps_budget` lane at all.

Companion docs: `PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md` (the measured
17-id target list: class (a) descend-applicable 286/296/415/463/468/
471/476, class (b) cued-but-screen-disengaged 108/119/222/223/229/240/
245/280/394/431), `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` §9 (R2.5's screen
— the mechanism this phase generalises, and the Attempt-1 false-negative
this phase's design deliberately does NOT repeat: isolation never judges
a candidate's correctness, it only changes which budget counter gates
entry into the next rung).

Gates:
  1. seed structure — version 1.6.0, the new counters exist at mint, the
     new rule (`ps_isolate_fallthrough`) is present, rule count is 58.
  2. THE 17-ID HEADLINE — every id in HA1's measured target list, run
     end-to-end on FULL-R3 (PRIMARY protocol, the arc3 battery driver
     pattern): 16/17 escape `gapped:exhausted` entirely; the one named
     residual (222) is root-caused LIVE, not excused — the enumerator and
     descent BOTH demonstrably got their guaranteed turn
     (`rungs.enumerate==1.0`, `enumerate_outcome=='ok'`) before an
     UNRELATED, pre-existing, unchanged lane (the P7-B enum-retry round
     budget, `ps_enum_round`/`ps_enum_round_budget`) separately exhausted
     — a genuinely different event from budget STARVATION, sharing only
     the status string.
  3. RESERVED-BUDGET INVARIANT — a pathological all-wrong proposal pool
     (20 decoys vs 4) cannot reduce the enumerator's own turn or the
     propose lane's own real-attempt count: both pool sizes produce
     byte-identical `attempts`/`excluded`/`rungs` (pinned numbers).
  4. ISOLATION IS NOT SCREENING — a SCREENABLE goal (R2.5's own decoy-kill
     fixture, pool0 >= budget) is COMPLETELY UNCHANGED by S1: the screen
     still kills every decoy for free, `ps_propose_attempts` never moves,
     `ps_isolate_fallthrough` never fires (screening prevents a real
     attempt; isolation only reroutes what happens once real attempts are
     spent — the two mechanisms have disjoint triggers, verified live).
  5. NO-PARK — every fixture in this file reaches a TERMINAL status
     (never `pending`/`counterexample`/`screen_running`/`enumerate_pending`
     left dangling).
  6. NO-PYTHON-DECISION source audit of the modified adapter surface
     (`domains/prog_synthesis.py`'s new `isolation` read-back in
     `read_goal`).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_budget_isolation_migrated.py
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
from domains import mbpp_spec as ms  # noqa: E402
import mbpp_arc3_battery as bat  # noqa: E402 — THE driver, reused, not modified

SYNTH_SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

# PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md §1 — the measured, complete
# gapped:exhausted target list (17 ids, classes (a)+(b), (c)/(d) empty).
TARGET_IDS = (286, 296, 415, 463, 468, 471, 476,       # class (a)
             108, 119, 222, 223, 229, 240, 245, 280, 394, 431)  # class (b)

# The ONE named, root-caused residual (see gate 2's own docstring below):
# task 222 demonstrably exercises BOTH descent and the reserved enumerator
# (rungs.descend==1.0, rungs.enumerate==1.0, enumerate_outcome=='ok') before
# a SEPARATE, pre-existing, S1-unrelated lane (the P7-B enum-retry round
# budget) independently exhausts and the classic (untouched) exclude/
# reproposal path closes the goal — a genuinely different event from the
# starvation this phase targets, sharing only the terminal status string.
KNOWN_NON_STARVED_RESIDUAL_IDS = frozenset({222})


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


_TERMINAL_STATUSES = {"accepted", "gapped", "no_shape", "enumerate_unavailable"}


def _teach_decoy(s, name, triggers, term, args, *, branch=False):
    """Verbatim of test_program_synthesis_migrated.py's own helper — a
    DESCEND_APPLICABLE (branch-shaped) wrong decoy, the shape class (a)'s
    own 7 ids are built from."""
    attrs: dict = {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
    }
    if branch:
        term = {"type": "IfThenElse", "cond": {"type": "Lit", "value": True},
                "then": term, "other": term}
        attrs.update(tmpl_fold=0.0, tmpl_scalar_fold=0.0, tmpl_branch=1.0)
    attrs["ground_template"] = json.dumps(
        {"desc": "gate decoy", "term": term, "args": list(args),
         "mode": "code_write"})
    s.add_node("ShapeSignature", attrs)


def _teach_chunk(s, name, triggers, wrong_value, arg="a"):
    """Verbatim of test_screen_codebook_migrated.py's own helper — a
    CHUNK-shaped (`mode: code_write_stmts`) decoy, structurally incapable
    of tmpl_branch/tmpl_scalar_fold (`_normalise_fold_marks`'s own
    `mode == 'code_write'` gate) — the dominant class (b) decoy shape."""
    s.add_node("ShapeSignature", {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
        "ground_template": json.dumps({
            "desc": "chunk decoy", "args": [arg], "mode": "code_write_stmts",
            "stmts": [{"type": "ProgReturn",
                      "value": {"type": "Lit", "value": wrong_value}}],
        })})


# ---------------------------------------------------------------------------
# 1) seed structure.
# ---------------------------------------------------------------------------
def test_seed_version_and_isolation_lanes_present():
    # 2026-08-01 (arc4 S2 reconciliation): S2 landed two new rules
    # (`ps_structural_reject`/`ps_structural_clear`) and bumped the seed
    # 1.6.0 -> 1.7.0, 58 -> 60 rules (PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md
    # §8). Pure version/count pin update; the isolation-lane checks below
    # are unaffected (S1's own rules are untouched by S2).
    with open(SYNTH_SEED_PATH) as f:
        d = json.load(f)
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
    # MOVES.md); S1's own isolation-lane rules (ps_isolate_fallthrough)
    # are untouched by it, so the checks below are unaffected.
    # 2026-08-01 (arc6 seam D, reconciled): v1.10.0/70 -> v1.11.0/73. Added
    # the PROPERTY-REFUTATION rung (ps_property_clear / ps_property_reject_
    # gap / ps_property_reject_reopen) plus one edit to ps_accept's gate
    # (now also requires ps_property_reject == 0.0), PROGRAM_SYNTHESIS_
    # ARC6_D.md §1/§6. S1's own isolation-lane rule (ps_isolate_
    # fallthrough) and the ps_goal/ps_goal_top budget attrs asserted below
    # are untouched by it — the property rung spends no propose-lane
    # attempt of its own; pure version/count pin update.
    assert d["version"] == "1.12.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    assert len(d["rules"]) == 73
    names = {r["name"] for r in d["rules"]}
    assert "ps_isolate_fallthrough" in names
    rules = {r["name"]: r for r in d["rules"]}
    for goal_mint in ("ps_goal", "ps_goal_top"):
        eff = rules[goal_mint]["effects"]
        attrs = next(e[3] for e in eff if e[0] == "add_node" and e[2] == "Goal")
        for key, val in (("ps_propose_attempts", 0.0), ("ps_propose_budget", 3.0),
                         ("ps_enum_reserve_used", 0.0),
                         ("ps_enum_reserve_budget", 1.0)):
            assert attrs[key] == val, (goal_mint, key)
    # ps_repair_entered is stamped by ps_repair_mark (additive; the P7-B
    # repair loop's own terminal path must never be redirected here).
    repair_mark_src = json.dumps(rules["ps_repair_mark"]["effects"])
    assert "ps_repair_entered" in repair_mark_src


# ---------------------------------------------------------------------------
# 2) THE 17-ID HEADLINE.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def all_tasks():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def _run_id_full_r3(task_id, tasks_by_id):
    task = dict(tasks_by_id[task_id])
    task.pop("code", None)
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    assert spec["runnable"], "target id unexpectedly non-runnable"
    report = {}
    return bat.run_task(task, spec, report, bat.boot_full_r3, "primary")


def test_17_target_ids_headline(all_tasks):
    """HA1's own measured target list, re-run end-to-end (PRIMARY protocol,
    the FULL-R3 boot `scripts/mbpp_arc3_battery.py` uses) LIVE against the
    S1-landed seed. Reports where every id lands; asserts the headline
    claim precisely: 16/17 never show `gapped:exhausted` (any of accepted /
    accepted_holdout_fail / gapped:enumerate_failed / a retrieval-driven
    pass are legitimate — the enumerator/descent got their turn, not that
    the task is solved); the one named residual (222) is asserted to be
    the SAME residual, root-caused with its own proof facts, never a
    silent new exception."""
    tasks_by_id = {t["task_id"]: t for t in all_tasks}
    landing = {}
    for tid in TARGET_IDS:
        landing[tid] = _run_id_full_r3(tid, tasks_by_id)

    exhausted_ids = sorted(tid for tid, row in landing.items()
                           if row["outcome"] == "gapped:exhausted")
    assert set(exhausted_ids) == KNOWN_NON_STARVED_RESIDUAL_IDS, (
        "budget-isolation headline drift -- every id in TARGET_IDS except "
        "the named, root-caused residual set must escape gapped:exhausted; "
        "got exhausted=%r expected=%r (report: %s)"
        % (exhausted_ids, sorted(KNOWN_NON_STARVED_RESIDUAL_IDS),
           {tid: row["outcome"] for tid, row in landing.items()}))

    # every non-residual id: the enumerator's own reserved lane is either
    # populated (it got a real turn) or the goal resolved via an EARLIER
    # rung/retrieval before the enumerator was ever needed -- both are the
    # registered acceptance shape, never a silent park.
    for tid, row in landing.items():
        if tid in KNOWN_NON_STARVED_RESIDUAL_IDS:
            continue
        assert row["outcome"] != "gapped:exhausted", (tid, row["outcome"])
        assert row["status"] in ("accepted", "gapped"), (tid, row)

    # the residual (222): root-caused, not excused -- proof facts, not an
    # assumption. Both mark-once rungs fired for real; the enumerator's
    # own finding was evaluated (outcome 'ok', a real candidate, not
    # 'unavailable'/'failed-to-run'); the terminal exhaustion comes from
    # exhausting an ENTIRELY DIFFERENT, pre-existing, S1-unrelated lane
    # (the P7-B enum-retry round budget) — never from the propose lane
    # starving the next rung of a turn (the bug this phase fixes).
    for tid in KNOWN_NON_STARVED_RESIDUAL_IDS:
        row = landing[tid]
        assert row["outcome"] == "gapped:exhausted", (tid, row)
        assert row["rungs"]["descend"] == 1.0, (tid, "descent must have run")
        assert row["rungs"]["enumerate"] == 1.0, (tid, "enumerate must have run")
        assert row["enumerate_outcome"] == "ok", (
            tid, "the enumerator must have found and evaluated a real "
            "candidate, not been denied a turn")
        # `bat.run_task`'s row has no "budget" key (psy.read_goal's has;
        # the arc3 battery driver's own row schema is narrower) -- the
        # mint-time propose budget is a fixed, seed-pinned constant (3.0,
        # see ps_goal/ps_goal_top and gate 1 above).
        assert row["attempts"] > 3.0, (
            tid, "attempts must exceed the propose-lane budget -- proof "
            "the goal spent real cycles on descend+enumerate+retries, "
            "never merely capped by the propose lane alone")


# ---------------------------------------------------------------------------
# 3) RESERVED-BUDGET INVARIANT.
# ---------------------------------------------------------------------------
def _pool_probe(npool):
    s, ag = boot()
    trigs = [["QUUX"] + ["T%d" % i for i in range(npool - 1 - j)]
            for j in range(npool)]
    for i, t in enumerate(trigs):
        _teach_decoy(s, "decoy_%d" % i, t, {"type": "Lit", "value": 0}, ["a"],
                     branch=True)
    r = run(s, ag, "write a function quux_fn that returns the quux value "
                   "of a number",
           [({"a": 5}, 2), ({"a": 3}, 8), ({"a": 7}, 1)])
    return r


def test_reserved_budget_invariant_pool_size_does_not_reduce_enumerator_turn():
    """A PATHOLOGICAL all-wrong proposal pool (20 DESCEND_APPLICABLE decoys,
    every one of them wrong, strictly decreasing specificity) is compared
    against a 4-decoy pool of the SAME shape. Pinned numbers: BOTH pool
    sizes burn EXACTLY `ps_propose_budget` (3) real propose attempts (never
    more, however many decoys exist), decoy_3 onward is NEVER tried for
    real in EITHER pool, and BOTH pool sizes reach descent AND the
    RESERVED enumerator identically (`rungs`, `attempts`, `gap_reason`
    byte-identical) — the enumerator's own reserved lane is provably
    UNTOUCHED by proposal-pool size, the isolation claim itself."""
    r4 = _pool_probe(4)
    r20 = _pool_probe(20)
    for r, npool in ((r4, 4), (r20, 20)):
        assert r["attempts"] == 4.0, (npool, r["attempts"])
        assert r["excluded"] == ["decoy_0", "decoy_1", "decoy_2"], (npool, r)
        assert r["rungs"]["codebook"] == 1.0
        assert r["rungs"]["descend"] == 1.0
        assert r["rungs"]["enumerate"] == 1.0
        assert r["gap_reason"] == "enumerate_failed"
        assert r["status"] == "gapped"
    # byte-identical modulo nothing pool-size-dependent leaked through.
    for key in ("attempts", "budget", "excluded", "rungs", "gap_reason",
               "status", "descend_kind"):
        assert r4[key] == r20[key], key


# ---------------------------------------------------------------------------
# 4) ISOLATION IS NOT SCREENING.
# ---------------------------------------------------------------------------
def test_isolation_does_not_change_screened_goals():
    """R2.5's own screen decoy-kill fixture (pool0=4 chunk decoys >=
    budget=3, NOT_SLACK engages the screen): S1 must be a COMPLETE no-op
    here — the screen already isolates this goal from the propose lane
    entirely (every decoy dies for free), so `ps_propose_attempts` stays
    at 0, `ps_isolate_fallthrough` never fires (there is no propose-lane
    exhaustion to redirect), and the outcome is byte-identical to
    tests/test_screen_codebook_migrated.py's own frozen expectation. This
    is the concrete verification that isolation and screening have
    disjoint triggers: screening prevents an attempt from ever being
    spent; isolation only changes what happens once real attempts ARE
    spent and the propose lane closes."""
    s, ag = boot()
    trigs = [["QUUX", "ALPHA", "BETA", "GAMMA"],
             ["QUUX", "ALPHA", "BETA"],
             ["QUUX", "ALPHA"],
             ["QUUX"]]
    for i, t in enumerate(trigs):
        _teach_chunk(s, "chunk_decoy_%d" % i, t, wrong_value=0)
    r = run(s, ag, "write a function quux_fn that returns the quux alpha "
                   "beta gamma of a number", [({"a": 5}, 5)])
    assert r["screen"]["kills"] == 4.0
    assert r["isolation"]["propose_attempts"] == 0.0
    assert r["attempts"] == 0.0
    assert r["rungs"]["codebook"] is None
    assert r["rungs"]["descend"] is None
    assert r["rungs"]["enumerate"] == 1.0
    assert r["status"] == "accepted"
    assert r["gap_reason"] is None


def test_isolation_fallthrough_never_fires_once_repair_entered():
    """Structural guard, not a live-run: `ps_isolate_fallthrough`'s own
    `where` carries `Not(Eq(ps_repair_entered, 1.0))` — the SAME base
    state `ps_ce_exhausted` requires, plus that ONE extra condition and
    its own next-rung disjunct — so once `ps_repair_mark` has stamped
    `ps_repair_entered`, this rule can never fire again for that goal.
    Verified against the seed JSON directly (never re-derived by running
    the repair suite here — that suite is owned elsewhere, gated in
    tests/test_prog_repair_migrated.py, and this phase must not touch it)."""
    with open(SYNTH_SEED_PATH) as f:
        d = json.load(f)
    rules = {r["name"]: r for r in d["rules"]}
    body = json.dumps(rules["ps_isolate_fallthrough"]["where"])
    assert "ps_repair_entered" in body


# ---------------------------------------------------------------------------
# 5) NO-PARK.
# ---------------------------------------------------------------------------
def test_no_park_across_every_fixture_in_this_file():
    fixtures = []
    for npool in (4, 20):
        fixtures.append(_pool_probe(npool))
    s, ag = boot()
    trigs = [["QUUX", "ALPHA", "BETA", "GAMMA"], ["QUUX", "ALPHA", "BETA"],
             ["QUUX", "ALPHA"], ["QUUX"]]
    for i, t in enumerate(trigs):
        _teach_chunk(s, "park_chunk_%d" % i, t, wrong_value=0)
    fixtures.append(run(s, ag, "write a function quux_fn that returns the "
                              "quux alpha beta gamma of a number",
                        [({"a": 5}, 5)]))
    for r in fixtures:
        assert r["status"] in _TERMINAL_STATUSES, r


# ---------------------------------------------------------------------------
# 6) NO-PYTHON-DECISION source audit — the modified adapter surface.
# ---------------------------------------------------------------------------
_BANNED_DECISION_RE = re.compile(
    r"\bif\s+.*:\s*$|\belif\b|\bwhile\b|\.arg(?:min|max)\(", re.MULTILINE)


def _isolation_readback_source() -> str:
    src = Path(psy.__file__).read_text()
    start = src.index('"isolation": {')
    end = src.index("},", start) + 2
    return src[start:end]


def test_isolation_readback_makes_no_decision_only_reads_attrs():
    """The `isolation` sub-dict `read_goal` gained (Arc4-S1) is a STATIC
    literal of `.get()` calls on the goal's own attrs — no conditional, no
    branch, no derived verdict. The DECISION (which lane gates which rung)
    lives entirely in seeds/program_synthesis.json's rules; this span is
    pure mechanical read-back, the same discipline every other read_goal
    sub-dict (`screen`, `retrieval`, `repair`) already follows."""
    src = _isolation_readback_source()
    assert not _BANNED_DECISION_RE.search(src)
    assert "sub.add_node" not in src
    assert "sub.add_edge" not in src
    assert 'set_attr' not in src
    for key in ("ps_propose_attempts", "ps_propose_budget",
               "ps_enum_reserve_used", "ps_enum_reserve_budget",
               "ps_repair_entered"):
        assert key in src
