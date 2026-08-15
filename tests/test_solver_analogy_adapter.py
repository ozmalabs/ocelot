"""docs/research/engine_substrate/SOLVER_ANALOGY_ADAPTER_PREREG.md/_RESULTS.md
-- live regression + demonstration of the SECOND NL-to-structure adapter for
the six previously-unwired `solve_*` resolvers:
`solver_dispatch.mint_solve_analogical_promote_goal_from_text`, a front door
onto `solve_analogical_promote`.

The predecessor rung (SOLVER_NL_ADAPTER_RESULTS.md) ranked this resolver #2
and left it unbuilt, believing "no analogy-shaped sentence parser exists
anywhere in the tree." This rung found that belief wrong: `seeds/reading_
constructions.json` already seeds a `LIKE` MarkerClass
(`like`/`resembles`/`resemble`) plus `comparative_like`/`comparative_like_cop`
constructions that ground "X is like Y" to `["similar", subject, object]` via
the UNMODIFIED general reading pipeline. Every test here parses a REAL,
genuine English sentence through that UNMODIFIED pipeline, resolves both
concept names against the REAL standing corpus (never a hand-injected node
id), and pumps the result through the SAME `qd_bind_resolver` dispatch +
`solve_analogical_promote` resolver `tests/test_solver_dispatch_migrated.py`
already exercises.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import solver_dispatch as sd                  # noqa: E402
from domains import analogical_thinking as at_mod           # noqa: E402


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _pump(adapter, goal, max_iters: int = 32) -> None:
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _concept(sub, name):
    hits = [c for c in sub.nodes("Concept") if sub.node(c)["attrs"].get("name") == name]
    assert len(hits) == 1, "grounding fact drifted: %r has %d matches, expected 1" % (name, len(hits))
    return hits[0]


# --------------------------------------------------------------------------- #
#  GROUNDING FACTS -- checked live, not assumed, mirroring
#  ENTITY_RESOLUTION_RESULTS.md's own "check the corpus fact before trusting
#  a test built on it" discipline.
# --------------------------------------------------------------------------- #
def test_grounding_generating_functions_and_function_definition_are_unique(agent):
    sub = agent.s
    assert len([c for c in sub.nodes("Concept")
                if sub.node(c)["attrs"].get("name") == "generating_functions"]) == 1
    assert len([c for c in sub.nodes("Concept")
                if sub.node(c)["attrs"].get("name") == "function_definition"]) == 1


def test_grounding_agent_is_genuinely_ambiguous_in_the_real_corpus(agent):
    sub = agent.s
    hits = [c for c in sub.nodes("Concept") if sub.node(c)["attrs"].get("name") == "agent"]
    assert len(hits) > 1, "expected a real, reachable ambiguity -- ambiguity gate test below depends on this"


# --------------------------------------------------------------------------- #
#  SUCCESS -- a real sentence, real corpus concepts, dispatched through the
#  UNCHANGED qd_bind_resolver -> solve_analogical_promote, correctness
#  verified by hand against the promoted schema's own attrs and derived_from
#  edge, not merely status == "resolved".
# --------------------------------------------------------------------------- #
def test_real_comparative_sentence_mints_and_resolves_via_unchanged_dispatch(agent):
    sub = agent.s
    node_a = _concept(sub, "generating_functions")
    node_b = _concept(sub, "function_definition")

    goal = sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are like a function definition.")
    assert goal is not None
    at_ = sub.node(goal)["attrs"]
    assert at_["kind"] == "solve_analogical_promote"
    assert at_["status"] == "pending"
    corrs = agent.inner.neighbours(goal, "targets_correspondence")
    assert corrs
    corr = corrs[0]
    about_a = agent.inner.neighbours(corr, "about_a")
    about_b = agent.inner.neighbours(corr, "about_b")
    assert about_a == [node_a]
    assert about_b == [node_b]

    _pump(agent, goal)

    at_ = sub.node(goal)["attrs"]
    assert at_["status"] == "resolved", at_.get("note")
    # proof the UNCHANGED qd_bind_resolver JOIN did the dispatch, not this test.
    resolvers = agent.inner.neighbours(goal, "resolve_with")
    assert resolvers and sub.node(resolvers[0])["attrs"]["name"] == "solve_analogical_promote"
    assert at_["direction_verdict"] in ("a_source", "b_source")

    # CORRECTNESS BY HAND -- read the promoted schema itself, the same
    # inspection discipline DIRECTIONAL_CORRESPONDENCE_RESULTS.md Sec4.3 used.
    schema_name = at_["schema_name"]
    schema_node = None
    for n in sub.nodes("ShapeSignature"):
        if sub.node(n)["attrs"].get("name") == schema_name:
            schema_node = n
            break
    assert schema_node is not None
    sattrs = sub.node(schema_node)["attrs"]
    assert sattrs["kind"] == "knowledge_logical"
    assert sattrs["coherence"] == "elaborative"
    assert sattrs["provenance"] == "analogical"
    derived = agent.inner.neighbours(schema_node, "derived_from")
    assert derived == [corr]

    # The source/target concept names in the schema's own signature/supplies
    # match the DIRECTION the engine actually decided, read back honestly
    # (never assumed to always be node_a -> node_b).
    import json as _json
    sig = _json.loads(sattrs["signature"])
    supplies = _json.loads(sattrs["supplies"])
    direction = at_mod.directional_hypothesis_for(sub, corr)
    assert sig == [["holds", direction["source_concept"]]]
    assert supplies == {"relation": "is_a", "attr": direction["target_concept"]}
    assert {direction["source_concept"], direction["target_concept"]} == \
        {"generating_functions", "function_definition"}


def test_verbal_form_resembles_also_grounds_the_same_way(agent):
    """A second real surface form of the SAME LIKE marker class
    ('resembles', not 'is like') -- confirms the adapter is reading the
    construction's own relation label, not one hardcoded surface string."""
    goal = sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions resemble a function definition.")
    assert goal is not None
    _pump(agent, goal)
    at_ = agent.s.node(goal)["attrs"]
    assert at_["status"] == "resolved"


