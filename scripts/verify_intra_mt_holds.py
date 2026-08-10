"""Verify refactor K — intra-Mt Holds wiring.

Steps:
  1. Bring up a fresh substrate; install every seed.
  2. Measure baseline:
       · intra-Mt connections (per ask_jabberwock_deeper.out §3 logic)
       · cortex compositional_reuse on the 12 large Mts.
  3. Run install_intra_mt_holds.
  4. Re-measure.
  5. Print delta.
"""
from __future__ import annotations

import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    for t in ("Microtheory", "Concept", "Rule"):
        for u in ("Microtheory", "Concept", "Rule"):
            for et in ("has_concept", "has_rule", "genlMt", "depends_on",
                       "owns_microtheory"):
                try:
                    s.add_production({
                        "src": {"type": t, "var": "a"},
                        "edge_type": et,
                        "tgt": {"type": u, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "verify_intra_mt",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    installed = []
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
                    installed.append((f.stem, m.group(1)))
            except Exception:
                continue
    return installed


def _holds_refs_in(term):
    out = []
    if isinstance(term, dict):
        if term.get("type") == "Holds":
            c = term.get("concept")
            if isinstance(c, str):
                out.append(c)
        for v in term.values():
            if isinstance(v, (dict, list)):
                out.extend(_holds_refs_in(v))
    elif isinstance(term, list):
        for x in term:
            out.extend(_holds_refs_in(x))
    return out


def survey_intra_mt(s):
    """Compute intra-Mt Holds connection counts per Mt, per the same
    logic as ask_jabberwock_deeper.out §3."""
    from domains.concept_promotion_rules import PROMOTED_CONCEPTS
    try:
        from domains.concept_grounding import GROUNDED_CONCEPTS
    except Exception:
        GROUNDED_CONCEPTS = []

    term_lookup = {}
    for nm, term in PROMOTED_CONCEPTS:
        term_lookup[nm] = term
    for nm, term in GROUNDED_CONCEPTS:
        term_lookup[nm] = term

    mt_concepts = {}
    for mt in s.nodes("Microtheory"):
        nm = s.node(mt)["attrs"].get("name", "?")
        concepts = set()
        for c in s.neighbours(mt, "has_concept"):
            cn = s.node(c)["attrs"].get("name", "")
            if cn:
                concepts.add(cn)
        mt_concepts[nm] = concepts

    per_mt: dict[str, int] = {}
    n_flat = 0
    n_with = 0
    for mt_name, concepts in mt_concepts.items():
        intra = 0
        for cn in concepts:
            term = term_lookup.get(cn)
            if term is None:
                continue
            refs = set(_holds_refs_in(term))
            siblings = refs & (concepts - {cn})
            if siblings:
                intra += 1
        per_mt[mt_name] = intra
        if not concepts:
            continue
        if intra == 0:
            n_flat += 1
        else:
            n_with += 1
    return per_mt, n_flat, n_with, mt_concepts


def score_cortex_compositional_reuse_for_mts(s, mt_name_list):
    """Apply the cortex compositional_reuse formula directly to a set of
    Mts, summing inbound depends_on edges on each Mt's concepts (the
    grounding-aware path)."""
    out: dict[str, dict] = {}
    for mt in s.nodes("Microtheory"):
        nm = s.node(mt)["attrs"].get("name", "?")
        if nm not in mt_name_list:
            continue
        inbound_mt = 0
        inbound_concept = 0
        for nid in s.in_neighbours(mt, "genlMt"):
            inbound_mt += 1
        for c in s.neighbours(mt, "has_concept"):
            for nid in s.in_neighbours(c, "depends_on"):
                inbound_concept += 1
        weighted = inbound_mt * 3 + inbound_concept
        score = max(0, min(10, weighted // 3))
        out[nm] = {
            "inbound_mt": inbound_mt,
            "inbound_concept": inbound_concept,
            "weighted": weighted,
            "score": score,
        }
    return out


TARGET_MTS = [
    "engineering",
    "video_coding_theory",
    "computer_architecture",
    "mathematics",
    "databases_and_storage",
    "embedded_iot_realtime",
    "security_and_cryptography",
    "art_design_drawing",
    "cloud_infrastructure",
    "philosophy",
    "data_structures_algorithms",
    "operating_systems",
]


def main():
    print("=" * 78)
    print("VERIFY refactor K — intra-Mt Holds wiring")
    print("=" * 78)

    s = fresh_substrate()
    installed = install_all(s)
    print(f"  Installed {len(installed)} seeds")
    print(f"  Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts")
    print()

    # --- baseline.
    per_mt_b, flat_b, with_b, mt_concepts = survey_intra_mt(s)
    cortex_before = score_cortex_compositional_reuse_for_mts(s, TARGET_MTS)
    n_depends_on_before = 0
    for c in s.nodes("Concept"):
        n_depends_on_before += len(s.neighbours(c, "depends_on"))

    print(f"  BEFORE: {flat_b} flat Mts, {with_b} connected Mts")
    print(f"  Total depends_on edges (Concept→Concept): {n_depends_on_before}")
    print()
    print(f"  Cortex compositional_reuse on 12 target Mts (BEFORE):")
    avg_before = 0
    for mt in TARGET_MTS:
        info = cortex_before.get(mt, {})
        sc = info.get("score", "?")
        ic = info.get("inbound_concept", "?")
        avg_before += info.get("score", 0)
        print(f"    {mt:<32}  score={sc:>2}  inbound_concept={ic}")
    avg_before /= len(TARGET_MTS)
    print(f"    AVG SCORE BEFORE: {avg_before:.2f}/10")
    print()

    # --- apply refactor.
    print("  Applying install_intra_mt_holds ...")
    from domains.intra_mt_holds import install_intra_mt_holds
    report = install_intra_mt_holds(s)
    print(f"    mts_processed:     {report['mts_processed']}")
    print(f"    mts_with_refs:     {report['mts_with_refs']}")
    print(f"    edges_added:       {report['edges_added']}")
    print(f"    terms_registered:  {report['terms_registered']}")
    print(f"    terms_extended:    {report['terms_extended']}")
    print()

    # --- after.
    per_mt_a, flat_a, with_a, _ = survey_intra_mt(s)
    cortex_after = score_cortex_compositional_reuse_for_mts(s, TARGET_MTS)
    n_depends_on_after = 0
    for c in s.nodes("Concept"):
        n_depends_on_after += len(s.neighbours(c, "depends_on"))

    print(f"  AFTER: {flat_a} flat Mts, {with_a} connected Mts")
    print(f"  Total depends_on edges (Concept→Concept): {n_depends_on_after}")
    print(f"  Delta depends_on: +{n_depends_on_after - n_depends_on_before}")
    print()
    print(f"  Cortex compositional_reuse on 12 target Mts (AFTER):")
    avg_after = 0
    for mt in TARGET_MTS:
        info = cortex_after.get(mt, {})
        sc = info.get("score", "?")
        ic = info.get("inbound_concept", "?")
        old = cortex_before.get(mt, {}).get("score", 0)
        delta = info.get("score", 0) - old
        avg_after += info.get("score", 0)
        print(f"    {mt:<32}  score={sc:>2}  inbound_concept={ic}  "
              f"Δscore={delta:+d}")
    avg_after /= len(TARGET_MTS)
    print(f"    AVG SCORE AFTER:  {avg_after:.2f}/10  "
          f"(Δ = {avg_after - avg_before:+.2f})")
    print()

    # Sample per Mt.
    print(f"  Sample intra-Mt references — top 5 Mts by connections:")
    for mt_name, samples in report["sample_per_mt"].items():
        n = report["per_mt_breakdown"].get(mt_name, 0)
        print(f"    {mt_name}  ({n} intra-Mt connections):")
        for src, refs in samples:
            print(f"      · {src} → {refs}")
    print()

    # Largest intra-Mt connection deltas per Mt.
    print(f"  Intra-Mt connections per Mt (top 15):")
    rows = sorted(report["per_mt_breakdown"].items(),
                  key=lambda kv: -kv[1])[:15]
    for mt, n in rows:
        bn = per_mt_b.get(mt, 0)
        an = per_mt_a.get(mt, 0)
        print(f"    {mt:<36}  intra-concepts(before/after)={bn}/{an}  "
              f"edges_added={n}")
    print()


if __name__ == "__main__":
    main()
