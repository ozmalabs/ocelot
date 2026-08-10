"""correctness_trust — FIX the fusion weighting with CORRECTNESS-KEYED TRUST (gap 2, the named
next from commit 7cd7f60e).

WHY pcw (per-context MARGIN) STALLED at 61.4% < formant-alone 62.2%: the residual drag is the
weak AUX (articulatory) prong being CONFIDENTLY WRONG on six (six->eight 68/300, six->seven
66/300). Margin = CONFIDENCE != CORRECTNESS, so a confidently-wrong prong has HIGH margin and
keeps full weight (Dunning-Kruger inside the fusion). Margin can only down-weight UNCERTAIN
prongs; it cannot catch a prong that is reliably wrong while certain.

THE AGENT'S DESIGN (correctness-keyed trust — the prong's TRACK RECORD):
=======================================================================
On the TRAIN speakers ONLY, measure the AUX prong's PRECISION-when-it-asserts-d:

    prec_a[d] = P(true == d | AUX prong's argmax == d)
              = (# train tokens where AUX asserts d AND truth == d) / (# train tokens AUX asserts d)

This is a MEASUREMENT of the prong's reliability AT THE MOMENT it claims a digit. A prong
reliably-wrong when it asserts "six" gets a LOW prec_a["six"]; reliably-right when it asserts
"eight" gets a HIGH prec_a["eight"]. The AUX prong's vote FOR a digit is its ASSERTION (its own
argmax); the correctness trust on a token is prec_a[that asserted digit], read NATIVELY as
Attr( Argmax_w aux_field, prec_a ) inside the fusion Term.

COMBINED WITH THE EXISTING MARGIN (the agent's choice — soft-AND of two excluders):

    trust_a(token) = min(1, conf_a/cref_a)   *   prec_a[ argmax_w a_c(w) ]
                     [______ margin ______]      [____ correctness _____]

The PRODUCT defers when the AUX prong is EITHER uncertain here (low margin) OR reliably-wrong on
what it asserts (low precision) — exactly the union of failure modes. Both factors are in [0,1],
so the AUX weight w_art*trust_a can still only DROP BELOW its global w_art, never rise (a pure
soft-EXCLUDER down-weighter). The formant ANCHOR keeps full weight (same safety argument). We
ALSO measure the MIN combiner and the correctness-ALONE ablation, to show the result is not an
artifact of one combiner choice.

DONKEY / TRAIN-ONLY SAFETY (the line between a track record and a fit):
  prec_a is recomputed PER FOLD from that fold's TRAIN speakers ONLY — the LOSO held-out speaker
  is NEVER used to build the precision table. It is a MEASUREMENT of the prong's track record,
  NOT a sweep-to-fit: no tuning against the test, no per-test-token peeking, no gradient, no .fit.
  The whole decision (AUX argmax, precision lookup, margin, their product, weighting, sum, argmax)
  is ONE native Term via substrate.evaluate (Argmax/Attr/Min/Div/Times/Plus all already in
  term.rs; ZERO new primitives, NO Rust). Recogniser prongs UNCHANGED. CortexLoop + solve_for_n
  UNTOUCHED.

TEST (FSDD LOSO, n=3000, chance 0.10, held-out NEVER banked):
  correctness-keyed fusion  vs
    (a) formant-prong-alone            62.2%   <- THE BAR (fusion must clear it)
    (b) per-context-margin fusion      61.4%
    (c) global-weight fusion           60.6%
    (d) exemplar bank                  80.6%
  + per-digit (especially SIX — does the six->eight/six->seven drag clear?).

VERDICT RULE: gap 2 is CLOSED iff correctness-keyed fusion >= 62.2% (clears the best single
prong) by down-weighting the confidently-wrong AUX votes. HONEST if it still trails: pinpoint
why (train-vs-test precision generalisation? the trust form?). No sweep-to-fit; never "more data".

Run:  PYTHONUNBUFFERED=1 python -m scripts.correctness_trust
      PYTHONUNBUFFERED=1 python -m scripts.correctness_trust --quick
"""
from __future__ import annotations

