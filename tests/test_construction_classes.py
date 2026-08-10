"""CONSTRUCTION-LEARNING IS CLASS-LEARNING (domains/reading_collapse.py +
seeds/reading_constructions.json).

Adding constructions one surface-form at a time is a slower trenchcoat. Naming /
classification / "known as" / "termed" / "described as" / "defined as" are all
INSTANCES of ONE relation — DESIGNATION (a thing bound to what it is CALLED). The
codebook grows by ABSTRACTIONS (marker-classes + constructions over them), not
surface variants; an UNSEEN variant is covered on arrival.

Discriminative gates (donkey=0 — no fit, no LM, WordNet + ShapeDecode only):

  * ONE CLASS COVERS THE FAMILY — called / described as / known as AND an UNSEEN
    'termed' all decode to the SAME `designation` class-construction (marker slot =
    the DESIGNATE member used); the codebook holds ONE designation class, NOT four
    leaves.
  * NEW MARKER JOINS BY ADJACENCY — 'termed' (NOT in the seed member list) is placed
    into DESIGNATE by WordNet nearness to the known members, THEN covered by the
    class-construction — no new leaf minted.
  * CLASS vs LEAF MINT — a residual that shares the designation SHAPE is covered by
    the class (no leaf); a genuinely NOVEL shape mints a new class.
  * BASALT re-read corrected — 'described as scoria' grounds is_a(rock, scoria) and
    'called the europium anomaly' grounds is_a(deviation, europium_anomaly) — NOT
    part_of (the enum artifacts).
  * SOURCE AUDIT — marker-class + class-construction + class-level cover + adjacency
    placement are seed data + the collapse; NO `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_construction_classes.py -p no:randomly -q
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
def _designation_class_count(s) -> int:
    return sum(1 for nd in s.nodes("ShapeSignature")
               if s.node(nd)["attrs"].get("kind") == "construction"
               and s.node(nd)["attrs"].get("class_marker") == "DESIGNATE")


def _learned_leaves(s) -> list:
    return sorted(s.node(nd)["attrs"].get("name") for nd in s.nodes("ShapeSignature")
                  if s.node(nd)["attrs"].get("learned"))


def _seed_designate_forms(s) -> list:
    for nd in s.nodes("MarkerClass"):
        if s.node(nd)["attrs"].get("cls") == "DESIGNATE":
            return [str(f).lower() for f in (s.node(nd)["attrs"].get("forms") or [])]
    return []


def _filled_member(agent, clause: str) -> list:
    from domains import comprehend_text as ct
    _, _, ms = rc._skeleton_from_words(agent, ct._recognise_words(agent, clause))
    return [w for cl, w in ms if cl == "DESIGNATE"]


# --------------------------------------------------------------------------- #
#  ONE CLASS COVERS THE FAMILY (incl. the unseen 'termed').
# --------------------------------------------------------------------------- #
FAMILY = [
    ("a sonnet is called a poem",       "called"),
    ("a sonnet is described as a poem",  "described"),
    ("a sonnet is known as a poem",      "known"),
    ("a sonnet is termed a poem",        "termed"),    # UNSEEN member
]


@pytest.mark.parametrize("clause,member", FAMILY)
def test_one_class_covers_family(agent, clause, member):
    r = rc.read_clause(agent, clause, write=False)
    assert r["construction"] == "designation", (clause, r)
    assert ["is_a", "sonnet", "poem"] in r["predications"], (clause, r["predications"])
    assert not r["minted"], (clause, "a class member must not mint a leaf")
    assert _filled_member(agent, clause) == [member], (clause, "marker slot = member used")


def test_codebook_holds_one_designation_class_not_four_leaves(agent):
    """The whole family decodes through ONE class; the codebook holds ONE designation
    class-construction and MINTS NO leaves for it."""
    for clause, _ in FAMILY:
        rc.read_clause(agent, clause, write=False)
    assert _designation_class_count(agent.s) == 1, "exactly ONE designation class"
    assert _learned_leaves(agent.s) == [], "no per-surface leaves minted for the family"


# --------------------------------------------------------------------------- #
#  NEW MARKER JOINS BY ADJACENCY (the mechanism, not a hardcoded hit).
# --------------------------------------------------------------------------- #
def test_termed_is_not_a_seed_member(agent):
    assert "termed" not in _seed_designate_forms(agent.s), \
        "'termed' must be UNSEEN — it joins by adjacency, not by being on the list"


def test_new_marker_joins_by_adjacency(agent):
    """'termed' is placed into DESIGNATE by WordNet nearness to the known members —
    the nearness signal + score are shown, and no new leaf is minted."""
    ev = rc.adjacency_evidence(agent, "termed")
    assert ev["cls"] == "DESIGNATE", ev
    assert ev["signal"] == "wordnet_path_similarity", ev
    assert ev["nearness"] >= 0.5, ev
    assert ev["nearest_member"] in ("call", "name", "designate", "label"), ev
    # reading it covers by the class-construction — no leaf.
    before = _learned_leaves(agent.s)
    r = rc.read_clause(agent, "a sonnet is termed a poem", write=False)
    assert r["construction"] == "designation" and not r["minted"], r
    assert _learned_leaves(agent.s) == before, "adjacency-join must not mint a leaf"
    # and the surface is now a live member of the class (joined in-graph).
    assert "termed" in _seed_designate_forms(agent.s), "joined into the live class forms"


def test_distributional_gate_polysemous_noun_out_of_slot_stays_content(agent):
    """A polysemous noun with a naming VERB sense ('report' near 'describe', 'point'
    near 'designate') does NOT hijack a clause where it is a NOUN out of the marker
    slot — the distributional gate (post-copular) rejects it. 'the report infers ...'
    must NOT read as designation."""
    r = rc.read_clause(agent, "the report infers that prices will rise", write=False)
    assert r["construction"] != "designation", (r["construction"], r["predications"])
    r2 = rc.read_clause(agent, "a mute point", write=False)
    # 'point' stays content (no post-copular slot), so no designation reading.
    assert r2["construction"] != "designation", (r2["construction"], r2["predications"])
    assert "point" not in _seed_designate_forms(agent.s), "must not have joined out of slot"


def test_adjacency_rejects_non_designation_verb(agent):
    """A content verb ('chased') is NOT near the designation anchor — it stays content
    (the nearness signal discriminates, it is not a blanket 'unknown verb -> join')."""
    ev = rc.adjacency_evidence(agent, "chased")
    assert ev["cls"] is None and ev["nearness"] < 0.5, ev
    r = rc.read_clause(agent, "the cat chased the mouse", write=False)
    assert r["construction"] == "event", r


# --------------------------------------------------------------------------- #
#  CLASS vs LEAF MINT — the abstraction, not a designation-specific hack.
# --------------------------------------------------------------------------- #
def test_designation_shape_residual_covered_by_class_no_leaf(agent):
    """An UNSEEN designation surface ('styled') shares the DESIGNATE shape -> covered
    by the class (marker slot filled), NOT minted as a leaf."""
    assert "styled" not in _seed_designate_forms(agent.s)
    before = _learned_leaves(agent.s)
    r = rc.read_clause(agent, "a sonnet is styled a poem", write=False)
    assert r["construction"] == "designation" and not r["minted"], r
    assert ["is_a", "sonnet", "poem"] in r["predications"], r
    assert _learned_leaves(agent.s) == before, "covered by class -> no leaf"
    assert _designation_class_count(agent.s) == 1


def test_novel_shape_mints_a_new_class(agent):
    """A genuinely NOVEL shape (possessive [OF], unlike any held class) DOES mint a new
    class — the class-vs-leaf discipline, not designation-specific."""
    r = rc.read_clause(agent, "the capital of france", write=False)
    assert r["residual_before"] == [["OF"]], r
    assert r["minted"] is True and r["learned"] is True, r
    assert "learned_of" in _learned_leaves(agent.s), _learned_leaves(agent.s)


# --------------------------------------------------------------------------- #
#  BASALT re-read corrected — the enum's two artifacts become designation is_a.
# --------------------------------------------------------------------------- #
def test_basalt_scoria_is_designation_not_part_of(agent):
    r = rc.read_clause(agent, "the rock is described as scoria", write=False)
    assert r["construction"] == "designation", r
    assert ["is_a", "rock", "scoria"] in r["predications"], r
    for p in r["predications"]:
        assert p[0] != "part_of", ("enum artifact must be gone", p)


def test_basalt_europium_anomaly_is_designation_not_part_of(agent):
    r = rc.read_clause(agent, "the deviation is called the europium anomaly", write=False)
    assert r["construction"] == "designation", r
    assert ["is_a", "deviation", "europium_anomaly"] in r["predications"], r
    for p in r["predications"]:
        assert p[0] != "part_of", ("europium anomaly must be a NAME, not a part", p)


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — graph-native, not enumeration; no regex.
# --------------------------------------------------------------------------- #
def test_no_regex_in_reading_collapse():
    src = open(os.path.join(ROOT, "domains", "reading_collapse.py")).read()
    lines = {ln.strip() for ln in src.splitlines()}
    assert "import re" not in lines and "import re, os" not in lines, \
        "reading must stay recognition-based — no regex"
    assert not any(ln.strip().startswith(("import re ", "import re,")) or ln.strip() == "import re"
                   for ln in src.splitlines()), "no regex import"


def test_mechanism_is_seed_data_and_collapse(agent):
    """The DESIGNATE marker-class + the designation class-construction live as SEED
    graph data (MarkerClass + ShapeSignature nodes), and the winning construction is
    the ShapeDecode verdict — not a per-variant Python branch."""
    s = agent.s
    assert any(s.node(nd)["attrs"].get("cls") == "DESIGNATE" for nd in s.nodes("MarkerClass"))
    assert _designation_class_count(s) == 1
    # the adjacency anchor is DATA on the class node (join-by-adjacency is not a list).
    anchor = None
    for nd in s.nodes("MarkerClass"):
        if s.node(nd)["attrs"].get("cls") == "DESIGNATE":
            anchor = s.node(nd)["attrs"].get("adjacency_anchor")
    assert anchor, "the class declares its adjacency_anchor as data"
