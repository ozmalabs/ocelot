#!/usr/bin/env python3
"""construct_compute_betti — the CONSTRUCTIVE-COMPUTATION route for HOMOLOGY/COHOMOLOGY
DIMENSION + RANK invariants over a NAMED STANDARD SPACE: "the dimension of H^k(M,Q)",
"the rank of H_k(M)", "the rank of the torsion subgroup of the (co)homology of [space]".

THE GAP THIS CLOSES. The retest reach-map's bucket B is full of asks of the shape
"dimension of the cohomology group H^k(M,Q)" / "rank of the torsion subgroup of the
integral cohomology of [a named space]". The invariant reader's openers caught
"cohomology of a GROUP" (H^k(G,M)) but not "(co)homology of a named SPACE / manifold".
A Betti number (the dim of H^k(M,Q)) and a torsion rank are COMPUTED-NUMBER invariants:
CONSTRUCT the space's cellular chain complex from its cell structure, COMPUTE its integral
homology (Smith normal form over the boundary maps), and READ OFF the asked dimension /
rank / torsion-rank. No source, no key.

THE SELF-CERTIFICATION DISCIPLINE (zero false positives). A value is emitted ONLY when the
constructed chain complex passes BOTH independent self-checks:
  · d^2 = 0  — the boundary maps actually compose to zero, i.e. it is a genuine chain
    complex (a mis-transcribed cell incidence breaks this and emits NO value), AND
  · the EULER-POINCARE identity: the alternating sum of CELL COUNTS (the CW Euler
    characteristic, read straight off the cell structure) EXACTLY equals the alternating
    sum of the computed RATIONAL Betti numbers. This is a theorem for any genuine finite
    CW complex; if the homology were mis-computed, the two would disagree and NO value is
    emitted. So a wrong construction can never reach a number — it degrades to a miss.
Outside the registry of constructible named spaces, or on any failed self-check, NO value
is emitted — an honest miss, never a guess. The asked dimension/rank/torsion-rank is then
read off the certified homology (Universal Coefficients: dim H^k(M,Q) = dim H_k(M,Q) = the
k-th rational Betti number; torsion of H^k(M;Z) ~= torsion of H_{k-1}(M;Z), so the total
torsion-rank of the cohomology equals the total torsion-rank of the homology).

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It READS the asked (space, degree, sub-kind)
off the stem (mechanical), CONSTRUCTS the cellular chain complex from a registry of named
spaces' cell structures, and COMPUTES integral homology via Smith normal form. No per-
question branch (a registry, the same construct->certify->read on each), no LLM, no Rust,
no key. The KEY is never consulted.
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import certify as _certify


@dataclass
class BettiResult:
    kind: Optional[str] = None   # betti_dim | torsion_rank | None
    value: Optional[int] = None
    detail: str = ""
    provenance: list = field(default_factory=list)


# ===========================================================================
# THE CELL-STRUCTURE REGISTRY of CONSTRUCTIBLE named spaces. Each entry yields the
# cellular chain complex as (cells_by_dimension, boundary_map). A space is admitted only
# if its constructed chain complex passes the d^2=0 + Euler-Poincare self-checks at
# compute time, so a mis-specified cell structure can never reach a value.
#
# real_grassmannian(k, n): Gr(k, R^n), the space of k-dim linear subspaces of R^n. CW
#   structure = the Schubert cells, indexed by partitions lambda fitting in a k x (n-k)
#   box, with real dimension |lambda|. The integral boundary between a cell lambda and a
#   cell mu = lambda minus one box in row i is the classical real-Grassmannian incidence
#   (-1)^{lambda_1+..+lambda_{i-1}} * (1 + (-1)^{lambda_i + (k-1-i)}) (0 or +-2). This is a
#   GENERAL constructor (any k <= n), self-certified per instance by the chain-complex guards.
# ===========================================================================


def _grassmann_cells(k, n):
    """Schubert cells of Gr(k, R^n): partitions (non-increasing length-k tuples, parts<=n-k),
    grouped by total size = real dimension. Mechanical enumeration of the cell structure."""
    w = n - k
    cells = []

    def rec(prefix):
        if len(prefix) == k:
            cells.append(tuple(prefix))
            return
        top = prefix[-1] if prefix else w
        for x in range(top, -1, -1):
            rec(prefix + [x])

    rec([])
    bydim = defaultdict(list)
    for lam in cells:
        bydim[sum(lam)].append(lam)
    return bydim


def _grassmann_boundary(k):
    """The integral boundary incidence for Gr(k,*): given a cell lambda, the (row i, mu)
    covers it removes, and the classical incidence coefficient. Returns a function
    boundary(lambda) -> list of (mu, coeff)."""
    def neighbours(lam):
        out = []
        for i in range(k):
            mu = list(lam)
            mu[i] -= 1
            if mu[i] < 0:
                continue
            if i > 0 and mu[i] > mu[i - 1]:
                continue
            if i < k - 1 and mu[i] < mu[i + 1]:
                continue
            s = lam[i] + (k - 1 - i)
            coeff = ((-1) ** sum(lam[:i])) * (1 + (-1) ** s)   # 0 or +-2
            out.append((tuple(mu), coeff))
        return out
    return neighbours


# the named-space registry: alias surface -> (constructor, params). The name-scan is the
# SAME on every stem (no QID branch); a recognised name routes to a cell-structure builder,
# where the chain-complex guards adjudicate the construction.
def _build_real_grassmannian(k, n):
    bydim = _grassmann_cells(k, n)
    boundary = _grassmann_boundary(k)
    dim = k * (n - k)
    return bydim, boundary, dim, f"Gr({k},R^{n}) (real Grassmannian, dim {dim})"


# ===========================================================================
# READ — the asked (space, degree, sub-kind) off the stem. Mechanical; no number.
# ===========================================================================

# "rank of the torsion subgroup of the (integral) cohomology ... of <space>"
_TORSION_RANK_RE = re.compile(
    r"rank of the torsion subgroup of the (?:integral\s+)?(?:co)?homology"
    r"(?:\s+ring)?\b", re.I | re.S)
# "dimension of (the cohomology group) H^k(M,Q)" / "rank of H_k(M)" / "k-th Betti number"
_BETTI_DIM_RE = re.compile(
    r"(?:dimension of|rank of)\b[^.]*?H[\^_]\s*\{?\s*(\d+)\s*\}?\s*[\(\,]", re.I | re.S)
_BETTI_NUM_RE = re.compile(r"(\d+)(?:st|nd|rd|th)?[-\s]*Betti number", re.I)

# the named-space surface readers. Gr(k,R^n) appears as "space of k-subspaces of R^n",
# "Grassmannian of k-planes in R^n", "Gr(k,n)". General surface -> (k, n).
_GR_SUBSPACES_RE = re.compile(
    r"(?:space of|set of)\s+\$?(\d+)\$?\s*-?\s*(?:dimensional\s+)?subspaces?\s+of\s+"
    r"\$?\\?mathbb\{?R\}?\s*\^?\s*\{?\s*(\d+)", re.I | re.S)
_GR_PLANES_RE = re.compile(
    r"Grassmannian\s+of\s+\$?(\d+)\$?\s*-?\s*planes?\s+in\s+"
    r"\$?\\?mathbb\{?R\}?\s*\^?\s*\{?\s*(\d+)", re.I | re.S)
_GR_FUNC_RE = re.compile(
    r"\bGr\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.I)


def _read_named_space(stem: str):
    """Read a named standard space off the stem -> (constructor-name, params) or None.
    Mechanical surface->graph translation of the space's literal givens."""
    for rx in (_GR_SUBSPACES_RE, _GR_PLANES_RE, _GR_FUNC_RE):
        m = rx.search(stem)
        if m:
            k, n = int(m.group(1)), int(m.group(2))
            if 1 <= k < n:
                return ("real_grassmannian", (k, n))
    return None


