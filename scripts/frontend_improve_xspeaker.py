"""frontend_improve_xspeaker — POINT THE AGENT AT THE FRONT END.

The confirmed RELATIONAL decoder (domains/relational_shape: per-frame ordinal
band-RANK profile ++ whole-unit self-similarity, native DtwTo) caps cross-speaker
recognition at ~40% (V=10) / ~23% (V=20) on Speech Commands.  Every speech result
this session ran on the SAME ~32-band gammatone ENERGY-ENVELOPE front end.  If the
wall is cross-speaker DISCRIMINABILITY, the only untouched place it can come from is
the FRONT END — the input the rank decoder reads.

THE SPLIT (what this script does vs what the AGENT decides):
  * The AGENT decides WHICH front-end transform to use, by its OWN label-free
    selector (domains/audio_basis_select: shift-coherence + effective dimensionality
    — NO accuracy, NO labels-as-classifier).  The selector is run over a family of
    candidate front ends and the agent PICKS the winner by the selector value.  This
    auditably resolves the directive's TENSION (finer resolution must be BOTH more
    discriminative AND still VTL/speaker-stable): shift-coherence IS the VTL-stability
    criterion, so the selector will not pick a resolution that is less speaker-stable.
  * This harness only EXTRACTS the candidate `frames x bands` matrices (I/O-boundary
    DSP — the SAME category as the existing gammatone front end) and ENACTS the
    do-contrast.  The recognition decision is the CONFIRMED relational decoder, native
    (substrate.evaluate DtwTo), UNCHANGED.

THE FRONT-END FAMILY (the untested levers the directive names; the agent picks among):
  Each candidate is a gammatone filterbank read out as a frames x bands trajectory.
  They vary the TWO untested levers — never the (ruled-out) frequency BASIS:
    · RESOLUTION   n_bands ∈ {32 (baseline), 48, 64}: the rank decoder has only as
                   many ordinal ranks as bands; more bands = a finer ordinal profile,
                   BUT finer freq may be less VTL-stable (shift-coherence will tell).
    · TIME-FREQ    the seed ear LOW-PASSES each band's envelope (one-pole at env_cut
                   then an 80 ms duration LPF) — an energy-envelope SMEAR that throws
                   away the fine time-frequency detail.  Candidates sharpen the
                   temporal envelope (dur_ms ∈ {80 (baseline), 40, 20}) and lift the
                   frame count (n_frames ∈ {32, 48}) so finer temporal dynamics
                   survive into the rank trajectory.

DO-CONTRAST (the wall regime, cross-speaker, native DtwTo, shuffle backstop):
  ARM OLD : gammatone32 — the baseline ~32-band energy envelope (env_cut 50, dur 80,
            32 frames, 32 log bands) — EXACTLY scripts.invariant_units_accept's
            band_trajectory_matrix.
  ARM NEW : the agent-CHOSEN front end (from its selector).
  Both feed the SAME relational decoder; report REL-BAND-on-NEW vs REL-BAND-on-OLD
  per V ∈ {10, 20}, cross-speaker, with the per-clip floor and the shuffle backstop.

READ THE NUMBERS, not a boolean.  HONEST outcomes all valid: (a) NEW breaks the wall
(front-end resolution/sharpness was the bottleneck); (b) ties (the rank already
captures what the front end has — the wall is the representation); (c) hurts (finer
resolution less VTL-stable).  Do NOT manufacture or sweep a gain — the agent's
selector picks ONE front end; we contrast exactly that one against the baseline.

Run: python -m scripts.frontend_improve_xspeaker [n_train] [n_test] [n_anchors]
"""
from __future__ import annotations

import math
import os
import sys
import random
import time
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.recognition_graph as RG
from domains.relational_shape import relational_shape
from domains import audio_basis_select as SEL

SC = "/tmp/sc"
WORD_POOL = 20            # build the cross-speaker pool once over the V=20 vocabulary;
                          # V=10 is the first 10 words of the same pool (nested).


