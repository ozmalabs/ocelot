"""test_arc_decompose_migrated — MG4: ORDER-N DECOMPOSITION.

Prereg:  `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A16** (`MG4a`-`MG4d`).
Design:  `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §6 ("MG4 — THE DESIGN. NOT
         BUILT."), `PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md` §10.
Results: `PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md`.
Seed:    `seeds/arc_decompose.json` (emitted by
         `tools/build_arc_decompose_seed.py`), plus the ONE additive guard in
         `seeds/arc_magnitude.json` v1.1.0 (`mg_goal_order_n_default`).

WHAT THIS GATES.  `mg_rung` (`seeds/arc_magnitude.json`) computes
`decompose_required` and names the measured ladder a split would use, but
nothing consumed it — MAGNITUDE.md §6 designed the consumer and did not
build it. This suite gates the consumer: `mg_decompose` mints one child
`ArcGoal` per un-materialised tier of the ladder once `decompose_required`
holds, `mg_decompose_retire` moves the parent to a terminal, pool-excluded
state once every tier is materialised, and `mg_child_order_n` gives each
child its own discounted order-N headroom.

A REAL DESIGN CORRECTION LANDED MID-BUILD, reported here rather than
smoothed over (A16's own registered correction).  A first draft gated each
child's mint on the tier's own `in_horizon` flag; this is MATHEMATICALLY
INCOMPATIBLE with `decompose_required`'s own trigger (`ratio_first > 1`
implies EVERY tier's cumulative cost exceeds the horizon, by monotonicity —
so `decompose_required==1` and `EXISTS t, in_horizon(t)` never co-occur) and
would have made `mg_decompose` permanently dead under its own natural
trigger. Corrected: every tier mints unconditionally; the horizon instead
determines each child's OWN `magnitude_rung` afterward, via the unchanged
`mg_rung`. The registered arithmetic identity therefore holds on a
CONSTRUCTED scene (decomposition forced with no horizon truncating the
parent's reading) but NOT on the natural push_back trigger, where the
parent's own `orderN_headroom_n` is horizon-truncated to `0` while the
children correctly sum to the ladder's full projected value — both measured
below, neither hidden.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    pytest tests/test_arc_decompose_migrated.py --confcutdir=<this worktree> -q
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest  # noqa: E402
import substrate_rs as srs  # noqa: E402

from domains import arc_decompose_ingest as adi  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "arc_decompose.json")
MAG_SEED_PATH = os.path.join(ROOT, "seeds", "arc_magnitude.json")
GOALS_SEED_PATH = os.path.join(ROOT, "seeds", "arc_goals.json")
STRUCTURAL = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"
EPS = 1e-6


# =========================================================================== #
#  BOOT / SCENE HELPERS
# =========================================================================== #
def _assert_engine_coherent(s):
    n = s.add_node("ArcDecompEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], (
        "VALUE LAYER ABSENT — list and tuple collapsed. Not this rung's "
        "result to re-pin: the tree is incoherent.")
    return True


def _boot(epoch=0, with_ladder=True, with_attrition=True, with_decompose=True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    _assert_engine_coherent(s)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_magnitude"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    if with_decompose:
        s._inner.load_seed_manifest(manifest_for("arc_decompose"), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, epoch)
    if with_ladder:
        ami.install_tier_ladder(s, ami.probe_tier_ladder())
    if with_attrition:
        ami.resolve_attrition_keys(s)
    s._inner.run_rules()
    return s, ag


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _rule(name, doc=None):
    for r in (doc or _seed())["rules"]:
        if r["name"] == name:
            return r
    raise AssertionError("no such rule: " + name)


def _answer_horizon(s, units, *, conditioned=False, ckind="horizon", **kw):
    qs = list(s.nodes("ArcConstraintQuestion"))
    assert qs, "no ArcConstraintQuestion to answer — the ask did not fire"
    extra = {}
    if conditioned:
        extra = {"cond_kind": "fact_equals",
                 "cond_filter_value": "arc6_structural_ceiling_present",
                 "cond_expected_str": "1"}
    ami.attach_constraint_reply(s, qs[0], "answer", con_kind=ckind,
                                horizon_units=units, **extra, **kw)
    s._inner.run_rules()


def _goal_node(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"]["agid"] == agid:
            return n
    raise AssertionError("no such goal: " + agid)


def _goal(s, agid):
    return s.node(_goal_node(s, agid))["attrs"]


def _children(s, parent_agid):
    return sorted((dict(s.node(n)["attrs"]) for n in s.nodes("ArcGoal")
                  if s.node(n)["attrs"].get("parent_agid") == parent_agid),
                  key=lambda a: a.get("tier_order") or 0.0)


def _drive_natural_decompose(s, horizon_units=5.0):
    """THE ONLY WORKING CONSTRUCTION — a REAL horizon reply (never a raw
    attribute poke) at a horizon tight enough to trigger `decompose_required`
    NATURALLY and PERSISTENTLY (every pass recomputes it fresh from the SAME
    held horizon, so it does not need to survive a poke).

    A FIRST DRAFT tried a raw `decompose_required` poke with NO horizon held
    (hoping to see every tier read `in_horizon` and a non-degenerate
    identity). MEASURED NOT TO WORK, and the reason is a genuine engine
    finding, not a mistake in the poke itself: `run_rules()` evaluates rules
    in LOAD order, not against one shared pre-pass snapshot ACROSS rules from
    different seeds (the pcon_mint "effects apply against pre-effect reads"
    guarantee is about ONE rule's own multiple candidate matches in a pass,
    not a cross-rule guarantee). `mg_rung` (`arc_magnitude`, loaded first)
    therefore reads and overwrites `decompose_required` back to `0.0` (its
    own unconditional, every-pass recompute under `NO_HORIZON`) BEFORE
    `mg_decompose` (`arc_decompose`, loaded after) ever gets to observe the
    poked `1.0` — REPEATING the poke does not help, because the SAME race
    re-happens on every single `run_rules()` call. Confirmed directly:
    evaluating `mg_decompose`'s own `where` Term against the freshly-poked
    graph BEFORE calling `run_rules()` returns `True` for every clause; only
    after `run_rules()` runs does the poke turn out to have been overwritten.
    """
    qs = list(s.nodes("ArcConstraintQuestion"))
    assert qs, "no ArcConstraintQuestion to answer — the ask did not fire"
    ami.attach_constraint_reply(s, qs[0], "answer", con_kind="horizon",
                                horizon_units=horizon_units)
    s._inner.run_rules()
    return s.node(_goal_node(s, STRUCTURAL))["attrs"]


# =========================================================================== #
#  PRECONDITION
# =========================================================================== #
def test_engine_coherent_probe_passes():
    s, _ = _boot()


def test_arc_decompose_seed_loads_and_carries_FOUR_rules():
    """INVERTED, not removed, per the WH1/A15/A16 precedent: A17 added
    `mg_tier_retire` (v1.0.0 -> v1.1.0) — a THIRD, independent retirement
    mechanism for a `decomposition_tier` child, at the same low cost
    (seed data + one adapter fact-probe + one rule, zero new Rust, zero
    touch to `ax_dispatch`). See PROGRAM_SYNTHESIS_ARC6_RETIRE_BLOCKER.md."""
    d = _seed()
    names = {r["name"] for r in d["rules"]}
    assert names == {"mg_decompose", "mg_decompose_retire", "mg_child_order_n",
                     "mg_tier_retire"}


# =========================================================================== #
#  MG4a — THE REGISTERED ARITHMETIC IDENTITY, BOTH DIRECTIONS.
# =========================================================================== #
def test_mg4a_the_identity_holds_against_the_PRE_horizon_captured_value():
    """THE CONSTRUCTED COMPARISON: `orderN_headroom_n` CAPTURED AT BOOT,
    before any horizon is held (the ladder's full, untruncated projected
    value — 13.637248 on the shipped ladder), against what the children sum
    to once a real horizon reply DRIVES decomposition. This is "a
    constructed decomposition scene" in the sense the bar means it — the
    reference value is deliberately captured before horizon truncation
    enters the picture, not read live off the post-decompose parent (see
    `test_mg4a_the_NATURAL_trigger_shows_the_HONEST_mismatch` for why that
    live reading is a DIFFERENT number)."""
    s, _ = _boot()
    pre = _goal(s, STRUCTURAL)
    assert pre["order_n_basis"] == "measured_tier_ladder"
    pre_orderN = pre["orderN_headroom_n"]
    assert pre_orderN > 13.0, pre_orderN  # sanity: the full, undiscounted sum

    parent = _drive_natural_decompose(s, 5.0)
    assert parent["status"] == "decomposed"
    assert parent["headroom_n"] == 0.0
    assert parent["orderN_headroom_n"] == 0.0

    children = _children(s, STRUCTURAL)
    assert len(children) == 4, [c["agid"] for c in children]
    total = sum(c["headroom_n"] * c["tier_survival"] for c in children)
    assert abs(total - pre_orderN) < EPS, (total, pre_orderN)


def test_mg4a_the_identity_is_a_check_that_CAN_fail():
    """A7's own discipline: a control not shown capable of detecting the
    violation it exists to catch is not a control. Corrupt one child's
    `tier_survival` after a correctly-built decomposition and show the SAME
    arithmetic check now reports a mismatch."""
    s, _ = _boot()
    pre_orderN = _goal(s, STRUCTURAL)["orderN_headroom_n"]
    _drive_natural_decompose(s, 5.0)
    children = _children(s, STRUCTURAL)
    total_correct = sum(c["headroom_n"] * c["tier_survival"] for c in children)
    assert abs(total_correct - pre_orderN) < EPS

    corrupted = list(children)
    corrupted[0] = dict(corrupted[0], tier_survival=0.0)  # dropped, per A10
    total_corrupted = sum(c["headroom_n"] * c["tier_survival"]
                          for c in corrupted)
    assert abs(total_corrupted - pre_orderN) > 1.0, (
        "the check did not notice a dropped survival factor")


def test_mg4a_the_NATURAL_trigger_shows_the_HONEST_mismatch():
    """A16's registered, honest finding. At the NATURAL push_back trigger
    (horizon=5, the SAME horizon the existing pinned MAGNITUDE.md scene
    uses), decompose_required is TRUE without any poke, and every tier
    materialises as a child — but the parent's own `orderN_headroom_n`
    reads 0.0 post-decompose (horizon-truncated: nothing fit, which is WHY
    decomposition triggered), while the children correctly sum to the
    ladder's full, untruncated projected value. `Sum(children) ==
    parent.orderN_headroom_n` — the bar AS LITERALLY WORDED — does NOT hold
    here (13.637 != 0); it holds only on the constructed scene above. Both
    are measured, neither is hidden."""
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    parent = _goal(s, STRUCTURAL)
    assert parent["magnitude_rung"] == "push_back"
    assert parent["decompose_required"] == 1.0
    assert parent["status"] == "decomposed"
    assert parent["orderN_headroom_n"] == 0.0

    children = _children(s, STRUCTURAL)
    assert len(children) == 4, [c["agid"] for c in children]
    total = sum(c["headroom_n"] * c["tier_survival"] for c in children)
    assert abs(total - 13.637248) < 1e-3, total
    # THE LITERAL BAR FAILS HERE, ON PURPOSE, DOCUMENTED:
    assert abs(total - parent["orderN_headroom_n"]) > 1.0


# =========================================================================== #
#  MG4b — THE PARENT LEAVES THE POOL, PAIRED LISTS.
# =========================================================================== #
def test_mg4b_pool_membership_paired_list_natural_horizon():
    s, _ = _boot()
    before_pool = set(adi.pool_agids(s))
    assert STRUCTURAL in before_pool

    _answer_horizon(s, 5.0)
    after_pool = set(adi.pool_agids(s))
    children = _children(s, STRUCTURAL)
    child_agids = {c["agid"] for c in children}

    assert STRUCTURAL not in after_pool
    assert child_agids <= after_pool
    assert before_pool - after_pool == {STRUCTURAL}
    assert after_pool - before_pool == child_agids
    assert len(child_agids) == 4


def test_mg4b_each_child_is_INDIVIDUALLY_repriced_by_the_UNCHANGED_mg_rung():
    """MAGNITUDE.md §6.3's own promise: a child is a SEPARATE ArcGoal, so
    `mg_rung` (untouched) prices it on its OWN `cost_bits` against the SAME
    horizon. LIVE, on the SAME natural horizon=5 scene: each child's
    `magnitude_ratio` tracks ITS OWN `cost_bits` (8/5, 18/5, 24/5, 28/5),
    four DIFFERENT numbers, rather than all four sharing the parent's single
    28/5 ratio — the demonstration that mg_rung prices each fragment
    independently, not merely "it doesn't crash".

    A NAMED RESIDUAL, reported rather than fixed: on THIS shipped, NESTED
    ladder, `cost_bits` is each tier's CUMULATIVE cost, and tier 1's
    cumulative cost IS `cost_first` — the exact quantity
    `decompose_required`'s own trigger already tested against the horizon.
    So no child can be individually MORE AFFORDABLE (cross into `absorb`)
    than what `decompose_required` already implied at the horizon that
    triggered decomposition — computed, not measured live here (a second,
    wider horizon cannot be layered onto the SAME scene: `mg_ask_constraints`
    only re-asks once a NEW measurement epoch bumps, and this rung does not
    touch the epoch producer). At horizon=10 (26.7% wider than the ladder's
    minimum tier cost), tier 1 alone WOULD read `absorb` (8/10=0.8) while
    the un-decomposed parent's own ladder ratio (28/10=2.8) would not — the
    arithmetic is reported in
    `PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md` as a computed illustration,
    not asserted as a second live graph state here."""
    s, _ = _boot()
    parent = _drive_natural_decompose(s, 5.0)
    assert parent["status"] == "decomposed"
    children = _children(s, STRUCTURAL)
    assert [c["magnitude_cost_units"] for c in children] == [8.0, 18.0, 24.0,
                                                              28.0]
    assert [c["cost_bits"] for c in children] == [8.0, 18.0, 24.0, 28.0]
    ratios = [c["magnitude_ratio"] for c in children]
    assert ratios == [8.0 / 5.0, 18.0 / 5.0, 24.0 / 5.0, 28.0 / 5.0], ratios
    assert len(set(ratios)) == 4, "children were NOT individually repriced"
    # every child individually reads push_back at THIS horizon (see docstring
    # residual) — but the RATIOS still differ, which is the demonstration.
    assert all(c["magnitude_rung"] == "push_back" for c in children)


# =========================================================================== #
#  MG4c — NO DOUBLE-COUNTING, LIVE.
# =========================================================================== #
def test_mg4c_the_parent_and_its_children_are_NEVER_simultaneously_pooled():
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    pool = set(adi.pool_agids(s))
    children = {c["agid"] for c in _children(s, STRUCTURAL)}
    assert STRUCTURAL not in pool
    assert children <= pool
    assert STRUCTURAL not in children  # sanity: disjoint identities


def test_mg4c_the_parents_own_value_is_STRUCTURALLY_unreachable_once_excluded():
    """Not merely absent from a printed rank: `MaxOver` over `ag_select`'s
    OWN `Filter` cannot select a filtered-out element, so the parent cannot
    be the order-1 winner once its `headroom_n` is `0.0` — read off
    `ag_select`'s own stamped selection, not re-derived here."""
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    sel = agi.selection(s)
    assert sel["arc_sel_agid"] != STRUCTURAL
    mag = ami.mag_selection(s)
    assert mag["mg_sel_agid"] != STRUCTURAL


def test_mg4c_decomposition_does_NOT_fire_when_nothing_is_required():
    """The negative half: `absorb`/`balance` never mint a child — the
    existing MG3 scenes are untouched by loading this seed."""
    for h, want in ((40.0, "absorb"), (20.0, "balance")):
        s, _ = _boot()
        _answer_horizon(s, h)
        g = _goal(s, STRUCTURAL)
        assert g["magnitude_rung"] == want
        assert g["status"] != "decomposed"
        assert _children(s, STRUCTURAL) == []


# =========================================================================== #
#  MG4d — NO REGRESSION.
# =========================================================================== #
def test_mg4d_the_seed_regenerates_byte_identically():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools",
                                      "build_arc_decompose_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr


def test_mg4d_arc_magnitude_seed_regenerates_byte_identically():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools",
                                      "build_arc_magnitude_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr


def test_mg4d_the_EXISTING_seeds_below_arc_magnitude_are_BYTE_IDENTICAL_to_HEAD():
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json"):
        r = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", rel],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, (rel, r.stdout[:400])


def test_mg4d_the_ONE_new_guard_is_INERT_on_every_existing_magnitude_scene():
    """`mg_goal_order_n_default` gained one additive exclusion
    (`parent_agid` absent) — this must change NOTHING on any scene that
    never loads `arc_decompose`. Re-run the 43 pre-existing magnitude gates'
    own module and require it fully green with this worktree's regenerated
    `seeds/arc_magnitude.json`."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_arc_magnitude_migrated.py",
         "-q", "--confcutdir", ROOT, "-p", "no:randomly"],
        capture_output=True, text=True, cwd=ROOT,
        env=dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1",
                 PYTHONPATH=os.pathsep.join(
                     [os.path.join(ROOT, "runners", "dsl", "python"), ROOT])))
    assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-2000:]
    assert "43 passed" in r.stdout, r.stdout[-800:]


def test_mg4d_no_python_decision_was_added():
    """The adapter is held to the module-specific form `arc_magnitude_ingest`
    passes. Read through `ast` with string literals stripped."""
    path = os.path.join(ROOT, "domains", "arc_decompose_ingest.py")
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""
    src = ast.unparse(tree)
    for banned in ("import substrate_rs", ".evaluate(", "run_rules",
                   "graph_rewrite", "add_rule"):
        assert banned not in src, banned
    assert "_inner" in src  # the adapter does touch the substrate, mechanically


def test_mg4d_every_rule_installed_and_fires_at_least_once():
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    installed = {r["name"] for r in s._inner.export_rules()}
    for name in ("mg_decompose", "mg_decompose_retire", "mg_child_order_n"):
        assert name in installed, name
    fired = {
        "mg_decompose": len(_children(s, STRUCTURAL)) == 4,
        "mg_decompose_retire": _goal(s, STRUCTURAL)["status"] == "decomposed",
        "mg_child_order_n": all(
            c.get("order_n_basis") == "decomposition_child_tier_survival"
            for c in _children(s, STRUCTURAL)),
    }
    assert all(fired.values()), [k for k, v in fired.items() if not v]


def test_mg4d_the_fixpoint_TERMINATES_a_second_pass_moves_nothing():
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    before = sorted((g.get("agid"), g.get("orderN_headroom_n"),
                     g.get("status")) for g in ami.goal_rows(s))
    n_before = len(list(s.nodes("ArcGoal")))
    s._inner.run_rules()
    s._inner.run_rules()
    after = sorted((g.get("agid"), g.get("orderN_headroom_n"),
                    g.get("status")) for g in ami.goal_rows(s))
    n_after = len(list(s.nodes("ArcGoal")))
    assert before == after and n_before == n_after


def test_mg4d_the_seed_is_NOT_globbed_into_every_agent_in_the_tree():
    assert _seed()["self_load_only"] is True
    from substrate.boot_all import _read_seeds
    loaded = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "arc_decompose" not in loaded
    assert "arc_magnitude" not in loaded
    assert manifest_for("arc_decompose")["id"] == "arc_decompose"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    for sid in ("goal_residuals", "arc_goals", "arc_magnitude"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    assert adi.ensure_arc_decompose(s, ag) is True
    assert adi.ensure_arc_decompose(s, ag) is False
    assert any(r["name"].startswith("mg_decompose")
               for r in s._inner.export_rules())


def test_mg4d_no_dependency_on_arc_executor():
    assert "arc_executor" not in _seed()["depends_on"]
    assert _seed()["depends_on"] == ["goal_residuals", "arc_goals",
                                      "arc_magnitude"]


# =========================================================================== #
#  A17 — RETIRING A supply_blocker-DESCENDED POOL MEMBER.
#  `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A17.
#  `PROGRAM_SYNTHESIS_ARC6_RETIRE_BLOCKER.md`.
# =========================================================================== #
STRUCTURAL_LADDER_KEY = "missing_structural_primitive"


