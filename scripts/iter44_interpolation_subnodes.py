"""iter44_interpolation_subnodes — the INTERPOLATION SUB-NODE iteration.

THE USER'S INSIGHT: "noise is just signal you don't understand; the graph needs
interpolation sub-nodes." The per-word token cloud (per-speaker + coarticulation
variation) is SIGNAL with continuous structure. The two reflexes fail:
  · 1-NN (current)      IGNORES the cloud structure;
  · centroid (iter-41)  AVERAGES it away (HURT -0.122 FSDD);
  · all-pole (iter-43)  SHARPENS the axis, REDUNDANT (drop-it ~+0.00).

THE LEVER (composable geometry, NO-FIT): model each word's token cloud as a low-rank
AFFINE MANIFOLD (centroid + top-r principal directions of the centered cloud, by
closed-form SVD) — the continuous structure BETWEEN the exemplars. Recognise a heard
token by its RECONSTRUCTION distance to each word's manifold (how well it interpolates
within the cloud), softmaxed by the channel's own median (the identical channel math).
domains/interpolation_subnodes. The decision Term is UNCHANGED; only the channel's
distance SOURCE changes from raw-token 1-NN to manifold-reconstruction residual.

EVALUATE on the bound's venue: FSDD LOSO over held-out speakers, multi-metric, with
SHUFFLE. The decisive read: does MODELING the cloud variation (interpolation) LIFT
held-out recognition where AVERAGING (centroid) HURT and SHARPENING (all-pole) was
REDUNDANT? Interpolation vs 1-NN vs centroid vs frozen; per-fold; drop-it; error-overlap.

  python -m scripts.iter44_interpolation_subnodes [n_per] [rounds] [rank]
"""
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_whisper import gather, load_wav
import scripts.enriched_hvpt_accept as EH
import domains.many_settings_recognizer as MS
from domains.interpolation_subnodes import (
    word_manifolds, manifold_channel_likelihood, heldout_1nn_manifold,
)
from domains.speaker_invariant_centroids import (
    speaker_invariant_centroids, centroid_channel_likelihood, heldout_1nn_centroid,
)
from scripts.iter41_speaker_invariance import (
    train_speaker_labels, heldout_combined_centroid,
)
from scripts.many_settings_hvpt_accept import heldout_1nn


# ---------------------------------------------------------------------------
# Interpolation variant of EH.heldout_combined: every cosine VECTOR channel's
# per-candidate likelihood comes from the INTERPOLATION-MANIFOLD reconstruction
# residual (modeling the spread); the precomputed-likelihood channels (AxS) are
# unchanged. Same variadic Argmax-of-product, decision Term byte-identical.
# ---------------------------------------------------------------------------

