"""test_cortices_tick — THE READING IS A SOCIETY OF CORTICES, TICK-DRIVEN.

The reading is reconceived from a LINEAR dispatch chain (the 15 la_dispatch_*
stages advanced one-per-firing, pumped by hand-called run_rules()+fire_reflexes())
into FIVE concurrent graph-resident cortices (seeds/reading_cortices.json), each a
Cortex node + a per-tick Reflex, driven by the AGENT'S cognitive tick. This gate
proves:

  * CROW byte-identical VIA TICK — seed the goal + ingest, TICK to steady state
    (NOT run_rules), get the SAME report byte-for-byte.
  * NESTED (Lion & Mouse) VIA TICK — per-episode isolation + the RECIPROCITY
    spanning theme, driven by cognitive_tick.
  * CORTICES EXIST + ALL TICK — the five Cortex bundles are graph-resident and
    every one advances its stages over the ticks.
  * TICK-DRIVEN AUDIT — the reading path drives via cognitive_tick; NO
    run_rules(/fire_reflexes( in the reading loop; no import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_cortices_tick.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
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
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
import jabberwock_ticks_a_reading as jtr                               # noqa: E402
import jabberwock_reads_nested_story as jrns                           # noqa: E402


# The frozen linear-dispatch baseline (identical to test_goal_driven_analysis's
# and test_order_n_nested_story's _CROW_REPORT) — the tick drive must reproduce
# it byte-for-byte (this reorganises the DRIVE, not the meaning).
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

_CORTICES = ["language", "situation", "social", "narrative", "executive"]


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
#  CROW — byte-identical, driven by the AGENT'S COGNITIVE TICK to steady state.
# --------------------------------------------------------------------------- #
def test_crow_report_byte_identical_via_tick():
    out = jtr.tick_a_reading(jtr.CROW, trace=True)
    print("\n" + "=" * 78 + "\nCROW (ticked reading, %d ticks, %d cortices)\n"
          % (out["ticks"], out["cortices"]) + "=" * 78 + "\n" + out["report"])
    assert out["report"] == _CROW_REPORT, "the ticked crow report drifted from the frozen baseline"
    assert out["cortices"] == 5


def test_ticked_reading_matches_run_reading_flow_report():
    """The visible tick loop (jtr.tick_a_reading) and the library driver
    (rd.run_reading_flow, which also ticks) produce the identical report."""
    s, node = boot_core()
    rd.run_reading_flow(_Agent(s, node), jtr.CROW, report="analysis")
    import jabberwock_produces_analysis_from_goal as jpafg
    lib = jpafg._read_report_off_graph(s)
    assert jtr.tick_a_reading(jtr.CROW)["report"] == lib == _CROW_REPORT


# --------------------------------------------------------------------------- #
#  NESTED (Lion & Mouse) — per-episode isolation + reciprocity, TICK-DRIVEN.
# --------------------------------------------------------------------------- #
def test_nested_lion_mouse_reciprocity_via_tick():
    ag = _fresh()
    out = rd.run_nested_reading_flow(ag, jrns.LION_MOUSE)
    assert out["depth"] == 2 and len(out["units"]) == 2
    ep1, ep2 = out["units"]
    # ISOLATION: episode 1's lion and episode 2's lion are DISTINCT graph nodes.
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
    # RECIPROCITY: the parent composes a spanning theme spanning both episodes.
    stt = out["spanning_theme"]
    assert stt is not None and stt.get("theme")
    assert stt.get("token") == "RETURN_ACTION"
    print("\nRECIPROCITY (ticked):", stt.get("theme"))


# --------------------------------------------------------------------------- #
#  CORTICES EXIST + ALL FIVE TICK — the five bundles are graph-resident and
#  every one advances at least one stage over the ticks.
# --------------------------------------------------------------------------- #
def test_five_cortices_are_graph_resident():
    s, node = boot_core()
    rd.run_reading_flow(_Agent(s, node), jtr.CROW, report="analysis")
    cortices = {s.node(n)["attrs"].get("name"): s.node(n)["attrs"] for n in s.nodes("Cortex")}
    assert set(cortices) == set(_CORTICES), "expected exactly the five named cortices"
    # each Cortex node carries its member-stage list (graph-inspectable bundle)
    for name, at in cortices.items():
        stages = json.loads(at.get("stages") or "[]")
        assert stages, "cortex %s has no member stages" % name
        for stg in stages:
            assert rd._CORTEX_OF[stg] == name
    # every faculty stage is bundled into exactly one cortex, via an in_cortex edge
    for n in s.nodes("AnalysisStage"):
        at = s.node(n)["attrs"]
        assert at.get("cortex") in _CORTICES
        ins = list(s._inner.neighbours(n, "in_cortex"))
        assert len(ins) == 1, "stage %s not wired to exactly one Cortex" % at.get("name")


def test_reading_cortices_map_to_generic_cognitive_areas():
    s, node = boot_core()
    agent = _Agent(s, node)
    rd.run_reading_flow(agent, jtr.CROW, report="analysis")
    for seed_name in ("cognitive_areas", "reading_async_areas"):
        with open(os.path.join(ROOT, "seeds", seed_name + ".json")) as f:
            agent.inner.load_seed_manifest(json.load(f), agent.agent)
    agent.inner.run_rules()
    areas = {
        s.node(n)["attrs"].get("cortex"): n
        for n in s.nodes("CognitiveArea")
        if s.node(n)["attrs"].get("cortex")
    }
    assert set(areas) == set(_CORTICES)
    for cortex in s.nodes("Cortex"):
        name = s.node(cortex)["attrs"].get("name")
        assert list(s._inner.neighbours(cortex, "maps_to_area")) == [areas[name]]
    for stage in s.nodes("AnalysisStage"):
        mapped = list(s._inner.neighbours(stage, "in_cognitive_area"))
        assert len(mapped) == 1


def test_all_five_cortices_have_a_reflex_and_all_advance():
    s, node = boot_core()
    ad = rd._LAAdapter(s)
    from domains.reflective_faculty import _ensure_seed_chain
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_driving",))
    rd._register_cortices(ad)
    # each cortex ships a graph-resident Reflex named "<name>_cortex".
    reflex_names = {s.node(n)["attrs"].get("name") for n in s.nodes("Reflex")}
    for name in _CORTICES:
        assert "%s_cortex" % name in reflex_names, "no reflex for cortex %s" % name

    # drive a full reading and confirm EVERY cortex advanced at least one stage
    # to done (all five ticked, not just a linear subset).
    ad._master["analysis_bb"] = {"text": jtr.CROW, "window": 2, "max_sentences": 40,
                                 "claims": [], "sections": {}}
    src = rd._ingest_source(ad, jtr.CROW)
    rd._mint_goal(ad, src, produce=True)
    rd._mint_stages(ad, produce=True)
    rd._tick_reading(ad)
    advanced = {name: 0 for name in _CORTICES}
    for n in s.nodes("AnalysisStage"):
        at = s.node(n)["attrs"]
        if at.get("status") == "done":
            advanced[at.get("cortex")] += 1
    for name in _CORTICES:
        assert advanced[name] >= 1, "cortex %s never advanced a stage over the ticks" % name


def test_cortices_fire_concurrently_within_a_tick():
    """REAL CONCURRENCY (not a hidden linear chain): at least one tick advances
    stages belonging to MORE THAN ONE cortex — the cortices process whatever of
    their inputs are ready in the SAME tick, they do not wait for one another."""
    s, node = boot_core()
    ad = rd._LAAdapter(s)
    from domains.reflective_faculty import _ensure_seed_chain
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_driving",))
    rd._register_cortices(ad)
    ad._master["analysis_bb"] = {"text": jtr.CROW, "window": 2, "max_sentences": 40,
                                 "claims": [], "sections": {}}
    src = rd._ingest_source(ad, jtr.CROW)
    rd._mint_goal(ad, src, produce=True)
    rd._mint_stages(ad, produce=True)
    multi = False
    prev = set()
    last = None
    for _ in range(200):
        ad.cognitive_tick()
        done = {s.node(n)["attrs"].get("name"): s.node(n)["attrs"].get("cortex")
                for n in s.nodes("AnalysisStage")
                if s.node(n)["attrs"].get("status") == "done"}
        just_cortices = {done[k] for k in (set(done) - prev)}
        if len(just_cortices) >= 2:
            multi = True
        prev = set(done)
        snap = rd._statuses(ad)
        if snap == last:
            break
        last = snap
    assert multi, "no tick ever advanced more than one cortex -- the cortices ran strictly sequentially"


# --------------------------------------------------------------------------- #
#  TICK-DRIVEN AUDIT — the reading loop rides cognitive_tick; no engine reach-in.
# --------------------------------------------------------------------------- #
def _calls_in(fn):
    """The set of method names CALLED in fn's body (AST — ignores docstring/comment
    prose, which legitimately names the old run_rules()/fire_reflexes() pump)."""
    names = set()
    for n in ast.walk(ast.parse(inspect.getsource(fn))):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute):
                names.add(n.func.attr)
            elif isinstance(n.func, ast.Name):
                names.add(n.func.id)
    return names


def test_reading_loop_drives_via_cognitive_tick_not_run_rules():
    for fn in (rd._tick_reading, rd.run_reading_flow, rd.run_produce_over_graph,
               rd.run_nested_reading_flow):
        calls = _calls_in(fn)
        assert "run_rules" not in calls, "%s hand-calls run_rules()" % fn.__name__
        assert "fire_reflexes" not in calls, "%s hand-calls fire_reflexes()" % fn.__name__
    # and the loop DOES ride the agent's cognitive tick
    assert "cognitive_tick" in _calls_in(rd._tick_reading)
    for driver in (rd.run_reading_flow, rd.run_produce_over_graph, rd.run_nested_reading_flow):
        assert "_tick_reading" in _calls_in(driver)


def test_cognitive_tick_is_the_agents_own_cycle():
    """cognitive_tick lives on the AGENT (world_adapter), not the reading adapter
    — the driver rides the agent's cycle, it does not define a bespoke pump."""
    from substrate.world_adapter import WorldAdapter
    src = inspect.getsource(WorldAdapter.cognitive_tick)
    assert 'run_cycle("cognitive_legacy"' in src and "fire_reflexes(" in src, (
        "cognitive_tick must ride the native cycle plan then enact reflex boundaries")


def test_donkey_zero_no_regex():
    for mod in (rd, jtr):
        tree = ast.parse(inspect.getsource(mod))
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name == "re" for a in n.names)
            if isinstance(n, ast.ImportFrom):
                assert n.module != "re"
    src = inspect.getsource(rd)
    for banned in ("openai", "anthropic", "requests.post", "call_model"):
        assert banned not in src


def test_advance_cortex_stage_is_a_nonbranching_shim_lookup():
    """the cortex reflex response picks the shim by the stage's NAME (a dict
    lookup) filtered to its cortex, and never branches on graph state to choose a
    faculty — the _question_pursue_advance precedent, one level of society up."""
    src = inspect.getsource(rd._advance_cortex_stage)
    assert "_STAGE_SHIMS.get(" in src
    for mod in ("coref_entities", "situation_model_reader", "inference_generation",
                "discourse_coherence", "global_monitoring", "character_tom",
                "narrative_structure", "trope_theme"):
        assert mod not in src
