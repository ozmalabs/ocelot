#!/usr/bin/env python3
"""Emit seeds/vision_grain_policy.json (tranche 4).

The held-generator grain ladder (shape_decode_loop v1.14.0, agent.dim_grains)
was confirmed on held-out Omniglot alphabets (SUBSTRATE_DIMINFER_GRAIN_HELDOUT_V1:
60/100 jittered vs 0/100, 0/100 cross-character). This seed makes it the
default FOR VISION ROUTES as graph data: one rule sets agent.dim_grains to
the policy's grains when the agent has none. Any explicit agent setting wins;
loading this seed is the route's opt-in (domains.reflective_faculty.
_ensure_vision_grain_policy). Not a core seed.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = lambda n: {"type": "Var", "name": n}
A = lambda n, k: {"type": "Attr", "node": V(n), "key": k}
L = lambda v: {"type": "Lit", "value": v}
seed = {
    "id": "vision_grain_policy", "version": "1.0.0", "self_load_only": True,
    "depends_on": ["shape_decode_loop"], "description": __doc__,
    "nodes": [{"local_id": 0, "type": "VisionGrainPolicy",
               "attrs": {"name": "vision_held_generator_grains", "dim_grains": [0, 1, 2],
                         "evidence": "SUBSTRATE_DIMINFER_GRAIN_HELDOUT_V1_RESULTS (tranche 3)"}}],
    "edges": [{"src": {"role": "agent_root"}, "type": "has_vision_grain_policy", "tgt": {"local": 0}, "attrs": {}}],
    "productions": [],
    "rules": [{
        "name": "vg_apply_vision_grain_policy",
        "comment": "Vision route default: copy the policy's dim_grains onto the agent once, only when the agent has no explicit dim_grains.",
        "match": [["ag", "has_vision_grain_policy", "vp"]],
        "where": {"type": "Eq", "a": A("ag", "dim_grains"), "b": L(None)},
        "effects": [["set_attr", "ag", "dim_grains", {"__term__": A("vp", "dim_grains")}]],
    }],
}
(ROOT / "seeds/vision_grain_policy.json").write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("wrote seeds/vision_grain_policy.json")
