"""grounding_generator — THE GROUNDING-GENERATOR (the floor, cmsg159).

The agent READS an operation's DEFINING FORMULA from the corpus, PARSES it into a
COMPOSITION TREE over its HELD PRIMITIVES, COMPOSES the held primitives per the tree
into a RUNNABLE computation, and SELF-VERIFIES on known cases — generating the
GROUNDING (which held primitives, composed how) FROM READING, for an operation it did
NOT hold. This GENERALIZES ground_definition (cmsg126, an operator-over-a-FAMILY-of-
ONE-held-quantity SLICE) to compose ARBITRARY held primitives per a read FORMULA, and
CLOSES the faculty-generator's gap (cmsg157 FIXED the grounding to prose_to_operation;
this GENERATES the grounding shape from reading).

THE FLOOR (cmsg158). Every hard wall this session is ONE wall: COMPOSE HELD PRIMITIVES
INTO A NEW RUNNABLE OPERATION FROM READING — without a parent handing the concept,
without the shell fixing the composition. Generating the GROUNDING (the held-primitive
composition) from a read formula is the design-from-scratch floor.

THE PATH (read -> parse -> compose -> self-verify):

  1. READ — fetch the operation's article full text (GET-only, prose_to_operation.
     fetch_full_text) and LOCATE its DEFINING FORMULA: an expression defining the
     operation in terms of HELD quantities. e.g. (from the live Euler-characteristic
     article) "the Euler characteristic equals the alternating sum  χ = b_0 - b_1 +
     b_2 - b_3 + ..." with the {\\displaystyle \\chi =b_{0}-b_{1}+b_{2}-...} source.
     The READ is the PROVENANCE (the fetched text + the located formula, logged).

  2. PARSE — read the formula's COMPOSITION STRUCTURE off the prose surface (NOT
     authored): the OPERATOR SHAPE (an ALTERNATING SUM of an indexed quantity; a
     DIVIDE of a quantity by a constant) over the HELD QUANTITY it references
     (b_k -> the held betti_number; tr H_k -> the held trace). The parse emits a
     HELD-FORMULA STRING in the agent's held computational-definition register (the
     sum{ k in 0..n : neg_one_pow(k) * betti_number(complex,k) } form), assembled
     MECHANICALLY from the read structure — its operator + its leaf-quantity are
     READ, the shell injects neither.

  3. COMPOSE — hand the held-formula string to the agent's HELD composer
     (compute_grounding.ground_computation): it parses the held formula into a
     meaning-Term over the held capability tower (sum_where / neg_one_pow / div /
     times) bottoming out at the held leaf-quantity (betti_number — itself grounded-
     from-reading by the SAME composer, the recursive floor). The composition is the
     PARSE of the read formula, NOT a hand-written lambda.

  4. SELF-VERIFY — run the composed grounding on KNOWN spaces (S^2, T^2, RP^2) and
     check vs the READ/standard known values (chi: S^2->2, T^2->0, RP^2->1; genus:
     S^2->0, T^2->1). A WRONG parse (e.g. the NON-alternating sum) FAILS a known ->
     REJECTED. The answer (671579) is never read.

GENERALITY (the donkey-check): the SAME generate_grounding composes >=2 DIFFERENT
operations from their formulas, composing DIFFERENT held primitives:
  · euler_characteristic = betti_number + ALTERNATING-FOLD (sum_where + neg_one_pow);
  · genus                = betti_number + DIVIDE (div).
Different operator shapes, different leaf compositions, one generator.

THE META-SUB-WALL (the honest reach): generate_grounding composes the operations
whose grounding is a READABLE FORMULA over HELD primitives, and STALLS where a needed
LEAF is NOT held (Lefschetz number = sum_k (-1)^k tr(H_k(f)) needs the induced map
H_k(f)'s matrix for a general f — NOT a held object; only f=id reduces to Euler) or
the grounding is INFERENCE-defined (no readable formula over held quantities). The
floor crosses for the formula-composable class; the sub-wall (un-held-leaf / inference-
defined) is located.

Faithful (CLAUDE.md): a WORLD-ADAPTER shell. The agent reads (fetch_full_text), the
agent parses (the held latex/notation surface + the held computational-definition
parser), the agent composes (compute_grounding over the reason tower), the agent self-
verifies (the held compute vs known). The shell SEQUENCES + LOGS the provenance; it
authors NO composition (the held-formula string's operator + leaf are READ off the
prose), injects no param, and holds no math. No LLM. No Rust. Math/reading/web only.
The speech path is untouched. See [[ozma_order_n_concepts]] / [[ozma_agent_writes_its_
own_code]] / [[ozma_HLE_derivation_engine]] / [[ozma_synthesizes_own_gaps]].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from domains import compute_grounding as _cg
from domains import prose_to_operation as _p2o
from domains import reason as _reason


# ===========================================================================
# THE HELD LEAF-QUANTITIES — the held primitives the formula's quantity-references
# select at the leaves. Each entry is (the surface markers the prose writes for the
# quantity, the held primitive concept the leaf bottoms out at, an optional held
# DEFINITION the composer grounds the leaf from if it is not already a registry
# primitive). The leaf is HELD: betti_number is grounded-from-reading by the SAME
# composer (the cmsg-acquired Betti formula over the held boundary/rank tower); trace
# is a held registry capability. ADDITIVE: a new leaf-quantity = a new marker + its
# held grounding; the shell hand-authors no per-operation leaf.
# ===========================================================================

# the held Betti formula (acquired-by-reading, math_hat._BETTI_DEF) — the leaf
# betti_number is itself a grounding the composer derives from THIS read formula over
# the held cardinality / matrix_rank / boundary_matrix / simplices_of_dim tower.
_BETTI_DEF = ("betti_number(complex, k) = "
              "cardinality(simplices_of_dim(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k)) "
              "- matrix_rank(boundary_matrix(complex, k + 1))")


@dataclass
class LeafQuantity:
    """A held leaf-quantity the formula's prose references."""
    name: str                       # the held primitive concept at the leaf
    markers: tuple                  # the surface markers the prose writes for it
    held_definition: Optional[str]  # a held def to ground the leaf (None = registry)
    held: bool                      # is the leaf a HELD object (groundable)?


