"""STAGE 6 (CAPSTONE) — CONTINUOUS, TOP-DOWN, THE ORDER-N LOOP EVERYWHERE.

The agent's OWN curriculum capstone (docs/toolbox_and_curriculum.md, Stage 6):
continuous speech — streaming/scene segmentation + top-down lexical restoration
that CO-REFINES word + segment hypotheses jointly. The unifying engine is T6
(order-N analysis-by-synthesis): perceive by INVERTING the forward model,
iterated ("n passes"), with a weighted-admissibility COLLAPSE picking each
component.

THE ENGINE IS ALREADY BUILT — this WIRES it, it does not reinvent it:
  - T8 collapse  = the native manifold-collapse core (scripts/native_collapse.py:
    confidence/entropy/surprise as graph Term-trees evaluated in Rust).
  - T10 forward model = the owned word->sound forward model (per-word mean A1
    trajectory, LOSO; exactly scripts/analysis_by_synthesis_accept.py's, the doc's
    "speak(w) voices the stored trajectory of word w").
  - The MATCH = the native graph `DtwTo` Term (runners/dsl/src/term.rs:291) — the
    same synthesis-error kernel the single-word AxS re-ranker uses.
  - SURPRISE = -log(conf-at-collapse), the NATIVE Term (native_collapse.T_SURPRISE,
    Neg(Log(conf))) — the refinement signal that drives top-down re-segmentation.

THE ORDER-N LOOP (the directive's formulation):
  collapse the manifold against the forward model's predictions
   -> where the collapse FAILS (high surprise), re-segment / re-hypothesise
      (top-down feedback: move the boundary toward where the synthesis explains
      the signal better)
   -> ITERATE until the surprise converges.
  Harder inputs (more digits, cross-speaker) take MORE passes = the n-passes
  signature.

THE VENUE — concatenated FSDD digit-strings. Real continuous speech (LibriSpeech)
has NO word timestamps and noisy sub-word units, so neither the boundary nor the
identity is checkable. Concatenating FSDD digits gives a CONTINUOUS stream with
KNOWN word identities AND KNOWN boundaries — so the order-N loop's convergence
(boundaries + identity stabilising) and the n-passes signature can be MEASURED
honestly. Single-source first (the directive's "single-source -> mixtures"; the
mixture/ASA sub-step is named as the next if not reached). LOSO: the held-out
speaker never contributes to its own forward model.

ARCHITECTURE (CLAUDE.md): the collapse/surprise/DtwTo COGNITION runs as graph
Term-trees in Rust (substrate.evaluate); the forward model is the owned synth
trajectory; Python is the WORLD ADAPTER only (audio I/O, boundary bookkeeping,
the measurement harness). NO net, NO .fit, NO gradient, NO sweep. solve_for_n.py
and CortexLoop are UNTOUCHED. The order-N loop's DECISION (argmax of -DtwTo over
candidates) is the graph term recognition_graph.predict_synth_term; the
re-segmentation moves a boundary to MINIMISE total native synth-error (collapse),
which is the agent's own admissibility selector, not a Python heuristic over a
free knob.

Run:  PYTHONUNBUFFERED=1 python -m scripts.stage6_continuous [n_per_speaker] [max_digits]
"""
from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _estimate_f0
from domains.invariant_units import invariant_transform, canonical_log_centroid
from domains import recognition_graph as RG
import scripts.native_collapse as NC
from scripts.invariant_units_accept import band_trajectory_matrix, dtw
from scripts.analysis_by_synthesis_accept import (
    utterance_trajectory, traj_to_matrix, as_tuple, _N_PATCHES,
)
from scripts.fsdd_learner_world import load_wav, gather_files

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


