"""comprehend_theorem — the THEOREM-COMPREHENSION faculty: read a theorem
STATEMENT (prose + LaTeX) -> PARSE its grammatical/logical structure -> emit a
grounded IMPLICATION (an ANTECEDENT held-predicate over the object => a CONSEQUENT
value) BY GRAMMAR, not hand-wiring. This CROSSES the read-statement -> runnable-
structure wall: cmsg128 READ each cd/ends theorem but the COMPREHENSION (turning
the theorem PROSE into the ImplicationClause) was HAND-WIRED in the builder
functions (a human wrote the clauses). Here the ImplicationClause is PRODUCED BY
PARSING the read text.

THE THEOREM-STATEMENT STRUCTURE the faculty parses (the prompt's shape):

  "[quantifier] [SUBJECT object-class] [MODIFIER with/that PROPERTY]
   [COPULA has/is/iff] [PREDICATE INVARIANT VALUE]"

  "a group WITH TORSION has cohomological dimension INFINITE"
      SUBJECT = group ; MODIFIER = with torsion ; INVARIANT = cohomological
      dimension ; VALUE = infinite -> the implication  has-torsion(G) => cd = inf.
  "a finitely generated group has MORE THAN ONE end IF AND ONLY IF it splits over
   a finite subgroup" -> biconditional: antecedent = splits-over-finite,
      consequent = #ends > 1.

THE PIPELINE (all over GENERAL SEED GRAMMAR — seeds/theorem_constructions.json):

  1. PARSE — apply the seeded STATEMENT CONSTRUCTIONS (general surface forms:
     "X with P has I V", "X that P has V I", "X has V I iff C", "P X has I V", ...)
     to the theorem prose, binding {subject}/{modifier}/{invariant}/{value}/
     {condition}. The copula (has/is/iff) sets the IMPLICATION DIRECTION. This is
     the SAME construction-grammar matcher the held reader uses (literal+slot
     patterns over graph DATA) — adding a theorem-form is adding a construction,
     NOT a per-theorem hardcode.

  2. GROUND — the parsed parts to held machinery:
       · the PROPERTY-MODIFIER -> a HELD PREDICATE (the cmsg128 ground_reductions
         predicates: 'with torsion' -> some_factor_finite_cyclic, 'free' ->
         all_factors_infinite_cyclic_nonempty, ...), composed over the held
         free-product structure. Typed from the property word via the seeded
         property_modifiers atoms.
       · the INVARIANT -> the typed invariant id (the presupposition pipeline's
         invariant typing; the canonical cohomological_dimension / ends key the
         ground_reductions store routes by). Structured invariants are typed by
         the GENERAL READER (construction_grammar.comprehend_structure).
       · the VALUE -> the consequent value (inf / 1 / 2 / 0 / >1 / a number),
         from the seeded value_atoms.

  3. EMIT — the ImplicationClause (antecedent-predicate => consequent-value) — the
     SAME structure cmsg128's builders hand-wrote, now PRODUCED BY PARSING.

THE BAR (the only real check against hand-wiring — GENERALITY). The SAME parser,
from PROSE alone, produces the correct implication for the cd theorem, the ends
theorem, AND a theorem it was NOT tuned for: a PARAPHRASE ('a group that contains
an element of finite order has infinite cohomological dimension') AND a DIFFERENT-
invariant held-out theorem ('a free abelian group of rank n has cohomological
dimension n', 'a nontrivial free product has infinitely many ends'). If it parsed
ONLY the exact cd/ends sentences cmsg128 hand-wired, it would be the gift again.

HONEST. The faculty PARSES the common theorem-forms (general, demonstrated on
paraphrase + held-out) + grounds them; theorem-prose forms NO construction parses
are the NAMED residual (each an addable construction). No over-claim of arbitrary
theorems; no hand-wire (the generality test is the proof).

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL over the agent's held machinery — the
PARSE is the construction-grammar matcher over seed DATA; the property->predicate
grounding reuses the cmsg128 held predicates; the invariant typing reuses the
general reader / the presupposition canonical keys. NO LLM, NO Rust, NO per-theorem
clause-list. See [[ozma_agent_writes_its_own_code]] / ground_reductions (the held
predicates) / construction_grammar (the general reader) / presupposition_derivation
(the invariant typing).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional

from domains import ground_reductions as _gr


_SEED = Path(__file__).resolve().parent.parent / "seeds" / \
    "theorem_constructions.json"


def load_theorem_grammar(path: Path = _SEED) -> dict:
    """Load the THEOREM-STATEMENT grammar (graph DATA): the statement_forms +
    property_modifiers + invariant_atoms + value_atoms. Empty families on a read
    miss (the honest degenerate — nothing parses). The agent's grammar lives here
    as seed data; the faculty applies whichever constructions are seeded."""
    try:
        g = json.loads(Path(path).read_text())
    except Exception:
        return {"statement_forms": [], "property_modifiers": [],
                "invariant_atoms": [], "value_atoms": []}
    return {"statement_forms": g.get("statement_forms", []),
            "property_modifiers": g.get("property_modifiers", []),
            "invariant_atoms": g.get("invariant_atoms", []),
            "value_atoms": g.get("value_atoms", []),
            "antecedent_stopwords": g.get("antecedent_stopwords", [])}


# the HELD PREDICATES the property-modifier atoms BIND (the cmsg128 ground_reductions
# predicates, composed over the held free-product structure). Read off the module by
# name — ONE source of truth (the property word names which held predicate, the
# predicate itself is the agent's held composition, not re-implemented here).
def _held_predicate(name: str) -> Optional[Callable[[dict], bool]]:
    """Resolve a property_modifier atom's `held_predicate` NAME to the held
    predicate function exported by domains/ground_reductions. None if the name is
    not a held predicate (the honest miss — a property whose held predicate the
    agent does not hold; the residual)."""
    fn = getattr(_gr, name, None)
    return fn if callable(fn) else None


# ---------------------------------------------------------------------------
# (0) SURFACE NORMALISATION — a mechanical world-adapter text->tokens translation
# (the SAME kind comprehend_question.plainify is). Lower-case, strip leading
# quantifier articles ('a'/'an'/'every'/'a finitely generated'), collapse
# whitespace, drop a trailing citation/clause. NO meaning decided here — the
# meaning (the parsed structure) is produced by the seeded constructions.
# ---------------------------------------------------------------------------

# leading quantifier/determiner words a theorem opens with — stripped so the
# construction's {subject} slot starts at the object-class head. These are NOT
# part of the meaning (a universally-quantified 'a group' / 'every group' / 'a
# finitely generated group' all assert the same subject class).
_QUANTIFIER_OPENERS = ("for every", "for all", "for each", "every", "each",
                       "any", "a", "an", "the")
# adjuncts inside the subject that qualify the object-class but are not the
# property-modifier antecedent (a generation/presentation hypothesis the theorem
# ranges the whole class under). Dropped to reach the object-class head; the
# property-modifier (with/that/free/...) is what carries the antecedent.
_SUBJECT_ADJUNCTS = ("finitely generated", "finitely presented", "countable",
                     "discrete", "f g", "fg")


def _normalise(statement: str) -> str:
    """Lower-case + collapse whitespace + strip a trailing citation bracket / a
    trailing 'is an invariant ...' descriptor clause + leading filler. A surface
    op only — it neither types an invariant nor grounds a predicate."""
    t = (statement or "").strip()
    # drop a trailing bracketed citation '[Brown VIII.2]' / '(Stallings)'.
    t = re.sub(r"\s*[\[(][^\])]*[\])]\s*$", "", t)
    # cut at the first sentence boundary — a theorem STATEMENT is one clause; a
    # trailing parenthetical reason ('(a finite subgroup ... never vanishes)') is
    # already dropped above; a trailing '; ...' second clause is not the statement.
    t = re.split(r"[;.]\s", t)[0]
    t = re.sub(r"\s+", " ", t).strip().rstrip(".")
    # expand the 'iff' abbreviation to the canonical 'if and only if' biconditional
    # connective the statement-form pattern matches (a surface synonym, not meaning —
    # 'iff' IS 'if and only if'). Word-boundary so it never fires inside another word.
    t = re.sub(r"\biff\b", "if and only if", t)
    return t


def _tok(text: str) -> List[str]:
    """Tokenise to lower-case word tokens (digits kept; '>' / '1' kept as tokens
    for comparative/number values). A HYPHENATED COMPOUND ('torsion-free') is kept
    as ONE token (the hyphen is part of the word) so the atom matcher treats it as a
    single unit — 'torsion-free' is the NEGATION of 'torsion', not the bare property
    word inside it. The matcher works over these."""
    return re.findall(r"[a-z]+(?:-[a-z]+)*|\d+|>", (text or "").lower())


def _strip_leading(toks: List[str], openers) -> List[str]:
    """Strip a single leading multi-word opener phrase (longest-first) from a token
    list. Used to drop the quantifier article and the subject adjunct."""
    low = [t.lower() for t in toks]
    for op in sorted(openers, key=lambda o: -len(o.split())):
        parts = op.split()
        n = len(parts)
        if low[:n] == parts:
            return toks[n:]
    return toks


# ---------------------------------------------------------------------------
# (1) PARSE — apply the seeded STATEMENT CONSTRUCTIONS, binding slots. The matcher
# is the construction-grammar literal+slot matcher (a slot captures one-or-more
# tokens up to the next literal). Longest/most-specific construction first.
# ---------------------------------------------------------------------------

def _match_pattern(pattern: List[str], toks: List[str]) -> Optional[dict]:
    """Match a construction pattern (literals + '{slot}') against the token list.
    A slot greedily captures up to the next literal (or, for the FINAL slot, to the
    end). Returns {slot: captured-surface} on a FULL match, else None. (The same
    semantics as construction_grammar._match, inlined so the faculty is self-
    contained over the theorem grammar.)"""
    binds: dict[str, str] = {}
    i = 0
    n = len(pattern)
    for j, pt in enumerate(pattern):
        is_slot = pt.startswith("{") and pt.endswith("}")
        if is_slot:
            slot = pt[1:-1]
            # the next literal (if any) bounds this slot's capture.
            nxt = None
            for k in range(j + 1, n):
                if not (pattern[k].startswith("{") and pattern[k].endswith("}")):
                    nxt = pattern[k].lower()
                    break
            cap: List[str] = []
            while i < len(toks) and (nxt is None or toks[i].lower() != nxt):
                cap.append(toks[i])
                i += 1
            if not cap:
                return None
            binds[slot] = " ".join(cap)
        else:
            if i >= len(toks) or toks[i].lower() != pt.lower():
                return None
            i += 1
    if i != len(toks):
        return None
    return binds


@dataclass
class ParsedTheorem:
    """The PARSED grammatical structure of a theorem statement (before grounding):
    the subject object-class, the property-MODIFIER (antecedent), the COPULA
    (implication direction), the INVARIANT + VALUE (consequent), and the iff
    CONDITION. `form` names the matched construction (the provenance). parsed=False
    when no construction matches (the honest residual — a theorem-form to acquire)."""
    raw: str = ""
    normalised: str = ""
    parsed: bool = False
    form: str = ""
    copula: str = ""                       # has | is | iff
    subject: str = ""                      # the object-class (or the subjphrase)
    modifier: Optional[str] = None         # the explicit property antecedent
    subjphrase: Optional[str] = None       # an adjective-lead subject span (scanned)
    predicate: Optional[str] = None        # the consequent span (invariant + value)
    condition: Optional[str] = None        # the iff right-hand antecedent
    reason: str = ""

    def line(self) -> str:
        ante = (self.modifier if self.modifier is not None
                else (self.condition if self.condition is not None
                      else self.subjphrase))
        return (f"FORM={self.form}  COPULA={self.copula}  SUBJECT={self.subject!r}  "
                f"ANTECEDENT-SPAN={ante!r}  PREDICATE={self.predicate!r}")


def parse_theorem(statement: str, grammar: Optional[dict] = None) -> ParsedTheorem:
    """PARSE a theorem STATEMENT into its grammatical structure via the seeded
    STATEMENT CONSTRUCTIONS. Strips the leading quantifier article + subject adjunct
    (a surface op), then applies each construction longest/most-specific first,
    binding {subject}/{modifier}/{invariant}/{value}/{condition}. Returns a
    ParsedTheorem; parsed=False when no construction matches (the NAMED residual —
    a theorem-form to acquire as a construction, never hand-wired)."""
    g = grammar or load_theorem_grammar()
    out = ParsedTheorem(raw=statement or "")
    norm = _normalise(statement)
    out.normalised = norm
    toks = _tok(norm)
    # strip a leading quantifier article + a subject adjunct (surface only).
    toks = _strip_leading(toks, _QUANTIFIER_OPENERS)
    toks = _strip_leading(toks, _SUBJECT_ADJUNCTS)
    if not toks:
        out.reason = "empty after normalisation (no statement to parse)"
        return out
    # try the constructions in seed order (the seed is authored most-specific
    # first). The first FULL match wins.
    forms = g.get("statement_forms", [])
    for c in forms:
        pat = c.get("pattern", [])
        binds = _match_pattern(pat, toks)
        if binds is None:
            continue
        out.parsed = True
        out.form = c.get("name", "")
        out.copula = c.get("copula", "has")
        out.subject = binds.get("subject") or binds.get("subjphrase", "")
        msl = c.get("antecedent_slot")
        if msl == "modifier":
            out.modifier = binds.get("modifier")
        elif msl == "condition":
            out.condition = binds.get("condition")
        elif msl == "subjphrase":
            out.subjphrase = binds.get("subjphrase")
        psl = c.get("predicate_slot")
        if psl:
            out.predicate = binds.get(psl)
        out.reason = (f"parsed via construction {out.form!r} "
                      f"(the seeded statement-grammar)")
        return out
    out.reason = (f"NO seeded statement construction parses {norm!r} — the NAMED "
                  f"residual (a theorem-form to acquire as a construction; never "
                  f"hand-wired)")
    return out


# ---------------------------------------------------------------------------
# (2) GROUND — the parsed parts to held machinery.
# ---------------------------------------------------------------------------

def _atom_match(phrase: Optional[str], atoms: List[dict],
                key: str) -> Optional[dict]:
    """Match a parsed phrase against an atom table's `phrases` (substring, longest-
    first), returning the matched atom dict (carrying `key`'s grounded value). The
    longest phrase wins so 'free product' beats 'free', 'free abelian' beats
    'free', 'cohomological dimension' is whole. None = no atom (the honest miss).

    NOTE: substring matching is the right semantics for the INVARIANT / VALUE scans
    (those phrases legitimately carry other words — the predicate span 'infinite
    cohomological dimension' should match the invariant 'cohomological dimension'
    AND the value 'infinite' independently). For the ANTECEDENT, substring matching
    alone is UNSOUND (a known atom buried in a larger unknown qualifier — 'finite'
    inside 'residually finite' — would fire); the antecedent path uses
    `_account_antecedent` (full-modifier accounting) instead."""
    if phrase is None:
        return None
    low = " " + re.sub(r"\s+", " ", phrase.lower()).strip() + " "
    best: Optional[dict] = None
    best_len = -1
    for a in atoms:
        if key not in a:
            continue
        for ph in a.get("phrases", []):
            p = ph.lower().strip()
            if (" " + p + " ") in low or low.strip() == p:
                if len(p) > best_len:
                    best_len = len(p)
                    best = a
    return best


def _account_antecedent(phrase: Optional[str], atoms: List[dict],
                        stopwords) -> tuple[Optional[dict], str]:
    """FULL-MODIFIER ACCOUNTING (the cmsg131 un-accounted-residual principle, applied
    to the antecedent-bearing phrase). A known property atom may ground the antecedent
    ONLY IF the ENTIRE phrase is ACCOUNTED FOR: every token is either (a) covered by a
    matched property-atom phrase, or (b) a structural STOPWORD (article / object-class
    noun head / relative-copula glue / iff-subject pronoun / participle glue — general
    DATA, never a per-phrase atom). If ANY contentful token is left UNACCOUNTED — a
    word that is neither a known atom token nor a stopword — the modifier is NOT
    comprehended -> MISS (None + a named residual). This is exactly the cmsg115
    admissibility gate: an un-accounted contentful word BREAKS the grounding; a known
    token buried in a LARGER unknown qualifier ('finite' inside 'residually finite',
    'torsion-free' inside 'virtually torsion-free') must NOT fire.

    Mechanism: greedily cover the token sequence left-to-right with the LONGEST atom
    phrase that matches at each position (the same longest-first preference _atom_match
    uses, but as a CONTIGUOUS COVER over the tokens, not a free-floating substring).
    The atom whose phrase covers the antecedent's HEAD content is the grounding atom;
    any token outside a covered span and not a stopword is the unaccounted residual.

    Returns (atom, note): (atom, '') when fully accounted (the grounding atom), or
    (None, residual) naming the first unaccounted contentful word. (None, '') for an
    empty phrase."""
    if phrase is None:
        return (None, "no antecedent phrase")
    toks = _tok(phrase)
    if not toks:
        return (None, "empty antecedent phrase")
    sw = set(w.lower() for w in (stopwords or []))
    # build the candidate (phrase-token-list, atom) table, longest phrase first so a
    # longer phrase ('free product', 'an element of finite order') wins over a shorter
    # one ('free', 'finite') at the same position.
    cands: List[tuple[List[str], dict]] = []
    for a in atoms:
        if "held_predicate" not in a:
            continue
        for ph in a.get("phrases", []):
            ptoks = _tok(ph)
            if ptoks:
                cands.append((ptoks, a))
    cands.sort(key=lambda c: -len(c[0]))

    n = len(toks)
    covered = [False] * n          # token i covered by a matched atom phrase
    grounding: Optional[dict] = None
    i = 0
    while i < n:
        # try to match the LONGEST atom phrase starting at position i.
        matched = False
        for ptoks, atom in cands:
            m = len(ptoks)
            if i + m <= n and [t.lower() for t in toks[i:i + m]] == \
                    [t.lower() for t in ptoks]:
                for k in range(i, i + m):
                    covered[k] = True
                # the FIRST atom that covers content is the grounding atom (the
                # antecedent's property head). (The canonical antecedents carry a
                # SINGLE property atom; a second property atom is not expected, but
                # if present the first-covering one is the antecedent head.)
                if grounding is None:
                    grounding = atom
                i += m
                matched = True
                break
        if not matched:
            i += 1

    # every uncovered token must be a stopword, else it is the unaccounted residual.
    for idx, t in enumerate(toks):
        if covered[idx]:
            continue
        if t.lower() in sw:
            continue
        return (None,
                f"unaccounted contentful word {t!r} in antecedent phrase "
                f"{phrase!r} (neither a known property atom nor a structural "
                f"stopword) -> the modifier is NOT fully accounted -> MISS "
                f"(full-modifier accounting: a known atom buried in a LARGER "
                f"unknown qualifier must NOT fire — the NAMED residual)")
    if grounding is None:
        return (None,
                f"no property atom in antecedent phrase {phrase!r} (all tokens "
                f"structural) -> MISS (no antecedent property to ground)")
    return (grounding, "")


def ground_modifier(parsed: ParsedTheorem,
                    grammar: dict) -> tuple[Optional[Callable], str, str]:
    """GROUND the parsed property-MODIFIER (the antecedent) to a HELD PREDICATE.
    Types the modifier phrase via the seeded property_modifiers atoms -> the named
    held predicate (the cmsg128 ground_reductions composition over the held
    structure). For a biconditional the {condition} carries the antecedent property
    (grounded the same way). For the adjective-lead form the SUBJECT PHRASE carries
    the antecedent property ('a free group' -> 'free'). Returns (predicate_fn,
    predicate_name, note); (None, '', residual) on any antecedent that does NOT
    ground.

    THE FALSE-GROUNDING GUARD (cmsg131). There is NO always-true / unconditional
    fallback: a clause MUST carry an antecedent the agent actually extracted+grounded
    from the prose. A subject-class that does NOT ground to a held property atom
    ('a group whose every element ...', a bare 'a group has cd inf') is a MISS, NOT an
    always-true => value clause — manufacturing an always-true antecedent over a
    subject that is not a held predicate asserts the value for EVERY object (a false
    implication: cd=inf for free groups too). A MISS (comprehended=False, named
    residual) is CORRECT; a confident wrong grounding is the failure. The ONLY way to
    ground the antecedent is a property atom that types to a HELD predicate (the
    subject-class-grounds case, e.g. 'free group' -> all_factors_infinite_cyclic_*)."""
    atoms = grammar.get("property_modifiers", [])
    stopwords = grammar.get("antecedent_stopwords", [])
    # the antecedent property phrase: an explicit modifier ('with torsion'), an iff
    # condition ('splits over a finite subgroup'), or — for the adjective-lead form —
    # the SUBJECT PHRASE scanned for a property atom ('a free group' -> 'free'). In ALL
    # three cases the phrase CARRIES THE ANTECEDENT, so FULL-MODIFIER ACCOUNTING
    # applies: a property atom grounds it ONLY IF every contentful word of the phrase
    # is accounted (a matched atom phrase or a stopword); ANY unaccounted contentful
    # word -> MISS (a known atom buried in a larger unknown qualifier must NOT fire).
    explicit = parsed.modifier if parsed.modifier is not None else parsed.condition
    if explicit is not None:
        prop = explicit
        kind = "modifier" if parsed.modifier is not None else "condition"
    elif parsed.subjphrase is not None:
        prop = parsed.subjphrase
        kind = "subject-class"
    else:
        # NO modifier, NO condition, NO subject-phrase span: nothing to ground the
        # antecedent from -> a MISS, NOT an always-true clause (cmsg131: never assert
        # a value with an antecedent that was not extracted from the prose).
        return (None, "",
                "no property-modifier / condition / subject-phrase antecedent span "
                "to ground -> MISS (never an always-true => value clause)")
    # FULL-MODIFIER ACCOUNTING — the principle (cmsg131). The whole antecedent phrase
    # must be accounted; an unaccounted contentful word ('residually' / 'locally' /
    # 'virtually') breaks the grounding -> MISS (not a substring match on 'finite').
    atom, residual = _account_antecedent(prop, atoms, stopwords)
    if atom is None:
        return (None, "",
                f"{kind} {prop!r}: {residual}. NOT an always-true clause and NOT a "
                f"partial substring match: asserting the value here would be a FALSE "
                f"implication over objects the predicate does not actually hold of "
                f"(the NAMED residual — add a property_modifier atom only if the WHOLE "
                f"phrase is a held property).")
    name = atom.get("held_predicate", "")
    fn = _held_predicate(name)
    if fn is None:
        return (None, "",
                f"{kind} {prop!r} -> held predicate {name!r} which the agent does "
                f"NOT hold (the residual)")
    note = (f"{kind} {prop!r} -> property atom (fully accounted) -> held predicate "
            f"{name} (composed over the held free-product structure)")
    return (fn, name, note)


def ground_invariant(parsed: ParsedTheorem,
                     grammar: dict) -> tuple[Optional[str], str]:
    """GROUND the parsed INVARIANT phrase to a TYPED invariant id (the canonical
    cohomological_dimension / virtual_cohomological_dimension / ends key the
    ground_reductions store routes by — the SAME canonical keys the presupposition
    pipeline types). Reuses the GENERAL READER for a structured invariant phrase;
    falls back to the seeded invariant_atoms for the bare-noun invariant head a
    theorem states (quantified over the subject, so stated without an explicit
    object). Returns (invariant_id, note). None = the invariant is implicit in the
    value (a copula-'is' value-as-property theorem) or not typed (residual)."""
    atoms = grammar.get("invariant_atoms", [])
    phrase = parsed.predicate
    if phrase is None:
        return (None, "no predicate span (value-as-property theorem)")
    # try the GENERAL READER first (a structured 'cohomological dimension of X'
    # phrase types to op(args)); fall back to scanning the bare-noun atom table over
    # the predicate span (the invariant is stated bare, quantified over the subject).
    try:
        from domains import construction_grammar as _cg
        typed = _cg.comprehend_structure(phrase)
    except Exception:
        typed = None
    if typed and isinstance(typed.get("structure"), dict):
        op = typed["structure"].get("op")
        if op in ("cohomological_dimension", "virtual_cohomological_dimension",
                  "ends"):
            return (op, f"invariant in {phrase!r} typed via the general reader -> {op}")
    atom = _atom_match(phrase, atoms, "invariant")
    if atom is not None:
        inv = atom.get("invariant")
        return (inv, f"invariant in {phrase!r} -> {inv} (seeded invariant atom)")
    return (None, f"no seeded invariant in {phrase!r} (residual)")


def ground_value(parsed: ParsedTheorem, grammar: dict) -> tuple[Any, str]:
    """GROUND the parsed VALUE phrase to the CONSEQUENT value (inf / 0 / 1 / 2 / >1
    / a symbol). From the seeded value_atoms (substring, longest-first). A SYMBOLIC
    value ('n', the held-out 'free abelian of rank n has cd n') stays the symbol —
    grounded to the object's rank at compute time. Returns (value, note). The
    sentinel _UNGROUNDED on a value the atoms do not type (residual)."""
    atoms = grammar.get("value_atoms", [])
    phrase = parsed.predicate
    if phrase is None:
        return (_UNGROUNDED, "no predicate span parsed (residual)")
    atom = _atom_match(phrase, atoms, "value")
    if atom is not None:
        return (atom.get("value"), f"value in {phrase!r} -> {atom.get('value')!r} "
                f"(seeded value atom)")
    # a bare integer literal in the predicate span the atoms did not enumerate.
    m = re.search(r"(?<![A-Za-z0-9])(-?\d+)(?![A-Za-z0-9])", phrase)
    if m:
        return (int(m.group(1)), f"value in {phrase!r} -> integer literal {m.group(1)}")
    return (_UNGROUNDED, f"no seeded value in {phrase!r} (residual)")


_UNGROUNDED = object()    # sentinel: a value the grammar did not type.


# ---------------------------------------------------------------------------
# (3) EMIT — the grounded ImplicationClause (antecedent-predicate => consequent-
# value). The SAME dataclass cmsg128's builders produced, now PRODUCED BY PARSING.
# ---------------------------------------------------------------------------

@dataclass
class ComprehendedTheorem:
    """The faculty's output: the PARSED structure + the GROUNDED ImplicationClause.
    `clause` is the ground_reductions.ImplicationClause (antecedent held-predicate
    => consequent value) emitted from the parse — None when the parse or a grounding
    failed (the residual, named in `residual`). `provenance` is the inspectable
    PROSE -> parsed -> grounded chain (the proof it is not hand-wired).

    `verified` / `verification` carry the SELF-VERIFY verdict (cmsg133): every
    grounded clause is a CHECKABLE CLAIM, run against the SAME verify-vs-known the
    reduction store holds (ground_reductions.KNOWN_OBJECTS / KNOWN_VALUES). A clause
    whose antecedent FIRES on a known object but whose value MISMATCHES that known is
    SELF-REJECTED (comprehended=False); a clause for an invariant with no known set,
    or whose antecedent fires on NO known, is comprehended-but-UNVERIFIED (flagged,
    NOT asserted as verified). `verified` is True only when the clause faced a known
    and reproduced it."""
    parsed: ParsedTheorem
    clause: Optional["_gr.ImplicationClause"] = None
    comprehended: bool = False
    invariant: Optional[str] = None
    residual: str = ""
    verified: bool = False
    verification: str = ""
    provenance: dict = field(default_factory=dict)


def _value_predicate(value: Any) -> Callable[[dict], Any]:
    """Realise a SYMBOLIC consequent value as a per-object compute. A literal value
    (inf/0/1/2/>1) is returned as-is; the symbol 'n' (the held-out 'rank n => cd n')
    is grounded to the object's RANK (the number of infinite-cyclic free factors),
    composed over the held structure (NOT a baked number)."""
    if value == "n":
        def _n(obj: dict):
            facs = _gr._factors(obj)
            return sum(1 for f in facs if _gr._is_infinite_cyclic(f))
        return _n
    return (lambda obj, _v=value: _v)


# ---------------------------------------------------------------------------
# (3b) SELF-VERIFY — the cmsg117 systemic principle (every grounded claim through
# the gate) applied to comprehend_theorem's OWN output. THE FIX (cmsg133): every
# grounded ImplicationClause is a CHECKABLE CLAIM — "for objects where the antecedent
# holds, invariant = value". It is verified against the SAME verify-vs-known the
# reduction store already holds (ground_reductions.KNOWN_OBJECTS / KNOWN_VALUES — the
# textbook known cd/vcd/ends values, NONE a question's answer), REUSED here, not
# duplicated. Run the clause's antecedent over each KNOWN object for its invariant;
# where the antecedent FIRES, the clause's value MUST equal the known invariant value;
# any mismatch -> the grounding is REJECTED. This is the check that did NOT fire on
# the cmsg130/131 false groundings (the faculty's output bypassed verify-vs-known —
# it ran only DOWNSTREAM on the assembled reduction's canonical clauses, never on a
# per-grounding clause). Now it is WIRED INTO the faculty's output path.
# ---------------------------------------------------------------------------

# the SELF-VERIFY verdicts (a grounded clause's status against verify-vs-known).
_VERIFIED = "verified"        # faced a known, reproduced it
_REJECTED = "rejected"        # mismatched a known where the antecedent fired
_UNVERIFIED = "unverified"    # no known set / antecedent fires on no known (flagged)


def _value_consistent(clause_value: Any, known: Any) -> bool:
    """Is the clause's CONSEQUENT value CONSISTENT with a KNOWN invariant value?
    Exact equality for a definite value (inf / 0 / 1 / 2 / a number). A COMPARATIVE
    consequent ('>1', the biconditional 'more than one end') is satisfied by ANY known
    count greater than one — so '>1' is consistent with the known ends 2 AND the known
    ends inf (both are > 1), NOT only with a literal '>1'. This keeps the self-verify
    HONEST: a comparative consequent is a relation, not an exact value, so verify-vs-
    known checks the relation holds — it must not spuriously reject the TRUE 'more than
    one end' biconditional against the exact-count knowns the store holds."""
    if clause_value == ">1":
        if known == "inf":
            return True
        return isinstance(known, int) and known > 1
    return clause_value == known


def self_verify_clause(antecedent: Callable[[dict], bool], invariant: Optional[str],
                       value: Any,
                       value_compute: Optional[Callable[[dict], Any]] = None
                       ) -> tuple[str, str]:
    """SELF-VERIFY a grounded clause against the EXISTING verify-vs-known (REUSED from
    ground_reductions: KNOWN_OBJECTS / KNOWN_VALUES — NOT a new bespoke check). Run the
    clause's `antecedent` over each KNOWN object that has a known value for `invariant`;
    where the antecedent FIRES, the clause's value (literal `value`, or `value_compute`
    for a symbolic consequent) MUST equal the known. Returns (verdict, note):

      · (_REJECTED, ...)  on ANY known where the antecedent fires but the value !=
        the known invariant value (the cmsg130/131 false-grounding case). The caller
        sets comprehended=False — a self-rejected grounding is an honest MISS.
      · (_UNVERIFIED, ...) when the invariant has NO known set (cannot be checked) OR
        the antecedent fires on NO known object (nothing to check it against). Flagged
        comprehended-but-UNVERIFIED — NOT asserted as verified, NOT silently passed.
      · (_VERIFIED, ...)  when the antecedent fired on >= 1 known and reproduced every
        such known's value (the canonical cd/ends groundings).

    The known values are textbook (NONE a question's answer); the check is the SAME
    verify-vs-known the reduction store runs on its assembled clauses, now run on the
    faculty's per-grounding output BEFORE it is asserted."""
    knowns = _gr.KNOWN_VALUES.get(invariant) if invariant is not None else None
    if not knowns:
        return (_UNVERIFIED,
                f"invariant {invariant!r} has NO known object set (verify-vs-known "
                f"cannot face this clause) -> comprehended but UNVERIFIED (flagged, "
                f"not asserted as verified)")
    fired_on: List[str] = []
    for name, want in knowns.items():
        obj = _gr.KNOWN_OBJECTS.get(name)
        if obj is None:
            continue
        try:
            holds = bool(antecedent(obj))
        except Exception:                          # noqa: BLE001 — a broken antecedent
            return (_REJECTED,
                    f"antecedent raised on known {name!r} -> REJECTED (the clause's "
                    f"composed predicate is not even runnable on a held object)")
        if not holds:
            continue
        got = value_compute(obj) if callable(value_compute) else value
        if not _value_consistent(got, want):
            return (_REJECTED,
                    f"failed self-verification vs known: antecedent fires on {name!r} "
                    f"but value {got!r} != known {want!r} (the grounded clause is a "
                    f"FALSE implication — REJECTED by the SAME verify-vs-known the "
                    f"reduction store holds; the check now fires from INSIDE the "
                    f"faculty, not an external probe)")
        fired_on.append(name)
    if not fired_on:
        return (_UNVERIFIED,
                f"antecedent fires on NO known object for invariant {invariant!r} "
                f"(verify-vs-known has nothing to check it against) -> comprehended "
                f"but UNVERIFIED (flagged, not asserted as verified)")
    return (_VERIFIED,
            f"self-verified vs known: antecedent fires on {fired_on} and value "
            f"{value!r} reproduces every such known invariant value (the SAME "
            f"verify-vs-known the reduction store holds, run on the faculty's output)")


def comprehend_theorem(statement: str,
                       grammar: Optional[dict] = None) -> ComprehendedTheorem:
    """THE FACULTY. Read a theorem STATEMENT -> PARSE (seeded constructions) ->
    GROUND (held predicate + typed invariant + consequent value) -> EMIT the
    grounded ImplicationClause. The clause's antecedent is the HELD predicate the
    property word grounded to (composed over the held structure); its value the
    parsed consequent. The full PROSE -> parsed -> grounded chain is in
    `provenance` (inspectable). Returns a ComprehendedTheorem; comprehended=False +
    a NAMED residual when the parse or a grounding fails (a theorem-form / property
    / invariant / value to acquire — never hand-wired)."""
    g = grammar or load_theorem_grammar()
    parsed = parse_theorem(statement, g)
    out = ComprehendedTheorem(parsed=parsed)
    out.provenance["prose"] = statement
    out.provenance["normalised"] = parsed.normalised
    if not parsed.parsed:
        out.residual = parsed.reason
        return out
    out.provenance["parsed"] = {
        "form": parsed.form, "copula": parsed.copula, "subject": parsed.subject,
        "modifier": parsed.modifier, "subjphrase": parsed.subjphrase,
        "predicate": parsed.predicate, "condition": parsed.condition}

    pred_fn, pred_name, pred_note = ground_modifier(parsed, g)
    inv, inv_note = ground_invariant(parsed, g)
    val, val_note = ground_value(parsed, g)

    grounded = {"antecedent": pred_note, "invariant": inv_note, "value": val_note}
    out.provenance["grounded"] = grounded
    out.invariant = inv

    # a failed grounding is the NAMED residual (never hand-wired around).
    if pred_fn is None:
        out.residual = f"antecedent ungrounded: {pred_note}"
        return out
    # the INVARIANT must ground (the consequent is invariant=value; an ungrounded
    # invariant means the faculty did not actually comprehend the consequent — a
    # NAMED residual, NOT a false-positive 'comprehended' with invariant=None). This
    # guards against a greedy parse that bound a value but no invariant.
    if inv is None:
        out.residual = f"invariant ungrounded: {inv_note}"
        return out
    if val is _UNGROUNDED:
        out.residual = f"value ungrounded: {val_note}"
        return out

    value_compute = _value_predicate(val)
    # the value the theorem assigns: a literal (inf/0/1/2/>1) for the clause `value`
    # field (ground_reductions clauses carry a literal value); a symbolic 'n' value
    # is realised as a per-object compute and the clause carries it via a callable.
    clause_value: Any = val
    ante_span = (parsed.modifier if parsed.modifier is not None
                 else (parsed.condition if parsed.condition is not None
                       else parsed.subjphrase))
    chain = (f"PARSE {statement!r} -> form {parsed.form} (copula {parsed.copula}) "
             f"-> SUBJECT {parsed.subject!r}, ANTECEDENT-SPAN {ante_span!r}, "
             f"PREDICATE {parsed.predicate!r} -> GROUND: antecedent={pred_name}; "
             f"invariant={inv}; value={val!r}.")
    out.provenance["chain"] = chain

    clause = _gr.ImplicationClause(
        antecedent=pred_fn,
        antecedent_name=f"{pred_name} (PARSED from prose, not hand-wired)",
        value=clause_value,
        chain=chain)
    # carry the per-object value compute for the symbolic case (the store's
    # compute() reads `.value`; for symbolic 'n' the caller uses value_compute).
    clause.value_compute = value_compute            # type: ignore[attr-defined]

    # SELF-VERIFY the grounded clause against the EXISTING verify-vs-known (cmsg133 —
    # the systemic check WIRED INTO the faculty's output, the cmsg117 gate applied to
    # comprehend_theorem). A self-REJECTED grounding (its value mismatches a known
    # where its antecedent fires — the cmsg130/131 false-grounding case) is an honest
    # MISS (comprehended=False). An UNVERIFIED grounding (no known set / antecedent
    # fires on no known) is flagged, NOT asserted as verified, and NOT silently passed.
    verdict, vnote = self_verify_clause(pred_fn, inv, clause_value, value_compute)
    out.verification = vnote
    out.provenance["self_verify"] = {"verdict": verdict, "note": vnote}
    if verdict == _REJECTED:
        out.residual = f"self-verify REJECTED the grounding: {vnote}"
        return out
    out.verified = (verdict == _VERIFIED)

    out.clause = clause
    out.comprehended = True
    return out


__all__ = [
    "load_theorem_grammar", "ParsedTheorem", "parse_theorem",
    "ground_modifier", "ground_invariant", "ground_value",
    "ComprehendedTheorem", "comprehend_theorem", "self_verify_clause",
]
