"""native_fusion_accept — acceptance run for the NATIVE fusion Term (Rank-1 migration audit).

Re-runs the NEW/SOTA hearing path's LOSO recognition (scripts.articulatory_gamma helpers,
READ-ONLY) and, per token, computes BOTH:
  · the PYTHON fusion (verbatim from articulatory_gamma.evaluate ~600-611): the dict-comp
    argmax over logA[w] = log_a_h_c[w] + w_art*log_a_a_c[w] + ng_logp[w];
  · the NATIVE fusion (domains.native_fusion.predict_fusion_term): the SAME arithmetic as a
    graph Term (Argmax over Plus of [Minus(Attr,MaxOver), Times(Lit,Minus(Attr,MaxOver)),
    Attr]) evaluated by substrate.evaluate (native Rust eval).

Reports native-fusion accuracy, Python-fusion accuracy, and per-token AGREEMENT rate. The
fusion SCORING files are NOT modified — every prong helper is imported read-only; this is a
separate consumer that feeds the prong channels into the native Term as graph attrs.

PREDICTION: agreement ~100%, identical accuracy (same arithmetic, now graph-resident).
"""
from __future__ import annotations

import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import the NEW-path recogniser's helpers READ-ONLY (no modification to the scoring files).
import scripts.articulatory_gamma as AG
from scripts.articulatory_gamma import (
    DIGITS, WORD_ATTR, Q_ATTR, TRAJ_ATTR,
    Substrate, dtw_predict_term, articulatory_models, articulatory_distance,
    _harmonic_dists, _measure_prong_weights, build_corpus, _traj_tuple,
)
from scripts import mcu_infer as mi

import domains.native_fusion as NF
import domains.many_settings_recognizer as MS


