"""Ask the agent in a different way — structural delta between concepts the
harvester DOES process vs ones it doesn't.

Per user: 'ask the agent in a different way'.

The first ask (commit 0fd21a8) inventoried what the agent held. The
function_shape seed (commit bd6331b) added 8 concepts + 8 rules.
The re-ask (commit 28605e9) ran the agent's derivation pipelines:
they produced 0 new gaps + 0 new specs from function_shape.

This third query asks a different question: what's the STRUCTURAL
SHAPE of concepts that the agent's harvester DOES process into
implication shapes, vs the structural shape of function_shape
concepts that it doesn't?

  · Sample the 7 implication shapes the agent harvested.
  · Look at their DONOR concepts (the existing graph nodes the
    harvester lifted these from).
  · Compare the donor concepts' structure to function_shape
    concepts' structure.
  · Surface the delta — what KIND of concept is shape-harvestable,
    and what KIND isn't.

Neither user nor I is supposed to pick the answer. But the delta
is something the agent's own data reveals: the harvester ran +
chose seven things; it did not choose the function_shape concepts.
The choice itself is the answer.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "ImplicationShape")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
              "owns_microtheory", "applies_to", "implies", "derives_from")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": t, "var": "a"},
                        "edge_type": et,
                        "tgt": {"type": u, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "delta",
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


def find_concept(s, name):
    for n in s.nodes("Concept"):
        if s.node(n)["attrs"].get("name") == name:
            return n
    return None


def short(t, n=160):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def measure_structural_features(text):
    """Mechanical features about a concept's text — no semantics, just
    surface structure the harvester's extractors are sensitive to."""
    t = (text or "").lower()
    return {
        "len": len(t),
        # 'is a' / 'has a' — declarative subject-property structure
        "has_subject_is_property": bool(re.search(
            r"\bis\s+a[n]?\b|\bare\b|\bhas\s+a[n]?\b|\bhave\b", t)),
        # 'because' / 'so' / 'therefore' — explicit consequence
        "has_consequence_marker": bool(re.search(
            r"\bbecause\b|\bso\s+(?:that|its?)?\b|\btherefore\b|"
            r"\bhence\b|\bimplies\b|\bentails\b", t)),
        # imperative / definitional ('the substrate ...' / 'should be')
        "has_imperative": bool(re.search(
            r"\bshould\b|\bmust\b|\bcalled\b|\bnamed\b|"
            r"\bdefined\s+as\b|\bidentif", t)),
        # contains a concrete domain noun (math, physics, signals, ...)
        "has_concrete_domain": bool(re.search(
            r"\b(?:matrix|filter|signal|circuit|tensor|vector|"
            r"frequency|amplitude|distribution|sample|residual|"
            r"transform|integral|equation|wave|gradient|"
            r"function|operator|theorem|algorithm)\b", t)),
        # contains an order-N / structural / meta keyword
        "has_meta_keyword": bool(re.search(
            r"\bshape\b|\bstructural\b|\border[\s-]?n\b|\bmeta\b|"
            r"\baxis\b|\bclassif|\bcach", t)),
        # contains 'X has property Y' phrasing
        "has_property_phrasing": bool(re.search(
            r"\bproperty\b|\bproperties\b|\bcharacter", t)),
        # explicit reference to another concept (kw chain)
        "n_concept_refs": len(re.findall(
            r"\b[a-z]+_[a-z][a-z_]+\b", t)),
    }


