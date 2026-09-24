"""Cognitive rule frames stay private and never become world mechanics."""

from substrate.world_adapter import WorldAdapter
from domains.cognitive_rule_frames import (
    commit_prediction,
    draft_document,
    observe_situation,
    propose_document_write,
    read_rule_document,
    revise_document_draft,
)


def _adapter():
    return WorldAdapter(shadow_read=False, deep_ingest=False)


def test_rulebook_is_read_as_private_cognition_and_activates_on_observation():
    resident = _adapter()
    paper = resident.s.add_node("UploadedDocument", {
        "name": "rules", "kind": "rulebook"})

    held = read_rule_document(
        resident,
        paper,
        "On a turn, roll two dice. If you cannot pay, leave the table.",
        name="rulebook",
    )

    assert len(held["rules"]) == 2
    assert {
        resident.s.node(rule)["attrs"]["kind"] for rule in held["rules"]
    } >= {"procedure", "conditional"}
    assert all(
        resident.s.node(rule)["attrs"]["status"] == "held"
        for rule in held["rules"]
    )

    observed = observe_situation(resident, "roll two dice", kind="room")
    assert observed["activations"]
    assert observed["predictions"]
    assert all(
        resident.s.node(prediction)["type"] == "RulePrediction"
        for prediction in observed["predictions"]
    )
    # Reading and prediction do not silently create a Monopoly/game/world
    # state machine.  Any physical action must still be proposed separately.
    assert not list(resident.s.nodes("PhysicalAction"))
    assert not list(resident.s.nodes("WorldFact"))
    assert not list(resident.s.nodes("MonopolyState"))
    receipts = list(resident.s.nodes("NativeCognitiveRuleFrameReceipt"))
    assert len(receipts) == 2
    assert {resident.s.node(n)["attrs"]["cluster"] for n in receipts} == {
        "cognitive_rule_frames.document_settlement",
        "cognitive_rule_frames.observation_settlement",
    }


def test_different_residents_can_hold_different_interpretations():
    first, second = _adapter(), _adapter()
    paper_a = first.s.add_node("UploadedDocument", {})
    paper_b = second.s.add_node("UploadedDocument", {})
    held_a = read_rule_document(first, paper_a, "The council shall meet at noon.",
                                name="proclamation")
    held_b = read_rule_document(second, paper_b, "The council shall meet at noon.",
                                name="proclamation")

    rule_a, rule_b = held_a["rules"][0], held_b["rules"][0]
    first.inner.set_attr(rule_a, "confidence", 0.2)
    assert first.s.node(rule_a)["attrs"]["confidence"] == 0.2
    assert second.s.node(rule_b)["attrs"]["confidence"] != 0.2
    assert first.s.node(held_a["rule_document"])["attrs"]["provenance"] == (
        "resident_read_document"
    )


def test_commitment_and_writing_are_explicit_boundaries():
    resident = _adapter()
    paper = resident.s.add_node("UploadedDocument", {})
    held = read_rule_document(resident, paper, "If the bell rings, gather at the hall.",
                              name="charter")
    observed = observe_situation(resident, "the bell rings", kind="village")
    commitment = commit_prediction(resident, observed["predictions"][0],
                                   mode="goal")
    assert commitment["goal"] in resident.s.nodes("Goal")

    draft = draft_document(
        resident,
        "The council will meet at noon.",
        name="council notice",
        kind="proclamation",
        audience=["council", "villagers"],
    )
    revised = revise_document_draft(
        resident, draft["draft"], "The council will meet at one o'clock."
    )
    proposal = propose_document_write(
        resident, draft["draft"], destination="noticeboard"
    )

    assert revised["revision"] == 1
    assert proposal["kind"] == "proclamation"
    assert proposal["text"] == "The council will meet at one o'clock."
    assert proposal["destination"] == "noticeboard"
    # The cognition provider has only made a proposal.  A world/backend action
    # must accept it and place a physical document before anybody else can read.
    assert not list(resident.s.nodes("WrittenDocument"))
