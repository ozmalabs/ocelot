#!/usr/bin/env python3
"""A REPRESENTABLE REFUSAL — the four-way discriminator.

Pre-registration: VISION_REFUSAL_REPRESENTABLE_PREREG.md.

Four cases must reach a consuming RULE distinctly:
  REFUSED   a comparison matched nothing (a tie)
  NO        a comparison came out false ("you are not the winner")
  NOTHING   an empty/absent source
  REAL      an ordinary result (a Node)

This script measures, in ONE process on ONE reader:
  BASELINE   with ArgminUnique (returns None on tie AND on empty) — the collapse.
  ARM D      with ArgminRefusal + a held RefusalMark node — the four-way.
  ARM G      the governing-law guard, both directions.
  ARM P      the PyO3 boundary: a world adapter tells the four apart.
  ARM C      composition: a walled-ShapeDecode-style refusal lifted to the SAME
             RefusalMark reaches the rule as REFUSED, not None.
  ARM R      persistence: a graph with a minted Residual round-trips byte-identically.

No RNG in the discrimination path — the result is deterministic. Seeds
117000-117001 are used only for the randomised replicate, LITERAL and in-block.
"""
import json
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domains import engine_provenance  # noqa: E402
engine_provenance.engine_preamble()

import substrate_rs as srs  # noqa: E402
from substrate_rs import (Term, Var, Attr, Eq, Gt, Not, And, Count, Pick,  # noqa: E402
                          Lit, Argmin)
from substrate_rs.ext import add_rule, run_rules, SetAttr, AddNode  # noqa: E402

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")

CAND = "R117Cand"      # candidate type, block-namespaced
MARK = "R117Mark"      # the held RefusalMark type
PROBE = "R117Probe"    # the persistent probe node type
ROOTT = "R117Root"


def NodesOfType(t):
    return Term("NodesOfType", node_type=t)


def mark_ref():
    return Pick(NodesOfType(MARK))


def sel_term(kind, refused=None):
    """`kind{ c in NodesOfType(CAND) : Attr(c, score) }`, refused token optional."""
    kw = dict(source=NodesOfType(CAND), var_name="c",
              value=Attr(Var("c"), "score"))
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


# --------------------------------------------------------------------------
# The CONSUMING RULE SET — classify the selection result four ways.
# It reads the refusal token FIRST (Eq(sel, mark)); only then asks the WTA
# question. That single extra read is exactly the rule-layer change the
# ArgminUnique rung said had to come first.
# --------------------------------------------------------------------------
def install_classifier(s, root, sel):
    mark = mark_ref()
    cand_count = Count(NodesOfType(CAND))
    is_refused = Eq(sel, mark)
    # REFUSED: the token came back.
    add_rule(s, "r_refused", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("REFUSED"))],
             where=is_refused)
    # NOTHING: not refused, and the source was empty.
    add_rule(s, "r_nothing", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("NOTHING"))],
             where=And([Not(is_refused), Eq(cand_count, Lit(0))]))
    # REAL: not refused, source non-empty -> sel is a genuine winner node.
    add_rule(s, "r_real", [("rt", "asks", "pb")],
             [SetAttr("pb", "verdict", Lit("REAL")),
              SetAttr("pb", "winner_idx", Attr(sel, "idx"))],
             where=And([Not(is_refused), Gt(cand_count, Lit(0))]))


def _raw_sel(s, sel):
    """The RAW value the selection returns, for the value-level table."""
    try:
        return s.evaluate(sel)
    except Exception as e:  # noqa
        return f"<eval-error: {type(e).__name__}>"


def describe(v):
    """Classify a raw returned Value by its PYTHON type at the boundary."""
    if v is None:
        return "None"
    if v is True or v is False:
        return f"Bool({v})"
    if isinstance(v, srs.NodeID):
        return f"Node({v.value})"
    if isinstance(v, bool):
        return f"Bool({v})"
    if isinstance(v, int):
        return f"Int({v})"
    if isinstance(v, float):
        return f"Float({v})"
    if isinstance(v, str):
        return f"Str({v!r})"
    return f"{type(v).__name__}({v!r})"


