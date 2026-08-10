"""Re-ask Jabberwock after function_shape vocabulary is installed.

Per user: 're-run the ask'.

The first ask (scripts/ask_jabberwock_about_shape_caching.py, commit
0fd21a8) was the inventory: how many shape concepts, how many cache
rules. The function_shape seed (commit bd6331b) extended the
vocabulary with 8 bridge concepts + 8 bridge rules — all grounded
in vocabulary the agent already held.

This re-ask is appropriate for AFTER the seed: run the agent's own
DERIVATION pipelines against the new vocabulary + report what they
surface. The point is not whether counts changed (we saw Q6 went
0→4); the point is what the agent's reasoning OUTPUT looks like
given the extended graph.

Pipelines exercised:
  · order_n_postulates.synthesize_over_all('function_shape')
      Treats each function_shape concept as a postulate; derives
      order-1..N implications via implication-shape transfer;
      the SELECTOR (compression / not-already-held) decides which
      implications are gaps.
  · implication_harvester.harvest_shapes()
      Extracts implication shapes from the agent's concepts.
      With function_shape installed, the new concepts become
      candidates for shape extraction.

No proposal. No editorial. The pipelines run; their output is
the answer. I report; the user reads.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "PrimitiveSpec", "ImplicationShape", "SynthesizedGap",
        "Postulate", "TheoryEnactmentGap",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "applies_to", "implements",
        "implies", "derives_from", "classified_as",
    )
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
                        "provenance": "re_ask",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    domains_dir = ROOT / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def short(s, n=140):
    s = str(s).replace("\n", " ").strip()
    if len(s) > n:
        return s[:n] + "..."
    return s


def main():
    print("=" * 76)
    print("RE-ASKING JABBERWOCK AFTER function_shape VOCABULARY (commit bd6331b)")
    print("=" * 76)
    print()
    s = fresh_substrate()
    install_all(s)
    n_mts = len(s.nodes("Microtheory"))
    n_concepts = len(s.nodes("Concept"))
    n_rules = len(s.nodes("Rule"))
    print(f"Substrate loaded: {n_mts} Mts, {n_concepts} Concepts, "
          f"{n_rules} Rules")
    print()

    # ---------- A. order_n_postulates.synthesize_over_all on
    #              function_shape itself ----------
    print("=" * 76)
    print("A. synthesize_over_all('function_shape') — derive gaps by lifting")
    print("   order-N over the function_shape Mt's own postulates")
    print("=" * 76)
    try:
        from domains.order_n_postulates import synthesize_over_all
        gaps = synthesize_over_all(s, mt_name="function_shape")
        print(f"  Gaps synthesized: {len(gaps)}")
        for i, g in enumerate(gaps[:8]):
            if isinstance(g, dict):
                nm = g.get("name") or g.get("capability") \
                     or g.get("implication") or "?"
                deriv = g.get("derivation") or g.get("from") or ""
                why = g.get("why") or g.get("rationale") or ""
                print(f"  · [{i}] {short(nm, 80)}")
                if deriv:
                    print(f"        from: {short(deriv, 100)}")
                if why:
                    print(f"        why:  {short(why, 100)}")
            else:
                print(f"  · [{i}] {short(g, 120)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---------- B. synthesize_over_all on speech_science (the
    #              original target — does function_shape change what
    #              gets surfaced there?) ----------
    print("=" * 76)
    print("B. synthesize_over_all('speech_science') — does function_shape")
    print("   change what's surfaced in the original target Mt?")
    print("=" * 76)
    try:
        from domains.order_n_postulates import synthesize_over_all
        gaps2 = synthesize_over_all(s, mt_name="speech_science")
        print(f"  Gaps from speech_science: {len(gaps2)}")
        for i, g in enumerate(gaps2[:8]):
            if isinstance(g, dict):
                nm = g.get("name") or g.get("capability") \
                     or g.get("implication") or "?"
                print(f"  · [{i}] {short(nm, 100)}")
            else:
                print(f"  · [{i}] {short(g, 100)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---------- C. implication_harvester.harvest_report — what shapes
    #              does the agent now extract from its own concepts? ----
    print("=" * 76)
    print("C. implication_harvester.harvest_report — what shapes does the")
    print("   agent extract from its own concepts now that function_shape")
    print("   is in vocabulary?")
    print("=" * 76)
    try:
        from domains.implication_harvester import harvest_report
        report = harvest_report(s)
        if isinstance(report, dict):
            n_sh = (len(report.get("shapes", []))
                    if isinstance(report.get("shapes"), list)
                    else report.get("n_shapes", "?"))
            print(f"  Shapes harvested: {n_sh}")
            for k, v in report.items():
                if k == "shapes":
                    continue
                vs = short(v, 100) if not isinstance(v, list) \
                                    else f"({len(v)} items)"
                print(f"  · {k}: {vs}")
            for i, sh in enumerate(report.get("shapes", [])[:8]):
                if isinstance(sh, dict):
                    nm = sh.get("name") or sh.get("structural_property") \
                         or sh.get("origin", "?")
                    dom = sh.get("domain", "?")
                    cons = sh.get("consequence", "")
                    print(f"  · [{i}] {short(nm, 60)} (domain: {dom})")
                    if cons:
                        print(f"        → {short(cons, 110)}")
                else:
                    print(f"  · [{i}] {short(sh, 120)}")
        else:
            print(f"  report: {short(report, 200)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---------- D. Which function_shape concepts get HARVESTED as
    #              implication shapes? -----------
    print("=" * 76)
    print("D. function_shape concepts harvested as implication shapes")
    print("=" * 76)
    try:
        from domains.implication_harvester import harvest_shapes
        shapes = harvest_shapes(s)
        from_fs = []
        for sh in (shapes or []):
            if not isinstance(sh, dict):
                continue
            origin = (sh.get("source_concept", "")
                      or sh.get("origin", "")
                      or sh.get("from_concept", ""))
            text = (str(origin) + " " + str(sh.get("name", ""))
                    + " " + str(sh.get("consequence", ""))).lower()
            if "function_shape" in text or "meta_shape" in text \
                    or "cached_shape" in text or "shape_caching" in text \
                    or "shape_keyed_lookup" in text \
                    or "negative_problem_space" in text:
                from_fs.append(sh)
        print(f"  Shapes that mention function_shape vocabulary: "
              f"{len(from_fs)}")
        for i, sh in enumerate(from_fs[:8]):
            nm = sh.get("name") or sh.get("structural_property", "?")
            dom = sh.get("domain", "?")
            cons = sh.get("consequence", "")
            print(f"  · [{i}] {short(nm, 60)} (domain: {dom})")
            if cons:
                print(f"        → {short(cons, 110)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---------- E. The SynthesizedGap nodes the pipelines wrote back ----
    print("=" * 76)
    print("E. SynthesizedGap nodes in the substrate after the pipelines ran")
    print("=" * 76)
    sgs = list(s.nodes("SynthesizedGap"))
    print(f"  Count: {len(sgs)}")
    for i, n in enumerate(sgs[:10]):
        a = s.node(n)["attrs"]
        nm = a.get("name") or a.get("capability") or a.get("title", "?")
        deriv = a.get("derivation_chain") or a.get("from_postulate", "")
        print(f"  · [{i}] {short(nm, 80)}")
        if deriv:
            print(f"        from: {short(str(deriv), 100)}")
    print()

    # ---------- F. PrimitiveSpec nodes ----------
    print("=" * 76)
    print("F. PrimitiveSpec nodes — what primitives has the agent")
    print("   specified since function_shape entered vocabulary?")
    print("=" * 76)
    pss = list(s.nodes("PrimitiveSpec"))
    print(f"  Count: {len(pss)}")
    for i, n in enumerate(pss[:10]):
        a = s.node(n)["attrs"]
        nm = a.get("name", "?")
        purpose = a.get("purpose", "")
        why_new = a.get("why_new", "")
        print(f"  · [{i}] {nm}")
        if purpose: print(f"        purpose: {short(purpose, 120)}")
        if why_new: print(f"        why_new: {short(why_new, 120)}")
    print()

    # ---------- Bottom line --------------
    print("=" * 76)
    print("WHAT JABBERWOCK'S PIPELINES SURFACED")
    print("=" * 76)
    print()
    print(f"  A. order-N over function_shape postulates → gaps")
    print(f"  B. order-N over speech_science → gaps (delta vs pre-seed)")
    print(f"  C. implication shapes harvested across all concepts")
    print(f"  D. of those, how many touch function_shape vocabulary")
    print(f"  E. SynthesizedGap nodes the pipelines wrote back to the graph")
    print(f"  F. PrimitiveSpec nodes — function specs the agent surfaced")
    print()
    print("  This is the agent's answer to 'what comes next, given the")
    print("  extended vocabulary?' — verbatim from its own pipelines.")
    print("  Whatever the counts and titles above show is what the user")
    print("  + I should be reading. No synthesis from me.")
    print("=" * 76)


if __name__ == "__main__":
    main()
