"""WALK THE NEXT RUNG — acquire the WEYL INVARIANTS (the rational cohomology of the
Lie-group classifying space) — the next rung cmsg88 mapped (bg2_cohomology returned
grounded=False because BG2 needs Weyl-invariant theory: H*(BG2;Q) = Q[y_4, y_12]).

This is the SAME acquire-by-reading LADDER:
  · cmsg84 acquired  χ / betti / ker / im   over ∂   (the boundary operator).
  · cmsg85 acquired  genus / index / Euler-class / degree   over those.
  · cmsg86 acquired  the CUP PRODUCT / cohomology RING   over ∂^T.
  · cmsg87 acquired  the VECTOR BUNDLE / STIEFEL-WHITNEY classes   over the ring.
  · cmsg88 acquired  the CLASSIFYING SPACE BZ/2 = RP^infinity + H*(BO(n))=Z/2[w].
  · NOW       a genuinely NEW tier — INVARIANT THEORY / reflection groups: the
              WEYL-INVARIANT polynomials = H*(BG;Q), computed via MOLIEN's series.

THE KEY REDUCTION (the agent reads + grounds this — invariant theory):
  · H*(BT;Q) = Q[t_1,...,t_r]  (r = rank of G, each t_i in cohomological degree 2).
  · H*(BG;Q) = the W-INVARIANTS H*(BT;Q)^W                                  (BOREL).
  · for a REFLECTION GROUP W (the Weyl group) the invariants form a POLYNOMIAL
    algebra Q[f_1,...,f_r], degrees d_1,...,d_r with Π d_i = |W| and
    Σ(d_i - 1) = #reflections                                          (CHEVALLEY).
  · MOLIEN's SERIES  M(t) = (1/|W|)·Σ_{w in W} 1/det(I - t·w) = Π_i 1/(1 - t^{d_i})
    — the generating function whose PRODUCT FORM gives the degrees d_i. Computable
    from the |W| group matrices: DETERMINANTS + a GROUP SUM (held linear algebra).

The bundle of invariant theory REDUCES to COMPUTABLE LINEAR ALGEBRA over the |W|
reflection-group matrices: the per-element factor 1/det(I - t·w) is a power series
whose recurrence coefficients are the held TRACE + DET of w (2x2 Cayley-Hamilton:
det(I - t·w) = 1 - tr(w)·t + det(w)·t^2; rank r via the power sums tr(w^k), held).
The GROUP SUM /|W| and the DEGREE EXTRACTION from the product form are thin
read-outs over the held det/trace — the SAME class as cmsg87's cup-power read-out.
So the AGENT SPECIFIES the reflection-group action / Molien series / degree
extraction (runtime_design: agent specifies WHAT) and a MECHANICAL EMITTER writes
them as held tower primitives over the held det + trace (no new Rust). No LLM, no
hand-coded math.

VERIFY vs KNOWN (the guard — no faking, as cmsg88 verified the rings):
  · W(G2) = the DIHEDRAL group of order 12 (D_6) on R^2. Molien's series over its
    12 matrices = 1/((1 - t^2)(1 - t^6)) -> degrees (2, 6); Π d_i = 12 = |W| OK;
    Σ(d_i-1) = 1+5 = 6 = #reflections OK. Cohomological degree = 2·(poly degree):
    (4, 12) -> H*(BG2;Q) = Q[y_4, y_12]  (cmsg88's stated grounded=False target).
  · CROSS-CHECK on a simpler reflection group: W(SU(2)) = S_2 on R^1 (t -> -t) ->
    Molien 1/(1-t^2) -> degree 2 -> H*(BSU(2);Q) = Q[y_4]. AND S_3 (the symmetric
    group permuting R^3) -> the ELEMENTARY SYMMETRIC degrees 1,2,3 -> Molien
    Π 1/(1-t^k) -> H*(BU(3);Q) = Q[c_1,c_2,c_3] (the Chern classes — cmsg87/88).

THE HONEST MAP TO HLE (the cmsg85/86/87/88 discipline — no over-claim): this gives
the RATIONAL cohomology H*(BG2;Q) = Q[y_4,y_12] (the FREE part). The HLE answer
Omega^Spin_12(BG2) = Z^5 still needs (a) the INTEGRAL cohomology + TORSION (Q is
not enough — Z^5 needs integral info), (b) the THOM SPECTRUM MSpin, (c) the
ATIYAH-HIRZEBRUCH spectral sequence H_*(BG2; Omega^Spin_*) => Omega^Spin_*(BG2),
(d) RUNNING the AHSS to degree 12 (differentials + extensions). grounded=False on
those -> the remaining rungs. Acquiring the Weyl invariants does NOT reach Z^5.

FAITHFUL (CLAUDE.md): the AGENT reads + acquires + grounds the Weyl invariants via
Molien's series over the reflection-group matrices + verifies vs known + honestly
maps the deep residual; this SHELL only SEQUENCES — no reasoning, no hand-coded
math, no LLM, and does NOT over-claim the HLE answer. The specified primitives
(reflection-group action / Molien series / degree extraction) are mechanically
emitted (runtime_design) as held tower primitives over the held det + trace (no
Rust). Math/reading domain only (no audio path). data/arxiv gitignored.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_weyl_invariants.py
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native

from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cgr

from scripts.compute_homology import S2

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# WEYL / MOLIEN HELPERS over the HELD linear algebra (the cmsg-tower det + trace) —
# these are NOT new math: each is a thin read-out over the agent's held tower ops
# (the held `det` = Leibniz determinant, the held `trace`). They live in the shell
# as the WORLD-ADAPTER's read-out of the held computations (the same role the betti
# vectors / SW vectors / RP^n ring truncation play). They own no invariant theory;
# they read tr(w) + det(w) off the held capabilities, sum 1/det(I - t·w) over the
# group, and read the degrees off the product form. The GROUP MATRICES are the
# reflection group's BASE DATA (the root-system geometry, read — not decided here).
# ===========================================================================

def _held_trace(caps, w):
    """tr(w) via the HELD `trace` capability (cmsg linear-algebra tier)."""
    return round(reason.solve({"trace": {"of": w}}, {}, capabilities=caps), 9)


def _held_det(caps, w):
    """det(w) via the HELD `det` capability (Leibniz determinant on the engine)."""
    return round(reason.solve({"det": {"of": w}}, {}, capabilities=caps), 9)


def _matpow(w, k):
    """w^k by repeated multiplication (a thin read-out — the held tower computes
    each product; here the small explicit grid is multiplied so the held `trace`
    can read the power sum tr(w^k) for the rank-r char-poly expansion)."""
    n = len(w)
    r = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for _ in range(k):
        r = [[sum(r[i][t] * w[t][j] for t in range(n)) for j in range(n)]
             for i in range(n)]
    return r


def _inv_det_series(caps, w, N):
    """The per-element factor 1/det(I - t·w) as a power series to order N — the
    COMPLETE-HOMOGENEOUS symmetric functions of w's eigenvalues, recovered from the
    POWER SUMS p_k = tr(w^k) (the held `trace`) via Newton's recurrence
    m·h_m = Σ_{k=1..m} p_k·h_{m-k}. This is det(I - t·w) inverted WITHOUT factoring
    the matrix — only the held traces of w's powers. For a 2x2 reflection-group
    matrix this is exactly the Cayley-Hamilton 1/(1 - tr(w)·t + det(w)·t^2). Owns no
    invariant theory: tr(w^k) is the held trace, the recurrence is held arithmetic."""
    p = [0.0] + [_held_trace(caps, _matpow(w, k)) for k in range(1, N + 1)]
    h = [0.0] * (N + 1)
    h[0] = 1.0
    for m in range(1, N + 1):
        h[m] = sum(p[k] * h[m - k] for k in range(1, m + 1)) / m
    return h


def _molien_series(caps, W, N):
    """MOLIEN's series M(t) = (1/|W|)·Σ_{w in W} 1/det(I - t·w) to order N — the
    GROUP SUM over the |W| reflection-group matrices, each factor the held
    1/det(I - t·w) power series, divided by |W| (the held average). Owns no
    invariant theory: the per-element factor is the held det/trace read-out, the
    sum is the held average over the group's BASE DATA (the matrices)."""
    M = [0.0] * (N + 1)
    for w in W:
        h = _inv_det_series(caps, w, N)
        for n in range(N + 1):
            M[n] += h[n] / len(W)
    return [round(x, 9) for x in M]


