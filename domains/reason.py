"""The reasoning loop — answering a comprehended question with grounded capability.

The speech faculty turns text into a meaning Term over grounded concepts; the
math tower turns those concepts into actual computation. This closes the loop:
``solve`` walks a meaning Term and routes each head concept to the substrate's
capability, with object names bound to real values — so the entity doesn't just
*talk about* a determinant or a coset index, it *computes* one.

The capabilities are graph-resident computations (the determinant on the search
layer, the coset index by Todd–Coxeter, the next term by recurrence inference,
matrix rank on the engine, …). ``solve`` is the interpreter that dispatches a
comprehended meaning to them — the language↔computation interface, the same
boundary role as a world's callables. (Routing research-level HLE concepts is a
matter of having the capability at all — concept coverage — not of this loop.)
"""
from __future__ import annotations

import math
from fractions import Fraction as _Fraction


from domains import ca_infer as ci
from domains import continuous as cont
from domains import equation as eq
from domains import fp_group as fp
from domains import linear_algebra as la
from domains import sequence_infer as si


def _isprime(n) -> bool:
    n = int(n)
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def _factorize(n) -> list:
    """Prime factorisation by trial division (with multiplicity)."""
    n, out, d = int(n), [], 2
    while d * d <= n:
        while n % d == 0:
            out.append(d)
            n //= d
        d += 1
    if n > 1:
        out.append(n)
    return out


def _totient(n) -> int:
    """Euler's totient φ(n) — number of integers ≤ n coprime to n.
    Computed from the prime factorisation: φ(n) = n · Π (1 − 1/p)."""
    n = int(n)
    if n <= 0:
        return 0
    result = n
    seen: set = set()
    for p in _factorize(n):
        if p in seen:
            continue
        seen.add(p)
        result -= result // p
    return result


def _divisor_count(n) -> int:
    """d(n) — number of positive divisors. From prime factorisation:
    d(p_1^a_1 · p_2^a_2 · …) = (a_1+1)(a_2+1)…"""
    n = int(n)
    if n <= 0:
        return 0
    counts: dict = {}
    for p in _factorize(n):
        counts[p] = counts.get(p, 0) + 1
    result = 1
    for c in counts.values():
        result *= (c + 1)
    return result


def _divisor_sum(n) -> int:
    """σ(n) — sum of positive divisors. From prime factorisation:
    σ(p^a) = (p^(a+1) − 1) / (p − 1), multiplicative."""
    n = int(n)
    if n <= 0:
        return 0
    counts: dict = {}
    for p in _factorize(n):
        counts[p] = counts.get(p, 0) + 1
    result = 1
    for p, a in counts.items():
        result *= (p ** (a + 1) - 1) // (p - 1)
    return result


def _nth_fibonacci(n) -> int:
    """F(n) via the fast doubling identity — O(log n) multiplications."""
    n = int(n)
    if n < 0:
        return 0

    def go(k):
        if k == 0:
            return (0, 1)
        a, b = go(k >> 1)
        c = a * ((b << 1) - a)
        d = a * a + b * b
        if k & 1:
            return (d, c + d)
        return (c, d)

    return go(n)[0]


def _is_perfect_square(n) -> bool:
    n = int(n)
    if n < 0:
        return False
    s = math.isqrt(n)
    return s * s == n


def _mat(grid):
    g = la.new_graph()   # linear_algebra runs on the Rust-native engine now
    return g, la.make_matrix(g, "m", grid)


def _combine_chain(chain):
    """COMBINE-LIKE-TERMS over a CHAIN (a list of (coeff, simplex) terms): sum
    the coefficients of EQUAL simplices and DROP any whose total cancels to 0.
    This is the formal-sum reduction — the mechanism by which ∂∂ collapses to the
    ZERO chain (the boundary's two appearances of each face carry opposite signs,
    so they cancel here). Order-stable on first appearance.

    A chain term is (coeff, simplex) with simplex an ordered vertex list. Mirrors
    a DSL group-by Fold over the chain; owns no homology — just adds coefficients
    of like terms, the defining move of a formal sum."""
    order: list = []
    totals: dict = {}
    for coeff, simplex in chain:
        key = tuple(simplex)
        if key not in totals:
            totals[key] = 0
            order.append(key)
        totals[key] += coeff
    return [(totals[k], list(k)) for k in order if totals[k] != 0]


# ---- HOMOLOGY over the SIMPLICIAL boundary operator ∂ ----------------------
# The agent already holds ∂ (boundary_operator, ∂∂=0 verified). HOMOLOGY climbs
# ONE NAMED RUNG above ∂: H_n = ker ∂_n / im ∂_{n+1}, and the n-th BETTI number
#   b_n = dim ker ∂_n − dim im ∂_{n+1}
#       = (#n-simplices − rank ∂_n) − rank ∂_{n+1}.
# Every piece COMPOSES over the held ∂ + a matrix RANK. The primitives below
# mirror DSL Term shapes (a complex = a list of simplices = a world-adapter input
# like a chain; a boundary MATRIX = a list-of-lists; rank = Gaussian elimination
# over a field). NONE of them KNOW homology — they add the lower operations the
# Betti FORMULA (acquired by reading) composes over.


def _simplices_of_dim(complex_, k):
    """The k-simplices of a complex, in a STABLE order. A complex is given as a
    flat list of simplices (each an ordered vertex list); a k-simplex has k+1
    vertices (dim = len − 1). Order-stable on first appearance so the boundary
    MATRIX rows/cols line up across dimensions (column j of ∂_k ↔ this list[j])."""
    k = int(k)
    seen: list = []
    for s in complex_:
        s = list(s)
        if len(s) - 1 == k and s not in seen:
            seen.append(s)
    return seen


def _boundary_matrix(complex_, k):
    """∂_k as a MATRIX over the simplex bases — ∂ (held) expressed in coordinates.
    Columns = the k-simplices, rows = the (k−1)-simplices; entry M[i][j] = the
    (mod-2) coefficient of the i-th (k−1)-simplex in ∂(j-th k-simplex). The COLUMN
    is exactly ∂ of that k-simplex (the held boundary_operator's signed faces),
    read off over the (k−1)-simplex basis. This is the climb FROM ∂: the matrix is
    ∂ in a basis, nothing more. Returned over GF(2) (coeffs reduced mod 2) — the
    field Betti numbers of these torsion-free spaces are computed over.

    Edge cases as a matrix: ∂_0 (k=0) maps 0-simplices to the empty basis → a
    0-row × (#0-simplices) matrix, rank 0 (a point has no boundary). ∂_k with no
    k-simplices → a (#(k−1)-simplices)-row × 0-col matrix, rank 0."""
    k = int(k)
    cols = _simplices_of_dim(complex_, k)
    rows = _simplices_of_dim(complex_, k - 1) if k > 0 else []
    row_index = {tuple(r): i for i, r in enumerate(rows)}
    M = [[0] * len(cols) for _ in range(len(rows))]
    for j, simplex in enumerate(cols):
        # the j-th column IS ∂(simplex): for each i, drop vertex i → a face with
        # sign (−1)^i; place its coefficient (mod 2) in that face's row.
        for i in range(len(simplex)):
            face = [v for pos, v in enumerate(simplex) if pos != i]
            ridx = row_index.get(tuple(face))
            if ridx is not None:
                M[ridx][j] = (M[ridx][j] + 1) % 2          # coeff mod 2
    return M


def _matrix_rank_gf2(M):
    """rank(M) = the number of LINEARLY INDEPENDENT rows — computed by GAUSSIAN
    ELIMINATION over GF(2) (the field {0,1}, add = XOR). Sweep columns; for each,
    find a pivot row with a 1, eliminate that column from every other row (XOR),
    count the pivots. The number of pivots = the number of independent rows =
    the rank. Owns no homology — the textbook field rank. (GF(2) suffices for the
    Betti numbers of these torsion-free standard spaces.)"""
    # work on a copy as integer bitmask rows for fast XOR.
    rows = [list(int(x) % 2 for x in r) for r in M]
    if not rows or not rows[0]:
        return 0
    ncols = len(rows[0])
    rank = 0
    pivot_row = 0
    for col in range(ncols):
        # find a row at/after pivot_row with a 1 in this column.
        sel = None
        for r in range(pivot_row, len(rows)):
            if rows[r][col]:
                sel = r
                break
        if sel is None:
            continue
        rows[pivot_row], rows[sel] = rows[sel], rows[pivot_row]
        # eliminate this column from all OTHER rows (XOR).
        for r in range(len(rows)):
            if r != pivot_row and rows[r][col]:
                rows[r] = [(a ^ b) for a, b in zip(rows[r], rows[pivot_row])]
        rank += 1
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rank


def _matrix_rank_q(M):
    """rank(M) over Q — EXACT rational Gaussian elimination. The held-basis sibling
    of `_matrix_rank_gf2`: the SAME pivot-and-eliminate, but over the field of
    rationals (exact Fraction arithmetic, no rounding) instead of GF(2). The held
    `linear_algebra.rank` ALSO computes the exact rational rank, but by enumerating
    r×r minor determinants — correct yet combinatorial (intractable past a handful
    of rows). This is that same exact rank by the SCALABLE algorithm: forward
    elimination, count the pivots. Owns no homology / no cohomology — the textbook
    field rank over Q. Needed once the coefficient module is a Q-vector space (group
    cohomology H^*(G, Q^d), the rational coker/ker dimensions), where the GF(2) rank
    would give the wrong field's answer. No new Rust — held exact Fraction ring ops."""
    from fractions import Fraction as _Fr
    rows = [[_Fr(x) for x in r] for r in M]
    if not rows or not rows[0]:
        return 0
    ncols = len(rows[0])
    rank = 0
    pivot_row = 0
    for col in range(ncols):
        # find a row at/after pivot_row with a NONZERO entry in this column.
        sel = None
        for r in range(pivot_row, len(rows)):
            if rows[r][col] != 0:
                sel = r
                break
        if sel is None:
            continue
        rows[pivot_row], rows[sel] = rows[sel], rows[pivot_row]
        piv = rows[pivot_row][col]
        # eliminate this column from every OTHER row (subtract the scaled pivot row).
        for r in range(len(rows)):
            if r != pivot_row and rows[r][col] != 0:
                f = rows[r][col] / piv
                rows[r] = [a - f * b for a, b in zip(rows[r], rows[pivot_row])]
        rank += 1
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rank


# ---- INTEGRAL HOMOLOGY: the SIGNED-INTEGER boundary matrix + SMITH NORMAL FORM
# over Z (the tier ABOVE the GF(2) Betti — TORSION the field rank cannot see).
# The held GF(2) boundary matrix reduces coefficients mod 2, so it sees only the
# FREE rank (Betti) and is BLIND to torsion. The INTEGRAL boundary matrix keeps
# the SIGNED coefficient (-1)^i (the alternating sign the held boundary operator ∂
# already carries — neg_one_pow), so its SMITH NORMAL FORM over Z exposes the
# INVARIANT FACTORS d_1 | d_2 | ... — the d_i > 1 are exactly the TORSION
# coefficients. Each piece is the HELD integer arithmetic (+, -, *, //, gcd via
# the Euclidean row/col ops); none knows homology. The SNF is integer Gaussian
# elimination pivoting on the SMALLEST entry (the gcd reduction), the textbook
# algorithm — the agent SPECIFIES it (runtime_design) and it reduces to the held
# integer ring ops, so it is emitted as a held tower primitive (no Rust).


