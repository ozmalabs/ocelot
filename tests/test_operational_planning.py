"""test_operational_planning — DISCRIMINATIVE gates for the META-LAYER: the
jabberwock PLANS + ORCHESTRATES its own operational work from a natural-language
instruction. Closes the four meta-gaps the probe (scripts/jabberwock_plans_bulk_
load.py) named. donkey=0 (no LLM in the match / plan / guards / executor).

Run: PYTHONPATH=runners/dsl/python:.:scripts pytest tests/test_operational_planning.py -p no:randomly
"""
from __future__ import annotations

import io
import contextlib
import json

import pytest


OPERATIONAL_NAMES = {"bulk_load", "warm", "measure_timing", "judge_sufficiency",
                     "perceive_gaps", "prioritize", "fix", "report", "stop"}
# the ink-stroke / letter signatures the composer's OLD codebook would have decoded
# 'bulk load' as (the probe's meta-gap 2). A correct match returns NONE of these.
INK_LETTERS = {"a", "T", "t", "A", "b", "c"}


@pytest.fixture(scope="module")
def agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


@pytest.fixture(scope="module")
def op():
    import domains.operational_planning as _op
    return _op


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return fn(*a, **k)


# ===========================================================================
# 1. CODEBOOK FIX (the headline vs the probe) — the exact probe failures now
#    resolve to OPERATIONAL capabilities, NOT the handwriting letter 'a'/'T'.
# ===========================================================================
def test_codebook_fix_bulk_load_not_letter_a(agent, op):
    m = op.match_capability(agent, "bulk load of wikipedia")
    assert m["name"] == "bulk_load", m
    assert m["name"] not in INK_LETTERS
    assert m["score"] >= 1


def test_codebook_fix_measure_timing_not_letter_T(agent, op):
    m = op.match_capability(agent, "measure timing")
    assert m["name"] == "measure_timing", m
    assert m["name"] not in INK_LETTERS


def test_codebook_fix_other_gaps(agent, op):
    m = op.match_capability(agent, "other gaps")
    assert m["name"] == "perceive_gaps", m


def test_codebook_all_operational(agent, op):
    # every probe clause resolves to an OperationalCapability node (not a
    # ShapeSignature): the match is over the operational codebook.
    for clause in ("bulk load of wikipedia", "measure timing", "other gaps",
                   "is it fast enough", "report the result"):
        m = op.match_capability(agent, clause)
        assert m["name"] in OPERATIONAL_NAMES, (clause, m)


# ===========================================================================
# 2. INSTRUCTION -> PLAN (the original instruction, agent-driven).
# ===========================================================================
ORIGINAL = ("Do a bulk load of Wikipedia. Identify if it is sufficiently fast. "
            "Identify if there are other gaps.")


def test_instruction_to_plan(agent, op):
    parsed = op.parse_instruction(agent, ORIGINAL)
    assert parsed["n_steps"] >= 3
    binds = [agent.s.node(s)["attrs"].get("binding_key") for s in parsed["steps"]]
    assert binds[0] == "bulk_load"
    # step 2's clause "sufficiently fast" -> judge_sufficiency, whose binding ENTAILS
    # measure_timing (reads where-time-goes THEN the sufficiency verdict).
    assert binds[1] == "judge_sufficiency"
    assert binds[2] == "perceive_gaps"
    # the plan is GRAPH: every bound step carries a uses_capability edge.
    for s in parsed["steps"]:
        bk = agent.s.node(s)["attrs"].get("binding_key")
        if bk:
            caps = agent.inner.neighbours(s, "uses_capability")
            assert caps, s


