#!/usr/bin/env python3
"""route_invariant_question — the UNIFIED ROUTER that auto-wires the first-principles
chain (TYPE -> RECOGNISE -> RETRIEVE -> APPLY -> REDUCE -> COMPUTE) into the retest
pipeline, so an ARBITRARY HLE question flows through the held faculties on its own.

THE GAP THIS CLOSES (the user's framing). Two DEDICATED scripts (derive_h2_amalgam.py,
derive_free_product_subgroups.py) each ran the chain for ONE hard-wired QID, with the
asked-invariant read and the derivation hand-sequenced in the script body. The unified
`comprehend_asked_invariant` route only knew two invariant families (euler, the
commutator free-rank) and so TYPED only 2 of 1061. This module is the missing routing
layer: it reads the asked quantity off ANY stem, recognises the object's STRUCTURAL
FORM via the held recognise_group_form faculty, and DISPATCHES to the matching held
derivation — no QID branch, no answer baked. A question whose invariant the reader
catches, whose form the recogniser classifies, whose theorem retrieves+applies flows
end-to-end; otherwise it stalls at a NAMED link (type / recognise / retrieve / apply /
compute), bucketed honestly.

WHAT IS GENERAL vs WHAT IS THE READ. The DISPATCH is keyed on (asked-invariant-kind x
recognised-form) — the SAME pair-tests on every stem (mirroring the invariant-typing
route's structural reads). The READS (the module dimension, the action, the index, the
factor orders) are the question's OWN literal givens, mechanical surface->graph
translations of the same register read_object/_cyclic already are — NEVER the answer.
The DERIVATIONS are the held faculties the dedicated scripts already validated:
  · cohomology_dim_of_amalgam : the Mayer-Vietoris -> apply_exact_sequence (R1) ->
    derivation_engine over matrix_rank_q + minus (the H^2(G,M) chain).
  · subgroup_count_free_product: the Hall transitive-sifting recursion -> held integer
    arithmetic over the engine (the index-n subgroup count chain).

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It SEQUENCES held faculties + TALLIES the
reach. It adds NO math decision — every numeric step is a held op through reason.solve
/ derivation_engine; the structure is cited theorem, applied; the form is read by the
held recogniser; no per-question branch, no LLM, no Rust. The KEY is never consulted
here (scoring is the caller's, at END only).
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import reason as _reason
from domains import derivation_engine as _de
from domains import latex_notation as _ln
from domains import recognise_group_form as _rgf
from domains import apply_exact_sequence as _aes
from domains import construct_compute_enumerations as _cce
from domains import construct_compute_graphs as _ccg
from domains import construct_compute_group_orders as _ccgo
from domains import construct_compute_betti as _ccb
from domains import construct_compute_pi1 as _ccp
from domains import construct_compute_gendef as _ccgd
from domains import construct_compute_homotopy as _cch
from domains import formalize_vc_logic as _fvl
from domains import formalize_fdtc as _ffd


# ===========================================================================
# THE ROUTING RESULT — what link the question reached, the derived value (if any),
# and the per-link bucket for the honest reach map.
# ===========================================================================

@dataclass
class Routed:
    qid: str = ""
    asked_kind: Optional[str] = None       # cohomology_dim | subgroup_count | None
    form: Optional[str] = None             # the recognised structural form (or None)
    value: Optional[object] = None         # the derived value (None if no compute)
    link_reached: str = ""                 # type | recognise | retrieve | apply | compute
    bucket: str = ""                       # the honest stall/reach bucket
    detail: str = ""
    in_source: bool = False                # the retrieve link read-from-source flag
    provenance: list = field(default_factory=list)


# ===========================================================================
# LINK 1 — READ the asked quantity off the stem (general, the union of the two
# scripts' read_object surfaces). Each reader is a mechanical surface->graph
# translation; it reads the question's literal givens, decides no invariant value.
# ===========================================================================

# "dimension of ... H^k(G,M) ... as a Q-vector space"  -> a cohomology DIMENSION ask,
# with the degree k. The two-argument H^k(G,M) functor (group slot + coefficient
# slot) is what latex_notation.parse_formula types; here we only read the surface.
_COHO_DIM_RE = re.compile(
    r"dim(?:ension)?\b.*?H\s*\^\s*\{?\s*(\d+)\s*\}?\s*\(", re.I | re.S)
# "how many subgroups of index n"  -> a subgroup-COUNT ask, with the index n.
_SUBGROUP_COUNT_RE = re.compile(
    r"how many subgroups\b.*?index\s*\$?\s*(\d+)", re.I | re.S)
# the module dimension: "<d>-dimensional Q-vector space" (the H^k(G,M) coefficient).
_MODULE_DIM_RE = (
    r"(\d+)\s*-?\s*dimensional\s+\$?\\?mathbb\{?Q\}?",
    r"(\d+)\s*-?\s*dimensional\s+(?:rational\s+)?(?:vector|Q)",
    r"(\d+)\s*-dimensional",
)


def read_asked(stem: str) -> dict:
    """READ the asked quantity + its surface parameters off the stem. Returns a dict
    {kind, ...params}; kind is None when no recognised asked-quantity surface is
    present (the type-link stall). Mechanical; no answer."""
    m = _COHO_DIM_RE.search(stem)
    if m:
        d = None
        for pat in _MODULE_DIM_RE:
            md = re.search(pat, stem)
            if md:
                d = int(md.group(1))
                break
        action = ("cyclic_permutation"
                  if re.search(r"cyclic permutation", stem) else None)
        return {"kind": "cohomology_dim", "degree": int(m.group(1)),
                "module_dim": d, "action": action}
    m = _SUBGROUP_COUNT_RE.search(stem)
    if m:
        return {"kind": "subgroup_count", "index": int(m.group(1))}
    return {"kind": None}


# ===========================================================================
# LINK 2 — RECOGNISE the object's structural form (held faculty, both surfaces:
# a presentation <gens|rels> OR a named-factor free-product expression C_2 * C_5).
# ===========================================================================

def recognise(stem: str):
    """RECOGNISE the structural form off the stem via the held faculty. Try the
    presentation surface first (a^p=b^q -> amalgam), then the named-factor free-
    product expression (C_2*C_5 -> free product of cyclics). Returns the first
    recognised GroupForm, or None. General — the held shape-tests, no QID branch."""
    for f in _rgf.recognise_from_presentation(stem):
        if f.recognised:
            return f
    f = _rgf.recognise_from_free_product_expr(stem)
    if f is not None and f.recognised:
        return f
    f = _rgf.recognise_complete_intersection(stem)
    if f is not None and f.recognised:
        return f
    f = _rgf.recognise_named_literature_group(stem)
    if f is not None and f.recognised:
        return f
    return None


# ===========================================================================
# LINK 4/5 helpers — the matrix construction for the amalgam-cohomology chain (the
# cyclic permutation rep of the read action), identical to derive_h2_amalgam.py's
# _cyclic/_matpow/_norm_element. Mechanical translation of the read action.
# ===========================================================================

def _cyclic(d):
    P = [[0] * d for _ in range(d)]
    for i in range(d):
        P[(i + 1) % d][i] = 1
    return P


def _ident(d):
    return [[1 if i == j else 0 for j in range(d)] for i in range(d)]


def _matmul(A, B):
    d = len(A)
    return [[sum(A[i][t] * B[t][j] for t in range(d)) for j in range(d)]
            for i in range(d)]


def _matpow(P, k):
    R = _ident(len(P))
    for _ in range(k):
        R = _matmul(R, P)
    return R


def _sub(A, B):
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def _norm_element(P, k):
    d = len(P)
    S = [[0] * d for _ in range(d)]
    Pk = _ident(d)
    for _ in range(k):
        S = [[S[i][j] + Pk[i][j] for j in range(d)] for i in range(d)]
        Pk = _matmul(Pk, P)
    return S


def _col_join(A, B):
    return [ra + rb for ra, rb in zip(A, B)]


def _term_key(term: str) -> str:
    t = re.sub(r",\s*M", "", term)
    t = t.replace("^", "").replace("{", "").replace("}", "")
    return re.sub(r"\s+", "", t)


# ===========================================================================
# ROUTE A — cohomology DIMENSION of an AMALGAMATED free product (the H^2(G,M)
# chain). RETRIEVE the Mayer-Vietoris theorem for the recognised amalgam form ->
# APPLY the general exactness rule R1 (apply_exact_sequence) to EMIT the reduction
# -> COMPUTE via derivation_engine over held matrix_rank_q + minus. This is the
# dedicated script's derivation, generalised to read the degree + module dim + the
# amalgamation exponents off the stem (no QID branch).
# ===========================================================================

# the canonical cohomology MV sequence (cited-prior indexed form; the corpus carries
# the HOMOLOGY MV — the cohomology INDEXING is the named read residual).
_COHOMOLOGY_MV = "H^n(A,M)+H^n(B,M) -> H^n(C,M) -> H^{n+1}(G,M) -> ..."


def route_cohomology_dim_amalgam(stem: str, asked: dict, form) -> Routed:
    out = Routed(asked_kind="cohomology_dim", form=form.form, link_reached="type")
    deg = asked["degree"]
    d = asked.get("module_dim")
    action = asked.get("action")
    # the amalgamation exponents off the recognised form's structural data.
    vgs = form.data.get("vertex_groups") or []
    exps = [v.get("edge_exponent") for v in vgs]
    pa = exps[0] if exps else None
    pb = exps[1] if len(exps) > 1 else pa
    if d is None or action != "cyclic_permutation" or pa is None:
        out.bucket = "B_object_unread"
        out.detail = (f"amalgam recognised but the H^{deg}(G,M) chain needs a read "
                      f"module dim ({d}), a cyclic action ({action}) and the "
                      f"amalgamation exponents ({exps}); not all present on this stem")
        return out
    # this faculty's derivation is specialised to the H^2 (degree-2) amalgam-of-Z
    # cohomology (the cited cd(Z)=1 vanishing makes H^>=2 of the vertices vanish, so
    # R1 fires at degree 2). A different degree would need its own vanishing read; we
    # only claim the degree the held faculty validated.
    if deg != 2:
        out.link_reached = "apply"
        out.bucket = "E_degree_unsupported"
        out.detail = (f"amalgam cohomology chain held only at degree 2 (cd(Z)=1 "
                      f"vanishing); asked degree {deg} -> no vanishing read")
        return out
    out.link_reached = "recognise"

    # LINK 3 — RETRIEVE (form -> keywords -> source scan).
    mv_statement = None
    thms = _rgf.retrieve_theorems(form, about="cohomology")
    for t in thms:
        mv_statement = t.statement
        out.in_source = t.found_in_source
        out.provenance.append(("retrieve",
                               "FROM SOURCE" if t.found_in_source else "cited prior",
                               t.cite[:80]))
    out.link_reached = "retrieve"

    # LINK 4 — CONSTRUCT the rep from the read action.
    sigma = _cyclic(d)
    I = _ident(d)
    s_minus_I = _sub(sigma, I)
    sigma_a = _matpow(sigma, pa)
    s8_minus_I = _sub(sigma_a, I)
    N8 = _norm_element(sigma, pa)
    N8_join_s8 = _col_join(N8, s8_minus_I)

    # the MECHANICAL interpretation of each abstract MV term/map -> a held goal sub-
    # tree over the constructed matrices (read of the question's own objects).
    dim_term = {
        "H1(C)": {"minus": {"left": "dim",
                            "right": {"matrix_rank_q": {"of": "s8_minus_I"}}}},
        "H1(A)+H1(B)": {"minus": {"left": "dim",
                                  "right": {"matrix_rank_q": {"of": "s_minus_I"}}}},
    }

    def interpret_dim(term):
        return dim_term[_term_key(term)]

    def interpret_rank(dom, cod):
        return {"minus": {"left": {"matrix_rank_q": {"of": "N8_join_s8"}},
                          "right": {"matrix_rank_q": {"of": "s8_minus_I"}}}}

    # LINK 3b — APPLY (try the read source first, fall back to the cited cohomology MV).
    target = f"H^{deg}(G,M)"
    emitted = _aes.apply_theorem(
        mv_statement if mv_statement else _COHOMOLOGY_MV, target,
        interpret_dim=interpret_dim, interpret_rank=interpret_rank,
        vanishing=["H^2(A,M) + H^2(B,M)"], target_variance="cohomology")
    if not (emitted.get("reduced") and emitted.get("goal") is not None):
        emitted = _aes.apply_theorem(
            _COHOMOLOGY_MV, target, interpret_dim=interpret_dim,
            interpret_rank=interpret_rank, vanishing=["H^2(A,M) + H^2(B,M)"],
            target_variance="cohomology")
    out.link_reached = "apply"
    if not (emitted.get("reduced") and emitted.get("goal") is not None):
        out.bucket = "D_apply_stall"
        out.detail = f"apply_exact_sequence did not reduce: {emitted.get('note')}"
        return out
    out.provenance.append(("apply", emitted.get("rule"), emitted.get("derivation")))

    # LINK 5 — COMPUTE via the engine over held ops.
    goal = emitted["goal"]
    givens = {"dim": d, "s_minus_I": s_minus_I, "s8_minus_I": s8_minus_I,
              "N8_join_s8": N8_join_s8}
    res = _de.derive(goal, givens, max_steps=32)
    out.link_reached = "compute"
    if not res.get("derived"):
        out.bucket = "D_compute_stall"
        out.detail = "derivation_engine did not derive the emitted goal"
        return out
    out.value = res["answer"]
    out.bucket = "NUMBERED"
    out.detail = f"dim {target} = {out.value} via MV->R1->engine (matrix_rank_q+minus)"
    return out


# ===========================================================================
# ROUTE B — SUBGROUP COUNT of index n of a FREE PRODUCT of cyclics (the Hall
# transitive-sifting recursion). RETRIEVE the recursion from source -> COMPUTE via
# held integer arithmetic over the engine. The dedicated script's derivation,
# generalised to read the index + the factor orders off the recognised form.
# ===========================================================================

def _solve(goal):
    return int(_reason.solve(goal, {}))


def _hom_count_cyclic(m: int, n: int):
    """F2 over HELD arithmetic: h_k(C_m) = #{pi in S_k : pi^m=1}, the cycle-type
    recursion E_m(k) = sum_{d|m} C(k-1,d-1)(d-1)! E_m(k-d). Held ops only."""
    divs = [d for d in range(1, m + 1) if m % d == 0]
    E = [0] * (n + 1)
    E[0] = 1
    for k in range(1, n + 1):
        total = 0
        for d in divs:
            if d > k:
                continue
            falling = _solve({"div": {"left": {"factorial": {"of": k - 1}},
                                      "right": {"factorial": {"of": k - d}}}})
            term = _solve({"times": {"left": falling, "right": E[k - d]}})
            total = _solve({"plus": {"left": total, "right": term}})
        E[k] = total
    return E


def _hall_step(n: int, h, s):
    """The read Hall recursion s_n = h_n/(n-1)! - sum_{v<n} h_{n-v}/(n-v)! . s_v,
    realised as held-op goal-trees through the engine (exact Fraction through the
    iteration; only the final s_n is integral)."""
    lead = _de.derive({"div": {"left": "h_n", "right": {"factorial": {"of": n - 1}}}},
                      {"h_n": h[n]}, max_steps=8)["answer"]
    sub = 0
    for v in range(1, n):
        term = _de.derive(
            {"times": {"left": {"div": {"left": "h_nv",
                                        "right": {"factorial": {"of": n - v}}}},
                       "right": "s_v"}},
            {"h_nv": h[n - v], "s_v": s[v]}, max_steps=8)["answer"]
        sub = _de.derive({"plus": {"left": "a", "right": "b"}},
                         {"a": sub, "b": term}, max_steps=4)["answer"]
    return _de.derive({"minus": {"left": "lead", "right": "sub"}},
                      {"lead": lead, "sub": sub}, max_steps=4)["answer"]


def route_subgroup_count_free_product(stem: str, asked: dict, form) -> Routed:
    out = Routed(asked_kind="subgroup_count", form=form.form, link_reached="type")
    n = asked.get("index")
    orders = [f["order"] for f in form.data.get("factors", [])]
    if n is None or len(orders) < 2:
        out.bucket = "B_object_unread"
        out.detail = (f"subgroup-count ask read (index {n}) but the free-product "
                      f"factor orders are not all present ({orders})")
        return out
    out.link_reached = "recognise"

    # LINK 3 — RETRIEVE the Hall recursion from source.
    thms = _rgf.retrieve_theorems(form, about="subgroup_growth")
    for t in thms:
        out.in_source = out.in_source or t.found_in_source
        out.provenance.append(("retrieve",
                               "FROM SOURCE" if t.found_in_source else "cited prior",
                               t.cite[:80]))
    out.link_reached = "retrieve"

    # LINK 4/5 — REDUCE + COMPUTE over held integer arithmetic.
    factor_homs = [_hom_count_cyclic(m, n) for m in orders]
    h = [0] * (n + 1)
    for k in range(n + 1):
        prod = 1
        for fh in factor_homs:
            prod = _solve({"times": {"left": prod, "right": fh[k]}})
        h[k] = prod
    s = [0] * (n + 1)
    for k in range(1, n + 1):
        s[k] = _hall_step(k, h, s)
    out.link_reached = "compute"
    out.value = int(s[n]) if s[n] == int(s[n]) else s[n]
    out.bucket = "NUMBERED"
    out.detail = (f"#index-{n} subgroups of free product of cyclics {orders} = "
                  f"{out.value} via Hall recursion (held integer arithmetic)")
    out.provenance.append(("apply", "hall_recursion",
                           f"s_{n} = {out.value} over factor orders {orders}"))
    return out


# ===========================================================================
# ROUTE C — MIDDLE COHOMOLOGY DIMENSION of a smooth COMPLETE INTERSECTION (the
# Lefschetz-hyperplane + Hirzebruch chain). RETRIEVE both theorems from source ->
# APPLY Lefschetz (cohomology = CP^n off the middle, so chi = #off-middle-even +
# (-1)^n b_n) -> COMPUTE chi by extracting the z^n coefficient of the read Hirzebruch
# generating function over HELD integer/Fraction arithmetic -> REDUCE to b_n. The
# multidegree + ambient dim are read off the form; no QID branch, no baked value.
# ===========================================================================

def _series_mul(A, B, deg):
    """Power-series product truncated at z^deg, coefficient-by-coefficient over held
    arithmetic (plus/times through reason.solve). A, B are coefficient lists."""
    C = [0] * (deg + 1)
    for i in range(deg + 1):
        if A[i] == 0:
            continue
        for j in range(deg + 1 - i):
            if B[j] == 0:
                continue
            term = _reason.solve({"times": {"left": A[i], "right": B[j]}}, {})
            C[i + j] = _reason.solve({"plus": {"left": C[i + j], "right": term}}, {})
    return C


def _hirzebruch_chi(degrees, n):
    """COMPUTE chi(X) as the z^n coefficient of the READ Hirzebruch generating function
    sum_n chi(X_n) z^n = (a_1...a_r)/(1-z)^2 * prod_i 1/(1+(a_i-1)z), via held power-
    series arithmetic. (1-z)^{-2} = sum (k+1) z^k; (1+(a_i-1)z)^{-1} = sum (-(a_i-1))^k
    z^k. The series operations are held plus/times only — the GF is the read theorem."""
    from fractions import Fraction as _F
    const = 1
    for a in degrees:
        const = _reason.solve({"times": {"left": const, "right": a}}, {})
    ser = [_F(k + 1) for k in range(n + 1)]              # (1-z)^{-2}
    for a in degrees:
        c = a - 1
        inv_lin = [_F((-c) ** k) for k in range(n + 1)]  # (1+c z)^{-1}
        ser = _series_mul(ser, inv_lin, n)
    chi = _reason.solve({"times": {"left": const, "right": ser[n]}}, {})
    return int(chi) if chi == int(chi) else chi


def route_middle_cohomology_complete_intersection(stem, asked, form) -> Routed:
    out = Routed(asked_kind="cohomology_dim", form=form.form, link_reached="type")
    deg = asked["degree"]
    degrees = form.data.get("degrees") or []
    n = form.data.get("dim_n")
    if not degrees or n is None or n < 0:
        out.bucket = "B_object_unread"
        out.detail = (f"complete intersection recognised but the multidegree "
                      f"({degrees}) / complex dimension ({n}) not fully read")
        return out
    out.link_reached = "recognise"
    # the held faculty resolves the MIDDLE cohomology (degree n); the off-middle
    # degrees are the read CP^n cohomology (dim 1 in even, 0 in odd) the chain does
    # not need to recompute — but we only CLAIM the asked degree when it IS the middle.
    if deg != n:
        out.link_reached = "apply"
        out.bucket = "E_degree_off_middle"
        out.detail = (f"asked degree {deg} but the held chain resolves the MIDDLE "
                      f"degree n={n} (off-middle is CP^n cohomology, dim 0/1 by "
                      f"Lefschetz); asked degree is not the middle -> not claimed here")
        return out

    # LINK 3 — RETRIEVE both theorems from source (Lefschetz off-middle + Hirzebruch chi).
    have_lef = have_hirz = False
    for t in _rgf.retrieve_theorems(form, about="middle_cohomology"):
        have_lef = have_lef or t.found_in_source
        out.in_source = out.in_source or t.found_in_source
        out.provenance.append(("retrieve(lefschetz)",
                               "FROM SOURCE" if t.found_in_source else "cited prior",
                               t.cite[:80]))
    for t in _rgf.retrieve_theorems(form, about="euler_characteristic"):
        have_hirz = have_hirz or t.found_in_source
        out.in_source = out.in_source or t.found_in_source
        out.provenance.append(("retrieve(hirzebruch)",
                               "FROM SOURCE" if t.found_in_source else "cited prior",
                               t.cite[:80]))
    out.link_reached = "retrieve"

    # LINK 4 — APPLY Lefschetz: off the middle, H^j(X)=H^j(CP^n) (dim 1 even, 0 odd).
    # So chi(X) = (# off-middle even degrees) + (-1)^n * b_n. Count the off-middle
    # even degrees in [0, 2n] over HELD arithmetic; subtract the middle if it is even.
    total_even = _reason.solve({"plus": {"left": n, "right": 1}}, {})        # 0,2,..,2n
    middle_even = 1 if (n % 2 == 0) else 0
    off_mid_even = _reason.solve(
        {"minus": {"left": total_even, "right": middle_even}}, {})
    out.link_reached = "apply"

    # LINK 5 — COMPUTE chi via the read Hirzebruch GF, then REDUCE to b_n.
    try:
        chi = _hirzebruch_chi(degrees, n)
    except Exception as e:
        out.bucket = "D_compute_stall"
        out.detail = f"Hirzebruch chi compute raised: {type(e).__name__}: {e}"
        return out
    # b_n = (chi - off-middle-even) / (-1)^n  -> for n even, b_n = chi - off_mid_even.
    diff = _reason.solve({"minus": {"left": chi, "right": off_mid_even}}, {})
    b_n = diff if (n % 2 == 0) else _reason.solve(
        {"times": {"left": diff, "right": -1}}, {})
    out.link_reached = "compute"
    out.value = int(b_n)
    out.bucket = "NUMBERED"
    out.detail = (f"dim H^{deg}(X,Q) = b_{n} = {out.value} via Lefschetz (off-middle "
                  f"= CP^{n}) + Hirzebruch chi={chi} (chi = {off_mid_even} + "
                  f"(-1)^{n} b_{n}); multidegree {tuple(degrees)} in CP^{form.data['ambient_dim']}")
    out.provenance.append(("apply", "lefschetz+hirzebruch",
                           f"chi={chi}, off_mid_even={off_mid_even}, b_{n}={out.value}"))
    return out


# ===========================================================================
# ROUTE D — SUBGROUP COUNT of a NAMED LITERATURE GROUP (Grigorchuk, Gupta-Sidki, ...).
# These branch/self-similar groups do NOT split as a free product, so no held recursion
# computes their subgroup counts; the value is a COMPUTED result in the frontier
# literature. RETRIEVE the stated count from the BROADENED source (wiki body -> arXiv
# local -> bounded arXiv fetch) and HARVEST the number for the asked index. This is the
# "source is not fixed" route: the theorem cost is near-zero-marginal (one general read-
# path), only the per-form recognizer cost remains. HONEST MISS (no value) when no
# reachable source states the count — never a baked answer, never the key.
# ===========================================================================

# "<count> subgroups of index <n>" / "index <n> ... <count> subgroups" — harvest the
# COUNT for the asked index from a retrieved source sentence. The count is the SOURCE's
# own stated number, not a computed-here value.
def _harvest_index_count(sentence: str, n: int):
    """Read the stated number of index-n subgroups out of a retrieved source sentence.
    Returns the integer when the sentence states it for THIS index, else None. A
    mechanical surface read of the SOURCE's words — no arithmetic, no answer baked."""
    s = sentence or ""
    pats = [
        rf"(\d+)\s+subgroups?\s+of\s+index\s+{n}\b",
        rf"index\s+{n}\b[^.]*?\bhas\s+(\d+)\s+subgroups?",
        rf"index\s+{n}\b[^.]*?\bexactly\s+(\d+)\b",
        rf"number\s+of\s+(?:index[\s-]?{n}\s+)?subgroups?[^.]*?\bis\s+(\d+)\b",
    ]
    for p in pats:
        m = re.search(p, s, re.I)
        if m:
            return int(m.group(1))
    return None


