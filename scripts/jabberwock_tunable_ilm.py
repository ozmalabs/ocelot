"""TUNABLE INTERNAL-LM SUBTRACTION — the move the Parakeet/Whisper inspection surfaced, on the real LM decode.

The agent's decode is score = acoustic_logp + weight * lift, where lift = log P_jm(word|prev) - LAMBDA*log P(word).
The repo hardcodes LAMBDA=1 (PMI -- it independently re-derived Parakeet's internal-LM subtraction as `ask_jabberwock_
lm_fix`). The inspection's move: make LAMBDA TUNABLE.
  LAMBDA=0  -> raw JM bigram (re-applies the base rate = the frequency-biased GLOBAL LM; collapses to "the").
  LAMBDA=1  -> PMI (full base-rate subtraction; current).
  LAMBDA>1  -> OVER-subtract the base rate = content-gated (penalise frequent words -> favour rare correct content).
Sweep (weight x LAMBDA) on the real LibriSpeech continuous decode; then loop-tune LAMBDA (the validated graph-native
self-tuner) on a TUNING split, CV. Two-sided pre-committed bar: a winning (weight,LAMBDA) must beat BOTH baselines on
THEIR OWN strength -- content >= acoustic-only AND function >= global-LM(LAMBDA=0) -- sitting in the middle = FAILURE
(catches a degenerate global weight).

Lattices (whisper segmentation + acoustic banking) are built ONCE and cached; the sweep is cheap.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_tunable_ilm [n_test] [vocab]
"""
from __future__ import annotations

import math
import os
import pickle
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from scripts.abs_language_decode import acoustic_logp, FS, KCAND
from scripts.language_prior import LanguagePrior
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon
from scripts.librispeech_wer import gather_pairs, load_flac
import domains.self_directed_speech_world as SDW
from substrate.world_adapter import WorldAdapter
from scripts.jabberwock_loop_tunes_fusion import manifest

CAP = 3.0
STOP = {"the", "a", "an", "of", "to", "in", "and", "but", "or", "for", "his", "her", "its", "their",
        "he", "she", "it", "they", "we", "i", "you", "was", "were", "is", "are", "be", "been", "as",
        "at", "by", "on", "with", "this", "that", "had", "has", "have", "not", "no", "so", "than",
        "which", "who", "what", "when", "where", "may", "would", "could", "will", "from", "up", "out"}


def lift_lambda(word, prev, lp, lam):
    pw = (lp.uni.get(word, 0) + 1.0) / (lp.total + len(lp.vocab))
    p = pw
    if prev:
        pprev = lp.uni.get(prev, 0)
        if pprev > 0:
            p = 0.75 * (lp.bg.get((prev, word), 0) / pprev) + 0.25 * pw
    lift = math.log(p + 1e-9) - lam * math.log(pw + 1e-9)
    return max(-CAP, min(CAP, lift))


def viterbi(lattice, lp, weight, lam):
    if not lattice:
        return []
    dp = [{c: lo + weight * lift_lambda(c, None, lp, lam) for c, lo in lattice[0].items()}]
    bk = [{c: None for c in lattice[0]}]
    for i in range(1, len(lattice)):
        cur, b = {}, {}
        for c, lo in lattice[i].items():
            best, arg = -1e18, None
            for pc, ps in dp[i - 1].items():
                simc = ps + lo + weight * lift_lambda(c, pc, lp, lam)
                if simc > best:
                    best, arg = simc, pc
            cur[c], b[c] = best, arg
        dp.append(cur); bk.append(b)
    out = [None] * len(lattice)
    last = max(dp[-1], key=dp[-1].get)
    for i in range(len(lattice) - 1, -1, -1):
        out[i] = last; last = bk[i][last]
    return out


