"""PUSH THE FRAME-RELATIVITY TEST DEEPER. So far: facts are frame-relative (Wigner's
friend / Local Friendliness), the framework passes — but that is shared with RQM/QBism
(binary relational facts: the friend has a fact, Wigner doesn't). The framework's version
is MORE specific: a frame is an ADMISSIBILITY GRAMMAR, and signal/noise = what that
grammar can resolve. Push that, and three things sharpen — and land on measured physics.

  (1) FACTS ARE GRADED, NOT BINARY. A frame with PARTIAL resolving power has PARTIAL facts.
      RQM's relational fact is on/off; the framework predicts a continuum set by how much
      structure the grammar resolves as signal.

  (2) OBJECTIVITY = REDUNDANCY ACROSS GRAMMARS. The SAME structure that is signal in one
      frame and noise in another becomes a FRAME-INVARIANT (objective) fact exactly when MANY
      independent grammars redundantly resolve it. That is Zurek's QUANTUM DARWINISM:
      objectivity is the redundancy of a record across environment fragments. The framework
      derives it: 'objective' = signal in (nearly) every frame = redundantly resolved.

  (3) THE POINTER BASIS = THE ADMISSIBILITY-SELECTED BASIS. Why does the world go classical in
      THIS basis (position) and not another? Einselection: the basis stable under, and
      redundantly copied by, the interaction. Framework: redundant copyability ⟺ COMPRESSIBILITY
      — a variable proliferates across fragments precisely because it has a compact, stable
      description cheap to replicate. So einselection = the admissibility/MDL selector, the SAME
      one the agent uses to select stable structure in cognition.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

PREMISES = [
    ("a_fact_in_frame_F", "is", "structure_F_grammar_resolves_as_signal",
     "framework: signal = what the frame's admissibility grammar resolves as a distinguishable "
     "difference. A definite outcome IS the resolved structure."),
    ("partial_resolving_grammar", "constitutes", "partial_facts_graded_not_binary",
     "an observer/apparatus that records SOME but not all distinctions holds a PARTIAL fact — a "
     "continuum, set by resolving power. (RQM's relational fact is binary; this is graded.)"),
    ("same_structure_signal_in_many_independent_grammars", "constitutes", "redundancy",
     "the structure that is signal in F may be noise in F'; but if MANY independent frames "
     "resolve it as signal, the record is redundant."),
    ("redundancy_across_grammars", "constitutes", "objectivity",
     "objectivity = frame-INVARIANCE across the set of grammars = the structure being signal in "
     "(nearly) every frame. No observer-independent absolute is needed — just redundancy."),
    ("objectivity_equals_redundancy", "is", "quantum_darwinism",
     "Zurek's quantum Darwinism, derived: a fact is objective to the degree its record is "
     "redundantly copied into the environment. Measured (Unden NV-centre 2019; photonic Ciampini)."),
    ("redundant_copyability", "is", "compressibility",
     "a pointer state proliferates across fragments BECAUSE it has a compact, stable description "
     "cheap to replicate. Redundant-copyability ⟺ compressibility ⟺ admissibility-stability."),
    ("the_pointer_basis", "is", "the_admissibility_selected_basis",
     "so einselection (which basis goes classical) = the MDL/compression/admissibility selector. "
     "The classical variables are the COMPRESSIBLE, robust, redundantly-copyable ones."),
    ("admissibility_selection", "unifies", "einselection_and_cognition",
     "the SAME selector — stable, compressible, redundantly-copyable structure — makes things "
     "OBJECTIVE in physics and KNOWN in cognition. Quantum Darwinism's redundancy = the agent's "
     "compression-payoff. One principle across measurement and mind."),
]


def main():
    print("FRAME-RELATIVITY, PUSHED DEEPER — graded facts, redundancy, einselection")
    print("=" * 82)
    print("\nPremises (chained by the agent's composition faculty):\n")
    for A, rel, B, why in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {why}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=12)
    print("\n" + "=" * 82)
    print("WHAT COMPOSES")
    print("=" * 82)
    for src, tgt in [("same_structure_signal_in_many_independent_grammars", "quantum_darwinism"),
                     ("redundant_copyability", "einselection_and_cognition")]:
        ch = query(derived, src, tgt)
        if ch:
            net, steps = ch
            print(f"\n  ⟹ {tgt}:")
            print("    " + fmt_chain(steps))

    print("\n" + "=" * 82)
    print("THREE DEEPER, MEASURABLE HANDLES (beyond binary Wigner's friend)")
    print("=" * 82)
    print("""
  [A] GRADED FACTS. Tune an observer/apparatus's resolving power (recording fidelity / number of
      distinguished states) and the 'definiteness' of its fact should scale CONTINUOUSLY — partial
      resolution ⇒ partial fact. RQM predicts a binary relational fact; the framework predicts a
      gradient. Falsifier: a sharp on/off with no graded regime.

  [B] OBJECTIVITY TRACKS REDUNDANCY. The 'absoluteness' of an outcome should scale with how many
      independent environment fragments hold the record — the quantum-Darwinism redundancy plateau
      (R_δ). Measured already (NV centres, photonics). Falsifier: facts becoming objective WITHOUT
      redundant recording, or redundancy without objectivity.

  [C] THE CLASSICAL BASIS IS THE COMPRESSIBLE ONE. The emergent pointer basis should be exactly the
      MDL/compression-optimal, robustly-copyable basis — not merely 'whatever commutes with the
      interaction' as a brute fact, but the SAME stability/compressibility the agent's grammar uses.
      Falsifier: a decoherence basis that is robust/redundant yet NOT the compressible/admissible one.""")

    print("=" * 82)
    print("HONEST GRADING — what is deepened, what is genuinely new, what is re-description")
    print("=" * 82)
    print("""
  · DEEPENED & MEASURABLE: the test moves from binary 'are facts relative?' to GRADED structure —
    objectivity = redundancy across grammars (quantum Darwinism, already measured), facts graded by
    resolving power, classical basis = compressible basis. These are sharper handles with explicit
    falsifiers, and they CONNECT frame-relativity to the actual emergence of classicality.

  · MOSTLY SUBSUMPTION, HONESTLY: (1)–(2) re-derive decoherence + einselection + quantum Darwinism
    (Zurek) in the framework's vocabulary. That is consistency and unification, NOT new physics —
    the framework lands on established, measured results rather than predicting against them.

  · THE GENUINELY NEW & RISKIEST CLAIM — the distinguishing one: the CROSS-DOMAIN IDENTITY. The
    SAME admissibility/compression selector that picks the classical pointer basis in physics is the
    one that selects stable structure in COGNITION (and the agent's compression-payoff = quantum
    Darwinism's redundancy). If true, the emergence of classicality and the emergence of a learned
    concept are ONE law. This is where the framework is uniquely exposed — and where a real
    distinguishing test would have to live: show the physical pointer basis is the compression-
    optimal one by the SAME criterion the agent uses, not just the interaction-commuting one.
    NOT yet a designed experiment; it is the sharp open edge this push reaches.

  · BORN MEASURE still relocated — unchanged. Redundancy/typicality reframes WHY outcomes look
    objective, not why their weights are |ψ|².

  VERDICT: pushing deeper converts the frame-relativity test from binary-and-shared-with-RQM into a
  GRADED structure that meets measured physics (quantum Darwinism, einselection) — the framework
  subsumes those cleanly — and isolates its one genuinely distinctive, falsifiable claim: objectivity-
  by-redundancy and the classical pointer basis are the SAME compression/admissibility selection the
  agent runs in cognition. Measurement and mind select reality the same way. That identity is the
  deep test worth designing next; everything above it is corroborated re-description, honestly.
""")


if __name__ == "__main__":
    main()