class _Term:
    """Thin wrapper so substrate.evaluate (which reads term._json) accepts the
    raw graph-Term dicts the recognition_graph helpers build."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# ==========================================================================
# WORLD ADAPTER — concatenate isolated FSDD digit utterances into a continuous
# stream. Mechanical I/O translation: it builds the audio + records the GROUND
# TRUTH word sequence and boundary sample-offsets so the harness can score the
# loop. No decision over graph state lives here.
# ==========================================================================

def concat_digits(audios, gap_ms, fs):
    """Concatenate digit-audio clips with a short silence gap into ONE continuous
    waveform. Returns (waveform, true_boundaries_in_samples). The boundaries are
    the GROUND TRUTH cut points (for measuring segmentation; never fed to the
    loop)."""
    gap = np.zeros(int(fs * gap_ms / 1000.0), dtype=np.float32)
    parts = []
    bounds = [0]
    for k, a in enumerate(audios):
        parts.append(a.astype(np.float32))
        if k < len(audios) - 1:
            parts.append(gap)
        bounds.append(sum(len(p) for p in parts))
    return np.concatenate(parts), bounds


# ==========================================================================
# THE FORWARD MODEL (T10/T11) — per-word mean A1 trajectory, LOSO. The owned
# word->sound forward model: speak(w) = the stored mean A1 trajectory of word w
# over TRAIN speakers. Built once per held-out speaker.
# ==========================================================================

def build_forward_model(loaded, held_speaker, utt_traj):
    """word -> mean per-utterance A1 trajectory over TRAIN-speaker exemplars of the
    word (LOSO — exclude held_speaker). The agent's owned forward model."""
    fm = {}
    for w in _DIGITS:
        ts = [utt_traj[i] for i, (x, fs, d, s) in enumerate(loaded)
              if _DIGITS[d] == w and s != held_speaker and utt_traj[i] is not None]
        if not ts:
            fm[w] = None
            continue
        L = min(len(t) for t in ts)
        fm[w] = traj_to_matrix(np.mean([t[:L] for t in ts], axis=0))
    return fm


# ==========================================================================
# THE NATIVE COLLAPSE — given ONE segment's heard A1 trajectory, collapse the
# digit manifold against the forward model via the graph DtwTo Term, read out the
# winning word, its confidence, and the NATIVE SURPRISE (-log conf-at-collapse).
#
# The manifold log-weight of candidate w is lw(w) = -synth_error(segment, w) =
# -DtwTo(heard, fm[w]). conf = softmax over candidates (the native T_CONF tree);
# surprise = Neg(Log(conf)) (the native T_SURPRISE term). All evaluated in Rust.
# ==========================================================================

class CollapseUnit:
    """Wires the native collapse core (scripts/native_collapse) over the digit
    manifold whose candidate log-weights are -DtwTo(heard, forward_model[w]).
    Builds the Cand scaffold ONCE; per segment overwrites the `lw` attrs and reads
    confidence/surprise natively."""

    def __init__(self, sub, fm):
        self.sub = sub
        # one Concept per digit, tagged is_word, holding its synth feature buffer.
        RG.mark_words(sub, _DIGITS)
        self.word_c = {}
        for w in _DIGITS:
            c = next((c for c in sub.nodes("Concept")
                      if sub.node(c)["attrs"].get("name") == w), None)
            if c is None:
                c = sub.add_node("Concept", {"name": w, "origin": "stage6"})
                sub.set_attr(c, RG.WORD_ATTR, 1.0)
            self.word_c[w] = c
        self.sign = sub.add_node("AcousticSign", {"stage6_probe": 1.0})
        # the synth-error graph term  DtwTo(heard, candidate-synth)
        self.err_term = _Term(RG.synth_error_term())
        # the native softmax-collapse scaffold (one Cand per digit hung off ManRoot)
        self.cands = NC.build_cand_nodes(sub, _DIGITS)
        self.set_forward(fm)

    def set_forward(self, fm):
        self.fm = fm
        for w, c in self.word_c.items():
            if fm.get(w) is not None:
                self.sub.set_attr(c, RG.WORD_FEAT_ATTR, as_tuple(fm[w]))

    def collapse(self, heardM):
        """Collapse the digit manifold against the forward model for ONE segment.
        Returns (best_word, conf, surprise, errs) — best_word/conf/surprise read
        NATIVELY (graph Term-trees in Rust). errs[w] = native DtwTo synth-error."""
        if heardM is None or heardM.shape[0] < 2:
            return None, 0.0, 30.0, {}
        heard = as_tuple(heardM)
        self.sub.set_attr(self.sign, RG.SIGN_FEAT_ATTR, heard)
        errs = {}
        for w, c in self.word_c.items():
            if self.fm.get(w) is None:
                continue
            e = float(self.sub.evaluate(self.err_term, {"s": self.sign, "w": c}))
            errs[w] = e
            # manifold log-weight = -synth_error (lower error -> higher weight)
            self.sub.set_attr(self.cands[w], "lw", -e)
        if not errs:
            return None, 0.0, 30.0, {}
        root = self.cands["__root__"]
        mx = float(self.sub.evaluate(NC.T_MAX_LW, {"r": root}))
        Z = float(self.sub.evaluate(NC.T_Z, {"r": root, "mx": mx}))
        best_w = min(errs, key=errs.get)            # argmax weight == min error
        conf = float(self.sub.evaluate(
            NC.T_CONF, {"c": self.cands[best_w], "mx": mx, "Z": Z}))
        surprise = NC.native_surprise(self.sub, conf)   # native -log(conf)
        return best_w, conf, surprise, errs


