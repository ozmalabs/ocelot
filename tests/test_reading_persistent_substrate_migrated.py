"""test_reading_persistent_substrate_migrated — Deep-Reader WAVE 1A.

The deep reading pipeline (domains/reading_drive.py::run_reading_flow, called via
domains/comprehension_reader.py::read_and_comprehend) is about to become the
agent's SINGLE language-understanding system (chat turns included), which means
it must be safe and correct on a PERSISTENT substrate — many successive reads of
DIFFERENT texts on one long-lived agent graph. Before this change it was
one-shot-only: `_source_text` returned the FIRST `Source` node ever minted, so
every later flow silently re-read flow #1's text forever (measured: three
successive reads of different sentences -> only sentence #1's SmEntities ever
minted), the seeded `la_rearm_*` rules re-armed order-N stages off UNSCOPED
global `Count(...)`s (so a later flow's growth could re-trigger and SUPERSEDE an
earlier, already-returned flow's Trope/NarrativeRole/Claim nodes), and the five
cortex Reflex nodes had their Python responses registered only on the transient
per-call `_LAAdapter`, so a live, persistent `WorldAdapter` driving the SAME
substrate afterward would phantom-fire them forever (stimulus trips, `fire_count`
still increments, no response resolves).

This gate proves the fix: (1) multi-read correctness — each flow's own
SmEntities/SentenceParse/predications correspond to ITS OWN text, independently
queryable; (2) near-flat cost — 30-60 single-sentence reads don't blow up
O(turns^2); (3) zero phantom cortex-reflex fires on a live WorldAdapter's tick
loop after a read completes; (4) the reading-side `SmMention` rename never mints
a conversation-typed `Mention`, and conversation tokenisation is unaffected; (5)
the new `coref_entities.arm_deictic_centre` API grounds "I"/"you" to a
caller-supplied speaker/addressee, with unarmed behaviour unchanged (parity).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_reading_persistent_substrate_migrated.py -p no:randomly -q -s
"""
from __future__ import annotations

import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core, CORE_SEEDS                  # noqa: E402
from substrate.world_adapter import WorldAdapter                       # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import coref_entities as ce                               # noqa: E402
from domains import comprehension_reader as cr                         # noqa: E402
from domains import reading_drive as rd                                # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


class _Agent:
    """A bare-substrate adapter facade, the SAME shape tests/test_gender_shape.py
    and friends already use — no WorldAdapter machinery, so the multi-read/cost
    gates exercise the flow-scoping fix in isolation from the live-tick concern
    (that is gate 3's own job, on a REAL WorldAdapter)."""
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  (1) MULTI-READ CORRECTNESS — kill the stale-Source bug.
# --------------------------------------------------------------------------- #
def test_three_successive_reads_each_see_only_their_own_text():
    """Three DIFFERENT texts, read one after another on ONE substrate. Before the
    fix, `_source_text` always returned the FIRST Source's text, so every flow
    after the first minted entities for sentence #1 only. Each read here must
    see ONLY its own entities/sentences/predications."""
    agent = _fresh()
    texts = [
        "A thirsty crow found a pitcher. The water was too low. The crow dropped "
        "pebbles into the pitcher.",
        "A hungry fox saw ripe grapes on a vine. The grapes hung too high. The fox "
        "gave up and walked away.",
        "A slow tortoise challenged a proud hare to a race. The hare napped midway. "
        "The tortoise won the race.",
    ]
    expect_entities = [
        {"crow", "water"},
        {"fox", "grapes"},
        {"tortoise", "hare", "race"},
    ]
    results = []
    for text in texts:
        bb = cr.read_and_comprehend(agent, text, window=2)
        results.append(bb)

    for bb, text, expect in zip(results, texts, expect_entities):
        sm_names = set(bb["spine"]["situation_model"].keys())
        assert expect & sm_names == expect, (
            "flow lost its own entities: expected %r subset of %r" % (expect, sm_names))
        # the sentences this flow's own comprehension view carries are ONLY its own.
        assert bb["sentences"], "flow has no sentences at all"
        for s in bb["sentences"]:
            assert s in text, "flow leaked a foreign sentence: %r not in %r" % (s, text)
        # textbase/predications (off SentenceParse) are this flow's OWN, in order.
        textbase = bb["spine"]["textbase"]
        assert [t["sentence"] for t in textbase] == bb["sentences"]

    # cross-check: NONE of flow 0's entities leak into flow 1's or flow 2's view,
    # and vice versa (the stale-Source bug would make them ALL identical to flow 0).
    sm0, sm1, sm2 = (set(r["spine"]["situation_model"].keys()) for r in results)
    assert sm0 != sm1 and sm1 != sm2 and sm0 != sm2


