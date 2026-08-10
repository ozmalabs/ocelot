"""bigville production-economy R3 (block 302000): emergent scarcity prices.
Scarce good -> higher price, glut -> lower price, from local supply/demand
imbalance -- not hand-set. Gates mirror BIGVILLE_PRICES_PREREG.md.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_price_world import BigvillePriceWorld        # noqa: E402


def _scarcity(T=30):
    """demand >> supply: 6 customers, one slow supplier."""
    w = BigvillePriceWorld()
    w.add_shop("fishmonger", (0, 0), input_kind="fish", output_kind="fish_ready",
               price=3.0, price_step=0.5, glut_threshold=8.0)
    w.add_deposit("fish", (2, 3), stock=100.0, growback=1.0, capacity=100.0)
    w.add_supplier("finn", (2, 3), dep_kind="fish", to_trade="fishmonger", yield_=1.0)
    for i in range(6):
        w.add_customer("c%d" % i, "fishmonger", coin=1000.0)
    traj = [w.price("fishmonger")]
    for _ in range(T):
        w.step()
        traj.append(w.price("fishmonger"))
    return w, traj


# ------------------------------------------------------ G-scarcity-raises (headline)
def test_scarcity_raises_price():
    w, traj = _scarcity()
    assert traj[-1] > traj[0], f"scarcity did not raise the price: {traj[0]} -> {traj[-1]}"
    w.close()


# ------------------------------------------------------ G-bounded (settles)
def test_scarcity_price_plateaus_not_diverges():
    """The price climbs then PLATEAUS (finds a clearing level); it does not run
    away -- the last few ticks are stable."""
    w, traj = _scarcity(T=40)
    tail = traj[-5:]
    assert max(tail) - min(tail) <= 1.0, f"price did not settle: tail {tail}"
    assert traj[-1] > traj[0]
    w.close()


# ------------------------------------------------------ G-glut-lowers
def test_glut_lowers_price_to_floor():
    """supply >> demand: output piles -> price falls, floored at min_price."""
    w = BigvillePriceWorld()
    w.add_shop("fishmonger", (0, 0), input_kind="fish", output_kind="fish_ready",
               price=6.0, min_price=1.0, price_step=0.5, glut_threshold=8.0)
    w.add_deposit("fish", (2, 3), stock=100.0, growback=6.0, capacity=100.0)
    for i in range(3):
        w.add_supplier("s%d" % i, (2, 3), dep_kind="fish", to_trade="fishmonger", yield_=3.0)
    w.add_customer("c0", "fishmonger", coin=1000.0)
    start = w.price("fishmonger")
    for _ in range(30):
        w.step()
        assert w.price("fishmonger") >= 1.0 - 1e-9, "price fell below min_price"
    assert w.price("fishmonger") < start, "glut did not lower the price"
    assert w.price("fishmonger") == 1.0, "price should floor at min_price under a glut"
    w.close()


# ------------------------------------------------------ G-price-emergent
def test_price_is_rule_emergent_not_python_set():
    src = open(os.path.join(_ROOT, "worlds", "bigville_price_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    # the adapter must not compute a price from demand -- only set rates/state.
    assert 'set_attr(shop, "price"' not in src, "adapter writes price after init (should be rules)"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_prices.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"pr_note_unmet", "pr_scarce_raise", "pr_glut_lower"} <= names, names
