"""Intent + referent-resolution + speech-bridge RULES, migrated — they now live
in the `intent` seed as graph-resident RewriteRules and fire under the Rust rule
engine (`run_rules`) on a seed-booted WorldAdapter, with NO CuriousAgent.

These rules were authored as Python `gr.make_rule` rules in domains/intent.py;
`tools/capture_intent_rules.py` extracts them into seeds/intent.json's `rules`
section (the loader/run_rules path the migrated core rules already use). The
speech-act taxonomy + adjacency pairs they read (statement/question/greeting +
expects_response) come from the conversation seed as graph data.

The WorldAdapter surface is mechanical I/O: receive_utterance mints a
Message{has_speech_act, sent_by}, comprehend() ticks the rules to a fixed point,
intent_of reads the result. The COMPREHENSION is the seeded Rules.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def _names(wa, src, edge):
    return [wa.s.node(t)["attrs"].get("name")
            for t in wa.inner.neighbours(src, edge)]


def _types(wa, src, edge):
    return [wa.s.node(t)["type"] for t in wa.inner.neighbours(src, edge)]


# --- intent construction ------------------------------------------------

def test_inbound_message_gets_an_intent():
    """intent_from_claim matches (Message, has_speech_act, sent_by) and builds
    an Intent."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("the sky is blue", speech_act="statement")
    wa.comprehend()
    it = wa.intent_of(mid)
    assert it is not None
    assert wa.s.node(it)["type"] == "Intent"


def test_intent_has_speech_act_speaker_and_claimed_speaker():
    wa = WorldAdapter()
    mid = wa.receive_utterance("what is it?", speech_act="question",
                               speaker="user")
    wa.comprehend()
    it = wa.intent_of(mid)
    assert _names(wa, it, "speech_act") == ["question"]
    # both speaker and claimed_speaker point at the Interlocutor (initial belief)
    assert _types(wa, it, "speaker") == ["Interlocutor"]
    assert _types(wa, it, "claimed_speaker") == ["Interlocutor"]


def test_each_inbound_gets_its_own_intent():
    wa = WorldAdapter()
    m1 = wa.receive_utterance("hi", speech_act="greeting")
    m2 = wa.receive_utterance("bye", speech_act="statement")
    wa.comprehend()
    i1, i2 = wa.intent_of(m1), wa.intent_of(m2)
    assert i1 is not None and i2 is not None and i1 != i2


# --- adjacency pairs (expects_response propagation) ---------------------

def test_question_intent_inherits_expects_answer():
    """intent_inherit_expects_response copies the speech-act's expects_response
    (question -> answer, wired in the conversation seed) onto the Intent."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("what is it?", speech_act="question")
    wa.comprehend()
    assert _names(wa, wa.intent_of(mid), "expects_response") == ["answer"]


def test_greeting_intent_expects_greeting_back():
    """The mirrored rule handles the self-pair greeting -> greeting (sa == r)."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("hello", speech_act="greeting")
    wa.comprehend()
    assert _names(wa, wa.intent_of(mid), "expects_response") == ["greeting"]


# --- unknown speaker ----------------------------------------------------

def test_unknown_speaker_when_no_claim_on_record():
    """A Message with a speech act but NO sent_by -> intent_from_no_claim builds
    an Unknown speaker placeholder."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("anybody there?", speech_act="question",
                               speaker=None)
    wa.comprehend()
    it = wa.intent_of(mid)
    assert it is not None
    assert _types(wa, it, "speaker") == ["Unknown"]


# --- fixed point --------------------------------------------------------

def test_rules_idempotent_at_fixed_point():
    """Running comprehend again adds nothing — the rules are at a fixed point."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("the sky is blue", speech_act="statement")
    wa.comprehend()
    n_intent = len(list(wa.inner.neighbours(mid, "has_intent")))
    wa.comprehend()
    assert len(list(wa.inner.neighbours(mid, "has_intent"))) == n_intent
    assert n_intent == 1


# --- speech bridge (ties the audio faculty into intent) -----------------

