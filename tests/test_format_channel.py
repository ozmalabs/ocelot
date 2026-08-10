"""test_format_channel — FORMAT AS A GENERIC SIGNAL CHANNEL, decoded by collapse.

The reader had ONLY prosody (the meter faculty) and so MISTOOK a hard-wrapped
Grimm tale for verse — a MEDIUM signal (a file laid out for an ~80-column
terminal) read as PROSODY (format-as-content). This gate asserts the generic
FORMAT faculty: a ShapeDecode collapse over a layout-function codebook
(seeds/format_channel.json) that decodes the format FUNCTION at order-N scales,
so prosody becomes ONE member of a general faculty, not the default reading of
any multi-line block.

The discriminator is FUNCTION, not line length:
  · MEDIUM   — line breaks FORCED by a width limit (wrap_pressure high), no rhyme
  · PROSODY  — breaks fall SHORT of the width (voluntary) + a regular rhyme scheme
  · STRUCTURE— leading whitespace (indentation = nesting / code)
  · REGISTER — a plain block (a letter/note): free breaks, no rhyme, no indent

CONSEQUENCE (the headline): the RAW hard-wrapped Grimm corpus (no manual newline
normalization) now decodes as MEDIUM -> the AGENT reflows it -> the verse-
misdetection dissolves -> the coref/antagonist chain FIRES on the RAW corpus
(vs task-115's masked raw baseline). Format reflow carries ALL FOUR tales to an
opposition/conflict antagonist. 'The Travelling Musicians' USED to rest at the honest
limit `agency+salience` — its conflict-object is the singular pronoun 'him' the
number-aware coref would not bind to the plural 'robbers'. The self-growth descent
surfaced that floor (bridging anaphora was NOT BUILT) and grew the minimal
set-membership primitive, so the pronoun now individuates a `member_of` the group and
the agent's own arc-opposition Argmax re-derives `opposition` DURING reading
(jabberwock_grounds_the_travelling_musicians + test_bridging_anaphora_migrated).

donkey = 0 (no LLM), no `import re` (features are a character scan), graph-native
(the classification is the ShapeDecode verdict, a Format node is recorded).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_format_channel.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                        # noqa: E402
from domains import dictionary_lexicon as dl                     # noqa: E402
from domains import format_channel as fc                         # noqa: E402
import domains.reading_corpus as rc                              # noqa: E402


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
#  FIXTURE TEXTS — real Grimm (medium wrap), verse (prosody), code, letter.
# --------------------------------------------------------------------------- #
JABBERWOCKY = (
    "'Twas brillig, and the slithy toves\n"
    "Did gyre and gimble in the wabe:\n"
    "All mimsy were the borogoves,\n"
    "And the mome raths outgrabe.\n"
    "Beware the Jabberwock, my son!\n"
    "The jaws that bite, the claws that catch!\n"
    "Beware the Jubjub bird, and shun\n"
    "The frumious Bandersnatch!"
)
SONNET = (
    "Shall I compare thee to a summer's day?\n"
    "Thou art more lovely and more temperate:\n"
    "Rough winds do shake the darling buds of May,\n"
    "And summer's lease hath all too short a date:\n"
    "Sometime too hot the eye of heaven shines,\n"
    "And often is his gold complexion dimm'd;\n"
    "And every fair from fair sometime declines,\n"
    "By chance or nature's changing course untrimm'd"
)
CODE = (
    "def solve(xs):\n"
    "    total = 0\n"
    "    for x in xs:\n"
    "        if x > 0:\n"
    "            total += x\n"
    "    return total"
)
LETTER = (
    "Dear Sir,\n\n"
    "I am writing to inform you that the shipment has arrived.\n"
    "Please find enclosed the invoice for your records.\n\n"
    "Yours faithfully,\n"
    "J. Smith"
)
# The crow fable — a single newline-free block (the byte-identity guard).
CROW = (
    "In a spell of dry weather, when the Birds could find very little to "
    "drink, a thirsty Crow found a pitcher with a little water in it. "
    "But the pitcher was high and had a narrow neck, and no matter how he "
    "tried, the Crow could not reach the water."
)


def _grimm():
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    return {u["label"]: u["text"] for u in rc.load_units(sources=grimm)}


# --------------------------------------------------------------------------- #
#  (a) FORMAT-AS-SIGNAL — the 80-char Grimm wrap = MEDIUM; verse = PROSODY.
# --------------------------------------------------------------------------- #
def test_grimm_hard_wrap_decodes_as_medium_not_verse():
    """The RAW hard-wrapped Grimm tale is a file laid out for a terminal: it
    decodes as MEDIUM (is_prosody=False), NOT verse. This is the misdetection
    that swamped coref — dissolved by reading the layout as a signal channel."""
    ag = _fresh()
    by = _grimm()
    for lbl in ("THE TRAVELLING MUSICIANS", "OLD SULTAN",
                "CAT AND MOUSE IN PARTNERSHIP", "THE DOG AND THE SPARROW"):
        v = fc.decode_format(ag, by[lbl], record=False)
        assert v["format"] == "medium", (lbl, v)
        assert v["is_prosody"] is False, (lbl, v)


def test_verse_decodes_as_prosody():
    """Jabberwocky and a Shakespeare sonnet decode as PROSODY (is_prosody=True):
    the line breaks are format-AS-content (rhythm), kept for the meter faculty."""
    ag = _fresh()
    for name, text in (("jabberwocky", JABBERWOCKY), ("sonnet", SONNET)):
        v = fc.decode_format(ag, text, record=False)
        assert v["format"] == "prosody", (name, v)
        assert v["is_prosody"] is True, (name, v)


# --------------------------------------------------------------------------- #
#  (b) PROSODY vs MEDIUM by FUNCTION, not length — the constructed pair.
# --------------------------------------------------------------------------- #
def test_prosody_vs_medium_by_function_not_length():
    """A constructed pair proves the discriminator is FUNCTION, not line length:
    hard-wrapped prose at col ~70 (breaks width-FORCED, no rhyme) -> MEDIUM;
    verse at col ~32 (breaks short + regular rhyme) -> PROSODY."""
    wrapped_prose = (
        "The old miller lived beside the river with his three sons and a\n"
        "single donkey, and every morning before the sun had climbed above\n"
        "the hills he would load the sacks of grain onto the patient beast\n"
        "and lead it slowly down the winding road toward the busy market."
    )
    verse = (
        "The cat sat on the mat,\n"
        "and watched a passing rat,\n"
        "it wore a tiny hat,\n"
        "and that was simply that."
    )
    ag = _fresh()
    w = fc.decode_format(ag, wrapped_prose, record=False)
    v = fc.decode_format(ag, verse, record=False)
    assert w["format"] == "medium", w
    assert v["format"] == "prosody", v
    # the verse lines are SHORTER than the medium lines, yet FUNCTION decides:
    assert v["features"]["max_len"] < w["features"]["max_len"]


# --------------------------------------------------------------------------- #
#  (c)+(d) GENERIC (>=3 kinds) + ORDER-N (format signal at >=2 scales).
# --------------------------------------------------------------------------- #
def test_generic_at_least_three_format_kinds():
    """A GENERIC decoder, not a verse gate: medium + prosody + structure(code)
    + register(letter) — four distinct format FUNCTIONS from one codebook."""
    ag = _fresh()
    kinds = {
        fc.decode_format(ag, _grimm()["OLD SULTAN"], record=False)["format"],
        fc.decode_format(ag, JABBERWOCKY, record=False)["format"],
        fc.decode_format(ag, CODE, record=False)["format"],
        fc.decode_format(ag, LETTER, record=False)["format"],
    }
    assert {"medium", "prosody", "structure", "register"} <= kinds, kinds


def test_order_n_format_at_multiple_scales():
    """Format is order-N: the FILE/MEDIUM scale (wrap_pressure — is the file laid
    out for a column) and the LINE/PROSODY scale (local_rhyme — do endings track a
    scheme) and the DOCUMENT/STRUCTURE scale (indent — nesting) are DIFFERENT
    scales of one faculty, and each is the deciding token for a different format."""
    ag = _fresh()
    med = fc.decode_format(ag, _grimm()["OLD SULTAN"], record=False)
    pro = fc.decode_format(ag, JABBERWOCKY, record=False)
    cod = fc.decode_format(ag, CODE, record=False)
    # file scale distinguishes medium; line scale distinguishes prosody; doc scale code.
    assert med["tokens"][0] == "wrap_forced"     # FILE/MEDIUM scale
    assert pro["tokens"][1] == "rhyme_reg"        # LINE/PROSODY scale
    assert cod["tokens"][2] == "indent_yes"       # DOCUMENT/STRUCTURE scale


# --------------------------------------------------------------------------- #
#  REFLOW — the agent unwraps MEDIUM by its OWN verdict; PROSODY keeps breaks.
# --------------------------------------------------------------------------- #
def test_medium_reflows_prosody_keeps_line_breaks():
    """The verdict DRIVES perception: a MEDIUM file's wrapped newlines are SOFT,
    so the agent reflows them into flowing prose (fewer newlines); a PROSODY
    file's line breaks are CONTENT, kept intact."""
    ag = _fresh()
    med = fc.reflow(ag, _grimm()["OLD SULTAN"])
    pro = fc.reflow(ag, JABBERWOCKY)
    assert med["reflowed"] is True
    assert med["text"].count("\n") < _grimm()["OLD SULTAN"].count("\n")
    assert pro["reflowed"] is False
    assert pro["text"] == JABBERWOCKY


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTITY (hard guard) — a single block is untouched.
# --------------------------------------------------------------------------- #
def test_crow_is_not_prosody_and_reflow_is_identity():
    """The crow fable is a single newline-free block: it is NOT prosody, and the
    reflow is the IDENTITY on it (nothing to unwrap) — the byte-identity guard."""
    ag = _fresh()
    v = fc.decode_format(ag, CROW, record=False)
    assert v["is_prosody"] is False
    r = fc.reflow(ag, CROW)
    assert r["text"] == CROW


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE + donkey=0 — the classification is a ShapeDecode; no regex.
# --------------------------------------------------------------------------- #
def test_records_a_format_node():
    """The format signal is HELD in the graph parallel to the content: decoding
    records a `Format` node carrying the function + is_prosody + the features."""
    ag = _fresh()
    fc.decode_format(ag, _grimm()["OLD SULTAN"], record=True)
    fmts = [ag.s.node(n)["attrs"] for n in ag.s.nodes("Format")]
    assert any(f.get("format") == "medium" for f in fmts), fmts


