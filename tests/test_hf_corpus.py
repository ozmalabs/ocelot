"""test_hf_corpus — THE WIDER (Hugging Face) CORPUS world adapter (domains/hf_corpus).

A WORLD ADAPTER (CLAUDE.md): stream a BALANCED multi-genre corpus from Hugging
Face, extract each row's natural reading unit, strip dataset boilerplate, and
sequence the units into the style-manifold reader (cross_text_prior). NO agent
decisions — fetch/cache/split/feed only.

Gated (all OFFLINE + deterministic — inline HF-shaped fixtures, NO network):
  * the per-genre extractors pick the field + clean the boilerplate (datelines,
    escape artefacts) on the natural unit;
  * the token loader sets os.environ without leaking the value;
  * read_into_manifold GROWS the manifold one StylePoint per unit;
  * the manifold CLUSTERS by genre on the read units (within << cross);
  * persist round-trips to a tmp seed dir and RE-INSTALLS on a fresh boot,
    never touching the real seeds/ or the default boot (crow-safe);
  * WORLD-ADAPTER audit — no rule engine, no graph-state decisions, donkey=0
    (the only external I/O is a Hugging Face dataset fetch — NOT a model).
  * a REAL-DATA validation runs only when the sampled units are already cached
    (skipped offline), so a fresh checkout stays deterministic.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_hf_corpus.py -p no:randomly -q
"""
from __future__ import annotations

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
from domains import hf_corpus as hf                                   # noqa: E402


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
#  INLINE FIXTURES — tiny HF-row-shaped dicts, one per genre shape (offline).
#  Register-distinct so the manifold clusters: archaic verse, plain narrative,
#  latinate encyclopedic, casual second-person review, digit-heavy news.
# --------------------------------------------------------------------------- #
POETRY_ROWS = [
    {"content": "Thou art the fairest rose of summer's morn,\r\n"
                "Whose gentle bloom doth grace the dewy lawn;\r\n"
                "O love, thy tender grace shall ne'er be gone,\r\n"
                "Though beauty fade and every fair be shorn.",
     "poem name": "To A Rose", "author": "A POET"},
    {"content": "Sweet joy doth fill my heart with tender glee,\r\n"
                "The merry lark sings glad upon the tree;\r\n"
                "O hope, thy gentle light shines fair and free,\r\n"
                "And every bloom doth breathe its love to me.",
     "poem name": "Glad Song", "author": "A POET"},
]
STORY_ROWS = [
    {"text": "One day a little girl found a small dog in the park. The dog was "
             "sad and cold. She gave the dog some bread and took it home. The dog "
             "was happy and they played all day in the warm sun."},
    {"text": "Tom had a red ball. He kicked the ball to his friend Sam. Sam kicked "
             "it back. They ran and laughed in the green grass. When the sun went "
             "down they went home and had warm milk before bed."},
]
WIKI_ROWS = [
    {"title": "Photosynthesis",
     "text": "Photosynthesis is a biological process utilized by numerous organisms "
             "for the conversion of luminous radiation into chemical composition. "
             "The mechanism involves the assimilation of carbon dioxide and the "
             "production of organic compounds through complex metabolic reactions."},
    {"title": "Federalism",
     "text": "Federalism is a political organisation characterised by the "
             "distribution of governmental authority between a central "
             "administration and constituent regional institutions. The "
             "constitutional arrangement establishes concurrent jurisdiction and "
             "delineates the competencies of each administrative division."},
]
REVIEW_ROWS = [
    {"text": "honestly you have to try this place! i can't believe how good the "
             "tacos are. the staff is super friendly and they don't rush you. "
             "you won't regret it, it's my favorite spot in town.", "label": 4},
    {"text": "i don't know what you were thinking coming here. the service was slow "
             "and it isn't worth your money. you'd be better off cooking at home. "
             "i'm never going back, don't waste your time.", "label": 0},
]
NEWS_ROWS = [
    {"text": "Stocks Rally 3 Percent as Oil Falls to 42 Dollars (Reuters) Reuters - "
             "The index climbed 300 points on Tuesday after crude dropped 5 percent "
             "in the 3rd session of the week.", "label": 2},
    {"text": "Team Wins 4 to 1 in Game 7 Final (AP) The visitors scored 3 goals in "
             "the 2nd period to take the title before 40,000 fans on Sunday night.",
     "label": 1},
]


def _genre_units(spec_key, rows):
    spec = next(s for s in hf.GENRES if s["key"] == spec_key)
    out = []
    for r in rows:
        txt = spec["extract"](r)
        if txt and len(txt.split()) >= spec["min_words"]:
            out.append({"source": spec_key, "genre": spec["genre"],
                        "register": spec["register"], "label": spec_key, "text": txt})
    return out


def _mixed_corpus():
    return (_genre_units("poetry", POETRY_ROWS)
            + _genre_units("stories", STORY_ROWS)
            + _genre_units("wikipedia", WIKI_ROWS)
            + _genre_units("reviews", REVIEW_ROWS)
            + _genre_units("news", NEWS_ROWS))


# --------------------------------------------------------------------------- #
#  Extractors — field pick + boilerplate strip on the natural unit.
# --------------------------------------------------------------------------- #
def test_extractors_pick_field_and_clean():
    verse = hf._unit_verse(POETRY_ROWS[0])
    assert "Thou art" in verse and "\r" not in verse       # de-escaped, CR stripped
    wiki = hf._unit_wiki_lead(WIKI_ROWS[0])
    assert wiki.startswith("Photosynthesis") and len(wiki.split()) <= 120
    story = hf._unit_story(STORY_ROWS[0])
    assert "\n" not in story                                # prose collapsed


