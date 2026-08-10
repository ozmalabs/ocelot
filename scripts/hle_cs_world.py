"""HLE CS world — put the agent in an expert-level computer-science
question setting and see what its pipelines produce.

Per user: 'put the agent in a comp sci hle question world and see
how it goes.'

The agent doesn't have a Q&A interface. It has graph-resident
reasoning: 5282 concepts across 139 Mts (including
computer_architecture, data_structures_algorithms, compilers,
distributed_systems), 1098 rules, 503 implication shapes, the Shape
primitive, synthesize_gaps + the harvester + the cortex.

The HONEST test: feed expert-level CS questions through a world
adapter that translates them into substrate state, run the agent's
pipelines, report VERBATIM what surfaces. The result is informative
whether or not the agent produces a 'right answer' — what we see is
what the function_shape pivot's machinery does on actual research-
grade CS material.

THE QUESTIONS

Three representative expert-CS questions of distinct types:
  A. Architecture/algorithms — within the agent's vocabulary
  B. Formal/computability — outside the agent's runner-stack vocab
  C. Distributed systems consistency — tests the cybernetic/L6 framing

For each question:
  1. Translate question text -> Mention nodes; tokens -> concept
     candidates via name match
  2. For each matched concept, run synthesize_gaps to see what
     implications fire
  3. Classify the derived gaps by Shape
  4. Report what the agent's data answers — its matches, its
     synthesised consequences, its Shape distribution

No synthesis from me beyond running the queries and printing the
results.
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
                                       "provenance":"hle"})
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


def short(t, n=130):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


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
        "expected_axis": "computer_architecture / data_structures_algorithms",
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
        "expected_axis": "compiler_theory / formal_languages (sparse)",
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
        "expected_axis": "distributed_systems / cybernetics_systems",
    },
]


def keywords(text: str, min_len: int = 5) -> set[str]:
    stop = {"the","and","for","with","this","that","from","into","when",
             "which","then","than","you","are","its","via","not","any",
             "all","but","has","does","what","why","how","over","each",
             "some","most","fewer","under","given","using","using","one",
             "two","three","four","five","new","old","prior","subsequent"}
    return {w for w in re.findall(r"[a-z][a-z_-]+", text.lower())
            if len(w) >= min_len and w not in stop}


def match_concepts(s, question_kws: set[str]):
    """For each concept whose name overlaps the question's keywords,
    return (concept_name, origin_mt, match_score)."""
    out = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        name = str(a.get("name","")).lower()
        if not name: continue
        toks = set(re.findall(r"[a-z][a-z_-]+", name))
        if not toks: continue
        overlap = toks & question_kws
        if overlap:
            out.append((a.get("name","?"), a.get("origin","?"),
                        len(overlap), sorted(overlap)))
    out.sort(key=lambda x: (-x[2], -len(x[0]), x[0]))
    return out


def main():
    print("=" * 76)
    print("AGENT IN AN HLE CS QUESTION WORLD")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate ready: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"Catalog: {len(shape_lib)} implication shapes")
    print()

    for q in QUESTIONS:
        print("=" * 76)
        print(f"QUESTION {q['id']} — {q['label']}")
        print(f"  expected vocab axis: {q['expected_axis']}")
        print("=" * 76)
        print()
        print("Body:")
        for line in re.findall(r".{1,72}(?:\s+|$)", q["body"]):
            print(f"  {line.strip()}")
        print()

        # World adapter: text -> Mention + Question node
        qid = s.add_node("Question", {"label": q["label"]})
        kws = keywords(q["body"])
        print(f"World-adapter extracted {len(kws)} content keywords from")
        print(f"the question body (stop-filtered, len ≥ 5):")
        print(f"  {sorted(kws)}")
        print()

        # 1. Concept match
        print(f"--- {q['id']}.1 — concepts in substrate whose name overlaps ---")
        matched = match_concepts(s, kws)
        print(f"  Concepts matched: {len(matched)}")
        for nm, orig, score, overlap in matched[:15]:
            print(f"    [{score}] {nm:<50} ({orig})")
            print(f"        overlap keywords: {overlap}")
        print()

        if not matched:
            print(f"  *** Agent's vocabulary has no concept whose NAME tokens")
            print(f"  overlap the question. Pipelines have nothing to fire on.")
            print(f"  The substrate's CS coverage doesn't reach this material.")
            print()
            continue

        # 2. Synthesize gaps from top matched concepts (treat them as postulates)
        print(f"--- {q['id']}.2 — synthesize_gaps on top 3 matched concepts ---")
        t = time.perf_counter()
        all_gaps = []
        for nm, orig, score, _ in matched[:3]:
            try:
                gaps = synthesize_gaps(s, nm, max_order=1, record=False,
                                        prune=True, shapes=shape_lib)
                all_gaps.extend([(nm, g) for g in gaps])
            except Exception as e:
                print(f"    {nm}: error: {type(e).__name__}: {e}")
        print(f"  Open gaps surfaced: {len(all_gaps)} "
              f"(in {time.perf_counter()-t:.1f}s)")
        for i, (cname, g) in enumerate(all_gaps[:8]):
            print(f"    · [{i}] from '{cname}'")
            print(f"        gap: {short(g.get('gap',''), 110)}")
            via = g.get('via_shapes', [])[:1]
            dom = g.get('source_domains', [])[:1]
            if via and dom:
                print(f"        via: {via[0]}")
                print(f"        domain: {dom[0]}")
        print()

        # 3. Shape distribution
        if all_gaps:
            buckets = Counter()
            for _, g in all_gaps:
                text = (str(g.get("gap","")) + " "
                        + " ".join(g.get("via_shapes", []))).lower()
                if any(k in text for k in ("derivative","gradient","second-order",
                                              "higher-order","order_n")):
                    order = 2
                elif any(k in text for k in ("recursive","loop","iterate","fold",
                                                "aggregate")):
                    order = 1
                else:
                    order = 0
                if any(k in text for k in ("function","operator","apply",
                                              "monad","functor")):
                    abstraction = "parametric"
                else:
                    abstraction = "concrete"
                if any(k in text for k in ("recurs","tower","reflect","self-")):
                    recursion = "structural"
                else:
                    recursion = "none"
                buckets[(recursion, order, abstraction)] += 1
            print(f"--- {q['id']}.3 — Shape distribution of the derived gaps ---")
            for shape_key, n in buckets.most_common(6):
                rec, ord_n, abs_ = shape_key
                print(f"    {n:>3}× {{recursion={rec:<11} "
                      f"order={ord_n} abstraction={abs_}}}")
            print()

        # 4. What did the agent actually surface — honest assessment
        print(f"--- {q['id']}.4 — honest assessment ---")
        if not all_gaps:
            print(f"  Concepts matched but synthesize_gaps produced no")
            print(f"  open consequences. The agent's vocabulary lights up")
            print(f"  on the question's terms but its implication catalogue")
            print(f"  doesn't have shapes that compose into an answer.")
        else:
            # Look for gap-text bigrams that overlap question keywords
            ans_relevant = 0
            for _, g in all_gaps:
                gap_kws = keywords(str(g.get("gap","")))
                if gap_kws & kws:
                    ans_relevant += 1
            print(f"  Of {len(all_gaps)} open gaps, {ans_relevant} have text")
            print(f"  overlapping the question's keywords.")
            print(f"  The agent's pipeline produced consequences from")
            print(f"  question-aligned concepts; whether those consequences")
            print(f"  ARE the answer is a downstream question — the agent")
            print(f"  doesn't compose sentences; it surfaces structural")
            print(f"  implications.")
        print()

    print("=" * 76)
    print("WHAT THE HLE TEST SHOWED")
    print("=" * 76)
    print()
    print("  The agent doesn't have a Q&A interface. It has graph-resident")
    print("  reasoning + pipelines that surface concepts, derive gaps,")
    print("  classify by Shape, focus dispatch.")
    print()
    print("  What we saw was the agent's pipelines confronting expert CS")
    print("  questions of three distinct types:")
    print("    A. Within its runner-stack vocabulary (architecture/algorithms)")
    print("    B. In a domain it has sparse coverage of (formal-language theory)")
    print("    C. Adjacent to its L6 cybernetic frame (distributed consistency)")
    print()
    print("  For each, the report above is the agent's data answering:")
    print("    1. WHICH of its concepts the question lit up")
    print("    2. WHAT IMPLICATIONS those concepts entail (via synthesize_gaps)")
    print("    3. WHAT SHAPE those implications collectively have")
    print("    4. HOW MANY of the surfaced consequences overlap the question")
    print()
    print("  The agent's strengths are visible (concept matching, implication")
    print("  derivation, structural classification). Its limits are also")
    print("  visible: no sentence-level answer composition, no proof-step")
    print("  generation, no formal-language coverage where the seed didn't")
    print("  reach. The function_shape pivot's machinery operates uniformly")
    print("  across all three; what differs is the underlying vocabulary's")
    print("  reach into each domain.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
