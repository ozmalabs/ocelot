"""Language comprehension — the bridge from text to grounded meaning, built the
way the brain's language network is and run on the SAME engine as everything
else (the rewrite + search engine; cf. KB word reduction, which reduces a chain
— here the chain is reduced UP into structure).

Biologically (Hickok–Poeppel dual stream, mirroring the substrate's vision dual
stream), comprehension is a cascade:
  * orthographic features — characters are the receptors (we start here, not at
    words), each annotated with sub-lexical features (is_alpha/is_digit/…);
  * lexical access (ventral "what" stream) — runs of characters are recognised
    as signs: a Word (form + syntactic category) or a Number (a folded value);
  * composition / Merge (dorsal stream, Broca's) — adjacent constituents combine
    into a parent carrying a composed meaning Term  [next stage];
  * semantic integration — the root meaning Term is handed back to reason over.

Everything is graph-resident: the character chain, the lexicon (signs), and the
recognition/composition rules. Python only ingests text into the graph and turns
the engine's crank. This module is the lexical layer; ``lex`` returns the
constituent sequence a sentence reduces to.

Runs on the Rust-native engine (``substrate_rs``): the rules are installed with
``Substrate.add_rule`` and driven to a fixed point with ``apply_rule_once`` (so
each phase — lexical access, then cleanup — runs its own rule set, the way the
old two-call ``gr.run`` did). No Python rule engine.
"""
from __future__ import annotations

from itertools import product

from substrate_rs import (And, Attr, Eq, Exists, Lit, Neighbours, Not, Or, Plus,
                          Term, Times, TypeOf, Var, _native)

_PUNCT = set(",.?!;:()[]")

_TYPES = ("Anchor", "Char", "Word", "Number", "Lexicon", "Lexeme", "LexSlot",
          "Constituent", "Meaning", "Marker", "Slot", "Arg")
_EDGES = ("next", "entry", "arg", "meaning", "has_slot", "value")


