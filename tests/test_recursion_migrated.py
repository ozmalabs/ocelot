"""RECURSION, migrated — a concept whose definition references its OWN name,
grounded and evaluated on the seed-booted ``WorldAdapter`` (NO ``CuriousAgent``).

"Infinity is just recursion backwards": ℕ is not stored, it is the base 0 plus
the successor rule, and any number is comprehended by recursing BACKWARD down
the successor graph to 0. A recursive concept is a self-referential definition
the recursion WALKS down its own structure to a base case:
  • reachable_from_zero(x) := x==0 OR reachable_from_zero(predecessor(x));
  • factorial(x) := 1 if x<=0 else x * factorial(predecessor(x))  — a QUANTITY;
  • add / sub / mod from succ/pred only, each returning a NODE so they compose;
  • power(g,k) over a cyclic group — recover g^k by applying the generator k
    times; finiteness = whether the recursion closes back to the identity.

How recursion is expressed on the substrate
--------------------------------------------
The Rust ``Holds`` arm carries a visited-set cycle guard
(``holds_stack.contains(concept)`` -> None), so a concept that invokes its OWN
name via ``Holds`` is treated as a true cycle and bails BEFORE the base case
unrolls — ``Holds`` self-recursion does not run. ``EvalSubgraph`` shares only
the depth budget (no visited-set), so SELF-recursion is expressed by
re-evaluating the concept's OWN ``definition`` subgraph with the recursing
variable(s) rebound: ``WorldAdapter.self_call`` builds that call,
``learn_recursive_concept`` grounds the definition as a ``Concept``'s
``definition`` subgraph, ``eval_recursive`` runs it (auto-binding the self
pointer). Every DECISION is the definition Term, evaluated in Rust; the adapter
only ingests the definition and runs it.

Coverage vs ``tests/test_recursion`` (the CuriousAgent original)
---------------------------------------------------------------
  • test_recursive_predicate_reachable_from_zero  -> migrated in full
  • test_recursive_quantity_factorial             -> migrated in full
  • test_arithmetic_built_from_successor           -> add/sub/mod migrated in
        full; gcd-by-Euclid is NOT covered — the gcd∘mod∘sub composition
        re-evaluates a self subgraph per step and EXCEEDS the Rust ``holds``
        depth budget (32), which the Python original avoided (its budget is
        100 and Python ``Holds`` adds no per-call subgraph frame). A Rust depth
        bump / iterative tick form would be required; not done here (no Rust).
  • test_group_by_generator_rule_recovers_powers_by_recursion -> migrated full
  • test_finite_vs_infinite_by_closure            -> migrated in full
Because gcd cannot be covered, the original ``tests/test_recursion.py`` is KEPT.
"""
from __future__ import annotations

import math

from substrate.world_adapter import WorldAdapter
from domains.number_world import NumberWorld
from domains.structure_world import StructureWorld

# --- Term-tree builders (JSON the substrate evaluates) ----------------------
_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_M = lambda v: {"type": "Attr", "node": _V(v), "key": "value"}

# walk the successor graph BACKWARD (predecessors of x) — the recursion's edge.
_PRED_SET = {"type": "InNeighbours", "node": _V("x"), "edge_type": "succ"}
# pred / succ that yield a NODE (the single neighbour), so recursion composes.
_PRED = lambda v: {"type": "Pick", "source": {
    "type": "InNeighbours", "node": _V(v), "edge_type": "succ"}}
_SUCC = lambda v: {"type": "Pick", "source": {
    "type": "Neighbours", "node": _V(v), "edge_type": "succ"}}
_GACT = lambda v: {"type": "Pick", "source": {
    "type": "Neighbours", "node": _V(v), "edge_type": "g_acts"}}


def _number_adapter(up_to: int = 20):
    """Boot the seed agent, walk the number line perceiving 0..up_to.
    Returns (adapter, {value -> Number NodeID})."""
    wa = WorldAdapter()
    world = NumberWorld(max_n=up_to + 4)
    substrate, ctx = world.reset()
    wa.observe(substrate)
    for _ in range(up_to):
        substrate, ctx = world.apply_action(ctx, ("count_up",))
        wa.observe(substrate)
    nums = {wa.instance_attr(nid, "value"): nid
            for nid in wa.instances("Number").values()}
    return wa, nums


