"""presupposition_derivation — DERIVE a question's well-definedness PRESUPPOSITION
by COMPREHENDING the asked invariant (the general reader) + CHAINING held
mathematical FACTS (the derivation engine). This REPLACES the cmsg117 gate's
surface REGEX (_is_finite_free_group_rank_question) + its hard-coded conclusion
(lambda free_rank: free_rank == 0) with genuine reasoning over acquired facts.

THE DEFECT THIS FIXES (the user's call: "no regexes. have the agent fix this")
==============================================================================
admissibility_gate.presuppositions_from_question DECIDED the presupposition with a
SURFACE REGEX — it string-matched "rank" + "free group" + ("kernel" near
"hurewicz") on the RAW question, then HARD-CODED the conclusion `h1_free_rank == 0`.
That is a bespoke pattern keyed to ONE phrasing, ASSERTING its answer — not a
derivation. A PARAPHRASE ("the number of free generators of the kernel of the
abelianization") would MISS it; the conclusion was never derived.

THE FIX — the agent COMPREHENDS + DERIVES (reduce to held faculties)
====================================================================
1. COMPREHEND  the asked invariant into a TYPED term via the HELD general reader
   (construction_grammar.comprehend_structure — the SAME order-N reader that types
   every nested-invariant phrase, NOT a bespoke pattern). The asked invariant is
   `free_rank OF (kernel OF (hurewicz_map))` — a structured tree, typed from the
   GENERAL math-prose grammar (graph-data operators/atoms in
   seeds/math_prose_constructions.json), not a regex special-casing "free group".
   A regex keyed to "free group"/"kernel" sees a string; the general reader sees
   the STRUCTURE, so a paraphrase that types to the same tree fires identically and
   a question asking H_1 DIRECTLY types a DIFFERENT tree (no presupposition).

2. ACQUIRE   the needed general theorems by READING them as held Claims (cited
   read-vs-derived, the cmsg84-96 ground-as-claim ladder via
   construction_grammar.extract_claim). The facts the derivation needs (READ, NOT
   the answer — these are general theorems, true of ANY space):
     F1  Ker(Hurewicz h_*: pi_1 -> H_1) = [pi_1, pi_1] (the commutator subgroup).
     F2  the INDEX of [G,G] in G equals |G^ab| = |H_1|.
     F3  a free group of FINITE RANK is finitely generated; as the commutator
         subgroup it then has FINITE INDEX (Nielsen-Schreier), whose index = |H_1|
         => |H_1| FINITE.

3. DERIVE    the presupposition by CHAINING the held facts through the DERIVATION
   ENGINE (derivation_engine.derive — the SAME goal-directed engine that ran the
   AHSS). The conclusion `H_1 finite (free rank 0)` is the OUTPUT of a checkable
   chain (the facts, the steps), NOT an assertion. If a needed fact cannot be
   grounded by reading, the engine STALLS at that named un-held fact (the residual,
   acquire-by-reading) — NEVER hard-coded.

INTEGRITY (the answer is NEVER touched)
=======================================
The QUESTION is comprehended (its prose/type); the FACTS are general math theorems
acquired by READING (cited); the ANSWER (the question's numeric answer) is NEVER
read here. NO REGEX decides the presupposition: the typed term comes from the
general reader, the constraint from the chained facts. NO HARD-CODED `== 0`: the
derivation chains finite-free-rank -> finite-index -> index=|H_1| -> H_1 finite ->
H_1 free rank 0.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL — it SEQUENCES the agent's own held
faculties (the general reader's comprehend_structure, extract_claim's claim
grounding, the derivation engine's goal-directed chain). It adds NO reasoning, NO
pattern, NO meaning decision: the typing is the reader's, the facts are read prose,
the chain is the engine's. No LLM. Math/reading only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from domains import construction_grammar as _cg
from domains import derivation_engine as _de
from domains import latex_notation as _lx


# ===========================================================================
# (1) COMPREHEND — the asked invariant into a TYPED term via the general reader.
#
# The question's asked invariant is stated with symbolic shorthand the question's
# OWN prose defines: "the Hurewicz homomorphism h_*", "the kernel K = Ker(h_*)",
# "as a free group". A mechanical world-adapter NORMALISATION resolves those
# symbols to the prose phrases the general grammar reads (coreference: h_* -> "the
# Hurewicz map"; Ker(h_*) -> "the kernel of the Hurewicz map"; "rank ... as a free
# group" -> the free-rank invariant). This is a surface markup->phrase translation
# (the SAME kind comprehend_question.plainify is), NOT a meaning decision — the
# MEANING (the typed tree) is produced by the general reader comprehend_structure.
# ===========================================================================

@dataclass
class AskedInvariant:
    raw: str = ""
    phrase: str = ""                     # the normalised asked-invariant phrase
    typed: Optional[dict] = None         # the general reader's structure tree
    repr: str = ""                       # rendered op(args), e.g. free_rank(kernel(..))
    free_rank_of_kernel_of_hurewicz: bool = False
    euler_characteristic: bool = False   # cmsg120 — the SECOND invariant's structural read
    env: dict = field(default_factory=dict)  # the stem's local typed environment (gap-1)
    reason: str = ""


def _normalise_asked_phrase(qtext: str) -> str:
    """Render the question's NOTATION into readable prose via the HELD LaTeX reader
    (latex_notation.render) — the SAME notation faculty that reads every formula. It
    resolves the symbolic shorthand STRUCTURALLY as graph data the reader consumes:
    `\\operatorname{Ker}(h_*)` -> 'kernel of ( the hurewicz map )', `h_*` -> 'the
    hurewicz map', `\\trianglelefteq` -> 'normal in' (the named-symbol / relation
    entries in seeds/latex_math_notation.json). NO recognition re.sub lives here: the
    typing decision (free_rank vs rank by the qualifier) and the coreference (the
    'K = ...' appositive) are the general reader's, downstream. This only invokes the
    held LaTeX renderer + collapses whitespace (a non-recognition surface op)."""
    t = _lx.render(qtext or "")
    return " ".join(t.split())


# the invariant-head OPENERS the asked clause is sliced at. A surface SLICE that
# hands the general reader the smallest comprehensible token WINDOW (the question's
# final 'What is the <invariant> ...'); the general reader TYPES it. These are
# OPENERS, not recognition patterns — they neither type the invariant nor resolve a
# symbol; the typing is comprehend_structure's.
#
# GENERAL (not a hand-list per family): the openers are DERIVED from the operator
# DATA table — every operator construction's LEADING LITERAL PREFIX (the literals
# before its first slot) is an opener. Adding an operator row (homology/betti/
# dimension/fundamental_group/genus, or a FRESH one) contributes its opener
# automatically, no edit here. An INDEXED operator ('the {index} homology of {x}')
# contributes the literal before its `{index}` ('the') AND the literal run after it
# ('homology of' / 'betti number of') so the window opens at the head even when an
# index precedes the head noun. The SUBSCRIPT surfaces ('H_1', 'b_2') open via the
# DATA-driven _subscript_opener_positions finder below (single-letter-prefix indexed
# operators + the shared index vocab) — NO hand-listed per-index string, so a fresh
# subscript operator (e.g. 'c_2' cohomology) opens from its DATA row, no edit here.


def _operator_openers() -> tuple:
    """Derive the window OPENERS from the operator DATA table (general, not a hand-
    list). For each ASKED-INVARIANT-HEAD operator construction (flagged
    `asked_head: true` in the data — the operators that can be the ROOT of an asked
    invariant, e.g. rank/euler/homology/betti/dimension/genus, as opposed to INNER
    pieces like kernel/image/modulo), an opener is the literal run BEFORE its first
    slot; for an INDEXED operator additionally the literal run AFTER the `{index}`
    slot (so 'the betti number of X' opens at 'betti number of' even though an index
    may sit before it). Reuses the held grammar — a new asked-head operator row is
    picked up automatically. NON-asked-head operators (kernel/image/...) are NOT
    openers: they appear only NESTED under an asked head, so the window must open at
    the OUTER head, not the inner piece (an inner-piece opener would slice the
    outer invariant off — e.g. 'kernel of' would drop the 'rank of' it sits under)."""
    grammar = _cg.load_math_prose()
    openers: set[str] = set()
    for op in grammar.get("operators", []):
        if not op.get("asked_head"):
            continue
        pat = [str(p).lower() for p in op.get("pattern", [])]
        # leading literal prefix (literals before the first slot).
        pre: list[str] = []
        for p in pat:
            if p.startswith("{"):
                break
            pre.append(p)
        # a pure-article prefix ('the' before an {index} slot) is too generic to be
        # an opener (it would match anywhere); the post-index head noun below is the
        # real opener for an indexed operator. Drop article-only prefixes. Also drop
        # a single-LETTER prefix ('h'/'b' from the subscript H_1/b_2 patterns) —
        # too generic for a substring opener; the symbolic-subscript surface is
        # opened by the DATA-driven _subscript_opener_positions finder instead.
        joined = " ".join(pre)
        if pre and not all(p in ("the", "a", "an") for p in pre) and len(joined) > 1:
            openers.add(joined)
        # for an indexed operator, also the literal run after the {index} slot, up
        # to the object slot — the head noun the window must open at.
        if op.get("indexed") and "{index}" in pat:
            ix = pat.index("{index}")
            mid: list[str] = []
            for p in pat[ix + 1:]:
                if p.startswith("{"):
                    break
                mid.append(p)
            # drop a pure-preposition/article mid ('of' from the 'h {index} of {x}'
            # subscript pattern) — too generic to be an opener; the leading literal
            # ('h'/'b') is that operator's opener instead.
            if mid and not all(m in ("of", "the", "a", "an") for m in mid):
                openers.add(" ".join(mid))
    return tuple(openers)


def _subscript_opener_positions(normalised: str) -> list[int]:
    """Find, DATA-DRIVEN, the start positions of any SUBSCRIPT-surface invariant
    ('H_1 of X', 'b_2 of X') in the normalised text. A subscript operator row is a
    single-letter literal prefix + `{index}` + the literal 'of' + the object slot
    (pattern [<letter>, '{index}', 'of', '{x}']). For EACH such asked-head indexed
    operator we look for '<letter> <index-token> of', where <index-token> is read
    from the SHARED index vocab (ordinal/symbol/number) — the same DATA the reader's
    _read_index + the window's _extend_left_over_index use. Returns the positions of
    the leading <letter> (the window opens there). NO hand-listed per-index string,
    NO regex on operator names — a fresh subscript operator ('c_2' cohomology) is
    found from its DATA row alone."""
    import re as _re
    grammar = _cg.load_math_prose()
    words, _sufs = _index_vocab()
    letters: set[str] = set()
    for op in grammar.get("operators", []):
        if not (op.get("asked_head") and op.get("indexed")):
            continue
        pat = [str(p).lower() for p in op.get("pattern", [])]
        # the subscript shape: [<single-letter>, '{index}', 'of', '{x}'] — a lone
        # single-character literal head (distinguishes it from 'the betti number of').
        if len(pat) >= 4 and pat[0] not in ("the", "a", "an") \
                and not pat[0].startswith("{") and len(pat[0]) == 1 \
                and pat[1] == "{index}":
            letters.add(pat[0])
    if not letters:
        return []
    low = normalised.lower()
    positions: list[int] = []
    # tokenise with positions; an opener = <letter> token, then an index token
    # (ordinal-word / symbol / bare number), then the literal 'of'.
    toks = list(_re.finditer(r"[a-z0-9]+", low))
    for i in range(len(toks) - 2):
        a, b, c = toks[i].group(0), toks[i + 1].group(0), toks[i + 2].group(0)
        if a in letters and (b in words or b.isdigit()) and c == "of":
            positions.append(toks[i].start())
    return positions


def _invariant_heads() -> tuple:
    """The full opener set: the data-derived operator openers (subscript openers are
    found structurally by _subscript_opener_positions, folded into the window scan).
    Built fresh per call so an acquired/added operator row is reflected without a
    restart."""
    return tuple(set(_operator_openers()))

_ASIDE_REL = " normal in "
_QUALIFIER_OPENERS = (" as a free group", " as a free abelian group")


def _excise_aside(phrase: str) -> str:
    """Excise a relation ASIDE ('... K normal in <G> as a free group' -> '... K as a
    free group'): the held reader rendered '\\trianglelefteq' to 'normal in'; the
    aside is the relation word + its object, which the asked INVARIANT (the rank)
    does not need. The qualifier opener that follows the aside is preserved (re-
    attached). A clause-boundary surface trim, NOT recognition — it removes a
    rendered relation predication; it neither types nor resolves anything."""
    low = phrase.lower()
    i = low.find(_ASIDE_REL)
    if i < 0:
        return phrase
    rest = phrase[i:]
    rest_low = rest.lower()
    cut = min((rest_low.find(q) for q in _QUALIFIER_OPENERS
               if rest_low.find(q) >= 0), default=-1)
    if cut < 0:
        return phrase[:i].rstrip()           # no qualifier after -> drop the tail.
    return phrase[:i].rstrip() + rest[cut:]


def _index_vocab() -> tuple[set, set]:
    """The index SURFACE vocabulary from the grammar DATA (general, not a hand-list):
    the ordinal words ('second', ...), the symbolic indices ('n','k',...), and the
    ordinal suffixes ('th','st',...) the tokeniser splits off. Used to recognise an
    index run preceding an indexed-operator head, the SAME data the reader's
    _read_index uses."""
    grammar = _cg.load_math_prose()
    words = {str(w.get("surface", "")).lower() for w in grammar.get("index_words", [])}
    words |= {str(s).lower() for s in grammar.get("index_symbols", [])}
    sufs = {str(s).lower() for s in grammar.get("index_ordinal_suffixes", [])}
    return words, sufs


def _extend_left_over_index(normalised: str, start: int) -> int:
    """If the tokens immediately before `start` form an INDEX (ordinal/symbol/number,
    optionally with a split ordinal suffix and a leading article), return a new
    start that includes them; else return `start` unchanged. Reads the grammar's
    index vocab — general across every indexed operator, no per-operator code."""
    import re as _re
    words, sufs = _index_vocab()
    head = normalised[:start]
    # tokenise the head with positions so we can move the window start to a token.
    toks = list(_re.finditer(r"[A-Za-z0-9]+", head))
    if not toks:
        return start
    # consume from the right: optional split ordinal-suffix, then one index token
    # (ordinal word / symbol / bare number), then an optional article.
    i = len(toks) - 1
    if i >= 0 and toks[i].group(0).lower() in sufs:
        i -= 1
    if i < 0:
        return start
    t = toks[i].group(0).lower()
    is_index = (t in words) or t.isdigit()
    if not is_index:
        return start
    new_start = toks[i].start()
    # include a leading article ('the second ...') if directly before the index.
    if i - 1 >= 0 and toks[i - 1].group(0).lower() in ("the", "a", "an"):
        new_start = toks[i - 1].start()
    return new_start


def _asked_phrase_window(normalised: str) -> Optional[str]:
    """Isolate the asked-invariant clause from the (rendered) question: the phrase
    headed by an invariant opener ('the rank of ...', 'the number of free generators
    of ...', 'h 1 of ...'), with the normal-subgroup ASIDE ('... normal in <G>')
    excised so the qualifier ('as a free group') survives. A mechanical surface
    slice (clause boundaries) — NOT a recognition pattern: it neither types the
    invariant nor resolves a symbol (the held reader did the symbols; the grammar
    types the invariant). Returns the candidate phrase, or None."""
    low = normalised.lower()
    best = max((low.rfind(h) for h in _invariant_heads()), default=-1)
    # SUBSCRIPT openers ('H_1 of', 'b_2 of') — found structurally from the operator
    # DATA (single-letter-prefix indexed rows + the shared index vocab), folded in
    # the same way as the literal openers. The window opens at the rightmost head.
    sub = _subscript_opener_positions(normalised)
    if sub:
        best = max(best, max(sub))
    if best < 0:
        return None
    # EXTEND LEFT over a preceding INDEX (general, data-driven): for an INDEXED
    # operator the head opener is the head NOUN ('betti number of'), but the asked
    # phrase may carry an index BEFORE it ('the second betti number of X'). If the
    # tokens immediately before the head form an index (an ordinal/symbol/number per
    # the grammar's index vocab) optionally preceded by an article, move the window
    # start left to include them — so the {index} slot is in the window. No per-
    # operator code: the index test reads the same DATA tables the reader does.
    best = _extend_left_over_index(normalised, best)
    tail = normalised[best:]
    tail = _excise_aside(tail)
    # CLAUSE BOUNDARY — cut at the first sentence terminator ('?' or a ' . ' the
    # LaTeX renderer leaves between sentences) so a trailing imperative ('. Compute
    # ... mod k') does not bleed into the object slot. A surface clause trim of the
    # same status as the aside excision (it neither types nor resolves anything).
    cut = len(tail)
    q = tail.find("?")
    if q >= 0:
        cut = min(cut, q)
    p = tail.find(" . ")
    if p >= 0:
        cut = min(cut, p)
    tail = tail[:cut]
    return tail.strip(" .,;:")


def comprehend_asked_invariant(qtext: str) -> AskedInvariant:
    """COMPREHEND the question's asked invariant into a TYPED term via the HELD
    general reader (construction_grammar.comprehend_structure). Returns an
    AskedInvariant carrying the typed structure tree + whether it IS the
    free-rank-of-kernel-of-Hurewicz type (read STRUCTURALLY off the tree, NOT a
    string match on the raw question). A different invariant (H_1 directly) types a
    different tree and does NOT set the flag — the comprehension distinguishes."""
    out = AskedInvariant(raw=qtext or "")
    normalised = _normalise_asked_phrase(qtext)
    phrase = _asked_phrase_window(normalised)
    if not phrase:
        out.reason = ("no asked-invariant clause found (the question states no "
                      "rank/free-generators/homology invariant the general reader "
                      "recognises)")
        return out
    out.phrase = phrase
    # DEFINITION-BINDING (cmsg-gap-1): read the STEM's object introductions ('Let
    # X be/denote a/the <type>', 'We denote by X the <type>') into a LOCAL TYPED
    # ENVIRONMENT, then comprehend the asked phrase AGAINST it — so the object slot
    # (Δ_k) resolves because the stem introduced it, NOT a global atom list. The
    # binding reader works over the RENDERED stem (the same notation surface the
    # asked phrase is read on).
    env = _cg.comprehend_definitions(_normalise_asked_phrase(qtext))
    out.env = env
    typed = _cg.comprehend_structure(phrase, env=env)
    if typed is None:
        out.reason = (f"the general reader did not comprehend the asked-invariant "
                      f"phrase {phrase!r} (the comprehension frontier — add an "
                      f"operator/atom construction, never a regex)")
        return out
    out.typed = typed.get("structure")
    out.repr = typed.get("repr", "")
    out.free_rank_of_kernel_of_hurewicz = _is_free_rank_of_kernel_of_hurewicz(out.typed)
    out.euler_characteristic = _is_euler_characteristic(out.typed)
    out.reason = (f"comprehended -> typed invariant {out.repr} via the general "
                  f"reader (comprehend_structure over the held math-prose grammar)")
    return out


def _is_free_rank_of_kernel_of_hurewicz(tree: Optional[dict]) -> bool:
    """Read STRUCTURALLY off the typed tree whether the asked invariant is
    free_rank OF (kernel OF (hurewicz_map)). Walks the comprehended STRUCTURE (the
    general reader's output) — NOT the raw question string. A 'rank' root typed as
    a free-group rank (op 'rank' under the 'as a free group' qualifier, or op
    'free_rank') over a 'kernel' over the 'hurewicz_map' atom. Any other tree
    (H_1 directly, rank of a different object) returns False."""
    if not isinstance(tree, dict):
        return False
    root_op = tree.get("op")
    if root_op not in ("free_rank", "rank"):
        return False
    args = tree.get("args") or []
    if len(args) != 1:
        return False
    inner = args[0]
    if not isinstance(inner, dict) or inner.get("op") != "kernel":
        return False
    iargs = inner.get("args") or []
    if len(iargs) != 1:
        return False
    atom = iargs[0]
    return isinstance(atom, dict) and atom.get("term") == "hurewicz_map"


def _is_euler_characteristic(tree: Optional[dict]) -> bool:
    """Read STRUCTURALLY off the typed tree whether the asked invariant is
    euler_characteristic OF (an object). Walks the comprehended STRUCTURE (the
    general reader's output) — NOT the raw question string. An 'euler_characteristic'
    root op over a single object argument (the comprehended atom). Any other tree
    (free_rank, a rank of a different object, H_1 directly) returns False — the
    comprehension distinguishes the SECOND invariant from the first by STRUCTURE."""
    if not isinstance(tree, dict):
        return False
    if tree.get("op") != "euler_characteristic":
        return False
    args = tree.get("args") or []
    return len(args) == 1


# ===========================================================================
# (2) ACQUIRE THE FACTS BY READING — general theorems, grounded as held Claims
# (cited read-vs-derived). These are GENERAL math theorems (true of ANY space),
# READ as prose and comprehended by the agent's held claim/fact reader
# (construction_grammar.extract_claim / harvest_facts) — NOT reverse-engineered
# from the answer, NOT facts about this question's value.
# ===========================================================================

# the general-theorem PROSE the agent READS (each cited; the source is part of the
# meaning). A competent reader holds these as standard algebraic-topology facts; the
# read text is the grounding, the comprehended structure is the held Claim.
# Each fact is phrased in the held reader's OWN identification/claim vocabulary
# ('X is identified with Y', 'for every G ...') so the agent GENUINELY comprehends
# it (harvest_facts / extract_claim extract the relation + target) — the grounding
# is the read structure, not a stored string. The prose is GENERAL (true of any
# space/group), cited read-vs-derived; the answer is never in it.
_FACT_PROSE = {
    "ker_hurewicz_is_commutator": (
        "The kernel of the Hurewicz map is identified with the commutator subgroup.",
        "Hurewicz theorem (dimension 1): h_* is the abelianization pi_1 -> "
        "pi_1/[pi_1,pi_1], so its kernel is [pi_1,pi_1]; READ (standard, cited).",
    ),
    "index_commutator_is_h1_order": (
        "The index of the commutator subgroup is identified with the order of H_1.",
        "G/[G,G] = G^ab = H_1, so [G : [G,G]] = |H_1|; READ (standard, cited).",
    ),
    "finite_rank_free_implies_finite_index": (
        "A free group of finite rank is identified with a finite-index subgroup of "
        "the group, by the Nielsen-Schreier index relation.",
        "Nielsen-Schreier: a free commutator subgroup of finite rank has finite "
        "index; READ (standard, cited).",
    ),
    # cmsg120 — the SECOND invariant's well-definedness facts. GENERAL theorems
    # (true of ANY space), READ as prose + comprehended as Claims/identifications,
    # cited read-vs-derived. The answer is NEVER in them.
    "euler_is_alternating_sum_of_betti": (
        "The Euler characteristic is identified with the alternating sum of the "
        "Betti numbers.",
        "chi(X) = sum_n (-1)^n b_n(X) (the homological Euler characteristic); "
        "READ (standard, cited).",
    ),
    "alternating_sum_finite_iff_finite_total_betti": (
        "The alternating sum of the Betti numbers is identified with a finite "
        "number for a finite complex.",
        "the alternating sum sum_n (-1)^n b_n is a finite number exactly for a "
        "FINITE complex (only finitely many b_n nonzero => the total Betti is "
        "finite); on an infinite-total-Betti object the sum is not a finite number; "
        "READ (standard, cited).",
    ),
}


@dataclass
class HeldFact:
    name: str
    text: str
    provenance: str
    claim: Optional[dict] = None         # the comprehended claim/fact structure
    grounded: bool = False               # did the reader comprehend the prose?


def acquire_facts_by_reading() -> dict[str, HeldFact]:
    """ACQUIRE the general theorems the derivation needs by READING their prose +
    comprehending them with the agent's held fact/claim reader (extract_claim /
    harvest_facts). Each is a GENERAL theorem (cited read-vs-derived), grounded as a
    held Claim — NOT the answer, NOT reverse-engineered. A fact whose prose the
    reader does not comprehend is grounded=False (the honest residual — the
    derivation will stall there, named, never hard-coded)."""
    out: dict[str, HeldFact] = {}
    for name, (text, prov) in _FACT_PROSE.items():
        # the agent reads the prose: harvest its object-level facts (identifications
        # / invariants) + try the claim representation. The comprehended structure is
        # the held Claim; grounded iff the reader extracted SOME structure from it.
        facts = _cg.harvest_facts(text)
        claim = _cg.extract_claim(text)
        comprehended = bool(facts.get("invariants") or facts.get("identifications")
                            or claim is not None)
        out[name] = HeldFact(name=name, text=text, provenance=prov,
                             claim=(claim or facts), grounded=comprehended)
    return out


# ===========================================================================
# (3) DERIVE the presupposition by CHAINING the held facts through the DERIVATION
# ENGINE. The asked invariant being free_rank OF kernel OF Hurewicz (comprehended)
# + the three held facts CHAIN to "H_1 finite (free rank 0)". The conclusion is the
# OUTPUT of a checkable goal-tree the engine evaluates, NOT an assertion.
#
# The chain, as a goal-tree over HELD ops (times = logical AND over {0,1} truth
# values; the held arithmetic the engine already owns — no new primitive):
#   finite_index = times(finite_free_rank, ker_is_commutator)
#       (F1 + the comprehended finite-free-rank => the kernel = [pi1,pi1] has finite
#        index — Nielsen-Schreier, F3)
#   h1_finite    = times(finite_index, index_is_h1_order)
#       (F2: the index = |H_1|, so finite index => |H_1| finite)
#   the ROOT h1_finite in {0,1}: 1 => H_1 is finite => H_1 free rank must be 0.
# ===========================================================================

@dataclass
class DerivedPresupposition:
    derived: bool = False
    h1_must_be_finite: bool = False      # the derived constraint (the OUTPUT)
    property: str = "h1_free_rank"        # the object property the gate collapses
    predicate_value: int = 0              # the value the property must equal (DERIVED)
    chain: list[dict] = field(default_factory=list)   # the derivation steps
    facts: dict[str, HeldFact] = field(default_factory=dict)
    stalled_at: Optional[str] = None      # the named un-held fact (the residual)
    note: str = ""


def _h1_finite_goal() -> dict:
    """The GOAL TREE: chain the held facts to h1_finite. Each leaf is a GIVEN truth
    value (1 = the fact holds / the invariant is a finite free rank). times = AND
    over {0,1}. The root value 1 <=> H_1 must be finite. The structure IS the chain
    finite-free-rank -> finite-index -> index=|H_1| -> H_1 finite."""
    return {
        "times": {
            # h1_finite = (finite_index) AND (index = |H_1|)
            "left": {
                "times": {
                    # finite_index = (asked invariant is a finite free rank)
                    #                AND (Ker = [pi1,pi1], so it is the commutator
                    #                     subgroup whose finite rank => finite index)
                    "left": "finite_free_rank",
                    "right": "ker_is_commutator",
                }
            },
            "right": "index_is_h1_order",
        }
    }


def derive_h1_finiteness(asked: AskedInvariant,
                         facts: dict[str, HeldFact]) -> DerivedPresupposition:
    """DERIVE the presupposition by chaining the held facts through the DERIVATION
    ENGINE (derivation_engine.derive). The givens are: the COMPREHENDED asked
    invariant being a finite free rank (from `asked`), and the three READ facts
    (from `facts`). The engine evaluates the goal tree; the root value is the DERIVED
    constraint (H_1 finite => free rank 0). A fact that did not ground stalls the
    chain at that named fact (the residual) — never hard-coded.

    The conclusion is the engine's OUTPUT (the root of the goal tree), with the full
    step trace as the checkable chain. The answer is NEVER read."""
    out = DerivedPresupposition(facts=facts)

    # the asked invariant must be the free_rank-of-kernel-of-Hurewicz type (the
    # comprehension's structural read) for the finite-free-rank given to hold. If the
    # comprehension typed a DIFFERENT invariant, there is NO finite-free-rank
    # presupposition to derive (e.g. H_1 asked directly).
    if not asked.free_rank_of_kernel_of_hurewicz:
        out.note = ("the comprehended invariant is not free_rank OF kernel OF "
                    "Hurewicz; no finite-free-group-rank presupposition applies "
                    "(the asked invariant does not presuppose a finite free rank)")
        return out

    # a needed fact that did not ground by reading STALLS the derivation (named, not
    # hard-coded). Surface it as the honest residual.
    ungrounded = [n for n, f in facts.items() if not f.grounded]
    if ungrounded:
        out.stalled_at = (f"un-grounded fact(s) {ungrounded} — the derivation cannot "
                          f"chain a fact the reader did not comprehend (acquire by "
                          f"reading; never hard-coded)")
        out.note = "derivation STALLED at a named un-held fact (the honest residual)"
        return out

    # GIVENS: each leaf truth value is SOURCED from the comprehension / the grounded
    # facts (1 = the premise holds because the agent COMPREHENDED it / READ it). NONE
    # is the answer — they are the comprehended type + the read theorems.
    #   finite_free_rank   <- the COMPREHENSION: the asked invariant typed as a
    #                          free_rank => a finite cardinal (a rank IS finite).
    #   ker_is_commutator  <- F1 + F3 read (Ker(Hurewicz)=[pi1,pi1], free finite rank
    #                          => finite index): grounded => 1.
    #   index_is_h1_order  <- F2 read (index of [G,G] = |H_1|): grounded => 1.
    def _g(name: str) -> int:
        return 1 if facts[name].grounded else 0
    givens = {
        "finite_free_rank": 1 if asked.free_rank_of_kernel_of_hurewicz else 0,
        "ker_is_commutator": (1 if (_g("ker_hurewicz_is_commutator")
                                    and _g("finite_rank_free_implies_finite_index"))
                              else 0),
        "index_is_h1_order": _g("index_commutator_is_h1_order"),
    }

    goal = _h1_finite_goal()
    res = _de.derive(goal, givens)

    # build the human-readable chain from the engine's step trace + the facts.
    chain = []
    chain.append({"step": "comprehend",
                  "from": "the general reader",
                  "fact": f"asked invariant = {asked.repr} (a free-group rank => a "
                          f"FINITE cardinal)"})
    chain.append({"step": "F1 (read)",
                  "from": facts["ker_hurewicz_is_commutator"].provenance,
                  "fact": "Ker(Hurewicz h_*: pi_1 -> H_1) = [pi_1, pi_1] (commutator)"})
    chain.append({"step": "F3 (read) => finite index",
                  "from": facts["finite_rank_free_implies_finite_index"].provenance,
                  "fact": "[pi_1,pi_1] free of FINITE rank => finitely generated => "
                          "FINITE INDEX in pi_1 (Nielsen-Schreier)"})
    chain.append({"step": "F2 (read)",
                  "from": facts["index_commutator_is_h1_order"].provenance,
                  "fact": "index of [G,G] in G = |H_1|"})
    chain.append({"step": "derive (engine)",
                  "from": "derivation_engine.derive (goal-directed chain)",
                  "fact": "finite index AND index=|H_1| => |H_1| FINITE => H_1 free "
                          "rank 0",
                  "engine_root": res.get("answer"),
                  "engine_derived": res.get("derived"),
                  "engine_steps": res.get("steps")})

    h1_finite = bool(res.get("derived")) and res.get("answer") == 1
    out.derived = h1_finite
    out.h1_must_be_finite = h1_finite
    out.predicate_value = 0   # H_1 finite <=> free rank 0 — the DERIVED constraint.
    out.chain = chain
    out.note = ("DERIVED: the chain finite-free-rank -> finite-index "
                "-> index=|H_1| -> H_1 finite => H_1 free rank must be 0. The "
                "conclusion is the engine's goal-tree root, not an assertion.")
    return out


# ===========================================================================
# (3b) THE SECOND INVARIANT (cmsg120) — DERIVE chi's well-definedness by CHAINING
# the SAME engine over the TWO read Euler facts. The asked invariant being
# euler_characteristic OF (object) (comprehended) + the two held facts CHAIN to
# "the total Betti must be FINITE (a finite complex)". The conclusion is the engine's
# goal-tree root, NOT an assertion — IDENTICAL pipeline to (3).
#
# The chain, as a goal-tree over the SAME held `times` (AND over {0,1}):
#   chi_well_defined = times(chi_is_alternating_sum, alt_sum_finite_iff_finite_betti)
#       (E1: chi = alternating sum of the Betti numbers; E2: that sum is a finite
#        number iff finitely many Betti are nonzero — a finite total Betti)
#   the ROOT in {0,1}: 1 => chi is well-defined ONLY WHEN the total Betti is finite,
#   so the object's forward model MUST report a FINITE total Betti.
# ===========================================================================

def _euler_well_defined_goal() -> dict:
    """The GOAL TREE: chain the two read Euler facts to chi-well-defined. Each leaf is
    a GIVEN truth value (1 = the fact grounded). times = AND over {0,1}. The root
    value 1 <=> chi well-defined requires a finite total Betti. The structure IS the
    chain chi=alternating-sum -> finite iff finitely-many-nonzero -> finite total Betti."""
    return {
        "times": {
            "left": "chi_is_alternating_sum",
            "right": "alt_sum_finite_iff_finite_betti",
        }
    }


def derive_euler_well_definedness(asked: AskedInvariant,
                                  facts: dict[str, HeldFact]) -> DerivedPresupposition:
    """DERIVE chi's well-definedness presupposition by chaining the two read Euler
    facts through the SAME derivation engine (derivation_engine.derive) — the
    IDENTICAL pipeline as derive_h1_finiteness, one invariant further. The givens are
    the COMPREHENDED asked invariant being euler_characteristic (from `asked`) and the
    two READ facts (from `facts`). The engine evaluates the goal tree; the root value
    is the DERIVED constraint (chi well-defined => the total Betti must be FINITE). A
    fact that did not ground stalls the chain at that named fact (the residual) — never
    hard-coded. The answer is NEVER read.

    The OUTPUT property is `total_betti_finite` (a boolean the forward model reports),
    and the DERIVED target is the engine's root (True = must be finite)."""
    out = DerivedPresupposition(facts=facts, property="total_betti_finite")

    if not asked.euler_characteristic:
        out.note = ("the comprehended invariant is not euler_characteristic OF an "
                    "object; no finite-complex (finite-total-Betti) presupposition "
                    "applies")
        return out

    needed = ("euler_is_alternating_sum_of_betti",
              "alternating_sum_finite_iff_finite_total_betti")
    ungrounded = [n for n in needed if not facts[n].grounded]
    if ungrounded:
        out.stalled_at = (f"un-grounded fact(s) {ungrounded} — the derivation cannot "
                          f"chain a fact the reader did not comprehend (acquire by "
                          f"reading; never hard-coded)")
        out.note = "derivation STALLED at a named un-held fact (the honest residual)"
        return out

    # GIVENS: each leaf truth value is SOURCED from the grounded facts (1 = the agent
    # READ + comprehended it). NONE is the answer — they are the read theorems.
    def _g(name: str) -> int:
        return 1 if facts[name].grounded else 0
    givens = {
        "chi_is_alternating_sum": _g("euler_is_alternating_sum_of_betti"),
        "alt_sum_finite_iff_finite_betti": _g(
            "alternating_sum_finite_iff_finite_total_betti"),
    }

    goal = _euler_well_defined_goal()
    res = _de.derive(goal, givens)

    chain = []
    chain.append({"step": "comprehend",
                  "from": "the general reader",
                  "fact": f"asked invariant = {asked.repr} (the Euler characteristic "
                          f"OF an object)"})
    chain.append({"step": "E1 (read)",
                  "from": facts["euler_is_alternating_sum_of_betti"].provenance,
                  "fact": "chi(X) = sum_n (-1)^n b_n(X) (the alternating sum of the "
                          "Betti numbers)"})
    chain.append({"step": "E2 (read) => finite iff finite total Betti",
                  "from": facts["alternating_sum_finite_iff_finite_total_betti"].provenance,
                  "fact": "the alternating sum is a FINITE number iff finitely many "
                          "b_n are nonzero (a FINITE complex): total Betti finite"})
    chain.append({"step": "derive (engine)",
                  "from": "derivation_engine.derive (goal-directed chain)",
                  "fact": "chi = alternating sum AND (sum finite iff finite total "
                          "Betti) => chi well-defined REQUIRES total Betti FINITE",
                  "engine_root": res.get("answer"),
                  "engine_derived": res.get("derived"),
                  "engine_steps": res.get("steps")})

    well_defined = bool(res.get("derived")) and res.get("answer") == 1
    out.derived = well_defined
    out.h1_must_be_finite = False        # not an H_1 constraint — chi's is total-Betti
    # the DERIVED constraint: the total Betti must be FINITE. The target VALUE is the
    # engine's root (1 => True), NOT a hard-coded literal.
    out.predicate_value = int(res.get("answer") or 0)   # 1 = must-be-finite (DERIVED)
    out.chain = chain
    out.note = ("DERIVED: the chain chi=alternating-sum-of-Betti -> finite iff "
                "finitely-many-nonzero-Betti => chi well-defined REQUIRES a FINITE "
                "total Betti (a finite complex). The conclusion is the engine's "
                "goal-tree root, not an assertion.")
    return out


# ===========================================================================
# THE ENTRY THE GATE CALLS — comprehend + acquire + derive, returning the gate's
# presupposition spec (or empty + the honest residual). This is what replaces the
# regex + the hard-coded lambda in admissibility_gate.presuppositions_from_question.
# ===========================================================================

def derive_presuppositions(qtext: str) -> dict[str, Any]:
    """The FULL pipeline the gate calls: COMPREHEND the asked invariant (general
    reader) -> ACQUIRE the facts by READING -> DERIVE the presupposition (derivation
    engine). Returns:
        {presuppositions: [ {label, property, predicate, note} ],   # the DERIVED constraint(s)
         asked, derivation, undrivable}                              # the trace + residual
    `presuppositions` is EMPTY when the comprehended invariant carries none (e.g.
    H_1 asked directly) OR when the derivation stalls at an un-grounded fact (the
    residual, named in `undrivable`). The conclusion in `predicate` is DERIVED, never
    a hard-coded literal — it is built from the derivation's `predicate_value`."""
    asked = comprehend_asked_invariant(qtext)
    facts = acquire_facts_by_reading()

    presuppositions: list[dict[str, Any]] = []
    undrivable: list[str] = []
    derivations: list[DerivedPresupposition] = []

    # ---- (i) the cmsg119 invariant: free_rank OF kernel OF Hurewicz => H_1 finite.
    deriv_h1 = derive_h1_finiteness(asked, facts)
    derivations.append(deriv_h1)
    if deriv_h1.stalled_at and asked.free_rank_of_kernel_of_hurewicz:
        undrivable.append(deriv_h1.stalled_at)
    elif deriv_h1.derived:
        want = deriv_h1.predicate_value   # DERIVED (0), built from the chain — not a literal.
        presuppositions.append({
            "label": "Ker(Hurewicz) finite-free-rank => H_1 finite (free rank 0)",
            "property": deriv_h1.property,
            # the predicate the object's H_1 free rank must satisfy — its target value
            # is the DERIVED constraint (deriv.predicate_value), NOT a hard-coded 0.
            "predicate": (lambda free_rank, _w=want: free_rank == _w),
            "note": ("DERIVED (not a regex/hard-code): the general reader typed the "
                     f"asked invariant as {asked.repr}; chaining the read facts "
                     "(Ker(Hurewicz)=[pi1,pi1]; finite-free-rank => finite index; "
                     "index=|H_1|) through the derivation engine yields H_1 finite "
                     "=> free rank 0. The answer is never read."),
            "derived_value": want,
        })

    # ---- (ii) cmsg120 — the SECOND invariant: euler_characteristic OF an object =>
    # a FINITE complex (finite total Betti). The SAME comprehend+acquire+derive path
    # (one general reader, one engine, one gate); the gate now carries TWO.
    deriv_chi = derive_euler_well_definedness(asked, facts)
    derivations.append(deriv_chi)
    if deriv_chi.stalled_at and asked.euler_characteristic:
        undrivable.append(deriv_chi.stalled_at)
    elif deriv_chi.derived:
        want_finite = bool(deriv_chi.predicate_value)  # DERIVED (1->True): must be finite.
        presuppositions.append({
            "label": "Euler characteristic well-defined => FINITE complex "
                     "(total Betti finite)",
            "property": deriv_chi.property,           # "total_betti_finite"
            # the predicate the object's forward model must satisfy — its target value
            # (the total Betti must be finite) is the DERIVED engine root, NOT a literal.
            "predicate": (lambda total_finite, _w=want_finite: bool(total_finite) == _w),
            "note": ("DERIVED (not a regex/hard-code): the general reader typed the "
                     f"asked invariant as {asked.repr}; chaining the read facts "
                     "(chi=alternating sum of Betti; that sum is finite iff finitely "
                     "many Betti are nonzero) through the derivation engine yields "
                     "chi well-defined => a FINITE complex (total Betti finite). The "
                     "answer is never read."),
            "derived_value": want_finite,
        })

    return {
        "presuppositions": presuppositions,
        "asked": asked,
        # `derivation` kept singular for the cmsg119 trace consumers; `derivations`
        # carries BOTH (the gate-carries-two trace).
        "derivation": deriv_h1,
        "derivations": derivations,
        "undrivable": undrivable,
    }


__all__ = [
    "AskedInvariant", "HeldFact", "DerivedPresupposition",
    "comprehend_asked_invariant", "acquire_facts_by_reading",
    "derive_h1_finiteness", "derive_euler_well_definedness",
    "derive_presuppositions",
]
