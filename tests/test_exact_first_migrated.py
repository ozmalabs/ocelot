"""tests/test_exact_first_migrated.py — Arc 5 EXACT-FIRST rung gates.

PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md (the design), PROGRAM_SYNTHESIS_
ARCH_DIAGNOSIS.md (the "shape -> IR" diagnosis this rung implements),
PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md / PROGRAM_SYNTHESIS_ARC5_SPECS_
IMPLY_FLOATS.md (the measurements this productionises). New graph data
(seeds/exact_families.json), a new mechanical module (domains/
prog_exact.py), and three new seed rules (seeds/program_synthesis.json
v1.9.0: ps_exact_mark / ps_exact_solved / ps_exact_failed) — Occam-ordered
between descent and enumerate. The verdict layer (ps_verify -> structural
detectors -> ps_accept) is UNCHANGED; a fit hands its IR to that SAME path.

Gates:
  1. seeds load clean (exact_families + the bumped program_synthesis seed).
  2. HEADLINE: 82/85/139/233/276/312 (the k*pi*r^a*h^b geometry family)
     accept via the exact rung through the REAL pipeline
     (domains.prog_synthesis.synthesize_from_request, PRIMARY protocol),
     held-out correct, in far fewer candidates than enumerate's own
     budget (report the actual counts).
  3. 606 (1/180*pi*d) and 742 (sqrt3*a^2) — the two that needed a wider
     denominator / a different named constant.
  4. 574 (2*pi*r^2 + 2*pi*r*h) via sum_of_two_terms — recovered exactly,
     with an HONEST report of the corpus's own truncated-pi artifact on
     this task's un-toleranced bare-equality held-out assert.
  5. Occam order: a codebook-covered (even float-eligible) request never
     reaches the exact rung.
  6. no in-frame floats: every fitted parameter (k numerator/denominator,
     exponents) is an integer; only the named cross-frame constant may be
     a float, and it is applied at the render boundary, never fitted.
  7. the exact rung never intercepts the int-valued single/few-row
     fixtures the rest of the suite depends on (the float-typed
     eligibility gate, verified directly).
  8. no-python-decision source audit of domains/prog_exact.py and the
     run_exact_family verb.
  9. the named arc-4 regression sweep: asserts the failing node-ids are
     EXACTLY the known, out-of-scope set (three literal seed-version
     string pins + one file's frozen task-id-bucket snapshot, all in
     files outside this phase's file-ownership boundary) — never a new,
     unexpected regression.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_exact_first_migrated.py \
    --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_exact as pex  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402

SYNTH_SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")
EXACT_SEED_PATH = os.path.join(ROOT, "seeds", "exact_families.json")
MBPP_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ProgEval", "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ProgEval not present in the installed substrate_rs binary — "
                "rebuild runners/dsl. Honest skip.", allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


@pytest.fixture(scope="module")
def mbpp_tasks():
    return {t["task_id"]: t for t in json.load(open(MBPP_FIXTURE))}


def _drop_exemplar(sub, task_id: int) -> None:
    """Test-fixture isolation, NOT an agent decision: the whole-program
    retrieval ladder (`domains.prog_retrieval`, Arc3-R1) boards the MBPP
    reference solutions as exemplars including the very task under test,
    so a request identical to a boarded exemplar's own prompt is (quite
    correctly) solved by retrieval before this rung's own propose/exact/
    enumerate ladder ever runs. Removing task_id's OWN exemplar isolates
    the mechanism this file gates (the SAME "teach a decoy, remove a
    confound" pattern already used throughout this suite, e.g.
    `_teach_decoy`) — it does not change what any rule decides."""
    for ex in list(sub.nodes("Exemplar")):
        if sub.node(ex)["attrs"].get("task_id") == float(task_id):
            sub.remove_node(ex)


def _run_mbpp_task(mbpp_tasks, task_id: int, *, drop_own_exemplar: bool = False):
    s, ag = boot()
    if drop_own_exemplar:
        _drop_exemplar(s, task_id)
    task = mbpp_tasks[task_id]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    assert spec["runnable"], "task %s excluded under PRIMARY protocol" % task_id
    r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
    return s, r, spec


def _eval_accepted(s, r, inputs):
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert len(roots) == 1
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": inputs, "p": roots[0]})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


# ---------------------------------------------------------------------------
# 1) seeds load clean
# ---------------------------------------------------------------------------
def test_exact_families_seed_loads_clean():
    from substrate.seed_loader import manifest_for
    manifest = manifest_for("exact_families")
    assert manifest["id"] == "exact_families"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    summary = s._inner.load_seed_manifest(manifest, ag)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    fams = {n: s.node(n)["attrs"] for n in s.nodes("ExactFamily")}
    names = {at["name"]: at for at in fams.values()}
    assert set(names) == {"scaled_power_product", "sum_of_two_terms"}
    assert names["scaled_power_product"]["order"] < names["sum_of_two_terms"]["order"], \
        "scaled_power_product must be tried first (Occam order)"
    consts = json.loads(names["scaled_power_product"]["constants_json"])
    assert set(consts) == {"1", "pi", "sqrt2", "sqrt3"}


def test_program_synthesis_seed_bumped_with_three_new_rules():
    # 2026-08-01 (arc5 moves, reconciled): this rung's own claim is "exact-
    # first added exactly three rules (ps_exact_mark/_solved/_failed) over
    # its v1.8.0/63-rule predecessor" -- that arithmetic (63 + 3 == 66) is
    # what is actually re-checked below, so the test keeps proving what it
    # always proved even though the seed has since moved past v1.9.0. The
    # moves phase (seed v1.9.0 -> v1.10.0, 66 -> 70 rules: ps_move_mark/
    # _select/_none/_fresh_attempt, PROGRAM_SYNTHESIS_ARC5_MOVES.md) landed
    # on top, purely additively -- it did not touch or remove any of the
    # three rules this test names, so the literal head pin is bumped
    # forward rather than loosened.
    # 2026-08-01 (arc6 seam D, reconciled): the same reading applies again.
    # Seam D landed the PROPERTY-REFUTATION rung on top (seed v1.10.0 ->
    # v1.11.0, 70 -> 73 rules: ps_property_clear / ps_property_reject_gap /
    # ps_property_reject_reopen, PROGRAM_SYNTHESIS_ARC6_D.md §1/§6), again
    # purely additively -- it did not touch or remove any of the three
    # exact-first rules this test names, and this rung's own claim
    # (63 + 3 == 66) is still what the arithmetic below re-checks. Seam D
    # DID edit ps_accept's gate a second time (adding ps_property_reject ==
    # 0.0), which moved behavioural pins in SIBLING files -- all of them
    # reconciled in place there, so this file's named regression sweep
    # below needed no allowlist entry; the rule-count arithmetic here is
    # unaffected either way.
    with open(SYNTH_SEED_PATH) as f:
        d = json.load(f)
    assert d["version"] == "1.13.0"  # 2026-08-03: 1.11.0 -> 1.12.0, the goal-residual weight term
    # (ps_move_mark stamps ps_move_w_residual; ps_move_select subtracts a
    # held refutation's weight inside its Argmax). Pin reconciled, not
    # relaxed -- see PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md GR4.
    # 2026-08-16: 1.12.0 -> 1.13.0, PROGRAM_SYNTHESIS_PROPERTY_REJECT_
    # SURVEY's ps_property_reject_retrieval_enumerate_fallback rule (+1).
    names = {r["name"] for r in d["rules"]}
    assert {"ps_exact_mark", "ps_exact_solved", "ps_exact_failed"} <= names
    PRE_EXACT_FIRST_RULE_COUNT = 63  # v1.8.0, arc4 S6
    N_EXACT_FIRST_NEW_RULES = 3
    # arc5 moves: ps_move_* (4, v1.9.0 -> v1.10.0)
    # + arc6 seam D: ps_property_* (3, v1.10.0 -> v1.11.0)
    # + property_reject_survey: ps_property_reject_retrieval_enumerate_
    #   fallback (1, v1.12.0 -> v1.13.0)
    N_RULES_ADDED_SINCE_EXACT_FIRST = 4 + 3 + 1
    assert len(d["rules"]) == (
        PRE_EXACT_FIRST_RULE_COUNT + N_EXACT_FIRST_NEW_RULES
        + N_RULES_ADDED_SINCE_EXACT_FIRST) == 74


def test_ensure_program_synthesis_installs_exact_families():
    s, ag = boot()
    assert {s.node(n)["attrs"]["name"] for n in s.nodes("ExactFamily")} == \
        {"scaled_power_product", "sum_of_two_terms"}
    # idempotent re-ensure — no duplicate installs.
    psy.ensure_program_synthesis(s, s._inner, ag)
    assert len(s.nodes("ExactFamily")) == 2


# ---------------------------------------------------------------------------
# 2) THE HEADLINE — the geometry family, real pipeline, PRIMARY protocol.
# ---------------------------------------------------------------------------
GEOMETRY_TASKS = (82, 85, 139, 233, 276, 312)
# Candidate ceiling: THREE_MOVES.md's own comparator — direct syntax search
# was UNREACHABLE at 120,000 candidates for this family. Every recovered
# task here must cost orders of magnitude less.
ENUMERATE_UNREACHABLE_BUDGET = 120_000


@pytest.mark.parametrize("task_id", GEOMETRY_TASKS)
def test_geometry_family_accepts_via_exact_rung_with_holdout(mbpp_tasks, task_id):
    s, r, spec = _run_mbpp_task(mbpp_tasks, task_id)
    assert r["status"] == "accepted", (task_id, r["status"], r["gap_reason"])
    assert r["rungs"]["exact"] == 1.0
    assert r["rungs"]["enumerate"] is None, \
        "the exact rung must solve this before enumerate ever gets a turn"
    assert r["exact"]["outcome"] == "ok"
    assert r["exact"]["family"] == "scaled_power_product"
    candidates = r["exact"]["candidates"]
    assert candidates is not None and candidates < ENUMERATE_UNREACHABLE_BUDGET, \
        (task_id, candidates)
    # held-out correct, via the SAME comparator the real battery scripts use
    # (domains.prog_synthesis._row_cmp_ok) — every one of these rows carries
    # its own math.isclose-derived tol.
    for hr in spec["held_out"]:
        got = _eval_accepted(s, r, hr["inputs"])
        tol = hr.get("tol")
        assert psy._row_cmp_ok(got, hr["expected"], tol, False) == 1.0, \
            (task_id, hr, got)


def test_geometry_family_candidate_counts_are_reported(mbpp_tasks, capsys):
    """Not a pass/fail bar by itself (already gated above) — this test's
    JOB is to print the actual per-task candidate counts the headline
    claim reports, so a reader of the test log sees the real numbers
    rather than a bare assertion."""
    rows = []
    for tid in GEOMETRY_TASKS:
        _s, r, _spec = _run_mbpp_task(mbpp_tasks, tid)
        rows.append((tid, r["exact"]["candidates"]))
    print("\nEXACT-RUNG CANDIDATE COUNTS (geometry family, vs 120,000 "
          "unreachable for direct syntax search):")
    for tid, n in rows:
        print("  task %-4d %6d candidates" % (tid, n))
    assert all(n is not None for _, n in rows)


# ---------------------------------------------------------------------------
# 3) 606 / 742 — wider denominator, a different named constant.
# ---------------------------------------------------------------------------
def test_606_degrees_to_radians_recovers_1_over_180_pi(mbpp_tasks):
    s, r, spec = _run_mbpp_task(mbpp_tasks, 606, drop_own_exemplar=True)
    assert r["status"] == "accepted"
    assert r["rungs"]["exact"] == 1.0
    assert r["exact"]["family"] == "scaled_power_product"
    assert r["exact"]["const"] == "pi"
    assert r["exact"]["k_num"] == 1.0 and r["exact"]["k_den"] == 180.0
    for hr in spec["held_out"]:
        got = _eval_accepted(s, r, hr["inputs"])
        assert psy._row_cmp_ok(got, hr["expected"], hr.get("tol"), False) == 1.0


def test_742_tetrahedron_area_recovers_sqrt3(mbpp_tasks):
    s, r, spec = _run_mbpp_task(mbpp_tasks, 742, drop_own_exemplar=True)
    assert r["status"] == "accepted"
    assert r["rungs"]["exact"] == 1.0
    assert r["exact"]["family"] == "scaled_power_product"
    assert r["exact"]["const"] == "sqrt3"
    assert r["exact"]["k_num"] == 1.0 and r["exact"]["k_den"] == 1.0
    for hr in spec["held_out"]:
        got = _eval_accepted(s, r, hr["inputs"])
        assert psy._row_cmp_ok(got, hr["expected"], hr.get("tol"), False) == 1.0


# ---------------------------------------------------------------------------
# 4) 574 — sum_of_two_terms, WITH the honest corpus-artifact report.
# ---------------------------------------------------------------------------
def test_574_cylinder_surface_recovers_sum_of_two_terms(mbpp_tasks):
    s, r, spec = _run_mbpp_task(mbpp_tasks, 574)
    assert r["status"] == "accepted"
    assert r["rungs"]["exact"] == 1.0
    assert r["exact"]["family"] == "sum_of_two_terms"
    assert r["exact"]["const"] == "pi"
    assert r["exact"]["k_num"] == 2.0 and r["exact"]["k_den"] == 1.0
    assert r["exact"]["exps"] == [[1, 1], [2, 0]], r["exact"]["exps"]
    # the recovered structure IS correct — real math.pi, checked at a
    # relative tolerance matching the corpus's own math.isclose convention
    # (0.001) used elsewhere in this exact family.
    for hr in spec["held_out"]:
        got = _eval_accepted(s, r, hr["inputs"])
        assert psy._row_cmp_ok(got, hr["expected"], 0.001, False) == 1.0, \
            "the recovered 2*pi*r*(r+h) must be relatively-correct"
    # HONEST REPORT: this task's asserts are bare `==` compares against a
    # float literal computed by the REFERENCE solution's own hand-truncated
    # `3.1415` (PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md) — they carry
    # NO declared tolerance. The real battery's held-out comparator
    # (`agree()` in scripts/mbpp_arc3_battery.py / mbpp_endgame_battery.py)
    # therefore checks EXACT float equality for this task, which the
    # textbook-correct real-math.pi answer fails by ~0.01 absolute (a
    # corpus artifact, not a defect in the recovered shape) — reproduced
    # directly here, not hidden:
    for hr in spec["held_out"]:
        got = _eval_accepted(s, r, hr["inputs"])
        assert psy._row_cmp_ok(got, hr["expected"], None, False) == 0.0, (
            "574's held-out row is expected to FAIL exact equality against "
            "the corpus's own truncated-pi reference value — if this ever "
            "starts passing, the corpus fixture changed underneath us")


# ---------------------------------------------------------------------------
# 5) Occam order — codebook before exact, even when exact-eligible.
# ---------------------------------------------------------------------------
def _teach_float_decoy(s, name, triggers, term, args):
    s.add_node("ShapeSignature", {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
        "ground_template": json.dumps(
            {"desc": "float-eligible codebook decoy", "term": term,
            "args": list(args), "mode": "code_write"}),
    })


def test_codebook_covered_float_request_never_reaches_exact_rung():
    s, ag = boot()
    # a codebook construction that trigger-matches AND is textbook-correct
    # for this request (returns 2.0*a) — a float-typed, exact-eligible spec
    # that a codebook hit must still win outright, Occam order.
    _teach_float_decoy(s, "double_float_decoy", ["DOUBLEFLOAT"],
                       {"type": "Times", "items": [
                           {"type": "Lit", "value": 2.0},
                           {"type": "Var", "name": "a"}]},
                       ["a"])
    m = psy.ingest_spec(s, ag,
                        "write a function doublefloat_fn that returns the "
                        "doublefloat of a number",
                        [({"a": 3}, 6.0), ({"a": 5}, 10.0)])
    psy.pump(s, ag)
    goals = s.in_neighbours(m, "about_message")
    assert len(goals) == 1
    r = psy.read_goal(s, goals[0])
    assert r["status"] == "accepted"
    assert r["construction"] == "double_float_decoy"
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["exact"] is None, \
        "a codebook hit must pre-empt the exact rung entirely"
    assert r["exact"]["outcome"] is None


# ---------------------------------------------------------------------------
# 6) no in-frame floats — the frame/continuum invariant, enforced.
# ---------------------------------------------------------------------------
def _walk_ir(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk_ir(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk_ir(x)


def test_recovered_parameters_are_integers_only_the_named_constant_is_float():
    """k (numerator/denominator) and every exponent are Python `int`s in
    BOTH the recovered params dict AND the rendered IR's Lit nodes; the
    ONLY float Lit permitted anywhere in the tree is the named cross-frame
    constant's own value (pi/sqrt2/sqrt3) — never a fitted parameter."""
    s, ag = boot()
    fam = pex.family_from_substrate(s, "scaled_power_product")
    named_const_values = set(fam["constants"].values()) - {1.0}
    cases = [
        # (args, rows, expected const)
        (["a"], [{"inputs": {"a": 10}, "expected": 4188.790204786391, "tol": 0.001},
                 {"inputs": {"a": 25}, "expected": 65449.84694978735, "tol": 0.001}],
         "pi"),
        (["a"], [{"inputs": {"a": 3}, "expected": 15.588457268119894},
                 {"inputs": {"a": 20}, "expected": 692.8203230275509}],
         "sqrt3"),
    ]
    for args, row_dicts, expect_const in cases:
        rows = pex.interval_rows(row_dicts, args)
        params, _n = pex.fit_family(fam, rows)
        assert params is not None
        assert isinstance(params["k_num"], int) and isinstance(params["k_den"], int)
        assert all(isinstance(e, int) for e in params["exps"])
        assert params["const"] == expect_const
        ir = pex.render_family_to_ir(fam, params, args)
        for node in _walk_ir(ir):
            if node.get("type") != "Lit":
                continue
            v = node["value"]
            if isinstance(v, float):
                assert v in named_const_values, (
                    "a float Lit that is not a named cross-frame constant: %r" % (v,))
            elif isinstance(v, dict):
                # PROGRAM_SYNTHESIS_ARC5_RATIONAL.md: a non-integer `k`
                # renders as a single EXACT rational Lit (the
                # `{"__rational__": [n, d]}` wire tag `Value::Rational`
                # decodes from), not a `Div` of two int Lits any more —
                # STRICTLY stronger than the old "int Lit that computes
                # to a float via runtime Div" shape this gate accepted:
                # the fitted parameter never touches a float, literally,
                # anywhere in the tree now.
                assert set(v.keys()) == {"__rational__"}, ("non-rational dict Lit value: %r" % (v,))
                n, d = v["__rational__"]
                assert isinstance(n, int) and isinstance(d, int), (
                    "rational Lit numerator/denominator must be int: %r" % (v,))
            else:
                assert isinstance(v, int), ("non-int, non-float, non-rational Lit value: %r" % (v,))


