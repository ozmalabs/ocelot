"""A REPRESENTABLE REFUSAL — the four-way discriminator.

Gates VISION_REFUSAL_REPRESENTABLE_PREREG.md / VISION_REFUSAL_REPRESENTABLE_RESULTS.md.

The finding acted on (VISION_ARGMIN_UNIQUE_RESULTS.md): "`ArgminUnique` can refuse,
and no caller in the seed layer can hear it." At the WTA idiom `Eq(node, sel)` a
refusal is `Bool(false)` — byte-identical to "you are not the winner" AND to "the
source was empty"; and `argmin_or_argmax_over` returns `default` on BOTH the
tie-path AND the empty-path, so even the shared `default` conflates REFUSED with
NOTHING.

This rung makes a refusal HEARABLE: a new additive Term `ArgminRefusal` (index 180)
routes a held `RefusalMark` node to the TIE PATH ONLY (empty stays `None`), so a
consuming rule reads FOUR distinct things — REFUSED (the marker), NO (`Bool(false)`),
NOTHING (`None`), and REAL (a winner node).

The positive control that makes the rest mean something is
`test_positive_control_ArgminUnique_COLLAPSES_the_four_way`: the SAME classifier,
fed the pre-fix mechanism (`ArgminUnique`), MISCLASSIFIES a tie as REAL. A gate that
would pass on the broken mechanism is not a gate.
"""
from __future__ import annotations
import json
import os

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import substrate_rs as srs  # noqa: E402
from substrate_rs import (Term, Var, Attr, Eq, Gt, Not, And, Count, Pick,  # noqa: E402
                          Lit, Argmin)
from substrate_rs.ext import add_rule, run_rules, SetAttr, AddNode  # noqa: E402

CAND, MARK, PROBE, ROOTT = "TRCand", "TRMark", "TRProbe", "TRRoot"
SD_KW = dict(codebook_type="ShapeSignature", beam=4, max_steps=4, cand_k=4, wild="?")


def NodesOfType(t):
    return Term("NodesOfType", node_type=t)


def mark_ref():
    return Pick(NodesOfType(MARK))


def sel_term(kind, refused=None):
    kw = dict(source=NodesOfType(CAND), var_name="c", value=Attr(Var("c"), "score"))
    if kind in ("Argmin", "ArgminUnique"):
        kw["default"] = None
    if kind == "ArgminRefusal":
        kw["refused"] = refused
    return Term(kind, **kw)


def build(scores, with_mark=True):
    s = srs.Substrate()
    root = s.add_node(ROOTT, {})
    probe = s.add_node(PROBE, {})
    s.add_edge_unchecked(root, "asks", probe)
    if with_mark:
        s.add_node(MARK, {"is_refusal_marker": 1})
    for i, v in enumerate(scores):
        s.add_node(CAND, {"score": float(v), "idx": i})
    return s, root, probe


def classify(scores, kind):
    """Install the consuming classifier over `kind` and return the probe verdict.
    The classifier reads the refusal token FIRST (`Eq(sel, mark)`); that single
    extra read is the rule-layer change the ArgminUnique rung said had to come
    first."""
    refused = mark_ref() if kind == "ArgminRefusal" else None
    s, root, probe = build(scores)
    sel = sel_term(kind, refused=refused)
    mark = mark_ref()
    cand_count = Count(NodesOfType(CAND))
    is_refused = Eq(sel, mark)
    add_rule(s, "r_refused", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("REFUSED"))], where=is_refused)
    add_rule(s, "r_nothing", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("NOTHING"))],
             where=And([Not(is_refused), Eq(cand_count, Lit(0))]))
    add_rule(s, "r_real", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("REAL"))],
             where=And([Not(is_refused), Gt(cand_count, Lit(0))]))
    run_rules(s)
    return s.evaluate(Attr(Lit(probe), "verdict"))


TIE = [7.0, 7.0, 7.0, 7.0, 7.0]
EMPTY = []
UNIQUE = [7.0, 7.0, 3.0, 7.0, 7.0]


# --------------------------------------------------------------------------
def test_the_new_term_exists_at_index_180():
    """ArgminRefusal is a real Term (RED by construction on any engine lacking
    index 180 — e.g. the pre-change engine, where it raises UnknownTermType)."""
    s, _, _ = build(TIE)
    out = s.evaluate(sel_term("ArgminRefusal", refused=mark_ref()))
    assert isinstance(out, srs.NodeID)  # the marker, on a tie


