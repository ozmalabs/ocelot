#!/usr/bin/env python3
"""recognise_group_form — RECOGNISE a group's STRUCTURAL SPLITTING FORM from the
SYNTACTIC SHAPE of its presentation's relator(s).

THE GAP THIS CLOSES (link 2B of the H^2(G,M) derivation). Given a presentation
<gens | rels> (already parsed by prose_to_operation.parse_presentations), decide
the STRUCTURAL FORM of the group — free / free-product / amalgamated-free-product /
... — from the RELATOR SHAPE alone, NOT from a concept name and NOT from the answer.
This is the "a^8 = b^8 ⇒ G = Z *_Z Z" recognition that derive_h2_amalgam.py used to
print as a hand-written LINK 2; here it is PRODUCED by a general parse of the relator.

GENERAL (no per-question branch — the SAME shape-tests run on every presentation,
mirroring prose_to_operation.extract_operations' delta-shape classifier):

  · NO relators                                  -> free  (free group on the gens).
  · every relator is a single GENERATOR POWER
    x^n = 1 (a torsion relator on ONE generator) -> free_product_of_cyclics
                                                     (each generator a finite cyclic
                                                     factor C_n; <a|a^n> = C_n).
  · a SINGLE relator equating a POWER of one
    generator to a POWER of another,  x^p = y^q,
    on a 2-generator presentation                -> amalgamated_free_product
            G = <x> *_<t> <y>  with  t = x^p = y^q,  each vertex group infinite
            cyclic Z = <x> / <y>, the edge group the common cyclic <t> = Z.
            (x^p = y^q is ONE relator, NOT a proper power on a single generator,
            so the free-product-with-amalgamation normal form holds.)

The FORM carries the data a downstream theorem needs (the vertex groups, the edge
group, the amalgamation exponents) — read off the relator, so the theorem-retrieval
(link 3) can key on the form, not on the prose.

FAITHFUL (CLAUDE.md): a thin SURFACE-STRUCTURE translator. It reads the parsed
presentation (a boundary parse) and matches the relator's SYNTAX against general
shape patterns; it makes NO decision over graph state, holds no agent state, runs no
rule engine. The classification is the relator's shape, the same register as
prose_to_operation's delta classifier. No LLM, no Rust.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from domains import prose_to_operation as _pto


# a single generator raised to a power, possibly compared to 1:  x^n  /  x^n = 1.
# group(1) = the generator letter, group(2) = the exponent.
_POWER_RE = re.compile(r"^([A-Za-z])\s*\^?\s*\{?\s*(\d+)\s*\}?\s*(?:=\s*1)?$")
# a power-equals-power relator:  x^p = y^q   (two DISTINCT generator letters).
# group(1)=x, group(2)=p, group(3)=y, group(4)=q.
_POWEQ_RE = re.compile(
    r"^([A-Za-z])\s*\^?\s*\{?\s*(\d+)\s*\}?\s*=\s*"
    r"([A-Za-z])\s*\^?\s*\{?\s*(\d+)\s*\}?$")


@dataclass
class GroupForm:
    """The recognised STRUCTURAL FORM of a group, read off the presentation's
    relator shape. `form` is the splitting-form label a downstream theorem keys on;
    `data` carries the read structural parameters (vertex/edge groups, exponents)."""
    form: str                                  # free | free_product_of_cyclics |
    #                                            amalgamated_free_product | unknown
    gens: List[str] = field(default_factory=list)
    rels: List[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)   # vertex_groups, edge_group, exponents
    evidence: str = ""                         # the relator-shape the form came from
    recognised: bool = False


def _norm_rel(r: str) -> str:
    """Light surface cleanup of a relator: collapse whitespace, drop a leading
    'where'/braces the prose register leaves. Mechanical."""
    t = re.sub(r"\s+", " ", r).strip()
    return t


def recognise_form(gens: List[str], rels: List[str]) -> GroupForm:
    """Classify the structural form from the relator SHAPE. The same shape-tests on
    every presentation; the form is the relator's syntax, not the concept name."""
    rels = [_norm_rel(r) for r in rels if _norm_rel(r)]

    # FREE — no relators.
    if not rels:
        return GroupForm(form="free", gens=gens, rels=rels,
                         data={"rank": len(gens)},
                         evidence="no relators -> free group on the generators",
                         recognised=True)

    # FREE PRODUCT OF CYCLICS — every relator is a single-generator power x^n(=1).
    powers = [_POWER_RE.match(r) for r in rels]
    if powers and all(powers):
        cyc = {m.group(1): int(m.group(2)) for m in powers}
        return GroupForm(
            form="free_product_of_cyclics", gens=gens, rels=rels,
            data={"factors": [{"gen": g, "order": n} for g, n in cyc.items()]},
            evidence=("every relator a single-generator power x^n=1 -> each "
                      f"generator a finite cyclic factor: {cyc}"),
            recognised=True)

    # AMALGAMATED FREE PRODUCT — a SINGLE relator  x^p = y^q  on 2 DISTINCT
    # generators. The two cyclic <x>, <y> amalgamated over the common <x^p>=<y^q>.
    if len(rels) == 1:
        m = _POWEQ_RE.match(rels[0])
        if m and m.group(1) != m.group(3):
            x, p, y, q = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
            # the two relator generators must be ALL the generators for the GLOBAL
            # form to be the clean amalgam Z *_Z Z; any EXTRA generator is a free
            # factor (G = (Z *_Z Z) * F), flagged in the data so we do not overclaim.
            relator_gens = {x, y}
            extra = [gn for gn in gens if gn not in relator_gens]
            return GroupForm(
                form="amalgamated_free_product", gens=gens, rels=rels,
                data={
                    "free_factors": extra,
                    "pure_amalgam": not extra,
                    "vertex_groups": [
                        {"gen": x, "group": "Z", "edge_exponent": p},
                        {"gen": y, "group": "Z", "edge_exponent": q},
                    ],
                    "edge_group": "Z",
                    "edge_element": f"{x}^{p} = {y}^{q}",
                    "exponents": {x: p, y: q},
                },
                evidence=(f"single relator equates a power of {x} to a power of {y} "
                          f"({x}^{p} = {y}^{q}) -> <{x}>=Z and <{y}>=Z amalgamated "
                          f"over the common cyclic <{x}^{p}>=<{y}^{q}>=Z, "
                          f"i.e. G = Z *_Z Z"),
                recognised=True)

    return GroupForm(form="unknown", gens=gens, rels=rels,
                     evidence=f"relator shape not matched: {rels}", recognised=False)


