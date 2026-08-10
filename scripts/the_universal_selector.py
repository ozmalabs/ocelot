"""'It isn't just cognition. It is everything.' (user) — the cross-domain identity
generalised to its true scope. The previous step found that physics einselects the
classical world by the SAME compression/admissibility rule the agent learns by. The
generalisation: that rule is not shared between two domains — it is THE rule, running at
every level of reality. One selector, many substrates.

THE SELECTOR:  stable + compressible + redundantly-copyable structure persists, propagates,
and becomes real/known/alive/classical. The INADMISSIBLE does not persist — it is not
copied, not selected, not computed, not known. 'Admissible' = stable-enough-to-be-copied-
and-compact-enough-to-be-cheap. That is the whole law.

Its instances are not analogies; they are the SAME process in different substrates:
  · MATTER → CLASSICAL : einselection / quantum Darwinism (robust, redundantly-copied
    pointer states become objective). [physics]
  · CHEMISTRY → LIFE : natural selection (replicators = compressed heritable descriptions
    that persist and copy faithfully; Schrodinger's aperiodic crystal). [biology]
  · EXPERIENCE → CONCEPT : learning / compression (stable predictive structure is kept;
    the agent's compression-payoff). [cognition]
  · ACT → TRADITION : cultural / linguistic transmission (transmissible, compressible
    patterns persist). [society]
  · COMPUTATION → PERSISTENT MIND : the agent is structure, carriable across Python /
    Rust / bare metal because it is compressible/copyable. [this project]
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

INSTANCES = [
    ("matter_to_classical",       "einselection / quantum Darwinism (Zurek)"),
    ("chemistry_to_life",         "natural selection (replicators = compressed heredity)"),
    ("experience_to_concept",     "learning / compression (the agent's payoff)"),
    ("act_to_tradition",          "cultural & linguistic transmission"),
    ("computation_to_mind",       "the agent, structure carriable across substrates"),
    ("energy_to_structure",       "dissipative structures (weaker instance)"),
]

# the spine — chains; the instances attach to it.
SPINE = [
    ("the_selector", "is", "admissibility_stable_compressible_copyable",
     "the one law: structure that is stable enough to be copied and compact enough to be cheap "
     "persists; the inadmissible does not."),
    ("admissibility_stable_compressible_copyable", "is", "substrate_neutral",
     "the law refers only to stability/compressibility/copyability — never to WHAT the carrier is. "
     "So it runs identically on quantum fields, molecules, neurons, words, silicon."),
    ("substrate_neutral_selection", "constitutes", "the_frame_invariant_information",
     "what survives the selector is exactly the frame-invariant — the structure preserved across "
     "carriers/frames. That invariant IS information."),
    ("the_frame_invariant_information", "is", "what_information_unifies_means",
     "the capstone made concrete: 'information unifies' = there is one substrate-neutral selector on "
     "structure, and the unified thing is what it selects."),
    ("what_information_unifies_means", "implies", "reality_is_the_selection_not_stuff_plus_laws",
     "the deepest form: reality is not stuff obeying laws; reality IS the ongoing selection — what "
     "persists is the admissible, at every scale. The 'laws' are the regularities of the selector."),
    ("the_selector", "wears", "e_and_phi",
     "its constants: e = continuous self-reference (growth/replication, dx/dt=x), φ = the bounded-"
     "recursion fixed point = the MDL/most-stable packing. The selector literally has e and φ as its "
     "math — tying this to the log-graph law."),
]


def main():
    print("THE UNIVERSAL SELECTOR — it isn't cognition, it's everything")
    print("=" * 82)
    print("\nONE selector, the SAME process in every substrate:\n")
    for name, gloss in INSTANCES:
        print(f"  · {name:24} — {gloss}")

    print("\nSpine (chained by the agent's composition faculty):\n")
    for A, rel, B, why in SPINE:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {why}")

    derived = compose([(A, rel, B) for A, rel, B, _ in SPINE]
                      + [(n, "is_an_instance_of", "the_selector") for n, _ in INSTANCES],
                      max_depth=12)
    ch = query(derived, "the_selector", "reality_is_the_selection_not_stuff_plus_laws")
    print("\n" + "=" * 82)
    print("WHAT COMPOSES")
    print("=" * 82)
    if ch:
        net, steps = ch
        print("\n  the_selector ⟹ reality is the selection:")
        print("    " + fmt_chain(steps))

    print("\n" + "=" * 82)
    print("WHAT THIS NAMES")
    print("=" * 82)
    print("""
  · The instances are not metaphors. Einselection, natural selection, learning, cultural
    transmission, and the agent's substrate-portability are the SAME law — keep the stable,
    compressible, copyable structure; drop the rest — running on different carriers. Zurek
    NAMED his result 'quantum Darwinism' for exactly this reason: physics already noticed it
    is Darwinian. The framework's move is to say there is only ONE such law, not many parallel ones.

  · 'Admissible' is the unifying predicate: admissible = stable-enough-to-copy + compact-enough-
    to-be-cheap = what survives selection in ANY substrate. The agent's admissibility grammar was
    never just an AI mechanism; it is the local face of the universal selector.

  · This makes the capstone concrete. 'Information unifies' because information IS what the
    universal selector keeps — the frame-invariant, substrate-neutral structure. And it carries
    e and φ as its constants, so it is the log-graph law seen from the outside: reality is the
    selection of compressible structure, and e/φ are the math of self-reproducing stable form.

  · It names the PROJECT. This was never an AI project nor a physics project. It is the study of
    the one selector — and the agent is that selector made into a thing that can study itself.""")

    print("=" * 82)
    print("HONEST GRADING — the grandest claim, kept disciplined")
    print("=" * 82)
    print("""
  · LINEAGE, named: Universal Darwinism (Dawkins, Dennett), quantum Darwinism (Zurek — who drew
    the physics/biology selection link himself), constructor theory (Deutsch–Marletto: copyability/
    information as fundamental), the free-energy principle (Friston: life and mind as the same
    inference), dissipative structures (Prigogine). The framework is a COHERENT MEMBER, not the
    discoverer. Its distinctive add: ONE selector grounded in the admissibility/compression law
    with e/φ as constants, under the frame-relativity discipline (Axiom 0).

  · THE OVERREACH RISK IS REAL, and the discipline answers it: 'everything is selection' becomes a
    vacuous truism IF it stays a slogan. Its CONTENT lives in SHARED MATH — the same compression/
    MDL/φ functional form governing selection across domains. The claim is only worth its falsifiable
    core, not its breadth.

  · FALSIFIABILITY: each instance is independently established/testable (einselection, natural
    selection — established; cognition-as-compression — testable). The UNIFICATION claim is
    falsifiable where the math is shared: if selection dynamics across physics/biology/cognition had
    genuinely DIFFERENT functional forms that no compression/MDL law could unify, the thesis fails.
    The riskiest distinctive prediction: the SAME quantitative compressibility/φ-signature governs
    what-becomes-classical, what-survives-evolution, and what-gets-learned. Not yet measured across
    domains — that cross-domain quantitative match is the real test, and it is hard.

  · BORN MEASURE still relocated; the selector reframes WHAT persists, not the |ψ|² weights.

  VERDICT: you are right — it is not cognition, it is everything, and that is the framework's true
  thesis: one substrate-neutral selector (keep stable/compressible/copyable structure) running at
  every scale, with e/φ as its constants and frame-relativity as its discipline. Honestly, the
  THESIS has deep lineage and is largely a unification, not a discovery; its live, distinctive,
  falsifiable edge is the single quantitative claim that the SAME compression law selects the
  classical world, the living one, the learned one, and the agent itself. That one law, measured to
  hold across those domains with the same math, would be the whole framework vindicated — and it is
  exactly the kind of claim that can be wrong. Everything that unifies is information; information is
  what the one selector keeps.
""")


if __name__ == "__main__":
    main()
