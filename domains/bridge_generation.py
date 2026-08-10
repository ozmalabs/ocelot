"""bridge_generation — the ABDUCTIVE faculty: hypothesize connecting relations
that NO text states, from principled moves. Output is HYPOTHESES (low confidence,
defeasible), never facts — so a conclusion resting on abduced bridges inherits the
weakest confidence in its chain. This is what was missing: extraction returns only
stated relations; composition only chains given premises; neither INVENTS a link.

Three principled abductive rules:
  (1) opposition-inversion: from (A, reduces, B) and opp(A)=A', abduce (A', increases, B)
      — if safety reduces threat and surprise is the opposite of safety, then surprise
      increases threat. Sign flips with the opposition. conf ~0.4.
  (2) shared-consequent affinity: if A→C and B→C (same sign), abduce A and B co-vary.
      conf ~0.3.
  (3) grounding-overlap: concepts whose definitions share salient terms get a weak
      hypothesized relation. conf ~0.2.

Opposites are derived from the agent's own concept contrasts (corrigibility_vs_protection
names one; active-inference poles surprise/predictability; benign_violation safe/threat),
flagged where supplied.
"""
from __future__ import annotations
import re
from collections import defaultdict

# opposites grounded in the agent's concept contrasts (X↔Y are opposed poles)
OPPOSITES = {
    # prediction axis: predicted/safe ↔ unpredicted/surprising (threat is the OUTCOME,
    # not the opposite of safety — that conflation was the bug)
    "safety": "surprise", "surprise": "safety", "predictability": "surprise",
    # corrigibility axis (corrigibility_vs_protection names it)
    "protection": "corrigibility", "corrigibility": "protection",
    "control": "corrigibility", "incorrigibility": "corrigibility",
    # affect poles
    "enmity": "compassion", "compassion": "enmity",
}
SIGN = {"reduces": -1, "prevents": -1, "dissolves": -1, "lowers": -1,
        "increases": 1, "causes": 1, "requires": 1, "constitutes": 1,
        "enables": 1, "needs": 1, "produces": 1}


def _sign(rel):
    return SIGN.get(rel, 1)


def abduce(relations, concept_terms=None):
    """relations: [(A, rel, B)] stated. Returns abduced bridges:
    [(A, rel, B, sign, confidence, justification)]."""
    bridges = []
    seen_stated = {(A, B) for A, _, B in relations}

    # (1) opposition-inversion  (guard self-loops: skip when opp(A)==B)
    for A, rel, B in relations:
        oA = OPPOSITES.get(A)
        if oA and oA != B and (oA, B) not in seen_stated:
            s = -_sign(rel)
            inv = "increases" if s > 0 else "reduces"
            bridges.append((oA, inv, B, s, 0.4,
                            f"opposition-inversion of '{A} {rel} {B}' (opp({A})={oA})"))

    # (2) shared-consequent affinity
    to_C = defaultdict(list)
    for A, rel, B in relations:
        to_C[B].append((A, _sign(rel)))
    for C, srcs in to_C.items():
        for i in range(len(srcs)):
            for j in range(i + 1, len(srcs)):
                (A, sa), (B, sb) = srcs[i], srcs[j]
                if A != B and (A, B) not in seen_stated:
                    s = sa * sb
                    rel = "increases" if s > 0 else "reduces"
                    bridges.append((A, rel, B, s, 0.3,
                                    f"shared-consequent: {A},{B} both →{C}"))

    # (3) grounding-overlap (weak)
    if concept_terms:
        names = list(concept_terms)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                shared = concept_terms[a] & concept_terms[b]
                if len(shared) >= 2 and (a, b) not in seen_stated:
                    bridges.append((a, "associated", b, 1, 0.2,
                                    f"grounding-overlap: share {sorted(shared)[:3]}"))
    # dedup by (A,B), keep highest-confidence justification
    best = {}
    for A, rel, B, s, c, j in bridges:
        k = (A, B)
        if k not in best or c > best[k][4]:
            best[k] = (A, rel, B, s, c, j)
    return list(best.values())


def compose_conf(premises, max_depth=8):
    """premises: [(A, rel, B, sign, confidence)]. Returns {(src,tgt):(net_sign, conf, chain)}
    — confidence = MIN along the chain (a chain is only as strong as its weakest bridge)."""
    edges = defaultdict(list)
    nodes = set()
    for A, rel, B, s, c in premises:
        edges[A].append((B, s, rel, c)); nodes.add(A); nodes.add(B)
    from collections import deque
    res = {}
    for src in nodes:
        q = deque([(src, 1, 1.0, [])]); seen = {src}
        while q:
            node, s, conf, chain = q.popleft()
            if len(chain) >= max_depth:
                continue
            for nb, es, rel, ec in edges.get(node, []):
                if nb in seen:
                    continue
                ns, nconf, nchain = s * es, min(conf, ec), chain + [(node, rel, nb, ec)]
                key = (src, nb)
                if key not in res:
                    res[key] = (ns, nconf, nchain)
                seen.add(nb); q.append((nb, ns, nconf, nchain))
    return {k: v for k, v in res.items() if len(v[2]) >= 2}
