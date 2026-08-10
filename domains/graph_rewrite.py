"""Graph-resident constructive procedures — the deeper fix.

The DSL evaluates the graph (read-only): it can decide and compute, but it
cannot CONSTRUCT — build a reduced word, a coset table, a completed rule set.
That is why the algorithm floors (rewriting, Knuth–Bendix, Todd–Coxeter) slid
into Python: an imperative search/mutation has no read-only Term-tree form.

The substrate's own foundation is typed-graph REWRITING (G, Γ): a production is
a graph-resident rule the engine applies. So the right capability is the agent's
own rewrite rules — each a PATTERN (a subgraph to match, with a graph-resident
``where`` Term-tree as its side-condition) and an EFFECT (graph mutations on the
matched bindings) — stored AS DATA in the graph. An engine (Python, doing only
its sanctioned job — *running* the graph) matches a rule and applies its effect,
to a fixed point. The reasoning (which rules, what they do) lives in the graph;
Python just turns the crank. Constructive algorithms become rule sets the agent
holds and runs, not opaque code.
"""
from __future__ import annotations

from substrate import TypedGraph, term_from_json


def _enc(v):
    """Encode an effect argument for storage: a DSL Term → graph-resident JSON
    (a computed value, evaluated over the match at apply-time); a dict → its
    values encoded; anything else stored literally."""
    from substrate import Term, term_to_json
    if isinstance(v, Term):
        return {"__term__": term_to_json(v)}
    if isinstance(v, dict):
        return {k: _enc(x) for k, x in v.items()}
    return v


def make_rule(graph: TypedGraph, name: str, match_edges, where, effects) -> object:
    """Store a rewrite rule as graph data on a Rule node:
      * ``match`` : edge constraints [(src_var, edge_type, tgt_var), …]
      * ``where`` : a DSL Term over the matched variables (side-condition)
      * ``effect``: graph mutations, each a tuple:
          ("add_edge", sv, et, tv) | ("del_edge", sv, et, tv) | ("del_node", v)
          ("add_node", new_var, type, {attr: literal-or-Term})  — CONSTRUCTS a
              node (bound to new_var for later effects); attrs may be computed
              Terms over the match
          ("set_attr", v, key, literal-or-Term)                 — sets/derives
    Computed Terms are evaluated over the match binding when the rule fires."""
    from substrate import term_to_json
    return graph._insert_node("Rule", {
        "id": f"rule_{name}",
        "match": [list(e) for e in match_edges],
        "where": term_to_json(where) if where is not None else None,
        "effect": [[_enc(x) for x in op] for op in effects],
    })


def _match(graph: TypedGraph, rule: object):
    """Find one binding {var: node} satisfying the rule's edge constraints and
    its ``where`` Term — a small backtracking subgraph match."""
    spec = graph.node(rule).attrs
    edges = spec["match"]
    where = term_from_json(spec["where"]) if spec["where"] else None

    def extend(i, binding):
        if i == len(edges):
            if len(set(binding.values())) != len(binding):
                return None                     # variables must be distinct nodes
            if where is not None:
                env = {**binding, "_resolve_concept": lambda n: None}
                try:
                    if not where.evaluate(env, graph):
                        return None
                except Exception:
                    return None
            return dict(binding)
        sv, et, tv = edges[i]
        cands = []
        if sv in binding:
            cands = [(binding[sv], t) for t in graph.neighbours(binding[sv], et)]
        elif tv in binding:
            cands = [(s.key.src, binding[tv]) for s in graph.in_edges(binding[tv], et)]
        else:
            cands = [(e.key.src, e.key.tgt) for e in graph._edges.values()
                     if e.key.edge_type == et]
        for s, t in cands:
            if sv in binding and binding[sv] != s:
                continue
            if tv in binding and binding[tv] != t:
                continue
            b = {**binding, sv: s, tv: t}
            r = extend(i + 1, b)
            if r is not None:
                return r
        return None

    return extend(0, {})


def _resolve(v, binding, graph):
    """Resolve a stored effect argument: a {"__term__": …} computed value is
    evaluated over the current match binding (the engine running a graph-
    resident expression); everything else is the literal."""
    if isinstance(v, dict) and "__term__" in v:
        from substrate import term_from_json
        env = {**binding, "_resolve_concept": lambda n: None}
        return term_from_json(v["__term__"]).evaluate(env, graph)
    return v


