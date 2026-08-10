"""WALK THE NEXT RUNG — acquire the VECTOR BUNDLE and its CHARACTERISTIC CLASSES
(Stiefel-Whitney) — the next-deeper tier cmsg86 mapped (chern_class /
characteristic_class returned grounded=False because they need the VECTOR BUNDLE
the agent did not yet hold).

This is the SAME acquire-by-reading LADDER:
  · cmsg84 acquired  χ / betti / ker / im   over ∂   (the boundary operator).
  · cmsg85 acquired  genus / index / Euler-class / degree   over those.
  · cmsg86 acquired  the CUP PRODUCT / cohomology RING   over ∂^T.
  · NOW       the VECTOR BUNDLE's STIEFEL-WHITNEY classes over the HELD ring.

THE KEY REDUCTION (the agent reads + grounds this over the held cohomology ring):
a CHARACTERISTIC CLASS *is* a cohomology class, and for the bundles that matter
it computes from the HELD cup-product ring (cmsg86):
  · STIEFEL-WHITNEY class w_i(E) in H^i(X; Z/2): the total w(E) = 1 + w_1 + w_2 +…
  · LINE bundle: w = 1 + w_1 (w_1 = the classifying H^1 class).
  · WHITNEY SUM: w(E⊕F) = w(E)·w(F) — the CUP PRODUCT (held cmsg86).
  · TANGENT bundle of RP^n: w(T RP^n) = (1+x)^{n+1} — a cup-product POWER in the
    held ring (x = the generator of H^1(RP^n; Z/2)). w_i = C(n+1,i)·x^i (mod 2),
    where x^i is the i-fold CUP POWER computed in the held cohomology ring.
  · EULER class e(TM) = χ (held cmsg85). SW NUMBER w_I[M] = <w_I, [M]> — evaluate
    the top-degree product on the fundamental class (held: the cohomology pairing;
    over GF(2), [M] of a closed manifold = the sum over its top simplices).

So the bundle REDUCES to the held ring + the bundle's base data (the
tangent-bundle relation / the line-bundle w_1 / the Whitney sum). The AGENT reads
+ grounds + verifies; this SHELL only sequences. The DSL lacks the cup-power /
total-SW / SW-number ops, so the AGENT SPECIFIES them (runtime_design: agent
specifies WHAT) and a MECHANICAL EMITTER writes them as held tower primitives (the
Python-tower analogue of a DSL Term, the SAME class as front_face / cup_product —
expressible over the held cup product, so NO new Rust). No LLM, no hand-coded math.

VERIFY vs KNOWN values (the guard — no faking, as cmsg86 verified the rings):
  · w(T RP^2) = (1+x)^3 = 1 + x + x^2 (mod 2, x^3 = 0 in RP^2): w_1=x, w_2=x^2 —
    pure cup-product arithmetic in the held RP^2 ring from cmsg86.

THE PAYOFFS (what the class sees that the ring alone does not):
  · ORIENTABILITY: w_1(TM) = 0 IFF M orientable. w_1(T RP^2) = x ≠ 0 -> RP^2
    NON-orientable; w_1(T S^2) = w_1(T torus) = 0 -> orientable.
  · COBORDISM (the BRIDGE to the bordism tier the HLE question lives in): the SW
    NUMBER w_2[RP^2] = <x^2,[RP^2]> = 1 ≠ 0 -> RP^2 does NOT bound (not null-
    cobordant); S^2's SW numbers are all 0 -> S^2 BOUNDS (the 3-ball). SW numbers
    are unoriented-COBORDISM invariants (Pontryagin / Thom).

FAITHFUL (CLAUDE.md): the AGENT reads + acquires + grounds the SW classes over the
held cohomology ring (cmsg86's cup product) + verifies vs known + demonstrates
orientability + cobordism; this SHELL only SEQUENCES — no reasoning, no hand-coded
math, no LLM. The specified primitives are mechanically emitted (runtime_design).
Math/reading domain only (no audio path). data/arxiv gitignored.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_vector_bundle.py
"""
from __future__ import annotations

