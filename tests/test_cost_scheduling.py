"""COST-SUBTRACTED SALIENCE — the missing half of the Graph Law.

Residual "drives refinement" (residual_salience, commit 4bca77bc); COARSENESS is driven by
COST, which the frontier_pick_term never subtracted, so two axes with equal residual/value
always tied regardless of how differently expensive they were to keep refining. This test pins
the fix authored in scripts/jabberwock_costs_its_frontier.py (jabberwock-authored via
induce_concern -> learn_term_for_concern, donkey=0, matching the SAME residual_recurrence
keystone the residual-salience fix matched): seeds/residual_salience.json's new `cost_salience`
concept = the residual_salience Term with a `- cost(axis)` subtrahend, where `cost` is
mechanically stamped (adapter I/O) from two EXISTING rule-maintained effort signals already
held on every CapabilityAxis: `investigated_count` (sunk investigation effort) and `mf_stall`
(meta_monitor's effort-without-payoff plateau counter, seeds/investigation_loop.json
`bank_measurement_to_axis`) — no new signal invented.

Exercises the SAME helpers the standalone gate script (scripts/jabberwock_costs_its_frontier.py)
runs, so this is a pytest-collected pin of that gate, not a re-implementation.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

native = pytest.importorskip("substrate_rs._native")

from substrate.world_adapter import WorldAdapter                                   # noqa: E402
from substrate.boot_all import load_all_seeds                                      # noqa: E402
from domains.reflective_faculty import induce_concern, learn_term_for_concern       # noqa: E402
from scripts.jabberwock_costs_its_frontier import (                                # noqa: E402
    author_cost_salience, install_cost_salience, stamp_axis_cost,
    _residual_salience_term, _cost_salience_term, _value_only,
    _tie_scenario, _tradeoff_scenario, _zero_cost_scenario, _original_tietrap_scenario,
)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _v(a, term, node):
    return float(a.inner.evaluate(term, {"x": node}))


# ---------------------------------------------------------------------------
# AUTHORING — donkey=0, matches its own held keystone (the SAME one the
# residual-salience fix matched — this is a further refinement of that law).
# ---------------------------------------------------------------------------
def test_authored_donkey_zero_and_matches_residual_recurrence_keystone(agent):
    donkey = {"n": 0}
    agent.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    auth = author_cost_salience(agent)
    assert donkey["n"] == 0, "authoring must be donkey=0 (no LLM calls)"
    assert auth["induce"]["minted"] is True
    assert auth["term_family"] == "residual_recurrence"


def test_cost_salience_concept_exists_in_seed():
    term = _cost_salience_term()
    assert term["type"] == "Argmax"
    # the value has one more addend than residual_salience (the cost subtrahend)
    old_items = _residual_salience_term()["value"]["items"]
    new_items = term["value"]["items"]
    assert len(new_items) == len(old_items) + 1


# ---------------------------------------------------------------------------
# MACHINERY — cost is stamped mechanically from EXISTING effort signals.
# ---------------------------------------------------------------------------
def test_cost_stamped_from_existing_effort_signals(agent):
    ids = _tie_scenario(agent)
    n = stamp_axis_cost(agent)
    assert n == 2
    at_cheap = agent.s.node(ids["cheap"])["attrs"]
    at_exp = agent.s.node(ids["expensive"])["attrs"]
    assert at_cheap["cost"] == at_cheap["investigated_count"] + at_cheap["mf_stall"]
    assert at_exp["cost"] == at_exp["investigated_count"] + at_exp["mf_stall"]
    assert at_exp["cost"] > at_cheap["cost"]


# ---------------------------------------------------------------------------
# DISCRIMINATIVE GATES.
# ---------------------------------------------------------------------------
def test_tie_break_on_equal_residual_different_cost(agent):
    ids = _tie_scenario(agent)
    stamp_axis_cost(agent)
    OLD = _value_only(_residual_salience_term())
    NEW = _value_only(_cost_salience_term())
    # OLD ties: cost-blind
    assert _v(agent, OLD, ids["cheap"]) == _v(agent, OLD, ids["expensive"])
    # NEW discriminates: the cheaper axis wins
    assert _v(agent, NEW, ids["cheap"]) > _v(agent, NEW, ids["expensive"])


def test_tradeoff_flips_when_cost_exceeds_residual_margin(agent):
    ids = _tradeoff_scenario(agent, hi_investigated_count=3.0, hi_mf_stall=0.0)  # cost 3.0 > 0.8 margin
    stamp_axis_cost(agent)
    OLD = _value_only(_residual_salience_term())
    NEW = _value_only(_cost_salience_term())
    # cost-blind: high-residual axis wins regardless of expense
    assert _v(agent, OLD, ids["hi"]) > _v(agent, OLD, ids["lo_cheap"])
    # cost-aware: the cheap lower-residual axis now wins -- a genuine flip
    assert _v(agent, NEW, ids["lo_cheap"]) > _v(agent, NEW, ids["hi"])


def test_tradeoff_holds_when_cost_is_below_residual_margin(agent):
    ids = _tradeoff_scenario(agent, hi_investigated_count=0.5, hi_mf_stall=0.0)  # cost 0.5 < 0.8 margin
    stamp_axis_cost(agent)
    NEW = _value_only(_cost_salience_term())
    # the SAME high-residual axis shape, only mildly expensive -- still wins
    assert _v(agent, NEW, ids["hi"]) > _v(agent, NEW, ids["lo_cheap"])


def test_not_a_cost_only_override(agent):
    """The trade-off runs BOTH directions on the identical axis shapes -- proving cost is
    weighed against residual, not simply overriding it (a cost-only rule would always prefer
    the cheaper axis regardless of the residual gap)."""
    a_flip = WorldAdapter(seeds=()); load_all_seeds(a_flip)
    ids_flip = _tradeoff_scenario(a_flip, hi_investigated_count=3.0, hi_mf_stall=0.0)
    stamp_axis_cost(a_flip)
    NEW = _value_only(_cost_salience_term())
    flips = _v(a_flip, NEW, ids_flip["lo_cheap"]) > _v(a_flip, NEW, ids_flip["hi"])

    a_hold = WorldAdapter(seeds=()); load_all_seeds(a_hold)
    ids_hold = _tradeoff_scenario(a_hold, hi_investigated_count=0.5, hi_mf_stall=0.0)
    stamp_axis_cost(a_hold)
    holds = _v(a_hold, NEW, ids_hold["hi"]) > _v(a_hold, NEW, ids_hold["lo_cheap"])
    assert flips and holds


# ---------------------------------------------------------------------------
# BACKWARD COMPATIBILITY.
# ---------------------------------------------------------------------------
def test_zero_cost_reduces_exactly_to_residual_salience(agent):
    ids = _zero_cost_scenario(agent)
    stamp_axis_cost(agent)  # all axes have investigated_count=mf_stall=0 -> cost=0
    OLD = _value_only(_residual_salience_term())
    NEW = _value_only(_cost_salience_term())
    for node in ids.values():
        assert _v(agent, OLD, node) == _v(agent, NEW, node)


def test_original_tietrap_scenario_still_resolves_hard_under_cost_term(agent):
    """The ORIGINAL 4bca77bc tie-trap scenario, with its real accumulated mf_stall /
    investigated_count, still picks the high-residual hard frontier once cost_salience is
    installed and run through the live _frontier_advance reflex -- no regression."""
    ids = _original_tietrap_scenario(agent)
    assert install_cost_salience(agent)
    stamp_axis_cost(agent)
    agent._frontier_advance()
    edges = agent.inner.neighbours(agent.agent, "frontier_pick")
    assert edges and edges[0] == ids["hard"]


def test_residual_salience_gate_script_unaffected():
    """The precedent gate (scripts/jabberwock_wires_residual_salience.py) must still pass --
    appending the new cost_salience concept to seeds/residual_salience.json must not disturb
    the existing residual_salience concept it reads."""
    from scripts.jabberwock_wires_residual_salience import main as residual_main
    assert residual_main() == 0


# ---------------------------------------------------------------------------
# FROZEN CORE.
# ---------------------------------------------------------------------------
def test_understand_drive_stays_frozen_after_swap(agent):
    assert install_cost_salience(agent)
    drives = [n for n in agent.s.nodes("Drive") if agent.s.node(n)["attrs"].get("name") == "understand"]
    assert drives
    assert agent.s.node(drives[0])["attrs"].get("frozen") is True


def test_gate_script_exits_zero():
    from scripts.jabberwock_costs_its_frontier import main
    assert main() == 0
