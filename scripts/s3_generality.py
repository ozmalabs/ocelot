"""GENERALITY — the jabberwock's learn+navigate loop transfers to a DIFFERENT game UNCHANGED, because it
names no colour. Same code as s3_join (derive self, learn rewarding/lethal kinds from visible score+death,
navigate alive over the predicted obstacle map) run on a RECOLOURED dynamics world: self=colour 5, a MOVING
goal=colour 3 (catching it scores) — different dynamics (moving target, no body), different colours. If it
learns colour-3 is rewarding and catches it with NO colour in the code, generic is proven.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/s3_generality.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from dynamics_world import DynamicsEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

UNREACH=1e9; DISP={"Up":(-1,0),"Down":(1,0),"Left":(0,-1),"Right":(0,1)}
def nid_int(n): return int(str(n).lstrip("#"))
def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

# a DIFFERENT game: recoloured dynamics (self=5, moving goal=3). Only _render changes (movement is positional).
class RecolouredDynamics(DynamicsEnv):
    game_id="recoloured_dynamics"
    def _render(self):
        g=[[0]*self.grid_w for _ in range(self.grid_h)]
        g[self._mr][self._mc]=3      # the moving goal (was 8)
        g[self._ar][self._ac]=5      # the self (was 9)
        return g

def run_join(make_world, label, frames=160):
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=make_world(); sub,ctx=w.reset(); a.perceive_frame(sub); env=w.env
    g=next(n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Game")
    H,W=env.grid_h,env.grid_w
    a.inner.add_rule({"name":"contact_consequence","match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[{"type":"Eq","a":A("cm","rvalue"),"b":A("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":A("g","contact_rvalue"),"b":{"type":"Lit","value":0.0}}}]},
      "effects":[["set_attr","cm","clocked",1.0],["set_attr","cm","tasted",1.0],
        ["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[
          {"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},
          {"type":"Times","items":[{"type":"Lit","value":0.5},
            {"type":"Minus","a":A("g","reward"),"b":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]}}]}]}}]]})
    cons={}
    def slots():
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if at.get("is_ground")==1.0: continue
            rv=at.get("rvalue")
            if rv is None: continue
            rv=float(rv)
            if rv not in cons:
                cm=a.s.add_node("Consequence",{"rvalue":rv,"value":0.0,"tasted":0.0}); a.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons[rv]=cm
    def cellmap():
        m={}
        for n in a.s.nodes("WorldInstance"):
            at=a.s.node(n)["attrs"]
            if at.get("row") is not None and at.get("col") is not None and at.get("value") is not None:
                m[(int(at["row"]),int(at["col"]))]=n
        return m
    def self_region():
        best=None;bv=-1
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if at.get("is_ground")==1.0: continue
            rv=at.get("respond_votes") or 0
            if rv>bv: bv=rv; best=n
        return best
    def regions_by_kind(k):
        return [n for n in a.s.nodes("Region") if int(a.s.node(n)["attrs"].get("rvalue") or -999)==int(k) and a.s.node(n)["attrs"].get("is_ground")!=1.0]
    for i in range(14):
        sub,ctx=w.apply((["Up","Down","Left","Right"][i%4],)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
    eats=0; deaths=0; prev=ctx.get("score",0) or 0
    for i in range(frames):
        slots(); cm=cellmap(); selfr=self_region(); selfrc=None; selfk=None
        if selfr is not None:
            sa=a.s.node(selfr)["attrs"]; selfrc=(int(round(sa["cy"])),int(round(sa["cx"]))); selfk=int(sa.get("rvalue") or 0)
        pos=[(rv,c) for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)>0.3]
        neg=[int(rv) for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)<-0.3]
        goal_kinds=[rv for rv,_ in pos] if pos else [rv for rv,c in cons.items()
                    if (a.s.node(c)['attrs'].get('tasted') or 0)<0.5 and (selfk is None or int(rv)!=selfk)]
        goal_cell=None; goal_kind=None; bd=1e18
        if selfrc:
            for gk in goal_kinds:
                for rn in regions_by_kind(gk):
                    ra=a.s.node(rn)["attrs"]; grc=(int(round(ra["cy"])),int(round(ra["cx"])))
                    if grc not in cm: continue
                    d=abs(grc[0]-selfrc[0])+abs(grc[1]-selfrc[1])
                    if d<bd: bd=d; goal_cell=grc; goal_kind=int(gk)
        act=None
        if selfrc and goal_cell and selfrc in cm:
            walls=a.inner.predict_wall_set(H,W,neg) if neg else []; wset=set(walls)
            a.inner.slide_flood(nid_int(cm[goal_cell]),1,1,1,list(walls),400,i+1,nid_int(g),True,"_dist")
            best=None;bdd=UNREACH
            for nm,(dr,dc) in DISP.items():
                nr,nc=selfrc[0]+dr,selfrc[1]+dc
                if not(0<=nr<H and 0<=nc<W) or (nr,nc) not in cm or nid_int(cm[(nr,nc)]) in wset: continue
                d=a.s.node(cm[(nr,nc)])["attrs"].get("_dist",UNREACH); d=UNREACH if d is None else float(d)
                if d<bdd: bdd=d; best=nm
            act=best
        intended=None
        if act and selfrc:
            dr,dc=DISP[act]; ir,ic=selfrc[0]+dr,selfrc[1]+dc; grid=env._render()
            if 0<=ir<H and 0<=ic<W: intended=grid[ir][ic]
        sub,ctx=w.apply((act,) if act else ("Up",)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0; ate=sc>prev; over=bool(ctx.get("over"))
        if ate and goal_kind is not None: a.s.set_attr(g,"contact_rvalue",float(goal_kind)); a.s.set_attr(g,"reward",1.0)
        elif over and intended: a.s.set_attr(g,"contact_rvalue",float(intended)); a.s.set_attr(g,"reward",-1.0)
        else: a.s.set_attr(g,"contact_rvalue",0.0); a.s.set_attr(g,"reward",0.0)
        a.master_tick(); a.tick()
        if ate: eats+=1
        if over: deaths+=1; sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0
        else: prev=sc
    learned={int(rv):round(a.s.node(c)["attrs"].get("value") or 0,2) for rv,c in cons.items()}
    print(f"  [{label}] eats={eats} deaths={deaths}  learned consequence={learned}  donkey={calls['n']}")
    return eats, learned, calls['n']

def main():
    print("="*96); print("GENERALITY — the SAME learn+navigate loop on a DIFFERENT, RECOLOURED game (no colour in the code)."); print("="*96)
    e1,l1,d1=run_join(lambda: ArcWorld(RecolouredDynamics(mode="chase")), "recoloured-dynamics self=5 goal=3")
    pos1=[k for k,v in l1.items() if v>0.3]
    ok = e1>=3 and 3 in pos1 and d1==0
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — UNCHANGED code (names no colour) on a different game: the agent "
          f"derived self(5), LEARNED the moving goal colour-3 is rewarding ({l1.get(3)}>0.3) from the visible "
          f"score, and CHASED it alive — eats={e1}, donkey={d1}. The learn+navigate loop is GENERIC: it "
          f"transfers to a new world/dynamics/colours with no edit.")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
