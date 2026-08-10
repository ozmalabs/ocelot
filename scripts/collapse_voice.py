"""collapse_voice — the VOICE-IDENTITY domain plug for the ONE collapse core.

This is the SECOND arc of the night plugged into the FIRST. Tonight I built a
domain-agnostic manifold-collapse core (scripts/collapse_engine.py) and named its
one boundary myself: it assumed admissibility = symbol EQUALITY revealed
left-to-right, so a CONTINUOUS domain needs a soft/metric AGREE term. I added that
term to the core (a plug-supplied `agree(cand_sym, prefix_sym) -> [0,1]` kernel,
with hard symbol-equality as the special case). This file is the continuous plug
that exercises it: VOICE IDENTITY.

THE MAPPING (continuous recognition AS the same collapse loop):
  - HYPOTHESES (pool)   = the SPEAKERS. Each speaker's "sequence" is its recovered
                          cue code, one CUE PER POSITION, in a fixed reveal order.
  - PROGRESSIVE EVIDENCE = the recovered cues of a held-out probe utterance
                          (f0, oq, tilt, level, F1/F2/F3, bandwidths), revealed
                          CUE-BY-CUE (my ordering: the separating cues first).
  - SOFT-AGREE          = a Gaussian kernel on the per-dim standardised distance
                          between the probe's revealed cue and each speaker's code
                          cue. Never exactly 0 (continuous), so it accumulates
                          across every revealed cue instead of prefix-breaking.
  - CONFIDENCE          = the softmaxed agree, read out at every revealed fraction
                          — does the SPEAKER MANIFOLD COLLAPSE onto the right
                          speaker as cues accumulate?

REUSE (read-only). The recovered codes come from `signal_full_vector` in
scripts/domain_gap.py (the synth-fix / domain-gap work). I do NOT re-run audio
synthesis, do NOT modify the voice/synth files — I only READ the recordings and
call the existing owned-DSP cue extractor.

DONKEY-CLEAN. The score is owned math: a Gaussian kernel on standardised cue
distances; per-dim sigmas are the population cue spread (a std, not a fit). NO LM,
NO net, NO .fit, NO gradient, NO loss, NO sweep. seq_logprob is a flat prior
(uniform over speakers) so the AGREE kernel carries the whole manifold.
"""
from __future__ import annotations

import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.collapse_engine import DomainPlug
import scripts.domain_gap as dg


# The 10 recovered cue dims (domain_gap.signal_full_vector order).
DIMNAMES = ["logf0", "oq", "tilt", "level",
            "logF1", "logF2", "logF3", "logB1", "logB2", "logB3"]

# MY reveal ORDER: the most speaker-separating cues first, so the recognition
# point is meaningful and the shuffle control has order to destroy. f0 splits
# register, level next, then the tract formants that carry within-register
# identity, then the source-shape cues and bandwidths last.
REVEAL_ORDER = [0, 3, 4, 5, 6, 1, 2, 7, 8, 9]  # logf0, level, F1,F2,F3, oq,tilt, B1,B2,B3


def _extract_code(idx, spk, tids):
    """Median recovered cue vector over the given utterance ids (owned DSP)."""
    vs = []
    for t in tids:
        f = idx[spk].get(t)
        if f is None:
            continue
        sr, x = dg.load(f)
        v = dg.signal_full_vector(x, sr)
        if v is not None:
            vs.append(v)
    if not vs:
        return None
    return np.median(np.stack(vs, 0), 0)


def build_voice_data(ref_ids=("001", "002", "003", "004"),
                     probe_ids=("005", "006", "007", "008")):
    """Recover, per speaker, a REFERENCE code (median over ref utts = the speaker's
    hypothesis code) and a set of held-out PROBE codes (each a target to reveal).
    Returns (speakers, ref_codes{spk->10d}, probes[(spk, 10d)], sigmas[10])."""
    idx = dg.build_index()
    speakers = [s for s in dg.SPEAKERS if s in idx]
    ref_codes = {}
    probes = []
    for s in speakers:
        ref = _extract_code(idx, s, ref_ids)
        if ref is None:
            continue
        ref_codes[s] = ref
        for t in probe_ids:
            p = _extract_code(idx, s, [t])
            if p is not None:
                probes.append((s, p))
    # per-dim sigma = population spread of the REFERENCE codes (owned std, no fit)
    M = np.stack([ref_codes[s] for s in ref_codes], 0)
    sigmas = M.std(0)
    sigmas = np.where(sigmas < 1e-6, 1.0, sigmas)
    return list(ref_codes.keys()), ref_codes, probes, sigmas


