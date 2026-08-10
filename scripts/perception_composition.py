"""perception_composition — THE AGENT OWNS AND COMPOSES ITS PERCEPTION.

(memory ozma_agent_owns_its_perception). Perception is NOT a fixed pre-processing
pipeline. It is a GRAPH the agent composes from OWNED DSP primitives — and, crucially,
RE-COMPOSES from the inside when it notices a lossy transform dropped a discriminating
dimension. This is the SAME self-modification the agent already proved on its memory graph:
compose primitives into a graph, observe the limit, re-compose to fix it.

=========================================================================================
THE LOSSY TRANSFORM WE FIX FROM THE INSIDE (commit 6021611e)
=========================================================================================
The articulatory-Γ forward-model prong (scripts/articulatory_gamma.py) recovers /s/ from
its shadow (24.0% >> chance) and cleanly fixes its targeted frication confusions — but the
multi-pronged FUSION did NOT net-improve (59.4% vs the 62.2% formant-trajectory base, -2.8).
The DIAGNOSED cause is a LOSSY TRANSFORM on the OBSERVATION side: the pairing tracker
(formant_track) emits ONLY VOICED frames (it `continue`s every frame with energy below
VOICED_FLOOR), so the silence-then-frication GAP — the sharpest six/seven/stop-burst marker —
is DELETED before the articulatory prong can match it. The model SYNTHESISES a voicing/gap
envelope per digit (synth_voicing); the observed side has NO voicing channel to compare it to.
W_VOICING_SHADOW (=0.6) was DECLARED in articulatory_gamma but DEAD — there was no observed
gap to weight.

THE FIX IS NOT "more/better audio" (forbidden — the reader's surrender). The gap IS in the
8 kHz signal; the lossy TRANSFORM dropped it. We RE-COMPOSE the perception to OBSERVE it.

=========================================================================================
1. PERCEPTION PRIMITIVE LIBRARY (owned composable DSP ops; raw waveform in -> features out)
=========================================================================================
Each primitive has a clear signature and is a pure owned-numpy / owned-DSP transform — NO net,
NO .fit, NO gradient. They are the composable units; the perception is a GRAPH over them.

  load_raw_waveform(path)            -> (sig, fs)                    [world I/O boundary]
  voiced_formant_track(sig, fs)      -> (n_v x 3) Hz   | None        [pairing tracker, voiced-only]
  rel_formant_shadow(track)          -> (n_v x 3)                    [speaker-relative log, VTL-cancelled]
  trajectory_dynamics(sub, track)    -> (m x 9)                      [order-N over time, native]
  unvoiced_gap_detect(sig, fs)       -> (n_all,) voicing-envelope    [NEW — the DROPPED channel]
  log_mel_envelope(sig, fs)          -> (T x B)                      [full-envelope, exemplar baseline]

unvoiced_gap_detect is the re-composition's new primitive. It runs the SAME framing as the
tracker but over ALL frames and emits a per-frame voicing indicator (1=voiced above the floor,
0=unvoiced/silence below it) — i.e. exactly the gap structure the tracker threw away. It is
the OBSERVED counterpart to the model's synth_voicing.

=========================================================================================
2. COMPOSABLE PERCEPTION GRAPH (PerceptionGraph): a composed sequence of primitives, raw
   waveform -> the feature set the recogniser consumes. The agent PICKS the primitives.
=========================================================================================
A PerceptionGraph is just an ordered list of (name, primitive) the agent composes. Running it
on a raw token yields the named feature outputs. The point: the perception is COMPOSED and
RE-COMPOSABLE — not a fixed function. Two perceptions are composed here:

  (a) CURRENT  = load_raw -> voiced_formant_track -> rel_formant_shadow -> trajectory_dynamics
                 (+ log_mel for the exemplar baseline). NO gap channel — the lossy default.
  (b) RE-COMPOSED = the SAME graph PLUS unvoiced_gap_detect, so the gap envelope survives to
                 the articulatory comparison (the model's synth_voicing now has an observed
                 partner; W_VOICING_SHADOW becomes live).

=========================================================================================
3. DEMONSTRATE RE-COMPOSITION (fix the lossy transform from inside) + 4. VALIDATE
=========================================================================================
Feed each perception's features into the SAME articulatory/multi-pronged fusion recogniser and
recognise FSDD digits cross-speaker (LOSO, held-out NEVER banked, chance 0.10). Does observing
the gap improve six/seven/eight (the gap is their sharpest cue)?

DONKEY AUDIT:
  * DSP primitives = OWNED (numpy / the agent's pairing tracker / its log-mel front end). No net,
    no .fit, no gradient. unvoiced_gap_detect is the SAME owned framing+energy-gate as the tracker,
    inverted to emit the dropped frames.
  * Perception = a COMPOSED GRAPH of those primitives (PerceptionGraph). Re-composition = ADD a
    primitive + wire its output into the already-declared W_VOICING_SHADOW term. Nothing fitted.
  * RECOGNISER LOGIC UNCHANGED: the formant-trajectory prong (Viterbi-pairing DtwTo/MinOver/Argmin
    native Term), the fusion math (weighted-admissibility soft-excluder sum), the n-gram, the
    exemplar bank — ALL imported VERBATIM from scripts.articulatory_gamma / formant_trajectory_dynamics.
    The ONLY change between (a) and (b) is whether the gap channel is observed and weighted.
  * Exemplars / tau / n-gram / reliability weights = TRAIN speakers only; held-out NEVER banked.
  * CortexLoop + solve_for_n.py untouched.

PREDICTION: the gap shadow is the sharpest six/seven/stop-burst cue; observing it (re-composed
perception) lets the articulatory/frication evidence net-improve where the gap-dropped version
couldn't — six/seven/eight confusions tighten and fusion climbs over the gap-dropped 59.4%.
HONEST: if observing the gap still doesn't net-improve, we SAY SO and pinpoint the next limiter
(never "more audio"). The architectural point stands regardless: the perception is COMPOSED by
the agent and RE-COMPOSABLE from the inside.

Run:  PYTHONUNBUFFERED=1 python -m scripts.perception_composition
      PYTHONUNBUFFERED=1 python -m scripts.perception_composition --quick
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

# the 62.2% formant-trajectory prong: importing viterbi_pairing patches ftd.formant_track.
import scripts.viterbi_pairing as VP          # noqa: F401  (side effect: ftd.formant_track patched)
import scripts.formant_trajectory_dynamics as ftd
# Recogniser pieces come VERBATIM from formant_trajectory_dynamics / articulatory_gamma.
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
)
from scripts import mcu_infer as mi             # noqa: E402  (the ~83.5% exemplar bank, verbatim)
# NATIVE cognition Terms — the agent's graph-resident DECISIONS (substrate.evaluate). The d_A
# argmin (incl. the gap/voicing prong), the fusion argmax, and the k-NN mel vote are graph
# Terms, not Python. Transduction (tracker, Γ forward model, gap-envelope, mel) stays Python.
import domains.native_fusion as NF             # noqa: E402  fusion DECISION
import domains.native_cognition as NC          # noqa: E402  d_A (Argmin of DtwTo+Γ [+ voicing])
import domains.native_vote as NV               # noqa: E402  k-NN mel majority vote
import domains.many_settings_recognizer as MS  # noqa: E402  the _Pred evaluable-Term wrapper


# =========================================================================================
#  1. PERCEPTION PRIMITIVE LIBRARY — owned composable DSP ops (raw waveform in -> features out)
# =========================================================================================

def load_raw_waveform(path):
    """PRIMITIVE: world I/O boundary. raw .wav path -> (sig float64, fs). Owned (verbatim ftd)."""
    return load_wav(path)


def voiced_formant_track(sig, fs):
    """PRIMITIVE: (sig, fs) -> (n_voiced x 3) Hz formant track. The pairing tracker (Viterbi),
    voiced-only — this IS the lossy transform (drops sub-floor frames). Owned. Verbatim."""
    return ftd.formant_track(sig, fs)


def rel_formant_shadow(track):
    """PRIMITIVE: (n x 3) Hz track -> (n x 3) speaker-relative log shadow (VTL-cancelled). Owned."""
    return np.array([relative_formants_frame(f) for f in track])


def trajectory_dynamics(sub, track):
    """PRIMITIVE: (n x 3) Hz track -> (m x 9) order-N dynamics feature (native order-N). Owned."""
    return trajectory_feature(sub, track)


def log_mel_envelope(sig, fs, mel_ops):
    """PRIMITIVE: (sig, fs) -> (T x B) log-mel envelope for the exemplar baseline. Owned (verbatim)."""
    return mi.front_end(sig, fs, mel_ops)


def unvoiced_gap_detect(sig, fs):
    """PRIMITIVE (NEW — the DROPPED channel). (sig, fs) -> (n_all,) per-frame VOICING ENVELOPE
    in {0,1}: 1 where the frame energy is above the voicing floor (voiced), 0 below it
    (unvoiced frication / silence / the GAP). This is the OBSERVED counterpart of the model's
    synth_voicing — the silence-then-frication gap structure the voiced-only tracker deleted.

    Same OWNED framing + energy gate as formant_track / viterbi_formant_track (FRAME_MS, HOP_MS,
    VOICED_FLOOR), but it RETAINS every frame and emits its voiced/unvoiced label instead of
    `continue`-ing the sub-floor ones. No net, no fit. Returns None if the token is too short."""
    flen = int(fs * FRAME_MS / 1000)
    hop = int(fs * HOP_MS / 1000)
    if len(sig) < flen:
        return None
    starts = list(range(0, len(sig) - flen + 1, hop))
    energies = np.array([np.sqrt(np.mean(sig[s:s + flen] ** 2)) for s in starts])
    if energies.max() <= 1e-9:
        return None
    thr = VOICED_FLOOR * energies.max()
    return (energies >= thr).astype(np.float64)      # 1=voiced, 0=unvoiced/silence (the gap)


# =========================================================================================
#  2. COMPOSABLE PERCEPTION GRAPH — an ordered list of primitives the agent composes. Two
#  perceptions: CURRENT (gap-dropped) and RE-COMPOSED (+ unvoiced_gap_detect). The agent PICKS.
# =========================================================================================

class PerceptionGraph:
    """A composed graph of owned perception primitives, raw waveform -> the feature set the
    recogniser consumes. RE-COMPOSABLE: `observe_gap` toggles whether the unvoiced-gap primitive
    is in the graph. NOT a fixed pipeline — the agent composes (and re-composes) which ops run."""

    def __init__(self, observe_gap: bool):
        self.observe_gap = observe_gap
        # the composed primitive set (named) — this IS the graph the agent picked.
        self.primitives = [
            ("load_raw_waveform", load_raw_waveform),
            ("voiced_formant_track", voiced_formant_track),
            ("rel_formant_shadow", rel_formant_shadow),
            ("trajectory_dynamics", trajectory_dynamics),
            ("log_mel_envelope", log_mel_envelope),
        ]
        if observe_gap:
            # RE-COMPOSITION: add the dropped channel so the gap survives to the comparison.
            self.primitives.append(("unvoiced_gap_detect", unvoiced_gap_detect))

    def describe(self):
        return " -> ".join(name for name, _ in self.primitives)

    def perceive(self, sub, path, mel_ops):
        """Run the composed graph on one raw token. Returns the feature dict the recogniser reads:
        {traj, obs_rel, obs_voicing (None if not composed), mel}. Mechanical — no decisions."""
        sig, fs = load_raw_waveform(path)
        track = voiced_formant_track(sig, fs)
        if track is None:
            return None
        feat = trajectory_dynamics(sub, track)
        obs_rel = rel_formant_shadow(track)
        M = log_mel_envelope(sig, fs, mel_ops)
        if M.shape[0] < 2:
            return None
        obs_voicing = unvoiced_gap_detect(sig, fs) if self.observe_gap else None
        return {"traj": feat, "obs_rel": obs_rel, "obs_voicing": obs_voicing, "mel": M}


# =========================================================================================
#  3. RE-COMPOSITION wired into the articulatory distance: the gap channel becomes live.
#  This is the ONLY behavioural change between the two perceptions. The recogniser logic
#  (formant prong, fusion, n-gram, exemplar) is UNCHANGED — see donkey audit in the header.
# =========================================================================================

def native_d_a(art_sub, art_q, art_word_nodes, obs_rel, obs_voicing, observe_gap):
    """The per-digit articulatory admissibility d_A(w) as the agent's NATIVE Term (Argmin score),
    NOW with the OBSERVED gap channel when the perception is re-composed:
        d_A(w) = W_FORMANT_SHADOW * DtwTo(obs_rel, syn_rel(w)) + W_GAMMA * γ(w)
               [+ W_VOICING_SHADOW * DtwTo(obs_voi, syn_voi(w))   iff observe_gap].
    The voicing prong (the re-composition that makes W_VOICING_SHADOW live) is now a native
    DtwTo over the observed gap envelope vs digit w's synthesised voicing envelope — the
    ownership superset of the prior Python fixed-resample L1. When observe_gap is False the
    voicing term is OMITTED (the gap-dropped d_A). Returns {word: d_A}. Cognition is the native
    evaluator; the gap envelope itself is owned transduction."""
    w_voi = W_VOICING_SHADOW if observe_gap else 0.0
    return NC.native_articulatory_scores(
        art_sub, art_q, art_word_nodes, obs_rel, W_FORMANT_SHADOW, W_GAMMA, MS._Pred,
        obs_voi=(obs_voicing if observe_gap else None), w_voicing_shadow=w_voi)


# =========================================================================================
#  CORPUS — run a PerceptionGraph over the FSDD tokens (mechanical ingest, no agent decisions).
# =========================================================================================

def build_corpus(sub, perception: PerceptionGraph, seed=0, quick=False):
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
            out = perception.perceive(sub, p, mel_ops)
            if out is None:
                skipped += 1
                continue
            out["word"] = DIGITS[d]
            out["speaker"] = spk
            corpus.append(out)
    return corpus, skipped


def _measure_art_weight(corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap, chance):
    """Reliability of the ARTICULATORY prong on the TRAIN fold ONLY -> its fusion weight. The
    forward model needs no bank (it IS the knowledge), so no speaker-fold leakage is possible.
    Measured under the SAME perception (gap on/off) so the weight is honest for that perception.
    The per-token d_A is the agent's NATIVE Term."""
    c = t = 0
    for i in train_idx:
        true = corpus[i]["word"]
        ov = corpus[i]["obs_voicing"] if observe_gap else None
        d_a = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
        pred = min(DIGITS, key=lambda w: d_a[w])
        t += 1; c += int(pred == true)
    return reliability_weight(c / max(1, t), chance)


