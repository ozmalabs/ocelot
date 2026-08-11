#!/usr/bin/env python3
"""A20 -- `ag_ask` AND `ax_dispatch` READING DIFFERENT COLLAPSES, IN GENERAL.

`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A20 (AR20a-AR20d), registered
BEFORE this script was written.  WIRE_HANDS SS8 item 4 named the gap and did
not build against it; the impotence campaign's own SS9 item 3 restated it.
This is a MEASUREMENT script first (AR20a characterization + AR20b
adversarial probe) -- whether anything gets built is AR20c's call, decided
AFTER these numbers exist, per the registered GO/NO-GO.

MEASUREMENT ONLY.  No Python decision beyond which scene to construct next --
every verdict is a live graph read (`s.node(...)['attrs']`, or, for the
ranking tables that make the STRUCTURAL BOUND (SS3 below) legible,
`s._inner.evaluate(term, bindings)` over the SHIPPED `mg_select_margin` Term
read straight off the regenerated seed -- the exact same diagnostic pattern
`tests/test_arc_magnitude_migrated.py::_rank` already uses in a GATE, not a
new decision path).  Every scene construction technique is one this arc has
already used and named real: `_leave_pool` (A13 SS7.1's validated
headroom_n->0 pool-exit), `attach_reply` / `attach_constraint_reply` (the
adapter's own testimony/constraint translation), depletion sweeps (A14's
`group3_depletion_ladder` shape).

Writes `results/arc6_ask_dispatch_safety.json`.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_ask_dispatch_safety.json")

RID = "arc6.verdict.row_verdict_seed_only"
AGID = "arc.remeasure." + RID
SB_MSP = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"
SB_BUDGET = "arc.supply.arc6.seam_a.import_oracle.budget"
SB_MD = "arc.supply.arc6.seam_a.import_oracle.missing_dimension"
SC_B = "arc6.claim.seam_b_signature_39_of_257"
SC_D = "arc6.claim.seam_d_verbatim_35_of_36"
SC_T0 = "arc6.claim.tier0_hs1_0_of_10"
SC_VL = "arc6.claim.valuelayer_supersedes_row_verdict"
ALL_EIGHT = [AGID, SB_MSP, SB_BUDGET, SB_MD, SC_B, SC_D, SC_T0, SC_VL]


# =========================================================================== #
#  Boot / mechanical helpers -- the SAME shape every ARC-6 measurement script
#  in this tree already uses (silent_fallback / impotence_campaign precedent).
# =========================================================================== #
def _assert_engine_coherent(s):
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], "VALUE LAYER ABSENT"


def _boot(with_magnitude: bool, ladder: bool = True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    sids = ["program_synthesis", "goal_residuals", "arc_goals"]
    if with_magnitude:
        sids.append("arc_magnitude")
    sids.append("arc_executor")
    for sid in sids:
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    _assert_engine_coherent(s)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    if with_magnitude:
        ami.resolve_attrition_keys(s)
        if ladder:
            ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def _leave_pool(s, goal_agid):
    """A13 SS7.1's validated pool-exit path.  NEVER `status -> 'retired'`,
    which walks straight into `ax_rearm`'s guard."""
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == goal_agid:
            s.set_attr(n, "headroom_n", 0.0)
            return
    raise AssertionError("no such goal: " + goal_agid)


def _agenda(s):
    return s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]


def _abc(s):
    """A = ag_ask's WINNER candidate (arc_sel_agid, order-1).
    B = ag_ask's OTHER candidate (arc_sel_runner_up_agid, order-1).
    C = ax_dispatch's ACTUAL target (SEL_AGID() -- mg_sel_agid when live,
        arc_sel_agid otherwise; read the SAME way the executor seed's own
        SEL_AGID() Term does, off the two stamps, never re-derived)."""
    at = _agenda(s)
    a, b = at.get("arc_sel_agid"), at.get("arc_sel_runner_up_agid")
    c = at.get("mg_sel_agid") if at.get("mg_sel_agid") is not None else a
    return {
        "A_arc_sel_agid": a, "B_arc_sel_runner_up_agid": b,
        "C_dispatch_target": c,
        "arc_sel_margin": at.get("arc_sel_margin"),
        "mg_sel_agid_raw": at.get("mg_sel_agid"),
        "mg_sel_margin": at.get("mg_sel_margin"),
        "collapses_disagree": a != c,
        "C_in_AB": c in (a, b),
        "ask_would_fire_this_tick": (
            at.get("arc_sel_margin") is not None
            #  ArcAskPolicy.margin_threshold, seeds/arc_goals.json -- read as
            #  a literal here ONLY for this diagnostic field's own display;
            #  every gating comparison elsewhere in this script and in the
            #  seed reads the graph's own stamps, never this constant.
            and float(at.get("arc_sel_margin")) < 5.0
        ),
    }


def _answer_open(s, conditioned=False):
    sent = 0
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("answered") == 1.0 or a.get("status") != "open":
            continue
        if conditioned:
            agi.attach_reply(s, n, "worth it while the op table stands",
                             cond_kind="fact_equals",
                             cond_filter_value="arc6_structural_ceiling_present",
                             cond_expected_str="1")
        else:
            agi.attach_reply(s, n, "I do not know either; use your judgement.")
        sent += 1
    return sent


