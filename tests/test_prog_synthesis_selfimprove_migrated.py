"""test_prog_synthesis_selfimprove_migrated — P6-B gates: program synthesis
wired into the agent's STANDING self-improvement machinery + the capability
self-report (PROGRAM_SYNTHESIS_PLAN.md §4-P6; PROGRAM_SYNTHESIS_PREREG.md §8;
companion doc PROGRAM_SYNTHESIS_P6_SELFIMPROVE.md).

Gates:

  1. THE LOOP (headline, the plan's RLHF analog) — a synthesis request the
     agent cannot build (rung 1 finds no shape; rung 3 SynthEnumerate
     honestly fails on the rows) →
       gap:      SelfConcern{kind:'code_write', source:'implicit',
                 status:'noted'} (the P4 ps_gap_file wiring, re-gated);
       promote:  jabberwock_daemon.promote_self_concern (the HUMAN-GATED
                 spine) → StandingConcern{status:'pending'} — the standing
                 pipeline's entry point;
       repair:   teach-by-example (code_write_growth, the CODE-4 facility)
                 supplies the missing shape;
       re-run:   the SAME request now ACCEPTS at rung 1 (exactly one
                 Program node, held-out input correct);
       close:    the agent's OWN resolve_code_write_gap rule marks the
                 concern resolved from the taught shape's taught_for
                 provenance — no Python status write.
     SCOPE HONESTY: the Experiment/adopt spine (self_optimisation) is
     demonstrated only as far as the StandingConcern hand-off; running a
     full dispatched child experiment is out of scope here — the hand-off
     IS the standing pipeline's entry (asserted: promote mints NOTHING
     beyond the pending StandingConcern).

  2. CAPABILITY SELF-REPORT — capability_report (additive P6 extension)
     buckets accepted Program{provenance:'program_synthesis'} nodes WITH
     their rung provenance, and carries code_write / prog_read gap COUNTS;
     the NL surface ("what can you do with code?") reports both through the
     EXISTING code_capabilities dispatch registration.

  3. WRITE-REQUEST PRECISION RE-RUN (the P4-carried residual, prereg §6) —
     the P0-era curriculum run flagged 4 lesson sentences as write requests
     (3 false positives, 1 genuine: results/code_curriculum/
     code_curriculum_report.json, 2026-07-13). Re-run through the CURRENT
     cue machinery (held cue Concepts + the wave-2 imperative gate, which
     ps_goal reads via the recorded ps_write_request fact): only the
     genuine exercise flags (precision 1.0 on the flagged set) and only it
     mints a synth_program Goal. A full sentence sweep of all three
     published-lesson fixtures confirms zero remaining false positives.

Run (worktree engine discipline — the P1 note):
    pytest tests/test_prog_synthesis_selfimprove_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402


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

jd = pytest.importorskip("jabberwock_daemon")

from substrate.world_adapter import WorldAdapter        # noqa: E402
from domains import code_curriculum as cc               # noqa: E402
from domains import code_write_growth as cwg            # noqa: E402
from domains import code_writing as cw                  # noqa: E402
from domains import prog_synthesis as psy               # noqa: E402
import domains.reflective_faculty as rf                 # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    # The durable teach() guard (the test_code_growth precedent): teaching in
    # these gates must never mutate the real boot seed files.
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


def fresh_agent():
    """CORE-seeded WorldAdapter + the synthesis seed (rules, starter write
    codebook, cue Concepts, bigrams) + the code_write_gap spine (the
    resolve_code_write_gap rule the close leg needs)."""
    a = WorldAdapter()
    psy.ensure_program_synthesis(a.s, a.s._inner, a.agent)
    cwg.ensure_growth_rules(a)
    return a


# The loop task: a * 10 + b is OUTSIDE the starter codebook and OUTSIDE
# SynthEnumerate's reach on these rows (no const 10; the outputs 34/72/19
# do not compose to it within the size-9 / 200k-candidate budget — probed
# deterministic: halt_reason='budget', tested=200000, found=False), yet it
# is exactly teachable by example through the CODE-4 reader. The DSL term
# (Plus(Times(a,10),b)) is integer-exact, so the taught shape verifies
# cleanly on the same rows.
REQ = ("write a function weighted_pair that returns the weighted pair code "
       "of two numbers")
ROWS = [({"a": 3, "b": 4}, 34), ({"a": 7, "b": 2}, 72), ({"a": 1, "b": 9}, 19)]
EXAMPLE = "def weighted(a, b):\n    return a * 10 + b\n"


def _prog_eval(sub, root, env):
    out = sub._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""}, {"e": env, "p": root})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


# =========================================================================== #
#  (1) THE HEADLINE — gap → human-gated promote → teach-by-example → the
#      SAME request accepts → the concern resolves by the agent's own rule.
# =========================================================================== #
def test_gap_promote_teach_accept_full_circle(tmp_path):
    a = fresh_agent()

    # LEG 1 — the request GAPS (P4 wiring, re-gated on the standing spine).
    r = psy.synthesize_from_request(a.s, a.agent, REQ, ROWS)
    assert r["status"] == "gapped"
    # enumerate honestly failed (or, on a binary without the Term, was
    # honestly unavailable) — either way the gap files.
    assert r["gap_reason"] in ("enumerate_failed", "enumerate_unavailable")
    assert r["program"] is None
    assert a.s.nodes("Program") == []
    gaps = cwg.pending_code_write_gaps(a)
    assert [g["content"] for g in gaps] == [REQ]
    assert gaps[0]["kind"] == "code_write"
    assert gaps[0]["source"] == "implicit"
    assert gaps[0]["status"] == "noted"

    # LEG 2 — HUMAN-GATED promote → StandingConcern{pending}: the standing
    # pipeline's entry point (jabberwock_daemon.promote_self_concern, the
    # exact spine test_self_concern_promote gates).
    scs = [c for c in jd.list_self_concerns(a) if c.get("kind") == "code_write"]
    assert len(scs) == 1 and scs[0]["status"] == "noted"
    res = jd.promote_self_concern(a, str(scs[0]["id"]))
    assert res["ok"], res
    standing = [n for n in a.s.nodes("StandingConcern")
                if a.s.node(n)["attrs"].get("status") == "pending"]
    assert len(standing) == 1
    sat = a.s.node(standing[0])["attrs"]
    assert sat.get("kind") == "code_write"
    assert str(sat.get("about")) == REQ
    # SCOPE HONESTY: the hand-off IS the demonstration — promotion mints
    # the pending StandingConcern and NOTHING else runs here (no Experiment
    # is dispatched; _concern_tick is the daemon's job, out of scope).
    assert a.s.nodes("Experiment") == []

    # LEG 3 — the REPAIR ACTION: teach-by-example supplies the missing shape
    # (the CODE-4 facility, unchanged — read, validate-by-running, teach).
    out = cwg.teach_write_shape_from_example(a, EXAMPLE, request_text=REQ,
                                             seeds_dir=tmp_path)
    assert out["ok"], out
    assert out["validate"]["agree"] is True
    assert out["shape"] == "taught_weighted"

    # LEG 4 — the SAME request re-runs and ACCEPTS at rung 1 (the taught
    # shape proposes; ProgEval verifies every row; exactly ONE Program).
    r2 = psy.synthesize_from_request(a.s, a.agent, REQ, ROWS)
    assert r2["status"] == "accepted"
    assert r2["construction"] == "taught_weighted"
    assert r2["rungs"]["codebook"] == 1.0
    progs = a.s.nodes("Program")
    assert len(progs) == 1
    roots = a.s.neighbours(r2["program"], "ir_subgraph")
    assert len(roots) == 1
    # held-out input — never in ROWS.
    assert _prog_eval(a.s, roots[0], {"a": 5, "b": 6}) == 56

    # LEG 5 — the gap CLOSES by the agent's OWN rule: resolve_code_write_gap
    # reads the taught shape's taught_for provenance and marks the concern
    # resolved in the run_rules fixpoint — never a Python status write.
    a.s._inner.run_rules(400000)
    concern = [c for c in jd.list_self_concerns(a)
               if c.get("kind") == "code_write"]
    assert len(concern) == 1
    assert concern[0]["status"] == "resolved"
    # the StandingConcern hand-off remains pending for the standing pipeline
    # (promotion is not undone by the capability closing — the human-gated
    # record of "this was worth improving" stands).
    assert a.s.node(standing[0])["attrs"].get("status") == "pending"


# =========================================================================== #
#  (2) CAPABILITY SELF-REPORT — synthesized bucket + gap counts, through the
#      EXISTING code_capabilities dispatch.
# =========================================================================== #
MAX_REQ = "write a function max_of_two that returns the larger of two numbers"
MAX_ROWS = [({"a": 2, "b": 9}, 9), ({"a": 7, "b": 3}, 7), ({"a": 4, "b": 4}, 4)]
GAP_REQ = ("write a function fourier_transform that returns the spectrum "
           "of a signal")


def test_capability_report_and_nl_surface_include_synthesis(tmp_path):
    a = fresh_agent()
    # one accepted synthesized program (starter-codebook rung 1)...
    r = psy.synthesize_from_request(a.s, a.agent, MAX_REQ, MAX_ROWS)
    assert r["status"] == "accepted"
    # ...and one honest gap (no shape, no examples).
    r2 = psy.synthesize_from_request(a.s, a.agent, GAP_REQ)
    assert r2["status"] == "gapped"

    rep = cc.capability_report(a)
    # the synthesized bucket: the accepted Program WITH rung provenance.
    assert len(rep["synthesized"]) == 1
    row = rep["synthesized"][0]
    assert row["name"] == "max_of_two"
    assert row["construction"] == "max_of_two"
    assert row["attempts"] == 1.0
    assert row["rungs"] == {"codebook": 1.0, "lattice": None, "enumerate": None}
    # the gap counts: exactly the filed code_write concern; no prog_read.
    assert rep["gap_counts"] == {"code_write": 1, "prog_read": 0}
    assert [g.get("content") for g in rep["filed_as_gap"]] == [GAP_REQ]

    # THE NL SURFACE — ask through the EXISTING code_capabilities dispatch
    # registration (reflective_faculty._DISPATCH, boot-time registered).
    fn = rf._DISPATCH.get("code_capabilities")
    assert fn is not None, "code_capabilities dispatch must be registered"
    outd = fn(a, None)
    note = outd["note"]
    assert "synthesized end-to-end" in note
    assert "max_of_two" in note
    assert "Open gap counts: 1 code_write, 0 prog_read." in note


def test_capability_report_prog_read_gap_counts(tmp_path):
    """A prog_read SelfConcern (the P2.5 seeds/prog_read_gap.json node
    shape) is COUNTED in gap_counts.prog_read — filed here directly in the
    seed's exact shape (the mint itself is gated in
    tests/test_prog_read_gap_migrated.py; this gate is the report's read)."""
    a = fresh_agent()
    sc = a.s.add_node("SelfConcern", {
        "kind": "prog_read", "source": "implicit", "status": "noted",
        "content": "read gap: unsupported_construct in upload.py"})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    rep = cc.capability_report(a)
    assert rep["gap_counts"]["prog_read"] == 1
    fn = rf._DISPATCH["code_capabilities"]
    note = fn(a, None)["note"]
    assert "1 prog_read" in note


