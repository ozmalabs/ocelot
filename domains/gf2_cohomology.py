"""gf2_cohomology — the HELD GF(2) CUP-LENGTH of a simplicial complex, composed over
the agent's held cohomology tower (reason._cup_product / _coboundary_matrix /
_simplices_of_dim — the Alexander-Whitney cochain product the cmsg84-96 ladder
acquired). NO new primitive, NO Rust: GF(2) linear algebra over the held coboundary +
the held cup product.

The cup-length is the LS-category lower bound the ground_definition faculty SEEKS for
the LS-category invariant (the infinite "min over coverings" family reduces to this
HELD compute — the cup-length<=cat bound, achieved on closed surfaces). Pulled out of
the cmsg126 lookup SCRIPT into a held domain so BOTH the faculty's reduction and the
script's stall-3 grounding reduce to the SAME held compute (no duplication).

Composes over reason (held): _simplices_of_dim, _coboundary_matrix (= boundary^T),
_cup_product. See [[ozma_HLE_derivation_engine]] / [[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

from domains import reason as _reason


# --- GF(2) linear algebra (the held field arithmetic the homology read uses). ---

def _rref(M):
    M = [r[:] for r in M]
    rows = len(M)
    cols = len(M[0]) if rows else 0
    piv = []
    r = 0
    for c in range(cols):
        sel = next((i for i in range(r, rows) if M[i][c] & 1), None)
        if sel is None:
            continue
        M[r], M[sel] = M[sel], M[r]
        for i in range(rows):
            if i != r and M[i][c] & 1:
                M[i] = [(a ^ b) & 1 for a, b in zip(M[i], M[r])]
        piv.append(c)
        r += 1
    return M[:r], piv


def _rank(M):
    return len(_rref(M)[1]) if M else 0


def _cols(M):
    return [[M[r][c] for r in range(len(M))] for c in range(len(M[0]))] if M else []


def _null(M, n):
    if not M:
        return [[1 if i == j else 0 for i in range(n)] for j in range(n)]
    R, p = _rref(M)
    ps = set(p)
    free = [c for c in range(n) if c not in ps]
    B = []
    for f in free:
        v = [0] * n
        v[f] = 1
        for ri, pc in enumerate(p):
            v[pc] = R[ri][f] & 1
        B.append(v)
    return B


def _inspan(v, rows):
    return _rank(rows + [v]) == _rank(rows)


def _Hbasis(cx, k):
    """A GF(2) cohomology-class basis at degree k: 1-cocycles (ker delta^k) modulo
    coboundaries (im delta^{k-1}). The HELD coboundary_matrix is delta = boundary^T."""
    nC = len(_reason._simplices_of_dim(cx, k))
    if nC == 0:
        return []
    Z = _null(_reason._coboundary_matrix(cx, k), nC)
    B = _cols(_reason._coboundary_matrix(cx, k - 1)) if k > 0 else []
    cur = [r[:] for r in B]
    h = []
    for z in Z:
        if not _inspan(z, cur):
            h.append(z)
            cur = cur + [z]
    return h


def _nz(cx, k, c):
    B = _cols(_reason._coboundary_matrix(cx, k - 1)) if k > 0 else []
    return any(c) and not _inspan(c, B)


def cup_length_gf2(cx, dim=2):
    """The GF(2) CUP-LENGTH of a simplicial complex: the longest product of
    positive-degree cohomology classes that is nonzero (the LS-category lower bound).
    Reduces to the HELD cup_product over the held cohomology basis. Caps at `dim`."""
    b1 = _Hbasis(cx, 1)
    best = 0
    # length-1: any nonzero positive-degree class (incl. a top H^2 generator).
    for k in range(1, dim + 1):
        for v in _Hbasis(cx, k):
            if _nz(cx, k, v):
                best = max(best, 1)
    # length-2: a nonzero product of two degree-1 classes (the surface case).
    for a in b1:
        for b in b1:
            if 1 + 1 <= dim:
                prod = _reason._cup_product(cx, 1, 1, a, b)
                if _nz(cx, 2, prod):
                    best = max(best, 2)
    return best


# --- the KNOWN surfaces (textbook triangulations) the verify-vs-known uses. NONE
# is a question's answer. ---

def _faces_closure(triangles):
    cx = set()
    for t in triangles:
        t = sorted(t)
        cx.add(tuple(t))
        for i in range(len(t)):
            for j in range(i + 1, len(t)):
                cx.add((t[i], t[j]))
        for v in t:
            cx.add((v,))
    return [list(s) for s in cx]


def _torus_complex():
    """The held minimal 7-vertex (Mobius) torus triangulation (compute_homology.py)."""
    from compute_homology import TORUS
    return TORUS


KNOWN_SURF = {
    "S^2": _faces_closure([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]),
    "T^2": _torus_complex(),
    "RP^2": _faces_closure([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5], [0, 1, 5],
                            [1, 2, 4], [2, 3, 5], [1, 3, 4], [2, 4, 5], [1, 3, 5]]),
}
# KNOWN cup-lengths (READ, standard): S^2 -> 1, T^2 -> 2, RP^2 -> 2. min crit = +1.
KNOWN_CUPLEN = {"S^2": 1, "T^2": 2, "RP^2": 2}


__all__ = ["cup_length_gf2", "KNOWN_SURF", "KNOWN_CUPLEN"]
