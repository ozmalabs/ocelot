"""Gate for MANIFOLD-RELATIVE CONTENT SHAPING (domains/audience_adaptation.py + the world_adapter
self-organisation wiring). DISCRIMINATIVE, donkey=0.

The failure this fixes: asked "how are you organised?", the jabberwock listed video_coding_theory /
cloud_infrastructure / machine_learning FLATLY to Cornelius Vane, a Victorian of 1885 — it answered
from its FIXED self-model regardless of who asked. Here the reply is rendered RELATIVE to the
interlocutor's manifold: modern-technical domains foreign to a period/non-technical manifold are
abstracted/flagged, not dumped; the SAME question to a technical manifold keeps the full content; and
with no observed interlocutor the answer is byte-identical (no regression).
"""
import pytest

from domains import audience_adaptation as aa

# Twelve real self-organisation areas (the first-12 the render surfaces), mixing modern-technical
# domains with period-compatible / universal ones.
AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]

VANE = {"id": "Cornelius Vane", "observed": True,
        "known_concepts": ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]}
TECHNICAL = {"id": "dev", "observed": True,
             "known_concepts": ["python", "rust", "algorithm", "compiler", "server", "database"]}
DEFAULT = {"id": "user", "observed": False, "known_concepts": []}


@pytest.fixture(scope="module")
def agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# --------------------------------------------------------------------------- #
#  1. MANIFOLD-RELATIVE CONTENT (headline): same concepts, manifold-adapted vs full.
# --------------------------------------------------------------------------- #

def test_headline_period_manifold_adapts_modern_tech(agent):
    """A period/non-technical (Victorian-typed formal) manifold ADAPTS: modern-tech domains are
    abstracted, NOT listed flat."""
    r = aa.adapt_concepts(agent, AREAS, VANE)
    assert r["manifold_type"] == "formal"
    assert r["adapted_flag"] is True
    # the exact modern-tech domains Vane saw flatly are now foreign (abstracted away).
    for foreign in ("video_coding_theory", "cloud_infrastructure", "machine_learning"):
        assert foreign in r["foreign"]
        assert foreign not in r["adapted"]
    # period-compatible / universal domains still land.
    for live in ("mathematics", "philosophy", "communication", "engineering"):
        assert live in r["adapted"]
    # the foreign group is abstracted to ONE umbrella (not dumped, not per-concept).
    assert r["abstraction"] in r["adapted"]
    assert r["adapted"][-1] == r["abstraction"]


def test_headline_technical_manifold_keeps_full_content(agent):
    """The SAME concepts to a technical manifold keep the FULL technical content — the modern world
    is live for it, nothing is foreign."""
    r = aa.adapt_concepts(agent, AREAS, TECHNICAL)
    assert r["manifold_type"] == "technical"
    assert r["adapted_flag"] is False
    assert r["foreign"] == []
    assert r["adapted"] == AREAS   # byte-identical, full content


def test_headline_contrast_verbatim(agent):
    """Pin the CONTRAST verbatim: the same question, manifold-adapted delivery vs full."""
    vane = " ".join(aa.adapt_concepts(agent, AREAS, VANE)["adapted"])
    tech = " ".join(aa.adapt_concepts(agent, AREAS, TECHNICAL)["adapted"])
    assert vane == ("engineering communication mathematics art_design_drawing philosophy "
                    "certain modern arts unfamiliar in your world")
    assert tech == " ".join(AREAS)
    assert vane != tech


# --------------------------------------------------------------------------- #
#  2. CONCEPT-LIVENESS: a concept not in the manifold is detected + handled.
# --------------------------------------------------------------------------- #

def test_concept_liveness_split(agent):
    """Concept-liveness split: modern-technical concepts are the residual (foreign), universal ones
    are live — the split is shown, not a flat dump."""
    split = aa.split_by_manifold(agent, AREAS, VANE)
    assert split["fired"] is True
    assert set(split["foreign"]) & {"video_coding_theory", "machine_learning"}
    assert "philosophy" in split["live"] and "mathematics" in split["live"]
    # every concept is accounted for exactly once.
    assert sorted(split["live"] + split["foreign"]) == sorted(AREAS)