def test_four_way_at_a_consuming_rule():
    """A downstream RULE branches DIFFERENTLY on all four cases."""
    assert classify(TIE, "ArgminRefusal") == "REFUSED"
    assert classify(EMPTY, "ArgminRefusal") == "NOTHING"
    assert classify(UNIQUE, "ArgminRefusal") == "REAL"
    # NO: a false comparison, distinct from REFUSED — read WITH the refusal read.
    s, root, probe = build(UNIQUE)
    sel = sel_term("ArgminRefusal", refused=mark_ref())
    non_winner = [c for c in s.evaluate(NodesOfType(CAND))
                  if s.evaluate(Attr(Lit(c), "idx")) == 0][0]
    assert s.evaluate(Eq(sel, mark_ref())) is False          # not REFUSED
    assert s.evaluate(Eq(Lit(non_winner), sel)) is False     # NO — not the winner


def test_positive_control_ArgminUnique_COLLAPSES_the_four_way():
    """THE ARM THE WHOLE GATE RESTS ON. The pre-fix mechanism (`ArgminUnique`,
    which returns None on tie AND on empty) MISCLASSIFIES a tie as REAL, because
    `Eq(None, mark)` is False so the refusal is never heard. If ArgminRefusal
    behaved like ArgminUnique, this gate would pass — so this arm must FAIL for
    ArgminUnique and PASS for ArgminRefusal."""
    # broken mechanism: a tie is indistinguishable from a real winner
    assert classify(TIE, "ArgminUnique") == "REAL"       # WRONG — the collapse
    # fixed mechanism: the same tie is heard as REFUSED
    assert classify(TIE, "ArgminRefusal") == "REFUSED"   # RIGHT
    # and the two mechanisms AGREE on a genuine winner (the fix subtracts only
    # the ambiguous case — it never widens an answer)
    assert classify(UNIQUE, "ArgminUnique") == "REAL"
    assert classify(UNIQUE, "ArgminRefusal") == "REAL"


def test_governing_law_direction_1_selection_never_yields_the_token():
    """A SELECTION over ordinary values can NEVER yield REFUSED; the token
    appears IFF the uniqueness comparison failed (a tie)."""
    s, _, _ = build(UNIQUE)
    mark_node = s.evaluate(mark_ref())
    # over DISTINCT candidates, both plain Argmin and ArgminRefusal return a winner
    assert s.evaluate(sel_term("Argmin")) != mark_node
    assert s.evaluate(sel_term("ArgminRefusal", refused=mark_ref())) != mark_node
    # over a TIE, plain Argmin still returns a winner; ONLY ArgminRefusal refuses
    s2, _, _ = build(TIE)
    m2 = s2.evaluate(mark_ref())
    assert s2.evaluate(sel_term("Argmin")) != m2
    assert s2.evaluate(sel_term("ArgminRefusal", refused=mark_ref())) == m2


def test_governing_law_direction_2_token_distinct_from_none_false_zero():
    """REFUSED is distinct from None AND Bool(false) AND 0 at a Term boundary,
    and is TRUTHY (unlike all three)."""
    s, _, _ = build(UNIQUE)
    tok = mark_ref()
    assert s.evaluate(Eq(tok, Lit(None))) is False
    assert s.evaluate(Eq(tok, Lit(False))) is False
    assert s.evaluate(Eq(tok, Lit(0))) is False
    assert s.evaluate(Term("IfThenElse", cond=tok, then=Lit("t"), other=Lit("f"))) == "t"


def test_pyo3_boundary_a_world_adapter_tells_the_four_apart():
    """Across PyO3, the four results are distinct Python objects; an adapter that
    knows only the RefusalMark node id classifies all four."""
    s, _, _ = build(UNIQUE)
    mark_id = s.evaluate(mark_ref()).value

    def adapter(v):
        if v is None:
            return "NOTHING"
        if v is False:
            return "NO"
        if isinstance(v, srs.NodeID):
            return "REFUSED" if v.value == mark_id else "REAL"
        return f"other:{v!r}"

    s_t, _, _ = build(TIE)
    assert adapter(s_t.evaluate(sel_term("ArgminRefusal", refused=mark_ref()))) == "REFUSED"
    s_e, _, _ = build(EMPTY)
    assert adapter(s_e.evaluate(sel_term("ArgminRefusal", refused=mark_ref()))) == "NOTHING"
    s_u, _, _ = build(UNIQUE)
    assert adapter(s_u.evaluate(sel_term("ArgminRefusal", refused=mark_ref()))) == "REAL"
    c0 = [c for c in s_u.evaluate(NodesOfType(CAND))
          if s_u.evaluate(Attr(Lit(c), "idx")) == 0][0]
    assert adapter(s_u.evaluate(Eq(Lit(c0), sel_term("ArgminRefusal", refused=mark_ref())))) == "NO"


