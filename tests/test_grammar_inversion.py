"""Phase-6/7 grammar inversion gate.

The gate exercises the existing grammar-owned producer/comprehender pair and
the existing self-target monitor.  It does not infer meaning from surface
word order outside the held grammar and does not add a second parser.
"""
from __future__ import annotations

from domains import language as lang
from domains.self_target_monitor import score_self_target


_LEX = [
    {"form": "determinant", "concept": "det",
     "args": [{"role": "of", "marker": "of", "dir": "R"}]},
    {"form": "trace", "concept": "trace",
     "args": [{"role": "of", "marker": "of", "dir": "R"}]},
    {"form": "product", "concept": "product", "args": [
        {"role": "a", "marker": "of", "dir": "R"},
        {"role": "b", "marker": "and", "dir": "R"}]},
    {"form": "plus", "concept": "plus",
     "args": [{"role": "left", "dir": "L"},
              {"role": "right", "dir": "R"}]},
    {"form": "A", "concept": "A"}, {"form": "B", "concept": "B"},
    {"form": "M", "concept": "M"},
    {"form": "of", "mark": True}, {"form": "and", "mark": True},
    {"form": "the", "drop": True}, {"form": "is", "drop": True},
    {"form": "what", "drop": True},
]


def test_grammar_production_parse_back_is_fully_recoverable():
    meanings = [
        {"force": "tell", "det": {"of": "M"}},
        {"force": "tell", "plus": {"left": "A", "right": "B"}},
        {"force": "tell", "trace": {"of": {
            "product": {"a": "A", "b": "B"}}}},
        {"force": "ask", "det": {"of": "M"}},
    ]
    for meaning in meanings:
        surface = lang.produce(meaning, _LEX)
        assert lang.comprehend(surface, _LEX)[0] == meaning


def test_self_target_monitor_reports_complete_semantic_recovery():
    # This uses the existing recognizer mode of the self-target monitor: the
    # producer's own output is read back, and every intended concept must be
    # present before it can be considered recoverable.
    result = score_self_target(
        object(), "trace of the product of A and B",
        ["trace", "product", "A", "B"],
    )
    assert result["recoverable"] is True
    assert result["coverage"] == 1.0
    assert result["missing"] == []

