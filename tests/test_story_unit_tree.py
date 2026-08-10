"""test_story_unit_tree — MOVE 2a: a story's NESTED structure is recognised as a
StoryUnit TREE via a StoryBoundary collapse (a ShapeDecode over inter-sentence
seams), one level up from narrative_structure's per-sentence role collapse.

ADDITIVE RECOGNITION ONLY: the tree is minted; NO faculty is unit-scoped, NO
comprehension changes (that is MOVE 2b). This gate proves:

  * PRECISION-SAFE — the single-arc crow is NOT split (a false boundary is worse
    than a missed one); its goal-driven analysis report stays BYTE-IDENTICAL.
  * NESTED — a two-episode fable with a temporal-shift seam and a frame narrative
    with an embedded-narrative marker each yield a 2+-unit tree, root + children,
    each child carrying its sentence span + the boundary signal that split it.
  * GRAPH-NATIVE — the boundary is the ShapeDecode's verdict over graph signals;
    no Python paragraph/blank-line/regex splitter; no `import re`; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_story_unit_tree.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import story_tree as st                                   # noqa: E402
import jabberwock_story_tree as jst                                    # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402


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
#  PRECISION-SAFE — the single-arc crow is NOT split (depth-1, root only).
# --------------------------------------------------------------------------- #
def test_crow_is_a_single_depth1_unit():
    ag = _fresh()
    tree = st.recognize_story_tree(ag, jst.CROW)
    jst.print_tree("CROW (precision-safe)", tree)
    assert tree["depth"] == 1
    assert tree["children"] == []
    assert not tree["boundaries"], "a false boundary split the single-arc crow"
    # every seam is the honest null token -- no schema covers it.
    assert all(sm["token"] == "SEAM_NONE" and sm["boundary"] is None
               for sm in tree["seams"])
    # the root spans ALL six sentences.
    assert tree["root"]["span_start"] == 0 and tree["root"]["span_end"] == 5
    assert tree["root"]["n_sentences"] == 6
    # read back off the graph: exactly one StoryUnit, the root.
    rb = st.read_story_tree(ag)
    assert rb["root"] is not None and rb["children"] == []


# the crow's goal-driven analysis report, FROZEN — MOVE 2a is additive
# recognition, so the comprehension->analysis flow is byte-for-byte unchanged.
_CROW_REPORT = (
    "Summary. The story follows a crow, which is thirsty. Its central difficulty, "
    "the most causally connected event, is that the crow cannot reach the water. "
    "In the end, the water rose, and the crow drink.\n\n"
    "Narrative structure. In the setup, the crow found the pitcher. The problem is "
    "that the crow cannot reach the water. The solution comes when the crow dropped "
    "the pebble. In the resolution, the water rose, and the crow drink.\n\n"
    "Technique. Through its problem and indirect structure, the story instantiates "
    "MacGyvering (INGENUITY_OVER_STRENGTH). Through its incremental and resolution "
    "structure, the story instantiates Determinator (PERSISTENCE_PAYS).\n\n"
    "Theme. Read from the trope(s) it instantiates, the story's theme is: Ingenuity "
    "overcomes an obstacle that force could not -- cleverness over strength. Small "
    "repeated efforts accumulate into success -- little by little, persistence pays.")


def test_crow_report_byte_identical_move_2a_is_additive():
    report = jpafg.analyse(jpafg.CROW)["report"]
    assert report == _CROW_REPORT, (
        "MOVE 2a changed the crow report -- it must be additive recognition only")


# --------------------------------------------------------------------------- #
#  NESTED — a two-episode fable (temporal-shift seam) -> a 2-unit tree.
# --------------------------------------------------------------------------- #
def test_two_episode_fable_temporal_shift_splits_into_two_units():
    ag = _fresh()
    tree = st.recognize_story_tree(ag, jst.LION_MOUSE)
    jst.print_tree("LION & MOUSE (temporal-shift seam)", tree)
    assert tree["depth"] == 2
    # exactly one boundary, of the temporal-shift kind, at the 'Some time later' seam.
    assert len(tree["boundaries"]) == 1
    b = tree["boundaries"][0]
    assert b["boundary"] == "temporal_shift"
    assert b["position"] == 2                 # before sentence 2 ('Some time later, ...')
    # two child units partition the story: episode 1 [0..1], episode 2 [2..4].
    kinds = [(c["span_start"], c["span_end"], c["boundary_signal"]) for c in tree["children"]]
    assert kinds == [(0, 1, "story_start"), (2, 4, "temporal_shift")]
    # the split child carries the temporal marker as its OPENING sentence.
    ep2 = tree["children"][1]
    assert "some time later" in ep2["sentences"][0].lower()


# --------------------------------------------------------------------------- #
#  NESTED — a frame narrative (embedded-narrative marker) -> a 2-unit tree with
#  a nested 'embedded' child.
# --------------------------------------------------------------------------- #
def test_frame_narrative_embedded_marker_splits_off_embedded_unit():
    ag = _fresh()
    tree = st.recognize_story_tree(ag, jst.FRAME)
    jst.print_tree("FRAME + EMBEDDED", tree)
    assert tree["depth"] == 2
    assert len(tree["boundaries"]) == 1
    b = tree["boundaries"][0]
    assert b["boundary"] == "embedded_narrative"
    assert b["position"] == 2                 # after 'He told the children a story.'
    # the frame opening [0..1] + the embedded tale [2..4], tagged 'embedded'.
    child_kinds = [(c["kind"], c["span_start"], c["span_end"]) for c in tree["children"]]
    assert child_kinds == [("opening", 0, 1), ("embedded", 2, 4)]
    # the telling sentence stays in the frame opening; the reported story is embedded.
    assert "told" in tree["children"][0]["sentences"][1].lower()
    assert "crow" in " ".join(tree["children"][1]["sentences"]).lower()


# --------------------------------------------------------------------------- #
#  ARC-DISCONTINUITY — read off the already-minted NarrativeRole arc (a
#  resolution/consequence role then a fresh setup/problem role across the seam),
#  a boundary WITHOUT any surface temporal marker. Representation-bound: fires
#  only when the arc has been minted upstream (synthetic here, the crow-gate
#  precedent for a node-marker-driven signal).
# --------------------------------------------------------------------------- #
def test_arc_discontinuity_boundary_from_minted_narrative_roles():
    ag = _fresh()
    st.ensure_codebook(ag)
    ag.s.add_node("NarrativeRole", {"entity": "lion", "order": 1, "role": "resolution"})
    ag.s.add_node("NarrativeRole", {"entity": "lion", "order": 2, "role": "setup"})
    text = "A lion hunted. The lion was full. A storm rolled in. The lion hid."
    tree = st.recognize_story_tree(ag, text)
    jst.print_tree("ARC-DISCONTINUITY (synthetic arc, no temporal marker)", tree)
    assert tree["depth"] == 2
    assert [b["boundary"] for b in tree["boundaries"]] == ["arc_discontinuity"]
    assert tree["boundaries"][0]["position"] == 2
    # honest null WITHOUT the arc: same text, no minted roles -> NO boundary.
    ag2 = _fresh()
    bare = st.recognize_story_tree(ag2, text)
    assert bare["depth"] == 1 and not bare["boundaries"], (
        "arc-discontinuity fired without a minted arc -- it must be "
        "representation-bound on the upstream NarrativeRole nodes")


# --------------------------------------------------------------------------- #
#  DECODE DISCRIMINATION — a known boundary token wins with fit>0; an unknown
#  token (SEAM_NONE) covers no schema (honest null). The verdict is the decode's.
# --------------------------------------------------------------------------- #
def test_decode_seam_is_the_shapedecode_verdict():
    ag = _fresh()
    for tok, exp in (("TEMPORAL_SHIFT", "temporal_shift"),
                     ("EMBEDDED_NARRATIVE", "embedded_narrative"),
                     ("ARC_DISCONTINUITY", "arc_discontinuity")):
        dec = st.decode_seam(ag, tok)
        assert dec["boundary"] == exp and dec["shape_fit"] > 0
    null = st.decode_seam(ag, "SEAM_NONE")
    assert null["boundary"] is None and null["shape_fit"] == 0


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — the boundary is a ShapeDecode over graph signals,
#  not a Python paragraph/blank-line/regex splitter; markers recognised against
#  held data; donkey = 0.
# --------------------------------------------------------------------------- #
def test_source_audit_graph_native_no_splitter_no_regex():
    src = inspect.getsource(st)
    tree = ast.parse(src)
    # no `import re`
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names), "import re found"
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re", "from re import ... found"
    # donkey = 0: no LLM / no network call
    for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
        assert banned not in src, "donkey token %r found" % banned
    # the boundary decision is the ShapeDecode Term's, read off _winner (reused).
    assert '"type": "ShapeDecode"' in src
    assert "rc._winner(" in src
    # the markers are recognised against held MarkerClass data (the lexicon), NOT
    # split by paragraphs/blank lines/newlines in Python.
    assert "_marker_lexicon" in src
    # no concrete paragraph/blank-line/newline SPLITTER CALL (the words
    # "paragraph"/"blank-line" appear in the module's own prose describing what it
    # does NOT do -- audit the splitter CALLS, not the prose).
    for splitter in (".split(\"\\n\")", ".split('\\n')", "splitlines(",
                     "split(\"\\n\\n\")", "split('\\n\\n')"):
        assert splitter not in src, "a Python paragraph/newline splitter %r found" % splitter
    # the seam-token builder never NAMES a boundary string as a decision (the
    # boundary comes only from the decode's `boundary` attr, via _boundary_for).
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_seam_token")
    returned_strs = {c.value for r in ast.walk(fn) if isinstance(r, ast.Return)
                     for c in ast.walk(r.value) if isinstance(c, ast.Constant)
                     and isinstance(c.value, str)}
    for kind in ("temporal_shift", "embedded_narrative", "arc_discontinuity"):
        assert kind not in returned_strs, (
            "_seam_token returns a boundary string %r -- the boundary must be "
            "the decode's verdict, not a Python assignment" % kind)


def test_marker_recognition_is_leading_and_held():
    """The temporal-shift marker is recognised at the LEADING position against
    held MarkerClass forms (single AND multi-word), never mid-sentence; 'then'
    (a within-episode connective) is DELIBERATELY not a temporal-shift marker."""
    ag = _fresh()
    st.ensure_codebook(ag)
    assert st._leading_temporal_shift(ag, "Some time later, the lion was caught.") \
        == "some time later"
    assert st._leading_temporal_shift(ag, "One day, a fox passed by.") == "one day"
    # 'then' must NOT be a temporal-shift marker (it would false-split the crow).
    assert st._leading_temporal_shift(ag, "Then an idea came to him.") is None
    # a temporal word mid-sentence is not a LEADING episode marker.
    assert st._leading_temporal_shift(ag, "The lion rested some time later.") is None
    # the telling marker is recognised off the held TELL class.
    assert st._has_telling_marker(ag, "He told the children a story.") == "told"
    assert st._has_telling_marker(ag, "The crow found a pitcher.") is None
