"""iter49_node_admissibility_graphs — ADMISSIBILITY GRAPHS ON THE NODES THEMSELVES.

THE USER: "the finer grain is admissibility graphs on the nodes themselves."

iter-48 found per-NODE reliability is too COARSE: a wrong-order node confidently-wrong on
a SPECIFIC contrast but HIGH on AVERAGE keeps its per-node weight high and DILUTES that
contrast. THE FIX (this iter): each (cue x order) node gets its OWN admissibility
sub-graph — its per-WORD reliability, measured inner-LOSO on TRAIN speakers only — GATING
its contribution PER candidate word:

    score(w) = PROD_i  P_i(w) ^ weight_i(w)          (graph Times of Pow; weight PER word)
    weight_i(w) = max(0, (precision_i(w) - chance)/(1 - chance))

precision_i(w) = node i's inner-LOSO PRECISION for w on TRAIN speakers (of the held-out
train tokens it CLAIMED were w, the fraction truly w). So a node confidently-WRONG when it
claims w gets low weight_i(w) -> ABSTAINS on w (P^0) -> the per-contrast dilution
disappears. iter-48 (per-node) is the special case weight_i(w)==weight_i; iter-45 (equal)
is weight_i(w)==1. MEASURED not searched; LOSO-clean; NO fit/sweep/gradient/donkey.

EVALUATE: FSDD LOSO, multi-metric, SHUFFLE, per-fold. The decisive read: does PER-CONTRAST
admissibility (each node's admissibility graph) ACT on the dilution and LIFT recognition
past iter-48's per-node weight (0.594) and past iter-44 (0.644)? ALSO report the
per-contrast measurement SPARSITY (precision sample size per (node,word)) — if it is too
thin to act cleanly on this small venue, that is the scale-the-venue convergence.

  PYTHONUNBUFFERED=1 python -m scripts.iter49_node_admissibility_graphs [n_per] [rounds] [n_max] [ridge]
"""
import os
import sys
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_whisper import gather, load_wav
import scripts.enriched_hvpt_accept as EH
import domains.many_settings_recognizer as MS
import domains.node_admissibility_graphs as NA
from domains.order_n_interpolation import (
    word_cloud_models, order_n_channel_likelihood,
)
from scripts.iter45_ordern_interpolation import heldout_combined_ordern
from scripts.many_settings_hvpt_accept import heldout_1nn
from scripts.iter41_speaker_invariance import train_speaker_labels
# iter-48 per-node weights, for the per-node comparator + the no-claim fallback.
from scripts.iter48_weighted_admissibility import (
    measure_node_reliabilities, heldout_combined_weighted,
)


# ---------------------------------------------------------------------------
# (A) The PER-CONTRAST reliability MEASUREMENT — each node's admissibility sub-graph.
# Inner leave-one-speaker-out on the TRAIN folds ONLY. For each (order x channel) node and
# each candidate word w, the node's PRECISION for w: of the held-out train tokens whose
# single-node argmax-likelihood prediction was w, the fraction whose TRUTH was w. Mapped to
# weight_i(w) = (precision - chance)/(1 - chance), clipped at 0. A node that confidently
# CLAIMS w but is usually wrong when it claims w -> low precision -> abstains on w.
#
# Returns per node a dict {word: weight} (the node's admissibility sub-graph) PLUS the
# per-(node,word) claim-count (the precision sample size — the sparsity probe) PLUS the
# per-node overall accuracy (iter-48 fallback when a node never claimed a word, so it has
# no precision sample — graceful, LOSO-clean default).
# NO test leakage (the outer-held voice is absent from train); NO sweep.
# ---------------------------------------------------------------------------

