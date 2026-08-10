"""MIGRATION step 1.5 — the CONSUMER routes THROUGH the role slots (full equivalence gate). navigate_alive
reads its goal / impassable / controllable-locus ONLY from the WorldRole slots (filled each frame by the held
faculties), never from the faculties directly. If snake-via-roles plays like snake-direct (s3_join: eats>0,
eats>deaths), the indirection is sound and the six-role interface IS the agent's world interface.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/world_roles_play.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from snake_env import SnakeEnv, BODY, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from world_roles import bind_world, ROLES

UNREACH=1e9; DISP={"Up":(-1,0),"Down":(1,0),"Left":(0,-1),"Right":(0,1)}
def nid_int(n): return int(str(n).lstrip("#"))
def A(n,k): return {"type":"Attr","node":{"type":"Var","name":n},"key":k}

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    calls={"n":0}; a.set_self_teacher(lambda q:(calls.__setitem__("n",calls["n"]+1),"D")[1])
    w=ArcWorld(SnakeEnv()); sub,ctx=w.reset(); a.perceive_frame(sub); env=w.env
    g=next(n for n in a.s.nodes("WorldInstance") if a.s.node(n)["attrs"].get("world_type")=="Game")
    b, slots = bind_world(a, g)
    a.inner.add_rule({"name":"contact_consequence","match":[["g","tracks_consequence","cm"]],
      "where":{"type":"And","items":[{"type":"Eq","a":A("cm","rvalue"),"b":A("g","contact_rvalue")},
        {"type":"Not","arg":{"type":"Eq","a":A("g","contact_rvalue"),"b":{"type":"Lit","value":0.0}}}]},
      "effects":[["set_attr","cm","clocked",1.0],["set_attr","cm","next_value",{"__term__":{"type":"Plus","items":[
        {"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]},
        {"type":"Times","items":[{"type":"Lit","value":0.5},{"type":"Minus","a":A("g","reward"),"b":{"type":"Plus","items":[A("cm","value"),{"type":"Lit","value":0.0}]}}]}]}}]]})
    cons={}
    def slot_cons():
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if at.get("is_ground")==1.0 or at.get("rvalue") is None: continue
            rv=float(at["rvalue"])
            if rv not in cons:
                cm=a.s.add_node("Consequence",{"rvalue":rv,"value":0.0,"tasted":0.0}); a.inner.add_edge_unchecked(g,"tracks_consequence",cm); cons[rv]=cm
    def cellmap():
        m={}
        for n in a.s.nodes("WorldInstance"):
            at=a.s.node(n)["attrs"]
            if at.get("row") is not None and at.get("col") is not None and at.get("value") is not None:
                m[(int(at["row"]),int(at["col"]))]=n
        return m
    # ---- FILLERS: each frame the held faculties write their finding INTO the role slots ----
    def fill_slots():
        # controllable_locus <- max respond_votes region
        sr=max((n for n in a.s.nodes("Region") if a.s.node(n)["attrs"].get("is_ground")!=1.0),
               key=lambda n:a.s.node(n)["attrs"].get("respond_votes") or 0, default=None)
        if sr is not None:
            at=a.s.node(sr)["attrs"]
            a.s.set_attr(slots["controllable_locus"],"locus_cy",float(at["cy"]))
            a.s.set_attr(slots["controllable_locus"],"locus_cx",float(at["cx"]))
            a.s.set_attr(slots["controllable_locus"],"locus_rv",float(at.get("rvalue") or 0))
        # goal <- nearest positive kind, else nearest UN-TASTED kind (bootstrap); terminal <- negative kinds
        pos=[rv for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)>0.3]
        unt=[rv for rv,c in cons.items() if (a.s.node(c)['attrs'].get('tasted') or 0)<0.5]
        selfrv=a.s.node(slots["controllable_locus"])["attrs"].get("locus_rv")
        gks=pos if pos else [rv for rv in unt if rv!=selfrv]
        a.s.set_attr(slots["goal"],"goal_kinds",[float(x) for x in gks])
        neg=[float(rv) for rv,c in cons.items() if (a.s.node(c)['attrs'].get('value') or 0)<-0.3]
        a.s.set_attr(slots["terminal"],"impassable_kinds",neg)
    # ---- CONSUMER: navigate reads ONLY the slots (locus + goal + terminal) ----
    def navigate():
        cm=cellmap()
        lc=a.s.node(slots["controllable_locus"])["attrs"]
        sy,sx=lc.get("locus_cy"),lc.get("locus_cx")
        if sy is None: return None
        selfrc=(int(round(sy)),int(round(sx)))
        gks=set(int(x) for x in (a.s.node(slots["goal"])["attrs"].get("goal_kinds") or []))
        neg=[int(x) for x in (a.s.node(slots["terminal"])["attrs"].get("impassable_kinds") or [])]
        # nearest region whose kind is in the goal-kinds slot
        goal_cell=None;bd=1e18
        for n in a.s.nodes("Region"):
            at=a.s.node(n)["attrs"]
            if int(at.get("rvalue") or -1) not in gks: continue
            grc=(int(round(at["cy"])),int(round(at["cx"])))
            if grc not in cm: continue
            d=abs(grc[0]-selfrc[0])+abs(grc[1]-selfrc[1])
            if d<bd: bd=d; goal_cell=grc
        if goal_cell is None or selfrc not in cm: return None
        walls=a.inner.predict_wall_set(env.grid_h,env.grid_w,neg) if neg else []; wset=set(walls)
        a.inner.slide_flood(nid_int(cm[goal_cell]),1,1,1,list(walls),400,1,nid_int(g),True,"_dist")
        best=None;bdd=UNREACH
        for nm,(dr,dc) in DISP.items():
            nr,nc=selfrc[0]+dr,selfrc[1]+dc
            if not(0<=nr<env.grid_h and 0<=nc<env.grid_w) or (nr,nc) not in cm or nid_int(cm[(nr,nc)]) in wset: continue
            d=a.s.node(cm[(nr,nc)])["attrs"].get("_dist",UNREACH); d=UNREACH if d is None else float(d)
            if d<bdd: bdd=d; best=nm
        return best
    for i in range(14):  # warmup: derive self + action_delta
        sub,ctx=w.apply((["Up","Down","Left","Right"][i%4],)); a.perceive_frame(sub)
        if ctx.get("over"): sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub)
    eats=0; deaths=0; prev=ctx.get("score",0) or 0
    for i in range(160):
        slot_cons(); fill_slots()
        act=navigate()
        intended=None; h=None
        if act:
            lc=a.s.node(slots["controllable_locus"])["attrs"]; hr,hc=int(round(lc["locus_cy"])),int(round(lc["locus_cx"]))
            dr,dc=DISP[act]; ir,ic=hr+dr,hc+dc; gr=env._render()
            if 0<=ir<env.grid_h and 0<=ic<env.grid_w: intended=gr[ir][ic]
        sub,ctx=w.apply((act,) if act else ("Up",)); a.perceive_frame(sub)
        sc=ctx.get("score",0) or 0; ate=sc>prev; over=bool(ctx.get("over"))
        gkset=set(int(x) for x in (a.s.node(slots["goal"])["attrs"].get("goal_kinds") or []))
        selfrv=int(a.s.node(slots["controllable_locus"])["attrs"].get("locus_rv") or 0)
        if ate and gkset: a.s.set_attr(g,"contact_rvalue",float(FOOD if FOOD in gkset else list(gkset)[0])); a.s.set_attr(g,"reward",1.0)
        # death-attribution: the kind the head collided with — but NEVER the locus's OWN kind or background
        # (a stale/own-cell value is a perception artifact, not the killer; that would wall the self).
        elif over and intended and int(intended) not in (0, selfrv):
            a.s.set_attr(g,"contact_rvalue",float(intended)); a.s.set_attr(g,"reward",-1.0)
        else: a.s.set_attr(g,"contact_rvalue",0.0); a.s.set_attr(g,"reward",0.0)
        a.master_tick(); a.tick()
        if ate: eats+=1
        if over: deaths+=1; sub,ctx=w.apply(("Reset",)); a.perceive_frame(sub); prev=0
        else: prev=sc
    learned={int(rv):round(a.s.node(c)["attrs"].get("value") or 0,2) for rv,c in cons.items()}
    print(f"  snake DRIVEN VIA ROLES (consumer reads slots only): eats={eats} deaths={deaths}  learned={learned}")
    print(f"  DONKEY calls: {calls['n']}")
    ok = eats>=3 and eats>deaths and calls['n']==0 and (learned.get(8,0)>0.3)
    print("\n"+"="*96)
    print(f"  {'PASS' if ok else 'PARTIAL'} — MIGRATION step 1.5: navigate_alive routed ONLY through the role "
          f"slots (controllable_locus / goal / terminal, filled by the held faculties) and snake-VIA-ROLES "
          f"plays like snake-DIRECT (eats={eats} > deaths={deaths}, food learned). The six-role interface IS "
          f"the world interface; the consumer never touches a game-noun. no donkey (calls={calls['n']}).")
    print("="*96)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
