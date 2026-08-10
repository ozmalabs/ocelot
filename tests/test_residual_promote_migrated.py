"""A PROMOTED REFUSAL — Residual -> SelfConcern -> (human-gated) StandingConcern.

Gates VISION_RESIDUAL_PROMOTE_PREREG.md / VISION_RESIDUAL_PROMOTE_RESULTS.md.

The refusal_representable rung built HEAR + MINT (a rule mints a `Residual` from a
heard `ArgminRefusal` refusal) and named the successor: PROMOTE. This rung composes
ONE promote rule onto the EXISTING gap-awareness / SelfConcern -> StandingConcern
spine (seeds/gap_awareness.json, jabberwock_daemon.promote_self_concern), and makes
the eye-view rung's un-carved HOLE actionable.

The load-bearing instance is the PERCEPTION residual (`perception_hole_mints_residual`),
which fires on REAL hole structure, not on a rare tie. The refusal residual reuses the
existing mint. The positive control that makes the rest mean something:
`test_default_off_is_byte_identical` (a graph with no attends/has_residual edge is
unchanged) + `test_no_residual_no_selfconcern` (the loop mints nothing without a
residual) — a loop that fired on nothing, or floods, is not the loop.
"""
from __future__ import annotations
import json
import os

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from domains.engine_provenance import engine_preamble, engine_provenance, provenance_line  # noqa: E402
engine_preamble()
# Assert SOURCE identity, never a specific BUILD hash: a build hash is unique to
# one build of the source (the authoring worktree's), so pinning it — as this
# gate first did with "7041d2e6a7dd" — fails on canonical and every other valid
# rebuild of the identical source. engine_preamble() already refuses a DIVERGED /
# stale engine; this confirms the loaded engine is a build of THIS tree.
assert engine_provenance(_ROOT).get("source_match") in ("own", "shared"), provenance_line()

import substrate_rs as srs  # noqa: E402
from substrate_rs import Term  # noqa: E402
from substrate_rs.ext import run_rules  # noqa: E402

RP = json.load(open(os.path.join(_ROOT, "seeds", "residual_promote.json")))
RR = json.load(open(os.path.join(_ROOT, "seeds", "refusal_representable.json")))


def NodesOfType(t):
    return Term("NodesOfType", node_type=t)


def _active_selfconcerns(s):
    """Content of every ACTIVE (not-retired) SelfConcern — the surfacing contract
    (reflective_faculty._run_self_gaps skips status=='retired')."""
    out = []
    for x in s.evaluate(NodesOfType("SelfConcern")):
        a = s.node(x)["attrs"]
        if a.get("status") != "retired":
            out.append(a)
    return out


def _perception(uncarved, n_fields=1):
    """The eye holds a VisionField whose carve left `uncarved` HOLE cells."""
    s = srs.Substrate()
    summ = s.load_seed_manifest(RP)
    assert summ.get("rules") == 3 and not summ.get("rules_skipped"), summ
    ag = s.add_node("Agent", {})
    for _ in range(n_fields):
        f = s.add_node("VisionField", {"uncarved_count": float(uncarved)})
        s.add_edge_unchecked(ag, "attends", f)
    run_rules(s)
    return s


def _refusal(scores):
    """A refusal_probe whose refusal_cand set has no unique extremum, attended by
    the agent — the existing refusal_query_mints_residual mints the Residual."""
    s = srs.Substrate()
    s.load_seed_manifest(RR)
    s.load_seed_manifest(RP)
    ag = s.add_node("Agent", {})
    q = s.add_node("RefusalQuery", {})
    p = s.add_node("RefusalProbe", {})
    s.add_edge_unchecked(q, "refusal_probe", p)
    s.add_edge_unchecked(ag, "attends", q)
    for i, v in enumerate(scores):
        c = s.add_node("RefusalCandidate", {"score": float(v), "idx": i})
        s.add_edge_unchecked(q, "refusal_cand", c)
    run_rules(s)
    return s


