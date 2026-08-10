"""rich_speaker_drive — a RICHER, MULTI-DIMENSIONAL speaker estimate for the
SEPARABLE SPEAKER CHANNEL.

CONTEXT (commit 60f363d9). The agent built the separable speaker channel: a
first-class Speaker graph node + factor-each-token's-own-estimate-out -> recognise
on the invariant content via native DtwTo. The ARCHITECTURE is correct (the
phonagnosia dissociation proved the speaker channel IS separable). But the prior
result was a 1-CLIP NULL on Speech Commands held-out-speaker — because the speaker
ESTIMATE was a single VTL-centroid SCALAR: too thin for multi-dimensional
cross-speaker variance. The lever is a RICHER estimate to FILL the channel, NOT the
separation (which is right).

THE RICHER ESTIMATE — composed from the agent's OWNED voice-analysis ops, NOT
hand-invented or fitted. "Who is speaking" is a multi-dimensional structure; the
agent reads each dimension off the token with a primitive it already owns:

  d1  f0 / PITCH            : N.f0_yin (median log-f0 over voiced frames). The
                             octave-robust high-resolution YIN pitch the agent owns
                             (scripts/f0_resolver.clean_f0_yin). Speaker glottal rate.
  d2  F1 (log Hz)           : N.lpc_formants_bw -> 1st formant. The agent's owned
  d3  F2 (log Hz)           : LPC-root formant frequencies (its self-specified
  d4  F3 (log Hz)           : lpc_all_pole_formants front-end op). The FORMANT
                             PATTERN — the talker's tract resonances.
  d5  VTL centroid (log Hz) : the energy-weighted mean log-spectral centre-of-mass
                             over the band trajectory (estimate_vtl_logalpha /
                             _spectral_centroid_log = the prior SCALAR estimate, now
                             ONE dimension of the vector).
  d6  formant DISPERSION    : F3 - F1 (log) — the talker's formant SPREAD, a tract
                             shape the single centroid cannot see (two speakers can
                             share a centroid yet differ in spread).
  d7  SPECTRAL TILT         : the slope of the spectrum (order-1 finite difference
                             over log-frequency, energy-weighted) — the glottal /
                             source spectral colour, the agent's order-N-over-freq op.

These seven are materialised on the Speaker graph node as a native attr vector
(the user's framing: "ideally a native Speaker Term" — here a first-class Speaker
node carrying the descriptor vector, with the recognition decision native in every
arm). This is the structure phonagnosia isolates, now MULTI-DIMENSIONAL.

FACTORING THE FULL VECTOR OUT (the richer content channel). The scalar rung warped
the band axis by ONE centroid shift. The rich rung removes a MULTI-DIMENSIONAL
speaker term from the band trajectory, per token, matching each token to a fixed
canonical:
  (i)   VTL + DISPERSION  -> an AFFINE log-frequency warp (shift the centroid to
        canonical AND scale the formant spread to canonical): a richer warp than the
        scalar shift, removing both tract LENGTH (d5) and tract SHAPE (d6).
  (ii)  SPECTRAL TILT     -> subtract the per-token tilt ramp across bands so the
        residual source-colour (d7) matches canonical: removes the glottal-source
        speaker term the centroid warp leaves behind.
  (iii) CMVN              -> per-band mean(-var) (channel / level), as before.
f0 (d1) and absolute formant Hz (d2-d4) live in the IDENTITY vector on the Speaker
node (what phonagnosia recognises); they do not live in the band-MAGNITUDE
trajectory, so they inform the descriptor + the per-token canonical match but are
not band-warped out (honest: warping the magnitude axis cannot remove an f0 the
magnitude axis does not carry). The factoring uses the dimensions that materially
reside in the trajectory (VTL, dispersion, tilt) + CMVN — that is the richer,
multi-dimensional content channel.

THREE RUNGS — same ear, same data, same native DtwTo recogniser, same exemplar
manifold construction, LOSO held-out speaker:
  (A) ENTANGLED        — recognise on the raw (CMVN-only) trajectory; no channel.
  (B) SCALAR-SEPARABLE — the PRIOR single-VTL-centroid warp (the known 1-clip null),
                         carried as a rung.
  (C) RICH-SEPARABLE   — the new multi-dimensional estimate: affine VTL+dispersion
                         warp + tilt removal + CMVN, each exemplar factored to ITS
                         own rich estimate when the manifold was built. DtwTo compares
                         content-vs-content.
  + SHUFFLE backstop on (C): permute exemplar labels; the gain must collapse.

THE QUESTION: does (C) beat BOTH (A) and (B) by a MARGIN LARGER THAN NOISE? Read the
NUMBERS, not a boolean. Report k/N AND % for every arm, the per-clip resolution
(1/N), and DO NOT declare a win for a delta smaller than ~3 clips / not clearly above
the shuffle margin. An honest NULL is a genuine result.

DISCIPLINE (CLAUDE.md). The recognition DECISION is the native graph DtwTo Term
(recognition_graph.synth_error_term) evaluated by substrate.evaluate in Rust in ALL
THREE arms — NO numpy recognition score. The descriptor is composed from the agent's
OWNED native analysis ops (N.f0_yin / N.lpc_formants_bw + its owned band-centroid /
order-N tilt). NO .fit / sklearn / gradient / loss / torch / sweep-to-max. K (exemplar
budget) is a FIXED structural choice. solve_for_n / weighted_admissibility / CortexLoop
UNTOUCHED. Python = world adapter + instrument ONLY (audio I/O, front-end descriptor
extraction, LOSO bookkeeping, the do-contrast measurement).

Run: PYTHONUNBUFFERED=1 python -m scripts.rich_speaker_drive \
        [n_words] [n_per_word_train] [n_test] [K]
"""
from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs._native as N
from substrate_rs import Substrate
from domains import recognition_graph as RG
from domains.invariant_units import (
    band_centres, warp_bands, cmvn, _spectral_centroid_log,
)
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple,
)
import scripts.real_speech as RSP