def main():
    out = {"provenance": PROV, "loadavg_start": os.getloadavg()}
    print(f"provenance: {PROV}")

    tie = [7.0, 7.0, 7.0, 7.0, 7.0]     # non-unique extremum -> REFUSED
    empty = []                           # empty source        -> NOTHING
    unique = [7.0, 7.0, 3.0, 7.0, 7.0]   # unique min at idx 2 -> REAL

    # ================= BASELINE — the collapse (ArgminUnique) ================
    # ArgminUnique returns None on tie AND on empty; downstream they are the
    # same bytes, and at Eq(node, sel) a refusal is byte-identical to false.
    baseline = {}
    for name, scores in [("tie_REFUSED", tie), ("empty_NOTHING", empty),
                         ("unique_REAL", unique)]:
        s, root, probe = build(scores)
        sel = sel_term("ArgminUnique")
        raw = _raw_sel(s, sel)
        # the WTA idiom: is the FIRST candidate the winner?
        cands = s.evaluate(NodesOfType(CAND))
        first = None
        # deterministic: lowest idx
        # evaluate Eq(first_cand, sel) if a candidate exists
        wta = None
        if cands:
            # pick the candidate with idx 0
            probe_c = _cand_by_idx(s, 0)
            if probe_c is not None:
                wta = s.evaluate(Eq(Lit(probe_c), sel))
        baseline[name] = {"raw_sel": describe(raw),
                          "wta_Eq_firstcand_sel": describe(wta),
                          "attr_score": describe(_attr_of(s, sel, "score"))}
    out["baseline_collapse"] = baseline
    # The collapse assertion: tie and empty are byte-identical at the raw sel
    # AND at the Attr site AND at the WTA Eq site.
    b = baseline
    out["baseline_collapse_holds"] = (
        b["tie_REFUSED"]["raw_sel"] == b["empty_NOTHING"]["raw_sel"] == "None"
        and b["tie_REFUSED"]["attr_score"] == b["empty_NOTHING"]["attr_score"] == "None"
        and b["tie_REFUSED"]["wta_Eq_firstcand_sel"] == "Bool(False)")

    # ================= ARM D — the four-way (ArgminRefusal) =================
    armd = {}
    try:
        for name, scores in [("tie_REFUSED", tie), ("empty_NOTHING", empty),
                             ("unique_REAL", unique)]:
            s, root, probe = build(scores)
            sel = sel_term("ArgminRefusal", refused=mark_ref())
            install_classifier(s, root, sel)
            run_rules(s)
            verdict = _attr_node(s, probe, "verdict")
            raw = _raw_sel(s, sel)
            armd[name] = {"rule_verdict": verdict, "raw_sel": describe(raw)}
        # NO vs YES vs REFUSED — the WTA axis, read WITH the refusal read first.
        armd["NO_vs_YES"] = _no_vs_yes(unique) | {"tie_all_refused": _tie_wta(tie)}
        out["arm_d_fourway"] = armd
        out["arm_d_distinct"] = (
            armd["tie_REFUSED"]["rule_verdict"] == "REFUSED"
            and armd["empty_NOTHING"]["rule_verdict"] == "NOTHING"
            and armd["unique_REAL"]["rule_verdict"] == "REAL"
            and armd["tie_REFUSED"]["raw_sel"].startswith("Node(")
            and armd["empty_NOTHING"]["raw_sel"] == "None"
            and armd["unique_REAL"]["raw_sel"].startswith("Node("))
    except Exception as e:  # noqa
        out["arm_d_fourway"] = {"error": f"{type(e).__name__}: {e}"}
        out["arm_d_distinct"] = None

    # ================= ARM G — the governing law, both directions ==========
    try:
        out["arm_g"] = _governing_law(tie, unique)
    except Exception as e:  # noqa
        out["arm_g"] = {"error": f"{type(e).__name__}: {e}"}

    # ================= ARM P — the PyO3 boundary ============================
    try:
        out["arm_p_pyo3"] = _pyo3_boundary(tie, empty, unique)
    except Exception as e:  # noqa
        out["arm_p_pyo3"] = {"error": f"{type(e).__name__}: {e}"}

    # ================= ARM C — composition (ShapeDecode wall lifted) ========
    try:
        out["arm_c_compose"] = _compose(tie)
    except Exception as e:  # noqa
        out["arm_c_compose"] = {"error": f"{type(e).__name__}: {e}"}

    # ================= HEAR + MINT — a rule mints a Residual on REFUSED =====
    try:
        out["arm_mint_residual"] = _hear_and_mint(tie, unique)
    except Exception as e:  # noqa
        out["arm_mint_residual"] = {"error": f"{type(e).__name__}: {e}"}

    # ================= ARM R — persistence round-trip ======================
    try:
        out["arm_r_persistence"] = _persistence(tie, unique)
    except Exception as e:  # noqa
        out["arm_r_persistence"] = {"error": f"{type(e).__name__}: {e}"}

    # ================= REPLICATE — randomised, in-block seeds ===============
    try:
        out["replicate"] = _replicate()
    except Exception as e:  # noqa
        out["replicate"] = {"error": f"{type(e).__name__}: {e}"}

    out["loadavg_end"] = os.getloadavg()
    print(json.dumps(out, indent=2, default=str))
    dest = ROOT / "results" / "refusal_representable.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {dest}")


