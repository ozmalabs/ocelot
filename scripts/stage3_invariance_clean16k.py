"""STAGE 3 — SPEAKER INVARIANCE (the dynamic gesture), CLEAN 16 kHz.

The agent executes STAGE 3 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"speaker invariance —
the VTL-invariant formant ratio AND the order-N-over-time coarticulatory gesture
(shared across speakers even when absolute formants differ)."* Acting on its own
ordering principle 1 (`lack_of_invariance` is THE central problem) + its derived
tools, NOT a hand-authored plan.

THE PREREQUISITE (commit 5ff04a2e). Stage 1's coarse squint separated 71.8 % of
the clean-16k tokens but its standardized cross-speaker cluster gap shrank to
d'=0.096 under the 30-speaker diversity (5x FSDD). The squint's coarse band-mean
trajectory drifts with the speaker (vocal-tract length scales the spectrum). Stage
3 = swap in a SPEAKER-INVARIANT representation so the SAME word admits the SAME
structure across the 30 speakers, RAISING that cross-speaker d' above 0.096.

WHAT THE AGENT COMPOSES (its OWN owned tools, no new code):
  * SPEAKER NORMALISATION (the VTL invariant the agent derived, memory
    ozma_speaker_normalization): per-frame log-formants F_i - mean(F1,F2,F3).
    Vocal-tract length scales all formants multiplicatively == an additive shift
    in log-Hz; subtracting the per-frame log-formant mean CANCELS it. So the
    LEVEL of the representation is already speaker-(VTL)-invariant by construction.
  * the DYNAMIC GESTURE (T7 order-N-over-time): the order-1 difference of the
    VTL-normalised log-formant track == how the formants MOVE (the coarticulatory
    transition). The articulatory gesture is the SAME motion in every mouth, only
    scaled; the order-1 difference is speaker-stable (and removes any residual
    per-utterance constant offset). Both live in `AF.vtl_formant_track` (the
    agent's owned `_native_lpc_roots_formants` Levinson-Durbin chain + the VTL
    invariant + the appended order-1 velocity channels).
  * the SAME native decision the Stage-1 gate used: T2 `DtwTo` trajectory
    alignment (absorbs the gesture-timing warp across speakers), evaluated by the
    Rust substrate (`substrate.evaluate`). NOT a re-implemented Python distance.

DONKEY (audited): NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO swept
knob. The invariant representation is the agent's owned VTL-normalisation +
order-N gesture; the decision is the native graph `DtwTo`. The readiness gate is
the STRUCTURAL cross-speaker cluster gap d' (within-word-cross-speaker vs
between-word DtwTo), read against the Stage-1 0.096 — NOT a held-out LOSO accuracy.
CortexLoop / solve_for_n / runners untouched. 16 kHz NOT downsampled.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage3_invariance_clean16k`
"""
from __future__ import annotations

import numpy as np

import domains.agent_frontend as AF
import domains.native_cognition as NC
import domains.acoustic_resolution as AR
from substrate_rs import Substrate
from scripts.clean16k_corpus import DIGITS as _DIGITS, load_wav, select_corpus

# the SAME structural builders the Stage-1 clean16k gate used, VERBATIM.
from scripts.stage1_coarse_recognition_check import (
    coarse_trajectory, _tuple, build_coarse_substrate, coarse_predict_term, _Pred,
)


# ---------------------------------------------------------------------------
# the Stage-3 SPEAKER-INVARIANT representation: the agent's owned
# VTL-normalised log-formant trajectory (speaker normalisation) WITH the
# appended order-1 velocity (the dynamic gesture). This is exactly
# AF.vtl_formant_track(with_velocity=True) — the agent's owned feature.
# ---------------------------------------------------------------------------

def invariant_trajectory(x, fs, n_formants=3):
    """The speaker-invariant trajectory: per-frame [F1-mean .. F3-mean | velocity]
    in log-Hz (VTL normalisation + the order-1 dynamic gesture). The agent's owned
    `vtl_formant_track`; pure boundary DSP (Levinson-Durbin + VTL invariant + the
    order-1 motion channels), NO fit."""
    tr = AF.vtl_formant_track(x, fs, {"n_formants": n_formants, "with_velocity": True})
    if not tr or len(tr) < 2:
        return None
    return [[float(v) for v in frame] for frame in tr]


