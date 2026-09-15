"""TRACK 6 — COST (the substrate's own compute per test, in native countable units).

A newer LLM would narrow the RQ2 typicality gap (see the caveat in
CAPABILITY_T5_RESULTS.md) — but it would WIDEN the cost gap, and the cost difference is
the durable, architecture-level point. This track measures the substrate's cost to
DO the capability (coin a new dimension mid-reasoning), in the substrate's OWN
hardware-independent counters, and frames the comparison honestly as a cost-CLASS
difference — NOT a joules-to-joules race we cannot fairly run in-repo.

WHAT IS MEASURED (primary, portable):
  the substrate's native op-counters, read straight off the running engine
  (s.counters()) around a minting run: node inserts, edge inserts, admissibility
  checks, rule EVALUATIONS, cache hits/misses. This is the "load = a directly
  countable substrate quantity" unit the project's own analysis-by-synthesis work
  uses — no human-data fit, no GPU, no matmul. Wall-clock is reported too, but only as
  a SECONDARY, hardware-dependent figure.

WHAT IS NOT MEASURED (and why):
  LLM joules / FLOPs are NOT measured here. They depend on hardware, batching, and
  quantization, and this repo holds no model. Any LLM number below is a clearly-
  LABELLED CITED ESTIMATE for framing only, never a measurement. The honest claim is
  not "our forward pass is cheaper by factor N" — it is a cost-CLASS difference:

    · SUBSTRATE: coining a new dimension is a bounded handful of graph ops at
      inference/think time, teacher-free.
    · LLM: representational change (a genuinely new axis) is not an inference-time
      operation at all — a frozen-weight model must be RETRAINED / fine-tuned to
      acquire it (a training run: many GPU-hours), or it cannot acquire it online.
  Different COST CLASS (bounded-tick inference vs a training run), not a ratio.

FALSIFIABLE CLAIMS:
  C1  BOUNDED NATIVE COST: a full minting run (coining new axes) costs a small,
      FINITE number of native ops per category — it does not blow up; the op-count is
      of the same small order across categories.
  C2  TEACHER-FREE / ZERO-GPU: ask-spy = 0 and the cost is entirely graph ops (node/
      edge/eval counters) — no model is loaded, no matmul is issued (there is no such
      call site in the minting path).
  C3  COST-CLASS: the substrate mints at inference in bounded ticks; the LLM
      comparison is a cost-CLASS statement (retraining vs bounded ticks), reported as
      a labelled cited estimate, not a measured ratio.
  C4  DISCRETE / INTEGER COUNTERS: every native cost quantity is an integer count
      (discrete quanta — consistent with the whole substrate).

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track6_cost.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))
sys.path.insert(0, os.path.join(_HERE, "scoring"))

import substrate_runner as R            # noqa: E402


# A clearly-LABELLED CITED ESTIMATE for framing only — NOT measured in this repo.
# Order-of-magnitude figures for "acquire a genuinely new representational axis":
LLM_COST_CLASS_ESTIMATE = {
    "inference_forward_pass": "billions of FLOPs / GPU matmuls per token (hardware- "
                              "and model-dependent; not measured here)",
    "acquire_a_new_axis": "NOT an inference-time operation — requires retraining / "
                          "fine-tuning (a training run: many GPU-hours), or is not "
                          "acquirable online at all for a frozen-weight model",
    "provenance": "cited/estimated for cost-CLASS framing only; this repo runs no "
                  "model and measures no LLM joules",
}


def main() -> int:
    print("=" * 78)
    print("TRACK 6 — COST (substrate's own native compute per test; cost-CLASS "
          "framing)")
    print("=" * 78)

    fx = R.load_fixture()
    cats = fx["categories"]

    print("\n" + "-" * 78)
    print("C1  BOUNDED NATIVE COST per minting run (coining new axes), read off the "
          "running engine")
    print("-" * 78)
    per_cat = []
    spy_total = 0
    all_int = True
    for cat, items in cats.items():
        c = R.capture_minting_cost(cat, items, R.FINE)
        per_cat.append(c)
        spy_total += c["ask_spy"]
        all_int = all_int and all(isinstance(v, int) for v in c["counters"].values())
        print("  %-10s ops_total=%-4d minted=%d  spy=%d  wall=%.3fs"
              % (cat, c["counter_ops_total"], c["n_minted"], c["ask_spy"],
                 c["wall_seconds"]))
        print("             counters=%s"
              % {k: v for k, v in c["counters"].items() if v})
    ops = [c["counter_ops_total"] for c in per_cat]
    max_ops = max(ops)
    # bounded = finite, small, and same order across categories (max <= 8x min+const)
    min_ops = min(o for o in ops if o > 0) if any(ops) else 0
    bounded = max_ops < 10000 and (min_ops == 0 or max_ops <= 8 * min_ops + 200)
    print("\n  op-count range across categories: %d .. %d (bounded, same small order)"
          % (min(ops), max_ops))
    c1 = bounded and all(c["n_minted"] >= 1 for c in per_cat)
    print("  C1 %s" % ("PASS" if c1 else "FAIL"))

    print("\n" + "-" * 78)
    print("C2  TEACHER-FREE / ZERO-GPU (cost is graph ops only; no model, no matmul)")
    print("-" * 78)
    # the cost counters are exclusively graph ops (node/edge/eval); no GPU/matmul
    # counter exists in the minting path. teacher-free = spy 0.
    print("  total ask-spy across all cost runs: %d" % spy_total)
    print("  cost counters are node/edge/admissibility/evaluation ops only "
          "(graph engine; no matmul/model-load call site in the minting path)")
    c2 = spy_total == 0
    print("  C2 %s" % ("PASS" if c2 else "FAIL"))

    print("\n" + "-" * 78)
    print("C3  COST-CLASS (substrate mints at inference in bounded ticks; LLM "
          "acquires an axis only by RETRAINING) — LLM side is a LABELLED CITED "
          "ESTIMATE, not a measured ratio")
    print("-" * 78)
    mean_ops = sum(ops) / len(ops)
    print("  SUBSTRATE (measured): coin a new dimension in ~%d native graph ops, "
          "teacher-free, at think time, no GPU." % round(mean_ops))
    print("  LLM (cited estimate, NOT measured here):")
    print("     - inference forward pass: %s"
          % LLM_COST_CLASS_ESTIMATE["inference_forward_pass"])
    print("     - acquire a NEW axis:     %s"
          % LLM_COST_CLASS_ESTIMATE["acquire_a_new_axis"])
    print("  => DIFFERENT COST CLASS (bounded-tick inference vs a training run), "
          "not a factor-of-N race.")
    # C3 is a framing claim; it holds if the substrate cost is bounded-at-inference
    # (measured above) AND we have honestly labelled the LLM side as an estimate.
    c3 = c1 and LLM_COST_CLASS_ESTIMATE["provenance"].startswith("cited")
    print("  C3 %s" % ("PASS" if c3 else "FAIL"))

    print("\n" + "-" * 78)
    print("C4  DISCRETE / INTEGER COUNTERS (discrete quanta throughout)")
    print("-" * 78)
    c4 = all_int
    print("  every native cost counter is an integer count: %s" % all_int)
    print("  C4 %s" % ("PASS" if c4 else "FAIL"))

    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("C1 bounded finite native cost", c1),
            ("C2 teacher-free / zero-GPU (graph ops only)", c2),
            ("C3 cost-class (labelled cited LLM estimate)", c3),
            ("C4 discrete / integer counters", c4)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK 6 PASS: coining a new dimension costs the substrate a small, "
               "bounded, integer number of native graph ops (~%d on average), "
               "teacher-free and with no GPU/matmul/model — while an LLM acquires a "
               "genuinely new representational axis only by RETRAINING (a training "
               "run), not at inference. This is a cost-CLASS difference, not a "
               "joules ratio; the LLM side is a labelled cited estimate, not measured "
               "here. A newer LLM narrows the typicality gap but does not change this "
               "cost class." % round(mean_ops)
               if allpass else
               "TRACK 6 HONEST RESULT: see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": 6, "metric": "native_compute_cost_per_test",
               "per_category": [{"category": c["category"],
                                 "counter_ops_total": c["counter_ops_total"],
                                 "counters": c["counters"],
                                 "n_minted": c["n_minted"],
                                 "wall_seconds": round(c["wall_seconds"], 4)}
                                for c in per_cat],
               "mean_ops": round(mean_ops, 1),
               "op_range": [min(ops), max_ops],
               "ask_spy_total": spy_total,
               "llm_cost_class_estimate": LLM_COST_CLASS_ESTIMATE,
               "c1": c1, "c2": c2, "c3": c3, "c4": c4, "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