def test_ar17_the_seed_version_bumped_and_carries_mg_tier_retire():
    d = _seed()
    assert d["version"] == "1.1.0"
    assert any(r["name"] == "mg_tier_retire" for r in d["rules"])


def test_ar17_probe_reads_the_REAL_committed_artifact_HONESTLY():
    """AR17b(ii)'s own bar: the mechanism must be shown to correctly DECLINE
    on the real, currently-reachable state.  On the artifact this rung's own
    base commit ships (`results/arc6_structural_ceiling.json`,
    `strict_reach.witness_and_in_budget_ids ==
    [75, 98, 106, 161, 257, 290]`), tier 1's own 10-id increment is NOT
    fully covered -- `18` and `310` were never witness-verified there at
    all, and `424`/`450` are only covered after a LIVE re-measurement (see
    the live test below), not on the frozen committed artifact.  A check
    that cannot fail is not a check (A7's standing rule); this one does,
    honestly, on real data, with no mutation of the artifact."""
    recs = adi.probe_tier_witness_coverage()
    assert recs, "the ladder must resolve against the shipped artifacts"
    by_order = {r["tier_order"]: r for r in recs}
    assert set(by_order) == {1.0, 2.0, 3.0, 4.0}
    tier1 = by_order[1.0]
    assert tier1["ladder_key"] == STRUCTURAL_LADDER_KEY
    assert tier1["increment_ids"] == [18, 75, 98, 106, 161, 257, 290, 310,
                                      424, 450]
    assert tier1["all_ids_covered"] == 0.0
    assert set(tier1["missing_ids"]) >= {18, 310}, tier1["missing_ids"]
    # every tier is honestly unresolved on the committed artifact -- tiers
    # 2-4 need capability this tree does not have at all (new Term
    # variants, the string-order fix, Recurse), so their gap is far wider.
    assert all(r["all_ids_covered"] == 0.0 for r in recs)


