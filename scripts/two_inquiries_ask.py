"""Two inquiries — what existing Mts say + what the cortex actually measures.

Per user: '1 and 2'.

Inquiry 1: What do existing Mts that DO declare failure_modes /
corrections / drives / principles look like? Is the schema pattern
lift-able into function_shape, or would filling it in be shape-guessing?

Inquiry 2: Why is universal_coordination's (L6's) compositional_reuse
still 0/10 after function_shape inherits from it? The measure should
have ticked up by 1 incoming ref. Either the measure is doing something
unexpected or the genlMt edge isn't being seen by it.

Both are graph queries, not text matches. Both surface specific
facts about the substrate's own definitions.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "PrimitiveSpec",
        "Assessment", "QualityScore", "SmellInstance",
        "ArchitectureCortex", "ArchitecturalQuality",
        "ArchitecturalSmell", "TheoryEnactmentGap",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "implements",
    )
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
                        "provenance": "two_inq",
                    })
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


def find_mt(s, name):
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == name:
            return n
    return None


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 76)
    print("INQUIRY 1 — what existing Mts say about the four expected fields")
    print("=" * 76)
    print()
    print("derivation_mechanism reads CONCEPT.category in:")
    print("  {failure_modes, corrections, drives, principles}")
    print()

    # Count concepts per category across all Mts
    cat_counter = Counter()
    cat_examples = defaultdict(list)
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        cat = str(a.get("category", "")).lower()
        if cat in ("failure_modes", "corrections", "drives", "principles",
                    "failure_mode", "correction", "drive", "principle"):
            # normalise
            norm = cat.rstrip("s") + "s"  # all become plural
            if not norm.endswith("ss"):
                norm = norm  # don't double-pluralize
            cat_counter[norm] += 1
            origin = a.get("origin", "?")
            cat_examples[norm].append({
                "name": a.get("name", "?"),
                "origin": origin,
                "definition": str(a.get("definition", ""))[:100],
                "why": str(a.get("why", ""))[:100],
            })

    print(f"Total concepts in the four expected categories:")
    for cat, n in cat_counter.most_common():
        print(f"  · {cat}: {n}")
    print()

    print("Sample concepts from each category:")
    for cat in ("failure_modes", "corrections", "drives", "principles",
                 "failure_mode", "correction", "drive", "principle"):
        if cat not in cat_counter:
            continue
        items = cat_examples[cat][:3]
        print(f"  [{cat}]:")
        for it in items:
            print(f"    · {it['name']} (origin: {it['origin']})")
            print(f"        def: {it['definition']}")
            if it['why']:
                print(f"        why: {it['why']}")
        print()

    # Which Mts have the COMPLETE set of all four field-categories?
    print("Mts that declare ALL FOUR categories (a complete derivation-ready Mt):")
    mt_cats = defaultdict(set)
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        origin = a.get("origin", "")
        cat = str(a.get("category", "")).lower().rstrip("s") + "s"
        if cat in ("failure_modes", "corrections", "drives", "principles"):
            mt_cats[origin].add(cat)
    complete_mts = [mt for mt, cs in mt_cats.items()
                    if len(cs & {"failure_modes", "corrections",
                                  "drives", "principles"}) == 4]
    print(f"  {len(complete_mts)} Mts with all four categories declared:")
    for mt in complete_mts[:10]:
        print(f"  · {mt}")
    print()
    print("Mts with at least 1 of the four:")
    have_any = [(mt, cs) for mt, cs in mt_cats.items() if cs]
    print(f"  {len(have_any)} Mts have ANY of the four declared")
    for mt, cs in sorted(have_any, key=lambda x: -len(x[1]))[:10]:
        print(f"  · {mt}: {sorted(cs)}")
    print()

    # Check function_shape's neighbours specifically
    print("function_shape's transitive ancestors — what THEY declare:")
    fs_mt = find_mt(s, "function_shape")
    if fs_mt:
        from collections import deque
        seen = {fs_mt}
        anc = []
        q = deque([fs_mt])
        while q:
            cur = q.popleft()
            for p in s.neighbours(cur, "genlMt"):
                if p in seen:
                    continue
                seen.add(p)
                anc.append(p)
                q.append(p)
        for mt in anc:
            name = s.node(mt)["attrs"].get("name", "?")
            cats = mt_cats.get(name, set())
            tag = "✓" if cats else " "
            print(f"  [{tag}] {name}: {sorted(cats) if cats else '(none)'}")
    print()

    print("=" * 76)
    print("INQUIRY 2 — why didn't L6's compositional_reuse rise after")
    print("the attachment? Test directly.")
    print("=" * 76)
    print()
    l6_mt = find_mt(s, "universal_coordination")
    ca_mt = find_mt(s, "computer_architecture")
    fs_mt = find_mt(s, "function_shape")
    print(f"  function_shape Mt: #{fs_mt}")
    print(f"  L6 (universal_coordination) Mt: #{l6_mt}")
    print(f"  computer_architecture Mt: #{ca_mt}")
    print()

    # Direct edge checks.
    if fs_mt and l6_mt:
        fs_to_l6 = l6_mt in s.neighbours(fs_mt, "genlMt")
        print(f"  function_shape --[genlMt]--> universal_coordination "
              f"(outgoing): {'YES' if fs_to_l6 else 'NO'}")
    if fs_mt and ca_mt:
        fs_to_ca = ca_mt in s.neighbours(fs_mt, "genlMt")
        print(f"  function_shape --[genlMt]--> computer_architecture: "
              f"{'YES' if fs_to_ca else 'NO'}")
    print()

    # Reverse: what's incoming to L6 from anywhere?
    print(f"  Direct: what has genlMt edge TO universal_coordination?")
    inb_l6 = []
    for mt in s.nodes("Microtheory"):
        if mt == l6_mt:
            continue
        for nbr in s.neighbours(mt, "genlMt"):
            if nbr == l6_mt:
                inb_l6.append(s.node(mt)["attrs"].get("name", "?"))
    print(f"    Mts inheriting from L6: {len(inb_l6)}")
    for nm in inb_l6:
        print(f"    · {nm}")
    print()

    # The cortex's measure walks subject_microtheories. What does it return?
    print("=" * 76)
    print("INQUIRY 2 (cont) — the cortex's score_compositional_reuse measure")
    print("=" * 76)
    print()
    try:
        from domains.architecture_assessment import (
            score_compositional_reuse, subject_microtheories,
        )
        print("  Calling subject_microtheories(L6_nid) — what does the")
        print("  cortex think L6's owned Mts are?")
        l6_mts = subject_microtheories(s, l6_mt)
        print(f"    subject_microtheories returned {len(list(l6_mts))} Mts")
        for mt in list(l6_mts)[:8]:
            print(f"    · {s.node(mt)['attrs'].get('name','?')}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()
    try:
        from domains.architecture_assessment import score_compositional_reuse
        print("  Direct call: score_compositional_reuse(s, l6_mt)")
        score, reason = score_compositional_reuse(s, l6_mt)
        print(f"    score: {score}/10")
        print(f"    reason: {reason}")
        print()
        print("  Direct call: score_compositional_reuse(s, fs_mt)")
        score2, reason2 = score_compositional_reuse(s, fs_mt)
        print(f"    score: {score2}/10")
        print(f"    reason: {reason2}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # What about the architecture_cortex's full ArchitectureCortex assessment?
    try:
        from domains.architecture_cortex import ArchitectureCortex
        cortex = ArchitectureCortex(s).install()
        if l6_mt:
            a = cortex.assess(l6_mt)
            print("  Full cortex assessment of L6:")
            for line in cortex.render_assessment(a).splitlines():
                if "compositional" in line.lower():
                    print(f"    {line.strip()}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    print("=" * 76)
    print("WHAT THE INQUIRIES SURFACED")
    print("=" * 76)
    print()
    print("  Inquiry 1: counts + examples of failure_modes / corrections /")
    print("    drives / principles concepts across all Mts. Mts that")
    print("    declare the COMPLETE set are visible. function_shape's")
    print("    transitive ancestors are tagged as having any of these or")
    print("    not. If the pattern is consistent, function_shape could")
    print("    LIFT from it; if it's inconsistent, filling them in is")
    print("    shape-guessing.")
    print()
    print("  Inquiry 2: direct edge check + direct cortex measure call.")
    print("    If function_shape -[genlMt]-> L6 exists AND L6's incoming")
    print("    edges include function_shape, the measure either returns")
    print("    the expected number or surfaces a discrepancy.")
    print("=" * 76)


if __name__ == "__main__":
    main()
