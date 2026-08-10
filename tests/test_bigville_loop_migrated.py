"""bigville R5 (block 253000) -- THE LOOP CLOSES + emergent cascades. INTEGRATION
gates: the multi-day town loop (measure-first: sustain or a real breakdown), the full
fishmonger cascade (every hop off the graph), the sever-edge falsifier, the
carrying-capacity balance, and the money-conservation invariant. Gates mirror
BIGVILLE_LOOP_PREREG.md. No agent decision lives in Python -- every produce / buy /
credit / default / affect-flip / badmouth / opinion / open-shut / surprise / satisfice
is a seed rule (source-audit below).
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_loop_world import BigvilleLoopWorld, CONSUMERS   # noqa: E402
from worlds.bigville_econ_world import FISH, BREAD, ALE, FISHING      # noqa: E402
from worlds.bigville_time_world import NIGHT                          # noqa: E402
import scripts.bigville_loop_run as run                               # noqa: E402


# ================================================== G-town-runs (measure-first)
def test_viable_town_sustains_over_multiple_days_money_conserved():
    """G-town-runs: the DEFAULT viable regime SUSTAINS a multi-day loop -- every
    consumer is fed each day (no unmet demand), the carrying-capacity bread margin is
    positive, and total coin is CONSERVED (money is a fixed supply of transfers)."""
    w = BigvilleLoopWorld(day_range=16, regime="viable", wages_on=True)
    cap = w.carrying_capacity()
    assert cap["bread"]["margin"] > 0, cap          # harvest meets population demand
    cen = w.run_town(days=4)                         # asserts Σcoin conserved internally
    assert all(not r["unmet_demand"] for r in cen), [r["unmet_demand"] for r in cen]
    cc = w.coin_conserved()
    assert cc["drift"] == 0.0, cc                    # money NOT minted/burned
    w.close()


def test_marjorie_full_day_reads_off_the_graph():
    """Glass-box (spec headline): Marjorie's WHOLE day, phase by phase, off the graph --
    wake -> bake during hours (yield ∝ skill) -> sell -> eat/town -> restock grain
    up-chain -> sleep. Every field a read-off."""
    w = BigvilleLoopWorld(day_range=16, regime="viable")
    w.run_town(days=1)
    d = w.marjorie_day(1)[0]
    assert d["shop_open"] == 1                       # open during hours
    assert d["baked_to_stock"] == 5                  # yield = viable baker skill (5)
    assert d["sold_units"] >= 1 and d["coin_from_sales"] >= 1   # sold, coin in
    assert d["grain_after_restock"] >= 1             # bought grain up-chain
    assert "night_energy" in d and "end_coin" in d   # tired -> sleep
    w.close()


def test_carrying_capacity_shortfall_is_famine_named_knob():
    """G-town-runs (imbalance is a finding): turning the carrying-capacity knob DOWN
    (baker skill below population bread-demand) flips the margin NEGATIVE and produces a
    real FAMINE (unmet demand appears), while the viable regime feeds everyone. The knob
    is the baker's harvest ceiling -- not hand-forced sustainability."""
    viable = BigvilleLoopWorld(day_range=16, regime="viable")
    short = BigvilleLoopWorld(day_range=16, regime="shortfall")
    assert viable.carrying_capacity()["bread"]["margin"] > 0
    assert short.carrying_capacity()["bread"]["margin"] < 0
    cv = viable.run_town(days=4)
    cs = short.run_town(days=4)
    assert all(not r["unmet_demand"] for r in cv)            # viable: nobody starves
    assert any(r["unmet_demand"] for r in cs)                # shortfall: famine appears
    viable.close(); short.close()


def test_money_conservation_holds_in_every_regime():
    """G-discipline (money is FIXED): Σcoin is INVARIANT across the loop in EVERY
    regime -- viable+wages, wages-off, and shortfall. A wage is a conserving transfer,
    never a mint; a drift would be a currency bug (asserted inside run_town)."""
    for regime, wages in [("viable", True), ("viable", False), ("shortfall", True)]:
        w = BigvilleLoopWorld(day_range=16, regime=regime, wages_on=wages)
        w.run_town(days=4)
        assert w.coin_conserved()["drift"] == 0.0, (regime, wages, w.coin_conserved())
        w.close()


def test_wages_off_money_pools_and_demand_seizes():
    """Monetary finding (goods viable, but circulation matters): with the wage loop OFF,
    coin POOLS at the producers and consumer demand SEIZES though the carrying-capacity
    bread margin is still POSITIVE (goods are plentiful) -- money must circulate, not
    just be conserved. Σcoin stays conserved throughout."""
    w = BigvilleLoopWorld(day_range=16, regime="viable", wages_on=False)
    assert w.carrying_capacity()["bread"]["margin"] > 0     # goods are plentiful
    cen = w.run_town(days=4)
    assert any(r["unmet_demand"] for r in cen), "demand should seize once coin pools"
    assert w.coin_conserved()["drift"] == 0.0
    # coin pooled: a producer ends far richer than a (drained) consumer
    prod = max(w.coin_of(nm) for nm in w._trade_names)
    cons = [w.coin_of(nm) for nm in CONSUMERS if nm in w._movers]
    assert prod > max(cons), (prod, cons)
    w.close()


