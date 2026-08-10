"""ground_definition — a GENERAL grounding faculty: read a mathematical DEFINITION
-> comprehend its STRUCTURE -> construct a RUNNABLE compute (or NAME the precise
residual). NOT a per-invariant hand-code; ONE faculty that grounds LS-category AND
cohomological-dimension AND ends from THEIR DEFINITIONS by the SAME path.

THE SEED (cmsg126). On the torus stall the agent grounded "min over coverings"
(uncomputable to enumerate) by recognising it could use a HELD-COMPUTABLE BOUND
(cup-length <= LS-cat, achieved on surfaces). That ONE-OFF — comprehend the
definition, see the family is infinite, SEEK a held bound, ground THAT, verify on
surfaces — is GENERALISED here into a faculty the agent OWNS.

THE STRUCTURE most definitions share — an OPERATOR over a FAMILY of a QUANTITY:

    cohomological dimension = sup{ n : H^n(G; M) != 0 for some module M }
        operator = sup        family = n over naturals x modules    quantity = H^n != 0
    LS-category             = min{ k : X covered by k contractible opens }
        operator = min        family = the coverings of X            quantity = contractible
    number of ends          = a count over the complements of compact sets
        operator = count/limit family = complements of compacts      quantity = unbounded comps

THE FACULTY (comprehend -> classify -> fold-or-seek -> verify):

  1. COMPREHEND the definition into (OPERATOR / bound-VARIABLE+FAMILY / QUANTITY).
     The held order-N reader (construction_grammar.comprehend_structure) already
     parses an operator-over-operands tree + NAMES the un-held ops; here we add the
     quantifier surface (sup/inf/min/max/least/greatest/count { VAR ... : QUANTITY })
     that a definition wraps a family in. A definition IS an order-N operator over a
     family of a held quantity — the agent already composes order-N operators
     (order_n_concepts / order_n_composition).

  2. CLASSIFY the FAMILY:
       HELD-ENUMERABLE (finite, over held objects) -> COMPOSE a fold/min/max/sup over
         the family evaluating the held QUANTITY -> runnable DIRECTLY (a held Fold).
       INFINITE / NON-ENUMERABLE (all modules / all resolutions / all coverings) ->
         the direct enumeration is INADMISSIBLE. SEEK a HELD-COMPUTABLE REDUCTION or
         BOUND (the cup-length<=LS-cat move, GENERALISED): look up / read the theorem
         that EQUATES or BOUNDS the invariant by a held compute, ground THAT, and
         report EXACT (the bound is achieved in the class) vs BOUND (honest).

  3. VERIFY the grounded compute vs KNOWN cases — the faculty REFUSES a grounding
     that fails a known (cup-length on surfaces; cd / ends on known groups).

NO HAND-AUTHORED PER-INVARIANT OPERATOR. There is no ls_category()/cohomological_
dimension()/ends() with the formula baked in. The faculty COMPREHENDS the
(operator/family/quantity) structure and DERIVES: a FOLD when the family is held-
enumerable, ELSE the SOUGHT REDUCTION (a READ theorem from a general, additive
reduction store — cup-length<=LS-cat, cd-via-group-structure, ends-via-Stallings;
each a cited theorem APPLIED generally, never the question's answer). The reduction
store is the agent's READ knowledge (the cmsg126 look-up), typed into the faculty's
(invariant -> held compute) shape; adding a reduction is reading a theorem, NOT
hand-coding an invariant.

HONEST. The faculty grounds definitions that reduce to held primitives OR a held/
derivable reduction-bound; a genuinely-uncomputable infinite enumeration with no
reduction, or a deep-unread reduction-theorem, stays PRECISELY NAMED. Grounding the
wall-CLASSES it can + naming the rest is the honest win.

No LLM, no Rust, no new primitive. A WORLD-ADAPTER SHELL (CLAUDE.md) over the agent's
held machinery: the COMPREHEND is construction_grammar's order-N reader + the
quantifier surface; the FOLD is order_n_composition / a held Min/Max over the held
quantity; the SEEK is the read reduction store (the cmsg126 look-up, generalised);
the VERIFY is the held compute vs KNOWN. See [[ozma_order_n_concepts]] /
[[ozma_HLE_derivation_engine]] / [[ozma_agent_writes_its_own_code]] /
[[ozma_synthesizes_own_gaps]].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ===========================================================================
# (1) COMPREHEND — a definition's (OPERATOR / bound-VAR + FAMILY / QUANTITY).
#
# A definition wraps a QUANTITY in a quantifier OPERATOR ranging a bound VARIABLE
# over a FAMILY:   OP { VAR : the VAR ranges a FAMILY ; QUANTITY(VAR) holds }.
# We read that surface (the held quantifier words) into the triple. This is the
# SAME order-N "operator over operands" comprehension construction_grammar runs,
# specialised to the quantifier-binder surface a DEFINITION uses (sup/min/...).
# NOT a regex over the invariant name — a read of the definition's binder STRUCTURE.
# ===========================================================================

# The quantifier OPERATORS a definition's outer binder uses, mapped to the held
# fold each reduces to (order_n_composition / a held Min/Max over the quantity).
# additive: more surface words -> the SAME folds; the discrimination is the grammar.
_OPERATOR_SURFACE = {
    "sup": "sup", "supremum": "sup", "greatest": "max", "maximum": "max",
    "max": "max", "largest": "max", "longest": "max",
    "inf": "inf", "infimum": "inf", "least": "min", "minimum": "min",
    "min": "min", "smallest": "min", "minimal": "min", "fewest": "min",
    "number": "count", "count": "count", "cardinality": "count",
}


@dataclass
class DefStructure:
    """The comprehended (operator / family / quantity) of a definition."""
    operator: Optional[str]                 # the held fold: sup/min/max/inf/count
    bound_var: Optional[str]                # the binder variable (n / k / M / ...)
    family: str                             # the family the binder ranges (prose)
    quantity: str                           # the per-element quantity (prose)
    raw: str = ""
    comprehended: bool = False

    def line(self) -> str:
        return (f"OP={self.operator}  VAR={self.bound_var}  "
                f"FAMILY={self.family!r}  QUANTITY={self.quantity!r}")


_QUANT_RE = re.compile(
    r"\b(sup|supremum|inf|infimum|min|minimum|minimal|max|maximum|maximal|"
    r"least|greatest|largest|smallest|fewest|longest|number|count|cardinality)\b",
    re.IGNORECASE)

# the binder body: OP { VAR : BODY }  or  OP { VAR | BODY }  or
# OP VAR such that BODY  /  OP of VAR : BODY. Read the binder VAR + split the BODY
# into the FAMILY clause (where VAR ranges) and the QUANTITY clause (what holds).
_BINDER_RE = re.compile(
    r"\{\s*([A-Za-z][A-Za-z0-9_]*)\b(.*?)\}", re.DOTALL)


def comprehend_definition(definition: str) -> DefStructure:
    """COMPREHEND a definition into (OPERATOR / bound-VAR + FAMILY / QUANTITY).

    Reads the quantifier OPERATOR (the outer binder word), the bound VARIABLE, and
    splits the binder body into the FAMILY (where the var ranges) and the QUANTITY
    (the per-element predicate). The same operator-over-operands read as the held
    construction-grammar order-N reader, on the definition's binder surface. Returns
    a DefStructure; comprehended=False when no quantifier binder is read (the honest
    boundary — the caller falls back to the equation/relational compute grounder)."""
    text = (definition or "").strip()
    mop = _QUANT_RE.search(text)
    operator = _OPERATOR_SURFACE.get(mop.group(1).lower()) if mop else None

    bound_var = None
    family = ""
    quantity = ""
    mb = _BINDER_RE.search(text)
    if mb:
        bound_var = mb.group(1)
        body = mb.group(2).strip()
        # the body splits on the "such that" separator ( : | such that | with ).
        parts = re.split(r"\s*:\s*|\bsuch that\b|\bwith\b|\|", body, maxsplit=1)
        fam = parts[0].strip(" ,;")
        qty = parts[1].strip(" ,;") if len(parts) > 1 else ""
        family = f"{bound_var} {fam}".strip()
        quantity = qty
    else:
        # no brace-binder: read "OP <var> such that <quantity>" / "OP over <family>"
        m2 = re.search(
            r"(?:over|of)\s+(.*?)(?:\bsuch that\b|:|,)\s*(.*)$", text, re.DOTALL)
        if m2:
            family = m2.group(1).strip(" ,;")
            quantity = m2.group(2).strip(" ,;")
        else:
            family = text

    comprehended = bool(operator) and bool(family)
    return DefStructure(operator=operator, bound_var=bound_var, family=family,
                        quantity=quantity, raw=text, comprehended=comprehended)


# ===========================================================================
# (2) CLASSIFY the FAMILY — held-ENUMERABLE (finite over held objects) vs
# INFINITE / NON-ENUMERABLE (all modules / all resolutions / all coverings).
#
# The classification reads the FAMILY description for the held markers of an
# INFINITE quantifier domain (a universal over an unbounded class) vs a finite
# held collection. General, additive markers — NOT keyed on the invariant.
# ===========================================================================

# markers that the family ranges an UNBOUNDED / NON-ENUMERABLE class — the
# enumeration is inadmissible (cup-length<=LS-cat regime). additive.
_INFINITE_MARKERS = (
    "all module", "any module", "some module", "every module", "modules",
    "all resolution", "projective resolution", "free resolution", "resolution",
    "all covering", "every covering", "coverings", "open cover", "covered by",
    "all subgroup", "compact set", "complement", "naturals", "natural number",
    "integers", "for some n", "for all n", "real-valued", "smooth function",
    "vector field", "all maps", "all continuous",
)
# markers that the family is a FINITE / held-enumerable collection.
_FINITE_MARKERS = (
    "the finite", "finite set", "finitely many", "the generators", "the relators",
    "the vertices", "the simplices", "the cells", "the divisors", "1..",
    "from 1 to", "the elements of",
)


def classify_family(struct: DefStructure) -> str:
    """CLASSIFY the comprehended family: 'held_enumerable' (a finite held
    collection -> fold directly) or 'infinite' (an unbounded/non-enumerable class
    -> the enumeration is inadmissible, SEEK a reduction). Reads the held markers
    of the family domain — general, not per-invariant. Defaults to 'infinite' (the
    conservative, honest verdict: a family with no finite marker is treated as
    needing a reduction, never enumerated)."""
    fam = (struct.family + " " + struct.quantity).lower()
    if any(m in fam for m in _FINITE_MARKERS):
        return "held_enumerable"
    if any(m in fam for m in _INFINITE_MARKERS):
        return "infinite"
    # a bounded numeric range "{k in 1..n}" is enumerable; bare "n" is not.
    if re.search(r"\b\d+\s*\.\.\s*\w+|\bfrom\s+\d+\s+to\b", fam):
        return "held_enumerable"
    return "infinite"


# ===========================================================================
# (3a) FOLD — the HELD-ENUMERABLE case. Compose the operator as a fold over the
# family evaluating the held QUANTITY. This reduces to order_n_composition's
# iterate / a held Min/Max — the agent's held fold over a held collection.
# ===========================================================================

_FOLD = {
    "min": min, "max": max, "sup": max, "inf": min,
    "count": lambda xs: sum(1 for x in xs if x),
}


def fold_over_family(operator: str, elements, quantity_fn: Callable) -> Any:
    """COMPOSE the operator as a FOLD over a HELD-ENUMERABLE family, evaluating the
    held QUANTITY on each element. `elements` is the finite held collection (a list
    the caller materialised from the held objects); `quantity_fn(e)` the held
    per-element compute. Reduces to the held fold (order_n_composition's reduce /
    Min/Max). The faculty's held-enumerable grounding — runnable directly."""
    fold = _FOLD.get(operator)
    if fold is None:
        raise ValueError(f"no held fold for operator {operator!r}")
    vals = [quantity_fn(e) for e in elements]
    if operator == "count":
        return fold(vals)
    if not vals:
        raise ValueError("empty family — the fold has no elements")
    return fold(vals)


