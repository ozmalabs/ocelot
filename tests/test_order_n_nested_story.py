"""test_order_n_nested_story — MOVE 2b: comprehension RECURSES over the StoryUnit
tree. Each StoryUnit comprehends in ISOLATION (the `unit` graph dimension
threaded through the six faculties), and the PARENT composes a SPANNING theme
from its children.

  * CROW (depth-1) — order-N with N=1 IS the flat case: no child units, the flat
    comprehension is UNCHANGED, the goal-driven report BYTE-IDENTICAL (the hard
    invariant; frozen-baseline assert).
  * LION & MOUSE (2-unit tree) — each episode gets its OWN entities + actions,
    ISOLATED (episode 2's re-introduced lion is a DISTINCT graph node from
    episode 1's lion — no contamination); the PARENT composes the spanning theme
    RECIPROCITY (episode 2's rescue reciprocates episode 1's mercy) — a
    cross-episode RELATION, read off the children's own UnitAction nodes by a
    ShapeDecode over the ShapeSignatureSpanningTheme codebook.
  * GRAPH-NATIVE — unit scope is a node attr; per-unit firing is the seeded
    u_dispatch_* rules matching per StoryUnit; compose is a rule; the reflex
    advances ONE stage per firing (run_rules drives the recursion). NO Python
    `for unit: comprehend(unit)` loop; no `import re`; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_order_n_nested_story.py -p no:randomly -q -s
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
from domains import reading_drive as rd                               # noqa: E402
from domains import nested_reading as nr                               # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402
import jabberwock_reads_nested_story as jrns                           # noqa: E402


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


# the crow's goal-driven analysis report, FROZEN — MOVE 2b unit-scoping is
# byte-for-byte transparent at depth-1 (order-N with N=1 IS the flat case).
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


# --------------------------------------------------------------------------- #
#  CROW — depth-1: order-N N=1 = flat, report byte-identical (the invariant).
# --------------------------------------------------------------------------- #
def test_crow_report_byte_identical_move_2b_is_transparent_at_depth1():
    report = jpafg.analyse(jpafg.CROW)["report"]
    assert report == _CROW_REPORT, (
        "MOVE 2b changed the crow report -- unit-scoping must be transparent at "
        "depth-1 (order-N with N=1 IS the flat case)")


def test_crow_nested_flow_is_depth1_no_recursion():
    out = rd.run_nested_reading_flow(_fresh(), jrns.CROW)
    assert out["depth"] == 1
    assert out["units"] == []                       # no leaves -> no per-unit recursion
    assert out["spanning_theme"] is None            # nothing to compose


# --------------------------------------------------------------------------- #
#  LION & MOUSE — 2-unit tree: per-episode isolation + composed spanning theme.
# --------------------------------------------------------------------------- #
def test_lion_mouse_two_units_isolated_entities_and_actions():
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, jrns.LION_MOUSE)
    assert out["depth"] == 2
    assert len(out["units"]) == 2
    ep1, ep2 = out["units"]
    # each episode has its own lion + mouse.
    assert "lion" in ep1["entities"] and "mouse" in ep1["entities"]
    assert "lion" in ep2["entities"] and "mouse" in ep2["entities"]
    # ISOLATION: the ep1 lion SmEntity and the ep2 lion SmEntity are DISTINCT
    # graph nodes (a name resolves WITHIN its StoryUnit — no contamination).
    lion1 = [n for n in ag.s.nodes("SmEntity")
             if ag.s.node(n)["attrs"].get("name") == "lion"
             and ag.s.node(n)["attrs"].get("unit") == ep1["unit"]]
    lion2 = [n for n in ag.s.nodes("SmEntity")
             if ag.s.node(n)["attrs"].get("name") == "lion"
             and ag.s.node(n)["attrs"].get("unit") == ep2["unit"]]
    assert len(lion1) == 1 and len(lion2) == 1
    v1 = lion1[0].value if hasattr(lion1[0], "value") else lion1[0]
    v2 = lion2[0].value if hasattr(lion2[0], "value") else lion2[0]
    assert v1 != v2, "episode 1's lion and episode 2's lion collapsed to ONE node"
    # per-episode ACTIONS isolate: ep1 lion acts on mouse; ep2 mouse acts on lion.
    a1 = {(a["agent"], a["patient"]) for a in ep1["actions"]}
    a2 = {(a["agent"], a["patient"]) for a in ep2["actions"]}
    assert ("lion", "mouse") in a1
    assert ("mouse", "lion") in a2


def test_lion_mouse_parent_composes_spanning_reciprocity_theme():
    out = rd.run_nested_reading_flow(_fresh(), jrns.LION_MOUSE)
    stt = out["spanning_theme"]
    assert stt is not None, "the parent composed no spanning theme"
    assert stt["theme"] == "reciprocity"
    assert stt["construction"] == "reciprocity"
    assert stt["token"] == "RETURN_ACTION"
    # VERBATIM the codebook line — the spanning theme read off the tree.
    assert stt["line"] == (
        "A kindness is repaid -- the one acted upon returns the deed to the "
        "actor. Invisible in either episode alone; it emerges only from the two "
        "episodes together: episode 2's rescue reciprocates episode 1's mercy.")
    # traced to BOTH children (spans_unit edges) — not a flat union of one child.
    import json as _json
    kids = _json.loads(stt.get("children") or "[]")
    assert len([k for k in kids if k is not None]) == 2


def test_span_token_is_the_shapedecode_verdict():
    ag = _fresh()
    nr.ensure_codebook(ag)
    win = nr.decode_span(ag, "RETURN_ACTION")
    assert win["theme"] == "reciprocity" and win["shape_fit"] > 0
    null = nr.decode_span(ag, "SPAN_NONE")
    assert null["theme"] is None and null["shape_fit"] == 0


# --------------------------------------------------------------------------- #
#  PER-UNIT DISPATCH — stages minted PER leaf; the seeded rule fires per unit
#  (run_rules recurses); the compose stage fires only after the children.
# --------------------------------------------------------------------------- #
def test_per_unit_dispatch_is_rules_firing_per_story_unit():
    ag = _fresh()
    rd.run_nested_reading_flow(ag, jrns.LION_MOUSE)
    stages = [(ag.s.node(n)["attrs"].get("name"), ag.s.node(n)["attrs"].get("status"),
               ag.s.node(n)["attrs"].get("unit")) for n in ag.s.nodes("AnalysisStage")]
    comprehend = [s for s in stages if s[0] == "unit_comprehend"]
    compose = [s for s in stages if s[0] == "compose"]
    # ONE unit_comprehend stage per LEAF unit (2), each carrying its own `unit`.
    assert len(comprehend) == 2
    assert len({s[2] for s in comprehend}) == 2      # two distinct unit ids
    # ONE compose stage on the parent; every stage reached 'done' at the fixpoint.
    assert len(compose) == 1
    assert all(s[1] == "done" for s in stages), "the rule/reflex fixpoint stalled"


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT — unit-scope is a node attr; the recursion is per-node
#  rule firing (NO Python `for unit: comprehend(unit)`); no regex; donkey = 0.
# --------------------------------------------------------------------------- #
def test_no_python_per_unit_comprehension_loop():
    # the DRIVER mints stages + pumps; it NEVER comprehends a unit itself.
    drv = inspect.getsource(rd.run_nested_reading_flow)
    assert "comprehend_unit" not in drv, (
        "the nested driver calls comprehend_unit directly -- the per-unit "
        "recursion must be the reflex firing per rule-dispatched stage")
    # UPDATED (society-of-cortices reconception): the recursion driver is the
    # AGENT'S COGNITIVE TICK to steady state (`_tick_reading`, which loops
    # ad.cognitive_tick()), NOT a hand-called run_rules+fire_reflexes pump. The
    # per-unit recursion is still the seeded u_dispatch_* rules firing per
    # StoryUnit inside cognitive_tick's rule settle, and the unit_analysis_advance
    # reflex firing inside cognitive_tick's reflex phase -- the driver no longer
    # reaches into the engine itself.
    assert "_tick_reading(" in drv
    assert "run_rules(" not in drv and "fire_reflexes(" not in drv
    # the reflex RESPONSE advances ONE stage per firing (a `return` inside the
    # stage loop) -- it is NOT a loop that comprehends every unit.
    adv = rd._advance_unit_stage
    tree = ast.parse(inspect.getsource(adv))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
    assert len(loops) == 1, "expected exactly one stage-scan loop in the reflex"
    assert any(isinstance(n, ast.Return) for n in ast.walk(loops[0])), (
        "_advance_unit_stage must return after advancing ONE stage (advance-one-"
        "per-firing), not iterate every unit")


def test_source_audit_graph_native_no_regex_no_donkey():
    for mod in (nr, rd):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name == "re" for a in n.names), "import re found"
            if isinstance(n, ast.ImportFrom):
                assert n.module != "re", "from re import ... found"
        for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
            assert banned not in src, "donkey token %r found in %s" % (banned, mod.__name__)
    # the spanning-theme decision is the ShapeDecode Term's, read off _winner.
    nsrc = inspect.getsource(nr)
    assert '"type": "ShapeDecode"' in nsrc
    assert "rc._winner(" in nsrc
    # the compose never NAMES the theme as a Python decision (it comes from the
    # decoded schema's `theme` attr, via _theme_for).
    fn = next(n for n in ast.walk(ast.parse(nsrc))
              if isinstance(n, ast.FunctionDef) and n.name == "_span_token")
    returned_strs = {c.value for r in ast.walk(fn) if isinstance(r, ast.Return)
                     for c in ast.walk(r.value) if isinstance(c, ast.Constant)
                     and isinstance(c.value, str)}
    assert "reciprocity" not in returned_strs, (
        "_span_token names the theme 'reciprocity' -- the theme must be the "
        "decode's verdict, not a Python assignment")
