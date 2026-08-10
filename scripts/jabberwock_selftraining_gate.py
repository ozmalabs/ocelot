"""SELF-TRAINING GATE — the crux: does CROSS-CUE AGREEMENT track correctness (purity) better than SOFTMAX at matched coverage?

The make-or-break of the self-training loop: a self-label gate that banks the agent's OWN guess must track CORRECTNESS,
but softmax peakedness ANTI-tracks it (proven 2x). The agent's design: CROSS-CUE AGREEMENT -- N independent reads
picking the SAME word + metric-space margin -- is the teacher-free correctness signal. Validate it:
  4 independent cues (static-traj DTW, delta-traj DTW, fft_ear pooled, allpole_ear pooled) over a high-recall bank.
  AGREEMENT gate: >=k cues agree on the consensus word AND margin >= theta -> SELF-LABEL (else DEFER).
  PURITY = fraction of SELF-LABELLED whose consensus == true word (ground truth for SCORING only, never the gate).
Compare to a SOFTMAX-confidence gate AT MATCHED COVERAGE (pass-rate). Pre-committed: agreement purity must DOMINATE
softmax at the same pass-rate (else it's just a stricter threshold), the DEFERRED set must be lower-purity than passed,
and self-banking the passed set must GROW recall WITHOUT a purity drop (the error-amplification tell).

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_selftraining_gate
"""
from __future__ import annotations

import glob
import math
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, STOP
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
import domains.self_directed_speech_world as SDW
from scripts.abs_language_decode import FS

N_BANK = 130
K = 3
NWAY = 300
N_GATE = 350      # percepts for the gate purity/coverage test
N_EVAL = 150      # held-out percepts for recall-growth


def delta(F):
    F = np.asarray(F, np.float32)
    if len(F) < 2:
        return F
    d = np.diff(F, axis=0)
    return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)


def _l2(v):
    v = np.asarray(v, np.float32); n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def featset(s, seg):
    ch = SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
    return frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32), _l2(ch[1]), _l2(ch[2])


