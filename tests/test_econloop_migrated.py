"""bigville production-economy R5 (block 304000): the closed self-balancing loop,
on the real 100-resident cast. Resource supply + emergent price (R3) + labour
mobility (R4) composed into one loop. Gates mirror BIGVILLE_ECONLOOP_PREREG.md.
ANTI-TUNING: params are set; stability / self-balance / shock-response fall out.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_economy_world import BigvilleEconomyWorld     # noqa: E402

TRADES = ("fishing", "foresting", "quarrying")


def _town(crowd=0.1, demand=18.0):
    w = BigvilleEconomyWorld(friction_scale=6.0)
    for t in TRADES:
        w.add_trade(t, stock=200.0, growback=30.0, capacity=200.0, yield_=1.0,
                    demand=demand, price=8.0, price_step=0.5, min_price=1.0, crowd=crowd)
    w.load_cast_labour()
    return w


def _spread(w):
    return max(w.wage(t) for t in TRADES) - min(w.wage(t) for t in TRADES)


# ------------------------------------------------------ G-stable-equilibrium (headline)
def test_loop_converges_to_bounded_steady_state():
    w = _town()
    hist = []
    for _ in range(40):
        w.tick()
        hist.append(tuple(w.n_in(t) for t in TRADES))
    tail = hist[-8:]
    spread = max(max(h[i] for h in tail) - min(h[i] for h in tail) for i in range(3))
    # bounded small jitter (integer moves between near-equal-wage trades), NOT the
    # herd oscillation (>=10 swings) the crowd=0 falsifier produces.
    assert spread <= 6, f"headcounts did not settle (last-8 spread {spread})"
    assert _spread(w) <= 2.0, f"wages did not equalize: spread {_spread(w):.2f}"
    w.close() if hasattr(w, "close") else None


# ------------------------------------------------------ G-self-balances
def test_unbalanced_labour_self_balances():
    """The cast starts many workers in fishing and few in quarrying; the loop moves
    labour off the crowded trade toward the under-worked ones."""
    w = _town()
    start = {t: w.n_in(t) for t in TRADES}
    w.run(40)
    end = {t: w.n_in(t) for t in TRADES}
    # the most-crowded trade sheds workers; the least-crowded gains.
    most = max(start, key=start.get)
    least = min(start, key=start.get)
    assert end[most] < start[most], f"{most} did not shed labour: {start}->{end}"
    assert end[least] > start[least], f"{least} did not gain labour: {start}->{end}"
    w.close() if hasattr(w, "close") else None


# ------------------------------------------------------ G-shock-response (headline)
def test_resource_shock_raises_price_and_pulls_labour():
    """Collapse the fishing resource at equilibrium -> fishing scarce -> price RISES
    and labour FLOWS IN. The closed loop responds to a perturbation."""
    w = _town()
    w.run(40)
    p0, n0 = w.price("fishing"), w.n_in("fishing")
    w.eng.set_attr(w._deps["fishing"], "stock", 0.0)
    w.eng.set_attr(w._deps["fishing"], "growback", 3.0)   # scarce henceforth
    w.run(25)
    assert w.price("fishing") > p0, f"fish price did not rise on the shock: {p0}->{w.price('fishing')}"
    assert w.n_in("fishing") >= n0, f"labour did not flow toward the scarce trade: {n0}->{w.n_in('fishing')}"
    w.close() if hasattr(w, "close") else None


# ------------------------------------------------------ G-material-bounded
def test_material_stays_physical():
    w = _town()
    for _ in range(40):
        w.tick()
        for t in TRADES:
            s = w.deposit_stock(t)
            assert -1e-9 <= s <= 200.0 + 1e-9, f"{t} stock out of [0,cap]: {s}"
    w.close() if hasattr(w, "close") else None


# ------------------------------------------------------ G-crowd-is-load-bearing (falsifier)
def test_without_crowd_damper_the_loop_oscillates():
    """crowd=0 -> the mobile pool herds to one trade each tick and OSCILLATES
    (large headcount swings). Proves the crowding term is what makes it converge."""
    w = _town(crowd=0.0)
    hist = []
    for _ in range(40):
        w.tick()
        hist.append(tuple(w.n_in(t) for t in TRADES))
    tail = hist[-10:]
    spread = max(max(h[i] for h in tail) - min(h[i] for h in tail) for i in range(3))
    assert spread >= 10, f"crowd=0 unexpectedly stable (spread {spread}); the falsifier is vacuous"
    w.close() if hasattr(w, "close") else None


# ------------------------------------------------------ G-no-python-decision
def test_no_python_decides_the_economy():
    src = open(os.path.join(_ROOT, "worlds", "bigville_economy_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    assert "remove_edge" not in src, "adapter moves the works_as edge (the switch must be the rule)"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econloop.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"ec_extract", "ec_price_glut", "ec_price_scarce", "ec_wage", "ec_switch"} <= names, names
