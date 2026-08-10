"""TOCK IS THE MODULO OF TICK — the agent's decisive test, on the real substrate.

The session's end: the law is a monotone least-fixpoint (tick = assert-until-stable; Tarski: order-independent,
no asserted quantity can DECREASE). The missing tock is the restoring RETURN -- and the creator's compression is
that the return is the MODULO of the tick: the monotone count (Z, the ramp) FOLDED at the tick boundary becomes the
oscillator (Z/NZ, the circle, the clock). The fold lives at the tick boundary -- exactly the stratum where the
agent's frame-guards already live (every frame-guard WAS a modulo, stratify-to-once-per-tick).

This runs three things on the REAL substrate (state in nodes, clock = s.tick()):
  - RAMP   : pure tick -- monotone accumulation, only ever grows, never returns.
  - PID    : the fold as a RESTORING return -- e = observed - setpoint; observed -= k*e at the boundary. e decays
             geometrically DOWN to 0 (a value going down under a restoring force -- which a monotone in-tick
             fixpoint cannot represent: the decrease lives ONLY at the fold).
  - MODULO : the fold as a WRAP -- phase = (phase+1) mod N. A sustained cycle: lawful non-halting (the clock), vs
             the agent's del_edge-in-fixpoint UNlawful non-halting (the crash). tock = modulo of tick.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_tock_is_modulo
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

K = 0.5          # PID gain (0<k<1 -> damped return)
N = 4            # modulus (the fold period)
TICKS = 13


def main():
    print("=" * 92)
    print("TOCK IS THE MODULO OF TICK — monotone ramp (tick) vs the fold at the boundary (tock), on the substrate")
    print("=" * 92)
    s = srs.Substrate()
    c = s.add_node("Clock", {"observed": 16.0, "setpoint": 0.0, "phase": 0.0, "ramp": 0.0})

    print(f"\n  k={K}  N={N}\n")
    print(f"    {'tick':>5}{'RAMP (tick: monotone, only up)':>34}{'PID e (fold: restoring return)':>34}{'phase mod N (fold: cycle)':>28}")
    for t in range(TICKS):
        a = s.node(c)["attrs"]
        e = a["observed"] - a["setpoint"]
        print(f"    {t:>5}{a['ramp']:>30.0f}    {e:>30.3f}    {a['phase']:>24.0f}")
        # THE FOLD at the tick boundary (= the modulo): the only place a value may go DOWN or WRAP.
        s.set_attr(c, "ramp", a["ramp"] + 1.0)                       # pure tick: monotone, never returns
        s.set_attr(c, "observed", a["observed"] - K * e)            # PID fold: restoring return  -> e decays to 0
        s.set_attr(c, "phase", (a["phase"] + 1.0) % N)              # modulo fold: sustained cycle (the clock)
        s.tick()                                                    # the real master clock

    af = s.node(c)["attrs"]
    e_final = af["observed"] - af["setpoint"]
    print("\n" + "=" * 92)
    print(f"  RAMP ran {af['ramp']:.0f} -> a monotone least-fixpoint: it ONLY grew, never returned (Tarski: no decrease).")
    print(f"  PID  e: 16 -> {e_final:.3f}: a DAMPED RETURN -- the error went DOWN under a restoring force, geometric")
    print(f"          (x{1-K:g} per fold). A single in-tick fixpoint cannot make a value decrease; the decrease lives")
    print(f"          ONLY at the fold (the tick boundary -- where retraction is already legal, the frame-guard stratum).")
    print(f"  MODULO phase cycled 0..{N-1}..0: a SUSTAINED, LAWFUL non-halting cycle -- the clock. (vs del_edge-in-")
    print(f"          fixpoint = UNlawful non-halting = the crash. The fold makes the non-halt periodic instead of chaotic.)")
    print("\n  THE CLICK: tick is Z (the ramp, monotone, accumulate); the FOLD at the boundary is mod (the tock);")
    print("  tick folded by mod is Z/NZ -- the circle, the oscillator, the clock. tock = modulo of tick, on the")
    print("  substrate's own clock -- the agent's 'logic-per-tick, restoring-force-across-ticks', demonstrated. And")
    print("  the same fold IS musical: octave = frequency mod 2, pitch-class = Z/12Z -- the oscillator and the octave")
    print("  are one object, met at the modulo. Not a new law: assert the residual, fold it at the clock you have.")
    print("=" * 92)


if __name__ == "__main__":
    main()
