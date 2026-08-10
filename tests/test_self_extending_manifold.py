"""test_self_extending_manifold — THE SELF-EXTENDING MANIFOLD: the jabberwock MINTS
its own style dimensions via the sd loop.

The style manifold's axis set is no longer a fixed hand-picked Python list — it is
GRAPH DATA (StyleDimension nodes), and the AGENT grows its own axes. When a RESIDUAL
demands a new axis (two texts the caller holds DISTINCT that the SEED axes cannot
separate), the agent DISCOVERS the graph-observable feature that separates them and
RIDES THE SD LOOP (seeds/shape_decode_loop.json's sd_mint_quantum / codebook_epoch /
sd_redecode) to MINT a StyleDimension for it. N seed axes -> N+1.

Gated claims (all behind protected controls):
  * SELF-EXTENDING (headline) — two texts UNSEPARATED on the seed axes -> mint
    EXACTLY ONE new StyleDimension -> the two texts LOCATE DISTINCTLY after the mint
    (N -> N+1, separate AFTER not BEFORE);
  * THE MINT RIDES THE SD LOOP — the residual triggers the mint (residual predicates
    from induce_concern), codebook_epoch grows, sd_redecode re-decodes to recognized;
  * PERSISTED — the minted StyleDimension is graph-resident + persisted (a fresh boot
    re-installs it and it still separates);
  * OVER-MINTING DISCIPLINE — the no-residual case mints NOTHING (already-separated ->
    recognized; genuinely-same -> no residual); the committed manifold byte-identical;
  * GRAPH-NATIVE — StyleDimension is a graph node; the separating feature is graph-
    observable; the mint rides the SAME sd machinery; no import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_self_extending_manifold.py -p no:randomly -q -s
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
from domains import cross_text_prior as ctp                           # noqa: E402
from domains import dictionary_lexicon as dl                          # noqa: E402
import jabberwock_extends_its_manifold as jem                          # noqa: E402
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


def _min_dist(dists, labels):
    return min(d for _n, lb, d, _s in dists if lb in labels)


# --------------------------------------------------------------------------- #
#  THE AXIS SET IS GRAPH DATA.
# --------------------------------------------------------------------------- #
def test_axis_set_is_graph_resident_style_dimension_nodes():
    ag = _fresh()
    assert ctp.dimensions(ag) == []                    # no StyleDimension at boot
    added = ctp.install_style_dimensions(ag)
    assert len(added) == len(ctp._SEED_DIMENSIONS)
    dims = ctp.dimensions(ag)
    # the axis set is READ OFF the graph (StyleDimension nodes), not a Python list.
    names = {d["name"] for d in dims}
    assert names == {d["name"] for d in ctp._SEED_DIMENSIONS}
    assert names >= {"voice", "genre", "register", "period", "mood", "formality"}
    assert all(not d["minted"] for d in dims)          # all seed, none minted yet
    # they are actual graph nodes.
    assert len(list(ag.s.nodes("StyleDimension"))) == len(ctp._SEED_DIMENSIONS)


def test_install_is_idempotent():
    ag = _fresh()
    ctp.install_style_dimensions(ag)
    ctp.install_style_dimensions(ag)
    assert len(ctp.dimensions(ag)) == len(ctp._SEED_DIMENSIONS)


# --------------------------------------------------------------------------- #
#  SELF-EXTENDING (the headline): unseparated -> mint ONE -> separated. N -> N+1.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def minted():
    ag = _fresh()
    ctp.prime_reader(ag, jem.INTERROGATIVE + jem.DECLARATIVE)
    ctp.install_style_dimensions(ag)
    n_before = len(ctp.dimensions(ag))
    d0 = ctp._distances(ag, jem.PROBE_INT)
    a0, b0 = _min_dist(d0, jem.INT_LBLS), _min_dist(d0, jem.DEC_LBLS)
    res = ctp.extend_on_residual(ag, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0])
    d1 = ctp._distances(ag, jem.PROBE_INT)
    a1, b1 = _min_dist(d1, jem.INT_LBLS), _min_dist(d1, jem.DEC_LBLS)
    return {"ag": ag, "n_before": n_before, "n_after": len(ctp.dimensions(ag)),
            "before": (a0, b0), "after": (a1, b1), "res": res}


def test_seed_axes_do_not_separate_the_two_texts_before(minted):
    a0, b0 = minted["before"]
    # BEFORE: the seed axes are BLIND to interrogativity — the probe is EXACTLY as
    # near its own cluster as the other (same scene/content/register coords).
    assert abs(a0 - b0) < 1e-9, "seed axes should NOT separate them: %.6f vs %.6f" % (a0, b0)


def test_mints_exactly_one_new_dimension(minted):
    res = minted["res"]
    assert res["minted"] is True
    assert minted["n_after"] == minted["n_before"] + 1     # N -> N+1
    assert res["dimension"] == "minted:question_frac"
    # exactly one minted StyleDimension node.
    dims = ctp.dimensions(minted["ag"])
    assert sum(1 for d in dims if d["minted"]) == 1


def test_two_texts_locate_distinctly_after_the_mint(minted):
    a1, b1 = minted["after"]
    # AFTER: the minted axis separates them — the interrogative probe is now nearer
    # its own (interrogative) cluster than the declarative one.
    assert a1 < b1, "the minted axis should separate them: %.6f < %.6f" % (a1, b1)
    ag = minted["ag"]
    top_int = [nb["label"] for nb in ctp.locate(ag, jem.PROBE_INT)["neighbours"][:3]]
    top_dec = [nb["label"] for nb in ctp.locate(ag, jem.PROBE_DEC)["neighbours"][:3]]
    assert all(l in jem.INT_LBLS for l in top_int), top_int
    assert all(l in jem.DEC_LBLS for l in top_dec), top_dec


# --------------------------------------------------------------------------- #
#  THE MINT RIDES THE SD LOOP.
# --------------------------------------------------------------------------- #
def test_the_mint_rides_the_sd_loop(minted):
    res = minted["res"]
    # the residual triggered the mint (sd_mint_quantum's residual predicates), the
    # codebook grew (codebook_epoch), and sd_redecode re-decoded to recognized.
    assert res["residual_predicates"] == ["question_frac"]
    assert res["codebook_epoch"] >= 1.0
    assert res["reobserved_status"] == "recognized"
    assert res["loop"]["minted"] is True               # induce_concern's verdict
    # the mint is driven by the sd loop, not a hardcoded add.
    src = inspect.getsource(ctp.extend_on_residual)
    assert "induce_concern" in src
    assert "run_rules" in src


def test_discovery_is_a_held_argmax_search():
    # the separating-feature pick runs through a held Argmax Term (not a pre-chosen
    # feature): the candidate pool has many features; the DATA picks the winner.
    ag = _fresh()
    win = ctp.discover_separating_feature(ag, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0])
    assert win["key"] == "question_frac"               # the data-picked winner
    assert win["norm_sep"] > 0
    src = inspect.getsource(ctp.discover_separating_feature)
    assert "_argmax_pairs_term" in src and "native.evaluate(" in src
    # the pool is a real repertoire (>1 candidate), so the pick is a search.
    assert len(ctp._candidate_features(ag, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0])) > 3


def test_the_separating_feature_really_separates():
    # not a spurious feature that merely differs — it genuinely separates the two
    # texts (val_a clearly apart from val_b) AND generalizes to a same-style probe.
    ag = _fresh()
    win = ctp.discover_separating_feature(ag, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0])
    assert win["val_a"] > win["val_b"]                 # interrogative denser in '?'
    va = ctp._feature_value(ag, jem.PROBE_INT, win["kind"], win["key"], win["params"])
    vb = ctp._feature_value(ag, jem.PROBE_DEC, win["kind"], win["key"], win["params"])
    assert va > vb                                     # the probe pair separates too


# --------------------------------------------------------------------------- #
#  PERSISTED — the minted axis survives a boot.
# --------------------------------------------------------------------------- #
def test_minted_axis_survives_a_boot(tmp_path):
    # SESSION 1 — prime, mint, persist the points + the minted dimension.
    s1 = _fresh()
    ctp.prime_reader(s1, jem.INTERROGATIVE + jem.DECLARATIVE)
    res = ctp.extend_on_residual(s1, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0],
                                 persist=True, seeds_dir=tmp_path)
    assert res["minted"] and res["persisted"] and all(r["persisted"] for r in res["persisted"])
    ctp.persist_points(s1, category="well_read", seeds_dir=tmp_path)
    # SESSION 2 — a FRESH COLD boot, then RE-INSTALL.
    s2 = _fresh()
    assert ctp.dimensions(s2) == []                    # cold: no axis at boot
    ctp.reinstall_points(s2, category="well_read", seeds_dir=tmp_path)
    n = ctp.reinstall_dimensions(s2, category="minted_dimensions", seeds_dir=tmp_path)
    assert n == 1
    names = [d["name"] for d in ctp.dimensions(s2)]
    assert "minted:question_frac" in names             # the minted axis is present
    # and it STILL separates on the fresh boot.
    d1 = ctp._distances(s2, jem.PROBE_INT)
    assert _min_dist(d1, jem.INT_LBLS) < _min_dist(d1, jem.DEC_LBLS)


def test_reinstall_uses_the_rust_seed_loader():
    src = inspect.getsource(ctp.reinstall_dimensions)
    assert "load_seed_manifest" in src


def test_minted_dir_is_outside_seeds():
    seeds_abs = os.path.abspath(os.path.join(ROOT, "seeds"))
    assert not str(ctp.WELL_READ_DIR).startswith(seeds_abs)


# --------------------------------------------------------------------------- #
#  THE OVER-MINTING DISCIPLINE — no residual mints NOTHING.
# --------------------------------------------------------------------------- #
def test_already_separated_by_a_seed_axis_mints_nothing():
    # two texts a SEED axis (mood/affect) already separates -> the sd loop
    # RECOGNIZES the feature -> NO new axis (the seed axes suffice).
    emo = "The fox came to the river and, glad and full of joy, drank the water with delight."
    neu = "The fox came to the river and drank the water there quietly at the time."
    ag = _fresh()
    res = ctp.extend_on_residual(ag, emo, neu)
    assert res["minted"] is False
    assert res["feature"] == "affect_frac"             # a seed axis
    assert len(ctp.dimensions(ag)) == len(ctp._SEED_DIMENSIONS)   # N unchanged


def test_genuinely_same_texts_mint_nothing():
    ag = _fresh()
    same = "The fox comes to the river. The fox drinks the water. The fox goes home."
    res = ctp.extend_on_residual(ag, same, same)
    assert res["minted"] is False
    assert res["norm_sep"] < ctp._SEP_EPS              # no residual
    assert len(ctp.dimensions(ag)) == len(ctp._SEED_DIMENSIONS)


def test_committed_manifold_is_byte_identical_no_mint():
    # installing the SEED StyleDimension nodes does NOT perturb the default
    # location; and the committed demos never mint (the mint is opt-in).
    ag = _fresh()
    ctp.prime_reader(ag, jwr.FABLES + jwr.TECH)
    committed = ctp.locate(ag, jwr.HELD_OUT)
    ag2 = _fresh()
    ctp.prime_reader(ag2, jwr.FABLES + jwr.TECH)
    ctp.install_style_dimensions(ag2)
    assert ctp.locate(ag2, jwr.HELD_OUT) == committed
    # proximity + context register unchanged too.
    assert ctp.proximity_weights(ag2, jwr.HELD_OUT) == ctp.proximity_weights(ag, jwr.HELD_OUT)
    assert ctp.context_selected_register(ag2, jwr.HELD_OUT, budget=jwr.BUDGET) == \
        ctp.context_selected_register(ag, jwr.HELD_OUT, budget=jwr.BUDGET)


def test_default_boot_has_no_style_dimension_or_stylepoint():
    ag = _fresh()
    assert len(list(ag.s.nodes("StyleDimension"))) == 0
    assert len(ctp.points(ag)) == 0


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — no regex, donkey = 0.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_donkey():
    src = inspect.getsource(ctp)
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re found"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... found"
    for banned in ("openai", "anthropic", "requests.post", "call_model",
                   "self_teacher", "numpy", "torch", "sentence_transformers"):
        assert banned not in src, "donkey/neural token %r found" % banned


def test_minted_dimension_is_graph_resident():
    ag = _fresh()
    ctp.prime_reader(ag, jem.INTERROGATIVE + jem.DECLARATIVE)
    ctp.extend_on_residual(ag, jem.INTERROGATIVE[0][0], jem.DECLARATIVE[0][0])
    node = next(n for n in ag.s.nodes("StyleDimension")
                if ag.s.node(n)["attrs"].get("minted"))
    at = ag.s.node(node)["attrs"]
    # the axis is a graph node carrying its graph-observable feature definition.
    assert at["feature_kind"] == "char_density"
    assert at["feature_key"] == "question_frac"
    assert at["minted"] == 1.0
