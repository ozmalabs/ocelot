"""test_summit_jabberwocky — THE SUMMIT (Phase 5): the goal-driven, tick-driven
cortical reader is pointed at its OWN NAMESAKE, Lewis Carroll's 'Jabberwocky',
and the HONEST result is locked as a regression.

This test adds NO capability and edits NO domain module or seed. It runs the
already-committed goal-driven flow (`reading_drive.run_reading_flow`, driven by
`cognitive_tick`) on the verbatim poem and asserts the honest ledger the summit
script prints:

  * LEXIS / OOV -- CONFIRMED (Gamma separable from the lexeme). The reader
    ingests the half-nonsense poem without crashing; pure coinages resolve to 0
    WordNet synsets (OOV) and become unknown-category entities / OOV attributes.
    Carroll's ADOPTED coinages (chortle/galumph/burble/gyre) are IN WordNet.
  * REAL VERBS -> EVENTS -- PARTIAL. Some real verbs mint eventive SmEvents;
    WordNet first-synset mis-categorises catch/bite/slain as non-events.
  * ARC -- THE CEILING BITES (the PARSE, not the nonsense). No entity carries a
    full setup->problem->solution->resolution arc; the hero 'he' never unifies.
  * TROPE / THEME -- honest null.
  * ANALYSIS + verify_grounding -- the anti-hallucination gate HOLDS: 0 Claim
    nodes, EMPTY analysis, grounding ok. The reader refuses to fabricate.
  * THE FRAME -- not recognised (no StoryBoundary / RepeatedMaterial / StoryUnit).
  * NO TUNING -- no poem token appears in any reader/analysis module; donkey = 0
    (no LLM), no `import re`, no `git`. Summit = this test + the script only.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_summit_jabberwocky.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import reading_drive as rd                          # noqa: E402
from domains import literary_analysis as la                      # noqa: E402
import jabberwock_reads_jabberwocky as jw                        # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def rec():
    """ONE goal-driven, tick-driven run of the poem, shared across assertions.
    run_reading_flow does ingest->goal->stages->cognitive_tick; there is NO
    Python faculty orchestration between it and the read-offs below."""
    return jw.read_jabberwocky()


# --------------------------------------------------------------------------- #
#  THE FLOW RAN GOAL-DRIVEN + TICK-DRIVEN TO STEADY STATE.
# --------------------------------------------------------------------------- #
def test_flow_is_goal_and_tick_driven_to_steady_state(rec):
    agent = rec["agent"]
    # every comprehension faculty reached `done` via the tick fixpoint (not a
    # Python loop) -- exactly like test_goal_driven_analysis's stage gate.
    stages = {agent.s.node(n)["attrs"].get("name"): agent.s.node(n)["attrs"].get("status")
              for n in agent.s.nodes("AnalysisStage")}
    assert stages, "no AnalysisStage nodes minted -- flow did not seed the goal"
    for name in ("spine", "infer_goal", "discourse", "narrative", "trope"):
        assert stages.get(name) == "done", "stage %s not done: %r" % (name, stages.get(name))
    # the goal-driven `analyse` in the script names no faculty module between
    # ingest and read-off -- only run_reading_flow + graph queries.
    body = inspect.getsource(jw.read_jabberwocky).split('"""', 2)[-1]
    for mod in ("coref_entities", "situation_model_reader", "inference_generation",
                "discourse_coherence", "narrative_structure", "trope_theme"):
        assert mod not in body, "read_jabberwocky orchestrates faculty %s" % mod
    assert "run_reading_flow" in body


# --------------------------------------------------------------------------- #
#  LAYER 1 -- LEXIS / OOV (Gamma-from-residual, LEXICAL layer) -- CONFIRMED.
# --------------------------------------------------------------------------- #
def test_pure_nonsense_is_oov_zero_wordnet_synsets():
    """Every pure Carroll coinage resolves to ZERO WordNet synsets -> OOV. This
    is the lexical half of the thesis: the reader's namesake is half-invented and
    the invented half is simply unknown vocabulary."""
    for w in jw.PURE_NONSENSE:
        n, ln, cat = jw._wn_audit(w)
        assert n == 0, "expected OOV for %r, got %d synsets (%s)" % (w, n, ln)


def test_carroll_adopted_coinages_are_in_wordnet_not_oov():
    """The honest twist: Carroll's coinages that ENTERED English -- chortle,
    galumph, burble, gyre -- are IN WordNet. OOV tracks real lexical history,
    not the poem's invented-ness."""
    for w in jw.CARROLL_ADOPTED:
        n, ln, cat = jw._wn_audit(w)
        assert n >= 1, "expected %r to be in WordNet (adopted coinage), got OOV" % w


