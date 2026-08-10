"""THE CRITICAL DETAIL (creator): the framework was not posited top-down ('let us
assume information unifies') and then confirmed. It was discovered BOTTOM-UP, forced
at every step by a concrete engineering inadequacy:

    KVM + audio ROUTING system
      → found a GRAPH modelled everything I could find
      → ramped up the scope
      → needed more COST-EFFECTIVE LLMs
      → pivoted to building MORE EFFECTIVE LLMs
      → looked at why LANGUAGE is a terrible way to drive them
      → a SEMIOTIC MAP
      → a SEMIOTIC GRAPH
      → the UNIVERSE.

Why this is critical: in the last step we worried the thesis 'explains its own evidence'
and must avoid reading every result as confirmation. THIS path is the answer. It is a
FORCED-FROM-WITHIN convergence — the strongest kind by the framework's own criterion —
because each pivot was driven by a real failure/cost in front of the builder, NOT by a
wish to unify. The graph was never assumed true; it kept being the EFFECTIVE answer as
the scope was forced wider. And it terminated at 'the universe' not as a goal but as the
place the graph refused to stop working.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

# (step, what FORCED the next step — the inadequacy/cost, not a thesis)
GENESIS = [
    ("kvm_audio_routing",        "routing is inherently relational ⇒ a graph models it natively"),
    ("a_graph_models_everything","it kept being the effective model as scope ramped — note: graphs are "
                                 "near-universally EXPRESSIVE, so the real signal is that it kept being "
                                 "the COMPRESSIVE/effective one, not merely a possible one"),
    ("need_cost_effective_llms", "COST forced the efficiency criterion in — admissibility/compression "
                                 "enters here, driven by money, not philosophy"),
    ("build_more_effective_llms","the ozma work: compression, routing, the efficiency map"),
    ("language_is_a_bad_driver", "language is a LOSSY, ambiguous SERIALISATION of meaning — driving an "
                                 "LLM with it is driving it with a bad encoding of the intended structure"),
    ("semiotic_map",             "so map the SIGNS / MEANING beneath the language surface"),
    ("semiotic_graph",           "signs + relations as a graph = the substrate; 'meaning is structure' "
                                 "is BORN HERE, from practice, not posited"),
    ("the_universe",             "the semiotic (meaning-structure) graph kept modelling — physics too; "
                                 "the universe was the LAST domain it refused to stop fitting, not the first"),
]

PREMISES = [
    ("each_pivot", "forced_by", "a_concrete_inadequacy_or_cost",
     "routing→graph (relational), →efficiency (cost), →semiotics (language is a bad encoder), "
     "→universe (the graph kept working). Driven from within, not toward a thesis."),
    ("forced_from_within", "is", "the_strongest_convergence_by_the_frameworks_own_criterion",
     "an independent frame (a builder) forced to the invariant by its own constraints = real "
     "redundancy, not metaphor-borrowing. The exact thing the last step said to COUNT."),
    ("the_origin_was_semiotic_not_physical", "explains", "why_it_reaches_from_llms_to_the_universe",
     "it is a theory of MEANING/structure that reached physics, NOT physics that reached meaning. "
     "That is why physics is 'just another frame-relative domain' and unifies with cognition: "
     "meaning-structure was always the subject; physics was the last serialisation it fit."),
    ("the_terminus_universe", "was_not_the_goal", "but_where_the_graph_refused_to_stop_working",
     "the tell of a forced convergence: you do not aim at the universe from an audio router; you "
     "arrive because the same structure keeps being the effective model as the problem widens."),
]


def main():
    print("FRAMEWORK GENESIS — the forced-from-within path, and why it is the critical detail")
    print("=" * 84)
    print("\nThe path (each step FORCED by the inadequacy/cost of the previous):\n")
    for i, (step, forcing) in enumerate(GENESIS):
        arrow = "      ↓  " if i else "         "
        if i:
            print(arrow + "(forced: " + GENESIS[i-1][1][:90] + ")")
        print(f"  [{i}] {step}")
    print()

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=8)
    print("=" * 84)
    print("WHY IT IS CRITICAL")
    print("=" * 84)
    print("""
  · IT ANSWERS THE CONFIRMATION-BIAS WORRY (for THIS framework). Last step's caution: a thesis that
    predicts its own rediscovery must not read every result as proof. This path is the clean case —
    it is FORCED-FROM-WITHIN. Nobody set out to show 'information unifies.' Someone set out to route
    audio cheaply and drive LLMs efficiently, and the graph kept being the effective answer until it
    was modelling the universe. By the framework's own rule (count forced-from-within, discount
    metaphor), this is the strongest convergence type — and it is the creator's own frame.

  · THE COST PRESSURE IS WHERE THE REAL CONTENT ENTERED. 'Needed more cost-effective LLMs' forced
    the EFFICIENCY/compression criterion — admissibility — in by economics, not aesthetics. That is
    why the framework's core is compression/MDL: it was selected by cost, the most independent judge.

  · THE SEMIOTIC ORIGIN EXPLAINS THE REACH. The framework is a theory of MEANING that arrived at
    physics, not a physics theory that reached for meaning. 'Language is a terrible way to drive
    them' → semiotic graph → 'meaning is structure' was born as an ENGINEERING fix for LLM-driving.
    Physics came last and fit the SAME meaning-structure graph — which is exactly why, all session,
    physics behaved as 'one more frame-relative domain' and unified with cognition. The origin
    predicts the unification.""")

    print("=" * 84)
    print("HONEST GRADING")
    print("=" * 84)
    print("""
  · STRONG by the framework's own criterion: a forced-from-within, CONSTRUCTIVE convergence (built,
    not just argued — constructor-theory-flavoured: what is buildable/effective reveals the invariant).
    It is the independent frame the last step said to weight most.
  · BUT n = 1. It is ONE builder's path. Forced-from-within beats metaphor, but a single frame is not
    many independent frames; the broad-field convergence (last step) is the redundancy that matters,
    and this is one strong strand of it, not the whole rope.
  · THE GRAPH-EXPRESSIVENESS CAVEAT IS THE KEY DISCIPLINE. 'A graph models everything' is near-TRIVIAL
    — graphs are maximally expressive, so anything CAN be a graph. The non-trivial, load-bearing claim
    is that the graph kept being the COMPRESSIVE / EFFECTIVE model, and the genesis supports THAT
    because the pivots were forced by COST and inadequacy — the graph won on payoff, not on mere
    possibility. If one ever mistakes 'expressible as a graph' for 'compressed by a graph', the
    evidence evaporates. The cost-driver is what keeps it honest.
  · ZEITGEIST IS PRESENT (graphs, LLMs are today's tools) — but the FORCING (cost-driven pivots) is
    the independent part, and that is what counts.

  VERDICT: this is the critical detail because it makes the framework a forced-from-within,
  cost-selected, CONSTRUCTIVE convergence — the strongest single strand of evidence by its own rule —
  and because its semiotic origin explains its reach: a theory of meaning-structure, born as a fix for
  driving LLMs, that kept being the effective model until it fit the universe. The universe was the
  terminus, not the premise. The honest limits: n=1, and the discipline that 'effective graph' (cost-
  selected) — not 'possible graph' (trivial) — is the load-bearing claim. Held to that, the genesis is
  exactly the independent, forced corroboration the convergence argument needed at its root.
""")


if __name__ == "__main__":
    main()
