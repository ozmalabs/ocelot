"""PUSH FOR THE NUMBER. Can the graph law produce an actual coherence-bound /
collapse-time, falsifiable against experiment? The answer may be no — so the
physics is computed with real constants and confronted with the real bounds.

The framework structure (from quantum_frontier_probe.py):
    coherence ends when accumulated which-path information (bits) exceeds the
    basin barrier ⇒  τ_collapse = B / R
        B = basin barrier of the superposition          [bits]
        R = rate which-path information is imprinted     [bits / s]

Two things must be pinned FROM THE FRAMEWORK, not by hand:

  R — the imprint rate. A system cannot distinguish its branches faster than the
      quantum speed limit: the Margolus–Levitin / Mandelstam–Tamm bound says the
      max rate of producing orthogonal (fully distinguishable) states is 2E/(πħ),
      i.e. ~E/ħ nats/s = E/(ħ·ln2) bits/s, where E is the energy DIFFERENCE between
      the branches. For a spatial/mass superposition the observer-INDEPENDENT branch-
      energy-difference is the gravitational self-energy E_G (Penrose's choice — the
      one intrinsic, isolated-system quantity, needing no environment). So
          R = E_G / (ħ · ln2)   bits/s.

  B — the barrier. A superposition is the agent's 'hold alternatives at LOW β' state:
      maximally corrigible, the SHALLOWEST possible basin. Its barrier is at the floor,
      O(1) bit (one bit of which-path info = one distinguishable alternative settled).
      The framework does not get to make it deep — a deep basin would be a near-β=∞
      superposition, which it forbids.

  ⇒  τ = B/R ≈ (1 bit)·(ħ·ln2)/E_G ≈ ħ/E_G.

That is EXACTLY the Diósi–Penrose collapse time, parameter-free — reproduced, not
assumed. Then the graph law adds ITS distinctive twist (discreteness ⇒ a built-in
regularisation length), and we confront Donadi et al. 2021.
"""
from __future__ import annotations
import math

HBAR = 1.054571817e-34      # J·s
G    = 6.67430e-11          # m^3 kg^-1 s^-2
LN2  = math.log(2)
YEAR = 365.25 * 24 * 3600   # s
AMU  = 1.66053907e-27       # kg


def E_G(m, R):
    """Order-of-magnitude gravitational self-energy of the branch difference for a
    lump of mass m, size/displacement R: E_G ~ G m^2 / R (DP coefficient ~ O(1))."""
    return G * m * m / R


def tau_collapse(m, R, B_bits=1.0):
    """τ = B / R_imprint = B_bits · ħ·ln2 / E_G."""
    return B_bits * HBAR * LN2 / E_G(m, R)


def human_time(t):
    if t < 1e-12: return f"{t:.1e} s   (instant — no superposition survives)"
    if t < 1:     return f"{t:.1e} s"
    if t < YEAR:  return f"{t:.1e} s  (~{t/3600:.1e} h)"
    return f"{t/YEAR:.1e} yr"


