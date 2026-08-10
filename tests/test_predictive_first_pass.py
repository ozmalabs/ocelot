"""test_predictive_first_pass — THE WHOLE FIRST PASS IS PREDICTION.

Lifts the AbS capstone from ONE arc to the WHOLE TEXT: as the reader streams a
fable sentence by sentence, at EACH sentence the ACCUMULATING writer/audience/
context model PREDICTS the next sentence's words BEFORE reading them (the
production faculty forward), the arriving sentence is DECODED against the
prediction (the AbS ShapeDecode collapse — the `residual` IS the surprise), and
the predicted words FAST-CONFIRM while the residual is the NEWS.

Gated claims (all behind protected controls):
  * PER-SENTENCE + AGGREGATE — a real confirm-vs-deep split across the whole text;
    the predicted structure/function words fast-confirm, the novel content is the
    residual (the news).
  * FINAL COMPREHENSION UNCHANGED — prediction is the PROCESS: the settled report
    is BYTE-IDENTICAL to the non-predictive baseline. Prediction speeds the
    process; it does not change the answer.
  * THE ACCUMULATING MODEL IMPROVES PREDICTION — full accumulation confirms MORE
    than a no-register control.
  * GRAPH-NATIVE — production faculty forward + ShapeDecode residual, driven by
    cognitive_tick; NO hardcoded expected words; no import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_predictive_first_pass.py -p no:randomly -q -s
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
from domains import predictive_reading as pr                           # noqa: E402
from domains import reading_collapse as rc                             # noqa: E402
from domains import reading_drive as rd                               # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402
import jabberwock_reads_a_multiarc_story as jrms                       # noqa: E402
import jabberwock_reads_predictively as jrp                            # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module")
def crow_pass():
    dl.warm_wordnet("en")
    ag = _fresh()
    out = pr.predict_first_pass(ag, jpafg.CROW)
    return ag, out


@pytest.fixture(scope="module")
def story_pass():
    dl.warm_wordnet("en")
    ag = _fresh()
    out = pr.predict_first_pass(ag, jrms.STORY)
    return ag, out


# --------------------------------------------------------------------------- #
#  PER-SENTENCE STREAM — one step per sentence, ordered, predict→confirm→residual.
# --------------------------------------------------------------------------- #
def test_streams_every_sentence_in_order(crow_pass):
    _ag, out = crow_pass
    sents = rc._split_sentences(jpafg.CROW)
    steps = out["steps"]
    # one step per sentence, in order (the first pass stays ORDERED).
    assert len(steps) == len(sents)
    assert [s["k"] for s in steps] == list(range(1, len(sents) + 1))
    for s, sent in zip(steps, sents):
        assert s["sentence"] == sent


def test_first_sentence_is_cold_start_all_residual(crow_pass):
    _ag, out = crow_pass
    first = out["steps"][0]
    # the first sentence has no prior context — it is the honest cold start:
    # nothing predicted, everything is the residual (the news).
    assert first["cold_start"] is True
    assert first["predicted"] == [] and first["confirmed"] == []
    assert first["surprise"] and first["n_actual"] == len(first["surprise"])
    # every LATER sentence is a real predict→confirm→residual step.
    for s in out["steps"][1:]:
        assert s["cold_start"] is False


# --------------------------------------------------------------------------- #
#  AGGREGATE — a real confirm-vs-deep split across the WHOLE text.
# --------------------------------------------------------------------------- #
def test_aggregate_confirm_split_across_whole_text(story_pass):
    _ag, out = story_pass
    a = out["aggregate"]
    # the confirm fraction (the speedup) is a genuine fraction of the arriving
    # tokens — a real split, neither all-confirmed nor all-surprise.
    assert 0.0 < a["confirm_frac"] < 1.0
    assert abs(a["confirm_frac"] + a["deep_process_frac"] - 1.0) < 1e-9
    # the recurring-beat story is substantially predictable (the register + the
    # recurring beat fast-confirm): a meaningful speedup.
    assert a["confirm_frac"] >= 0.40, "expected a real fast-confirm speedup"
    # every arriving word is accounted for: confirmed + surprise = total.
    tot = sum(s["n_actual"] for s in out["steps"])
    assert a["total_confirmed"] + a["total_surprise"] == tot == a["total_words"]


def test_residual_is_the_news_structure_confirms_content_surprises(story_pass):
    _ag, out = story_pass
    # aggregate the confirmed / residual across the whole text.
    confirmed, surprise = set(), set()
    for s in out["steps"]:
        confirmed |= set(s["confirmed"])
        surprise |= set(s["surprise"])
    # the recurring STRUCTURE/beat words fast-confirm (the register + the beat).
    for w in ("the", "her", "gave", "thanked", "she"):
        assert w in confirmed, "recurring structure word %r should fast-confirm" % w
    # the NOVEL content lands in the residual (the news) at least once — the
    # per-arc specifics + the payoff content the model had not yet seen.
    for w in ("bread", "feather", "castle", "spell"):
        assert w in surprise, "novel content %r should be in the residual (news)" % w


def test_recurring_beat_fast_confirms_as_it_recurs(story_pass):
    _ag, out = story_pass
    # the AbS payoff, now whole-text: the sentences carrying the recurring beat
    # ('... thanked her and gave her a ...') fast-confirm at a HIGH fraction (the
    # beat's recurring words are covered; only the specific gift is the residual).
    beat_steps = [s for s in out["steps"]
                  if "thanked" in s["confirmed"] and "gave" in s["confirmed"]]
    assert beat_steps, "the recurring beat never fast-confirmed"
    assert max(s["confirm_frac"] for s in beat_steps) >= 0.75


# --------------------------------------------------------------------------- #
#  FINAL COMPREHENSION UNCHANGED — prediction is the PROCESS, not the answer.
# --------------------------------------------------------------------------- #
def test_final_comprehension_byte_identical_to_baseline():
    dl.warm_wordnet("en")
    # BASELINE: the non-predictive comprehension report (fresh agent).
    base = jpafg.analyse(jpafg.CROW)["report"]
    # PREDICTIVE: the SAME agent runs the predictive first pass THEN comprehends.
    ag = _fresh()
    pr.predict_first_pass(ag, jpafg.CROW)
    rd.run_reading_flow(ag, jpafg.CROW, report="analysis")
    after = jpafg._read_report_off_graph(ag.s)
    # prediction speeds the PROCESS; the settled comprehension is the SAME answer.
    assert after == base, "the predictive overlay changed the settled comprehension"
    assert len(base) > 0


# --------------------------------------------------------------------------- #
#  THE ACCUMULATING MODEL IMPROVES PREDICTION — full > no-register.
# --------------------------------------------------------------------------- #
def test_accumulating_register_improves_prediction():
    dl.warm_wordnet("en")
    for text in (jpafg.CROW, jrms.STORY):
        ag = _fresh()
        no_reg = jrp._windowed_confirm(ag, text, 0)     # beat + context only
        full = jrp._windowed_confirm(ag, text, 999)     # full accumulation
        # the accumulating register genuinely improves prediction as the text
        # proceeds — full accumulation confirms MORE than no register.
        assert full > no_reg, "the accumulating model did not improve prediction"


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — production forward + ShapeDecode residual, tick-driven.
# --------------------------------------------------------------------------- #
def test_predict_first_pass_is_tick_driven_via_shapedecode():
    src = inspect.getsource(pr.predict_first_pass)
    # the compare/residual runs through read_arc_predictively (tick-driven) — no
    # hand-pump in the streaming loop.
    assert "read_arc_predictively" in src
    assert "run_rules(" not in src and "fire_reflexes(" not in src
    # read_arc_predictively is cognitive_tick-driven and the residual is a
    # ShapeDecode Term (not a Python set-difference deciding the surprise).
    assert "cognitive_tick(" in inspect.getsource(pr.read_arc_predictively)
    assert '"type": "ShapeDecode"' in inspect.getsource(pr._decode_actual_against_prediction)
    assert 'res.get("residual")' in inspect.getsource(pr.abs_compare)


def test_no_hardcoded_story_words_in_first_pass_code():
    # the predicted words are HARVESTED from the graph (register + recurring beat +
    # discourse content); the streaming code must not name story content literally.
    tree = ast.parse(inspect.getsource(pr))
    doc_ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                doc_ids.add(id(body[0].value))
    banned = {"mira", "bird", "dog", "crow", "pitcher", "pebble", "whistle",
              "feather", "lantern", "castle", "child", "thanked", "gave"}
    for c in ast.walk(tree):
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in doc_ids:
            words = set("".join(ch if ch.isalpha() else " " for ch in c.value.lower()).split())
            hit = words & banned
            assert not hit, "hardcoded story literal(s) %s in code string %r" % (hit, c.value)


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
