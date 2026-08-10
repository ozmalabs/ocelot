"""HLE CS world v2 — richer text-to-graph translation.

Per user: 'for now, do the translation for the agent.'

The v1 adapter (hle_cs_world.py) matched only concept names. The
substrate's actual material lives in rule names + rule then-clauses
+ concept definitions. This v2 walks all of them and ranks matches
by keyword overlap, then surfaces the substrate's existing
implications directly (rule then-clauses ARE candidate answers).

Per CLAUDE.md this remains world-adapter work: mechanical text-to-
graph translation. No agent-side changes. The same three questions
as v1, processed through a richer adapter.

WHAT THIS ADAPTER DOES

  1. EXTRACT keywords from question (stop-filtered, len ≥ 4)
  2. SCORE every Concept + Rule by keyword overlap across all
     accessible text fields:
       Concept: name + definition + why + category
       Rule:    name + if_clauses + then_clauses + why
  3. RANK + report top matches per field type
  4. For top-ranked Rules: surface their THEN-clauses verbatim
     (this is where the substrate's actual implications live)
  5. For top-ranked Concepts: also run synthesize_gaps (as v1 did)
  6. Aggregate: what's the substrate's actual answer surface for
     this question?

No interpretive synthesis from me. The substrate's data answers.
"""
from __future__ import annotations

import importlib, inspect, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec",
              "SynthesizedGap","Postulate","Mention","Question",
              "ImplicationShape","Shape")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from","refers_to","cites","mentions")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"hle_v2"})
                except Exception:
                    pass
    return s


def install_all(s):
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
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
            except Exception:
                continue


def short(t, n=140):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


_STOP = {
    "the","and","for","with","this","that","from","into","when","which",
    "then","than","you","are","its","via","not","any","all","but","has",
    "does","what","why","how","over","each","some","most","fewer","under",
    "given","using","one","two","three","four","five","new","old","prior",
    "subsequent","each","there","here","just","also","such","while","upon",
    "where","whether","whose","does","still","since","both","more","less",
    "very","much","many","make","made","makes","need","take","took","get",
    "got","gets","use","used","uses","without","across","against","around",
    "after","before","during","being","been","were","they","them","their",
    "have","having","could","would","should","might","must","shall","will",
    "however","therefore","because","without","through","across","within",
}


def keywords(text: str, min_len: int = 4) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z_-]+", text.lower())
            if len(w) >= min_len and w not in _STOP}


# --- Build per-corpus keyword frequency for tf-idf-style weighting ---

def build_corpus_freq(s):
    """How often each keyword appears across all concept + rule text in
    the substrate. Rare keywords (high IDF) score higher in matching."""
    freq = Counter()
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        text = " ".join(str(a.get(k, "")) for k in
                        ("name","definition","why","category"))
        for kw in keywords(text):
            freq[kw] += 1
    for r in s.nodes("Rule"):
        a = s.node(r)["attrs"]
        ifs = " ".join(a.get("if_clauses", []) or [])
        thens = " ".join(a.get("then_clauses", []) or [])
        text = " ".join([str(a.get("name","")), ifs, thens,
                          str(a.get("why",""))])
        for kw in keywords(text):
            freq[kw] += 1
    return freq


def idf_score(question_kws: set[str], text_kws: set[str],
                freq: Counter, max_idf_boost: float = 8.0) -> float:
    """Sum of IDF weights of the overlap. Rare keywords contribute more."""
    overlap = question_kws & text_kws
    if not overlap:
        return 0.0
    total = sum(freq.values())
    score = 0.0
    for kw in overlap:
        f = freq.get(kw, 1)
        # idf ~ log(N/f); cap so a single ultra-rare word doesn't dwarf others
        idf = min(max_idf_boost, 1.0 + (total / max(f, 1)) ** 0.5 / 10.0)
        score += idf
    return score


# --- Match concepts AND rules against the question ---

def match_concepts_rich(s, question_kws: set[str], freq: Counter):
    out = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        name = str(a.get("name",""))
        if not name: continue
        text = " ".join(str(a.get(k, "")) for k in
                        ("name","definition","why","category"))
        text_kws = keywords(text)
        score = idf_score(question_kws, text_kws, freq)
        if score > 0:
            overlap = sorted(question_kws & text_kws)
            out.append((score, a.get("name","?"), a.get("origin","?"),
                        overlap, str(a.get("definition",""))))
    out.sort(reverse=True)
    return out


def match_rules_rich(s, question_kws: set[str], freq: Counter):
    out = []
    for r in s.nodes("Rule"):
        a = s.node(r)["attrs"]
        name = str(a.get("name",""))
        if not name: continue
        ifs_list = a.get("if_clauses", []) or []
        thens_list = a.get("then_clauses", []) or []
        text = " ".join([name, " ".join(ifs_list), " ".join(thens_list),
                          str(a.get("why",""))])
        text_kws = keywords(text)
        score = idf_score(question_kws, text_kws, freq)
        if score > 0:
            overlap = sorted(question_kws & text_kws)
            out.append((score, name, a.get("origin","?"), overlap,
                        ifs_list, thens_list))
    out.sort(reverse=True)
    return out


