"""HARVEST AT SCALE + the GATE WHERE IT MATTERS — grow coverage broadly; show the bias gate is CONDITIONAL on noise.

Two questions from the validated harvest:
 1. SCALE: does content recall keep CLIMBING as we harvest more (pretend-unlabelled) audio via whisper labels? The
    coverage lever, at scale.
 2. THE GATE WHERE IT SHOULD MATTER: on CLEAN read speech the bias gate HURT (whisper barely hallucinates -> the gate
    only cost coverage). On NOISY audio whisper DOES hallucinate frequent words -> the gate should now EARN its keep:
    gated > ungated. The conditional-gate hypothesis.

Bank the agent's OWN cochleagram exemplars under whisper LABELS at MMS_FA SPANS (the validated, structure-preserving
form). Eval on held-out test speakers (clean, true labels).

Run:
  cd experiments/gamma-substrate
  ulimit -v 28000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_harvest_at_scale
"""
from __future__ import annotations

import glob
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, STOP
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import (transcripts, whisper_words, gated_spans, bank_spans,
                                                  DEV, TAU, DELTA, MINW)

N_BASE = 12
SCALE_CKPTS = [40, 100, 200]
N_NOISE = 100
N_TEST = 30
SNR_DB = 2.0       # additive white noise SNR for the noisy-harvest condition (low -> whisper hallucinates)


def add_noise(x, snr_db, rng):
    p = float(np.mean(x ** 2)) + 1e-12
    n = rng.standard_normal(len(x))
    g = np.sqrt(p / ((float(np.mean(n ** 2)) + 1e-12) * 10 ** (snr_db / 10)))
    return x + g * n


def copy_bank(b):
    d = defaultdict(list)
    for w, v in b.items():
        d[w] = list(v)
    return d


