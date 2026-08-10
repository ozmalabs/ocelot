"""iter41_speaker_invariance — the FEATURE-SPACE SPEAKER-INVARIANCE iteration.

THE CONVERGENT BOUND (iter-40 verdict + the agent's LIVE order-N derivative + the human
reading all land here): feature-space DISCRIMINATION. The cue-graph carries the
information (iter-37/38 error-overlaps above chance) but its per-channel evidence is a
1-NN over RAW per-SPEAKER tokens, so held-out-speaker queries match the nearest TOKEN
(often same-speaker / wrong-word) rather than the right word's cross-speaker cluster.

THE LEVER (the agent's #1 frontier pick, cross-speaker clustering, enacted no-fit):
replace each channel's raw-token 1-NN evidence with the CROSS-SPEAKER CENTROID distance
(domains/speaker_invariant_centroids) — per-speaker-mean then pool (k=1), or k
cross-speaker modes (k-means over the per-speaker prototypes, k>1). The recognition
DECISION is UNCHANGED (the same variadic Argmax-of-product over the same softmax
likelihoods); only the channel's distance SOURCE changes from token-1-NN to
speaker-invariant centroid. Drop-in, composable, NO fit / NO net / NO donkey.

EVALUATE on the bound's venue: FSDD LOSO over held-out speakers, multi-metric, with
SHUFFLE. The decisive read: does the speaker-invariant centroid evidence LIFT held-out
recognition vs the current raw-token cue-graph? Per-fold + per-channel + error-overlap.

  python -m scripts.iter41_speaker_invariance [n_per_speaker_per_digit] [rounds] [k]

The same machinery transfers to the continuous gold-span venue via
scripts.iter36_continuous_graph (run separately); here the FSDD LOSO is the primary
cross-speaker venue (6 real speakers, balanced vocab, the bound's home).
"""
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_whisper import gather, load_wav
import scripts.enriched_hvpt_accept as EH
import domains.many_settings_recognizer as MS
from domains.speaker_invariant_centroids import (
    speaker_invariant_centroids, centroid_channel_likelihood, heldout_1nn_centroid,
)
from scripts.many_settings_hvpt_accept import heldout_1nn


# ---------------------------------------------------------------------------
# build_fold gives us the per-channel train/held vectors but flattens speakers; we
# need the per-train-token SPEAKER label to cluster across speakers. Reconstruct it
# from the SAME ordering build_fold uses: train_audio = [(w,x,fs) for v in train_voices
# for (x,fs,w) in voice_audio[v]] — grouped by speaker, in speaker order. The gammatone
# channels use the IDENTICAL per-speaker order (tr_items iterates train_voices the same
# way). So one pass over the train_voices in the same order yields the token speaker
# labels aligned to every channel's train-vector list.
# ---------------------------------------------------------------------------

def train_speaker_labels(voice_audio, held_voice, shuffle=False):
    """The per-train-token speaker label, in build_fold's train order. Mirrors
    build_fold's flatten (train_voices order, then each voice's clips). Under shuffle
    build_fold re-buckets into shuf0..shuf{k-1} by slot index; we reproduce the SAME
    deterministic slot order (random.Random(1234)) so the speaker labels stay aligned
    to the shuffled channel vectors."""
    train_voices = [v for v in voice_audio if v != held_voice]
    labels = []
    for v in train_voices:
        for _ in voice_audio[v]:
            labels.append(v)
    if not shuffle:
        return labels
    # Reproduce build_fold's shuffle: slot_order = shuffled range, then bucket
    # idx % k -> shuf{bucket}. The label we want is the SHUFFLE-bucket speaker id
    # (so same-bucket tokens are treated as one 'speaker' — the control: cross-speaker
    # clustering over a SCRAMBLED voice partition must not help).
    rng = random.Random(1234)
    n = len(labels)
    slot_order = list(range(n))
    rng.shuffle(slot_order)
    k = len(train_voices)
    out = [None] * n
    for idx, src in enumerate(slot_order):
        out[idx] = f"shuf{idx % k}"
    return out


# ---------------------------------------------------------------------------
# Speaker-invariant variant of EH.heldout_combined: the vector channels use
# CROSS-SPEAKER CENTROID evidence; the precomputed-likelihood channels (AxS) are
# unchanged (they are already cross-speaker forward models). Same Argmax-of-product.
# ---------------------------------------------------------------------------

