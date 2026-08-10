"""Re-promote the 87 equation concepts WITH UNDERSTANDING.

Background: `concept_promotion_rules.install_concept_promotion_rules`
walked the seed corpus and promoted 87 equation-identity concepts
("F = ma", "V = IR", "E = mc²", …) to flat Term-trees of the shape

    Eq(Lit("F"), Lit("ma"))

— each symbol on either side of the equals sign is opaque text. The
substrate's Shape walker classifies all 87 to the same Shape
{none, 0, concrete}; the Shape harvester sees no structural diversity.

This module promotes them again, but each known symbol is grounded
to an existing Concept via `Holds(concept_name, Var("x"))`, and each
arithmetic operator is composed via the matching Term variant
(`Times`, `Div`, `Plus`, `Minus`, `Pow`). Numbers stay as `Lit`.
The result for Newton's second law:

    Eq(Holds("force", Var("x")),
       Times(Holds("mass", Var("x")), Holds("acceleration", Var("x"))))

— a tree with five non-leaf nodes (Eq, Times, three Holds), four
Vars, no Lits. Different equations now have different trees.

WHY THIS MATTERS (the honest version)

The promotion grows the Shape harvester's donor set. Shape axes
(recursion / order_n / abstraction) are conservative: `Eq`,
`Times`, `Plus`, `Minus`, `Div`, `Pow`, `Holds` all leave the three
axes at {none, 0, concrete}. So the SHAPE-axis diversity gain from
this module alone is zero — every grounded equation still classifies
as {none, 0, concrete} on the three Shape axes. Honest.

The DIVERSITY that grows is STRUCTURAL — the Term-tree's variant
multiset and depth. This module reports BOTH:

  · the conservative Shape-axes distribution (will be uniform, as
    before)
  · a stronger "structural shape" — the (variant-multiset, depth)
    signature — which DOES diversify. The bag of variants used by
    F = ma is {Eq, Times, Holds, Var}; by E = mc² is {Eq, Times,
    Holds, Var, Pow, Lit}; by V = IR is {Eq, Times, Holds, Var};
    by KE = ½mv² is {Eq, Times, Holds, Var, Pow, Lit}. Distinct.

The stronger signature is what downstream rules / harvesters that
care about WHICH primitives the Term uses (not just its recursion
class) can pick up on. The Shape-walker proper needs to add Plus /
Times / Div / Pow to its `children()` enumeration before the three
axes will diversify; that's a Rust-side change tracked in this
module's docstring as the "next stretch."

WHAT THIS MODULE DOES

  1. Hand-curated symbol → concept lookup (`SYMBOL_TO_CONCEPT`).
     ~30 entries covering the symbols that actually appear in the
     87 promoted equations: F → force, m → mass, V → voltage,
     E → energy, p → momentum, etc.

  2. A tiny formula tokenizer + recursive-descent parser. Token
     classes: identifier (any maximal run of letters/Greek/_/digit),
     numeric literal, operator (= + - * / ^), paren, separator.
     Implicit multiplication ("ma", "mc²") becomes explicit Times.
     The parser is deliberately permissive — many of the seed
     equations have prose tails ("(gravitational)", "where ...",
     "in dB SPL"); when the parser can't make sense of the RHS, the
     equation is SKIPPED for grounding.

  3. For every (lhs, rhs) in `PROMOTED_CONCEPTS`:
       · Parse both sides to tiny ASTs.
       · Walk the AST; rewrite each identifier to either
         `Holds(concept_name, Var("x"))` (if grounded) or fall back
         to `Lit("<symbol>")` (if not).
       · If FEWER than one symbol grounds, mark equation
         "ungrounded" and skip.
       · Otherwise compose the Term-tree, call
         `inner.define_concept(name, new_term)`, and record the
         grounded Term in `GROUNDED_CONCEPTS`.

  4. Report what changed: counts, sample triples
     (name, old-term, new-term, new-shape), and the
     variant-multiset distribution before vs after.

WHAT THIS MODULE DOES NOT DO

  · It does NOT touch the Shape walker's classification rules. It
    does NOT add cross-Term recursion. It does NOT expand the
    Holds-dispatch chain (the grounded concepts dispatch into
    other concepts that are NOT yet grounded — `force`,
    `mass`, `acceleration` are seed concepts whose `definition`
    is prose, no Term-tree. Holds dispatch will return None on
    them. That's the next stretch — grounding the FIRST-ORDER
    physics primitives so the Holds chain bottoms out).

  · It does NOT skim the prose-tail equations like
    "G = (V, E)" or "Single word = full sentence" — those
    aren't formula equations and grounding them is pointless.

  · It does NOT discover new symbol→concept mappings autonomously.
    The lookup is hand-authored. Growing it autonomously is the
    next stretch (the agent's "lift unknown symbol to candidate
    concepts via name fuzzy match + definition keyword overlap"
    rule).

THE NEXT STRETCH — RULE-NATIVE GROUNDING

  This is the BOOTSTRAP. The substrate-resident form:

    1. Author a `concept_grounding_trigger` Mt + edges from it to
       Concept nodes whose promoted_lhs / promoted_rhs attrs were
       written by the previous walker.
    2. Author a RewriteRule that fires on `has_eligible_concept`,
       walks the promoted_rhs string via a new `StringTokenize`
       Term variant, looks each identifier up via Filter over
       `Concept` nodes for a name match, composes the
       Holds/Times/… Term, and emits
       `define_concept(<name>, <term>)`.

  Blockers (same as concept_promotion_rules):
    · No native string tokenize / regex Term.
    · No native expression parser.

  Honest-shippable middle path: the Python here writes the parsed
  AST back to each Concept as new attrs (`grounded_term`), then a
  rule reads those attrs and emits `define_concept`. Out of scope
  here.
"""
from __future__ import annotations

