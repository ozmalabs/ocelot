"""PHASE 0 (corrected, form i) — the LAST shot at the generative premise: SCALE-NORMALISED LPC (content-preserving).

The first Phase-0 ran form (ii) -- subtract the speaker's mean LPC envelope = divide out the filter where the FORMANTS
(content) LIVE -> destroyed content (1.9, far below cold-start 11.5). The agent ruled BOTCHED (content-destruction !=
the pre-committed "matches-warp" kill) and pre-registered form (i): SCALE-NORMALISE the pole structure (remove tract
length/resonance scale) while PRESERVING the formant pattern -- apply_lpc_scale_invariant. Recognise cross-speaker on it.
PRE-REGISTERED (the agent's): KEEP if >= 28.8 (beats cold-start 11.5 AND clears half the gap to within-speaker 46.1);
KILL if ~13 (warp territory -> speaker reduces to a linear warp, removal buys nothing); KILL if sub-cold-start (second
artifact, but BOTH authored forms then exhausted -> the premise is honestly, finally killed). THE LAST SHOT.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_scale_invariant
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
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, FS
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from domains.filter_settings import cochleagram
from domains.lpc_formant_representation import apply_lpc_scale_invariant
from domains.cmvn import apply_cmvn

N_BANK = 220
KMAX = 5
NWAY = 400
N_TEST = 260
PRUNE = 30
LPC_ORDER = 12
FPS = 50


def _coch(x):
    nf = max(4, int(len(x) / FS * FPS))
    return np.asarray(cochleagram(np.asarray(x, dtype=np.float64), FS, n_frames=nf), dtype=np.float64)


def _l2rows(M):
    M = np.asarray(M, np.float32)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def cold_feat(M):
    return _l2rows(apply_cmvn(M))


def si_feat(M):
    return _l2rows(apply_lpc_scale_invariant(M, order=LPC_ORDER))   # scale-invariant LPC: tract scale out, formant pattern kept


def recog(fr, bank, vocab, PW):
    pv = fr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
    top = np.argsort(-(PW @ pv))[:PRUNE]
    best, arg = 1e18, None
    for i in top:
        c = vocab[i]
        d = min(dtw(fr, e) for e in bank[c])
        if d < best:
            best, arg = d, c
    return arg


def main():
    print("=" * 100)
    print("PHASE 0 (form i) — SCALE-INVARIANT LPC content vs cold-start vs within-speaker ceiling (the last shot)")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    def gather(spk_list, cap):
        spk_words = defaultdict(list); nu = 0
        for sp in spk_list:
            for (f, t) in by_spk[sp]:
                if nu >= cap:
                    break
                x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nu += 1
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) < MINW:
                        continue
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size < int(0.05 * fs):
                        continue
                    M = _coch(seg)
                    spk_words[sp].append((w, cold_feat(M), si_feat(M)))
            if nu >= cap:
                break
        return spk_words

    print("  gathering (cochleagram + scale-invariant LPC)...", flush=True)
    train_words = gather(train_spk, N_BANK)
    test_words = gather(test_spk, 999)

    bank_cold = defaultdict(list); bank_si = defaultdict(list); cnt = defaultdict(int)
    for sp, words in train_words.items():
        for (w, cf, si) in words:
            if cnt[w] >= KMAX:
                continue
            bank_cold[w].append(cf); bank_si[w].append(si); cnt[w] += 1
    vocab = [w for w, e in sorted(bank_cold.items(), key=lambda kv: -len(kv[1]))[:NWAY] if len(e) >= 2]
    vset = set(vocab)
    PWc = np.stack([np.stack([e.mean(0) for e in bank_cold[w]]).mean(0) for w in vocab]); PWc /= (np.linalg.norm(PWc, axis=1, keepdims=True) + 1e-9)
    PWs = np.stack([np.stack([e.mean(0) for e in bank_si[w]]).mean(0) for w in vocab]); PWs /= (np.linalg.norm(PWs, axis=1, keepdims=True) + 1e-9)
    print(f"  {len(vocab)}-way; {len(train_spk)} train / {len(test_spk)} test spk\n", flush=True)

    test_toks = []
    for sp, words in test_words.items():
        for (w, cf, si) in words:
            if w in vset:
                test_toks.append((w, cf, si))
    test_toks = test_toks[:N_TEST]
    cold_x = 100 * np.mean([recog(cf, bank_cold, vocab, PWc) == w for (w, cf, _si) in test_toks])
    phase0 = 100 * np.mean([recog(si, bank_si, vocab, PWs) == w for (w, _cf, si) in test_toks])

    within = []
    for sp, words in list(train_words.items())[:6]:
        ww = [(w, cf) for (w, cf, _si) in words if w in vset]
        if len(ww) < 16:
            continue
        h = len(ww) // 2
        b = defaultdict(list)
        for (w, cf) in ww[:h]:
            b[w].append(cf)
        pw = np.stack([np.stack([e.mean(0) for e in b[w]]).mean(0) for w in b]); pw /= (np.linalg.norm(pw, axis=1, keepdims=True) + 1e-9)
        bv = list(b)
        ok = [int(recog(cf, b, bv, pw) == w) for (w, cf) in ww[h:] if w in b]
        if ok:
            within.append(100 * np.mean(ok))
    within_ceil = np.mean(within) if within else float("nan")

    print("\n" + "=" * 100)
    print(f"  @{len(vocab)}-way, {len(test_toks)} cross-speaker tokens:")
    print(f"    COLD-START (CMVN cochleagram):          {cold_x:.1f}%")
    print(f"    PHASE-0 form i (scale-invariant LPC):   {phase0:.1f}%  ({phase0-cold_x:+.1f})")
    print(f"    WITHIN-SPEAKER ceiling:                 {within_ceil:.1f}%")
    gap = within_ceil - cold_x
    rec = (phase0 - cold_x) / gap if gap > 1 else 0.0
    halfgap = cold_x + gap / 2
    print(f"    pre-registered: KEEP >= {halfgap:.1f} (half-gap); recovered {100*rec:.0f}% of the cold->within gap")
    print("-" * 100)
    if phase0 >= halfgap:
        print(f"  KEEP — PHASE 0 PASSES (form i): scale-invariant LPC factors the speaker (cross-speaker {cold_x:.1f}->{phase0:.1f},")
        print(f"  recovered {100*rec:.0f}% of the gap to within-speaker {within_ceil:.1f}, decisively past warp). The generative premise")
        print("  holds; pour the foundation (P1 synth -> P2 inversion -> P3 online fit).")
    elif phase0 <= cold_x + 2:
        print(f"  KILL — both authored forms exhausted: form-i {phase0:.1f} ~= cold-start {cold_x:.1f} (warp territory / below). The speaker")
        print("  does NOT factor into a fitted filter even with oracle params, in EITHER form. The cross-speaker wall IS the")
        print("  training-free ceiling. The generative programme is honestly, finally killed. Fail-fast complete.")
    else:
        print(f"  PARTIAL — form-i beats cold-start (+{phase0-cold_x:.1f}) but under the half-gap bar ({halfgap:.1f}); real factoring but")
        print(f"  modest, recovered {100*rec:.0f}%. Premise has a pulse but doesn't clear the KEEP bar -- the agent's call. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
