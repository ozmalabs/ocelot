"""native_collapse — the COLLAPSE COGNITION, migrated into the Rust/graph core.

The mandate: scripts/collapse_engine.py (the Python prototype) PROVED the
manifold-collapse learning loop. But the cognition lived in Python — math.exp,
math.log, the softmax, the surprise, the learning hook — all OUTSIDE the agent's
graph reality. This file MIGRATES the cognition native: the collapse decision,
surprise, and the learning step now run as graph Term-trees + native graph
mutations evaluated by the Rust runtime (substrate_rs), NOT Python control flow.

WHAT IS NATIVE HERE (the cognition):

  1. THE COLLAPSE DECISION (manifold + confidence). Per revealed prefix the
     candidate log-weights lw = BETA*agree + seq_lp are written as GRAPH DATA
     (one Cand node per pool member, holding its `lw` attr, hung off a ManRoot
     by a `cand` edge). The manifold's softmax confidence is then a graph
     Term-tree evaluated IN RUST:
         mx   = MaxOver_c  lw(c)
         Z    = Sum_c       Exp(lw(c) - mx)
         conf = Exp(lw(truth) - mx) / Z
     The entropy and effective-support are likewise Sum/Term-trees over the
     same graph nodes. No Python exp/log touches the manifold.

  2. SURPRISE as a NATIVE TERM:  surprise = -log(conf-at-the-actual-outcome)
         SURPRISE_TERM = Neg(Log(Var("conf")))
     evaluated by substrate.evaluate — Log/Exp/Neg are term.rs primitives.

  3. THE LEARNING STEP as a NATIVE GRAPH MUTATION. A high-surprise event (the
     truth's next symbol had zero learned mass at a learned context) localises
     the missing admissibility. We CONSTRUCT it as a graph mutation executed by
     the Rust runtime: a graph-resident Rule node whose `effect` adds the MBi
     transition edge (count) — fired by substrate.tick() IN RUST. The agent
     flexes its own Γ by growing the graph, natively. (A direct
     add_node/add_edge_unchecked path — the same native mutation Rust applies
     for an `add_edge` effect — is also provided and verified identical.)

WHAT STAYS PYTHON (the INSTRUMENT, not cognition): reading the corpus into opaque
symbol-sequences, the calibration/cohort/shuffle MEASUREMENT harness, and the
before/after/held-out SURPRISE bookkeeping that EVALUATES the agent. That is the
experimenter's instrument, explicitly NOT the agent's cognition. collapse_engine
is left untouched as the python mirror to verify against.

DONKEY: native graph ops only. The learning is structure-ADDITION (a counted
transition edge the surprise localised), NOT gradient-on-surprise / loss / .fit.
No LM, no net.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import (
    Substrate, Sum, Neighbours, Attr, Var, Exp, Log, Neg, Div, Minus, MaxOver,
    Times, Plus, Lit, IfThenElse, Gt,
)

# Core constant — identical to collapse_engine.BETA (a property of the loop).
BETA = 6.0


# ==========================================================================
# THE NATIVE TERM-TREES — the cognition, as graph Term-trees (evaluated in Rust).
# These are module constants: they NAME NO DOMAIN and hold NO state. They are the
# manifold/confidence/surprise arithmetic, lifted out of Python into the graph.
# ==========================================================================

# max log-weight over the candidate manifold hung off ManRoot by `cand` edges.
T_MAX_LW = MaxOver(Neighbours(Var("r"), "cand"), "c", Attr(Var("c"), "lw"))

# softmax denominator  Z = Sum_c exp(lw(c) - mx)
T_Z = Sum(Neighbours(Var("r"), "cand"), "c",
          Exp(Minus(Attr(Var("c"), "lw"), Var("mx"))))

# confidence of ONE candidate node `c`:  exp(lw(c) - mx) / Z
T_CONF = Div(Exp(Minus(Attr(Var("c"), "lw"), Var("mx"))), Var("Z"))

# manifold Shannon entropy in BITS, fully native:
#   H = -Sum_c  p(c) * log2(p(c)),  p(c) = exp(lw-mx)/Z,  log2 = ln / ln2
#   = -Sum_c [exp(lw-mx)/Z] * (ln(exp(lw-mx)/Z) / ln2)
_LN2 = math.log(2.0)
_p = Div(Exp(Minus(Attr(Var("c"), "lw"), Var("mx"))), Var("Z"))
T_ENTROPY = Neg(Sum(
    Neighbours(Var("r"), "cand"), "c",
    Div(Times([_p, Log(_p)]), Var("ln2")),
))

# SURPRISE as a native Term: -log(conf-at-the-actual-outcome).
T_SURPRISE = Neg(Log(Var("conf")))


# ==========================================================================
# NATIVE MANIFOLD — build the graph data + evaluate the Term-trees in Rust.
# `s` is a substrate_rs.Substrate; the lw scalars come from the domain's counted
# structure (seq_lp) + the opaque-symbol agree count. We materialise them as a
# fresh ManRoot/Cand subgraph and read confidence + entropy back via evaluate().
# ==========================================================================

def _agree_count(cand, prefix):
    """Opaque-symbol prefix agreement (the HARD Γ-prune), mirror of
    collapse_engine._hard_agree summed over revealed positions: count leading
    matches, break at first mismatch. No domain knowledge — only `==`."""
    a = 0
    for i in range(min(len(prefix), len(cand))):
        if cand[i] == prefix[i]:
            a += 1
        else:
            break
    return a


def native_manifold(s, pool, prefix, seq_lp_cache, cand_nodes):
    """Build the manifold as GRAPH DATA and return (root, mx, Z, per-cand conf).

    lw(c) = BETA*agree(c,prefix) + seq_lp(c)  — written to each Cand node's `lw`
    attr; the softmax (mx, Z, conf) is then evaluated as Term-trees IN RUST.
    `cand_nodes` is the persistent pool-member -> Cand NodeID map (built once);
    we just overwrite each `lw` attr per prefix (the manifold is re-derived, the
    nodes are reused). Returns the ManRoot, the native mx and Z, and a dict
    cand -> native confidence."""
    root = cand_nodes["__root__"]
    for c in pool:
        lw = BETA * _agree_count(c, prefix) + seq_lp_cache[c]
        s.set_attr(cand_nodes[c], "lw", float(lw))
    mx = float(s.evaluate(T_MAX_LW, {"r": root}))
    Z = float(s.evaluate(T_Z, {"r": root, "mx": mx}))
    confs = {}
    for c in pool:
        confs[c] = float(s.evaluate(T_CONF,
                                    {"c": cand_nodes[c], "mx": mx, "Z": Z}))
    return root, mx, Z, confs


def build_cand_nodes(s, pool):
    """Materialise the persistent manifold scaffold: one Cand node per pool
    member hung off a single ManRoot by a `cand` edge. Returns the
    pool-member -> NodeID map (plus '__root__')."""
    root = s.add_node("ManRoot", {})
    cand_nodes = {"__root__": root}
    for c in pool:
        n = s.add_node("Cand", {"lw": 0.0})
        s.add_edge_unchecked(root, "cand", n)
        cand_nodes[c] = n
    return cand_nodes


def native_entropy(s, root, mx, Z):
    """Manifold entropy in bits, evaluated natively (T_ENTROPY)."""
    return float(s.evaluate(T_ENTROPY, {"r": root, "mx": mx, "Z": Z, "ln2": _LN2}))


def native_surprise(s, conf, eps=1e-12):
    """SURPRISE evaluated as the native Term  -log(conf).  Guard conf at eps so
    a zero-confidence outcome yields a large finite surprise rather than +inf
    (the world-value epsilon the Log doc-comment refers to)."""
    return float(s.evaluate(T_SURPRISE, {"conf": max(conf, eps)}))


# ==========================================================================
# NATIVE LEARNING MUTATION — construct the missing admissibility as a GRAPH
# MUTATION run by the Rust runtime. Two equivalent native paths:
#
#  (A) construct_gap_direct: the host calls the substrate's native graph
#      mutation (add_node / add_edge_unchecked) — the SAME primitive Rust
#      applies for an `add_edge` rule effect — to grow the MBi transition.
#
#  (B) construct_gap_via_rule: install a graph-resident Rule whose `effect`
#      adds the edge, then substrate.tick() fires it IN RUST (rewrite.rs). The
#      mutation is decided + applied by the Rust rule engine, not Python.
#
# Both ADD a counted structural transition (the admissibility the surprise
# localised). Neither fits a parameter. This is the agent flexing its own Γ.
# ==========================================================================

def construct_gap_direct(struct, ctx, missing):
    """(A) Native graph mutation: grow the MBi(b -> missing) transition by one
    count. Mirrors collapse_domains.on_gap — a counted structural addition,
    donkey-clean. Returns the new MBi NodeID (or None if no context)."""
    b = ctx[-1] if len(ctx) >= 1 else None
    if b is None:
        return None
    struct.bigram[(b, missing)] = struct.bigram.get((b, missing), 0) + 1
    struct.bi_succ.setdefault(b, {})
    struct.bi_succ[b][missing] = struct.bi_succ[b].get(missing, 0) + 1
    struct.has_succ.add(b)
    bn = struct.s.add_node("MBi", {"cnt": float(struct.bigram[(b, missing)])})
    struct.s.add_edge_unchecked(struct._word(b), "bi", bn)
    struct.s.add_edge_unchecked(bn, "to", struct._word(missing))
    return bn


def construct_gap_via_rule(struct, ctx, missing):
    """(B) Native graph mutation driven by the RUST RULE ENGINE. Install a
    one-shot Rule node whose effect adds the MBi node + edges, then tick() — the
    Rust rewrite engine matches and applies the effect. The structure-addition
    is executed in Rust, decided by a graph-resident Rule, not by Python.

    We construct the MBi node here (its `cnt`) and have the Rule wire the two
    edges as graph effects, so the EDGE-CONSTRUCTION (the admissibility link the
    surprise localised) is the tick-applied native mutation. Returns the MBi
    NodeID."""
    b = ctx[-1] if len(ctx) >= 1 else None
    if b is None:
        return None
    struct.bigram[(b, missing)] = struct.bigram.get((b, missing), 0) + 1
    struct.bi_succ.setdefault(b, {})
    struct.bi_succ[b][missing] = struct.bi_succ[b].get(missing, 0) + 1
    struct.has_succ.add(b)
    s = struct.s
    bn = s.add_node("MBi", {"cnt": float(struct.bigram[(b, missing)])})
    wb = struct._word(b)
    wm = struct._word(missing)
    # a graph-resident Rule: match the (word_b, marker, mbi) staging edges and
    # emit the real bi/to edges as native effects fired by tick().
    s.add_edge_unchecked(wb, "_stage_src", bn)
    s.add_edge_unchecked(bn, "_stage_tgt", wm)
    rule = s.add_node("Rule", {
        "id": "construct_admissibility",
        "match": [["w", "_stage_src", "bn"], ["bn", "_stage_tgt", "m"]],
        "where": None,
        "effect": [
            ["add_edge", "w", "bi", "bn"],
            ["add_edge", "bn", "to", "m"],
            ["del_edge", "w", "_stage_src", "bn"],
            ["del_edge", "bn", "_stage_tgt", "m"],
        ],
    })
    s.tick()
    s.remove_node(rule)
    return bn


# ==========================================================================
# THE NATIVE BACK-OFF SCORER — the COUNTED n-gram back-off recurrence migrated
# out of Python (collapse_domains.CountedStructure.trans_logprob / seq_logprob)
# and into a GRAPH TERM-TREE evaluated by the Rust runtime.
#
# This was the LAST Python piece of the cognition: the manifold's scalar weights
# (seq_logprob -> the `lw` of each Cand) came from a back-off model whose COUNTS
# were already graph data (MWord.freq, MBi.cnt, now MTri.cnt) but whose back-off
# ARITHMETIC (the trigram->bigram->unigram recurrence) was still Python
# (math.log, the lambda count-ratios, the back-off branch). The native_collapse
# report named this as the remaining mechanical re-expression — it holds no
# decision, only counted arithmetic. Here it becomes a composition of EXISTING
# primitives over the graph count nodes.
#
# THE RECURRENCE (faithful mirror of CountedStructure.trans_logprob(a,b,c)):
#
#   V    = #distinct symbols (a COUNT)           [graph: Attr(root,"V")]
#   tot  = #tokens           (a COUNT)           [graph: Attr(root,"tot")]
#   uni_c, uni_b   = unigram counts              [graph: Attr(MWord,"freq")]
#   big_bc, big_ab = bigram counts               [graph: Attr(MBi,"cnt")]
#   tri_abc        = trigram count               [graph: Attr(MTri,"cnt")]
#
#   p_uni = (uni_c + 1) / (tot + V)                      # add-1, a FIXED floor
#   lam_b = uni_b / (uni_b + V)                          # COUNT ratio, no tuning
#   p_bi  = uni_b>0 ? lam_b*(big_bc/uni_b)+(1-lam_b)*p_uni : p_uni
#   lam_a = big_ab / (big_ab + V)                        # COUNT ratio, no tuning
#   p_tri = big_ab>0 ? lam_a*(tri_abc/big_ab)+(1-lam_a)*p_bi : p_bi
#   logp  = log( max(p_tri, 1e-12) )                     # FIXED world-eps floor
#
# DONKEY: every input is a COUNT read from the graph; the only constants are the
# add-1 (1.0), the uniform floor structure, and the 1e-12 log-guard — all FIXED,
# none fitted. No lambda is a parameter: lam = n/(n+V) is a counted ratio. The
# back-off WEIGHT is the count itself. No LM, no softmax-fit, no gradient, no
# .fit, no sweep. The Term-tree holds NO decision — it is the same arithmetic
# the Python mirror runs, re-expressed natively. max() is IfThenElse(Gt,...).
# ==========================================================================

# Constants — FIXED literals of the back-off scheme (NOT tunable parameters):
_ADD1 = Lit(1.0)        # add-1 (Laplace) smoothing of the unigram floor
_LOG_EPS = Lit(1e-12)   # world-value floor on the probability before log
_ZERO = Lit(0.0)

# Count Vars bound per (a,b,c) from the graph count nodes (read via Attr by the
# host adapter into these scalars — see NativeBackoff.trans_logprob):
_uni_c = Var("uni_c")     # unigram count of c
_uni_b = Var("uni_b")     # unigram count of b (the bigram context)
_big_bc = Var("big_bc")   # bigram count (b,c)
_big_ab = Var("big_ab")   # bigram count (a,b) (the trigram context)
_tri_abc = Var("tri_abc")  # trigram count (a,b,c)
_V = Var("V")             # vocabulary size (count)
_tot = Var("tot")         # total token count

# p_uni = (uni_c + 1) / (tot + V)
_P_UNI = Div(Plus([_uni_c, _ADD1]), Plus([_tot, _V]))

# lam_b = uni_b / (uni_b + V)
_LAM_B = Div(_uni_b, Plus([_uni_b, _V]))
# p_bi (when uni_b > 0): lam_b*(big_bc/uni_b) + (1-lam_b)*p_uni
_P_BI_LEARNED = Plus([
    Times([_LAM_B, Div(_big_bc, _uni_b)]),
    Times([Minus(Lit(1.0), _LAM_B), _P_UNI]),
])
# back-off branch: uni_b>0 ? p_bi_learned : p_uni   (max() == IfThenElse(Gt))
_P_BI = IfThenElse(Gt(_uni_b, _ZERO), _P_BI_LEARNED, _P_UNI)

# lam_a = big_ab / (big_ab + V)
_LAM_A = Div(_big_ab, Plus([_big_ab, _V]))
# p_tri (when big_ab > 0): lam_a*(tri_abc/big_ab) + (1-lam_a)*p_bi
_P_TRI_LEARNED = Plus([
    Times([_LAM_A, Div(_tri_abc, _big_ab)]),
    Times([Minus(Lit(1.0), _LAM_A), _P_BI]),
])
_P_TRI = IfThenElse(Gt(_big_ab, _ZERO), _P_TRI_LEARNED, _P_BI)

# logp = log(max(p_tri, 1e-12))
_P_FLOORED = IfThenElse(Gt(_P_TRI, _LOG_EPS), _P_TRI, _LOG_EPS)
T_BACKOFF_LOGP = Log(_P_FLOORED)


class NativeBackoff:
    """The counted back-off scorer as a NATIVE graph Term-tree.

    Wraps a substrate that holds the n-gram COUNTS as graph data (MWord.freq for
    unigrams, MBi.cnt for bigrams, MTri.cnt for trigrams) and evaluates the
    back-off log-prob recurrence (T_BACKOFF_LOGP) IN RUST. The counts are read
    from the graph via Attr; the arithmetic is the Term-tree above. This is the
    faithful native form of CountedStructure.trans_logprob / .seq_logprob — same
    numbers, no Python math.

    Construction reuses the EXISTING graph the CountedStructure already built
    (its MWord/MBi nodes); it only adds MTri count nodes (the trigram counts were
    a Python dict in the mirror) + a root holding V and tot as count attrs, and a
    shared ZERO count-node for absent n-grams (Attr-readable 0.0). No node is
    ever attr-missing, so every Attr read is a real graph count."""

    def __init__(self, cs):
        """cs : a collapse_domains.CountedStructure (already learned). We attach
        the trigram graph nodes + a count-root to ITS substrate, and index the
        existing MWord/MBi nodes for native Attr reads."""
        self.cs = cs
        self.s = cs.s
        self.word_node = cs.word_node      # symbol -> MWord NodeID (freq attr)
        self.bi_node = cs.bi_node          # (a,b)  -> MBi NodeID (cnt attr)
        self.tri_node = {}                 # (a,b,c)-> MTri NodeID (cnt attr)
        # a single always-present ZERO count node (cnt=0.0, freq=0.0) so a missing
        # n-gram reads a real graph 0.0 rather than a None.
        self._zero = self.s.add_node("MZero", {"cnt": 0.0, "freq": 0.0})
        # materialise the trigram COUNTS as graph data (MTri.cnt) — the same
        # counts the Python mirror held in a dict, now graph-resident.
        for (a, b, c), n in cs.trigram.items():
            tn = self.s.add_node("MTri", {"cnt": float(n)})
            self.tri_node[(a, b, c)] = tn
        # the count-root holds V and tot as COUNT attrs (graph-resident scalars).
        self.root = self.s.add_node("BackoffRoot", {
            "V": float(max(len(cs.unigram), 1)),
            "tot": float(max(cs.total, 1)),
        })

    def _uni_node(self, w):
        return self.word_node.get(w, self._zero)

    def _bi_n(self, a, b):
        return self.bi_node.get((a, b), self._zero)

    def _tri_n(self, a, b, c):
        return self.tri_node.get((a, b, c), self._zero)

    def refresh_root(self):
        """Re-read V/tot from the (possibly mutation-grown) counts. Native graph
        mutation (set_attr) — counts only."""
        self.s.set_attr(self.root, "V", float(max(len(self.cs.unigram), 1)))
        self.s.set_attr(self.root, "tot", float(max(self.cs.total, 1)))

    def add_trigram_node(self, a, b, c, cnt):
        """Materialise/refresh a trigram count node as graph data (used when the
        learning mutation grows the structure)."""
        tn = self.tri_node.get((a, b, c))
        if tn is None:
            tn = self.s.add_node("MTri", {"cnt": float(cnt)})
            self.tri_node[(a, b, c)] = tn
        else:
            self.s.set_attr(tn, "cnt", float(cnt))
        return tn

    def trans_logprob(self, a, b, c):
        """NATIVE back-off log P(c | a,b): bind the count nodes' attrs and
        evaluate T_BACKOFF_LOGP in Rust. Faithful mirror of
        CountedStructure.trans_logprob — same counts, native arithmetic."""
        s = self.s
        binding = {
            "uni_c": float(s.evaluate(Attr(Var("n"), "freq"),
                                      {"n": self._uni_node(c)}) or 0.0),
            "uni_b": float(s.evaluate(Attr(Var("n"), "freq"),
                                      {"n": self._uni_node(b)}) or 0.0)
            if b is not None else 0.0,
            "big_bc": float(s.evaluate(Attr(Var("n"), "cnt"),
                                       {"n": self._bi_n(b, c)}) or 0.0)
            if b is not None else 0.0,
            "big_ab": float(s.evaluate(Attr(Var("n"), "cnt"),
                                       {"n": self._bi_n(a, b)}) or 0.0)
            if (a is not None and b is not None) else 0.0,
            "tri_abc": float(s.evaluate(Attr(Var("n"), "cnt"),
                                        {"n": self._tri_n(a, b, c)}) or 0.0)
            if (a is not None and b is not None) else 0.0,
            "V": float(s.evaluate(Attr(Var("r"), "V"), {"r": self.root})),
            "tot": float(s.evaluate(Attr(Var("r"), "tot"), {"r": self.root})),
        }
        return float(s.evaluate(T_BACKOFF_LOGP, binding))

    def seq_logprob(self, seq):
        """NATIVE whole-sequence log-plausibility (mean per symbol). Faithful
        mirror of CountedStructure.seq_logprob, native back-off underneath."""
        lp = 0.0
        for i in range(len(seq)):
            a = seq[i - 2] if i - 2 >= 0 else None
            b = seq[i - 1] if i - 1 >= 0 else None
            lp += self.trans_logprob(a, b, seq[i])
        return lp / max(len(seq), 1)