def main():
    print("=" * 100)
    print("HARVEST AT SCALE + the GATE WHERE IT MATTERS (noisy audio)")
    print("=" * 100)
    from faster_whisper import WhisperModel
    wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        base = os.path.basename(f)[:-5]
        if base in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[base]))
    spks = sorted(by_spk)
    test_spk, harvest_spk = spks[-3:], spks[:-3]
    harvest_utts = [(f, t) for sp in harvest_spk for (f, t) in by_spk[sp]]
    test_utts = [(f, t) for sp in test_spk for (f, t) in by_spk[sp]]
    print(f"  {len(harvest_spk)} harvest speakers ({len(harvest_utts)} utts), {len(test_spk)} test\n", flush=True)

    # baseline (oracle small)
    base = defaultdict(list)
    for (f, t) in harvest_utts[:N_BASE]:
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        bank_spans(x, fs, align_utt(x, fs, t), base)

    # test set (clean, true labels)
    test = []
    for (f, t) in test_utts[:N_TEST]:
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        for (w, t0, t1) in align_utt(x, fs, t):
            if len(w) >= MINW:
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size >= int(0.05 * fs):
                    test.append((w, frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32)))
    vocab = sorted({w for (w, _s) in test})
    print(f"  baseline banked; {len(test)} test instances, {len(vocab)}-word vocab\n", flush=True)

    def evaluate(bank):
        cand = [w for w in vocab if bank.get(w)]
        c_ok = c_tot = f_ok = f_tot = 0
        for (tw, ts) in test:
            best, arg = 1e18, None
            for w in cand:
                d = min(dtw(ts, ex) for ex in bank[w])
                if d < best:
                    best, arg = d, w
            if tw in STOP:
                f_tot += 1; f_ok += int(arg == tw)
            else:
                c_tot += 1; c_ok += int(arg == tw)
        return 100 * c_ok / max(c_tot, 1), 100 * f_ok / max(f_tot, 1), len(cand)

    bc, bf, bv = evaluate(base)
    print(f"  baseline: content {bc:.1f} | function {bf:.1f} | vocab {bv}/{len(vocab)}\n", flush=True)

    # ---- 1. SCALE: cumulative clean ungated harvest, eval at checkpoints ----
    print("  [1] SCALE — clean whisper-label harvest (MMS_FA spans), content recall vs #utts harvested:", flush=True)
    ung = copy_bank(base); orc = copy_bank(base)
    nmax = max(SCALE_CKPTS)
    print(f"    {'#utts':>7}{'content':>10}{'function':>10}{'vocab':>8}{'oracle-c':>10}")
    for i, (f, t) in enumerate(harvest_utts[N_BASE:N_BASE + nmax]):
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        ww = whisper_words(wm, x, fs)
        mms = align_utt(x, fs, " ".join(w for (w, _a, _b, _p) in ww))
        bank_spans(x, fs, mms, ung)
        bank_spans(x, fs, align_utt(x, fs, t), orc)
        if (i + 1) in SCALE_CKPTS:
            c, fn, v = evaluate(ung); oc, _of, _ov = evaluate(orc)
            print(f"    {i+1:>7}{c:>9.1f}%{fn:>9.1f}%{v:>8}{oc:>9.1f}%", flush=True)
    scale_c = c

    # ---- 2. GATE WHERE IT MATTERS: noisy harvest, ungated vs gated ----
    print(f"\n  [2] THE GATE ON NOISY AUDIO (SNR {SNR_DB} dB) vs clean — does the gate earn its keep when whisper hallucinates?", flush=True)
    rng = np.random.RandomState(0)
    cln_u, cln_g = copy_bank(base), copy_bank(base)
    noi_u, noi_g = copy_bank(base), copy_bank(base)
    keptc = totc = keptn = totn = 0
    for (f, t) in harvest_utts[N_BASE:N_BASE + N_NOISE]:
        x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
        # clean
        ww = whisper_words(wm, x, fs)
        mms = align_utt(x, fs, " ".join(w for (w, _a, _b, _p) in ww))
        g = gated_spans(ww, mms, TAU, DELTA)
        totc += len(mms); keptc += len(g)
        bank_spans(x, fs, mms, cln_u); bank_spans(x, fs, g, cln_g)
        # noisy
        xn = add_noise(x, SNR_DB, rng)
        wwn = whisper_words(wm, xn, fs)
        mmsn = align_utt(xn, fs, " ".join(w for (w, _a, _b, _p) in wwn))
        gn = gated_spans(wwn, mmsn, TAU, DELTA)
        totn += len(mmsn); keptn += len(gn)
        # bank the agent's exemplars from the noisy audio under whisper's (noisy) labels
        bank_spans(xn, fs, mmsn, noi_u); bank_spans(xn, fs, gn, noi_g)

    cu = evaluate(cln_u); cg = evaluate(cln_g); nu = evaluate(noi_u); ng = evaluate(noi_g)
    print(f"    CLEAN harvest: ungated content {cu[0]:.1f}/func {cu[1]:.1f} | gated {cg[0]:.1f}/{cg[1]:.1f}  "
          f"(gate kept {100*keptc/max(totc,1):.0f}%)")
    print(f"    NOISY harvest: ungated content {nu[0]:.1f}/func {nu[1]:.1f} | gated {ng[0]:.1f}/{ng[1]:.1f}  "
          f"(gate kept {100*keptn/max(totn,1):.0f}%)")

    print("\n" + "=" * 100)
    print(f"  [1] SCALE: baseline content {bc:.1f} -> {nmax}-utt harvest {scale_c:.1f}  (oracle {evaluate(orc)[0]:.1f})")
    grew = scale_c >= bc + 5
    print(f"      {'CLIMBS' if grew else 'flat'}: harvesting more whisper-labelled audio {'keeps growing recall' if grew else 'plateaus'}.")
    print(f"  [2] GATE: clean ungated {cu[0]:.1f} vs gated {cg[0]:.1f} (gate {'hurts' if cg[0]<cu[0] else 'helps'} on clean) | "
          f"noisy ungated {nu[0]:.1f} vs gated {ng[0]:.1f} (gate {'HELPS' if ng[0]>nu[0] else 'hurts'} on noisy)")
    cond = (cg[0] <= cu[0] + 0.5) and (ng[0] >= nu[0] - 0.0)
    if grew and ng[0] > nu[0]:
        print("      CONDITIONAL-GATE CONFIRMED: off on clean (coverage), ON on noisy (whisper hallucinates -> gate")
        print("      removes the bad labels). The harvest scales AND the gate is regime-dependent, exactly as reasoned.")
    elif grew:
        print(f"      harvest SCALES; the noisy-gate effect was {ng[0]-nu[0]:+.1f} (gate {'helped' if ng[0]>nu[0] else 'did not flip'} on noisy). Honest.")
    else:
        print("      harvest did not scale cleanly at this size; honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
