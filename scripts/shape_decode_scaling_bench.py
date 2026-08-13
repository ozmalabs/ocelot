#!/usr/bin/env python3
"""scripts/shape_decode_scaling_bench.py — SHAPE_DECODE_LIBRARY_SCALING_PREREG.md's
measurement. Boots a real agent (`boot_core` + `load_all_seeds`, the same
pattern `scripts/rule_signature_measure.py` uses), then:

  1. Measures real `ShapeDecode` latency against the REAL, seed-sourced
     `ShapeSignature` codebook (407 parts on a full boot) at both real
     caller configurations (`beam=1,max_steps=1,cand_k=1` and
     `beam=3,max_steps=8,cand_k=3`).
  2. Sweeps codebook size synthetically (real signatures, cloned with
     replacement to controlled sizes) from 50 to 10,000 to establish the
     scaling trend past what today's real corpus reaches.
  3. Reports the real `ShapeSignature` distributional stats (predicate-set /
     `kind` / arity bucket balance) needed to evaluate a structural
     pre-filter's soundness.
  4. Builds a REAL, adapted `RuleSummary`-derived codebook (2229 parts, each
     part's signature is that rule's own real `where_signature_json` rows)
     and decodes against it via the unmodified `ShapeDecode` Term — the
     2000+-entry real-content test the charter asks for.

MEASUREMENT SCRIPT ONLY — no agent decisions, no graph writes beyond the
throwaway benchmark codebook nodes minted into this one-shot process's own
substrate (never persisted, never installed as a seed).
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
import domains.rule_signature as rsig  # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


REAL_CONFIGS = {
    "rt(1,1,1)": (1, 1, 1),
    "composer(3,8,3)": (3, 8, 3),
}


def get_sig(s, n):
    at = s.node(n)["attrs"]
    sig = at.get("signature")
    if isinstance(sig, str):
        try:
            sig = json.loads(sig)
        except Exception:
            sig = None
    return at, sig


def run_decode(native, goal, codebook_type, beam, max_steps, cand_k, budget=0, n=7):
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": goal},
            "codebook_type": codebook_type,
            "beam": beam, "max_steps": max_steps, "cand_k": cand_k,
            "budget": budget, "field": ""}
    times = []
    out = None
    for _ in range(n):
        t0 = time.perf_counter()
        out = native.evaluate(term, {})
        times.append(time.perf_counter() - t0)
    times.sort()
    return times, out


def main():
    t0 = time.time()
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    native = s._inner
    print(f"boot: {time.time()-t0:.2f}s, loaded {rep['loaded']}/{rep['total']} seeds, "
          f"{len(rep['failed'])} failed (expected: chess/vision optional-dep)", flush=True)

    results = {}

    # --- Part 1: real ShapeSignature codebook, real caller configs ---
    ns = s.nodes("ShapeSignature")
    sigs = []
    for n in ns:
        at, sig = get_sig(s, n)
        if isinstance(sig, (list, tuple)) and sig:
            sigs.append(sig)
    print(f"\n=== Part 1: real ShapeSignature codebook ({len(ns)} nodes, "
          f"{len(sigs)} usable) ===", flush=True)

    random.seed(42)
    goal = []
    for sig in random.sample(sigs, 3):
        goal.extend(sig[:4])
    print(f"goal: {len(goal)} relations (sampled from 3 real parts)", flush=True)

    real_results = {}
    for label, (beam, ms, ck) in REAL_CONFIGS.items():
        times, out = run_decode(native, goal, "ShapeSignature", beam, ms, ck)
        med = times[len(times) // 2]
        real_results[label] = {
            "median_ms": round(med * 1000, 3),
            "min_ms": round(times[0] * 1000, 3),
            "max_ms": round(times[-1] * 1000, 3),
            "budget_exhausted": out.get("budget_exhausted"),
        }
        print(f"  {label}: median={real_results[label]['median_ms']}ms "
              f"min={real_results[label]['min_ms']}ms max={real_results[label]['max_ms']}ms "
              f"budget_exhausted={out.get('budget_exhausted')}", flush=True)
    load_only_times, _ = run_decode(native, [], "ShapeSignature", 1, 1, 1, n=7)
    load_only_ms = round(load_only_times[len(load_only_times) // 2] * 1000, 3)
    real_results["load_parts_only_ms"] = load_only_ms
    print(f"  load_parts-only cost (empty goal): {load_only_ms}ms", flush=True)
    results["real_shapesignature_407"] = real_results

    # --- Part 1b: distributional / bucket-balance stats ---
    import collections
    pset_bucket, kind_bucket, arity_bucket = (collections.Counter() for _ in range(3))
    for n in ns:
        at, sig = get_sig(s, n)
        if not isinstance(sig, (list, tuple)):
            continue
        preds = tuple(sorted(set(r[0] for r in sig if isinstance(r, (list, tuple)) and r)))
        pset_bucket[preds] += 1
        kind_bucket[at.get("kind")] += 1
        arities = tuple(sorted(set(len(r) for r in sig if isinstance(r, (list, tuple)))))
        arity_bucket[arities] += 1

    def bucket_report(name, counter):
        sizes = sorted(counter.values(), reverse=True)
        total = sum(sizes)
        return {"n_buckets": len(counter), "total": total,
                "largest_bucket": sizes[0] if sizes else 0,
                "largest_bucket_frac": round(sizes[0] / total, 3) if total else 0,
                "top5_sizes": sizes[:5]}

    bucket_stats = {
        "predicate_set": bucket_report("predicate_set", pset_bucket),
        "kind": bucket_report("kind", kind_bucket),
        "arity_set": bucket_report("arity_set", arity_bucket),
    }
    print("\n=== Part 1b: bucket-balance stats (real 407-part codebook) ===", flush=True)
    for k, v in bucket_stats.items():
        print(f"  {k}: {v}", flush=True)
    results["bucket_balance"] = bucket_stats

    # --- Part 2: synthetic size sweep (real signatures cloned to controlled sizes) ---
    print("\n=== Part 2: synthetic codebook-size sweep ===", flush=True)
    sweep_sizes = [50, 200, 500, 1000, 2000, 5000, 10000]
    sweep_results = {}
    for sz in sweep_sizes:
        ct = f"Bench{sz}"
        for i in range(sz):
            src = sigs[i % len(sigs)]
            s.add_node(ct, {"name": f"bench_{ct}_{i}", "signature": src, "kind": "bench"})
        row = {}
        for label, (beam, ms, ck) in REAL_CONFIGS.items():
            times, out = run_decode(native, goal, ct, beam, ms, ck)
            med = times[len(times) // 2]
            row[label] = {"median_ms": round(med * 1000, 3),
                           "min_ms": round(times[0] * 1000, 3),
                           "max_ms": round(times[-1] * 1000, 3),
                           "budget_exhausted": out.get("budget_exhausted")}
        sweep_results[sz] = row
        print(f"  size={sz}: {row}", flush=True)
    results["synthetic_sweep"] = sweep_results

    # --- Part 3: real RuleSummary-adapted codebook (2000+ entries, real content) ---
    print("\n=== Part 3: real RuleSummary-adapted codebook (ShapeDecode over real rule where-signatures) ===", flush=True)
    rn = s.nodes("RuleSummary")
    print(f"RuleSummary count: {len(rn)}", flush=True)
    t0 = time.time()
    n_touched = rsig.ensure_where_signature(s)
    print(f"where_signature computed for {n_touched} rules in {time.time()-t0:.1f}s", flush=True)

    parts_built = 0
    sig_lens = []
    median_candidate = None  # (row_count, sig_list) closest to the median, for a realistic goal
    for n in rn:
        at = s.node(n)["attrs"]
        rows_json = at.get("where_signature_json")
        if not rows_json:
            continue
        sig = rsig._rows_from_jsonable(rows_json)
        sig_list = [list(row) for row in sig]
        if not sig_list:
            continue
        sig_lens.append(len(sig_list))
        s.add_node("RuleShapeCodebook", {"name": f"rule_{n}", "signature": sig_list, "kind": "rule_where"})
        parts_built += 1
        # Track the SMALLEST non-trivial real rule signature as the goal source —
        # a real caller decoding a small/typical observation, not the 83881-row
        # outlier (which would test a different, part-SIZE-dominated regime, see
        # RESULTS doc §honest-caveat).
        if 5 <= len(sig_list) <= 40 and median_candidate is None:
            median_candidate = sig_list
    print(f"real rule-shape parts built: {parts_built}, "
          f"min/max/avg rows: {min(sig_lens)}/{max(sig_lens)}/{sum(sig_lens)/len(sig_lens):.1f}",
          flush=True)

    rule_goal = median_candidate if median_candidate is not None else sig_lens and [list(r) for r in
        rsig._rows_from_jsonable(s.node(rn[0])["attrs"].get("where_signature_json"))][:20]
    print(f"goal: {len(rule_goal)} relations (a real, small/typical rule's own where-signature)", flush=True)

    # Load-only isolation: an EMPTY goal makes eval_shape_decode return right
    # after `load_parts` (before scoring_sigs/search) — isolates the pure
    # graph-scan + attr-deserialize cost `load_parts` pays on EVERY call,
    # independent of the goal/observation or search depth (shape_decode.rs
    # :1457-1470: parts-empty and goal-empty checks both fire before any
    # per-part scoring work).
    load_only_times, _ = run_decode(native, [], "RuleShapeCodebook", 1, 1, 1, n=5)
    load_only_ms = round(load_only_times[len(load_only_times) // 2] * 1000, 3)
    print(f"  load_parts-only cost (empty goal, isolates the graph scan): {load_only_ms}ms", flush=True)

    rule_results = {}
    for label, (beam, ms, ck) in REAL_CONFIGS.items():
        t0 = time.time()
        times, out = run_decode(native, rule_goal, "RuleShapeCodebook", beam, ms, ck, n=5)
        med = times[len(times) // 2]
        rule_results[label] = {"median_ms": round(med * 1000, 3),
                                "min_ms": round(times[0] * 1000, 3),
                                "max_ms": round(times[-1] * 1000, 3),
                                "budget_exhausted": out.get("budget_exhausted"),
                                "wall_s_for_5_calls": round(time.time() - t0, 2)}
        print(f"  {label}: {rule_results[label]}", flush=True)
    results["rule_summary_adapted_2229"] = {
        "parts_built": parts_built,
        "sig_len_min": min(sig_lens), "sig_len_max": max(sig_lens),
        "sig_len_avg": round(sum(sig_lens) / len(sig_lens), 1),
        "where_signature_compute_s": round(time.time() - t0, 1),
        "load_parts_only_ms": load_only_ms,
        "goal_len": len(rule_goal),
        "results": rule_results,
    }

    out_path = os.path.join(ROOT, "scripts", "shape_decode_scaling_bench_results.json")
    json.dump(results, open(out_path, "w"), indent=2)
    print(f"\nWrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