def test_compose_a_shapedecode_wall_lifts_to_the_same_marker():
    """The marker is a GENERAL refusal representation: a WALLED ShapeDecode
    no-match (which erases to a bare None) is LIFTED by a rule to the SAME
    RefusalMark, reaching the consuming rule as REFUSED, not None."""
    s, _, _ = build(TIE)
    mark_node = s.evaluate(mark_ref())
    # the erasure: outside {authored, reason}, a walled ShapeDecode field is None
    assert s.evaluate(Term("ShapeDecode", goal=Lit([]), field="explained", **SD_KW)) is None
    # the lift: read the wall (authored != True) and yield the marker
    lifted = Term("IfThenElse",
                  cond=Not(Eq(Term("ShapeDecode", goal=Lit([]), field="authored", **SD_KW),
                              Lit(True))),
                  then=mark_ref(), other=Lit(None))
    assert s.evaluate(lifted) == mark_node
    # and it COMPOSES with ArgminRefusal's tie token — the SAME refusal value
    assert s.evaluate(Eq(lifted, sel_term("ArgminRefusal", refused=mark_ref()))) is True


def test_seed_hears_a_refusal_and_mints_a_residual():
    """The graph-resident seed: a rule HEARS a refusal (ArgminRefusal tie ==
    RefusalMark) and MINTS a first-class Residual node — in run_rules, no Python
    decision. NOTHING (empty) does NOT mint (the token is not returned on empty)."""
    seed = json.load(open(os.path.join(_ROOT, "seeds", "refusal_representable.json")))

    def scenario(scores):
        s = srs.Substrate()
        summ = s.load_seed_manifest(seed)
        assert summ.get("rules") == 1 and not summ.get("rules_skipped")
        q = s.add_node("RefusalQuery", {})
        p = s.add_node("RefusalProbe", {})
        s.add_edge_unchecked(q, "refusal_probe", p)
        for i, v in enumerate(scores):
            c = s.add_node("RefusalCandidate", {"score": float(v), "idx": i})
            s.add_edge_unchecked(q, "refusal_cand", c)
        run_rules(s)
        return len(s.evaluate(NodesOfType("Residual")))

    assert scenario([7.0] * 5) == 1        # REFUSED -> mint
    assert scenario([7.0, 7.0, 3.0]) == 0  # REAL -> no mint
    assert scenario([]) == 0               # NOTHING -> no mint (not a refusal)


def test_persistence_roundtrip_with_and_without_a_refusal():
    """A graph with a minted Residual (+ the RefusalMark) round-trips
    byte-identically; a graph WITHOUT any refusal machinery is unchanged."""
    def roundtrip_identical(s):
        d1 = s.graph_to_dict()
        s2 = srs.Substrate()
        s2.graph_from_dict(d1)
        d2 = s2.graph_to_dict()
        return (json.dumps(d1, sort_keys=True, default=str)
                == json.dumps(d2, sort_keys=True, default=str))

    seed = json.load(open(os.path.join(_ROOT, "seeds", "refusal_representable.json")))
    s = srs.Substrate()
    s.load_seed_manifest(seed)
    q = s.add_node("RefusalQuery", {})
    p = s.add_node("RefusalProbe", {})
    s.add_edge_unchecked(q, "refusal_probe", p)
    for i, v in enumerate([7.0] * 5):
        c = s.add_node("RefusalCandidate", {"score": float(v), "idx": i})
        s.add_edge_unchecked(q, "refusal_cand", c)
    run_rules(s)
    assert len(s.evaluate(NodesOfType("Residual"))) == 1
    assert roundtrip_identical(s)

    s2, _, _ = build(UNIQUE, with_mark=False)
    assert roundtrip_identical(s2)


def test_ArgminRefusal_is_bound_by_no_OTHER_committed_seed():
    """§9: ArgminRefusal is additive — this rung's seed is the ONLY committed
    seed that binds it, so every committed result reproduces byte-identically."""
    seed_dir = os.path.join(_ROOT, "seeds")
    offenders = []
    for fn in os.listdir(seed_dir):
        if not fn.endswith(".json"):
            continue
        text = open(os.path.join(seed_dir, fn)).read()
        if "ArgminRefusal" in text and fn != "refusal_representable.json":
            offenders.append(fn)
    assert offenders == []
