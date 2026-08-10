"""Gate for the NAV FLOOD-FIELD CACHE (block 291000, worlds/bigville_move_world.py).

The map is STATIC, so a goal's BFS gdist field is valid for the whole run and every
mover heading there. The cache floods each goal ONCE and RESTORES it thereafter
(O(cells) writes) instead of re-running the Bellman-Ford flood (O(cells x passes))
every goal-switch -- a droppable, byte-identical perf mirror. NO Rust; NO seed.
"""
import pytest

from worlds.bigville_play_world import BigvillePlayWorld as W


def _run(field_cache, ticks=14):
    w = W(cast=10, seed=276000)
    w._use_field_cache = field_cache
    pos = []
    for _ in range(ticks):
        w.integ_step()
        pos.append({nm: tuple(w.pos[nm]) for nm in w.people if nm in w.pos})
    out = dict(pos=pos, floods=w._floods, cost=w._cost_steps,
               moves=None, cache=len(w._field_cache))
    w.close()
    return out


@pytest.fixture(scope="module")
def paired():
    return _run(field_cache=False), _run(field_cache=True)


def test_field_cache_is_byte_identical(paired):
    """Every resident's position, every tick, is identical with the cache on vs off:
    the restored field == a fresh flood, so no decision changes."""
    off, on = paired
    assert on["pos"] == off["pos"]


def test_cache_floods_far_less(paired):
    """With the cache, only NEW goals flood; repeated goals restore. So floods drop
    to ~the number of unique goals ever seen, well below the no-cache count."""
    off, on = paired
    assert on["floods"] < off["floods"] / 3          # >=3x fewer floods
    assert on["floods"] == on["cache"]                # one flood per unique goal
    assert on["cost"] < off["cost"]                   # fewer total rule-fires


def test_restored_field_equals_a_fresh_flood():
    """Correctness of the mirror: a restored gdist field is bit-for-bit a fresh
    flood of the same goal."""
    w = W(cast=6, seed=276000)
    try:
        nm = w.people[0]
        m = w._movers[nm]
        goal = list(w._cell_at.keys())[12]
        w.set_goal(nm, goal)
        w._flood_and_budget(nm, m)                     # flood + cache
        fresh = {nid: float(w.eng.node(nid)["attrs"]["gdist"])
                 for nid in w._cell_at.values()}
        # move the field elsewhere, then restore the cached goal
        other = list(w._cell_at.keys())[-12]
        w.set_goal(nm, other); w._flood_and_budget(nm, m)
        w.set_goal(nm, goal); w._flood_and_budget(nm, m)   # RESTORE from cache
        restored = {nid: float(w.eng.node(nid)["attrs"]["gdist"])
                    for nid in w._cell_at.values()}
        assert restored == fresh
    finally:
        w.close()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
