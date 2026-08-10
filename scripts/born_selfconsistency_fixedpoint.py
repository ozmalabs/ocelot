"""THE CONSISTENCY CHECK THAT COULD KILL IT. The pinning rule sets R₀ = ℓ[ψ], the
localisation length of the collapsing degree of freedom. But the collapse DYNAMICS,
regularised at R₀, itself drives the wavefunction to some localisation ℓ'. Self-
consistency demands a FIXED POINT:  ℓ = ℓ[collapse[ℓ]].  If that loop has no
well-defined stable solution (runs to 0 or ∞, or is a repeller), the state-dependent
R₀ is incoherent and the theory dies here.

Solve it (order-of-magnitude, Gaussian ansatz — honest about that):

  Two competing rates on a free mass m of width σ (so ℓ ~ σ, and R₀ = σ):
    · SCHRÖDINGER SPREADING widens it.  Doubling time  t_spread ~ m σ² / ħ.
    · COLLAPSE LOCALISATION narrows it. Diósi–Penrose localisation strength for a mass
      smeared at R₀ is  η ~ G m² / (ħ R₀³)  [units 1/(L²·T)]; the time to localise a
      separation ~σ is  t_coll ~ 1/(η σ²).
  Substituting the SELF-CONSISTENT R₀ = σ:  η = G m² / (ħ σ³),  t_coll ~ ħ σ /(G m²).

  Fixed point  t_spread = t_coll:
        m σ² / ħ  =  ħ σ / (G m²)   ⟹   σ* = ħ² / (G m³).

  That is the GRAVITATIONAL BOHR RADIUS — the Schrödinger–Newton soliton width (Diósi
  1984; Penrose 1998; existence/uniqueness proved by Moroz–Penrose–Tod 1998). The self-
  referential R₀ = ℓ does NOT run away: it lands on a known, well-defined stationary
  solution — the size at which a mass's quantum spreading balances its own self-gravity.
"""
from __future__ import annotations

HBAR = 1.054571817e-34
G    = 6.67430e-11
AMU  = 1.66053907e-27
A0   = 5.29177e-11          # Bohr radius
LP   = 1.616255e-35         # Planck length
MP   = 2.176434e-8          # Planck mass
R_UNIV = 8.8e26             # observable-universe radius (m)


def sigma_star(m):
    """Self-consistent localisation length ℓ* = ħ²/(G m³) — gravitational Bohr radius."""
    return HBAR**2 / (G * m**3)


def fmt_len(L):
    if L > R_UNIV:   return f"{L:.1e} m  (≫ universe ⇒ never self-localises; QM exact)"
    if L > 1:        return f"{L:.1e} m"
    if L > 1e-12:    return f"{L:.1e} m  (~{L/A0:.1e}·a₀)"
    return f"{L:.1e} m"