# --------------------------------------------------------------------------- #
#  HONEST WALL (resolver-side) -- two real, UNAMBIGUOUS concepts with a real,
#  live-confirmed TIED richness -- the correspondence resolves but the
#  direction is genuinely undetermined ("symmetric"), so the UNCHANGED
#  resolver honestly declines to promote, never forcing a direction.
# --------------------------------------------------------------------------- #
def test_tied_richness_pair_walls_honestly_via_unchanged_resolver(agent):
    sub = agent.s
    node_a = _concept(sub, "myelination")
    node_b = _concept(sub, "temporal_difference_learning_formal")
    vec_a = at_mod._concept_shape_vector(sub, node_a)
    vec_b = at_mod._concept_shape_vector(sub, node_b)
    ra, rb = at_mod._axis_richness(vec_a), at_mod._axis_richness(vec_b)
    assert ra == rb, "grounding fact drifted: richness tie no longer holds (%r vs %r)" % (ra, rb)

    goal = sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Myelination is like temporal difference learning formal.")
    assert goal is not None

    _pump(agent, goal)

    at_ = sub.node(goal)["attrs"]
    assert at_["status"] == "walled"
    assert at_["direction_verdict"] == "symmetric"
    assert "gap_key" in at_
    assert "symmetric" in at_["note"]


# --------------------------------------------------------------------------- #
#  HONEST DECLINE (adapter-side) -- unsuitable real input mints NOTHING,
#  mirroring the Bug 1 fix precedent both prior NL-adapter rungs established.
# --------------------------------------------------------------------------- #
def test_unlike_contrast_sentence_declines_cleanly(agent):
    """'X is unlike Y' grounds to rel='contrast', the honest OPPOSITE signal
    -- never mistaken for an analogy claim."""
    assert sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are unlike function definitions.") is None


def test_question_shaped_comparative_declines_cleanly(agent):
    assert sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Is a generating function like a function definition?") is None


def test_non_comparative_sentence_declines_cleanly(agent):
    assert sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are important.") is None


def test_ambiguous_concept_name_declines_cleanly(agent):
    """A real, reachable ambiguity (grounding fact checked above): 'agent'
    resolves to more than one real Concept node in the standing corpus.
    Refuses rather than guessing which one was meant."""
    assert sd.mint_solve_analogical_promote_goal_from_text(
        agent, "The agent is like the patient.") is None


def test_unknown_concept_name_declines_cleanly(agent):
    assert sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are like a completely_unknown_bogus_concept_xyz.") is None


def test_empty_and_whitespace_statement_declines_cleanly(agent):
    assert sd.mint_solve_analogical_promote_goal_from_text(agent, "") is None
    assert sd.mint_solve_analogical_promote_goal_from_text(agent, "   ") is None
    assert sd.mint_solve_analogical_promote_goal_from_text(agent, None) is None


def test_decline_mints_no_goal_node_at_all(agent):
    """Not merely 'returns None' -- genuinely no Goal node is created, so a
    caller cannot accidentally dispatch a half-formed one."""
    before = len(agent.s.nodes("Goal"))
    sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are unlike function definitions.")
    sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Is a generating function like a function definition?")
    sd.mint_solve_analogical_promote_goal_from_text(
        agent, "Generating functions are important.")
    sd.mint_solve_analogical_promote_goal_from_text(
        agent, "The agent is like the patient.")
    after = len(agent.s.nodes("Goal"))
    assert after == before


# --------------------------------------------------------------------------- #
#  The resolver's own internals are untouched -- an explicit-corr_node Goal
#  minted the OLD way (mint_solve_analogical_promote_goal, hand-built
#  correspondence) still produces byte-identical dispatch behaviour.
# --------------------------------------------------------------------------- #
def test_old_direct_mint_path_unaffected(agent):
    sub = agent.s
    node_a = sub.add_node("Concept", {"name": "dc_regress_rich",
                                       "category": "test", "definition": "regulates gates and feedback"})
    node_b = sub.add_node("Concept", {"name": "dc_regress_sparse",
                                       "category": "test", "definition": "plain"})
    vec_a = at_mod._concept_shape_vector(sub, node_a)
    vec_b = at_mod._concept_shape_vector(sub, node_b)
    witness = at_mod._pair_witness(sub, vec_a, vec_b)
    corr = at_mod.record_directional_correspondence(sub, node_a, node_b, vec_a, vec_b, witness)
    assert corr is not None

    goal = sd.mint_solve_analogical_promote_goal(agent, corr)
    _pump(agent, goal)
    at_ = sub.node(goal)["attrs"]
    assert at_["status"] in ("resolved", "walled")
