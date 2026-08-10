"""build_pattern_recognition_seed — a GENERIC shape/pattern recognition mechanism (block
209000). We are building an EYE that happens to work in Doom, NOT a Doom-playing eye.

The mechanism is domain-free and integer-native:
  * A `PatternLibrary` holds `PatternPrototype`s. Each prototype is a HELD pattern: an
    integer descriptor (here 2-D: [geometry_level, texture_level], each a quantised 0..K
    level from the eye), a label, a tier, and (optionally) an affordance. Prototypes are
    graph DATA — add one and the same rules recognise it. `door` / `switch` are just two
    entries (competent-man domain bootstrap); `background` (plain surface) and the coarse
    family `operable_feature` are others.
  * SALIENCE is GENERIC NOVELTY: a perceived region whose descriptor is far (integer L1)
    from the nearest BACKGROUND prototype is under-compressed -> salient. A region that
    matches the background reads ~0 -> not salient (the false-positive control is intrinsic).
  * RECOGNITION is GENERIC NEAREST-PROTOTYPE (the `figure_geometric_shape` idiom, made
    integer): a salient region is matched to a prototype by integer L1 descriptor distance
    under the prototype's threshold. Scramble a prototype's descriptor -> its recognition
    fails (the held pattern does the work, not a hardcoded detector).
  * INVESTIGATION is GENERIC: a recognised prototype that carries an affordance mints a Goal.

Two tiers make "spotting a different kind of thing" (easy, FAR) separate from naming it
(harder, NEAR): a COARSE family prototype is matched on distinctness alone; FINE prototypes
(door/switch) need R.near=1 (enough resolvable detail, set by the eye on approach).

ALL arithmetic is integer (Plus/Minus/Abs/Gte/Lt) — descriptors are integer quanta
(in-frame observations are integer; only cross-frame maps are continuous). No float, no
Python decision: the eye emits integer quanta, every decision is a rule.

    python3 scripts/build_pattern_recognition_seed.py   # -> seeds/pattern_recognition.json
"""
from __future__ import annotations
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "pattern_recognition.json")

K = 8  # descriptor levels 0..K


def var(n): return {"type": "Var", "name": n}
def attr(n, k): return {"type": "Attr", "node": var(n), "key": k}
def lit(v): return {"type": "Lit", "value": v}
def plus(*xs): return {"type": "Plus", "items": list(xs)}
def minus(a, b): return {"type": "Minus", "a": a, "b": b}
def abst(a): return {"type": "Abs", "arg": a}
def eq(a, b): return {"type": "Eq", "a": a, "b": b}
def neq(a, b): return {"type": "Not", "arg": eq(a, b)}
def gte(a, b): return {"type": "Gte", "a": a, "b": b}
def lt(a, b): return {"type": "Lt", "a": a, "b": b}
def andt(*xs): return {"type": "And", "items": list(xs)}
def T(term): return {"__term__": term}


def l1(rg, rt, cg, ct):
    """Integer L1 (Manhattan) descriptor distance |Rg-Cg| + |Rt-Ct|."""
    return plus(abst(minus(rg, cg)), abst(minus(rt, ct)))