def test_recursive_predicate_reachable_from_zero():
    """reachable_from_zero(x) := x==0 OR exists p in pred(x): reachable(p).
    The recursive definition of the naturals (a predicate) — its own name
    invoked over the reflexive successor structure, bottoming out at 0."""
    wa, nums = _number_adapter()
    reachable = {"type": "Or", "items": [
        {"type": "Eq", "a": _M("x"), "b": _L(0)},
        {"type": "Exists", "source": _PRED_SET, "var_name": "p",
         "predicate": WorldAdapter.self_call(("x", _V("p")))}]}
    wa.learn_recursive_concept("reachable_from_zero", reachable)
    assert wa.recursive_concept("reachable_from_zero") is not None  # self-ref grounds
    for k in (0, 1, 5, 12, 20):
        assert bool(wa.eval_recursive("reachable_from_zero", {"x": nums[k]})) is True


def test_recursive_quantity_factorial():
    """factorial(x) := 1 if x<=0 else x * sum_{p in pred(x)} factorial(p).
    A recursive QUANTITY — the self-reference returns a VALUE, not just a bool."""
    wa, nums = _number_adapter()
    factorial = {"type": "IfThenElse",
                 "cond": {"type": "Lte", "a": _M("x"), "b": _L(0)},
                 "then": _L(1),
                 "other": {"type": "Times", "items": [
                     _M("x"),
                     {"type": "Sum", "source": _PRED_SET, "var_name": "p",
                      "value": WorldAdapter.self_call(("x", _V("p")))}]}}
    wa.learn_recursive_concept("factorial", factorial)
    assert wa.recursive_concept("factorial") is not None
    for k in (0, 1, 3, 5, 7):
        assert wa.eval_recursive("factorial", {"x": nums[k]}) == math.factorial(k)


def test_arithmetic_built_from_successor():
    """add / sub / mod defined recursively from succ/pred only (no Plus/Times),
    each returning a NODE so they compose (mod calls sub).

    gcd-by-Euclid is intentionally OMITTED: gcd∘mod∘sub re-evaluates a self
    subgraph per step and overruns the Rust ``holds`` depth budget (32). See
    the module docstring; the original ``test_recursion`` covers it via the
    Python evaluator's depth-100 budget."""
    wa, nums = _number_adapter(up_to=40)

    add = {"type": "IfThenElse",
           "cond": {"type": "Eq", "a": _M("y"), "b": _L(0)}, "then": _V("x"),
           "other": WorldAdapter.self_call(("x", _SUCC("x")), ("y", _PRED("y")))}
    sub = {"type": "IfThenElse",
           "cond": {"type": "Eq", "a": _M("y"), "b": _L(0)}, "then": _V("x"),
           "other": WorldAdapter.self_call(("x", _PRED("x")), ("y", _PRED("y")))}
    wa.learn_recursive_concept("add", add)
    sub_cid = wa.learn_recursive_concept("sub", sub)
    assert wa.recursive_concept("add") is not None
    assert sub_cid is not None

    # mod(x,y) := x if x<y else mod(sub(x,y), y) — COMPOSES the grounded `sub`
    # (cross-call via `call_concept`, which switches `recur_self` to the `sub`
    # node bound as `subc` so sub recurses on ITSELF), then self-recurses.
    call_sub = lambda x, y: WorldAdapter.call_concept("subc", ("x", x), ("y", y))
    mod = {"type": "IfThenElse",
           "cond": {"type": "Lt", "a": _M("x"), "b": _M("y")}, "then": _V("x"),
           "other": WorldAdapter.self_call(
               ("x", call_sub(_V("x"), _V("y"))), ("y", _V("y")))}
    mod_cid = wa.learn_recursive_concept("mod", mod)
    assert mod_cid is not None

    # gcd(x,y) := x if y==0 else gcd(y, mod(x,y)) — Euclid, COMPOSES mod (which
    # composes sub). Now expressible: the Rust EvalSubgraph depth budget was
    # raised to 256, so gcd∘mod∘sub bottoms out within budget.
    # capture mod(x,y) and y into temps in the ORIGINAL env (the rebind x<-y,
    # y<-mod(x,y) is simultaneous; sequential self_call Lets would let x's new
    # value leak into mod's args), then self-recurse on the temps.
    call_mod = lambda x, y: WorldAdapter.call_concept("modc", ("x", x), ("y", y))
    gcd = {"type": "IfThenElse",
           "cond": {"type": "Eq", "a": _M("y"), "b": _L(0)}, "then": _V("x"),
           "other": {"type": "Let", "name": "gm", "value": call_mod(_V("x"), _V("y")),
                     "body": {"type": "Let", "name": "gy", "value": _V("y"),
                              "body": WorldAdapter.self_call(
                                  ("x", _V("gy")), ("y", _V("gm")))}}}
    wa.learn_recursive_concept("gcd", gcd)

    def num(node):
        return wa.inner.node(node)["attrs"]["value"]

    assert num(wa.eval_recursive("add", {"x": nums[7], "y": nums[5]})) == 12
    assert num(wa.eval_recursive("sub", {"x": nums[20], "y": nums[8]})) == 12
    # mod needs the `sub` concept node in env for its inner cross-call.
    assert num(wa.eval_recursive("mod", {"x": nums[13], "y": nums[5],
                                         "subc": sub_cid})) == 3
    assert num(wa.eval_recursive("mod", {"x": nums[30], "y": nums[7],
                                         "subc": sub_cid})) == 2
    # gcd needs the mod + sub concept nodes in env for its nested cross-calls.
    g = lambda a, b: num(wa.eval_recursive(
        "gcd", {"x": nums[a], "y": nums[b], "modc": mod_cid, "subc": sub_cid}))
    assert g(12, 8) == 4
    assert g(17, 5) == 1
    assert g(6, 4) == 2


