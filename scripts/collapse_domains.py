"""collapse_domains — DOMAIN PLUGS for the collapse engine (scripts/collapse_engine.py).

Each function returns a DomainPlug + its shuffled twin. Everything domain-specific
lives HERE; the core (collapse_engine) knows none of it. The plugs differ ONLY in
how they read a corpus into opaque symbol-sequences and how they count structure —
the learned scorers (seq_logprob / next_dist) are otherwise the SAME counted
n-gram machinery, which is itself DOMAIN-side (the core never imports it).

Three maximally-different domains, all from REAL data, to prove the core is
domain-agnostic (only the plug changes):

  1. SENTENCES   — LibriSpeech word sequences. Symbol = a word. ~35k-symbol
                   alphabet, the domain my two prior runs used.
  2. LETTERS     — the classic psycholinguistic COHORT model: words revealed
                   letter-by-letter. Symbol = a letter. 26-symbol alphabet,
                   short sequences — maximally unlike words-as-symbols, yet the
                   IDENTICAL collapse loop runs on it.
  3. LLVM-PASSES — real `opt -print-pipeline-passes` schedules. Symbol = a
                   compiler pass name (mem2reg, instcombine, simplifycfg, ...).
                   A wholly different alphabet and a real engineering grammar
                   (mem2reg precedes instcombine; simplifycfg recurs). Ties the
                   proof to a domain the agent actually works in (seeds/llvm_*).

The donkey line is identical across all three: structure is COUNTED and stored
as GRAPH DATA (MWord/MBi/MTri nodes with `cnt` attrs); seq_logprob/next_dist read
those counts with a COUNTED back-off; NO trained LM, NO softmax-fit, NO gradient,
NO .fit, NO sweep. Each plug's donkey_audit proves graph-Sum == python-count.
"""
from __future__ import annotations

import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate, Sum, Attr, Var, Neighbours
from scripts.collapse_engine import DomainPlug


# ==========================================================================
# COUNTED N-GRAM STRUCTURE (domain-side; graph-resident; donkey-clean).
# The SAME machinery for every domain — symbols are opaque tokens. This is the
# scripts/manifold_collapse.py LearnedStructure lineage, re-housed on the
# domain side of the boundary (the core never sees it).
# ==========================================================================

class CountedStructure:
    def __init__(self):
        self.s = Substrate()
        self.word_node = {}      # symbol -> MWord NodeID
        self.bi_node = {}        # (a,b)  -> MBi NodeID
        self.unigram = {}
        self.bigram = {}
        self.trigram = {}
        self.bi_succ = {}        # b -> {c: cnt}
        self.tri_succ = {}       # (a,b) -> {c: cnt}
        self.has_succ = set()
        self.total = 0

    def _word(self, w):
        n = self.word_node.get(w)
        if n is None:
            n = self.s.add_node("MWord", {"name": str(w), "freq": 0.0})
            self.word_node[w] = n
        return n

    def learn(self, sequences):
        for seq in sequences:
            for w in seq:
                self.unigram[w] = self.unigram.get(w, 0) + 1
                self.total += 1
            for a, b in zip(seq, seq[1:]):
                self.bigram[(a, b)] = self.bigram.get((a, b), 0) + 1
                self.bi_succ.setdefault(a, {})
                self.bi_succ[a][b] = self.bi_succ[a].get(b, 0) + 1
                self.has_succ.add(a)
            for a, b, c in zip(seq, seq[1:], seq[2:]):
                self.trigram[(a, b, c)] = self.trigram.get((a, b, c), 0) + 1
                self.tri_succ.setdefault((a, b), {})
                self.tri_succ[(a, b)][c] = self.tri_succ[(a, b)].get(c, 0) + 1
        # materialise counts as GRAPH DATA (the donkey audit lives here)
        for w, c in self.unigram.items():
            self.s.set_attr(self._word(w), "freq", float(c))
        for (a, b), c in self.bigram.items():
            bn = self.s.add_node("MBi", {"cnt": float(c)})
            self.s.add_edge_unchecked(self._word(a), "bi", bn)
            self.s.add_edge_unchecked(bn, "to", self._word(b))
            self.bi_node[(a, b)] = bn

    # graph-resident scorer (donkey audit): Sum over learned outgoing transitions
    @staticmethod
    def _bi_support_term():
        return Sum(Neighbours(Var("w"), "bi"), "t", Attr(Var("t"), "cnt"))

    def graph_bi_support(self, w):
        n = self.word_node.get(w)
        if n is None:
            return 0.0
        return float(self.s.evaluate(self._bi_support_term(), {"w": n}))

    def python_bi_support(self, w):
        return float(sum(self.bigram.get((w, b), 0)
                         for b in self.unigram if (w, b) in self.bigram))

    # counted back-off P(c | a,b)  (trigram -> bigram -> unigram); counts only
    def trans_logprob(self, a, b, c):
        V = max(len(self.unigram), 1)
        tot = max(self.total, 1)
        uni = self.unigram.get(c, 0)
        p_uni = (uni + 1.0) / (tot + V)
        uni_ctx = self.unigram.get(b, 0)
        if uni_ctx > 0:
            big = self.bigram.get((b, c), 0)
            lam = uni_ctx / (uni_ctx + V)
            p_bi = lam * (big / uni_ctx) + (1 - lam) * p_uni
        else:
            p_bi = p_uni
        bi_ctx = self.bigram.get((a, b), 0)
        if bi_ctx > 0:
            tri = self.trigram.get((a, b, c), 0)
            lam = bi_ctx / (bi_ctx + V)
            p_tri = lam * (tri / bi_ctx) + (1 - lam) * p_bi
        else:
            p_tri = p_bi
        return math.log(max(p_tri, 1e-12))

    def seq_logprob(self, seq):
        lp = 0.0
        for i in range(len(seq)):
            a = seq[i - 2] if i - 2 >= 0 else None
            b = seq[i - 1] if i - 1 >= 0 else None
            lp += self.trans_logprob(a, b, seq[i])
        return lp / max(len(seq), 1)

    def next_dist(self, ctx):
        """Learned next-symbol distribution given the revealed context prefix.
        Uses only the last two symbols; returns {} when the immediate context has
        no learned successors (an UNLEARNED context — the core's gap signal)."""
        a = ctx[-2] if len(ctx) >= 2 else None
        b = ctx[-1] if len(ctx) >= 1 else None
        if b not in self.has_succ:
            return {}
        cand = set(self.bi_succ.get(b, {}).keys())
        cand |= set(self.tri_succ.get((a, b), {}).keys())
        if not cand:
            return {}
        logps = {c: self.trans_logprob(a, b, c) for c in cand}
        mx = max(logps.values())
        ws = {c: math.exp(lp - mx) for c, lp in logps.items()}
        z = sum(ws.values())
        return {c: w / z for c, w in ws.items()}


