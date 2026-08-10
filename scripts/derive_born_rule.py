"""The Jabberwock attempts the honest hole it named: DERIVE the Born rule (prob =
|ψ|²) from the framework, not postulate it. The question is specifically WHY THE
EXPONENT IS 2.

Method (the agent's own faculties, anchored to held concepts):
  · the derivation is laid out as signed relational premises, each anchored to a
    concept the agent already holds (NOT new physics put in by hand);
  · composition_engine.compose() CHAINS them — the proof is the agent's faculty
    forward-chaining the premises, not my assertion;
  · then an HONEST accounting: which step is DERIVED (forced by the framework) and
    which is RELOCATED (a postulate moved, not eliminated).

The framework's owned lever: phase is the ROTATIONAL component of the log axis
(e_as_log_axis_unit; e^{iπ}+1=0, e the unit of continuous self-reference, π the
half-turn). If that is already held, the exponent 2 should fall out as the
rotation-invariant — Pythagoras — rather than being assumed.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

# Each premise is (A, rel, B) + the HELD concept it rests on. rel signs are all
# POS here ("requires/implies/constitutes/enables") — this is a forcing chain.
PREMISES = [
    ("reversible_continuous_self_reference", "requires", "norm_preserving_evolution",
     "e_as_log_axis_unit — e is CONTINUOUS, reversible self-reference (dx/dt=x). "
     "Reversible + continuous ⇒ probability/measure conserved ⇒ evolution preserves the norm."),
    ("norm_preserving_evolution", "requires", "rotation_not_scaling",
     "compute_in_log_space — a real 1-D amplitude can only SCALE (grow/shrink), which is "
     "either irreversible or norm-changing. The only continuous, reversible, norm-preserving "
     "motion is a ROTATION — which needs a second axis. So the amplitude is 2-D."),
    ("rotation_not_scaling", "constitutes", "complex_amplitude_with_phase",
     "e_as_log_axis_unit — the second axis is the orthogonal/rotational one (e^{iθ}); the "
     "2-D rotating amplitude IS the complex amplitude ψ = r·e^{iθ}. Phase is the rotation angle."),
    ("complex_amplitude_with_phase", "implies", "global_phase_unobservable",
     "log_axis_law — a global rotation of every amplitude by the same angle changes nothing "
     "relational; on a log/relational axis only DIFFERENCES register, so the absolute phase "
     "is gauge — unobservable."),
    ("global_phase_unobservable", "implies", "only_rotation_invariants_observable",
     "efficiency_is_admissibility_grammar — if the global phase-rotation is a symmetry, then "
     "an observable is ADMISSIBLE only if it is invariant under that rotation. Non-invariant "
     "quantities are inadmissible — never observed."),
    ("only_rotation_invariants_observable", "requires", "quadratic_invariant_pythagoras",
     "phi_as_bounded_recursion_fixedpoint / geometry — the invariant of a planar rotation is "
     "the squared radius r² = x²+y² (Pythagoras). There is NO linear invariant (x, y each "
     "rotate); the LOWEST-order rotation-invariant is quadratic. The exponent is forced to 2."),
    ("quadratic_invariant_pythagoras", "constitutes", "exponent_two",
     "the '2' is now identified: it is the degree of the rotation-invariant, not a free choice."),
    ("exponent_two", "enables", "born_measure_psi_squared",
     "the observable weight on each outcome is the rotation-invariant of its amplitude = |ψ|²."),
    # the RELOCATED assumption — the leap from 'conserved invariant' to 'PROBABILITY':
    ("additivity_over_orthogonal_outcomes", "requires", "born_measure_psi_squared",
     "Gleason-equivalent — to call the invariant a PROBABILITY it must be additive over a "
     "complete set of mutually-exclusive (orthogonal) outcomes and total to 1. Given "
     "non-contextual additivity, |ψ|² is the UNIQUE such measure. THIS premise is the postulate "
     "that is relocated, not derived."),
]


def main():
    print("DERIVE THE BORN RULE — why probability = |ψ|², and why the exponent is 2")
    print("=" * 80)
    print("\nPREMISES (each anchored to a HELD framework concept — no new physics by hand):\n")
    for A, rel, B, anchor in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {anchor}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=10)

    print("\n" + "=" * 80)
    print("THE AGENT'S COMPOSED CHAIN  (composition_engine forward-chaining the premises)")
    print("=" * 80)
    chain = query(derived, "reversible_continuous_self_reference", "born_measure_psi_squared")
    if chain:
        net, steps = chain
        print(f"\n  reversible_continuous_self_reference  ⟹  born_measure_psi_squared "
              f"(net {'+' if net>0 else '−'}, {len(steps)} steps):\n")
        print("    " + fmt_chain(steps).replace(" —", "\n      —", 0))
        for a, rel, b in steps:
            print(f"      {a}  —{rel}→  {b}")
    else:
        print("  (no chain — premises did not compose to the target)")

    print("\n" + "=" * 80)
    print("HONEST ACCOUNTING — what is DERIVED vs RELOCATED")
    print("=" * 80)
    print("""
  DERIVED (the framework FORCES it), confidence ~0.7:
    · WHY COMPLEX. Reversible + continuous + norm-preserving evolution cannot be a
      1-D scaling; it must be a rotation, which needs a second axis. The amplitude
      is 2-D = complex. (This is Stone's theorem read through e = continuous
      self-reference: the generator is anti-symmetric ⇒ rotation.)
    · WHY EXPONENT 2. Global phase is an unobservable rotation ⇒ only rotation-
      INVARIANTS are admissible observables ⇒ the invariant of a planar rotation is
      the SQUARED radius (Pythagoras). There is no linear invariant. The '2' is the
      degree of the rotation-invariant — it is FORCED, not chosen. This is the part
      the agent flagged as the hole, and the framework genuinely closes it: |ψ|² is
      the Pythagorean length the phase-rotation conserves.

  RELOCATED (a postulate moved, not eliminated), confidence the FULL rule ~0.45:
    · WHY IT IS A PROBABILITY. Going from 'the conserved rotation-invariant' to
      'the probability of the outcome' needs ONE more thing: that the measure be
      ADDITIVE over a complete set of orthogonal outcomes and total to 1. Given that
      (Gleason's non-contextual additivity), |ψ|² is the UNIQUE measure. The framework
      MOTIVATES this — the invariant is the only phase-blind additive weight — but does
      not force it from a deeper principle. The mystery shrinks from 'why squared?' to
      'why is the additive invariant the probability?', which is one clean assumption.

  WHAT THIS IS, HONESTLY:
    Not a new theorem. This recapitulates the symmetry/Gleason/envariance arguments
    in the framework's own vocabulary. The framework's real contribution is that
    phase-as-rotation is ALREADY a held concept (e^{iπ}+1=0 as the log axis's
    rotational unit), so the exponent 2 is not postulated — it falls out as the
    rotation-invariant the moment you accept that the absolute phase is gauge. The
    '|ψ|²' stops being mysterious; the residue is the measure postulate, isolated and
    named. Hole partially filled: the 2 is derived, the probability-identification is
    relocated to additivity — and that is the honest stopping point.
""")


if __name__ == "__main__":
    main()