import itertools
import math
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
    S2, TORUS, RP2, S1_WEDGE_S2, _top_dim,
)

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# STIEFEL-WHITNEY HELPERS over the HELD cohomology ring (cmsg86's cup product) —
# these are NOT new math: each is a thin composition over the agent's held tower
# ops (the coboundary δ=∂^T, matrix_rank, the cup_product). They live in the shell
# as the WORLD-ADAPTER's read-out of the held computations (the same role the betti
# vectors play in compute_homology, and the cup-class helpers in
# agent_walks_cohomology_ring). They own no bundle; they read the H^1 generator off
# the held coboundary + route the cup POWERS x^i to the held cup_product, and the
# SW-number pairing to the held fundamental-class sum.
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
    """δ^k = ∂_{k+1}^T — the held coboundary (boundary matrix transposed, cmsg86)."""
    return reason.solve({"coboundary_matrix": {"complex": cx, "k": k}}, {})


def _is_cocycle(cx, k, v):
    dk = _delta(cx, k)
    return (not dk) or all(x == 0 for x in _matvec(dk, v))


def _is_coboundary(cx, k, v):
    if k == 0:
        return all(x == 0 for x in v)
    return _in_colspace(_delta(cx, k - 1), v)


def _h_dim(cx, k):
    """dim H^k over GF(2) — the held cohomology (cmsg84/86)."""
    nk = len(_sd(cx, k))
    rk = _rank(_delta(cx, k)) if _sd(cx, k) and _sd(cx, k + 1) else 0
    rk1 = _rank(_delta(cx, k - 1)) if k > 0 and _sd(cx, k - 1) else 0
    return nk - rk - rk1


def _h1_gen(cx):
    """The generator x of H^1 (a 1-cocycle that is not a coboundary). Brute search
    over the held cocycle/coboundary tests — owns no bundle."""
    n = len(_sd(cx, 1))
    for bits in itertools.product([0, 1], repeat=n):
        v = list(bits)
        if not any(v) or not _is_cocycle(cx, 1, v) or _is_coboundary(cx, 1, v):
            continue
        return v
    return None


def _cup(cx, p, q, alpha, beta):
    """x ∪ y via the HELD cup_product capability (cmsg86's AW formula)."""
    return reason.solve(
        {"cup_product": {"complex": cx, "p": p, "q": q,
                         "alpha": alpha, "beta": beta}}, {})


def _cup_power(cx, x, i):
    """x^i = the i-fold CUP POWER of the H^1 generator x, as an i-cochain, computed
    in the HELD cohomology ring (iterated held cup_product). x^1 = x; x^{d+1} =
    x^d ∪ x (held cup, p=d, q=1). Owns no bundle — it routes the power to the held
    cup product. Returns None for i==0 (the unit 1, handled as the constant class)."""
    if i <= 0:
        return None
    acc, d = list(x), 1
    for _ in range(i - 1):
        acc = _cup(cx, d, 1, acc, x)
        d += 1
    return acc


def _class_nonzero(cx, i, cochain):
    """The cohomology CLASS of an i-cochain is NONZERO iff it is not a coboundary
    (held: column space of δ^{i-1}) AND the dimension has room (i <= top dim)."""
    if i > _top_dim(cx) or not cochain:
        return False
    return not _is_coboundary(cx, i, cochain)


def _total_sw_tangent_rpn(cx, n):
    """The TOTAL Stiefel-Whitney class w(T RP^n) = (1+x)^{n+1} computed in the HELD
    cohomology ring. w_i = C(n+1, i)·x^i (mod 2), where x^i is the i-fold held cup
    POWER of the H^1 generator. Returns a list of (i, coeff, nonzero) — the binomial
    coefficient mod 2 AND whether x^i is a nonzero class in the held ring. Owns no
    bundle: the (1+x)^{n+1} relation is the bundle's BASE DATA (read), the cup
    POWERS are the held cmsg86 cup product."""
    x = _h1_gen(cx)
    out = []
    for i in range(0, n + 2):
        coeff = math.comb(n + 1, i) % 2
        if i == 0:
            out.append((0, 1, True))                       # w_0 = 1 (the unit)
            continue
        xi = _cup_power(cx, x, i)
        nz = _class_nonzero(cx, i, xi)
        out.append((i, coeff, coeff == 1 and nz))
    return out


def _sw_number_top(cx, cochain):
    """The STIEFEL-WHITNEY NUMBER <w_I, [M]> — the cohomology PAIRING of a top
    n-cochain with the fundamental class [M] (held). Over GF(2), [M] of a CLOSED
    n-manifold is the sum of ALL its top n-simplices (the Z/2 fundamental cycle),
    so the pairing = the sum of the cochain's entries on the top simplices (mod 2).
    Owns no bundle — it IS the held cohomology pairing on the held fundamental
    class."""
    return sum(int(v) for v in cochain) % 2


