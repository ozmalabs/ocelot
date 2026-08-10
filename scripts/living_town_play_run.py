"""Run the LIVE fold-in town (block 289000) and export a play document in the
conduct-player format: real positions hop-by-hop + the Bond-directed, surprise-gated
conduct the residents actually performed. Every position + event is a real read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worlds.bigville_living_town_world import BigvilleLivingTownWorld as W

FACE = ["\U0001F468","\U0001F469","\U0001F9D1","\U0001F471","\U0001F9D4","\U0001F475",
        "\U0001F466","\U0001F467","\U0001F9D3","\U0001F468‍\U0001F33E"]

def run():
    w = W(cast=8, seed=276000)
    residents_cfg, bonds = w._derive_social()
    predicts = {r["name"]: r.get("predicts", []) for r in residents_cfg}
    frames = []
    for t in range(40):
        before = len(w.conduct_events)
        w.integ_step()
        pos = {nm: [int(p[0]), int(p[1])] for nm in w.people
               if (p := w.pos.get(nm)) and not w.is_dead(nm)}
        evs = []
        for e in w.conduct_events[before:]:
            evs.append({"actor":e["actors"][0], "act":e["act"], "target":e["target"],
                        "deepened":0, "text":e["text"]})
        frames.append({"t":t, "pos":pos, "events":evs})
    xs = [p[0] for f in frames for p in f["pos"].values()]
    ys = [p[1] for f in frames for p in f["pos"].values()]
    grid = [max(xs)+2, max(ys)+2]
    residents = []
    for i, nm in enumerate(w.people):
        rels = []
        for (a,b),v in bonds.items():
            if a == nm:
                aff = v.get("affection",0.0) - v.get("resentment",0.0)
                rels.append({"who":b, "feeling":"warm" if aff>0 else ("hostile" if aff<0 else "neutral")})
        residents.append({"name":nm, "face":FACE[i%len(FACE)],
                          "home":list(w.homes.get(nm, w.pos.get(nm,[0,0]))),
                          "predicts":predicts.get(nm,[]), "rels":rels,
                          "health":100})
    sq = list(getattr(w, "map_anchors", {}).get("townhall", [grid[0]//2, grid[1]//2]))
    doc = {"grid":grid, "square":sq, "residents":residents, "frames":frames, "ticks":len(frames)}
    json.dump(doc, open("results/living_town_play/play.json","w"))
    from collections import Counter
    allev = [e for f in frames for e in f["events"]]
    print("wrote results/living_town_play/play.json | grid", grid, "ticks", len(frames), "residents", len(residents))
    print("conduct:", dict(Counter(e["act"] for e in allev)))
    print("harms:", [(f["t"],e["actor"],e["target"]) for f in frames for e in f["events"] if e["act"]=="harm"])
    w.close()

if __name__ == "__main__":
    run()
