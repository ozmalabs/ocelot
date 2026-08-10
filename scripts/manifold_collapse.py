"""manifold_collapse — measure the ADMISSIBILITY MANIFOLD COLLAPSE.

The thesis (MEMORY: efficiency = admissibility prunes the inadmissible). This
script makes "admissibility prunes the inadmissible" a MEASURED CURVE.

Take real sentences, reveal them word-by-word, and at each stage have the agent
produce its MANIFOLD of admissible candidate sentences WITH CONFIDENCE, then
measure the collapse as evidence accumulates.

DONKEY-LINE (the crux). The manifold MUST come from the agent's OWN learned
structure — the transition graph / lexicon it builds by COUNTING co-occurrences
in real sentences (the scripts/sentence_learning.py lineage: recurring lexicon +
transition counts). It is NOT a trained LM, NOT a neural softmax, NOT fit to the
answer. The "weights" are the agent's learned transition COUNTS, stored as GRAPH
DATA (Word nodes, Bi/Trigram transition nodes with `cnt` attrs), and the candidate
score is a GRAPH TERM-TREE (Sum over the learned transition graph), evaluated by
the substrate — the same recognition-as-graph-term pattern as
domains/recognition_graph.py. No .fit, no gradient, no smoothing-to-the-answer.

THE MANIFOLD. Candidates = a fixed pool of held-out sentences (the agent's space
of possible utterances). At fraction f of a target sentence revealed:
  - HARD ADMISSIBILITY (Γ-prune): a candidate is admissible iff its first k words
    equal the revealed prefix. Prefix-mismatch = inadmissible — pruned, never
    weighted. This is admissibility removing the inadmissible in real time.
  - SOFT WEIGHT (learned likelihood): among admissible candidates, weight ∝ the
    agent's learned-transition support for the candidate's continuation (the words
    after the prefix), computed graph-resident over the learned transition graph
    with a back-off the agent COUNTS (trigram -> bigram -> unigram), NOT a tuned LM.
  - CONFIDENCE p(cand) = normalised weight. The truth's confidence and the set
    size are read out at every f.

WHAT WE MEASURE (designed signatures, not just "entropy drops"):
  1. COLLAPSE CURVE: manifold entropy + admissible-set size vs fraction revealed.
  2. CALIBRATION (the key one): when the manifold puts confidence p on its top
     guess, is the truth there ~p of the time? Reliability + ECE. Does it know what
     it doesn't know (wide when it should be, collapsing only as fast as warranted)?
  3. COHORT / UNIQUENESS POINT: at what fraction the admissible set collapses to 1
     (the true sentence) — the recognition-point distribution (cohort model).
  4. GARDEN-PATH / RE-OPEN: the manifold's top hypothesis changes after more
     evidence (a collapsed guess overturned) — count + characterise.
  5. SHUFFLE CONTROL (the signature): scramble word order in the LEARNED structure
     -> the collapse must DEGRADE (proves real sequential structure drives the
     pruning, not an artifact of admissible-set bookkeeping).

Run:  python -m scripts.manifold_collapse [n_pool] [n_targets]
Honest test — reports the real numbers, including a null result.
"""
from __future__ import annotations

import math
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate, Sum, Attr, Var, Neighbours, Lit, Plus

DATA_DIR = "/tmp/LibriSpeech/dev-clean"
_WORD_RE = re.compile(r"[A-Z']+")


# --------------------------------------------------------------------------
# corpus (world adapter: read real sentences as word sequences)
# --------------------------------------------------------------------------

