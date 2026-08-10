"""test_fast_reader — THE FAST READER: reading speed IS the AbS fraction.

A fast reader does more analysis-by-synthesis: it PREDICTS more (fast-confirms) and
bottom-up-decodes less. Three gated payoffs, each behind a protected control:

  1. SPEED = CONFIRM — a RICHER model (a class-register prior harvested from a
     writer-class corpus, held on the AudienceCentroid) reads FASTER (higher
     confirm-fraction) with the SAME settled comprehension (byte-identical report).
  2. EFFORT FOLLOWS RESIDUAL — the per-sentence deep-process DWELL tracks the
     ShapeDecode residual (correlated), vs a UNIFORM reader (uncorrelated): effort
     concentrates on the news. Graph-driven (a DwellStage + seeded rule/reflex,
     drained by cognitive_tick).
  3. CHAR-SUB — a PREDICTED word tolerates character-substitution noise ('b1rd' ->
     'bird'): prediction-guided accuracy > bottom-up. A graph-native per-position
     consistency check, not a hardcoded typo table.

GRAPH-NATIVE audit: the class model is graph-resident; the residual is a ShapeDecode
collapse; the dwell is cognitive_tick-driven; the char-sub tolerance is a scratch-
node Eq consistency check. No import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_fast_reader.py -p no:randomly -q -s
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

from substrate.boot_core import boot_core                                # noqa: E402
from domains import dictionary_lexicon as dl                             # noqa: E402
from domains import reading_collapse as rc                               # noqa: E402
from domains import reading_drive as rd                                  # noqa: E402
from domains import predictive_reading as pr                             # noqa: E402
from domains import comprehend_text as ct                               # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                   # noqa: E402
import jabberwock_reads_a_multiarc_story as jrms                         # noqa: E402
import jabberwock_reads_fast as jrf                                      # noqa: E402


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
def _warm():
    dl.warm_wordnet("en")
    return True


# --------------------------------------------------------------------------- #
#  1. SPEED = CONFIRM — a richer model reads faster, same comprehension.
# --------------------------------------------------------------------------- #
def test_speed_is_confirm_rich_beats_thin(_warm):
    text = jpafg.CROW
    thin = pr.predict_first_pass(_fresh(), text)["aggregate"]["confirm_frac"]
    rich = pr.predict_first_pass(_fresh(), text, class_corpus=jrf.CLASS_CORPUS)["aggregate"]["confirm_frac"]
    print("\n  SPEED=CONFIRM: thin=%.4f rich=%.4f" % (thin, rich))
    # reading speed IS the confirm fraction; the richer model reads FASTER.
    assert rich > thin, "richer model did not read faster (confirm rich %.4f !> thin %.4f)" % (rich, thin)
    assert thin > 0.0 and rich > 0.0


def test_comprehension_unchanged_byte_identical(_warm):
    text = jpafg.CROW
    base = jpafg.analyse(text)["report"]
    ag_t = _fresh(); pr.predict_first_pass(ag_t, text)
    rd.run_reading_flow(ag_t, text, report="analysis")
    rep_thin = jpafg._read_report_off_graph(ag_t.s)
    ag_r = _fresh(); pr.predict_first_pass(ag_r, text, class_corpus=jrf.CLASS_CORPUS)
    rd.run_reading_flow(ag_r, text, report="analysis")
    rep_rich = jpafg._read_report_off_graph(ag_r.s)
    # a faster reader is not a shallower one — the settled answer is UNCHANGED.
    assert base == rep_thin, "thin-stream changed the comprehension report"
    assert base == rep_rich, "rich-stream changed the comprehension report"


def test_class_register_is_graph_resident(_warm):
    ag = _fresh()
    reg = pr._class_register_from_corpus(ag, jrf.CLASS_CORPUS)
    assert len(reg) > 10, "class-register prior implausibly small"
    model = pr.build_writer_model(ag, [jrf.CLASS_CORPUS[0]], class_corpus=jrf.CLASS_CORPUS)
    # the prior lives on the AudienceCentroid (the class it belongs to) AND is read
    # back on the WriterStyle model — a REAL class model, graph-resident.
    cen = ag.s.node(model["audience_centroid"])["attrs"]
    assert cen.get("class_register"), "class register not stored on the AudienceCentroid"
    got = pr.read_writer_model(ag, model["writer_style"])["class_register"]
    assert got == reg, "class register not carried on the WriterStyle model"
    # provenance: predict_next_words tags the prior words 'class_prior'.
    pw = pr.predict_next_words(ag, model["writer_style"])
    assert any(v == "class_prior" for v in pw["provenance"].values()), \
        "no class_prior provenance in the prediction"


# --------------------------------------------------------------------------- #
#  2. EFFORT FOLLOWS THE RESIDUAL — the variable-aperture dwell.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def dwell(_warm):
    return pr.adaptive_dwell_pass(_fresh(), jrms.STORY)


def test_effort_follows_residual(dwell):
    print("\n  EFFORT: adaptive_r=%.3f uniform_r=%.3f dwell=%d uniform=%d saved=%d"
          % (dwell["adaptive_r"], dwell["uniform_r"], dwell["total_dwell"],
             dwell["total_uniform"], dwell["saved"]))
    # the deep-process DWELL tracks the residual (effort follows the news) —
    # strongly correlated — while a UNIFORM reader's constant dwell does not.
    assert dwell["adaptive_r"] >= 0.9, "dwell does not track the residual"
    assert dwell["uniform_r"] < 0.1, "the uniform control is not uncorrelated"
    assert dwell["adaptive_r"] > dwell["uniform_r"]
    # the residual varies across sentences (a real reallocation, not flat).
    res = [s["residual_count"] for s in dwell["steps"] if not s["cold_start"]]
    assert max(res) > min(res), "residual is flat — no aperture to open"
    # adaptive reallocation SAVES effort vs deep-processing every word.
    assert dwell["total_dwell"] < dwell["total_uniform"], "no effort saved vs uniform"


def test_high_residual_sentences_get_more_dwell(dwell):
    steps = [s for s in dwell["steps"] if not s["cold_start"]]
    # per-sentence: dwell is monotone in the residual (the aperture opens as wide as
    # the news) — the high-residual sentences get the most deep processing.
    hi = max(steps, key=lambda s: s["residual_count"])
    lo = min(steps, key=lambda s: s["residual_count"])
    assert hi["dwell"] >= lo["dwell"], "the high-residual sentence did not dwell more"


def test_dwell_is_graph_driven_cognitive_tick(_warm):
    # source audit: the dwell is driven by cognitive_tick, NOT a hand-pump.
    src = inspect.getsource(pr.read_arc_with_dwell)
    assert "cognitive_tick(" in src, "the dwell must be driven by cognitive_tick"
    assert "run_rules(" not in src and "fire_reflexes(" not in src, "no hand-pump allowed"
    assert "DwellStage" in src, "the dwell budget must be a graph-resident DwellStage"
    # the reflex RESPONSE consumes ONE unit per firing (a return inside the scan).
    adv = pr._advance_dwell_stage
    tree = ast.parse(inspect.getsource(adv))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    scan = next(l for l in ast.walk(fn) if isinstance(l, ast.For))
    assert any(isinstance(n, ast.Return) for n in ast.walk(scan))
    # end-to-end: a real run mints DwellStage + DeepProcess nodes (the order-N work
    # materialised in the graph), and the budget drains to spent==residual.
    ag = _fresh()
    model = pr.build_writer_model(ag, ["On the road she met a starving dog."])
    r = pr.read_arc_with_dwell(ag, model["writer_style"],
                               "The dog thanked her and gave her a whistle.",
                               context="On the road she met a starving dog.")
    assert ag.s.nodes("DwellStage"), "no DwellStage minted"
    assert r["dwell"] == r["residual_count"], "dwell did not equal the drained residual"
    if r["residual_count"] > 0:
        assert ag.s.nodes("DeepProcess"), "no DeepProcess (deep order-N work) minted"


# --------------------------------------------------------------------------- #
#  3. CHARACTER-SUBSTITUTION — prediction-guided beats bottom-up.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def story_model(_warm):
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, jrms.STORY)
    sents = rc._split_sentences(jrms.STORY)
    arcs = [" ".join(sents[c["span_start"]:c["span_end"] + 1]) for c in out["tree"]["children"]]
    beat = next((t["name"] for t in out["throughlines"] if t["kind"] == "pattern"), None)
    model = pr.build_writer_model(ag, arcs[:2], throughline_beat=beat)
    return ag, model


def test_char_sub_guided_beats_bottom_up(story_model):
    ag, model = story_model
    cases = [
        ("On the road she met a starving dog.", "the d0g thanked her",
         ["the", "dog", "thanked", "her"]),
        ("The next day she met a shivering bird.", "the b1rd thanked her",
         ["the", "bird", "thanked", "her"]),
    ]
    bu_accs, pg_accs = [], []
    for ctx, noisy, truth in cases:
        predicted = pr.predict_next_words(ag, model["writer_style"], context=ctx)["predicted_words"]
        bu = pr.bottom_up_segment(ag, noisy)
        pg = pr.prediction_guided_segment(ag, predicted, noisy)
        a_bu = pr.segmentation_accuracy(bu, truth)
        a_pg = pr.segmentation_accuracy(pg, truth)
        bu_accs.append(a_bu); pg_accs.append(a_pg)
        # per-case: prediction-guided recovers the char-sub word; bottom-up does not.
        assert a_pg == 1.0, "prediction-guided failed to recover %r -> %s" % (noisy, pg)
        assert a_pg > a_bu, "prediction-guided did not beat bottom-up on %r" % noisy
    mbu, mpg = sum(bu_accs) / len(bu_accs), sum(pg_accs) / len(pg_accs)
    print("\n  CHAR-SUB: bottom-up=%.3f prediction-guided=%.3f" % (mbu, mpg))
    assert mpg == 1.0 and mpg > mbu
    assert mbu < 0.8, "bottom-up unexpectedly strong on char-substituted input"


def test_missing_space_still_recovered(story_model):
    # the SAME prediction still closes the ORIGINAL missing-space case (no regression).
    ag, model = story_model
    predicted = pr.predict_next_words(
        ag, model["writer_style"],
        context="The next day she met a shivering bird.")["predicted_words"]
    pg = pr.prediction_guided_segment(ag, predicted, "thebirdthankedher")
    assert pr.segmentation_accuracy(pg, ["the", "bird", "thanked", "her"]) == 1.0


def test_char_sub_is_graph_native_consistency():
    # the char-sub tolerance is a graph-native per-position consistency check
    # (scratch Char nodes + an Eq Term), NOT a hardcoded typo table.
    src = inspect.getsource(ct._char_consistency)
    assert '"type": "Eq"' in src, "char consistency must be an Eq Term decision"
    assert "Substrate()" in src and "add_node(\"Char\"" in src, \
        "char consistency must be decided over scratch Char nodes"
    # behaviour: 'b1rd' is consistent with 'bird' (3/4 agree), recovered as 'bird';
    # a clean word is NOT 'recovered' into a different word; length mismatch -> None.
    assert ct._char_consistency("b1rd", "bird") == 3
    assert ct._char_consistency("bird", "birds") is None
    assert ct.char_sub_recover("b1rd", ["bird", "gave", "the"]) == "bird"
    assert ct.char_sub_recover("herd", ["herd", "bird"]) is None   # exact word: no swap
    # no typo table: char_sub_recover holds no literal mapping of noisy->clean.
    csr = inspect.getsource(ct.char_sub_recover)
    assert "b1rd" not in csr and "typo" not in csr.lower()


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — no regex, donkey = 0, no hardcoded story words in the module.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_donkey():
    for mod in (pr, ct):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name == "re" for a in n.names), "import re in %s" % mod.__name__
            if isinstance(n, ast.ImportFrom):
                assert n.module != "re", "from re import in %s" % mod.__name__
        for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
            assert banned not in src, "donkey token %r in %s" % (banned, mod.__name__)


def test_no_hardcoded_story_words_in_predictive_module():
    # the new class-prior / dwell code must not name the story's content in
    # executable strings — the class corpus is the CALLER's (the script), the
    # predicted/residual words HARVESTED from the graph.
    tree = ast.parse(inspect.getsource(pr))
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    banned = {"mira", "bird", "dog", "whistle", "feather", "lantern", "castle",
              "child", "fortune", "thanked", "gave", "crow", "pitcher", "pebbles"}
    for c in ast.walk(tree):
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in docs:
            words = set("".join(ch if ch.isalpha() else " " for ch in c.value.lower()).split())
            assert not (words & banned), "hardcoded story literal(s) %s in %r" % (words & banned, c.value)
