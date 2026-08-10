"""arc_ls20_flash_measure — RUNG 223000: the powered OFFLINE gates for FLASH-
ONSET-GUIDED mechanic discovery.

Tests the owner's claim that the avatar<->shape flash is a salience indicator of
the rules. Gates:

  G-flash-detects       -- the flash fires ONSET events (the EXISTING general
                           onset stream), localised, with magnitude_db CI-
                           separated above the distractor-motion onsets; the
                           Argmax-magnitude onset localises to a flash cell in
                           >= 90% of arenas.
  G-sample-efficiency   -- (HEADLINE, FALSIFIABLE) observations to reach held-out
                           change-set strict-F1 >= tau, flash-guided vs 222000's
                           blind mode-colour control, over a CLUTTER SWEEP. The
                           flash advantage is ~0 at n_distractors=0 (anti-rig) and
                           GROWS with clutter; at the headline n_distractors=2 the
                           flash arm's observations-to-converge is CI-separated
                           BELOW blind.
  G-pointer-vs-content  -- a CONFLATE arm (predicts the transient flash as a
                           persistent change) scores WORSE held-out change-set F1
                           than the SEPARATE arm (flash = pointer only) -- the
                           transient/persistent separation is load-bearing.
  source-audit          -- the agent's prediction/transform path reads NO ground-
                           truth _MOVE/_XFORM table; the mechanic is discovered.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_flash_measure.py
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

import worlds.arc_ls20_flash as FL  # noqa: E402
import worlds.arc_ls20_percell as PC  # noqa: E402
from worlds.arc_ls20_flash import (  # noqa: E402
    FlashArena, OnsetEye, FlashAgent, ACTIONS, make_eval_scenes,
    observations_to_converge, held_out_f1,
)
from seed_claim import check_claim  # noqa: E402

N = 20


def bootstrap_ci(xs, reps=1000, seed=0):
    xs = np.asarray(xs, dtype=float)
    if xs.size == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, xs.size, size=(reps, xs.size))
    means = xs[idx].mean(axis=1)
    return {"mean": float(xs.mean()), "lo": float(np.percentile(means, 2.5)),
            "hi": float(np.percentile(means, 97.5)), "n": int(xs.size)}


# ---------------------------------------------------------------------------
# G-flash-detects — the flash is an ONSET event (general stream), localised
# ---------------------------------------------------------------------------
def g_flash_detects(n_arenas=30, steps=8):
    """Over random arenas, collect the onset magnitude_db AT the flash cells vs at
    the distractor-motion cells, and whether the Argmax-magnitude onset localises
    to a flash cell. The REAL GraphEye 2-D onset stream, no bespoke detector."""
    flash_mags, distractor_mags = [], []
    localised = 0
    total = 0
    for a in range(n_arenas):
        rng = np.random.default_rng(7000 + a)
        arena = FlashArena(rng, n=N, n_distractors=2)
        eye = OnsetEye(N)
        eye.adapt(arena.grid())
        for k in range(steps):
            act = ACTIONS[int(rng.integers(0, len(ACTIONS)))]
            prev, nxt, flash_cells, centroid = arena.step(act)
            events = eye.onset_on_transition(prev, nxt, flash_cells)
            if not events:
                continue
            fset = set(flash_cells)
            fmag = [m for (r, c, m) in events if (r, c) in fset]
            dmag = [m for (r, c, m) in events if (r, c) not in fset]
            if fmag:
                flash_mags.append(float(np.mean(fmag)))
            if dmag:
                distractor_mags.append(float(np.mean(dmag)))
            events.sort(key=lambda e: -e[2])
            top = events[0]
            localised += int((top[0], top[1]) in fset)
            total += 1
        eye.stop()
    fci = bootstrap_ci(flash_mags, seed=1)
    dci = bootstrap_ci(distractor_mags, seed=2)
    loc_rate = localised / total if total else 0.0
    return {
        "flash_onset_magnitude_db": fci,
        "distractor_motion_onset_magnitude_db": dci,
        "CI_separated_flash_above_distractor": (
            fci["lo"] is not None and dci["hi"] is not None and fci["lo"] > dci["hi"]),
        "argmax_onset_localises_to_flash_rate": loc_rate,
        "localisation_ge_90pct": loc_rate >= 0.90,
        "n_onset_frames": total,
    }


# ---------------------------------------------------------------------------
# G-sample-efficiency — the HEADLINE (clutter sweep, powered)
# ---------------------------------------------------------------------------
def g_sample_efficiency(n_seeds=24, budget=500, tau=0.9, clutter=(0, 1, 2, 3),
                        eval_scenes_n=10):
    sweep = {}
    for nd in clutter:
        ev = make_eval_scenes(np.random.default_rng(9000 + nd), eval_scenes_n, N, nd)
        blind_obs, flash_obs = [], []
        blind_conv, flash_conv = 0, 0
        for seed in range(n_seeds):
            rb = observations_to_converge("blind", 100 * nd + seed, n=N,
                                          n_distractors=nd, tau=tau, budget=budget,
                                          eval_scenes=ev)
            rf = observations_to_converge("flash_separate", 100 * nd + seed, n=N,
                                          n_distractors=nd, tau=tau, budget=budget,
                                          eval_scenes=ev)
            blind_obs.append(rb["observations"]); blind_conv += int(rb["converged"])
            flash_obs.append(rf["observations"]); flash_conv += int(rf["converged"])
        bci = bootstrap_ci(blind_obs, seed=3)
        fci = bootstrap_ci(flash_obs, seed=4)
        sweep[nd] = {
            "blind_observations_to_converge": bci,
            "flash_observations_to_converge": fci,
            "blind_convergence_rate": blind_conv / n_seeds,
            "flash_convergence_rate": flash_conv / n_seeds,
            # censored-at-budget => blind's mean is a conservative LOWER bound on
            # its true cost, so CI-separation below it is conservative.
            "flash_CI_separated_below_blind": (
                fci["hi"] is not None and bci["lo"] is not None and fci["hi"] < bci["lo"]),
            "flash_advantage_obs": (None if bci["mean"] is None or fci["mean"] is None
                                    else bci["mean"] - fci["mean"]),
        }
    return sweep


# ---------------------------------------------------------------------------
# G-pointer-vs-content — conflating the pointer with content scores worse
# ---------------------------------------------------------------------------
def g_pointer_vs_content(n_seeds=16, obs_budget=60, n_distractors=2, eval_scenes_n=10):
    """Run the SEPARATE and CONFLATE flash arms for a FIXED observation budget on
    the SAME arenas (identical attention + discovery), then compare held-out
    change-set F1. Conflate additionally predicts the transient flash as a
    persistent change -> false-positive changed cells -> lower F1."""
    ev = make_eval_scenes(np.random.default_rng(9500), eval_scenes_n, N, n_distractors)
    sep_f1, conf_f1 = [], []
    for seed in range(n_seeds):
        for arm, bucket in (("flash_separate", sep_f1), ("flash_conflate", conf_f1)):
            rng = np.random.default_rng(4200 + seed)
            agent = FlashAgent(arm=arm)
            arena = FlashArena(rng, n=N, n_distractors=n_distractors)
            eye = OnsetEye(N); eye.adapt(arena.grid())
            for t in range(1, obs_budget + 1):
                act = agent.next_probe() or ACTIONS[t % len(ACTIONS)]
                prev, nxt, fc, ctr = arena.step(act)
                events = eye.onset_on_transition(prev, nxt, fc)
                ch = agent.attend_flash(events)
                agent.observe(act, prev, nxt, ch)
            eye.stop()
            bucket.append(held_out_f1(agent, ev))
    sci = bootstrap_ci(sep_f1, seed=5)
    cci = bootstrap_ci(conf_f1, seed=6)
    return {
        "separate_changeset_f1": sci,
        "conflate_changeset_f1": cci,
        "separate_CI_separated_above_conflate": (
            sci["lo"] is not None and cci["hi"] is not None and sci["lo"] > cci["hi"]),
        "obs_budget": obs_budget,
    }


# ---------------------------------------------------------------------------
# source-audit — the mechanic is discovered, never table-read
# ---------------------------------------------------------------------------
def source_audit():
    agent_fns = ["discover_blind", "discover_flash_separate", "_window_region_spec",
                 "_spec_from_objs", "predict_conflate"]
    banned = ["_MOVE", "_XFORM"]
    hits = {}
    for name in agent_fns:
        fn = getattr(FL, name)
        hits[name] = [b for b in banned if b in inspect.getsource(fn)]
    agent_uses = sorted({b for v in hits.values() for b in v})
    # the arena (WORLD PHYSICS) is allowed to read the tables, exactly like 222000.
    physics_uses = [b for b in banned if b in inspect.getsource(FL.FlashArena.step)]
    return {
        "agent_prediction_fns_referencing_ground_truth_tables": agent_uses,  # MUST be []
        "world_physics_uses_tables_by_design": physics_uses,
        "per_fn": hits,
        "PASS": agent_uses == [],
    }


def main():
    base = 223000
    ok, claim = check_claim(base, base + 999)
    print(claim.splitlines()[0])

    print("\n[1/4] G-flash-detects (real onset stream) ...")
    fd = g_flash_detects()
    print("[2/4] G-sample-efficiency (clutter sweep, powered) ...")
    se = g_sample_efficiency()
    print("[3/4] G-pointer-vs-content ...")
    pc = g_pointer_vs_content()
    print("[4/4] source-audit ...")
    audit = source_audit()

    result = {
        "rung": 223000,
        "claim_under_test": "the avatar<->shape flash is a salience indicator of "
                            "the rules: it LOCALISES + TIMES the mechanic.",
        "seed_claim_first_line": claim.splitlines()[0],
        "grid": N,
        "G_flash_detects": fd,
        "G_sample_efficiency_clutter_sweep": {str(k): v for k, v in se.items()},
        "G_pointer_vs_content": pc,
        "source_audit": audit,
        "anti_circularity": (
            "the flash is a LUMINANCE-ONLY transient (never in the colour grid), "
            "identical for all 10 actions -> it carries WHERE/WHEN, never WHAT; both "
            "arms discover the transform via the IDENTICAL 222000 sd-loop; blind "
            "ALSO converges (sample-efficiency, not can-converge); the flash "
            "advantage is ~0 at n_distractors=0 (anti-rig)."),
    }
    out = _ROOT / "results" / "arc_ls20_flash_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    # ---- console summary ----
    print("\n=== RUNG 223000 — FLASH-ONSET-GUIDED discovery, OFFLINE powered ===\n")
    print("G-flash-detects (the flash IS an onset event, general stream):")
    fm = fd["flash_onset_magnitude_db"]; dm = fd["distractor_motion_onset_magnitude_db"]
    print(f"  flash onset dB      mean={fm['mean']:.1f} CI[{fm['lo']:.1f},{fm['hi']:.1f}] (n={fm['n']})")
    print(f"  distractor onset dB mean={dm['mean']:.1f} CI[{dm['lo']:.1f},{dm['hi']:.1f}] (n={dm['n']})")
    print(f"  flash CI-separated ABOVE distractor: {fd['CI_separated_flash_above_distractor']}")
    print(f"  Argmax onset localises to flash: {fd['argmax_onset_localises_to_flash_rate']:.1%} "
          f"(>=90%: {fd['localisation_ge_90pct']})")

    print("\nG-SAMPLE-EFFICIENCY (HEADLINE) — observations to change-set F1>=0.9, "
          "flash vs blind:")
    print("  clutter | blind obs (conv%) | flash obs (conv%) | flash CI-sep below blind")
    for nd in sorted(se):
        s = se[nd]
        b = s["blind_observations_to_converge"]; f = s["flash_observations_to_converge"]
        print(f"    nd={nd}  | {b['mean']:6.1f} [{b['lo']:.0f},{b['hi']:.0f}] "
              f"({s['blind_convergence_rate']:.0%}) | {f['mean']:6.1f} [{f['lo']:.0f},{f['hi']:.0f}] "
              f"({s['flash_convergence_rate']:.0%}) | {s['flash_CI_separated_below_blind']}")
    print("  (nd=0 = anti-rig null: flash should NOT beat blind on a clean scene.)")

    print("\nG-pointer-vs-content — conflating the transient flash with content:")
    print(f"  SEPARATE F1 mean={pc['separate_changeset_f1']['mean']:.2f} "
          f"CI[{pc['separate_changeset_f1']['lo']:.2f},{pc['separate_changeset_f1']['hi']:.2f}]")
    print(f"  CONFLATE F1 mean={pc['conflate_changeset_f1']['mean']:.2f} "
          f"CI[{pc['conflate_changeset_f1']['lo']:.2f},{pc['conflate_changeset_f1']['hi']:.2f}]")
    print(f"  separate CI-separated ABOVE conflate: {pc['separate_CI_separated_above_conflate']}")

    print(f"\nsource-audit PASS={audit['PASS']}: agent-prediction fns referencing "
          f"ground-truth tables={audit['agent_prediction_fns_referencing_ground_truth_tables']} "
          f"(MUST be []); world physics uses tables by design="
          f"{audit['world_physics_uses_tables_by_design']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
