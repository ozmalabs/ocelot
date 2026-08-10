"""DERIVE r_C FROM THE DE SITTER HORIZON — the step that would turn the cosmological
collapse prediction from a mass-RANGE into a POINT. The honest outcome is NO, and the
reason is illuminating: it tells us the spatial structure of collapse cannot be cosmological.

A collapse mechanism must LOCALISE position, which requires the collapse noise to have
SHORT spatial correlation length r_C — comparable to the displacement you want to
distinguish (CSL uses r_C ~ 100 nm; the framework's pinning rule gave r_C = ℓ ~ atomic).
A noise that is spatially SMOOTH over the superposition (r_C ≫ Δ) shifts both branches
together → an unobservable global translation → it localises NOTHING. Formally the
collapse rate carries a (Δ/r_C)² factor that → 0 as r_C → ∞.

So the question: what spatial correlation length does the de Sitter horizon give?
"""
from __future__ import annotations
import math

C    = 2.99792458e8
HBAR = 1.054571817e-34
KB   = 1.380649e-23
G    = 6.67430e-11
AMU  = 1.66053907e-27
LAMBDA = 1.1e-52
NU = C * math.sqrt(LAMBDA)                 # cosmological rate ~3e-18 s^-1
H  = C * math.sqrt(LAMBDA / 3)             # de Sitter / Hubble rate
L_HUBBLE = C / H                           # de Sitter horizon radius
L_PLANCK = math.sqrt(HBAR * G / C**3)


def collapse_rate(N, rC, Delta, nu=NU, rho_n=3e30):
    """Γ ≈ ν · N·min(N,n_corr) · min(1,(Δ/r_C)²)  — CSL-class, with the smoothness
    suppression that bites when the noise is correlated over more than Δ."""
    n_corr = rho_n * (4 * math.pi / 3) * rC**3
    A = N * min(N, n_corr)
    supp = min(1.0, (Delta / rC) ** 2)
    return nu * A * supp


def main():
    print("DERIVE r_C FROM THE DE SITTER HORIZON")
    print("=" * 80)
    print(f"""
  Lengths the de Sitter horizon offers (Λ = {LAMBDA:.1e} m⁻²):
    Hubble / horizon radius  c/H        = {L_HUBBLE:.2e} m   (the only NATURAL de Sitter length)
    holographic UV–IR mean   √(ℓ_P·c/H) = {math.sqrt(L_PLANCK*L_HUBBLE):.2e} m   (~50 µm; speculative)
    de Sitter thermal λ      ~2πc/H     = {2*math.pi*L_HUBBLE:.2e} m
  Every one is ENORMOUS compared to any laboratory displacement (nm–µm). There is no
  short length here. And for Λ a true CONSTANT, its imprint is spatially UNIFORM on all
  sub-horizon scales — effectively r_C → ∞.""")

    print("=" * 80)
    print("WHAT r_C = HORIZON DOES TO COLLAPSE  (the smoothness catastrophe)")
    print("=" * 80)
    N_ptr, Delta = 1e23, 1e-3   # a 1-gram pointer in a 1 mm superposition
    print(f"  Test object: 1 g pointer (N={N_ptr:.0e}), superposition Δ = {Delta*1e3:.0f} mm.")
    print(f"    {'r_C':>16} {'Γ [s⁻¹]':>12} {'τ_collapse':>16}")
    print("    " + "-" * 48)
    for rC, lbl in [(1e-7, "100 nm (CSL ref)"), (math.sqrt(L_PLANCK*L_HUBBLE), "~50 µm (holo)"),
                    (L_HUBBLE, "Hubble c/H")]:
        G_ = collapse_rate(N_ptr, rC, Delta)
        tau = 1/G_ if G_ > 0 else float("inf")
        tau_s = f"{tau:.1e} s" if tau < 3e7 else f"{tau/3.15e7:.1e} yr"
        print(f"    {lbl:>16} {G_:>12.1e} {tau_s:>16}")
    print(f"""
  With the horizon-scale r_C, a 1-gram pointer collapses in ~10²² YEARS — it NEVER collapses.
  The (Δ/r_C)² ≈ ({Delta:.0e}/{L_HUBBLE:.0e})² ≈ {(Delta/L_HUBBLE)**2:.0e} factor annihilates it. Even the
  speculative ~50 µm holographic length suppresses every sub-50-µm lab superposition.""")

    print("=" * 80)
    print("WHY — and it is rigorous for a constant Λ")
    print("=" * 80)
    print("""
  Λ is a CONSTANT. A constant-sourced field is spatially UNIFORM; a uniform noise displaces
  both branches of a superposition identically — a global translation, which is unobservable
  and localises nothing. Position collapse REQUIRES a noise that differs across the
  displacement, i.e. short r_C. The de Sitter horizon, being smooth on every sub-horizon
  scale, is exactly the wrong spatial structure. This is not a missing factor — it is a
  category mismatch: cosmology supplies a RATE (and a huge length), never a short one.""")

    print("=" * 80)
    print("VERDICT — the derivation FAILS, and that is the result")
    print("=" * 80)
    print(f"""
  r_C from the de Sitter horizon = c/H ≈ {L_HUBBLE:.0e} m (or, for constant Λ, effectively ∞).
  That is ~36 orders of magnitude too LONG to localise anything. The cosmological imprint
  CANNOT supply the short, structured correlation length a collapse model needs.

  CONSEQUENCES (honest):
   · The seductive coincidence — ν_Λ ≈ the CSL collapse rate — was very likely just a
     coincidence. Λ plausibly sets a RATE near the right magnitude, but it cannot source the
     SPATIAL structure collapse requires, so the rate-match doesn't assemble into a mechanism.
   · The cosmological lead does NOT close. Its spatial correlation length has to come from
     somewhere non-cosmological — the matter's own localisation (the pinning rule, r_C = ℓ ~
     atomic). That surviving HYBRID (cosmological rate + matter-set r_C) reverts to linear
     amplification (threshold ~µg, future-testable) and abandons the 'everything from Λ'
     unification. It works, but it is no longer a parameter-free cosmological prediction —
     ν_Λ becomes just a candidate magnitude for an otherwise CSL-like model.
   · BOTH concrete imprints have now failed a push-to-the-end: GRAVITATIONAL refuted by real
     Donadi data; COSMOLOGICAL spatial structure refuted by its own smoothness. The framework's
     CORE (β=∞-forbidden ⇒ objective collapse, isolated systems) is untouched and still
     falsifiable-in-principle — but it has NOT delivered a working quantitative collapse model.
     The unsolved piece is now sharply named: the SPATIAL LOCALISATION STRUCTURE of the noise.

  NET: pushing to derive r_C did its job — it returned a clean NO and told us exactly why
  (a constant Λ is spatially smooth, so it cannot localise). The investigation's honest end:
  the graph law strongly MOTIVATES objective collapse and even lands a tantalising rate, but
  neither gravitational nor cosmological imprint yields a surviving sharp model — the spatial
  structure is where it stops. That is the real boundary, found by refusing to fudge past it.
""")


if __name__ == "__main__":
    main()
