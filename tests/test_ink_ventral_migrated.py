"""GATE for the INK × VENTRAL rung — does the ventral machinery retroactively improve the
handwriting arc?

Pre-registration `VISION_INK_VENTRAL_PREREG.md` (committed BEFORE the run at 91793bcf, §3);
results `VISION_INK_VENTRAL_RESULTS.md`; pinned raw `results/ink_ventral_measure.json`.

THIS RUNG'S RESULT IS A DIAGNOSED NEGATIVE, AND THAT SHAPES THE GATE. A gate over a negative
has a specific failure mode: **it passes on a build where nothing works at all** (§1.1 — a dead
arm scores a perfect floor, confirmed repeatedly in this arc). So the CONJUNCTION is the gate:

  * the INSTRUMENT must be ALIVE and EXACT (G0a's six synthetic cases, and the §13
    resolution-derivation invariances) — a broken `EnclosedCount` would "explain" the null;
  * the CONTROLS must REPRODUCE their standing numbers (A0 vs RUN 15, A1 vs RUN 16) — a null
    measured on a broken harness is worth nothing;
  * and only THEN are the negative verdicts pinned at their MEASURED values.

Every headline number is pinned at its measured value, never at its pre-registered inequality.
"""
from __future__ import annotations

import ast
import json
import math
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results", "ink_ventral_measure.json")
RUNNER = os.path.join(HERE, "scripts", "ink_ventral_measure.py")
RUST = os.path.join(HERE, "runners", "dsl", "src", "ink_topology.rs")
PROVENANCE = os.path.join(HERE, "results", "ink_ventral_provenance.json")

# The base this rung was cut from (§11). BOTH ENDPOINTS OF THE PROVENANCE DIFF ARE FIXED: this
# constant and the rung's OWN commit recorded in the pin file. NEVER base->working-tree, NEVER
# base->HEAD — HEAD moves the moment anything merges, and that exact defect has bitten three
# rungs in this arc.
BASE_SHA = "328065b62a31cf1daeb601557f21a0d331a2aed2"

TOL = 1e-9


@pytest.fixture(scope="module")
def res():
    with open(RESULTS) as f:
        return json.load(f)


def _native():
    import sys
    for p in (HERE, os.path.join(HERE, "runners", "dsl", "python")):
        if p not in sys.path:
            sys.path.insert(0, p)
    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    return s._inner


def _ec(native, strokes):
    return native.evaluate(
        {"type": "EnclosedCount", "arg": {"type": "Lit", "value": strokes}}, {})


def _circle(cx, cy, r, n, frac=1.0):
    return [[cx + r * math.cos(frac * 2 * math.pi * i / n),
             cy + r * math.sin(frac * 2 * math.pi * i / n)] for i in range(n + 1)]


# ---------------------------------------------------------------------------
# THE INSTRUMENT MUST BE ALIVE AND EXACT — without this, the null is unearned.
# ---------------------------------------------------------------------------
def test_G0a_the_six_synthetic_controls_are_EXACT():
    """§1: gate the measure before the agent, in BOTH directions. A hole-counter that returns 0
    everywhere would pass a positive-only check AND would fully 'explain' this rung's null."""
    native = _native()
    cases = [
        ([_circle(0, 0, 10, 120)], 1),
        ([_circle(0, 0, 10, 120, 0.75)], 0),
        ([[[10 * math.sin(2 * t), 10 * math.sin(t)]
           for t in [2 * math.pi * i / 200 for i in range(201)]]], 2),
        ([_circle(0, 0, 10, 120), _circle(0, 0, 4, 60)], 2),
        ([[[0, 0], [10, 0], [20, 0]]], 0),
        ([[[0, 0], [1, 0]], [[9, 4], [10, 4]], [[3, 9], [4, 9]]], 0),
    ]
    for strokes, want in cases:
        got = int(round(float(_ec(native, strokes)["holes"])))
        assert got == want, f"EnclosedCount returned {got}, want {want}"


def test_G0a_result_is_pinned_as_PASS(res):
    assert res["g0a"]["pass"] is True
    assert len(res["g0a"]["rows"]) == 6
    assert all(r["ok"] for r in res["g0a"]["rows"])


def test_the_resolution_is_SAMPLING_DERIVED_not_chosen():
    """THE §13 CLAIM, IN CODE. The raster resolution is the ink's own mean inter-sample arc
    step, so the SAME shape sampled at three densities and at three scales must give the SAME
    topology. If a grid size had been hand-picked, these would diverge."""
    native = _native()
    for n in (40, 120, 400):
        assert int(round(float(_ec(native, [_circle(0, 0, 10, n)])["holes"]))) == 1
    for r in (1.0, 10.0, 1000.0):
        assert int(round(float(_ec(native, [_circle(0, 0, r, 120)])["holes"]))) == 1