def new_graph():
    """A substrate carrying a permissive grammar for the language schema. The
    Rust engine checks Γ-admissibility on every add; these open productions
    admit the chain/lexicon/meaning shapes this module constructs."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"},
                    "edge_type": e,
                    "tgt": {"type": b, "var": "t"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "language",
                })
    return g


_PARSE_CHAIN_TYPES = ("Anchor", "Char", "Word", "Number",
                     "Constituent", "Marker")
_PARSE_EDGE_TRIPLES = tuple(
    (src, "next", tgt)
    for src, tgt in product(_PARSE_CHAIN_TYPES, repeat=2)
) + (
    ("Constituent", "meaning", "Meaning"),
    ("Constituent", "has_slot", "Slot"),
    ("Meaning", "arg", "Arg"),
    ("Arg", "value", "Meaning"),
)


def _new_parse_graph():
    """Create the parser's exact typed edge grammar, not the public open graph.

    ``new_graph`` remains the permissive language-schema constructor for
    external callers. The hot parser scratch graph only needs the chain and
    argument edges this module actually creates; opening every one of 12 x 12 x
    6 triples costs hundreds of native calls per utterance.
    """
    graph = _native.Substrate()
    for src, edge_type, tgt in _PARSE_EDGE_TRIPLES:
        graph.add_production({
            "src": {"type": src, "var": "s"},
            "edge_type": edge_type,
            "tgt": {"type": tgt, "var": "t"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "language_parser",
        })
    return graph


def _enc(v):
    """Encode a rule-effect value: a Term becomes its JSON (the engine computes
    it at apply time); a literal passes through."""
    return {"__term__": v.to_dict()} if isinstance(v, Term) else v


def _effect(eff):
    kind = eff[0]
    if kind == "add_node":
        _, var, typ, attrs = eff
        return ["add_node", var, typ, {k: _enc(v) for k, v in attrs.items()}]
    if kind == "set_attr":
        _, var, key, val = eff
        return ["set_attr", var, key, _enc(val)]
    return [*eff]


def _rule(name, match, where, effects) -> dict:
    """A rewrite rule in the wire format ``Substrate.add_rule`` parses."""
    return {"name": name,
            "match": [list(m) for m in match],
            "where": where.to_dict() if where is not None else None,
            "effects": [_effect(e) for e in effects]}


def _run(graph, idxs) -> None:
    """Drive the given rule indices to a fixed point — round-robin
    apply_rule_once, so only THIS phase's rules fire (run_rules would also fire
    any other rules installed on the substrate)."""
    progress = True
    while progress:
        progress = False
        for i in idxs:
            if graph.apply_rule_once(i):
                progress = True


def ingest(graph, text: str):
    """Text → a HEAD …next… TAIL chain of Char nodes, each carrying sub-lexical
    features (the orthographic front end). Returns (head, tail)."""
    head = graph.add_node("Anchor", {"id": "head", "symbol": None,
                                     "is_alpha": False, "is_digit": False,
                                     "digit": None, "is_delim": False})
    prev = head
    for i, ch in enumerate(text):
        c = graph.add_node("Char", {
            "id": f"ch{i}", "symbol": ch,
            "is_alpha": ch.isalpha(), "is_digit": ch.isdigit(),
            "digit": int(ch) if ch.isdigit() else None,
            "is_delim": ch.isspace() or ch in _PUNCT})
        graph.add_edge(prev, "next", c, {})
        prev = c
    tail = graph.add_node("Anchor", {"id": "tail", "symbol": None,
                                     "is_alpha": False, "is_digit": False,
                                     "digit": None, "is_delim": False})
    graph.add_edge(prev, "next", tail, {})
    return head, tail


# --- the GRAPH-RESIDENT lexicon: signs the agent learns and grounds ---------
#
# The lexicon is not a Python list — it lives in the graph as Lexeme nodes the
# agent acquires (LLM teaches / agent grounds) and that BOTH comprehension and
# production read. A sign is a Lexeme (form + concept + kind) with Slot children
# carrying its argument structure (role / marker / direction). ``learn_sign`` is
# the acquisition primitive (ground a taught word); ``signs_from_graph`` reads
# the lexicon back into the sign dicts the parser/producer consume — so a word
# taught at runtime is immediately usable in both directions.

# NB: make_lexicon / learn_sign / signs_from_graph operate on WHATEVER graph the
# caller hands them — currently `CuriousAgent.mind_graph`, still a Python
# TypedGraph. They use the generic `_insert_node` / `out_edges` API (no python-
# substrate import) so they keep serving that consumer; they move to the native
# `add_node`/`neighbours` API when the agent's graph does. The rule-engine path
# (comprehend / lex) above is already fully on the Rust-native engine.

def make_lexicon(graph) -> int:
    """An empty graph-resident lexicon (the anchor its Lexemes hang off)."""
    return graph._insert_node("Lexicon", {"id": "lexicon"})


def learn_sign(graph, lexicon, sign: dict) -> int:
    """ACQUIRE a sign — store it as a Lexeme in the graph (form, grounded
    ``concept``, kind, and a Slot per argument). ``sign`` is the same dict shape
    the faculty uses: {form, concept, args:[{role,marker,dir}]} | {form,mark} |
    {form,drop}. The agent's vocabulary grows by learning these, not by code."""
    kind = "mark" if sign.get("mark") else ("func" if sign.get("drop") else "content")
    lex = graph._insert_node("Lexeme", {
        "id": f"lex_{sign['form']}", "form": sign["form"], "kind": kind,
        "concept": sign.get("concept")})
    graph._insert_edge(lexicon, "entry", lex)
    for i, arg in enumerate(sign.get("args", [])):
        slot = graph._insert_node("LexSlot", {
            "id": f"{sign['form']}_arg{i}", "role": arg["role"],
            "marker": arg.get("marker"), "dir": arg.get("dir", "R"), "order": i})
        graph._insert_edge(lex, "arg", slot)
    return lex


