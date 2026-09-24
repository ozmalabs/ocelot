"""Phase 6A: substantive legacy fact readback crosses the production gate."""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402


def _corpus():
    path = os.path.join(ROOT, "tests", "fixtures", "conversational_manifold",
                       "phase6_semantic_production.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_legacy_fact_readback_releases_only_after_parse_back_gate():
    wa = WorldAdapter(seeds=())
    for item in _corpus():
        concept = next(key for key in item["meaning"] if key != "force")
        sign = item.get("sign", {})
        if sign:
            wa.learn_sign(sign["form"], concept, sign.get("marker", ""))
        wa.learn_fact(item["meaning"])
        assert wa.answer_about(item["subject"]) == item["expected_surface"]

    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == len(_corpus())
    for receipt in receipts:
        attrs = wa.s.node(receipt)["attrs"]
        assert attrs["status"] == "released"
        assert attrs["parse_back_mode"] == "legacy_structural_readback"
        assert attrs["recoverable"] is True
        assert attrs["coverage"] == 1.0


def test_full_legacy_corpus_is_reachable_through_question_readback():
    """The production gate must cover the substantive legacy QA route, not
    only direct ``answer_about`` calls."""
    wa = WorldAdapter(seeds=())
    for item in _corpus():
        concept = next(key for key in item["meaning"] if key != "force")
        sign = item.get("sign", {})
        if sign:
            wa.learn_sign(sign["form"], concept, sign.get("marker", ""))
        wa.learn_fact(item["meaning"])

    for _ in range(2):
        for item in _corpus():
            assert wa.answer_question(f"what is {item['subject']}?") == item["expected_surface"]

    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 2 * len(_corpus())
    assert all(wa.s.node(node)["attrs"]["status"] == "released"
               for node in receipts)
    assert all("noted" not in (wa.s.node(node)["attrs"]["surface"] or "").lower()
               for node in receipts)


@pytest.mark.parametrize("question_template", [
    "what is {subject}?",
    "what's {subject}?",
    "what are {subject}?",
])
def test_all_legacy_faculty_question_forms_cross_the_same_release_gate(
        question_template):
    """Question routing is a legacy readback faculty, not a second renderer.

    Every surface form must re-enter ``answer_about`` and therefore leave the
    same semantic parse-back receipt.  This specifically covers the front-end
    variants which previously could return a cached answer without a release
    receipt.
    """
    wa = WorldAdapter(seeds=())
    for item in _corpus():
        sign = item.get("sign", {})
        if sign:
            concept = next(key for key in item["meaning"] if key != "force")
            wa.learn_sign(sign["form"], concept, sign.get("marker", ""))
        wa.learn_fact(item["meaning"])

    for item in _corpus():
        assert wa.answer_question(question_template.format(
            subject=item["subject"])) == item["expected_surface"]

    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == len(_corpus())
    assert all(wa.s.node(node)["attrs"]["status"] == "released"
               for node in receipts)
    assert all(wa.s.node(node)["attrs"]["parse_back_mode"]
               == "legacy_structural_readback" for node in receipts)
    assert all("noted" not in (wa.s.node(node)["attrs"]["surface"] or "").lower()
               for node in receipts)


def test_legacy_readback_parse_back_failure_is_explicit(monkeypatch):
    wa = WorldAdapter(seeds=())
    wa.learn_fact({"is_a": {"left": "graph", "right": "structure"}})

    from domains import production_gate
    monkeypatch.setattr(
        production_gate,
        "legacy_readback_gate",
        lambda frame, surface: {
            "recoverable": False, "coverage": 0.0,
            "missing": ["structure"], "recovered": ["graph"],
            "intended": ["is_a", "graph", "structure"],
            "mode": "legacy_structural_readback",
        },
    )

    assert wa.answer_about("graph") is None
    receipt = list(wa.s.nodes("ProductionGateReceipt"))[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "withheld"
    assert "parse_back_not_recoverable" in attrs["withhold_reasons"]
    assert "noted" not in (attrs["surface"] or "").lower()


def test_question_readback_failure_cannot_become_a_released_or_noted_surface(
        monkeypatch):
    """The legacy QA route must not bypass the gate on parse-back failure."""
    wa = WorldAdapter(seeds=())
    wa.learn_fact({"is_a": {"left": "graph", "right": "structure"}})

    from domains import production_gate
    monkeypatch.setattr(
        production_gate,
        "legacy_readback_gate",
        lambda frame, surface: {
            "recoverable": False, "coverage": 0.0,
            "missing": ["structure"], "recovered": ["graph"],
            "intended": ["is_a", "graph", "structure"],
            "mode": "legacy_structural_readback",
        },
    )

    assert wa.answer_question("what is graph?") is None
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["recoverable"] is False
    assert attrs["coverage"] == 0.0
    assert "parse_back_not_recoverable" in attrs["withhold_reasons"]
    assert "noted" not in (attrs["surface"] or "").lower()


def test_audited_legacy_surface_routes_share_the_release_gate():
    """Audit the actual substantive legacy routes, not only the helper.

    ``answer_about`` is the direct reader, ``answer_question`` is its question
    front end, and ``converse`` is the live question route.  Each must leave a
    released receipt for the same graph-held fact.  Numeric/predicate readers
    are intentionally absent: they return non-surface values and therefore do
    not belong to a semantic utterance release corpus.
    """
    item = _corpus()[0]
    routes = ("answer_about", "answer_question", "converse")
    for route in routes:
        wa = WorldAdapter(seeds=())
        wa.learn_fact(item["meaning"])
        if route == "answer_about":
            reply = wa.answer_about(item["subject"])
        elif route == "answer_question":
            reply = wa.answer_question(f"what is {item['subject']}?")
        else:
            reply = wa.converse(f"what is {item['subject']}?", "question")
        assert reply == item["expected_surface"], route
        receipts = list(wa.s.nodes("ProductionGateReceipt"))
        assert receipts, route
        attrs = wa.s.node(receipts[-1])["attrs"]
        assert attrs["status"] == "released", route
        expected_mode = (
            "conversation_information_graph"
            if route == "converse" else "legacy_structural_readback"
        )
        assert attrs["parse_back_mode"] == expected_mode, route
        assert "noted" not in attrs["surface"].lower(), route


def test_taught_fact_readback_is_not_a_cached_gate_bypass():
    """The taught-capability fallback is a substantive legacy readback path."""
    wa = WorldAdapter(seeds=())
    wa.learn_from_teacher(
        "what is volcanoes",
        {"answer": "a volcano is a rupture in a planet's crust",
         "learn": [{"phrase": "volcanoes",
                    "answer": "a volcano is a rupture in a planet's crust"}]},
    )

    assert wa.answer_about("volcanoes") == \
        "a volcano is a rupture in a planet's crust"
    receipts = list(wa.s.nodes("ProductionGateReceipt"))
    assert len(receipts) == 1
    attrs = wa.s.node(receipts[0])["attrs"]
    assert attrs["status"] == "released"
    assert attrs["parse_back_mode"] == "legacy_structural_readback"
    assert attrs["semantic_event"] == "inform"
    assert attrs["recoverable"] is True
    assert list(wa.inner.neighbours(receipts[0], "releases"))


def test_taught_readback_failure_is_withheld_and_converse_exposes_error(
        monkeypatch):
    wa = WorldAdapter(seeds=())
    wa.learn_from_teacher(
        "what is volcanoes",
        {"answer": "noted",
         "learn": [{"phrase": "volcanoes", "answer": "noted"}]},
    )
    from domains import production_gate
    monkeypatch.setattr(
        production_gate,
        "legacy_readback_gate",
        lambda frame, surface, **kwargs: {
            "recoverable": False, "coverage": 0.0,
            "missing": ["volcanoes"], "recovered": [],
            "intended": ["inform", "agent", "volcanoes"],
            "mode": "legacy_structural_readback",
        },
    )

    assert wa.answer_about("volcanoes") is None
    receipt = list(wa.s.nodes("ProductionGateReceipt"))[0]
    attrs = wa.s.node(receipt)["attrs"]
    assert attrs["status"] == "withheld"
    assert attrs["recoverable"] is False
    assert not list(wa.inner.neighbours(receipt, "releases"))
    assert wa.converse("what is volcanoes?", "question") == \
        "ERROR: no communicative response could be generated."
