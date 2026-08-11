"""MG4 — ORDER-N DECOMPOSITION — the world adapter.

MECHANICAL I/O ONLY, held to the same module-specific form
`domains/arc_magnitude_ingest.py` passes: it never imports `substrate_rs`,
never calls `.evaluate(`, never calls `run_rules`, and its only substrate
contact is `add_node` / `node` / `nodes` / `set_attr` / `add_edge_unchecked` /
`load_seed_manifest`.  There is therefore no place in it for a decision over
graph state to hide.

Decomposition itself — which tiers become children, when a parent retires,
what a child's own order-N headroom is — is entirely `seeds/arc_decompose.json`
(`mg_decompose` / `mg_decompose_retire` / `mg_child_order_n`).  This module
does exactly three things, all translation:

1. **self-load the seed** — `seeds/arc_decompose.json` carries
   `self_load_only`, so `substrate/boot_all.py::_read_seeds` SKIPS it.
   `ensure_arc_decompose` is the on-demand loader, idempotent on a
   `Seed{id:'arc_decompose'}` marker — the `arc_magnitude_ingest.
   ensure_arc_magnitude` precedent, verbatim.

2. **read-off helpers** — pure queries for the write-up / the gates.  A
   decomposition child is recognised by carrying `parent_agid`; nothing here
   decides that a goal IS a child, it only reads the attr the rule already
   stamped.

3. **A17 — tier witness coverage, the `goal_residual_ingest.probe_facts`/
   `install_facts` shape applied to a decomposition child.**
   `probe_tier_witness_coverage`/`install_tier_witness_facts` read TWO
   dotted paths already resolved by existing code —
   `arc_magnitude_ingest.probe_tier_ladder`'s own per-tier CUMULATIVE
   `unlocked_ids` (the same artifact `arc_magnitude_ingest.LADDER_ARTIFACT`
   names) and that SAME artifact's `strict_reach.witness_and_in_budget_ids`
   (freshly re-measured by the ALREADY-WIRED second `ExecClass`, A15's
   `scripts/arc6_remeasure_structural.py`) — take ONE set difference (a
   tier's own increment, the identical arithmetic
   `arc_magnitude_ingest.probe_tier_ladder` already performs for
   `increment_n`) and ONE set-containment check, and write the verdict as a
   `TierWitnessFact` node. Nothing here decides whether a tier IS resolved;
   `mg_tier_retire` (`seeds/arc_decompose.json` v1.1.0) reads the fact and
   makes that call as a Rule, exactly as CLAUDE.md requires.
"""
from __future__ import annotations

from typing import Any

from domains import arc_magnitude_ingest as ami
from substrate.seed_loader import manifest_for

SEED_ID = "arc_decompose"


# --------------------------------------------------------------------------- #
#  1.  Self-load.
# --------------------------------------------------------------------------- #
def ensure_arc_decompose(sub, ag_node) -> bool:
    """Install `seeds/arc_decompose.json` if it is not already present."""
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
#  2.  Read-off helpers.  Pure queries.
# --------------------------------------------------------------------------- #
def children_of(sub, parent_agid: str) -> list:
    """Every ArcGoal minted as a decomposition child of `parent_agid`."""
    return [dict(sub.node(n)["attrs"], _id=str(n)) for n in sub.nodes("ArcGoal")
            if sub.node(n)["attrs"].get("parent_agid") == parent_agid]


def decomposed_goals(sub) -> list:
    """Every ArcGoal that has reached the 'decomposed' terminal status."""
    return [dict(sub.node(n)["attrs"], _id=str(n)) for n in sub.nodes("ArcGoal")
            if sub.node(n)["attrs"].get("status") == "decomposed"]


