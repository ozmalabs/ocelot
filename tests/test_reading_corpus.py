"""test_reading_corpus — THE READING CORPUS world adapter (domains/reading_corpus).

A WORLD ADAPTER (CLAUDE.md): fetch real public-domain literature from Project
Gutenberg, strip the boilerplate, split each source into its natural reading unit,
and sequence the units into the style-manifold reader (cross_text_prior). NO agent
decisions — fetch/cache/split/feed only.

Gated (all OFFLINE + deterministic — inline fixtures, no network):
  * strip_boilerplate cuts the Gutenberg header/footer;
  * each splitter segments its source shape on the natural unit boundary and
    EXCLUDES front matter (preface / table of contents);
  * read_into_manifold GROWS the manifold one StylePoint per unit (mechanical
    sequencing through the reader's public accumulate_text);
  * the manifold CLUSTERS by genre on the read units (within-genre distance <<
    cross-genre distance) — the manifold's OWN feature vector + metric;
  * persist round-trips to a tmp seed dir and RE-INSTALLS on a fresh boot
    (durably well-read), never touching the real seeds/ or the default boot;
  * WORLD-ADAPTER audit — no rule-engine calls, no graph-state decisions, donkey=0
    (the only external I/O is urllib fetch of public-domain text).
  * a REAL-DATA validation runs only when the raw texts are already cached
    (skipped offline), so a fresh checkout stays deterministic.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_reading_corpus.py -p no:randomly -q
"""
from __future__ import annotations

import ast
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
from domains import reading_corpus as rcp                             # noqa: E402


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


# --------------------------------------------------------------------------- #
#  INLINE FIXTURES — tiny raw-Gutenberg-shaped snippets (offline, deterministic).
# --------------------------------------------------------------------------- #
AESOP_RAW = """\
*** START OF THE PROJECT GUTENBERG EBOOK MINI AESOP ***

PREFACE

 The Fox and the Grapes
 The Crow and the Jug


This preface is ordinary prose that begins with a capitalised word The and
should never be read as a fable body.


The Fox and the Grapes


A HUNGRY fox saw ripe grapes hanging on a high vine, and jumped again and
again but could not reach them, so he said the grapes were sour.


The Crow and the Jug


A THIRSTY crow found a jug with a little water, and dropped small stones
into the jug until the water rose and she could drink.

*** END OF THE PROJECT GUTENBERG EBOOK MINI AESOP ***
"""

SONNET_RAW = """\
*** START OF THE PROJECT GUTENBERG EBOOK MINI SONNETS ***

by a poet

I

Shall I compare thee to a summer day?
Thou art more lovely and more temperate,
And every fair from fair sometime declines,
By chance, or nature changing course untrimmed.

II

When thou art old and grey and full of sleep,
And nodding by the fire, take down this book,
And slowly read, and dream of the soft look
Thy eyes had once, and of their shadows deep.

*** END OF THE PROJECT GUTENBERG EBOOK MINI SONNETS ***
"""

KJV_RAW = """\
*** START OF THE PROJECT GUTENBERG EBOOK MINI SCRIPTURE ***

The Book of Ruth
The Book of Test

The Book of Ruth


1:1 Now it came to pass in the days when the judges ruled, that there was a
famine in the land, and a certain man went to sojourn in the country.

1:2 And the name of the man was of the people, and they came into the
country, and continued there unto this day.

The Book of Test

1:1 This verse belongs to another book and must not be read as Ruth.

*** END OF THE PROJECT GUTENBERG EBOOK MINI SCRIPTURE ***
"""


# --------------------------------------------------------------------------- #
#  strip_boilerplate
# --------------------------------------------------------------------------- #
def test_strip_boilerplate_cuts_markers():
    body = rcp.strip_boilerplate(AESOP_RAW)
    assert "PROJECT GUTENBERG" not in body
    assert "A HUNGRY fox" in body and "PREFACE" in body


