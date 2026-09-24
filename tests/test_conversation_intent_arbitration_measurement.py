from __future__ import annotations

from evaluation.conversation_intent_arbitration import load_fixture, measure


def test_frozen_intent_corpus_is_measured_without_promoting_a_winner():
    measurement = measure(load_fixture())

    assert measurement["rows"] == 160
    assert measurement["kind_agree"] == 150
    assert measurement["kind_disagree"] == 10
    assert measurement["kind_agreement_rate"] < 0.95
    assert measurement["disagreement_classes"] == {
        "question_promoted_from_instruction": 3,
        "question_promoted_from_statement": 5,
        "instruction_promoted_from_statement": 2,
    }
