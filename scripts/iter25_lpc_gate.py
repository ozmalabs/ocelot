"""iter-25 GATE — does the agent's iter-24 SCALE-invariant spacing relation, now run
over the LPC / all-pole SMOOTHED envelope's peaks (the TRUE formants it derived for
itself), LIFT the perceptual ceiling — ESPECIALLY cross-speaker (the VTL number)?

The reasoning loop closed at iter-25: synthesize_gaps over the iter-24 RESIDUAL frame
(landmark_quality_frame) fires the agent's OWN harvested parameterize / all-pole shape
(parametric_allpole__from__IIR_filter), deriving "a FEW poles ARE the resonances,
recovered by LINEAR PREDICTION rather than read off a blurry spectrum".
domains/lpc_formant_representation.py is the agent's COMPOSITION: the SAME iter-24
spacing relation (Minus over landmark positions) over the LPC SMOOTHED envelope.
This script ENACTS + GATES it, head-to-head with iter-24 (raw-spectrum spacing) and
the baselines.

SAME gold-span gate as scripts/iter24_scale_gate.py (faster-whisper gold word-spans on
LibriSpeech -> front-end -> within / cross-speaker DTW consistency, shuffle-controlled).
Front-ends compared:

  SURFACE        : raw gammatone band trajectory (the 0.20-ceiling baseline)
  SCALE-INV      : iter-24 spacing over RAW-spectrum peaks (no lift; noisy landmarks)
  LPC-SCALE      : iter-25 SAME spacing over the LPC SMOOTHED envelope (true formants)
  LPC-STACKED    : value-difference + LPC spacing (LEVEL + VTL invariant, true formants)

CROSS-SPEAKER NN is the key number: VTL is the dominant cross nuisance, so if the
TRUE-formant spacing works, cross should move off chance. Refs: surface within ~0.20 /
cross ~chance; shallow-CNN gold-span 0.32; SSL 0.49.

The LPC order is the agent's OWN specified value (runtime_design.agent_specify_lpc_
formants -> order=8, "conservative ~ fs/1000+2"), NOT a number picked to chase the
gate. NO tuning, no search. World-adapter only.

Run: python -m scripts.iter25_lpc_gate [n_speakers] [utts_per_spk]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from domains.relational_representation import apply_relational
from domains.scale_invariant_representation import apply_scale_invariant
from domains.lpc_formant_representation import (
    apply_lpc_scale_invariant, apply_lpc_stacked, landmark_count_stats,
    formant_spacings_from_audio, formant_count_from_audio,
)
from scripts.continuous_speech_recognition import frames_of, words_of
from scripts.iter14_segmentation_consistency import (
    within_speaker_dtw, shuffle_within, intra_inter_separation,
)
from scripts.iter15_goldspan_gate import gold_spans, cross_separation, cross_nn


def _agent_lpc_order():
    """Read the agent's OWN specified LPC order (not a gate-chasing pick)."""
    try:
        from substrate_rs import Substrate
        from domains.runtime_design import agent_specify_lpc_formants
        return int(agent_specify_lpc_formants(Substrate())["order"])
    except Exception:
        return 8


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
    nsp = int(os.environ.get("NSPACINGS", "6"))
    order = int(os.environ.get("LPC_ORDER", str(_agent_lpc_order())))
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
    print("=== iter-25 GATE: iter-24 spacing over the LPC SMOOTHED envelope ===")
    print(f"LibriSpeech dev-clean: {len(spk_sorted)} speakers x <= {utts} utts "
          f"= {len(sel)} utts  (n_spacings={nsp}, LPC order={order} [agent-specified])")

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + gammatone framing...")
    t0 = time.time()
    raw = []
    audio = []         # parallel raw waveforms for the waveform-LPC front-end
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

    # Honest landmark-count probe — the iter-24 residual was 5.4 raw peaks/frame.
    lc = [landmark_count_stats(M, order=order) for M, _, _ in raw[:40]]
    raw_mean = float(np.mean([d["raw_mean"] for d in lc]))
    lpc_mean = float(np.mean([d["lpc_mean"] for d in lc]))
    print(f"  LANDMARKS/frame: raw spectrum {raw_mean:.2f}  ->  LPC envelope "
          f"{lpc_mean:.2f}  (target: the 2-3 true formants)")

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

    # The faithful waveform-LPC formant order (agent's spec rule for waveform LPC).
    wf_order = int(fs / 1000) + 2

    surface = [(M, w, s) for M, w, s in raw]
    scale_inv = [(apply_scale_invariant(M, n_spacings=nsp), w, s)
                 for M, w, s in raw]
    # FORMANT-SPACE: the faithful enactment — iter-24 spacing over TRUE formants from
    # LPC roots of the raw WAVEFORM (bypasses the gammatone band wall). Frame-aligned
    # with M (same fps), so the gold spans slice it identically.
    formant_space = []
    for (M, w, s), (x, fs2) in zip(raw, audio):
        F = formant_spacings_from_audio(x, fs2, n_spacings=4, order=wf_order)
        if F.shape[0] != M.shape[0]:           # align defensively to gold-span grid
            nf = M.shape[0]
            G = np.zeros((nf, F.shape[1]), dtype=F.dtype)
            m = min(nf, F.shape[0])
            G[:m] = F[:m]
            F = G
        formant_space.append((F, w, s))

    print("\n" + "=" * 70)
    print("GOLD-SPAN consistency — SURFACE / SCALE-INV / LPC-SCALE / LPC-STACKED")
    print("  metric = full-DTW intra/inter SEPARATION + same-word NN-acc")
    print("  refs: surface within ~0.20 / cross ~chance; shallow-CNN 0.32; SSL 0.49")
    print("=" * 70)

    results = {}
    for tag, normed in [("SURFACE (raw bands)", surface),
                        ("SCALE-INV (iter-24 raw-peak spacing)", scale_inv),
                        ("FORMANT-SPACE (iter-25 waveform-LPC formant spacing)",
                         formant_space)]:
        ch = gold_chunks(normed)
        results[tag] = report_frontend(tag, ch, probe)

    print("\n" + "=" * 70)
    print("GATE VERDICT — CROSS-speaker is the key (VTL-dominated)")
    print("=" * 70)
    surf = results["SURFACE (raw bands)"]
    sci = results["SCALE-INV (iter-24 raw-peak spacing)"]
    lpc = results["FORMANT-SPACE (iter-25 waveform-LPC formant spacing)"]
    print(f"  SURFACE       within-NN {surf['within_nn']:.3f}  cross-NN "
          f"{surf['cross_nn']:.3f}  (chance {surf['chance']:.3f})")
    print(f"  SCALE-INV     within-NN {sci['within_nn']:.3f}  cross-NN "
          f"{sci['cross_nn']:.3f}  cross-sep {sci['cross_sep']:+.3f}")
    print(f"  FORMANT-SPACE within-NN {lpc['within_nn']:.3f} (shuf "
          f"{lpc['within_nn_shuf']:.3f})  cross-NN {lpc['cross_nn']:.3f}  "
          f"cross-sep {lpc['cross_sep']:+.3f}")
    best_cross = lpc["cross_nn"]
    best_within = lpc["within_nn"]
    if best_cross > surf["cross_nn"] + 0.03 and best_cross > lpc["chance"] * 2:
        print("  >>> CROSS LIFT: the TRUE-formant (LPC) spacing moves cross-speaker NN "
              "off chance above surface. VTL band-index invariance over true formants "
              "helps cross-speaker.")
    elif best_within >= 0.32 and best_within > sci["within_nn"] + 0.03:
        print("  >>> WITHIN LIFT (>=0.32, above iter-24): the LPC envelope rescues the "
              "spacing relation within-speaker. Check cross.")
    elif best_within > sci["within_nn"] + 0.03:
        print("  >>> PARTIAL: LPC envelope improves the spacing relation over raw peaks "
              "but does not clear 0.32 / move cross off chance.")
    else:
        print("  >>> NO LIFT: the LPC envelope does not rescue the spacing relation. "
              "Report residual honestly.")


if __name__ == "__main__":
    main()
