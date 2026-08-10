"""Seed authoring tool: emit seeds/feature_discrimination.json — a GENERAL graph-native
discrimination over a Sense's labelled Exemplars, each carrying an L2-normalised feature
vector `feat`. distance(e1,e2) = |e1-e2|^2 = Dot(e1,e1) - 2 Dot(e1,e2) + Dot(e2,e2) (Dot is a
Rust DSL Term over array attrs). discrimination = (mean between-label dist - mean within-label
dist)/(between+within), scale-normalised. Used by ANY feature source (the cue-gating ear, etc.)
whose features the world lays as `feat` — the score is a Rust fold, no Python. Deletable tool."""
import json
import os

P = os.path.join(os.path.dirname(__file__), "..", "seeds", "feature_discrimination.json")

A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
N = lambda n, e: {"type": "Neighbours", "node": {"type": "Var", "name": n}, "edge_type": e, "any_type": False}
V = lambda n: {"type": "Var", "name": n}
Lc = lambda v: {"type": "Lit", "value": v}
Dot = lambda a, b: {"type": "Dot", "a": a, "b": b}


def distance(e1, e2):
    f1, f2 = A(e1, "feat"), A(e2, "feat")
    return {"type": "Minus",
            "a": {"type": "Plus", "items": [Dot(f1, f1), Dot(f2, f2)]},
            "b": {"type": "Times", "items": [Lc(2.0), Dot(f1, f2)]}}


def filt(pred):
    return {"type": "Filter", "source": N("sense", "has_exemplar"), "var_name": "e2", "predicate": pred}


same = {"type": "And", "items": [{"type": "Eq", "a": A("e1", "label"), "b": A("e2", "label")},
                                 {"type": "Not", "arg": {"type": "Eq", "a": V("e1"), "b": V("e2")}}]}
diff = {"type": "Not", "arg": {"type": "Eq", "a": A("e1", "label"), "b": A("e2", "label")}}


def sumd(pred):
    return {"type": "Sum", "source": N("sense", "has_exemplar"), "var_name": "e1",
            "value": {"type": "Sum", "source": filt(pred), "var_name": "e2", "value": distance("e1", "e2")}}


def cnt(pred):
    return {"type": "Sum", "source": N("sense", "has_exemplar"), "var_name": "e1",
            "value": {"type": "Count", "source": filt(pred)}}


between = {"type": "Div", "a": sumd(diff), "b": cnt(diff)}
within = {"type": "Div", "a": sumd(same), "b": cnt(same)}
disc = {"type": "Div", "a": {"type": "Minus", "a": between, "b": within},
        "b": {"type": "Plus", "items": [between, within, Lc(1e-6)]}}

seed = {
    "id": "feature_discrimination",
    "version": "1.0.0",
    "depends_on": [],
    "description": "GENERAL graph-native discrimination: score how well a Sense's labelled "
                   "Exemplars (each with an L2-normalised `feat` vector laid by the world) "
                   "separate by label. (mean between-label - mean within-label squared distance)"
                   "/(between+within); distance via the Rust Dot Term. No Python measurement — "
                   "the world lays the features (affordance), the GRAPH scores them.",
    "microtheory": {"name": "feature_discrimination",
                    "description": "between-within over labelled feature vectors; a Rust DSL fold."},
    "nodes": [{"local_id": 0, "type": "FeatureDisc",
               "attrs": {"name": "feature_discrimination", "discrimination_term": json.dumps(disc)}}],
    "edges": [],
    "productions": [
        {"provenance": "seed:feature_discrimination:has_exemplar",
         "src": {"type": "Sense", "var": "a"}, "edge_type": "has_exemplar",
         "tgt": {"type": "Exemplar", "var": "b"}}],
    "rules": []
}
json.dump(seed, open(P, "w"), indent=2)
print("ok: feature_discrimination.json, term len", len(seed["nodes"][0]["attrs"]["discrimination_term"]))