def test_modern_tech_classifier_discriminates():
    """The modern-tech marker discriminates modern computing domains from timeless ones (no boot)."""
    for modern in ("machine_learning", "cloud_infrastructure", "video_coding_theory",
                   "computer_architecture", "network_protocols", "compilers"):
        assert aa.concept_is_modern_tech(modern), modern
    for universal in ("philosophy", "mathematics", "communication", "engineering",
                      "medicine_general", "agriculture", "astronomy_foundation", "gastronomy"):
        assert not aa.concept_is_modern_tech(universal), universal


def test_grounded_concept_rescued_live(agent):
    """MANIFOLD-CONDITIONED, not a hardcoded 'if Victorian': a modern-tech concept the manifold
    ACTUALLY holds (in known_concepts, grounded common ground) is rescued LIVE even in a period
    manifold — the residual is against the manifold, not a fixed foreign list."""
    vane_knows_ml = dict(VANE)
    vane_knows_ml["known_concepts"] = VANE["known_concepts"] + ["machine_learning"]
    split = aa.split_by_manifold(agent, AREAS, vane_knows_ml)
    assert "machine_learning" in split["grounded_known"]
    assert "machine_learning" in split["live"]
    assert "machine_learning" not in split["foreign"]


# --------------------------------------------------------------------------- #
#  3. INTERLOCUTOR VISIBLY RESHAPES THE REPLY (through the live answer path).
# --------------------------------------------------------------------------- #

def _org_reply(agent, interlocutor):
    # install the interlocutor as the active/observed party, then ask via the real answer path.
    for n in list(agent.s.nodes("Interlocutor")):
        agent.inner.set_attr(n, "active", False)
    agent.s.add_node("Interlocutor", {"name": interlocutor["id"], "active": True,
                                      "observed": interlocutor["observed"],
                                      "known_concepts": list(interlocutor["known_concepts"])})
    return agent.answer_question("How are you organised?")


def test_interlocutor_reshapes_reply(agent):
    """The delivered self-organisation reply DIFFERS by interlocutor manifold — the model now
    visibly changes what Vane sees."""
    vane_reply = _org_reply(agent, VANE)
    tech_reply = _org_reply(agent, TECHNICAL)
    assert vane_reply != tech_reply
    assert "machine_learning" not in vane_reply and "video_coding_theory" not in vane_reply
    assert "unfamiliar in your world" in vane_reply
    assert "machine_learning" in tech_reply and "video_coding_theory" in tech_reply


# --------------------------------------------------------------------------- #
#  4. NO REGRESSION: unobserved / default manifold -> byte-identical.
# --------------------------------------------------------------------------- #

def test_no_regression_default_unchanged(agent):
    """No observed interlocutor -> adaptation does NOT fire -> the concept list is byte-identical."""
    r = aa.adapt_concepts(agent, AREAS, DEFAULT)
    assert r["adapted_flag"] is False
    assert r["fired"] is False
    assert r["adapted"] == AREAS


def test_no_regression_undertyped_manifold_hedges(agent):
    """An OBSERVED but under-typed manifold (one weak cue, not committed) HEDGES — adapts nothing."""
    weak = {"id": "x", "observed": True, "known_concepts": ["virtue"]}  # one formal cue -> not committed
    r = aa.adapt_concepts(agent, AREAS, weak)
    assert r["adapted_flag"] is False
    assert r["adapted"] == AREAS


def test_no_regression_live_default_answer_byte_identical(agent):
    """The live answer path with no observed interlocutor renders the full flat list (the prior
    behaviour) — adaptation only fires on an observed non-matching manifold."""
    for n in list(agent.s.nodes("Interlocutor")):
        agent.inner.set_attr(n, "active", False)
    reply = agent.answer_question("How are you organised?")
    assert "machine_learning" in reply and "video_coding_theory" in reply
    assert "unfamiliar in your world" not in reply


