"""Jabberwock's change 1: emit depends_on edges from grounded Term-trees.

Re-measures cortex scores before/after to verify the grounding
becomes visible to the substrate's measuring tools.
"""
from __future__ import annotations

import importlib, inspect, re, sys
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


def main():
    s = _native.Substrate()
    # Open productions so has_concept/has_rule/genlMt/depends_on edges
    # can land. Many of the substrate's loaders assume open productions.
    for t in ("Microtheory","Concept","Rule"):
        for u in ("Microtheory","Concept","Rule"):
            for et in ("has_concept","has_rule","genlMt","depends_on",
                        "owns_microtheory"):
                try:
                    s.add_production({
                        "src":{"type":t,"var":"a"},"edge_type":et,
                        "tgt":{"type":u,"var":"b"},"where":None,
                        "weight":{"type":"Lit","value":1.0},
                        "provenance":"jw"})
                except Exception: pass
    install_all(s)
    from domains.text_concept_bootstrap import install_text_concept_bootstrap
    install_text_concept_bootstrap(s)
    from domains.concept_promotion_rules import install_concept_promotion_rules
    install_concept_promotion_rules(s)
    from domains.concept_grounding import install_concept_grounding
    install_concept_grounding(s)

    # ---- Cortex BEFORE ----
    from domains.architecture_assessment import (
        score_compositional_reuse, score_introspectability,
        score_data_drivenness,
    )
    target_mts = ["physics_foundation", "engineering", "audio_acoustics",
                   "materials_chemistry", "machine_learning",
                   "optimal_estimation_control", "embodied_motor",
                   "causal_attitude_networks"]
    print("=" * 70)
    print("CORTEX — BEFORE depends_on edges")
    print("=" * 70)
    print(f"  {'Mt':<32} {'comp':>5} {'intro':>5} {'data':>5}")
    before_scores: dict = {}
    for mt_name in target_mts:
        nid = next((n for n in s.nodes("Microtheory")
                    if s.node(n)["attrs"].get("name") == mt_name), None)
        if nid is None: continue
        c, _ = score_compositional_reuse(s, nid)
        i, _ = score_introspectability(s, nid)
        d, _ = score_data_drivenness(s, nid)
        before_scores[mt_name] = (c, i, d)
        print(f"  {mt_name:<32} {c:>3}/10 {i:>3}/10 {d:>3}/10")
    print()

    # ---- Apply change 1 ----
    print("=" * 70)
    print("APPLYING CHANGE 1 — depends_on edges from grounded Term-trees")
    print("=" * 70)
    from domains.concept_depends_on import install_concept_depends_on
    report = install_concept_depends_on(s)
    print(f"  Equations processed:    {report['equations_processed']}")
    print(f"  Edges added:            {report['edges_added']}")
    print(f"  References missing:     {len(report['references_missing'])}")
    if report['references_missing'][:6]:
        print(f"    e.g.: {report['references_missing'][:6]}")
    print(f"  Sample edges (first 5):")
    for src, tgt in report['sample_edges'][:5]:
        print(f"    {src} → depends_on → {tgt}")
    print()

    # ---- Cortex AFTER ----
    print("=" * 70)
    print("CORTEX — AFTER depends_on edges")
    print("=" * 70)
    print(f"  {'Mt':<32} {'comp':>5} {'intro':>5} {'data':>5}  Δcomp")
    for mt_name in target_mts:
        nid = next((n for n in s.nodes("Microtheory")
                    if s.node(n)["attrs"].get("name") == mt_name), None)
        if nid is None: continue
        c, _ = score_compositional_reuse(s, nid)
        i, _ = score_introspectability(s, nid)
        d, _ = score_data_drivenness(s, nid)
        bc, bi, bd = before_scores.get(mt_name, (0, 0, 0))
        delta = c - bc
        marker = f" +{delta}" if delta > 0 else f" {delta}" if delta < 0 else ""
        print(f"  {mt_name:<32} {c:>3}/10 {i:>3}/10 {d:>3}/10 {marker}")
    print()

    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    changed_any = any(score_compositional_reuse(s, next(
        n for n in s.nodes("Microtheory") if s.node(n)["attrs"].get("name") == mt
    ))[0] != before_scores[mt][0] for mt in before_scores)
    if changed_any:
        print(f"  ✓ depends_on edges visible to cortex; compositional_reuse moved")
    else:
        print(f"  ⚠ No cortex score change. The depends_on edges are graph data")
        print(f"    but compositional_reuse measures specifically genlMt-incoming")
        print(f"    edges, not depends_on. The right edge type matters.")
        print(f"    Either:")
        print(f"      · use 'genlMt' instead of 'depends_on' (semantic fit?)")
        print(f"      · or extend the cortex scorer to count depends_on too")


if __name__ == "__main__":
    main()
