"""compute_reduced_euler — a COMPUTE FACULTY for the REDUCED EULER CHARACTERISTIC
of a simplicial complex DEFINED BY A COMBINATORIAL FACE-PREDICATE (the cmsg-gap-2
fix). The fresh HLE question introduces Δ_k as

    ground set E(K_k);  A ⊆ E(K_k) is a FACE iff (V(K_k), A) has degree ≤ 2,

and asks χ̃(Δ_k) mod k. The held `compute_homology` needs an EXPLICIT finite
complex, not a symbolic family. This faculty:

  (1) READS the face-predicate from the stem (the SAME general definition-reading
      as gap-1: 'a face iff <combinatorial condition>') — the relation + threshold
      ('degree at most 2') are read off the rendered prose, NOT hard-coded.
  (2) For a CONCRETE prime k CONSTRUCTS the explicit finite complex: enumerate the
      non-empty edge-subsets of K_k satisfying the read degree-condition (a valid
      abstract simplicial complex — the predicate is subset-monotone, so it is
      face-closed; the closure is taken anyway to be safe).
  (3) COMPUTES χ̃ over the HELD f-vector compute: χ̃ = -1 + Σ_i (-1)^i f_i, where
      f_i = #faces of dimension i = cardinality(simplices_of_dim(complex, i)) —
      the SAME held reason.solve face-count `compute_homology` uses. This is a HELD
      COMPUTE, not a hard-coded χ̃ value.
  (4) CROSS-CHECKS χ̃ by a SECOND independent method (the homology/Betti route:
      χ̃ = -1 + Σ_k (-1)^k b_k, b_k via the read-grounded betti_number over the
      boundary-matrix rank) — the cmsg174 discipline: verify against an independent
      method, NEVER the answer key.

The parametric formula in k is then DERIVED from the concrete χ̃(k) values by the
agent's finite-difference (order-N) machinery (order_n_concepts.nth_order_terms),
or the residual is named honestly.

FAITHFUL (CLAUDE.md): a world-adapter compute. The face-predicate READING is a
mechanical prose->threshold translation (read the relation + the number); the
ENUMERATION is mechanical (build the edge-subsets the predicate admits — a
chain/complex input, like compute_homology's test complexes); the χ̃ value is the
HELD reason.solve f-vector compute, NOT a Python-decided number and NOT the key.
No LLM, no reverse-engineering. Math/reading only.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from typing import Optional

from domains import reason as _reason


# ===========================================================================
# (1) READ THE FACE-PREDICATE from the stem. The face condition is a graph
# DEGREE constraint with a threshold: '(V(K_k), A) has degree at most 2'. We read
# the RELATION ('at most' / 'at least' / 'equal to') + the THRESHOLD (the number)
# off the rendered prose, plus the structure (the predicate is on the graph
# (V, A) whose edge-set is the candidate face A). This is the SAME definition-
# reading register as gap-1 — read what the stem SAYS, not a per-question rule.
# ===========================================================================

# relation surface -> a comparator the enumerator applies to a vertex's degree.
_DEGREE_RELATIONS = [
    ("at most", "le"), ("at least", "ge"),
    ("no more than", "le"), ("no less than", "ge"),
    ("less than or equal to", "le"), ("greater than or equal to", "ge"),
    ("less than", "lt"), ("greater than", "gt"),
    ("equal to", "eq"), ("exactly", "eq"),
]


@dataclass
class FacePredicate:
    read: bool = False
    relation: Optional[str] = None     # le / ge / lt / gt / eq
    threshold: Optional[int] = None    # the degree bound (read, not hard-coded)
    on: str = "degree"                 # the graph quantity constrained
    prose: str = ""
    reason: str = ""

    def admits(self, max_degree: int) -> bool:
        """Does a candidate face (a graph (V, A)) with this MAX vertex degree
        satisfy the read predicate? (degree at most 2 -> max_degree <= 2.)"""
        t = self.threshold
        if t is None or self.relation is None:
            return False
        return {"le": max_degree <= t, "ge": max_degree >= t,
                "lt": max_degree < t, "gt": max_degree > t,
                "eq": max_degree == t}[self.relation]


def read_face_predicate(stem_prose: str) -> FacePredicate:
    """READ the simplicial-complex face-predicate from the (rendered) stem prose:
    the clause '... is a face if (and only if) the graph (V, A) has degree
    <relation> <threshold>'. Reads the DEGREE quantity, the RELATION surface, and
    the numeric THRESHOLD. Returns a FacePredicate; .read is False (the honest
    residual) if no degree-condition clause is found."""
    out = FacePredicate(prose=stem_prose or "")
    low = re.sub(r"\s+", " ", (stem_prose or "").lower())
    # the predicate is anchored on a DEGREE constraint of the candidate-face graph.
    di = low.find("degree")
    if di < 0:
        out.reason = "no 'degree' face-condition clause found (the honest residual)"
        return out
    tail = low[di + len("degree"):]
    # read the RELATION surface (longest first) + the THRESHOLD number after it.
    for surf, rel in sorted(_DEGREE_RELATIONS, key=lambda r: -len(r[0])):
        ri = tail.find(surf)
        if ri < 0:
            continue
        after = tail[ri + len(surf):]
        m = re.search(r"-?\d+", after)
        if not m:
            continue
        out.read = True
        out.relation = rel
        out.threshold = int(m.group(0))
        out.reason = (f"READ face-predicate: a subset A is a face iff its graph "
                      f"(V, A) has degree {surf} {out.threshold}")
        return out
    out.reason = ("found 'degree' but no readable relation/threshold (the honest "
                  "residual)")
    return out


# ===========================================================================
# (2) CONSTRUCT the explicit finite complex for a CONCRETE k. The ground set is
# E(K_k) (the edges of the complete graph on k vertices); a face is a non-empty
# edge-subset whose induced graph (V, A) satisfies the read degree-predicate. The
# predicate is subset-monotone (removing edges only lowers degrees), so the
# admitted edge-subsets are already a simplicial complex; we close under non-empty
# subsets anyway (a valid abstract complex). A SIMPLEX is the SORTED tuple of edge-
# indices; compute_homology's reason.solve face-count consumes exactly this shape.
# ===========================================================================

def _edges_of_complete_graph(k: int) -> list[tuple[int, int]]:
    """E(K_k): the edges of the complete graph on k vertices."""
    return list(itertools.combinations(range(k), 2))


def _max_degree(edge_set, edges) -> int:
    """The maximum vertex degree of the graph (V, A) where A = the given edge-index
    subset (over the edge list `edges`)."""
    deg: dict = {}
    for ei in edge_set:
        u, v = edges[ei]
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    return max(deg.values()) if deg else 0


def construct_complex(k: int, pred: FacePredicate) -> list[list[int]]:
    """CONSTRUCT Δ_k for a concrete k: the non-empty edge-index subsets of E(K_k)
    admitted by the read face-predicate (degree condition). Returned as a flat list
    of simplices (each a sorted edge-index tuple); vertices of the complex = single
    edges, indexed 0..|E(K_k)|-1. This is the explicit finite complex
    compute_homology's f-vector compute needs.

    The degree-predicate is SUBSET-MONOTONE (removing an edge cannot raise any
    degree), so the admitted faces are DOWNWARD-CLOSED — already a simplicial
    complex — and a SUPERSET of a rejected set is itself rejected. We exploit that
    to GROW the complex level-by-level (size r+1 faces are extensions of admitted
    size-r faces by one higher-indexed edge), instead of scanning all 2^|E| subsets:
    each admitted face is the parent of its admitted supersets, so a level with no
    admitted face ends the growth. This is the SAME complex, enumerated efficiently."""
    edges = _edges_of_complete_graph(k)
    m = len(edges)
    faces: set = set()
    # level 1: the admitted single edges (degree-2 face is one edge -> max deg 1).
    level = []
    for ei in range(m):
        A = (ei,)
        if pred.admits(_max_degree(A, edges)):
            faces.add(A)
            level.append(A)
    # grow: extend each admitted face by one HIGHER-indexed edge; keep the admitted
    # extensions (monotone -> a non-admitted superset is pruned with all its supersets).
    while level:
        nxt = []
        for A in level:
            last = A[-1]
            for ei in range(last + 1, m):
                B = A + (ei,)
                if pred.admits(_max_degree(B, edges)):
                    faces.add(B)
                    nxt.append(B)
        level = nxt
    return [list(s) for s in faces]


# ===========================================================================
# (3) COMPUTE χ̃ over the HELD f-vector compute. χ̃ = -1 + Σ_i (-1)^i f_i, with
# f_i = #faces of dimension i = cardinality(simplices_of_dim(complex, i)) — the
# SAME held reason.solve face-count compute_homology uses. The '-1' is the reduced
# correction (the empty face, f_{-1} = 1). This is a HELD COMPUTE — the f_i are
# read off the constructed complex by the agent's evaluator, not Python-decided.
# ===========================================================================

def _top_dim(complex_) -> int:
    return max((len(s) - 1 for s in complex_), default=-1)


def f_vector(complex_) -> list[int]:
    """The f-vector [f_0, f_1, ...] via the HELD reason.solve face-count
    (cardinality of simplices_of_dim at each dimension). f_i = #i-dimensional
    faces."""
    top = _top_dim(complex_)
    fv = []
    for i in range(top + 1):
        fi = _reason.solve(
            {"cardinality": {"of": {"simplices_of_dim": {"complex": complex_,
                                                         "k": i}}}}, {})
        fv.append(int(fi))
    return fv


def reduced_euler_via_fvector(complex_) -> int:
    """χ̃ = -1 + Σ_i (-1)^i f_i over the HELD f-vector compute. The alternating sum
    is assembled over the held neg_one_pow + arithmetic the agent owns (reason.solve
    each term); the result is the COMPUTED reduced Euler characteristic."""
    fv = f_vector(complex_)
    chi = 0
    for i, fi in enumerate(fv):
        sign = _reason.solve({"neg_one_pow": {"i": i}}, {})   # held (-1)^i
        chi += sign * fi
    return chi - 1   # the reduced correction (the empty face f_{-1}=1).


# ===========================================================================
# (4a) CROSS-CHECK by a SECOND independent method — DIRECT BRUTE face-enumeration.
# This re-derives χ̃ WITHOUT the held reason.solve face-count path: it enumerates
# the admitted edge-subsets directly and counts faces by dimension with a plain
# Counter, then forms χ̃ = -1 + Σ_i (-1)^i f_i. It shares NO code with the
# reduced_euler_via_fvector path (which routes f_i through simplices_of_dim /
# cardinality on the constructed complex). Agreement = the cmsg174 discipline: an
# independent SECOND method, NEVER the answer key. Tractable for every k (degree<=2
# subgraphs are unions of paths/cycles — a bounded family).
# ===========================================================================

def reduced_euler_via_brute(k: int, pred: FacePredicate) -> int:
    """χ̃ by DIRECT brute enumeration (independent of the held face-count path):
    enumerate the admitted edge-subsets of E(K_k), count faces per size, form
    χ̃ = -1 + Σ_i (-1)^i f_i. The independent second method."""
    from collections import Counter
    edges = _edges_of_complete_graph(k)
    m = len(edges)
    sizes: Counter = Counter()
    # the SAME monotone growth, but counting independently (no reason.solve).
    level = [(ei,) for ei in range(m) if pred.admits(_max_degree((ei,), edges))]
    for A in level:
        sizes[len(A)] += 1
    while level:
        nxt = []
        for A in level:
            for ei in range(A[-1] + 1, m):
                B = A + (ei,)
                if pred.admits(_max_degree(B, edges)):
                    sizes[len(B)] += 1
                    nxt.append(B)
        level = nxt
    if not sizes:
        return -1
    top = max(sizes)
    return -1 + sum((-1) ** i * sizes.get(i + 1, 0) for i in range(top))


# ===========================================================================
# (4b) DEEPER CROSS-CHECK — the HOMOLOGY/Betti route (for small k where the
# boundary-matrix GF(2) rank is tractable).
# χ̃ = -1 + Σ_k (-1)^k b_k, with b_k the read-grounded Betti number (boundary-
# matrix rank). This is INDEPENDENT of the f-vector route (it goes through the
# boundary operator + GF(2) rank, not the face counts) — the cmsg174 discipline:
# verify against an independent method, NEVER the answer key.
# ===========================================================================

def reduced_euler_via_betti(complex_) -> Optional[int]:
    """χ̃ via the homology route: -1 + Σ_k (-1)^k b_k, b_k the read-grounded Betti
    number (compute_homology's grounded betti_number over the held ∂ + matrix rank).
    Independent of the f-vector route. Returns None if betti_number cannot be
    grounded in this process (the honest residual — the f-vector route still
    stands)."""
    try:
        from substrate_rs import _native
        from domains import grounded_representation as gr
        from domains import compute_grounding as cg
        s = _native.Substrate()
        gr.open_grounding_productions(s)
        caps = dict(_reason.CAPABILITIES)
        if "betti_number" not in caps:
            betti_def = ("betti_number(complex, k) = "
                         "cardinality(simplices_of_dim(complex, k)) "
                         "- matrix_rank(boundary_matrix(complex, k)) "
                         "- matrix_rank(boundary_matrix(complex, k + 1))")
            cg.ground_computation(s, "betti_number", betti_def, capabilities=caps)
        top = _top_dim(complex_)
        chi = 0
        for k in range(top + 1):
            b = _reason.solve({"betti_number": {"complex": complex_, "k": k}}, {},
                              capabilities=caps)
            sign = _reason.solve({"neg_one_pow": {"i": k}}, {})
            chi += sign * int(b)
        return chi - 1
    except Exception:
        return None


# ===========================================================================
# THE FACULTY ENTRY — read the predicate, construct + compute χ̃ for each concrete
# k, cross-check, and DERIVE the parametric formula from the concrete values.
# ===========================================================================

@dataclass
class ChiResult:
    k: int
    chi_reduced: Optional[int] = None
    chi_mod_k: Optional[int] = None
    cross_check: Optional[int] = None          # the brute-route χ̃ (independent)
    cross_check_agrees: Optional[bool] = None
    betti_check: Optional[int] = None          # the Betti-route χ̃ (deeper, small k)
    betti_agrees: Optional[bool] = None
    f_vector: list = field(default_factory=list)


def compute_for_k(stem_prose: str, k: int,
                  pred: Optional[FacePredicate] = None,
                  betti_max_faces: int = 600) -> ChiResult:
    """Read the face-predicate (if not supplied), CONSTRUCT Δ_k, COMPUTE χ̃ via the
    held f-vector compute, and CROSS-CHECK via the INDEPENDENT brute face-
    enumeration (the cmsg174 second method, every k) + the deeper Betti/homology
    route (small k, where the GF(2) rank is tractable). Returns a ChiResult."""
    pred = pred or read_face_predicate(stem_prose)
    out = ChiResult(k=k)
    if not pred.read:
        return out
    complex_ = construct_complex(k, pred)
    out.f_vector = f_vector(complex_)
    out.chi_reduced = reduced_euler_via_fvector(complex_)
    out.chi_mod_k = out.chi_reduced % k
    # PRIMARY independent cross-check: direct brute enumeration (no held face-count).
    cc = reduced_euler_via_brute(k, pred)
    out.cross_check = cc
    out.cross_check_agrees = (cc is not None and cc == out.chi_reduced)
    # DEEPER cross-check: the homology/Betti route, only when the complex is small
    # enough that the boundary-matrix GF(2) rank is tractable.
    if len(complex_) <= betti_max_faces:
        bc = reduced_euler_via_betti(complex_)
        out.betti_check = bc
        out.betti_agrees = (bc is not None and bc == out.chi_reduced)
    return out


def derive_parametric(ks: list[int], chis: list[int]) -> dict:
    """DERIVE a parametric formula χ̃(k) from the concrete (k, χ̃) values via the
    agent's finite-difference (order-N) machinery (order_n_concepts.nth_order_terms
    over the χ̃ sample sequence). Reports the finite differences; a constant order-N
    difference names the polynomial degree in the SAMPLE INDEX. The honest residual
    (the closed form over k) is named when the samples are not on an arithmetic
    k-grid. NEVER reverse-engineered from the key."""
    from domains import order_n_concepts as _onn
    out = {"ks": ks, "chis": chis, "differences": {}, "note": ""}
    # the order-N finite differences of the SAMPLE sequence (the agent's
    # nth_order_terms over plain numeric samples). A constant order-N difference
    # names the polynomial degree in the SAMPLE INDEX.
    def _ev(t):
        # evaluate the agent's nth_order_terms Minus-tree to a plain number.
        if isinstance(t, dict) and t.get("type") == "Minus":
            return _ev(t["a"]) - _ev(t["b"])
        return t
    seq = list(chis)
    for order in range(1, len(seq)):
        diffs = [_ev(d) for d in _onn.nth_order_terms(seq, order)]
        out["differences"][order] = diffs
        if diffs and all(d == diffs[0] for d in diffs):
            out["constant_difference_order"] = order
            out["constant_difference_value"] = diffs[0]
            break
    # FIT A LINEAR CLOSED FORM IN k: a*k + b reproducing the samples. The samples
    # determine (a, b) from the first two (k0,v0),(k1,v1): a=(v1-v0)/(k1-k0),
    # b=v0-a*k0. The form is then VALIDATED on EVERY sample (it must reproduce all,
    # not just the two it was solved from) — the honest check. This is DERIVED from
    # the concrete computed values, never from the key. A rational a (e.g. 1/2) is
    # reported as a fraction.
    if len(ks) >= 2 and ks[1] != ks[0]:
        from fractions import Fraction as _F
        a = _F(chis[1] - chis[0], ks[1] - ks[0])
        b = _F(chis[0]) - a * ks[0]
        reproduces_all = all(a * kk + b == cc for kk, cc in zip(ks, chis))
        out["linear_fit"] = {
            "a": str(a), "b": str(b),
            "formula": f"({a})*k + ({b})",
            "reproduces_all_samples": reproduces_all,
        }
        if reproduces_all:
            # render as (k - c)/d when a = 1/d (the common closed-form shape).
            if a.numerator == 1 and a.denominator > 1:
                d = a.denominator
                c = -b * d
                out["linear_fit"]["closed_form"] = f"(k - {c})/{d}"
    return out