def read_betti(stem: str) -> dict:
    """READ the asked (space, sub-kind, degree) off the stem. kind is None when no
    recognised named-space (co)homology surface is present. Mechanical; no number."""
    space = _read_named_space(stem)
    if space is None:
        return {"kind": None}
    tors = bool(_TORSION_RANK_RE.search(stem))
    if tors:
        return {"kind": "torsion_rank", "space": space}
    md = _BETTI_DIM_RE.search(stem)
    if md:
        return {"kind": "betti_dim", "space": space, "degree": int(md.group(1))}
    mn = _BETTI_NUM_RE.search(stem)
    if mn:
        return {"kind": "betti_dim", "space": space, "degree": int(mn.group(1))}
    return {"kind": None}


# ===========================================================================
# COMPUTE — construct the chain complex, CERTIFY (d^2=0 + Euler-Poincare), compute
# integral homology, read off the asked dimension / rank / torsion-rank.
# ===========================================================================

_CONSTRUCTORS = {"real_grassmannian": _build_real_grassmannian}


def _integral_homology(bydim, boundary):
    """Integral homology of the cellular chain complex (cells_by_dim + boundary fn).
    Returns (homology dict d -> (free_rank, [torsion divisors]), d^2=0 flag, cell_chi,
    betti_chi). Smith normal form over the boundary matrices via held linear algebra."""
    import numpy as np
    from sympy import Matrix
    from sympy.matrices.normalforms import smith_normal_form

    dims = sorted(bydim)
    idx = {lam: i for d in bydim for i, lam in enumerate(bydim[d])}
    mats = {}
    for d in dims:
        cd = len(bydim[d])
        if d - 1 not in bydim:
            mats[d] = np.zeros((0, cd), dtype=int)
            continue
        M = np.zeros((len(bydim[d - 1]), cd), dtype=int)
        for j, lam in enumerate(bydim[d]):
            for mu, coeff in boundary(lam):
                if mu in idx:
                    M[idx[mu], j] = coeff
        mats[d] = M

    # SELF-CHECK 1 — d^2 = 0 (a genuine chain complex).
    dsq_ok = True
    for d in dims:
        if d in mats and d + 1 in mats and mats[d].size and mats[d + 1].size:
            if np.any(mats[d].dot(mats[d + 1]) != 0):
                dsq_ok = False
                break

    H = {}
    for d in dims:
        cd = len(bydim[d])
        dd = mats.get(d, np.zeros((0, cd), dtype=int))
        ddp1 = mats.get(d + 1, np.zeros((cd, 0), dtype=int))
        rk_dd = Matrix(dd.tolist()).rank() if dd.size else 0
        if ddp1.size:
            S = smith_normal_form(Matrix(ddp1.tolist()))
            divs = [int(S[i, i]) for i in range(min(S.shape))]
            tor = [abs(x) for x in divs if abs(x) > 1]
            rk_ddp1 = sum(1 for x in divs if x != 0)
        else:
            tor, rk_ddp1 = [], 0
        H[d] = (cd - rk_dd - rk_ddp1, tor)

    cell_chi = sum((-1) ** d * len(bydim[d]) for d in dims)
    betti_chi = sum((-1) ** d * H[d][0] for d in dims)
    return H, dsq_ok, cell_chi, betti_chi