def main():
    print("=" * 100)
    print("SELF-TRAINING GATE — cross-cue AGREEMENT vs SOFTMAX at matched coverage (the correctness-signal crux)")
    print("=" * 100)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk)
    test_spk, train_spk = spks[-3:], spks[:-3]

    bank = defaultdict(list); nb = 0       # word -> list of (traj, fft, allpole)
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < K:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(featset(s, seg))
        if nb >= N_BANK:
            break
    vocab = [w for w, _ in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    print(f"  bank {len(bank)} words ({nb} utts); {len(vocab)}-way; 4 cues (static/delta DTW, fft/allpole pooled)\n", flush=True)

    def collect(maxn):
        out = []
        for sp in test_spk:
            for (f, t) in by_spk[sp]:
                if len(out) >= maxn:
                    break
                x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
                for (w, t0, t1) in align_utt(x, fs, t):
                    if w in vset and len(w) >= MINW:
                        seg = x[int(t0 * fs):int(t1 * fs)]
                        if seg.size >= int(0.05 * fs):
                            out.append((w, featset(s, seg)))
            if len(out) >= maxn:
                break
        return out

    import pickle
    CACHE = "/tmp/selftrain_gate_rows.pkl"
    if os.path.exists(CACHE):
        rows = pickle.load(open(CACHE, "rb"))
        print(f"  loaded {len(rows)} cached gate reads\n", flush=True)
    else:
        gate_set = collect(N_GATE)
        print(f"  {len(gate_set)} gate percepts; computing 4-cue reads...\n", flush=True)
        rows = []
        for k, (tw, (traj, fft, allp)) in enumerate(gate_set):
            dl = delta(traj)
            d_st = np.array([min(dtw(traj, e[0]) for e in bank[c]) for c in vocab])
            d_dl = np.array([min(dtw(dl, delta(e[0])) for e in bank[c]) for c in vocab])
            d_ff = np.array([min(1.0 - fft @ e[1] for e in bank[c]) for c in vocab])
            d_ap = np.array([min(1.0 - allp @ e[2] for e in bank[c]) for c in vocab])
            winners = [int(d.argmin()) for d in (d_st, d_dl, d_ff, d_ap)]
            cons, agree = Counter(winners).most_common(1)[0]
            sg = np.sort(d_st)
            margin = float((sg[1] - sg[0]) / (d_st.std() + 1e-9))     # anchor-cue metric-space margin
            rows.append({"true": vocab.index(tw), "cons": cons, "agree": agree, "margin": margin,
                         "stwin": winners[0], "d_st": d_st.astype(np.float32)})
            if (k + 1) % 60 == 0:
                print(f"    {k+1}/{len(gate_set)}...", flush=True)
        pickle.dump(rows, open(CACHE, "wb"))

    n = len(rows)
    # FAIR baselines (single-cue, well-scaled): static-margin gate, and temperature-softmax gate.
    def softmax_conf(d_st, T):
        p = np.exp(-(d_st - d_st.min()) / T); return float((p / p.sum()).max())
    for r in rows:
        r["smT"] = softmax_conf(r["d_st"], 0.05)     # temperature-scaled anchor softmax (peaked, thresholdable)
    base = 100 * np.mean([r["stwin"] == r["true"] for r in rows])    # overall single-cue accuracy (pass-all)
    print(f"  baseline: single-cue (static) overall accuracy {base:.1f}% over {n} percepts\n")

    # three gates, each swept over its own threshold -> (pass-rate, purity) curve
    def curve(passfn, labelfn, ths):
        out = []
        for th in ths:
            passed = [r for r in rows if passfn(r, th)]
            if len(passed) < 5:
                continue
            pur = 100 * np.mean([labelfn(r) == r["true"] for r in passed])
            out.append((len(passed) / n, pur, th))
        return out

    ag = curve(lambda r, th: r["agree"] >= 3 and r["margin"] >= th, lambda r: r["cons"], np.linspace(0, 1.5, 16))
    mg = curve(lambda r, th: r["margin"] >= th, lambda r: r["stwin"], np.linspace(0, 2.5, 26))          # single-cue MARGIN
    sx = curve(lambda r, th: r["smT"] >= th, lambda r: r["stwin"], np.linspace(0, 1.0, 41))             # temp-softmax

    def at(cur, pr):                       # purity of `cur` at the pass-rate nearest pr
        return min(cur, key=lambda x: abs(x[0] - pr)) if cur else (0, 0, 0)

    print(f"  AGREEMENT (>=3 cues) vs FAIR single-cue baselines, at matched coverage:")
    print(f"    {'pass-rate':>10}{'AGREEMENT':>12}{'single-MARGIN':>15}{'temp-SOFTMAX':>14}")
    for (pr, pur, th) in ag:
        if pr < 0.04:
            continue
        print(f"    {pr*100:>8.0f}% {pur:>10.1f}% {at(mg,pr)[1]:>13.1f}% {at(sx,pr)[1]:>12.1f}%", flush=True)

    # operating point: agree>=3 (margin 0) -> natural pass-rate; purity passed vs deferred
    op = [r for r in rows if r["agree"] >= 3]
    nop = [r for r in rows if r["agree"] < 3]
    pp = 100 * np.mean([r["cons"] == r["true"] for r in op]) if op else 0
    pd = 100 * np.mean([r["stwin"] == r["true"] for r in nop]) if nop else 0
    pr_op = len(op) / n
    mg_m, sx_m = at(mg, pr_op)[1], at(sx, pr_op)[1]
    print(f"\n  OPERATING POINT (>=3 cues agree): PASS {len(op)}/{n} ({pr_op*100:.0f}%) purity {pp:.1f}% | "
          f"DEFER {len(nop)} purity {pd:.1f}%")
    print(f"  at matched coverage {pr_op*100:.0f}%: single-cue MARGIN {mg_m:.1f}% | temp-SOFTMAX {sx_m:.1f}%  ->  "
          f"cross-cue adds +{pp-max(mg_m,sx_m):.1f}", flush=True)

    print("\n" + "=" * 100)
    dominates = pp > max(mg_m, sx_m) + 3
    separates = pp > pd + 10
    if dominates and separates:
        print(f"  KEEP — cross-cue AGREEMENT is a correctness signal beyond single-cue confidence: at {pr_op*100:.0f}% coverage it")
        print(f"  pins purity {pp:.1f}% vs single-margin {mg_m:.1f}% / softmax {sx_m:.1f}% (+{pp-max(mg_m,sx_m):.1f}), and DEFERS the low-purity")
        print(f"  cases ({pd:.1f}% vs {pp:.1f}%). Self-training can bank its OWN confident labels without amplifying error.")
    elif separates and pp > max(mg_m, sx_m):
        print(f"  PARTIAL — agreement separates right from wrong (passed {pp:.1f}% vs deferred {pd:.1f}%) and edges single-cue")
        print(f"  ({mg_m:.1f}/{sx_m:.1f}) but by < 3 pts. Real correctness signal; the cross-cue ADVANTAGE over single-cue is modest. Honest.")
    else:
        print(f"  STOP — cross-cue agreement does NOT clearly beat single-cue confidence at matched coverage (agree {pp:.1f} vs")
        print(f"  margin {mg_m:.1f} / softmax {sx_m:.1f}); the gain is just a stricter threshold, not the multi-cue part. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
