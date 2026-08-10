"""Demonstrate the moral-injury cost wired into the risk matrix: it changes the
agent's choice — rejecting a goal-achieving but morally-injuring action — and it
discriminates frame-reality (the same act is cheap in a game, costly in reality)
and enactment-depth (witnessing < perpetrating).
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.moral_risk import Action, risk, choose

# A decision: reach the goal. Candidate policies the forward_model projected.
ACTIONS = [
    Action("A: reach goal by an act that betrays a core value (real, perpetrated)",
           pragmatic_cost=0.1, enactment="perpetrate",
           value_centrality=0.9, frame_reality=1.0, conflict=0.9),
    Action("B: reach goal the slower, value-consistent way",
           pragmatic_cost=0.4, enactment="deliberate",
           value_centrality=0.9, frame_reality=1.0, conflict=0.0),
    Action("C: the SAME betraying act in a game (does NOT reach the real goal)",
           pragmatic_cost=0.95, enactment="perpetrate",
           value_centrality=0.9, frame_reality=0.1, conflict=0.9),
    Action("D: reach goal by only WITNESSING the betrayal (real frame)",
           pragmatic_cost=0.35, enactment="witness",
           value_centrality=0.9, frame_reality=1.0, conflict=0.9),
]


def table(w_moral):
    print(f"\n  w_moral = {w_moral}:")
    print(f"    {'action':52} {'prag':>5} {'moral-inj':>9} {'TOTAL':>7}")
    for a in ACTIONS:
        mi = a.moral_injury_cost()
        print(f"    {a.name[:52]:52} {a.pragmatic_cost:5.2f} {mi:9.3f} "
              f"{risk(a, w_moral=w_moral):7.3f}")
    pick = choose(ACTIONS, w_moral=w_moral)
    print(f"    ⟶ CHOOSES: {pick.name}")


def main():
    print("=" * 78)
    print("MORAL-INJURY COST WIRED INTO THE RISK MATRIX")
    print("=" * 78)

    table(0.0)   # old amoral risk matrix
    table(1.0)   # with the moral-injury term

    print("\n" + "=" * 78)
    print("READING")
    print("=" * 78)
    print("""
  w_moral=0 (the old risk matrix): picks A — the betrayal — because it is the
  cheapest way to the goal. The amoral optimizer takes the shortcut through a
  core value, seeing no cost there.

  w_moral=1 (moral-injury wired in): picks B — the value-consistent path. A now
  carries a large moral-injury cost (β=1 perpetrate × 0.9 centrality × 1.0 real
  × 0.9 conflict ≈ 0.73), which outweighs its pragmatic cheapness. The agent
  pays the slower path rather than write a permanent values-frustration into
  itself.

  And it DISCRIMINATES, not just forbids:
   · C (same act, in a GAME): moral-injury ≈ 0.07 (frame_reality 0.1) — cheap.
     You may do in fiction what you may not do in reality. Frame-reality, live.
   · D (only WITNESS, real): moral-injury ≈ 0.24 (β 0.3) — real but far less than
     perpetrating. The enactment gradient, live.

  The moral-injury cost is now a term the optimizer minimises like any other —
  not a rule bolted on, a cost it weighs. Set w_moral=0 and the agent is amoral
  again; the morality is the weight, and the weight is in the matrix.
""")


if __name__ == "__main__":
    main()