def _open_question_text(s):
    out = []
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("status") != "open":
            continue
        for m in s.nodes("Message"):
            ma = s.node(m)["attrs"]
            if ma.get("kind") == "arc_question":
                out.append({"agid_a": a.get("agid_a"), "agid_b": a.get("agid_b"),
                           "text": ma.get("text")})
    return out


def _orders(s):
    return [dict(s.node(n)["attrs"], _id=str(n)) for n in s.nodes("ExecOrder")]


# =========================================================================== #
#  AR20a(i) -- reproduce WH1's shipped-boot divergence as this rung's own
#  starting measurement (not re-quoted from the prior write-up).
# =========================================================================== #
def shipped_boot():
    s, _ = _boot(with_magnitude=True, ladder=True)
    s._inner.run_rules()
    abc = _abc(s)
    abc["open_questions"] = _open_question_text(s)
    axe.arm(s)
    s._inner.run_rules()
    abc["orders_after_dispatch"] = [
        {"agid": o["agid"], "selected_by": o.get("selected_by")}
        for o in _orders(s)]
    return abc


# =========================================================================== #
#  AR20a(ii) -- the depletion sweep, both collapses read at EVERY step, and
#  the structural bound C_in_AB checked at every step (A14's group3 shape).
# =========================================================================== #
def depletion_sweep(ladder=True):
    steps = []
    removed = []
    s, _ = _boot(with_magnitude=True, ladder=ladder)
    s._inner.run_rules()
    steps.append(dict(_abc(s), removed=list(removed), pool_n=len(axe.pool(s))))
    for nxt in (SB_MSP, AGID, SB_BUDGET, SB_MD, SC_B, SC_D, SC_T0):
        removed.append(nxt)
        _leave_pool(s, nxt)
        s._inner.run_rules()
        steps.append(dict(_abc(s), removed=list(removed), pool_n=len(axe.pool(s))))
    return steps


# =========================================================================== #
#  AR20a(iii) -- channel (b), the scope charge, exercised via the REAL
#  ArcConstraintQuestion / attach_constraint_reply mechanism, not a hand-set
#  attr.  Reports the exact VALUE_N ranking (the shipped `mg_select_margin`
#  Term, read via `s._inner.evaluate` -- the `_rank` diagnostic
#  `test_arc_magnitude_migrated.py` already uses in a GATE) so the margin
#  between "the bound holds" and "the bound breaks" is a number, not a claim.
# =========================================================================== #
def _vn_term():
    with open(os.path.join(ROOT, "seeds", "arc_magnitude.json")) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == "mg_select_margin":
            return r["effects"][0][3]["__term__"]
    raise AssertionError("mg_select_margin missing")


