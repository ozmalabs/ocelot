"""substrate_rs.ext — capability extensions beyond the Python baseline.

The drop-in core (`substrate_rs`) matches `substrate/` for parity. This
submodule carries features the Python substrate didn't have:

* **Set-algebra Terms** — `Union`, `Intersect`, `Difference`, `MapSet`.
  Closes the gap where set composition had to go via `Filter` + `Exists`.
* **Edge-attr DSL access** — `Edges`, `EdgeAttr`. Closes the gap where
  the DSL could read node attrs (`Attr`) but not edge attrs.
* **Observability** — `counters(substrate)` returns a snapshot dict of
  per-type node counts, per-production hit/reject tallies, eval-cache
  hit-rate, evaluations performed, and the ρ helper (|G|).
"""
from __future__ import annotations

from typing import Any, Callable

from . import _native
from . import Substrate as _PySubstrate
from . import Term


# --- Set-algebra Terms ----------------------------------------------------

def Union(a: Term, b: Term) -> Term:
    """Set union — `{a's elements} ∪ {b's elements}`. Deduped."""
    return Term("Union", a=a, b=b)


def Intersect(a: Term, b: Term) -> Term:
    """Set intersection — `{a's elements} ∩ {b's elements}`."""
    return Term("Intersect", a=a, b=b)


def Difference(a: Term, b: Term) -> Term:
    """Set difference — `{a's elements} \\ {b's elements}`."""
    return Term("Difference", a=a, b=b)


def MapSet(source: Term, var_name: str, value: Term) -> Term:
    """Map-then-collect: bind each element of `source` to `var_name`,
    evaluate `value`, collect the unique results as a set.
    """
    return Term("MapSet", source=source, var_name=var_name, value=value)


# --- Edge-attr DSL --------------------------------------------------------

def Edges(node: Term, edge_type: str | None = None) -> Term:
    """Outgoing edges of `node` as `(src, edge_type, tgt)` triples
    (Tuple Values). Pair with `EdgeAttr` to query edge attributes.
    """
    return Term("Edges", node=node, edge_type=edge_type)


def EdgeAttr(edge: Term, key: str) -> Term:
    """Read an attribute from an edge handle. `edge` should evaluate to
    a `(src, edge_type, tgt)` tuple — typically produced by `Edges`.
    """
    return Term("EdgeAttr", edge=edge, key=key)


# --- Indexed lookup (Phase 7b) ----------------------------------------

def NodesWhere(node_type: str, attr_key: str, value: Term) -> Term:
    """Indexed attr-equality lookup. Returns the frozenset of nodes
    typed `node_type` whose `attr_key` equals the evaluated `value`.

    O(1+result) if `declare_attr_index(substrate, node_type, attr_key)`
    has been called; otherwise falls back to a linear scan of nodes of
    that type so the Term is always correct.
    """
    return Term("NodesWhere", node_type=node_type, attr_key=attr_key, value=value)


def declare_attr_index(substrate: _PySubstrate | Any, node_type: str, attr_key: str) -> None:
    """Declare a secondary attribute index. Idempotent. Existing
    matching nodes are back-filled on declaration; subsequent
    insert/delete/set_attr/set_type maintain the index automatically.
    """
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    inner.declare_attr_index(node_type, attr_key)


def has_attr_index(substrate: _PySubstrate | Any, node_type: str, attr_key: str) -> bool:
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.has_attr_index(node_type, attr_key)


def nodes_where(substrate: _PySubstrate | Any, node_type: str, attr_key: str, value: Any) -> list:
    """Direct indexed lookup — same answer as evaluating `NodesWhere(...)`,
    minus the Term construction. Returns a list of NodeID."""
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.nodes_where(node_type, attr_key, value)


# --- Lifecycle hooks (Phase 7b) ---------------------------------------

def register_hook(substrate: _PySubstrate | Any, event: str, callback) -> None:
    """Register `callback` to fire on `event`. Multiple callbacks per
    event are supported and fire in registration order. The callback
    runs on the same thread as the mutation; a raising callback
    propagates as a Python exception out of the substrate call.

    Events and their callback signatures:
      * "node_inserted"  → (nid: NodeID, type: str)
      * "node_deleted"   → (nid: NodeID, type: str)
      * "edge_inserted"  → (src: NodeID, edge_type: str, tgt: NodeID)
      * "edge_deleted"   → (src: NodeID, edge_type: str, tgt: NodeID)
      * "attr_set"       → (nid: NodeID, key: str, old: Any, new: Any)
    """
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    inner.register_hook(event, callback)


def clear_hooks(substrate: _PySubstrate | Any) -> None:
    """Drop every registered hook callback."""
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    inner.clear_hooks()


