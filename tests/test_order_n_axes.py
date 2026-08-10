"""test_order_n_axes — THE STYLE MANIFOLD ALIGNS BY ORDER-N STRUCTURE, not just
vocabulary (cross_text_prior's structural axes).

The creator's point: 'the axes need to be ORDER N — the vocabulary isn't how
things align only.' The committed manifold located a text by VOCABULARY (bag-of-
content-words cosine) + flat register markers, so two fables were 'near' because
they share lion/fox. This suite gates the ORDER-N structural axes — read from the
reader's own nested comprehension (comprehension_reader.read_and_comprehend):

  * (order-2) CONSTRUCTION — clause/argument-pattern distribution.
  * (order-3) DISCOURSE   — coherence-relation distribution.
  * (order-N) NARRATIVE   — story-grammar arc shape.

Gated claims (all behind the VOCABULARY null, struct_w=0):
  (a) SAME-ARC-DIFFERENT-VOCAB ALIGN — two fables with different animals but the
      same arc locate NEAR on structure though vocabulary-cosine (0 shared words)
      cannot align them; a vocabulary DECOY that shares the held-out fable's words
      wrongly wins on vocabulary but is banished by structure.
  (b) SHARED-VOCAB-DIFFERENT-STRUCTURE SEPARATE — a fable + an encyclopedic text
      sharing content words locate APART on the structural axes.
  (c) LOAD-BEARING per level — NARRATIVE + CONSTRUCTION carry the separation;
      DISCOURSE is honestly weak on short prose.
  (d) REAL CORPUS — order-N alignment clusters by GENRE (scale-free ratio) better
      than the vocabulary-alone baseline.
  * BYTE-IDENTICAL default-off — accumulate_text/locate with structure off store
    the committed StylePoint attrs and never run comprehension.
  * GRAPH-NATIVE — no import re, donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_order_n_axes.py -p no:randomly -q -s
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                               # noqa: E402
from domains import cross_text_prior as ctp                            # noqa: E402
import jabberwock_aligns_by_structure as jabs                          # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# committed StylePoint attr set — the byte-identity anchor (structural adds keys
# ONLY when structural=True).
_COMMITTED_POINT_ATTRS = {"label", "text", "word_counts", "construction_counts",
                          "features", "style_features", "n_word_tokens", "note"}


# --------------------------------------------------------------------------- #
#  (a) SAME-ARC-DIFFERENT-VOCABULARY ALIGN — the headline.
# --------------------------------------------------------------------------- #
def test_a_same_arc_different_vocab_aligns():
    ag = _fresh()
    r = jabs.gate_a_same_arc_different_vocab(ag)
    # the two fables share ZERO content words: vocabulary-cosine cannot align them.
    assert r["vocab_cosine_fableA_fableB"] == 0.0
    assert r["shared_content_words_between_fables"] == []
    # yet STRUCTURE puts them essentially on top of each other.
    assert r["structural_distance_fableA_fableB"] < 0.05
    # THE FLIP: vocabulary picks the structureless decoy; structure picks the fable.
    assert r["vocab_only_nearest"] == "hawk-list-DECOY"
    assert r["structure_nearest"] == "fable-lion"
    # and structure banishes the vocabulary decoy to LAST.
    assert r["structure_ranking"][-1][0] == "hawk-list-DECOY"


# --------------------------------------------------------------------------- #
#  (b) SHARED-VOCABULARY-DIFFERENT-STRUCTURE SEPARATE.
# --------------------------------------------------------------------------- #
def test_b_shared_vocab_different_structure_separates():
    ag = _fresh()
    r = jabs.gate_b_shared_vocab_different_structure(ag)
    # they DO share content words — vocabulary would align them.
    assert r["vocab_cosine"] > 0.4
    assert set(r["shared_content_words"]) >= {"lion", "deer"}
    # structure holds them APART; the NARRATIVE axis is maximal (arc vs no-arc).
    assert r["structural_distance"] > 0.3
    assert r["level_distances"]["narrative"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
#  (c) LOAD-BEARING per level.
# --------------------------------------------------------------------------- #
def test_c_load_bearing_per_level():
    ag = _fresh()
    r = jabs.gate_c_load_bearing_per_level(ag)
    ff = r["fable_vs_fable_levels"]
    fe = r["fable_vs_encyclopedic_levels"]
    # same-arc fables: construction + narrative ~0 (they align at those levels).
    assert abs(ff["construction"]) < 1e-6
    assert abs(ff["narrative"]) < 1e-6
    # fable vs encyclopedic: NARRATIVE + CONSTRUCTION carry the separation.
    assert fe["narrative"] == pytest.approx(1.0)
    assert fe["construction"] > 0.3
    # DISCOURSE is the weak level on short prose (honest) — small on BOTH pairs.
    assert fe["discourse"] < 0.1


# --------------------------------------------------------------------------- #
#  (d) REAL CORPUS — genre clustering (scale-free ratio) beats vocabulary alone.
# --------------------------------------------------------------------------- #
def test_d_real_corpus_genre_clustering():
    ag = _fresh()
    r = jabs.gate_d_real_corpus_clustering(ag, genres=("stories", "news", "wikipedia"),
                                           cap=3)
    if sum(r["n_per_genre"].values()) < 6:
        pytest.skip("hf_corpus cache absent -- real-corpus gate needs data/hf_corpus")
    # cross-genre is farther than within-genre for BOTH metrics (both > 1.0)...
    assert r["vocab_separation_ratio"] > 1.0
    assert r["struct_separation_ratio"] > 1.0
    # ...but STRUCTURE's scale-free separation ratio beats vocabulary's.
    assert r["structure_ratio_beats_vocab"] is True


# --------------------------------------------------------------------------- #
#  BYTE-IDENTICAL default-off (cold == committed).
# --------------------------------------------------------------------------- #
def test_default_off_byte_identical():
    ag = _fresh()
    # accumulate WITHOUT structure -> exactly the committed StylePoint attr set.
    n = ctp.accumulate_text(ag, "A crow found a pitcher.", label="x")
    attrs = set(ag.s.node(n)["attrs"].keys())
    assert attrs == _COMMITTED_POINT_ATTRS
    # locate default-off -> no structural field, no per-neighbour levels, no
    # comprehension pollution (no SmEntity / DiscourseEvent / NarrativeRole minted).
    ctp.accumulate_text(ag, "A fox found a jug.", label="y")
    loc = ctp.locate(ag, "A wolf found a bowl.")
    assert loc["structural"] == {}
    assert all(nb.get("levels") is None for nb in loc["neighbours"])
    for polluting in ("SmEntity", "DiscourseEvent", "NarrativeRole", "Source"):
        assert not list(ag.s.nodes(polluting)), \
            "default-off locate must not run comprehension on the manifold agent"


def test_structural_on_adds_only_structural_keys():
    ag = _fresh()
    n = ctp.accumulate_text(ag, "A hungry lion saw a deer. The lion set a trap. "
                            "The deer fell.", label="z", structural=True)
    attrs = set(ag.s.node(n)["attrs"].keys())
    # committed keys PLUS exactly the three structural-signature keys.
    assert attrs == _COMMITTED_POINT_ATTRS | {"construction_sig", "discourse_sig",
                                              "narrative_sig"}


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE audit — no import re, donkey = 0.
# --------------------------------------------------------------------------- #
def _imports_re(src: str) -> bool:
    for line in src.splitlines():
        s = line.strip()
        if s == "import re" or s.startswith("import re ") or s.startswith("import re,") \
                or s.startswith("from re "):
            return True
    return False


def test_graph_native_no_regex_donkey_zero():
    for mod in (ctp, jabs, sys.modules[__name__]):
        src = inspect.getsource(mod)
        assert not _imports_re(src), f"{mod.__name__} must not import re"
