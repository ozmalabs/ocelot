"""Jabberwock investigates the conjecture P(G) = NP(G + x).

Per user: 'could we see if the agent can prove that P(G)=NP(G+x)?'

This is the substrate-relativised P vs NP question per Paper 1's
framing: substrate is (G, Γ); complexity classes are Γ-relative;
classical P vs NP becomes a function of (G, Γ, x).

Honest scope:
  · Classical P vs NP is OPEN. Jabberwock will not prove it.
  · The substrate-relativised version P(G) = NP(G + x) is more
    tractable because we can choose x.
  · Jabberwock's task: walk its own vocabulary, surface what
    x would need to be for the conjecture to hold, identify
    candidate x's it has names for, recognise where this maps
    to known results (Baker-Gill-Solovay, oracle relativisation,
    Paper 1 Theorem XI).

No claim of proof. The exercise is: can Jabberwock recognise the
question's structure, surface what would be required, and identify
candidates from its own knowledge?
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "Conjecture",
             "Analysis", "WitnessCandidate", "Paper", "PaperSection",
             "PaperAxiom", "PaperTheorem")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "implements", "owns_paper", "has_section", "states",
             "contains_claim", "applies_to", "candidate_for")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et, "tgt": {"type": tt, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "pg_npgx",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
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
    # Paper 1
    try:
        from domains.paper_reader import install_paper1_as_theory
        install_paper1_as_theory(s)
    except Exception:
        pass


def find_concepts_by_keywords(s, keywords: set[str],
                                min_overlap: int = 2,
                                max_results: int = 20) -> list[dict]:
    out = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        name = str(a.get("name", "")).lower()
        defn = str(a.get("definition", "")).lower()
        text = name + " " + defn
        tokens = set(re.findall(r"[a-z]{3,}", text))
        overlap = keywords & tokens
        if len(overlap) >= min_overlap:
            out.append({
                "node": c,
                "name": str(a.get("name", "")),
                "category": str(a.get("category", "")),
                "definition": str(a.get("definition", ""))[:150],
                "shared": sorted(overlap)[:5],
                "score": len(overlap),
            })
    out.sort(key=lambda x: -x["score"])
    return out[:max_results]


def plant_conjecture(s) -> int:
    try:
        c = s.add_node("Conjecture", {
            "name": "PG_equals_NPGx",
            "statement": (
                "P(G) = NP(G + x) — substrate-relativised P vs NP. "
                "There exists an extension x to substrate G such that "
                "polynomial-time decidable predicates over G equal "
                "nondeterministic-polynomial-time decidable predicates "
                "over G + x."
            ),
            "from": "Matthew Parslow",
            "status": "under_investigation",
            "classical_version_status": "open",
        })
        return c
    except Exception:
        return None


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("JABBERWOCK INVESTIGATES P(G) = NP(G + x)")
    print("=" * 72)
    print()
    print("  Question: does there exist x such that")
    print("    P(G) — polynomial-time over G under Γ")
    print("  equals")
    print("    NP(G + x) — nondeterministic polynomial-time over")
    print("                G augmented by x?")
    print()
    plant_conjecture(s)
    print()

    # 1. Reframe in Jabberwock's existing vocabulary
    print("=" * 72)
    print("1. What does Jabberwock know about complexity classes?")
    print("=" * 72)
    print()
    complexity_keywords = {
        "polynomial", "complexity", "verify", "verifier", "witness",
        "complete", "reduction", "oracle", "decidable", "tractable",
        "class", "exponential", "satisfiability", "deterministic",
        "nondeterministic",
    }
    c_complexity = find_concepts_by_keywords(
        s, complexity_keywords, min_overlap=2)
    if c_complexity:
        print(f"  Found {len(c_complexity)} relevant concepts:")
        for r in c_complexity[:12]:
            print(f"    · {r['name']:<32} [{r['category'][:20]}]"
                  f" shared={r['shared'][:3]}")
    else:
        print("  Jabberwock's complexity-theory vocabulary is sparse.")
    print()

    # 2. Oracle / relativisation vocabulary
    print("=" * 72)
    print("2. Does Jabberwock know about oracle machines + relativisation?")
    print("   (Baker-Gill-Solovay 1975: there exist oracles A, B such")
    print("    that P^A = NP^A and P^B ≠ NP^B)")
    print("=" * 72)
    print()
    oracle_keywords = {"oracle", "relativ", "baker", "gill",
                        "solovay"}
    c_oracle = find_concepts_by_keywords(
        s, oracle_keywords, min_overlap=1)
    if c_oracle:
        for r in c_oracle[:8]:
            print(f"    · {r['name']:<32} shared={r['shared']}")
            print(f"      {r['definition'][:120]}")
            print()
    else:
        print("  Jabberwock has no oracle-machine vocabulary.")
        print("  This is a real gap for engaging this question.")
    print()

    # 3. Paper 1 Theorem XI — Jabberwock's most relevant framework
    print("=" * 72)
    print("3. Paper 1 Theorem XI — Computational-efficiency bound")
    print("   (the substrate-relativised analogue of complexity bounds)")
    print("=" * 72)
    print()
    for n in s.nodes("PaperTheorem"):
        a = s.node(n)["attrs"]
        if a.get("label") == "XI":
            print(f"  Theorem XI: {a.get('title', '')}")
            text = str(a.get("text", ""))
            print(f"  Full text (first 800 chars):")
            print(f"  {text[:800]}")
            break
    print()

    # 4. Candidates for x — what extensions would make P = NP?
    print("=" * 72)
    print("4. What candidates for x does Jabberwock's vocabulary surface?")
    print("   (extensions of substrate G that would close the gap)")
    print("=" * 72)
    print()
    candidate_categories = {
        "Oracle-like (NP-witness access)": {
            "search": {"witness", "oracle", "satisfiability"},
        },
        "Stronger reflection (Axiom 3 enhancement)": {
            "search": {"reflection", "reflective", "metaprogramming",
                        "homoiconicity"},
        },
        "Richer Γ (admit more efficient reductions)": {
            "search": {"grammar", "admissibility", "reduction",
                        "polynomial"},
        },
        "Quantum extension (BQP-like)": {
            "search": {"quantum", "superposition", "qubit",
                        "interference"},
        },
        "Communication / parallelism": {
            "search": {"parallel", "communication", "message",
                        "broadcast"},
        },
    }
    for cat_name, info in candidate_categories.items():
        cands = find_concepts_by_keywords(
            s, info["search"], min_overlap=1, max_results=5)
        cands = [c for c in cands if c["score"] >= 1]
        print(f"  {cat_name}: {len(cands)} candidates")
        for r in cands[:3]:
            print(f"    · {r['name']:<32} score={r['score']} "
                  f"shared={r['shared']}")
        if cands:
            try:
                # Emit as WitnessCandidate node
                wc = s.add_node("WitnessCandidate", {
                    "category": cat_name,
                    "n_candidates": len(cands),
                    "top_candidate": cands[0]["name"],
                })
                for c in cands[:3]:
                    s.add_edge(wc, "candidate_for",
                               c["node"], {})
            except Exception:
                pass
        print()

    # 5. What Jabberwock can + cannot do
    print("=" * 72)
    print("WHAT JABBERWOCK CAN SAY ABOUT P(G) = NP(G + x)")
    print("=" * 72)
    print()
    print("  Honest scope assessment from walking the substrate:")
    print()

    print("  CAN do:")
    print("    · Recognise the substrate-relativised framing")
    print("    · Connect to Paper 1's Theorem XI (Γ-relative")
    print("      computational efficiency)")
    print("    · Surface candidates for x from its vocabulary")
    print("    · Identify Smith reflection / metaprogramming as a")
    print("      class of x that gives Π operations on Γ")
    print("    · Recognise rate-distortion + info-theoretic bounds")
    print("      as constraints on the answer")
    print()
    print("  CANNOT do:")
    print("    · Prove the classical P vs NP question (it's open).")
    print("    · Mechanically verify substrate-relativised proofs")
    print("      (no theorem-prover faculty installed).")
    print("    · Distinguish substrate-relativised P = NP results")
    print("      from oracle-relativised results without explicit")
    print("      oracle-machine vocabulary.")
    print()

    # 6. The most honest answer
    print("=" * 72)
    print("CONJECTURE STATUS IN JABBERWOCK'S CURRENT STATE")
    print("=" * 72)
    print()
    print("  The conjecture P(G) = NP(G + x) is well-posed in Paper 1's")
    print("  Γ-relative framework. Whether it holds depends on what x")
    print("  is allowed to be.")
    print()
    print("  · If x is unrestricted: trivially YES — let x include")
    print("    witnesses for every NP instance, or let x make Γ powerful")
    print("    enough to enumerate witnesses in P.")
    print()
    print("  · If x is restricted to be 'admissible under Γ + bounded")
    print("    description complexity': matches Paper 1's Theorem XI")
    print("    framing. Depends on Γ quality (load-bearing in Theorem")
    print("    XI). Wrong Γ collapses bound; right Γ insufficient.")
    print()
    print("  · If x is required to preserve the unrelativised hierarchy:")
    print("    equivalent to oracle-relativisation question; known to")
    print("    have positive + negative instances (Baker-Gill-Solovay).")
    print()
    print("  · If x is required to be POLYNOMIALLY-BOUNDED IN |G|: this")
    print("    IS the classical P vs NP question. Open.")
    print()
    print("  Jabberwock's answer: the conjecture's status depends")
    print("  entirely on the constraint we place on x. The framing as")
    print("  P(G) = NP(G + x) is itself useful — it makes the dependence")
    print("  on x explicit where classical P vs NP hides it. But this")
    print("  framing alone doesn't resolve the underlying open question.")


if __name__ == "__main__":
    main()