# ===========================================================================
# LINK 3 — RETRIEVE the theorem that APPLIES to a recognised form. The recognised
# form (amalgamated_free_product / free_product_of_cyclics / free) names the
# HYPOTHESIS a structural theorem keys on; this maps the form -> the applicability
# KEYWORDS the theorem must mention, then queries the READ SOURCE (the held
# ground_reductions._read_statement corpus reader) for a statement carrying them.
# The retrieval is general (form -> keywords -> source scan); whether a statement
# comes back depends on what the SOURCE contains — an HONEST miss when it does not.
# ===========================================================================

# the structural theorems keyed by the FORM they apply to: each entry names the
# article(s) to consult + the keywords a relevant statement must carry. GENERAL
# (the form is the hypothesis; the theorem is read, not hand-coded). The INVARIANT
# the question asks (cohomology / cd / ends / ...) selects which keyword family to
# require, so the SAME form retrieves the cohomology-theorem for an H^n question and
# the ends-theorem for an ends question.
_FORM_THEOREMS = {
    "amalgamated_free_product": [
        {"about": "cohomology",
         # the MV-for-amalgams statement lives in the BODY of 'Group cohomology'
         # (read once the section JSON is parsed); the other titles are real
         # fallbacks. The keyword pair "amalgamated product" + "long exact
         # sequence" matches the article's OWN phrasing of the theorem (it writes
         # "the homology of the amalgamated product ... lies in a long exact
         # sequence"), so the genuine sentence is recognised from source.
         "titles": ["Group cohomology", "Mayer-Vietoris sequence",
                    "Cohomology of groups", "Bass-Serre theory"],
         "keywords": ["amalgamated product", "amalgam", "mayer",
                      "long exact sequence"],
         "require_pair": [["amalgam", "exact sequence"],
                          ["amalgam", "mayer"]],
         "fallback": "for G = A *_C B there is a Mayer-Vietoris long exact sequence "
                     "... -> H^n(A,M) + H^n(B,M) -> H^n(C,M) -> H^{n+1}(G,M) -> ... "
                     "[Bieri / Bass-Serre]."},
        {"about": "ends",
         "titles": ["Stallings theorem about ends of groups"],
         "keywords": ["amalgam", "hnn", "more than one end", "ends"],
         "fallback": "a f.g. group splitting as a nontrivial amalgam over a finite "
                     "subgroup has more than one end [Stallings]."},
    ],
    "free_product_of_cyclics": [
        {"about": "virtually_free",
         "titles": ["Free product"],
         "keywords": ["virtually free", "free product", "finite"],
         "fallback": "a free product of finite groups is virtually free [KPS]."},
        {"about": "subgroup_growth",
         # the transitive-sifting (Hall) recursion lives in the BODY of 'Subgroup
         # growth': "s_n(G) = h_n(G)/(n-1)! - sum ... h_{n-v}(G) s_v(G)/(n-v)!".
         # The pair "transitive" + "(n-1)!" matches its own phrasing of the recursion.
         "titles": ["Subgroup growth"],
         "keywords": ["transitive", "index", "(n-1)!", "(n − 1) !"],
         "require_pair": [["transitive", "(n − 1) !"], ["transitive", "(n-1)!"],
                          ["number of transitive", "divided by"]],
         "fallback": "the number s_n(G) of index-n subgroups satisfies the Hall "
                     "recursion s_n = h_n/(n-1)! - sum_{v<n} h_{n-v}/(n-v)! s_v, "
                     "where h_n = #Hom(G,S_n) [M. Hall 1949]."},
    ],
    "free": [
        {"about": "cohomological_dimension",
         "titles": ["Cohomological dimension"],
         "keywords": ["free group", "cohomological dimension", "cd"],
         "fallback": "a free group has cohomological dimension 1 [Stallings-Swan]."},
    ],
    "named_literature_group": [
        # the COMPUTED subgroup count of a named branch/self-similar group is a stated
        # LITERATURE result, NOT a held recursion. The retrieve keys on the group NAME +
        # the "subgroups of index" phrasing; the broad-source reader (wiki body, then
        # arXiv local/fetch) returns the stated count sentence when a source carries it,
        # else an HONEST miss (the cited-prior fallback names where the result lives).
        {"about": "subgroup_count",
         "titles": ["Grigorchuk group", "Gupta-Sidki group", "Branch group",
                    "Subgroup growth"],
         "keywords": ["subgroups of index", "subgroup of index", "index 4",
                      "number of subgroups"],
         "require_pair": [["subgroups of index", "4"],
                          ["number of subgroups", "index"],
                          ["index 4", "subgroup"]],
         "fallback": "the number of index-n subgroups of a branch/self-similar group "
                     "(Grigorchuk, Gupta-Sidki, ...) is a COMPUTED result in the "
                     "subgroup-growth literature [Bartholdi-Pervova; Pervova]; not "
                     "derivable from a free-product/amalgam splitting."},
    ],
    "complete_intersection": [
        # the OFF-MIDDLE Lefschetz fact + the middle-is-fixed-by-chi corollary live in
        # the BODY of 'Complete intersection' ("we can use the Lefschetz hyperplane
        # theorem to deduce that H^j(X)=Z for j<n ... the middle homology group is
        # determined by the Euler characteristic of the space"). The pair
        # "lefschetz"+"deduce" (its own phrasing) reads the genuine sentence from source.
        {"about": "middle_cohomology",
         "titles": ["Complete intersection", "Lefschetz hyperplane theorem"],
         "keywords": ["lefschetz", "euler characteristic", "middle homology"],
         "require_pair": [["lefschetz", "deduce"],
                          ["lefschetz", "hyperplane"],
                          ["middle homology", "euler characteristic"]],
         "fallback": "for a smooth complete intersection X of complex dimension n, "
                     "Lefschetz gives H^j(X;Q)=H^j(CP^n;Q) for j != n (Q in even "
                     "degrees, 0 in odd), so the middle Betti number b_n is fixed by "
                     "the Euler characteristic chi(X) [Lefschetz hyperplane theorem]."},
        # the Hirzebruch GENERATING FUNCTION for chi(X_n(a_1..a_r)) is stated verbatim
        # in the SAME article ("Hirzebruch gave a generating function computing the
        # dimension of all complete intersections of multi-degree (a_1,...,a_r)").
        {"about": "euler_characteristic",
         "titles": ["Complete intersection"],
         "keywords": ["hirzebruch", "generating function", "multi-degree"],
         "require_pair": [["hirzebruch", "generating function"],
                          ["generating function", "complete intersection"]],
         "fallback": "Hirzebruch's generating function: sum_n chi(X_n(a_1..a_r)) z^n = "
                     "(a_1...a_r)/(1-z)^2 * prod_i 1/(1+(a_i-1)z) [Hirzebruch]."},
    ],
}