def test_ar17_a_LIVE_stash_protected_remeasurement_shows_REAL_partial_progress():
    """A real subprocess re-run of the UNMODIFIED
    `scripts/arc6_structural_ceiling.py` (the same script A15's second
    `ExecClass` already wires), stash-protected and sha-verified before and
    after, exactly A15 SS1 item 7 / SS2's own discipline.  Demonstrates the
    mechanism's fact-probe reads REAL drift (not a fixture): witness
    coverage genuinely GROWS (+424, +450, the identical delta A15 found on
    a different engine) but tier 1 STILL does not reach full coverage (`18`
    and `310` remain missing) -- the honest natural-state finding this
    rung's own design investigation names, reproduced live here rather than
    merely quoted."""
    import hashlib
    import shutil
    import subprocess
    import tempfile

    art = os.path.join(ROOT, "results", "arc6_structural_ceiling.json")
    before_sha = hashlib.sha256(open(art, "rb").read()).hexdigest()
    stash_dir = tempfile.mkdtemp(prefix="ar17_structural_stash_")
    stash_path = os.path.join(stash_dir, "arc6_structural_ceiling.json")
    shutil.copy2(art, stash_path)
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts",
                                          "arc6_structural_ceiling.py")],
            capture_output=True, text=True, cwd=ROOT,
            env=dict(os.environ, OZMA_NO_LLM="1",
                     PYTHONPATH=os.pathsep.join(
                         [os.path.join(ROOT, "runners", "dsl", "python"),
                          ROOT])),
            timeout=120)
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]

        recs = adi.probe_tier_witness_coverage()
        tier1 = next(x for x in recs if x["tier_order"] == 1.0)
        # the live delta: 424/450 now covered, 18/310 still not.
        assert set(tier1["missing_ids"]) == {18, 310}, tier1["missing_ids"]
        assert tier1["all_ids_covered"] == 0.0
        with open(art) as fh:
            fresh = json.load(fh)
        witness = set(fresh["strict_reach"]["witness_and_in_budget_ids"])
        assert {424, 450} <= witness
        assert not ({18, 310} & witness)
    finally:
        after_sha_before_restore = hashlib.sha256(open(art, "rb").read()).hexdigest()
        shutil.copy2(stash_path, art)
        restored_sha = hashlib.sha256(open(art, "rb").read()).hexdigest()
        assert restored_sha == before_sha, (
            "protected artifact restore FAILED to reproduce the pristine "
            "sha — before=%s after_live_run=%s restored=%s" %
            (before_sha, after_sha_before_restore, restored_sha))
        shutil.rmtree(stash_dir, ignore_errors=True)


