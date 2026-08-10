"""iter45_ordern_interpolation — the ARBITRARY, ORDER-N interpolation iteration.

THE USER: "selective interp should be arbitrary and order n." iter-44 showed the
interpolation manifold LIFTS (interp 0.644 vs 1-NN 0.594, +0.050) but is per-channel
MIXED (helps broad/formant channels, HURTS sparse narrow-window ones), and its margin
stayed smoothing-dominated (+0.031 vs 1-NN's +0.075). iter-44's manifold was a SINGLE
fixed order (the linear affine span).

THE GENERALIZATION (NOT a new mechanism, NOT a hand-pick): point the agent's OWNED
order-N operator (order_n_concepts: 0=value, 1=tilt, 2=curvature, … n) at the CLOUD
manifold. Per channel's per-word token cloud build EVERY order:
  · order-0 = the POINT estimate (centroid — the value)
  · order-1 = the local LINEAR manifold (~iter-44)
  · order-2 = the local QUADRATIC manifold (curvature)
  · … order-n
Each (order × channel) is a NODE; ALL enter the SAME variadic Argmax-of-product
(combine-all). The graph KEEPS whichever order fits each channel's cloud — the helpful
widen, the harmful (near-flat / sparse) multiply in near-uniform and cannot drag the
rest. NO channel hand-picked for an order (the forbidden select-best). The graph
self-selects the order per channel. domains/order_n_interpolation. Decision Term
UNCHANGED (just more nodes in the product); closed-form SVD geometry, NO fit, NO net.

EVALUATE: FSDD LOSO over held-out speakers, multi-metric, with SHUFFLE + per-order
drop-it. The decisive read: does the ARBITRARY order-N family (combine-all) LIFT
held-out recognition AND RESOLVE the iter-44 per-channel mix (each channel finding its
own order) WITHOUT hand-picking, AND widen the real-vs-shuffle margin past iter-44's
+0.031 toward 1-NN's +0.075 (i.e. is the lift cross-voice structure, not smoothing)?

  PYTHONUNBUFFERED=1 python -m scripts.iter45_ordern_interpolation [n_per] [rounds] [n_max] [ridge]
"""
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_whisper import gather, load_wav
import scripts.enriched_hvpt_accept as EH
import domains.many_settings_recognizer as MS
from domains.order_n_interpolation import (
    word_cloud_models, order_n_channel_likelihood, heldout_1nn_order_n,
)
from domains.interpolation_subnodes import (
    word_manifolds, manifold_channel_likelihood,
)
from scripts.many_settings_hvpt_accept import heldout_1nn


# ---------------------------------------------------------------------------
# combine-all over EVERY (order × channel) node. For n_vec cosine channels and orders
# 0..n_max, the product has n_vec*(n_max+1) order-N nodes (+ any extra-lik channels).
# Each (order, channel) is one node; ALL enter the SAME variadic Argmax-of-product.
# The decision Term is byte-identical to EH.heldout_combined — only the NODE COUNT and
# each node's distance SOURCE (order-N cloud residual) differ. NO hand-pick, NO weight.
# ---------------------------------------------------------------------------