# ---------------------------------------------------------------------------
# 7) the exact rung never intercepts the existing int-valued fixtures.
# ---------------------------------------------------------------------------
def test_int_valued_single_and_multi_row_fixtures_stay_ineligible():
    """The SAME fixture shapes used throughout the wider suite to exercise
    decoy/screen/isolation/repair mechanics (a lone `{"a": 5} -> 5` row, or
    a handful of small-int rows) must NEVER become exact-rung-eligible —
    an int-valued identity relation is trivially inside
    `scaled_power_product`'s own grid and would silently reroute those
    fixtures through this rung ahead of the rungs they exist to gate."""
    assert psy._examples_numeric_eligible([({"a": 5}, 5)]) is False
    assert psy._examples_numeric_eligible(
        [({"a": 5}, 2), ({"a": 3}, 8), ({"a": 7}, 1)]) is False
    assert psy._examples_numeric_eligible(
        [({"a": 2, "b": 9}, 9), ({"a": 7, "b": 3}, 7)]) is False       # MAX_ROWS-shaped
    assert psy._examples_numeric_eligible(
        [({"items": [1, 2, 3]}, 6)]) is False                          # list input
    assert psy._examples_numeric_eligible([]) is False                 # no examples
    assert psy._examples_numeric_eligible(
        [({"a": 1, "b": 2, "c": 3, "d": 4}, 10.0)]) is False           # arity 4 > schema max
    # float-typed IS eligible (the positive control).
    assert psy._examples_numeric_eligible(
        [({"a": 10}, 4188.790204786391), ({"a": 25}, 65449.84694978735)]) is True