def build():
    nodes = [{"local_id": 1, "type": "PatternLibrary", "attrs": {"name": "pattern_library"}}]

    # ---- HELD prototypes (graph DATA; the mechanism is generic) ------------------
    # descriptor = [geometry_level, texture_level], integer 0..K.
    protos = [
        # background: the expected plain surface. Salience = novelty vs this.
        (2, "background", "background", 0, 0, None, None, None),
        # coarse family: "an operable feature" == a DIFFERENT KIND OF THING than background.
        #   recognised FAR on distinctness alone (min_distinctness), no fine descriptor needed.
        (3, "operable_feature", "coarse", 4, 6, "worth_approaching", "approach", 2),
        # fine members (competent-man): door = framed/recessed geometry + marked surface;
        #   switch = marked surface, ~flush geometry, REMOTE effect.
        (4, "door", "fine", 4, 6, "gates_passage", "use", 3),
        (5, "switch", "fine", 0, 6, "changes_remote_sector", "use", 3),
    ]
    edges = []
    for lid, name, tier, g, t, aff, act, thr in protos:
        a = {"name": name, "label": name, "tier": tier,
             "geom_sig": g, "tex_sig": t, "descriptor_vec": [g, t]}
        if tier == "coarse":
            a["min_distinctness"] = thr
            a["operate_action"] = act; a["affordance"] = aff; a["effect_locality"] = "unknown"
        if tier == "fine":
            a["match_thresh"] = thr; a["affordance"] = aff; a["operate_action"] = act
            a["effect_locality"] = "local" if name == "door" else "remote"
        nodes.append({"local_id": lid, "type": "PatternPrototype", "attrs": a})
        edges.append({"src": {"local": 1}, "tgt": {"local": lid}, "type": "has_prototype", "attrs": {}})

    productions = []
    def prod(prov, s_t, s_v, et, t_t, t_v):
        productions.append({"provenance": prov, "src": {"type": s_t, "var": s_v},
                            "edge_type": et, "tgt": {"type": t_t, "var": t_v}})
    prod("seed:pattern:params", "WorldInstance", "game", "has_pattern_params", "PatternParams", "p")
    prod("seed:pattern:region", "WorldInstance", "game", "has_perceived_region", "PerceivedRegion", "R")
    prod("seed:pattern:lib", "WorldInstance", "game", "has_pattern_library", "PatternLibrary", "lib")
    prod("seed:pattern:has_proto", "PatternLibrary", "lib", "has_prototype", "PatternPrototype", "C")
    prod("seed:pattern:recognised", "PerceivedRegion", "R", "recognised_prototype", "PatternPrototype", "C")
    prod("seed:pattern:goal", "WorldInstance", "game", "has_pattern_goal", "Investigation", "inv")
    prod("seed:pattern:investigates", "Investigation", "inv", "investigates", "PerceivedRegion", "R")

    rules = []

    # (a) SALIENCE = generic novelty: integer L1 distance of the region descriptor from the
    #     BACKGROUND prototype. background ([0,0]) match -> ~0 -> not salient (false-positive
    #     control is intrinsic and integer). Gated on PatternParams (OFF by default).
    rules.append({
        "name": "pattern_salience", "area": "vision", "order": 3, "latency_class": "deferred",
        "match": [["game", "has_pattern_params", "p"], ["game", "has_pattern_library", "lib"],
                  ["lib", "has_prototype", "BG"], ["game", "has_perceived_region", "R"]],
        "where": andt(
            eq(attr("p", "enabled"), lit(1.0)),
            eq(attr("BG", "tier"), lit("background")),
            neq(attr("R", "sal_done"), lit(1.0))),
        "effects": [
            ["set_attr", "R", "salience",
                T(l1(attr("R", "geom_level"), attr("R", "tex_level"),
                     attr("BG", "geom_sig"), attr("BG", "tex_sig")))],
            ["set_attr", "R", "salient", T({"type": "IfThenElse",
                "cond": gte(l1(attr("R", "geom_level"), attr("R", "tex_level"),
                              attr("BG", "geom_sig"), attr("BG", "tex_sig")),
                            attr("p", "salience_floor")),
                "then": lit(1.0), "other": lit(0.0)})],
            ["set_attr", "R", "sal_done", T(lit(1.0))]]})

    # (b) COARSE recognition (FAR, easy) — a salient region whose distinctness clears the
    #     family prototype's bar IS an `operable_feature` (candidate). Held affordance mints
    #     an APPROACH goal (go look closer to name it).
    rules.append({
        "name": "pattern_recognise_coarse", "area": "vision", "order": 4, "latency_class": "deferred",
        "match": [["game", "has_pattern_library", "lib"], ["lib", "has_prototype", "C"],
                  ["game", "has_perceived_region", "R"]],
        "where": andt(
            eq(attr("C", "tier"), lit("coarse")),
            eq(attr("R", "salient"), lit(1.0)),
            neq(attr("R", "coarse_done"), lit(1.0)),
            gte(attr("R", "salience"), attr("C", "min_distinctness"))),
        "effects": [
            ["set_attr", "R", "recognised_family", T(attr("C", "name"))],
            ["set_attr", "R", "coarse_done", T(lit(1.0))],
            ["add_node", "inv", "Investigation", {
                "kind": "approach_to_resolve", "target_concept": T(attr("C", "name")),
                "action": T(attr("C", "operate_action")), "locality": T(attr("C", "effect_locality")),
                "status": "planned"}],
            ["add_edge", "game", "has_pattern_goal", "inv"],
            ["add_edge", "inv", "investigates", "R"]]})

    # (c) FINE recognition (NEAR, harder) — up close (R.near=1) the salient region is matched
    #     to the nearest FINE prototype by integer L1 distance under its threshold. Scramble a
    #     prototype descriptor -> distance blows up -> no match (the HELD pattern does the work).
    rules.append({
        "name": "pattern_recognise_fine", "area": "vision", "order": 5, "latency_class": "deferred",
        "match": [["game", "has_pattern_library", "lib"], ["lib", "has_prototype", "C"],
                  ["game", "has_perceived_region", "R"]],
        "where": andt(
            eq(attr("C", "tier"), lit("fine")),
            eq(attr("R", "salient"), lit(1.0)),
            eq(attr("R", "near"), lit(1.0)),
            neq(attr("R", "recognised"), lit(1.0)),
            lt(l1(attr("R", "geom_level"), attr("R", "tex_level"),
                  attr("C", "geom_sig"), attr("C", "tex_sig")),
               attr("C", "match_thresh"))),
        "effects": [
            ["add_edge", "R", "recognised_prototype", "C"],
            ["set_attr", "R", "recognised_as", T(attr("C", "name"))],
            ["set_attr", "R", "recognised", T(lit(1.0))],
            ["set_attr", "R", "recog_affordance", T(attr("C", "affordance"))]]})

    # (d) INVESTIGATION — a FINE recognition + a held affordance mints an OPERATE goal.
    rules.append({
        "name": "pattern_investigate_operate", "area": "vision", "order": 6, "latency_class": "deferred",
        "match": [["game", "has_perceived_region", "R"], ["R", "recognised_prototype", "C"]],
        "where": andt(
            eq(attr("R", "recognised"), lit(1.0)),
            neq(attr("R", "investigated"), lit(1.0))),
        "effects": [
            ["add_node", "inv", "Investigation", {
                "kind": "operate", "target_concept": T(attr("C", "name")),
                "action": T(attr("C", "operate_action")), "locality": T(attr("C", "effect_locality")),
                "status": "planned"}],
            ["add_edge", "game", "has_pattern_goal", "inv"],
            ["add_edge", "inv", "investigates", "R"],
            ["set_attr", "R", "investigated", T(lit(1.0))]]})

    return {
        "id": "pattern_recognition", "version": "1.0.0", "self_load_only": True,
        "depends_on": [], "area": "vision",
        "description": ("GENERIC integer-native shape/pattern recognition: a PatternLibrary of "
                        "HELD PatternPrototypes (integer descriptors), generic novelty-salience "
                        "(L1 distance from a background prototype), generic nearest-prototype "
                        "recognition (coarse family FAR, fine members NEAR), and affordance-driven "
                        "investigation. door/switch/background/operable_feature are library DATA; "
                        "the mechanism is domain-free. OFF by default (gated on a PatternParams node)."),
        "microtheory": "perception",
        "nodes": nodes, "edges": edges, "productions": productions, "rules": rules,
    }


if __name__ == "__main__":
    seed = build()
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=2)
    print("wrote", OUT, "-", len(seed["nodes"]), "prototypes+lib,", len(seed["rules"]), "generic rules")