def measure_per_contrast_reliabilities(vec_train, train_words, train_spk, orders,
                                       n_max, ridge, chance):
    """Per (order x channel) node, the inner-LOSO PER-WORD precision on TRAIN speakers,
    mapped to a per-word reliability weight. Returns:
      node_word_weight : list (node order [ci,o]) of {word: weight}  (admissibility graph)
      node_word_claims : list of {word: n_times_node_claimed_word}    (sparsity probe)
      node_acc         : list of node overall inner-LOSO accuracy     (per-node fallback)
    Node order matches the weighted product: for ci in channels, for o in orders.
    MEASURED (the same per-node argmax-likelihood the harness scores with), LOSO-clean."""
    spk = np.asarray(train_spk)
    inner_speakers = sorted(set(train_spk))
    cands = sorted(set(train_words))
    n_vec = len(vec_train)
    node_word_weight = []
    node_word_claims = []
    node_acc = []
    for ci in range(n_vec):
        Xc = np.asarray(vec_train[ci])
        tw = np.asarray(train_words)
        # per order: collect (predicted_word, truth) over all inner held tokens.
        per_order_pairs = {o: [] for o in orders}
        for held_spk in inner_speakers:
            tr_mask = (spk != held_spk)
            he_mask = (spk == held_spk)
            if not he_mask.any() or not tr_mask.any():
                continue
            inner_tr_vecs = Xc[tr_mask]
            inner_tr_words = list(tw[tr_mask])
            inner_he_vecs = Xc[he_mask]
            inner_he_words = list(tw[he_mask])
            mans = word_cloud_models(inner_tr_vecs, inner_tr_words, n_max=n_max)
            for o in orders:
                for q, truth in zip(inner_he_vecs, inner_he_words):
                    p = order_n_channel_likelihood(q, mans, cands, o, ridge=ridge)
                    pred = max(p, key=p.get)
                    per_order_pairs[o].append((pred, truth))
        for o in orders:
            pairs = per_order_pairs[o]
            n_tot = len(pairs)
            n_correct = sum(int(pr == tr) for pr, tr in pairs)
            acc = n_correct / n_tot if n_tot else chance
            # per-word PRECISION: of tokens the node claimed were w, fraction truly w.
            claimed = defaultdict(int)
            claimed_correct = defaultdict(int)
            for pr, tr in pairs:
                claimed[pr] += 1
                if pr == tr:
                    claimed_correct[pr] += 1
            ww = {}
            wclaims = {}
            for w in cands:
                c = claimed.get(w, 0)
                wclaims[w] = c
                if c > 0:
                    prec = claimed_correct[w] / c
                    ww[w] = NA.per_contrast_weight(prec, chance)
                else:
                    # the node NEVER claimed w on inner-LOSO -> no precision sample.
                    # Fall back to the node's OVERALL reliability (iter-48 per-node weight)
                    # — a graceful, LOSO-clean default (no claim => use the coarse signal).
                    ww[w] = NA.reliability_to_weight(acc, chance)
            node_word_weight.append(ww)
            node_word_claims.append(wclaims)
            node_acc.append(acc)
    return node_word_weight, node_word_claims, node_acc


# ---------------------------------------------------------------------------
# (B) The PER-CONTRAST weighted combine-all. Identical node layout + decision Term to
# iter-48 (Argmax of Times-of-Pow over (order x channel) nodes); the ONLY change is the
# weight attr w_ch{i} is set PER candidate word (from the node's admissibility sub-graph)
# rather than node-constant. node_word_weight[ni][w] gates node ni's contribution to w.
# ---------------------------------------------------------------------------

_PSUB = None
_PTERM = None
_PNCH = None
_PCANDS = None
_PWC: dict = {}


def _p_substrate(candidate_words, n_node):
    global _PSUB, _PTERM, _PNCH, _PCANDS
    cand_key = frozenset(candidate_words)
    if _PSUB is None or _PNCH != n_node or _PCANDS != cand_key:
        from substrate_rs import Substrate
        _PSUB = Substrate()
        _PTERM = MS._Pred(NA.predict_weighted_term(n_node))
        _PNCH = n_node
        _PCANDS = cand_key
        _PWC.clear()
    for w in candidate_words:
        if w not in _PWC:
            c = _PSUB.add_node("Concept", {"name": w})
            _PSUB.set_attr(c, MS.WORD_ATTR, 1.0)
            _PWC[w] = c
    return _PSUB