import gc
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

CKPT_DIR = "/tmp/correctness_trust_ckpt"

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
from scripts.tfs_validation import TFSPerceptionGraph


def _conf_ref(s, word_nodes, log_a_list, attr_key):
    """Train reference confidence for one prong = the MEDIAN per-token margin over train tokens
    (verbatim from fusion_weighting). Floor 1e-6."""
    margins = [NF.native_confidence(s, word_nodes, la, attr_key, MS._Pred) for la in log_a_list]
    return max(float(np.median(margins)) if margins else 1.0, 1e-6)


def _measure_aux_precision(corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap):
    """TRAIN-ONLY precision table for the AUX (articulatory) prong: prec_a[d] = fraction of train
    tokens, AMONG those where the AUX prong asserts d (its own argmin d_A == argmax a_c), that are
    actually d. The AUX assertion is argmin_w d_a[w] (a_c(w) = -d_a[w]/tau, so argmax a_c = argmin
    d_a — the AUX argmax does NOT depend on tau). Held-out NEVER touched: only train_idx tokens
    enter this measurement. A track record, not a fit.

    Returns (prec_a, asserted_counts, correct_counts) — prec_a defaults to a NEUTRAL 1.0 for any
    digit the AUX prong never asserts on train (no track record => no down-weight; the margin and
    anchor still govern). Optionally we could smooth, but the neutral default is the honest 'no
    evidence to penalise' choice and is reported.
    """
    asserted = Counter()   # d -> # train tokens where AUX asserts d
    correct = Counter()    # d -> # of those that are truly d
    for i in train_idx:
        ov = corpus[i]["obs_voicing"]
        d_a = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
        assert_w = min(d_a, key=lambda w: d_a[w])   # AUX prong's argmax word (= argmin distance)
        asserted[assert_w] += 1
        if corpus[i]["word"] == assert_w:
            correct[assert_w] += 1
    prec_a = {}
    for d in DIGITS:
        n = asserted.get(d, 0)
        prec_a[d] = (correct.get(d, 0) / n) if n > 0 else 1.0   # neutral 1.0 when never asserted
    return prec_a, dict(asserted), dict(correct)