def test_exact_eligibility_is_a_recorded_message_fact():
    s, ag = boot()
    m_int = psy.ingest_spec(s, ag, "write a function f that returns a", [({"a": 5}, 5)])
    assert s.node(m_int)["attrs"]["ps_exact_eligible"] == 0.0
    m_float = psy.ingest_spec(s, ag, "write a function g that returns a",
                              [({"a": 10}, 4188.790204786391)])
    assert s.node(m_float)["attrs"]["ps_exact_eligible"] == 1.0


# ---------------------------------------------------------------------------
# 8) NO-PYTHON-DECISION source audit — domains/prog_exact.py + the verb.
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count",
                   "covered", "vote", "logp")
_ALLOWED_SORT_KEYS = {"pair[0]"}


def _audit_source(src: str):
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, violations


def test_prog_exact_no_python_decisions():
    _audit_source(Path(pex.__file__).read_text())


def test_run_exact_family_verb_no_python_decisions():
    src = Path(psy.__file__).read_text()
    start = src.index("def run_exact_family(")
    end = src.index("\ndef ", start + 1)
    _audit_source(src[start:end])


# ---------------------------------------------------------------------------
# 9) the named arc-4 regression sweep — known drift only.
# ---------------------------------------------------------------------------
_REGRESSION_SWEEP_FILES = (
    "test_program_synthesis_migrated.py",
    "test_budget_isolation_migrated.py",
    "test_verdict_discrimination_migrated.py",
    "test_structural_verdicts_migrated.py",
    "test_prog_repair_migrated.py",
    "test_prog_descent_migrated.py",
    "test_descent_widening_migrated.py",
    "test_retrieval_migrated.py",
    "test_retrieval_ceiling_migrated.py",
    "test_search_reach_migrated.py",
    "test_screen_codebook_migrated.py",
    "test_prog_synthesis_battery_migrated.py",
    "test_arc4_endgame_migrated.py",
    "test_mbpp_arc3_endgame_migrated.py",
    "test_mbpp_endgame_migrated.py",
    "test_mbpp_baseline_migrated.py",
    "test_code_synthesis_baseline_migrated.py",
    "test_prog_ir_migrated.py",
    "test_value_domain_migrated.py",
)

