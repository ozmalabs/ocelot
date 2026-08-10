"""STAGE 4 — CLOSE THE GROUNDING LOOP by FUSING the two bases (correctness-keyed trust).

THE DECISION (docs/grounding_fusion.md, Phase 1): the Stage-3 speaker-INVARIANT base
collapses the agent's own synthetic personas to "three" (17.5%) while the OLD pre-curriculum
base keeps the word-discriminative cues it discarded (62.5%) — but the invariant base's
discard is what BOUGHT the +18.9% real-speech cross-speaker d'. There is NO single rep that
is both maximally invariant (real-speech win) AND maximally word-discriminative (synthetic-
persona win): that is the self-imposed-wall = one-ear lesson ([[ozma_wall_is_self_imposed]]).
So the two are COMPLEMENTARY EARS — fuse them, do NOT try to "fix the rep" (which would
un-discard the cues that bought the d').

This script re-runs the EXACT Stage-4 grounding harness (same projection FORWARD = owned
articulatory voice, persona f0/q/vtl; same FSDD train/held split; same DEFAULT_PERSONAS; same
real-speech medoid prototypes for the invariant base; same OLD NativeRecogniser for the
contrast) — and swaps ONLY the inverse to a FUSED inverse that combines the two bases' per-word
distance fields via the agent's OWNED correctness-keyed-trust fusion Term
(domains.native_fusion.fusion_score_term_ckt). Apples-to-apples with the 17.5%/62.5% run.

THE FUSION (owned primitive, ZERO new code in native_fusion):
    score(w) = old_fused_c[w]                                          # ANCHOR — the word-discriminative
                                                                       #   OLD base, full weight, ALWAYS
             + w_inv * min(1,conf_inv/cref) * prec_inv[argmax_inv] * inv_c[w]   # AUX — the invariant base,
                                                                       #   correctness-keyed + margin trust
             + ng_logp[w]                                             # train unigram prior
    predict  = Argmax_w score(w)

  * ANCHOR field LOG_A_H_ATTR = the OLD base's INTERNAL fused log-admissibility field
    (top-centred log_a_h + w_art*log_a_a + ng — the SAME 62.5% word-discriminative decision,
    consumed here as ONE combined anchor field; never re-weighted, the safety prong).
  * AUX field LOG_A_A_ATTR = the NEW invariant base's per-word field log_a_inv = -DtwTo/tau_inv
    to the real-speech medoid prototypes (the persona-robust prong).
  * prec_inv[w] = the invariant prong's TRAIN per-asserted-digit PRECISION, measured on FSDD
    TRAIN tokens ONLY (held-out speaker NEVER used) — a MEASUREMENT of its track record, not a
    fit/sweep. The invariant prong collapses onto "three" -> low prec_inv["three"] -> its whole
    excluder is scaled down on tokens it asserts "three", catching exactly the confident-wrong
    collapse the persona round-trip exposes; where it confidently-asserts a digit it is reliable
    on (high prec) it HELPS.
  * conf_ref = the invariant prong's median TRAIN margin (a Lit, per the design).

DONKEY AUDIT (file:line)
==============================================================================
  * forward = owned articulatory synth (UNCHANGED): domains/projection.py:120 ->
    scripts/articulatory_gamma. NO TTS net.
  * the two prongs = the EXACT Stage-4 inverses: OLD NativeRecogniser
    (scripts/speech_world_native.py:149) + InvariantInverse (scripts/stage4_grounding.py:123).
    Each produces a per-word DISTANCE FIELD over the SAME 10 digits (prong-compatible).
  * fusion = domains.native_fusion.fusion_score_term_ckt (correctness-keyed trust), evaluated
    by substrate.evaluate (native Rust). ZERO new primitives, ZERO new Rust, ZERO new code in
    native_fusion. NO net, NO .fit, NO gradient, NO sweep-to-fit. prec_inv + conf_ref are
    train-only MEASUREMENTS. CortexLoop / solve_for_n / runners UNTOUCHED.
  * READINESS = STRUCTURAL round-trip grounding coherence (speak W -> hear -> recognise W; per-
    persona), NOT a held-out LOSO accuracy.

Run:  PYTHONUNBUFFERED=1 python -m scripts.stage4_fusion
      PYTHONUNBUFFERED=1 python -m scripts.stage4_fusion --quick
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

import domains.native_cognition as NC
import domains.native_fusion as NF
import domains.many_settings_recognizer as MS
import domains.projection as PROJ
import scripts.articulatory_gamma as AG
import scripts.formant_trajectory_dynamics as ftd
from scripts.formant_trajectory_dynamics import DIGITS
from domains.persona_speech_world import DEFAULT_PERSONAS
from scripts.stage1_coarse_recognition_check import _Pred

# the two inverses + the shared setup — imported VERBATIM from the Stage-4 harness so this is
# apples-to-apples with the 17.5% / 62.5% run.
from scripts.speech_world_native import (
    gather_fsdd, build_native_banks, NativeRecogniser,
)
from scripts.stage4_grounding import (
    build_invariant_prototypes, InvariantInverse, invariant_track, _tuple,
    run_loop, _acc, _print_conf,
)


# ===========================================================================
#  OLD-base per-word FIELDS (the anchor prong's log-admissibility field).
# ===========================================================================
#  The OLD NativeRecogniser.recognise returns only argmax predictions; the fusion needs the
#  per-word FIELD. We reproduce the SAME field it builds INTERNALLY (its lines 261-277): the
#  formant-traj DTW prong log_a_h and the articulatory prong log_a_a, combined into the OLD
#  fused log-admissibility (top-centred log_a_h + w_art*log_a_a + ng). This is world-adapter
#  glue — it reads the OLD recogniser's OWN prong machinery, makes NO new decision.

def _old_prong_fields(rec, sig):
    """The OLD base's per-word (log_a_h, log_a_a) fields for a raw signal, exactly as
    NativeRecogniser.recognise computes them. Returns (log_a_h, log_a_a) dicts or None."""
    f = rec.features(sig)
    if f is None:
        return None
    feat, obs_rel, _M = f
    rec.s.set_attr(rec.q_node, ftd.Q_ATTR, ftd._traj_tuple(feat))
    d_h = AG._harmonic_dists(rec.s, rec.term, rec.q_node, rec.word_nodes)
    d_a = NC.native_articulatory_scores(
        rec.art_sub, rec.art_q, rec.art_word_nodes, obs_rel,
        AG.W_FORMANT_SHADOW, AG.W_GAMMA, MS._Pred)
    log_a_h = {w: (-d_h[w] / rec.tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
    log_a_a = {w: -d_a[w] / rec.tau_a for w in DIGITS}
    return log_a_h, log_a_a


def _old_fused_field(rec, log_a_h, log_a_a):
    """The OLD base's INTERNAL fused log-admissibility field, per word — the SAME combination
    NF.native_predict argmaxes (top-centred log_a_h + w_art*top_centred log_a_a + ng_logp). This
    is the OLD 62.5% word-discriminative decision EXPRESSED AS ONE COMBINED ANCHOR FIELD for the
    meta-fusion. Pure reproduction of the OLD field; no new decision."""
    top_h = max(log_a_h.values())
    top_a = max(log_a_a.values())
    return {w: (log_a_h[w] - top_h)
               + rec.w_art * (log_a_a[w] - top_a)
               + rec.ng_logp[w]
            for w in DIGITS}


# ===========================================================================
#  INVARIANT-base per-word FIELD (the aux prong) + its train precision table.
# ===========================================================================

def _inv_field(inverse, sig, fs, tau_inv):
    """The invariant base's per-word log-admissibility field: -DtwTo(track, prototype)/tau_inv
    for each digit (higher = more admissible). Returns {word: log_a} or None."""
    d = inverse.distances(np.asarray(sig, dtype=np.float64), fs)
    if d is None:
        return None
    return {w: -d[w] / tau_inv for w in DIGITS}


def measure_tau_inv(inverse, train_files, per_word, fs, n_sample=80):
    """tau_inv = median across-digit spread of the invariant base's per-word DtwTo distances
    over a sample of real TRAIN tokens (the same scale-normaliser pattern the OLD base uses for
    tau_h/tau_a). A MEASUREMENT, not a fit."""
    by_digit = defaultdict(list)
    for path, d, spk, idx in train_files:
        by_digit[d].append(path)
    paths = []
    for d in sorted(by_digit):
        ps = sorted(by_digit[d])
        if per_word is not None:
            ps = ps[:per_word]
        paths.extend(ps)
    if len(paths) > n_sample:
        paths = [paths[j] for j in np.linspace(0, len(paths) - 1, n_sample).astype(int)]
    spreads = []
    for p in paths:
        sig, fsx = ftd.load_wav(p)
        dd = inverse.distances(np.asarray(sig, dtype=np.float64), fsx)
        if dd is None:
            continue
        vals = [v for v in dd.values() if math.isfinite(v)]
        if len(vals) >= 2:
            spreads.append(max(vals) - min(vals))
    return max(float(np.median(spreads)) if spreads else 1.0, 1e-6)


def measure_inv_precision_and_confref(inverse, train_files, per_word, fs, tau_inv):
    """On FSDD TRAIN tokens ONLY (held-out speaker NEVER used): measure the invariant prong's
    per-asserted-digit PRECISION prec_inv[d] = P(true==d | invariant prong argmaxes d), and its
    median per-token confidence (mean depth of the top-centred field) = conf_ref. Both are
    train-only MEASUREMENTS of the prong's track record / typical margin — no fit, no sweep, no
    test peeking. Returns (prec_inv dict, conf_ref float)."""
    by_digit = defaultdict(list)
    for path, d, spk, idx in train_files:
        by_digit[d].append(path)
    # per-asserted-digit confusion: assert_counts[asserted][true] -> count.
    assert_true = {w: Counter() for w in DIGITS}
    margins = []
    for d in sorted(by_digit):
        true_w = DIGITS[d]
        ps = sorted(by_digit[d])
        if per_word is not None:
            ps = ps[:per_word]
        for p in ps:
            sig, fsx = ftd.load_wav(p)
            field = _inv_field(inverse, sig, fsx, tau_inv)
            if field is None:
                continue
            asserted = max(field, key=field.get)
            assert_true[asserted][true_w] += 1
            top = max(field.values())
            margins.append(-float(np.mean([field[w] - top for w in DIGITS])))
    prec_inv = {}
    for w in DIGITS:
        tot = sum(assert_true[w].values())
        prec_inv[w] = (assert_true[w][w] / tot) if tot > 0 else 0.0
    conf_ref = max(float(np.median(margins)) if margins else 1.0, 1e-6)
    return prec_inv, conf_ref


# ===========================================================================
#  THE FUSED INVERSE — combine the two bases' fields via the owned ckt Term.
# ===========================================================================

class FusedInverse:
    """The fused grounding inverse: feed the OLD base's fused field (ANCHOR) and the invariant
    base's field (AUX, correctness-keyed-trust) into the agent's OWNED native_fusion
    correctness-keyed Term, return the argmax word. Every fusion decision is a graph Term
    evaluated by substrate.evaluate. Python is world-adapter glue only."""

    def __init__(self, old_rec, inv_inverse, fs, tau_inv, prec_inv, conf_ref, w_inv,
                 combiner="product"):
        self.old = old_rec
        self.inv = inv_inverse
        self.fs = fs
        self.tau_inv = tau_inv
        self.prec_inv = prec_inv
        self.conf_ref = conf_ref
        self.w_inv = w_inv
        self.combiner = combiner
        # the candidate-word substrate the ckt Term argmaxes over (is_word==1).
        self.fuse_sub, self.fuse_nodes = NF.build_word_substrate(Substrate, DIGITS)
        # bake the train precision table once (per-word PREC_A_ATTR — train-only constant).
        for w, nid in self.fuse_nodes.items():
            self.fuse_sub.set_attr(nid, NF.PREC_A_ATTR, float(prec_inv[w]))

    def recognise(self, sig):
        sig = np.asarray(sig, dtype=np.float64)
        old_f = _old_prong_fields(self.old, sig)
        inv_log = _inv_field(self.inv, sig, self.fs, self.tau_inv)
        if old_f is None or inv_log is None:
            return None
        log_a_h, log_a_a = old_f
        anchor = _old_fused_field(self.old, log_a_h, log_a_a)   # OLD fused -> ANCHOR field
        # feed ANCHOR (as log_a_h slot), AUX=invariant (as log_a_a slot), ng=train unigram.
        for w, nid in self.fuse_nodes.items():
            self.fuse_sub.set_attr(nid, NF.LOG_A_H_ATTR, float(anchor[w]))
            self.fuse_sub.set_attr(nid, NF.LOG_A_A_ATTR, float(inv_log[w]))
            self.fuse_sub.set_attr(nid, NF.NG_LOGP_ATTR, float(self.old.ng_logp[w]))
        term = MS._Pred(NF.predict_fusion_term_ckt(self.w_inv, self.conf_ref, self.combiner))
        pick = self.fuse_sub.evaluate(term, {})
        return self.fuse_sub.node(pick)["attrs"]["name"]


# ===========================================================================
#  MAIN — re-run the Stage-4 loop with the FUSED inverse (apples-to-apples).
# ===========================================================================

def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    per_word = 12 if quick else None
    fs = 8000

    print("=" * 80)
    print("STAGE 4 — FUSE the two bases (correctness-keyed trust), then close the grounding loop")
    print("anchor = OLD pre-curriculum base (word-discriminative, 62.5%) at FULL weight")
    print("aux    = Stage-3 SPEAKER-INVARIANT base (persona-robust, 17.5%) at ckt trust")
    print("fusion = owned native_fusion.fusion_score_term_ckt (ZERO new code)")
    print("=" * 80)

    files = gather_fsdd()
    speakers = sorted(set(f[2] for f in files))
    held = "jackson"
    train_files = [f for f in files if f[2] != held]
    print(f"\nspeakers: {speakers} | banks/prototypes from {len(speakers)-1} train speakers "
          f"(held: {held}); TEST audio = the agent's OWN projection-spoken speech.")

    # --- the NEW invariant inverse (Stage-3 base) — IDENTICAL build to stage4_grounding ---
    print("\nbuilding the Stage-3 INVARIANT base (VTL-norm + dynamic gesture, real-speech "
          "medoids) ...", flush=True)
    prototypes = build_invariant_prototypes(train_files, per_word=per_word)
    inv_inverse = InvariantInverse(prototypes)

    # --- the OLD pre-curriculum inverse — IDENTICAL build to stage4_grounding ---
    print("building the OLD pre-curriculum inverse (formant-traj + mel k-NN + articulatory) ...",
          flush=True)
    old_bank = build_native_banks(train_files, per_word=per_word, verbose=False)
    old_rec = NativeRecogniser(old_bank)

    # --- the T3 projection (speak path — UNCHANGED owned voice) ---
    sub = Substrate()
    proj = PROJ.speech_projection(AG, old_rec, prong="fused")

    # --- measure the invariant prong's scale, train precision table, and conf_ref (TRAIN only) ---
    print("\nmeasuring the invariant prong's tau / train precision / conf_ref (train-only) ...",
          flush=True)
    tau_inv = measure_tau_inv(inv_inverse, train_files, per_word, fs)
    prec_inv, conf_ref = measure_inv_precision_and_confref(
        inv_inverse, train_files, per_word, fs, tau_inv)
    # the invariant prong's GLOBAL reliability weight = its overall train accuracy vs chance
    # (the same reliability_weight the OLD base uses for w_art). A train MEASUREMENT.
    chance = 1.0 / len(DIGITS)
    # measure the prong's overall train accuracy directly for w_inv.
    n_c = n_t = 0
    by_digit = defaultdict(list)
    for path, d, spk, idx in train_files:
        by_digit[d].append(path)
    for d in sorted(by_digit):
        ps = sorted(by_digit[d])
        if per_word is not None:
            ps = ps[:per_word]
        for p in ps:
            sig, fsx = ftd.load_wav(p)
            fld = _inv_field(inv_inverse, sig, fsx, tau_inv)
            if fld is None:
                continue
            n_t += 1
            if max(fld, key=fld.get) == DIGITS[d]:
                n_c += 1
    inv_train_acc = n_c / max(1, n_t)
    w_inv = AG.reliability_weight(inv_train_acc, chance)
    print(f"  tau_inv={tau_inv:.4f}  conf_ref={conf_ref:.4f}  invariant train acc={inv_train_acc:.3f}"
          f"  -> w_inv={w_inv:.3f}", flush=True)
    print(f"  invariant prong TRAIN precision per asserted digit (the correctness key):")
    for w in DIGITS:
        print(f"    asserts {w:>6}: prec {prec_inv[w]:.3f}", flush=True)

    # --- the FUSED inverse ---
    fused = FusedInverse(old_rec, inv_inverse, fs, tau_inv, prec_inv, conf_ref, w_inv,
                         combiner="product")

    # ============================================================
    #  RUN THE LOOP — NEW (invariant), OLD, FUSED — on the SAME spoken audio.
    # ============================================================
    print("\n" + "=" * 80)
    print("CLOSED LOOP: speak -> hear -> recognise   (NEW invariant / OLD / FUSED)")
    print("=" * 80)
    res_new = run_loop(proj, lambda a: inv_inverse.recognise(a, fs), sub, fs,
                       DEFAULT_PERSONAS, "INV", verbose=False)
    res_old = run_loop(proj, lambda a: (old_rec.recognise(a) or {}).get("fused"),
                       sub, fs, DEFAULT_PERSONAS, "OLD", verbose=False)
    res_fus = run_loop(proj, lambda a: fused.recognise(a), sub, fs,
                       DEFAULT_PERSONAS, "FUS", verbose=False)

    # ============================================================
    #  REPORT.
    # ============================================================
    print("\n" + "=" * 80)
    print("ROUND-TRIP GROUNDING (the agent's OWN projection-spoken speech)")
    print("=" * 80)
    print(f"  attempts (digit x persona, voiced): {res_fus['n']}   unvoiced: {res_fus['unvoiced']}")
    print(f"\n  *** FUSED (anchor OLD + aux invariant, ckt)  : {_acc(res_fus)*100:5.1f}%  "
          f"(n={res_fus['n']})")
    print(f"      NEW base (Stage-3 invariant) alone       : {_acc(res_new)*100:5.1f}%  "
          f"(n={res_new['n']})  [prior 17.5%]")
    print(f"      OLD base (pre-curriculum) alone          : {_acc(res_old)*100:5.1f}%  "
          f"(n={res_old['n']})  [prior 62.5%]")

    print(f"\n  per-persona round-trip (invariance across f0/q/vtl):")
    print(f"    {'persona':<10} {'f0':>5} {'vtl':>5}   {'FUSED':>7} {'NEW':>7} {'OLD':>7}")
    for name, f0, q, vtl in DEFAULT_PERSONAS:
        af = _acc(res_fus['per_persona'][name])
        an = _acc(res_new['per_persona'][name])
        ao = _acc(res_old['per_persona'][name])
        print(f"    {name:<10} {f0:>5.0f} {vtl:>5.2f}   {af*100:>6.1f}% {an*100:>6.1f}% "
              f"{ao*100:>6.1f}%")

    _print_conf("FUSED round-trip confusion (collapse broken?)", res_fus["conf"])

    sink = Counter()
    for w in DIGITS:
        for u in DIGITS:
            if u != w:
                sink[u] += res_fus["conf"][w][u]
    top_sink = sink.most_common(1)
    if top_sink:
        print(f"\n  largest wrong-sink (FUSED): '{top_sink[0][0]}' absorbs "
              f"{top_sink[0][1]} of the wrong predictions")

    # ============================================================
    #  VERDICT — did fusion move toward the OLD base while keeping the invariant prong in play?
    # ============================================================
    new_acc = _acc(res_new)
    old_acc = _acc(res_old)
    fus_acc = _acc(res_fus)
    chance = 0.10
    moves_toward_old = fus_acc >= new_acc            # at least recovers from the collapse
    matches_or_beats_old = fus_acc >= old_acc - 0.025
    pa = np.asarray([_acc(res_fus['per_persona'][name]) for name, *_ in DEFAULT_PERSONAS])
    persona_min = float(pa.min()) if pa.size else 0.0
    coherent = persona_min > chance

    print("\n" + "=" * 80)
    print("VERDICT — did the fusion close / move toward the OLD base?")
    print("=" * 80)
    print(f"  FUSED {fus_acc*100:.1f}%   NEW(invariant) {new_acc*100:.1f}%   OLD {old_acc*100:.1f}%")
    print(f"  recovers from the invariant collapse (FUSED >= NEW) : {moves_toward_old}")
    print(f"  matches/beats OLD (within 2.5 pts)                  : {matches_or_beats_old}")
    print(f"  coherent across personas (every voice > chance)     : {coherent} "
          f"(min {persona_min*100:.1f}%)")
    print(f"\n  NOTE: the invariant base is UNCHANGED (consumed as a prong) -> its real-speech")
    print(f"        cross-speaker d' gain (+18.9%, bandwidth_bug_ab) is PRESERVED by construction;")
    print(f"        fusion adds a word-discriminative anchor WITHOUT touching the invariant rep.")
    print(f"\n  >>> FUSION CLOSES/MOVES-TOWARD-OLD: {moves_toward_old and matches_or_beats_old}")
    print("===MARKER_STAGE4_FUSION_COMPLETE===")
    print(f"\nelapsed {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
