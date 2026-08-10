"""Gate for COLOUR IDENTITY'S REFUSAL BOUND — the packing radius of the minted
codebook (VISION_COLOUR_BOUND_PREREG.md / VISION_COLOUR_BOUND_RESULTS.md).

L1b (VISION_UNIQUENESS_RESULTS.md) found `ci_assign` to be the worst case in its
audit: an `Argmin` over `ColourCategory` with ZERO `Lte` — no admission bound at all,
so a probe at opponent distance 269.52 was confidently assigned and the equidistant
probe was decided by a margin of exactly 0.0000. This gate pins the fix.

THE CONJUNCTION IS THE GATE (process rule 5). A build that refuses EVERYTHING scores
a PERFECT FLOOR on arms B, D and F. It is caught ONLY by `test_C_no_regression_*`
and `test_E_boundary_is_exact_*`. Both are positive-controlled in the results file
against three independently injected defects.
"""
from __future__ import annotations

import ast
import json
import math
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_SHA = "afc195b9"          # base `main` HEAD this rung branched from (§11)
RUNG_SHA = "41a3158c"          # this rung's own commit — the diff BASE_SHA..RUNG_SHA is
                               # immutable, so the provenance claims below stay true
                               # regardless of what merges on top afterwards (§12.3)

from scripts.colour_bound_measure import (  # noqa: E402
    arm_A, arm_B, arm_C, arm_D, arm_E, arm_F, arm_X, delta_on,
    _packing_admits, _packing_radius, FAR_PROBE, EQUI_PROBE, OFF_PROTO_PROBE,
)
from domains import colour_bound_world as cbw  # noqa: E402


# --- the arms -----------------------------------------------------------------
def test_A_the_defect_reproduces_with_the_flag_off():
    """The PREMISE: without the bound, a probe 269.52 away is confidently assigned
    and the equidistant probe is decided by a margin of exactly 0.0000."""
    a = arm_A()
    assert a["PASS"], a
    far = a["probes"]["far"]
    assert far["assigned"] == 1 and far["refused"] == 0
    assert far["sign_dist"] == pytest.approx(269.5199, abs=1e-3)
    equi = a["probes"]["equidistant"]
    assert equi["assigned"] == 1
    assert equi["margin"] == 0.0            # L1b's exact-zero margin, pinned
    assert equi["sign_dist"] == pytest.approx(10.0)


def test_B_the_bound_refuses_the_far_probe():
    b = arm_B()
    assert b["PASS"], b
    assert b["far_probe"]["ci_refused"] == 1.0
    assert b["far_probe"]["sign_dist"] == -1.0          # never assigned
    assert b["far_probe"]["ci_refused_dist"] == pytest.approx(269.5199, abs=1e-3)
    # The bound is 7.8102 on this codebook — DERIVED from it, never written down.
    assert set(b["packing_radius"].values()) == {7.8102}


def test_C_no_regression_every_landed_assignment_survives():
    """THE CONJUNCTION (§1.1 / process rule 5). A refuse-everything build FAILS HERE."""
    c = arm_C()
    assert c["PASS"], c
    assert c["a_field"]["n_assigned"] == 36 and c["a_field"]["n_refused"] == 0
    assert c["c_recognize_not_remint"]["n_cats_before"] == 3
    assert c["c_recognize_not_remint"]["n_cats_after"] == 3


def test_C_the_discriminating_probe_at_distance_4_is_STILL_assigned():
    """Colour identity's OWN landed arm A(b): the off-prototype colour at (6,0) is
    assigned to (10,0) at distance 4. The bound is 7.8102, so this probe sits 3.81
    INSIDE the region where a tighter bound would refuse it.

    THIS IS THE ARM THAT CAN FAIL. The exact-cluster-extent bound (0), the
    lattice-step bound (1.0), the `Times` a/b-form trap (empty product = 1.0) and a
    refuse-everything build ALL turn this test RED. It is the reason the fix is a
    fix and not a lobotomy."""
    b = arm_C()["b_off_prototype"]
    assert b["crg"] == 6.0 and b["cby"] == 0.0
    assert b["ci_refused"] == 0.0
    assert b["sign_dist"] == pytest.approx(4.0)
    assert (b["sign_rg"], b["sign_by"]) == (10.0, 0.0)
    assert set(b["packing_radius"].values()) == {7.8102}
    assert 4.0 < 7.8102                      # the margin that makes this arm risked


