"""iter-5 driver — run the agent's autopoietic PICK on the SCALED gap-set.

Earlier speech-loop iterations (2/3/4) ran the ranker on a gap set
synthesized ONLY over speech_science postulates (the old narrow default),
so the only OPEN axes the ranker ever saw were speech gaps (clustering
payoff 6, word-scale chunking payoff 4). This driver runs the SAME agent
pipeline on the SCALED machinery: synthesize OPEN gaps (prune=True,
record=True) across a BROAD postulate set, build the CapabilityAxis env,
and run the agent's own graph-resident ranker (gap_prioritiser.rank_gaps /
pick_frontier) over it.

Question: does the richer machinery surface a better/different/cross-domain
frontier than the speech picks, and how many distinct capability axes
survive the openness selector?

No synthesis from me: synthesize_gaps + the ranking Term are the agent's;
this script only installs seeds, runs the pipeline, and prints what the
agent's Argmax returns. All numbers are live.
"""
from __future__ import annotations

import importlib, inspect, re, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "PrimitiveSpec",
             "SynthesizedGap", "TheoryEnactmentGap", "ImplicationShape",
             "Postulate", "ArchitecturalQuality", "ArchitecturalSmell",
             "FilterSpec", "ActionSpec", "CapabilityAxis", "FrontierRoot",
             "FrontierChoice")
    edges = ("has_concept", "has_rule", "genlMt", "owns_microtheory",
             "implies", "derives_from", "refers_to", "applies_to",
             "for_quality", "for_smell", "unifies", "self")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src": {"type": t, "var": "a"},
                                      "edge_type": et, "tgt": {"type": u, "var": "b"},
                                      "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "iter5"})
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