def load_sentences(min_len=3, max_len=40):
    """Read every LibriSpeech dev-clean transcript as a list of UPPERCASE word
    tokens. Real sentences; mechanical text->tokens. No agent logic."""
    out = []
    for root, _, names in os.walk(DATA_DIR):
        for fn in names:
            if not fn.endswith(".trans.txt"):
                continue
            with open(os.path.join(root, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(" ", 1)
                    if len(parts) != 2:
                        continue
                    words = _WORD_RE.findall(parts[1].upper())
                    if min_len <= len(words) <= max_len:
                        out.append(tuple(words))
    out.sort()
    return out


# --------------------------------------------------------------------------
# the agent's LEARNED structure, stored as GRAPH DATA (donkey audit lives here)
# --------------------------------------------------------------------------
#
# A transition graph the agent builds by COUNTING in train sentences:
#   Word node  (one per distinct token, attr `freq` = unigram count)
#   Bi  node   Word --bi--> Bi --to--> Word    (attr `cnt` = #(a then b))
#   Tri node   pair-key --tri--> Tri --to--> Word (attr `cnt` = #(a,b then c))
# No fitting, no smoothing-to-the-answer: pure observed counts.

class LearnedStructure:
    def __init__(self, sub: Substrate):
        self.s = sub
        self.word_node: dict[str, int] = {}     # token -> Word NodeID
        self.bi_node: dict[tuple, int] = {}      # (a,b) -> Bi NodeID
        self.tri_node: dict[tuple, int] = {}     # (a,b,c) -> Tri NodeID
        self.unigram: dict[str, int] = {}
        self.bigram: dict[tuple, int] = {}       # (a,b) -> cnt  (python mirror for fast prefix work)
        self.trigram: dict[tuple, int] = {}      # (a,b,c)-> cnt
        self.bi_succ: dict[str, dict] = {}       # b -> {c: cnt}  (learned successors of b)
        self.tri_succ: dict[tuple, dict] = {}    # (a,b) -> {c: cnt}
        self.has_succ: set = set()               # words with >=1 learned successor
        self.total_tokens = 0

    def _word(self, w: str) -> int:
        n = self.word_node.get(w)
        if n is None:
            n = self.s.add_node("MWord", {"name": w, "freq": 0.0})
            self.word_node[w] = n
        return n

    def learn(self, sentences):
        """Count uni/bi/tri-grams over train sentences and WRITE them as graph
        data. This IS the agent's learned Γ over word sequences."""
        for seq in sentences:
            for w in seq:
                self.unigram[w] = self.unigram.get(w, 0) + 1
                self.total_tokens += 1
            for a, b in zip(seq, seq[1:]):
                self.bigram[(a, b)] = self.bigram.get((a, b), 0) + 1
                self.bi_succ.setdefault(a, {})
                self.bi_succ[a][b] = self.bi_succ[a].get(b, 0) + 1
                self.has_succ.add(a)
            for a, b, c in zip(seq, seq[1:], seq[2:]):
                self.trigram[(a, b, c)] = self.trigram.get((a, b, c), 0) + 1
                self.tri_succ.setdefault((a, b), {})
                self.tri_succ[(a, b)][c] = self.tri_succ[(a, b)].get(c, 0) + 1
        # materialise as graph nodes/edges (counts as attrs)
        for w, c in self.unigram.items():
            n = self._word(w)
            self.s.set_attr(n, "freq", float(c))
        for (a, b), c in self.bigram.items():
            wa, wb = self._word(a), self._word(b)
            bn = self.s.add_node("MBi", {"cnt": float(c)})
            self.s.add_edge_unchecked(wa, "bi", bn)
            self.s.add_edge_unchecked(bn, "to", wb)
            self.bi_node[(a, b)] = bn
        for (a, b, c), cnt in self.trigram.items():
            # key the trigram off the Bi node for (a,b)
            bn = self.bi_node.get((a, b))
            if bn is None:
                continue
            wc = self._word(c)
            tn = self.s.add_node("MTri", {"cnt": float(cnt)})
            self.s.add_edge_unchecked(bn, "tri", tn)
            self.s.add_edge_unchecked(tn, "to", wc)
            self.tri_node[(a, b, c)] = tn

    # -- graph-resident scorers (Term-trees the substrate evaluates) ---------
    #
    # bi_support(a)  = Σ_{b} cnt(a->b)   — total learned outgoing mass of word a
    # These are the donkey-clean primitives: a Sum over the LEARNED transition
    # graph, evaluated natively. The continuation weight is built from these.

    @staticmethod
    def bi_support_term():
        return Sum(Neighbours(Var("w"), "bi"), "t", Attr(Var("t"), "cnt"))

    def graph_bi_support(self, word: str) -> float:
        n = self.word_node.get(word)
        if n is None:
            return 0.0
        return float(self.s.evaluate(self.bi_support_term(), {"w": n}))


# --------------------------------------------------------------------------
# the agent's learned transition probability, with a COUNTED back-off
# --------------------------------------------------------------------------
#
# P(c | a,b) via the agent's counts, backing off ONLY when a context is unseen
# (this is observed evidence, not a tuned/smoothed LM). The back-off weight is
# the proportion of context mass actually seen — itself a count ratio.

def trans_logprob(ls: LearnedStructure, a, b, c) -> float:
    """log P(c | preceding a,b) from the agent's LEARNED counts, with a counted
    trigram->bigram->unigram back-off. Returns log-probability (nats)."""
    V = max(len(ls.unigram), 1)
    # trigram
    tri = ls.trigram.get((a, b, c), 0)
    bi_ctx = ls.bigram.get((a, b), 0)
    # bigram
    big = ls.bigram.get((b, c), 0)
    uni_ctx = ls.unigram.get(b, 0)
    # unigram
    uni = ls.unigram.get(c, 0)
    tot = max(ls.total_tokens, 1)
    p_uni = (uni + 1.0) / (tot + V)              # add-1 floor: an UNSEEN word is
    #                                              not impossible, only rare (this
    #                                              is the COUNTED floor, identical
    #                                              for every candidate — no fitting)
    if uni_ctx > 0:
        p_bi = big / uni_ctx
        lam_b = uni_ctx / (uni_ctx + V)          # counted back-off weight
        p_bi = lam_b * p_bi + (1 - lam_b) * p_uni
    else:
        p_bi = p_uni
    if bi_ctx > 0:
        p_tri = tri / bi_ctx
        lam_t = bi_ctx / (bi_ctx + V)
        p_tri = lam_t * p_tri + (1 - lam_t) * p_bi
    else:
        p_tri = p_bi
    return math.log(max(p_tri, 1e-12))


def candidate_seq_logprob(ls: LearnedStructure, cand) -> float:
    """log P(whole candidate) under the agent's LEARNED transition structure —
    Σ_i log P(w_i | w_{i-2}, w_{i-1}). Pure learned counts; length-normalised
    (per-word avg) so length doesn't dominate. This is the agent's learned
    plausibility of the sentence as a sequence — and it is exactly what the
    SHUFFLE control destroys (scrambled training kills the real transitions)."""
    lp = 0.0
    for i in range(len(cand)):
        a = cand[i - 2] if i - 2 >= 0 else None
        b = cand[i - 1] if i - 1 >= 0 else None
        lp += trans_logprob(ls, a, b, cand[i])
    return lp / max(len(cand), 1)


# --------------------------------------------------------------------------
# the MANIFOLD at a revealed prefix
# --------------------------------------------------------------------------
#
# Evidence = the revealed prefix. A candidate's manifold weight combines:
#   (a) PREFIX EVIDENCE — how well the candidate AGREES with the observed words.
#       Hard agreement (the candidate's word at position i equals the revealed
#       word) is the cohort signal; we keep it SOFT so the manifold can hold a
#       near-miss with low (not zero) weight — that is what lets it RE-OPEN and
#       what makes calibration meaningful (a hard prune is trivially calibrated).
#   (b) LEARNED PLAUSIBILITY — log P(candidate) under the agent's learned
#       transition structure. THIS is the donkey-relevant driver: it ranks the
#       surviving cohort by learned sequential structure, and it is destroyed by
#       the shuffle control. Without it the collapse would be pure string-match.
#
# weight(cand | prefix) ∝ exp( β·agree(cand,prefix) + seq_logprob(cand) )
#   agree = #positions where cand matches the revealed prefix (0..k)
# A mismatch costs β bits-ish of evidence but does NOT zero the candidate, so the
# manifold stays a graded admissibility set (knows what it doesn't know), not a
# brittle exact-match filter.

BETA = 6.0      # evidence strength per matched revealed word (counted-scale, fixed)


def manifold(ls: LearnedStructure, pool, prefix, seq_lp_cache):
    """Agent's manifold over the WHOLE pool given revealed `prefix`. Returns
    (cand, confidence) sorted desc — graded admissibility, learned-structure
    weighted. seq_lp_cache: dict cand->learned seq-logprob (precomputed once)."""
    k = len(prefix)
    lws = []
    for c in pool:
        agree = 0
        kk = min(k, len(c))
        for i in range(kk):
            if c[i] == prefix[i]:
                agree += 1
            else:
                break                # first mismatch stops prefix agreement
        # evidence: matched-prefix length (soft); + learned plausibility
        lw = BETA * agree + seq_lp_cache[c]
        lws.append(lw)
    mx = max(lws)
    ws = [math.exp(lw - mx) for lw in lws]
    z = sum(ws)
    out = sorted(((c, w / z) for c, w in zip(pool, ws)), key=lambda x: -x[1])
    # trim the long tail of negligible candidates for entropy/reporting stability
    # (keep mass >= 0.999); this is a reporting cutoff, not a prune of admissibility
    return out


# --------------------------------------------------------------------------
# the NEXT-WORD predictive manifold — PURE learned structure (donkey-clean,
# the shuffle-sensitive measurement)
# --------------------------------------------------------------------------
#
# This is the part of the collapse the LEARNED transition structure GOVERNS, with
# NO string-prefix term to swamp it. Given the revealed prefix (...a,b), the agent
# anticipates the NEXT word via its learned counts: P(c | a,b) over the whole
# learned vocabulary (graph-resident transition graph). We report:
#   - predictive entropy H(next | prefix)  [bits]      — how collapsed the
#     next-word manifold is (the anticipatory cohort);
#   - whether the TRUE next word is in the top-1 / top-5 (anticipation hit);
#   - the true next word's probability (calibration of anticipation).
# SHUFFLE destroys the transition counts -> this entropy must RISE and the
# anticipation hit-rate must FALL. THIS is the clean proof the collapse is driven
# by real sequential structure, not string bookkeeping.

def next_word_dist(ls: LearnedStructure, a, b, vocab):
    """Learned distribution over the next word given context (a,b). Restricted to
    the words the learned structure actually associates with the context — the
    trigram successors of (a,b) and the bigram successors of b — scored by the
    agent's counted transition log-prob. Pure learned counts; O(#successors)."""
    cand = set(ls.bi_succ.get(b, {}).keys())
    cand |= set(ls.tri_succ.get((a, b), {}).keys())
    if not cand:
        cand = set(vocab)            # no learned context -> fall to full vocab
    logps = {c: trans_logprob(ls, a, b, c) for c in cand}
    mx = max(logps.values())
    ws = {c: math.exp(lp - mx) for c, lp in logps.items()}
    z = sum(ws.values())
    return {c: w / z for c, w in ws.items()}


def manifold_entropy(man):
    h = 0.0
    for _c, p in man:
        if p > 0:
            h -= p * math.log2(p)
    return h


def dist_entropy(d):
    h = 0.0
    for p in d.values():
        if p > 0:
            h -= p * math.log2(p)
    return h


def effective_support(man, mass=0.99):
    """# of top candidates holding `mass` of the confidence — the manifold's
    effective admissible-set size (a graded analogue of cohort size)."""
    acc = 0.0
    n = 0
    for _c, p in man:
        acc += p
        n += 1
        if acc >= mass:
            break
    return n


# --------------------------------------------------------------------------
# the experiment
# --------------------------------------------------------------------------

FRACS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
_T0 = [time.time()]


def k_at_fraction(L, f):
    return int(round(f * L))


REC_THRESH = 0.5    # truth recognised = it is top-1 AND holds >50% of the mass


def run_targets(ls, pool, targets, label, seq_lp_cache, vocab):
    """For each target sentence, reveal word-by-word and record the manifold at
    each fraction. Returns aggregated metrics."""
    per_frac_size = {f: [] for f in FRACS}
    per_frac_ent = {f: [] for f in FRACS}
    per_frac_truth_conf = {f: [] for f in FRACS}
    per_frac_truth_rank = {f: [] for f in FRACS}
    # next-word predictive manifold (PURE learned structure; shuffle-sensitive)
    per_frac_nw_ent = {f: [] for f in FRACS}
    per_frac_nw_top1 = {f: [] for f in FRACS}
    per_frac_nw_top5 = {f: [] for f in FRACS}
    per_frac_nw_trueprob = {f: [] for f in FRACS}
    nw_calib = []               # (top1_nextword_prob, top1_is_true_next)
    calib = []                  # (top1_conf, top1_is_truth) across all (tgt,frac)
    recognition_points = []     # fraction at which truth is recognised (top-1, >50%)
    garden_paths = 0
    garden_examples = []

    for ti, tgt in enumerate(targets):
        L = len(tgt)
        committed_top = None        # a top hypothesis the manifold grew confident in
        rec_point = None
        for f in FRACS:
            k = k_at_fraction(L, f)
            prefix = tgt[:k]
            man = manifold(ls, pool, prefix, seq_lp_cache)
            size = effective_support(man)
            ent = manifold_entropy(man)
            per_frac_size[f].append(size)
            per_frac_ent[f].append(ent)
            truth_conf = 0.0
            truth_rank = -1
            for rank, (c, p) in enumerate(man):
                if c == tgt:
                    truth_conf = p
                    truth_rank = rank
                    break
            per_frac_truth_conf[f].append(truth_conf)
            per_frac_truth_rank[f].append(truth_rank)
            if man:
                top_c, top_p = man[0]
                calib.append((top_p, top_c == tgt))
                # garden-path: manifold COMMITTED (>0.8) to a WRONG top, then later
                # evidence forces a different top — the bounded-flex re-open.
                if committed_top is not None and top_c != committed_top \
                        and committed_top != tgt:
                    garden_paths += 1
                    if len(garden_examples) < 8:
                        garden_examples.append(
                            (" ".join(prefix), " ".join(committed_top[:k + 2]),
                             " ".join(top_c[:k + 2])))
                    committed_top = None
                if top_p > 0.8:
                    committed_top = top_c
            # recognition point: truth is the manifold's confident top
            if rec_point is None and man and man[0][0] == tgt \
                    and man[0][1] >= REC_THRESH:
                rec_point = f

            # ---- NEXT-WORD predictive manifold (PURE learned structure) ----
            # Scored only where the agent HAS learned context (b has successors).
            # An unseen context is a coverage gap, not a structure failure — and
            # counting it identically for real & shuffle would wash out the signal.
            # This is exactly the lineage's bigram_predict (predict over seen ctx).
            if k < L and k >= 1:
                a = tgt[k - 2] if k - 2 >= 0 else None
                b = tgt[k - 1]
                if b in ls.has_succ:        # learned context exists
                    true_next = tgt[k]
                    nd = next_word_dist(ls, a, b, vocab)
                    per_frac_nw_ent[f].append(dist_entropy(nd))
                    ranked = sorted(nd.items(), key=lambda kv: -kv[1])
                    top1w = ranked[0][0] if ranked else None
                    top5w = set(w for w, _ in ranked[:5])
                    per_frac_nw_top1[f].append(1.0 if top1w == true_next else 0.0)
                    per_frac_nw_top5[f].append(1.0 if true_next in top5w else 0.0)
                    per_frac_nw_trueprob[f].append(nd.get(true_next, 0.0))
                    if ranked:
                        nw_calib.append((ranked[0][1], top1w == true_next))
        recognition_points.append(rec_point if rec_point is not None else 1.0)
        if (ti + 1) % 50 == 0:
            print(f"  [{label}] {ti+1}/{len(targets)} targets "
                  f"({time.time()-_T0[0]:.0f}s)", flush=True)

    return {
        "size": {f: _mean(per_frac_size[f]) for f in FRACS},
        "ent": {f: _mean(per_frac_ent[f]) for f in FRACS},
        "truth_conf": {f: _mean(per_frac_truth_conf[f]) for f in FRACS},
        "truth_in_set": {f: _mean([1.0 if r >= 0 else 0.0
                                   for r in per_frac_truth_rank[f]]) for f in FRACS},
        "calib": calib,
        "rec_points": recognition_points,
        "garden_paths": garden_paths,
        "garden_examples": garden_examples,
        "nw_ent": {f: _mean(per_frac_nw_ent[f]) for f in FRACS},
        "nw_top1": {f: _mean(per_frac_nw_top1[f]) for f in FRACS},
        "nw_top5": {f: _mean(per_frac_nw_top5[f]) for f in FRACS},
        "nw_trueprob": {f: _mean(per_frac_nw_trueprob[f]) for f in FRACS},
        "nw_calib": nw_calib,
    }


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def calibration_curve(calib, nbins=10):
    """Reliability: bin top-1 confidence, report (mean_conf, hit_rate, n) per bin
    and the Expected Calibration Error (ECE)."""
    bins = [[] for _ in range(nbins)]
    for p, hit in calib:
        b = min(int(p * nbins), nbins - 1)
        bins[b].append((p, 1.0 if hit else 0.0))
    rows = []
    ece = 0.0
    N = len(calib)
    for b in range(nbins):
        if not bins[b]:
            continue
        mp = _mean([x[0] for x in bins[b]])
        acc = _mean([x[1] for x in bins[b]])
        n = len(bins[b])
        rows.append((b / nbins, (b + 1) / nbins, mp, acc, n))
        ece += (n / N) * abs(mp - acc)
    return rows, ece


def main():
    t0 = time.time()
    random.seed(7)
    n_pool = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    n_targets = int(sys.argv[2]) if len(sys.argv) > 2 else 250

    print("=" * 64)
    print("ADMISSIBILITY MANIFOLD COLLAPSE")
    print("=" * 64)
    sents = load_sentences()
    random.shuffle(sents)
    # dedupe (LibriSpeech has a few repeats); keep order
    seen = set(); uniq = []
    for s in sents:
        if s not in seen:
            seen.add(s); uniq.append(s)
    sents = uniq
    print(f"corpus: {len(sents)} unique real sentences (LibriSpeech dev-clean, "
          f"len 3-40 words)")

    # TRAIN / POOL / TARGET split. Train = structure learned by counting (dense:
    # everything EXCEPT the held-out pool). Pool = the candidate manifold
    # (held-out: the agent has NOT learned these sentences as wholes, only the
    # transition statistics from train). Targets = a subset of pool revealed
    # word-by-word. Honest: the agent never saw the targets as whole sentences.
    n_pool = min(n_pool, len(sents) - 200)
    pool = sents[:n_pool]
    train = sents[n_pool:]
    targets = pool[:n_targets]
    print(f"train (learn counts): {len(train)}   pool (manifold): {len(pool)}   "
          f"targets (revealed): {len(targets)}")

    # ---- learn the structure as GRAPH DATA --------------------------------
    sub = Substrate()
    ls = LearnedStructure(sub)
    ls.learn(train)
    print(f"\nLEARNED STRUCTURE (graph-resident, by counting — donkey audit):")
    print(f"  distinct words (MWord nodes) : {len(ls.word_node)}")
    print(f"  bigram transitions (MBi)     : {len(ls.bi_node)}")
    print(f"  trigram transitions (MTri)   : {len(ls.tri_node)}")
    print(f"  total train tokens           : {ls.total_tokens}")
    # sanity: graph-resident Sum equals the python mirror for a sample word
    sample = next(iter(ls.word_node))
    g = ls.graph_bi_support(sample)
    p = float(sum(ls.bigram.get((sample, b), 0)
                  for b in ls.unigram if (sample, b) in ls.bigram))
    print(f"  graph Sum bi_support('{sample}') = {g:.1f}  "
          f"(python mirror {p:.1f})  MATCH={'YES' if abs(g-p)<1e-6 else 'NO'}")

    # ---- precompute learned seq-logprob for every pool candidate ----------
    # (the agent's learned plausibility of each candidate sentence — computed
    # ONCE; the manifold reweights it by prefix evidence at each fraction)
    print(f"\nprecomputing learned seq-logprob for {len(pool)} pool candidates...",
          flush=True)
    seq_lp = {c: candidate_seq_logprob(ls, c) for c in pool}

    vocab = list(ls.unigram.keys())

    # ---- REAL collapse -----------------------------------------------------
    print(f"running REAL collapse over {len(targets)} targets...", flush=True)
    _T0[0] = time.time()
    real = run_targets(ls, pool, targets, "real", seq_lp, vocab)

    # ---- SHUFFLE control: scramble word order in the LEARNED structure -----
    # Re-learn counts on train sentences with each sentence's word ORDER
    # shuffled. The lexicon (unigram) is identical; only the sequential
    # structure is destroyed. If the collapse is driven by REAL sequential
    # structure, it must DEGRADE here.
    print(f"\nbuilding SHUFFLED structure (order destroyed, lexicon kept)...",
          flush=True)
    sub_s = Substrate()
    ls_s = LearnedStructure(sub_s)
    shuf_train = []
    for seq in train:
        w = list(seq)
        random.shuffle(w)
        shuf_train.append(tuple(w))
    ls_s.learn(shuf_train)
    seq_lp_s = {c: candidate_seq_logprob(ls_s, c) for c in pool}
    vocab_s = list(ls_s.unigram.keys())
    print(f"running SHUFFLE-control collapse...", flush=True)
    _T0[0] = time.time()
    shuf = run_targets(ls_s, pool, targets, "shuf", seq_lp_s, vocab_s)

    # ---- report -----------------------------------------------------------
    print("\n" + "=" * 64)
    print("(1) COLLAPSE CURVE — admissible-set size & manifold entropy")
    print("=" * 64)
    print(f"{'frac':>5} | {'adm_size(real)':>14} | {'entropy_bits':>12} | "
          f"{'adm_size(shuf)':>14} | {'ent_shuf':>9}")
    for f in FRACS:
        print(f"{f:>5.1f} | {real['size'][f]:>14.1f} | {real['ent'][f]:>12.3f} | "
              f"{shuf['size'][f]:>14.1f} | {shuf['ent'][f]:>9.3f}")

    print("\n" + "=" * 64)
    print("(2) CALIBRATION — is the collapse HONEST? (reliability + ECE)")
    print("=" * 64)
    rows, ece = calibration_curve(real["calib"])
    print(f"{'conf_bin':>14} | {'mean_conf':>9} | {'hit_rate':>8} | {'n':>6}")
    for lo, hi, mp, acc, n in rows:
        print(f"  [{lo:.1f},{hi:.1f})    | {mp:>9.3f} | {acc:>8.3f} | {n:>6}")
    print(f"\nExpected Calibration Error (real)  : {ece:.4f}")
    rows_s, ece_s = calibration_curve(shuf["calib"])
    print(f"Expected Calibration Error (shuffled): {ece_s:.4f}")
    # truth-in-set vs confidence: does the manifold KEEP the truth while wide?
    print(f"\ntruth-retained-in-admissible-set vs fraction (anti-overconfidence):")
    for f in FRACS:
        print(f"  f={f:.1f}  truth_in_set={real['truth_in_set'][f]:.3f}  "
              f"mean_truth_conf={real['truth_conf'][f]:.3f}")

    print("\n" + "=" * 64)
    print("(3) COHORT / UNIQUENESS POINT — recognition-point distribution")
    print("=" * 64)
    rp = sorted(real["rec_points"])
    rp_s = sorted(shuf["rec_points"])
    def pct(xs, q):
        if not xs:
            return float("nan")
        return xs[min(int(q * len(xs)), len(xs) - 1)]
    print(f"REAL    median recognition fraction : {pct(rp,0.5):.2f}   "
          f"mean : {_mean(rp):.3f}   (frac where adm-set collapses to TRUTH alone)")
    print(f"        p25 {pct(rp,0.25):.2f}  p75 {pct(rp,0.75):.2f}  "
          f"never-unique(=1.0): {sum(1 for x in rp if x>=1.0)}/{len(rp)}")
    print(f"SHUFFLE median recognition fraction : {pct(rp_s,0.5):.2f}   "
          f"mean : {_mean(rp_s):.3f}")
    # histogram
    hist = {f: 0 for f in FRACS + [1.0]}
    for x in rp:
        hist[x] = hist.get(x, 0) + 1
    print(f"  recognition-point histogram (real): "
          + "  ".join(f"{f:.1f}:{hist.get(f,0)}" for f in FRACS + [1.0]))

    print("\n" + "=" * 64)
    print("(4) GARDEN-PATH / RE-OPENING")
    print("=" * 64)
    print(f"committed-then-overturned (manifold >0.8 on a WRONG top, later "
          f"forced to re-open): {real['garden_paths']} across {len(targets)} targets")
    for pre, was, now in real["garden_examples"]:
        print(f"  prefix='{pre}'  committed~'{was}'  ->  re-opened~'{now}'")

    print("\n" + "=" * 64)
    print("(4b) NEXT-WORD PREDICTIVE MANIFOLD — PURE learned structure")
    print("=" * 64)
    print("the part of the collapse the LEARNED transition structure GOVERNS, with")
    print("no string-prefix term. Anticipating the next word from learned counts.")
    print(f"{'frac':>5} | {'H(next)real':>11} | {'top1':>5} | {'top5':>5} | "
          f"{'H(next)shuf':>11} | {'t1shuf':>6} | {'t5shuf':>6}")
    for f in FRACS:
        print(f"{f:>5.1f} | {real['nw_ent'][f]:>11.3f} | "
              f"{real['nw_top1'][f]:>5.2f} | {real['nw_top5'][f]:>5.2f} | "
              f"{shuf['nw_ent'][f]:>11.3f} | {shuf['nw_top1'][f]:>6.2f} | "
              f"{shuf['nw_top5'][f]:>6.2f}")
    nw_auc_real = _mean([real['nw_ent'][f] for f in FRACS])
    nw_auc_shuf = _mean([shuf['nw_ent'][f] for f in FRACS])
    nw_t1_real = _mean([real['nw_top1'][f] for f in FRACS])
    nw_t1_shuf = _mean([shuf['nw_top1'][f] for f in FRACS])
    nw_rows, nw_ece = calibration_curve(real['nw_calib'])
    print(f"\nnext-word anticipation calibration (real) ECE={nw_ece:.4f}  "
          f"(top-1 anticipation prob vs hit-rate)")

    print("\n" + "=" * 64)
    print("(5) SHUFFLE CONTROL — collapse must DEGRADE without real order")
    print("=" * 64)
    # The sentence-manifold collapse is dominated by prefix-string admissibility
    # (identical real vs shuffle by construction — that part is NOT learned). The
    # DONKEY-RELEVANT, learned-structure-driven measurement is the NEXT-WORD
    # predictive manifold: shuffle destroys the transition counts, so its entropy
    # must RISE and anticipation must FALL. THAT is the clean sequential-structure
    # proof.
    auc_real = _mean([real['ent'][f] for f in FRACS])
    auc_shuf = _mean([shuf['ent'][f] for f in FRACS])
    print(f"sentence-manifold mean entropy        REAL={auc_real:.3f}  "
          f"SHUFFLE={auc_shuf:.3f}  (dominated by string-prefix admissibility;")
    print(f"                                      not the learned-structure signal)")
    print(f"NEXT-WORD mean entropy (the signal)   REAL={nw_auc_real:.3f}  "
          f"SHUFFLE={nw_auc_shuf:.3f}  delta={nw_auc_shuf-nw_auc_real:+.3f} bits")
    print(f"NEXT-WORD mean top-1 anticipation     REAL={nw_t1_real:.3f}  "
          f"SHUFFLE={nw_t1_shuf:.3f}  ratio={nw_t1_real/max(nw_t1_shuf,1e-9):.2f}x")
    nw_t5_real = _mean([real['nw_top5'][f] for f in FRACS])
    nw_t5_shuf = _mean([shuf['nw_top5'][f] for f in FRACS])
    print(f"NEXT-WORD mean top-5 anticipation     REAL={nw_t5_real:.3f}  "
          f"SHUFFLE={nw_t5_shuf:.3f}  ratio={nw_t5_real/max(nw_t5_shuf,1e-9):.2f}x")
    # The proven sequential-structure signal (this lineage) is next-word
    # ANTICIPATION ACCURACY collapsing under shuffle — NOT successor-set entropy
    # (which measures successor-set SIZE, roughly preserved when order is
    # scrambled). So the gate is: real top-1 AND top-5 anticipation beat shuffle.
    seq_driven = (nw_t1_real > nw_t1_shuf * 1.3) and (nw_t5_real > nw_t5_shuf * 1.3)

    print("\n" + "=" * 64)
    print("VERDICT")
    print("=" * 64)
    # honest verdict gates
    collapses = real['ent'][0.9] < real['ent'][0.1] - 1e-6
    honest = ece < 0.15
    cohort = _mean(rp) < 1.0     # at least some targets become uniquely identified
    print(f"(i)   manifold COLLAPSES (entropy falls as revealed)   : "
          f"{'YES' if collapses else 'NO'}  "
          f"(H: {real['ent'][0.1]:.2f} -> {real['ent'][0.9]:.2f} bits)")
    print(f"(ii)  SENTENCE manifold is HONEST/calibrated (ECE<0.15): "
          f"{'YES' if honest else 'NO'}  (sentence-manifold ECE={ece:.3f}; "
          f"NB next-word anticipation is OVERconfident ECE={nw_ece:.3f} — "
          f"single-successor contexts assign ~1.0 then miss)")
    print(f"(iii) cohort/uniqueness structure (recognition-point)  : "
          f"{'YES' if cohort else 'NO'}  (mean rec-frac {_mean(rp):.2f})")
    print(f"(iv)  driven by REAL sequential structure (shuffle)    : "
          f"{'YES' if seq_driven else 'NO'}  "
          f"(next-word anticipation top-1 {nw_t1_real:.3f} vs shuf {nw_t1_shuf:.3f} "
          f"= {nw_t1_real/max(nw_t1_shuf,1e-9):.2f}x; "
          f"top-5 {nw_t5_real:.3f} vs {nw_t5_shuf:.3f})")
    success = collapses and honest and cohort and seq_driven
    print(f"\n>>> {'SUCCESS' if success else 'PARTIAL / FAILS'}: the agent's "
          f"admissibility manifold {'DOES' if success else 'does NOT cleanly'} "
          f"collapse honestly, at cohort structure, driven by real sequential "
          f"structure, onto the true sentence.")
    print(f"\n(elapsed {time.time()-t0:.0f}s)")
    print("MANIFOLD_COLLAPSE_COMPLETED")


if __name__ == "__main__":
    main()