def test_D_the_zero_margin_ambiguity_is_refused_tie_independently():
    """L1b's 0.0000-margin probe. It is refused by the SAME bound — no tie rule, no
    special case — and the refusal does not depend on which way the Argmin tie fell,
    because BOTH tied candidates lie outside their packing balls."""
    d = arm_D()
    assert d["PASS"], d
    assert d["probe"]["ci_refused"] == 1.0
    assert d["margin"] == 0.0 and d["n_tied"] == 2
    assert d["winner_dist"] == pytest.approx(10.0)
    assert d["tie_independent"] is True


def test_E_the_graph_decision_IS_the_derived_packing_predicate():
    """n=100, seeds 50000-50099. The seed's admit/refuse decision agrees POINTWISE
    with the independently re-derived packing-radius predicate — 0 disagreements —
    and the sample is non-degenerate in BOTH directions, so neither a
    refuse-everything nor an admit-everything build can pass."""
    e = arm_E()
    assert e["PASS"], e
    assert e["n"] == 100 and e["disagreements"] == 0
    assert e["n_admitted"] >= 1 and e["n_refused"] >= 1
    assert e["seeds"] == [50000, 50099]


def test_F_noise_floor_mints_and_signs_nothing():
    f = arm_F()
    assert f["PASS"], f
    assert f["fields_minting"] == 0 and f["fields_with_signs"] == 0
    assert f["seeds"] == [50100, 50199]


def test_X_offday_the_flag_at_ZERO_is_inert():
    """§9. With the flag at 0 the bound clause is a vacuously-true disjunct and
    `ci_refuse` can never fire — the far probe is assigned exactly as before.

    NOTE: this arm writes `bound=0.0` EXPLICITLY (via `arm_X`), so it is unchanged in
    behaviour by the k=1 rung's default flip. Its title and docstring formerly said
    "OFF by default"; as of `vision_colour_identity` v1.3.0 the default is ARMED, so
    that sentence was false and was corrected. What the test checks — flag at 0 ⇒
    inert — is untouched. See VISION_COLOUR_BOUND_K1_PREREG.md §6 item 3."""
    x = arm_X()
    assert x["PASS"], x
    assert x["max_ci_refused"] == 0.0
    assert x["far_probe"]["ci_refused"] == 0.0
    assert x["far_probe"]["ci_refused_dist"] == -1.0
    assert x["far_probe"]["sign_dist"] > 0.0


