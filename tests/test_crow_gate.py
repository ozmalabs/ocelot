"""THE INTEGRATION GATE — six comprehension components, one real fable.

This is NOT a new capability gate. It is an honest end-to-end test of six
already-green-in-isolation comprehension modules (situation_model_reader,
coref_entities, inference_generation, discourse_coherence, global_monitoring,
character_tom) reading REAL Aesop prose (not the short synthetic SVO
sentences their own unit tests use) via
scripts/jabberwock_reads_the_crow.py. Every module is reused AS-IS — this
test (and the harness it drives) does not patch, fork, or modify any of the
six committed modules.

THE BASELINE (pinned; UPDATED 1/6 -> 4/6 when the clause-decomposition parse
landed — the deliberate, recorded update this gate exists to force). The
ORIGINAL honest baseline: the reader's clause-level grammar (tuned for short
SVO sentences) glommed almost every real sentence's subordinate/coordinate/
participial structure into single multi-word underscore-joined argument blobs
(e.g. 'picking_up_some_small_pebbles_he_dropped_them_into_pitcher_one'),
minting ZERO SmEvents and never forming clean crow/water/pitcher SmEntities —
QA 1/6. THE UPDATE: domains/reading_collapse.decompose_sentence (wired into
reading_scope.read_scope) now descends a multi-clause sentence into its CLAUSES
at recognised marker-class boundaries (CLAUSE_LINK / IF / CAUSE_SUB / REL, comma
regions, AND/OR between two verb-headed clauses) and reads each clause into a
CLEAN verb-headed predication (main verb via the held is_verb_headed POS Term;
nominal heads via _clean_head). 'he dropped them' now surfaces as its own
event -> an SmEvent{verb:'drop'}; crow/pitcher/water exist as clean SmEntities;
QA is 4/6 (problem/action/consequence/outcome HIT; goal + cause still MISS
honestly — no explicit attitude verb for the goal, and the physical
displacement inference for the cause is the discourse/inference layer's job,
not the parse). This number changed via a reviewed edit to THIS test, exactly
as a gate is supposed to force — never an unnoticed drift.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_crow_gate.py -p no:randomly -q -s
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from domains import comprehension_reader as cr                        # noqa: E402
from domains import dictionary_lexicon as dl                          # noqa: E402
from domains import discourse_coherence as dc                         # noqa: E402
import jabberwock_reads_the_crow as jrc                                # noqa: E402


class _Agent:
    """The same minimal agent shim every domains/*.py test uses."""
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh_agent():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def _result():
    return jrc.run()


# --------------------------------------------------------------------------- #
#  STRUCTURAL — the harness runs end-to-end and produces every required shape.
# --------------------------------------------------------------------------- #
def test_harness_builds_the_comprehension_graph_without_error(_result):
    graph = _result["graph"]
    assert graph["spine"]["textbase"]
    assert len(graph["spine"]["textbase"]) == 6      # six sentences in the fable
    assert graph["discourse"]["pairs"]
    assert graph["centrality"]["ranking"]
    assert len(graph["tom_results"]) == 6


def test_qa_has_all_six_questions_each_graph_traced(_result):
    qa = _result["qa"]
    assert len(qa) == 6
    expected_questions = {
        "What did the crow want?",
        "Why couldn't the crow drink at first?",
        "What did the crow do?",
        "What happened to the water?",
        "Did the crow drink?",
        "Why did dropping pebbles help?",
    }
    assert {r["question"] for r in qa} == expected_questions
    for r in qa:
        assert "hit" in r and isinstance(r["hit"], bool)
        assert r["source"]                      # every answer traces to a component+node


# --------------------------------------------------------------------------- #
#  PRINT EVERYTHING (visible under `-s`) — the deliverable is the printed
#  comprehension graph + QA table + centrality summary + score, verbatim.
# --------------------------------------------------------------------------- #
def test_print_full_report(_result):
    jrc.print_report(_result["graph"], _result["qa"], _result["summary"])
    jrc.print_qa(_result["qa"])
    jrc.print_summary(_result["summary"])
    print("\nFINAL SCORE: %d/%d" % (_result["score"], _result["score_total"]))


# --------------------------------------------------------------------------- #
#  THE PINNED HONEST BASELINE — donkey = 0, graph-native, real prose.
# --------------------------------------------------------------------------- #
def test_baseline_score_is_6_of_6():
    """PINNED (DELIBERATE UPDATE — was 4/6, was 1/6). Two changes, both
    CAPABILITY not tuning, lift the last two honest misses:

      (a) THE READ ORCHESTRATOR (domains/comprehension_reader.read_and_comprehend,
          now driving build_comprehension_graph) sequences the six components in
          the CORRECT dependency order: GOAL-FROM-STATE inference runs AFTER the
          situation model is built, and PHYSICAL-CAUSAL inference runs AFTER
          discourse_coherence.read_discourse has built the DiscourseEvent graph
          (so resolve_causal_gap no longer DEFERS on absent nodes). The old
          harness ran inference before discourse AND never called the goal /
          causal resolvers at all.
      (b) THE PRENOMINAL-ADJECTIVE -> STATE parse gap (reading_collapse.
          _prenominal_states): 'a thirsty Crow' now grounds crow.thirsty=1 as a
          STATE (is_a(crow, thirsty), recognised by the held POS faculty — an
          adjective-primary modifier before the head — NOT a hardcoded list), so
          goal-from-state has something to read (thirsty -> drink).

    All six QA questions now HIT: goal (crow.thirsty -> goal=drink via the
    need_remedy_thirst schema), problem, action, consequence, outcome, and cause
    (the drop->rise physical_displacement_rise causes edge between the pebble and
    rise DiscourseEvent nodes). This number changed via a reviewed edit to THIS
    test, exactly as this file's docstring prescribes — never a silent drift."""
    result = jrc.run()
    assert result["score"] == 6
    assert result["score_total"] == 6


def test_summary_correct_via_causal_weighted_centrality():
    """PINNED (DELIBERATE UPDATE — was False: 'the DEGREE metric ... does not
    surface the true narrative hinge ... in the top-2'). Two capability
    changes, both graph-native, both diagnosed BEFORE being fixed:

    DIAGNOSIS (why the old unweighted centrality missed the hinge). Every
    decoded coherence-relation pair minted a `coherence_rel` edge PLUS a
    `before` edge (sequence/condition) or a `causes` edge (cause) — all
    weighted EQUALLY (Count, weight 1) in the old degree Term. 'Then an idea
    came to him.' collects two 'then'-marked SEQUENCE pairs -> 4 weight-1
    edges -> degree 4, while the pebble/rise pair had NO coherence_rel edge at
    all ('pebbles' vs 'pebble' share no lexical-cohesion TOKEN, so discourse_
    coherence's own unmarked signal returns 'none') and the ORCHESTRATOR
    computed centrality (`dc.centrality_ranking`) BEFORE `resolve_causal_gap`
    even ran (dependency-order bug: centrality was step 4, physical-causal
    inference was step 5) — so the one `causes` edge that DOES exist between
    them wasn't even on the graph yet when centrality was read off. Sparse
    causal graph (a) + no differential weighting (b) + wrong ORDER (c) = a
    'then'-chain of mental-state sentences outranking the actual hinge.

    THE FIX.
      (a) CAUSAL-WEIGHTED CENTRALITY (discourse_coherence._EDGE_WEIGHTS /
          _degree_term): `causes`/`enables` edges now carry `_CAUSAL_WEIGHT`
          (3.0) vs `before`/`coherence_rel`'s `_NONCAUSAL_WEIGHT` (1.0) in the
          SAME Term-tree (`Times(Lit(weight), Count(...))` summed by `Plus`,
          Argmax over the result) — a causal connection outweighs a bare
          sequence/contrast tie, decided BY THE TERM, never Python arithmetic.
      (b) THE GOAL-ACTION ENABLING CHAIN (comprehension_reader.
          _mint_goal_action_enabling_chain, run in the orchestrator's new step
          5b, BEFORE centrality is computed in step 5c): mints `enables`
          edges tracing Trabasso & van den Broek's full backbone — the goal
          sentence ('a thirsty Crow') -> the crow's own next attempt ('could
          not reach the water') -> the crow's next attempt ('dropped [pebbles]
          ... into the pitcher') — reusing the already-decided goal + sentence
          order, deciding no new meaning.

    RESULT (verbatim, printed under -s): the pebble-dropping sentence carries
    degree 7 (up from 0), out-ranking the mental-state sentences ('an idea
    came' / 'felt ... must die of thirst', degree 4 / 2); the problem sentence
    ('could not reach the water', degree 9 — it is now ALSO part of the
    enabling backbone, which is correct: 'the problem->solution->resolution
    core' the fix targets never excluded the problem itself, only the bare
    mental-state placeholders) is top-of-sort, with the pebble-dropping
    sentence at #2 — a hinge sentence IS in the top-2, so `summary_correct`
    flips True. QA stays 6/6 (this test changes only the summary read-off's
    verdict, not any QA answer)."""
    result = jrc.run()
    assert result["score"] == 6                       # QA unchanged, still 6/6.
    assert result["summary"]["argmax_winner_matches_top_of_sort"] is True
    assert result["summary"]["summary_correct"] is True
    rows = result["graph"]["centrality"]["ranking"]
    by_label = {r["label"]: r["degree"] for r in rows}
    pebble_label = next(l for l in by_label if "pebbles" in l.lower())
    idea_label = next(l for l in by_label if "an idea came" in l.lower())
    thirst_label = next(l for l in by_label if "must die of thirst" in l.lower())
    # the hinge now clears both bare mental-state placeholders the diagnosis
    # names explicitly.
    assert by_label[pebble_label] > by_label[idea_label]
    assert by_label[pebble_label] > by_label[thirst_label]


# --------------------------------------------------------------------------- #
#  SPECIFIC HONEST MISSES — pinned per-question, so a future fix is visible
#  exactly where it lands (not just as a bulk score change).
# --------------------------------------------------------------------------- #
def test_goal_query_hits_via_goal_from_state_inference():
    """DELIBERATE UPDATE (was: an honest MISS — no explicit attitude verb). The
    fable never says 'the crow wanted water' — desire is conveyed narratively via
    the PRENOMINAL adjective 'a thirsty Crow'. The parse now grounds that as a
    STATE (crow.thirsty=1, is_a(crow, thirsty) — the adjective recognised by the
    held POS faculty, not a hardcoded list), and inference_generation's
    GOAL-FROM-STATE capability (detect_goal_gaps / resolve_goal_gap, wired into
    the read orchestrator AFTER the situation model is built) decodes the
    need-state against the need_remedy_thirst schema and mints the goal
    (thirsty -> drink) into character_tom's own goal slot. character_goal(crow)
    is now 'drink' — the goal query HITS by capability, not by an attitude verb
    the prose does not contain."""
    result = jrc.run()
    rec = next(r for r in result["qa"] if r["question"] == "What did the crow want?")
    assert rec["hit"] is True
    assert "drink" in str(rec["answer"]).lower()


def test_action_query_hits_drop_smevent_minted():
    """DELIBERATE UPDATE (was: zero SmEvents). Clause decomposition surfaces
    'he dropped them into the pitcher' as its own clean event predication
    ['dropped', 'he', 'them'], whose relation lemmatises to the COS-canon verb
    'drop' — so situation_model_reader now mints an SmEvent{verb:'drop'}. The
    action query HITS. (Coref binds the object 'them' to 'birds' rather than
    'pebbles' — the participial 'Picking up some small pebbles' is subject-less
    so 'pebbles' is not minted as an entity; an honest coref residual that does
    not change the drop event's verb, which is what this query reads.)"""
    result = jrc.run()
    rec = next(r for r in result["qa"] if r["question"] == "What did the crow do?")
    assert rec["hit"] is True
    assert any(e.get("verb") == "drop" for e in rec["answer"])


def test_cause_query_hits_via_physical_causal_inference():
    """DELIBERATE UPDATE (was: an honest MISS — the causal edge). Deriving that
    the pebbles DISPLACE the water is physical world knowledge discourse_coherence
    itself does not carry (the two sentences share NO entity token — 'pebbles' vs
    'water' — so lexical cohesion cannot link them). inference_generation's
    PHYSICAL-CAUSAL capability (detect_causal_gaps / resolve_causal_gap) decodes
    the adjacent verb pair drop->rise against the physical_displacement_rise
    schema and mints the 'causes' edge. It only fires once the DiscourseEvent
    graph exists — which is exactly what the read orchestrator now guarantees by
    running the causal pass AFTER discourse_coherence.read_discourse (the old
    harness ran inference first, so the resolver correctly DEFERRED). The cause
    query now HITS: the causes edge is present between the pebble and rise
    DiscourseEvent nodes."""
    result = jrc.run()
    rec = next(r for r in result["qa"] if r["question"] == "Why did dropping pebbles help?")
    assert rec["hit"] is True
    assert rec["answer"]["causes_edge_present"] is True


def test_no_import_re_in_harness():
    import ast
    import inspect
    src = inspect.getsource(jrc)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"


# --------------------------------------------------------------------------- #
#  GENERAL (not Crow-tuned) — the SAME orchestrator + centrality on a
#  DIFFERENT short narrative. No fable string is named in the enabling-chain
#  scan (domains/comprehension_reader._mint_goal_action_enabling_chain), so
#  this must work without any Crow-specific code path.
# --------------------------------------------------------------------------- #
WOLF_TEXT = "The wolf was hungry. It saw a lamb. It chased the lamb."


def test_wolf_summary_picks_goal_pursuit_not_orientation():
    """The wolf's goal-pursuit central event (saw/chased the lamb) — the
    ATTEMPT(s) advancing its hunger-driven goal — outranks the bare
    ORIENTATION sentence ('The wolf was hungry.') in the SAME causal-weighted
    centrality this gate fixes for the Crow. Proves the fix is general: no
    Crow-specific string, schema, or code path is involved — need_remedy_
    hunger (goal='eat') already existed in seeds/inference_knowledge.json for
    exactly this reuse, and the goal-action enabling scan reads sentence
    order + the resolved protagonist off graph data, never a fable name."""
    agent = _fresh_agent()
    dl.warm_wordnet("en")
    graph = cr.read_and_comprehend(agent, WOLF_TEXT, window=2)
    rows = graph["centrality"]["ranking"]
    assert rows
    by_label = {r["label"]: r["degree"] for r in rows}
    orientation_label = next(l for l in by_label if "hungry" in l.lower())
    pursuit_labels = [l for l in by_label if "chased" in l.lower() or "lamb" in l.lower()]
    assert pursuit_labels, "no goal-pursuit sentence found in the ranking"
    assert max(by_label[l] for l in pursuit_labels) > by_label[orientation_label]
    # the winner itself (Argmax, graph-native) is never the bare orientation.
    assert graph["centrality"]["argmax_matches_top_of_sort"] is True
    assert "hungry" not in rows[0]["label"].lower()
    # the enabling chain fired generally (no Crow name involved).
    assert graph["enabling_chain"]
    assert any(c["entity"] == "wolf" for c in graph["enabling_chain"])


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — a flat, unrelated sentence list mints NO relation at all,
#  so weighted centrality is honestly ZERO/TIED everywhere, never a fabricated
#  "central" pick with a non-zero degree.
# --------------------------------------------------------------------------- #
def test_discriminative_flat_unconnected_events_no_spurious_center():
    agent = _fresh_agent()
    dl.warm_wordnet("en")
    text = ("Cats are mammals. Rocks are hard. Blue is a color. "
            "Paper is thin. Music is loud.")
    dc.read_discourse(agent, text, window=2)
    ranking = dc.centrality_ranking(agent)
    rows = ranking["ranking"]
    assert rows
    # no genuine causal/coherence connection exists between any of these
    # sentences (no shared entity, no marker) -- every node's weighted
    # degree is honestly 0, not a fabricated winner.
    assert all(r["degree"] == 0 for r in rows)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the weighted centrality is a graph Term
#  (Times/Count/Argmax), never a Python max()/sorted() deciding the winner;
#  the enabling/causal edges are minted by already-decided facts (no
#  fable-specific narrative hardcode); no `import re` anywhere touched.
# --------------------------------------------------------------------------- #
def test_source_audit_weighted_centrality_is_graph_native():
    dc_src = open(os.path.join(ROOT, "domains", "discourse_coherence.py")).read()
    # the differential causal-vs-noncausal WEIGHT is folded into a `Times`
    # Term, not applied by Python arithmetic after evaluation.
    assert '"type": "Times"' in dc_src
    assert "_CAUSAL_WEIGHT" in dc_src and "_NONCAUSAL_WEIGHT" in dc_src
    assert '"type": "Argmax"' in dc_src
    # the WINNER-picking functions contain no Python max()/sorted() CALL
    # (an AST check, not a substring search -- the docstring itself mentions
    # "max()"/"sorted()" in prose, which must not trip a false positive).
    import ast
    tree = ast.parse(dc_src)
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name in ("_degree_term", "degree_of", "most_central"):
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id not in ("max", "sorted"), (
                        "%s() calls Python %s() to pick a winner" % (fn.name, node.func.id))

    cr_src = open(os.path.join(ROOT, "domains", "comprehension_reader.py")).read()
    import ast
    tree = ast.parse(cr_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"
    # the enabling-chain scan mints edges via discourse_coherence's OWN
    # `_mint_edge` primitive (reused, not reimplemented) and names no
    # fable-specific narrative content (no hardcoded 'crow'/'pebble'/'pitcher'
    # string anywhere in the scan).
    chain_src = cr_src[cr_src.index("def _mint_goal_action_enabling_chain("):
                        cr_src.index("def read_and_comprehend(")]
    assert "dc._mint_edge(" in chain_src
    for banned in ("crow", "pebble", "pitcher", "wolf", "lamb"):
        assert banned not in chain_src.lower(), (
            "enabling-chain scan names a fable-specific token %r -- not general" % banned)