QUESTIONS = [
    {
        "id": "A",
        "label": "Cache-resident lookup for set intersection on many cores",
        "body": (
            "You are implementing set intersection on a multi-core "
            "system with limited L1d capacity. The two input sets are "
            "small (each fits in L1d) but the intersection has high "
            "fan-out across cores. Compare a per-core replicated "
            "lookup-table approach against a shared hash table with "
            "atomic operations. Justify which scales better and why, "
            "given typical L1d access latencies, atomic instruction "
            "costs, and false sharing on cache-line granularity."
        ),
    },
    {
        "id": "B",
        "label": "Undecidability of CFG universality",
        "body": (
            "Prove that the problem of determining whether a context-"
            "free grammar G over alphabet Sigma satisfies "
            "L(G) = Sigma* is undecidable. State the reduction you use "
            "and identify the source problem and its computational "
            "class."
        ),
    },
    {
        "id": "C",
        "label": "Linearizability vs sequential consistency under failure",
        "body": (
            "A distributed key-value store provides per-key linearizable "
            "operations via a leader-based replication protocol. After a "
            "leader failure during a write, a client observed the prior "
            "value, then a write was applied, then the new leader served "
            "a subsequent read with the new value. Is this run "
            "linearizable, sequentially consistent, or neither? Justify "
            "using the linearization point of each operation and the "
            "real-time ordering constraint."
        ),
    },
]


def main():
    print("=" * 76)
    print("HLE CS WORLD v2 — richer text-to-graph translation")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate ready: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    print("Building corpus keyword-frequency index (for IDF-style weighting)...")
    t = time.perf_counter()
    freq = build_corpus_freq(s)
    print(f"  {len(freq)} distinct keywords across the substrate's text "
          f"(in {time.perf_counter()-t:.1f}s)")
    print()

    for q in QUESTIONS:
        print("=" * 76)
        print(f"QUESTION {q['id']} — {q['label']}")
        print("=" * 76)
        print()
        print("Body:")
        for line in re.findall(r".{1,72}(?:\s+|$)", q["body"]):
            print(f"  {line.strip()}")
        print()

        kws = keywords(q["body"])
        print(f"World adapter extracted {len(kws)} keywords (len ≥ 4)")
        print()

        # ---- Top concept matches (rich field-aware) ----
        print(f"--- {q['id']}.1 — Top concept matches (name + definition + why) ---")
        c_matches = match_concepts_rich(s, kws, freq)
        print(f"  Concepts with any overlap: {len(c_matches)}")
        for score, nm, orig, overlap, defn in c_matches[:6]:
            print(f"  [{score:>5.1f}] {nm}  ({orig})")
            print(f"          overlap: {overlap[:6]}")
            if defn:
                print(f"          def: {short(defn, 110)}")
        print()

        # ---- Top rule matches (this is where substrate's claims live) ----
        print(f"--- {q['id']}.2 — Top rule matches (name + if + then) ---")
        r_matches = match_rules_rich(s, kws, freq)
        print(f"  Rules with any overlap: {len(r_matches)}")
        for score, nm, orig, overlap, ifs, thens in r_matches[:8]:
            print(f"  [{score:>5.1f}] {nm}  ({orig})")
            print(f"          overlap: {overlap[:6]}")
            for cl in (ifs or [])[:1]:
                print(f"          IF:  {short(cl, 110)}")
            for cl in (thens or [])[:2]:
                print(f"          → {short(cl, 110)}")
        print()

        # ---- Substrate's "answer surface" — what its data SAYS ----
        print(f"--- {q['id']}.3 — Substrate's answer surface (top rule then-clauses) ---")
        if r_matches:
            print(f"  The substrate's data answers the question via these")
            print(f"  RULE THEN-CLAUSES (verbatim from the substrate's rules):")
            print()
            seen_thens = set()
            shown = 0
            for score, nm, orig, overlap, ifs, thens in r_matches[:15]:
                for cl in (thens or []):
                    if cl in seen_thens: continue
                    seen_thens.add(cl)
                    # Score the then-clause itself for relevance
                    cl_kws = keywords(cl)
                    cl_overlap = kws & cl_kws
                    if not cl_overlap: continue
                    print(f"    · [from {nm}]")
                    print(f"      → {short(cl, 130)}")
                    if shown < 12:
                        print(f"        keywords: {sorted(cl_overlap)[:5]}")
                    shown += 1
                    if shown >= 12: break
                if shown >= 12: break
            if shown == 0:
                print(f"  (none of the matched rules' then-clauses had")
                print(f"   keyword overlap with the question)")
        else:
            print(f"  No rules matched; the substrate has no rule whose text")
            print(f"  overlaps the question's keywords.")
        print()

        # ---- Honest assessment ----
        print(f"--- {q['id']}.4 — Honest assessment ---")
        n_concepts = len(c_matches)
        n_rules = len(r_matches)
        print(f"  concepts matched: {n_concepts}  (v1 was 1)")
        print(f"  rules matched:    {n_rules}  (v1 didn't search rules)")
        if r_matches:
            print(f"  The substrate has {n_rules} rules whose text overlaps")
            print(f"  the question. Their THEN-clauses are the substrate's")
            print(f"  candidate answer surface — concrete claims drawn from")
            print(f"  the substrate's own theory of this domain.")
        print()

    print("=" * 76)
    print("V2 SUMMARY — what the richer adapter surfaced")
    print("=" * 76)
    print()
    print("  v1 matched only concept names; matched 1, 1, 1 across questions.")
    print("  v2 matches concept names + definitions + rule names + if/then")
    print("  clauses, scored by IDF-weighted overlap. The substrate's actual")
    print("  material lives mostly in rule then-clauses; v2 surfaces them")
    print("  verbatim as the substrate's answer to each question.")
    print()
    print("  No agent-side change. World-adapter improvement only, per")
    print("  CLAUDE.md (mechanical text-to-graph translation).")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