def main():
    print("SELF-CONSISTENCY FIXED POINT  ℓ = ℓ[collapse[ℓ]]")
    print("=" * 78)
    print("""
  Balance Schrödinger spreading (t ~ mσ²/ħ) against DP collapse localisation
  (η = Gm²/ħσ³, t ~ ħσ/Gm²) with the self-consistent R₀ = σ:

        σ* = ħ² / (G m³)     ← the gravitational Bohr radius / Schrödinger–Newton soliton
""")

    print("  STABILITY (is the fixed point an attractor or a repeller?):")
    print("    narrowing rate  1/t_coll   = G m²/(ħ σ)     ∝ 1/σ")
    print("    widening  rate  1/t_spread = ħ/(m σ²)       ∝ 1/σ²")
    print("    σ > σ*:  1/σ  >  1/σ²  ⇒ narrowing wins ⇒ σ shrinks → back to σ*")
    print("    σ < σ*:  1/σ² >  1/σ   ⇒ spreading wins ⇒ σ grows  → back to σ*")
    print("    ⇒ σ* is a STABLE ATTRACTOR. The loop converges; it does not run to 0 or ∞.\n")

    print("  σ* = ħ²/(G m³) across scales:")
    print(f"    {'system':30} {'mass [kg]':>11}   ℓ* = σ*")
    print("    " + "-" * 68)
    cases = [
        ("electron",                       9.109e-31),
        ("proton",                         1.673e-27),
        ("large molecule ~1e6 amu",        1e6 * AMU),
        ("nanoparticle ~1e10 amu",         1e10 * AMU),
        ("CROSSOVER: σ* = a₀",             (HBAR**2 / (G * A0))**(1/3)),
        ("Planck mass",                    MP),
    ]
    for label, m in cases:
        print(f"    {label:30} {m:>11.2e}   {fmt_len(sigma_star(m))}")

    m_cross = (HBAR**2 / (G * A0))**(1/3)
    print(f"""
  Reading: microscopic masses → σ* ≫ universe ⇒ self-gravity NEVER localises them ⇒ QM
  is exact (electron interference, matter waves — all consistent). Localisation to atomic
  scale needs m ~ {m_cross:.1e} kg ≈ {m_cross/AMU:.0e} amu ~ 0.1 pg — a levitated nanoparticle,
  exactly the regime where gravitational decoherence is actually being hunted (Romero-Isart;
  levitated optomechanics). And at the Planck mass, σ* = the Planck length — the limits close.""")

    print("=" * 78)
    print("DOES THIS CONFLICT WITH R₀ ≈ a₀ FROM THE DONADI CASE?  (no — two regimes)")
    print("=" * 78)
    print("""
  No. There are two ways a DOF gets its localisation, and only one runs the loop:
    · FREE / isolated DOF (no external binding): ℓ is set BY the collapse-vs-gravity
      balance ⇒ the fixed point σ* = ħ²/Gm³ above. (Self-consistent; huge for micro masses.)
    · EXTERNALLY BOUND DOF (atomic electron): ℓ is set by the EM binding (orbital ~ a₀),
      not by gravity. No self-loop — R₀ = a₀ is just read off the bound state. THIS is the
      Donadi regime; it is governed by the binding, not by σ*.
  So the self-consistency fixed point governs free/levitated masses; the EM-bound electrons
  keep R₀ ~ a₀. The two numbers are different because they are different physical situations,
  not a contradiction.""")

    print("=" * 78)
    print("VERDICT — did the consistency check pass?")
    print("=" * 78)
    print("""
  PASSES, at the level it was posed. The self-referential R₀ = ℓ[ψ] does NOT blow up or
  vanish: the loop has a UNIQUE, STABLE fixed point σ* = ħ²/(G m³), which is a KNOWN,
  rigorously-established object — the Schrödinger–Newton soliton (existence/uniqueness:
  Moroz–Penrose–Tod 1998). So the state-dependent regularisation is coherent, not circular-
  in-a-fatal-way, and it reproduces the correct physics (micro = quantum, localisation only
  for ~0.1 pg+ masses, Planck-mass ↔ Planck-length).

  WHAT IS STILL OPEN (honest):
    · Order-of-magnitude only. I balanced timescales with a Gaussian ansatz; the full
      Schrödinger–Newton numerics fix O(1) factors but the scale ħ²/Gm³ is the established
      soliton width, so the conclusion is robust.
    · This shows the FREE-DOF loop converges. GLOBAL consistency of the full many-body
      collapse model with R₀ = ℓ everywhere (and the radiation problem from before) is NOT
      proved — it is the next layer.
    · The fixed point IS the Schrödinger–Newton soliton, so it inherits SN's own status as a
      semiclassical-gravity / mean-field equation, with the interpretational debates that
      carries. The framework rediscovers SN; it does not transcend it.

  NET: the check that 'could kill it' did not. The self-consistent localisation length is the
  gravitational soliton — a real, stable, unique attractor — and the framework's self-
  referential pinning rule lands exactly on established gravitational-localisation physics.
  That is a genuine pass, with the heavier consistency (full many-body + radiation) still to do.
""")


if __name__ == "__main__":
    main()
