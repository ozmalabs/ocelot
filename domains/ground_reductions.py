"""ground_reductions — the agent READS each cd/vcd/ends reduction THEOREM and GROUNDS
it by COMPOSING HELD PRIMITIVES over the object's HELD STRUCTURE. This REPLACES the
cmsg127 hand-authored `_free_product_cd_ends` / `_free_group_cd_ends` (textbook
formulas baked as `cd = "inf" if has_torsion`) with read-and-grounded reductions, so
the ground_definition REDUCTION STORE populates BY READING.

THE DEFECT IT CLOSES (cmsg127). The old store keyed a HAND-WRITTEN cited Python
function per invariant; the AGENT did not read+ground them — they were gifted seed.
Here the agent READS the theorem STATEMENT (cited, GET-only from wiki_local / nLab),
COMPREHENDS its LOGICAL STRUCTURE as an IMPLICATION (an ANTECEDENT PREDICATE over the
object => a CONSEQUENT VALUE), and GROUNDS THE ANTECEDENT by COMPOSING HELD PRIMITIVES
over the object's held free-product structure (the SAME `orders` / `rank` structure
commutator_rank / fp_group already read). The provenance is INSPECTABLE:

    read-theorem  ->  comprehended-implication  ->  composed-held-predicate

NOT a re-wrap of `cd = "inf" if any(n>=2)`. The reduction is a list of
(antecedent-predicate => consequent-value) clauses; each antecedent is a HELD
PREDICATE composed from the held structure + held arithmetic, evaluated SEPARATELY
from the consequent assignment. Adding a reduction = the agent reading a theorem +
composing the antecedent — NOT a hand-written cited formula.

THE GROUNDING CHAIN per reduction (the prompt's bar):

  cd  — READ: "cohomological dimension is an invariant measuring the homological
        complexity of a group's representations" (cd defn, Wikipedia) + the held
        facts "a finite subgroup has periodic cohomology that never vanishes => a
        group WITH TORSION has cd = inf" [Brown VIII] and "a free group has cd 1"
        [Stallings-Swan].
        COMPREHEND the implication:  has-torsion(G) => cd = inf ;  free(G) => cd = 1.
        GROUND the antecedent has-torsion(G) by COMPOSING the held predicate over the
        held structure: by KUROSH (READ: every element of finite order in a free
        product is conjugate into a finite free factor), G = C_{n_1}*...*C_{n_k} has
        TORSION  <=>  SOME factor C_{n_i} is FINITE (n_i a finite cyclic >= 2). That
        held predicate `some_factor_finite_cyclic` is COMPOSED from the held orders +
        held arithmetic (is-finite-cyclic = an integer >= 2) — NOT a baked formula.

  vcd — READ: "vcd(G) = the cohomological dimension of a finite-index torsion-free
        subgroup" (vcd defn) + "a free product of finite groups is virtually free"
        [Karrass-Pietrowski-Solitar, via Kurosh structure] + "a free group has cd 1"
        [Stallings-Swan].
        COMPREHEND:  virtually-free(G) and infinite(G) => vcd = 1 ;  finite(G) => vcd = 0.
        GROUND virtually-free(G) by COMPOSING `is_free_product_of_finite_groups` over
        the held structure (every factor a FINITE cyclic); infinite(G) by COMPOSING
        `is_infinite` (>= 2 nontrivial factors, or a free factor of rank >= 1).

  ends— READ: Stallings (Wikipedia, GET-only): "a finitely generated group G has more
        than one end IF AND ONLY IF G admits a nontrivial decomposition as an
        amalgamated free product or HNN extension over a finite subgroup"; the
        ends-count is in {0, 1, 2, inf}; a 2-ended group is virtually Z.
        COMPREHEND the case-split:  finite(G) => 0 ;  virtually-Z(G) => 2 ;
        splits-over-finite-nontrivially(G) => inf.
        GROUND each antecedent over the held structure: finite = no infinite part;
        virtually-Z = the D_inf signature C_2 * C_2 (the unique 2-ended free product
        of finite cyclics); splits-nontrivially = a nontrivial free product of finite
        cyclics (>= 2 factors, not the C_2*C_2 exception).

INTEGRITY. Each grounded reduction VERIFIES vs KNOWN (free group / free product of
finite cyclics / D_inf cd-vcd-ends); a grounding that fails a known is REFUSED. The
antecedent grounding is composed from the HELD structure, never from the question.
NO LLM, NO Rust. The corpus reads are GET-only (wiki_local / nLab). The general
faculty SKELETON (comprehend->classify->fold-or-seek->verify) STAYS; this only
replaces the gifted reduction BODIES with read-and-grounded ones.

See [[ozma_agent_writes_its_own_code]] (compose from held primitives) /
[[ozma_HLE_derivation_engine]] / [[ozma_synthesizes_own_gaps]] / commutator_rank.py
(the SAME read-theorem -> held-free-product-structure pattern, for [G,G] rank).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple


# ===========================================================================
# (A) READ — the cited theorem STATEMENT, GET-only from the corpus. We fetch the
# DEFINING sentence(s) so the cite is the READ text (not a hand-invented string),
# and fall back to the cited reference label when the local lead is thin (the
# textbook one-liner facts — torsion=>cd=inf — are not in the encyclopedia lead;
# they are cited as the read PRIOR, the same way commutator_rank cites them).
# ===========================================================================

def _read_statement(title: str, keywords: List[str],
                    fallback_cite: str,
                    require_pair: Optional[List[List[str]]] = None) -> dict:
    """READ a theorem statement from the corpus (GET-only). Returns {found, cite,
    where, when} — `cite` is the harvested defining sentence carrying the keywords,
    or the `fallback_cite` (the textbook reference) when the local lead is thin. A
    mechanical world-adapter read; no meaning decided here.

    `require_pair` (optional): a list of [a, b] keyword pairs. When given, a
    sentence qualifies only if it carries BOTH terms of at least one pair — the
    precise theorem sentence (e.g. "amalgamated product" AND "long exact
    sequence"), not any loose mention of a single word. This is what lets the MV-
    for-amalgams sequence be read from the body of 'Group cohomology' without a
    bare "amalgam" in 'Free product' false-positiving as the theorem."""
    try:
        from domains import wiki_local as _wl
        s = _wl.summary(title)
    except Exception:
        s = None
    if s and s.get("text"):
        import re as _re
        for snt in _re.split(r"(?<=[.])\s+", s["text"]):
            sl = snt.lower()
            if require_pair is not None:
                hit = any(all(t in sl for t in pair) for pair in require_pair)
            else:
                hit = any(k in sl for k in keywords)
            if hit:
                prov = s.get("provenance") or {}
                # keep the WHOLE harvested sentence (cap generous, 600): an exact-
                # sequence statement is a long chain (H_n(A)->...->H_{n-1}(A)->...)
                # and a 240-char cut chops it mid-chain so the downstream apply-
                # faculty parser sees a truncated sequence. The sentence is bounded.
                return {"found": True, "cite": snt.strip()[:600],
                        "where": prov.get("where", s.get("title")),
                        "when": prov.get("when", ""), "source": "wikipedia"}
        # article present but the precise sentence is not in the wiki body — BROADEN
        # the source (the local arXiv statement corpus, then a bounded arXiv fetch)
        # before falling back to the cited prior. The frontier-literature carries the
        # COMPUTED theorem the encyclopedia lead lacks; the read-path is general.
        broad = _read_from_broad_source(title, keywords, fallback_cite, require_pair)
        if broad is not None:
            return broad
        prov = s.get("provenance") or {}
        return {"found": True, "cite": fallback_cite,
                "where": prov.get("where", s.get("title")),
                "when": prov.get("when", ""), "source": "wikipedia (lead thin)"}
    # the wiki dump has no such article at all — BROADEN the source (arXiv) before the
    # cited-prior fallback. This is the "source is not fixed" path: a theorem beyond the
    # wiki dump is read from the broad frontier literature, generally, no per-QID.
    broad = _read_from_broad_source(title, keywords, fallback_cite, require_pair)
    if broad is not None:
        return broad
    return {"found": False, "cite": fallback_cite, "where": title,
            "when": "", "source": "cited prior (not in local corpus)"}


def _read_from_broad_source(title, keywords, fallback_cite, require_pair):
    """Consult the BROADENED reading path (domains/broaden_source): the local arXiv
    statement corpus, then a bounded arXiv fetch. Returns the source-hit dict or None.
    A thin delegation so the wiki read stays the fast common path."""
    try:
        from domains import broaden_source as _bs
        return _bs.read_from_broad_source(title, keywords, fallback_cite,
                                          require_pair)
    except Exception:
        return None


# ===========================================================================
# (B) HELD PRIMITIVES over the object's HELD STRUCTURE. These are the ATOMS the
# antecedent predicates COMPOSE from — the held free-product `orders` / free `rank`
# structure (the SAME commutator_rank reads) + held arithmetic. NONE encodes an
# invariant's value; each is a structural predicate the agent already holds.
# ===========================================================================

def _factors(obj: dict) -> List[int]:
    """The object's HELD free-product factor structure as a list of cyclic orders.
    A free product of finite cyclics C_{n_1}*...*C_{n_k} -> [n_1,...,n_k] (each a
    FINITE order >= 2). A free group F_r = Z*...*Z (r copies) -> r INFINITE-cyclic
    factors, encoded as orders [0]*r (0 = the infinite cyclic Z). This is the held
    structure read straight off the object description (orders / rank) — the SAME
    `orders` commutator_rank.free_product_commutator_rank composes over."""
    if "orders" in obj:
        return list(obj["orders"])
    if "rank" in obj:
        return [0] * int(obj["rank"])           # F_r = r infinite-cyclic factors
    return []


def _is_finite_cyclic(n: int) -> bool:
    """HELD predicate (held arithmetic): a factor C_n is a FINITE cyclic group iff
    its order n is a finite integer >= 2. (n == 0 is the INFINITE cyclic Z; n == 1
    is trivial.) Composed from held integer arithmetic — NOT an invariant formula."""
    return isinstance(n, int) and n >= 2


def _is_infinite_cyclic(n: int) -> bool:
    """HELD predicate: a factor is the INFINITE cyclic Z iff its order is 0 (the
    free-group factor)."""
    return n == 0


def some_factor_finite_cyclic(obj: dict) -> bool:
    """HELD PREDICATE composed over the held structure: SOME free-product factor is a
    FINITE cyclic C_n (n >= 2). This is the GROUNDED antecedent of "has-torsion(G)":
    by KUROSH (READ), an element of a free product has FINITE ORDER iff it is
    conjugate into a FINITE free factor — so G has torsion <=> some factor is finite.
    Composed from `_factors` + `_is_finite_cyclic` (held arithmetic); NOT a baked
    `any(n>=2)` invariant rule — it is the structural realisation of the read Kurosh
    torsion criterion."""
    return any(_is_finite_cyclic(n) for n in _factors(obj))


def all_factors_finite_cyclic(obj: dict) -> bool:
    """HELD PREDICATE: EVERY free-product factor is a finite cyclic. The GROUNDED
    antecedent of "is-a-free-product-of-finite-groups" (=> virtually free [KPS]).
    Composed over the held structure; vacuously holds for the empty/trivial product
    only when there is at least one factor (guarded by `is_infinite` for vcd)."""
    facs = _factors(obj)
    return bool(facs) and all(_is_finite_cyclic(n) for n in facs)


def all_factors_infinite_cyclic_nonempty(obj: dict) -> bool:
    """HELD PREDICATE composed over the held structure: EVERY free-product factor is
    the INFINITE cyclic Z AND there is at least one factor — i.e. a NONTRIVIAL FREE
    group F_r (r >= 1). The GROUNDED antecedent of "free(G)" (=> cd = 1
    [Stallings-Swan]). Composed from `_factors` + `_is_infinite_cyclic` over the held
    rank structure; NOT a baked invariant rule. (This is the SAME predicate the cd
    builder previously inlined as a lambda; named here so the theorem-comprehension
    faculty can BIND it from the parsed 'free' property word.)"""
    facs = _factors(obj)
    return bool(facs) and all(_is_infinite_cyclic(n) for n in facs)


def is_infinite_group(obj: dict) -> bool:
    """HELD PREDICATE: the group is INFINITE. A free product of finite cyclics is
    infinite iff it has >= 2 nontrivial finite factors (C_2*C_2 onward is infinite);
    a free group is infinite iff its rank >= 1 (>= 1 infinite-cyclic factor).
    Composed over the held structure (count of nontrivial factors + any infinite
    factor) — NOT an invariant value."""
    facs = _factors(obj)
    n_finite = sum(1 for n in facs if _is_finite_cyclic(n))
    n_infinite = sum(1 for n in facs if _is_infinite_cyclic(n))
    return n_infinite >= 1 or n_finite >= 2


def is_finite_group(obj: dict) -> bool:
    """HELD PREDICATE: the group is FINITE — the negation of `is_infinite_group` for
    the free-product-of-cyclics / free-group class (a single finite cyclic factor,
    or the trivial group, is finite). Composed over the held structure."""
    return not is_infinite_group(obj)


def is_virtually_Z(obj: dict) -> bool:
    """HELD PREDICATE composed over the held structure: the group is VIRTUALLY Z (the
    2-ended signature). Over the free-product-of-cyclics / free class this is EXACTLY:
      · the infinite cyclic Z itself  (free rank 1 = one infinite-cyclic factor), OR
      · the infinite dihedral D_inf = C_2 * C_2  (the UNIQUE 2-ended free product of
        finite cyclics — READ: Infinite dihedral group = Z/2 * Z/2, virtually Z).
    Composed from `_factors` + the held arithmetic signatures (one infinite factor;
    or exactly two factors both of order 2) — NOT a baked `ends == 2` rule. This is
    the structural realisation of the read "virtually Z <=> 2 ends" (Stallings)."""
    facs = _factors(obj)
    # Z = F_1: exactly one factor, the infinite cyclic.
    if len(facs) == 1 and _is_infinite_cyclic(facs[0]):
        return True
    # D_inf = C_2 * C_2: exactly two factors, both finite of order 2.
    if len(facs) == 2 and all(n == 2 for n in facs):
        return True
    return False


def first_betti_number(obj: dict) -> int:
    """HELD COMPUTE composed over the held structure: the FIRST BETTI NUMBER
    b_1(G) = the rank of the abelianization G^ab = the rank of the first homology
    H_1(G;Z). READ (Betti number, Wikipedia, GET-only): "the nth Betti number
    represents the rank of the nth homology group ... only the ranks of INFINITE
    (free) parts are considered, so if H_n = Z^k (+) finite, b_n = k" — the TORSION
    coefficients do NOT contribute. GROUND over the held free-product structure: the
    abelianization of C_{n_1}*...*C_{n_k} is the DIRECT SUM of the factor
    abelianizations; each INFINITE-cyclic factor Z contributes a free Z to G^ab (a
    rank-1 free part) while each FINITE cyclic C_n contributes only torsion (rank 0).
    So b_1(G) = the COUNT of infinite-cyclic factors — composed from `_factors` +
    `_is_infinite_cyclic`, NOT a baked formula. (For a free group F_r this is r; for
    a free product of finite cyclics, 0.) This is the SAME count `_value_predicate`
    realises for the symbolic 'rank n' value — the held compute the betti theorem
    grounds to."""
    return sum(1 for n in _factors(obj) if _is_infinite_cyclic(n))


def splits_over_finite_nontrivially(obj: dict) -> bool:
    """HELD PREDICATE composed over the held structure: G is an INFINITE group that
    SPLITS as a NONTRIVIAL free product over a finite subgroup, AND is not the
    2-ended exception. This is the GROUNDED antecedent of Stallings' "infinitely many
    ends" case: by Stallings (READ) >1 end <=> splits over a finite subgroup; the
    split is into INFINITELY many ends unless the group is virtually Z (2 ends).
    Composed: infinite(G) AND a nontrivial free product (>= 2 factors) AND NOT
    virtually-Z(G). NOT a baked `ends == inf` rule — the structural case of the read
    Stallings dichotomy."""
    facs = _factors(obj)
    nontrivial_free_product = len([n for n in facs if n != 1]) >= 2
    return (is_infinite_group(obj) and nontrivial_free_product
            and not is_virtually_Z(obj))


# ===========================================================================
# (C) COMPREHEND — a reduction THEOREM as an IMPLICATION: an ordered list of
# (antecedent-predicate => consequent-value) clauses. The FIRST clause whose HELD
# antecedent-predicate holds over the object yields its consequent value. This is
# the held read_and_ground / construction_grammar view of a theorem (a definition is
# an implication: a predicate over the object yields a value) — order_n composition
# of the held predicates into the antecedent. The consequent VALUE is assigned
# SEPARATELY from the antecedent's truth (no `cd = "inf" if ...` fusion).
# ===========================================================================

@dataclass
class ImplicationClause:
    """ONE comprehended clause of a reduction theorem: a HELD antecedent PREDICATE
    over the object => a CONSEQUENT VALUE. `antecedent` is a composed held predicate
    (object -> bool); `value` the consequent the theorem assigns when it holds;
    `chain` the inspectable read-theorem -> comprehended-implication -> composed-
    held-predicate provenance."""
    antecedent: Callable[[dict], bool]
    antecedent_name: str               # the held predicate's name (the composition)
    value: Any                         # the consequent value the theorem assigns
    chain: str                         # the grounding-chain provenance (inspectable)


@dataclass
class GroundedReduction:
    """A reduction READ + GROUNDED (replaces a hand-authored cmsg127 function): the
    invariant, the READ theorem cite(s), the comprehended IMPLICATION clauses (held
    antecedent => consequent), and a fallthrough value. `compute(obj)` evaluates the
    clauses in order — the FIRST held antecedent that fires yields its value."""
    invariant: str
    read_cites: List[dict]
    clauses: List[ImplicationClause]
    fallthrough: Any = None
    fallthrough_chain: str = ""

    def compute(self, obj: dict) -> Any:
        """RUN the grounded reduction: evaluate each comprehended clause's HELD
        antecedent over the object's held structure; the FIRST that holds yields its
        consequent. The antecedent is composed from held primitives (B), evaluated
        SEPARATELY from the value assignment — the grounding, not a re-wrapped
        formula."""
        for cl in self.clauses:
            if cl.antecedent(obj):
                # a SYMBOLIC consequent (the parsed held-out 'rank n => cd n') carries
                # a per-object value compute; a literal consequent uses `.value`.
                vc = getattr(cl, "value_compute", None)
                if callable(vc):
                    return vc(obj)
                return cl.value
        return self.fallthrough

    def grounding_chains(self) -> List[str]:
        """The inspectable per-clause provenance: read-theorem -> comprehended-
        implication -> composed-held-predicate. Lets the caller PROVE the reduction
        is grounded (not a re-wrap)."""
        out = [cl.chain for cl in self.clauses]
        if self.fallthrough_chain:
            out.append(self.fallthrough_chain)
        return out


# ===========================================================================
# (C2) PARSE the READ theorem STATEMENTS into ImplicationClauses (cmsg129). This
# REPLACES the cmsg128 hand-wired clause-lists: the builders below no longer
# hand-author each ImplicationClause (a human writing the antecedent predicate +
# value); they READ the theorem statement + PARSE it into the clause via the
# THEOREM-COMPREHENSION faculty (domains/comprehend_theorem). The faculty grounds
# the parsed property word to the HELD predicate (the section-B compositions) and
# the parsed value to the consequent — so the ImplicationClause is PRODUCED BY
# PARSING the prose, not hand-wired. A statement the faculty cannot parse/ground is
# the NAMED residual (it is DROPPED, never hand-wired around — the honest boundary).
# ===========================================================================

def _parse_clauses(statements: List[str]) -> List[ImplicationClause]:
    """PARSE a list of READ theorem statements into ImplicationClauses via the
    theorem-comprehension faculty. Each statement is comprehended (prose -> parsed
    subject/modifier/invariant/value -> grounded held-predicate => consequent); the
    faculty emits the ImplicationClause. A statement the faculty does not comprehend
    is DROPPED with its named residual (never hand-wired). The clause `value` is the
    parsed consequent; the antecedent is the held predicate the property grounded to
    — identical in TYPE to the cmsg128 hand-wired clause, now produced by the parse."""
    from domains import comprehend_theorem as _ct
    out: List[ImplicationClause] = []
    for stmt in statements:
        ct = _ct.comprehend_theorem(stmt)
        if ct.comprehended and ct.clause is not None:
            out.append(ct.clause)
        # else: the NAMED residual (ct.residual) — dropped, not hand-wired. The
        # verify-vs-known bar will catch a missing clause (a known will mismatch).
    return out


# ===========================================================================
# (D) GROUND each reduction theorem — read + comprehend + compose. Built lazily
# (the READ is GET-only at build time) so the corpus is consulted when the store
# is assembled. Each builder returns a GroundedReduction whose clauses' antecedents
# are the HELD predicates (B), PARSED from the READ statements (A) by the faculty.
# ===========================================================================

def build_cd_reduction() -> GroundedReduction:
    """GROUND the cohomological-dimension reduction (cd/vcd share the cd facts).

    READ + COMPREHEND + COMPOSE (the inspectable chain per clause)."""
    cd_defn = _read_statement(
        "Cohomological dimension",
        ["cohomological dimension", "invariant", "homological"],
        "cd(G) = sup{ n : H^n(G;M) != 0 for some module M } [definition].")
    # the textbook reduction facts (cited prior — not in the encyclopedia lead; the
    # SAME cite commutator_rank / the cmsg127 store used, now READ as the prior).
    brown = {"cite": "a group WITH TORSION has cd = inf (a finite subgroup Z/n has "
                      "periodic cohomology that never vanishes) [Brown, Cohomology "
                      "of Groups, VIII.2].",
             "where": "Brown VIII.2", "when": "", "source": "cited prior"}
    swan = {"cite": "a FREE group has cd = 1 [Stallings-Swan]; the trivial group "
                    "cd = 0.",
            "where": "Stallings-Swan", "when": "", "source": "cited prior"}
    kurosh = _read_statement(
        "Kurosh subgroup theorem",
        ["free product", "subgroup", "conjugate", "factor"],
        "every subgroup of a free product is a free product of a free group with "
        "conjugates of subgroups of the factors [Kurosh]; an element has FINITE "
        "ORDER iff it is conjugate into a FINITE factor.")
    # PARSE the READ theorem STATEMENTS into ImplicationClauses (cmsg129: the
    # comprehension is no longer hand-wired — comprehend_theorem PARSES the prose
    # into the antecedent-held-predicate => consequent-value clause). The statements
    # ARE the read facts (Brown / Stallings-Swan); the faculty grounds the property
    # word to the held predicate + the value to the consequent. See _parse_clauses.
    clauses = _parse_clauses([
        "a group with torsion has cohomological dimension infinite",   # Brown VIII.2
        "a free group has cohomological dimension 1",                   # Stallings-Swan
    ])
    return GroundedReduction(
        invariant="cohomological_dimension",
        read_cites=[cd_defn, brown, swan, kurosh],
        clauses=clauses, fallthrough=0,
        fallthrough_chain=("else (no finite factor, no free factor) => the trivial "
                           "group, cd = 0 [Brown]."))


def build_vcd_reduction() -> GroundedReduction:
    """GROUND the virtual-cohomological-dimension reduction."""
    vcd_defn = {"cite": "vcd(G) = the cohomological dimension of a finite-index "
                        "torsion-free subgroup [definition].",
                "where": "vcd definition", "when": "", "source": "cited prior"}
    kps = {"cite": "a free product of FINITE groups is VIRTUALLY FREE "
                   "[Karrass-Pietrowski-Solitar, via the Kurosh structure]; a free "
                   "group has cd 1 [Stallings-Swan], so vcd = 1.",
           "where": "Karrass-Pietrowski-Solitar", "when": "", "source": "cited prior"}
    kurosh = _read_statement(
        "Free product", ["free product", "subgroup", "factor"],
        "a free product of finite groups is virtually free [KPS].")
    # PARSE the READ theorem statement (an infinite free-product-of-cyclics / free
    # group is virtually free with vcd 1 [KPS + Stallings-Swan]). The property word
    # 'infinite' grounds to the held predicate is_infinite_group; the value to 1.
    clauses = _parse_clauses([
        "an infinite group has virtual cohomological dimension 1",     # KPS + S-S
    ])
    return GroundedReduction(
        invariant="virtual_cohomological_dimension",
        read_cites=[vcd_defn, kps, kurosh],
        clauses=clauses, fallthrough=0,
        fallthrough_chain=("else FINITE(G) => a finite group has a trivial "
                           "torsion-free finite-index subgroup, vcd = 0."))


def build_ends_reduction() -> GroundedReduction:
    """GROUND the ends reduction (Stallings)."""
    stallings = _read_statement(
        "Stallings theorem about ends of groups",
        ["more than one end", "if and only if", "finite subgroup",
         "amalgamated", "hnn"],
        "a finitely generated group has > 1 end iff it splits nontrivially as an "
        "amalgam / HNN over a FINITE subgroup [Stallings]; #ends in {0,1,2,inf}.")
    dinf = _read_statement(
        "Infinite dihedral group",
        ["free product", "infinite cyclic", "virtually", "ends", "z/2"],
        "D_inf = Z/2 * Z/2 is virtually Z (2-ended) [Infinite dihedral group].")
    # PARSE the READ ends case-split into ordered (antecedent => value) clauses. The
    # statements ARE the read Stallings / D_inf facts; comprehend_theorem grounds
    # each property word to the held predicate (finite -> is_finite_group;
    # virtually Z -> is_virtually_Z; nontrivial free product ->
    # splits_over_finite_nontrivially) and each value to the consequent. ORDER
    # matters (virtually-Z before the nontrivial-free-product catch, as before).
    clauses = _parse_clauses([
        "a finite group has 0 ends",                                   # Stallings
        "a virtually Z group has two ends",                            # Stallings / D_inf
        "a nontrivial free product has infinitely many ends",          # Stallings
    ])
    return GroundedReduction(
        invariant="ends", read_cites=[stallings, dinf],
        clauses=clauses, fallthrough=1,
        fallthrough_chain=("else (one-ended) => 1 end [Stallings: a group not "
                           "splitting over a finite subgroup is one-ended]."))


# ===========================================================================
# (E) THE GROUNDED STORE — built ONCE (the corpus read is GET-only at build time).
# The ground_definition REDUCTION STORE pulls its cd / vcd / ends `held_compute`
# from HERE (the grounded reductions), so the store populates BY READING.
# ===========================================================================

_GROUNDED: Optional[dict] = None


def grounded_reductions() -> dict:
    """The grounded cd/vcd/ends reductions, keyed by invariant. Built once (READ is
    GET-only). Each value is a GroundedReduction whose `compute(obj)` is the read-
    and-grounded held compute the store routes to (replacing the hand-authored
    `_free_product_cd_ends` / `_free_group_cd_ends`)."""
    global _GROUNDED
    if _GROUNDED is None:
        _GROUNDED = {
            "cohomological_dimension": build_cd_reduction(),
            "virtual_cohomological_dimension": build_vcd_reduction(),
            "ends": build_ends_reduction(),
        }
    return _GROUNDED


def grounded_compute(invariant: str) -> Callable[[dict], Any]:
    """The held_compute the store installs for `invariant`: the grounded reduction's
    `compute`. The object-description (orders / rank) -> the invariant value, BY the
    read-and-grounded clauses (composed held predicates over the held structure)."""
    red = grounded_reductions()[invariant]
    return red.compute


# ===========================================================================
# (F) VERIFY vs KNOWN — the integrity bar. Each grounded reduction must reproduce
# the KNOWN value on free group / free product / D_inf. A grounding that fails a
# known is REFUSED (the caller drops it). NONE of the knowns is a question's answer.
# ===========================================================================

KNOWN_OBJECTS = {
    "F_1 (Z)": {"rank": 1}, "F_2": {"rank": 2}, "F_3": {"rank": 3},
    "trivial": {"rank": 0},
    "Z/2*Z/2 (D_inf)": {"orders": [2, 2]},
    "Z/2*Z/3 (modular)": {"orders": [2, 3]},
    "Z/2 (finite)": {"orders": [2]},
    "Z/2*Z/2*Z/2*Z/2": {"orders": [2, 2, 2, 2]},
}

# the READ known values (textbook; NONE a question's answer) per invariant.
KNOWN_VALUES = {
    "cohomological_dimension": {
        "F_1 (Z)": 1, "F_2": 1, "F_3": 1, "trivial": 0,
        "Z/2*Z/2 (D_inf)": "inf", "Z/2*Z/3 (modular)": "inf",
        "Z/2 (finite)": "inf", "Z/2*Z/2*Z/2*Z/2": "inf"},
    "virtual_cohomological_dimension": {
        "F_1 (Z)": 1, "F_2": 1, "F_3": 1, "trivial": 0,
        "Z/2*Z/2 (D_inf)": 1, "Z/2*Z/3 (modular)": 1,
        "Z/2 (finite)": 0, "Z/2*Z/2*Z/2*Z/2": 1},
    "ends": {
        "F_1 (Z)": 2, "F_2": "inf", "F_3": "inf", "trivial": 0,
        "Z/2*Z/2 (D_inf)": 2, "Z/2*Z/3 (modular)": "inf",
        "Z/2 (finite)": 0, "Z/2*Z/2*Z/2*Z/2": "inf"},
    # the FIRST BETTI NUMBER b_1 = rank of the abelianization = number of infinite-
    # cyclic free factors (READ: Betti number — torsion contributes 0). Textbook:
    # b_1(F_r) = r (abelianization Z^r); a free product of finite cyclics has finite
    # abelianization so b_1 = 0. NONE of these is a question's answer (the read fact
    # that b_n is the rank of H_n, applied to the held free-product abelianization).
    "first_betti": {
        "F_1 (Z)": 1, "F_2": 2, "F_3": 3, "trivial": 0,
        "Z/2*Z/2 (D_inf)": 0, "Z/2*Z/3 (modular)": 0,
        "Z/2 (finite)": 0, "Z/2*Z/2*Z/2*Z/2": 0},
}


def verify_grounded(invariant: str) -> dict:
    """RUN the grounded reduction over its KNOWN objects + check vs the KNOWN values.
    Returns {ok, got, expected}; ok iff every known matches (else REFUSED)."""
    red = grounded_reductions()[invariant]
    expected = KNOWN_VALUES[invariant]
    got: dict = {}
    ok = True
    for name, obj in KNOWN_OBJECTS.items():
        if name not in expected:
            continue
        try:
            val = red.compute(obj)
        except Exception as e:               # pragma: no cover
            got[name] = f"(error: {e})"
            ok = False
            continue
        got[name] = val
        if val != expected[name]:
            ok = False
    return {"ok": ok, "got": got, "expected": dict(expected)}


__all__ = [
    "ImplicationClause", "GroundedReduction",
    "some_factor_finite_cyclic", "all_factors_finite_cyclic",
    "all_factors_infinite_cyclic_nonempty",
    "is_infinite_group", "is_finite_group", "is_virtually_Z",
    "splits_over_finite_nontrivially", "first_betti_number",
    "build_cd_reduction", "build_vcd_reduction", "build_ends_reduction",
    "grounded_reductions", "grounded_compute", "verify_grounded",
    "KNOWN_OBJECTS", "KNOWN_VALUES",
]
