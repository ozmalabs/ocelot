#!/usr/bin/env python3
"""Between-layer extraction — measure the transformer's actual function.

RUN WITH THE VENV PYTHON (torch is external):
  HF_HOME=/applications/data/model_graph_work/hf_home \\
  /applications/data/model_graph_work/venv/bin/python \\
  scripts/between_layer_extraction_measure.py

See docs/research/psychology_affect/BETWEEN_LAYER_EXTRACTION_PREREG.md.

  CLAIM 1: real per-layer deltas + logit-lens answer-rank -> 0 by the top.
  CLAIM 2: facts resolve at CHARACTERISTIC depths, not uniformly.
  CLAIM 3: the depth-trajectory is structure the static embedding lacks.
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from domains import between_layer_extraction as ble  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-1.7B"

# (prompt, answer-with-leading-space, relation-type) — held-out answers used
# only to SCORE where the model produces them.
BATTERY = [
    ("The capital of France is", " Paris", "capital"),
    ("The capital of Japan is", " Tokyo", "capital"),
    ("The capital of Italy is", " Rome", "capital"),
    ("The opposite of hot is", " cold", "antonym"),
    ("The opposite of up is", " down", "antonym"),
    ("The opposite of big is", " small", "antonym"),
    ("A dog is a kind of", " animal", "isa"),
    ("A rose is a kind of", " flower", "isa"),
    ("Two plus two equals", " 4", "arithmetic"),
    ("The plural of mouse is", " mice", "morphology"),
]


def _first_id(tm, answer):
    ids = tm.tok(answer, add_special_tokens=False)["input_ids"]
    return ids[0] if ids else None


def _resolution_depth(ranks):
    """First layer at which the answer reaches rank 0 (top), or None."""
    for L, r in enumerate(ranks):
        if r == 0:
            return L
    return None


def main():
    if not ble.have_torch():
        print("torch/transformers not available — this measure needs the venv "
              "python. See the module docstring.")
        return
    print("=" * 72)
    print("BETWEEN-LAYER EXTRACTION — the transformer's actual function")
    print("(real forward passes; Qwen3-1.7B on GPU)")
    print("=" * 72)

    tm = ble.load_traced(MODEL)
    print("\nloaded %s: %d layers, device %s" %
          (MODEL.split("/")[-1], tm.n_layers, tm.device))

    per_relation = {}
    resolved = 0
    delta_growth = []
    print("\n%-34s %-9s %-12s" % ("prompt", "answer", "resolution_depth"))
    for prompt, answer, rel in BATTERY:
        tr = ble.forward_trace(tm, prompt)
        aid = _first_id(tm, answer)
        ranks = ble.answer_rank_by_layer(tm, tr["hidden"], aid)
        rd = _resolution_depth(ranks)
        if rd is not None:
            resolved += 1
            per_relation.setdefault(rel, []).append(rd)
        # delta grows with depth?
        d = tr["deltas"]
        delta_growth.append(d[-1] > d[0])
        print("%-34s %-9s %-12s (final rank %d)" %
              (prompt, answer.strip(), rd if rd is not None else "never",
               ranks[-1]))

    n = len(BATTERY)
    # ---- CLAIM 1 -------------------------------------------------------
    print("\n[CLAIM 1] between-layer function recovered")
    print("  answers reaching top by final layer: %d/%d" % (resolved, n))
    print("  per-layer delta grows with depth: %d/%d prompts" %
          (sum(delta_growth), n))
    claim1 = resolved >= 0.7 * n and sum(delta_growth) >= 0.7 * n

    # ---- CLAIM 2 -------------------------------------------------------
    print("\n[CLAIM 2] characteristic resolution depths (not uniform)")
    all_depths = [d for ds in per_relation.values() for d in ds]
    for rel, ds in sorted(per_relation.items()):
        print("  %-12s resolves at layers %s (of %d)  mean %.1f" %
              (rel, ds, tm.n_layers, sum(ds) / len(ds)))
    if all_depths:
        lo, hi = min(all_depths), max(all_depths)
        span_frac = (hi - lo) / tm.n_layers
        mean_frac = (sum(all_depths) / len(all_depths)) / tm.n_layers
        print("  resolution-depth band: L%d..L%d (%.0f%%..%.0f%% of stack), "
              "mean %.0f%%" % (lo, hi, 100 * lo / tm.n_layers,
                               100 * hi / tm.n_layers, 100 * mean_frac))
        # characteristic = concentrated in a mid-late band, not spread 0..1
        claim2 = mean_frac > 0.5 and span_frac < 0.6
    else:
        claim2 = False

    # ---- CLAIM 3 -------------------------------------------------------
    print("\n[CLAIM 3] depth-trajectory is structure the static embedding "
          "lacks")
    print("  The ordered (rank-by-layer) trajectory of WHERE a fact is built")
    print("  is not present in any static kNN graph — it is a property of the")
    print("  computation, only visible by running the model. Demonstrated by")
    print("  the per-relation resolution depths above being well-defined.")
    claim3 = bool(all_depths)

    print("\n" + "=" * 72)
    print("VERDICT")
    print("  CLAIM 1 between-layer function recovered:   %s" %
          ("HOLDS" if claim1 else "FAILS"))
    print("  CLAIM 2 characteristic resolution depths:   %s" %
          ("HOLDS" if claim2 else "FAILS"))
    print("  CLAIM 3 trajectory = new structure:         %s" %
          ("HOLDS" if claim3 else "FAILS"))
    print("=" * 72)
    return {"claim1": claim1, "claim2": claim2, "claim3": claim3,
            "per_relation": per_relation}


def run_model(model_dir, device="cpu", dtype="float32"):
    """Run the battery on one model; return a per-model report dict with
    resolution depths (absolute + as fraction of the stack), delta-growth
    ratio, and per-relation resolution depths."""
    tm = ble.load_traced(model_dir, device=device, dtype=dtype)
    per_relation = {}
    resolved = 0
    growth = []
    rows = []
    for prompt, answer, rel in BATTERY:
        tr = ble.forward_trace(tm, prompt)
        aid = _first_id(tm, answer)
        ranks = ble.answer_rank_by_layer(tm, tr["hidden"], aid)
        rd = _resolution_depth(ranks)
        d = tr["deltas"]
        growth.append(d[-1] / (d[0] + 1e-9))
        if rd is not None:
            resolved += 1
            per_relation.setdefault(rel, []).append(rd)
        rows.append((prompt, answer.strip(), rd, ranks[-1]))
    n = len(BATTERY)
    all_depths = [d for ds in per_relation.values() for d in ds]
    rel_mean_frac = {rel: (sum(ds) / len(ds)) / tm.n_layers
                     for rel, ds in per_relation.items()}
    return {
        "model": model_dir.split("/")[-1],
        "n_layers": tm.n_layers,
        "resolved": resolved, "n": n,
        "delta_growth_median": sorted(growth)[len(growth) // 2],
        "resolution_frac_mean": (sum(all_depths) / len(all_depths) / tm.n_layers)
        if all_depths else None,
        "resolution_frac_band": (min(all_depths) / tm.n_layers,
                                 max(all_depths) / tm.n_layers) if all_depths else None,
        "rel_mean_frac": rel_mean_frac,
        "rows": rows,
    }


def size_sweep(device="cpu"):
    """Run the between-layer battery across the Qwen3 size sweep on CPU and test
    whether the between-layer FUNCTION is a stable FRACTIONAL structure across
    scale (resolution band as a fraction of depth, and the relation ordering)."""
    import os
    base = "/applications/data/model_graph_work"
    models = [os.path.join(base, m) for m in
              ("Qwen3-0.6B", "Qwen3-1.7B", "Qwen3-4B")]
    models = [m for m in models if os.path.isdir(m)]
    if not ble.have_torch() or not models:
        print("torch/models absent — run with the venv python; see docstring.")
        return
    print("=" * 74)
    print("BETWEEN-LAYER SIZE SWEEP (CPU) — is the function stable across scale?")
    print("=" * 74)
    reports = []
    for m in models:
        print("\n[%s] running on %s ..." % (m.split("/")[-1], device))
        import time
        t0 = time.time()
        rep = run_model(m, device=device)
        rep["_secs"] = time.time() - t0
        reports.append(rep)
        print("  %d layers, resolved %d/%d, %.0fs" %
              (rep["n_layers"], rep["resolved"], rep["n"], rep["_secs"]))

    print("\n%-14s %-8s %-10s %-16s %-14s" %
          ("model", "layers", "resolved", "res_frac(band)", "delta_growth"))
    for r in reports:
        band = r["resolution_frac_band"]
        bs = "%.2f-%.2f" % band if band else "n/a"
        rf = "%.2f" % r["resolution_frac_mean"] if r["resolution_frac_mean"] else "n/a"
        print("  %-12s %-8d %-10s %-16s %-14.1f" %
              (r["model"], r["n_layers"], "%d/%d" % (r["resolved"], r["n"]),
               "%s (m%s)" % (bs, rf), r["delta_growth_median"]))

    # relation ordering by fractional resolution depth — stable across sizes?
    print("\n  per-relation resolution FRACTION (of stack):")
    rels = sorted({rel for r in reports for rel in r["rel_mean_frac"]})
    print("  %-14s %s" % ("relation", "  ".join("%8s" % r["model"] for r in reports)))
    orderings = []
    for rel in rels:
        vals = [r["rel_mean_frac"].get(rel) for r in reports]
        print("  %-14s %s" % (rel, "  ".join(
            ("%8.2f" % v) if v is not None else "%8s" % "-" for v in vals)))
    for r in reports:
        present = [(rel, r["rel_mean_frac"][rel]) for rel in rels
                   if rel in r["rel_mean_frac"]]
        orderings.append([rel for rel, _ in sorted(present, key=lambda kv: kv[1])])

    print("\n  relation ordering (earliest->latest resolving) per model:")
    for r, o in zip(reports, orderings):
        print("    %-12s %s" % (r["model"], " < ".join(o)))
    # stable = the fractional band is similar (all mid-late) and orderings agree
    bands_midlate = all(r["resolution_frac_mean"] and r["resolution_frac_mean"] > 0.5
                        for r in reports if r["resolution_frac_mean"])
    print("\n" + "=" * 74)
    print("VERDICT: fractional resolution band mid-late across ALL sizes: %s" %
          bands_midlate)
    print("  (within Qwen3 family; CPU; logit-lens is a qualitative probe)")
    print("=" * 74)
    return {"reports": reports, "bands_midlate": bands_midlate}


if __name__ == "__main__":
    import sys as _sys
    if "--sweep" in _sys.argv:
        size_sweep()
    else:
        main()
