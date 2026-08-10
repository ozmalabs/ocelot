"""test_well_read — THE WELL-READ READER as a STYLE-MANIFOLD (cross_text_prior).

Cross-text priors distributed in a continuous feature-vector space; a held-out
text is LOCATED as a point and the near same-style priors are up-weighted by a
smooth proximity kernel (genre/register/voice are axes, selected automatically).

Gated claims (all behind protected controls):
  * THE MANIFOLD GROWS per text (one StylePoint added per accumulated text);
  * LOCATE is EXPLAINABLE — the held-out fable's nearest prior-texts are the other
    FABLES (not the technical specs), with the shared features that put it there;
    the nearest pick is a held Argmax Term;
  * THREE-WAY: PROXIMITY > UNIFORM > COLD on the held-out fable, BOTH confirm-
    fraction and perplexity (context-selection beats a flat average beats empty);
  * READING-EXPERIENCE CURVE — denser manifold -> better (mean confirm up, mean
    perplexity down as N texts read, averaged over size-N subsets);
  * GENERALIZES — the held-out fable is DISJOINT from every primed text;
  * COLD == COMMITTED byte-identical (empty manifold = the committed cold reader);
    crow byte-identical (empty prior); final comprehension byte-identical;
  * GRAPH-NATIVE — graph-resident feature vector, held Argmax pick, no import re,
    donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_well_read.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import itertools
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from domains import cross_text_prior as ctp                           # noqa: E402
from domains import dictionary_lexicon as dl                          # noqa: E402
from domains import predictive_reading as pr                          # noqa: E402
from domains import reading_drive as rd                              # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402
import jabberwock_is_well_read as jwr                                  # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


FABLES, TECH, HELD_OUT, BUDGET = jwr.FABLES, jwr.TECH, jwr.HELD_OUT, jwr.BUDGET


def _confirm(reg) -> float:
    return pr.predict_first_pass(_fresh(), HELD_OUT,
                                 class_register=reg)["aggregate"]["confirm_frac"]


def _perplexity(reg) -> float:
    return pr.weighted_first_pass(_fresh(), HELD_OUT,
                                  class_register=reg)["perplexity_weighted"]


# --------------------------------------------------------------------------- #
#  THE MANIFOLD GROWS per text.
# --------------------------------------------------------------------------- #
def test_manifold_grows_one_point_per_text():
    ag = _fresh()
    assert len(ctp.points(ag)) == 0                     # empty manifold to start
    for i, (t, lb) in enumerate(FABLES, start=1):
        ctp.accumulate_text(ag, t, label=lb)
        assert len(ctp.points(ag)) == i                 # one StylePoint per text
    # each point carries its own feature-vector coords + its word prior.
    p0 = ctp.read_point(ag, ctp.points(ag)[0])
    assert set(p0["features"]) >= {"mean_wlen", "mean_slen", "ttr", "ed_frac"}
    assert p0["n_word_types"] > 0 and p0["register_top"]


# --------------------------------------------------------------------------- #
#  LOCATE — explainable; near = fables, far = specs; nearest is a held Argmax.
# --------------------------------------------------------------------------- #
def test_locate_places_heldout_near_fables_far_from_specs():
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    loc = ctp.locate(ag, HELD_OUT)
    # the held-out text has coordinates (its own feature vector).
    assert set(loc["features"]) >= {"mean_wlen", "mean_slen", "ttr", "ed_frac"}
    labels = [nb["label"] for nb in loc["neighbours"]]
    dists = {nb["label"]: nb["distance"] for nb in loc["neighbours"]}
    # EVERY fable is nearer than EVERY spec — the manifold separates the registers.
    fable_lbls = [lb for _t, lb in FABLES]
    spec_lbls = [lb for _t, lb in TECH]
    assert max(dists[l] for l in fable_lbls) < min(dists[l] for l in spec_lbls)
    # the nearest is a fable, and it is EXPLAINABLE (shares real content words).
    assert loc["nearest"]["label"] in fable_lbls
    assert loc["nearest"]["shared"], "nearest neighbour has no explaining features"
    # proximity fades the far specs to near-zero vs the near fables.
    pw = ctp.proximity_weights(ag, HELD_OUT)
    by_lbl = {ag.s.node(n)["attrs"]["label"]: pw[ctp._v(n)] for n in ctp.points(ag)}
    assert min(by_lbl[l] for l in fable_lbls) > max(by_lbl[l] for l in spec_lbls)


def test_nearest_pick_is_a_held_argmax_term():
    # the nearest-point decision runs through predictive_reading's held Argmax Term.
    src = inspect.getsource(ctp.locate)
    assert "_argmax_pairs_term" in src
    assert "native.evaluate(" in src


# --------------------------------------------------------------------------- #
#  THREE-WAY — proximity > uniform > cold, BOTH confirm and perplexity.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def three_way():
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    uni = ctp.uniform_register(ag, budget=BUDGET)
    ctx = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET)
    return {"cold": ([], _confirm([]), _perplexity([])),
            "uniform": (uni, _confirm(uni), _perplexity(uni)),
            "proximity": (ctx, _confirm(ctx), _perplexity(ctx))}


def test_confirm_proximity_beats_uniform_beats_cold(three_way):
    c = three_way["cold"][1]
    u = three_way["uniform"][1]
    x = three_way["proximity"][1]
    assert x > u > c, "confirm: proximity %.3f > uniform %.3f > cold %.3f" % (x, u, c)


def test_perplexity_proximity_beats_uniform_beats_cold(three_way):
    c = three_way["cold"][2]
    u = three_way["uniform"][2]
    x = three_way["proximity"][2]
    # lower perplexity is better.
    assert x < u < c, "perplexity: proximity %.1f < uniform %.1f < cold %.1f" % (x, u, c)


def test_proximity_budget_holds_fable_words_uniform_wastes_on_specs(three_way):
    uni = set(three_way["uniform"][0])
    ctx = set(three_way["proximity"][0])
    # the uniform budget wastes slots on the far technical register's frequent
    # words; the proximity budget does not (it selected the near fable region).
    tech_words = {"system", "module", "device", "buffer", "signal", "value", "output"}
    assert uni & tech_words, "uniform budget should be diluted by technical words"
    assert not (ctx & tech_words), "proximity budget should exclude technical words"


# --------------------------------------------------------------------------- #
#  READING-EXPERIENCE CURVE — denser manifold -> better (averaged over subsets).
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def curve():
    rows = []
    for N in range(0, len(FABLES) + 1):
        subsets = list(itertools.combinations(range(len(FABLES)), N)) or [()]
        cfs, pps = [], []
        for sub in subsets:
            ag = _fresh()
            ctp.prime_reader(ag, [FABLES[i] for i in sub])
            reg = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET) if N else []
            cfs.append(_confirm(reg))
            pps.append(_perplexity(reg))
        rows.append((N, sum(cfs) / len(cfs), sum(pps) / len(pps)))
    return rows


def test_curve_confirm_monotone_ish_up(curve):
    confirms = [c for _n, c, _p in curve]
    # non-decreasing across the whole curve (denser manifold never hurts the mean).
    assert all(confirms[i + 1] >= confirms[i] - 1e-9 for i in range(len(confirms) - 1))
    # and a real end-to-end lift: the full manifold beats the empty one.
    assert confirms[-1] > confirms[0]


def test_curve_perplexity_monotone_ish_down(curve):
    ppls = [p for _n, _c, p in curve]
    assert all(ppls[i + 1] <= ppls[i] + 1e-6 for i in range(len(ppls) - 1))
    assert ppls[-1] < ppls[0]


# --------------------------------------------------------------------------- #
#  GENERALIZES — the held-out fable is DISJOINT from every primed text.
# --------------------------------------------------------------------------- #
def test_heldout_is_disjoint_from_prime_set():
    primes = [t for t, _ in FABLES + TECH]
    assert HELD_OUT not in primes
    # the lift rides SHARED fable-register vocabulary, not a memorized primed text.
    ag = _fresh()
    ctp.prime_reader(ag, FABLES + TECH)
    ctx = ctp.context_selected_register(ag, HELD_OUT, budget=BUDGET)
    heldout_content = set(pr._content_words(ag, HELD_OUT))
    shared = [w for w in ctx if w in heldout_content]
    assert shared, "the context register shares no content word with the held-out"


# --------------------------------------------------------------------------- #
#  COLD == COMMITTED + BYTE-IDENTICAL guards.
# --------------------------------------------------------------------------- #
def test_cold_equals_committed_predict_first_pass():
    base = pr.predict_first_pass(_fresh(), jpafg.CROW)
    cold = pr.predict_first_pass(_fresh(), jpafg.CROW, class_register=[])
    assert base == cold                                # empty prior = committed
    none = pr.predict_first_pass(_fresh(), jpafg.CROW, class_register=None)
    assert base == none


def test_cold_equals_committed_weighted_first_pass():
    base = pr.weighted_first_pass(_fresh(), jpafg.CROW)
    cold = pr.weighted_first_pass(_fresh(), jpafg.CROW, class_register=[])
    assert base == cold


def test_final_comprehension_byte_identical_with_well_read_process():
    base = jpafg.analyse(jpafg.CROW)["report"]
    ag = _fresh()
    ctp.prime_reader(ag, FABLES)
    reg = ctp.context_selected_register(ag, jpafg.CROW, budget=BUDGET)
    pr.predict_first_pass(ag, jpafg.CROW, class_register=reg)   # the well-read process
    rd.run_reading_flow(ag, jpafg.CROW, report="analysis")
    after = jpafg._read_report_off_graph(ag.s)
    assert after == base and len(base) > 0


# --------------------------------------------------------------------------- #
#  PERSISTENCE — the well-read seed (teach idiom), to a TMP dir (never real seeds).
# --------------------------------------------------------------------------- #
def test_persist_points_round_trips_to_a_seed(tmp_path):
    ag = _fresh()
    ctp.prime_reader(ag, FABLES[:2])
    receipts = ctp.persist_points(ag, category="well_read_test", seeds_dir=tmp_path)
    assert receipts and all(r.get("persisted") for r in receipts)
    seed = tmp_path / "well_read_test.json"
    assert seed.exists()
    manifest = json.loads(seed.read_text())
    nodes = [n for n in manifest["nodes"] if n["type"] == "StylePoint"]
    assert len(nodes) == 2                              # both points persisted
    assert all("word_counts" in n["attrs"] and "features" in n["attrs"] for n in nodes)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — feature vector graph-resident; no regex; donkey=0.
# --------------------------------------------------------------------------- #
def test_feature_vector_is_graph_resident():
    ag = _fresh()
    node = ctp.accumulate_text(ag, FABLES[0][0], label="x")
    # the coordinates are stored ON the node (JSON attr), not a Python-side dict.
    attrs = ag.s.node(node)["attrs"]
    feats = json.loads(attrs["features"])
    assert set(feats) >= {"mean_wlen", "mean_slen", "long_frac", "ttr", "ed_frac"}
    assert "word_counts" in attrs and "construction_counts" in attrs


def test_source_audit_no_regex_no_donkey():
    src = inspect.getsource(ctp)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re found"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... found"
    for banned in ("openai", "anthropic", "requests.post", "call_model",
                   "self_teacher", "numpy", "torch"):
        assert banned not in src, "donkey/neural token %r found" % banned
    # no NEURAL embedding import/use (the disclaimer word in the docstring aside).
    assert "import torch" not in src and "sentence_transformers" not in src


def test_no_hardcoded_fable_literals_in_module():
    # the module holds NO corpus literals — the texts live in the caller (the gate
    # script), the module only reads whatever it is handed.
    tree = ast.parse(inspect.getsource(ctp))
    doc_ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                doc_ids.add(id(body[0].value))
    banned = {"fox", "grapes", "lion", "mouse", "crow", "jug", "bird", "dog",
              "bone", "thirsty", "pebble", "pitcher", "system", "module", "device"}
    for c in ast.walk(tree):
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and id(c) not in doc_ids:
            words = set("".join(ch if ch.isalpha() else " " for ch in c.value.lower()).split())
            assert not (words & banned), "hardcoded corpus literal in %r" % c.value