def pool_agids(sub, term_builder: Any = None) -> list:
    """Convenience: every ArcGoal agid currently NOT retired/settled/decomposed
    with positive headroom — the same predicate POOL() encodes, read off
    Python-side for a report rather than through a Term.  MIRRORS the filter,
    never DEFINES it: the rule's own POOL() is the authority."""
    out = []
    for n in sub.nodes("ArcGoal"):
        a = sub.node(n)["attrs"]
        if a.get("status") in ("retired", "settled"):
            continue
        if not (a.get("headroom_n") or 0.0) > 0.0:
            continue
        out.append(a.get("agid"))
    return out


# --------------------------------------------------------------------------- #
#  3.  A17 — tier witness coverage.  PURE MEASUREMENT, mirroring
#      goal_residual_ingest.probe_facts/install_facts's own "measure, then
#      write the answer down" shape.  No decision: `all_ids_covered` is a
#      FACT about set containment, not a verdict on whether the goal should
#      retire — `mg_tier_retire` (seeds/arc_decompose.json) makes that call.
# --------------------------------------------------------------------------- #
def probe_tier_witness_coverage(ladder_rec: Any = None) -> list:
    """For each tier of the MEASURED ladder (`arc_magnitude_ingest`'s own
    `LADDER_ARTIFACT`), whether this tier's OWN increment of task ids — the
    SAME increment `mg_decompose` mints a child for — is now FULLY covered
    by the artifact's `strict_reach.witness_and_in_budget_ids`.

    `ladder_rec` may be a pre-computed `arc_magnitude_ingest.
    probe_tier_ladder()` result (so a caller that already has one does not
    pay for a second population join); default re-derives it.

    A `all_ids_covered` verdict here is FALSIFIABLE, not vacuous: on the
    artifact committed at this rung's own base commit it reads `0.0` for
    EVERY tier — measured, not assumed (`PROGRAM_SYNTHESIS_ARC6_
    RETIRE_BLOCKER.md` §"the honest natural-state finding") — and a real
    re-measurement (`scripts/arc6_remeasure_structural.py`, already wired as
    the executor's second `ExecClass`, A15) is the only thing that can make
    it read `1.0` for a tier whose own increment it has fully verified.
    """
    ladder_rec = ladder_rec if ladder_rec is not None else ami.probe_tier_ladder()
    if not ladder_rec.get("resolved") or not ladder_rec.get("ladder_key"):
        return []
    sc = ami._load_artifact(ami.LADDER_ARTIFACT)
    if sc is None:
        return []
    witness = sorted(set(
        (sc.get("strict_reach") or {}).get("witness_and_in_budget_ids") or []))
    witness_set = set(witness)
    bundles = sc.get("bundles") or []
    out = []
    prev_ids: set = set()
    for i, t in enumerate(ladder_rec["tiers"]):
        b = bundles[i] if i < len(bundles) else {}
        cur_ids = set(b.get("unlocked_ids") or [])
        increment_ids = sorted(cur_ids - prev_ids)
        missing_ids = sorted(set(increment_ids) - witness_set)
        out.append({
            "ladder_key": ladder_rec["ladder_key"],
            "tier_order": t["order"],
            "bundle": t.get("bundle"),
            "increment_ids": increment_ids,
            "witness_ids_at_probe": witness,
            "missing_ids": missing_ids,
            "all_ids_covered": (1.0 if (increment_ids and not missing_ids)
                                else 0.0),
            "evidence_artifact": ami.LADDER_ARTIFACT,
        })
        prev_ids = cur_ids
    return out


def install_tier_witness_facts(sub, recs: list) -> list:
    """Write each probed tier's verdict as a `TierWitnessFact` node.
    Mechanical: one `add_node` per record, nothing conditional."""
    out = []
    for r in recs:
        out.append(sub.add_node("TierWitnessFact", {
            "ladder_key": r["ladder_key"],
            "tier_order": r["tier_order"],
            "all_ids_covered": r["all_ids_covered"],
            "n_increment_ids": float(len(r["increment_ids"])),
            "n_missing_ids": float(len(r["missing_ids"])),
            "evidence_artifact": r["evidence_artifact"],
        }))
    return out