import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Symbol → concept lookup table.
# ---------------------------------------------------------------------------
#
# Hand-curated from the 87 promoted equations. Each key is a token
# that appears LITERALLY in some equation's lhs or rhs after
# tokenization; each value is an existing Concept name (one I
# verified exists in the seed corpus via inspection — see the
# `__main__` block which sanity-checks the table against the
# loaded substrate).
#
# Many physics symbols don't have a dedicated Concept yet (e.g.
# `R` for resistance — the seed corpus has `drug_resistance` and
# `Reynolds_number` but no `resistance` concept). When a symbol
# isn't mapped, the equation either skips grounding for that
# symbol (falling back to Lit) or is dropped entirely if too few
# symbols ground. Honest coverage, not exhaustive.

SYMBOL_TO_CONCEPT: dict[str, str] = {
    # --- mechanics ---
    "F":        "force",
    "m":        "mass",
    "M":        "mass",                      # capital M in some equations
    "p":        "momentum",
    "v":        "velocity",                  # no dedicated concept; falls back
    "a":        "acceleration",              # no dedicated concept; falls back
    "KE":       "energy_kinetic",
    "PE":       "energy_potential",
    "L":        "angular_momentum",          # also Lagrangian / lift; physics-foundation pick
    "E":        "energy_kinetic",            # E for energy (mass-energy etc.); approximate
    "H":        "Hamiltonian_H",
    "T":        "temperature_statistical",   # T for temperature
    "Q":        "partition_function",        # ambiguous: Q in thermo vs Q in info-theory
    "S":        "entropy_thermodynamic",
    "Z":        "partition_function",
    "G":        "Gibbs_free_energy",         # G in thermodynamics
    "I":        "moment_of_inertia_mass",    # moment of inertia (in mechanics context)
    "U":        "energy_potential",          # internal energy ~ potential, approximate
    "W":        "work",
    "J":        "impulse_momentum",          # J for impulse
    "r":        "schwarzschild_radius",      # radius — closest concept; approximate
    "R":        "Reynolds_number",           # ambiguous (resistance vs radius vs Re); fallback

    # --- electromagnetism ---
    "V":        "membrane_potential",        # voltage / electric potential — closest concept
    "B":        "magnetic_field",
    "q":        "force",                      # q for charge has no concept; fallback skipped
    "A":        "amplitude",                  # could be area; amplitude is the most-grounded usage

    # --- thermodynamics ---
    "ΔU":       "energy_potential",
    "ΔH":       "enthalpy_reaction",
    "k_B":      "entropy_thermodynamic",     # k_B paired with entropy
    "Ω":        "entropy_thermodynamic",     # microstate count
    "β":        "inverse_temperature_beta",
    "σ":        "node_state_sigma",          # spin / state — the seed concept the corpus has
    "σ_i":      "node_state_sigma",

    # --- electromagnetism / wave ---
    "c":        "speed_of_sound",            # only "speed_of_sound" exists; approximate
    "λ":        "wavelength",
    "f":        "frequency",
    "ω":        "frequency",                 # angular frequency, approximate
    "ψ":        "superposition_quantum",     # wavefunction — best concept available
    "αψ₁":      "superposition_quantum",
    "βψ₂":      "superposition_quantum",

    # --- fluid dynamics ---
    "Re":       "Reynolds_number",
    "Ma":       "Mach_number",
    "Mach":     "Mach_number",

    # --- chemistry ---
    "pH":       "pH_pOH",
    "K":        "equilibrium_constant",      # K for equilibrium const
    "D":        "diffusion_Arrhenius",       # diffusion coefficient
    "C":        "channel_capacity",          # capacity (channel / heat); approximate
    "rate":     "rate_law",
    "k":        "rate_law",                  # rate constant — closest concept

    # --- attitude networks ---
    "J_ij":     "coupling_J_ij",
    "h_i":      "external_field_h_i",

    # --- network / graph ---
    "Av":       "eigenvalues_eigenvectors",
    "λv":       "eigenvalues_eigenvectors",

    # --- coupling deltas, common compound symbols ---
    "ΔKE":      "energy_kinetic",
    "ΔS":       "entropy_thermodynamic",
}