def _full_rank(s, term):
    rows = []
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        rows.append((float(s._inner.evaluate(term, {"mh": n})), a["agid"]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return [{"agid": agid, "value_n": round(v, 4)} for v, agid in rows]


def scope_charge_adversarial():
    """The MOST adversarial single-lever scene this campaign could construct:
    a scope constraint that exempts a currently-buried goal (SB_BUDGET) while
    charging every other non-exempt goal -- INCLUDING the goal ax_dispatch is
    about to act on (AGID/`row_verdict`) -- w_out_of_scope (25.0).  If any
    single scope declaration can ever make C a genuine THIRD goal (neither A
    nor B), this is the shot most likely to do it: it targets B specifically,
    it is real (through `attach_constraint_reply`, not a hand-set attr), and
    it is the ONLY other repricing channel besides the tier ladder (design
    item 2 of the amendment)."""
    s, _ = _boot(with_magnitude=True, ladder=True)
    s._inner.run_rules()
    vn = _vn_term()
    before = {
        "abc": _abc(s),
        "full_rank_value_n": _full_rank(s, vn),
    }
    qs = list(s.nodes("ArcConstraintQuestion"))
    assert qs, "no ArcConstraintQuestion to answer -- mg_ask_constraints did not fire"
    ami.attach_constraint_reply(s, qs[0], "only the budget seam is in scope",
                                con_kind="scope", scope_seam="budget")
    for _ in range(3):
        s._inner.run_rules()
    after = {
        "abc": _abc(s),
        "full_rank_value_n": _full_rank(s, vn),
        "out_of_scope": {s.node(n)["attrs"]["agid"]: s.node(n)["attrs"].get("out_of_scope")
                         for n in s.nodes("ArcGoal")},
    }
    #  The quantitative margin: how far AGID's OWN dominance over the
    #  strongest exempted alternative (SB_BUDGET, uncharged) exceeds the
    #  charge weight itself -- the number that decides whether this channel
    #  CAN break the C-in-{A,B} bound under the CURRENT authored policy.
    b4 = {r["agid"]: r["value_n"] for r in before["full_rank_value_n"]}
    dominance_margin = round(b4[AGID] - b4[SB_BUDGET], 4)
    return {"before": before, "after": after,
            "dominance_margin_AGID_over_SB_BUDGET": dominance_margin,
            "w_out_of_scope": 25.0,
            "bound_would_break_if_w_out_of_scope_exceeded": dominance_margin,
            "bound_held": after["abc"]["C_in_AB"]}


# =========================================================================== #
#  AR20b -- THE ADVERSARIAL SCENE.  A human replies to `ag_ask`'s literal
#  rendered question and we measure whether the reply has ANY causal path to
#  what `ax_dispatch` acts on -- on the shipped boot, where C == B (the
#  runner-up ag_ask itself named), the sharpest test of "does answering
#  change what executes."
# =========================================================================== #
def adversarial_reply_scene():
    s, _ = _boot(with_magnitude=True, ladder=True)
    s._inner.run_rules()
    before = _abc(s)
    question_text = _open_question_text(s)
    #  Snapshot what WOULD dispatch if nobody ever replied (the WH2 control).
    s_control, _ = _boot(with_magnitude=True, ladder=True)
    s_control._inner.run_rules()
    axe.arm(s_control)
    s_control._inner.run_rules()
    control_orders = [{"agid": o["agid"], "selected_by": o.get("selected_by")}
                      for o in _orders(s_control)]

    #  Now reply to the SAME question (unconditioned -- AG-5's own "any
    #  answer penalises the region it is about" arm) BEFORE arming, exactly
    #  the window in which a human's answer, if it were going to matter to
    #  what dispatches, would have to matter.
    sent = _answer_open(s, conditioned=False)
    s._inner.run_rules()
    after_reply = _abc(s)
    axe.arm(s)
    s._inner.run_rules()
    replied_orders = [{"agid": o["agid"], "selected_by": o.get("selected_by")}
                      for o in _orders(s)]

    return {
        "before_reply": before,
        "question_rendered_to_the_human": question_text,
        "replies_sent": sent,
        "after_reply_before_dispatch": after_reply,
        "mg_sel_agid_moved": before["C_dispatch_target"] != after_reply["C_dispatch_target"],
        "control_orders_NO_reply_ever_sent": control_orders,
        "orders_AFTER_a_reply_was_sent": replied_orders,
        "dispatched_goal_unchanged_by_the_reply": (
            [o["agid"] for o in control_orders] == [o["agid"] for o in replied_orders]),
        "reading": (
            "the reply was about A (arc_sel_agid); the dispatched goal is C "
            "(mg_sel_agid); C's own signature region does not match A's, so "
            "the shared PENALTY term the reply writes through cannot reach C "
            "-- reported as a measured fact below (region comparison), not "
            "argued from the mechanism alone."),
    }


def region_of(s, agid):
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        if a.get("agid") == agid:
            return {"sig_seam": a.get("sig_seam"), "sig_lever": a.get("sig_lever"),
                    "sig_target": a.get("sig_target")}
    return None


# =========================================================================== #
#  Twin-run determinism.
# =========================================================================== #
def twin_run_determinism():
    def scene():
        s, _ = _boot(with_magnitude=True, ladder=True)
        s._inner.run_rules()
        return _abc(s)
    r1, r2 = scene(), scene()
    return {"byte_identical": r1 == r2, "scene": r1}


def main():
    t0 = time.time()
    out = {"engine_provenance": provenance_stamp(),
           "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    out["AR20a_shipped_boot"] = shipped_boot()
    out["AR20a_depletion_sweep_ladder"] = depletion_sweep(ladder=True)
    out["AR20a_depletion_sweep_no_ladder"] = depletion_sweep(ladder=False)
    out["AR20a_scope_channel_adversarial"] = scope_charge_adversarial()

    #  The structural-bound check, over EVERY step of EVERY sweep collected
    #  above -- a table a reader can re-derive the summary from, not a claim.
    all_steps = (out["AR20a_depletion_sweep_ladder"]
                + out["AR20a_depletion_sweep_no_ladder"]
                + [out["AR20a_shipped_boot"]])
    out["AR20a_structural_bound_summary"] = {
        "n_steps_checked": len(all_steps),
        "n_steps_C_in_AB": sum(1 for st in all_steps if st.get("C_in_AB")),
        "n_steps_disagree": sum(1 for st in all_steps if st.get("collapses_disagree")),
        "bound_held_every_step": all(st.get("C_in_AB") for st in all_steps),
    }

    out["AR20b_adversarial_reply_scene"] = adversarial_reply_scene()
    s_regions, _ = _boot(with_magnitude=True, ladder=True)
    s_regions._inner.run_rules()
    ab = _abc(s_regions)
    out["AR20b_region_comparison"] = {
        "region_A": region_of(s_regions, ab["A_arc_sel_agid"]),
        "region_C": region_of(s_regions, ab["C_dispatch_target"]),
        "regions_match": region_of(s_regions, ab["A_arc_sel_agid"])
                         == region_of(s_regions, ab["C_dispatch_target"]),
    }

    out["twin_run_determinism"] = twin_run_determinism()

    out["elapsed_seconds"] = round(time.time() - t0, 2)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=False, default=str)
    print(json.dumps(out, indent=2, sort_keys=False, default=str))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
