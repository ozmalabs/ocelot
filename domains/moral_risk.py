"""moral_risk — wires the MORAL-INJURY COST into the agent's risk matrix (the
expected-free-energy / MPC cost it already minimises). For each projected action
it adds the frustration that action would WRITE between an enacted-basin and a
values-basin, per the seeded quantification:

    moral_injury_cost = β_enactment × value_centrality × frame_reality × conflict

  · β_enactment    : perpetrate(1.0) > fail_to_prevent(0.6) > witness(0.3) > deliberate(0)
  · value_centrality: depth of the values-basin crossed (0..1, from mt_target_equilibria)
  · frame_reality   : reality-depth of the frame acted in (0..1; real≈1, game≈0.1)
  · conflict        : how far the act contradicts the values-basin (0..1)

The cost-function wiring is the real, general part. The per-action descriptors
(which act enacts which frame at what β against which value) are, in the live
agent, read from forward_model (projected outcome) + partial_frame_inheritance
(frame_reality) + the values-basin (centrality, conflict).
"""
from __future__ import annotations
from dataclasses import dataclass, field

BETA = {"perpetrate": 1.0, "fail_to_prevent": 0.6, "witness": 0.3, "deliberate": 0.0}


@dataclass
class Action:
    name: str
    pragmatic_cost: float            # distance of outcome from goal (the existing EFE term)
    epistemic_cost: float = 0.0      # expected uncertainty (the existing EFE term)
    enactment: str = "deliberate"    # perpetrate | fail_to_prevent | witness | deliberate
    value_centrality: float = 0.0    # 0..1 (foundational values-basin depth)
    frame_reality: float = 0.0       # 0..1 (real frame ≈1, contained game ≈0.1)
    conflict: float = 0.0            # 0..1 (act-vs-values misalignment)

    def moral_injury_cost(self) -> float:
        return (BETA.get(self.enactment, 0.0) * self.value_centrality
                * self.frame_reality * self.conflict)


def risk(action: Action, w_moral: float = 1.0,
         w_prag: float = 1.0, w_epist: float = 1.0) -> float:
    """Total expected cost = pragmatic + epistemic + MORAL-INJURY. The optimizer
    minimises this; w_moral=0 recovers the old (amoral) risk matrix."""
    return (w_prag * action.pragmatic_cost
            + w_epist * action.epistemic_cost
            + w_moral * action.moral_injury_cost())


def choose(actions, **w):
    """Select the minimum-total-cost action (active-inference policy selection)."""
    return min(actions, key=lambda a: risk(a, **w))