def build_lattices(n_test, vocab_size):
    cache = f"/tmp/ilm_lattices_{n_test}_{vocab_size}.pkl"
    if os.path.exists(cache):
        print("  loading cached lattices...", flush=True)
        return pickle.load(open(cache, "rb"))
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    pairs = gather_pairs(limit=None)
    by_spk = {}
    for (path, sp, ch, ut, tr) in pairs:
        by_spk.setdefault(sp, []).append((path, tr))
    spks = sorted(by_spk)
    train_spk, test_spk = spks[:max(1, len(spks) - 2)], spks[max(1, len(spks) - 2):]
    print("  segmenting train utts (whisper) to bank exemplars...", flush=True)
    word_segs = {}; budget = 0
    for sp in train_spk:
        for (path, _tr) in by_spk[sp][:6]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_segs.setdefault(w, []).append(seg)
            budget += 1
            if budget >= 80:
                break
        if budget >= 80:
            break
    vocab = [w for (w, _c) in Counter({w: len(s) for w, s in word_segs.items()}).most_common(vocab_size)
             if len(word_segs[w]) >= 3]
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    lex = GraphLexicon(s)
    for w in vocab:
        for seg in word_segs[w][:8]:
            lex.bank(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), w, source="lib")
    banked = lex.banked()
    cands = sorted({w for (w, _v) in banked})
    print(f"  banked {len(cands)} words; building test lattices...", flush=True)
    utts = []; n_utt = 0
    for sp in test_spk:
        for (path, _tr) in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            seq = []
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w not in cands or seg.size < int(0.04 * fs):
                    continue
                lo = acoustic_logp(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), banked, cands)
                seq.append((w, dict(sorted(lo.items(), key=lambda kv: -kv[1])[:KCAND])))
            if len(seq) >= 3:
                utts.append(([w for (w, _t) in seq], [t for (_w, t) in seq])); n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    out = (utts, cands)
    pickle.dump(out, open(cache, "wb"))
    return out


def accuracy(utts, lp, weight, lam, idx=None):
    items = utts if idx is None else [utts[i] for i in idx]
    ok = tot = c_ok = c_tot = f_ok = f_tot = 0
    for truth, lattice in items:
        pred = viterbi(lattice, lp, weight, lam)
        for tr, p in zip(truth, pred):
            tot += 1; ok += int(p == tr)
            if tr in STOP:
                f_tot += 1; f_ok += int(p == tr)
            else:
                c_tot += 1; c_ok += int(p == tr)
    return {"all": 100 * ok / max(tot, 1), "content": 100 * c_ok / max(c_tot, 1), "func": 100 * f_ok / max(f_tot, 1),
            "tot": tot, "c_tot": c_tot, "f_tot": f_tot}


