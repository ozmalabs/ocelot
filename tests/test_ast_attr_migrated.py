"""GATE — ATTR-THRESHOLD FALSE NEGATIVE (T2 codebook-crossing).

Pre-registered in `VISION_AST_ATTR_PREREG.md`, committed BEFORE the run at `bfc1eef5`.

Closes the false-negative class the tripwire rung measured in its OWN detector and left
unpatched under §5, and PROVES the part that cannot be closed (§1.5).

THE CONJUNCTION IS THE GATE (process rule 5, confirmed SEVEN times before this rung):
a detect-nothing build scores a PERFECT false-positive arm, and a detect-everything
build scores a PERFECT evasion arm. Neither floor alone is a gate. The tests below are
written so that each degenerate build reddens a DIFFERENT arm, and
`test_positive_control_*` injects both into the REAL detector to demonstrate it.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import term_ast_audit as A  # noqa: E402
from tools.term_ast_audit import (  # noqa: E402
    audit_seed_file, comparisons_in, is_codebook_crossing, scope_from_match,
    walk_terms_scoped,
)

SEEDS = os.path.join(ROOT, "seeds")


def _seed(name):
    return os.path.join(SEEDS, name)


def _tripwire():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tripwire_repair_measure",
        os.path.join(ROOT, "scripts", "tripwire_repair_measure.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ================================================================================
# THE HEADLINE — the Attr-threshold bound is DETECTED
# ================================================================================

def test_headline_t2_category_box_containment_is_found():
    """T2 category's FOUR `Lte(Attr,Attr)` box-containment bounds are found.

    This is the concrete affected case named by the tripwire rung: T1 measured 0.
    """
    a = audit_seed_file(_seed("vision_category.json"), "cat_recognize")
    assert a["T1_bound_like"] == 0, "premise: T1 misses these — if not, the rung is moot"
    assert a["T2_bound_like"] == 4
    promoted = [d for d in a["T2_detail"] if d["via"] == "T2_codebook_crossing"]
    assert len(promoted) == 4
    assert all(d["op"] == "Lte" and d["operands"] == ["Attr", "Attr"] for d in promoted)


def test_headline_the_bare_attr_threshold_probe_is_still_missed():
    """The tripwire rung's BARE probe is NOT recovered — and that is CORRECT, not a bug.

    Pinned so nobody later "fixes" it into a false positive: §1.5 proves it is
    AST-identical to a declared non-bound.
    """
    probe = {"type": "Lt",
             "a": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "dist"},
             "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"}, "key": "bound"}}
    assert not any(c.t2_bound_like for c in comparisons_in(probe))
    assert all(c.undecidable_residual for c in comparisons_in(probe))


# ================================================================================
# THE CONJUNCTION — no over-reporting (T0's 19 must NOT return)
# ================================================================================

def test_conjunction_similarity_still_reports_zero_bounds():
    """T0 finds 19 comparators in the similarity path; T2 must still find ZERO bounds."""
    a = audit_seed_file(_seed("shape_decode_loop.json"), None)
    assert a["T0_any_comparator"] == 19, "T0 population must reproduce"
    assert a["T1_bound_like"] == 0
    assert a["T2_bound_like"] == 0, "T0's over-reporting must NOT return via T2"


def test_conjunction_sd_redecode_epoch_read_is_not_promoted():
    """The single `Attr`-vs-`Attr` in the similarity path is an EPOCH read, not a bound.

    `Lt(Attr(obs,'decoded_epoch'), Attr(ag,'codebook_epoch'))` — both operands
    match-bound, so no codebook candidate is in scope and no admission is decided.
    """
    seed = json.load(open(_seed("shape_decode_loop.json")))
    rule = [r for r in seed["rules"] if r["name"] == "sd_redecode"][0]
    found = [c for c in comparisons_in(rule, rule="sd_redecode")
             if tuple(c.operand_roots) == ("Attr", "Attr")]
    assert len(found) == 1
    assert not found[0].t2_bound_like
    assert found[0].undecidable_residual


def test_conjunction_tripwire_nonbound_battery_still_clean():
    """All THREE of the tripwire rung's declared non-bounds stay non-bounds under T2."""
    for name, _why, tree in _tripwire().nonbound_battery():
        assert not any(c.t2_bound_like for c in comparisons_in(tree)), name