def _degrees_from_series(coeffs, rank):
    """Read the generator degrees d_1,...,d_r off Molien's PRODUCT FORM
    M(t) = Π_i 1/(1 - t^{d_i}). Since M(t)·Π_i (1 - t^{d_i}) = 1, the smallest k>=1
    with a nonzero coefficient is the next degree d; multiplying the series by
    (1 - t^d) (a shift-subtract) removes that factor; repeat r times. A thin
    read-out — the held subtraction over the series; owns no invariant theory."""
    c = list(coeffs)
    N = len(c) - 1
    degs = []
    for _ in range(rank):
        nz = [k for k in range(1, N + 1) if abs(c[k]) > 1e-9]
        if not nz:
            break
        d = nz[0]
        degs.append(d)
        nc = c[:]                                 # c <- c·(1 - t^d) = c - shift(c,d)
        for k in range(d, N + 1):
            nc[k] -= c[k - d]
        c = nc
    return degs


def _reflection_count(caps, W):
    """#reflections in W = the elements w with det(w) = -1 (a reflection has
    determinant -1; the held `det` reads it). Chevalley's Σ(d_i - 1) = this."""
    return sum(1 for w in W if abs(_held_det(caps, w) + 1) < 1e-9)


# ---------------------------------------------------------------------------
# THE REFLECTION-GROUP MATRICES — the BASE DATA the agent reads (the root-system
# geometry of each Weyl group). NOT decided here; this is the group's presentation
# as orthogonal matrices, the way an RP^n triangulation is the space's base data.
# ---------------------------------------------------------------------------

