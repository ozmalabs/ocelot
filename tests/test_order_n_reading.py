"""ORDER-N RECURSIVE READING — the descent is the SAME collapse recursed.

domains/reading_collapse.read_clause grounds a clause's TOP-LEVEL construction at
ORDER 1. Some of the arguments it fills carry RESIDUAL STRUCTURE (a coordinated
LIST 'A, B and C', the compound [FROM],[OF] causal tail, a nested relative clause).
Per the sd-loop principle 'a remainder goes to more detail', a structured argument
is a residual that decodes at ORDER N+1 into its constituents. read_clause_order_n
reuses the order-1 machinery (the marker lexicon, the glue split, the construction's
own relation) at a finer grain — NOT a new extractor, NOT the enum cue-regex.

Discriminative gates (donkey=0, no LLM):

  * SYNTHETIC MECHANISM — an enumeration list descends into per-member part_of; a
    nested relative-clause enumeration grounds part_of to the subject; both with
    CLEAN single-nominal members.
  * CLEAN SPANS + COMPOUND TAIL — the Basalt lead grounds is_a(basalt, igneous_rock)
    with a CLEAN genus head (nominal_head_term/WordNet compound, NOT the order-1
    participle salad) and grounds the [FROM],[OF] compound tail by descent.
  * TERMINATES + NO OVER-DESCENT — a plain-nominal argument is NOT recursed
    (depth 1); order-N is ADDITIVE / opt-in (max_order=1 == order-1 only).
  * BASALT READER-ALONE (enum UNUSED) — the order-N reader over the Basalt body
    reproduces the enum path's members as part_of by recursing into the enumeration
    constructions, WITHOUT invoking gap_driven_acquisition.extract_microtheory.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_order_n_reading.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core           # noqa: E402
from domains import reading_collapse as rc           # noqa: E402
from domains import dictionary_lexicon as dl         # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module")
def agent():
    dl.warm_wordnet("en")          # the clean-head compound lookup reads WordNet
    s, node = boot_core()
    return _Agent(s, node)


def _preds(agent, clause, **kw):
    return rc.read_clause_order_n(agent, clause, write=False, **kw)


# --------------------------------------------------------------------------- #
#  SYNTHETIC MECHANISM — enumeration list descent + nested relative clause.
# --------------------------------------------------------------------------- #
def test_enumeration_list_descends_to_clean_members(agent):
    """'a computer includes a processor, memory, and storage' — order 1 merges the
    comma list ('processor_memory'); order-N descends the LIST argument into THREE
    clean members, each part_of the head. This is the enum's members, principled."""
    r = _preds(agent, "a computer includes a processor, memory, and storage")
    assert r["members"] == ["processor", "memory", "storage"]
    on = r["order_n_predications"]
    assert ["part_of", "processor", "computer"] in on
    assert ["part_of", "memory", "computer"] in on
    assert ["part_of", "storage", "computer"] in on
    assert r["depth"] == 2


def test_nested_relative_clause_enumeration(agent):
    """'water is a liquid that contains hydrogen and oxygen' — is_a(water, liquid)
    at order 1; the relative-clause enumeration descends to part_of(member, SUBJECT)
    for each member (the 'that' refers back through the genus to the subject)."""
    r = _preds(agent, "water is a liquid that contains hydrogen and oxygen")
    on = r["order_n_predications"]
    assert ["is_a", "water", "liquid"] in on
    assert ["part_of", "hydrogen", "water"] in on
    assert ["part_of", "oxygen", "water"] in on
    assert r["members"] == ["hydrogen", "oxygen"]


# --------------------------------------------------------------------------- #
#  CLEAN SPANS + COMPOUND TAIL — the Basalt lead.
# --------------------------------------------------------------------------- #
BASALT_LEAD = ("Basalt is an aphanitic fine-grained extrusive igneous rock formed "
               "from the rapid cooling of low-viscosity lava rich in magnesium and iron")


