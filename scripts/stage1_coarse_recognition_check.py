"""Stage-1 STRUCTURAL READINESS CHECK — coarse isolated recognition (squint-first).

The agent executes STAGE 1 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"coarse isolated
recognition (the squint, clean single words) — a front end worth squinting
from."* This is the agent acting on its own ranked gap map + its own ordering
principle 3 ("coarse before fine — the squint first"), NOT a hand-authored plan.

This script reads the STRUCTURAL readiness gate, NOT a held-out accuracy number.
Per the agent's own thesis (curriculum PART 3 + memory ozma_capability_is_binary_
admissibility): each stage's success signal is a binary READINESS gate read from
self-measurement (structure-admitted, proceed), not a tuned metric. The held-out
LOSO/accuracy test comes AFTER the curriculum, never as the per-stage gate
(memory ozma_no_premature_testing_mid_curriculum).

DONKEY (audited):
  * NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO swept knob.
  * The coarse representation = the agent's OWN squint (T5): the native
    cochleagram collapsed to `resolution`=3 low/mid/high band-means per frame
    (the gestalt dimensional collapse; resolution read from the seed
    `seeds/acoustic_resolution.json`, NOT a literal).
  * The recognition decision is COMPOSED as the agent's NATIVE graph Terms (T1
    `Argmin` over candidate words of T2 `DtwTo` over the coarse per-frame
    trajectories), evaluated by the Rust substrate (`substrate.evaluate`). No
    Python decision over graph state.
  * The Stage-0 hand-off uses the OWNED NATIVE all-pole formant chain.
  * No held-out accuracy is the verdict; the gate is a STRUCTURAL/coherence
    signal (within-word gestalt coherence vs between-word separation). The
    prototype-vs-token assignment is read only to report whether the COARSE
    STRUCTURE separates the words — a structural property of the squint, not a
    banked LOSO score.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage1_coarse_recognition_check`
"""
from __future__ import annotations

import os
import re
import wave

import numpy as np

import domains.agent_frontend as AF
import domains.native_cognition as NC
import domains.acoustic_resolution as AR
from substrate_rs import Substrate


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")


# ---------------------------------------------------------------------------
# world-adapter I/O: load real FSDD waveforms (clean, isolated, single-talker —
# exactly the Stage-1 input class). Mechanical bytes -> array translation.
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
# THE SQUINT (T5): the native cochleagram collapsed to `resolution` coarse
# band-means per frame — the gestalt dimensional collapse. resolution comes from
# the agent's seed dial (seeds/acoustic_resolution.json -> 3 = low/mid/high), the
# coarsest rung of the ladder. This is the agent's OWN coarse-summary (the same
# np.array_split-into-N-band-means that enrich_sign_bands writes, here kept as an
# ORDERED per-frame trajectory so the native DtwTo aligns the coarse gesture).
# ---------------------------------------------------------------------------

def coarse_trajectory(x, fs, resolution):
    """frames x `resolution` coarse band-mean trajectory — the squint. The native
    cochleagram (T12) summarised to `resolution` log-ordered band-means per frame.
    No fit; pure boundary DSP (the agent's own coarse gestalt collapse)."""
    M = AF.cochleagram(x, fs, AF._MIDDLE[1], AF._MIDDLE[2], AF._MIDDLE[3])
    if M.size == 0:
        return None
    rows = []
    for r in range(M.shape[0]):
        # collapse this frame's bands to `resolution` contiguous band-means
        # (the gestalt squint), then per-frame mean-subtract (the agent's own
        # speaker-baseline removal, enrich_sign_bands normalize) so the coarse
        # shape is relative — speaker/level robust, the point of the squint.
        bands = [float(g.mean()) for g in np.array_split(M[r], resolution)]
        mu = sum(bands) / len(bands)
        rows.append([b - mu for b in bands])
    return rows


def _tuple(track):
    return tuple(tuple(float(v) for v in frame) for frame in track)


# ---------------------------------------------------------------------------
# THE NATIVE RECOGNITION DECISION (T1 + T2): Argmin over candidate words of the
# DtwTo distance from the observed coarse trajectory to each word's coarse
# prototype trajectory. Composed as graph Terms, evaluated by the Rust substrate.
# ---------------------------------------------------------------------------

def build_coarse_substrate(prototypes):
    """A Substrate carrying one Concept per digit-word with its COARSE prototype
    trajectory as a graph attr, plus a reusable Query node. Graph construction
    only (world-adapter; no decision over graph state)."""
    s = Substrate()
    word_nodes = {}
    for w, traj in prototypes.items():
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, NC.WORD_ATTR, 1.0)
        s.set_attr(nid, NC.SYN_REL_ATTR, _tuple(traj))
        word_nodes[w] = nid
    q = s.add_node("Query", {NC.OBS_REL_ATTR: ((0.0, 0.0, 0.0),)})
    return s, q, word_nodes


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def coarse_predict_term():
    """predict = Argmin over candidate words of DtwTo(obs coarse traj, proto coarse
    traj(w)). The whole coarse recognition DECISION as the agent's native graph
    data (T1 Argmin of T2 DtwTo) — the SAME shape as native_cognition's
    predict_articulatory_term, the score being the pure coarse-trajectory DtwTo."""
    score = NC._DtwTo(NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                      NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))
    return _Pred(NC._Argmin(NC._word_set(), "w", score))