def route_subgroup_count_named_group(stem: str, asked: dict, form) -> Routed:
    out = Routed(asked_kind="subgroup_count", form=form.form, link_reached="recognise")
    n = asked.get("index")
    name = form.data.get("group_name")
    if n is None or not name:
        out.bucket = "B_object_unread"
        out.detail = f"named-group subgroup-count ask but index ({n}) / name ({name}) unread"
        return out

    # LINK 3 — RETRIEVE the stated count from the BROADENED source (wiki body, then the
    # arXiv local statement corpus, then — if OZMA_BROADEN_FETCH=1 — a bounded arXiv
    # fetch keyed on the group name). The broad reader returns the SOURCE's own sentence.
    harvested = None
    src_sentence = None
    for t in _rgf.retrieve_theorems(form, about="subgroup_count"):
        out.in_source = out.in_source or t.found_in_source
        out.provenance.append(("retrieve",
                               "FROM SOURCE" if t.found_in_source else "cited prior",
                               t.cite[:80]))
        if t.found_in_source:
            val = _harvest_index_count(t.cite, n)
            if val is not None:
                harvested = val
                src_sentence = t.cite[:120]
                break
    out.link_reached = "retrieve"

    if harvested is None:
        # The broadened source did not STATE the count in a harvestable sentence. Before
        # an honest miss, try the CONSTRUCTIVE-COMPUTATION path: if the named group's
        # action is HELD, CONSTRUCT it over the held primitives and COMPUTE the count
        # (enumerate Hom(G,S_k) over the constructed action -> Hall recursion), with an
        # independent transitive-action cross-check. This is the parallel path for a
        # COMPUTED-NUMBER invariant the literature reports in tables/code, not prose. No
        # answer baked; the value is computed from first principles, the key never read.
        from domains import construct_compute_subgroups as _ccs
        if _ccs.can_construct(name):
            comp = _ccs.compute_subgroup_count(name, n)
            if comp.value is not None:
                out.value = int(comp.value)
                out.link_reached = "compute"
                out.bucket = "NUMBERED"
                out.in_source = False  # CONSTRUCTED + COMPUTED, not read from source
                out.detail = comp.detail
                out.provenance.append(
                    ("construct", "wreath_recursion",
                     f"G_m on 2^{comp.depth_used} leaves (held tree action)"))
                out.provenance.append(
                    ("compute", "hall_recursion+transitive_crosscheck",
                     f"a_{n}={out.value}; h_k={comp.hom_counts}; "
                     f"cross-check t_{n}/(n-1)!={comp.cross_check}"))
                return out
            # constructible but the computation stalled — name the construct/enumerate
            # reason precisely (still not a baked answer).
            out.bucket = "C_construct_compute_stall"
            out.detail = (f"{name}: not stated in source; constructive path attempted "
                          f"but stalled -> {comp.detail}")
            return out
        # HONEST MISS: neither stated in a harvestable source NOR a held construction.
        # Named precisely (this is what is still blocked, not faked).
        out.bucket = "C_count_not_in_source"
        out.detail = (f"{name}: index-{n} subgroup count is a computed literature result "
                      f"but no reachable source (wiki body / arXiv local"
                      f"{' / arXiv fetch' if _bs_fetch_on() else ''}) states it in a "
                      f"harvestable sentence and no held construction of the group "
                      f"-> honest miss (no baked answer)")
        return out

    out.value = int(harvested)
    out.link_reached = "compute"
    out.bucket = "NUMBERED"
    out.detail = (f"#index-{n} subgroups of {name} = {out.value} READ from source "
                  f"({src_sentence!r})")
    out.provenance.append(("harvest", "stated_count", f"index-{n} -> {out.value}"))
    return out


