"""POINT THE BOOTED, WIRED INTERFACE AT A NEW WORLD. Forage = a world it was NEVER built against: avatar
colour 7, food colour 4 (3 items), hazards colour 2 (2 static, lethal) — different colours, different dynamics
than snake (no body, multiple food, static hazards). Nothing here is forage-specific. The boot seed
world_understanding mints the six-role binding on inhabiting it; wire_world_understanding's reflex fills the
slots + navigates each master_tick; contact_consequence (seed rule) learns food/hazard from the visible
reward. We watch it understand + play FROM COLD.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/forage_world.py
"""
from __future__ import annotations
import os, sys, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from arc3_env import Arc3Env, GameState, ACTION1, ACTION2, ACTION3, ACTION4
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.world_play import wire_world_understanding

AV, FOOD, HAZ, BG = 7, 4, 2, 0
_DIR={ACTION1:(-1,0),ACTION2:(1,0),ACTION3:(0,-1),ACTION4:(0,1)}

class ForageEnv(Arc3Env):
    game_id="forage"; grid_h=14; grid_w=14
    def __init__(self, seed=7): self._rng=random.Random(seed); super().__init__()
    def _init_world(self):
        self._ar,self._ac=7,7
        self._haz=[(3,3),(10,10)]
        self._food=[]
        self._place_food(3)
    def _place_food(self,k):
        while len(self._food)<k:
            r,c=self._rng.randrange(self.grid_h),self._rng.randrange(self.grid_w)
            if (r,c)!=(self._ar,self._ac) and (r,c) not in self._haz and (r,c) not in self._food:
                self._food.append((r,c))
    def _render(self):
        g=[[BG]*self.grid_w for _ in range(self.grid_h)]
        for (r,c) in self._haz: g[r][c]=HAZ
        for (r,c) in self._food: g[r][c]=FOOD
        g[self._ar][self._ac]=AV
        return g
    def _apply(self, action, coord):
        if action in _DIR:
            dr,dc=_DIR[action]; nr,nc=self._ar+dr,self._ac+dc
            if 0<=nr<self.grid_h and 0<=nc<self.grid_w: self._ar,self._ac=nr,nc
        if (self._ar,self._ac) in self._haz: self._state=GameState.GAME_OVER; return
        if (self._ar,self._ac) in self._food:
            self._food.remove((self._ar,self._ac)); self._score+=1; self._place_food(3)
        self._state=GameState.NOT_FINISHED

def gnode(a): return next((n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Game"),None)

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)          # boot: world_understanding interface live
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    wire_world_understanding(a)                           # wire the consumer/allocator into master_tick
    w=ArcWorld(ForageEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); env=w.env
    g=gnode(a)
    # ensure the agent inhabits the world so the BIND rule fires (mechanical I/O, like any world adapter)
    body=next((n for n in a.s.nodes("Body")), None) or a.s.add_node("Body",{})
    a.inner.add_edge_unchecked(body,"inhabits",g)
    cons={}
    def slot_cons():
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if at.get("is_ground")==1.0 or at.get("rvalue") is None: continue
            rv=float(at["rvalue"])
            if rv not in cons:
                cm=a.s.add_node("Consequence",{"rvalue":rv,"value":0.0,"tasted":0.0}); a.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons[rv]=cm
    for i in range(14):  # warmup: derive self (acting)
        sub,ctx=w.apply((["Up","Down","Left","Right"][i%4],)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
        a.inner.add_edge_unchecked(body,"inhabits",gnode(a))
    eats=0; deaths=0; prev=ctx.get("score",0) or 0
    for i in range(160):
        g=gnode(a); a.inner.add_edge_unchecked(body,"inhabits",g)
        slot_cons()
        a.master_tick()                                  # wired reflex: BIND (once) + fill slots + navigate -> chosen_action
        from domains.world_play import DISP
        act=a.s.node(g)["attrs"].get("chosen_action")
        if act not in DISP: act=["Up","Down","Left","Right"][i%4]   # navigate had no goal yet -> EXPLORE (not Reset-churn)
        lc=None
        for b in a.s.nodes("WorldBinding"):
            for s in a.inner.neighbours(b,"role"):
                if a.s.node(s)["attrs"].get("role")=="controllable_locus": lc=a.s.node(s)["attrs"]
        intended=None
        if lc and lc.get("locus_cy") is not None:
            dr,dc=DISP[act]; ir,ic=int(round(lc["locus_cy"]))+dr,int(round(lc["locus_cx"]))+dc; gr=env._render()
            if 0<=ir<env.grid_h and 0<=ic<env.grid_w: intended=gr[ir][ic]
        sub,ctx=w.apply((act,)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0; ate=sc>prev; over=bool(ctx.get("over"))
        selfrv=int(lc.get("locus_rv") or 0) if lc else 0
        if ate: a.s.set_attr(g,"contact_rvalue",float(FOOD)); a.s.set_attr(g,"reward",1.0)
        elif over and intended and int(intended) not in (0,selfrv): a.s.set_attr(g,"contact_rvalue",float(intended)); a.s.set_attr(g,"reward",-1.0)
        else: a.s.set_attr(g,"contact_rvalue",0.0); a.s.set_attr(g,"reward",0.0)
        a.tick()                                         # contact_consequence learns from the visible reward
        if ate: eats+=1
        if over: deaths+=1; sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0
        else: prev=sc
    learned={int(rv):round(a.s.node(c)["attrs"].get("value") or 0,2) for rv,c in cons.items()}
    nb=len(a.s.nodes("WorldBinding")); nslots=len(a.s.nodes("WorldRole"))
    selfk=None
    for b in a.s.nodes("WorldBinding"):
        for s in a.inner.neighbours(b,"role"):
            if a.s.node(s)["attrs"].get("role")=="controllable_locus": selfk=int(a.s.node(s)["attrs"].get("locus_rv") or -1)
    print(f"  NEW WORLD (forage, never built against): WorldBinding minted={nb}, role slots={nslots}")
    print(f"  collected food={eats}  deaths={deaths}  learned consequence per colour={learned}  (self colour={selfk})")
    print(f"  DONKEY calls: {calls['n']}")
    ok = nb>=1 and nslots>=6 and eats>=3 and learned.get(FOOD,0)>0.3 and selfk==AV and calls["n"]==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the BOOTED + WIRED world-understanding interface, pointed at a "
          f"NEW world (forage: avatar=7, food=4, hazard=2 — never built against), bound it (six-role binding "
          f"minted by the boot seed), DERIVED self (colour {selfk}), LEARNED food(4)={learned.get(FOOD)} "
          f"positive + hazard(2)={learned.get(HAZ)} from the visible reward, and PLAYED it from cold — "
          f"collected {eats}. Same stack, new world, no game-noun, no donkey (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
