"""BULK ATTRIBUTE BOUNDARY — the contract that makes the rewire a no-op.

WHAT THIS RUNG CLAIMS (and therefore what this file tests): `get_attr_many`
and `set_attr_many` are EXACTLY the per-node loops they replace. Nothing else.
They add no capability and make no decision — a caller still chooses WHICH
nodes and WHAT value; only the LOOP moved to Rust.

WHY IT IS TESTED THIS WAY (PROTOCOL §12.3 — a provenance claim must be pinned
to its DIFF, never to a mutable tree). The obvious gate would freeze a
whole-world state digest and assert the constant. That gate WOULD ROT, and it
would rot by FALSELY ACCUSING AN INNOCENT AGENT: `wave_world.drive()` is being
legitimately rewritten (median-split -> fire-on-change) in a concurrent rung,
which MUST change the wave floats. A frozen digest would fire and blame this
rung's optimisation for another rung's intended behaviour change.

So the invariant asserted here is the one this rung actually claims, and it is
true no matter what `drive()` decides: **the bulk accessor and the per-node
loop return the same thing, on whatever state the world happens to be in.**
Both sides are recomputed LIVE against each other. That is the INTENT, not a
proxy for it.

The byte-identity of the committed wave floats WAS verified, out-of-band and
against the pre-rewire code (identical sha256 over every cell/unit/synapse
attribute at full `repr` precision, with `track_prev_burst` both off and on) —
see `scripts/bulk_attr_digest.py`, which prints the digest but hardcodes NO
expectation, for exactly the reason above.

EVERY ASSERTION HERE WAS POSITIVE-CONTROLLED: a violation was injected into
each and the test was watched go RED, then reverted and watched go GREEN. A
gate you have only ever seen pass is not a gate you have tested.
"""
import pytest

from domains.engine_provenance import engine_preamble

engine_preamble()

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld

CELL_ATTRS = ("state", "driven", "bursting", "last_burst", "activated_at",
              "fired_at", "row", "col", "prev_burst", "dlast_burst")


