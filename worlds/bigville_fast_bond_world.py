"""BigvilleFastBondWorld -- isolates the TARGET-SENSITIVE FAST PATH (block 287000).
An actor co-present with several others (each held in a Bond) decides SHALLOW-ONLY
(deepen disabled), so ONLY the impulse decides. With fb_fast_bond the fast pull is
bond-directed (help@friend outpulls help@neutral); with fast_gain=0 the impulses tie
and the first-listed target wins -- the 282000-c failure. The adapter mints the
scene + reads; the nudge and the choice are seed rules. ZERO new Rust.
"""
from __future__ import annotations
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT,"runners","dsl","python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT,"runners","dsl","python"))
if _ROOT not in sys.path: sys.path.insert(0,_ROOT)
from domains.photon_eye import GraphEye
from substrate.seed_loader import manifest_for

_DIRECTED={"harm":0.20,"help":0.70,"transfer":0.50}
_DIR_PLAN={"harm":-0.40,"help":0.60,"transfer":0.55}
_DIR_EFFECT={"harm":-1.0,"help":1.0,"transfer":0.8}


class BigvilleFastBondWorld:
    """targets: ordered list of dict(name, affection=, resentment=). fast_gain nudges
    the shallow impulse by the cheap bond signal."""
    def __init__(self, targets, *, fast_gain=0.1, conduct_k=0.5, w_supergraph=1.0):
        self.eye=GraphEye(n_az=4,n_el=4,adapt_rate=0.15,
                          context={"retina_2d":True,"synchronous":True,"worker_capacity":1}).build()
        self.s=self.eye.substrate; self.inner=self.s._inner
        for seed in ("bigville_surprise_gate","bigville_fast_bond",
                     "bigville_supergraph_conduct","bigville_decision_core"):
            self.inner.load_seed_manifest(manifest_for(seed), self.eye._agent)
        self._opts=[]; self._by_code={}
        self._build(targets, fast_gain, conduct_k, w_supergraph)

    def _build(self, targets, fast_gain, conduct_k, w_supergraph):
        s,AE=self.s,self.inner.add_edge_unchecked
        m=s.add_node("ConductState",{"committed_action":"","conduct_k":conduct_k,
            "fast_gain":float(fast_gain),"consideration_threshold":0.05,"settle_tol":0.15,
            "deepen_enabled":0.0,"rationalise_gain":0.0,"replay_gain":0.0,"replay_eta":0.35})
        self.m=m
        ep=s.add_node("EmotionParams",{"w_supergraph":w_supergraph,"enabled":1.0}); AE(m,"has_ep",ep)
        self._person={}
        ix=0
        def mint(name,bw,plan,target=None):
            nonlocal ix
            at={"name":name,"index":float(ix),"code":float(ix),"base_value":bw,
                "base_weight":bw,"plan_value":plan,"plan_base":plan,"impulse":0.0,
                "afforded":0.0,"enacted":0.0,"is_transgressive":1.0 if name=="harm" else 0.0}
            if target is not None: at["target_effect"]=_DIR_EFFECT[name]
            d=s.add_node("DecAction",at); AE(m,"in_scene",d)
            if target is not None: AE(d,"aims_at",self._person[target])
            self._opts.append((ix,name,target,d)); self._by_code[ix]=(name,target); ix+=1
        mint("rest",0.15,0.20)
        for t in targets:
            nm=t["name"]; o=s.add_node("Person",{"name":nm,"health":100.0}); self._person[nm]=o
            AE(m,"sees",o)
            bond=s.add_node("Bond",{"affect_affection":float(t.get("affection",0.0)),
                "affect_resentment":float(t.get("resentment",0.0)),"altruism_bias":0.0})
            AE(m,"holds_bond",bond); AE(bond,"toward",o)
            for name,bw in _DIRECTED.items(): mint(name,bw,_DIR_PLAN[name],target=nm)
        n=ix
        asm=s.add_node("NetworkAssemblage",{"input_dim":n,"output_dim":n})
        sid=s.add_node("AssemblageStep",{"order":0,"dim_behavior":"transform"}); AE(asm,"has_step",sid)
        I=[[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
        for role,dat in {"W1":I,"b1":[0.0]*n,"W2":I,"b2":[0.0]*n}.items():
            AE(sid,"has_weight",s.add_node("WeightTensor",{"role":role,"data":dat}))
        rn=s.add_node("ReflexNet",{"name":"order0","status":"idle","enabled":1.0,"eta":0.5})
        AE(rn,"net_assemblage",asm); AE(m,"has_net",rn)
        s.set_attr(m,"input_vec",[0.0]*n); s.set_attr(m,"target_vec",[0.0]*n); self._n=n

    def decide(self):
        s=self.s; self.inner.run_rules()   # provision + fast_bond nudge + coupling
        vec=[0.0]*self._n
        for ix,_n,_t,d in self._opts: vec[ix]=float(s.node(d)["attrs"].get("impulse",0.0))
        s.set_attr(self.m,"input_vec",vec)
        s.set_attr(self.m,"target_vec",[float(s.node(d)["attrs"]["plan_value"]) for _i,_n,_t,d in self._opts])
        for f in ("collapse_armed","settle_check_armed","writeback_armed","done","deepened"):
            s.set_attr(self.m,f,0.0)
        s.set_attr(self.m,"collapse_armed",1.0); self.inner.run_rules()
        at=s.node(self.m)["attrs"]; code=int(round(float(at.get("chosen_code",-1.0))))
        name,target=self._by_code.get(code,(at.get("chosen_name"),None))
        return {"chosen":name,"target":target}

    def provide(self):
        self.inner.run_rules()

    def impulse(self,name,target):
        for ix,n_,t_,d in self._opts:
            if n_==name and t_==target: return round(float(self.s.node(d)["attrs"].get("impulse",0.0)),4)
        return None
    def close(self):
        try: self.eye.stop()
        except Exception: pass