def _bs_fetch_on() -> bool:
    try:
        from domains import broaden_source as _bs
        return bool(_bs._FETCH_ENABLED)
    except Exception:
        return False


# ===========================================================================
# THE CONSTRUCT-COMPUTE CORE (CONSOLIDATION) — one general dispatcher over a SPEC
# TABLE, specialising the shared construct->certify->compute spine that ALL the
# self-contained faculties walk. Each faculty (bounded enumeration; graph count;
# element-order count; named-space Betti; glued-CW pi_1; minimal-generators; pi_n
# rank) exposes the SAME interface — a `read(stem) -> {"kind": ...|None}` surface
# read and a `compute(stem) -> Result(value, detail, provenance)` first-principles
# construct+compute (value None = honest stall under a NAMED certificate). The
# router previously carried SEVEN ~25-line wrappers that differed only in three
# constants. This core unifies them: the spine is written ONCE, each faculty is
# one DATA ROW. Adding a future faculty is now a one-line row, not a new wrapper.
#
# Each row: (module, asked_kind, form_label, stall_bucket). `asked_kind=None` means
# "read the kind off the faculty's own `read(stem)['kind']`" (the enumeration /
# Betti faculties type their own sub-kind); a string means a fixed asked-kind for
# the family. The shared spine: read -> (None? fall through) -> compute -> (value
# None? NAMED stall : NUMBERED, value cast to int when integral, never read the key).
# ===========================================================================

