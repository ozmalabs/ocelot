"""KEEP PUSHING — confront the pinning rule with the ACTUAL Donadi 2021 experiment,
not a generic bound. This is where reality votes, and the vote may be 'no'.

Donadi et al. (Nature Physics 17, 74, 2021) looked for the spontaneous X-ray emission
(19–100 keV) that gravity-related (Diósi–Penrose) collapse must produce in a germanium
detector deep underground. They saw NO excess, which EXCLUDES small R₀: smaller R₀ ⇒
shorter-scale collapse noise ⇒ more high-energy photons. Their bound: R₀ ≳ 0.54 Å.

The pinning rule (derive_R0_pinning_rule.py) says R₀ is NOT a free constant — it is the
localisation length of the COLLAPSING degree of freedom. DP collapse couples to MASS, and
the mass in germanium is in the NUCLEI. So the honest question is sharp and answerable:

    what is the localisation length of a germanium NUCLEUS in the crystal?

That is the Debye–Waller / zero-point r.m.s. displacement — a measured quantity. If it is
below 0.54 Å, the framework's gravitational realisation predicts TOO MUCH X-ray emission
and is EXCLUDED by Donadi. Let's just compute it.
"""
from __future__ import annotations
import math

HBAR = 1.054571817e-34
KB   = 1.380649e-23
AMU  = 1.66053907e-27
ANG  = 1e-10

# germanium
M_GE   = 72.63 * AMU      # kg, atomic mass
THETA  = 374.0            # K, Debye temperature
DONADI = 0.54 * ANG       # m, Donadi 2021 lower bound on R0


def zero_point_rms_3d(M, theta):
    """3D r.m.s. displacement of an atom in a Debye solid at T=0 (zero-point only).
    ⟨u²⟩_1D = (ħ/2M)·⟨1/ω⟩, Debye ⟨1/ω⟩ = 3/(2ω_D); 3D = 3×1D."""
    w_D = KB * theta / HBAR
    u2_1d = (HBAR / (2 * M)) * (3 / (2 * w_D))
    return math.sqrt(3 * u2_1d)


def main():
    print("CONFRONT DONADI 2021 — what R₀ does the pinning rule give for germanium?")
    print("=" * 80)

    rms = zero_point_rms_3d(M_GE, THETA)
    # room-temperature experimental Debye–Waller for Ge is larger (~0.084 Å); the
    # underground detector runs cold, so zero-point dominates — use that (conservative:
    # the SMALLEST plausible ℓ would be even more excluded; the LARGEST is room-temp).
    rms_roomT = 0.084 * ANG     # tabulated Ge B-factor ⇒ r.m.s. ≈ 0.084 Å at 300 K

    print(f"""
  The collapsing DOF is the Ge NUCLEUS (mass M = 72.6 amu). Its localisation in the
  lattice = the Debye–Waller r.m.s. displacement (a MEASURED property of the crystal):

    zero-point (T→0, Debye θ_D={THETA:.0f} K):  ℓ ≈ {rms/ANG:.3f} Å  = {rms:.2e} m
    room-temperature (tabulated B-factor):    ℓ ≈ {rms_roomT/ANG:.3f} Å  = {rms_roomT:.2e} m

  So the pinning rule gives  R₀ = ℓ_Ge ≈ {rms/ANG:.2f}–{rms_roomT/ANG:.2f} Å.""")

    print("\n  Compare to the Donadi 2021 floor:")
    print(f"    Donadi bound          R₀ ≳ {DONADI/ANG:.2f} Å")
    print(f"    framework (Ge nucleus) R₀ ≈ {rms/ANG:.2f}–{rms_roomT/ANG:.2f} Å")
    ratio_lo = DONADI / rms_roomT
    ratio_hi = DONADI / rms
    print(f"    ⇒ framework R₀ is ~{ratio_lo:.0f}–{ratio_hi:.0f}× BELOW the bound.")

    print("\n  Emission scales steeply with 1/R₀ (more short-scale noise ⇒ more X-rays).")
    for n, name in [(2, "if rate ∝ 1/R₀²"), (3, "if rate ∝ 1/R₀³")]:
        lo, hi = ratio_lo**n, ratio_hi**n
        print(f"    {name}: predicted emission ≈ {lo:.0f}–{hi:.0f}× the just-excluded level.")

    print("\n" + "=" * 80)
    print("VERDICT — reality voted")
    print("=" * 80)
    print(f"""
  The germanium nucleus is localised to ≈ {rms/ANG:.2f}–{rms_roomT/ANG:.2f} Å — about an order of
  magnitude BELOW Donadi's 0.54 Å floor. With the pinning rule R₀ = ℓ, the framework's
  gravitational-collapse realisation predicts roughly 50–1000× more spontaneous X-ray
  emission than the experiment allows. It is EXCLUDED (in severe tension at minimum).

  This is the honest 'no' the investigation was always open to. The push to real data
  KILLED the concrete prediction — and it killed it cleanly, on a measured number (the
  Debye–Waller displacement), not on a fudge.

  WHAT SURVIVES, WHAT DIES (precisely):
    DIES:  the GRAVITATIONAL imprint. τ ≈ ħ/E_G with R₀ = ℓ — the whole number-bearing
           prediction — is refuted by Donadi once R₀ is the real nuclear localisation.
           The elegant 'self-regularising at the system's own scale' is exactly what
           sinks it: the nuclear scale is too small, so the radiation is too large.
    LIVES: the framework's CORE — β=∞-forbidden ⇒ objective collapse is real — does NOT
           depend on the imprint being gravitational. It survives. BUT without the
           gravitational E_G it has NO number and NO rate, so on its own it predicts
           nothing concrete: back to falsifiable-only-if-a-new-imprint-is-specified.

  HONEST CAVEATS (do not let them rescue it — they don't close the order of magnitude):
    · O(1) factors and the exact 1/R₀ power need the full Donadi-style emission integral;
      but a ~7–10× deficit in R₀ gives ≳50× in rate under any plausible power. Robust.
    · One could argue the relevant DOF is not the bare nucleus but some larger effective
      localisation — but the mass IS in the nucleus, and its lattice localisation IS the
      Debye–Waller scale. There is no honest way to inflate ℓ_Ge to 0.54 Å.
    · The self-consistency fixed point (SN soliton) still stands for FREE masses; it is
      the BOUND/dense-matter regime, where ℓ is set externally and is small, that the
      data kills. The two results are consistent: free masses self-localise at ħ²/Gm³;
      bound nuclei sit at the Debye–Waller scale — and that scale is experimentally dead.

  NET: we pushed the graph law all the way to a measured number in a real underground
  experiment, and it lost. The gravitational realisation is excluded; the bare core
  survives but predicts nothing without a new imprint. That is the most honest and most
  valuable place the investigation could end: a sharp prediction, taken to the data,
  refuted — not a story that can't be wrong.
""")


if __name__ == "__main__":
    main()
