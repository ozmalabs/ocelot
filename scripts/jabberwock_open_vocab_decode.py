"""OPEN-VOCABULARY DECODE — wire the phone-marginal reader as the OOV path of the whole-word decode.

The content-word bottleneck is two problems: representation (fixed for KNOWN words by the multi-scale pyramid,
20.8% content) AND open vocabulary (~half of real content words are never banked, so the whole-word decode SKIPS
them -- 0% by construction). The speech-BPL build reads a never-banked word from a phone library by marginal
alignment. This wires the two into one recogniser:
  - lexicon = IN-VOCAB whole-word candidates (banked, scored by the pyramid) + OOV candidates (NOT banked whole,
    scored by the phone-marginal forward algorithm over the phone library).
  - the two heterogeneous scorers are CALIBRATED onto one scale: per position, each scorer's candidate scores are
    z-normalised within its own pool -> a comparable acoustic log-likelihood (higher=better); an `oov_bias` trims
    the OOV pool (its reads are less reliable). Top-K -> the lattice the LM+prosody decode already consumes.
The claim: OOV words go from 0% (unreadable/skipped) to above chance, WITHOUT collapsing the in-vocab words --
the decode becomes open-vocabulary. Reports acoustic recall split IN-VOCAB vs OOV, CLOSED (iv-only) vs OPEN.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_open_vocab_decode
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
from scripts.abs_language_decode import acoustic_logp, lm_logp, register_language_prior
from scripts.language_prior import LanguagePrior
from scripts.jabberwock_prosodic_decode import pyramid_features, prosodic_logp, STOP, is_content
from scripts.jabberwock_reads_oov_from_phones import phones, frames, align_uniform
from scripts.jabberwock_marginal_phone_read import _softmin2

FS = 16000
N_IV = 150           # in-vocab whole-word lexicon (banked)
N_OOV = 60           # OOV content words (NOT banked whole; read from phones)
BANK_UTTS = 300
TEST_UTTS = 50
KCAND = 10
CAP_FRAMES = 600
BETA = 8.0           # phone-alignment marginalisation temperature (the speech-BPL best)
OOV_BIAS = 0.5       # trim OOV log-likelihoods (their reads are less reliable than whole-word)


def forward_md(md, phs, beta):
    """Forward (marginal) phone-alignment distance using a PRECOMPUTED per-phone 1-NN distance dict `md`."""
    phs = [p for p in phs if p in md]
    L = len(phs)
    if L == 0:
        return 1e9
    T = len(md[phs[0]])
    if T < L:
        return 1e9
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


def zlogL(score_map, lower_is_better):
    """Calibrate one scorer's per-position candidate scores to a comparable log-likelihood (z-norm, higher=better)."""
    if not score_map:
        return {}
    v = np.array(list(score_map.values())); mu, sd = v.mean(), v.std() + 1e-9
    sign = -1.0 if lower_is_better else 1.0
    return {w: sign * (sc - mu) / sd for w, sc in score_map.items()}


