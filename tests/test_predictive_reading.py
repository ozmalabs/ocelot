"""test_predictive_reading — ANALYSIS-BY-SYNTHESIS READING: reading and writing are
ONE model run in opposite directions.

The reader SYNTHESIZES what the writer is about to write (the production faculty
run forward, conditioned on a graph-resident WriterStyle/AudienceCentroid + the
recurring Throughline beat + the discourse context), COMPARES it to the arriving
words (a ShapeDecode collapse), and the RESIDUAL is the comprehension signal.

Gated payoffs (both measured behind the SAME machinery):
  (a) FASTER — the recurring beat predicts arc 3 before reading it: high hit-rate,
      the residual is the SPECIFICS (child / family / lantern).
  (b) MORE ACCURATE FOR NON-TOKENISED TEXT — on the SAME noisy un-spaced input,
      prediction-guided recognition BEATS bottom-up segmentation alone.

GRAPH-NATIVE audit: the writer/audience model is graph-resident (WriterStyle /
AudienceCentroid nodes + relative_to edge); the compare/residual is a ShapeDecode
collapse (not a Python branch); driven by cognitive_tick; NO hardcoded expected
words; no import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_predictive_reading.py -p no:randomly -q -s
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
from domains import reading_collapse as rc                             # noqa: E402
from domains import reading_drive as rd                               # noqa: E402
from domains import predictive_reading as pr                          # noqa: E402
import jabberwock_reads_a_multiarc_story as jrms                       # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _v(x):
    return x.value if hasattr(x, "value") else x


@pytest.fixture(scope="module")
def built():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    out = rd.run_nested_reading_flow(ag, jrms.STORY)
    sents = rc._split_sentences(jrms.STORY)
    arcs = [" ".join(sents[c["span_start"]:c["span_end"] + 1]) for c in out["tree"]["children"]]
    beat = next((t["name"] for t in out["throughlines"] if t["kind"] == "pattern"), None)
    model = pr.build_writer_model(ag, arcs[:2], throughline_beat=beat)
    return ag, arcs, beat, model


# --------------------------------------------------------------------------- #
#  WRITER MODEL + AUDIENCE CENTROID — graph-resident, a point relative to class.
# --------------------------------------------------------------------------- #
def test_writer_model_and_centroid_are_graph_nodes(built):
    ag, _arcs, _beat, model = built
    # both are real graph nodes.
    assert ag.s.nodes("WriterStyle"), "no WriterStyle node minted"
    assert ag.s.nodes("AudienceCentroid"), "no AudienceCentroid node minted"
    # the WriterStyle is a POINT relative to the class centroid (relative_to edge).
    ws = model["writer_style"]
    rel = [_v(d) for d in ag.s.neighbours(ws, "relative_to")]
    assert _v(model["audience_centroid"]) in rel, "WriterStyle -relative_to-> centroid missing"
    # the centroid is the class register average.
    cen = ag.s.node(model["audience_centroid"])["attrs"]
    assert cen.get("genre") == "fable" and cen.get("audience") == "children"


def test_recurring_beat_harvested_not_hardcoded(built):
    ag, _arcs, beat, model = built
    ws = pr.read_writer_model(ag, model["writer_style"])
    # the recurring beat surface is HARVESTED from arcs 1-2 by cross-arc recurrence
    # (the writer's repeated phrasing) — it carries the throughline beat words.
    surface = ws["recurring_surface"]
    assert "thanked" in surface and "gave" in surface, "recurring beat not harvested"
    # the maximal recurring phrase is the verbatim repeated run.
    assert "thanked_her_and_gave_her_a" in ws["recurring_beats"]
    # the throughline beat (from throughlines.py) is carried on the model.
    assert ws["throughline_beat"] == beat == "thanked:her"


# --------------------------------------------------------------------------- #
#  (a) FASTER — the recurring beat predicts arc 3 BEFORE reading it.
# --------------------------------------------------------------------------- #
def test_beat_predicts_arc3_high_hit_rate(built):
    ag, arcs, _beat, model = built
    # predict arc 3 BEFORE reading it (no arc-3 context — the beat alone), tick-driven.
    res = pr.read_arc_predictively(ag, model["writer_style"], arcs[2], context="")
    assert res, "no PredictiveRead minted (tick-driven read produced nothing)"
    # the beat's recurring words materialise in arc 3 — a high prediction hit-rate.
    assert res["hit_rate"] >= 0.8, "the recurring beat failed to predict arc 3"


def test_confirm_vs_deep_split_residual_is_the_specifics(built):
    ag, arcs, _beat, model = built
    res = pr.read_predictive_reads(ag, target=arcs[2])
    assert res, "no PredictiveRead for arc 3"
    confirmed, surprise = res["confirmed"], res["surprise"]
    # a real split: some fast-confirmed, some deep-processed.
    assert confirmed and surprise, "expected both a confirmed and a surprise set"
    # the recurring beat CONFIRMS its recurring words (fast).
    for w in ("thanked", "gave", "met"):
        assert w in confirmed, "the recurring beat word %r was not confirmed" % w
    # the RESIDUAL is the arc's SPECIFICS (the surprise SHOULD be the residual).
    for w in ("child", "family", "lantern"):
        assert w in surprise, "the specific %r should be in the residual (surprise)" % w
    # the confirm split is a genuine fraction (not all-or-nothing).
    assert 0.0 < res["confirm_frac"] < 1.0


def test_residual_is_the_shapedecode_collapse_not_a_python_branch(built):
    ag, arcs, _beat, model = built
    # abs_compare's surprise IS the ShapeDecode residual: re-run the compare and check
    # the surprise words are exactly the words no prediction covered.
    pred = pr.predict_next_words(ag, model["writer_style"], context="")["predicted_words"]
    cmp = pr.abs_compare(ag, pred, pr._words(ag, arcs[2]))
    # every surprise word is NOT among the predicted (the collapse left it in residual);
    # every confirmed word IS predicted (the collapse covered it).
    pset = set(pred)
    assert all(w not in pset for w in cmp["surprise"])
    assert all(w in pset for w in cmp["confirmed"])
    # source audit: the compare is a ShapeDecode Term, residual read off the decode.
    src = inspect.getsource(pr._decode_actual_against_prediction)
    assert '"type": "ShapeDecode"' in src
    assert "codebook_type" in src
    assert 'res.get("residual")' in inspect.getsource(pr.abs_compare)


# --------------------------------------------------------------------------- #
#  (b) MORE ACCURATE FOR NON-TOKENISED TEXT — prediction beats bottom-up.
# --------------------------------------------------------------------------- #
def test_prediction_disambiguates_nontokenised_beats_bottom_up(built):
    ag, arcs, _beat, model = built
    cases = [
        ("On the road she met a starving dog.", "thedogthankedher",
         ["the", "dog", "thanked", "her"]),
        ("The next day she met a shivering bird.", "thebirdthankedher",
         ["the", "bird", "thanked", "her"]),
    ]
    bu_accs, pg_accs = [], []
    for ctx, noisy, truth in cases:
        predicted = pr.predict_next_words(ag, model["writer_style"], context=ctx)["predicted_words"]
        bu = pr.bottom_up_segment(ag, noisy)
        pg = pr.prediction_guided_segment(ag, predicted, noisy)
        a_bu = pr.segmentation_accuracy(bu, truth)
        a_pg = pr.segmentation_accuracy(pg, truth)
        bu_accs.append(a_bu)
        pg_accs.append(a_pg)
        # per-case: prediction-guided recovers the truth exactly; bottom-up does not.
        assert a_pg == 1.0, "prediction-guided failed to recover %r" % noisy
        assert a_pg > a_bu, "prediction-guided did not beat bottom-up on %r" % noisy
    mbu = sum(bu_accs) / len(bu_accs)
    mpg = sum(pg_accs) / len(pg_accs)
    # the categorical jump: bottom-up ~0%, prediction-guided 100%.
    assert mpg == 1.0
    assert mpg > mbu
    assert mbu < 0.5, "bottom-up unexpectedly strong on un-spaced input"


def test_same_decoder_only_lexicon_differs(built):
    # the two arms use the SAME held lattice decoder; only the LEXICON differs (the
    # prediction bias) — not two different algorithms.
    for fn in (pr.bottom_up_segment, pr.prediction_guided_segment):
        src = inspect.getsource(fn)
        assert "_lattice_decode" in src, "%s must use the held lattice decoder" % fn.__name__


# --------------------------------------------------------------------------- #
#  DRIVEN BY cognitive_tick — no hand-pump, one stage per reflex firing.
# --------------------------------------------------------------------------- #
def test_driven_by_cognitive_tick_no_hand_pump():
    drv = inspect.getsource(pr.read_arc_predictively)
    assert "cognitive_tick(" in drv, "the read must be driven by cognitive_tick"
    assert "run_rules(" not in drv and "fire_reflexes(" not in drv, "no hand-pump allowed"
    assert "recognize_throughlines" not in drv
    # the reflex RESPONSE advances ONE stage per firing (a return inside the one loop).
    adv = pr._advance_predictive_stage
    tree = ast.parse(inspect.getsource(adv))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
    # one stage-scan loop (an inner loop resolves the WriterStyle node id).
    scan = next(l for l in loops
                if any("PredictiveReadingStage" in ast.dump(c) for c in ast.walk(l)))
    assert any(isinstance(n, ast.Return) for n in ast.walk(scan))


def test_stage_dispatched_and_done(built):
    ag, arcs, _beat, model = built
    stages = {(ag.s.node(n)["attrs"].get("name")): ag.s.node(n)["attrs"].get("status")
              for n in ag.s.nodes("PredictiveReadingStage")}
    assert stages.get("predict_read") == "done", "the predictive stage did not settle done"


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — no hardcoded story words; no regex; donkey = 0.
# --------------------------------------------------------------------------- #
def _docstring_node_ids(tree) -> set:
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def test_no_hardcoded_story_words_in_module():
    # the module must not name the story's specific content IN EXECUTABLE CODE — the
    # predicted words are HARVESTED from the graph, never literal-listed. Docstrings
    # (which cite the 'thebirdthankedher' EXAMPLE) are documentation, excluded.
    tree = ast.parse(inspect.getsource(pr))
    docs = _docstring_node_ids(tree)
    code_strings = [c.value.lower() for c in ast.walk(tree)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                    and id(c) not in docs]
    banned = {"mira", "bird", "dog", "whistle", "feather", "lantern", "castle",
              "child", "fortune", "thanked", "gave"}
    for lit in code_strings:
        # word-level membership (so 'children' the audience class is not a hit on 'child').
        words = set("".join(ch if ch.isalpha() else " " for ch in lit).split())
        hit = words & banned
        assert not hit, "hardcoded story literal(s) %s found in code string %r" % (hit, lit)


def test_source_audit_no_regex_no_donkey():
    src = inspect.getsource(pr)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re found"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... found"
    for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
        assert banned not in src, "donkey token %r found" % banned