# ================================================================================
# THE EVASION BATTERY — re-run, must stay 7/7
# ================================================================================

def test_evasion_battery_still_seven_of_seven():
    rows = [(name, any(c.t2_bound_like for c in comparisons_in(tree)))
            for name, _why, tree in _tripwire().evasion_battery()]
    assert len(rows) == 7
    assert all(hit for _n, hit in rows), [n for n, h in rows if not h]


# ================================================================================
# TIER ALGEBRA — T2 only ever PROMOTES; it reverses nothing
# ================================================================================

@pytest.mark.parametrize("seed_name", [
    "vision_category.json", "shape_decode_loop.json", "vision_uniqueness.json",
    "vision_deformation.json", "vision_colour_identity.json",
])
def test_tier_algebra_t1_subset_t2_subset_t0(seed_name):
    a = audit_seed_file(_seed(seed_name), None)
    assert a["T1_bound_like"] <= a["T2_bound_like"] <= a["T0_any_comparator"]
    assert a["bound_range"] == [a["T2_bound_like"], a["T0_any_comparator"]]


def test_t2_fires_only_on_attr_vs_attr():
    """T2 must not touch any verdict T1 already reaches — the class is disjoint."""
    for path in sorted(os.listdir(SEEDS)):
        if not path.endswith(".json"):
            continue
        try:
            seed = json.load(open(_seed(path)))
        except Exception:
            continue
        if not isinstance(seed, dict):
            continue
        for r in seed.get("rules", []) or []:
            for c in comparisons_in(r, rule=r.get("name", "")):
                if c.codebook_crossing:
                    assert tuple(c.operand_roots) == ("Attr", "Attr"), (path, c.rule)
                    assert not c.bound_like, "T2 fired on something T1 already had"


# ================================================================================
# THE DERIVED NEGATIVE — proven, not asserted
# ================================================================================

def test_derived_negative_residual_class_is_not_structurally_decidable():
    """A genuine stored-threshold bound and a DECLARED non-bound are the SAME AST.

    Erase attribute names — the only thing that differs — and they are equal. So no
    structural predicate separates them, and the audit table must report a RANGE.
    """
    def canon(n):
        if isinstance(n, dict):
            return {k: ("<erased>" if k in ("key", "name") and isinstance(v, str)
                        and n.get("type") in ("Attr", "Var") else canon(v))
                    for k, v in sorted(n.items())}
        return [canon(x) for x in n] if isinstance(n, list) else n

    genuine = {"type": "Lt",
               "a": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "dist"},
               "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"}, "key": "bound"}}
    nonbound = {"type": "Lt",
                "a": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "epoch"},
                "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"},
                      "key": "codebook_epoch"}}
    assert canon(genuine) == canon(nonbound)
    # and the detector treats them identically, as it must
    assert (any(c.t2_bound_like for c in comparisons_in(genuine))
            == any(c.t2_bound_like for c in comparisons_in(nonbound)))


def test_audit_reports_a_range_not_a_verdict_where_residual_exists():
    a = audit_seed_file(_seed("shape_decode_loop.json"), None)
    assert a["undecidable_residual"] >= 1
    assert not a["range_is_tight"], "a scope with residual must NOT claim a tight range"
    assert a["bound_range"][0] < a["bound_range"][1]


# ================================================================================
# THE AUDIT TABLE — exactly ONE verdict moves
# ================================================================================

TABLE = [
    ("colour identity", "vision_colour_identity.json", "ci_assign", 6, 1, 1),
    ("similarity",      "shape_decode_loop.json",      None,        19, 0, 0),
    ("deformation",     "vision_deformation.json",     "df_recognize", 3, 3, 3),
    ("T2 category",     "vision_category.json",        None,        9, 0, 4),
    ("L1b gate",        "vision_uniqueness.json",      None,        10, 6, 6),
]