def test_strip_dateline_cuts_wire_prefix():
    body = "LONDON, England (Reuters) -- Harry Potter star gains a fortune today."
    assert hf._strip_dateline(body).startswith("Harry Potter")
    assert "(CNN)Something happened here in the world today for a while now indeed."
    assert hf._strip_dateline("(CNN) -- Big news broke overnight.").startswith("Big news")


def test_all_genres_extract_a_unit():
    units = _mixed_corpus()
    genres = {u["genre"] for u in units}
    assert {"poetry", "stories", "wikipedia", "reviews", "news"} <= genres
    assert all(u["text"] and set(u) >= {"source", "genre", "label", "text"}
               for u in units)


# --------------------------------------------------------------------------- #
#  Token loader sets os.environ without leaking the value.
# --------------------------------------------------------------------------- #
def test_load_hf_token_no_leak(tmp_path, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    envp = tmp_path / ".env"
    envp.write_text("HF_TOKEN=hf_secret_value_xyz\nOTHER=1\n")
    ok = hf.load_hf_token(env_path=envp)
    # the loader RETURNS a bool, never the value (the value only lives in env).
    assert ok is True and isinstance(ok, bool)
    assert os.environ.get("HF_TOKEN") == "hf_secret_value_xyz"


# --------------------------------------------------------------------------- #
#  read_into_manifold — the manifold grows one StylePoint per unit.
# --------------------------------------------------------------------------- #
def test_read_into_manifold_grows_one_point_per_unit():
    ag = _fresh()
    assert len(ctp.points(ag)) == 0
    units = _mixed_corpus()
    pts = hf.read_into_manifold(ag, units)
    assert len(pts) == len(units) == len(ctp.points(ag))
    genres = {hf.genre_of_label(ag.s.node(n)["attrs"]["label"]) for n in ctp.points(ag)}
    assert {"poetry", "stories", "wikipedia", "reviews", "news"} <= genres


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
    within, cross = ws / wn, cs / cn
    assert cross > within, "genres did not cluster: within %.3f cross %.3f" % (within, cross)


# --------------------------------------------------------------------------- #
#  genre_counts reads the BALANCE off a unit list.
# --------------------------------------------------------------------------- #
def test_genre_counts_reports_balance():
    counts = hf.genre_counts(_mixed_corpus())
    assert set(counts) >= {"poetry", "stories", "wikipedia", "reviews", "news"}
    assert all(v >= 1 for v in counts.values())


# --------------------------------------------------------------------------- #
#  PERSIST — round-trips to a TMP dir + re-installs on a fresh boot.
# --------------------------------------------------------------------------- #
def test_persist_and_reinstall_round_trip(tmp_path):
    ag = _fresh()
    hf.read_into_manifold(ag, _mixed_corpus())
    n = len(ctp.points(ag))
    receipts = ctp.persist_points(ag, category="hf_corpus_test", seeds_dir=tmp_path)
    assert receipts and all(r.get("persisted") for r in receipts)
    seed = tmp_path / "hf_corpus_test.json"
    assert seed.exists()
    manifest = json.loads(seed.read_text())
    assert len([x for x in manifest["nodes"] if x["type"] == "StylePoint"]) == n
    fresh = _fresh()
    assert len(ctp.points(fresh)) == 0
    assert ctp.reinstall_points(fresh, category="hf_corpus_test", seeds_dir=tmp_path) == n
    assert len(ctp.points(fresh)) == n


# --------------------------------------------------------------------------- #
#  WORLD-ADAPTER audit — no rule engine, no graph-state decisions, donkey=0.
# --------------------------------------------------------------------------- #
def test_world_adapter_no_rule_engine_no_donkey():
    src = inspect.getsource(hf)
    for banned in ("graph_rewrite", "make_rule", "gr._match", "gr._apply",
                   "openai", "anthropic", "call_model", "self_teacher",
                   "sentence_transformers", "import torch", "numpy"):
        assert banned not in src, "world-adapter/donkey violation: %r" % banned
    # the only external I/O is a Hugging Face dataset fetch (DATASET ACCESS only).
    assert "datasets" in src and "load_dataset" in src


def test_default_boot_manifold_is_empty():
    # the corpus manifold is opt-in; a default boot never reads it (crow-safe).
    assert len(ctp.points(_fresh())) == 0


# --------------------------------------------------------------------------- #
#  REAL-DATA validation — only when the sampled units are already cached (offline
#  runs skip; a machine with the cache validates the real corpus end-to-end).
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not hf.cache_present(), reason="HF units not cached")
def test_real_corpus_is_balanced_and_clusters():
    units = hf.units_from_cache(cap=150)
    counts = hf.genre_counts(units)
    assert len(counts) == 6                             # six genres
    assert min(counts.values()) == max(counts.values())  # exactly balanced
    ag = _fresh()
    sample = units[::6][:120]                           # a cross-genre slice
    feats = [(u["genre"], ctp._content_freq(ag, u["text"]),
              ctp._register_features(ag, u["text"]),
              ctp._style_features(ag, u["text"])) for u in sample]
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
    assert cs / cn > ws / wn                             # real genres cluster
