"""R10e (block 276000) gate: the SCALE-TO-50 town boots, the 50-register has 50 distinct
named residents drawn from the generative model (not clones), and conservation holds on a
short run. The full genuine-dynamics / cost measurement is the 1800-tick run (not a test).
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def test_register_50_has_50_distinct_residents_not_clones():
    p = os.path.join(_ROOT, "seeds", "bigville_townspeople_50.json")
    d = json.load(open(p))
    inh = d["inhabitants"]
    assert len(inh) == 50
    names = [i["name"] for i in inh]
    assert len(set(names)) == 50, "register has duplicate names"
    cw = [i["params"]["charm_weight"] for i in inh]
    assert len(set(round(x, 6) for x in cw)) > 40, "params look cloned (zero variance tell)"


def test_scale50_boots_and_conserves():
    from worlds.bigville_integ5_world import BigvilleInteg5World
    w = BigvilleInteg5World(cast=50, seed=276000)
    assert w.living_count() == 50
    s0 = w.system_coin()
    for _ in range(30):
        w.integ_step()
    assert abs(w.system_coin() - s0) < 1e-6, "Sigma(coin) not invariant at cast=50"
    # named cast: real register names assigned (no bare v## for the seeded residents)
    named = sum(1 for nm in w.people if w.display.get(nm, nm) and not w.display.get(nm, "").startswith("v"))
    assert named >= 45
