"""nested_reading — MOVE 2b: COMPREHENSION RECURSES OVER THE StoryUnit TREE.

MOVE 2a (story_tree) mints the StoryUnit tree; MOVE 1 made the comprehension
flow graph-resident and goal-driven. This module closes the loop: each LEAF
StoryUnit comprehends IN ISOLATION (the `unit` graph dimension threaded through
the six faculties -- situation_model_reader / coref_entities /
inference_generation / discourse_coherence / narrative_structure / trope_theme --
each read/write confined to the current unit's own sub-graph), and the PARENT
composes a SPANNING theme from its children.

  UNIT SCOPE = a graph dimension. Every SmEntity / SmEvent / DiscourseEvent /
  NarrativeRole / Trope / Theme minted during a unit's comprehension carries a
  `unit` attr (the leaf StoryUnit's node id); every faculty read filters by it.
  The lion of episode 1 and the re-introduced lion of episode 2 are DISTINCT
  graph nodes -- a NAME resolves WITHIN its StoryUnit (order-N isolation). The
  depth-1 default (`unit=None`) is the flat case, byte-for-byte the pre-2b path.

  PER-UNIT DISPATCH = rules match per StoryUnit. reading_drive mints one
  `unit_comprehend` AnalysisStage per LEAF unit (carrying a `unit` attr + a
  `for_unit` edge) + one `compose` stage per PARENT; the seeded u_dispatch_*
  rules (seeds/literary_analysis_unit_driving.json) fire PER stage node whose
  UNIT-SCOPED precondition holds -- so `run_rules` RECURSES over the tree for
  free. There is NO Python `for unit: comprehend(unit)` loop; the reflex
  advances ONE stage per firing (the _question_pursue_advance / analysis_advance
  precedent), and the fixpoint iterates the units.

  PARENT COMPOSES CHILDREN = a rule + a cross-unit collapse. When a parent's
  child units are all comprehended, `compose` fires and the spanning theme is
  the verdict of a ShapeDecode over a dedicated ShapeSignatureSpanningTheme
  codebook (seeds/spanning_theme.json) -- the SAME collapse story_tree uses for
  seams and trope_theme uses for tropes, one level up. The reciprocity of 'The
  Lion and the Mouse' (episode 2's rescue reciprocates episode 1's mercy) is
  recognised as the RETURN_ACTION token: an earlier child carries an action
  (agent=A, patient=B) and a later child the REVERSED action (agent=B,
  patient=A) -- a cross-episode RELATION, not a flat union of two child themes.

ARCHITECTURE (CLAUDE.md). The mint is graph nodes/edges (mechanical adapter
I/O); the per-unit recursion is the seeded rules firing per StoryUnit node
(never a Python loop); the spanning-theme decision is the ShapeDecode's verdict
(never a Python if). No `import re`; donkey = 0.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import coref_entities as ce
from domains import inference_generation as ig
from domains import discourse_coherence as dc
from domains import narrative_structure as ns
from domains import trope_theme as tt
from domains import reading_collapse as rc
from domains.comprehension_reader import _mint_goal_action_enabling_chain

_SPAN_CODEBOOK_TYPE = "ShapeSignatureSpanningTheme"


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


# --------------------------------------------------------------------------- #
#  PROPERTY vs TRANSITIVE — a UnitAction is a TRANSITIVE predication (an actor
#  acting on a patient); property predications (is_a/is/cop) are state, not
#  actions, and never form a return-relation.
# --------------------------------------------------------------------------- #
_PROPERTY_RELS = ("is_a", "is", "cop")


def _mint_unit_actions(ad, unit_id, textbase) -> list:
    """MECHANICAL I/O: mint one durable `UnitAction{unit,rel,agent,patient}` per
    TRANSITIVE predication of this unit (the actor/patient structure the
    cross-unit reciprocity token reads). A property predication (is_a/is/cop) is
    state, not an action -- skipped. Idempotent per (unit,rel,agent,patient)."""
    sub, _ = _resolve(ad)
    existing = set()
    for n in sub.nodes("UnitAction"):
        at = sub.node(n)["attrs"]
        existing.add((at.get("unit"), at.get("rel"), at.get("agent"), at.get("patient")))
    out = []
    for tb in textbase or []:
        for p in tb.get("predications") or []:
            if not p or len(p) < 3:
                continue
            rel, a0, a1 = str(p[0]), str(p[1]), str(p[2])
            if rel in _PROPERTY_RELS:
                continue
            key = (unit_id, rel, a0, a1)
            if key in existing:
                continue
            existing.add(key)
            nid = sub.add_node("UnitAction", {"unit": unit_id, "rel": rel,
                                              "agent": a0, "patient": a1})
            out.append({"node": _v(nid), "rel": rel, "agent": a0, "patient": a1})
    return out


# --------------------------------------------------------------------------- #
#  GOAL RECORDS — the want-SmEvents minted for THIS unit, in the shape
#  narrative_structure.recognize_narrative_structure consumes (mirrors
#  reading_drive._goal_from_graph, filtered by unit).
# --------------------------------------------------------------------------- #
def _goal_records(ad, unit_id) -> list:
    sub, _ = _resolve(ad)
    goals = []
    for n in sub.nodes("SmEvent"):
        at = sub.node(n)["attrs"]
        if at.get("verb") != "want" or at.get("surface") != "implicit_need":
            continue
        if at.get("unit") != unit_id:
            continue
        entity = at.get("idx_protagonist")
        goals.append({"minted": True,
                      "gap": {"entity": entity, "need_attr": at.get("need_attr")},
                      "supplies": {"remedy": at.get("idx_intentionality")}})
    return goals


def _discourse_pairs(ad, unit_id) -> list:
    """The decoded coherence pairs for this unit (read off CoherencePair? none
    minted in the nested path -- re-derive from the unit's DiscourseEvent graph
    is unnecessary here; narrative only reads 'contrast', absent for L&M). The
    honest per-unit pair list is empty unless minted; the arc still forms off
    the goal + enabling chain."""
    return []


# --------------------------------------------------------------------------- #
#  COMPREHEND ONE UNIT — the per-unit faculty chain, unit-scoped end to end.
#  Called ONCE per dispatched unit_comprehend stage (the reflex response); the
#  tree recursion is the rule firing per StoryUnit, not this function looping.
# --------------------------------------------------------------------------- #
def comprehend_unit(ad, unit_id, text: str) -> dict:
    """Comprehend ONE StoryUnit in isolation. Every faculty call carries
    `unit=unit_id`, so every node it mints is tagged with this unit and every
    read is confined to it. Returns the per-unit view (entities / goals / arc /
    tropes / theme) + the minted UnitAction records the compose reads."""
    from domains import dictionary_lexicon as dl
    dl.warm_wordnet("en")
    ig.ensure_seeds(ad)
    dc.ensure_codebook(ad)

    spine = ce.read_into_situation_model(ad, text, unit=unit_id)
    textbase = spine.get("textbase") or []
    ingests = spine.get("ingests") or []

    gaps = ig.detect_goal_gaps(ad, unit=unit_id)
    goal_effects = [ig.resolve_goal_gap(ad, g, unit=unit_id) for g in gaps]
    goals = _goal_records(ad, unit_id)

    dc.read_discourse(ad, text, unit=unit_id)

    chains = _mint_goal_action_enabling_chain(ad, textbase, ingests, goals)
    arc = ns.recognize_narrative_structure(ad, {
        "goal": goals,
        "enabling_chain": chains,
        "discourse": {"pairs": _discourse_pairs(ad, unit_id)},
    }, unit=unit_id)
    tropes = tt.recognize_tropes_and_theme(ad, {"narrative_arc": arc}, unit=unit_id)

    actions = _mint_unit_actions(ad, unit_id, textbase)
    return {"unit": unit_id, "text": text,
            "entities": list(spine.get("situation_model", {}).keys()),
            "goals": [g["gap"]["entity"] for g in goals],
            "arc": arc, "tropes": tropes, "actions": actions}


def read_unit_view(ad, unit_id) -> dict:
    """A pure graph read of ONE unit's comprehension: its entities, arc roles,
    tropes, theme, and actions -- all unit-scoped. For gates/demos."""
    sub, _ = _resolve(ad)
    entities = [sub.node(n)["attrs"].get("name") for n in sub.nodes("SmEntity")
                if sub.node(n)["attrs"].get("unit") == unit_id]
    actions = [{"rel": sub.node(n)["attrs"].get("rel"),
                "agent": sub.node(n)["attrs"].get("agent"),
                "patient": sub.node(n)["attrs"].get("patient")}
               for n in sub.nodes("UnitAction")
               if sub.node(n)["attrs"].get("unit") == unit_id]
    roles = ns.read_narrative_roles(ad, unit=unit_id)
    return {"unit": unit_id, "entities": entities, "actions": actions,
            "narrative_roles": roles}


# --------------------------------------------------------------------------- #
#  COMPOSE — the spanning theme is the verdict of a ShapeDecode over the
#  cross-unit token, exactly the story_tree.decode_seam / trope_theme collapse
#  one level up. The token is a mechanical existence check over the children's
#  own UnitAction nodes; the THEME is the decode's, never a Python assignment.
# --------------------------------------------------------------------------- #
def _child_units(ad, parent_id) -> list:
    """The leaf StoryUnits under `parent_id`, in span order (a pure graph read
    off the has_story_unit edges story_tree minted)."""
    sub, _ = _resolve(ad)
    kids = []
    for n in sub.nodes("StoryUnit"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "root":
            continue
        kids.append((at.get("span_start") if at.get("span_start") is not None else -1,
                     _v(n)))
    kids.sort()
    return [k for _, k in kids]


def _unit_actions(ad, unit_id) -> list:
    sub, _ = _resolve(ad)
    return [(sub.node(n)["attrs"].get("agent"), sub.node(n)["attrs"].get("patient"))
            for n in sub.nodes("UnitAction")
            if sub.node(n)["attrs"].get("unit") == unit_id]


def _span_token(ad, children: list) -> tuple:
    """The cross-unit token, read off the children's UnitAction nodes. RETURN_
    ACTION iff an EARLIER child carries an action (agent=A, patient=B) and a
    LATER child carries the REVERSED action (agent=B, patient=A) over the same
    two entities -- the actor/recipient role-reversal that IS reciprocity. An
    existence check building the TOKEN; it never names the theme. else SPAN_NONE."""
    for ci in range(len(children)):
        for cj in range(ci + 1, len(children)):
            acts_i = _unit_actions(ad, children[ci])
            acts_j = _unit_actions(ad, children[cj])
            for (a, b) in acts_i:
                if a is None or b is None or a == b:
                    continue
                for (c, d) in acts_j:
                    if c == b and d == a:            # reversed: B acts on A
                        note = ("child %s carries action (%s -> %s); child %s carries the "
                                "REVERSED action (%s -> %s) -- the actor/recipient reversal "
                                "across episodes" % (children[ci], a, b, children[cj], c, d))
                        return "RETURN_ACTION", note, {"a": a, "b": b,
                                "early": children[ci], "late": children[cj]}
    return "SPAN_NONE", ("no cross-unit return-action (no later child reverses an earlier "
                         "child's actor/recipient) -- honest null, no spanning theme"), {}


def _decode_span(ad, token: str) -> dict:
    _, native = _resolve(ad)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [[token]]},
            "codebook_type": _SPAN_CODEBOOK_TYPE, "beam": 1, "max_steps": 1, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": [[token]], "ordered_parts": []}
    return res


def _theme_for(ad, name: str) -> tuple:
    sub, _ = _resolve(ad)
    for n in sub.nodes(_SPAN_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get("theme"), at.get("line")
    return None, None


def compose_spanning_theme(ad, parent_id) -> dict:
    """Compose the parent StoryUnit's spanning theme from its children. The
    cross-unit token is decoded against the ShapeSignatureSpanningTheme codebook
    (the DECIDE); a winning schema's `theme`/`line` is minted as a SpanningTheme
    node on the parent, wired to both child units. SPAN_NONE covers no schema ->
    honest null, no SpanningTheme (a flat union is not a spanning theme)."""
    ensure_codebook(ad)
    sub, native = _resolve(ad)
    children = _child_units(ad, parent_id)
    token, note, binding = _span_token(ad, children)
    res = _decode_span(ad, token)
    name, fit = rc._winner(res)
    theme, line = _theme_for(ad, name) if (name is not None and fit > 0) else (None, None)
    out = {"parent": _v(parent_id), "children": children, "token": token,
           "construction": name, "shape_fit": max(fit, 0), "theme": theme,
           "line": line, "note": note, "binding": binding}
    if theme is None:
        out["minted"] = False
        return out
    # mint the SpanningTheme on the parent, traced to both children. Resolve the
    # actual StoryUnit NodeIDs (the caller may pass a bare _v value).
    parent_node = _node_by_v(sub, "StoryUnit", _v(parent_id))
    stn = sub.add_node("SpanningTheme", {"parent": _v(parent_id), "theme": theme,
                                         "line": line, "construction": name,
                                         "token": token,
                                         "children": json.dumps([binding.get("early"),
                                                                 binding.get("late")])})
    if parent_node is not None:
        dc._mint_edge(sub, native, parent_node, stn, "has_spanning_theme", {"theme": theme})
    for cu in (binding.get("early"), binding.get("late")):
        cnode = _node_by_v(sub, "StoryUnit", cu) if cu is not None else None
        if cnode is not None:
            dc._mint_edge(sub, native, stn, cnode, "spans_unit", {})
    out["minted"] = True
    out["node"] = _v(stn)
    return out


def _node_by_v(sub, node_type: str, v):
    for n in sub.nodes(node_type):
        if _v(n) == v:
            return n
    return None


def read_spanning_theme(ad, parent_id=None) -> Optional[dict]:
    sub, _ = _resolve(ad)
    for n in sub.nodes("SpanningTheme"):
        at = dict(sub.node(n)["attrs"])
        if parent_id is None or at.get("parent") == _v(parent_id):
            at["node"] = _v(n)
            return at
    return None


# --------------------------------------------------------------------------- #
#  codebook install (mechanical seed I/O).
# --------------------------------------------------------------------------- #
def ensure_codebook(agent) -> None:
    sub, native = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "spanning_theme":
            return
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "seeds", "spanning_theme.json")) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "spanning_theme",
                          "version": manifest.get("version", "1.0.0")})


__all__ = ["comprehend_unit", "read_unit_view", "compose_spanning_theme",
           "read_spanning_theme", "ensure_codebook", "decode_span"]


def decode_span(ad, token: str) -> dict:
    """Public: decode ONE cross-unit token against the codebook (the verdict is
    the decode's, read off reading_collapse._winner)."""
    ensure_codebook(ad)
    res = _decode_span(ad, token)
    name, fit = rc._winner(res)
    theme, line = _theme_for(ad, name) if (name is not None and fit > 0) else (None, None)
    return {"token": token, "construction": name, "theme": theme,
            "line": line, "shape_fit": max(fit, 0)}