def main():
    print("=" * 100)
    print("OPEN-VOCABULARY DECODE — phone-marginal reader as the OOV path of the whole-word pyramid decode")
    print("=" * 100)

    lp = LanguagePrior(); register_language_prior(lp)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    # ---- bank: whole-word exemplars (for IV vocab) + phone library (for OOV), from the same train pass ----
    print("\n  banking whole-word exemplars + phone library from train...", flush=True)
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
    # OOV lexicon: frequent CONTENT words, CMU-known, NOT in the whole-word bank
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
    oov_phones = {w: [p for p in phones(w) if p in cloud] for w in oov_vocab}
    print(f"  IV {len(iv_vocab)} whole-word | OOV {len(oov_vocab)} phone-read | {len(cloud)} phones in library\n")

    # ---- score the test set ----
    def score_clip(seg):
        """Return per-candidate calibrated logL for the FULL lexicon (IV via pyramid, OOV via phone-marginal)."""
        pchan = pyramid_features(s, seg)
        iv_lo = acoustic_logp(pchan, iv_banked, iv_vocab)            # {w: logp}, higher better
        F, _e = frames(seg)
        uniq = sorted({p for ph in oov_phones.values() for p in ph})
        md = {p: (1.0 - F @ cloud[p].T).min(1) for p in uniq}
        oov_d = {w: forward_md(md, oov_phones[w], BETA) for w in oov_vocab if oov_phones[w]}
        iv_L = zlogL(iv_lo, lower_is_better=False)
        oov_L = {w: v - OOV_BIAS for w, v in zlogL(oov_d, lower_is_better=True).items()}
        return iv_L, oov_L

    print(f"  decoding {TEST_UTTS} test utterances (lexicon {len(lexicon)}; OOV via forward beta={BETA})...\n", flush=True)
    # recall counters: [top1, top5, total]
    R = {"closed": {"iv": [0, 0, 0], "oov": [0, 0, 0]}, "open": {"iv": [0, 0, 0], "oov": [0, 0, 0]}}
    n = 0
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                if w not in iv_set and w not in oov_vocab:          # truly unknown -> out of scope
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                cls = "iv" if w in iv_set else "oov"
                iv_L, oov_L = score_clip(seg)
                for mode, pool in (("closed", iv_L), ("open", {**iv_L, **oov_L})):
                    ranked = sorted(pool, key=lambda c: -pool[c])
                    R[mode][cls][2] += 1
                    if ranked and ranked[0] == w:
                        R[mode][cls][0] += 1
                    if w in ranked[:5]:
                        R[mode][cls][1] += 1
            n += 1
            if n >= TEST_UTTS:
                break
        if n >= TEST_UTTS:
            break

    def line(mode, cls):
        t1, t5, tot = R[mode][cls]
        return f"{100*t1/max(tot,1):5.1f}% /{100*t5/max(tot,1):5.1f}%  (n={tot})"
    print(f"  acoustic recall (top-1 / top-5), by test-word class:")
    print(f"    {'':20}{'IN-VOCAB':>22}{'OOV':>22}")
    print(f"    {'CLOSED (iv-only)':20}{line('closed','iv'):>22}{line('closed','oov'):>22}")
    print(f"    {'OPEN (iv+phone-oov)':20}{line('open','iv'):>22}{line('open','oov'):>22}")

    oov_open1 = R["open"]["oov"][0] / max(R["open"]["oov"][2], 1)
    oov_open5 = R["open"]["oov"][1] / max(R["open"]["oov"][2], 1)
    iv_closed1 = R["closed"]["iv"][0] / max(R["closed"]["iv"][2], 1)
    iv_open1 = R["open"]["iv"][0] / max(R["open"]["iv"][2], 1)
    chance = 1.0 / max(len(lexicon), 1)
    print("\n" + "=" * 100)
    print(f"  OOV words: CLOSED 0% (skipped by construction) -> OPEN {oov_open1*100:.0f}%/{oov_open5*100:.0f}% top-1/5 "
          f"({oov_open1/chance:.0f}x chance); IN-VOCAB top-1 {iv_closed1*100:.0f}% -> {iv_open1*100:.0f}% (open).")
    if oov_open1 > chance * 2 and iv_open1 >= iv_closed1 - 0.03:
        print("  OPEN VOCABULARY ACHIEVED: words never banked whole are now read from the phone library through the")
        print("  same decode, above chance, WITHOUT collapsing the in-vocab words. The phone-marginal reader is wired")
        print("  in as the OOV path -- whole-word pyramid for known words, compositional phones for the open vocabulary.")
    elif oov_open1 > chance * 2:
        print(f"  OOV words become readable ({oov_open1*100:.0f}%) but the in-vocab words drop ({iv_closed1*100:.0f}->{iv_open1*100:.0f}%): the")
        print("  OOV pool adds confusers the calibration doesn't fully separate. The open-vocab CAPABILITY is shown;")
        print("  the IV/OOV calibration (oov_bias) is the tunable. Honest.")
    else:
        print(f"  OOV recall stayed near chance ({oov_open1*100:.0f}%); the phone path doesn't yet surface OOV words in the")
        print("  mixed lexicon. Reported as measured.")
    print("=" * 100)


if __name__ == "__main__":
    main()