def _power_definition():
    """power(x,k) := x if k==0 else power(g_acts(x), pred(k)) — apply the
    generator k times by recursion (the exponent crosses the number floor,
    the generator the group floor)."""
    return {"type": "IfThenElse",
            "cond": {"type": "Eq", "a": {"type": "Attr", "node": _V("y"),
                                         "key": "value"}, "b": _L(0)},
            "then": _V("x"),
            "other": WorldAdapter.self_call(("x", _GACT("x")), ("y", _PRED("y")))}


def _group_adapter(n_count: int, n_focus: int):
    wa = WorldAdapter()
    nw = NumberWorld(max_n=n_count + 2)
    s, c = nw.reset()
    wa.observe(s)
    for _ in range(n_count):
        s, c = nw.apply_action(c, ("count_up",))
        wa.observe(s)
    sw = StructureWorld()
    s, c = sw.reset()
    wa.observe(s)
    for _ in range(n_focus):
        s, c = sw.apply_action(c, ("focus_next",))
        wa.observe(s)
    nums = {wa.instance_attr(nid, "value"): nid
            for nid in wa.instances("Number").values()}
    inst = dict(wa.instances("GElem"))
    return wa, nums, inst


def test_group_by_generator_rule_recovers_powers_by_recursion():
    """A cyclic group given ONLY by its generator cycle (no Cayley table): the
    agent recovers g^k by recursion (apply g_acts k times)."""
    wa, nums, inst = _group_adapter(n_count=11, n_focus=8)
    wa.learn_recursive_concept("power", _power_definition())
    assert wa.recursive_concept("power") is not None
    e0 = inst["C5_e0"]
    for k in (0, 1, 3, 5, 7, 10):
        node = wa.eval_recursive("power", {"x": e0, "y": nums[k]})
        assert wa.inner.node(node)["attrs"]["world_id"] == f"C5_e{k % 5}"


def test_finite_vs_infinite_by_closure():
    """Same generator rule; finiteness is exactly whether the recursion closes
    back to the identity. C5 (cycle closes) is finite; Zinf (open chain) is not
    — 'infinity is the recursion that never closes back'."""
    wa, nums, inst = _group_adapter(n_count=12, n_focus=14)

    # the generator cycle closes for C5, not for the infinite chain (read off
    # the mirrored instance g_acts edges).
    assert wa.instance_neighbours(inst["C5_e4"], "g_acts")       # closes
    assert not wa.instance_neighbours(inst["Zinf_e11"], "g_acts")  # open

    wa.learn_recursive_concept("power", _power_definition())

    # finite_order(x): exists a known positive number k (1..10) with
    # power(x,k)==x — i.e. the orbit returns to x. COMPOSES the grounded
    # `power` concept (cross-call via `call_concept`, the `power` node bound as
    # `powc`) inside the Exists predicate.
    call_power = lambda x, k: WorldAdapter.call_concept("powc", ("x", x), ("y", k))

    known_pos = {"type": "Filter",
                 "source": {"type": "Neighbours", "node": _V("agent"),
                            "edge_type": "knows"},
                 "var_name": "k",
                 "predicate": {"type": "And", "items": [
                     {"type": "Eq", "a": {"type": "Attr", "node": _V("k"),
                                          "key": "world_type"}, "b": _L("Number")},
                     {"type": "Gt", "a": _M("k"), "b": _L(0)},
                     {"type": "Lte", "a": _M("k"), "b": _L(10)}]}}
    finite_order = {"type": "Exists", "source": known_pos, "var_name": "k",
                    "predicate": {"type": "Eq",
                                  "a": call_power(_V("x"), _V("k")),
                                  "b": _V("x")}}
    powc = wa.recursive_concept("power")

    def ev(node):
        return bool(wa.inner.evaluate(
            finite_order, {"x": node, "powc": powc,
                           "agent": wa.agent, "self": wa.agent}))

    assert ev(inst["C5_e0"]) is True       # cycle closes -> finite
    assert ev(inst["Zinf_e0"]) is False    # never returns -> infinite