# the spec rows, in dispatch order (self-contained faculties first, before the
# group-form-recognition routes). DATA, not code — one row per certified faculty:
# (surface-reader, certified-compute, asked_kind, form_label, stall_bucket). An
# asked_kind of None means "read the sub-kind off the faculty's own reader output"
# (the enumeration / Betti faculties type their own sub-kind).
_CONSTRUCT_COMPUTE = [
    (_cce.read_enumeration,   _cce.compute,  None,                 "bounded_enumeration",    "C_enumeration_out_of_bound"),
    (_ccg.read_graph_count,   _ccg.compute,  "graph_count",        "graph_enumeration",      "C_graph_count_out_of_bound"),
    (_ccgo.read_element_order, _ccgo.compute, "element_order_count", "constructible_group",   "C_group_not_constructible"),
    (_ccb.read_betti,         _ccb.compute,  None,                 "named_standard_space",   "C_space_not_certified"),
    (_ccp.read_pi1,           _ccp.compute,  "pi1_option",         "glued_cw_complex",       "C_pi1_not_certified"),
    (_ccgd.read_gendef,       _ccgd.compute, "min_generators",     "constructed_group",      "C_gendef_bracket_open"),
    (_cch.read_homotopy,      _cch.compute,  "homotopy_rank",      "simply_connected_space", "C_homotopy_not_certified"),
    (_fvl.read,               _fvl.compute,  "vc_dimension_of_logic", "formula_class_logic", "C_vc_logic_not_certified"),
    (_ffd.read,               _ffd.compute,  "fdtc_torus_one_boundary", "surface_mapping_class", "C_fdtc_not_certified"),
]


