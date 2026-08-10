"""Stage-2 STRUCTURAL READINESS RE-CHECK — the SONORITY-VALLEY SKELETON.

This is the agent's OWN precise within-Stage-2 fix (commit 0c8d6a20). Stage 2's
PART 1 (the voiced<->unvoiced AXIS) already fired strongly (d'=6.02, 100% of
tokens, graded per digit). PART 2 (coherent sharpening) did NOT, because the
sonority prong was the WRONG SHAPE: a FULL-ENVELOPE `DtwTo` over the per-frame
graded-voicing trajectory is a weak word-discriminator (sonority-alone
separability 0.147 vs chance 0.10) that adds correlated noise on place-confusable
ties and REGRESSED the coarse separation (0.761 -> 0.745).

The agent's own diagnosis (fix-the-fixer, memory ozma_fix_the_fixer): re-compose
the sonority prong as a SEGMENTATION SKELETON / manner-class landmark, NOT a
full-envelope DtwTo. Expose the already-native `detect_sonority_valleys`
(audio_primitives.rs:1217 — now bound at `substrate_rs._native.detect_sonority_valleys`)
and use the sonority-valley segmentation to extract the word's DISCRETE
manner/sonority SKELETON: the sequence of sonority peaks (vowel nuclei) and
valleys (consonant boundaries) — the COUNT and PATTERN (e.g. `six` =
fric-vowel-stop-fric vs `two` = stop-vowel). Disambiguate words by this
structural skeleton, fused with the Stage-1 coarse place recogniser by
weighted-admissibility (MEASURED reliability, not swept). SQUINT-FIRST: the
coarse manner GESTALT (the syllable/sonority pattern), not fine frication
quality.

THE KEY DIFFERENCE FROM THE FAILED PRONG (the prong SHAPE, the agent's point):
  * FAILED: DtwTo over the FULL per-frame voicing envelope (hundreds of frames;
    a dense trajectory; weak discriminator; correlated noise on ties).
  * SKELETON: DtwTo over the DISCRETE LANDMARK SEQUENCE — the sonority value
    sampled AT each nucleus peak and each valley, in temporal order (typically
    1-7 elements). A SHORT manner-class pattern. The native banded-DTW aligns
    sequences of DIFFERENT length (band 8), so a word with more landmarks
    (`six`: fric-vowel-stop-fric) is distinguished from one with fewer (`two`:
    stop-vowel) BY THE ALIGNMENT itself — exactly the manner-class landmark
    match. This is the agent's "segment by sonority valleys ... the sonority
    skeleton" applied as the prong, instead of a dense envelope.

PER-STAGE GATE DISCIPLINE (memory ozma_no_premature_testing_mid_curriculum): the
success signal is the binary READINESS gate read from self-measurement
(structure-admitted, the (G,Γ) structural separation), NOT a held-out LOSO
accuracy sweep. The accuracy test comes AFTER the curriculum.

DONKEY (audited):
  * NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO swept knob.
  * The skeleton uses the NATIVE segmenter (`detect_sonority_valleys`, the
    PyO3 binding just added) + the agent's OWNED native TFS voicing chain
    (tfs_voicing_track, validated commit 90b799c9) sampled at the landmarks.
  * The recognition decision is COMPOSED as native graph Terms (T1 `Argmin`
    over words of a T8 weighted SUM of the Stage-1 place `DtwTo` prong + the
    SKELETON `DtwTo` prong), evaluated by the Rust substrate. No Python
    decision over graph state.
  * The prong weight is a MEASUREMENT (above-chance skeleton separability mapped
    to [0,1], the agent's max(0,(acc-chance)/(1-chance)) rule), never tuned.
  * `CortexLoop` + `scripts/solve_for_n.py` untouched.
  * No held-out accuracy banked as the verdict; the gate is the STRUCTURAL
    separation / coherent-sharpening signal.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_skeleton_check`
"""
from __future__ import annotations

import os
import re
import wave

import numpy as np

import domains.native_cognition as NC
import domains.acoustic_resolution as AR
import domains.agent_frontend as AF
from substrate_rs import Substrate
import substrate_rs._native as _n


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")

