"""PHASE 0 — the fail-fast test of the generative-speaker programme's riskiest assumption (no synthesis, no loop).

The whole programme rests on: a per-speaker FITTED SOURCE-FILTER makes the formant trajectory SPEAKER-INVARIANT (the
speaker factors into a fitted filter) where every LINEAR proxy failed. Test it CHEAPLY with an ORACLE STATIC FIT:
  per speaker, fit one all-pole LPC filter on their VOICED speech (oracle: fit on the speaker's OWN data = easiest case);
  represent each word's CONTENT as the per-frame LPC envelope with the speaker's fitted filter (mean envelope) DIVIDED
  OUT (subtracted in log) -> the formant DEVIATIONS = content, speaker-factored; run cross-speaker recognition on it.
Compare: COLD-START (CMVN cochleagram, ~17-25%) | PHASE-0 (speaker-filter-removed LPC content) | WITHIN-speaker CEILING.
Pre-committed bar (the agent's): PHASE-0 must beat cold-start (and the warp's +1.7) by recovering >= HALF the cold-start
-> within-speaker gap. KILL if it merely matches the linear warp -> the speaker does NOT factor into a fitted filter ->
the generative programme is WRONG, the wall is the training-free ceiling.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_speaker_filter
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
from domains.lpc_formant_representation import lpc_envelope_matrix

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
    from domains.cmvn import apply_cmvn
    return _l2rows(apply_cmvn(M))


def lpc_env(M):
    return np.asarray(lpc_envelope_matrix(M, order=LPC_ORDER), dtype=np.float32)   # log all-pole envelope (frames x bands)


def recog(fr, bank, vocab, PW):
    dl = np.diff(fr, axis=0); dl = dl / (np.linalg.norm(dl, axis=1, keepdims=True) + 1e-9) if len(fr) > 1 else fr
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
    print("PHASE 0 — speaker-fitted LPC filter removal vs cold-start vs within-speaker ceiling (the fail-fast)")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    # gather words per speaker: raw cochleagram + cold feat + LPC envelope; speaker filter = mean LPC envelope
    def gather(spk_list, cap):
        spk_words = defaultdict(list); spk_env = defaultdict(list); nu = 0
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
                    M = _coch(seg); E = lpc_env(M)
                    spk_words[sp].append((w, cold_feat(M), E))
                    spk_env[sp].append(E)
            if nu >= cap:
                break
        spk_filter = {sp: np.concatenate(spk_env[sp], 0).mean(0) for sp in spk_env if spk_env[sp]}
        return spk_words, spk_filter

    print("  gathering train + test (cochleagram + LPC envelope + speaker filters)...", flush=True)
    train_words, train_filter = gather(train_spk, N_BANK)
    test_words, test_filter = gather(test_spk, 999)

    # bank: cold + content (LPC envelope - speaker filter), per train speaker
    bank_cold = defaultdict(list); bank_cont = defaultdict(list); cnt = defaultdict(int)
    for sp, words in train_words.items():
        flt = train_filter[sp]
        for (w, cf, E) in words:
            if cnt[w] >= KMAX:
                continue
            bank_cold[w].append(cf); bank_cont[w].append(_l2rows(E - flt)); cnt[w] += 1
    vocab = [w for w, e in sorted(bank_cold.items(), key=lambda kv: -len(kv[1]))[:NWAY] if len(e) >= 2]
    vset = set(vocab)
    PWc = np.stack([np.stack([e.mean(0) for e in bank_cold[w]]).mean(0) for w in vocab]); PWc /= (np.linalg.norm(PWc, axis=1, keepdims=True) + 1e-9)
    PWk = np.stack([np.stack([e.mean(0) for e in bank_cont[w]]).mean(0) for w in vocab]); PWk /= (np.linalg.norm(PWk, axis=1, keepdims=True) + 1e-9)
    print(f"  {len(vocab)}-way; {len(train_spk)} train / {len(test_spk)} test spk\n", flush=True)

    # CROSS-SPEAKER cold + phase0
    test_toks = []
    for sp, words in test_words.items():
        flt = test_filter.get(sp)
        for (w, cf, E) in words:
            if w in vset and flt is not None:
                test_toks.append((w, cf, _l2rows(E - flt)))
    test_toks = test_toks[:N_TEST]
    cold_x = 100 * np.mean([recog(cf, bank_cold, vocab, PWc) == w for (w, cf, _ct) in test_toks])
    phase0 = 100 * np.mean([recog(ct, bank_cont, vocab, PWk) == w for (w, _cf, ct) in test_toks])

    # WITHIN-SPEAKER ceiling: per train speaker, bank half their words, test the other half (cold-start)
    within = []
    for sp, words in list(train_words.items())[:6]:
        ww = [(w, cf) for (w, cf, _E) in words if w in vset]
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
    print(f"    PHASE-0 (speaker-LPC-filter removed):   {phase0:.1f}%  ({phase0-cold_x:+.1f})")
    print(f"    WITHIN-SPEAKER ceiling (same speaker):  {within_ceil:.1f}%")
    gap = within_ceil - cold_x
    recovered = (phase0 - cold_x) / gap if gap > 1 else 0.0
    print(f"    gap cold->within {gap:.1f}; PHASE-0 recovered {100*recovered:.0f}% of it")
    print("-" * 100)
    if phase0 >= cold_x + 3 and recovered >= 0.5:
        print(f"  KEEP — PHASE 0 PASSES: the speaker FACTORS into a fitted filter (cross-speaker {cold_x:.1f}->{phase0:.1f}, recovered")
        print(f"  {100*recovered:.0f}% of the gap to within-speaker {within_ceil:.1f}) -- decisively past the linear warp's +1.7. The")
        print("  generative premise holds; pour the foundation (P1 synthesiser -> P2 inversion -> P3 online fit).")
    elif phase0 >= cold_x + 1.7:
        print(f"  WEAK — beats cold-start (+{phase0-cold_x:.1f}) but only ~warp territory, recovered {100*recovered:.0f}% (<half). The fitted")
        print("  filter is barely better than the affine warp; the speaker doesn't cleanly factor. Programme on thin ice. Honest.")
    else:
        print(f"  STOP — PHASE 0 KILLS THE PROGRAMME: speaker-LPC-filter removal {phase0:.1f} ~= cold-start {cold_x:.1f}; the speaker does")
        print("  NOT factor into a fitted filter (no better than the linear proxies). No closed-loop search rescues a premise that")
        print("  fails open-loop with ORACLE params. The cross-speaker wall IS the training-free ceiling. Honest, fail-fast.")
    print("=" * 100)


if __name__ == "__main__":
    main()