def run(quick: bool = False, verbose: bool = True):
    sub = Substrate()
    corpus, skipped = build_corpus(sub, seed=0, quick=quick)
    if verbose:
        print(f"corpus: {len(corpus)} tokens (skipped {skipped})", flush=True)

    speakers = sorted(set(it["speaker"] for it in corpus))
    term = dtw_predict_term()
    models = articulatory_models()

    # exemplar-baseline plumbing is NOT needed here (we only compare the two fusions); skip it.
    chance = 1.0 / len(DIGITS)

    py_c = py_n = 0
    nat_c = nat_n = 0
    agree = 0
    total = 0

    for held in speakers:
        test_idx = [i for i, it in enumerate(corpus) if it["speaker"] == held]
        train_idx = [i for i, it in enumerate(corpus) if it["speaker"] != held]

        # formant-trajectory prong: exemplar bank (graph), TRAIN only — verbatim.
        s = Substrate()
        word_nodes = {}
        for w in DIGITS:
            word_nodes[w] = s.add_node("Concept", {"name": w, WORD_ATTR: 1.0})
        for i in train_idx:
            ex = s.add_node("Exemplar", {TRAJ_ATTR: _traj_tuple(corpus[i]["traj"])})
            s.add_edge_unchecked(word_nodes[corpus[i]["word"]], "has_exemplar", ex)
        q_node = s.add_node("Query", {Q_ATTR: ((0.0,) * 9,)})

        # n-gram prong: TRAIN unigram, log-prior centred (max 0) — verbatim.
        train_counts = Counter(corpus[i]["word"] for i in train_idx)
        tot = sum(train_counts.values())
        ng_logp = {w: math.log((train_counts.get(w, 0) + 1.0) / (tot + len(DIGITS)))
                   for w in DIGITS}
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
            da = articulatory_distance(corpus[i]["obs_rel"], models, sub)
            vals = list(da.values())
            a_spreads.append(max(vals) - min(vals))
        tau_a = max(float(np.median(a_spreads)) if a_spreads else 1.0, 1e-6)

        # MEASURED articulatory weight (inner LOSO on TRAIN only) — verbatim.
        w_form, w_art = _measure_prong_weights(
            corpus, train_idx, models, sub, term, tau_h, tau_a, chance)

        # native-fusion word substrate (separate from the formant-bank substrate s).
        nf_sub, nf_nodes = NF.build_word_substrate(Substrate, DIGITS)

        for i in test_idx:
            true = corpus[i]["word"]
            s.set_attr(q_node, Q_ATTR, _traj_tuple(corpus[i]["traj"]))
            d_h = _harmonic_dists(s, term, q_node, word_nodes)
            d_a = articulatory_distance(corpus[i]["obs_rel"], models, sub)

            log_a_h = {w: (-d_h[w] / tau_h if math.isfinite(d_h[w]) else -1e18) for w in DIGITS}
            log_a_a = {w: -d_a[w] / tau_a for w in DIGITS}

            # ---- PYTHON FUSION (verbatim articulatory_gamma ~605-611) ----
            h_top = max(v for v in log_a_h.values() if v > -1e17) if any(
                v > -1e17 for v in log_a_h.values()) else 0.0
            log_a_h_c = {w: (log_a_h[w] - h_top if log_a_h[w] > -1e17 else -1e18) for w in DIGITS}
            a_top = max(log_a_a.values())
            log_a_a_c = {w: log_a_a[w] - a_top for w in DIGITS}
            logA = {w: log_a_h_c[w] + w_art * log_a_a_c[w] + ng_logp[w] for w in DIGITS}
            pred_py = max(DIGITS, key=lambda w: logA[w])

            # ---- NATIVE FUSION (graph Term, native eval) ----
            # Feed the RAW (un-centred) prong channels; the Term centres + weights + argmaxes.
            # log_a_h has -1e18 sentinels for non-finite formant distances; the Term's MaxOver
            # over those words would corrupt the top-centring, so we mirror the Python guard:
            # a word with no finite formant distance is excluded from the candidate set the same
            # way (Python's h_top ignores <= -1e17 and the centred value stays -1e18, never the
            # argmax). We pass the sentinel through; the native MaxOver picks the same finite top
            # because every finite candidate is > any sentinel only if a finite one exists. To be
            # faithful we hand the native Term the SAME centred-input contract: raw log_a_h with
            # sentinel, raw log_a_a, raw ng_logp.
            pred_nat = NF.native_predict(
                nf_sub, nf_nodes, log_a_h, log_a_a, ng_logp, w_art, MS._Pred)

            py_n += 1; py_c += int(pred_py == true)
            nat_n += 1; nat_c += int(pred_nat == true)
            total += 1; agree += int(pred_py == pred_nat)

    return {
        "n": total,
        "py_acc": py_c / max(1, py_n),
        "nat_acc": nat_c / max(1, nat_n),
        "agreement": agree / max(1, total),
        "agree": agree,
        "disagree": total - agree,
    }


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 80)
    print("native_fusion_accept — NATIVE fusion Term vs PYTHON fusion (FSDD LOSO)")
    print("Rank-1 migration audit: the new hearing path's FUSION DECISION, now graph-resident.")
    print("=" * 80, flush=True)
    r = run(quick=quick, verbose=True)
    print("-" * 80)
    print(f"  n (held-out tokens, never banked) : {r['n']}")
    print(f"  PYTHON-fusion accuracy            : {r['py_acc']:.4f}")
    print(f"  NATIVE-fusion accuracy            : {r['nat_acc']:.4f}")
    print(f"  per-token AGREEMENT rate          : {r['agreement']:.4f} "
          f"({r['agree']}/{r['n']}, disagree={r['disagree']})")
    print(f"  chance                            : {1.0/len(DIGITS):.4f}")
    print(f"  elapsed                           : {time.time()-t0:.1f}s")
    print("=" * 80)
    if r["agreement"] >= 0.9999:
        print("VERDICT: FAITHFUL — the native Term reproduces the Python decision EXACTLY.")
        print("The new path's fusion DECISION is now a graph-resident Rust Term.")
    else:
        print(f"VERDICT: DISCREPANCY — agreement {r['agreement']:.4f} < 1.0; "
              f"{r['disagree']} tokens differ. Root-cause required.")
    print("NATIVE_FUSION_ACCEPT_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