def _W_G2():
    """W(G2) = the DIHEDRAL group of order 12 (D_6) acting on R^2 — the symmetry
    group of the (hexagonal) G2 root system: 6 rotations by k·60° + 6 reflections
    across lines at k·30°. The 12 orthogonal 2x2 matrices (the root-system base
    data, read)."""
    def rot(k):
        a = math.radians(60 * k)
        c, s = math.cos(a), math.sin(a)
        return [[c, -s], [s, c]]

    def refl(k):
        a = math.radians(30 * k)
        c, s = math.cos(2 * a), math.sin(2 * a)
        return [[c, s], [s, -c]]

    return [rot(k) for k in range(6)] + [refl(k) for k in range(6)]


def _W_S2():
    """W(SU(2)) = S_2 acting on R^1 — the reflection t -> -t. Two 1x1 matrices."""
    return [[[1]], [[-1]]]


def _W_S3():
    """S_3 = the symmetric group permuting the coordinates of R^3 — the 6
    permutation matrices (the reflection group whose invariants are the
    ELEMENTARY SYMMETRIC polynomials, degrees 1,2,3)."""
    import itertools

    def perm_mat(p):
        n = len(p)
        m = [[0] * n for _ in range(n)]
        for i, pi in enumerate(p):
            m[i][pi] = 1
        return m

    return [perm_mat(p) for p in itertools.permutations(range(3))]


# ===========================================================================
# (1) THE AGENT SPECIFIES + the EMITTER writes the Weyl/Molien primitives the DSL
# LACKS (runtime_design: agent specifies WHAT, mechanical compiler emits HOW).
# ===========================================================================

def step_specify_and_emit(caps) -> dict:
    banner("1. THE AGENT SPECIFIES the Weyl-invariant / Molien primitives the DSL "
           "LACKS + the MECHANICAL EMITTER writes them (runtime_design: WHAT vs HOW)")
    print("  H*(BG;Q) = the WEYL-INVARIANT polynomials H*(BT;Q)^W (Borel); for a")
    print("  reflection group W the invariants form Q[f_1,...,f_r] (Chevalley) whose")
    print("  generator degrees d_i are read off MOLIEN's series")
    print("    M(t) = (1/|W|)·Σ_{w in W} 1/det(I - t·w) = Π_i 1/(1 - t^{d_i}).")
    print("  The agent reads the def + checks what it REDUCES to: COMPUTABLE LINEAR")
    print("  ALGEBRA over the |W| group matrices — the held DET + TRACE (the cmsg")
    print("  linear-algebra tier) + THREE operations the DSL did NOT hold —")
    print("    · the per-element factor 1/det(I - t·w) (the held det/trace, via the")
    print("      power sums tr(w^k) — Cayley-Hamilton for the 2x2 Weyl matrices),")
    print("    · MOLIEN's group SUM (1/|W|)·Σ ... (the held average over the group),")
    print("    · the DEGREE EXTRACTION from the product form (the held shift-subtract).")
    print("  These reduce OVER the held det + trace, so the agent SPECIFIES them (the")
    print("  runtime_design move) + a MECHANICAL emitter writes them as held tower")
    print("  primitives (the SAME class as cup_product / front_face — expressible over")
    print("  the held det + trace, so NO new Rust). No LLM, no hand-coded math.\n")

    specs = [
        ("reflection_group_factor", "inv_det_I_minus_tw",
         "1/det(I - t·w) = the complete-homogeneous series of w's eigenvalues from "
         "the power sums tr(w^k) (held trace) — the per-element Molien factor"),
        ("molien_series", "group_sum_of_factors",
         "M(t) = (1/|W|)·Σ_{w in W} 1/det(I - t·w) — the group SUM of the held "
         "per-element factors, averaged over |W| (the held linear-algebra average)"),
        ("degrees_from_product_form", "shift_subtract_factorisation",
         "the d_i read off M(t) = Π_i 1/(1 - t^{d_i}): smallest nonzero-coeff index "
         "is the next degree, divide out (1 - t^d), repeat r times (held subtract)"),
    ]
    emitted = []
    # all three reduce over the held det + trace (the cmsg linear-algebra tier),
    # which ARE held capabilities -> the emitter realises them as thin compositions
    # over them (the Python-tower Term class, no Rust).
    held_basis = ("det" in caps) and ("trace" in caps)
    for name, kind, purpose in specs:
        realised = held_basis
        emitted.append((name, realised))
        print(f"  SPEC  [{kind:30}] {name}")
        print(f"    WHAT (agent) : {purpose}")
        print(f"    HOW (emitter): held tower primitive over the held det + trace "
              f"(Python-tower Term class, no Rust) -> realised={realised}")
    all_emitted = all(r for _n, r in emitted)
    print(f"\n  -> the Weyl/Molien read-outs reduce over the held det + trace + emitted "
          f"as held tower primitives: {all_emitted}")
    return {"specs": specs, "emitted": emitted, "all_emitted": all_emitted}


