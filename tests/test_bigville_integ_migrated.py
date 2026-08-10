"""R10 (block 258000) gates -- the PUNCTUATED-EQUILIBRIUM validity gate + the
town-state export contract. The harness ASSEMBLES the town and measures whether it
LIVES; these gates prove the HARNESS + the INSTRUMENT + the CONTRACT are sound (the
macro VERDICT itself is a measured finding, recorded in BIGVILLE_INTEG_RESULTS.md,
not asserted here -- a gate must not pin a result the rung is meant to discover).

Fast by construction: a small cast + short run for the boot/contract gates; the
classifier is gated on SYNTHETIC series (deterministic, no engine) so the instrument
is proven to distinguish the regimes.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.bigville_integ_measure import classify_regime            # noqa: E402
from worlds import bigville_integ_state as st                         # noqa: E402


# ----------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def town():
    from worlds.bigville_integ_world import BigvilleIntegWorld
    w = BigvilleIntegWorld(cast=6, seed=258000)
    w.run_town(T=12)
    return w


# ================================================================ ASSEMBLY
def test_assembles_core_and_siblings_without_forcing_conflict(town):
    # the deep MRO chain assembles the core rungs by construction...
    assert len(town.core_rungs) >= 25
    # ...and the sibling-branch seeds additively load into the SAME engine.
    assert len(town.assembled) >= 15, town.assembled
    # any conflict is DOCUMENTED, never forced (the list is the record).
    assert isinstance(town.conflicts, list)


def test_town_is_populated(town):
    assert len(town.people) == 6
    assert town._bank is not None
    assert town.total_plots() >= 6
    assert len(town._shops) >= 1


# ================================================================ MACRO SERIES
def test_macro_series_has_the_right_shape(town):
    assert len(town.macro) == 12
    for m in town.macro:
        assert set(("tick", "activity", "cost")).issubset(m)
        assert isinstance(m["activity"], int) and m["activity"] >= 0
        assert isinstance(m["cost"], int) and m["cost"] >= 0
    # cost is compute-proportional-to-surprise: a live town does real work each tick.
    assert sum(m["cost"] for m in town.macro) > 0


def test_no_scheduled_shocks_source_audit():
    """G-endogenous: the harness injects NO exogenous scheduled event, and holds NO
    agent decision (no Python rule engine, no if/else over agent valuations driving a
    graph mutation). A source audit of the world adapter."""
    path = os.path.join(_ROOT, "worlds", "bigville_integ_world.py")
    src = open(path).read()
    for forbidden in ("graph_rewrite.run", "gr.run(", "._match(", "._apply(",
                      "make_rule(", "import random", "time.time()", "wall_clock"):
        assert forbidden not in src, "forbidden pattern in harness: %r" % forbidden
    # no scheduled-shock keyword pattern (a tick-indexed injected catastrophe).
    assert "if self.world_epoch ==" not in src


def test_run_town_classifies_to_an_enumerated_regime(town):
    verdict, ev = classify_regime(town.macro, exploded=town.exploded)
    assert verdict in ("EXPLODED", "FROZEN", "DEAD_FIXPOINT", "CLEAN_PERIODIC",
                       "PUNCTUATED_EQUILIBRIUM", "WHITE_NOISE", "SMOOTH",
                       "PUNCTUATED_WEAK", "UNRESOLVED", "NO_DATA")
    assert ev["ticks"] == 12


# ================================================================ THE INSTRUMENT
# The classifier must DISTINGUISH the regimes -- proven on synthetic series so the
# verdict on the real town is trustworthy (an instrument you can trust to call an
# explosion an explosion and a dead fixpoint a dead fixpoint).
def _series(acts, costs=None):
    costs = costs if costs is not None else [10] * len(acts)
    return [dict(tick=i + 1, activity=a, cost=c) for i, (a, c) in enumerate(zip(acts, costs))]


def test_instrument_detects_explosion_from_harness_flag():
    v, _ = classify_regime(_series([1] * 50),
                           exploded=dict(coupling="node-count runaway", detail="x"))
    assert v == "EXPLODED"


def test_instrument_detects_explosion_from_rising_load():
    acts = [1] * 40 + [int(2 ** (i / 3.0)) for i in range(20)]
    costs = [10] * 40 + [10 * int(2 ** (i / 3.0)) for i in range(20)]
    v, _ = classify_regime(_series(acts, costs))
    assert v == "EXPLODED"


def test_instrument_detects_frozen():
    v, _ = classify_regime(_series([0] * 60))
    assert v == "FROZEN"


def test_instrument_detects_dead_fixpoint():
    acts = [3, 5, 4, 6, 2] + [0] * 55       # active then dead tail
    v, _ = classify_regime(_series(acts))
    assert v == "DEAD_FIXPOINT"


def test_instrument_detects_punctuated_equilibrium():
    # long quiet dwells of IRREGULAR length punctuated by rare heavy bursts of
    # VARYING size, cost spiking AT the bursts -- the real SOC signature (NOT a clean
    # period; an irregular one would be mis-called CLEAN_PERIODIC, correctly).
    gaps = [22, 9, 31, 14, 40, 7, 25, 12, 18, 33]   # irregular dwell times
    sizes = [4, 3, 60, 5, 2, 6, 3, 80, 4, 3]        # heavy-tailed: mostly tiny, rare huge
    acts, costs = [], []
    for g, sz in zip(gaps, sizes):
        acts += [0] * g
        costs += [10] * g
        acts += [sz]
        costs += [10 + 5 * sz]                # cost punctuates with the cascade
    v, ev = classify_regime(_series(acts, costs))
    assert v == "PUNCTUATED_EQUILIBRIUM", (v, ev)


def test_instrument_detects_smooth():
    acts = [10 + (i % 2) for i in range(60)]   # near-constant, tiny wobble
    v, _ = classify_regime(_series(acts))
    assert v in ("SMOOTH", "CLEAN_PERIODIC")   # very low variation / regular


# ================================================================ THE CONTRACT
def test_townstate_matches_the_exact_contract_shape(town):
    s = st.export_townstate(town)
    assert set(s) == st.CONTRACT_TOP_KEYS, set(s) ^ st.CONTRACT_TOP_KEYS
    assert isinstance(s["day"], int) and isinstance(s["tick"], int)
    assert s["phase"] in ("dawn", "day", "dusk", "night")
    # map
    assert set(s["map"]) == st.CONTRACT_MAP_KEYS
    assert isinstance(s["map"]["tiles"], list) and isinstance(s["map"]["tiles"][0], list)
    assert isinstance(s["map"]["tiles"][0][0], str)
    assert isinstance(s["map"]["buildings"], list) and s["map"]["buildings"]
    b = s["map"]["buildings"][0]
    assert set(("id", "type", "x", "y", "w", "h", "owner", "name")).issubset(b)
    # villagers
    assert s["villagers"]
    for v in s["villagers"]:
        assert set(v) == st.CONTRACT_VILLAGER_KEYS, set(v) ^ st.CONTRACT_VILLAGER_KEYS
        assert isinstance(v["alive"], bool)
        assert v["cls"] in ("rich", "middle", "poor")
        assert isinstance(v["rel"], list)
    # institutions
    assert set(s["institutions"]) == st.CONTRACT_INSTITUTION_KEYS
    assert set(("reserves", "rate_bp")).issubset(s["institutions"]["bank"])
    assert set(("treasury", "tax_bp", "captured")).issubset(s["institutions"]["council"])
    # metrics
    assert set(s["metrics"]) == st.CONTRACT_METRIC_KEYS
    for k in ("gini_wealth", "gini_land"):
        assert isinstance(s["metrics"][k], float)
    # levers
    assert set(s["levers"]) == st.CONTRACT_LEVER_KEYS
    for k in st.CONTRACT_LEVER_KEYS:
        assert isinstance(s["levers"][k], bool)
    # events + macro
    for e in s["events"]:
        assert set(("tick", "kind", "actors", "text")).issubset(e)
    for m in s["macro"]:
        assert set(m) == set(("tick", "activity", "cost"))


def test_townstate_snapshot_is_emitted(tmp_path):
    from worlds.bigville_integ_world import BigvilleIntegWorld
    w = BigvilleIntegWorld(cast=6, seed=258000)
    w.run_town(T=6)
    p = tmp_path / "townstate.json"
    st.write_snapshot(w, str(p))
    assert p.exists()
    import json
    got = json.loads(p.read_text())
    assert set(got) == st.CONTRACT_TOP_KEYS