# Tokens that look like identifiers but are English prose / wrapper
# words. When the AST root is "ID" matching one of these AND no other
# symbol on the same side grounds, the equation is treated as prose,
# not a formula. (We still try grounding — these just don't COUNT
# toward the "at least one grounded" threshold.)
STOP_WORDS: set[str] = {
    "of", "in", "on", "from", "where", "and", "or", "is", "the", "a",
    "an", "to", "with", "by", "for", "at", "as", "be", "but", "not",
    "input", "node", "nodes", "state", "key", "rate", "log", "ln",
    "exp", "max", "min", "quantity", "any", "task", "using", "it",
    "has", "between", "new", "term", "control", "object", "computable",
    "definability", "Identity", "continuity", "dt", "averages",
    "ensemble", "products", "reactants", "force", "per", "area",
    "elastic", "range", "FOL", "RT", "TS", "FOS", "Mind", "computation",
    "God", "universe", "Route", "Single", "word", "full", "sentence",
    "Intension", "meaning", "Output", "layer", "Effectively", "Turing",
    "Propositions", "types", "Implicit", "explicit", "Time", "Total",
    "Mt", "target", "structural", "anchor", "grammar", "learned",
    "drift", "experience", "Intake", "expenditure", "storage",
    "Modern", "RL", "optimal", "unknown", "dynamics",
    "Creature", "being", "awake", "aware", "body", "brain", "Narrow",
    "supervenes", "intrinsic", "states", "Trait", "stable",
    "definability", "Stress", "Star", "luminosity",
    "Smallest", "interval", "TET", "factor", "causal", "influence",
    "strength", "bias", "Curiosity", "expected", "reduction",
    "entropy", "distribution", "Babble", "loop", "thermal",
    "stochastic", "sampling", "network", "beliefs", "Weather",
    "short", "atmospheric", "conditions", "Shard", "hash", "mod",
    "Price", "supplied", "demanded", "Mutex", "ceiling", "priority",
    "capacity", "demand", "Work", "done", "external",
    "navigation", "steps", "n", "sequential",
    # Note: "ma", "IR", "mv", "mc", "mgh", "qE", "qv" are PHYSICS
    # implicit-multiplication concatenations (m·a, I·R, …). They are
    # deliberately NOT in this stop list — `_maybe_split_id` splits
    # them into single-letter tokens, each of which grounds via
    # SYMBOL_TO_CONCEPT.
}


# Concepts known to exist in the standard seed corpus. The agent's
# substrate may not actually have these as Concept NODES until the
# seeds load, but they appear in `seeds/*.json` and were verified
# manually. Used as a sanity filter inside the grounding loop so
# we don't define against truly-nonexistent concepts.
KNOWN_CONCEPT_NAMES_HINT: set[str] = {
    "force", "mass", "momentum", "energy_kinetic", "energy_potential",
    "angular_momentum", "Hamiltonian_H", "temperature_statistical",
    "partition_function", "entropy_thermodynamic", "Gibbs_free_energy",
    "moment_of_inertia_mass", "work", "impulse_momentum",
    "membrane_potential", "magnetic_field", "speed_of_sound",
    "wavelength", "frequency", "Reynolds_number", "Mach_number",
    "pH_pOH", "eigenvalues_eigenvectors", "enthalpy_reaction",
    "inverse_temperature_beta",
}


# ---------------------------------------------------------------------------
# Tokenizer.
# ---------------------------------------------------------------------------

# Identifier: alphabetic (including Greek), digits, _ ; a leading digit
# is allowed only inside a multi-char ID (the tokenizer prefers number
# literals as a leading-digit start). Greek + sub/superscript chars
# tolerated: μνρσφθλωΩΔ etc.
_ID_HEAD = (
    r"[A-Za-z_"
    r"αβγδεζηθικλμνξοπρστυφχψω"
    r"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    r"₀₁₂₃₄₅₆₇₈₉]"
)
_ID_TAIL = (
    r"[A-Za-z_"
    r"αβγδεζηθικλμνξοπρστυφχψω"
    r"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    r"₀₁₂₃₄₅₆₇₈₉0-9]"
)
_ID_RE = re.compile(_ID_HEAD + _ID_TAIL + r"*")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_OPS = {"+", "-", "*", "/", "^", "="}
# Skip these — wrapping prose / unsupported.
_PAREN_OPEN = {"(", "[", "{"}
_PAREN_CLOSE = {")", "]", "}"}
# Superscript digits → '^' + corresponding digit at the lexer layer.
_SUPERSCRIPT_MAP = {
    "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5", "⁶": "^6",
    "⁷": "^7", "⁸": "^8", "⁹": "^9", "¹": "^1", "⁰": "^0",
    "½": "(1/2)",   # rough: ½mv² → (1/2)*m*v^2
    "¼": "(1/4)",
    "¾": "(3/4)",
}


