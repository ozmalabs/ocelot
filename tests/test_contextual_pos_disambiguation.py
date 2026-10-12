"""Context resolves adjective/verb homographs without choosing semantics."""

from domains import construction_grammar as cg
from domains import wiktionary_reference as wikt
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_subject_context_selects_verb_reading_of_participial_homograph(monkeypatch):
    pos = {
        "i": ["pronoun"],
        "learned": ["adj", "verb", "name"],
        "that": ["pronoun"],
        "the": ["det"],
        "skill": ["noun"],
    }
    monkeypatch.setattr(wikt, "wiktionary_pos",
                        lambda surface, lang="en": pos.get(surface.lower(), []))

    clause = cg.parse_with_gaps("I learned that skill.")
    assert [(e["surface"], e["pos"]) for e in clause["elements"]] == [
        ("I", "pronoun"), ("learned", "verb"),
        ("that", "determiner"), ("skill.", "noun"),
    ]


def test_same_homograph_stays_adjectival_inside_a_noun_phrase(monkeypatch):
    pos = {
        "the": ["det"],
        "learned": ["adj", "verb", "name"],
        "skill": ["noun"],
    }
    monkeypatch.setattr(wikt, "wiktionary_pos",
                        lambda surface, lang="en": pos.get(surface.lower(), []))

    clause = cg.parse_with_gaps("the learned skill")
    assert [(e["surface"], e["pos"]) for e in clause["elements"]] == [
        ("the", "determiner"), ("learned", "adj"), ("skill", "noun"),
    ]


def test_modal_metadata_does_not_override_determiner_noun_context(monkeypatch):
    pos = {
        "pursue": ["verb"], "the": ["det"],
        "flurble": [], "gap": ["verb", "noun"],
    }
    monkeypatch.setattr(wikt, "wiktionary_pos",
                        lambda surface, lang="en": pos.get(
                            surface.lower().strip(".,;:?!"), []))
    # `gap` is graph-tagged as a deficiency cue, so modal metadata can inform
    # a clause-level reading. It must not erase syntax that puts the homograph
    # inside a determiner-headed noun phrase.
    monkeypatch.setattr(cg, "_typed_modal_word",
                        lambda substrate, low: low == "gap")

    frame = cg.parse_with_gaps("Pursue the flurble gap.", substrate=object())
    final = frame["elements"][-1]
    assert final == {"surface": "gap.", "role": "content", "pos": "noun"}
    relation = cg.compose_relation(frame)
    assert relation["object"]["surface"] == "gap."


def test_negated_copular_polar_query_keeps_adjective_as_property_predicate(
        monkeypatch):
    pos = {
        "the": ["det"], "gate": ["noun"], "not": ["adv"],
        "open": ["adj"],
    }
    monkeypatch.setattr(
        wikt, "wiktionary_pos",
        lambda surface, lang="en": pos.get(
            surface.lower().strip(".,;:?!"), []))

    relation = cg.compose_relation(
        cg.parse_with_gaps("Is the gate not open?"))

    assert relation["focus"] == "polar"
    assert relation["predicate"]["surface"].lower() == "open"
    assert relation["predicate"]["pos"] == "adj"
    assert relation["subject"]["surface"].lower() == "gate"


def test_complementizer_preserves_matrix_and_embedded_relations(monkeypatch):
    pos = {
        "i": ["pronoun"],
        "learned": ["adj", "verb", "name"],
        "that": ["pronoun"],
        "the": ["det"],
        "gate": ["noun"],
        "needs": ["adv", "noun", "verb", "name"],
        "power": ["noun", "verb", "adj", "intj", "name"],
    }
    monkeypatch.setattr(wikt, "wiktionary_pos",
                        lambda surface, lang="en": pos.get(surface.lower().strip(".,;:?!"), []))

    frame = cg.parse_with_gaps("I learned that the gate needs power.")
    relation = cg.compose_relation(frame)
    assert relation["predicate"]["surface"] == "learned"
    assert len(relation["embedded_relations"]) == 1
    embedded = relation["embedded_relations"][0]
    assert embedded["predicate"]["surface"] == "needs"
    assert embedded["subject"]["surface"] == "gate"
    assert embedded["object"]["surface"] == "power."


def test_embedded_relation_is_preserved_as_unverified_graph_evidence():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "I learned that the gate needs power.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    embedded_nodes = agent.inner.neighbours(
        interpretation, "has_embedded_relation")
    assert len(embedded_nodes) == 1
    attrs = agent.s.node(embedded_nodes[0])["attrs"]
    assert attrs["relation_kind"] == "embedded_proposition"
    assert attrs["status"] == "selected_parse_unverified"
    assert attrs["parsed_predicate"] == "needs"
    assert attrs["parsed_subject"] == "gate"
    assert attrs["parsed_object"].rstrip(".") == "power"
    assert agent.inner.neighbours(
        embedded_nodes[0], "relation_subject_concept")
    assert agent.inner.neighbours(
        embedded_nodes[0], "relation_predicate_concept")
    assert agent.s.nodes("InformationLearningRequest") == []


def test_auxiliary_question_keeps_determiner_object_np_out_of_predicate_slot():
    from domains.comprehend_text import comprehend_text

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    parsed = comprehend_text(agent, "Should we use the north route?",
                             kind="question")
    assert parsed.relation["predicate"]["surface"].lower() == "use"
    assert parsed.relation["subject"]["surface"].lower() == "we"
    assert parsed.relation["object"]["surface"].lower() == "route"
    assert parsed.dispatch["concept"].lower() == "route"
    assert parsed.intent == "ask_world:route"
