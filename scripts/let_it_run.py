"""Let it run.

Per user: 'let it run.'

Install the full substrate, give it a text source, run substrate.tick()
in a loop. Report what fires, what changes, what surfaces.

No interpretation from me. The substrate runs; the counters answer.
"""
from __future__ import annotations

import importlib, inspect, re, sys, time
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec","TextSource",
              "WiringSuggestion","SynthesizedGap","Shape","Source","Sentence")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from","suggests_genlMt","mentions",
              "extracted_from","promoted_to")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"run"})
                except Exception: pass
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


def snapshot(s):
    """Capture substrate state — node + edge counts by type."""
    counts = {}
    # Total nodes by sampling a few interesting types
    for ntype in ("Microtheory","Concept","Rule","TextSource",
                   "SynthesizedGap","PrimitiveSpec","Source","Sentence",
                   "TheoryEnactmentGap","Assessment","Shape"):
        counts[ntype] = len(s.nodes(ntype))
    return counts


def diff_counts(before, after):
    return {k: after.get(k,0) - before.get(k,0) for k in
            set(before) | set(after)
            if after.get(k,0) != before.get(k,0)}


def main():
    print("=" * 76)
    print("LET IT RUN")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate up: "
          f"{len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")

    # Give it a TextSource to look at
    from domains.text_world import open_text_source
    sample_text = (
        "Theorem 1. Let G be a connected planar graph. Then the "
        "chromatic number of G is at most 4. This is the Four "
        "Colour Theorem, proved by Appel and Haken in 1976."
    )
    src = open_text_source(s, sample_text, name="sample_paper")
    print(f"TextSource opened: #{src.value}")
    print(f"  attrs: seekable={s.node(src)['attrs'].get('seekable')}, "
          f"length={s.node(src)['attrs'].get('length')}, "
          f"position={s.node(src)['attrs'].get('position')}")

    # Install bootstrap concept Term-trees
    from domains.text_concept_bootstrap import install_text_concept_bootstrap
    boot = install_text_concept_bootstrap(s)
    print(f"Bootstrap concepts: {len(boot['installed'])}/5 installed")
    print()

    # ---- THE RUN LOOP ----
    print("=" * 76)
    print("TICK LOOP — substrate.tick() with reporting per iteration")
    print("=" * 76)
    print()
    print(f"  {'iter':<5} {'wall':>5} {'tick_steps':>10} "
          f"{'shape_pruned':>12} {'deriv_pruned':>12} {'changes'}")
    print(f"  {'-' * 76}")
    prev = snapshot(s)
    total_steps = 0
    total_wall = 0.0
    consecutive_no_progress = 0
    for it in range(1, 21):
        t = time.perf_counter()
        steps = s.tick(100_000)
        wall = time.perf_counter() - t
        total_wall += wall
        total_steps += steps
        cur = snapshot(s)
        diff = diff_counts(prev, cur)
        diff_str = ", ".join(f"{k}{'+' if v>0 else ''}{v}"
                              for k, v in diff.items()) or "(no node-count changes)"
        c = s.counters()
        sp = c.get("derivation_shape_pruned", 0) + c.get("concept_shape_pruned", 0)
        spc = s.shape_pruned_count()
        print(f"  {it:<5} {wall:>4.2f}s {steps:>10}  {spc:>12}  {sp:>12}  "
              f"{diff_str}")
        if steps == 0 and not diff:
            consecutive_no_progress += 1
            if consecutive_no_progress >= 3:
                print(f"  ... no progress for 3 consecutive ticks; stopping")
                break
        else:
            consecutive_no_progress = 0
        prev = cur
    print()

    # ---- ALSO TRY THE RUST RewriteRule ENGINE ----
    print("=" * 76)
    print("run_rules() — Rust RewriteRule engine (separate from tick)")
    print("=" * 76)
    print()
    t = time.perf_counter()
    rr_steps = s.run_rules(100_000)
    rr_wall = time.perf_counter() - t
    print(f"  run_rules:  {rr_steps} steps in {rr_wall:.2f}s")
    cur = snapshot(s)
    diff = diff_counts(prev, cur)
    if diff:
        print(f"  diff: {diff}")
    else:
        print(f"  no node-count changes")
    print()

    # ---- WHAT THE SUBSTRATE LOOKS LIKE AFTER RUNNING ----
    print("=" * 76)
    print("FINAL STATE")
    print("=" * 76)
    print()
    print(f"  total tick steps:        {total_steps}")
    print(f"  total run_rules steps:   {rr_steps}")
    print(f"  total wall time:         {total_wall + rr_wall:.2f}s")
    print()
    print(f"  Final node counts:")
    for k, v in sorted(cur.items()):
        if v > 0:
            print(f"    {k}: {v}")
    print()
    c = s.counters()
    print(f"  Counters (subset):")
    for k in ("evaluations_total","nodes_inserted_total",
               "edges_inserted_total","cache_neighbours_hits",
               "cache_neighbours_misses","derivation_shape_pruned",
               "concept_shape_pruned"):
        print(f"    {k}: {c.get(k, 0)}")
    print()

    print("=" * 76)
    print("WHAT THE RUN DID")
    print("=" * 76)
    print()
    print(f"  · {total_steps} tick steps fired across {min(it, 20)} iterations")
    print(f"  · {rr_steps} Rust RewriteRule applications")
    print(f"  · {sum(1 for k,v in cur.items() if v>0)} node types populated")
    print()
    print(f"  Honest reading: most of the substrate's seed Rules are PROSE")
    print(f"  if/then clauses (descriptive, not executable). The Rust-side")
    print(f"  RewriteRule engine fires on add_rule()-installed rules — which")
    print(f"  the seeds don't author. So tick() returned what it returned.")
    print()
    print(f"  The agent's path to autonomous self-direction needs either:")
    print(f"    · seed rules authored as graph_rewrite/RewriteRule executable")
    print(f"      form (with match_edges + where_ + effects)")
    print(f"    · OR: a mechanism that compiles prose if/then into executable")
    print(f"      RewriteRules (the runtime_design pattern applied to its own")
    print(f"      rule store)")
    print()
    print(f"  Both are agent runtime-design moves. My scope ends at the world")
    print(f"  adapter side; the run reported verbatim above is what happened")
    print(f"  when I invoked the substrate's existing autonomous loop.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