# =========================================================================== #
#  (3) WRITE-REQUEST PRECISION RE-RUN — the P4-carried residual, closed.
# =========================================================================== #
# The four sentences the P0-era curriculum run flagged as write requests
# (results/code_curriculum/code_curriculum_report.json, published_lessons[*]
# .requests, 2026-07-13) — quoted VERBATIM with their lesson provenance.
GENUINE = ("As an exercise, use incremental development to write a function "
           "called hypotenuse that returns the length of the hypotenuse of a "
           "right triangle given the lengths of the two legs as arguments.")
P0_FLAGGED = [
    # lesson_return_values.txt — prose ABOUT writing functions (false pos.):
    ("In this chapter we are going to write fruitful functions instead, "
     "which hand a computed value back to whatever code called them in the "
     "first place, so that value can be stored in a variable or used as "
     "part of a bigger expression."),
    # lesson_incremental_development.txt — narration, not a directive:
    "Immediately you can write an outline of the function:",
    # lesson_incremental_development.txt — the GENUINE exercise request:
    GENUINE,
    # lesson_boolean_functions.txt — prose about rewriting (false pos.):
    ("The result of the == operator is already a boolean, so we can write "
     "the function more concisely by returning it directly instead of "
     "branching on it with an explicit if statement."),
]


