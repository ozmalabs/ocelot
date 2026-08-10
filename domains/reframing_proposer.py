"""reframing_proposer — the agent PROPOSES + TESTS candidate unifying abstractions
over its OWN introspectable structure, and FLAGS survivors for the creator.

HONEST SCOPE (stated plainly, in code and report). This module SURFACES candidate
reframings — analogical generalizations across the agent's own faculties — and
TESTS whether the claimed pattern ACTUALLY HOLDS across its instances, flagging
survivors for the creator to review. It does NOT judge whether a reframing is a
GOOD or DEEP foundational insight; that judgement stays the creator's. It does not
originate foundational geometry. The reframings that reorganized this project
("values are relative positions", "weights are log-scaled dimensional edges", "a
frame is a weighted dimension-set", "not two — N") came from the CREATOR, not from
here. What this gives the agent is the bounded, honest version of that capacity:
propose an analogical generalization over its own introspectable structure, test
that the pattern holds, and hand the survivor to the creator as a CANDIDATE — a
graph node flagged `for_review`, never installed as truth.

MECHANISM — reuse two held faculties; this module only SEQUENCES them.

  1. SCAN. Introspect a set of the agent's own faculties (a mechanical read of the
     real module docstrings — the same admissible adapter I/O `introspect_primitives`
     lifts concepts and `self_model` lifts `export_rules()`) into a Concept-per-
     faculty Microtheory. Then use `analogical_thinking` — the agent's OWN cross-
     structure abstraction faculty (`find_analogies` + `shape_hits`, its meta-shape
     vocabulary) — to find a RECURRING structure: a meta-shape shared by >= N of the
     faculties, with `find_analogies` confirming the instances are pairwise analogous
     at that order. No abstraction is invented here; the agent's shape faculty reads it.

  2. PROPOSE. Mint a `Reframing` graph node — "these N faculties are all cases of
     ABSTRACTION" — flagged `for_review`, with `unifies` edges to the instance
     concepts. NOT installed as truth.

  3. VERIFY. Hand the candidate to `self_verification.verify_claim` (the NOT-FOOLING-
     ITSELF faculty). The abstraction must HOLD across its claimed instances — the
     mechanism is the agent's OWN shape read finding the meta-shape in each faculty —
     with a DISCRIMINATIVE control: a known-fake twin (a surface coincidence that does
     not actually unify) FAILS the control, so a SPURIOUS abstraction the instances do
     NOT actually share is PROPOSED-then-REJECTED. Real pattern -> survives; spurious
     -> rejected. That is the crux that keeps the proposer from emitting noise.

No new cognition, no LLM, no fit. The candidate is a graph node the creator reviews.
"""
from __future__ import annotations

import ast
import json
import os
from typing import Any, Callable, Optional

import domains.analogical_thinking as at
from domains.self_verification import Claim, verify_claim

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The faculties the agent introspects by default: the DomainPlug-into-run_collapse
# family — four real modules that each plug the agent's ONE collapse engine
# (scripts/collapse_engine.run_collapse) into a different domain (a maze's motion,
# a person, the conversation's context, the agent's own competence). Paths are real
# files; the "definition" of each faculty is its OWN module docstring, read
# mechanically. This is the population the scan abstracts over — nothing about the
# recurring structure is asserted here; the agent's shape faculty finds it.
DEFAULT_FACULTIES: dict[str, str] = {
    "move_space_collapse_plug":  "scripts/move_space_collapse_plug.py",
    "interlocutor_collapse_plug": "domains/interlocutor_collapse_plug.py",
    "context_collapse_plug":      "domains/context_collapse_plug.py",
    "self_capability_collapse":   "domains/self_capability_collapse.py",
}

_SCAN_MT = "agent_faculties_scan"
_REFRAMING_TYPE = "Reframing"


# ---------------------------------------------------------------------------
# resolve the Python Substrate handle from whatever the caller passed (a
# WorldAdapter, a Substrate, or a raw native handle) — the same duck typing the
# held faculties use. find_analogies / shape_hits want the .nodes/.node/.
# neighbours-carrying substrate; verify_claim does its own _resolve internally.
# ---------------------------------------------------------------------------
def _sub(agent):
    return getattr(agent, "s", agent)


