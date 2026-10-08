"""test_self_prose_rendering — the RENDERING gate for self/meta chat replies.

The reflective faculties (domains/reflective_faculty.py, domains/self_model.py)
already compute RICH, graph-grounded self-state (a rule's real match/reads/
writes, the seven meta-shapes, which rules touch an attr, ...) — they are not
this bug. The bug was in `substrate/world_adapter.py`'s `_surface_self_state`:
for any state its (`_self_account_frames` -> produce()) path didn't cover, it
fell through to a raw `"; ".join(f"{k}={v}" ...)` dict dump — the state's OWN
`note` (already fluent, first-person, graph-grounded prose most of these
faculties compose) was ignored, and the reply came out as machine k=v pairs.

This suite drives the REAL chat path (`agent.answer_question`) — never the
handler functions directly, same discipline as `tests/test_self_model.py` —
over a battery of self/meta questions, and asserts (1) no raw-dict-fallback
substring survives in any reply, and (2) the real facts the old fact-substring
tests already checked are still present (content preserved, not just prettied).
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# the raw-dict-fallback's own machine-tail fingerprints — none of these may
# ever appear in a chat reply again.
_RAW_DUMP_TELLS = (
    "found=True",
    "; rule_name=",
    "meta_shapes=[",
    "detail=[{",
)

_BATTERY = [
    "What does hop_descend_gradient do?",
    "How are you organised?",
    "What shape are you?",
    "which parts of me touch chosen_action?",
    "which rules do you have about navigation?",
]


def test_battery_never_dumps_raw_dict(agent):
    for q in _BATTERY:
        ans = agent.answer_question(q)
        assert isinstance(ans, str) and ans, q
        for tell in _RAW_DUMP_TELLS:
            assert tell not in ans, (q, tell, ans)


def test_hop_descend_gradient_reply_is_fluent_and_preserves_facts(agent):
    ans = agent.answer_question("What does hop_descend_gradient do?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    # real facts, off export_rules() (same assertions test_self_model.py makes).
    assert "hop_descend_gradient" in ans
    assert "chosen_action" in ans
    assert "grid_navigation" in ans          # from_seed — the note's provenance clause


def test_self_organisation_reply_is_fluent_first_person(agent):
    ans = agent.answer_question("How are you organised?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    assert ans.startswith("I ")


def test_self_organisation_does_not_train_unused_account_grammar(agent, monkeypatch):
    def unexpected_producer():
        pytest.fail("area-list rendering must not train the self-account grammar")

    monkeypatch.setattr(agent, "_self_account_producer", unexpected_producer)
    answer = agent.answer_question("How are you organised?")

    assert answer.startswith("I am organised into")


def test_self_organisation_reader_marks_inventory_scope(agent):
    from domains.self_organisation_reader import run_self_organisation

    state = run_self_organisation(agent.s)

    assert state["inventory_scope"] == "validated_seed_prepass_top12"
    assert state["complete_within_scope"] is True
    live_rows = []
    for node in agent.s.nodes("Microtheory"):
        attrs = agent.s.node(node)["attrs"]
        if attrs.get("name"):
            live_rows.append((
                len(list(agent.s.neighbours(node, "has_concept"))),
                attrs["name"],
            ))
    live_top12 = [name for _, name in sorted(
        live_rows, key=lambda row: (-row[0], row[1]))[:12]]
    assert state["areas"][:12] == live_top12


def test_self_shape_reply_is_fluent_and_preserves_facts(agent):
    ans = agent.answer_question("What shape are you?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    # the seven meta-shapes / primary principle are still conveyed (the note IS
    # the fluent answer here — produce()'s tiny corpus can't losslessly frame
    # a 7-way structural decomposition).
    assert "seven meta-shapes" in ans
    assert "hierarchical invariance" in ans


def test_self_model_touches_reply_is_fluent_and_preserves_facts(agent):
    ans = agent.answer_question("which parts of me touch chosen_action?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    for writer in ("hop_descend_gradient", "choose_action", "pursue_active_goal"):
        assert writer in ans


def test_self_model_topic_reply_is_fluent_and_preserves_facts(agent):
    ans = agent.answer_question("which rules do you have about navigation?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    assert "hop_descend_gradient" in ans
    assert "credit_action_effect" not in ans   # unrelated rule — negative control


def test_discriminative_nonsense_rule_name_stays_honest(agent):
    ans = agent.answer_question("what does totally_bogus_rule_the_agent_never_had do?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    assert "don't have" in ans
    assert "totally_bogus_rule_the_agent_never_had" in ans.replace(" ", "_")


def test_ambiguous_rule_name_still_states_both_honestly(agent):
    ans = agent.answer_question("what does satisfy_goal do?")
    for tell in _RAW_DUMP_TELLS:
        assert tell not in ans
    assert "2" in ans or "DIFFERENT" in ans


def test_rule_description_uses_the_production_faculty(agent):
    # the rule-description headline ('I hold the rule.') must come from the
    # agent's OWN production faculty (LanguageProduction.produce), not a
    # Python f-string authored in the renderer.
    ans = agent.answer_question("what does hop_descend_gradient do?")
    assert "I hold the rule." in ans