def heldout_combined_ordern(vec_train, vec_test, train_words, test_words,
                            orders, extra_lik_channels=(), n_max=None, ridge=0.0,
                            return_preds=False):
    """Variadic-product recognition over (len(orders) × n_vec) order-N cloud nodes PLUS
    the precomputed-likelihood channels. EVERY (order × channel) is one symmetric node
    in the SAME product (combine-all). Decision Term unchanged."""
    n_vec = len(vec_train)
    if n_max is None:
        n_max = max(orders)
    n_order = len(orders)
    n_extra = len(extra_lik_channels)
    n_node = n_vec * n_order + n_extra
    candidates = sorted(set(train_words))
    # Per channel, the per-word cloud model (one SVD serves all orders). NO fit.
    chan_models = [word_cloud_models(vec_train[ci], train_words, n_max=n_max)
                   for ci in range(n_vec)]
    sub = EH._enr_substrate(candidates, n_node)
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
                    sub.set_attr(EH._ENR_WC[w], MS.channel_attr(ni), p[w])
                ni += 1
        for ei, chan in enumerate(extra_lik_channels):
            p = chan[qi]
            for w in candidates:
                sub.set_attr(EH._ENR_WC[w], MS.channel_attr(ni),
                             float(p.get(w, 1.0 / len(candidates))))
            ni += 1
        pred = sub.evaluate(EH._ENR_TERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        preds.append(pw)
        correct += int(pw == test_words[qi])
    if return_preds:
        return preds
    return correct / max(n_test, 1)


# ---------------------------------------------------------------------------
# Score one LOSO fold: ORDER-N combine-all vs iter-44 single-interp vs 1-NN vs
# centroid vs frozen, plus the per-ORDER drop-it (the WHOLE order removed from the
# combine-all — which orders does the graph effectively use?) and the per-channel
# best-order diagnostic (which order each channel prefers ALONE — diagnostic, NOT a
# selection: the accepted graph is always the full all-orders combine-all).
# ---------------------------------------------------------------------------

def score_fold(voice_audio, held_voice, rounds=2, shuffle=False,
               n_max=2, ridge=0.0):
    from domains.speaker_invariant_centroids import (
        speaker_invariant_centroids, centroid_channel_likelihood, heldout_1nn_centroid,
    )
    from scripts.iter41_speaker_invariance import (
        train_speaker_labels, heldout_combined_centroid,
    )
    from scripts.iter44_interpolation_subnodes import heldout_combined_manifold

    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=shuffle,
                         skip_axs=True)
    tw, hw = fold["train_words"], fold["held_words"]
    spk = train_speaker_labels(voice_audio, held_voice, shuffle=shuffle)
    assert len(spk) == len(tw), (len(spk), len(tw), "speaker-label/train misalign")

    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    vec_tr = many_tr + ot_tr
    vec_he = many_he + ot_he
    names = fold["many_names"] + fold["ortho_names"]
    orders = list(range(n_max + 1))             # 0,1,2,...,n_max

    # The comparators (all combine-all over the WHOLE cue-graph):
    #   order-N : EVERY (order × channel) node in the product (this iter)
    #   iter-44 : the SINGLE linear manifold per channel (order-1 only)
    #   1-NN    : the raw-token point estimate per channel (the CURRENT graph)
    #   centroid: the cloud mean per channel (iter-41 — AVERAGES the spread)
    ordern = heldout_combined_ordern(vec_tr, vec_he, tw, hw, orders,
                                     n_max=n_max, ridge=ridge)
    interp44 = heldout_combined_manifold(vec_tr, vec_he, tw, hw, rank=3, ridge=ridge)
    nn = EH.heldout_combined(vec_tr, vec_he, tw, hw)
    cent = heldout_combined_centroid(vec_tr, vec_he, tw, spk, hw, k=1)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    # PER-ORDER DROP-IT: remove ONE whole order's nodes from the combine-all — which
    # orders does the graph effectively USE? (drop Δ > 0 => that order carries info.)
    per_order_drop = {}
    for drop_o in orders:
        kept = [o for o in orders if o != drop_o]
        if not kept:
            per_order_drop[drop_o] = 0.0
            continue
        without = heldout_combined_ordern(vec_tr, vec_he, tw, hw, kept,
                                          n_max=n_max, ridge=ridge)
        per_order_drop[drop_o] = ordern - without

    # PER-ORDER ALONE: the whole cue-graph at a SINGLE order (diagnostic).
    per_order_alone = {}
    for o in orders:
        per_order_alone[o] = heldout_combined_ordern(vec_tr, vec_he, tw, hw, [o],
                                                     n_max=n_max, ridge=ridge)

    # PER-CHANNEL best-order (diagnostic, NOT selection): for each channel, which single
    # order recognises best ALONE? Shows each channel finding its own order — the
    # resolution of the iter-44 per-channel mix WITHOUT hand-picking (the graph keeps ALL
    # orders; this only REPORTS that different channels favour different orders).
    per_chan_best = {}
    for ci, nm in enumerate(names):
        accs = {o: heldout_1nn_order_n(vec_tr[ci], tw, vec_he[ci], hw, o,
                                       n_max=n_max, ridge=ridge) for o in orders}
        best_o = max(accs, key=accs.get)
        per_chan_best[nm] = (best_o, accs)

    # error-overlap: on queries 1-NN gets WRONG, does order-N get them right?
    nn_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw, return_preds=True)
    on_pred = heldout_combined_ordern(vec_tr, vec_he, tw, hw, orders,
                                      n_max=n_max, ridge=ridge, return_preds=True)
    nn_err = [i for i, (p, w) in enumerate(zip(nn_pred, hw)) if p != w]
    on_fix = sum(int(on_pred[i] == hw[i]) for i in nn_err)
    on_err = [i for i, (p, w) in enumerate(zip(on_pred, hw)) if p != w]
    nn_fix = sum(int(nn_pred[i] == hw[i]) for i in on_err)

    return {"held_voice": held_voice, "shuffle": shuffle, "n_max": n_max, "ridge": ridge,
            "ordern": ordern, "interp44": interp44, "nn": nn, "cent": cent,
            "frozen": frozen, "orders": orders,
            "per_order_drop": per_order_drop, "per_order_alone": per_order_alone,
            "per_chan_best": per_chan_best, "names": names,
            "n_held": len(hw), "n_train": len(tw),
            "nn_err": len(nn_err), "ordern_fixes_nn_err": on_fix,
            "ordern_err": len(on_err), "nn_fixes_ordern_err": nn_fix}


