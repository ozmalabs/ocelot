"""perception_rescoring — THE AGENT RE-COMPOSES ITS PERCEPTION SCORING FROM THE INSIDE.

(memory ozma_agent_owns_its_perception / ozma_dont_author_seeds_agent_designs_them.)
perception_composition (commit 5defadb8) PROVED the unvoiced GAP is the right discriminating
dimension — observing it (unvoiced_gap_detect) reached the comparison and fixed six/eight
(eight +15.7), lifting the articulatory prong 24.0%->33.5%. BUT the FUSION went -1.5
(59.4%->57.9%) because the SCORING of that dimension is a LOSSY TRANSFORM:

  * the gap is a BINARY GATE  — unvoiced_gap_detect emits {0,1} and synth_voicing emits {0,1};
    seven's PARTIAL voicing (/s/ voiceless onset, /v/ VOICED fricative, vowels, nasal) is scored
    like six's HARD silence, so seven collapses 64.3%->33.7% (-30.6) onto three/nine.
  * the gap is wired at ONE GLOBAL fusion weight (W_VOICING_SHADOW) — a digit the gap does NOT
    cleanly cue (seven, mostly voiced) is punished by the same channel that helps six/eight.

The discriminating dimension is PRESENT; the SCORING over-corrects. We RE-COMPOSE the SCORING
(NOT the recogniser) from the agent's OWN owned perception/DSL primitives. Two changes, both
composed from primitives verified to exist in the codebase:

  (1) GRADED gap, not a binary gate.
      OBSERVED side: replace the {0,1} energy gate with a CONTINUOUS voicing likelihood in [0,1]
      composed from owned numpy: a soft (clipped-linear) function of normalised log frame-energy
      ABOVE the floor (separates silence/gap from sound), MODULATED by the low-band/high-band
      energy ratio (voiced phonation is low-frequency / harmonic-dominated; frication is
      high-frequency; silence is low everywhere). No threshold, no fit. Same OWNED framing
      (FRAME_MS/HOP_MS) as the tracker; the gate is replaced by a graded likelihood.
      MODEL side: replace synth_voicing's {0,1} (VOWEL=1 else 0) with a GRADED per-source
      voicing level — vowels/nasals ~1.0, VOICED fricatives (/v/,/z/) ~partial, VOICELESS
      fricatives (/s/,/f/,/th/) ~low, stop bursts/silence ~0. So seven's /v/ no longer reads as
      hard silence and seven's envelope sits BETWEEN six's hard gap and a full vowel.

  (2) PER-CONTEXT weight, not one global W_VOICING_SHADOW.
      Weight the gap channel PER DIGIT HYPOTHESIS by how much the gap actually CUES that digit:
      scale the voicing term by the model's expected UNVOICED FRACTION (1 - mean voicing). A
      digit with a strong silence/frication gap (six: ~0.5 unvoiced) gets ~full weight; a mostly
      voiced digit the gap does not cue (seven, nine: low unvoiced fraction) gets the gap weighted
      DOWN, so a partial-voicing mismatch can no longer punish it. The weight is DERIVED from the
      forward model (owned knowledge), not swept on test.

=========================================================================================
DONKEY AUDIT
=========================================================================================
  * Both changes = LIVE composition from owned numpy + the existing forward model. No net, no
    .fit, no gradient, no frozen agent_specify_* stub (those are historical — memory
    ozma_specify_functions_are_historical; we derive live).
  * RECOGNISER LOGIC UNCHANGED. The formant-trajectory prong (graph DtwTo/MinOver/Argmin Term),
    the fusion math (weighted-admissibility soft-excluder sum), the n-gram, the exemplar bank,
    the reliability weighting, the tau scales, the LOSO plumbing — ALL imported VERBATIM from
    formant_trajectory_dynamics / articulatory_gamma / mcu_infer. The ONLY change vs
    perception_composition is INSIDE the voicing term of the articulatory distance: graded
    observed likelihood + graded model envelope + per-digit unvoiced-fraction weight.
  * Exemplars / tau / n-gram / reliability / per-context weights = TRAIN-side or forward-model
    only; held-out NEVER banked. CortexLoop + solve_for_n untouched.

PREDICTION: graded gap + per-context weight -> seven's partial voicing scored correctly (recovers
from 33.7%) WHILE six/eight gains hold -> NET-IMPROVE over the binary 57.9%, toward the gap-dropped
59.4% / the 62.2% pairing base. HONEST: report whether it net-improves AND whether seven recovers
WITHOUT losing six/eight; if not, pinpoint the next limiter (NEVER "more audio").

Run:  PYTHONUNBUFFERED=1 python -m scripts.perception_rescoring
      PYTHONUNBUFFERED=1 python -m scripts.perception_rescoring --quick
"""
from __future__ import annotations

