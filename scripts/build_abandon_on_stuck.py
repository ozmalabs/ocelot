"""seeds/abandon_on_stuck.json — the jabberwock's nav fix (feedback_control + competitive_inhibition): a
committed goal that yields NO MOVEMENT for K turns is dead. Cut effort there (abandon — feedback_control on the
payoff = movement), inhibit it (mark unreachable so the explorable filter drops it — competitive_inhibition),
and RELEASE it so select_seek commits a different reachable cell (the winner). Keyed on the avatar's MOVEMENT
(game.nav_stuck), which is reliable now that the authored cortex gives a stable position — the existing
goal_abandon used cover_stuck (coverage growth) which trickles and never fired. So the avatar covers the whole
reachable frontier instead of pressing one blocked direction into a wall."""
import json, os

def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def GTE(a, b): return {"type": "Gte", "a": a, "b": b}

K_STUCK = 4.0   # turns of NO MOVEMENT (reliable signal) before a goal is judged dead.

abandon = {
    "name": "abandon_goal_on_no_movement",
    "match": [["game", "committed_goal", "G"]],
    "where": GTE(P0(V("game"), "nav_stuck"), L(K_STUCK)),
    "effects": [
        ["set_attr", "G", "abandoned", 1.0],          # feedback_control: cut effort on the non-paying goal
        ["set_attr", "G", "unreachable", 1.0],         # competitive_inhibition: inhibit it from selection
        ["set_attr", "G", "committed", 0.0],
        ["del_edge", "game", "committed_goal", "G"]]}  # release -> select_seek picks a reachable winner

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
seed = {"id": "abandon_on_stuck", "version": "1.0.0", "depends_on": [],
        "description": ("abandon_goal_on_no_movement: a committed goal yielding no avatar movement for K turns "
            "is abandoned + inhibited + released, so the nav retargets a reachable frontier cell instead of "
            "pressing a blocked direction. Keyed on movement (nav_stuck), reliable with stable perception."),
        "nodes": [], "edges": [], "productions": [], "concepts": [], "rules": [abandon]}
json.dump(seed, open(os.path.join(ROOT, "seeds", "abandon_on_stuck.json"), "w"), indent=1)
json.load(open(os.path.join(ROOT, "seeds", "abandon_on_stuck.json")))
print("wrote seeds/abandon_on_stuck.json:", [r["name"] for r in seed["rules"]])