def _integer_boundary_matrix(complex_, k):
    """∂_k as a SIGNED-INTEGER matrix over the simplex bases — the held boundary
    operator ∂ in coordinates WITHOUT the mod-2 reduction. Columns = the
    k-simplices, rows = the (k−1)-simplices; entry M[i][j] = Σ over faces of the
    j-th k-simplex equal to the i-th (k−1)-simplex of the ALTERNATING SIGN (−1)^i
    (the held neg_one_pow the boundary operator already carries). This is the SAME
    column-is-∂(simplex) structure as `_boundary_matrix`, only it keeps the SIGN
    instead of reducing mod 2 — so its Smith normal form over Z sees the TORSION
    the GF(2) rank discards. Edge cases identical to the GF(2) version (∂_0 → a
    0-row matrix; no k-simplices → a 0-col matrix)."""
    k = int(k)
    cols = _simplices_of_dim(complex_, k)
    rows = _simplices_of_dim(complex_, k - 1) if k > 0 else []
    row_index = {tuple(r): i for i, r in enumerate(rows)}
    M = [[0] * len(cols) for _ in range(len(rows))]
    for j, simplex in enumerate(cols):
        # the j-th column IS ∂(simplex): drop vertex i → a face with sign (−1)^i;
        # ADD that signed coefficient (no mod 2) to the face's row.
        for i in range(len(simplex)):
            face = [v for pos, v in enumerate(simplex) if pos != i]
            ridx = row_index.get(tuple(face))
            if ridx is not None:
                M[ridx][j] += (-1) ** i
    return M


def _smith_normal_form_factors(M):
    """The SMITH NORMAL FORM of an integer matrix M = U·D·V (U, V invertible over
    Z), returned as the list of INVARIANT FACTORS |d_1|, |d_2|, ... on D's diagonal
    (the nonzero ones, in divisibility order d_1 | d_2 | ...). Computed by INTEGER
    Gaussian elimination: at each pivot step, bring the SMALLEST nonzero entry
    (by absolute value) to the pivot, then reduce every other entry in the pivot's
    row and column by integer quotients (the held // — the Euclidean gcd reduction);
    when a residue remains nonzero it is smaller, so it becomes the new pivot — the
    process terminates at the gcd, exactly as the Euclidean algorithm does. The
    number of invariant factors = the integer RANK; the factors > 1 are the
    TORSION coefficients. Owns no homology — the textbook SNF over the held integer
    ring (+, −, *, //)."""
    A = [list(int(x) for x in row) for row in M]
    if not A or not A[0]:
        return []
    nrows, ncols = len(A), len(A[0])
    factors: list = []
    t = 0
    while t < min(nrows, ncols):
        # find the pivot: the smallest-|value| nonzero entry in the active block.
        piv = None
        for i in range(t, nrows):
            for j in range(t, ncols):
                if A[i][j] != 0 and (
                        piv is None or abs(A[i][j]) < abs(A[piv[0]][piv[1]])):
                    piv = (i, j)
        if piv is None:
            break                                   # the rest is all-zero — done
        pi, pj = piv
        A[t], A[pi] = A[pi], A[t]                    # bring the pivot to (t, t)
        for i in range(nrows):
            A[i][t], A[i][pj] = A[i][pj], A[i][t]
        # reduce the pivot row + column by integer quotients (the gcd reduction);
        # any nonzero residue is smaller, so re-pivot until row+col are cleared.
        cleared = False
        while not cleared:
            cleared = True
            for i in range(t + 1, nrows):           # clear the pivot COLUMN
                if A[i][t] != 0:
                    q = A[i][t] // A[t][t]
                    for j in range(ncols):
                        A[i][j] -= q * A[t][j]
                    if A[i][t] != 0:                # residue < pivot — re-pivot
                        A[t], A[i] = A[i], A[t]
                        cleared = False
            for j in range(t + 1, ncols):           # clear the pivot ROW
                if A[t][j] != 0:
                    q = A[t][j] // A[t][t]
                    for i in range(nrows):
                        A[i][j] -= q * A[i][t]
                    if A[t][j] != 0:                # residue < pivot — re-pivot
                        for i in range(nrows):
                            A[i][t], A[i][j] = A[i][j], A[i][t]
                        cleared = False
        factors.append(abs(A[t][t]))
        t += 1
    # enforce the divisibility chain d_1 | d_2 | ... (replace adjacent pairs by
    # (gcd, lcm) until stable — the SNF normalisation; held gcd/lcm).
    changed = True
    while changed:
        changed = False
        for i in range(len(factors) - 1):
            g = math.gcd(factors[i], factors[i + 1])
            if g != factors[i]:
                l = factors[i] * factors[i + 1] // g if g else 0
                factors[i], factors[i + 1] = g, l
                changed = True
    return factors


def _integral_homology(complex_, k):
    """The k-th INTEGRAL homology H_k(X;Z) = Z^{free} ⊕ (⊕ Z/d_i), returned as
    {"free": free_rank, "torsion": [d_i > 1]}. The FREE rank = the k-th Betti
    number = #k-simplices − rank ∂_k − rank ∂_{k+1} (rank over Z = the number of
    invariant factors of the SNF). The TORSION of H_k = the invariant factors > 1
    of the SNF of ∂_{k+1} (the boundary INTO degree k) — the d_i > 1 the GF(2)
    rank could not see. Composes over the held integer boundary matrix + SNF."""
    k = int(k)
    nk = len(_simplices_of_dim(complex_, k))
    f_k = _smith_normal_form_factors(_integer_boundary_matrix(complex_, k))
    f_k1 = _smith_normal_form_factors(_integer_boundary_matrix(complex_, k + 1))
    free = nk - len(f_k) - len(f_k1)
    torsion = [d for d in f_k1 if d > 1]
    return {"free": free, "torsion": torsion}


def _partition_count(n):
    """p(n) — the number of PARTITIONS of the non-negative integer n (the ways to
    write n as a sum of positive integers, order-independent). Computed by the
    standard partition recurrence over the held integer ring: p(0)=1, and the DP
    p[m] += p[m - c] over coin-sizes c = 1..n accumulates every partition exactly
    once (the coins-summing-to-n count). Owns no topology — a count over the held
    integer +; p(0)=1, p(1)=1, p(2)=2, p(3)=3, p(4)=5, p(5)=7."""
    n = int(n)
    if n < 0:
        return 0
    p = [0] * (n + 1)
    p[0] = 1
    for c in range(1, n + 1):
        for m in range(c, n + 1):
            p[m] += p[m - c]
    return p[n]