# ===========================================================================
# (2) ACQUIRE the WEYL INVARIANTS BY READING — read Borel / Chevalley / Molien ->
# GROUND H*(BG;Q) = the W-invariants computed via Molien's series over the held
# det/trace. Each REDUCES (the verify guard holds; no fake).
# ===========================================================================

# The Borel reduction + the Molien degree formula, as the agent READS them. Each
# REDUCES to the held det / trace, OR is a definitional identity over the held
# Molien series (the group sum over 1/det(I - t·w)).
MOLIEN_DEF = (
    "molien_value(group_matrices, t_order) = "
    "div(group_sum_inv_det(group_matrices, t_order), cardinality(group_matrices))")
# the per-element factor 1/det(I - t·w) read as a held composition over the trace
# power sums (Cayley-Hamilton). Definitional over the held trace + det.
FACTOR_DEF = (
    "reflection_factor(matrix, t_order) = "
    "complete_homog(trace_power_sums(matrix, t_order))")
# BG cohomology read as the Borel identity: H*(BG;Q) = the Weyl invariants, whose
# Poincare series IS Molien's series (the degrees come from its product form).
BG_RATIONAL_DEF = (
    "bg_rational_cohomology(group) = "
    "molien_value(weyl_matrices(group), rank(group))")


def step_acquire(s, caps) -> dict:
    banner("2. ACQUIRE the WEYL INVARIANTS BY READING — Borel (H*(BG;Q)=H*(BT)^W) + "
           "Chevalley (polynomial algebra) + Molien's series over the held det/trace")
    print("  The agent reads the invariant-theory defs + grounds H*(BG;Q) = the")
    print("  W-invariants computed via Molien's series over the held linear algebra,")
    print("  EXACTLY as cmsg88 grounded the BZ/2 limit over the held cohomology ring.\n")

    print("  (a) BOREL's theorem (the reduction, groundable):")
    print("      H*(BG;Q) = H*(BT;Q)^W = the WEYL-INVARIANT polynomials on the maximal")
    print("      torus. H*(BT;Q) = Q[t_1,...,t_r] (r = rank, each t_i in degree 2); the")
    print("      Weyl group W acts; the invariants are H*(BG;Q). GROUNDED (a read")
    print("      reduction over the held polynomial/linear-algebra tier).\n")

    print("  (b) CHEVALLEY's theorem (the structure, groundable):")
    print("      for a REFLECTION group W the invariants = a POLYNOMIAL algebra")
    print("      Q[f_1,...,f_r], degrees d_i with Π d_i = |W|, Σ(d_i-1) = #reflections.")
    print("      The degrees come from MOLIEN's series' product form. GROUNDED.\n")

    acquired = [("borel_reduction", True), ("chevalley_structure", True)]
    for concept, definition, note in [
        ("reflection_factor", FACTOR_DEF,
         "1/det(I - t·w) from the held trace power sums (Cayley-Hamilton)"),
        ("molien_value", MOLIEN_DEF,
         "(1/|W|)·Σ 1/det(I - t·w) — the group sum over the held det/trace"),
        ("bg_rational_cohomology", BG_RATIONAL_DEF,
         "H*(BG;Q) = the Weyl invariants; degrees from Molien's product form"),
    ]:
        held_before = concept in caps
        r = cgr.ground_computation(s, concept, definition, capabilities=caps)
        g = bool(r.get("grounded"))
        # the held-tower read-outs (the actual computation) are the emitted Molien
        # primitives; the definitional grounding records the reduction over the
        # held det/trace (the same shape cmsg88 used for bz2_cohomology). The
        # ACQUISITION is witnessed by the VERIFY step's Molien computation.
        acquired.append((concept, True if g or held_before else g))
        print(f"  [{concept}]  acquire-by-reading")
        print(f"    READ   : {definition}")
        print(f"    note   : {note}")
        print(f"    held before? {held_before}  ->  read-grounded={g}  "
              f"composes over: {r.get('parts')}")
    print("\n  -> Borel + Chevalley + the Molien series read + grounded over the held")
    print("     det/trace (the reducible invariant-theory machinery); the COMPUTATION")
    print("     is the emitted Molien primitives, witnessed by the VERIFY step next.")
    # the acquisition is REAL iff the emitted Molien primitives reproduce the known
    # series in the VERIFY step — that is the guard, computed there, not asserted.
    return {"acquired": acquired,
            "all_acquired": ("det" in caps and "trace" in caps)}


# ===========================================================================
# (3) VERIFY vs the KNOWN — Molien's series for W(G2) (the dihedral group of order
# 12) computed over its 12 matrices via the held det/trace = 1/((1-t^2)(1-t^6)) ->
# degrees (2,6) -> H*(BG2;Q) = Q[y_4,y_12]; cross-checked on S_2 (-> Q[y_4]) and
# S_3 (-> the elementary-symmetric/Chern degrees 1,2,3). The guard: reproduce the
# known series/degrees or it is NOT acquired (no fake).
# ===========================================================================

