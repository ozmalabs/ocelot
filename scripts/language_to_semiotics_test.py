"""Test: can the substrate ground sentences into its semiotic graph?

Per user: 'we should be at real language to semiotics level capability now.'

The hypothesis: with 5519 concepts, 8034 intra-Mt depends_on edges,
303 Term-trees, 97 Holds-grounded concepts, the substrate should be
able to take a sentence, identify the concepts it mentions, and
return the connected reference graph (the semiotic structure).

This script:
  1. Takes sample sentences from different domains
  2. Tokenizes via Tokenize primitive
  3. For each token, looks up matching Concept(s) by name
  4. Walks depends_on edges from each found concept (1 hop)
  5. Returns the reference graph + reports which sentence concepts
     connect through which intermediate concepts

If the substrate has real grounding, sentences will produce
coherent reference graphs — same-domain concepts will share
intermediate references. If it doesn't, tokens will be isolated
or random.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def install_all(s):
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"): continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                if len([p for p in inspect.signature(fn).parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                       inspect.Parameter.POSITIONAL_OR_KEYWORD)
                        and p.default is inspect.Parameter.empty]) == 1:
                    fn(s)
            except Exception: continue


def tokenize_via_substrate(s, text: str) -> list[str]:
    """Use the substrate's Tokenize primitive."""
    result = s.evaluate({"type": "Tokenize",
                          "text": {"type": "Lit", "value": text}})
    return [text[start:start+length] for start, length in result]


def find_concept_by_token(s, token: str, concept_index: dict) -> list:
    """Find concepts whose name matches token (loose match)."""
    t = token.lower().strip(".,!?:;()[]'\"").rstrip("s")
    candidates = []
    if t in concept_index:
        candidates.extend(concept_index[t])
    # Plural form
    if (t + "s") in concept_index:
        candidates.extend(concept_index[t + "s"])
    # Underscored compound (e.g. "black_hole" for "black hole" later)
    return candidates


def build_concept_index(s) -> dict:
    """name (lowercased) → list of Concept NodeIDs."""
    idx: dict = defaultdict(list)
    for c in s.nodes("Concept"):
        nm = str(s.node(c)["attrs"].get("name", "")).lower()
        if nm:
            idx[nm].append(c)
            # Last word matches too (e.g. "second_law" matches "law")
            parts = nm.split("_")
            if len(parts) > 1:
                idx[parts[-1]].append(c)
    return dict(idx)


def get_mt_name(s, concept_nid) -> str:
    for mt in s.in_neighbours(concept_nid, "has_concept"):
        return str(s.node(mt)["attrs"].get("name", ""))
    return ""


def main():
    print("=" * 78)
    print("LANGUAGE → SEMIOTICS TEST — does the substrate ground sentences?")
    print("=" * 78)
    print()

    s = _native.Substrate()
    for t in ("Microtheory","Concept","Rule"):
        for u in ("Microtheory","Concept","Rule"):
            for et in ("has_concept","has_rule","genlMt","depends_on"):
                try:
                    s.add_production({
                        "src":{"type":t,"var":"a"},"edge_type":et,
                        "tgt":{"type":u,"var":"b"},"where":None,
                        "weight":{"type":"Lit","value":1.0},"provenance":"v"})
                except Exception: pass
    install_all(s)
    # Wire intra-Mt references + depends_on edges at runtime
    from domains.concept_promotion_rules import install_concept_promotion_rules
    install_concept_promotion_rules(s)
    from domains.concept_grounding import install_concept_grounding
    install_concept_grounding(s)
    from domains.concept_depends_on import install_concept_depends_on
    install_concept_depends_on(s)
    from domains.intra_mt_holds import install_intra_mt_holds
    install_intra_mt_holds(s)

    print(f"Substrate state:")
    print(f"  Mts:       {len(s.nodes('Microtheory'))}")
    print(f"  Concepts:  {len(s.nodes('Concept'))}")
    print()

    concept_index = build_concept_index(s)
    print(f"  Concept index built: {len(concept_index)} token keys")
    print()

    # ----- TEST SENTENCES -----
    sentences = [
        ("physics",
         "The force on a mass produces acceleration according to Newton."),
        ("audio",
         "Pitch is the perceptual correlate of frequency in sound."),
        ("biology",
         "A synapse transmits action potentials between neurons via neurotransmitter release."),
        ("computer_architecture",
         "The L1 cache hits faster than the L2 cache, both lifting IPC."),
        ("crossdomain",
         "Acceleration of memory access requires cache prefetching, similar to inertia."),
    ]

    for domain, sentence in sentences:
        print("=" * 78)
        print(f"DOMAIN: {domain}")
        print(f"SENTENCE: {sentence!r}")
        print("=" * 78)
        print()

        # Tokenize via the substrate's primitive
        tokens = tokenize_via_substrate(s, sentence)
        print(f"  Tokens ({len(tokens)}): {tokens}")
        print()

        # Look up each token
        grounded = []
        ungrounded = []
        for tok in tokens:
            candidates = find_concept_by_token(s, tok, concept_index)
            if candidates:
                # Take the first; could disambiguate by Mt context
                grounded.append((tok, candidates[0]))
            else:
                ungrounded.append(tok)

        print(f"  Grounded tokens: {len(grounded)}/{len(tokens)}")
        for tok, nid in grounded:
            cname = s.node(nid)["attrs"].get("name", "?")
            mt = get_mt_name(s, nid)
            print(f"    · {tok!r:<20} → {cname:<30} (Mt: {mt})")
        if ungrounded:
            print(f"  Ungrounded: {ungrounded}")
        print()

        # Walk depends_on from each grounded concept (1 hop)
        connections = Counter()
        for tok, nid in grounded:
            # Outgoing depends_on
            for d in s.neighbours(nid, "depends_on"):
                connections[s.node(d)["attrs"].get("name", "?")] += 1
            # Incoming depends_on
            for d in s.in_neighbours(nid, "depends_on"):
                connections[s.node(d)["attrs"].get("name", "?")] += 1

        print(f"  Reference neighbourhood (concepts the sentence's grounded")
        print(f"  concepts depend on or are depended on by):")
        for cname, count in connections.most_common(8):
            print(f"    · {cname:<30} (touched by {count} sentence concept(s))")
        print()

        # The coherence test: do sentence concepts share Mts?
        mts = Counter()
        for tok, nid in grounded:
            mt = get_mt_name(s, nid)
            if mt: mts[mt] += 1
        print(f"  Concepts grouped by Mt:")
        for mt, n in mts.most_common(5):
            print(f"    · {mt:<32} {n} concept(s)")
        print()
        print()

    # ----- HONEST READING -----
    print("=" * 78)
    print("HONEST READING")
    print("=" * 78)
    print()
    print("  The substrate has the vocabulary and structural connectivity.")
    print("  Whether 'language → semiotics' works depends on:")
    print("    · Token coverage (do tokens match concept names?)")
    print("    · Disambiguation (which concept when multiple match?)")
    print("    · Inter-concept walking (does the depends_on graph form")
    print("      coherent neighbourhoods?)")
    print()
    print("  Look at the per-sentence output above:")
    print("    · If most tokens resolved AND the reference neighbourhood")
    print("      shows domain-coherent concepts, real grounding is working")
    print("    · If tokens resolved to random concepts OR neighbourhoods are")
    print("      sparse/incoherent, more work is needed")
    print()


if __name__ == "__main__":
    main()