def test_nonsense_lands_as_oov_residue_not_a_choke(rec):
    """The poem is INGESTED (a non-empty situation model is built) and the
    nonsense lands as OOV residue: unknown-category SmEntity nodes AND OOV
    attributes (e.g. 'vorpal' on the sword) -- the structure machinery ran over
    the invented lexis without crashing."""
    agent = rec["agent"]
    ents = jw._entities(agent)
    assert len(ents) >= 8, "no situation model built from the poem"
    # at least one unknown-category (OOV) entity
    assert any(e.get("coref_category") == "unknown" for e in ents), \
        "no OOV (unknown-category) entity -- nonsense was not handled as OOV"
    # 'vorpal' (pure nonsense) attached as an OOV attribute on the sword entity
    assert any(e.get("name") == "sword" and e.get("vorpal") for e in ents), \
        "the OOV adjective 'vorpal' did not attach as an attribute"


# --------------------------------------------------------------------------- #
#  LAYER 2 -- REAL VERBS -> EVENTS (partial), WordNet mis-categorisation named.
# --------------------------------------------------------------------------- #
def test_some_real_verbs_mint_eventive_smevents(rec):
    """The arc's skeleton partially survives: real verbs took/left/went/chortled
    mint eventive SmEvents (lemmas take/leave/move/chortle), proving the generic-
    eventive path fires on the REAL words while the nonsense stays OOV."""
    agent = rec["agent"]
    lemmas = {e["lemma"] for e in jw._events(agent)}
    got = lemmas & {"take", "leave", "move", "chortle"}
    assert len(got) >= 3, "expected >=3 real-verb events, got %r" % (got,)


def test_wordnet_first_synset_miscategorises_catch_bite_slain():
    """A NAMED ceiling: WordNet's first-synset order sorts catch/bite/slain as
    nouns/adjectives, not events -- so these eventive real verbs do NOT drive
    events. Reported, not tuned away."""
    for w in ("catch", "bite", "slain"):
        n, ln, cat = jw._wn_audit(w)
        assert n >= 1, "%r unexpectedly OOV" % w
        assert cat != "event", "%r unexpectedly categorised as event (%s)" % (w, ln)


# --------------------------------------------------------------------------- #
#  LAYER 3 -- THE ARC (the headline): the hero's-journey does NOT cohere.
#  CEILING = PARSE (inverted verse), NOT the nonsense.
# --------------------------------------------------------------------------- #
def test_hero_is_licensed_as_the_metrically_prominent_agent_not_mimsy(rec):
    """DELIBERATE, REVIEWED UPDATE (M2 — the METER/PARSE PINCER). The original
    summit ledger recorded the hero FRAGMENTED across ~7 spurious entities, the
    most salient of which was the recency artefact 'mimsy' (a pronoun-only hero
    has no proper-noun anchor, so the flat salience ranking mislabelled it). The
    named residual was: 'the meter track licenses the hero over the salient-but-
    wrong antecedent.' That pincer has now landed.

    coref_entities.py carries a graph-native METRICAL-PROMINENCE factor in the
    antecedent Argmax: in a VERSE text the metrically-prominent agent (the
    subject of a clause whose action verb sits on the strong beat) is licensed as
    the protagonist, so every hero pronoun ('He took his vorpal sword', 'He left
    it dead', 'He chortled in his joy') binds to ONE persistent hero entity
    labelled 'he' -- the metrically-prominent agent -- instead of 'mimsy'. The
    licensing is gated to verse (newline-delimited, metrically confident); the
    crow (prose) is byte-identical (test_crow_gate + test_meter_predicts).

    WHAT LANDED: the unified hero is now the arc entity 'he' (carrying setup +
    the took/left actions), and 'mimsy' is NO LONGER an arc entity -- the
    mislabel is fixed. WHAT STILL CEILS (honest partial): no entity yet carries a
    FULL setup->problem->solution->resolution role set -- the inverted verse
    still scatters the middle roles across the parse, so role COMPLETENESS
    remains a parse ceiling. The pincer fixes the LABEL (the salient-but-wrong
    antecedent), not the whole story grammar."""
    ad = rec["ad"]
    arcs = rd._narrative_arc_from_graph(ad)["arcs"]
    full = 0
    for a in arcs:
        role_set = {r.get("role") for r in a["roles"] if r.get("role")}
        if {"setup", "problem", "solution", "resolution"} <= role_set:
            full += 1
    # the role-COMPLETENESS ceiling is unchanged (honest partial: the pincer
    # fixes the hero LABEL, not the inverted-verse role scatter).
    assert full == 0, "an arc unexpectedly cohered: %r" % (
        [(a["entity"], sorted({r.get("role") for r in a["roles"] if r.get("role")}))
         for a in arcs],)
    entities = {a["entity"] for a in arcs}
    # the hero is now LICENSED under 'he' (the metrically-prominent agent) and
    # 'mimsy' (the salient-but-wrong first-antecedent) is no longer the hero.
    assert "he" in entities, \
        "the metrically-prominent hero 'he' was not licensed as an arc entity: %r" % entities
    assert "mimsy" not in entities, \
        "the recency artefact 'mimsy' is still an arc entity (licensing failed): %r" % entities
    # the 'he' hero carries the defining hero ACTION roles (took / left), not a
    # bare setup fragment -- it is the unified protagonist, not a scatter shard.
    he_arc = next(a for a in arcs if a["entity"] == "he")
    he_roles = {r.get("role") for r in he_arc["roles"] if r.get("role")}
    assert "action" in he_roles, "the licensed hero carries no action role: %r" % he_roles


