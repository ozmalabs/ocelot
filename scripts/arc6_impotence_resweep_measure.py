#!/usr/bin/env python3
"""A22 — THE IMPOTENCE RE-SWEEP.  Measurement runner.

`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A22, registered BEFORE this
script was written.  A14 measured real-only n=2 (NO-GO for both candidate
(a) and (b), purely on power).  A15 added a second `ExecClass` and checked,
explicitly, that it does not grow real-only n (the final impotent
composition it settles into is identical to A14's own state 1).  A17 built
`mg_tier_retire` -- a real retirement mechanism for a FIFTH ArcGoal kind
(`decomposition_tier`, A16's own MG4 output) -- and named, but did not
measure, whether closing this gap grows A14's real-only n.  This script
takes that measurement, on the CURRENT tree (A15/A16/A17/A18/A19/A20/A21 all
landed since A14's own base commit).

METHOD, reusing A14's own IC1 rules exactly.  Every scene below is either:
  * a REAL live execution (the row-verdict ~140s remeasurement, the
    structural <1s remeasurement -- both ALREADY-wired `ExecClass`
    dispatches, A15), or
  * a real `attach_constraint_reply` -- the SAME class of mechanism as
    `attach_reply` (a real inbound reply translation feeding a real,
    already-shipped Rule), applied to the ONE constraint-question channel
    `mg_ask_constraints` already asks over.  A16/A17's own test suite
    documents this as "THE ONLY WORKING CONSTRUCTION -- a REAL horizon
    reply (never a raw attribute poke)" for reaching decomposition at all;
    a raw `decompose_required` poke is measured NOT to survive a
    `run_rules()` pass (the cross-seed race A16 documented).  horizon=5.0
    is the SAME value every existing MG4/A17 gate scene uses -- chosen for
    direct comparability with the already-gated scene, not cherry-picked
    for this rung.
  * the SAME `headroom_n -> 0` synthetic pool-exit A13 SS7.1 validated,
    used ONLY to isolate one goal's dispatch from the others (A15's own
    `run_one` precedent) -- never to fabricate a pool composition this
    system cannot reach on its own.
Never a hand-faked `AgendaVerdict`, never `status -> 'retired'`, never an
edited `ArcGoalPolicy` weight, never an invented `ArcGoal.kind`.

The one place this script deliberately does NOT count a result as REAL: if
`mg_tier_retire`'s natural firing condition (full live witness coverage of
tier 1's own 10-id increment) has not closed, this script does NOT install a
hand-constructed `TierWitnessFact` to force a fire (that would be exactly
the "documented construction" A17 SS4.2 already reported once, honestly
labelled as not-natural) -- it installs the REAL `probe_tier_witness_
coverage()` output, whatever it says, and reports the honest decline if the
gap has not closed.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    PYTHONPATH=runners/dsl/python:. timeout 480 \\
    python3 scripts/arc6_impotence_resweep_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_decompose_ingest as adi  # noqa: E402
from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_impotence_resweep.json")

RID_ROW = "arc6.verdict.row_verdict_seed_only"
AGID_ROW = "arc.remeasure." + RID_ROW
RID_STRUCT = "arc6.structural.enum_op_table"
AGID_STRUCT = "arc.remeasure." + RID_STRUCT
STRUCTURAL_PARENT = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"
STRUCTURAL_LADDER_KEY = "missing_structural_primitive"
SB_BUDGET = "arc.supply.arc6.seam_a.import_oracle.budget"
SB_MD = "arc.supply.arc6.seam_a.import_oracle.missing_dimension"
SC_B = "arc6.claim.seam_b_signature_39_of_257"
SC_D = "arc6.claim.seam_d_verbatim_35_of_36"
SC_T0 = "arc6.claim.tier0_hs1_0_of_10"
SC_VL = "arc6.claim.valuelayer_supersedes_row_verdict"

# A14's own state 1 / state 2 (AMENDMENT A14 / IC2 table, PROGRAM_SYNTHESIS_
# ARC6_IMPOTENCE_CAMPAIGN.md SS3): the SAME 7-goal pool signature, reached
# two ways, differing only in the LIVE winner kind under testimony re-rank.
A14_STATE_POOL_SIG = tuple(sorted(
    [STRUCTURAL_PARENT, SB_BUDGET, SB_MD, SC_B, SC_D, SC_T0, SC_VL]))
A14_STATE1_KIND = "supply_blocker"
A14_STATE2_KIND = "source_claim"


def log(*a):
    print(*a, file=sys.stderr)
    sys.stderr.flush()


# =========================================================================== #
#  Boot / mechanical helpers -- the SAME shape A14/A15/A17's own scripts use.
# =========================================================================== #
def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _engine_sha() -> str:
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    return _sha256_file(so)


def _coherence_probe(s) -> bool:
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    return a["lst"] != a["tup"]


def boot():
    """The FULL current-capability boot: order-N magnitude + decomposition +
    the two-ExecClass executor, all in one graph -- never exercised together
    before this rung (every prior A15/A17 gate exercised the executor OR
    decompose, not both at once)."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
               "arc_magnitude", "arc_executor", "arc_decompose"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    assert _coherence_probe(s), "VALUE LAYER ABSENT on this engine"
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    ami.resolve_attrition_keys(s)
    ami.install_tier_ladder(s, ami.probe_tier_ladder())
    s._inner.run_rules()
    return s, ag


