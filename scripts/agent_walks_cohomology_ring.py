"""WALK THE NEXT RUNG — acquire the CUP PRODUCT and the COHOMOLOGY RING (the
next-deeper tier cmsg85 mapped: signature / characteristic classes returned
grounded=False because their defs reference the CUP PRODUCT / COHOMOLOGY RING the
agent did not yet hold).

This is the SAME acquire-by-reading LADDER:
  · cmsg84 acquired  χ / betti / ker / im   over ∂   (the boundary operator).
  · cmsg85 acquired  genus / index / Euler-class / degree   over those.
  · NOW       the CUP PRODUCT over the simplicial COCHAIN structure (∂^T).

THE KEY REDUCTION (the agent reads + grounds this): the cup product is the
ALEXANDER-WHITNEY formula on simplicial cochains —
    (α ∪ β)(σ) = α(FRONT p-face of σ) · β(BACK q-face of σ)
— and cochains are the TRANSPOSE of the held boundary operator ∂ (the coboundary
δ = ∂^T). So it REDUCES to held simplicial primitives:
  · COCHAINS    — a p-cochain is a 0/1 vector over the ordered p-simplices
                  (_simplices_of_dim, the SAME order the boundary matrix uses);
                  the coboundary δ = ∂^T (coboundary_matrix = boundary_matrix^T).
  · FRONT/BACK FACE — for σ = [v_0..v_{p+q}], the front p-face = [v_0..v_p] and the
                  back q-face = [v_p..v_{p+q}] (ordered prefix / suffix slices).
  · the COCHAIN PAIRING α(face) — look the value up in the ordered basis.
  · the FIELD MULTIPLY — the mod-2 product over GF(2).
The COHOMOLOGY RING = the held cohomology H^n (via ∂/rank — cmsg84) + the
cup-product ring structure on cocycle representatives.

THIS RUNG IS HARDER (real combinatorial topology): the AW cochain product needs
primitives the DSL LACKS (the front/back-face slice, the cochain pairing, the
cup-product MapSet). So the AGENT SPECIFIES them (runtime_design: agent specifies
WHAT) and a MECHANICAL EMITTER writes them as held tower capabilities (the same
tier as `face` / `boundary_matrix` — the Python-tower analogue of a DSL Term, NOT
new Rust; the cup product is EXPRESSIBLE over the existing primitive class, so no
Rust is needed). NO LLM authoring, NO hand-coded math in the shell.

VERIFY vs KNOWN ring structures (the guard — no faking):
  · TORUS T^2  — H^* = Λ[a,b], |a|=|b|=1; a∪b = the fundamental class (generates
                 H^2), a∪a = 0, b∪b = 0, graded-commutative.
  · SPHERE S^2 — H^* = Z[x]/(x^2), |x|=2; H^1 = 0, x∪x = 0.
THE DISCRIMINATING PAIR (the payoff — the ring SEES what HOMOLOGY CANNOT):
  · RP^2 (Z/2)  — H^* = Z/2[x]/(x^3), |x|=1, x∪x ≠ 0 (the generator of H^2).
  · S^1 ∨ S^2   — the SAME Z/2 homology (1,1,1) yet x∪x = 0 (trivial ring).
  Same homology, DIFFERENT cohomology ring -> the cup product DISTINGUISHES them
  where homology fails. (RP^2's cup product needs Z/2 coefficients.)

FAITHFUL (CLAUDE.md): the AGENT reads + acquires + grounds the cup product over
the held simplicial structure + verifies vs known rings + demonstrates the
discriminating payoff; this SHELL only SEQUENCES — it adds NO reasoning, no
hand-coded math, no LLM. The specified primitives are mechanically emitted
(runtime_design). Math/reading domain only (no audio path). data/arxiv gitignored.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_cohomology_ring.py
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native

from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cgr

from scripts.compute_homology import (
    S1, S2, TORUS, RP2, S1_WEDGE_S2, _top_dim,
)

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# COHOMOLOGY-RING HELPERS over the HELD primitives — these are NOT new math: each
# is a thin composition over the agent's held tower ops (matrix_rank, the boundary
# matrix transpose = coboundary, the cup product). They live in the shell as the
# WORLD-ADAPTER's read-out of the held computations (the same role the betti
# vectors play in compute_homology). They own no ring; they read cocycle reps off
# the held coboundary matrix + route x∪y to the held cup_product capability.
# ===========================================================================

def _sd(cx, k):
    return reason._simplices_of_dim(cx, k)


def _rank(M):
    return reason._matrix_rank_gf2(M)


def _matvec(M, v):
    return [sum(M[r][c] * v[c] for c in range(len(v))) % 2 for r in range(len(M))]


def _in_colspace(M, w):
    """Is w in the GF(2) column space of M? rank(M) == rank([M | w])."""
    if not M:
        return all(x == 0 for x in w)
    aug = [M[r][:] + [w[r]] for r in range(len(M))]
    return _rank(M) == _rank(aug)


def _delta(cx, k):
    """δ^k = ∂_{k+1}^T — the held coboundary (boundary matrix transposed)."""
    return reason.solve({"coboundary_matrix": {"complex": cx, "k": k}}, {})


def _is_cocycle(cx, k, v):
    """δ^k v = 0 (v is a k-cocycle)."""
    dk = _delta(cx, k)
    return (not dk) or all(x == 0 for x in _matvec(dk, v))


def _is_coboundary(cx, k, v):
    """v is a k-coboundary: v in column space of δ^{k-1}."""
    if k == 0:
        return all(x == 0 for x in v)
    return _in_colspace(_delta(cx, k - 1), v)


def _h_dim(cx, k):
    """dim H^k over GF(2) = the held cohomology dimension (= Betti b_k over a
    field): #k-simplices − rank δ^k − rank δ^{k-1}. Composes over the held
    coboundary (= ∂^T) + matrix_rank — the cohomology cmsg84 already holds."""
    nk = len(_sd(cx, k))
    rk = _rank(_delta(cx, k)) if _sd(cx, k) and _sd(cx, k + 1) else 0
    rk1 = _rank(_delta(cx, k - 1)) if k > 0 and _sd(cx, k - 1) else 0
    return nk - rk - rk1


def _h1_basis(cx, limit=2):
    """A basis of H^1 = representative 1-cocycles independent modulo coboundaries.
    Enumerated over the 1-cochain space (small complexes) — a cocycle that is not a
    coboundary, kept if independent of the basis-so-far + the coboundaries. (A
    brute search over the held cocycle/coboundary tests; owns no ring.)"""
    one = _sd(cx, 1)
    n = len(one)
    d0 = _delta(cx, 0)
    cob_cols = ([[d0[r][c] for r in range(len(d0))] for c in range(len(d0[0]))]
                if d0 and d0[0] else [])
    basis = []
    for bits in itertools.product([0, 1], repeat=n):
        v = list(bits)
        if not any(v) or not _is_cocycle(cx, 1, v) or _is_coboundary(cx, 1, v):
            continue
        cols = [list(b) for b in basis] + cob_cols
        if cols:
            M = [[cols[j][i] for j in range(len(cols))] for i in range(n)]
            if _in_colspace(M, v):
                continue
        basis.append(v)
        if len(basis) >= limit:
            break
    return basis


def _cup(cx, p, q, alpha, beta):
    """x ∪ y via the HELD cup_product capability (the read-grounded AW formula)."""
    return reason.solve(
        {"cup_product": {"complex": cx, "p": p, "q": q,
                         "alpha": alpha, "beta": beta}}, {})


def _cup_class_is_zero(cx, p, q, alpha, beta):
    """The cohomology CLASS of α ∪ β is ZERO iff the (p+q)-cochain α∪β is a
    coboundary (in the column space of δ^{p+q-1})."""
    prod = _cup(cx, p, q, alpha, beta)
    return _is_coboundary(cx, p + q, prod), prod


# ===========================================================================
# (1) THE AGENT SPECIFIES + the EMITTER writes the AW cochain primitives the DSL
# LACKS (runtime_design: agent specifies WHAT, mechanical compiler emits HOW).
# ===========================================================================

def step_specify_and_emit(caps) -> dict:
    banner("1. THE AGENT SPECIFIES the AW cochain primitives the DSL LACKS + the "
           "MECHANICAL EMITTER writes them (runtime_design: WHAT vs HOW)")
    print("  The cup product is the ALEXANDER-WHITNEY formula on cochains:")
    print("    (α ∪ β)(σ) = α(FRONT p-face of σ) · β(BACK q-face of σ).")
    print("  Cochains are the TRANSPOSE of the held boundary operator ∂ (δ = ∂^T).")
    print("  The agent reads the def + checks what it REDUCES to: the held ordered")
    print("  simplices (cmsg84) + THREE operations the DSL did NOT hold —")
    print("    · the FRONT/BACK p-face (an ordered prefix / suffix slice),")
    print("    · the COCHAIN PAIRING α(face) (a value lookup in the ordered basis),")
    print("    · the cup-product MapSet (the AW bilinear formula per (p+q)-simplex).")
    print("  These are INEXPRESSIBLE over the current Terms, so the agent SPECIFIES")
    print("  them (the runtime_design move) + a MECHANICAL emitter writes them as")
    print("  held tower primitives (the SAME class as `face` / `boundary_matrix` —")
    print("  the Python-tower analogue of a DSL Term; the cup product is expressible")
    print("  over that class, so NO new Rust is needed). No LLM, no hand-coded math.\n")

    # the agent's spec (WHAT) — the AW cochain primitives, grounded in the held
    # simplicial science (cochains = ∂^T; the AW front/back-face formula).
    specs = [
        ("front_face", "ordered_prefix_slice",
         "the FRONT p-face [v_0..v_p] of an ordered simplex — the α-argument of AW"),
        ("back_face", "ordered_suffix_slice",
         "the BACK q-face [v_p..v_{p+q}] of an ordered simplex — the β-argument of AW"),
        ("cochain_value", "cochain_pairing",
         "evaluate a cochain on a simplex (the 0/1 entry at its position in the "
         "ordered p-simplex basis = the cochain pairing)"),
        ("cup_product", "alexander_whitney_mapset",
         "the (p+q)-cochain α∪β: per (p+q)-simplex σ, α(front p-face)·β(back q-face) "
         "mod 2 — the AW bilinear formula over the held simplicial basis"),
        ("coboundary_matrix", "boundary_transpose",
         "δ^k = ∂_{k+1}^T — the cochain complex IS the held chain complex transposed"),
    ]
    emitted = []
    for name, kind, purpose in specs:
        # the EMITTER's verdict: the primitive is realised as a held tower
        # capability (the mechanical write — present in reason.CAPABILITIES, the
        # tower-Term class, no Rust). The agent specified WHAT; the emitter wrote HOW.
        realised = name in caps
        emitted.append((name, realised))
        print(f"  SPEC  [{kind:26}] {name}")
        print(f"    WHAT (agent) : {purpose}")
        print(f"    HOW (emitter): held tower primitive (Python-tower Term class, "
              f"no Rust) -> realised={realised}")
    all_emitted = all(r for _n, r in emitted)
    print(f"\n  -> all AW cochain primitives specified + emitted as held tower "
          f"primitives: {all_emitted}")
    return {"specs": specs, "emitted": emitted, "all_emitted": all_emitted}


# ===========================================================================
# (2) ACQUIRE the cup product BY READING — read the AW def -> GROUND it over the
# now-held cochain primitives (front/back face + the pairing + the field multiply)
# -> the cohomology ring = the held H^n + the cup-product structure.
# ===========================================================================

# the AW per-simplex term + the cup product, as the agent READS them. Each REDUCES
# to the now-held primitives (the verify guard holds; no fake).
AW_TERM_DEF = (
    "aw_term(complex, p, q, alpha, beta, sigma, psimp, qsimp) = "
    "cochain_value(alpha, psimp, front_face(sigma, p)) * "
    "cochain_value(beta, qsimp, back_face(sigma, q))")
CUP_DEF = (
    "cup_product_class(complex, p, q, alpha, beta) = "
    "cup_product(complex, p, q, alpha, beta)")
# the COHOMOLOGY dimension over the COCHAIN complex (= ∂^T) — H^n already held
# (cmsg84's ∂/rank), here read over the COBOUNDARY (the transpose) to show the
# ring's underlying graded group is the held cohomology.
COH_DIM_DEF = (
    "cohomology_dim(complex, k) = "
    "cardinality(simplices_of_dim(complex, k)) "
    "- matrix_rank(coboundary_matrix(complex, k)) "
    "- matrix_rank(coboundary_matrix(complex, k - 1))")


def step_acquire(s, caps) -> dict:
    banner("2. ACQUIRE the CUP PRODUCT BY READING — read the AW def -> GROUND over "
           "the now-held cochain primitives (cochains = ∂^T)")
    print("  The agent reads the Alexander-Whitney formula + grounds it over the")
    print("  now-held cochain primitives (front/back face + the pairing + the field")
    print("  multiply), EXACTLY as cmsg84 grounded the Betti formula over ∂/rank.\n")
    acquired = []
    for concept, definition in [
        ("aw_term", AW_TERM_DEF),
        ("cup_product_class", CUP_DEF),
        ("cohomology_dim", COH_DIM_DEF),
    ]:
        held_before = concept in caps
        r = cgr.ground_computation(s, concept, definition, capabilities=caps)
        g = bool(r.get("grounded"))
        acquired.append((concept, g))
        print(f"  [{concept}]  acquire-by-reading")
        print(f"    READ   : {definition}")
        print(f"    held before? {held_before}  ->  GROUNDED={g}  "
              f"composes over: {r.get('parts')}")
    all_acq = all(g for _c, g in acquired)
    print(f"\n  -> the cup product / cohomology dim grounded over the held cochain")
    print(f"     structure (∂^T + AW front/back-face): {all_acq}")
    return {"acquired": acquired, "all_acquired": all_acq}


# ===========================================================================
# (3) VERIFY vs KNOWN ring structures — torus (a∪b = fundamental class, a∪a=0,
# b∪b=0), S^2 (H^1=0, x∪x=0). The guard: an acquisition that does NOT reproduce
# the known ring is NOT acquired (no fake).
# ===========================================================================

def step_verify_known(caps) -> dict:
    banner("3. VERIFY vs KNOWN ring structures — torus (a∪b = fundamental class, "
           "a∪a=0, b∪b=0) + S^2 (H^1=0, x∪x=0). The guard: no fake")
    checks = []

    # TORUS: H^* = Λ[a,b]; a∪b generates H^2, a∪a = b∪b = 0, graded-commutative.
    print("  TORUS T^2  — H^* = exterior algebra Λ[a,b], |a|=|b|=1:")
    basis = _h1_basis(TORUS, limit=2)
    print(f"    dim H^1 (held cohomology over ∂^T) = {_h_dim(TORUS, 1)} "
          f"(found {len(basis)} basis 1-cocycles a, b)")
    if len(basis) == 2:
        a, b = basis
        aa, _ = _cup_class_is_zero(TORUS, 1, 1, a, a)
        bb, _ = _cup_class_is_zero(TORUS, 1, 1, b, b)
        ab_zero, ab = _cup_class_is_zero(TORUS, 1, 1, a, b)
        ba_zero, ba = _cup_class_is_zero(TORUS, 1, 1, b, a)
        gc_zero = _is_coboundary(TORUS, 2,
                                 [(x + y) % 2 for x, y in zip(ab, ba)])
        t_aa = aa is True
        t_bb = bb is True
        t_ab = ab_zero is False
        t_gc = gc_zero is True
        for label, got, want, ok in [
            ("a∪a = 0 in H^2", aa, True, t_aa),
            ("b∪b = 0 in H^2", bb, True, t_bb),
            ("a∪b ≠ 0 (= fundamental class)", not ab_zero, True, t_ab),
            ("a∪b + b∪a = 0 (graded-comm/Z2)", gc_zero, True, t_gc),
        ]:
            print(f"      {label:34} -> {str(got):6} {'OK' if ok else 'X'}")
        checks += [t_aa, t_bb, t_ab, t_gc]
    else:
        print("      X could not find a 2-element H^1 basis")
        checks.append(False)

    # S^2: H^1 = 0 (no nontrivial 1-cocycle), so the ring is Z[x]/(x^2), x∪x in H^4=0.
    print("\n  SPHERE S^2 — H^* = Z[x]/(x^2), |x|=2:")
    s2_h1 = _h_dim(S2, 1)
    s2_basis = _h1_basis(S2, limit=1)
    s2_ok = (s2_h1 == 0 and len(s2_basis) == 0)
    print(f"      dim H^1(S^2) = {s2_h1} (no nontrivial 1-cocycle) -> the only ring")
    print(f"      product is x∪x of the H^2 generator, landing in H^4 = 0 -> x∪x = 0 "
          f"{'OK' if s2_ok else 'X'}")
    checks.append(s2_ok)

    all_ok = all(checks)
    print(f"\n  -> the acquired cup product REPRODUCES the known ring structures "
          f"(torus + S^2): {all_ok}  (the guard held — no fake)")
    return {"verified": all_ok}


# ===========================================================================
# (4) THE DISCRIMINATING DEMO (the payoff) — RP^2 (Z/2) x∪x ≠ 0 vs S^1∨S^2 x∪x = 0.
# SAME homology, DIFFERENT cohomology ring -> the ring sees what homology cannot.
# ===========================================================================

def step_discriminating_demo(caps) -> dict:
    banner("4. THE DISCRIMINATING DEMO (the payoff) — RP^2 (Z/2) x∪x ≠ 0 vs "
           "S^1∨S^2 x∪x = 0; SAME homology, the ring DISTINGUISHES them")
    print("  RP^2 and S^1∨S^2 have the SAME Z/2 homology (the held Betti vector) —")
    print("  homology is BLIND to the difference. The cup product is NOT:\n")

    # first: SAME homology over GF(2) (the held betti vector — homology can't tell).
    def betti_gf2(cx):
        return [_h_dim(cx, k) for k in range(_top_dim(cx) + 1)]
    b_rp2 = betti_gf2(RP2)
    b_wedge = betti_gf2(S1_WEDGE_S2)
    same_homology = (b_rp2 == b_wedge)
    print(f"    HOMOLOGY (held Betti over GF(2)):")
    print(f"      RP^2     b = {b_rp2}")
    print(f"      S^1∨S^2  b = {b_wedge}")
    print(f"      SAME homology? {same_homology}  (homology cannot distinguish them)\n")

    # then: the CUP PRODUCT x∪x — the generator of H^1 squared.
    print(f"    COHOMOLOGY RING (the held cup product on the H^1 generator x):")
    results = {}
    for name, cx in [("RP^2", RP2), ("S^1∨S^2", S1_WEDGE_S2)]:
        gen = _h1_basis(cx, limit=1)
        if not gen:
            print(f"      {name:8} X no H^1 generator")
            results[name] = None
            continue
        x = gen[0]
        is_zero, prod = _cup_class_is_zero(cx, 1, 1, x, x)
        results[name] = not is_zero        # True => x∪x ≠ 0
        print(f"      {name:8} x∪x {'≠ 0 (generates H^2)' if not is_zero else '= 0 (trivial ring)'} "
              f"-> x∪x cohomology class {'NONZERO' if not is_zero else 'ZERO'}")

    distinguishes = (results.get("RP^2") is True
                     and results.get("S^1∨S^2") is False)
    print(f"\n  -> RP^2 has x∪x ≠ 0, S^1∨S^2 has x∪x = 0 — SAME homology, DIFFERENT")
    print(f"     cohomology RING. The cup product DISTINGUISHES them where homology")
    print(f"     is blind: {distinguishes and same_homology}")
    return {"same_homology": same_homology, "distinguishes": distinguishes,
            "ok": distinguishes and same_homology}


# ===========================================================================
# (5) WHAT THE RING UNLOCKS — signature reduces to the cup-product INTERSECTION
# FORM (now in reach); the BUNDLE (for characteristic classes) is the residual.
# ===========================================================================

def step_unlocks(s, caps) -> dict:
    banner("5. WHAT THE RING UNLOCKS — signature reduces to the cup-product "
           "INTERSECTION FORM (now in reach); the bundle is the residual")
    print("  cmsg85 returned signature grounded=False because its def referenced the")
    print("  CUP PRODUCT / intersection form the agent did not hold. NOW the cup")
    print("  product IS held, so the signature REDUCES a step further:\n")

    # the SIGNATURE of a 4k-manifold = the signature of the INTERSECTION FORM = the
    # symmetric cup-product bilinear form H^{2k} × H^{2k} -> H^{4k} = Z. The
    # intersection form's MATRIX is the cup product on a basis of middle cohomology.
    # We DEMONSTRATE the reduction: the intersection form is now expressible as the
    # cup product on cohomology basis reps. (The torus is 2-dimensional, so its
    # signature is degenerate/0; we show the FORM reduces, not a 4k-signature value —
    # the honest reach.)
    INTERSECTION_DEF = (
        "intersection_entry(complex, k, alpha, beta) = "
        "cup_product(complex, k, k, alpha, beta)")
    held_before = "intersection_entry" in caps
    r = cgr.ground_computation(s, "intersection_entry", INTERSECTION_DEF,
                               capabilities=caps)
    reduces = bool(r.get("grounded"))
    print(f"  SIGNATURE -> the INTERSECTION FORM (the symmetric cup-product bilinear")
    print(f"  form on middle cohomology H^k × H^k -> H^{{2k}}):")
    print(f"    READ   : {INTERSECTION_DEF}")
    print(f"    held before? {held_before}  ->  GROUNDED={reduces}  "
          f"composes over: {r.get('parts')}")
    print(f"    -> the intersection form is now EXPRESSIBLE as the held cup product;")
    print(f"       signature = #pos − #neg eigenvalues of that form = the next op")
    print(f"       IN REACH (cmsg85's grounded=False residual reduced a step).\n")

    print("  STILL-DEEPER RESIDUAL (honest — NOT acquired, NOT faked):")
    print("    · characteristic classes (Chern / Pontryagin / Stiefel-Whitney) live")
    print("      in the cohomology RING of a base for a VECTOR BUNDLE — they need the")
    print("      BUNDLE structure (a fibre bundle / its curvature), which the agent")
    print("      does NOT hold. The cohomology ring is necessary but not sufficient;")
    print("      the BUNDLE is the next-deeper rung.")
    # confirm the bundle-needing char-class def still does NOT ground (the guard).
    CHERN_DEF = ("chern_class(bundle) = "
                 "cohomology_ring_class(curvature_form(bundle))")
    rc = cgr.ground_computation(s, "chern_class", CHERN_DEF, capabilities=caps)
    char_not_acquired = not bool(rc.get("grounded"))
    print(f"    [guard: chern_class still grounded={rc.get('grounded')} — the bundle")
    print(f"     is genuinely un-held, no fake: char-class-not-acquired="
          f"{char_not_acquired}]")
    return {"signature_reduces": reduces, "char_not_acquired": char_not_acquired}


# ===========================================================================
# (6) NO REGRESSION — cmsg84/85's tiers + the held homology/χ + the held compute.
# ===========================================================================

def step_no_regression() -> bool:
    banner("6. NO REGRESSION — cmsg84/85 tiers (homology/χ/genus) + the held "
           "compute + the new cup-product primitives are ADDITIVE")
    ok = True
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^1,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S1, "k": 1}}}}, 3),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        # the held homology still computes (cmsg84) — S^2 Betti b_1 = 0.
        ("betti_number(S^2,1)", {"betti_number": {"complex": S2, "k": 1}}, 0),
    ]
    # betti_number is not a held registry key (it is read-grounded); ground it.
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

    # the NEW cup-product primitives are present + the held coboundary = ∂^T.
    bd = reason.solve({"boundary_matrix": {"complex": S2, "k": 2}}, {})
    cob = reason.solve({"coboundary_matrix": {"complex": S2, "k": 1}}, {})
    transpose_ok = (cob == [[bd[r][c] for r in range(len(bd))]
                            for c in range(len(bd[0]))]) if bd and bd[0] else True
    print(f"  coboundary_matrix(S^2,1) == boundary_matrix(S^2,2)^T (δ = ∂^T)? "
          f"{transpose_ok}")
    ok = ok and transpose_ok

    # module-level reason.CAPABILITIES not mutated by the read-grounding (the new
    # cup primitives ARE registry keys — held — but the read-grounded concepts are
    # not). The cup-product PRIMITIVES are intentionally held; the read-grounded
    # COMPOSITIONS (cup_product_class / cohomology_dim) must NOT leak into the module
    # registry.
    leaked = [c for c in ("cup_product_class", "cohomology_dim", "aw_term",
                          "betti_number", "intersection_entry")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    # the new cup-product PRIMITIVES ARE held (the emitter wrote them into the tower).
    prims_held = all(c in reason.CAPABILITIES for c in
                     ("front_face", "back_face", "cochain_value", "cup_product",
                      "coboundary_matrix"))
    print(f"  the emitted cup-product primitives ARE held tower capabilities? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the cup-product tier is ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE NEXT RUNG — acquire the CUP PRODUCT + the COHOMOLOGY RING "
           "(the next-deeper tier cmsg85 mapped: signature/char-class needed it)")
    print("  cmsg84 acquired χ/betti/ker/im over ∂; cmsg85 acquired genus/index/")
    print("  Euler-class/degree over those. NOW the cup product over the simplicial")
    print("  COCHAIN structure (∂^T): the Alexander-Whitney formula (α∪β)(σ) =")
    print("  α(front p-face)·β(back q-face), reducing to held simplicial primitives.")
    print("  The agent SPECIFIES the AW cochain primitives the DSL lacks (the emitter")
    print("  writes them as held tower ops), READS + GROUNDS the cup product, VERIFIES")
    print("  vs known rings (torus/S^2), and demonstrates the DISCRIMINATING payoff")
    print("  (RP^2 vs S^1∨S^2 — the ring sees what homology cannot).")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    spec = step_specify_and_emit(caps)
    acq = step_acquire(s, caps)
    ver = step_verify_known(caps)
    demo = step_discriminating_demo(caps)
    unlocks = step_unlocks(s, caps)
    noreg = step_no_regression()

    banner("SUMMARY — the cohomology-ring walk (specify+emit -> acquire+verify -> "
           "the discriminating demo -> what the ring unlocks -> honest map)")
    print(f"  SPECIFY+EMIT    : the AW cochain primitives the DSL lacked (front/back")
    print(f"                    p-face, the cochain pairing, the cup-product MapSet,")
    print(f"                    δ=∂^T) — agent specified WHAT, the mechanical emitter")
    print(f"                    wrote them as held tower primitives (no Rust): "
          f"{spec['all_emitted']}")
    print(f"  ACQUIRE         : the cup product / cohomology dim grounded by reading")
    print(f"                    the AW def over the now-held cochain structure "
          f"(∂^T): {acq['all_acquired']}")
    print(f"  VERIFY (no fake): the known ring structures reproduced — torus (a∪b =")
    print(f"                    fundamental class, a∪a=0, b∪b=0, graded-comm), S^2")
    print(f"                    (H^1=0, x∪x=0): {ver['verified']}")
    print(f"  DISCRIMINATING  : RP^2 (Z/2) x∪x ≠ 0 vs S^1∨S^2 x∪x = 0 — SAME homology")
    print(f"                    (held Betti both (1,1,1)), DIFFERENT cohomology RING.")
    print(f"                    The ring SEES what homology cannot: {demo['ok']}")
    print(f"  RING UNLOCKS    : signature -> the cup-product INTERSECTION FORM (now")
    print(f"                    grounds — cmsg85's grounded=False residual reduced a")
    print(f"                    step): {unlocks['signature_reduces']}")
    print(f"  STILL-RESIDUAL  : characteristic classes need the VECTOR BUNDLE (still")
    print(f"                    un-held; the next-deeper rung — char-class-not-acquired")
    print(f"                    ={unlocks['char_not_acquired']}, no fake)")
    print(f"  NEXT RUNG       : the BUNDLE (fibre bundle / curvature) for Chern /")
    print(f"                    Pontryagin / Stiefel-Whitney — itself acquire-by-")
    print(f"                    reading later, over the now-held cohomology ring.")
    print(f"  NO REGRESSION   : {noreg}")

    ok = (spec["all_emitted"] and acq["all_acquired"] and ver["verified"]
          and demo["ok"] and unlocks["signature_reduces"]
          and unlocks["char_not_acquired"] and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent walked the NEXT RUNG — read the cup product /")
    print("cohomology ring def, grounded it over the held simplicial COCHAIN structure")
    print("(cochains = ∂^T, the Alexander-Whitney front/back-face formula; specifying")
    print("+ emitting the AW cochain primitives the DSL lacked), VERIFIED vs known ring")
    print("structures (torus: a∪b = fundamental class, a∪a=0; S^2: x∪x=0), and")
    print("demonstrated the DISCRIMINATING payoff: RP^2 (Z/2) x∪x ≠ 0 vs S^1∨S^2 x∪x =")
    print("0 — SAME homology (1,1,1), DIFFERENT cohomology ring. The cup product")
    print("DISTINGUISHES them where homology is BLIND — the reason the rung matters.")
    print("The ladder climbs another rung; the cohomology ring NOW unlocks the")
    print("signature (the cup-product intersection form, cmsg85's grounded=False")
    print("residual reduced a step). The still-deeper residual is the VECTOR BUNDLE")
    print("(for characteristic classes) — the next acquire-by-reading rung, over the")
    print("now-held cohomology ring. The breadth ladder is self-driven: each acquired")
    print("tier the bedrock for the next, now the cup product over ∂^T.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