def test_degenerate_ink_is_an_HONEST_ZERO_not_a_crash_and_not_a_guess():
    native = _native()
    d = _ec(native, [])
    assert float(d["holes"]) == 0.0 and float(d["grid_w"]) == 0.0
    assert float(_ec(native, [[[1.0, 1.0]]])["holes"]) == 0.0


def test_the_clamp_guard_NEVER_BOUND_on_the_confirmatory_set(res):
    """The one memory guard in `ink_topology.rs` is a declared non-derivation. If it ever binds,
    the §13 resolution claim is lost for those figures — so the rung must show it did not."""
    assert res["g0bc"]["clamp_hits"] == 0
    assert res["diagnostics"]["query_clamp_hits"] == 0


# ---------------------------------------------------------------------------
# THE CONTROLS MUST REPRODUCE — a null on a broken harness is worth nothing.
# ---------------------------------------------------------------------------
def test_the_protocol_is_the_pre_registered_one(res):
    p = res["protocol"]
    assert p["way"] == 20 and p["r"] == 2 and p["episodes_per_alphabet"] == 20
    assert p["n"] == 400, "n was FIXED IN ADVANCE at 400 (§3.3)"
    assert p["split"] == "evaluation"
    assert p["alphabets"] == ["Angelic", "Atemayar_Qelisayer", "Atlantean", "Aurek-Besh",
                              "Avesta", "Ge_ez", "Glagolitic", "Gurmukhi", "Kannada", "Keble"]
    assert res["seeds"] == {"powered": 54000, "g0b_null": 54001, "shuffled_labels": 54002}


def test_CONTROL_A0_reproduces_RUN15s_earned_quanta_ceiling(res):
    """A0 is byte-identical machinery to RUN 15/16's `adopted` arm. Its CI must overlap
    26.8% [22.6, 31.3]."""
    assert res["controls_reproduced"]["a0_vs_run15"] is True
    lo, hi = res["arms"]["a0"]["ci"]
    assert lo <= 0.313 and hi >= 0.226


def test_CONTROL_A1_reproduces_RUN16s_SCTPS_full_dwell(res):
    """A1 is byte-identical machinery to RUN 16's SC+TPS FULL DWELL. Its CI must overlap
    73.5% [67.0, 79.1]."""
    assert res["controls_reproduced"]["a1_vs_run16"] is True
    lo, hi = res["arms"]["a1"]["ci"]
    assert lo <= 0.791 and hi >= 0.670


def test_every_arm_is_ALIVE_above_its_own_shuffled_control(res):
    """§1 clause 4: the arms must be alive. Each arm's real accuracy must beat its own
    shuffled-label control, which breaks the query<->exemplar correspondence."""
    for k in ("a0", "a1", "a2", "a3", "a4"):
        a = res["arms"][k]
        assert a["acc"] > a["acc_shuffled"], f"arm {k} is not above its shuffled control"
        assert a["n"] == 400


# ---------------------------------------------------------------------------
# THE MEASURED VERDICTS, PINNED AT VALUE.
# ---------------------------------------------------------------------------
def test_H1_verdict_is_pinned(res):
    assert res["h1_verdict"].startswith(PINS["h1_prefix"])
    assert abs(res["arms"]["a3"]["acc"] - PINS["a3"]) < TOL


def test_H2_verdict_is_pinned(res):
    assert res["h2_verdict"] == PINS["h2"]
    assert abs(res["h2"]["acc"] - PINS["h2_acc"]) < TOL


def test_H3_verdict_is_pinned(res):
    assert res["h3_verdict"].startswith(PINS["h3_prefix"])
    assert abs(res["arms"]["a4"]["acc"] - PINS["a4"]) < TOL


def test_the_overall_verdict_is_pinned(res):
    assert res["overall"] == PINS["overall"]


def test_G0b_and_G0c_are_pinned(res):
    g = res["g0bc"]
    assert g["g0b_pass"] is PINS["g0b_pass"]
    assert g["g0c_refutes_at_premise"] is PINS["g0c_refutes"]
    assert abs(g["modal_agreement"] - PINS["g0b_obs"]) < TOL
    assert abs(g["null_modal_agreement"] - PINS["g0b_null"]) < TOL
    assert abs(g["f0"] - PINS["g0c_f0"]) < TOL


