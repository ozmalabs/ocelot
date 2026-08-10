#!/usr/bin/env python3
"""jabberwock_omniglot_motor_intent.py — Omniglot 20-way test for the generic motor-intent layer.

Lake protocol (same shape as jabberwock_omniglot_dynamic_quantization.py TEST phase):
  • held-out strokes_evaluation alphabets (never LEARN)
  • one fixed 20-exemplar support set per alphabet (drawer ex)
  • 20 query trials (one per class, drawer q != ex)
  • within-alphabet, cross-drawer classification

TWO ARMS (mechanical held-Term verdicts only):
  (i)  INTENT — realize noise → inverse-model plan → compare extracted intents
  (ii) ARRANGEMENT — raw canvas outcome compare (the failure mode motor intent supersedes)

No stroke-codebook LEARN required: motor intent reads plan topology directly from pen
trajectories via held StrokeQuantize + TransformDecode (noise realization path).

Run:
  PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_omniglot_motor_intent.py
  PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_omniglot_motor_intent.py --quick
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from domains import motor_intent as mi
from domains import omniglot_world as ow
from domains.abs_read import _argmin_pairs_term
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

SEP = "=" * 88
WAY = 20
SEED = 42
EVAL_ALPHABETS = ["Angelic", "Atemayar_Qelisayer", "Atlantean", "Aurek-Besh"]
EPISODES_PER_ALPHABET = 20
RESULT_PATH = os.path.join(ROOT, "results", "omniglot_motor_intent.json")


def boot():
    s, ag = boot_core()
    native = s._inner
    native.load_seed_manifest(manifest_for("motor_intent_core"), ag)
    return s, ag, native


def _strokes_from_path(path: str) -> list[list]:
    return [st.tolist() for st in ow.load_strokes(path, drop_degenerate=True)]


def _classify_intent(native, query_strokes: list, exemplar_strokes_list: list[list]) -> int:
    """Held Argmin over per-candidate extracted-intent DtwTo scores."""
    if not query_strokes:
        return -1
    query_plan = mi.extract_motor_plan(native, query_strokes)["plan_segments"]
    pairs = []
    for ci, ex_strokes in enumerate(exemplar_strokes_list):
        if len(ex_strokes) != len(query_strokes):
            pairs.append((1e9, ci))
            continue
        ex_plan = mi.extract_motor_plan(native, ex_strokes)["plan_segments"]
        term = mi.intent_match_term(query_plan, ex_plan, native=native)
        if term is None:
            pairs.append((1e9, ci))
        else:
            pairs.append((float(native.evaluate(term, {}) or 1e9), ci))
    w = native.evaluate(_argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


def _classify_arrangement(native, query_strokes: list, exemplar_strokes_list: list[list]) -> int:
    """Held Argmin over arrangement (raw canvas) scores — outcome-matching baseline."""
    cand_segs = []
    for ex_strokes in exemplar_strokes_list:
        if len(ex_strokes) != len(query_strokes):
            cand_segs.append([])
        else:
            cand_segs.append(mi.extract_plan_segments(native, ex_strokes))
    res = mi.motor_intent_verdict(native, query_strokes, cand_segs, mode="arrangement")
    return int(res["winner"]) if res.get("winner") is not None else -1


def run_omniglot_test(native, alphabets: list[str], way: int, episodes_per: int,
                      rng: np.random.Generator) -> dict:
    preds_intent, preds_arr, trues = [], [], []
    per_alph_intent, per_alph_arr = {}, {}
    skipped = []
    n_stroke_mismatch = 0
    n_episodes = 0

    for alph in alphabets:
        chars = sorted(ow.characters(alph, "evaluation"))
        if len(chars) < way:
            skipped.append((alph, f"only {len(chars)} characters, need {way}"))
            continue
        chars = chars[:way]
        drawer_files = [ow.drawings(cd) for cd in chars]
        n_drawers = min(len(fl) for fl in drawer_files)
        ex_drawer = int(rng.integers(n_drawers))
        exemplar_strokes = [_strokes_from_path(drawer_files[ci][ex_drawer]) for ci in range(way)]

        pi, pa, pt = [], [], []
        for qi in range(min(episodes_per, way)):
            q_drawer = int(rng.integers(n_drawers))
            while q_drawer == ex_drawer:
                q_drawer = int(rng.integers(n_drawers))
            query_strokes = _strokes_from_path(drawer_files[qi][q_drawer])
            if len(query_strokes) != len(exemplar_strokes[qi]):
                n_stroke_mismatch += 1
            pred_i = _classify_intent(native, query_strokes, exemplar_strokes)
            pred_a = _classify_arrangement(native, query_strokes, exemplar_strokes)
            pi.append(pred_i)
            pa.append(pred_a)
            pt.append(qi)
            preds_intent.append(pred_i)
            preds_arr.append(pred_a)
            trues.append(qi)
            n_episodes += 1

        per_alph_intent[alph] = float(np.mean([a == b for a, b in zip(pi, pt)])) if pt else 0.0
        per_alph_arr[alph] = float(np.mean([a == b for a, b in zip(pa, pt)])) if pt else 0.0

    def _acc(preds, labels):
        return float(np.mean([a == b for a, b in zip(preds, labels)])) if labels else 0.0

    shuf = list(trues)
    rng.shuffle(shuf)

    return {
        "n_episodes": n_episodes,
        "n_stroke_count_mismatch_query_vs_own_exemplar": n_stroke_mismatch,
        "skipped_alphabets": skipped,
        "per_alph_intent": per_alph_intent,
        "per_alph_arrangement": per_alph_arr,
        "acc_intent": _acc(preds_intent, trues),
        "acc_arrangement": _acc(preds_arr, trues),
        "acc_intent_shuffled": _acc(preds_intent, shuf),
        "acc_arrangement_shuffled": _acc(preds_arr, shuf),
        "chance": 1.0 / way,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="1 alphabet, 10 episodes (smoke)")
    ap.add_argument("--alphabets", nargs="*", default=None)
    args = ap.parse_args()

    if not mi.stroke_quantize_live():
        print("SKIP: StrokeQuantize not built — run maturin develop in runners/dsl")
        return 0

    if not ow.have_data("evaluation"):
        print(f"WALL: Omniglot evaluation data not found under {ow.DATA}")
        return 1

    alphabets = args.alphabets or (EVAL_ALPHABETS[:1] if args.quick else EVAL_ALPHABETS)
    episodes = 10 if args.quick else EPISODES_PER_ALPHABET

    print(SEP)
    print("OMNIGLOT MOTOR-INTENT GATE — realize noise → extract intent → 20-way classify")
    print(f"  alphabets: {alphabets}")
    print(f"  way={WAY}  episodes/alphabet={episodes}  seed={SEED}")
    print(SEP)

    t0 = time.time()
    s, ag, native = boot()
    rng = np.random.default_rng(SEED)
    rep = run_omniglot_test(native, alphabets, WAY, episodes, rng)
    rep["elapsed_s"] = round(time.time() - t0, 2)
    rep["alphabets"] = alphabets
    rep["episodes_per_alphabet"] = episodes
    rep["delta_intent_minus_arrangement_pp"] = 100 * (rep["acc_intent"] - rep["acc_arrangement"])

    chance_pct = 100 * rep["chance"]
    print(f"\n  episodes: {rep['n_episodes']}  elapsed: {rep['elapsed_s']}s")
    if rep["skipped_alphabets"]:
        for a, r in rep["skipped_alphabets"]:
            print(f"  SKIPPED {a!r}: {r}")

    print(f"\n  per-alphabet accuracy (INTENT | ARRANGEMENT):")
    for a in rep["per_alph_intent"]:
        print(f"    {a:>24}: {100*rep['per_alph_intent'][a]:5.1f}%  |  "
              f"{100*rep['per_alph_arrangement'][a]:5.1f}%")

    print(f"\n  ONE-SHOT ACCURACY, INTENT (extracted motor plan):     "
          f"{100*rep['acc_intent']:5.1f}%  (chance {chance_pct:.1f}%, "
          f"shuffled {100*rep['acc_intent_shuffled']:5.1f}%)")
    print(f"  ONE-SHOT ACCURACY, ARRANGEMENT (raw canvas baseline): "
          f"{100*rep['acc_arrangement']:5.1f}%  (chance {chance_pct:.1f}%, "
          f"shuffled {100*rep['acc_arrangement_shuffled']:5.1f}%)")
    print(f"  DELTA (intent - arrangement): {rep['delta_intent_minus_arrangement_pp']:+5.1f}pp")

    rep["pass_intent_above_chance"] = rep["acc_intent"] > rep["chance"]
    rep["pass_intent_beats_shuffle"] = rep["acc_intent_shuffled"] < rep["acc_intent"]
    rep["pass_intent_beats_arrangement"] = rep["acc_intent"] > rep["acc_arrangement"]

    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"\nwrote {RESULT_PATH}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
