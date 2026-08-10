"""RESIDUAL-CLOSURE wave gate: the knob_edit variation family — the agent
closes a HELD-THRESHOLD residual through its OWN pipeline.

The missing variation capability this wave adds: many held beliefs (e.g.
ApertureBudget's per-register reading thresholds, seeds/reading_aperture.json)
are plain NODE ATTRS with no owning acting rule, so neither threshold_shift
(rule-literal shifts via RuleSummary provenance) nor any conversation family
could ever vary them. `knob_edit` (seeds/variation_ops.json v1.1.0) is the
held-node-attr twin: the SeedDelta gains a `set_node_attrs` channel
({type, key_attr, key_value, attrs}, applied by BOTH child runners via
scripts/arc_child_run.apply_node_attr_delta), `_compose_knob_variant`
(domains/reflective_faculty.py — a legal builder: assembles the delta from
graph data; WHICH knob is a token-overlap Argmax over the held knob rows'
own attr keys, honest abstain at zero overlap) builds it, adoption applies
the SAME attr change to the PARENT's node with the old value captured on the
Adoption record, and revert restores it. The verdict is
seeds/self_optimisation.json v1.1.0's judge_knob_experiment_outcome over the
child's CONTROLLED double-pass replay (control pass at the parent's held
value, then the knob, then the variant pass — fewer reform marks supports,
tied is inconclusive, more or any regression refutes; the run-15
protected-control lesson applied to self-experiments) — the adoption-safety
regression veto applies unchanged (it reads Experiment.regressions,
family-agnostic).

Gated here:
  * delta mechanics: set_node_attrs applies on a (child-shaped) agent;
    typed add_concepts carries a non-Concept node type (R4's enabler);
  * adoption mechanics: a supported knob experiment folds the attr change
    into the parent + Adoption carries old value; revert restores it;
    idempotent re-revert is a no-op;
  * the veto: a knob experiment with regressions is adopt_denied by the
    agent's own adopt_denied_on_regression rule, parent knob unchanged;
  * the pick: the held variation_pick Program chooses knob_edit exactly
    when 'bound' grounds (and never hijacks cue_set_edit's instruction
    family);
  * the compose: _compose_knob_variant picks the content-named knob and
    honestly abstains when nothing matches;
  * the R1 vertical slice END-TO-END (real subprocess): explicit NL report
    -> gap files -> NL promote -> ground (knob_edit delta) -> dispatch ->
    child replays with the shifted knob under the parent's shadow_read ->
    the agent's own judges verdict it -> supported+zero-regression adopts
    (parent knob moves, revertible) OR refuted/inconclusive leaves the
    parent byte-unchanged — both terminal states asserted honestly;
  * the audit runner's AST source discipline (scripts/residual_closure_run.py
    drives ONLY sanctioned surfaces).
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")

import domains.reflective_faculty as rf                                  # noqa: E402
from domains.experiment_dispatch import (mint_experiment,                # noqa: E402
                                         scan_and_dispatch, _INFLIGHT)
from arc_child_run import apply_node_attr_delta, apply_concept_delta     # noqa: E402

_GUARDED_SEEDS = (
    os.path.join(ROOT, "seeds", "experiment_conclusions.json"),
)


@pytest.fixture(autouse=True)
def _guard_seed_files():
    before = {}
    for p in _GUARDED_SEEDS:
        before[p] = open(p).read() if os.path.exists(p) else None
    try:
        yield
    finally:
        for p, content in before.items():
            if content is not None:
                with open(p, "w") as f:
                    f.write(content)
            elif os.path.exists(p):
                os.unlink(p)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def light_agent():
    return WorldAdapter(seeds=())


def _conversational_budget(a):
    for n in a.s.nodes("ApertureBudget"):
        if a.s.node(n)["attrs"].get("register") == "conversational":
            return n
    return None


# --- delta mechanics -----------------------------------------------------------

def test_set_node_attrs_applies_and_typed_add_concepts(light_agent):
    a = light_agent
    a.s.add_node("ApertureBudget", {"register": "conversational",
                                    "reform_swallowed_threshold": 0.5})
    delta = {"set_node_attrs": [{"type": "ApertureBudget", "key_attr": "register",
                                 "key_value": "conversational",
                                 "attrs": {"reform_swallowed_threshold": 0.6}}]}
    changed = apply_node_attr_delta(a, delta)
    assert changed == [("ApertureBudget", "conversational", "reform_swallowed_threshold")]
    n = _conversational_budget(a)
    assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == 0.6

    # a delta naming a node that does not exist is an honest no-op
    changed2 = apply_node_attr_delta(a, {"set_node_attrs": [
        {"type": "ApertureBudget", "key_attr": "register", "key_value": "nonexistent",
         "attrs": {"reform_swallowed_threshold": 9.9}}]})
    assert changed2 == []

    # typed add_concepts (R4's enabler): a non-Concept node rides the channel
    added = apply_concept_delta(a, {"add_concepts": [
        {"type": "InterlocutorShape", "attrs": {"name": "probe_shape", "n_obs": 0.0}}]})
    assert added == ["probe_shape"]
    shapes = [n for n in a.s.nodes("InterlocutorShape")
              if a.s.node(n)["attrs"].get("name") == "probe_shape"]
    assert len(shapes) == 1


# --- the pick + the compose ------------------------------------------------------

_CONVO = ["test", "replay", "send", "judge", "adopt"]


def test_variation_pick_chooses_knob_edit_exactly_when_bound_grounds(light_agent):
    a = light_agent
    a.s.add_node("StandingConcern", {"name": "k_rep", "kind": "reported"})
    assert rf._pick_variation_op(a, _CONVO + ["bound"], "k_rep") == "knob_edit"
    assert rf._pick_variation_op(a, _CONVO, "k_rep") == "reply_ablation"
    # never hijacks the instruction family's cue_set_edit (priority 10 < 15)
    a.s.add_node("StandingConcern", {"name": "k_ins", "kind": "instruction"})
    assert rf._pick_variation_op(a, _CONVO + ["bound"], "k_ins") == "cue_set_edit"


def test_compose_knob_variant_picks_named_knob_and_abstains(agent):
    a = agent
    sc = a.s.add_node("SelfConcern", {
        "status": "noted", "source": "explicit_report", "kind": "reported",
        "content": "your reading reform swallowed threshold is wrong"})
    st = a.s.add_node("StandingConcern", {"name": "k_knob", "kind": "reported"})
    a.inner.add_edge_unchecked(sc, "promoted_to", st)
    rep = rf._compose_knob_variant(a, ["k_knob"], "t1")
    assert rep["built"] is True
    assert rep["attr"] == "reform_swallowed_threshold"
    assert rep["node_type"] == "ApertureBudget" and rep["key_value"] == "conversational"
    assert rep["new_value"] == pytest.approx(rep["old_value"] + 0.1)
    item = rep["set_node_attrs_item"]
    assert item["attrs"] == {"reform_swallowed_threshold": rep["new_value"]}

    # honest abstain: content naming NO held knob words
    sc2 = a.s.add_node("SelfConcern", {"status": "noted", "kind": "reported",
                                       "content": "you always mumble incoherently"})
    st2 = a.s.add_node("StandingConcern", {"name": "k_none", "kind": "reported"})
    a.inner.add_edge_unchecked(sc2, "promoted_to", st2)
    rep2 = rf._compose_knob_variant(a, ["k_none"], "t2")
    assert rep2["built"] is False and "abstain" in rep2["wall"]


# --- adoption + revert + veto ---------------------------------------------------

def _mint_knob_experiment(a, *, regressions=0, outcome="supported"):
    """Hand-mint a judged knob Experiment (the mint/judge path has its own
    gates below and in the vertical slice; this exercises the ADOPTION
    mechanics in isolation, exactly like test_experiment_dispatch does for
    dispatch)."""
    exp = mint_experiment(a, "knob probe", "conversation",
                          set_node_attrs=[{"type": "ApertureBudget",
                                           "key_attr": "register",
                                           "key_value": "conversational",
                                           "attrs": {"reform_swallowed_threshold": 0.6}}])
    delta = next(d for d in a.inner.neighbours(exp, "has_delta"))
    a.inner.set_attr(delta, "knob_edit", 1.0)
    a.inner.set_attr(delta, "knob_node_type", "ApertureBudget")
    a.inner.set_attr(delta, "knob_key_attr", "register")
    a.inner.set_attr(delta, "knob_key_value", "conversational")
    a.inner.set_attr(delta, "knob_attr", "reform_swallowed_threshold")
    a.inner.set_attr(delta, "knob_old_value", 0.5)
    a.inner.set_attr(delta, "knob_new_value", 0.6)
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", outcome)
    a.inner.set_attr(exp, "regressions", regressions)
    a.inner.set_attr(exp, "adopt_ready", True)
    return exp


def test_knob_adoption_applies_to_parent_and_revert_restores(agent):
    a = agent
    n = _conversational_budget(a)
    assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == 0.5
    exp = _mint_knob_experiment(a)
    records = rf.perform_adoptions(a)
    knob_recs = [r for r in records if r.get("knob_attr") == "reform_swallowed_threshold"]
    assert len(knob_recs) == 1
    assert a.s.node(exp)["attrs"].get("adopted") is True
    assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == 0.6

    adoption = knob_recs[0]["adoption"]
    at = a.s.node(adoption)["attrs"]
    assert at["knob_old_value"] == 0.5 and at["knob_new_value"] == 0.6

    r = rf.revert_adoption(a, adoption)
    assert r["reverted"] is True and r["restored_knob"] == "reform_swallowed_threshold"
    assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == 0.5
    assert a.s.node(exp)["attrs"].get("adopted") is False
    # idempotent
    r2 = rf.revert_adoption(a, adoption)
    assert r2["reverted"] is False and r2["reason"] == "already reverted"


def test_knob_adoption_vetoed_on_regressions(agent):
    a = agent
    n = _conversational_budget(a)
    before = a.s.node(n)["attrs"]["reform_swallowed_threshold"]
    exp = _mint_knob_experiment(a, regressions=2)
    a.tick()      # the agent's own adopt_denied_on_regression rule (adoption_safety)
    at = a.s.node(exp)["attrs"]
    assert at.get("adopt_denied") is True, at
    assert at.get("adopt_denied_reason")
    records = rf.perform_adoptions(a)
    assert not any(r.get("knob_attr") for r in records)
    assert a.s.node(exp)["attrs"].get("adopted") is not True
    assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == before, (
        "a vetoed knob experiment must leave the parent's held belief unchanged")


# --- the R1 vertical slice (real subprocess) -------------------------------------

def _dispatch_until(a, runs_dir, exp, timeout_s=420.0):
    _INFLIGHT.clear()
    t0 = time.time()
    scan_and_dispatch(a, str(runs_dir))
    while time.time() - t0 < timeout_s:
        status = a.s.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            return status
        time.sleep(1.0)
        scan_and_dispatch(a, str(runs_dir))
    return a.s.node(exp)["attrs"].get("status")


def test_r1_vertical_slice_end_to_end(tmp_path):
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.shadow_read = True
    a.deep_ingest = True

    # a small replay corpus incl. the motivating PP sentence
    a.converse("Hello.", speech_act="greeting")
    a.converse("Miners extract ore from the mountain.", speech_act="statement")
    a.converse("Farmers haul grain from the valley.", speech_act="statement")
    assert a.s.node(a.agent)["attrs"].get("shadow_latency_recent_avg") is not None

    # FILE: the interlocutor reports the deficiency (gap_awareness surface)
    a.converse("Your reading reform swallowed threshold is wrong; it reforms "
               "simple sentences too eagerly.", speech_act="statement")
    mine = [n for n in a.s.nodes("SelfConcern")
            if "swallowed" in str(a.s.node(n)["attrs"].get("content") or "")]
    assert len(mine) == 1, "the explicit report files exactly one SelfConcern"
    assert a.s.node(mine[0])["attrs"]["kind"] == "reported"

    # PROMOTE via NL -> _steer_tick (the daemon's own hook)
    steer = a.converse("Work on the swallowed threshold gap.", speech_act="request")
    assert (steer or "").lower().startswith("promoting:"), steer
    promoted = jd._steer_tick(a)
    assert len(promoted) == 1 and promoted[0]["ok"]
    assert promoted[0]["pipeline"] == "experiment", (
        "a reported threshold gap takes the conversation experiment bundle")

    # GROUND: the pipeline picks knob_edit and mints the Experiment
    jd._concern_tick(a)
    convo = [n for n in a.s.nodes("Experiment")
             if a.s.node(n)["attrs"].get("game") == "conversation"]
    assert len(convo) == 1, "exactly one conversation experiment expected"
    exp = convo[0]
    da = {}
    for d in a.inner.neighbours(exp, "has_delta"):
        da = dict(a.s.node(d)["attrs"])
    assert da.get("knob_edit") == 1.0, da
    assert da.get("knob_attr") == "reform_swallowed_threshold"
    items = json.loads(da.get("set_node_attrs") or "[]")
    assert len(items) == 1 and items[0]["key_value"] == "conversational"
    assert items[0]["attrs"]["reform_swallowed_threshold"] == pytest.approx(0.6)

    # (memory discipline: the pre-existing standing metascience concern mints
    # ARC experiments on a fresh boot — cancel them so this slice spawns ONE
    # child; cancel_experiment is the host/human console surface.)
    from domains.experiment_dispatch import cancel_experiment
    for other in a.s.nodes("Experiment"):
        if a.s.node(other)["attrs"].get("game") != "conversation" \
                and a.s.node(other)["attrs"].get("status") == "requested":
            cancel_experiment(a, str(int(other.value)))

    # DISPATCH: real subprocess; the child runs the CONTROLLED double-pass
    # under the parent's shadow_read (parent-fidelity flag).
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, a.s.node(exp)["attrs"].get("error"))
    child = json.load(open(os.path.join(a.s.node(exp)["attrs"]["run_dir"], "result.json")))
    assert child["status"] == "done"
    assert "control_reforms" in child and "variant_reforms" in child, (
        "a knob delta must run the controlled double-pass and report both counts", child)
    # the reporting turn + steering turn are excluded; 3 behaviour probes remain
    assert child["frames"] == 3, child

    # JUDGE: the agent's own rules (generic + knob judge) verdict it
    a.tick()
    at = dict(a.s.node(exp)["attrs"])
    assert at.get("knob_judged") is True, at
    assert at.get("outcome") in ("supported", "refuted", "inconclusive")
    if int(at.get("regressions") or 0) > 0:
        assert at.get("outcome") == "refuted", "regressions always refute a knob trial"
    elif int(child["variant_reforms"]) < int(child["control_reforms"]):
        assert at.get("outcome") == "supported", (
            "fewer reforms with zero regressions must support", child, at)
    elif int(child["variant_reforms"]) == int(child["control_reforms"]):
        assert at.get("outcome") == "inconclusive", (child, at)

    # CLOSE: adoption folds a supported winner into the PARENT (revertible),
    # a refuted/inconclusive one leaves it byte-unchanged. Both honest ends.
    n = _conversational_budget(a)
    rf.close_experiment_loop(a)
    at = dict(a.s.node(exp)["attrs"])
    knob_now = a.s.node(n)["attrs"]["reform_swallowed_threshold"]
    if at.get("outcome") == "supported" and not at.get("adopt_denied"):
        assert at.get("adopted") is True
        assert knob_now == pytest.approx(0.6), "the parent's held belief moved"
        adoptions = [x for x in a.s.nodes("Adoption")
                     if a.s.node(x)["attrs"].get("knob_attr") == "reform_swallowed_threshold"]
        assert len(adoptions) == 1
        aat = a.s.node(adoptions[0])["attrs"]
        assert aat["knob_old_value"] == pytest.approx(0.5), "revert info captured"
        r = rf.revert_adoption(a, adoptions[0])
        assert r["reverted"] is True
        assert a.s.node(n)["attrs"]["reform_swallowed_threshold"] == pytest.approx(0.5)
    else:
        assert at.get("adopted") is not True
        assert knob_now == pytest.approx(0.5), (
            "a non-adopted knob trial leaves the parent byte-unchanged")


# --- blind-spot filing + the audit runner's discipline ----------------------------

def test_blind_spot_residual_files_and_surfaces(agent):
    a = agent
    # R6 (bare first-person routing) is a Python-frontend blind spot: the agent
    # cannot fix comprehend_text — the correct closure is FIND + SURFACE.
    a.converse("You cannot answer the question who am I; that routing is broken.",
               speech_act="statement")
    mine = [n for n in a.s.nodes("SelfConcern")
            if "who am i" in str(a.s.node(n)["attrs"].get("content") or "").lower()]
    assert len(mine) == 1, "the explicit report files the blind-spot gap"
    assert a.s.node(mine[0])["attrs"]["kind"] == "reported"
    surfaced = a.converse("What gaps do you have?", speech_act="question")
    assert "who am i" in (surfaced or "").lower(), (
        "the filed blind spot surfaces over NL", surfaced)


def test_residual_closure_runner_source_discipline():
    import residual_closure_run as rcr
    violations = rcr.audit_source_discipline()
    assert violations == [], violations
