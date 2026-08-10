"""Net economy — the agent's OWN worth law applied to its own reflexes.

Gates seeds/net_economy.json + domains/net_economy.py. A reflex net earns its
footprint iff worth = residual - cost > 0, where the residual is the cognition
it COMPRESSES (accumulated speedup over regression-free in-basin hits — the
agent's held quality measure) and the cost is its footprint (storage rent) plus
the corrections it forces (confidently-wrong-outside-basin misses). The value
law (worth = residual - cost) is the agent's own named relation; the regulation
is its feedback_control meta-shape; ADMISSION (adopt) and RETIREMENT (ablate)
are two rules on the existing reflex-net spine — retirement realizing the
concern the agent's design faculty itself minted.

The whole loop runs in ONE run_rules fixpoint: measured trial -> judge
(supported/refuted) -> ledger credit/debit -> admit/retire.
"""
from __future__ import annotations

import json
import os

from substrate_rs import _native
from domains.net_economy import mint_policy, init_ledger, net_footprint, worth

_SEED_REFLEX = os.path.join(os.path.dirname(__file__), "..", "seeds", "reflex_net.json")
_SEED_ECON = os.path.join(os.path.dirname(__file__), "..", "seeds", "net_economy.json")

_NODE = ("NetEconomyPolicy", "ReflexNet", "NetworkAssemblage", "AssemblageStep",
         "WeightTensor", "ReflexTrial", "Agent")
_EDGE = ("net_assemblage", "has_step", "has_weight", "judges", "for_reflex")


def _rules(path, *names):
    allr = {r["name"]: r for r in json.load(open(path))["rules"]}
    return [allr[n] for n in names]


def _fresh(**policy):
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    # The judge (held) + the economy (new) — the full measured->admit/retire chain.
    for r in _rules(_SEED_REFLEX, "reflex_trial_judge", "reflex_trial_refuted"):
        s.add_rule(r)
    for r in _rules(_SEED_ECON, "net_ledger_credit_hit", "net_ledger_debit_miss",
                    "net_admit_when_worth_positive", "net_retire_when_worth_negative"):
        s.add_rule(r)
    mint_policy(s, **policy)
    return s


def _net(s, *, status="proposed", enabled=0.0, hidden=4, in_dim=2, out_dim=1):
    """A minimal reflex net with a real assemblage (so footprint is nonzero),
    ledger zeroed."""
    rn = s.add_node("ReflexNet", {"name": "n", "status": status, "enabled": enabled})
    asm = s.add_node("NetworkAssemblage", {"input_dim": in_dim, "output_dim": out_dim})
    sid = s.add_node("AssemblageStep", {"order": 0})
    s.add_edge(asm, "has_step", sid, {})
    for role, dat in (("W1", [[0.0] * in_dim for _ in range(hidden)]),
                      ("b1", [0.0] * hidden),
                      ("W2", [[0.0] * hidden for _ in range(out_dim)]),
                      ("b2", [0.0] * out_dim)):
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    s.add_edge(rn, "net_assemblage", asm, {})
    init_ledger(s, rn)
    return rn


def _trial(s, ag, rn, *, regression, reflex_ms, slow_ms, tol=0.01):
    t = s.add_node("ReflexTrial", {"status": "measured", "regression": regression,
                                   "tolerance": tol, "reflex_ms": reflex_ms,
                                   "slow_ms": slow_ms})
    s.add_edge(ag, "judges", t, {})
    s.add_edge(t, "for_reflex", rn, {})
    return t


def test_footprint_counts_parameters():
    """Footprint = the net's parameter count, read structurally off its
    WeightTensors — the storage-rent basis, no decision."""
    s = _fresh()
    rn = _net(s, hidden=4, in_dim=2, out_dim=1)
    # W1(4x2)=8 + b1(4)=4 + W2(1x4)=4 + b2(1)=1 = 17
    assert net_footprint(s, rn) == 17
    assert s.node(rn)["attrs"]["footprint"] == 17.0


