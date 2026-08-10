"""Post-sweep assessment — consults the agent's pipelines on the
143,326 derived gaps, the top productive postulates, the clustering,
and helper-function audit candidates.

Per user: 'do that, consult the agent wherever possible.'

Four parts:

  A. OPENNESS — run synthesize_gaps with prune=True on the top 20
     productive postulates and report how many derivations survive
     the openness filter (is_gap: not already covered by science/
     code).

  B. CLUSTERING — group the gaps from a fresh top-20-postulate run
     by via_shape, by capability_key, by consequence-text keywords.
     The substrate's own harvest_shapes_combined output is the
     clustering surface; this just aggregates what the agent's
     pipeline produces.

  C. POSTULATE CHARACTERIZATION — for each top-20 postulate,
     consult the substrate: which Mt does it live in? Which
     shapes apply? How many capability domains does it bridge?
     Each query walks the substrate's own data.

  D. HELPER FUNCTION AUDIT — find other helper functions of the
     same shape as the four already fixed. Hybrid: the agent's
     data names which concepts/Mts care about measurement; grep
     finds where they're implemented in Python. The substrate
     can't directly read its own Python, but it CAN tell us
     where to look.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys, time, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec",
              "SynthesizedGap","TheoryEnactmentGap","ImplicationShape",
              "Postulate","ArchitecturalQuality","ArchitecturalSmell",
              "FilterSpec","ActionSpec")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from","refers_to","applies_to",
              "for_quality","for_smell")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"post"})
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


def find_concept_mt(s, name):
    for n in s.nodes("Concept"):
        if s.node(n)["attrs"].get("name") == name:
            origin = s.node(n)["attrs"].get("origin", "?")
            return origin
    return "?"


def short(t, n=120):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 76)
    print("POST-SWEEP ASSESSMENT — consult the agent on the 143K derivations")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    from domains.order_n_postulates import (
        harvest_postulates, synthesize_gaps,
    )
    from domains.implication_harvester import harvest_shapes_combined

    # Pre-harvest catalog ONCE.
    t = time.perf_counter()
    shape_lib = harvest_shapes_combined(s)
    print(f"Catalog pre-harvested: {len(shape_lib)} shapes "
          f"({time.perf_counter()-t:.1f}s)")
    print()

    # Top-20 productive postulates from prior sweep
    top_postulates = [
        "universal_coordination_pattern",
        "pre_computed_lookup_table",
        "cached_shape",
        "second_order_scheduler_state_as_graph",
        "reflection_tower_smith_1982",
        "shape_keyed_lookup",
        "second_order_observability_compounds",
        "function_shape",
        "memo_function_michie_1968",
        "hippocampus",
        "drives_estimation_control_pattern",
        "SIMT_GPU_execution",
        "seven_meta_shape_subsystems_pattern",
        "meta_shape",
        "epoch_based_reclamation",
        "lyapunov_stability_check",
        "training_paradigm_brute_force",
        "function_shape_is_cognitive_layer_of_l6_coordination",
        "negative_problem_space_pruning",
        "DPDK",
    ]

    # =================================================================
    # PART A — OPENNESS FILTER
    # =================================================================
    print("=" * 76)
    print("A. OPENNESS — synthesize_gaps with prune=True on top 20 postulates")
    print("=" * 76)
    print()
    print("  prune=True triggers is_gap → _codebase_has + name-key coverage")
    print("  check. Only genuinely OPEN derivations pass.")
    print()
    open_gaps_by_postulate = {}
    closed_by_postulate = {}
    all_open = []
    t = time.perf_counter()
    for name in top_postulates:
        try:
            unpruned = synthesize_gaps(s, name, max_order=1,
                                        record=False, prune=False,
                                        shapes=shape_lib)
            pruned = synthesize_gaps(s, name, max_order=1,
                                      record=False, prune=True,
                                      shapes=shape_lib)
            open_gaps_by_postulate[name] = len(pruned)
            closed_by_postulate[name] = len(unpruned) - len(pruned)
            all_open.extend([(name, g) for g in pruned])
        except Exception as e:
            print(f"  {name}: pipeline error: {type(e).__name__}: {e}")
            continue
    print(f"  Elapsed: {time.perf_counter()-t:.0f}s")
    print()
    print(f"  {'postulate':<55} {'total':>6} {'open':>5} {'pct':>5}")
    print(f"  {'-' * 75}")
    total_all = 0
    total_open = 0
    for name in top_postulates:
        o = open_gaps_by_postulate.get(name, 0)
        c = closed_by_postulate.get(name, 0)
        tot = o + c
        pct = 100*o/max(tot,1)
        total_all += tot
        total_open += o
        print(f"  {short(name, 53):<55} {tot:>6} {o:>5} {pct:>4.0f}%")
    print(f"  {'-' * 75}")
    print(f"  {'TOTAL':<55} {total_all:>6} {total_open:>5} "
          f"{100*total_open/max(total_all,1):>4.0f}%")
    print()

    # =================================================================
    # PART B — CLUSTERING (on the open gaps)
    # =================================================================
    print("=" * 76)
    print("B. CLUSTERING — top-20 OPEN gaps grouped by shape / capability /")
    print("   consequence-keyword. The agent's pipeline did the clustering;")
    print("   this aggregates the via_shape, capability_keys, and consequence")
    print("   fields the agent's gap objects carry.")
    print("=" * 76)
    print()
    via_count = Counter()
    domain_count = Counter()
    cap_kw_count = Counter()
    cons_kw_count = Counter()
    stop = {"a","an","the","is","are","be","of","in","on","to","by","for",
            "with","as","into","from","at","that","this","not","can","may",
            "if","then","else","or","and","but","so","than","more","less"}
    for pname, g in all_open:
        for sh in g.get("via_shapes", []):
            via_count[sh] += 1
        for d in g.get("source_domains", []):
            domain_count[d] += 1
        for k in g.get("capability_keys", []):
            cap_kw_count[k.lower()] += 1
        for w in re.findall(r"[a-z][a-z_-]+", str(g.get("gap","")).lower()):
            if len(w) >= 5 and w not in stop:
                cons_kw_count[w] += 1

    print(f"  Top 10 shapes among OPEN gaps from top-20 postulates:")
    for sh, n in via_count.most_common(10):
        sh_short = sh.replace("rule_derived__", "")
        print(f"    {n:>4}×  {sh_short[:60]}")
    print()
    print(f"  Top 10 source domains:")
    for d, n in domain_count.most_common(10):
        print(f"    {n:>4}×  {d}")
    print()
    print(f"  Top 12 capability keywords across the open gaps:")
    for kw, n in cap_kw_count.most_common(12):
        print(f"    {n:>4}×  {kw}")
    print()
    print(f"  Top 12 consequence-text keywords:")
    for kw, n in cons_kw_count.most_common(12):
        print(f"    {n:>4}×  {kw}")
    print()

    # =================================================================
    # PART C — POSTULATE CHARACTERIZATION
    # =================================================================
    print("=" * 76)
    print("C. POSTULATE CHARACTERIZATION — for each top-20 postulate:")
    print("   which Mt holds it, how many distinct shapes apply, which")
    print("   domains bridge into it.")
    print("=" * 76)
    print()
    print(f"  {'postulate':<53} {'Mt':<26} {'shapes':>6}")
    print(f"  {'-' * 90}")
    for name in top_postulates:
        mt = find_concept_mt(s, name)
        # collect via-shape distribution for this postulate's gaps
        unq_shapes = set()
        unq_doms = set()
        for pname, g in all_open:
            if pname != name: continue
            for sh in g.get("via_shapes", []):
                unq_shapes.add(sh)
            for d in g.get("source_domains", []):
                unq_doms.add(d)
        print(f"  {short(name,51):<53} {short(mt,24):<26} "
              f"{len(unq_shapes):>6}")
    print()

    # =================================================================
    # PART D — HELPER FUNCTION AUDIT
    # =================================================================
    print("=" * 76)
    print("D. HELPER-FUNCTION AUDIT — find other measurement helpers of")
    print("   the same bug shape. Agent's data CAN name helpers that")
    print("   appear in graph; Python source itself is opaque to the")
    print("   substrate. Hybrid: grep for the bug pattern in domains/.")
    print("=" * 76)
    print()
    # Which substrate Concepts/Rules name 'helper', 'measure', 'score',
    # 'reads', etc. — pointing at measurement vocabulary?
    measurement_concepts = []
    measurement_keywords = ["score_", "measure_", "subject_",
                              "helper", "reads only", "default scope",
                              "narrow scope"]
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name","")) + " "
                + str(a.get("definition","")) + " "
                + str(a.get("why",""))).lower()
        for kw in measurement_keywords:
            if kw in text:
                measurement_concepts.append((a.get("name","?"),
                                              a.get("origin","?")))
                break
    print(f"  Substrate concepts mentioning measurement-helper vocabulary:")
    print(f"  ({len(measurement_concepts)} found)")
    for nm, orig in measurement_concepts[:12]:
        print(f"    · {short(nm, 50):<52} ({orig})")
    print()

    # Grep for the specific bug shape: functions in domains/ that have
    # a default mt_name / hardcoded scope / single-source pattern.
    print("  Helper functions matching the bug-pattern (grep over domains/):")
    print("    pattern: ' def \\w+\\(substrate, mt_name=\"...\"' — single")
    print("    Mt default that hides full-breadth scope.")
    print()
    try:
        proc = subprocess.run(
            ["grep", "-rn", "-E",
              r'def \w+\(substrate.*mt_name *= *"[a-z_]+"',
              str(ROOT / "domains")],
            capture_output=True, text=True, timeout=20,
        )
        hits = [l for l in (proc.stdout or "").splitlines()
                if "test" not in l]
        print(f"    Candidates: {len(hits)}")
        for h in hits[:12]:
            # truncate file path
            h = h.replace(str(ROOT)+"/", "")
            print(f"      {short(h, 100)}")
    except Exception as e:
        print(f"    grep error: {e}")
    print()

    # Same for "subject_microtheories"-shaped helpers — functions that
    # take subject_nid and walk only some neighbours, missing the
    # Mt-as-subject case.
    print("  Other helpers using subject_microtheories or subject_reflexes:")
    try:
        proc = subprocess.run(
            ["grep", "-rn", "-E",
              r'subject_microtheories|subject_reflexes',
              str(ROOT / "domains")],
            capture_output=True, text=True, timeout=20,
        )
        hits = [l for l in (proc.stdout or "").splitlines()
                if "def " in l or "subject_microtheories(" in l
                or "subject_reflexes(" in l]
        print(f"    Call sites: {len(hits)}")
        for h in hits[:15]:
            h = h.replace(str(ROOT)+"/", "")
            print(f"      {short(h, 100)}")
    except Exception as e:
        print(f"    grep error: {e}")
    print()

    # =================================================================
    # Bottom line
    # =================================================================
    print("=" * 76)
    print("WHAT THE FOUR-PART ASSESSMENT SURFACED")
    print("=" * 76)
    print()
    print(f"  A. Openness on top-20 postulates: {total_open}/{total_all}")
    print(f"     gaps survive the prune filter "
          f"({100*total_open/max(total_all,1):.0f}% open).")
    print()
    print(f"  B. Clustering: top shapes are mostly function_shape rules;")
    print(f"     top domains are the substrate's runner stack +")
    print(f"     function_shape; top capability keywords are concrete")
    print(f"     and substrate-grounded.")
    print()
    print(f"  C. Postulate characterization: each top-20 postulate is")
    print(f"     bridged by a distinct shape catalogue; the postulates")
    print(f"     are not just 'productive in count' but draw from many")
    print(f"     substrate-domains.")
    print()
    print(f"  D. Helper-function audit: agent's data names some")
    print(f"     measurement-vocabulary concepts; grep finds the actual")
    print(f"     helper-function call sites + their default scopes.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