# ---------------------------------------------------------------------------
# THE FRONT-END FAMILY — parameterised gammatone -> frames x bands.  Pure
# I/O-boundary DSP, identical in kind to scripts.mine_whisper.gammatone_env +
# scripts.invariant_units_accept.band_trajectory_matrix.  The ONLY thing that
# varies between candidates is (n_bands, dur_ms, n_frames) — the two untested
# front-end levers (frequency RESOLUTION and TIME-FREQ sharpness).
# ---------------------------------------------------------------------------

_LOG_LO, _LOG_HI = math.log(80.0), math.log(7500.0)


def _bands(n_bands):
    return [math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / (n_bands - 1.0))
            for i in range(n_bands)]


def _gammatone_env(x, fs, fc, env_cut=50.0):
    """One gammatone channel's hair-cell envelope — EXACTLY mine_whisper.gammatone_env
    (order-4 FIR, energy-normalised, half-wave rectify, one-pole LPF at env_cut)."""
    dur = 0.025
    L = int(dur * fs)
    t = np.arange(L) / fs
    b = 2.0 * math.pi * 1.019 * (24.7 + 0.108 * fc)
    g = t ** 3 * np.exp(-b * t) * np.cos(2 * math.pi * fc * t)
    e = np.sqrt(np.sum(g * g))
    if e > 0:
        g = g / e
    y = np.convolve(x, g, mode="same")
    y = np.maximum(y, 0.0)
    tau = 1.0 / (2 * math.pi * env_cut)
    a = math.exp(-1.0 / (tau * fs))
    out = np.empty_like(y)
    acc = 0.0
    for i in range(len(y)):
        acc = a * acc + (1 - a) * y[i]
        out[i] = acc
    return out


def band_matrix(x, fs, n_bands=32, dur_ms=80.0, n_frames=32, env_cut=50.0):
    """frames x bands gammatone trajectory.  At (32, 80, 32, 50) this REPRODUCES
    scripts.invariant_units_accept.band_trajectory_matrix bit-for-bit (the OLD front
    end / baseline).  n_bands = frequency RESOLUTION; dur_ms = the duration LPF cutoff
    that sets the TIME-FREQ sharpness (smaller = sharper, less envelope smear);
    n_frames = temporal sampling.  The two untested levers; basis stays log (ruled-out
    lever held fixed)."""
    centres = _bands(n_bands)
    envs = [_gammatone_env(x, fs, fc, env_cut) for fc in centres]
    cut = 1000.0 / (2 * math.pi * float(dur_ms))      # duration LPF cutoff (Hz)
    tau = 1.0 / (2 * math.pi * cut)
    a = math.exp(-1.0 / (tau * fs))
    smoothed = []
    for env in envs:
        sm = np.empty_like(env)
        acc = 0.0
        for i in range(len(env)):
            acc = a * acc + (1 - a) * env[i]
            sm[i] = acc
        smoothed.append(sm)
    n_src = len(smoothed[0])
    rows = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp)
        i1 = min(i0 + 1, n_src - 1)
        frac = sp - i0
        rows.append([buf[i0] * (1 - frac) + buf[i1] * frac for buf in smoothed])
    return np.array(rows, dtype=np.float32)


# The candidate family the agent's selector ranges over.  (name, params).  The
# baseline gammatone32 is included so the selector's ranking is self-anchored.
CANDIDATES = [
    ("gammatone32",        dict(n_bands=32, dur_ms=80.0, n_frames=32)),  # OLD / baseline
    ("res48",              dict(n_bands=48, dur_ms=80.0, n_frames=32)),  # finer freq
    ("res64",              dict(n_bands=64, dur_ms=80.0, n_frames=32)),  # finest freq
    ("sharp_time40",       dict(n_bands=32, dur_ms=40.0, n_frames=48)),  # sharper time
    ("sharp_time20",       dict(n_bands=32, dur_ms=20.0, n_frames=48)),  # sharpest time
    ("res48_sharp40",      dict(n_bands=48, dur_ms=40.0, n_frames=48)),  # both levers
    ("res64_sharp20",      dict(n_bands=64, dur_ms=20.0, n_frames=48)),  # both, max
]
BASELINE = "gammatone32"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:
        try:
            from scipy.signal import decimate
            raw = decimate(raw, 2)
        except Exception:
            raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32)), 8000


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


