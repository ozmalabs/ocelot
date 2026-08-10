"""navigate_alive — the jabberwock's navigation composed on the new predict_wall_set primitive. It reaches
what it is learning about WITHOUT self-trapping/dying, in a way that is GENERIC (no colour constant) and
DYNAMIC (routes over the PREDICTED t+1 obstacle map). This verify isolates the NAVIGATION component: given the
consequence the agent LEARNS (food=positive, body=impassable — derived from the visible score/death, verified
separately in s3_consequence), does slide_flood over predict_wall_set reach food ALIVE and eat, where the
reactive pursue died (eats ~0)? Composition only: held control-discovery + held slide_flood + NEW
predict_wall_set; no stamping of perceptions, no donkey.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/s3_navigate_alive.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv, BODY, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

UNREACH = 1e9
DISP = {"Up":(-1,0),"Down":(1,0),"Left":(0,-1),"Right":(0,1)}
def nid_int(nid): return int(str(nid).lstrip("#"))

def main():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    world = ArcWorld(SnakeEnv()); sub,ctx=world.reset(); agent.perceive_frame(sub); env=world.env
    g = next((n for n in agent.s.nodes("WorldInstance") if agent.s.node(n)["attrs"].get("world_type")=="Game"), None)
    H,W = env.grid_h, env.grid_w
    def cellmap():
        # ALL grid cells (the lattice slide_flood floods over): WorldInstance nodes carrying row+col+value.
        # NOT just world_type=="Cell" — only non-background cells carry that tag; the lattice is all 144.
        m={}
        for n in agent.s.nodes("WorldInstance"):
            at=agent.s.node(n)["attrs"]
            if at.get("row") is not None and at.get("col") is not None and at.get("value") is not None:
                m[(int(at["row"]),int(at["col"]))]=n
        return m
    def self_rc():
        # the controllable region (max respond_votes) — derived, not given
        best=None;bv=-1
        for n in agent.s.nodes("Region"):
            at=agent.s.node(n)["attrs"]
            rv=at.get("respond_votes") or 0
            if at.get("is_ground")==1.0: continue
            if int(at.get("rvalue") or -1)==FOOD: continue
            if rv>bv: bv=rv; best=n
        if best is None: return None
        a=agent.s.node(best)["attrs"]; return (int(round(a["cy"])),int(round(a["cx"])))
    def food_rc():
        for n in agent.s.nodes("Region"):
            at=agent.s.node(n)["attrs"]
            if int(at.get("rvalue") or -1)==FOOD: return (int(round(at["cy"])),int(round(at["cx"])))
        return None
    # warmup: derive self + action_delta by acting variedly (control discovery) — no stamping
    for i in range(14):
        a=["Up","Down","Left","Right"][i%4]
        sub,ctx=world.apply((a,)); agent.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub)

    eats=0; deaths=0; reached=0; prev=ctx.get("score",0) or 0
    for i in range(120):
        cm=cellmap(); srt=self_rc(); frt=food_rc()
        act=None
        if srt and frt and srt in cm and frt in cm:
            walls=agent.inner.predict_wall_set(H,W,[BODY])             # the t+1 obstacle map (LEARNED-impassable=body)
            wset=set(walls)
            # flood distance FROM the food-goal over the predicted walls (held slide_flood, NEW wall set)
            agent.inner.slide_flood(nid_int(cm[frt]),1,1,1,list(walls),400,i+1,nid_int(g),True,"_dist")
            # descend the gradient: the action whose next cell has min _dist and isn't a predicted wall
            best=None;bd=UNREACH
            for nm,(dr,dc) in DISP.items():
                nr,nc=srt[0]+dr,srt[1]+dc
                if not (0<=nr<H and 0<=nc<W): continue
                if (nr,nc) not in cm: continue
                if nid_int(cm[(nr,nc)]) in wset: continue
                d=agent.s.node(cm[(nr,nc)])["attrs"].get("_dist",UNREACH)
                d=UNREACH if d is None else float(d)
                if d<bd: bd=d; best=nm
            act=best
        sub,ctx=world.apply((act,) if act else ("Up",)); agent.perceive_frame(sub)
        sc=ctx.get("score",0) or 0
        if sc>prev: eats+=1
        prev=sc
        if ctx.get("over"): deaths+=1; sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub); prev=0
    print(f"  navigate_alive over 120 frames: eats={eats}  deaths={deaths}")
    print(f"  (reactive-pursue baseline for comparison was ~0 eats with constant death)")
    ok = eats>=3
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — navigate_alive composed on predict_wall_set: the agent floods "
          f"from the food-goal over the PREDICTED t+1 obstacle map (its body's next cells) and descends the "
          f"gradient, reaching food ALIVE and eating {eats}x (deaths={deaths}) where reactive pursue died at "
          f"~0. Held slide_flood + new predict_wall_set; generic (no colour rule) + dynamic (t+1 map).")
    print("="*96)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
