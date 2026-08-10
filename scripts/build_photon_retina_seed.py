"""Emit the graph-native photoreceptor/retinal-column rules."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "photon_retina.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Abs(x): return {"type": "Abs", "arg": x}
def Idx(seq, i): return {"type": "IndexAt", "seq": seq, "index": L(i)}


def set_if(var, key, value, computed=False):
    return ["set_attr_if_different", var, key, {"__term__": value} if computed else value]


RULES = [
    {
        "name": "photon_apply_receptor_transduction",
        "area": "retina",
        "order": 0,
        "latency_class": "hard_realtime",
        "match": [
            ["column", "has_receptor", "receptor"],
            ["receptor", "has_task", "task"],
        ],
        "where": And(
            Eq(A("task", "status"), L("done")),
            Not(Eq(A("task", "retina_applied"), L(1.0))),
        ),
        "effects": [
            set_if("receptor", "prev_activation", A("receptor", "activation"), True),
            set_if("receptor", "activation", Idx(A("task", "output"), 0), True),
            set_if("receptor", "adaptation", Idx(A("task", "output"), 1), True),
            set_if("receptor", "caught_quanta", Idx(A("task", "output"), 2), True),
            set_if("receptor", "input_epoch", A("task", "input_epoch"), True),
            set_if("task", "retina_applied", 1.0),
        ],
    },
    {
        "name": "photon_column_synthesizes_retinal_percept",
        "area": "retina",
        "order": 1,
        "latency_class": "hard_realtime",
        "match": [
            ["column", "rod_receptor", "rod"],
            ["column", "l_receptor", "l"],
            ["column", "m_receptor", "m"],
            ["column", "s_receptor", "s"],
            ["column", "has_retinal_percept", "percept"],
        ],
        "where": And(
            Gt(A("column", "input_epoch"), A("percept", "input_epoch")),
            Eq(A("rod", "input_epoch"), A("column", "input_epoch")),
            Eq(A("l", "input_epoch"), A("column", "input_epoch")),
            Eq(A("m", "input_epoch"), A("column", "input_epoch")),
            Eq(A("s", "input_epoch"), A("column", "input_epoch")),
        ),
        "effects": [
            set_if("percept", "intensity", Plus(
                Times(L(0.4), Plus(A("l", "activation"), A("m", "activation"))),
                Times(L(0.2), A("rod", "activation")),
            ), True),
            set_if("percept", "red_green", Minus(
                A("l", "activation"), A("m", "activation")), True),
            set_if("percept", "blue_yellow", Minus(
                A("s", "activation"),
                Times(L(0.5), Plus(A("l", "activation"), A("m", "activation"))),
            ), True),
            set_if("percept", "salience", Plus(
                Abs(Minus(A("rod", "activation"), A("rod", "prev_activation"))),
                Abs(Minus(A("l", "activation"), A("l", "prev_activation"))),
                Abs(Minus(A("m", "activation"), A("m", "prev_activation"))),
                Abs(Minus(A("s", "activation"), A("s", "prev_activation"))),
            ), True),
            set_if("percept", "input_epoch", A("column", "input_epoch"), True),
        ],
    },
]

MANIFEST = {
    "id": "photon_retina",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["cognitive_areas", "cognitive_scheduler"],
    "area": "retina",
    "description": (
        "Photon/biology visual floor. Integer photon packets drive typed "
        "rod/L/M/S photoreceptors through a native spectral-transduction task; "
        "adaptation persists in graph state; retinal columns synthesize "
        "intensity, opponent colour and temporal salience by graph rules. "
        "No RGB pixels, Sobel, Harris, Gaussian blur or contours enter cognition."
    ),
    "microtheory": {
        "name": "photon_retina",
        "description": "photon quanta -> adapting receptors -> opponent retinal field",
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {"provenance": "seed:photon_retina:retina-column",
         "src": {"type": "Retina", "var": "retina"},
         "edge_type": "has_column",
         "tgt": {"type": "RetinalColumn", "var": "column"}},
        {"provenance": "seed:photon_retina:retina-exposure",
         "src": {"type": "Retina", "var": "retina"},
         "edge_type": "has_exposure",
         "tgt": {"type": "PhotonExposure", "var": "exposure"}},
        {"provenance": "seed:photon_retina:column-receptor",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "has_receptor",
         "tgt": {"type": "Photoreceptor", "var": "receptor"}},
        {"provenance": "seed:photon_retina:column-rod",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "rod_receptor",
         "tgt": {"type": "Photoreceptor", "var": "receptor"}},
        {"provenance": "seed:photon_retina:column-l",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "l_receptor",
         "tgt": {"type": "Photoreceptor", "var": "receptor"}},
        {"provenance": "seed:photon_retina:column-m",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "m_receptor",
         "tgt": {"type": "Photoreceptor", "var": "receptor"}},
        {"provenance": "seed:photon_retina:column-s",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "s_receptor",
         "tgt": {"type": "Photoreceptor", "var": "receptor"}},
        {"provenance": "seed:photon_retina:column-percept",
         "src": {"type": "RetinalColumn", "var": "column"},
         "edge_type": "has_retinal_percept",
         "tgt": {"type": "RetinalPercept", "var": "percept"}},
        {"provenance": "seed:photon_retina:receptor-task",
         "src": {"type": "Photoreceptor", "var": "receptor"},
         "edge_type": "has_task",
         "tgt": {"type": "CognitiveTask", "var": "task"}},
    ],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