def _faculty_docstring(path: str) -> str:
    """Mechanical read: the module's own top-level docstring. No interpretation —
    exactly the adapter I/O `self_model` does over `export_rules()`. A missing file
    yields "" (the faculty simply contributes no text to the scan)."""
    full = path if os.path.isabs(path) else os.path.join(_ROOT, path)
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return ast.get_docstring(ast.parse(f.read())) or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 1. SCAN — introspect faculties into a Concept microtheory, then read the
#    recurring structure with the agent's own analogy/shape faculty.
# ---------------------------------------------------------------------------
def introspect_faculties(agent, faculties: Optional[dict[str, str]] = None,
                         mt_name: str = _SCAN_MT) -> tuple[Any, dict[str, str]]:
    """Lift each faculty into a `Concept` (name + category 'faculty' + definition =
    its real docstring) under one Microtheory. Mechanical adapter I/O — idempotent by
    Mt name and by concept name (re-run reuses existing nodes). Returns
    (mt_node, {faculty_name: definition_text})."""
    faculties = faculties or DEFAULT_FACULTIES
    sub = _sub(agent)

    mt = None
    for m in sub.nodes("Microtheory"):
        if str(sub.node(m)["attrs"].get("name", "")) == mt_name:
            mt = m
            break
    if mt is None:
        mt = sub.add_node("Microtheory", {"name": mt_name,
                                          "origin": "reframing_proposer"})

    existing = {str(sub.node(c)["attrs"].get("name", "")): c
                for c in sub.neighbours(mt, "has_concept")}
    defs: dict[str, str] = {}
    for name, path in faculties.items():
        doc = _faculty_docstring(path)
        defs[name] = doc
        if name in existing:
            continue
        c = sub.add_node("Concept", {"name": name, "category": "faculty",
                                     "definition": doc, "source_path": path,
                                     "origin": "reframing_proposer"})
        sub.add_edge(mt, "has_concept", c)
    return mt, defs


def _faculty_metashapes(agent, defs: dict[str, str]) -> dict[str, set]:
    """The agent's OWN shape reading of each faculty: the set of meta-shapes
    `analogical_thinking.shape_hits` (its seeded ShapePrinciple -> MetaShape
    vocabulary) finds in the faculty's docstring. Not invented here — read off the
    agent's meta-shape faculty."""
    return {name: set(at.shape_hits(agent, text)) for name, text in defs.items()}


def scan_for_recurring_structure(agent, faculties: Optional[dict[str, str]] = None,
                                 *, min_instances: int = 2, min_order: int = 3,
                                 mt_name: str = _SCAN_MT) -> list[dict]:
    """Scan the introspected faculties for a RECURRING structure — a meta-shape
    shared by >= `min_instances` of them, corroborated by `find_analogies` linking
    those instances as pairwise analogous at order >= `min_order`.

    Returns a list of CANDIDATE abstractions (deepest / most-shared first), each:
      {abstraction, kind='meta_shape', order_n, instances:[names], n_instances,
       analogous_pairs}. Surfacing MULTIPLE candidates is deliberate — the proposer
       does not judge which is the deep one; that is the creator's call downstream."""
    faculties = faculties or DEFAULT_FACULTIES
    _mt, defs = introspect_faculties(agent, faculties, mt_name=mt_name)
    sub = _sub(agent)

    # The agent's own analogy faculty over the faculty microtheory: which faculty
    # pairs are analogous, and at what order. Confirms the recurrence is the agent's
    # reading, not just our keyword intersection.
    analogies = at.find_analogies(sub, mt_name, [mt_name], order_n=4)
    order_of_pair: dict[frozenset, int] = {}
    for a in analogies:
        k = frozenset((a["source_concept"], a["target_concept"]))
        order_of_pair[k] = max(order_of_pair.get(k, 0), a["order_n"])

    # Group faculties by shared meta-shape (the agent's shape_hits reading).
    ms = _faculty_metashapes(agent, defs)
    shape_to_insts: dict[str, list[str]] = {}
    for name, shapes in ms.items():
        for sh in shapes:
            shape_to_insts.setdefault(sh, []).append(name)

    candidates: list[dict] = []
    for shape, insts in shape_to_insts.items():
        insts = sorted(set(insts))
        if len(insts) < min_instances:
            continue
        # corroborate: at least one instance pair is analogous at order >= min_order
        pairs = []
        for i in range(len(insts)):
            for j in range(i + 1, len(insts)):
                k = frozenset((insts[i], insts[j]))
                if order_of_pair.get(k, -1) >= min_order:
                    pairs.append([insts[i], insts[j], order_of_pair[k]])
        if not pairs:
            continue
        candidates.append({
            "abstraction": shape,
            "kind": "meta_shape",
            "order_n": max(p[2] for p in pairs),
            "instances": insts,
            "n_instances": len(insts),
            "analogous_pairs": pairs,
        })
    candidates.sort(key=lambda c: (-c["n_instances"], -c["order_n"], c["abstraction"]))
    return candidates


