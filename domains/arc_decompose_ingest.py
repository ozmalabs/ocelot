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
does exactly two things, both translation:

1. **self-load the seed** — `seeds/arc_decompose.json` carries
   `self_load_only`, so `substrate/boot_all.py::_read_seeds` SKIPS it.
   `ensure_arc_decompose` is the on-demand loader, idempotent on a
   `Seed{id:'arc_decompose'}` marker — the `arc_magnitude_ingest.
   ensure_arc_magnitude` precedent, verbatim.

2. **read-off helpers** — pure queries for the write-up / the gates.  A
   decomposition child is recognised by carrying `parent_agid`; nothing here
   decides that a goal IS a child, it only reads the attr the rule already
   stamped.
"""
from __future__ import annotations

from typing import Any

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
