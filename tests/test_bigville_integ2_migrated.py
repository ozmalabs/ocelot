"""R10b (block 273000) gate -- the BALANCE FIX. Fast, short-run assertions that the two
diagnosed defects are FIXED as correctness (no coefficient tuned to a regime):

  DEFECT 1  -- Sigma(coin) is INVARIANT across a run (conserving WagePool double-entry).
  PRIORITY 2 -- the demographic timescale is realistic: a healthy normal-age adult does
                NOT die over a short run; only genuine elders are near end-of-life.
  PRIORITY 3 -- the renewal path is wired (fertility decided by the graph; a new death
                triggers a replacement birth); births counted as structural activity.
  + the town-state contract (named cast, deep held, real/null journal, coherent map),
    the source audit (no agent decision in the adapter), and a clean seed load.

These run a SHORT horizon (deaths start ~day 27 = ~972 ticks, too long for a unit test),
so the death/renewal LOOP itself is exercised by a direct injected-death probe rather
than a full demographic run (the full run is the RESULTS measurement).
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def world():
    from worlds.bigville_integ2_world import BigvilleInteg2World
    return BigvilleInteg2World(cast=16, seed=273000)


# ------------------------------------------------------------ DEFECT 1: conserve
def test_conserving_seed_loads_all_rules():
    from substrate.seed_loader import manifest_for
    m = manifest_for("bigville_integ2_conserve")
    names = {r["name"] for r in m.get("rules", [])}
    assert {"bi2_work_sink", "bi2_withdraw_source", "bi2_drink_source",
            "bi2_snap_source", "bi2_outcome_idle"} <= names


def test_sigma_coin_invariant_over_a_run():
    from worlds.bigville_integ2_world import BigvilleInteg2World, TICKS_PER_DAY
    w = BigvilleInteg2World(cast=16, seed=273000)
    s0 = w.system_coin()
    for _ in range(TICKS_PER_DAY + 6):         # span > 1 day so the wage cycle fires
        w.integ_step()
    s1 = w.system_coin()
    # the WHOLE-system coin (every coin attr + reserves + pool) is invariant.
    assert abs(s1 - s0) < 1e-6, "coin leaked: %.6f -> %.6f" % (s0, s1)
    # the pool went negative -- it ABSORBED the wage debits (the sink R10 lacked).
    assert w.pool_coin() < 0.0


def test_wagepool_exists(world):
    assert world.eng.node(world._pool)["attrs"] is not None
    assert world.pool_coin() <= 0.0            # a ledger account (0 at t0)


# ------------------------------------------------------------ PRIORITY 2: timescale
def test_healthy_adult_does_not_die_in_weeks(world):
    """The acceptance bar, checked on the calibrated timescale (fast/static): every
    non-elder resident's lifespan is MANY weeks, so a healthy normal-age adult cannot
    die of routine aging over a span of weeks (base death rate ~0)."""
    for nm, days in world.lifespan_after_days.items():
        if nm in world.elders:
            continue
        assert days >= 28.0, \
            "%s (non-elder) would die of aging in %.1f days (< 4 weeks)" % (nm, days)


def test_lifespans_are_many_days_and_longer_than_r10(world):
    # a normal adult lives many days; every R10b lifespan exceeds its R10 value.
    assert world.lifespan_after_days
    assert min(world.lifespan_after_days.values()) >= 20.0    # even elders: many days
    assert max(world.lifespan_after_days.values()) >= 60.0    # adults: a long life
    for nm in world.lifespan_after:
        assert world.lifespan_after[nm] >= world.lifespan_before[nm]  # strictly slower


def test_genuine_elder_cohort_present(world):
    from worlds.bigville_integ2_world import N_GENUINE_ELDERS
    assert len(world.elders) == N_GENUINE_ELDERS
    for e in world.elders:                      # elders are near end-of-life
        assert world.age_of(e) >= 80.0


# ------------------------------------------------------------ PRIORITY 3: renewal
def test_death_triggers_a_replacement_birth():
    """A death triggers exactly one replacement (graph fertility decides willingness),
    added to the living cast. `_renew(dead_before)` is exactly what integ_step calls;
    `dead_before` is the pre-death snapshot, so the killed resident reads as a NEW
    death (the renewal trigger)."""
    from worlds.bigville_integ2_world import BigvilleInteg2World
    w = BigvilleInteg2World(cast=16, seed=273000)
    victim = next(nm for nm in w.people if not w.is_dead(nm))
    n_people0 = len(w.people)
    dead_before = set(nm for nm in w.people if w.is_dead(nm))   # pre-death snapshot
    w.die(victim, cause=2.0)                    # a real R14 death (health->0)
    births = w._renew(dead_before)              # what integ_step runs after the tick
    assert w.is_dead(victim)
    assert births == 1, "no replacement birth for the death"
    assert len(w.people) == n_people0 + 1
    # the death was logged with a cause + age (acceptance evidence).
    assert any(d["id"] == victim for d in w.death_log)


def test_birth_is_conserving_and_fully_endowed():
    from worlds.bigville_integ2_world import BigvilleInteg2World
    w = BigvilleInteg2World(cast=16, seed=273000)
    s0 = w.system_coin()
    victim = next(nm for nm in w.people if not w.is_dead(nm))
    dead_before = set(nm for nm in w.people if w.is_dead(nm))
    w.die(victim, cause=2.0)
    w._renew(dead_before)
    child = w.births[-1]["child"]
    assert w.coin_of(child) == 0.0              # newborn holds nothing (no creation)
    assert child in w._fert2                    # can itself reproduce
    assert child in w._life                     # has health/aging
    assert abs(w.system_coin() - s0) < 1e-6     # birth conserves coin


# ------------------------------------------------------------ presentation contract
def test_named_cast_no_generic_names(world):
    for nm in world.people:
        disp = world.display.get(nm)
        assert disp and not disp.startswith("v0"), "generic name survived: %r" % disp
    bk = world._banker
    assert world.display.get(bk) == "Scrooge"


def test_deep_held_is_real_graph_state_and_journal_null(world):
    from worlds.bigville_integ2_state import export_townstate2
    st = export_townstate2(world)
    banker = [v for v in st["villagers"] if v["role"] == "banker"][0]
    assert banker["held"] != "bank"             # the R10 hardcode is gone
    assert banker["held"] is None or "reserves=" in banker["held"] \
        or "rate_bp=" in banker["held"]         # real bank state
    for v in st["villagers"]:
        # journal is a real read -> null when the nightly-journal faculty is dormant.
        assert v["journal"] is None or isinstance(v["journal"], str)


def test_townstate_contract_shape(world):
    from worlds.bigville_integ2_state import (
        export_townstate2, CONTRACT2_TOP_KEYS, CONTRACT2_MAP_KEYS,
        CONTRACT2_VILLAGER_KEYS)
    st = export_townstate2(world)
    assert CONTRACT2_TOP_KEYS <= set(st)
    assert CONTRACT2_MAP_KEYS <= set(st["map"])
    assert st["map"]["features"] and all(
        {"type", "x", "y"} <= set(f) for f in st["map"]["features"])
    for v in st["villagers"]:
        assert CONTRACT2_VILLAGER_KEYS <= set(v)


def test_no_agent_decision_in_adapter():
    """Source audit: the integ2 world/state make no agent decision -- no Python rule
    engine, no gr.make_rule/run. Decisions are seed rules; Python ingests/ticks/reads."""
    for fn in ("worlds/bigville_integ2_world.py", "worlds/bigville_integ2_state.py"):
        src = open(os.path.join(_ROOT, fn)).read()
        for forbidden in ("graph_rewrite.run", "gr.make_rule", "gr._match",
                          "gr._apply", ".run_python_rules("):
            assert forbidden not in src, "%s calls %s" % (fn, forbidden)