def _spin_rational_rank(n):
    """The FREE rank of Omega^Spin_n ⊗ Q — the RATIONAL Spin-bordism coefficient
    group in degree n. Omega^Spin_* ⊗ Q is a POLYNOMIAL ring on one generator in
    each degree 4k (the Pontryagin numbers), so its degree-n free rank is the number
    of PARTITIONS of n/4 when 4 | n, else 0 (an odd / non-4k degree has no rational
    Pontryagin class). Reduces to the held p(n/4) + the 4|n test (mod) — integer
    arithmetic, no topology: rank at degrees 0,4,8,12 = p(0),p(1),p(2),p(3) =
    1,1,2,3. This is the part that genuinely COMPUTES (vs the read 2-torsion)."""
    n = int(n)
    if n < 0 or n % 4 != 0:
        return 0
    return _partition_count(n // 4)


def _weyl_hp_rank_bg2(p):
    """rank H_p(BG2;Q) — the FREE rank of BG2's degree-p rational homology. By the
    Weyl-invariant computation (cmsg89) H*(BG2;Q) = Q[y_4, y_12], a polynomial ring
    on generators in cohomological degrees 4 and 12; so the degree-p graded piece is
    spanned by the MONOMIALS y_4^a y_12^b with 4a + 12b = p (a,b >= 0), and (Poincaré
    duality / the graded dimension) rank H_p = the NUMBER of such monomials. This is
    a count over the held integer ring — the number of (a,b) with 4a + 12b = p — no
    topology: ranks 1,0,0,0,1,0,0,0,1,0,0,0,2 at p = 0..12 (1 at p=0,4,8; 2 at p=12,
    namely y_4^3 and y_12)."""
    p = int(p)
    if p < 0:
        return 0
    # count (a, b) >= 0 with 4a + 12b = p, i.e. a + 3b = p/4 (0 unless 4 | p).
    if p % 4 != 0:
        return 0
    q = p // 4
    count = 0
    b = 0
    while 12 * b <= p:                 # a = q - 3b must be >= 0
        if q - 3 * b >= 0:
            count += 1
        b += 1
    return count


def _ahss_e2_rank_bg2_spin(p, q):
    """rank E^2_{p,q} ⊗ Q of the Atiyah-Hirzebruch spectral sequence for the Spin
    bordism of BG2 — E^2_{p,q} = H_p(BG2; Omega^Spin_q), so rationally its free rank
    is the PRODUCT rank H_p(BG2;Q) · rank(Omega^Spin_q ⊗ Q). Reduces to the held
    integer multiply over the two held rank read-outs (weyl_hp_rank · spin_rational_
    rank) — no topology, no new Rust. The REDUCED page drops the p = 0 column (the
    trivial-G2-bundle classes = the point's bordism)."""
    return int(_weyl_hp_rank_bg2(p)) * int(_spin_rational_rank(q))


# ---- the CUP PRODUCT over SIMPLICIAL COCHAINS (Alexander-Whitney) ----------
# The COHOMOLOGY RING is ONE NAMED RUNG above the held cohomology H^n: H^*(X) =
# ⊕_n H^n(X) with the CUP PRODUCT as the ring multiplication. A COCHAIN is the
# TRANSPOSE of the held chain structure — a p-cochain assigns a field value to
# each ordered p-simplex, so over GF(2) it is a 0/1 VECTOR aligned to the ordered
# p-simplices (_simplices_of_dim, the SAME stable order the boundary MATRIX uses).
# The coboundary δ = ∂^T (the transpose of the held boundary matrix). The CUP
# PRODUCT is the ALEXANDER-WHITNEY formula on cochains:
#   (α ∪ β)(σ) = α(FRONT p-face of σ) · β(BACK q-face of σ)   for each (p+q)-simplex σ,
# where for σ = [v_0..v_{p+q}] the FRONT p-face = [v_0..v_p] and the BACK q-face =
# [v_p..v_{p+q}] (they SHARE the middle vertex v_p), and · is the FIELD multiply
# (mod-2 product = AND over GF(2)). Each piece reduces to HELD simplicial primitives
# (the ordered simplices + an ordered slice + a value lookup + the field multiply) —
# the AW reduction the agent reads. NONE of these know the ring; they add the lower
# cochain operations the read-grounded cup-product formula composes over. Mirrors DSL
# Term shapes (a list slice = Filter-by-position; a lookup = index-of + nth; the
# product = MapSet over the (p+q)-simplices) — no new Rust.


def _front_face(simplex, p):
    """The FRONT p-face of an ordered simplex σ = [v_0..v_n]: the first p+1
    vertices [v_0..v_p] (an ordered prefix slice). The α-argument of the
    Alexander-Whitney cup product. A list-prefix by POSITION — a DSL Filter over
    the index positions keeping pos <= p; owns no cohomology."""
    return list(simplex)[: int(p) + 1]


def _back_face(simplex, q):
    """The BACK q-face of an ordered simplex σ = [v_0..v_n] of dimension p+q: the
    LAST q+1 vertices [v_p..v_{p+q}] = the suffix starting at index p = n − q (an
    ordered suffix slice). The β-argument of the Alexander-Whitney cup product;
    it SHARES the middle vertex v_p with the front p-face. A list-suffix by
    POSITION — a DSL Filter over the index positions keeping pos >= p."""
    s = list(simplex)
    return s[len(s) - 1 - int(q):]


def _cochain_value(cochain, simplices, simplex):
    """EVALUATE a cochain on a simplex: a p-cochain assigns a field value to each
    ordered p-simplex, represented over GF(2) as a 0/1 VECTOR aligned to
    `simplices` (the ordered p-simplices, _simplices_of_dim order). The value on
    `simplex` is the entry at its POSITION in that ordered basis (0 if the simplex
    is not a p-simplex of the complex — a cochain vanishes off its basis). A
    lookup = index-of then nth; owns no cohomology, just the cochain pairing."""
    key = list(simplex)
    for i, s in enumerate(simplices):
        if list(s) == key:
            return int(cochain[i]) % 2 if i < len(cochain) else 0
    return 0


def _cup_product(complex_, p, q, alpha, beta):
    """THE CUP PRODUCT (Alexander-Whitney) of a p-cochain α and a q-cochain β,
    over GF(2): the (p+q)-cochain whose value on each ordered (p+q)-simplex σ is
        (α ∪ β)(σ) = α(front_p_face(σ)) · β(back_q_face(σ))   (mod 2).
    α / β are 0/1 vectors aligned to the ordered p- / q-simplices; the result is a
    0/1 vector aligned to the ordered (p+q)-simplices (_simplices_of_dim order, the
    SAME basis the boundary matrix / cohomology use). A MapSet over the
    (p+q)-simplices of the product of the two cochain pairings — the field bilinear
    AW formula, composed over the held simplices + the slice + the lookup + the
    mod-2 multiply. Owns no ring; it IS the read-grounded formula realised."""
    p, q = int(p), int(q)
    p_simp = _simplices_of_dim(complex_, p)
    q_simp = _simplices_of_dim(complex_, q)
    pq_simp = _simplices_of_dim(complex_, p + q)
    out = []
    for sigma in pq_simp:
        a = _cochain_value(alpha, p_simp, _front_face(sigma, p))
        b = _cochain_value(beta, q_simp, _back_face(sigma, q))
        out.append((a * b) % 2)
    return out


def _coboundary_matrix(complex_, k):
    """δ^k = ∂_{k+1}^T (the coboundary IS the transpose of the held boundary
    matrix): δ maps k-cochains to (k+1)-cochains. The held ∂_{k+1} is rows =
    k-simplices, cols = (k+1)-simplices; its TRANSPOSE is the coboundary on
    cochains. The cochain complex is the held chain structure, transposed — no new
    operator, just ∂^T. Used to compute H^k = ker δ^k / im δ^{k-1} via rank (the
    cohomology dim, which over a field equals the homology Betti b_k)."""
    M = _boundary_matrix(complex_, int(k) + 1)
    if not M:
        return []
    rows, cols = len(M), len(M[0])
    return [[M[r][c] for r in range(rows)] for c in range(cols)]


# ---- STEENROD SQUARES via the CUP-i PRODUCTS (the tier ABOVE the cup product —
# the higher chain homotopies that extend the cup product over the cochain
# structure ∂^T). The CUP-i PRODUCT ∪_i is Steenrod's higher diagonal on
# simplicial cochains: for a p-cochain α and q-cochain β, α ∪_i β is a
# (p+q−i)-cochain. The combinatorial formula over GF(2) (Steenrod 1947): on an
# ordered (p+q−i)-simplex σ = [v_0..v_N], sum over the (i+1) internal CUT POINTS
# 0 ≤ j_1 < ... < j_{i+1} ≤ N, splitting σ into i+2 RUNS that SHARE endpoints; α
# eats the even-indexed runs (0,2,4,...), β the odd-indexed runs (1,3,5,...); keep
# the terms whose α-face has p+1 vertices and β-face has q+1 vertices, multiply the
# two cochain pairings mod 2, sum over σ. At i=0 this is EXACTLY the held cup
# product (one cut = the Alexander-Whitney front/back split). The STEENROD SQUARE
# is then Sq^i(x) = x ∪_{n−i} x for an n-cochain x: a cohomology OPERATION
# H^n(X;Z/2) → H^{n+i}(X;Z/2). Sq^0 = id, Sq^n(x) = x^2 (the top square = the cup
# square), Sq^i(x) = 0 for i > n. Each piece composes over the HELD simplices +
# slices + the cochain pairing + the mod-2 multiply — the cup product the agent
# already holds, extended by the higher diagonal. No new Rust (the SAME held tower
# class as cup_product). The agent SPECIFIES it (runtime_design); the emitter
# realises it over the held cup-product structure.


def _cup_i_product(complex_, p, q, i, alpha, beta):
    """THE CUP-i PRODUCT (Steenrod higher diagonal) of a p-cochain α and a
    q-cochain β over GF(2): the (p+q−i)-cochain whose value on each ordered
    (p+q−i)-simplex σ = [v_0..v_N] is the sum over the (i+1) cut points
    0 ≤ j_1 < ... < j_{i+1} ≤ N of α(α-face)·β(β-face) (mod 2), where the cuts
    split σ into i+2 runs sharing endpoints, α takes runs 0,2,4,..., β takes runs
    1,3,5,...; only terms with |α-face| = p+1 and |β-face| = q+1 contribute. At
    i = 0 this is EXACTLY the held Alexander-Whitney cup product (one cut = the
    front/back split). The higher homotopies the Steenrod squares are built from.
    Composes over the held simplices + the cochain pairing + the mod-2 multiply —
    no ring, just the read-grounded cup-i formula realised."""
    import itertools as _it
    p, q, i = int(p), int(q), int(i)
    N = p + q - i
    if N < 0:
        return []
    p_simp = _simplices_of_dim(complex_, p)
    q_simp = _simplices_of_dim(complex_, q)
    pq_simp = _simplices_of_dim(complex_, N)
    out = []
    for sigma in pq_simp:
        n = len(sigma) - 1            # == N
        total = 0
        for cuts in _it.combinations(range(0, n + 1), i + 1):
            ls = [0] + list(cuts) + [n]
            a_face: list = []
            b_face: list = []
            for r in range(len(ls) - 1):
                seg = sigma[ls[r]: ls[r + 1] + 1]      # runs share endpoints
                tgt = a_face if r % 2 == 0 else b_face
                if tgt and tgt[-1] == seg[0]:
                    tgt.extend(seg[1:])
                else:
                    tgt.extend(seg)
            if len(a_face) == p + 1 and len(b_face) == q + 1:
                a = _cochain_value(alpha, p_simp, a_face)
                b = _cochain_value(beta, q_simp, b_face)
                total = (total + a * b) % 2
        out.append(total)
    return out


def _steenrod_square_cochain(complex_, n, i, x):
    """THE STEENROD SQUARE Sq^i on an n-cochain x over GF(2): the (n+i)-cochain
    Sq^i(x) = x ∪_{n−i} x (the cup-(n−i) product of x with itself). A cohomology
    operation H^n(X;Z/2) → H^{n+i}(X;Z/2). By the cup-i axioms: Sq^0(x) = x ∪_n x
    = x (the identity, at the cochain level up to a coboundary), Sq^n(x) = x ∪_0 x
    = x^2 (the cup square, the held cup product), Sq^i(x) = 0 for i > n
    (the cup-(n−i) with negative index vanishes — instability). Composes over the
    held cup-i product; no new Rust."""
    n, i = int(n), int(i)
    if i > n:
        # instability: Sq^i = 0 for i > |x| — a zero (n+i)-cochain.
        return [0] * len(_simplices_of_dim(complex_, n + i))
    return _cup_i_product(complex_, n, n, n - i, x, x)


def _bg2_integral_homology_rank(p):
    """The FREE rank of H_p(BG2;Z) — the rank of BG2's degree-p integral homology.
    By Poincare/universal-coefficient duality with the rational cohomology ring
    H*(BG2;Q) = Q[y_4,y_12] (cmsg89), the free rank of H_p equals the rank of H^p,
    = #monomials y_4^a y_12^b of degree p (the SAME count as weyl_hp_rank). The
    2-TORSION is carried separately (bg2_integral_torsion_2rank); this is only the
    free rank. A held integer monomial count — no topology, no new Rust."""
    return _weyl_hp_rank_bg2(p)


# the READ 2-torsion of H_*(BG2;Z) (the documented G2 result; READ, NOT derived —
# the SAME read-and-label model cmsg91 used for the ABP coefficient ring). The
# integral cohomology of BG2 is Z[y_4,y_12] (free) PLUS a 2-torsion ideal generated
# by the degree-7 class x_7 = beta(x_6) (the integral Bockstein of the mod-2 class
# x_6 = Sq^2 x_4). On the FREE polynomial part the torsion classes are x_7 times the
# free generators: the degree-(7+4a+12b) torsion classes x_7 * y_4^a y_12^b. By UCT
# the COHOMOLOGY 2-torsion in degree n = the HOMOLOGY 2-torsion in degree n-1, so the
# homology 2-torsion sits one degree below the cohomology torsion. The number of
# Z/2 summands in H_n(BG2;Z)_tors (read, labeled): degree-by-degree, n = 0..13.
#   H^n(BG2;Z): 7->Z/2, 11->Z/2 (x_7, x_7*y_4) in the range n<=13; higher products
#   (x_7^2 deg14, x_7*y_12 deg19, ...) lie above degree 13.
#   H_n(BG2;Z)_tors (one degree below the cohomology torsion, UCT) -> nonzero at
#   n = 6 (dual to H^7 torsion) and n = 10 (dual to H^11 torsion).
_BG2_INT_HOMOLOGY_TORSION_2RANK_READ = {
    0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0,
    6: 1,    # Z/2  (UCT-dual to the cohomology torsion x_7 in H^7)
    7: 0,
    8: 0, 9: 0,
    10: 1,   # Z/2  (UCT-dual to x_7*y_4 in H^11)
    11: 0, 12: 0, 13: 0,
}


def _bg2_integral_torsion_2rank(p):
    """The NUMBER of Z/2 summands in the 2-torsion of H_p(BG2;Z) — a READ value
    (the documented G2 2-torsion, labeled read-not-derived, like the ABP coefficient
    ring). The torsion is generated by x_7 = beta(x_6) and its products with the free
    generators y_4,y_12; UCT places the HOMOLOGY torsion one degree below the
    COHOMOLOGY torsion. In the range p = 0..13 the nonzero entries are p=6 and p=10
    (Z/2 each). This is the deep structural input the agent READS — it does NOT derive
    BG2's torsion from a finite-complex SNF (BG2 is infinite)."""
    p = int(p)
    return int(_BG2_INT_HOMOLOGY_TORSION_2RANK_READ.get(p, 0))


def _spin_bordism_free_rank(q):
    """The FREE rank of Omega^Spin_q (the READ ABP coefficient ring, cmsg91). Equals
    the rational rank for the degrees where the ring is known: 1,1,2,3 at q=0,4,8,12.
    A held read-out (cross-checked vs the computed rational rank)."""
    return _spin_rational_rank(q)


# the READ 2-torsion of Omega^Spin_q (ABP, cmsg91): Z/2 at q=1,2,10; (Z/2)^2 at q=9.
_SPIN_BORDISM_TORSION_2RANK_READ = {1: 1, 2: 1, 9: 2, 10: 1}


def _spin_bordism_torsion_2rank(q):
    """The NUMBER of Z/2 summands in Omega^Spin_q (the READ ABP 2-torsion, cmsg91):
    q=1->1, q=2->1, q=9->2, q=10->1, else 0. A held read-out."""
    return int(_SPIN_BORDISM_TORSION_2RANK_READ.get(int(q), 0))


def _bg2_integral_e2(p, q):
    """THE INTEGRAL Atiyah-Hirzebruch E_2 entry E^2_{p,q} = H_p(BG2; Omega^Spin_q),
    returned as a structured group {free, torsion_2rank}. By the universal coefficient
    theorem for homology with coefficients in the graded ring Omega^Spin_*:
        H_p(BG2; G) = (H_p(BG2;Z) (x) G) (+) Tor(H_{p-1}(BG2;Z), G),
    applied with G = Omega^Spin_q. Over the 2-LOCAL part (the only torsion present is
    2-torsion on both sides) the Z/2-summand count assembles as:
      free      = free(H_p) * free(Omega_q)
      torsion   = free(H_p)*tors(Omega_q)            (Z (x) Z/2 = Z/2)
                + tors(H_p)*free(Omega_q)            (Z/2 (x) Z = Z/2)
                + tors(H_p)*tors(Omega_q)            (Z/2 (x) Z/2 = Z/2)
                + Tor(H_{p-1}, Omega_q):
                    tors(H_{p-1})*free(Omega_q)? no — Tor(Z/2,Z)=0;
                    tors(H_{p-1})*tors(Omega_q)      (Tor(Z/2,Z/2)=Z/2)
                  i.e. + tors(H_{p-1}) * tors(Omega_q).
    All inputs are the READ values (BG2's integral homology free rank + its READ
    2-torsion; the READ ABP coefficient ring free rank + 2-torsion). The ASSEMBLY (the
    tensor + Tor bookkeeping over the held integer multiply/add) is the agent's. No
    new Rust — held integer arithmetic over the read inputs."""
    p, q = int(p), int(q)
    fp = _bg2_integral_homology_rank(p)
    tp = _bg2_integral_torsion_2rank(p)
    tp1 = _bg2_integral_torsion_2rank(p - 1) if p - 1 >= 0 else 0
    fq = _spin_bordism_free_rank(q)
    tq = _spin_bordism_torsion_2rank(q)
    free = fp * fq
    tors2 = fp * tq + tp * fq + tp * tq + tp1 * tq
    return {"free": int(free), "torsion_2rank": int(tors2)}


def _steenrod_square_poly_coeff(j, i):
    """THE STEENROD SQUARE on the polynomial ring H*(RP^∞;Z/2) = Z/2[x]: the
    coefficient of x^{i+j} in Sq^i(x^j). By the total-square Cartan formula
    Sq(x^j) = (Sq x)^j = (x + x^2)^j (Sq x = x + x^2: Sq^0 x = x, Sq^1 x = x^2, the
    cochain-verified base values, extended multiplicatively), the coefficient of
    x^{i+j} is C(j,i) mod 2. So Sq^i(x^j) = C(j,i) x^{i+j} mod 2: Sq^0(x^j) = x^j
    (id), Sq^j(x^j) = x^{2j} (square), Sq^i = 0 for i > j (instability). Held
    integer arithmetic (the binomial mod 2) over the verified base values; no
    topology beyond the cochain-grounded cup-i."""
    j, i = int(j), int(i)
    if i < 0 or i > j:
        return 0
    return math.comb(j, i) % 2


# the READ per-generator Steenrod action on the mod-2 cohomology ring of BG2,
# H*(BG2;Z/2) = Z/2[x_4, x_6, x_7] (degrees 4,6,7). READ from the documented G2
# result (the SAME read-and-label model cmsg91 used for the ABP coefficient ring and
# cmsg94 used for the integral cohomology): the total Steenrod action on the ring
# generators. Each entry maps Sq^k(generator) to a list of (monomial, coeff) terms
# over the ring, monomials encoded as (a,b,c) = x_4^a x_6^b x_7^c. Only the generator
# action is READ; the action on PRODUCTS is DERIVED by the Cartan formula (below).
#   Sq^0 g = g (identity, all generators).
#   Sq^1 x_4 = 0   (x_4 is the mod-2 reduction of the integral y_4; beta x_4 = 0).
#   Sq^2 x_4 = x_6 (the defining relation; x_6 = Sq^2 x_4).
#   Sq^3 x_4 = Sq^1 Sq^2 x_4 = Sq^1 x_6 = x_7  (Adem; the integral Bockstein of x_6).
#   Sq^4 x_4 = x_4^2 (the top square, |x_4|=4).
#   Sq^1 x_6 = x_7 (= beta x_6, the degree-7 integral 2-torsion generator).
#   Sq^2 x_6 = ? (degree 8) — by Wu/instability on the ring this is 0 in the range we
#               use (no degree-8 monomial below is invoked by the d_2 we compute; left
#               unspecified -> empty, the honest in-range read).
#   Sq^1 x_7 = Sq^1 Sq^1 x_6 = 0 (Sq^1 Sq^1 = 0, Adem).
#   Sq^2 x_7 = 0 (degree 9 is EMPTY in Z/2[x_4,x_6,x_7]: 9 is not a non-neg combo of
#               4,6,7 -> no degree-9 monomial, so Sq^2 x_7 has nowhere to land = 0).
# Entries below cover only the (generator, k) pairs the BG2 d_2 computations invoke;
# Sq^0 is the identity for any generator and is handled in the Cartan routine.
_BG2_GEN_STEENROD_ACTION_READ = {
    # (gen_index, k) -> list of (a,b,c, coeff)   [gen 0=x_4, 1=x_6, 2=x_7]
    (0, 1): [],                       # Sq^1 x_4 = 0
    (0, 2): [(0, 1, 0, 1)],           # Sq^2 x_4 = x_6
    (1, 1): [(0, 0, 1, 1)],           # Sq^1 x_6 = x_7
    (1, 2): [],                       # Sq^2 x_6 = 0 (in-range read; degree 8 unused)
    (2, 1): [],                       # Sq^1 x_7 = 0
    (2, 2): [],                       # Sq^2 x_7 = 0 (degree 9 empty in the ring)
}
_BG2_GEN_DEG = {0: 4, 1: 6, 2: 7}     # x_4, x_6, x_7


def _bg2_gen_sq(gen, k):
    """Sq^k of a single READ ring generator (gen in {0,1,2} = x_4,x_6,x_7) as a list
    of (a,b,c,coeff) ring terms. Sq^0 = identity; Sq^k for k>deg = 0 (instability);
    Sq^deg = the square (the generator's own square monomial); otherwise the READ
    per-generator action above. The generator action is READ (labeled); this routine
    only LOOKS IT UP (no derivation of the generator action)."""
    gen, k = int(gen), int(k)
    if k == 0:
        term = [0, 0, 0]
        term[gen] = 1
        return [(term[0], term[1], term[2], 1)]
    d = _BG2_GEN_DEG[gen]
    if k > d:
        return []                      # instability: Sq^k = 0 for k > |x|
    if k == d:                         # top square Sq^{|x|}(x) = x^2
        term = [0, 0, 0]
        term[gen] = 2
        return [(term[0], term[1], term[2], 1)]
    return list(_BG2_GEN_STEENROD_ACTION_READ.get((gen, k), []))


def _mono_mul(m1, m2):
    """Multiply two ring monomials (a,b,c)·(a',b',c') in Z/2[x_4,x_6,x_7] = add the
    exponent vectors (the held integer add)."""
    return (m1[0] + m2[0], m1[1] + m2[1], m1[2] + m2[2])


def _bg2_steenrod_product(factors, k):
    """Sq^k of a PRODUCT of READ ring generators in H*(BG2;Z/2) = Z/2[x_4,x_6,x_7],
    DERIVED by the CARTAN FORMULA over the READ per-generator action.

    `factors` is a list of generator indices (e.g. [0,2] = x_4·x_7). The Cartan
    formula (the multiplicativity of the total square, the SAME axiom the single-
    generator coeff is built on) gives, iterating two factors at a time:
        Sq^k(u·v) = sum_{a+b=k} Sq^a(u) · Sq^b(v).
    Generalised over the list: distribute k across the factors in all ways, multiply
    the per-factor Sq results (held monomial multiply), sum mod 2. The per-generator
    Sq^a is the READ action (_bg2_gen_sq); the Cartan distribution + the monomial
    multiply + the mod-2 sum are the agent's HELD arithmetic. Returns the result as a
    dict {(a,b,c): coeff mod 2} over the ring basis (zero terms dropped).

    This is the DERIVED differential value: with d_2 = dual Sq^2 (the READ ko
    k-invariant), Sq^2(x_4·x_7) is exactly this with factors=[0,2], k=2 — forced by
    the Cartan algebra + the read generator action, NOT by any known answer."""
    k = int(k)
    factors = [int(g) for g in factors]
    # accumulate as a dict monomial -> coeff mod 2; start with the unit (k distributed)
    # via a recursive Cartan distribution over the factor list.
    from itertools import product as _iproduct

    # for each factor choose an exponent a_i >= 0 with sum a_i = k; Sq^{a_i} of that
    # generator gives a list of terms; multiply across factors, sum mod 2.
    nf = len(factors)
    acc: dict = {}
    # enumerate compositions of k into nf non-negative parts (each <= the gen degree
    # is enforced by _bg2_gen_sq returning [] for k>deg, so the term vanishes).
    def _compositions(total, parts):
        if parts == 1:
            yield (total,)
            return
        for first in range(total + 1):
            for rest in _compositions(total - first, parts - 1):
                yield (first,) + rest

    for comp in _compositions(k, nf):
        # per-factor Sq^{comp[i]} term lists
        per = [_bg2_gen_sq(factors[i], comp[i]) for i in range(nf)]
        if any(len(t) == 0 for t in per):
            continue
        # multiply across the factors (cartesian product of term choices)
        for choice in _iproduct(*per):
            mono = (0, 0, 0)
            coeff = 1
            for (a, b, c, cf) in choice:
                mono = _mono_mul(mono, (a, b, c))
                coeff = (coeff * cf) % 2
            if coeff:
                acc[mono] = (acc.get(mono, 0) + coeff) % 2
    return {m: c for m, c in acc.items() if c % 2}


def _exact_div(a):
    """EXACT a/b: an exact Fraction (reduced to int when integral), no float rounding,
    when both operands are integers/Fractions; float division otherwise. The held
    rational-arithmetic atom a recursion with fractional intermediates reduces over."""
    left, right = a["left"], a["right"]
    def _rational(x):
        if isinstance(x, _Fraction):
            return True
        if isinstance(x, int) and not isinstance(x, bool):
            return True
        if isinstance(x, float) and x.is_integer():
            return True
        return False
    if _rational(left) and _rational(right):
        q = _Fraction(left) / _Fraction(right)
        return int(q) if q.denominator == 1 else q
    return left / right


# concept → capability. Object args arrive already evaluated (matrices as grids,
# numbers as ints, a group as (generators, relators), a sequence as a list, an
# automaton as a 0/1 grid). The values dispatch into the engine's computations.
CAPABILITIES = {
    # linear algebra (on the engine)
    "det": lambda a: la.determinant(*_mat(a["of"])),
    "rank": lambda a: la.rank(*_mat(a["of"])),
    "trace": lambda a: la.trace(*_mat(a["of"])),
    "invertible": lambda a: la.is_invertible(*_mat(a["arg"])),
    # number theory
    "gcd": lambda a: math.gcd(int(a["a"]), int(a["b"])),
    "lcm": lambda a: math.lcm(int(a["a"]), int(a["b"])),
    "prime": lambda a: _isprime(a["arg"]),
    "even": lambda a: int(a["arg"]) % 2 == 0,
    "odd": lambda a: int(a["arg"]) % 2 == 1,
    "largest_prime_factor": lambda a: max(_factorize(a["of"])),
    "prime_factors": lambda a: sorted(set(_factorize(a["of"]))),
    "divides": lambda a: int(a["right"]) % int(a["left"]) == 0,
    "plus": lambda a: a["left"] + a["right"],
    "times": lambda a: a["left"] * a["right"],
    # the remaining held arithmetic primitives (parallel to plus/times above) —
    # the same trivial computable basis a composed combination Term-tree composes
    # over. Each mirrors a DSL Term variant (Minus / Div / Mod / Eq) and is the
    # held primitive a read-and-grounded computational definition reduces to.
    "minus": lambda a: a["left"] - a["right"],
    # EXACT division. When both operands are integers (or exact Fractions) the result
    # is the exact rational a/b as a Fraction (reduced to an int when the denominator
    # is 1) — NO float rounding. This is what a recursion whose INTERMEDIATE terms are
    # fractional but whose final value is integral (e.g. the Hall subgroup-count
    # recursion s_n = h_n/(n-1)! - ...) needs to land exactly. Falls back to float
    # division only for genuine float operands.
    "div": _exact_div,
    "mod": lambda a: int(a["left"]) % int(a["right"]),
    "eq": lambda a: a["left"] == a["right"],
    # comparison primitives (mirror DSL Gt / Lt / Ge / Le Terms) — the held
    # computable basis a read-grounded predicate definition (e.g. an abundant
    # number := aliquot_sum(n) > n) reduces to.
    "gt": lambda a: a["left"] > a["right"],
    "lt": lambda a: a["left"] < a["right"],
    "ge": lambda a: a["left"] >= a["right"],
    "le": lambda a: a["left"] <= a["right"],
    "factorial": lambda a: math.factorial(int(a["of"])),
    "totient": lambda a: _totient(a["of"]),
    "divisor_count": lambda a: _divisor_count(a["of"]),
    "divisor_sum": lambda a: _divisor_sum(a["of"]),
    # ---- COLLECTION / ITERATION primitives (the base over which the agent
    # acquires DISCRETE-STRUCTURE OPERATIONS by reading). Each mirrors a DSL Term
    # variant (range/iota, Count, Intersect, member, IsEmpty); the collection
    # OPERAND is a concrete representation — a range 1..n (a list) or a small
    # explicit set (a list). The two ITERATION binders (count_where / sum_where)
    # are handled by solve's binder evaluator above (they need a lazy body); these
    # are the eager, value-level collection ops.
    #   range_incl{lo,hi}     -> the inclusive integer range [lo..hi] (a list).
    #   cardinality{of}       -> |S| (DSL Count).
    #   member{elem,of}       -> elem in S (DSL member).
    #   is_empty{of}          -> S has no elements (DSL IsEmpty).
    #   intersection{a,b}     -> elements in BOTH (DSL Intersect), order-stable.
    #   are_disjoint{a,b}     -> intersection(a,b) is empty.
    "range_incl": lambda a: list(range(int(a["lo"]), int(a["hi"]) + 1)),
    "cardinality": lambda a: len(list(a["of"])),
    "member": lambda a: a["elem"] in list(a["of"]),
    "is_empty": lambda a: len(list(a["of"])) == 0,
    "intersection": lambda a: [x for x in list(a["a"]) if x in set(a["b"])],
    "are_disjoint": lambda a: set(a["a"]).isdisjoint(set(a["b"])),
    # ---- STRUCTURED-OBJECT primitives (the tier ABOVE collections — operations
    # over SIMPLICES and CHAINS, the bedrock the simplicial boundary operator ∂
    # composes from). The agent acquires ∂ by READING over THESE, exactly as it
    # acquired divisor_count over the collection primitives. Each mirrors a DSL
    # Term shape (Filter / Pow / Tuple / MapSet / Fold / IsEmpty) — no new Rust.
    # The REPRESENTATION is small + explicit:
    #   · a SIMPLEX = an ordered vertex list, e.g. [0,1,2].
    #   · a CHAIN   = a formal sum = a list of (coeff, simplex) terms, e.g.
    #                 [(1,[1,2]), (-1,[0,2]), (1,[0,1])].
    #
    #   simplex_dim{of}      -> dim of a simplex = len - 1 (DSL Count then Minus).
    #   face{of,i}           -> the simplex with vertex i DROPPED — a list-drop by
    #                           POSITION (DSL Filter over the index positions:
    #                           keep v where its position != i). The face_i part.
    #   neg_one_pow{i}       -> (-1)^i, the ALTERNATING SIGN (DSL Pow, base -1; a
    #                           parity expression: +1 even i, -1 odd i).
    #   chain_term{coeff,simplex} -> a single signed-simplex term (coeff, simplex)
    #                           — a CHAIN of one term (the formal-sum atom; a pair).
    #   combine_like_terms{of}    -> COMBINE-LIKE-TERMS: sum coefficients of equal
    #                           simplices, dropping any that cancel to 0 (the formal
    #                           SUM reduced — a group-by-Fold). This is what makes
    #                           ∂∂ COLLAPSE to the zero chain.
    #   is_zero_chain{of}    -> the (combined) chain has NO surviving terms (DSL
    #                           IsEmpty after combine) — the ∂∂=0 witness.
    "simplex_dim": lambda a: len(list(a["of"])) - 1,
    "face": lambda a: [v for pos, v in enumerate(list(a["of"]))
                       if pos != int(a["i"])],
    "neg_one_pow": lambda a: (-1) ** int(a["i"]),
    "chain_term": lambda a: [(a["coeff"], list(a["simplex"]))],
    "combine_like_terms": lambda a: _combine_chain(a["of"]),
    "is_zero_chain": lambda a: len(_combine_chain(a["of"])) == 0,
    # scale_chain{coeff, of} -> multiply EVERY term's coefficient (linearity of
    # ∂ over a chain: ∂(c·σ) = c·∂(σ)). Mirrors a DSL MapSet over the chain.
    "scale_chain": lambda a: [(a["coeff"] * c, list(s)) for c, s in a["of"]],
    # ---- HOMOLOGY primitives (the tier ABOVE ∂ — kernel/image via matrix RANK
    # over the held boundary operator). A COMPLEX is a flat list of simplices (a
    # world-adapter input, like a chain). The Betti FORMULA — acquired by READING
    # ("b_n = dim ker ∂_n − dim im ∂_{n+1}") — composes over THESE + the held
    # minus / cardinality. Each mirrors a DSL Term shape; none knows homology.
    #   simplices_of_dim{complex,k} -> the k-simplices, stable order (DSL Filter).
    #   boundary_matrix{complex,k}  -> ∂_k as a MATRIX over the simplex bases (∂ in
    #                                  coordinates — the climb FROM the held ∂).
    #   matrix_rank{of}             -> #linearly-independent rows = Gaussian
    #                                  elimination over GF(2) (DSL field-rank).
    "simplices_of_dim": lambda a: _simplices_of_dim(a["complex"], a["k"]),
    "boundary_matrix": lambda a: _boundary_matrix(a["complex"], a["k"]),
    "matrix_rank": lambda a: _matrix_rank_gf2(a["of"]),
    # matrix_rank_q{of} -> EXACT rational rank (Gaussian elimination over Q). The
    # held-basis sibling of matrix_rank for Q-coefficient cohomology — the rational
    # coker/ker dimensions reduce to it (dim coker(L) = #rows − rank_Q(L)). Field
    # rank only; owns no (co)homology.
    "matrix_rank_q": lambda a: _matrix_rank_q(a["of"]),
    # ---- INTEGRAL HOMOLOGY / SMITH NORMAL FORM primitives (the tier ABOVE the
    # GF(2) Betti — TORSION the field rank is blind to). The signed-integer ∂ keeps
    # the alternating sign (no mod 2); its SNF over Z exposes the INVARIANT FACTORS
    # whose d_i > 1 are the torsion coefficients. The integral-homology read of
    # "H_k = Z^Betti ⊕ (⊕ Z/d_i), the d_i > 1 from SNF(∂_{k+1})" composes over THESE
    # + the held minus/cardinality. Each is held integer arithmetic; none knows
    # homology (no new Rust — the SNF reduces to the held ring ops + gcd).
    #   integer_boundary_matrix{complex,k} -> ∂_k SIGNED over Z (the held ∂, no mod 2).
    #   smith_normal_form{of}              -> the invariant factors |d_i| (SNF over Z).
    #   integral_homology{complex,k}       -> {free: Betti, torsion: [d_i > 1]}.
    "integer_boundary_matrix":
        lambda a: _integer_boundary_matrix(a["complex"], a["k"]),
    "smith_normal_form": lambda a: _smith_normal_form_factors(a["of"]),
    "integral_homology": lambda a: _integral_homology(a["complex"], a["k"]),
    # ---- RATIONAL SPIN-BORDISM COEFFICIENT RANK primitives (the tier ABOVE the
    # integer SNF — the generalized-homology coefficient ring Omega^Spin_* ⊗ Q).
    # Omega^Spin_* ⊗ Q is a POLYNOMIAL ring on a degree-4k generator each k (the
    # Pontryagin numbers), so its degree-n free rank = p(n/4) for 4|n, else 0. The
    # partition count p(m) reduces to the held integer + (the DP recurrence); the
    # 4|n test is the held mod. This is the COMPUTED-RATIONAL part (the read 2-torsion
    # of the full ring is NOT here — it is the Anderson-Brown-Peterson theorem, read,
    # not derived). No new Rust — held integer arithmetic.
    #   partition_count{of}        -> p(n), the number of integer partitions of n.
    #   spin_rational_rank{of}     -> rank Omega^Spin_n ⊗ Q = p(n/4) if 4|n else 0.
    "partition_count": lambda a: _partition_count(a["of"]),
    "spin_rational_rank": lambda a: _spin_rational_rank(a["of"]),
    # ---- ATIYAH-HIRZEBRUCH E_2-PAGE rank primitives (the tier ABOVE the coefficient
    # ring — the AHSS that assembles H_p(BG2; Omega^Spin_q) => Omega^Spin_{p+q}(BG2)).
    # Rationally MSpin splits as a product of Eilenberg-MacLane spectra (the bordism
    # is detected by Pontryagin numbers), so the AHSS COLLAPSES at E_2 ⊗ Q = E_inf ⊗ Q
    # (no rational differentials) and the free rank of E^2_{p,q} = rank H_p(BG2;Q) ·
    # rank(Omega^Spin_q ⊗ Q). The H_p rank reduces to a held monomial COUNT over the
    # Weyl ring Q[y_4,y_12] (cmsg89); the product is the held integer multiply. No new
    # Rust. (RANK only — the integral torsion differentials need BG2's full integral
    # cohomology, not held; that is the honest residual, stated plainly in the walk.)
    #   weyl_hp_rank{of}          -> rank H_p(BG2;Q) = #monomials y_4^a y_12^b, deg p.
    #   ahss_e2_rank{p,q}         -> rank E^2_{p,q} ⊗ Q = weyl_hp_rank(p)·spin_rat(q).
    "weyl_hp_rank": lambda a: _weyl_hp_rank_bg2(a["of"]),
    "ahss_e2_rank": lambda a: _ahss_e2_rank_bg2_spin(a["p"], a["q"]),
    # ---- INTEGRAL AHSS E_2-PAGE primitive (the tier ABOVE the rational rank — the
    # E_2 entry WITH its torsion, assembled from the READ integral inputs). The free
    # rank + the 2-torsion of E^2_{p,q} = H_p(BG2; Omega^Spin_q) via the universal
    # coefficient theorem (tensor + Tor) over the READ H_*(BG2;Z) torsion + the READ
    # ABP coefficient-ring torsion. The READ values are the deep inputs (BG2's integral
    # torsion + the ABP ring, labeled read-not-derived); the ASSEMBLY (the UCT tensor +
    # Tor bookkeeping) is the held integer arithmetic. No new Rust.
    #   bg2_int_homology_rank{of}     -> free rank of H_p(BG2;Z) (= weyl_hp_rank).
    #   bg2_int_torsion_2rank{of}     -> #Z/2 summands of H_p(BG2;Z) (READ G2 torsion).
    #   spin_bordism_free_rank{of}    -> free rank of Omega^Spin_q (READ ABP).
    #   spin_bordism_torsion_2rank{of}-> #Z/2 summands of Omega^Spin_q (READ ABP).
    #   bg2_integral_e2{p,q}          -> {free, torsion_2rank} of E^2_{p,q} (UCT).
    "bg2_int_homology_rank": lambda a: _bg2_integral_homology_rank(a["of"]),
    "bg2_int_torsion_2rank": lambda a: _bg2_integral_torsion_2rank(a["of"]),
    "spin_bordism_free_rank": lambda a: _spin_bordism_free_rank(a["of"]),
    "spin_bordism_torsion_2rank": lambda a: _spin_bordism_torsion_2rank(a["of"]),
    "bg2_integral_e2": lambda a: _bg2_integral_e2(a["p"], a["q"]),
    # ---- CUP PRODUCT / COHOMOLOGY RING primitives (the tier ABOVE cohomology —
    # the Alexander-Whitney cochain product over the held simplicial structure,
    # cochains = ∂^T). The agent acquires the CUP PRODUCT by READING the AW formula
    # ((α∪β)(σ) = α(front p-face) · β(back q-face)) and composing it over THESE +
    # the held simplices, EXACTLY as it acquired the Betti formula over ∂/rank. Each
    # mirrors a DSL Term shape (Filter-by-position / index-of+nth / MapSet); none
    # knows the ring.
    #   front_face{of,p}        -> the front p-face [v_0..v_p] (ordered prefix).
    #   back_face{of,q}         -> the back q-face [v_p..v_{p+q}] (ordered suffix).
    #   cochain_value{cochain,simplices,simplex} -> the cochain's value on a simplex
    #                              (the cochain pairing: index-of in the ordered
    #                              basis, then the 0/1 entry).
    #   cup_product{complex,p,q,alpha,beta} -> the (p+q)-cochain α ∪ β (the AW
    #                              formula realised over the held simplicial basis).
    #   coboundary_matrix{complex,k} -> δ^k = ∂_{k+1}^T (the held boundary matrix
    #                              transposed — the cochain complex IS the chain
    #                              complex transposed).
    "front_face": lambda a: _front_face(a["of"], a["p"]),
    "back_face": lambda a: _back_face(a["of"], a["q"]),
    "cochain_value": lambda a: _cochain_value(
        a["cochain"], a["simplices"], a["simplex"]),
    "cup_product": lambda a: _cup_product(
        a["complex"], a["p"], a["q"], a["alpha"], a["beta"]),
    "coboundary_matrix": lambda a: _coboundary_matrix(a["complex"], a["k"]),
    # ---- STEENROD SQUARE / CUP-i primitives (the tier ABOVE the cup product —
    # the higher chain homotopies that ARE the AHSS differentials). The CUP-i
    # product ∪_i (Steenrod's higher diagonal) extends the held cup product over
    # the cochain structure ∂^T: at i=0 it IS the held cup product, the higher i
    # are the extra homotopies. Sq^i(x) = x ∪_{n−i} x is the cohomology operation
    # H^n→H^{n+i}. The polynomial-ring read Sq^i(x^j) = C(j,i) x^{i+j} on
    # Z/2[x] = H*(RP^∞) follows from the total-square Cartan formula over the
    # cochain-verified base values (Sq^0=id, Sq^1 x = x^2). Held tower primitives
    # over the held cup product + held integer arithmetic (the binomial mod 2) —
    # no new Rust. The agent SPECIFIES them (runtime_design); the emitter realises
    # them over the held cup-product structure.
    #   cup_i_product{complex,p,q,i,alpha,beta} -> the (p+q−i)-cochain α ∪_i β
    #                              (Steenrod higher diagonal; i=0 = the cup product).
    #   steenrod_square{complex,n,i,x} -> Sq^i(x) = x ∪_{n−i} x, an (n+i)-cochain.
    #   steenrod_square_coeff{j,i} -> coeff of x^{i+j} in Sq^i(x^j) on Z/2[x] =
    #                              C(j,i) mod 2 (the RP^∞ polynomial-ring value).
    "cup_i_product": lambda a: _cup_i_product(
        a["complex"], a["p"], a["q"], a["i"], a["alpha"], a["beta"]),
    "steenrod_square": lambda a: _steenrod_square_cochain(
        a["complex"], a["n"], a["i"], a["x"]),
    "steenrod_square_coeff": lambda a: _steenrod_square_poly_coeff(a["j"], a["i"]),
    # ---- the multi-generator CARTAN-PRODUCT Steenrod square on the READ BG2 ring
    # Z/2[x_4,x_6,x_7]: Sq^k of a PRODUCT of generators, DERIVED by the Cartan formula
    # Sq^k(uv) = sum_{a+b=k} Sq^a(u) Sq^b(v) over the READ per-generator action
    # (Sq^2 x_4 = x_6, Sq^1 x_6 = x_7, ...). The single-generator coeff above is the
    # Z/2[x] case; THIS is the genuinely-needed extension to a product of DISTINCT
    # generators — exactly the d_2 = dual-Sq^2 value Sq^2(x_4 x_7). The per-generator
    # action is READ (labeled); the Cartan distribution + monomial multiply + mod-2 sum
    # are held arithmetic. Returns {(a,b,c): coeff} over the ring basis. No new Rust.
    #   bg2_steenrod_product{factors,k} -> dict of ring monomials of Sq^k(prod factors).
    "bg2_steenrod_product": lambda a: _bg2_steenrod_product(a["factors"], a["k"]),
    "nth_fibonacci": lambda a: _nth_fibonacci(a["of"]),
    "is_perfect_square": lambda a: _is_perfect_square(a["arg"]),
    # finitely-presented groups — a group is (generators, relators);
    # a subgroup is its generating words
    "order": lambda a: fp.coset_index(a["of"][0], a["of"][1], []),
    "index": lambda a: fp.coset_index(a["b"][0], a["b"][1], a["a"]),
    # continuous probability — a distribution bound as (family, *params)
    "expectation": lambda a: cont.mean(a["of"]),
    "variance": lambda a: cont.variance(a["of"]),
    # inference capabilities
    "next_term": lambda a: si.predict_next(a["of"]),
    "wolfram_code": lambda a: ci.infer_wolfram_code(a["of"]),
    # solving — dispatches on the bound object: a linear SYSTEM (A a matrix grid,
    # b a vector) via Cramer's rule reusing the determinant, else an EQUATION
    # (lhs, rhs expression trees) by rewriting
    "solution": lambda a: (la.solve_linear_system(a["of"][0], a["of"][1])
                           if isinstance(a["of"][0], list)
                           else eq.solve_for(a["of"][0], a["of"][1])),
}


def _bigint_log10(n) -> float:
    """log10 of a (possibly huge) integer, robust to overflow that breaks float."""
    n = abs(int(n))
    if n == 0:
        return 0.0
    s = str(n)
    return len(s) - 1 + math.log10(int(s[:1]) + int(s[1:2] or 0) / 10)


def _matsize(grid) -> int:
    """Side length of a square matrix-shaped list-of-lists, or len for a flat
    list (rough proxy for n in O(n^3) matrix ops)."""
    if isinstance(grid, list):
        return len(grid)
    return 1


def _sqrt_ops(n) -> float:
    """Cost in ops of a trial-division-style sweep up to sqrt(n). For huge n,
    return a value FAR above any plausible budget so the agent declines —
    that is the whole point: the agent SEES it's too expensive, doesn't try."""
    log_n = _bigint_log10(n)
    # ≈ 10^(log_n / 2) ops; return as a magnitude. cap representation at 1e300.
    return min(10.0 ** (log_n / 2.0), 1e300)


# Per-capability complexity estimators. Each takes the args dict (the SAME dict
# the runtime callable will see) and returns the estimated ops it would cost.
# The agent consults these BEFORE running — if the estimate exceeds its budget,
# the capability is declined upfront. The agent UNDERSTANDS the cost of its
# moves, instead of being babysat by a wall-clock timeout. Same keys as
# CAPABILITIES; a default of 1 is used for any that lack an entry here.
COMPLEXITY = {
    # linear algebra — O(n^3) on the matrix side
    "det": lambda a: _matsize(a["of"]) ** 3,
    "rank": lambda a: _matsize(a["of"]) ** 3,
    "trace": lambda a: _matsize(a["of"]),
    "invertible": lambda a: _matsize(a["arg"]) ** 3,
    # number theory — sqrt-bounded scans
    "gcd": lambda a: 64,                          # log-bounded Euclidean
    "lcm": lambda a: 64,
    "prime": lambda a: _sqrt_ops(a["arg"]),
    "even": lambda a: 1, "odd": lambda a: 1,
    "largest_prime_factor": lambda a: _sqrt_ops(a["of"]),
    "prime_factors": lambda a: _sqrt_ops(a["of"]),
    "divides": lambda a: 1,
    "plus": lambda a: 1, "times": lambda a: 1,
    "minus": lambda a: 1, "div": lambda a: 1,
    "mod": lambda a: 1, "eq": lambda a: 1,
    "gt": lambda a: 1, "lt": lambda a: 1, "ge": lambda a: 1, "le": lambda a: 1,
    # factorial: O(n) integer multiplications, but each multiplication is
    # O(d²) for d-digit numbers — return the magnitude n²
    "factorial": lambda a: max(int(a["of"]) ** 2, 1),
    # totient / divisor functions: dominated by the trial-division factorisation
    "totient": lambda a: _sqrt_ops(a["of"]),
    "divisor_count": lambda a: _sqrt_ops(a["of"]),
    "divisor_sum": lambda a: _sqrt_ops(a["of"]),
    # collection / iteration primitives — a range is O(n) to build, a scan O(n);
    # the binders (count_where / sum_where) cost the range length × the body.
    "range_incl": lambda a: max(int(a["hi"]) - int(a["lo"]) + 1, 1),
    "cardinality": lambda a: max(len(list(a["of"])), 1),
    "member": lambda a: max(len(list(a["of"])), 1),
    "is_empty": lambda a: 1,
    "intersection": lambda a: max(len(list(a["a"])) + len(list(a["b"])), 1),
    "are_disjoint": lambda a: max(len(list(a["a"])) + len(list(a["b"])), 1),
    # structured-object primitives — a face is O(dim), a combine O(terms²).
    "simplex_dim": lambda a: 1,
    "face": lambda a: max(len(list(a["of"])), 1),
    "neg_one_pow": lambda a: 1,
    "chain_term": lambda a: 1,
    "combine_like_terms": lambda a: max(len(list(a["of"])) ** 2, 1),
    "is_zero_chain": lambda a: max(len(list(a["of"])) ** 2, 1),
    "scale_chain": lambda a: max(len(list(a["of"])), 1),
    # homology primitives — a complex scan is O(simplices), a boundary matrix is
    # O(simplices²), a GF(2) rank is O(rows·cols²).
    "simplices_of_dim": lambda a: max(len(list(a["complex"])), 1),
    "boundary_matrix": lambda a: max(len(list(a["complex"])) ** 2, 1),
    "matrix_rank": lambda a: max(len(list(a["of"])) ** 2 + 1, 1),
    "matrix_rank_q": lambda a: max(len(list(a["of"])) ** 2 + 1, 1),
    # integral homology / SNF — the signed boundary matrix is O(simplices²); the
    # SNF over Z is integer Gaussian elimination, O(rows·cols·min(rows,cols)).
    "integer_boundary_matrix": lambda a: max(len(list(a["complex"])) ** 2, 1),
    "smith_normal_form": lambda a: max(len(list(a["of"])) ** 3 + 1, 1),
    "integral_homology": lambda a: max(len(list(a["complex"])) ** 3, 1),
    # rational spin-bordism rank — the partition DP is O(n^2) over the held integer +.
    "partition_count": lambda a: max(int(a["of"]) ** 2, 1),
    "spin_rational_rank": lambda a: max((int(a["of"]) // 4) ** 2, 1),
    # AHSS E_2-page ranks — the Weyl monomial count is O(p/4), the E_2 entry is the
    # held integer multiply of the two rank read-outs.
    "weyl_hp_rank": lambda a: max(int(a["of"]) // 4 + 1, 1),
    "ahss_e2_rank": lambda a: max(int(a["p"]) // 4 + int(a["q"]) // 4 + 1, 1),
    # integral AHSS E_2 entry — the UCT assembly (tensor + Tor) over the read inputs
    # is a constant number of held integer multiplies/adds.
    "bg2_int_homology_rank": lambda a: max(int(a["of"]) // 4 + 1, 1),
    "bg2_int_torsion_2rank": lambda a: 1,
    "spin_bordism_free_rank": lambda a: max((int(a["of"]) // 4) ** 2, 1),
    "spin_bordism_torsion_2rank": lambda a: 1,
    "bg2_integral_e2": lambda a: max(int(a["p"]) // 4 + int(a["q"]) // 4 + 1, 1),
    # cup-product / cohomology-ring primitives — a face slice is O(dim), a cochain
    # lookup is O(#simplices), the cup product is O(#(p+q)-simplices · #simplices).
    "front_face": lambda a: 1,
    "back_face": lambda a: 1,
    "cochain_value": lambda a: max(len(list(a["simplices"])), 1),
    "cup_product": lambda a: max(len(list(a["complex"])) ** 2, 1),
    "coboundary_matrix": lambda a: max(len(list(a["complex"])) ** 2, 1),
    # steenrod-square / cup-i primitives — the cup-i sums over C(N, i+1) cut-point
    # subsets per (p+q−i)-simplex; surface as O(#simplices · 2^dim) for safety. The
    # polynomial-ring coeff is one held binomial mod 2 (O(1)).
    "cup_i_product": lambda a: max(len(list(a["complex"])) ** 2 * (2 ** 6), 1),
    "steenrod_square": lambda a: max(len(list(a["complex"])) ** 2 * (2 ** 6), 1),
    "steenrod_square_coeff": lambda a: 1,
    # the Cartan-product square: O(#compositions of k into #factors) per the held
    # distribution — a small constant for the degree-bounded BG2 generators.
    "bg2_steenrod_product": lambda a: max(len(list(a["factors"])) ** int(a["k"]), 1),
    # nth_fibonacci: O(log n) multiplications, but each mul is O(d²) for the
    # ~n·log(φ)-digit result — surface as n² for safety
    "nth_fibonacci": lambda a: max(int(a["of"]) ** 2, 1),
    "is_perfect_square": lambda a: 1,
    # finitely-presented groups — coset enumeration ≈ index × relator length;
    # for an unknown bound, assume ≤ 10^4 (enough for hand-sized presentations)
    "order": lambda a: 1_000,
    "index": lambda a: 1_000,
    # continuous probability — closed-form moments
    "expectation": lambda a: 1, "variance": lambda a: 1,
    # inference capabilities — linear scans over the sequence
    "next_term": lambda a: max(len(a["of"]) ** 2, 100)
                     if isinstance(a.get("of"), list) else 100,
    "wolfram_code": lambda a: 1_000,
    "solution": lambda a: 10_000,
}


class BudgetExceeded(Exception):
    """Raised when no strategy (default + every alternative) the agent has for a
    concept fits within the budget. The estimate + budget are on the exception
    so the gap-map can record what it would have cost."""

    def __init__(self, concept: str, est: float, budget: float):
        super().__init__(f"{concept}: ~{est:.2e} ops vs {budget:.2e} budget")
        self.concept = concept
        self.estimate = est
        self.budget = budget


class UnknownShape(Exception):
    """Raised by ``answer_within`` as the call-site signal when no Frame
    matched AND no teacher is available. The agent has already recorded an
    Impasse in its graph — this exception is just the control-flow surface
    for callers that want a Python-level handler (e.g. HLEWorld.run_solve)."""


# --- RECONSIDER — when the default plan blows the budget, the agent doesn't
# bail. It asks "is there a more efficient way?" + "is this in a special form
# I can exploit (e.g. a G+X structure)?" before giving up. Alternatives below
# encode those reconsiderations: cheaper algorithms AND structural exploits.

def _is_probably_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 3.3 × 10^14, virtually-certain for
    larger n with this witness set — a cheap primality check the structural
    alternatives use to know when stripping small primes was enough."""
    n = int(n)
    if n < 2:
        return False
    witnesses = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in witnesses:
        if n == p:
            return True
        if n % p == 0:
            return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in witnesses:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


class _CantApply(Exception):
    """An alternative says it can't handle this instance — try the next one."""


def _largest_prime_factor_strip_smalls(args, bound: int = 100_000):
    """STRUCTURAL alternative for ``largest_prime_factor``: strip small primes
    cheaply (≈ ``bound`` divisions). For an n like 10^100 = 2^100 × 5^100 the
    answer falls out in microseconds. For an n whose largest prime factor is
    huge AND coprime to all small primes, we surface _CantApply so the caller
    tries the next strategy."""
    n = int(args["of"])
    largest = 1
    d = 2
    while d <= bound and d * d <= n:
        if n % d == 0:
            while n % d == 0:
                n //= d
            largest = d
        d += 1
    if n == 1:
        return largest
    if n <= bound * bound:           # cofactor is small enough to factor outright
        return max(largest, max(_factorize(n)))
    if _is_probably_prime(n):
        return max(largest, n)
    raise _CantApply("largest_prime_factor: residue is large + composite")


ALTERNATIVES = {
    "largest_prime_factor": [
        ("strip_small_primes",
         _largest_prime_factor_strip_smalls,
         lambda a: 200_000),
    ],
    "prime_factors": [
        ("strip_small_primes",
         lambda a: sorted(set([_largest_prime_factor_strip_smalls(a)])),
         lambda a: 200_000),
    ],
}


def reconsider(concept: str, args: dict, budget: float,
               attempted=()) -> tuple:
    """Default plan would blow the budget — try the alternatives this concept
    declares. Pick the cheapest whose estimator fits the budget AND whose
    body successfully applies; return ``(answer, est, strategy_name)``. If no
    alternative both fits and applies, re-raise ``BudgetExceeded``."""
    candidates = []
    for name, body, estimator in ALTERNATIVES.get(concept, []):
        if name in attempted:
            continue
        try:
            est = float(estimator(args))
        except Exception:
            est = float("inf")
        if est <= budget:
            candidates.append((est, name, body))
    candidates.sort()
    for est, name, body in candidates:
        try:
            return body(args), est, name
        except _CantApply:
            continue
    raise BudgetExceeded(concept + ":no_alternative", float("inf"), budget)


def estimate_complexity(meaning, bindings: dict) -> float:
    """Walk the comprehended meaning and SUM the estimated ops of every
    capability call along the way. Inner expressions are materialised (they
    must be cheap for their own estimator to fire); the outer estimator is
    consulted with those materialised values. Returns the cumulative ops."""
    if isinstance(meaning, (bool, int, float)) or isinstance(meaning, str):
        return 0
    concept = next(k for k in meaning if k != "force")
    total = 0.0
    materialised: dict = {}
    for role, child in meaning[concept].items():
        total += estimate_complexity(child, bindings)
        # materialise the inner expression so the outer estimator gets the
        # real value (e.g., int 8139881) and can estimate sqrt-ops accurately
        materialised[role] = solve(child, bindings)
    estimator = COMPLEXITY.get(concept, lambda a: 1)
    try:
        own = float(estimator(materialised))
    except Exception:
        own = 1.0
    return total + own


def solve_within(meaning, bindings: dict, budget_ops: float,
                 capabilities=None):
    """Like ``solve``, but the agent first ESTIMATES the cost of the planned
    computation against its budget. If the estimate fits, the default plan
    runs and we return ``(answer, est, "default")``. If it exceeds, the agent
    RECONSIDERS — does this concept declare a cheaper alternative? a structural
    exploit (the G+X / strip-small-primes shape)? — and tries each one in cost
    order. Only when no strategy fits does it raise ``BudgetExceeded``."""
    caps = capabilities or CAPABILITIES
    est = estimate_complexity(meaning, bindings)
    if est <= budget_ops:
        return solve(meaning, bindings, caps), est, "default"
    if not isinstance(meaning, dict):
        raise BudgetExceeded("<value>", est, budget_ops)
    concept = next(k for k in meaning if k != "force")
    # materialise the IMMEDIATE args (inner expressions are evaluated with the
    # default plan; their own reconsider is a future iteration)
    args = {role: solve(child, bindings, caps)
            for role, child in meaning[concept].items()}
    ans, alt_est, strategy = reconsider(concept, args, budget_ops)
    return ans, alt_est, f"reconsider:{strategy}"


def answer_within(question: str, bindings: dict, budget_ops: float,
                  lexicon=None, teacher=None, agent=None):
    """Comprehend a natural-language question and answer it WITHIN a complexity
    budget. When an ``agent`` is supplied, recognition runs through its
    graph-native FRAME LAYER — Frame evocation + Microtheory scope check +
    core-element binding — and the matched Frame's ``realised_by`` Concept is
    routed to its capability. If no Frame matches, the agent records an
    IMPASSE (graph data) and escalates to the teacher when one is available.
    Without an agent the older Python shape recogniser is used (legacy path).

    Returns ``(answer, estimated_ops, strategy)``; ``strategy`` is ``"default"``
    when the agent's first plan fit, ``"reconsider:<name>"`` for a cheaper
    alternative, ``"taught"`` when the teacher answered an unrecognised
    question, and ``"learned"`` when the agent answered from a capability
    that came from a previous teaching."""
    from domains.language import comprehend, core_lexicon

    if agent is not None:
        # GRAPH-NATIVE path: ask the agent's Frame layer.
        frame_id, slots, _fok = agent.recognise_frame(question)
        if frame_id is None:
            # The agent records the no-match outcome as graph data — SOAR's
            # impasse — before deciding what to do about it. The question
            # text lands on the Impasse node so a self-teaching pass can
            # find it later.
            imp_id = agent.impasse(over=None, reason="no Frame matched",
                                   question=question)
            # Try the external teacher first; if it doesn't have an answer
            # (or wasn't supplied), fall back to the agent's registered
            # self-teacher (set_self_teacher) — autonomous learning from
            # its own impasses.
            taught = teacher(question) if teacher is not None else None
            if taught is None and getattr(
                    agent, "_self_teacher", None) is not None:
                taught = agent._self_teacher(question)
            if taught is None:
                # Last resort: per-word grounding. The whole-question
                # teacher couldn't ground a single subject; try each
                # unknown token individually. If anything new lands, the
                # Frame layer gets another pass with the grown lexicon —
                # multi-concept questions like 'what is X and Y?' make
                # progress this way even when no single-subject lookup
                # matches.
                word_teacher = teacher or getattr(
                    agent, "_self_teacher", None)
                if word_teacher is not None:
                    newly_learnt = agent.ground_unknowns(
                        question, word_teacher)
                    if newly_learnt:
                        frame_id, slots, _fok = agent.recognise_frame(
                            question)
                        if frame_id is not None:
                            # fall through to the success path below
                            agent.mark_impasse_resolved(imp_id)
                if frame_id is None:
                    raise UnknownShape(
                        f"shape unknown and teacher couldn't help:"
                        f" {question[:80]!r}")
            else:
                answer = agent.learn_from_teacher(question, taught)
                agent.mark_impasse_resolved(imp_id)
                return answer, 0.0, "taught"
        # A Frame matched → its realised_by Concept names the capability
        # solve will dispatch to, with the slot bindings as args.
        meaning = agent._meaning_from_frame(frame_id, slots)
        caps = dict(CAPABILITIES)
        caps.update(agent.taught_capabilities())
        # runtime capabilities answer about the agent's own engine — perf
        # stats, op counts, etc. — so the agent can introspect itself
        # through the same answer_within pipeline.
        caps.update(agent.runtime_capabilities())
        ans, est, strategy = solve_within(meaning, bindings, budget_ops, caps)
        # Surface a taught-then-routed answer as "learned" rather than "default"
        if strategy == "default":
            concept = next((k for k in meaning if k != "force"), None)
            if concept is not None and concept in agent._taught_lookup:
                strategy = "learned"
        return ans, est, strategy

    # No agent supplied → comprehend + solve directly. Recognition is a
    # property of an agent's installed Frame library; without one there's
    # nothing to recognise from, so we just route through the static
    # CAPABILITIES via the existing comprehender. Callers that want
    # graph-native recognition supply an agent.
    signs = list(lexicon or core_lexicon())
    meaning = comprehend(question, signs)[0]
    ans, est, strategy = solve_within(meaning, bindings, budget_ops)
    return ans, est, strategy


# The ITERATION (binder) heads — operations over a COLLECTION that bind a free
# variable over each element. Unlike the scalar heads above, their `predicate` /
# `value` sub-term is NOT evaluated eagerly: it is re-solved once PER element with
# the binder variable bound (the interpreter mechanism for iteration — the same
# shape as the DSL's `Fold` / `Filter{source, var_name, predicate}` evaluators).
# `solve` special-cases these so the body sees each binding; everything else is
# the eager dispatch. This is interpreter machinery (a binder evaluator), NOT an
# agent decision — the collection OPERATIONS the agent acquires by reading compose
# OVER these binders, they are not these binders.
#
# chain_sum{var in lo..hi : body} is the STRUCTURED-OBJECT binder: the same
# binder shape, but its body evaluates to a CHAIN (a list of (coeff,simplex)
# terms) per element, and the results are CONCATENATED into one chain (the formal
# SUM over i). This is how ∂ = Σ_i (-1)^i face_i(σ) is realised — a sum-over-i
# producing a chain, not a scalar. Mirrors the DSL MapSet/Fold binder.
#
# chain_bind{(coeff_var, simplex_var) in CHAIN : body} iterates a CHAIN's terms,
# binding each term's COEFFICIENT and SIMPLEX, body -> a chain, concatenated. This
# extends ∂ over a chain BY LINEARITY (∂∂ applies the outer ∂ to the inner ∂'s
# chain) — the move ∂∂=0 needs. The `var` role carries [coeff_var, simplex_var].
_ITERATION_HEADS = {"count_where", "sum_where", "chain_sum", "chain_bind"}


def solve(meaning, bindings: dict, capabilities=None):
    """Answer a comprehended meaning Term: numbers are themselves, names resolve
    against ``bindings`` (the objects the question refers to), and a head concept
    has its arguments solved then routed to its capability. ``capabilities``
    defaults to ``CAPABILITIES`` (the static registry) but accepts a merged dict
    so a per-call extension (e.g. agent-taught capabilities) is routable here.
    Raises if a concept has no capability.

    ITERATION heads (``count_where`` / ``sum_where``) bind a free variable over a
    COLLECTION: their ``source`` is evaluated to a concrete collection (e.g. a
    range 1..n), then the ``predicate`` / ``value`` sub-term is re-solved once per
    element with the binder bound. This is the binder evaluator — the Python-tower
    analogue of the DSL's ``Fold`` / ``Filter`` evaluators."""
    caps = capabilities or CAPABILITIES
    if isinstance(meaning, bool) or isinstance(meaning, (int, float)):
        return meaning
    # an exact RATIONAL literal (Fraction) is a scalar value — pass it through (it is
    # NOT a Term dict to descend into). Lets exact rational arithmetic flow as givens.
    if isinstance(meaning, _Fraction):
        return meaning
    if isinstance(meaning, str):
        return bindings.get(meaning, meaning)
    # a COLLECTION literal (an explicit small set, e.g. {3,5,7} bound as a list)
    # is a value — pass it through. The collection OPERAND is a representation; a
    # range is produced by range_incl, an explicit set is a list literal.
    if isinstance(meaning, (list, tuple)):
        return [solve(el, bindings, caps) for el in meaning]
    concept = next(k for k in meaning if k != "force")

    # ITERATION over a collection: evaluate the source to a concrete collection,
    # then walk it binding the loop variable, re-solving the body each step. The
    # body is held UNEVALUATED in the meaning-Term (it references the binder var).
    if concept in _ITERATION_HEADS:
        spec = meaning[concept]
        source = solve(spec["source"], bindings, caps)
        var = spec["var"]               # the binder name (a literal string)
        # chain_bind carries a PAIR of binder names [coeff, simplex] (read in its
        # own branch); the other binders carry a single name.
        if not isinstance(var, str) and concept != "chain_bind":
            var = solve(var, bindings, caps)
        if concept == "count_where":
            body = spec["predicate"]
            n = 0
            for el in source:
                inner = dict(bindings)
                inner[var] = el
                if solve(body, inner, caps):
                    n += 1
            return n
        if concept == "chain_sum":
            # the STRUCTURED-OBJECT binder: each body is a CHAIN (a list of
            # (coeff, simplex) terms); CONCATENATE them into the formal sum over i.
            body = spec["value"]
            chain: list = []
            for el in source:
                inner = dict(bindings)
                inner[var] = el
                part = solve(body, inner, caps)
                chain.extend(list(part))
            return chain
        if concept == "chain_bind":
            # iterate a CHAIN's terms, binding each term's COEFFICIENT + SIMPLEX
            # (var = [coeff_name, simplex_name]); body -> a chain, concatenated.
            # ∂ extended over a chain by linearity.
            body = spec["value"]
            coeff_name, simplex_name = spec["var"]
            chain = []
            for term in source:
                coeff, simplex = term
                inner = dict(bindings)
                inner[coeff_name] = coeff
                inner[simplex_name] = list(simplex)
                part = solve(body, inner, caps)
                chain.extend(list(part))
            return chain
        # sum_where
        body = spec["value"]
        total = 0
        for el in source:
            inner = dict(bindings)
            inner[var] = el
            total += solve(body, inner, caps)
        return total

    args = {role: solve(child, bindings, caps)
            for role, child in meaning[concept].items()}
    if concept not in caps:
        raise KeyError(f"no capability grounds '{concept}'")
    return caps[concept](args)


def answer(question: str, bindings: dict, lexicon=None):
    """Comprehend a natural-language question and answer it: text → meaning Term
    → grounded computation. ``bindings`` maps the question's object names to real
    values (M → a matrix grid, G → (generators, relators), the sequence → a list)."""
    from domains.language import comprehend, core_lexicon
    meaning = comprehend(question, lexicon or core_lexicon())[0]
    return solve(meaning, bindings)