# --- Rewrite rules (Phase 7c) ----------------------------------------

def _encode_effect_arg(v: Any) -> Any:
    """Encode an effect argument for the wire format. A Term wraps
    into `{"__term__": <term dict>}`; everything else passes through
    as a literal."""
    if isinstance(v, Term):
        return {"__term__": v.to_dict()}
    return v


def _encode_attrs(attrs: dict[str, Any] | None) -> dict[str, Any]:
    if not attrs:
        return {}
    return {k: _encode_effect_arg(v) for k, v in attrs.items()}


def AddEdge(src_var: str, edge_type: str, tgt_var: str, attrs: dict | None = None) -> list:
    """Effect: add an edge between bound variables. `attrs` values may
    be literals or Terms — Terms get evaluated under the match binding
    at apply time."""
    return ["add_edge", src_var, edge_type, tgt_var, _encode_attrs(attrs)]


def DelEdge(src_var: str, edge_type: str, tgt_var: str) -> list:
    return ["del_edge", src_var, edge_type, tgt_var]


def AddNode(new_var: str, type_: str, attrs: dict | None = None) -> list:
    """Effect: insert a new node. `new_var` becomes bound to the new
    NodeID in subsequent effects of the same rule."""
    return ["add_node", new_var, type_, _encode_attrs(attrs)]


def DelNode(var: str) -> list:
    return ["del_node", var]


def SetAttr(var: str, key: str, value: Any) -> list:
    """Effect: set / overwrite an attribute. `value` may be a literal
    or a Term (evaluated at apply time)."""
    return ["set_attr", var, key, _encode_effect_arg(value)]


def FbSample(fb: Any, game_var: str, grid_w: Any, grid_h: Any) -> list:
    """PERCEPTION-AS-ACTION effect: a rule triggers a shared-memory
    framebuffer sample — the "when to look" decision made by the
    agent's own rules instead of a host `fb_sample` call. Mints/updates
    the same `WorldInstance`/Cell + `Region` graph state
    `Substrate.fb_sample` does directly.

    Args:
        fb: the `fb_id` a prior `fb_attach` call returned — a literal
            int or a Term (evaluated at apply time).
        game_var: name of an ALREADY-BOUND match variable holding the
            `WorldInstance`/game root NodeID `segment_and_track` mints/
            updates Regions under (a bare var name, like `AddEdge`'s
            `src_var`/`tgt_var` — not itself an effect arg).
        grid_w / grid_h: the downsample grid dimensions — literal ints
            or Terms.

    A driver authoring a "look rule" typically pairs this with a
    `where=Gt(FbFrameSeq(Lit(fb_id)), Attr(Var(game_var), "last_looked_seq"))`
    gate and a trailing `SetAttr(game_var, "last_looked_seq",
    FbFrameSeq(Lit(fb_id)))` effect that advances the watermark — so the
    rule fires exactly once per genuinely new frame and stays silent
    (no churn) once caught up. See
    `runners/dsl/src/rewrite.rs::tests::fb_frame_seq_gates_where_clause`
    and `tests/test_rule_driven_look.py` for the full shape.
    """
    return ["fb_sample", _encode_effect_arg(fb), game_var,
            _encode_effect_arg(grid_w), _encode_effect_arg(grid_h)]


def add_rule(
    substrate: _PySubstrate | Any,
    name: str,
    match_edges: list[tuple[str, str, str]],
    effects: list,
    where: Term | None = None,
) -> int:
    """Register a rewrite rule with the substrate.

    Args:
        name: human-readable label; used for diagnostics.
        match_edges: list of `(src_var, edge_type, tgt_var)` triples —
            the pattern. Variables are strings; the engine resolves
            them to NodeIDs during matching.
        effects: list of effect ops, each produced by `AddEdge` /
            `DelEdge` / `AddNode` / `DelNode` / `SetAttr`.
        where: optional Term side-condition evaluated over the match
            binding. False → no match.

    Returns:
        Integer rule index. Pass to `apply_rule_once` or use
        `run_rules` to fire all rules to a fixed point.
    """
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    rule = {
        "name": name,
        "match": [list(e) for e in match_edges],
        "where": where.to_dict() if where is not None else None,
        "effects": effects,
    }
    return inner.add_rule(rule)


def apply_rule_once(substrate: _PySubstrate | Any, rule_idx: int) -> bool:
    """Find one match for `rule_idx` and apply its effects. Returns
    True iff a match was found and applied."""
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.apply_rule_once(rule_idx)