def _report(r):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    print(f"\n--- held-out {r['held_voice']}{tag}  (held {r['n_held']} train "
          f"{r['n_train']}, n_max={r['n_max']} ridge={r['ridge']}) ---", flush=True)
    print(f"  ORDER-N {r['ordern']:.3f}   iter-44 {r['interp44']:.3f}   "
          f"1-NN {r['nn']:.3f}   CENTROID {r['cent']:.3f}   frozen {r['frozen']:.3f}",
          flush=True)
    print(f"    Δ(orderN - iter44) {r['ordern']-r['interp44']:+.3f}   "
          f"Δ(orderN - 1NN) {r['ordern']-r['nn']:+.3f}  "
          f"({'LIFTS' if r['ordern'] > r['nn'] else 'no lift' if r['ordern']==r['nn'] else 'HURTS'})",
          flush=True)
    pod = "  ".join(f"o{o}[{r['per_order_drop'][o]:+.3f}]" for o in r["orders"])
    poa = "  ".join(f"o{o}[{r['per_order_alone'][o]:.3f}]" for o in r["orders"])
    print(f"    per-order drop-it: {pod}", flush=True)
    print(f"    per-order alone:   {poa}", flush=True)
    print(f"  error-overlap: order-N fixes {r['ordern_fixes_nn_err']}/{r['nn_err']} of "
          f"1-NN's errors;  1-NN fixes {r['nn_fixes_ordern_err']}/{r['ordern_err']} of "
          f"order-N's errors", flush=True)
    # which order each channel prefers ALONE (the per-channel mix resolution)
    from collections import Counter
    pref = Counter(b for b, _ in r["per_chan_best"].values())
    print(f"    per-channel best-order spread: "
          f"{dict(sorted(pref.items()))}  (channels finding their own order)", flush=True)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    ridge = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-45 — ARBITRARY ORDER-N INTERPOLATION (the agent's order-N operator", flush=True)
    print("           pointed at the token CLOUD manifold; combine-all over orders)", flush=True)
    print(f"  orders 0..{n_max} per channel, ridge={ridge}   "
          f"(0=value, 1=linear~iter44, 2=curvature, …)", flush=True)
    print("  EVERY (order × channel) is a node in the SAME variadic product; the graph", flush=True)
    print("  self-selects the order per channel. NO hand-pick, NO fit, NO net, NO donkey", flush=True)
    print("=" * 72, flush=True)

    items = gather(n_per_class_per_speaker=n_per)
    voice_audio = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)
    print(f"ortho cues = {EH.ORTHO_NAMES}", flush=True)

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
    ordern = mean(real, "ordern"); interp44 = mean(real, "interp44")
    nn = mean(real, "nn"); cent = mean(real, "cent"); fr = mean(real, "frozen")
    son = mean(shuf, "ordern"); si44 = mean(shuf, "interp44")
    snn = mean(shuf, "nn"); scent = mean(shuf, "cent")

    print(f"  ORDER-N combine-all (all orders × channels) {ordern:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1 only)        {interp44:.3f}", flush=True)
    print(f"  1-NN graph (order-0 point estimate, CURRENT){nn:.3f}", flush=True)
    print(f"  CENTROID graph (iter-41)                    {cent:.3f}", flush=True)
    print(f"  frozen                                      {fr:.3f}", flush=True)
    print(f"  *** order-N vs 1-NN     Δ {ordern-nn:+.3f}  "
          f"=> {'ORDER-N LIFTS held-out recognition' if ordern > nn else 'NO LIFT' if ordern==nn else 'HURTS'}",
          flush=True)
    print(f"  *** order-N vs iter-44  Δ {ordern-interp44:+.3f}  "
          f"=> {'order-N beats the single fixed order' if ordern > interp44 else 'no gain over single order' if ordern==interp44 else 'WORSE than single order'}",
          flush=True)

    print("\n  PER-ORDER DROP-IT (mean over folds; which orders does the graph use?):",
          flush=True)
    orders = real[0]["orders"]
    for o in orders:
        d = float(np.mean([r["per_order_drop"][o] for r in real]))
        a = float(np.mean([r["per_order_alone"][o] for r in real]))
        print(f"    order-{o}: drop-it Δ {d:+.3f} (alone {a:.3f})  "
              f"=> {'graph USES this order' if d > 0 else 'redundant/neutral' if d==0 else 'hurts (combine-all absorbs)'}",
              flush=True)

    print("\n  SHUFFLE control (voice partition scrambled — order-N must NOT help if the "
          "cloud spread is structureless):", flush=True)
    print(f"    order-N  real {ordern:.3f}  shuffle {son:.3f}  => margin {ordern-son:+.3f}  "
          f"({'CLEAN' if ordern > son else 'NOT CLEAN'})", flush=True)
    print(f"    iter-44  real {interp44:.3f}  shuffle {si44:.3f}  => margin {interp44-si44:+.3f}",
          flush=True)
    print(f"    1-NN     real {nn:.3f}  shuffle {snn:.3f}  => margin {nn-snn:+.3f}", flush=True)
    print(f"    => order-N's cross-voice margin {ordern-son:+.3f}  vs iter-44 +0.031  vs "
          f"1-NN {nn-snn:+.3f}", flush=True)
    print(f"    => order-N margin {'WIDER' if (ordern-son) > (interp44-si44) else 'NOT wider'} "
          f"than iter-44 ({ordern-son:+.3f} vs {interp44-si44:+.3f}); "
          f"{'reaches toward 1-NN structure' if (ordern-son) >= (nn-snn) else 'still below 1-NN (smoothing-leaning)'}",
          flush=True)

    nn_err = sum(r["nn_err"] for r in real)
    on_fix = sum(r["ordern_fixes_nn_err"] for r in real)
    on_err = sum(r["ordern_err"] for r in real)
    nn_fix = sum(r["nn_fixes_ordern_err"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): order-N fixes {on_fix}/{nn_err} of 1-NN's "
          f"errors; 1-NN fixes {nn_fix}/{on_err} of order-N's errors  "
          f"(net {on_fix - nn_fix:+d} in order-N's favour)", flush=True)

    print("\n  PER-CHANNEL BEST-ORDER (diagnostic — each channel finding its OWN order, "
          "the resolution of the iter-44 mix WITHOUT hand-picking):", flush=True)
    from collections import Counter
    names = real[0]["names"]
    spread = Counter()
    for nm in names:
        # mean accuracy per order over folds, then the best
        accs = {o: float(np.mean([r["per_chan_best"][nm][1][o] for r in real]))
                for o in orders}
        best_o = max(accs, key=accs.get)
        spread[best_o] += 1
        accstr = " ".join(f"o{o}:{accs[o]:.3f}" for o in orders)
        print(f"    {nm:22s} best order-{best_o}   ({accstr})", flush=True)
    print(f"    => channels distribute across orders {dict(sorted(spread.items()))}  "
          f"(NOT all one order = the mix is real; the graph keeps ALL of them)", flush=True)

    print("\n(order-N graph = the iter-34 cue-graph with EVERY (order × channel) cloud "
          "node — order-0 centroid / order-1 linear manifold (~iter-44) / order-2 "
          "curvature / … — ALL in the agent's Argmax-of-product. The agent's OWNED "
          "order-N operator (order_n_concepts) pointed at the token CLOUD manifold "
          "instead of time/frequency. combine-all NOT select-best; closed-form SVD "
          "geometry, NO fit, NO net, NO donkey.)", flush=True)


if __name__ == "__main__":
    main()
