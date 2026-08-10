"""bigville 100-resident cast + expanded map (blocks 305000-309000). Gates mirror
BIGVILLE_CAST100_PREREG.md, thresholds FIXED before measurement. The cast and map
are graph DATA (seed-builder work); NO agent decision logic is asserted absent.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import statistics as st
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_sim_world import build_town, SOLID                 # noqa: E402
from worlds.bigville_town100_world import (                             # noqa: E402
    build_town_100, generate_cast100, BigvilleTown100World, ROLE_SPEC,
    _PARAM_SPEC, W100, H100, SEED_DEFAULT)

_GROUP_OF = {role: grp for role, _, grp, *_ in ROLE_SPEC}


def _cast(seed=SEED_DEFAULT):
    _, _, layout = build_town_100(seed)
    return generate_cast100(layout, seed)["residents"], layout


# -------------------------------------------------------- G-count
def test_exactly_100_distinct_residents():
    cast, _ = _cast()
    assert len(cast) == 100, len(cast)
    names = [r["name"] for r in cast]
    assert len(set(names)) == 100, "names not distinct: %d unique" % len(set(names))


# -------------------------------------------------------- G-everyone-housed-and-employed
def test_everyone_housed_and_employed_and_reachable():
    w = BigvilleTown100World()
    try:
        recs = w.resident_records()
        assert len(recs) == 100
        for r in recs:
            assert r["home_cell"] and r["workplace_cell"]
            assert tuple(r["home_cell"]) in w._cell_at, "home not walkable: %s" % r["name"]
            assert tuple(r["workplace_cell"]) in w._cell_at, "work not walkable"
        # two arbitrary residents: a nav path exists home -> work
        for r in (recs[7], recs[63]):
            assert w.reachable(tuple(r["home_cell"]), tuple(r["workplace_cell"])), \
                "no path home->work for %s" % r["name"]
        # stronger: every home + workplace lies in ONE connected component
        anchor = tuple(recs[0]["home_cell"])
        for r in recs:
            assert w.reachable(anchor, tuple(r["home_cell"]))
            assert w.reachable(anchor, tuple(r["workplace_cell"]))
    finally:
        w.close()


# -------------------------------------------------------- G-role-identity-distribution
def test_role_identity_high_sticky_low_mobile_and_varied():
    cast, _ = _cast()
    high = [r["role_identity"] for r in cast if r["group"] == "high"]
    low = [r["role_identity"] for r in cast if r["group"] == "low"]
    assert st.mean(high) >= 0.80, "owners/tradesmen not sticky: %.3f" % st.mean(high)
    assert st.mean(low) <= 0.35, "labourers not mobile: %.3f" % st.mean(low)
    # NOT constant (drawn, not cloned)
    assert st.pvariance([r["role_identity"] for r in cast]) > 0.0
    assert st.pvariance(high) > 0.0 and st.pvariance(low) > 0.0


# -------------------------------------------------------- G-params-not-cloned
def test_drawn_params_have_variance():
    cast, _ = _cast()
    for k in _PARAM_SPEC:
        vs = [r["params"][k] for r in cast]
        assert st.pvariance(vs) > 0.0, "param %s is cloned (zero variance)" % k


# -------------------------------------------------------- G-job-mix-realistic
def test_job_mix_is_a_pyramid():
    cast, _ = _cast()
    hist = collections.Counter(r["role"] for r in cast)
    # labourer is the single plurality role
    top = hist.most_common(1)[0]
    assert top[0] == "labourer", "plurality role is %s not labourer" % top[0]
    assert top[1] > hist["farmer"] and top[1] > hist["farm_labourer"]
    # owners+tradesmen (high group) are a small minority, fewer than the labour base
    high = sum(1 for r in cast if r["group"] == "high")
    low = sum(1 for r in cast if r["group"] == "low")
    assert high <= 20, "owners+tradesmen not a minority: %d" % high
    assert high < low, "high group (%d) not < labour base (%d)" % (high, low)


# -------------------------------------------------------- G-resources-on-map
def test_resources_on_map_match_economy():
    w = BigvilleTown100World()
    try:
        grid, _, layout = build_town_100()
        assert set(layout["deposits"]) == {"fish", "lumber", "stone"}
        body = {"fish": 6, "lumber": 5, "stone": 2}   # WATER / TREE / WALL codes
        for kind, cell in layout["deposits"].items():
            cell = tuple(cell)
            assert cell in w._cell_at, "%s deposit not walkable" % kind
            assert w.deposit_stock(kind) > 0.0
            # orthogonally adjacent to its resource body
            x, y = cell
            adj = any(0 <= nx < W100 and 0 <= ny < H100 and grid[ny][nx] == body[kind]
                      for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
            assert adj, "%s deposit not beside its body" % kind
    finally:
        w.close()


# -------------------------------------------------------- G-deterministic
def test_same_seed_identical_cast_and_map():
    def digest(seed):
        g, _, l = build_town_100(seed)
        c = generate_cast100(l, seed)
        return hashlib.sha256(json.dumps({"g": g, "c": c}, sort_keys=True).encode()).hexdigest()
    assert digest(SEED_DEFAULT) == digest(SEED_DEFAULT)
    # committed seed file matches a fresh regeneration
    p = os.path.join(_ROOT, "seeds", "bigville_cast100.json")
    onfile = json.load(open(p))
    fresh = generate_cast100(build_town_100(SEED_DEFAULT)[2], SEED_DEFAULT)
    assert onfile == fresh, "committed seed drifted from the generator"


# -------------------------------------------------------- G-no-mutation
def test_build_town_byte_unchanged():
    g, a = build_town()
    assert len(g[0]) == 30 and len(g) == 18, "build_town dims changed"
    assert len(a) == 5
    h = hashlib.sha256(json.dumps(g).encode()).hexdigest()
    assert h == "0c7837e234cd40d08b69d7276a39dd0944c4d7fc77bad307fd69510b5c3be01a", \
        "build_town grid content mutated"


# -------------------------------------------------------- G-no-python-decision
def test_no_python_rule_engine_in_adapter():
    src = open(os.path.join(_ROOT, "worlds", "bigville_town100_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "._match", "._apply"):
        assert forbidden not in src, "adapter must not run a rule engine: %s" % forbidden