@dataclass
class RetrievedTheorem:
    form: str
    about: str
    cite: str                  # what the corpus reader returned (may be a weak lead)
    where: str
    source: str
    found_in_source: bool
    statement: str = ""        # the APPLICABLE theorem statement (the structured
    #                            sequence/fact) — from source when found_in_source,
    #                            else the cited-prior fallback. This is what the
    #                            apply-faculty (apply_exact_sequence) consumes; cite
    #                            stays the honest record of what the SOURCE gave.


def retrieve_theorems(form: "GroupForm",
                      about: Optional[str] = None) -> List[RetrievedTheorem]:
    """RETRIEVE the structural theorems that apply to a recognised form. If `about`
    is given (the invariant the question asks — 'cohomology' / 'ends' / ...), only
    the matching theorem family is returned. Each theorem statement is READ from the
    source via the held ground_reductions._read_statement corpus reader; the
    `found_in_source` flag is the HONEST signal — True only when the source actually
    carries a statement with the applicability keywords (else the fallback cite is
    returned, flagged not-found, the named residual)."""
    try:
        from domains import ground_reductions as _gr
        reader = _gr._read_statement
    except Exception:
        reader = None
    out: List[RetrievedTheorem] = []
    for entry in _FORM_THEOREMS.get(form.form, []):
        if about is not None and about not in entry["about"]:
            continue
        got = None
        require_pair = entry.get("require_pair")
        if reader is not None:
            for title in entry["titles"]:
                r = reader(title, entry["keywords"], entry["fallback"],
                           require_pair=require_pair)
                # a genuine source hit: the reader found the article AND the
                # harvested cite is NOT the fallback (the body carried the theorem)
                # AND the harvested sentence ACTUALLY carries the applicability
                # signal. When a require_pair is set the sentence must carry BOTH
                # terms of some pair (the precise theorem sentence, not a loose
                # single-word mention); else any one keyword suffices.
                cite = (r.get("cite") or "").lower()
                if require_pair is not None:
                    carries = any(all(t in cite for t in pair)
                                  for pair in require_pair)
                else:
                    carries = any(k in cite for k in entry["keywords"])
                hit = (r.get("found") and r.get("cite") != entry["fallback"]
                       and carries)
                if hit:
                    got = (r, True)
                    break
                if got is None and r.get("found"):
                    got = (r, False)
        if got is None:
            out.append(RetrievedTheorem(
                form=form.form, about=entry["about"], cite=entry["fallback"],
                where="(no source)", source="cited prior (not in local corpus)",
                found_in_source=False, statement=entry["fallback"]))
        else:
            r, in_src = got
            # the APPLICABLE statement: the source sentence when it genuinely carried
            # the theorem (found_in_source), else the cited-prior structured fallback
            # (the weak lead the corpus returned is NOT the applicable theorem). cite
            # stays the honest record of what the corpus gave; statement is what the
            # apply-faculty consumes.
            stmt = r["cite"] if in_src else entry["fallback"]
            out.append(RetrievedTheorem(
                form=form.form, about=entry["about"], cite=r["cite"],
                where=r.get("where", ""), source=r.get("source", ""),
                found_in_source=in_src, statement=stmt))
    return out


