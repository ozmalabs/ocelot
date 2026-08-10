"""Finitely-presented groups by REWRITING — ⟨generators | relations⟩.

A finite cyclic group was one generator and a closure (gⁿ=e). The general case
is many generators and many relations, and an element is no longer a single
node — it is a WORD over the generators, and two words name the same element iff
the relations rewrite one to the other. So the group is given by a finite
PRESENTATION, and computing in it is REWRITING: reduce a word to a normal form
by applying the relations as rewrite rules until none applies. The whole
(possibly infinite) group is never enumerated — its elements are generated, and
its operation decided, by rewriting on demand.

This is graph-native: the presentation (generators + relation rewrite rules) and
each word (a chain of Letter nodes) live in the graph; ``normal_form`` reads the
relations and the word off the graph and applies them — the rewriting engine
running graph-resident rules, the same shape as the DSL evaluator running
graph-resident Term-trees.

Scope: relations are string rewrite rules ``lhs → rhs``; reduction applies the
leftmost applicable rule to a fixed point. For a length-reducing confluent
system (e.g. the infinite dihedral group ⟨a,b | aa=e, bb=e⟩, or free reduction
with inverses) this terminates at a UNIQUE normal form. General presentations
need Knuth–Bendix completion first to guarantee confluence — that is the
frontier; the rewriting mechanism here is the load-bearing part.
"""
from __future__ import annotations

import itertools

from substrate import TypedGraph


def present(graph: TypedGraph, name: str, generators: str,
            relations: list[tuple[str, str]]) -> object:
    """Store a group presentation ⟨generators | relations⟩ in the graph: a
    Presentation node, a Generator node per symbol, and a RewriteRule node
    (lhs → rhs) per relation. Returns the presentation node id."""
    pid = graph._insert_node("Presentation", {"id": f"pres_{name}",
                                               "generators": generators})
    for s in generators:
        g = graph._insert_node("Generator", {"id": f"{name}_gen_{s}", "symbol": s})
        graph._insert_edge(pid, "generator", g)
    for i, (lhs, rhs) in enumerate(relations):
        r = graph._insert_node("RewriteRule",
                               {"id": f"{name}_rule_{i}", "lhs": lhs, "rhs": rhs})
        graph._insert_edge(pid, "relation", r)
    return pid


def make_word(graph: TypedGraph, name: str, symbols: str) -> object:
    """Build a word as a chain of Letter nodes (``symbol`` + ``next`` edges) in
    the graph. Returns the Word node id."""
    wid = graph._insert_node("Word", {"id": f"word_{name}", "spelling": symbols})
    prev = None
    for i, s in enumerate(symbols):
        lid = graph._insert_node("Letter", {"id": f"{name}_l{i}", "symbol": s})
        graph._insert_edge(wid, "letter", lid)
        if i == 0:
            graph._insert_edge(wid, "first", lid)
        if prev is not None:
            graph._insert_edge(prev, "next", lid)
        prev = lid
    return wid


def _spell(graph: TypedGraph, word: object) -> str:
    """Read a word's symbols off the graph by walking the ``next`` chain from
    ``first`` — the spelling as it currently stands in the graph."""
    first = next((e.key.tgt for e in graph.out_edges(word, "first")), None)
    out = []
    cur = first
    while cur is not None:
        out.append(graph.node(cur).attrs["symbol"])
        cur = next((e.key.tgt for e in graph.out_edges(cur, "next")), None)
    return "".join(out)


def _relations(graph: TypedGraph, pres: object) -> list[tuple[str, str]]:
    rules = []
    for e in graph.out_edges(pres, "relation"):
        a = graph.node(e.key.tgt).attrs
        rules.append((a["lhs"], a["rhs"]))
    return rules