# 2026-08-01 (arc5 cross-phase reconciliation — PROGRAM_SYNTHESIS_ARC5_
# FINAL.md): the six entries this allowlist used to carry (three literal
# `seed["version"]` string pins, three of `test_search_reach_migrated.py`'s
# frozen id-bucket assertions) have ALL been reconciled IN PLACE,
# attribution-aware, in their own files as later phases landed (seed now
# v1.10.0/70 rules post arc5-moves; the search-reach bucket now also holds
# out arc5-moves' own `_ARC5_MOVES_PASS_IDS`/`_ARC5_MOVES_ACCEPTED_
# HOLDOUT_FAIL_IDS`) — never blanket-loosened. Pruned per this test's own
# "prune the allowlist" instruction now that they no longer fail. What
# remains is the ONE class outside every phase's file-ownership boundary:
# a PRE-EXISTING defect (task 267's 'sum_of_two' vs 'range_sum_spine'
# construction drift), verified directly (an isolated worktree at commit
# ec41d3001c — this rung's own starting commit — with domains/prog_
# synthesis.py, seeds/program_synthesis.json and the affected test files
# ALL at that commit) to already fail there, predating exact-first itself.
_KNOWN_OUT_OF_SCOPE_FAILURES = frozenset({
    "test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct",
    "test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live",
})
# 2026-08-01 (arc6 seam D, reconciled): this allowlist is UNCHANGED, and
# that is the point. Seam D's property rung + seed bump (v1.10.0/70 ->
# v1.11.0/73) broke 8 node ids inside this sweep's own file set (seed
# version/count pins in test_program_synthesis / test_budget_isolation /
# test_verdict_discrimination / test_retrieval, plus test_retrieval's
# ceiling[105/238/405] and occam-order behavioural pins). Every one was
# reconciled IN PLACE in its own file, attribution-aware and with a
# constructed witness where the verdict changed — so none of them was
# allowlisted here, and this sweep went green again on its own. The two
# entries that remain are the pre-existing task-267 construction drift the
# arc5 reconciliation verified at ec41d3001c and deliberately left red.


def test_named_regression_sweep_only_known_pins_drift():
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    tests_dir = os.path.join(ROOT, "tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         *[os.path.join(tests_dir, f) for f in _REGRESSION_SWEEP_FILES],
         "--confcutdir=.", "-q", "--tb=no", "-rf"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=280)
    failed = set()
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED "):
            node_id = line[len("FAILED "):].split(" ")[0]
            # normalise "tests/test_x.py::y" -> "test_x.py::y"
            failed.add(node_id.split("tests" + os.sep, 1)[-1].lstrip(os.sep))
    unexpected = failed - _KNOWN_OUT_OF_SCOPE_FAILURES
    assert not unexpected, (
        "unexpected new regressions in the arc-4 sweep:\n%s\n\nfull output:\n%s"
        % ("\n".join(sorted(unexpected)), proc.stdout[-4000:]))
    missing_known = _KNOWN_OUT_OF_SCOPE_FAILURES - failed
    if missing_known:
        # a "known" failure stopped failing — good news, not a gate: print
        # it so the allowlist above can be pruned, never silently swallow it.
        print("\nKNOWN out-of-scope failures no longer failing (prune the "
              "allowlist): %s" % sorted(missing_known))
