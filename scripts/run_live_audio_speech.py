"""RUN the LiveAudioWorld — stream real audio through the strong ear + graph-native selective-action faculty, end to end.

For each incoming utterance (audio file here; a mic is a trivial input swap): the adapter runs the wav2vec2 EAR (perception),
recognises each word against the banked exemplars, writes Recognition{word, margin} nodes, ticks (the graph faculty decides
ACT/DEFER and the agent's delta-rule trainer tunes the gate online), and emits the selective decision. The gate adapts over
the stream (nothing frozen). Reports a streaming trace + the online theta/coverage adaptation + ACT-set accuracy vs act-on-all.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.run_live_audio_speech
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import w2v_all_layers, fit_pca, pca_apply, dtw
from scripts.earn_strong_ear_rescore import build_ear
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from substrate.world_adapter import WorldAdapter
from domains.live_audio_world import LiveAudioWorld

CACHE = "/tmp/p0lat_cache_L6.pkl"
N_STREAM_UTT = 90
LAYER = 6


def ear(audio, fs):
    return w2v_all_layers(audio, fs)[LAYER]            # wav2vec2 latent (perception primitive)


def main():
    print("=" * 100)
    print("LIVE AUDIO WORLD — streaming speech -> strong ear -> graph selective-action faculty -> decision")
    print("=" * 100)

    # bank (strong ear exemplars) from the cache: raw wav2vec latent -> PCA64
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train = data["train"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    bank_words = [(t[0], t[1], t[2], pca_apply(t[4], mu_p, V_p)) for t in train]
    bank, vocab, vset, PW = build_ear(bank_words)
    print(f"  bank: {len(vocab)}-way exemplar vocab from {len({t[1] for t in train})} speakers")

    # the live world adapter: minimal substrate + the faculty installed inside it
    agent = WorldAdapter(seeds=())
    world = LiveAudioWorld(agent, ear=ear, bank=bank, vocab=vocab, PW=PW,
                           pca_mu=mu_p, pca_V=V_p, dtw=dtw, target_coverage=0.5, eta=0.3)

    # the stream: real test-speaker utterances (cross-speaker), in order
    import glob
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk = spks[-5:]
    stream = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            stream.append((f, t))
    stream = stream[:N_STREAM_UTT]

    print(f"  streaming {len(stream)} utterances (cross-speaker) through the live adapter...\n")
    print("  trace (first utterances) — word | gold | margin | GRAPH decision:")
    all_rec = []
    theta_hist = []
    for ui, (f, t) in enumerate(stream):
        x, fs = load_flac(f); x = np.asarray(x, np.float64)
        try:
            # the agent acts on words it KNOWS (in its banked vocabulary); OOV deferral is a separate capability
            # (needs an absolute-distance novelty gate, not the relative top1/top2 margin).
            spans = [(w, t0, t1) for (w, t0, t1) in align_utt(x, fs, t) if len(w) >= MINW and w in world.vset]
        except Exception:
            continue
        if not spans:
            continue
        rids = world.ingest_utterance(x, fs, spans)       # PERCEPTION + ingest
        world.step(rids)                                  # TICK: faculty decides + trainer tunes
        theta_hist.append(world.threshold())
        for (rid, word, gold) in rids:
            w_out, decision = world.emit(rid)             # read back the GRAPH's decision
            correct = int(w_out == gold)
            all_rec.append((correct, decision))
            if ui < 4:
                mar = agent.s.node(rid)["attrs"]["margin"]
                mark = "OK" if correct else "x "
                print(f"    [{mark}] {w_out:<12} | {gold:<12} | {mar:.3f} | {decision}")

    # online adaptation + selective-action stats (gold used only to SCORE)
    cor = np.array([c for (c, _d) in all_rec]); dec = np.array([d for (_c, d) in all_rec])
    base = 100 * cor.mean()
    act_mask = dec == "ACT"
    cov = 100 * act_mask.mean()
    act_acc = 100 * cor[act_mask].mean() if act_mask.any() else float("nan")
    def_acc = 100 * cor[~act_mask].mean() if (~act_mask).any() else float("nan")

    print("\n" + "=" * 100)
    print(f"  streamed {len(all_rec)} word-recognitions over {len(theta_hist)} utterances")
    print(f"  gate threshold adapted online: {theta_hist[0]:.3f} -> {theta_hist[-1]:.3f}  (median over stream {np.median(theta_hist):.3f})")
    print(f"    base accuracy (act-on-all):  {base:.1f}%")
    print(f"    ACT set:    {cov:.1f}% coverage,  accuracy {act_acc:.1f}%")
    print(f"    DEFER set:  {100-cov:.1f}% coverage,  accuracy {def_acc:.1f}%")
    print("-" * 100)
    if act_acc >= 93.0 and 35 <= cov <= 65:
        print(f"  LIVE — the strong ear is wired into a streaming world adapter: audio -> wav2vec2 ear (perception) -> Recognition")
        print(f"  nodes -> graph Rules decide ACT/DEFER -> the agent's trainer tunes the gate online ({theta_hist[0]:.3f}->{theta_hist[-1]:.3f}).")
        print(f"  Acting on {cov:.0f}% at {act_acc:.0f}% (vs {base:.0f}% act-on-all), deferring the uncertain rest. Zero Python decision.")
    else:
        print(f"  PARTIAL — pipeline runs end-to-end (cov {cov:.0f}%, ACT acc {act_acc:.1f}%) but off the bar (>=93% @ 35-65% cov);")
        print("  likely the online gate needs more stream to converge, or the margin scale differs live. End-to-end flow works.")
    print("=" * 100)


if __name__ == "__main__":
    main()
