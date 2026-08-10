"""test_throughlines — A THROUGHLINE is a PERSISTENT thread woven through N (3+)
arcs of a multi-arc story, one level up from nested_reading's SPANNING THEME (a
single cross-episode relation between TWO units).

The test story (four arcs: dog / bird / child helping arcs + castle PAYOFF arc)
carries deliberate throughlines:

  * MIRA — the recurring PROTAGONIST across every arc (kind:character). Verbatim
    the spans_unit edges to all four arcs.
  * the help->thank recurring BEAT across arcs 1-3 (kind:pattern).
  * the whole-story META-THEME the threads compose into.

HONEST LEDGER (recorded in the asserts): the CHARACTER + PATTERN throughlines
LAND; the PAYOFF throughline is PARSE-BLIND (the conjoined gift clause '...thanked
her AND gave her a whistle' drops the gift in arcs 1-3, so the whistle/feather/
lantern appear ONLY in the payoff arc -- no early->late object link forms). The
composed meta-theme is therefore 'recurring kindness' (character + pattern); a
SYNTHETIC test proves that WITH a payoff throughline present the SAME compose
collapses to 'kindness returned' -- the mechanism is complete, the gap is parse
recall.

GRAPH-NATIVE: each throughline is a cross-unit ShapeDecode verdict + a Throughline
node with spans_unit edges; NO Python per-unit loop decides a throughline; no
import re; donkey = 0; driven by cognitive_tick.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_throughlines.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import reading_drive as rd                               # noqa: E402
from domains import throughlines as thr                               # noqa: E402
import jabberwock_reads_a_multiarc_story as jrms                       # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _v(x):
    return x.value if hasattr(x, "value") else x


@pytest.fixture(scope="module")
def read():
    dl.warm_wordnet("en")
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, jrms.STORY)
    return ag, out


# --------------------------------------------------------------------------- #
#  THE 4-ARC TREE — the boundaries fire (temporal-shift markers).
# --------------------------------------------------------------------------- #
def test_story_tree_has_four_arcs(read):
    _, out = read
    assert out["depth"] == 2
    assert len(out["units"]) == 4, "the 4-arc boundaries did not all fire"
    kids = out["tree"]["children"]
    signals = [c["boundary_signal"] for c in kids]
    # arc 1 opens the story; arcs 2-4 open on a recognised temporal-shift marker
    # ('The next day' / 'Later' / 'At last').
    assert signals[0] == "story_start"
    assert signals[1:] == ["temporal_shift", "temporal_shift", "temporal_shift"]


# --------------------------------------------------------------------------- #
#  MIRA — the recurring-protagonist throughline (the PRIMARY throughline).
# --------------------------------------------------------------------------- #
def test_recurring_protagonist_throughline_spans_all_arcs(read):
    ag, out = read
    chars = [t for t in out["throughlines"] if t["kind"] == "character"]
    assert len(chars) == 1, "expected exactly one recurring-protagonist throughline"
    mira = chars[0]
    # Mira threads ALL FOUR arcs (the coref-reference 'she' recurs as the actor of
    # every arc -- unit-scoping made the per-arc occurrences distinct; the
    # throughline re-links them).
    unit_ids = [u["unit"] for u in out["units"]]
    assert sorted(mira["spans"]) == sorted(unit_ids)
    assert len(mira["spans"]) == 4
    # VERBATIM the spans_unit edges (a real graph edge to each arc, not just an attr).
    tn = next(n for n in ag.s.nodes("Throughline")
              if _v(n) == mira["node"])
    edge_units = sorted(_v(d) for d in ag.s.neighbours(tn, "spans_unit"))
    assert edge_units == sorted(unit_ids), "spans_unit edges must reach every arc"
    # VERBATIM the codebook line (the throughline read off the tree, the decode's
    # own verdict).
    assert mira["line"] == (
        "A recurring protagonist -- the same character acts across every arc of "
        "the story. Unit-scoping made the per-arc occurrences DISTINCT graph "
        "nodes; the throughline re-links them into one thread. The primary "
        "throughline: it is the character whose returning presence makes the "
        "separate arcs one story.")


def test_recurring_protagonist_reused_coref_reference_not_proper_name(read):
    # HONEST finding: the protagonist thread is the coref-reference 'she' (not the
    # proper name 'Mira') -- the SVO parse gloms 'Mira left home ...' into a clause
    # fragment, so 'Mira' does not recur cleanly as an actor; 'she' does, in every
    # arc. The throughline rides the coref surface, no new mechanism needed.
    _, out = read
    mira = next(t for t in out["throughlines"] if t["kind"] == "character")
    assert mira["name"] == "she"


# --------------------------------------------------------------------------- #
#  THE RECURRING BEAT — help->thank across arcs 1-3 (kind:pattern).
# --------------------------------------------------------------------------- #
def test_recurring_beat_throughline_spans_arcs_1_to_3(read):
    ag, out = read
    beats = [t for t in out["throughlines"] if t["kind"] == "pattern"]
    by_name = {b["name"]: b for b in beats}
    # the help->thank beat: a helper THANKS the protagonist, arc after arc -- the
    # three helping arcs (dog/bird/child), NOT the payoff arc.
    assert "thanked:her" in by_name, "the help->thank beat did not thread"
    beat = by_name["thanked:her"]
    assert len(beat["spans"]) == 3
    unit_ids = [u["unit"] for u in out["units"]]
    assert beat["spans"] == unit_ids[:3]        # arcs 1-3 in span order
    # spans_unit edges reach the three helping arcs.
    tn = next(n for n in ag.s.nodes("Throughline") if _v(n) == beat["node"])
    edge_units = sorted(_v(d) for d in ag.s.neighbours(tn, "spans_unit"))
    assert edge_units == sorted(unit_ids[:3])
    # CONJOINED-VP RECALL (2026-07-07): the gift clause '...thanked her AND gave her a
    # whistle' now KEEPS the second conjunct (shared subject + ditransitive theme), so
    # the give->recipient beat 'gave:her' ALSO threads arcs 1-3 -- the recovered second
    # VP, not the parse-blind drop it used to be.
    assert "gave:her" in by_name, "the recovered gave beat did not thread"
    assert by_name["gave:her"]["spans"] == unit_ids[:3]


# --------------------------------------------------------------------------- #
#  THE PAYOFF — NOW LANDS: conjoined-VP recall keeps the gift clause (2026-07-07).
# --------------------------------------------------------------------------- #
def test_payoff_throughline_lands_via_conjoined_vp_recall(read):
    _, out = read
    payoffs = [t for t in out["throughlines"] if t["kind"] == "payoff"]
    # THE FIX: '...thanked her AND gave her a whistle' now recovers the dropped second
    # conjunct -- the shared subject binds ('gave her a whistle' shares 'the dog') and
    # the ditransitive THEME (whistle) surfaces as its own binary predication, so the
    # gift registers as a UnitAction patient in arcs 1-3. The gifts are then used in
    # the payoff arc ('She blew the whistle' / waved the feather / raised the lantern),
    # closing the early->late loop -> a payoff throughline PER gift.
    names = {t["name"] for t in payoffs}
    assert {"whistle", "feather", "lantern"} <= names, (
        "the gift payoff throughlines did not all form -- got %s" % sorted(names))
    unit_ids = [u["unit"] for u in out["units"]]
    payoff_arc = unit_ids[3]
    # each gift is introduced in its own helping arc and used again in the payoff arc.
    for gift, intro_arc in (("whistle", unit_ids[0]), ("feather", unit_ids[1]),
                            ("lantern", unit_ids[2])):
        t = next(t for t in payoffs if t["name"] == gift)
        assert intro_arc in t["spans"] and payoff_arc in t["spans"]


def test_payoff_mechanism_is_complete_synthetic_proof():
    # SYNTHETIC: inject a payoff throughline and re-compose -- the SAME compose
    # collapses the full set {character, pattern, payoff} to 'kindness returned'.
    # This proves the payoff->theme path is wired; the real story only misses it
    # because the parser drops the gift clause (measured above).
    ag = _fresh()
    thr.ensure_codebook(ag)
    root = ag.s.add_node("StoryUnit", {"kind": "root", "span_start": 0, "span_end": 3})
    thr._mint_throughline(ag, root, "character", "she", "RECURRING_CHARACTER", "-", [_v(root)])
    thr._mint_throughline(ag, root, "pattern", "thanked:her", "RECURRING_BEAT", "-", [_v(root)])
    partial = thr.compose_meta_theme(ag, root)
    assert partial["theme"] == "recurring kindness" and partial["token"] == "CHAR_BEAT"
    # now add the payoff thread and recompose.
    for m in list(ag.s.nodes("MetaTheme")):
        ag.inner.remove_node(m)
    thr._mint_throughline(ag, root, "payoff", "whistle", "CAUSAL_PAYOFF", "-", [_v(root)])
    full = thr.compose_meta_theme(ag, root)
    assert full["token"] == "CHAR_BEAT_PAYOFF"
    assert full["theme"] == "kindness returned"


# --------------------------------------------------------------------------- #
#  THE COMPOSED META-THEME — the whole-story theme threading the arcs.
# --------------------------------------------------------------------------- #
def test_meta_theme_composes_from_the_throughlines(read):
    ag, out = read
    mt = out["meta_theme"]
    assert mt is not None, "the root composed no meta-theme"
    # the verdict for THIS story now that conjoined-VP recall keeps the gift clause:
    # character + pattern + payoff ALL thread -> 'kindness returned' (the synthetic
    # proof made real). Before the fix the payoff was parse-blind -> 'recurring kindness'.
    assert mt["token"] == "CHAR_BEAT_PAYOFF"
    assert sorted(mt["kinds"]) == ["character", "pattern", "payoff"]
    assert mt["theme"] == "kindness returned"
    # VERBATIM the composed line.
    assert mt["line"] == (
        "A recurring protagonist enacts a recurring kindness across the arcs, and "
        "every kindness given returns to her in the final arc -- the gifts earned by "
        "the early arcs pay off at the climax. The whole-story theme, invisible in "
        "any single arc: kindness returned.")
    # minted on the ROOT, threaded to the throughlines (threads_throughline edges).
    root = next(r for r in ag.s.nodes("StoryUnit")
                if ag.s.node(r)["attrs"].get("kind") == "root")
    hm = [_v(d) for d in ag.s.neighbours(root, "has_meta_theme")]
    assert len(hm) == 1
    mtn = next(n for n in ag.s.nodes("MetaTheme") if _v(n) == mt["node"])
    threaded = [_v(d) for d in ag.s.neighbours(mtn, "threads_throughline")]
    assert len(threaded) >= 3                    # character + pattern(s) + payoff(s)


def test_meta_theme_is_the_shapedecode_verdict():
    ag = _fresh()
    thr.ensure_codebook(ag)
    assert thr.decode_meta_theme(ag, "CHAR_BEAT")["theme"] == "recurring kindness"
    assert thr.decode_meta_theme(ag, "CHAR_BEAT_PAYOFF")["theme"] == "kindness returned"
    null = thr.decode_meta_theme(ag, "META_NONE")
    assert null["theme"] is None and null["shape_fit"] == 0
    # and the per-thread decode.
    assert thr.decode_throughline(ag, "RECURRING_CHARACTER")["kind"] == "character"
    assert thr.decode_throughline(ag, "RECURRING_BEAT")["kind"] == "pattern"
    assert thr.decode_throughline(ag, "CAUSAL_PAYOFF")["kind"] == "payoff"
    assert thr.decode_throughline(ag, "NOPE")["kind"] is None


# --------------------------------------------------------------------------- #
#  PER-UNIT DISPATCH — the throughline + meta stages are seeded rule-dispatched.
# --------------------------------------------------------------------------- #
def test_throughline_and_meta_stages_dispatched_and_done(read):
    ag, _ = read
    stages = {(ag.s.node(n)["attrs"].get("name")): ag.s.node(n)["attrs"].get("status")
              for n in ag.s.nodes("AnalysisStage")}
    assert stages.get("throughline") == "done"
    assert stages.get("meta_theme") == "done"


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT — the throughline is a cross-unit ShapeDecode collapse, NOT
#  a Python per-unit loop deciding it; no regex; donkey = 0.
# --------------------------------------------------------------------------- #
def test_throughline_is_shapedecode_verdict_not_python_naming():
    tsrc = inspect.getsource(thr)
    # the decision is the ShapeDecode Term, read off reading_collapse._winner.
    assert '"type": "ShapeDecode"' in tsrc
    assert "rc._winner(" in tsrc
    # the token builders never NAME the kind/theme -- those come from the decoded
    # schema's own `kind`/`theme` attr (via _schema_attr). Assert no builder returns
    # a verdict string as a constant.
    for fn_name in ("_character_candidates", "_beat_candidates", "_payoff_candidates",
                    "_meta_token"):
        fn = next(n for n in ast.walk(ast.parse(tsrc))
                  if isinstance(n, ast.FunctionDef) and n.name == fn_name)
        strs = {c.value for r in ast.walk(fn) if isinstance(r, ast.Return)
                for c in ast.walk(r) if isinstance(c, ast.Constant)
                and isinstance(c.value, str)}
        for verdict in ("character", "pattern", "payoff", "recurring kindness",
                        "kindness returned"):
            assert verdict not in strs, (
                "%s returns the verdict %r -- the throughline kind/theme must be "
                "the decode's, not a Python assignment" % (fn_name, verdict))


def test_no_python_per_unit_loop_deciding_the_throughline():
    # the DRIVER mints the throughline/meta stages + pumps; it NEVER recognizes a
    # throughline itself (that is the reflex firing per rule-dispatched stage).
    drv = inspect.getsource(rd.run_nested_reading_flow)
    assert "recognize_throughlines" not in drv and "compose_meta_theme" not in drv
    assert "_tick_reading(" in drv
    assert "run_rules(" not in drv and "fire_reflexes(" not in drv
    # the reflex RESPONSE advances ONE stage per firing (a return inside the loop).
    adv = rd._advance_unit_stage
    tree = ast.parse(inspect.getsource(adv))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
    assert len(loops) == 1, "expected exactly one stage-scan loop in the reflex"
    assert any(isinstance(n, ast.Return) for n in ast.walk(loops[0]))


def test_source_audit_no_regex_no_donkey():
    src = inspect.getsource(thr)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re found"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... found"
    for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
        assert banned not in src, "donkey token %r found" % banned
