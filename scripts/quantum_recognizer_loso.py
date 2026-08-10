"""quantum_recognizer_loso — apply the "a postulate is a quantum state" framework
(ozma_postulate_is_a_quantum_state / ozma_collapse_is_gamma_application) to the EAR:
a QUANTUM-PROBABILITY recognizer tested against the CLASSICAL combines that hit the
cross-speaker LOSO wall (FLAT 0.323, EXCLUSION 0.228, VECTOR 0.305 on the full
10-digit set — commit 54fd606b).

THE CLAIM: the classical combines are ALL commutative (order-blind) and
interference-free (sum/product of paths). Recognition might instead carry
QUANTUM-PROBABILITY structure: candidate words = a SUPERPOSITION (complex amplitude
vector psi); each cue = a MEASUREMENT operator that collapses the state; cues apply
SEQUENTIALLY (can FAIL TO COMMUTE); outcome = Born rule |amplitude|^2 with
INTERFERENCE cross-terms the classical product cannot have. The operator + phase are
DERIVED from the cue's own distances (no fit/net/searched param) — see
domains/many_settings_recognizer.cue_amplitude / cue_operator / quantum_recognize.

THE THREE TESTS (robust SC 40-speaker LOSO, ungameable; held-out NEVER banked; same
banks/channels/features as the classical runs — only the COMBINE differs):
  (1) ACCURACY: does the quantum combine beat FLAT 0.323 / VECTOR 0.305 on the full
      10-digit AND the fricative set? Ladder vs FLAT / EXCLUSION / VECTOR.
  (2) ORDER EFFECTS: apply the cues in several orders — does the result depend on
      order (non-commutativity)? Spread across orders (classical = exactly zero).
  (3) INTERFERENCE: is |psi|^2 different from the no-phase product? Compare
      quantum-with-phase vs quantum-with-phase-ZEROED (phi=0). Quantify how much
      the cross-terms move the accuracy and the per-query distribution.

PREDICTION / KILL: if quantum BEATS classical AND shows order-effects + interference,
recognition has quantum-probability structure the classical combine couldn't hold. If
it does NOT beat classical and commutes/sums (no interference), the residual is pure
perception (the feature wall, already confirmed at 54fd606b) and the quantum framing
buys nothing HERE — say so plainly, do NOT rescue.

DONKEY BOUNDARY (audited): amplitudes / projectors / Born = the agent's composable
linear algebra (owned ops; NO fit, NO net, NO searched param — phase DERIVED from the
cue's signed margin, beta a fixed structural 1/2). Cues = the agent's existing
features (the SAME COCHLEA / SHARP-HF / MANNER-VOICE / FRIC-VOICE channels). Held-out
speakers NEVER banked; LOSO ungameable.

Run: python -m scripts.quantum_recognizer_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import itertools
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# reuse the classical harness VERBATIM: split, extract, channels, classical combines.
from scripts.combined_pool_loso import (
    CHANNELS, DIGITS, FRIC_WORDS, build_split, extract_all,
    run_combined, _confusion, LIKELIHOOD)
from scripts.sibilant_sharp_ear import SC_DIR, NATIVE_FS, WORLD_FS
from domains.many_settings_recognizer import (
    channel_likelihood, channel_likelihood_exclusion,
    channel_vector, combine_vectors,
    cue_amplitude, quantum_recognize, _Q_BETA, _Q_PHI)

# the cue pool — the SAME channels the classical combine uses, fused.
POOL = ["COCHLEA", "SHARP-HF", "MANNER-VOICE", "FRIC-VOICE"]


# ---------------------------------------------------------------------------
# CLASSICAL combines (reused) — argmax over the classical product / exclusion / vector.
# ---------------------------------------------------------------------------

def classical_guess(qi, chan_names, trf, trw, prf, cand, like_fn):
    prod = {w: 1.0 for w in cand}
    for name in chan_names:
        p = like_fn(np.asarray(prf[name][qi]), trf[name], trw, cand)
        for w in cand:
            prod[w] *= p[w]
    return max(prod.items(), key=lambda kv: kv[1])[0] if prod else None


def vector_guess(qi, chan_names, trf, trw, prf, cand):
    vecs = [channel_vector(np.asarray(prf[name][qi]), trf[name], trw, cand)
            for name in chan_names]
    score = combine_vectors(vecs, cand)
    return max(score.items(), key=lambda kv: kv[1])[0] if score else None


def run_classical(chan_names, trf, trw, prf, prw, words, like_fn):
    cand = sorted(set(trw))
    guesses = [classical_guess(qi, chan_names, trf, trw, prf, cand, like_fn)
               for qi in range(len(prw))]
    return _confusion(guesses, prw, words)


def run_vector(chan_names, trf, trw, prf, prw, words):
    cand = sorted(set(trw))
    guesses = [vector_guess(qi, chan_names, trf, trw, prf, cand)
               for qi in range(len(prw))]
    return _confusion(guesses, prw, words)


# ---------------------------------------------------------------------------
# QUANTUM combine — superpose -> sequential measurement -> Born readout.
# ---------------------------------------------------------------------------

def quantum_guess(qi, chan_order, trf, trw, prf, cand, beta, phi):
    """Born argmax: apply the cue operators in chan_order to the uniform superposition.
    Each cue's complex amplitude e_c is DERIVED from its own 1-NN distances + signed
    margin (cue_amplitude). phi=0 zeroes the phase (interference OFF control)."""
    amps = [cue_amplitude(np.asarray(prf[name][qi]), trf[name], trw, cand, phi=phi)
            for name in chan_order]
    born = quantum_recognize(amps, cand, beta=beta)
    return max(born.items(), key=lambda kv: kv[1])[0] if born else None


def run_quantum(chan_order, trf, trw, prf, prw, words, beta=_Q_BETA, phi=_Q_PHI):
    cand = sorted(set(trw))
    guesses = [quantum_guess(qi, chan_order, trf, trw, prf, cand, beta, phi)
               for qi in range(len(prw))]
    return _confusion(guesses, prw, words)


def quantum_born_matrix(chan_order, trf, trw, prf, prw, cand, beta, phi):
    """Born distribution per query (n_probe x n_cand) — for the interference probe
    (compare distributions phase-on vs phase-off, not just the argmax)."""
    out = np.zeros((len(prw), len(cand)), dtype=np.float64)
    for qi in range(len(prw)):
        amps = [cue_amplitude(np.asarray(prf[name][qi]), trf[name], trw, cand, phi=phi)
                for name in chan_order]
        born = quantum_recognize(amps, cand, beta=beta)
        out[qi] = np.array([born[w] for w in cand])
    return out


# ===========================================================================
# THE THREE TESTS, run on one (fricative or 10-digit) feature bank.
# ===========================================================================

def run_suite(tag, words, trf, trw, prf, prw):
    cand = sorted(set(trw))
    chance = 1.0 / len(words)
    print("\n" + "=" * 78, flush=True)
    print(f"SUITE {tag}: words={words}  chance {chance:.3f}", flush=True)
    print("=" * 78, flush=True)

    # ---- CLASSICAL baselines (the wall) on the SAME pool ----
    flat_acc, _ = run_classical(POOL, trf, trw, prf, prw, words, channel_likelihood)
    excl_acc, _ = run_classical(POOL, trf, trw, prf, prw, words, channel_likelihood_exclusion)
    vec_acc, _ = run_vector(POOL, trf, trw, prf, prw, words)
    print(f"  CLASSICAL on the same pool: FLAT {flat_acc:.3f}  EXCLUSION {excl_acc:.3f}  "
          f"VECTOR {vec_acc:.3f}", flush=True)

    # ---- TEST 1: ACCURACY — quantum (canonical order, full phase) ----
    q_acc, q_conf = run_quantum(POOL, trf, trw, prf, prw, words, beta=_Q_BETA, phi=_Q_PHI)
    print(f"  QUANTUM (pool order, beta={_Q_BETA}, phi=pi/2): {q_acc:.3f}  "
          f"(vs FLAT {q_acc - flat_acc:+.3f}, vs VECTOR {q_acc - vec_acc:+.3f})", flush=True)

    # ---- TEST 2: ORDER EFFECTS — several cue orders ----
    # all permutations if few cues, else a sampled set; classical product = zero spread.
    perms = list(itertools.permutations(POOL))
    rng = random.Random(0)
    rng.shuffle(perms)
    perms = perms[:8]
    order_accs = []
    print("  ORDER EFFECTS (quantum accuracy under different cue orders):", flush=True)
    for order in perms:
        acc, _ = run_quantum(list(order), trf, trw, prf, prw, words, beta=_Q_BETA, phi=_Q_PHI)
        order_accs.append(acc)
        print(f"    {' -> '.join(o[:5] for o in order):42s}  {acc:.3f}", flush=True)
    order_spread = max(order_accs) - min(order_accs)
    # per-query order disagreement: fraction of probes whose Born-argmax CHANGES with order.
    g_by_order = []
    for order in perms:
        gs = [quantum_guess(qi, list(order), trf, trw, prf, cand, _Q_BETA, _Q_PHI)
              for qi in range(len(prw))]
        g_by_order.append(gs)
    disagree = sum(1 for qi in range(len(prw))
                   if len({g[qi] for g in g_by_order}) > 1) / max(len(prw), 1)
    print(f"    => order spread (max-min acc) {order_spread:.3f} over {len(perms)} orders; "
          f"per-query argmax changes with order on {disagree:.1%} of probes "
          f"(classical = exactly 0)", flush=True)

    # ---- TEST 3: INTERFERENCE — phase-ON vs phase-OFF (phi=0) ----
    qoff_acc, _ = run_quantum(POOL, trf, trw, prf, prw, words, beta=_Q_BETA, phi=0.0)
    # distribution-level: how much do the Born probabilities move when phase is on?
    born_on = quantum_born_matrix(POOL, trf, trw, prf, prw, cand, _Q_BETA, _Q_PHI)
    born_off = quantum_born_matrix(POOL, trf, trw, prf, prw, cand, _Q_BETA, 0.0)
    l1 = float(np.abs(born_on - born_off).sum(axis=1).mean())   # mean per-query L1 shift
    argmax_flip = float(np.mean(born_on.argmax(1) != born_off.argmax(1)))
    print(f"  INTERFERENCE (phase-ON vs phase-OFF phi=0):", flush=True)
    print(f"    accuracy phase-ON {q_acc:.3f}  vs  phase-OFF {qoff_acc:.3f}  "
          f"({q_acc - qoff_acc:+.3f})", flush=True)
    print(f"    mean per-query Born-distribution L1 shift {l1:.3f} (0 = no interference); "
          f"argmax flips on {argmax_flip:.1%} of probes", flush=True)

    return {
        "flat": flat_acc, "excl": excl_acc, "vector": vec_acc,
        "quantum": q_acc, "quantum_nophase": qoff_acc,
        "order_spread": order_spread, "order_disagree": disagree,
        "interf_l1": l1, "interf_argmax_flip": argmax_flip,
        "best_order_acc": max(order_accs), "worst_order_acc": min(order_accs),
    }


def main():
    if not os.path.isdir(SC_DIR):
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240609

    print("=" * 78, flush=True)
    print("QUANTUM-PROBABILITY RECOGNIZER vs the classical combines (cross-speaker LOSO)",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  config: {n_train_spk} train / {n_held_spk} held-out speakers, {n_per}/word, "
          f"seed {seed}", flush=True)
    print(f"  audio: native {NATIVE_FS} Hz (sharp ear + manner reach the full band); "
          f"cochlea downsamples to {WORLD_FS} Hz", flush=True)
    print(f"  cue pool: {POOL}   beta={_Q_BETA} (structural), phi=pi/2 (derived unit)",
          flush=True)
    print("  donkey audit: amplitudes/projectors/Born = owned linear algebra; phase "
          "derived from the cue's signed margin; NO fit/net/searched param.", flush=True)

    # EXTRACT ONCE — fricative + 10-digit banks, shared with the classical combine.
    print("\n[extract] fricative banks ...", flush=True)
    trA, loA = build_split(FRIC_WORDS, n_train_spk, n_held_spk, n_per, seed)
    trfA, trwA = extract_all(trA)
    prfA, prwA = extract_all(loA)
    print("[extract] 10-digit banks ...", flush=True)
    trB, loB = build_split(DIGITS, n_train_spk, n_held_spk, n_per, seed)
    trfB, trwB = extract_all(trB)
    prfB, prwB = extract_all(loB)

    rA = run_suite("A (fricative set)", FRIC_WORDS, trfA, trwA, prfA, prwA)
    rB = run_suite("B (full 10-digit)", DIGITS, trfB, trwB, prfB, prwB)

    # ---- THE VERDICT ----
    print("\n" + "=" * 78, flush=True)
    print("VERDICT — does QUANTUM beat classical AND show order-effects + interference?",
          flush=True)
    print("=" * 78, flush=True)
    for tag, r in [("A fricative", rA), ("B 10-digit", rB)]:
        print(f"\n  [{tag}]", flush=True)
        print(f"    accuracy:  FLAT {r['flat']:.3f}  EXCL {r['excl']:.3f}  "
              f"VECTOR {r['vector']:.3f}  ->  QUANTUM {r['quantum']:.3f}  "
              f"(vs FLAT {r['quantum'] - r['flat']:+.3f}, vs VECTOR "
              f"{r['quantum'] - r['vector']:+.3f})", flush=True)
        print(f"    order effects: spread {r['order_spread']:.3f}, argmax changes on "
              f"{r['order_disagree']:.1%} of probes  "
              f"({'PRESENT' if r['order_spread'] > 1e-9 or r['order_disagree'] > 0 else 'NONE (commutes)'})",
              flush=True)
        print(f"    interference: phase-ON {r['quantum']:.3f} vs phase-OFF "
              f"{r['quantum_nophase']:.3f} ({r['quantum'] - r['quantum_nophase']:+.3f}); "
              f"Born L1 shift {r['interf_l1']:.3f}, argmax flips {r['interf_argmax_flip']:.1%}  "
              f"({'PRESENT' if r['interf_l1'] > 1e-6 else 'NONE'})", flush=True)

    # decisive numbers = the full 10-digit set (the headline wall).
    beats_flat = rB["quantum"] > rB["flat"] + 1e-9
    beats_vector = rB["quantum"] > rB["vector"] + 1e-9
    has_order = rB["order_spread"] > 1e-9 or rB["order_disagree"] > 0
    has_interf = rB["interf_l1"] > 1e-6
    print("\n  => 10-digit decisive: ", end="", flush=True)
    if beats_flat and beats_vector and has_order and has_interf:
        print(f"QUANTUM STRUCTURE CONFIRMED — quantum {rB['quantum']:.3f} beats FLAT "
              f"{rB['flat']:.3f} and VECTOR {rB['vector']:.3f}, WITH order-effects "
              f"(spread {rB['order_spread']:.3f}) and interference (L1 {rB['interf_l1']:.3f}). "
              "Recognition carries quantum-probability structure the classical combine "
              "could not hold.", flush=True)
    else:
        why = []
        if not (beats_flat and beats_vector):
            why.append(f"quantum {rB['quantum']:.3f} does NOT beat classical "
                       f"(FLAT {rB['flat']:.3f}, VECTOR {rB['vector']:.3f})")
        if not has_order:
            why.append("no order effects (commutes)")
        if not has_interf:
            why.append("no interference")
        print("QUANTUM FRAMING BUYS NOTHING HERE — " + "; ".join(why) + ". "
              + ("The machinery DOES show order-effects/interference "
                 f"(spread {rB['order_spread']:.3f}, L1 {rB['interf_l1']:.3f}) but does not "
                 "lift accuracy — " if (has_order or has_interf) else "")
              + "the residual is PURE PERCEPTION (the cross-speaker feature wall, "
              "confirmed at 54fd606b), not the combine. Reported plainly, NOT rescued.",
              flush=True)

    print("\n[MARKER] QUANTUM_RECOGNIZER_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