def _goal_node(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            return n
    return None


def _goal_kind(s, agid):
    n = _goal_node(s, agid)
    return s.node(n)["attrs"].get("kind") if n is not None else None


def _agenda_attrs(s):
    return s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]


def _live_winner_kind(s):
    """Bypasses any frozen stored AgendaVerdict field -- reads the CURRENT
    collapse the same way SEL_AGID is defined (A14 SS8's corrected view)."""
    at = _agenda_attrs(s)
    sel = at.get("arc_sel_agid") if at.get("mg_sel_agid") is None else at.get("mg_sel_agid")
    return {"sel_agid": sel, "sel_kind": _goal_kind(s, sel) if sel else None,
            "arc_sel_agid": at.get("arc_sel_agid"), "arc_sel_value": at.get("arc_sel_value"),
            "mg_sel_agid": at.get("mg_sel_agid"), "mg_sel_value": at.get("mg_sel_value")}


def _verdicts_live(s):
    out = []
    for v in axe.agenda_verdicts(s, "impotent"):
        if v.get("stale") == 1.0:
            continue
        out.append({k: v.get(k) for k in
                    ("epoch", "pool_n", "pool_agids", "exec_classes_held",
                     "nearest_unroutable_agid", "nearest_unroutable_kind",
                     "pool_stale")})
    return out


def _snapshot(s, label):
    pool = axe.pool(s)
    return {"label": label, "pool": sorted(pool), "pool_n": len(pool),
            "live_winner": _live_winner_kind(s),
            "verdicts": _verdicts_live(s)}


# =========================================================================== #
#  STEP 1 -- drive decomposition, via a REAL constraint reply (never a poke).
# =========================================================================== #
def drive_decompose(s, horizon_units=5.0):
    qs = list(s.nodes("ArcConstraintQuestion"))
    assert qs, "no ArcConstraintQuestion to answer -- mg_ask_constraints did not fire"
    ami.attach_constraint_reply(s, qs[0], "answer", con_kind="horizon",
                                horizon_units=horizon_units)
    s._inner.run_rules()
    parent = s.node(_goal_node(s, STRUCTURAL_PARENT))["attrs"] if \
        _goal_node(s, STRUCTURAL_PARENT) is not None else None
    children = sorted((dict(s.node(n)["attrs"]) for n in s.nodes("ArcGoal")
                       if s.node(n)["attrs"].get("parent_agid") == STRUCTURAL_PARENT),
                      key=lambda a: a.get("tier_order") or 0.0)
    return {"parent_status": parent.get("status") if parent else None,
            "n_children": len(children),
            "children_agids": [c.get("agid") for c in children]}


# =========================================================================== #
#  STEP 2 -- drive BOTH ExecClasses to REAL completion (A15 SS6's own shape).
# =========================================================================== #
def run_one_execclass(s, agid, tag):
    """Clamp every OTHER goal's headroom to 0 (A13 SS7.1's pool-exit
    technique, used here ONLY to isolate dispatch -- A15's precedent),
    drive `agid` to a real dispatch + execution, then RESTORE every clamped
    goal's real headroom so the loop's own next-step agenda is not left
    artificially narrowed."""
    snapshot = {}
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        if a.get("agid") != agid:
            snapshot[n] = a.get("headroom_n")
            s.set_attr(n, "headroom_n", 0.0)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, (agid, pending)
    rec = axe.run_order(s, pending[0], tag=tag)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    for n, orig in snapshot.items():
        if orig is not None:
            s.set_attr(n, "headroom_n", orig)
    s._inner.run_rules()
    return rec