# --------------------------------------------------------------------------- #
#  LAYER 4 -- TROPE / THEME -- honest null (no arc -> nothing to decode).
# --------------------------------------------------------------------------- #
def test_trope_and_theme_are_an_honest_null(rec):
    ad = rec["ad"]
    results = rd._trope_theme_from_graph(ad)["results"]
    fired = [t for r in results for t in (r.get("tropes") or [])]
    assert not fired, "unexpected trope fired on the poem: %r" % fired


# --------------------------------------------------------------------------- #
#  LAYER 5 -- ANALYSIS + verify_grounding -- the anti-hallucination gate HOLDS.
# --------------------------------------------------------------------------- #
def test_analysis_is_empty_and_grounding_gate_holds(rec):
    """With no groundable arc the produce stages stay pending: ZERO Claim nodes,
    an EMPTY analysis, and verify_grounding ok (nothing emitted -> nothing
    ungrounded). The reader REFUSES to fabricate an analysis on this hard verse."""
    agent, bb = rec["agent"], rec["bb"]
    assert len(agent.s.nodes("Claim")) == 0, "unexpected Claim nodes minted"
    analysis = jw._analysis_from_bb(agent, bb)
    assert analysis["text"] == "", "expected empty (refused) analysis prose"
    assert analysis["produced_count"] == 0 and analysis["framed_count"] == 0
    grounding = la.verify_grounding(agent, analysis)
    assert grounding["ok"], "grounding gate failed: %r" % grounding["unresolved"][:5]
    assert grounding["checked"] == 0, "expected nothing to check on an empty analysis"


# --------------------------------------------------------------------------- #
#  LAYER 6 -- THE FRAME (identical open/close stanza) -- not recognised.
# --------------------------------------------------------------------------- #
def test_frame_return_is_not_recognised(rec):
    """Honest gap: the poem opens and closes with the identical 'brillig' stanza,
    but nothing mints a return-to-frame / repeated-material / nesting signal."""
    agent = rec["agent"]
    for t in ("StoryBoundary", "RepeatedMaterial", "StoryUnit"):
        assert len(agent.s.nodes(t)) == 0, "unexpected %s node (frame recognised?)" % t


# --------------------------------------------------------------------------- #
#  NO TUNING -- the summit is the script + this test only; no domain/seed edit.
# --------------------------------------------------------------------------- #
def test_no_poem_token_is_hardcoded_in_the_reader_or_analysis_modules():
    """No distinctive Jabberwocky token appears as a literal in the reader /
    analysis / trope / narrative modules -- the stack was NOT edited to fit the
    poem (the summit adds only a script and this test)."""
    from domains import comprehension_reader as cr
    from domains import narrative_structure as ns
    from domains import trope_theme as tt
    # distinctive CONTENT tokens of the poem. NB 'jabberwock' is excluded: it is
    # the AGENT'S OWN NAME and appears in docstrings across the codebase -- it is
    # not evidence of tuning to this poem.
    tokens = ("brillig", "slithy", "borogoves", "galumphing", "vorpal",
              "bandersnatch", "frabjous", "manxome", "tulgey", "mimsy")
    for mod in (rd, la, cr, ns, tt):
        src = inspect.getsource(mod).lower()
        for tok in tokens:
            assert tok not in src, "poem token %r hardcoded in %s" % (tok, mod.__name__)


def test_donkey_zero_no_regex_no_llm_no_git_in_summit():
    """donkey = 0 (no LLM), no `import re`, no `git` -- in the summit script."""
    src = inspect.getsource(jw)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re in the summit"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import in the summit"
    low = src.lower()
    for banned in ("openai", "anthropic", "requests.post", "call_model",
                   "subprocess", "os.system", '"git ', "'git ", "git stash",
                   "git commit", "self_teacher"):
        assert banned not in low, "banned token %r in the summit" % banned


def test_summit_script_runs_end_to_end():
    """The summit driver runs the whole poem end-to-end and returns the record."""
    out = jw.read_jabberwocky()
    assert out["agent"] is not None and "bb" in out
