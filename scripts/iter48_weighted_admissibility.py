"""iter48_weighted_admissibility — the WEIGHTED ADMISSIBILITY RULE GRAPH iteration.

THE USER: "they need weight — almost like a weighted admissibility rule graph."

iter-45 found the wall: the EQUAL symmetric Argmax-of-product over every (cue x order)
node SURFACES which order each channel wants but CANNOT ACT on it — a wrong-order node
is informative-but-WRONG (peaked at the wrong word, NOT near-flat), so it DILUTES.

THE FIX (this iter): weight each (cue x order) node by its MEASURED reliability so the
product can down-weight the unreliable:

    score(w) = PROD_i  P_i(w) ^ weight_i
    weight_i = max(0, (acc_i - chance)/(1 - chance))

acc_i = node i's held-out accuracy MEASURED ON THE TRAIN FOLDS ONLY (inner
leave-one-speaker-out over train speakers — the iter-42 yardstick). chance = DERIVED
1/n_candidates. The map is fixed (no free parameter); the accuracy is a MEASUREMENT,
NOT a swept/fit/gradient weight. iter-45's per-channel best-order diagnostic IS this
reliability map, now ACTED on. A reliable node counts full (P^~1); a wrong-order node
is raised toward P^0 = 1 (flat, cannot dilute). The structure stays binary-admissible;
the RULES carry weights.

EVALUATE: FSDD LOSO, multi-metric, SHUFFLE, per-fold. The decisive read: does weighting
by MEASURED reliability ACT on the per-channel/order selection (down-weighting
wrong-order nodes) and LIFT recognition over the equal combine-all (iter-45) and past
iter-44 0.644? Does it widen the cross-voice margin toward 1-NN's +0.075?

  PYTHONUNBUFFERED=1 python -m scripts.iter48_weighted_admissibility [n_per] [rounds] [n_max] [ridge]
"""
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_whisper import gather, load_wav
import scripts.enriched_hvpt_accept as EH
import domains.many_settings_recognizer as MS
import domains.weighted_admissibility as WA
from domains.order_n_interpolation import (
    word_cloud_models, order_n_channel_likelihood,
)
from scripts.iter45_ordern_interpolation import heldout_combined_ordern
from scripts.many_settings_hvpt_accept import heldout_1nn
from scripts.iter41_speaker_invariance import train_speaker_labels


# ---------------------------------------------------------------------------
# (A) The per-node reliability MEASUREMENT — inner leave-one-speaker-out on the TRAIN
# folds ONLY. For each (order x channel) node, hold out one train speaker, build the
# node's per-word cloud model from the REMAINING train speakers, predict the held-out
# train speaker's tokens with that single node, average over inner folds -> acc.
# weight = (acc - chance)/(1 - chance), clipped at 0. NO test leakage (the outer-held
# voice is absent from train entirely); NO sweep (acc is a measurement, the map fixed).
# ---------------------------------------------------------------------------

def measure_node_reliabilities(vec_train, train_words, train_spk, orders,
                               n_max, ridge, chance):
    """Per (order x channel) node, the inner-LOSO held-out accuracy on TRAIN speakers,
    mapped to the reliability weight. Returns a list of weights in the SAME node order
    the weighted product uses: for ci in channels, for o in orders.

    Reliability is a MEASUREMENT (the same per-node argmax-likelihood the harness
    scores with), computed with the held voice absent (LOSO-clean) and no sweep."""
    spk = np.asarray(train_spk)
    inner_speakers = sorted(set(train_spk))
    cands = sorted(set(train_words))
    weights = []
    accs = []
    n_vec = len(vec_train)
    for ci in range(n_vec):
        Xc = np.asarray(vec_train[ci])
        tw = np.asarray(train_words)
        # Per inner speaker held out, per order, the single-node predictions.
        # We measure each order separately (each is its own node in the product).
        per_order_correct = {o: 0 for o in orders}
        per_order_total = {o: 0 for o in orders}
        for held_spk in inner_speakers:
            tr_mask = (spk != held_spk)
            he_mask = (spk == held_spk)
            if not he_mask.any() or not tr_mask.any():
                continue
            inner_tr_vecs = Xc[tr_mask]
            inner_tr_words = list(tw[tr_mask])
            inner_he_vecs = Xc[he_mask]
            inner_he_words = list(tw[he_mask])
            # one cloud-model set for this channel/inner-fold (all orders share the SVD).
            mans = word_cloud_models(inner_tr_vecs, inner_tr_words, n_max=n_max)
            for o in orders:
                for q, truth in zip(inner_he_vecs, inner_he_words):
                    p = order_n_channel_likelihood(q, mans, cands, o, ridge=ridge)
                    pred = max(p, key=p.get)
                    per_order_correct[o] += int(pred == truth)
                    per_order_total[o] += 1
        for o in orders:
            tot = per_order_total[o]
            acc = per_order_correct[o] / tot if tot else chance
            accs.append((ci, o, acc))
            weights.append(WA.reliability_to_weight(acc, chance))
    return weights, accs