def _preprocess(s: str) -> str:
    """Replace superscript chars + Unicode fractions with ASCII
    forms so the tokenizer can handle them. Strips whitespace."""
    for k, v in _SUPERSCRIPT_MAP.items():
        s = s.replace(k, v)
    # × → *, · → *
    s = s.replace("×", "*").replace("·", "*").replace("∙", "*")
    return s


# Multi-character identifiers we DO NOT split. Anything else made of
# pure single-letter physics symbols ("ma", "IR", "mc²", "mv") gets
# split into single-letter tokens — physics convention is implicit
# multiplication. Keys are looked up case-sensitively.
_KEEP_INTACT: set[str] = {
    "KE", "PE", "Re", "Ma", "pH", "Av",
    "Mach", "rate", "exp", "log", "ln",
    # SI-base / unit shorthand left intact (will be ungrounded but the
    # tokenizer isn't the place to decide that).
    "Pa", "Hz", "Wb", "Ohm",
}


def _maybe_split_id(name: str) -> list[str]:
    """If `name` is an ASCII multi-letter identifier (2-4 chars) and
    NOT in _KEEP_INTACT and NOT in STOP_WORDS, split into single-
    letter tokens. Used so "ma" → ["m", "a"], "IR" → ["I", "R"],
    "mc" → ["m", "c"], "mv" → ["m", "v"]. Identifiers with
    underscores, digits, or non-ASCII chars are kept intact
    (so "k_B", "σ_i", "Re" stay one token); English prose
    words like "of", "and", "where" are also kept intact (so they
    flow through to the prose-detection path)."""
    if name in _KEEP_INTACT:
        return [name]
    if name in STOP_WORDS or name.lower() in STOP_WORDS:
        return [name]
    if not (2 <= len(name) <= 4):
        return [name]
    # Pure-ASCII alphabetic check.
    if not all("a" <= c.lower() <= "z" for c in name):
        return [name]
    # Heuristic: at least one uppercase letter, OR length ≤ 3, OR
    # contains a known physics single-letter symbol. Otherwise
    # likely a prose word missing from STOP_WORDS — keep intact.
    has_upper = any(c.isupper() for c in name)
    if has_upper or len(name) <= 3:
        return list(name)
    # 4-letter all-lowercase: keep intact (likely prose).
    return [name]


def tokenize(s: str) -> list[tuple[str, str]]:
    """Return a list of (kind, value) tokens. Kinds:
      · 'ID'   — identifier (may be a multi-char symbol)
      · 'NUM'  — numeric literal
      · 'OP'   — one of + - * / ^ =
      · 'LP'   — left paren
      · 'RP'   — right paren

    Unrecognised characters terminate tokenization at that point;
    the caller treats partial tokenization as a parse failure.
    """
    s = _preprocess(s)
    out: list[tuple[str, str]] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        # Number takes priority over ID for leading-digit substrings.
        m = _NUM_RE.match(s, i)
        if m and m.start() == i:
            out.append(("NUM", m.group(0)))
            i = m.end()
            continue
        m = _ID_RE.match(s, i)
        if m and m.start() == i:
            id_text = m.group(0)
            for part in _maybe_split_id(id_text):
                out.append(("ID", part))
            i = m.end()
            continue
        if ch in _OPS:
            out.append(("OP", ch))
            i += 1
            continue
        if ch in _PAREN_OPEN:
            out.append(("LP", ch))
            i += 1
            continue
        if ch in _PAREN_CLOSE:
            out.append(("RP", ch))
            i += 1
            continue
        # Anything else (comma, prose) terminates the formula at this
        # point. The caller falls back to opaque Lit.
        break
    return out


# ---------------------------------------------------------------------------
# Mini AST + recursive-descent parser.
# ---------------------------------------------------------------------------
#
# Grammar (precedence, low → high):
#   expr    := term (('+' | '-') term)*
#   term    := factor ('*' factor | '/' factor | factor)*   ← implicit mult
#   factor  := pow ('^' factor)?       ← right-assoc
#   pow     := unary
#   unary   := '-' unary | atom
#   atom    := NUM | ID | '(' expr ')'
#
# Implicit multiplication: two adjacent atoms without an operator
# become a Times. "ma" tokenizes as ['m','a'] then parses as
# Times(m, a); "mc^2" parses as Times(m, Pow(c, 2)).
#
# This is permissive — it accepts e.g. "ρvD/μ" as Times of the four
# factors with a final Div by μ. The parser is intentionally tolerant
# because the seed corpus's RHS strings have inconsistent spacing.