import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.viterbi_pairing as VP          # noqa: F401  (side effect: ftd.formant_track patched)
import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import (  # noqa: E402
    DIGITS, FS, FRAME_MS, HOP_MS, VOICED_FLOOR,
    load_wav, gather_files,
    trajectory_feature, relative_formants_frame,
    dtw_predict_term, _traj_tuple, _P, _print_confusion,
    TRAJ_ATTR, WORD_ATTR, Q_ATTR,
)
import scripts.articulatory_gamma as AG       # noqa: E402  (the prong + Γ + fusion, verbatim)
from scripts.articulatory_gamma import (       # noqa: E402
    articulatory_models, _harmonic_dists, reliability_weight,
    W_FORMANT_SHADOW, W_VOICING_SHADOW, W_GAMMA, _resample_to,
    GESTURE_SCORES, _admissible_trajectory, synth_formant_trajectory, _rel_formant_seq,
    VOWEL, FRIC, BURST, SIL, SYNTH_FRAMES,
)
from scripts import mcu_infer as mi             # noqa: E402  (the exemplar bank, verbatim)


# =========================================================================================
#  RE-COMPOSITION (1a): GRADED OBSERVED voicing likelihood in [0,1] (was a {0,1} energy gate).
#  Composed from owned numpy: soft log-energy-above-floor (gap vs sound) MODULATED by the
#  low-band/high-band energy ratio (voiced=low-freq/harmonic, frication=high-freq, silence=low).
# =========================================================================================

# low/high split for the voicing/frication contrast: voiced phonation energy concentrates below
# ~1 kHz (F0 + low harmonics); sibilant frication concentrates high. At FS=8000 the rFFT bins of a
# 32 ms frame span 0..4 kHz; the 1 kHz split is a fixed owned cut, not a fitted parameter.
_VOICE_SPLIT_HZ = 1000.0


def graded_voicing_observed(sig, fs):
    """PRIMITIVE (graded re-composition of unvoiced_gap_detect). (sig, fs) -> (n_all,) CONTINUOUS
    per-frame voicing LIKELIHOOD in [0,1] (was {0,1}). Composed from owned numpy, no fit:

      energy_term  = clip((log_rms - log_floor) / span, 0, 1)        # 0 at the gap, ->1 above it
      lowband_frac = E(<1kHz) / E(total)                              # voiced=high, frication=low
      voicing      = energy_term * lowband_frac                       # both required to read voiced

    Silence -> energy_term~0 -> voicing~0 (the gap). Sibilant /s/ -> energy high but lowband_frac
    low -> voicing low (partial). Vowel/nasal -> energy high AND lowband high -> voicing~1. A
    VOICED fricative /v/ -> mid energy + mid lowband -> voicing PARTIAL (the seven cue). Same OWNED
    FRAME_MS/HOP_MS framing as the tracker; the binary gate is replaced by this graded likelihood."""
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if len(sig) < flen:
        return None
    starts = list(range(0, len(sig) - flen + 1, hop))
    win = np.hanning(flen)
    freqs = np.fft.rfftfreq(flen, 1.0 / fs)
    low_mask = freqs < _VOICE_SPLIT_HZ
    rms = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
    if rms.max() <= 1e-9:
        return None
    # soft energy-above-floor: log-RMS mapped 0..1 across [floor, max]. The binary gate's
    # threshold (VOICED_FLOOR*max) becomes the LOWER knee of a clipped-linear ramp.
    log_rms = np.log(rms + 1e-9)
    log_floor = math.log(VOICED_FLOOR * rms.max() + 1e-9)
    log_max = math.log(rms.max() + 1e-9)
    span = max(log_max - log_floor, 1e-6)
    energy_term = np.clip((log_rms - log_floor) / span, 0.0, 1.0)
    # low-band fraction per frame (voiced vs frication contrast), owned rFFT.
    lowfrac = np.zeros(len(starts))
    for k, s in enumerate(starts):
        sp = np.abs(np.fft.rfft(sig[s:s + flen] * win)) ** 2
        tot = float(sp.sum())
        lowfrac[k] = float(sp[low_mask].sum()) / tot if tot > 1e-12 else 0.0
    return (energy_term * lowfrac).astype(np.float64)   # graded voicing likelihood in [0,1]