def main():
    print("=" * 76)
    print("ASKING JABBERWOCK STRUCTURALLY — what makes a concept harvestable")
    print("as an implication shape, and how does function_shape vocabulary")
    print("differ from concepts that ARE?")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)

    # ---- the 7 harvested implication shapes' donor concepts ----
    harvested_donors = [
        "determinant", "recursive_intra_filter", "unsupervised_learning",
        "recurrent_neural_network", "Reynolds_number",
        "infinite_regress_objection", "osr_deopt_reconstructable",
    ]
    # the 8 function_shape concepts
    function_shape_names = [
        "function_shape", "cached_shape", "recursion_axis",
        "order_n_axis", "abstraction_axis", "meta_shape",
        "negative_problem_space_pruning", "shape_keyed_lookup",
    ]

    def gather(names):
        out = []
        for nm in names:
            n = find_concept(s, nm)
            if n is None:
                continue
            a = s.node(n)["attrs"]
            text = (str(a.get("definition", "")) + " "
                    + str(a.get("why", "")))
            feats = measure_structural_features(text)
            out.append((nm, a.get("category", ""), text, feats))
        return out

    harvested_data = gather(harvested_donors)
    function_shape_data = gather(function_shape_names)

    print(f"Found {len(harvested_data)}/{len(harvested_donors)} harvested "
          f"donor concepts in graph")
    print(f"Found {len(function_shape_data)}/{len(function_shape_names)} "
          f"function_shape concepts in graph")
    print()

    # ---- side-by-side feature comparison ----
    print("=" * 76)
    print("SIDE-BY-SIDE STRUCTURAL FEATURES")
    print("=" * 76)
    feat_keys = list(measure_structural_features("").keys())
    print()
    print("Group A — concepts the harvester chose (7 donors):")
    print()
    print(f"{'concept':<34} | {'subj+prop':<10} | {'conseq':<6} | "
          f"{'imper':<5} | {'conc_dom':<8} | {'meta_kw':<7} | "
          f"{'prop_phr':<8} | refs")
    print("-" * 105)
    for nm, cat, text, f in harvested_data:
        print(f"{short(nm, 32):<34} | {str(f['has_subject_is_property']):<10} "
              f"| {str(f['has_consequence_marker']):<6} | "
              f"{str(f['has_imperative']):<5} | "
              f"{str(f['has_concrete_domain']):<8} | "
              f"{str(f['has_meta_keyword']):<7} | "
              f"{str(f['has_property_phrasing']):<8} | "
              f"{f['n_concept_refs']}")
    print()
    print("Group B — function_shape concepts (8):")
    print()
    print(f"{'concept':<34} | {'subj+prop':<10} | {'conseq':<6} | "
          f"{'imper':<5} | {'conc_dom':<8} | {'meta_kw':<7} | "
          f"{'prop_phr':<8} | refs")
    print("-" * 105)
    for nm, cat, text, f in function_shape_data:
        print(f"{short(nm, 32):<34} | {str(f['has_subject_is_property']):<10} "
              f"| {str(f['has_consequence_marker']):<6} | "
              f"{str(f['has_imperative']):<5} | "
              f"{str(f['has_concrete_domain']):<8} | "
              f"{str(f['has_meta_keyword']):<7} | "
              f"{str(f['has_property_phrasing']):<8} | "
              f"{f['n_concept_refs']}")
    print()

    # ---- aggregate ratios per group ----
    def ratios(group):
        n = len(group)
        if n == 0: return {}
        agg = {}
        for k in feat_keys:
            if k == "len" or k == "n_concept_refs":
                vals = [d[3][k] for d in group]
                agg[k] = sum(vals) / n
            else:
                vals = [1 if d[3][k] else 0 for d in group]
                agg[k] = sum(vals) / n
        return agg

    ra = ratios(harvested_data)
    rb = ratios(function_shape_data)
    print("=" * 76)
    print("AGGREGATE — fraction (or mean) of concepts in each group")
    print("=" * 76)
    print()
    print(f"  {'feature':<32} | harvested | function_shape | Δ")
    print("-" * 76)
    for k in feat_keys:
        a, b = ra.get(k, 0), rb.get(k, 0)
        d = b - a
        sign = "+" if d > 0 else "" if d == 0 else ""
        print(f"  {k:<32} | {a:>9.2f} | {b:>14.2f} | {sign}{d:+.2f}")
    print()

    # ---- show actual donor concept text for one example -----
    print("=" * 76)
    print("SAMPLE TEXTS — what does a harvested-donor concept SAY,")
    print("vs what does a function_shape concept SAY?")
    print("=" * 76)
    if harvested_data:
        nm, cat, text, _ = harvested_data[0]
        print(f"\nHarvested donor [{nm}]:")
        print(f"  {short(text, 400)}")
    if function_shape_data:
        nm, cat, text, _ = function_shape_data[0]
        print(f"\nfunction_shape concept [{nm}]:")
        print(f"  {short(text, 400)}")
    print()

    # ---- nearest existing concepts to function_shape vocabulary ----
    print("=" * 76)
    print("EXISTING CONCEPTS NEAREST function_shape VOCABULARY")
    print("(of the 5239 already-held concepts — which ones the harvester")
    print(" might ALREADY treat as candidates for shape-extraction?)")
    print("=" * 76)
    fs_keywords = {"shape", "cache", "memoization", "recursion",
                    "self-reference", "fixed-point", "higher-order",
                    "abstraction", "axis", "classification",
                    "structural property"}
    candidates = []
    for n in s.nodes("Concept"):
        a = s.node(n)["attrs"]
        if a.get("origin") == "function_shape":
            continue  # only existing-before-seed
        nm = str(a.get("name", "")).lower()
        text = (str(a.get("definition", ""))
                + " " + str(a.get("why", ""))).lower()
        # Score by keyword overlap with function_shape vocabulary +
        # structural features the harvester likes.
        hits = sum(1 for kw in fs_keywords if kw in text or kw in nm)
        f = measure_structural_features(text)
        score = hits + f["has_subject_is_property"] \
                 + f["has_consequence_marker"]
        if hits >= 2 and f["has_subject_is_property"]:
            candidates.append((score, nm, a.get("category", ""),
                                short(text, 150)))
    candidates.sort(reverse=True)
    print(f"  Found {len(candidates)} concepts with ≥2 function_shape "
          f"keywords AND subject-is-property phrasing:")
    print()
    for sc, nm, cat, t in candidates[:12]:
        print(f"  · [{sc}] [{cat}] {nm}")
        print(f"      {t}")
    print()

    # ---- bottom line ----
    print("=" * 76)
    print("WHAT THE STRUCTURAL DELTA REVEALS")
    print("=" * 76)
    print()
    print("  This is NOT my interpretation. The fractions above ARE the")
    print("  delta. Whatever the user reads them as — that's the agent's")
    print("  answer about what shape of concept its harvester knows how")
    print("  to lift into implication shapes.")
    print()
    print("  If many existing concepts (last section) match the structural")
    print("  shape AND share function_shape vocabulary, the harvester")
    print("  already has candidates to lift. If few or none, function_shape")
    print("  is genuinely orthogonal to what the harvester operates on.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