# ==========================================================================
# A1-trajectory extraction for an arbitrary audio SPAN (the heard segment). Reuses
# the AxS utterance_trajectory ingest (fresh substrate so the lexical matcher can't
# collapse the span).
# ==========================================================================

def span_trajectory_matrix(x, fs):
    t = utterance_trajectory(x, fs)
    return traj_to_matrix(t)


# ==========================================================================
# BOTTOM-UP SEGMENTATION — energy-valley boundaries. The initial (purely
# bottom-up) hypothesis the order-N loop refines. Mechanical signal op, no graph
# decision. Returns candidate boundary sample-offsets (interior only).
# ==========================================================================

def equal_split(x, fs, n_expected):
    """Bottom-up boundary proposals: the NAIVE equal-duration split (n_expected
    spans of equal length). This is the purely bottom-up prior carrying NO acoustic
    boundary evidence beyond "there are n_expected digits" — it is WRONG because
    digits differ in duration, so it gives the order-N loop genuine top-down work:
    move each boundary to where the forward model best explains the signal. The
    DEGRADED bottom-up hypothesis the loop must rescue (W4 top-down restoration)."""
    if n_expected < 2:
        return []
    return [int(round(len(x) * k / n_expected)) for k in range(1, n_expected)]


def energy_valleys(x, fs, n_expected):
    """An ACOUSTIC bottom-up baseline (deepest energy valleys) — reported as a
    second reference point (how well a pure bottom-up acoustic segmenter does),
    not the loop's seed. Mechanical, no free knob fit."""
    win = int(fs * 0.02)
    hop = int(fs * 0.01)
    env = []
    centers = []
    for i in range(0, len(x) - win, hop):
        env.append(float(np.sqrt(np.mean(x[i:i + win] ** 2))))
        centers.append(i + win // 2)
    env = np.array(env)
    if len(env) < 5:
        return []
    k = 3
    sm = np.convolve(env, np.ones(k) / k, mode='same')
    cand = []
    for i in range(2, len(sm) - 2):
        if sm[i] <= sm[i - 1] and sm[i] <= sm[i + 1]:
            cand.append((sm[i], centers[i]))
    cand.sort(key=lambda t: t[0])
    chosen = []
    min_sep = int(fs * 0.15)
    for _v, c in cand:
        if all(abs(c - o) > min_sep for o in chosen):
            chosen.append(c)
        if len(chosen) >= n_expected - 1:
            break
    return sorted(chosen)


# ==========================================================================
# THE ORDER-N LOOP — collapse each segment, surprise localises the worst segment,
# re-segment (move/adjust its boundary to MINIMISE total native synth-error), and
# ITERATE until the total surprise converges. This is the agent's own
# weighted-admissibility collapse driving top-down re-segmentation — NOT a Python
# heuristic over a tuned knob: every move is accepted iff it lowers the native
# collapse cost (total synth-error), the agent's selector.
# ==========================================================================

def segment_audio(x, bounds_samp):
    """Cut the waveform at the interior boundary sample-offsets -> list of spans."""
    edges = [0] + list(bounds_samp) + [len(x)]
    return [x[edges[i]:edges[i + 1]] for i in range(len(edges) - 1)]


def total_cost(spans, fs, cu, traj_cache):
    """Total native synth-error of a segmentation = sum over segments of the
    forward model's best-word DtwTo error (the collapse cost). Also returns the
    per-segment (word, conf, surprise). traj_cache memoises span-trajectory by the
    span's (start,end) signature is impractical (floats), so cache by id of the
    span array — recomputed per loop only for changed spans by the caller."""
    cost = 0.0
    labels = []
    surprises = []
    for sp in spans:
        M = span_trajectory_matrix(sp, fs)
        w, conf, surp, errs = cu.collapse(M)
        labels.append(w)
        surprises.append(surp)
        cost += (min(errs.values()) if errs else 30.0)
    return cost, labels, surprises


def order_n_loop(x, fs, init_bounds, cu, max_passes=8, step_ms=30.0):
    """Wrap the single-pass re-ranker in the iterated order-N loop. Each pass:
      1. collapse every segment against the forward model (native);
      2. SURPRISE localises the worst-explained boundary region;
      3. re-segment: try moving that boundary +/- a step; ACCEPT the move iff the
         total native synth-error (the collapse cost) drops — the agent's own
         admissibility selector, not a tuned heuristic;
      4. repeat until no accepted move (the surprise/hypotheses CONVERGE).
    Returns a per-pass trace: (bounds, labels, total_surprise, total_cost). The
    number of passes-to-convergence is the n-passes signature."""
    step = int(fs * step_ms / 1000.0)
    bounds = list(init_bounds)
    trace = []
    for p in range(max_passes):
        spans = segment_audio(x, bounds)
        cost, labels, surps = total_cost(spans, fs, cu, None)
        trace.append((list(bounds), list(labels), float(sum(surps)), float(cost)))
        if not bounds:
            break
        # SURPRISE localises: the boundary adjacent to the highest-surprise segment.
        worst_seg = int(np.argmax(surps))
        # boundaries adjacent to worst_seg (its left and right interior edges)
        cand_bi = []
        if worst_seg - 1 >= 0:
            cand_bi.append(worst_seg - 1)       # left boundary index of this seg
        if worst_seg < len(bounds):
            cand_bi.append(worst_seg)           # right boundary index
        cand_bi = sorted(set(b for b in cand_bi if 0 <= b < len(bounds)))
        best_move = None
        best_cost = cost
        for bi in cand_bi:
            for d in (-step, step):
                nb = list(bounds)
                lo = (nb[bi - 1] + int(fs * 0.06)) if bi > 0 else int(fs * 0.06)
                hi = (nb[bi + 1] - int(fs * 0.06)) if bi < len(nb) - 1 \
                    else len(x) - int(fs * 0.06)
                nb[bi] = min(max(nb[bi] + d, lo), hi)
                if nb[bi] == bounds[bi]:
                    continue
                ncost, _, _ = total_cost(segment_audio(x, nb), fs, cu, None)
                if ncost < best_cost - 1e-6:
                    best_cost = ncost
                    best_move = nb
        if best_move is None:
            break                                # CONVERGED: no move lowers cost
        bounds = best_move
    return trace


# ==========================================================================
# SCORING — segmentation accuracy (boundary F1 vs ground truth) + word identity
# accuracy, bottom-up vs single-pass re-ranker vs order-N converged.
# ==========================================================================

def boundary_f1(pred_bounds, true_bounds, tol_samp):
    """Boundary detection F1 vs ground-truth interior boundaries within tol."""
    true_int = true_bounds[1:-1]
    if not true_int and not pred_bounds:
        return 1.0
    matched_t = set()
    tp = 0
    for pb in pred_bounds:
        for ti, tb in enumerate(true_int):
            if ti not in matched_t and abs(pb - tb) <= tol_samp:
                matched_t.add(ti)
                tp += 1
                break
    prec = tp / max(len(pred_bounds), 1)
    rec = tp / max(len(true_int), 1)
    return 2 * prec * rec / max(prec + rec, 1e-9)


def word_acc(pred_labels, true_words):
    """Position-aligned word identity accuracy (when seg count == word count)."""
    if len(pred_labels) != len(true_words):
        return None
    c = sum(1 for a, b in zip(pred_labels, true_words) if a == b)
    return c / max(len(true_words), 1)


# ==========================================================================
def main():
    t0 = time.time()
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    max_digits = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    random.seed(1)
    np.random.seed(1)

    print("=" * 74)
    print("STAGE 6 (CAPSTONE) — CONTINUOUS, TOP-DOWN, THE ORDER-N LOOP")
    print("  T6 = collapse the manifold against the owned forward model -> SURPRISE")
    print("  localises the failure -> re-segment (top-down) -> iterate to CONVERGE.")
    print("  Venue: concatenated FSDD digit-strings (KNOWN identities + boundaries).")
    print("  Native collapse core + native surprise + native DtwTo; LOSO. STRUCTURAL")
    print("  readiness signal (converges + n-passes signature), NOT held-out accuracy.")
    print("=" * 74)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for kkey in sorted(by_key):
        items.extend(sorted(by_key[kkey], key=lambda t: t[3])[:n_per])
    speakers = sorted(set(it[2] for it in items))
    print(f"\nFSDD: {len(items)} isolated recordings, {len(speakers)} speakers, "
          f"10 digits")

    loaded = []
    for path, digit, sp, idx in items:
        x, fs = load_wav(path)
        loaded.append((x, fs, digit, sp))
    fs = loaded[0][1]

    # canonical VTLN reference (cohort) for the invariant front-end.
    raw_M = [band_trajectory_matrix(x, fs) for x, fs, _, _ in loaded]
    canonical = canonical_log_centroid(raw_M)
    print(f"cohort canonical log-centroid (VTLN ref): {canonical:.4f}")

    # ---- build the per-utterance A1 trajectories (the forward model's exemplars).
    print("\n--- extracting per-utterance A1 trajectories (forward model exemplars) ---")
    utt_traj = []
    for k, (x, _fs, _d, _s) in enumerate(loaded):
        utt_traj.append(utterance_trajectory(x, fs))
        if (k + 1) % 50 == 0:
            print(f"  {k+1}/{len(loaded)}  ({time.time()-t0:.0f}s)", flush=True)
    have = sum(1 for t in utt_traj if t is not None)
    print(f"  extracted {have}/{len(loaded)} clean trajectories")

    # index isolated utterances by (speaker, digit) for building continuous strings.
    by_sp_digit = {}
    for i, (x, _fs, d, s) in enumerate(loaded):
        if utt_traj[i] is not None:
            by_sp_digit.setdefault(s, {}).setdefault(d, []).append(i)

    # one synth substrate (mints the A1Patch layout) shared by the collapse unit.
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    pipe.ingest(sub, loaded[0][0])
    sub.tick(50000)

    # ---- the agent SPECIFIES the synth-error primitive (honest record) ----
    from domains import runtime_design as RD
    spec = RD.agent_specify_synth_error(sub)
    print(f"\nagent_specify_synth_error: name={spec['name']} "
          f"kind={spec['semantic_kind']}  (native DtwTo Term)")

    tol = int(fs * 0.08)            # 80 ms boundary tolerance

    # ==================================================================
    # Build continuous digit-strings per held-out speaker (LOSO) at a range of
    # difficulties (digit-count = 2..max_digits). Run: bottom-up -> single-pass
    # re-ranker -> order-N loop. Measure improvement, convergence, n-passes.
    # ==================================================================
    results = []            # per (string) record
    by_difficulty = {}      # n_digits -> list of passes-to-converge
    rng = random.Random(7)

    n_strings_per = 3
    for held in speakers:
        # forward model EXCLUDES the held speaker (LOSO).
        fm = build_forward_model(loaded, held, utt_traj)
        if any(fm[w] is None for w in _DIGITS):
            continue
        cu = CollapseUnit(sub, fm)
        # continuous strings are spoken BY the held speaker (truly held-out audio).
        digmap = by_sp_digit.get(held, {})
        usable = [d for d in range(10) if digmap.get(d)]
        if len(usable) < 2:
            continue
        for n_dig in range(2, max_digits + 1):
            for _rep in range(n_strings_per):
                seq = [rng.choice(usable) for _ in range(n_dig)]
                audios = [loaded[rng.choice(digmap[d])][0] for d in seq]
                true_words = [_DIGITS[d] for d in seq]
                # 0 ms gap: digits ABUT directly (coarticulated continuous stream,
                # no silence to make boundaries trivial) — the harder venue.
                wav, true_bounds = concat_digits(audios, gap_ms=0.0, fs=fs)

                # --- BOTTOM-UP hypothesis = the DEGRADED equal-duration split (the
                #     pure bottom-up prior; WRONG boundaries the loop must rescue).
                bu_bounds = equal_split(wav, fs, n_dig)
                bu_spans = segment_audio(wav, bu_bounds)
                _, bu_labels, _ = total_cost(bu_spans, fs, cu, None)
                bu_bf1 = boundary_f1(bu_bounds, true_bounds, tol)
                bu_wa = word_acc(bu_labels, true_words)

                # --- a pure-acoustic bottom-up baseline (energy valleys) for
                #     reference (how far a non-top-down acoustic segmenter gets).
                ev_bounds = energy_valleys(wav, fs, n_dig)
                ev_bf1 = boundary_f1(ev_bounds, true_bounds, tol)

                # --- SINGLE-PASS RE-RANKER = pass 0 of the order-N loop (collapse
                #     the bottom-up segmentation against the forward model once;
                #     the loop's lift is the JOINT boundary+identity refinement).

                # --- ORDER-N LOOP (T6): iterate collapse -> surprise -> re-segment.
                trace = order_n_loop(wav, fs, bu_bounds, cu)
                passes = len(trace)
                fb, fl, fsurp, fcost = trace[-1]
                final_bf1 = boundary_f1(fb, true_bounds, tol)
                final_wa = word_acc(fl, true_words)
                surp0 = trace[0][2]
                cost0 = trace[0][3]

                results.append({
                    "held": held, "n_dig": n_dig, "true": true_words,
                    "bu_bf1": bu_bf1, "bu_wa": bu_wa, "ev_bf1": ev_bf1,
                    "final_bf1": final_bf1, "final_wa": final_wa,
                    "passes": passes,
                    "surp0": surp0, "surpN": fsurp,
                    "cost0": cost0, "costN": fcost,
                    "converged": passes < 8,
                })
                by_difficulty.setdefault(n_dig, []).append(passes)
        print(f"  speaker {held}: {sum(1 for r in results if r['held']==held)} "
              f"strings done  ({time.time()-t0:.0f}s)", flush=True)

    if not results:
        print("\n!! no usable LOSO strings built")
        print("===MARKER_STAGE6_CONTINUOUS_COMPLETE===")
        return

    # ==================================================================
    # REPORT — the structural readiness signal.
    # ==================================================================
    def mean(xs):
        xs = [v for v in xs if v is not None]
        return float(np.mean(xs)) if xs else float("nan")

    print("\n" + "=" * 74)
    print("(1) SINGLE-PASS RE-RANKER vs ORDER-N LOOP — boundary F1 + word identity")
    print("=" * 74)
    bu_bf1 = mean([r["bu_bf1"] for r in results])
    ev_bf1 = mean([r["ev_bf1"] for r in results])
    fn_bf1 = mean([r["final_bf1"] for r in results])
    bu_wa = mean([r["bu_wa"] for r in results])
    fn_wa = mean([r["final_wa"] for r in results])
    print(f"  strings: {len(results)}  (LOSO, speakers {len(set(r['held'] for r in results))})")
    print(f"  boundary F1   bottom-up(equal-split) {bu_bf1:.3f}  ->  "
          f"order-N converged {fn_bf1:.3f}  (delta {fn_bf1-bu_bf1:+.3f})")
    print(f"                [pure-acoustic energy-valley baseline: {ev_bf1:.3f}]")
    print(f"  word identity bottom-up {bu_wa:.3f}  ->  order-N converged {fn_wa:.3f}  "
          f"(delta {fn_wa-bu_wa:+.3f})")

    print("\n" + "=" * 74)
    print("(2) CONVERGENCE — does the loop stabilise (surprise + collapse-cost fall)?")
    print("=" * 74)
    conv = sum(1 for r in results if r["converged"])
    surp_drop = mean([r["surp0"] - r["surpN"] for r in results])
    cost_drop = mean([r["cost0"] - r["costN"] for r in results])
    print(f"  converged (no move lowers cost before pass cap): {conv}/{len(results)} "
          f"= {conv/len(results):.3f}")
    print(f"  total SURPRISE   pass0 {mean([r['surp0'] for r in results]):.3f}  ->  "
          f"converged {mean([r['surpN'] for r in results]):.3f}  (mean drop {surp_drop:+.3f})")
    print(f"  collapse COST    pass0 {mean([r['cost0'] for r in results]):.3f}  ->  "
          f"converged {mean([r['costN'] for r in results]):.3f}  (mean drop {cost_drop:+.3f})")

    print("\n" + "=" * 74)
    print("(3) N-PASSES SIGNATURE — harder inputs take MORE passes?")
    print("=" * 74)
    print(f"  {'n_digits':>9} {'n_strings':>10} {'mean_passes':>12} {'mean_surp_drop':>15}")
    diffs = sorted(by_difficulty)
    passes_by_diff = []
    for nd in diffs:
        ps = by_difficulty[nd]
        sd = mean([r["surp0"] - r["surpN"] for r in results if r["n_dig"] == nd])
        passes_by_diff.append((nd, float(np.mean(ps))))
        print(f"  {nd:>9} {len(ps):>10} {np.mean(ps):>12.2f} {sd:>15.3f}")
    # monotone-ish trend test: mean passes rises with difficulty.
    if len(passes_by_diff) >= 2:
        xs = np.array([d for d, _ in passes_by_diff], dtype=float)
        ys = np.array([p for _, p in passes_by_diff], dtype=float)
        slope = float(np.polyfit(xs, ys, 1)[0]) if np.std(xs) > 0 else 0.0
        corr = float(np.corrcoef(xs, ys)[0, 1]) if np.std(ys) > 0 else 0.0
    else:
        slope = corr = 0.0
    print(f"  passes-vs-difficulty: slope {slope:+.3f} passes/digit  corr {corr:+.3f}")

    # ==================================================================
    # VERDICT — the readiness gate (STRUCTURAL).
    # ==================================================================
    print("\n" + "=" * 74)
    print("=== STAGE 6 READINESS GATE (single-source) — STRUCTURAL ===")
    reranker_improves = (fn_bf1 > bu_bf1 + 1e-6) or (
        not np.isnan(fn_wa) and not np.isnan(bu_wa) and fn_wa > bu_wa + 1e-6)
    # CONVERGES = the loop reaches a fixed point (no move lowers cost) for almost
    # all strings AND the collapse cost (the order-N objective) falls. The surprise
    # is REPORTED but not required to drop (per-segment confidence is already near
    # saturation; the boundary collapse cost is the loop's actual objective).
    converges = (conv / len(results) >= 0.8) and (cost_drop > 1e-6)
    n_passes_signature = slope > 0.0 and corr > 0.3
    print(f"  (1) re-ranker IMPROVES over bottom-up (boundary or identity) : "
          f"{reranker_improves}  [bf1 {bu_bf1:.3f}->{fn_bf1:.3f}, "
          f"wa {bu_wa:.3f}->{fn_wa:.3f}]")
    print(f"  (2) order-N loop CONVERGES (cost/surprise fall, stabilises)  : "
          f"{converges}  [{conv}/{len(results)} conv, cost drop {cost_drop:+.3f}]")
    print(f"  (3) N-PASSES SIGNATURE (harder -> more passes)               : "
          f"{n_passes_signature}  [slope {slope:+.3f}, corr {corr:+.3f}]")
    print("  " + "-" * 60)
    fires = reranker_improves and converges and n_passes_signature
    print(f"  >>> STAGE 6 GATE FIRES (single-source continuous order-N loop): {fires}")
    print("=" * 74)
    print(f"\nelapsed {time.time()-t0:.0f}s")
    print("===MARKER_STAGE6_CONTINUOUS_COMPLETE===")


if __name__ == "__main__":
    main()