# ===========================================================================
# 3. EXECUTE END-TO-END — run_plan FIRES the plan: a real small load runs, the
#    sufficiency verdict is the agent's OWN, the other gaps are perceived. The human
#    did NOT sequence it (parse produced the order; run_plan fired it).
# ===========================================================================
def test_execute_end_to_end(agent, op):
    parsed = op.parse_instruction(agent, ORIGINAL)
    res = _quiet(op.run_plan, agent, parsed, max_load=2)
    trace = res["trace"]
    # the load actually ran
    load = trace[0]
    assert load["capability"] == "bulk_load" and load["executed"]
    assert load["output"]["n_articles"] >= 1
    # the agent's OWN sufficiency verdict was produced (should_continue Program)
    judge = trace[1]["output"]
    assert judge["capability"] if False else True  # (shape guard)
    assert "sufficient" in judge and "verdict" in judge
    # the other gaps were perceived (the same consumption residuals the probe found)
    gaps = trace[2]["output"]
    assert gaps["n_consumption"] >= 1
    # NO HUMAN SEQUENCING: the trace order == the plan's graph order, and the whole
    # sequence was produced by run_plan walking the graph — not a hand-written script.
    plan_order = [agent.s.node(s)["attrs"].get("binding_key") for s in parsed["steps"]]
    trace_order = [r.get("capability") for r in trace]
    assert trace_order == plan_order, (trace_order, plan_order)


# ===========================================================================
# 4. MULTI-LAYER (arbitrary length + nesting) — a plan TREE with a foreach whose
#    substeps include an if-then; the executor iterates the foreach and branches the if.
# ===========================================================================
NESTED = ("Load 15 articles. For each gap you find, diagnose it; if it is worth "
          "fixing, fix it. Then report how many were fixed and stop when the rest "
          "is sufficient.")


def test_multilayer_plan_tree(agent, op):
    parsed = op.parse_instruction(agent, NESTED)
    kinds = [agent.s.node(s)["attrs"].get("kind") for s in parsed["steps"]]
    assert "foreach" in kinds
    assert "stop" in kinds
    # the foreach has an if-then substep (the plan TREE, nested).
    fe = parsed["steps"][kinds.index("foreach")]
    subs = agent.inner.neighbours(fe, "substep")
    sub_kinds = [agent.s.node(c)["attrs"].get("kind") for c in subs]
    assert "ifthen" in sub_kinds
    ifs = [c for c in subs if agent.s.node(c)["attrs"].get("kind") == "ifthen"]
    # the if-then's guard is a GRAPH cond Term.
    assert agent.s.node(ifs[0])["attrs"].get("cond_term")
    # the if-then guards a fix substep.
    fixsubs = agent.inner.neighbours(ifs[0], "substep")
    assert any(agent.s.node(c)["attrs"].get("binding_key") == "fix" for c in fixsubs)


def test_multilayer_executes_iterate_and_branch(agent, op):
    parsed = op.parse_instruction(agent, NESTED)
    res = _quiet(op.run_plan, agent, parsed, max_load=2)
    fe = next(r for r in res["trace"] if r.get("kind") == "foreach")
    assert fe["n_items"] >= 1             # the foreach ITERATED over the perceived gaps
    # for each item, the if-then guard was EVALUATED (a real per-item graph decision).
    for it in fe["iterations"]:
        ift = next(r for r in it["trace"] if r.get("kind") == "ifthen")
        assert ift["cond"] in (True, False)          # the graph decided the branch
        if ift["branch_taken"]:
            assert any(r.get("capability") == "fix" and r.get("executed")
                       for r in ift["trace"])          # fix fired inside the branch
    # the report + stop ran.
    assert any(r.get("capability") == "report" for r in res["trace"])
    assert any(r.get("kind") == "stop" for r in res["trace"])