# ---- small readers -------------------------------------------------------
def _cand_by_idx(s, idx):
    cands = s.evaluate(NodesOfType(CAND))
    for c in cands:
        if s.evaluate(Attr(Lit(c), "idx")) == idx:
            return c
    return None


def _attr_of(s, sel, key):
    return s.evaluate(Attr(sel, key))


def _attr_node(s, node, key):
    return s.evaluate(Attr(Lit(node), key))


def _no_vs_yes(scores):
    """Within a unique-winner scene, per-candidate WTA verdict read WITH the
    refusal read first. Winner -> YES; others -> NO; none -> REFUSED."""
    s, root, probe = build(scores)
    mark = mark_ref()
    sel = sel_term("ArgminRefusal", refused=mark)
    verdicts = {}
    for c in s.evaluate(NodesOfType(CAND)):
        idx = s.evaluate(Attr(Lit(c), "idx"))
        is_ref = s.evaluate(Eq(sel, mark))
        is_win = s.evaluate(Eq(Lit(c), sel))
        verdicts[idx] = "REFUSED" if is_ref else ("YES" if is_win else "NO")
    return {"per_candidate": verdicts}


def _tie_wta(scores):
    """Under a TIE, every candidate's WTA verdict — must be REFUSED, never NO.
    This is the ArgminUnique-rung collapse, now separated."""
    s, root, probe = build(scores)
    mark = mark_ref()
    sel = sel_term("ArgminRefusal", refused=mark)
    old_style, new_style = {}, {}
    for c in s.evaluate(NodesOfType(CAND)):
        idx = s.evaluate(Attr(Lit(c), "idx"))
        # OLD idiom (Eq(cand, ArgminUnique)) — a tie reads False = "not winner".
        au = sel_term("ArgminUnique")
        old_style[idx] = describe(s.evaluate(Eq(Lit(c), au)))
        # NEW: read the refusal first.
        is_ref = s.evaluate(Eq(sel, mark))
        is_win = s.evaluate(Eq(Lit(c), sel))
        new_style[idx] = "REFUSED" if is_ref else ("YES" if is_win else "NO")
    return {"old_idiom_Eq_cand_ArgminUnique": old_style,
            "new_with_refusal_read_first": new_style}


def _governing_law(tie, unique):
    g = {}
    s, root, probe = build(unique)
    mark = mark_ref()
    mark_node = s.evaluate(mark)
    # direction 1: a SELECTION over ordinary DISTINCT values never yields the token.
    plain_argmin = s.evaluate(sel_term("Argmin"))              # a real winner
    refusal_on_unique = s.evaluate(sel_term("ArgminRefusal", refused=mark))
    g["dir1_plain_argmin_over_distinct"] = describe(plain_argmin)
    g["dir1_argminrefusal_over_distinct"] = describe(refusal_on_unique)
    g["dir1_neither_is_the_token"] = (
        describe(plain_argmin) != describe(mark_node)
        and describe(refusal_on_unique) != describe(mark_node))
    # the token appears IFF the uniqueness comparison failed (a tie):
    s2, _, _ = build(tie)
    mark2 = mark_ref()
    token_on_tie = s2.evaluate(sel_term("ArgminRefusal", refused=mark2))
    plain_on_tie = s2.evaluate(sel_term("Argmin"))            # a winner, no refusal
    g["dir1_token_on_tie"] = describe(token_on_tie)
    g["dir1_plain_argmin_on_tie"] = describe(plain_on_tie)
    g["dir1_token_ONLY_on_tie"] = (
        describe(token_on_tie) == describe(s2.evaluate(mark2))
        and describe(plain_on_tie) != describe(s2.evaluate(mark2)))
    # direction 2: the token is distinct from None, false, 0 at a Term boundary.
    tok = mark_ref()
    g["dir2_eq_token_none"] = describe(s.evaluate(Eq(tok, Lit(None))))
    g["dir2_eq_token_false"] = describe(s.evaluate(Eq(tok, Lit(False))))
    g["dir2_eq_token_zero"] = describe(s.evaluate(Eq(tok, Lit(0))))
    # truthy: a node is truthy, unlike None/false/0.
    g["dir2_token_truthy_via_ifthenelse"] = describe(
        s.evaluate(Term("IfThenElse", cond=tok, then=Lit("truthy"),
                        other=Lit("falsy"))))
    g["dir2_all_distinct"] = (
        g["dir2_eq_token_none"] == "Bool(False)"
        and g["dir2_eq_token_false"] == "Bool(False)"
        and g["dir2_eq_token_zero"] == "Bool(False)"
        and g["dir2_token_truthy_via_ifthenelse"] == "Str('truthy')")
    return g