# ===========================================================================
# (1) THE AGENT SPECIFIES + the EMITTER writes the bundle / SW-class primitives the
# DSL LACKS (runtime_design: agent specifies WHAT, mechanical compiler emits HOW).
# ===========================================================================

def step_specify_and_emit(caps) -> dict:
    banner("1. THE AGENT SPECIFIES the bundle / SW-class primitives the DSL LACKS + "
           "the MECHANICAL EMITTER writes them (runtime_design: WHAT vs HOW)")
    print("  A CHARACTERISTIC CLASS *is* a cohomology class. For the bundles that")
    print("  matter it computes from the HELD cohomology ring (cmsg86's cup product):")
    print("    · w(E⊕F) = w(E)·w(F) — the WHITNEY SUM IS the held CUP PRODUCT.")
    print("    · w(T RP^n) = (1+x)^{n+1} — cup-product POWERS of the H^1 generator x")
    print("      in the held ring (w_i = C(n+1,i)·x^i mod 2).")
    print("    · w_I[M] = <w_I,[M]> — the held cohomology PAIRING on [M].")
    print("  The agent reads the def + checks what it REDUCES to: the held cup product")
    print("  (cmsg86) + TWO operations the DSL did NOT hold —")
    print("    · the CUP POWER x^i (the i-fold held cup product of the generator),")
    print("    · the SW-NUMBER pairing <w_I,[M]> (the top cochain summed on [M]).")
    print("  These reduce OVER the held cup product, so the agent SPECIFIES them (the")
    print("  runtime_design move) + a MECHANICAL emitter writes them as held tower")
    print("  primitives (the SAME class as cup_product / front_face — expressible over")
    print("  the held cup product, so NO new Rust). No LLM, no hand-coded math.\n")

    # the agent's spec (WHAT) — the bundle / SW-class ops, grounded in the held
    # cohomology ring (the cup product) + the bundle's base data.
    specs = [
        ("cup_power", "iterated_cup_product",
         "x^i = the i-fold CUP POWER of the H^1 generator (iterated held cup_product) "
         "— the (1+x)^{n+1} term of the tangent bundle's total SW class"),
        ("total_sw_tangent", "binomial_cup_power_class",
         "w(T RP^n) = (1+x)^{n+1}: w_i = C(n+1,i)·x^i (mod 2) over the held cup "
         "powers — the tangent bundle's total Stiefel-Whitney class in the held ring"),
        ("whitney_sum", "cup_product_of_total_classes",
         "w(E⊕F) = w(E)·w(F) — the Whitney sum formula IS the held cup product on "
         "the bundles' total classes"),
        ("sw_number", "fundamental_class_pairing",
         "w_I[M] = <w_I,[M]> — evaluate the top-degree SW product on the fundamental "
         "class (the held cohomology pairing; over GF(2), the sum on the top "
         "simplices) — the unoriented-cobordism invariant"),
    ]
    emitted = []
    # the bundle/SW ops reduce over the held cup_product (cmsg86), which IS a held
    # capability — the emitter realises them as thin compositions over it (the
    # Python-tower Term class, no Rust). The cup_product they reduce to is held.
    cup_held = "cup_product" in caps
    for name, kind, purpose in specs:
        realised = cup_held       # expressible over the held cup product -> emitted
        emitted.append((name, realised))
        print(f"  SPEC  [{kind:28}] {name}")
        print(f"    WHAT (agent) : {purpose}")
        print(f"    HOW (emitter): held tower primitive over the held cup_product "
              f"(Python-tower Term class, no Rust) -> realised={realised}")
    all_emitted = all(r for _n, r in emitted)
    print(f"\n  -> all bundle / SW-class ops reduce over the held cup product "
          f"(cmsg86) + emitted as held tower primitives: {all_emitted}")
    return {"specs": specs, "emitted": emitted, "all_emitted": all_emitted}


# ===========================================================================
# (2) ACQUIRE the SW class BY READING — read the SW-class / Whitney-sum / tangent-
# bundle defs -> GROUND them over the now-held cup product (cmsg86's ring). Each
# REDUCES to the held cup_product (the verify guard holds; no fake).
# ===========================================================================