# =========================================================================== #
#  STEP 3 -- a GENUINE attempt at mg_tier_retire's natural firing condition:
#  a real, stash-protected, sha-verified live re-run of the UNMODIFIED
#  scripts/arc6_structural_ceiling.py (A15's own second-ExecClass runner
#  script, A17's own SS4.1 methodology reproduced here on the current
#  engine), reading the FRESH witness set before restoring the protected
#  artifact.  If tier 1's real coverage has closed, the REAL probe result is
#  installed and mg_tier_retire is allowed to fire NATURALLY.  If it has not
#  closed, the REAL (declining) probe result is installed anyway (for the
#  record) and no synthetic override is applied.
# =========================================================================== #
def attempt_tier_witness_close(s):
    art = os.path.join(ROOT, "results", "arc6_structural_ceiling.json")
    upstream = os.path.join(ROOT, "results", "arc6_a_ceiling.json")
    assert os.path.exists(upstream), "upstream arc6_a_ceiling.json missing"
    before_sha = _sha256_file(art)
    stash_dir = tempfile.mkdtemp(prefix="a22_structural_stash_")
    stash_path = os.path.join(stash_dir, "arc6_structural_ceiling.json")
    shutil.copy2(art, stash_path)
    recs = None
    live_run_elapsed = None
    live_run_rc = None
    try:
        t0 = time.time()
        env = dict(os.environ, OZMA_NO_LLM="1",
                  PYTHONPATH=os.pathsep.join(
                      [os.path.join(ROOT, "runners", "dsl", "python"), ROOT]))
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts",
                                          "arc6_structural_ceiling.py")],
            capture_output=True, text=True, cwd=ROOT, env=env, timeout=120)
        live_run_elapsed = round(time.time() - t0, 3)
        live_run_rc = r.returncode
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        recs = adi.probe_tier_witness_coverage()
        with open(art) as fh:
            fresh_artifact = json.load(fh)
        fresh_witness = sorted(set(
            (fresh_artifact.get("strict_reach") or {}).get(
                "witness_and_in_budget_ids") or []))
    finally:
        after_sha_before_restore = _sha256_file(art)
        shutil.copy2(stash_path, art)
        restored_sha = _sha256_file(art)
        shutil.rmtree(stash_dir, ignore_errors=True)
    restored_ok = restored_sha == before_sha
    tier1 = next((r for r in (recs or []) if r["tier_order"] == 1.0), None)
    return {
        "live_run_elapsed_seconds": live_run_elapsed,
        "live_run_returncode": live_run_rc,
        "protected_artifact_before_sha256": before_sha,
        "protected_artifact_after_live_run_sha256": after_sha_before_restore,
        "protected_artifact_restored_byte_identical": restored_ok,
        "fresh_witness_and_in_budget_ids": fresh_witness,
        "all_tier_recs": recs,
        "tier1_all_ids_covered": tier1["all_ids_covered"] if tier1 else None,
        "tier1_missing_ids": tier1["missing_ids"] if tier1 else None,
        "gap_closed": bool(tier1 and tier1["all_ids_covered"] == 1.0),
    }