def _eval_one_fold(corpus, held, quick=False):
    """Run ONE held-out fold and return a checkpoint dict with per-fold counts + confusion matrices
    for every recogniser. Isolated so it can run in its own process (the Rust evaluator can SIGSEGV
    under host memory pressure on the big exemplar-DTW path; per-fold isolation means a crash loses
    at most one fold, retried, never the whole LOSO). The precision table is measured from this
    fold's TRAIN tokens ONLY — held-out NEVER banked nor used for prec_a."""
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
    ckt_c = ckt_n = 0
    cktmin_c = cktmin_n = 0
    corronly_c = corronly_n = 0
    mel_c = mel_n = 0
    conf_form = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_glob = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_pcw = {w: {u: 0 for u in DIGITS} for w in DIGITS}
    conf_ckt = {w: {u: 0 for u in DIGITS} for w in DIGITS}

    if True:
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

        # tau scales (TRAIN only) — verbatim.
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

        # GLOBAL reliability weight (TRAIN only).
        w_art = _measure_art_weight(
            corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap, chance)

        # TRAIN reference per-context AUX margin (conf_ref_a) — TRAIN sample only.
        a_fields = []
        for i in h_sample:
            ov = corpus[i]["obs_voicing"]
            da = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)
            a_fields.append({w: -da[w] / tau_a for w in DIGITS})
        cref_a = _conf_ref(fuse_sub, fuse_nodes, a_fields, NF.LOG_A_A_ATTR)

        # TRAIN-ONLY AUX precision table (the correctness key) — held-out NEVER used.
        prec_a, asserted, correct = _measure_aux_precision(
            corpus, train_idx, art_sub, art_q, art_word_nodes, observe_gap)

        # exemplar bank (verbatim).
        bank_mel = [(mel_normed[i], corpus[i]["word"]) for i in train_idx]
        bank_mel_words = [w for _, w in bank_mel]
        vote_sub, _vwn, vote_ex_nodes = NV.build_vote_substrate(Substrate, DIGITS, bank_mel_words)

        s_ckt_c = s_ckt_t = 0
        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            ov = corpus[i]["obs_voicing"]
            d_a = native_d_a(art_sub, art_q, art_word_nodes, corpus[i]["obs_rel"], ov, observe_gap)

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_a = {w: -d_a[w] / tau_a for w in DIGITS}

            # (a) formant prong ALONE = native DTW Argmin Term (the 62.2% recogniser).
            pn_form = s.evaluate(_P(term), {"q": q_node})
            pred_form = s.node(pn_form)["attrs"].get("name") if pn_form is not None else None
            form_n += 1
            if pred_form == true:
                form_c += 1
            if pred_form in DIGITS:
                conf_form[true][pred_form] += 1

            # (c) GLOBAL-weight fusion.
            pred_glob = NF.native_predict(fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, MS._Pred)
            glob_n += 1
            if pred_glob == true:
                glob_c += 1
            conf_glob[true][pred_glob] += 1

            # (b) PER-CONTEXT-MARGIN fusion (the 61.4% pcw).
            pred_pcw = NF.native_predict_pcw(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, cref_a, MS._Pred)
            pcw_n += 1
            if pred_pcw == true:
                pcw_c += 1
            conf_pcw[true][pred_pcw] += 1

            # (fix) CORRECTNESS-KEYED fusion — margin x precision (product).
            pred_ckt = NF.native_predict_ckt(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, cref_a, prec_a,
                MS._Pred, combiner="product")
            ckt_n += 1; s_ckt_t += 1
            if pred_ckt == true:
                ckt_c += 1; s_ckt_c += 1
            conf_ckt[true][pred_ckt] += 1

            # robustness: MIN combiner + correctness-ALONE ablation (counts only).
            pred_min = NF.native_predict_ckt(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, cref_a, prec_a,
                MS._Pred, combiner="min")
            cktmin_n += 1; cktmin_c += int(pred_min == true)
            pred_co = NF.native_predict_ckt(
                fuse_sub, fuse_nodes, log_a_h, log_a_a, ng_logp, w_art, cref_a, prec_a,
                MS._Pred, combiner="corr_only")
            corronly_n += 1; corronly_c += int(pred_co == true)

            # (d) exemplar baseline.
            dists = [mi.dtw(mel_normed[i], Mtr, mel_ops) for Mtr, _ in bank_mel]
            pred_mel = NV.native_vote(vote_sub, vote_ex_nodes, dists, mi.KNN_K, _P)
            mel_n += 1; mel_c += int(pred_mel == true)

        sixp = prec_a.get("six", float("nan"))
        print(f"    held-out {held:10s}: ckt {s_ckt_c/max(1,s_ckt_t):.3f} "
              f"(n={s_ckt_t}, w_art={w_art:.3f}, cref_a={cref_a:.3f}, "
              f"prec_a[six]={sixp:.2f})", flush=True)

    return {
        "held": held,
        "form_c": form_c, "form_n": form_n,
        "glob_c": glob_c, "glob_n": glob_n,
        "pcw_c": pcw_c, "pcw_n": pcw_n,
        "ckt_c": ckt_c, "ckt_n": ckt_n,
        "cktmin_c": cktmin_c, "cktmin_n": cktmin_n,
        "corronly_c": corronly_c, "corronly_n": corronly_n,
        "mel_c": mel_c, "mel_n": mel_n,
        "prec_a": prec_a,
        "conf_form": conf_form, "conf_glob": conf_glob,
        "conf_pcw": conf_pcw, "conf_ckt": conf_ckt,
    }