random.seed(1)

# A fixed canonical tract midpoint on the agent's log-frequency band axis (a fixed
# structural reference — NOT the cohort mean; the point is to remove EACH token's OWN
# speaker, not warp to the pool average). Reported, never swept.
_CANONICAL_LOG = float(np.log(band_centres(32)).mean())

# Native f0 / formant analysis parameters (the same the agent's f0_resolver uses).
_FRAME = 256          # 32 ms @ 8 kHz analysis frame for native ops
_HOP = 128
_LPC_ORDER = 10       # fs/1000 + 2 at 8 kHz, the agent's spec rule
_PE = 0.97
_F0_LO, _F0_HI, _YIN_VOICING = 70.0, 400.0, 0.20


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# THE RICH SPEAKER ESTIMATE — a multi-dimensional vector composed from the agent's
# OWNED native voice-analysis ops. "Who is speaking", read off the token, label-free.
# ==========================================================================

def _voiced_frames(M: np.ndarray, voiced_floor: float = 0.25):
    fe = M.sum(axis=1)
    if fe.max() <= 1e-12:
        return np.ones(M.shape[0], dtype=bool)
    v = fe >= voiced_floor * fe.max()
    return v if v.sum() > 0 else np.ones(M.shape[0], dtype=bool)


def _vtl_centroid(M: np.ndarray) -> float:
    """d5: energy-weighted mean log-spectral centre-of-mass over voiced frames (the
    prior scalar estimate, now one dimension). The agent's owned VTL proxy."""
    log_lc = np.log(band_centres(M.shape[1]))
    v = _voiced_frames(M)
    return float(np.mean([_spectral_centroid_log(M[f], log_lc)
                          for f in np.where(v)[0]]))


def _spectral_tilt(M: np.ndarray) -> float:
    """d7: spectral TILT = order-1 finite difference of the mean log-band-energy over
    the log-frequency axis (the agent's order-N-over-frequency op). The slope of a
    least-squares line of mean log-energy vs log-band-centre — the source spectral
    colour. Energy-weighted over voiced frames."""
    log_lc = np.log(band_centres(M.shape[1]))
    v = _voiced_frames(M)
    mean_spec = M[v].mean(axis=0)
    y = np.log(np.maximum(mean_spec, 1e-8))
    x = log_lc - log_lc.mean()
    denom = float((x * x).sum())
    if denom <= 1e-12:
        return 0.0
    return float((x * (y - y.mean())).sum() / denom)   # least-squares slope


