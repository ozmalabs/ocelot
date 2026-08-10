"""STEP 3: GENERATE THE UNSTATED INFERENCE (domains/inference_generation.py).

situation_model_reader (step 2) grounds/infers only from STATED information:
a bare "John dropped the glass." infers `on_floor` but never `broken`,
because event_reasoning.json's `infer_broken` rule also needs `fragile` on
the theme, and the bare sentence never states it — an honest residual.

This step closes it with ONE mechanism (gap-detect -> ShapeDecode collapse
against a knowledge codebook -> mint -> re-run the fixpoint), used for TWO
gap flavors:

  * WORLD-KNOWLEDGE / ENABLING-CONDITION: the stalled `fragile` precondition
    is filled from `seeds/inference_knowledge.json`'s `fragile_glassware`
    schema, closing the spine's own documented residual.
  * BRIDGING (referential/part-whole): "We checked the picnic supplies. The
    beer was warm." -> `beer` bridges `part_of(beer, supplies)` with NO
    lexical cue (Haviland & Clark given-new).

Discriminative gates (donkey = 0, no LLM):

  * HEADLINE — BEFORE (spine alone: on_floor, NOT broken) vs AFTER
    (inference: broken, via the supplied fragility) — verbatim closes the
    spine's residual.
  * BRIDGING — part_of(beer, supplies) minted with no lexical cue.
  * STANDARD-OF-COHERENCE gate — shallow fires only the blocking inference;
    deep additionally fires the elaborative one; same input, one tunable
    node flips it.
  * DISCRIMINATIVE / NO OVER-INFERENCE — an entity the codebook does not
    know is fragile (a bare ball) mints nothing; a fully-stated sentence
    triggers no gap at all.
  * GRAPH-NATIVE SOURCE AUDIT — the inference is the ShapeDecode collapse +
    the existing run_rules fixpoint; no Python if/else selects the inferred
    relation; no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_inference_generation.py -p no:randomly -q
"""
from __future__ import annotations

import os
import re as _re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                # noqa: E402
from domains import dictionary_lexicon as dl              # noqa: E402
from domains import inference_generation as ig            # noqa: E402
from domains import situation_model_reader as smr         # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  HEADLINE — closes the spine's own documented residual.
# --------------------------------------------------------------------------- #
def test_headline_closes_the_spine_residual():
    ag = _fresh()
    r = ig.read_and_infer(ag, "John dropped the glass.")

    # BEFORE (the spine alone, situation_model_reader unchanged): on_floor,
    # NOT broken -- the exact residual test_situation_model_wire.py documents.
    before = r["before_situation_model"]["glass"]
    assert before.get("on_floor") == 1 and before.get("fell") == 1
    assert before.get("broken") is None and before.get("fragile") is None

    # a world-knowledge gap was detected and resolved: fragile was NOT stated.
    assert len(r["blocking"]) == 1
    b = r["blocking"][0]
    assert b["minted"] is True
    assert b["gap"]["entity"] == "glass" and b["gap"]["need_attr"] == "fragile"
    assert b["schema"] == "fragile_glassware"
    assert b["supplies"] == {"relation": "is_a", "attr": "fragile"}

    # AFTER: the supplied fragility cascaded through the UNCHANGED fixpoint.
    after = r["situation_model"]["glass"]
    assert after.get("fragile") == 1
    assert after.get("broken") == 1
    assert after.get("worthless") == 1
    assert after.get("broken_inferred") == 1        # the seed's own inferred stamp


def test_headline_verbatim_before_after():
    ag = _fresh()
    r = ig.read_and_infer(ag, "John dropped the glass.")
    before = r["before_situation_model"]["glass"]
    after = r["situation_model"]["glass"]
    assert (before.get("on_floor"), before.get("broken")) == (1, None)
    assert (after.get("on_floor"), after.get("broken"), after.get("worthless")) == (1, 1, 1)


