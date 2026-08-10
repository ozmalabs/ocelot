"""RUNG 8 — CONVERGENCE (PROTOCOL §2), on burned seeds (3000-3011 block reused).

**RUNG 6's OWN CONVERGENCE GATE, RE-RUN UNCHANGED ON THE COMPOSED INPUT.**
Same checkpoints, same drift definition, same OSI probe, same two etas, same
two normalisations, same `adapt_theta` preamble — the ONLY difference is which
retina is upstream. That is the whole design: if the gate's verdict moves, the
channels moved it.

Rung 6's result on its OWN (degenerate) channels, for reference:
  eta=5e-4 : RUNS AWAY   (drift 0.004 -> 0.461, clumpiness -> 0.85, OSI decaying)
  eta=1e-4 : STABLE, EMPTY (OSI 0.283 -> 0.329 vs a 0.3168 floor; peak/base ~1.5)
=> BOTH of PROTOCOL §2's stop conditions at once. The rung stopped here and
burned no confirmatory seed.

  CONVERGENT + USEFUL : OSI plateaus at non-zero AND drift -> 0
  never converges     : the scaffold is a TRANSIENT; every arm is measured at an
                        arbitrary point on a decay curve  => STOP
  converges to death  : drift -> 0 at floor structure      => STOP

**If this fails, REPORT AND STOP.** Rungs 5, 6 and phase 0 all correctly burned
no seeds when their gates failed.

The `degenerate` arm is run alongside as the reproduction check: rung 6's
numbers must come back, or the harness — not the channels — is what changed.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import provenance_line  # noqa: E402
from domains.onoff_world import segregation, set_params, weights  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    adapt_theta, build, develop_retina, osi_of, run_waves,
)

CHECKPOINTS = [400, 800, 1600, 3200, 6400]


def line(k, v):
    print(f"  {k:<40s} {v}")


def main():
    print("=" * 78)
    print("RUNG 8 CONVERGENCE — rung 6's gate, UNCHANGED, on rung 7's channels")
    print(provenance_line())
    print("=" * 78)

    for channels in ("lateral", "degenerate"):
        for subnorm, tag in ((1.0, "MILLER subtractive"), (0.0, "plain OJA")):
            for eta in (5e-4, 1e-4):
                print(f"\n--- channels={channels}  {tag}  eta={eta:g} ---")
                w, us, _anat, _bip = build(seed=3000, n_units=6,
                                           subnorm=subnorm, eta=eta,
                                           channels=channels)
                # THE RETINA DEVELOPS FIRST — the sequence that corresponds to
                # the animal (retinal centre-surround precedes cortical simple
                # cells), and the state ALL of rung 7's claims are measured at.
                # Without this the cortex spends its early plasticity on a DEAD
                # OFF channel (at g=0, OFF = max(-c,0) = 0), which is an
                # instrument artifact, not a fact about the channels.
                develop_retina(w, 3000)
                adapt_theta(w, 400)
                set_params(w, oo_eta=eta, frozen=0.0)
                if w.s.nodes("LatParams"):
                    # The retina keeps learning during the arm — that IS the
                    # composed system. Only `adapt_theta` froze it.
                    from domains.lateral_world import set_lat_params
                    set_lat_params(w, frozen=0.0)
                prev = weights(w, us).copy()
                done = 0
                for cp in CHECKPOINTS:
                    run_waves(w, cp - done)
                    done = cp
                    cur = weights(w, us)
                    drift = float(np.linalg.norm(cur - prev)
                                  / max(np.linalg.norm(cur), 1e-12))
                    nan = int(np.isnan(cur).sum())
                    o, st = osi_of(w, us)
                    set_params(w, frozen=0.0)   # un-freeze to continue training
                    if w.s.nodes("LatParams"):
                        from domains.lateral_world import set_lat_params
                        set_lat_params(w, frozen=0.0)
                    pk = st["tuning"].max(axis=1)
                    bs = np.maximum(st["baseline"], 1e-9)
                    clump = float(np.mean(
                        [segregation(w, u)["clumpiness"] for u in us]))
                    line(f"{cp:5d} steps  OSI",
                         f"{o.mean():.4f}  drift {drift:.4f}  NaN {nan}  "
                         f"peak/base {(pk / bs).mean():9.2f}  clump {clump:.3f}")
                    prev = cur.copy()


if __name__ == "__main__":
    main()
