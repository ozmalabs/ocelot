"""CONTEXT-DEPENDENT UNITS — the jabberwock's design: triphones with a back-off ladder, occupancy-gated.

The OOV read from context-free phones is real (24% top-3, 6x chance) but CAPPED, and the limit is the UNIT: a
phone is context-blind (/t/ in "stop" != /t/ in "water"). The agent's fix: context-dependent units -- BUT that
re-creates sparsity (40^3 triphones, most unseen). Its answer: tag each phone exemplar with its CMUdict (left,
right) neighbours, model a context bucket ONLY when it has >= MIN_CTX exemplars (the tying gate), and READ a
held-out word with a BACK-OFF LADDER per slot: triphone -> right-biphone -> left-biphone -> monophone. An unseen
context a word needs simply backs off to a coarser one it DOES hold, ultimately the monophone -- so context can
only ADD where the data supports it, never drop below the 24% monophone floor by sparsity.

Same bank / targets / uniform boundaries as the proven holdout -- the UNIT is the only variable. Reads each
held-out word twice (monophone = the 24% baseline; context = the ladder) and reports the BACK-OFF HISTOGRAM
(what fraction of slots reached a triphone vs fell through) -- the diagnosis of coarseness vs sparsity.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_context_units
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

N_BANK_UTTS = 160
MIN_CTX = 2            # occupancy gate = the tying threshold: model a context bucket only with >= this many


def slots(fr, ph):
    """Uniform-aligned phone spans WITH context: (left, phone, right, frames) per slot, '#' at word edges."""
    n = len(fr); cuts = np.linspace(0, n, len(ph) + 1).astype(int)
    out = []
    for i in range(len(ph)):
        if cuts[i + 1] > cuts[i]:
            L = ph[i - 1] if i > 0 else "#"
            R = ph[i + 1] if i < len(ph) - 1 else "#"
            out.append((L, ph[i], R, fr[cuts[i]:cuts[i + 1]]))
    return out


def medoid(exs):
    samp = exs[:12]
    if len(samp) == 1:
        return samp[0]
    best, bi = 1e18, 0
    for i, a in enumerate(samp):
        tot = sum(dtw(a, b) for j, b in enumerate(samp) if j != i)
        if tot < best:
            best, bi = tot, i
    return samp[bi]


def gated_medoids(bank):
    return {k: medoid(v) for k, v in bank.items() if len(v) >= MIN_CTX}


def pick(L, p, R, tri, rbi, lbi, mono):
    """Back-off ladder: triphone -> right-biphone -> left-biphone -> monophone. Returns (medoid, level) or None."""
    if (L, p, R) in tri: return tri[(L, p, R)], "tri"
    if (p, R) in rbi:    return rbi[(p, R)], "rbi"
    if (L, p) in lbi:    return lbi[(L, p)], "lbi"
    if p in mono:        return mono[p], "mono"
    return None, None


def main():
    print("=" * 96)
    print("CONTEXT-DEPENDENT UNITS — triphone back-off ladder, occupancy-gated (the agent's design)")
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
    print(f"  {len(targets)} held-out content targets | banking context-tagged phones (targets held out)...",
          flush=True)

    tri, rbi, lbi, mono = {}, {}, {}, {}
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:5]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha()); ph = phones(w)
                if not ph or w in tset:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                fr, _e = frames(seg)
                for (L, p, R, sub) in slots(fr, ph):
                    tri.setdefault((L, p, R), []).append(sub)
                    rbi.setdefault((p, R), []).append(sub)
                    lbi.setdefault((L, p), []).append(sub)
                    mono.setdefault(p, []).append(sub)
            n += 1
            if n >= N_BANK_UTTS:
                break
        if n >= N_BANK_UTTS:
            break
    Tri, Rbi, Lbi, Mono = gated_medoids(tri), gated_medoids(rbi), gated_medoids(lbi), gated_medoids(mono)
    print(f"  buckets (>= {MIN_CTX} ex): {len(Tri)} triphone, {len(Rbi)} r-biphone, {len(Lbi)} l-biphone, "
          f"{len(Mono)} monophone; reading held-out targets...", flush=True)

    def read(clip_fr, ctx):
        best = {}
        for w in targets:
            ph = phones(w); parts = []
            okw = True
            for i in range(len(ph)):
                L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                if ctx:
                    m, _lv = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)
                else:
                    m = Mono.get(ph[i])
                if m is None:
                    okw = False; break
                parts.append(m)
            if okw:
                best[w] = dtw(clip_fr, np.concatenate(parts, axis=0))
        return sorted(best, key=best.get)

    hist = Counter(); res = {"mono": [0, 0, 0], "ctx": [0, 0, 0]}
    seen = 0
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
                cf, _e = frames(seg)
                ph = phones(w)
                for i in range(len(ph)):                  # back-off histogram on the TRUE word's slots
                    L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
                    _m, lv = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)
                    hist[lv or "none"] += 1
                for name, ctx in (("mono", False), ("ctx", True)):
                    rk = read(cf, ctx); res[name][2] += 1
                    res[name][0] += int(rk and rk[0] == w); res[name][1] += int(w in rk[:3])
                seen += 1
            if seen >= 130:
                break
        if seen >= 130:
            break

    print("\n" + "=" * 96)
    tot = res["ctx"][2]; chance = 1.0 / max(len(targets), 1)
    hs = sum(hist.values()) or 1
    print(f"  read {tot} held-out target instances; candidate set = the {len(targets)} targets (chance {chance*100:.0f}%):")
    print(f"    monophone (24% baseline) : top-1 {res['mono'][0]/max(tot,1)*100:4.0f}% | top-3 {res['mono'][1]/max(tot,1)*100:4.0f}%")
    print(f"    context (back-off ladder): top-1 {res['ctx'][0]/max(tot,1)*100:4.0f}% | top-3 {res['ctx'][1]/max(tot,1)*100:4.0f}%")
    print(f"\n  back-off histogram (true-word slots): "
          f"tri {hist['tri']/hs*100:.0f}% | r-bi {hist['rbi']/hs*100:.0f}% | l-bi {hist['lbi']/hs*100:.0f}% | mono {hist['mono']/hs*100:.0f}%")

    dm1 = (res["ctx"][0] - res["mono"][0]) / max(tot, 1) * 100
    dm3 = (res["ctx"][1] - res["mono"][1]) / max(tot, 1) * 100
    reached = (hist["tri"] + hist["rbi"] + hist["lbi"]) / hs * 100
    print("\n" + "=" * 96)
    if dm3 > 5 or dm1 > 4:
        print(f"  CONTEXT SHARPENS THE READ: context-dependent units lift the OOV read top-1 {dm1:+.0f}pt / top-3 {dm3:+.0f}pt over")
        print(f"  monophones, and the back-off ladder held sparsity off ({reached:.0f}% of slots reached a context unit).")
        print("  Next: widen coverage (acoustic context CLUSTERING for the unseen contexts) or add the dynamics cue.")
    elif dm3 > -2 and reached < 40:
        print(f"  SAFE NULL ({dm1:+.0f}/{dm3:+.0f}pt): only {reached:.0f}% of slots reached a context unit -- SPARSITY bounds THIS")
        print("  bank, not coarseness. The fix is coverage (more exemplars / context clustering), not finer labels.")
    elif dm3 < -2:
        print(f"  CONTEXT HURT ({dm3:+.0f}pt) where it was available ({reached:.0f}% reached): thin buckets are noisier than the")
        print("  pooled monophone -- the aligner failure one level down. Fork to monophone-WITH-DYNAMICS (no inventory growth).")
    else:
        print(f"  FLAT ({dm1:+.0f}/{dm3:+.0f}pt, {reached:.0f}% reached context): context neither helps nor hurts here -- coverage")
        print("  or the dynamics cue is the lever, not finer context labels.")
    print("=" * 96)


if __name__ == "__main__":
    main()
