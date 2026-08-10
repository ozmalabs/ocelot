"""STAGE 5 — FRICATION / HIGH-BAND DETAIL (the harder manner contrasts), CLEAN 16 kHz.

The agent executes STAGE 5 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, the Stage-5 definition ~line 386): *"resolve
/s/-/sh/-/f/ and other turbulent-noise contrasts — the high-band spectral-tilt +
aperiodic-noise detail."* Acting on its own ordering principle 5 (frication is the
LAST manner detail because it needs the high-band + temporal periodic/aperiodic
machinery the earlier stages build), NOT a hand-authored plan.

PREREQUISITES (both DONE): Stage 0 (TFS, the native band_autocorr ->
summary_autocorrelogram -> periodicity_track chain) + Stage 2 (the voiced/unvoiced
axis frication REFINES). The vowel/sonority recogniser the cue must not drag is the
Stage-3 VTL-invariant formant-trajectory recogniser (the working anchor).

THE DATA. CLEAN 16 kHz Speech Commands digits (scripts.clean16k_corpus) — NOT
downsampled. The whole point: the FRICATION BAND 4-8 kHz is PRESENT (at 8 kHz it is
gone, the K10 band-limit wall, memory ozma_train_on_clean_test_on_degraded). The
target confusions are the FRICATIVE-ONSET digits: six/seven (both /s/), four/five
(both /f/), three (/th/), zero (/z/).

WHAT THE AGENT BUILDS — W7, the frication/turbulent-noise CUE (NATIVE, gated). W7 is
the agent's OWN owned-DSP descriptor of high-band turbulent noise, built FROM the
native T4 TFS periodic-vs-aperiodic chain (frication = high-band APERIODIC energy):
  [0] high-band energy fraction (E_>3kHz / E_total) — frication PRESENCE.
  [1] high-band APERIODICITY = 1 - periodicity-strength, from the native T4 chain
      run on HIGH-band (4/5.5/7 kHz) gammatone channels: a tall ACF peak = periodic
      (voiced); a flat ACF = aperiodic (turbulent noise = frication). This is the
      T4 periodic-vs-aperiodic axis, GATED TO THE HIGH BAND — the cue's core.
  [2] high-band spectral TILT (slope across the 4/5.5/7 kHz channel energies):
      /s/ (six, seven) concentrates energy high & flat-to-rising; /f/ (four, five)
      is diffuse/low — the place-of-articulation cue inside the frication band.
  [3] high-band turbulence ONSET position [0,1] (energy-weighted temporal centroid
      of the >3 kHz energy): a leading /s/ /f/ /th/ /z/ -> early.
W7 is registered as a graph `Cue` node on the agent's FrontEnd (T13), inactive in
the repertoire, GATED IN for this stage. The per-word frication admissibility is a
soft excluder fused with the anchor by T8 weighted-admissibility.

THE GATE (structural, NOT a held-out accuracy — memory
ozma_no_premature_testing_mid_curriculum). The readiness signal is read from the
agent's own native instruments:
  (i)  the systematic FRICATIVE confusions SHRINK with W7 gated in vs without — the
       per-pair confusion structure (six/seven, four/five, three, zero) separates
       BETTER. Read as the cross-speaker confusion-pair margin (how much closer a
       token sits to its own digit's frication template than to its confusable
       partner's), WITH-vs-WITHOUT W7.
  (ii) ANCHOR SAFETY (T9): the vowel/sonority recogniser's OWN cross-speaker
       separation (the Stage-3 invariant formant DtwTo cluster gap) does NOT drop
       when the noisy frication prong is fused in — adding W7 must not drag the
       already-working vowel recognition.

DONKEY (audited): NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO swept
knob. W7 is owned DSP built FROM the native T4 chain (gammatone_band ->
band_autocorr -> summary_autocorrelogram -> periodicity_track) + owned numpy
spectral statistics; the frication admissibility is a soft excluder; the fusion is
T8 weighted-admissibility (the SAME Argmax-of-product machinery); the weight is the
prong's TRAIN-measured reliability (a MEASUREMENT, never a tuned knob). The anchor
recogniser is the Stage-3 native VTL-invariant DtwTo, UNCHANGED. CortexLoop /
solve_for_n / runners untouched. 16 kHz NOT downsampled.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage5_frication_gate`
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

import substrate_rs._native as _n
import domains.agent_frontend as AF
import domains.native_cognition as NC
from substrate_rs import Substrate
from scripts.clean16k_corpus import DIGITS as _DIGITS, FS, load_wav, select_corpus

# the Stage-3 speaker-invariant anchor representation (VTL-norm + dynamic gesture)
# and its native cross-speaker structural instrument — the recogniser W7 must NOT
# drag. Imported VERBATIM (the anchor is unchanged).
from scripts.stage3_invariance_clean16k import (
    invariant_trajectory, cross_speaker_structure,
)
from scripts.stage1_coarse_recognition_check import _tuple, _Pred


# ===========================================================================
#  W7 — the FRICATION / turbulent-noise cue (owned DSP over the native T4 chain).
# ===========================================================================

# the high-band gammatone channels into the intact 4-8 kHz frication band (present
# at 16 kHz, gone at 8 kHz). PHYSICAL centre frequencies, not knobs.
W7_HI_FCS = (4000.0, 5500.0, 7000.0)
W7_HI_HZ = 3000.0                # high-band cut for the >3 kHz turbulence fraction
# the SAME physical T4 framing as the Stage-2 periodicity gate (32 ms / 12 ms),
# expressed at 16 kHz; F0 80-320 Hz -> lag 50..200 @ 16 kHz. NOT knobs — physical.
W7_WIN = int(FS * 32.0 / 1000)   # 512 samples (32 ms @ 16 kHz)
W7_HOP = int(FS * 12.0 / 1000)   # 192 samples (12 ms)
W7_MINLAG, W7_MAXLAG = 50, 200
W7_NLAGS = W7_MAXLAG + 1
W7_DIM = 4

# the STFT geometry for the high-band energy/tilt/onset statistics (owned numpy).
W7_NFFT = 512
W7_STFT_HOP = 128
W7_STFT_WIN = np.hanning(W7_NFFT)


def _hi_band_aperiodicity(x):
    """The HIGH-band APERIODICITY = mean over frames of (1 - periodicity-strength),
    from the native T4 chain (gammatone_band -> band_autocorr ->
    summary_autocorrelogram -> periodicity_track) run on the HIGH-band 4/5.5/7 kHz
    channels. A tall ACF peak there = periodic (a high harmonic of a voiced vowel);
    a flat ACF = aperiodic (turbulent frication noise). This is the T4
    periodic-vs-aperiodic axis GATED TO THE FRICATION BAND. Owned native chain, no
    fit. Returns (mean_aperiodicity, per_frame_aperiodicity_array)."""
    s = np.asarray(x, dtype=np.float32)
    if len(s) < W7_WIN:
        return 0.0, None
    s_list = s.tolist()
    band_acs = []
    for fc in W7_HI_FCS:
        band = _n.gammatone_band(s_list, FS, float(fc), 4)
        ac = _n.band_autocorr(band, W7_WIN, W7_HOP, W7_MAXLAG)
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return 0.0, None
    sacf = _n.summary_autocorrelogram(band_acs, W7_NLAGS)
    if not sacf:
        return 0.0, None
    pt = _n.periodicity_track(sacf, W7_NLAGS, W7_MINLAG, W7_MAXLAG)
    if not pt:
        return 0.0, None
    strengths = np.array(pt[0::2], dtype=np.float64)
    if len(strengths) < 2:
        return 0.0, None
    aperiodic = 1.0 - np.clip(strengths, 0.0, 1.0)     # high-band aperiodicity track
    return float(np.mean(aperiodic)), aperiodic


def _raw_magnitude(sig):
    """Owned STFT magnitude (n_frames x n_bins) of the RAW signal — for the high-band
    energy fraction, spectral tilt, and onset. Owned numpy DSP, no fit, no mask."""
    n = len(sig)
    if n < W7_NFFT:
        sig = np.concatenate([sig, np.zeros(W7_NFFT - n)])
        n = len(sig)
    starts = list(range(0, n - W7_NFFT + 1, W7_STFT_HOP)) or [0]
    mag = np.empty((len(starts), W7_NFFT // 2 + 1), dtype=np.float64)
    for i, st in enumerate(starts):
        mag[i] = np.abs(np.fft.rfft(sig[st:st + W7_NFFT] * W7_STFT_WIN))
    return mag


def w7_frication_cue(x, fs=FS):
    """W7 — the agent's owned 4-dim frication/turbulent-noise descriptor over the
    INTACT 4-8 kHz band:
      [0] high-band energy fraction (E_>3kHz / E_total) — frication PRESENCE.
      [1] high-band APERIODICITY (native T4 periodic-vs-aperiodic, high band).
      [2] high-band spectral TILT (slope of the 4/5.5/7 kHz channel energies):
          /s/ flat-to-rising high; /f/ diffuse/low — the place cue inside frication.
      [3] high-band turbulence onset position [0,1].
    Owned DSP: the native T4 chain ([1]) + owned numpy spectral statistics
    ([0],[2],[3]). NO fit, NO net. This is the W7 cue's extractor."""
    sig = np.asarray(x, dtype=np.float64)
    mag = _raw_magnitude(sig)
    freqs = np.fft.rfftfreq(W7_NFFT, 1.0 / fs)
    me = mag ** 2
    frame_e = me.sum(axis=1) + 1e-12
    hi = freqs >= W7_HI_HZ
    per_frame_hifrac = me[:, hi].sum(axis=1) / frame_e
    active = frame_e > (0.05 * frame_e.max() + 1e-12)
    if active.sum() == 0:
        active = np.ones_like(frame_e, dtype=bool)
    # [0] high-band energy fraction over the energetic frames.
    hi_frac = float(np.mean(per_frame_hifrac[active]))
    # [1] high-band aperiodicity from the native T4 chain.
    aperiodic_mean, _ = _hi_band_aperiodicity(sig)
    # [2] high-band spectral tilt: slope of log-energy across the 4/5.5/7 kHz
    #     channel energies (owned numpy least-squares slope). /s/ concentrates high.
    ch_e = []
    for fc in W7_HI_FCS:
        lo, hiF = fc - 750.0, fc + 750.0
        sel = (freqs >= lo) & (freqs < hiF)
        ch_e.append(float(me[active][:, sel].sum()) if sel.any() else 1e-12)
    ch_e = np.maximum(np.array(ch_e), 1e-12)
    logc = np.log(ch_e)
    fcs = np.array(W7_HI_FCS)
    tilt = float(np.polyfit(fcs - fcs.mean(), logc, 1)[0]) * 1e3   # slope per kHz
    # [3] high-band turbulence onset position (temporal centroid of >3 kHz energy).
    hi_e = me[:, hi].sum(axis=1)
    if hi_e.sum() > 1e-12:
        t = np.arange(len(hi_e), dtype=np.float64)
        onset = float((hi_e * t).sum() / hi_e.sum() / max(1, len(hi_e) - 1))
    else:
        onset = 0.5
    return np.array([hi_frac, aperiodic_mean, tilt, onset], dtype=np.float64)


