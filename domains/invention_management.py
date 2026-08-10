"""Feature-invention management as a GRAPH-RESIDENT rule (CLAUDE.md: the agent is
a graph; decisions are Rules, not Python).

The agent controls how readily it invents new phonological features via the
`invention_balance_threshold` on its DevelopmentRoot. The old Python logic in
`DevelopmentCortex.observe()` gated easing on EXACT predicate stability
(`predicate_delta_norm < 1e-6`) — but predicates never stabilise (continuous
belief revision keeps retuning them BECAUSE the features are insufficient), so
the agent perpetually RAISED the threshold and invention deadlocked (1 feature in
40 cycles, threshold 0.70→0.90).

This installs the agent's own Rule that breaks the deadlock. The key judgement:
predicate churn that PERSISTS alongside impasses is NOT "detectors still settling
— hold off"; it is the signature of an INSUFFICIENT feature space (the agent has
tuned its detectors as far as they go and STILL can't satisfy the teaching).
Counted over cycles (`tuning_plateau`), once tuning has churned-with-impasses for
a window, the agent eases invention DECISIVELY rather than waiting for a stability
that the insufficiency itself prevents.

The world adapter only RECORDS observations (predicate_delta_norm, recent_impasses)
onto the root and ticks; the THRESHOLD decision is this Rule. See
[[ozma_self_developmental_cortex]] / speech_development's feature_invention concept.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (Attr, Lit, Var, Lt, Gte, Eq, And,
                          IfThenElse, Plus, Minus, Max, Min)

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "invention_management.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


def _invention_threshold_terms():
    """The agent's invention-management decision, as Term-trees over its
    DevelopmentRoot's own observations AND its seeded dials (invention_eps,
    plateau_window, impasse_threshold, invention_floor/ceiling, the ease/raise
    steps) — all read from the root, no Python constants. Returns
    (plateau_next, threshold_next)."""
    R = Var("R")
    delta = Attr(R, "predicate_delta_norm")     # how much predicates churned
    imp = Attr(R, "recent_impasses")            # persistent disagreement
    thr = Attr(R, "invention_balance_threshold")
    plat = Attr(R, "tuning_plateau")
    eps = Attr(R, "invention_eps")
    window = Attr(R, "plateau_window")
    imp_thr = Attr(R, "impasse_threshold")
    floor = Attr(R, "invention_floor")
    ceil = Attr(R, "invention_ceiling")
    deadlock_step = Attr(R, "deadlock_ease_step")
    stable_step = Attr(R, "stable_ease_step")
    gentle_step = Attr(R, "gentle_raise_step")

    churn = Gte(a=delta, b=eps)                  # detectors still moving
    stable = Lt(a=delta, b=eps)                  # detectors settled
    persistent_impasse = Gte(a=imp, b=imp_thr)

    # tuning_plateau: count consecutive cycles where tuning churns WITHOUT
    # clearing impasses — the deadlock signature; reset the moment it breaks.
    plateau_next = IfThenElse(
        And(items=(churn, persistent_impasse)),
        Plus(items=(plat, Lit(1))),
        Lit(0))

    # invention_balance_threshold (lower = invent more readily):
    #   plateau >= window     -> DEADLOCK: tuning plateaued with impasses -> ease hard
    #   stable & impasse       -> clean signal of a too-coarse feature space -> ease
    #   churn (no deadlock yet) -> still settling -> nudge up, gently
    #   else (stable, no impasse) -> hold
    threshold_next = IfThenElse(
        Gte(a=plateau_next, b=window),
        Max(items=(floor, Minus(a=thr, b=deadlock_step))),
        IfThenElse(
            And(items=(stable, persistent_impasse)),
            Max(items=(floor, Minus(a=thr, b=stable_step))),
            IfThenElse(
                churn,
                Min(items=(ceil, Plus(items=(thr, gentle_step)))),
                thr)))
    return plateau_next, threshold_next


def install_invention_management(substrate) -> dict:
    """Install the graph-resident feature-invention management Rule on the
    DevelopmentRoot. Idempotent-ish (re-mints the rule each call). Returns
    {'root': NodeID, 'rule_index': int}. The world adapter writes
    predicate_delta_norm + recent_impasses to the root, sets
    invention_eval_pending=1, and ticks/apply_rule_once to let the agent decide."""
    nat = _native(substrate)
    try:
        substrate.add_production({
            "src": {"type": "DevelopmentRoot", "var": "a"},
            "edge_type": "manages",
            "tgt": {"type": "DevelopmentRoot", "var": "b"},
            "provenance": "invention_management:self",
        })
    except Exception:
        pass

    root = None
    for n in substrate.nodes("DevelopmentRoot"):
        root = n
        break
    if root is None:
        root = substrate.add_node("DevelopmentRoot",
                                  {"origin": "development_cortex"})
    # Seed the invention dials onto the root (this is their authority — read by
    # the rule). Set unconditionally so the seed value wins over any transient
    # default minted elsewhere (e.g. development_cortex._dev_root).
    for k, v in _load_seed().get("development_root", {}).items():
        substrate.set_attr(root, k, v)
    # Ensure the runtime-state attrs the rule reads/accumulates exist.
    a = substrate.node(root)["attrs"]
    for k, v in (("tuning_plateau", 0), ("recent_impasses", 0.0),
                 ("predicate_delta_norm", 0.0), ("invention_eval_pending", 0)):
        if k not in a:
            substrate.set_attr(root, k, v)
    # Self-edge so the rule can match the lone root node.
    if root not in substrate.neighbours(root, "manages"):
        try:
            substrate.add_edge(root, "manages", root, {})
        except Exception:
            pass

    plateau_next, threshold_next = _invention_threshold_terms()
    R = Var("R")
    rule = {
        "name": "manage_feature_invention",
        "match": [["R", "manages", "R"]],
        "where": Eq(a=Attr(R, "invention_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            # threshold first (reads the ORIGINAL tuning_plateau), then update it.
            ["set_attr", "R", "invention_balance_threshold",
             {"__term__": threshold_next.to_dict()}],
            ["set_attr", "R", "tuning_plateau",
             {"__term__": plateau_next.to_dict()}],
            ["set_attr", "R", "invention_eval_pending", 0],
        ],
    }
    rule_index = nat.add_rule(rule)
    return {"root": root, "rule_index": rule_index}


__all__ = ["install_invention_management"]
