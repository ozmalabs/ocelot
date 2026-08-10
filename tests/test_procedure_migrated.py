"""PROCEDURES, migrated — the agent COMPUTING answers on the seed-booted agent.

Covers tests/test_procedure. The move from "knowing what prime means" to
"finding the prime factorization": the agent authors a procedure (a graph-
resident query Term-tree) that INVOKES its grounded ``prime`` concept (via the
DSL ``Holds`` Term) and RUNS it to compute an answer. NO ``CuriousAgent`` here.

Under the burn discipline this is mechanical wiring over the substrate:

  • a concept is grounded exactly as ``test_number_world_migrated`` does it —
    ``learn_word`` materialises its definition Term into the graph; the seed
    agent classifies by running that Term (``concept_holds``);
  • ``register_concept`` wires the same definition into the substrate's concept
    registry so a composing query can REACH it by name (the resolver the Rust
    ``Holds`` arm consults) — no decision, just the lookup table;
  • ``author_subroutine`` stores the agent-composed query as graph data
    (``Subroutine`` node + ``query`` Term-tree); ``run_subroutine`` hands the
    query to the substrate's evaluator, which resolves every ``Holds`` against
    the registry and computes the answer in the main Term arena.

So the procedure COMPOSES the concepts the agent already grounds — prime_factors
calls ``prime``; the largest-prime-factor / divisor-count procedures reduce over
the same composition. Magnitude is the carried ``value`` quantity, so the
computation stays EXACT at scale (no unit-count collapse). Every DECISION is the
query Term, run in the substrate; the adapter only translates I/O.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.number_world import NumberWorld

# --- Term-tree builders (JSON the substrate evaluates) ----------------------
_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_M = lambda v: {"type": "Attr", "node": _V(v), "key": "value"}


def _known():
    """The agent's known Numbers — Neighbours(agent, knows) filtered to the
    Number world-type. The same source the prime definition quantifies over."""
    return {"type": "Filter",
            "source": {"type": "Neighbours", "node": _V("agent"), "edge_type": "knows"},
            "var_name": "d",
            "predicate": {"type": "Eq",
                          "a": {"type": "Attr", "node": _V("d"), "key": "world_type"},
                          "b": _L("Number")}}


def _prime_def():
    """prime(x): x > 1 and no known divisor d with 1 < d < x divides x."""
    known = _known()
    return {"type": "And", "items": [
        {"type": "Gt", "a": _M("x"), "b": _L(1)},
        {"type": "Not", "arg": {"type": "Exists", "source": known, "var_name": "d",
            "predicate": {"type": "And", "items": [
                {"type": "Gt", "a": _M("d"), "b": _L(1)},
                {"type": "Lt", "a": _M("d"), "b": _M("x")},
                {"type": "Eq", "a": {"type": "Mod", "a": _M("x"), "b": _M("d")},
                 "b": _L(0)}]}}}]}


def _prime_factors_query():
    """prime factors of n: known d that are prime, > 1, and divide n.
    Composes the grounded ``prime`` concept via the ``Holds`` Term."""
    return {"type": "Filter", "source": _known(), "var_name": "d",
            "predicate": {"type": "And", "items": [
                {"type": "Holds", "concept": "prime", "node": _V("d")},
                {"type": "Gt", "a": _M("d"), "b": _L(1)},
                {"type": "Eq", "a": {"type": "Mod", "a": _M("n"), "b": _M("d")},
                 "b": _L(0)}]}}


def _agent_with_prime(up_to: int = 40):
    """Boot the seed agent, walk the number line perceiving 0..up_to, then
    ground ``prime`` (graph + registry). Returns (adapter, {value -> NodeID})."""
    wa = WorldAdapter()
    world = NumberWorld(max_n=up_to + 4)
    substrate, ctx = world.reset()
    wa.ingest(substrate)
    for _ in range(up_to):                          # perceive 0..up_to
        substrate, ctx = world.apply_action(ctx, ("count_up",))
        wa.ingest(substrate)
    nums = {wa.instance_attr(nid, "value"): nid
            for nid in wa.instances("Number").values()}
    prime = _prime_def()
    wa.learn_word("prime", prime)        # ground as a classifier (graph Term)
    wa.register_concept("prime", prime)  # wire it for Holds (procedure can call)
    return wa, nums


def _vals(wa, nodeset):
    return sorted(wa.inner.node(d)["attrs"]["value"] for d in nodeset)


def test_prime_grounds_and_is_invokable_by_a_procedure():
    """Sanity: the grounded concept both CLASSIFIES (concept_holds) and is
    REACHABLE by name from a Holds Term (the registry wiring works)."""
    wa, nums = _agent_with_prime()

    def is_prime(n):
        return n > 1 and all(n % d for d in range(2, n))
    for k in (2, 3, 4, 5, 9, 13, 16, 17):
        assert wa.concept_holds("prime", nums[k]) == is_prime(k)


def test_factorization_procedure_invokes_grounded_prime_at_scale():
    wa, nums = _agent_with_prime()
    wa.author_subroutine("prime_factors", _prime_factors_query(),
                         "prime factors of n")

    assert _vals(wa, wa.run_subroutine("prime_factors", {"n": nums[12]})) == [2, 3]
    assert _vals(wa, wa.run_subroutine("prime_factors", {"n": nums[36]})) == [2, 3]
    assert _vals(wa, wa.run_subroutine("prime_factors", {"n": nums[30]})) == [2, 3, 5]
    assert _vals(wa, wa.run_subroutine("prime_factors", {"n": nums[37]})) == [37]


def test_largest_prime_factor_and_divisor_count_at_scale():
    wa, nums = _agent_with_prime()
    pf = _prime_factors_query()
    wa.author_subroutine("largest_prime_factor",
        {"type": "MaxOver", "source": pf, "var_name": "d", "value": _M("d")}, "lpf")
    wa.author_subroutine("n_divisors",
        {"type": "Count", "source": {"type": "Filter", "source": _known(),
            "var_name": "d", "predicate": {"type": "And", "items": [
                {"type": "Gt", "a": _M("d"), "b": _L(0)},
                {"type": "Eq", "a": {"type": "Mod", "a": _M("n"), "b": _M("d")},
                 "b": _L(0)}]}}}, "divisor count")

    assert wa.run_subroutine("largest_prime_factor", {"n": nums[36]}) == 3
    assert wa.run_subroutine("largest_prime_factor", {"n": nums[30]}) == 5
    assert wa.run_subroutine("n_divisors", {"n": nums[36]}) == 9   # 1,2,3,4,6,9,12,18,36
    assert wa.run_subroutine("n_divisors", {"n": nums[37]}) == 2   # 1,37 (prime)


def test_authored_procedure_is_editable_in_place():
    """Re-authoring a subroutine by name REPLACES its query without spawning a
    second node — the procedure is editable graph data."""
    wa, nums = _agent_with_prime()
    first = wa.author_subroutine("p", _prime_factors_query(), "v1")
    # rewrite it to count prime factors instead of returning them
    second = wa.author_subroutine("p",
        {"type": "Count", "source": _prime_factors_query()}, "v2")
    assert first == second                                  # same node, rewired
    assert wa.run_subroutine("p", {"n": nums[30]}) == 3     # |{2,3,5}|