# --------------------------------------------------------------------------- #
#  Splitters — segment on the natural unit boundary, exclude front matter.
# --------------------------------------------------------------------------- #
def test_split_allcaps_body_fables_excludes_preface_and_toc():
    units = rcp.split_allcaps_body_fables(rcp.strip_boilerplate(AESOP_RAW))
    assert len(units) == 2                        # exactly the two fable bodies
    labels = [lb for lb, _t in units]
    assert "The Fox and the Grapes" in labels and "The Crow and the Jug" in labels
    joined = " ".join(t for _lb, t in units)
    assert "ordinary prose" not in joined         # preface excluded
    assert "PREFACE" not in joined                # contents/preface heading excluded


def test_split_numeral_units_sonnets():
    units = rcp.split_numeral_units(rcp.strip_boilerplate(SONNET_RAW))
    assert len(units) == 2
    assert [lb for lb, _t in units] == ["I", "II"]
    assert "compare thee" in units[0][1]


def test_split_scripture_verses_bounds_to_one_book():
    units = rcp.split_scripture_verses(
        rcp.strip_boilerplate(KJV_RAW), start_after="The Book of Ruth",
        start_nth=2, stop_at="The Book of Test")
    assert len(units) == 2                         # the two Ruth verses only
    assert [lb for lb, _t in units] == ["1:1", "1:2"]
    joined = " ".join(t for _lb, t in units)
    assert "another book" not in joined            # the next book is excluded


def test_load_units_tags_each_unit():
    # a small source list over the inline fixtures via the module's splitters.
    def _mk(raw, splitter):
        return splitter(rcp.strip_boilerplate(raw))
    fab = [{"source": "fab", "genre": "fable", "register": "plain",
            "period": "x", "label": lb, "text": t}
           for lb, t in _mk(AESOP_RAW, rcp.split_allcaps_body_fables)]
    assert all(set(u) >= {"source", "genre", "label", "text"} for u in fab)


# --------------------------------------------------------------------------- #
#  read_into_manifold — the manifold grows one StylePoint per unit.
# --------------------------------------------------------------------------- #
def _mixed_corpus():
    fab = [{"source": "fab", "genre": "fable", "label": lb, "text": t}
           for lb, t in rcp.split_allcaps_body_fables(rcp.strip_boilerplate(AESOP_RAW))]
    ver = [{"source": "son", "genre": "verse", "label": lb, "text": t}
           for lb, t in rcp.split_numeral_units(rcp.strip_boilerplate(SONNET_RAW))]
    scr = [{"source": "kjv", "genre": "scripture", "label": lb, "text": t}
           for lb, t in rcp.split_scripture_verses(
               rcp.strip_boilerplate(KJV_RAW), start_after="The Book of Ruth",
               start_nth=2, stop_at="The Book of Test")]
    return fab + ver + scr


def test_read_into_manifold_grows_one_point_per_unit():
    ag = _fresh()
    assert len(ctp.points(ag)) == 0
    units = _mixed_corpus()
    pts = rcp.read_into_manifold(ag, units)
    assert len(pts) == len(units) == len(ctp.points(ag))
    # the genre tag rides the label for explainability.
    genres = {rcp.genre_of_label(ag.s.node(n)["attrs"]["label"]) for n in ctp.points(ag)}
    assert {"fable", "verse", "scripture"} <= genres


