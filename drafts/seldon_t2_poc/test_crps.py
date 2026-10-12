"""
Correctness gate for the CRPS implementation. Run directly:

    python3 drafts/seldon_t2_poc/test_crps.py

No pytest dependency (keeps the PoC self-contained and avoids the repo's
conftest machinery). Prints PASS/FAIL per check and exits non-zero on any
failure so the end-to-end runner can trust the numbers downstream.

Checks:
  1. Point mass CRPS == |m - y|                       (MAE reduction case)
  2. crps_stepped agrees with crps_energy to ~machine precision (mutual check)
  3. Two-point analytic case worked out by hand
  4. Symmetric distribution + symmetric y offset gives equal CRPS
  5. Adding mass exactly at y never increases CRPS (sharper = better here)
  6. CRPS of a sample matches a brute-force numerical integral of the CDF
  7. Known closed form: uniform-on-{ -1,0,1 } vs y=0
"""

from __future__ import annotations

import numpy as np

from crps import crps_stepped, crps_energy, crps_sample, crps_point


def _brute_force_crps(values, masses, y, lo=None, hi=None, n=2_000_00):
    """Numerically integrate (F(x)-1{x>=y})^2 dx on a fine grid as ground truth."""
    v = np.asarray(values, float)
    p = np.asarray(masses, float)
    p = p / p.sum()
    order = np.argsort(v)
    v, p = v[order], p[order]
    cdf_levels = np.cumsum(p)
    if lo is None:
        lo = min(v.min(), y) - 5.0
    if hi is None:
        hi = max(v.max(), y) + 5.0
    xs = np.linspace(lo, hi, n)
    # F(x): right-continuous step
    idx = np.searchsorted(v, xs, side="right") - 1
    F = np.where(idx >= 0, cdf_levels[np.clip(idx, 0, len(v) - 1)], 0.0)
    ind = (xs >= y).astype(float)
    integrand = (F - ind) ** 2
    return np.trapezoid(integrand, xs)


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail else ""))
    return cond


def main():
    ok = True
    rng = np.random.default_rng(0)
    print("CRPS correctness gate")

    # 1. Point mass == |m - y|
    for m, y in [(3.0, 5.0), (-2.0, -2.0), (0.0, 7.5)]:
        got = crps_stepped([m], [1.0], y)
        want = crps_point(m, y)
        ok &= check(f"point mass at {m} vs y={y}: CRPS={got:.6f} == |m-y|={want:.6f}",
                    abs(got - want) < 1e-9)

    # 2. stepped vs energy identity across random discrete distributions
    max_err = 0.0
    for _ in range(200):
        k = rng.integers(1, 8)
        vals = rng.normal(size=k) * 5
        mass = rng.random(size=k) + 1e-3
        y = float(rng.normal() * 5)
        a = crps_stepped(vals, mass, y)
        b = crps_energy(vals, mass, y)
        max_err = max(max_err, abs(a - b))
    ok &= check("stepped == energy identity (200 random discrete dists)",
                max_err < 1e-9, f"max abs diff = {max_err:.2e}")

    # 3. Two-point analytic case:
    # support {0,1}, mass {0.5,0.5}, y=0.
    # F(x)=0 for x<0; 0.5 for 0<=x<1; 1 for x>=1.
    # integrand (F-1{x>=0})^2: on [0,1) F=0.5, indicator=1 -> 0.25, width 1 -> 0.25
    #                          on [1,inf) F=1, indicator=1 -> 0. left tail 0.
    got = crps_stepped([0.0, 1.0], [0.5, 0.5], 0.0)
    ok &= check("two-point {0,1}@0.5 vs y=0: CRPS == 0.25",
                abs(got - 0.25) < 1e-9, f"got {got:.6f}")

    # 4. symmetry: dist symmetric about 0, y=+d and y=-d give equal CRPS
    vals = [-2.0, 0.0, 2.0]
    mass = [0.25, 0.5, 0.25]
    c_plus = crps_stepped(vals, mass, 1.3)
    c_minus = crps_stepped(vals, mass, -1.3)
    ok &= check("symmetry: CRPS(y=+1.3) == CRPS(y=-1.3)",
                abs(c_plus - c_minus) < 1e-9, f"{c_plus:.6f} vs {c_minus:.6f}")

    # 5. sharper-at-truth never worse: move mass toward y=0
    diffuse = crps_stepped([-3, 0, 3], [1/3, 1/3, 1/3], 0.0)
    sharp = crps_stepped([-3, 0, 3], [0.1, 0.8, 0.1], 0.0)
    ok &= check("concentrating mass at truth reduces CRPS",
                sharp < diffuse, f"sharp {sharp:.4f} < diffuse {diffuse:.4f}")

    # 6. brute-force numerical integral match
    max_bf = 0.0
    for _ in range(20):
        k = rng.integers(2, 6)
        vals = np.sort(rng.normal(size=k) * 3)
        mass = rng.random(size=k) + 0.1
        y = float(rng.normal() * 3)
        exact = crps_stepped(vals, mass, y)
        bf = _brute_force_crps(vals, mass, y)
        max_bf = max(max_bf, abs(exact - bf))
    ok &= check("stepped == brute-force numerical integral (20 cases)",
                max_bf < 1e-3, f"max abs diff = {max_bf:.2e}")

    # 7. uniform on {-1,0,1} vs y=0, worked by hand:
    # F: 0 (x<-1), 1/3 ([-1,0)), 2/3 ([0,1)), 1 (x>=1)
    # y=0 -> indicator 0 for x<0, 1 for x>=0
    # [-1,0): (1/3-0)^2 *1 = 1/9
    # [0,1):  (2/3-1)^2 *1 = 1/9
    # total = 2/9
    got = crps_stepped([-1, 0, 1], [1/3, 1/3, 1/3], 0.0)
    ok &= check("uniform{-1,0,1} vs y=0: CRPS == 2/9",
                abs(got - 2/9) < 1e-9, f"got {got:.6f} vs {2/9:.6f}")

    # 8. crps_sample sanity: large sample from N(0,1) vs y=0 approx 0.234 (known)
    s = rng.normal(size=20000)
    got = crps_sample(s, 0.0)
    # closed form CRPS(N(0,1),0) = 1/sqrt(pi) - ... actually = 2*phi(0)+... ~ 0.2337
    want = 1.0 / np.sqrt(np.pi) * (1.0)  # placeholder; use known value below
    known = 0.23369  # CRPS(N(0,1), y=0)
    ok &= check("empirical N(0,1) sample vs y=0 ~ 0.2337",
                abs(got - known) < 5e-3, f"got {got:.5f} vs {known}")

    print()
    print("ALL CRPS CHECKS PASSED" if ok else "SOME CRPS CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
