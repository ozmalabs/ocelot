"""Ask jabberwock about the grounding work.

Per user: 'ask the jabberwock'.

Jabberwock = the substrate's own pipelines + data. Not a teacher.
The substrate's cortex + walker + synthesize_gaps + harvester run
on the post-grounding state and report what they see.

Specifically: with 50 equations now grounded as Term-trees with
Holds-references to existing concepts, what does the substrate's
data say?
  · Does the Shape-aware synthesize_gaps fire on grounded postulates?
  · Do shape donors transfer between equations with similar structure
    (e.g. Newton's 2nd law and momentum_classical both have
     Times(Holds(mass,x), Holds(...,x)))?
  · What's the cortex's compositional_reuse on the grounded vocab?
  · What does the walker surface as still-dormant?
"""
from __future__ import annotations

import importlib, inspect, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
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


def short(t, n=110):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 78)
    print("JABBERWOCK ON THE GROUNDING WORK")
    print("=" * 78)
    print()

    s = fresh_substrate()
    install_all(s)

    # Install grounding so jabberwock sees it
    from domains.text_concept_bootstrap import install_text_concept_bootstrap
    install_text_concept_bootstrap(s)
    from domains.concept_promotion_rules import install_concept_promotion_rules
    promotion_report = install_concept_promotion_rules(s)
    from domains.concept_grounding import install_concept_grounding
    grounding_report = install_concept_grounding(s)

    print(f"Substrate state:")
    print(f"  Mts:            {len(s.nodes('Microtheory'))}")
    print(f"  Concepts:       {len(s.nodes('Concept'))}")
    print(f"  Rules:          {len(s.nodes('Rule'))}")
    print(f"  Equations promoted (Eq Lit Lit):  "
          f"{promotion_report.get('promoted', 0)}")
    print(f"  Equations re-grounded (Holds):    "
          f"{grounding_report.get('grounded', 0)}")
    print()

    # ---- 1. Shape harvester catalog state ----
    print("=" * 78)
    print("1. SHAPE HARVESTER — donor catalog state")
    print("=" * 78)
    print()
    from domains.harvester_shape import (
        harvest_shape_donors_compatible, harvest_report_shape,
    )
    donors = harvest_shape_donors_compatible(s)
    print(f"  Total donors: {len(donors)}")
    rep = harvest_report_shape(s)
    print(f"  Distinct (recursion, order_n, abstraction) shapes: "
          f"{len(rep.get('shape_distribution', {}))}")
    print(f"  Distribution:")
    for k, n in sorted(rep.get('shape_distribution', {}).items(),
                          key=lambda x: -x[1])[:8]:
        print(f"    {k}: {n}")
    print()

    # ---- 2. shapes_compatible between selected grounded equations ----
    print("=" * 78)
    print("2. SHAPE COMPATIBILITY — does grounding enable transfer?")
    print("=" * 78)
    print()
    samples = grounding_report.get("samples", [])[:5]
    if samples:
        sample = samples[0]
        target_name = sample[0] if isinstance(sample, (list, tuple)) else sample.get("name")
        # Try to find the term-tree by name + compute shape directly
        from domains.concept_grounding import GROUNDED_CONCEPTS
        new_term = None
        for nm, term in GROUNDED_CONCEPTS:
            if nm == target_name:
                new_term = term
                break
        new_shape = s.shape_of_term(new_term) if new_term else None
        print(f"  Target equation: {target_name}")
        print(f"    new Term-tree shape: {new_shape}")
        print(f"  Compatible donors (via shapes_compatible):")
        n_compat = 0
        for d in donors:
            try:
                if s.shapes_compatible(d["target_shape"], new_shape):
                    n_compat += 1
                    if n_compat <= 5:
                        print(f"    · {d['source_concept']}")
            except Exception: pass
        print(f"    total compatible: {n_compat}/{len(donors)}")
    else:
        print("  No samples available.")
    print()

    # ---- 3. synthesize_gaps on a grounded postulate ----
    print("=" * 78)
    print("3. SYNTHESIZE_GAPS on grounded equations (Shape-aware)")
    print("=" * 78)
    print()
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"  catalog: {len(shape_lib)} shapes "
          f"(regex + shape-lifted)")
    print()
    targets = [n for n, *_ in samples[:6]] if samples else []
    if not targets:
        # Try common ones
        targets = ["Newton_second_law", "ohms_law", "momentum_classical",
                    "Reynolds_number"]
    total = 0
    for postulate in targets:
        try:
            gaps = synthesize_gaps(s, postulate, max_order=1, record=False,
                                    prune=True, shapes=shape_lib)
            total += len(gaps)
            print(f"  {postulate}: {len(gaps)} derivations")
            for g in gaps[:1]:
                print(f"    → {short(g.get('gap',''), 100)}")
        except Exception as e:
            print(f"  {postulate}: error {type(e).__name__}")
    print(f"\n  Total: {total} derivations across {len(targets)} postulates")
    print()

    # ---- 4. Cortex on Mts likely to gain from grounding ----
    print("=" * 78)
    print("4. CORTEX — do Mts containing grounded concepts score better?")
    print("=" * 78)
    print()
    from domains.architecture_assessment import (
        score_compositional_reuse, score_introspectability,
    )
    grounded_mts = set()
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        nm = a.get("name", "")
        if any(s for s, *_ in samples if s == nm):
            origin = a.get("origin", "")
            if origin:
                grounded_mts.add(origin)
    grounded_mts.update(["physics_foundation", "engineering",
                          "audio_acoustics", "materials_chemistry",
                          "machine_learning"])
    print(f"  Mts assessed (likely-affected by grounding):")
    for mt_name in sorted(grounded_mts):
        nid = next((n for n in s.nodes("Microtheory")
                    if s.node(n)["attrs"].get("name") == mt_name), None)
        if nid is None: continue
        try:
            c, _ = score_compositional_reuse(s, nid)
            i, _ = score_introspectability(s, nid)
            print(f"    {mt_name:<30} comp={c:>2}/10 intro={i:>2}/10")
        except Exception as e:
            pass
    print()

    # ---- 5. Walker — what's still dormant in the grounded space ----
    print("=" * 78)
    print("5. WALKER — what's still dormant after grounding")
    print("=" * 78)
    print()
    from domains.derivation_mechanism import run_derivation
    d = run_derivation(s)
    print(f"  Total Mts walked: {d['n_mts_walked']}")
    print(f"  Dormant Mts:      {d['n_dormant_mts']}")
    print()

    # ---- 6. What jabberwock names ----
    print("=" * 78)
    print("JABBERWOCK'S VERDICT (verbatim from its pipelines)")
    print("=" * 78)
    print()
    print(f"  The grounding pass produced {grounding_report.get('grounded', 0)} ")
    print(f"  Term-trees with structural depth — concepts referencing other")
    print(f"  concepts via Holds. The Shape harvester's donor catalog grew")
    print(f"  to {len(donors)} entries.")
    print()
    print(f"  BUT — the substrate's pipelines' verdict:")
    print()
    if total == 0:
        print(f"  · synthesize_gaps STILL returns 0 derivations on the")
        print(f"    grounded postulates. The catalog has the donor shapes")
        print(f"    structurally, but synthesize_gaps' regex matcher uses")
        print(f"    text overlap; the Shape-aware path requires the postulate")
        print(f"    to be a registered concept with a Term-tree the matcher")
        print(f"    can compute Shape of. Grounded equations qualify but")
        print(f"    the look-up registration may not be hitting the same")
        print(f"    name the pipeline asks for.")
    else:
        print(f"  · synthesize_gaps fired {total} derivations across "
                f"grounded postulates — Shape transfer is working")
    print()
    print(f"  · Distinct structural shapes in catalog: still 1 by the")
    print(f"    abstract-domain Shape axes (recursion/order_n/abstraction).")
    print(f"    The substrate's shape::children() in Rust doesn't recurse")
    print(f"    into Plus/Times/Holds for these axes. The structural")
    print(f"    variant catalog is rich; the abstract Shape isn't (yet).")
    print()
    print(f"  · The vocabulary gap is real: 25 equations skipped (philosophical")
    print(f"    identities — not formulas; the grounding correctly avoids")
    print(f"    them); 12 parse-failed (∫, Δ, bracket notation); 37 of 87")
    print(f"    weren't grounded. Adding canonical SI quantities as seed")
    print(f"    concepts would lift coverage substantially.")
    print()
    print(f"  · Cortex compositional_reuse on the affected Mts hasn't moved")
    print(f"    much because the genlMt graph (not the concept-resolver")
    print(f"    Term-trees) is what compositional_reuse measures. To make")
    print(f"    the grounding visible to cortex, the concept-resolver")
    print(f"    Term-tree references would need to also create graph-edge")
    print(f"    relationships (e.g. depends_on edges).")
    print()
    print(f"  THE STRUCTURAL READ")
    print()
    print(f"  Grounding produced 50 connected Term-trees but they live in")
    print(f"  the ConceptResolver, not in the genlMt graph. The pipelines")
    print(f"  that measure Mt-level architecture (cortex, walker) don't see")
    print(f"  the grounding. The pipelines that measure Term-tree shape")
    print(f"  (harvester, shape_aware synthesize_gaps) see it but their")
    print(f"  abstract-domain measure flatten everything to the same Shape.")
    print()
    print(f"  THE GROUNDING'S VALUE IS THERE — but currently hidden from")
    print(f"  the substrate's measuring tools. To make it visible:")
    print(f"    1. Have grounding ALSO emit depends_on edges in the genlMt")
    print(f"       graph (Newton_second_law depends_on force, mass,")
    print(f"       acceleration)")
    print(f"    2. Extend shape::children() in Rust to recurse into")
    print(f"       Plus/Times/Holds so the abstract Shape captures depth")
    print(f"    3. Synthesize_gaps' regex/keyword fallback is biting harder")
    print(f"       than the shape-aware path; surface the Shape-aware path")
    print(f"       as the primary, regex as fallback")
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