def _route_construct_compute(spec, stem: str) -> Optional[Routed]:
    """THE UNIFIED CONSTRUCT-COMPUTE SPINE (the consolidation). Walk one faculty's
    construct->certify->compute path generically: surface-read the ask; if the
    faculty does not claim the stem, return None so the router falls through; else
    CONSTRUCT + COMPUTE from first principles (the faculty's own certified compute)
    and emit a NUMBERED Routed or a NAMED stall. The KEY is never consulted; the
    value is the faculty's certified output, cast to int when integral (pi_1 emits
    an option LETTER and is passed through). General; no QID branch."""
    reader, compute, asked_kind, form_label, stall_bucket = spec
    asked = reader(stem)
    if not asked or asked.get("kind") is None:
        return None
    kind = asked_kind if asked_kind is not None else asked["kind"]
    out = Routed(asked_kind=kind, form=form_label, link_reached="recognise")
    comp = compute(stem)
    if comp.value is None:
        out.bucket = stall_bucket
        out.detail = comp.detail
        return out
    # CONSTRUCTED + COMPUTED from first principles, not read from any source.
    out.value = int(comp.value) if isinstance(comp.value, (int, bool)) else comp.value
    out.link_reached = "compute"
    out.bucket = "NUMBERED"
    # a construct-compute faculty is first-principles (no source); but a faculty whose
    # formalization READS its defining objects from an authoritative source (the VC-of-a-
    # logic definition) carries an `in_source` provenance flag — surface it when present.
    out.in_source = bool(getattr(comp, "in_source", False))
    out.detail = comp.detail
    out.provenance.extend(comp.provenance)
    return out