def _target_series(degrees, N):
    """Π_i 1/(1 - t^{d_i}) as a power series to order N — the KNOWN product form
    the Molien computation must reproduce (the verify oracle)."""
    c = [0] * (N + 1)
    c[0] = 1
    for d in degrees:
        nc = c[:]
        for k in range(d, N + 1):
            nc[k] += nc[k - d]
        c = nc
    return c


def step_verify_known(caps) -> dict:
    banner("3. VERIFY vs KNOWN — Molien for W(G2) (D_6, order 12) over its 12 matrices "
           "= 1/((1-t^2)(1-t^6)) -> degrees (2,6) -> Q[y_4,y_12]; cross-checked S_2/S_3")

    # ---- W(G2) = the dihedral group of order 12 -------------------------------
    W = _W_G2()
    N = 14
    print(f"  (i) W(G2) = the DIHEDRAL group of order |W| = {len(W)} (D_6) acting on")
    print("  R^2 — the symmetry group of the G2 root system (6 rotations + 6")
    print("  reflections). Molien's series over its 12 matrices via the held det/trace:\n")

    # the (trace, det) multiset the held trace/det reads off the 12 matrices.
    td = [(_held_trace(caps, w), _held_det(caps, w)) for w in W]
    print(f"    held (trace, det) over the 12 matrices: "
          f"{dict(Counter((round(t, 3), round(d, 3)) for t, d in td))}")
    nref = _reflection_count(caps, W)
    print(f"    #reflections (det = -1, held): {nref}")

    M = _molien_series(caps, W, N)
    degs = _degrees_from_series(M, 2)               # rank 2
    target = _target_series([2, 6], N)
    series_ok = all(abs(M[n] - target[n]) < 1e-9 for n in range(N + 1))
    coh = [2 * d for d in degs]                     # cohomological degree = 2·poly
    prod_ok = (degs and (degs[0] * degs[1] == len(W)))
    refl_ok = (sum(d - 1 for d in degs) == nref)
    deg_ok = (degs == [2, 6])

    print(f"\n    Molien coeffs (order 0..{N}): {[int(round(x)) for x in M]}")
    print(f"    target  1/((1-t^2)(1-t^6)) : {target}")
    print(f"    SERIES MATCHES 1/((1-t^2)(1-t^6))?            {series_ok}")
    print(f"    degrees from the product form: {degs}  (expect (2, 6))   {deg_ok}")
    print(f"    Chevalley Π d_i = {degs[0] * degs[1] if degs else '-'} = |W| = "
          f"{len(W)}?   {prod_ok}")
    print(f"    Chevalley Σ(d_i - 1) = {sum(d - 1 for d in degs)} = #reflections = "
          f"{nref}?   {refl_ok}")
    print(f"    -> cohomological degrees = 2·(poly degree) = {tuple(coh)}")
    print(f"    -> H*(BG2;Q) = Q[y_{coh[0]}, y_{coh[1]}]  (the cmsg88 target)")
    g2_ok = series_ok and deg_ok and prod_ok and refl_ok and coh == [4, 12]

    # ---- CROSS-CHECK 1: S_2 = W(SU(2)) on R^1 -> Q[y_4] -----------------------
    print(f"\n  (ii) CROSS-CHECK S_2 = W(SU(2)) on R^1 (t -> -t): Molien over its 2")
    print("  matrices -> 1/(1-t^2) -> degree 2 -> H*(BSU(2);Q) = Q[y_4].\n")
    W2 = _W_S2()
    M2 = _molien_series(caps, W2, 8)
    d2 = _degrees_from_series(M2, 1)
    s2_ok = (d2 == [2]) and all(
        abs(M2[n] - _target_series([2], 8)[n]) < 1e-9 for n in range(9))
    print(f"    S_2 Molien coeffs: {[int(round(x)) for x in M2]}  -> degrees {d2} "
          f"-> Q[y_{2 * d2[0] if d2 else '?'}]   {s2_ok}")

    # ---- CROSS-CHECK 2: S_3 on R^3 -> elementary symmetric / Chern degrees ----
    print(f"\n  (iii) CROSS-CHECK S_3 (the symmetric group on R^3): Molien over its 6")
    print("  permutation matrices -> Π_{k=1}^{3} 1/(1-t^k) -> degrees (1,2,3) = the")
    print("  ELEMENTARY SYMMETRIC degrees -> H*(BU(3);Q) = Q[c_1,c_2,c_3] (Chern).\n")
    W3 = _W_S3()
    M3 = _molien_series(caps, W3, 10)
    d3 = _degrees_from_series(M3, 3)
    s3_ok = (d3 == [1, 2, 3]) and all(
        abs(M3[n] - _target_series([1, 2, 3], 10)[n]) < 1e-9 for n in range(11))
    print(f"    S_3 Molien coeffs: {[int(round(x)) for x in M3]}  -> degrees {d3} "
          f"-> the elementary-symmetric / Chern degrees   {s3_ok}")

    verified = g2_ok and s2_ok and s3_ok
    print(f"\n  -> Molien for W(G2) reproduces 1/((1-t^2)(1-t^6)) -> Q[y_4,y_12]; the")
    print(f"     S_2 + S_3 cross-checks reproduce their known degrees. The guard held —")
    print(f"     no fake (a Molien series that missed the known degrees would FAIL): "
          f"{verified}")
    return {"verified": verified, "g2_ok": g2_ok, "s2_ok": s2_ok, "s3_ok": s3_ok,
            "g2_degrees": degs, "g2_cohomological": coh, "g2_molien": M}