def _aggregate(folds):
    """Sum the per-fold checkpoints into the full LOSO result (n=3000), summing confusion matrices
    and counts. Identical aggregation to the original whole-run path — just assembled from the
    per-fold checkpoints instead of one process."""
    def _agg_conf(key):
        out = {w: {u: 0 for u in DIGITS} for w in DIGITS}
        for f in folds:
            for w in DIGITS:
                for u in DIGITS:
                    out[w][u] += f[key][w][u]
        return out
    tot = lambda k: sum(f[k] for f in folds)
    res = {
        "form_acc": tot("form_c") / max(1, tot("form_n")), "form_n": tot("form_n"),
        "glob_acc": tot("glob_c") / max(1, tot("glob_n")), "glob_n": tot("glob_n"),
        "pcw_acc": tot("pcw_c") / max(1, tot("pcw_n")), "pcw_n": tot("pcw_n"),
        "ckt_acc": tot("ckt_c") / max(1, tot("ckt_n")), "ckt_n": tot("ckt_n"),
        "cktmin_acc": tot("cktmin_c") / max(1, tot("cktmin_n")),
        "corronly_acc": tot("corronly_c") / max(1, tot("corronly_n")),
        "mel_acc": tot("mel_c") / max(1, tot("mel_n")), "mel_n": tot("mel_n"),
        "per_speaker": {f["held"]: (f["ckt_c"] / max(1, f["ckt_n"])) for f in folds},
        "prec_log": {f["held"]: f["prec_a"] for f in folds},
        "conf_form": _agg_conf("conf_form"), "conf_glob": _agg_conf("conf_glob"),
        "conf_pcw": _agg_conf("conf_pcw"), "conf_ckt": _agg_conf("conf_ckt"),
    }
    return res


def _ckpt_path(held, quick):
    tag = "quick" if quick else "full"
    return os.path.join(CKPT_DIR, f"{tag}_{held}.json")


def run_one_fold_mode(held, quick):
    """Single-fold worker: build the corpus, run ONLY this held-out fold, write the checkpoint JSON.
    Invoked as a subprocess by the orchestrator so a SIGSEGV in the Rust evaluator (host memory
    pressure on the exemplar-DTW path) loses at most this fold, not the whole LOSO."""
    sub = Substrate()
    P_tfs = TFSPerceptionGraph()
    corpus, skipped = build_corpus(sub, P_tfs, seed=0, quick=quick)
    fold = _eval_one_fold(corpus, held, quick=quick)
    os.makedirs(CKPT_DIR, exist_ok=True)
    with open(_ckpt_path(held, quick), "w") as fh:
        json.dump(fold, fh)
    print(f"  CKPT written: {_ckpt_path(held, quick)}", flush=True)


