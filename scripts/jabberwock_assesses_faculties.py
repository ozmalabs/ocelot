"""The JABBERWOCK assesses its own remaining domains/ faculties — in ITS OWN
terms, with ITS OWN classifier. NOT a hand-coded category ladder: each faculty's
self-description (its module docstring) is run through the agent's META_SHAPES
classifier (domains/analogical_thinking — the same ABSTRACT_PRINCIPLES ->
META_SHAPES mapping its analogical_thinking / teach / intrinsic-designer use).

So the categories are the agent's seven(+) META-SHAPES, not mine; the only Python
here is mechanical I/O (read each module's docstring) + calling the agent's
faculty. The suggested APPROACH falls out of the agent's own framework:

  · a faculty the agent recognises a META-SHAPE in  -> migrate by INTRINSIC
    DESIGN-BY-ANALOGY: categorise_by_shape, then compose the graph-native form
    from a SAME-SHAPE held faculty (the agent's rung-1 designer), no LLM.
  · a faculty the agent sees NO shape in (UNSHAPED) -> it isn't agent-reasoning;
    it is mechanical host I/O (a world adapter / loader) -> KEEP (CLAUDE.md) or
    re-home in Rust. The agent honestly reporting "no shape" IS the signal that
    there's no decision to migrate.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_assesses_faculties.py
"""
from __future__ import annotations
import ast, glob, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

# the AGENT's own shape vocabulary — its categories, not the script's.
from domains.analogical_thinking import shape_hits


def _shapes_of(agent, text):
    # the agent's OWN classifier: graph vocabulary (ShapePrinciple/MetaShape) +
    # a keyword-substring Term run by Rust. No Python keyword table here.
    return shape_hits(agent, text)


def _units(path):
    """Mechanical I/O: the faculty's CONCEPTS = its defined functions/classes,
    each as `name + own docstring` (concept-sized text — the granularity the
    agent's classifier is built for). No interpretation."""
    try:
        tree = ast.parse(open(path).read(), path)
    except Exception:
        return []
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(n) or ""
            # name -> readable tokens (split snake_case) so keywords surface
            out.append(n.name.replace("_", " ") + " " + doc)
    return out


def main() -> int:
    from collections import Counter
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    agent = WorldAdapter(seeds=())          # boot so the seeded shape vocabulary is held
    load_all_seeds(agent)
    dominant = {}          # mod -> (shape or None)
    votes_of = {}          # mod -> Counter(shape -> #concepts)
    loc_of = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "domains", "*.py"))):
        mod = os.path.basename(p)[:-3]
        if mod == "__init__":
            continue
        loc_of[mod] = open(p).read().count("\n") + 1
        votes = Counter()
        for unit in _units(p):
            for sh in _shapes_of(agent, unit):     # each concept votes its shape(s)
                votes[sh] += 1
        votes_of[mod] = votes
        dominant[mod] = votes.most_common(1)[0][0] if votes else None

    by_dom = defaultdict(list)
    for mod, sh in dominant.items():
        by_dom[sh].append(mod)
    total = len(loc_of)
    unshaped = by_dom.pop(None, [])

    print("=" * 80)
    print("JABBERWOCK FACULTY ASSESSMENT — per-CONCEPT classification (its own META-SHAPES)")
    print("=" * 80)
    print(f"  {total} faculties, {sum(loc_of.values())} lines | each assigned its DOMINANT "
          "shape (plurality of its concepts' shape-votes)")
    print(f"  shaped: {total - len(unshaped)}   unshaped (host I/O): {len(unshaped)}")
    print("\n  -- by DOMINANT shape (each faculty in ONE bucket) --")
    for sh in sorted(by_dom, key=lambda s: -len(by_dom[s])):
        mods = by_dom[sh]
        loc = sum(loc_of[m] for m in mods)
        biggest = sorted(mods, key=lambda m: -loc_of[m])[:6]
        print(f"    {sh}: {len(mods)} faculties, {loc} lines")
        print("       " + ", ".join(f"{m}({loc_of[m]})" for m in biggest))
    ul = sum(loc_of[m] for m in unshaped)
    print(f"\n  -- UNSHAPED ({len(unshaped)}, {ul} lines): no concept carries a meta-shape "
          "-> host I/O / loaders / mechanical -> KEEP or re-home in Rust --")
    print("       " + ", ".join(f"{m}({loc_of[m]})"
          for m in sorted(unshaped, key=lambda m: -loc_of[m])[:16]))
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