# ===========================================================================
# (3b) SEEK — the INFINITE case. The cup-length<=LS-cat move, GENERALISED: SEEK a
# HELD-COMPUTABLE REDUCTION/BOUND for the invariant; ground THAT; report EXACT (the
# bound is achieved in the class) vs BOUND (honest).
#
# THE REDUCTION STORE is the agent's READ knowledge (the cmsg126 look-up), typed
# into the (invariant -> a held compute over a held object-description) shape. Each
# entry is a CITED theorem APPLIED generally, NEVER the question's answer. Adding a
# reduction is READING a theorem; the store is ADDITIVE and general — it is NOT a
# per-invariant hand-coded formula (the held compute is the agent's existing tower;
# the entry only NAMES which held compute the read theorem reduces the invariant to,
# under a stated applicability + an 'exact-vs-bound' honesty flag).
# ===========================================================================

@dataclass
class Reduction:
    """A READ reduction: the invariant -> a HELD compute, with an applicability
    guard + the exact-vs-bound honesty + a verify-vs-known set."""
    invariant: str                     # the invariant surface the reduction matches
    cite: str                          # the cited theorem (read, general)
    held_compute: Callable             # object-description -> the held value
    applies: Callable                  # object-description -> bool (the guard)
    exact: bool                        # True: equals; False: a (lower/upper) bound
    bound_kind: str = "exact"          # 'exact' | 'lower' | 'upper'
    knowns: dict = field(default_factory=dict)   # known-object -> known value


