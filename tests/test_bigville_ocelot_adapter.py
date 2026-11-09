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


def test_decide_returns_the_exact_duplicate_tuple_affordance_with_extra_fields():
    resident = BigvilleOcelotResident("ChoiceAda")
    resident.replace_options([
        {"action": "move_object", "kind": "box", "trade": "", "recipe": "",
         "target": "", "score": 1.0, "object_id": "box_a", "destination": "table"},
        {"action": "move_object", "kind": "box", "trade": "", "recipe": "",
         "target": "", "score": 5.0, "object_id": "box_b", "destination": "world"},
        {"action": "move_object", "kind": "box", "trade": "", "recipe": "",
         "target": "", "score": 2.0, "object_id": "box_c", "destination": "Ada"},
    ])

    choice = resident.decide()

    assert choice == {
        "action": "move_object", "kind": "box", "trade": "", "recipe": "",
        "target": "", "score": 5.0, "object_id": "box_b", "destination": "world",
    }


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "scenarios" /
                         "monopoly_four_players.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_real_village_object_affordance_discriminator_preserves_object_and_destination(monkeypatch):
    """Normal village object affordances can share every public tuple field."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))
    from bigville import create_world

    world = create_world(scenario="monopoly_four_players",
                         cognition_factory=BigvilleOcelotResident)
    mind = world.actor_mind("Alice")
    options = world.actor_affordances("Alice")
    move_options = [option for option in options
                    if option.get("action") == "move_object"
                    and option.get("object_id") == "game_box"]
    assert len(move_options) >= 2
    assert len({option.get("destination") for option in move_options}) >= 2
    expected = dict(move_options[-1])
    expected["score"] = 10.0
    options = [dict(option, score=10.0 if option is move_options[-1] else 0.0)
               for option in options]

    mind.replace_options(options)
    choice = mind.decide()

    assert choice == expected
    assert "option_id" not in choice


@pytest.mark.skipif(not (_BIGVILLE_ROOT / "bigville" / "seeds" /
                         "bigville_actor_decision.json").is_file(),
                    reason="standalone Bigville checkout is not present")
def test_observed_hunger_changes_graph_choice_for_eat_and_food_fetch(monkeypatch):
    """The same afforded choices yield different graph choices at high hunger."""
    monkeypatch.setenv("BIGVILLE_ROOT", str(_BIGVILLE_ROOT))
    carrying_bread = [
        {"action": "work", "kind": "", "recipe": "forge", "target": "", "score": 0.0},
        {"action": "eat", "kind": "bread", "target": "", "score": 0.0},
        {"action": "put", "kind": "bread", "target": "target:put", "score": 0.0},
        {"action": "fetch", "kind": "bread", "food": True,
         "target": "target:fetch", "score": 0.0},
        {"action": "rest", "kind": "", "target": "", "score": 0.0},
    ]

    def choose(name, hunger, options):
        resident = BigvilleOcelotResident(name)
        observed = resident.observe_situation(
            kind="village_observation", attributes={"hunger": hunger, "turn": 1})
        resident.replace_options(options)
        selected = resident.decide()
        attrs = resident.s.node(resident.agent)["attrs"]
        option_nodes = list(resident.inner.neighbours(resident.agent, "has_option"))
        offered = [resident.s.node(node)["attrs"] for node in option_nodes]
        observation = resident.s.node(observed["observation"])["attrs"]
        scores_before = [float(resident.s.node(node)["attrs"].get("score", 0.0))
                         for node in option_nodes]
        resident.inner.run_rules()
        scores_after = [float(resident.s.node(node)["attrs"].get("score", 0.0))
                        for node in option_nodes]
        assert scores_after == scores_before, "the same affordance must not be rescored cumulatively"
        return selected, attrs, offered, observation

    sated, sated_attrs, _, _ = choose("SatedChoice", 0.0, carrying_bread)
    hungry, hungry_attrs, hungry_options, observation = choose(
        "HungryChoice", 0.65, carrying_bread)

    assert sated["action"] == "work"
    assert hungry["action"] == "eat"
    assert hungry_attrs["observed_hunger"] == pytest.approx(0.65)
    assert json.loads(observation["attributes_json"])["hunger"] == pytest.approx(0.65)
    scores = {option["action"]: float(option.get("score", 0.0))
              for option in hungry_options}
    assert scores["eat"] > scores["work"]

    strong_work = [dict(option) for option in carrying_bread]
    strong_work[0]["score"] = 70.0
    high_priority_work, _, _, _ = choose("StrongWork", 0.65, strong_work)
    assert high_priority_work["action"] == "work", "appetite utility must preserve stronger authored scores"

    no_bread = [
        {"action": "work", "kind": "", "recipe": "forge", "target": "", "score": 0.0},
        {"action": "fetch", "kind": "bread", "food": True,
         "target": "target:bread", "score": 0.0},
        {"action": "rest", "kind": "", "target": "", "score": 0.0},
    ]
    sated_fetch, _, _, _ = choose("SatedFetch", 0.0, no_bread)
    hungry_fetch, _, fetched_options, _ = choose("HungryFetch", 0.65, no_bread)
    assert sated_fetch["action"] == "work"
    assert hungry_fetch["action"] == "fetch"
    fetch_score = next(float(option["score"]) for option in fetched_options
                       if option["action"] == "fetch")
    assert fetch_score > 0.0

    no_other_action = [option for option in no_bread if option["action"] == "fetch"]
    sated_idle, _, idle_options, _ = choose("SatedIdle", 0.0, no_other_action)
    assert sated_idle["action"] == "none"
    assert next(option for option in idle_options if option["action"] == "none")["score"] == -0.5


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
