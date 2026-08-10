"""BULK-ATTR DIGEST — the §9 byte-identity oracle for the boundary rewire.

*** A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Prints a sha256 over EVERY attribute of EVERY cell / unit / synapse of a run
wave world, at full `repr` precision, plus the activity movie and every
receptive field. It exercises every path the bulk rewire touched:
`step` / `ignite` / `drive` / `_mark_bursts` / `frame` /
`set_bursting_from_frame` / `replay_step` / `record`, with `track_prev_burst`
BOTH off (the default, rungs 1-2) and on (rung 3).

HOW IT WAS USED (2026-07-17, the Python<->Rust boundary rewire): run it, stash
the rewire, run it again, compare. The digests were IDENTICAL on both arms —
that is the §9 proof that replacing ~4N per-cell FFI crossings with 2-3 bulk
crossings per tick moved not one bit.

IT HARDCODES NO EXPECTED VALUE, DELIBERATELY (PROTOCOL §12.3). A frozen
constant here would ROT, and would rot by FALSELY ACCUSING AN INNOCENT RUNG:
`drive()` is under legitimate concurrent rewrite (median-split -> fire-on-
change), which MUST move these floats. A digest is only meaningful BETWEEN TWO
TREES YOU ARE DELIBERATELY COMPARING; frozen into a gate it just asserts that
nobody has done any work since. Compare it against a specific commit, never
against "the expected value".

    python scripts/bulk_attr_digest.py

The standing contract — `get_attr_many` / `set_attr_many` ARE the per-node
loops — is gated properly, and rot-proof, in
`tests/test_bulk_attr_boundary_migrated.py`.
"""
from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld, record  # noqa: E402

# Every attribute `wave_world` writes. `repr` (not a rounded format) so a
# one-ulp difference cannot hide — verified: injecting +1e-9 into one
# `last_burst` write flips the digest, and reverting restores it exactly.
ATTRS = ("state", "fired_at", "activated_at", "bursting", "last_burst",
         "driven", "prev_burst", "dlast_burst", "row", "col",
         # the CHANGE rung's per-cell luminance channels (a740154a) — covered
         # so this oracle keeps biting on the drive path it shares with us.
         "lum_raw", "lum_prev", "lum_seen")


def digest(track_prev_burst: bool) -> str:
    h = hashlib.sha256()
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=24, w=24, seed=0, track_prev_burst=track_prev_burst)
    units = w.add_units(6, rf=7)
    rng = np.random.default_rng(3)

    for i in range(40):
        frame = rng.random((24, 24)).astype(np.float32) if i % 3 == 0 else None
        w.step(ignite_k=2 if i % 5 == 0 else 0, frame=frame)
        for n in w.cells.values():
            at = s.node(n)["attrs"]
            for k in ATTRS:
                h.update(repr(at.get(k)).encode())
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

    # `record()` drives frame() + step() together — the read-out path.
    s2, ag2 = boot_core()
    load_seeds_into(s2, ag2, ["vision_waves"])
    s2.set_attr(s2.nodes("WaveParams")[0], "propagate", 1.0)
    w2 = WaveWorld(s2, h=16, w=16, seed=7, track_prev_burst=track_prev_burst)
    h.update(record(w2, steps=25, ignite_k=1, ignite_every=6).tobytes())
    return h.hexdigest()


def main() -> None:
    print(provenance_line(), flush=True)
    for t in (False, True):
        print(f"track_prev_burst={t!s:5s}  {digest(t)}", flush=True)


if __name__ == "__main__":
    main()