def signs_from_graph(graph, lexicon) -> list[dict]:
    """Read the graph-resident lexicon back into sign dicts (the form the parser
    and producer consume). The graph is the source of truth; this is the view."""
    out = []
    for e in graph.out_edges(lexicon, "entry"):
        a = graph.node(e.key.tgt).attrs
        if a["kind"] == "mark":
            out.append({"form": a["form"], "mark": True})
        elif a["kind"] == "func":
            out.append({"form": a["form"], "drop": True})
        else:
            args = sorted(
                (graph.node(s.key.tgt).attrs for s in graph.out_edges(e.key.tgt, "arg")),
                key=lambda sa: sa["order"])
            sign = {"form": a["form"], "concept": a["concept"]}
            if args:
                sign["args"] = [{"role": sa["role"], "marker": sa["marker"],
                                 "dir": sa["dir"]} for sa in args]
            out.append(sign)
    return out


def seed_core_lexicon(graph) -> int:
    """A graph-resident lexicon pre-stocked with `core_lexicon()` — the agent's
    starter vocabulary, now learnable/extensible in the graph."""
    lexicon = make_lexicon(graph)
    for sign in core_lexicon():
        learn_sign(graph, lexicon, sign)
    return lexicon


def _word_rule(form, category) -> dict:
    """Recognition rule: a boundary-delimited run of Chars spelling ``form`` →
    one Word constituent (form + category), spliced into the chain in place of
    its characters (lexical access as a chain rewrite)."""
    p = len(form)
    lv = [f"L{i}" for i in range(p)]
    match = [("X", "next", lv[0])]
    for i in range(p - 1):
        match.append((lv[i], "next", lv[i + 1]))
    match.append((lv[p - 1], "next", "Y"))
    where = And(items=(
        Not(arg=Attr(Var("X"), "is_alpha")),           # left boundary
        Not(arg=Attr(Var("Y"), "is_alpha")),           # right boundary
        *[Eq(a=Attr(Var(lv[i]), "symbol"), b=Lit(form[i])) for i in range(p)]))
    effects = [("add_node", "W", "Word", {"form": form, "category": category}),
               ("add_edge", "X", "next", "W"), ("add_edge", "W", "next", "Y")]
    effects += [("del_node", v) for v in lv]
    return _rule(f"word_{form}", match, where, effects)


def _number_rules() -> list[dict]:
    """Fold a run of digit Chars into one Number constituent (value built
    left-to-right): seed the leftmost digit, then absorb each following digit as
    value·10 + digit."""
    extend = _rule(
        "num_extend",
        match=[("N", "next", "D"), ("D", "next", "Y")],
        where=And(items=(Eq(a=TypeOf(Var("N")), b=Lit("Number")),
                         Attr(Var("D"), "is_digit"))),
        effects=[("set_attr", "N", "value",
                  Plus(items=(Times(items=(Attr(Var("N"), "value"), Lit(10))),
                              Attr(Var("D"), "digit")))),
                 ("add_edge", "N", "next", "Y"), ("del_node", "D")])
    seed = _rule(
        "num_seed",
        match=[("X", "next", "D"), ("D", "next", "Y")],
        where=And(items=(
            Attr(Var("D"), "is_digit"),
            Not(arg=Or(items=(Attr(Var("X"), "is_digit"),
                              Eq(a=TypeOf(Var("X")), b=Lit("Number"))))))),
        effects=[("add_node", "N", "Number", {"value": Attr(Var("D"), "digit")}),
                 ("add_edge", "X", "next", "N"), ("add_edge", "N", "next", "Y"),
                 ("del_node", "D")])
    return [extend, seed]