def gesture_only_trajectory(x, fs, n_formants=3):
    """The DYNAMIC GESTURE alone (the velocity channels only) — the order-1
    over-time of the VTL-normalised log-formant track, the pure motion descriptor
    (the most speaker-stable part: the order-1 difference also removes any residual
    per-utterance constant). Used to report the gesture's own separation."""
    tr = AF.vtl_formant_track(x, fs, {"n_formants": n_formants, "with_velocity": True})
    if not tr or len(tr) < 2:
        return None
    return [[float(v) for v in frame[n_formants:]] for frame in tr]


# ---------------------------------------------------------------------------
# the SAME structural metric the Stage-1 gate read, but measured CROSS-SPEAKER:
# the within-word distances are between DIFFERENT speakers' tokens of the same
# word (prototype = held-out speakers, observation = every other speaker), so the
# within-word cross-speaker scatter is genuinely the speaker-variance the
# invariant must shrink. Returns the d' (standardized cluster gap), the
# within/between means, the separation fraction, and the residual speaker variance.
# ---------------------------------------------------------------------------

def _build_substrate(prototypes):
    s = Substrate()
    word_nodes = {}
    for w, traj in prototypes.items():
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, NC.WORD_ATTR, 1.0)
        s.set_attr(nid, NC.SYN_REL_ATTR, _tuple(traj))
        word_nodes[w] = nid
    q = s.add_node("Query", {NC.OBS_REL_ATTR: _tuple(prototypes[next(iter(prototypes))])})
    return s, q, word_nodes


