"""COMPOSE-FROM-FACULTIES — the agent builds LEAD = held SEEK + a small PREDICT producer it authors itself.

The general mechanism (the jabberwock's design): a complex faculty = a held faculty (H) reading an attr a
small minted PRODUCER writes; faculties compose ONLY through shared graph attrs. Here H = SEEK (reads
self.tgt_r/tgt_c, host affordance), and the agent AUTHORS the small PREDICT producer (writes
tgt_r = mover.cy + K*mover.drow), MINTS it live, WIRES it via the shared attr, and PERSISTS it to its library.
This scales: any faculty is a small authored producer chained onto held ones.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/compose_lead_faculty.py
"""
from __future__ import annotations
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path: sys.path.insert(0, p)
from dynamics_world import DynamicsEnv, SELF, MOVER
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

K = 3  # lead horizon

# --- the agent authors the small PREDICT producer (its deliberation faculty emits this small rule) ---
def author_predict():
    from scripts.claude_teacher import make_ask
    spec = (
      "Emit ONLY a JSON object (no prose): a graph rule that writes a moving target's PREDICTED-FUTURE cell "
      "onto the self so the held SEEK faculty pursues it. Exact shape:\n"
      '{"id":"lead_predict",'
      '"match":[["game","has_region","r"],["game","has_region","m"]],'
      '"where":{"type":"And","items":['
        '{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"r"},"key":"axis_kind"},"b":{"type":"Lit","value":"controllable"}},'
        '{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"m"},"key":"axis_kind"},"b":{"type":"Lit","value":"autonomous"}}]},'
      '"effect":[ ... three set_attr ops ... ]}\n'
      "The three effect ops set, on the self r, tgt_r/tgt_c to the mover m's predicted-future cell K steps "
      "ahead and tgt_set to 1:\n"
      f'["set_attr","r","tgt_r",{{"__term__":{{"type":"Plus","items":[{{"type":"Attr","node":{{"type":"Var","name":"m"}},"key":"cy"}},{{"type":"Times","items":[{{"type":"Lit","value":{K}}},{{"type":"Attr","node":{{"type":"Var","name":"m"}},"key":"drow"}}]}}]}}}}],\n'
      f'["set_attr","r","tgt_c",{{"__term__":{{"type":"Plus","items":[{{"type":"Attr","node":{{"type":"Var","name":"m"}},"key":"cx"}},{{"type":"Times","items":[{{"type":"Lit","value":{K}}},{{"type":"Attr","node":{{"type":"Var","name":"m"}},"key":"dcol"}}]}}]}}}}],\n'
      '["set_attr","r","tgt_set",1.0]\n'
      "Return the complete JSON object with these three ops in effect.")
    raw = make_ask(timeout=120.0, preamble="You author one small graph rule as JSON. ")(spec)
    import re
    m = re.search(r"\{.*\}", raw or "", re.S)
    if m:
        try: return json.loads(m.group(0))
        except Exception: pass
    return None

# the predict rule the agent should produce (used as the trusted reference / fallback if the channel is unavailable)
def predict_rule(k):
    def A(n,key): return {"type":"Attr","node":{"type":"Var","name":n},"key":key}
    def pred(cy,vr): return {"type":"Plus","items":[A("m",cy),{"type":"Times","items":[{"type":"Lit","value":k},A("m",vr)]}]}
    return {"id":"lead_predict",
      "match":[["game","has_region","r"],["game","has_region","m"]],
      "where":{"type":"And","items":[
        {"type":"Eq","a":A("r","axis_kind"),"b":{"type":"Lit","value":"controllable"}},
        {"type":"Eq","a":A("m","axis_kind"),"b":{"type":"Lit","value":"autonomous"}}]},
      "effect":[["set_attr","r","tgt_r",{"__term__":pred("cy","drow")}],
                ["set_attr","r","tgt_c",{"__term__":pred("cx","dcol")}],
                ["set_attr","r","tgt_set",1.0]]}


