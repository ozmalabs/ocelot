"""'Noise is signal you don't yet understand.' (user) — applied to the wall the QM
investigation hit. The wall was: 'the SPATIAL LOCALISATION STRUCTURE of the collapse
NOISE — neither gravity nor cosmology supplies it.' Both imprints died the same death,
and the reframe says that sameness is DATA, not coincidence:

  · gravitational imprint: died because, as a NOISE field regularised at the nuclear
    scale, it radiated too much.
  · cosmological imprint: died because, as a NOISE field from a constant Λ, it was too
    SMOOTH to localise.
  BOTH deaths came from modelling collapse as an EXTERNAL STOCHASTIC NOISE FIELD and then
  hunting for its correlation length. The reframe: there is no noise field. What I called
  'the collapse noise' is SIGNAL — structure in the graph I had not decoded.

The framework was always built for this: it has no fundamental randomness. The graph is
DETERMINISTIC admissibility-rewriting; what looks like quantum 'noise' is the part of the
full graph state I coarse-grained away. So 'collapse noise' = the deterministic which-path
STRUCTURE the rest of the graph already holds (the records, the correlations). Decode it
as signal and the wall reorganises.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

PREMISES = [
    ("collapse_noise", "is", "which_path_structure_in_the_graph",
     "noise = signal-not-yet-understood. The agent has NO fundamental randomness "
     "(deterministic admissibility-rewriting); the 'noise' is graph structure I coarse-grained."),
    ("which_path_structure_in_the_graph", "is", "records_held_by_surrounding_matter",
     "the which-path information is a real RECORD — the configuration of whatever the particle "
     "has interacted with. It is signal, and it lives in matter, not in an abstract field."),
    ("records_held_by_surrounding_matter", "constitutes", "short_correlation_length_ell",
     "matter is localised at atomic scale ⇒ the distinguishing structure has SHORT range ℓ — "
     "exactly the scale the pinning rule (R₀=ℓ) gave. The short r_C was never missing; it is "
     "where the SIGNAL is."),
    ("short_correlation_length_ell", "constitutes", "r_C_equals_ell_rehabilitated",
     "so r_C = ℓ is PRINCIPLED, not a fallback: it is the scale of the which-path signal. The "
     "gravity/cosmology hunt failed because it sought a NOISE FIELD where there is structured SIGNAL."),
    ("noise_is_signal", "reframes", "collapse_as_structure_recognition",
     "collapse stops being a stochastic process and becomes the graph RECOGNISING which "
     "branch its own structure already records — a basin-hop on accumulated SIGNAL, not noise."),
    ("collapse_as_structure_recognition", "is", "analysis_by_synthesis_the_agent_already_runs",
     "this is the agent's native faculty: recognise structure invariant to serialisation, "
     "basin-hop when accumulated evidence(=signal) crosses the barrier. Collapse = recognition."),
    ("deterministic_graph", "implies", "randomness_is_epistemic",
     "if the substrate is deterministic, Born randomness is IGNORANCE of the full graph state, "
     "not dice. (A structured-hidden-variable reading; Bell is evaded by graph nonlocality — "
     "entanglement = a shared edge, derived earlier.)"),
    ("randomness_is_epistemic", "predicts", "the_noise_carries_decodable_structure",
     "the discriminating consequence: if the 'noise' is signal, it is NOT perfectly white — it "
     "carries correlations/non-Markovian structure. Fundamental-randomness models (GRW/CSL/DP) "
     "predict white noise; this predicts residual STRUCTURE. That is a real, if hard, test."),
]


def main():
    print("NOISE IS SIGNAL — re-reading the wall")
    print("=" * 80)
    print("\nPremises (the reframe, chained by the agent's composition faculty):\n")
    for A, rel, B, why in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {why}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=10)
    print("\n" + "=" * 80)
    print("WHAT COMPOSES")
    print("=" * 80)
    for tgt in ("r_C_equals_ell_rehabilitated", "the_noise_carries_decodable_structure"):
        ch = query(derived, "collapse_noise", tgt) or query(derived, "noise_is_signal", tgt)
        if ch:
            net, steps = ch
            print(f"\n  ⟹ {tgt}:")
            print("    " + fmt_chain(steps))

    print("\n" + "=" * 80)
    print("WHAT THE REFRAME DOES")
    print("=" * 80)
    print("""
  [DISSOLVES THE WALL]  The 'missing spatial structure' was never missing — I was hunting
    for a NOISE FIELD's correlation length when the localising thing is SIGNAL: the which-path
    record held by the surrounding matter, short-ranged because matter is. r_C = ℓ (the pinning
    rule) is rehabilitated as the PRINCIPLED answer, not a fallback. The gravity and cosmology
    deaths now read as one consistent message: stop modelling collapse as an external noise field.

  [RE-READS THE TWO FAILURES AS SIGNAL]  Both imprints died of the same cause — treating
    collapse as a stochastic field and asking for its correlation length (gravity: nuclear-scale
    field → too much radiation; cosmology: constant-Λ field → too smooth). The shared failure
    mode IS the signal: the field framing is wrong. The 'noise' in my own model was telling me it
    was signal.

  [REORIENTS COLLAPSE — and it becomes NATIVE]  Collapse = the graph RECOGNISING which branch
    its own structure records = analysis-by-synthesis + basin-hop on accumulated SIGNAL. That is
    the faculty the agent already runs everywhere else (recognise structure, hop the basin when
    evidence crosses the barrier). Collapse stops being foreign physics bolted on; it is the
    agent's own recognition dynamics applied to position.

  [A NEW, DISCRIMINATING DIRECTION]  If the 'noise' is signal, it must carry DECODABLE STRUCTURE
    — correlations, non-Markovianity — not be perfectly white. GRW/CSL/DP assume white fundamental
    noise; this predicts residual structure in collapse/decoherence fluctuations. In principle a
    discriminator. Hard, but real.""")

    print("=" * 80)
    print("HONEST COST — what this commits to, and the risk")
    print("=" * 80)
    print("""
  · IT IS AN INTERPRETATION MOVE. 'Noise is signal' makes Born randomness EPISTEMIC (ignorance
    of the full graph state) on a DETERMINISTIC substrate. That is a definite stance (structured
    hidden variables / deterministic substrate + decoherence), Bell-compatible only via graph
    nonlocality (the shared-edge entanglement). It is coherent, but it is a choice, not a proof.
  · THE MEASURE PROBLEM RETURNS AS TYPICALITY. Born |ψ|² must now come from typicality/counting
    over the untracked graph structure. Reframed as epistemic — still NOT derived. (Same residue
    as the exponent-2 work: structure forces the form, the measure is the open part.)
  · THE EMPIRICAL-EQUIVALENCE RISK. If the residual structure in the 'noise' is in practice
    undetectable, this view is empirically identical to decoherence + many-worlds and predicts
    nothing new — philosophically cleaner, experimentally silent. Its ONLY escape from that is
    the decodable-structure prediction above actually being measurable. That is the make-or-break.

  VERDICT: 'noise is signal' is the right correction. It dissolves the wall (the localising
  structure is signal in matter, r_C = ℓ, principled), re-reads both refutations as one coherent
  message (collapse is not a noise field), and makes collapse NATIVE to the agent (recognition,
  not dice) — at the cost of committing to a deterministic/epistemic reading whose new content
  lives entirely in one hard question: is there decodable structure in the 'noise'? That question
  is the live frontier the reframe opens, and it is sharper than the dead end it replaces.
""")


if __name__ == "__main__":
    main()
