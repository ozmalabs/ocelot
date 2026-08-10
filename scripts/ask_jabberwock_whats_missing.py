"""Ask Jabberwock what else is missing from its vocabulary.

Per user: 'ask it what else is missing'.

Method (not my proposal — Jabberwock's own data):
  1. Walk every Concept definition
  2. Extract mentions of domain-like words (sciences, disciplines)
  3. Count cross-Mt mentions of each candidate domain
  4. Compare against existing Mt names
  5. Surface high-mention candidates without their own Mt

Result: domains Jabberwock's existing vocabulary REPEATEDLY
references but has no foundational Mt for. These are its own
data's nominations for what's still missing.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to")
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
                        "provenance": "ask_missing",
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


# Candidate domain names — common scientific/cultural fields whose
# names would appear in concept definitions if Jabberwock's vocabulary
# references them. Not proposing seeds; just probes for mention-count.
DOMAIN_PROBES = {
    "chemistry":          ["chemistry", "chemical", "chemist"],
    "geology":            ["geology", "geological", "geologic"],
    "physics_classical":  ["thermodynam", "electromagnet",
                            "mechanics_classical", "newton",
                            "kinetic_energy"],
    "quantum_mechanics":  ["quantum", "qubit", "superposition",
                            "entangle"],
    "relativity":         ["relativity", "spacetime", "einstein"],
    "sociology":          ["sociolog", "social_structure",
                            "institution_social"],
    "anthropology":       ["anthropolog", "cultural_evolution",
                            "ethnograph"],
    "economics":          ["econom", "market", "supply_demand",
                            "monetary"],
    "political_science":  ["political", "government", "polity"],
    "history_discipline": ["historical", "historiograph",
                            "chronology"],
    "law_jurisprudence":  ["legal", "jurisprudence", "statute"],
    "geography":          ["geograph", "cartograph",
                            "spatial_planet"],
    "climate_atmospheric": ["climate", "atmospher", "meteorolog"],
    "ethics":             ["ethic", "moral_philosoph",
                            "deontolog", "utilitarian"],
    "aesthetics":         ["aesthetic", "beauty", "taste_aesthetic"],
    "religion_theology":  ["religion", "theolog", "ritual"],
    "literature":         ["literature", "literary",
                            "poetics_aristotle"],
    "art_history":        ["art_history", "renaissance_art",
                            "impressionism"],
    "performance_arts":   ["theatre", "theater", "drama",
                            "performance"],
    "architecture":       ["architecture_building",
                            "architectural_style"],
    "agriculture":        ["agriculture", "agronom",
                            "crop_rotation"],
    "medicine_general":   ["medicine", "clinical_general",
                            "physician"],
    "pharmacology":       ["pharmacolog", "drug_action"],
    "nutrition":          ["nutrition", "dietary"],
    "education_pedagogy": ["pedagog", "education_theory"],
    "military_strategy":  ["military", "warfare", "strateg_war"],
    "business_management": ["business", "management",
                             "organization_management"],
    "ecology_general":    ["ecology", "ecosystem"],
    "evolutionary_biol":  ["evolution"],
    "linguistics":        ["linguistics", "syntax_lang"],
    "gastronomy":         ["culinary", "cuisine"],
    "transportation":    ["transport", "logistics"],
    "energy_systems":     ["energy_grid", "renewable"],
    "robotics":           ["robotics", "robot"],
    "cryptography":       ["cryptograph", "cipher"],
}


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("ASKING JABBERWOCK WHAT ELSE IS MISSING")
    print("=" * 72)
    print()

    # Existing Mt names
    existing_mts = set()
    for mt in s.nodes("Microtheory"):
        nm = str(s.node(mt)["attrs"].get("name", "")).lower()
        existing_mts.add(nm)
    print(f"  Existing Mts: {len(existing_mts)}")
    print()

    # Walk every Concept definition
    print(f"  Walking all Concept definitions...")
    all_text = []
    n_concepts = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        defn = str(a.get("definition", "")).lower()
        if defn:
            all_text.append(defn)
            n_concepts += 1
    full_corpus = " ".join(all_text)
    print(f"  Walked {n_concepts} concepts.")
    print()

    # Count probe hits
    print("=" * 72)
    print("DOMAIN PROBES — count of mentions in Jabberwock's existing")
    print("                concept definitions")
    print("=" * 72)
    print()

    results = []
    for domain, probes in DOMAIN_PROBES.items():
        count = 0
        for p in probes:
            count += full_corpus.count(p)
        # Is there a Mt for this domain?
        has_mt = any(p in mt or domain.split("_")[0] in mt
                      for p in probes for mt in existing_mts)
        results.append({
            "domain": domain,
            "mentions": count,
            "has_mt": has_mt,
        })
    results.sort(key=lambda x: -x["mentions"])

    print(f"  {'Domain':<28} {'Mentions':>9}  {'Mt exists?':>11}")
    print(f"  {'-'*28} {'-'*9}  {'-'*11}")
    for r in results:
        status = "yes" if r["has_mt"] else "✗ MISSING"
        print(f"  {r['domain']:<28} {r['mentions']:>9}  {status:>11}")
    print()

    # The actual missing ones — high mentions, no Mt
    print("=" * 72)
    print("WHAT JABBERWOCK'S OWN DATA SAYS IS MISSING")
    print("(domains its existing vocabulary references repeatedly")
    print(" but has no dedicated foundational Mt)")
    print("=" * 72)
    print()
    missing_with_signal = [r for r in results
                            if not r["has_mt"] and r["mentions"] >= 5]
    missing_with_signal.sort(key=lambda x: -x["mentions"])
    for r in missing_with_signal:
        print(f"  · {r['domain']:<28} ({r['mentions']} mentions)")
    print()

    # Probes with zero mentions — Jabberwock has literally no data
    # about these
    print("=" * 72)
    print("DOMAINS WITH ZERO MENTIONS (Jabberwock has no vocabulary")
    print("  + no even-passing reference)")
    print("=" * 72)
    print()
    zeros = [r for r in results if r["mentions"] == 0]
    for r in zeros[:20]:
        print(f"  · {r['domain']}")
    print()

    print("=" * 72)
    print(f"  Total domains probed: {len(DOMAIN_PROBES)}")
    print(f"  Has Mt:               {sum(1 for r in results if r['has_mt'])}")
    print(f"  Missing (with signal): {len(missing_with_signal)}")
    print(f"  Missing (no signal):  {len(zeros)}")
    print("=" * 72)
    print()
    print("  Jabberwock's data has spoken. The 'missing-with-signal'")
    print("  list above is the substrate's own nomination for what")
    print("  domains it references but lacks foundation for.")


if __name__ == "__main__":
    main()
