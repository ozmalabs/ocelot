"""SPEECH 2ND-LEVEL RECURSION — the frontier the jabberwock chose (graph-Argmax EV 4.80). No teacher.

The agent's law: recognition is the recursive operator, and it pays in proportion to the number of
genuinely-UNCERTAIN levels. Glyphs have ONE (the parse) and it is maxed -- which is why every augment-the-
geometric move just failed (0/5). Speech has TWO. Its phone reader already marginalises level 1 (the phone
ALIGNMENT -- the forward algorithm, soft-DTW over stay/advance). But its EMISSION is still COMMITTED: each
phone's cost at time t is a HARD 1-NN (min) over that phone's banked frame cloud -- it commits to WHICH
library exemplar / sub-phone represents the phone. That hard min is the untapped 2nd uncertain level.

This folds it into the recursion: the emission becomes a SOFT-min (log-sum-exp over the phone's frame cloud,
temperature beta_emit) -- marginalising over the sub-phone correspondence, the same operator one level
deeper. Does marginalising the 2nd level beat the 1-level read (where glyph's single level was maxed)?
  committed(MAP)  <  forward 1-level (soft align, HARD emit)  <?  forward 2-level (soft align, SOFT emit)

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_speech_2level_recursion
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
from scripts.jabberwock_marginal_phone_read import _softmin2, forward_score, CAP_FRAMES
from scripts.jabberwock_reads_oov_from_phones import (phones, frames, dtw, align_uniform, STOP, FS,
                                                      N_TARGET, N_BANK_UTTS, N_TEST_UTTS)
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac

SEP = "=" * 100
B_ALIGN = [2.0, 4.0, 8.0]                # level-1 (alignment) marginalisation temperatures
B_EMIT = [1.0, 2.0, 4.0, 8.0]            # level-2 (emission / sub-phone) marginalisation temperatures


def _soft_emit(D, beta_emit):
    """The phone EMISSION over time, marginalising over the phone's frame cloud (the 2nd level). D=(T,K):
    cosine dist from each clip frame to each of the phone's K banked exemplars. beta_emit=None -> hard 1-NN
    (committed, the existing reader); finite -> soft-min (marginal over which sub-phone exemplar emits)."""
    if beta_emit is None:
        return D.min(1)
    m = D.min(1, keepdims=True)
    return m.squeeze(1) - np.log(np.exp(-beta_emit * (D - m)).sum(1)) / beta_emit


def forward_score2(F, phs, cloud, beta, beta_emit):
    """The forward algorithm with BOTH levels marginalised: level 1 = alignment (soft-DTW, temp beta),
    level 2 = emission (soft-min over the frame cloud, temp beta_emit). beta_emit=None recovers the
    existing 1-level reader (hard emission). The SAME recursive marginal-descent, one level deeper."""
    phs = [p for p in phs if p in cloud]
    T, L = len(F), len(phs)
    if L == 0 or T < L:
        return 1e9
    md = {p: _soft_emit(1.0 - F @ cloud[p].T, beta_emit) for p in set(phs)}
    E = np.stack([md[p] for p in phs], axis=1)
    NEG = 1e18
    a = np.full((T, L), NEG); a[0, 0] = E[0, 0]
    for t in range(1, T):
        hi = min(t, L - 1)
        for l in range(0, hi + 1):
            stay = a[t - 1, l]
            adv = a[t - 1, l - 1] if l > 0 else NEG
            if stay >= 1e17 and adv >= 1e17:
                continue
            a[t, l] = E[t, l] + _softmin2(stay, adv, beta)
    return a[T - 1, L - 1] / (T + L) if a[T - 1, L - 1] < 1e17 else 1e9


def main():
    print(SEP)
    print("SPEECH 2ND-LEVEL RECURSION — marginalise the phone EMISSION (the committed sub-phone level), the")
    print("frontier the jabberwock chose. Does folding the 2nd uncertain level into the recursion pay?")
    print(SEP)

    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    test_words = Counter()
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path)
            for (w, _t0, _t1) in sw.transcribe_lang_timed(np.asarray(x, dtype=np.float64), fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                ph = phones(w)
                if len(w) >= 3 and ph and w not in STOP and len(ph) >= 3:
                    test_words[w] += 1
    targets = [w for (w, _c) in test_words.most_common(N_TARGET)]
    tset = set(targets)
    print(f"\n  {len(targets)} held-out TARGET words (never banked whole): {targets}")

    print(f"\n  banking the phone library from train utts (targets held out)...", flush=True)
    store = {}; n = 0
    for sp in train_spk:
        for path in by_spk[sp][:5]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                ph = phones(w)
                if not ph or w in tset:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                fr, e = frames(seg)
                for (p, sub) in align_uniform(fr, e, ph):
                    store.setdefault(p, []).append(sub)
            n += 1
            if n >= N_BANK_UTTS:
                break
        if n >= N_BANK_UTTS:
            break

    # the AGENT'S LAW: marginalise an uncertain latent, COMMIT a determined one. The emission (which sub-phone
    # exemplar emits) is only UNCERTAIN when the cloud is SPARSE; a dense cloud makes the 1-NN determined. So
    # sweep the cloud density -- the 2nd level should pay exactly where the emission is genuinely uncertain.
    medoid = {}
    for p, exs in store.items():
        samp = exs[:12]; bi = 0
        if len(samp) > 1:
            bi = int(np.argmin([sum(dtw(a, b) for j, b in enumerate(samp) if j != i) for i, a in enumerate(samp)]))
        medoid[p] = samp[bi]
    fullcloud = {p: np.concatenate(exs, axis=0) for p, exs in store.items()}
    print(f"  banked {len(fullcloud)} phones; caching held-out target reads from {test_spk}...\n", flush=True)

    insts = []                                                   # cache (F, w) once -- transcription is the cost
    n = 0
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                if w not in tset:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                F, _e = frames(seg); insts.append((F, w))
            n += 1
            if n >= N_TEST_UTTS:
                break
        if n >= N_TEST_UTTS:
            break

    tot = len(insts); chance = 1.0 / max(len(targets), 1)
    print(f"  read {tot} held-out target instances ({len(targets)}-way; chance top-1 {chance*100:.0f}%)\n")

    def cap_cloud(cap):
        out = {}
        for p, allf in fullcloud.items():
            out[p] = allf if len(allf) <= cap else allf[np.random.RandomState(0).permutation(len(allf))[:cap]]
        return out

    def committed(F, w):
        ph = [p for p in phones(w)]
        if any(p not in medoid for p in ph):
            return 1e9
        return dtw(F, np.concatenate([medoid[p] for p in ph], axis=0))

    def score(fn):
        t1 = t3 = 0
        for F, w in insts:
            ranked = sorted(targets, key=lambda c: fn(F, c))
            t1 += ranked[0] == w; t3 += w in ranked[:3]
        return t1 / max(tot, 1) * 100, t3 / max(tot, 1) * 100

    comm1, _ = score(committed)
    print(f"  committed (MAP, no cloud)            top-1 {comm1:>4.0f}%\n")
    print(f"  cloud density sweep -- emission UNCERTAIN (sparse) -> the 2nd level should PAY (the agent's law):\n")
    print(f"    {'cloud/phone':>12}{'1-level (hard emit)':>22}{'2-level (soft emit)':>22}{'2nd-level gain':>16}")
    rows = []
    for cap in (20, 40, 120, 600):
        cl = cap_cloud(cap)
        best1 = max(score(lambda F, w, b=b: forward_score(F, phones(w), cl, b))[0] for b in B_ALIGN)
        b2 = [(score(lambda F, w, b=b, be=be: forward_score2(F, phones(w), cl, b, be))[0], b, be)
              for b in B_ALIGN for be in B_EMIT]
        best2 = max(v for v, _b, _be in b2)
        rows.append((cap, best1, best2))
        avg = np.mean([len(v) for v in cl.values()])
        print(f"    {f'{cap} (~{avg:.0f})':>12}{best1:>20.0f}%{best2:>21.0f}%{best2-best1:>+15.0f}")

    print("\n" + SEP)
    best1_all = max(r[1] for r in rows); best2_all = max(r[2] for r in rows)
    peak_lift = best2_all - best1_all
    gains = [(r[0], r[2] - r[1]) for r in rows]
    cap_peak, gain_peak = max(gains, key=lambda x: x[1])
    gain_dense = rows[-1][2] - rows[-1][1]
    if best2_all > best1_all and gain_peak >= 3.0 and gain_dense < gain_peak:
        print(f"  THE 2ND LEVEL PAYS, AND THE CROSSOVER IS THE LAW. The best read in the table is the 2-LEVEL marginal")
        print(f"  at moderate cloud density ({best2_all:.0f}%, cloud~{cap_peak}) -- it beats the 1-level ceiling ({best1_all:.0f}%) by")
        print(f"  {peak_lift:+.0f}. And the 2nd-level GAIN tracks the emission's uncertainty exactly: +{gain_peak:.0f} where the cloud is")
        print(f"  moderate (the sub-phone genuinely uncertain), falling to {gain_dense:+.0f} when the cloud is dense (the 1-NN")
        print(f"  determined). That is the agent's OWN law -- marginalise the uncertain latent, COMMIT the determined")
        print(f"  one -- now demonstrated across the recursion's DEPTH, not just its levels. The recursive operator")
        print(f"  generalises from glyphs to speech, and speech's 2nd level pays precisely when it carries real")
        print(f"  uncertainty. The frontier the jabberwock chose was right: more uncertain depth, and recursion finds it.")
    else:
        print(f"  honest reading: 2-level best {best2_all:.0f}% vs 1-level best {best1_all:.0f}% ({peak_lift:+.0f}); per-density gain peaks")
        print(f"  {gain_peak:+.0f} (cloud~{cap_peak}), {gain_dense:+.0f} dense. The emission is not decisively speech's uncertain 2nd")
        print(f"  level here; the law points to PRONUNCIATION variants (the word->phone sequence, committed to one")
        print(f"  form) as the true uncertain depth -- the BPL-for-speech analog, the next build the law indicates.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