# --------------------------------------------------------------------------- #
#  REGISTER -> MANIFOLD TYPE (the live Vane fix): a formal register on the
#  interlocutor snapshot types `formal`/committed even when the content-concepts
#  (Vane's real greeting words) miss the formal CONTENT cue table. Casual /
#  neutral snapshots stay general -> adaptation does NOT fire (discriminant).
# --------------------------------------------------------------------------- #

# Vane's REAL live concepts (none hit the formal CONTENT cues) + a formal register.
VANE_LIVE_FORMAL = {"id": "Cornelius Vane", "observed": True,
                    "known_concepts": ["cornelius", "humble", "scholar", "natural", "philosophy"],
                    "register": "formal", "formal_cues": 1.0, "casual_cues": 0.0}
VANE_LIVE_CASUAL = {"id": "gamer", "observed": True,
                    "known_concepts": ["cornelius", "humble", "scholar", "natural", "philosophy"],
                    "register": "casual", "formal_cues": 0.0, "casual_cues": 4.0}
VANE_LIVE_NEUTRAL = {"id": "n", "observed": True,
                     "known_concepts": ["cornelius", "humble", "scholar", "natural", "philosophy"],
                     "register": "neutral", "formal_cues": 0.0, "casual_cues": 0.0}


def test_register_types_formal_when_content_misses(agent):
    # WITHOUT the register the same concepts are `general` (content misses formal cues) ...
    assert aa.manifold_type({"known_concepts": VANE_LIVE_FORMAL["known_concepts"]})["type"] == "general"
    # ... WITH the formal register on the snapshot it types formal/committed and FIRES.
    est = aa.manifold_type(VANE_LIVE_FORMAL)
    assert est["type"] == "formal" and est["committed"] is True
    assert aa.fires_for(VANE_LIVE_FORMAL) is True
    r = aa.adapt_concepts(agent, AREAS, VANE_LIVE_FORMAL)
    assert r["adapted_flag"] is True
    assert r["adapted"][-1] == aa.abstraction_for(r["foreign"])


def test_casual_register_snapshot_does_not_fire(agent):
    assert aa.manifold_type(VANE_LIVE_CASUAL)["type"] != "formal"
    assert aa.fires_for(VANE_LIVE_CASUAL) is False
    assert aa.adapt_concepts(agent, AREAS, VANE_LIVE_CASUAL)["adapted"] == AREAS


def test_neutral_register_snapshot_does_not_fire(agent):
    assert aa.fires_for(VANE_LIVE_NEUTRAL) is False
    assert aa.adapt_concepts(agent, AREAS, VANE_LIVE_NEUTRAL)["adapted"] == AREAS


# --------------------------------------------------------------------------- #
#  LIVE 2-TURN through converse (the headline): a formal-register greeting then
#  "How are you organised?" -> the organisation answer is ADAPTED (modern-tech
#  collapsed to the umbrella), NOT the flat list. Casual/neutral -> full list.
# --------------------------------------------------------------------------- #

def _live():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _turn(a, text):
    return a.converse(text, a.classify_speech_act(text))


def test_live_formal_register_adapts_organisation_answer():
    a = _live()
    _turn(a, "Good day. I am Cornelius Vane, a humble scholar of natural philosophy.")
    reply = _turn(a, "How are you organised?")
    assert reply.startswith("I am organised into")
    assert "unfamiliar in your world" in reply           # the umbrella landed
    for foreign in ("video_coding_theory", "cloud_infrastructure", "machine_learning"):
        assert foreign not in reply                        # modern-tech collapsed, not dumped flat
    for live in ("mathematics", "philosophy", "engineering"):
        assert live in reply                               # period-compatible domains still land


def test_live_casual_register_keeps_full_list():
    a = _live()
    _turn(a, "hey dude, yeah this is cool, thanks!")
    reply = _turn(a, "How are you organised?")
    assert "video_coding_theory" in reply and "machine_learning" in reply
    assert "unfamiliar in your world" not in reply


def test_live_neutral_default_keeps_full_list():
    a = _live()
    _turn(a, "The weather is fine today.")
    reply = _turn(a, "How are you organised?")
    assert "video_coding_theory" in reply and "machine_learning" in reply
    assert "unfamiliar in your world" not in reply
