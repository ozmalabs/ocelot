"""AG-5 THE EXECUTOR — the world adapter.  MECHANICAL I/O ONLY.

`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A10: *"running a measurement
script is mechanical I/O and is admissible adapter work.  THE DECISION OF WHAT
TO RUN IS THE COLLAPSE.  No Python decisions."*  This file is the hands, and it
is held to the same module-specific source audit `domains/arc_goal_ingest.py`
passes: **it never imports `substrate_rs`, never calls `.evaluate(`, never
calls `run_rules`**, and its only substrate contact is `add_node` / `node` /
`nodes` / `set_attr` / `add_edge_unchecked` / `load_seed_manifest`.  With no
evaluator and no rule engine reachable from it there is nowhere for a decision
over graph state to hide.

FOUR JOBS, all translation.

1. **self-load the seed** — `seeds/arc_executor.json` carries `self_load_only`
   (the `arc_goals` / `arc_magnitude` precedent), so `boot_all::_read_seeds`
   skips it and it is not live in every agent in the tree.

2. **run an ordered job** — `ax_dispatch` (a RULE) writes an `ExecOrder`
   carrying a `runner` NAME.  This adapter resolves that name against
   `RUNNERS`, a frozen capability table, and invokes it.  **The table is a
   permission boundary, not a decision**: it is the same shape as
   `seed_loader.manifest_for`, and a name with no entry is REFUSED and
   recorded on the order rather than executed.  The choice of job was made by
   the graph; this cannot widen it, and cannot narrow it in a way that depends
   on graph state — the lookup is on the order's own `runner` string.

3. **re-ingest the fresh evidence, WITH ITS PROVENANCE** — and this is the one
   modelling choice in the rung, stated in the open.  A `ResidualCondition` in
   this tree records **the world-state a measurement was taken under**: the six
   shipped ones all read *"the artifact this residual quotes is still on disk
   with the content sha it was ingested at"* or *"this refutation applies while
   the value layer collapses list and tuple"*.  A RE-measurement is a new
   measurement, so its provenance is the world **as probed at the moment it
   ran** — the adapter copies that probe onto the residual's own conditions.
   It never writes a value chosen to make a condition hold; it writes what
   `goal_residual_ingest.probe_facts` measured, and if that probe had returned
   the other value the condition would be re-anchored to the other value and
   would still be stale.  **The proof that this is not tautological is that the
   re-anchored conditions can and do RE-FAIL**: the freshly-added
   evidence-presence condition goes false the moment the fresh artifact leaves
   the disk, which is measured in both directions in the gate.

4. **bump the measurement epoch** — `arc_measure_epoch` has been a counter with
   no producer through two rungs, and every expiry mechanism below turns on it
   (an unconditioned answer lives one epoch; an unanswered question lapses at
   the next epoch; the anti-oscillation latch is defined in epochs).  It is
   bumped **when and only when a measurement actually ran**, so the clock
   counts measurements rather than ticks.
"""
from __future__ import annotations

import hashlib
import importlib
import os
import time
from typing import Any, Dict, List, Optional

from domains import arc_goal_ingest as agi
from domains import goal_residual_ingest as gri
from substrate.seed_loader import manifest_for

SEED_ID = "arc_executor"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#  THE CAPABILITY TABLE.  A `runner` name the graph produced is looked up here
#  and nowhere else: it is never a path, never an argv word and never reaches a
#  shell.  Exactly one entry, matching the one `ExecClass` the seed ships.
RUNNERS: Dict[str, str] = {
    "arc6_remeasure_row_verdict": "scripts.arc6_remeasure_row_verdict",
}

EVIDENCE_FACT_PREFIX = "remeasured_evidence_present."


