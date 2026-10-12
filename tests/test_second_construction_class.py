"""A SECOND CONSTRUCTION CLASS FROM SEED DATA ALONE — the abstraction proven
NOT designation-specific (domains/reading_collapse.py + domain_data/reading_constructions.json).

The designation class (is_a) proved construction-learning is class-learning. This
gate proves the SAME machinery admits a SECOND, DIFFERENT-RELATION class with ZERO
new decision code: POSSESSION — a thing bound to a PROPERTY it HAS (exhibits /
possesses / features / bears / evinces) -> has_property(subject, property). The class
is pure SEED DATA (a MarkerClass + ONE class-construction ShapeSignature); the ONLY
reading_collapse.py touch is a one-line set-membership add of the class symbol to
`_SKELETON` (a data-ish generic add, NOT a second-class branch/function).

Discriminative gates (donkey=0 — no fit, no LM, WordNet + ShapeDecode only):

  * ZERO-CODE-CHANGE — reading_collapse.py has NO possession function and NO
    possession branch; the class symbol 'POSSESS' appears there exactly ONCE (the
    `_SKELETON` membership). The class + construction are seed graph data.
  * FAMILY -> ONE CLASS — exhibits / possesses / features / bears AND an UNSEEN
    'evinces' all decode to the SAME `possession` class-construction grounding
    has_property (NOT is_a); the codebook holds ONE possession class, 0 leaves.
  * UNSEEN JOINS BY ADJACENCY — 'evinces' (NOT in the seed forms) is placed into
    POSSESS by WordNet nearness to the members (in the main-verb slot); a content
    verb ('chased'/'runs') is rejected (nearness < threshold).
  * CLASS vs LEAF — a residual sharing the possession shape is covered by the class
    (no leaf); a novel shape ([OF]) mints a leaf.
  * DESIGNATION COEXIST — a designation clause still reads is_a, a possession clause
    reads has_property; NO cross-firing between the two classes.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_second_construction_class.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core          # noqa: E402
from domains import reading_collapse as rc          # noqa: E402
from domains import comprehend_text as ct           # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    s, node = boot_core()
    a = _Agent(s, node)
    rc.ensure_codebook(a)
    return a


# --------------------------------------------------------------------------- #
#  helpers — codebook introspection (graph reads).
# --------------------------------------------------------------------------- #
def _possession_class_count(s) -> int:
    return sum(1 for nd in s.nodes("ShapeSignature")
               if s.node(nd)["attrs"].get("kind") == "construction"
               and s.node(nd)["attrs"].get("class_marker") == "POSSESS")


def _learned_leaves(s) -> list:
    return sorted(s.node(nd)["attrs"].get("name") for nd in s.nodes("ShapeSignature")
                  if s.node(nd)["attrs"].get("learned"))


def _seed_possess_forms(s) -> list:
    for nd in s.nodes("MarkerClass"):
        if s.node(nd)["attrs"].get("cls") == "POSSESS":
            return [str(f).lower() for f in (s.node(nd)["attrs"].get("forms") or [])]
    return []


def _filled_member(agent, clause: str) -> list:
    _, _, ms = rc._skeleton_from_words(agent, ct._recognise_words(agent, clause))
    return [w for cl, w in ms if cl == "POSSESS"]


# --------------------------------------------------------------------------- #
#  ZERO-CODE-CHANGE (the headline) — no possession function, no possession branch.
# --------------------------------------------------------------------------- #
def test_no_second_class_code_path_in_reading_collapse():
    """The class is SEED DATA. reading_collapse.py must contain no possession-named
    function/branch; the class symbol 'POSSESS' may appear there ONLY as the one-line
    `_SKELETON` set membership (a data-ish add, not a code path)."""
    src = open(os.path.join(ROOT, "domains", "reading_collapse.py")).read()
    assert "possession" not in src.lower(), "no possession-named logic in reading_collapse.py"
    assert src.count("POSSESS") == 1, \
        "'POSSESS' may appear ONLY once — the _SKELETON set-membership add"
    # and that single occurrence is a QUOTED set-member literal, not a def/branch.
    for ln in src.splitlines():
        if "POSSESS" in ln:
            assert '"POSSESS"' in ln, ("must be a quoted set-member literal", ln)
            assert "def " not in ln and ln.strip().startswith('"'), \
                ("must be a set member on a continuation line, not a branch/def", ln)


def test_second_class_is_seed_data():
    """The POSSESS marker-class + the possession class-construction live as SEED graph
    data (MarkerClass + ShapeSignature nodes), mirroring designation."""
    s, node = boot_core()
    a = _Agent(s, node)
    rc.ensure_codebook(a)
    assert any(s.node(nd)["attrs"].get("cls") == "POSSESS" for nd in s.nodes("MarkerClass"))
    assert _possession_class_count(s) == 1
    anchor = None
    for nd in s.nodes("MarkerClass"):
        if s.node(nd)["attrs"].get("cls") == "POSSESS":
            anchor = s.node(nd)["attrs"].get("adjacency_anchor")
    assert anchor, "the class declares its adjacency_anchor as data"


# --------------------------------------------------------------------------- #
#  FAMILY -> ONE CLASS (incl. the unseen 'evinces').
# --------------------------------------------------------------------------- #
FAMILY = [
    ("a diamond exhibits hardness",      "exhibits"),
    ("a diamond possesses hardness",     "possesses"),
    ("a diamond features hardness",      "features"),
    ("a diamond bears hardness",         "bears"),
    ("a diamond demonstrates hardness",  "demonstrates"),   # UNSEEN member (joins by adjacency)
]


@pytest.mark.parametrize("clause,member", FAMILY)
def test_family_decodes_to_one_possession_class(agent, clause, member):
    r = rc.read_clause(agent, clause, write=False)
    assert r["construction"] == "possession", (clause, r)
    assert ["has_property", "diamond", "hardness"] in r["predications"], (clause, r["predications"])
    assert not r["minted"], (clause, "a class member must not mint a leaf")
    assert _filled_member(agent, clause) == [member], (clause, "marker slot = member used")
    # the RIGHT relation — NOT designation's is_a.
    assert all(p[0] != "is_a" for p in r["predications"]), (clause, "must not be is_a")


def test_codebook_holds_one_possession_class_not_five_leaves(agent):
    for clause, _ in FAMILY:
        rc.read_clause(agent, clause, write=False)
    assert _possession_class_count(agent.s) == 1, "exactly ONE possession class"
    assert _learned_leaves(agent.s) == [], "no per-surface leaves minted for the family"


# --------------------------------------------------------------------------- #
#  UNSEEN JOINS BY ADJACENCY (the mechanism, not a hardcoded hit).
# --------------------------------------------------------------------------- #
def test_unseen_is_not_a_seed_member(agent):
    assert "demonstrates" not in _seed_possess_forms(agent.s), \
        "'demonstrates' must be UNSEEN — it joins by adjacency, not by being on the list"


def test_unseen_member_joins_by_adjacency(agent):
    """'demonstrates' (a genuine non-anchor exhibit-family verb) is placed into POSSESS
    by WordNet nearness to the members — the nearness signal + score are shown, and no
    new leaf is minted."""
    ev = rc.adjacency_evidence(agent, "demonstrates")
    assert ev["cls"] == "POSSESS", ev
    assert ev["signal"] == "wordnet_path_similarity", ev
    assert ev["nearness"] >= 0.7, ev
    assert ev["nearest_member"] in ("exhibit", "display", "manifest"), ev
    before = _learned_leaves(agent.s)
    r = rc.read_clause(agent, "a diamond demonstrates hardness", write=False)
    assert r["construction"] == "possession" and not r["minted"], r
    assert ["has_property", "diamond", "hardness"] in r["predications"], r
    assert _learned_leaves(agent.s) == before, "adjacency-join must not mint a leaf"
    assert "demonstrates" in _seed_possess_forms(agent.s), "joined into the live class forms"


def test_adjacency_rejects_content_verb(agent):
    """A content verb ('chased') is NOT near the possession anchor — it stays content
    and reads as an event; the nearness signal discriminates (not 'unknown verb -> join')."""
    ev = rc.adjacency_evidence(agent, "chased")
    assert ev["cls"] is None, ev
    r = rc.read_clause(agent, "the cat chased the mouse", write=False)
    assert r["construction"] == "event", r


def test_adjacency_threshold_rejects_mid_similarity_content(agent):
    """A content verb at MID similarity ('runs' ~0.5) is below the 0.7 threshold and is
    rejected — the threshold, not a hardcoded list, does the discrimination."""
    ev = rc.adjacency_evidence(agent, "runs")
    assert ev["cls"] is None, ("0.5 < 0.7 threshold must reject", ev)
    assert "runs" not in _seed_possess_forms(agent.s), "must not have joined"


def test_polysemy_dodge_no_overfire_on_aux_or_noun(agent):
    """The anchor is chosen to dodge polysemy (the honest cost of possession's weak
    main-verb-slot gate): the auxiliary 'have' (WordNet-synonym of possess/bear) and
    the noun 'point' (its indicate-verb sense is a 'show' synonym) must NOT join POSSESS
    — otherwise 'could have done' / 'a mute point' would mis-read as possession."""
    assert rc.adjacency_evidence(agent, "have")["cls"] != "POSSESS"
    assert rc.adjacency_evidence(agent, "point")["cls"] != "POSSESS"
    r = rc.read_clause(agent, "a mute point", write=False)
    assert r["construction"] != "possession", (r["construction"], r["predications"])


# --------------------------------------------------------------------------- #
#  CLASS vs LEAF MINT — the abstraction, not a possession-specific hack.
# --------------------------------------------------------------------------- #
def test_possession_shape_covered_by_class_no_leaf(agent):
    """An UNSEEN possession surface ('displays') shares the POSSESS shape -> covered by
    the class, NOT minted as a leaf."""
    assert "displays" not in _seed_possess_forms(agent.s)
    before = _learned_leaves(agent.s)
    r = rc.read_clause(agent, "a metal displays conductivity", write=False)
    assert r["construction"] == "possession" and not r["minted"], r
    assert ["has_property", "metal", "conductivity"] in r["predications"], r
    assert _learned_leaves(agent.s) == before, "covered by class -> no leaf"
    assert _possession_class_count(agent.s) == 1


def test_novel_shape_still_mints_a_leaf(agent):
    """A genuinely NOVEL shape ([OF]) still mints a leaf — the class-vs-leaf discipline
    is unchanged by adding the possession class."""
    r = rc.read_clause(agent, "the capital of france", write=False)
    assert r["residual_before"] == [["OF"]], r
    assert r["minted"] is True and r["learned"] is True, r
    assert "learned_of" in _learned_leaves(agent.s), _learned_leaves(agent.s)


# --------------------------------------------------------------------------- #
#  DESIGNATION COEXIST — the two classes ground different relations, no cross-fire.
# --------------------------------------------------------------------------- #
def test_designation_unaffected_by_possession(agent):
    r = rc.read_clause(agent, "a sonnet is called a poem", write=False)
    assert r["construction"] == "designation", r
    assert ["is_a", "sonnet", "poem"] in r["predications"], r


def test_two_classes_do_not_cross_fire(agent):
    """A designation clause reads is_a; a possession clause reads has_property; neither
    is misread as the other."""
    d = rc.read_clause(agent, "a sonnet is called a poem", write=False)
    p = rc.read_clause(agent, "a diamond exhibits hardness", write=False)
    assert d["construction"] == "designation" and p["construction"] == "possession", (d, p)
    assert d["construction"] != p["construction"]
    assert ["is_a", "sonnet", "poem"] in d["predications"]
    assert ["has_property", "diamond", "hardness"] in p["predications"]
    # a possession member is not near the designation anchor, and vice versa.
    assert rc.adjacency_evidence(agent, "displays")["cls"] != "DESIGNATE"
    assert rc.adjacency_evidence(agent, "called")["cls"] != "POSSESS"
    # the auxiliary 'have' does NOT join possession (the anchor excludes possess/bear
    # precisely so the WordNet-synonymous aux 'have'/'has' cannot over-fire).
    assert rc.adjacency_evidence(agent, "have")["cls"] != "POSSESS"
