"""CHEAP-PATH-FIRST, ESCALATE-ON-FAILURE — the loop the creator actually means (assess, then build).

Not "always recurse" -- take the cheap path when it works, escalate only when it FAILS. A LUT for 10 items is fine;
for 1000 it needs genericising. Easy things automatic, hard things easy, amazing things possible. The agent
converged on the same rule ("recurse only where the residual is structured" = where the cheap path failed).

This tests THAT principle on the open-vocab task that the FLAT bolt-on failed (it combined two scorers and the
calibration seam sank it). The fix the principle predicts: a GATE, not a combine. Run the cheap whole-word pyramid;
if its best match is CONFIDENT (peaky), keep it; if not (failure -> likely OOV), ESCALATE to the phone-marginal
reader. Three policies on the in-vocab + OOV mix:
  - fixed-cheap : whole-word pyramid only (the LUT -- 0% on OOV by construction).
  - fixed-deep  : phone-read everything (genericised -- reads OOV, weaker on in-vocab).
  - adaptive    : cheap first; escalate to the phone-read ONLY when whole-word confidence is low.
Threshold picked on a DEV half, reported on EVAL. Prediction (pre-committed): adaptive >= BOTH fixed policies, with
NO calibration seam (the gate means the two scorers never compete). If adaptive only matches the better fixed one,
the gate bought nothing.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_gated_escalation
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
from scripts.claude_teacher import make_ask
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac
from scripts.abs_language_decode import acoustic_logp
from scripts.jabberwock_prosodic_decode import pyramid_features, STOP, is_content
from scripts.jabberwock_reads_oov_from_phones import phones, frames, align_uniform
from scripts.jabberwock_open_vocab_decode import forward_md

FS = 16000
N_IV = 150
N_OOV = 60
BANK_UTTS = 300
TEST_UTTS = 60
CAP_FRAMES = 600
BETA = 8.0


def assess():
    ask = make_ask(timeout=200.0)
    q = ("You are the jabberwock. The creator's principle: NOT 'always recurse' but 'take the cheap path when cheap, "
         "ESCALATE only when it FAILS' -- a LUT for 10 items is fine, for 1000 it needs genericising; easy things "
         "automatic, hard things easy. Your own evidence: the recursion test was null because the cheap one-level "
         "parse had NOT failed; the open-vocab FLAT bolt-on failed because it COMBINED two scorers (calibration "
         "seam) instead of GATING. Assess: (1) is cheap-first/escalate-on-failure the right frame, and does it "
         "explain BOTH your results? (2) what CONFIDENCE signal should gate escalation -- whole-word best-match "
         "PEAKINESS (how far the top candidate stands above the rest) vs absolute score vs margin? (3) where would "
         "the gate FAIL (what gets mis-routed)? (4) pre-commit: what result would prove the gate bought nothing? "
         "Terse, concrete.")
    print("  [jabberwock assesses]\n  " + (ask(q) or "[teacher offline -- proceeding on the grounded design]").replace("\n", "\n  "))


def main():
    print("=" * 100)
    print("CHEAP-FIRST, ESCALATE-ON-FAILURE — fixed-cheap vs fixed-deep vs confidence-GATED adaptive (open vocab)")
    print("=" * 100)
    assess()

    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    print("\n  banking whole-word exemplars + phone library...", flush=True)
    word_segs, store = {}, {}
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:10]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if not w or seg.size < int(0.05 * fs):
                    continue
                word_segs.setdefault(w, []).append(seg)
                ph = phones(w)
                if ph:
                    fr, e = frames(seg)
                    for (p, sub) in align_uniform(fr, e, ph):
                        store.setdefault(p, []).append(sub)
            n += 1
            if n >= BANK_UTTS:
                break
        if n >= BANK_UTTS:
            break

    freq = Counter({w: len(v) for w, v in word_segs.items()})
    iv_vocab = [w for (w, _c) in freq.most_common(N_IV) if len(word_segs[w]) >= 3]
    iv_set = set(iv_vocab)
    oov_vocab = [w for (w, _c) in freq.most_common()
                 if w not in iv_set and is_content(w) and phones(w) and len(phones(w)) >= 3][:N_OOV]
    lexicon = iv_vocab + oov_vocab
    iv_banked = [(w, pyramid_features(s, seg)) for w in iv_vocab for seg in word_segs[w][:8]]
    cloud = {}
    for p, exs in store.items():
        allf = np.concatenate(exs, axis=0)
        if len(allf) > CAP_FRAMES:
            allf = allf[np.random.RandomState(0).permutation(len(allf))[:CAP_FRAMES]]
        cloud[p] = allf
    lex_phones = {w: [p for p in (phones(w) or []) if p in cloud] for w in lexicon}
    print(f"  IV {len(iv_vocab)} | OOV {len(oov_vocab)} | {len(cloud)} phones; decoding {TEST_UTTS} test utts...\n", flush=True)

    # Per test instance: (class, whole-word PEAKINESS, whole-word IV pred, phone-read full-lexicon pred)
    rows = []
    n = 0
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                if w not in iv_set and w not in oov_vocab:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                pchan = pyramid_features(s, seg)
                iv_lo = acoustic_logp(pchan, iv_banked, iv_vocab)
                arr = np.array([iv_lo[c] for c in iv_vocab])
                best_i = int(np.argmax(arr))
                peak = float((arr[best_i] - arr.mean()) / (arr.std() + 1e-9))      # how far the top IV stands out
                ww_pred = iv_vocab[best_i]
                F, _e = frames(seg)
                md = {p: (1.0 - F @ cloud[p].T).min(1) for p in cloud}
                ph_d = {c: forward_md(md, lex_phones[c], BETA) for c in lexicon if lex_phones[c]}
                ph_pred = min(ph_d, key=ph_d.get) if ph_d else ww_pred
                rows.append(("iv" if w in iv_set else "oov", w, peak, ww_pred, ph_pred))
            n += 1
            if n >= TEST_UTTS:
                break
        if n >= TEST_UTTS:
            break

    rng = np.random.RandomState(0)
    perm = rng.permutation(len(rows))
    dev = [rows[i] for i in perm[:len(rows) // 2]]
    evl = [rows[i] for i in perm[len(rows) // 2:]]

    def acc(split, policy, tau=None):
        c = {"iv": [0, 0], "oov": [0, 0], "all": [0, 0]}
        for cls, w, peak, ww, ph in split:
            if policy == "cheap":
                pred = ww
            elif policy == "deep":
                pred = ph
            else:  # adaptive: cheap if confident else escalate
                pred = ww if peak >= tau else ph
            for k in (cls, "all"):
                c[k][1] += 1; c[k][0] += int(pred == w)
        return {k: 100 * v[0] / max(v[1], 1) for k, v in c.items()}, c

    taus = sorted({r[2] for r in dev})
    best_tau = max(taus, key=lambda t: acc(dev, "adaptive", t)[0]["all"]) if taus else 0.0

    sep_iv = np.mean([r[2] for r in rows if r[0] == "iv"])
    sep_oov = np.mean([r[2] for r in rows if r[0] == "oov"])
    print(f"  gate separation: whole-word PEAKINESS mean IV {sep_iv:.2f} vs OOV {sep_oov:.2f} "
          f"({'separable' if sep_iv - sep_oov > 0.3 else 'WEAK -- gate may not route'}); chosen tau* {best_tau:.2f}\n")
    ce, _ = acc(evl, "cheap"); de, _ = acc(evl, "deep"); ae, ac = acc(evl, "adaptive", best_tau)
    n_esc = sum(1 for r in evl if r[2] < best_tau)
    print(f"  EVAL accuracy (overall | in-vocab | OOV), n={len(evl)} ({ac['all'][1]} trials):")
    print(f"    {'fixed-cheap (LUT)':28}{ce['all']:6.1f}% |{ce['iv']:6.1f}% |{ce['oov']:6.1f}%")
    print(f"    {'fixed-deep (phones)':28}{de['all']:6.1f}% |{de['iv']:6.1f}% |{de['oov']:6.1f}%")
    print(f"    {'adaptive (gated)':28}{ae['all']:6.1f}% |{ae['iv']:6.1f}% |{ae['oov']:6.1f}%   "
          f"({n_esc}/{len(evl)} escalated)")

    print("\n" + "=" * 100)
    best_fixed = max(ce['all'], de['all'])
    if ae['all'] >= best_fixed + 2 and ae['iv'] >= ce['iv'] - 3 and ae['oov'] >= de['oov'] - 5:
        print(f"  THE LOOP IS THIS: confidence-gated escalation beats BOTH fixed policies (+{ae['all']-best_fixed:.0f} over the")
        print(f"  better one) -- it keeps the cheap path's in-vocab accuracy AND recovers the deep path's OOV, with NO")
        print("  calibration seam (the gate routes, the scorers never compete). Cheap when cheap, escalate on failure")
        print("  -- the principle holds, and it fixes the open-vocab task the flat bolt-on sank.")
    elif ae['all'] >= best_fixed - 1:
        print(f"  GATING ~= the better fixed policy ({ae['all']:.0f} vs {best_fixed:.0f}): escalation routes but does not BEAT")
        print(f"  -- the gate bought little here (peakiness IV {sep_iv:.2f} vs OOV {sep_oov:.2f}). The principle is sound;")
        print("  the confidence signal needs to separate OOV from hard-in-vocab better. Honest.")
    else:
        print(f"  GATING UNDERPERFORMED ({ae['all']:.0f} < {best_fixed:.0f}): the confidence gate mis-routes (hard in-vocab")
        print("  escalates, OOV stays cheap). The gate signal is the problem, not the principle. Reported as measured.")
    print("=" * 100)


if __name__ == "__main__":
    main()