FS = 8000
FRAME_MS = 32.0
HOP_MS = 12.0
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)
TFS_HOP = int(FS * HOP_MS / 1000)
TFS_MINLAG, TFS_MAXLAG = 25, 100
TFS_NLAGS = TFS_MAXLAG + 1

# --- the broadband total envelope the segmenter reads (full time resolution) --
# The Stage-1 PLACE squint is a fixed 32-frame gestalt — far too coarse for the
# native segmenter to land manner-class valleys (env_fs ~40-110 Hz starves the
# ms params to ~2-4 samples; it returns 0 valleys even at depth 0.05). So the
# SONORITY total envelope is built at FULL time resolution from a native cochlear
# bank (sum of hair-cell envelopes), the SAME OWNED native primitives, decimated
# to a 1 kHz grid where the ms segmenter params map correctly. A perception
# front-end choice (give the segmenter an envelope it can resolve), NOT a knob.
SEG_FCS = (200.0, 350.0, 550.0, 800.0, 1200.0, 1800.0, 2600.0, 3600.0)
SEG_ENV_CUTOFF_HZ = 200.0    # hair-cell LPF — syllable/manner-rate envelope
SEG_DECIM = 8                # 8 kHz -> 1 kHz envelope grid
SEG_ENV_FS = FS // SEG_DECIM
# Word-rate isolated digits: ~25 ms smoothing suppresses intra-phoneme jitter;
# ~50 ms min-separation keeps syllable/manner-scale landmarks; a modest 0.18
# depth admits the manner-class valleys (consonant boundaries) without flooding
# on micro-dips. Fixed front-end constants, the same for every word.
SEG_SMOOTH_MS = 25.0
SEG_MIN_SEP_MS = 50.0
SEG_DEPTH = 0.18


def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float64) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float64), fs


def gather_files():
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        out.append((os.path.join(DATA_DIR, fn), int(digit), speaker, int(idx)))
    return out


# ---------------------------------------------------------------------------
# the agent's OWNED NATIVE TFS graded-voicing chain (the sonority AXIS, validated
# 90b799c9). Per-frame periodicity in [0,1] = the SONORITY signal we will SAMPLE
# at the skeleton landmarks. Returns (strengths, frame_centres_in_samples).
# ---------------------------------------------------------------------------

def tfs_voicing_track(sig, fs):
    s = np.asarray(sig, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None, None
    s_list = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)
        ac = _n.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None, None
    sacf = _n.summary_autocorrelogram(band_acs, TFS_NLAGS)
    if not sacf:
        return None, None
    pt = _n.periodicity_track(sacf, TFS_NLAGS, TFS_MINLAG, TFS_MAXLAG)
    if not pt:
        return None, None
    strengths = np.array(pt[0::2], dtype=np.float64)
    # frame f covers samples [f*HOP, f*HOP+WIN); centre = f*HOP + WIN/2.
    centres = np.array([f * TFS_HOP + TFS_WIN / 2.0 for f in range(len(strengths))])
    return strengths, centres


# ---------------------------------------------------------------------------
# THE STAGE-1 PLACE SQUINT (T5): VERBATIM from the working prerequisite recogniser.
# ---------------------------------------------------------------------------

def coarse_trajectory(x, fs, resolution):
    M = AF.cochleagram(x, fs, AF._MIDDLE[1], AF._MIDDLE[2], AF._MIDDLE[3])
    if M.size == 0:
        return None
    rows = []
    for r in range(M.shape[0]):
        bands = [float(g.mean()) for g in np.array_split(M[r], resolution)]
        mu = sum(bands) / len(bands)
        rows.append([b - mu for b in bands])
    return rows