def heldout_combined_manifold(vec_train, vec_test, train_words, test_words,
                              extra_lik_channels=(), rank=3, ridge=0.0,
                              return_preds=False):
    """Same variadic-product recognition as EH.heldout_combined, but every cosine
    vector channel's per-candidate likelihood comes from the INTERPOLATION MANIFOLD
    reconstruction residual instead of the raw-token 1-NN. The decision Term, the
    softmax, the product are byte-identical; only the distance SOURCE changes."""
    n_vec = len(vec_train)
    n_extra = len(extra_lik_channels)
    n_ch = n_vec + n_extra
    candidates = sorted(set(train_words))
    # Pre-build each channel's per-word affine manifold ONCE (closed-form SVD, no fit).
    chan_mans = [word_manifolds(vec_train[ci], train_words, rank=rank)
                 for ci in range(n_vec)]
    sub = EH._enr_substrate(candidates, n_ch)
    correct = 0
    preds = []
    n_test = len(test_words)
    for qi in range(n_test):
        for ci in range(n_vec):
            p = manifold_channel_likelihood(np.asarray(vec_test[ci][qi]),
                                            chan_mans[ci], candidates, ridge=ridge)
            for w in candidates:
                sub.set_attr(EH._ENR_WC[w], MS.channel_attr(ci), p[w])
        for ei, chan in enumerate(extra_lik_channels):
            p = chan[qi]
            for w in candidates:
                sub.set_attr(EH._ENR_WC[w], MS.channel_attr(n_vec + ei),
                             float(p.get(w, 1.0 / len(candidates))))
        pred = sub.evaluate(EH._ENR_TERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        preds.append(pw)
        correct += int(pw == test_words[qi])
    if return_preds:
        return preds
    return correct / max(n_test, 1)


# ---------------------------------------------------------------------------
# Score one LOSO fold: INTERPOLATION graph vs 1-NN graph vs CENTROID graph vs frozen,
# plus single-flat (all four reads), per-channel interpolation Δ, error-overlap, and
# the interpolation sub-node DROP-IT (the manifold node removed from the combine-all).
# ---------------------------------------------------------------------------

def score_fold(voice_audio, held_voice, rounds=2, shuffle=False,
               rank=3, ridge=0.0, k=1):
    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=shuffle,
                         skip_axs=True)
    tw, hw = fold["train_words"], fold["held_words"]
    spk = train_speaker_labels(voice_audio, held_voice, shuffle=shuffle)
    assert len(spk) == len(tw), (len(spk), len(tw), "speaker-label/train misalign")

    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    vec_tr = many_tr + ot_tr
    vec_he = many_he + ot_he

    # The three readings of the SAME token cloud, the WHOLE graph (combine-all):
    #   1-NN     : distance to the nearest raw exemplar (the CURRENT graph)
    #   centroid : distance to the cloud's mean point   (iter-41, AVERAGES the spread)
    #   manifold : reconstruction onto the cloud's span (iter-44, MODELS the spread)
    nn = EH.heldout_combined(vec_tr, vec_he, tw, hw)
    cent = heldout_combined_centroid(vec_tr, vec_he, tw, spk, hw, k=k)
    interp = heldout_combined_manifold(vec_tr, vec_he, tw, hw, rank=rank, ridge=ridge)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    # single-flat: the cleanest single-channel read of all three.
    sf_tr, sf_he = fold["single_flat_train"], fold["single_flat_held"]
    sf_nn = heldout_1nn(sf_tr, tw, sf_he, hw)
    sf_cent = heldout_1nn_centroid(sf_tr, tw, spk, sf_he, hw, k=k)
    sf_interp = heldout_1nn_manifold(sf_tr, tw, sf_he, hw, rank=rank, ridge=ridge)

    # per-CHANNEL interpolation Δ vs 1-NN (diagnostic: which channels does modeling the
    # cloud help?) — single channel each.
    per_chan = {}
    names = fold["many_names"] + fold["ortho_names"]
    for ci, nm in enumerate(names):
        raw = heldout_1nn(vec_tr[ci], tw, vec_he[ci], hw)
        man = heldout_1nn_manifold(vec_tr[ci], tw, vec_he[ci], hw,
                                   rank=rank, ridge=ridge)
        per_chan[nm] = (raw, man)

    # DROP-IT: the interpolation sub-node as ONE MORE node in the combine-all — does it
    # add information ON TOP of the existing 1-NN graph? We compose a single
    # manifold-likelihood channel (the single-flat manifold read, the strongest single
    # interpolation cue) and add it as an extra precomputed-likelihood channel to the
    # 1-NN graph; the Δ vs the 1-NN graph alone is the sub-node's drop-it contribution.
    cands = sorted(set(tw))
    sf_mans = word_manifolds(sf_tr, tw, rank=rank)
    sf_man_lik = [manifold_channel_likelihood(np.asarray(q), sf_mans, cands,
                                              ridge=ridge) for q in sf_he]
    nn_plus_interp = EH.heldout_combined(vec_tr, vec_he, tw, hw,
                                         extra_lik_channels=[sf_man_lik])
    interp_dropit = nn_plus_interp - nn       # sub-node added to the 1-NN graph

    # error-overlap: on queries the 1-NN graph gets WRONG, does the INTERPOLATION graph
    # get them right (and vice versa)?
    nn_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw, return_preds=True)
    interp_pred = heldout_combined_manifold(vec_tr, vec_he, tw, hw, rank=rank,
                                            ridge=ridge, return_preds=True)
    nn_err = [i for i, (p, w) in enumerate(zip(nn_pred, hw)) if p != w]
    interp_fix = sum(int(interp_pred[i] == hw[i]) for i in nn_err)
    interp_err = [i for i, (p, w) in enumerate(zip(interp_pred, hw)) if p != w]
    nn_fix = sum(int(nn_pred[i] == hw[i]) for i in interp_err)

    return {"held_voice": held_voice, "shuffle": shuffle, "rank": rank, "ridge": ridge,
            "nn": nn, "cent": cent, "interp": interp, "frozen": frozen,
            "sf_nn": sf_nn, "sf_cent": sf_cent, "sf_interp": sf_interp,
            "per_chan": per_chan, "names": names,
            "interp_dropit": interp_dropit,
            "n_held": len(hw), "n_train": len(tw),
            "nn_err": len(nn_err), "interp_fixes_nn_err": interp_fix,
            "interp_err": len(interp_err), "nn_fixes_interp_err": nn_fix}


