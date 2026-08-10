#!/usr/bin/env python3
"""THE BLINK — the RETINAL step. A rigidly-translating footprint drifts across a
30x30 retina; the eyelid closes for two ticks (a real temporal hole: no active
cells). The bridge CONTINUES the drift generator through the blink and the belief
tracks the moving footprint; a shuffled pre-blink drift is held open. Honest scope
is the active-cell/change level (the footprint's retinal footprint), exactly as
the TIME/DEPTH retinal probes bounded theirs. Not confirmatory (burned seed 0)."""
from __future__ import annotations
import json, sys
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
H = W = 30
# an L-tromino footprint (active cells), read as its per-tick active-cell set
FOOT = [(0, 0), (1, 0), (2, 0), (2, 1)]


def frame_at(dr, dc):
    return [["on", r + dr, c + dc, 1] for (r, c) in FOOT]


def drift(vel, n):
    return [frame_at(vel[0] * t, vel[1] * t) for t in range(n)]


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "foot", "signature": json.dumps(frame_at(0, 0)),
               "kind": "faculty", "faculty": "foot", "dim_types": DT})
    return s, ag, native


def run(frames):
    s, ag, native = boot()
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "blink_seq", "key": ["retblink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    return s.node(o)["attrs"]


def norm(f):
    return sorted(tuple(x) for x in (f or []))


def main():
    print("ENGINE:", provenance_line())
    ok = True
    for vel in [(1, 0), (2, 1), (0, 1)]:
        truth = drift(vel, 7)                          # ground-truth, no blink
        seq = [truth[0], truth[1], truth[2], [], [], truth[5], truth[6]]
        at = run(seq)
        bridged_ok = at.get("status") == "blink_bridged" and at.get("bridged") is not None
        tracks = bridged_ok and all(
            norm(bf) == norm(truth[3 + j]) for j, bf in enumerate(at["bridged"]))
        invisible = at.get("diverged_at") == -1
        print(f"  drift{vel}: status={at.get('status')} bridged_tracks_footprint={tracks} "
              f"invisible(diverged_at={at.get('diverged_at')})")
        ok = ok and bridged_ok and tracks and invisible
    # shuffled retinal drift -> held open
    tr = drift((1, 0), 6)
    import random
    random.seed(0)
    pref = tr[:4][:]; random.shuffle(pref)
    while [min(c[1] for c in f) for f in pref] in (
            sorted([min(c[1] for c in f) for f in tr[:4]]),
            sorted([min(c[1] for c in f) for f in tr[:4]], reverse=True)):
        random.shuffle(pref)
    at2 = run(pref + [[], []])
    # confabulate-by-default: still fills, but UNCONSTRAINED (constraint flag honest)
    unconstrained = at2.get("bridged") is not None and at2.get("constrained") == 0.0
    print(f"  shuffled retinal drift -> {at2.get('status')} "
          f"(fills but unconstrained={unconstrained})")
    ok = ok and unconstrained
    print(f"\nRETINAL BLINK reached, positive: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