TIE = [7.0] * 5


# --------------------------------------------------------------------------
def test_perception_hole_mints_residual_and_promotes():
    """C1 (load-bearing): a held field with un-carved HOLE cells mints EXACTLY
    ONE Residual{uncarved_hole} and the promote rule files EXACTLY ONE
    SelfConcern{source:residual} — in one run_rules fixpoint."""
    s = _perception(9)
    res = list(s.evaluate(NodesOfType("Residual")))
    assert len(res) == 1
    assert s.node(res[0])["attrs"]["kind"] == "uncarved_hole"
    assert s.node(res[0])["attrs"]["source_count"] == 9.0
    scs = _active_selfconcerns(s)
    assert len(scs) == 1
    assert scs[0]["source"] == "residual" and scs[0]["kind"] == "residual"
    assert scs[0]["residual_kind"] == "uncarved_hole"


def test_flat_space_constancy_mints_nothing():
    """C1: a clean/full carve (uncarved_count=0 — the FLAT space-constancy case,
    correct 'nothing here') mints NO residual and NO concern. Correct absence is
    not a gap."""
    s = _perception(0)
    assert len(s.evaluate(NodesOfType("Residual"))) == 0
    assert len(_active_selfconcerns(s)) == 0


def test_refusal_residual_promotes_distinctly():
    """C2: the existing ArgminRefusal->Residual mint reaches the SAME promote rule;
    the SelfConcern is DISTINCT from the perception one (distinct residual_kind)."""
    s = _refusal(TIE)
    res = list(s.evaluate(NodesOfType("Residual")))
    assert len(res) == 1 and s.node(res[0])["attrs"]["kind"] == "no_unique_extremum"
    scs = _active_selfconcerns(s)
    assert len(scs) == 1 and scs[0]["residual_kind"] == "no_unique_extremum"
    # a unique winner and an empty source mint neither residual nor concern
    for scores in ([7.0, 7.0, 3.0], []):
        s2 = _refusal(scores)
        assert len(s2.evaluate(NodesOfType("Residual"))) == 0
        assert len(_active_selfconcerns(s2)) == 0


def test_both_sources_reach_one_promote_rule():
    """C2: a perception hole AND a refusal, in one graph, both reach the ONE
    promote rule -> two DISTINCT active SelfConcerns."""
    s = srs.Substrate()
    s.load_seed_manifest(RR)
    s.load_seed_manifest(RP)
    ag = s.add_node("Agent", {})
    f = s.add_node("VisionField", {"uncarved_count": 9.0})
    s.add_edge_unchecked(ag, "attends", f)
    q = s.add_node("RefusalQuery", {})
    p = s.add_node("RefusalProbe", {})
    s.add_edge_unchecked(q, "refusal_probe", p)
    s.add_edge_unchecked(ag, "attends", q)
    for i in range(5):
        c = s.add_node("RefusalCandidate", {"score": 7.0, "idx": i})
        s.add_edge_unchecked(q, "refusal_cand", c)
    run_rules(s)
    kinds = sorted(a["residual_kind"] for a in _active_selfconcerns(s))
    assert kinds == ["no_unique_extremum", "uncarved_hole"]


def test_dedup_no_flood():
    """C4: N residuals of the SAME kind -> EXACTLY ONE active SelfConcern (the
    retire_duplicate_residual_concern Argmin-survivor guard); idempotent under a
    second run_rules (mint-once). CLAUDE.md: gaps must be deduped by content."""
    s = _perception(9, n_fields=4)
    assert len(s.evaluate(NodesOfType("Residual"))) == 4     # 4 distinct residuals
    assert len(_active_selfconcerns(s)) == 1                 # ONE concern
    run_rules(s)
    assert len(_active_selfconcerns(s)) == 1                 # no growth on re-run


