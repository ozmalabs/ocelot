"""Net economy — mechanical host I/O for the worth ledger (seeds/net_economy.json).

The DECISIONS live in the seed rules (net_admit_when_worth_positive /
net_retire_when_worth_negative); this module only does mechanical structural
translation:

  * mint the NetEconomyPolicy singleton,
  * initialise a net's ledger attrs to zero (so accumulation starts clean),
  * measure a net's footprint = its parameter count (a static structural fact,
    the storage-rent basis — read off the WeightTensors, no decision),
  * a `worth` getter that reads the four ledger attrs + the policy back out
    (inspection only; the rules, not this getter, decide admit/retire).

No conditional over graph state chooses anything here — worth is arithmetic,
admission/retirement are the Rules.
"""
from __future__ import annotations


def _attrs(substrate, nid):
    # node/set_attr/neighbours all accept a NodeID object (as returned by
    # add_node / neighbours); pass it through unchanged.
    return substrate.node(nid)["attrs"]


def mint_policy(substrate, **overrides):
    """Mint the NetEconomyPolicy singleton (idempotent on kind). Overrides let a
    caller/test set a knob at mint; editing it later is a plain set_attr."""
    for n in substrate.nodes("NetEconomyPolicy"):
        return n  # already present — singleton
    attrs = {
        "kind": "net_economy_policy",
        "admit_margin": 0.0,
        "retire_floor": 0.0,
        "miss_penalty_weight": 1.0,
        "footprint_weight": 0.0001,
        "ledger_window": 3,
    }
    attrs.update(overrides)
    return substrate.add_node("NetEconomyPolicy", attrs)


def net_footprint(substrate, rn):
    """The net's storage footprint = its parameter count: the total number of
    weights across the WeightTensors of every assemblage the net wraps. Purely
    structural — walks net_assemblage -> has_step -> has_weight and sums the
    flattened `data` lengths. No decision."""
    total = 0
    for asm in substrate.neighbours(rn, "net_assemblage"):
        for step in substrate.neighbours(asm, "has_step"):
            for wt in substrate.neighbours(step, "has_weight"):
                data = _attrs(substrate, wt).get("data")
                total += _count(data)
    return total


def _count(data):
    if data is None:
        return 0
    if isinstance(data, (list, tuple)):
        return sum(_count(d) for d in data)
    return 1


def init_ledger(substrate, rn, *, footprint=None):
    """Zero a net's ledger and stamp its footprint, so the credit/debit rules
    accumulate from a clean, real base. Mechanical: footprint is measured, the
    rest are set to 0."""
    fp = net_footprint(substrate, rn) if footprint is None else footprint
    for key, val in (("net_residual", 0.0), ("net_cost", 0.0),
                     ("n_ledger_trials", 0.0), ("footprint", float(fp))):
        substrate.set_attr(rn, key, val)
    return fp


def worth(substrate, rn, policy=None):
    """Read a net's current worth = net_residual - net_cost -
    footprint_weight x footprint (inspection/getter — the same expression the
    admit/retire rules compute inside the engine)."""
    a = _attrs(substrate, rn)
    if policy is None:
        policy = next(iter(substrate.nodes("NetEconomyPolicy")))
    fpw = _attrs(substrate, policy).get("footprint_weight", 0.0)
    return (float(a.get("net_residual", 0.0))
            - float(a.get("net_cost", 0.0))
            - float(fpw) * float(a.get("footprint", 0.0)))