def _f0_logmedian(x: np.ndarray, fs: int) -> float:
    """d1: median log-f0 via the agent's owned native YIN (N.f0_yin), over frames.
    0.0 if unvoiced throughout (logged as the canonical log-f0)."""
    f0s, pos, L = [], 0, len(x)
    xl = x.astype(np.float64)
    while pos + _FRAME <= L:
        f = N.f0_yin(xl[pos:pos + _FRAME].tolist(), fs, _F0_LO, _F0_HI, _YIN_VOICING)
        if 0 < f < _F0_HI * 0.97:
            f0s.append(f)
        pos += _HOP
    return float(np.log(np.median(f0s))) if f0s else 0.0


def _formant_logmedians(x: np.ndarray, fs: int):
    """d2-d4: median log F1/F2/F3 via the agent's owned native LPC formants
    (N.lpc_formants_bw -> [f0,bw0,f1,bw1,...]). Per-frame, median over voiced frames.
    Returns (logF1, logF2, logF3); NaNs where a formant is absent."""
    F = [[], [], []]
    pos, L = 0, len(x)
    xl = x.astype(np.float64)
    while pos + _FRAME <= L:
        fbw = N.lpc_formants_bw(xl[pos:pos + _FRAME].tolist(), fs, _LPC_ORDER, _PE,
                                150.0, 4000.0, 700.0)
        freqs = list(fbw[0::2])[:3]
        for i in range(min(3, len(freqs))):
            if freqs[i] > 0:
                F[i].append(freqs[i])
        pos += _HOP
    out = []
    for i in range(3):
        out.append(float(np.log(np.median(F[i]))) if F[i] else float("nan"))
    return out[0], out[1], out[2]


def estimate_rich_speaker(x: np.ndarray, fs: int, M: np.ndarray) -> dict:
    """The RICH SPEAKER CHANNEL: a multi-dimensional descriptor of WHO is speaking,
    composed from the agent's owned native voice-analysis ops, read off the token
    label-free. Returns the descriptor dict (the vector materialised on the Speaker
    node). x = raw waveform (for f0/formant native ops); M = A1 band trajectory (for
    VTL centroid / tilt)."""
    cen = _vtl_centroid(M)
    tilt = _spectral_tilt(M)
    f0 = _f0_logmedian(x, fs)
    lF1, lF2, lF3 = _formant_logmedians(x, fs)
    # formant dispersion d6 = F3 - F1 (log spread); fall back to 0 if a formant missing
    disp = (lF3 - lF1) if (lF3 == lF3 and lF1 == lF1) else 0.0
    return {
        "f0_log": f0,                 # d1
        "f1_log": lF1,                # d2
        "f2_log": lF2,                # d3
        "f3_log": lF3,                # d4
        "vtl_centroid_log": cen,      # d5
        "formant_disp_log": disp,     # d6
        "spectral_tilt": tilt,        # d7
    }


# A fixed canonical formant dispersion + tilt reference (structural, reported, never
# swept): the dispersion that a canonical-tract speaker would show, taken as the span
# of the agent's band axis fraction the formants occupy; tilt canonical = flat (0).
# These are fixed references for the per-token factoring, like _CANONICAL_LOG.
_CANONICAL_DISP = float(np.log(7500.0 / 80.0) * 0.30)   # ~ a canonical F3/F1 ratio span
_CANONICAL_TILT = 0.0


