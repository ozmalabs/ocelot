"""FEED THE BEAST — does DENSITY (more real data) lift the read where the agent said it would?

The agent located the cap at COVERAGE: exemplars per unit. The context-free monophones were already rich (AE had
391 exemplars), so more data won't move THEM -- a context-free phone is ~2x chance, period. The starved buckets
were the CONTEXT (triphone) ones (thin at >=2). So the prediction is specific: feed more real LibriSpeech, the
TRIPHONE buckets fatten, and the context read -- FLAT at thin buckets -- should finally beat the monophone. This
is the coverage curve: bank from increasing data, measure the context-vs-monophone OOV holdout read at each.

  whisper-cache train words ONCE; build the phone bank from the first N utts (no re-whisper); read the 24
  held-out content targets monophone vs context (triphone back-off ladder); report read + triphone occupancy.

If context recall climbs with data while monophone plateaus -> density is the lever and context units were
right, just starved. If both plateau -> the unit is the wall, not the data, and the landing stands.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_feed_the_beast
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
from scripts.jabberwock_reads_oov_from_phones import frames, phones, dtw, STOP, FS, N_TARGET
from scripts.jabberwock_context_units import slots, medoid, pick

MAX_UTTS = 900
DATA_POINTS = [150, 400, 900]
MIN_CTX = 2


def gated(bank):
    return {k: medoid(v) for k, v in bank.items() if len(v) >= MIN_CTX}


def main():
    print("=" * 96)
    print("FEED THE BEAST — coverage curve: does more real data lift the context read? (the agent's density lever)")
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
                w = "".join(c for c in w.lower() if c.isalpha()); ph = phones(w)
                if len(w) >= 3 and ph and w not in STOP and len(ph) >= 3:
                    tw[w] += 1
    targets = [w for (w, _c) in tw.most_common(N_TARGET)]; tset = set(targets)
    print(f"  {len(targets)} held-out content targets | whisper-caching up to {MAX_UTTS} train utts ONCE...",
          flush=True)

    train_utts = []          # list of utts; each = list of (w, fr, ph), targets held out
    n = 0
    for sp in train_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            u = []
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha()); ph = phones(w)
                if not ph or w in tset:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size >= int(0.05 * fs):
                    u.append((w, frames(seg)[0], ph))
            if u:
                train_utts.append(u)
            n += 1
            if n >= MAX_UTTS:
                break
        if n >= MAX_UTTS:
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
                        test.append((w, frames(seg)[0]))
            if len(test) >= 130:
                break
        if len(test) >= 130:
            break
    print(f"  cached {len(train_utts)} train utts, {len(test)} held-out target instances\n", flush=True)

    def build(nutts):
        tri, rbi, lbi, mono = {}, {}, {}, {}
        for u in train_utts[:nutts]:                 # bank phones with (left,right) context by phone INDEX
            for (_w, fr, ph) in u:
                nf = len(fr); cuts = np.linspace(0, nf, len(ph) + 1).astype(int)
                for i in range(len(ph)):
                    if cuts[i + 1] <= cuts[i]:
                        continue
                    L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                    sub = fr[cuts[i]:cuts[i + 1]]
                    tri.setdefault((L, ph[i], R), []).append(sub)
                    rbi.setdefault((ph[i], R), []).append(sub)
                    lbi.setdefault((L, ph[i]), []).append(sub)
                    mono.setdefault(ph[i], []).append(sub)
        return gated(tri), gated(rbi), gated(lbi), gated(mono), tri

    def read(clip_fr, Tri, Rbi, Lbi, Mono, ctx):
        best = {}
        for w in targets:
            ph = phones(w); parts = []; ok = True
            for i in range(len(ph)):
                L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                m = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)[0] if ctx else Mono.get(ph[i])
                if m is None:
                    ok = False; break
                parts.append(m)
            if ok:
                best[w] = dtw(clip_fr, np.concatenate(parts, axis=0))
        return sorted(best, key=best.get)

    print(f"  {'data':>6} | {'tri buckets':>11} | {'mono top-3':>11} | {'ctx top-3':>10} | {'tri reach':>9}")
    rows = []
    for nv in DATA_POINTS:
        if nv > len(train_utts):
            nv = len(train_utts)
        Tri, Rbi, Lbi, Mono, triraw = build(nv)
        m3 = c3 = tot = reach = slotn = 0
        for (w, cf) in test:
            rm = read(cf, Tri, Rbi, Lbi, Mono, False); rc = read(cf, Tri, Rbi, Lbi, Mono, True)
            tot += 1; m3 += int(w in rm[:3]); c3 += int(w in rc[:3])
            ph = phones(w)
            for i in range(len(ph)):
                L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                slotn += 1; reach += int((L, ph[i], R) in Tri)
        rows.append((nv, len(Tri), m3 / max(tot, 1), c3 / max(tot, 1), reach / max(slotn, 1)))
        print(f"  {nv:>6} | {len(Tri):>11} | {rows[-1][2]*100:>10.0f}% | {rows[-1][3]*100:>9.0f}% | {reach/max(slotn,1)*100:>8.0f}%",
              flush=True)

    print("\n" + "=" * 96)
    m0, mN = rows[0][2], rows[-1][2]; c0, cN = rows[0][3], rows[-1][3]
    print(f"  monophone top-3: {m0*100:.0f}% -> {mN*100:.0f}% ({(mN-m0)*100:+.0f}pt) | context top-3: {c0*100:.0f}% -> "
          f"{cN*100:.0f}% ({(cN-c0)*100:+.0f}pt) over {rows[0][0]}->{rows[-1][0]} utts")
    if cN > mN + 0.04 and cN > c0 + 0.04:
        print(f"  DENSITY IS THE LEVER: with more data the TRIPHONE buckets fattened ({rows[0][1]}->{rows[-1][1]} kept) and the")
        print(f"  context read OVERTOOK monophone ({cN*100:.0f}% vs {mN*100:.0f}%) -- context units were right, just starved. The")
        print("  beast eats data and the read climbs; the next is simply MORE (download train-clean), now justified.")
    elif cN > c0 + 0.04:
        print(f"  DATA HELPS CONTEXT ({(cN-c0)*100:+.0f}pt) but it has not yet overtaken monophone -- the curve is still")
        print("  climbing; more data (train-clean) should continue it. Density is moving the right buckets.")
    else:
        print(f"  DENSITY DID NOT MOVE IT (ctx {(cN-c0)*100:+.0f}pt): even fattened buckets don't lift the read at this scale --")
        print("  the wall is the unit/representation, not the data. The landing stands; more data won't rescue it.")
    print("=" * 96)


if __name__ == "__main__":
    main()