# --------------------------------------------------------------------------- #
#  1.  Self-load.
# --------------------------------------------------------------------------- #
def ensure_arc_executor(sub, ag_node) -> bool:
    """Install `seeds/arc_executor.json` if it is not already on this graph."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == SEED_ID:
            return False
    sub._inner.load_seed_manifest(manifest_for(SEED_ID), ag_node)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == SEED_ID:
            return True
    sub.add_node("Seed", {"id": SEED_ID, "version": "1.0.0"})
    return True


# --------------------------------------------------------------------------- #
#  Pure queries.
# --------------------------------------------------------------------------- #
def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def orders(sub) -> List[dict]:
    return [dict(sub.node(n)["attrs"], _id=str(n)) for n in sub.nodes("ExecOrder")]


def pending_orders(sub) -> list:
    return [n for n in sub.nodes("ExecOrder")
            if sub.node(n)["attrs"].get("status") == "ordered"]


def _residual_node(sub, rid: str):
    for n in sub.nodes("GoalResidual"):
        if sub.node(n)["attrs"].get("rid") == rid:
            return n
    return None


def _conditions_of(sub, rid: str) -> list:
    return [n for n in sub.nodes("ResidualCondition")
            if sub.node(n)["attrs"].get("rid") == rid]


def _fact_node(sub, name: str):
    for n in sub.nodes("ResidualFact"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def _put_fact(sub, name: str, value: str):
    """Write a measured fact.  IN PLACE — `gr_condition_lapse`'s `fact_equals`
    branch requires `Count(matching ResidualFact) == 1`, so a second node with
    the same name silently breaks every condition that reads it."""
    n = _fact_node(sub, name)
    if n is None:
        return sub.add_node("ResidualFact", {"name": name, "value": value})
    sub.set_attr(n, "value", value)
    return n


def _agenda_node(sub):
    for n in sub.nodes("ArcAgenda"):
        return n
    return None


def arm(sub) -> dict:
    """THE TICK BOUNDARY.  Copy the SETTLED selection forward, verbatim.

    `run_rules` is a fixpoint with no rule ordering, so `ag_select`'s stamp is
    a TRANSIENT while `ag_mint_*` is still populating the pool — and a rule
    that reads it inside the same fixpoint reads whatever it happened to hold.
    Measured: the first draft of `ax_dispatch` ordered the RUNNER-UP on the
    shipped boot.

    This is the fix's adapter half, and it is a VERBATIM COPY — two reads, two
    writes, no comparison and no branch.  **The agreement test is
    `ax_dispatch`'s own `Eq`**, evaluated in the next fixpoint against these
    values; a selection that is still moving cannot match both.  Carrying a
    settled conclusion across a tick boundary is what a world adapter is for.
    """
    a = _agenda_node(sub)
    if a is None:
        return {}
    at = sub.node(a)["attrs"]
    sub.set_attr(a, "arc_exec_armed_agid", at.get("arc_sel_agid"))
    sub.set_attr(a, "arc_exec_armed_value", at.get("arc_sel_value"))
    return {"arc_exec_armed_agid": at.get("arc_sel_agid"),
            "arc_exec_armed_value": at.get("arc_sel_value")}


# --------------------------------------------------------------------------- #
#  2.  Run an ordered job.
# --------------------------------------------------------------------------- #
def run_order(sub, order_node, tag: Optional[str] = None) -> dict:
    """Execute one `ExecOrder`.  Mechanical: table lookup, invoke, write back.

    Returns the record written onto the order.
    """
    at = sub.node(order_node)["attrs"]
    runner = at.get("runner")
    module_name = RUNNERS.get(runner)
    if module_name is None:
        sub.set_attr(order_node, "status", "refused")
        sub.set_attr(order_node, "refused_because",
                     "runner_name_not_in_the_capability_table")
        return {"agid": at.get("agid"), "runner": runner, "status": "refused",
                "refused_because": "runner_name_not_in_the_capability_table"}

    epoch = agi.measure_epoch(sub)
    tag = tag or ("e%s" % (epoch if epoch is not None else "0"))
    sub.set_attr(order_node, "status", "running")
    t0 = time.time()
    mod = importlib.import_module(module_name)
    ran = mod.remeasure(tag)
    elapsed = round(time.time() - t0, 2)

    for k, v in (("status", "ran"),
                 ("ran_epoch", str(epoch)),
                 ("artifact", ran["artifact"]),
                 ("artifact_sha256", ran["artifact_sha256"]),
                 ("runner_engine_sha256", ran.get("engine_sha256")),
                 ("elapsed_seconds", elapsed),
                 ("protected_files_restored_byte_identical",
                  1.0 if ran.get("protected_files_restored_byte_identical")
                  else 0.0)):
        sub.set_attr(order_node, k, v)

    reingest = reingest_evidence(sub, at.get("source_rid"), ran["artifact"],
                                 ran["artifact_sha256"])
    agi.bump_measure_epoch(sub)
    rec = {"agid": at.get("agid"), "runner": runner, "status": "ran",
           "tag": tag, "elapsed_seconds": elapsed, "ran_at_epoch": epoch,
           "epoch_after": agi.measure_epoch(sub)}
    rec.update(ran)
    rec["reingest"] = reingest
    return rec


# --------------------------------------------------------------------------- #
#  3.  Re-ingest the fresh evidence, with its provenance.
# --------------------------------------------------------------------------- #
def reingest_evidence(sub, rid: Optional[str], artifact_rel: str,
                      artifact_sha: str) -> dict:
    """Re-stamp the residual from the FRESH artifact and re-anchor its
    conditions to the world as probed AT THIS MOMENT.

    Every number comes from the same dotted paths `goal_residual_ingest.SPEC`
    used for the original ingest — nothing is transcribed and nothing is
    recomputed by a different route.  `stale` is NEVER written here: whether
    the residual still describes the world is `gr_condition_lapse` /
    `gr_condition_hold`'s verdict, and this adapter must not pre-empt it.
    """
    out: Dict[str, Any] = {"rid": rid, "artifact": artifact_rel,
                           "artifact_sha256": artifact_sha}
    r = _residual_node(sub, rid) if rid else None
    if r is None:
        out["reingested"] = False
        out["why"] = "no GoalResidual carries that rid"
        return out

    import json
    doc = json.load(open(os.path.join(ROOT, artifact_rel)))
    entry = None
    for e in gri.SPEC:
        if e["rid"] == rid:
            entry = e
            break
    if entry is None:
        out["reingested"] = False
        out["why"] = "no ingest SPEC entry for that rid"
        return out

    honest = gri._at(doc, entry["honest_ids_path"])
    denom = gri._at(doc, entry["denominator_path"])
    fresh = {
        "evidence_artifact": artifact_rel,
        "evidence_artifact_sha256": artifact_sha,
        "evidence_engine_sha256": gri._at(doc, entry["engine_sha_path"]),
        "ceiling_honest_n": float(len(honest)) if isinstance(honest, list) else None,
        "denominator_n": float(len(denom)) if isinstance(denom, list) else None,
        "mechanism": gri._at(doc, entry["mechanism_path"]),
    }
    before = {k: sub.node(r)["attrs"].get(k) for k in fresh}
    for k, v in fresh.items():
        if v is not None:
            sub.set_attr(r, k, v)
    sub.set_attr(r, "remeasured_at_epoch", str(agi.measure_epoch(sub)))
    out["residual_before"] = before
    out["residual_after"] = {k: sub.node(r)["attrs"].get(k) for k in fresh}

    #  THE PROVENANCE RE-ANCHOR.  `probe_facts` measures the world live, in
    #  this process, on this engine — the same call the original ingest used.
    probed = gri.probe_facts(sub)
    for name, value in sorted(probed.items()):
        _put_fact(sub, name, value)
    out["probed_facts"] = dict(sorted(probed.items()))

    reanchored = []
    for c in _conditions_of(sub, rid):
        ca = sub.node(c)["attrs"]
        if ca.get("ckind") != "fact_equals":
            continue
        fv = ca.get("filter_value")
        if fv not in probed:
            continue
        reanchored.append({"filter_value": fv, "was": ca.get("expected_str"),
                           "now": probed[fv]})
        sub.set_attr(c, "expected_str", probed[fv])
        sub.set_attr(c, "reanchored_at_epoch", str(agi.measure_epoch(sub)))
        sub.set_attr(c, "why", (
            "RE-ANCHORED by the executor: this residual's evidence was "
            "re-measured at measurement epoch %s on engine %s, and %s measured "
            "'%s' at that moment.  The condition records the world the "
            "measurement was taken under, so it lapses again if that world "
            "moves." % (agi.measure_epoch(sub),
                        (fresh["evidence_engine_sha256"] or "?")[:12],
                        fv, probed[fv])))
    out["reanchored_conditions"] = reanchored

    #  The FRESH artifact becomes evidence in its own right, on exactly the
    #  shipped idiom: five of the six committed residuals already hold under
    #  "the artifact is still on disk with the sha it was ingested at".
    fact_name = EVIDENCE_FACT_PREFIX + rid
    _put_fact(sub, fact_name, "1")
    if not any(sub.node(c)["attrs"].get("filter_value") == fact_name
               for c in _conditions_of(sub, rid)):
        cond = sub.add_node("ResidualCondition", {
            "rid": rid,
            "ckind": "fact_equals",
            "filter_value": fact_name,
            "expected_str": "1",
            "why": ("the RE-MEASUREMENT's own artifact is the evidence now; if "
                    "it leaves the disk or its content changes, this residual "
                    "must be re-read rather than re-used.  Same condition the "
                    "five artifact-backed residuals already ship."),
        })
        sub._inner.add_edge_unchecked(r, "holds_under", cond)
        out["condition_added"] = fact_name
    sub.set_attr(r, "remeasured_evidence_sha256", artifact_sha)
    out["reingested"] = True
    return out


def refresh_evidence_facts(sub) -> dict:
    """Re-probe the world the re-anchored conditions read.  Pure measurement.

    A re-measured residual holds under *its own fresh artifact still being on
    disk with the sha it was measured at*.  This re-checks that, in place, and
    re-runs the value-layer probe.  Called once per loop iteration by the
    driver; it decides nothing — `gr_condition_lapse` reads the numbers.
    """
    out = {}
    for name, value in sorted(gri.probe_facts(sub).items()):
        _put_fact(sub, name, value)
        out[name] = value
    for n in sub.nodes("GoalResidual"):
        a = sub.node(n)["attrs"]
        rid, sha = a.get("rid"), a.get("remeasured_evidence_sha256")
        if not rid or not sha:
            continue
        path = os.path.join(ROOT, a.get("evidence_artifact") or "")
        ok = _sha256(path) == sha
        name = EVIDENCE_FACT_PREFIX + rid
        _put_fact(sub, name, "1" if ok else "0")
        out[name] = "1" if ok else "0"
    return out


# --------------------------------------------------------------------------- #
#  Read-off helpers.  Pure queries for the gates and the write-up.
# --------------------------------------------------------------------------- #
def exec_classes(sub) -> list:
    return sorted((sub.node(n)["attrs"].get("name"),
                   sub.node(n)["attrs"].get("runner"))
                  for n in sub.nodes("ExecClass"))


def pool(sub) -> list:
    """`ag_select`'s POOL, read back — status not terminal and headroom > 0."""
    out = []
    for n in sub.nodes("ArcGoal"):
        a = sub.node(n)["attrs"]
        if a.get("status") in ("retired", "settled"):
            continue
        if not isinstance(a.get("headroom_n"), (int, float)):
            continue
        if a["headroom_n"] <= 0:
            continue
        out.append(a.get("agid"))
    return sorted(out)


def statuses(sub) -> dict:
    return {sub.node(n)["attrs"].get("agid"): sub.node(n)["attrs"].get("status")
            for n in sub.nodes("ArcGoal")}