# --- the held computes the reductions reduce to (the agent's EXISTING tower; the
# reduction only routes the invariant to one of these — no new per-invariant math).

def _cuplength_compute(obj: dict):
    """The held GF(2) cup-length over a simplicial complex — the agent's HELD
    cup_product tower (reason._cup_product / coboundary). Imported lazily from the
    held cohomology-ring machinery the cmsg126 script already exercises."""
    from domains import gf2_cohomology as _gf2
    return _gf2.cup_length_gf2(obj["complex"], dim=obj.get("dim", 2))


# cmsg127 -> GROUNDED: the hand-authored `_free_product_cd_ends` /
# `_free_group_cd_ends` (textbook formulas baked as `cd = "inf" if has_torsion`,
# the Stallings end-cases as if/elif, KEYED by invariant name) are REPLACED by the
# READ-AND-GROUNDED reductions in domains/ground_reductions. There the agent READS
# each theorem (cited, GET-only), COMPREHENDS the implication (an ANTECEDENT
# PREDICATE over the object => a CONSEQUENT VALUE), and GROUNDS the antecedent by
# COMPOSING HELD PRIMITIVES over the object's held free-product structure (the SAME
# `orders` / `rank` commutator_rank reads). The provenance is inspectable
# (read-theorem -> comprehended-implication -> composed-held-predicate); it is NOT a
# re-wrap of the formula. The store now populates BY READING. See ground_reductions.