def test_clean_genus_head_not_participle_salad(agent):
    """The order-1 genus is the flat NP 'aphanitic_..._igneous_rock_formed'; order-N
    cleans it to the single held nominal 'igneous_rock' (a WordNet compound) via the
    held POS + lexical faculties — NOT a regex, NOT the participle salad."""
    r = _preds(agent, BASALT_LEAD)
    assert r["genus"] == "igneous_rock"
    assert ["is_a", "basalt", "igneous_rock"] in r["order_n_predications"]
    # the order-1 salad is what order-N REPLACES (proof it was noisy before descent).
    salad = r["order1"]["predications"]
    assert salad and salad[0][2].startswith("aphanitic")


def test_compound_tail_grounded_by_descent(agent):
    """The compound lead's [FROM],[OF] residual — dangling at order 1 — is grounded
    by descent as marker predications over clean heads (no longer a bare residual)."""
    r = _preds(agent, BASALT_LEAD)
    assert r["order1"]["residual"], "order-1 leaves a [FROM],[OF] residual"
    rels = {p[0] for p in r["compound_tail"]}
    assert "from" in rels
    # the FROM predication ties the clean genus to the cooling process.
    assert ["from", "igneous_rock", "cooling"] in r["order_n_predications"]


# --------------------------------------------------------------------------- #
#  TERMINATES + NO OVER-DESCENT — a plain nominal is not recursed.
# --------------------------------------------------------------------------- #
def test_plain_nominal_not_recursed(agent):
    """'gold is a metal' — a plain-nominal genus with NO residual structure is NOT
    recursed: depth stays 1, no members, no compound tail (no runaway descent)."""
    r = _preds(agent, "gold is a metal")
    assert r["order_n_predications"] == [["is_a", "gold", "metal"]]
    assert r["depth"] == 1
    assert r["members"] == [] and r["compound_tail"] == []


def test_order_n_is_additive_opt_in(agent):
    """max_order=1 == the order-1 read only (no descent): the descent is ADDITIVE.
    The single-order read_clause behaviour is preserved."""
    r1 = _preds(agent, BASALT_LEAD, max_order=1)
    assert r1["order_n_predications"] == []
    assert r1["depth"] == 1
    # read_clause itself is unchanged — still grounds the order-1 is_a.
    base = rc.read_clause(agent, BASALT_LEAD, write=False)
    assert base["construction"] == "definitional"
    assert base["predications"][0][:2] == ["is_a", "basalt"]


# --------------------------------------------------------------------------- #
#  BASALT READER-ALONE — reproduce the enum members, enum path UNUSED.
# --------------------------------------------------------------------------- #
def _wiki_agent():
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        from domains import reading_review as rr
        ag = WorldAdapter(seeds=())
        load_all_seeds(ag)
        rr.ensure_review_seed(ag)
        dl.warm_wordnet("en")
    return ag


def test_basalt_reader_alone_reproduces_enum_members():
    """READER ALONE over the Basalt body reproduces the enum path's members as
    part_of by recursing into the enumeration constructions — WITHOUT invoking the
    enum cue extractor. Reproduces a strong majority of the enum's 22 members
    (token-level) AND finds many clean members the enum missed."""
    from domains import wiki_local as wl
    if not wl.present():
        pytest.skip("wiki_local corpus not present")
    import contextlib
    import io
    from domains import gap_driven_acquisition as gda
    from domains.gap_driven_acquisition import _first_sentence

    s = wl.summary("Basalt")
    text = s["text"]
    ag = _wiki_agent()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        rt = rc.read_text_order_n(ag, text, write=False)
    reader = set(rt["members"])

    # the enum path is used ONLY as the side-by-side reference — not by the reader.
    src = {"found": True, "text": text, "lead": _first_sentence(text),
           "title": "Basalt", "source": "fed_document"}
    enum = {c["name"] for c in gda.extract_microtheory("basalt", src, max_concepts=30,
                                                       nominal_filter=True)["concepts"]}

    def _toks(n):
        return set(n.split("_"))

    reproduced = {en for en in enum if any(rm == en or rm in _toks(en) or (_toks(rm) & _toks(en))
                                           for rm in reader)}
    # the calcium/sodium/magnesium enumeration is the canonical reproduced list.
    assert {"calcium", "sodium", "magnesium"} <= reader
    # a strong majority of the enum's members are reproduced by the reader alone.
    assert len(reproduced) >= 15, (len(reproduced), sorted(reproduced))
    # and the reader EXCEEDS the enum (clean members the cue-regex missed).
    assert len(reader) > len(enum)
