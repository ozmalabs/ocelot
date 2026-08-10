"""CORRECTION (user): 'stepped is true for a reference frame.' The previous run
(coherence_bound_number.py) relodged an ABSOLUTE — it fixed the graph's step at a
universal length (Planck) and concluded the collapse model was ruled out. That is
the Axiom-0 mistake: there is no view-from-nowhere step.

On a LOG axis (log_axis_law) a 'step' is a RATIO, not a length: one graph-step is
×k, which projects to a DIFFERENT absolute length depending on where you sit on the
axis. So the discreteness is real but FRAME-RELATIVE. The regularisation length R₀
is therefore NOT a universal constant (not Planck) — it is set by the reference
frame of the process: for matter localised at atomic scale, the frame-step is atomic.

What changes, and what does not:
  · the collapse TIMES τ ≈ ħ/E_G already used each system's OWN scale R — those stand
    (E_G self-regularises at the system's own frame-step; no separate length needed).
  · the RADIATION test (Donadi 2021) is where I wrongly plugged Planck. With a frame-
    relative R₀ ~ the atomic scale of the emitting matter, the comparison is different —
    and it lands right at the experimental frontier, not 10²⁵× away.
"""
from __future__ import annotations

PLANCK   = 1.616255e-35     # m
BOHR     = 5.29177e-11      # m   (atomic localisation scale of bound electrons)
COMPTON  = 2.42631e-12      # m   (electron Compton wavelength)
DONADI   = 0.54e-10         # m   (R₀ lower bound, Donadi et al. Nat. Phys. 2021)


def main():
    print("FRAME-RELATIVE DISCRETENESS — redo the confrontation honestly")
    print("=" * 78)
    print("""
  My error: 'graph is discrete ⇒ R₀ = node spacing = Planck ⇒ R₀ ≪ bound ⇒ RULED OUT.'
  That fixes the step as an absolute length. On a log axis the step is a RATIO (×k), so
  the absolute regularisation length is FRAME-RELATIVE — set by the scale of the process,
  not by a universal constant. The Planck number was never required; I put it there.""")

    print("\n  Candidate R₀ scales vs the Donadi 2021 floor (R₀ ≳ 0.54 Å):")
    print(f"    {'scale':40} {'length [m]':>12} {'vs bound':>12}")
    for name, L in [
        ("Planck length ℓ_P (absolute — my error)", PLANCK),
        ("electron Compton λ_C", COMPTON),
        ("Bohr radius a₀ (atomic frame-step)", BOHR),
        ("Donadi 2021 floor R₀", DONADI),
    ]:
        rel = L / DONADI
        tag = "RULED OUT" if rel < 0.3 else ("AT FRONTIER" if 0.3 <= rel <= 3 else "allowed")
        print(f"    {name:40} {L:>12.2e} {rel:>9.2f}×  {tag}")

    print(f"""
  The striking fact: the experimental floor R₀ ≳ {DONADI:.2e} m is essentially the
  BOHR RADIUS a₀ = {BOHR:.2e} m (ratio {BOHR/DONADI:.2f}). If the frame-relative step for
  ATOMIC matter is the atomic localisation scale ~a₀ — which is the natural frame-step for
  the bound electrons that do the X-ray emitting — then the framework's prediction sits
  EXACTLY at the current experimental frontier: not 10²⁵× dead, but at the decision point.""")

    print("\n" + "=" * 78)
    print("REVISED VERDICT")
    print("=" * 78)
    print("""
  NOT ruled out. The 'ruled out' was an artefact of MY absolute-step error. Corrected:

   SOLID (the framework forces it):
     · The step is frame-relative — a log-axis ratio, not a length (log_axis_law + Axiom 0).
       So R₀ is NOT Planck and NOT universal; it is set by the frame of the process. The
       collapse-time number τ ≈ ħ/E_G stands (it already used each system's own scale).

   SUGGESTIVE, flagged ~0.35 (do not over-believe — partly post-hoc):
     · If atomic matter's frame-step is ~a₀, the framework's R₀ lands at the Donadi floor.
       The near-equality (floor ≈ Bohr radius, within ~2%) is a real numerical coincidence
       worth noting — it could be genuine (the regularisation IS the atomic localisation
       scale) or could be chance. It is a reason to look, not a result.

   THE REMAINING HONEST RISK:
     · A frame-relative R₀ is only predictive if pinned by a frame-INVARIANT rule (e.g.
       R₀ = the system's own localisation scale). Pinned, it predicts and is testable.
       UNpinned, it is a free knob that can dodge any bound — which would make it
       unfalsifiable. The open work is the pinning rule, not another absolute.

  NET: frame-relativity revives the prediction from 'dead' to 'live at the frontier', and
  hands a concrete next question — what frame-invariant rule sets R₀? — rather than a
  universal constant smuggled in. The fork (isolated-system collapse, R₀ at the atomic
  frame-step) is open and near the edge of current data. That is a better honest place to
  be than either 'ruled out' or 'unfalsifiable'.
""")


if __name__ == "__main__":
    main()