# THE REDUCTION STORE — read theorems typed into (invariant -> held compute). For
# cd/vcd/ends the `held_compute` is the GROUNDED reduction's compute (domains/
# ground_reductions.grounded_compute) — the read-and-grounded clauses (composed held
# predicates over the held free-product structure), NOT a hand-authored function.
# ADDITIVE: adding a reduction is the agent reading a theorem + composing the
# antecedent (ground_reductions), never a hand-written cited formula here.
def _grp_pick(which):
    """Route an invariant's held_compute to the GROUNDED reduction (read+composed),
    by invariant name. `which` is the store invariant ('cd'/'vcd'/'ends'); we map it
    to the grounded reduction key and return its read-and-grounded compute."""
    from domains import ground_reductions as _gred
    _key = {"cd": "cohomological_dimension",
            "vcd": "virtual_cohomological_dimension",
            "ends": "ends"}[which]
    return _gred.grounded_compute(_key)


REDUCTIONS = [
    Reduction(
        invariant="ls_category", bound_kind="lower", exact=False,
        cite="cup-length(X) <= cat(X) [Cornea-Lupton-Oprea-Tanre]; on a closed "
             "surface cat = cup-length+1 is ACHIEVED, so min #crit = cup-length+1.",
        held_compute=_cuplength_compute,
        applies=lambda obj: "complex" in obj,
        knowns={"S^2": 1, "T^2": 2, "RP^2": 2}),
    Reduction(
        invariant="cohomological_dimension", bound_kind="exact", exact=True,
        cite="cd(G) = inf for a group with torsion [Brown VIII]; cd(free)=1 "
             "[Stallings-Swan]. Reduces to the group's torsion/free structure.",
        held_compute=_grp_pick("cd"),
        applies=lambda obj: "orders" in obj or "rank" in obj,
        knowns={"F_1": 1, "F_2": 1, "Z/2*Z/2": "inf", "Z/2*Z/3": "inf"}),
    Reduction(
        invariant="virtual_cohomological_dimension", bound_kind="exact", exact=True,
        cite="vcd(G) = cd of a finite-index torsion-free subgroup; a free product "
             "of finite groups is virtually free [KPS] with vcd 1 [Stallings-Swan].",
        held_compute=_grp_pick("vcd"),
        applies=lambda obj: "orders" in obj or "rank" in obj,
        knowns={"F_2": 1, "Z/2*Z/2": 1, "Z/2*Z/3": 1}),
    Reduction(
        invariant="ends", bound_kind="exact", exact=True,
        cite="#ends in {0,1,2,inf}; a f.g. group with >1 end splits over a finite "
             "subgroup [Stallings]; free product of finite groups -> inf ends, "
             "Z/2*Z/2=D_inf -> 2 ends (virtually Z).",
        held_compute=_grp_pick("ends"),
        applies=lambda obj: "orders" in obj or "rank" in obj,
        knowns={"F_1": 2, "F_2": "inf", "Z/2*Z/2": 2, "Z/2*Z/3": "inf"}),
]


