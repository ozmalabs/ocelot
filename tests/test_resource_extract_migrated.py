"""bigville production-economy R1 (block 300000): the natural-resource base +
extraction. Fish/lumber/stone deposits with Sugarscape growback; a labourer walks
to a deposit, extracts, delivers to a store. Gates mirror BIGVILLE_RESOURCE_PREREG.md.
ANTI-TUNING: rates are set; the balance (steady vs depletion) is what falls out.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_resource_world import BigvilleResourceWorld    # noqa: E402

CELL = (2, 3)


def _world(kinds_cells):
    w = BigvilleResourceWorld()
    return w


# ------------------------------------------------------ G-extract-delivers + conserve
def test_extract_delivers_and_conserves_material():
    """A labourer extracts from the deposit and delivers to the store; with growback
    OFF (no source) the total material (deposit + carried + store) stays constant and
    the deposit never goes negative -- extraction/delivery move material, never mint it."""
    w = BigvilleResourceWorld()
    w.add_deposit("fish", CELL, stock=30.0, growback=0.0, capacity=100.0)
    w.add_store(CELL, ["fish", "lumber", "stone"])
    names = ["a", "b", "c", "d"]
    for n in names:
        w.add_labourer(n, CELL, dep_kind="fish", yield_=3.0)
    min_dep = 30.0
    for _ in range(40):
        w.step()
        total = (w.deposit_stock("fish") + sum(w.carrying(n) for n in names)
                 + w.store_stock("fish"))
        assert abs(total - 30.0) < 1e-6, f"material not conserved: {total}"
        min_dep = min(min_dep, w.deposit_stock("fish"))
    assert min_dep >= -1e-9, f"deposit went negative: {min_dep}"
    assert w.store_stock("fish") > 0, "nothing was ever delivered"
    w.close()


# ------------------------------------------------------ G-growback-regenerates
def test_growback_regenerates_and_caps():
    """With no labourers a drawn-down deposit refills toward capacity at growback/epoch
    and stops at capacity (never exceeds)."""
    w = BigvilleResourceWorld()
    w.add_deposit("fish", CELL, stock=20.0, growback=3.0, capacity=100.0)
    w.add_store(CELL, ["fish"])
    for _ in range(40):
        w.step()
    assert w.deposit_stock("fish") == 100.0, w.deposit_stock("fish")
    # one more run must NOT exceed capacity
    w.step()
    assert w.deposit_stock("fish") == 100.0, "growback exceeded capacity"
    w.close()


# ------------------------------------------------------ G-sustainable-steady (headline)
def test_sustainable_rate_reaches_bounded_steady_state():
    """extraction <= growback -> the deposit stays bounded ABOVE zero (steady), not
    trending to depletion. Measured, not tuned."""
    w = BigvilleResourceWorld()
    w.add_deposit("fish", CELL, stock=50.0, growback=3.0, capacity=100.0)
    w.add_store(CELL, ["fish"])
    w.add_labourer("l0", CELL, dep_kind="fish", yield_=2.0)   # ~1 unit/tick << gb 3
    for _ in range(50):
        w.step()
    assert w.deposit_stock("fish") > 20.0, (
        "a sustainable rate depleted the deposit: %.1f" % w.deposit_stock("fish"))
    w.close()


# ------------------------------------------------------ G-overextraction-depletes
def test_overextraction_depletes_to_floor():
    """extraction >> growback -> the deposit trends to 0 and floors there (extraction
    stalls: nothing left to take). The balance is a REAL constraint."""
    w = BigvilleResourceWorld()
    w.add_deposit("fish", CELL, stock=60.0, growback=2.0, capacity=100.0)
    w.add_store(CELL, ["fish"])
    for i in range(4):
        w.add_labourer("l%d" % i, CELL, dep_kind="fish", yield_=3.0)  # ~6/tick >> gb 2
    for _ in range(50):
        w.step()
        assert w.deposit_stock("fish") >= -1e-9, "deposit went negative"
    assert w.deposit_stock("fish") < 10.0, (
        "over-extraction did not deplete: %.1f" % w.deposit_stock("fish"))
    w.close()


# ------------------------------------------------------ G-per-kind
def test_material_flows_to_its_own_kind_bucket():
    """fish / lumber / stone flow to their own Stock buckets; a fish labourer never
    fills the lumber stock (kind-matched delivery)."""
    w = BigvilleResourceWorld()
    w.add_deposit("fish", (2, 3), stock=40.0, growback=0.0, capacity=100.0)
    w.add_deposit("lumber", (5, 0), stock=40.0, growback=0.0, capacity=100.0)
    w.add_deposit("stone", (0, 0), stock=40.0, growback=0.0, capacity=100.0)
    w.add_store((2, 3), ["fish", "lumber", "stone"])
    w.add_labourer("f", (2, 3), dep_kind="fish", yield_=2.0)
    w.add_labourer("w", (5, 0), dep_kind="lumber", yield_=2.0)
    w.add_labourer("s", (0, 0), dep_kind="stone", yield_=2.0)
    for _ in range(60):
        w.step()
    for k in ("fish", "lumber", "stone"):
        assert w.store_stock(k) > 0, f"{k} never delivered"
        assert w.deposit_stock(k) < 40.0, f"{k} deposit never drawn"
    # cross-check conservation per kind (growback 0): store + deposit + carried == 40
    for k, nm in (("fish", "f"), ("lumber", "w"), ("stone", "s")):
        tot = w.store_stock(k) + w.deposit_stock(k) + w.carrying(nm)
        assert abs(tot - 40.0) < 1e-6, f"{k} not conserved: {tot}"
    w.close()


# ------------------------------------------------------ G-no-python-decision
def test_no_python_decides_extraction():
    src = open(os.path.join(_ROOT, "worlds", "bigville_resource_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    import json
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_resource_extract.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"rx_growback", "rx_extract", "rx_deliver"} <= names, names
