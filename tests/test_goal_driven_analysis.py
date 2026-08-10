"""test_goal_driven_analysis — THE JABBERWOCK IS SEEDED WITH A GOAL + THE SOURCE
AND PRODUCES A LITERARY ANALYSIS, with NO Python orchestration between ingest and
read-out. The comprehension->analysis process is a run_rules FIXPOINT driven by
the goal + data-dependencies (seeds/literary_analysis_driving.json), NOT a
hand-sequenced Python faculty list.

This gate proves: (1) the headline crow report matches the current quality,
graph-driven; (2) the SEQUENCING is graph-resident (seed rules/reflexes), and the
old Python sequences (read_and_comprehend's 10-step list + produce_analysis's
section marshalling) are GONE; (3) the same goal generalises to the mouse fable.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_goal_driven_analysis.py -p no:randomly -q -s
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
from domains import comprehension_reader as cr                         # noqa: E402
from domains import literary_analysis as la                            # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                  # noqa: E402


SEED_PATH = os.path.join(ROOT, "seeds", "literary_analysis_driving.json")

# faculty MODULES whose ordered invocation was the violation — none of these may
# appear in the Python that sits between ingest and read-out.
_FACULTY_MODULES = ("coref_entities", "situation_model_reader", "inference_generation",
                    "discourse_coherence", "global_monitoring", "character_tom",
                    "narrative_structure", "trope_theme")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


# --------------------------------------------------------------------------- #
#  THE HEADLINE — goal in, analysis out, graph-driven; matches current quality.
# --------------------------------------------------------------------------- #
def test_crow_report_is_graph_driven_and_matches_quality():
    out = jpafg.analyse(jpafg.CROW)
    report = out["report"]

    print("\n" + "=" * 78 + "\nGOAL-DRIVEN CROW ANALYSIS (read off graph Claim nodes)\n" + "=" * 78)
    print(report)
    print("=" * 78)

    # the report was READ OFF GRAPH STATE (minted Claim nodes), not a Python return
    assert out["claim_nodes"] >= 8

    low = report.lower()
    # SUMMARY — thirsty crow + unreachable water
    assert "crow" in low and "thirsty" in low
    assert "cannot reach the water" in low
    # STRUCTURE — problem / solution / resolution, FLUENT past tense
    assert "the problem is that the crow cannot reach the water" in low
    assert "the crow dropped the pebble" in low
    assert "the water rose" in low
    assert "the crow drink" in low                     # honest residual (no 'drank' token)
    # TECHNIQUE — both TVTropes labels, graph-sourced
    assert "MacGyvering" in report and "INGENUITY_OVER_STRENGTH" in report
    assert "Determinator" in report and "PERSISTENCE_PAYS" in report
    # THEME — the trope-derived moral lines
    assert "cleverness over strength" in low
    assert "persistence pays" in low
    # section headers present
    for header in ("Summary.", "Narrative structure.", "Technique.", "Theme."):
        assert header in report


def test_produce_analysis_public_entry_still_matches():
    """literary_analysis.produce_analysis (the reused public gate) returns the
    SAME dict shape, now goal-driven."""
    s, node = boot_core()
    agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
    res = la.produce_analysis(agent, jpafg.CROW)
    assert res["produced_count"] >= 3 and res["framed_count"] >= 1
    assert res["entity"] == "crow"
    for c in res["claims"]:
        assert c["graph_pointers"], "claim has no grounding: %r" % c["sentence"]
    assert la.verify_grounding(agent, res)["ok"]


# --------------------------------------------------------------------------- #
#  GENERAL — the SAME goal, the mouse fable, its OWN (different) trope.
# --------------------------------------------------------------------------- #
def test_mouse_report_is_graph_driven_general():
    out = jpafg.analyse(jpafg.MOUSE)
    low = out["report"].lower()

    print("\n" + "=" * 78 + "\nGOAL-DRIVEN MOUSE ANALYSIS\n" + "=" * 78)
    print(out["report"])
    print("=" * 78)

    assert "mouse" in low and "hungry" in low
    assert "cannot reach the cheese" in low
    assert "the mouse took" in low
    assert "the mouse ate" in low
    assert "crow" not in low and "pebble" not in low and "water" not in low
    # its OWN trope only: pure persistence, NO ingenuity/MacGyvering
    assert "Determinator" in out["report"] and "PERSISTENCE_PAYS" in out["report"]
    assert "MacGyvering" not in out["report"]
    assert "persistence pays" in low
    assert "cleverness over strength" not in low


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — the sequencing is GRAPH-RESIDENT; the old Python faculty
#  sequences are GONE; no Python orchestration between ingest and read-out.
# --------------------------------------------------------------------------- #
def _func_ast(mod, name):
    tree = ast.parse(inspect.getsource(mod))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    raise AssertionError("no function %r" % name)


def test_sequencing_lives_in_seed_rules_and_a_reflex():
    with open(SEED_PATH) as fh:
        seed = json.load(fh)
    rule_names = [r["name"] for r in seed["rules"]]
    # every faculty stage has its OWN dispatch rule (the graph-resident sequencer)
    assert len([r for r in rule_names if r.startswith("la_dispatch_")]) == 15
    for stage in ("spine", "infer_goal", "discourse", "infer_causal", "enabling",
                  "centrality", "monitoring", "tom", "narrative", "trope",
                  "produce_frames", "produce_summary", "produce_structure",
                  "produce_technique", "produce_theme"):
        assert "la_dispatch_%s" % stage in rule_names
    # ONE reflex advances a dispatched stage (the _question_pursue_advance shape)
    assert [rf["name"] for rf in seed["reflexes"]] == ["analysis_advance"]


def test_read_and_comprehend_python_sequence_is_gone():
    """read_and_comprehend no longer sequences faculties: its body calls NO
    faculty module and contains NO `if` (the ordering moved to the seed)."""
    src = inspect.getsource(cr.read_and_comprehend)
    for mod in _FACULTY_MODULES:
        assert "%s." % mod not in src.split('"""', 2)[-1], \
            "read_and_comprehend still calls faculty %s" % mod
    fn = _func_ast(cr, "read_and_comprehend")
    assert [n for n in ast.walk(fn) if isinstance(n, ast.If)] == []
    assert "reading_drive" in src           # it delegates to the goal-driven adapter


