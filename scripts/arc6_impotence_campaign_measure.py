#!/usr/bin/env python3
"""A14 — THE IMPOTENCE CAMPAIGN.  Measurement runner.

`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A14, registered BEFORE this
script was written.  A13 built `ax_impotent` (the pool-quantified
`AgendaVerdict{kind:'impotent'}` rule) and named, unbuilt, the question this
script answers: does the loop's impotence CONCENTRATE on one missing
`ExecClass`-adjacent goal kind (arguing for WH4 candidate (b), mint a
capability-acquisition goal) or SPREAD across many (arguing for candidate
(a), a general "I'm stuck" question)?

MEASUREMENT ONLY.  No Python decision beyond which scene to construct next;
every verdict is read via `axe.agenda_verdicts` — the same pure read-off the
adapter already ships.  Every scene is either:
  * a REAL live execution (order-1 and order-N, at most one each — the
    154 IM4 precedent already establishes the synthetic path reproduces
    what a real execution reaches, so this campaign does not re-derive
    that; it uses it),
  * the SAME `headroom_n -> 0` synthetic pool-exit A13 SS7.1 validated
    (never `status -> 'retired'`, which walks into `ax_rearm`), or
  * a real `attach_reply` (the adapter's own testimony-reply translation).
Group 3/4 scenes are explicitly HYPOTHETICAL — reachable only by depleting
goals this system cannot currently retire unaided — and are labelled as such
in the artifact, never conflated with the REAL/natural-trajectory scenes of
groups 1-2.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    PYTHONPATH=runners/dsl/python:. python3 scripts/arc6_impotence_campaign_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_impotence_campaign.json")

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
#  Boot / mechanical helpers — the SAME shape every ARC-6 measurement script
#  in this tree already uses (arc6_impotence_term_measure.py precedent).
# =========================================================================== #
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _engine_sha() -> str:
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    return _sha256(so)


def _coherence_probe(s) -> bool:
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    return a["lst"] != a["tup"]


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
    assert _coherence_probe(s), "VALUE LAYER ABSENT on this engine"
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    if with_magnitude:
        ami.resolve_attrition_keys(s)
        if ladder:
            ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def _leave_pool(s, agid):
    """A13 SS7.1's validated pool-exit path.  NEVER `status -> 'retired'`,
    which walks straight into `ax_rearm`'s guard."""
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            s.set_attr(n, "headroom_n", 0.0)
            return
    raise AssertionError("no such goal: " + agid)


def _agenda_attrs(s):
    return s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]