# --------------------------------------------------------------------------- #
#  BRIDGING — a definite with no antecedent, no lexical cue.
# --------------------------------------------------------------------------- #
def test_bridging_no_lexical_cue():
    ag = _fresh()
    text = "We checked the picnic supplies. The beer was warm."
    r = ig.read_and_infer(ag, text)

    assert len(r["bridging"]) == 1
    br = r["bridging"][0]
    assert br["minted"] is True
    assert br["gap"]["entity"] == "beer"
    assert br["schema"] == "picnic_supplies_parts"
    assert br["supplies"] == {"relation": "part_of", "object": "supplies"}

    beer = None
    for n in ag.s.nodes("SmEntity"):
        if ag.s.node(n)["attrs"].get("name") == "beer":
            beer = n
    assert beer is not None
    wholes = [ag.s.node(w)["attrs"].get("name") for w in ag.s.neighbours(beer, "part_of")]
    assert "supplies" in wholes

    # no marker word ("part of", "belongs to", ...) appears in the text --
    # the bridge came from the gap (definite, no antecedent), not a cue.
    assert "part of" not in text.lower() and "belongs" not in text.lower()


# --------------------------------------------------------------------------- #
#  STANDARD-OF-COHERENCE — shallow blocks the elaborative inference; deep fires it.
# --------------------------------------------------------------------------- #
def test_shallow_standard_fires_only_blocking():
    ag = _fresh()
    assert ig.coherence_depth(ag) == "shallow"        # the seed default
    r = ig.read_and_infer(ag, "John dropped the glass.")

    assert any(b["minted"] and b["schema"] == "fragile_glassware" for b in r["blocking"])
    elabs = {e["schema"]: e for e in r["elaborative"] if e["schema"] == "glassware_composition"}
    assert "glassware_composition" in elabs
    assert elabs["glassware_composition"]["minted"] is False
    assert "shallow" in elabs["glassware_composition"]["reason"]
    assert r["situation_model"]["glass"].get("made_of_glass") is None


def test_deep_standard_additionally_fires_elaborative():
    ag = _fresh()
    ig.set_coherence_depth(ag, "deep")
    assert ig.coherence_depth(ag) == "deep"
    r = ig.read_and_infer(ag, "John dropped the glass.")

    # the SAME blocking inference still fires (coherence:"blocking" is depth-independent).
    assert any(b["minted"] and b["schema"] == "fragile_glassware" for b in r["blocking"])
    assert r["situation_model"]["glass"].get("broken") == 1

    # AND now the elaborative one ALSO fires -- same input, one tunable node flips it.
    elabs = {e["schema"]: e for e in r["elaborative"] if e["schema"] == "glassware_composition"}
    assert elabs["glassware_composition"]["minted"] is True
    assert r["situation_model"]["glass"].get("made_of_glass") == 1


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — no over-inference.
# --------------------------------------------------------------------------- #
def test_no_over_inference_uncovered_entity():
    ag = _fresh()
    r = ig.read_and_infer(ag, "John dropped the ball.")
    # the gap IS detected (ball is one conjunct short of broken)...
    assert len(r["blocking"]) == 1
    b = r["blocking"][0]
    # ...but the codebook does not know a ball is fragile -- honest null, nothing minted.
    assert b["minted"] is False
    assert b["schema"] is None
    ball = r["situation_model"]["ball"]
    assert ball.get("broken") is None and ball.get("fragile") is None
    assert ball.get("on_floor") == 1                  # the spine's own inference is untouched


def test_no_gap_when_fully_stated():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The glass is fragile. John dropped the glass.")
    # fragility is STATED -- the spine's own fixpoint already reaches broken,
    # so there is no stalled precondition left for step 3 to detect at all.
    assert r["blocking"] == []
    assert r["before_situation_model"]["glass"].get("broken") == 1
    assert r["situation_model"]["glass"].get("broken") == 1


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_and_decode_is_the_decision():
    src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    assert not _re.search(r"^\s*import re\b", src, _re.M)
    assert "re.compile(" not in src and "re.match(" not in src and "re.search(" not in src
    # the WINNER is read off the decode (reading_collapse._winner), never re-picked.
    assert "rc._winner(res)" in src
    assert "compose_design_for_goal" in src
    # no Python branch keyed on the literal content of a gap's need_attr/entity
    # (e.g. `if need_attr == "fragile"` or `if entity == "glass"`) selects the mint.
    assert 'need_attr ==' not in src
    assert "== \"glass\"" not in src and "== 'glass'" not in src


def test_mint_reuses_ingest_predication_unchanged():
    # the enabling-condition mint is literally situation_model_reader's own
    # property-predication branch -- proven by the SAME *_inferred stamps
    # the spine's own headline test checks.
    ag = _fresh()
    r = ig.read_and_infer(ag, "John dropped the glass.")
    assert r["blocking"][0]["ingest"]["kind"] == "property"
    assert r["blocking"][0]["ingest"]["property"] == "fragile"