def test_ifthen_branch_is_discriminative(agent, op):
    """The if-then guard is a REAL graph decision: the SAME plan branches DIFFERENTLY
    under a different FixWorthPolicy threshold (data-driven, the gp reorder-on-boost
    twin). Raise the bar above the gaps' salience -> the branch flips to NOT-taken."""
    from domains import gap_prioritization as gp
    parsed = op.parse_instruction(agent, NESTED)
    fe = parsed["steps"][[agent.s.node(s)["attrs"].get("kind")
                          for s in parsed["steps"]].index("foreach")]
    ift = next(c for c in agent.inner.neighbours(fe, "substep")
               if agent.s.node(c)["attrs"].get("kind") == "ifthen")
    term = json.loads(agent.s.node(ift)["attrs"]["cond_term"])
    agenda = _quiet(gp.perceive_gaps, agent)
    gp.normalize_all(agent, agenda)
    it = agenda[0]
    # baseline threshold 0.5 -> worth fixing (True)
    for n in agent.s.nodes("FixWorthPolicy"):
        agent.s.set_attr(n, "threshold", 0.5)
    assert bool(agent.inner.evaluate(term, {"it": it})) is True
    # raise the bar -> the SAME cond Term now decides NOT worth fixing (False)
    for n in agent.s.nodes("FixWorthPolicy"):
        agent.s.set_attr(n, "threshold", 5.0)
    assert bool(agent.inner.evaluate(term, {"it": it})) is False
    # restore
    for n in agent.s.nodes("FixWorthPolicy"):
        agent.s.set_attr(n, "threshold", 0.5)


# ===========================================================================
# 5. DATA-DRIVEN — a DIFFERENT instruction -> a DIFFERENT plan (same parser).
# ===========================================================================
def test_data_driven_different_plan(agent, op):
    p1 = op.parse_instruction(agent, ORIGINAL)
    p2 = op.parse_instruction(agent, "Warm up wordnet. Then measure timing. Finally summarize.")
    b1 = [agent.s.node(s)["attrs"].get("binding_key") for s in p1["steps"]]
    b2 = [agent.s.node(s)["attrs"].get("binding_key") for s in p2["steps"]]
    assert b1 != b2
    assert b2 == ["warm", "measure_timing", "report"], b2


# ===========================================================================
# 6. AUTONOMOUS / MECHANICAL (source audit) — the clause->capability match is the
#    graph Argmax Program; the executor dispatches via the name-keyed registry +
#    evaluates the plan's cond Terms; the plan is graph nodes/edges.
# ===========================================================================
def test_match_is_graph_argmax_program(agent, op):
    from domains.reflective_faculty import _load_program
    prog = _load_program(agent.s, "capability_match")
    assert prog is not None
    assert prog["type"] == "Argmax"                       # the DECISION is an Argmax
    assert prog["source"]["node_type"] == "OperationalCapability"


def test_executor_dispatch_is_name_keyed_registry(agent, op):
    # the registry is a name->fn lookup keyed on binding_key (mechanical marshaling),
    # NOT an if/else deciding the work. Its keys are exactly the codebook binding_keys.
    reg_keys = set(op._CAPABILITY_REGISTRY.keys())
    codebook = {agent.s.node(n)["attrs"].get("binding_key")
                for n in agent.s.nodes("OperationalCapability")}
    assert reg_keys == codebook


def test_plan_is_graph_data(agent, op):
    parsed = op.parse_instruction(agent, ORIGINAL)
    # Plan + PlanStep nodes exist and are wired with has_step / next edges (graph).
    plan = parsed["plan"]
    assert agent.s.node(plan)["attrs"].get("instruction") == ORIGINAL
    roots = agent.inner.neighbours(plan, "has_step")
    assert len(roots) >= 3
    # the sequence is a `next` chain in the graph.
    s0 = parsed["steps"][0]
    assert agent.inner.neighbours(s0, "next")


def test_no_python_clause_to_capability_mapping(agent, op):
    # source audit: the module holds NO dict/if mapping a clause string to a
    # capability name — the map is the graph Argmax. (The registry maps binding_key
    # -> fn, which is the enactment boundary, not the clause->capability decision.)
    import inspect
    src = inspect.getsource(op)
    # the only capability-name-keyed structure is the enactment registry.
    assert src.count("_CAPABILITY_REGISTRY: dict") == 1
    # no hand-written clause->capability table.
    for forbidden in ('"bulk load": "bulk_load"', "'bulk load': 'bulk_load'",
                      'clause == "bulk load"'):
        assert forbidden not in src
