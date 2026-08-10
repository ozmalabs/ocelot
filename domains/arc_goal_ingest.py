"""ARC-GRAIN GOALS — the world adapter.  MECHANICAL I/O ONLY.

`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md` §9: *"no Python decisions —
minting, matching, ranking, lapsing, asking are all Rules/Terms.  The only
Python is an ingest adapter."*  This file is that adapter, and it is held to
the stronger module-specific form the goal-residual ingest adapter already
passes: **it never imports `substrate_rs`, never calls `.evaluate(`, never
calls `run_rules`**, and its only substrate contact is
`add_node` / `nodes` / `node` / `set_attr` / `load_seed_manifest`.  There is
therefore no place in it for a hidden decision over graph state.

THREE JOBS, all translation:

1. **self-load the seed** — `seeds/arc_goals.json` carries `self_load_only`,
   so `substrate/boot_all.py::_read_seeds` SKIPS it and it is not live in
   every agent in the tree.  `ensure_arc_goals` is the on-demand loader
   (`domains/reading_collapse.py::_ensure_role_decode_loop` precedent),
   idempotent on a `Seed{id:'arc_goals'}` marker.

2. **carry the measurement epoch** — as a `ResidualFact{name:
   'arc_measure_epoch'}`, i.e. the SAME node type `gr_condition_lapse`'s
   `fact_equals` branch already reads.  A measurement happening is a fact
   about the world, not a decision: the adapter records it, the rules decide
   what it means (an unconditioned testimony residual goes stale; an open
   question retires).  Stored as a STRING because that is what `fact_equals`
   compares.

3. **carry a reply's structured condition** — when a human answers an
   `ArcQuestion` naming a checkable reason, the reason arrives in whatever
   external form the world uses; `attach_reply` writes it onto the reply
   Message as `cond_*` attrs.  This is the `comp_topic` precedent exactly:
   the adapter records what the world said, and the RULE decides whether that
   makes a condition (`ag_reply_mints_testimony_conditioned`) or whether the
   epoch default applies (`..._unconditioned`).  **The reply text is never
   parsed, and nothing here ever derives a signature from a string.**
"""
from __future__ import annotations

import os
from typing import Any, Optional

from substrate.seed_loader import manifest_for

SEED_ID = "arc_goals"
EPOCH_FACT = "arc_measure_epoch"


# --------------------------------------------------------------------------- #
#  1.  Self-load.
# --------------------------------------------------------------------------- #
def ensure_arc_goals(sub, ag_node) -> bool:
    """Install `seeds/arc_goals.json` if it is not already on this substrate.

    Returns True if it installed, False if the marker was already present.
    """
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
#  2.  The measurement epoch.
# --------------------------------------------------------------------------- #
def _epoch_node(sub) -> Optional[Any]:
    for n in sub.nodes("ResidualFact"):
        if sub.node(n)["attrs"].get("name") == EPOCH_FACT:
            return n
    return None


def measure_epoch(sub) -> Optional[str]:
    """Read the epoch back out.  A pure query."""
    n = _epoch_node(sub)
    return None if n is None else sub.node(n)["attrs"].get("value")


def set_measure_epoch(sub, epoch: int) -> Any:
    """Record the measurement epoch as the string `fact_equals` compares."""
    n = _epoch_node(sub)
    if n is None:
        return sub.add_node("ResidualFact",
                            {"name": EPOCH_FACT, "value": str(int(epoch))})
    sub.set_attr(n, "value", str(int(epoch)))
    return n


def bump_measure_epoch(sub) -> Any:
    """A measurement happened.  Mechanical +1; the rules decide what lapses."""
    cur = measure_epoch(sub)
    return set_measure_epoch(sub, (int(cur) if cur is not None else 0) + 1)


# --------------------------------------------------------------------------- #
#  3.  A reply, and the condition the world attached to it (if any).
# --------------------------------------------------------------------------- #
def attach_reply(sub, question_node, text: str, *,
                 cond_kind: Optional[str] = None,
                 cond_filter_value: Optional[str] = None,
                 cond_expected_str: Optional[str] = None,
                 cond_expected: Optional[float] = None,
                 sender: str = "interlocutor") -> Any:
    """Write an inbound reply to an `ArcQuestion` into the graph.

    `cond_*` are passed through EXACTLY as the world supplied them — absent
    means absent.  The adapter does not infer a condition from the text, and
    it does not decide whether the reply "counts": the two mirrored reply
    rules do that, on the presence of `cond_kind`.
    """
    attrs = {"from": sender, "text": text, "kind": "arc_reply"}
    if cond_kind is not None:
        attrs["cond_kind"] = cond_kind
    if cond_filter_value is not None:
        attrs["cond_filter_value"] = cond_filter_value
    if cond_expected_str is not None:
        attrs["cond_expected_str"] = cond_expected_str
    if cond_expected is not None:
        attrs["cond_expected"] = cond_expected
    m = sub.add_node("Message", attrs)
    sub._inner.add_edge_unchecked(m, "responds_to", question_node)
    return m


# --------------------------------------------------------------------------- #
#  Read-off helpers.  Pure queries for the write-up / the gates.
# --------------------------------------------------------------------------- #
def arc_goals(sub) -> list:
    return [dict(sub.node(n)["attrs"], _id=str(n)) for n in sub.nodes("ArcGoal")]


def selection(sub) -> dict:
    for n in sub.nodes("ArcAgenda"):
        a = sub.node(n)["attrs"]
        return {k: v for k, v in a.items() if k.startswith("arc_sel")
                or k == "arc_vocab_epoch"}
    return {}


def minted_vocab(sub) -> list:
    return sorted(sub.node(n)["attrs"].get("token")
                  for n in sub.nodes("SignatureVocab")
                  if sub.node(n)["attrs"].get("minted") == 1.0)


def questions(sub) -> list:
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("ArcQuestion")]


def ask_texts(sub) -> list:
    return [sub.node(n)["attrs"].get("text") for n in sub.nodes("Message")
            if sub.node(n)["attrs"].get("kind") == "arc_question"]
