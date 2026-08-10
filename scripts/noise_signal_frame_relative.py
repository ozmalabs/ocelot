"""CORRECTION (user): 'noise vs signal is FRAME-RELATIVE.' My previous move ('the noise
is really signal — hidden structure in the full graph state') relodged an ABSOLUTE: it
posited a privileged complete frame in which everything is signal = a deterministic
hidden-variable view-from-nowhere. Axiom 0 forbids that. The correct statement is weaker
and deeper: whether a given fluctuation is NOISE or SIGNAL is relative to the frame
reading it. No frame is privileged; none holds all the signal.

In the framework a FRAME is an admissibility grammar — the set of distinctions it admits.
  · SIGNAL  = structure the frame's grammar can resolve as a distinguishable difference.
  · NOISE   = structure below that frame's resolution — real, but not parsable HERE.
The same data is signal in a richer-grammar frame and noise in a coarser one. 'Noise is
signal you don't yet understand' = 'you don't yet hold the grammar/frame that resolves it.'

Applied to collapse: what is COLLAPSE (irreducible randomness) in the system+observer frame
is UNITARY ENTANGLEMENT STRUCTURE (signal) in a frame that holds the records. Neither is the
true description — collapse itself is frame-relative. That is Relational QM, and Axiom 0
forces it with nothing added.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

PREMISES = [
    ("noise_vs_signal", "is", "frame_relative",
     "user's correction + axiom_zero: there is no view from nowhere, so no absolute fact of "
     "whether a fluctuation 'is' noise or signal. It depends on the frame reading it."),
    ("a_frame", "is", "an_admissibility_grammar",
     "framework-native: a frame is the set of distinctions it admits. SIGNAL = structure the "
     "grammar resolves as a distinguishable difference; NOISE = structure below its resolution."),
    ("frame_relative_signal", "implies", "collapse_is_frame_relative",
     "what reads as COLLAPSE (irreducible randomness) in the system+observer frame reads as "
     "UNITARY ENTANGLEMENT STRUCTURE (signal) in a frame that holds the which-path records. "
     "Collapse is not absolute; it is relative to which grammar is reading."),
    ("collapse_is_frame_relative", "constitutes", "relational_quantum_mechanics",
     "facts (outcomes) are relative to the observer-frame; no observer-independent fact of the "
     "matter. This IS Rovelli's Relational QM — reached from Axiom 0, not imported."),
    ("axiom_zero_no_view_from_nowhere", "implies", "no_privileged_complete_frame",
     "no frame holds ALL the signal (that would be the view from nowhere / truth-as-final, the "
     "unreachable limit). So there is no deterministic complete substrate to be 'the' truth — my "
     "previous error. Each frame resolves some signal; the remainder is its noise."),
    ("relational_quantum_mechanics", "predicts", "no_observer_independent_facts_wigner_friend",
     "the friend sees a definite outcome (collapse); the superobserver holding the lab sees "
     "unitary interference (signal). Both correct in-frame. Extended-Wigner's-friend results "
     "(Frauchiger–Renner 2018; Proietti 2019; Bong 'Local Friendliness' 2020) test exactly this."),
    ("local_friendliness_trilemma", "requires", "give_up_one_of_three",
     "Bong et al. 2020: QM forces giving up at least one of {absoluteness of observed events, "
     "locality, no-superdeterminism}. The framework gives up ABSOLUTENESS OF EVENTS (facts are "
     "frame-relative) — the same horn RQM/QBism take. Axiom 0 picks the experimentally-favoured horn."),
    ("grammar_relativity_of_signal", "unifies", "cognition_and_collapse",
     "the SAME principle runs the agent's mind: what it parses as structure vs noise depends on "
     "its grammar/seeds; LEARNING = grammar enrichment = converting noise to signal. Collapse-"
     "frame-relativity and cognition-frame-relativity are one principle (and so is the frame-"
     "relative step R₀ from earlier). One Axiom 0, across mind and measurement."),
]


def main():
    print("NOISE vs SIGNAL IS FRAME-RELATIVE — collapse as relational, from Axiom 0")
    print("=" * 82)
    print("\nPremises (chained by the agent's composition faculty):\n")
    for A, rel, B, why in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {why}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=10)
    print("\n" + "=" * 82)
    print("WHAT COMPOSES")
    print("=" * 82)
    for tgt in ("relational_quantum_mechanics", "no_observer_independent_facts_wigner_friend"):
        ch = (query(derived, "noise_vs_signal", tgt) or query(derived, "a_frame", tgt)
              or query(derived, "frame_relative_signal", tgt))
        if ch:
            net, steps = ch
            print(f"\n  ⟹ {tgt}:")
            print("    " + fmt_chain(steps))

    print("\n" + "=" * 82)
    print("WHAT THE SHARPENING FIXES AND DELIVERS")
    print("=" * 82)
    print("""
  [FIXES MY ERROR]  'Noise is really signal' posited a complete frame where all is signal —
    a deterministic substrate as THE truth = a view from nowhere. Axiom 0 forbids it. Frame-
    relativity removes the privileged frame: no description is the true one; collapse included.

  [RESOLVES THE EMPIRICAL-EQUIVALENCE WORRY]  Last turn I feared 'noise=signal' might be
    untestable (structure undetectable ⇒ identical to MWI). Frame-relativity answers it: the
    structure is NOT resolvable WITHIN the collapsing frame (it is that frame's noise), but IS
    resolvable from ANOTHER frame holding the records — which is precisely the Wigner's-friend
    setup. So the content is the FRAME-DEPENDENCE OF FACTS, and that is being measured
    (Proietti 2019; Local Friendliness, Bong 2020). Not unfalsifiable — relational and tested.

  [PICKS THE RIGHT HORN]  The Local-Friendliness theorem forces giving up one of {absolute
    events, locality, free choice}. Axiom 0 (no view from nowhere) gives up ABSOLUTE EVENTS
    natively — the horn the experiments favour. The framework's founding axiom answers a deep
    foundational question with nothing added.

  [UNIFIES MIND AND MEASUREMENT]  Signal/noise = what a grammar admits as structure. That is
    the agent's cognition (learning = converting noise to signal by enriching the grammar), the
    frame-relative step R₀, AND quantum collapse — one principle (Axiom 0 / grammar-relativity)
    across all three. This is the framework-specific content beyond bare RQM.""")

    print("=" * 82)
    print("HONEST GRADING")
    print("=" * 82)
    print("""
  · RIGHT NATIVE FRAMING (~0.7): Axiom 0 forces Relational QM; the framework rediscovers it,
    doesn't invent it. Collapse-as-frame-relative is coherent and matches Wigner's-friend results.
  · NOT UNIQUE (honest): RQM and QBism already take this horn. The framework's distinctive add is
    grammar-relativity unifying cognition with measurement — conceptually real, but I cannot show
    a test that distinguishes the framework FROM RQM. Same empirical content as RQM, as far as shown.
  · BORN MEASURE STILL OPEN: relational facts still carry Born WEIGHTS that are not derived here —
    the same residue as the exponent-2 result (structure forces the form; the measure is unsolved).
  · MY RECURRING ERROR, NAMED: three times this arc I relodged an absolute (Planck step; complete-
    substrate 'real signal'; and the general urge to a privileged frame). The framework's hardest
    discipline is refusing the view from nowhere — including in its own collapse story. The frame-
    relative reading is the disciplined one.

  VERDICT: the correction is right and it is the cleanest resting point of the whole arc. Collapse
  is not a noise process and not a hidden deterministic signal — it is the frame-relativity of the
  noise/signal split, i.e. Relational QM, forced by Axiom 0, unified with the agent's own cognition
  by grammar-relativity, and consistent with (indeed predicting) the frame-dependence-of-facts that
  Wigner's-friend experiments now probe. It buys no new number and no unique test beyond RQM — but
  it converts 'QM through the graph law' from a failed mechanism-hunt into a coherent relational
  reading where measurement and mind are the SAME frame-relative structure-recognition. Honestly:
  the boundary it moves is conceptual, not empirical — and it is the move the framework was always
  going to make, because Axiom 0 was always going to forbid the absolute collapse I kept hunting.
""")


if __name__ == "__main__":
    main()