def _scene_with_children(s=None, horizon=5.0):
    if s is None:
        s, _ = _boot()
    _drive_natural_decompose(s, horizon)
    return s


def test_ar17_a_CONSTRUCTED_witness_fact_retires_ONLY_the_matching_tier():
    """THE POSITIVE SCENE, constructed exactly as A13 SS7.1 / A15 SS4.2
    constructed theirs: the retirement condition's NATURAL trigger (full
    live witness coverage) is not cheaply reachable on this engine (the
    live test above shows it genuinely short by 2 ids), so this scene
    installs the fact a real, completed re-measurement WOULD produce and
    demonstrates the RULE fires correctly on it — the same "synthetic
    trigger, real rule" separation A15 SS4.2 named explicitly. Only tier 1's
    OWN child resolves; tiers 2-4 are untouched by a fact naming tier 1."""
    s = _scene_with_children()
    children_before = _children(s, STRUCTURAL)
    assert len(children_before) == 4
    assert all(c.get("status") != "resolved" for c in children_before)

    adi.install_tier_witness_facts(s, [{
        "ladder_key": STRUCTURAL_LADDER_KEY, "tier_order": 1.0,
        "all_ids_covered": 1.0, "increment_ids": list(range(10)),
        "missing_ids": [], "evidence_artifact": "results/TEST_CONSTRUCTED",
    }])
    s._inner.run_rules()

    children = {c["tier_order"]: c for c in _children(s, STRUCTURAL)}
    assert children[1.0]["status"] == "resolved"
    assert children[1.0]["headroom_n"] == 0.0
    assert children[1.0]["orderN_headroom_n"] == 0.0
    assert children[1.0]["resolved_because"] == "tier_units_witness_verified_live"
    for order in (2.0, 3.0, 4.0):
        assert children[order]["status"] != "resolved", order
        assert children[order]["headroom_n"] > 0.0, order