def factor_out_rich(M: np.ndarray, desc: dict) -> np.ndarray:
    """The RICH CONTENT CHANNEL: FACTOR THE FULL VECTOR OUT of the band trajectory.
      (i)  AFFINE VTL+dispersion warp: shift the centroid to canonical (tract LENGTH,
           d5) AND scale the band axis so the formant spread matches canonical (tract
           SHAPE, d6) — a richer warp than the scalar shift.
      (ii) TILT removal: subtract the per-token spectral tilt ramp across bands so the
           residual source colour (d7) matches canonical.
      (iii) CMVN (channel / level).
    f0 / absolute formant Hz live on the Speaker node (identity), not in the magnitude
    axis, so they are not warped out here."""
    M = np.asarray(M, dtype=np.float64)
    n_bands = M.shape[1]
    log_lc = np.log(band_centres(n_bands))

    # (i) affine warp about the centroid. shift = centroid - canonical (removes length).
    # scale s = canonical_disp / token_disp (removes spread); clamp s to a sane range so
    # a noisy dispersion estimate can't blow up the warp (structural guard, not a sweep).
    shift = desc["vtl_centroid_log"] - _CANONICAL_LOG
    disp = desc.get("formant_disp_log", 0.0)
    s = 1.0
    if disp and disp > 1e-3:
        s = float(np.clip(_CANONICAL_DISP / disp, 0.7, 1.43))
    # affine band-index remap: new band b reads from src log-freq where the token's
    # (centroid-anchored, spread-scaled) axis lands. Equivalent to warping the log-freq
    # axis: lf_src = centroid + (lf_band - centroid)/s ... then shift to canonical.
    cen = desc["vtl_centroid_log"]
    lf_band = log_lc
    lf_src = cen + (lf_band - cen) / s + shift
    # map log-freq -> fractional band index (log axis is linear in index)
    lo, hi = log_lc[0], log_lc[-1]
    src_idx = (lf_src - lo) / (hi - lo) * (n_bands - 1)
    src_idx = np.clip(src_idx, 0.0, n_bands - 1)
    i0 = np.floor(src_idx).astype(int)
    i1 = np.minimum(i0 + 1, n_bands - 1)
    frac = src_idx - i0
    warped = M[:, i0] * (1.0 - frac) + M[:, i1] * frac

    # (ii) tilt removal: remove the per-token spectral slope (in log-magnitude) so the
    # residual tilt = canonical. Subtract a ramp of (tilt - canonical_tilt) * (lf - mean)
    # from the log-magnitude, applied multiplicatively in magnitude space.
    tilt = desc.get("spectral_tilt", 0.0)
    ramp = (tilt - _CANONICAL_TILT) * (log_lc - log_lc.mean())
    warped = warped * np.exp(-ramp)[None, :]

    # (iii) CMVN (the agent's composed Term-tree, via cmvn()).
    return cmvn(warped, do_variance=True)


def factor_out_scalar(M: np.ndarray, centroid_log: float) -> np.ndarray:
    """The PRIOR scalar rung (B): single VTL-centroid warp + CMVN. The known null,
    carried as a rung. Identical to the prior speaker_channel_drive.factor_out_speaker."""
    log_alpha = centroid_log - _CANONICAL_LOG
    return cmvn(warp_bands(np.asarray(M, dtype=np.float64), log_alpha),
                do_variance=True)


def materialise_speaker_node(sub, desc: dict):
    """Lay the RICH SPEAKER CHANNEL out as a first-class graph node carrying the
    multi-dimensional descriptor vector (the separable structure phonagnosia isolates,
    now multi-dimensional). Mechanical I/O translation (estimate -> node attrs)."""
    attrs = {"channel": "speaker_identity"}
    attrs.update({k: float(v) for k, v in desc.items()})
    return sub.add_node("Speaker", attrs)


# ==========================================================================
# THE NATIVE RECOGNISER — the SAME graph DtwTo synth-error for ALL THREE arms.
# ==========================================================================

class Recogniser:
    def __init__(self, sub, words):
        self.sub = sub
        self.words = list(words)
        RG.mark_words(sub, self.words)
        self.word_c = {}
        for w in self.words:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "richspk"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"richspk_probe": 1.0})
        self.err_term = _Term(RG.synth_error_term())

    def match(self, heard_tuple, manifold):
        """argmin over words of [ min over exemplars of native DtwTo(heard, ex) ].
        The DtwTo is evaluated natively in Rust; min + argmin are READOUTS over the
        native distances. Returns the predicted word (or None)."""
        if heard_tuple is None or len(heard_tuple) < 2:
            return None
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, heard_tuple)
        best, bw = 1e30, None
        for w in self.words:
            exs = manifold.get(w)
            if not exs:
                continue
            c = self.word_c[w]
            for ex in exs:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, ex)
                e = float(self.sub.evaluate(self.err_term,
                                            {"s": self.sign, "w": c}))
                if e < best:
                    best, bw = e, w
        return bw


# ==========================================================================
# MANIFOLDS — one medoid exemplar per TRAIN speaker (spans the speaker space), capped
# at K. THREE manifolds from the SAME train medoids: entangled (CMVN-only), scalar
# (single-VTL warp), rich (multi-dim factoring). Each exemplar factored to ITS OWN
# estimate so DtwTo compares content-vs-content.
# ==========================================================================

