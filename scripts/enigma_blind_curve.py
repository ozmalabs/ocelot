"""enigma_blind_curve — the HEADLINE experiment for the full-Enigma blind attack.

Full 3-rotor (historical I/II/III) + FULL 10-pair plugboard. Ciphertext-only
(blind) recovery via IoC rotor search + quadgram plugboard hill-climbing with
multi-start basin-hopping escape. Produces the N-vs-success curve + wall-clock
+ local-optima stall/rescue rate.

TRAIN / TEST DISJOINT: the quadgram LM is trained on Jane Austen (Emma +
Persuasion + Sense & Sensibility). The TEST plaintexts are drawn from DIFFERENT
authors (Shakespeare, Carroll, Milton, Chesterton) so the n-gram model never saw
the test text — a genuinely blind, disjoint-corpus evaluation.

Run:  OMP_NUM_THREADS=1 python3 scripts/enigma_blind_curve.py
Honest: reports where it works, where it fails, and the wall-clock per length.
"""
from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.toy_enigma import random_settings, Settings
from domains.enigma_blind import QuadgramLM, recover_blind, grade
from nltk.corpus import gutenberg


def clean(text: str) -> str:
    return "".join(c for c in text.upper() if "A" <= c <= "Z")


def build_lm() -> QuadgramLM:
    lm = QuadgramLM()
    for f in ("austen-emma.txt", "austen-persuasion.txt", "austen-sense.txt"):
        lm.train(gutenberg.raw(f))
    lm.finalize()
    return lm


# test plaintext pool — DISJOINT authors from the Austen training set
TEST_FILES = [
    "shakespeare-hamlet.txt", "shakespeare-macbeth.txt", "shakespeare-caesar.txt",
    "carroll-alice.txt", "milton-paradise.txt", "chesterton-thursday.txt",
    "chesterton-ball.txt", "bryant-stories.txt",
]


def test_pool() -> str:
    return "  ".join(clean(gutenberg.raw(f)) for f in TEST_FILES)


def run_curve(lengths, trials, topk_ioc, n_starts, max_pairs=10,
              n_plugs=10, seed0=1000):
    lm = build_lm()
    pool = test_pool()
    print(f"[lm] trained_chars={lm.trained_chars} quadgrams={len(lm.counts)} "
          f"(train: Austen)  test pool chars={len(pool)} (disjoint authors)")
    print(f"[cfg] full plugboard n_plugs={n_plugs}  topk_ioc={topk_ioc}  "
          f"n_starts={n_starts}  max_pairs={max_pairs}  trials/len={trials}")
    print(f"[search-space] rotor 6*26^3=105456  x plugboard(10)=1.5e14  "
          f"=> ~1.6e19 keys (ring fixed AAA)")
    sys.stdout.flush()

    results = {}
    for L in lengths:
        n_full = n_rotor = 0
        recalls = []
        precisions = []
        times = []
        rescues_tot = stalls_tot = 0
        for t in range(trials):
            rng = random.Random(seed0 + L * 31 + t)
            s = random_settings(rng, n_plugs=n_plugs, ring_zero=True)
            # pick a random disjoint window of the test pool
            start_off = rng.randrange(0, len(pool) - L - 1)
            pt = pool[start_off:start_off + L]
            ct = s.encrypt(pt)
            t0 = time.time()
            res = recover_blind(ct, lm, topk_ioc=topk_ioc, sharpen_pairs=4,
                                topk_rotor=12, max_pairs=max_pairs,
                                n_starts=n_starts, rng=random.Random(seed0 + t))
            dt = time.time() - t0
            rotor_ok, start_ok, recall, precision, full_ok = grade(s, res["best"])
            rs = rotor_ok and start_ok
            n_full += int(full_ok)
            n_rotor += int(rs)
            recalls.append(recall)
            precisions.append(precision)
            times.append(dt)
            rescues_tot += res["total_rescues"]
            stalls_tot += res["stalls"]
            print(f"  L={L:5d} trial={t} time={dt:5.1f}s rotor+pos={rs} "
                  f"plug_recall={recall:.2f} full={full_ok} "
                  f"rescues={res['total_rescues']} B-evals={res['stage_b_evals']}")
            sys.stdout.flush()
        avg_t = sum(times) / len(times)
        avg_recall = sum(recalls) / len(recalls)
        avg_prec = sum(precisions) / len(precisions)
        results[L] = dict(full=n_full, rotor=n_rotor, trials=trials,
                          avg_time=avg_t, avg_recall=avg_recall,
                          avg_prec=avg_prec, rescues=rescues_tot, stalls=stalls_tot)
        print(f"[SUMMARY L={L}] rotor+pos={n_rotor}/{trials} "
              f"full(rotor+pos+ALL plugs)={n_full}/{trials} "
              f"avg_plug_recall={avg_recall:.2f} avg_plug_prec={avg_prec:.2f} "
              f"avg_time={avg_t:.1f}s rescues={rescues_tot} stalls={stalls_tot}")
        sys.stdout.flush()

    print("\n==================== N-vs-SUCCESS CURVE ====================")
    print(f"{'len':>6} {'rotor+pos':>10} {'full':>8} {'plug_recall':>12} "
          f"{'avg_time(s)':>12} {'rescues':>8} {'stalls':>7}")
    for L in lengths:
        r = results[L]
        print(f"{L:>6} {r['rotor']}/{r['trials']:<8} {r['full']}/{r['trials']:<5} "
              f"{r['avg_recall']:>12.2f} {r['avg_time']:>12.1f} "
              f"{r['rescues']:>8} {r['stalls']:>7}")
    return results


if __name__ == "__main__":
    import platform
    print("CPU:", platform.processor() or "unknown")
    try:
        with open("/proc/cpuinfo") as fh:
            for line in fh:
                if line.startswith("model name"):
                    print("CPU model:", line.split(":", 1)[1].strip())
                    break
    except Exception:
        pass

    # lengths + trials chosen so the whole run completes in a sane wall-clock
    LENGTHS = [int(x) for x in os.environ.get("LENGTHS", "200,400,800,1600,3200").split(",")]
    TRIALS = int(os.environ.get("TRIALS", "5"))
    TOPK_IOC = int(os.environ.get("TOPK_IOC", "400"))
    N_STARTS = int(os.environ.get("N_STARTS", "5"))
    t0 = time.time()
    run_curve(LENGTHS, TRIALS, TOPK_IOC, N_STARTS)
    print(f"\nTOTAL WALL-CLOCK: {time.time()-t0:.1f}s")
    print("RUN_COMPLETED_MARKER")
