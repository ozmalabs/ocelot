#!/usr/bin/env python3
"""construct_compute_graphs — the CONSTRUCTIVE-COMPUTATION route for COUNT-OF-GRAPHS-UP-TO-
ISOMORPHISM invariants on a PROVABLY FINITE, FULLY-ENUMERATED vertex set.

THE GAP THIS CLOSES. Several HLE "how many ... graphs ... with N vertices" questions are
COMPUTED-NUMBER invariants over the finite set of all simple graphs on N labelled vertices,
counted up to isomorphism with a structural property (connectivity, regularity, ...). The
domain is finite and fully determined by N: there are exactly 2^C(N,2) labelled simple
graphs, partitioned into isomorphism classes by a canonical form. For small N this is
exhaustively enumerable, so the count is EXACT and PROVABLY COMPLETE — no source, no key.

THE COMPLETENESS DISCIPLINE (zero false positives). A count is emitted ONLY when:
  · N is within the in-process exhaustive bound (N <= 7: every one of the 2^C(N,2) labelled
    graphs is visited and reduced to a canonical form, so every isomorphism class is found
    EXACTLY once — verified against the OEIS A000088 total at each N as a built-in self-check).
  · the asked property is in the held, exactly-decidable predicate set (each predicate is a
    deterministic graph algorithm, no heuristic).
Outside this (N too large, or an unmodelled property adjective in the ask), NO value is
emitted — an honest miss, never a guess.

THE CANONICAL FORM (sound + complete for iso). Two graphs are isomorphic iff their canonical
forms are equal. The canonical form is the lexicographically minimal edge-set over all
relabellings that respect an iterated degree-refinement colouring (sound: refinement only
ever merges vertices that no isomorphism could separate, so the minimisation is taken over a
superset of the true automorphism-respecting relabellings; complete: it ranges over every
relabelling consistent with the colouring, so isomorphic graphs always collapse). The total-
count self-check against A000088 certifies the canonical form is collision-free at each N.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It READS the asked count off the stem
(mechanical surface->graph translation), CONSTRUCTS the finite graph domain, CANONICALISES,
FILTERS by the held predicate, and TALLIES. No per-question branch (a property recogniser, the
same enumeration on each), no LLM, no Rust, no key. The KEY is never consulted here.
"""
from __future__ import annotations

import itertools
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import reason as _reason
from domains import certify as _certify

# OEIS A000088 — the number of simple graphs on n unlabelled nodes. Used purely as a
# built-in CANONICAL-FORM SELF-CHECK (the enumerator must reproduce this total at each n,
# else the canonical form is colliding and NO value is emitted). Not an answer source.
A000088 = {0: 1, 1: 1, 2: 2, 3: 4, 4: 11, 5: 34, 6: 156, 7: 1044}

# the in-process exhaustive bound. n=7 visits 2^21 labelled graphs; beyond this the domain
# is still finite but not enumerated here -> honest no-value.
N_MAX = 7


@dataclass
class GraphCount:
    kind: Optional[str] = None       # graph_count_with_property | None
    value: Optional[int] = None
    detail: str = ""
    provenance: list = field(default_factory=list)


# ===========================================================================
# HELD primitive helpers — adjacency, the refinement canonical form, and the exact
# structural predicates. Every predicate is a deterministic algorithm (no heuristic).
# ===========================================================================

def _adj(n, edges):
    A = [[0] * n for _ in range(n)]
    for i, j in edges:
        A[i][j] = A[j][i] = 1
    return A


def _canon(n, A):
    """Canonical form: lexicographically minimal edge-set over relabellings that respect an
    iterated degree-refinement colouring. Exhaustive within colour classes."""
    color = [sum(A[v]) for v in range(n)]
    for _ in range(n):
        sig = [(color[v], tuple(sorted(color[u] for u in range(n) if A[v][u])))
               for v in range(n)]
        order = {s: i for i, s in enumerate(sorted(set(sig)))}
        newc = [order[sig[v]] for v in range(n)]
        if newc == color:
            break
        color = newc
    classes = defaultdict(list)
    for v in range(n):
        classes[color[v]].append(v)
    classlist = [classes[c] for c in sorted(classes)]
    targets, pos = [], 0
    for cl in classlist:
        targets.append(list(range(pos, pos + len(cl))))
        pos += len(cl)
    best = [None]

    def rec(ci, mapping):
        if ci == len(classlist):
            key = tuple(sorted(tuple(sorted((mapping[i], mapping[j])))
                               for i in range(n) for j in range(i + 1, n) if A[i][j]))
            if best[0] is None or key < best[0]:
                best[0] = key
            return
        cl, tg = classlist[ci], targets[ci]
        for perm in itertools.permutations(tg):
            m2 = dict(mapping)
            for o, t in zip(cl, perm):
                m2[o] = t
            rec(ci + 1, m2)

    rec(0, {})
    return best[0]