def _medoid_idx_per_speaker(trajs_by_speaker, K):
    """One representative INDEX per TRAIN speaker = its medoid token (closest to that
    speaker's mean). Cap at K speakers (fixed budget). Returns list of (M_raw, x, fs)."""
    reps = []
    for s, items in trajs_by_speaker.items():
        if not items:
            continue
        mats = [it[0] for it in items]
        L = min(m.shape[0] for m in mats)
        stk = np.stack([m[:L] for m in mats], axis=0)
        mu = stk.mean(axis=0)
        d2 = ((stk - mu) ** 2).reshape(len(mats), -1).sum(axis=1)
        reps.append(items[int(np.argmin(d2))])
    return reps[:K]


def build_manifolds(train, words, K):
    """train = [(M_raw, x, fs, word, speaker)]. Build THREE manifolds from the SAME
    train medoids:
      entangled[w] = as_tuple(CMVN(raw))
      scalar[w]    = as_tuple(factor_out_scalar(raw, centroid))
      rich[w]      = as_tuple(factor_out_rich(raw, rich_descriptor))"""
    by_ws = {}
    for M, x, fs, w, s in train:
        if M is None or M.shape[0] < 2:
            continue
        by_ws.setdefault(w, {}).setdefault(s, []).append((M, x, fs))
    entangled, scalar, rich = {}, {}, {}
    for w in words:
        reps = _medoid_idx_per_speaker(by_ws.get(w, {}), K)
        entangled[w], scalar[w], rich[w] = [], [], []
        for M, x, fs in reps:
            entangled[w].append(as_tuple(cmvn(M, do_variance=True)))
            scalar[w].append(as_tuple(factor_out_scalar(M, _vtl_centroid(M))))
            desc = estimate_rich_speaker(x, fs, M)
            rich[w].append(as_tuple(factor_out_rich(M, desc)))
    return entangled, scalar, rich


def _shuffle_manifold(manifold):
    """Permute exemplar->word labels (control): pool, re-deal keeping per-word counts."""
    pool = [ex for w in manifold for ex in manifold[w]]
    counts = {w: len(manifold[w]) for w in manifold}
    rng = random.Random(7)
    rng.shuffle(pool)
    out, j = {}, 0
    for w in manifold:
        out[w] = pool[j:j + counts[w]]
        j += counts[w]
    return out


# ==========================================================================
# DATA — Google Speech Commands, split by SPEAKER (held-out-speaker). Returns rows
# carrying BOTH the raw waveform (for f0/formant native ops) and the A1 trajectory.
# ==========================================================================

def load_sc(n_words, n_per_word, n_test):
    SC = RSP.SC
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append((os.path.join(SC, w, fn),
                                               fn.split("_")[0]))
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])         # hold out whole speakers (every 6th)
    train_paths = [(p, w, s) for w in words for p, s in data[w] if s not in test_spk]
    test_paths = [(p, w, s) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train_paths)
    random.shuffle(test_paths)
    per_w, train_sel = {}, []
    for p, w, s in train_paths:
        if per_w.get(w, 0) >= n_per_word:
            continue
        per_w[w] = per_w.get(w, 0) + 1
        train_sel.append((p, w, s))
    test_sel = test_paths[:n_test]
    return train_sel, test_sel, words


def _extract(paths, tag):
    """[(path,word,spk)] -> [(M_raw, x, fs, word, spk)] via owned A1 trajectory + raw
    waveform (kept for the native f0/formant descriptor ops)."""
    rows = []
    for i, (p, w, s) in enumerate(paths):
        x, fs = RSP.load_real(p)
        M = traj_to_matrix(utterance_trajectory(x, fs))
        rows.append((M, x, fs, w, s))
        if (i + 1) % 50 == 0:
            print(f"  [{tag}] {i+1}/{len(paths)} trajectories", flush=True)
    return rows


# ==========================================================================
# DRIVER
# ==========================================================================