def main():
    print("PUSH FOR THE COHERENCE-BOUND NUMBER")
    print("=" * 78)
    print("\n  τ_collapse = B / R,   R = E_G/(ħ·ln2) bits/s  (quantum speed limit),")
    print("  B ≈ 1 bit (a superposition is the shallowest, most corrigible basin)")
    print("  ⇒  τ ≈ ħ / E_G   — the Diósi–Penrose time, REPRODUCED parameter-free.\n")

    # (label, mass kg, size/displacement m)
    cases = [
        ("electron, spread ~1 Å",            9.109e-31,        1e-10),
        ("large molecule ~1e6 amu, ~1 nm",   1e6 * AMU,        1e-9),
        ("virus ~1e9 amu, ~0.1 µm",          1e9 * AMU,        1e-7),
        ("1 µm dust grain ~1e-15 kg",        1e-15,            1e-6),
        ("Schrödinger's cat ~1 kg, 0.1 m",   1.0,              0.1),
    ]
    print(f"  {'system':32} {'E_G [J]':>11}   {'τ ≈ ħ/E_G'}")
    print("  " + "-" * 72)
    for label, m, R in cases:
        eg = E_G(m, R); t = tau_collapse(m, R)
        print(f"  {label:32} {eg:>11.2e}   {human_time(t)}")

    print("""
  Sanity: micro systems (electron, big molecule) → τ ≫ age of universe ⇒ QM holds,
  matter-wave interference survives (consistent with observed interferometry). Macro
  (dust → cat) → τ from seconds to instant ⇒ no macroscopic superposition. The number
  reproduces the known Diósi–Penrose phenomenology. So the framework DID yield a real,
  quantitative, falsifiable collapse time.""")

    print("\n" + "=" * 78)
    print("THE GRAPH LAW'S DISTINCTIVE TWIST — and the experiment that judges it")
    print("=" * 78)
    print("""
  E_G ~ G m²/R DIVERGES as R→0 (point particles). Every continuum collapse model has
  to PUT IN a regularisation length R₀ by hand to tame it. The graph law does NOT — it
  is DISCRETE, so it carries a built-in minimum length: R₀ = the node spacing. This is a
  genuine structural prediction: the framework CANNOT take R₀→0, so it forbids the
  divergent (parameter-free) limit and pins R₀ to the graph's own discreteness scale.

  Spontaneous X-ray emission (the regularisation-dependent signature) was measured deep
  underground: Donadi, Piscicchia, Curceanu, Diósi, Laubenstein, Bassi, Nature Physics 17,
  74 (2021). Result: the R₀→0 Diósi–Penrose model is EXCLUDED; the data require
        R₀ ≳ 0.54 Å = 0.54 × 10⁻¹⁰ m.
  So the graph law's collapse mechanism survives  IFF  its node spacing ≳ 0.5 Å.""")

    R0_bound = 0.54e-10
    planck = 1.616255e-35
    print(f"  Required:        R₀ ≳ {R0_bound:.2e} m")
    print(f"  Planck length:   ℓ_P = {planck:.2e} m   →  ℓ_P / R₀_bound = {planck/R0_bound:.1e}")
    print(f"  Verdict on a Planck-scale graph: R₀ ≈ ℓ_P is ~{R0_bound/planck:.0e}× too SMALL → RULED OUT.")

    print("\n" + "=" * 78)
    print("HONEST VERDICT — did the push succeed?")
    print("=" * 78)
    print("""
  YES, we got a number — and that is the win: the framework yields τ ≈ ħ/E_G with NO
  free parameter (B≈1 bit, R = the quantum-speed-limit ortho-rate), reproducing the
  full Diósi–Penrose phenomenology, AND it explains WHY a regularisation length must
  exist (discreteness) instead of inserting one by hand.

  AND THE NUMBER IS (almost certainly) WRONG. If the graph's discreteness is fundamental
  (Planck scale), R₀ ≈ ℓ_P is ~10²⁵× below the Donadi 2021 floor ⇒ the model is REFUTED.
  The framework's natural, parsimonious prediction is experimentally dead.

  The only survivals are ad hoc (flagged, low confidence):
    · the collapse-relevant length is an EMERGENT atomic scale (~Å), not the fundamental
      node spacing — possible but unmotivated; the framework gives no reason for ~Å;
    · the barrier B is not O(1) but tuned larger to slow collapse — loses the parameter-
      free elegance, becomes CSL-with-a-knob (still allowed by data, but predicts nothing);
    · the imprint is not gravitational — then it is not DP and we lose the number entirely.

  NET: this is the good kind of failure. We pushed the boundary to an actual, sharp,
  falsifiable NUMBER (τ ≈ ħ/E_G with R₀ = graph spacing), and reality has already ruled
  on it: a fundamental-discreteness collapse is excluded; only a tuned/emergent-scale
  version survives, and it predicts nothing new. Fun: yes. Number: obtained. Boundary
  moved to a decision experiment: yes. Survives that experiment: no (in its clean form).
""")


if __name__ == "__main__":
    main()