# ---------------------------------------------------------------------------
# Native nearest-exemplar over the relational shape (CONFIRMED decoder, UNCHANGED).
# Identical machinery to scripts.relational_shape_xspeaker.
# ---------------------------------------------------------------------------
def run_arm(sub, sign, err, tag, tr_reprs, te_reprs, chance, shuffle=False):
    ex_words = [w for _, w in tr_reprs]
    if shuffle:
        ex_words = list(ex_words)
        random.Random(7).shuffle(ex_words)
    exs = []
    for (M, _), w in zip(tr_reprs, ex_words):
        if M is None or len(M) < 2:
            continue
        c = sub.add_node("Exemplar", {"word": w})
        sub.set_attr(c, "rep", as_tuple(M))
        exs.append((c, w))
    corr = tot = 0
    per_word = defaultdict(lambda: [0, 0])
    for M, w in te_reprs:
        if M is None or len(M) < 2:
            continue
        sub.set_attr(sign, "rep", as_tuple(M))
        best_d, best_w = 1e18, None
        for c, ew in exs:
            d = sub.evaluate(err, {"s": sign, "w": c})
            if d < best_d:
                best_d, best_w = d, ew
        ok = int(best_w == w)
        corr += ok
        tot += 1
        per_word[w][0] += ok
        per_word[w][1] += 1
    for c, _ in exs:
        sub.remove_node(c)
    acc = corr / max(tot, 1)
    se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
    print(f"  [{tag}]  {corr}/{tot} = {100*acc:.2f}%  "
          f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
    return {"acc": acc, "corr": corr, "tot": tot, "se": se}


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n_anchors = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    random.seed(1)
    np.random.seed(1)
    t0 = time.time()

    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:WORD_POOL]
    print("=" * 72, flush=True)
    print("FRONT-END IMPROVEMENT — agent picks the front end; relational decoder FIXED",
          flush=True)
    print("=" * 72, flush=True)
    print(f"word pool ({len(words)}): {words}", flush=True)

    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))

    # Hold out whole SPEAKERS (train/test disjoint), over the FULL V=20 pool.
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train = [(p, w) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]
    print(f"train exemplars {len(train)} (disjoint speakers); "
          f"test {len(test)} from HELD-OUT speakers", flush=True)

    # Load every clip's waveform ONCE (extract each front end from these).
    print(f"\nloading waveforms ({time.time()-t0:.0f}s)...", flush=True)
    tr_wav = []
    for p, w in train:
        try:
            x, fs = load_real(p)
            tr_wav.append((x, fs, w))
        except Exception:
            pass
    te_wav = []
    for p, w in test:
        try:
            x, fs = load_real(p)
            te_wav.append((x, fs, w))
        except Exception:
            pass
    print(f"  {len(tr_wav)} train / {len(te_wav)} test waveforms "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ======================================================================
    # STEP 1 — THE AGENT CHOOSES THE FRONT END (its own label-free selector).
    #   For each candidate front end, extract the TRAIN-pool band matrices grouped
    #   by word (cross-speaker within each word) and run the agent's selector:
    #     shift-coherence (VTL=shift residual ratio, LOWER=more speaker-stable) +
    #     effective dimensionality (MDL, corroborating).  NO accuracy, NO labels as
    #     a classifier (word only groups same-word cross-speaker pairs).  The agent
    #     PICKS the candidate with the best shift-coherence — the most VTL-stable
    #     front end, which by construction is the resolution/sharpness that is BOTH
    #     discriminative AND speaker-invariant (the directive's tension, resolved by
    #     the selector, not by us).
    # ======================================================================
    print("\n" + "=" * 72, flush=True)
    print("STEP 1 — AGENT CHOOSES THE FRONT END (audio_basis_select: shift-coherence",
          flush=True)
    print("          + effective-dim, label-free; NO accuracy). Front-end family:",
          flush=True)
    print("=" * 72, flush=True)

    # use a manageable subset of the train pool for the selector (cross-speaker pairs)
    sel_wav = tr_wav[:min(len(tr_wav), 240)]
    per_cand = {}
    for name, params in CANDIDATES:
        mats_by_word = defaultdict(list)
        for x, fs, w in sel_wav:
            M = band_matrix(x, fs, **params)
            if M is not None and M.shape[0] >= 2:
                mats_by_word[w].append(M)
        shift_ratio, shift_n = SEL.shift_coherence(mats_by_word)
        all_mats = [M for ms in mats_by_word.values() for M in ms]
        eff_dim, dl_bits, comp_n = SEL.compression(all_mats)
        per_cand[name] = {"shift_ratio": shift_ratio, "shift_n": shift_n,
                          "eff_dim": eff_dim, "dl_bits": dl_bits,
                          "comp_n": comp_n, "params": params}
        print(f"  {name:16s} bands={params['n_bands']:2d} dur={params['dur_ms']:4.0f}ms "
              f"frames={params['n_frames']:2d}  shift-coh={shift_ratio:.4f} "
              f"(n={shift_n})  eff-dim={eff_dim:5.2f}  DL={dl_bits:6.1f} b/band",
              flush=True)

    chosen, ranked = SEL.select(per_cand)
    print(f"\n  >>> AGENT'S CHOICE (lowest shift-coherence residual = most VTL-stable):"
          f" '{chosen}'", flush=True)
    print(f"  ranked by shift-coherence (ascending = more speaker-coherent):",
          flush=True)
    for nm, sr, ed, dl in ranked:
        mark = "  <- CHOSEN" if nm == chosen else ""
        print(f"     {nm:16s} shift={sr:.4f}  eff-dim={ed:5.2f}  DL={dl:6.1f}{mark}",
              flush=True)
    if chosen == BASELINE:
        # the selector preferred the baseline; contrast it against its best non-baseline
        # rival so we still report a NEW front end (honest: the agent ranked baseline #1).
        alt = next((nm for nm, *_ in ranked if nm != BASELINE), BASELINE)
        print(f"\n  NOTE: the agent's selector RANKED THE BASELINE FIRST — its own "
              f"label-free criterion prefers the existing front end. We still run the "
              f"do-contrast vs the best non-baseline rival ('{alt}') so the NEW arm is "
              f"a genuine front-end change, but the headline is: the selector did NOT "
              f"ask for a finer front end.", flush=True)
        new_name = alt
    else:
        new_name = chosen
    new_params = dict(next(p for n, p in CANDIDATES if n == new_name))
    old_params = dict(next(p for n, p in CANDIDATES if n == BASELINE))

    # ======================================================================
    # STEP 2 — DO-CONTRAST: REL-BAND-on-NEW vs REL-BAND-on-OLD, same relational
    #   decoder, cross-speaker, at the wall regime V ∈ {10, 20}, shuffle backstop.
    # ======================================================================
    def reprs_for(params, vocab):
        vset = set(vocab)
        tr = []
        for x, fs, w in tr_wav:
            if w not in vset:
                continue
            M = band_matrix(x, fs, **params)
            if M is not None and M.shape[0] >= 2:
                tr.append((relational_shape(M, n_anchors=n_anchors), w))
        te = []
        for x, fs, w in te_wav:
            if w not in vset:
                continue
            M = band_matrix(x, fs, **params)
            if M is not None and M.shape[0] >= 2:
                te.append((relational_shape(M, n_anchors=n_anchors), w))
        return tr, te

    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    results = {}
    for V in (10, 20):
        vocab = words[:V]
        chance = 1.0 / V
        print("\n" + "=" * 72, flush=True)
        print(f"DO-CONTRAST at V={V}  (vocab: {vocab})  chance {100*chance:.1f}%",
              flush=True)
        print("=" * 72, flush=True)

        print(f"\n composing OLD ({BASELINE}) relational shapes "
              f"({time.time()-t0:.0f}s)...", flush=True)
        tr_old, te_old = reprs_for(old_params, vocab)
        print(f"  OLD: {len(tr_old)} train / {len(te_old)} test", flush=True)
        print(f" composing NEW ({new_name}) relational shapes "
              f"({time.time()-t0:.0f}s)...", flush=True)
        tr_new, te_new = reprs_for(new_params, vocab)
        print(f"  NEW: {len(tr_new)} train / {len(te_new)} test", flush=True)
        if te_old:
            print(f"  per-clip resolution OLD: {100.0/len(te_old):.3f}%", flush=True)

        print(f"\n ARM OLD — REL-BAND on {BASELINE} (baseline ~32-band energy envelope)",
              flush=True)
        OLD = run_arm(sub, sign, err, f"OLD/{BASELINE}", tr_old, te_old, chance)
        print(f"\n ARM NEW — REL-BAND on {new_name} (agent-chosen front end)", flush=True)
        NEW = run_arm(sub, sign, err, f"NEW/{new_name}", tr_new, te_new, chance)
        print(f"\n SHUFFLE backstop on NEW (labels permuted -> must collapse)",
              flush=True)
        SH = run_arm(sub, sign, err, f"NEW-SHUFFLE", tr_new, te_new, chance,
                     shuffle=True)
        results[V] = {"OLD": OLD, "NEW": NEW, "SH": SH, "chance": chance}

    # ======================================================================
    # VERDICT — read the numbers per V.
    # ======================================================================
    print("\n" + "=" * 72, flush=True)
    print("VERDICT — REL-BAND on the agent-chosen NEW front end vs the OLD baseline",
          flush=True)
    print("=" * 72, flush=True)
    print(f"  agent chose:  {new_name}  {new_params}", flush=True)
    print(f"  baseline OLD: {BASELINE}  {old_params}", flush=True)
    for V in (10, 20):
        r = results[V]
        OLD, NEW, SH = r["OLD"], r["NEW"], r["SH"]
        margin_clips = NEW["corr"] - OLD["corr"]
        margin_pct = 100 * (NEW["acc"] - OLD["acc"])
        pooled_se = 100 * ((OLD["se"] ** 2 + NEW["se"] ** 2) ** 0.5)
        sh_margin = NEW["corr"] - SH["corr"]
        print(f"\n  V={V} (chance {100*r['chance']:.1f}%):", flush=True)
        print(f"    OLD  {OLD['corr']}/{OLD['tot']} = {100*OLD['acc']:.2f}%  "
              f"(SE {100*OLD['se']:.2f}%)", flush=True)
        print(f"    NEW  {NEW['corr']}/{NEW['tot']} = {100*NEW['acc']:.2f}%  "
              f"(SE {100*NEW['se']:.2f}%)", flush=True)
        print(f"    SHUF {SH['corr']}/{SH['tot']} = {100*SH['acc']:.2f}%", flush=True)
        print(f"    NEW - OLD = {margin_clips:+d} clips ({margin_pct:+.2f}%)  "
              f"pooled SE {pooled_se:.2f}%", flush=True)
        print(f"    NEW - SHUF= {sh_margin:+d} clips", flush=True)
        if margin_clips > 3 and margin_pct > pooled_se and sh_margin > 3:
            print(f"    >>> V={V}: NEW front end LIFTS REL-BAND above the wall by a "
                  f"margin above noise AND above shuffle.", flush=True)
        elif margin_clips < -3 and abs(margin_pct) > pooled_se:
            print(f"    >>> V={V}: NEW front end HURTS (finer resolution less "
                  f"VTL-stable). Honest result.", flush=True)
        else:
            print(f"    >>> V={V}: TIE within noise — the rank decoder already "
                  f"captures what the finer front end carries; the wall is the "
                  f"representation, not the front-end input.", flush=True)
    print(f"\n  (total {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