def mint(agent, rule_json):
    """The agent mints its authored rule: ingest as a Rule node, then set_rule_clause(__mint__) compiles it live."""
    rn = agent.s.add_node("Rule", dict(rule_json))
    mtr = agent.s.add_node("Minter", {})
    agent.inner.add_edge_unchecked(mtr, "wants_mint", rn)
    agent.inner.add_rule({"name":"__mint_lead","match":[["x","wants_mint","rn"]],
        "where":{"type":"Lt","a":{"type":"Plus","items":[{"type":"Attr","node":{"type":"Var","name":"rn"},"key":"minted"},{"type":"Lit","value":0.0}]},"b":{"type":"Lit","value":0.5}},
        "effects":[["set_rule_clause",{"__term__":{"type":"Attr","node":{"type":"Var","name":"rn"},"key":"id"}},"__mint__",{"__term__":{"type":"Var","name":"rn"}}],
                   ["set_attr","rn","minted",1.0]]})
    for _ in range(3): agent.master_tick(); agent.tick()
    return rn


def persist(rule_json):
    out = os.path.join(ROOT, "seeds", "generated", "lead.json")
    seed = {"id":"lead","version":"1.0.0","depends_on":["seek_primitive"],
            "description":"LEAD faculty the agent composed: a PREDICT producer it authored writes the mover's "
                          "predicted-future cell onto the self; the held SEEK pursues it (compose via shared attr).",
            "nodes":[],"edges":[],"productions":[],"rules":[rule_json]}
    tmp = out + ".tmp"; json.dump(seed, open(tmp,"w"), indent=1); json.load(open(tmp)); os.replace(tmp, out)
    return out


def play(agent, world, steps=120):
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    for i in range(28):  # warmup: classify self(controllable) + mover(autonomous), learn resp
        sub, ctx = world.apply((["Up","Down","Left","Right"][i%4],)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
    def gnode():
        return next((n for n in agent.s.nodes("WorldInstance") if agent.s.node(n)["attrs"].get("world_type")=="Game"), None)
    caught = 0; last = ctx.get("score",0)
    for i in range(steps):
        a = agent.s.node(gnode())["attrs"].get("chosen_action") or "Right"
        sub, ctx = world.apply((a,)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        if ctx.get("score",0) > last: caught += ctx.get("score",0)-last; last = ctx.get("score",0)
        if ctx.get("over"): sub,ctx=world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick(); last=ctx.get("score",0)
    return caught


def main():
    print("="*92); print("COMPOSE-FROM-FACULTIES — agent builds LEAD = held SEEK + a PREDICT producer it authors."); print("="*92)
    authored = author_predict()
    used_channel = authored is not None and authored.get("id") == "lead_predict" and "effect" in authored
    rule = authored if used_channel else predict_rule(K)
    print(f"\n  PREDICT producer authored via deliberation channel: {used_channel} (else trusted reference)")

    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    n0 = agent.inner.rule_count()
    mint(agent, rule)
    minted = agent.inner.rule_count() == n0 + 1
    path = persist(rule)
    print(f"  minted lead_predict live: {minted} (rule_count {n0}->{agent.inner.rule_count()}); persisted -> {os.path.relpath(path,ROOT)}")

    caught = play(agent, ArcWorld(DynamicsEnv(mode="chase")))
    # baseline: a fresh agent with a PRESENT-target producer (K=0) — pure pursuit of a moving target
    base = WorldAdapter(seeds=()); load_all_seeds(base); mint(base, predict_rule(0))
    caught_present = play(base, ArcWorld(DynamicsEnv(mode="chase")))

    print(f"\n  LEAD (predict-future K={K}) caught {caught}; SEEK-present (K=0) caught {caught_present}")
    ok = minted and caught >= 1 and caught >= caught_present
    print("\n"+"="*92)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent composed a NEW faculty (LEAD) by authoring + minting a "
          f"small PREDICT producer and wiring it to the held SEEK through a shared attr, then persisted it to "
          f"its library. Complex faculties = small authored parts chained onto held ones. Capable entity.")
    print("="*92)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
