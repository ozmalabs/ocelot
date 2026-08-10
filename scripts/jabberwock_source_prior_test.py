"""THE SOURCE-PRIOR TEST (the jabberwock's design, with its kill-control) — does CONTEXT help OOV through a PRIOR?

The deciding measurement showed no cheap AUDIO LIKELIHOOD cue separates OOV (best 0.63). The agent's resolution:
context helps not through likelihood but through a PRIOR recovered from the SOURCE/SITUATION signature -- a cheap,
low-D channel feature that carries NO phone identity, inverted to a vocabulary prior. Its design + falsifier:

  A "situation" bundles a CHANNEL signature with a VOCABULARY. S1 = full-band channel + content set V1; S2 =
  telephone band-limit (300-3400 Hz) + content set V2 (V1, V2 disjoint). A test instance of a V1 word goes through
  full-band; a V2 word through the telephone channel. The SOURCE calculator reads ONLY the high-frequency energy
  ratio (band-edge) -- it cannot tell `cat` from `dog`, only studio from telephone -> it infers the situation ->
  it applies that situation's vocabulary PRIOR before the likelihood speaks. Decode held-out OOV content words
  (where the likelihood is blind) three ways: likelihood-only, +REAL source-prior, +SHUFFLED source-prior.

  KILL CONTROL: the SHUFFLED-source lift must collapse to zero. If real-source lifts OOV recovery clearly above
  likelihood-only AND shuffled-source does not, context provably helped THROUGH THE PRIOR on words the likelihood
  could not see (the source feature carries no phone identity, so it cannot be a disguised likelihood cue). If
  real ~= shuffled, killed -- the 'prior' was leaking likelihood.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_source_prior_test
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
from scripts.jabberwock_reads_oov_from_phones import phones, frames, align_uniform, STOP
from scripts.jabberwock_open_vocab_decode import forward_md

FS = 16000
N_VOCAB = 30          # held-out content words split into two disjoint sets (small enough the likelihood has a FLOOR)
BANK_UTTS = 300
TEST_UTTS = 160
CAP_FRAMES = 600
BETA = 8.0
HF_THRESH = 0.004     # high-freq energy ratio below this = telephone (band-limited=exactly 0) = S2; speech has little >3.4kHz
LAMBDAS = [0.0, 0.15, 0.3, 0.6, 1.0]    # prior strength (0 = likelihood-only)


def bandlimit(x, lo=300.0, hi=3400.0):
    """Telephone channel: brick-wall band-pass via rFFT (zero bins outside 300-3400 Hz)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / FS)
    X[(f < lo) | (f > hi)] = 0.0
    return np.fft.irfft(X, n=len(x))


def hf_ratio(x):
    """SOURCE feature: fraction of spectral energy above 3.4 kHz. ~0 for telephone, substantial for full-band.
    Carries NO phone identity -- the same low value for ANY band-limited word."""
    X = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1.0 / FS)
    lo = X[(f >= 50) & (f <= 8000)].sum()
    hi = X[(f > 3400) & (f <= 8000)].sum()
    return float(hi / (lo + 1e-12))


