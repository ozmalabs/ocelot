"""test_lifelong — THE LIFELONG READER: MORE AXES + BOOT-TIME PERSISTENCE.

Extends the well-read style manifold (domains/cross_text_prior.py) with:
  * MORE AXES — period / mood / formality style dimensions (graph-native
    reference sets, the _CLOSED_CLASS idiom). Same-genre minimal pairs of
    DIFFERENT period/mood/formality locate at DIFFERENT points, nearer their OWN
    sub-cluster; the axes are LOAD-BEARING (an ablation with the axis OFF but the
    same voice representation collapses the separation to genre).
  * BOOT-TIME PERSISTENCE — persist the manifold to a well-read seed and
    RE-INSTALL it on a fresh boot (via the Rust load_seed_manifest). A fresh
    agent that re-installs IS well-read (manifold present at boot) and predicts
    the held-out fable BETTER than a cold boot.

THE HARD GUARD (opt-in): the well-read seed lives OUTSIDE seeds/, so the DEFAULT
boot stays COLD — the committed axes-off behaviour is byte-identical, and the
default seed-set holds no StylePoint.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_lifelong.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import glob
import inspect
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
import jabberwock_is_well_read as jwr                                  # noqa: E402
import jabberwock_is_lifelong as jl                                    # noqa: E402


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


def _top(ag, probe, style_w):
    return [nb["label"] for nb in
            ctp.locate(ag, probe, exclude_style=True, style_w=style_w)["neighbours"][:3]]


# --------------------------------------------------------------------------- #
#  MORE AXES — each axis load-bearing: OFF (voice only) mixed, ON its own cluster.
# --------------------------------------------------------------------------- #
def _axis_loadbearing(cluster_a, cluster_b, probe_a, probe_b):
    ag = _fresh()
    ctp.prime_reader(ag, cluster_a + cluster_b)
    a_lbls = {lb for _t, lb in cluster_a}
    b_lbls = {lb for _t, lb in cluster_b}
    # probe A: ON -> all in A's cluster; OFF -> not purely A (voice pulls B).
    on_a = _top(ag, probe_a, jl.STYLE_W)
    off_a = _top(ag, probe_a, 0.0)
    # probe B: ON -> all in B's cluster.
    on_b = _top(ag, probe_b, jl.STYLE_W)
    return (all(l in a_lbls for l in on_a), all(l in b_lbls for l in on_b),
            not all(l in a_lbls for l in off_a), on_a, off_a, on_b)


def test_period_axis_is_load_bearing():
    on_a, on_b, off_mixed, on_a_l, off_a_l, on_b_l = _axis_loadbearing(
        jl.PERIOD_MODERN, jl.PERIOD_ARCHAIC,
        jl.PERIOD_PROBE_MODERN, jl.PERIOD_PROBE_ARCHAIC)
    assert on_a, "modern probe ON should locate among modern: %s" % on_a_l
    assert on_b, "archaic probe ON should locate among archaic: %s" % on_b_l
    assert off_mixed, "with the axis OFF, voice alone should NOT purely separate: %s" % off_a_l


def test_mood_axis_is_load_bearing():
    on_a, on_b, off_mixed, on_a_l, off_a_l, on_b_l = _axis_loadbearing(
        jl.MOOD_EMO, jl.MOOD_NEUTRAL, jl.MOOD_PROBE_EMO, jl.MOOD_PROBE_NEUTRAL)
    assert on_a, "emotional probe ON should locate among emotional: %s" % on_a_l
    assert on_b, "neutral probe ON should locate among neutral: %s" % on_b_l
    assert off_mixed, "with the axis OFF, voice alone should NOT purely separate: %s" % off_a_l


def test_formality_axis_is_load_bearing():
    # the FORMAL probe is the clean ablation (contraction surface tokens leak a
    # partial voice signal for the casual probe, noted honestly).
    on_a, on_b, _off_mixed, on_a_l, _off_a_l, on_b_l = _axis_loadbearing(
        jl.FORM_CASUAL, jl.FORM_FORMAL, jl.FORM_PROBE_CASUAL, jl.FORM_PROBE_FORMAL)
    assert on_a, "casual probe ON should locate among casual: %s" % on_a_l
    assert on_b, "formal probe ON should locate among formal: %s" % on_b_l
    # the formal probe: OFF is mixed, ON is pure formal — the load-bearing arm.
    ag = _fresh()
    ctp.prime_reader(ag, jl.FORM_CASUAL + jl.FORM_FORMAL)
    off_formal = _top(ag, jl.FORM_PROBE_FORMAL, 0.0)
    for_lbls = {lb for _t, lb in jl.FORM_FORMAL}
    assert not all(l in for_lbls for l in off_formal), \
        "formal probe OFF should be mixed (voice not pure): %s" % off_formal


def test_axis_densities_separate_the_clusters():
    ag = _fresh()
    # archaic text has archaic_frac > 0, modern has 0.
    assert ctp._style_features(ag, jl.PERIOD_ARCHAIC[0][0])["archaic_frac"] > 0
    assert ctp._style_features(ag, jl.PERIOD_MODERN[0][0])["archaic_frac"] == 0
    # emotional text has affect_frac > 0, neutral has 0.
    assert ctp._style_features(ag, jl.MOOD_EMO[0][0])["affect_frac"] > 0
    assert ctp._style_features(ag, jl.MOOD_NEUTRAL[0][0])["affect_frac"] == 0
    # casual has contraction_frac > 0, formal has 0.
    assert ctp._style_features(ag, jl.FORM_CASUAL[0][0])["contraction_frac"] > 0
    assert ctp._style_features(ag, jl.FORM_FORMAL[0][0])["contraction_frac"] == 0


# --------------------------------------------------------------------------- #
#  BOOT-TIME PERSISTENCE — a fresh boot re-installs the manifold and IS well-read.
# --------------------------------------------------------------------------- #
def _confirm(reg) -> float:
    return pr.predict_first_pass(_fresh(), jwr.HELD_OUT,
                                 class_register=reg)["aggregate"]["confirm_frac"]


def _perplexity(reg) -> float:
    return pr.weighted_first_pass(_fresh(), jwr.HELD_OUT,
                                  class_register=reg)["perplexity_weighted"]


def test_reinstall_reinstates_the_manifold_on_a_fresh_boot(tmp_path):
    s1 = _fresh()
    ctp.prime_reader(s1, jwr.FABLES)
    ctp.persist_points(s1, category="well_read", seeds_dir=tmp_path)
    # a FRESH agent boots cold, then re-installs the persisted manifold.
    wr = _fresh()
    assert len(ctp.points(wr)) == 0                     # cold at boot
    n = ctp.reinstall_points(wr, category="well_read", seeds_dir=tmp_path)
    assert n == len(jwr.FABLES)                         # every point re-installed
    assert len(ctp.points(wr)) == len(jwr.FABLES)       # the manifold IS present
    # the re-installed points carry their feature + style coords + word prior.
    rp = ctp.read_point(wr, ctp.points(wr)[0])
    assert set(rp["features"]) >= {"mean_wlen", "ttr"}
    assert set(rp["style_features"]) >= {"archaic_frac", "affect_frac"}
    assert rp["n_word_types"] > 0


def test_well_read_boot_predicts_better_than_cold_boot(tmp_path):
    # SESSION 1 — read + persist.
    s1 = _fresh()
    ctp.prime_reader(s1, jwr.FABLES)
    ctp.persist_points(s1, category="well_read", seeds_dir=tmp_path)
    # SESSION 2 — COLD boot (no seed): empty manifold, empty register.
    cold_conf, cold_ppl = _confirm([]), _perplexity([])
    # SESSION 3 — WELL-READ boot: re-install, then predict with the manifold.
    wr = _fresh()
    ctp.reinstall_points(wr, category="well_read", seeds_dir=tmp_path)
    reg = ctp.context_selected_register(wr, jwr.HELD_OUT, budget=jwr.BUDGET)
    wr_conf, wr_ppl = _confirm(reg), _perplexity(reg)
    assert wr_conf > cold_conf, \
        "well-read boot confirm %.3f should beat cold %.3f" % (wr_conf, cold_conf)
    assert wr_ppl < cold_ppl, \
        "well-read boot perplexity %.1f should beat cold %.1f" % (wr_ppl, cold_ppl)


def test_reinstall_uses_the_rust_seed_loader():
    # the re-install reuses the SAME seed-loader the boot uses (load_seed_manifest).
    src = inspect.getsource(ctp.reinstall_points)
    assert "load_seed_manifest" in src


# --------------------------------------------------------------------------- #
#  DEFAULT-BOOT UNPERTURBED — the well-read seed is OPT-IN (the HARD guard).
# --------------------------------------------------------------------------- #
def test_default_seed_set_holds_no_stylepoint():
    # the persisted manifold must NOT live in seeds/ (which load_all_seeds scans),
    # so it can never enter the default seed-set.
    bad = []
    for f in glob.glob(os.path.join(ROOT, "seeds", "*.json")) + \
            glob.glob(os.path.join(ROOT, "seeds", "generated", "*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict) and any(
                isinstance(n, dict) and n.get("type") == "StylePoint"
                for n in (d.get("nodes") or [])):
            bad.append(os.path.basename(f))
    assert not bad, "seeds/ must hold no StylePoint (found %s)" % bad


def test_well_read_dir_is_outside_seeds():
    seeds_abs = os.path.abspath(os.path.join(ROOT, "seeds"))
    assert not str(ctp.WELL_READ_DIR).startswith(seeds_abs)


def test_default_boot_is_cold():
    assert len(ctp.points(_fresh())) == 0


def test_default_location_is_byte_identical_axes_off():
    # the committed default location (no axes) equals the explicit axes-off call —
    # the new axes are additive and opt-in; the default boot is unperturbed.
    ag = _fresh()
    ctp.prime_reader(ag, jwr.FABLES + jwr.TECH)
    committed = ctp.locate(ag, jwr.HELD_OUT)
    axes_off = ctp.locate(ag, jwr.HELD_OUT, exclude_style=False, style_w=0.0)
    assert committed == axes_off
    # proximity weighting + context register unchanged too.
    assert ctp.proximity_weights(ag, jwr.HELD_OUT) == \
        ctp.proximity_weights(ag, jwr.HELD_OUT, exclude_style=False, style_w=0.0)
    assert ctp.context_selected_register(ag, jwr.HELD_OUT, budget=jwr.BUDGET) == \
        ctp.context_selected_register(ag, jwr.HELD_OUT, budget=jwr.BUDGET,
                                      exclude_style=False, style_w=0.0)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the new axes are reference sets, no regex, donkey=0.
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


def test_style_features_are_graph_resident_on_the_node():
    ag = _fresh()
    node = ctp.accumulate_text(ag, jl.PERIOD_ARCHAIC[0][0], label="x")
    attrs = ag.s.node(node)["attrs"]
    style = json.loads(attrs["style_features"])
    assert set(style) >= {"archaic_frac", "affect_frac", "latinate_frac",
                          "contraction_frac"}
    assert style["archaic_frac"] > 0