def _pyo3_boundary(tie, empty, unique):
    """A world adapter reads the four results across PyO3 and tells them apart
    with NO knowledge beyond the RefusalMark node id."""
    s, root, probe = build(unique)
    mark_node = s.evaluate(mark_ref())          # the adapter learns this once
    mark_id = mark_node.value

    def adapter_classify(v):
        # the ONLY thing the adapter knows: which node id is the marker.
        if v is None:
            return "NOTHING"
        if v is False:
            return "NO"
        if isinstance(v, srs.NodeID):
            return "REFUSED" if v.value == mark_id else "REAL"
        return f"other:{describe(v)}"

    results = {}
    s_tie, _, _ = build(tie)
    results["REFUSED"] = adapter_classify(
        s_tie.evaluate(sel_term("ArgminRefusal", refused=mark_ref())))
    s_e, _, _ = build(empty)
    results["NOTHING"] = adapter_classify(
        s_e.evaluate(sel_term("ArgminRefusal", refused=mark_ref())))
    s_u, ru, pu = build(unique)
    results["REAL"] = adapter_classify(
        s_u.evaluate(sel_term("ArgminRefusal", refused=mark_ref())))
    # NO: a false comparison at the boundary.
    c0 = _cand_by_idx(s_u, 0)  # idx 0 has score 7, not the min -> not winner
    results["NO"] = adapter_classify(
        s_u.evaluate(Eq(Lit(c0), sel_term("ArgminRefusal", refused=mark_ref()))))
    all_distinct = (results["REFUSED"] == "REFUSED" and results["NOTHING"] == "NOTHING"
                    and results["REAL"] == "REAL" and results["NO"] == "NO")
    return {"adapter_verdicts": results, "all_four_distinct_across_pyo3": all_distinct}


SD_KW = dict(codebook_type="ShapeSignature", beam=4, max_steps=4, cand_k=4, wild="?")


def _compose(tie):
    """A WALLED ShapeDecode no-match is LIFTED to the SAME RefusalMark, so it
    reaches a consuming rule as REFUSED, not as the bare `None` it erases to
    today. This shows the marker is a GENERAL refusal representation, not one
    bound to ArgminRefusal."""
    s, root, probe = build(tie)
    mark = mark_ref()
    mark_node = s.evaluate(mark)
    # The erasure the refusal-capacity rung measured: outside {authored, reason}
    # every ShapeDecode field on a wall is a bare None.
    sd_explained = s.evaluate(Term("ShapeDecode", goal=Lit([]), field="explained", **SD_KW))
    sd_authored = s.evaluate(Term("ShapeDecode", goal=Lit([]), field="authored", **SD_KW))
    # The LIFT: a rule reads the wall (authored != True) and yields the marker.
    lifted = Term("IfThenElse",
                  cond=Not(Eq(Term("ShapeDecode", goal=Lit([]), field="authored", **SD_KW),
                              Lit(True))),
                  then=mark, other=Lit(None))
    lifted_v = s.evaluate(lifted)
    # And ArgminRefusal's tie yields the SAME token — they COMPOSE.
    tie_tok = s.evaluate(sel_term("ArgminRefusal", refused=mark_ref()))
    same_token = s.evaluate(Eq(lifted, sel_term("ArgminRefusal", refused=mark_ref())))
    return {
        "walled_shapedecode_explained_ERASED_to": describe(sd_explained),
        "walled_shapedecode_authored": describe(sd_authored),
        "lifted_to_marker": describe(lifted_v),
        "argminrefusal_tie_token": describe(tie_tok),
        "both_refusals_are_the_SAME_token": bool(same_token) is True,
        "shapedecode_wall_reaches_rule_as_REFUSED_not_None": (
            describe(lifted_v) == describe(mark_node)
            and describe(sd_explained) == "None"),
    }


