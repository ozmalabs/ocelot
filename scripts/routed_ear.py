"""ROUTED EAR — certify the resource-rational profile: the best ear + the agreement gate (cheap-first / escalate).

The refined rule defines the system as ROUTED (cheap-first, escalate-on-failure) and names INEFFICIENCY (no routing) as
a core problem with a static model. Both ingredients are certified separately -- the best ear (trajectory + static+delta,
+17 over pooled) and the CROSS-CUE AGREEMENT gate (it knows when it's right). COMPOSE them: gate each token by cross-cue
agreement (>=3 of 4 independent cues concur) -> CONFIDENT (cheap, accept) vs TAIL (escalate). Reframe the misleading
"~20% frozen average" into the operating characteristic that matters: a CHEAP HIGH-ACCURACY confident subset + a
correctly-flagged escalation tail.

Pre-committed bar (the agent's): KEEP if confident-subset accuracy >= 2x overall at >= 20% coverage AND tail accuracy <
overall (the gate separates); STOP if < 1.5x or coverage < 10%. FAIRNESS FLOOR: the confident subset must span >= half
the test speakers AND >= 50 distinct labels (no collapse to one speaker / a few easy words).

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.routed_ear
"""
from __future__ import annotations

import glob
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, dtw
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from scripts.jabberwock_selftraining_gate import featset, delta, _l2

N_BANK = 300
KMAX = 5
NWAY = 500
N_TEST = 700
PRUNE = 30


def main():
    print("=" * 100)
    print("ROUTED EAR — best ear + cross-cue agreement gate: confident (cheap, accurate) vs escalation tail")
    print("=" * 100)
    import substrate_rs as srs
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-7:], spks[:-7]   # more test speakers -> fair generality/span test

    bank = defaultdict(list); nb = 0       # word -> list of (traj, fft, allpole)
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < KMAX:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(featset(s, seg))
        if nb >= N_BANK:
            break
    vocab = [w for w, e in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    PW = np.stack([_l2(np.stack([e[0].mean(0) for e in bank[w]]).mean(0)) for w in vocab])
    print(f"  bank {len(bank)} words ({nb} utts, {len(train_spk)} spk); {len(vocab)}-way; {len(test_spk)} test speakers\n", flush=True)

    test = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if len(test) >= N_TEST:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in vset and len(w) >= MINW:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        test.append((w, sp, featset(s, seg)))
        if len(test) >= N_TEST:
            break
    print(f"  {len(test)} held-out cross-speaker tokens; scoring best-ear + 4-cue gate...\n", flush=True)

    rows = []
    for (w, sp, (traj, fft, allp)) in test:
        dl = delta(traj)
        pv = _l2(traj.mean(0)); top = np.argsort(-(PW @ pv))[:PRUNE]
        cwords = [vocab[i] for i in top]
        d_st = np.array([min(dtw(traj, e[0]) for e in bank[c]) for c in cwords])
        d_dl = np.array([min(dtw(dl, delta(e[0])) for e in bank[c]) for c in cwords])
        d_ff = np.array([min(1.0 - fft @ e[1] for e in bank[c]) for c in cwords])
        d_ap = np.array([min(1.0 - allp @ e[2] for e in bank[c]) for c in cwords])
        z = lambda d: (d - d.mean()) / (d.std() + 1e-9)
        best_ear = cwords[int((z(d_st) + 0.3 * z(d_dl)).argmin())]      # certified best ear (trajectory static+delta)
        winners = [cwords[int(d.argmin())] for d in (d_st, d_dl, d_ff, d_ap)]
        cons, agree = Counter(winners).most_common(1)[0]
        rows.append({"true": w, "sp": sp, "best": best_ear, "agree": agree})

    n = len(rows)
    overall = 100 * np.mean([r["best"] == r["true"] for r in rows])
    conf = [r for r in rows if r["agree"] >= 3]
    tail = [r for r in rows if r["agree"] < 3]
    conf_acc = 100 * np.mean([r["best"] == r["true"] for r in conf]) if conf else 0.0
    tail_acc = 100 * np.mean([r["best"] == r["true"] for r in tail]) if tail else 0.0
    cov = 100 * len(conf) / n
    conf_spk = len({r["sp"] for r in conf}); conf_lab = len({r["true"] for r in conf if r["best"] == r["true"]})

    print("\n" + "=" * 100)
    print(f"  @{len(vocab)}-way cross-speaker, {n} tokens:")
    print(f"    OVERALL (best ear, no routing):     {overall:.1f}%")
    print(f"    CONFIDENT subset (>=3 cues agree):  {conf_acc:.1f}%  @ {cov:.0f}% coverage  ({len(conf)} tokens)")
    print(f"    ESCALATION TAIL (<3 agree):         {tail_acc:.1f}%  ({len(tail)} tokens -> teacher/expensive)")
    print(f"    confident-subset span: {conf_spk}/{len(test_spk)} speakers, {conf_lab} distinct correct labels")
    print("-" * 100)
    ratio = conf_acc / max(overall, 1e-9)
    keep = conf_acc >= 2 * overall and cov >= 20 and tail_acc < overall
    fair = conf_spk >= (len(test_spk) + 1) // 2 and conf_lab >= 50
    if not fair:
        print(f"  FAIRNESS FAIL: confident subset collapsed ({conf_spk} spk, {conf_lab} labels) -> not a real routing signal. Void.")
    elif keep:
        print(f"  KEEP — the ROUTED ear is the real object: on the {cov:.0f}% it's confident the ear is {conf_acc:.0f}% ({ratio:.1f}x the")
        print(f"  {overall:.0f}% average), and the tail it correctly flags for escalation is only {tail_acc:.0f}%. The '20% average' was")
        print("  the wrong number -- cheap-first/escalate is the operating characteristic. Routing certified (problem-1 part).")
    elif ratio >= 1.5 and cov >= 10:
        print(f"  PARTIAL — routing helps ({conf_acc:.0f}% on {cov:.0f}% = {ratio:.1f}x overall) but under the 2x/20% bar; real signal, modest. Honest.")
    else:
        print(f"  STOP — the gate does NOT compose with the best ear ({conf_acc:.0f}% @ {cov:.0f}%, {ratio:.1f}x); reallocate to (A) or (C). Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
