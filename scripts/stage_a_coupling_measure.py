"""THE SETTLING MEASUREMENT — does batching the UNCOUPLED rules differ from
running them to fixpoint?

Prediction registered at 472b303 (`STAGE_A_REASSESSED_AGAINST_V23.md`), before
this file existed:

    "does batching the uncoupled 56.3% differ from running them to fixpoint, on
    any workload? On the theory it should be byte-identical, and if it is not,
    the coupling test is incomplete in the same way the write-set relation was."

Under the revised theory (`papers/formal/01_...`, 2026-08-26) a rule whose
`read_set ∩ write_set` is empty has no boundary coupling its bindings' collapses,
so they are asynchronous by default and ordering them together must be a no-op.
`stage_a::rule_is_derivable` already refuses everything else, so Stage A ON is
exactly "batch the uncoupled, fixpoint the rest".

Compare mode runs BOTH and reports divergence per drain, plus the soundness
property: drains that diverged and that `conflicts` did NOT flag.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

OUTDIR = os.path.join(ROOT, "results", "stage_a_coupling")

# Workloads: real seeded runs that exercise many rules over many drains.
WORKLOADS = [
    ("learning_progress", "learning_progress_measure"),
    ("psychosis_grounding", "psychosis_grounding_demo"),
]


def _native():
    import substrate_rs
    return substrate_rs._native if hasattr(substrate_rs, "_native") else None


def run_workload(modname, native):
    """Import and main() a measure script under compare mode."""
    native.stage_a_compare_reset()
    native.stage_a_reset()
    mod = importlib.import_module(modname)
    for attr in dir(mod):
        if attr.startswith("render_"):
            setattr(mod, attr, lambda *a, **k: None)
    mod.main()
    stats = native.stage_a_stats()
    cmp_ = native.stage_a_compare_stats()
    return stats, cmp_, native.stage_a_compare_samples()


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    import substrate_rs
    native = substrate_rs._native

    native.stage_a_enable(True)
    native.stage_a_compare_enable(True)

    out = {"prediction_registered_at": "472b303", "workloads": {}}
    for name, mod in WORKLOADS:
        try:
            stats, cmp_, samples = run_workload(mod, native)
        except Exception as exc:                      # a workload that cannot run
            out["workloads"][name] = {"error": f"{type(exc).__name__}: {exc}"}
            print(f"  {name:22s} SKIPPED — {type(exc).__name__}: {exc}")
            continue
        out["workloads"][name] = {
            "stats": dict(stats), "compare": dict(cmp_),
            "samples": samples[:6],
        }
        c = cmp_
        print(f"  {name:22s} compared={c['compared_drains']:6d} "
              f"diverged={c['diverged_drains']:4d} "
              f"UNSOUND={c['unsound_drains']:4d} "
              f"fallbacks={stats['conflict_fallbacks']} "
              f"excluded={stats['excluded_drains']}")
        if c["diverged_rules"]:
            print(f"  {'':22s} diverging rules: {c['diverged_rules'][:6]}")
        if c["unsound_rules"]:
            print(f"  {'':22s} UNSOUND rules:   {c['unsound_rules'][:6]}")

    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n  wrote {os.path.join(OUTDIR, 'results.json')}")


if __name__ == "__main__":
    main()