# ============================================ G-fishmonger-cascade (HEADLINE)
def test_fishmonger_cascade_every_hop_off_the_graph():
    """G-fishmonger-cascade (the anti-bullshit gate): induce Doreen's exhaustion
    collapse, then EVERY hop is a real state change read off the graph --
    (a) missed opening -> expectation SURPRISE;
    (b) DOWN-chain: no fish -> the fish-preferrer SATISFICES to bread;
    (c) UP-chain: drink -> can't pay -> DEFAULT -> the fisherman's AFFECT flips (arousal
        up, valence down, demand_cash=1) -> he BADMOUTHS Doreen -> townsfolk backing
        flips 1->0 (the 245 credibility layer MOVES). economy->affect->society CLOSED."""
    c = run.demo_cascade(sever=False)
    # drink really cost coins; collapse is involuntary
    assert c["drink"]["coin_after"] < c["drink"]["coin_before"] and c["drink"]["ale_held"] == 1
    assert c["collapse"]["sleep_kind"] == 2 and c["collapse"]["collapsed"] == 1
    # (a) expectation surprise
    assert c["expectation"]["stall_open"] == 0 and c["expectation"]["surprise"] == 1
    # (b) down-chain satisfice: fish preferred, then bread taken when fish is gone
    assert c["down_chain"]["with_fish_chosen"] == int(FISH)
    assert c["down_chain"]["satisfices_to"] == int(BREAD)
    # (c) up-chain: default -> affect flip -> badmouth -> society moves
    u = c["up_chain"]
    assert u["doreen_defaulted"] == 1 and len(u["owe_minted"]) == 1
    assert u["fisherman_arousal"][1] > u["fisherman_arousal"][0]      # arousal up
    assert u["fisherman_valence"][1] < u["fisherman_valence"][0]      # valence down
    assert u["fisherman_demand_cash"] == 1 and u["fisherman_unpaid"] > 0
    assert u["doreen_badmouthed"] > 0 and u["n_badmouth_nodes"] == 1
    assert c["pre_backs"] == [1, 1, 1] and u["post_backs"] == [0, 0, 0]  # 245 layer moves


# ============================================ G-propagates (the sever falsifier)
def test_sever_edge_makes_the_whole_cascade_vanish():
    """G-propagates-along-the-graph: SEVER the supply edge and the ENTIRE downstream
    cascade + affect flip + society move VANISH -- no owe, no default, no affect flip,
    no badmouth, backing unchanged. Proves every consequence FLOWS the dependency graph;
    nothing is authored."""
    c = run.demo_cascade(sever=True)["up_chain"]
    assert c["owe_minted"] == [] and c["doreen_defaulted"] == 0
    assert c["fisherman_arousal"][1] == c["fisherman_arousal"][0]     # affect unchanged
    assert c["fisherman_demand_cash"] == 0 and c["doreen_badmouthed"] == 0
    assert c["n_badmouth_nodes"] == 0 and c["post_backs"] == [1, 1, 1]


# ============================================ register-distinctness (source-audit)
def test_reputation_rule_is_credibility_not_enforcement():
    """The R5 badmouth->credibility move is the 245 REPUTATION register (standing vs
    testimony), NOT the 247 enforcement/censure register -- the reputation seed touches
    no law/censure machinery (two registers stay distinct, source-audited)."""
    rep = json.load(open(os.path.join(_ROOT, "seeds", "bigville_loop_reputation.json")))
    names = [r["name"] for r in rep["rules"]]
    assert "bl_badmouth" in names and "bl_townsfolk_opinion" in names
    blob = json.dumps(rep["rules"])
    for censure_word in ("censure", "enforce", "Violation", "arrest", "sentence"):
        assert censure_word not in blob, f"reputation leaks into the law register: {censure_word}"


def test_no_python_agent_decision_in_the_loop_adapter():
    """Source-audit: the loop adapter holds NO agent decision -- no Python rule engine
    and no if/else over an agent's graph valuation that selects an agent ACTION. Every
    such decision is a seed rule; the adapter only ingests, arms, ticks, and reads."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_loop_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "._match(", "._apply(", "make_rule("):
        assert forbidden not in src, f"loop adapter runs the Python rule engine: {forbidden}"
    # the reputation seed rules exist and drive the decisions (not Python)
    rep = json.load(open(os.path.join(_ROOT, "seeds", "bigville_loop_reputation.json")))
    assert len(rep["rules"]) == 2


def test_runners_dsl_untouched_zero_new_rust():
    """No new Rust: the R5 build is seeds + adapter + tests only. The reputation seed
    composes existing DSL Terms; no term.rs / engine change."""
    import subprocess
    r = subprocess.run(["git", "diff", "--name-only",
                        "1450c77a80d44789ece12d901a24f8d96d14e7c4", "--", "runners/dsl"],
                       cwd=_ROOT, capture_output=True, text=True)
    changed = [l for l in r.stdout.splitlines() if l.strip()]
    assert changed == [], f"runners/dsl changed (new Rust): {changed}"