def main():
    print("=" * 100)
    print("SOURCE-PRIOR TEST — does a channel-only situation prior help OOV where the likelihood is blind? (+ shuffle)")
    print("=" * 100)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    print("\n  banking phone library + choosing the two situation vocabularies...", flush=True)
    store, seen = {}, Counter()
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:10]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if not w or seg.size < int(0.05 * fs):
                    continue
                seen[w] += 1
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

    # held-out content words (these are the OOV candidates), split into two DISJOINT situation vocabularies
    content = [w for (w, _c) in seen.most_common()
               if w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4][:N_VOCAB]
    V1 = set(content[0::2]); V2 = set(content[1::2])      # disjoint, interleaved
    vocab = sorted(V1 | V2)
    cloud = {}
    for p, exs in store.items():
        allf = np.concatenate(exs, axis=0)
        if len(allf) > CAP_FRAMES:
            allf = allf[np.random.RandomState(0).permutation(len(allf))[:CAP_FRAMES]]
        cloud[p] = allf
    vphones = {w: [p for p in (phones(w) or []) if p in cloud] for w in vocab}
    print(f"  {len(vocab)} OOV content words: |V1|={len(V1)} (full-band) |V2|={len(V2)} (telephone); "
          f"{len(cloud)} phones banked\n", flush=True)

    # score each test instance: true word + its phone-marginal distance over the full vocab + detected situation
    print(f"  decoding {TEST_UTTS} test utts (situation = channel determined by vocab set)...", flush=True)
    items = []          # (true_word, true_set, det_set, {word: phone_dist})
    src_ok = src_tot = 0
    n = 0
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                if w not in V1 and w not in V2:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                true_set = 1 if w in V1 else 2
                audio = seg if true_set == 1 else bandlimit(seg)        # the situation's CHANNEL
                det_set = 1 if hf_ratio(audio) >= HF_THRESH else 2      # SOURCE calculator (channel only)
                src_tot += 1; src_ok += int(det_set == true_set)
                F, _e = frames(np.asarray(audio, dtype=np.float64))
                md = {p: (1.0 - F @ cloud[p].T).min(1) for p in cloud}
                pd = {c: forward_md(md, vphones[c], BETA) for c in vocab if vphones[c]}
                items.append((w, true_set, det_set, pd))
            n += 1
            if n >= TEST_UTTS:
                break
        if n >= TEST_UTTS:
            break

    print(f"  {len(items)} OOV-content instances; source-detect accuracy {100*src_ok/max(src_tot,1):.0f}% "
          f"(channel full-band vs telephone)\n", flush=True)

    rng = np.random.RandomState(7)
    shuf = [int(rng.randint(1, 3)) for _ in items]         # random situation label per instance (the kill control)

    def top1(lam, mode):
        """mode: 'det' (real source), 'shuffle' (kill control), 'oracle' (true situation = prior-mechanism ceiling)."""
        ok = 0
        for i, (w, ts, det, pd) in enumerate(items):
            d = ts if mode == "oracle" else (shuf[i] if mode == "shuffle" else det)
            inset = (V1 if d == 1 else V2)
            score = {c: pd[c] - (lam if c in inset else 0.0) for c in pd}   # prior: favour the detected set
            if min(score, key=score.get) == w:
                ok += 1
        return 100.0 * ok / max(len(items), 1)

    base = top1(0.0, "det")
    print(f"  OOV-content top-1 (likelihood-only = {base:.1f}%; chance ~{100.0/len(vocab):.1f}%):")
    print(f"    {'lambda':>8}{'+REAL-source':>15}{'+SHUFFLED':>12}{'+ORACLE-situation':>19}")
    best_real = base; best_lam = 0.0
    for lam in LAMBDAS[1:]:
        r = top1(lam, "det"); sh = top1(lam, "shuffle"); orc = top1(lam, "oracle")
        if r > best_real:
            best_real, best_lam = r, lam
        print(f"    {lam:>8.2f}{r:>14.1f}%{sh:>11.1f}%{orc:>18.1f}%")

    sh_at_best = top1(best_lam, "shuffle")
    print("\n" + "=" * 100)
    real_lift = best_real - base
    shuf_lift = sh_at_best - base
    print(f"  best REAL-source +{real_lift:.1f} pts (lambda {best_lam}); SHUFFLED-source at same lambda "
          f"{shuf_lift:+.1f} pts.")
    if real_lift >= 5 and real_lift >= shuf_lift + 4:
        print(f"  CONTEXT HELPS OOV THROUGH THE PRIOR: the channel-only source feature -- which carries NO phone")
        print(f"  identity -- lifts OOV recovery {base:.0f}%->{best_real:.0f}% ({real_lift:+.0f}), and the SHUFFLE CONTROL")
        print(f"  collapses it ({shuf_lift:+.0f}). The lift comes through the situation->vocabulary PRIOR on words the")
        print("  likelihood could not see, NOT a disguised likelihood cue. The agent's design holds; CONTEXT is a")
        print("  real, orthogonal, cheap lever -- weighted by a source the likelihood is blind to.")
    elif real_lift >= 5:
        print(f"  AMBIGUOUS: real-source lifts (+{real_lift:.0f}) but the shuffle does NOT fully collapse ({shuf_lift:+.0f}) --")
        print("  the prior is partly leaking likelihood / set-size effects. Tighten the control before believing it.")
    else:
        print(f"  CONTEXT DID NOT HELP ({real_lift:+.0f}): even a correct situation prior didn't recover OOV here -- the")
        print("  source->vocabulary path is too weak at this scale, or the likelihood floor is too low to lift. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