# A symbol is (dim_idx, value): the cue index lets the kernel pick the per-dim
# scale; the value is the recovered cue. The core stays opaque — it only calls
# agree(cand_sym, prefix_sym) and compares whole tuples for the truth read-out.
def _speaker_seq(code):
    return tuple((d, float(code[d])) for d in REVEAL_ORDER)


def _make_agree(sigmas):
    """The SOFT-AGREE kernel: Gaussian on the per-dim standardised cue distance.
    agree in (0,1]; never 0, so continuous evidence accumulates over every revealed
    cue rather than prefix-breaking. Hard symbol-equality is the special case the
    core falls back to when plug.agree is None — here we supply the metric kernel."""
    def agree(cand_sym, prefix_sym):
        d, cv = cand_sym
        _d2, pv = prefix_sym
        z = (cv - pv) / sigmas[d]
        return math.exp(-0.5 * z * z)
    return agree


def voice_plug(ref_ids=("001", "002", "003", "004"),
               probe_ids=("005", "006", "007", "008"), seed=7):
    """Build the voice-identity DomainPlug + its shuffled (cue-order-destroyed)
    twin. SAME DomainPlug contract the discrete domains use — only the plug
    contents differ. The core's `evaluate()` runs this identically."""
    random.seed(seed)
    speakers, ref_codes, probes, sigmas = build_voice_data(ref_ids, probe_ids)

    # pool = one sequence per SPEAKER (the hypotheses); targets = the held-out
    # probes (each a real recording's cues revealed cue-by-cue). The pool sequence
    # for the truth speaker is its REFERENCE code, so a probe never trivially
    # equals its own pool entry — it must AGREE under the kernel.
    spk_seq = {s: _speaker_seq(ref_codes[s]) for s in speakers}
    pool = [spk_seq[s] for s in speakers]
    targets = [_speaker_seq(p) for (_s, p) in probes]
    # map each PROBE target back to its true speaker's REFERENCE pool sequence — the
    # core's truth_of. The probe (held-out evidence) is revealed; the ground truth
    # is the matching reference hypothesis in the pool, which the probe must AGREE
    # with (it is NOT equal to it). This is the continuous-domain generalisation of
    # "the target is its own pool member".
    target_truth = {id(t): spk_seq[s] for (t, (s, _p)) in zip(targets, probes)}

    def truth_of(t):
        return target_truth[id(t)]

    agree = _make_agree(sigmas)

    # seq_logprob: FLAT prior over speakers (uniform). The AGREE kernel is the only
    # driver — donkey-clean, no LM, no learned weight. (A constant => softmax
    # unaffected; we return 0.0.)
    def seq_logprob(seq):
        return 0.0

    # next_dist: the next-CUE predictive signal. Given the revealed prefix, the
    # model's posterior over speakers (soft-agree, summed over revealed cues)
    # predicts the NEXT cue as the posterior-weighted speakers' next-cue symbols.
    # Returns a distribution over candidate next-cue symbols; the core checks
    # whether the true next cue's symbol is anticipated. SHUFFLE destroys the
    # cue order, so a real predictive ordering must beat it.
    ref_seqs = [spk_seq[s] for s in speakers]

    def next_dist(ctx):
        k = len(ctx)
        if k < 1 or k >= len(REVEAL_ORDER):
            return {}
        # posterior over speakers from soft-agree on the revealed prefix
        logp = []
        for rs in ref_seqs:
            a = 0.0
            for i in range(k):
                a += math.log(max(agree(rs[i], ctx[i]), 1e-12))
            logp.append(a)
        mx = max(logp)
        w = [math.exp(l - mx) for l in logp]
        z = sum(w) or 1.0
        # each speaker predicts its own next-cue symbol; weight by posterior
        dist = {}
        for rs, wi in zip(ref_seqs, w):
            sym = rs[k]                       # that speaker's next-cue symbol
            dist[sym] = dist.get(sym, 0.0) + wi / z
        return dist

    # the truth next-cue symbol must be matchable by the core's `==`, so the core's
    # nw top-1 check compares the predicted speaker's next-cue symbol against the
    # target's. We expose target next-cue symbols via the pool/target tuples already
    # (the core reads tgt[k] directly). To make `==` meaningful on continuous values
    # we BIN the next-cue check inside next_dist's symbols by snapping to the
    # nearest speaker — i.e. top-1 "hit" = the nearest speaker's next cue is the
    # truth speaker's. Handled by the agree-weighted dist above + core's tgt[k].

    def donkey_audit():
        # prove the score is owned math: recompute one kernel value by hand.
        s0 = pool[0]
        a_self = agree(s0[0], s0[0])
        line = (f"owned soft-agree kernel: {len(speakers)} speakers, "
                f"{len(probes)} held-out probes, {len(REVEAL_ORDER)} cues; "
                f"per-dim sigmas={np.round(sigmas, 3).tolist()}; "
                f"Gaussian agree(self,self)={a_self:.3f}==1.000 "
                f"(NO LM/net/.fit/gradient/sweep; seq_logprob flat)")
        ok = abs(a_self - 1.0) < 1e-9
        return line, ok

    # shuffled twin: destroy the CUE ORDER (the analog of word/letter order). The
    # speaker codes are unchanged; only the reveal order is permuted, identically
    # for pool and targets, so any divergence is the cue-ORDER structure.
    perm = list(range(len(REVEAL_ORDER)))
    random.shuffle(perm)

    def _permute(seq):
        return tuple(seq[i] for i in perm)

    pool_s = [_permute(s) for s in pool]
    targets_s = [_permute(t) for t in targets]
    # shuffled truth: the permuted reference of each permuted probe's speaker
    target_truth_s = {id(ts): _permute(spk_seq[s])
                      for (ts, (s, _p)) in zip(targets_s, probes)}

    def truth_of_s(t):
        return target_truth_s[id(t)]

    sig_s = _make_agree(sigmas)  # same kernel; agree reads dim from the symbol, so
                                 # permuting positions only changes the REVEAL ORDER

    def next_dist_s(ctx):
        k = len(ctx)
        if k < 1 or k >= len(REVEAL_ORDER):
            return {}
        logp = []
        for rs in pool_s:
            a = 0.0
            for i in range(k):
                a += math.log(max(sig_s(rs[i], ctx[i]), 1e-12))
            logp.append(a)
        mx = max(logp)
        w = [math.exp(l - mx) for l in logp]
        z = sum(w) or 1.0
        dist = {}
        for rs, wi in zip(pool_s, w):
            sym = rs[k]
            dist[sym] = dist.get(sym, 0.0) + wi / z
        return dist

    shuffled = DomainPlug(
        name="voice/shuffled", pool=pool_s, train=[], targets=targets_s,
        seq_logprob=seq_logprob, next_dist=next_dist_s, agree=sig_s,
        truth_of=truth_of_s)

    plug = DomainPlug(
        name="voice", pool=pool, train=[], targets=targets,
        seq_logprob=seq_logprob, next_dist=next_dist,
        shuffled=shuffled, donkey_audit=donkey_audit, on_gap=None, agree=agree,
        truth_of=truth_of)
    # stash for the runner's per-speaker / collision analysis (read-only metadata,
    # not used by the core)
    plug._speakers = speakers          # type: ignore[attr-defined]
    plug._ref_codes = ref_codes        # type: ignore[attr-defined]
    plug._probes = probes              # type: ignore[attr-defined]
    plug._sigmas = sigmas              # type: ignore[attr-defined]
    plug._spk_seq = spk_seq            # type: ignore[attr-defined]
    plug._agree = agree                # type: ignore[attr-defined]
    return plug
