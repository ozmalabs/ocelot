"""RUN defer-and-learn in the LIVE audio adapter — stream real speech, learn OOV words one-shot AS IT LISTENS.

The LiveAudioWorld now grows its lexicon: ear (perception) -> Recognition -> graph Rules decide ACT/DEFER -> on DEFER the
host reifies an Unknown ('teach me'), the pluggable teacher (oracle here) labels it, and the exemplar is appended to the
GROWING bank (in-vocab next time). Held words OUT of the initial bank; stream cross-speaker utterances; measure cross-speaker
one-shot recognition + the falling defer-rate, all in the live streaming adapter. The gate threshold is FIXED (eta=0) so the
defer-rate decay comes purely from LEARNING (held-out words becoming in-vocab), not from re-tuning.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.run_live_defer_learn
"""
from __future__ import annotations

import glob
import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import w2v_all_layers, fit_pca, pca_apply, dtw, NWAY
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from substrate.world_adapter import WorldAdapter
from domains.live_audio_world import LiveAudioWorld

CACHE = "/tmp/p0lat_cache_L6.pkl"
LAYER = 6
N_HOLDOUT = 35
N_STREAM_UTT = 140
MARGIN_THRESH = 0.10


def ear(audio, fs):
    return w2v_all_layers(audio, fs)[LAYER]


def main():
    print("=" * 100)
    print("LIVE DEFER-AND-LEARN — stream real speech, learn OOV one-shot as it listens (graph-native loop)")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train = data["train"]
    mu_p, V_p = fit_pca([t[4] for t in train])

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)

    # which in-vocab words appear across >=2 TEST speakers -> hold them out (learn from A, test on B)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk = spks[-5:]
    tsp = defaultdict(set)
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            for w in t.lower().split():
                w = w.strip(".,?!;:\"'")
                if w in vset:
                    tsp[w].add(sp)
    holdout = set([w for w in vocab if len(tsp[w]) >= 2][:N_HOLDOUT])
    known = [w for w in vocab if w not in holdout]

    # initial bank = KNOWN words only (holdout is OOV)
    init_bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        if w in known and cnt[w] < 6:
            init_bank[w].append(pca_apply(lat, mu_p, V_p)); cnt[w] += 1
    PW0 = np.stack([np.stack([e.mean(0) for e in init_bank[w]]).mean(0) for w in known if init_bank[w]])
    print(f"  initial bank {len([w for w in known if init_bank[w]])} KNOWN words; {len(holdout)} held OUT as OOV\n")

    # the live world with defer-and-learn ON; oracle teacher (the external label source); FIXED gate (eta=0)
    agent = WorldAdapter(seeds=())
    def oracle(traj, gold):
        return gold                                      # external label source (whisper/human in production)
    world = LiveAudioWorld(agent, ear=ear, bank=init_bank, vocab=[w for w in known if init_bank[w]], PW=PW0,
                           pca_mu=mu_p, pca_V=V_p, dtw=dtw, eta=0.0, init_threshold=MARGIN_THRESH,
                           teacher=oracle, learn=True)

    stream = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            stream.append((sp, f, t))
    stream = stream[:N_STREAM_UTT]
    print(f"  streaming {len(stream)} utterances (speaker-by-speaker) through the live learning adapter...\n")

    learned_from = {}; one_shot = []; pre_learn = []; defers = []; n_words = 0; bank_trace = []
    for ui, (sp, f, t) in enumerate(stream):
        x, fs = load_flac(f); x = np.asarray(x, np.float64)
        try:
            spans = [(w, t0, t1) for (w, t0, t1) in align_utt(x, fs, t) if len(w) >= MINW and w in vset]
        except Exception:
            continue
        if not spans:
            continue
        rids = world.ingest_utterance(x, fs, spans)
        world.step(rids)
        # score held-out cross-speaker BEFORE the learn pass mutates the bank for this batch's deferred
        for (rid, word, gold) in rids:
            _w, decision = world.emit(rid); n_words += 1
            defers.append(1 if decision == "DEFER" else 0)
            if gold in holdout:
                if gold not in learned_from:
                    pre_learn.append(int(_w == gold))
                elif sp != learned_from[gold]:
                    one_shot.append(int(_w == gold))
        world.learn_pass(rids)                           # DEFER -> teach -> grow bank
        for (rid, word, gold) in rids:
            if gold in holdout and gold not in learned_from and world.a.s.node(rid)["attrs"].get("act", 0.0) < 0.5:
                learned_from[gold] = sp                  # taught this round
        bank_trace.append(world.bank_size())

    n = len(defers); W = max(40, n // 10)
    windows = [100 * np.mean(defers[i:i + W]) for i in range(0, n - W, W)]
    cs = 100 * np.mean(one_shot) if one_shot else 0.0
    pre = 100 * np.mean(pre_learn) if pre_learn else 0.0

    print("=" * 100)
    print(f"  streamed {n} words; teacher queried {sum(defers)} ({100*sum(defers)/n:.0f}%, only on DEFER); bank grew {bank_trace[0]}->{bank_trace[-1]} words")
    print(f"  held-out BEFORE learning (control):           {pre:.1f}%  (OOV, not in bank)")
    print(f"  CROSS-SPEAKER ONE-SHOT (learned A -> heard B): {cs:.1f}%  ({len(one_shot)} instances)")
    print(f"  defer-rate over stream (windows of {W}): {' '.join(f'{x:.0f}' for x in windows)}")
    print("-" * 100)
    decayed = len(windows) >= 2 and windows[-1] < windows[0]
    if cs >= 70 and pre < 15 and world.bank_size() > bank_trace[0]:
        print(f"  LIVE DEFER-AND-LEARN — the streaming adapter LEARNS as it listens: held-out words ~{pre:.0f}% (OOV) -> after ONE")
        print(f"  taught exemplar recognised CROSS-SPEAKER at {cs:.0f}%, the bank grew {bank_trace[0]}->{bank_trace[-1]}, the teacher asked only")
        print(f"  on DEFER ({100*sum(defers)/n:.0f}%), defer-rate {windows[0]:.0f}->{windows[-1]:.0f}%. Graph Rules decide; the host teaches. Loop closed, live.")
    else:
        print(f"  PARTIAL — cross-speaker one-shot {cs:.0f}% (bar 70), pre {pre:.0f}%, bank {bank_trace[0]}->{bank_trace[-1]}. Loop runs live;")
        print("  check margin / coverage if the one-shot misses.")
    print("=" * 100)


if __name__ == "__main__":
    main()
