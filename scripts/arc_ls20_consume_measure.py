"""arc_ls20_consume_measure — RUNG 225000: the POWERED OFFLINE ablation (the gated
deliverable). Folds 223000's flash consume-marking onto 224000's tracker.

Pre-registered in LS20_CONSUME_PREREG.md (committed ALONE). Runs the paired ablation
over many seeds (all arms see IDENTICAL frames + onsets) and reports:
  * G-trail-closed (HEADLINE): paired mean(flash_F1 - translate_F1) bootstrap CI > 0.
  * G-flash-localises-consume: flash consume-F1 CI vs random-flash consume-F1 CI.
  * Anti-rig null: random-flash does NOT beat 224-alone.
  * Over-predict control: blind_all (mark all vacated) scores below 224-alone.
  * Honesty bound: flash consume PRECISION < 1.0 (not an oracle).
  * Source-audit: the agent path references no hardcoded consume table.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_consume import record_episode, eval_arm  # noqa: E402

ARMS = ["translate", "flash", "random", "blind_all"]


def _boot_ci(x, reps=1000, seed=0):
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return None, None, None
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, x.size, size=(reps, x.size))].mean(axis=1)
    return float(x.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _paired_ci(a, b, reps=1000, seed=0):
    """Bootstrap CI of the PAIRED difference mean(a - b) (a, b matched by index)."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    d = a - b
    if d.size == 0:
        return None, None, None
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, d.size, size=(reps, d.size))].mean(axis=1)
    return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _source_audit():
    """The agent's discovery/prediction path must reference no ground-truth consume
    table. The arena (WORLD PHYSICS) legitimately writes the trail; the AGENT
    (ConsumeTracker predict/observe + the seed rules) must not read a consume map."""
    src = (_ROOT / "worlds" / "arc_ls20_consume.py").read_text()
    # isolate the agent (ConsumeTracker) portion from the arena (ConsumeArena)
    agent_start = src.index("class ConsumeTracker")
    agent_src = src[agent_start:]
    # a hardcoded consume table would look like a dict literal mapping actions/cells
    # to consumed values; the trail colour TRAIL is only READ back from observation.
    hits = re.findall(r"consumed_cells\s*=\s*\[|_CONSUME_TABLE|consume_map\s*=", agent_src)
    # TRAIL is referenced only as the palette constant; the agent never assigns it.
    trail_assign = re.findall(r"g\[[^\]]+\]\s*=\s*TRAIL", agent_src)
    return {"agent_hardcoded_consume_hits": hits, "agent_writes_trail_value": trail_assign,
            "pass": (len(hits) == 0 and len(trail_assign) == 0)}


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    n_distractors = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    # matched (per scored step) F1 arrays, one per arm; consume-F1 + precision arrays
    f1 = {a: [] for a in ARMS}
    consume_f1 = {a: [] for a in ARMS}
    consume_prec = {a: [] for a in ARMS}
    for s in range(n_seeds):
        rec = record_episode(s, steps=steps, n_distractors=n_distractors)
        per = {a: eval_arm(a, rec, seed=s) for a in ARMS}
        # all arms score the same steps (identical observe) -> matched by index
        m = min(len(per[a][0]) for a in ARMS)
        for a in ARMS:
            f1s, prs = per[a]
            f1[a].extend(f1s[:m])
            consume_f1[a].extend([p[2] for p in prs[:m]])
            consume_prec[a].extend([p[0] for p in prs[:m]])
        print(f"seed {s}: n_scored={m} "
              f"transl={np.mean(per['translate'][0][:m]):.3f} "
              f"flash={np.mean(per['flash'][0][:m]):.3f}", flush=True)

    per_arm = {a: dict(zip(("mean", "lo", "hi"), _boot_ci(f1[a], seed=1))) for a in ARMS}
    flash_vs_transl = dict(zip(("mean", "lo", "hi"), _paired_ci(f1["flash"], f1["translate"], seed=2)))
    random_vs_transl = dict(zip(("mean", "lo", "hi"), _paired_ci(f1["random"], f1["translate"], seed=3)))
    cf_flash = dict(zip(("mean", "lo", "hi"), _boot_ci(consume_f1["flash"], seed=4)))
    cf_random = dict(zip(("mean", "lo", "hi"), _boot_ci(consume_f1["random"], seed=5)))
    flash_prec_mean = float(np.mean(consume_prec["flash"])) if consume_prec["flash"] else None

    g_trail_closed = flash_vs_transl["lo"] is not None and flash_vs_transl["lo"] > 0.0
    g_flash_localises = (cf_flash["lo"] is not None and cf_random["hi"] is not None
                         and cf_flash["lo"] > cf_random["hi"])
    anti_rig_null = random_vs_transl["hi"] is not None and random_vs_transl["hi"] <= flash_vs_transl["lo"] \
        and not (random_vs_transl["lo"] is not None and random_vs_transl["lo"] > 0.0)
    over_predict_punished = per_arm["blind_all"]["mean"] < per_arm["translate"]["mean"]
    honesty_precision_lt1 = flash_prec_mean is not None and flash_prec_mean < 1.0
    audit = _source_audit()

    result = {
        "rung": 225000, "kind": "offline_powered_ablation",
        "n_seeds": n_seeds, "steps": steps, "n_distractors": n_distractors,
        "n_scored_steps": len(f1["translate"]),
        "per_arm_changeset_f1": per_arm,
        "G_trail_closed_HEADLINE": {
            "paired_flash_minus_translate": flash_vs_transl,
            "ci_separated_above_zero": bool(g_trail_closed)},
        "G_flash_localises_consume": {
            "flash_consume_f1": cf_flash, "random_consume_f1": cf_random,
            "ci_separated_above_random": bool(g_flash_localises)},
        "anti_rig_null": {
            "paired_random_minus_translate": random_vs_transl,
            "random_does_not_beat_translate": bool(anti_rig_null)},
        "over_predict_control": {
            "blind_all_mean": per_arm["blind_all"]["mean"],
            "translate_mean": per_arm["translate"]["mean"],
            "over_prediction_punished": bool(over_predict_punished)},
        "honesty_bound": {
            "flash_consume_precision_mean": flash_prec_mean,
            "precision_lt_1_not_oracle": bool(honesty_precision_lt1)},
        "source_audit": audit,
        "all_gates_pass": bool(g_trail_closed and g_flash_localises and anti_rig_null
                               and over_predict_punished and honesty_precision_lt1 and audit["pass"]),
    }
    out = _ROOT / "results" / "arc_ls20_consume_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    print("\n=== RUNG 225000 — FLASH-CONSUME FOLD (offline powered ablation) ===")
    for a in ARMS:
        pa = per_arm[a]
        print(f"  {a:10s} change-set F1 = {pa['mean']:.4f} [{pa['lo']:.4f}, {pa['hi']:.4f}]")
    print(f"\nG-trail-closed (HEADLINE): flash - translate = {flash_vs_transl['mean']:+.4f} "
          f"[{flash_vs_transl['lo']:+.4f}, {flash_vs_transl['hi']:+.4f}]  "
          f"CI>0 = {g_trail_closed}")
    print(f"G-flash-localises: flash consume-F1 {cf_flash['mean']:.3f} [{cf_flash['lo']:.3f},{cf_flash['hi']:.3f}] "
          f"vs random {cf_random['mean']:.3f} [{cf_random['lo']:.3f},{cf_random['hi']:.3f}]  "
          f"sep = {g_flash_localises}")
    print(f"anti-rig null (random-translate): {random_vs_transl['mean']:+.4f} "
          f"[{random_vs_transl['lo']:+.4f}, {random_vs_transl['hi']:+.4f}]  no_win = {anti_rig_null}")
    print(f"over-predict: blind_all {per_arm['blind_all']['mean']:.4f} < translate "
          f"{per_arm['translate']['mean']:.4f} = {over_predict_punished}")
    print(f"honesty: flash consume precision = {flash_prec_mean:.3f} (<1 not oracle = {honesty_precision_lt1})")
    print(f"source-audit pass = {audit['pass']}  {audit}")
    print(f"ALL GATES PASS = {result['all_gates_pass']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
