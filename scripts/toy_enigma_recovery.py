"""toy_enigma_recovery — the TOY-ENIGMA diagnostic-ladder rung.

Drives the structure-recoverer (analysis-by-synthesis + weighted admissibility)
against the toy Enigma forward model. Ground truth KNOWN. Reports recovery
success rate, crib length, and SEARCH COST vs brute force (the Bombe pruning).

Run: PYTHONUNBUFFERED=1 python -m scripts.toy_enigma_recovery
"""
from __future__ import annotations

import os
import sys
import glob
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.toy_enigma import Settings, random_settings, N
from domains.enigma_recoverer import (
    TrigramLM, recover_level1, bombe_test, complete_plugboard, to_idx,
)


def load_corpus() -> str:
    """LibriSpeech dev-clean transcripts = clean uppercase English (train-only)."""
    files = glob.glob("/tmp/LibriSpeech/*/*/*/*.trans.txt")
    chunks = []
    for f in files:
        with open(f) as fh:
            for line in fh:
                # strip the leading utterance id
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    chunks.append(parts[1])
    return " ".join(chunks)


# A held-out plaintext NOT in the LM corpus (so the n-gram isn't scoring its own
# training text). A pangram-style English message.
PLAINTEXTS = [
    "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOGANDRUNSAWAYINTOTHEDARKFOREST",
    "ATTACKATDAWNTHEENEMYPOSITIONNEARTHERIVERWITHALLAVAILABLEFORCES",
    "WEATHERREPORTFORTHEMORNINGCLEARSKIESLIGHTWINDFROMTHENORTHWEST",
    "THEMEETINGWILLTAKEPLACEATNOONINSIDETHEOLDLIBRARYBYTHEMAINHALL",
    "SENDREINFORCEMENTSTOTHESOUTHERNFLANKBEFORETHENEXTSCHEDULEDWAVE",
]


def fmt_sci(x):
    return f"{x:.3e}"


def run_level1_trials(lm, n_trials=8, crib_len=12, seed=42, verbose_first=True):
    rng = random.Random(seed)
    successes = 0
    rows = []
    for t in range(n_trials):
        pt = PLAINTEXTS[t % len(PLAINTEXTS)]
        truth = random_settings(rng, n_plugs=0, ring_zero=True)
        ct = truth.encrypt(pt)
        crib_offset = 0
        crib = pt[:crib_len]
        # sanity: crib must encrypt to the matching ciphertext prefix under truth
        t0 = time.time()
        best, score, n_eval, brute, ranked = recover_level1(
            ct, crib, crib_offset, lm, ring=(0, 0, 0), known_plug="")
        dt = time.time() - t0
        ok_order = best is not None and tuple(best.rotor_order) == tuple(truth.rotor_order)
        ok_start = best is not None and tuple(best.start) == tuple(truth.start)
        ok = ok_order and ok_start
        successes += int(ok)
        rows.append((t, truth, best, score, ok_order, ok_start, n_eval, brute, dt, ranked))
        tag = "OK " if ok else "XX "
        print(f"[L1 trial {t}] {tag} truth: {truth}")
        if best:
            print(f"            recovered: {best}  score={score:.4f}")
        print(f"            order_ok={ok_order} start_ok={ok_start}  "
              f"evaluated={n_eval}/{brute} ({dt:.1f}s)")
        if verbose_first and t == 0:
            print(f"            top-{len(ranked)} candidates by admissibility:")
            for sc, order, start in ranked:
                print(f"               {sc:.4f}  order={'/'.join(order)} start={start}")
    return successes, rows


def run_crib_length_sweep(lm, lengths=(4, 6, 8, 10, 12), n_trials=5, seed=7):
    print("\n=== CRIB-LENGTH SWEEP (Level 1, plug=0) ===")
    out = {}
    for cl in lengths:
        rng = random.Random(seed)
        succ = 0
        for t in range(n_trials):
            pt = PLAINTEXTS[t % len(PLAINTEXTS)]
            truth = random_settings(rng, n_plugs=0, ring_zero=True)
            ct = truth.encrypt(pt)
            crib = pt[:cl]
            best, score, n_eval, brute, ranked = recover_level1(
                ct, crib, 0, lm, ring=(0, 0, 0), known_plug="")
            ok = (best is not None and tuple(best.rotor_order) == tuple(truth.rotor_order)
                  and tuple(best.start) == tuple(truth.start))
            succ += int(ok)
        out[cl] = (succ, n_trials)
        print(f"  crib_len={cl:2d}: {succ}/{n_trials} recovered")
    return out