def _cleanup_rule() -> dict:
    """Splice out delimiter Chars (whitespace / punctuation) once words and
    numbers are recognised, leaving a clean constituent chain."""
    return _rule(
        "drop_delim",
        match=[("X", "next", "S"), ("S", "next", "Y")],
        where=Attr(Var("S"), "is_delim"),
        effects=[("add_edge", "X", "next", "Y"), ("del_node", "S")])


def lexical_rules(forms: list[tuple[str, str]]) -> list[dict]:
    """All recognition rules for the lexicon, longest forms first (longest-match
    lexical access), then number folding."""
    words = [_word_rule(f, cat)
             for f, cat in sorted(forms, key=lambda fc: -len(fc[0]))]
    return words + _number_rules()


def _lex_graph(text: str, forms: list[tuple[str, str]]):
    """Build a native lexical chain for ``text`` using ``forms``."""
    g = _new_parse_graph()
    head, tail = ingest(g, text)
    _run(g, [g.add_rule(r) for r in lexical_rules(forms)])
    _run(g, [g.add_rule(_cleanup_rule())])
    return g, head, tail


def _lex_readback(g, head) -> list[dict]:
    out, cur = [], head
    while True:
        nbrs = g.neighbours(cur, "next")
        if not nbrs:
            break
        nxt = nbrs[0]
        node = g.node(nxt)
        a = node["attrs"]
        if node["type"] == "Word":
            out.append({"kind": "Word", "form": a["form"], "cat": a["category"]})
        elif node["type"] == "Number":
            out.append({"kind": "Number", "value": a["value"]})
        cur = nxt
    return out


def lex(text: str, forms: list[tuple[str, str]]) -> list[dict]:
    """Reduce text to lexical constituents via the native recognition rules."""
    g, head, _tail = _lex_graph(text, forms)
    return _lex_readback(g, head)


# --- composition / Merge — the dorsal+Broca's faculty -----------------------
#
# ONE general mechanism, not bespoke constructions. Each content sign is a
# grounded concept with argument-structure SLOTS (role, optional role-marker
# word, direction). A small set of general Merge rules fills any head's open
# slot with an adjacent SATURATED constituent — building a predicate-argument
# meaning Term over grounded concepts (the substrate's native form). The
# vocabulary (signs) is data; the rules are vocabulary-independent.


def _saturated(var):
    """A constituent is a legal filler only when it has no unfilled slots — so
    composition proceeds bottom-up (inner phrases close before outer bind them)."""
    return Not(arg=Exists(Neighbours(Var(var), "has_slot"), "s2",
                          Eq(a=Attr(Var("s2"), "filled"), b=Lit(0))))


def _bind():
    """Bind the current slot S of head-meaning MH to filler-meaning MF: attach an
    Arg (carrying the role) and mark the slot filled. Shared by every Merge rule."""
    return [("add_node", "A", "Arg", {"role": Attr(Var("S"), "role")}),
            ("add_edge", "MH", "arg", "A"), ("add_edge", "A", "value", "MF"),
            ("set_attr", "S", "filled", 1)]