def test_default_off_is_byte_identical():
    """C5 (§9): the seed loaded onto a graph with NO attends/has_residual edges is
    inert and round-trips byte-identically. A seed that changed disarmed behaviour
    fails here."""
    s = srs.Substrate()
    s.load_seed_manifest(RP)
    s.add_node("Message", {"text": "hello"})
    s.add_node("Goal", {"kind": "answer_topic"})
    d1 = s.graph_to_dict()
    run_rules(s)
    d2 = s.graph_to_dict()
    assert json.dumps(d1, sort_keys=True, default=str) == json.dumps(d2, sort_keys=True, default=str)


def test_no_residual_no_selfconcern():
    """Positive control (the gate bites): an agent that attends a field with NO
    hole (and no probe) mints nothing — the loop does not fire on nothing."""
    s = srs.Substrate()
    s.load_seed_manifest(RP)
    ag = s.add_node("Agent", {})
    f = s.add_node("VisionField", {"uncarved_count": 0.0})
    s.add_edge_unchecked(ag, "attends", f)
    run_rules(s)
    assert len(_active_selfconcerns(s)) == 0


@pytest.fixture(scope="module")
def booted():
    """A fully-booted agent with the residual_promote seed loaded — the real
    spine, for the two end-to-end integration tests. Skips if the full boot is
    unavailable in this env (optional deps)."""
    import sys
    sys.path.insert(0, os.path.join(_ROOT, "scripts"))
    try:
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"full boot unavailable: {e}")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)  # globs seeds/*.json -> residual_promote is auto-loaded
    return a


def test_selfconcern_reaches_the_real_promote_spine(booted):
    """C3: the minted SelfConcern is accepted by the REAL human-gated
    jabberwock_daemon.promote_self_concern -> StandingConcern{status:pending}, and
    the SelfConcern flips to 'promoted'. This is the loop closed end-to-end on the
    booted agent — the perception HOLE the eye-view rung renders becomes a standing
    concern the self-improvement pipeline runs."""
    import jabberwock_daemon as jd
    a = booted
    fld = a.s.add_node("VisionField", {"uncarved_count": 9.0})
    a.s.add_edge_unchecked(a.agent, "attends", fld)
    run_rules(a.s)
    scs = [x for x in a.s.nodes("SelfConcern")
           if a.s.node(x)["attrs"].get("source") == "residual"]
    assert len(scs) >= 1
    sc = scs[0]
    before = len(list(a.s.nodes("StandingConcern")))
    res = jd.promote_self_concern(a, str(sc.value))
    assert res.get("ok") is True and res.get("kind") == "residual"
    assert len(list(a.s.nodes("StandingConcern"))) == before + 1
    assert a.s.node(sc)["attrs"].get("status") == "promoted"
    st = a.s.node(srs.NodeID(int(res["standing_concern"])))
    assert st["attrs"]["status"] == "pending"
    assert "uncarved_hole" in st["attrs"]["about"]


def test_ground_a_residuals_content_via_the_teacher_loop(booted):
    """C6 GROUND: a knowledge residual's content ('matches nothing I hold') routed
    through the DOCUMENTED per-word teacher loop (ground_unknowns) becomes a
    grounded concept the agent can THEN recognise. The teacher decides meaning; the
    adapter is only the I/O loop (here the teacher is SUPPLIED — the real
    dictionary/wiki self-teacher needs network; the loop is the same). Honest scope:
    the PERCEPTION hole heals by RE-SAMPLING (the eye-view rung's named lever), NOT
    by dictionary grounding — GROUND is for content/knowledge residuals."""
    a = booted
    term = "zzquokkax"   # a token the agent does not hold
    assert term not in {s["form"] for s in a.taught_signs()}

    def teacher(form):
        return {"answer": f"{form} is a made-up test creature",
                "learn": [{"phrase": form, "microtheory": "animals",
                           "description": "a test creature"}]}

    grounded = a.ground_unknowns(term, teacher=teacher)
    assert term in grounded
    assert term in {s["form"] for s in a.taught_signs()}
    names = {a.s.node(n)["attrs"].get("name") for n in a.s.nodes("Concept")}
    assert f"taught_{term}" in names