def _apply(graph: TypedGraph, rule: object, binding: dict) -> None:
    from substrate import EdgeKey
    b = dict(binding)                                # new nodes extend the binding
    for op in graph.node(rule).attrs["effect"]:
        kind = op[0]
        if kind == "add_edge":
            # ("add_edge", src, edge_type, tgt[, attrs_dict]) — optional
            # 5th element carries edge attrs (each value literal or Term).
            edge_attrs = None
            if len(op) >= 5:
                raw = op[4]
                if isinstance(raw, dict):
                    edge_attrs = {k: _resolve(v, b, graph)
                                  for k, v in raw.items()}
                else:
                    edge_attrs = _resolve(raw, b, graph)
            graph._insert_edge(b[op[1]], op[2], b[op[3]], edge_attrs)
        elif kind == "del_edge":
            graph._delete_edge(EdgeKey(b[op[1]], op[2], b[op[3]]))
        elif kind == "del_node":
            graph._delete_node(b[op[1]])
        elif kind == "add_node":                     # CONSTRUCT a node
            attrs = {k: _resolve(x, b, graph) for k, x in op[3].items()}
            b[op[1]] = graph._insert_node(op[2], attrs)
        elif kind == "set_attr":                     # set / derive an attr
            graph.node(b[op[1]]).attrs[op[2]] = _resolve(op[3], b, graph)


def search_count(graph: TypedGraph, open_term, options_term, assign_edge: str,
                 fail_term, env: dict | None = None) -> int:
    """Graph-resident BACKTRACKING SEARCH (DFS with undo). The STRATEGY is
    graph-resident Term-trees; the engine just explores:
      * ``open_term``    yields the undecided items (e.g. uncoloured vertices);
      * if none remain and ``fail_term`` is false, that's a SOLUTION (count 1);
      * ``fail_term``    — a constraint violated → dead end (prune);
      * for the first open item, try each option (``options_term``) by adding an
        ``assign_edge`` to it, recurse, then UNDO (backtrack).
    Returns the number of solutions. This is the missing capability behind the
    search algorithms (low-index subgroups, Todd–Coxeter, Knuth–Bendix)."""
    from substrate import EdgeKey
    base = {"_resolve_concept": lambda n: None}
    if env:
        base.update(env)
    if bool(fail_term.evaluate(base, graph)):
        return 0                                    # constraint violated → prune
    opens = list(open_term.evaluate(base, graph))
    if not opens:
        return 1                                    # complete + consistent → a solution
    item = min(opens, key=lambda n: n.value)        # deterministic choice
    total = 0
    for opt in options_term.evaluate(base, graph):
        graph._insert_edge(item, assign_edge, opt)
        total += search_count(graph, open_term, options_term, assign_edge,
                              fail_term, env)
        graph._delete_edge(EdgeKey(item, assign_edge, opt))   # backtrack
    return total


_MISSING = object()


def apply_rule_recording(graph: TypedGraph, rule: object, binding: dict) -> list:
    """Apply a rule's effects over a *given* binding (vars pre-bound by the
    caller, e.g. a search step's chosen assignment), recording an UNDO token —
    a list of reversers — so a backtracking search can restore the prior state.
    add_edge only inserts an absent edge (a duplicate is a no-op, so undo would
    be wrong to delete it); set_attr remembers the previous value."""
    from substrate import EdgeKey
    b = dict(binding)
    undo: list = []
    for op in graph.node(rule).attrs["effect"]:
        kind = op[0]
        if kind == "add_edge":
            src, et, tgt = b[op[1]], op[2], b[op[3]]
            key = EdgeKey(src, et, tgt)
            if key not in graph._edges:
                graph._insert_edge(src, et, tgt)
                undo.append(lambda k=key: graph._delete_edge(k))
        elif kind == "del_edge":
            graph._delete_edge(EdgeKey(b[op[1]], op[2], b[op[3]]))
        elif kind == "set_attr":
            node = graph.node(b[op[1]])
            k, old = op[2], graph.node(b[op[1]]).attrs.get(op[2], _MISSING)
            node.attrs[k] = _resolve(op[3], b, graph)

            def rev(n=node, key=k, o=old):
                if o is _MISSING:
                    n.attrs.pop(key, None)
                else:
                    n.attrs[key] = o
            undo.append(rev)
    return undo