def _relation_rule(scratch, name: str, lhs: str, rhs: str):
    """A relation lhs → rhs as a graph rewrite rule over a Letter chain: match a
    sub-chain X →next→ L0 …→ L_{p-1} →next→ Y whose letters spell ``lhs`` (a
    ``where`` on the ``symbol`` attrs), then splice it out and stitch ``rhs`` in
    its place (construct the new Letter nodes, relink X →…→ Y, delete the old)."""
    from substrate import And, Attr, Eq, Lit, Var

    from domains import graph_rewrite as gr

    p = len(lhs)
    lv = [f"L{i}" for i in range(p)]
    match_edges = [("X", "next", lv[0])]
    for i in range(p - 1):
        match_edges.append((lv[i], "next", lv[i + 1]))
    match_edges.append((lv[p - 1], "next", "Y"))
    where = And(items=tuple(
        Eq(a=Attr(Var(lv[i]), "symbol"), b=Lit(lhs[i])) for i in range(p)))
    effects, prev = [], "X"
    for j, ch in enumerate(rhs):
        effects.append(("add_node", f"N{j}", "Letter", {"symbol": ch}))
        effects.append(("add_edge", prev, "next", f"N{j}"))
        prev = f"N{j}"
    effects.append(("add_edge", prev, "next", "Y"))
    effects += [("del_node", v) for v in lv]
    return gr.make_rule(scratch, name, match_edges, where, effects)


def normal_form(graph: TypedGraph, word: object, pres: object,
                max_steps: int = 100000) -> str:
    """Reduce a word to normal form by REWRITING — now run on the rewrite
    ENGINE: read the word and the presentation's relations off the graph, build
    a Letter chain plus a graph rewrite rule per relation, and apply them to a
    fixed point. The element's canonical representative — computed by the engine
    turning the crank on graph-resident rules, never looked up in a table."""
    from substrate import TypedGraph as _TG

    from domains import graph_rewrite as gr

    scratch = _TG()
    head, _tail = gr.make_word(scratch, "w", _spell(graph, word))
    rules = [_relation_rule(scratch, f"rel{i}", lhs, rhs)
             for i, (lhs, rhs) in enumerate(_relations(graph, pres)) if lhs]
    gr.run(scratch, rules, max_steps=max_steps)
    return gr.read_word(scratch, head)


def equal(graph: TypedGraph, w1: object, w2: object, pres: object) -> bool:
    """Do two words name the SAME group element? Iff they share a normal form."""
    return normal_form(graph, w1, pres) == normal_form(graph, w2, pres)


def multiply(graph: TypedGraph, name: str, w1: object, w2: object,
             pres: object) -> str:
    """The group product w1·w2: concatenate the spellings and reduce."""
    combined = make_word(graph, name, _spell(graph, w1) + _spell(graph, w2))
    return normal_form(graph, combined, pres)


# --- Knuth–Bendix completion: make a presentation's rewriting CONFLUENT ---
#
# Leftmost-to-fixpoint only gives unique normal forms if the rule set is
# confluent. An arbitrary presentation is not: e.g. ⟨a,b | a²=e, b²=e, abab=e⟩
# leaves both "ab" and "ba" irreducible though ab=ba — too many normal forms.
# Knuth–Bendix repairs this: orient every rule by a reduction ordering
# (shortlex: shorter first, then lexicographic — a well-ordering, so rewriting
# always terminates), find CRITICAL PAIRS (words two rules reduce two ways),
# and for each that disagrees add a new oriented rule. Repeat to a fixed point.
# The result is confluent + terminating: every word has ONE normal form, so the
# whole (finite) group is captured exactly — without ever enumerating it.

def _key(s: str):
    return (len(s), s)               # shortlex: length, then lexicographic


def _orient(u: str, v: str) -> tuple[str, str]:
    """Orient an equation u=v into a rule lhs→rhs with lhs > rhs (shortlex), so
    applying it strictly decreases the word and rewriting terminates."""
    return (u, v) if _key(u) > _key(v) else (v, u)


def _reduce_str(s: str, rules: list[tuple[str, str]]) -> str:
    while True:
        for lhs, rhs in rules:
            if lhs and lhs in s:
                s = s.replace(lhs, rhs, 1)
                break
        else:
            return s