def test_ar17_a_witness_fact_naming_a_DIFFERENT_tier_leaves_tier1_UNRESOLVED():
    """Negative control, both halves: (a) a `covered=1.0` fact for tier 2
    resolves tier 2 and ONLY tier 2 — tier 1 is untouched by a fact that
    does not name it; (b) an `all_ids_covered=0.0` fact for tier 1 itself
    does NOT resolve it — the guard reads the fact's VALUE, not merely its
    existence for that (ladder_key, tier_order) pair."""
    s = _scene_with_children()
    adi.install_tier_witness_facts(s, [
        {"ladder_key": STRUCTURAL_LADDER_KEY, "tier_order": 2.0,
         "all_ids_covered": 1.0, "increment_ids": [], "missing_ids": [],
         "evidence_artifact": "results/TEST"},
        {"ladder_key": STRUCTURAL_LADDER_KEY, "tier_order": 1.0,
         "all_ids_covered": 0.0, "increment_ids": [18], "missing_ids": [18],
         "evidence_artifact": "results/TEST"},
    ])
    s._inner.run_rules()
    children = {c["tier_order"]: c for c in _children(s, STRUCTURAL)}
    assert children[1.0]["status"] != "resolved"
    assert children[1.0]["headroom_n"] > 0.0
    assert children[2.0]["status"] == "resolved"
    assert children[2.0]["headroom_n"] == 0.0
    for order in (3.0, 4.0):
        assert children[order]["status"] != "resolved", order
        assert children[order]["headroom_n"] > 0.0, order


