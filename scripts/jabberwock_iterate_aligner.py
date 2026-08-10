"""ITERATE THE ALIGNER — the agent's "re-align with the v1 phone bank" (EM forced alignment).

The holdout proof read a never-banked word from phones at 6x chance top-3, but top-1 was noisy and UNIFORM align
beat the agent's sonority -- the ALIGNER is the limiter. The agent's fix: iterate it. v1 phones are banked by a
crude uniform alignment; use those phone MODELS to RE-ALIGN each training word to its CMUdict phone sequence
ACOUSTICALLY (a forced-path / Viterbi alignment, cost = frame->phone-centroid distance, monotonic in CMU order),
re-bank cleaner phone exemplars, and repeat. This is EM: better phones -> better boundaries -> better phones.

Measures the OOV holdout read (top-1 / top-3, never-banked content words read from parts) at each pass:
  v1 uniform  ->  v2 forced(v1 models)  ->  v3 forced(v2 models).
If recall climbs and converges, the aligner WAS the limiter and EM is the fix (no new model, no labels --
the CMUdict order + the phones' own acoustics bootstrap the boundaries).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_iterate_aligner
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac
from scripts.jabberwock_reads_oov_from_phones import frames, phones, dtw, align_uniform, STOP, FS, N_TARGET

N_BANK_UTTS = 160
N_PASSES = 3


def centroids(bank):
    """One L2-normalised mean frame per phone (its acoustic model for the forced aligner)."""
    cen = {}
    for p, exs in bank.items():
        a = np.concatenate(exs, axis=0).mean(0)
        cen[p] = a / (np.linalg.norm(a) + 1e-9)
    return cen


def align_forced(fr, cen, phs):
    """Monotonic forced alignment of frames to the CMU phone sequence by ACOUSTIC cost to each phone's centroid
    (the agent's forced-path with the previous bank's models). Falls back to uniform if a phone has no model."""
    T, N = len(fr), len(phs)
    if N == 0 or T < N or any(p not in cen for p in phs):
        return align_uniform(fr, None, phs)
    C = np.stack([1.0 - fr @ cen[p] for p in phs])          # (N, T) frame->phone-centroid cosine cost
    dp = np.full((N + 1, T + 1), 1e18); dp[0, 0] = 0.0
    bk = np.zeros((N + 1, T + 1), dtype=np.int8)
    for i in range(1, N + 1):
        for j in range(i, T - (N - i) + 1):
            adv, stay = dp[i - 1, j - 1], dp[i, j - 1]
            if adv <= stay:
                dp[i, j], bk[i, j] = C[i - 1, j - 1] + adv, 0
            else:
                dp[i, j], bk[i, j] = C[i - 1, j - 1] + stay, 1
    spans = {k: [] for k in range(N)}
    i, j = N, T
    while j > 0 and i > 0:
        spans[i - 1].append(j - 1)
        i, j = (i - 1, j - 1) if bk[i, j] == 0 else (i, j - 1)
    return [(phs[k], fr[sorted(spans[k])]) for k in range(N) if spans[k]]


def bank_phones(train, align_fn, cen=None):
    bank = {}
    for (_w, fr, ph) in train:
        for (p, sub) in align_fn(fr, cen, ph):
            bank.setdefault(p, []).append(sub)
    return bank


def medoids(bank):
    med = {}
    for p, exs in bank.items():
        samp = exs[:12]
        if len(samp) == 1:
            med[p] = samp[0]; continue
        best, bi = 1e18, 0
        for i, a in enumerate(samp):
            tot = sum(dtw(a, b) for j, b in enumerate(samp) if j != i)
            if tot < best:
                best, bi = tot, i
        med[p] = samp[bi]
    return med


def read(clip_fr, targets, med):
    best = {}
    for w in targets:
        ph = phones(w)
        if any(p not in med for p in ph):
            continue
        tmpl = np.concatenate([med[p] for p in ph], axis=0)
        best[w] = dtw(clip_fr, tmpl)
    return sorted(best, key=best.get)


def main():
    print("=" * 96)
    print("ITERATE THE ALIGNER — EM forced alignment with the phones' own models (the agent's fix)")
    print("=" * 96)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    pairs = gather_pairs(limit=None)
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in pairs:
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    tw = Counter()
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path)
            for (w, _t0, _t1) in sw.transcribe_lang_timed(np.asarray(x, dtype=np.float64), fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                ph = phones(w)
                if len(w) >= 3 and ph and w not in STOP and len(ph) >= 3:
                    tw[w] += 1
    targets = [w for (w, _c) in tw.most_common(N_TARGET)]; tset = set(targets)
    print(f"  {len(targets)} held-out content targets | caching train word frames+phones (whisper)...", flush=True)

    train = []
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:5]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha()); ph = phones(w)
                if not ph or w in tset:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size >= int(0.05 * fs):
                    fr, _e = frames(seg)
                    train.append((w, fr, ph))
            n += 1
            if n >= N_BANK_UTTS:
                break
        if n >= N_BANK_UTTS:
            break

    test = []
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                if w in tset:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        cf, _e = frames(seg)
                        test.append((w, cf))
            if len(test) >= 130:
                break
        if len(test) >= 130:
            break
    print(f"  {len(train)} train words, {len(test)} held-out target instances; running {N_PASSES} EM passes...\n",
          flush=True)

    chance = 1.0 / max(len(targets), 1)
    print(f"  candidate set = the {len(targets)} targets (chance {chance*100:.0f}%); whole-word matcher = 0 by construction:")
    cen = None
    rows = []
    for p in range(1, N_PASSES + 1):
        bank = bank_phones(train, align_uniform if cen is None else align_forced, cen)
        med = medoids(bank)
        t1 = t3 = tot = 0
        for (w, cf) in test:
            rk = read(cf, targets, med); tot += 1
            t1 += int(rk and rk[0] == w); t3 += int(w in rk[:3])
        rows.append((t1 / max(tot, 1), t3 / max(tot, 1)))
        tag = "uniform (v1)" if p == 1 else f"forced EM pass {p}"
        print(f"    {tag:<18}: top-1 {rows[-1][0]*100:4.0f}% | top-3 {rows[-1][1]*100:4.0f}%", flush=True)
        cen = centroids(bank)

    print("\n" + "=" * 96)
    d1 = (rows[-1][0] - rows[0][0]) * 100; d3 = (rows[-1][1] - rows[0][1]) * 100
    if d1 > 4 or d3 > 5:
        print(f"  THE ALIGNER WAS THE LIMITER: EM forced alignment lifts the OOV read top-1 {d1:+.0f}pt / top-3 {d3:+.0f}pt over")
        print("  the crude uniform v1 -- better phone models find better boundaries find better phone models. No new")
        print("  model, no labels: CMUdict order + the phones' own acoustics bootstrap it. Wire-in = SeqDtw forced-path.")
    elif d1 > 1 or d3 > 1:
        print(f"  MODEST ({d1:+.0f}/{d3:+.0f}pt): EM helps a little; the boundaries sharpen but the ceiling is elsewhere")
        print("  (phones too coarse under coarticulation, or more exemplars needed). Worth keeping, not the whole gap.")
    else:
        print(f"  EM DOES NOT LIFT IT ({d1:+.0f}/{d3:+.0f}pt): the aligner was not the binding limit after all -- the gap is")
        print("  the unit (phones too coarse / context-blind) or coverage. The agent's fork: context-dependent units next.")
    print("=" * 96)


if __name__ == "__main__":
    main()