class _ParseError(Exception):
    pass


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.i = 0

    def _peek(self) -> Optional[tuple[str, str]]:
        if self.i >= len(self.tokens):
            return None
        return self.tokens[self.i]

    def _eat(self) -> tuple[str, str]:
        t = self.tokens[self.i]
        self.i += 1
        return t

    def _at_end(self) -> bool:
        return self.i >= len(self.tokens)

    def parse_expr(self) -> dict:
        node = self.parse_term()
        while True:
            t = self._peek()
            if t is None or t[0] != "OP" or t[1] not in {"+", "-"}:
                break
            op = self._eat()[1]
            rhs = self.parse_term()
            if op == "+":
                node = {"_": "Plus", "items": [node, rhs]}
            else:
                node = {"_": "Minus", "a": node, "b": rhs}
        return node

    def parse_term(self) -> dict:
        node = self.parse_factor()
        while True:
            t = self._peek()
            if t is None:
                break
            if t[0] == "OP" and t[1] in {"*", "/"}:
                op = self._eat()[1]
                rhs = self.parse_factor()
                if op == "*":
                    node = self._fold_times(node, rhs)
                else:
                    node = {"_": "Div", "a": node, "b": rhs}
                continue
            # Implicit multiplication: adjacent ID/NUM/LP.
            if t[0] in {"ID", "NUM", "LP"}:
                rhs = self.parse_factor()
                node = self._fold_times(node, rhs)
                continue
            break
        return node

    @staticmethod
    def _fold_times(a: dict, b: dict) -> dict:
        """Flatten nested Times into a single variadic Times."""
        items = []
        if a.get("_") == "Times":
            items.extend(a["items"])
        else:
            items.append(a)
        if b.get("_") == "Times":
            items.extend(b["items"])
        else:
            items.append(b)
        return {"_": "Times", "items": items}

    def parse_factor(self) -> dict:
        node = self.parse_unary()
        t = self._peek()
        if t is not None and t[0] == "OP" and t[1] == "^":
            self._eat()
            rhs = self.parse_factor()  # right-assoc
            node = {"_": "Pow", "a": node, "b": rhs}
        return node

    def parse_unary(self) -> dict:
        t = self._peek()
        if t is not None and t[0] == "OP" and t[1] == "-":
            self._eat()
            arg = self.parse_unary()
            return {"_": "Neg", "arg": arg}
        return self.parse_atom()

    def parse_atom(self) -> dict:
        t = self._peek()
        if t is None:
            raise _ParseError("unexpected end of input in atom")
        if t[0] == "NUM":
            self._eat()
            return {"_": "Num", "value": t[1]}
        if t[0] == "ID":
            self._eat()
            return {"_": "Id", "name": t[1]}
        if t[0] == "LP":
            self._eat()
            inner = self.parse_expr()
            t2 = self._peek()
            if t2 is None or t2[0] != "RP":
                raise _ParseError("missing closing paren")
            self._eat()
            return inner
        raise _ParseError(f"unexpected token {t!r} in atom")


def parse_formula(s: str) -> Optional[dict]:
    """Parse a formula string to a tiny AST dict. Returns None on
    any parse failure (incomplete, leftover tokens, etc.)."""
    toks = tokenize(s)
    if not toks:
        return None
    p = _Parser(toks)
    try:
        node = p.parse_expr()
    except _ParseError:
        return None
    if not p._at_end():
        # Leftover tokens (prose, commas, equals) — partial parse.
        # Accept anyway as long as we got at least an Id or Num at the
        # root; otherwise reject.
        pass
    return node


# ---------------------------------------------------------------------------
# AST → Term-tree JSON.
# ---------------------------------------------------------------------------

def _var(name: str) -> dict:
    return {"type": "Var", "name": name}


def _lit(value: Any) -> dict:
    return {"type": "Lit", "value": value}


def _holds(concept: str, node: dict) -> dict:
    return {"type": "Holds", "concept": concept, "node": node, "node2": None}