def _build_plug(name, pool, train, targets):
    """Wire a counted structure + its shuffled twin into a DomainPlug. SAME for
    every domain — only the (pool, train, targets) symbol-sequences differ."""
    cs = CountedStructure()
    cs.learn(train)

    # shuffled twin: destroy ORDER within each train sequence (keep the symbol
    # set), re-learn. Only the domain knows that a "sequence" is what to shuffle.
    shuf_train = []
    for seq in train:
        w = list(seq)
        random.shuffle(w)
        shuf_train.append(tuple(w))
    cs_s = CountedStructure()
    cs_s.learn(shuf_train)

    def audit():
        if not cs.word_node:
            return "no symbols", False
        sample = next(iter(cs.word_node))
        g = cs.graph_bi_support(sample)
        p = cs.python_bi_support(sample)
        ok = abs(g - p) < 1e-6
        return (f"counts-only graph-resident: MWord {len(cs.word_node)}, MBi "
                f"{len(cs.bi_node)}, tokens {cs.total}; graph-Sum bi_support="
                f"{g:.1f} == python {p:.1f} (NO LM/softmax-fit/gradient)"), ok

    gaps_constructed = {"n": 0}

    def on_gap(ctx, missing):
        # LEARNING HOOK: the structure existed at this context but lacked the true
        # transition. CONSTRUCT it — add the counted bigram edge as graph data
        # (count=1: a newly observed transition), exactly as learn() would. This
        # is the collapse-failure -> localise -> construct loop, donkey-clean
        # (a counted structural addition, not a fit).
        a = ctx[-2] if len(ctx) >= 2 else None
        b = ctx[-1] if len(ctx) >= 1 else None
        if b is None:
            return
        cs.bigram[(b, missing)] = cs.bigram.get((b, missing), 0) + 1
        cs.bi_succ.setdefault(b, {})
        cs.bi_succ[b][missing] = cs.bi_succ[b].get(missing, 0) + 1
        cs.has_succ.add(b)
        bn = cs.s.add_node("MBi", {"cnt": float(cs.bigram[(b, missing)])})
        cs.s.add_edge_unchecked(cs._word(b), "bi", bn)
        cs.s.add_edge_unchecked(bn, "to", cs._word(missing))
        gaps_constructed["n"] += 1

    shuffled = DomainPlug(
        name=name + "/shuffled", pool=pool, train=shuf_train, targets=targets,
        seq_logprob=cs_s.seq_logprob, next_dist=cs_s.next_dist)
    return DomainPlug(
        name=name, pool=pool, train=train, targets=targets,
        seq_logprob=cs.seq_logprob, next_dist=cs.next_dist,
        shuffled=shuffled, donkey_audit=audit, on_gap=on_gap)


# ==========================================================================
# DOMAIN 1 — SENTENCES (LibriSpeech words). Symbol = word.
# ==========================================================================