def run_rules(substrate: _PySubstrate | Any, max_steps: int = 100_000) -> int:
    """Apply every registered rule to a fixed point. Returns the number
    of rewrite steps taken before no rule matched anymore (or
    `max_steps` was reached)."""
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.run_rules(max_steps)


def rule_count(substrate: _PySubstrate | Any) -> int:
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.rule_count()


# --- Module / namespace system (Phase 7d) ----------------------------

def _prefix_type(t: str, ns: str, exclude: set[str]) -> str:
    """Prefix `t` with `ns:` unless it's already in `exclude` (callers
    can pin shared types — e.g. `NodeID`, primitive types — that
    shouldn't be namespaced)."""
    if t in exclude or ":" in t:
        # Already-namespaced or excluded — leave as-is.
        return t
    return f"{ns}:{t}"


def _prefix_term(term_json: dict[str, Any], ns: str, exclude: set[str]) -> dict[str, Any]:
    """Walk a Term JSON tree, rewriting Lit-string-values and
    Neighbours/InNeighbours/MapNeighbours edge_type fields under the
    namespace. Variable names (Var.name, Filter.var_name, etc.) are
    NOT namespaced — they're scope-local to the Term.
    """
    if not isinstance(term_json, dict) or "type" not in term_json:
        return term_json
    out = dict(term_json)
    kind = term_json["type"]
    # Lit values that look like types — heuristic: a Str whose value
    # appears in the grammar. We can't know the grammar from here, so
    # we leave Lit values alone. (A more sophisticated import_grammar
    # tracks which strings are types and rewrites only those.)
    if kind in ("Neighbours", "InNeighbours", "MapNeighbours", "Edges"):
        et = term_json.get("edge_type")
        if isinstance(et, str):
            out["edge_type"] = _prefix_type(et, ns, exclude)
    if kind in ("Attr", "EdgeAttr"):
        # Attribute keys (like "state", "label") are NOT types — leave
        # them. Only their owning type would be namespaced (and that's
        # encoded by the Production, not here).
        pass
    # Recurse into child fields.
    for k, v in term_json.items():
        if isinstance(v, dict) and "type" in v:
            out[k] = _prefix_term(v, ns, exclude)
        elif isinstance(v, list) and v and isinstance(v[0], dict) and "type" in v[0]:
            out[k] = [_prefix_term(x, ns, exclude) for x in v]
    return out


def import_grammar(
    substrate: _PySubstrate | Any,
    grammar_json: dict[str, Any],
    namespace: str,
    exclude: list[str] | set[str] | None = None,
) -> int:
    """Add every production in `grammar_json` to `substrate`, prefixing
    every node-type, edge-type, and provenance with `namespace:`. This
    lets a caller pull a published grammar module (e.g. a published
    `chess` ruleset) into a substrate that already has its own
    grammar, without type-name collisions.

    `exclude` is a set of type names that are shared and should NOT be
    namespaced — for example, primitive types or types already namespaced.
    A type already containing `:` is treated as already-namespaced and
    left alone.

    Returns the number of productions imported. Raises ValueError if
    the namespace is empty or contains `:`.
    """
    if not namespace or ":" in namespace:
        raise ValueError(f"namespace must be a non-empty string without ':' — got {namespace!r}")
    exclude_set = set(exclude or ())
    productions = grammar_json.get("productions", [])
    imported = 0
    for pd in productions:
        # Build a namespaced clone of the production JSON.
        src = pd["src"]
        tgt = pd["tgt"]
        new_pd = {
            "name": pd.get("name", ""),  # kept verbatim for diagnostics
            "src": {
                "type": _prefix_type(src["type"], namespace, exclude_set),
                "var": src["var"],
            },
            "edge_type": _prefix_type(pd["edge_type"], namespace, exclude_set),
            "tgt": {
                "type": _prefix_type(tgt["type"], namespace, exclude_set),
                "var": tgt["var"],
            },
            "where": _prefix_term(pd["where"], namespace, exclude_set) if pd.get("where") else None,
            "weight": pd.get("weight"),  # weight Terms passed through; the
                                        # type vocabulary they reference is
                                        # the env's, not Γ's, so no rewrite.
            "provenance": f"{namespace}:{pd.get('provenance', '')}",
        }
        inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
        # Wrap in the {"productions": [...]} shape add_production expects.
        inner.add_production(new_pd)
        imported += 1
    return imported


def namespaced_type(namespace: str, type_: str) -> str:
    """Convenience: build a `namespace:type_` string the same way
    `import_grammar` does. Useful when the caller is adding nodes that
    should land under an imported namespace."""
    if ":" in type_:
        return type_
    return f"{namespace}:{type_}"


