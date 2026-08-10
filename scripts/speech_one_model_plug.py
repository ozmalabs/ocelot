"""SPEECH as a plug into the agent's EXISTING collapse cognition — the ONE-MODEL-LOOPED-BACK spine.

The creator's architecture: speech is ONE generative model M used in four loop configurations, not six
modules. M = a gestural plan (phone sequence) -> a predicted smooth acoustic trajectory (the FORWARD
model). UNDERSTANDING = M inverted (acoustic -> plan). INTERNAL (inner speech) = M run as PREDICTION with
execution inhibited (imagine: render a plan, no external audio; recognise an imagined trajectory).
EXTERNAL = M executed and GROUNDED against real audio. The falsifiable core: it is the SAME M looped
back, so grounding M through the EXTERNAL loop must improve the INTERNAL (imagined) loop — because they
SHARE the one M (the one inventory of gestural targets theta).

REUSE (no new layer — this is the recurring lesson):
  M               = scripts/dynamic_sequence_speech_abs.render_dynamic (gestural plan -> min-jerk
                    coarticulated trajectory; the held writer-physics motor model) + the held DtwTo Term
                    (scripts/dynamic_sequence_speech_abs.dtw) as the INVERSION/decision (acoustic->plan).
  inventory theta = the per-phone gestural TARGET region (band centroid) + duration. M's only parameter.
                    Both the internal and external loops read the SAME theta = the ONE model.
  GROUNDING       = the agent's HELD collapse cognition. Two faithful reuses, no parallel rule set:
     (1) SYMBOLIC : the held collapse_engine.run_collapse (the DomainPlug loop that move_space, sentences,
                    voice already plug into). Phones are the symbols; real-audio phone-sequences are the
                    targets revealed phone-by-phone; next_dist is the agent's learned transition model with
                    a generalisation prior; a transition the prior mispredicts is a RESIDUAL the manifold
                    cannot collapse -> run_collapse records a GAP and calls on_gap = LEARN it (grow Gamma).
                    Pass 1 localises the gaps (the admissible-transition inventory emerges); pass 2 = 0.
     (2) ACOUSTIC : the held native_collapse cognition (T_SURPRISE = Neg(Log(conf)), evaluated in Rust).
                    predict = render theta via M; surprise = the held native term on the per-phone
                    recognition confidence; construct_gap = refine theta toward the observed frames (a
                    COUNTED running mean = a structural addition toward the observation, grow Gamma; NOT a
                    gradient/loss/.fit) and ADD unseen phones (the inventory emerges + sharpens). Surprise
                    falls toward 0 as theta -> the real acoustic cluster means.

donkey=0: M render = numpy adapter (as in every held AbS script); the DECISION = held DtwTo Term; SURPRISE
= held native term; the collapse loop = held run_collapse; the learning = counted structure-addition. No
LLM, no borrowed net, no gradient. XTTS is NOT used.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

import substrate_rs as _srs
from collapse_engine import DomainPlug, run_collapse
from scripts.native_collapse import native_surprise
from scripts.dynamic_sequence_speech_abs import render_dynamic

# one held substrate for the native SURPRISE term (the cognition runs in Rust).
_S = _srs.Substrate()


# ============================================================================
# (1) SYMBOLIC GROUNDING — the speech DomainPlug into the HELD run_collapse.
#     Mirror of scripts/move_space_collapse_plug.py: predict = manifold collapse,
#     surprise/stuck = the residual GAP the prediction cannot collapse, learn =
#     on_gap growing Gamma. Phones are the opaque symbols.
# ============================================================================

def make_speech_plug(model, utterances, top_phone):
    """A DomainPlug: real-audio phone-sequences revealed phone-by-phone; next_dist is the agent's learned
    phone-transition model, falling back to a GENERALISATION prior (predict the globally-commonest phone)
    where a context is UNLEARNED. A transition the prior mispredicts is a residual the manifold cannot
    collapse -> run_collapse localises a GAP and calls on_gap = count the real transition (grow Gamma).

    `model` is the agent's transition store (a dict, the graph-resident counts); it starts EMPTY and is
    grown by on_gap. `utterances` are the (word, phone-seq) the external loop grounds on."""
    seqs = [tuple(ph) for _w, ph in utterances if len(ph) >= 2]

    def next_dist(ctx):
        if len(ctx) < 1:
            return {}
        b = ctx[-1]
        if b in model and model[b]:                          # LEARNED transition (counts)
            tot = sum(model[b].values())
            return {o: n / tot for o, n in model[b].items()}
        return {top_phone: 1.0}                              # GENERALISATION prior (wrong at most)

    def on_gap(ctx, missing):                                # LEARN: count the real transition (grow Gamma)
        b = ctx[-1]
        model.setdefault(b, {}).setdefault(missing, 0)
        model[b][missing] += 1

    return DomainPlug(name="speech_phones", pool=seqs, train=seqs, targets=seqs,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)


def symbolic_grounding(utterances):
    """Run the HELD collapse loop on real phone-sequences. PASS 1: the generalisation prior mispredicts
    most transitions -> run_collapse records the gaps and on_gap learns them. PASS 2: the model explains
    every transition -> 0 gaps. Returns (gaps_pass1, gaps_pass2, n_transitions_learned)."""
    top_phone = Counter(p for _w, ph in utterances for p in ph).most_common(1)[0][0]
    model = {}
    plug = make_speech_plug(model, utterances, top_phone)
    seq_lp = {s: 0.0 for s in plug.pool}
    r1 = run_collapse(plug, seq_lp)
    learned = sum(len(v) for v in model.values())
    r2 = run_collapse(plug, seq_lp)
    return len(r1.gaps), len(r2.gaps), learned


# ============================================================================
# (2) ACOUSTIC GROUNDING — the HELD native collapse-cognition refines the ONE
#     inventory theta. predict (M) -> surprise (held native term) -> construct_gap
#     (refine theta toward the observed frames = grow Gamma; NOT a gradient).
# ============================================================================

def flatstart_assign(O, ph):
    """Proportional (HMM flat-start) alignment of frames to phones — the same earn-alignment the held
    targets use. Returns the per-frame phone label list."""
    n, P = len(O), len(ph)
    return [ph[int(i * P / n)] for i in range(n)]


def collect_targets_few(words):
    """theta_0: the gestural targets EARNED from a FEW exemplars (poor, possibly missing phones). Same
    earn as dynamic_sequence_speech_abs.collect_targets, kept local so the plug is self-contained."""
    acc = defaultdict(list); dur = defaultdict(list)
    for w, fr, ph in words:
        O = np.asarray(fr, float); assign = flatstart_assign(O, ph)
        for i, p in enumerate(assign):
            acc[p].append(O[i])
        for p, ct in Counter(assign).items():
            dur[p].append(ct)
    theta = {p: np.mean(v, 0) for p, v in acc.items() if v}
    durs = {p: float(np.mean(d)) for p, d in dur.items() if d}
    return theta, durs


def _conf_softmax(obs, theta, phl, p_true, sigma):
    """Per-phone recognition confidence = softmax over the inventory of -||obs - theta[q]||^2 / 2 sigma^2,
    read out at the true phone. This is the manifold confidence (numpy adapter MEASUREMENT, exactly like
    the held AbS scripts compute distances in numpy); the SURPRISE on it is the held native Rust term."""
    d2 = np.array([((obs - theta[q]) ** 2).sum() for q in phl])
    w = np.exp(-(d2 - d2.min()) / (2.0 * sigma * sigma))
    z = w.sum()
    return float(w[phl.index(p_true)] / z) if z > 0 else 0.0


def ground_targets(theta0, durs0, grounding_words, passes=3, sigma=2.0):
    """EXTERNAL acoustic grounding of the ONE inventory through the held collapse cognition.

    For each real utterance: M predicts (theta describes each phone region); per phone the SURPRISE is the
    held native term on the recognition confidence; construct_gap refines theta toward the observed frames
    (counted running mean = structure addition, grow Gamma) and ADDS unseen phones (inventory emerges).

    Returns (theta, durs, surprise_trajectory[list per pass])."""
    theta = {p: v.copy() for p, v in theta0.items()}
    durs = dict(durs0)
    cnt = {p: 1.0 for p in theta}
    traj = []
    for _it in range(passes):
        phl = sorted(theta.keys())
        tot_s, n = 0.0, 0
        for w, fr, ph in grounding_words:
            O = np.asarray(fr, float); assign = flatstart_assign(O, ph)
            by_phone = defaultdict(list)
            for i, p in enumerate(assign):
                by_phone[p].append(O[i])
            for p, frames in by_phone.items():
                obs = np.mean(frames, 0)
                if p not in theta:                            # GROW the inventory: a phone M lacked
                    theta[p] = obs.copy(); cnt[p] = 1.0
                    durs[p] = float(len(frames)); phl = sorted(theta.keys()); continue
                conf = _conf_softmax(obs, theta, phl, p, sigma)
                tot_s += native_surprise(_S, conf); n += 1     # HELD native surprise term
                # construct_gap: refine theta[p] toward the observation (counted mean = grow Gamma)
                theta[p] = (cnt[p] * theta[p] + obs) / (cnt[p] + 1.0); cnt[p] += 1.0
                durs[p] = 0.9 * durs.get(p, len(frames)) + 0.1 * len(frames)
        traj.append(tot_s / max(n, 1))
    return theta, durs, traj
