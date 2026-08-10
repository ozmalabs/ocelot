"""seeds/navigation_modes.json — the CONCEPTS the jabberwock holds so it can UNDERSTAND that navigation has
several MODES and ACTIVELY CHOOSE between them. I (host) seed only WHAT a mode IS (concepts, worded so the
agent's OWN categorise_by_shape faculty files them); the agent decides HOW to choose, BY SHAPE — and the shape
it sees (select the WINNER by ARGMAX among COMPETING modes whose activation the situation drives = the
winner_take_all / competitive_inhibition meta-shape, regulating movement = feedback_control) IS the structure
of the selection rules (in grid_navigation: per-mode activation from situation signals -> Argmax winner ->
game.nav_mode -> the mode gates which select/escape behaviour runs).

A navigation MODE = a policy for choosing the next move, suited to a SITUATION. The three the agent is given:
  frontier_seek  — the default explorer: head for the nearest unexplored cell. Suits a situation where the
                   avatar is making progress (covering new ground each move).
  mover_avoid    — the patient one: when the reachable frontier CHURNS because objects are moving, do NOT
                   chase the ever-fresh cells the movers vacate; hold a committed goal and let movement settle.
  pocket_escape  — the prober: when CONFINED (no new coverage for several moves, walled in), stop seeking the
                   unreachable frontier; retry the directions a transient block closed and push for the region
                   edge, to break OUT of the pocket.
"""
import json, os

CONCEPTS = [
    {"name": "navigation_mode",
     "definition": "a policy for choosing the avatar's next move, suited to one situation; navigation has "
                   "several such modes and the agent regulates movement by selecting the one its situation fits",
     "category": "navigation"},
    {"name": "navigation_mode_selection",
     "definition": "actively choose between navigation modes: each competing mode has an activation the current "
                   "situation drives, and the agent selects the WINNER by argmax to gate behaviour; a "
                   "winner-take-all competition that regulates which movement policy is active",
     "category": "navigation"},
    {"name": "frontier_seek",
     "definition": "navigation mode (the default explorer): head for the nearest unexplored reachable cell; "
                   "its activation is high while the avatar makes progress, covering new ground each move",
     "category": "navigation"},
    {"name": "mover_avoid",
     "definition": "navigation mode (the patient one): when the reachable frontier churns because objects are "
                   "moving, do not chase the fresh cells the movers vacate; hold the committed goal until "
                   "movement settles; its activation is high when frontier flux is high",
     "category": "navigation"},
    {"name": "pocket_escape",
     "definition": "navigation mode (the prober): when confined with no new coverage for several moves, stop "
                   "seeking the unreachable frontier; retry blocked directions and push for the region edge to "
                   "break out; its activation is high when the no-progress count is high",
     "category": "navigation"},
    {"name": "coverage_progress",
     "definition": "situation signal: how many new cells the avatar covers per move; low progress means "
                   "confinement", "category": "navigation"},
    {"name": "confinement",
     "definition": "situation signal: consecutive moves with no new coverage; the avatar is walled into a "
                   "pocket", "category": "navigation"},
    {"name": "frontier_flux",
     "definition": "situation signal: how much the reachable frontier changes move to move because objects "
                   "are moving", "category": "navigation"},
]

# The three modes ALSO as NavMode NODES (the competitors the winner-take-all selection runs over). Each holds
# an `activation` the situation drives; the Argmax winner becomes game.nav_mode. The host wires game --has_mode-->
# each at startup; the activation + WTA + gating rules live in grid_navigation.
MODES = ["frontier_seek", "mover_avoid", "pocket_escape"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nodes = [{"local_id": i, "type": "Concept", "attrs": c} for i, c in enumerate(CONCEPTS)]
nodes += [{"local_id": len(CONCEPTS) + j, "type": "NavMode", "attrs": {"name": m, "activation": 0.0}}
          for j, m in enumerate(MODES)]
seed = {"id": "navigation_modes", "version": "1.0.0", "depends_on": [],
        "description": ("The CONCEPTS the agent holds to understand that navigation has several modes "
            "(frontier_seek / mover_avoid / pocket_escape) and to actively choose between them by shape "
            "(winner-take-all over situation-driven activations) + the NavMode competitor nodes. The CHOOSING "
            "rules (activation -> Argmax winner -> mode-gated select) live in grid_navigation."),
        "nodes": nodes, "edges": [], "productions": [], "concepts": [], "rules": []}
path = os.path.join(ROOT, "seeds", "navigation_modes.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/navigation_modes.json:", [c["name"] for c in CONCEPTS])