# --- Backtracking search (Phase 7d) ----------------------------------
#
# Ports the search_count / search_count_general / search_sum
# primitives from `domains/graph_rewrite.py`. The strategy lives in
# graph-resident Terms (open / options / fail / accept / value);
# control flow stays on the Python side because the recursion depths
# typical of these algorithms (10-30 levels for coset enumeration,
# Knuth-Bendix word reduction, etc.) sit well within Python's default
# stack and benefit from the simpler debuggability of pure Python.

def _native_substrate(substrate: _PySubstrate | Any) -> Any:
    """Resolve the wrapped native substrate."""
    return substrate._inner if isinstance(substrate, _PySubstrate) else substrate


def search_count(
    substrate: _PySubstrate | Any,
    open_term: Term,
    options_term: Term,
    assign_edge: str,
    fail_term: Term,
    env: dict[str, Any] | None = None,
) -> int:
    """Graph-resident backtracking DFS counting solutions.

    Strategy (all graph-resident Terms):
      * `open_term`    yields the undecided items (set of NodeIDs);
      * `options_term` yields candidate assignments for the lowest
        open item;
      * `fail_term`    boolean — true ⇒ prune (a constraint violated);
      * `assign_edge`  edge-type used to mark `item -[assign_edge]-> opt`
        while the DFS recurses; the edge is removed on backtrack.

    If `open_term` is empty AND `fail_term` is false, the leaf counts
    as one solution.
    """
    inner = _native_substrate(substrate)
    base_env = dict(env or {})
    if inner.evaluate(fail_term._json, base_env):
        return 0
    opens = inner.evaluate(open_term._json, base_env)
    if not opens:
        return 1
    # Deterministic choice — match Python `min(... key=lambda n: n.value)`
    # so the search is reproducible across runs.
    item = min(opens, key=lambda n: n.value)
    options = inner.evaluate(options_term._json, base_env)
    total = 0
    for opt in options:
        inner.add_edge_unchecked(item, assign_edge, opt)
        total += search_count(substrate, open_term, options_term, assign_edge, fail_term, env)
        inner.remove_edge_unchecked(item, assign_edge, opt)
    return total


def apply_rule_with_undo(
    substrate: _PySubstrate | Any,
    rule_idx: int,
    binding: dict[str, "NodeID"],  # noqa: F821 (forward ref)
) -> Callable[[], None]:
    """Apply rule `rule_idx` under a caller-supplied binding,
    returning a callable that undoes the apply (replays the undo
    steps in reverse). Used as the `apply_option` callback for
    `search_count_general` — the caller provides the binding (say,
    `{"item": cur, "opt": choice}`) and the rule's match_edges should
    be empty (or self-consistent under the provided binding).

    Returns an `undo()` callable; call it on backtrack.
    """
    # This calls into a future PyO3 method that applies a rule under
    # an externally-supplied binding with undo. For Phase 7d we
    # provide a Python fallback that goes through add_rule + a one-
    # shot apply — equivalent but slower than a dedicated path.
    raise NotImplementedError(
        "apply_rule_with_undo: requires per-effect undo plumbing through "
        "the PyO3 layer; use search_count for assign-edge style search, "
        "or build the search-step rule yourself and call apply_rule_once."
    )


def search_count_general(
    substrate: _PySubstrate | Any,
    *,
    open_term: Term,
    options_term: Term,
    apply_option: Callable[[Any, "NodeID", "NodeID"], Callable[[], None]],  # noqa: F821
    fail_term: Term | None = None,
    accept_term: Term | None = None,
    env: dict[str, Any] | None = None,
) -> int:
    """Generic backtracking DFS where the assign-step is a caller
    supplied `apply_option(substrate, item, opt) -> undo_callable`.
    Same strategy shape as `search_count` but lifts the assign-edge
    specialisation so callers can apply any rewrite step (including
    multi-effect rules) per option.
    """
    inner = _native_substrate(substrate)
    base_env = dict(env or {})
    if fail_term is not None and inner.evaluate(fail_term._json, base_env):
        return 0
    opens = inner.evaluate(open_term._json, base_env)
    if not opens:
        if accept_term is None or inner.evaluate(accept_term._json, base_env):
            return 1
        return 0
    item = min(opens, key=lambda n: n.value)
    options = inner.evaluate(options_term._json, base_env)
    total = 0
    for opt in options:
        undo = apply_option(substrate, item, opt)
        total += search_count_general(
            substrate,
            open_term=open_term,
            options_term=options_term,
            apply_option=apply_option,
            fail_term=fail_term,
            accept_term=accept_term,
            env=env,
        )
        undo()
    return total