def test_worth_is_residual_minus_cost():
    """After judging, the ledger accumulates the agent's law: net_residual =
    sum of hit speedups, net_cost = sum of miss penalties, and worth =
    residual - cost - footprint rent."""
    s = _fresh()
    ag = s.add_node("Agent", {"name": "self"})
    rn = _net(s)
    # 3 in-basin hits (regression-free AND faster; speedup 4 each) ...
    for _ in range(3):
        _trial(s, ag, rn, regression=0.001, reflex_ms=1.0, slow_ms=5.0)
    # ... and 1 miss (regresses -> refuted; penalty = 1*(1+5) = 6)
    _trial(s, ag, rn, regression=0.5, reflex_ms=1.0, slow_ms=5.0)
    s.run_rules()
    a = s.node(rn)["attrs"]
    assert a["net_residual"] == 12.0, "3 hits x (5-1) speedup"
    assert a["net_cost"] == 6.0, "1 miss x (1+5) correction"
    assert a["n_ledger_trials"] == 4.0
    # worth = 12 - 6 - 0.0001*17 ~ 5.9983
    assert abs(worth(s, rn) - (12.0 - 6.0 - 0.0001 * 17)) < 1e-6


def test_admit_when_worth_positive():
    """A proposed (OFF) net that proves positive worth over the window turns
    ITSELF on — the economy is the admission decision."""
    s = _fresh()
    ag = s.add_node("Agent", {"name": "self"})
    rn = _net(s, status="proposed", enabled=0.0)
    for _ in range(5):  # > ledger_window (3), all hits -> worth strongly positive
        _trial(s, ag, rn, regression=0.001, reflex_ms=1.0, slow_ms=5.0)
    s.run_rules()
    a = s.node(rn)["attrs"]
    assert a["enabled"] == 1.0, "positive-worth net admitted (enabled on)"
    assert a["status"] == "adopted"
    assert a["admitted_worth"] > 0.0


def test_retire_when_worth_negative_realizes_minted_concern():
    """An ENABLED net whose corrections come to outweigh the cognition it saves
    turns ITSELF off — the retirement law the agent's design faculty minted."""
    s = _fresh()
    ag = s.add_node("Agent", {"name": "self"})
    rn = _net(s, status="adopted", enabled=1.0)
    # mostly misses: 1 hit (+4), 4 misses (-6 each = -24) -> worth ~ -20
    _trial(s, ag, rn, regression=0.001, reflex_ms=1.0, slow_ms=5.0)
    for _ in range(4):
        _trial(s, ag, rn, regression=0.5, reflex_ms=1.0, slow_ms=5.0)
    s.run_rules()
    a = s.node(rn)["attrs"]
    assert a["enabled"] == 0.0, "negative-worth net retired (enabled off)"
    assert a["status"] == "retired"
    assert a["retired_worth"] < 0.0


def test_policy_retire_floor_is_a_tweakable_knob():
    """The retirement decision is a graph edit: the SAME net with the SAME
    ledger survives at a lenient retire_floor and is culled at a strict one —
    zero code, just set_attr on the feedback_control knob."""
    def run(retire_floor):
        s = _fresh()
        # Edit the held policy LIVE — a plain set_attr, zero code.
        pol = next(iter(s.nodes("NetEconomyPolicy")))
        s.set_attr(pol, "retire_floor", retire_floor)
        ag = s.add_node("Agent", {"name": "self"})
        rn = _net(s, status="adopted", enabled=1.0)
        # worth ends slightly negative: 4 hits (+16), 5 misses (-30) -> -14
        for _ in range(4):
            _trial(s, ag, rn, regression=0.001, reflex_ms=1.0, slow_ms=5.0)
        for _ in range(5):
            _trial(s, ag, rn, regression=0.5, reflex_ms=1.0, slow_ms=5.0)
        s.run_rules()
        return s.node(rn)["attrs"]["enabled"]

    assert run(-100.0) == 1.0, "lenient floor spares the net"
    assert run(0.0) == 0.0, "strict floor retires the same net"


def test_ledger_folds_each_trial_once():
    """Running the fixpoint again does not double-count — the `ledgered` guard
    makes each trial fold in exactly once (idempotent)."""
    s = _fresh()
    ag = s.add_node("Agent", {"name": "self"})
    rn = _net(s)
    for _ in range(3):
        _trial(s, ag, rn, regression=0.001, reflex_ms=1.0, slow_ms=5.0)
    s.run_rules()
    first = s.node(rn)["attrs"]["net_residual"]
    s.run_rules()
    assert s.node(rn)["attrs"]["net_residual"] == first, "no double credit"