def test_produce_analysis_section_marshalling_is_gone():
    """produce_analysis no longer calls the four section builders in sequence —
    they are the goal-fired stages' shims now; produce_analysis only reads back."""
    body = inspect.getsource(la.produce_analysis).split('"""', 2)[-1]
    for builder in ("_build_summary(", "_build_structure(", "_build_technique(",
                    "_build_theme(", "read_narrative_roles("):
        assert builder not in body, "produce_analysis still marshals %s" % builder
    assert "reading_drive" in body


def test_no_python_orchestration_between_ingest_and_readoff():
    """The script's `analyse` — the whole flow — calls NO faculty module between
    ingest and read-out: only run_reading_flow (ingest+goal+pump) and the graph
    read-off. The ordering is the seed's, not this function's."""
    body = inspect.getsource(jpafg.analyse).split('"""', 2)[-1]
    for mod in _FACULTY_MODULES:
        assert mod not in body
    assert "run_reading_flow" in body and "_read_report_off_graph" in body


def test_executor_is_a_nonbranching_shim_lookup():
    """_advance_dispatched_stage picks the shim by the stage's NAME (a dict
    lookup) and never branches on graph state to choose a faculty."""
    src = inspect.getsource(rd._advance_dispatched_stage)
    assert "_STAGE_SHIMS.get(" in src
    # it names no faculty module directly (it dispatches by lookup)
    for mod in _FACULTY_MODULES:
        assert mod not in src


def test_donkey_zero_no_regex_no_llm_in_driver():
    src = inspect.getsource(rd)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
    for banned in ("openai", "anthropic", "requests.post", "call_model", "self_teacher"):
        assert banned not in src


def test_stages_reached_done_via_the_fixpoint():
    """After a run, the AnalysisStage nodes exist and reached `done` — the seed's
    reflex+rules drove them there (not a Python loop calling faculties)."""
    s, node = boot_core()
    agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
    rd.run_reading_flow(agent, jpafg.CROW, report="analysis")
    stages = {s.node(n)["attrs"].get("name"): s.node(n)["attrs"].get("status")
              for n in s.nodes("AnalysisStage")}
    assert stages, "no AnalysisStage nodes minted"
    for name in ("spine", "narrative", "trope", "produce_summary", "produce_theme"):
        assert stages.get(name) == "done", "stage %s did not reach done: %r" % (name, stages.get(name))
    # the report is genuinely graph-resident
    assert len(s.nodes("Claim")) >= 8