# ---------------------------------------------------------------------------
# (B) The WEIGHTED combine-all over (order x channel) nodes. Identical node layout to
# iter45's heldout_combined_ordern, but the decision Term is the WEIGHTED product
# (Times of Pow(likelihood, weight)) and each node's weight attr is set from the
# measured reliability. weights==1 for all nodes recovers the equal combine-all exactly.
# ---------------------------------------------------------------------------

_WSUB = None
_WTERM = None
_WNCH = None
_WCANDS = None
_WWC: dict = {}


def _w_substrate(candidate_words, n_node):
    global _WSUB, _WTERM, _WNCH, _WCANDS
    cand_key = frozenset(candidate_words)
    if _WSUB is None or _WNCH != n_node or _WCANDS != cand_key:
        from substrate_rs import Substrate
        _WSUB = Substrate()
        _WTERM = MS._Pred(WA.predict_weighted_term(n_node))
        _WNCH = n_node
        _WCANDS = cand_key
        _WWC.clear()
    for w in candidate_words:
        if w not in _WWC:
            c = _WSUB.add_node("Concept", {"name": w})
            _WSUB.set_attr(c, MS.WORD_ATTR, 1.0)
            _WWC[w] = c
    return _WSUB


def heldout_combined_weighted(vec_train, vec_test, train_words, test_words,
                              orders, weights, n_max, ridge=0.0, return_preds=False):
    """Weighted-product recognition over (len(orders) x n_vec) order-N nodes. Same
    nodes as heldout_combined_ordern; the decision Term raises each node's likelihood
    to its measured-reliability weight before the product. weights is a flat list in
    node order [ (ci, o) for ci for o ]. NO fit; the weights were MEASURED on train."""
    n_vec = len(vec_train)
    n_order = len(orders)
    n_node = n_vec * n_order
    assert len(weights) == n_node, (len(weights), n_node)
    candidates = sorted(set(train_words))
    chan_models = [word_cloud_models(vec_train[ci], train_words, n_max=n_max)
                   for ci in range(n_vec)]
    sub = _w_substrate(candidates, n_node)
    # set the (constant-per-fold) per-node weights once.
    for w in candidates:
        for ni in range(n_node):
            sub.set_attr(_WWC[w], WA.weight_attr(ni), float(weights[ni]))
    correct = 0
    preds = []
    n_test = len(test_words)
    for qi in range(n_test):
        ni = 0
        for ci in range(n_vec):
            qv = np.asarray(vec_test[ci][qi])
            for o in orders:
                p = order_n_channel_likelihood(qv, chan_models[ci], candidates,
                                               o, ridge=ridge)
                for w in candidates:
                    sub.set_attr(_WWC[w], MS.channel_attr(ni), p[w])
                ni += 1
        pred = sub.evaluate(_WTERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        preds.append(pw)
        correct += int(pw == test_words[qi])
    if return_preds:
        return preds
    return correct / max(n_test, 1)


# ---------------------------------------------------------------------------
# Score one LOSO fold: WEIGHTED vs EQUAL combine-all (iter-45) vs iter-44 vs 1-NN.
# ---------------------------------------------------------------------------

def score_fold(voice_audio, held_voice, rounds=2, shuffle=False, n_max=2, ridge=0.0):
    from scripts.iter44_interpolation_subnodes import heldout_combined_manifold

    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=shuffle,
                         skip_axs=True)
    tw, hw = fold["train_words"], fold["held_words"]
    spk = train_speaker_labels(voice_audio, held_voice, shuffle=shuffle)
    assert len(spk) == len(tw), (len(spk), len(tw))

    vec_tr = fold["many_train"] + fold["ortho_train"]
    vec_he = fold["many_held"] + fold["ortho_held"]
    names = fold["many_names"] + fold["ortho_names"]
    orders = list(range(n_max + 1))
    cands = sorted(set(tw))
    chance = 1.0 / max(len(cands), 1)

    # (1) MEASURE per-node reliability on TRAIN folds only -> weights (LOSO-clean).
    weights, accs = measure_node_reliabilities(vec_tr, tw, spk, orders,
                                               n_max, ridge, chance)

    # (2) the comparators.
    weighted = heldout_combined_weighted(vec_tr, vec_he, tw, hw, orders, weights,
                                         n_max=n_max, ridge=ridge)
    equal = heldout_combined_ordern(vec_tr, vec_he, tw, hw, orders,
                                    n_max=n_max, ridge=ridge)
    interp44 = heldout_combined_manifold(vec_tr, vec_he, tw, hw, rank=3, ridge=ridge)
    nn = EH.heldout_combined(vec_tr, vec_he, tw, hw)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    # error-overlap weighted vs equal.
    eq_pred = heldout_combined_ordern(vec_tr, vec_he, tw, hw, orders,
                                      n_max=n_max, ridge=ridge, return_preds=True)
    w_pred = heldout_combined_weighted(vec_tr, vec_he, tw, hw, orders, weights,
                                       n_max=n_max, ridge=ridge, return_preds=True)
    eq_err = [i for i, (p, w) in enumerate(zip(eq_pred, hw)) if p != w]
    w_fix = sum(int(w_pred[i] == hw[i]) for i in eq_err)
    w_err = [i for i, (p, w) in enumerate(zip(w_pred, hw)) if p != w]
    eq_fix = sum(int(eq_pred[i] == hw[i]) for i in w_err)

    return {"held_voice": held_voice, "shuffle": shuffle, "n_max": n_max, "ridge": ridge,
            "weighted": weighted, "equal": equal, "interp44": interp44, "nn": nn,
            "frozen": frozen, "orders": orders, "names": names,
            "weights": weights, "accs": accs, "chance": chance,
            "n_held": len(hw), "n_train": len(tw),
            "eq_err": len(eq_err), "weighted_fixes_eq": w_fix,
            "w_err": len(w_err), "eq_fixes_w": eq_fix}


