"""term_graph — the agent's code as INTROSPECTABLE graph.

A Term-tree is graph structure. The legacy mechanism `term_to_subgraph`
(substrate/dsl.py) already materialises a Term into one node per Term-node + a
`child.<field>` edge per subterm — so the agent can READ and REWRITE its own
programs as graph, not as opaque dict-blobs. This module does the same for the
NATIVE Term dicts the agent composes today.

Once a Term is materialised, the "primitives" the agent was missing are just GRAPH
OPERATIONS over it: skeletonise = walk the tree and hollow the Attr/Lit leaves;
instantiate = walk and fill them. No Rust primitive, no opaque Python — the
transform is graph traversal the agent can introspect (and, eventually, do with a
rewrite Rule). See [[ozma_concepts_in_gamma]] / [[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

from substrate_rs import Eq, And, Attr, Lit, Var


def materialize_term(substrate, d, field=None, index=None):
    """Insert a native Term dict as a subgraph (TermNode per node, `child` edges).
    Returns the root NodeID. The agent's code becomes introspectable graph."""
    attrs = {"term_type": d.get("type", "?"), "skel": 0}
    if field is not None:
        attrs["_field"] = field
    if index is not None:
        attrs["_index"] = index
    kids = []
    for k, v in d.items():
        if k == "type":
            continue
        if isinstance(v, dict):
            kids.append((k, None, v))
        elif isinstance(v, list):
            for i, it in enumerate(v):
                if isinstance(it, dict):
                    kids.append((k, i, it))
        else:
            attrs[k] = v
    try:
        substrate.add_production({
            "src": {"type": "TermNode", "var": "a"}, "edge_type": "child",
            "tgt": {"type": "TermNode", "var": "b"},
            "provenance": "term_graph:child"})
    except Exception:
        pass
    nid = substrate.add_node("TermNode", attrs)
    for f, idx, cv in kids:
        substrate.add_edge(nid, "child", materialize_term(substrate, cv, f, idx))
    return nid


def dematerialize_term(substrate, nid) -> dict:
    """Rebuild the runnable Term dict from its subgraph (the native
    term_from_subgraph)."""
    a = dict(substrate.node(nid)["attrs"])
    ty = a.pop("term_type")
    for bookkeeping in ("_field", "_index", "skel"):
        a.pop(bookkeeping, None)
    d = {"type": ty, **a}
    by_field = {}
    for c in substrate.neighbours(nid, "child"):
        ca = substrate.node(c)["attrs"]
        field, idx = ca.get("_field"), ca.get("_index")
        child = dematerialize_term(substrate, c)
        if idx is None:
            d[field] = child
        else:
            by_field.setdefault(field, []).append((idx, child))
    for field, items in by_field.items():
        d[field] = [ch for _, ch in sorted(items)]
    return d


def skeletonize_graph(substrate, root) -> None:
    """Skeletonise IN THE GRAPH (the simple Python-walk version): hollow the leaves
    (Attr key -> ?band, Lit value -> ?lit). Kept for reference; the graph-native
    form is compose_skeletonize_rules below."""
    stack = [root]
    while stack:
        n = stack.pop()
        ty = substrate.node(n)["attrs"].get("term_type")
        if ty == "Attr":
            substrate.set_attr(n, "key", "?band")
        elif ty == "Lit":
            substrate.set_attr(n, "value", "?lit")
        stack.extend(substrate.neighbours(n, "child"))


def compose_skeletonize_rules(substrate) -> list:
    """The agent COMPOSES the skeletonise TRANSFORM as graph rewrite RULES over its
    own materialised code — the same move as compose_selection_rule, now for a
    code transform. Two rules: 'a TermNode that is an Attr (and not yet hollowed)
    -> set its key to ?band'; likewise Lit -> ?lit. The decision + the rewrite are
    Term-trees the agent authors; the substrate's rule engine runs them. No Python
    walk. Returns the rule indices."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    try:
        substrate.add_production({
            "src": {"type": "SkeletonRoot", "var": "a"}, "edge_type": "term_node",
            "tgt": {"type": "TermNode", "var": "b"},
            "provenance": "term_graph:term_node"})
    except Exception:
        pass
    T = Var("T")
    rules = []
    for ttype, hole_key, hole_val in (("Attr", "key", "?band"),
                                      ("Lit", "value", "?lit")):
        where = And(items=(Eq(a=Attr(T, "term_type"), b=Lit(ttype)),
                           Eq(a=Attr(T, "skel"), b=Lit(0))))
        rules.append(nat.add_rule({
            "name": f"skeletonize_{ttype.lower()}",
            "match": [["R", "term_node", "T"]],
            "where": where.to_dict(),
            "effects": [
                ["set_attr", "T", hole_key, {"__term__": Lit(hole_val).to_dict()}],
                ["set_attr", "T", "skel", {"__term__": Lit(1).to_dict()}],
            ],
        }))
    return rules


def _all_termnodes(substrate, root) -> set:
    seen, stack = set(), [root]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(substrate.neighbours(n, "child"))
    return seen


def agent_skeletonize(substrate, root, rule_indices) -> None:
    """Wire a Term's nodes under a SkeletonRoot and fire the agent's OWN composed
    rewrite rules to fixed point. The transform is now graph rewriting the agent
    authored, over code it can introspect."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    sroot = next((n for n in substrate.nodes("SkeletonRoot")), None)
    if sroot is None:
        sroot = substrate.add_node("SkeletonRoot", {"origin": "agent"})
    nodes = _all_termnodes(substrate, root)
    for n in nodes:
        try:
            substrate.add_edge(sroot, "term_node", n)
        except Exception:
            pass
    for idx in rule_indices:
        for _ in range(len(nodes) + 1):
            nat.apply_rule_once(idx)


__all__ = ["materialize_term", "dematerialize_term", "skeletonize_graph",
           "compose_skeletonize_rules", "agent_skeletonize"]