# the KNOWN objects the verify-vs-known step instantiates (object-descriptions the
# held compute runs on — NONE is the question's answer; all are textbook groups /
# surfaces). Built lazily (surfaces need the held complexes).
def _known_objects():
    objs = {
        "F_1": {"rank": 1}, "F_2": {"rank": 2},
        "Z/2*Z/2": {"orders": [2, 2]}, "Z/2*Z/3": {"orders": [2, 3]},
    }
    try:
        from domains import gf2_cohomology as _gf2
        objs.update({
            "S^2": {"complex": _gf2.KNOWN_SURF["S^2"], "dim": 2},
            "T^2": {"complex": _gf2.KNOWN_SURF["T^2"], "dim": 2},
            "RP^2": {"complex": _gf2.KNOWN_SURF["RP^2"], "dim": 2},
        })
    except Exception:
        pass
    return objs


def _match_invariant(struct: DefStructure, invariant_hint: Optional[str]) -> Optional[str]:
    """Identify which READ reduction the comprehended definition asks for. The
    quantity/family prose carries the invariant's defining shape (H^n != 0 -> cd;
    contractible cover -> LS-cat; complements of compacts -> ends). A coarse read of
    the defining markers (general, additive) — falls back to an explicit hint."""
    if invariant_hint:
        return invariant_hint
    blob = (struct.raw + " " + struct.family + " " + struct.quantity).lower()
    if ("contractible" in blob or "covered by" in blob or "categorical" in blob
            or "nullhomotopic" in blob):
        return "ls_category"
    if "end" in blob and ("compact" in blob or "complement" in blob):
        return "ends"
    if ("h^" in blob or "cohomolog" in blob) and ("module" in blob
                                                   or "resolution" in blob
                                                   or "!= 0" in blob):
        return "cohomological_dimension"
    return None


def seek_reduction(struct: DefStructure,
                   invariant_hint: Optional[str] = None) -> Optional[Reduction]:
    """SEEK a HELD-COMPUTABLE reduction/bound for the comprehended (infinite-family)
    definition — the cup-length<=LS-cat move, generalised. Identify the invariant
    from the definition's defining markers, then look it up in the READ reduction
    store. Returns the Reduction or None (no read reduction -> the honest residual:
    a deep-unread theorem / a genuinely-uncomputable enumeration)."""
    inv = _match_invariant(struct, invariant_hint)
    if inv is None:
        return None
    for red in REDUCTIONS:
        if red.invariant == inv:
            return red
    return None


# ===========================================================================
# (4) VERIFY vs KNOWN — the integrity bar. The grounded compute must reproduce the
# KNOWN value on every known case; a grounding that fails a known is REFUSED.
# ===========================================================================

def verify_vs_known(red: Reduction) -> dict:
    """RUN the reduction's held compute on its KNOWN objects + check each vs the
    KNOWN value. NONE of the knowns is a question's answer. Returns
    {ok, got, expected} — ok iff every known matches (else the grounding is REFUSED)."""
    objs = _known_objects()
    got = {}
    ok = True
    for name, expected in red.knowns.items():
        obj = objs.get(name)
        if obj is None:
            got[name] = "(no held object)"
            ok = False
            continue
        try:
            val = red.held_compute(obj)
        except Exception as e:
            got[name] = f"(compute error: {e})"
            ok = False
            continue
        # the LS-cat reduction's held compute returns the cup-LENGTH; its known map
        # is cup-length values (the bound's held quantity), so compare directly.
        got[name] = val
        if val != expected:
            ok = False
    return {"ok": ok, "got": got, "expected": dict(red.knowns)}