def test_speech_bridge_acoustic_sign_refers_to_denoted_concept():
    """rule_acoustic_sign_refers_to_denoted_concept: an AcousticSign that is a
    Message's has_mention and denotes a Concept gets a refers_to edge to it —
    so a heard sign is treated as a Mention by the intent layer. This is exactly
    the shape WorldAdapter.ingest_audio_file produces (Message -has_mention->
    AcousticSign)."""
    wa = WorldAdapter()
    wa._ensure_intent_seeds()
    concept = wa._concept_by_name("greeting")
    msg = wa.s.add_node("Message", {"from": "interlocutor", "source": "audio"})
    sign = wa.s.add_node("AcousticSign", {"form": "hi"})
    wa.inner.add_edge_unchecked(msg, "has_mention", sign)
    wa.inner.add_edge_unchecked(sign, "denotes", concept)
    wa.comprehend()
    assert concept in set(wa.inner.neighbours(sign, "refers_to"))


# --- referent resolution (Mention -> Concept) ---------------------------

def _mention_ref(wa, mid, word):
    """The label (concept name or node type) `word`'s Mention resolves to."""
    for mn in wa.inner.neighbours(mid, "has_mention"):
        if wa.s.node(mn)["attrs"].get("text") == word:
            refs = wa.inner.neighbours(mn, "refers_to")
            if not refs:
                return None
            n = wa.s.node(refs[0])
            return n["attrs"].get("name") or n["type"]
    return "NO_MENTION"


def test_inbound_writes_a_mention_per_token():
    wa = WorldAdapter()
    mid = wa.receive_utterance("tell me about question", speech_act="statement")
    mentions = [wa.s.node(m)["attrs"]["text"]
                for m in wa.inner.neighbours(mid, "has_mention")]
    assert mentions == ["tell", "me", "about", "question"]


def test_mention_resolves_to_known_concept():
    """'question' is a seed Concept the agent knows -> its Mention refers_to it."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("about question", speech_act="statement")
    wa.comprehend()
    assert _mention_ref(wa, mid, "question") == "question"


def test_intent_about_concept_propagated_from_mention():
    wa = WorldAdapter()
    mid = wa.receive_utterance("about question", speech_act="statement")
    wa.comprehend()
    assert "question" in _names(wa, wa.intent_of(mid), "about_concept")


def test_unknown_word_produces_unresolved_mention():
    wa = WorldAdapter()
    mid = wa.receive_utterance("about zzzqqq", speech_act="statement")
    wa.comprehend()
    assert _mention_ref(wa, mid, "zzzqqq") is None


def test_referent_resolution_is_idempotent():
    wa = WorldAdapter()
    mid = wa.receive_utterance("about question", speech_act="statement")
    wa.comprehend()
    n = len(wa.inner.neighbours(
        next(m for m in wa.inner.neighbours(mid, "has_mention")
             if wa.s.node(m)["attrs"]["text"] == "question"), "refers_to"))
    wa.comprehend()
    again = len(wa.inner.neighbours(
        next(m for m in wa.inner.neighbours(mid, "has_mention")
             if wa.s.node(m)["attrs"]["text"] == "question"), "refers_to"))
    assert n == again == 1


def test_multiple_known_concepts_all_resolve():
    """Several known concepts in one utterance each resolve."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("tell and know question", speech_act="statement")
    wa.comprehend()
    assert _mention_ref(wa, mid, "tell") == "tell"
    assert _mention_ref(wa, mid, "know") == "know"
    assert _mention_ref(wa, mid, "question") == "question"


# --- pronoun resolution (first / second person) -------------------------

def test_first_person_resolves_to_speaker():
    wa = WorldAdapter()
    mid = wa.receive_utterance("do you know me", speech_act="question",
                               speaker="user")
    wa.comprehend()
    assert _mention_ref(wa, mid, "me") == "user"


def test_first_person_variants_all_resolve_to_speaker():
    wa = WorldAdapter()
    mid = wa.receive_utterance("i me my mine", speech_act="statement",
                               speaker="user")
    wa.comprehend()
    for form in ("i", "me", "my", "mine"):
        assert _mention_ref(wa, mid, form) == "user", form


def test_second_person_resolves_to_addressee():
    wa = WorldAdapter()
    mid = wa.receive_utterance("do you know", speech_act="question",
                               speaker="user")
    wa.comprehend()
    assert _mention_ref(wa, mid, "you") == "Agent"


def test_second_person_variants_all_resolve_to_addressee():
    wa = WorldAdapter()
    mid = wa.receive_utterance("you your yours", speech_act="statement",
                               speaker="user")
    wa.comprehend()
    for form in ("you", "your", "yours"):
        assert _mention_ref(wa, mid, form) == "Agent", form