def _critical_pairs(rules):
    """Words where two rules' left sides overlap, each yielding the two results
    those rules produce — the places confluence can fail."""
    for l1, r1 in rules:
        for l2, r2 in rules:
            # l2 occurs inside l1: l1 = x·l2·y → reduce to r1, or to x·r2·y
            start = 0
            while True:
                i = l1.find(l2, start)
                if i < 0:
                    break
                if not (l1 == l2 and i == 0):           # skip the trivial self-overlap
                    yield (r1, l1[:i] + r2 + l1[i + len(l2):])
                start = i + 1
            # a suffix of l1 equals a prefix of l2: l1·l2[k:] reduces two ways
            for k in range(1, min(len(l1), len(l2))):
                if l1[-k:] == l2[:k]:
                    yield (r1 + l2[k:], l1[:-k] + r2)


def complete(relations: list[tuple[str, str]], cap: int = 2000):
    """Knuth–Bendix: complete a list of equations into a confluent, terminating
    set of oriented rewrite rules (shortlex). Returns the completed rules.
    (May not terminate for some infinite groups — semi-decidable; ``cap``
    bounds it.)"""
    rules: list[tuple[str, str]] = []
    for u, v in relations:
        lhs, rhs = _orient(u, v)
        if lhs != rhs and (lhs, rhs) not in rules:
            rules.append((lhs, rhs))
    for _ in range(cap):
        added = None
        for p, q in _critical_pairs(rules):
            p2, q2 = _reduce_str(p, rules), _reduce_str(q, rules)
            if p2 != q2:
                lhs, rhs = _orient(p2, q2)
                if lhs and lhs != rhs and (lhs, rhs) not in rules:
                    added = (lhs, rhs)
                    break
        if added is None:
            return rules            # confluent: every critical pair resolves
        rules.append(added)
    return rules


# --- cosets and quotients: structure built ON the rewriting ---
#
# Once normal forms are unique (KB-completed), elements ARE normal forms and the
# product is concat-then-reduce. Everything else in finite group theory is built
# on that: the elements (all reachable normal forms), a subgroup's closure under
# the product, the cosets it cuts G into (Lagrange: |G| = index · |H|), and the
# quotient G/N when N is normal.

def elements(graph: TypedGraph, pres: object, generators: str,
             upto: int = 8) -> set:
    """All elements of a finite group: the distinct normal forms of words over
    the generators up to a length that has stabilised."""
    rules = _relations(graph, pres)
    return {_reduce_str("".join(t), rules)
            for L in range(upto + 1)
            for t in itertools.product(generators, repeat=L)}


def subgroup_closure(graph: TypedGraph, pres: object,
                     sub_generators: list[str]) -> set:
    """The subgroup ⟨sub_generators⟩: close the generators (and the identity)
    under the group product, to a fixed point. (Finite ⇒ reaches inverses too,
    since gᵏ=e.)"""
    rules = _relations(graph, pres)
    elems = {""} | {_reduce_str(s, rules) for s in sub_generators}
    changed = True
    while changed:
        changed = False
        for x in list(elems):
            for y in list(elems):
                p = _reduce_str(x + y, rules)
                if p not in elems:
                    elems.add(p)
                    changed = True
    return elems


def left_cosets(graph: TypedGraph, pres: object, group_elems: set,
                subgroup: set) -> list:
    """Partition G into the left cosets gH = { g·h : h ∈ H } (distinct sets)."""
    rules = _relations(graph, pres)
    seen, cosets = set(), []
    for g in sorted(group_elems, key=_key):
        coset = frozenset(_reduce_str(g + h, rules) for h in subgroup)
        if coset not in seen:
            seen.add(coset)
            cosets.append(coset)
    return cosets


def is_normal(graph: TypedGraph, pres: object, group_elems: set,
              subgroup: set) -> bool:
    """Is H normal in G? (gH = Hg for every g — so the cosets form a quotient
    group G/H.)"""
    rules = _relations(graph, pres)
    for g in group_elems:
        gH = frozenset(_reduce_str(g + h, rules) for h in subgroup)
        Hg = frozenset(_reduce_str(h + g, rules) for h in subgroup)
        if gH != Hg:
            return False
    return True


