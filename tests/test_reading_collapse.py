"""Reading = COLLAPSE over a construction codebook (domains/reading_collapse.py).

Discriminative gates for the escape from the enum-only trenchcoat:

  * ARBITRARY TEXT — one clause per seeded construction, each grounded by the SAME
    ShapeDecode over the codebook (not a per-construction Python branch).
  * LEARNS A HELD-OUT CONSTRUCTION (the headline) — a construction NOT in the seed
    codebook (possessive "X of Y") does NOT decode (residual), the sd loop MINTS a
    quantum, this module installs it, and the re-decode GROUNDS it (0 -> N).
  * FAULTY — a garbled clause still grounds the recognisable predication.
  * TVTROPES STRESS — the 5 zero-yield tropes ground N>=3 by definitional decode.
  * WIKIPEDIA LIFT — a definitional lead grounds subject+genus (is_a).
  * GRAPH-NATIVE SOURCE AUDIT — decode is ShapeDecode, the codebook is
    ShapeSignatures, the learn is the seeded sd_* rules; no per-construction regex.
  * NO REGRESSION — the enum path is byte-identical when collapse is not requested.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest tests/test_reading_collapse.py -p no:randomly -q
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
from domains import gap_driven_acquisition as gda    # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  ARBITRARY TEXT — one clause per seeded construction, same decode.
# --------------------------------------------------------------------------- #
BATTERY = [
    ("a sonnet is a lyric poem",                    "definitional",        ["is_a", "sonnet", "lyric_poem"]),
    ("a computer includes a processor and memory",  "enumeration_includes", ["part_of", "processor", "computer"]),
    ("rain because clouds",                         "causal_because",      ["causes", "clouds", "rain"]),
    ("a raven is unlike a desk",                    "comparative_unlike_cop", ["contrast", "raven", "desk"]),
    ("if it rains then the ground is wet",          "conditional",         ["implies", "it_rains", "ground"]),
    ("the cat chased the mouse",                    "event",               ["chased", "cat", "mouse"]),
]


@pytest.mark.parametrize("clause,cons,pred", BATTERY)
def test_arbitrary_text_battery(agent, clause, cons, pred):
    r = rc.read_clause(agent, clause)
    assert r["construction"] == cons, (clause, r)
    assert pred in r["predications"], (clause, r["predications"])
    assert not r["minted"], "a seeded construction must not mint"


def test_battery_is_one_decode_not_per_construction_branches(agent):
    """Every construction is grounded through the SAME entry (read_clause ->
    compose_design_for_goal). The verdicts DIFFER (definitional vs event vs ...)
    yet no branch names them — proof the construction WINS by decode."""
    verdicts = {clause: rc.read_clause(agent, clause)["construction"] for clause, _, _ in BATTERY}
    assert len(set(verdicts.values())) >= 5, verdicts


# --------------------------------------------------------------------------- #
#  THE HEADLINE — learn a held-out construction via the sd loop.
# --------------------------------------------------------------------------- #
def test_learns_held_out_construction(agent):
    # possessive "X of Y" is deliberately NOT in seeds/reading_constructions.json.
    r = rc.read_clause(agent, "the capital of france")
    # BEFORE: no held construction covers the [[OF]] skeleton -> residual.
    assert r["residual_before"] == [["OF"]], r["residual_before"]
    # the sd loop minted a quantum for the residual (the seeded sd_mint_quantum rule).
    assert r["minted"] is True, r
    assert r.get("mint_axis"), r
    # this module installed the skeleton as a NEW construction; re-decode covers it.
    assert r["learned"] is True
    assert r.get("residual_after") == [], r.get("residual_after")
    # AFTER: it now GROUNDS the predication (0 -> N).
    assert r["predications"] == [["of", "capital", "france"]], r["predications"]
    # the learned construction is reused with NO further mint.
    r2 = rc.read_clause(agent, "the king of spain")
    assert r2["minted"] is False
    assert ["of", "king", "spain"] in r2["predications"], r2


def test_learned_construction_is_a_shape_signature(agent):
    rc.read_clause(agent, "the capital of france")
    names = [agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("ShapeSignature")
             if agent.s.node(n)["attrs"].get("kind") == "construction"
             and agent.s.node(n)["attrs"].get("learned")]
    assert any(nm and nm.startswith("learned_") for nm in names), names


# --------------------------------------------------------------------------- #
#  FAULTY — garbled clause still grounds the recognisable predication.
# --------------------------------------------------------------------------- #
def test_faulty_clause_grounds_recognisable_predication(agent):
    r = rc.read_clause(agent, "Chekhov gun be narrative thing where element early it pay off")
    assert r["construction"] is not None
    assert ["is_a", "chekhov_gun", "narrative_thing"] in r["predications"], r["predications"]


# --------------------------------------------------------------------------- #
#  TVTROPES STRESS — 5 zero-yield tropes now ground N>=3.
# --------------------------------------------------------------------------- #
TROPES = {
    "chekhovsgun": "A Chekhov's Gun is a narrative device, an object introduced early in the story, which becomes significant later.",
    "bigbad": "The Big Bad is the primary antagonist, a villain who drives the central conflict of the story.",
    "deusexmachina": "A Deus Ex Machina is an implausible plot device, a sudden intervention that abruptly resolves the conflict.",
    "redshirt": "A Redshirt is an expendable character, a minor figure who exists to die and establish danger.",
    "abandonedarea": "An Abandoned Area is a deserted location, a ruined place that evokes decay and isolation.",
}


@pytest.mark.parametrize("name,defn", list(TROPES.items()))
def test_tvtropes_zero_to_n(agent, name, defn):
    src = {"text": defn, "lead": defn, "title": name}
    enum = gda.extract_microtheory(name, src)              # enum-only path
    col = rc.concepts_from_reading(agent, name, src)       # reading-by-collapse
    assert len(enum["concepts"]) == 0, (name, enum["concepts"])   # BEFORE: 0
    assert len(col["concepts"]) >= 3, (name, col["concepts"])     # AFTER: N>=3
    # the definitional decode grounded the subject's is_a genus.
    assert any(p[0] == "is_a" for p in col["predications"]), col["predications"]


# --------------------------------------------------------------------------- #
#  WIKIPEDIA LIFT — a definitional lead grounds subject+genus.
# --------------------------------------------------------------------------- #
def test_wikipedia_lead_grounds_subject_genus(agent):
    lead = "A volcano is a rupture in the crust of a planetary object that allows hot lava to escape."
    src = {"text": lead, "lead": lead, "title": "volcano"}
    col = rc.concepts_from_reading(agent, "volcano", src)
    isa = [p for p in col["predications"] if p[0] == "is_a" and p[1] == "volcano"]
    assert isa and isa[0][2].startswith("rupture"), col["predications"]


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT.
# --------------------------------------------------------------------------- #
def test_source_audit_no_per_construction_regex():
    with open(os.path.join(ROOT, "domains", "reading_collapse.py")) as f:
        src = f.read()
    # the decode is the ShapeDecode collapse op (via compose_design_for_goal), the
    # learn is induce_concern (the seeded sd_* rules) — not a regex/if-else parser.
    assert "compose_design_for_goal" in src
    assert "induce_concern" in src
    # no regex module at all — reading is by recognition + decode, never a pattern.
    assert "\nimport re\n" not in src and "\nimport re " not in src
    for bad in ("re.compile", "re.search", "re.match", "re.findall", "re.split", "re.sub"):
        assert bad not in src, bad


def test_codebook_is_shape_signatures(agent):
    rc.ensure_codebook(agent)
    cons = [agent.s.node(n)["attrs"] for n in agent.s.nodes("ShapeSignature")
            if agent.s.node(n)["attrs"].get("kind") == "construction"]
    assert len(cons) >= 10, len(cons)
    # each carries a data-driven role->predication template (never a Python branch).
    assert all(c.get("ground_template") for c in cons)


# --------------------------------------------------------------------------- #
#  NO REGRESSION — the enum path is untouched when collapse is not requested.
# --------------------------------------------------------------------------- #
def test_enum_path_unchanged_without_collapse():
    src = {"text": "A pipeline consists of stages: preprocessing, parsing, and codegen.",
           "lead": "A pipeline consists of stages.", "title": "pipeline"}
    base = gda.extract_microtheory("pipeline", src)
    same = gda.extract_microtheory("pipeline", src, collapse_agent=None)
    assert [c["name"] for c in base["concepts"]] == [c["name"] for c in same["concepts"]]
    assert base["collapse_concepts"] == []