def test_the_flag_now_ships_ARMED_with_its_caveat_recorded():
    """RETARGETED BY THE k=1 RUNG — the deliberate default flip (§9 "changed,
    measured and enumerated", VISION_COLOUR_BOUND_K1_PREREG.md §6 item 2).

    This test previously asserted `bound == 0.0` / version 1.2.0. The k=1 rung
    measured DELTA-ON-FLIPPED EMPTY across all five landed scenes and the k=1 regime
    byte-identical ON vs OFF, and flipped the default under a decision rule fixed in
    advance. The other two flags are UNCHANGED and still ship OFF.

    The caveat is asserted, not merely written: arming the bound guarantees refusal
    for k >= 2 ONLY, and the seed must say so in its own description."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    attrs = seed["nodes"][0]["attrs"]
    assert attrs["bound"] == 1.0
    assert attrs["identity"] == 0.0 and attrs["achromatopsia"] == 0.0
    assert seed["version"] == "1.3.0"
    # the k=1 caveat is RECORDED in the seed, not implied away
    desc = seed["description"]
    assert "k>=2 ONLY" in desc
    assert "single-quantum codebook still admits" in desc.lower()


# --- the §9 delta measurement --------------------------------------------------
def test_DELTA_ON_changes_NOTHING_in_the_landed_rungs():
    """The measurement the rung exists to report: with the bound ARMED, not one
    number moves in colour identity's or achromatopsia's landed scenes. Every landed
    assignment sits at distance 0 or 4 against bounds of 7.8102 / 10.0 / undefined."""
    d = delta_on()
    assert d["n_changed_fields_across_landed_scenes"] == 0, d
    for name, sc in d["scenes"].items():
        assert sc["changed"] == {}, (name, sc["changed"])


def test_the_k1_hole_is_REAL_and_is_reported_not_hidden():
    """HONEST RESIDUAL (§8): at k=1 the packing radius is UNDEFINED, so the bound is
    vacuous and ci_assign still cannot refuse. This is pinned as a FACT of the build,
    not smoothed over — two of achromatopsia's landed scenes are exactly this case,
    which is WHY they are unchanged."""
    d = delta_on()
    k1 = {n: sc for n, sc in d["scenes"].items() if sc["k"] == 1}
    assert k1, "expected at least one k=1 landed scene"
    for name, sc in k1.items():
        assert set(sc["packing_radius"].values()) == {None}, (name, sc)
    # and the predicate itself admits everything at k=1, however far away
    assert _packing_admits((10_000.0, -10_000.0), [(0, 0)]) is True


# --- composition / no-new-Rust / adapter purity --------------------------------
def _rung_diff_names():
    """Every path this rung touches, pinned to THIS RUNG'S OWN IMMUTABLE COMMIT RANGE
    (§12.3).

    Originally this diffed BASE_SHA against the WORKING TREE and also scanned every
    untracked file repo-wide. That was correct only while the rung sat alone on its own
    branch: once any later rung merged, the base->worktree diff legitimately contained
    that rung's files too, and the repo-wide untracked scan swept up `var/pytest_tmp/**`
    temp artifacts (including stray `*.rs` from other tests' scratch dirs). Both produced
    FALSE failures about THIS rung's provenance.

    The provenance claims themselves are unchanged — no Rust, exactly one committed seed,
    no other rung's files. They are simply measured against `BASE_SHA..RUNG_SHA`, which is
    immutable and cannot be polluted by later merges or by a dirty tree."""
    out = subprocess.run(["git", "diff", "--name-only", BASE_SHA, RUNG_SHA],
                         cwd=HERE, capture_output=True, text=True).stdout
    return sorted({ln for ln in out.splitlines() if ln.strip()})


def test_this_rung_adds_NO_Rust():
    """§12.3: pinned to THIS RUNG'S OWN DIFF, not to a mutable tree."""
    changed = _rung_diff_names()
    assert changed, "expected a non-empty rung diff"
    rs = [f for f in changed if f.endswith(".rs")]
    assert rs == [], f"this rung claims NO new Rust but touched: {rs}"


def test_this_rung_edits_exactly_ONE_committed_seed():
    changed = [f for f in _rung_diff_names() if "/seeds/" in f]
    assert changed == ["research/experiments/gamma-substrate/seeds/"
                       "vision_colour_identity.json"], changed


def test_this_rung_touches_no_other_rungs_files():
    """§11 rule 4 — own your files. Nothing outside this rung's own artifacts plus
    the ONE seed + builder it is chartered to fix."""
    owned = {
        "VISION_COLOUR_BOUND_PREREG.md", "VISION_COLOUR_BOUND_RESULTS.md",
        "seeds/vision_colour_identity.json",
        "tools/build_vision_colour_identity.py",
        "domains/colour_bound_world.py", "scripts/colour_bound_measure.py",
        "tests/test_colour_bound_migrated.py",
        "results/colour_bound_measure.json",
        "VISION_PROTOCOL.md",               # ledger append only
        # The k=1 rung (VISION_COLOUR_BOUND_K1_PREREG.md §6 item 4) lands on top of
        # this one and its diff is computed against the SAME base `afc195b9`, so this
        # set now legitimately spans both rungs. The NO-Rust and one-seed assertions
        # above are UNCHANGED and still green: the k=1 rung adds no Rust and edits the
        # same single seed.
        "VISION_COLOUR_BOUND_K1_PREREG.md", "VISION_COLOUR_BOUND_K1_RESULTS.md",
        "scripts/colour_bound_k1_measure.py",
        "tests/test_colour_bound_k1_migrated.py",
        "results/colour_bound_k1_measure.json",
        "scripts/uniqueness_measure.py",    # §6 item 5 — the L1b defect-record pin
    }
    prefix = "research/experiments/gamma-substrate/"
    stray = [f for f in _rung_diff_names()
             if f.startswith(prefix) and f[len(prefix):] not in owned]
    assert stray == [], stray


def test_the_bound_introduces_no_tuned_constant():
    """§13. The seed's whole literal set stays definitional: the flag comparisons
    (0.5), the done-markers (1.0/0.0), the MDL member count (3) — and the ONE literal
    this rung adds, `2`, which is the non-overlap factor of `2r <= D`, i.e. the
    DEFINITION of a packing radius, not a threshold.

    The bound VALUE (7.8102, 10.0, undefined) appears NOWHERE in the seed: it is
    computed from the codebook, which is what makes it fall out rather than go in."""
    text = open(os.path.join(HERE, "seeds",
                             "vision_colour_identity.json")).read()
    seed = json.loads(text)
    lits = set()

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit":
                lits.add(float(o["value"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(seed["rules"])
    assert lits == {0.0, 0.5, 1.0, 2.0, 3.0}, sorted(lits)

    # And the derived bound VALUES appear in no EXECUTABLE term — only, at most, in
    # the rules' `comment` prose, where documenting the derivation is the point. The
    # scan is over the term trees with comments stripped, so prose cannot mask a
    # hard-coded threshold and a hard-coded threshold cannot hide in prose.
    exec_only = json.dumps([{k: v for k, v in r.items() if k != "comment"}
                            for r in seed["rules"]])
    for forbidden in ("7.81", "15.62", "269.5", "10.0"):
        assert forbidden not in exec_only, forbidden


def test_the_bound_composes_from_HELD_terms_only():
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    refuse = [r for r in seed["rules"] if r["name"] == "ci_refuse"]
    assert len(refuse) == 1
    types = set()

    def walk(o):
        if isinstance(o, dict):
            if "type" in o and isinstance(o["type"], str):
                types.add(o["type"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(refuse[0])
    held = {"Var", "Lit", "Attr", "Gt", "Lt", "Eq", "Not", "And", "Or", "Plus",
            "Minus", "Times", "Sqrt", "NodesOfType", "Filter", "Count", "Exists",
            "Argmin", "PickUnique"}
    assert types <= held, types - held


def test_the_bound_is_absence_tolerant_and_never_PickUnique_on_the_codebook():
    """Process rule 3. The k=1 case is handled by `Not(Exists ...)` over the
    codebook-complement — absence-tolerant BY CONSTRUCTION — and `PickUnique` is used
    ONLY for the params node, never to select a category."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    for rule in seed["rules"]:
        stack = [rule]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                if o.get("type") == "PickUnique":
                    src = o.get("source", {})
                    assert src.get("node_type") == "ColourIdentityParams", o
                stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(o)


def test_ci_refuse_never_writes_a_sign_attribute():
    """L1b's load-bearing lesson: the refusal writes ONLY new attributes. Clearing an
    assignment would let `ci_assign` re-fire and flip the attribute forever, and
    `run_rules` terminates on exact value equality — that build would not terminate."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    refuse = [r for r in seed["rules"] if r["name"] == "ci_refuse"][0]
    written = {e[2] for e in refuse["effects"] if e[0] == "set_attr"}
    assert written == {"ci_refused", "ci_refused_dist", "assigned_epoch"}
    assert not ({"sign_rg", "sign_by", "sign_dist"} & written)


def test_no_python_decision_in_the_adapter():
    """CLAUDE.md / §0, AST-scanned (not a substring scan — the substring version of
    this test was once caught by its own type annotation)."""
    src = open(os.path.join(HERE, "domains", "colour_bound_world.py")).read()
    tree = ast.parse(src)
    bad = [n for n in ast.walk(tree)
           if isinstance(n, (ast.If, ast.IfExp, ast.Compare, ast.BoolOp))]
    assert bad == [], [type(n).__name__ for n in bad]


def test_the_landed_gates_are_untouched_at_the_default():
    """§9 byte-identity, run in THIS process against the edited seed."""
    r = subprocess.run(
        ["python3", "-m", "pytest", "-q",
         os.path.join(HERE, "tests", "test_colour_identity_migrated.py"),
         os.path.join(HERE, "tests", "test_achromatopsia_migrated.py"),
         os.path.join(HERE, "tests", "test_colour_salience_migrated.py")],
        cwd=HERE, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-3000:]
    assert "17 passed" in r.stdout, r.stdout[-2000:]