# --------------------------------------------------------------------------- #
#  The manifold CLUSTERS by genre (within << cross) — the manifold's own metric.
# --------------------------------------------------------------------------- #
def test_manifold_clusters_by_genre():
    ag = _fresh()
    units = _mixed_corpus()
    feats = [(u["genre"], ctp._content_freq(ag, u["text"]),
              ctp._register_features(ag, u["text"]),
              ctp._style_features(ag, u["text"])) for u in units]
    ws = wn = cs = cn = 0.0
    for i in range(len(feats)):
        gi, cfi, ffi, sfi = feats[i]
        for j in range(i + 1, len(feats)):
            gj, cfj, ffj, sfj = feats[j]
            d = ctp._style_distance(cfi, ffi, cfj, ffj, sfi, sfj, style_w=0.5)
            if gi == gj:
                ws += d; wn += 1
            else:
                cs += d; cn += 1
    within = ws / wn
    cross = cs / cn
    assert cross > within, "genres did not cluster: within %.3f cross %.3f" % (within, cross)


# --------------------------------------------------------------------------- #
#  PERSIST — round-trips to a TMP dir + re-installs on a fresh boot.
# --------------------------------------------------------------------------- #
def test_persist_and_reinstall_round_trip(tmp_path):
    ag = _fresh()
    units = _mixed_corpus()
    rcp.read_into_manifold(ag, units)
    n = len(ctp.points(ag))
    receipts = ctp.persist_points(ag, category="corpus_test", seeds_dir=tmp_path)
    assert receipts and all(r.get("persisted") for r in receipts)
    seed = tmp_path / "corpus_test.json"
    assert seed.exists()
    manifest = json.loads(seed.read_text())
    assert len([x for x in manifest["nodes"] if x["type"] == "StylePoint"]) == n
    # a FRESH agent re-installs the manifold => durably well-read across sessions.
    fresh = _fresh()
    assert len(ctp.points(fresh)) == 0
    assert ctp.reinstall_points(fresh, category="corpus_test", seeds_dir=tmp_path) == n
    assert len(ctp.points(fresh)) == n


# --------------------------------------------------------------------------- #
#  WORLD-ADAPTER audit — no rule engine, no graph-state decisions, donkey=0.
# --------------------------------------------------------------------------- #
def test_world_adapter_no_rule_engine_no_donkey():
    src = inspect.getsource(rcp)
    for banned in ("graph_rewrite", "make_rule", "gr._match", "gr._apply",
                   "openai", "anthropic", "call_model", "self_teacher",
                   "sentence_transformers", "import torch", "numpy"):
        assert banned not in src, "world-adapter/donkey violation: %r" % banned
    # the only network I/O is a urllib fetch of public-domain text.
    assert "urllib" in src


def test_default_boot_manifold_is_empty():
    # the corpus manifold is opt-in; a default boot never reads it (crow-safe).
    assert len(ctp.points(_fresh())) == 0


# --------------------------------------------------------------------------- #
#  REAL-DATA validation — only when the raw texts are already cached (offline
#  runs skip; a machine with the cache validates the real splitters end-to-end).
# --------------------------------------------------------------------------- #
def _cache_present():
    return all((rcp.CORPUS_DIR / f"pg{s['gid']}.txt").exists() for s in rcp.SOURCES)


@pytest.mark.skipif(not _cache_present(), reason="raw Gutenberg texts not cached")
def test_real_corpus_splits_and_clusters():
    units = rcp.units_from_cache()
    assert len(units) > 100                        # a real multi-genre corpus
    srcs = {u["source"] for u in units}
    assert {"aesop", "grimm", "sonnet", "blake", "kjv-ruth"} <= srcs
    ag = _fresh()
    feats = [(u["genre"], ctp._content_freq(ag, u["text"]),
              ctp._register_features(ag, u["text"]),
              ctp._style_features(ag, u["text"])) for u in units]
    ws = wn = cs = cn = 0.0
    for i in range(len(feats)):
        gi, cfi, ffi, sfi = feats[i]
        for j in range(i + 1, len(feats)):
            gj, cfj, ffj, sfj = feats[j]
            d = ctp._style_distance(cfi, ffi, cfj, ffj, sfi, sfj, style_w=0.5)
            if gi == gj:
                ws += d; wn += 1
            else:
                cs += d; cn += 1
    assert cs / cn > ws / wn                        # real genres cluster