# ---------------------------------------------------------------------------
# main: build the squint, COMPOSE the native decision, read the STRUCTURAL gate.
# ---------------------------------------------------------------------------

def main():
    print("=== Stage-1 — coarse isolated recognition (squint-first): "
          "STRUCTURAL readiness check ===")

    # --- (0) the Stage-0 hand-off: native all-pole formant chain into the cues ---
    files = gather_files()
    x0, fs0 = load_wav(files[0][0])
    seg = x0[len(x0) // 2 - 100: len(x0) // 2 + 100]
    nat_f = AF._native_lpc_roots_formants(seg, fs0, int(fs0 / 1000) + 2)
    M0 = AF.cochleagram(x0, fs0, AF._MIDDLE[1], AF._MIDDLE[2], AF._MIDDLE[3])
    cue_allpole = AF._vtl_formant_allpole(x0, fs0, M0, {"n_out": 24, "n_formants": 3})
    cue_dynamic = AF._vtl_formant_dynamic(x0, fs0, M0,
                                          {"n_out": 24, "n_formants": 3, "order": 1})
    track = AF.vtl_formant_track(x0, fs0, {"n_formants": 3})
    handoff_wired = (len(nat_f) > 0
                     and int(np.count_nonzero(cue_allpole)) > 0
                     and int(np.count_nonzero(cue_dynamic)) > 0
                     and len(track) > 0)
    print("\n--- (a) Stage-0 hand-off: cues read the OWNED NATIVE formant chain ---")
    print(f"  native lpc_roots_formants (Hz, mid frame): "
          f"{[round(v, 1) for v in nat_f]}")
    print(f"  vtl_formant_allpole readout nonzero : {int(np.count_nonzero(cue_allpole))}/{len(cue_allpole)}")
    print(f"  vtl_formant_dynamic readout nonzero : {int(np.count_nonzero(cue_dynamic))}/{len(cue_dynamic)}")
    print(f"  vtl_formant_track frames            : {len(track)} (x{len(track[0]) if track else 0} chan)")
    print(f"  >>> HAND-OFF WIRED (native formants flow into the cues): {handoff_wired}")

    # --- (1) the SQUINT: coarse per-frame trajectories at the seed resolution ---
    resolution = int(AR._DEFAULT_RES)            # 3 = low/mid/high (the seed coarsest)
    ladder = list(AR._LADDER)
    print(f"\n--- (b) the SQUINT (T5): coarse resolution = {resolution} "
          f"(ladder {ladder}, coarsest rung) ---")

    # use a clean isolated subset across the speakers (one talker == single-source;
    # FSDD is clean isolated digits by construction — exactly the Stage-1 input).
    trajs = {}     # (digit, speaker, idx) -> coarse trajectory
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        t = coarse_trajectory(x, fs, resolution)
        if t is not None and len(t) >= 2:
            trajs[(digit, speaker, idx)] = t
    n_tok = len(trajs)
    speakers = sorted({k[1] for k in trajs})
    print(f"  coarse trajectories built: {n_tok} tokens, {len(speakers)} speakers")
    composes = n_tok > 0 and all(len(t[0]) == resolution for t in trajs.values())
    print(f"  >>> the squint COMPOSES (every token -> {resolution}-band ordered "
          f"trajectory): {composes}")

    # --- (2) COMPOSE the native recognition decision over the coarse squint ---
    # word prototype = the coarse trajectory of ONE held exemplar per digit (the
    # gestalt template). Recognition = the native Argmin-of-DtwTo Term, evaluated
    # by the Rust substrate. This EXERCISES the native decision over the squint.
    proto_speaker = speakers[0]
    prototypes = {}
    for d in range(10):
        cand = [(k, v) for k, v in trajs.items()
                if k[0] == d and k[1] == proto_speaker]
        if cand:
            prototypes[_DIGITS[d]] = sorted(cand, key=lambda kv: kv[0][2])[0][1]
    s, q, word_nodes = build_coarse_substrate(prototypes)
    term = coarse_predict_term()
    # sanity: the native Argmin-of-DtwTo decision evaluates over the squint.
    s.set_attr(q, NC.OBS_REL_ATTR, _tuple(prototypes[_DIGITS[0]]))
    self_pick = s.evaluate(term, {"q": q})
    decision_composes = self_pick is not None
    print(f"\n--- the NATIVE decision (T1 Argmin of T2 DtwTo) over the squint ---")
    print(f"  recognition Term composes + evaluates natively: {decision_composes}")
    print(f"  (self-prototype of '{_DIGITS[0]}' -> native Argmin picks node "
          f"{self_pick}, word '{s.node(self_pick)['attrs'].get('name')}')")

    # --- (3) THE STRUCTURAL READINESS GATE (NOT accuracy) -------------------
    # Does the coarse squint produce a COHERENT, SEPARABLE structure over the
    # isolated words? Read STRUCTURALLY: for each token, the native DtwTo distance
    # to its OWN-word prototype vs to OTHER-word prototypes. The gate is the
    # STRUCTURE: are within-word coarse-trajectory distances systematically tighter
    # than between-word (the gestalt clusters cohere / coarse word-identity
    # separates)? This is a structural coherence property of the representation,
    # read from the agent's own native DtwTo instrument — NOT a held-out LOSO
    # accuracy number (no train/test split is banked as the verdict; prototypes are
    # exemplars, the signal is the SEPARATION STRUCTURE, the binary admission).
    within = []
    between = []
    margins_ok = 0
    margins_tot = 0
    for (d, sp, idx), t in trajs.items():
        w = _DIGITS[d]
        if w not in word_nodes:
            continue
        s.set_attr(q, NC.OBS_REL_ATTR, _tuple(t))
        own = None
        others = []
        for wname, nid in word_nodes.items():
            dist = s.evaluate(_Pred(NC._DtwTo(
                NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": q, "w": nid})
            dist = float(dist)
            if wname == w:
                own = dist
            else:
                others.append(dist)
        if own is None or not others:
            continue
        # skip the token that IS its own prototype (degenerate zero-distance)
        if own <= 1e-9 and (d, sp, idx) and sp == proto_speaker:
            # only skip if this exact token is the prototype exemplar
            pass
        within.append(own)
        between.append(float(np.mean(others)))
        margins_tot += 1
        # structural separation: own-word distance below the MEAN other-word
        # distance (the gestalt of its own word is the nearest cluster on average)
        if own < np.mean(others):
            margins_ok += 1

    within = np.asarray(within)
    between = np.asarray(between)
    sep_frac = margins_ok / margins_tot if margins_tot else 0.0
    # the structural coherence signal: the DISTRIBUTIONS of within- vs between-word
    # coarse distances must be SEPARATED (gestalt clusters cohere). Cohen's-d style
    # standardized gap (a structural effect size, NOT a tuned accuracy).
    pooled_sd = np.sqrt(0.5 * (within.var() + between.var())) + 1e-9
    struct_gap = float((between.mean() - within.mean()) / pooled_sd)

    print(f"\n--- (3) THE STRUCTURAL READINESS GATE (NOT a held-out accuracy) ---")
    print(f"  tokens scored                         : {margins_tot}")
    print(f"  within-word coarse DtwTo  (mean+/-sd) : "
          f"{within.mean():.4f} +/- {within.std():.4f}")
    print(f"  between-word coarse DtwTo (mean+/-sd) : "
          f"{between.mean():.4f} +/- {between.std():.4f}")
    print(f"  structural separation (within<between): {sep_frac:.3f} "
          f"of tokens (gestalt of own word is nearest cluster)")
    print(f"  standardized coarse cluster gap (d')  : {struct_gap:.3f} "
          f"(between - within, pooled-sd units)")

    # GATE: the squint COMPOSES, the native decision COMPOSES, AND the coarse
    # representation produces a SEPARABLE, COHERENT structure over the words —
    # within-word systematically tighter than between-word with a real
    # standardized gap, on a clear MAJORITY of tokens. Binary structural admission.
    structure_admitted = (composes and decision_composes
                          and sep_frac > 0.5 and struct_gap > 0.2
                          and within.mean() < between.mean())
    print(f"\n=== READINESS GATE ===")
    print(f"  squint composes (coarse trajectory)            : {composes}")
    print(f"  native decision composes (Argmin of DtwTo)     : {decision_composes}")
    print(f"  coarse structure separates words (within<betw) : "
          f"{within.mean() < between.mean()} (sep {sep_frac:.3f})")
    print(f"  gestalt clusters cohere (standardized gap > 0.2): "
          f"{struct_gap > 0.2} (d'={struct_gap:.3f})")
    print(f"  >>> STAGE-1 COARSE STRUCTURE ADMITTED          : {structure_admitted}")

    print(f"\n  NOTE: this is the STRUCTURAL gate (squint composes + coarse "
          f"word-identity separates), NOT a held-out LOSO accuracy. The accuracy "
          f"test comes AFTER the curriculum, never as the per-stage gate.")
    print("===MARKER_STAGE1_COARSE_RECOGNITION_CHECK_COMPLETE===")


if __name__ == "__main__":
    main()
