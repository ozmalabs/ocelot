"""unsup_clustering_loso — the agent's OWN frontier pick: UNSUPERVISED CROSS-SPEAKER
CLUSTERING over its DTW-trajectory tokens, NO labels in the clustering.

The agent's live self-assessment (docs/ask_the_agent_frontier.md) named this its
frontier, ranked it most foundational by compression-payoff over its own 637 held
postulates, and corroborated it with a perception yardstick reading frontier='none'
on bottom-up units:

  "an unlabelled DISTRIBUTION has recoverable LATENT structure ... unsupervised
   CLUSTERING carves its categories at the valleys between modes with NO labels —
   across speakers, the same word's tokens are one cluster."

The token representation is the agent's speaker-invariant DTW TRAJECTORY (the +0.152
cross-speaker breakthrough, docs/dtw_trajectory_loso.md): each clip is the ordered
CMVN cochleagram trajectory (agent_frontend.cmvn_track), and the distance between two
tokens is the agent's OWNED DtwTo Term (banded Sakoe-Chiba alignment) — the roughly
speaker-invariant token distance that gives supervised LOSO 0.593.

THE CLUSTERING (graph-resident structure discovery, NO gradient, NO labels). We use
K-MEDOIDS over the DtwTo distance, because the medoid is an ACTUAL token (no mean is
defined for variable-length trajectories), and both of its steps are the agent's
OWNED graph Term-trees, evaluated NATIVELY (the SAME shape as the DTW recognizer's
Argmin-MinOver-DtwTo decision, one layer up — tokens not exemplars, medoids not words):

  assignment   each TOKEN t -> the nearest MEDOID:
                 assign(t) = Argmin_{m in medoids} DtwTo(traj(t), traj(m))
               (identical to the recognizer's per-word distance; here the candidate
                set is the k medoids, not the banked words.)

  update       each cluster's new MEDOID = the member minimising total within-cluster
               DtwTo cost (the point closest to all others = the mode of the cluster):
                 medoid(c) = Argmin_{p in members(c)} ( Σ_{t in members(c)} DtwTo(traj(p), traj(t)) )
               (Argmin over members of a Sum over members of DtwTo — the agent's
                Argmin / Sum / DtwTo / Neighbours, no mean, no arithmetic in Python.)

The within-cluster total-DtwTo cost the medoid step minimises IS the compression /
MDL selector: the clustering that minimises total intra-cluster alignment distance is
the structure that most compresses the token distribution. NO label is ever read by
the clusterer. Labels are used ONLY AFTER, to SCORE the recovered structure (purity,
NMI, cross-speaker held-out recovery, semi-supervised recognition vs the 0.593
supervised DTW baseline).

DONKEY BOUNDARY (audited):
  · TOKENS    = the agent's DTW trajectory feature (agent_frontend.cmvn_track) — the
                SAME source-normalized cochleagram the dominant cmvn_ear cue uses.
  · DISTANCE  = the agent's OWNED DtwTo Term (banded Sakoe-Chiba), evaluated natively.
  · CLUSTERING= the agent's graph-resident k-medoids: assignment = Argmin-DtwTo Term;
                medoid update = Argmin-Sum-DtwTo Term. NO gradient, NO net, NO learned
                weight, NO label-fitting. k-medoids++ seeding is mechanical distance
                arithmetic over the SAME DtwTo (no labels). The numbers come out of
                substrate.evaluate.
  · LABELS    = used ONLY to score (purity / NMI / cross-speaker / semi-sup). Never in
                the clustering.
  · SC load + the 40-speaker split = world-adapter mechanics; HELD-OUT speakers' clips
                are NEVER in the clustered set (the cross-speaker test assigns them to
                the discovered medoids AFTER the structure is fixed — ungameable).

Run: python -m scripts.unsup_clustering_loso [n_train_spk] [n_held_spk] [n_per] [seed]
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
from scripts.sc_loso_frontend_norm import build_split, FS


# --------------------------------------------------------------------------------
# The agent's OWNED graph Term-trees for k-medoids over DtwTo (composed from its DSL).
# Same _Pred / _DtwTo / _Argmin / _MinOver scaffold the DTW recognizer uses.
# --------------------------------------------------------------------------------

TOKEN_TYPE = "ClusterToken"
MEDOID_TYPE = "Medoid"
ROOT_TYPE = "ClusteringRoot"
TRAJ_ATTR = "traj"
MEDOID_EDGE = "has_medoid"      # root -> the current k medoids
MEMBER_EDGE = "has_member"      # medoid -> the tokens currently assigned to it


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nb(node, e): return {"type": "Neighbours", "node": node, "edge_type": e,
                          "any_type": False}
def _DtwTo(a, b): return {"type": "DtwTo", "a": a, "b": b}
def _MinOver(src, var, val): return {"type": "MinOver", "source": src,
                                     "var_name": var, "value": val, "default": None}
def _Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var,
                                 "value": val}
def _Argmin(src, var, val): return {"type": "Argmin", "source": src,
                                    "var_name": var, "value": val, "default": None}


def assignment_term():
    """assign(t) = Argmin_{m in root.has_medoid} DtwTo(traj(t), traj(m)).
    Evaluated with env {"t": token, "root": clustering-root}; returns the nearest
    medoid node. The SAME Argmin-DtwTo shape as the DTW recognizer, candidate set =
    the k medoids instead of the banked word exemplars."""
    medoids = _Nb(_V("root"), MEDOID_EDGE)
    return _Argmin(medoids, "m",
                   _DtwTo(_Attr(_V("t"), TRAJ_ATTR), _Attr(_V("m"), TRAJ_ATTR)))


def medoid_update_term():
    """medoid(m) = Argmin_{p in members(m)} Σ_{t in members(m)} DtwTo(traj(p), traj(t)).
    The member minimising total within-cluster DtwTo cost — the mode of the cluster,
    the MDL-best representative. Evaluated with env {"m": current-medoid}; returns the
    new medoid token. Argmin over members of a Sum over members of DtwTo — all owned
    ops, no mean, no Python arithmetic."""
    members_p = _Nb(_V("m"), MEMBER_EDGE)
    members_t = _Nb(_V("m"), MEMBER_EDGE)
    total_cost = _Sum(members_t, "t",
                      _DtwTo(_Attr(_V("p"), TRAJ_ATTR), _Attr(_V("t"), TRAJ_ATTR)))
    return _Argmin(members_p, "p", total_cost)


def _traj_tuple(track):
    """A trajectory (list of frames) as a tuple-of-tuples the graph stores as an attr
    (frames x channels). Empty -> a single zero frame so DtwTo stays finite."""
    if track is None or len(track) == 0:
        return ((0.0,) * 4,)
    return tuple(tuple(float(v) for v in frame) for frame in track)


# --------------------------------------------------------------------------------
# I/O boundary: lay the token cloud out as a graph, run the agent's k-medoids Terms
# to convergence. NO label read; NO decision in Python — assignment + medoid moves
# are substrate.evaluate of the owned Terms.
# --------------------------------------------------------------------------------

def kmedoids(s, trajs, k, n_iters=30, seed=0):
    """Cluster `trajs` (a list of trajectory-tuples) into k clusters by running the
    agent's composed assignment + medoid-update Terms to convergence. Returns a list
    of cluster labels (one int per token) and the medoid token indices.

    LABEL-FREE: trajs carry no truth. k-medoids++ seeding uses the SAME DtwTo distance
    (mechanical init over the agent's metric, no labels). Empty clusters keep their
    medoid (standard k-medoids)."""
    n = len(trajs)
    k = min(k, n)
    rng = np.random.default_rng(seed)

    root = s.add_node(ROOT_TYPE, {})
    tok_ids = [s.add_node(TOKEN_TYPE, {TRAJ_ATTR: trajs[i]}) for i in range(n)]

    # --- precompute the DtwTo distance for the seeding via the owned Term (no labels).
    # one scratch pair-distance Term so the seeding uses the SAME metric the clustering
    # does (not a separate Python DTW). env binds two token nodes a, b.
    pair_term = _Pred(_DtwTo(_Attr(_V("a"), TRAJ_ATTR), _Attr(_V("b"), TRAJ_ATTR)))

    def dist(i, j):
        if i == j:
            return 0.0
        return float(s.evaluate(pair_term, {"a": tok_ids[i], "b": tok_ids[j]}))

    # k-medoids++ seeding: first medoid random, each next farthest (D^2) from chosen.
    idx0 = int(rng.integers(n))
    seeds = [idx0]
    d2 = np.array([dist(idx0, j) ** 2 for j in range(n)])
    for _ in range(1, k):
        tot = d2.sum()
        probs = d2 / tot if tot > 0 else None
        nxt = int(rng.choice(n, p=probs)) if probs is not None else int(rng.integers(n))
        seeds.append(nxt)
        dn = np.array([dist(nxt, j) ** 2 for j in range(n)])
        d2 = np.minimum(d2, dn)

    # medoid nodes carry the SAME trajectory as their seed token (a copy the Argmin
    # ranges over); we track which token index each medoid currently is.
    med_ids = []
    med_token_idx = []
    for si in seeds:
        m = s.add_node(MEDOID_TYPE, {TRAJ_ATTR: trajs[si]})
        s.add_edge_unchecked(root, MEDOID_EDGE, m)
        med_ids.append(m)
        med_token_idx.append(si)
    mid_index = {m: c for c, m in enumerate(med_ids)}

    assign_term = _Pred(assignment_term())
    update_term = _Pred(medoid_update_term())

    labels = [-1] * n
    for _ in range(n_iters):
        # --- assignment: evaluate the agent's Argmin-DtwTo Term for every token. ---
        new_members = {m: [] for m in med_ids}
        new_labels = []
        for r, t in enumerate(tok_ids):
            chosen = s.evaluate(assign_term, {"t": t, "root": root})
            m = chosen if chosen in mid_index else med_ids[0]
            new_members[m].append(t)
            new_labels.append(mid_index[m])
        # rewire has_member edges so the update Term sees the new assignment.
        for m in med_ids:
            for old in list(s.neighbours(m, MEMBER_EDGE)):
                s.remove_edge(m, MEMBER_EDGE, old)
            for t in new_members[m]:
                s.add_edge_unchecked(m, MEMBER_EDGE, t)
        # --- update: evaluate the agent's Argmin-Sum-DtwTo medoid Term per cluster. ---
        for c, m in enumerate(med_ids):
            if not new_members[m]:
                continue   # empty cluster keeps its medoid (standard k-medoids)
            new_med_tok = s.evaluate(update_term, {"m": m})
            if new_med_tok is not None:
                # set the medoid node's trajectory to the chosen member's trajectory.
                nt = s.node(new_med_tok)["attrs"].get(TRAJ_ATTR)
                if nt is not None:
                    s.set_attr(m, TRAJ_ATTR, nt)
                    med_token_idx[c] = tok_ids.index(new_med_tok)
        if new_labels == labels:
            break
        labels = new_labels

    return labels, med_ids, root, tok_ids, mid_index


def assign_external(s, root, mid_index, traj):
    """Assign ONE external (held-out) token to the FIXED discovered medoids via the
    agent's Argmin-DtwTo Term. Used for the cross-speaker test: the held-out speakers'
    tokens are assigned to the structure discovered WITHOUT them. Returns cluster id."""
    qn = s.add_node(TOKEN_TYPE, {TRAJ_ATTR: _traj_tuple_from(traj)})
    assign_term = _Pred(assignment_term())
    chosen = s.evaluate(assign_term, {"t": qn, "root": root})
    s.remove_node(qn)
    if chosen is None or chosen not in mid_index:
        return 0
    return mid_index[chosen]


def _traj_tuple_from(track):
    return _traj_tuple(track)


# --------------------------------------------------------------------------------
# Scoring (labels used ONLY here — never in the clustering).
# --------------------------------------------------------------------------------

def purity(labels, truth):
    """Σ_clusters max-class-count / N. 1.0 = every cluster pure."""
    hit = 0
    for cl in set(labels):
        members = [truth[i] for i, l in enumerate(labels) if l == cl]
        if members:
            hit += max(Counter(members).values())
    return hit / max(len(truth), 1)


def nmi(labels, truth):
    """Normalised mutual information I(L;T) / sqrt(H(L) H(T))."""
    n = len(truth)
    if n == 0:
        return 0.0
    Lc, Tc = Counter(labels), Counter(truth)
    joint = Counter(zip(labels, truth))

    def H(c):
        return -sum((v / n) * math.log(v / n) for v in c.values() if v > 0)
    HL, HT = H(Lc), H(Tc)
    I = 0.0
    for (l, t), v in joint.items():
        pj = v / n
        I += pj * math.log(pj / ((Lc[l] / n) * (Tc[t] / n)))
    denom = math.sqrt(HL * HT)
    return I / denom if denom > 1e-12 else 0.0


def cluster_to_word(labels, truth):
    """Name each cluster by its MAJORITY truth word (a MAP, not used in clustering).
    Returns {cluster_id: word}."""
    m = {}
    for cl in set(labels):
        members = [truth[i] for i, l in enumerate(labels) if l == cl]
        if members:
            m[cl] = Counter(members).most_common(1)[0][0]
    return m


def random_floor(truth, k, trials=30, seed=0):
    rng = np.random.default_rng(seed)
    return float(np.mean([purity(list(rng.integers(0, k, len(truth))), truth)
                          for _ in range(trials)]))


# --------------------------------------------------------------------------------
# Feature extraction (the agent's DTW trajectory) — pure I/O.
# --------------------------------------------------------------------------------

def _track(x, fs):
    return _traj_tuple(FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs)))


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240608
    n_seeds = int(os.environ.get("N_SEEDS", "5"))

    print("=" * 78, flush=True)
    print("UNSUPERVISED CROSS-SPEAKER CLUSTERING over the agent's DTW trajectories",
          flush=True)
    print("  (k-medoids over DtwTo — the agent's owned distance — NO labels in the "
          "clustering)", flush=True)
    print("=" * 78, flush=True)

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=seed)
    words = W.sc_words()
    k = len(words)
    chance = 1.0 / k

    # --- the clustered set: the TRAIN-speaker clips' DTW trajectories (the unlabelled
    # distribution). Held-out speakers are NOT in here. ---
    print("\n[feat] extracting DTW (CMVN) trajectories for the clustered token cloud "
          "...", flush=True)
    train_trajs = [_track(x, fs) for (w, x, fs) in train_clips]
    train_truth = [w for (w, x, fs) in train_clips]
    print(f"[feat] {len(train_trajs)} train-speaker tokens (k={k} clusters, "
          f"chance {chance:.3f})", flush=True)

    rf = random_floor(train_truth, k)
    print(f"[floor] random-assignment purity floor = {rf:.3f}\n", flush=True)

    # --- run the agent's k-medoids over several seeds (k-medoids is seed-sensitive). ---
    best = None   # keep the run with lowest within-cluster DtwTo cost (the MDL pick)
    results = []
    for sd in range(n_seeds):
        s = Substrate()
        labels, med_ids, root, tok_ids, mid_index = kmedoids(
            s, train_trajs, k=k, seed=sd)
        pur = purity(labels, train_truth)
        nm = nmi(labels, train_truth)
        # within-cluster total DtwTo cost = the agent's MDL selector (label-free).
        cost = 0.0
        pair_term = _Pred(_DtwTo(_Attr(_V("a"), TRAJ_ATTR), _Attr(_V("b"), TRAJ_ATTR)))
        for c, m in enumerate(med_ids):
            for t in s.neighbours(m, MEMBER_EDGE):
                cost += float(s.evaluate(pair_term, {"a": m, "b": t}))
        results.append((pur, nm, cost))
        print(f"[seed {sd}] purity {pur:.3f}  NMI {nm:.3f}  "
              f"within-cluster DtwTo cost {cost:.2f}", flush=True)
        if best is None or cost < best[0]:
            best = (cost, s, labels, med_ids, root, mid_index, pur, nm)

    purs = [r[0] for r in results]
    nms = [r[1] for r in results]
    print(f"\n[clustering] purity {np.mean(purs):.3f} +/- {np.std(purs):.3f}   "
          f"NMI {np.mean(nms):.3f} +/- {np.std(nms):.3f}   over {n_seeds} seeds",
          flush=True)
    print(f"[clustering] random floor {rf:.3f}   chance {chance:.3f}", flush=True)

    # --- adopt the MDL-best run (lowest within-cluster DtwTo cost — label-free pick). ---
    _cost, s, labels, med_ids, root, mid_index, b_pur, b_nm = best
    print(f"\n[MDL pick] lowest-cost run: within-cluster cost {_cost:.2f}  "
          f"purity {b_pur:.3f}  NMI {b_nm:.3f}  (selected by compression, NO labels)",
          flush=True)

    # --- (b) CROSS-SPEAKER TEST: assign HELD-OUT speakers' tokens to the FIXED medoids
    # discovered WITHOUT them. Does speaker-invariant identity emerge from structure? ---
    c2w = cluster_to_word(labels, train_truth)   # name clusters by majority (a MAP)
    print(f"\n[xspk] cluster->majority-word map (labels used only to NAME, not to "
          f"cluster): {dict(sorted(c2w.items()))}", flush=True)
    held_correct = held_tot = 0
    # also measure cross-speaker cluster purity directly: do held tokens of the same
    # word land in the same cluster as each other?
    held_labels, held_truth = [], []
    for (w, x, fs) in loso_probe:
        traj = FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs))
        cl = assign_external(s, root, mid_index, traj)
        held_labels.append(cl)
        held_truth.append(w)
        if c2w.get(cl) == w:
            held_correct += 1
        held_tot += 1
    xspk_recog = held_correct / max(held_tot, 1)   # semi-supervised cross-speaker recog
    xspk_purity = purity(held_labels, held_truth)
    xspk_nmi = nmi(held_labels, held_truth)
    print(f"[xspk] HELD-OUT speakers ({held_tot} tokens, NEVER clustered):", flush=True)
    print(f"       cross-speaker cluster purity {xspk_purity:.3f}   "
          f"NMI {xspk_nmi:.3f}", flush=True)
    print(f"       semi-supervised recognition (cluster->majority-word) "
          f"{xspk_recog:.3f}   vs chance {chance:.3f}", flush=True)

    # --- (c) seen-speaker semi-supervised recognition for the same naming map. ---
    seen_correct = seen_tot = 0
    for (w, x, fs) in seen_probe:
        traj = FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs))
        cl = assign_external(s, root, mid_index, traj)
        if c2w.get(cl) == w:
            seen_correct += 1
        seen_tot += 1
    seen_recog = seen_correct / max(seen_tot, 1)
    print(f"[seen] seen-speaker semi-supervised recognition {seen_recog:.3f}", flush=True)

    # --- VERDICT ---
    print("\n" + "=" * 78, flush=True)
    print("VERDICT — does speaker-invariant word identity EMERGE from the unlabelled "
          "distribution?", flush=True)
    print("=" * 78, flush=True)
    print(f"  clustered-set purity      {np.mean(purs):.3f} +/- {np.std(purs):.3f}   "
          f"(random floor {rf:.3f})", flush=True)
    print(f"  clustered-set NMI         {np.mean(nms):.3f} +/- {np.std(nms):.3f}",
          flush=True)
    print(f"  HELD-OUT cross-speaker purity {xspk_purity:.3f}   NMI {xspk_nmi:.3f}",
          flush=True)
    print(f"  semi-supervised recog: seen {seen_recog:.3f}  cross-speaker "
          f"{xspk_recog:.3f}  vs supervised-DTW 0.593  (chance {chance:.3f})",
          flush=True)
    print("-" * 78, flush=True)
    if np.mean(purs) > rf + 0.05:
        print(f"  => STRUCTURE RECOVERED: the unsupervised k-medoids over the agent's "
              f"DtwTo distance recovers word structure across speakers WITHOUT labels "
              f"(purity {np.mean(purs):.3f} > floor {rf:.3f}).", flush=True)
    else:
        print(f"  => NO clear structure: clustering purity {np.mean(purs):.3f} not "
              f"above the random floor {rf:.3f}.", flush=True)
    if xspk_purity > rf + 0.05:
        print(f"  => CROSS-SPEAKER EMERGENCE: held-out speakers' tokens land in the "
              f"right cluster (purity {xspk_purity:.3f}) — speaker-invariant identity "
              f"emerges from structure alone.", flush=True)
    else:
        print(f"  => held-out cross-speaker structure weak ({xspk_purity:.3f}).",
              flush=True)
    gap = 0.593 - xspk_recog
    print(f"  => SEMI-SUP vs SUPERVISED: cross-speaker semi-supervised recog "
          f"{xspk_recog:.3f} vs supervised-DTW 0.593 (residual {gap:+.3f}); a FEW "
          f"labels (the cluster->word map) name the discovered clusters.", flush=True)
    print("[MARKER] UNSUP_CLUSTERING_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
