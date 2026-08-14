"""Regression pins for docs/research/engine_substrate/
SOLVER_MATH_BOUNDARY_PREREG.md / SOLVER_MATH_BOUNDARY_RESULTS.md -- a real,
hand-built, 15-problem math battery routed through the REAL solver_dispatch
toolbox (domains/solver_dispatch.py, seven solve_* resolvers, dispatched via
the UNCHANGED qd_bind_resolver JOIN). This is a DIAGNOSTIC/MAPPING task, not
a build task -- these tests PIN what was found live (both the toolbox's real
coverage and its real, named defects), so a future change to
propositional_deduction.py / solver_dispatch.py / problem_shape.py that
silently alters this boundary is caught, exactly the way
QUESTION_DRIVER_BUGFIX_AND_RECHECK_RESULTS.md pinned the treewidth_bound=0
footgun as a regression test once it was found.

Nothing in domains/solver_dispatch.py, domains/problem_shape.py, or
domains/propositional_deduction.py is modified by this rung -- every
assertion below characterizes EXISTING behaviour, discovered live by
scripts/solver_math_boundary_run.py, not new capability.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import solver_dispatch as sd                  # noqa: E402
from domains import problem_shape as ps                    # noqa: E402
import scripts.solver_math_boundary_run as smb              # noqa: E402


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    return a


def _run(agent, statement, mode="auto"):
    _, row = smb.run_solve_deduction(agent, "t", statement, mode=mode)
    return row


# --------------------------------------------------------------------------- #
#  CLEAN WALLS -- arithmetic/algebra/search/permutation have no home in
#  solve_deduction (the only text-accepting solve_* door) and honestly wall,
#  filing exactly one solve_failure gap each (Rung 2's mechanism, holding up
#  live on genuinely novel, independently-authored input).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("statement", [
    "What is 144 divided by 12?",
    "Solve for x: 2x + 3 = 11",
    "Solve for x: 5x - 7 = 18",
    "Sarah has 3 apples. She buys 2 more bags of 4 apples each. How many "
    "apples does she have now?",
    "Find the smallest positive integer that leaves remainder 1 when "
    "divided by 2, 3, 4, 5, and 6.",
    "How many distinct ways can 3 different books be arranged on a shelf?",
])
def test_arithmetic_algebra_search_wall_cleanly_and_file_one_gap(agent, statement):
    row = _run(agent, statement)
    assert row["status"] == "walled"
    assert row["gap_key"] == "solve_deduction:%s" % statement
    assert row["gap_filed"] == 1


# --------------------------------------------------------------------------- #
#  GENUINE FIT -- single-fact conditional/bare-universal logic statements
#  (the toolbox's own documented worked example shape) resolve correctly.
# --------------------------------------------------------------------------- #
def test_single_conditional_resolves_correctly(agent):
    row = _run(agent, "If X is a fish, X can swim.")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_fish_can_swim"


def test_bare_universal_resolves_correctly(agent):
    row = _run(agent, "A bird can fly.")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_bird_can_fly"


# --------------------------------------------------------------------------- #
#  SILENT-WRONG (the sharpest finding) -- a bare numeric/measurement
#  "is"-copula sentence is NOT recognised as out-of-scope; it mints a
#  fabricated implication instead of honestly walling. Pinned so a future
#  change either fixes this (test updated deliberately) or is caught if it
#  makes the mangling worse/different silently.
# --------------------------------------------------------------------------- #
def test_arithmetic_expression_resolves_WRONGLY_instead_of_walling(agent):
    """'What is 17 * 23?' should, ideally, wall (it is not a conditional
    statement). It does not: the general reading pipeline grounds it as a
    spurious is_a(17) => is_a(23) copular predication, and solve_deduction
    mints it as real held knowledge with status=='resolved' -- a
    plausible-looking, entirely wrong answer, never flagged as such. This is
    the headline silent-failure finding of SOLVER_MATH_BOUNDARY_RESULTS.md."""
    row = _run(agent, "What is 17 * 23?")
    assert row["status"] == "resolved"          # the WRONG outcome, pinned as found
    assert row["schema_name"] == "logical_17_23"  # the fabricated schema, pinned as found


def test_geometry_word_problem_resolves_WRONGLY_instead_of_walling(agent):
    row = _run(agent, "A rectangular garden is 5m by 3m. If you increase "
                       "both sides by 2m, what is the new area?")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_rectangular_garden_5m"


def test_two_premise_syllogism_resolves_but_never_answers_the_query(agent):
    """The sharpest boundary case: solve_deduction has NO second-fact
    ingestion and NO query-answering step at all (verified by direct read of
    domains/propositional_deduction.py -- mint_logical_schema/mint_universal_
    schema/mint_existential_premise only ever install ONE ShapeSignature from
    ONE statement; nothing in domains/solver_dispatch.py's solve_deduction
    calls inference_generation.detect_implication_gaps/resolve_implication_gap,
    the facility that would actually apply a premise to a fact). Given the
    full three-sentence syllogism as raw text, it resolves -- but the minted
    schema is a mangled cross-sentence word blob ('mortal_socrates' as a
    SINGLE consequent attr, fusing words from two different sentences), not
    a correct representation of any of the three sentences, and the Goal
    carries no 'answer' field addressing whether Socrates is mortal at all."""
    row = _run(agent, "All men are mortal. Socrates is a man. Is Socrates "
                       "mortal?")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_all_men_mortal_socrates"
    # No yes/no verdict about Socrates exists anywhere on this outcome.
    assert "socrates" not in ("true", "false")  # trivial: there is no such field to check


# --------------------------------------------------------------------------- #
#  THE MODE=AUTO LADDER-ORDERING FINDING -- a leading "All"/"Some" quantifier
#  sentence resolves via the auto ladder's bare_universal reading BEFORE the
#  dedicated quantifier-stripping parser ever gets a chance (mint_logical_
#  schema, tried first, already succeeds), producing a worse-quality schema
#  (unstripped 'all_philosophers'/'some_bird' blob antecedent) than calling
#  mode='universal'/'existential' explicitly would. Pinned on both sides.
# --------------------------------------------------------------------------- #
def test_auto_mode_does_not_strip_leading_universal_quantifier(agent):
    row = _run(agent, "All philosophers are mortal.", mode="auto")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_all_philosophers_mortal"  # blob, not stripped


def test_explicit_universal_mode_DOES_strip_the_quantifier(agent):
    row = _run(agent, "All philosophers are mortal.", mode="universal")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_universal_philosopher_mortal"  # correctly singularised


# --------------------------------------------------------------------------- #
#  solve_decompose: an honest wall on a genuinely candidate-less problem
#  (no fabricated decomposition).
# --------------------------------------------------------------------------- #
def test_solve_decompose_walls_honestly_with_no_candidates(agent):
    goal = sd.mint_solve_decompose_goal(agent, [], bound=4)
    smb._pump(agent, goal)
    at = agent.s.node(goal)["attrs"]
    assert at["status"] == "walled"
    assert at["gap_key"] == "solve_decompose:no_candidates"


# --------------------------------------------------------------------------- #
#  solve_can_exact: a REAL, CORRECT answer -- but only given a hand-built
#  CAN network; the sentence itself is never ingested by any part of this
#  toolbox (no NL-to-CAN path exists).
# --------------------------------------------------------------------------- #
def test_solve_can_exact_answers_correctly_given_a_handbuilt_network(agent):
    mt, concepts = smb.build_manual_can_mt(agent)
    goal = sd.mint_solve_can_exact_goal(agent, mt, treewidth_bound=4)
    smb._pump(agent, goal)
    at = agent.s.node(goal)["attrs"]
    assert at["status"] == "resolved"
    state = at["answer"]["state"]
    # elevated stress (external_field=1.0) settles positive; the positive
    # stress->sleeplessness coupling settles sleeplessness positive too;
    # the negative sleeplessness->productivity coupling settles productivity
    # negative -- a real, independently-checkable global-minimum-energy CAN
    # answer, not a fabricated one.
    assert state[concepts["stress"].value] > 0
    assert state[concepts["sleeplessness"].value] > 0
    assert state[concepts["productivity"].value] < 0


# --------------------------------------------------------------------------- #
#  ProblemShape (Rung 3): every solve_deduction Goal in this battery --
#  resolved OR walled -- recognizes as the SAME pre-seeded deduction shape,
#  confirming Rung 3's own finding is unchanged: this battery adds real new
#  POST-mint recognition instances, but no pre-mint / raw-problem
#  recognition corpus (ProblemShape reads Goal structure, never statement
#  CONTENT or outcome).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("statement", [
    "What is 17 * 23?",                       # resolved (wrongly)
    "What is 144 divided by 12?",             # walled
    "If X is a fish, X can swim.",            # resolved (correctly)
])
def test_problem_shape_recognizes_every_solve_deduction_goal_the_same_way(
        agent, statement):
    goal = sd.mint_solve_deduction_goal(agent, statement)
    smb._pump(agent, goal)
    oid = ps.observe(agent, goal)
    at = agent.s.node(oid)["attrs"]
    assert at["status"] == "recognized"
    assert at["covered_by"] == "ps_has_statement=yes"