def _goal_kind(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            return s.node(n)["attrs"].get("kind")
    return None


def _live_winner_kind(s):
    """The kind the loop is CURRENTLY armed on, read the SAME way SEL_AGID
    reads it (order-N when live, order-1 otherwise) — bypassing any already-
    minted AgendaVerdict node, whose nearest_unroutable_* fields are frozen
    at mint time (SS8, item logged below)."""
    at = _agenda_attrs(s)
    sel = at.get("arc_sel_agid") if at.get("mg_sel_agid") is None else at.get("mg_sel_agid")
    return {"sel_agid": sel, "sel_kind": _goal_kind(s, sel) if sel else None,
            "arc_sel_agid": at.get("arc_sel_agid"), "arc_sel_value": at.get("arc_sel_value"),
            "mg_sel_agid": at.get("mg_sel_agid"), "mg_sel_value": at.get("mg_sel_value")}


def _answer_open(s, conditioned=False, cond_kw=None):
    """Reply to every open ArcQuestion.  Mirrors
    `tests/test_arc_executor_migrated.py::answer_open_questions` and
    `scripts/arc6_wire_hands_measure.py::wh2_loop`'s reply step — the SAME
    `attach_reply` translation, no new mechanism."""
    sent = 0
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("answered") == 1.0 or a.get("status") != "open":
            continue
        if conditioned:
            agi.attach_reply(s, n, "worth it while the op table stands", **(cond_kw or {}))
        else:
            agi.attach_reply(s, n, "I do not know either; use your judgement.")
        sent += 1
    return sent


def _verdicts_live(s):
    """Non-stale impotent verdicts, the summary fields the write-up quotes."""
    out = []
    for v in axe.agenda_verdicts(s, "impotent"):
        if v.get("stale") == 1.0:
            continue
        out.append({k: v.get(k) for k in
                    ("epoch", "pool_n", "pool_agids", "exec_classes_held",
                     "nearest_unroutable_agid", "nearest_unroutable_kind")})
    return out


def _snapshot(s, label):
    return {"label": label, "pool": axe.pool(s), "pool_n": len(axe.pool(s)),
            "live_winner": _live_winner_kind(s),
            "verdicts": _verdicts_live(s),
            "n_open_questions": len([q for q in agi.questions(s) if q.get("status") == "open"])}


# =========================================================================== #
#  GROUP 1 — the loop's OWN reachable trajectory.  REAL executions, at most
#  one per collapse, plus the synthetic cross-check that reaching the SAME
#  post-execution pool without a live measurement reads the SAME verdict.
# =========================================================================== #
def group1_real_order1():
    s, ag = _boot(with_magnitude=False)
    s._inner.run_rules()
    before = _snapshot(s, "pre_reply")
    sent = _answer_open(s, conditioned=True, cond_kw=dict(
        cond_kind="fact_equals", cond_filter_value="arc6_structural_ceiling_present",
        cond_expected_str="1"))
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    executed = None
    if pending:
        rec = axe.run_order(s, pending[0], tag="campaign_order1")
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        executed = {"agid": rec.get("agid"), "elapsed_seconds": rec.get("elapsed_seconds")}
    after = _snapshot(s, "post_execution")
    return {"replies_sent": sent, "before": before, "executed": executed, "after": after}


def group1_real_orderN():
    s, ag = _boot(with_magnitude=True, ladder=True)
    s._inner.run_rules()  # SILENT -- no reply, matches WH2's own arm
    before = _snapshot(s, "pre_dispatch")
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    executed = None
    if pending:
        rec = axe.run_order(s, pending[0], tag="campaign_orderN")
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        executed = {"agid": rec.get("agid"), "elapsed_seconds": rec.get("elapsed_seconds")}
    after = _snapshot(s, "post_execution")
    return {"replies_sent": 0, "before": before, "executed": executed, "after": after}


def group1s_synthetic_cross_check():
    """The SAME post-execution pool (AGID gone), reached WITHOUT a live
    measurement, order-1 and order-N.  Cross-checked against group1's REAL
    executions rather than re-running them."""
    out = {}
    for name, with_mag in (("order1", False), ("orderN", True)):
        s, ag = _boot(with_magnitude=with_mag, ladder=True)
        s._inner.run_rules()
        _leave_pool(s, AGID)
        s._inner.run_rules()
        out[name] = _snapshot(s, "synthetic_post_" + name)
    return out


# =========================================================================== #
#  GROUP 2 — testimony REweights the remaining 7-goal pool WITHOUT changing
#  its membership.  A REAL mechanism (attach_reply / gr_move_penalty), chained
#  to see whether nearest_unroutable_kind is stable or keeps moving.
# =========================================================================== #
def group2_testimony_chain(with_magnitude, ladder=True, n_replies=6):
    s, ag = _boot(with_magnitude=with_magnitude, ladder=ladder)
    s._inner.run_rules()
    _leave_pool(s, AGID)
    s._inner.run_rules()
    steps = [dict(_snapshot(s, "reply_0"), replies_sent_this_step=0,
                 pool_agids_sig=sorted(axe.pool(s)))]
    for i in range(1, n_replies + 1):
        sent = _answer_open(s, conditioned=False)
        s._inner.run_rules()
        snap = _snapshot(s, "reply_%d" % i)
        snap["replies_sent_this_step"] = sent
        snap["pool_agids_sig"] = sorted(axe.pool(s))
        steps.append(snap)
        if sent == 0:
            break  # no open question -- the chain has nothing left to answer
    kinds_seen = [st["live_winner"]["sel_kind"] for st in steps]
    return {"steps": steps,
            "pool_signature_constant": len({tuple(st["pool_agids_sig"]) for st in steps}) == 1,
            "live_winner_kind_sequence": kinds_seen,
            "reached_fixed_point": kinds_seen[-1] == kinds_seen[-2] if len(kinds_seen) > 1 else True,
            "n_distinct_kinds_in_chain": len(set(kinds_seen))}


# =========================================================================== #
#  GROUP 3 — HYPOTHETICAL depletion ladder.  These pool compositions are NOT
#  reachable by the loop's own current action (nothing here can retire a
#  supply_blocker or source_claim goal unaided) -- constructed via the SAME
#  headroom_n -> 0 technique to explore the shape of the KIND SPACE beyond
#  the one state this system can currently reach on its own.
# =========================================================================== #
def group3_depletion_ladder():
    steps = []
    removed = [AGID]
    s, ag = _boot(with_magnitude=False)
    s._inner.run_rules()
    for agid in removed:
        _leave_pool(s, agid)
    s._inner.run_rules()
    steps.append(dict(_snapshot(s, "after removing " + str(removed)), removed=list(removed)))

    for nxt in (SB_MSP, SB_BUDGET, SB_MD, SC_B, SC_D, SC_T0):
        removed.append(nxt)
        _leave_pool(s, nxt)
        s._inner.run_rules()
        steps.append(dict(_snapshot(s, "after removing " + str(removed)), removed=list(removed)))

    # final step: remove the very last goal (SC_VL) -> EMPTY pool, not impotent.
    removed.append(SC_VL)
    _leave_pool(s, SC_VL)
    s._inner.run_rules()
    steps.append(dict(_snapshot(s, "EMPTY pool -- done, not impotent"), removed=list(removed)))
    return steps


# =========================================================================== #
#  GROUP 4 — the FOURTH goal kind, 'reported' (self_concern source).  Zero
#  shipped instances; this graph's own ag_mint_self_concern rule (real, not
#  invented) mints one from a directly-added SelfConcern node -- the SAME
#  kind of narrow, mechanism-real poke as headroom_n -> 0, aimed at a
#  different mint source instead of a different attribute.  HYPOTHETICAL in
#  the sense that no shipped seed set currently wires a SelfConcern onto this
#  agent without the separate gap-awareness pipeline.
# =========================================================================== #
def group4_self_concern_kind():
    s, ag = _boot(with_magnitude=False)
    s._inner.run_rules()
    scn = s.add_node("SelfConcern", {"status": "noted", "content": "campaign_probe_concern"})
    s._inner.add_edge_unchecked(ag, "has_self_concern", scn)
    s._inner.run_rules()
    minted = [s.node(n)["attrs"].get("agid") for n in s.nodes("ArcGoal")
             if s.node(n)["attrs"].get("kind") == "reported"]
    natural_pool_snapshot = _snapshot(s, "reported_goal_present_in_full_pool")

    # Deplete everything else so 'reported' is the sole survivor.
    for agid in (AGID, SB_MSP, SB_BUDGET, SB_MD, SC_B, SC_D, SC_T0, SC_VL):
        _leave_pool(s, agid)
    s._inner.run_rules()
    sole_survivor_snapshot = _snapshot(s, "reported_goal_is_the_SOLE_survivor")
    return {"minted_reported_goals": minted,
            "natural_pool_snapshot": natural_pool_snapshot,
            "sole_survivor_snapshot": sole_survivor_snapshot}


# =========================================================================== #
#  TWIN-RUN DETERMINISM (IC1)
# =========================================================================== #
def twin_run_determinism():
    def scene():
        s, _ = _boot(with_magnitude=False)
        s._inner.run_rules()
        _leave_pool(s, AGID)
        s._inner.run_rules()
        return _verdicts_live(s)
    r1, r2 = scene(), scene()
    return {"byte_identical": r1 == r2, "scene": r1}


# =========================================================================== #
#  Aggregation — IC2's concentration/spread statistic.
# =========================================================================== #
def _dedup_by_signature(entries):
    seen, out = set(), []
    for e in entries:
        sig = e.get("pool_agids")
        if sig in seen:
            continue
        seen.add(sig)
        out.append(e)
    return out


def _dedup_by_state(entries):
    """(pool_agids, nearest_unroutable_kind) over the STORED verdict field —
    kept for comparison, but SS8's own finding is that this UNDER-counts:
    see `_live_states` below, which is the corrected view."""
    seen, out = set(), []
    for e in entries:
        key = (e.get("pool_agids"), e.get("nearest_unroutable_kind"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _live_states(snapshots):
    """THE CORRECTED VIEW (SS8, discovered mid-measurement, not registered in
    advance).  `ax_impotent`'s mint-once-by-pool-signature guard means a
    reply that moves the live winner WITHOUT changing pool MEMBERSHIP does
    NOT re-mint -- so the STORED `AgendaVerdict.nearest_unroutable_kind`
    freezes at first-mint and does not track a live ranking that keeps
    moving under a constant signature (measured directly: group 2's chain
    shows the LIVE winner move supply_blocker -> supply_blocker ->
    source_claim while every stored verdict in the same chain still reads
    'supply_blocker').  This walks `_snapshot()`'s own `live_winner.sel_kind`
    (computed the SAME way `SEL_AGID` is defined -- order-N when live, else
    order-1 -- bypassing the frozen node) and dedupes on
    (pool signature, live winner kind), which is the reading that actually
    answers "what does this system currently believe is the nearest missing
    capability" at each distinct scene."""
    seen, out = set(), []
    for snap in snapshots:
        if snap.get("pool_n", 0) == 0:
            continue  # empty pool -- not impotent, not a state to count
        lw = snap.get("live_winner") or {}
        kind = lw.get("sel_kind")
        if kind is None:
            continue
        key = (tuple(sorted(snap.get("pool", []))), kind)
        if key in seen:
            continue
        seen.add(key)
        out.append({"pool_agids": json.dumps(sorted(snap.get("pool", []))),
                    "nearest_unroutable_kind": kind,
                    "nearest_unroutable_agid": lw.get("sel_agid"),
                    "pool_n": snap.get("pool_n"), "label": snap.get("label")})
    return out


def concentration_stat(entries, label):
    if not entries:
        return {"label": label, "n": 0, "modal_kind": None, "fraction": None, "read": "NO_DATA"}
    from collections import Counter
    kinds = [e.get("nearest_unroutable_kind") for e in entries]
    c = Counter(kinds)
    modal_kind, modal_n = c.most_common(1)[0]
    f = modal_n / len(entries)
    if len(entries) < 5:
        read = "AMBIGUOUS_underpowered"
    elif f >= 0.75:
        read = "CONCENTRATED"
    elif f <= 0.50:
        read = "SPREAD"
    else:
        read = "AMBIGUOUS"
    return {"label": label, "n": len(entries), "kind_counts": dict(c),
            "modal_kind": modal_kind, "fraction": round(f, 4), "read": read}


def main():
    print("== group 1: real executions (order-1, order-N) ==", file=sys.stderr)
    g1_o1 = group1_real_order1()
    g1_oN = group1_real_orderN()
    print("== group 1s: synthetic cross-check ==", file=sys.stderr)
    g1s = group1s_synthetic_cross_check()
    print("== group 2: testimony chains ==", file=sys.stderr)
    g2_o1 = group2_testimony_chain(with_magnitude=False)
    g2_oN = group2_testimony_chain(with_magnitude=True, ladder=True)
    print("== group 3: hypothetical depletion ladder ==", file=sys.stderr)
    g3 = group3_depletion_ladder()
    print("== group 4: the 'reported' kind ==", file=sys.stderr)
    g4 = group4_self_concern_kind()
    print("== twin-run determinism ==", file=sys.stderr)
    twin = twin_run_determinism()

    # -------- assemble the sweep set S -----------------------------------
    real_entries = []
    real_entries += g1_o1["after"]["verdicts"]
    real_entries += g1_oN["after"]["verdicts"]
    real_entries += g1s["order1"]["verdicts"]
    real_entries += g1s["orderN"]["verdicts"]
    for st in g2_o1["steps"]:
        real_entries += st["verdicts"]
    for st in g2_oN["steps"]:
        real_entries += st["verdicts"]

    hypothetical_entries = []
    for st in g3:
        hypothetical_entries += st["verdicts"]
    hypothetical_entries += g4["natural_pool_snapshot"]["verdicts"]
    hypothetical_entries += g4["sole_survivor_snapshot"]["verdicts"]

    real_by_sig = _dedup_by_signature(real_entries)
    real_by_state = _dedup_by_state(real_entries)
    all_by_sig = _dedup_by_signature(real_entries + hypothetical_entries)
    all_by_state = _dedup_by_state(real_entries + hypothetical_entries)

    # -------- SS8's corrected view: LIVE winner, not the frozen stored ---
    # verdict field.  Collect every snapshot dict (each carries its own
    # `live_winner`) from the REAL/natural-trajectory groups (1, 1s, 2) and,
    # separately, the HYPOTHETICAL groups (3, 4).
    real_snapshots = ([g1_o1["after"], g1_oN["after"], g1s["order1"], g1s["orderN"]]
                      + g2_o1["steps"] + g2_oN["steps"])
    hypothetical_snapshots = list(g3) + [g4["natural_pool_snapshot"],
                                         g4["sole_survivor_snapshot"]]
    real_live_states = _live_states(real_snapshots)
    all_live_states = _live_states(real_snapshots + hypothetical_snapshots)

    out = {
        "_README": (
            "A14 -- THE IMPOTENCE CAMPAIGN.  Every scene is a LIVE boot + "
            "mutation + run_rules() + read-off; group 1 includes two REAL "
            "live executions (~140s each), everything else is the SAME "
            "headroom_n->0 / attach_reply mechanisms A13/AG-5/WH2 already "
            "used, no live remeasurement.  Groups 3-4 are HYPOTHETICAL "
            "(pool states this system cannot currently reach unaided) and "
            "are reported SEPARATELY from groups 1-2 (REAL/natural-"
            "trajectory).  Bars: PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment "
            "A14."),
        "engine_sha256": _engine_sha(),
        "seed_sha256": _sha256(os.path.join(ROOT, "seeds", "arc_executor.json")),
        "GROUP1_real_executions": {"order1": g1_o1, "orderN": g1_oN},
        "GROUP1s_synthetic_cross_check": g1s,
        "GROUP2_testimony_chains": {"order1": g2_o1, "orderN": g2_oN},
        "GROUP3_hypothetical_depletion_ladder": g3,
        "GROUP4_reported_kind": g4,
        "twin_run_determinism": twin,
        "IC2_concentration_statistics": {
            "real_only__by_pool_signature__AS_REGISTERED":
                concentration_stat(real_by_sig, "real_only_by_signature"),
            "real_only__by_STORED_verdict_kind__STILL_UNDERCOUNTS":
                concentration_stat(real_by_state, "real_only_by_stored_verdict_kind"),
            "real_plus_hypothetical__by_pool_signature__AS_REGISTERED":
                concentration_stat(all_by_sig, "all_by_signature"),
            "real_plus_hypothetical__by_STORED_verdict_kind__STILL_UNDERCOUNTS":
                concentration_stat(all_by_state, "all_by_stored_verdict_kind"),
            "real_only__by_LIVE_winner_state__CORRECTED_see_SS8":
                concentration_stat(real_live_states, "real_only_live_states"),
            "real_plus_hypothetical__by_LIVE_winner_state__CORRECTED_see_SS8":
                concentration_stat(all_live_states, "all_live_states"),
        },
        "SS8_finding_stored_verdict_freezes_at_mint": {
            "explanation": (
                "ax_impotent mints once per POOL SIGNATURE; a reply that "
                "moves the live winner WITHOUT changing pool membership does "
                "NOT re-mint, so the stored AgendaVerdict.nearest_unroutable_"
                "kind freezes at first-mint and does not track further "
                "ranking drift under a constant signature.  Measured "
                "directly in group 2's own chain (both collapses): the LIVE "
                "winner moves supply_blocker -> supply_blocker -> "
                "source_claim while every stored verdict in the SAME chain "
                "still reads 'supply_blocker'.  Not a bug in IM5's own bar "
                "(mint-once-by-signature is exactly what IM5 registered and "
                "gated) -- a previously unmeasured CONSEQUENCE of it, found "
                "by this campaign."),
            "order1_chain_live_winner_kinds": g2_o1["live_winner_kind_sequence"],
            "order1_chain_stored_verdict_kinds":
                [st["verdicts"][0]["nearest_unroutable_kind"] if st["verdicts"] else None
                 for st in g2_o1["steps"]],
            "orderN_chain_live_winner_kinds": g2_oN["live_winner_kind_sequence"],
            "orderN_chain_stored_verdict_kinds":
                [st["verdicts"][0]["nearest_unroutable_kind"] if st["verdicts"] else None
                 for st in g2_oN["steps"]],
        },
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
    print("wrote", OUT)
    print("engine", out["engine_sha256"][:12])
    print("seed  ", out["seed_sha256"][:12])
    print(json.dumps(out["IC2_concentration_statistics"], indent=2, default=str))


if __name__ == "__main__":
    main()
