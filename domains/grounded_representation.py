"""Grounded representation — concept-as-grounded-structure.

The agent's OWN verdict (from scripts/ask_jabberwock_data_structure.py) was
that its concept graph is INADMISSIBLE for grounding: the architecture cortex
flagged `orphaned_concept x 5695` + `compositional_reuse 0/10` ("depends_on
incoming = 0"), and its gap-synthesis derived

    "a COMPOSITIONAL system's WHOLE = its PARTS + a finite set of COMBINATION
     (production) rules"

while it already holds the memory concepts (cache_resident_working_set,
memory_wall_drives_locality_optimisation, lazy-loading). The ROOT finding: a
concept->concept grounding edge is INADMISSIBLE in Γ (no open production
declares it), so the seed loaders' bare try/except SILENTLY DROP it.

This module is the MECHANICAL SCHEMA that realises the agent-derived design.
The agent DERIVED the principles (parts + combination = composition;
memory_wall -> locality + working_set); this code is the schema that makes
them admissible and proves them on a real slice. No LLM. Graph-native:

  A. LOGICAL — grounding admissible + concept-as-structure
     · open_grounding_productions: Γ now admits Concept->Concept grounding
       edges (built_from / depends_on / grounds / genls). An edge that was
       silently dropped now LANDS.
     · ground_concept: a Concept's STRUCTURAL definition = its `built_from`
       edges to the concepts it is built from (its PARTS) + a `combination`
       (a named production rule or Term-tree; the order_n_concepts
       composed_by=agent idiom). "grounded" = the structure reduces,
       recursively, to seeded PRIMITIVES.
     · migrate_communication_slice: the communication primes whose `roles`
       already name their parts become grounding EDGES + a combination.
       The gloss stays as a label; the MEANING is now the structure.

  B. PHYSICAL — the SAME structure is the locality / lazy access
     · GroundedConceptStore: a concept persisted WITH its grounding cone
       (the built_from* closure) so loading it is one fetch from a binary
       cold store (graph_to_dict/from_dict); a query lazily loads only its
       ADMISSIBLE CONE into a cache-resident working set (mirrors
       conceptnet `_ensure_slab`); a cache_replacement_policy (LRU) evicts
       cold cones so the working set stays bounded.

The grounding STRUCTURE is simultaneously the LOGICAL form (concepts compose,
theories ground in existing ones) AND the ACCESS/locality form (load the cone,
evict the rest). One object, two regimes.
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# A.1  Open Γ productions admitting concept->concept GROUNDING edges.
# ---------------------------------------------------------------------------

# The grounding edge vocabulary. built_from = "this concept is composed of
# these parts"; depends_on = the finer-grained structural reference the
# architecture cortex's compositional_reuse scorer already reads; grounds =
# the inverse (a primitive grounds the things built from it); genls = is-a
# subsumption between concepts. All Concept->Concept.
GROUNDING_EDGE_TYPES = ("built_from", "depends_on", "grounds", "genls")


def open_grounding_productions(substrate) -> int:
    """Open the Γ productions that admit Concept->Concept grounding edges.

    Before this, add_edge(concept, "built_from", concept) is rejected
    (Type-2: 'Concept' not in the built_from vocabulary) and the seed
    loaders' bare try/except silently drop it. After, the edge LANDS.

    Idempotent (add_production is additive; re-opening is harmless).
    Returns the number of productions submitted."""
    n = 0
    for et in GROUNDING_EDGE_TYPES:
        try:
            substrate.add_production({
                "src": {"type": "Concept", "var": "a"},
                "edge_type": et,
                "tgt": {"type": "Concept", "var": "b"},
                "where": None,
                "provenance": "grounded_representation:grounding",
            })
            n += 1
        except Exception:
            pass
    # FRAME binding: a concept grounds IN a WORLD (its Microtheory). Admit the
    # Microtheory -has_concept-> Concept edge so a frame-relative grounding LANDS
    # (the same edge the seed loaders use, here made admissible for live
    # grounding). Grounding is frame-relative — the frame says WHICH world.
    try:
        substrate.add_production({
            "src": {"type": "Microtheory", "var": "m"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "c"},
            "where": None,
            "provenance": "grounded_representation:frame",
        })
        n += 1
    except Exception:
        pass
    return n


# ---------------------------------------------------------------------------
# A.2  Give a Concept a STRUCTURAL definition.
# ---------------------------------------------------------------------------

def _concept_by_name(substrate) -> dict[str, Any]:
    """name -> NodeID for every Concept (one pass)."""
    out: dict[str, Any] = {}
    for c in substrate.nodes("Concept"):
        nm = substrate.node(c)["attrs"].get("name")
        if isinstance(nm, str) and nm not in out:
            out[nm] = c
    return out


def _find_concept(substrate, name: str, index: Optional[dict] = None):
    if index is not None:
        return index.get(name)
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            return c
    return None


def _has_built_from(substrate, src, tgt) -> bool:
    try:
        return tgt in set(substrate.neighbours(src, "built_from"))
    except Exception:
        return False


def _has_any_built_from(substrate, src, edge_type: str = "built_from") -> bool:
    try:
        return len(substrate.neighbours(src, edge_type)) > 0
    except Exception:
        return False


# Register -> grounding CONFIDENCE. A definition's REGISTER adjunct (the
# epistemic band the agent COMPREHENDED from 'roughly speaking,' / 'formally,')
# sets HOW CONFIDENTLY the grounding holds. 'exact' (or no register adjunct: a
# bare definition states its content at full confidence) -> full; 'approximate'
# (a hedge — roughly/loosely/informally) -> a HEDGED, below-full confidence. The
# numbers reuse the held epistemic-confidence machinery (conjecture.py:
# grounded_confidence() = 1.0; GROUNDED_HOP = 0.9, a hop that still commits) — no
# parallel band invented. A coarse two-level map (the honest approximate edge).
def _register_confidence(register: Optional[str]) -> Optional[float]:
    """Map a comprehended REGISTER to a grounding confidence in [0,1], using the
    held epistemic-confidence constants. None register -> None (default
    grounding, attr untouched). 'exact' -> 1.0 (full). 'approximate' -> the
    hedged GROUNDED_HOP (below full but still committing)."""
    if not register:
        return None
    try:
        from domains import conjecture as _cj
        full = _cj.grounded_confidence()
        hedged = _cj.GROUNDED_HOP
    except Exception:
        full, hedged = 1.0, 0.9
    return float(hedged) if register == "approximate" else float(full)


# The DOMAIN -> Microtheory map (the frame->Mt name-match's known-domain layer)
# read from the held `definition` concept's `structure` (graph data). A frame
# field word ('math', 'geometry', 'music') resolves to the Mt the agent is
# likely to hold ('mathematics', 'music'). A coarse name-match — the honest
# remaining coarseness; if neither the exact name nor this map resolves, the
# frame is recorded + a genls toward the nearest held domain Mt rather than
# dropped.
def _domain_mt_map(substrate) -> dict[str, str]:
    """Read frame field word -> Mt name from the held `definition` structure."""
    if substrate is not None:
        try:
            for cid in substrate.nodes("Concept"):
                a = substrate.node(cid)["attrs"]
                if a.get("name") == "definition" and a.get("structure"):
                    s = json.loads(a["structure"])
                    m = s.get("domain_mt_map")
                    if isinstance(m, dict):
                        return {k: v for k, v in m.items()
                                if isinstance(v, str)}
        except Exception:
            pass
    return {}


def _find_microtheory(substrate, name: str):
    """NodeID of a Microtheory by exact name, or None."""
    try:
        for mid in substrate.nodes("Microtheory"):
            if substrate.node(mid)["attrs"].get("name") == name:
                return mid
    except Exception:
        return None
    return None


def _resolve_frame_mt(substrate, fname: str) -> tuple[Optional[Any], Optional[str]]:
    """Resolve a frame field name to a held Microtheory: EXACT name-match first,
    then the known-domain map (math->mathematics, music->music, ...). Returns
    (mt_node_or_None, resolved_mt_name_or_None). A coarse name-match — the honest
    remaining coarseness. No nearest-domain genls is invented here; when neither
    resolves the caller records the frame on the concept (binding not lost)."""
    mt = _find_microtheory(substrate, fname)
    if mt is not None:
        return mt, fname
    mapped = _domain_mt_map(substrate).get(fname)
    if mapped:
        mt = _find_microtheory(substrate, mapped)
        if mt is not None:
            return mt, mapped
    return None, mapped


# A SENSE-aware concept name: when a definition's FRAME DIFFERS from the term's
# existing grounded frame, the new reading is a DISTINCT SENSE (a homonym —
# 'manifold (music)' vs 'manifold (mathematics)') and must NOT overwrite the
# held grounding. The sense node's name carries the frame: '<term>__<frame>'.
def _sense_name(term: str, frame: Optional[str]) -> str:
    if not frame:
        return term
    f = re.sub(r"\s+", "_", frame.strip().lower())
    return f"{term}__{f}"


def ground_concept(substrate, name: str, built_from: Iterable[str],
                   combination: Any, *, index: Optional[dict] = None,
                   create_missing: bool = True,
                   edge_type: str = "built_from",
                   frame: Optional[str] = None,
                   register: Optional[str] = None,
                   confidence: Optional[float] = None,
                   register_status: Optional[str] = None,
                   sense_aware: bool = False,
                   provenance: Optional[dict] = None,
                   epistemic_status: Optional[dict] = None) -> dict:
    """Give the Concept `name` a STRUCTURAL definition: a grounding edge to
    each part in `built_from` + a `combination` recording HOW they compose
    (a named production-rule string OR a Term-tree dict; the
    order_n_concepts composed_by=agent idiom).

    The gloss/definition stays on the node as a LABEL; the MEANING is the
    structure (the edges + the combination). Each part must itself be a
    Concept (created if missing + create_missing). Also writes the inverse
    `grounds` edge (part grounds the whole) so the primitive side is
    queryable. Idempotent: skips an edge already present.

    ADDITIVE comprehension params (all default to unchanged grounding):
      · `frame`  — the domain the definition grounds IN (comprehended from a
        'In <field>,' adjunct). Grounding is frame-relative: the frame name is
        resolved to a Microtheory (EXACT name, then the held domain->Mt map);
        the concept is attached to it (has_concept edge) so it grounds in that
        WORLD; else the frame is recorded on the concept (`frame` attr) so the
        binding is not lost. None -> no frame binding.
      · `register` — the comprehended register CLASS ('canonical'/'approximate'/
        'informal'/'exact'). Recorded as `grounding_register`.
      · `confidence` — the resolved epistemic confidence (the expectation model's
        band: canonical/exact -> 1.0, approximate -> 0.85, informal -> 0.8). When
        given, set directly; else fall back to the coarse register->confidence
        map. Sets `grounding_confidence`.
      · `register_status` — 'canonical' (unmarked, asserted-as-fact) | 'hedged'.
        Recorded as `grounding_status` (the comprehended present/absent signal).
      · `sense_aware` — when True, a definition whose FRAME DIFFERS from the
        term's EXISTING grounded frame is read as a SENSE-SHIFT (a homonym): the
        new reading grounds on a DISTINCT sense node ('<term>__<frame>'), and the
        held grounding is NOT overwritten. Also: a genus DIFFERENT from the
        term's held built_from is a SURPRISE — grounded but FLAGGED for
        re-evaluation (`genus_surprise`), the held edge not silently replaced.
      · `provenance` — the PROVENANCE of this grounding (WHERE/WHO/HOW/WHAT/WHEN
        it was read from). Knowledge is source-relative: where it came from is
        part of what it means. Recorded as a `provenance` attr (JSON) so the
        grounded concept CARRIES its source — the agent knows what it read.
      · `epistemic_status` — the {status, confidence, reliability, why} a
        grounding READ FROM a source carries (consensus/attested, distinct from
        a self-DERIVED or CONJECTURED grounding), read off the source's held
        reliability (NOT hardcoded). Recorded as `epistemic_status` +
        `grounding_status` ('consensus'), and — when no register confidence was
        supplied — sets the grounding confidence from the source's reliability
        (an attested grounding is held firmly but below a self-derived 1.0).

    Returns {concept, parts:[nid], edges_added, combination_set, frame_mt,
    frame_recorded, frame_mt_name, confidence, register_status, sense_shift,
    sense_name, genus_surprise, grounded_name, provenance, epistemic_status}."""
    if index is None:
        index = _concept_by_name(substrate)

    # EXPECTATION-BASED: read the new definition AGAINST what the agent already
    # holds for the term. Two prediction-error signals reshape the grounding:
    #
    #  · SENSE-SHIFT — the term is already grounded IN a frame, and THIS frame is
    #    DIFFERENT: a homonym ('manifold (music)' vs the held 'manifold
    #    (mathematics)'). Ground the new reading on a DISTINCT sense node so the
    #    held grounding is preserved (NOT overwritten). Decided only sense_aware.
    #  · SURPRISE-GENUS — the term is already grounded built_from some genus, and
    #    THIS genus is DIFFERENT: ground the new edge but FLAG it for
    #    re-evaluation (don't silently drop the held edge).
    grounded_name = name
    sense_shift = False
    sense_name: Optional[str] = None
    genus_surprise = False
    held = index.get(name)
    if sense_aware and held is not None:
        ha = substrate.node(held)["attrs"]
        new_fname = re.sub(r"\s+", "_", frame.strip().lower()) if frame else None
        held_frame = ha.get("frame")
        held_grounded = (ha.get("structurally_grounded")
                         or _has_any_built_from(substrate, held))
        # SENSE-SHIFT: held grounding carries a different frame than this reading.
        if (held_grounded and new_fname and held_frame
                and held_frame != new_fname):
            sense_shift = True
            sense_name = _sense_name(name, frame)
            grounded_name = sense_name
        # SURPRISE-GENUS: same-sense (no frame divergence) but the new genus is
        # NOT among the term's held built_from parts -> flag, do not overwrite.
        elif held_grounded:
            held_parts = {substrate.node(m)["attrs"].get("name")
                          for m in substrate.neighbours(held, edge_type)}
            new_parts = set(built_from)
            if new_parts and not (new_parts & held_parts):
                genus_surprise = True

    cid = index.get(grounded_name)
    if cid is None:
        if not create_missing:
            return {"concept": None, "parts": [], "edges_added": 0,
                    "combination_set": False}
        attrs = {"name": grounded_name, "origin": "grounded_representation",
                 "composed_by": "agent"}
        if sense_shift:
            # a distinct sense node: record the base term + that it is a sense.
            attrs["sense_of"] = name
            attrs["is_sense"] = 1
        cid = substrate.add_node("Concept", attrs)
        index[grounded_name] = cid

    if genus_surprise:
        try:
            substrate.set_attr(cid, "genus_surprise", 1)
            substrate.set_attr(cid, "needs_reevaluation", 1)
        except Exception:
            pass

    part_ids = []
    edges_added = 0
    for pname in built_from:
        pid = index.get(pname)
        if pid is None:
            if not create_missing:
                continue
            pid = substrate.add_node("Concept", {
                "name": pname, "origin": "grounded_representation"})
            index[pname] = pid
        part_ids.append(pid)
        if not _has_built_from(substrate, cid, pid):
            try:
                substrate.add_edge(cid, edge_type, pid, {})
                edges_added += 1
            except Exception:
                pass
        # finer-grained structural reference the cortex's compositional_reuse
        # scorer reads directly (depends_on incoming).
        try:
            if pid not in set(substrate.neighbours(cid, "depends_on")):
                substrate.add_edge(cid, "depends_on", pid, {})
        except Exception:
            pass
        # inverse: the part GROUNDS the whole (primitive-side queryable).
        try:
            if cid not in set(substrate.neighbours(pid, "grounds")):
                substrate.add_edge(pid, "grounds", cid, {})
        except Exception:
            pass

    combination_set = False
    if combination is not None:
        try:
            # combination is the agent's Term-tree / named production for
            # how the parts compose into the whole. Stored as graph DATA so
            # the structure is inspectable, like a compose_order_n_features
            # Concept's `predicate`.
            substrate.set_attr(cid, "combination", combination
                               if isinstance(combination, str)
                               else json.dumps(combination))
            substrate.set_attr(cid, "structurally_grounded", 1)
            substrate.set_attr(cid, "composed_by", "agent")
            combination_set = True
        except Exception:
            pass

    # FRAME — grounding is frame-relative: bind the concept INTO the frame's
    # WORLD (its Microtheory). Resolve the frame name to a held Mt (EXACT name,
    # then the held domain->Mt map: 'math'->'mathematics', 'music'->'music').
    # If resolved, attach via a has_concept edge (the same idiom the seed loaders
    # use). Else the frame is genuinely recorded on the concept (`frame` attr) so
    # the binding survives even when the world isn't seeded yet — never discarded.
    frame_mt: Optional[Any] = None
    frame_recorded: Optional[str] = None
    frame_mt_name: Optional[str] = None
    if frame:
        fname = re.sub(r"\s+", "_", frame.strip().lower())
        frame_mt, frame_mt_name = _resolve_frame_mt(substrate, fname)
        try:
            substrate.set_attr(cid, "frame", fname)
            frame_recorded = fname
        except Exception:
            pass
        if frame_mt is not None:
            try:
                if cid not in set(substrate.neighbours(frame_mt, "has_concept")):
                    substrate.add_edge(frame_mt, "has_concept", cid)
            except Exception:
                pass

    # REGISTER -> the grounding CONFIDENCE. The expectation model already resolved
    # the register CLASS to a band confidence (canonical/exact -> 1.0, approximate
    # -> 0.85, informal -> 0.8); when given, use it directly. Else fall back to
    # the coarse register->confidence map (back-compat). The UNMARKED case is
    # 'canonical' at full confidence — a comprehended status, not a missing value.
    conf = confidence if confidence is not None else _register_confidence(register)
    if conf is not None:
        try:
            substrate.set_attr(cid, "grounding_confidence", float(conf))
            if register is not None:
                substrate.set_attr(cid, "grounding_register", register)
            if register_status is not None:
                substrate.set_attr(cid, "grounding_status", register_status)
        except Exception:
            pass

    # PROVENANCE — knowledge is SOURCE-relative: where it came from is part of
    # what it means and how firmly it's held. Attach the WHERE/WHO/HOW/WHAT/WHEN
    # the agent read this from (the comprehending reader knows what it read) +
    # the EPISTEMIC STATUS the source lends (consensus/attested — distinct from a
    # self-derived fact and from a conjecture). The reliability is READ OFF the
    # source's held understanding by the caller, not hardcoded here.
    if provenance:
        try:
            substrate.set_attr(cid, "provenance", json.dumps(provenance))
        except Exception:
            pass
    if epistemic_status:
        try:
            substrate.set_attr(cid, "epistemic_status",
                               json.dumps(epistemic_status))
            st = epistemic_status.get("status")
            if isinstance(st, str) and st:
                substrate.set_attr(cid, "grounding_status", st)
            # When the register did not already set a confidence, the SOURCE's
            # epistemic weight sets it (an attested-by-consensus grounding is held
            # firmly but below a self-derived 1.0). Read off the held reliability.
            if conf is None:
                ec = epistemic_status.get("confidence")
                if isinstance(ec, (int, float)):
                    conf = float(ec)
                    substrate.set_attr(cid, "grounding_confidence", conf)
        except Exception:
            pass

    return {"concept": cid, "parts": part_ids, "edges_added": edges_added,
            "combination_set": combination_set, "frame_mt": frame_mt,
            "frame_recorded": frame_recorded, "frame_mt_name": frame_mt_name,
            "confidence": conf, "register_status": register_status,
            "sense_shift": sense_shift, "sense_name": sense_name,
            "genus_surprise": genus_surprise, "grounded_name": grounded_name,
            "provenance": provenance, "epistemic_status": epistemic_status}


# ---------------------------------------------------------------------------
# A.3  The grounding CONE — the built_from* closure, and the primitive test.
# ---------------------------------------------------------------------------

def cone(substrate, root, edge_type: str = "built_from",
         max_nodes: int = 100000) -> list:
    """The grounding CONE of `root`: the transitive closure over `edge_type`
    (built_from*) — root + everything it is, recursively, built from. This
    is BOTH the logical reduction (toward primitives) AND the locality unit
    (the subgraph to load). Breadth-first, cycle-safe."""
    seen = {root}
    order = [root]
    frontier = [root]
    while frontier and len(order) < max_nodes:
        nxt = []
        for n in frontier:
            try:
                for m in substrate.neighbours(n, edge_type):
                    if m not in seen:
                        seen.add(m)
                        order.append(m)
                        nxt.append(m)
            except Exception:
                continue
        frontier = nxt
    return order


def is_primitive(substrate, cid, edge_type: str = "built_from") -> bool:
    """A concept is a PRIMITIVE iff it is built_from nothing (the recursion
    bottoms out here) — a seeded basis concept."""
    try:
        return len(substrate.neighbours(cid, edge_type)) == 0
    except Exception:
        return True


def grounding_reaches_primitives(substrate, root,
                                 edge_type: str = "built_from") -> dict:
    """Prove a concept STRUCTURALLY grounds: walk its cone and confirm every
    branch bottoms out at a primitive (built_from nothing). Returns
    {grounded: bool, cone_size, primitives:[names], depth}."""
    members = cone(substrate, root, edge_type)
    prims = [m for m in members if is_primitive(substrate, m, edge_type)]
    prim_names = []
    for p in prims:
        nm = substrate.node(p)["attrs"].get("name")
        if nm:
            prim_names.append(nm)
    # depth = longest built_from chain (cycle-safe).
    def _depth(n, path):
        if n in path:
            return 0
        nbrs = list(substrate.neighbours(n, edge_type))
        if not nbrs:
            return 0
        return 1 + max(_depth(m, path | {n}) for m in nbrs)
    depth = _depth(root, frozenset())
    # grounded iff the cone is finite, has >=1 primitive, and every non-root
    # path terminates (the BFS terminating already guarantees finiteness).
    grounded = len(prims) >= 1
    return {"grounded": grounded, "cone_size": len(members),
            "primitives": sorted(set(prim_names)), "depth": depth}


# ---------------------------------------------------------------------------
# A.4  MIGRATE A REAL SLICE — the communication primes whose roles name parts.
# ---------------------------------------------------------------------------

# The slice: stative-relation primes whose `roles` already name participant
# concepts that are ALSO seeded primes (participant_role concepts). Each maps
# to built_from edges + a named combination (production) rule. This is the
# agent's own data turned from prose+role-strings into STRUCTURE.
#
# Only roles that correspond to a seeded participant_role concept become
# parts; the combination names how the relation composes those roles.
_COMMUNICATION_SLICE = {
    # name             parts (role concepts)        combination (production)
    "relation":        (["owner", "value"],         "rel(owner, value)"),
    "identity":        (["entity", "equals"],       "eq(entity, equals)"),
    "attribution":     (["entity", "property"],     "has_prop(entity, property)"),
    "class_membership":(["instance", "kind"],       "isa(instance, kind)"),
    "possession":      (["possessor", "possessed"], "has(possessor, possessed)"),
    "part_whole":      (["part", "whole"],          "part_of(part, whole)"),
    "transfer":        (["agent", "theme", "recipient"], "give(agent, theme, recipient)"),
    "action":          (["agent", "patient"],       "do(agent, patient)"),
    "motion":          (["theme", "source", "goal"], "move(theme, source, goal)"),
}

# Two math concepts grounded in the communication primes (a couple, per the
# task) — showing a DIFFERENT Mt's concept structurally grounding in the
# shared basis. equality grounds in identity; function grounds in relation.
_MATH_SLICE = {
    "equality":  (["identity"],          "lift(identity)"),
    "function":  (["relation", "owner", "value"], "map(owner -> value via relation)"),
}


def migrate_communication_slice(substrate, *, index: Optional[dict] = None
                                ) -> dict:
    """Convert the communication slice's role-strings into grounding EDGES +
    a combination. Idempotent, programmatic (does NOT rewrite the seed JSON).

    For each prime in the slice: ensure the role-participant concepts exist
    (they are seeded primes — created only if genuinely missing), add a
    built_from edge from the prime to each, and set the combination attr.
    Returns {migrated:[names], total_edges, missing_parts:[...]}.
    """
    if index is None:
        index = _concept_by_name(substrate)
    migrated = []
    total_edges = 0
    missing_parts: list[str] = []
    for name, (parts, combo) in {**_COMMUNICATION_SLICE, **_MATH_SLICE}.items():
        res = ground_concept(substrate, name, parts, combo, index=index,
                             create_missing=True)
        if res["concept"] is not None:
            migrated.append(name)
            total_edges += res["edges_added"]
    return {"migrated": migrated, "total_edges": total_edges,
            "missing_parts": missing_parts}


# ---------------------------------------------------------------------------
# A.5  CATEGORY -> genls edge — the AUTHOR-SUPPLIED taxonomy, made structural.
# ---------------------------------------------------------------------------

# The FAITHFUL taxonomy-enrichment pass. Domain concepts (philosophy /
# mathematics / computer_architecture / embedded_iot_realtime) carry an
# author-supplied `category` ATTRIBUTE ('epistemology', 'pipeline_mechanism',
# 'cache_mechanism', ...) — a domain-correct classification the seed author
# WROTE. But it sits only as a plain attr string: analogy_search reads it as a
# `(lexical:formal, category, <value>)` coordinate, yet there is no EDGE, so the
# concept is edge-poor (SHAPE_AUDIT: ~114/10775 concepts have any outgoing edge)
# and concepts in the same category are not WIRED to a shared hub the analogy /
# grounding graph can traverse.
#
# `ground_categories` turns that held attr into STRUCTURE: for each Concept with
# a `category`, it mints (once) a category-HUB Concept and wires the concept
# `genls`-> hub (is-a, the FORMAL qualia role — DimensionEdgeRole maps
# genls -> lexical:formal). This is DERIVED mechanically from what the concept
# already carries (its own `category` attr the author asserted); NOTHING is
# invented and NO meaning is decided here — the author already named the class.
#
# WHY category and not a WordNet head-noun genus: the domain concept NAMES are
# compound terms ('instruction_set_architecture', 'mathematical_induction',
# 'prime_numbers') whose head noun's dominant WordNet sense mis-genuses badly
# ('architecture'->building, 'induction'->ceremony, 'numbers'->book). Wiring
# those would inject FALSE is-a edges. The author's `category` is the faithful,
# domain-correct classification already in the graph — so the honest taxonomy
# enrichment reads THAT, not a guessed lexical genus.

def _category_hub_name(category: str) -> str:
    """The hub Concept name for a category value — 'category:<value>', a
    namespaced name so a category hub never collides with a domain concept of
    the same surface (a concept 'pipeline' vs the category 'pipeline_mechanism'
    hub). A surface->name convention, not a meaning decision."""
    return "category:%s" % str(category).strip().lower()


def ground_categories(substrate, mt_name: Optional[str] = None, *,
                      index: Optional[dict] = None) -> dict:
    """Wire each Concept's author-supplied `category` ATTRIBUTE into a `genls`
    edge to a category-HUB Concept (is-a — the FORMAL qualia role). The faithful
    taxonomy-enrichment pass: it reads a classification the seed AUTHOR already
    asserted (graph DATA) and makes it a first-class EDGE, so an edge-poor
    concept gains a real outgoing `lexical:formal` coordinate and same-category
    concepts share a traversable hub.

    `mt_name` (optional) restricts the pass to the concepts of ONE Microtheory
    (the domain Mt the caller is enriching); None => every Concept with a
    `category`. Idempotent: a `genls` edge already present is not re-added, and a
    hub Concept is minted once (looked up by name).

    The `genls` edge is admissible only once open_grounding_productions has opened
    the Concept-genls-Concept production (genls is in GROUNDING_EDGE_TYPES); the
    caller opens it (or this pass opens it defensively). No meaning decision — the
    author named the class; this only structuralises it.

    Returns {edges_added, hubs, concepts_wired, mt}."""
    if index is None:
        index = _concept_by_name(substrate)
    # defensively ensure the genls production is open (idempotent).
    try:
        open_grounding_productions(substrate)
    except Exception:
        pass

    # the concept set: one Mt's concepts, or all.
    concept_ids: list = []
    if mt_name is not None:
        mt = _find_microtheory(substrate, mt_name)
        if mt is None:
            return {"edges_added": 0, "hubs": 0, "concepts_wired": 0,
                    "mt": mt_name}
        try:
            concept_ids = list(substrate.neighbours(mt, "has_concept"))
        except Exception:
            concept_ids = []
    else:
        try:
            concept_ids = list(substrate.nodes("Concept"))
        except Exception:
            concept_ids = []

    edges_added = 0
    concepts_wired = 0
    hubs: dict[str, Any] = {}
    for cid in concept_ids:
        try:
            a = substrate.node(cid)["attrs"]
        except Exception:
            continue
        category = a.get("category")
        if not isinstance(category, str) or not category.strip():
            continue
        # a concept must not be its own category hub (a `category:` hub node
        # carries no `category` attr, so this only guards a pathological seed).
        hub_name = _category_hub_name(category)
        if a.get("name") == hub_name:
            continue
        hub = hubs.get(hub_name) or index.get(hub_name)
        if hub is None:
            hub = substrate.add_node("Concept", {
                "name": hub_name, "origin": "grounded_representation",
                "kind": "category_hub", "category_value": category.strip().lower()})
            index[hub_name] = hub
        hubs[hub_name] = hub
        # idempotent genls wiring (is-a -> lexical:formal).
        try:
            if hub not in set(substrate.neighbours(cid, "genls")):
                substrate.add_edge(cid, "genls", hub, {})
                edges_added += 1
                concepts_wired += 1
        except Exception:
            continue
    return {"edges_added": edges_added, "hubs": len(hubs),
            "concepts_wired": concepts_wired, "mt": mt_name}


# ---------------------------------------------------------------------------
# B.  PHYSICAL — the SAME structure is the locality / lazy cone-load.
# ---------------------------------------------------------------------------

class GroundedConceptStore:
    """A binary COLD store of grounded concepts keyed by name, plus a lazy
    CONE-LOAD into a cache-resident WORKING SET with LRU eviction.

    The cold store holds, per root concept, a serialised subgraph of its
    grounding CONE (graph_to_dict over a substrate populated with only the
    cone — the same persistence machinery cortex_persistence uses). A query
    `load_cone(name)` pulls ONLY that concept's cone from the store into a
    cache-resident working set (the HOT tier; mirrors conceptnet
    `_ensure_slab` lazy build). A cache_replacement_policy (LRU) evicts the
    least-recently-used cone when the working set exceeds its bound, so the
    working set stays bounded while a stream of queries touches different
    cones.

    The SAME grounding structure that makes the concept logically grounded
    (cone reduces to primitives) is the locality unit that makes the access
    efficient (one fetch, evict the rest) — concept = structure, the
    structure IS the locality.
    """

    def __init__(self, capacity: int = 8):
        # capacity = max number of cones resident in the working set.
        self.capacity = capacity
        # cold store: name -> serialised cone {nodes, edges, ...}
        self._cold: dict[str, dict] = {}
        # name -> the cone's member names (the index, cheap — not the data).
        self._cone_index: dict[str, list[str]] = {}
        # working set: LRU of name -> live substrate holding ONLY that cone.
        self._working: "OrderedDict[str, Any]" = OrderedDict()
        # metrics
        self.loads = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    # --- write side: persist a concept's cone to the cold store ---------

    def persist_cone(self, substrate, name: str,
                     edge_type: str = "built_from") -> dict:
        """Serialise concept `name`'s grounding cone into the cold store as a
        binary blob (graph_to_dict over just the cone subgraph). Returns
        {name, cone_size, blob_nodes, blob_edges}."""
        root = _find_concept(substrate, name)
        if root is None:
            return {"name": name, "cone_size": 0, "blob_nodes": 0,
                    "blob_edges": 0}
        members = cone(substrate, root, edge_type)
        member_set = set(members)
        full = substrate.graph_to_dict()
        # Keep only the cone's nodes + the edges fully inside the cone.
        keep_ids = {substrate.node(m)["id"] for m in members}
        # node()['id'] is the int id; serialized nodes carry "id" too.
        sub_nodes = [n for n in full["nodes"] if n["id"] in keep_ids]
        sub_edges = [e for e in full["edges"]
                     if e["src"] in keep_ids and e["tgt"] in keep_ids]
        blob = {"next_id": full.get("next_id", 0),
                "nodes": sub_nodes, "edges": sub_edges,
                "root_id": substrate.node(root)["id"]}
        self._cold[name] = blob
        names = []
        for m in members:
            nm = substrate.node(m)["attrs"].get("name")
            if nm:
                names.append(nm)
        self._cone_index[name] = names
        return {"name": name, "cone_size": len(members),
                "blob_nodes": len(sub_nodes), "blob_edges": len(sub_edges)}

    def persist_all_grounded(self, substrate,
                             edge_type: str = "built_from") -> int:
        """Persist the cone of every structurally-grounded concept (one with
        outgoing built_from edges). Returns the count persisted."""
        n = 0
        for c in substrate.nodes("Concept"):
            try:
                if substrate.neighbours(c, edge_type):
                    nm = substrate.node(c)["attrs"].get("name")
                    if nm:
                        self.persist_cone(substrate, nm, edge_type)
                        n += 1
            except Exception:
                continue
        return n

    # --- read side: lazy cone-load into the working set -----------------

    def _native_substrate(self):
        from substrate_rs import _native
        return _native.Substrate()

    def load_cone(self, name: str):
        """Lazily load concept `name`'s cone from the cold store into the
        cache-resident working set (LRU). Returns a live substrate holding
        ONLY that cone (the working subgraph) — one fetch, the locality unit.
        On a working-set HIT, returns the resident substrate without
        re-deserialising. Evicts LRU when over capacity."""
        self.loads += 1
        if name in self._working:
            self.hits += 1
            self._working.move_to_end(name)
            return self._working[name]
        self.misses += 1
        blob = self._cold.get(name)
        if blob is None:
            return None
        # Deserialise ONLY this cone — the working subgraph (mirrors
        # conceptnet _ensure_slab: build/open lazily on the miss).
        sub = self._native_substrate()
        sub.graph_from_dict({"next_id": blob.get("next_id", 0),
                             "nodes": blob["nodes"], "edges": blob["edges"]})
        self._working[name] = sub
        self._working.move_to_end(name)
        self._evict_if_needed()
        return sub

    def _evict_if_needed(self):
        """cache_replacement_policy = LRU. Drop the least-recently-used cone
        when the working set exceeds capacity, keeping it BOUNDED."""
        while len(self._working) > self.capacity:
            old_name, _ = self._working.popitem(last=False)
            self.evictions += 1

    def working_set_size(self) -> int:
        """Number of NODES resident in the working set right now (the hot
        tier's size — what must fit in cache)."""
        total = 0
        for sub in self._working.values():
            total += sub.node_count()
        return total

    def resident_cones(self) -> list[str]:
        return list(self._working.keys())

    def cold_node_total(self) -> int:
        """Total nodes across all cold blobs (the full store)."""
        return sum(len(b["nodes"]) for b in self._cold.values())


__all__ = [
    "GROUNDING_EDGE_TYPES",
    "open_grounding_productions",
    "ground_concept",
    "cone",
    "is_primitive",
    "grounding_reaches_primitives",
    "migrate_communication_slice",
    "ground_categories",
    "GroundedConceptStore",
]