def heldout_combined_per_contrast(vec_train, vec_test, train_words, test_words,
                                  orders, node_word_weight, n_max, ridge=0.0,
                                  return_preds=False):
    """Per-CONTRAST weighted-product recognition over (len(orders) x n_vec) order-N nodes.
    Same nodes / decision Term as iter-48; each node ni's likelihood for candidate w is
    raised to weight_i(w) = node_word_weight[ni][w] (the node's admissibility sub-graph for
    w) before the product. NO fit; the per-word weights were MEASURED on train."""
    n_vec = len(vec_train)
    n_order = len(orders)
    n_node = n_vec * n_order
    assert len(node_word_weight) == n_node, (len(node_word_weight), n_node)
    candidates = sorted(set(train_words))
    chan_models = [word_cloud_models(vec_train[ci], train_words, n_max=n_max)
                   for ci in range(n_vec)]
    sub = _p_substrate(candidates, n_node)
    flat = 1.0 / max(len(candidates), 1)   # the word-neutral flat reference an
    #                                        inadmissible node blends toward (abstains).
    # set the (constant-per-fold) PER-WORD per-node weights + the flat reference once.
    for w in candidates:
        for ni in range(n_node):
            sub.set_attr(_PWC[w], NA.weight_attr(ni), float(node_word_weight[ni][w]))
            sub.set_attr(_PWC[w], NA.flat_attr(ni), flat)
    correct = 0
    preds = []
    n_test = len(test_words)
    for qi in range(n_test):
        ni = 0
        for ci in range(n_vec):
            qv = np.asarray(vec_test[ci][qi])
            for o in orders:
                p = order_n_channel_likelihood(qv, chan_models[ci], candidates,
                                               o, ridge=ridge)
                for w in candidates:
                    sub.set_attr(_PWC[w], MS.channel_attr(ni), p[w])
                ni += 1
        pred = sub.evaluate(_PTERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        preds.append(pw)
        correct += int(pw == test_words[qi])
    if return_preds:
        return preds
    return correct / max(n_test, 1)


# ---------------------------------------------------------------------------
# Score one LOSO fold: PER-CONTRAST vs PER-NODE (iter-48) vs EQUAL (iter-45) vs iter-44
# vs 1-NN, with the error-overlap of per-contrast vs per-node, and the sparsity probe.
# ---------------------------------------------------------------------------

def score_fold(voice_audio, held_voice, rounds=2, shuffle=False, n_max=2, ridge=0.0):
    from scripts.iter44_interpolation_subnodes import heldout_combined_manifold

    fold = EH.build_fold(voice_audio, held_voice, rounds, shuffle=shuffle,
                         skip_axs=True)
    tw, hw = fold["train_words"], fold["held_words"]
    spk = train_speaker_labels(voice_audio, held_voice, shuffle=shuffle)
    assert len(spk) == len(tw), (len(spk), len(tw))

    vec_tr = fold["many_train"] + fold["ortho_train"]
    vec_he = fold["many_held"] + fold["ortho_held"]
    names = fold["many_names"] + fold["ortho_names"]
    orders = list(range(n_max + 1))
    cands = sorted(set(tw))
    chance = 1.0 / max(len(cands), 1)

    # (1) MEASURE per-CONTRAST reliability (each node's admissibility sub-graph) on TRAIN.
    nww, nwc, nacc = measure_per_contrast_reliabilities(vec_tr, tw, spk, orders,
                                                        n_max, ridge, chance)
    # (1b) the iter-48 per-NODE weights (the coarse comparator) — same inner-LOSO.
    pn_weights, pn_accs = measure_node_reliabilities(vec_tr, tw, spk, orders,
                                                     n_max, ridge, chance)

    # (2) the comparators.
    per_contrast = heldout_combined_per_contrast(vec_tr, vec_he, tw, hw, orders, nww,
                                                 n_max=n_max, ridge=ridge)
    per_node = heldout_combined_weighted(vec_tr, vec_he, tw, hw, orders, pn_weights,
                                         n_max=n_max, ridge=ridge)
    equal = heldout_combined_ordern(vec_tr, vec_he, tw, hw, orders,
                                    n_max=n_max, ridge=ridge)
    interp44 = heldout_combined_manifold(vec_tr, vec_he, tw, hw, rank=3, ridge=ridge)
    nn = EH.heldout_combined(vec_tr, vec_he, tw, hw)
    frozen = heldout_1nn(fold["frozen_train"], tw, fold["frozen_held"], hw)

    # error-overlap per-contrast vs per-node (does the finer grain ACT on the dilution?).
    pc_pred = heldout_combined_per_contrast(vec_tr, vec_he, tw, hw, orders, nww,
                                            n_max=n_max, ridge=ridge, return_preds=True)
    pn_pred = heldout_combined_weighted(vec_tr, vec_he, tw, hw, orders, pn_weights,
                                        n_max=n_max, ridge=ridge, return_preds=True)
    pn_err = [i for i, (p, w) in enumerate(zip(pn_pred, hw)) if p != w]
    pc_fix = sum(int(pc_pred[i] == hw[i]) for i in pn_err)
    pc_err = [i for i, (p, w) in enumerate(zip(pc_pred, hw)) if p != w]
    pn_fix = sum(int(pn_pred[i] == hw[i]) for i in pc_err)

    # sparsity probe: per-(node,word) precision sample size (claim counts).
    claim_counts = [c for wc in nwc for c in wc.values()]
    nonzero_claims = [c for c in claim_counts if c > 0]
    frac_no_claim = 1.0 - (len(nonzero_claims) / max(len(claim_counts), 1))

    return {"held_voice": held_voice, "shuffle": shuffle, "n_max": n_max, "ridge": ridge,
            "per_contrast": per_contrast, "per_node": per_node, "equal": equal,
            "interp44": interp44, "nn": nn, "frozen": frozen,
            "orders": orders, "names": names, "chance": chance,
            "n_held": len(hw), "n_train": len(tw),
            "pn_err": len(pn_err), "pc_fixes_pn": pc_fix,
            "pc_err": len(pc_err), "pn_fixes_pc": pn_fix,
            "node_word_weight": nww, "node_acc": nacc,
            "claim_mean": float(np.mean(nonzero_claims)) if nonzero_claims else 0.0,
            "claim_median": float(np.median(nonzero_claims)) if nonzero_claims else 0.0,
            "claim_min": int(min(nonzero_claims)) if nonzero_claims else 0,
            "frac_no_claim": frac_no_claim, "n_cells": len(claim_counts)}


def _report(r):
    tag = " [SHUFFLE]" if r["shuffle"] else ""
    print(f"\n--- held-out {r['held_voice']}{tag}  (held {r['n_held']} train "
          f"{r['n_train']}, n_max={r['n_max']} ridge={r['ridge']}) ---", flush=True)
    print(f"  PER-CONTRAST {r['per_contrast']:.3f}   PER-NODE(iter48) {r['per_node']:.3f}"
          f"   EQUAL(iter45) {r['equal']:.3f}   iter-44 {r['interp44']:.3f}   "
          f"1-NN {r['nn']:.3f}   frozen {r['frozen']:.3f}", flush=True)
    print(f"    Δ(per-contrast - per-node) {r['per_contrast']-r['per_node']:+.3f}   "
          f"Δ(per-contrast - equal) {r['per_contrast']-r['equal']:+.3f}   "
          f"Δ(per-contrast - iter44) {r['per_contrast']-r['interp44']:+.3f}", flush=True)
    print(f"  error-overlap: per-contrast fixes {r['pc_fixes_pn']}/{r['pn_err']} of "
          f"per-node's errors;  per-node fixes {r['pn_fixes_pc']}/{r['pc_err']} of "
          f"per-contrast's", flush=True)
    print(f"  SPARSITY (precision sample per (node,word)): claims/cell mean "
          f"{r['claim_mean']:.1f} median {r['claim_median']:.0f} min {r['claim_min']}; "
          f"{r['frac_no_claim']*100:.0f}% of {r['n_cells']} cells had NO claim "
          f"(fell back to per-node)", flush=True)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    ridge = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    random.seed(1)
    np.random.seed(1)

    print("=" * 72, flush=True)
    print("ITER-49 — ADMISSIBILITY GRAPHS ON THE NODES THEMSELVES", flush=True)
    print("  gated_i(w) = weight_i(w)*P_i(w) + (1-weight_i(w))*u_i  (convex blend to flat)", flush=True)
    print("  score(w) = PROD_i gated_i(w) ; weight_i(w) PER candidate word", flush=True)
    print("  weight_i(w) = (precision_i(w) - chance)/(1-chance)  [inner-LOSO precision]", flush=True)
    print("  each (cue x order) node has its OWN per-word admissibility sub-graph", flush=True)
    print("  MEASURED not searched; LOSO-clean; NO fit/sweep/gradient/donkey", flush=True)
    print(f"  orders 0..{n_max} per channel, ridge={ridge}", flush=True)
    print("=" * 72, flush=True)

    items = gather(n_per_class_per_speaker=n_per)
    voice_audio = {}
    for p, d, s in items:
        x, fs = load_wav(p)
        voice_audio.setdefault(s, []).append((x, fs, str(d)))
    speakers = sorted(voice_audio)
    print(f"FSDD: {sum(len(v) for v in voice_audio.values())} recordings, "
          f"{len(speakers)} speakers {speakers}", flush=True)

    real, shuf = [], []
    for held in speakers:
        r = score_fold(voice_audio, held, rounds, shuffle=False, n_max=n_max, ridge=ridge)
        _report(r); real.append(r)
        sr = score_fold(voice_audio, held, rounds, shuffle=True, n_max=n_max, ridge=ridge)
        _report(sr); shuf.append(sr)

    def mean(rs, key):
        return float(np.mean([x[key] for x in rs]))

    print("\n" + "=" * 72, flush=True)
    print("VERDICT (mean over 6 held-out FSDD speakers, chance 0.100)", flush=True)
    print("=" * 72, flush=True)
    pc = mean(real, "per_contrast"); pn = mean(real, "per_node"); eq = mean(real, "equal")
    i44 = mean(real, "interp44"); nn = mean(real, "nn"); fr = mean(real, "frozen")
    spc = mean(shuf, "per_contrast"); spn = mean(shuf, "per_node")
    seq = mean(shuf, "equal"); si44 = mean(shuf, "interp44"); snn = mean(shuf, "nn")

    print(f"  PER-CONTRAST admissibility graphs (this iter)  {pc:.3f}", flush=True)
    print(f"  PER-NODE weighted (iter-48)                    {pn:.3f}", flush=True)
    print(f"  EQUAL combine-all (iter-45)                    {eq:.3f}", flush=True)
    print(f"  iter-44 single-interp (order-1)                {i44:.3f}", flush=True)
    print(f"  1-NN graph (order-0 point estimate)            {nn:.3f}", flush=True)
    print(f"  frozen                                         {fr:.3f}", flush=True)
    print(f"  *** per-contrast vs PER-NODE  Δ {pc-pn:+.3f}  "
          f"=> {'FINER GRAIN LIFTS over per-node' if pc > pn else 'NO LIFT' if pc==pn else 'HURTS'}",
          flush=True)
    print(f"  *** per-contrast vs EQUAL     Δ {pc-eq:+.3f}", flush=True)
    print(f"  *** per-contrast vs iter-44   Δ {pc-i44:+.3f}  "
          f"=> {'beats iter-44 0.644' if pc > i44 else 'no gain over iter-44' if pc==i44 else 'BELOW iter-44'}",
          flush=True)
    print(f"  *** per-contrast vs 1-NN      Δ {pc-nn:+.3f}", flush=True)

    print("\n  SHUFFLE control (voice partition scrambled, reliability measured on it too):",
          flush=True)
    print(f"    PER-CONTRAST real {pc:.3f}  shuffle {spc:.3f}  => margin {pc-spc:+.3f}  "
          f"({'CLEAN' if pc > spc else 'NOT CLEAN'})", flush=True)
    print(f"    PER-NODE     real {pn:.3f}  shuffle {spn:.3f}  => margin {pn-spn:+.3f}", flush=True)
    print(f"    EQUAL        real {eq:.3f}  shuffle {seq:.3f}  => margin {eq-seq:+.3f}", flush=True)
    print(f"    iter-44      real {i44:.3f}  shuffle {si44:.3f}  => margin {i44-si44:+.3f}", flush=True)
    print(f"    1-NN         real {nn:.3f}  shuffle {snn:.3f}  => margin {nn-snn:+.3f}", flush=True)
    print(f"    => per-contrast margin {'WIDER' if (pc-spc) > (pn-spn) else 'NOT wider'} "
          f"than per-node ({pc-spc:+.3f} vs {pn-spn:+.3f}); "
          f"{'reaches' if (pc-spc) >= (nn-snn) else 'below'} 1-NN ({nn-snn:+.3f})", flush=True)

    pn_err = sum(r["pn_err"] for r in real)
    pc_fix = sum(r["pc_fixes_pn"] for r in real)
    pc_err = sum(r["pc_err"] for r in real)
    pn_fix = sum(r["pn_fixes_pc"] for r in real)
    print(f"\n  ERROR-OVERLAP (aggregate): per-contrast fixes {pc_fix}/{pn_err} of "
          f"per-node's errors; per-node fixes {pn_fix}/{pc_err} of per-contrast's  "
          f"(net {pc_fix - pn_fix:+d} in per-contrast's favour)", flush=True)

    cm = mean(real, "claim_mean"); cmed = mean(real, "claim_median")
    fnc = mean(real, "frac_no_claim")
    print(f"\n  PER-CONTRAST MEASUREMENT SPARSITY (the scale-the-venue probe):", flush=True)
    print(f"    precision sample per (node,word) cell: mean {cm:.1f} claims, median "
          f"{cmed:.0f}; {fnc*100:.0f}% of cells had ZERO claims (fell back to per-node)",
          flush=True)
    print(f"    => {'ADEQUATE' if cmed >= 5 and fnc < 0.25 else 'THIN'} per-contrast "
          f"measurement on this venue", flush=True)

    print("\n(per-contrast admissibility graphs = the iter-48 weighted combine-all with "
          "each (cue x order) node's weight set PER candidate word from the node's "
          "inner-LOSO per-word PRECISION (its admissibility sub-graph), so a node "
          "confidently-wrong on a contrast ABSTAINS on that contrast. The weight is a "
          "MEASUREMENT not a searched param; LOSO-clean; the decision is the SAME graph "
          "Term Argmax of Times-of-Pow. Recursive admissibility: the recognition is "
          "admissible iff its nodes are, each node admissible iff its sub-graph says so "
          "for THIS contrast. NO fit, NO sweep, NO gradient, NO donkey.)", flush=True)


if __name__ == "__main__":
    main()