def test_p0_flagged_set_reruns_at_precision_one():
    """P0-era: 4 flagged, 1 genuine → precision 0.25. Now (held cue
    Concepts + the wave-2 imperative-lead gate): only the genuine exercise
    flags → precision 1.0 on the flagged set, recall on the genuine
    request preserved. And the goal-mint wiring agrees: ps_goal (reading
    the recorded ps_write_request fact) mints a synth_program Goal for the
    genuine request ONLY."""
    a = fresh_agent()
    flagged = [s for s in P0_FLAGGED if cw.looks_like_write_request(s, a)]
    assert flagged == [GENUINE]
    for s in P0_FLAGGED:
        m = psy.ingest_spec(a.s, a.agent, s, ())
        a.s._inner.run_rules(400000)
        goals = a.s.in_neighbours(m, "about_message")
        assert len(goals) == (1 if s == GENUINE else 0), s[:60]


def test_full_lesson_sentence_sweep_flags_only_the_genuine_exercise():
    """The FULL published-lesson fixture set (all three lessons, every
    sentence outside a code-family region, the attempt_exercise_requests
    region/sentence machinery): exactly ONE sentence reads as a write
    request — the genuine hypotenuse exercise. Zero false positives
    remain anywhere in the corpus."""
    from substrate.boot_all import load_all_seeds
    from domains import reading_collapse as rc
    from domains import register_source as rs
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    fix = os.path.join(ROOT, "tests", "fixtures", "code_curriculum")
    total, flagged = 0, []
    for fn in sorted(os.listdir(fix)):
        if not fn.endswith(".txt"):
            continue
        text = open(os.path.join(fix, fn)).read()
        er = rs.embedded_regions(a, text, min_words=6)
        code_idx = {r["index"] for r in er["regions"]
                    if r.get("family") == "code"}
        for r in er["regions"]:
            if r["index"] in code_idx:
                continue
            joined = " ".join(str(r.get("text", "")).split())
            for sent in rc._split_sentences(joined):
                if not sent:
                    continue
                total += 1
                if cw.looks_like_write_request(sent, a):
                    flagged.append((fn, sent))
    assert total >= 30, "the sweep must actually cover the lesson prose"
    assert len(flagged) == 1, flagged
    assert flagged[0][0] == "lesson_incremental_development.txt"
    assert "hypotenuse" in flagged[0][1]
