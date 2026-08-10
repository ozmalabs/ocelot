"""test_self_capability_collapse — the agent's collapse loop turned INWARD on its
OWN COMPETENCE.  Gates that self-gap perception is:

  * REAL: a challenge battery of things the agent is EXPECTED to handle -> the
    ones it FAILS mint a CapabilityGap localized to the failing faculty; the ones
    it HANDLES mint none.  Gap iff observed-failure-under-predicted-competence.
  * DISCRIMINATIVE: same harness, a substantive outcome -> NO gap (residual zero),
    a failure outcome -> a gap, by ACTUAL competence not a Python flag.
  * A GROUNDABLE CONCERN: the minted gap is consumable by induce_concern.
  * COLLAPSE-NATIVE: the gap decision routes through run_collapse (the plug), not a
    bespoke weakness classifier (source + spy audit).
  * NO REGRESSION: converse still works after running the battery (scratch agent).

donkey=0: the outcome is the agent's OWN faculties' behavior; the gap is the
collapse residual.  No self-teacher (LLM) call.
"""
from __future__ import annotations

import inspect

import pytest

from domains import self_capability_collapse as scc


# ==========================================================================
# UNIT — the plug + mechanical outcome classifier (no agent needed).
# ==========================================================================

def test_observe_outcome_surfaces():
    assert scc.observe_outcome(None) == "silence"
    assert scc.observe_outcome("") == "silence"
    assert scc.observe_outcome("   ") == "silence"
    assert scc.observe_outcome("noted") == "bare_ack"
    assert scc.observe_outcome("Noted.") == "bare_ack"
    assert scc.observe_outcome("understood") == "bare_ack"
    assert scc.observe_outcome("what do you mean?") == "clarify_repair"
    # a substantive prose reply is handled, even though it is long.
    assert scc.observe_outcome("I am organised into microtheories and rules.") == "substantive"
    # a greeting round-trip is substantive (not a bare-ack, no trailing '?').
    assert scc.observe_outcome("hello") == "substantive"


def test_discriminative_residual_pure():
    # SAME plug, opposite outcome by ACTUAL competence:
    competence = {"f": {"substantive": 1}}
    # solved -> the observed outcome matches the prediction -> NO gap (residual zero).
    assert scc.collapse_residual(competence, {"f": "substantive"}) == []
    # failed -> the observed failure has zero predicted mass -> a gap.
    assert scc.collapse_residual(competence, {"f": "bare_ack"}) == [("f", "bare_ack")]
    assert scc.collapse_residual(competence, {"f": "silence"}) == [("f", "silence")]


def test_gap_only_under_predicted_competence():
    # a faculty the agent does NOT claim (absent from competence) -> no prediction,
    # no surprise, even on a failure surface.  Gap requires predicted competence.
    assert scc.collapse_residual({}, {"unclaimed": "bare_ack"}) == []
    # add the claim -> the SAME failure now surprises -> a gap.
    assert scc.collapse_residual({"unclaimed": {"substantive": 1}},
                                 {"unclaimed": "bare_ack"}) == [("unclaimed", "bare_ack")]


def test_mixed_battery_residual_localizes():
    competence = {"a": {"substantive": 1}, "b": {"substantive": 1}, "c": {"substantive": 1}}
    obs = {"a": "substantive", "b": "bare_ack", "c": "substantive"}
    res = scc.collapse_residual(competence, obs)
    assert res == [("b", "bare_ack")]        # localized to exactly the failing faculty


# ==========================================================================
# COLLAPSE-NATIVE AUDIT — the gap decision is run_collapse's residual.
# ==========================================================================

def test_collapse_native_same_run_collapse():
    from collapse_engine import run_collapse as engine_run_collapse
    assert scc.run_collapse is engine_run_collapse   # the agent's domain-general loop, unmodified


def test_collapse_native_spy(monkeypatch):
    # PROVE the residual comes from run_collapse's on_gap, not a python classifier:
    # if run_collapse never calls on_gap (a no-op stand-in), the residual is empty
    # even for a genuine failure — there is no bespoke fallback deciding a gap.
    calls = {"n": 0}
    real = scc.run_collapse

    def spy(plug, seq_lp, *a, **k):
        calls["n"] += 1
        return real(plug, seq_lp, *a, **k)
    monkeypatch.setattr(scc, "run_collapse", spy)
    res = scc.collapse_residual({"f": {"substantive": 1}}, {"f": "silence"})
    assert calls["n"] == 1 and res == [("f", "silence")]

    # a no-op run_collapse (never fires on_gap) -> NO gap: nothing else decides it.
    monkeypatch.setattr(scc, "run_collapse", lambda plug, seq_lp, *a, **k: None)
    assert scc.collapse_residual({"f": {"substantive": 1}}, {"f": "silence"}) == []