@pytest.mark.parametrize("label,seed,scope,t0,t1,t2", TABLE)
def test_audit_table_row(label, seed, scope, t0, t1, t2):
    """Every row re-run. T0 and T1 must REPRODUCE the tripwire rung's published numbers."""
    a = audit_seed_file(_seed(seed), scope)
    assert a["T0_any_comparator"] == t0, f"{label}: T0 must reproduce"
    assert a["T1_bound_like"] == t1, f"{label}: T1 must reproduce"
    assert a["T2_bound_like"] == t2, f"{label}: T2"


def test_audit_table_exactly_one_verdict_moves():
    moved = []
    for label, seed, scope, _t0, _t1, _t2 in TABLE:
        a = audit_seed_file(_seed(seed), scope)
        if a["T2_bound_like"] != a["T1_bound_like"]:
            moved.append(label)
    assert moved == ["T2 category"], moved


# ================================================================================
# POSITIVE CONTROLS (§12.3 / process rules 5, 6) — measured, not asserted
# ================================================================================

def _restore(fn):
    A.is_codebook_crossing = fn


def test_positive_control_detect_nothing_reddens_headline_not_fp():
    """A T2 that promotes NOTHING scores a PERFECT false-positive arm — and is caught
    ONLY by the headline arm. This is process rule 5, instantiated."""
    orig = A.is_codebook_crossing
    try:
        A.is_codebook_crossing = lambda node, scope: False
        a = audit_seed_file(_seed("vision_category.json"), "cat_recognize")
        assert a["T2_bound_like"] == 0, "detect-nothing must RED the headline"
        # ...while the FP arm is PERFECT
        sim = audit_seed_file(_seed("shape_decode_loop.json"), None)
        assert sim["T2_bound_like"] == 0, "and scores a perfect FP arm — the trap"
        for _n, _w, tree in _tripwire().nonbound_battery():
            assert not any(c.t2_bound_like for c in comparisons_in(tree))
    finally:
        _restore(orig)
    assert audit_seed_file(_seed("vision_category.json"), "cat_recognize")["T2_bound_like"] == 4


def test_positive_control_detect_everything_reddens_fp_not_headline():
    """A T2 that promotes EVERY `Attr`-vs-`Attr` passes the headline and is caught ONLY
    by the conjunction arm. The mirror image — so the CONJUNCTION is the gate."""
    orig = A.is_codebook_crossing
    try:
        A.is_codebook_crossing = lambda node, scope: (
            A._root_type(node.get("a")) == "Attr" and A._root_type(node.get("b")) == "Attr")
        headline = audit_seed_file(_seed("vision_category.json"), "cat_recognize")
        assert headline["T2_bound_like"] == 4, "detect-everything PASSES the headline"
        sim = audit_seed_file(_seed("shape_decode_loop.json"), None)
        assert sim["T2_bound_like"] == 1, "but REDDENS the conjunction (sd_redecode)"
        hits = [n for n, _w, tree in _tripwire().nonbound_battery()
                if any(c.t2_bound_like for c in comparisons_in(tree))]
        assert hits == ["N3_epoch"], hits
    finally:
        _restore(orig)
    assert audit_seed_file(_seed("shape_decode_loop.json"), None)["T2_bound_like"] == 0


def test_positive_control_detector_source_restored_byte_identical():
    """The injections above are monkeypatches on the module object; the SOURCE FILE is
    never written. Pinned by hash so a future edit cannot silently mutate the detector."""
    import hashlib
    src = open(os.path.join(ROOT, "tools", "term_ast_audit.py"), "rb").read()
    assert hashlib.sha256(src).hexdigest() == DETECTOR_SHA256


# Filled in by the run; asserted so the detector cannot drift unnoticed.
DETECTOR_SHA256 = "a5daa5fc94bbeac83380859f324373f9eca382859b013cadf4b95448e66eecbb"


# ================================================================================
# CLAUDE.md — this rung adds NO agent decision
# ================================================================================

def test_no_agent_decision_added():
    """The detector is static analysis: no substrate import, no graph mutation."""
    src = open(os.path.join(ROOT, "tools", "term_ast_audit.py")).read()
    for forbidden in ("substrate_rs", "add_node", "add_edge", "run_rules", "tick("):
        assert forbidden not in src, forbidden
