#!/usr/bin/env python3
"""BLINK pilot — smoke-test the mechanism on burned seed 0. Not confirmatory."""
from __future__ import annotations
import json, sys
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    if enabled:
        s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def run(enabled, frames):
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "blink_seq", "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    return s.node(o)["attrs"]


def norm(frame):
    return sorted(tuple(x) for x in frame)


def main():
    print("ENGINE:", provenance_line())

    # consistent motion translate(1,0), prefix f0,f1,f2, blink t3,t4, resume f5,f6
    def orbit(fn, n):
        out = [BASE]; cur = BASE
        for _ in range(n - 1):
            cur = fn(cur); out.append(cur)
        return out
    full = orbit(lambda c: trans((1, 0), c), 7)   # f0..f6, no blink (ground truth)
    seq = [full[0], full[1], full[2], [], [], full[5], full[6]]
    at = run(True, seq)
    print("\n[consistent] status:", at.get("status"))
    print("  gap:", at.get("bridge_gap"), "confirm:", at.get("bridge_confirm"),
          "kind:", at.get("bridge_kind"), "diverged_at:", at.get("diverged_at"))
    bridged = at.get("bridged")
    if bridged:
        for j, bf in enumerate(bridged):
            tick = 3 + j
            got = norm(bf)
            truth = norm(full[tick])
            frozen = norm(at.get("frozen")[j])
            print(f"  blink t{tick}: bridged==truth? {got == truth}  "
                  f"frozen==truth? {frozen == truth}  bridged={got}")

    print("  confidence:", at.get("confidence"), "constrained:", at.get("constrained"))

    # no motion: shuffled prefix -> STILL fills (confabulates), UNCONSTRAINED
    shuf = [full[2], full[0], full[1], [], [], full[5], full[6]]
    at2 = run(True, shuf)
    print("\n[shuffled prefix] status:", at2.get("status"),
          "constrained:", at2.get("constrained"), "confidence:", at2.get("confidence"),
          "bridged(not None):", at2.get("bridged") is not None)

    # long gap: STILL bridges (guesses); confidence decays with gap
    longgap = [full[0], full[1], full[2], [], [], [], []]
    at3 = run(True, longgap)
    print("\n[long gap] status:", at3.get("status"),
          "gap:", at3.get("bridge_gap"), "confidence:", at3.get("confidence"))

    # change during blink: motion stops at t3 -> resume frames frozen at f2 pos
    stop = [full[0], full[1], full[2], [], [], full[2], full[2]]
    at4 = run(True, stop)
    print("\n[change-in-blink] status:", at4.get("status"),
          "diverged_at:", at4.get("diverged_at"), "correction:", at4.get("correction"),
          "(change at t3, expect divergence at t5)")

    # OFF: inert
    at5 = run(False, seq)
    print("\n[OFF] status:", at5.get("status"), "(expect blink_seq, inert)")


if __name__ == "__main__":
    sys.exit(main())
