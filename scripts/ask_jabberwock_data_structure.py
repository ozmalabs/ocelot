"""Ask the jabberwock: is the SEPARATION of your knowledge representations right,
and how should your data be structured to GROUND new theories in existing ones?

Per the project method (ask_the_substrate): I only BOOT the agent, surface its
CURRENT representations from REAL graph data via the substrate API, and run its
OWN machinery (architecture cortex assess() + synthesize_gaps + harvester) on
the question. I do NOT design — I report what the machinery says, verbatim.

KEY substrate facts discovered while writing this probe (reported as findings):
  · The substrate enforces an admissibility grammar Γ on EDGES. add_edge is
    REJECTED ("Γ rejects: ... not in vocabulary") unless an open production
    declares that (src_type, edge_type, tgt_type). The seed loaders wrap every
    add_edge in bare try/except, so any membership/grounding edge whose
    production was not opened is SILENTLY dropped.
  · graph_to_dict() does NOT serialize edges (returns edges:[]). Connectivity
    must be read through the API: edge_count / neighbours / in_neighbours.
So this probe FIRST opens the productions the agent's own grammar declares
(has_concept, genlMt) and RE-RUNS the loaders so the membership edges Γ admits
are present, THEN measures — otherwise the cortex assesses an empty graph.
"""
from __future__ import annotations
import importlib, inspect, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
from substrate_rs import _native