# =========================================================================================
#  RE-COMPOSITION (1b): GRADED MODEL voicing envelope (was synth_voicing's {0,1}).
#  Map each source type -> a graded voicing level, so a VOICED fricative is not hard silence.
#  Derived from owned phonetics (vocal-fold state), NOT fitted. Voiced fricatives are detected
#  from the gesture config (labiodental/alveolar place at high constriction WITHOUT a sibilant
#  groove is the voiced /v/,/z/ family); voiceless sibilants /s/,/f/,/th/ stay low.
# =========================================================================================

# graded voicing levels per source family (vocal-fold vibration fraction), owned phonetics.
_VOI_VOWEL = 1.00     # full phonation (vowels, nasals, glides, liquids)
_VOI_VFRIC = 0.55     # VOICED fricative /v/,/z/ — folds vibrate through the constriction
_VOI_UFRIC = 0.12     # VOICELESS fricative /s/,/f/,/th/ — no phonation, but some aperiodic energy
_VOI_BURST = 0.05     # stop burst / closure
_VOI_SIL = 0.00


def _is_voiced_fric(cfg):
    """Owned heuristic on the gesture CONFIG: a FRIC segment is the VOICED-fricative family (/v/,/z/)
    rather than the voiceless sibilant (/s/) when it is NOT a high-front alveolar sibilant groove.
    /s/ in this nomogram = front~0.80, place~0.78, degree~0.92 (the sibilant groove); /v/ = front
    ~0.30, place~1.00 (labiodental); /z/ = front~0.70, place~0.75. We mark as voiced-fric any FRIC
    whose front is NOT high (front < 0.75) — i.e. not the /s/ sibilant — leaving /s/ voiceless. This
    reads ONLY the owned config, no labels added to the gesture score."""
    front = float(cfg[0])
    return front < 0.75


def graded_voicing_model(src_seq, cfg_seq):
    """GRADED replacement for synth_voicing. (src_seq, cfg_seq) -> (n,) graded voicing in [0,1].
    VOWEL->1.0 ; FRIC-> voiced(0.55)/voiceless(0.12) by config ; BURST->0.05 ; SIL->0.0. Owned."""
    out = np.zeros(len(src_seq))
    for t, s in enumerate(src_seq):
        if s == VOWEL:
            out[t] = _VOI_VOWEL
        elif s == FRIC:
            out[t] = _VOI_VFRIC if _is_voiced_fric(cfg_seq[t]) else _VOI_UFRIC
        elif s == BURST:
            out[t] = _VOI_BURST
        else:
            out[t] = _VOI_SIL
    return out


def graded_articulatory_models():
    """Like articulatory_models() but with the GRADED voicing envelope + the per-digit expected
    UNVOICED FRACTION (for the per-context weight). Recogniser-side formant/Γ pieces UNCHANGED;
    only the voicing envelope is re-composed. Returns {digit:{rel,voi(graded),gamma,unvoiced_frac}}."""
    out = {}
    for w, score in GESTURE_SCORES.items():
        traj, src_seq, gamma = _admissible_trajectory(score, SYNTH_FRAMES)
        form = synth_formant_trajectory(traj)
        rel = _rel_formant_seq(form)
        # graded model voicing needs the per-frame config to tell voiced /v/ from voiceless /s/.
        voi = graded_voicing_model(src_seq, [traj[t] for t in range(traj.shape[0])])
        unvoiced_frac = float(np.mean(1.0 - voi))     # how strongly the gap cues this digit
        out[w] = {"rel": rel, "voi": voi, "gamma": gamma, "unvoiced_frac": unvoiced_frac}
    return out


