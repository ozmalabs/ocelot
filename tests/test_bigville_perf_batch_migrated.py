"""Perf gate: the batched per-tick phases (produce/buy/restock/consider run as ONE
run_rules fixpoint each, instead of one fixpoint PER entity) must be BYTE-IDENTICAL
to the per-entity path in the town's observable trajectory.

Profiled motivation: run_rules was 92% of wall-clock and the per-entity arm-then-run
loops called it ~O(people) times per tick, each re-scanning the whole graph. Batching
makes per-tick cost scale with the GRAPH, not the POPULATION (~4x measured at cast=16).
This is a droppable, behaviour-preserving optimisation -- gated here on identity of the
town's evolution (activity + obs per tick + final per-person coin/health/alive), which
must NOT change. `cost` (the run_rules step count) is EXPECTED to drop and is excluded.

NOTE: byte-identity holds where the batched fixpoint cannot reorder a CONTENDED outcome
(e.g. two buyers racing for the last unit of stock, or one attacker in two tensions).
If a future town introduces such contention, THIS GATE will catch it -- and the fix is
to leave the contended phase per-entity, not to loosen the gate.
"""
import os
import sys


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fingerprint(batch, n=40, seed=555000):
    from worlds.bigville_integ3_world import BigvilleInteg3World
    w = BigvilleInteg3World(cast=16, seed=seed)
    w._batch_phases = batch
    for _ in range(n):
        w.integ_step()
    traj = []
    for m in w.macro:
        obs = m.get("obs", {})
        traj.append((m["tick"], m["activity"], m.get("births", 0),
                     tuple(sorted((k, round(float(v), 4) if isinstance(v, (int, float)) else v)
                                  for k, v in obs.items()))))
    final = []
    for nm in sorted(w.people):
        a = w.eng.node(w._movers[nm])["attrs"]
        final.append((nm, round(float(a.get("coin", 0.0)), 3),
                      round(float(a.get("health", 0.0)), 3), w.is_dead(nm)))
    return traj, final


def test_batched_phases_are_byte_identical_to_per_entity():
    """The optimisation must not change the town: batched ≡ per-entity, tick for tick."""
    per_entity = _fingerprint(False)
    batched = _fingerprint(True)
    assert batched == per_entity, (
        "batched phases diverged from the per-entity baseline -- a contended phase is "
        "reordering an outcome; leave that phase per-entity rather than loosening this gate")


def test_batch_is_the_default():
    """The fast path ships ON (the whole point); the flag exists only for this gate."""
    from worlds.bigville_integ2_world import BigvilleInteg2World
    assert BigvilleInteg2World._batch_phases is True