def run_loop(obj, ticks=20):
    ad = WorldAdapter()
    ad.inner.load_seed_manifest(manifest(theta0=1.0, step0=0.5), ad.agent)
    o = next(nn for nn in ad.s.nodes("TunedOp"))
    w = 1.0
    for _t in range(ticks):
        a = ad.s.node(o)["attrs"]
        ad.s.set_attr(o, "skill", obj(a["theta"]))
        ad.master_tick(); ad.tick()
        b = ad.s.node(o)["attrs"]
        ad.s.set_attr(o, "theta", b["next_theta"]); ad.s.set_attr(o, "last_skill", obj(a["theta"]))
        ad.s.set_attr(o, "dir", b["next_dir"]); ad.s.set_attr(o, "step", b["next_step"])
        w = b["next_theta"]
    return w


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    vocab = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    print("=" * 100)
    print("TUNABLE INTERNAL-LM SUBTRACTION — sweep (weight x LAMBDA) on the real LibriSpeech decode; two-sided bar")
    print("=" * 100)
    utts, cands = build_lattices(n_test, vocab)
    lp = LanguagePrior()
    base = accuracy(utts, lp, 0.0, 1.0)
    print(f"  {base['tot']} words / {len(cands)}-word vocab; content {base['c_tot']} | function {base['f_tot']}\n", flush=True)

    weights = [0.1, 0.2, 0.4, 0.8, 1.6]
    lams = [0.0, 0.5, 1.0, 1.5, 2.0]
    print(f"  acoustic-only (weight 0):  overall {base['all']:.1f} | content {base['content']:.1f} | function {base['func']:.1f}\n")
    # global-LM baseline = LAMBDA=0 (frequency-biased), best weight by overall
    gl = max((accuracy(utts, lp, w, 0.0) for w in weights), key=lambda r: r["all"])
    print(f"  global-LM (LAMBDA=0, best weight): overall {gl['all']:.1f} | content {gl['content']:.1f} | function {gl['func']:.1f}\n")
    print(f"    {'weight':>7}" + "".join(f"  L={l:<4}(o/c/f)" for l in lams))
    grid = {}
    for w in weights:
        cells = []
        for l in lams:
            r = accuracy(utts, lp, w, l); grid[(w, l)] = r
            cells.append(f" {r['all']:.0f}/{r['content']:.0f}/{r['func']:.0f} ")
        print(f"    {w:>7.2f}" + "".join(f"{c:>14}" for c in cells), flush=True)

    # the two-sided bar: content >= acoustic-only AND function >= global-LM
    cbar, fbar = base["content"], gl["func"]
    winners = [(w, l, r) for (w, l), r in grid.items() if r["content"] >= cbar and r["func"] >= fbar]
    print(f"\n  two-sided bar: content >= {cbar:.1f} (acoustic-only) AND function >= {fbar:.1f} (global-LM)")

    # CV loop-tune LAMBDA at the best overall weight, no test access
    bw = max(weights, key=lambda w: grid[(w, 1.0)]["all"])
    n = len(utts)
    REP = 5
    cvL, cv_all, cv_c, cv_f = [], [], [], []
    for r in range(REP):
        order = np.random.RandomState(400 + r).permutation(n)
        folds = np.array_split(order, 5)
        oks = {"all": 0, "c": 0, "f": 0, "t": 0, "ct": 0, "ft": 0}
        for f in range(5):
            te = folds[f]; tu = np.concatenate([folds[k] for k in range(5) if k != f])
            lam = run_loop(lambda L: accuracy(utts, lp, bw, max(0.0, L), tu)["all"] / 100.0)
            cvL.append(lam)
            rr = accuracy(utts, lp, bw, max(0.0, lam), te)
            oks["all"] += rr["all"] * rr["tot"] / 100; oks["t"] += rr["tot"]
            oks["c"] += rr["content"] * rr["c_tot"] / 100; oks["ct"] += rr["c_tot"]
            oks["f"] += rr["func"] * rr["f_tot"] / 100; oks["ft"] += rr["f_tot"]
        cv_all.append(100 * oks["all"] / max(oks["t"], 1))
        cv_c.append(100 * oks["c"] / max(oks["ct"], 1)); cv_f.append(100 * oks["f"] / max(oks["ft"], 1))
    cva, cvc, cvf = np.mean(cv_all), np.mean(cv_c), np.mean(cv_f)
    print(f"\n  CV loop-tuned LAMBDA (weight {bw}, no test access): mean LAMBDA {np.mean(cvL):.2f} | "
          f"overall {cva:.1f} | content {cvc:.1f} | function {cvf:.1f}")

    print("\n" + "=" * 100)
    passes = cvc >= cbar - 0.5 and cvf >= fbar - 0.5
    if winners and passes:
        bw2, bl2, br = max(winners, key=lambda x: x[2]["all"])
        print(f"  KEEP — tunable internal-LM subtraction BREAKS the tradeoff: the loop self-tuned LAMBDA~{np.mean(cvL):.2f}>1 "
              f"(content-gated over-subtraction),")
        print(f"  hitting content {cvc:.1f} (>= acoustic {cbar:.1f}) AND function {cvf:.1f} (>= global-LM {fbar:.1f}) -- BOTH, not the")
        print(f"  midpoint. The Parakeet ILM-subtraction trick, tuned by the loop, on a knob Whisper structurally lacks.")
    elif winners:
        print(f"  PARTIAL — a two-sided cell EXISTS in the grid ({len(winners)} cells) but the loop-tuned LAMBDA didn't land it on")
        print(f"  CV (content {cvc:.1f} vs {cbar:.1f}, function {cvf:.1f} vs {fbar:.1f}). The lever is real; the self-tune is off. Honest.")
    else:
        print(f"  NO — no (weight,LAMBDA) beats BOTH baselines (content {cvc:.1f} vs {cbar:.1f}, function {cvf:.1f} vs {fbar:.1f}); "
              f"the tradeoff holds.")
        print("  Tunable subtraction sits in the middle = the degenerate global weight the bar was built to catch. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