def search_sum(
    substrate: _PySubstrate | Any,
    *,
    open_term: Term,
    options_term: Term,
    apply_option: Callable[[Any, "NodeID", "NodeID"], Callable[[], None]],  # noqa: F821
    value_term: Term,
    fail_term: Term | None = None,
    env: dict[str, Any] | None = None,
) -> Any:
    """Backtracking DFS summing `value_term` over every complete leaf.

    Same shape as `search_count_general`. At each leaf (no open items)
    the search evaluates `value_term` (under the same env) and adds it
    to the running total. The lowest open item is bound as `"item"`
    in the env passed to nested `options_term` evaluations so the
    options can depend on the current item.

    Common use: determinant = ∑_perm sign(perm) × ∏ entries — the
    search enumerates permutations, value_term computes the signed
    product per leaf.
    """
    inner = _native_substrate(substrate)
    base_env = dict(env or {})
    if fail_term is not None and inner.evaluate(fail_term._json, base_env):
        return 0
    opens = inner.evaluate(open_term._json, base_env)
    if not opens:
        return inner.evaluate(value_term._json, base_env)
    item = min(opens, key=lambda n: n.value)
    item_env = {**base_env, "item": item}
    total = 0
    options = inner.evaluate(options_term._json, item_env)
    for opt in options:
        undo = apply_option(substrate, item, opt)
        total += search_sum(
            substrate,
            open_term=open_term,
            options_term=options_term,
            apply_option=apply_option,
            value_term=value_term,
            fail_term=fail_term,
            env=env,
        )
        undo()
    return total


# Convenience: a stock apply_option that adds + removes a single edge.
# Lets callers reach the search_count_general / search_sum surface
# without writing the undo-closure boilerplate.
def assign_edge_apply(edge_type: str) -> Callable[[Any, "NodeID", "NodeID"], Callable[[], None]]:  # noqa: F821
    """Returns an `apply_option` callback that adds `item -[edge_type]-> opt`
    and yields an `undo()` that removes it. Suitable for the same
    search shape `search_count` handles, but reusable through the
    generic search surface."""
    def _apply(substrate, item, opt):
        inner = _native_substrate(substrate)
        inner.add_edge_unchecked(item, edge_type, opt)
        def _undo():
            inner.remove_edge_unchecked(item, edge_type, opt)
        return _undo
    return _apply


# --- Observability --------------------------------------------------------

def counters(substrate: _PySubstrate | Any) -> dict[str, Any]:
    """Snapshot the per-Substrate counters.

    Returns a dict with:
        nodes_inserted_total              int  (cumulative)
        nodes_inserted_by_type            dict[type, int]
        edges_inserted_total              int
        edges_inserted_by_type            dict[edge_type, int]
        admissibility_checks_total        int
        rejections_type1                  int   (Γ has no admitting production)
        rejections_type2                  int   (vocabulary absent)
        evaluations_total                 int
        cache_neighbours_hits, misses     int
        cache_filter_hits, misses         int
        production_admits                 dict[provenance, int]
        production_rejects                dict[provenance, int]
        rho_g_size                        int   (|G| — node_count + edge_count)
    """
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    return inner.counters()


def counters_clear(substrate: _PySubstrate | Any) -> None:
    """Reset every counter to 0. Useful when sampling over a window."""
    inner = substrate._inner if isinstance(substrate, _PySubstrate) else substrate
    inner.counters_clear()


def cache_hit_rate(snapshot: dict[str, Any]) -> dict[str, float]:
    """Compute hit-rate fractions from a counters() snapshot. Returns
    a dict with `neighbours` and `filter` keys (each in [0.0, 1.0],
    or 0.0 when the cache was never probed)."""
    def _rate(hits: int, misses: int) -> float:
        total = hits + misses
        return (hits / total) if total else 0.0

    return {
        "neighbours": _rate(
            snapshot.get("cache_neighbours_hits", 0),
            snapshot.get("cache_neighbours_misses", 0),
        ),
        "filter": _rate(
            snapshot.get("cache_filter_hits", 0),
            snapshot.get("cache_filter_misses", 0),
        ),
    }


__all__ = [
    "Union", "Intersect", "Difference", "MapSet",
    "Edges", "EdgeAttr",
    "NodesWhere", "declare_attr_index", "has_attr_index", "nodes_where",
    "register_hook", "clear_hooks",
    "counters", "counters_clear", "cache_hit_rate",
    "AddEdge", "DelEdge", "AddNode", "DelNode", "SetAttr",
    "add_rule", "apply_rule_once", "run_rules", "rule_count",
    "import_grammar", "namespaced_type",
    "search_count", "search_count_general", "search_sum", "assign_edge_apply",
]
