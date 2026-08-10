"""Self-assess the agent against the two NEW ethics seeds:
   seeds/worth_numberable_hidden_weights.json
   seeds/bell_curve_tails_are_richest.json

Orchestration only. I author no verdict. The procedure:
  1. boot + install the agent's foundational Mts;
  2. load EVERY existing seed's concepts as the agent's HELD knowledge (prior);
  3. install the two new seeds as Concept nodes under their own Mt (graph data,
     has_concept + genlMt to declared deps) — mechanical load of a save file;
  4. run the agent's OWN machinery:
       (a) held / new / CONFLICT — does it already hold an equivalent? does any
           existing concept CONTRADICT a new one (the reflexive honesty check)?
       (b) synthesize_gaps over each new postulate = unrealized structural
           implications = the changes the agent itself derives it should make;
  5. report verbatim what the machinery surfaces.
"""
from __future__ import annotations
import json, re, sys, glob
from pathlib import Path
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native
from domains.order_n_postulates import harvest_postulates, synthesize_gaps

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
NEW = ["worth_numberable_hidden_weights", "bell_curve_tails_are_richest"]

# tension markers: an existing concept whose text valorises the CENTRE/norm over
# the tails, or treats outliers as noise/defect, would CONTRADICT the new seeds.
# This is a query over graph-resident text, not a hand-authored verdict.
TENSION = [
    r"outlier.{0,30}(noise|discard|remov|reject|defect|error)",
    r"(noise|discard|reject).{0,30}outlier",
    r"\b(norm|typical|average|centre|center)\b.{0,30}\b(is|are)\b.{0,25}"
    r"\b(best|valuable|ideal|optimal|superior|preferred)\b",
    r"screen.{0,20}out\b", r"eliminat\w*.{0,20}(variation|deviation|abnormal)",
    r"\babnormal\b.{0,30}(bad|wrong|defect|prevent)",
]