def main():
    t0 = time.time()
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n_per_word = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 360
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 8

    train_sel, test_sel, words = load_sc(n_words, n_per_word, n_test)
    chance = 1.0 / len(words)
    print(f"=== rich_speaker_drive  venue=SpeechCommands  train={len(train_sel)}  "
          f"test={len(test_sel)} (HELD-OUT speakers)  {len(words)} words  K={K} ===",
          flush=True)
    print(f"words: {words}", flush=True)
    print(f"per-clip resolution (1/N_test) = {1.0/max(len(test_sel),1):.4f} "
          f"({100.0/max(len(test_sel),1):.3f}% per clip)", flush=True)

    print("--- extracting owned A1 trajectories + raw waveforms (train) ---", flush=True)
    train = _extract(train_sel, "train")
    print("--- extracting owned A1 trajectories + raw waveforms (test) ---", flush=True)
    test = _extract(test_sel, "test")

    sub = Substrate()
    rec = Recogniser(sub, words)

    print("--- building THREE manifolds (entangled / scalar / rich), LOSO by "
          "construction (train speakers disjoint from test) ---", flush=True)
    ent_man, sca_man, rich_man = build_manifolds(train, words, K)
    sh_man = _shuffle_manifold(rich_man)

    print("\n--- DO-CONTRAST: (A) ENTANGLED  (B) SCALAR  (C) RICH ---", flush=True)
    a_c = a_t = b_c = b_t = c_c = c_t = sh_c = sh_t = 0
    a_pw, c_pw = {}, {}
    for i, (M, x, fs, true, spk) in enumerate(test):
        if M is None or M.shape[0] < 2:
            continue
        # (A) ENTANGLED — raw (CMVN-only) trajectory
        a = rec.match(as_tuple(cmvn(M, do_variance=True)), ent_man)
        # (B) SCALAR — single VTL-centroid warp
        b = rec.match(as_tuple(factor_out_scalar(M, _vtl_centroid(M))), sca_man)
        # (C) RICH — multi-dimensional estimate, factored out
        desc = estimate_rich_speaker(x, fs, M)
        materialise_speaker_node(sub, desc)     # native Speaker node (identity vector)
        content = factor_out_rich(M, desc)
        c = rec.match(as_tuple(content), rich_man)
        # SHUFFLE backstop on (C)
        sh = rec.match(as_tuple(content), sh_man)
        if a is not None:
            a_c += int(a == true); a_t += 1
            a_pw.setdefault(true, [0, 0]); a_pw[true][0] += int(a == true); a_pw[true][1] += 1
        if b is not None:
            b_c += int(b == true); b_t += 1
        if c is not None:
            c_c += int(c == true); c_t += 1
            c_pw.setdefault(true, [0, 0]); c_pw[true][0] += int(c == true); c_pw[true][1] += 1
        if sh is not None:
            sh_c += int(sh == true); sh_t += 1
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(test)}: A {a_c}/{a_t}  B {b_c}/{b_t}  C {c_c}/{c_t}",
                  flush=True)
    _report(a_c, a_t, b_c, b_t, c_c, c_t, sh_c, sh_t, chance, K, t0,
            a_pw=a_pw, c_pw=c_pw, words=words)