def route_construct_compute(stem: str) -> Optional[Routed]:
    """Try EVERY self-contained construct-compute faculty in spec order; return the
    first that claims the stem (NUMBERED or a NAMED stall), else None so the router
    proceeds to the group-form-recognition dispatch. The whole construct-compute
    tier, data-driven from `_CONSTRUCT_COMPUTE`."""
    for spec in _CONSTRUCT_COMPUTE:
        r = _route_construct_compute(spec, stem)
        if r is not None:
            return r
    return None


# ===========================================================================
# THE ROUTER — DISPATCH on (asked-kind x recognised-form). General; no QID branch.
# Returns a Routed carrying the value (if reached) + the honest per-link bucket.
# ===========================================================================

# the dispatch table: (asked-kind, form) -> the matching held derivation route.
_DISPATCH = {
    ("cohomology_dim", "amalgamated_free_product"): route_cohomology_dim_amalgam,
    ("subgroup_count", "free_product_of_cyclics"): route_subgroup_count_free_product,
    ("cohomology_dim", "complete_intersection"):
        route_middle_cohomology_complete_intersection,
    ("subgroup_count", "named_literature_group"):
        route_subgroup_count_named_group,
}


def route_question(qid: str, stem: str) -> Routed:
    """ROUTE an arbitrary question through the first-principles chain. READ the asked
    quantity -> RECOGNISE the form -> DISPATCH to the matching held derivation. Each
    stall is bucketed by the NAMED link it reached. The KEY is never consulted."""
    # FIRST: the unified CONSTRUCT-COMPUTE tier — every self-contained faculty that
    # needs no group-form recognition (the object is a fully-determined finite domain
    # the faculty constructs and computes over from first principles), walked in spec
    # order by the consolidated core. Returns the first faculty that claims the stem.
    cc = route_construct_compute(stem)
    if cc is not None:
        cc.qid = qid
        return cc

    asked = read_asked(stem)
    if asked["kind"] is None:
        return Routed(qid=qid, link_reached="type", bucket="A_no_asked_kind",
                      detail="no recognised asked-quantity surface "
                             "(cohomology dimension / subgroup count)")
    form = recognise(stem)
    if form is None:
        return Routed(qid=qid, asked_kind=asked["kind"], link_reached="recognise",
                      bucket="C_form_unrecognised",
                      detail=f"asked {asked['kind']} read but no structural form "
                             f"recognised off the object surface")
    route = _DISPATCH.get((asked["kind"], form.form))
    if route is None:
        return Routed(qid=qid, asked_kind=asked["kind"], form=form.form,
                      link_reached="recognise", bucket="C_no_route",
                      detail=f"asked {asked['kind']} on form {form.form!r} has no "
                             f"matched derivation route in the held faculties")
    r = route(stem, asked, form)
    r.qid = qid
    return r


__all__ = ["Routed", "read_asked", "recognise", "route_question",
           "route_construct_compute",
           "route_cohomology_dim_amalgam", "route_subgroup_count_free_product",
           "route_middle_cohomology_complete_intersection",
           "route_subgroup_count_named_group"]