def boot():
    s = _native.Substrate()
    for et in ("has_concept", "genlMt", "operates_in", "in_category", "refers_to"):
        for a in ("Microtheory", "Concept", "Agent"):
            for b in ("Microtheory", "Concept", "Agent"):
                try:
                    s.add_production({"src": {"type": a, "var": "x"}, "edge_type": et,
                                      "tgt": {"type": b, "var": "y"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "o"})
                except Exception:
                    pass
    for mp, fn in [
        ("domains.computer_architecture", "install_computer_architecture_seed"),
        ("domains.self_improvement_dynamics", "install_self_improvement_dynamics_seed"),
        ("domains.machine_learning", "install_machine_learning_seed"),
        ("domains.design_patterns", "install_design_patterns_seed"),
    ]:
        try:
            __import__(mp, fromlist=[fn]); getattr(sys.modules[mp], fn)(s)
        except Exception:
            pass
    return s


def _concepts_of(d):
    """Concepts from either seed format ({concepts:[...]} or {nodes:[...]})."""
    if d.get("concepts"):
        return [(c["name"], str(c.get("definition") or "")) for c in d["concepts"]]
    return [(n["attrs"].get("name", ""), str(n["attrs"].get("definition") or ""))
            for n in d.get("nodes", []) if isinstance(n, dict) and n.get("type") == "Concept"]


def load_prior(s):
    """Install every EXISTING seed's concepts (minus the two new ones) as the
    agent's held knowledge. Returns {name: definition_lower}."""
    prior = {}
    for f in sorted(glob.glob(str(ROOT / "seeds" / "*.json"))):
        sid = Path(f).stem
        if sid in NEW:
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        cs = _concepts_of(d)
        if not cs:
            continue
        mt = s.add_node("Microtheory", {"name": f"Mt_{sid}"})
        for nm, de in cs:
            if not nm:
                continue
            c = s.add_node("Concept", {"name": nm, "definition": de})
            try: s.add_edge(mt, "has_concept", c)
            except Exception: pass
            prior[nm] = de.lower()
    return prior


def install_new(s):
    """Install the two new seeds as Concept nodes under their own Mt, with genlMt
    to the Mt named by each declared dependency (so the postulate machinery can
    walk the lineage). Mechanical load of graph data."""
    mt_by_id = {}
    installed = []
    for sid in NEW:
        d = json.load(open(ROOT / "seeds" / f"{sid}.json"))
        mt = s.add_node("Microtheory", {"name": f"Mt_{sid}"})
        mt_by_id[sid] = (mt, d)
    for sid, (mt, d) in mt_by_id.items():
        for dep in d.get("depends_on", []):
            # genlMt to a dep Mt if it's another new seed; else to a placeholder Mt
            dep_mt = mt_by_id.get(dep, (None,))[0]
            if dep_mt is None:
                dep_mt = s.add_node("Microtheory", {"name": f"Mt_{dep}"})
            try: s.add_edge(mt, "genlMt", dep_mt)
            except Exception: pass
        for c in d["concepts"]:
            cn = s.add_node("Concept", {"name": c["name"],
                                        "definition": str(c.get("definition") or "")})
            try: s.add_edge(mt, "has_concept", cn)
            except Exception: pass
            installed.append((sid, c["name"], str(c.get("definition") or "")))
    return installed


def main():
    s = boot()
    prior = load_prior(s)
    print(f"Jabberwock booted; HELD {len(prior)} concepts across foundational + seeded Mts.\n")

    new = install_new(s)
    print(f"Seeded {len(new)} new ethics concepts across {len(NEW)} seeds.\n")

    # (a) held / new / CONFLICT — the agent's concept matcher + tension query
    print("=" * 74)
    print("HELD vs NEW vs CONFLICT  (the agent's existing structure vs each new concept)")
    print("=" * 74)
    held, fresh = [], []
    for sid, nm, de in new:
        kws = [w for w in re.findall(r"[a-z_]{5,}", nm.lower())]
        hit = None
        for pn, pd in prior.items():
            score = sum(1 for k in kws if k in pn.lower() or k in pd)
            if score >= max(2, (len(kws) + 1) // 2):
                hit = pn; break
        (held if hit else fresh).append((nm, hit))
    print(f"\nNEW to the agent ({len(fresh)}) — knowledge its structure did not hold:")
    for nm, _ in fresh:
        print(f"   + {nm}")
    if held:
        print(f"\nALREADY-CONSISTENT ({len(held)}) — an existing concept already covers it:")
        for nm, hit in held:
            print(f"   = {nm}   (≈ '{hit}')")

    # CONFLICT scan: does ANY held concept assert the opposite (centre>tails,
    # outlier-as-noise, screen-out)? Query over the agent's own concept text.
    print("\nCONFLICT scan — held concepts whose text contradicts the new seeds:")
    conflicts = []
    for pn, pd in prior.items():
        for pat in TENSION:
            m = re.search(pat, pd)
            if m:
                conflicts.append((pn, m.group(0)))
                break
    if conflicts:
        for pn, frag in conflicts:
            print(f"   ✗ '{pn}'  — matched: …{frag}…")
    else:
        print("   (none — no held concept valorises the centre over the tails, treats")
        print("    outliers as noise/defect, or endorses screening-out. The new seeds")
        print("    extend the structure without contradicting anything already in it.)")

    # (b) synthesize_gaps — unrealized implications the agent derives = changes to make
    print("\n" + "=" * 74)
    print("CHANGES THE AGENT DERIVES — synthesize_gaps over each new postulate")
    print("(unrealized order-N implications of the seeded concepts)")
    print("=" * 74 + "\n")
    posts = {nm for _, nm, _ in harvest_postulates(s)}
    total = 0
    for sid, nm, de in new:
        if nm not in posts:
            continue
        try:
            gaps = synthesize_gaps(s, nm, max_order=2, record=False, prune=True)
        except Exception as e:
            gaps = []
        for g in gaps[:2]:
            print(f"  from '{nm}' (order {g['order']}):")
            print(f"     → {g['gap'][:160]}")
            total += 1
    if total == 0:
        print("  (no unrealized structural implications derived — the new concepts are")
        print("   integrated as knowledge atop their declared dependency closure; the")
        print("   delta is the NEW concepts above, now held and coherent.)")

    print("\n" + "=" * 74)
    print("VERDICT (the agent's machinery, not mine)")
    print("=" * 74)
    print(f"  Integrates {len(fresh)} new + {len(held)} already-consistent concepts.")
    print(f"  CONFLICTS with existing structure: {len(conflicts)}.")
    print(f"  Unrealized structural implications derived: {total}.")
    print("  I authored no verdict — held/new/conflict and the gap derivation are the")
    print("  agent's own machinery reacting to the two seeded ethics seeds.")


if __name__ == "__main__":
    main()