def _merge_rules() -> list[dict]:
    """The general Merge rules (vocabulary-independent): a head H with an open
    slot S absorbs an adjacent saturated filler F, in three shapes — a right
    argument via a role-marker word, a bare right argument, a bare left argument."""
    common = lambda extra: And(items=(Eq(a=Attr(Var("S"), "filled"), b=Lit(0)),
                                      _saturated("F"), *extra))
    r_marked = _rule(
        "merge_R_marked",
        match=[("H", "has_slot", "S"), ("H", "meaning", "MH"),
               ("H", "next", "M"), ("M", "next", "F"),
               ("F", "meaning", "MF"), ("F", "next", "Y")],
        where=common((Eq(a=TypeOf(Var("M")), b=Lit("Marker")),
                      Eq(a=Attr(Var("S"), "marker"), b=Attr(Var("M"), "form")))),
        effects=_bind() + [("add_edge", "H", "next", "Y"),
                           ("del_node", "M"), ("del_node", "F")])
    r_bare = _rule(
        "merge_R_bare",
        match=[("H", "has_slot", "S"), ("H", "meaning", "MH"),
               ("H", "next", "F"), ("F", "meaning", "MF"), ("F", "next", "Y")],
        where=common((Eq(a=Attr(Var("S"), "marker"), b=Lit(None)),
                      Eq(a=Attr(Var("S"), "dir"), b=Lit("R")),
                      Eq(a=TypeOf(Var("F")), b=Lit("Constituent")))),
        effects=_bind() + [("add_edge", "H", "next", "Y"), ("del_node", "F")])
    l_bare = _rule(
        "merge_L_bare",
        match=[("X", "next", "F"), ("F", "next", "H"), ("F", "meaning", "MF"),
               ("H", "has_slot", "S"), ("H", "meaning", "MH")],
        where=common((Eq(a=Attr(Var("S"), "marker"), b=Lit(None)),
                      Eq(a=Attr(Var("S"), "dir"), b=Lit("L")),
                      Eq(a=TypeOf(Var("F")), b=Lit("Constituent")))),
        effects=_bind() + [("add_edge", "X", "next", "H"), ("del_node", "F")])
    return [r_marked, r_bare, l_bare]


def _sign_kind(s):
    return "MARK" if s.get("mark") else ("FUNC" if s.get("drop") else "C")


def _read_meaning(g, m):
    """Read a meaning node into a nested predicate-argument structure: a leaf is
    its grounded concept (or number value); a head is {concept: {role: child}}."""
    a = g.node(m)["attrs"]
    if "concept" not in a:
        return a.get("value")
    args = {}
    for arg in g.neighbours(m, "arg"):
        val = g.neighbours(arg, "value")[0]
        args[g.node(arg)["attrs"]["role"]] = _read_meaning(g, val)
    return {a["concept"]: args} if args else a["concept"]


def comprehend(text: str, lexicon: list[dict], audience=None) -> list:
    """Comprehend ``text`` into grounded meaning Term(s): lexical access (chars→
    signs) then general Merge (slots filled by adjacent saturated constituents).
    Returns the meaning of each top-level constituent that remains. ``audience``
    is the reserved context hook (for the inverse, audience-relative production).
    """
    forms = [(s["form"], _sign_kind(s)) for s in lexicon]
    by_form = {s["form"]: s for s in lexicon}
    g, head, tail = _lex_graph(text, forms)
    tokens = _lex_readback(g, head)
    # Preserve graph-authored lexical recognition, but reuse its scratch graph
    # for semantic composition instead of constructing a second native graph.
    for old_node in list(g.nodes()):
        if old_node != head and old_node != tail:
            g.remove_node(old_node)
    prev, i = head, 0
    for tok in tokens:
        if tok["kind"] == "Number":
            node = g.add_node("Constituent", {"id": f"k{i}", "cat": "expr"})
            g.add_edge(node, "meaning",
                       g.add_node("Meaning", {"id": f"m{i}", "value": tok["value"]}), {})
        else:
            s = by_form.get(tok["form"])
            if s is None or s.get("drop"):
                continue
            if s.get("mark"):
                node = g.add_node("Marker", {"id": f"k{i}", "form": tok["form"]})
            else:
                node = g.add_node("Constituent", {"id": f"k{i}", "cat": "expr"})
                g.add_edge(node, "meaning",
                           g.add_node("Meaning", {"id": f"m{i}", "concept": s["concept"]}), {})
                for j, arg in enumerate(s.get("args", [])):
                    g.add_edge(node, "has_slot", g.add_node(
                        "Slot", {"id": f"s{i}_{j}", "role": arg["role"],
                                 "marker": arg.get("marker"),
                                 "dir": arg.get("dir", "R"), "filled": 0}), {})
        g.add_edge(prev, "next", node, {})
        prev, i = node, i + 1
    g.add_edge(prev, "next", tail, {})
    _run(g, [g.add_rule(r) for r in _merge_rules()])
    out, cur = [], head
    while True:
        nbrs = g.neighbours(cur, "next")
        if not nbrs:
            break
        nxt = nbrs[0]
        if g.node(nxt)["type"] == "Constituent":
            out.append(_read_meaning(g, g.neighbours(nxt, "meaning")[0]))
        cur = nxt
    force = "ask" if text.rstrip().endswith("?") else "tell"   # minimal prosody
    if len(out) == 1 and isinstance(out[0], dict):
        out[0] = {"force": force, **out[0]}
    return out