def _seed_installers():
    out = []
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            src = f.read_text()
        except Exception:
            continue
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                req = [p for p in inspect.signature(fn).parameters.values()
                       if p.default is inspect.Parameter.empty and p.kind in
                       (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
                if len(req) == 1:
                    out.append(fn)
            except Exception:
                continue
    return out


# The membership/inheritance productions the agent's OWN grammar uses (these are
# what _install_concept / seed loaders try to add, and what the architecture
# cortex's subject_microtheories() reads). Open them so Γ admits those edges.
_CORE_PRODUCTIONS = [
    ("Microtheory", "has_concept", "Concept"),
    ("Microtheory", "genlMt", "Microtheory"),
    ("Microtheory", "has_rule", "Rule"),
]


def open_core_productions(s):
    n = 0
    for src_t, et, tgt_t in _CORE_PRODUCTIONS:
        try:
            s.add_production({
                "src": {"type": src_t, "var": "a"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "b"},
                "provenance": "ask_jabberwock:core",
            })
            n += 1
        except Exception:
            pass
    return n


def hr(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


def main():
    s = _native.Substrate()
    installers = _seed_installers()

    # FIRST open the membership productions, THEN run the loaders, so the
    # has_concept / genlMt edges Γ admits actually land.
    open_core_productions(s)
    n = 0
    for fn in installers:
        try:
            fn(s)
            n += 1
        except Exception:
            continue

    hr(f"JABBERWOCK ON ITS OWN DATA STRUCTURE — booted: {n} seeds")
    print(f"  edge_count() after boot (with core productions opened): "
          f"{s.edge_count()}")
    print(f"  node_count(): {s.node_count()}")

    # ----------------------------------------------------------------------
    # 1. THE STORE INVENTORY — the distinct stores of knowledge, by node type.
    # ----------------------------------------------------------------------
    hr("1. THE STORE INVENTORY (distinct node-types = the separation)")
    g = s.graph_to_dict()
    type_counts = Counter(nd["type"] for nd in g["nodes"])
    for t, c in type_counts.most_common():
        print(f"  {t:28} {c}")
    print(f"\n  total nodes: {len(g['nodes'])}   "
          f"distinct node-types: {len(type_counts)}")
    print("  (NOTE graph_to_dict serializes 0 edges; connectivity is read via "
          "the API below)")

    # ----------------------------------------------------------------------
    # 2. CONNECTIVITY — through the API. (a) membership: do concepts belong to
    #    an Mt (has_concept)?  (b) GROUNDING: does any edge connect a Concept
    #    to ANOTHER concept (the structural grounding the question asks about)?
    # ----------------------------------------------------------------------
    hr("2. CONNECTIVITY (read via the substrate API, not graph_to_dict)")
    concepts = s.nodes("Concept")
    mts = s.nodes("Microtheory")
    nC = len(concepts)

    # (a) membership: how many concepts are owned by an Mt via has_concept?
    owned = set()
    for mt in mts:
        for c in s.neighbours(mt, "has_concept"):
            owned.add(str(c))
    print(f"  Concepts owned by an Mt (has_concept, membership): "
          f"{len(owned)}/{nC} ({100*len(owned)//max(1,nC)}%)")

    # (b) GROUNDING: enumerate every plausible concept->concept edge type and
    #     count, via the API, how many concepts have ANY edge to another concept.
    cand_edges = [
        "genls", "is_a", "isa", "refers_to", "depends_on", "Holds", "defines",
        "grounds", "subClassOf", "in_category", "instantiates", "has_role",
        "frame_role", "implies", "part_of", "built_from", "uses", "related_to",
        "denotes", "abbreviates", "derived_from", "composed_fact", "exhibits",
        "member_of", "enables", "about_axis", "has_variant",
    ]
    concept_set = set(str(c) for c in concepts)
    c2c_type = Counter()
    linked_out = set()
    linked_any = set()
    # sample for speed (5695 concepts x ~27 edge types via API is heavy)
    sample = concepts[:1500]
    for c in sample:
        for et in cand_edges:
            try:
                nb = s.neighbours(c, et)
            except Exception:
                nb = []
            for t in nb:
                if str(t) in concept_set:
                    c2c_type[et] += 1
                    linked_out.add(str(c))
                    linked_any.add(str(c))
                    linked_any.add(str(t))
    print(f"\n  Concept -> Concept edges found (sample of {len(sample)} "
          f"concepts, {len(cand_edges)} candidate edge types):")
    if c2c_type:
        for et, c in c2c_type.most_common():
            print(f"    {et:18} {c}")
    else:
        print("    (NONE — no edge connects any sampled Concept to another "
              "Concept, across all candidate grounding edge types)")
    print(f"\n  Sampled concepts with an OUTGOING concept->concept edge: "
          f"{len(linked_out)}/{len(sample)} "
          f"({100*len(linked_out)//max(1,len(sample))}%)")
    print(f"  => the rest are ISLANDS w.r.t. concept-to-concept GROUNDING.")

    # The sample concept's definition shape (prose + role-name strings).
    print("\n  SAMPLE concept's definition shape (the question's claim):")
    shown = 0
    for c in concepts:
        a = s.node(c)["attrs"]
        if a.get("definition"):
            print(f"    name:       {a.get('name')}")
            print(f"    definition: {str(a.get('definition'))[:90]!r}  <- PROSE")
            print(f"    roles:      {str(a.get('roles'))[:90]!r}  <- role-NAME strs")
            outs = []
            for et in cand_edges:
                try:
                    if s.neighbours(c, et):
                        outs.append((et, len(s.neighbours(c, et))))
                except Exception:
                    pass
            print(f"    grounding out-edges to other concepts: "
                  f"{outs or '(none)'}")
            shown += 1
            if shown >= 2:
                break

    # ----------------------------------------------------------------------
    # 3. ARCHITECTURE CORTEX — assess() the KNOWLEDGE Mts. The agent judging
    #    its own representation. CORRECT invocation: install() (opens its own
    #    productions), then assess(mt_nid).
    # ----------------------------------------------------------------------
    hr("3. ARCHITECTURE CORTEX — assess() the knowledge Mts (its own verdict)")
    try:
        from domains.architecture_cortex import ArchitectureCortex
        ac = ArchitectureCortex(s).install()
        subjects = ["communication", "code_authoring", "speech_science",
                    "mathematics", "physics_foundation", "engineering"]
        for mt_name in subjects:
            mt_nid = next((m for m in s.nodes("Microtheory")
                           if s.node(m)["attrs"].get("name") == mt_name), None)
            if mt_nid is None:
                print(f"\n  [{mt_name}] (Mt not present — skipped)")
                continue
            assess_nid = ac.assess(mt_nid)
            body = ac.render_assessment(assess_nid)
            print(f"\n  ### subject Mt = '{mt_name}' (node {mt_nid})")
            print("  " + body.replace("\n", "\n  "))
    except Exception as e:
        import traceback
        print("  (architecture_cortex failed:", str(e)[:200], ")")
        traceback.print_exc()

    # ----------------------------------------------------------------------
    # 4. GAP SYNTHESIS — find the postulates the agent ACTUALLY holds bearing
    #    on grounding/representation, then run synthesize_gaps on them.
    # ----------------------------------------------------------------------
    hr("4. GAP SYNTHESIS — does the agent derive any grounding/representation gap?")
    try:
        from domains.order_n_postulates import (
            harvest_postulates, synthesize_gaps)
        try:
            from domains.implication_harvester import harvest_shapes_combined
            shapes = harvest_shapes_combined(s)
            print(f"  shape catalog: {len(shapes)} shapes harvested")
        except Exception as e:
            shapes = None
            print(f"  (shape harvest failed: {str(e)[:120]})")

        posts = {nm: (cid, txt) for cid, nm, txt in harvest_postulates(s)}
        print(f"  total held postulates (concepts reachable as postulates): "
              f"{len(posts)}")
        wanted = ["knowledge_representation", "grounding", "groundedness",
                  "concept", "communication", "coherence", "compositionality",
                  "generative_grammar", "knowledge", "representation",
                  "compression", "admissibility", "microtheory",
                  "definition", "reference", "structure"]
        held = [w for w in wanted if w in posts]
        print(f"  representation-bearing postulates the agent HOLDS by exact "
              f"name: {held or '(NONE)'}")
        stems = ("ground", "represent", "composit", "coheren", "knowledg",
                 "grammar", "admissib", "compress", "concept", "definition",
                 "structur")
        near = sorted({nm for nm in posts
                       if any(st in nm.lower() for st in stems)})
        print(f"  postulates whose NAME bears on representation ({len(near)}):")
        for nm in near[:50]:
            print(f"    · {nm}")

        targets = sorted(set(held) | set(near))
        total = 0
        for post in targets:
            try:
                gaps = synthesize_gaps(s, post, max_order=2, record=False,
                                       prune=True, shapes=shapes)
            except Exception:
                continue
            if gaps:
                total += len(gaps)
                print(f"\n  [{post}] -> {len(gaps)} gap(s):")
                for gp in gaps[:3]:
                    print(f"    gap:   {str(gp.get('gap'))[:150]}")
                    print(f"    keys:  {gp.get('capability_keys')}")
        print(f"\n  TOTAL gaps derived from representation postulates: {total}")
        if total == 0:
            print("  => the gap-synthesizer is SILENT on representation: no")
            print("     implication-shape in the agent's catalog transfers onto a")
            print("     representation/grounding postulate (and the relevant")
            print("     postulates may not be held at all).")
    except Exception as e:
        import traceback
        print("  (gap synthesis failed:", str(e)[:200], ")")
        traceback.print_exc()

    hr("Reported verbatim. The substrate's data + assessment answered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