def test_the_diagnosis_is_RECORDED_not_merely_asserted(res):
    """§7: a negative that is diagnosed is worth more than a positive that is not understood.
    The diagnostic fields that identify WHICH failure mode this is must be present and
    non-degenerate — a null with an empty diagnostic block is the shrug this rule forbids."""
    g = res["g0bc"]
    for k in ("diag_total_holes", "diag_one_cell_holes", "diag_one_cell_fraction",
              "diag_largest_hole_area_fraction_median", "mean_holes_per_drawing"):
        assert k in g
    assert g["diag_total_holes"] > 0, "no holes at all would be a DIFFERENT diagnosis"
    d = res["diagnostics"]
    for k in ("a3_gate_changed", "a3_mean_admitted", "a2_mean_ties", "coverage_shortlist"):
        assert k in d


# ---------------------------------------------------------------------------
# ARCHITECTURE + §9 + §10.
# ---------------------------------------------------------------------------
_DECISION_CALLS = {"min", "max", "sorted", "argmin", "argmax"}


def test_the_runner_makes_NO_python_decision_on_any_verdict_path():
    """donkey=0, checked STRUCTURALLY (AST, not grep — the tripwire rung's own lesson that a
    substring audit is evadable). Every winner in `_episode` must come from a held Term
    evaluate. The ONLY tolerated bare `min` is the one computing the DIAGNOSTIC tie count,
    which is explicitly not a decision — and it is admitted BY NAME, not by pattern."""
    with open(RUNNER) as f:
        tree = ast.parse(f.read())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_episode")
    offenders = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _DECISION_CALLS:
                offenders.append((node.func.id, node.lineno))
    # the single admitted exception: `best = min(sc for sc, _ in pairs_t)` feeds `n_topo_ties`,
    # a REPORTED diagnostic; the A2 winner itself is the held Argmin two lines below it.
    assert len(offenders) <= 1, f"Python decisions on the verdict path: {offenders}"
    if offenders:
        assert offenders[0][0] == "min"


def test_the_new_Rust_primitive_DECIDES_NOTHING():
    """The architecture rule: a primitive in Rust computes a fact; it must not branch on graph
    state or embed a verdict. `ink_topology.rs` must contain no threshold comparison that
    classifies its own output."""
    # CODE ONLY — comments are prose and may legitimately name the Term that dispatches to this
    # module. Auditing the raw text would flag the module's own doc-comment, which is precisely
    # the substring-audit disease the tripwire rung diagnosed.
    code = "\n".join(ln for ln in open(RUST).read().splitlines()
                     if not ln.lstrip().startswith(("//", "//!", "///")))
    for forbidden in ("TermNode", "Substrate", "NodeID", "evaluate("):
        assert forbidden not in code, (
            f"a primitive must not reach into the graph/Term layer, found {forbidden!r}")
    # the module's only constant is the declared memory guard
    consts = [ln for ln in code.splitlines() if ln.strip().startswith("const ")]
    assert len(consts) == 1 and "MAX_SIDE" in consts[0], f"unexpected constants: {consts}"


def test_EnclosedCount_is_constructed_by_NO_seed():
    """§9 by construction: the new Term is purely additive. If no seed builds it, no committed
    result can move because of it."""
    seeds_dir = os.path.join(HERE, "seeds")
    hits = []
    for name in os.listdir(seeds_dir):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(seeds_dir, name)) as f:
            if "EnclosedCount" in f.read():
                hits.append(name)
    assert hits == [], f"EnclosedCount leaked into seed data: {hits}"