def total_envelope(x, fs):
    """The broadband sonority envelope at FULL time resolution = sum of native
    hair-cell envelopes across a cochlear bank, decimated to a 1 kHz grid. The
    total-energy track the native sonority-valley segmenter reads its minima off
    (audio_primitives.rs `detect_sonority_valleys`). Mechanical world-adapter:
    native gammatone_band -> native hair_cell_envelope -> sum -> decimate. NO
    Python DSP decision. Returns (env_on_1kHz_grid, samples_per_env_step)."""
    s = np.asarray(x, dtype=np.float32).tolist()
    acc = None
    for fc in SEG_FCS:
        band = _n.gammatone_band(s, FS, float(fc), 4)                 # native band
        env = np.array(_n.hair_cell_envelope(band, SEG_ENV_CUTOFF_HZ, FS),
                       dtype=np.float32)                              # native IHC env
        if acc is None:
            acc = env
        else:
            m = min(len(acc), len(env))
            acc = acc[:m] + env[:m]
    if acc is None or len(acc) < 8:
        return None, None
    env = acc[::SEG_DECIM]                          # 8 kHz -> 1 kHz envelope grid
    return env, SEG_DECIM                           # SEG_DECIM raw samples per step


# ---------------------------------------------------------------------------
# THE SONORITY-VALLEY SKELETON (the agent's re-composed prong SHAPE). Use the
# NATIVE segmenter on the broadband total envelope to find the consonant-boundary
# valleys; the spans between them are the sonorant nuclei. Build the DISCRETE
# manner/sonority skeleton: the graded TFS sonority value sampled AT each NUCLEUS
# PEAK and each VALLEY, in temporal order. A short landmark sequence (the
# manner-class pattern), NOT the dense per-frame envelope. The COUNT and PATTERN
# of landmarks is what disambiguates (six: more landmarks; two: fewer).
# ---------------------------------------------------------------------------

def _sample_sonority_at(samp_centres, son, target_sample):
    """The graded TFS sonority at a given sample position (nearest TFS frame)."""
    if son is None or len(son) == 0:
        return 0.0
    j = int(np.argmin(np.abs(samp_centres - target_sample)))
    return float(son[j])


