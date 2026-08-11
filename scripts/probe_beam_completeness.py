#!/usr/bin/env python3
"""Read-only probe for GAMMA_SEARCH_COMPLETENESS_CEILING.md, Probe 3(c).

NOT part of the seed/domain/runner tree. Touches nothing under seeds/,
domains/, or runners/ — it only builds a throwaway in-memory substrate via
the existing `boot_core()` + `reflective_faculty.compose_design_for_goal`
entry points (the same harness shape `tests/test_transform_decode_migrated.py`
already uses for its own hand-built ShapeSignature parts) and calls the
composer twice, at two beam widths, over a hand-constructed goal signature
deliberately shaped as a "beam trap": at step 1 two single-relation parts tie
on coverage but differ sharply in `shape_fit`; the high-fit part leads to a
partial-coverage dead end, the low-fit part (discarded at beam=1, per
`eval_shape_decode`'s cross-state prune, shape_decode.rs ~line 1332) is the
only branch that reaches a fully-covering plan.

This does not prove how OFTEN the gap bites in the wild — it demonstrates
that the failure mode named in the correction section of
PROBLEM_DIFFICULTY_QUANTIFICATION_LITERATURE.md is real and trivially
constructible, not merely a theoretical worst case, and that the composer's
output carries no signal distinguishing "this is the only covering plan" from
"a wider beam might find a better one."

Runtime: well under a second. Read-only w.r.t. the repo (no writes anywhere;
the substrate built here is process-local and discarded on exit).
"""
from __future__ import annotations

import json
import sys

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf


def _add_part(s, name, signature, kind="faculty"):
    attrs = {"name": name, "signature": json.dumps(signature), "kind": kind}
    if kind == "faculty":
        attrs["faculty"] = name
    else:
        attrs["concept"] = name
    return s.add_node("ShapeSignature", attrs)


def run():
    s, ag = boot_core()

    # Classic greedy-set-cover adversarial construction (Johnson 1974 shape,
    # miniaturised to 4 elements), transplanted onto ShapeDecode's beam:
    #
    #   universe  {g1, g3, g2, g4}      (order matters -- see part_C below)
    #   OPTIMAL   {g1,g2} + {g3,g4}     2 parts, disjoint, full cover
    #   GREEDY    {g1,g3}               ties the optimal parts on COVERAGE
    #             (ncov=2 each) at step 1, wins the FIT tie-break by
    #             construction (its signature is POSITION-ALIGNED with the
    #             residual, shape_decode.rs's `shape_fit` -- see the
    #             module's `_add_part` calls below), then needs 2 MORE
    #             single-relation steps to finish (3 parts total) because
    #             nothing else covers {g2,g4} together.
    #
    # `eval_shape_decode`'s beam-wide prune (shape_decode.rs ~line 1332)
    # ranks strictly by (coverage DESC, total_fit DESC) at every step, so a
    # narrow beam keeps ONLY the higher-fit "greedy" state after step 1 and
    # discards the OPTIMAL state -- at max_steps=2 (the optimal's own step
    # count) the greedy branch cannot finish, the optimal branch would have.
    g1, g2, g3, g4 = ["e", "1"], ["e", "2"], ["e", "3"], ["e", "4"]
    goal = [g1, g3, g2, g4]

    _add_part(s, "part_A", [g1, g2])          # optimal half 1: covers {1,2}
    _add_part(s, "part_B", [g3, g4])          # optimal half 2: covers {3,4}
    _add_part(s, "part_C", [g1, g3])          # greedy: covers {1,3}, POSITION-
                                               # ALIGNED with residual[0:2] at
                                               # step 1 (goal[0:2] == [g1,g3])
                                               # -> max shape_fit, wins the tie
    _add_part(s, "part_only2", [g2])          # slow finisher for {2}
    _add_part(s, "part_only4", [g4])          # slow finisher for {4}

    results = {}
    for beam in (1, 2, 3):
        out = rf.compose_design_for_goal(s, goal, beam=beam, max_steps=2, cand_k=5)
        results[beam] = {
            "beam": beam,
            "authored": out.get("authored"),
            "covered_count": out.get("covered_count"),
            "goal_relations": out.get("goal_relations"),
            "residual": out.get("residual"),
            "ordered_parts": out.get("ordered_parts"),
            "total_fit": out.get("total_fit"),
        }

    print(json.dumps(results, indent=2, default=str))

    full = 4
    beam1_cov = results[1]["covered_count"]
    best_cov = max(r["covered_count"] for r in results.values())
    print()
    print(f"beam=1 covered {beam1_cov}/{full} at max_steps=2; "
          f"best-of-{{1,2,3}} covered {best_cov}/{full}")
    if beam1_cov < best_cov:
        print("CONFIRMED: beam=1 silently returns a strictly worse (incomplete) "
              "covering plan than a wider beam finds over the SAME codebook and "
              "goal -- and its output ('authored': true) carries no flag "
              "distinguishing this from a certified-optimal result.")
        return 0
    print("NOT REPRODUCED in this construction (beam width did not change the "
          "outcome) -- the trap needs re-shaping.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
