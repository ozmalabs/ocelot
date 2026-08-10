"""discourse_coherence — coherence relations (marked + unmarked) and causal-
network centrality (Trabasso & van den Broek: central events = highest degree
over the causes/before/coherence_rel graph).

Discriminative gates (donkey = 0, no LLM):

  * MARKED — a discourse connective ('therefore'/'however') leads the decode.
  * UNMARKED — no connective; the situation-model-style signal (shared entity +
    change-of-state / telic-result verb) decodes the SAME relation.
  * MARKED == UNMARKED — the SAME two events decode to the SAME relation
    ('cause') whether the marker is present or not — proves it's not
    marker-regex.
  * DISCRIMINATIVE — two unrelated sentences (no marker, no shared entity) mint
    NO coherence relation.
  * CENTRALITY — a short causal chain's hinge event(s) rank above peripheral
    orientation/resolution sentences by Argmax-picked degree.
  * GRAPH-NATIVE — no `import re`; the relation is ShapeDecode's verdict, the
    central node is Argmax's verdict, never a Python if/else or max()/sorted().

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_discourse_coherence.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                # noqa: E402
from domains import dictionary_lexicon as dl             # noqa: E402
from domains import discourse_coherence as dc             # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  MARKED coherence relations.
# --------------------------------------------------------------------------- #
def test_marked_cause_therefore():
    ag = _fresh()
    r = dc.coherence_between(ag, "It was raining.", "Therefore the match was cancelled.")
    print("MARKED CAUSE:", r)
    assert r["relation"] == "cause"
    assert r["trigger"].startswith("marked:DISC_CAUSE")


def test_marked_contrast_however():
    ag = _fresh()
    r = dc.coherence_between(ag, "The house was cheap.", "However, it was far.")
    print("MARKED CONTRAST:", r)
    assert r["relation"] == "contrast"
    assert r["trigger"].startswith("marked:DISC_CONTRAST")


# --------------------------------------------------------------------------- #
#  UNMARKED coherence relation — situation-model-style signal, no connective.
# --------------------------------------------------------------------------- #
def test_unmarked_cause_or_sequence():
    ag = _fresh()
    r = dc.coherence_between(ag, "She trained daily.", "She won the race.")
    print("UNMARKED (she trained / she won):", r)
    assert r["trigger"].startswith("unmarked:")
    assert r["relation"] in ("cause", "sequence")
    # this specific pair — spanB's verb ('won') is a TELIC_RESULT achievement
    # verb + shared entity 'she' — is designed to reach 'cause'.
    assert r["relation"] == "cause"


# --------------------------------------------------------------------------- #
#  MARKED == UNMARKED — the SAME two events, same relation, marker present vs
#  absent — proves the decode is not marker-regex.
# --------------------------------------------------------------------------- #
def test_marked_and_unmarked_converge_on_same_relation():
    ag1 = _fresh()
    unmarked = dc.coherence_between(ag1, "She trained daily.", "She won the race.")
    ag2 = _fresh()
    marked = dc.coherence_between(ag2, "She trained daily.", "Therefore she won the race.")
    print("UNMARKED:", unmarked)
    print("MARKED:  ", marked)
    assert unmarked["relation"] == marked["relation"] == "cause"
    assert unmarked["trigger"].startswith("unmarked:")
    assert marked["trigger"].startswith("marked:")


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — unrelated adjacent sentences mint NO spurious relation.
# --------------------------------------------------------------------------- #
def test_discriminative_no_spurious_relation():
    ag = _fresh()
    r = dc.coherence_between(ag, "The cat slept on the mat.",
                              "Stock prices rose sharply in Tokyo.")
    print("DISCRIMINATIVE (unrelated):", r)
    assert r["relation"] is None
    assert r["trigger"] == "none"


# --------------------------------------------------------------------------- #
#  CONDITION — bonus coverage (leading 'if'/'unless' on the second span).
# --------------------------------------------------------------------------- #
def test_marked_condition_if():
    ag = _fresh()
    r = dc.coherence_between(ag, "It might rain today.", "If it rains, we will cancel the match.")
    print("MARKED CONDITION:", r)
    assert r["relation"] == "condition"


# --------------------------------------------------------------------------- #
#  CENTRALITY — a short causal chain; the hinge ranks above peripheral detail.
# --------------------------------------------------------------------------- #
_CROW_STORY = (
    "The crow was thirsty. "
    "The crow found a pitcher. "
    "The pitcher held water. "
    "The crow dropped pebbles in the pitcher. "
    "The water in the pitcher rose. "
    "The crow was able to drink."
)


def test_centrality_hinge_ranks_above_periphery():
    ag = _fresh()
    read = dc.read_discourse(ag, _CROW_STORY, window=2)
    print("PAIRS:")
    for p in read["pairs"]:
        print(" ", p["i"], p["j"], p["trigger"], "->", p["relation"])
    ranking = dc.centrality_ranking(ag)
    print("CENTRALITY RANKING (most central first):")
    for row in ranking["ranking"]:
        print("  degree=%d  %s" % (row["degree"], row["label"]))
    print("argmax_winner:", ranking["argmax_winner"],
          "matches top-of-sort:", ranking["argmax_matches_top_of_sort"])

    # the Argmax-picked winner IS the top of the (display-only) sorted ranking.
    assert ranking["argmax_matches_top_of_sort"]
    rows = ranking["ranking"]
    assert len(rows) == 6
    top_label = rows[0]["label"]
    # the hinge (dropped pebbles / water rose) ranks at or above the peripheral
    # orientation/resolution sentences (thirsty / able to drink).
    assert "dropped pebbles" in top_label or "rose" in top_label
    assert rows[0]["degree"] > rows[-1]["degree"]
    peripheral_texts = [r for r in rows if "thirsty" in r["label"] or "able to drink" in r["label"]]
    hinge_texts = [r for r in rows if "dropped pebbles" in r["label"] or "rose" in r["label"]]
    assert hinge_texts and peripheral_texts
    assert max(h["degree"] for h in hinge_texts) > min(p["degree"] for p in peripheral_texts)


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the relation is ShapeDecode's verdict, the
#  central node is Argmax's verdict; no regex, no Python if/else naming a
#  relation, no Python max()/sorted() picking the central node.
# --------------------------------------------------------------------------- #
def test_source_audit_graph_native():
    src = open(os.path.join(ROOT, "domains", "discourse_coherence.py")).read()
    import re as _re
    assert not _re.search(r"^\s*import re\b", src, _re.M)
    assert "re.compile(" not in src and "re.match(" not in src and "re.search(" not in src
    # the coherence-relation decode is a real ShapeDecode Term call.
    assert '"type": "ShapeDecode"' in src
    assert "_CODEBOOK_TYPE" in src and "ShapeSignatureCoherence" in src
    # the centrality WINNER is an Argmax Term call, not a Python max()/sorted().
    assert '"type": "Argmax"' in src
    assert '"type": "Count"' in src and '"type": "Neighbours"' in src
    # `sorted()`/`.sort(` (Python) appears ONLY in the display-only ranking
    # function, and ONLY after the Argmax winner has already been computed —
    # i.e. it never decides the relation or the central node, it orders print
    # output the same way gap_prioritiser.rank_gaps does (see that module's
    # own docstring for the identical precedent).
    assert "def centrality_ranking(" in src
    ranking_fn = src[src.index("def centrality_ranking("):]
    assert "most_central(agent" in ranking_fn.split("rows.sort")[0]


def test_source_audit_no_regression_in_reused_faculties():
    # this module calls reading_collapse / situation_model_reader machinery
    # AS-IS; confirm the calls are present (no local re-implementation).
    src = open(os.path.join(ROOT, "domains", "discourse_coherence.py")).read()
    assert "rc._marker_lexicon(" in src
    assert "rc._skeleton_from_words(" in src
    assert "rc.read_clause(" in src
    assert "rc._split_sentences(" in src
    assert "smr.cos_membership(" in src
    assert "smr.ensure_seeds(" in src
