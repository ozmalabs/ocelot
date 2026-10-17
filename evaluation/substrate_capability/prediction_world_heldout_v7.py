#!/usr/bin/env python3
"""Held-out levels over many draws for loop 1.9.0 (2026-10-10): predicates the
agent authors itself, and an escalating curriculum. Pre-registered in
docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_V8_20261010.md.

Arms (each from the same state per seed base, forks of one trained agent per
variant):
  on_trained            the 5-level curriculum (60 episodes), predicate
                        authoring on, then the held-out level
  on_trained_noatoms    the same with atom_authoring off throughout
  on_trained_escalated  the curriculum, then an escalation phase: ESC_LEVELS
                        further levels from the same physics family (seeds
                        10**8 + seed_base, a range no evaluation uses),
                        ordered by how badly the newborn model predicts them
                        (easiest first), with level_patience episodes at each
                        before the agent's own rule moves it on; then the level
  on_naive              a newborn
Per run: up to BUDGET episodes at the level (robust mastery stops it); final
surprise on fresh episodes, retention harm on curriculum levels 1-5,
experiments.

Usage: <this> <draw_hash> <first_draw> <end_draw>
Writes evaluation/reports/prediction_world_heldout_v7_<hash[:8]>_d<first>-<end>_20261010.json.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "evaluation/substrate_capability")]

import prediction_world_heldout_v6 as base  # noqa: E402  (fork, settle, _at_level, retention harm)

CURRICULUM_EPISODES = 60
BUDGET = 30
K_LEVELS = 8
SEED_BASES = (1000, 2024, 5000, 9000)
ARMS = ("on_trained", "on_trained_noatoms", "on_trained_escalated", "on_naive")
ESC_POOL = 16
ESC_LEVELS = 8
ESC_PATIENCE = 12
_TRAINED = {}


def escalation_levels(pw, seed_base):
    """ESC_LEVELS levels, ids 6.., from the family, easiest first by the newborn
    (velocity) model's mean surprise on 3 sample episodes."""
    pool = pw.heldout_levels(10**8 + seed_base, ESC_POOL, first_id=6000)
    for lv, spec in pool.items():
        pw.LEVELS[lv] = spec
    score = {lv: sum(pw.replay(pw.simulate(lv, 10**6 + s), 1) for s in range(3)) / 3 for lv in pool}
    order = sorted(pool, key=lambda lv: (score[lv], lv))
    # the hardest ESC_LEVELS of the easier half onward: spread across difficulty, easiest first
    chosen = sorted(order[::max(1, ESC_POOL // ESC_LEVELS)][:ESC_LEVELS], key=lambda lv: (score[lv], lv))
    return {6 + i: pool[lv] for i, lv in enumerate(chosen)}


def _train(pw, seed_base, variant):
    a = base._newborn()
    S, I = a.s, a.inner
    pol = S.nodes("PredictionPolicy")[0]
    if variant == "noatoms":
        I.set_attr(pol, "atom_authoring", 0)
    for i in range(CURRICULUM_EPISODES):
        pw.run_episode(a, seed=seed_base + i)
        base._settle(pw, a)
    if variant == "escalated":
        esc = escalation_levels(pw, seed_base)
        for lv, spec in esc.items():
            pw.LEVELS[lv] = spec
        cur = S.nodes("PredictionCurriculum")[0]
        I.set_attr(cur, "max_level", 5 + ESC_LEVELS)
        I.set_attr(cur, "current_level", 6)
        I.set_attr(pol, "level_patience", ESC_PATIENCE)
        for i in range(ESC_LEVELS * ESC_PATIENCE):
            pw.run_episode(a, seed=seed_base + 200000 + i)
            base._settle(pw, a)
        I.set_attr(pol, "level_patience", 0)
    return a


def _trained(pw, seed_base, variant):
    key = (seed_base, variant)
    if key not in _TRAINED:
        _TRAINED[key] = _train(pw, seed_base, variant)
    return base._Fork(_TRAINED[key])


def job(args):
    seed_base, arm, level, spec, draw = args
    from domains import prediction_world as pw
    pw.LEVELS[level] = spec
    t0 = time.time()
    if arm == "on_naive":
        a = base._newborn()
    else:
        a = _trained(pw, seed_base, {"on_trained": "standard", "on_trained_noatoms": "noatoms",
                                     "on_trained_escalated": "escalated"}[arm])
    r = base._at_level(pw, a, level, seed_base + 100000 + level * 100, BUDGET, retention=(arm != "on_naive"))
    return {"draw": draw, "seed_base": seed_base, "arm": arm, "level": level, **r,
            "elapsed_s": round(time.time() - t0, 1)}


def escalation_report(args):
    """What the escalated agent did in its escalation phase (one per seed base)."""
    seed_base = args
    from domains import prediction_world as pw
    a = _trained(pw, seed_base, "escalated")
    S = a.s
    cur = S.node(S.nodes("PredictionCurriculum")[0])["attrs"]
    eps = [S.node(e)["attrs"] for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"]["level"] >= 6]
    per = {}
    for e in eps:
        per.setdefault(e["level"], []).append(round(e["mean_surprise"], 3))
    return {"seed_base": seed_base, "mastered_through": cur.get("mastered_through"), "moved_on": cur.get("moved_on"),
            "final_level": cur.get("current_level"), "adoptions": len(S.nodes("Adoption")),
            "model": S.node(S.nodes("Predictor")[0])["attrs"].get("model"), "curves": per}


def main():
    draw_hash, d0, d1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    from domains import prediction_world as pw
    b = int(draw_hash[:8], 16)
    draws = {d: pw.heldout_levels(b + 7919 * d, K_LEVELS, first_id=101 + K_LEVELS * d) for d in range(d0, d1)}
    assert all(b + 7919 * d != 10**8 + sb for d in range(d0, d1) for sb in SEED_BASES)
    jobs = [(sb, arm, lv, spec, d) for sb in SEED_BASES for d, lv_specs in draws.items()
            for lv, spec in lv_specs.items() for arm in ARMS]
    with ProcessPoolExecutor(max_workers=int(os.environ.get("PW_WORKERS", "14"))) as ex:
        esc = list(ex.map(escalation_report, SEED_BASES))
        rows = list(ex.map(job, jobs, chunksize=4))
    summary = {}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm]
        summary[arm] = {"runs": len(r), "mastered": sum(x["mastered"] for x in r),
                        "mean_final_surprise": round(sum(x["final_surprise"] for x in r) / len(r), 4),
                        "mean_retention_harm": round(sum(x["retention_harm"] for x in r) / len(r), 4),
                        "mean_experiments": round(sum(x["experiments"] for x in r) / len(r), 2),
                        "adoptions": sum(x["adoptions"] for x in r)}
    rep = {"draw_hash": draw_hash, "draws": draws, "seed_bases": SEED_BASES, "budget": BUDGET,
           "loop_version": json.loads((ROOT / "seeds/prediction_self_improvement.json").read_text())["version"],
           "escalation": esc, "summary": summary, "rows": rows}
    out = ROOT / f"evaluation/reports/prediction_world_heldout_v7_{draw_hash[:8]}_d{d0}-{d1}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(esc, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
