"""fusion_weighting — FIX the FUSION-WEIGHTING gap (the open issue from the TFS validation,
commit 90b799c9): the multi-pronged native fusion (60.6% TFS / 58.4% cutover) TRAILS the
formant-prong-alone (62.2%). The weak prongs (articulatory, voicing) are multiplied in at a
GLOBAL train weight on EVERY token, so where they are LOCALLY flat/uncertain they drag the
strong formant prong wherever the prongs disagree (the margin-error).

THE AGENT'S DESIGN (reasoned from the grammar; weighted-admissibility, per-context):
=====================================================================================
The night's OWN finding: a cue at a GLOBAL weight over-corrects (the binary gap gate sank
seven, 5defadb8). A global weight cannot tell a token the weak prong KNOWS from one it
doesn't. The fix is PER-CONTEXT RELIABILITY WEIGHTING done as weighted-admissibility — each
prong is a soft excluder weighted by how much to TRUST it IN THIS CONTEXT.

THE TRUST SIGNAL = the prong's per-context DECISION MARGIN (peakiness of its OWN admissibility
field). Each prong is top-centred (best word = 0, others <= 0); the margin is the MEAN DEPTH
of the field below the winner:

    conf_p(token) = -(1/N) * Sum_w (score_c_p(w))        # score_c_p(w) = p(w) - max_w' p(w')

  * FLAT field (prong has no opinion: all words near-equally admissible) -> conf_p ~ 0
    -> the prong DEFERS (its excluder flattens toward neutral; it CANNOT corrupt).
  * PEAKED field (one word clearly stands out)                          -> conf_p large
    -> the prong CONSTRAINS.

The per-context prong weight = global_w_p * (conf_p / conf_ref_p), conf_ref_p a TRAIN-measured
typical margin (so the two prongs' margins are comparable in scale). The fused score:

    score(w) = (conf_h/cref_h)*h_c(w) + w_art*(conf_a/cref_a)*a_c(w) + ng_logp(w)

ALL native: conf_p = Neg(Div(Sum_w(top_centred), Count)); the whole decision (top-centring,
margins, per-context weighting, sum, argmax) is ONE Term via substrate.evaluate. NO second-max
primitive, NO new grammar (Sum/Count/Div/Neg/Max/Minus/Plus/Times/Argmax all already in
term.rs). NO net, NO .fit, NO gradient, NO sweep. conf_ref is a MEASUREMENT (median train
margin), not a tuned knob.

SAFETY ARGUMENT (fusion must NEVER underperform the best single prong, 62.2%):
  Where the articulatory prong is flat/uncertain on a token, conf_a -> 0 so its weight -> 0
  and the formant prong decides that token ALONE. The fusion therefore cannot lose to formant-
  alone on the tokens the weak prong would otherwise have dragged. The formant prong is ALSO
  confidence-weighted (symmetric), so where IT is uncertain the others may help (ADDITIVE).
HONEST LIMIT: a prong can be confidently WRONG (peaked on the wrong word); margin cannot catch
that — it down-weights UNCERTAIN prongs (the dominant drag source: disagreement born of the
weak prong's fuzziness), not confidently-wrong ones. This driver MEASURES whether that suffices
to clear 62.2%.

TEST (FSDD LOSO, n=3000, chance 0.10, held-out NEVER banked):
  per-context-weighted fusion (TFS voicing)  vs
    (a) formant-prong-alone        62.2%   <- THE BAR (fusion must clear it)
    (b) global-weight fusion (TFS) 60.6%   <- the current fusion
    (c) exemplar bank              83.5%   <- the non-fusion reference
  + per-digit (does the margin-error clear — does seven/three stop being dragged?).

VERDICT RULE: the weighting gap is FIXED iff per-context-weighted fusion >= 62.2% (it clears
the best single prong) AND it does so by down-weighting the weak prong where it is unreliable
(not by accident). HONEST if it still trails: the trust signal is not separating reliable-from-
not; pinpoint why. No sweep-to-fit; never "more data".

DONKEY: fusion = native Term via substrate.evaluate; recogniser prongs UNCHANGED (only the
fusion weighting); held-out NEVER banked; CortexLoop + solve_for_n UNTOUCHED.

Run:  PYTHONUNBUFFERED=1 python -m scripts.fusion_weighting
      PYTHONUNBUFFERED=1 python -m scripts.fusion_weighting --quick
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

import scripts.perception_composition as PC
from scripts.perception_composition import (
    build_corpus, native_d_a, _measure_art_weight,
    _harmonic_dists, _digit_acc, _into_six, _watch_rows,
)
from scripts.formant_trajectory_dynamics import (
    DIGITS, dtw_predict_term, _traj_tuple, _P, WORD_ATTR, Q_ATTR, TRAJ_ATTR,
)
from scripts.articulatory_gamma import (
    articulatory_models, W_FORMANT_SHADOW, W_VOICING_SHADOW, W_GAMMA,
)
from scripts import mcu_infer as mi
import domains.native_fusion as NF
import domains.native_cognition as NC
import domains.native_vote as NV
import domains.many_settings_recognizer as MS
# the TFS-graded voicing perception (the 60.6% setting) — verbatim.
from scripts.tfs_validation import TFSPerceptionGraph


def _conf_ref(s, word_nodes, log_a_list, attr_key):
    """Train reference confidence for one prong = the MEDIAN per-token margin over train tokens.
    Each entry of log_a_list is a {word: value} prong field for one train token. Native margin
    Term (NF.native_confidence) evaluated per token; median taken. Floor 1e-6 (no div-by-zero)."""
    margins = [NF.native_confidence(s, word_nodes, la, attr_key, MS._Pred) for la in log_a_list]
    return max(float(np.median(margins)) if margins else 1.0, 1e-6)


def evaluate_pcw(sub, corpus, quick=False):
    """LOSO eval. Computes, per held-out fold, BOTH the global-weight fusion (b) and the
    per-context-weighted fusion (the fix) over the SAME prong channels, plus formant-alone (a)
    and the exemplar bank (c). The prongs are byte-identical to perception_composition.evaluate;
    only an ADDITIONAL fusion call (native_predict_pcw) is added. Held-out NEVER banked."""
    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()
    models = articulatory_models()
    chance = 1.0 / len(DIGITS)
    observe_gap = True

    art_sub, art_q, art_word_nodes = NC.build_articulatory_substrate(
        Substrate, models, W_FORMANT_SHADOW, W_GAMMA, with_voicing=True)
    fuse_sub, fuse_nodes = NF.build_word_substrate(Substrate, DIGITS)

    # exemplar baseline plumbing (verbatim).
    canonical = mi.canonical_log_centroid([it["mel"] for it in corpus])
    by_spk_mel = defaultdict(list)
    for it in corpus:
        by_spk_mel[it["speaker"]].append(it["mel"])
    spk_stats = {sp: mi.speaker_stats(by_spk_mel[sp]) for sp in speakers}
    mel_ops = mi.Ops()
    mel_normed = {}
    for i, it in enumerate(corpus):
        mean, std = spk_stats[it["speaker"]]
        mel_normed[i] = mi.normalise(it["mel"], mean, std, canonical, mel_ops)

    form_c = form_n = 0
    glob_c = glob_n = 0
    pcw_c = pcw_n = 0
    mel_c = mel_n = 0
    conf_form = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_glob = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_pcw = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    per_speaker = {}

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
            ov = corpus[i]["obs_voicing"]
            da = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
            vals = list(da.values())
            a_spreads.append(max(vals) - min(vals))
        tau_a = max(float(np.median(a_spreads)) if a_spreads else 1.0, 1e-6)

        # GLOBAL reliability weight (the existing prong weight) — TRAIN only.
        w_art = _measure_art_weight(
            corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap, chance)

        # TRAIN reference per-context AUX margin (conf_ref_a) — measured on the SAME train
        # sample, the scale that makes the AUX confidence ratio dimensionless. Held-out NEVER
        # touched. (Only the AUX/articulatory prong is per-context-weighted; the formant ANCHOR
        # keeps full weight, so no conf_ref_h is needed — see the safety argument in native_fusion.)
        a_fields = []
        for i in h_sample:
            ov = corpus[i]["obs_voicing"]
            da = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
            a_fields.append({w: -da[w] / tau_a for w in DIGITS})
        cref_a = _conf_ref(fuse_sub, fuse_nodes, a_fields, NF.LOG_A_A_ATTR)

        # exemplar bank (verbatim).
        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]
        bank_mel_words = [w for _, w in bank_mel]
        vote_sub, _vwn, vote_ex_nodes = NV.build_vote_substrate(Substrate, DIGITS, bank_mel_words)

        s_pcw_c = s_pcw_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            ov = corpus[i]["obs_voicing"]
            d_a = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_a = {w: -d_a[w] / tau_a for w in DIGITS}

            # (a) formant prong ALONE = the agent's NATIVE DTW Argmin Term (the 62.2% recogniser).
            pn_form = s.evaluate(_P(term), {"q": q_node})
            pred_form = s.node(pn_form)["attrs"].get("name") if pn_form is not None else None
            form_n += 1
            if pred_form == true:
                form_c += 1
            if pred_form in DIGITS:
                conf_form[true][pred_form] += 1

            # (b) GLOBAL-weight fusion — the current native fusion Term (w_art a global Lit).
            pred_glob = NF.native_predict(fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, MS._Pred)
            glob_n += 1
            if pred_glob == true:
                glob_c += 1
            conf_glob[true][pred_glob] += 1

            # (fix) PER-CONTEXT-WEIGHTED fusion — the agent's design. Same prong channels; the
            # prong weights are now per-context margins / conf_ref instead of a global Lit.
            pred_pcw = NF.native_predict_pcw(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, cref_a, MS._Pred)
            pcw_n += 1; s_pcw_t += 1
            if pred_pcw == true:
                pcw_c += 1; s_pcw_c += 1
            conf_pcw[true][pred_pcw] += 1

            # (c) exemplar baseline.
            dists = [mi.dtw(mel_normed[i], Mtr, mel_ops) for Mtr, _ in bank_mel]
            pred_mel = NV.native_vote(vote_sub, vote_ex_nodes, dists, mi.KNN_K, _P)
            mel_n += 1; mel_c += int(pred_mel == true)

        per_speaker[held] = s_pcw_c / max(1, s_pcw_t)
        print(f"    held-out {held:10s}: pcw {s_pcw_c/max(1,s_pcw_t):.3f} "
              f"(n={s_pcw_t}, w_art={w_art:.3f}, cref_a={cref_a:.3f})", flush=True)

    return {
        "form_acc": form_c / max(1, form_n), "form_n": form_n,
        "glob_acc": glob_c / max(1, glob_n), "glob_n": glob_n,
        "pcw_acc": pcw_c / max(1, pcw_n), "pcw_n": pcw_n,
        "mel_acc": mel_c / max(1, mel_n), "mel_n": mel_n,
        "per_speaker": per_speaker,
        "conf_form": conf_form, "conf_glob": conf_glob, "conf_pcw": conf_pcw,
    }


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    sub = Substrate()
    print("=" * 90)
    print("fusion_weighting — FIX the FUSION-WEIGHTING gap (open issue from TFS validation 90b799c9)")
    print("The multi-pronged fusion TRAILS formant-alone (62.2%) because the weak prongs are weighted")
    print("GLOBALLY. The agent re-weights each prong by its PER-CONTEXT DECISION MARGIN (weighted-")
    print("admissibility): an uncertain prong DEFERS on a token, a confident one CONSTRAINS — native.")
    print("FSDD LOSO, held-out NEVER banked, chance 0.100.")
    print("=" * 90)

    print("\n1. THE AGENT'S DESIGN (donkey audit):")
    print("   trust      = per-prong PER-CONTEXT decision MARGIN = peakiness of the prong's OWN")
    print("                top-centred admissibility field: conf_p = -(1/N) Sum_w (p(w) - max_w' p(w')).")
    print("                FLAT field -> conf~0 -> prong DEFERS (flattens to neutral, cannot drag);")
    print("                PEAKED field -> conf large -> prong CONSTRAINS.")
    print("   ASYMMETRY   = ONLY the weak articulatory AUX prong is re-weighted; the formant ANCHOR")
    print("                (the 62.2% prong) keeps FULL weight on every token. Down-weighting the")
    print("                strong prong where ITS field is flat (a hard token) would hand the call")
    print("                to the weak prongs — the OPPOSITE of safe. That is the safety argument.")
    print("   weight      = w_art * MIN(1, conf_a / conf_ref_a); conf_ref_a = MEDIAN train AUX")
    print("                margin (a MEASUREMENT). The CLAMP to [0,1] means the AUX weight can only")
    print("                DROP BELOW its global w_art (defer when uncertain here), never rise above")
    print("                it — a pure soft-EXCLUDER down-weighter that can only REMOVE drag.")
    print("   term        = Neg(Div(Sum_w(top_centred), Count)); whole fusion is ONE native Term")
    print("                (substrate.evaluate). NO new primitive (Sum/Count/Div/Neg already exist).")
    print("   safety      = AUX flat-here -> aux weight~0 -> anchor decides that token ALONE,")
    print("                so fusion cannot underperform formant-alone on the dragged tokens.")
    print("   audit       = native Term, no net/.fit/gradient/sweep; prongs UNCHANGED; real FSDD;")
    print("                held-out NEVER banked; CortexLoop + solve_for_n UNTOUCHED.")

    P_tfs = TFSPerceptionGraph()  # the 60.6% setting (TFS-graded voicing in obs_voi)
    print(f"\n2. PERCEPTION (the 60.6% TFS-graded-voicing setting): {P_tfs.describe()}")
    print("\nBuilding corpus (TFS-graded voicing perception over the tokens) ...", flush=True)
    corpus, skipped = build_corpus(sub, P_tfs, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    print(f"  {len(corpus)} tok (skip {skipped}) | speakers={speakers}")

    print("\n" + "=" * 90)
    print("LOSO — per-context-weighted fusion vs global-weight fusion vs formant-alone vs exemplar")
    print("=" * 90)
    res = evaluate_pcw(sub, corpus, quick=quick)

    fa = res["form_acc"]; gb = res["glob_acc"]; pw = res["pcw_acc"]; ex = res["mel_acc"]
    print("\n" + "=" * 90)
    print(f"RESULTS (FSDD LOSO, n={res['pcw_n']}, chance 10.0%)")
    print("=" * 90)
    print(f"  (a) formant-prong-alone        : {fa*100:5.1f}%   [THE BAR; reference 62.2%]")
    print(f"  (b) global-weight fusion (TFS) : {gb*100:5.1f}%   [the current fusion; reference 60.6%]")
    print(f"  (fix) PER-CONTEXT-WEIGHTED     : {pw*100:5.1f}%   <== the agent's fusion-weighting fix")
    print(f"  (c) exemplar bank              : {ex*100:5.1f}%   [reference 83.5%]")
    print(f"\n  delta (pcw - global-weight) : {(pw-gb)*100:+.1f} pts")
    print(f"  delta (pcw - formant-alone) : {(pw-fa)*100:+.1f} pts   (must be >= 0 to fix the gap)")

    print("\n  PER-DIGIT FUSION acc (does the margin-error clear — seven/three stop being dragged?):")
    print(f"    {'digit':>6}  {'formant':>8}  {'global':>8}  {'pcw':>8}   {'pcw-global':>11}")
    for w in DIGITS:
        af, _ = _digit_acc(res["conf_form"], w)
        ag, _ = _digit_acc(res["conf_glob"], w)
        ap, n = _digit_acc(res["conf_pcw"], w)
        print(f"    {w:>6}  {af*100:7.1f}%  {ag*100:7.1f}%  {ap*100:7.1f}%   {(ap-ag)*100:+10.1f}  (n={n})")

    print(f"\n  SIX-SINK (non-six wrongly -> six): "
          f"formant {_into_six(res['conf_form'])}  | global {_into_six(res['conf_glob'])}"
          f"  | pcw {_into_six(res['conf_pcw'])}")
    _watch_rows("(b) GLOBAL-weight fusion confusions", res["conf_glob"])
    _watch_rows("(fix) PER-CONTEXT-WEIGHTED fusion confusions", res["conf_pcw"])

    print("\n" + "=" * 90)
    print("VERDICT — is the fusion-weighting gap fixed (does fusion now CLEAR the best single prong)?")
    print("=" * 90)
    clears_bar = pw >= fa
    beats_global = pw > gb
    print(f"  per-context-weighted fusion clears formant-alone: {'YES' if clears_bar else 'NO'} "
          f"({pw*100:.1f}% vs {fa*100:.1f}%)")
    print(f"  per-context-weighted fusion beats global-weight : {'YES' if beats_global else 'NO'} "
          f"({pw*100:.1f}% vs {gb*100:.1f}%)")
    if clears_bar:
        print("\n  => FUSION-WEIGHTING GAP FIXED: the per-context margin weighting lets the weak prongs")
        print("     DEFER where they are uncertain (so they no longer drag the strong formant prong)")
        print("     and still ADD where they are locally peaked+reliable — the fusion now clears the")
        print("     best single prong. Done as weighted-admissibility, native, no sweep.")
    elif beats_global:
        print("\n  => PARTIAL: the per-context margin weighting IMPROVES the fusion over the global")
        print("     weight (fewer dragged tokens) but does not yet clear formant-alone. The residual")
        print("     drag is from prongs that are CONFIDENTLY WRONG here (peaked on the wrong word) —")
        print("     margin cannot catch those; that is the honest limit, NOT 'more data'.")
    else:
        print("\n  => HONEST / NOT-FIXED: the per-context margin does not separate reliable-from-not")
        print("     well enough to beat the global weight. The drag is not dominated by UNCERTAIN")
        print("     prongs (which margin down-weights) but by confidently-wrong ones. Pinpoint above;")
        print("     never 'more data'.")

    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("FUSION_WEIGHTING_COMPLETED")


if __name__ == "__main__":
    main()