def test_each_flow_independently_queryable_after_the_fact():
    """Re-run `run_reading_flow` a fourth time and confirm the FIRST flow's report
    (captured before) is still what a fresh independent read of ITS text alone
    produces — i.e. flow 1 was never mutated by flows 2-4 running afterward."""
    agent = _fresh()
    text_a = "A wolf chased a lamb through the meadow. The lamb hid in the reeds."
    bb_a_first = cr.read_and_comprehend(agent, text_a, window=2)

    for extra in ("A dog buried a bone in the yard. The dog forgot where it was.",
                  "A mouse freed a lion from a net. The lion thanked the mouse.",
                  "A boy cried wolf twice. The villagers stopped believing the boy."):
        cr.read_and_comprehend(agent, extra, window=2)

    # an INDEPENDENT, single-shot read of text_a on a FRESH substrate is the oracle.
    oracle = cr.read_and_comprehend(_fresh(), text_a, window=2)
    assert set(bb_a_first["spine"]["situation_model"].keys()) == \
        set(oracle["spine"]["situation_model"].keys())
    assert bb_a_first["sentences"] == oracle["sentences"]


def test_goal_and_source_are_flow_scoped_via_reads_source_edge():
    """Each flow's Goal carries its OWN `reads_source` edge to its OWN Source —
    the flow identity `run_reading_flow` threads through every re-reader."""
    agent = _fresh()
    cr.read_and_comprehend(agent, "A crow found a pitcher.", window=2)
    cr.read_and_comprehend(agent, "A fox saw some grapes.", window=2)
    sub = agent.s
    sources = list(sub.nodes("Source"))
    goals = list(sub.nodes("Goal"))
    assert len(sources) == 2
    assert len(goals) == 2
    texts = set()
    for g in goals:
        tgt = list(sub.neighbours(g, "reads_source"))
        assert len(tgt) == 1, "each flow's Goal must read exactly its OWN Source"
        texts.add(sub.node(tgt[0])["attrs"].get("text"))
    assert texts == {"A crow found a pitcher.", "A fox saw some grapes."}


# --------------------------------------------------------------------------- #
#  (2) NEAR-FLAT COST — O(turns) -> O(this-flow), not O(turns^2) over the run.
# --------------------------------------------------------------------------- #
def test_near_flat_cost_over_many_single_sentence_reads():
    """30-60 single-sentence reads on ONE substrate. Per-read node-mint count
    stays constant (each sentence mints the same shape of graph data regardless
    of how many earlier reads happened); wall time for late reads is not blown
    up relative to early reads (loosely — not >3x)."""
    agent = _fresh()
    n = 40
    mint_deltas = []
    times = []
    prev_total = len(list(agent.s.nodes("SmEntity")))
    for i in range(n):
        text = "A fox%d chased a hare%d across the field." % (i, i)
        t0 = time.perf_counter()
        cr.read_and_comprehend(agent, text, window=2)
        times.append(time.perf_counter() - t0)
        total = len(list(agent.s.nodes("SmEntity")))
        mint_deltas.append(total - prev_total)
        prev_total = total

    # every single-sentence read mints the SAME NUMBER of new SmEntity nodes
    # (2 entities: fox%d, hare%d) -- a growing per-read mint count would mean a
    # later read is (wrongly) re-processing earlier flows' material.
    assert len(set(mint_deltas)) == 1, (
        "per-read SmEntity mint count is NOT constant across reads: %r" % mint_deltas)

    early = sum(times[:10]) / 10
    late = sum(times[-10:]) / 10
    print("\nnear-flat cost: early(1-10) avg=%.4fs late(31-40) avg=%.4fs ratio=%.2fx"
          % (early, late, (late / early) if early else float("inf")))
    assert late < max(early * 3.0, early + 0.05), (
        "cost grew super-linearly: early avg %.4fs -> late avg %.4fs" % (early, late))


