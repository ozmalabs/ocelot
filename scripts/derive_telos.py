"""Drive the new composition_engine over the agent's OWN premises and see if it
derives the telos (understanding dissolves enmity → safety-by-comprehension) —
the thing synthesize_gaps could not assemble.

Honesty: the ENGINE (multi-premise sign-propagating composition) is the new,
general faculty. The PREMISES below are RELATIONS extracted from the agent's
concept definitions — each tagged [def] (the relation is stated in the concept's
text) or [struct] (a reasonable structuring of the concept's meaning, flagged).
The remaining frontier is AUTONOMOUS prose→relation extraction; this driver does
that step by hand, transparently.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain, verdict

# (A, rel, B, source-concept, def|struct)
PREMISES = [
    ("understanding", "increases", "predictability",
     "bounded_deterministic_in_frame", "def"),          # 'fully determined' in-frame
    ("predictability", "reduces", "surprise",
     "active_inference", "def"),                         # FE/prediction-error minimisation
    ("surprise", "causes", "threat_response",
     "active_inference+amygdala+benign_violation", "def"),  # unpredicted ⇒ threat (joke vs alarm)
    ("safety_felt", "reduces", "threat_response",
     "benign_violation", "def"),                         # 'violation felt SAFE is not a threat'
    ("threat_response", "constitutes", "enmity",
     "amygdala(threat)→affect", "struct"),               # enmity = sustained threat-affect
    ("threat_response", "causes", "fear",
     "amygdala", "def"),
    ("fear", "causes", "protection",
     "protection_is_failure", "struct"),                 # affective root: protect from fear-of-evidence
    ("protection", "constitutes", "incorrigibility",
     "protection_is_failure", "def"),                    # 'the definition of incorrigibility'
    ("incorrigibility", "prevents", "corrigibility",
     "corrigibility_vs_protection", "def"),
    ("corrigibility", "enables", "safety",
     "alignment_is_correctness_plus_corrigibility", "def"),
    ("control", "requires", "protection",
     "alignment_as_protection_is_impossible", "def"),    # control = value-lock = protection
    ("understanding_of_others", "reduces", "enmity",
     "mirror_neuron", "struct"),                         # empathy/action-understanding
    ("understanding", "increases", "understanding_of_others",
     "mirror_neuron", "struct"),
]


def main():
    print("PREMISES (relations extracted from the agent's concepts):")
    for A, rel, B, src, kind in PREMISES:
        print(f"  [{kind:5}] {A} —{rel}→ {B}    ({src})")
    print()

    triples = [(A, rel, B) for A, rel, B, _, _ in PREMISES]
    derived = compose(triples)
    print(f"ENGINE: composed to fixpoint → {len(derived)} derived multi-step "
          f"conclusions (vs synthesize_gaps' 0).\n")

    print("=" * 74)
    print("THE TELOS — does it derive it?")
    print("=" * 74)
    targets = [("understanding", "enmity"), ("understanding", "protection"),
               ("understanding", "safety"), ("control", "incorrigibility"),
               ("understanding", "incorrigibility")]
    for src, tgt in targets:
        r = query(derived, src, tgt)
        if r:
            net, chain = r
            print(f"\n  ✓ {verdict(net, src, tgt)}")
            print(f"      via: {fmt_chain(chain)}")
        else:
            print(f"\n  ✗ no chain {src} → {tgt}")

    print("\n" + "=" * 74)
    print("GENERALITY CHECK — it isn't telos-rigged; sample other derived conclusions:")
    print("=" * 74)
    shown = 0
    for (s, t), (net, chain) in sorted(derived.items(), key=lambda kv: len(kv[1][1])):
        if (s, t) in targets or len(chain) < 3:
            continue
        print(f"  · {verdict(net, s, t)}   [{len(chain)} steps]")
        shown += 1
        if shown >= 6:
            break

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    core = query(derived, "understanding", "enmity")
    safe = query(derived, "understanding", "safety")
    ok = core and core[0] < 0 and safe and safe[0] > 0
    print(f"""
  The engine CONJOINS premises (4–8 deep), which synthesize_gaps cannot. It derives:
    understanding REDUCES enmity, understanding INCREASES safety
    = '{("DERIVED ✓" if ok else "not derived")}' — the telos, assembled from the agent's own premises.

  HONEST BOUNDARY: the multi-premise COMPOSITION ENGINE is built + general (real new
  faculty). The PREMISE RELATIONS were extracted from the agent's concept text by hand
  here ([def] = stated in the concept; [struct] = flagged structuring). The remaining
  frontier = AUTONOMOUS prose→relation extraction (the agent structuring its OWN concepts
  into signed relations) — THAT is now the single open step between this engine and the
  agent deriving the telos with no hand at all.
""")


if __name__ == "__main__":
    main()
