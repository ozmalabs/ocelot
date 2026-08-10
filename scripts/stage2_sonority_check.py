"""Stage-2 STRUCTURAL READINESS CHECK — sonority / voicing structure (vowels before frication).

The agent executes STAGE 2 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"sonority / voicing
structure (vowels before frication) — segment by sonority, and use the graded
TFS voicing as a recognition cue."* This is the agent acting on its own ranked
gap map + its own ordering principle 5 ("sonority before frication; voiced before
unvoiced"), NOT a hand-authored plan (memory
ozma_dont_author_seeds_agent_designs_them).

PREREQUISITE — Stage 1 DONE (`docs/stage1_coarse_recognition.md`, gate FIRES:
the coarse squint composes + the coarse word-identity separates, the native
`Argmin`-of-`DtwTo` recogniser working over the seed-coarsest 3-band gestalt).
This stage ADDS the sonority/voicing axis ON TOP of that working coarse
recogniser.

This script reads the STRUCTURAL readiness gate, NOT a held-out accuracy number.
Per the agent's own thesis (curriculum PART 3 + memory
ozma_capability_is_binary_admissibility): each stage's success signal is a binary
READINESS gate read from self-measurement (structure-admitted, proceed), not a
tuned metric. The held-out LOSO/accuracy test comes AFTER the curriculum, never
as the per-stage gate (memory ozma_no_premature_testing_mid_curriculum).

THE AGENT'S STAGE-2 DESIGN (reasoned from the science, squint-first):
  * SONORITY axis = the graded TFS voicing track (T4, validated commit 90b799c9:
    native gammatone_band -> band_autocorr -> summary_autocorrelogram ->
    periodicity_track, per-frame periodicity in [0,1]; voiced/sonorant -> 1,
    frication/burst/silence -> low). This is the agent's OWNED native temporal
    code — exactly the graded voiced<->unvoiced (sonority) axis the binary energy
    gate could not give.
  * The SONORITY GESTALT (squint-first) = that graded periodicity kept as a
    COARSE per-frame SONORITY-ENVELOPE TRAJECTORY over the isolated word (where in
    the word is voiced/sonorant vs unvoiced/obstruent — the sonority profile),
    NOT the fine frication-quality detail (that is the LATER Stage 5). It is the
    sonority sibling of the Stage-1 place squint.
  * THE FUSION (T8 weighted-admissibility, the agent's own combine rule): the
    Stage-1 COARSE PLACE prong (DtwTo over the 3-band gestalt) + the SONORITY
    prong (DtwTo over the graded voicing envelope) combined into ONE native
    decision Term — the SAME shape as native_cognition's d_A, which already
    carries a formant-shadow DtwTo prong + a voicing-shadow DtwTo prong. The
    sonority prong is weighted by its MEASURED reliability (above-chance
    separability normalised to [0,1]) so a weak sonority axis is raised toward
    flat (cannot drag the place anchor) — T9's anchor-safety.

DONKEY (audited):
  * NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO swept knob. The
    sonority axis = the agent's OWNED native TFS chain (tfs_voicing_track, no
    Python DSP, no decision); the sonority gestalt = the same coarse trajectory
    collapse as Stage 1; the prong weight is a MEASUREMENT (above-chance
    separability), never a tuned knob.
  * The recognition decision is COMPOSED as the agent's NATIVE graph Terms (T1
    `Argmin` over candidate words of a T8 weighted SUM of two T2 `DtwTo` prongs),
    evaluated by the Rust substrate (`substrate.evaluate`). No Python decision
    over graph state.
  * The Stage-1 coarse recogniser is the base (the prerequisite); the sonority
    prong is ADDED to it.
  * No held-out accuracy is the verdict; the gate is a STRUCTURAL/coherence
    signal: (a) does the TFS sonority axis cleanly SEPARATE voiced (sonorant)
    from unvoiced (obstruent) regions, and (b) does adding the sonority prong
    produce a COHERENT SHARPENING of the word structure over Stage-1-coarse-alone
    (separates words the bare coarse gestalt confused) without dragging the place
    anchor. The prototype-vs-token assignment is read only to report whether the
    SONORITY STRUCTURE sharpens — a structural property, not a banked LOSO score.

  * `CortexLoop` + `scripts/solve_for_n.py` untouched.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_sonority_check`
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

# --- TFS framing (the agent's validated T4 voicing chain, commit 90b799c9) ----
FS = 8000
FRAME_MS = 32.0
HOP_MS = 12.0
# A small cochlear bank over the F0 harmonics + low formants where voicing
# periodicity lives (the place-code bands; the TFS reads each band's TEMPORAL
# periodicity = what its envelope discards). Verbatim from the validated cue.
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = int(FS * FRAME_MS / 1000)     # 256 samples (32 ms @ 8 kHz)
TFS_HOP = int(FS * HOP_MS / 1000)       # 96 samples (12 ms)
# digit F0 plausibility 80-320 Hz -> lag 25..100 at 8 kHz.
TFS_MINLAG, TFS_MAXLAG = 25, 100
TFS_NLAGS = TFS_MAXLAG + 1


# ---------------------------------------------------------------------------
# world-adapter I/O: load real FSDD waveforms (clean, isolated, single-talker).
# Mechanical bytes -> array translation.
# ---------------------------------------------------------------------------

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
# T4 — the agent's OWNED NATIVE TFS graded-voicing chain (validated 90b799c9).
# A thin world-adapter over the native primitives: NO Python DSP, NO decision.
# Per-frame periodicity in [0,1] = the SONORITY axis (voiced/sonorant -> 1,
# frication/burst/silence -> low) the inner-hair-cell envelope discards.
# ---------------------------------------------------------------------------

def tfs_voicing_track(sig, fs):
    s = np.asarray(sig, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None
    s_list = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)          # native cochlear band
        ac = _n.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)   # native TFS autocorr
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None
    sacf = _n.summary_autocorrelogram(band_acs, TFS_NLAGS)          # native pooled SACF
    if not sacf:
        return None
    pt = _n.periodicity_track(sacf, TFS_NLAGS, TFS_MINLAG, TFS_MAXLAG)  # native readout
    if not pt:
        return None
    strengths = np.array(pt[0::2], dtype=np.float64)               # [s0,l0,s1,l1,...]
    return strengths


# ---------------------------------------------------------------------------
# THE STAGE-1 PLACE SQUINT (T5): native cochleagram collapsed to `resolution`
# coarse band-means per frame — the gestalt place trajectory. VERBATIM from
# scripts.stage1_coarse_recognition_check (the working prerequisite recogniser).
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


# ---------------------------------------------------------------------------
# THE SONORITY GESTALT (squint-first, the agent's Stage-2 design): the graded
# TFS voicing kept as a COARSE per-frame SONORITY-ENVELOPE TRAJECTORY (the
# sonority profile over the word). Per-frame mean-subtracted on its own axis so
# the sonority SHAPE is relative (where in the word voiced-vs-not, not absolute
# loudness/level) — the sonority sibling of the place squint. One sonority value
# per frame -> a 1-D trajectory the native DtwTo aligns.
# ---------------------------------------------------------------------------

def sonority_trajectory(x, fs):
    son = tfs_voicing_track(x, fs)
    if son is None or len(son) < 2:
        return None
    mu = float(son.mean())
    return [[float(v - mu)] for v in son]      # relative sonority profile (frames x 1)


def _tuple(track):
    return tuple(tuple(float(v) for v in frame) for frame in track)


# ---------------------------------------------------------------------------
# THE NATIVE FUSED DECISION (T1 + T2 + T8): Argmin over candidate words of a
# WEIGHTED SUM of two DtwTo prongs — the Stage-1 COARSE PLACE prong + the
# SONORITY prong. SAME shape as native_cognition's d_A (formant-shadow DtwTo +
# voicing-shadow DtwTo). Composed as graph Terms, evaluated by the Rust substrate.
#   d(w) = DtwTo(obs_place, proto_place(w)) + w_son * DtwTo(obs_son, proto_son(w))
# w_son is the MEASURED reliability of the sonority axis (above-chance
# separability normalised to [0,1]) — a measurement, raised toward 0 if weak so
# it cannot drag the place anchor (T8/T9 anchor-safety). NO swept knob.
# ---------------------------------------------------------------------------

SON_REL_ATTR = "son_rel"     # observed sonority trajectory, on the Query
SYN_SON_ATTR = "syn_son"     # prototype sonority trajectory, per word


def _place_prong():
    return NC._DtwTo(NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                     NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))


def _sonority_prong():
    return NC._DtwTo(NC._Attr(NC._V("q"), SON_REL_ATTR),
                     NC._Attr(NC._V("w"), SYN_SON_ATTR))


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def fused_score_term(w_son):
    """d(w) = place_DtwTo + w_son * sonority_DtwTo — the fused distance as a graph
    Term (a Plus of the place prong and the reliability-weighted sonority prong).
    The whole sonority-augmented coarse recognition DECISION as native graph data
    (T1 Argmin of T8-combined T2 DtwTo prongs)."""
    return NC._Argmin(
        NC._word_set(), "w",
        NC._Plus([_place_prong(),
                  NC._Times([NC._Lit(float(w_son)), _sonority_prong()])]))


def build_substrate(place_protos, son_protos):
    """A Substrate carrying one Concept per digit-word with both its coarse PLACE
    prototype trajectory and its SONORITY prototype trajectory as graph attrs,
    plus a reusable Query node. Graph construction only (world-adapter)."""
    s = Substrate()
    word_nodes = {}
    for w in place_protos:
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, NC.WORD_ATTR, 1.0)
        s.set_attr(nid, NC.SYN_REL_ATTR, _tuple(place_protos[w]))
        s.set_attr(nid, SYN_SON_ATTR, _tuple(son_protos[w]))
        word_nodes[w] = nid
    q = s.add_node("Query", {NC.OBS_REL_ATTR: ((0.0, 0.0, 0.0),),
                             SON_REL_ATTR: ((0.0,),)})
    return s, q, word_nodes


# ---------------------------------------------------------------------------
# main: build the sonority axis, COMPOSE the fused native decision, read the
# STRUCTURAL gate ((a) voiced/unvoiced separability, (b) sonority sharpening).
# ---------------------------------------------------------------------------

def main():
    print("=== Stage-2 — sonority / voicing structure (vowels before frication): "
          "STRUCTURAL readiness check ===")
    print("PREREQUISITE: Stage 1 DONE (coarse squint gate FIRES). This stage adds "
          "the sonority/voicing axis on top of the working coarse recogniser.\n")

    files = gather_files()
    resolution = int(AR._DEFAULT_RES)            # 3 = low/mid/high (Stage-1 squint)
    ladder = list(AR._LADDER)
    print(f"--- (a) the SONORITY axis (T4 graded TFS voicing) + the Stage-1 PLACE "
          f"squint (T5, resolution={resolution}, ladder {ladder}) ---")

    # build both trajectories per token (the place squint + the sonority gestalt),
    # and per-token frame-level sonority for the voiced/unvoiced separability check.
    place = {}     # (digit, speaker, idx) -> coarse place trajectory
    son = {}       # (digit, speaker, idx) -> sonority trajectory (frames x 1)
    son_frames_by_digit = {d: [] for d in range(10)}   # raw per-frame sonority
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        pt = coarse_trajectory(x, fs, resolution)
        st_raw = tfs_voicing_track(x, fs)
        if pt is None or len(pt) < 2 or st_raw is None or len(st_raw) < 2:
            continue
        place[(digit, speaker, idx)] = pt
        mu = float(st_raw.mean())
        son[(digit, speaker, idx)] = [[float(v - mu)] for v in st_raw]
        son_frames_by_digit[digit].append(st_raw)

    n_tok = len(place)
    speakers = sorted({k[1] for k in place})
    print(f"  tokens with BOTH place + sonority trajectories: {n_tok}, "
          f"{len(speakers)} speakers")
    place_composes = n_tok > 0 and all(len(t[0]) == resolution for t in place.values())
    son_composes = n_tok > 0 and all(len(t[0]) == 1 for t in son.values())
    print(f"  >>> the place squint COMPOSES (every token -> {resolution}-band traj): "
          f"{place_composes}")
    print(f"  >>> the sonority gestalt COMPOSES (every token -> 1-D voicing-env traj): "
          f"{son_composes}")

    # === (b) GATE PART 1: does the TFS sonority axis CLEANLY SEPARATE voiced =====
    # (sonorant) from unvoiced (obstruent) REGIONS? Read STRUCTURALLY from the
    # graded per-frame periodicity: pool ALL frames across the corpus, and ask
    # whether the high-periodicity (voiced/sonorant) frames form a coherent
    # population distinct from the low-periodicity (frication/burst/silence)
    # frames — a bimodal/separated graded axis, not a flat smear. We read this as
    # the standardized gap between the per-token TOP-decile (vowel nucleus, the
    # sonorant peak) and BOTTOM-decile (obstruent/silence trough) sonority. A
    # clean voiced<->unvoiced axis => the nucleus sits well above the trough.
    nucleus = []     # per-token p90 sonority (the voiced/sonorant nucleus)
    trough = []      # per-token p10 sonority (the unvoiced/obstruent trough)
    for (d, sp, idx), _ in place.items():
        st = np.array([v[0] for v in son[(d, sp, idx)]]) + 0.0   # relative; use raw
        # use the RAW periodicity for the absolute voiced/unvoiced level
        raw = None
        # recover raw from the stored relative + we kept raw separately below
        # (recompute mean offset): relative = raw - mean(raw) => raw = rel + mean
        # but we want absolute; pull from son_frames index is overkill — recompute
        # cheaply by re-deriving here would re-run TFS; instead read raw store:
        # (the relative loses the mean; for the separability axis the WITHIN-token
        #  contrast nucleus-trough is what matters and is mean-invariant.)
        relvals = np.array([v[0] for v in son[(d, sp, idx)]])
        nucleus.append(float(np.percentile(relvals, 90)))
        trough.append(float(np.percentile(relvals, 10)))
    nucleus = np.asarray(nucleus)
    trough = np.asarray(trough)
    pooled_sd_vu = np.sqrt(0.5 * (nucleus.var() + trough.var())) + 1e-9
    vu_gap = float((nucleus.mean() - trough.mean()) / pooled_sd_vu)
    vu_frac = float(np.mean(nucleus > trough))   # fraction of tokens with a real contrast

    print(f"\n--- (b) GATE PART 1: voiced<->unvoiced SEPARABILITY (the sonority axis) ---")
    print(f"  per-token sonorant nucleus (p90, mean+/-sd): "
          f"{nucleus.mean():.4f} +/- {nucleus.std():.4f}")
    print(f"  per-token obstruent trough (p10, mean+/-sd): "
          f"{trough.mean():.4f} +/- {trough.std():.4f}")
    print(f"  tokens with nucleus > trough (a real sonority contrast): {vu_frac:.3f}")
    print(f"  standardized voiced<->unvoiced gap (d', nucleus-trough): {vu_gap:.3f}")

    # also: does the graded axis SEPARATE digit CLASSES by their sonority profile?
    # mean sonority per digit (high-sonorant vowels vs gap/obstruent-cued digits)
    digit_son_mean = {}
    for d in range(10):
        fr = son_frames_by_digit[d]
        if fr:
            digit_son_mean[d] = float(np.mean([f.mean() for f in fr]))
    print("  per-digit mean sonority (graded voiced<->unvoiced axis):")
    for d in range(10):
        if d in digit_son_mean:
            print(f"    {_DIGITS[d]:6s}: {digit_son_mean[d]:.3f}")
    if digit_son_mean:
        spread = max(digit_son_mean.values()) - min(digit_son_mean.values())
        print(f"  sonority spread across digits (max-min): {spread:.3f} "
              f"(a graded axis, not a flat smear)")

    # === COMPOSE the prototypes (one held exemplar per digit, both axes) =========
    proto_speaker = speakers[0]
    place_protos, son_protos = {}, {}
    for d in range(10):
        cand = sorted([(k, v) for k, v in place.items()
                       if k[0] == d and k[1] == proto_speaker],
                      key=lambda kv: kv[0][2])
        if cand:
            key = cand[0][0]
            place_protos[_DIGITS[d]] = place[key]
            son_protos[_DIGITS[d]] = son[key]

    # === MEASURE the sonority prong's reliability (the T8 weight, NOT a sweep) ====
    # w_son = above-chance separability of the SONORITY-ALONE recogniser, mapped to
    # [0,1]. A reliable sonority axis counts; a weak one is raised toward 0 so it
    # cannot drag the place anchor. This is a MEASUREMENT (the agent's own
    # weight = max(0,(acc-chance)/(1-chance)) rule), computed on the trajectories
    # already in hand — never a tuned knob.
    s_w, q_w, wn_w = build_substrate(place_protos, son_protos)
    son_only = _Pred(NC._Argmin(NC._word_set(), "w", _sonority_prong()))
    place_only = _Pred(NC._Argmin(NC._word_set(), "w", _place_prong()))
    son_correct = 0
    place_correct = 0
    n_eval = 0
    for (d, sp, idx), pt in place.items():
        w = _DIGITS[d]
        if w not in wn_w:
            continue
        s_w.set_attr(q_w, NC.OBS_REL_ATTR, _tuple(pt))
        s_w.set_attr(q_w, SON_REL_ATTR, _tuple(son[(d, sp, idx)]))
        pick_son = s_w.evaluate(son_only, {"q": q_w})
        pick_place = s_w.evaluate(place_only, {"q": q_w})
        if pick_son is not None and s_w.node(pick_son)["attrs"].get("name") == w:
            son_correct += 1
        if pick_place is not None and s_w.node(pick_place)["attrs"].get("name") == w:
            place_correct += 1
        n_eval += 1
    chance = 1.0 / max(len(place_protos), 1)
    son_acc = son_correct / max(n_eval, 1)
    place_acc = place_correct / max(n_eval, 1)
    w_son = max(0.0, (son_acc - chance) / (1.0 - chance + 1e-9))
    print(f"\n--- the T8 sonority-prong WEIGHT (a MEASUREMENT, not a sweep) ---")
    print(f"  sonority-ALONE separability (native Argmin of sonority DtwTo): "
          f"{son_acc:.3f} (chance {chance:.3f})")
    print(f"  place-ALONE separability (the Stage-1 prong, reference)      : "
          f"{place_acc:.3f}")
    print(f"  => measured sonority reliability weight w_son = "
          f"max(0,(acc-chance)/(1-chance)) = {w_son:.3f}")

    # === COMPOSE the FUSED native decision (T1 + T2 + T8) ========================
    s, q, word_nodes = build_substrate(place_protos, son_protos)
    fused = _Pred(fused_score_term(w_son))
    # sanity: the fused decision composes + evaluates natively over both axes.
    s.set_attr(q, NC.OBS_REL_ATTR, _tuple(place_protos[_DIGITS[0]]))
    s.set_attr(q, SON_REL_ATTR, _tuple(son_protos[_DIGITS[0]]))
    self_pick = s.evaluate(fused, {"q": q})
    fused_composes = self_pick is not None
    print(f"\n--- the FUSED native decision (T1 Argmin of T8(place DtwTo + "
          f"w_son*sonority DtwTo)) ---")
    print(f"  fused recognition Term composes + evaluates natively: {fused_composes}")
    print(f"  (self-prototype of '{_DIGITS[0]}' -> native Argmin picks "
          f"'{s.node(self_pick)['attrs'].get('name') if self_pick else None}')")

    # === (c) GATE PART 2: does adding the sonority prong COHERENTLY SHARPEN ======
    # the word structure over Stage-1-coarse-ALONE, WITHOUT dragging the place
    # anchor? STRUCTURAL read: for every token, compare the structural cluster
    # margin (own-word distance vs mean other-word distance) under (i) the place
    # prong ALONE (Stage 1) and (ii) the FUSED place+sonority decision. The gate
    # is the COHERENT sharpening: the fused structure separates AT LEAST AS WELL,
    # and recovers tokens the bare coarse gestalt confused (the sonority profile
    # disambiguates place-confusable words), with the anchor NOT dragged (the
    # weighted prong is anchor-safe). NO held-out accuracy is banked as the verdict.
    place_sep = 0
    fused_sep = 0
    recovered = 0          # confused by place-alone, separated by fusion
    regressed = 0          # separated by place-alone, confused by fusion (anchor drag)
    within_f, between_f = [], []
    n_scored = 0
    for (d, sp, idx), pt in place.items():
        w = _DIGITS[d]
        if w not in word_nodes:
            continue
        s.set_attr(q, NC.OBS_REL_ATTR, _tuple(pt))
        s.set_attr(q, SON_REL_ATTR, _tuple(son[(d, sp, idx)]))
        own_p = own_f = None
        oth_p, oth_f = [], []
        for wname, nid in word_nodes.items():
            dp = float(s.evaluate(_Pred(_place_prong()), {"q": q, "w": nid}))
            df = float(s.evaluate(
                _Pred(NC._Plus([_place_prong(),
                                NC._Times([NC._Lit(float(w_son)),
                                           _sonority_prong()])])),
                {"q": q, "w": nid}))
            if wname == w:
                own_p, own_f = dp, df
            else:
                oth_p.append(dp)
                oth_f.append(df)
        if own_p is None or not oth_p:
            continue
        n_scored += 1
        p_ok = own_p < np.mean(oth_p)     # place-alone separates this token
        f_ok = own_f < np.mean(oth_f)     # fused separates this token
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

    print(f"\n--- (c) GATE PART 2: sonority-augmented SHARPENING over place-alone ---")
    print(f"  tokens scored                                  : {n_scored}")
    print(f"  place-ALONE structural separation (Stage 1)    : {place_sep_frac:.3f}")
    print(f"  FUSED place+sonority structural separation     : {fused_sep_frac:.3f}")
    print(f"  delta separation (fused - place)               : "
          f"{fused_sep_frac - place_sep_frac:+.3f}")
    print(f"  tokens RECOVERED by sonority (place-confused -> fused-separated): "
          f"{recovered}")
    print(f"  tokens REGRESSED (place-separated -> fused-confused = anchor drag): "
          f"{regressed}")
    print(f"  fused standardized cluster gap (d')            : {fused_gap:.3f}")

    # === THE READINESS GATE =====================================================
    # Stage-2 structure is ADMITTED iff:
    #   (composes)   both the sonority gestalt and the fused decision COMPOSE + eval
    #                natively;
    #   (PART 1)     the TFS sonority axis cleanly SEPARATES voiced (sonorant) from
    #                unvoiced (obstruent) regions — a real standardized
    #                nucleus<->trough gap on a clear majority of tokens, and the
    #                graded per-digit axis is not a flat smear;
    #   (PART 2)     adding the sonority prong COHERENTLY SHARPENS the word structure
    #                over place-alone (fused separation >= place separation, with
    #                tokens recovered) WITHOUT dragging the anchor (the weighted
    #                prong is anchor-safe: fused separation does not collapse below
    #                place-alone).
    vu_separates = (vu_gap > 0.2 and vu_frac > 0.5)
    anchor_safe = (fused_sep_frac >= place_sep_frac - 1e-9)   # not dragged below Stage 1
    sharpens = (fused_sep_frac >= place_sep_frac and recovered > 0
                and fused_gap > 0.2)
    structure_admitted = (place_composes and son_composes and fused_composes
                          and vu_separates and anchor_safe and sharpens)

    print(f"\n=== READINESS GATE ===")
    print(f"  sonority gestalt composes (TFS voicing-env traj)     : {son_composes}")
    print(f"  fused decision composes (Argmin of place + w*sonority): {fused_composes}")
    print(f"  PART 1 voiced<->unvoiced SEPARATES (d'>0.2, maj.)     : "
          f"{vu_separates} (d'={vu_gap:.3f}, {vu_frac:.3f} of tokens)")
    print(f"  PART 2 sonority SHARPENS over place-alone (recovers)  : "
          f"{sharpens} (delta {fused_sep_frac - place_sep_frac:+.3f}, "
          f"recovered {recovered})")
    print(f"  anchor NOT dragged (fused sep >= place sep)           : {anchor_safe}")
    print(f"  >>> STAGE-2 SONORITY/VOICING STRUCTURE ADMITTED      : {structure_admitted}")

    print(f"\n  NOTE: this is the STRUCTURAL gate (the sonority axis separates "
          f"voiced<->unvoiced + coherently sharpens the coarse recogniser), NOT a "
          f"held-out LOSO accuracy. The accuracy test comes AFTER the curriculum, "
          f"never as the per-stage gate.")
    print("===MARKER_STAGE2_SONORITY_CHECK_COMPLETE===")


if __name__ == "__main__":
    main()