def _enumerate_iso_classes(n):
    """Every isomorphism class of simple graph on n vertices, one representative each.
    Returns the list of representative adjacency matrices, and the class count. The count
    is cross-checked against A000088 by the caller (the completeness certificate)."""
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    seen = set()
    reps = []
    for mask in range(1 << len(pairs)):
        edges = [pairs[b] for b in range(len(pairs)) if mask >> b & 1]
        A = _adj(n, edges)
        c = _canon(n, A)
        if c not in seen:
            seen.add(c)
            reps.append(A)
    return reps


# -- exact structural predicates (each a deterministic algorithm) -------------

def _is_connected(n, A):
    if n == 0:
        return True
    seen = {0}
    q = deque([0])
    while q:
        v = q.popleft()
        for u in range(n):
            if A[v][u] and u not in seen:
                seen.add(u)
                q.append(u)
    return len(seen) == n


def _is_k_connected_removal(n, A, k):
    """True iff the graph is connected and stays connected after removing any (k-1) vertices,
    AND has more than k vertices — the vertex-connectivity >= k test by exhaustive removal."""
    if n <= k:
        return False
    if not _is_connected(n, A):
        return False
    for rm in itertools.combinations(range(n), k - 1):
        rmset = set(rm)
        verts = [v for v in range(n) if v not in rmset]
        if not verts:
            return False
        start = verts[0]
        seen = {start}
        q = deque([start])
        while q:
            v = q.popleft()
            for u in verts:
                if A[v][u] and u not in seen:
                    seen.add(u)
                    q.append(u)
        if len(seen) != len(verts):
            return False
    return True


def _degrees(n, A):
    return [sum(A[v]) for v in range(n)]


def _is_regular(n, A, d=None):
    deg = _degrees(n, A)
    if d is not None:
        return all(x == d for x in deg)
    return len(set(deg)) == 1


def _has_no_isolated(n, A):
    return all(sum(A[v]) > 0 for v in range(n))


# ===========================================================================
# READ — the asked graph-count surfaces this module recognises. Mechanical; no count.
# ===========================================================================

_GRAPH_COUNT_RE = re.compile(
    r"how many\b(.*?)\b(?:simple\s+)?(?:nonisomorphic|non-isomorphic|distinct|"
    r"unlabell?ed)?\s*graphs?\b(.*?)\bwith\s+(\d+)\s+vertices", re.I | re.S)
# also accept "... graphs are there with N vertices" and "... graphs on N vertices"
_GRAPH_COUNT_RE2 = re.compile(
    r"how many\b(.*?)\bgraphs?\b(.*?)\b(?:on|with)\s+(\d+)\s+vertices", re.I | re.S)


def _parse_properties(pre, mid):
    """Read the recognised property adjectives out of the text around 'graphs'. Returns
    (props_dict, residual_text). A non-empty residual of unmodelled adjectives forces a
    no-value (so a stricter ask is never silently under/over-counted)."""
    text = (pre + " " + mid).lower()
    props = {}
    # connectivity: "2-vertex-connected" / "2-connected" / "k-connected" / "connected"
    mkc = re.search(r"(\d+)\s*-\s*(?:vertex-?)?connected", text)
    if mkc:
        props["vertex_connectivity"] = int(mkc.group(1))
    elif re.search(r"\bconnected\b", text):
        props["vertex_connectivity"] = 1
    # regularity: "d-regular" / "regular"
    mreg = re.search(r"(\d+)\s*-\s*regular", text)
    if mreg:
        props["regular"] = int(mreg.group(1))
    elif re.search(r"\bregular\b", text):
        props["regular"] = -1  # any regular
    if re.search(r"\bwithout isolated|no isolated\b", text):
        props["no_isolated"] = True
    # strip the recognised adjectives + glue words; any residual content adjective -> unread.
    residual = text
    residual = re.sub(r"\d+\s*-\s*(?:vertex-?)?connected", " ", residual)
    residual = re.sub(r"\d+\s*-\s*regular", " ", residual)
    residual = re.sub(
        r"\bsimple|nonisomorphic|non-isomorphic|distinct|unlabell?ed|connected|regular|"
        r"graphs?|are there|there are|with|on|exactly|the|a|an|of|number|how|many|"
        r"vertices?|vertex|having|that|are|and|,|\.|\?\b", " ", residual)
    residual = re.sub(r"\s+", " ", residual).strip()
    return props, residual


