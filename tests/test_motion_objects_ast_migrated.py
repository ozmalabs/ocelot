"""§13 GATE for `vision_motion_group`: NO MOTION-AGREEMENT CONSTANT ENTERED.

A TERM-TREE AST WALK, never a substring selector. `-k` is a substring match and
a `grep` for a number cannot see a literal that was folded, renamed or moved
into a sibling subtree — PROTOCOL §12, and four failures in this arc, twice red
on their own docstrings.

The claim under test is narrow and is the one the brief places: THE GROUPING
CRITERION contains no hand-set number. The sensor's aperture (`BLOCK`) is a
DECLARED residual and is not covered by this file — it lives in the adapter and
is reported as an unfixed magic number, not hidden here.

Asserted BOTH WAYS ROUND, so a hole in one cannot satisfy the other:
  * every literal in a comparison is compared against a 0/1 FLAG or a phase
    marker — never against a motion quantity;
  * no literal is compared against `v`, `pd`, `mtol`, `mlabel`, `cid`,
    `members`, `disp`, `contrast` or `dom_v`;
  * the tolerance test is STRUCTURALLY a vector read against an attribute, with
    no literal on either side;
  * Otsu's candidates are the OBSERVED nodes themselves.
"""
from __future__ import annotations

import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "vision_motion_group.json")

COMPARISONS = {"Gt", "Lt", "Gte", "Lte", "Eq"}

# 0/1 flags and phase markers. A literal MAY be compared against these — that is
# a flag test, not a threshold on a measured quantity.
FLAGS = {"marm", "mcontrast", "mtol_exact", "mflood",
         "pd_done", "mtol_done", "dom_done"}

# Measured motion quantities. A literal may NEVER be compared against these.
MOTION = {"v", "pd", "mtol", "mlabel", "cid", "members", "disp",
          "contrast", "dom_v", "dom_root"}

# Attributes that hold a WHOLE 2-vector. Both are corroborated by
# `test_dom_v_is_a_whole_vector_not_a_scalar` — this set is not an allowlist
# that can be widened without evidence.
WHOLE_VECTORS = {"v", "dom_v"}


@pytest.fixture(scope="module")
def seed():
    with open(SEED) as fh:
        return json.load(fh)


def walk(node, path=()):
    """Yield every dict node of the term tree with its path."""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + (i,))


def rule_terms(rule):
    """The rule's `where` tree plus every term embedded in its effects."""
    yield rule.get("where")
    for eff in rule.get("effects", []):
        for part in eff:
            if isinstance(part, dict):
                if "__term__" in part:
                    yield part["__term__"]
                else:
                    for v in part.values():
                        if isinstance(v, dict) and "__term__" in v:
                            yield v["__term__"]


def all_terms(seed):
    for rule in seed["rules"]:
        for t in rule_terms(rule):
            if t:
                yield rule["name"], t


def attr_key(side):
    """The attribute key this side of a comparison reads, if it reads one."""
    if isinstance(side, dict) and side.get("type") == "Attr":
        return side.get("key")
    return None


def literal_of(side):
    if isinstance(side, dict) and side.get("type") == "Lit":
        return side.get("value")
    return None


def comparisons(seed):
    for rname, term in all_terms(seed):
        for _, node in walk(term):
            if isinstance(node, dict) and node.get("type") in COMPARISONS:
                yield rname, node


def test_seed_is_master_off_by_default(seed):
    """§9 — defaults preserve committed results."""
    params = [n for n in seed["nodes"] if n["type"] == "MotionParams"]
    assert len(params) == 1
    assert params[0]["attrs"]["marm"] == 0.0


def test_every_literal_in_a_comparison_is_a_flag_test(seed):
    """Forward direction: each literal comparison is against a 0/1 flag."""
    offenders = []
    for rname, node in comparisons(seed):
        for near, far in ((node.get("a"), node.get("b")),
                          (node.get("b"), node.get("a"))):
            if literal_of(near) is None:
                continue
            key = attr_key(far)
            if key is None or key not in FLAGS:
                offenders.append((rname, node.get("type"), key,
                                  literal_of(near)))
    assert offenders == [], (
        "a literal is compared against something that is not a 0/1 flag — "
        "a threshold has entered the grouping criterion: " + repr(offenders))


def test_no_literal_is_compared_against_any_motion_quantity(seed):
    """Reverse direction, so a hole in the forward test cannot satisfy this."""
    offenders = []
    for rname, node in comparisons(seed):
        keys = {attr_key(node.get("a")), attr_key(node.get("b"))}
        lits = {literal_of(node.get("a")), literal_of(node.get("b"))}
        if (keys & MOTION) and any(l is not None for l in lits):
            offenders.append((rname, node.get("type"), sorted(k for k in keys if k)))
    assert offenders == [], (
        "a measured motion quantity is compared against a literal: "
        + repr(offenders))