def main():
    quick = "--quick" in sys.argv

    # Single-fold worker mode (invoked per held-out speaker as an isolated subprocess).
    if "--held" in sys.argv:
        held = sys.argv[sys.argv.index("--held") + 1]
        run_one_fold_mode(held, quick)
        return

    t0 = time.time()
    sub = Substrate()
    print("=" * 90)
    print("correctness_trust — FIX the fusion weighting with CORRECTNESS-KEYED TRUST (gap 2)")
    print("pcw (per-context MARGIN) stalled at 61.4% < formant-alone 62.2%: the weak AUX prong is")
    print("CONFIDENTLY WRONG on six (six->eight/six->seven), and margin = confidence != correctness,")
    print("so it keeps full weight. The agent keys trust to the prong's per-asserted-digit TRACK")
    print("RECORD (train precision-when-it-asserts-d), combined with margin. FSDD LOSO, chance 0.100.")
    print("=" * 90)

    print("\n1. THE AGENT'S DESIGN (donkey audit):")
    print("   correctness = prec_a[d] = P(true==d | AUX prong asserts d), MEASURED on TRAIN speakers")
    print("                ONLY (recomputed per fold; held-out NEVER used to build it). The AUX vote")
    print("                FOR a digit is its assertion (argmax); the trust is prec_a[that digit],")
    print("                read natively as Attr(Argmax_w aux_field, prec_a). Catches confident-")
    print("                wrongness margin cannot. In [0,1] (a precision) — no clamp.")
    print("   combine     = trust_a = min(1, conf_a/cref_a) * prec_a[argmax_a]  (PRODUCT = soft-AND).")
    print("                Defers when the AUX prong is EITHER uncertain here OR reliably-wrong on")
    print("                what it asserts. Both <= 1 => AUX weight can only DROP below w_art (pure")
    print("                soft-excluder). Anchor (formant) stays FULL weight (the safety argument).")
    print("                MIN combiner + correctness-ALONE ablation measured alongside.")
    print("   term        = Attr(Argmax_w(aux_field), prec_a); whole fusion is ONE native Term")
    print("                (substrate.evaluate). Argmax/Attr/Min/Div/Times/Plus all already exist.")
    print("   train-only  = prec_a built from that fold's TRAIN tokens ONLY (the AUX argmin over the")
    print("                train tokens + their truth). NO test peeking, NO sweep-to-fit, NO .fit/")
    print("                gradient. A MEASUREMENT of the prong's track record. NO Rust.")
    print("   audit       = native Term; prongs UNCHANGED; real FSDD; held-out NEVER banked nor used")
    print("                for prec_a; CortexLoop + solve_for_n UNTOUCHED.")

    P_tfs = TFSPerceptionGraph()
    print(f"\n2. PERCEPTION (the 60.6% TFS-graded-voicing setting): {P_tfs.describe()}")
    print("\nBuilding corpus (TFS-graded voicing perception over the tokens) ...", flush=True)
    corpus, skipped = build_corpus(sub, P_tfs, seed=0, quick=quick)
    speakers = sorted(set(it["speaker"] for it in corpus))
    print(f"  {len(corpus)} tok (skip {skipped}) | speakers={speakers}")

    print("\n" + "=" * 90)
    print("LOSO — correctness-keyed fusion vs margin-pcw vs global vs formant-alone vs exemplar")
    print("(per-fold subprocess isolation + checkpoint; a flaky Rust-evaluator SIGSEGV on the heavy")
    print(" exemplar-DTW path under host memory pressure costs at most one fold, retried — never")
    print(" the whole LOSO. Same numbers; the eval logic is unchanged.)")
    print("=" * 90)

    import subprocess
    os.makedirs(CKPT_DIR, exist_ok=True)
    folds = []
    for held in speakers:
        cp = _ckpt_path(held, quick)
        ok = False
        for attempt in range(1, 5):
            if os.path.exists(cp):
                ok = True
                break
            print(f"  [fold {held}] attempt {attempt} ...", flush=True)
            env = dict(os.environ, PYTHONUNBUFFERED="1", MALLOC_ARENA_MAX="1")
            cmd = [sys.executable, "-m", "scripts.correctness_trust", "--held", held]
            if quick:
                cmd.append("--quick")
            rc = subprocess.call(cmd, env=env)
            if rc == 0 and os.path.exists(cp):
                ok = True
                break
            print(f"  [fold {held}] subprocess rc={rc} (segfault=139) — retrying", flush=True)
        if not ok:
            print(f"  [fold {held}] FAILED after retries — aborting honestly (no fake numbers).",
                  flush=True)
            sys.exit(2)
        with open(cp) as fh:
            folds.append(json.load(fh))
        f = folds[-1]
        print(f"    held-out {held:10s}: ckt {f['ckt_c']/max(1,f['ckt_n']):.3f} "
              f"(n={f['ckt_n']}, prec_a[six]={f['prec_a'].get('six', float('nan')):.2f})", flush=True)

    res = _aggregate(folds)

    fa = res["form_acc"]; gb = res["glob_acc"]; pw = res["pcw_acc"]
    ck = res["ckt_acc"]; ex = res["mel_acc"]
    print("\n" + "=" * 90)
    print(f"RESULTS (FSDD LOSO, n={res['ckt_n']}, chance 10.0%)")
    print("=" * 90)
    print(f"  (a) formant-prong-alone            : {fa*100:5.1f}%   [THE BAR; reference 62.2%]")
    print(f"  (b) per-context-MARGIN fusion (pcw): {pw*100:5.1f}%   [reference 61.4%]")
    print(f"  (c) global-weight fusion           : {gb*100:5.1f}%   [reference 60.6%]")
    print(f"  (fix) CORRECTNESS-KEYED (product)  : {ck*100:5.1f}%   <== the agent's gap-2 fix")
    print(f"        correctness-keyed (min)      : {res['cktmin_acc']*100:5.1f}%   [robustness combiner]")
    print(f"        correctness-ALONE (ablation) : {res['corronly_acc']*100:5.1f}%   [no margin]")
    print(f"  (d) exemplar bank                  : {ex*100:5.1f}%   [reference 80.6%]")
    print(f"\n  delta (ckt - margin-pcw)   : {(ck-pw)*100:+.1f} pts")
    print(f"  delta (ckt - formant-alone): {(ck-fa)*100:+.1f} pts   (must be >= 0 to close gap 2)")

    print("\n  PER-DIGIT FUSION acc (does the SIX drag clear?):")
    print(f"    {'digit':>6}  {'formant':>8}  {'margin':>8}  {'ckt':>8}   {'ckt-formant':>12}")
    for w in DIGITS:
        af, _ = _digit_acc(res["conf_form"], w)
        ap, _ = _digit_acc(res["conf_pcw"], w)
        ac, n = _digit_acc(res["conf_ckt"], w)
        mark = "  <== SIX" if w == "six" else ""
        print(f"    {w:>6}  {af*100:7.1f}%  {ap*100:7.1f}%  {ac*100:7.1f}%   {(ac-af)*100:+11.1f}  (n={n}){mark}")

    print(f"\n  SIX-SINK (non-six wrongly -> six): "
          f"formant {_into_six(res['conf_form'])}  | margin {_into_six(res['conf_pcw'])}"
          f"  | ckt {_into_six(res['conf_ckt'])}")
    print(f"  SIX-confusions formant: six->eight {res['conf_form']['six']['eight']}, "
          f"six->seven {res['conf_form']['six']['seven']}  | "
          f"ckt: six->eight {res['conf_ckt']['six']['eight']}, "
          f"six->seven {res['conf_ckt']['six']['seven']}")
    _watch_rows("(b) MARGIN-pcw fusion confusions", res["conf_pcw"])
    _watch_rows("(fix) CORRECTNESS-KEYED fusion confusions", res["conf_ckt"])

    # AUX precision table summary (averaged across folds) — what the track record SAYS.
    print("\n  AUX prong TRAIN precision-when-it-asserts-d (mean over folds, the correctness key):")
    avg_prec = {d: float(np.mean([res["prec_log"][h][d] for h in res["prec_log"]])) for d in DIGITS}
    print("    " + "  ".join(f"{d}:{avg_prec[d]:.2f}" for d in DIGITS))

    print("\n" + "=" * 90)
    print("VERDICT — does correctness-keyed trust CLEAR formant-alone (gap 2 closed)?")
    print("=" * 90)
    clears_bar = ck >= fa
    beats_margin = ck > pw
    print(f"  correctness-keyed clears formant-alone 62.2%: {'YES' if clears_bar else 'NO'} "
          f"({ck*100:.1f}% vs {fa*100:.1f}%)")
    print(f"  correctness-keyed beats margin-pcw 61.4%    : {'YES' if beats_margin else 'NO'} "
          f"({ck*100:.1f}% vs {pw*100:.1f}%)")
    if clears_bar:
        print("\n  => GAP 2 CLOSED: the correctness key down-weights the AUX prong's confidently-WRONG")
        print("     six votes (which margin could not catch — high margin, low precision), the six")
        print("     drag clears, and the fusion now CLEARS the best single prong. Train-only track")
        print("     record, native Term, no sweep.")
    elif beats_margin:
        print("\n  => PARTIAL: correctness-keyed improves on margin-pcw but does not yet clear formant-")
        print("     alone. Pinpoint above — train-vs-test precision generalisation, or the trust form.")
        print("     NOT 'more data'.")
    else:
        print("\n  => HONEST / NOT-CLEARED: the correctness key does not separate reliable-from-not on")
        print("     held-out speakers (train precision may not generalise across the speaker fold).")
        print("     Pinpoint above; never 'more data'.")

    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("CORRECTNESS_TRUST_COMPLETED")


if __name__ == "__main__":
    main()
