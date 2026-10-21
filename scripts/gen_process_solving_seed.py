#!/usr/bin/env python3
"""Author the `process_solving` seed (Track I, I2.7 / I5.2 harness for tasks).

A `SolveTask{domain, state, goal}` is worked by ONE generic strategy rule:
greedy means-ends descent. Each step applies the active process in the task's
domain (held or invented) whose result is closest to the goal by Hamming
distance, cheapest first on ties, and only if it strictly reduces the
distance. When no process reduces it, the task is `stuck`: an impasse the
graph answers elsewhere (an invention round in `invention_round`, a wall
explanation in `invariant_miner`). When the domain's process library grows
past what the task last saw, a stuck task retries.

This is a fixed, hand-written, domain-neutral strategy (hill-climbing on a
distance), not a puzzle solver: nothing here knows Loopover, 3-cycles or
piece placement. Replacing it with an agent-found strategy is I3.4, which
is blocked on goal regression (I5.1 / P5.E4).

Every step is appended to `trace` (the process nodes used), which library
learning (I3.2) reads.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Append, Argmin, Count, Eq, Filter, Gt, Gte, IfThenElse, L, Let, Lt, MinOver,
    N, Not, ONLINE_AREA, Or, PApply, Plus, T, Times, Union, V, ZERO, hamming, is_none,
    policy_on, productions, rule,
)

SEED_ID = "process_solving"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"
FAR = 1.0e9


def candidates():
    return Filter(Union(N("d", "has_held_process"), N("d", "has_invented_process")), "c",
                  Eq(A("c", "status"), L("active")))


def dist_after(var):
    after = PApply(A(var, "params"), A("t", "state"))
    return IfThenElse(is_none(after), L(FAR), hamming(after, A("t", "goal")))


def current_dist():
    return hamming(A("t", "state"), A("t", "goal"))


def best():
    return Argmin(candidates(), "c", Plus(Times(dist_after("c"), L(1.0e6)), A("c", "cost")))


def best_dist():
    return MinOver(candidates(), "c", dist_after("c"), L(FAR))


MATCH = [
    ["agent", "has_solver_policy", "pol"],
    ["agent", "has_solve_task", "t"],
    ["t", "about_domain", "d"],
]


def step_rule():
    with_best = lambda term: T(Let("bp", best(), term))  # noqa: E731
    return rule(
        "sv_greedy_step", ONLINE_AREA, 10,
        "Apply the domain process that most reduces Hamming distance to the goal "
        "(cheapest on ties), only if it strictly reduces it. One step per pass per task.",
        MATCH,
        And(policy_on(), Eq(A("t", "status"), L("active")), Gt(current_dist(), ZERO),
            Lt(A("t", "steps"), A("pol", "max_steps")), Lt(best_dist(), current_dist())),
        [
            ["set_attr", "t", "state", with_best(PApply(A("bp", "params"), A("t", "state")))],
            ["set_attr", "t", "steps", T(Plus(A("t", "steps"), L(1)))],
            ["set_attr", "t", "moves", with_best(Plus(A("t", "moves"), A("bp", "cost")))],
            ["set_attr", "t", "trace", with_best(Append(A("t", "trace"), V("bp")))],
        ],
    )


def solved_rule():
    return rule(
        "sv_solved", ONLINE_AREA, 11, "A task whose state equals its goal is solved.",
        MATCH,
        And(policy_on(), Eq(A("t", "status"), L("active")), Eq(current_dist(), ZERO)),
        [["set_attr", "t", "status", "solved"]],
    )


def stuck_rule():
    return rule(
        "sv_stuck", ONLINE_AREA, 12,
        "Impasse: no process in the domain reduces the distance (or the step bound is hit). "
        "Record how many processes the task has seen so it can retry when the library grows.",
        MATCH,
        And(policy_on(), Eq(A("t", "status"), L("active")), Gt(current_dist(), ZERO),
            Or(Gte(best_dist(), current_dist()), Gte(A("t", "steps"), A("pol", "max_steps")))),
        [
            ["set_attr", "t", "status", "stuck"],
            ["set_attr", "t", "tools_seen", T(Count(candidates()))],
            ["set_attr", "t", "stuck_count", T(Plus(A("t", "stuck_count"), L(1)))],
        ],
    )


def retry_rule():
    return rule(
        "sv_retry_when_library_grows", ONLINE_AREA, 13,
        "A stuck task retries once the domain holds more active processes than it last saw.",
        MATCH,
        And(policy_on(), Eq(A("t", "status"), L("stuck")), Lt(A("t", "steps"), A("pol", "max_steps")),
            Gt(Count(candidates()), A("t", "tools_seen"))),
        [["set_attr", "t", "status", "active"]],
    )


def build():
    specs = [
        ("Agent", "has_solver_policy", "SolverPolicy"),
        ("Agent", "has_solve_task", "SolveTask"),
        ("SolveTask", "about_domain", "ProcessDomain"),
    ]
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": ["process_schema"],
        "self_load_only": True,
        "area": ONLINE_AREA,
        "description": (
            "Track I: generic greedy means-ends solving of SolveTasks with a domain's held and "
            "invented processes; impasses are left for invention and wall explanation."
        ),
        "microtheory": {
            "name": SEED_ID,
            "description": "Use the process that brings the state closest to the goal; stop when none helps.",
        },
        "nodes": [
            {"local_id": 0, "type": "SolverPolicy", "attrs": {
                "name": "core_solver_policy", "enabled": 0.0, "max_steps": 400.0}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_solver_policy", "tgt": {"local": 0}, "attrs": {}},
        ],
        "productions": productions(SEED_ID, specs),
        "rules": [step_rule(), solved_rule(), stuck_rule(), retry_rule()],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