def test_pronouns_do_not_resolve_to_concepts():
    """First/second-person pronouns resolve to the speaker/addressee, never to a
    Concept — even though they are matched by the same has_mention surface."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("you and me", speech_act="statement",
                               speaker="user")
    wa.comprehend()
    assert _mention_ref(wa, mid, "you") == "Agent"
    assert _mention_ref(wa, mid, "me") == "user"


# --- anaphora (it / this / that -> prior turn's about_concept) -----------

def _two_turns(wa, t1, t2):
    wa.receive_utterance(t1, speech_act="statement", speaker="user")
    wa.comprehend()
    mid2 = wa.receive_utterance(t2, speech_act="statement", speaker="user")
    wa.comprehend()
    return mid2


def test_anaphoric_it_binds_to_prior_about_concept():
    wa = WorldAdapter()
    mid2 = _two_turns(wa, "the question matters", "answer it")
    assert _mention_ref(wa, mid2, "it") == "question"


def test_anaphoric_it_propagates_to_intent_about_concept():
    wa = WorldAdapter()
    mid2 = _two_turns(wa, "the question matters", "answer it")
    assert "question" in _names(wa, wa.intent_of(mid2), "about_concept")


def test_it_in_first_turn_remains_unresolved():
    wa = WorldAdapter()
    mid = wa.receive_utterance("answer it", speech_act="statement",
                               speaker="user")
    wa.comprehend()
    assert _mention_ref(wa, mid, "it") is None


def test_this_and_that_resolve_anaphorically_like_it():
    wa = WorldAdapter()
    assert _mention_ref(wa, _two_turns(wa, "the question matters",
                                       "explain this"), "this") == "question"
    wa2 = WorldAdapter()
    assert _mention_ref(wa2, _two_turns(wa2, "the question matters",
                                        "explain that"), "that") == "question"


def test_anaphoric_chain_walks_through_intermediate_pronoun_turns():
    """Turn 2 references 'question' via 'it' (propagating it onto turn 2's
    Intent); turn 3's 'it' walks back one step to turn 2 and finds it there."""
    wa = WorldAdapter()
    wa.receive_utterance("the question is hard", speech_act="statement",
                         speaker="user")
    wa.comprehend()
    wa.receive_utterance("i need it answered", speech_act="statement",
                         speaker="user")
    wa.comprehend()
    mid3 = wa.receive_utterance("consider it", speech_act="statement",
                                speaker="user")
    wa.comprehend()
    assert "question" in _names(wa, wa.intent_of(mid3), "about_concept")


def test_anaphoric_fires_only_when_prior_intent_has_about_concept():
    """A prior turn with no known concept gives 'it' nothing to bind to."""
    wa = WorldAdapter()
    mid2 = _two_turns(wa, "the foobletwizz exploded", "consider it")
    assert _mention_ref(wa, mid2, "it") is None


# --- speech bridge (AcousticSign as Mention) ----------------------------

def _heard_sign(wa, mid, concept_name):
    """Attach an AcousticSign that denotes a concept to a Message (as a heard
    Mention) — the shape the audio faculty produces."""
    c = wa._concept_by_name(concept_name)
    sign = wa.s.add_node("AcousticSign", {"label": "heard"})
    wa.inner.add_edge_unchecked(mid, "has_mention", sign)
    wa.inner.add_edge_unchecked(sign, "denotes", c)
    return sign


def test_acoustic_sign_plays_the_role_of_a_mention():
    """A heard AcousticSign denoting a Concept gets refers_to (bridge) and its
    Intent about_concept (propagation) — same path a text Mention takes."""
    wa = WorldAdapter()
    mid = wa.receive_utterance("listen", speech_act="statement", speaker="user")
    wa.comprehend()
    sign = _heard_sign(wa, mid, "question")
    wa.comprehend()
    assert "question" in [wa.s.node(c)["attrs"].get("name")
                          for c in wa.inner.neighbours(sign, "refers_to")]
    assert "question" in _names(wa, wa.intent_of(mid), "about_concept")


def test_speech_bridge_propagates_only_once():
    wa = WorldAdapter()
    mid = wa.receive_utterance("listen", speech_act="statement", speaker="user")
    wa.comprehend()
    sign = _heard_sign(wa, mid, "question")
    wa.comprehend()
    wa.comprehend()
    assert len(wa.inner.neighbours(sign, "refers_to")) == 1