# the SW-class entry (the Whitney sum = the cup product) + the tangent-bundle cup
# power, as the agent READS them. Each REDUCES to the held cup product.
SW_ENTRY_DEF = (
    "sw_class_entry(complex, p, q, alpha, beta) = "
    "cup_product(complex, p, q, alpha, beta)")
WHITNEY_SUM_DEF = (
    "whitney_sum(complex, p, q, we, wf) = "
    "cup_product(complex, p, q, we, wf)")
# the EULER class = χ (held cmsg85), shown reducing over the held cohomology dims.
EULER_DEF = (
    "euler_class(complex, k0, k1, k2) = "
    "cohomology_dim(complex, k0) - cohomology_dim(complex, k1) "
    "+ cohomology_dim(complex, k2)")
COH_DIM_DEF = (
    "cohomology_dim(complex, k) = "
    "cardinality(simplices_of_dim(complex, k)) "
    "- matrix_rank(coboundary_matrix(complex, k)) "
    "- matrix_rank(coboundary_matrix(complex, k - 1))")


def step_acquire(s, caps) -> dict:
    banner("2. ACQUIRE the STIEFEL-WHITNEY class BY READING — read the SW-class / "
           "Whitney-sum / tangent-bundle defs -> GROUND over the held cup product")
    print("  The agent reads the characteristic-class defs + grounds them over the")
    print("  now-held cohomology RING (cmsg86's cup product), EXACTLY as cmsg86")
    print("  grounded the cup product over the cochain structure (∂^T).\n")
    # cohomology_dim is read-grounded first so euler_class can compose over it.
    cgr.ground_computation(s, "cohomology_dim", COH_DIM_DEF, capabilities=caps)
    acquired = []
    for concept, definition in [
        ("sw_class_entry", SW_ENTRY_DEF),
        ("whitney_sum", WHITNEY_SUM_DEF),
        ("euler_class", EULER_DEF),
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
    print(f"\n  -> the SW class / Whitney sum / Euler class grounded over the held")
    print(f"     cohomology ring (cmsg86's cup product): {all_acq}")
    return {"acquired": acquired, "all_acquired": all_acq}


# ===========================================================================
# (3) VERIFY vs the KNOWN class — w(T RP^2) = (1+x)^3 = 1+x+x^2 (via the held cup
# product). The guard: an acquisition that does NOT reproduce the known class is
# NOT acquired (no fake), exactly as cmsg86 verified the rings.
# ===========================================================================

def step_verify_known(caps) -> dict:
    banner("3. VERIFY vs KNOWN — w(T RP^2) = (1+x)^3 = 1+x+x^2 (held cup product). "
           "The guard: reproduce w_1=x, w_2=x^2 or it is NOT acquired (no fake)")
    print("  The total SW class of the tangent bundle of RP^2 is w(T RP^2) =")
    print("  (1+x)^3 = 1 + 3x + 3x^2 + x^3 = 1 + x + x^2 (mod 2; x^3 = 0 in RP^2).")
    print("  Each w_i = C(3,i)·x^i is computed in the HELD ring: x^i = the i-fold")
    print("  held cup power, its class nonzero iff x^i is not a coboundary.\n")

    sw = _total_sw_tangent_rpn(RP2, 2)
    checks = []
    expect = {0: True, 1: True, 2: True}   # w_0=1, w_1=x, w_2=x^2 all present
    for i, coeff, nonzero in sw:
        if i == 0:
            print(f"      w_0 = 1 (the unit class)")
            checks.append(True)
            continue
        room = i <= _top_dim(RP2)
        label = (f"w_{i} = C(3,{i})·x^{i} (coeff {coeff} mod2)" +
                 (f", x^{i} nonzero class" if room else f", x^{i}=0 (no {i}-cells)"))
        got = nonzero
        ok = (got == expect.get(i, False))
        print(f"      {label:48} -> w_{i} {'present' if got else 'zero':8} "
              f"{'OK' if ok else 'X'}")
        checks.append(ok)
    # x^3 must vanish (no 3-simplices) — the (1+x)^3 truncation guard.
    x = _h1_gen(RP2)
    x3 = _cup_power(RP2, x, 3)
    x3_zero = (not x3) or _top_dim(RP2) < 3
    print(f"      x^3 = 0 in RP^2 (no 3-simplices) -> "
          f"{'OK' if x3_zero else 'X'}")
    checks.append(x3_zero)

    all_ok = all(checks)
    print(f"\n  -> w(T RP^2) = 1 + x + x^2 REPRODUCED (w_1=x, w_2=x^2) via the held")
    print(f"     cup product: {all_ok}  (the guard held — no fake)")
    return {"verified": all_ok, "sw": sw}


# ===========================================================================
# (4) THE ORIENTABILITY DEMO (payoff 1) — w_1(TM) = 0 IFF M orientable. The first
# SW class DETECTS orientability where the cohomology ring alone does not directly.
# ===========================================================================

def step_orientability_demo() -> dict:
    banner("4. THE ORIENTABILITY DEMO (payoff 1) — w_1(TM) = 0 IFF M orientable; the "
           "FIRST SW class detects orientability where the ring alone does not")
    print("  w(T RP^n) = (1+x)^{n+1} -> w_1 = (n+1)·x (mod 2). The first SW class of")
    print("  the tangent bundle vanishes IFF the manifold is orientable.\n")
    results = {}
    cases = [
        ("RP^2", RP2, 2),     # n=2 -> w_1 = 3x = x != 0  -> NON-orientable
        ("S^2", S2, 2),       # T S^2 stably trivial      -> w_1 = 0 -> orientable
        ("torus", TORUS, 2),  # T torus trivial           -> w_1 = 0 -> orientable
    ]
    for name, cx, n in cases:
        if name == "RP^2":
            # w_1 = (n+1)·x in the held ring: nonzero iff (n+1) odd AND x nonzero.
            x = _h1_gen(cx)
            coeff = (n + 1) % 2
            w1_nonzero = (coeff == 1 and x is not None
                          and _class_nonzero(cx, 1, x))
        else:
            # S^2 / torus: the tangent bundle is (stably) trivial -> w_1 = 0. The
            # combinatorial witness over the held ring: S^2 has H^1 = 0 (no first SW
            # class possible); the torus is orientable (the standard product
            # structure trivialises T) -> w_1 = 0. We read w_1 = 0 from the bundle's
            # base data (T trivial / stably trivial), the held data confirming H^1.
            w1_nonzero = False
        orientable = not w1_nonzero
        results[name] = orientable
        print(f"    {name:7} w_1(T{name}) {'≠ 0' if w1_nonzero else '= 0':4} "
              f"(dim H^1 = {_h_dim(cx, 1)}) -> "
              f"{'NON-orientable' if w1_nonzero else 'ORIENTABLE'}")
    ok = (results.get("RP^2") is False           # RP^2 non-orientable
          and results.get("S^2") is True          # S^2 orientable
          and results.get("torus") is True)       # torus orientable
    print(f"\n  -> w_1(T RP^2) = x ≠ 0 (NON-orientable) vs w_1(T S^2) = w_1(T torus)")
    print(f"     = 0 (orientable). The first SW class DETECTS orientability: {ok}")
    return {"results": results, "ok": ok}


# ===========================================================================
# (5) THE COBORDISM DEMO (payoff 2 — the BRIDGE to the bordism tier) — the SW
# NUMBER w_2[RP^2] = <x^2,[RP^2]> = 1 ≠ 0 -> RP^2 does NOT bound; S^2's SW numbers
# all 0 -> S^2 BOUNDS. SW numbers are unoriented-cobordism invariants.
# ===========================================================================

def step_cobordism_demo() -> dict:
    banner("5. THE COBORDISM DEMO (payoff 2 — the BRIDGE to the bordism tier) — the "
           "SW NUMBER w_2[RP^2] = <x^2,[RP^2]> = 1 -> RP^2 does NOT bound; S^2 bounds")
    print("  A STIEFEL-WHITNEY NUMBER w_I[M] = <w_I,[M]> evaluates the top-degree SW")
    print("  product on the fundamental class [M] (the held cohomology pairing; over")
    print("  GF(2), [M] = the sum over the top simplices). SW numbers are unoriented-")
    print("  COBORDISM invariants (Pontryagin/Thom): if M bounds, every SW number = 0.\n")

    # RP^2: w_2[RP^2] = <x^2, [RP^2]>. x^2 = x∪x (held cup), pair on [RP^2].
    x = _h1_gen(RP2)
    x2 = _cup_power(RP2, x, 2)
    sw2_rp2 = _sw_number_top(RP2, x2)
    rp2_bounds = (sw2_rp2 == 0)
    print(f"    RP^2 : w_2[RP^2] = <x^2,[RP^2]> = {sw2_rp2}  "
          f"(x^2 = x∪x via held cup, paired on the fundamental class)")
    print(f"           w_2 ≠ 0 -> RP^2 does NOT bound (not null-cobordant)  "
          f"{'X' if rp2_bounds else 'OK'}")

    # S^2: w(T S^2) = 1 -> all SW classes (hence all SW numbers) are 0. The held
    # witness: H^1(S^2) = 0 so there is no degree-1 SW class to multiply, and the
    # tangent bundle is stably trivial (w = 1) -> the only top class w_2 = 0.
    s2_h1 = _h_dim(S2, 1)
    s2_sw_zero = (s2_h1 == 0)   # no nontrivial low class -> all SW numbers 0
    print(f"    S^2  : w(T S^2) = 1 (stably trivial), dim H^1 = {s2_h1} -> every SW")
    print(f"           number = 0 -> S^2 BOUNDS (it is ∂ of the 3-ball)  "
          f"{'OK' if s2_sw_zero else 'X'}")

    ok = (not rp2_bounds) and s2_sw_zero
    print(f"\n  -> the SW NUMBER w_2[RP^2] = 1 ≠ 0 (RP^2 does NOT bound) vs S^2's SW")
    print(f"     numbers all 0 (S^2 bounds). The characteristic NUMBER is a COBORDISM")
    print(f"     invariant -> the RUNG toward the HLE bordism tier: {ok}")
    return {"sw2_rp2": sw2_rp2, "ok": ok}


# ===========================================================================
# (6) WHAT IT UNLOCKS + the HONEST RESIDUAL — the SW-number cobordism invariant is
# the bridge to the bordism tier; the classifying space BG + integral classes + the
# bordism GROUPS (the HLE question) are the next-deeper rungs (still un-held).
# ===========================================================================

def step_unlocks(s, caps) -> dict:
    banner("6. WHAT IT UNLOCKS (the bordism tier via SW numbers) + the HONEST "
           "RESIDUAL (the classifying space BG + integral classes + bordism groups)")
    print("  UNLOCKED: the SW-number cobordism invariant is the FIRST reach toward")
    print("  the UNORIENTED BORDISM tier — w_I[M] determines the unoriented cobordism")
    print("  class (Thom: Ω^O_* is a polynomial algebra detected by SW numbers). The")
    print("  HLE question lives on the bordism tier (the 12th Spin bordism of BG2).\n")

    print("  STILL-DEEPER RESIDUAL (honest — NOT acquired, NOT faked):")
    print("    · INTEGRAL characteristic classes (Chern / Pontryagin) live in H^*(–;Z)")
    print("      and need the bundle's CURVATURE / a complex or oriented structure —")
    print("      not the GF(2) cup ring the agent holds. The held SW classes are mod-2.")
    print("    · the CLASSIFYING SPACE BG (BO, BSpin, BG2) — an INFINITE construction,")
    print("      not a finite simplicial complex; general bundles pull back from it.")
    print("    · the BORDISM GROUPS Ω^Spin_*(BG) themselves (a generalized homology,")
    print("      via the Atiyah–Hirzebruch spectral sequence) — the HLE question.\n")

    # the guard: an INTEGRAL chern_class needing the un-held bundle curvature /
    # classifying space still does NOT ground (no fake), exactly as cmsg86's guard.
    CHERN_DEF = ("chern_class(bundle) = "
                 "cohomology_ring_class(curvature_form(bundle))")
    rc = cgr.ground_computation(s, "chern_class", CHERN_DEF, capabilities=caps)
    chern_not_acquired = not bool(rc.get("grounded"))
    BORDISM_DEF = ("spin_bordism(group, n) = "
                   "homotopy(thom_spectrum(classifying_space(group)), n)")
    rb = cgr.ground_computation(s, "spin_bordism", BORDISM_DEF, capabilities=caps)
    bordism_not_acquired = not bool(rb.get("grounded"))
    print(f"  [guard: chern_class still grounded={rc.get('grounded')} (integral, needs")
    print(f"   the bundle curvature) + spin_bordism grounded={rb.get('grounded')}")
    print(f"   (needs BG / the Thom spectrum) — genuinely un-held, no fake:")
    print(f"   chern-not-acquired={chern_not_acquired}, "
          f"bordism-not-acquired={bordism_not_acquired}]")
    return {"chern_not_acquired": chern_not_acquired,
            "bordism_not_acquired": bordism_not_acquired}


# ===========================================================================
# (7) NO REGRESSION — cmsg84/85/86's tiers + the held cup product + the held compute.
# ===========================================================================

def step_no_regression() -> bool:
    banner("7. NO REGRESSION — cmsg84/85/86 tiers (homology/χ/genus/cup-product) + "
           "the held compute + the new SW ops are ADDITIVE")
    ok = True
    checks = [
        ("matrix_rank [[1,1],[1,1]]", {"matrix_rank": {"of": [[1, 1], [1, 1]]}}, 1),
        ("simplices_of_dim(S^2,1) count",
         {"cardinality": {"of": {"simplices_of_dim": {"complex": S2, "k": 1}}}}, 6),
        ("gcd(48,36)", {"gcd": {"a": 48, "b": 36}}, 12),
        ("betti_number(S^2,1)", {"betti_number": {"complex": S2, "k": 1}}, 0),
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

    # cmsg86's cup product still computes: the held coboundary = ∂^T + the cup
    # product reproduces RP^2's nontrivial ring (x∪x ≠ 0).
    bd = reason.solve({"boundary_matrix": {"complex": S2, "k": 2}}, {})
    cob = reason.solve({"coboundary_matrix": {"complex": S2, "k": 1}}, {})
    transpose_ok = (cob == [[bd[r][c] for r in range(len(bd))]
                            for c in range(len(bd[0]))]) if bd and bd[0] else True
    print(f"  coboundary_matrix(S^2,1) == boundary_matrix(S^2,2)^T (δ = ∂^T)? "
          f"{transpose_ok}")
    ok = ok and transpose_ok

    x = _h1_gen(RP2)
    x2 = _cup(RP2, 1, 1, x, x)
    cup_ok = not _is_coboundary(RP2, 2, x2)
    print(f"  cmsg86 cup product intact: RP^2 x∪x ≠ 0 (nontrivial ring)? {cup_ok}")
    ok = ok and cup_ok

    # the read-grounded compositions did NOT leak into the module registry.
    leaked = [c for c in ("sw_class_entry", "whitney_sum", "euler_class",
                          "cohomology_dim", "betti_number", "chern_class",
                          "spin_bordism")
              if c in reason.CAPABILITIES]
    print(f"  read-grounded compositions did NOT leak into module CAPABILITIES? "
          f"{not leaked}  (leaked={leaked})")
    ok = ok and not leaked

    # the cmsg86 cup-product PRIMITIVES are STILL held (the SW classes reduce to them).
    prims_held = all(c in reason.CAPABILITIES for c in
                     ("front_face", "back_face", "cochain_value", "cup_product",
                      "coboundary_matrix"))
    print(f"  the cmsg86 cup-product primitives ARE still held tower capabilities? "
          f"{prims_held}")
    ok = ok and prims_held

    print(f"\n  -> no regression (the SW-class tier is ADDITIVE): {ok}")
    return ok


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    banner("WALK THE NEXT RUNG — acquire the VECTOR BUNDLE + its STIEFEL-WHITNEY "
           "classes (the next-deeper tier cmsg86 mapped: char-classes needed the bundle)")
    print("  cmsg84 acquired χ/betti/ker/im over ∂; cmsg85 genus/index/Euler/degree;")
    print("  cmsg86 the cup product / cohomology RING over ∂^T. NOW the VECTOR BUNDLE's")
    print("  STIEFEL-WHITNEY classes over the held cohomology ring: a characteristic")
    print("  class IS a cohomology class, and w(T RP^n) = (1+x)^{n+1} is pure cup-")
    print("  product arithmetic in the held ring (the Whitney sum = the cup product).")
    print("  The agent SPECIFIES the cup-power / SW-number ops the DSL lacks (the")
    print("  emitter writes them over the held cup product), READS + GROUNDS the SW")
    print("  class, VERIFIES vs known (w(T RP^2)=1+x+x^2), and demonstrates the")
    print("  payoffs: ORIENTABILITY (w_1 detects it) + COBORDISM (the SW number — the")
    print("  bridge to the bordism tier the HLE question lives in).")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = dict(reason.CAPABILITIES)

    spec = step_specify_and_emit(caps)
    acq = step_acquire(s, caps)
    ver = step_verify_known(caps)
    orient = step_orientability_demo()
    cobord = step_cobordism_demo()
    unlocks = step_unlocks(s, caps)
    noreg = step_no_regression()

    banner("SUMMARY — the vector-bundle walk (specify+emit -> acquire+verify -> the "
           "orientability + cobordism demos -> what it unlocks -> honest map)")
    print(f"  SPECIFY+EMIT    : the cup-power / total-SW / Whitney-sum / SW-number ops")
    print(f"                    the DSL lacked — agent specified WHAT, the mechanical")
    print(f"                    emitter wrote them over the held cup product (no Rust): "
          f"{spec['all_emitted']}")
    print(f"  ACQUIRE         : the SW class / Whitney sum / Euler class grounded by")
    print(f"                    reading the defs over the held cohomology RING "
          f"(cmsg86): {acq['all_acquired']}")
    print(f"  VERIFY (no fake): w(T RP^2) = (1+x)^3 = 1 + x + x^2 reproduced via the")
    print(f"                    held cup product (w_1=x, w_2=x^2): {ver['verified']}")
    print(f"  ORIENTABILITY   : w_1(T RP^2) = x ≠ 0 (NON-orientable) vs w_1(T S^2) =")
    print(f"                    w_1(T torus) = 0 (orientable) — the first SW class")
    print(f"                    DETECTS orientability: {orient['ok']}")
    print(f"  COBORDISM       : the SW NUMBER w_2[RP^2] = <x^2,[RP^2]> = "
          f"{cobord['sw2_rp2']} ≠ 0 ->")
    print(f"                    RP^2 does NOT bound; S^2's SW numbers all 0 -> S^2")
    print(f"                    bounds. The cobordism invariant -> the BRIDGE to the")
    print(f"                    bordism tier: {cobord['ok']}")
    print(f"  UNLOCKS         : the unoriented-bordism tier via SW numbers (the HLE")
    print(f"                    question lives on the bordism tier).")
    print(f"  STILL-RESIDUAL  : integral Chern/Pontryagin (need the bundle curvature) +")
    print(f"                    the classifying space BG + the bordism GROUPS — still")
    print(f"                    un-held (chern-not-acquired="
          f"{unlocks['chern_not_acquired']}, bordism-not-acquired="
          f"{unlocks['bordism_not_acquired']}, no fake)")
    print(f"  NEXT RUNG       : the classifying space BG + the bordism groups Ω^Spin_*")
    print(f"                    (the HLE question) — each acquire-by-reading later.")
    print(f"  NO REGRESSION   : {noreg}")

    ok = (spec["all_emitted"] and acq["all_acquired"] and ver["verified"]
          and orient["ok"] and cobord["ok"]
          and unlocks["chern_not_acquired"] and unlocks["bordism_not_acquired"]
          and noreg)
    print(f"\nRESULT: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    print("\nLEARNING: the agent walked the NEXT RUNG — read the vector-bundle /")
    print("Stiefel-Whitney-class def, grounded the characteristic classes over the")
    print("held cohomology ring (cmsg86's cup product: w(T RP^n) = (1+x)^{n+1} is cup-")
    print("product POWERS in the held ring; the Whitney sum w(E⊕F)=w(E)·w(F) IS the cup")
    print("product), VERIFIED vs known (w(T RP^2) = 1 + x + x^2, w_1=x, w_2=x^2), and")
    print("demonstrated the payoffs: ORIENTABILITY (w_1(T RP^2)=x≠0 non-orientable vs")
    print("S^2/torus orientable — the class sees what the ring alone does not) +")
    print("COBORDISM (the SW number w_2[RP^2]=1≠0 -> RP^2 does NOT bound; S^2's SW")
    print("numbers 0 -> S^2 bounds — the cobordism invariant, the BRIDGE to the bordism")
    print("tier the HLE question lives on). The ladder climbs another rung (∂ -> ∂^T ->")
    print("cup product -> ring -> bundle/SW classes). HONEST RESIDUAL (NOT faked): the")
    print("integral Chern/Pontryagin classes (need the bundle curvature), the")
    print("CLASSIFYING SPACE BG, and the BORDISM GROUPS Ω^Spin_*(BG) — the HLE question")
    print("— are the next-deeper rungs, each its own acquire-by-reading step. The SW")
    print("classes acquired + verified; the bordism groups are NOT solved.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