# --- production — encode(meaning | audience), comprehension's inverse --------
#
# Production is comprehension run backwards over the SAME signs: unfold a meaning
# Term into a signal by linearising each head with its arguments (left args, head
# form, right args with their role-markers), recursing into argument meanings.
# Correctness is ROUND-TRIP: comprehend(produce(m)) == m.


def _op(form, concept, marker="of"):
    """A unary operator sign: '<form> of X' → concept(of=X)."""
    return {"form": form, "concept": concept,
            "args": [{"role": "of", "marker": marker, "dir": "R"}]}


def _op2(form, concept, m1, m2):
    """A binary sign with two role-markers: '<form> <m1> X <m2> Y'."""
    return {"form": form, "concept": concept,
            "args": [{"role": "a", "marker": m1, "dir": "R"},
                     {"role": "b", "marker": m2, "dir": "R"}]}


def _infix(form, concept):
    """An infix binary sign: 'X <form> Y' → concept(left=X, right=Y)."""
    return {"form": form, "concept": concept,
            "args": [{"role": "left", "dir": "L"}, {"role": "right", "dir": "R"}]}


def _pred(form, concept):
    """A predicate over a left subject: 'X <form>' → concept(arg=X)
    (with the copula 'is' dropped, 'X is <form>' parses the same)."""
    return {"form": form, "concept": concept, "args": [{"role": "arg", "dir": "L"}]}