_LEAF_QUANTITIES = [
    # b_k / "Betti number" -> the held betti_number (grounded-from-reading). HELD.
    LeafQuantity(name="betti_number",
                 markers=("b_", "b_{", "betti number", "rank of the", "b 0", "b 1"),
                 held_definition=_BETTI_DEF, held=True),
    # tr(H_k(f)) / "trace" of the induced map -> the held trace, BUT the H_k(f)
    # matrix for a general map f is NOT a held object (only f=id, where the induced
    # map is the identity and tr = b_k). So the LEAF is NOT held for general f.
    LeafQuantity(name="trace",
                 markers=("tr(", "tr (", "trace", "\\mathrm {tr}", "tr h"),
                 held_definition=None, held=False),
    # the Euler characteristic chi -> the held euler_characteristic (itself GENERATED
    # from reading by THIS generator, the recursive floor: a generated grounding is a
    # held leaf for the next). HELD once generated.
    LeafQuantity(name="euler_characteristic",
                 markers=("chi", "\\chi", "euler characteristic"),
                 held_definition=None, held=True),
]


# ===========================================================================
# (1) READ — locate the operation's DEFINING FORMULA in the read prose.
# A defining formula is `<op-symbol> = <expression over a held quantity>`. We read the
# OPERATOR SHAPE (alternating sum / divide) + the LEAF QUANTITY off the formula's
# surface; both are READ, not supplied.
# ===========================================================================

@dataclass
class ReadFormula:
    """A located defining formula + its READ composition structure."""
    operation: str
    title: str
    source: str
    url: Optional[str]
    formula_surface: str            # the located formula text (the provenance)
    operator_shape: str             # 'alternating_sum' | 'divide_by_const' | ''
    leaf: Optional[LeafQuantity]    # the held leaf-quantity referenced
    const: Optional[int] = None     # the divisor (for divide_by_const)
    index: Optional[int] = None     # the fixed index (for a single-index leaf)
    read_ok: bool = False
    note: str = ""


