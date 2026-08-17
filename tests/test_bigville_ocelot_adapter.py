import json
from pathlib import Path

import pytest

from worlds.bigville_ocelot_adapter import BigvilleOcelotResident


_BIGVILLE_ROOT = Path(__file__).resolve().parents[2] / "bigville"


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_bigville_document_read_enters_real_ocelot_graph(monkeypatch):
    pytest.importorskip("nltk")
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))
    resident = BigvilleOcelotResident("Bob")
    text = (
        "Each player begins with 1500 dollars. On a turn, roll two dice and "
        "move that many spaces. A player who cannot pay is bankrupt."
    )

    first = resident.ingest_document(text, name="Monopoly rulebook")
    second = resident.ingest_document(text, name="Monopoly rulebook")

    assert first["status"] == "understood"
    assert second == first
    assert len(first["sentence_parses"]) >= 1
    assert len(first["held_answers"]) >= 1
    assert len(list(resident.s.nodes("Understanding"))) == 1
    assert not list(resident.s.nodes("ComprehensionResidual"))


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_bigville_goal_speech_uses_ocelot_full_text_production(monkeypatch):
    """Bigville's meaning stays raw data; Ocelot owns the surface sentence."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))
    resident = BigvilleOcelotResident("Alice")

    greeting = resident.goal_utterance("Bob", {"greeting": {"of": "Bob"}})
    weather = resident.goal_utterance("Bob", {"weather": {"of": "clear"}})
    warning = resident.goal_utterance("Bob", {"warning": {"of": "Bob"}})

    assert greeting == "I greet Bob."
    assert weather == "The weather is clear."
    assert warning == "I warn Bob."

    assert all(" of " not in text for text in (greeting, weather, warning))
    assert hasattr(resident.wa, "full_text_for")
    assert not hasattr(resident, "_full_text_voice")

    goal = list(resident.s.nodes("CommunicativeGoal"))[-1]
    attrs = resident.s.node(goal)["attrs"]
    assert json.loads(attrs["meaning_json"]) == {"warning": {"of": "Bob"}}
    assert json.loads(attrs["render_meaning_json"])["event"] == "warn"


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_character_payload_seeds_emotional_core_and_spontaneous_speech(monkeypatch):
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))
    resident = BigvilleOcelotResident("Alice")
    resident.seed_character(
        identity={"occupation": "teacher"},
        personality={
            "emotional_core_enabled": 1.0,
            "talkativeness": 0.9,
            "self_efficacy_prior": 0.7,
            "social_dispositions": {
                "Bob": {"regard": 0.7, "trust": 0.6, "admiration": 0.8}
            },
            "emotion": {"appraisal": {"valued_goal": 1.0}},
        },
        memories=[{"memory_id": "m1", "content": "A held memory."}],
        held_frames=["core_emotions", "theory_of_mind"],
    )

    payload = resident.dump_held_state()
    assert payload["identity"]["occupation"] == "teacher"
    assert payload["memories"][0]["memory_id"] == "m1"
    assert any(node["type"] == "FrameSeed" for node in payload["held_frames"])
    assert payload["backend_state"]["emotional_state"]["enabled"] is True
    assert list(resident.s.nodes("TargetPattern"))

    choice = resident.decide_speech("Bob")
    assert choice["code"] >= 0
    assert choice["kind"] in {"stay_silent", "greeting", "smalltalk", "barb",
                               "hedged", "share", "answer", "request", "offer",
                               "question", "thanks", "apology", "farewell",
                               "complaint", "promise"}
    if choice["spoken"]:
        # Real free text, not a bare menu label -- routed through
        # goal_utterance's full-text pipeline (BIGVILLE_SOCIAL_EXPERIMENT_1
        # rung 2 fix).
        assert isinstance(choice.get("text"), str) and choice["text"]
        assert choice.get("act")


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_decide_speech_diverges_by_disposition_not_always_smalltalk(monkeypatch):
    """Regression guard for the diagnosed defect (BIGVILLE_SOCIAL_EXPERIMENT_1_
    RESULTS.md): SpeechOption's relational-affect coefficients used to be all
    zero, so decide_speech always picked 'smalltalk' regardless of disposition.
    Two residents with OPPOSITE seeded dispositions toward the SAME target,
    at zero baseline arousal (isolating the disposition channel from the
    separate arousal*hostile_aff channel), must choose DIFFERENT acts."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))

    resentful = BigvilleOcelotResident("Resentful")
    resentful.seed_character(personality={
        "emotional_core_enabled": 1.0,
        "social_dispositions": {"Target": {"resentment_debt": 1.0, "regard": -0.8}},
    })
    grateful = BigvilleOcelotResident("Grateful")
    grateful.seed_character(personality={
        "emotional_core_enabled": 1.0,
        "social_dispositions": {"Target": {"gratitude_debt": 1.0, "regard": 0.8}},
    })

    resentful_choice = resentful.decide_speech("Target", arousal=0.0)
    grateful_choice = grateful.decide_speech("Target", arousal=0.0)

    assert resentful_choice["spoken"] and grateful_choice["spoken"]
    assert resentful_choice["kind"] != grateful_choice["kind"]
    assert resentful_choice["text"] != grateful_choice["text"]


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_shared_bucket_count_gives_familiarity_warmth_not_stranger_zero(monkeypatch):
    """A target with NO relationship history and NO seeded backstory, but
    sharing real buckets (role/class/group, bigville/game.py's own
    shared_bucket_count), gets mild warmth instead of a hard-zero stranger
    Bond. A target sharing NOTHING still gets zero -- the genuinely-
    unclassified-stranger case from BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md
    stays correct."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))

    familiar = BigvilleOcelotResident("Familiar")
    familiar.seed_character(personality={"emotional_core_enabled": 1.0})
    stranger = BigvilleOcelotResident("Stranger")
    stranger.seed_character(personality={"emotional_core_enabled": 1.0})

    bond_familiar = familiar._speech_bond("Target", shared_bucket_count=3)
    bond_stranger = stranger._speech_bond("Target", shared_bucket_count=0)

    assert familiar.s.node(bond_familiar)["attrs"]["affect_affection"] > 0.0
    assert stranger.s.node(bond_stranger)["attrs"]["affect_affection"] == 0.0


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_shared_bucket_familiarity_never_beats_a_real_seeded_disposition(monkeypatch):
    """Mere-exposure warmth is a weak prior, not a strong bond: when a real
    seeded social_dispositions entry exists, it wins outright -- bucket
    familiarity never blends in or dilutes it."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))

    resident = BigvilleOcelotResident("Grateful2")
    resident.seed_character(personality={
        "emotional_core_enabled": 1.0,
        "social_dispositions": {"Target": {"regard": 2.0, "admiration": 2.0}},
    })
    bond = resident._speech_bond("Target", shared_bucket_count=3)
    assert resident.s.node(bond)["attrs"]["affect_affection"] == pytest.approx(2.0)
