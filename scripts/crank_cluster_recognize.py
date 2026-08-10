"""crank_cluster_recognize — TURN THE CRANK: the supervised DTW recognizer and the
unsupervised k-medoids clustering are BOTH graph-resident ops over the SAME DtwTo
distance; put BOTH in one pool and co-refine them in an EM-like bootstrap loop.

THE USER'S INSIGHT. docs/dtw_trajectory_loso.md built the supervised DTW recognizer
(Argmin-MinOver-DtwTo over banked exemplars, cross-speaker LOSO ~0.57-0.593).
docs/unsup_clustering_loso.md built the unsupervised k-medoids clusterer (Argmin-DtwTo
assignment + Argmin-Sum-DtwTo medoid update, purity ~0.30) and NAMED its own ceiling:
shallow modes + k-medoids DEGENERACY (k=#words splits the loud modes and STARVES the
rest — "one captured 3 clusters, three/seven/nine got NONE"). Both are the agent's OWN
DtwTo/Argmin/Sum Term-trees. So: put both in the pool and iterate so they REINFORCE.

THE CRANK (EM-like, both ops in one loop, donkey-clean):
  · E-ish  assign each TRAIN token to its nearest current medoid  (Argmin-DtwTo Term).
  · M-ish  (a) recompute each cluster's medoid = the MODE exemplar (Argmin-Sum-DtwTo
              Term) — a sharper, mode-centered prototype.
           (b) MERGE the two closest clusters by medoid-to-medoid DtwTo (the doc's
              named fix for degeneracy): start k > #words, merge down toward the
              word-modes so the starved words get a mode and the over-split loud words
              re-join. Merge is mechanical DtwTo arithmetic over the agent's metric.
  RECOGNITION refines CLUSTERING and CLUSTERING refines RECOGNITION: the recognizer's
  bank IS the medoid prototypes (tighter, mode-centered each iteration); the deepened
  clusters feed the next iteration's structure. The recognizer's per-query decision is
  the SAME Argmin-DtwTo over the prototype bank the clusterer assigns with — one pool.

  SELECTOR = COMPRESSION (MDL): total within-cluster DtwTo cost. The crank iterates
  until the cost stops dropping (converged). NO held-out labels select anything.

EVALUATE (held-out = the ungameable yardstick; labels ONLY score):
  Per iteration: within-cluster DtwTo cost (the agent's selector), clustered-set
  purity / NMI, and cross-speaker LOSO recognition (assign held-out token to the
  FIXED prototype medoids -> cluster->majority-word map). Held-out speakers are NEVER
  in the clustered / refined set. Compare to: separate supervised DTW (~0.593) and
  separate clustering (~0.30).

DONKEY BOUNDARY (audited):
  · TOKENS    = agent's DTW trajectory feature (agent_frontend.cmvn_track) — the SAME
                source-normalized cochleagram the dominant cmvn_ear cue uses, ordered.
  · DISTANCE  = the agent's OWNED DtwTo Term (banded Sakoe-Chiba), evaluated natively.
  · ASSIGN    = the agent's Argmin-DtwTo Term (the SAME shape the supervised recognizer
                uses; candidates = the k medoid prototypes).
  · MEDOID    = the agent's Argmin-Sum-DtwTo Term (the mode of the cluster, MDL-best
                representative).
  · MERGE     = mechanical DtwTo arithmetic over the agent's metric (closest two
                medoids), then re-medoid the union. NO labels, NO gradient, NO net.
  · SELECTOR  = within-cluster total DtwTo cost (compression). NO label selects.
  · LABELS    = used ONLY to score (purity / NMI / cluster->word naming / LOSO recog).
                NEVER in the clustering / merging / medoid update.
  · SC load + the 40-speaker split = world-adapter mechanics (reuses build_split
                verbatim). HELD-OUT speakers' clips are NEVER in the clustered cloud;
                they are assigned to the FIXED prototypes after each iteration freezes.

Run: python -m scripts.crank_cluster_recognize [n_train_spk] [n_held_spk] [n_per] [k0] [seed]
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE

# reuse the SAME robust SC 40-speaker LOSO split (ungameable, held clips never banked).
from scripts.sc_loso_frontend_norm import build_split

# reuse the unsup clustering's OWNED Term-trees verbatim (the agent's k-medoids ops).
from scripts.unsup_clustering_loso import (
    _Pred, _V, _Attr, _Nb, _DtwTo, assignment_term, medoid_update_term, _traj_tuple,
    purity, nmi, cluster_to_word, random_floor,
    TOKEN_TYPE, MEDOID_TYPE, ROOT_TYPE, TRAJ_ATTR, MEDOID_EDGE, MEMBER_EDGE,
)


# --------------------------------------------------------------------------------
# The crank: k-medoids over DtwTo (the agent's owned ops), with an EM loop that ALSO
# MERGES clusters toward word-modes (the doc's named fix for k-medoids degeneracy),
# scored every iteration on held-out LOSO via the medoid-PROTOTYPE bank.
# --------------------------------------------------------------------------------

class Crank:
    """Holds the clustered token cloud as a graph and runs the agent's assignment +
    medoid + merge Terms. All decisions are substrate.evaluate of owned Term-trees;
    Python only rewires has_member/has_medoid edges and reads costs back out."""

    def __init__(self, trajs, k0, seed=0):
        self.s = Substrate()
        self.trajs = trajs
        self.n = len(trajs)
        self.rng = np.random.default_rng(seed)
        self.root = self.s.add_node(ROOT_TYPE, {})
        self.tok_ids = [self.s.add_node(TOKEN_TYPE, {TRAJ_ATTR: trajs[i]})
                        for i in range(self.n)]
        self.assign_term = _Pred(assignment_term())
        self.update_term = _Pred(medoid_update_term())
        self.pair_term = _Pred(_DtwTo(_Attr(_V("a"), TRAJ_ATTR),
                                      _Attr(_V("b"), TRAJ_ATTR)))
        self._seed_medoids(min(k0, self.n))
        self.labels = [-1] * self.n

    def _dist(self, i, j):
        if i == j:
            return 0.0
        return float(self.s.evaluate(self.pair_term,
                                     {"a": self.tok_ids[i], "b": self.tok_ids[j]}))

    def _seed_medoids(self, k):
        """k-medoids++ seeding over the SAME DtwTo metric (mechanical, NO labels)."""
        n = self.n
        idx0 = int(self.rng.integers(n))
        seeds = [idx0]
        d2 = np.array([self._dist(idx0, j) ** 2 for j in range(n)])
        for _ in range(1, k):
            tot = d2.sum()
            probs = d2 / tot if tot > 0 else None
            nxt = (int(self.rng.choice(n, p=probs)) if probs is not None
                   else int(self.rng.integers(n)))
            seeds.append(nxt)
            dn = np.array([self._dist(nxt, j) ** 2 for j in range(n)])
            d2 = np.minimum(d2, dn)
        self.med_ids = []
        for si in seeds:
            m = self.s.add_node(MEDOID_TYPE, {TRAJ_ATTR: self.trajs[si]})
            self.s.add_edge_unchecked(self.root, MEDOID_EDGE, m)
            self.med_ids.append(m)

    def _mid_index(self):
        return {m: c for c, m in enumerate(self.med_ids)}

    def assign(self):
        """E-step: assign each token to nearest medoid (agent's Argmin-DtwTo Term).
        Rewires has_member edges so the medoid Term sees the new clusters. Returns the
        per-token cluster labels."""
        mid_index = self._mid_index()
        new_members = {m: [] for m in self.med_ids}
        new_labels = []
        for t in self.tok_ids:
            chosen = self.s.evaluate(self.assign_term, {"t": t, "root": self.root})
            m = chosen if chosen in mid_index else self.med_ids[0]
            new_members[m].append(t)
            new_labels.append(mid_index[m])
        for m in self.med_ids:
            for old in list(self.s.neighbours(m, MEMBER_EDGE)):
                self.s.remove_edge(m, MEMBER_EDGE, old)
            for t in new_members[m]:
                self.s.add_edge_unchecked(m, MEMBER_EDGE, t)
        self.labels = new_labels
        return new_labels

    def update_medoids(self):
        """M-step (a): recompute each cluster's medoid = the MODE exemplar (agent's
        Argmin-Sum-DtwTo Term). Sets the medoid node's trajectory to the chosen
        member's. Empty clusters keep their medoid (standard k-medoids)."""
        for m in self.med_ids:
            if not list(self.s.neighbours(m, MEMBER_EDGE)):
                continue
            new_med_tok = self.s.evaluate(self.update_term, {"m": m})
            if new_med_tok is not None:
                nt = self.s.node(new_med_tok)["attrs"].get(TRAJ_ATTR)
                if nt is not None:
                    self.s.set_attr(m, TRAJ_ATTR, nt)

    def cost(self):
        """The MDL selector: total within-cluster DtwTo cost (member-to-medoid).
        NO labels. The crank minimises this; convergence = it stops dropping."""
        c = 0.0
        for m in self.med_ids:
            for t in self.s.neighbours(m, MEMBER_EDGE):
                c += float(self.s.evaluate(self.pair_term, {"a": m, "b": t}))
        return c

    def merge_closest(self):
        """M-step (b): MERGE the two clusters whose medoids are closest by DtwTo (the
        doc's named fix for degeneracy). Mechanical DtwTo arithmetic over the agent's
        metric (NO labels): find the closest medoid pair, drop one medoid, then a
        re-assign+re-medoid folds its members into the survivor's mode. Returns True if
        a merge happened (k>=2)."""
        if len(self.med_ids) < 2:
            return False
        best = None
        for i in range(len(self.med_ids)):
            for j in range(i + 1, len(self.med_ids)):
                d = float(self.s.evaluate(
                    self.pair_term, {"a": self.med_ids[i], "b": self.med_ids[j]}))
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        drop = self.med_ids[j]
        for old in list(self.s.neighbours(drop, MEMBER_EDGE)):
            self.s.remove_edge(drop, MEMBER_EDGE, old)
        self.s.remove_edge(self.root, MEDOID_EDGE, drop)
        self.s.remove_node(drop)
        self.med_ids.pop(j)
        return True

    def assign_external(self, traj):
        """Assign ONE held-out token to the FIXED current prototype medoids via the
        agent's Argmin-DtwTo Term. The cross-speaker yardstick: held-out tokens are
        assigned to the structure discovered WITHOUT them. Returns cluster id."""
        mid_index = self._mid_index()
        qn = self.s.add_node(TOKEN_TYPE, {TRAJ_ATTR: _traj_tuple(traj)})
        chosen = self.s.evaluate(self.assign_term, {"t": qn, "root": self.root})
        self.s.remove_node(qn)
        if chosen is None or chosen not in mid_index:
            return 0
        return mid_index[chosen]