def run_bombe_crib_curve(lm, n_plugs=3, lengths=(10, 14, 18, 24), seed=321):
    """The Bombe efficiency curve: survivors (after plugboard-independent
    constraint propagation) vs crib length, at the FIXED rotor scope. Shows the
    prune from 105,456 rotor hypotheses down toward 1 as the crib over-determines."""
    print(f"\n=== BOMBE PRUNING CURVE (survivors vs crib length, plug={n_plugs}) ===")
    import itertools
    rng = random.Random(seed)
    pt = PLAINTEXTS[1]
    truth = random_settings(rng, n_plugs=n_plugs, ring_zero=True)
    ct = truth.encrypt(pt)
    rotor_hyps = len(list(itertools.permutations(("I", "II", "III")))) * (N ** 3)
    print(f"  truth: {truth}")
    print(f"  rotor hypotheses (brute, plug-free) = {rotor_hyps:,}")
    rows = []
    for cl in lengths:
        crib = pt[:cl]
        surv = 0
        true_in = False
        for order in itertools.permutations(("I", "II", "III")):
            for s0 in range(N):
                for s1 in range(N):
                    for s2 in range(N):
                        ok, plug, br, co = bombe_test(order, (0, 0, 0),
                                                      (s0, s1, s2), crib, ct, 0)
                        if ok:
                            surv += 1
                            if (order == truth.rotor_order
                                    and (s0, s1, s2) == truth.start):
                                true_in = True
        prune = rotor_hyps / max(1, surv)
        rows.append((cl, surv, true_in, prune))
        print(f"  crib_len={cl:2d}: survivors={surv:6d}  true_in={true_in}  "
              f"prune={prune:.1f}x  ({rotor_hyps:,} -> {surv})")
    return rows


def run_level2_bombe(lm, n_trials=6, n_plugs=3, crib_len=18, seed=123):
    """LEVEL 2: recover plugboard + rotors via the Bombe constraint propagation.

    For tractability we test the Bombe's PLUGBOARD-INDEPENDENT pruning directly:
    over the rotor hypotheses, the Bombe either (a) finds a self-consistent
    steckering => candidate survives + plug recovered, or (b) every branch
    contradicts => the whole rotor hypothesis (and its ~C(26,...) plugboards) is
    rejected in bulk. We measure how many rotor hypotheses survive (the prune)."""
    print(f"\n=== LEVEL 2: BOMBE (plug={n_plugs} pairs, crib_len={crib_len}) ===")
    rng = random.Random(seed)
    import itertools
    rotor_pool = ("I", "II", "III")
    successes = 0
    rows = []
    for t in range(n_trials):
        pt = PLAINTEXTS[t % len(PLAINTEXTS)]
        truth = random_settings(rng, n_plugs=n_plugs, ring_zero=True)
        ct = truth.encrypt(pt)
        crib = pt[:crib_len]
        crib_offset = 0

        # Brute-force baseline size for this scope (rotor orders x starts x plugboards)
        from math import comb, factorial
        n_plug_space = 1
        avail = N
        for i in range(n_plugs):
            n_plug_space *= comb(avail, 2)
            avail -= 2
        n_plug_space //= factorial(n_plugs)  # unordered disjoint pairs
        brute_full = len(list(itertools.permutations(rotor_pool))) * (N ** 3) * n_plug_space

        # The Bombe: iterate rotor hypotheses; bombe_test prunes plugboard-free.
        t0 = time.time()
        survivors = []
        rotor_hyps = 0
        for order in itertools.permutations(rotor_pool):
            for s0 in range(N):
                for s1 in range(N):
                    for s2 in range(N):
                        rotor_hyps += 1
                        ok, plug, branches, contra = bombe_test(
                            order, (0, 0, 0), (s0, s1, s2), crib, ct, crib_offset)
                        if ok:
                            survivors.append((order, (s0, s1, s2), plug))
        dt = time.time() - t0

        # Among survivors, pick the one whose full decrypt (with recovered plug) is
        # most admissible (n-gram) — the weighted-admissibility tie-break. Then
        # COMPLETE the plugboard (crib only forces plug letters it exercises) by the
        # same n-gram admissibility selector (the 'finish the Steckerbrett' step).
        best = None; best_sc = -1e18
        for order, start, plug in survivors:
            full_plug = complete_plugboard(order, (0, 0, 0), start, ct, lm, plug)
            cand = Settings(order, (0, 0, 0), start, full_plug)
            dec = cand.encrypt(ct)
            sc = lm.logprob(to_idx(dec))
            if sc > best_sc:
                best_sc = sc; best = cand

        ok_order = best and tuple(best.rotor_order) == tuple(truth.rotor_order)
        ok_start = best and tuple(best.start) == tuple(truth.start)
        # plug correctness: same set of pairs
        def plugset(s):
            return set(frozenset(tok) for tok in s.split())
        ok_plug = best and plugset(best.plug) == plugset(truth.plug)
        ok = ok_order and ok_start and ok_plug
        successes += int(ok)
        rotor_brute = len(list(itertools.permutations(rotor_pool))) * (N ** 3)
        prune = brute_full / max(1, len(survivors))
        rows.append((t, truth, best, len(survivors), rotor_hyps, brute_full, prune, dt))
        tag = "OK " if ok else "XX "
        print(f"[L2 trial {t}] {tag} truth: {truth}")
        if best:
            print(f"            recovered: {best}  (ngram={best_sc:.4f})")
        print(f"            order_ok={ok_order} start_ok={ok_start} plug_ok={ok_plug}")
        print(f"            rotor_hyps_tested={rotor_hyps}  survivors={len(survivors)}  "
              f"({dt:.1f}s)")
        print(f"            brute_full(rotor x start x plug)={fmt_sci(brute_full)}  "
              f"=> prune_to_survivors ~ {fmt_sci(prune)}x")
    return successes, rows