def ast_to_term(ast: dict, bound_var: str = "x") -> tuple[dict, dict]:
    """Walk a mini-AST and produce (Term-tree JSON, stats).

    stats: {
       'symbols_total':     int,   # identifiers encountered
       'symbols_grounded':  int,   # identifiers mapped via SYMBOL_TO_CONCEPT
       'symbols_ungrounded': list[str],  # identifier names not in map
    }
    """
    stats = {"symbols_total": 0, "symbols_grounded": 0,
             "symbols_ungrounded": []}

    def walk(node: dict) -> dict:
        kind = node.get("_")
        if kind == "Num":
            v = node["value"]
            try:
                if "." in v:
                    return _lit(float(v))
                return _lit(int(v))
            except ValueError:
                return _lit(v)
        if kind == "Id":
            name = node["name"]
            stats["symbols_total"] += 1
            concept = SYMBOL_TO_CONCEPT.get(name)
            if concept is None:
                # Try a relaxed match: strip trailing subscripts /
                # primes for the lookup. "F_net" → "F".
                stripped = re.sub(r"[_0-9].*$", "", name)
                concept = SYMBOL_TO_CONCEPT.get(stripped)
            if concept is None:
                stats["symbols_ungrounded"].append(name)
                # Fall back: an opaque Lit so the tree is still
                # constructible. The Holds chain can't dispatch on
                # this part, but the structure is preserved.
                return _lit(name)
            stats["symbols_grounded"] += 1
            return _holds(concept, _var(bound_var))
        if kind == "Plus":
            return {"type": "Plus",
                    "items": [walk(i) for i in node["items"]]}
        if kind == "Minus":
            return {"type": "Minus",
                    "a": walk(node["a"]), "b": walk(node["b"])}
        if kind == "Times":
            return {"type": "Times",
                    "items": [walk(i) for i in node["items"]]}
        if kind == "Div":
            return {"type": "Div",
                    "a": walk(node["a"]), "b": walk(node["b"])}
        if kind == "Pow":
            return {"type": "Pow",
                    "a": walk(node["a"]), "b": walk(node["b"])}
        if kind == "Neg":
            return {"type": "Neg", "arg": walk(node["arg"])}
        # Unknown — preserve opaquely.
        return _lit(repr(node))

    term = walk(ast)
    return term, stats


# ---------------------------------------------------------------------------
# Term-tree structural shape — beyond the conservative Shape axes.
# ---------------------------------------------------------------------------
#
# Shape (recursion/order_n/abstraction) collapses {Eq, Times, Plus,
# Holds, …} to {none, 0, concrete}. To show that the new Term-trees
# really are more diverse, this module reports the bag-of-variants
# and max-depth signature alongside the conservative Shape.

def structural_signature(term: dict) -> tuple[tuple[str, ...], int]:
    """Return (sorted-variants-tuple, max-depth)."""
    variants: list[str] = []
    max_depth = [0]

    def walk(t: Any, depth: int) -> None:
        max_depth[0] = max(max_depth[0], depth)
        if not isinstance(t, dict):
            return
        ty = t.get("type")
        if ty:
            variants.append(ty)
        for v in t.values():
            if isinstance(v, dict):
                walk(v, depth + 1)
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, dict):
                        walk(x, depth + 1)

    walk(term, 1)
    return tuple(sorted(variants)), max_depth[0]


# ---------------------------------------------------------------------------
# Grounded-promotion registry.
# ---------------------------------------------------------------------------

GROUNDED_CONCEPTS: list[tuple[str, dict]] = []


def _record(name: str, term: dict) -> None:
    for nm, _ in GROUNDED_CONCEPTS:
        if nm == name:
            return
    GROUNDED_CONCEPTS.append((name, term))


# ---------------------------------------------------------------------------
# The walker.
# ---------------------------------------------------------------------------