def heldout_combined_centroid(vec_train, vec_test, train_words, train_speakers,
                              test_words, extra_lik_channels=(), k=1, seed=0,
                              return_preds=False):
    """Same variadic-product recognition as EH.heldout_combined, but every cosine
    vector channel's per-candidate likelihood comes from the CROSS-SPEAKER CENTROID
    distance (speaker-invariant) instead of the raw-token 1-NN. The decision Term, the
    softmax, the product are byte-identical; only the distance SOURCE changes."""
    n_vec = len(vec_train)
    n_extra = len(extra_lik_channels)
    n_ch = n_vec + n_extra
    candidates = sorted(set(train_words))
    # Pre-cluster each channel's train vectors into speaker-invariant centroids ONCE.
    chan_cents = [speaker_invariant_centroids(vec_train[ci], train_words,
                                              train_speakers, k=k, seed=seed)
                  for ci in range(n_vec)]
    sub = EH._enr_substrate(candidates, n_ch)
    correct = 0
    preds = []
    n_test = len(test_words)
    for qi in range(n_test):
        for ci in range(n_vec):
            p = centroid_channel_likelihood(np.asarray(vec_test[ci][qi]),
                                            chan_cents[ci], candidates)
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
# Score one LOSO fold: the CURRENT raw-token graph vs the SPEAKER-INVARIANT graph,
# plus single-flat (raw 1-NN vs centroid 1-NN) and frozen, plus per-channel centroid
# probe and the cross-speaker error-overlap.
# ---------------------------------------------------------------------------

def score_fold_si(voice_audio, held_voice, rounds=2, shuffle=False, k=1):
    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=shuffle)
    tw, hw = fold["train_words"], fold["held_words"]
    spk = train_speaker_labels(voice_audio, held_voice, shuffle=shuffle)
    assert len(spk) == len(tw), (len(spk), len(tw), "speaker-label/train misalign")

    many_tr, many_he = fold["many_train"], fold["many_held"]
    ot_tr, ot_he = fold["ortho_train"], fold["ortho_held"]
    axs_lik = fold["axs_held_lik"]
    vec_tr = many_tr + ot_tr
    vec_he = many_he + ot_he

    # CURRENT raw-token cue-graph (iter-34/37: vector channels + AxS), the comparator.
    cur = EH.heldout_combined(vec_tr, vec_he, tw, hw, extra_lik_channels=[axs_lik])
    # SPEAKER-INVARIANT cue-graph: same channels, cross-speaker centroid evidence.
    si = heldout_combined_centroid(vec_tr, vec_he, tw, spk, hw,
                                   extra_lik_channels=[axs_lik], k=k)
    # single-flat: raw 1-NN vs centroid 1-NN (the cleanest single-channel read).
    sf_tr, sf_he = fold["single_flat_train"], fold["single_flat_held"]
    sf_raw = heldout_1nn(sf_tr, tw, sf_he, hw)
    sf_cent = heldout_1nn_centroid(sf_tr, tw, spk, sf_he, hw, k=k)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    # per-CHANNEL centroid probe (raw 1-NN vs centroid 1-NN, single channel each) —
    # diagnostic: which channels benefit from cross-speaker clustering?
    per_chan = {}
    names = fold["many_names"] + fold["ortho_names"]
    for ci, nm in enumerate(names):
        raw = heldout_1nn(vec_tr[ci], tw, vec_he[ci], hw)
        cen = heldout_1nn_centroid(vec_tr[ci], tw, spk, vec_he[ci], hw, k=k)
        per_chan[nm] = (raw, cen)

    # cross-speaker error-overlap: on queries the RAW graph gets wrong, does the
    # SPEAKER-INVARIANT graph get them right (and vice versa)?
    cur_pred = EH.heldout_combined(vec_tr, vec_he, tw, hw,
                                   extra_lik_channels=[axs_lik], return_preds=True)
    si_pred = heldout_combined_centroid(vec_tr, vec_he, tw, spk, hw,
                                        extra_lik_channels=[axs_lik], k=k,
                                        return_preds=True)
    cur_err = [i for i, (p, w) in enumerate(zip(cur_pred, hw)) if p != w]
    si_fix = sum(int(si_pred[i] == hw[i]) for i in cur_err)
    si_err = [i for i, (p, w) in enumerate(zip(si_pred, hw)) if p != w]
    cur_fix = sum(int(cur_pred[i] == hw[i]) for i in si_err)

    return {"held_voice": held_voice, "shuffle": shuffle, "k": k,
            "cur": cur, "si": si, "sf_raw": sf_raw, "sf_cent": sf_cent,
            "frozen": frozen, "per_chan": per_chan, "names": names,
            "n_held": len(hw), "n_train": len(tw),
            "cur_err": len(cur_err), "si_fixes_cur_err": si_fix,
            "si_err": len(si_err), "cur_fixes_si_err": cur_fix}