def main():
    print("=" * 72)
    print("TOY-ENIGMA STRUCTURE-RECOVERY — analysis-by-synthesis + weighted admissibility")
    print("=" * 72)

    # --- world: train the trigram LM (train-only corpus) ---
    print("\n[corpus] loading LibriSpeech dev-clean transcripts (English, train-only)...")
    corpus = load_corpus()
    lm = TrigramLM(k=0.1)
    lm.train(corpus)
    print(f"[corpus] trained trigram LM on {lm.trained_chars:,} letters; "
          f"{len(lm.tri):,} distinct trigrams")

    # --- config / search-space statement ---
    import itertools
    n_orders = len(list(itertools.permutations(("I", "II", "III"))))
    print("\n[config] 3-rotor Enigma, alphabet A..Z (N=26), reflector B (no fixed point)")
    print(f"[config] rotor wirings = historical Enigma I (I/II/III), ring=AAA (start-only)")
    print(f"[search] rotor orders = {n_orders};  start positions = 26^3 = {N**3:,}")
    print(f"[search] Level-1 feasible set = {n_orders} x 26^3 = {n_orders*N**3:,}")
    from math import comb
    print(f"[search] plugboard p=3 pairs = {comb(26,2)*comb(24,2)*comb(22,2)//6:,}")
    print(f"[search] full key space (order x start x plug=3) ~ "
          f"{fmt_sci(n_orders*N**3*comb(26,2)*comb(24,2)*comb(22,2)//6)}")

    # --- LEVEL 1 ---
    print("\n" + "=" * 72)
    print("LEVEL 1 — rotor order + start positions (plugboard = 0)")
    print("=" * 72)
    succ1, rows1 = run_level1_trials(lm, n_trials=8, crib_len=12)
    print(f"\n[L1 RESULT] recovery success: {succ1}/8 trials "
          f"(rotor order + all 3 start positions EXACT)")

    # crib-length sweep
    sweep = run_crib_length_sweep(lm, lengths=(4, 6, 8, 10, 12), n_trials=5)

    # --- LEVEL 2 ---
    print("\n" + "=" * 72)
    print("LEVEL 2 — plugboard via the BOMBE (constraint propagation)")
    print("=" * 72)
    # First: the pruning curve (survivors vs crib length) — the Bombe efficiency.
    curve = run_bombe_crib_curve(lm, n_plugs=3, lengths=(10, 14, 18, 24))
    # Then: full recovery trials at the convergence crib length.
    succ2, rows2 = run_level2_bombe(lm, n_trials=6, n_plugs=3, crib_len=18)
    print(f"\n[L2 RESULT] recovery success: {succ2}/6 trials "
          f"(rotor + start + plugboard pairs EXACT)")

    # --- summary ---
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Level 1 (rotors+start, plug=0): {succ1}/8 exact")
    print(f"Level 2 (rotors+start+plug=3, Bombe): {succ2}/6 exact")
    print("Crib-length sweep (L1):", {k: f"{v[0]}/{v[1]}" for k, v in sweep.items()})

    print("\nTOY-ENIGMA-RECOVERY COMPLETED")


if __name__ == "__main__":
    main()
