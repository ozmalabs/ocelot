"""iter-26 GATE — does the agent's MULTI-CHANNEL STACK (formant-relation + tracking +
manner/voicing), DERIVED for itself over the iter-25 residual (iter26_stacked_derive),
clear the perceptual ceiling the single formant-relation could not? within-NN past
surface 0.20 toward 0.32, AND/OR cross-NN off chance.

SAME gold-span gate as scripts/iter25_lpc_gate.py (faster-whisper gold word-spans on
LibriSpeech dev-clean -> front-end -> within / cross-speaker DTW consistency,
shuffle-controlled). Front-ends head-to-head on identical gold spans:

  SURFACE        : raw gammatone band trajectory (the 0.20-ceiling baseline)
  FORMANT (i25)  : iter-25 spacing over waveform-LPC true formants (no track)
  MANNER         : the agent's phonology manner/voicing channel ALONE        -- (b)
  STACK (i26)    : formant+track ++ manner (the agent's full derived stack)  -- (a)+(c)

CROSS-NN is the key (VTL-dominated). within-NN the bar. Refs: surface within ~0.20 /
cross ~chance; shallow-CNN gold-span 0.32; SSL 0.49.

LPC order = the agent's waveform-LPC spec rule fs/1000+2. No tuning, no search.

Run: python -m scripts.iter26_stacked_gate [n_speakers] [utts_per_spk]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from domains.stacked_representation import apply_stacked
from substrate_rs import Substrate
from scripts.continuous_speech_recognition import frames_of, words_of
from scripts.iter14_segmentation_consistency import (
    within_speaker_dtw, shuffle_within, intra_inter_separation,
)
from scripts.iter15_goldspan_gate import gold_spans, cross_separation, cross_nn


def _shuf(xs, seed=0):
    rng = random.Random(seed + 99)
    ys = list(xs)
    rng.shuffle(ys)
    return ys


def report_frontend(tag, chunks, probe):
    n_words = len(set(c[1] for c in chunks))
    wsep, wim, wxm, wnin, _ = intra_inter_separation(chunks)
    sh_ch = [(b, w, s) for (b, _, s), w in
             zip(chunks, _shuf([c[1] for c in chunks]))]
    wssep, _, _, _, _ = intra_inter_separation(sh_ch)
    wnn, wnt, _ = within_speaker_dtw(chunks, max_n=probe)
    wsh, _, _ = shuffle_within(chunks, max_n=probe)
    xsep, xim, xxm, xnin, _ = cross_separation(chunks)
    xnn, xnt = cross_nn(chunks)
    print(f"\n[{tag}]  segs={len(chunks)}  distinct words={n_words}  "
          f"chance~{1.0/max(n_words,1):.3f}")
    print(f"  WITHIN sep  {wsep:+.3f}  (intra {wim:.3f} < inter {wxm:.3f}? "
          f"n={wnin})  [shuffle {wssep:+.3f}]")
    print(f"  WITHIN NN   {wnn:.3f}   (n={wnt})  [shuffle {wsh:.3f}]")
    print(f"  CROSS  sep  {xsep:+.3f}  (intra {xim:.3f} < inter {xxm:.3f}? "
          f"n={xnin})")
    print(f"  CROSS  NN   {xnn:.3f}   (n={xnt})  [chance {1.0/max(n_words,1):.3f}]")
    return {"within_nn": wnn, "within_nn_shuf": wsh, "within_sep": wsep,
            "within_sep_shuf": wssep, "cross_nn": xnn, "cross_sep": xsep,
            "chance": 1.0 / max(n_words, 1)}


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    probe = int(os.environ.get("PROBE", "450"))
    nsp = int(os.environ.get("NSPACINGS", "4"))
    random.seed(1)
    np.random.seed(1)

    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_spk]
    sel = []
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        sel.extend(ps[:utts])
    print("=== iter-26 GATE: the agent's multi-channel STACK ===")
    print(f"LibriSpeech dev-clean: {len(spk_sorted)} speakers x <= {utts} utts "
          f"= {len(sel)} utts  (n_spacings={nsp})")

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + gammatone framing...")
    t0 = time.time()
    raw = []
    audio = []
    gold_idx = []
    n_used = 0
    for path, sp, ch, ut, transcript in sel:
        try:
            x, fs = SL.load_flac_8k(path)
        except Exception:
            continue
        dur = len(x) / fs
        if dur < 0.4:
            continue
        M = frames_of(x, fs)
        nf = M.shape[0]
        if nf < 4:
            continue
        try:
            gs = gold_spans(wmodel, path)
        except Exception:
            gs = []
        spans = []
        for w, ts, te in gs:
            fa = int(round(ts / dur * nf))
            fb = int(round(te / dur * nf))
            fa = max(0, min(fa, nf - 1))
            fb = max(fa + 1, min(fb, nf))
            if len(w) >= 3 and fb - fa >= 2:
                spans.append((w, fa, fb))
        if not spans:
            continue
        words = words_of(transcript)
        raw.append((M, words, sp))
        audio.append((x, fs))
        gold_idx.append((len(raw) - 1, spans))
        n_used += 1
    print(f"  {n_used} utts framed + aligned ({time.time()-t0:.0f}s); "
          f"gold segs {sum(len(g[1]) for g in gold_idx)}")
    if n_used < 8:
        print("Too few usable utterances — aborting.")
        return

    def gold_chunks(normed):
        out = []
        for ridx, spans in gold_idx:
            M = normed[ridx][0]
            spk = normed[ridx][2]
            nf = M.shape[0]
            for w, fa, fb in spans:
                a = max(0, min(fa, nf - 1))
                b = max(a + 1, min(fb, nf))
                seg = np.asarray(M[a:b], dtype=np.float64)
                if seg.shape[0] >= 2:
                    out.append((seg, w, spk))
        return out

    surface = [(M, w, s) for M, w, s in raw]

    def build(channels, track):
        rep = []
        for (M, w, s), (x, fs2) in zip(raw, audio):
            F = apply_stacked(x, fs2, M=M, n_spacings=nsp, substrate=Substrate(),
                              channels=channels, track=track)
            if F.shape[0] != M.shape[0]:
                nf = M.shape[0]
                G = np.zeros((nf, F.shape[1]), dtype=F.dtype)
                m = min(nf, F.shape[0])
                G[:m] = F[:m]
                F = G
            rep.append((F, w, s))
        return rep

    formant = build("formant", False)
    manner = build("manner", True)
    stack = build("both", True)

    print("\n" + "=" * 70)
    print("GOLD-SPAN consistency — SURFACE / FORMANT / MANNER / STACK")
    print("  refs: surface within ~0.20 / cross ~chance; shallow-CNN 0.32; SSL 0.49")
    print("=" * 70)

    results = {}
    for tag, normed in [("SURFACE (raw bands)", surface),
                        ("FORMANT (i25 spacing, true formants)", formant),
                        ("MANNER (agent phonology channel)", manner),
                        ("STACK (i26: formant+track ++ manner)", stack)]:
        results[tag] = report_frontend(tag, gold_chunks(normed), probe)

    print("\n" + "=" * 70)
    print("GATE VERDICT — within-NN vs surface 0.20 / 0.32; cross-NN vs chance")
    print("=" * 70)
    surf = results["SURFACE (raw bands)"]
    f = results["FORMANT (i25 spacing, true formants)"]
    st = results["STACK (i26: formant+track ++ manner)"]
    print(f"  SURFACE  within-NN {surf['within_nn']:.3f}  cross-NN "
          f"{surf['cross_nn']:.3f}  (chance {surf['chance']:.3f})")
    print(f"  FORMANT  within-NN {f['within_nn']:.3f}  cross-NN {f['cross_nn']:.3f}  "
          f"cross-sep {f['cross_sep']:+.3f}")
    print(f"  STACK    within-NN {st['within_nn']:.3f} (shuf "
          f"{st['within_nn_shuf']:.3f})  cross-NN {st['cross_nn']:.3f}  "
          f"cross-sep {st['cross_sep']:+.3f}")
    within_clears = st["within_nn"] >= surf["within_nn"] and \
        st["within_nn"] > st["within_nn_shuf"] + 0.03
    cross_off = st["cross_nn"] > surf["cross_nn"] + 0.03 and \
        st["cross_nn"] > st["chance"] * 2
    if st["within_nn"] >= 0.32 and within_clears:
        print("  >>> CLEARS: STACK within-NN >= 0.32 above shuffle.")
    elif within_clears and cross_off:
        print("  >>> PARTIAL+: STACK clears surface within AND moves cross off chance.")
    elif within_clears:
        print("  >>> STACK reaches/clears surface within-NN (above shuffle); "
              "check cross.")
    elif cross_off:
        print("  >>> CROSS LIFT: STACK moves cross-NN off chance above surface.")
    else:
        print("  >>> NO CLEARANCE: report residual honestly.")


if __name__ == "__main__":
    main()