def _report(r):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    print(f"\n--- held-out {r['held_voice']}{tag}  (held {r['n_held']} "
          f"train {r['n_train']}, k={r['k']}) ---", flush=True)
    print(f"  SPEAKER-INVARIANT graph {r['si']:.3f}   CURRENT raw-token graph "
          f"{r['cur']:.3f}   Δ {r['si']-r['cur']:+.3f}  "
          f"({'LIFTS' if r['si'] > r['cur'] else 'no lift' if r['si']==r['cur'] else 'HURTS'})",
          flush=True)
    print(f"  single-flat: centroid {r['sf_cent']:.3f}  raw {r['sf_raw']:.3f}  "
          f"Δ {r['sf_cent']-r['sf_raw']:+.3f}    frozen {r['frozen']:.3f}", flush=True)
    print(f"  error-overlap: SI fixes {r['si_fixes_cur_err']}/{r['cur_err']} of raw's "
          f"errors;  raw fixes {r['cur_fixes_si_err']}/{r['si_err']} of SI's errors",
          flush=True)
    # show the channels where the centroid most helps / hurts
    deltas = sorted(((nm, c - raw) for nm, (raw, c) in r["per_chan"].items()),
                    key=lambda t: -t[1])
    top = "  ".join(f"{nm}[{d:+.3f}]" for nm, d in deltas[:4])
    bot = "  ".join(f"{nm}[{d:+.3f}]" for nm, d in deltas[-4:])
    print(f"  per-channel centroid Δ  best: {top}   worst: {bot}", flush=True)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-41 — FEATURE-SPACE SPEAKER-INVARIANCE via CROSS-SPEAKER CLUSTERING",
          flush=True)
    print(f"  k={k} cross-speaker centroids per word per channel  "
          f"(k=1 = per-speaker-mean then pool; k>1 = k-means modes)", flush=True)
    print("  decision Term UNCHANGED; only the channel distance source changes from",
          flush=True)
    print("  raw-token 1-NN -> speaker-invariant centroid.  NO fit / NO net / NO donkey",
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
        r = score_fold_si(voice_audio, held, rounds, shuffle=False, k=k)
        _report(r); real.append(r)
        sr = score_fold_si(voice_audio, held, rounds, shuffle=True, k=k)
        _report(sr); shuf.append(sr)

    def mean(rs, key):
        return float(np.mean([x[key] for x in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over 6 held-out FSDD speakers, chance 0.100)", flush=True)
    print("=" * 72, flush=True)
    si = mean(real, "si"); cur = mean(real, "cur")
    sfc = mean(real, "sf_cent"); sfr = mean(real, "sf_raw"); fr = mean(real, "frozen")
    ssi = mean(shuf, "si"); scur = mean(shuf, "cur")
    print(f"  SPEAKER-INVARIANT graph  {si:.3f}", flush=True)
    print(f"  CURRENT raw-token graph  {cur:.3f}", flush=True)
    print(f"  *** SI vs CURRENT  Δ {si-cur:+.3f}  "
          f"=> {'SPEAKER-INVARIANCE LIFTS held-out recognition' if si > cur else 'NO LIFT (null)' if si==cur else 'HURTS'}",
          flush=True)
    print(f"  single-flat: centroid {sfc:.3f}  raw {sfr:.3f}  Δ {sfc-sfr:+.3f}  "
          f"(the cleanest single-channel speaker-invariance read)", flush=True)
    print(f"  frozen                   {fr:.3f}", flush=True)
    print("\n  SHUFFLE control (voice partition scrambled — cross-speaker clustering "
          "must NOT help):", flush=True)
    print(f"    SI graph   real {si:.3f}  shuffle {ssi:.3f}  => margin {si-ssi:+.3f}  "
          f"({'CLEAN' if si > ssi else 'NOT CLEAN'})", flush=True)
    print(f"    raw graph  real {cur:.3f}  shuffle {scur:.3f}  => margin {cur-scur:+.3f}",
          flush=True)
    print(f"    => SI's real-vs-shuffle margin "
          f"{'WIDER' if (si-ssi) > (cur-scur) else 'NOT wider'} than raw's "
          f"({si-ssi:+.3f} vs {cur-scur:+.3f})  "
          f"(wider => the lift is genuine cross-speaker structure, not an artifact)",
          flush=True)

    # aggregate error-overlap
    cur_err = sum(r["cur_err"] for r in real)
    si_fix = sum(r["si_fixes_cur_err"] for r in real)
    si_err = sum(r["si_err"] for r in real)
    cur_fix = sum(r["cur_fixes_si_err"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): SI fixes {si_fix}/{cur_err} of raw's errors; "
          f"raw fixes {cur_fix}/{si_err} of SI's errors  "
          f"(net {si_fix - cur_fix:+d} in SI's favour)", flush=True)

    # per-channel aggregate centroid delta
    print("\n  PER-CHANNEL centroid Δ (mean over folds; which channels does "
          "cross-speaker clustering help?):", flush=True)
    names = real[0]["names"]
    chan_deltas = []
    for nm in names:
        raws = [r["per_chan"][nm][0] for r in real]
        cens = [r["per_chan"][nm][1] for r in real]
        chan_deltas.append((nm, float(np.mean(cens)) - float(np.mean(raws)),
                            float(np.mean(raws)), float(np.mean(cens))))
    for nm, d, raw, cen in sorted(chan_deltas, key=lambda t: -t[1]):
        print(f"    {nm:22s} raw {raw:.3f} -> centroid {cen:.3f}  Δ {d:+.3f}",
              flush=True)

    print("\n(SI graph = the iter-34/37 cue-graph with each channel's distance source "
          "swapped from raw-token 1-NN to CROSS-SPEAKER centroid; the agent's #1 "
          "frontier pick (cross-speaker clustering) enacting the convergent "
          "feature-space speaker-invariance bound. Decision Term UNCHANGED; group-mean "
          "/ k-means prototypes, NO fit, NO net, NO donkey.)", flush=True)


if __name__ == "__main__":
    main()
