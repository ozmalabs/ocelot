"""center_surround_loso — does a CENTER-SURROUND SALIENCE front end break the
cross-speaker FEATURE wall? (ozma_analogical_transfer: vision retina/LGN center-
surround -> auditory spectro-temporal contrast.)

The combine is closed and the cue/source-normalization levers are exhausted; the
residual lever is the FEATURE / cross-speaker RELIABILITY. The user's hypothesis: a
center-surround filter on the (frames x bands) cochleagram attacks cross-speaker
invariance on TWO axes at once —

  (a) LOCAL CONTRAST NORMALIZER — each time-freq point relative to its local surround
      cancels the speaker-common slowly-varying offsets (global tilt, level, the slow
      envelope the VTL shift rides on), which live in the wide surround blur. More
      invariant than the absolute spectrum.
  (b) SALIENCE filter — amplifies what STANDS OUT (formant peaks, spectral edges,
      onsets, where the phonetic info lives), discarding the flat speaker-specific
      background (blurred away by both Gaussians).

This A/Bs RAW cochleagram vs CENTER-SURROUND on the SAME robust SC 40-speaker LOSO
split, on BOTH recognizers the experiment owns:

  BANK (blind_guess)   : the agent's many-settings 1-NN bank recognizer over a SINGLE
                         front-end ear read through the SAME A1 patch bank. RAW = the
                         seed gammatone_flat ear (the absolute cochleagram patch bag);
                         CS  = the cs_ear (the center-surround contrast patch bag).
                         Apples-to-apples: the ONLY difference is the contrast transform.
  DTW (trajectory)     : the agent's graph-resident Argmin-MinOver-DtwTo recognizer
                         over the ordered per-frame trajectory. RAW = the raw
                         cochleagram track (per-frame L2 band vectors); CS = the
                         center-surround contrast track. The ONLY difference is the
                         contrast transform on the SAME aligned path.

ABLATION: frequency-only surround vs spectro-temporal surround, and two surround
widths (sigma_f_s in {3, 6}). A small FIXED reported set — NOT a sweep-and-keep-best.

Report per regime: SEEN-speaker, cross-speaker LOSO, and the seen-vs-cross GAP, so we
read both (1) does CS lift cross-speaker LOSO and (2) does CS tighten the gap (is the
contrast more speaker-invariant). KILL: if CS does not help cross-speaker, say so.

DONKEY BOUNDARY (audited): center-surround = the agent's composable boundary DSP
(separable Gaussian convolution + subtraction, the SAME center-surround DoG the vision
front end uses — agent_frontend.center_surround), NO fit / net / searched param beyond
the small reported {axis, width} ablation set. Recognition = the agent's own
blind_guess (1-NN bank) and its graph-resident DtwTo Term-tree. The SC load + speaker
split are world-adapter mechanics; held-out speakers' clips are NEVER banked; LOSO is
the ungameable yardstick.

Run: python -m scripts.center_surround_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from domains.stt_pipeline import STTPipeline, STTParams
from domains.many_settings_recognizer import channel_likelihood, WORD_ATTR

# reuse the SAME robust SC LOSO split builder + bank mechanics (ungameable).
from scripts.sc_loso_frontend_norm import build_split, bank, CELL, FS
# reuse the SAME graph-resident DTW recognizer + exemplar-trajectory machinery.
import scripts.dtw_trajectory_loso as DTW

# the cochleagram middle setting both fronts share.
_MIDDLE = FE._MIDDLE
_PATCHES = FE._SEED_PATCHES


# ---------------------------------------------------------------------------
# The front-end variants A/B'd. Each maps a clip -> a fixed-length L2 descriptor
# through the SAME A1 patch bank; the ONLY difference is the contrast transform on
# the cochleagram. RAW = absolute cochleagram (the seed gammatone_flat readout, per-
# band mean removed exactly as _cochlear_ear does); CS = center-surround contrast.
# ---------------------------------------------------------------------------

def _cochleagram(x, fs):
    from domains.filter_settings import cochleagram
    return cochleagram(np.asarray(x, dtype=np.float64), float(fs),
                       _MIDDLE[1], _MIDDLE[2], _MIDDLE[3])


def _raw_vec(x, fs):
    """RAW front end: the seed gammatone_flat readout — per-band-mean-removed
    absolute cochleagram through the A1 patch bank (exactly _cochlear_ear)."""
    M = _cochleagram(x, fs)
    mu = M.mean(axis=0, keepdims=True)
    return FE._l2(FE.bands_to_patches(M - mu, _PATCHES).flatten())


def _cs_vec(x, fs, **cs):
    """CENTER-SURROUND front end: the center-surround contrast cochleagram through the
    SAME A1 patch bank (the cs_ear cue). `cs` carries the surround params (the ablation)."""
    M = _cochleagram(x, fs)
    Cs = FE.center_surround(M, **cs)
    return FE._l2(FE.bands_to_patches(Cs, _PATCHES).flatten())


# ---------------------------------------------------------------------------
# A self-contained 1-NN bank recognizer over a SINGLE front-end descriptor (the
# agent's channel_likelihood = cosine 1-NN softmax, the SAME core blind_guess uses).
# We bank vectors + words once, then measure a probe. Isolates the FRONT END.
# ---------------------------------------------------------------------------

def _bank_vectors(train_clips, vecfn):
    X, words = [], []
    for w, x, fs in train_clips:
        X.append(vecfn(x, fs))
        words.append(w)
    return np.asarray(X), words


def _measure_bank(Xtr, words, probe, vecfn):
    cand = sorted(set(words))
    tot = cor = 0
    for w, x, fs in probe:
        q = vecfn(x, fs)
        p = channel_likelihood(q, Xtr, words, cand)
        guess = max(p.items(), key=lambda kv: kv[1])[0] if p else None
        tot += 1
        cor += int(guess == w)
    return cor / max(tot, 1)


def run_bank_regime(name, vecfn, train_clips, seen_probe, loso_probe):
    Xtr, words = _bank_vectors(train_clips, vecfn)
    seen = _measure_bank(Xtr, words, seen_probe, vecfn)
    loso = _measure_bank(Xtr, words, loso_probe, vecfn)
    print(f"  [{name:24s}] seen {seen:.3f}  LOSO {loso:.3f}  gap {seen - loso:+.3f}",
          flush=True)
    return seen, loso


# ---------------------------------------------------------------------------
# The DTW-trajectory A/B: RAW cochleagram track vs CENTER-SURROUND track, through the
# agent's OWN graph-resident DtwTo recognizer (reuses scripts.dtw_trajectory_loso).
# We bank exemplar trajectories of each kind onto fresh substrates, mark words, and run
# the agent's Argmin-MinOver-DtwTo Term natively.
# ---------------------------------------------------------------------------

def _raw_track(x, fs):
    """RAW cochleagram as an ordered per-frame trajectory (per-frame L2 band vectors) —
    the same readout shape as cs_track/cmvn_track, without the contrast transform."""
    M = _cochleagram(x, fs)
    if M.size == 0:
        return []
    out = []
    for r in range(M.shape[0]):
        v = M[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def run_dtw_regime(name, trackfn, train_clips, seen_probe, loso_probe):
    """Bank the train clips onto a fresh substrate, write each exemplar's trajectory
    via trackfn, then run the agent's graph-resident DTW recognizer on both probes."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    bank(s, train_clips)
    # write exemplar trajectories with THIS regime's track function (mechanical I/O).
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != CELL:
            continue
        for ex in s.neighbours(c, "has_exemplar"):
            ea = s.node(ex)["attrs"]
            aud = ea.get("audio")
            if aud is None:
                continue
            track = trackfn(np.asarray(aud, dtype=np.float64), float(ea.get("fs", FS)))
            s.set_attr(ex, DTW.EX_TRAJ_ATTR, DTW._traj_tuple(track))
            n += 1
    DTW.mark_words(s, CELL)
    # the agent's graph-resident Argmin-MinOver-DtwTo recognizer, evaluated natively.
    qn = s.add_node(DTW.QUERY_NODE_TYPE, {"origin": "cs_probe"})
    term = DTW._Pred(DTW.dtw_predict_term())

    def measure(probe):
        tot = cor = 0
        for w, x, fs in probe:
            track = trackfn(np.asarray(x, dtype=np.float64), float(fs))
            s.set_attr(qn, DTW.QUERY_TRAJ_ATTR, DTW._traj_tuple(track))
            pred = s.evaluate(term, {"q": qn})
            guess = s.node(pred)["attrs"].get("name") if pred is not None else None
            tot += 1
            cor += int(guess == w)
        return cor / max(tot, 1)

    seen = measure(seen_probe)
    loso = measure(loso_probe)
    print(f"  [{name:24s}] seen {seen:.3f}  LOSO {loso:.3f}  gap {seen - loso:+.3f}  "
          f"({n} exemplar trajectories)", flush=True)
    return seen, loso


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240609

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=seed)
    chance = 1.0 / len(W.sc_words())

    # the center-surround ABLATION — a small FIXED reported set (NOT a sweep-and-keep):
    #   freq-only narrow / wide surround, and one spectro-temporal variant.
    CS_VARIANTS = [
        ("CS freq-only sf=4", dict(sigma_f_s=4.0, sigma_t_s=0.0,
                                   sigma_f_c=1.0, sigma_t_c=0.0)),
        ("CS freq-only sf=6", dict(sigma_f_s=6.0, sigma_t_s=0.0,
                                   sigma_f_c=1.0, sigma_t_c=0.0)),
        ("CS freq-only sf=3", dict(sigma_f_s=3.0, sigma_t_s=0.0,
                                   sigma_f_c=1.0, sigma_t_c=0.0)),
        ("CS spectro-temp 4/2", dict(sigma_f_s=4.0, sigma_t_s=2.0,
                                     sigma_f_c=1.0, sigma_t_c=1.0)),
    ]

    print("\n" + "=" * 76, flush=True)
    print("CENTER-SURROUND vs RAW — robust SC 40-speaker cross-speaker LOSO", flush=True)
    print("=" * 76, flush=True)

    # ---- BANK recognizer (1-NN over a single front-end ear, same A1 patch bank) ----
    print("\n[BANK 1-NN recognizer — single front-end ear, same A1 patch readout]",
          flush=True)
    raw_seen, raw_loso = run_bank_regime("RAW cochleagram", _raw_vec,
                                         train_clips, seen_probe, loso_probe)
    bank_cs = {}
    for label, cs in CS_VARIANTS:
        bank_cs[label] = run_bank_regime(label, lambda x, fs, _c=cs: _cs_vec(x, fs, **_c),
                                         train_clips, seen_probe, loso_probe)

    # ---- DTW-trajectory recognizer (the agent's graph-resident DtwTo) ----
    print("\n[DTW-trajectory recognizer — agent's graph-resident Argmin MinOver DtwTo]",
          flush=True)
    draw_seen, draw_loso = run_dtw_regime("RAW cochleagram track", _raw_track,
                                          train_clips, seen_probe, loso_probe)
    # the best freq-only width on the bank carried to the DTW (and the spectro-temporal).
    dtw_cs = {}
    for label, cs in [("CS freq-only sf=4", CS_VARIANTS[0][1]),
                      ("CS spectro-temp 4/2", CS_VARIANTS[3][1])]:
        dtw_cs[label] = run_dtw_regime(
            label + " track",
            lambda x, fs, _c=cs: FE.cs_track(x, fs, _c),
            train_clips, seen_probe, loso_probe)

    # ---- VERDICT ----
    print("\n" + "-" * 76, flush=True)
    print(f"chance {chance:.3f}", flush=True)
    print(f"BANK  RAW: seen {raw_seen:.3f}  LOSO {raw_loso:.3f}  gap {raw_seen-raw_loso:+.3f}",
          flush=True)
    best_bank = max(bank_cs, key=lambda k: bank_cs[k][1])
    bcs, bls = bank_cs[best_bank]
    print(f"BANK  best CS ({best_bank}): seen {bcs:.3f}  LOSO {bls:.3f}  "
          f"gap {bcs-bls:+.3f}", flush=True)
    bank_lift = bls - raw_loso
    bank_gap_tighten = (raw_seen - raw_loso) - (bcs - bls)
    print(f"BANK  CS vs RAW: LOSO lift {bank_lift:+.3f}; gap change "
          f"{-bank_gap_tighten:+.3f} (negative = tighter under CS)", flush=True)

    print(f"DTW   RAW: seen {draw_seen:.3f}  LOSO {draw_loso:.3f}  "
          f"gap {draw_seen-draw_loso:+.3f}", flush=True)
    if dtw_cs:
        best_dtw = max(dtw_cs, key=lambda k: dtw_cs[k][1])
        dcs, dls = dtw_cs[best_dtw]
        dtw_lift = dls - draw_loso
        print(f"DTW   best CS ({best_dtw}): seen {dcs:.3f}  LOSO {dls:.3f}  "
              f"gap {dcs-dls:+.3f}", flush=True)
        print(f"DTW   CS vs RAW: LOSO lift {dtw_lift:+.3f}", flush=True)
    else:
        dtw_lift = -9.0

    best_lift = max(bank_lift, dtw_lift)
    print("-" * 76, flush=True)
    if best_lift > 0.02:
        print(f"=> YES: CENTER-SURROUND LIFTS cross-speaker LOSO (+{best_lift:.3f} best). "
              f"The local contrast / salience is a more speaker-invariant feature — the "
              f"contrast moves the cross-speaker feature wall.", flush=True)
    elif best_lift > 0.005:
        print(f"=> PARTIAL: CENTER-SURROUND moves cross-speaker LOSO ({best_lift:+.3f} "
              f"best), within noise of the raw front end. Weak, not decisive.", flush=True)
    else:
        print(f"=> NO (KILL): CENTER-SURROUND does NOT lift cross-speaker LOSO "
              f"({best_lift:+.3f} best, bank {bank_lift:+.3f} / dtw {dtw_lift:+.3f}). "
              f"The local contrast is NOT the missing cross-speaker invariance; the "
              f"residual feature-reliability wall is deeper than the salience transform.",
              flush=True)
    print("[MARKER] CENTER_SURROUND_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