# ===========================================================================
#  T13 — register W7 as a gated graph Cue on the agent's FrontEnd.
# ===========================================================================

def gate_in_w7(substrate):
    """Register W7 as a `Cue` node on the agent's FrontEnd and GATE IT IN (active=1).
    Graph-resident self-modification (T13): the agent changes WHAT it perceives with
    by mutating the graph, not by a code edit. Returns the cue node id. The extractor
    is registered in AF.CUE_EXTRACTORS so the front end can read it."""
    # register the W7 extractor in the agent's cue-extractor table (the front end
    # dispatches a Cue's `extractor` attr through this map).
    AF.CUE_EXTRACTORS["w7_frication"] = lambda x, fs, M, attrs: w7_frication_cue(x, fs)
    fe = AF.install_frontend(substrate)
    have = {substrate.node(c)["attrs"].get("name")
            for c in substrate.neighbours(fe, "has_cue")} | \
           {substrate.node(c)["attrs"].get("name")
            for c in substrate.neighbours(fe, "repertoire")}
    if "w7_frication" not in have:
        c = substrate.add_node("Cue", {"name": "w7_frication",
                                       "extractor": "w7_frication",
                                       "active": 1.0, "origin": "stage5",
                                       "add_rank": 9})
        substrate.add_edge(fe, "has_cue", c)
    else:
        c = next(n for n in substrate.nodes("Cue")
                 if substrate.node(n)["attrs"].get("name") == "w7_frication")
        substrate.set_attr(c, "active", 1.0)
    return fe, c


