"""Dynamic, relevance-weighted reasoning depth — the agent weighs whether a
deep dive is worth it. Same hard query resolves DEEP under HIGH relevance and
is capped SHALLOW under LOW relevance; a stalling dive abandons early (jROL).
Per user: 'the speed of the process should be order-N weighted and dynamic —
the agent should be able to weight the relevance of a deep dive.'  Honest: the
relevance/budget/jROL numbers are CALIBRATABLE weights; the win is the mechanism.
"""
import sys; sys.path.insert(0, ".")
from substrate_rs import _native
from domains import dynamic_depth as dd

def fresh():
    s = _native.Substrate()
    for a in ("KnownFact",):
        for b in ("KnownFact","Concept","DepthDecision","ReasoningChain"):
            for et in ("frame_role","fact_event","composed_fact","has_depth_decision"):
                try: s.add_production({"src":{"type":a,"var":"x"},"edge_type":et,
                    "tgt":{"type":b,"var":"y"},"where":None,
                    "weight":{"type":"Lit","value":1.0},"provenance":"t"})
                except Exception: pass
    return s

def fact(s, **slots): return s.add_node("KnownFact", slots)

print(dd.weights_snapshot()); print()

# A genuine 3-hop chain: alice -know-> bob -know-> carol -live-> rome
def build():
    s=fresh()
    fact(s, event="know", agent="alice", patient="bob")
    fact(s, event="know", agent="bob",   patient="carol")
    fact(s, event="live", agent="carol", location="rome")
    return s

q = {"queried_relation":"live","queried_slot":"location","anchor":"alice",
     "agent":"alice"}

print("="*70); print("SAME hard 3-hop query at HIGH vs LOW relevance"); print("="*70)
for flag,label in [({"_asked":True},"HIGH (the asked question)"),
                   ({"_immaterial":True},"LOW (immaterial aside)")]:
    s=build()
    query=dict(q, **flag)
    rel=dd.relevance(query)
    bud=dd.depth_budget(rel)
    out=dd.reason_dynamic(s,"alice","live","location",anchor_slot="agent",budget=bud)
    ans=(out or {}).get("answer") if out else None
    print(f"\n{label}")
    print(f"  relevance: {rel['band']} ({rel['score']})  budget: max_order={bud['max_order']} "
          f"tiers={bud['ref_tiers']}")
    print(f"  -> answer={ans!r}  order_reached={(out or {}).get('order_reached') or (out or {}).get('order')}  "
          f"stop={(out or {}).get('stop_reason')}")

print("\n"+"="*70); print("PERSEVERANCE: a stalling dive abandons early (jROL)"); print("="*70)
# facts that DON'T chain to the query -> chains stall -> early stop before max_order
s=fresh()
fact(s, event="know", agent="alice", patient="bob")
fact(s, event="own",  agent="zoe",   patient="hat")   # disconnected
q2=dict(q,_asked=True)  # HIGH relevance => big budget, but no chain
bud=dd.depth_budget(dd.relevance(q2))
out=dd.reason_dynamic(s,"alice","live","location",anchor_slot="agent",budget=bud)
print(f"  HIGH relevance budget max_order={bud['max_order']}, but no chain ->")
print(f"  answer={(out or {}).get('answer')}  order_reached={(out or {}).get('order_reached')}  "
      f"stop={(out or {}).get('stop_reason')}  (abandoned before max_order={bud['max_order']})")
print("\nOK")
