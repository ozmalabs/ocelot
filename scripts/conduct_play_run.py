"""Run the self-driving conduct town (280-287 spine) and export a play document
for the player artifact. Residents walk hop-by-hop toward a shared square; friends
meet predicted (greet); a feud pair meet UNPREDICTED -> surprise -> directed harm.
Every position + event is a real read of the walking town (no scripted drama)."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from worlds.bigville_walking_town_world import BigvilleWalkingTownWorld as W

SQUARE = (6, 4)
FACE = {"Ada":"\U0001F469","Ben":"\U0001F468","Cy":"\U0001F9D1","Dot":"\U0001F469‍\U0001F9B0",
        "Eli":"\U0001F9D4","Fay":"\U0001F471"}
# name, home, who they predict meeting (friends), goal = the square
RES = [
    {"name":"Ada","pos":(0,0),"goal":SQUARE,"predicts":["Ben"]},
    {"name":"Ben","pos":(1,7),"goal":SQUARE,"predicts":["Ada"]},
    {"name":"Cy", "pos":(11,1),"goal":SQUARE,"predicts":["Dot"]},
    {"name":"Dot","pos":(11,7),"goal":SQUARE,"predicts":["Cy"]},
    {"name":"Eli","pos":(0,4),"goal":SQUARE,"predicts":[]},          # rival, unpredicted
    {"name":"Fay","pos":(6,0),"goal":SQUARE,"predicts":[]},
]
BONDS = {
    ("Ada","Ben"):{"affection":3.0}, ("Ben","Ada"):{"affection":3.0},
    ("Cy","Dot"):{"affection":2.5},  ("Dot","Cy"):{"affection":2.5},
    ("Ada","Eli"):{"resentment":5.0,"affection":-4.0},               # the feud
}

def run():
    w = W(RES, BONDS, range_r=1)
    frames = []
    for t in range(22):
        out = w.step()
        pos = w.pos_log[-1][1]
        says = []
        for r in out:
            r = dict(r, actor=r.get("resident", r.get("actor")))
            if r["surprised"] and r["chosen"]:
                verb = {"harm":"strikes","help":"helps","transfer":"gives to",
                        "rest":"pauses"}.get(r["chosen"], r["chosen"])
                says.append({"actor":r["actor"], "act":r["chosen"], "target":r["target"],
                             "deepened":r.get("deepened",0),
                             "text": (f"{r['actor']} {verb} {r['target']}" if r["target"]
                                      else f"{r['actor']} {verb}")})
        frames.append({"t":t, "pos":{k:list(v) for k,v in pos.items()}, "events":says})
    residents = []
    for r in RES:
        nm = r["name"]
        rels = []
        for (a,b),v in BONDS.items():
            if a == nm:
                aff = v.get("affection",0.0) - v.get("resentment",0.0)
                rels.append({"who":b, "feeling":"warm" if aff>0 else ("hostile" if aff<0 else "neutral"),
                             "affection":v.get("affection",0.0), "resentment":v.get("resentment",0.0)})
        residents.append({"name":nm, "face":FACE.get(nm,"\U0001F9D1"), "home":list(r["pos"]),
                          "predicts":r.get("predicts",[]), "rels":rels, "health":w.health(nm)})
    doc = {"grid":[12,8], "square":list(SQUARE), "residents":residents,
           "frames":frames, "ticks":len(frames)}
    out = os.path.join("results","conduct_play","play.json")
    json.dump(doc, open(out,"w"))
    harms = [(f["t"], e["actor"], e["target"]) for f in frames for e in f["events"] if e["act"]=="harm"]
    helps = [(f["t"], e["actor"], e["target"]) for f in frames for e in f["events"] if e["act"]=="help"]
    print("wrote", out, "| ticks", len(frames))
    print("harm events:", harms)
    print("help events:", helps[:6])
    for nm in FACE: print(f"  {nm} final health {w.health(nm)}")
    w.close()

if __name__ == "__main__":
    run()