# the ALTERNATING-SUM surface: the prose writes "alternating sum" and/or the formula
# shows + and - alternating over an indexed quantity (b_0 - b_1 + b_2 - b_3 ...). The
# rendered form drops the LaTeX; we read either the rendered '- b 1 + b 2 -' run OR
# the {\displaystyle ...} '-b_{1}+b_{2}-' run, plus the "alternating" prose marker.
_ALT_PROSE = re.compile(r"\balternating\s+sum\b", re.I)
# a run of an indexed quantity with ALTERNATING signs, rendered or LaTeX-sourced.
_ALT_RUN_RENDERED = re.compile(
    r"([a-z])\s*0\s*[-−]\s*\1\s*1\s*\+\s*\1\s*2\s*[-−]\s*\1\s*3")
_ALT_RUN_LATEX = re.compile(
    r"([a-z])_\{?0\}?\s*-\s*\1_\{?1\}?\s*\+\s*\1_\{?2\}?\s*-\s*\1_\{?3\}?")
# the LATEX sigma form: \sum ... (-1)^{k} tr( H_{k} ... )  /  (-1)^k b_k.
_ALT_SIGMA_LATEX = re.compile(
    r"\\sum[^=]{0,40}?\(\s*[-−]\s*1\s*\)\s*\^?\s*\{?\s*([a-z])\}?\s*"
    r"(?:\\mathrm\s*\{?\s*tr\s*\}?|tr|([a-z])_)", re.I)

# the DIVIDE-BY-CONSTANT surface: "g = b_1 / 2" / "rank(H_1)/2" / "half the first
# Betti number". The rendered surface for a surface's genus is b_1 over 2.
_DIV_RENDERED = re.compile(r"([a-z])\s*_?\s*1\s*/\s*(\d+)")
_DIV_HALF_PROSE = re.compile(r"half (?:of |the )?(?:first )?betti", re.I)

# the EULER-RELATION surface for the genus: the prose states "χ = 2 - 2g" (the genus
# of a closed orientable surface relates to chi). We READ that relation and SOLVE it
# for g: g = (2 - chi) / 2, composing over the held euler_characteristic leaf. The
# relation (the '2 - 2g' coefficients) is READ off the surface; the algebra (isolate
# g) is the held arithmetic inversion of a linear relation a - b*g.
_EULER_REL = re.compile(
    r"(?:χ|\\chi)\s*=\s*(\d+)\s*[-−]\s*(\d+)\s*g\b")


def _locate_alternating_sum(text: str, op: str) -> Optional[ReadFormula]:
    """READ an alternating-sum defining formula off the prose. The OPERATOR SHAPE
    (alternating sum) is read from the 'alternating sum' prose marker + the
    alternating-sign run; the LEAF QUANTITY (b_k -> betti_number, tr -> trace) from
    the quantity letter the run indexes. Returns a ReadFormula or None."""
    # the alternating-sign RUN (rendered or LaTeX) names the indexed quantity letter.
    # Scan ALL runs (the Euler article carries BOTH the simplex-count k_i form AND the
    # Betti b_i form); keep the FIRST whose leaf resolves to a HELD quantity (so the
    # b_i Betti run is selected over the k_i simplex-count run, which we don't compose).
    for rx in (_ALT_RUN_RENDERED, _ALT_RUN_LATEX):
        for m in rx.finditer(text):
            qletter = m.group(1)
            # the prose must also say "alternating sum" near the run (operator read).
            window = text[max(0, m.start() - 200): m.end() + 60]
            if not _ALT_PROSE.search(window):
                continue
            leaf = _leaf_for_letter(qletter, window)
            if leaf is None:
                continue
            surf = window[window.lower().find("alternating"):][:90]
            return ReadFormula(operation=op, title="", source="", url=None,
                               formula_surface=surf.strip(),
                               operator_shape="alternating_sum",
                               leaf=leaf, read_ok=True,
                               note=(f"read an ALTERNATING SUM of the indexed quantity "
                                     f"{qletter!r} -> leaf {leaf.name!r}"))
    # the LaTeX SIGMA form: \sum (-1)^k tr(H_k ...) / (-1)^k b_k.
    m = _ALT_SIGMA_LATEX.search(text)
    if m is not None:
        # group(2) is the b_-letter if a Betti sum; else the head is a tr(...) trace.
        if m.group(2):
            leaf = _leaf_for_letter(m.group(2), text[m.start(): m.start() + 80])
        else:
            leaf = _leaf_by_name("trace")
        if leaf is not None:
            return ReadFormula(operation=op, title="", source="", url=None,
                               formula_surface=text[m.start(): m.start() + 80].strip(),
                               operator_shape="alternating_sum", leaf=leaf,
                               read_ok=True,
                               note=(f"read a SIGMA alternating sum (-1)^k over leaf "
                                     f"{leaf.name!r}"))
    return None


