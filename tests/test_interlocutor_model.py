"""test_interlocutor_model — the PERSISTENT interlocutor model as the agent's OWN COLLAPSE
FACULTY pointed at the person at TWO TIMESCALES (creator's reframe 2026-07-04). Discriminative,
donkey=0. Gates:

  1. ACCUMULATION / GROUNDED FEED — a few turns from one interlocutor (incl. "I am X" + topics)
     accumulate name + concepts on the Party, and audience_model returns grounded=True with those
     concepts (an unobserved party stays grounded=False). This is the Conceptualizer's feed.
  2. PERTURBATION — the SAME interlocutor's affect shifts -> a SMALL/fast residual -> a mood shift
     on the SAME party (identity stable).
  3. IDENTIFICATION — a register/cadence/style break WITH a DISCONTINUITY cue (a time gap) ->
     RE-ATTRIBUTION to a DIFFERENT party. Discriminative vs the perturbation case.
  4. CONTEXT-WEIGHTED — the SAME single style break decides differently WITH vs WITHOUT a time gap
     (context = the discontinuity cue; a style break alone is not enough this turn).
  5. COLLAPSE-NATIVE — the same-vs-different decision routes through run_collapse (the DomainPlug),
     reusing predict->surprise->learn; no bespoke Python residual/classifier.
  6. STABLE WITHIN A CONVERSATION (the headline / Vane repro) — a long formal intro then a short
     formal question (cadence/length varies, NO discontinuity cue) stays the SAME party. Identity
     is the SLOW timescale: a single-turn style blip is a perturbation, not a new person.
  7. SUSTAINED MISMATCH — a coherent style break that PERSISTS across multiple turns (no context
     cue) eventually re-attributes (the slow signal), while the FIRST drift turn does not.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter                # noqa: E402
from substrate.boot_all import load_all_seeds                   # noqa: E402
import domains.interlocutor_model as im                         # noqa: E402
import domains.audience_driven_production as adp                # noqa: E402


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


# A stable formal/ornate persona (Cornelius) — several turns of accumulation.
CORNELIUS = [
    "Good evening. I am Cornelius Vane, and I should like to discuss ethics.",
    "Indeed, virtue could be understood as the disposition toward excellence, kindly weighed.",
    "Pardon me, but morality requires that we examine consequences carefully.",
]


# ===========================================================================
# 1. ACCUMULATION / GROUNDED FEED
# ===========================================================================
def test_accumulation_grounds_the_audience():
    a = _agent()
    for t in CORNELIUS:
        im.observe_turn(a, t)
    snap = im.snapshot(a)
    # the Party accumulated the self-identified NAME + prior concepts (common ground).
    assert snap["id"] == "Cornelius Vane"
    assert snap["observed"] is True
    assert {"ethics", "virtue", "morality"} <= set(snap["known_concepts"])
    # audience_model reads it as GROUNDED with those concepts — the Conceptualizer's feed.
    bundle = adp.audience_model(a, snap)
    assert bundle["grounded"] is True
    assert {"ethics", "virtue", "morality"} <= set(bundle["known"])

    # CONTRAST: an interlocutor never observed stays grounded=False (no feed).
    un = adp.audience_model(a, {"id": "stranger", "observed": False, "known_concepts": []})
    assert un["grounded"] is False and not un["known"]
    assert a._donkey["n"] == 0


# ===========================================================================
# 2. PERTURBATION — same person, mood shift, SMALL residual
# ===========================================================================
def test_perturbation_is_a_mood_shift_on_the_same_party():
    a = _agent()
    for t in CORNELIUS:
        im.observe_turn(a, t)
    party_before = im._active_party(a)

    # same speaker, affect flips agitated; register/cadence/style essentially stable.
    r = im.observe_turn(
        a, "This is outrageous and unacceptable; I am frankly furious about this disgraceful mess.")
    print("PERTURBATION:", r["decision"], "mood=", r["mood_shift"],
          "slow_residual=", r["slow_residual"])

    assert r["decision"] == "perturbation"
    assert r["mood_shift"] == "agitated"
    assert r["party"] == party_before, "SAME party — identity stable under a mood shift"
    assert a.s.node(r["party"])["attrs"].get("mood") == "agitated"
    assert a._donkey["n"] == 0


# ===========================================================================
# 3. IDENTIFICATION — different person, LARGE structured residual + context
# ===========================================================================
def test_identification_reattributes_to_a_different_party():
    a = _agent()
    for t in CORNELIUS:
        im.observe_turn(a, t)
    party_before = im._active_party(a)
    n_parties = len(im._parties(a))

    # a very different register/cadence/style + a time gap in context -> re-attribution.
    r = im.observe_turn(a, "hey yeah sup lol ok cool", context={"time_gap": True})
    print("IDENTIFICATION:", r["decision"], "new party=", r["party_name"],
          "slow_residual=", r["slow_residual"])

    assert r["decision"] == "identity"
    assert r["party"] != party_before, "DIFFERENT party — re-attributed"
    assert len(im._parties(a)) == n_parties + 1, "a new party was minted (grow Γ)"
    assert r["structured"] is True and len(r["style_gaps"]) >= 1
    assert a._donkey["n"] == 0


# ===========================================================================
# 4. CONTEXT-WEIGHTED — same style break, context decides
# ===========================================================================
def _build_persona(a):
    for t in ["Please kindly consider, indeed, the disposition toward virtue.",
              "Certainly, morality could, perhaps, be examined carefully.",
              "Pardon, would you consider consequences, thoughtfully weighed?"]:
        im.observe_turn(a, t)


def test_context_weights_the_identity_decision():
    # SAME single style break; only the context (a time gap) differs.
    break_text = "Please could you kindly clarify that point for me now"

    a_no = _agent(); _build_persona(a_no)
    r_no = a_no and im.observe_turn(a_no, break_text)  # no time gap

    a_gap = _agent(); _build_persona(a_gap)
    r_gap = im.observe_turn(a_gap, break_text, context={"time_gap": True})

    print("NO-GAP :", r_no["decision"], "style_gaps=", r_no["style_gaps"],
          "ctx=", r_no["context_gaps"])
    print("W/GAP  :", r_gap["decision"], "style_gaps=", r_gap["style_gaps"],
          "ctx=", r_gap["context_gaps"])

    # the SAME style residual — the ONLY difference is the context gap.
    assert r_no["style_gaps"] == r_gap["style_gaps"]
    assert not r_no["context_gaps"] and r_gap["context_gaps"]
    # ...and it decides differently: context tips a sub-coherent style break into re-attribution.
    assert r_no["decision"] != "identity"
    assert r_gap["decision"] == "identity"
    assert a_no._donkey["n"] == 0 and a_gap._donkey["n"] == 0


# ===========================================================================
# 6. STABLE WITHIN A CONVERSATION — the headline (Cornelius Vane repro)
# ===========================================================================
def test_stable_within_a_conversation_no_reattribution():
    """The Vane repro: a long formal SELF-INTRODUCTION (turn 1) then a short formal QUESTION
    (turn 2). Cadence/length vary but there is NO discontinuity cue -> the SAME established party,
    NOT an identity switch. Before this fix (_COHERENCE=2 on a single turn's style gaps) turn 2's
    register+cadence gaps tripped a re-attribution to a fresh speaker; now identity is the SLOW
    timescale and a single-turn style blip is a perturbation, so the party is stable."""
    a = _agent()
    r1 = im.observe_turn(
        a, "Good evening. I am Cornelius Vane, and I should like to discuss the finer "
           "points of ethics with you at some length this evening.")
    party_intro = r1["party"]
    assert a.s.node(party_intro)["attrs"].get("name") == "Cornelius Vane"

    # a SHORT, still-formal question — cadence collapses long -> short (a style gap), no context.
    r2 = im.observe_turn(a, "How are you organised?")
    print("STABLE:", r2["decision"], "style_gaps=", r2["style_gaps"],
          "ctx=", r2["context_gaps"], "streak=", r2["style_mismatch_streak"])

    assert r2["decision"] != "identity", "a single-turn style/cadence blip is NOT an identity switch"
    assert r2["party"] == party_intro, "SAME established party — inertia, not re-attribution"
    assert len(im._parties(a)) == 1, "no fresh speaker minted on a within-conversation variation"
    assert not r2["context_gaps"], "no discontinuity cue was present"
    assert a._donkey["n"] == 0


# ===========================================================================
# 7. SUSTAINED MISMATCH — persistence across turns is the slow identity signal
# ===========================================================================
def test_sustained_mismatch_eventually_reattributes():
    """A style break with NO discontinuity cue that PERSISTS across several turns is the SLOW
    signal -> eventually re-attributes. The FIRST drift turn is a perturbation (same party); only
    after the coherent break sustains does identity switch. Discriminative vs both the stable case
    (a single blip never switches) and the identification case (a context cue switches at once)."""
    a = _agent()
    for t in CORNELIUS:                       # establish the formal/ornate Cornelius persona
        im.observe_turn(a, t)
    party_before = im._active_party(a)
    n_parties = len(im._parties(a))

    # a SUSTAINED casual drift, no context cue on any turn.
    drift = ["yeah nah dunno lol", "sup gonna grab food", "ok cool whatever man"]
    decisions = []
    for t in drift:
        r = im.observe_turn(a, t)
        decisions.append(r["decision"])
        print("DRIFT:", t, "->", r["decision"], "break_size=", r["break_size"],
              "streak=", r["style_mismatch_streak"])

    # the FIRST coherent-break turn does NOT re-attribute (still the same person, so far).
    assert decisions[0] != "identity", "a single sustained-break turn is not yet an identity switch"
    # ...but once it PERSISTS it re-attributes to a new party (the slow signal fires).
    assert "identity" in decisions, "a sustained multi-turn style break eventually re-attributes"
    assert im._active_party(a) != party_before, "re-attributed to a DIFFERENT party"
    assert len(im._parties(a)) == n_parties + 1, "exactly one new party minted (grow Γ)"
    assert a._donkey["n"] == 0


# ===========================================================================
# 5. COLLAPSE-NATIVE — the decision IS the collapse residual (run_collapse plug)
# ===========================================================================
def test_decision_routes_through_the_collapse_engine():
    # the plug's residual is produced by scripts/collapse_engine.run_collapse (predict/surprise),
    # and the learn (consolidate / re-attribute) reads it — the move_space precedent exactly.
    import domains.interlocutor_collapse_plug as plug
    import collapse_engine as ce
    assert plug.run_collapse is ce.run_collapse, "residual comes from the agent's collapse loop"

    # a matched turn collapses (no residual); a value the model never saw is a gap (surprise).
    model = {"register": {"formal": 3}, "cadence": {"long": 3}}
    assert plug.collapse_residual(model, {"register": "formal", "cadence": "long"}) == []
    flipped = plug.collapse_residual(model, {"register": "casual", "cadence": "long"})
    assert flipped == [("register", "casual")], "the residual is the un-collapsible feature"

    # SOURCE AUDIT: interlocutor_model has no bespoke same-vs-different classifier — the decision
    # is read from the collapse residual (collapse_residual) at two timescales.
    src = open(os.path.join(ROOT, "domains", "interlocutor_model.py")).read()
    assert "collapse_residual(" in src
    assert "import" in src and "collapse_residual" in src
    # no hand-rolled softmax / fit / gradient — neither module imports the numeric machinery a
    # bespoke residual engine would need (the arithmetic lives in run_collapse, in Rust/graph).
    for fn in ("interlocutor_model.py", "interlocutor_collapse_plug.py"):
        code = [ln for ln in open(os.path.join(ROOT, "domains", fn)).read().splitlines()
                if not ln.lstrip().startswith("#")]
        code = "\n".join(code)
        for bad in ("import numpy", "import math", "math.exp(", ".fit(", ".backward("):
            assert bad not in code, f"{fn} smells like a parallel engine: {bad}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
