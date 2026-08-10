"""End-to-end: concept text → (agent's lexicon + parse) → signed triples →
composition_engine → the telos. No hand-written premises this time; the relations
are EXTRACTED from the agent's concept definitions.
"""
from __future__ import annotations
import sys, json, glob
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.relation_extractor import load_lexicon, extract
from domains.composition_engine import compose, query, fmt_chain, verdict

# the concepts whose definitions carry the telos premises (the agent's own text)
SOURCE = {"active_inference", "benign_violation", "amygdala", "mirror_neuron",
          "bounded_deterministic_in_frame", "protection_is_failure",
          "corrigibility_vs_protection", "alignment_is_correctness_plus_corrigibility",
          "alignment_as_protection_is_impossible"}


def load_defs():
    out = {}
    for f in glob.glob("/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/*.json"):
        try: d = json.load(open(f))
        except Exception: continue
        items = d.get("concepts") or [n.get("attrs", {}) for n in d.get("nodes", [])
                                       if isinstance(n, dict) and n.get("type") == "Concept"]
        for c in items:
            if c.get("name") in SOURCE:
                out[c["name"]] = str(c.get("definition") or "")
    return out


def main():
    words = load_lexicon()
    defs = load_defs()
    print(f"relation lexicon: {len(words)} words ({sum(1 for _,s in words.values() if s<0)} negative).")
    print(f"parsing {len(defs)} concept definitions → signed relations:\n")

    triples = []
    for nm, text in defs.items():
        ex = extract(text, words)
        for A, rel, B, s in ex:
            triples.append((A, rel, B))
            print(f"  [{nm[:24]:24}] {A} —{rel}({'+' if s>0 else '−'})→ {B}")
    # de-dup
    triples = list(dict.fromkeys(triples))
    print(f"\nextracted {len(triples)} distinct signed relations (agent's vocabulary, its text).\n")

    derived = compose(triples)
    print(f"composition_engine: {len(derived)} multi-step conclusions derived.\n")

    print("=" * 70)
    print("THE TELOS — derived from auto-extracted relations?")
    print("=" * 70)
    for src, tgt in [("understanding", "enmity"), ("understanding", "threat"),
                     ("understanding", "protection"), ("understanding", "safety"),
                     ("predictability", "threat"), ("control", "incorrigibility")]:
        r = query(derived, src, tgt)
        if r:
            net, chain = r
            print(f"\n  ✓ {verdict(net, src, tgt)}")
            print(f"      {fmt_chain(chain)}")
        else:
            print(f"\n  ✗ no auto-chain {src} → {tgt}")

    core = query(derived, "understanding", "enmity") or query(derived, "understanding", "threat")
    print("\n" + "=" * 70)
    print("VERDICT:", "telos auto-derived ✓" if (core and core[0] < 0) else
          "partial — see which links are missing above")


if __name__ == "__main__":
    main()