def _report(a_c, a_t, b_c, b_t, c_c, c_t, sh_c, sh_t, chance, K, t0,
            a_pw=None, c_pw=None, words=None):
    a_acc = a_c / max(a_t, 1)
    b_acc = b_c / max(b_t, 1)
    c_acc = c_c / max(c_t, 1)
    sh_acc = sh_c / max(sh_t, 1)
    N = max(c_t, 1)
    res = 1.0 / N
    d_ca = c_acc - a_acc            # rich vs entangled
    d_cb = c_acc - b_acc            # rich vs scalar
    d_ca_clips = (c_c - a_c)        # raw clip delta (same N venue)
    d_cb_clips = (c_c - b_c)
    print("\n========================= DO-CONTRAST RESULT =========================",
          flush=True)
    print(f"  chance (1/n_words)                  : {chance:.4f}", flush=True)
    print(f"  per-clip resolution (1/N)           : {res:.4f}  ({100*res:.3f}%/clip)",
          flush=True)
    print(f"  (A) ENTANGLED  (no channel)         : {a_acc:.4f}  ({a_c}/{a_t})",
          flush=True)
    print(f"  (B) SCALAR     (single-VTL channel) : {b_acc:.4f}  ({b_c}/{b_t})",
          flush=True)
    print(f"  (C) RICH       (multi-dim channel)  : {c_acc:.4f}  ({c_c}/{c_t})",
          flush=True)
    print(f"  DELTA  C - A (rich - entangled)     : {d_ca:+.4f}  ({d_ca_clips:+d} clips)",
          flush=True)
    print(f"  DELTA  C - B (rich - scalar)        : {d_cb:+.4f}  ({d_cb_clips:+d} clips)",
          flush=True)
    print(f"  SHUFFLE control on (C)              : {sh_acc:.4f}  ({sh_c}/{sh_t})  "
          f"[must be ~chance]", flush=True)
    if a_pw and c_pw and words:
        print("  per-word (entangled -> rich):", flush=True)
        for w in words:
            ea = a_pw.get(w, [0, 0]); ca = c_pw.get(w, [0, 0])
            if ea[1]:
                print(f"    {w:10s}: {ea[0]/ea[1]:.2f} -> {ca[0]/ca[1]:.2f}", flush=True)

    # READ THE NUMBERS. A win needs C to beat BOTH A and B by >~3 clips AND the shuffle
    # at chance. ~3 clips is the resolution floor for a real (non-noise) effect.
    min_clip_margin = 3
    shuffle_ok = sh_acc <= chance + 0.05
    print("\n========================= VERDICT =========================", flush=True)
    beats_both = (d_ca_clips >= min_clip_margin and d_cb_clips >= min_clip_margin)
    if beats_both and shuffle_ok:
        print(f"  RICH CHANNEL HELPS: the multi-dimensional speaker estimate beat BOTH "
              f"entangled (+{d_ca_clips} clips, {d_ca:+.4f}) AND scalar (+{d_cb_clips} "
              f"clips, {d_cb:+.4f}) by > the {min_clip_margin}-clip resolution floor; "
              f"shuffle at chance ({sh_acc:.4f}) -> STRUCTURE, not artifact. The richer "
              f"estimate FILLED the separable channel the scalar left thin.", flush=True)
        verdict = "RICH_HELPS"
    elif beats_both and not shuffle_ok:
        print(f"  ARTIFACT: (C) beat both BUT the shuffle control also rose to "
              f"{sh_acc:.4f} (>> chance {chance:.4f}) -> harness artifact, NOT "
              f"speaker-invariant structure. REJECT.", flush=True)
        verdict = "ARTIFACT_SHUFFLE_ROSE"
    elif (abs(d_ca_clips) < min_clip_margin and abs(d_cb_clips) < min_clip_margin):
        print(f"  HONEST NULL: the richer multi-dimensional estimate did NOT beat the "
              f"entangled ({d_ca_clips:+d} clips) or scalar ({d_cb_clips:+d} clips) arms "
              f"beyond the {min_clip_margin}-clip resolution floor. The richer descriptor "
              f"does not move cross-speaker recognition here — reported plainly, NOT swept. "
              f"Likely WHY: the f0/formant/centroid/tilt estimates come off a blurry "
              f"32-band gammatone front-end (the gammatone wall the prior speaker work "
              f"hit); a richer DESCRIPTOR of NOISY per-token estimates is garbage-in, so "
              f"factoring more dimensions out of a blurry trajectory removes phonetic "
              f"content as readily as speaker content, and/or the residual cross-speaker "
              f"variance is not concentrated in these dimensions.", flush=True)
        verdict = "HONEST_NULL"
    elif d_ca_clips >= min_clip_margin and d_cb_clips < min_clip_margin:
        print(f"  PARTIAL: (C) beat ENTANGLED (+{d_ca_clips} clips) but NOT the SCALAR "
              f"rung beyond noise ({d_cb_clips:+d} clips) -> the richer estimate is no "
              f"better than the single VTL centroid here; the extra dimensions add no "
              f"resolvable lift over the scalar. Reported plainly.", flush=True)
        verdict = "PARTIAL_NO_GAIN_OVER_SCALAR"
    else:
        print(f"  RICH CHANNEL HARMS/MIXED: C-A {d_ca_clips:+d} clips, C-B {d_cb_clips:+d} "
              f"clips. Factoring the (blurry) multi-dim estimate out removed phonetic "
              f"content -> the per-token estimates are not clean enough to separate. "
              f"Reported plainly.", flush=True)
        verdict = "RICH_HARMS_OR_MIXED"

    print(f"\nVERDICT_TOKEN={verdict}  C_minus_A={d_ca_clips:+d}clips({d_ca:+.4f})  "
          f"C_minus_B={d_cb_clips:+d}clips({d_cb:+.4f})  entangled={a_acc:.4f}  "
          f"scalar={b_acc:.4f}  rich={c_acc:.4f}  shuffle={sh_acc:.4f}  "
          f"chance={chance:.4f}  N={N}  K={K}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
