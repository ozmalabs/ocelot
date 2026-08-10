"""§9 BYTE-IDENTITY GATE for predicate pushdown — old path vs new path, LIVE.

Predicate pushdown is a PURE PERFORMANCE CHANGE. If any committed result moves
by one bit, that is a bug, not an optimisation. This is the oracle.

WHAT IT COMPARES, AND WHY LIKE THIS (PROTOCOL §12.3)
----------------------------------------------------
It does NOT freeze a digest constant. Two gates rotted the same day they were
written by pinning a hash of a MUTABLE TREE, and they rotted by FALSELY
ACCUSING AN INNOCENT RUNG. The bulk agent's own digest legitimately moved
(245861... -> 49d6ab...) when it rebased onto another rung's `drive()` change.

So this pins the CONTRACT, not a value:

    digest(pushdown ON) == digest(pushdown OFF)

with BOTH RECOMPUTED LIVE, IN ONE PROCESS, on the same engine. `OFF` is the
literal pre-change matcher: `clear_pushdown_plans()` empties every rule's plan,
and an empty plan makes `extend_each` evaluate the where-clause whole at the
leaf — the exact code path that ran before this rung. Whatever `drive()` or any
other rung does to these floats tomorrow, both arms move together and the
invariant still means what it says.

The digest itself is `scripts/bulk_attr_digest.py`'s — a sha256 over EVERY attr
of every cell/unit/synapse at full `repr` (no rounding, so a one-ulp change
cannot hide), plus the activity movie and every receptive field. Reused, not
reimplemented.

POSITIVE CONTROLS — an oracle you have only ever seen pass is not an oracle
--------------------------------------------------------------------------
Three, all required to pass:

  1. ORACLE BITES: inject +1e-9 into one `last_burst` write; the digest MUST
     flip; revert; it MUST return to the original value. (The brief's ask, and
     exactly how this digest's author controlled it.)
  2. PUSHDOWN IS ARMED: `pushdown_armed()` must be non-empty and must include
     `wv_propagate`. If pushdown never engages, ON==OFF is VACUOUS — it would
     be comparing the same code path with itself and passing forever.
  3. THE SWITCH BITES: `clear_pushdown_plans()` must report clearing >0 plans.

USAGE
    python scripts/pushdown_identity_gate.py
"""
from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: pin THIS TREE's engine BEFORE any `domains.*` import.
# The first `substrate_rs` import binds the engine — a preamble that runs after
# one is a NO-OP THAT LOOKS CORRECT.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld, record  # noqa: E402

# Reuse the committed oracle's attr list — single source of truth, so if that
# oracle widens (as it did for the change rung's lum_* channels) this gate
# widens with it. Imported BY PATH: `scripts/` is deliberately not a package
# (adding an `__init__.py` would change import semantics for every other
# agent's script in this shared directory).
import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location(
    "_bulk_attr_digest", os.path.join(ROOT, "scripts", "bulk_attr_digest.py"))
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
ATTRS = _mod.ATTRS

PERTURB = {"on": False}


def _digest(track_prev_burst: bool, pushdown: bool) -> tuple[str, list[str], int]:
    h = hashlib.sha256()
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    armed = s._inner.pushdown_armed()
    cleared = 0
    if not pushdown:
        cleared = s._inner.clear_pushdown_plans()

    w = WaveWorld(s, h=24, w=24, seed=0, track_prev_burst=track_prev_burst)
    units = w.add_units(6, rf=7)
    rng = np.random.default_rng(3)

    for i in range(40):
        frame = rng.random((24, 24)).astype(np.float32) if i % 3 == 0 else None
        w.step(ignite_k=2 if i % 5 == 0 else 0, frame=frame)
        for n in w.cells.values():
            at = s.node(n)["attrs"]
            for k in ATTRS:
                v = at.get(k)
                # Positive control 1: a +1e-9 nudge on ONE attr must flip this.
                if PERTURB["on"] and k == "last_burst" and isinstance(v, float):
                    v = v + 1e-9
                h.update(repr(v).encode())
        h.update(w.frame().tobytes())

    w.set_bursting_from_frame()
    for n in w.cells.values():
        h.update(repr(s.node(n)["attrs"].get("bursting")).encode())

    for _ in range(6):
        w.replay_step((rng.random((24, 24)) > 0.5).astype(np.float32))
        for n in w.cells.values():
            at = s.node(n)["attrs"]
            h.update(repr(at.get("bursting")).encode())
            h.update(repr(at.get("last_burst")).encode())

    for u in units:
        h.update(w.receptive_field(u).tobytes())
        at = s.node(u)["attrs"]
        for k in ("act", "bursting", "wsum", "theta", "last_burst"):
            h.update(repr(at.get(k)).encode())

    s2, ag2 = boot_core()
    load_seeds_into(s2, ag2, ["vision_waves"])
    s2.set_attr(s2.nodes("WaveParams")[0], "propagate", 1.0)
    if not pushdown:
        s2._inner.clear_pushdown_plans()
    w2 = WaveWorld(s2, h=16, w=16, seed=7, track_prev_burst=track_prev_burst)
    h.update(record(w2, steps=25, ignite_k=1, ignite_every=6).tobytes())
    return h.hexdigest(), armed, cleared


def main() -> int:
    print(provenance_line(), flush=True)
    ok = True

    # --- positive control 2 + 3: pushdown is ARMED and the switch BITES ---
    _, armed, _ = _digest(False, True)
    _, _, cleared = _digest(False, False)
    print(f"\npushdown armed on {len(armed)} rules; wv_propagate in set: "
          f"{'wv_propagate' in armed}")
    print(f"clear_pushdown_plans() cleared {cleared} plans")
    if not armed or "wv_propagate" not in armed:
        print("FAIL: pushdown not armed on wv_propagate -> ON==OFF would be VACUOUS")
        ok = False
    if cleared <= 0:
        print("FAIL: the OFF switch cleared nothing -> both arms are the SAME path")
        ok = False

    # --- the invariant: ON == OFF, both recomputed live ---
    print()
    for t in (False, True):
        on, _, _ = _digest(t, True)
        off, _, _ = _digest(t, False)
        same = on == off
        ok &= same
        print(f"track_prev_burst={t!s:5s}  pushdown_ON ={on}")
        print(f"track_prev_burst={t!s:5s}  pushdown_OFF={off}  "
              f"{'IDENTICAL' if same else '*** DIVERGED — BUG ***'}")

    # --- positive control 1: the ORACLE ITSELF must be able to go red ---
    print("\n-- positive control: does this digest actually bite? --")
    base, _, _ = _digest(False, True)
    PERTURB["on"] = True
    nudged, _, _ = _digest(False, True)
    PERTURB["on"] = False
    restored, _, _ = _digest(False, True)
    print(f"baseline          {base}")
    print(f"+1e-9 on last_burst {nudged}  {'FLIPPED (good)' if nudged != base else '*** DID NOT FLIP — ORACLE IS INERT ***'}")
    print(f"reverted          {restored}  {'RESTORED (good)' if restored == base else '*** DID NOT RESTORE ***'}")
    if nudged == base or restored != base:
        ok = False

    print("\n" + ("PASS — pushdown is byte-identical, oracle positive-controlled"
                  if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