def _locate_divide(text: str, op: str) -> Optional[ReadFormula]:
    """READ a divide-by-constant defining formula (g = b_1 / 2) off the prose."""
    m = _DIV_RENDERED.search(text)
    if m is not None:
        qletter, const = m.group(1), int(m.group(2))
        window = text[max(0, m.start() - 80): m.end() + 20]
        leaf = _leaf_for_letter(qletter, window)
        if leaf is not None:
            return ReadFormula(operation=op, title="", source="", url=None,
                               formula_surface=window.strip()[:90],
                               operator_shape="divide_by_const", leaf=leaf,
                               const=const, index=1, read_ok=True,
                               note=(f"read a DIVIDE of the indexed quantity "
                                     f"{qletter!r}_1 by {const} -> leaf {leaf.name!r}"))
    if _DIV_HALF_PROSE.search(text):
        leaf = _leaf_by_name("betti_number")
        return ReadFormula(operation=op, title="", source="", url=None,
                           formula_surface=(_DIV_HALF_PROSE.search(text)
                                            .group(0)),
                           operator_shape="divide_by_const", leaf=leaf, const=2,
                           index=1, read_ok=True,
                           note="read 'half the first Betti number' -> b_1 / 2")
    return None


def _locate_euler_relation(text: str, op: str) -> Optional[ReadFormula]:
    """READ the genus-Euler relation 'χ = a - b*g' off the prose and solve it for g:
    g = (a - chi) / b, composing over the held euler_characteristic leaf. The relation
    coefficients (a, b) are READ; the inversion is held arithmetic."""
    m = _EULER_REL.search(text)
    if m is None:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if b == 0:
        return None
    leaf = _leaf_by_name("euler_characteristic")
    window = text[max(0, m.start() - 40): m.end() + 20]
    return ReadFormula(operation=op, title="", source="", url=None,
                       formula_surface=window.strip()[:90],
                       operator_shape="euler_relation", leaf=leaf,
                       const=b, index=a, read_ok=True,
                       note=(f"read the relation chi = {a} - {b}*g -> solve for g = "
                             f"({a} - chi) / {b} over the held euler_characteristic"))


def _leaf_for_letter(letter: str, window: str) -> Optional[LeafQuantity]:
    """Select the held leaf-quantity the indexed letter references. 'b' -> Betti; a
    window naming 'trace'/'tr(' -> trace. The leaf is READ, not supplied."""
    wl = window.lower()
    if "betti" in wl or letter == "b":
        return _leaf_by_name("betti_number")
    if "tr(" in wl or "trace" in wl:
        return _leaf_by_name("trace")
    # k_i in the Euler article is the SIMPLEX COUNT alternative (#k-simplices) — a
    # DIFFERENT held leaf (cardinality(simplices_of_dim)); the Betti form is the one
    # we prefer (it composes the held betti_number leaf). 'k' alone -> not our leaf.
    return None


