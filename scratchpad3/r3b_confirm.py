"""RUNG 3B CONFIRMATORY RUN. Exactly the three pre-registered tests, on fresh
seeds 6000+, bistable=1. Run ONCE. No sweeps, no re-runs.

Parallel across seeds ONLY (each seed is an independent boot with its own RNG;
the SEED is the unit of analysis, PROTOCOL section 4). Parallelism cannot change
a number: every arm of a seed is computed in one worker from that seed alone."""
import numpy as np, sys, json, os
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, ".")
from scratchpad3.r3b_lib import run, signflip, VIDEO32, ARMS

N = int(sys.argv[1]); BI_ETA = float(sys.argv[2])
SEEDS = list(range(6000, 6000 + N))
_V = None

def _seed_row(seed):
    global _V
    if _V is None:
        _V = np.load(VIDEO32)
    return seed, {a: run(a, seed, _V, bistable=1.0, bi_eta=BI_ETA) for a in ARMS}

if __name__ == "__main__":
    R = {a: [] for a in ARMS}
    with ProcessPoolExecutor(max_workers=int(os.environ.get("NW", "10"))) as ex:
        for seed, row in ex.map(_seed_row, SEEDS):
            for a in ARMS:
                R[a].append(row[a])
            print(f"  seed {seed} done", flush=True)
    R = {a: np.array(x) for a, x in R.items()}
    rng = np.random.default_rng(31337)
    out = {}
    print(f"\nRUNG 3B CONFIRMATORY  n={N}  seeds {SEEDS[0]}-{SEEDS[-1]}  bi_eta={BI_ETA:g}\n")
    for key, nm, d in (("H1a", "d_normal  (normal - dark)", R["normal"] - R["dark"]),
                       ("H1b", "d_dark    (dark - untrained)", R["dark"] - R["untrained"]),
                       ("H1c", "d_strobe  (normal - strobe)", R["normal"] - R["strobe"])):
        obs, p, lo, hi = signflip(d, rng)
        out[key] = dict(obs=float(obs), p=float(p), lo=float(lo), hi=float(hi),
                        pct=float(100 * obs / 0.489))
        print(f"{key} {nm:28s} {obs:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  p={p:.4f}"
              f"   ({100*obs/0.489:+.1f}% of range)")
    print()
    for a in ARMS:
        print(f"  arm {a:10s} mean DSI {R[a].mean():+.4f}")
    print(f"\n  strobe - untrained = {(R['strobe']-R['untrained']).mean():+.4f}"
          "   (the dissolution diagnostic the untrained arm exists for)")
    h1a = out["H1a"]["obs"] > 0 and out["H1a"]["p"] < 0.0167
    h1b = out["H1b"]["lo"] > -0.049 and out["H1b"]["hi"] < 0.049
    h1c = out["H1c"]["obs"] > 0 and out["H1c"]["p"] < 0.0167
    print(f"\n  H1a (experience produces direction)    : {'PASS' if h1a else 'FAIL'}")
    print(f"  H1b (waves do NOT, equivalence +-0.049) : {'PASS' if h1b else 'FAIL'}")
    print(f"  H1c (motion, not spatial structure)     : {'PASS' if h1c else 'FAIL'}")
    print(f"\n  DECISION: RUNG 3B {'BUILT' if (h1a and h1b and h1c) else 'NOT BUILT'}")
    out["arms"] = {a: float(R[a].mean()) for a in ARMS}
    json.dump(out, open("results/r3b_confirm.json", "w"), indent=1)
