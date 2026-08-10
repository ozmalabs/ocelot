"""Seed authoring tool: add the GRAPH-NATIVE `keep_discriminative_cue` Rule + productions to
feature_discrimination.json. A CueGate `probes` one CueProbe per cue; each CueProbe
`has_exemplar` that cue's labelled responses. The Rule KEEPS a cue whose per-cue label
discrimination exceeds the MEAN across the gate's probes — the cue-selection effect-gate as a
Rust-evaluated Rule, not a Python loop. Deletable tool."""
import json
import os

P = os.path.join(os.path.dirname(__file__), "..", "seeds", "feature_discrimination.json")
d = json.load(open(P))

A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
N = lambda n, e: {"type": "Neighbours", "node": {"type": "Var", "name": n}, "edge_type": e, "any_type": False}
V = lambda n: {"type": "Var", "name": n}
Lc = lambda v: {"type": "Lit", "value": v}
Dot = lambda a, b: {"type": "Dot", "a": a, "b": b}


def distance(e1, e2):
    f1, f2 = A(e1, "feat"), A(e2, "feat")
    return {"type": "Minus", "a": {"type": "Plus", "items": [Dot(f1, f1), Dot(f2, f2)]},
            "b": {"type": "Times", "items": [Lc(2.0), Dot(f1, f2)]}}


def disc_for(pv, e1, e2):
    """The discrimination of the exemplars hanging off node `pv` (a CueProbe), using fresh
    pair-vars e1/e2 so nested copies don't shadow each other."""
    filt = lambda pred: {"type": "Filter", "source": N(pv, "has_exemplar"), "var_name": e2, "predicate": pred}
    same = {"type": "And", "items": [{"type": "Eq", "a": A(e1, "label"), "b": A(e2, "label")},
                                     {"type": "Not", "arg": {"type": "Eq", "a": V(e1), "b": V(e2)}}]}
    diff = {"type": "Not", "arg": {"type": "Eq", "a": A(e1, "label"), "b": A(e2, "label")}}
    sumd = lambda pred: {"type": "Sum", "source": N(pv, "has_exemplar"), "var_name": e1,
                         "value": {"type": "Sum", "source": filt(pred), "var_name": e2, "value": distance(e1, e2)}}
    cnt = lambda pred: {"type": "Sum", "source": N(pv, "has_exemplar"), "var_name": e1,
                        "value": {"type": "Count", "source": filt(pred)}}
    between = {"type": "Div", "a": sumd(diff), "b": cnt(diff)}
    within = {"type": "Div", "a": sumd(same), "b": cnt(same)}
    return {"type": "Div", "a": {"type": "Minus", "a": between, "b": within},
            "b": {"type": "Plus", "items": [between, within, Lc(1e-6)]}}


# mean per-cue discrimination across the gate's probes (use p2 + g1/g2 pair-vars inside).
mean_disc = {"type": "Div",
             "a": {"type": "Sum", "source": N("gate", "probes"), "var_name": "p2",
                   "value": disc_for("p2", "g1", "g2")},
             "b": {"type": "Count", "source": N("gate", "probes")}}

rule = {
    "name": "keep_discriminative_cue",
    "comment": "GRAPH-NATIVE cue selection (effect-gate). A CueGate probes one CueProbe per cue "
               "(each has_exemplar that cue's labelled responses, laid by the world). KEEP a cue "
               "whose per-cue label discrimination exceeds the mean across the gate's probes. The "
               "discrimination is the feature_discrimination fold; the KEEP is this Rule (Rust).",
    "match": [["gate", "probes", "probe"]],
    "where": {"type": "Gt", "a": disc_for("probe", "e1", "e2"), "b": mean_disc},
    "effects": [["add_edge", "gate", "kept_cue", "probe"]],
}

for e, src, tgt in (("probes", "CueGate", "CueProbe"),
                    ("has_exemplar", "CueProbe", "Exemplar"),
                    ("kept_cue", "CueGate", "CueProbe")):
    d["productions"].append({"provenance": f"seed:feature_discrimination:{e}",
                             "src": {"type": src, "var": "a"}, "edge_type": e,
                             "tgt": {"type": tgt, "var": "b"}})
d["rules"] = [rule]
json.dump(d, open(P, "w"), indent=2)
print("ok: keep_discriminative_cue rule added; productions", len(d["productions"]))