# a cyclic factor written by NAME + ORDER: 'C_2', 'C_{5}', 'Z/2', 'Z/2Z',
# 'the cyclic group of order 5'. group(1) = the order. GENERAL surface forms.
_CYCLIC_NAMED = re.compile(
    r"C\s*_?\s*\{?\s*(\d+)\s*\}?"
    r"|\\mathbb\{?Z\}?\s*/\s*(\d+)\s*\\?mathbb?\{?Z?\}?"
    r"|Z\s*/\s*(\d+)\s*Z?"
    r"|cyclic group of order\s+(\d+)")
# the free-product operator surface: '*', '\ast', '\star', the word 'free product'.
_FREEPROD = re.compile(r"\\ast|\\star|\*|free product", re.I)


def recognise_from_free_product_expr(text: str) -> Optional[GroupForm]:
    """RECOGNISE a free-product-of-cyclics group written as an EXPRESSION over named
    cyclic factors — 'C_2 * C_5', 'Z/2 * Z/5', 'the free product of the cyclic group
    of order 2 and the cyclic group of order 5'. This is the SAME structural form
    recognise_form yields from a presentation <a,b|a^2,b^5>, recovered from the OTHER
    common surface (named factors joined by the free-product operator). GENERAL: read
    every named cyclic factor + require the free-product operator joins them; emit the
    free_product_of_cyclics form with the factor orders. No per-question branch."""
    if not _FREEPROD.search(text):
        return None
    orders: List[int] = []
    for m in _CYCLIC_NAMED.finditer(text):
        g = next((x for x in m.groups() if x is not None), None)
        if g is not None:
            orders.append(int(g))
    if len(orders) < 2:
        return None
    return GroupForm(
        form="free_product_of_cyclics",
        gens=[f"x{i+1}" for i in range(len(orders))],
        rels=[f"x{i+1}^{n}" for i, n in enumerate(orders)],
        data={"factors": [{"gen": f"x{i+1}", "order": n}
                          for i, n in enumerate(orders)]},
        evidence=(f"a free product of named cyclic factors of orders {orders} "
                  f"(C_{orders[0]} * ... joined by the free-product operator) -> "
                  f"free product of cyclics"),
        recognised=True)