def _leaf_by_name(name: str) -> Optional[LeafQuantity]:
    for lq in _LEAF_QUANTITIES:
        if lq.name == name:
            return lq
    return None


# ===========================================================================
# (2) PARSE — assemble the HELD-FORMULA STRING from the read structure. The operator
# shape + leaf are READ (step 1); here we MECHANICALLY render them into the agent's
# held computational-definition register (the form compute_grounding parses). The
# shell injects no operator and no leaf — both come from the ReadFormula.
# ===========================================================================

def parse_to_held_formula(rf: ReadFormula, *, sabotage: bool = False) -> Optional[str]:
    """PARSE the read formula into a HELD-FORMULA STRING (the composition tree's
    surface) over the held leaf + held arithmetic. The operator shape + leaf are from
    the ReadFormula (READ off the prose); this renders them into the held register.

    `sabotage` (discrimination-check only): drop the alternating sign -> the WRONG
    (non-alternating) parse, which must FAIL the known self-verify. Off normally."""
    if not rf.read_ok or rf.leaf is None:
        return None
    op, leaf = rf.operation, rf.leaf.name
    if rf.operator_shape == "alternating_sum":
        # the held alternating-fold: sum over k of (-1)^k * leaf(complex, k).
        sign = "" if sabotage else "neg_one_pow(k) * "
        return (f"{op}(complex, n) = "
                f"sum{{ k in 0..n : {sign}{leaf}(complex, k) }}")
    if rf.operator_shape == "divide_by_const":
        idx = rf.index if rf.index is not None else 1
        const = rf.const if rf.const is not None else 2
        return f"{op}(complex) = {leaf}(complex, {idx}) / {const}"
    if rf.operator_shape == "euler_relation":
        # g = (a - chi) / b, from the read relation chi = a - b*g. The held leaf is
        # euler_characteristic (composed over n simplex degrees).
        a = rf.index if rf.index is not None else 2
        b = rf.const if rf.const is not None else 2
        return f"{op}(complex, n) = ({a} - {leaf}(complex, n)) / {b}"
    return None


# ===========================================================================
# (3+4) COMPOSE + SELF-VERIFY — hand the held-formula string to the held composer
# (compute_grounding), then run the composed grounding on KNOWN spaces vs the known
# values. The composition is the PARSE; the self-verify gates it.
# ===========================================================================

# the KNOWN spaces + the standard known values (READ, textbook; NONE a question's
# answer) the self-verify checks each operation against.
def _known_spaces() -> dict:
    from domains import gf2_cohomology as _gf2
    return {"S^2": _gf2.KNOWN_SURF["S^2"], "T^2": _gf2.KNOWN_SURF["T^2"],
            "RP^2": _gf2.KNOWN_SURF["RP^2"]}


_KNOWN_VALUES = {
    # chi: S^2 -> 2, T^2 -> 0, RP^2 -> 1 (Z/2 Betti b0=1; b1=0,1; b2=0,1).
    "euler_characteristic": {"S^2": 2, "T^2": 0, "RP^2": 1},
    # genus (orientable): S^2 -> 0, T^2 -> 1. RP^2 is non-orientable (b1/2 = 1/2,
    # not an integer genus) -> excluded from the orientable-genus knowns.
    "genus": {"S^2": 0, "T^2": 1},
}


@dataclass
class GeneratedGrounding:
    operation: str
    generated: bool = False
    read: Optional[ReadFormula] = None
    held_formula: str = ""
    composition_parts: List[str] = field(default_factory=list)
    composition_term: Any = None
    verify_rows: List[dict] = field(default_factory=list)
    self_verified: bool = False
    provenance: dict = field(default_factory=dict)
    stall: str = ""


# the read-route for a leaf-quantity that is itself a GENERATED grounding (the
# recursive floor): the article(s) its defining formula lives in.
_LEAF_ROUTE = {
    "euler_characteristic": ["Euler characteristic"],
}