def sonority_skeleton(x, fs):
    """The word's discrete sonority/manner SKELETON as a short sequence (frames x 1
    for the native DtwTo): the graded TFS sonority sampled at the ordered sequence
    of NUCLEUS PEAKS (sonorant maxima between valleys) and VALLEYS (consonant
    boundaries). Mean-subtracted on its own axis so the skeleton SHAPE is relative
    (the manner PATTERN, not absolute level). NATIVE segmenter + native voicing."""
    env, hop = total_envelope(x, fs)
    son, son_centres = tfs_voicing_track(x, fs)
    if env is None or son is None or len(son) < 2:
        return None
    n = len(env)
    # NATIVE valley detection on the broadband total envelope (1 kHz grid). The
    # ms segmenter params map at SEG_ENV_FS; `hop` (= SEG_DECIM) maps an env-grid
    # index back to a raw sample position for the TFS sonority sampling.
    flat = _n.detect_sonority_valleys(env.tolist(), SEG_ENV_FS,
                                      SEG_SMOOTH_MS, SEG_MIN_SEP_MS, SEG_DEPTH)
    valley_frames = sorted(int(flat[4 * k]) for k in range(len(flat) // 4))
    # The segmentation: valleys split the word into sonorant spans. Build the
    # ordered landmark sample positions = nucleus-peak of each span, interleaved
    # with the valleys. (nucleus_0, valley_0, nucleus_1, valley_1, ..., nucleus_k)
    bounds = [0] + valley_frames + [n]
    landmarks = []     # list of (sample_position, kind) in temporal order
    for i in range(len(bounds) - 1):
        a, b = bounds[i], bounds[i + 1]
        if b <= a:
            continue
        # nucleus = the sonorant PEAK of this span (max total energy).
        peak_local = a + int(np.argmax(env[a:b]))
        landmarks.append((peak_local * hop, "nuc"))
        if i < len(bounds) - 2:                 # a valley follows this span
            landmarks.append((valley_frames[i] * hop, "val"))
    if not landmarks:
        # degenerate (no internal structure): single nucleus at the global peak.
        peak = int(np.argmax(env))
        landmarks = [(peak * hop, "nuc")]
    # sample the graded TFS sonority at each landmark -> the skeleton sequence.
    skel = [_sample_sonority_at(son_centres, son, pos) for pos, _ in landmarks]
    mu = float(np.mean(skel))
    return [[float(v - mu)] for v in skel]      # relative manner pattern (L x 1)


def _tuple(track):
    return tuple(tuple(float(v) for v in frame) for frame in track)


# ---------------------------------------------------------------------------
# THE NATIVE FUSED DECISION (T1 + T2 + T8): Argmin over words of
#   d(w) = DtwTo(obs_place, proto_place(w)) + w_skel * DtwTo(obs_skel, proto_skel(w))
# the SKELETON prong replaces the failed full-envelope prong. Composed as native
# graph Terms, evaluated by the Rust substrate. w_skel is the MEASURED skeleton
# reliability (above-chance separability mapped to [0,1]) — a measurement.
# ---------------------------------------------------------------------------

SKEL_REL_ATTR = "skel_rel"     # observed skeleton, on the Query
SYN_SKEL_ATTR = "syn_skel"     # prototype skeleton, per word


def _place_prong():
    return NC._DtwTo(NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                     NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))


def _skeleton_prong():
    return NC._DtwTo(NC._Attr(NC._V("q"), SKEL_REL_ATTR),
                     NC._Attr(NC._V("w"), SYN_SKEL_ATTR))


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def fused_score_term(w_skel):
    return NC._Argmin(
        NC._word_set(), "w",
        NC._Plus([_place_prong(),
                  NC._Times([NC._Lit(float(w_skel)), _skeleton_prong()])]))


def build_substrate(place_protos, skel_protos):
    s = Substrate()
    word_nodes = {}
    for w in place_protos:
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, NC.WORD_ATTR, 1.0)
        s.set_attr(nid, NC.SYN_REL_ATTR, _tuple(place_protos[w]))
        s.set_attr(nid, SYN_SKEL_ATTR, _tuple(skel_protos[w]))
        word_nodes[w] = nid
    q = s.add_node("Query", {NC.OBS_REL_ATTR: ((0.0, 0.0, 0.0),),
                             SKEL_REL_ATTR: ((0.0,),)})
    return s, q, word_nodes


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=== Stage-2 RE-CHECK — the SONORITY-VALLEY SKELETON (the agent's "
          "within-stage fix, 0c8d6a20) ===")
    print("PART 1 (voiced<->unvoiced AXIS) already ADMITTED (d'=6.02). This "
          "re-check tests whether PART 2 (coherent sharpening) NOW FIRES with the "
          "skeleton prong SHAPE replacing the failed full-envelope DtwTo.\n")

    files = gather_files()
    resolution = int(AR._DEFAULT_RES)
    print(f"--- the native segmenter (detect_sonority_valleys, just bound) + the "
          f"Stage-1 PLACE squint (resolution={resolution}) ---")

    place = {}     # token -> coarse place trajectory
    skel = {}      # token -> sonority-valley skeleton (landmarks x 1)
    n_landmarks = {}   # token -> count of skeleton landmarks (the structural count)
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        pt = coarse_trajectory(x, fs, resolution)
        sk = sonority_skeleton(x, fs)
        if pt is None or len(pt) < 2 or sk is None or len(sk) < 1:
            continue
        place[(digit, speaker, idx)] = pt
        skel[(digit, speaker, idx)] = sk
        n_landmarks[(digit, speaker, idx)] = len(sk)

    n_tok = len(place)
    speakers = sorted({k[1] for k in place})
    print(f"  tokens with BOTH place + skeleton: {n_tok}, {len(speakers)} speakers")
    place_composes = n_tok > 0 and all(len(t[0]) == resolution for t in place.values())
    skel_composes = n_tok > 0 and all(len(t[0]) == 1 and len(t) >= 1 for t in skel.values())
    print(f"  >>> the place squint COMPOSES: {place_composes}")
    print(f"  >>> the sonority SKELETON COMPOSES (every token -> discrete landmark "
          f"seq): {skel_composes}")

    # the structural skeleton COUNT per digit — does the manner-class landmark
    # count carry word-discriminating structure? (six should have more landmarks
    # than two). A structural property of the segmentation, read for evidence.
    cnt_by_digit = {d: [] for d in range(10)}
    for (d, sp, idx), c in n_landmarks.items():
        cnt_by_digit[d].append(c)
    print("\n--- the manner-class landmark COUNT per digit (the skeleton structure) ---")
    for d in range(10):
        cs = cnt_by_digit[d]
        if cs:
            print(f"    {_DIGITS[d]:6s}: mean landmarks {np.mean(cs):.2f} "
                  f"(range {min(cs)}-{max(cs)})")
    all_counts = [c for cs in cnt_by_digit.values() for c in cs]
    if all_counts:
        between_var = np.var([np.mean(cs) for cs in cnt_by_digit.values() if cs])
        within_var = np.mean([np.var(cs) for cs in cnt_by_digit.values() if len(cs) > 1])
        f_like = between_var / (within_var + 1e-9)
        print(f"  landmark-count between/within variance ratio (structure in the "
              f"count): {f_like:.3f}")

    # === prototypes (one held exemplar per digit, both axes) ====================
    proto_speaker = speakers[0]
    place_protos, skel_protos = {}, {}
    for d in range(10):
        cand = sorted([(k, v) for k, v in place.items()
                       if k[0] == d and k[1] == proto_speaker],
                      key=lambda kv: kv[0][2])
        if cand:
            key = cand[0][0]
            place_protos[_DIGITS[d]] = place[key]
            skel_protos[_DIGITS[d]] = skel[key]

    # === MEASURE the skeleton prong reliability (the T8 weight, NOT a sweep) =====
    s_w, q_w, wn_w = build_substrate(place_protos, skel_protos)
    skel_only = _Pred(NC._Argmin(NC._word_set(), "w", _skeleton_prong()))
    place_only = _Pred(NC._Argmin(NC._word_set(), "w", _place_prong()))
    skel_correct = place_correct = n_eval = 0
    for (d, sp, idx), pt in place.items():
        w = _DIGITS[d]
        if w not in wn_w:
            continue
        s_w.set_attr(q_w, NC.OBS_REL_ATTR, _tuple(pt))
        s_w.set_attr(q_w, SKEL_REL_ATTR, _tuple(skel[(d, sp, idx)]))
        pick_skel = s_w.evaluate(skel_only, {"q": q_w})
        pick_place = s_w.evaluate(place_only, {"q": q_w})
        if pick_skel is not None and s_w.node(pick_skel)["attrs"].get("name") == w:
            skel_correct += 1
        if pick_place is not None and s_w.node(pick_place)["attrs"].get("name") == w:
            place_correct += 1
        n_eval += 1
    chance = 1.0 / max(len(place_protos), 1)
    skel_acc = skel_correct / max(n_eval, 1)
    place_acc = place_correct / max(n_eval, 1)
    w_skel = max(0.0, (skel_acc - chance) / (1.0 - chance + 1e-9))
    print(f"\n--- the T8 SKELETON-prong WEIGHT (a MEASUREMENT, not a sweep) ---")
    print(f"  skeleton-ALONE separability (native Argmin of skeleton DtwTo): "
          f"{skel_acc:.3f} (chance {chance:.3f})")
    print(f"  place-ALONE separability (the Stage-1 prong, reference)      : "
          f"{place_acc:.3f}")
    print(f"  (CONTRAST: the FAILED full-envelope prong scored 0.147 here — the "
          f"skeleton is the SHAPE the agent re-composed.)")
    print(f"  => measured skeleton reliability weight w_skel = {w_skel:.3f}")

    # === COMPOSE the FUSED native decision ======================================
    s, q, word_nodes = build_substrate(place_protos, skel_protos)
    fused = _Pred(fused_score_term(w_skel))
    s.set_attr(q, NC.OBS_REL_ATTR, _tuple(place_protos[_DIGITS[0]]))
    s.set_attr(q, SKEL_REL_ATTR, _tuple(skel_protos[_DIGITS[0]]))
    self_pick = s.evaluate(fused, {"q": q})
    fused_composes = self_pick is not None
    print(f"\n--- the FUSED native decision (T1 Argmin of T8(place DtwTo + "
          f"w_skel*SKELETON DtwTo)) ---")
    print(f"  fused recognition Term composes + evaluates natively: {fused_composes}")

    # === GATE PART 2: does the SKELETON COHERENTLY SHARPEN over place-alone? =====
    place_sep = fused_sep = recovered = regressed = n_scored = 0
    within_f, between_f = [], []
    for (d, sp, idx), pt in place.items():
        w = _DIGITS[d]
        if w not in word_nodes:
            continue
        s.set_attr(q, NC.OBS_REL_ATTR, _tuple(pt))
        s.set_attr(q, SKEL_REL_ATTR, _tuple(skel[(d, sp, idx)]))
        own_p = own_f = None
        oth_p, oth_f = [], []
        for wname, nid in word_nodes.items():
            dp = float(s.evaluate(_Pred(_place_prong()), {"q": q, "w": nid}))
            df = float(s.evaluate(
                _Pred(NC._Plus([_place_prong(),
                                NC._Times([NC._Lit(float(w_skel)),
                                           _skeleton_prong()])])),
                {"q": q, "w": nid}))
            if wname == w:
                own_p, own_f = dp, df
            else:
                oth_p.append(dp)
                oth_f.append(df)
        if own_p is None or not oth_p:
            continue
        n_scored += 1
        p_ok = own_p < np.mean(oth_p)
        f_ok = own_f < np.mean(oth_f)
        place_sep += int(p_ok)
        fused_sep += int(f_ok)
        if f_ok and not p_ok:
            recovered += 1
        if p_ok and not f_ok:
            regressed += 1
        within_f.append(own_f)
        between_f.append(float(np.mean(oth_f)))

    within_f = np.asarray(within_f)
    between_f = np.asarray(between_f)
    pooled_f = np.sqrt(0.5 * (within_f.var() + between_f.var())) + 1e-9
    fused_gap = float((between_f.mean() - within_f.mean()) / pooled_f)
    place_sep_frac = place_sep / max(n_scored, 1)
    fused_sep_frac = fused_sep / max(n_scored, 1)

    print(f"\n--- GATE PART 2: SKELETON-augmented SHARPENING over place-alone ---")
    print(f"  tokens scored                                  : {n_scored}")
    print(f"  place-ALONE structural separation (Stage 1)    : {place_sep_frac:.3f}")
    print(f"  FUSED place+SKELETON structural separation     : {fused_sep_frac:.3f}")
    print(f"  delta separation (fused - place)               : "
          f"{fused_sep_frac - place_sep_frac:+.3f}")
    print(f"  tokens RECOVERED by skeleton (place-confused -> fused-separated): "
          f"{recovered}")
    print(f"  tokens REGRESSED (anchor drag)                 : {regressed}")
    print(f"  fused standardized cluster gap (d')            : {fused_gap:.3f}")
    print(f"  (CONTRAST: the full-envelope prong gave 0.761 -> 0.745, 201 regressed "
          f"vs 151 recovered. The skeleton's job: sharpen, not regress.)")

    # === THE READINESS GATE =====================================================
    anchor_safe = (fused_sep_frac >= place_sep_frac - 1e-9)
    sharpens = (fused_sep_frac >= place_sep_frac and recovered > 0
                and fused_gap > 0.2)
    structure_admitted = (place_composes and skel_composes and fused_composes
                          and anchor_safe and sharpens)

    print(f"\n=== READINESS GATE (PART 2 re-check) ===")
    print(f"  skeleton composes (discrete landmark seq)            : {skel_composes}")
    print(f"  fused decision composes (Argmin place + w*SKELETON)  : {fused_composes}")
    print(f"  PART 1 voiced<->unvoiced AXIS (already admitted, d'=6.02): True")
    print(f"  PART 2 SKELETON SHARPENS over place-alone (recovers) : "
          f"{sharpens} (delta {fused_sep_frac - place_sep_frac:+.3f}, "
          f"recovered {recovered}, regressed {regressed})")
    print(f"  anchor NOT dragged (fused sep >= place sep)          : {anchor_safe}")
    print(f"  >>> STAGE-2 PART 2 (coherent sharpening) ADMITTED    : {structure_admitted}")
    print(f"  >>> STAGE-2 AS A WHOLE COMPLETE (both halves)        : {structure_admitted}")

    print(f"\n  NOTE: this is the STRUCTURAL gate (the sonority SKELETON sharpens the "
          f"coarse recogniser), NOT a held-out LOSO accuracy. The accuracy test "
          f"comes AFTER the curriculum, never as the per-stage gate.")
    print("===MARKER_STAGE2_SKELETON_CHECK_COMPLETE===")


if __name__ == "__main__":
    main()
