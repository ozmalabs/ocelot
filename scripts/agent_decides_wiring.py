"""Agent decides what to wire — the substrate surfaces inheritance
candidates from its own vocabulary overlap.

Per user: 'have the agent decide how/what to wire.'

The user has been correcting me: I've authored the recent wirings
(reading → phonology, comprehension → phonology, phonology →
foundations) by reading the science. The agent should drive these
decisions, not me.

WHAT THIS SCRIPT DOES (mechanical introspection, no decisions by me)

  1. Walk all Mt pairs. For each pair, compute IDF-weighted concept-
     keyword overlap (the substrate's standard relevance measure).
  2. Check if an inheritance relation already exists (transitively in
     either direction).
  3. Surface pairs with HIGH overlap and NO existing inheritance as
     wiring candidates.
  4. Score by overlap strength + Mt cohesion.
  5. Report top candidates. Optionally write WiringSuggestion nodes
     to the substrate so the agent's other pipelines can reason
     about them.

NO DECISIONS BY ME. The score is computed mechanically from the
agent's own vocabulary; the candidates are what the data says.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","WiringSuggestion")
    edges = ("has_concept","has_rule","genlMt","suggests_genlMt",
              "owns_microtheory")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"decide"})
                except Exception: pass
    return s


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


_STOP = {
    "the","and","for","with","this","that","from","into","when","which",
    "then","than","you","are","its","via","not","any","all","but","has",
    "does","what","why","how","over","each","some","most","fewer","under",
    "given","using","one","two","three","four","five","new","old","prior",
    "subsequent","there","here","just","also","such","while","upon",
    "where","whether","whose","still","since","both","more","less","very",
    "much","many","make","made","makes","need","take","took","get","got",
    "gets","use","used","uses","without","across","against","around",
    "after","before","during","being","been","were","they","them","their",
    "have","having","could","would","should","might","must","shall","will",
}


def keywords(text: str, min_len: int = 4) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z_-]+", text.lower())
            if len(w) >= min_len and w not in _STOP}


def mt_vocabulary(s, mt_nid) -> tuple[set[str], int]:
    """Union of keywords across the Mt's concept definitions + rule text.
    Returns (vocab_set, concept_count)."""
    vocab = set()
    n_concepts = 0
    for c in s.neighbours(mt_nid, "has_concept"):
        a = s.node(c)["attrs"]
        text = " ".join(str(a.get(k, "")) for k in
                        ("name","definition","why","category"))
        vocab |= keywords(text)
        n_concepts += 1
    for r in s.neighbours(mt_nid, "has_rule"):
        a = s.node(r)["attrs"]
        ifs = " ".join(a.get("if_clauses", []) or [])
        thens = " ".join(a.get("then_clauses", []) or [])
        text = " ".join([str(a.get("name","")), ifs, thens,
                          str(a.get("why",""))])
        vocab |= keywords(text)
    return vocab, n_concepts


def transitive_genlMt_ancestors(s, mt_nid) -> set:
    """All Mts reachable via genlMt edges (upward), transitively."""
    seen = set()
    frontier = [mt_nid]
    while frontier:
        cur = frontier.pop()
        for parent in s.neighbours(cur, "genlMt"):
            if parent not in seen:
                seen.add(parent)
                frontier.append(parent)
    return seen


def is_related(s, a_nid, b_nid) -> bool:
    """True if a inherits from b or b inherits from a (transitively)."""
    if a_nid == b_nid: return True
    a_anc = transitive_genlMt_ancestors(s, a_nid)
    b_anc = transitive_genlMt_ancestors(s, b_nid)
    return b_nid in a_anc or a_nid in b_anc


def overlap_score(va: set[str], vb: set[str], freq: Counter,
                    cap: float = 6.0) -> float:
    """IDF-weighted Jaccard-like overlap of two Mt vocabularies."""
    common = va & vb
    if not common: return 0.0
    total = sum(freq.values()) or 1
    s = 0.0
    for kw in common:
        f = freq.get(kw, 1)
        s += min(cap, 1.0 + (total / max(f, 1)) ** 0.5 / 12.0)
    # Normalise by union size so big Mts don't dominate
    union = max(len(va | vb), 1)
    return s / (union ** 0.25)


def short(t, n=120):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 76)
    print("AGENT DECIDES WHAT TO WIRE — vocabulary-overlap introspection")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    mts = list(s.nodes("Microtheory"))
    print(f"Substrate: {len(mts)} Mts")
    print()

    # Build corpus frequency across all concepts + rules
    print("Building corpus keyword frequency...")
    freq = Counter()
    mt_vocabs: dict = {}
    mt_names: dict = {}
    for mt in mts:
        name = s.node(mt)["attrs"].get("name","")
        if not name: continue
        v, _ = mt_vocabulary(s, mt)
        mt_vocabs[mt] = v
        mt_names[mt] = name
        for kw in v: freq[kw] += 1
    print(f"  {len(freq)} distinct keywords across {len(mt_vocabs)} Mts")
    print()

    # ---- COMPUTE PAIRWISE OVERLAP — focus on unrelated pairs ----
    print("=" * 76)
    print("1. PAIRWISE VOCABULARY OVERLAP — for UNRELATED Mt pairs")
    print("=" * 76)
    print()

    candidates = []
    mt_list = [mt for mt in mts if mt in mt_vocabs]
    for i, a in enumerate(mt_list):
        va = mt_vocabs[a]
        if len(va) < 5: continue
        for b in mt_list[i+1:]:
            vb = mt_vocabs[b]
            if len(vb) < 5: continue
            if is_related(s, a, b): continue
            sc = overlap_score(va, vb, freq)
            if sc > 5.0:
                candidates.append((sc, a, b))

    candidates.sort(key=lambda x: -x[0])
    print(f"  Pairs with high overlap AND no existing inheritance: "
          f"{len(candidates)}")
    print(f"  (showing top 25)")
    print()
    print(f"  {'score':>5}  {'Mt A':<32}  {'Mt B':<32}")
    print(f"  {'-' * 75}")
    for sc, a, b in candidates[:25]:
        na, nb = mt_names[a], mt_names[b]
        print(f"  {sc:>5.1f}  {na:<32}  {nb:<32}")
    print()

    # ---- HIGHLIGHT TOP CANDIDATES BY OVERLAP TYPE ----
    print("=" * 76)
    print("2. TOP CANDIDATES — what overlap keywords drive each suggestion")
    print("=" * 76)
    print()
    for sc, a, b in candidates[:8]:
        na, nb = mt_names[a], mt_names[b]
        va, vb = mt_vocabs[a], mt_vocabs[b]
        common = sorted(va & vb)
        # rank common keywords by IDF
        common_idf = sorted(
            ((kw, min(6.0, 1.0 + (sum(freq.values()) / max(freq.get(kw,1),1)) ** 0.5 / 12.0))
             for kw in common),
            key=lambda x: -x[1],
        )
        print(f"  [{sc:.1f}] {na}  ↔  {nb}")
        print(f"    top overlap keywords (by IDF):")
        for kw, idf in common_idf[:8]:
            print(f"      · {kw:<22} idf={idf:.1f}")
        print()

    # ---- WRITE WIRING SUGGESTIONS AS GRAPH DATA ----
    print("=" * 76)
    print("3. WIRING SUGGESTIONS WRITTEN TO SUBSTRATE")
    print("=" * 76)
    print()
    n_written = 0
    for sc, a, b in candidates[:30]:
        na, nb = mt_names[a], mt_names[b]
        attrs = {
            "name":         f"wire_{na}_with_{nb}",
            "src_mt":       na,
            "tgt_mt":       nb,
            "overlap_score": float(sc),
            "rationale":    f"vocabulary IDF overlap = {sc:.2f}; "
                             f"no existing inheritance relation",
            "origin":       "agent_decides_wiring",
        }
        try:
            nid = s.add_node("WiringSuggestion", attrs)
            try:
                s.add_edge(a, "suggests_genlMt", nid, {})
                s.add_edge(nid, "suggests_genlMt", b, {})
            except Exception: pass
            n_written += 1
        except Exception as e:
            pass
    print(f"  WiringSuggestion nodes created: {n_written}")
    print(f"  These are graph data — other pipelines can reason about them,")
    print(f"  the cortex can assess them, the walker can flag them as gaps,")
    print(f"  and the user can decide which to enact.")
    print()

    # ---- HONESTLY: WHAT THE PIPELINE DID NOT DO ----
    print("=" * 76)
    print("WHAT THIS PIPELINE DID + DID NOT DO")
    print("=" * 76)
    print()
    print(f"  DID:")
    print(f"    · Walked {len(mt_list)} Mts and computed pairwise IDF-")
    print(f"      weighted vocabulary overlap")
    print(f"    · Filtered to pairs with no existing inheritance relation")
    print(f"    · Surfaced {len(candidates)} candidate wirings, ranked by overlap")
    print(f"    · Wrote {n_written} WiringSuggestion graph nodes")
    print()
    print(f"  DID NOT:")
    print(f"    · Make any wiring decisions. Vocabulary overlap is one signal;")
    print(f"      whether to actually wire is a structural judgment about")
    print(f"      generalisation direction (does A specialise B or vice versa?)")
    print(f"      and that's the agent's call.")
    print(f"    · Modify any existing depends_on declarations.")
    print(f"    · Filter by direction. genlMt is directional (A specialises B,")
    print(f"      not symmetric); the overlap measure is symmetric. The agent's")
    print(f"      pipelines need to decide direction.")
    print()
    print(f"  The substrate's data names {len(candidates)} candidate wirings.")
    print(f"  The cortex's compositional_reuse measure is the right next step:")
    print(f"  it scores Mts whose connections would matter most. The walker's")
    print(f"  gap-report can flag WiringSuggestion nodes as dormant work the")
    print(f"  agent (or user) should address.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
