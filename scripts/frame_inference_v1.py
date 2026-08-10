"""frame_inference_v1 — the DERIVED CURE for the cross-speaker wall, measured.

THE DIAGNOSIS (Ladefoged-Broadbent, commit eb276156). The model perceives a fixed
test token ABSOLUTELY — its own formants, blind to the talker's formant RANGE
(carrier effect ~ -0.6%). Humans perceive RELATIVE to a "sliding template": they
INFER the talker's formant frame from context, then read the target relative to it.
Every ABSOLUTE / removal approach this session (CMVN, per-speaker VTLN, per-utterance
predict-remove) capped cross-speaker LOSO at ~0.50.

THE CURE (Axiom 0: the word holds nothing absolute; it is frame-relative). INFER the
talker's FRAME from CONTEXT (a few of their OTHER, UNLABELED utterances — extrinsic
normalization), then read the TEST clip's formants RELATIVE to that inferred frame
(the test's position WITHIN the talker's formant range). Cross-speaker invariance
FALLS OUT: the same relative position regardless of the absolute talker.

DESIGN (donkey-clean):
  · FRAME ESTIMATE (context -> talker frame): for each held-out speaker, pool LPC
    formants (F1,F2,F3) over a few of their UNLABELED context clips (DISJOINT from the
    test clip, NO labels, NO speaker-id used as a feature). The frame is the talker's
    formant DISTRIBUTION — percentile range / min-max / vowel-space corners.
  · RELATIVE READING (sliding template): re-express the TEST clip's per-frame formants
    as their RELATIVE position within the inferred talker frame (z-score within the
    talker's formant distribution, or fraction-of-range). Owned normalization (a
    subtract+divide, the same move as vtl_terms / cmvn), NO net, NO fit, NO gradient.
  · RECOGNISE: 1-NN over the frame-relative formant trajectories (the agent's
    nearest-exemplar Argmin cognition, the SAME recognizer mechanic the world uses).

TEST (robust SC 40-speaker LOSO, ungameable). For each held-out speaker: infer their
frame from their UNLABELED context clips (held-out, disjoint from the test), read the
test relative, recognise. Compare:
  (ABS)  absolute formant trajectory  (no context, no normalization) — the baseline.
  (CMVN) absolute formant trajectory, per-utterance CMVN over the formants (the
         ~0.50 removal-class bar, but in formant space for an apples-to-apples diff).
  (REL)  FRAME-RELATIVE: test read relative to the context-inferred talker frame.
Sweep the frame estimator (percentile-range vs min-max vs vowel-space corners) and
the number of context clips. Report SEEN + LOSO + gap + n.

NO-DONKEY / NO-LEAKAGE: frame estimate + relative reading = owned ops (formants via
LPC roots, range, z-score/fraction normalization). Context = the speaker's UNLABELED
clips, DISJOINT from the test clip (a per-speaker held-out split: context clips and
test clips never overlap), NO speaker labels used as a feature. Recognition = 1-NN
Argmin (the agent's). Held-out speakers' TEST clips are NEVER banked. LOSO ungameable.

Run: python -m scripts.frame_inference_v1 [n_train_spk] [n_held_spk] [n_per] [n_ctx]
"""
from __future__ import annotations

import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
from domains.lpc_formant_representation import _lpc_roots_formants

FS = W._TARGET_FS


# ---------------------------------------------------------------------------
# OWNED OP 1 — the per-frame formant trajectory (F1,F2,F3) of a clip.
# LPC roots (the agent's spec, lpc_formant_representation._lpc_roots_formants),
# the SAME adapter-math front end the session uses. Pure boundary DSP.
# ---------------------------------------------------------------------------