def short(t, n=110):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    n_postulates = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    print("=" * 76)
    print("ITER-5 — agent PICK on the SCALED gap-set (broad postulate synthesis)")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    from domains.order_n_postulates import harvest_postulates, synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    from domains import gap_prioritiser as gp

    t = time.perf_counter()
    shape_lib = harvest_shapes_combined(s)
    print(f"Shape catalog: {len(shape_lib)} shapes ({time.perf_counter()-t:.1f}s)")

    posts = harvest_postulates(s, mt_name=None)
    print(f"Postulates available: {len(posts)}")
    print()

    # The agent's loop synthesizes OPEN gaps (prune=True) and RECORDS them
    # (record=True) so the ranker's axis env can group them. To stay tractable
    # but representative, synthesize over the broadest deterministic slice we
    # can afford: the most-productive postulates from the sweep plus an evenly-
    # strided sample across the whole postulate list. This is a SAMPLE of the
    # full 5282-postulate space, reported honestly as such.
    top_productive = [
        "universal_coordination_pattern", "pre_computed_lookup_table",
        "cached_shape", "second_order_scheduler_state_as_graph",
        "reflection_tower_smith_1982", "shape_keyed_lookup",
        "second_order_observability_compounds", "function_shape",
        "memo_function_michie_1968", "hippocampus",
        "drives_estimation_control_pattern", "SIMT_GPU_execution",
        "seven_meta_shape_subsystems_pattern", "meta_shape",
        "epoch_based_reclamation", "lyapunov_stability_check",
        "training_paradigm_brute_force",
        "function_shape_is_cognitive_layer_of_l6_coordination",
        "negative_problem_space_pruning", "DPDK",
    ]
    by_name = {nm: (cid, txt) for cid, nm, txt in posts}
    # evenly-strided broad sample
    stride = max(1, len(posts) // max(1, (n_postulates - len(top_productive))))
    sample_names = []
    for i in range(0, len(posts), stride):
        sample_names.append(posts[i][1])
    chosen = list(dict.fromkeys(top_productive + sample_names))
    chosen = [c for c in chosen if c in by_name][:n_postulates]
    print(f"Synthesizing OPEN gaps (prune=True, record=True) over "
          f"{len(chosen)} postulates")
    print(f"  ({len(top_productive)} top-productive + strided broad sample)")
    print()

    t = time.perf_counter()
    total_open = 0
    open_postulates = 0
    per_post = Counter()
    for i, nm in enumerate(chosen):
        try:
            gaps = synthesize_gaps(s, nm, max_order=1, record=True,
                                   prune=True, shapes=shape_lib)
        except Exception:
            continue
        if gaps:
            open_postulates += 1
            per_post[nm] = len(gaps)
            total_open += len(gaps)
        if (i + 1) % 100 == 0:
            print(f"  ... {i+1}/{len(chosen)} postulates; "
                  f"open gaps so far={total_open}; "
                  f"{time.perf_counter()-t:.0f}s", flush=True)
    elapsed = time.perf_counter() - t
    print()
    print(f"Synthesis done in {elapsed:.0f}s")
    print()

    recorded = s.nodes("SynthesizedGap")
    print("=" * 76)
    print("OPEN GAP-SET CHARACTER (live)")
    print("=" * 76)
    print(f"  Postulates synthesized:               {len(chosen)}")
    print(f"  Postulates yielding any OPEN gap:      {open_postulates}")
    print(f"  Total OPEN gaps recorded:             {total_open}")
    print(f"  SynthesizedGap nodes in graph:        {len(recorded)}")
    print()

    # ---- how many DISTINCT capability axes do the open gaps collapse to? ----
    print("=" * 76)
    print("AXIS COLLAPSE — distinct capability-axes after the agent groups gaps")
    print("=" * 76)
    axes = gp.build_axis_env(s)
    n_axes = len([a for a in axes
                  if s.node(a)["attrs"].get(gp.AXIS_FLAG) == 1.0])
    print(f"  OPEN gaps:                            {total_open}")
    print(f"  collapse to distinct CapabilityAxes:  {n_axes}")
    if n_axes:
        print(f"  compression ratio (gaps/axes):        "
              f"{total_open / max(n_axes,1):.1f}x")
    print()

    # ---- the agent's ranker, live ----
    # gp.rank_gaps wraps the Term in _Pred (the OLD Python-wrapper substrate
    # path). Against the raw _native.Substrate, evaluate() takes the Term dict
    # directly. We evaluate the agent's OWN payoff/score Terms (gp.payoff_term /
    # gp.score_term — unchanged) natively here; the DECISION stays the agent's
    # graph Term, only the eval entrypoint differs.
    print("=" * 76)
    print("THE AGENT'S RANKER — payoff/score Terms (native eval), top 25 by score")
    print("=" * 76)

    def rank_native(sub):
        rows = []
        for ax in sub.nodes(gp.AXIS_TYPE):
            a = sub.node(ax)["attrs"]
            if a.get(gp.AXIS_FLAG) != 1.0:
                continue
            payoff = sub.evaluate(gp.payoff_term("x"), {"x": ax})
            score = sub.evaluate(gp.score_term("x"), {"x": ax})
            rows.append({
                "capability_keys": list(a.get("capability_keys", [])),
                "payoff": int(payoff),
                "min_order": int(a.get(gp.ORDER_ATTR, 99)),
                "score": int(score),
                "source_domains": list(a.get("source_domains", [])),
                "gap_text": a.get("gap_text", ""),
                "axis_id": ax,
            })
        rows.sort(key=lambda r: -r["score"])
        return rows

    ranked = rank_native(s)
    print(f"  {'payoff':>6} {'order':>5} {'score':>8}  capability_keys / domains")
    print(f"  {'-'*72}")
    for r in ranked[:25]:
        keys = ",".join(r["capability_keys"][:3])
        doms = ",".join(r["source_domains"][:2])
        print(f"  {r['payoff']:>6} {r['min_order']:>5} {r['score']:>8}  "
              f"{short(keys, 42):<44} [{short(doms,22)}]")
    print()

    # payoff distribution — is the selector concentrating (signal) or flat (noise)?
    payoff_hist = Counter(r["payoff"] for r in ranked)
    print("  Payoff distribution across all axes (postulates-unified per axis):")
    for p in sorted(payoff_hist, reverse=True):
        bar = "#" * min(50, payoff_hist[p])
        print(f"    payoff={p:>3}: {payoff_hist[p]:>4} axes  {bar}")
    print()

    # ---- the agent's PICK — the native Argmax Term (gp.pick_term) ----
    print("=" * 76)
    print("THE AGENT'S PICK — Argmax Term (gp.pick_term) evaluated natively")
    print("=" * 76)
    picked_axis = s.evaluate(gp.pick_term(), {})
    win_row = next((r for r in ranked if r["axis_id"] == picked_axis), ranked[0])
    runner = next((r for r in ranked if r["axis_id"] != win_row["axis_id"]), None)
    winner = dict(win_row)
    winner["runner_up_payoff"] = runner["payoff"] if runner else 0
    print(f"  Argmax-Term picked axis node: {picked_axis} "
          f"(== top-of-rank: {picked_axis == ranked[0]['axis_id']})")
    print(f"  PICKED capability_keys:  {winner['capability_keys']}")
    print(f"  payoff (postulates unified): {winner['payoff']}")
    print(f"  min_order:                   {winner['min_order']}")
    print(f"  score:                       {winner['score']}")
    print(f"  runner-up payoff:            {winner['runner_up_payoff']}")
    print(f"  source_domains:              {winner['source_domains']}")
    print(f"  gap_text: {short(winner['gap_text'], 200)}")
    print()
    # which postulates does the winning axis unify?
    ax = winner["axis_id"]
    unified = [s.node(p)["attrs"].get("name", "?")
               for p in s.neighbours(ax, gp.UNIFIES_EDGE)]
    print(f"  postulates unified by the winning axis ({len(unified)}):")
    for u in unified[:15]:
        print(f"    · {u}")
    print()

    # ---- HONESTY PROBE: is the winning axis an ARTIFACT? ----
    print("=" * 76)
    print("ARTIFACT CHECK on the ungated pick")
    print("=" * 76)
    gaps_in_axis = [n for n in s.nodes("SynthesizedGap")
                    if frozenset(str(k).lower()
                                 for k in s.node(n)["attrs"].get("capability_keys", []))
                    == frozenset(str(k).lower() for k in winner["capability_keys"])]
    via = set()
    txt = set()
    for n in gaps_in_axis:
        via.update(s.node(n)["attrs"].get("via_shapes", []))
        txt.add(s.node(n)["attrs"].get("gap", ""))
    print(f"  gaps under the winning capability sig: {len(gaps_in_axis)}")
    print(f"  distinct via_shapes producing them:    {len(via)}  {sorted(via)[:3]}")
    print(f"  distinct gap texts:                    {len(txt)}")
    print(f"  -> {'ARTIFACT (1 promiscuous shape, 1 canned text)' if len(via)==1 and len(txt)==1 else 'multi-shape (genuine candidate)'}")
    print()

    # ---- THE FIX: specificity-gated pick (the agent's own gate) ----
    print("=" * 76)
    print("SPECIFICITY-GATED PICK — the agent's compression-honest selector")
    print("=" * 76)
    breadth = gp.shape_firing_breadth(s, shape_lib)
    bvals = sorted(breadth.values())
    npost = len(posts)
    cap = gp.PROMISCUITY_FRAC * npost
    n_promisc = sum(1 for b in bvals if b > cap)
    print(f"  shape firing breadth: median={bvals[len(bvals)//2]} "
          f"max={bvals[-1]} (corpus N={npost})")
    print(f"  PROMISCUITY gate at >{gp.PROMISCUITY_FRAC:.0%} ({cap:.0f} postulates): "
          f"{n_promisc}/{len(bvals)} shapes gated out")
    print()
    # fresh substrate so the gate re-groups cleanly (axes are idempotent-cached).
    # build_axis_env(shape_breadth=...) IS the agent's gate; we then evaluate the
    # agent's OWN payoff/score Terms natively over the gated axes (the gp.rank_gaps
    # path wraps Terms in _Pred for the Python-wrapper substrate; against the raw
    # _native.Substrate we feed the Term dict directly — same Term, native eval).
    s2 = fresh_substrate()
    install_all(s2)
    for nm in chosen:
        try:
            synthesize_gaps(s2, nm, max_order=1, record=True,
                            prune=True, shapes=shape_lib)
        except Exception:
            continue
    gp.build_axis_env(s2, shape_breadth=breadth)   # the gate
    gated = []
    for ax in s2.nodes(gp.AXIS_TYPE):
        a = s2.node(ax)["attrs"]
        if a.get(gp.AXIS_FLAG) != 1.0:
            continue
        payoff = s2.evaluate(gp.payoff_term("x"), {"x": ax})
        score = s2.evaluate(gp.score_term("x"), {"x": ax})
        gated.append({"capability_keys": list(a.get("capability_keys", [])),
                      "payoff": int(payoff), "score": int(score),
                      "source_domains": list(a.get("source_domains", [])),
                      "gap_text": a.get("gap_text", ""), "axis_id": ax})
    gated.sort(key=lambda r: -r["score"])
    print(f"  axes after gate: {len(gated)} (was {n_axes} ungated)")
    print(f"  {'payoff':>6} {'score':>8}  capability_keys / domains")
    print(f"  {'-'*68}")
    for r in gated[:12]:
        keys = ",".join(r["capability_keys"][:3])
        doms = ",".join(r["source_domains"][:2])
        print(f"  {r['payoff']:>6} {r['score']:>8}  "
              f"{short(keys,40):<42} [{short(doms,20)}]")
    print()
    # the agent's Argmax Term over the GATED axes
    gpick = s2.evaluate(gp.pick_term(), {})
    gwin = next((r for r in gated if r["axis_id"] == gpick), gated[0])
    grunner = next((r for r in gated if r["axis_id"] != gwin["axis_id"]), None)
    print(f"  GATED PICK (Argmax Term): {gwin['capability_keys']}  "
          f"payoff={gwin['payoff']} (runner-up "
          f"{grunner['payoff'] if grunner else 0}) "
          f"domains={gwin['source_domains']}")
    print(f"  gap_text: {short(gwin['gap_text'], 180)}")
    # verify the gated pick is NOT an artifact
    gv = set(); gt = set()
    for n in s2.nodes("SynthesizedGap"):
        if frozenset(str(k).lower() for k in s2.node(n)["attrs"].get("capability_keys", [])) \
           == frozenset(str(k).lower() for k in gwin["capability_keys"]):
            gv.update(s2.node(n)["attrs"].get("via_shapes", []))
            gt.add(s2.node(n)["attrs"].get("gap", ""))
    print(f"  gated-pick via_shapes={len(gv)} texts={len(gt)} -> "
          f"{'STILL artifact' if len(gv)==1 and len(gt)==1 else 'genuine (multi-shape)'}"
          f"  shapes:{sorted(gv)[:2]}")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