def test_the_tolerance_test_is_a_vector_read_with_no_literal(seed):
    """The admissibility test is STRUCTURALLY `Magnitude(VecSub(a.v, b.v))`
    against an ATTRIBUTE — located structurally, not by name."""
    found = 0
    for rname, node in comparisons(seed):
        a, b = node.get("a"), node.get("b")
        if not (isinstance(a, dict) and a.get("type") == "Magnitude"):
            continue
        assert a["arg"]["type"] == "VecSub", (
            f"{rname}: the motion difference is not a vector read")
        # A direct vector read of two WHOLE vectors, never two scalar components.
        # `dom_v` is admitted here because it is verifiably a whole vector, not
        # because the gate was widened to make a failure go away: `mo_dominant`
        # assigns it `Attr(R, "v")` verbatim and the adapter initialises it as
        # [0.0, 0.0]. Both facts are asserted below, so this allowance cannot
        # silently come to cover a scalar.
        for side in ("a", "b"):
            operand = a["arg"][side]
            assert operand.get("type") == "Attr", (
                f"{rname}: VecSub operand is not an attribute read: {operand}")
            assert operand.get("key") in WHOLE_VECTORS, (
                f"{rname}: VecSub operand is not a whole vector: {operand}")
        assert literal_of(b) is None, (
            f"{rname}: the tolerance is a LITERAL — §13 violated")
        assert attr_key(b) in ("mtol",), (
            f"{rname}: the tolerance is not read from an attribute: {b}")
        found += 1
    assert found >= 3, (
        f"expected the vector-difference test in the flood, the settled "
        f"predicate and the mint; found {found}")


def test_otsu_candidates_are_the_observed_values_themselves(seed):
    """The split is the `pd` of a cell the graph picked — not a constructed
    candidate ladder and not a percentile."""
    rule = [r for r in seed["rules"] if r["name"] == "mo_tol_otsu"][0]
    argmaxes = [n for _, n in walk(rule["effects"])
                if isinstance(n, dict) and n.get("type") == "Argmax"]
    assert argmaxes, "mo_tol_otsu does not pick a candidate"
    src = argmaxes[0]["source"]
    assert src.get("type") == "NodesOfType" and src.get("node_type") == "MCell", (
        "Otsu's candidates are not the observed cells: " + repr(src))


def test_the_reference_frame_is_an_argmax_not_a_constant(seed):
    """`mo_dominant` picks the LARGEST group. No size constant anywhere."""
    rule = [r for r in seed["rules"] if r["name"] == "mo_dominant"][0]
    argmaxes = [n for _, n in walk(rule["where"])
                if isinstance(n, dict) and n.get("type") == "Argmax"]
    assert argmaxes, "the reference frame is not selected by an Argmax"
    assert any(n.get("type") == "Count"
               for _, n in walk(argmaxes[0]["value"])), (
        "the dominant group is not chosen by member count")


def test_no_rule_reads_a_scalar_motion_component(seed):
    """Motion is a VECTOR MATRIX. If any rule read `vy`/`vx` as separate
    scalars the representation would have been flattened back to per-cell
    numbers — the exact regression the correction warned against."""
    bad = [(rname, node.get("key"))
           for rname, term in all_terms(seed)
           for _, node in walk(term)
           if isinstance(node, dict) and node.get("type") == "Attr"
           and node.get("key") in ("vy", "vx", "v0", "v1")]
    assert bad == [], "a rule reads a scalar motion component: " + repr(bad)


def test_dom_v_is_a_whole_vector_not_a_scalar(seed):
    """Corroborates the WHOLE_VECTORS allowance used above. `dom_v` may be
    treated as a vector ONLY because the seed assigns it a whole `v` and the
    adapter initialises it as a 2-vector. If either changed, the allowance
    would be unearned and this test goes red before the structural one can
    silently pass."""
    rule = [r for r in seed["rules"] if r["name"] == "mo_dominant"][0]
    eff = [e for e in rule["effects"] if e[2] == "dom_v"]
    assert len(eff) == 1, "mo_dominant does not write dom_v exactly once"
    term = eff[0][3]["__term__"]
    assert term == {"type": "Attr", "node": {"type": "Var", "name": "R"},
                    "key": "v"}, (
        "dom_v is not assigned a whole motion vector: " + repr(term))

    adapter = os.path.join(ROOT, "domains", "motion_group_world.py")
    with open(adapter) as fh:
        src = fh.read()
    assert '"dom_v": [0.0, 0.0]' in src, (
        "the adapter no longer initialises dom_v as a 2-vector")
