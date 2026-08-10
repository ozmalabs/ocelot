"""Re-wire test for relation_ingest — the order-N shape-matching adapter.

relation_ingest is the MECHANICAL adapter that reads the role-canonical Relation
Frame (seeds/relation_role_frame.json, graph data) and places a domain's
role-keyed relations into the Frame's declared positional order — the
representation the held AntiUnify Term needs so corresponding roles align across
SURFACE-UNRELATED domains. It was committed (370a47c3) with no test, so it read as
an orphan; this restores it to the guarded surface by exercising the capability
end-to-end (and references the module).

Control = Gentner systematicity, the same read-out as scripts/shape_math_gate.py
(has_system): a DEEP analogy (solar system <-> atom) preserves the higher-order
CAUSE system under the held AntiUnify Term; a SURFACE pairing (solar <-> billiards,
flat — no higher-order system) does not. The Frame is LOAD-BEARING at the
representation level: with role-keys given in non-canonical input order, Frame-ON
re-canonicalises (so two domains' tuples align positionally) while Frame-OFF lets
the input order leak through.
"""
import pytest
import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.relation_ingest import ingest_domain

WILD = "·?·"


# ----- role-keyed domains (predicate + {role: filler}); roles in ANY order ---------
def _rel(pred, **roles):
    return {"predicate": pred, "args": dict(roles)}


def _cause(ante, cons):
    return {"predicate": "CAUSE", "args": {"antecedent": ante, "consequent": cons}}


def _solar():
    return [_rel("attracts", central="sun", orbiter="planet"),
            _rel("revolves", orbiter="planet", central="sun"),
            _rel("greater", more="sun", less="planet"),
            _cause(_rel("attracts", central="sun", orbiter="planet"),
                   _rel("revolves", orbiter="planet", central="sun"))]


def _atom(scramble=False):
    if scramble:                       # roles given in NON-canonical input order
        return [_rel("attracts", orbiter="electron", central="nucleus"),
                _rel("revolves", central="nucleus", orbiter="electron"),
                _rel("greater", less="electron", more="nucleus"),
                _cause(_rel("attracts", orbiter="electron", central="nucleus"),
                       _rel("revolves", central="nucleus", orbiter="electron"))]
    return [_rel("attracts", central="nucleus", orbiter="electron"),
            _rel("revolves", orbiter="electron", central="nucleus"),
            _rel("greater", more="nucleus", less="electron"),
            _cause(_rel("attracts", central="nucleus", orbiter="electron"),
                   _rel("revolves", orbiter="electron", central="nucleus"))]


def _billiards():                      # SURFACE: 4 flat relations, NO higher-order system
    return [_rel("collide", first="cue", second="ball"),
            _rel("transfer", donor="cue", recipient="ball"),
            _rel("greater", more="cue", less="ball"),
            _rel("borders", thing="cue", neighbour="ball")]


# ----- held AntiUnify Term + the systematicity read-out (== shape_math_gate) -------
def _norm(x):
    return [_norm(i) for i in x] if isinstance(x, (list, tuple)) else x


def _au(ev, a, b):
    term = {"type": "AntiUnify", "values": {"type": "Lit", "value": [a, b]}, "wild": WILD}
    return ev(term, {})


def _has_system(res):
    """A higher-order CAUSE system survives with predicate-bearing (non-wild) slots."""
    return isinstance(res, tuple) and any(
        isinstance(r, tuple) and r and r[0] == "CAUSE"
        and all(isinstance(x, tuple) and x and x[0] != WILD for x in r[1:])
        for r in res)


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture(scope="module")
def ev():
    return srs._NativeSubstrate().evaluate


def _ing(agent, dom, use_frame=True):
    return _norm(ingest_domain(agent.s, dom, use_frame=use_frame))


def test_frame_canonicalises_order_independently(agent):
    # The Frame's job: place fillers by declared role order regardless of input order.
    assert _ing(agent, _atom(scramble=False)) == _ing(agent, _atom(scramble=True)), \
        "Frame-ON must canonicalise role order (input-order-independent)"


def test_frame_off_leaks_input_order(agent):
    # Without the Frame, the input dict order leaks into the tuple slots.
    assert _ing(agent, _atom(scramble=False), use_frame=False) != \
        _ing(agent, _atom(scramble=True), use_frame=False), \
        "Frame-OFF must take args as given (input order leaks) — the Frame is load-bearing"


def test_deep_analogy_preserves_system(agent, ev):
    res = _au(ev, _ing(agent, _solar()), _ing(agent, _atom()))
    assert _has_system(res), "solar<->atom (deep) must preserve the higher-order CAUSE system"


def test_surface_pairing_does_not(agent, ev):
    res = _au(ev, _ing(agent, _solar()), _ing(agent, _billiards()))
    assert not _has_system(res), "solar<->billiards (surface/flat) must NOT preserve a shared system"


def test_frame_aligns_scrambled_domain_for_matching(agent, ev):
    # Frame-ON re-canonicalises a scrambled atom so it still aligns with solar.
    res = _au(ev, _ing(agent, _solar()), _ing(agent, _atom(scramble=True), use_frame=True))
    assert _has_system(res), "Frame-ON: a scrambled domain re-canonicalises and still matches the deep system"