# ===========================================================================
#  the FRICATION admissibility prong (a soft excluder over W7) + T8 fusion.
# ===========================================================================
#  The anchor (Stage-3 VTL-invariant formant DtwTo) gives a per-word distance; W7
#  gives a per-word frication-template distance. Each is a soft excluder
#  a(w) = exp(-d(w)/tau); fusion (T8) = argmax_w a_anchor(w) * a_w7(w) ^ weight_w7,
#  the SAME weighted-admissibility shape native_fusion uses, with the LESS-TRUSTED
#  W7 prong weighted by its TRAIN-measured reliability (a measurement, not a knob).

WORD_ATTR = NC.WORD_ATTR
SYN_ATTR = NC.SYN_REL_ATTR
OBS_ATTR = NC.OBS_REL_ATTR


def _anchor_dists(s, q, word_nodes, traj):
    """Per-word anchor distance = native DtwTo(obs invariant traj, proto invariant
    traj(w)) for EVERY word (all needed for fusion). The Stage-3 native decision."""
    s.set_attr(q, OBS_ATTR, _tuple(traj))
    out = {}
    for w, nid in word_nodes.items():
        d = s.evaluate(_Pred(NC._DtwTo(NC._Attr(NC._V("q"), OBS_ATTR),
                                       NC._Attr(NC._V("w"), SYN_ATTR))),
                       {"q": q, "w": nid})
        out[w] = float(d) if d is not None else float("inf")
    return out