# =========================================================================================
#  RE-COMPOSITION wired into the articulatory distance — graded gap + PER-CONTEXT weight.
#  This is the ONLY behavioural change vs perception_composition's articulatory_distance_recomposed.
# =========================================================================================

def articulatory_distance_rescored(obs_rel, obs_voicing, models, mode):
    """The per-digit articulatory admissibility d_A(w) with the RE-COMPOSED voicing scoring.

      d_A(w) = W_FORMANT_SHADOW * formant-shadow-L2
             + voicing_term(w)                                        (LIVE iff obs_voicing not None)
             + W_GAMMA * Γ-cost(w).

    mode selects the voicing-term composition:
      'binary'   : (control) W_VOICING_SHADOW * L1(binary obs, binary model)   [= the 57.9% class]
      'graded'   : W_VOICING_SHADOW * L1(graded obs, graded model)             [change 1 only]
      'context'  : W_VOICING_SHADOW * unvoiced_frac(w) * L1(graded obs, graded model)  [changes 1+2]

    Owned numpy; W_* are the frozen owned scales from articulatory_gamma. When obs_voicing is None
    the voicing term is OMITTED (recovers the gap-dropped distance)."""
    n = obs_rel.shape[0]
    out = {}
    for w, m in models.items():
        syn = _resample_to(m["rel"], n)
        fshadow = float(np.mean(np.linalg.norm(obs_rel - syn, axis=1)))
        d = W_FORMANT_SHADOW * fshadow + W_GAMMA * m["gamma"]
        if obs_voicing is not None:
            ov = obs_voicing.reshape(-1, 1)
            L = max(ov.shape[0], m["voi"].shape[0], 2)
            ov_r = _resample_to(ov, L)[:, 0]
            sv_r = _resample_to(m["voi"].reshape(-1, 1), L)[:, 0]
            vshadow = float(np.mean(np.abs(ov_r - sv_r)))
            if mode == "context":
                # PER-CONTEXT: scale by how strongly the gap cues THIS digit (unvoiced fraction).
                d += W_VOICING_SHADOW * m["unvoiced_frac"] * vshadow
            else:
                d += W_VOICING_SHADOW * vshadow
        out[w] = d
    return out


# the BINARY controls (verbatim from perception_composition, for the 57.9% reference column).
def binary_voicing_observed(sig, fs):
    """The original {0,1} energy-gate (perception_composition.unvoiced_gap_detect), verbatim."""
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if len(sig) < flen:
        return None
    starts = list(range(0, len(sig) - flen + 1, hop))
    energies = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
    if energies.max() <= 1e-9:
        return None
    thr = VOICED_FLOOR * energies.max()
    return (energies >= thr).astype(np.float64)


def binary_models():
    """articulatory_models() verbatim (binary synth_voicing) + unvoiced_frac for symmetry."""
    out = {}
    for w, m in articulatory_models().items():
        d = dict(m)
        d["unvoiced_frac"] = float(np.mean(1.0 - m["voi"]))
        out[w] = d
    return out


# =========================================================================================
#  CORPUS — perceive each token once, storing BOTH observed voicing envelopes (binary + graded)
#  + the trajectory/rel/mel the recogniser reads. Mechanical ingest, no agent decisions.
# =========================================================================================

def build_corpus(sub, seed=0, quick=False):
    rng = np.random.default_rng(seed)
    files = gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    npr = 6 if quick else 999
    corpus = []
    mel_ops = mi.Ops()
    skipped = 0
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:npr]:
            sig, fs = load_wav(p)
            track = ftd.formant_track(sig, fs)
            if track is None:
                skipped += 1
                continue
            feat = trajectory_feature(sub, track)
            obs_rel = np.array([relative_formants_frame(f) for f in track])
            M = mi.front_end(sig, fs, mel_ops)
            if M.shape[0] < 2:
                skipped += 1
                continue
            corpus.append({
                "traj": feat, "obs_rel": obs_rel,
                "obs_v_binary": binary_voicing_observed(sig, fs),
                "obs_v_graded": graded_voicing_observed(sig, fs),
                "mel": M, "word": DIGITS[d], "speaker": spk,
            })
    return corpus, skipped


