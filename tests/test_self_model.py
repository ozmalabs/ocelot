"""test_self_model — the jabberwock's FULL SELF-MODEL MIRROR (domains/self_model.py):
every rule it holds (not just the chosen_action-writing subset
`reflective_faculty._ensure_acting_rule_provenance` mirrors) as a queryable
`RuleSummary`, plus the self-query handlers ('what does <rule> do?', 'which
rules ... about <topic>?', 'which parts of me touch <attr>?') wired at the
same seam `self_organisation`/`self_shape` already answer through
(`WorldAdapter.answer_question` -> `comprehend_question.comprehend` ->
`reflective_faculty.reflect`, `mt in _rf._DISPATCH`).

Every assertion below drives the REAL chat path (`agent.answer_question`),
never the handler functions directly — the same discipline
`scripts/jabberwock_knows_itself.py`'s gate uses.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import self_model as sm


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_dispatch_registered(agent):
    from domains import reflective_faculty as rf
    assert "self_model_rule" in rf._DISPATCH
    assert "self_model_topic" in rf._DISPATCH
    assert "self_model_touches" in rf._DISPATCH


def test_mirror_covers_every_exported_rule(agent):
    n_export = len(agent.inner.export_rules())
    n_summary = len(list(agent.s.nodes("RuleSummary")))
    assert n_summary >= n_export, (n_summary, n_export)


def test_mirror_is_idempotent(agent):
    before = len(list(agent.s.nodes("RuleSummary")))
    rep1 = sm.ensure_rule_provenance(agent)
    rep2 = sm.ensure_rule_provenance(agent)
    after = len(list(agent.s.nodes("RuleSummary")))
    assert after == before                      # no duplicate minting
    assert rep1["minted"] == 0 and rep1["updated"] == 0
    assert rep2["minted"] == 0 and rep2["updated"] == 0


def test_unchanged_mirror_refresh_skips_structural_rule_walks(agent, monkeypatch):
    # A matching exported-body hash proves that every derived structural field
    # is unchanged. Refresh must use that proof before traversing large Where
    # trees or serializing summary strings.
    def unexpected_walk(*_args, **_kwargs):
        raise AssertionError("unchanged rule body was structurally re-walked")

    monkeypatch.setattr(sm, "_match_text", unexpected_walk)
    monkeypatch.setattr(sm, "_reads_text", unexpected_walk)
    monkeypatch.setattr(sm, "_effects_summary", unexpected_walk)
    monkeypatch.setattr(sm, "_find_threshold_lits", unexpected_walk)
    result = sm.ensure_rule_provenance(agent)
    assert result["minted"] == 0
    assert result["updated"] == 0
    assert result["unchanged"] > 0


def test_program_mirror_covers_every_program(agent):
    n_programs = len(list(agent.s.nodes("Program")))
    n_summary = len(list(agent.s.nodes("ProgramSummary")))
    assert n_summary >= n_programs


def test_ask_what_does_rule_do(agent):
    ans = agent.answer_question("what does hop_descend_gradient do?")
    assert isinstance(ans, str)
    assert "hop_descend_gradient" in ans
    assert "chosen_action" in ans      # the real write fact, off export_rules()


def test_ask_which_rules_about_topic(agent):
    ans = agent.answer_question("which rules do you have about navigation?")
    assert "hop_descend_gradient" in ans
    # an unrelated rule (no 'navigation' anywhere in its name/seed/reads/writes)
    # must not show up — a cheap negative control.
    assert "credit_action_effect" not in ans


def test_ask_which_parts_touch_attr(agent):
    ans = agent.answer_question("which parts of me touch chosen_action?")
    for writer in ("hop_descend_gradient", "choose_action", "pursue_active_goal"):
        assert writer in ans


def test_self_authored_rule_becomes_answerable_after_remirror(agent):
    # A turn-local query snapshot must not hide rules added by the graph and
    # mirrored into RuleSummary by the supported refresh path.
    agent._rule_summary_lookup_index = sm._build_rule_summary_exact_index(agent.s)
    agent.inner.add_rule({
        "name": "test_self_model_authored_rule",
        "match": [["m", "has_concept", "c"]],
        "where": None,
        "effects": [["set_attr", "c", "test_self_model_authored_attr", 1.0]],
        "batch": False,
        "match_type": None,
    })
    # before re-mirroring, the query is honest about not (yet) knowing it —
    # ensure_rule_provenance is the caller's job to invoke after add_rule.
    sm.ensure_self_model(agent)
    assert agent._rule_summary_lookup_index is None
    ans = agent.answer_question("what does test_self_model_authored_rule do?")
    assert "test_self_model_authored_attr" in ans


def test_discriminative_nonsense_rule_name(agent):
    ans = agent.answer_question("what does totally_bogus_rule_the_agent_never_had do?")
    assert "don't have" in ans
    assert "totally_bogus_rule_the_agent_never_had" in ans.replace(" ", "_")


def test_ambiguous_rule_name_states_both_honestly(agent):
    # a genuine property of the rule store: a few rule NAMES collide (two
    # distinct match/effects bodies share one name) — the self-model must not
    # silently pick one, it must say so.
    ans = agent.answer_question("what does satisfy_goal do?")
    assert "2" in ans or "DIFFERENT" in ans


def test_rule_summary_reads_writes_text_mechanical(agent):
    hits = sm._find_rule_summaries(agent.s, "hop_descend_gradient")
    assert len(hits) == 1
    _, at = hits[0]
    assert "chosen_action" in at["writes_text"]
    assert at["from_seed"] == "grid_navigation"


def test_batched_exact_rule_lookup_matches_individual_queries(agent):
    queries = ["hop_descend_gradient", "satisfy_goal", "hop descend gradient",
               "totally_bogus_rule"]
    batched = sm._find_rule_summaries_many(agent.s, queries)
    assert set(batched) == set(queries)
    for query in queries:
        assert batched[query] == sm._find_rule_summaries(agent.s, query)


def test_cached_exact_rule_lookup_matches_uncached_index(agent):
    queries = ["hop_descend_gradient", "satisfy_goal", "hop descend gradient",
               "totally_bogus_rule"]
    index = sm._build_rule_summary_exact_index(agent.s)
    assert all(not isinstance(node, dict)
               for rows in (*index["name"].values(),
                            *index["keywords"].values())
               for node in rows)
    indexed = sm._find_rule_summaries_many_indexed(
        agent.s, queries, index=index)
    assert indexed == sm._find_rule_summaries_many(agent.s, queries)


def test_existing_self_organisation_question_unaffected(agent):
    # the self_model additions must not regress the pre-existing meta seam.
    ans = agent.answer_question("how are you organised?")
    assert isinstance(ans, str) and ans
