"""test_weighted_prediction — the WEIGHTED WORD-LIKELIHOOD engine (finer grain for
predicting written text). Gates:

  * predict_next_words returns a word->likelihood DISTRIBUTION (not a flat set),
    normalized, with graph-resident source strengths;
  * the weighted top-1 / top-k matches the actual MORE often than the flat set, and
    the PERPLEXITY is LOWER (both numbers), strongest on repetitive text;
  * the surprisal is GRADED (-ln p, continuous) — a rare word high, a frequent word
    low;
  * the meter/rhyme weights sharpen the verse line-end (the rhyme slot);
  * FINAL COMPREHENSION is byte-identical (prediction is the PROCESS, not the answer);
  * graph-native: the combination/ranking/surprisal are held Terms; no regex; donkey=0.
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

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import metrical_reading as mr
from domains import predictive_reading as pr
from domains import reading_collapse as rc
from domains import reading_drive as rd
import jabberwock_produces_analysis_from_goal as jpafg
import jabberwock_reads_a_multiarc_story as jrms


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module")
def _warm():
    dl.warm_wordnet("en")
    return True


FORMULAIC = [
    "I do not like green eggs and ham", "I do not like them here or there",
    "I do not like them anywhere", "I will not eat green eggs and ham",
    "I will not eat them here or there", "I will not eat them anywhere",
    "I do not like green eggs and ham", "I will not eat them here or there"]


# --------------------------------------------------------------------------- #
#  1. THE WEIGHTED DISTRIBUTION.
# --------------------------------------------------------------------------- #
def test_predict_returns_normalized_likelihood_distribution(_warm):
    ag = _fresh()
    sents = rc._split_sentences(jrms.STORY)
    seen = sents[:4]
    counts: dict = {}
    for s in seen:
        for w in pr._words(ag, s):
            counts[w] = counts.get(w, 0) + 1
    model = pr.build_writer_model(ag, seen)
    pred = pr.predict_next_words(ag, model["writer_style"], context=" ".join(seen),
                                 seen_vocab=list(counts), register_freq=counts)
    lk = pred["likelihoods"]
    assert lk and set(lk) == set(pred["predicted_words"])          # word -> likelihood
    assert abs(sum(lk.values()) - 1.0) < 1e-9                      # a distribution
    assert all(0.0 <= p <= 1.0 for p in lk.values())
    # the top-1 is the argmax of the distribution (held Argmax Term).
    assert pred["top1"] == pred["ranked"][0][0]
    assert lk[pred["top1"]] == max(lk.values())
    # NOT flat — the distribution concentrates (max >> uniform).
    assert lk[pred["top1"]] > 1.5 / len(lk)


def test_source_strengths_are_graph_resident_not_uniform(_warm):
    ag = _fresh()
    sents = rc._split_sentences(jrms.STORY)
    seen = sents[:4]
    counts: dict = {}
    for s in seen:
        for w in pr._words(ag, s):
            counts[w] = counts.get(w, 0) + 1
    model = pr.build_writer_model(ag, seen)
    pred = pr.predict_next_words(ag, model["writer_style"], context=" ".join(seen),
                                 seen_vocab=list(counts), register_freq=counts)
    top = pred["top1"]
    s = pred["source_strengths"][top]
    # the top word is carried by real graph evidence — a recurring beat and/or a
    # frequent register word, never a bare uniform prior.
    assert s["register"] > 1.0 or s["beat"] > 0.0 or s["context"] > 0.0
    # the beat source's strength is the arc-recurrence count (>= 2 when present).
    beat_counts = model["recurring_beat_counts"]
    if beat_counts:
        assert all(c >= 2 for c in beat_counts.values())


# --------------------------------------------------------------------------- #
#  2. TOP-1 / TOP-K + PERPLEXITY beat the FLAT set.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def story_weighted(_warm):
    return pr.weighted_first_pass(_fresh(), jrms.STORY)


def test_weighted_top1_and_topk_beat_flat(story_weighted):
    r = story_weighted
    assert r["top1_weighted"] > r["top1_flat"]
    assert r["topk_weighted"] > r["topk_flat"]


def test_perplexity_lower_than_flat(story_weighted):
    r = story_weighted
    assert r["perplexity_weighted"] < r["perplexity_flat"]
    assert r["mean_surprisal_weighted"] < r["mean_surprisal_flat"]


def test_finer_grain_holds_on_a_second_text(_warm):
    r = pr.weighted_first_pass(_fresh(), jpafg.CROW)
    # even on the terse crow the weighted arm is no worse and top-k/perplexity better.
    assert r["perplexity_weighted"] <= r["perplexity_flat"]
    assert r["topk_weighted"] >= r["topk_flat"]


# --------------------------------------------------------------------------- #
#  3. SURPRISAL-GRADED (continuous) RESIDUAL.
# --------------------------------------------------------------------------- #
def test_surprisal_is_graded_rare_high_frequent_low(story_weighted):
    r = story_weighted
    surps = [row["surprisal"] for row in r["per_word"]]
    assert len(set(round(s, 3) for s in surps)) > 3          # NOT binary — graded
    # a word IN the distribution (predicted) is lower surprisal than an OOV word.
    in_set = [row["surprisal"] for row in r["per_word"] if row["in_set"]]
    oov = [row["surprisal"] for row in r["per_word"] if not row["in_set"]]
    if in_set and oov:
        assert min(in_set) < max(oov)
        assert sum(in_set) / len(in_set) < sum(oov) / len(oov)


def test_surprisal_is_the_held_log_term(_warm):
    ag = _fresh()
    # surprisal(p) == -ln(p), computed by the held Neg(Log) Term.
    import math
    for p in (0.5, 0.1, 0.02):
        assert abs(pr.surprisal(ag.inner, p) - (-math.log(p))) < 1e-9


# --------------------------------------------------------------------------- #
#  4. VERSE — meter/rhyme sharpens the line-end.
# --------------------------------------------------------------------------- #
def test_meter_rhyme_sharpens_formulaic_verse_lineend(_warm):
    ag = _fresh()
    mr.ensure_meter_codebook(ag)
    r = pr.weighted_verse_first_pass(ag, FORMULAIC)
    # on repeated-rhyme verse the meter/rhyme weight LOWERS the line-end surprisal.
    assert r["lineend_surprisal_guided"] < r["lineend_surprisal_baseline"]
    assert r["n_line_ends"] > 0


# --------------------------------------------------------------------------- #
#  5. FINAL COMPREHENSION BYTE-IDENTICAL.
# --------------------------------------------------------------------------- #
def test_final_comprehension_byte_identical(_warm):
    base = jpafg.analyse(jpafg.CROW)["report"]
    ag = _fresh()
    pr.weighted_first_pass(ag, jpafg.CROW)
    rd.run_reading_flow(ag, jpafg.CROW, report="analysis")
    after = jpafg._read_report_off_graph(ag.s)
    assert base == after


# --------------------------------------------------------------------------- #
#  6. GRAPH-NATIVE — the combination/ranking/surprisal are held Terms.
# --------------------------------------------------------------------------- #
def test_combination_and_surprisal_are_held_terms(_warm):
    ag = _fresh()
    # the weighted sum is a held Plus Term.
    assert pr._combine_term([1.0, 2.0, 3.0])["type"] == "Plus"
    assert abs(pr._combine_score(ag.inner, [1.0, 2.0, 3.0]) - 6.0) < 1e-9
    # the surprisal is a held Neg(Log) Term.
    assert pr._surprisal_term(0.5)["type"] == "Neg"
    assert pr._surprisal_term(0.5)["arg"]["type"] == "Log"
    # the top-1 is a held Argmax Term.
    assert pr._argmax_pairs_term([["a", 1.0], ["b", 2.0]])["type"] == "Argmax"


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


def test_no_hardcoded_story_words_in_weighting_code():
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
              "feather", "lantern", "castle", "child", "thanked", "gave", "ham"}
    for c in ast.walk(tree):
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in doc_ids:
            words = set("".join(ch if ch.isalpha() else " " for ch in c.value.lower()).split())
            hit = words & banned
            assert not hit, "hardcoded story literal(s) %s in %r" % (hit, c.value)