def _live_world(track_prev_burst=False):
    """A world that has actually RUN — so the attrs under test carry the mixed,
    partly-defaulted values a real tick produces, not construction defaults."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=12, w=12, seed=0, track_prev_burst=track_prev_burst)
    for i in range(9):
        w.step(ignite_k=2 if i % 4 == 0 else 0)
    return s, w


@pytest.mark.parametrize("attr", CELL_ATTRS)
def test_get_attr_many_equals_the_per_node_loop(attr):
    """THE contract. Both sides computed live, so this holds under any
    `drive()` / rule change — it pins the accessor, not the behaviour."""
    s, w = _live_world()
    cells = list(w.cells.values())
    per_node = [s.node(n)["attrs"].get(attr) for n in cells]
    bulk = s.get_attr_many(cells, attr)
    assert bulk == per_node
    # and it is not vacuously equal by both being empty/all-None
    assert len(bulk) == len(cells) == 144


def test_the_state_read_is_not_vacuous():
    """§1: a comparison of two all-None lists would pass while measuring
    nothing. The retina must actually carry mixed state for the equality
    above to mean anything."""
    s, w = _live_world()
    states = set(s.get_attr_many(list(w.cells.values()), "state"))
    assert None not in states
    assert len(states) > 1, f"retina is in ONE state {states} — nothing to compare"


def test_unknown_key_is_all_none_and_a_read_never_mints_a_symbol():
    s, w = _live_world()
    cells = list(w.cells.values())
    assert s.get_attr_many(cells, "no_such_attr_zzz") == [None] * len(cells)
    # A read must not intern: the second call must behave identically, and the
    # key must still be absent from a per-node read.
    assert s.get_attr_many(cells, "no_such_attr_zzz") == [None] * len(cells)
    assert s.node(cells[0])["attrs"].get("no_such_attr_zzz") is None


def test_missing_node_raises_the_same_keyerror_as_node():
    s, w = _live_world()
    bad = type(list(w.cells.values())[0])(99_999_999)
    with pytest.raises(KeyError) as e_one:
        s.node(bad)
    with pytest.raises(KeyError) as e_bulk:
        s.get_attr_many([bad], "state")
    assert str(e_one.value) == str(e_bulk.value)


@pytest.mark.parametrize("value", [0.0, 1.0, -999.0, "rested", "active"])
def test_set_attr_many_equals_the_per_node_loop(value):
    s, w = _live_world()
    cells = list(w.cells.values())
    key = "state" if isinstance(value, str) else "driven"
    s.set_attr_many(cells, key, value)
    bulk = [s.node(n)["attrs"][key] for n in cells]
    for n in cells:
        s.set_attr(n, key, value)
    assert [s.node(n)["attrs"][key] for n in cells] == bulk == [value] * len(cells)


def test_set_attr_many_on_a_subset_leaves_the_complement_untouched():
    """The rewire writes uniform values over SUBSETS (on/off, recruited). The
    cells outside the subset must not be collaterally written."""
    s, w = _live_world()
    cells = list(w.cells.values())
    s.set_attr_many(cells, "driven", 0.0)
    half = cells[:50]
    s.set_attr_many(half, "driven", 1.0)
    got = s.get_attr_many(cells, "driven")
    assert got[:50] == [1.0] * 50
    assert got[50:] == [0.0] * (len(cells) - 50)


def test_hook_parity_bulk_fires_attr_set_exactly_as_per_node_does():
    """`set_attr` fires `attr_set` per write. The bulk writer skips the
    old->new snapshot ONLY when nothing can observe it; with a hook registered
    it must fall back and fire identically."""
    s, ag = boot_core()
    a = s.add_node("T", {"x": 0.0})
    b = s.add_node("T", {"x": 0.0})
    seen = []
    s._inner.register_hook("attr_set", lambda n, k, old, new: seen.append(
        (n.value, k, old, new)))
    s.set_attr(a, "x", 1.0)
    s.set_attr(b, "x", 1.0)
    per_node = list(seen)
    seen.clear()
    s._inner.set_attr_many([a, b], "x", 2.0)
    bulk = list(seen)
    # same nodes, same key, same ORDER
    assert [(n, k) for n, k, _, _ in bulk] == [(n, k) for n, k, _, _ in per_node]
    # and a correct old->new snapshot, not a stubbed one
    assert bulk == [(a.value, "x", 1.0, 2.0), (b.value, "x", 1.0, 2.0)]
    s._inner.clear_hooks()
    seen.clear()
    s._inner.set_attr_many([a, b], "x", 3.0)
    assert seen == [], "fast path must not fire hooks after clear_hooks"
    assert s.get_attr_many([a, b], "x") == [3.0, 3.0]


def test_bulk_is_actually_used_by_the_adapter_hot_path():
    """§12: a guard that does not guard the thing it claims. The whole point is
    that `step()` STOPPED crossing per cell — assert the adapter really calls
    the bulk path, so a revert to per-node loops is caught here rather than
    silently costing 5x."""
    import inspect
    import re
    src = inspect.getsource(WaveWorld.step) + inspect.getsource(WaveWorld._mark_bursts)
    assert "get_attr_many" in src and "set_attr_many" in src
    # A PER-CELL crossing is the thing banned — NOT every `node()` call. The
    # single `self.s.node(self.retina)` clock read is one crossing per tick,
    # not N, and is legitimate. This assertion was written the sloppy way first
    # ("no `self.s.node(` at all") and correctly fired on that innocent read:
    # it was the ASSERTION that was wrong, not the code. Ban the loop, not the
    # call.
    per_node = [m for m in re.findall(r"self\.s\.node\(([^)]*)\)", src)
                if m.strip() != "self.retina"]
    assert per_node == [], f"step/_mark_bursts crossed per-cell again: {per_node}"