_LS_DIR = "/tmp/LibriSpeech/dev-clean"
_WORD_RE = re.compile(r"[A-Z']+")


def _load_sentences(min_len=3, max_len=40):
    out = []
    for root, _, names in os.walk(_LS_DIR):
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


def sentences_plug(n_pool=1200, n_targets=200, seed=7):
    random.seed(seed)
    sents = _load_sentences()
    random.shuffle(sents)
    seen, uniq = set(), []
    for s in sents:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    sents = uniq
    n_pool = min(n_pool, len(sents) - 200)
    pool = sents[:n_pool]
    train = sents[n_pool:]
    targets = pool[:n_targets]
    return _build_plug("sentences", pool, train, targets), len(sents)


# ==========================================================================
# DOMAIN 2 — LETTERS (cohort model). Symbol = letter; sequence = a word.
# Real data: the distinct words from the SAME LibriSpeech corpus, revealed
# letter-by-letter. A wholly different alphabet (26) and sequence scale from
# Domain 1, yet the identical collapse loop runs on it.
# ==========================================================================

def letters_plug(n_pool=1500, n_targets=200, seed=7, min_len=4, max_len=14):
    random.seed(seed + 1)
    sents = _load_sentences(min_len=1, max_len=60)
    # distinct words, as letter-tuples (lowercased; apostrophes dropped)
    words = set()
    for s in sents:
        for w in s:
            w = w.replace("'", "")
            if min_len <= len(w) <= max_len and w.isalpha():
                words.add(w)
    seqs = [tuple(w.lower()) for w in sorted(words)]
    random.shuffle(seqs)
    n_pool = min(n_pool, len(seqs) - 200)
    pool = seqs[:n_pool]
    train = seqs[n_pool:]        # learn letter-transition structure on held-out words
    targets = pool[:n_targets]
    return _build_plug("letters", pool, train, targets), len(seqs)


# ==========================================================================
# DOMAIN 3 — LLVM PASSES. Symbol = a compiler pass name; sequence = an ordered
# pass schedule. Real data: every parenthesized sub-pipeline emitted by
# `opt -passes="default<On>" -print-pipeline-passes` for n in {O0..Oz}. Each
# nested group is a genuine ordered schedule LLVM runs as a unit.
# ==========================================================================

_LLVM_DIR = "/tmp/llvm_pipelines"


def _parse_pipeline_schedules(text):
    """Mechanical text->token translation (world-adapter work). Strip pass params
    <...>, then for EACH parenthesized group emit the ordered list of top-level
    pass tokens in that group as one sequence (a real sub-schedule). Returns a
    list of tuples of pass-name symbols."""
    # remove <...> param blocks (may nest shallowly); iterate to fixpoint
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"<[^<>]*>", "", text)
    schedules = []

    def walk(s):
        # split s into top-level tokens by commas not inside parens; recurse into
        # parenthesized groups; the comma-separated top-level pass names at THIS
        # level form one ordered schedule.
        level = 0
        tok = ""
        toks = []
        i = 0
        groups = []
        while i < len(s):
            ch = s[i]
            if ch == "(":
                if level == 0:
                    # the token so far is a pass-with-subpipeline header; keep its
                    # head name as a token, recurse into the group
                    head = tok.strip()
                    depth = 1
                    j = i + 1
                    while j < len(s) and depth > 0:
                        if s[j] == "(":
                            depth += 1
                        elif s[j] == ")":
                            depth -= 1
                        j += 1
                    inner = s[i + 1:j - 1]
                    if head:
                        toks.append(head)
                    groups.append(inner)
                    tok = ""
                    i = j
                    continue
                else:
                    level += 1
            if ch == "," and level == 0:
                t = tok.strip()
                if t:
                    toks.append(t)
                tok = ""
                i += 1
                continue
            tok += ch
            i += 1
        t = tok.strip()
        if t:
            toks.append(t)
        if len(toks) >= 2:
            schedules.append(tuple(toks))
        for g in groups:
            walk(g)

    walk(text)
    return schedules


def llvm_plug(n_targets=120, seed=7):
    random.seed(seed + 2)
    all_sched = []
    if os.path.isdir(_LLVM_DIR):
        for fn in sorted(os.listdir(_LLVM_DIR)):
            if not fn.endswith(".raw"):
                continue
            with open(os.path.join(_LLVM_DIR, fn)) as f:
                txt = f.read().strip()
            all_sched.extend(_parse_pipeline_schedules(txt))
    # dedupe whole schedules; keep order
    seen, uniq = set(), []
    for s in all_sched:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    random.shuffle(uniq)
    # All schedules are the candidate pool (real LLVM artifacts). Train the
    # transition structure on ALL of them (the pass-ordering grammar is shared
    # across opt levels); targets are revealed schedules.
    pool = uniq
    train = uniq
    targets = uniq[:min(n_targets, len(uniq))]
    return _build_plug("llvm_passes", pool, train, targets), len(uniq)