def core_lexicon() -> list[dict]:
    """The entity's starter lexicon, sized to communicate in HLE-domain math —
    the vocabulary of the substrate's actual capability areas (groups & finitely-
    presented groups, linear algebra, sets/functions, number theory, probability,
    topology, the inference capabilities) plus the question structures HLE uses.
    The grammar is unchanged (vocabulary-independent); concept names match the
    substrate's capabilities so a parsed meaning can later route to one. NB this
    is the LANGUAGE to talk about these domains — answering research-level HLE
    questions is concept coverage, a separate matter."""
    lex = [
        # unary 'the <op> of X' — operators that take one object
        *[_op(f, c) for f, c in (
            ("determinant", "det"), ("trace", "trace"), ("rank", "rank"),
            ("inverse", "inverse"), ("transpose", "transpose"),
            ("dimension", "dim"), ("order", "order"), ("cardinality", "card"),
            ("kernel", "kernel"), ("image", "image"), ("domain", "domain"),
            ("genus", "genus"), ("Euler characteristic", "euler"),
            ("Wolfram code", "wolfram_code"), ("characteristic", "char"),
            ("expectation", "expectation"), ("variance", "variance"),
            ("largest prime divisor", "largest_prime_factor"),
            ("largest prime factor", "largest_prime_factor"),
            ("prime factors", "prime_factors"),
            ("derivative", "derivative"), ("limit", "limit"),
            ("subgroups", "subgroups"), ("generators", "generators"),
            ("automorphisms", "automorphisms"), ("next term", "next_term"),
            ("solution", "solution"), ("number", "count"))],
        # 'how many X' — a count question taking a BARE right argument (no 'of')
        {"form": "how many", "concept": "count",
         "args": [{"role": "of", "dir": "R"}]},
        # closed-form SUMMATIONS — the generator-COMPOSED capabilities
        # (capability_compose: sum_first_n / _squares / _cubes), reachable from
        # talk. Each is a multiword form taking a BARE right Number arg (like
        # 'how many X'): '<phrase> N' -> concept(of=N). Longest-match keeps these
        # distinct from the binary 'the sum of X and Y'. TAUGHT vocabulary data;
        # the capability itself is the persisted composed Term-tree.
        {"form": "sum of squares up to", "concept": "sum_first_n_squares",
         "args": [{"role": "of", "dir": "R"}]},
        {"form": "sum of cubes up to", "concept": "sum_first_n_cubes",
         "args": [{"role": "of", "dir": "R"}]},
        {"form": "sum of integers up to", "concept": "sum_first_n",
         "args": [{"role": "of", "dir": "R"}]},
        {"form": "sum up to", "concept": "sum_first_n",
         "args": [{"role": "of", "dir": "R"}]},
        # two-argument 'the <op> of X and Y'
        *[_op2(f, c, "of", "and") for f, c in (
            ("product", "product"), ("sum", "sum"), ("gcd", "gcd"),
            ("lcm", "lcm"), ("union", "union"), ("intersection", "intersection"))],
        # 'the index of H in G'
        _op2("index", "index", "of", "in"),
        # infix binaries 'X <op> Y'
        *[_infix(f, c) for f, c in (
            ("plus", "plus"), ("times", "times"), ("minus", "minus"),
            ("equals", "equals"), ("divides", "divides"))],
        # predicates 'X is <pred>'
        *[_pred(f, c) for f, c in (
            ("prime", "prime"), ("even", "even"), ("odd", "odd"),
            ("invertible", "invertible"), ("normal", "normal"),
            ("abelian", "abelian"), ("cyclic", "cyclic"),
            ("solvable", "solvable"), ("connected", "connected"),
            ("injective", "injective"), ("surjective", "surjective"),
            ("bijective", "bijective"), ("isomorphic", "isomorphic"),
            ("independent", "independent"), ("finite", "finite"),
            ("infinite", "infinite"))],
        # objects / nouns and bound variables
        *[{"form": v, "concept": v} for v in (
            "group", "matrix", "set", "function", "sequence", "field", "ring",
            "graph", "polynomial", "automaton", "equation", "system",
            "A", "B", "C", "M", "N", "G", "H", "X", "Y", "Z",
            "f", "g", "p", "q", "n")],
        # role-markers and (dropped) function words
        *[{"form": m, "mark": True} for m in ("of", "and", "in", "by", "under")],
        *[{"form": w, "drop": True} for w in (
            "the", "is", "are", "a", "an", "does", "do", "have", "what", "to")],
    ]
    return lex


def produce(meaning, lexicon: list[dict], audience=None) -> str:
    """Encode a meaning Term into a signal via the lexicon's signs. ``audience``
    is the reserved hook for audience-relative efficient encoding (search for the
    cheapest signal the audience comprehends back to ``meaning``); None ⇒ explicit."""
    by_concept = {s["concept"]: s for s in lexicon if s.get("concept")}

    def emit(m) -> list[str]:
        if isinstance(m, bool):                     # guard: bool is an int subclass
            return [str(m)]
        if isinstance(m, int):
            return [str(m)]
        if isinstance(m, str):                      # leaf concept → its form
            return [by_concept[m]["form"]]
        concept = next(k for k in m if k != "force")
        sign, args = by_concept[concept], m[concept]
        left, right = [], []
        for arg in sign.get("args", []):            # surface order from the sign
            child = args.get(arg["role"])
            if child is None:
                continue
            sub = emit(child)
            if arg.get("dir", "R") == "L":
                left += sub
            else:
                if arg.get("marker"):
                    right.append(arg["marker"])
                right += sub
        return left + [sign["form"]] + right

    signal = " ".join(emit(meaning))
    if isinstance(meaning, dict) and meaning.get("force") == "ask":
        signal += "?"
    return signal