# --------------------------------------------------------------------------- #
#  (3) PHANTOM REFLEXES — zero no-op cortex-reflex fires once a flow is idle.
# --------------------------------------------------------------------------- #
def test_no_phantom_cortex_reflex_fires_on_a_live_world_adapter():
    """Read on a REAL, persistent WorldAdapter (not the transient _LAAdapter) —
    exactly the shape a chat daemon would drive. Before the fix, the five cortex
    Reflex nodes (seeds/reading_cortices.json) had their Python responses
    registered ONLY on the throwaway `_LAAdapter` `run_reading_flow` builds
    internally; a live adapter ticking the SAME substrate afterward would
    discover them by name (`_merge_seed_loaded_reflexes`), evaluate their
    stimulus every tick, and silently no-op 'fire' them (stimulus true,
    `fire_count`/`last_fired_tick` stamped, no response resolves) FOREVER,
    because the `la_rearm_*` rules used unscoped `Count(...)`s that a later
    flow's own growth could re-trip for an EARLIER, already-idle stage. Both are
    now fixed (flow-scoped rearm Count()s + flow-scoped stage advance) so the
    stimulus is false once idle, regardless of which adapter evaluates it."""
    wa = WorldAdapter(seeds=CORE_SEEDS)
    rd.run_reading_flow(wa, "A crow found a pitcher of water. The water was too low. "
                            "The crow dropped pebbles into the pitcher.", report="comprehend")

    cortex_names = ("language_cortex", "situation_cortex", "social_cortex",
                    "narrative_cortex", "executive_cortex")
    # `reflex_nodes` is populated LAZILY, inside `fire_reflexes()` itself
    # (`_merge_seed_loaded_reflexes`) — one priming call before reading the
    # baseline counts, then every further call/count is the actual idle-loop
    # measurement the gate cares about.
    wa.fire_reflexes()
    wa._master["tick"] += 1
    fire_counts_before = {}
    for name in cortex_names:
        nid = wa._master["reflex_nodes"].get(name)
        assert nid is not None, "cortex reflex %r not installed" % name
        fire_counts_before[name] = int(wa.s.node(nid)["attrs"].get("fire_count", 0))

    total_fired = 0
    for _ in range(30):
        fired = wa.fire_reflexes()
        total_fired += len([f for f in fired if f in cortex_names])
        wa._master["tick"] += 1

    assert total_fired == 0, "cortex reflexes fired %d times while idle (phantom)" % total_fired
    for name in cortex_names:
        nid = wa._master["reflex_nodes"][name]
        after = int(wa.s.node(nid)["attrs"].get("fire_count", 0))
        assert after == fire_counts_before[name], (
            "%r fire_count moved from %d to %d while idle" % (name, fire_counts_before[name], after))


def test_cortex_responses_resolve_when_registered_on_the_live_adapter():
    """Defence-in-depth (Wave 1A option 1): `run_reading_flow` also registers the
    cortex advance responses on the CALLER's own live adapter (when it is one),
    not only the transient `_LAAdapter` — so if a stimulus ever DID legitimately
    trip on the live adapter, it has a real, resolving response rather than a
    registered-nowhere phantom."""
    wa = WorldAdapter(seeds=CORE_SEEDS)
    rd.run_reading_flow(wa, "A crow found a pitcher.", report="comprehend")
    for name in ("language_cortex_advance", "situation_cortex_advance",
                "social_cortex_advance", "narrative_cortex_advance",
                "executive_cortex_advance"):
        assert wa._master["reflex_responses"].get(name) is not None, (
            "%r has no resolvable response on the live adapter" % name)


# --------------------------------------------------------------------------- #
#  (4) SmMENTION — the reading-side rename never touches conversation Mention.
# --------------------------------------------------------------------------- #
def test_reading_mints_no_conversation_mention_nodes():
    agent = _fresh()
    # a pronoun so the coref pipeline actually mints an SmMention (a purely
    # third-person-proper-noun sentence never resolves a pronoun/deixis form).
    cr.read_and_comprehend(agent, "A crow found a pitcher. It was thirsty.", window=2)
    sub = agent.s
    assert list(sub.nodes("Mention")) == [], (
        "the reading pipeline minted a conversation-typed Mention node")
    assert list(sub.nodes("SmMention")), "the reading pipeline minted no SmMention at all"


def test_conversation_tokenisation_still_uses_plain_mention():
    wa = WorldAdapter(seeds=CORE_SEEDS)
    wa.add_inbound("The crow found a pitcher of water.")
    sub = wa.s
    mention_texts = {sub.node(m)["attrs"].get("text") for m in sub.nodes("Mention")}
    assert "crow" in mention_texts and "pitcher" in mention_texts
    # conversation Mentions carry `text`, never the reading side's `surface`/`deixis`.
    for m in sub.nodes("Mention"):
        at = sub.node(m)["attrs"]
        assert "surface" not in at and "deixis" not in at


def test_reading_and_conversation_coexist_on_one_substrate():
    """Both systems minting on the SAME substrate never collide by node type."""
    wa = WorldAdapter(seeds=CORE_SEEDS)
    wa.add_inbound("Tell me about crows.")
    rd.run_reading_flow(wa, "A crow found a pitcher. It was thirsty.", report="comprehend")
    sub = wa.s
    conv_mentions = {sub.node(m)["attrs"].get("text") for m in sub.nodes("Mention")}
    sm_mentions = {sub.node(m)["attrs"].get("surface") for m in sub.nodes("SmMention")}
    assert conv_mentions, "conversation tokenisation produced nothing"
    assert sm_mentions, "reading coref produced nothing"


