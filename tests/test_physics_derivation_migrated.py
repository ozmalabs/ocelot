"""PHYSICS FROM OBSERVATION — the RESTORED landmark, now graph-native + gated.

The jabberwock derives physics from raw observation with NO reward, NO label,
NO published rate, NO hardcoded law — reproduced on the current seed-booted Rust
substrate after the CuriousAgent deletion (commit c0288920) removed the original
Python `observe()`/derive/accumulate layer. The world adapters
(`domains/physics_world.py`) publish ONLY position + intrinsic mass; the
derivation + law-discovery are RULES (`seeds/physics_derivation.json`) that
REUSE the surviving `law_predicate` / `conservation_predicate` from
`seeds/epistemics_core.json` (via the `EvalSubgraph` reflection Term — NOT
re-authored). This is a POSITIVE-CONTROLLED gate:

  Galileo   : within `falling`, acc_y == -1, INDEPENDENT of mass (identical
              across masses 1/4/9) — Aristotle's exact inverse.
              CONTROL: the within-regime-VARYING quantity (`grounded` acc_y,
              and `mass` itself) mints NO law.
  Momentum  : Σ(mass·vel_x) stays EXACTLY constant (distinct==1) while the
              individual puck velocities vary (distinct>=3).
              CONTROL: an unconserved quantity (a single vel_x) is not lawed.
  Lever     : within `balanced`, net_torque == 0, INDEPENDENT of total load.
              CONTROL: the `unbalanced` regime mints no law.

Every vel/acc/momentum/torque is AGENT-DERIVED — never published (asserted by
capturing exactly what the world's publish() emits).

Determinism: free-fall and collision are RNG-free; the lever uses a fixed
seed (LeverWorld(seed=0)). No RNG-seed block is drawn.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

pytest.importorskip("substrate_rs")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.boot_core import boot_core
from domains.physics_world import (
    CollisionWorld, LeverWorld, PhysicsWorld,
    load_physics_seed, run_lever, run_world,
)

SEED_PATH = os.path.join(ROOT, "seeds", "physics_derivation.json")


# --------------------------------------------------------------------------- #
# graph read-off helpers  (native.evaluate / node reads return real values)
# --------------------------------------------------------------------------- #
def _nodes(s, t):
    return [n for n in s.nodes() if s.node(n)["type"] == t]


def _laws(s):
    return [s.node(l)["attrs"] for l in _nodes(s, "Law")]


def _obs(s, q):
    return [s.node(o)["attrs"] for o in _nodes(s, "Obs")
            if s.node(o)["attrs"].get("q") == q]


def _booted():
    s, ag = boot_core()
    load_physics_seed(s, ag)
    return s, ag


# --------------------------------------------------------------------------- #
# 0. SOURCE AUDIT — the kernel predicates are REUSED, not re-authored.
# --------------------------------------------------------------------------- #
def test_seed_reuses_kernel_predicates_not_reauthored():
    raw = open(SEED_PATH).read()
    manifest = json.loads(raw)
    # The law/conservation decision is reached by EvalSubgraph following the
    # named edge off agent_root — the surviving epistemics_core Term-trees.
    assert '"EvalSubgraph"' in raw
    assert '"edge_type": "law_predicate"' in raw
    assert '"edge_type": "conservation_predicate"' in raw
    # And the predicate itself is NOT re-inlined here: the seed must not carry
    # its own And(obs_count>=6, distinct==1, global>=2) — that lives ONLY in
    # epistemics_core. (obs_count/global_distinct are WRITTEN by recompute, but
    # never COMPARED to 6/2 in this seed.)
    assert '"global_distinct"' in raw          # written by recompute...
    assert '"value": 6' not in raw             # ...but the threshold is not here
    # No Python agent decision file resurrected.
    assert manifest["depends_on"] == ["epistemics_core"]


# --------------------------------------------------------------------------- #
# 1. GALILEO — acc ⟂ mass
# --------------------------------------------------------------------------- #
def test_galileo_acc_independent_of_mass():
    s, ag = _booted()
    # Capture EXACTLY what the world publishes — proves vel/acc are not fed in.
    published_keys = set()
    w = PhysicsWorld()
    _orig = w.publish
    def _spy():
        recs = _orig()
        for r in recs:
            published_keys.update(r.keys())
        return recs
    w.publish = _spy
    run_world(s, ag, w, ticks=16)

    # The world published position + mass ONLY — never a rate.
    assert "y_bin" in published_keys and "mass" in published_keys
    for forbidden in ("vel_y", "acc_y", "vel_x", "acc_x", "momentum"):
        assert forbidden not in published_keys, f"world leaked {forbidden}"

    # Exactly one regime-invariant law: acc_y == -1 while falling.
    galileo = [l for l in _laws(s) if l.get("kind") == "regime_invariant"
               and l.get("regime") == "falling" and l.get("quantity") == "acc_y"]
    assert len(galileo) == 1, _laws(s)
    law = galileo[0]
    assert law["invariant_value"] == -1
    # independent_of mass (mass varies within falling, acc_y does not).
    indep = {s.node(x)["attrs"].get("quantity")
             for x in s._inner.neighbours(_galileo_node(s), "independent_of")}
    assert "mass" in indep

    # acc_y == -1 IDENTICALLY across the falling regime; the mass stream shows
    # all three masses 1/4/9 fell under that same single acc value.
    accs_falling = {o["v"] for o in _obs(s, "acc_y") if o.get("regime") == "falling"}
    assert accs_falling == {-1}, accs_falling
    masses = {o["v"] for o in _obs(s, "mass") if o.get("regime") == "falling"}
    assert masses == {1.0, 4.0, 9.0}, masses

    # CONTROL: the within-regime-VARYING quantity mints no law.
    #   grounded acc_y varies (distinct>=2) -> no law; mass varies -> no law.
    for l in _laws(s):
        if l.get("kind") != "regime_invariant":
            continue
        assert not (l.get("regime") == "grounded" and l.get("quantity") == "acc_y"), \
            "grounded acc_y varies — must not be a law"
        assert l.get("quantity") != "mass", "mass varies within regime — not a law"


def _galileo_node(s):
    for l in _nodes(s, "Law"):
        a = s.node(l)["attrs"]
        if a.get("kind") == "regime_invariant" and a.get("regime") == "falling" \
                and a.get("quantity") == "acc_y":
            return l
    raise AssertionError("no galileo law node")


def test_velocity_and_acceleration_are_agent_derived():
    """vel_y/acc_y live on the graph but were NEVER published — they are minted
    by pw_kinematics, the agent inventing the rate."""
    s, ag = _booted()
    run_world(s, ag, PhysicsWorld(), ticks=8)
    live_balls = [s.node(n)["attrs"] for n in _nodes(s, "Ball")]
    assert live_balls, "expected live Ball nodes"
    assert any("vel_y" in b and "acc_y" in b for b in live_balls), \
        "no agent-derived kinematics on any Ball"


# --------------------------------------------------------------------------- #
# 2. MOMENTUM — a conserved composite whose parts vary
# --------------------------------------------------------------------------- #
def test_momentum_conserved_while_parts_vary():
    s, ag = _booted()
    run_world(s, ag, CollisionWorld(), ticks=24)

    mom = [o["v"] for o in _obs(s, "momentum")]
    assert len(mom) >= 6
    assert set(mom) == {2.0}, f"momentum not constant: {set(mom)}"

    vx = {o["v"] for o in _obs(s, "vel_x")}
    assert len(vx) >= 3, f"parts did not vary: {vx}"      # {3,-1,0}

    cons = [l for l in _laws(s) if l.get("kind") == "conservation"
            and l.get("quantity") == "momentum"]
    assert len(cons) == 1, _laws(s)
    assert cons[0]["invariant_value"] == 2.0
    assert cons[0].get("conserved_despite") == "vel_x"

    # CONTROL: an unconserved quantity (a single vel_x) is NOT lawed.
    assert not any(l.get("kind") == "conservation" and l.get("quantity") == "vel_x"
                   for l in _laws(s))


def test_momentum_law_needs_evidence():
    """The kernel law_predicate gates on obs_count>=6: too few observations ->
    no conservation law yet (positive control that the predicate is live)."""
    s, ag = _booted()
    run_world(s, ag, CollisionWorld(), ticks=3)
    assert not any(l.get("kind") == "conservation" for l in _laws(s))


# --------------------------------------------------------------------------- #
# 3. LEVER — Archimedes
# --------------------------------------------------------------------------- #
def test_lever_net_torque_zero_at_balance():
    s, ag = _booted()
    run_lever(s, ag, LeverWorld(seed=0), configs=40)

    balanced = [l for l in _laws(s) if l.get("kind") == "regime_invariant"
                and l.get("regime") == "balanced" and l.get("quantity") == "net_torque"]
    assert len(balanced) == 1, _laws(s)
    law = balanced[0]
    assert law["invariant_value"] == 0.0
    lnode = next(l for l in _nodes(s, "Law")
                 if s.node(l)["attrs"].get("regime") == "balanced"
                 and s.node(l)["attrs"].get("quantity") == "net_torque")
    indep = {s.node(x)["attrs"].get("quantity")
             for x in s._inner.neighbours(lnode, "independent_of")}
    assert "total_load" in indep

    # net_torque varies within `balanced`? No — it is pinned to 0. It varies
    # GLOBALLY (unbalanced configs), which is what makes 0 a law not a triviality.
    tq_bal = {o["v"] for o in _obs(s, "net_torque") if o.get("regime") == "balanced"}
    assert tq_bal == {0.0}, tq_bal
    tq_all = {o["v"] for o in _obs(s, "net_torque")}
    assert len(tq_all) >= 2, "net_torque must vary globally"

    # CONTROL: the `unbalanced` regime mints no net_torque law.
    assert not any(l.get("kind") == "regime_invariant"
                   and l.get("regime") == "unbalanced"
                   and l.get("quantity") == "net_torque" for l in _laws(s))
