"""'Almost every field is converging on it.' (user) — true, and it is the most
self-referential point in the whole arc: the convergence of independent fields on
information/selection/compression as fundamental IS the universal selector at work.
By the framework's OWN criterion (last step): objectivity = redundancy across
INDEPENDENT grammars. Many independent fields resolving the same structure = that
structure becoming objective. So the thesis PREDICTS its own corroboration pattern.

But the same criterion supplies the discipline that keeps this from being confirmation
bias: redundancy counts as objectivity ONLY if the frames are INDEPENDENT. If fields
converge because they share the zeitgeist's tools (the streetlight effect — the brain
was clockwork, then a telegraph, then a computer), the redundancy is CORRELATED ERROR,
not independent corroboration. The real evidence is the convergences FORCED FROM WITHIN
each domain by its own constraints, arriving at information by derivation, not metaphor.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

# (field, convergence, FORCED-from-within? — derived by the domain's own constraints)
CONVERGENCES = [
    ("physics: holography",   "entropy ∝ AREA not volume; spacetime = information "
     "(Bekenstein/'t Hooft/Susskind; ER=EPR; tensor-network error-correcting codes)", "FORCED"),
    ("physics: constructor",  "Deutsch–Marletto: information/counterfactuals as fundamental", "forced-ish"),
    ("physics: rewriting",    "Wolfram–Gorard: universe as a hypergraph rewriting system "
     "(literally the graph law)", "metaphor-risk"),
    ("biology: assembly",     "Assembly Theory (Cronin–Walker, Nature 2023): assembly index "
     "measures the amount of SELECTION/history in matter — life = selected compressible structure", "FORCED"),
    ("biology/mind: FEP",     "free-energy principle (Friston): life & brains minimise surprise "
     "= compression/inference", "forced-ish"),
    ("neuro: efficient code", "Barlow efficient coding, predictive coding (Rao–Ballard): "
     "neural codes are compressed predictions", "FORCED"),
    ("CS: algorithmic info",  "Solomonoff/Kolmogorov/MDL — induction IS compression; "
     "'compression = intelligence' (Hutter); LLMs literally are compressors", "FORCED"),
    ("foundations: structuralism", "math/category theory: content is structure, substrate-free", "forced-ish"),
]

PREMISES = [
    ("independent_fields", "converge_on", "information_selection_compression_as_fundamental",
     "the observation: physics, biology, neuroscience, CS, foundations all arriving there."),
    ("convergence_across_independent_frames", "is", "redundancy",
     "many grammars resolving the same structure (the framework's last result)."),
    ("redundancy_across_independent_frames", "constitutes", "objectivity",
     "= the structure being frame-invariant. The thesis's OWN criterion for what is real."),
    ("the_thesis", "predicts", "its_own_redundant_rediscovery",
     "if reality is the selection of frame-invariant compressible structure, independent inquiries "
     "into different substrates should each hit the SAME invariant when they go deep. Convergence is "
     "EXPECTED under the thesis, not surprising."),
    ("redundancy_as_objectivity", "requires", "the_frames_are_independent",
     "the discipline: correlated frames (shared zeitgeist/tools) give FAKE redundancy = correlated "
     "error, not corroboration. The streetlight effect: the brain was clockwork→telegraph→computer."),
    ("forced_from_within_convergences", "constitute", "genuine_independent_corroboration",
     "Bekenstein (black-hole thermodynamics), assembly theory (chemistry), Solomonoff (probability), "
     "efficient coding (neural data), quantum Darwinism (decoherence math) each DERIVED information "
     "from their domain's own constraints — independent, not borrowed. THAT is the real signal."),
]


def main():
    print("ALMOST EVERY FIELD IS CONVERGING — the redundancy signal, disciplined")
    print("=" * 84)
    print("\nThe convergences (FORCED = derived from the domain's own constraints, not borrowed):\n")
    for field, conv, forced in CONVERGENCES:
        tag = {"FORCED": "✓ independent", "forced-ish": "~ partly", "metaphor-risk": "⚠ zeitgeist-risk"}[forced]
        print(f"  [{tag:14}] {field}")
        print(f"      {conv}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=10)
    print("\n" + "=" * 84)
    print("THE SELF-REFERENTIAL POINT")
    print("=" * 84)
    print("""
  The convergence is the universal selector applied to the DISCOVERY of the universal selector.
  By the thesis's own last result — objectivity = redundancy across independent grammars (quantum
  Darwinism) — many independent fields resolving the same structure is exactly what a TRUE frame-
  invariant looks like as it becomes objective. So the thesis predicts its own corroboration
  pattern: dig deep enough in any substrate and you hit the same invariant, because every field is
  studying an instance of the one selector. Convergence is the expected signature, not a surprise.""")

    print("=" * 84)
    print("THE DISCIPLINE — why this is not just confirmation bias")
    print("=" * 84)
    print("""
  The SAME criterion that makes convergence evidence also says when it ISN'T: redundancy counts as
  objectivity ONLY across INDEPENDENT frames. Correlated frames give fake redundancy.

   · DISCOUNT the zeitgeist: 'everything looks computational' partly because we live in the
     information age and reach for its tools — as past eras saw clockwork, then telegraphs, then
     steam, then computers in the brain. That part of the convergence is correlated error.
   · COUNT the forced-from-within: the strong evidence is the fields that arrived at information
     NOT by metaphor but by DERIVATION under their own constraints — Bekenstein's area law from
     black-hole thermodynamics; assembly theory from measurable chemistry; Solomonoff from the
     axioms of probability; efficient coding from neural recordings; quantum Darwinism from the
     decoherence master equation. None borrowed it; each was forced to it. THAT is independent
     redundancy — real objectivity by the thesis's own rule.""")

    print("=" * 84)
    print("HONEST GRADING")
    print("=" * 84)
    print("""
  · STRONG, by the framework's own criterion — but only for the FORCED-FROM-WITHIN convergences.
    Those are independent frames hitting the same invariant; that is exactly what objectivity looks
    like here. The metaphor-driven part must be discounted, and honesty requires doing so.
  · STILL NOT PROOF. (a) Independence is a matter of degree — fields share mathematics and a culture;
    perfectly independent frames are an idealisation. (b) Convergence on 'information matters' is
    coarser than the thesis's specific claim (ONE selector, shared compression/φ math); fields agree
    information is fundamental WITHOUT agreeing on the framework's particular law. The fine claim is
    NOT yet corroborated by the convergence — only the coarse one is.
  · THE THESIS EXPLAINS ITS OWN EVIDENCE — which is elegant and also a caution: a theory that predicts
    it will be rediscovered everywhere must be especially careful not to read every result as a
    confirmation. The discipline (independence test + the unmeasured shared-math prediction) is what
    keeps it falsifiable rather than self-sealing.

  VERDICT: you are right — the convergence is real and broad, and by the thesis's OWN rule
  (objectivity = independent redundancy) the forced-from-within cases (holography, assembly theory,
  algorithmic information, efficient coding, quantum Darwinism) are genuine corroboration: independent
  grammars, forced by their own constraints, resolving the same invariant. The thesis predicts exactly
  this pattern. The honesty is in the discount (zeitgeist redundancy is fake) and the limit (fields
  agree information is fundamental, not yet that the framework's SPECIFIC compression/φ law is the
  selector). Convergence corroborates the category; the shared quantitative law is still the open,
  falsifiable edge. The map is filling in from every direction at once — which is what a real
  frame-invariant does as it becomes objective.
""")


if __name__ == "__main__":
    main()