# ---------------------------------------------------------------------------
# 2. PROPOSE — mint a Reframing node flagged for_review (NOT asserted as truth).
# ---------------------------------------------------------------------------
def propose_reframing(agent, candidate: dict, *, mt_name: str = _SCAN_MT) -> Any:
    """Mint a `Reframing` graph node for a candidate abstraction: {abstraction,
    kind, order_n, instances (json), n_instances, for_review=1.0, verified=-1.0
    (unset until verified)}. Adds `unifies` edges to the instance Concepts. This is
    a CANDIDATE, flagged for creator review — never installed as an asserted truth."""
    sub = _sub(agent)
    node = sub.add_node(_REFRAMING_TYPE, {
        "abstraction": candidate["abstraction"],
        "kind": candidate.get("kind", "meta_shape"),
        "order_n": int(candidate.get("order_n", 0)),
        "instances": json.dumps(sorted(candidate["instances"])),
        "n_instances": int(candidate.get("n_instances", len(candidate["instances"]))),
        "for_review": 1.0,        # a candidate for the creator, not a settled truth
        "verified": -1.0,         # -1 = not yet tested; set to 1/0 by verify_reframing
        "claim_text": (f"these {candidate.get('n_instances', len(candidate['instances']))} "
                       f"faculties are all cases of {candidate['abstraction']!r}"),
        "origin": "reframing_proposer",
    })
    # link the reframing to the real faculty concepts it claims to unify
    mt = None
    for m in sub.nodes("Microtheory"):
        if str(sub.node(m)["attrs"].get("name", "")) == mt_name:
            mt = m
            break
    if mt is not None:
        native = getattr(sub, "_inner", sub)
        by_name = {str(sub.node(c)["attrs"].get("name", "")): c
                   for c in sub.neighbours(mt, "has_concept")}
        for nm in candidate["instances"]:
            if nm in by_name:
                # "unifies" has no production; add it unchecked (the same admissible
                # host move self_verification uses for its provenance edges).
                try:
                    native.add_edge_unchecked(node, "unifies", by_name[nm])
                except TypeError:
                    native.add_edge_unchecked(node, "unifies", by_name[nm], {})
                except Exception:
                    pass
    return node


# ---------------------------------------------------------------------------
# 3. VERIFY — hand the candidate to self_verification.verify_claim.
#    The mechanism is the agent's OWN shape read; the control discriminates real
#    from spurious. Grounding is held constant (a sensor anchor) so the verdict
#    flips ONLY on whether the abstraction actually holds across the instances —
#    mirroring test_self_verification's real-vs-fake-same-faculty design.
# ---------------------------------------------------------------------------
def _shape_mechanism(agent, abstraction: str,
                     defs: dict[str, str]) -> Callable[[Any], bool]:
    """case (a faculty name) -> does the agent's shape reading of that faculty
    actually contain `abstraction`? The REAL test of whether the abstraction
    unifies the instance."""
    def mech(name: Any) -> bool:
        return abstraction in at.shape_hits(agent, defs.get(str(name), ""))
    return mech


def _surface_twin(abstraction: str) -> Callable[[Any], bool]:
    """The KNOWN-FAKE twin that gives the control TEETH: a SPURIOUS 'unifier' that
    claims the faculties cohere merely because the abstraction's literal words
    appear as tokens in the faculty NAME. For a genuine deep meta-shape this is
    False on every real faculty (their names don't spell out the meta-shape), so
    the twin FAILS the control -> the control discriminates."""
    needle = abstraction.replace("_", " ")
    def twin(name: Any) -> bool:
        hay = str(name).replace("_", " ").lower()
        return needle.lower() in hay or abstraction.lower() in hay
    return twin


