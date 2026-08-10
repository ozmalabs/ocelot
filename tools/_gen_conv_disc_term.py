"""One-off seed authoring tool: add the GRAPH-NATIVE discrimination Term to the
sensory_convolution seed's ConvFaculty node. Deletable; emits seed data, not agent runtime."""
import json
import os

P = os.path.join(os.path.dirname(__file__), "..", "seeds", "sensory_convolution.json")
d = json.load(open(P))

A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
N = lambda n, e: {"type": "Neighbours", "node": {"type": "Var", "name": n}, "edge_type": e, "any_type": False}
V = lambda n: {"type": "Var", "name": n}
Lc = lambda v: {"type": "Lit", "value": v}


def resp(fv, pv):
    return {"type": "MaxOver", "source": N(fv, "has_patch"), "var_name": pv,
            "value": {"type": "Dot", "a": A("k", "weights"), "b": A(pv, "vals")}, "default": Lc(0.0)}


def distance(f1, f2):
    diff = {"type": "Minus", "a": resp(f1, "pa"), "b": resp(f2, "pb")}
    return {"type": "Sum", "source": N("sense", "kept_kernel"), "var_name": "k",
            "value": {"type": "Times", "items": [diff, diff]}}


def filt(pred):
    return {"type": "Filter", "source": N("sense", "has_field"), "var_name": "f2", "predicate": pred}


same = {"type": "And", "items": [{"type": "Eq", "a": A("f1", "label"), "b": A("f2", "label")},
                                 {"type": "Not", "arg": {"type": "Eq", "a": V("f1"), "b": V("f2")}}]}
diff = {"type": "Not", "arg": {"type": "Eq", "a": A("f1", "label"), "b": A("f2", "label")}}


def sumdist(pred):
    return {"type": "Sum", "source": N("sense", "has_field"), "var_name": "f1",
            "value": {"type": "Sum", "source": filt(pred), "var_name": "f2", "value": distance("f1", "f2")}}


def cnt(pred):
    return {"type": "Sum", "source": N("sense", "has_field"), "var_name": "f1",
            "value": {"type": "Count", "source": filt(pred)}}


between = {"type": "Div", "a": sumdist(diff), "b": cnt(diff)}
within = {"type": "Div", "a": sumdist(same), "b": cnt(same)}
disc = {"type": "Div", "a": {"type": "Minus", "a": between, "b": within},
        "b": {"type": "Plus", "items": [between, within, Lc(1e-6)]}}

fac = d["nodes"][0]
assert fac["type"] == "ConvFaculty", fac["type"]
fac["attrs"]["discrimination_term"] = json.dumps(disc)
fac["attrs"]["discrimination_comment"] = (
    "GRAPH-NATIVE discrimination over a Sense's labelled fields: (mean between-label dist - "
    "mean within-label dist) / (between + within), scale-normalised. dist(f1,f2) = Sum over "
    "kept_kernel of (conv_resp(f1,k)-conv_resp(f2,k))^2. A Rust DSL fold; no Python math.")
json.dump(d, open(P, "w"), indent=2)
print("ok: discrimination_term len", len(fac["attrs"]["discrimination_term"]))
