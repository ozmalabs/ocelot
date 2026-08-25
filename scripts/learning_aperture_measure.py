"""THE LEARNING HALF — confirmatory measure (block 366500).

Prereg: STRESS_COMPRESSES_APERTURE_PREREG.md addendum, committed before this ran.

Three arms over the SAME shipped `learning_progress_curiosity` seed, driven by the
same adapter pattern as `scripts/learning_progress_measure.py` (set obs +
input_epoch, tick, read attrs — no decision in Python):

  LEARNABLE   regulated agent, an item whose observation differs from its held
              prediction. Should attend.
  COMPRESSED  dysregulated agent, THE SAME ITEM. The observation's dimension is
              unresolvable, so it arrives looking like the held prediction.
  MASTERED    regulated agent, an item that genuinely matches its prediction.

The registered claim is that COMPRESSED and MASTERED are indistinguishable on
every learning field, and separable only by `obs_established`.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.boot_core import boot_core  # noqa: E402
import learning_progress_measure as LP  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "learning_aperture")
FIELDS = ("residual", "fast_res", "slow_res", "learning_progress",
          "smoothed_progress", "interest", "attended")


def _manifest(name):
    return json.load(open(os.path.join(ROOT, "seeds", f"{name}.json")))


def _run(dysregulated, obs_seq, held=0.0, ticks=24):
    s, agent = boot_core()
    inner = s._inner
    inner.load_seed_manifest(LP.manifest_for(LP.SEED_ID), agent)
    inner.load_seed_manifest(_manifest("learning_aperture_gate"), agent)

    hub = s.add_node("CuriosityHub", {"kind": "aperture"})
    p = dict(LP.PARAMS)
    p["enabled"] = 1.0
    p["mode"] = 1.0
    cp = s.add_node("HeldCuriosityParams", p)
    inner.add_edge_unchecked(hub, "has_curiosity_params", cp)

    # dimension "d1" is the one stress removes
    aff = s.add_node("AffectiveState", {
        "dysregulated": 1.0 if dysregulated else 0.0,
        "stress_resolves_dims": ["d0"] if dysregulated else ["d0", "d1"]})
    s.add_edge(aff, "gates_attention", hub)

    init = dict(LP.ITEM_INIT)
    init.update(held=held, obs_dim="d1", obs_true=0.0, obs_established=1.0)
    item = s.add_node("AttentionItem", init)
    inner.add_edge_unchecked(hub, "has_attention_item", item)

    traj = []
    for t in range(ticks):
        # the adapter writes what the WORLD presented; the gate decides what the
        # learner actually observes.
        s.set_attr(item, "obs_true", float(obs_seq[t % len(obs_seq)]))
        s.set_attr(item, "input_epoch", float(t))
        inner.run_rules()
        a = s.node(item)["attrs"]
        traj.append({k: float(a.get(k, 0.0)) for k in FIELDS}
                    | {"obs_established": float(a.get("obs_established", 0.0)),
                       "obs": float(a.get("obs", 0.0))})
    return traj


def _summary(traj):
    last = traj[-1]
    return {k: last[k] for k in FIELDS} | {
        "obs_established": last["obs_established"],
        "obs": last["obs"],
        "ever_attended": float(any(r["attended"] > 0.0 for r in traj)),
        "max_residual": max(r["residual"] for r in traj),
        "max_progress": max(r["learning_progress"] for r in traj),
    }


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    LEARNABLE = [0, 3, 6, 9, 12, 15, 18, 21]      # differs from held=0
    MASTERED = [0, 0, 0, 0, 0, 0, 0, 0]           # genuinely matches held=0

    arms = {
        "LEARNABLE(regulated)":  _run(False, LEARNABLE),
        "COMPRESSED(stressed)":  _run(True, LEARNABLE),
        "MASTERED(regulated)":   _run(False, MASTERED),
    }
    out = {"prereg": "STRESS_COMPRESSES_APERTURE_PREREG.md#addendum",
           "block": 366500,
           "arms": {k: _summary(v) for k, v in arms.items()}}

    # P4: more exposure on the compressed arm
    out["exposure_sweep"] = [
        {"ticks": n, **_summary(_run(True, LEARNABLE, ticks=n))}
        for n in (24, 48, 96, 192)]

    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("=== THE LEARNING HALF (real engine, shipped curiosity seed) ===\n")
    hdr = f"  {'arm':22s} {'resid':>6s} {'progress':>9s} {'interest':>9s} " \
          f"{'attended':>9s} {'ever_att':>9s} {'established':>12s}"
    print(hdr)
    for name, sm in out["arms"].items():
        print(f"  {name:22s} {sm['residual']:6.1f} {sm['learning_progress']:9.1f} "
              f"{sm['interest']:9.1f} {sm['attended']:9.1f} "
              f"{sm['ever_attended']:9.1f} {sm['obs_established']:12.1f}")
    print("\n  exposure sweep on the compressed arm:")
    for row in out["exposure_sweep"]:
        print(f"    ticks={row['ticks']:4d} -> max_residual={row['max_residual']:.1f} "
              f"max_progress={row['max_progress']:.1f} ever_attended={row['ever_attended']:.0f}")
    print(f"\n  wrote {os.path.join(OUTDIR, 'results.json')}")


if __name__ == "__main__":
    main()