# a NAMED group whose invariants are a STATED LITERATURE RESULT (not derivable by a
# held free-product/amalgam recursion). 'the Grigorchuk group', 'the Gupta-Sidki
# group', 'the Hanoi towers group', ... are self-similar/branch groups whose subgroup
# counts / growth / Hausdorff dimension are COMPUTED in the frontier literature; the
# only honest way to a number is to RETRIEVE the stated result from a broad source. The
# recognizer reads the NAME off the surface (no answer, no held recursion) so the
# retrieve link can key on it. GENERAL: any named group in this family routes the same
# way — the recogniser cost is the only marginal cost (the theorem is read-from-source).
_NAMED_LITERATURE_GROUPS = (
    (r"\bGrigorchuk group\b", "Grigorchuk group"),
    (r"\b(?:first|second)\s+Grigorchuk group\b", "Grigorchuk group"),
    (r"\bGupta[-–\s]?Sidki group\b", "Gupta-Sidki group"),
    (r"\bHanoi [Tt]owers? group\b", "Hanoi towers group"),
    (r"\bbasilica group\b", "Basilica group"),
    (r"\bGGS[-–\s]?group\b", "GGS-group"),
)


def recognise_named_literature_group(text: str) -> Optional["GroupForm"]:
    """RECOGNISE a NAMED self-similar / branch group whose invariants are a STATED
    LITERATURE RESULT (the Grigorchuk group, Gupta-Sidki, Hanoi towers, ...). These do
    NOT split as a free product / amalgam, so no held recursion computes their subgroup
    counts; the value is a COMPUTED result in the frontier literature, reachable only by
    RETRIEVE-from-source. Reads the group NAME off the surface (no answer); emits the
    `named_literature_group` form carrying the name a source-scan keys on. GENERAL: the
    same name-scan on every stem, no per-question branch."""
    for pat, name in _NAMED_LITERATURE_GROUPS:
        if re.search(pat, text, re.I):
            return GroupForm(
                form="named_literature_group", gens=[], rels=[],
                data={"group_name": name},
                evidence=(f"the {name} — a named self-similar/branch group whose "
                          f"subgroup counts/invariants are a computed LITERATURE "
                          f"result (no free-product/amalgam splitting); reachable "
                          f"only by retrieving the stated result from a broad source"),
                recognised=True)
    return None


