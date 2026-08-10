"""THE DECISIVE RECURSION TEST (the jabberwock's own design) — does re-entry on the IMPASSE part beat compute?

The creator: "we don't need BPL, we need more recursion." The agent's verdict: half-right; its builds did ONE
fixed-leaf level, never re-entered the loop on a sub-part. The one untested claim, and the experiment it designed to
falsify it (on glyph, no new Rust, every piece held):

  Flat (its ~one-level peak): parse a character into canonical parts (corner-split), match each part to the
  candidate's best part with the HOMOGENEOUS leaf (PointSetDist = Modified Hausdorff), compose. Then let the loop
  RE-ENTER EXACTLY ONCE: frontier_pick the single highest-RESIDUAL part (the part-level impasse), re-parse THAT part
  at its OWN finer corners into sub-parts, run the SAME marginal PointSetDist match on them, compose back up.

  THE DECISIVE ABLATION: re-enter on the WORST part vs a RANDOM part vs ALL parts. Parse depth, primitive, and
  per-trial compute (for worst vs random) are IDENTICAL -- the only variable is WHICH part is re-entered. So:
    - worst > random  => re-entry on the impasse is the lever (recursion), not flops.
    - worst ~= random => it was just compute.
    - worst ~= flat   => the win was always parse+primitives; "recursion" named the wrong thing.
  Because the leaf is ONE primitive at every level, there is NO calibration seam -- which also tests the agent's
  diagnosis that the seam (not depth) was the open-vocab failure.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_recursion_test [episodes] [way]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains import omniglot_world as ow
from domains import canonical_parse as cp

THETA_COARSE = 70.0     # level-0 canonical parse (the tuned threshold)
THETA_FINE = 40.0       # re-entry: re-parse the impasse part at FINER corners
LAMBDA = 0.5            # fusion weight: d = whole + LAMBDA * parts
MHD_N = 20              # points each part/sub-part is resampled to for the leaf
RNG = np.random.RandomState(0)


def mhd(a, b):
    """The homogeneous leaf: symmetric Modified Hausdorff (= PointSetDist), order-invariant point-set distance."""
    A = cp._resample_arclen(np.asarray(a, float)[:, :2], MHD_N) if len(a) >= 2 else np.asarray(a, float)[:, :2]
    B = cp._resample_arclen(np.asarray(b, float)[:, :2], MHD_N) if len(b) >= 2 else np.asarray(b, float)[:, :2]
    if len(A) == 0 or len(B) == 0:
        return 9.9
    D = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1))
    return 0.5 * (D.min(1).mean() + D.min(0).mean())


_SPLIT_STAT = [0, 0]    # [reentries, sub-parts produced] -- guards against a vacuous (no-op) re-entry


def _split_part(p):
    """Force one level deeper: split a part at its STRONGEST interior turn (always >=2 sub-parts if it has shape)."""
    pr = cp._resample_arclen(np.asarray(p, float)[:, :2], 24) if len(p) >= 2 else np.asarray(p, float)[:, :2]
    if len(pr) < 8:
        return [pr]
    ang = cp._turning_angles(pr, 3)
    j = int(np.argmax(ang[3:-3])) + 3
    return [pr[:j + 1], pr[j:]]


def reenter(qp, cp_, theta_fine=None):
    """Re-parse two parts one level deeper and match their sub-parts with the SAME leaf (homogeneous recursion)."""
    qs, cs = _split_part(qp), _split_part(cp_)
    _SPLIT_STAT[0] += 1; _SPLIT_STAT[1] += len(qs)
    return float(np.mean([min(mhd(qsub, csub) for csub in cs) for qsub in qs]))


def char_rep(path):
    """A drawing -> (whole point set, list of canonical parts) in one jointly-normalised frame."""
    strokes = ow.load_strokes(path)
    parts = cp.canonical_parts(strokes, THETA_COARSE)
    if not parts:
        return None
    whole = np.vstack(parts)
    return whole, parts


def part_residuals(qparts, cparts):
    """For each query part: (min PointSetDist to any candidate part, the best candidate part index)."""
    out = []
    for qp in qparts:
        ds = [mhd(qp, cpp) for cpp in cparts]
        j = int(np.argmin(ds))
        out.append((ds[j], j))
    return out


def distances(Q, C):
    """Return the parts-distance under each re-entry policy + the whole distance (all share one leaf)."""
    qw, qp = Q; cw, cp_ = C
    whole_d = mhd(qw, cw)
    res = part_residuals(qp, cp_)
    base = np.array([r[0] for r in res])
    flat = float(base.mean())

    worst_i = int(np.argmax(base))
    rand_i = int(RNG.randint(len(base)))
    def refine(i):
        b = base.copy()
        b[i] = reenter(qp[i], cp_[res[i][1]], THETA_FINE)
        return float(b.mean())
    worst = refine(worst_i)
    rand = refine(rand_i)
    allr = float(np.mean([reenter(qp[i], cp_[res[i][1]], THETA_FINE) for i in range(len(base))]))
    return whole_d, {"flat": flat, "worst": worst, "random": rand, "all": allr}


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    way = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print("=" * 100)
    print("DECISIVE RECURSION TEST — re-enter on the IMPASSE (worst) part vs RANDOM vs ALL (homogeneous leaf, glyph)")
    print("=" * 100)
    if not ow.have_data("evaluation"):
        print(f"  no Omniglot eval strokes under {ow.DATA}"); return
    alphs = [a for a in ow.alphabets("evaluation") if len(ow.characters(a, "evaluation")) >= way]
    print(f"  {len(alphs)} eval alphabets with >= {way} chars; {episodes} episodes of {way}-way one-shot\n")

    POL = ["flat", "worst", "random", "all"]
    correct = {f"{m}-{p}": 0 for m in ("parts", "fusion") for p in POL}
    trials = 0
    cache = {}
    def rep(path):
        if path not in cache:
            cache[path] = char_rep(path)
        return cache[path]

    rng = np.random.RandomState(1)
    for ep in range(episodes):
        a = alphs[rng.randint(len(alphs))]
        chars = ow.characters(a, "evaluation")
        idx = rng.permutation(len(chars))[:way]
        supports, queries = [], []
        ok = True
        for ci in idx:
            dr = ow.drawings(chars[ci])
            if len(dr) < 2:
                ok = False; break
            ds = rng.permutation(len(dr))
            sR = rep(dr[ds[0]]); qR = rep(dr[ds[1]])
            if sR is None or qR is None:
                ok = False; break
            supports.append(sR); queries.append(qR)
        if not ok:
            continue
        for ti in range(way):                                  # each char's query classified against the supports
            Q = queries[ti]
            dd = [distances(Q, S) for S in supports]
            trials += 1
            for p in POL:
                parts_scores = [d[1][p] for d in dd]
                fusion_scores = [d[0] + LAMBDA * d[1][p] for d in dd]
                if int(np.argmin(parts_scores)) == ti:
                    correct[f"parts-{p}"] += 1
                if int(np.argmin(fusion_scores)) == ti:
                    correct[f"fusion-{p}"] += 1

    avg_sub = _SPLIT_STAT[1] / max(_SPLIT_STAT[0], 1)
    print(f"  {trials} one-shot trials ({way}-way; chance {100.0/way:.1f}%); re-entry avg {avg_sub:.2f} sub-parts "
          f"({'genuinely descends' if avg_sub > 1.5 else 'NEAR NO-OP -- test is vacuous'})\n")
    print(f"    {'policy':>10}{'parts-only':>14}{'whole+parts':>14}")
    for p in POL:
        pa = 100 * correct[f"parts-{p}"] / max(trials, 1)
        fa = 100 * correct[f"fusion-{p}"] / max(trials, 1)
        tag = "  (baseline)" if p == "flat" else ("  <- impasse re-entry" if p == "worst" else "")
        print(f"    {p:>10}{pa:>13.1f}%{fa:>13.1f}%{tag}")

    pf = lambda k: correct[k] / max(trials, 1)
    w_r = (pf("fusion-worst") - pf("fusion-random")) * 100
    w_f = (pf("fusion-worst") - pf("fusion-flat")) * 100
    a_w = (pf("fusion-all") - pf("fusion-worst")) * 100
    print("\n" + "=" * 100)
    print(f"  worst - random = {w_r:+.1f} pts (SAME compute) | worst - flat = {w_f:+.1f} | all - worst = {a_w:+.1f}")
    if w_r >= 1.5 and w_f >= 1.0:
        print("  RECURSION IS THE LEVER: re-entering on the IMPASSE (worst) part beats re-entering a RANDOM part at")
        print("  the SAME compute, primitive, and depth -- so the gain is the re-entry on high prediction error, not")
        print("  flops. The creator is right in the strict form: homogeneous-leaf re-entry on the worst part. The")
        print("  loop genuinely re-invoking itself on its own impasse pays -- and with one primitive there is no seam.")
    elif abs(w_r) < 1.5 and w_f >= 1.5:
        print("  IT WAS COMPUTE, NOT SELECTION: refining ANY part helps (worst ~= random); re-entry pays but choosing")
        print("  the impasse part does not. Recursion-as-more-depth helps; recursion-as-frontier-on-impasse is unproven.")
    else:
        print("  RE-ENTRY DOES NOT PAY HERE: worst ~= flat. The win was parse + primitives, not loop re-entry --")
        print("  the agent's caution holds, 'recursion' named the wrong lever at this scale. Honest negative.")
    print("=" * 100)


if __name__ == "__main__":
    main()