def formant_trajectory(x, fs=FS, fps=25, n_formants=3):
    """Per-frame F1..Fn (Hz) of one clip via LPC roots. Frames with fewer than
    n_formants resonances are dropped (an honest voiced-frame gate). Returns an
    (n_frames x n_formants) array (may be empty for an unvoiced/silent clip)."""
    x = np.asarray(x, dtype=np.float64)
    order = int(fs / 1000) + 2                      # agent's spec rule (~10 at 8 kHz)
    n_frames = max(8, min(300, int(len(x) / fs * fps)))
    win = max(int(0.025 * fs), order + 4)
    rows = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * len(x) / n_frames)
        a0 = max(0, c - win // 2)
        fmts = _lpc_roots_formants(x[a0:min(len(x), a0 + win)], fs, order)
        if len(fmts) >= n_formants:
            rows.append(fmts[:n_formants])
    if not rows:
        return np.zeros((0, n_formants), dtype=np.float64)
    return np.asarray(rows, dtype=np.float64)


# log-Hz: VTL scales formants multiplicatively -> a SHIFT in log-Hz, the axis the
# talker frame is a translation/scaling on. All frame ops run in log-Hz.
def _logf(traj):
    return np.log(np.clip(traj, 1e-6, None))


# ---------------------------------------------------------------------------
# OWNED OP 2 — INFER THE TALKER FRAME from CONTEXT (unlabeled clips).
# The frame is the talker's formant DISTRIBUTION (in log-Hz). Three estimators:
#   "pctl"   — per-formant low/high percentiles (a robust range).
#   "minmax" — per-formant min/max (the raw extent).
#   "vowel"  — vowel-space corners: per-formant 5th/95th percentile of the pooled
#              F1/F2 cloud (the extent of the talker's vowel triangle).
# Plus the per-formant mean + std (for the z-score relative reading). Owned ops:
# pooling, percentile, mean, std — the same aggregation class as CMVN's Sum/Count.
# ---------------------------------------------------------------------------

def infer_talker_frame(context_clips, fs=FS, estimator="pctl", lo=10.0, hi=90.0,
                       n_formants=3):
    """context_clips: list of raw waveforms (the speaker's UNLABELED utterances,
    DISJOINT from the test). Returns the talker frame: per-formant (low, high, mean,
    std) in log-Hz, pooled over all context frames. None if no voiced context."""
    pool = []
    for x in context_clips:
        tr = formant_trajectory(x, fs, n_formants=n_formants)
        if tr.shape[0]:
            pool.append(_logf(tr))
    if not pool:
        return None
    P = np.concatenate(pool, axis=0)                # (total_frames x n_formants)
    frame = []
    for k in range(n_formants):
        col = P[:, k]
        if estimator == "minmax":
            lo_v, hi_v = float(col.min()), float(col.max())
        elif estimator == "vowel":
            lo_v, hi_v = float(np.percentile(col, 5.0)), float(np.percentile(col, 95.0))
        else:  # "pctl"
            lo_v, hi_v = float(np.percentile(col, lo)), float(np.percentile(col, hi))
        frame.append((lo_v, hi_v, float(col.mean()), float(col.std() + 1e-6)))
    return frame


# ---------------------------------------------------------------------------
# OWNED OP 3 — READ RELATIVE (the sliding template). Re-express the test clip's
# formant trajectory RELATIVE to the inferred talker frame:
#   "frac"   — fraction of the talker's range:  (f - lo) / (hi - lo).
#   "z"      — z-score within the talker distribution:  (f - mean) / std.
# Both are owned subtract+divide (the cmvn/vtl move). If no frame (no context), the
# reading degrades to the absolute log-formant (so REL >= ABS information).
# ---------------------------------------------------------------------------

def read_relative(test_clip, frame, fs=FS, mode="frac", n_formants=3):
    """Test clip's formant trajectory expressed relative to the talker frame.
    Returns an (n_frames x n_formants) array of relative positions."""
    tr = formant_trajectory(test_clip, fs, n_formants=n_formants)
    if tr.shape[0] == 0:
        return np.zeros((0, n_formants), dtype=np.float64)
    L = _logf(tr)
    if frame is None:
        return L                                    # no context -> absolute log-f
    out = np.empty_like(L)
    for k in range(n_formants):
        lo_v, hi_v, mu, sd = frame[k]
        if mode == "z":
            out[:, k] = (L[:, k] - mu) / sd
        else:  # "frac"
            rng = hi_v - lo_v
            out[:, k] = (L[:, k] - lo_v) / rng if rng > 1e-6 else (L[:, k] - mu)
    return out


def absolute_logf(clip, fs=FS, n_formants=3):
    """The ABSOLUTE baseline representation: the raw log-formant trajectory (no
    context, no normalization). The model's current absolute perception."""
    tr = formant_trajectory(clip, fs, n_formants=n_formants)
    return _logf(tr) if tr.shape[0] else np.zeros((0, n_formants), dtype=np.float64)


def cmvn_logf(clip, fs=FS, n_formants=3):
    """The CMVN removal-class baseline IN FORMANT SPACE: per-utterance mean+var
    normalize the absolute log-formant trajectory. This is the ~0.50 absolute-removal
    bar, computed on the same formant features as REL for an apples-to-apples diff
    (the agent's cmvn move: subtract per-utterance mean, divide by std)."""
    L = absolute_logf(clip, fs, n_formants)
    if L.shape[0] == 0:
        return L
    mu = L.mean(axis=0, keepdims=True)
    sd = L.std(axis=0, keepdims=True) + 1e-6
    return (L - mu) / sd


# ---------------------------------------------------------------------------
# RECOGNISE — 1-NN Argmin over formant trajectories (the agent's nearest-exemplar
# cognition). DTW distance between two (frames x dim) trajectories (Euclidean per
# frame), the SAME alignment the agent's DtwTo computes. Mechanical readout.
# ---------------------------------------------------------------------------

def _dtw(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size == 0 or b.size == 0:
        return float("inf")
    na, nb = a.shape[0], b.shape[0]
    D = np.full((na + 1, nb + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, na + 1):
        ai = a[i - 1]
        row = D[i]
        prev = D[i - 1]
        for j in range(1, nb + 1):
            c = float(np.linalg.norm(ai - b[j - 1]))
            row[j] = c + min(prev[j], row[j - 1], prev[j - 1])
    return float(D[na, nb] / (na + nb))


def recognise(test_repr, bank):
    """1-NN Argmin: the banked (word, repr) nearest the test repr wins. bank is a
    list of (word, repr_array). Returns the predicted word (or None)."""
    if test_repr.shape[0] == 0 or not bank:
        return None
    best_w, best_d = None, float("inf")
    for w, r in bank:
        if r.shape[0] == 0:
            continue
        d = _dtw(test_repr, r)
        if d < best_d:
            best_d, best_w = d, w
    return best_w


# ---------------------------------------------------------------------------
# THE LOSO HARNESS — robust SC cross-speaker, with a per-held-speaker context split.
# ---------------------------------------------------------------------------

def build_split(n_train_spk, n_held_spk, n_per, n_ctx, seed=20240611):
    """Robust SC LOSO with a per-speaker CONTEXT split, on BOTH sides.

    THE CORE FIX (why an earlier draft KILLed): the sliding template only works if
    the bank exemplars AND the test live in the SAME frame-relative space. An
    absolute bank vs a [0,1]-fraction test compares apples to oranges (the DTW is
    meaningless). So BOTH sides are read relative to THEIR OWN talker frame:
      · TRAIN speakers: per speaker, infer their frame from n_ctx of their UNLABELED
        clips (disjoint from the banked clips), then store their banked exemplars
        frame-relative. The bank is now talker-normalized exemplars.
      · HELD speakers: per speaker, infer their frame from n_ctx UNLABELED clips
        (disjoint from the test), read the test relative. Same space as the bank.
    No clip is ever both context and bank/test for the same speaker; no labels used.

    Returns (train_by_speaker, seen_by_speaker, held_by_speaker), each
    {spk: (ctx_clips, [(word, x, fs), ...])}."""
    words = W.sc_words()
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    print(f"[split] {len(words)} words {words}", flush=True)
    print(f"[split] {len(train_spk)} TRAIN speakers, {len(held_spk)} HELD-OUT "
          f"speakers (disjoint; held TEST clips NEVER banked)", flush=True)

    def carve(spk_list, n_bank_or_test, seen_extra=0):
        """For each speaker: n_ctx UNLABELED context clips (frame only) + a DISJOINT
        slice of (word, clip) for the bank/test + an optional further-disjoint seen
        slice. Pure probe-construction I/O."""
        out, seen = {}, {}
        for spk in spk_list:
            spk_idx = W.sc_index_for([spk], words)
            wp = [(w, p) for w in words for p in spk_idx.get(w, [])]
            rng.shuffle(wp)
            if len(wp) < n_ctx + 2:
                continue
            ctx = wp[:n_ctx]
            body = wp[n_ctx:n_ctx + n_bank_or_test]
            ctx_clips = [W.load_sc_clip(p)[0] for _w, p in ctx]
            body_clips = [(w,) + W.load_sc_clip(p) for w, p in body]
            if body_clips:
                out[spk] = (ctx_clips, body_clips)
            if seen_extra:
                sx = wp[n_ctx + n_bank_or_test:n_ctx + n_bank_or_test + seen_extra]
                sc = [(w,) + W.load_sc_clip(p) for w, p in sx]
                if sc:
                    seen[spk] = (ctx_clips, sc)
        return out, seen

    # train: n_per bank clips/speaker + up to 4 seen-probe clips/speaker (all disjoint).
    train_by_speaker, seen_by_speaker = carve(train_spk, n_per, seen_extra=4)
    held_by_speaker, _ = carve(held_spk, 8)

    n_bank = sum(len(b) for _c, b in train_by_speaker.values())
    n_seen = sum(len(b) for _c, b in seen_by_speaker.values())
    n_test = sum(len(b) for _c, b in held_by_speaker.values())
    print(f"[split] {len(train_by_speaker)} train speakers ({n_bank} bank clips, "
          f"{n_seen} seen probes), {len(held_by_speaker)} held speakers ({n_test} "
          f"cross-speaker test clips); {n_ctx} UNLABELED context clips/speaker, "
          f"disjoint from bank/test", flush=True)
    return train_by_speaker, seen_by_speaker, held_by_speaker


def build_abs_bank(by_speaker, repr_fn):
    """ABS / CMVN bank: per-utterance representation, talker frame ignored. Flattens
    all train speakers into one exemplar list."""
    bank = []
    for spk, (_ctx, clips) in by_speaker.items():
        for w, x, _fs in clips:
            r = repr_fn(x)
            if r.shape[0]:
                bank.append((w, r))
    return bank


def build_rel_bank(by_speaker, estimator, mode, frame_cache):
    """REL bank: each train speaker's exemplars read RELATIVE to THAT speaker's
    inferred frame (from their own UNLABELED context clips). The bank is now in the
    SAME frame-relative space as a relative-read test clip -> the DTW is meaningful
    (the sliding-template, applied to BOTH the lexicon and the incoming token)."""
    bank = []
    for spk, (ctx, clips) in by_speaker.items():
        fr = frame_cache.get((spk, estimator))
        if fr is None:
            fr = infer_talker_frame(ctx, estimator=estimator)
            frame_cache[(spk, estimator)] = fr
        for w, x, _fs in clips:
            r = read_relative(x, fr, mode=mode)
            if r.shape[0]:
                bank.append((w, r))
    return bank


def measure_seen_abs(seen_by_speaker, bank, repr_fn):
    tot = cor = 0
    for spk, (_ctx, clips) in seen_by_speaker.items():
        for w, x, _fs in clips:
            g = recognise(repr_fn(x), bank)
            tot += 1
            cor += int(g == w)
    return cor, tot


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    n_ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 8

    train_by_speaker, seen_by_speaker, held = build_split(
        n_train_spk, n_held_spk, n_per, n_ctx)
    chance = 1.0 / len(W.sc_words())

    REL_VARIANTS = [("pctl", "frac"), ("pctl", "z"),
                    ("minmax", "frac"), ("vowel", "frac")]
    frame_cache = {}                                 # (speaker, estimator) -> frame

    # --- ABSOLUTE + CMVN banks (per-utterance; talker frame ignored) ---
    print("\n[bank] extracting train-clip formant trajectories ...", flush=True)
    abs_bank = build_abs_bank(train_by_speaker, absolute_logf)
    cmvn_bank = build_abs_bank(train_by_speaker, cmvn_logf)
    # --- FRAME-RELATIVE banks (one per REL variant): train exemplars read relative
    #     to THEIR OWN speaker's inferred frame -> same space as a relative-read test.
    rel_banks = {ev: build_rel_bank(train_by_speaker, ev[0], ev[1], frame_cache)
                 for ev in REL_VARIANTS}
    print(f"[bank] {len(abs_bank)} abs / {len(cmvn_bank)} cmvn exemplars; "
          + " ".join(f"{ev[0]}/{ev[1]}={len(rel_banks[ev])}" for ev in REL_VARIANTS),
          flush=True)

    # --- DONKEY AUDIT: show inferred frames are real talker ranges (not leakage) ---
    print("\n[donkey audit] inferred talker frames (log-Hz F1/F2/F3 range), first 3 "
          "held speakers — context-only, disjoint from test:", flush=True)
    for spk in list(held)[:3]:
        ctx_clips, _t = held[spk]
        fr = infer_talker_frame(ctx_clips, estimator="pctl")
        if fr:
            rng = " ".join(f"F{k+1}[{np.exp(fr[k][0]):.0f}-{np.exp(fr[k][1]):.0f}Hz]"
                           for k in range(len(fr)))
            print(f"   spk {spk[:8]}: {rng}  (from {len(ctx_clips)} ctx clips)",
                  flush=True)

    # === SEEN-speaker baselines (same-speaker; the ceiling) ===
    # The seen probe is also read relative to the speaker's frame for REL (apples to
    # apples with the rel bank), absolute for ABS/CMVN.
    print("\n[seen] same-speaker probe (ceiling) ...", flush=True)
    sc_abs = measure_seen_abs(seen_by_speaker, abs_bank, absolute_logf)
    sc_cmvn = measure_seen_abs(seen_by_speaker, cmvn_bank, cmvn_logf)
    seen_rel = {ev: [0, 0] for ev in REL_VARIANTS}
    for spk, (ctx, clips) in seen_by_speaker.items():
        for ev in REL_VARIANTS:
            fr = frame_cache.get((spk, ev[0]))
            if fr is None:
                fr = infer_talker_frame(ctx, estimator=ev[0])
                frame_cache[(spk, ev[0])] = fr
            for w, x, _fs in clips:
                g = recognise(read_relative(x, fr, mode=ev[1]), rel_banks[ev])
                seen_rel[ev][0] += int(g == w)
                seen_rel[ev][1] += 1
    print(f"   ABS  seen {sc_abs[0]/max(sc_abs[1],1):.3f} (n={sc_abs[1]})", flush=True)
    print(f"   CMVN seen {sc_cmvn[0]/max(sc_cmvn[1],1):.3f} (n={sc_cmvn[1]})", flush=True)
    for ev in REL_VARIANTS:
        c, t = seen_rel[ev]
        print(f"   REL {ev[0]}/{ev[1]} seen {c/max(t,1):.3f} (n={t})", flush=True)

    # === CROSS-SPEAKER LOSO ===
    # ABS/CMVN: per-utterance, no context. REL: test read relative to the held
    # speaker's context-inferred frame, against the same-space rel bank. SAME test clips.
    print("\n[LOSO] cross-speaker — ABS vs CMVN vs FRAME-RELATIVE (swept) ...",
          flush=True)

    abs_cor = abs_tot = 0
    cmvn_cor = cmvn_tot = 0
    rel_sweep = {ev: [0, 0] for ev in REL_VARIANTS}

    n_spk = 0
    for spk, (ctx_clips, test_clips) in held.items():
        n_spk += 1
        for est in {e for e, _m in REL_VARIANTS}:
            frame_cache[(spk, est)] = infer_talker_frame(ctx_clips, estimator=est)
        for w, x, _fs in test_clips:
            # ABS
            g = recognise(absolute_logf(x), abs_bank)
            abs_tot += 1
            abs_cor += int(g == w)
            # CMVN
            g = recognise(cmvn_logf(x), cmvn_bank)
            cmvn_tot += 1
            cmvn_cor += int(g == w)
            # REL — test read relative to the held speaker's frame, same-space bank.
            for (est, mode) in REL_VARIANTS:
                fr = frame_cache[(spk, est)]
                g = recognise(read_relative(x, fr, mode=mode), rel_banks[(est, mode)])
                rel_sweep[(est, mode)][0] += int(g == w)
                rel_sweep[(est, mode)][1] += 1
        if n_spk % 10 == 0:
            print(f"   ... {n_spk}/{len(held)} held speakers done", flush=True)

    def rate(c, t):
        return c / max(t, 1)

    abs_loso = rate(abs_cor, abs_tot)
    cmvn_loso = rate(cmvn_cor, cmvn_tot)

    print("\n" + "=" * 70, flush=True)
    print("FRAME-INFERENCE v1 — cross-speaker LOSO (SC, ungameable held-out)", flush=True)
    print("=" * 70, flush=True)
    print(f"  chance {chance:.3f}   held speakers {n_spk}   test clips n={abs_tot}",
          flush=True)
    print(f"  context clips/speaker {n_ctx} (UNLABELED, disjoint from test)", flush=True)
    print("-" * 70, flush=True)
    print(f"  {'regime':24s} {'LOSO':>8s} {'vs CMVN':>10s}", flush=True)
    print(f"  {'ABS (absolute log-f)':24s} {abs_loso:8.3f} {abs_loso-cmvn_loso:+10.3f}",
          flush=True)
    print(f"  {'CMVN (removal bar)':24s} {cmvn_loso:8.3f} {0.0:+10.3f}", flush=True)
    best_rel = None
    for (est, mode), (c, t) in rel_sweep.items():
        r = rate(c, t)
        tag = f"REL {est}/{mode}"
        print(f"  {tag:24s} {r:8.3f} {r-cmvn_loso:+10.3f}", flush=True)
        if best_rel is None or r > best_rel[1]:
            best_rel = ((est, mode), r)
    print("-" * 70, flush=True)
    (best_em, best_r) = best_rel
    # THE HONEST BASELINE is the BEST non-context regime — both ABS and CMVN are
    # zero-context removal/absolute approaches. The derived cure only PAYS if context
    # + relative perception beats the best of them (not just the weaker one).
    baseline = max(abs_loso, cmvn_loso)
    base_name = "ABS" if abs_loso >= cmvn_loso else "CMVN"
    lift = best_r - baseline
    print(f"  BEST FRAME-RELATIVE: {best_em[0]}/{best_em[1]}  LOSO {best_r:.3f}  "
          f"(vs best baseline {base_name} {baseline:.3f}: {lift:+.3f})", flush=True)

    # === VERDICT ===
    print("\n" + "=" * 70, flush=True)
    print("VERDICT", flush=True)
    print("=" * 70, flush=True)
    if lift > 0.02:
        print(f"  PAYS: FRAME-RELATIVE ({best_em[0]}/{best_em[1]}) BEATS the best "
              f"zero-context baseline ({base_name} {baseline:.3f}) by {lift:+.3f} "
              "cross-speaker.", flush=True)
        print("  -> context + relative perception is the missing mechanism; the "
              "derived cure (sliding template) lifts past the absolute/removal bar.",
              flush=True)
    elif best_r > baseline:
        print(f"  WEAK: FRAME-RELATIVE edges {base_name} by only {lift:+.3f} (within "
              "noise). Direction right, magnitude below the 0.02 bar.", flush=True)
    else:
        print(f"  KILL: FRAME-RELATIVE does NOT beat the best zero-context baseline "
              f"({base_name} {baseline:.3f}; best REL {best_r:.3f}, {lift:+.3f}). "
              "Context+relative does not add cross-speaker invariance OVER absolute "
              "log-formants here -- the relative reading discards as much "
              "discriminative formant-pattern as the talker-frame normalization "
              "removes.", flush=True)
    # the secondary read: REL vs the CMVN removal bar specifically (the session's
    # ~0.50 absolute-removal class), for continuity with the prior KILLs.
    print(f"  (vs CMVN removal bar specifically: best REL {best_r:.3f} - CMVN "
          f"{cmvn_loso:.3f} = {best_r - cmvn_loso:+.3f})", flush=True)
    print(f"  CHAIN: ABS {abs_loso:.3f} | CMVN {cmvn_loso:.3f} | REL {best_r:.3f} | "
          f"chance {chance:.3f}", flush=True)
    print("\n[MARKER] FRAME_INFERENCE_V1_COMPLETED", flush=True)


def ctx_sweep():
    """DIAGNOSTIC: does MORE context help? Holds the test set fixed and varies how many
    UNLABELED context clips feed the frame estimate. If REL rises with context, the
    frame estimate is the crude part (better range -> better invariance); if it's flat,
    the relative reading itself is the ceiling. Uses the best REL variant (pctl/frac).

    Run: python -m scripts.frame_inference_v1 sweep [n_train_spk] [n_held_spk] [n_per]
    """
    n_train_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    n_held_spk = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    n_per = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    CTX_VALUES = [2, 4, 8, 14]
    EST, MODE = "pctl", "frac"
    max_ctx = max(CTX_VALUES)
    chance = 1.0 / len(W.sc_words())

    # build a split with the LARGEST context reserve; smaller n_ctx just uses a prefix
    # of the SAME reserved context clips -> the test set + bank are identical across ctx
    # values, so the only variable is how much context the frame estimate sees.
    print(f"[ctx-sweep] building split with max_ctx={max_ctx} reserve ...", flush=True)
    train_by_speaker, _seen, held = build_split(n_train_spk, n_held_spk, n_per, max_ctx)
    abs_bank = build_abs_bank(train_by_speaker, absolute_logf)

    # ABS baseline (zero context) once.
    abs_cor = abs_tot = 0
    for spk, (_c, clips) in held.items():
        for w, x, _fs in clips:
            abs_cor += int(recognise(absolute_logf(x), abs_bank) == w)
            abs_tot += 1
    abs_loso = abs_cor / max(abs_tot, 1)

    print("\n" + "=" * 60, flush=True)
    print("CONTEXT SWEEP — does more context lift FRAME-RELATIVE?", flush=True)
    print("=" * 60, flush=True)
    print(f"  test clips n={abs_tot}; ABS (zero-ctx) LOSO {abs_loso:.3f}; "
          f"chance {chance:.3f}", flush=True)
    print(f"  {'n_ctx':>6s} {'REL LOSO':>10s} {'vs ABS':>8s}", flush=True)
    for nc in CTX_VALUES:
        # rebuild the rel bank + read tests using only the first nc context clips.
        fc = {}
        tb = {s: (c[:nc], clips) for s, (c, clips) in train_by_speaker.items()}
        rel_bank = build_rel_bank(tb, EST, MODE, fc)
        cor = tot = 0
        for spk, (ctx, clips) in held.items():
            fr = infer_talker_frame(ctx[:nc], estimator=EST)
            for w, x, _fs in clips:
                cor += int(recognise(read_relative(x, fr, mode=MODE), rel_bank) == w)
                tot += 1
        r = cor / max(tot, 1)
        print(f"  {nc:6d} {r:10.3f} {r-abs_loso:+8.3f}", flush=True)
    print("\n[MARKER] FRAME_INFERENCE_CTX_SWEEP_COMPLETED", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        ctx_sweep()
    else:
        main()