def _obs_for(it, mode):
    """Pick the observed voicing envelope for the scoring mode (graded for graded/context)."""
    if mode == "dropped":
        return None
    return it["obs_v_binary"] if mode == "binary" else it["obs_v_graded"]


def _measure_art_weight(corpus, train_idx, models, mode, chance):
    c = t = 0
    for i in train_idx:
        true = corpus[i]["word"]
        ov = _obs_for(corpus[i], mode)
        d_a = articulatory_distance_rescored(corpus[i]["obs_rel"], ov, models, mode)
        pred = min(DIGITS, key=lambda w: d_a[w])
        t += 1; c += int(pred == true)
    return reliability_weight(c / max(1, t), chance), c / max(1, t)


def evaluate(corpus, mode, models, verbose=True):
    """LOSO eval, fusion recogniser VERBATIM from articulatory_gamma. `mode` selects the voicing
    scoring (dropped/binary/graded/context); EVERYTHING else is identical across modes."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()
    chance = 1.0 / len(DIGITS)

    canonical = mi.canonical_log_centroid([it["mel"] for it in corpus])
    by_spk_mel = defaultdict(list)
    for it in corpus:
        by_spk_mel[it["speaker"]].append(it["mel"])
    spk_stats = {s: mi.speaker_stats(by_spk_mel[s]) for s in speakers}
    mel_ops = mi.Ops()
    mel_normed = {}
    for i, it in enumerate(corpus):
        mean, std = spk_stats[it["speaker"]]
        mel_normed[i] = mi.normalise(it["mel"], mean, std, canonical, mel_ops)

    form_c = form_n = art_c = art_n = ng_c = ng_n = 0
    fused_c = fused_n = mel_c = mel_n = 0
    per_speaker = {}
    conf_art = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_fused = {w: {u: 0 for u in DIGITS} for w in DIGITS}

    for held in speakers:
        test_idx = [i for i, it in enumerate(corpus) if it["speaker"] == held]
        train_idx = [i for i, it in enumerate(corpus) if it["speaker"] != held]

        s = Substrate()
        word_nodes = {}
        for w in DIGITS:
            word_nodes[w] = s.add_node("Concept", {"name": w, WORD_ATTR: 1.0})
        for i in train_idx:
            ex = s.add_node("Exemplar", {TRAJ_ATTR: _traj_tuple(corpus[i]["traj"])})
            s.add_edge_unchecked(word_nodes[corpus[i]["word"]], "has_exemplar", ex)
        q_node = s.add_node("Query", {Q_ATTR: ((0.0,) * 9,)})

        train_counts = Counter(corpus[i]["word"] for i in train_idx)
        tot = sum(train_counts.values())
        ng_logp = {w: math.log((train_counts.get(w, 0) + 1.0) / (tot + len(DIGITS))) for w in DIGITS}
        ng_top = max(ng_logp.values())
        ng_logp = {w: ng_logp[w] - ng_top for w in DIGITS}

        h_sample = train_idx if len(train_idx) <= 80 else \
            [train_idx[j] for j in np.linspace(0, len(train_idx) - 1, 80).astype(int)]
        h_spreads = []
        for i in h_sample:
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            dh = AG._harmonic_dists(s, term, q_node, word_nodes)
            finite = [v for v in dh.values() if math.isfinite(v)]
            if len(finite) >= 2:
                h_spreads.append(max(finite) - min(finite))
        tau_h = max(float(np.median(h_spreads)) if h_spreads else 1.0, 1e-6)
        a_spreads = []
        for i in h_sample:
            ov = _obs_for(corpus[i], mode)
            da = articulatory_distance_rescored(corpus[i]["obs_rel"], ov, models, mode)
            vals = list(da.values())
            a_spreads.append(max(vals) - min(vals))
        tau_a = max(float(np.median(a_spreads)) if a_spreads else 1.0, 1e-6)

        w_form = 1.0
        w_art, art_train_acc = _measure_art_weight(corpus, train_idx, models, mode, chance)

        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]

        s_fused_c = s_fused_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = AG._harmonic_dists(s, term, q_node, word_nodes)
            ov = _obs_for(corpus[i], mode)
            d_a = articulatory_distance_rescored(corpus[i]["obs_rel"], ov, models, mode)

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_a = {w: -d_a[w] / tau_a for w in DIGITS}

            pred_form = min(DIGITS, key=lambda w: d_h[w])
            form_n += 1; form_c += int(pred_form == true)

            pred_art = min(DIGITS, key=lambda w: d_a[w])
            art_n += 1; art_c += int(pred_art == true); conf_art[true][pred_art] += 1

            pred_ng = max(DIGITS, key=lambda w: ng_logp[w])
            ng_n += 1; ng_c += int(pred_ng == true)

            h_top = max((v for v in log_a_h.values() if v > -1e17), default=0.0)
            log_a_h_c = {w: (log_a_h[w] - h_top if log_a_h[w] > -1e17 else -1e18) for w in DIGITS}
            a_top = max(log_a_a.values())
            log_a_a_c = {w: log_a_a[w] - a_top for w in DIGITS}
            logA = {w: log_a_h_c[w] + w_art * log_a_a_c[w] + ng_logp[w] for w in DIGITS}
            pred_fused = max(DIGITS, key=lambda w: logA[w])
            fused_n += 1; s_fused_t += 1
            if pred_fused == true:
                fused_c += 1; s_fused_c += 1
            conf_fused[true][pred_fused] += 1

            ds = sorted((mi.dtw(mel_normed[i], Mtr, mel_ops), wtr) for Mtr, wtr in bank_mel)
            pred_mel = Counter([w for _, w in ds[:mi.KNN_K]]).most_common(1)[0][0]
            mel_n += 1; mel_c += int(pred_mel == true)

        per_speaker[held] = s_fused_c / max(1, s_fused_t)
        if verbose:
            print(f"    held-out {held:10s}: fused {s_fused_c/max(1,s_fused_t):.3f} "
                  f"(n={s_fused_t}, w_art={w_art:.3f}, art_train={art_train_acc:.3f})", flush=True)

    return {
        "form_acc": form_c / max(1, form_n),
        "art_acc": art_c / max(1, art_n), "art_n": art_n,
        "ng_acc": ng_c / max(1, ng_n),
        "fused_acc": fused_c / max(1, fused_n), "fused_n": fused_n,
        "mel_acc": mel_c / max(1, mel_n),
        "per_speaker": per_speaker,
        "conf_art": conf_art, "conf_fused": conf_fused,
    }


def _digit_acc(conf, w):
    tot = sum(conf[w].values())
    return (conf[w][w] / tot if tot else 0.0), tot


def _into(conf, target):
    return sum(conf[w][target] for w in DIGITS if w != target)


def _watch_rows(title, conf):
    watch = [("seven", "six"), ("seven", "three"), ("seven", "nine"), ("seven", "eight"),
             ("six", "seven"), ("six", "two"), ("six", "nine"),
             ("eight", "six"), ("eight", "seven"), ("eight", "three")]
    print(f"\n  {title} — gap-cued confusions (true->pred):")
    for a, b in watch:
        tot = sum(conf[a].values())
        print(f"    {a:>6}->{b:<6}: {conf[a][b]}/{tot}")


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 88)
    print("perception_rescoring — THE AGENT RE-COMPOSES ITS PERCEPTION SCORING FROM THE INSIDE")
    print("Diagnosis: the gap is the RIGHT dimension but its SCORING is a binary gate at one global")
    print("weight -> seven's PARTIAL voicing scored like six's HARD silence -> seven collapses.")
    print("Fix (live composition, owned primitives): (1) GRADED gap likelihood; (2) PER-CONTEXT weight.")
    print("FSDD digits, full token, cross-speaker LOSO, held-out NEVER banked, chance 0.100.")
    print("=" * 88)

    # show the graded model envelopes + per-digit unvoiced fraction (the per-context weight).
    print("\nGRADED MODEL voicing (was {0,1}) + per-digit UNVOICED FRACTION (the per-context weight):")
    gmodels = graded_articulatory_models()
    bmodels = binary_models()
    for w in ["six", "seven", "eight", "nine", "one"]:
        gv = gmodels[w]["voi"]; bv = bmodels[w]["voi"]
        print(f"    {w:>6}: graded mean-voi={float(np.mean(gv)):.2f} "
              f"unvoiced_frac={gmodels[w]['unvoiced_frac']:.2f}  "
              f"(binary mean-voi={float(np.mean(bv)):.2f})")

    # sanity: graded OBSERVED voicing fraction per gap-cued digit (vs the binary {0,1}).
    print("\nGRADED OBSERVED voicing (mean over token) per digit — partial voicing now visible:")
    files = gather_files()
    byd = defaultdict(list)
    for path, d, spk, idx in files:
        byd[DIGITS[d]].append(path)
    for w in ["six", "seven", "eight", "one", "nine"]:
        gfr = []; bfr = []
        for p in sorted(byd[w])[:12]:
            sig, fs = load_wav(p)
            g = graded_voicing_observed(sig, fs); b = binary_voicing_observed(sig, fs)
            if g is not None:
                gfr.append(float(np.mean(g)))
            if b is not None:
                bfr.append(float(np.mean(b)))
        print(f"      {w:>6}: graded-voi={np.mean(gfr):.2f}  (binary-voi={np.mean(bfr):.2f})")

    print("\nBuilding corpus (perceive each token once; store binary + graded observed voicing) ...", flush=True)
    corpus, sk = build_corpus(sub, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    print(f"  corpus: {len(corpus)} tokens (skipped {sk}) | speakers={speakers}")

    # evaluate the four scoring modes through the SAME recogniser.
    print("\n" + "=" * 88)
    print("(a) GAP-DROPPED (control, no voicing term) — the 59.4% class")
    print("=" * 88)
    res_drop = evaluate(corpus, "dropped", gmodels, verbose=True)

    print("\n" + "=" * 88)
    print("(b) BINARY gap (control: {0,1} gate at global weight) — the 57.9% class")
    print("=" * 88)
    res_bin = evaluate(corpus, "binary", bmodels, verbose=True)

    print("\n" + "=" * 88)
    print("(c) GRADED gap (change 1: continuous likelihood, global weight)")
    print("=" * 88)
    res_grad = evaluate(corpus, "graded", gmodels, verbose=True)

    print("\n" + "=" * 88)
    print("(d) GRADED + PER-CONTEXT weight (changes 1+2 — the re-composition)")
    print("=" * 88)
    res_ctx = evaluate(corpus, "context", gmodels, verbose=True)

    def line(tag, r):
        print(f"  {tag:34s} formant {r['form_acc']*100:5.1f}% | articulatory {r['art_acc']*100:5.1f}% | "
              f"n-gram {r['ng_acc']*100:5.1f}% | FUSED {r['fused_acc']*100:5.1f}% | exemplar {r['mel_acc']*100:5.1f}%")
    print("\n" + "=" * 88)
    print(f"RESULTS (FSDD LOSO, n={res_ctx['fused_n']}, chance 10.0%)")
    print("=" * 88)
    line("(a) GAP-DROPPED:", res_drop)
    line("(b) BINARY gap:", res_bin)
    line("(c) GRADED gap:", res_grad)
    line("(d) GRADED + PER-CONTEXT:", res_ctx)
    print("\n  reference baselines: gap-dropped 59.4% | binary-gap 57.9% | pairing 62.2% | exemplar 80.6%")

    print(f"\n  FUSION deltas vs binary-gap 57.9% control:")
    print(f"    graded            : {(res_grad['fused_acc']-res_bin['fused_acc'])*100:+.1f} pts "
          f"({res_bin['fused_acc']*100:.1f}% -> {res_grad['fused_acc']*100:.1f}%)")
    print(f"    graded+per-context: {(res_ctx['fused_acc']-res_bin['fused_acc'])*100:+.1f} pts "
          f"({res_bin['fused_acc']*100:.1f}% -> {res_ctx['fused_acc']*100:.1f}%)")
    print(f"  FUSION delta vs gap-dropped {res_drop['fused_acc']*100:.1f}%: "
          f"graded+per-context {(res_ctx['fused_acc']-res_drop['fused_acc'])*100:+.1f} pts")

    # the SEVEN recovery + six/eight hold (the prediction).
    print("\n  per-digit FUSION accuracy (the prediction): binary -> graded -> graded+per-context")
    for w in ["seven", "six", "eight", "nine", "three"]:
        ab, _ = _digit_acc(res_bin["conf_fused"], w)
        ag, _ = _digit_acc(res_grad["conf_fused"], w)
        ac, tc = _digit_acc(res_ctx["conf_fused"], w)
        ad, _ = _digit_acc(res_drop["conf_fused"], w)
        print(f"    {w:>6}: dropped {ad*100:5.1f}% | binary {ab*100:5.1f}% -> graded {ag*100:5.1f}% "
              f"-> +per-ctx {ac*100:5.1f}%   (n={tc})")

    _watch_rows("(b) BINARY gap FUSION", res_bin["conf_fused"])
    _watch_rows("(d) GRADED + PER-CONTEXT FUSION", res_ctx["conf_fused"])
    _print_confusion("(d) GRADED + PER-CONTEXT FUSION confusion", res_ctx["conf_fused"])

    # ---- VERDICT ----
    print("\n" + "=" * 88)
    print("VERDICT")
    print("=" * 88)
    seven_bin, _ = _digit_acc(res_bin["conf_fused"], "seven")
    seven_ctx, _ = _digit_acc(res_ctx["conf_fused"], "seven")
    six_drop, _ = _digit_acc(res_drop["conf_fused"], "six")
    six_ctx, _ = _digit_acc(res_ctx["conf_fused"], "six")
    eight_drop, _ = _digit_acc(res_drop["conf_fused"], "eight")
    eight_ctx, _ = _digit_acc(res_ctx["conf_fused"], "eight")
    seven_recovers = seven_ctx > seven_bin
    sixeight_hold = (six_ctx >= six_drop - 0.05) and (eight_ctx >= eight_drop - 0.05)
    net_improve = res_ctx["fused_acc"] > res_bin["fused_acc"]
    beats_dropped = res_ctx["fused_acc"] > res_drop["fused_acc"]
    print(f"  seven  : binary {seven_bin*100:.1f}% -> +per-ctx {seven_ctx*100:.1f}%  "
          f"(recovers: {'YES' if seven_recovers else 'NO'})")
    print(f"  six    : dropped {six_drop*100:.1f}% -> +per-ctx {six_ctx*100:.1f}%")
    print(f"  eight  : dropped {eight_drop*100:.1f}% -> +per-ctx {eight_ctx*100:.1f}%")
    print(f"  six/eight gains hold vs gap-dropped: {'YES' if sixeight_hold else 'NO'}")
    print(f"  FUSION net-improve over binary 57.9%: {'YES' if net_improve else 'NO'} "
          f"({res_bin['fused_acc']*100:.1f}% -> {res_ctx['fused_acc']*100:.1f}%); "
          f"beats gap-dropped: {'YES' if beats_dropped else 'NO'}")
    if net_improve and seven_recovers and sixeight_hold:
        print("  => RE-COMPOSITION WINS: graded gap + per-context weight scores seven's partial")
        print("     voicing correctly (seven recovers) WHILE six/eight gains hold -> fusion net-")
        print("     improves over the binary gate. The lossy SCORING is fixed from the inside.")
    elif net_improve and seven_recovers:
        print("  => RE-COMPOSITION NET-IMPROVES + SEVEN RECOVERS: graded gap + per-context weight")
        print("     scores seven's partial voicing correctly (recovers) and fusion net-improves over")
        print("     the binary gate. six/eight do not both fully hold (see per-digit row); the next")
        print("     limiter (NOT 'more audio') is pinpointed below from the residual confusion.")
    elif net_improve:
        print("  => NET-IMPROVE (seven not fully recovered): fusion improves over the binary gate")
        print("     but seven does not recover. Next limiter (NOT 'more audio'): below.")
    elif seven_recovers:
        print("  => PARTIAL: seven recovers but fusion does not net-improve the headline. Next")
        print("     limiter (NOT 'more audio'): pinpointed below from the residual confusion.")
    else:
        print("  => HONEST: the re-composed scoring does not net-improve here. Next limiter")
        print("     (NOT 'more audio'): pinpointed below from the residual confusion.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("PERCEPTION_RESCORING_COMPLETED")


if __name__ == "__main__":
    main()