def test_ar17_the_resolved_tier_is_STRUCTURALLY_excluded_from_BOTH_pools():
    """Mirrors MG4c exactly, one grain down: once tier 1's `headroom_n` is
    zeroed, it is absent from `POOL()` under BOTH `ag_select` (order-1) and
    `mg_select` (order-N, the same shared `Filter`), read via
    `adi.pool_agids` — the same predicate `POOL()` encodes, never a
    hand-rolled variant."""
    s = _scene_with_children()
    adi.install_tier_witness_facts(s, [{
        "ladder_key": STRUCTURAL_LADDER_KEY, "tier_order": 1.0,
        "all_ids_covered": 1.0, "increment_ids": [], "missing_ids": [],
        "evidence_artifact": "results/TEST",
    }])
    s._inner.run_rules()
    tier1_agid = next(c["agid"] for c in _children(s, STRUCTURAL)
                      if c["tier_order"] == 1.0)
    pool = adi.pool_agids(s)
    assert tier1_agid not in pool
    other_children = [c["agid"] for c in _children(s, STRUCTURAL)
                      if c["tier_order"] != 1.0]
    assert set(other_children) <= set(pool), (other_children, pool)


def test_ar17_the_fixpoint_TERMINATES_a_second_pass_moves_nothing():
    s = _scene_with_children()
    adi.install_tier_witness_facts(s, [{
        "ladder_key": STRUCTURAL_LADDER_KEY, "tier_order": 1.0,
        "all_ids_covered": 1.0, "increment_ids": [], "missing_ids": [],
        "evidence_artifact": "results/TEST",
    }])
    s._inner.run_rules()
    before = sorted((c["agid"], c["status"], c["headroom_n"])
                    for c in _children(s, STRUCTURAL))
    s._inner.run_rules()
    s._inner.run_rules()
    after = sorted((c["agid"], c["status"], c["headroom_n"])
                   for c in _children(s, STRUCTURAL))
    assert before == after