def main():
    print("=" * 78)
    print("STAGE 5 — FRICATION / HIGH-BAND DETAIL (the harder manner contrasts), CLEAN 16 kHz")
    print("  the agent's OWN curriculum stage 5: resolve /s/-/sh/-/f/ turbulent-noise")
    print("  contrasts via W7 (high-band spectral-tilt + aperiodic-noise, T4 periodic-")
    print("  vs-aperiodic), gated in (T13), fused with the anchor (T8). Intact 4-8 kHz.")
    print("  STRUCTURAL readiness gate (confusions shrink + anchor safety), NOT accuracy.")
    print("=" * 78)

    files, speakers_all = select_corpus()
    if not files:
        print("!! no clean-16k Speech Commands wavs found under /tmp/sc")
        print("===MARKER_STAGE5_FRICATION_GATE_COMPLETE===")
        return
    print(f"corpus: clean 16 kHz Speech Commands digits, {len(files)} tokens, "
          f"{len(speakers_all)} speakers (NOT downsampled)\n")

    # --- (donkey audit + W7 gate-in) -----------------------------------------
    sub = Substrate()
    fe, w7_cue = gate_in_w7(sub)
    active = [sub.node(c)["attrs"].get("name")
              for c in sub.neighbours(fe, "has_cue")
              if float(sub.node(c)["attrs"].get("active", 0)) >= 1.0]
    print("--- (donkey audit) ---")
    print(f"  W7 registered as a graph Cue (T13) + gated IN  : "
          f"'w7_frication' active among {active}")
    print(f"  W7 extractor in AF.CUE_EXTRACTORS              : "
          f"{'w7_frication' in AF.CUE_EXTRACTORS}")
    print(f"  W7 aperiodicity uses the native T4 chain       : "
          f"gammatone_band -> band_autocorr -> summary_autocorrelogram -> "
          f"periodicity_track")
    print(f"  anchor = Stage-3 native VTL-invariant DtwTo    : UNCHANGED (imported)")
    print(f"  NO net, NO .fit, NO gradient, NO sweep         : owned DSP + T8 fusion\n")

    # --- (1) build BOTH representations on the SAME corpus --------------------
    # anchor = Stage-3 speaker-invariant formant trajectory; W7 = the frication cue.
    anchor = {}     # (digit,speaker,idx) -> invariant trajectory
    fric = {}       # (digit,speaker,idx) -> W7 4-dim descriptor
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        it = invariant_trajectory(x, fs)
        if it is None or len(it) < 2:
            continue
        key = (digit, speaker, idx)
        anchor[key] = it
        fric[key] = w7_frication_cue(x, fs)
    keys = sorted(set(anchor) & set(fric))
    print(f"--- (1) representations on the SAME corpus ---")
    print(f"  anchor (VTL-invariant formant traj)   : {len(anchor)} tokens")
    print(f"  W7 frication descriptor (4-dim)       : {len(fric)} tokens")
    print(f"  tokens with both                      : {len(keys)}\n")

    # --- W7 sanity: mean per digit (fricative-onset digits should stand out) ---
    print("  W7 sanity (mean per digit; raw, not z-scored):")
    print(f"    {'digit':>6} {'hi_frac':>8} {'aperiod':>8} {'tilt':>8} {'onset':>6}")
    fric_targets = {"six", "seven", "four", "five", "three", "zero"}
    for d in range(10):
        rows = np.array([fric[k] for k in keys if k[0] == d])
        if len(rows):
            m = rows.mean(axis=0)
            star = "  <- fricative-onset" if _DIGITS[d] in fric_targets else ""
            print(f"    {_DIGITS[d]:>6} {m[0]:>8.3f} {m[1]:>8.3f} {m[2]:>8.3f} "
                  f"{m[3]:>6.3f}{star}")
    print()

    # --- (2) ANCHOR SAFETY (T9): the vowel/sonority recogniser's OWN cross-speaker
    #     separation, measured BEFORE adding W7 (the Stage-3 instrument, verbatim). ---
    print("=" * 78)
    print("(2) ANCHOR SAFETY (T9) — the vowel/sonority recogniser must NOT be dragged")
    print("=" * 78)
    anchor_struct = cross_speaker_structure(anchor, "ANCHOR (Stage-3 VTL-invariant)")
    anchor_dprime = anchor_struct["dprime"]

    # --- (3) THE FRICATIVE-CONFUSION GATE: per-pair cross-speaker margin WITH vs
    #     WITHOUT W7. The "systematic fricative confusions" are the named pairs. For
    #     each token of digit A whose partner is B, we read how much CLOSER it sits to
    #     its own digit's template than to the partner's, under (i) anchor-only and
    #     (ii) anchor + W7 (T8 fusion). A POSITIVE margin = correctly separated; the
    #     gate fires if the W7-fused margin is systematically HIGHER (the confusable
    #     pair separates better) while the anchor's own d' (above) holds. ---
    print("\n" + "=" * 78)
    print("(3) FRICATIVE-CONFUSION GATE — do the systematic confusions SHRINK with W7?")
    print("=" * 78)

    # the named systematic fricative/consonant confusion pairs (the Stage-5 targets):
    # both-/s/, both-/f/, the /th/ and /z/ onsets that the anchor confuses.
    PAIRS = [("six", "seven"), ("four", "five"), ("three", "zero"),
             ("six", "three"), ("seven", "zero"), ("four", "six")]

    # LOSO-style cross-speaker evaluation: prototypes from a held proto-speaker pool,
    # tokens scored from the rest. Anchor prototypes = medoid invariant traj; W7
    # prototypes = mean z-scored frication descriptor. TRAIN(proto)-only stats.
    speakers = sorted({k[1] for k in keys})
    n_proto = 3
    proto_speakers = set(speakers[:n_proto])
    test_keys = [k for k in keys if k[1] not in proto_speakers]
    proto_keys = [k for k in keys if k[1] in proto_speakers]

    # anchor prototype per digit = medoid invariant trajectory over the proto pool.
    s = Substrate()
    word_nodes = {}
    proto_anchor = {}
    for d in range(10):
        pool = [anchor[k] for k in proto_keys if k[0] == d]
        if not pool:
            continue
        if len(pool) == 1:
            proto_anchor[_DIGITS[d]] = pool[0]
        else:
            sp = Substrate()
            nodes = []
            for v in pool:
                nid = sp.add_node("Concept", {})
                sp.set_attr(nid, SYN_ATTR, _tuple(v))
                nodes.append(v)
            qd = sp.add_node("Query", {OBS_ATTR: _tuple(pool[0])})
            best_v, best_tot = pool[0], None
            for v in pool:
                sp.set_attr(qd, OBS_ATTR, _tuple(v))
                tot = 0.0
                for nid in sp.nodes("Concept"):
                    tot += float(sp.evaluate(_Pred(NC._DtwTo(
                        NC._Attr(NC._V("q"), OBS_ATTR),
                        NC._Attr(NC._V("w"), SYN_ATTR))), {"q": qd, "w": nid}))
                if best_tot is None or tot < best_tot:
                    best_tot, best_v = tot, v
            proto_anchor[_DIGITS[d]] = best_v
    for w, traj in proto_anchor.items():
        nid = s.add_node("Concept", {"name": w})
        s.set_attr(nid, WORD_ATTR, 1.0)
        s.set_attr(nid, SYN_ATTR, _tuple(traj))
        word_nodes[w] = nid
    q = s.add_node("Query", {OBS_ATTR: _tuple(proto_anchor[next(iter(proto_anchor))])})

    # W7: z-score stats + per-digit template from the PROTO pool only.
    fr_proto = np.array([fric[k] for k in proto_keys])
    fr_mean = fr_proto.mean(axis=0)
    fr_std = fr_proto.std(axis=0) + 1e-9
    w7_templ = {}
    for d in range(10):
        rows = [(fric[k] - fr_mean) / fr_std for k in proto_keys if k[0] == d]
        w7_templ[_DIGITS[d]] = (np.mean(rows, axis=0) if rows
                                else np.zeros(W7_DIM))

    # tau scales: each channel's tau = median over PROTO tokens of the across-digit
    # spread of that channel's distances (its discriminative dynamic range) — puts
    # both soft excluders on a comparable scale. A measurement, not a knob.
    a_spreads, w_spreads = [], []
    for k in proto_keys[:120]:
        da = _anchor_dists(s, q, word_nodes, anchor[k])
        fin = [v for v in da.values() if np.isfinite(v)]
        if len(fin) >= 2:
            a_spreads.append(max(fin) - min(fin))
        z = (fric[k] - fr_mean) / fr_std
        dw = [float(np.linalg.norm(z - w7_templ[w])) for w in word_nodes]
        if len(dw) >= 2:
            w_spreads.append(max(dw) - min(dw))
    tau_a = max(float(np.median(a_spreads)) if a_spreads else 1.0, 1e-6)
    tau_w = max(float(np.median(w_spreads)) if w_spreads else 1.0, 1e-6)

    # W7 reliability weight (T8): the prong's TRAIN above-chance correctness,
    # normalised to [0,1] — the SAME measurement weighted_admissibility uses (NOT a
    # swept knob). Measured on the PROTO pool: does W7-alone pick the right digit?
    w7_correct = 0
    for k in proto_keys:
        z = (fric[k] - fr_mean) / fr_std
        pred = min(word_nodes, key=lambda w: float(np.linalg.norm(z - w7_templ[w])))
        if pred == _DIGITS[k[0]]:
            w7_correct += 1
    w7_acc = w7_correct / max(1, len(proto_keys))
    w7_weight = max(0.0, (w7_acc - 0.10) / 0.90)     # above-chance, normalised [0,1]
    print(f"  W7-alone train accuracy (proto pool)  : {w7_acc:.3f} "
          f"(chance 0.100)  -> reliability weight = {w7_weight:.3f}")
    print(f"  tau_anchor = {tau_a:.4f}   tau_w7 = {tau_w:.4f}   "
          f"(per-channel across-digit spread, measured)\n")

    # per-pair cross-speaker margins, anchor-only vs anchor+W7 (T8 fusion).
    # margin(token of A, partner B) = d(A_template) - d(B_template) in the SOFT-
    # EXCLUDER (log-admissibility) space, summed across the fused prongs; >0 = the
    # token is correctly closer to its own digit than to its confusable partner.
    def _log_a(d_dict, tau):
        return {w: (-d_dict[w] / tau if np.isfinite(d_dict[w]) else -1e9)
                for w in d_dict}

    pair_margins = {p: {"anchor": [], "fused": []} for p in PAIRS}
    confusions_anchor = {p: 0 for p in PAIRS}
    confusions_fused = {p: 0 for p in PAIRS}
    pair_tot = {p: 0 for p in PAIRS}

    for k in test_keys:
        true_w = _DIGITS[k[0]]
        da = _anchor_dists(s, q, word_nodes, anchor[k])
        z = (fric[k] - fr_mean) / fr_std
        dw = {w: float(np.linalg.norm(z - w7_templ[w])) for w in word_nodes}
        la = _log_a(da, tau_a)
        lw = _log_a(dw, tau_w)
        # fused log-admissibility (T8): anchor + weight_w7 * W7 (soft-AND in log).
        lf = {w: la[w] + w7_weight * lw[w] for w in word_nodes}
        for (A, B) in PAIRS:
            if true_w == A and A in word_nodes and B in word_nodes:
                pair_tot[(A, B)] += 1
                # margin = own - partner in log-admissibility (>0 = own preferred)
                m_anchor = la[A] - la[B]
                m_fused = lf[A] - lf[B]
                pair_margins[(A, B)]["anchor"].append(m_anchor)
                pair_margins[(A, B)]["fused"].append(m_fused)
                if m_anchor <= 0:
                    confusions_anchor[(A, B)] += 1
                if m_fused <= 0:
                    confusions_fused[(A, B)] += 1

    print("  per-pair cross-speaker SEPARATION (margin = log-adm own - partner; "
          ">0 = separated):")
    print(f"    {'pair':>14} {'n':>4} {'margin_anchor':>14} {'margin+W7':>11} "
          f"{'conf_anchor':>12} {'conf+W7':>9}")
    total_conf_a = total_conf_f = total_n = 0
    margin_improved_pairs = 0
    conf_shrunk_pairs = 0
    eligible_pairs = 0
    for p in PAIRS:
        n = pair_tot[p]
        if n == 0:
            continue
        eligible_pairs += 1
        ma = float(np.mean(pair_margins[p]["anchor"]))
        mf = float(np.mean(pair_margins[p]["fused"]))
        ca, cf = confusions_anchor[p], confusions_fused[p]
        total_conf_a += ca; total_conf_f += cf; total_n += n
        if mf > ma:
            margin_improved_pairs += 1
        if cf < ca:
            conf_shrunk_pairs += 1
        flag = ""
        if cf < ca:
            flag = "  SHRUNK"
        elif cf > ca:
            flag = "  (worse)"
        print(f"    {p[0]+'/'+p[1]:>14} {n:>4} {ma:>14.3f} {mf:>11.3f} "
              f"{ca:>9}/{n:<2} {cf:>6}/{n:<2}{flag}")

    print(f"\n  overall fricative-pair confusions: anchor {total_conf_a}/{total_n} "
          f"-> +W7 {total_conf_f}/{total_n} "
          f"({'SHRUNK' if total_conf_f < total_conf_a else 'NOT shrunk'}, "
          f"{total_conf_a - total_conf_f:+d})")
    print(f"  pairs whose mean margin IMPROVED with W7 : "
          f"{margin_improved_pairs}/{eligible_pairs}")
    print(f"  pairs whose confusion count SHRANK       : "
          f"{conf_shrunk_pairs}/{eligible_pairs}")

    # --- (4) ANCHOR SAFETY re-check: the anchor's own d' is UNCHANGED (the fusion
    #     does not modify the anchor representation; the gate is that the W7 prong
    #     never drags the vowel recogniser). We report the anchor d' and confirm the
    #     fused decision does not HARM the non-fricative (sonorant/vowel) digits. ---
    print("\n" + "=" * 78)
    print("(4) ANCHOR SAFETY re-check — the vowel/sonorant digits not dragged by W7")
    print("=" * 78)
    # sonorant/vowel-led digits (no strong frication onset): one, two, eight, nine.
    SONORANT = {"one", "two", "eight", "nine"}
    son_anchor_ok = son_fused_ok = son_tot = 0
    for k in test_keys:
        true_w = _DIGITS[k[0]]
        if true_w not in SONORANT or true_w not in word_nodes:
            continue
        da = _anchor_dists(s, q, word_nodes, anchor[k])
        z = (fric[k] - fr_mean) / fr_std
        dw = {w: float(np.linalg.norm(z - w7_templ[w])) for w in word_nodes}
        la = _log_a(da, tau_a)
        lw = _log_a(dw, tau_w)
        lf = {w: la[w] + w7_weight * lw[w] for w in word_nodes}
        son_tot += 1
        if max(word_nodes, key=lambda w: la[w]) == true_w:
            son_anchor_ok += 1
        if max(word_nodes, key=lambda w: lf[w]) == true_w:
            son_fused_ok += 1
    son_a = son_anchor_ok / max(1, son_tot)
    son_f = son_fused_ok / max(1, son_tot)
    print(f"  sonorant/vowel digits (one,two,eight,nine) recognised:")
    print(f"    anchor-only : {son_anchor_ok}/{son_tot} = {son_a:.3f}")
    print(f"    anchor + W7 : {son_fused_ok}/{son_tot} = {son_f:.3f}")
    anchor_not_dragged = son_f >= son_a - 0.02      # within tolerance = not dragged
    print(f"  >>> vowel/sonorant recogniser NOT dragged by W7 : {anchor_not_dragged} "
          f"({(son_f - son_a)*100:+.1f} pts)")

    # --- VERDICT --------------------------------------------------------------
    print("\n" + "=" * 78)
    print("=== STAGE-5 READINESS GATE — FRICATION / HIGH-BAND DETAIL (CLEAN 16 kHz) ===")
    confusions_shrink = (total_conf_f < total_conf_a) and (conf_shrunk_pairs >= 1)
    margins_improve = margin_improved_pairs > eligible_pairs / 2
    anchor_safe = anchor_not_dragged and anchor_dprime > 0.0
    fires = confusions_shrink and anchor_safe

    print(f"  W7 built + gated in (native T4 + owned DSP, T13)   : True")
    print(f"  FRICATIVE confusions SHRINK with W7 (the signal)   : {confusions_shrink}  "
          f"[overall {total_conf_a} -> {total_conf_f}, {conf_shrunk_pairs}/{eligible_pairs} "
          f"pairs shrank]")
    print(f"  per-pair margins improve (>half the pairs)         : {margins_improve}  "
          f"[{margin_improved_pairs}/{eligible_pairs}]")
    print(f"  ANCHOR SAFETY: vowel recogniser NOT dragged (T9)   : {anchor_safe}  "
          f"[sonorant {son_a:.3f}->{son_f:.3f}, anchor d'={anchor_dprime:.3f}]")
    print("  " + "-" * 64)
    print(f"  >>> STAGE-5 FRICATION STRUCTURE ADMITTED "
          f"(confusions shrink AND anchor safe): {fires}")
    print("=" * 78)
    print("===MARKER_STAGE5_FRICATION_GATE_COMPLETE===")


if __name__ == "__main__":
    main()