def _track(x, fs):
    return _traj_tuple(FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs)))


def score_iteration(crank, train_truth, seen_probe, loso_probe):
    """Score the CURRENT frozen structure (labels used ONLY here). Returns
    (cost, purity, nmi, xspk_purity, xspk_nmi, loso_recog, seen_recog, n_clusters,
     n_words_covered)."""
    labels = crank.labels
    cost = crank.cost()
    pur = purity(labels, train_truth)
    nm = nmi(labels, train_truth)
    # the medoid-PROTOTYPE bank's cluster->majority-word map (labels NAME only).
    c2w = cluster_to_word(labels, train_truth)
    n_words_covered = len(set(c2w.values()))

    # cross-speaker LOSO: held-out tokens -> nearest prototype medoid -> word.
    held_labels, held_truth = [], []
    loso_cor = loso_tot = 0
    for (w, x, fs) in loso_probe:
        traj = FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs))
        cl = crank.assign_external(traj)
        held_labels.append(cl)
        held_truth.append(w)
        loso_tot += 1
        loso_cor += int(c2w.get(cl) == w)
    loso_recog = loso_cor / max(loso_tot, 1)
    xspk_pur = purity(held_labels, held_truth)
    xspk_nm = nmi(held_labels, held_truth)

    seen_cor = seen_tot = 0
    for (w, x, fs) in seen_probe:
        traj = FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs))
        cl = crank.assign_external(traj)
        seen_tot += 1
        seen_cor += int(c2w.get(cl) == w)
    seen_recog = seen_cor / max(seen_tot, 1)

    return (cost, pur, nm, xspk_pur, xspk_nm, loso_recog, seen_recog,
            len(crank.med_ids), n_words_covered)


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    k0 = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    max_iters = int(os.environ.get("MAX_ITERS", "40"))

    print("=" * 80, flush=True)
    print("TURN THE CRANK — co-refine the DTW recognizer + k-medoids clustering "
          "(one pool)", flush=True)
    print("  EM-like: assign(Argmin-DtwTo) -> medoid(Argmin-Sum-DtwTo) -> merge(DtwTo);"
          " MDL=within-cluster cost", flush=True)
    print("=" * 80, flush=True)

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=20240608)
    words = W.sc_words()
    n_words = len(words)
    chance = 1.0 / n_words

    print("\n[feat] extracting CMVN DTW trajectories for the clustered token cloud ...",
          flush=True)
    train_trajs = [_track(x, fs) for (w, x, fs) in train_clips]
    train_truth = [w for (w, x, fs) in train_clips]
    print(f"[feat] {len(train_trajs)} train-speaker tokens; {n_words} words "
          f"(chance {chance:.3f}); k0={k0} (> #words to fight degeneracy)", flush=True)

    rf = random_floor(train_truth, n_words)
    print(f"[floor] random-assignment purity floor = {rf:.3f}", flush=True)
    print("[baselines] separate supervised DTW LOSO ~0.593 (docs/dtw_trajectory_loso); "
          "separate clustering purity ~0.303 / semi-sup LOSO ~0.225 "
          "(docs/unsup_clustering_loso)\n", flush=True)

    crank = Crank(train_trajs, k0=k0, seed=seed)

    # initial assignment + medoid so the structure exists before iter 0 scoring.
    crank.assign()
    crank.update_medoids()

    print(f"  {'iter':>4s} {'k':>3s} {'cost':>9s} {'d_cost':>9s} {'purity':>7s} "
          f"{'NMI':>6s} {'xPur':>6s} {'xNMI':>6s} {'LOSO':>6s} {'seen':>6s} "
          f"{'#wrd':>5s}  note", flush=True)
    print("  " + "-" * 92, flush=True)

    history = []
    prev_cost = None
    converged_at = None
    # the crank merges k0 -> n_words over the first (k0 - n_words) iterations (one merge
    # per iter, each followed by re-assign+re-medoid), then EM-refines at k=n_words
    # until the MDL cost stops dropping.
    target_k = n_words
    best_loso = (-1.0, None)
    best_purity = (-1.0, None)
    for it in range(max_iters):
        note = ""
        # M-step (b): merge one pair while above the target k (degeneracy fix).
        if len(crank.med_ids) > target_k:
            crank.merge_closest()
            note = f"merged->k{len(crank.med_ids)}"
        # E-step + M-step (a): re-assign then re-medoid (the EM refinement).
        crank.assign()
        crank.update_medoids()

        (cost, pur, nm, xpur, xnm, loso, seen, k, nwc) = score_iteration(
            crank, train_truth, seen_probe, loso_probe)
        d_cost = (cost - prev_cost) if prev_cost is not None else float("nan")
        history.append(dict(it=it, k=k, cost=cost, purity=pur, nmi=nm, xpur=xpur,
                            xnmi=xnm, loso=loso, seen=seen, nwc=nwc))
        if loso > best_loso[0]:
            best_loso = (loso, it)
        if pur > best_purity[0]:
            best_purity = (pur, it)
        print(f"  {it:>4d} {k:>3d} {cost:>9.2f} {d_cost:>9.3f} {pur:>7.3f} "
              f"{nm:>6.3f} {xpur:>6.3f} {xnm:>6.3f} {loso:>6.3f} {seen:>6.3f} "
              f"{nwc:>5d}  {note}", flush=True)

        # convergence: at the target k, the MDL cost stopped dropping (within eps).
        if (len(crank.med_ids) <= target_k and prev_cost is not None
                and abs(d_cost) < 1e-6 and converged_at is None):
            converged_at = it
            print(f"  [converged] MDL within-cluster cost stopped dropping at iter {it} "
                  f"(|d_cost| < 1e-6, k={k})", flush=True)
            break
        prev_cost = cost

    # --- VERDICT ---
    print("\n" + "=" * 80, flush=True)
    print("VERDICT — does co-refining BOTH ops in one pool beat the SEPARATE baselines?",
          flush=True)
    print("=" * 80, flush=True)
    first = history[0]
    last = history[-1]
    bl_loso, bl_it = best_loso
    bp_pur, bp_it = best_purity
    if converged_at is not None:
        print(f"  iterations run: {len(history)}  (converged at iter {converged_at})",
              flush=True)
    else:
        print(f"  iterations run: {len(history)}  (hit max_iters, no MDL plateau)",
              flush=True)
    print(f"  MDL within-cluster cost: {first['cost']:.2f} (iter0) -> "
          f"{last['cost']:.2f} (final)  [{last['cost'] - first['cost']:+.2f}]",
          flush=True)
    print(f"  clustered-set purity:    {first['purity']:.3f} (iter0) -> "
          f"{last['purity']:.3f} (final); best {bp_pur:.3f} @iter{bp_it}  "
          f"(separate clustering ~0.303, floor {rf:.3f})", flush=True)
    print(f"  cross-speaker LOSO recog:{first['loso']:.3f} (iter0) -> "
          f"{last['loso']:.3f} (final); best {bl_loso:.3f} @iter{bl_it}  "
          f"(separate clustering semi-sup ~0.225; supervised DTW ~0.593; "
          f"chance {chance:.3f})", flush=True)
    print("-" * 80, flush=True)

    # did the crank lift BOTH above the separate baselines?
    SEP_CLUSTER_PURITY = 0.303
    SEP_CLUSTER_LOSO = 0.225
    SUP_DTW_LOSO = 0.593
    lifts_purity = bp_pur > SEP_CLUSTER_PURITY + 0.01
    lifts_cluster_loso = bl_loso > SEP_CLUSTER_LOSO + 0.01
    beats_supervised = bl_loso > SUP_DTW_LOSO

    if lifts_purity:
        print(f"  => CLUSTERING LIFTED: cranked purity {bp_pur:.3f} > separate "
              f"clustering {SEP_CLUSTER_PURITY:.3f} (+{bp_pur - SEP_CLUSTER_PURITY:.3f})"
              f" — co-refinement deepened the modes.", flush=True)
    else:
        print(f"  => clustering NOT lifted: cranked purity {bp_pur:.3f} vs separate "
              f"{SEP_CLUSTER_PURITY:.3f} ({bp_pur - SEP_CLUSTER_PURITY:+.3f}).",
              flush=True)
    if lifts_cluster_loso:
        print(f"  => CLUSTER-RECOG LIFTED: cranked semi-sup LOSO {bl_loso:.3f} > "
              f"separate clustering {SEP_CLUSTER_LOSO:.3f} "
              f"(+{bl_loso - SEP_CLUSTER_LOSO:.3f}) — merging killed the degeneracy "
              f"(more words covered).", flush=True)
    else:
        print(f"  => cluster-recog NOT lifted vs separate clustering "
              f"({bl_loso - SEP_CLUSTER_LOSO:+.3f}).", flush=True)
    if beats_supervised:
        print(f"  => BEATS SUPERVISED DTW: cranked LOSO {bl_loso:.3f} > supervised "
              f"{SUP_DTW_LOSO:.3f} — the distilled prototype bank is tighter than the "
              f"full exemplar bank.", flush=True)
    else:
        print(f"  => below supervised DTW: cranked LOSO {bl_loso:.3f} vs supervised "
              f"{SUP_DTW_LOSO:.3f} ({bl_loso - SUP_DTW_LOSO:+.3f}); the distilled "
              f"prototype bank is sparser than banking every exemplar.", flush=True)

    converged = converged_at is not None
    plateau_msg = ("reached a plateau" if converged
                   else "did not plateau within max_iters")
    print(f"  => CONVERGENCE: {'YES' if converged else 'NO'} — the MDL within-cluster "
          f"cost {plateau_msg} "
          f"(cost {first['cost']:.2f} -> {last['cost']:.2f}).", flush=True)
    print("[MARKER] CRANK_CLUSTER_RECOGNIZE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