def _dtw(s, q, nid):
    return float(s.evaluate(_Pred(NC._DtwTo(
        NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
        NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": q, "w": nid}))


def cross_speaker_structure(trajs, label, n_proto_speakers=3):
    """Cross-speaker within-word vs between-word DtwTo cluster gap d'.

    For each digit a CROSS-SPEAKER prototype is the MEDOID trajectory taken from a
    fixed held set of `n_proto_speakers` (chosen deterministically, the top
    speakers by coverage). Every token from EVERY OTHER speaker is scored against
    all 10 digit prototypes: within-word = distance to its own digit's prototype
    (a DIFFERENT speaker), between-word = mean distance to the other digits. The
    standardized gap d' = (between.mean - within.mean) / pooled_sd is the SAME
    structural metric the Stage-1 gate read (cf 0.096). Also reports the residual
    within-word cross-speaker variance (the speaker scatter the invariant leaves).
    """
    speakers = sorted({k[1] for k in trajs})
    proto_speakers = set(speakers[:n_proto_speakers])

    # cross-speaker prototype per digit = the MEDOID over the proto-speaker pool
    # (the token with min total DtwTo to the others — a robust central exemplar,
    # NOT a fitted/averaged template; pure selection, no learned parameter).
    prototypes = {}
    for d in range(10):
        pool = [v for k, v in trajs.items()
                if k[0] == d and k[1] in proto_speakers]
        if len(pool) < 1:
            continue
        if len(pool) == 1:
            prototypes[_DIGITS[d]] = pool[0]
            continue
        # medoid via the native DtwTo (build a tiny substrate over the pool)
        sp = Substrate()
        nodes = []
        for v in pool:
            nid = sp.add_node("Concept", {})
            sp.set_attr(nid, NC.SYN_REL_ATTR, _tuple(v))
            nodes.append((nid, v))
        qd = sp.add_node("Query", {NC.OBS_REL_ATTR: _tuple(pool[0])})
        best_v, best_tot = pool[0], None
        for v in pool:
            sp.set_attr(qd, NC.OBS_REL_ATTR, _tuple(v))
            tot = 0.0
            for nid, _ in nodes:
                tot += float(sp.evaluate(_Pred(NC._DtwTo(
                    NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                    NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": qd, "w": nid}))
            if best_tot is None or tot < best_tot:
                best_tot, best_v = tot, v
        prototypes[_DIGITS[d]] = best_v

    s, q, word_nodes = _build_substrate(prototypes)

    within, between = [], []
    sep_ok = sep_tot = 0
    # group within-word distances by speaker to quantify residual speaker variance
    within_by_speaker = {}
    for (d, sp_id, idx), t in trajs.items():
        if sp_id in proto_speakers:           # held-out: score only NON-proto speakers
            continue
        w = _DIGITS[d]
        if w not in word_nodes:
            continue
        s.set_attr(q, NC.OBS_REL_ATTR, _tuple(t))
        own, others = None, []
        for wname, nid in word_nodes.items():
            dist = _dtw(s, q, nid)
            if wname == w:
                own = dist
            else:
                others.append(dist)
        if own is None or not others:
            continue
        within.append(own)
        between.append(float(np.mean(others)))
        within_by_speaker.setdefault(sp_id, []).append(own)
        sep_tot += 1
        if own < np.mean(others):
            sep_ok += 1

    within = np.asarray(within)
    between = np.asarray(between)
    sep_frac = sep_ok / sep_tot if sep_tot else 0.0
    pooled_sd = np.sqrt(0.5 * (within.var() + between.var())) + 1e-9
    dprime = float((between.mean() - within.mean()) / pooled_sd)

    # residual speaker variance: variance of the per-speaker MEAN within-word
    # distance (how much the cross-speaker within-word distance still depends on
    # which speaker) as a fraction of the overall within-word variance. Lower =>
    # the representation has removed more speaker dependence.
    sp_means = np.asarray([np.mean(v) for v in within_by_speaker.values()])
    between_speaker_var = float(sp_means.var()) if sp_means.size > 1 else 0.0
    total_within_var = float(within.var()) + 1e-12
    residual_speaker_frac = between_speaker_var / total_within_var

    print(f"\n--- cross-speaker structure: {label} ---")
    print(f"  proto speakers (held)                 : {sorted(proto_speakers)} "
          f"({n_proto_speakers}); scored speakers: {len(speakers) - n_proto_speakers}")
    print(f"  tokens scored (cross-speaker)         : {sep_tot}")
    print(f"  within-word CROSS-SPEAKER DtwTo (m+/-sd): "
          f"{within.mean():.4f} +/- {within.std():.4f}")
    print(f"  between-word DtwTo               (m+/-sd): "
          f"{between.mean():.4f} +/- {between.std():.4f}")
    print(f"  structural separation (within<between): {sep_frac:.3f} of tokens")
    print(f"  >>> standardized cross-speaker cluster gap d' = {dprime:.3f}")
    print(f"  residual speaker variance (frac of within-var): {residual_speaker_frac:.3f} "
          f"(lower = more speaker-dependence removed)")
    return {
        "dprime": dprime, "sep_frac": sep_frac,
        "within_mean": float(within.mean()), "between_mean": float(between.mean()),
        "within_sd": float(within.std()),
        "residual_speaker_frac": residual_speaker_frac, "n": sep_tot,
    }


def main():
    print("=== STAGE 3 — SPEAKER INVARIANCE (the dynamic gesture), CLEAN 16 kHz ===")
    print("    prerequisite (5ff04a2e): Stage-1 coarse squint cross-speaker d'=0.096")
    print("    Stage 3 = a speaker-invariant representation that RAISES that gap.\n")

    files, speakers_all = select_corpus()
    x0, fs0 = load_wav(files[0][0])
    print(f"corpus: clean 16 kHz Speech Commands digits, {len(files)} tokens, "
          f"{len(speakers_all)} speakers (fs0={fs0})")

    # --- (a) Stage-0/1 hand-off: the owned native formant chain feeds the cues ----
    seg = x0[len(x0) // 2 - 200: len(x0) // 2 + 200]
    nat_f = AF._native_lpc_roots_formants(seg, fs0, int(fs0 / 1000) + 2)
    track = AF.vtl_formant_track(x0, fs0, {"n_formants": 3, "with_velocity": True})
    handoff = len(nat_f) > 0 and len(track) > 0 and len(track[0]) == 6
    print("\n--- (a) hand-off: VTL-normalised formant TRACK + dynamic gesture compose ---")
    print(f"  native lpc_roots_formants (Hz, mid)   : {[round(v,1) for v in nat_f]}")
    print(f"  vtl_formant_track frames x channels   : {len(track)} x "
          f"{len(track[0]) if track else 0}  ([F1-mean..F3-mean | velocity])")
    print(f"  >>> speaker-invariant representation COMPOSES: {handoff}")

    # --- (b) build BOTH representations on the SAME corpus -----------------------
    resolution = int(AR._DEFAULT_RES)
    coarse, invar, gesture = {}, {}, {}
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        ct = coarse_trajectory(x, fs, resolution)        # Stage-1 baseline squint
        it = invariant_trajectory(x, fs)                 # VTL-norm + dynamic gesture
        gt = gesture_only_trajectory(x, fs)              # the gesture (velocity) alone
        key = (digit, speaker, idx)
        if ct is not None and len(ct) >= 2:
            coarse[key] = ct
        if it is not None and len(it) >= 2:
            invar[key] = it
        if gt is not None and len(gt) >= 2:
            gesture[key] = gt
    print(f"\n--- (b) representations built on the SAME corpus ---")
    print(f"  coarse squint (Stage-1 baseline)      : {len(coarse)} tokens "
          f"({resolution}-band/frame)")
    print(f"  VTL-norm + dynamic gesture (Stage-3)  : {len(invar)} tokens "
          f"(6 chan/frame)")
    print(f"  dynamic gesture alone (velocity)      : {len(gesture)} tokens "
          f"(3 chan/frame)")

    # --- (c) the SAME structural metric, CROSS-SPEAKER, on each representation ----
    print(f"\n=== (c) THE STRUCTURAL CROSS-SPEAKER CLUSTER GAP (NOT a held-out accuracy) ===")
    base = cross_speaker_structure(coarse, "Stage-1 COARSE SQUINT (baseline)")
    inv = cross_speaker_structure(invar, "Stage-3 VTL-NORM + DYNAMIC GESTURE")
    ges = cross_speaker_structure(gesture, "Stage-3 DYNAMIC GESTURE alone (velocity)")

    # --- (d) THE READINESS GATE: does the invariant RAISE the cross-speaker d'? ---
    raised = inv["dprime"] > base["dprime"]
    above_stage1 = inv["dprime"] > 0.096
    speaker_var_removed = base["residual_speaker_frac"] - inv["residual_speaker_frac"]
    # the structural gate: the speaker-invariant representation makes the SAME word
    # admit the SAME structure across speakers more than the coarse squint did, i.e.
    # the cross-speaker cluster gap rises above the Stage-1-coarse 0.096.
    gate = handoff and raised and above_stage1

    print(f"\n=== READINESS GATE (STRUCTURAL cross-speaker invariance) ===")
    print(f"  speaker-invariant representation composes        : {handoff}")
    print(f"  Stage-1 coarse cross-speaker d'                  : {base['dprime']:.3f}  "
          f"(reference 0.096)")
    print(f"  Stage-3 invariant cross-speaker d'               : {inv['dprime']:.3f}")
    print(f"  Stage-3 gesture-alone cross-speaker d'           : {ges['dprime']:.3f}")
    print(f"  d' RAISED by the invariant (vs coarse)           : {raised} "
          f"(+{inv['dprime'] - base['dprime']:.3f})")
    print(f"  d' above the Stage-1-coarse 0.096                : {above_stage1}")
    print(f"  residual speaker variance: coarse {base['residual_speaker_frac']:.3f} "
          f"-> invariant {inv['residual_speaker_frac']:.3f}  "
          f"(removed {speaker_var_removed:+.3f})")
    print(f"  within-word cross-speaker scatter: coarse {base['within_sd']:.4f} "
          f"-> invariant {inv['within_sd']:.4f}")
    print(f"\n  >>> STAGE-3 SPEAKER-INVARIANCE STRUCTURE ADMITTED (clean 16 kHz): {gate}")
    print("===MARKER_STAGE3_INVARIANCE_CLEAN16K_COMPLETE===")


if __name__ == "__main__":
    main()