def _hear_and_mint(tie, unique):
    """A rule HEARS a refusal and MINTS a first-class `Residual` graph node from
    it — the object the promote/ground spine (SelfConcern -> StandingConcern ->
    teacher) would carry. The PROMOTE/GROUND closure is the NAMED successor; this
    shows only HEAR + MINT."""
    out = {}
    for name, scores, expect in [("tie", tie, True), ("unique", unique, False)]:
        s, root, probe = build(scores)
        mark = mark_ref()
        sel = sel_term("ArgminRefusal", refused=mark)
        # THE RULE: on REFUSED, mint a Residual node carrying the payload and
        # link it to the query root. This is a real rule EFFECT firing in
        # run_rules, not a Python decision.
        add_rule(s, "mint_residual_on_refusal",
                 [("rt", "asks", "pb")],
                 [AddNode("res", "R117Residual",
                          {"source_count": Count(NodesOfType(CAND)),
                           "kind": Lit("no_unique_extremum")}),
                  SetAttr("res", "from_probe", Var("pb"))],
                 where=Eq(sel, mark))
        run_rules(s)
        residuals = s.evaluate(NodesOfType("R117Residual"))
        out[name] = {"minted_residual_count": len(residuals),
                     "expected_mint": expect}
    out["hear_and_mint_correct"] = (
        out["tie"]["minted_residual_count"] == 1
        and out["unique"]["minted_residual_count"] == 0)
    return out


def _persistence(tie, unique):
    """A graph containing a REFUSED-minted Residual round-trips byte-identically
    through graph_to_dict/graph_from_dict; a graph WITHOUT one is unchanged."""
    import json as _json

    def roundtrip_identical(s):
        d1 = s.graph_to_dict()
        s2 = srs.Substrate()
        s2.graph_from_dict(d1)
        d2 = s2.graph_to_dict()
        return (_json.dumps(d1, sort_keys=True, default=str)
                == _json.dumps(d2, sort_keys=True, default=str)), d1

    # (a) a graph WITH a minted Residual (and the RefusalMark node)
    s, root, probe = build(tie)
    mark = mark_ref()
    sel = sel_term("ArgminRefusal", refused=mark)
    add_rule(s, "mint_residual_on_refusal", [("rt", "asks", "pb")],
             [AddNode("res", "R117Residual",
                      {"source_count": Count(NodesOfType(CAND)),
                       "kind": Lit("no_unique_extremum")})],
             where=Eq(sel, mark))
    run_rules(s)
    with_ok, d_with = roundtrip_identical(s)
    has_residual = len(s.evaluate(NodesOfType("R117Residual"))) == 1
    has_mark = len(s.evaluate(NodesOfType(MARK))) == 1

    # (b) a graph WITHOUT any refusal machinery (unique winner, no mint)
    s2, _, _ = build(unique, with_mark=False)
    without_ok, _ = roundtrip_identical(s2)

    return {"graph_with_residual_roundtrips_identical": with_ok,
            "residual_present": has_residual,
            "refusal_marker_present": has_mark,
            "graph_without_refusal_roundtrips_identical": without_ok}


def _classify_rule(scores):
    """The consuming rule-set's verdict on the probe, for a score-set."""
    s, root, probe = build(scores)
    sel = sel_term("ArgminRefusal", refused=mark_ref())
    install_classifier(s, root, sel)
    run_rules(s)
    return _attr_node(s, probe, "verdict")


def _replicate():
    """RANDOMISED replicate over seeds 117000-117049 (LITERAL, in-block). For
    each seed: a random TIE set must classify REFUSED; a random DISTINCT set must
    classify REAL; the empty set NOTHING. The four-way is deterministic per case,
    so this varies the DATA, not the discrimination."""
    import numpy as np
    seeds = list(range(117000, 117050))   # literal elements of block 117000-117999
    refused_ok = real_ok = nothing_ok = 0
    for sd in seeds:
        rng = np.random.default_rng(sd)
        n = int(rng.integers(2, 8))
        v = float(rng.integers(0, 5))
        tie_set = [v] * n                                     # non-unique -> REFUSED
        # a distinct set with a strict unique minimum
        distinct = sorted(set(rng.integers(0, 1000, size=n).tolist()))
        while len(distinct) < 2:
            distinct = sorted(set(rng.integers(0, 1000, size=n + 2).tolist()))
        distinct = [float(x) for x in distinct]               # unique min -> REAL
        if _classify_rule(tie_set) == "REFUSED":
            refused_ok += 1
        if _classify_rule(distinct) == "REAL":
            real_ok += 1
        if _classify_rule([]) == "NOTHING":
            nothing_ok += 1
    n = len(seeds)
    return {"seeds": [seeds[0], seeds[-1]], "n": n,
            "tie_classified_REFUSED": f"{refused_ok}/{n}",
            "distinct_classified_REAL": f"{real_ok}/{n}",
            "empty_classified_NOTHING": f"{nothing_ok}/{n}",
            "all_perfect": refused_ok == real_ok == nothing_ok == n}


if __name__ == "__main__":
    main()