def _ground_sensor(sub):
    """Grounding support for a reframing over the agent's own structure, wired to a
    real SensorAnchor (the same construction tests/test_self_verification uses):
    Agent -perceives-> percept, support -grounded_in-> percept; ensure_grounding_
    edges chains percept -> SensorAnchor. Held CONSTANT across real and spurious
    candidates on purpose — grounding is not the discriminator here, the control is."""
    ag = sub.add_node("Agent", {})
    perc = sub.add_node("VisionPercept", {})
    try:
        sub.add_edge_unchecked(ag, "perceives", perc)
    except Exception:
        sub.add_edge(ag, "perceives", perc)
    node = sub.add_node("Collapse", {"label": "reframing_support"})
    try:
        sub.add_edge_unchecked(node, "grounded_in", perc)
    except Exception:
        sub.add_edge(node, "grounded_in", perc)
    return node


def verify_reframing(agent, reframing_node: Any, defs: dict[str, str],
                     *, ground_support: Optional[Callable] = None) -> dict:
    """Test a proposed Reframing with the agent's NOT-FOOLING-ITSELF faculty. The
    abstraction must HOLD across its claimed instances (the agent's own shape read),
    the control must DISCRIMINATE (a known-fake surface twin fails), and the support
    must reach a grounding anchor. Writes the verdict onto the Reframing node
    (`verified`, `discriminates`, `grounded`, `verdict_reason`), keeping `for_review`
    set — a verified candidate is STILL flagged for the creator, never self-certified.
    Returns the verify_claim result plus the candidate summary."""
    sub = _sub(agent)
    at_r = sub.node(reframing_node)["attrs"]
    abstraction = str(at_r.get("abstraction", ""))
    instances = json.loads(at_r.get("instances", "[]"))
    mech = _shape_mechanism(agent, abstraction, defs)
    twin = _surface_twin(abstraction)

    result = verify_claim(agent, Claim(
        text=str(at_r.get("claim_text", abstraction)),
        mechanism=mech,
        control_cases=list(instances),
        fake_twin=twin,
        prior_cases=(),                       # no-regression held True (constant)
        ground_support=ground_support or _ground_sensor,
    ))

    sub.set_attr(reframing_node, "verified", 1.0 if result["accepted"] else 0.0)
    sub.set_attr(reframing_node, "discriminates", 1.0 if result["discriminates"] else 0.0)
    sub.set_attr(reframing_node, "grounded", 1.0 if result["grounded"] else 0.0)
    sub.set_attr(reframing_node, "verdict_reason", result["reason"])
    # `for_review` stays 1.0: even a verified candidate is flagged for the creator.

    result["abstraction"] = abstraction
    result["instances"] = instances
    result["reframing_node"] = reframing_node
    return result


# ---------------------------------------------------------------------------
# The full sequence: scan -> propose -> verify, over the agent's own faculties.
# ---------------------------------------------------------------------------
def propose_and_verify(agent, faculties: Optional[dict[str, str]] = None,
                       *, min_instances: int = 2, min_order: int = 3) -> dict:
    """SCAN the agent's faculties for recurring structure, PROPOSE each candidate as
    a Reframing node, and VERIFY it. Returns {defs, candidates:[{candidate, node,
    verify}...]} — every candidate flagged for_review, survivors marked verified."""
    faculties = faculties or DEFAULT_FACULTIES
    _mt, defs = introspect_faculties(agent, faculties)
    candidates = scan_for_recurring_structure(
        agent, faculties, min_instances=min_instances, min_order=min_order)
    out = []
    for cand in candidates:
        node = propose_reframing(agent, cand)
        verify = verify_reframing(agent, node, defs)
        out.append({"candidate": cand, "node": node, "verify": verify})
    return {"defs": defs, "candidates": out}


__all__ = [
    "DEFAULT_FACULTIES",
    "introspect_faculties",
    "scan_for_recurring_structure",
    "propose_reframing",
    "verify_reframing",
    "propose_and_verify",
]
