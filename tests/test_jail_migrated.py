"""bigville R26 (block 314000): the jail -- custodial sentences. A guilty charge
with a prescribed jail_term imprisons the defendant; the term counts down as days
advance; the inmate serves the full term then is released. Gates mirror
BIGVILLE_JAIL_PREREG.md. Imprison/serve/release are seed rules (jl_*).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_jail_world import BigvilleJailWorld   # noqa: E402

# A punitive-leaning bench that convicts a low-standing defendant (from the court).
_BENCH = [
    ("H1", dict(bloc="rich", credence=1.5, punitiveness=1.5, deference=0.5)),
    ("H2", dict(bloc="rich", credence=1.5, punitiveness=1.0, deference=0.5)),
    ("H3", dict(bloc="poor", credence=1.2, punitiveness=0.8, deference=0.5)),
    ("L1", dict(bloc="poor", credence=0.5, punitiveness=-1.0, deference=0.5)),
    ("L2", dict(bloc="poor", credence=0.4, punitiveness=-1.5, deference=0.5)),
]


def _jail(bench=_BENCH):
    w = BigvilleJailWorld()
    for n, d in bench:
        w.add_councillor(n, **d)
    w.add_constable("Dogberry")
    return w


# ------------------------------------------------------ G-custodial-imprisons (headline)
def test_guilty_custodial_charge_imprisons():
    w = _jail()
    w.add_resident("Felon", coin=30.0, standing=0.0)
    ch = w.prosecute("Felon", "highway robbery", evidence=1.0, penalty=6.0,
                     threshold=3, jail_term=3.0)
    w.run()
    assert w.verdict(ch) == "guilty"
    assert w.is_imprisoned("Felon"), "a custodial guilty verdict should imprison"
    assert w.remaining("Felon") == 3, w.remaining("Felon")
    assert w.jail_roll() == ["Felon"], w.jail_roll()
    # the fine still applied too (custody + fine are independent).
    assert abs(w.coin_of("Felon") - 24.0) < 1e-9, "the fine still applies alongside custody"


# ------------------------------------------------------ G-term-counts-down-and-releases (headline)
def test_term_counts_down_and_releases():
    w = _jail()
    w.add_resident("Felon", coin=30.0, standing=0.0)
    w.prosecute("Felon", "highway robbery", evidence=1.0, threshold=3, jail_term=3.0)
    w.run()
    for expected in (2, 1, 0):
        w.advance_day()
        assert w.remaining("Felon") == expected, f"remaining {w.remaining('Felon')} != {expected}"
    assert not w.is_imprisoned("Felon"), "the inmate should be released at term end"
    assert w.jail_roll() == [], "the jail roll should be empty after release"


# ------------------------------------------------------ G-serves-the-full-term
def test_serves_the_full_term_no_early_release():
    w = _jail()
    w.add_resident("Felon", coin=30.0, standing=0.0)
    w.prosecute("Felon", "arson", evidence=1.0, threshold=3, jail_term=3.0)
    w.run()
    w.advance_day(); w.advance_day()          # 2 of 3 days
    assert w.is_imprisoned("Felon"), "must not be released before the full term"
    assert w.remaining("Felon") == 1
    w.advance_day()                           # 3rd day
    assert not w.is_imprisoned("Felon"), "released on the final day, not before/after"


# ------------------------------------------------------ G-fine-only-does-not-jail
def test_fine_only_charge_does_not_imprison():
    w = _jail()
    w.add_resident("Petty", coin=30.0, standing=0.0)
    ch = w.prosecute("Petty", "scrumping apples", evidence=1.0, penalty=4.0,
                     threshold=3, jail_term=0.0)
    w.run()
    assert w.verdict(ch) == "guilty"
    assert not w.is_imprisoned("Petty"), "a fine-only charge must not jail"
    assert w.jail_roll() == [], "no custodial term -> empty jail"
    assert abs(w.coin_of("Petty") - 26.0) < 1e-9, "but the fine still applies"


# ------------------------------------------------------ G-acquitted-not-jailed (falsifier)
def test_acquitted_defendant_is_never_jailed():
    w = _jail()
    w.add_resident("Esteemed", coin=30.0, standing=8.0)   # deference shields -> acquittal
    ch = w.prosecute("Esteemed", "highway robbery", evidence=1.0, threshold=3, jail_term=5.0)
    w.run()
    assert w.verdict(ch) == "acquitted"
    assert not w.is_imprisoned("Esteemed"), "an acquittal must never imprison"
    assert w.jail_roll() == []
    # advancing days changes nothing for a free person.
    w.advance_day()
    assert not w.is_imprisoned("Esteemed")


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_custody():
    src = open(os.path.join(_ROOT, "worlds", "bigville_jail_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_jail.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"jl_imprison", "jl_serve_day", "jl_release"} <= names, names


# ------------------------------------------------------ G-day-advances-on-the-bell (block 321000)
def test_the_day_advances_only_when_the_curfew_bell_tolls():
    """The jail term counts down because the CURFEW BELL tolls the day -- not a forced
    counter. With no bell, no day passes; there is no `advancing` flag on the town."""
    w = _jail()
    w.add_resident("Felon", coin=30.0, standing=0.0)
    w.prosecute("Felon", "robbery", evidence=1.0, threshold=3, jail_term=3.0)
    w.run()
    assert w.remaining("Felon") == 3
    # run the fixpoint WITHOUT tolling the bell -> no day passes.
    for _ in range(3):
        w.run()
    assert w.remaining("Felon") == 3, "the day must not advance without the bell"
    # the town holds no forced day clock.
    assert "advancing" not in w.eng.node(w._town)["attrs"], "no forced `advancing` flag on the town"
    # toll the curfew bell -> exactly one day passes per toll.
    w.toll_curfew()
    assert w.remaining("Felon") == 2, "one curfew toll -> one day served"