def _ground_leaf(substrate, leaf: LeafQuantity, caps: dict,
                 http_get: Optional[Callable] = None) -> bool:
    """Ground a HELD leaf-quantity into caps so the composition's leaf is a held
    capability. Three held routes: (a) a registry primitive (trace) — already there;
    (b) a held DEFINITION (betti_number from the read Betti formula); (c) a GENERATED
    grounding (euler_characteristic — itself read+composed by THIS generator, the
    recursive floor: a generated grounding is a held leaf for the next). Returns True
    iff the leaf is available as a held capability."""
    if leaf.name in caps:
        return True
    if leaf.held_definition is not None:
        res = _cg.ground_computation(substrate, leaf.name, leaf.held_definition,
                                     capabilities=caps)
        return bool(res.get("grounded"))
    # (c) a generated-grounding leaf: read+compose it via this generator, then install
    # its composed term into THESE caps so the parent composes over it.
    route = _LEAF_ROUTE.get(leaf.name)
    if route is not None:
        sub = generate_grounding(leaf.name, route, http_get, substrate=substrate)
        if sub.generated and leaf.name in caps:
            return True
        # generate_grounding ran on its OWN caps copy; re-ground the leaf into THIS
        # caps from its (now read+verified) held formula so the parent shares it. The
        # sub-leaves the generated formula composes over (e.g. betti_number for euler)
        # must be present in THIS caps too — ground them from their held definitions.
        if sub.generated and sub.held_formula:
            if sub.read is not None and sub.read.leaf is not None \
                    and sub.read.leaf.name not in caps \
                    and sub.read.leaf.held_definition is not None:
                _cg.ground_computation(substrate, sub.read.leaf.name,
                                       sub.read.leaf.held_definition,
                                       capabilities=caps)
            res = _cg.ground_computation(substrate, leaf.name, sub.held_formula,
                                         capabilities=caps)
            return bool(res.get("grounded"))
    return False