def _report(r):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    print(f"\n--- held-out {r['held_voice']}{tag}  (held {r['n_held']} "
          f"train {r['n_train']}, rank={r['rank']} ridge={r['ridge']}) ---", flush=True)
    print(f"  INTERPOLATION {r['interp']:.3f}   1-NN {r['nn']:.3f}   "
          f"CENTROID {r['cent']:.3f}   frozen {r['frozen']:.3f}", flush=True)
    print(f"    Δ(interp - 1NN) {r['interp']-r['nn']:+.3f}  "
          f"({'LIFTS' if r['interp'] > r['nn'] else 'no lift' if r['interp']==r['nn'] else 'HURTS'})"
          f"   Δ(interp - centroid) {r['interp']-r['cent']:+.3f}", flush=True)
    print(f"  single-flat: interp {r['sf_interp']:.3f}  1-NN {r['sf_nn']:.3f}  "
          f"centroid {r['sf_cent']:.3f}  Δ(interp-1NN) {r['sf_interp']-r['sf_nn']:+.3f}",
          flush=True)
    print(f"  interp sub-node DROP-IT (added to 1-NN graph) Δ {r['interp_dropit']:+.3f}",
          flush=True)
    print(f"  error-overlap: interp fixes {r['interp_fixes_nn_err']}/{r['nn_err']} of "
          f"1-NN's errors;  1-NN fixes {r['nn_fixes_interp_err']}/{r['interp_err']} of "
          f"interp's errors", flush=True)
    deltas = sorted(((nm, m - raw) for nm, (raw, m) in r["per_chan"].items()),
                    key=lambda t: -t[1])
    top = "  ".join(f"{nm}[{d:+.3f}]" for nm, d in deltas[:4])
    bot = "  ".join(f"{nm}[{d:+.3f}]" for nm, d in deltas[-4:])
    print(f"  per-channel interp Δ  best: {top}   worst: {bot}", flush=True)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    rank = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    ridge = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-44 — INTERPOLATION SUB-NODES (model the cloud as a manifold)", flush=True)
    print(f"  rank={rank} principal directions per word per channel, ridge={ridge}",
          flush=True)
    print("  three reads of the SAME token cloud: 1-NN ignores / centroid averages /",
          flush=True)
    print("  MANIFOLD models the spread.  decision Term UNCHANGED; only the channel",
          flush=True)
    print("  distance source changes to manifold-reconstruction.  NO fit / NO net / NO donkey",
          flush=True)
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
        r = score_fold(voice_audio, held, rounds, shuffle=False, rank=rank, ridge=ridge)
        _report(r); real.append(r)
        sr = score_fold(voice_audio, held, rounds, shuffle=True, rank=rank, ridge=ridge)
        _report(sr); shuf.append(sr)

    def mean(rs, key):
        return float(np.mean([x[key] for x in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over 6 held-out FSDD speakers, chance 0.100)", flush=True)
    print("=" * 72, flush=True)
    interp = mean(real, "interp"); nn = mean(real, "nn")
    cent = mean(real, "cent"); fr = mean(real, "frozen")
    sfi = mean(real, "sf_interp"); sfn = mean(real, "sf_nn"); sfc = mean(real, "sf_cent")
    si = mean(shuf, "interp"); snn = mean(shuf, "nn"); scent = mean(shuf, "cent")
    dropit = mean(real, "interp_dropit")

    print(f"  INTERPOLATION graph (models the spread) {interp:.3f}", flush=True)
    print(f"  1-NN graph (ignores the spread, CURRENT) {nn:.3f}", flush=True)
    print(f"  CENTROID graph (averages the spread, iter-41) {cent:.3f}", flush=True)
    print(f"  frozen {fr:.3f}", flush=True)
    print(f"  *** interp vs 1-NN  Δ {interp-nn:+.3f}  "
          f"=> {'INTERPOLATION LIFTS held-out recognition' if interp > nn else 'NO LIFT (null)' if interp==nn else 'HURTS'}",
          flush=True)
    print(f"  *** interp vs centroid Δ {interp-cent:+.3f}  "
          f"(did modeling beat averaging?  centroid was iter-41's HURT)", flush=True)
    print(f"  single-flat: interp {sfi:.3f}  1-NN {sfn:.3f}  centroid {sfc:.3f}  "
          f"Δ(interp-1NN) {sfi-sfn:+.3f}  (cleanest single-channel read)", flush=True)
    print(f"  *** interp sub-node DROP-IT (added to 1-NN graph) Δ {dropit:+.3f}  "
          f"=> {'adds info on top of 1-NN' if dropit > 0 else 'redundant/neutral' if dropit==0 else 'hurts'}",
          flush=True)

    print("\n  SHUFFLE control (voice partition scrambled — modeling the cloud must "
          "NOT help if the spread is structureless):", flush=True)
    print(f"    interp   real {interp:.3f}  shuffle {si:.3f}  => margin {interp-si:+.3f}  "
          f"({'CLEAN' if interp > si else 'NOT CLEAN'})", flush=True)
    print(f"    1-NN     real {nn:.3f}  shuffle {snn:.3f}  => margin {nn-snn:+.3f}",
          flush=True)
    print(f"    centroid real {cent:.3f}  shuffle {scent:.3f}  => margin {cent-scent:+.3f}",
          flush=True)
    print(f"    => interp's real-vs-shuffle margin "
          f"{'WIDER' if (interp-si) > (nn-snn) else 'NOT wider'} than 1-NN's "
          f"({interp-si:+.3f} vs {nn-snn:+.3f})", flush=True)

    nn_err = sum(r["nn_err"] for r in real)
    interp_fix = sum(r["interp_fixes_nn_err"] for r in real)
    interp_err = sum(r["interp_err"] for r in real)
    nn_fix = sum(r["nn_fixes_interp_err"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): interp fixes {interp_fix}/{nn_err} of 1-NN's "
          f"errors; 1-NN fixes {nn_fix}/{interp_err} of interp's errors  "
          f"(net {interp_fix - nn_fix:+d} in interp's favour)", flush=True)

    print("\n  PER-CHANNEL interp Δ (mean over folds; which channels does modeling "
          "the cloud manifold help?):", flush=True)
    names = real[0]["names"]
    chan_deltas = []
    for nm in names:
        raws = [r["per_chan"][nm][0] for r in real]
        mans = [r["per_chan"][nm][1] for r in real]
        chan_deltas.append((nm, float(np.mean(mans)) - float(np.mean(raws)),
                            float(np.mean(raws)), float(np.mean(mans))))
    for nm, d, raw, man in sorted(chan_deltas, key=lambda t: -t[1]):
        print(f"    {nm:22s} 1-NN {raw:.3f} -> manifold {man:.3f}  Δ {d:+.3f}",
              flush=True)

    print("\n(interp graph = the iter-34 cue-graph with each channel's distance source "
          "swapped from raw-token 1-NN to MANIFOLD-reconstruction residual — the cloud "
          "modeled as a low-rank affine span (centroid + SVD principal directions of "
          "the centered cloud), the user's interpolation sub-node. Decision Term "
          "UNCHANGED; closed-form SVD geometry, NO fit, NO net, NO donkey.)", flush=True)


if __name__ == "__main__":
    main()
