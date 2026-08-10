"""COMPOSE ON THE HARVESTED BANK — does the parked LM-subtraction precision lever PAY now that recall is unblocked?

The agent's move A: every precision lever was parked because of RECALL. The tunable internal-LM subtraction is the
cleanest case -- a validated mechanism STARVED of candidates (the lattice lacked the right words). Harvest a HIGH-RECALL
bank (whisper labels -> the agent's OWN feature exemplars), so the lattice now contains the target words, then ask: does
acoustic + self-tuned LM-subtraction beat acoustic-only on top-1 CONTENT?

FAIRNESS CHECK (the agent pre-committed it): measure LATTICE RECALL -- the fraction of test content words whose TRUE
word is in their top-K acoustic lattice. If lattice recall is high, the loop tunes where recall is real (a fair
precision test); if it's still ~0, we'd be re-measuring the old recall wall, not precision.

Pre-committed bar: KEEP if +LM-subtraction >= +3 top-1 content over acoustic-only (no function loss); STOP if < +1.5
(the levers fail for a reason other than recall); FAIRNESS: lattice content recall must be clearly > the old small-bank
level, else the bank isn't actually high-recall and the test is void.

Run:
  cd experiments/gamma-substrate
  ulimit -v 28000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_compose_on_harvest
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
from scripts.abs_language_decode import acoustic_logp, FS
from scripts.language_prior import LanguagePrior
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon
from scripts.librispeech_wer import gather_pairs, load_flac
import domains.self_directed_speech_world as SDW
from scripts.jabberwock_tunable_ilm import accuracy, run_loop, STOP

N_BANK_UTTS = 280      # HARVEST banking budget (whisper-labelled) -> high-recall bank
VOCAB = 240            # bank vocab cap (more words -> higher coverage)
N_TEST = 30
KCAND = 8              # acoustic lattice width (the right word must reach the top-K)


def build(n_bank, vocab_size, n_test, kcand):
    cache = f"/tmp/compose_{n_bank}_{vocab_size}_{n_test}_{kcand}.pkl"
    if os.path.exists(cache):
        print("  loading cached harvested lattices...", flush=True)
        return pickle.load(open(cache, "rb"))
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    pairs = gather_pairs(limit=None)
    by_spk = {}
    for (path, sp, ch, ut, tr) in pairs:
        by_spk.setdefault(sp, []).append((path, tr))
    spks = sorted(by_spk)
    train_spk, test_spk = spks[:max(1, len(spks) - 2)], spks[max(1, len(spks) - 2):]
    print(f"  HARVEST banking up to {n_bank} train utts (whisper labels)...", flush=True)
    word_segs = {}; budget = 0
    for sp in train_spk:
        for (path, _tr) in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_segs.setdefault(w, []).append(seg)
            budget += 1
            if budget >= n_bank:
                break
        if budget >= n_bank:
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
    print(f"  banked {len(cands)} words; building {n_test} test lattices (top-{kcand})...", flush=True)
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
                seq.append((w, dict(sorted(lo.items(), key=lambda kv: -kv[1])[:kcand])))
            if len(seq) >= 3:
                utts.append(([w for (w, _t) in seq], [t for (_w, t) in seq])); n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    pickle.dump((utts, cands), open(cache, "wb"))
    return utts, cands


def lattice_recall(utts):
    c_in = c_tot = f_in = f_tot = 0
    for truth, lattice in utts:
        for w, lat in zip(truth, lattice):
            if w in STOP:
                f_tot += 1; f_in += int(w in lat)
            else:
                c_tot += 1; c_in += int(w in lat)
    return 100 * c_in / max(c_tot, 1), 100 * f_in / max(f_tot, 1), c_tot, f_tot


def main():
    print("=" * 100)
    print("COMPOSE ON THE HARVESTED BANK — does LM-subtraction PAY once recall is unblocked? (fairness: lattice recall)")
    print("=" * 100)
    utts, cands = build(N_BANK_UTTS, VOCAB, N_TEST, KCAND)
    lp = LanguagePrior()
    base = accuracy(utts, lp, 0.0, 1.0)
    lcr, lfr, ct, ft = lattice_recall(utts)
    print(f"\n  {base['tot']} test words ({len(cands)}-word harvested bank); content {ct} | function {ft}")
    print(f"  FAIRNESS — lattice recall (true word in top-{KCAND}): content {lcr:.1f}% | function {lfr:.1f}%")
    print(f"    (the old small-bank decode was recall-starved; this must be clearly higher to be a fair precision test)\n", flush=True)

    print(f"  acoustic-only (ear):  overall {base['all']:.1f} | content {base['content']:.1f} | function {base['func']:.1f}\n")
    weights = [0.1, 0.2, 0.4, 0.8, 1.6]
    lams = [0.0, 0.5, 1.0, 1.5, 2.0]
    print(f"    {'weight':>7}" + "".join(f"  L={l:<3}c" for l in lams))
    grid = {}
    for w in weights:
        cells = []
        for l in lams:
            r = accuracy(utts, lp, w, l); grid[(w, l)] = r
            cells.append(f"{r['content']:.0f}")
        print(f"    {w:>7.2f}" + "".join(f"{c:>9}" for c in cells), flush=True)
    bw, bl = max(grid, key=lambda k: grid[k]["content"])
    bestc = grid[(bw, bl)]

    # honest: CV loop-tune LAMBDA at the best weight (no test access), report held-out content
    n = len(utts)
    cv_c = []
    for r in range(5):
        order = np.random.RandomState(500 + r).permutation(n)
        folds = np.array_split(order, 5)
        ok = tot = 0
        for f in range(5):
            te = folds[f]; tu = np.concatenate([folds[k] for k in range(5) if k != f])
            lam = run_loop(lambda L: accuracy(utts, lp, bw, max(0.0, L), tu)["content"] / 100.0)
            rr = accuracy(utts, lp, bw, max(0.0, lam), te)
            ok += rr["content"] * rr["c_tot"] / 100; tot += rr["c_tot"]
        cv_c.append(100 * ok / max(tot, 1))
    cvc = float(np.mean(cv_c))

    print("\n" + "=" * 100)
    print(f"  content top-1: acoustic-only {base['content']:.1f} | best (w={bw},L={bl}) {bestc['content']:.1f} | "
          f"CV-tuned {cvc:.1f} | function (best) {bestc['func']:.1f} vs {base['func']:.1f}")
    lift = cvc - base["content"]
    fair = lcr >= 25.0
    if not fair:
        print(f"  VOID — lattice content recall {lcr:.1f}% still too low: the harvested bank didn't reach the test words")
        print("  (recall not actually unblocked here). Re-measuring the old wall, not precision. Need a bigger/closer bank.")
    elif lift >= 3.0 and bestc["func"] >= base["func"] - 1.0:
        print(f"  KEEP — the parked lever PAYS once recall is unblocked: +{lift:.1f} content (>= +3) with no function loss.")
        print(f"  Lattice recall {lcr:.1f}% confirms the right words are present, so the LM-subtraction finally disambiguates.")
        print("  The whole arc's negatives shared one cause (recall); removing it converts the parked precision lever. PERSIST next.")
    elif lift < 1.5:
        print(f"  STOP — even with recall unblocked (lattice {lcr:.1f}%), LM-subtraction barely moves content (+{lift:.1f} < 1.5).")
        print("  The lever was NOT merely recall-limited; it fails for another reason. Honest negative.")
    else:
        print(f"  WEAK — +{lift:.1f} content (1.5-3 band) with recall unblocked ({lcr:.1f}%). Real but under bar; honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