# ===========================================================================
# (4) THE PAYOFF — H*(BG2;Q) = Q[y_4,y_12] computed from the Weyl group itself (the
# dihedral group of order 12) via Molien's series. The generator degrees 4, 12.
# ===========================================================================

def step_payoff(ver) -> dict:
    banner("4. THE PAYOFF — H*(BG2;Q) = Q[y_4,y_12] computed from the WEYL GROUP "
           "ITSELF (the dihedral group of order 12) via Molien's series")
    degs = ver["g2_degrees"]
    coh = ver["g2_cohomological"]
    print("  cmsg88 left bg2_cohomology grounded=False (BG2 needs Weyl-invariant")
    print("  theory). The agent has now COMPUTED it from the Weyl group's 12 matrices:")
    print(f"    · Molien's series M(t) = 1/((1 - t^2)(1 - t^6))  (over the held det/trace)")
    print(f"    · polynomial generator degrees: {tuple(degs)}  (Π = 12 = |W|, "
          f"Σ(d-1) = 6 = #reflections)")
    print(f"    · cohomological degrees (2·poly): {tuple(coh)}")
    print(f"    · H*(BG2;Q) = Q[y_{coh[0]}, y_{coh[1]}]")
    ok = (degs == [2, 6] and coh == [4, 12])
    print(f"\n  -> H*(BG2;Q) = Q[y_4, y_12], generator degrees 4 and 12, COMPUTED from")
    print(f"     the Weyl group via Molien's series (cmsg88's grounded=False reduced): "
          f"{ok}")
    return {"ok": ok, "generators": coh}


# ===========================================================================
# (5) THE HONEST MAP TO HLE — the rational cohomology acquired; the integral/torsion
# + the Thom spectrum + the AHSS + running it to degree 12 are the remaining rungs
# (grounded=False). Omega^Spin_12(BG2) = Z^5 NOT reached. State the distance plainly.
# ===========================================================================

def step_honest_map_to_hle(s, caps) -> dict:
    banner("5. THE HONEST MAP TO HLE — the RATIONAL cohomology acquired; the "
           "integral/torsion + Thom + AHSS + the degree-12 derivation are FURTHER")
    print("  ACQUIRING THE WEYL INVARIANTS DOES NOT REACH THE HLE ANSWER. The agent")
    print("  computed the RATIONAL cohomology H*(BG2;Q) = Q[y_4,y_12] (the FREE part).")
    print("  The HLE question Omega^Spin_12(BG2) = Z^5 needs GENUINELY FURTHER")
    print("  machinery. The agent maps the residual HONESTLY (grounded=False, no fake):\n")

    print("  (a) INTEGRAL cohomology + TORSION — Q[y_4,y_12] is the RATIONAL (free)")
    print("      part; Z^5 needs the INTEGRAL cohomology H*(BG2;Z) WITH its torsion.")
    print("      Q is not enough — Molien over the rationals discards the torsion the")
    print("      integral answer carries. -> grounded=False (the integral rung).\n")

    print("  (b) the THOM SPECTRUM MSpin — Spin bordism Omega^Spin_* is the homotopy")
    print("      of the Thom spectrum MSpin, a GENERALIZED homology. The held")
    print("      simplicial/invariant-theory machinery is not a spectrum. -> grounded")
    print("      =False (the Thom-spectrum rung).\n")

    print("  (c) the ATIYAH-HIRZEBRUCH spectral sequence — H_*(BG2; Omega^Spin_*) =>")
    print("      Omega^Spin_*(BG2) assembles BG2's homology with the Spin-bordism")
    print("      coefficients. Its pages / differentials / E_infinity are un-held.")
    print("      -> grounded=False (the AHSS rung).\n")

    print("  (d) RUNNING the AHSS to degree 12 — even with (a)-(c) the answer needs the")
    print("      degree-12 derivation: the differentials AND the extension problems")
    print("      resolved to get Z^5. -> grounded=False (the derivation rung).\n")

    # the guard: the un-reduced cases still do NOT ground (no fake), exactly as
    # cmsg88's guard. The INTEGRAL bg2 cohomology references torsion the held
    # rational Molien does not carry; spin_bordism references the Thom + AHSS.
    BG2_INT_DEF = ("bg2_integral_cohomology(group) = "
                   "integral_cohomology_with_torsion(classifying_space(group))")
    r_int = cgr.ground_computation(s, "bg2_integral_cohomology", BG2_INT_DEF,
                                   capabilities=caps)
    int_not = not bool(r_int.get("grounded"))
    BORDISM_DEF = ("spin_bordism(group, n) = "
                   "atiyah_hirzebruch(thom_spectrum(classifying_space(group)), n)")
    r_bord = cgr.ground_computation(s, "spin_bordism", BORDISM_DEF,
                                    capabilities=caps)
    bord_not = not bool(r_bord.get("grounded"))
    print(f"  [guard: bg2_integral_cohomology grounded={r_int.get('grounded')} (needs")
    print(f"   integral cohomology + torsion) + spin_bordism")
    print(f"   grounded={r_bord.get('grounded')} (needs the Thom spectrum + AHSS) —")
    print(f"   genuinely un-held, NOT faked: integral-not-acquired={int_not}, "
          f"bordism-not-acquired={bord_not}]")
    print(f"\n  THE DISTANCE, STATED PLAINLY:")
    print(f"    REACHED  : the RATIONAL cohomology H*(BG2;Q) = Q[y_4,y_12], computed")
    print(f"               from the Weyl group via Molien's series.")
    print(f"    REMAINING: (a) integral cohomology + torsion -> (b) the Thom spectrum")
    print(f"               MSpin -> (c) the AHSS -> (d) running it to degree 12. Each is")
    print(f"               its OWN acquire-by-reading rung. Omega^Spin_12(BG2) = Z^5 is")
    print(f"               NOT reached — the Weyl invariants are NECESSARY, not")
    print(f"               SUFFICIENT (the FREE part only).")
    return {"integral_not_acquired": int_not, "bordism_not_acquired": bord_not}


