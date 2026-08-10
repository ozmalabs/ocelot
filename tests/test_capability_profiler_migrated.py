"""Capability profiler — the capstone: measure the capability graph from the agent's
OWN activity, not hand-wired.

A real workload (the net-economy rule chain) runs on one substrate. The profiler then
reads which rules fired (the engine's own `rule_costs()`) and derives their composes_on
dataflow from the rules themselves (rule B composes_on rule A iff B reads an attr A
writes), and builds a capability graph in a second substrate. The EXISTING
`cap_leverage_propagate` rule then computes leverage over that measured structure — and
the rule everything routes through (the judge, the chain's source) surfaces as the
highest-leverage capability, with no composes_on edge authored by hand.
"""
from __future__ import annotations

import json
import os

from substrate_rs import _native
from domains.capability_graph import (
    mint_root, settle, leverage, worth, tier_up, own_proficiency, eff_cap, correctness,
)
from domains.capability_profiler import profile, build_type_map

_R = os.path.join(os.path.dirname(__file__), "..", "seeds")
_ALL = {r["name"]: r
        for f in ("reflex_net.json", "net_economy.json", "capability_graph.json")
        for r in json.load(open(os.path.join(_R, f)))["rules"]}
_CHAIN = ["reflex_trial_judge", "reflex_trial_refuted", "net_ledger_credit_hit",
          "net_ledger_debit_miss", "net_admit_when_worth_positive",
          "net_retire_when_worth_negative"]
_TYPE_MAP = build_type_map([p for f in ("reflex_net.json", "net_economy.json")
                            for p in json.load(open(os.path.join(_R, f))).get("productions", [])])


def _open(nodes, edges):
    s = _native.Substrate()
    for a in nodes:
        for b in nodes:
            for et in edges:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    return s


def _run_workload():
    """Run the net-economy chain on a real scenario (hits + misses) so every rule fires."""
    w = _open(("NetEconomyPolicy", "ReflexNet", "NetworkAssemblage", "AssemblageStep",
               "WeightTensor", "ReflexTrial", "Agent"),
              ("net_assemblage", "has_step", "has_weight", "judges", "for_reflex"))
    for n in _CHAIN:
        w.add_rule(_ALL[n])
    w.add_node("NetEconomyPolicy", {"kind": "p", "admit_margin": 0.0, "retire_floor": 0.0,
               "miss_penalty_weight": 1.0, "footprint_weight": 0.0001, "ledger_window": 3})
    ag = w.add_node("Agent", {"name": "self"})

    def net(status, enabled):
        rn = w.add_node("ReflexNet", {"name": "n", "status": status, "enabled": enabled,
                        "net_residual": 0.0, "net_cost": 0.0, "n_ledger_trials": 0.0,
                        "footprint": 10.0})
        asm = w.add_node("NetworkAssemblage", {"input_dim": 2, "output_dim": 1})
        w.add_edge(rn, "net_assemblage", asm, {})
        return rn

    def trial(rn, reg):
        t = w.add_node("ReflexTrial", {"status": "measured", "regression": reg,
                       "tolerance": 0.01, "reflex_ms": 1.0, "slow_ms": 5.0})
        w.add_edge(ag, "judges", t, {})
        w.add_edge(t, "for_reflex", rn, {})

    n1 = net("proposed", 0.0)                 # hits -> judge + credit + admit
    for _ in range(5):
        trial(n1, 0.001)
    n2 = net("adopted", 1.0)                   # misses -> refuted + debit + retire
    trial(n2, 0.001)
    for _ in range(5):
        trial(n2, 0.5)
    w.run_rules()
    return w


def _self_model():
    c = _open(("CapabilityRoot", "Capability", "CapabilityPolicy"),
              ("has_capability", "composes_on"))
    for r in _ALL.values():
        if r["name"] in ("cap_leverage_propagate", "cap_stage_from_leverage",
                         "cap_tier_up", "cap_effective_compose"):
            c.add_rule(r)
    return c, mint_root(c)


def test_profiler_measures_leverage_from_activity():
    """The whole chain fired; the profiler builds the capability graph from firings +
    derived dataflow; leverage ranks the source (judge) above the ledger above the sinks
    — recovered, not authored."""
    w = _run_workload()
    fired = {name for (name, _u, _p, prog) in w.rule_costs() if prog > 0}
    assert set(_CHAIN) <= fired, f"the whole chain should fire; got {fired}"

    c, root = _self_model()
    caps = profile(w, _ALL, c, root)
    settle(c)
    assert set(caps) == set(_CHAIN), "every fired rule became a measured capability"

    lev = {n: leverage(c, caps[n]) for n in _CHAIN}
    # The judge is the source of the chain's dataflow (its `verdict` feeds the ledger,
    # whose totals feed admit/retire) — so it must carry the highest measured leverage,
    # though NO composes_on edge was hand-written.
    assert lev["reflex_trial_judge"] == max(lev.values()), \
        f"the judge surfaces as the highest-leverage capability: {lev}"
    assert (lev["reflex_trial_judge"] > lev["net_ledger_credit_hit"]
            > lev["net_admit_when_worth_positive"]), \
        f"source > ledger > sink, recovered from dataflow: {lev}"


