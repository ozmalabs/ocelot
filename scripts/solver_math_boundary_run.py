"""One-shot diagnostic runner for docs/research/engine_substrate/
SOLVER_MATH_BOUNDARY_PREREG.md — routes a real, hand-built, 15-problem math
battery through the REAL solver_dispatch toolbox (domains/solver_dispatch.py,
seven solve_* resolvers, dispatched via the UNCHANGED qd_bind_resolver JOIN)
and prints a per-problem outcome table. This is a MAPPING script, not a test
suite -- it is meant to be read (stdout captured into the RESULTS doc), not
asserted against in CI. Nothing here mutates the toolbox; it is a pure
caller exercising real, already-built machinery.

Usage: python3 scripts/solver_math_boundary_run.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import solver_dispatch as sd
from domains import problem_shape as ps
from domains import propositional_deduction as pd
from domains import problem_decomposition as pdec
from worlds import bigville_can_beliefs as bcb


def _pump(adapter, goal, max_iters: int = 32) -> None:
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        if adapter.s.node(goal)["attrs"].get("status") in ("resolved", "walled"):
            return


def _gap_count(adapter, gap_key) -> int:
    sub = adapter.s
    n = 0
    for node in sub.nodes("SelfConcern"):
        at = sub.node(node)["attrs"]
        if at.get("kind") == "solve_failure" and at.get("content") == gap_key:
            n += 1
    return n


def _shape_recognized(adapter, goal) -> str:
    """Run the real Rung-3 ProblemShape recognizer on this real Goal and
    report which ProblemShape (if any) it recognized as."""
    oid = ps.observe(adapter, goal)
    if oid is None:
        return "observe_failed"
    sub = adapter.s
    at = sub.node(oid)["attrs"]
    status = at.get("status")
    if status == "recognized":
        # `covered_by` is written as a plain attr (the winning ProblemShape's
        # own `name` string), not a graph edge -- confirmed live, not assumed
        # (an earlier version of this script wrongly read it as an edge).
        return "recognized:%s" % at.get("covered_by")
    return status or "unknown"


def build_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def run_solve_deduction(agent, label, statement, mode="auto"):
    goal = sd.mint_solve_deduction_goal(agent, statement, mode=mode)
    _pump(agent, goal)
    at = agent.s.node(goal)["attrs"]
    status = at.get("status")
    gap_key = at.get("gap_key")
    gap_filed = _gap_count(agent, gap_key) if gap_key else None
    shape = _shape_recognized(agent, goal)
    row = {
        "label": label,
        "statement": statement,
        "attempted_kind": "solve_deduction(mode=%s)" % mode,
        "status": status,
        "note": at.get("note"),
        "form_used": at.get("form_used"),
        "schema_name": at.get("schema_name"),
        "gap_key": gap_key,
        "gap_filed": gap_filed,
        "shape": shape,
    }
    return goal, row


def build_manual_can_mt(agent):
    """Hand-build a 3-concept CAN network for problem 13 (stress ->
    sleeplessness -> productivity), mirroring the SAME construction idiom
    every CAN toolbox test uses for a synthetic network
    (tests/test_can_junction_tree.py::_build_frustrated_draw). The sentence
    itself is NEVER ingested here -- the investigator builds this network by
    hand, exactly as SOLVER_MATH_BOUNDARY_PREREG.md Sec4 registers."""
    native = agent.inner
    bcb.install_productions(native)
    mt = native.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "3state",
                                          "can_tick": 0})
    stress = native.add_node("Concept", {"name": "stress", "state": 1.0,
                                          "external_field": 1.0, "identity_field": 0.0})
    sleepless = native.add_node("Concept", {"name": "sleeplessness", "state": 0.0,
                                             "external_field": 0.0, "identity_field": 0.0})
    productivity = native.add_node("Concept", {"name": "productivity", "state": 0.0,
                                                "external_field": 0.0, "identity_field": 0.0})
    for c in (stress, sleepless, productivity):
        native.add_edge(mt, "has_concept", c)
    # "stress increases sleeplessness" -> positive coupling
    native.add_edge(stress, "causal_influence", sleepless, {"weight": 1.0})
    native.add_edge(sleepless, "causal_influence", stress, {"weight": 1.0})
    # "sleeplessness decreases productivity" -> negative coupling
    native.add_edge(sleepless, "causal_influence", productivity, {"weight": -1.0})
    native.add_edge(productivity, "causal_influence", sleepless, {"weight": -1.0})
    return mt, {"stress": stress, "sleeplessness": sleepless, "productivity": productivity}


def main():
    agent = build_agent()
    rows = []

    # 1-4: arithmetic / algebra
    for label, stmt in [
        ("P1_arith_mult", "What is 17 * 23?"),
        ("P2_arith_div", "What is 144 divided by 12?"),
        ("P3_algebra", "Solve for x: 2x + 3 = 11"),
        ("P4_algebra", "Solve for x: 5x - 7 = 18"),
    ]:
        _, row = run_solve_deduction(agent, label, stmt)
        rows.append(row)

    # 5-8: logic, the toolbox's own documented scope
    for label, stmt in [
        ("P5_conditional", "If X is a fish, X can swim."),
        ("P6_bare_universal", "A bird can fly."),
        ("P7_explicit_universal", "All philosophers are mortal."),
        ("P8_existential", "Some bird is a penguin."),
    ]:
        _, row = run_solve_deduction(agent, label, stmt)
        rows.append(row)

    # 9: two-premise syllogism, AS LITERALLY PHRASED (the realistic case)
    goal9, row9 = run_solve_deduction(
        agent, "P9_syllogism_raw",
        "All men are mortal. Socrates is a man. Is Socrates mortal?")
    rows.append(row9)
    # 9b: the isolated first premise alone, to test the PRECISE claim that
    # solve_deduction can mint "all men are mortal" as knowledge but has no
    # path to apply it to "Socrates."
    goal9b, row9b = run_solve_deduction(agent, "P9b_syllogism_premise_only",
                                          "All men are mortal.")
    row9b["note_extra"] = ("mint-only check: does the resolver ANSWER "
                            "'is Socrates mortal' anywhere? No such attr "
                            "exists on this Goal or goal9 -- see script "
                            "source; solve_deduction has no second-fact "
                            "ingestion or query-answering step at all.")
    rows.append(row9b)

    # 10-11: word problems (arithmetic/geometry narrated in prose)
    for label, stmt in [
        ("P10_word_multistep", "Sarah has 3 apples. She buys 2 more bags of "
                                "4 apples each. How many apples does she "
                                "have now?"),
        ("P11_word_geometry", "A rectangular garden is 5m by 3m. If you "
                               "increase both sides by 2m, what is the new "
                               "area?"),
    ]:
        _, row = run_solve_deduction(agent, label, stmt)
        rows.append(row)

    # 12: decomposition-shaped word problem -- solve_deduction first (expect
    # wall), then an HONEST attempt at solve_decompose with NO real candidate
    # to build (empty candidate list -- there is no knowledge_logical schema
    # or CAN network this arithmetic-split problem projects onto).
    _, row12 = run_solve_deduction(
        agent, "P12_word_decomp",
        "Three friends split a $60 bill evenly. If two of them each pay $5 "
        "extra to cover the third, how much does the third person pay?")
    rows.append(row12)
    goal12b = sd.mint_solve_decompose_goal(agent, [], bound=4)
    _pump(agent, goal12b)
    at12b = agent.s.node(goal12b)["attrs"]
    rows.append({
        "label": "P12b_word_decomp_solve_decompose_attempt",
        "statement": "(same problem) -- attempted via solve_decompose with "
                     "an honest empty candidate list (no real "
                     "knowledge_logical/CAN projection exists for an "
                     "arithmetic bill-split problem)",
        "attempted_kind": "solve_decompose",
        "status": at12b.get("status"),
        "note": at12b.get("note"),
        "gap_key": at12b.get("gap_key"),
        "gap_filed": _gap_count(agent, at12b.get("gap_key")) if at12b.get("gap_key") else None,
        "shape": "n/a (solve_decompose Goal, not solve_deduction)",
    })

    # 13: CAN-shaped, hand-built network (real toolbox call, but the network
    # is investigator-built, never NL-extracted -- see PREREG Sec4).
    _, row13a = run_solve_deduction(
        agent, "P13a_can_shaped_raw_text",
        "Stress increases sleeplessness; sleeplessness decreases "
        "productivity. Given elevated stress, what happens to "
        "productivity?")
    rows.append(row13a)
    mt13, concepts13 = build_manual_can_mt(agent)
    goal13b = sd.mint_solve_can_exact_goal(agent, mt13, treewidth_bound=4)
    _pump(agent, goal13b)
    at13b = agent.s.node(goal13b)["attrs"]
    state13 = None
    if at13b.get("status") == "resolved":
        ans = at13b.get("answer") or {}
        raw_state = ans.get("state") or {}
        state13 = {
            name: raw_state.get(str(node)) if str(node) in raw_state
            else raw_state.get(node)
            for name, node in concepts13.items()
        }
    rows.append({
        "label": "P13b_can_shaped_handbuilt_network",
        "statement": "(same problem) -- attempted via solve_can_exact "
                     "against a MANUALLY-BUILT 3-concept CAN network "
                     "(stress->sleeplessness->productivity), sentence "
                     "itself never ingested",
        "attempted_kind": "solve_can_exact",
        "status": at13b.get("status"),
        "note": at13b.get("note"),
        "treewidth": at13b.get("treewidth"),
        "state_by_concept": state13,
        "concepts": concepts13,
        "gap_key": at13b.get("gap_key"),
    })

    # 14-15: combinatorial search / permutation
    for label, stmt in [
        ("P14_search", "Find the smallest positive integer that leaves "
                        "remainder 1 when divided by 2, 3, 4, 5, and 6."),
        ("P15_permutation", "How many distinct ways can 3 different books "
                             "be arranged on a shelf?"),
    ]:
        _, row = run_solve_deduction(agent, label, stmt)
        rows.append(row)

    # SUPPLEMENTARY (not part of the 15-problem battery, but a direct
    # follow-on the P7/P8/P9/P9b results demand): mode="auto" tries plain
    # `mint_logical_schema` (bare_universal, NO quantifier-word stripping)
    # BEFORE `mint_universal_schema`/`mint_existential_premise` -- if the
    # bare form already parses (which it always does for a leading "All"/
    # "Some" sentence, since "All X are Y" is itself grammatically a valid
    # bare-universal clause with subject "All X"), the auto ladder NEVER
    # reaches the dedicated quantifier-stripping parser at all. Checked
    # directly here by calling mode="universal"/"existential" EXPLICITLY on
    # the same statements, to see whether that produces a materially
    # different (correctly singularised / correctly quantifier-stripped)
    # schema than what mode="auto" actually minted above.
    for label, stmt, mode in [
        ("SUP_P7_explicit_universal_mode", "All philosophers are mortal.", "universal"),
        ("SUP_P9b_explicit_universal_mode", "All men are mortal.", "universal"),
        ("SUP_P8_explicit_existential_mode", "Some bird is a penguin.", "existential"),
    ]:
        _, row = run_solve_deduction(agent, label, stmt, mode=mode)
        rows.append(row)

    print(json.dumps(rows, indent=2, default=str))
    return rows


if __name__ == "__main__":
    main()