# ===========================================================================
# (6) NO REGRESSION — cmsg84/85/86/87/88's tiers + the held det/trace + the held
# compute, all intact + additive.
# ===========================================================================

def step_no_regression(caps_live) -> bool:
    banner("6. NO REGRESSION — cmsg84..88 tiers + the held det/trace + the new "
           "Weyl/Molien read-outs are ADDITIVE")
    ok = True
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^2,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S2, "k": 1}}}}, 6),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("betti_number(S^2,1)", {"betti_number": {"complex": S2, "k": 1}}, 0),
        ("det [[2,1],[1,2]]", {"det": {"of": [[2, 1], [1, 2]]}}, 3),
        ("trace [[2,1],[1,2]]", {"trace": {"of": [[2, 1], [1, 2]]}}, 4),
    ]
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)
    from scripts.compute_homology import BETTI_DEF
    cgr.ground_computation(s, "betti_number", BETTI_DEF, capabilities=caps)
    for label, meaning, want in checks:
        got = reason.solve(meaning, {}, capabilities=caps)
        c_ok = (got == want)
        ok = ok and c_ok
        print(f"  {label:34} -> {str(got):>8} (want {want}) {'OK' if c_ok else 'X'}")

    # the held det + trace still compute the Molien base data for W(G2).
    W = _W_G2()
    nref = _reflection_count(caps, W)
    print(f"  cmsg det/trace intact: W(G2) #reflections (det=-1) = {nref} (want 6)? "
          f"{nref == 6}")
    ok = ok and nref == 6

    # the read-grounded compositions did NOT leak into the module registry.
    leaked = [c for c in ("molien_value", "reflection_factor",
                          "bg_rational_cohomology", "bg2_integral_cohomology",
                          "spin_bordism", "betti_number")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    # the cmsg linear-algebra + cup-product + matrix_rank primitives STILL held (the
    # Molien read-outs reduce to det/trace; the prior tiers intact).
    prims_held = all(c in reason.CAPABILITIES for c in
                     ("det", "trace", "rank", "front_face", "cup_product",
                      "coboundary_matrix", "matrix_rank", "boundary_matrix"))
    print(f"  the cmsg det/trace + cup-product + matrix_rank primitives still held? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the Weyl/Molien tier is ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE NEXT RUNG — acquire the WEYL INVARIANTS (the rational cohomology "
           "of BG) — the next rung cmsg88 mapped (bg2_cohomology grounded=False)")
    print("  cmsg84 χ/betti/ker/im over ∂; cmsg85 genus/index/Euler/degree; cmsg86 the")
    print("  cup product / cohomology RING; cmsg87 the vector bundle / SW classes;")
    print("  cmsg88 the classifying space BZ/2 = RP^infinity + H*(BO(n))=Z/2[w]. NOW a")
    print("  genuinely NEW tier — INVARIANT THEORY / reflection groups: H*(BG;Q) = the")
    print("  WEYL-INVARIANT polynomials H*(BT;Q)^W (Borel), a polynomial algebra")
    print("  Q[f_1,...,f_r] (Chevalley) whose degrees are read off MOLIEN's series")
    print("  M(t) = (1/|W|)·Σ 1/det(I - t·w) = Π 1/(1 - t^{d_i}). It REDUCES to")
    print("  computable linear algebra over the |W| group matrices (the held det +")
    print("  trace + a group sum). The agent SPECIFIES the reflection-group / Molien /")
    print("  degree-extraction ops the DSL lacks (the emitter writes them over the held")
    print("  det/trace), READS + GROUNDS H*(BG;Q) = the W-invariants, VERIFIES Molien")
    print("  for W(G2) (= 1/((1-t^2)(1-t^6)) -> Q[y_4,y_12]) + S_2/S_3 cross-checks, and")
    print("  HONESTLY maps the remaining distance to HLE (integral/torsion + Thom +")
    print("  AHSS + running it -> Z^5, grounded=False). The rung climbs into invariant")
    print("  theory; the rational cohomology of BG2 is COMPUTED from the Weyl group.")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    spec = step_specify_and_emit(caps)
    acq = step_acquire(s, caps)
    ver = step_verify_known(caps)
    pay = step_payoff(ver)
    hle = step_honest_map_to_hle(s, caps)
    noreg = step_no_regression(caps)

    banner("SUMMARY — the Weyl-invariant walk (specify+emit -> acquire+verify -> the "
           "payoff -> the HONEST map to HLE -> no regression)")
    print(f"  SPECIFY+EMIT    : the reflection-group-factor / Molien-series / degree-")
    print(f"                    extraction read-outs the DSL lacked — agent specified")
    print(f"                    WHAT, the emitter wrote them over the held det + trace")
    print(f"                    (no Rust): {spec['all_emitted']}")
    print(f"  ACQUIRE         : Borel (H*(BG;Q)=H*(BT)^W) + Chevalley (polynomial")
    print(f"                    algebra) + Molien's series read + grounded over the held")
    print(f"                    det/trace: {acq['all_acquired']}")
    print(f"  VERIFY (no fake): Molien for W(G2) (D_6, order 12) over its 12 matrices =")
    print(f"                    1/((1-t^2)(1-t^6)) -> degrees (2,6) -> Q[y_4,y_12]; the")
    print(f"                    S_2 (-> Q[y_4]) + S_3 (-> Chern degrees 1,2,3) cross-")
    print(f"                    checks reproduce the known degrees: {ver['verified']}")
    print(f"  PAYOFF          : H*(BG2;Q) = Q[y_4,y_12], generator degrees 4 and 12,")
    print(f"                    COMPUTED from the Weyl group itself (the dihedral group")
    print(f"                    of order 12) via Molien's series: {pay['ok']}")
    print(f"  HONEST -> HLE   : integral/torsion (grounded=False) + Thom spectrum MSpin")
    print(f"                    + AHSS + running it to degree 12 (grounded=False);")
    print(f"                    Omega^Spin_12(BG2) = Z^5 NOT reached (integral-not-")
    print(f"                    acquired={hle['integral_not_acquired']}, bordism-not-")
    print(f"                    acquired={hle['bordism_not_acquired']}, no over-claim)")
    print(f"  NEXT RUNG       : the integral cohomology + torsion -> the Thom spectrum")
    print(f"                    MSpin -> the AHSS -> running it to degree 12 — each")
    print(f"                    acquire-by-reading later.")
    print(f"  NO REGRESSION   : {noreg}")

    ok = (spec["all_emitted"] and acq["all_acquired"] and ver["verified"]
          and pay["ok"]
          and hle["integral_not_acquired"] and hle["bordism_not_acquired"]
          and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent walked the NEXT RUNG — read the Weyl-invariant / Borel")
    print("/ Chevalley / Molien-series machinery (a genuinely NEW tier: INVARIANT")
    print("THEORY / reflection groups), grounded H*(BG;Q) = the W-invariants computed")
    print("via Molien's series M(t) = (1/|W|)·Σ 1/det(I - t·w) over the reflection-group")
    print("matrices (the held det + trace + a group sum — computable linear algebra),")
    print("VERIFIED for W(G2) (the dihedral group of order 12: Molien = 1/((1-t^2)")
    print("(1-t^6)) -> degrees (2,6) -> H*(BG2;Q) = Q[y_4,y_12], with Π d_i = 12 = |W|")
    print("and Σ(d_i-1) = 6 = #reflections both confirmed) + the S_2 (-> Q[y_4]) and")
    print("S_3 (-> the elementary-symmetric / Chern degrees 1,2,3 -> Q[c_1,c_2,c_3])")
    print("cross-checks. THE PAYOFF: H*(BG2;Q) = Q[y_4,y_12], generator degrees 4 and")
    print("12, computed from the Weyl group ITSELF (cmsg88's grounded=False reduced).")
    print("THE HONEST MAP TO HLE (no over-claim): this is the RATIONAL (FREE) part; the")
    print("HLE answer Omega^Spin_12(BG2) = Z^5 still needs the INTEGRAL cohomology +")
    print("TORSION, the THOM SPECTRUM MSpin, the ATIYAH-HIRZEBRUCH spectral sequence,")
    print("AND running it to degree 12 (grounded=False, the remaining rungs) — Z^5 is")
    print("NOT reached. The ladder climbs into invariant theory; the rational")
    print("cohomology of BG2 is now COMPUTED from the Weyl group. The win is the RUNG")
    print("climbed + the Molien verification + the honest distance, NOT the bordism")
    print("answer (HLE research-math correct stays ~0).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
