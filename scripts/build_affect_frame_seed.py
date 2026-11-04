#!/usr/bin/env python3
"""BUILDER for seeds/affect_frame.json (seed block 369000).

Emits the opt-in AFFECT FRAME seed. Each fired emotion publishes one integer
affect frame: an Observation of single-slot relations (`aff:<tag>:val_sign`,
`aff:<tag>:val_level`, `aff:<tag>:ar_level`). The frame's levels are
LogQuantum (base 2) of the emotion's existing magnitudes. The unchanged sd loop
(seeds/shape_decode_loop.json) decodes each frame against a codebook of twelve
ShapeSignature parts. One rule, `af_direction`, writes the valence and arousal
direction between two successive appraisals.

Design and predictions: docs/research/psychology_affect/AFFECT_FRAME_CODEBOOK_PREREG.md
(sections 2 and 4). The emitted rules are graph data. The codebook is not typed by
hand: it is copied from the frames that the canonical appraisals of
scripts/core_emotions_measure.py produce once this seed's rules are loaded.
No Rust and no Python decision.

Run from the worktree root:
    OZMA_SEED_PERSIST_DISABLED=1 <venv python> scripts/build_affect_frame_seed.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "affect_frame.json")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()


# ---------------------------------------------------------------- Term helpers
def A(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def L(v):
    return {"type": "Lit", "value": float(v)}


def L_str(s):
    return {"type": "Lit", "value": s}


def L_none():
    return {"type": "Lit", "value": None}


def Eq(a, b):   return {"type": "Eq", "a": a, "b": b}
def Gt(a, b):   return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):   return {"type": "Lt", "a": a, "b": b}
def And(*it):   return {"type": "And", "items": list(it)}
def Or(*it):    return {"type": "Or", "items": list(it)}
def Not(x):     return {"type": "Not", "arg": x}
def Plus(*it):  return {"type": "Plus", "items": list(it)}
def Minus(a, b):return {"type": "Minus", "a": a, "b": b}
def Times(*it): return {"type": "Times", "items": list(it)}
def Abs(x):     return {"type": "Abs", "arg": x}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def Vec(*items):
    return {"type": "Vec", "items": list(items)}


def IndexAt(seq, i):
    # Index is an int literal, as autonomous_discovery.json writes it.
    return {"type": "IndexAt", "seq": seq, "index": {"type": "Lit", "value": i}}


def Nbrs(node_var, edge):
    return {"type": "Neighbours", "node": {"type": "Var", "name": node_var},
            "edge_type": edge, "any_type": False}


def Count(src):
    return {"type": "Count", "source": src}


def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}


def LQ(x):
    """Integer log2 level of term x: round(log2 x) via LogQuantum (raw, base 2, delta 1).

    The population is one frame holding one relation [pred, x]. LogQuantum returns the
    same nesting with x replaced by its level. Three IndexAt steps unwrap it:
    population -> frame -> relation -> level.
    """
    lq = {"type": "LogQuantum",
          "population": Vec(Vec(Vec(L_str("x"), x))),
          "value_slot": 1, "base_num": 2, "base_den": 1,
          "delta_num": 1, "delta_den": 1, "raw": True}
    return IndexAt(IndexAt(IndexAt(lq, 0), 0), 1)


ENABLED = Eq(A("ep", "enabled"), L(1))


def fires(tag):
    if tag == "none":
        return And(Eq(A("ap", "n_fired"), L(0)), Eq(A("ap", "appraised"), L(1)))
    return Eq(A("ap", "hit_" + tag), L(1))


# ------------------------------------------------------------- affect table
# (tag, val_sign, val_level source or None, ar_level source). prereg section 2.3.
TABLE = [
    ("surprise",    0, None,                                   lambda: A("ap", "residual")),
    ("fear",       -1, None,                                   lambda: A("ap", "threat_precision")),
    ("anxiety",    -1, None,                                   lambda: A("ap", "threat_precision")),
    ("anger",      -1, None,                                   lambda: A("ep", "high_arousal")),
    ("frustration",-1, None,                                   lambda: A("ep", "high_arousal")),
    ("disgust",    -1, None,                                   lambda: A("ep", "mid_arousal")),
    ("joy",         1, lambda: A("ap", "value_progress"),      lambda: A("ap", "value_progress")),
    ("sadness",    -1, lambda: Abs(A("ap", "value_progress")), lambda: A("ep", "low_arousal")),
    ("curiosity",   1, lambda: A("ap", "learning_progress"),   lambda: A("ap", "learning_progress")),
    ("boredom",    -1, None,                                   lambda: A("ep", "low_arousal")),
    ("fulfilment",  1, lambda: Abs(A("ap", "weighted_contribution")),
                                                               lambda: Abs(A("ap", "weighted_contribution"))),
    ("none",        0, None,                                   lambda: A("ep", "low_arousal")),
]

# Codebook order: the 11 emotions, then `none`. The same canonical appraisal per tag as
# scripts/core_emotions_measure.py CANON (`none` is appraised=1 alone).
CODEBOOK_TAGS = [row[0] for row in TABLE]

# Install after core_emotions' readoff (order 9) so that hit_* and n_fired are settled.
EMIT_ORDER = 10
DIRECTION_ORDER = 11


def emit_rule(tag, sign, val_src, ar_src):
    sig = [Vec(L_str("aff:%s:val_sign" % tag), L(sign))]
    attrs = {
        "status": "pending",
        "aff_tag": tag,
        "key": {"__term__": Vec(L_str("affect"), L_str(tag))},
        "val_sign": sign,
    }
    if val_src is not None:
        attrs["val_level"] = {"__term__": LQ(val_src())}
        sig.append(Vec(L_str("aff:%s:val_level" % tag), LQ(val_src())))
    attrs["ar_level"] = {"__term__": LQ(ar_src())}
    sig.append(Vec(L_str("aff:%s:ar_level" % tag), LQ(ar_src())))
    attrs["signature"] = {"__term__": Vec(*sig)}
    where = And(ENABLED, fires(tag),
                Not(Exists(Nbrs("ap", "has_affect_frame"), "fx",
                           Eq(A("fx", "aff_tag"), L_str(tag)))))
    return {
        "name": "af_emit_" + tag,
        "area": "retina",
        "order": EMIT_ORDER,
        "latency_class": "hard_realtime",
        "match": [["ag", "has_emotion_hub", "hub"],
                  ["hub", "has_emotion_params", "ep"],
                  ["hub", "has_appraisal", "ap"]],
        "where": where,
        "effects": [
            ["add_node", "f", "Observation", attrs],
            ["add_edge", "ap", "has_affect_frame", "f"],
            ["add_edge", "ag", "observed", "f"],
        ],
    }


def K(f):
    """Signed log coordinate: val_sign * (val_level + 1), or val_sign when no level."""
    return Ite(Eq(A(f, "val_level"), L_none()),
               A(f, "val_sign"),
               Times(A(f, "val_sign"), Plus(A(f, "val_level"), L(1))))


def cmp3(a, b):
    return Ite(Gt(a, b), L(1), Ite(Lt(a, b), L(-1), L(0)))


direction_rule = {
    "name": "af_direction",
    "area": "retina",
    "order": DIRECTION_ORDER,
    "latency_class": "hard_realtime",
    "match": [["ap2", "follows", "ap1"],
              ["ap1", "has_affect_frame", "f1"],
              ["ap2", "has_affect_frame", "f2"]],
    "where": And(Eq(Count(Nbrs("ap1", "has_affect_frame")), L(1)),
                 Eq(Count(Nbrs("ap2", "has_affect_frame")), L(1))),
    "effects": [
        ["set_attr", "ap2", "val_direction", {"__term__": cmp3(K("f2"), K("f1"))}],
        ["set_attr", "ap2", "ar_direction",
         {"__term__": cmp3(A("f2", "ar_level"), A("f1", "ar_level"))}],
    ],
}

RULES = [emit_rule(tag, sign, vs, ars) for tag, sign, vs, ars in TABLE] + [direction_rule]

PRODUCTIONS = [
    {"provenance": "seed:affect_frame:agent-emotion-hub",
     "src": {"type": "Agent", "var": "ag"},
     "edge_type": "has_emotion_hub",
     "tgt": {"type": "EmotionHub", "var": "hub"}},
    {"provenance": "seed:affect_frame:appraisal-frame",
     "src": {"type": "Appraisal", "var": "ap"},
     "edge_type": "has_affect_frame",
     "tgt": {"type": "Observation", "var": "f"}},
    {"provenance": "seed:affect_frame:appraisal-follows",
     "src": {"type": "Appraisal", "var": "ap2"},
     "edge_type": "follows",
     "tgt": {"type": "Appraisal", "var": "ap1"}},
]

DESCRIPTION = (
    "AFFECT FRAME + CODEBOOK (block 369000; design and predictions in "
    "docs/research/psychology_affect/AFFECT_FRAME_CODEBOOK_PREREG.md). Each fired "
    "emotion of core_emotions publishes one integer affect frame, an Observation of "
    "relations aff:<tag>:val_sign, aff:<tag>:val_level and aff:<tag>:ar_level, whose "
    "levels are LogQuantum base-2 log levels of the emotion's own magnitudes. The "
    "unchanged shape_decode_loop decodes each frame against twelve affect ShapeSignature "
    "parts (the codebook, copied from the canonical appraisals' frames). An intensity "
    "change arrives as a per-predicate quantum delta and is recognised as "
    "recognized_transformed with no growth. The af_direction rule compares the frames of "
    "two successive appraisals (follows edge) and writes val_direction and ar_direction. "
    "Opt-in and self_load_only: no existing seed is changed, and the old valence/arousal "
    "contract is untouched. No Rust, no Python decision."
)


def _plain(x):
    """Tuples to lists, recursively, so the codebook signature is JSON."""
    if isinstance(x, (list, tuple)):
        return [_plain(i) for i in x]
    return x


def _canonical_kwargs(tag):
    from scripts import core_emotions_measure as M
    if tag == "none":
        return dict(appraised=1)
    return dict(M.CANON[tag])


def derive_codebook(base_manifest):
    """Boot the core_emotions harness with the rules, appraise each canonical tag, and copy
    the single frame's signature. Returns the ShapeSignature nodes for the codebook."""
    from scripts import core_emotions_measure as M
    from domains.reflective_faculty import _ensure_shape_decode_loop

    eye, inner = M._eye()
    try:
        _ensure_shape_decode_loop(eye.substrate, inner, eye._agent)
        inner.load_seed_manifest(base_manifest, eye._agent)
        nodes = []
        for i, tag in enumerate(CODEBOOK_TAGS, start=1):
            hub, _ = M._hub(eye, inner)
            inner.add_edge_unchecked(eye._agent, "has_emotion_hub", hub)
            ap = M._appraise(eye, inner, hub, **_canonical_kwargs(tag))
            inner.run_rules()
            frames = inner.neighbours(ap, "has_affect_frame")
            if len(frames) != 1:
                raise SystemExit("STOP: tag %s produced %d frames, expected 1" % (tag, len(frames)))
            attrs = eye.substrate.node(frames[0])["attrs"]
            sig = _plain(attrs["signature"])
            # VERBATIM copy (prereg §2.3): the native relation list, not a JSON string.
            # Run 1 stored json.dumps(sig) and failed G-2: sd_recognize's covered_by scores
            # parts with FixedCount(AntiUnify(obs.signature, sig.signature)), which sees a
            # JSON-string signature as one opaque string, so every part tied at 0.
            nodes.append({
                "local_id": i,
                "type": "ShapeSignature",
                "attrs": {"name": "affect:" + tag, "kind": "affect",
                          "signature": sig},
            })
        return nodes
    finally:
        eye.stop()


def main():
    base = {
        "id": "affect_frame",
        "version": "0.1.0",
        "self_load_only": True,
        "depends_on": ["core_emotions", "shape_decode_loop"],
        "area": "retina",
        "description": DESCRIPTION,
        "nodes": [],
        "edges": [],
        "productions": PRODUCTIONS,
        "rules": RULES,
    }
    # Step 2: the manifest without codebook nodes goes to a temp file, and is read back.
    fd, tmp = tempfile.mkstemp(prefix="affect_frame_base_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(base, fh, indent=1)
        with open(tmp) as fh:
            base_loaded = json.load(fh)
        codebook = derive_codebook(base_loaded)
    finally:
        os.remove(tmp)

    manifest = dict(base)
    manifest["nodes"] = codebook
    with open(OUT, "w") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    print("wrote", OUT, "-", len(codebook), "codebook nodes,",
          len(RULES), "rules,", len(PRODUCTIONS), "productions")


if __name__ == "__main__":
    main()