def evaluate(sub, corpus, observe_gap, verbose=True):
    """LOSO eval, fusion recogniser VERBATIM from articulatory_gamma. The ONLY difference vs the
    gap-dropped run is whether obs_voicing feeds articulatory_distance_recomposed (observe_gap)."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()
    models = articulatory_models()
    chance = 1.0 / len(DIGITS)

    # NATIVE d_A substrate (forward model AS GRAPH DATA: syn formant track + Γ + syn voicing).
    # Built ONCE; the voicing prong is present so the re-composed perception can use it.
    art_sub, art_q, art_word_nodes = NC.build_articulatory_substrate(
        Substrate, models, W_FORMANT_SHADOW, W_GAMMA, with_voicing=True)
    # NATIVE fusion substrate (one Concept/digit; the Argmax fusion Term). Built once.
    fuse_sub, fuse_nodes = NF.build_word_substrate(Substrate, DIGITS)

    # exemplar baseline plumbing (verbatim from ftd / mcu_infer).
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
    conf_form = {w: {u: 0 for u in DIGITS} for w in DIGITS}
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

        # n-gram prong: train-only digit unigram (verbatim).
        train_counts = Counter(corpus[i]["word"] for i in train_idx)
        tot = sum(train_counts.values())
        ng_logp = {w: math.log((train_counts.get(w, 0) + 1.0) / (tot + len(DIGITS))) for w in DIGITS}
        ng_top = max(ng_logp.values())
        ng_logp = {w: ng_logp[w] - ng_top for w in DIGITS}

        # tau scales (TRAIN only) — formant + articulatory (verbatim shape).
        h_sample = train_idx if len(train_idx) <= 80 else \
            [train_idx[j] for j in np.linspace(0, len(train_idx) - 1, 80).astype(int)]
        h_spreads = []
        for i in h_sample:
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            dh = _harmonic_dists(s, term, q_node, word_nodes)
            finite = [v for v in dh.values() if math.isfinite(v)]
            if len(finite) >= 2:
                h_spreads.append(max(finite) - min(finite))
        tau_h = max(float(np.median(h_spreads)) if h_spreads else 1.0, 1e-6)
        a_spreads = []
        for i in h_sample:
            ov = corpus[i]["obs_voicing"] if observe_gap else None
            da = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
            vals = list(da.values())
            a_spreads.append(max(vals) - min(vals))
        tau_a = max(float(np.median(a_spreads)) if a_spreads else 1.0, 1e-6)

        w_form = 1.0
        w_art = _measure_art_weight(
            corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap, chance)

        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]
        # NATIVE k-NN vote bank (one MelExemplar node per train exemplar). Built per fold.
        bank_mel_words = [w for _, w in bank_mel]
        vote_sub, _vwn, vote_ex_nodes = NV.build_vote_substrate(
            Substrate, DIGITS, bank_mel_words)

        s_fused_c = s_fused_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            ov = corpus[i]["obs_voicing"] if observe_gap else None
            # NATIVE d_A per word (Argmin score Term incl. the voicing prong when observe_gap).
            d_a = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_a = {w: -d_a[w] / tau_a for w in DIGITS}

            # formant prong = the agent's NATIVE DTW Argmin Term (the 62.2% recogniser).
            pn_form = s.evaluate(_P(term), {"q": q_node})
            pred_form = s.node(pn_form)["attrs"].get("name") if pn_form is not None else None
            form_n += 1
            if pred_form == true:
                form_c += 1
            if pred_form in DIGITS:
                conf_form[true][pred_form] += 1

            # articulatory prong ALONE = the NATIVE Argmin d_A decision (with the gap prong).
            pred_art = NC.native_articulatory_predict(
                art_sub, art_q, corpus[i]["obs_rel"], W_FORMANT_SHADOW, W_GAMMA, MS._Pred,
                obs_voi=ov, w_voicing_shadow=(W_VOICING_SHADOW if observe_gap else 0.0))
            art_n += 1; art_c += int(pred_art == true); conf_art[true][pred_art] += 1

            pred_ng = max(DIGITS, key=lambda w: ng_logp[w])
            ng_n += 1; ng_c += int(pred_ng == true)

            # FUSION: the NATIVE Argmax-of-Plus-of-Times Term (weighted-admissibility). Python
            # feeds the RAW prong log-admissibilities + ng-prior + w_art; the Term top-centres
            # (MaxOver), weights (Times), sums (Plus), and argmaxes — all native.
            pred_fused = NF.native_predict(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, MS._Pred)
            fused_n += 1; s_fused_t += 1
            if pred_fused == true:
                fused_c += 1; s_fused_c += 1
            conf_fused[true][pred_fused] += 1

            # exemplar baseline: owned log-mel banded-DTW distances -> NATIVE k-NN majority vote.
            dists = [mi.dtw(mel_normed[i], Mtr, mel_ops) for Mtr, _ in bank_mel]
            pred_mel = NV.native_vote(vote_sub, vote_ex_nodes, dists, mi.KNN_K, _P)
            mel_n += 1; mel_c += int(pred_mel == true)

        per_speaker[held] = s_fused_c / max(1, s_fused_t)
        if verbose:
            print(f"    held-out {held:10s}: fused {s_fused_c/max(1,s_fused_t):.3f} "
                  f"(n={s_fused_t}, w_art={w_art:.3f})", flush=True)

    return {
        "form_acc": form_c / max(1, form_n), "form_n": form_n,
        "art_acc": art_c / max(1, art_n), "art_n": art_n,
        "ng_acc": ng_c / max(1, ng_n), "ng_n": ng_n,
        "fused_acc": fused_c / max(1, fused_n), "fused_n": fused_n,
        "mel_acc": mel_c / max(1, mel_n), "mel_n": mel_n,
        "per_speaker": per_speaker,
        "conf_form": conf_form, "conf_art": conf_art, "conf_fused": conf_fused,
    }


def _into_six(conf):
    return sum(conf[w]["six"] for w in DIGITS if w != "six")


def _watch_rows(title, conf):
    watch = [("six", "two"), ("six", "nine"), ("six", "eight"), ("six", "seven"),
             ("seven", "six"), ("seven", "eight"), ("eight", "six"), ("eight", "seven"),
             ("three", "six"), ("six", "three"), ("eight", "three")]
    print(f"\n  {title} — six/seven/eight gap-cued confusions (true->pred):")
    for a, b in watch:
        tot = sum(conf[a].values())
        print(f"    {a:>6}->{b:<6}: {conf[a][b]}/{tot}")


def _digit_acc(conf, w):
    tot = sum(conf[w].values())
    return (conf[w][w] / tot if tot else 0.0), tot


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 84)
    print("perception_composition — THE AGENT OWNS AND COMPOSES (and RE-COMPOSES) ITS PERCEPTION")
    print("Owned DSP primitives -> a composed perception GRAPH -> fix a lossy transform from inside:")
    print("RE-COMPOSE to OBSERVE the unvoiced GAP the voiced-only tracker dropped (commit 6021611e).")
    print("FSDD digits, full token, cross-speaker LOSO, held-out NEVER banked, chance 0.100.")
    print("=" * 84)

    # ---- 1. STATE the perception primitive library (donkey audit) ----
    print("\n1. PERCEPTION PRIMITIVE LIBRARY (owned composable DSP; raw waveform in -> features out):")
    lib = [
        ("load_raw_waveform", "path -> (sig, fs)            [world I/O boundary]"),
        ("voiced_formant_track", "(sig,fs) -> (n_v x 3) Hz     [pairing tracker; VOICED-ONLY = the lossy transform]"),
        ("rel_formant_shadow", "(n x 3) -> (n x 3)           [speaker-relative log; VTL-cancelled]"),
        ("trajectory_dynamics", "(sub,track) -> (m x 9)       [order-N over time, native Rust eval]"),
        ("log_mel_envelope", "(sig,fs) -> (T x B)          [full-envelope; exemplar baseline]"),
        ("unvoiced_gap_detect", "(sig,fs) -> (n_all,) in {0,1} [NEW — the DROPPED voicing/gap channel]"),
    ]
    for name, sig in lib:
        print(f"    {name:22s} {sig}")
    print("  audit: all OWNED numpy/DSP — no net, no .fit, no gradient. unvoiced_gap_detect is the")
    print("         SAME framing+energy-gate as the tracker, inverted to KEEP the dropped frames.")

    # ---- 2. COMPOSE the two perception graphs (the agent picks the ops) ----
    P_current = PerceptionGraph(observe_gap=False)
    P_recomposed = PerceptionGraph(observe_gap=True)
    print("\n2. COMPOSABLE PERCEPTION GRAPH (composed, RE-COMPOSABLE — not a fixed pipeline):")
    print(f"    (a) CURRENT     : {P_current.describe()}")
    print(f"    (b) RE-COMPOSED : {P_recomposed.describe()}")
    print("    RE-COMPOSITION = add unvoiced_gap_detect + wire its envelope into the (already-")
    print(f"    declared, previously DEAD) W_VOICING_SHADOW={W_VOICING_SHADOW} articulatory term, so the")
    print("    silence-then-frication GAP shadow SURVIVES to the comparison. Recogniser UNCHANGED.")

    # show the gap is real: voiced-fraction the tracker would keep, per gap-cued digit.
    print("\n    sanity — observed voiced-fraction (1=all kept by tracker; <1 = gap frames the")
    print("    voiced-only track DROPS) on a few tokens per gap-cued digit:")
    files = gather_files()
    byd = defaultdict(list)
    for path, d, spk, idx in files:
        byd[DIGITS[d]].append(path)
    for w in ["six", "seven", "eight", "one", "nine"]:
        fr = []
        for p in sorted(byd[w])[:8]:
            sig, fs = load_raw_waveform(p)
            v = unvoiced_gap_detect(sig, fs)
            if v is not None:
                fr.append(float(np.mean(v)))
        print(f"      {w:>6}: voiced-frac={np.mean(fr):.2f}  (gap frames dropped = {(1-np.mean(fr))*100:.0f}%)")

    # ---- build corpora (one perceive pass each) ----
    print("\nBuilding corpora (running each composed perception graph over the tokens) ...", flush=True)
    corpus_cur, sk1 = build_corpus(sub, P_current, seed=0, quick=quick)
    corpus_rec, sk2 = build_corpus(sub, P_recomposed, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus_cur))
    print(f"  CURRENT corpus    : {len(corpus_cur)} tokens (skipped {sk1})")
    print(f"  RE-COMPOSED corpus: {len(corpus_rec)} tokens (skipped {sk2}) | speakers={speakers}")

    # ---- 3+4. evaluate both perceptions through the SAME recogniser ----
    print("\n" + "=" * 84)
    print("(a) CURRENT perception — GAP-DROPPED articulatory fusion (the 59.4% class)")
    print("=" * 84)
    res_cur = evaluate(sub, corpus_cur, observe_gap=False, verbose=True)

    print("\n" + "=" * 84)
    print("(b) RE-COMPOSED perception — GAP-OBSERVED (unvoiced_gap_detect wired in)")
    print("=" * 84)
    res_rec = evaluate(sub, corpus_rec, observe_gap=True, verbose=True)

    # ---- report ----
    def line(tag, r):
        print(f"  {tag:30s} formant {r['form_acc']*100:5.1f}% | articulatory {r['art_acc']*100:5.1f}% | "
              f"n-gram {r['ng_acc']*100:5.1f}% | FUSED {r['fused_acc']*100:5.1f}% | exemplar {r['mel_acc']*100:5.1f}%")
    print("\n" + "=" * 84)
    print("RESULTS (FSDD LOSO, n per column below, chance 10.0%)")
    print("=" * 84)
    print(f"  n = {res_cur['fused_n']} (current) / {res_rec['fused_n']} (re-composed)")
    line("(a) CURRENT  (gap-dropped):", res_cur)
    line("(b) RE-COMPOSED (gap-obs):", res_rec)
    print(f"\n  reference baselines: articulatory-fusion gap-dropped 59.4% | Viterbi-pairing 62.2% | exemplar 83.5%")

    d_fused = (res_rec["fused_acc"] - res_cur["fused_acc"]) * 100
    print(f"\n  FUSION delta (re-composed - current): {d_fused:+.1f} pts "
          f"({res_cur['fused_acc']*100:.1f}% -> {res_rec['fused_acc']*100:.1f}%)")

    # confusions: current vs re-composed (the gap-cued ones)
    _watch_rows("(a) CURRENT gap-dropped FUSION", res_cur["conf_fused"])
    _watch_rows("(b) RE-COMPOSED gap-observed FUSION", res_rec["conf_fused"])

    print("\n  per-digit FUSION accuracy six/seven/eight (gap-cued), current -> re-composed:")
    for w in ["six", "seven", "eight"]:
        ac, tc = _digit_acc(res_cur["conf_fused"], w)
        ar, tr = _digit_acc(res_rec["conf_fused"], w)
        print(f"    {w:>6}: {ac*100:5.1f}% -> {ar*100:5.1f}%   (n={tr})")

    print(f"\n  SIX-SINK (non-six wrongly -> six): current {_into_six(res_cur['conf_fused'])}"
          f"  ->  re-composed {_into_six(res_rec['conf_fused'])}")

    # full confusion matrices for the record.
    _print_confusion("(b) RE-COMPOSED gap-observed FUSION confusion", res_rec["conf_fused"])

    # ---- VERDICT ----
    print("\n" + "=" * 84)
    print("VERDICT")
    print("=" * 84)
    gap_improves = res_rec["fused_acc"] > res_cur["fused_acc"]
    beats_dropped_class = res_rec["fused_acc"] > 0.594
    # gap-cued digit improvement
    sse_cur = sum(_digit_acc(res_cur["conf_fused"], w)[0] for w in ["six", "seven", "eight"]) / 3
    sse_rec = sum(_digit_acc(res_rec["conf_fused"], w)[0] for w in ["six", "seven", "eight"]) / 3
    print(f"  architecture: perception is COMPOSED from owned primitives and RE-COMPOSED from the")
    print(f"                inside (added unvoiced_gap_detect; recogniser logic byte-unchanged). PROVEN.")
    print(f"  gap-cued six/seven/eight mean FUSION acc: {sse_cur*100:.1f}% -> {sse_rec*100:.1f}%  "
          f"({(sse_rec-sse_cur)*100:+.1f} pts)")
    print(f"  fusion net delta: {d_fused:+.1f} pts; observing the gap improves fusion: "
          f"{'YES' if gap_improves else 'NO'}")
    if gap_improves and beats_dropped_class:
        print("  => RE-COMPOSITION WINS: observing the unvoiced gap (the agent re-composed its")
        print("     perception from the inside) lets the articulatory/frication evidence net-improve")
        print("     where the gap-dropped perception could not. The lossy transform is fixed from inside.")
    elif sse_rec > sse_cur:
        print("  => PARTIAL: the gap channel tightens the six/seven/eight gap-cued confusions it")
        print("     targets, but fusion does not net-improve the headline. Next limiter (NOT 'more")
        print("     audio'): the articulatory prong's voicing envelope is coarse (binary energy gate);")
        print("     the sharpening is a graded frication/voicing model + front-cavity /s/-/th/ split.")
    else:
        print("  => HONEST: observing the gap does not net-improve cross-speaker here. The gap channel")
        print("     is real and survives the re-composition, but the binary voicing envelope is too")
        print("     coarse a discriminator at this fusion weight. Next limiter (NOT more audio): a")
        print("     graded gap/frication shadow + per-prong gap-localised weighting. The ARCHITECTURAL")
        print("     point stands: the perception is composed by the agent and re-composable from inside.")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("PERCEPTION_COMPOSITION_COMPLETED")


if __name__ == "__main__":
    main()
