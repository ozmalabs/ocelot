"""commutator_rank — WALL B of the cmsg121 construct-and-compute climb: the two
pi_1 / commutator-subgroup-rank operators the assessment named, ACQUIRED over the
HELD fp_group engine (coset_index / complete_presentation / the rewrite layer) +
the held SNF (reason._smith_normal_form_factors). NO new Rust, NO new primitive
engine — these COMPOSE over the held machinery, the same acquire-ladder
construction_operators used for the description->object constructors.

THE GAP (cmsg121, Wall B): the asked invariant for the construct-and-compute class is
the RANK of Ker(Hurewicz h_*: pi_1 -> H_1) AS A FREE GROUP. Ker(h_*) = [pi_1,pi_1]
(the commutator subgroup — Hurewicz, dim 1). The held tower computes HOMOLOGY (H_1),
but NOT pi_1 from the CW description, NOR the free rank of [pi_1,pi_1]. Two operators
bridge that, each reducing to held machinery:

  OPERATOR (1) pi1_from_cw — READ the CW 2-cell's ATTACHING WORD(s) -> the group
      PRESENTATION <1-cells (generators) | attaching-word(s) (relators)>. This is
      van Kampen for a CW 2-complex (READ/cited): pi_1 of a 2-complex with one
      0-cell is <the 1-cells | the 2-cells' attaching words>. The agent reads the
      held construction_operators' CW build (which already produces the edge-letters
      + the attaching word) and EMITS the presentation. VERIFY vs KNOWN:
        torus  aba^-1b^-1 -> <a,b | abAB>   (pi_1 = Z^2)
        RP^2   aa         -> <a   | aa>      (pi_1 = Z/2)

  OPERATOR (2) commutator_free_rank — the free rank of [G,G] for G = <gens | rels>.
      READ (cited): when H_1 = G^ab is FINITE of order m and [G,G] is FREE (G is
      virtually free — e.g. a free product of finite cyclics), the
      Euler-characteristic / Nielsen-Schreier index relation gives
          rank[G,G] = 1 - m * chi(G),     m = |H_1| = [G : [G,G]],
      where chi(G) is the Euler characteristic of the presentation 2-complex
      (1 - #gens + #rels for a one-vertex presentation), and the finite-index-m
      subgroup [G,G] has chi = m*chi(G) = 1 - rank (a free group of rank r has
      chi = 1 - r). The COMPUTE reduces to held arithmetic: m = |H_1| via the held
      SNF over the abelianized relator matrix (the SAME read integral_homology uses)
      or the held coset_index (Todd-Coxeter [G:[G,G]]); chi from the presentation
      sizes. VERIFY vs KNOWN: the modular group Z/2 * Z/3 = <a,b | a^2, b^3> has
      [G,G] free of rank 1 + 6*(2-1) = 7 (m=6, chi=1-2+2... see below).

INTEGRITY (cmsg121 rails): the operators VERIFY vs KNOWN groups, NEVER vs the
exemplar's answer. The rank FORMULA is READ (cited Nielsen-Schreier / Euler char);
the COMPUTE is the held engine + held arithmetic. The honest GUARD: the finite-rank
formula APPLIES ONLY when H_1 is FINITE and [G,G] is free (G virtually free); when
H_1 is INFINITE the operator REPORTS that [G,G] is not finite-rank-free (the named
stall), never forces a number.

No LLM, no Rust. Held-tower math. See [[ozma_agent_writes_its_own_code]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_HLE_derivation_engine]].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from domains import reason as _reason


# ===========================================================================
# OPERATOR (1) pi1_from_cw — the CW attaching word(s) -> the group presentation.
# READ (van Kampen): pi_1 of a 2-complex with ONE 0-cell = <1-cells | 2-cells'
# attaching words>. We consume the held construction_operators' CW build (its
# `edges` = the 1-cells, and the polygon WORD = the single 2-cell's attaching
# word). For a multi-relator construction (e.g. a connected sum of pseudo-surfaces
# built by amalgamation), the caller supplies the relator word list directly.
# ===========================================================================

@dataclass
class Presentation:
    generators: str                       # the 1-cells, as a generator alphabet
    relators: List[str]                   # the attaching words (uppercase = inverse)
    note: str = ""

    def __repr__(self) -> str:
        rels = ", ".join(self.relators) if self.relators else "(free)"
        return f"<{self.generators} | {rels}>"


def _word_to_relator(word: List[Tuple[str, int]]) -> str:
    """A parsed polygon word [(letter, sign)] -> a relator STRING in the coset/Todd-
    Coxeter convention: a forward letter is itself, an inverse letter is its
    UPPERCASE (the engine's self-/named-inverse convention). E.g. the torus word
    [(a,+),(b,+),(a,-),(b,-)] -> 'abAB'."""
    out = []
    for c, s in word:
        out.append(c if s > 0 else c.upper())
    return "".join(out)


def pi1_from_polygon_word(word_str: str) -> Presentation:
    """OPERATOR (1), single-2-cell case: read ONE attaching word -> <edge-letters |
    the attaching word>. The generators are the DISTINCT edge-letters (the 1-cells);
    the single relator is the attaching word in the inverse-as-uppercase convention.
    READ: van Kampen for a one-2-cell complex. Composes over construction_operators'
    word parse — no library literal."""
    from domains.construction_operators import parse_word
    parsed = parse_word(word_str)
    gens = "".join(sorted(set(c for c, _ in parsed)))
    relator = _word_to_relator(parsed)
    return Presentation(generators=gens, relators=[relator],
                        note="pi_1 = <1-cells | attaching-word> (van Kampen, READ)")


def pi1_from_relators(generators: str, relator_words: List[str]) -> Presentation:
    """OPERATOR (1), general case: an explicit generator alphabet + a list of relator
    polygon-words (each in the parse_word syntax) -> the presentation. Used when the
    construction yields MORE than one 2-cell / relation (e.g. a connected sum of
    pseudo-surfaces, whose van Kampen amalgamation gives k-1 relations
    a_1^{n_1}=...=a_k^{n_k}). The agent supplies the relators from its comprehension
    of the gluing; this operator only TYPES them into the held presentation form."""
    from domains.construction_operators import parse_word
    rels = [_word_to_relator(parse_word(w)) for w in relator_words]
    return Presentation(generators=generators, relators=rels,
                        note="pi_1 = <generators | relators> (van Kampen, READ)")


# ===========================================================================
# OPERATOR (2) commutator_free_rank — |H_1| via held machinery + the READ rank
# formula. The COMPUTE bottoms out at the held SNF / coset_index; the formula is
# cited.
# ===========================================================================

def _abelianized_relation_matrix(presentation: Presentation) -> List[List[int]]:
    """The abelianized relation matrix of <gens | rels>: row per relator, column per
    generator, entry = the signed exponent-sum of that generator in the relator
    (the held abelianization the integral_homology read already uses). H_1 = the
    cokernel = Z^gens / (rows). This is the SAME held boundary-in-coordinates the
    construction operators build."""
    gens = list(presentation.generators)
    gidx = {g: i for i, g in enumerate(gens)}
    M: List[List[int]] = []
    for r in presentation.relators:
        row = [0] * len(gens)
        for ch in r:
            low = ch.lower()
            if low in gidx:
                row[gidx[low]] += (1 if ch.islower() else -1)
        M.append(row)
    return M


@dataclass
class H1Read:
    free_rank: int
    torsion: List[int]
    order: Optional[int]                  # |H_1| if FINITE (free_rank==0), else None
    finite: bool


def h1_of_presentation(presentation: Presentation) -> H1Read:
    """H_1 = G^ab of <gens | rels>, via the HELD Smith-normal-form over the
    abelianized relation matrix (the SAME held SNF integral_homology uses). H_1 =
    Z^{#gens - rank} (+) torsion(SNF). |H_1| FINITE <=> free_rank 0; then the order
    is the product of the torsion invariants. NO new compute — the held SNF read."""
    M = _abelianized_relation_matrix(presentation)
    n = len(presentation.generators)
    snf = _reason._smith_normal_form_factors
    factors = snf(M) if M and n else []
    torsion = [d for d in factors if d > 1]
    free_rank = n - len(factors)
    if free_rank == 0:
        order = 1
        for d in torsion:
            order *= d
        return H1Read(free_rank=0, torsion=torsion, order=order, finite=True)
    return H1Read(free_rank=free_rank, torsion=torsion, order=None, finite=False)


def _euler_characteristic(presentation: Presentation) -> int:
    """chi of the presentation 2-complex (one 0-cell, #gens 1-cells, #rels 2-cells):
    chi = 1 - #gens + #rels. (The Euler characteristic the rank formula READS.)"""
    return 1 - len(presentation.generators) + len(presentation.relators)


@dataclass
class CommutatorRank:
    derived: bool                         # did the finite-rank formula APPLY + compute?
    rank: Optional[int]
    h1: H1Read = None                     # type: ignore[assignment]
    chi_group: int = 0
    formula: str = ""
    stall: str = ""                       # the named honest stall if not derived
    ledger: List[Dict[str, str]] = field(default_factory=list)


def _presentation_is_aspherical(presentation: Presentation) -> bool:
    """A relator is a PROPER POWER (w^k, k>=2) exactly when the presentation 2-complex
    has a non-trivial pi_2 (torsion) and is NOT aspherical — its presentation-chi then
    DIFFERS from the group's rational Euler characteristic, so the naive
    1 - m*chi(pres) formula is INVALID (READ: a one-relator/torsion presentation with a
    proper-power relator is not a K(G,1)). We detect a proper-power relator by the SNF
    of its single-row abelianization being a multiple > 1 (a torsion relator). If ANY
    relator is a proper power, the presentation is NOT aspherical."""
    snf = _reason._smith_normal_form_factors
    gens = list(presentation.generators)
    gidx = {g: i for i, g in enumerate(gens)}
    for r in presentation.relators:
        row = [0] * len(gens)
        for ch in r:
            low = ch.lower()
            if low in gidx:
                row[gidx[low]] += (1 if ch.islower() else -1)
        # a single-generator proper power a^k (k>=2) abelianizes to a row whose gcd>=2.
        g = 0
        for v in row:
            g = abs(v) if g == 0 else __import__("math").gcd(g, abs(v))
        # proper power detection: the relator as a WORD is a single repeated letter run
        letters = set(r.lower())
        if len(letters) == 1 and len(r) >= 2:
            return False
        if g >= 2 and sum(1 for v in row if v != 0) == 1:
            return False
    return True


def commutator_free_rank(presentation: Presentation) -> CommutatorRank:
    """OPERATOR (2): the FREE RANK of [G,G] = Ker(Hurewicz) for G = <gens | rels>.

    READ (cited): when H_1 = G^ab is FINITE of order m, [G,G] is FREE (G virtually
    free), AND the presentation 2-complex is ASPHERICAL (a K(G,1), so its chi IS the
    group's Euler characteristic), the Euler-characteristic / Nielsen-Schreier index
    relation gives
        chi([G,G]) = m * chi(G)   (finite-index-m subgroup)
        chi([G,G]) = 1 - rank     (a free group of rank r)
      => rank[G,G] = 1 - m * chi(G).
    The COMPUTE is held: m = |H_1| via the held SNF (h1_of_presentation); chi(G) from
    the presentation sizes. The formula is READ; the arithmetic is held.

    Two honest GUARDS (never force a number):
      (i)  H_1 INFINITE => [G,G] has infinite index, not finite-rank-free (named stall).
      (ii) the presentation has a PROPER-POWER relator (a^k) => it is NOT aspherical,
           so the presentation-chi is NOT the group chi and 1 - m*chi(pres) is INVALID
           (the modular group <a,b|a^2,b^3> would wrongly give -5). The operator
           REFUSES the presentation route and directs to the structural (rational
           Euler characteristic) route free_product_commutator_rank, which is the
           verified one for free products of finite cyclics."""
    h1 = h1_of_presentation(presentation)
    chi = _euler_characteristic(presentation)
    out = CommutatorRank(derived=False, rank=None, h1=h1, chi_group=chi)
    out.ledger = [
        {"label": "Ker(Hurewicz) = [pi_1, pi_1]",
         "kind": "READ", "cite": "Hurewicz theorem (dim 1): h_* is the abelianization "
                                  "pi_1 -> pi_1/[pi_1,pi_1]; kernel = [pi_1,pi_1]."},
        {"label": "index [G : [G,G]] = |H_1|",
         "kind": "READ", "cite": "G/[G,G] = G^ab = H_1."},
        {"label": f"|H_1| via held SNF over abelianized relations = "
                  f"{'order ' + str(h1.order) if h1.finite else 'INFINITE (free rank %d)' % h1.free_rank}",
         "kind": "DERIVED", "cite": "reason._smith_normal_form_factors (held)."},
        {"label": f"chi(presentation) = 1 - #gens + #rels = {chi}",
         "kind": "DERIVED", "cite": "Euler characteristic of the presentation 2-complex."},
    ]
    if not h1.finite:
        out.stall = (
            f"H_1 = G^ab is INFINITE (free rank {h1.free_rank}). Then [G,G] has "
            f"INFINITE index in G, so the finite-index Euler/Nielsen-Schreier rank "
            f"formula does NOT apply and [G,G] is (generically) not a finite-rank "
            f"free group. The operator REFUSES to emit a finite rank — the named "
            f"stall (a CORRECT construction with finite H_1 is required to close).")
        return out
    if not _presentation_is_aspherical(presentation):
        out.stall = (
            "the presentation has a PROPER-POWER relator (a^k, k>=2), so its 2-complex "
            "is NOT aspherical (it has torsion pi_2): the presentation-chi is NOT the "
            "group's rational Euler characteristic, and 1 - m*chi(pres) is INVALID. "
            "Route the structural free-product / amalgam to free_product_commutator_"
            "rank (the rational-Euler-char operator, verified on knowns).")
        return out
    m = h1.order or 0
    rank = 1 - m * chi
    out.derived = True
    out.rank = rank
    out.formula = (f"rank[G,G] = 1 - |H_1|*chi(G) = 1 - {m}*{chi} = {rank}  "
                   f"(Nielsen-Schreier / Euler characteristic, READ; aspherical pres)")
    out.ledger.append(
        {"label": out.formula, "kind": "DERIVED",
         "cite": "1 - m*chi(G): held arithmetic over the read m + chi."})
    return out


# ===========================================================================
# REGISTRATION — install the two operators into a held caps registry (the same
# boundary the construction operators install at). After install, reason.solve can
# route them; they reduce to the held SNF / coset_index.
# ===========================================================================

def operator_specs() -> List[dict]:
    return [
        {"name": "pi1_from_cw",
         "reduces_to": ["construction_operators.parse_word", "van_kampen (READ)"],
         "meaning": "read the CW 2-cell attaching word(s) -> the group presentation "
                    "<1-cells | attaching-words> (van Kampen for a 2-complex)."},
        {"name": "commutator_free_rank",
         "reduces_to": ["smith_normal_form (|H_1|)", "euler_characteristic",
                        "Nielsen-Schreier rank formula (READ)"],
         "meaning": "the free rank of [G,G] = Ker(Hurewicz): when H_1 finite of order "
                    "m, rank = 1 - m*chi(G); held SNF for m, held arithmetic for the "
                    "formula. Refuses (named stall) when H_1 infinite."},
    ]


def install(caps: dict) -> dict:
    caps["pi1_from_polygon_word"] = lambda a: pi1_from_polygon_word(a["word"])
    caps["pi1_from_relators"] = \
        lambda a: pi1_from_relators(a["generators"], a["relators"])
    caps["h1_of_presentation"] = lambda a: h1_of_presentation(a["presentation"])
    caps["commutator_free_rank"] = lambda a: commutator_free_rank(a["presentation"])
    return caps


# ===========================================================================
# VERIFY-vs-KNOWN — the integrity bar. Each operator must reproduce a KNOWN group's
# pi_1 / commutator rank. NONE is the exemplar's answer.
# ===========================================================================

# KNOWN pi_1 presentations from CW words (READ): the polygon word -> <gens | relator>.
KNOWN_PI1 = {
    "aba-b-": ("torus T^2", "ab", ["abAB"]),       # pi_1 = Z^2 (free abelian)
    "aa": ("RP^2", "a", ["aa"]),                    # pi_1 = Z/2
    "abab-": ("Klein bottle", "ab", ["abaB"]),      # pi_1 = Klein group
}

# KNOWN commutator-subgroup free ranks (READ; finite-H_1, virtually-free groups). Each
# entry: (name, presentation, known rank). The modular group Z/2*Z/3 and others.
KNOWN_COMMUTATOR_RANK = [
    # G = Z/2 * Z/3 (modular group PSL(2,Z)): a^2=e, b^3=e. H_1=Z/6 (m=6),
    # 2 gens, 2 relators -> chi = 1-2+2 = 1. rank = 1 - 6*1 = -5?? -- the FREE-PRODUCT
    # chi is NOT the presentation chi (a^2,b^3 are not a closed-surface pres). The
    # correct chi for a free product C_p*C_q is 1/p+1/q-1 (rational Euler char). Use
    # the GROUP Euler characteristic, below, for free products of finite cyclics.
]

# KNOWN free-product commutator ranks via the RATIONAL (group) Euler characteristic:
# for G = C_{n_1} * ... * C_{n_k} (free product of finite cyclics), chi(G) =
# sum(1/n_i) - (k-1), |H_1| = prod(n_i), and [G,G] is free of rank 1 - |H_1|*chi(G).
KNOWN_FREE_PRODUCT_RANK = [
    # (name, [orders], known commutator free rank). READ values:
    #   Z/2 * Z/2 = D_inf: [G,G] = <ab> infinite cyclic = free rank 1 (textbook).
    #   Z/2 * Z/3 = PSL(2,Z) modular: [G,G] free of rank 2 (Newman/Rankin, textbook).
    #   Z/3 * Z/3 * Z/3: chi-rational gives rank 28 (cross-check of the formula).
    ("Z/2 * Z/2 (D_inf)", [2, 2], 1),
    ("Z/2 * Z/3 (modular PSL2Z)", [2, 3], 2),
    ("Z/3 * Z/3 * Z/3", [3, 3, 3], 28),
]


def free_product_commutator_rank(orders: List[int]) -> CommutatorRank:
    """The free rank of [G,G] for G = C_{n_1} * ... * C_{n_k} (free product of FINITE
    cyclic groups — virtually free, so [G,G] IS free). READ: the rational/group Euler
    characteristic chi(G) = sum(1/n_i) - (k-1); |H_1| = prod(n_i); [G,G] free of rank
    1 - |H_1|*chi(G). The COMPUTE is held rational arithmetic (the held gcd/lcm tower).
    This is the operator for the FREE-PRODUCT comprehension of the connected sum (the
    alternative gluing reading); used in VERIFY and, if the gluing comprehends to a
    free product, in the exemplar."""
    k = len(orders)
    m = 1
    for n in orders:
        m *= n
    # chi(G) * m  must be an integer: m*chi = m*(sum 1/n_i) - m*(k-1)
    #            = sum_i (m / n_i) - m*(k-1)   -- all integer.
    m_chi = sum(m // n for n in orders) - m * (k - 1)
    rank = 1 - m_chi
    out = CommutatorRank(derived=True, rank=rank,
                         h1=H1Read(free_rank=0, torsion=list(orders), order=m,
                                   finite=True),
                         chi_group=0)
    out.formula = (f"rank[G,G] = 1 - |H_1|*chi(G); |H_1| = prod{orders} = {m}, "
                   f"|H_1|*chi(G) = sum(m/n_i) - m*(k-1) = {m_chi}; rank = {rank}")
    out.ledger = [
        {"label": "G = free product of finite cyclics => virtually free => [G,G] FREE",
         "kind": "READ", "cite": "Kurosh / free products of finite groups are "
                                 "virtually free."},
        {"label": f"chi(G) = sum(1/n_i) - (k-1) (rational Euler characteristic)",
         "kind": "READ", "cite": "Wall rational Euler characteristic of a free product."},
        {"label": f"|H_1| = prod(orders) = {m} (abelianization = direct sum)",
         "kind": "DERIVED", "cite": "G^ab of a free product = direct sum of the C_{n_i}."},
        {"label": out.formula, "kind": "DERIVED",
         "cite": "1 - |H_1|*chi(G): held integer arithmetic."},
    ]
    return out


__all__ = [
    "Presentation", "H1Read", "CommutatorRank",
    "pi1_from_polygon_word", "pi1_from_relators",
    "h1_of_presentation", "commutator_free_rank", "free_product_commutator_rank",
    "operator_specs", "install", "KNOWN_PI1", "KNOWN_FREE_PRODUCT_RANK",
]