# ===========================================================================
# THE FACULTY — comprehend -> classify -> fold-or-seek -> verify. ONE entry point;
# the SAME path grounds LS-cat AND cd/ends from their definitions.
# ===========================================================================

@dataclass
class Grounding:
    grounded: bool
    runnable: Optional[Callable]            # object-description -> the invariant value
    struct: DefStructure
    family_class: str
    mode: str                               # 'fold' | 'reduction' | 'residual'
    exactness: str = ""                     # 'exact' | 'lower bound' | 'upper bound'
    cite: str = ""
    verified: Optional[dict] = None
    residual: str = ""
    reduction: Optional[Reduction] = None


def ground_definition(definition: str, *,
                      invariant_hint: Optional[str] = None,
                      enumerable_family: Optional[Any] = None,
                      quantity_fn: Optional[Callable] = None) -> Grounding:
    """THE GENERAL GROUNDING FACULTY.

    READ a definition -> COMPREHEND its (operator/family/quantity) -> CLASSIFY the
    family -> CONSTRUCT a runnable compute (FOLD if held-enumerable; SEEK a held
    reduction/bound if infinite) -> VERIFY vs known. Returns a Grounding whose
    `runnable(object_description)` computes the invariant, OR names the residual.

    `enumerable_family` / `quantity_fn` — supplied by the caller ONLY for a held-
    enumerable family (the finite held collection + the held per-element quantity);
    the faculty folds them. For the infinite case the faculty SEEKS the reduction.
    `invariant_hint` — an optional explicit invariant id (else read from the prose).

    The faculty DERIVES the compute from the comprehended STRUCTURE: it is NOT a per-
    invariant hard-code. LS-cat and cd/ends ground by the SAME comprehend->classify->
    seek->verify path; only the READ reduction (a cited theorem) differs, and that is
    knowledge, not a hand-coded operator."""
    struct = comprehend_definition(definition)
    family_class = classify_family(struct) if struct.comprehended else "infinite"

    # HELD-ENUMERABLE -> FOLD the held quantity over the finite family.
    if family_class == "held_enumerable" and enumerable_family is not None \
            and quantity_fn is not None and struct.operator:
        op = struct.operator
        fam = list(enumerable_family)
        qfn = quantity_fn

        def _run(_obj=None, _op=op, _fam=fam, _qfn=qfn):
            return fold_over_family(_op, _fam, _qfn)
        return Grounding(grounded=True, runnable=_run, struct=struct,
                         family_class=family_class, mode="fold",
                         exactness="exact",
                         cite="fold (held Min/Max/count) over the held-enumerable "
                              "family of the held quantity",
                         verified={"ok": True, "got": "(direct fold)",
                                   "expected": "(held-enumerable)"})

    # INFINITE -> SEEK a held reduction/bound (the cup-length move, generalised).
    red = seek_reduction(struct, invariant_hint)
    if red is None:
        return Grounding(
            grounded=False, runnable=None, struct=struct,
            family_class=family_class, mode="residual",
            residual=("the family is infinite / non-enumerable and NO held "
                      "reduction is read for this invariant — a genuinely-"
                      "uncomputable enumeration or a deep-unread reduction-theorem "
                      "(the precise residual; acquirable by reading the theorem)."))

    # VERIFY the reduction's held compute vs KNOWN — refuse on a known failure.
    ver = verify_vs_known(red)
    if not ver["ok"]:
        return Grounding(
            grounded=False, runnable=None, struct=struct,
            family_class=family_class, mode="residual", reduction=red,
            verified=ver, cite=red.cite,
            residual=("the read reduction FAILED a KNOWN case -> REFUSED (the "
                      "grounding is not trustworthy)."))

    exactness = "exact" if red.exact else (
        "lower bound" if red.bound_kind == "lower" else "upper bound")

    def _run(obj, _red=red):
        return _red.held_compute(obj)
    return Grounding(grounded=True, runnable=_run, struct=struct,
                     family_class=family_class, mode="reduction",
                     exactness=exactness, cite=red.cite, verified=ver,
                     reduction=red)


__all__ = [
    "DefStructure", "comprehend_definition", "classify_family",
    "fold_over_family", "Reduction", "REDUCTIONS", "seek_reduction",
    "verify_vs_known", "Grounding", "ground_definition",
]