# --- Todd–Coxeter coset enumeration: the index [G:H] without enumerating G ---
#
# Rewriting/KB computes a group by reducing words; that needs the group small
# enough to enumerate. Todd–Coxeter is the other foundational algorithm: given
# ⟨generators | relators⟩ and a subgroup H by generating words, it ENUMERATES
# THE COSETS of H — building a coset table where every relator (traced from any
# coset) returns to it and every H-generator (traced from coset 1) returns to 1
# — and the number of live cosets IS the index [G:H]. It can find a finite index
# even when G itself is infinite. This is the engine behind "subgroups of index
# n" and computing |G| (= [G:1]).

def coset_index(generators: str, relators: list[str], subgroup_gens: list[str],
                inverses: dict | None = None, max_cosets: int = 200000) -> int:
    """Index [G:H] by graph-resident COSET ENUMERATION (Todd–Coxeter), built on
    the rewrite engine. The coset table IS the graph: Coset nodes and generator-
    typed edges c —g→ d (both directions kept). DEDUCTION is the engine running
    graph-resident rules to a fixpoint — for each cyclic rotation of each
    relator a gap-fill rule matches the loop's defined prefix and adds the one
    forced edge (``allow_repeat`` lets the loop revisit a coset). The driver
    turns the crank: resolve a multi-valued slot or a relator that closes on the
    wrong coset (found with a Pick/Neighbours trace Term) by MERGING the two
    cosets; DEFINE a fresh coset for the lowest live coset's first empty slot
    when deduction stalls; repeat. Live cosets = [G:H]. ``inverses`` maps each
    generator to its inverse (default self-inverse — for involutions). Raises if
    the table exceeds ``max_cosets`` (index likely infinite)."""
    from substrate import TypedGraph

    inv = dict(inverses) if inverses else {}
    for g in generators:
        inv.setdefault(g, g)
    for g in list(inv):
        inv.setdefault(inv[g], g)
    alphabet = _alphabet(generators, inv)

    graph = TypedGraph()
    counter = [0]
    bynum: dict[int, object] = {}

    def new_coset():
        counter[0] += 1
        c = graph._insert_node("Coset", {"id": f"k{counter[0]}", "num": counter[0]})
        bynum[counter[0]] = c
        return c

    c1 = new_coset()
    coincidences: list = []

    def succ(c, g):
        return next(iter(graph.neighbours(c, g)), None)

    def set_edge(c, g, d):
        """Define T[c][g]=d and its inverse (the deduction the relator forces);
        a clash with an existing value means the two targets are the same coset
        — a coincidence, queued for merging."""
        cur = succ(c, g)
        if cur is None:
            graph._insert_edge(c, g, d)
        elif cur != d:
            coincidences.append((cur, d))
        cur2 = succ(d, inv[g])
        if cur2 is None:
            graph._insert_edge(d, inv[g], c)
        elif cur2 != c:
            coincidences.append((cur2, c))

    def define(c, g):
        d = new_coset()
        set_edge(c, g, d)
        return d

    def merge(keep, drop):
        """Fold ``drop`` into ``keep``: capture its relations (both directions
        are out-edges in the graph), delete the node, and re-attach them to keep
        — clashes re-queue as further coincidences (cascade)."""
        if keep == drop:
            return
        moves = [(g, t) for g in alphabet for t in graph.neighbours(drop, g)]
        bynum.pop(graph.node(drop).attrs["num"], None)
        graph._delete_node(drop)
        for g, t in moves:
            set_edge(keep, g, keep if t == drop else t)

    def process_coincidences():
        while coincidences:
            x, y = coincidences.pop()
            if x == y or x not in graph._nodes or y not in graph._nodes:
                continue
            a, b = sorted((x, y), key=lambda n: graph.node(n).attrs["num"])
            merge(a, b)

    def scan(start, word):
        """Apply a relator (or subgroup generator) from ``start`` as a walk over
        the graph-resident table: follow defined edges, DEFINE a fresh coset at
        a gap, and at the final letter DEDUCE the closing edge back to ``start``
        (or record a coincidence if it already points elsewhere)."""
        cur = start
        for sym in word[:-1]:
            nxt = succ(cur, sym)
            cur = nxt if nxt is not None else define(cur, sym)
        set_edge(cur, word[-1], start)

    # subgroup generators must fix coset 1 (each, traced from 1, returns to 1)
    for h in subgroup_gens:
        if h:
            scan(c1, h)
            process_coincidences()

    # --- enumeration: scan every relator from each live coset, in turn (HLT) --
    c = 1
    while c <= counter[0]:
        node = bynum.get(c)
        if node is not None:
            for r in relators:
                if not r:
                    continue
                scan(node, r)
                process_coincidences()
            if node in graph._nodes:              # survived its own scans
                for g in alphabet:
                    if succ(node, g) is None:
                        define(node, g)
                        process_coincidences()
        if counter[0] > max_cosets:
            raise ValueError("coset enumeration did not close (index too large/infinite)")
        c += 1
    return len(bynum)


