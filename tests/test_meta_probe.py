"""CHARACTERIZATION of the CURRENT meta-planning state (NOT a new capability).

Pins the finding of scripts/jabberwock_plans_bulk_load.py: the jabberwock can do
the OBJECT-level self-assessment itself, but CANNOT turn a natural-language
operational instruction into an ordered sub-goal plan over its held
load/measure/perceive capabilities. These tests assert what CURRENTLY happens
(the meta-gaps), so a future meta-planner build would visibly flip them.
"""
from __future__ import annotations
import io, contextlib
import pytest


@pytest.fixture(scope="module")
def agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


INSTRUCTION = ("Do a bulk load of Wikipedia. Identify if it is sufficiently fast. "
               "Identify if there are other gaps.")


def test_operational_instruction_does_not_become_a_subgoal_plan(agent):
    """META-GAP 1: comprehend_text flattens the whole operational instruction to
    ONE polar KNOW query -- no ordered sub-goal plan, no capability binding."""
    from domains import comprehend_text as ct
    c = ct.comprehend_text(agent, INSTRUCTION)
    # It is comprehended as a single (question/know) turn, NOT a plan.
    assert c.dispatch.get("path") in ("know", "instruction", "table")
    # There is NO plan / sub-goal / capability-binding field anywhere in it.
    for key in ("plan", "subgoals", "sub_goals", "steps", "sequence"):
        assert key not in (c.dispatch or {}), f"unexpected plan field {key!r}"
    assert not hasattr(c, "plan")
    # The three operational verbs collapse to ONE relation (predicate = last verb).
    assert c.relation is not None
    assert (c.relation.get("predicate") or {}).get("surface") == "Identify"


def test_composer_has_no_operational_capability_parts(agent):
    """META-GAP 2: the composer 'authors' a plan for an operational goal, but
    only by decoding it against the INK-STROKE codebook (goal_source is a
    stroke/character signature). No operational capability is a part."""
    from domains import reflective_faculty as rf
    out = rf.compose_design_for_concept(agent.s, "bulk load of wikipedia")
    assert out.get("authored") is True         # it does NOT wall -- it false-positives
    src = str(out.get("goal_source") or "").lower()
    assert ("stroke" in src) or ("character" in src), \
        f"expected an ink/character decode, got goal_source={src!r}"
    # the codebook holds NO operational-capability signatures.
    sigs = [agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("ShapeSignature")]
    ops = ("load", "timing", "wikipedia", "consume", "perceive", "latency",
           "sufficien", "warm_wordnet")
    op_sigs = [s for s in sigs if s and any(o in str(s).lower() for o in ops)]
    assert op_sigs == [], f"unexpected operational signatures: {op_sigs}"


def test_self_improvement_cycles_take_no_instruction(agent):
    """META-GAP 3: the self-improvement cycles are FIXED -- they accept no
    instruction/goal parameter, so they cannot be commanded to run this task."""
    import inspect
    from domains import research_agenda as ra
    from domains import gap_prioritization as gp
    ra_params = set(inspect.signature(ra.run_cycle).parameters) - {"agent"}
    gp_params = set(inspect.signature(gp.run_cycle).parameters) - {"agent"}
    # no 'instruction' / 'goal' / 'task' entry point on either cycle.
    for p in ("instruction", "goal", "task", "command"):
        assert p not in ra_params and p not in gp_params
    # gap_prioritization.run_cycle takes ONLY the agent (a pure fixed cycle).
    assert gp_params == set()