def _report(r):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    print(f"\n--- held-out {r['held_voice']}{tag}  (held {r['n_held']} train "
          f"{r['n_train']}, n_max={r['n_max']} ridge={r['ridge']}) ---", flush=True)
    print(f"  WEIGHTED {r['weighted']:.3f}   EQUAL(iter45) {r['equal']:.3f}   "
          f"iter-44 {r['interp44']:.3f}   1-NN {r['nn']:.3f}   frozen {r['frozen']:.3f}",
          flush=True)
    print(f"    Δ(weighted - equal) {r['weighted']-r['equal']:+.3f}   "
          f"Δ(weighted - iter44) {r['weighted']-r['interp44']:+.3f}   "
          f"Δ(weighted - 1NN) {r['weighted']-r['nn']:+.3f}", flush=True)
    print(f"  error-overlap: weighted fixes {r['weighted_fixes_eq']}/{r['eq_err']} of "
          f"equal's errors;  equal fixes {r['eq_fixes_w']}/{r['w_err']} of weighted's",
          flush=True)
    # weight summary per order (mean over channels) — does weighting act on order?
    from collections import defaultdict
    by_order = defaultdict(list)
    for (ci, o, acc), wt in zip(r["accs"], r["weights"]):
        by_order[o].append((acc, wt))
    for o in r["orders"]:
        accs = [a for a, _ in by_order[o]]
        wts = [w for _, w in by_order[o]]
        print(f"    order-{o}: measured acc mean {np.mean(accs):.3f}  "
              f"weight mean {np.mean(wts):.3f}  (chance {r['chance']:.3f})", flush=True)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    ridge = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-48 — WEIGHTED ADMISSIBILITY RULE GRAPH", flush=True)
    print("  score(w) = PROD_i P_i(w)^weight_i ; weight_i = (acc_i - chance)/(1-chance)", flush=True)
    print("  acc_i = node's inner-LOSO accuracy on TRAIN folds (MEASURED, not searched)", flush=True)
    print(f"  orders 0..{n_max} per channel, ridge={ridge}", flush=True)
    print("=" * 72, flush=True)

    items = gather(n_per_class_per_speaker=n_per)
    voice_audio = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)

    real, shuf = [], []
    for held in speakers:
        r = score_fold(voice_audio, held, rounds, shuffle=False, n_max=n_max, ridge=ridge)
        _report(r); real.append(r)
        sr = score_fold(voice_audio, held, rounds, shuffle=True, n_max=n_max, ridge=ridge)
        _report(sr); shuf.append(sr)

    def mean(rs, key):
        return float(np.mean([x[key] for x in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over 6 held-out FSDD speakers, chance 0.100)", flush=True)
    print("=" * 72, flush=True)
    w = mean(real, "weighted"); eq = mean(real, "equal")
    i44 = mean(real, "interp44"); nn = mean(real, "nn"); fr = mean(real, "frozen")
    sw = mean(shuf, "weighted"); seq = mean(shuf, "equal")
    si44 = mean(shuf, "interp44"); snn = mean(shuf, "nn")

    print(f"  WEIGHTED admissibility graph                {w:.3f}", flush=True)
    print(f"  EQUAL combine-all (iter-45)                 {eq:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1)             {i44:.3f}", flush=True)
    print(f"  1-NN graph (order-0 point estimate)         {nn:.3f}", flush=True)
    print(f"  frozen                                      {fr:.3f}", flush=True)
    print(f"  *** weighted vs EQUAL    Δ {w-eq:+.3f}  "
          f"=> {'WEIGHTING LIFTS over equal combine-all' if w > eq else 'NO LIFT' if w==eq else 'HURTS'}",
          flush=True)
    print(f"  *** weighted vs iter-44  Δ {w-i44:+.3f}  "
          f"=> {'beats iter-44 0.644' if w > i44 else 'no gain over iter-44' if w==i44 else 'BELOW iter-44'}",
          flush=True)
    print(f"  *** weighted vs 1-NN     Δ {w-nn:+.3f}", flush=True)

    print("\n  SHUFFLE control (voice partition scrambled):", flush=True)
    print(f"    WEIGHTED real {w:.3f}  shuffle {sw:.3f}  => margin {w-sw:+.3f}  "
          f"({'CLEAN' if w > sw else 'NOT CLEAN'})", flush=True)
    print(f"    EQUAL    real {eq:.3f}  shuffle {seq:.3f}  => margin {eq-seq:+.3f}", flush=True)
    print(f"    iter-44  real {i44:.3f}  shuffle {si44:.3f}  => margin {i44-si44:+.3f}", flush=True)
    print(f"    1-NN     real {nn:.3f}  shuffle {snn:.3f}  => margin {nn-snn:+.3f}", flush=True)
    print(f"    => weighted margin {'WIDER' if (w-sw) > (eq-seq) else 'NOT wider'} than equal "
          f"({w-sw:+.3f} vs {eq-seq:+.3f}); {'reaches 1-NN' if (w-sw) >= (nn-snn) else 'below 1-NN'} "
          f"({nn-snn:+.3f})", flush=True)

    eq_err = sum(r["eq_err"] for r in real)
    w_fix = sum(r["weighted_fixes_eq"] for r in real)
    w_err = sum(r["w_err"] for r in real)
    eq_fix = sum(r["eq_fixes_w"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): weighted fixes {w_fix}/{eq_err} of equal's "
          f"errors; equal fixes {eq_fix}/{w_err} of weighted's  "
          f"(net {w_fix - eq_fix:+d} in weighted's favour)", flush=True)

    print("\n  MEASURED WEIGHTS by order (mean over folds x channels — the weighting ACTS):",
          flush=True)
    orders = real[0]["orders"]
    from collections import defaultdict
    agg = defaultdict(lambda: ([], []))
    for r in real:
        for (ci, o, acc), wt in zip(r["accs"], r["weights"]):
            agg[o][0].append(acc); agg[o][1].append(wt)
    for o in orders:
        accs, wts = agg[o]
        print(f"    order-{o}: measured-acc mean {np.mean(accs):.3f}  "
              f"weight mean {np.mean(wts):.3f}  (range {min(wts):.2f}-{max(wts):.2f})",
              flush=True)

    print("\n(weighted admissibility graph = the iter-45 (cue x order) combine-all with "
          "each node's likelihood raised to its MEASURED reliability weight (inner-LOSO "
          "train accuracy, normalised above chance) before the product. The weight is a "
          "MEASUREMENT not a searched param; LOSO-clean; the decision is the graph Term "
          "Argmax of Times-of-Pow. NO fit, NO sweep, NO gradient, NO donkey.)", flush=True)


if __name__ == "__main__":
    main()
