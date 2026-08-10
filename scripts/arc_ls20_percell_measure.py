"""arc_ls20_percell_measure — RUNG 222000: the powered OFFLINE teeth for the
PER-CELL live-mechanic model.

The HEADLINE: on held-out ls20-shaped scenarios with rich per-cell dynamics, the
learned per-cell model's CHANGE-SET metrics (strict changed-cell F1, location F1,
value-accuracy) are CI-separated ABOVE BOTH nulls (persistence + the 221000
aggregate-count model). RAW per-cell accuracy is reported ONLY to exhibit the
metric trap -- it is never the gate.

Also emits: the convergence staircase (G-convergence), the DISCOVERED action->
transform hypotheses (G-mechanic-discovered), and the source_match audit
(G-graph-native: the agent's prediction reads ONLY graph Hypothesis nodes; the
ground-truth _MOVE/_XFORM tables are WORLD PHYSICS, never consulted by the model).

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_percell_measure.py
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import worlds.arc_ls20_percell as PC  # noqa: E402
from worlds.arc_ls20_percell import (  # noqa: E402
    Percell, ACTIONS, make_scene, scene_grid, world_next, investigate,
    make_probe_set, score_prediction, AggregateCountNull,
)


def bootstrap_ci(xs, reps=1000, seed=0):
    xs = np.asarray(xs, dtype=float)
    if xs.size == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, xs.size, size=(reps, xs.size))
    means = xs[idx].mean(axis=1)
    return {"mean": float(xs.mean()), "lo": float(np.percentile(means, 2.5)),
            "hi": float(np.percentile(means, 97.5)), "n": int(xs.size)}


def source_audit():
    """Assert the AGENT's per-cell prediction path reads ONLY graph Hypothesis
    nodes -- never the ground-truth _MOVE/_XFORM action->transform tables (those
    are WORLD PHYSICS, consumed only by world_next). Returns the finding."""
    agent_fns = ["discover_spec", "_recognise_transform", "_apply_spec_to_grid",
                 "predict_next", "hypothesis"]
    banned = ["_MOVE", "_XFORM"]
    hits = {}
    for name in agent_fns:
        fn = getattr(PC, name, None) or getattr(Percell, name, None)
        src = inspect.getsource(fn)
        hits[name] = [b for b in banned if b in src]
    physics_uses = [b for b in banned if b in inspect.getsource(PC.world_next)]
    agent_uses = sorted({b for v in hits.values() for b in v})
    return {
        "agent_prediction_fns_referencing_ground_truth_tables": agent_uses,  # MUST be []
        "world_physics_uses_tables_by_design": physics_uses,                  # expected non-empty
        "per_fn": hits,
        "PASS": agent_uses == [],
    }


def main():
    N_EVAL = 200          # held-out scenes; x 10 actions = 2000 triples (pre-registered)
    BOOT = 1000
    base = 222000

    # ---- LEARN (curiosity investigation) + the convergence staircase ----------
    agent = Percell()
    probe = make_probe_set(np.random.default_rng(base + 1), 20)
    curve = investigate(agent, np.random.default_rng(base + 2), probe_scenes=probe)

    # ---- the aggregate-count null: trained on the SAME investigation budget ----
    agg = AggregateCountNull(seed=base + 3)
    trng = np.random.default_rng(base + 2)  # same stream shape as investigate probing
    # investigate observed each action ~2x; give the null the same per-action budget.
    for a in ACTIONS:
        for _ in range(2):
            sc = make_scene(trng); cur = scene_grid(sc); nxt = world_next(sc, cur, a)
            agg.observe(a, cur, nxt)

    # ---- EVALUATE on held-out triples -----------------------------------------
    erng = np.random.default_rng(base + 100)
    arms = {"learned": {}, "persistence": {}, "aggregate": {}}
    for k in arms:
        arms[k] = {m: [] for m in ("f1_strict", "f1_loc", "val_acc", "exact", "raw_acc")}
    for _ in range(N_EVAL):
        sc = make_scene(erng)
        cur = scene_grid(sc)
        for a in ACTIONS:
            true = world_next(sc, cur, a)
            preds = {"learned": agent.predict_next(cur, a),
                     "persistence": cur.copy(),
                     "aggregate": agg.predict(cur, a)}
            for arm, p in preds.items():
                sc_p = score_prediction(cur, true, p)
                for m in arms[arm]:
                    arms[arm][m].append(sc_p[m])

    # ---- bootstrap CIs ---------------------------------------------------------
    ci = {}
    for arm in arms:
        ci[arm] = {m: bootstrap_ci(arms[arm][m], BOOT, seed=base + 200)
                   for m in arms[arm]}

    def sep(metric):
        lo = ci["learned"][metric]["lo"]
        return {
            "learned": ci["learned"][metric],
            "persistence": ci["persistence"][metric],
            "aggregate": ci["aggregate"][metric],
            "CI_sep_above_persistence": lo > ci["persistence"][metric]["hi"],
            "CI_sep_above_aggregate": lo > ci["aggregate"][metric]["hi"],
        }

    model = {a: agent.hypothesis(a) for a in ACTIONS}
    audit = source_audit()

    result = {
        "rung": 222000,
        "commitment": "the per-cell model predicts WHICH cells change and to WHAT "
                      "value; scored on the CHANGE-SET, never raw accuracy.",
        "n_eval_scenes": N_EVAL, "n_triples": N_EVAL * len(ACTIONS), "bootstrap": BOOT,
        "G_percell_teeth_strict_f1": sep("f1_strict"),
        "G_percell_teeth_location_f1": sep("f1_loc"),
        "G_percell_teeth_value_acc": sep("val_acc"),
        "exact_frame_match_rate": {a: ci[a]["exact"] for a in ci},
        "raw_accuracy_THE_TRAP": {a: ci[a]["raw_acc"] for a in ci},
        "G_mechanic_discovered": {
            "confirmed": agent.confirmed_count(), "n_actions": len(ACTIONS),
            "discovered_hypotheses": model,
        },
        "G_convergence_surprise_curve": [round(x, 4) for x in curve],
        "G_graph_native_source_audit": audit,
    }
    out = _ROOT / "results" / "arc_ls20_percell_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    # ---- console summary -------------------------------------------------------
    print("=== RUNG 222000 — PER-CELL live mechanic, OFFLINE powered teeth ===")
    print(f"n_triples = {N_EVAL * len(ACTIONS)} (held-out), bootstrap = {BOOT}\n")
    print("HEADLINE — CHANGE-SET metrics (learned vs BOTH nulls), 95% bootstrap CI:")
    for label, metric in (("strict changed-cell F1", "f1_strict"),
                          ("location F1", "f1_loc"), ("value-accuracy", "val_acc")):
        s = sep(metric)
        print(f"\n  {label}:")
        for arm in ("learned", "persistence", "aggregate"):
            c = s[arm]
            print(f"    {arm:12s} mean={c['mean']:.4f}  CI[{c['lo']:.4f}, {c['hi']:.4f}]")
        print(f"    CI-separated above persistence: {s['CI_sep_above_persistence']}  "
              f"above aggregate: {s['CI_sep_above_aggregate']}")
    rt = result["raw_accuracy_THE_TRAP"]
    print(f"\nRAW per-cell accuracy (THE TRAP — never the gate): "
          f"learned={rt['learned']['mean']:.5f} persistence={rt['persistence']['mean']:.5f} "
          f"aggregate={rt['aggregate']['mean']:.5f}")
    print(f"  -> persistence aces RAW accuracy but scores {ci['persistence']['f1_strict']['mean']:.3f} "
          f"strict-F1: the trap is real.")
    print(f"\nG-mechanic-discovered: confirmed {agent.confirmed_count()}/{len(ACTIONS)} "
          f"action->Transform hypotheses (NONE given):")
    for a in ACTIONS:
        h = model[a]
        print(f"    {a:11s} -> key={h['key']:22s} region_colour={h['region_colour']} conf={h['conf']:.0f}")
    print(f"\nG-convergence surprise staircase: {[round(x,2) for x in curve]}")
    print(f"\nG-graph-native source_audit PASS={audit['PASS']}: "
          f"agent-prediction fns referencing ground-truth tables = "
          f"{audit['agent_prediction_fns_referencing_ground_truth_tables']} (MUST be []); "
          f"world physics uses tables by design = {audit['world_physics_uses_tables_by_design']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