def test_no_regex_and_shapedecode_source_audit():
    """donkey=0 / graph-native audit: format_channel does NOT `import re` (features
    are a character scan) and DELEGATES the classification to the ShapeDecode
    (compose_design_for_goal), never a Python format table."""
    src = open(os.path.join(ROOT, "domains", "format_channel.py")).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name != "re" for a in node.names), "no import re"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "no from re import"
    assert "compose_design_for_goal" in src           # the ShapeDecode collapse
    assert "ShapeSignatureFormat" not in src or "compose_design_for_goal" in src


# --------------------------------------------------------------------------- #
#  THE HEADLINE CONSEQUENCE — the raw-corpus chain FIRES (opposition on all 4).
# --------------------------------------------------------------------------- #
def test_raw_corpus_antagonist_flips_to_opposition():
    """The verified-correct MECHANISM consequence: on the RAW hard-wrapped corpus
    (jt.run(), NO manual normalization) the agent decodes the wrap as MEDIUM and
    reflows it, so the coref/antagonist chain FIRES on real text — vs task-115's
    masked raw baseline. Format reflow carries ALL FOUR tales to a bound opposition/
    conflict antagonist. 'The Travelling Musicians' USED to rest at the honest limit
    `agency+salience` — its conflict-object is a singular pronoun 'him' the
    number-aware coref would not bind to the plural 'robbers'. The self-growth
    descent surfaced that floor (bridging anaphora was NOT BUILT) and authored the
    minimal set-membership primitive: 'him' now INDIVIDUATES a `member_of` the salient
    plural group and the member's conflict propagates to the group, so the agent's OWN
    arc-opposition Argmax re-derives `opposition` DURING reading (see
    jabberwock_grounds_the_travelling_musicians + test_bridging_anaphora_migrated).
    (The antagonist NAMING rides on the parse/coref layer below format — a separate
    frontier — so only the decided_by mechanism is asserted, not the junk names.)"""
    import jabberwock_reads_a_tale as jt
    recs = {r["label"]: r for r in jt.run()}
    assert recs["OLD SULTAN"]["arc_antagonist"]["decided_by"] == "opposition"
    assert recs["THE DOG AND THE SPARROW"]["arc_antagonist"]["decided_by"] == "opposition"
    assert recs["CAT AND MOUSE IN PARTNERSHIP"]["arc_antagonist"]["decided_by"] in (
        "conflict", "opposition")
    # The fourth NO LONGER rests at agency+salience: the bridging primitive the descent
    # grew binds the pronoun-heavy conflict to the group, so it reaches opposition too.
    assert recs["THE TRAVELLING MUSICIANS"]["arc_antagonist"]["decided_by"] == "opposition"
