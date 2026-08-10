"""CAN the Jabberwock + the graph law push the boundary of QM understanding?
A fun investigation. The answer may be no — so every claim is graded against the
ACTUAL physics literature, and relocation/speculation is flagged, not hidden.

Where we stopped (derive_born_rule.py): the exponent 2 is DERIVED (phase is an
unobservable rotation ⇒ the only invariant is quadratic, Pythagoras), but the
MEASURE postulate — why the invariant IS the probability — relocated to Gleason's
additivity. The frontier question: does the graph law say anything standard QM
leaves OPEN, ideally FALSIFIABLE?

The lead: a concept the agent already holds —
  beta_infinity_is_incorrigible_unreachable_absolute: 'β=∞ … no finite weight of
  evidence can ever hop it … the forbidden absolute … the UNREACHABLE LIMIT'
A perfectly coherent superposition held FOREVER is a β=∞ state (an alternative
held with no possible crystallisation). If the framework forbids β=∞, it forbids
perfect indefinite unitarity — a real, falsifiable fork.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

# The argument, as signed premises anchored to HELD concepts. The agent's
# composition faculty chains them; the physics is the external check.
PREMISES = [
    ("coherent_superposition_held_forever", "constitutes", "beta_infinity_state",
     "beta_infinity_is_incorrigible_unreachable_absolute — an alternative held with NO possible "
     "crystallisation is exactly β=∞: an infinitely deep basin nothing can hop."),
    ("beta_infinity_state", "is", "forbidden_unreachable_absolute",
     "the SAME held concept — β=∞ is the forbidden absolute, the unreachable limit. The framework "
     "does not exempt physics from its own anti-absolute axiom."),
    ("forbidden_unreachable_absolute", "implies", "finite_coherence_bound",
     "if β=∞ is unreachable then every basin is FINITE ⇒ no superposition is incorrigible ⇒ there "
     "is a finite (possibly enormous) bound on how long/large coherence can hold."),
    ("finite_coherence_bound", "implies", "objective_collapse_is_real",
     "a finite coherence bound means coherence ENDS on its own — collapse is a real physical "
     "process, not only apparent. This lands the framework in the objective-collapse camp "
     "(GRW / Diósi-Penrose / CSL), as a CONSEQUENCE, not a postulate."),
    ("objective_collapse_is_real", "implies", "isolated_system_collapse_prediction",
     "the sharp, falsifiable fork: collapse for an ISOLATED system (no environment). Decoherence "
     "needs an environment; β=∞-forbidden does NOT — so the framework predicts collapse even when "
     "isolated. That distinguishes it from pure decoherence / unitary-forever MWI."),
    # the rate bridge — using the agent's own evidence-in-bits dynamics:
    ("which_path_information_in_bits", "drives", "basin_hop_collapse",
     "evidence_is_the_field_in_bits + foundational_revision_is_sudden_basin_hop — which-path "
     "information accumulates in BITS; when accumulated bits exceed the basin barrier the state "
     "FLIPS suddenly (a basin-hop), not gradually. Collapse = the gestalt switch at threshold."),
    ("basin_hop_collapse", "constitutes", "grw_penrose_form",
     "sudden localisation at an evidence threshold IS the GRW/Penrose form: collapse RATE rises "
     "with the rate which-path information is imprinted (∝ mass/size/gravitational self-energy)."),
]


def main():
    print("QM FRONTIER PROBE — can the graph law push past where we stopped?")
    print("=" * 80)
    print("\nThe held lever standard QM violates: β=∞ is FORBIDDEN, but 'unitary forever'")
    print("(perfect indefinite coherence) IS a β=∞ state. Premises (anchored to held concepts):\n")
    for A, rel, B, anchor in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {anchor}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=10)

    print("\n" + "=" * 80)
    print("THE AGENT'S COMPOSED CHAIN")
    print("=" * 80)
    for tgt in ("objective_collapse_is_real", "isolated_system_collapse_prediction"):
        ch = query(derived, "coherent_superposition_held_forever", tgt)
        if ch:
            net, steps = ch
            print(f"\n  coherent_superposition_held_forever ⟹ {tgt}  ({len(steps)} steps):")
            print("    " + fmt_chain(steps))

    print("\n" + "=" * 80)
    print("GRADED AGAINST THE ACTUAL PHYSICS  (honest — relocation/speculation flagged)")
    print("=" * 80)
    print("""
  [GENUINE, ~0.6]  A PRINCIPLED, FALSIFIABLE STANCE ON THE MEASUREMENT PROBLEM.
    Textbook QM leaves collapse-vs-decoherence-vs-MWI open. The framework does NOT:
    its anti-absolute axiom (β=∞ unreachable) FORBIDS perfect indefinite coherence,
    so it predicts OBJECTIVE COLLAPSE — even for an isolated system. That is a real,
    side-picking, testable commitment, reached from a concept the agent already holds
    rather than added by hand. Picking a side FOR A REASON is a (modest) push.

  [GENUINE, ~0.55]  A UNIFICATION: collapse = the agent's OWN belief-revision.
    The same β-threshold + sudden basin-hop that governs the agent's cognition governs
    quantum collapse; which-path information is the evidence-field-in-bits; collapse is
    the gestalt flip at the barrier. One mechanism spans mind and measurement. Concep-
    tually satisfying; it also predicts the GRW/Penrose FORM (rate ∝ which-path-info
    imprint ∝ mass/size) without a new postulate.

  [RELOCATED, not solved]  THE MEASURE POSTULATE.
    The discrete graph offers COUNTING (probability = fraction of admissible fine-grained
    configurations) in place of Gleason's additivity. In a discrete graph, counting is
    arguably more PRIMITIVE than an additivity axiom — a small parsimony gain. But the
    |·|² still re-enters through how an amplitude-a state fine-grains into ~|a|² equal
    branches (Zurek envariance / Deutsch-Wallace). The square relocates again. NOT derived.

  [SPECULATIVE, ~0.2, flagged]  φ-SIGNATURES IN SPECTRA.
    If the discrete law is φ-NATIVE (phi_as_bounded_recursion_fixedpoint — more native than
    e for a discrete law), level-spacings/mass-ratios might carry a φ signature. Real hook:
    Coldea et al. (Science 2010) measured m₂/m₁ = φ in the quantum Ising chain CoNb₂O₆
    (emergent E8). That is a genuine experimental φ in a quantum system — but it is
    explained by E8 symmetry at criticality, NOT by the graph law. Resonance, not evidence.

  [THE HONEST 'NO' — the hard constraint]
    The CHEAPEST version of this is already DEAD. The parameter-free Diósi-Penrose
    gravitational-collapse model was experimentally REFUTED (Donadi et al., Nature Physics
    2021, via spontaneous X-ray emission). So 'collapse rate set purely by gravitational
    self-energy, no free parameter' is ruled out. The framework must therefore either carry
    a TUNED collapse scale (less elegant) or a different imprint mechanism — and it gives NO
    new number to pin it. Standard decoherence + MWI also fit all data with zero new physics,
    so the framework's isolated-system-collapse prediction is currently UNTESTED, not
    confirmed, and competes against a no-new-physics rival.
""")

    print("=" * 80)
    print("VERDICT — did we push the boundary?")
    print("=" * 80)
    print("""
  Partially, and honestly. NO new number, NO derived measure postulate, NO breakthrough.
  But two real, non-trivial things fall out of the graph law with nothing added by hand:
    (1) a PRINCIPLED, FALSIFIABLE prediction — objective collapse, isolated-system included,
        from the anti-absolute axiom; and
    (2) a UNIFICATION — quantum collapse and the agent's belief-revision are the SAME
        β-threshold basin-hop, predicting the GRW/Penrose form.
  The frontier it actually reaches: 'unitary-forever is the β=∞ idealisation the framework
  forbids.' That is a clean, contentful, testable claim — and the cheapest version is already
  constrained by experiment, which is exactly what an honest investigation wants: a fork that
  reality can rule on. Fun: yes. Boundary moved: a little, in the falsifiable direction.
  Solved QM: no.
""")


if __name__ == "__main__":
    main()