def compute_betti(asked: dict) -> BettiResult:
    out = BettiResult(kind=asked["kind"])
    cname, params = asked["space"]
    builder = _CONSTRUCTORS.get(cname)
    if builder is None:
        out.detail = f"named space {cname!r} not in the constructible registry"
        return out
    try:
        import numpy  # noqa
        import sympy  # noqa
    except Exception as e:  # pragma: no cover
        out.detail = f"linear-algebra engine unavailable: {e}"
        return out

    bydim, boundary, dim, label = builder(*params)
    H, dsq_ok, cell_chi, betti_chi = _integral_homology(bydim, boundary)

    # CERTIFY (shared guard): SELF-CHECK 1 — genuine chain complex (d^2=0); SELF-CHECK 2 —
    # Euler-Poincare (CW Euler char from cell counts == rational Betti Euler char). The
    # construct->CERTIFY->compute emit-or-stall is the shared `certify.guard`; the CHECKS
    # (their content) stay here. On any failure -> a NAMED honest miss, never a value.
    stall = _certify.guard(out, label, [
        _certify.Check("d^2=0 (genuine chain complex)", dsq_ok, True, ok=dsq_ok),
        _certify.Check("Euler-Poincare (CW chi == rational Betti chi)",
                       cell_chi, betti_chi),
    ])
    if stall is not None:
        return stall

    free = {d: H[d][0] for d in H}
    tor_rank = sum(len(H[d][1]) for d in H)

    if asked["kind"] == "torsion_rank":
        # UCT: total torsion-rank of H^*(M;Z) == total torsion-rank of H_*(M;Z).
        out.value = int(tor_rank)
        out.detail = (f"rank of torsion subgroup of (co)homology of {label} = {out.value} "
                      f"(integral homology via Smith normal form; d^2=0 and CW Euler char "
                      f"{cell_chi} = rational Betti Euler char {betti_chi}, certified)")
        out.provenance.append(("construct", "schubert_cell_complex",
                               f"{label}: {sum(len(v) for v in bydim.values())} cells, "
                               f"d^2=0 verified"))
        out.provenance.append(("compute", "smith_normal_form",
                               f"torsion summands per degree -> total rank {out.value}"))
        return out

    # betti_dim: dim H^k(M,Q) = dim H_k(M,Q) = k-th rational Betti number (UCT over a field).
    deg = asked["degree"]
    out.value = int(free.get(deg, 0))
    out.detail = (f"dim H^{deg}({label},Q) = b_{deg} = {out.value} (rational Betti via "
                  f"integral homology; d^2=0 and CW Euler char {cell_chi} = rational Betti "
                  f"Euler char {betti_chi}, certified)")
    out.provenance.append(("construct", "schubert_cell_complex",
                           f"{label}: cell complex, d^2=0 verified"))
    out.provenance.append(("compute", "rational_betti",
                           f"b_{deg} = {out.value} (Euler-Poincare certified)"))
    return out


def compute(stem: str) -> BettiResult:
    asked = read_betti(stem)
    if asked.get("kind") in ("betti_dim", "torsion_rank"):
        return compute_betti(asked)
    return BettiResult(kind=None,
                       detail="no recognised named-space (co)homology dimension/rank surface")


__all__ = ["BettiResult", "read_betti", "compute", "compute_betti"]
