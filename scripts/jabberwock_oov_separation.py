"""THE DECIDING MEASUREMENT (the agent's pre-commit) — does ANY cheap cue separate in-vocab from OOV?

The gated gate was blind because its one cue (spectral-pyramid PEAKINESS) couldn't tell in-vocab from OOV
(1.73 vs 1.77). The design lives or dies on a factual question, not architecture: is the OOV/failure signal PRESENT
in a diverse cheap check, or ABSENT from all cheap things? This MEASURES it -- per item (same in-vocab + OOV mix),
several candidate cues, each scored by its standalone in/OOV AUROC:
  - ww_peak      : whole-word pyramid peakiness (best/rest) -- the BLIND gate, baseline.
  - ww_best_abs  : whole-word ABSOLUTE best log-likelihood -- the most direct "did the LUT find a good match" (the
                   gate never used this; an OOV word has NO banked whole-word, so its best match should be poorer).
  - ww_margin    : whole-word best - 2nd (raw).
  - phone_best   : phone-marginal forward ABSOLUTE best (negated) -- the agent's NAMED temporal/compositional cue.
  - phone_margin : phone best - 2nd.
  - agree        : does the spectral winner == the temporal winner? -- the agent's CROSS-CUE DIVERGENCE (un-collapsed
                   spectral-vs-temporal disagreement = the real escalation signal it said the scalar gate threw away).
THE PRE-COMMIT: AUROC <= 0.60 for ALL cheap cues kills the design (OOV below the cheap floor -> only a deep decoder
could gate). Any cue >= 0.75 proves a diverse separating cue exists -> build the 2-cue manifold gate.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_oov_separation
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
from scripts.abs_language_decode import acoustic_logp
from scripts.jabberwock_prosodic_decode import pyramid_features, is_content
from scripts.jabberwock_reads_oov_from_phones import phones, frames, align_uniform
from scripts.jabberwock_open_vocab_decode import forward_md

FS = 16000
N_IV, N_OOV, BANK_UTTS, TEST_UTTS, CAP_FRAMES, BETA = 150, 60, 300, 60, 600, 8.0


def auroc(scores, is_iv):
    """P(score_iv > score_oov); oriented so HIGHER score = more in-vocab. 0.5 = no separation."""
    pos = np.array([s for s, l in zip(scores, is_iv) if l])
    neg = np.array([s for s, l in zip(scores, is_iv) if not l])
    if not len(pos) or not len(neg):
        return 0.5
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def main():
    print("=" * 100)
    print("DECIDING MEASUREMENT — does ANY cheap cue separate in-vocab from OOV? (in/OOV AUROC per cue)")
    print("=" * 100)
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
    print(f"  IV {len(iv_vocab)} | OOV {len(oov_vocab)} | {len(cloud)} phones; scoring {TEST_UTTS} test utts...\n", flush=True)

    CUES = ["ww_peak", "ww_best_abs", "ww_margin", "phone_best", "phone_margin", "agree"]
    rec = {c: [] for c in CUES}
    is_iv = []
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
                a = np.sort(np.array([iv_lo[c] for c in iv_vocab]))[::-1]
                ww_pred = max(iv_lo, key=iv_lo.get)
                rec["ww_peak"].append(float((a[0] - a.mean()) / (a.std() + 1e-9)))
                rec["ww_best_abs"].append(float(a[0]))
                rec["ww_margin"].append(float(a[0] - a[1]))
                F, _e = frames(seg)
                md = {p: (1.0 - F @ cloud[p].T).min(1) for p in cloud}
                ph_d = {c: forward_md(md, lex_phones[c], BETA) for c in lexicon if lex_phones[c]}
                pv = np.sort(np.array(list(ph_d.values())))            # distances, ascending (lower=better)
                ph_pred = min(ph_d, key=ph_d.get)
                rec["phone_best"].append(float(-pv[0]))                # negate: higher = better match = more iv-like
                rec["phone_margin"].append(float(pv[1] - pv[0]) if len(pv) > 1 else 0.0)
                rec["agree"].append(1.0 if ww_pred == ph_pred else 0.0)
                is_iv.append(w in iv_set)
            n += 1
            if n >= TEST_UTTS:
                break
        if n >= TEST_UTTS:
            break

    n_iv = sum(is_iv); n_oov = len(is_iv) - n_iv
    print(f"  {len(is_iv)} items ({n_iv} in-vocab, {n_oov} OOV). in/OOV AUROC per cheap cue "
          f"(0.50 = blind; >=0.75 separating):\n")
    results = {}
    for c in CUES:
        au = auroc(rec[c], is_iv)
        results[c] = max(au, 1.0 - au)                                # separation power (either direction)
        arrow = "  <- separates" if results[c] >= 0.75 else ("  (weak)" if results[c] >= 0.6 else "")
        print(f"    {c:14} AUROC {au:.2f}  (sep {results[c]:.2f}){arrow}")

    best_cue = max(CUES, key=lambda c: results[c])
    best = results[best_cue]
    print("\n" + "=" * 100)
    if best >= 0.75:
        print(f"  A DIVERSE SEPARATING CUE EXISTS: {best_cue} separates in-vocab from OOV at AUROC {best:.2f} where the")
        print(f"  blind peakiness gate could not (sep {results['ww_peak']:.2f}). The design is VINDICATED -- the failure")
        print("  signal IS present in a cheap check, the gated gate just read the wrong one. Build the manifold gate on")
        print(f"  {best_cue} (+ the others as it helps). The escalation path the design needs is real.")
    elif best >= 0.6:
        print(f"  PARTIAL: best cue {best_cue} sep {best:.2f} -- some signal, below the 0.75 bar. The design is")
        print("  PLAUSIBLE but the cheap cues are weak OOV detectors; a 2-cue combo might clear it (reported above).")
    else:
        print(f"  THE DESIGN IS DEAD FOR THIS SYSTEM: every cheap cue is blind to OOV (best {best_cue} sep {best:.2f} < 0.60).")
        print("  The OOV/failure signal is ABSENT from all cheap checks -- no manifold over them can read it; only a")
        print("  (currently broken) deep decoder could gate. The agent's pre-commit fired against the design. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