def _alphabet(generators: str, inv: dict) -> list[str]:
    al = []
    for g in generators:
        for x in (g, inv.get(g, g)):
            if x not in al:
                al.append(x)
    return al


def low_index_subgroups(generators: str, relators: list[str], n: int,
                        inverses: dict | None = None) -> dict:
    """Count subgroups of each index 1..n of ⟨generators | relators⟩, by a
    graph-resident BACKTRACKING SEARCH over coset tables — built on the search
    layer (``graph_rewrite.search_count_general``), not Python control flow.

    The coset table lives in the graph: Coset nodes (each with a number and an
    ``active`` flag) and, when an entry T[c][g]=d is decided, a generator-typed
    edge c —g→ d (its inverse d —g⁻¹→ c forced in the same step, by a graph-
    resident assign rule per generator). The whole STRATEGY is Term-trees:
      * open    — a Slot of an *active* coset with no assignment yet;
      * options — the CANONICAL-NUMBERING set: every active coset, plus the one
                  smallest-numbered inactive coset (so a new coset is introduced
                  only as the next number → each subgroup is generated once);
      * fail    — bijectivity broken (a coset with two g-successors / a slot with
                  two values), i.e. an inverse/relation conflict;
      * accept  — every coset active (index exactly m, hence transitive by the
                  definitional numbering) AND every relator returns to its start
                  from every coset.
    The engine only turns the crank (pick the lowest open slot, try each option,
    backtrack); a raw count of accepted leaves is the number of subgroups."""
    from substrate import (And, Attr, Count, Eq, Exists, Filter, Gt, Lit,
                           MinOver, Neighbours, Not, Or, Pick, TypedGraph, Var)

    from domains import graph_rewrite as gr

    inv = dict(inverses) if inverses else {g: g for g in generators}
    for g in list(inv):
        inv.setdefault(inv[g], g)
    alphabet = _alphabet(generators, inv)

    def _trace(word):           # follow the generator edges spelling the relator
        t = Var("c")
        for ch in word:
            t = Pick(Neighbours(t, ch))
        return t

    counts = {}
    for m in range(1, n + 1):
        g = TypedGraph()
        allc = g._insert_node("Cosets", {"id": "allc"})
        alls = g._insert_node("Slots", {"id": "alls"})
        cos = {}
        for k in range(1, m + 1):
            cos[k] = g._insert_node("Coset", {"id": f"c{k}", "num": k,
                                              "active": 1 if k == 1 else 0})
            g._insert_edge(allc, "coset", cos[k])
        slot = {}
        for k in range(1, m + 1):               # coset-major, alphabet order:
            for x in alphabet:                  #   creation order = canonical scan
                s = g._insert_node("Slot", {"id": f"s{k}_{x}", "gen": x})
                g._insert_edge(s, "owner", cos[k])
                g._insert_edge(alls, "slot", s)
                slot[(k, x)] = s
        rule = {}                               # one assign rule per generator
        for x in alphabet:
            rule[x] = gr.make_rule(
                g, f"assign_{x}", match_edges=[], where=None,
                effects=[("add_edge", "c", x, "d"),
                         ("add_edge", "d", inv[x], "c"),
                         ("add_edge", "s", "to", "d"),
                         ("add_edge", "s2", "to", "c"),
                         ("set_attr", "d", "active", 1)])
        num_of = {cos[k]: k for k in cos}

        def apply_option(graph, item, option, _slot=slot, _rule=rule,
                         _inv=inv, _num=num_of):
            gen = graph.node(item).attrs["gen"]
            c = next(iter(graph.neighbours(item, "owner")))
            s2 = _slot[(_num[option], _inv[gen])]
            return gr.apply_rule_recording(
                graph, _rule[gen], {"c": c, "d": option, "s": item, "s2": s2})

        cosets = Neighbours(Var("allc"), "coset")
        inactive = Filter(cosets, "c2",
                          Not(arg=Eq(a=Attr(Var("c2"), "active"), b=Lit(1))))
        min_inactive = MinOver(source=inactive, var_name="c2",
                               value=Attr(Var("c2"), "num"), default=Lit(10 ** 9))
        options_term = Filter(cosets, "c", Or(items=(
            Eq(a=Attr(Var("c"), "active"), b=Lit(1)),
            Eq(a=Attr(Var("c"), "num"), b=min_inactive))))
        open_term = Filter(Neighbours(Var("alls"), "slot"), "s", And(items=(
            Eq(a=Count(Neighbours(Var("s"), "to")), b=Lit(0)),
            Exists(Neighbours(Var("s"), "owner"), "o",
                   Eq(a=Attr(Var("o"), "active"), b=Lit(1))))))
        fail_term = Or(items=tuple(
            Exists(cosets, "c", Gt(a=Count(Neighbours(Var("c"), x)), b=Lit(1)))
            for x in alphabet) + (
            Exists(Neighbours(Var("alls"), "slot"), "s",
                   Gt(a=Count(Neighbours(Var("s"), "to")), b=Lit(1))),))
        all_active = Not(arg=Exists(cosets, "c",
                         Not(arg=Eq(a=Attr(Var("c"), "active"), b=Lit(1)))))
        rel_terms = tuple(
            Not(arg=Exists(cosets, "c", Not(arg=Eq(a=_trace(r), b=Var("c")))))
            for r in relators if r)
        accept_term = And(items=(all_active,) + rel_terms)

        counts[m] = gr.search_count_general(
            g, open_term=open_term, options_term=options_term,
            apply_option=apply_option, fail_term=fail_term,
            accept_term=accept_term, env={"allc": allc, "alls": alls})
    return counts


