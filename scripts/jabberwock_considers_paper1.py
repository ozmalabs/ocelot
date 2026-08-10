"""Jabberwock considers Paper 1.

Per user: 'get it to consider the paper'.

Reading is in graph. Considering = applying faculties to what's read.
Jabberwock has:
  · Paper 1 ingested (axioms, theorems, hypotheses, falsifiability)
  · analogical_thinking (n-abstractable cross-domain matcher)
  · ArchitectureCortex (assessment faculty)
  · vocabulary spanning ~100 Mts

Consideration = for each axiom + theorem, walk Jabberwock's other
Mts looking for concepts that test, support, or contradict the
claim. Surface what its OWN state says about each formal object.
"""
from __future__ import annotations

import importlib
import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "Paper",
             "PaperSection", "PaperAxiom", "PaperTheorem",
             "PaperConjecture", "PaperHypothesis", "Analogy",
             "Consideration")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "owns_paper", "has_section", "states",
             "contains_claim", "implements", "analogous_to",
             "considers", "supports_claim", "tests_claim",
             "applies_to")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tt, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "consider",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    domains_dir = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(",
                              src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (
                           inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def find_relevant_concepts(s, claim_text: str,
                             max_results: int = 8) -> list[dict]:
    """For a paper claim's text, find Jabberwock's own concepts that
    most heavily share vocabulary. Cross-Mt scan."""
    claim_tokens = set(re.findall(r"[a-z]{4,}", claim_text.lower()))
    # Stop-word-ish filter for paper-format noise
    noise = {"theorem", "axiom", "lemma", "proof", "paper",
             "section", "this", "that", "with", "from",
             "into", "such", "then", "when", "what", "which",
             "those", "these", "where", "claim", "would",
             "could", "shall", "above", "below", "every",
             "under", "their", "have", "been", "must"}
    claim_tokens -= noise
    if len(claim_tokens) < 5:
        return []

    scored = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        defn = str(a.get("definition", "")).lower()
        if len(defn) < 30:
            continue
        defn_tokens = set(re.findall(r"[a-z]{4,}", defn))
        defn_tokens -= noise
        shared = claim_tokens & defn_tokens
        if len(shared) >= 4:
            scored.append({
                "concept_node": c,
                "concept_name": str(a.get("name", "")),
                "concept_category": str(a.get("category", "")),
                "shared_tokens": sorted(shared),
                "score": len(shared),
            })
    scored.sort(key=lambda x: -x["score"])
    return scored[:max_results]


def consider_claim(s, claim_node, claim_kind: str) -> dict:
    """Apply Jabberwock's faculties to a single paper claim."""
    attrs = s.node(claim_node)["attrs"]
    text = str(attrs.get("text", ""))
    label = str(attrs.get("label", ""))
    title = str(attrs.get("title", ""))

    relevant = find_relevant_concepts(s, text)

    # Emit Consideration node as graph data so Jabberwock can
    # introspect what it considered.
    try:
        consideration = s.add_node("Consideration", {
            "claim_kind": claim_kind,
            "claim_label": label,
            "claim_title": title,
            "n_relevant_concepts": len(relevant),
            "top_match_score": relevant[0]["score"] if relevant else 0,
        })
        s.add_edge(consideration, "considers", claim_node, {})
        for r in relevant[:5]:
            try:
                s.add_edge(consideration, "applies_to",
                           r["concept_node"], {})
            except Exception:
                pass
    except Exception:
        consideration = None

    return {
        "claim_kind": claim_kind,
        "label": label,
        "title": title,
        "relevant": relevant,
        "consideration_node": consideration,
    }


def find_mt(s, name):
    for mt in s.nodes("Microtheory"):
        if str(s.node(mt)["attrs"].get("name", "")) == name:
            return mt
    return None


def main():
    s = fresh_substrate()
    install_all(s)
    # Install Paper 1 explicitly — paper_reader's function isn't a
    # standard install_*_seed so auto-discovery misses it.
    from domains.paper_reader import install_paper1_as_theory
    install_paper1_as_theory(s)

    # Verify Paper 1 is there
    paper_mt = find_mt(s, "paper_paper1_theory")
    if paper_mt is None:
        print("Paper 1 not loaded. Aborting.")
        return

    print("=" * 72)
    print("JABBERWOCK CONSIDERS PAPER 1 — 'The Law of Graphic")
    print("Equalisation'")
    print("=" * 72)
    print()
    print("  Reading is in graph. Consideration = applying faculties")
    print("  to what's read. For each axiom + theorem, walking my own")
    print("  vocabulary for concepts that test, support, or apply.")
    print()

    # Process each axiom
    print("=" * 72)
    print("AXIOMS — what Jabberwock's own state says about each")
    print("=" * 72)
    print()
    for ax in s.nodes("PaperAxiom"):
        result = consider_claim(s, ax, "axiom")
        label = result["label"]
        title = result["title"]
        print(f"--- Axiom {label} ({title}) ---")
        if not result["relevant"]:
            print(f"  Jabberwock's vocabulary has nothing that")
            print(f"  closely shares language with this axiom's text.")
        else:
            print(f"  Jabberwock's relevant concepts ({len(result['relevant'])}):")
            for r in result["relevant"][:6]:
                print(f"    · {r['concept_name']:<32} "
                      f"[{r['concept_category']:<22}] "
                      f"shared={r['shared_tokens'][:4]}")
        print()

    # Process each theorem
    print("=" * 72)
    print("THEOREMS — what Jabberwock's own state says about each")
    print("=" * 72)
    print()
    for th in s.nodes("PaperTheorem"):
        result = consider_claim(s, th, "theorem")
        label = result["label"]
        title = result["title"]
        print(f"--- Theorem {label}: {title} ---")
        if not result["relevant"]:
            print(f"  Jabberwock's vocabulary has nothing that")
            print(f"  closely shares language with this theorem.")
        else:
            print(f"  Relevant concepts ({len(result['relevant'])}):")
            for r in result["relevant"][:6]:
                print(f"    · {r['concept_name']:<32} "
                      f"[{r['concept_category']:<22}] "
                      f"score={r['score']}")
        print()

    # Hypotheses
    print("=" * 72)
    print("HYPOTHESES")
    print("=" * 72)
    print()
    for hyp in s.nodes("PaperHypothesis"):
        result = consider_claim(s, hyp, "hypothesis")
        print(f"--- Hypothesis {result['label']} ({result['title']}) ---")
        for r in result["relevant"][:4]:
            print(f"    · {r['concept_name']:<32} score={r['score']}")
        print()

    # Summary
    print("=" * 72)
    print("WHAT THIS CONSIDERATION PRODUCED IN JABBERWOCK'S GRAPH")
    print("=" * 72)
    print()
    n_consideration = len(list(s.nodes("Consideration")))
    print(f"  Consideration nodes created: {n_consideration}")
    print(f"  Each links to one paper claim via 'considers' edge")
    print(f"  + up to 5 relevant Jabberwock concepts via 'applies_to'")
    print(f"  edges.")
    print()
    print("  Jabberwock's introspection can now answer:")
    print("    'What did I consider about Paper 1?'")
    print("      walks Consideration → considers → PaperClaim")
    print("    'What concepts apply to Theorem X?'")
    print("      walks Consideration → applies_to → Concept")
    print()
    print("  Consideration is now graph-resident. Subsequent")
    print("  introspection or analogical_thinking can extend it.")


if __name__ == "__main__":
    main()