def main():
    t0 = time.time()
    log("== boot: full current capability (order-N + decompose + 2 ExecClasses) ==")
    s, ag = boot()
    boot_snap = _snapshot(s, "boot")
    log("boot pool_n =", boot_snap["pool_n"])

    log("== step 1: drive decomposition via a REAL horizon reply (5.0) ==")
    decompose_rec = drive_decompose(s, 5.0)
    after_decompose_snap = _snapshot(s, "after_decompose")
    log("after decompose pool_n =", after_decompose_snap["pool_n"],
        "children:", decompose_rec["n_children"])

    log("== step 2a: drive STRUCTURAL ExecClass to real completion (~0.1-1s) ==")
    #  Force staleness the SAME narrow poke A13 SS7.1 / A15 SS4.2 validated.
    axe._put_fact(s, "arc6_structural_ceiling_present", "0")
    s._inner.run_rules()
    struct_stale_pool = _snapshot(s, "after_forcing_structural_stale")
    rec_struct = run_one_execclass(s, AGID_STRUCT, "a22_struct")
    after_struct_snap = _snapshot(s, "after_structural_retires")
    log("structural remeasure:", rec_struct.get("status"),
        rec_struct.get("elapsed_seconds"), "s")

    log("== step 2b: drive ROW-VERDICT ExecClass to real completion (~140-200s) ==")
    row_stale_at_boot = None
    for n in s.nodes("GoalResidual"):
        a = s.node(n)["attrs"]
        if a.get("rid") == RID_ROW:
            row_stale_at_boot = a.get("stale")
    rec_row = run_one_execclass(s, AGID_ROW, "a22_row")
    after_row_snap = _snapshot(s, "after_row_verdict_retires")
    log("row-verdict remeasure:", rec_row.get("status"),
        rec_row.get("elapsed_seconds"), "s")

    log("== step 3: genuine attempt at mg_tier_retire's natural firing condition ==")
    tier_probe = attempt_tier_witness_close(s)
    log("tier1 all_ids_covered (real, live) =", tier_probe["tier1_all_ids_covered"],
        "missing:", tier_probe["tier1_missing_ids"])

    installed_facts = None
    after_tier_attempt_snap = None
    if tier_probe["all_tier_recs"]:
        installed_facts = adi.install_tier_witness_facts(s, tier_probe["all_tier_recs"])
        s._inner.run_rules()
        after_tier_attempt_snap = _snapshot(s, "after_tier_witness_install")
        log("after tier-witness install pool_n =", after_tier_attempt_snap["pool_n"])

    final_snap = after_tier_attempt_snap or after_row_snap
    final_pool_sig = tuple(sorted(final_snap["pool"]))
    final_kind = final_snap["live_winner"]["sel_kind"]
    distinct_from_a14 = not (
        final_pool_sig == A14_STATE_POOL_SIG and
        final_kind in (A14_STATE1_KIND, A14_STATE2_KIND))

    out = {
        "_README": (
            "A22 -- THE IMPOTENCE RE-SWEEP.  Drives the CURRENT tree's full "
            "capability (order-N magnitude, MG4 decomposition via a REAL "
            "horizon reply, BOTH ExecClasses to real completion, and a "
            "genuine live attempt at mg_tier_retire's natural firing "
            "condition) in ONE boot, and compares the resulting real pool "
            "state against A14's own two documented real states.  Bars: "
            "PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A22."),
        "engine_sha256": _engine_sha(),
        "seed_sha256_arc_executor": _sha256_file(
            os.path.join(ROOT, "seeds", "arc_executor.json")),
        "seed_sha256_arc_decompose": _sha256_file(
            os.path.join(ROOT, "seeds", "arc_decompose.json")),
        "boot_snapshot": boot_snap,
        "decompose_rec": decompose_rec,
        "after_decompose_snapshot": after_decompose_snap,
        "structural_forced_stale_snapshot": struct_stale_pool,
        "structural_remeasure_rec": {
            k: rec_struct.get(k) for k in
            ("agid", "runner", "status", "elapsed_seconds")},
        "after_structural_snapshot": after_struct_snap,
        "row_verdict_organically_stale_at_boot": row_stale_at_boot,
        "row_verdict_remeasure_rec": {
            k: rec_row.get(k) for k in
            ("agid", "runner", "status", "elapsed_seconds")},
        "after_row_verdict_snapshot": after_row_snap,
        "tier_witness_probe": tier_probe,
        "installed_tier_witness_fact_node_ids": [str(x) for x in (installed_facts or [])],
        "after_tier_witness_install_snapshot": after_tier_attempt_snap,
        "FINAL": {
            "pool_agids_signature": list(final_pool_sig),
            "pool_n": final_snap["pool_n"],
            "live_nearest_unroutable_kind": final_kind,
            "live_nearest_unroutable_agid": final_snap["live_winner"]["sel_agid"],
            "verdicts": final_snap["verdicts"],
            "a14_state_pool_signature": list(A14_STATE_POOL_SIG),
            "a14_state1_kind": A14_STATE1_KIND,
            "a14_state2_kind": A14_STATE2_KIND,
            "pool_signature_matches_a14_state": (
                final_pool_sig == A14_STATE_POOL_SIG),
            "GENUINELY_DISTINCT_FROM_A14": distinct_from_a14,
        },
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
    log("wrote", OUT)
    print(json.dumps(out["FINAL"], indent=2, default=str))
    print("total elapsed:", out["elapsed_seconds"], "s")


if __name__ == "__main__":
    main()