# --------------------------------------------------------------------------- #
#  MOVE 1 — THE BLACKBOARD IS DISSOLVED. Every faculty stage re-reads its
#  INPUTS from graph nodes; nothing load-bearing passes between stages through
#  the Python blackboard. The de-cache changes NOTHING observable.
# --------------------------------------------------------------------------- #
# The crow + mouse reports, FROZEN before the blackboard dissolution. Dissolving
# a cache must be a pure de-cache: byte-for-byte identical output.
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
_MOUSE_REPORT = (
    "Summary. The story follows a mouse, which is hungry. Its central difficulty, "
    "the most causally connected event, is that the mouse cannot reach the cheese. "
    "In the end, the mouse ate.\n\n"
    "Narrative structure. The problem is that the mouse cannot reach the cheese. The "
    "solution comes when the mouse took. In the resolution, the mouse ate.\n\n"
    "Technique. Through its incremental and resolution structure, the story "
    "instantiates Determinator (PERSISTENCE_PAYS).\n\n"
    "Theme. Read from the trope(s) it instantiates, the story's theme is: Small "
    "repeated efforts accumulate into success -- little by little, persistence pays.")


def test_reports_are_byte_identical_after_dissolution():
    """BYTE-IDENTICAL: the crow AND mouse reports match the frozen pre-dissolution
    baseline exactly — a cache is dissolved, nothing observable changes."""
    crow = jpafg.analyse(jpafg.CROW)["report"]
    mouse = jpafg.analyse(jpafg.MOUSE)["report"]
    print("\n" + "=" * 78 + "\nCROW (post-dissolution)\n" + "=" * 78 + "\n" + crow)
    print("\n" + "=" * 78 + "\nMOUSE (post-dissolution)\n" + "=" * 78 + "\n" + mouse)
    assert crow == _CROW_REPORT, "crow report changed after the de-cache"
    assert mouse == _MOUSE_REPORT, "mouse report changed after the de-cache"


_BB_CONFIG_KEYS = {"text", "window", "max_sentences", "claims", "sections"}


def test_blackboard_holds_nothing_load_bearing():
    """BLACKBOARD-EMPTY: POISON every stage — wipe all non-config keys from the
    blackboard right before each stage runs. If any stage read a load-bearing
    value from bb, the report would change; it does not, because every stage
    re-reads its inputs from graph nodes. The report is graph-resident (Claim
    nodes) and unchanged."""
    orig = dict(rd._STAGE_SHIMS)

    def _poison(shim):
        def _wrapped(ad):
            bb = ad._master["analysis_bb"]
            for k in [k for k in bb if k not in _BB_CONFIG_KEYS]:
                del bb[k]
            return shim(ad)
        return _wrapped

    rd._STAGE_SHIMS = {k: _poison(v) for k, v in orig.items()}
    try:
        s, node = boot_core()
        agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
        rd.run_reading_flow(agent, jpafg.CROW, report="analysis")
        report = jpafg._read_report_off_graph(s)
    finally:
        rd._STAGE_SHIMS = orig
    assert report == _CROW_REPORT, (
        "poisoning the blackboard changed the report -- a stage read a "
        "load-bearing value from bb instead of re-reading from graph nodes")

    # and, orthogonally: after a NORMAL run, deleting the blackboard entirely
    # leaves the report intact (it is read off the Claim nodes).
    s2, node2 = boot_core()
    ag2 = type("A", (), {"s": s2, "inner": s2._inner, "agent": node2})()
    rd.run_reading_flow(ag2, jpafg.CROW, report="analysis")
    assert jpafg._read_report_off_graph(s2) == _CROW_REPORT


def test_incremental_signal_read_from_coref_number_node_marker():
    """SIGNALS FROM NODES (TROPE_INCREMENTAL): the crow's pebbles -> a durable
    `coref_number='plural'` marker on the change-of-state SmEvent (+ a
    `sentence_order` stamp), read GRAPH-NATIVE by trope_theme — never a
    transient ingest-record dict."""
    from domains import trope_theme as tt
    s, node = boot_core()
    agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
    rd.run_reading_flow(agent, jpafg.CROW, report="analysis")

    plural = [s.node(n)["attrs"] for n in s.nodes("SmEvent")
              if s.node(n)["attrs"].get("coref_number") == "plural"]
    assert plural, "no SmEvent carries the durable coref_number='plural' marker"
    orders = [e.get("sentence_order") for e in plural if e.get("sentence_order") is not None]
    assert orders, "the plural SmEvent carries no sentence_order stamp"
    # trope_theme reads the INCREMENTAL signal OFF THE NODE marker
    assert any(tt._incremental_evidence(s, o) is not None for o in orders)
    # and the crow's PERSISTENCE trope (which covers TROPE_INCREMENTAL) fired
    names = {t["name"] for t in tt.read_tropes(agent, "crow")}
    assert "PERSISTENCE_PAYS" in names
    persistence = next(t for t in tt.read_tropes(agent, "crow")
                       if t["name"] == "PERSISTENCE_PAYS")
    assert "TROPE_INCREMENTAL" in (persistence.get("covered_tokens") or [])