def search_count_general(graph: TypedGraph, *, open_term, options_term,
                         apply_option, fail_term=None, accept_term=None,
                         env: dict | None = None) -> int:
    """Generic graph-resident BACKTRACKING search, counting solutions. The
    STRATEGY is all graph-resident Term-trees — ``open_term`` (the undecided
    items), ``options_term`` (candidate assignments for the chosen item),
    ``fail_term`` (a violated constraint → prune), ``accept_term`` (a complete
    leaf counts iff it holds). The engine only turns the crank: prune on
    ``fail_term``; if nothing is open, count the leaf; else take the lowest open
    item and, for each option, apply it (``apply_option`` returns an undo token),
    recurse, then backtrack. ``apply_option(graph, item, option) -> [undo, …]``
    applies a graph-resident effect (e.g. via ``apply_rule_recording``)."""
    base = {"_resolve_concept": lambda n: None}
    if env:
        base.update(env)
    if fail_term is not None and bool(fail_term.evaluate(base, graph)):
        return 0
    opens = list(open_term.evaluate(base, graph))
    if not opens:
        ok = accept_term is None or bool(accept_term.evaluate(base, graph))
        return 1 if ok else 0
    item = min(opens, key=lambda n: n.value)
    total = 0
    for opt in options_term.evaluate(base, graph):
        undo = apply_option(graph, item, opt)
        total += search_count_general(
            graph, open_term=open_term, options_term=options_term,
            apply_option=apply_option, fail_term=fail_term,
            accept_term=accept_term, env=env)
        for rev in reversed(undo):
            rev()
    return total


def search_sum(graph: TypedGraph, *, open_term, options_term, apply_option,
               value_term, fail_term=None, env: dict | None = None):
    """Backtracking search that SUMS a graph-resident ``value_term`` over every
    complete leaf, rather than counting them — the search layer's reduce form.
    Same shape as :func:`search_count_general`: ``open_term`` yields the
    undecided items; with none left (and no ``fail_term``) the leaf contributes
    ``value_term``; otherwise the lowest open item is bound as ``item`` (so
    ``options_term`` may depend on it) and each option applied/undone. The
    determinant is exactly this — a signed product summed over the permutations
    the search enumerates."""
    base = {"_resolve_concept": lambda n: None}
    if env:
        base.update(env)
    if fail_term is not None and bool(fail_term.evaluate(base, graph)):
        return 0
    opens = list(open_term.evaluate(base, graph))
    if not opens:
        return value_term.evaluate(base, graph)
    item = min(opens, key=lambda n: n.value)
    item_env = {**base, "item": item}
    total = 0
    for opt in options_term.evaluate(item_env, graph):
        undo = apply_option(graph, item, opt)
        total += search_sum(graph, open_term=open_term, options_term=options_term,
                            apply_option=apply_option, value_term=value_term,
                            fail_term=fail_term, env=env)
        for rev in reversed(undo):
            rev()
    return total


def run(graph: TypedGraph, rule_ids, max_steps: int = 100000) -> int:
    """Apply the graph-resident rules to a fixed point (the engine running the
    agent's procedure). Returns the number of rewrite steps taken."""
    steps = 0
    while steps < max_steps:
        for rid in rule_ids:
            b = _match(graph, rid)
            if b is not None:
                _apply(graph, rid, b)
                steps += 1
                break
        else:
            return steps
    return steps


# --- words as graph chains (HEAD … TAIL sentinels make one uniform rule) ---

def make_word(graph: TypedGraph, name: str, symbols: str):
    """A word as HEAD →next→ letters →next→ TAIL. Returns (head, tail)."""
    head = graph._insert_node("Anchor", {"id": f"{name}_head", "symbol": None})
    prev = head
    for i, s in enumerate(symbols):
        lid = graph._insert_node("Letter", {"id": f"{name}_l{i}", "symbol": s})
        graph._insert_edge(prev, "next", lid)
        prev = lid
    tail = graph._insert_node("Anchor", {"id": f"{name}_tail", "symbol": None})
    graph._insert_edge(prev, "next", tail)
    return head, tail


def read_word(graph: TypedGraph, head: object) -> str:
    out, cur = [], head
    while True:
        nxt = next((e.key.tgt for e in graph.out_edges(cur, "next")), None)
        if nxt is None:
            break
        s = graph.node(nxt).attrs.get("symbol")
        if s is not None:
            out.append(s)
        cur = nxt
    return "".join(out)