# --------------------------------------------------------------------------- #
#  (5) DEICTIC ARMING — "I"/"you" ground to a caller-supplied speaker/addressee.
# --------------------------------------------------------------------------- #
def test_armed_you_resolves_to_the_addressee():
    agent = _fresh()
    armed = ce.arm_deictic_centre(agent, speaker="jabberwock", addressee="reader")
    assert armed == {"speaker": "jabberwock", "addressee": "reader"}
    ce.read_into_situation_model(agent, "You know the answer already.")
    sub, _ = ce._resolve(agent)
    you_mentions = [m for m in sub.nodes("SmMention")
                   if sub.node(m)["attrs"].get("surface") == "you"]
    assert you_mentions, "no 'you' SmMention minted"
    refs = [sub.node(n)["attrs"].get("name")
            for m in you_mentions for n in sub.neighbours(m, "refers_to")]
    assert "reader" in refs, "'you' did not resolve refers_to the armed addressee"


def test_armed_i_resolves_to_the_speaker():
    agent = _fresh()
    ce.arm_deictic_centre(agent, speaker="jabberwock", addressee="reader")
    # 'want' is not a WordNet communication verb, so this sentence carries no
    # in-text speech-act tag that would re-collapse the (already armed) centre --
    # isolates the EXTERNAL-arming path from the in-text speech-act-tag path.
    ce.read_into_situation_model(agent, "I want the truth.")
    sub, _ = ce._resolve(agent)
    i_mentions = [m for m in sub.nodes("SmMention")
                 if sub.node(m)["attrs"].get("surface") == "i"]
    assert i_mentions, "no 'i' SmMention minted"
    refs = [sub.node(n)["attrs"].get("name")
            for m in i_mentions for n in sub.neighbours(m, "refers_to")]
    assert "jabberwock" in refs, "'i' did not resolve refers_to the armed speaker"


def test_unarmed_deixis_stays_held_open_parity():
    """Parity: with NO arming, first/second person still HOLD OPEN exactly as
    before (the external-arming source changes nothing about the unarmed path)."""
    agent = _fresh()
    ce.read_into_situation_model(agent, "You know the answer already. I want the truth.")
    sub, _ = ce._resolve(agent)
    for surface in ("you", "i"):
        mentions = [m for m in sub.nodes("SmMention")
                   if sub.node(m)["attrs"].get("surface") == surface]
        assert mentions, "no %r SmMention minted" % surface
        for m in mentions:
            assert sub.node(m)["attrs"].get("held_open") == 1.0, (
                "%r resolved without arming -- should be held open" % surface)
            assert list(sub.neighbours(m, "refers_to")) == []


def test_in_text_speech_act_tag_still_overrides_after_arming():
    """An in-text speech-act tag encountered AFTER external arming still updates
    the centre (parity with the pre-Wave-1A in-text behaviour) -- arming is an
    additional SOURCE, not a new precedence rule that locks out the text. Drives
    `_update_deictic_centre` directly (the mechanism `_shim_spine`'s whole-text
    driver calls per sentence, UNCHANGED by Wave 1A) with a resident speaker, so
    the assertion is deterministic and independent of any particular sentence's
    end-to-end parse (a real English sentence's speech-act predication shape can
    vary with unrelated WordNet/lexicon warm-state; that variability belongs to
    `reading_collapse`/`situation_model_reader`, not to this arming gate)."""
    agent = _fresh()
    armed = ce.arm_deictic_centre(agent, speaker="jabberwock", addressee="reader")
    assert armed == {"speaker": "jabberwock", "addressee": "reader"}
    # 'fox' must be a RESIDENT participant before the speech-act predication is
    # read (`_arg_is_participant`'s residency gate) -- the same precondition a
    # real text satisfies by mentioning the speaker before it speaks.
    ce._touch_entity(agent, "The fox spoke.", "fox", "agent", 1)
    returned = ce._update_deictic_centre(agent, [["said", "fox", "i"]], 2)
    assert returned == "fox", "the in-text speech-act tag failed to resolve a speaker"

    sub, _ = ce._resolve(agent)
    nid = ce._deictic_node(agent, create=False)
    assert nid is not None
    at = sub.node(nid)["attrs"]
    # the in-text tag OVERRODE the armed speaker (arming was a starting value,
    # not a lock) -- and the adjacency-pair flip moved it to addressee, exactly
    # the documented behaviour for an in-text speaker CHANGE.
    assert at.get("speaker") == "fox"
    assert at.get("addressee") == "jabberwock"