def index_in_graph(graph: TypedGraph, pres: object, subgroup_gens: list[str],
                   inverses: dict | None = None) -> int:
    """[G:H] for a presentation stored in the graph: build relators from its
    relations (lhs=rhs ⇒ relator lhs·rhs⁻¹; for rhs='' just lhs) and run TC."""
    gens = graph.node(pres).attrs["generators"]
    inv = dict(inverses) if inverses else {g: g for g in gens}
    relators = []
    for lhs, rhs in _relations(graph, pres):
        relators.append(lhs + "".join(inv.get(ch, ch) for ch in reversed(rhs)))
    return coset_index(gens, relators, subgroup_gens, inv)


def complete_presentation(graph: TypedGraph, pres: object) -> list:
    """Read a presentation's relations off the graph, run Knuth–Bendix, and
    write the completed (confluent) rule set back as its relations — the agent
    repairing its own rewriting system so the group computes correctly."""
    completed = complete(_relations(graph, pres))
    for e in list(graph.out_edges(pres, "relation")):
        graph._delete_node(e.key.tgt)
    name = graph.node(pres).attrs["id"]
    for i, (lhs, rhs) in enumerate(completed):
        r = graph._insert_node("RewriteRule",
                               {"id": f"{name}_kb_{i}", "lhs": lhs, "rhs": rhs})
        graph._insert_edge(pres, "relation", r)
    return completed