def test_one_cost_model_tiers_up_the_hot_core():
    """The unified cost model at the capability grain: worth = leverage − cost_weight·cost,
    tier_up when worth clears the margin and it's hot enough. Fed the MEASURED leverage/cost/
    hotness, it flags the hot central rules to master and leaves the cold sinks — the same
    decision shape the net-economy uses to admit a net and the JIT to compile a Term."""
    w = _run_workload()
    c, root = _self_model()
    caps = profile(w, _ALL, c, root)
    settle(c)
    assert tier_up(c, caps["reflex_trial_judge"]), "the hot, central judge tiers up (worth mastering)"
    assert not tier_up(c, caps["net_retire_when_worth_negative"]), "the low-worth sink does not"
    assert worth(c, caps["reflex_trial_judge"]) > worth(c, caps["net_retire_when_worth_negative"])


def test_own_proficiency_is_measured_from_cost():
    """own_proficiency is no longer a constant 1.0 — it's MEASURED as efficiency (cheaper per
    firing => more mastered/optimised, the JIT's notion), from the engine's own cost counters."""
    w = _run_workload()
    c, root = _self_model()
    caps = profile(w, _ALL, c, root)
    settle(c)
    profs = {n: own_proficiency(c, caps[n]) for n in _CHAIN}
    assert all(0.0 < p <= 1.0 for p in profs.values()), "measured efficiency-proficiency in (0,1]"
    assert len(set(round(p, 4) for p in profs.values())) > 1, \
        "proficiency varies with measured cost — not a hardcoded constant"


def test_derived_dataflow_is_acyclic_and_effcap_composes():
    """The sharpened rule (B composes_on A iff B reads a key A writes that B does NOT itself
    write) excludes shared-accumulator keys, so the measured graph is a DAG — multiplicative
    effective capability composes cleanly instead of collapsing to 0 on a credit<->debit cycle."""
    w = _run_workload()
    c, root = _self_model()
    caps = profile(w, _ALL, c, root)
    settle(c)
    effs = {n: eff_cap(c, caps[n]) for n in _CHAIN}
    assert all(0.0 < e <= 1.0 for e in effs.values()), \
        f"no cyclic collapse — all effective capabilities in (0,1]: {effs}"
    # the ledger composes on the judge, so its eff_cap is bounded by the judge's (a product)
    assert effs["net_ledger_credit_hit"] <= own_proficiency(c, caps["reflex_trial_judge"]) + 1e-9


def test_type_qualified_dataflow_resolves_key_collisions():
    """With (node-type, key) read/write sets, `status` written on a ReflexTrial and read on a
    ReflexNet no longer collide — admit does NOT falsely compose_on the judge, while the real
    edge (credit reads the judge's `verdict`) survives. Types resolve it, no control-key hack."""
    w = _run_workload()
    c, root = _self_model()
    caps = profile(w, _ALL, c, root, type_map=_TYPE_MAP)
    settle(c)
    admit_founds = set(c.neighbours(caps["net_admit_when_worth_positive"], "composes_on"))
    assert caps["reflex_trial_judge"] not in admit_founds, \
        "no false status-edge: (ReflexNet,status) != (ReflexTrial,status)"
    credit_founds = set(c.neighbours(caps["net_ledger_credit_hit"], "composes_on"))
    assert caps["reflex_trial_judge"] in credit_founds, "the real (ReflexTrial,verdict) edge survives"
    lev = {n: leverage(c, caps[n]) for n in _CHAIN}
    assert lev["reflex_trial_judge"] == max(lev.values()), "the judge is still the measured source"


def test_correctness_accrues_from_standing_oracle():
    """The reflex-net judge is a STANDING ORACLE already running in run_rules. It verdicts trials
    supported/refuted as the graph ticks; cap_harvest_reflex_verdict turns each into a
    CapabilityTrial on the net, and correctness -> own_prof accrues live — no hand-supplied trials."""
    s = _open(("Agent", "ReflexTrial", "ReflexNet", "CapabilityTrial", "Capability"),
              ("judges", "for_reflex", "trial_of"))
    for n in ("reflex_trial_judge", "reflex_trial_refuted",
              "cap_harvest_reflex_verdict", "cap_correctness_from_trials"):
        s.add_rule(_ALL[n])
    ag = s.add_node("Agent", {"name": "self"})
    rn = s.add_node("ReflexNet", {"name": "cache", "correctness": -1.0, "own_prof": 0.5})

    def trial(reg):                    # measured, UN-judged — the oracle judges it in run_rules
        t = s.add_node("ReflexTrial", {"status": "measured", "regression": reg,
                       "tolerance": 0.01, "reflex_ms": 1.0, "slow_ms": 5.0})
        s.add_edge(ag, "judges", t, {})
        s.add_edge(t, "for_reflex", rn, {})

    for _ in range(8):
        trial(0.001)                   # regression-free & faster -> supported
    for _ in range(2):
        trial(0.5)                     # regresses -> refuted
    s.run_rules()                      # judge -> harvest -> correctness, all in one fixpoint

    assert abs(correctness(s, rn) - 0.8) < 1e-9, "8/10 supported, harvested live from the judge"
    assert own_proficiency(s, rn) == 0.8, "correctness became the net's own_prof, no supplied trials"


def test_composes_on_is_derived_not_authored():
    """The composition edges come from the rules' own read/write dataflow — the ledger
    composes_on the judge because it READS the `verdict` the judge WRITES."""
    w = _run_workload()
    c, root = _self_model()
    caps = profile(w, _ALL, c, root)
    credit_founds = set(c.neighbours(caps["net_ledger_credit_hit"], "composes_on"))
    assert caps["reflex_trial_judge"] in credit_founds, \
        "credit composes_on judge — derived from 'reads verdict', never authored"
    admit_founds = set(c.neighbours(caps["net_admit_when_worth_positive"], "composes_on"))
    assert caps["net_ledger_credit_hit"] in admit_founds, \
        "admit composes_on the ledger — derived from 'reads net_residual'"