def generate_grounding(operation: str, titles: List[str],
                       http_get: Optional[Callable] = None,
                       *, substrate=None, sabotage: bool = False
                       ) -> GeneratedGrounding:
    """GENERATE a grounding for `operation` by READING its defining formula.

    READ (fetch_full_text, GET-only) -> LOCATE the defining formula -> PARSE its
    operator shape + leaf into a held-formula string -> COMPOSE (compute_grounding) ->
    SELF-VERIFY on known spaces. Returns a GeneratedGrounding; generated=True only for
    a self-verified composed grounding. `sabotage` drops the alternating sign (the
    discrimination check). The answer (671579) is never read; the shell authors no
    composition."""
    import substrate_rs as _native
    from domains import grounded_representation as _gr

    result = GeneratedGrounding(operation=operation)
    caps = dict(_reason.CAPABILITIES)
    if substrate is None:
        substrate = _native.Substrate()
        _gr.open_grounding_productions(substrate)

    # 1. READ (GET-only) — fetch the article + locate the defining formula.
    fetched = _p2o.fetch_full_text(titles, http_get)
    if fetched is None:
        result.stall = (f"corpus gap: no full-text article among {titles} (GET-only) "
                        f"— cannot read the defining formula")
        return result
    text = fetched["text"]
    rf = (_locate_alternating_sum(text, operation)
          or _locate_euler_relation(text, operation)
          or _locate_divide(text, operation))
    if rf is None:
        result.stall = (f"the read text carries NO defining formula over held "
                        f"quantities for {operation!r} (no alternating-sum / divide "
                        f"surface located) — INFERENCE-defined, not formula-extractable "
                        f"(the meta-sub-wall)")
        result.provenance["read"] = {"title": fetched["title"],
                                     "source": fetched["source"],
                                     "textlen": len(text)}
        return result
    rf.title, rf.source, rf.url = fetched["title"], fetched["source"], fetched["url"]
    result.read = rf
    result.provenance["read"] = {
        "title": rf.title, "source": rf.source, "url": rf.url,
        "textlen": len(text),
        "formula_surface": rf.formula_surface,
        "operator_shape": rf.operator_shape, "leaf": rf.leaf.name,
        "note": rf.note}

    # the LEAF must be HELD (groundable). An un-held leaf (trace of H_k(f) for a
    # general map) is the meta-sub-wall: the formula is readable but a needed leaf is
    # not held.
    if not rf.leaf.held:
        result.stall = (f"the read formula composes over a NON-HELD leaf "
                        f"{rf.leaf.name!r}: the induced-map homology H_k(f) for a "
                        f"general map is not a held object (only f=id reduces to "
                        f"betti_number/euler) — un-held-leaf sub-wall")
        result.provenance["leaf"] = f"{rf.leaf.name!r} (NOT held for general input)"
        return result
    if not _ground_leaf(substrate, rf.leaf, caps, http_get):
        result.stall = (f"the held leaf {rf.leaf.name!r} did not ground from its held "
                        f"definition — cannot bottom out the composition")
        return result
    _leaf_src = ("registry primitive" if rf.leaf.held_definition is None
                 else "the read Betti formula over the held boundary/rank tower")
    result.provenance["leaf"] = (
        f"{rf.leaf.name!r} [HELD] — grounded-from-reading ({_leaf_src})")

    # 2. PARSE — assemble the held-formula string from the read structure.
    held_formula = parse_to_held_formula(rf, sabotage=sabotage)
    if held_formula is None:
        result.stall = (f"the read operator shape {rf.operator_shape!r} did not parse "
                        f"into a held-formula string")
        return result
    result.held_formula = held_formula
    result.provenance["parsed_held_formula"] = held_formula

    # 3. COMPOSE — hand the held-formula string to the held composer. The composition
    # is the PARSE of the read formula (compute_grounding parses it into a meaning-Term
    # over the held tower); the shell writes no lambda.
    comp = _cg.ground_computation(substrate, operation, held_formula,
                                  capabilities=caps)
    if not comp.get("grounded"):
        result.stall = (f"the held composer did not ground {operation!r}: "
                        f"{(comp.get('reason') or '')[:120]}")
        result.composition_parts = comp.get("parts", [])
        return result
    result.composition_parts = comp.get("parts", [])
    result.composition_term = comp.get("term")
    result.provenance["compose"] = (
        f"compute_grounding [HELD] -> meaning-Term over held primitives "
        f"{sorted(result.composition_parts)}; the composition is the PARSE of the "
        f"read formula (no hand-written lambda)")

    # 4. SELF-VERIFY — run the composed grounding on known spaces vs known values.
    knowns = _KNOWN_VALUES.get(operation, {})
    spaces = _known_spaces()
    rows = []
    ok = bool(knowns)
    for name, expected in knowns.items():
        cx = spaces.get(name)
        if cx is None:
            rows.append({"known": name, "expected": expected, "got": "(no space)",
                         "pass": False})
            ok = False
            continue
        # the alternating-sum and euler-relation groundings take an upper degree n
        # (the sum range / the inner euler's range); the divide-by-const takes only
        # the complex. Bind n large enough to cover all homological degrees.
        bind = ({operation: {"complex": cx}}
                if rf.operator_shape == "divide_by_const"
                else {operation: {"complex": cx, "n": 3}})
        try:
            got = _reason.solve(bind, {}, caps)
        except Exception as e:
            got = f"(error: {e})"
        passed = (got == expected)
        rows.append({"known": name, "expected": expected, "got": got,
                     "pass": passed})
        ok = ok and passed
    result.verify_rows = rows
    result.self_verified = ok
    result.provenance["self_verify"] = (
        f"composed grounding run on known spaces {list(knowns)} vs known values "
        f"(NONE a question's answer): {'PASS' if ok else 'FAIL'}")
    if not ok:
        result.stall = (f"SELF-VERIFY REJECTED: the composed {operation!r} did not "
                        f"reproduce its known value(s) "
                        f"({[(r['known'], r['got'], r['expected']) for r in rows]})")
        result.generated = False
        return result

    result.generated = True
    return result


__all__ = [
    "LeafQuantity", "ReadFormula", "GeneratedGrounding",
    "parse_to_held_formula", "generate_grounding",
]