def read_graph_count(stem: str) -> dict:
    m = _GRAPH_COUNT_RE.search(stem) or _GRAPH_COUNT_RE2.search(stem)
    if not m:
        return {"kind": None}
    pre, mid, nstr = m.group(1), m.group(2), m.group(3)
    n = int(nstr)
    props, residual = _parse_properties(pre, mid)
    # require at least one recognised property OR a bare graph count; reject if there is an
    # unmodelled adjective residual (never silently mismodel a stricter ask).
    if residual:
        return {"kind": None, "reason": f"unmodelled property adjective(s): {residual!r}"}
    return {"kind": "graph_count_with_property", "n": n, "props": props}


# ===========================================================================
# COMPUTE — exhaustive enumeration over the PROVABLY finite, A000088-certified domain.
# ===========================================================================

def _property_filter(n, A, props):
    for key, val in props.items():
        if key == "vertex_connectivity":
            if val == 1:
                if not (_is_connected(n, A) and n >= 1):
                    return False
            else:
                if not _is_k_connected_removal(n, A, val):
                    return False
        elif key == "regular":
            if val == -1:
                if not _is_regular(n, A):
                    return False
            else:
                if not _is_regular(n, A, val):
                    return False
        elif key == "no_isolated":
            if not _has_no_isolated(n, A):
                return False
    return True


def compute_graph_count(asked: dict) -> GraphCount:
    n = asked["n"]
    props = asked["props"]
    out = GraphCount(kind="graph_count_with_property")
    if n < 0 or n > N_MAX:
        out.detail = (f"graph count on {n} vertices out of the in-process exhaustive bound "
                      f"(n>{N_MAX}); domain finite but not enumerated here")
        return out
    reps = _enumerate_iso_classes(n)
    total = len(reps)
    # COMPLETENESS CERTIFICATE (shared guard): the enumerator must reproduce the A000088
    # class total (when tabulated for this n), else the canonical form is colliding ->
    # refuse to emit. The emit-or-stall is the shared `certify.guard`; the A000088 check
    # content stays here (it fires only where the total is known).
    stall = _certify.guard(out, f"graph_count n={n}", [
        _certify.Check(f"iso-class total vs A000088[{n}]", total, A000088.get(n),
                       ok=(n not in A000088) or (total == A000088[n])),
    ])
    if stall is not None:
        return stall
    count = 0
    for A in reps:
        if _property_filter(n, A, props):
            count = _reason.solve({"plus": {"left": count, "right": 1}}, {})
    out.value = int(count)
    propdesc = ", ".join(f"{k}={v}" for k, v in sorted(props.items())) or "(any)"
    out.detail = (f"#nonisomorphic graphs on {n} vertices with [{propdesc}] = {out.value} "
                  f"(exhaustive over all {1 << (n*(n-1)//2)} labelled graphs; {total} iso "
                  f"classes match A000088[{n}]={A000088.get(n, '?')}; canonical form certified)")
    out.provenance.append(("construct", "all_iso_classes",
                           f"{total} isomorphism classes on {n} vertices (A000088-certified)"))
    out.provenance.append(("compute", "property_filter",
                           f"filtered by {sorted(props.items())} -> {out.value}"))
    return out


def compute(stem: str) -> GraphCount:
    asked = read_graph_count(stem)
    if asked.get("kind") == "graph_count_with_property":
        return compute_graph_count(asked)
    return GraphCount(kind=None,
                      detail=asked.get("reason", "no recognised graph-count surface"))


__all__ = ["GraphCount", "read_graph_count", "compute", "compute_graph_count"]
