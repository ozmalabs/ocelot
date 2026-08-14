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

UPDATED 2026-08-15 (docs/research/engine_substrate/
SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md): the two defects this file used to
pin as CURRENT behaviour are now FIXED --
`domains/propositional_deduction.py::parse_conditional` gates its
`bare_universal` branch on the general reader's own `speech_act` (a
question no longer fabricates an implication) and
`domains/solver_dispatch.py::solve_deduction`'s `mode="auto"` ladder now
tries the quantifier-aware parsers first (a leading "All"/"Some" statement
under mode="auto" now matches an explicit mode call). The tests below assert
the CORRECTED behaviour; see the bugfix RESULTS doc for the root-cause
trace, the live demonstration, and the regression proof that genuine
conditional/universal parsing is unchanged.
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
#  FIXED (2026-08-15, SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md Sec1) -- these
#  three used to be SILENT-WRONG: a bare numeric/measurement "is"-copula
#  QUESTION was not recognised as out-of-scope; it minted a fabricated
#  implication instead of honestly walling (the headline silent-failure
#  finding of SOLVER_MATH_BOUNDARY_RESULTS.md). Root cause: `parse_conditional`'s
#  `bare_universal` branch checked only the RELATION LABEL of the grounded
#  predication (`is_a`/`can`), never the general reader's own `speech_act`
#  verdict -- so a wh-QUESTION whose fallback grounding happens to produce an
#  `is_a(...)` predication (the reader's own honest behaviour for a genuine
#  copular wh-question, e.g. `_ground_question`'s no-main-verb fallback) was
#  laundered through as if it were a declarative conditional/universal
#  STATEMENT. Fixed by gating `bare_universal` on
#  `whole.get("speech_act") == "question"` (`domains/propositional_
#  deduction.py::parse_conditional`) -- a conditional/universal premise is,
#  by definition, a declarative assertion, never a question. All three of
#  these pinned cases end in '?' and share this exact root cause (confirmed
#  live, not assumed -- see the RESULTS doc); the task named only the first
#  by name, but the SAME single-gate fix corrects all three, so all three are
#  updated here rather than leaving two of them silently un-pinned.
# --------------------------------------------------------------------------- #
def test_arithmetic_expression_now_walls_honestly(agent):
    """'What is 17 * 23?' is a QUESTION, not a conditional/universal
    statement -- it now walls honestly (no schema minted) instead of minting
    the fabricated `logical_17_23` implication this test used to pin."""
    row = _run(agent, "What is 17 * 23?")
    assert row["status"] == "walled"
    assert row["gap_key"] == "solve_deduction:What is 17 * 23?"
    assert row["schema_name"] is None


def test_geometry_word_problem_now_walls_honestly(agent):
    row = _run(agent, "A rectangular garden is 5m by 3m. If you increase "
                       "both sides by 2m, what is the new area?")
    assert row["status"] == "walled"
    assert row["schema_name"] is None


def test_two_premise_syllogism_now_walls_honestly(agent):
    """The sharpest boundary case, corrected: solve_deduction has NO
    second-fact ingestion and NO query-answering step at all (verified by
    direct read of domains/propositional_deduction.py -- mint_logical_schema/
    mint_universal_schema/mint_existential_premise only ever install ONE
    ShapeSignature from ONE statement; nothing in domains/solver_dispatch.py's
    solve_deduction calls inference_generation.detect_implication_gaps/
    resolve_implication_gap, the facility that would actually apply a premise
    to a fact). Given the full three-sentence syllogism as raw text, it used
    to resolve into a mangled cross-sentence word blob
    ('logical_all_men_mortal_socrates', fusing words from two different
    sentences); it now walls honestly instead, because the statement (like
    the whole battery's other two silent-wrong cases) is itself a QUESTION
    ("...Is Socrates mortal?") and the bare_universal speech-act gate refuses
    it. `solve_deduction` still has no query-answering step (that remains a
    real, separate, out-of-scope capability boundary -- see
    SOLVER_MATH_BOUNDARY_RESULTS.md Sec5) -- the fix only stops it from
    fabricating a wrong-shaped answer where it has none."""
    row = _run(agent, "All men are mortal. Socrates is a man. Is Socrates "
                       "mortal?")
    assert row["status"] == "walled"
    assert row["schema_name"] is None


# --------------------------------------------------------------------------- #
#  FIXED (2026-08-15, SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md Sec2) -- the
#  MODE=AUTO LADDER-ORDERING FINDING. A leading "All"/"Some" quantifier
#  sentence used to resolve via the auto ladder's bare_universal reading
#  BEFORE the dedicated quantifier-stripping parser ever got a chance
#  (mint_logical_schema, tried first, already succeeded), producing a
#  worse-quality schema (unstripped 'all_philosophers'/'some_bird' blob
#  antecedent) than calling mode='universal'/'existential' explicitly would.
#  Fixed by reordering the ladder (domains/solver_dispatch.py::solve_deduction)
#  to try the quantifier-aware parsers FIRST (universal -> existential ->
#  conditional) -- safe for every non-quantified statement because both
#  quantifier-aware parsers refuse in O(1) (one first-word lexicon check, no
#  reading-pipeline call) whenever no leading quantifier word is present, so
#  a plain conditional/indefinite-bare-universal statement falls straight
#  through to the unchanged `mint_logical_schema`. mode="auto" now reaches
#  parity with an explicit mode call whenever a real quantifier is present.
#  Pinned on both sides -- both now assert the SAME (correct) schema.
# --------------------------------------------------------------------------- #
def test_auto_mode_now_strips_leading_universal_quantifier(agent):
    row = _run(agent, "All philosophers are mortal.", mode="auto")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_universal_philosopher_mortal"  # correctly stripped now
    assert row["form_used"] == "universal"


def test_explicit_universal_mode_DOES_strip_the_quantifier(agent):
    row = _run(agent, "All philosophers are mortal.", mode="universal")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_universal_philosopher_mortal"  # correctly singularised


def test_auto_mode_leaves_a_plain_conditional_unchanged(agent):
    """Regression proof for the ladder reorder: a genuinely non-quantified
    conditional statement is byte-identical (same schema, same form_used)
    to what mode='auto' produced before this bugfix."""
    row = _run(agent, "If X is a fish, X can swim.", mode="auto")
    assert row["status"] == "resolved"
    assert row["schema_name"] == "logical_fish_can_swim"
    assert row["form_used"] == "conditional"


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