def test_blocked_signal_read_from_blocked_gap_node_marker():
    """SIGNALS FROM NODES (TROPE_BLOCKED): a precondition gap minted for an
    entity stamps a durable `blocked_gap=1` marker on its SmEntity node, and
    trope_theme reads the BLOCKED signal OFF THE NODE (synthetic case — none of
    the corpus fables trigger a precondition gap)."""
    from domains import trope_theme as tt
    s, node = boot_core()
    agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
    tt.ensure_codebook(agent)
    s.add_node("SmEntity", {"name": "hero", "blocked_gap": 1})

    ev = tt._blocking_evidence(s, "hero")
    assert ev is not None and ev["gap"]["entity"] == "hero"
    assert tt._blocking_evidence(s, "nobody") is None, "honest null without the marker"
    # the marker drives the TROPE_BLOCKED token (existence check over the node)
    tokens, evidence = tt._build_tokens(s, {}, {"entity": "hero", "roles": []})
    assert "TROPE_BLOCKED" in tokens
    assert evidence["TROPE_BLOCKED"]["kind"] == "precondition_gap"
    # and the BLOCKED+INDIRECT pair decodes to NECESSITY_INVENTION (mechanism)
    plan = tt._decode(agent, [["TROPE_BLOCKED"], ["TROPE_INDIRECT"]]).get("plan") or []
    assert plan and plan[0]["part"] == "NECESSITY_INVENTION"


def test_need_attr_is_graph_resident_on_the_want_event():
    """The triggering need-state ('thirsty') is persisted on the want-SmEvent
    and re-read by the goal re-reader (the SUMMARY reads it: 'a crow, which is
    thirsty')."""
    s, node = boot_core()
    agent = type("A", (), {"s": s, "inner": s._inner, "agent": node})()
    ad = rd._LAAdapter(s)
    rd.run_reading_flow(agent, jpafg.CROW, report="analysis")
    goals = rd._goal_from_graph(ad)
    crow = next(g for g in goals if g["gap"]["entity"] == "crow")
    assert crow["gap"]["need_attr"] == "thirsty"
    assert crow["supplies"]["remedy"] == "drink"


def test_shim_inputs_are_graph_queries_not_blackboard_reads():
    """GRAPH-NATIVE: no faculty shim reads a load-bearing VIEW from the
    blackboard — every `bb[...]` in a shim is a Store (the return buffer), never
    a Load (an inter-stage input). Inputs come from the `_*_from_graph`
    re-readers. Plus: no `import re` in the driver."""
    tree = ast.parse(inspect.getsource(rd))
    # no import re
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert not any(a.name == "re" for a in n.names)
        if isinstance(n, ast.ImportFrom):
            assert n.module != "re"
    shim_names = {"_shim_%s" % st for st in (
        "spine", "infer_goal", "discourse", "infer_causal", "enabling",
        "centrality", "monitoring", "tom", "narrative", "trope",
        "produce_frames", "produce_summary", "produce_structure",
        "produce_technique", "produce_theme")}
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name in shim_names:
            for node in ast.walk(fn):
                if (isinstance(node, ast.Subscript)
                        and isinstance(node.value, ast.Name) and node.value.id == "bb"
                        and isinstance(node.ctx, ast.Load)):
                    raise AssertionError(
                        "%s reads a load-bearing view from the blackboard (bb[...]"
                        " in Load context) -- it must re-read from graph nodes" % fn.name)
            # every comprehension shim calls at least one graph re-reader
            body = inspect.getsource(getattr(rd, fn.name))
            if fn.name not in ("_shim_centrality", "_shim_produce_frames"):
                assert ("_from_graph(ad)" in body or "_source_text(ad)" in body
                        or "_sentences_from_graph(ad)" in body
                        or "_produce_contexts(ad)" in body), \
                    "%s does not source its inputs from a graph re-reader" % fn.name