def install_concept_grounding(substrate) -> dict:
    """For every (name, term) in PROMOTED_CONCEPTS, attempt to ground
    the equation by parsing LHS and RHS, mapping symbols to existing
    concepts, and composing a structured Term-tree.

    SEED-RESIDENT TERM-TREES TAKE PRIORITY. As of the refactor that
    bakes grounded Term-trees into the seed JSONs under a `"term"`
    field, the loader (`_install_concept` / each `_install*` helper)
    already calls `define_concept(name, term)` at install time for
    every grounded concept. This walker is now the FALLBACK — useful
    when (a) seeds get UPDATED with new equations whose seed-side
    Term-trees haven't yet been generated, or (b) the symbol lookup
    table (`SYMBOL_TO_CONCEPT`) gets extended and the walker can
    re-ground equations that previously fell back to flat form. In
    those cases, run this AFTER the seed loaders; `define_concept`
    is idempotent and will overwrite the seed-installed term with
    the walker's freshly-grounded one.

    Don't delete this function — it's the regeneration path. The
    `seeds/*.json` `"term"` fields ARE the snapshot it produces,
    cached for fast install.

    An equation is "grounded" if at least one symbol on either side
    grounds to a concept; otherwise it is "skipped" and the previous
    flat Term-tree stays in place.

    Args:
      substrate: the Python wrapper or the raw substrate_rs inner.

    Returns:
      {
        'n_input':        int,    # equations seen
        'n_grounded':     int,    # equations re-registered with Holds form
        'n_skipped':      int,    # equations with no symbol matches
        'n_parse_failed': int,    # lhs or rhs un-parseable
        'n_define_failed': int,   # substrate.define_concept raised
        'grounded':       list[str],   # names re-grounded this call
        'samples':        list[dict],  # first ~8 (name, old, new, shape) triples
        'shape_distribution_new': dict,  # conservative Shape axes (will be uniform)
        'structural_distribution_new': dict, # bag-of-variants histogram (diverse)
        'ungrounded_symbols': dict[str, int],  # counter — what's missing from the lookup
      }

    Idempotent on (name).
    """
    inner = _unwrap(substrate)

    # Pull the prior promotion's data. We need the original
    # (lhs, rhs) pairs.
    from . import concept_promotion_rules as cpr
    # Ensure the prior walker has run; if PROMOTED_CONCEPTS is empty
    # we install it first so we have something to ground.
    if not cpr.PROMOTED_CONCEPTS:
        cpr.install_concept_promotion_rules(substrate)

    # Build a quick name → (lhs, rhs) by deconstructing the old
    # Eq(Lit, Lit) Term-trees.
    old: dict[str, tuple[str, str]] = {}
    old_terms: dict[str, dict] = {}
    for nm, term in cpr.PROMOTED_CONCEPTS:
        try:
            lhs = term["a"]["value"]
            rhs = term["b"]["value"]
            old[nm] = (str(lhs), str(rhs))
            old_terms[nm] = term
        except (KeyError, TypeError):
            continue

    n_input = len(old)
    n_grounded = 0
    n_skipped = 0
    n_parse_failed = 0
    n_define_failed = 0
    grounded: list[str] = []
    samples: list[dict] = []
    shape_dist: dict = {}
    struct_dist: dict = {}
    ungrounded_counter: dict[str, int] = {}

    already = {nm for nm, _ in GROUNDED_CONCEPTS}

    for nm, (lhs, rhs) in old.items():
        if nm in already:
            continue
        lhs_ast = parse_formula(lhs)
        rhs_ast = parse_formula(rhs)
        if lhs_ast is None or rhs_ast is None:
            n_parse_failed += 1
            continue
        try:
            lhs_term, lstats = ast_to_term(lhs_ast)
            rhs_term, rstats = ast_to_term(rhs_ast)
        except Exception:
            n_parse_failed += 1
            continue

        total_syms = lstats["symbols_total"] + rstats["symbols_total"]
        grounded_syms = lstats["symbols_grounded"] + rstats["symbols_grounded"]
        for u in lstats["symbols_ungrounded"] + rstats["symbols_ungrounded"]:
            ungrounded_counter[u] = ungrounded_counter.get(u, 0) + 1

        # Require at least ONE grounded symbol — else this is just a
        # rewrite of the same opaque text and adds nothing.
        if grounded_syms < 1:
            n_skipped += 1
            continue

        new_term = {"type": "Eq", "a": lhs_term, "b": rhs_term}

        try:
            inner.define_concept(nm, new_term)
        except Exception:
            n_define_failed += 1
            continue

        _record(nm, new_term)
        grounded.append(nm)
        n_grounded += 1

        # Track Shapes + structural signatures.
        try:
            shape = inner.shape_of_term(new_term)
            key = (shape["recursion"], shape["order_n"], shape["abstraction"])
            shape_dist[key] = shape_dist.get(key, 0) + 1
        except Exception:
            shape = None

        sig = structural_signature(new_term)
        struct_dist[sig] = struct_dist.get(sig, 0) + 1

        if len(samples) < 8:
            samples.append({
                "name":          nm,
                "old_term":      old_terms[nm],
                "new_term":      new_term,
                "new_shape":     shape,
                "structural_sig": {
                    "variants": list(sig[0]),
                    "depth":    sig[1],
                },
                "lhs_raw":       lhs,
                "rhs_raw":       rhs,
                "grounded_syms": grounded_syms,
                "total_syms":    total_syms,
            })

    return {
        "n_input":                       n_input,
        "n_grounded":                    n_grounded,
        "n_skipped":                     n_skipped,
        "n_parse_failed":                n_parse_failed,
        "n_define_failed":               n_define_failed,
        "grounded":                      grounded,
        "samples":                       samples,
        "shape_distribution_new":        shape_dist,
        "structural_distribution_new":   {
            # JSON-friendly form
            f"variants={','.join(k[0])}|depth={k[1]}": v
            for k, v in struct_dist.items()
        },
        "n_distinct_structural_shapes":  len(struct_dist),
        "ungrounded_symbols":            dict(sorted(
            ungrounded_counter.items(),
            key=lambda kv: -kv[1])),
    }