# a complete-intersection SURFACE: "complete intersection of (multi-)degree (d_1,...,d_r)"
# + an ambient complex projective space CP^N. The form a downstream Lefschetz +
# Hirzebruch theorem keys on; the structural data (the multidegree + the ambient
# dimension) is read off the surface, not the answer.
_CI_MULTIDEG_RE = re.compile(
    r"complete intersection\b.*?\bof\s+(?:multi-?)?degree\s*\(\s*([\d,\s]+?)\s*\)",
    re.I | re.S)
# the ambient complex projective space CP^N (\mathbb{C}P^N / CP^N / P^N), the dim N.
_CPN_RE = re.compile(
    r"(?:\\?mathbb\s*\{?\s*C\s*\}?\s*|\bC\s*)?P\s*\^\s*\{?\s*(\d+)", re.I)


def recognise_complete_intersection(text: str) -> Optional["GroupForm"]:
    """RECOGNISE a smooth COMPLETE INTERSECTION of multidegree (d_1,...,d_r) in an
    ambient complex projective space CP^N — the structural form a Lefschetz-hyperplane
    + Hirzebruch argument keys on. READ the multidegree tuple + the ambient dimension N
    off the surface; the complex dimension is n = N - r (codimension r = #degrees).
    GENERAL: the same surface tests on every stem; no per-question branch, no answer.
    Returns a GroupForm (reusing the recognised-form carrier) with the read data, or
    None when no complete-intersection surface is present."""
    md = _CI_MULTIDEG_RE.search(text)
    if md is None:
        return None
    degrees = [int(x) for x in re.findall(r"\d+", md.group(1))]
    if not degrees:
        return None
    r = len(degrees)
    cp = _CPN_RE.search(text)
    if cp is None:
        return None
    N = int(cp.group(1))
    n = N - r  # the complex dimension of the complete intersection
    if n < 0:
        return None
    return GroupForm(
        form="complete_intersection",
        gens=[], rels=[],
        data={"degrees": degrees, "ambient_dim": N, "codim": r, "dim_n": n,
              "middle_degree": n},
        evidence=(f"complete intersection of multidegree {tuple(degrees)} in CP^{N} "
                  f"-> codimension r={r}, complex dimension n=N-r={n}; by Lefschetz the "
                  f"cohomology equals that of CP^n off the middle degree n, the middle "
                  f"Betti number fixed by the Euler characteristic (Hirzebruch)"),
        recognised=True)


def recognise_from_presentation(text: str) -> List[GroupForm]:
    """READ every presentation written in `text` (via the held
    prose_to_operation.parse_presentations boundary parser) and recognise the
    structural form of each. The whole pipeline link 2B: prose -> presentation ->
    structural form, from the relator's shape."""
    out: List[GroupForm] = []
    for p in _pto.parse_presentations(text):
        out.append(recognise_form(p.gens, p.rels))
    return out


__all__ = ["GroupForm", "RetrievedTheorem", "recognise_form",
           "retrieve_theorems", "recognise_from_presentation",
           "recognise_from_free_product_expr", "recognise_complete_intersection",
           "recognise_named_literature_group"]