def test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED():
    """AR17b(iii)'s own cost bar: no new Rust, no change to
    `ax_dispatch`/`ROUTE`/`_routable`.

    A18 EXCEPTION, NAMED — the WH1 precedent this same suite already uses
    once (`test_mg4d_...`): invert a pin with a docstring, never silently
    remove it.  `domains/arc_executor.py` and `tools/build_arc_executor_
    seed.py` are no longer whole-file byte-identical to `HEAD` — A18 (the
    re-arm deadlock) legitimately ADDS a sixth rule (`ax_world_probe_epoch`)
    and a new adapter function pair to those two files.  AR17's own claim
    was narrower than the whole file even at the time it was written (its
    OWN docstring names `ax_dispatch`/`ROUTE`/`_routable`), so this asserts
    THAT claim directly — the specific route-matching Term builders A18's
    own PREREG amendment (AR18d) registered as untouched, read back by name
    via `ast` and compared against `HEAD`'s own source for the SAME
    functions — rather than the whole-file diff, which is what AR17
    actually had available to it before A18 existed and is no longer the
    right instrument."""
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/arc_magnitude.json", "seeds/program_synthesis.json"):
        r = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", rel],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, (rel, r.stdout[:400])
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--", "runners/dsl/src/"],
        capture_output=True, text=True, cwd=ROOT)
    assert diff.stdout.strip() == "", "no new Rust for A17/A18"

    import ast

    def _fn_src(path, name):
        tree = ast.parse(open(path).read())
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and n.name == name:
                return ast.unparse(n)
        raise AssertionError("no such function: %s in %s" % (name, path))

    def _fn_src_at_head(rel, name):
        prefix = subprocess.run(["git", "-C", ROOT, "rev-parse",
                                 "--show-prefix"], capture_output=True,
                                text=True).stdout.strip()
        text = subprocess.run(["git", "-C", ROOT, "show",
                               "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        tree = ast.parse(text)
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and n.name == name:
                return ast.unparse(n)
        raise AssertionError("no such function at HEAD: %s in %s" % (name, rel))

    builder = os.path.join(ROOT, "tools", "build_arc_executor_seed.py")
    for fn in ("ROUTE", "_routable", "_dispatchable", "_cue_matches",
               "_r_dispatch", "_r_rearm", "_armed", "_in_pool"):
        assert _fn_src(builder, fn) == _fn_src_at_head(
            "tools/build_arc_executor_seed.py", fn), fn

    adapter = os.path.join(ROOT, "domains", "arc_executor.py")
    for fn in ("run_order", "arm", "reingest_evidence"):
        assert _fn_src(adapter, fn) == _fn_src_at_head(
            "domains/arc_executor.py", fn), fn


def test_ar17_the_seed_regenerates_byte_identically():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools",
                                      "build_arc_decompose_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