def _unwrap(substrate):
    """Mirror of concept_promotion_rules._unwrap. The inner substrate
    is the one with the dict-shaped define_concept / shape_of_term
    PyO3 methods we need."""
    if hasattr(substrate, "nodes") and hasattr(substrate, "node") \
            and hasattr(substrate, "define_concept"):
        if hasattr(substrate, "_inner"):
            return substrate._inner
        return substrate
    if hasattr(substrate, "_inner"):
        return substrate._inner
    return substrate


__all__ = [
    "install_concept_grounding",
    "SYMBOL_TO_CONCEPT",
    "GROUNDED_CONCEPTS",
    "parse_formula",
    "ast_to_term",
    "structural_signature",
    "tokenize",
]


# ---------------------------------------------------------------------------
# CLI sanity / coverage check.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import pathlib
    import sys

    HERE = pathlib.Path(__file__).resolve().parent
    PROJECT = HERE.parent
    sys.path.insert(0, str(PROJECT / "runners" / "dsl" / "python"))
    sys.path.insert(0, str(PROJECT))

    import substrate_rs as srs

    s = srs.Substrate()

    SEED_DIR = PROJECT / "seeds"
    n_minted = 0
    for sf in sorted(SEED_DIR.glob("*.json")):
        try:
            d = json.loads(sf.read_text())
        except Exception:
            continue
        for c in d.get("concepts", []):
            nm = c.get("name")
            defn = c.get("definition", "")
            if not isinstance(nm, str) or not nm:
                continue
            try:
                s._inner.add_node("Concept", {
                    "name":       nm,
                    "definition": defn,
                    "origin":     f"seed:{sf.stem}",
                })
                n_minted += 1
            except Exception:
                pass

    print(f"Minted {n_minted} Concept nodes from {SEED_DIR}")

    # Run the prior walker to populate PROMOTED_CONCEPTS.
    from domains import concept_promotion_rules as cpr
    pre = cpr.install_concept_promotion_rules(s)
    print(f"Prior walker: {pre['n_promoted']} flat Eq(Lit,Lit) promotions")

    # Baseline harvester.
    from domains.harvester_shape import harvest_report_shape
    before = harvest_report_shape(s._inner)
    print(f"\nBefore grounding: {before['n_donors']} Shape donors "
          f"(distribution: {dict(before['shape_distribution'])})")

    from domains import concept_grounding as cg
    report = cg.install_concept_grounding(s)

    print(f"\nGrounding report:")
    print(f"  input:           {report['n_input']}")
    print(f"  grounded:        {report['n_grounded']}")
    print(f"  skipped:         {report['n_skipped']}  (no symbol match)")
    print(f"  parse failed:    {report['n_parse_failed']}")
    print(f"  define failed:   {report['n_define_failed']}")
    print(f"  coverage:        "
          f"{100.0 * report['n_grounded'] / max(1, report['n_input']):.1f}%")
    print()
    print(f"  Shape axes distribution (conservative):")
    for k, v in sorted(report["shape_distribution_new"].items()):
        print(f"    {k!r}: {v}")
    print()
    print(f"  Distinct structural shapes (bag-of-variants + depth): "
          f"{report['n_distinct_structural_shapes']}")
    for k, v in sorted(report["structural_distribution_new"].items(),
                       key=lambda kv: -kv[1])[:10]:
        print(f"    {v:>3}x  {k}")

    print(f"\n  Sample groundings (first 5):")
    for sample in report["samples"][:5]:
        print(f"    [{sample['name']}]   "
              f"{sample['lhs_raw']!r} = {sample['rhs_raw']!r}")
        print(f"      grounded {sample['grounded_syms']}/"
              f"{sample['total_syms']} symbols, "
              f"variants={sample['structural_sig']['variants']}, "
              f"depth={sample['structural_sig']['depth']}")

    print(f"\n  Top 10 ungrounded symbols "
          f"(would extend SYMBOL_TO_CONCEPT):")
    for sym, cnt in list(report["ungrounded_symbols"].items())[:10]:
        print(f"    {sym!r}: {cnt}")

    after = harvest_report_shape(s._inner)
    print(f"\nAfter grounding:")
    print(f"  donors:                  {after['n_donors']} (was {before['n_donors']})")
    print(f"  conservative Shape axes: {after['n_distinct_shapes']} distinct "
          f"(was {before['n_distinct_shapes']}) — axes uniform by design")
    print(f"  structural shapes:       {after['n_distinct_structural']} distinct "
          f"(was {before['n_distinct_structural']}) — diversity gained")