def test_the_sd_orbit_law_is_UNMOVED():
    """The standing regression oracle for this whole tree — re-asserted here because this rung
    ADDS RUST, so it is the first vision rung in a while that could actually move it."""
    import sys
    for p in (HERE, os.path.join(HERE, "runners", "dsl", "python"),
              os.path.join(HERE, "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    from sdloop_vision_measure import predicted_orbits
    for N, expected in ((2, 1), (3, 2), (4, 2), (6, 2), (12, 4)):
        ths = [i * 180.0 / N for i in range(N)]
        assert predicted_orbits(ths) == expected, f"orbit law moved at N={N}"


# ---------------------------------------------------------------------------
# PROVENANCE — BOTH ENDPOINTS FIXED.
# ---------------------------------------------------------------------------
def _git(*args):
    return subprocess.run(["git", "-C", HERE, *args], check=True, capture_output=True,
                          text=True).stdout


@pytest.fixture(scope="module")
def pin():
    assert os.path.exists(PROVENANCE), (
        "the provenance pin file is MISSING — the §10 claim cannot be made against a "
        "mutable tree")
    with open(PROVENANCE) as f:
        return json.load(f)


def test_the_provenance_pin_is_well_formed_and_REACHABLE(pin):
    assert pin["base_sha"] == BASE_SHA
    rung = pin["rung_commit_sha"]
    assert len(rung) == 40
    subprocess.run(["git", "-C", HERE, "merge-base", "--is-ancestor", rung, "HEAD"], check=True)
    subprocess.run(["git", "-C", HERE, "merge-base", "--is-ancestor", BASE_SHA, "HEAD"],
                   check=True)


def test_this_rung_ADDS_RUST_and_says_so(pin):
    """Unlike most rungs in this arc, this one DOES add Rust — so §10.1 rule 4 bites: the engine
    must have been built in THIS worktree. The diff is BASE_SHA..<this rung's own commit>, BOTH
    ENDPOINTS FIXED, TRACKED FILES ONLY."""
    rng = f"{BASE_SHA}..{pin['rung_commit_sha']}"
    changed = _git("diff", "--name-only", rng, "--").splitlines()
    rust = sorted(p for p in changed if p.endswith(".rs"))
    assert rust, "this rung claims to add Rust but the pinned diff has none"
    expected = {"runners/dsl/src/ink_topology.rs", "runners/dsl/src/jsonio.rs",
                "runners/dsl/src/lib.rs", "runners/dsl/src/reflect.rs",
                "runners/dsl/src/shape.rs", "runners/dsl/src/term.rs"}
    got = {p.split("gamma-substrate/")[-1] for p in rust}
    assert got == expected, f"unexpected Rust surface: {got ^ expected}"
    assert pin["engine_verdict"] == "own", (
        "§10.1 rule 4: a rung that touches .rs MUST build its own engine — a shared build "
        f"would be attributing numbers to source that did not produce them (got "
        f"{pin['engine_verdict']!r})")


def test_the_RUST_DIFF_IS_PURELY_ADDITIVE(pin):
    """§9's strongest available form for a rung that ADDS RUST. A new Term variant can only
    move a committed result if it CHANGED an existing code path — so show that it did not.
    The whole engine diff must be insertions, except for the two `shape.rs` match arms that
    were rewritten solely to append the new variant. Both endpoints fixed."""
    rng = f"{BASE_SHA}..{pin['rung_commit_sha']}"
    diff = _git("diff", rng, "--", "*.rs")
    deletions = [ln for ln in diff.splitlines()
                 if ln.startswith("-") and not ln.startswith("---")]
    assert len(deletions) == 2, f"expected exactly 2 rewritten lines, got {len(deletions)}:\n{deletions}"
    # both are `shape.rs` match arms, and each has an `+` twin that is the SAME line with the
    # new variant appended — i.e. nothing pre-existing was removed from either.
    additions = [ln[1:] for ln in diff.splitlines()
                 if ln.startswith("+") and not ln.startswith("+++")]
    for d in deletions:
        old = d[1:]
        twin = [a for a in additions if a.startswith(old.rstrip()[:40])]
        assert twin, f"a deleted line has no additive twin — this is NOT purely additive: {old!r}"
        assert any("EnclosedCount" in t for t in twin), (
            f"the rewritten line does not merely append EnclosedCount: {twin!r}")


def test_this_rung_edits_NO_earlier_rungs_seed_or_measurement(pin):
    """§11 rule 4. The handwriting arc's own scripts and every committed seed must be
    byte-unchanged: this rung ADDS a runner, it does not rewrite the arc."""
    _OWN_SCRIPTS = {"scripts/ink_ventral_measure.py", "scripts/ink_ventral_pin.py"}
    rng = f"{BASE_SHA}..{pin['rung_commit_sha']}"
    changed = [p.split("gamma-substrate/")[-1]
               for p in _git("diff", "--name-only", rng, "--").splitlines()]
    forbidden = [p for p in changed
                 if p.startswith("seeds/")
                 or (p.startswith("scripts/") and p not in _OWN_SCRIPTS)
                 or p.startswith("domains/")]
    assert forbidden == [], f"this rung touched files it does not own: {forbidden}"


# ---------------------------------------------------------------------------
# THE MEASURED PINS. Filled from results/ink_ventral_measure.json AFTER the run.
# ---------------------------------------------------------------------------
PINS = json.load(open(os.path.join(HERE, "results", "ink_ventral_pins.json"))) \
    if os.path.exists(os.path.join(HERE, "results", "ink_ventral_pins.json")) else {}