# --------------------------------------------------------------------------- #
#  GOAL-FROM-STATE — a need-state ('thirsty') with no explicit 'wanted' mints
#  the character's goal into character_tom's OWN slot.
# --------------------------------------------------------------------------- #
def test_goal_from_state_thirst_crow():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The crow was thirsty. It found a pitcher.")
    hits = [g for g in r["goal"] if g["gap"]["entity"] == "crow" and g["minted"]]
    assert len(hits) == 1
    g = hits[0]
    assert g["schema"] == "need_remedy_thirst"
    assert g["supplies"] == {"relation": "goal", "remedy": "drink"}
    assert r["situation_model"]["crow"].get("goal") == "drink"

    # character_tom's OWN query reads it back -- the SAME slot 'wanted' fills,
    # with NO change to character_tom.py.
    from domains import character_tom as ctom
    assert ctom.character_goal(ag, "crow") == "drink"


def test_goal_from_state_general_hunger_wolf():
    ag = _fresh()
    r = ig.read_and_infer(ag, "The wolf was hungry. It found a rabbit.")
    hits = [g for g in r["goal"] if g["gap"]["entity"] == "wolf" and g["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "need_remedy_hunger"
    assert hits[0]["supplies"] == {"relation": "goal", "remedy": "eat"}
    from domains import character_tom as ctom
    assert ctom.character_goal(ag, "wolf") == "eat"


def test_goal_from_state_discriminative_no_need_state():
    ag = _fresh()
    r = ig.read_and_infer(ag, "John dropped the glass.")
    # 'glass' carries plenty of attrs==1 (fell, on_floor, fragile, broken, ...)
    # -- every one is OFFERED as a candidate (this scan never hardcodes which
    # attr name counts as a need-state) but NONE decodes against the
    # need_remedy_* codebook -- honest null, no spurious goal.
    glass_gaps = [g for g in r["goal"] if g["gap"]["entity"] == "glass"]
    assert glass_gaps                                  # candidates WERE raised
    assert all(not g["minted"] for g in glass_gaps)    # none minted
    assert r["situation_model"]["glass"].get("goal") is None


# --------------------------------------------------------------------------- #
#  PHYSICAL-CAUSAL — a displacement/overflow schema explains a causal link
#  discourse_coherence's own lexical-cohesion signal cannot see (no shared
#  entity token between the two spans), minted onto discourse_coherence's OWN
#  DiscourseEvent graph via its OWN edge primitive.
# --------------------------------------------------------------------------- #
def test_causal_displacement_general():
    ag = _fresh()
    text = "She dropped ice into the glass. The water rose a little higher."
    r = ig.read_and_infer_causal(ag, text)
    hits = [c for c in r["causal"] if c["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "physical_displacement_rise"
    assert hits[0]["supplies"] == {"relation": "cause"}

    sub = ag.s
    a = next(n for n in sub.nodes("DiscourseEvent")
             if sub.node(n)["attrs"]["text"] == "She dropped ice into the glass.")
    b = next(n for n in sub.nodes("DiscourseEvent")
             if sub.node(n)["attrs"]["text"] == "The water rose a little higher.")
    assert sub.has_edge(a, "causes", b)
    assert sub.has_edge(a, "coherence_rel", b)


def test_causal_overflow_general_different_verbs():
    ag = _fresh()
    text = "She poured sugar into the cup. The cup overflowed a little."
    r = ig.read_and_infer_causal(ag, text)
    hits = [c for c in r["causal"] if c["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "physical_addition_overflow"
    assert hits[0]["supplies"] == {"relation": "cause"}


def test_causal_verbatim_fable_sentences():
    # the EXACT two Aesop sentences (pebble-drop / water-rise), verbatim.
    ag = _fresh()
    text = ("Picking up some small pebbles, he dropped them into the pitcher one by one. "
            "With each pebble the water rose a little higher until at last it was near "
            "enough so he could drink.")
    r = ig.read_and_infer_causal(ag, text)
    hits = [c for c in r["causal"] if c["minted"]]
    assert len(hits) == 1
    assert hits[0]["schema"] == "physical_displacement_rise"
    sub = ag.s
    a = next(n for n in sub.nodes("DiscourseEvent")
             if sub.node(n)["attrs"].get("order") == 0)
    b = next(n for n in sub.nodes("DiscourseEvent")
             if sub.node(n)["attrs"].get("order") == 1)
    assert sub.has_edge(a, "causes", b)


def test_causal_discriminative_unrelated_events():
    ag = _fresh()
    text = "He read a book. She sang a song."
    r = ig.read_and_infer_causal(ag, text)
    assert r["causal"]                                  # a candidate WAS raised
    assert all(not c["minted"] for c in r["causal"])    # honest null, no spurious cause
    assert r["causal"][0]["schema"] is None


def test_causal_deferred_when_discourse_graph_not_built():
    # resolve_causal_gap is HONEST about its own dependency: if discourse_
    # coherence.read_discourse has not run over this text yet (no DiscourseEvent
    # nodes exist), it defers rather than fabricating an edge on absent nodes.
    ag = _fresh()
    ig.ensure_seeds(ag)
    gap = {"sentence_a": "She dropped ice into the glass.",
           "sentence_b": "The water rose a little higher.",
           "i": 0, "j": 1, "verb_a": "drop", "verb_b": "rise"}
    rec = ig.resolve_causal_gap(ag, gap)
    assert rec["minted"] is False
    assert rec["schema"] == "physical_displacement_rise"   # the decode DID win...
    assert "not built yet" in rec["reason"]                # ...but the mint deferred honestly


# --------------------------------------------------------------------------- #
#  THE CROW GATE — BOTH mechanisms now FIRE on the frozen fable (DELIBERATE
#  UPDATE — was 4/6). The two obstacles that held them off were CAPABILITY gaps,
#  now closed:
#  (1) GOAL — 'a thirsty Crow' is a PRENOMINAL adjective. reading_collapse.
#      _prenominal_states now surfaces it as crow.thirsty=1 (is_a(crow, thirsty),
#      recognised by the held POS faculty), so this module's goal-from-state
#      gap-detect/decode/mint reaches the state (thirsty -> drink).
#  (2) CAUSE — the harness's build order was wrong (inference ran before
#      discourse). The comprehension READ ORCHESTRATOR (domains/comprehension_
#      reader.read_and_comprehend, now driving the harness) runs the physical-
#      causal pass AFTER discourse_coherence.read_discourse builds the
#      DiscourseEvent graph, so resolve_causal_gap mints the drop->rise causes
#      edge instead of deferring.
#  This module's mechanisms are UNCHANGED — only the harness's call ORDER and the
#  upstream parse changed. Score is now 6/6 (recorded, not silent drift).
# --------------------------------------------------------------------------- #
def test_crow_harness_score_lifted_to_6_by_correct_ordering_and_parse():
    import jabberwock_reads_the_crow as jrc
    result = jrc.run()
    assert result["score"] == 6
    assert result["score_total"] == 6
    goal_rec = next(r for r in result["qa"] if r["question"] == "What did the crow want?")
    cause_rec = next(r for r in result["qa"] if r["question"] == "Why did dropping pebbles help?")
    assert goal_rec["hit"] is True     # crow.thirsty (prenominal parse) -> goal=drink
    assert cause_rec["hit"] is True    # discourse graph built first -> drop->rise causes edge


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the two new mechanisms, same discipline.
# --------------------------------------------------------------------------- #
def test_goal_and_causal_source_audit():
    src = open(os.path.join(ROOT, "domains", "inference_generation.py")).read()
    assert not _re.search(r"^\s*import re\b", src, _re.M)
    assert "re.compile(" not in src and "re.match(" not in src and "re.search(" not in src
    # no Python branch keyed on the literal content of a need-state/verb pair
    # (e.g. `if need_attr == "thirsty"` or `if verb_a == "drop"`) selects the mint.
    assert 'need_attr ==' not in src
    assert 'verb_a ==' not in src and 'verb_b ==' not in src
    # both new resolvers go through the SAME decode_gap -> rc._winner collapse.
    assert src.count("decode_gap(agent,") >= 4


# --------------------------------------------------------------------------- #
#  NO REGRESSION — the knowledge codebook does not disturb the raw spine.
# --------------------------------------------------------------------------- #
def test_spine_unwired_still_bare():
    # calling situation_model_reader directly (NOT through this module) is
    # UNCHANGED -- proves this step only ADDS a pass, never edits the spine.
    ag = _fresh()
    r = smr.read_into_situation_model(ag, "John dropped the glass.")
    glass = r["situation_model"]["glass"]
    assert glass.get("on_floor") == 1
    assert glass.get("broken") is None and glass.get("worthless") is None