def test_no_bespoke_weakness_classifier_source_audit():
    src = inspect.getsource(scc)
    # the gap must not be decided by a hand-written comparison in the residual path.
    assert "collapse_residual" in src and "run_collapse(plug, seq_lp)" in src
    # on_gap only RECORDS the residual run_collapse handed it (append), never decides.
    on_gap_src = src[src.index("def on_gap"):src.index("plug = DomainPlug")]
    assert "residual.append" in on_gap_src
    # on_gap never DECIDES weakness: it does not compare the outcome against the
    # substantive/failure classes — the gap was already decided by run_collapse.
    assert "SUBSTANTIVE" not in on_gap_src and "FAILURE_CLASSES" not in on_gap_src
    assert '"substantive"' not in on_gap_src


# ==========================================================================
# BOOTED AGENT — the full loop on the real faculties (donkey=0).
# ==========================================================================

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture(scope="module")
def agent():
    return _agent()


def test_battery_loads():
    battery = scc.load_battery()
    facs = {c["faculty"] for c in battery}
    assert "explain_planning_failure" in facs        # the deliberately-weak faculty
    assert any(c.get("weak_stub") for c in battery)
    assert len(battery) >= 4


def test_perceives_a_real_gap_and_successes_mint_none(agent):
    out = scc.perceive_capability_gaps(agent)
    obs = out["observations"]
    # the real conversation challenges are HANDLED -> substantive -> no gap.
    assert obs["answer_question"] == "substantive"
    assert obs["act_on_instruction"] == "substantive"
    assert obs["greeting"] == "substantive"
    # the deliberately-weak faculty FAILS -> a residual localized to it.
    assert obs["explain_planning_failure"] in scc.FAILURE_CLASSES
    assert ("explain_planning_failure", obs["explain_planning_failure"]) in out["residual"]
    # exactly the failing faculty produced a gap; the successes produced none.
    failing = {f for f, _ in out["residual"]}
    assert failing == {"explain_planning_failure"}
    # the gap was minted as a CapabilityGap node localized to the faculty.
    gaps = [agent.s.node(g)["attrs"] for g in agent.s.nodes("CapabilityGap")]
    weak = [g for g in gaps if g.get("faculty") == "explain_planning_failure"]
    assert weak and weak[0]["failure_class"] in scc.FAILURE_CLASSES
    assert weak[0].get("status") == "perceived"
    # discriminative: no CapabilityGap for a handled faculty.
    assert not [g for g in gaps if g.get("faculty") in
                ("answer_question", "act_on_instruction", "greeting")]
    assert agent._donkey["n"] == 0                    # donkey=0


def test_gap_is_idempotent(agent):
    before = len(agent.s.nodes("CapabilityGap"))
    scc.perceive_capability_gaps(agent)               # re-run: same gap, no duplicate
    assert len(agent.s.nodes("CapabilityGap")) == before


def test_gap_is_a_groundable_concern(agent):
    # the minted CapabilityGap is consumable by the composer's concern machinery.
    gap = next(g for g in agent.s.nodes("CapabilityGap")
               if agent.s.node(g)["attrs"].get("faculty") == "explain_planning_failure")
    verdict = scc.ground_gap_as_concern(agent, gap)
    # induce_concern returns a well-formed verdict (recognized OR minted a concern).
    assert isinstance(verdict, dict)
    assert "note" in verdict
    assert ("minted" in verdict) or ("covered_by" in verdict)


def test_discriminative_on_agent(agent):
    # SAME harness, a genuinely-substantive faculty -> NO gap; the weak stub -> gap.
    strong = [{"id": "q", "faculty": "answer_question",
               "text": "How are you organised?", "speech_act": "question"}]
    weak = [{"id": "w", "faculty": "flaky_faculty",
             "text": "irrelevant", "weak_stub": "bare_ack"}]
    r_strong = scc.perceive_capability_gaps(agent, battery=strong, mint=False)
    r_weak = scc.perceive_capability_gaps(agent, battery=weak, mint=False)
    assert r_strong["residual"] == []                 # substantive -> no gap
    assert r_weak["residual"] == [("flaky_faculty", "bare_ack")]   # failure -> gap


def test_no_regression_converse_still_works(agent):
    # running the battery didn't corrupt the conversation faculties.
    assert agent.converse("hello", "greeting") == "hello"
    ans = agent.converse("How are you organised?", "question")
    assert isinstance(ans, str) and "organis" in ans.lower()
    assert agent._donkey["n"] == 0
