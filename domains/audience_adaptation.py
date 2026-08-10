"""audience_adaptation — MANIFOLD-RELATIVE CONTENT SHAPING: render a reply's concepts RELATIVE to
the interlocutor's manifold, not in the agent's ABSOLUTE ontology (the creator's founding principle
applied to conversation, 2026-07-04). "A value is a position in an axis, not a 5" — here, a concept's
DELIVERABILITY is a position relative to what THIS interlocutor's manifold holds. A concept NOT live
in the manifold is a GAP that must be abstracted / flagged / selected-away, never dumped flat.

WHY THIS EXISTS (the live failure it fixes): asked "how are you organised?", the jabberwock listed
`video_coding_theory, cloud_infrastructure, machine_learning` FLATLY to Cornelius Vane, a Victorian of
1885 with no concept of a computer. The interlocutor model was BUILT and fed a grounded audience, but
its effect was invisible — the agent answered from its FIXED self-model regardless of who asked. Vane's
verdict: it "did NOT feel like it was modelling me as a specific interlocutor." This module makes the
reply MANIFOLD-RELATIVE so the interlocutor VISIBLY reshapes what is said.

CLAUDE.md discipline. This is a WORLD-ADAPTER-SHAPED / BOUNDARY faculty — the SAME admissible class as
`domains/sense_of_reference` (reference-liveness = a residual/collapse against the manifold) and
`domains/interlocutor_model` (the collapse faculty pointed at the person). It holds NO agent state,
makes NO decision over GRAPH STATE, and reuses the arc's existing machinery READ-ONLY:

  * the manifold TYPE is `sense_of_reference.estimate_manifold_type` (a cue count over the accumulated
    known_concepts — the SAME type estimate the reference faculty uses: technical/gamer vs literary/
    formal/general), imported and called, never reimplemented;
  * the grounded common-ground split is `audience_driven_production.residual_vs_audience` against
    `audience_driven_production.audience_model` (VERBATIM reuse, read-only) — a concept already in the
    interlocutor's OBSERVED known_concepts is credited LIVE (the shared model), the rest is the residual;
  * CONCEPT-LIVENESS is then the manifold-conditioned residual, exactly the sense_of_reference shape: a
    concept whose WORLD the manifold does NOT hold (a modern-technical domain against a period/non-
    technical manifold) is FOREIGN — a residual — and must be abstracted/flagged, not landed flat.

THE DECISION IS MANIFOLD-CONDITIONED, NOT A HARDCODED "if Victorian" BRANCH. Adaptation fires only on
an OBSERVED, CONFIDENTLY period/non-technical manifold (formal/literary, `committed`), and WHICH concepts
are foreign is a residual against that manifold (grounded-known concepts are rescued LIVE even in a
period manifold; a technical manifold holds the modern world so NOTHING is foreign — full content lands).
An unobserved / default / technical / under-typed manifold adapts NOTHING: the concept list is returned
byte-identical (no regression). The abstraction of the foreign group is a COARSE umbrella term — the
manifold model is coarse (known_concepts + a cue-count type), reported honestly; the point is the reply
is RELATIVE to the manifold rather than an absolute dump.

THE CONCEPT->DIMENSION MAP IS EDGE-LEARNED (2026-07-04). The 60-token modern-tech cue table this
module once carried is RETIRED; a concept's world dimension is now read from its EDGES —
`concept_graph.world_dimension` places it by tf-idf cosine of its has_concept neighbourhood to a small
set of labelled anchor microtheories (an N-step recursive coarse-to-fine descent; foreignness = depth
of co-descent between the concept and the interlocutor's frame). Where the graph never grounded a
concept with concept edges (computer_architecture, compilers, mathematics) the placement honestly
falls to a DEMOTED small labelled seed anchor, reported per-concept by `world_dimension`'s source.

DONKEY=0: no fit, no gradient, no LM. The type is a cue count; the liveness split is the reused residual;
the world dimension is tf-idf arithmetic over graph membership + a small labelled anchor residual.
"""
from __future__ import annotations

import re
from typing import Optional

import domains.sense_of_reference as _sr
from domains import frame as _fr
from domains import concept_graph as _cg

# The two coarse WORLD dimensions the audience-adaptation foreign-check runs over. A reply concept
# belongs to exactly one (its `concept_dimension`); the interlocutor's frame either holds that
# dimension (live) or not (foreign). "universal" is the period-compatible / timeless world (in EVERY
# frame); "modern_tech" is the post-1885 computing world (absent from a committed period frame). These
# ARE `concept_graph`'s coarse RUNG-1 regions (REGION_UNIVERSAL / REGION_MODERN) — the labels align so
# the frame membership check reads the edge-learned dimension directly.
DIM_UNIVERSAL = _cg.REGION_UNIVERSAL       # "universal"
DIM_MODERN_TECH = _cg.REGION_MODERN        # "modern_tech"

# The manifolds that HOLD the modern-technical world: a modern-tech concept is LIVE for them, so
# NOTHING is foreign and the full technical content lands (byte-identical to the un-adapted reply).
MODERN_MANIFOLD_TYPES = frozenset({"technical", "gamer"})
# The confidently period / non-technical manifolds: modern-tech concepts are a residual (foreign)
# here. Adaptation fires ONLY on one of these, AND only once `committed` (>=2 cues) — an under-typed
# manifold HEDGES (adapts nothing), the SAME sharpen-turn-by-turn discipline sense_of_reference uses.
PERIOD_MANIFOLD_TYPES = frozenset({"formal", "literary"})


def _concept_tokens(concept: str) -> list:
    """Tokenise a concept / domain name into lower-case word parts (split on underscore and non-alpha).
    'video_coding_theory' -> ['video','coding','theory']; 'machine_learning' -> ['machine','learning']."""
    return [t for t in re.split(r"[^a-z]+", str(concept).lower()) if t]


def concept_is_modern_tech(concept: str) -> bool:
    """True iff `concept`'s world is MODERN-TECHNICAL — the AGENT-LESS rung-1 call. The 60-token
    `_MODERN_TECH_CUES` table this once carried is RETIRED: with a substrate the world dimension is
    edge-LEARNED (`concept_dimension(concept, agent)` -> `concept_graph.world_dimension`, tf-idf over
    the domain's has_concept neighbourhood). This agent-less entry point has NO graph to read, so it
    honestly defers to the DEMOTED small labelled seed anchor (`concept_graph.world_dimension_offline`
    over `_SEED_ANCHOR_MODERN`) — the residual the connectivity falls short on, documented as such."""
    return _cg.world_dimension_offline(str(concept)) == _cg.REGION_MODERN


def manifold_type(interlocutor: dict) -> dict:
    """The interlocutor's estimated world-TYPE, via `sense_of_reference.estimate_manifold_type` over its
    accumulated known_concepts AND its tracked conversational REGISTER (read-only reuse). Returns that
    faculty's dict {type, confidence, committed, scores}. The register (a formal register types the
    interlocutor `formal`/committed by turn 1-2, before content-concepts accumulate) rides on the
    interlocutor snapshot as `register`/`formal_cues`/`casual_cues` (threaded by the world adapter from
    the tracked Interlocutor node); a snapshot that carries none falls back to the content-only estimate."""
    interlocutor = interlocutor or {}
    known = interlocutor.get("known_concepts") or []
    return _sr.estimate_manifold_type(
        known,
        register=interlocutor.get("register"),
        formal_cues=interlocutor.get("formal_cues", 0.0),
        casual_cues=interlocutor.get("casual_cues", 0.0),
    )


def fires_for(interlocutor: dict) -> bool:
    """Does content-adaptation FIRE for this interlocutor? Only on an OBSERVED, CONFIDENTLY period/
    non-technical manifold (formal/literary, `committed`). An unobserved / default / technical / gamer /
    under-typed manifold does NOT fire — the reply is delivered in full (byte-identical). This is the
    no-regression gate: adaptation is visible ONLY when the agent has actually modelled a specific
    non-matching interlocutor."""
    interlocutor = interlocutor or {}
    if not interlocutor.get("observed"):
        return False
    est = manifold_type(interlocutor)
    return bool(est.get("committed")) and est.get("type") in PERIOD_MANIFOLD_TYPES


def _grounded_known(agent, concepts, interlocutor: dict) -> set:
    """The subset of `concepts` the interlocutor's OBSERVED manifold already holds (common ground),
    via `audience_driven_production.residual_vs_audience` against `audience_model` — VERBATIM read-only
    reuse. A grounded-known concept is rescued LIVE even in a period manifold (if this Victorian somehow
    knew 'machine_learning', it would land). Ungrounded/unobserved -> empty (nothing credited)."""
    try:
        import domains.audience_driven_production as _adp
        bundle = _adp.audience_model(agent, interlocutor)
        residual = _adp.residual_vs_audience(agent, set(map(str, concepts)), bundle)
        return set(residual.get("known") or ())
    except Exception:
        return set()


def concept_dimension(concept: str, agent=None) -> str:
    """The WORLD-DIMENSION (rung-1 region) a reply concept sits in — now LEARNED FROM EDGES. With a
    substrate (`agent`), `concept_graph.world_dimension` reads the concept's has_concept neighbourhood
    (tf-idf cosine to the labelled region anchors): a domain whose concepts cluster with the tech
    anchors (machine_learning near neural_networks, cloud near operating_systems) is `modern_tech`;
    one that clusters with the period anchors (ethics near philosophy) is `universal`. A zero-edge /
    ambiguous concept (computer_architecture, compilers, mathematics) falls to the demoted seed anchor
    — reported by `world_dimension`'s source. Agent-less, it uses the anchor alone. This is the
    concept->dimension map the frame-membership foreign-check queries against."""
    if agent is not None:
        return _cg.world_dimension(agent, str(concept))[0]
    return DIM_MODERN_TECH if concept_is_modern_tech(concept) else DIM_UNIVERSAL


def interlocutor_frame(agent, interlocutor: dict):
    """The INTERLOCUTOR'S MANIFOLD AS A FRAME (graph-resident) — a Frame node whose dimensions are the
    WORLDS this interlocutor weights. Built from what they weight: their estimated TYPE + register
    select the dimensions. Every manifold holds the `universal` (timeless) world; the `modern_tech`
    world is in the frame IFF the manifold is NOT a committed period/non-technical one — i.e. exactly
    when audience-adaptation does not fire (a default / under-typed / technical / gamer manifold holds
    the modern world, so nothing modern is foreign; a committed Victorian formal manifold does not).

    The DECISION "is a concept foreign?" then falls out of frame-membership: a concept whose dimension
    is not in this frame is foreign (`split_by_manifold`). Refreshed per interlocutor by a stable key
    so the frame is a live view, not an accumulation.

    RELATIVE-TO-FRAME (edge-learned): when adaptation fires, the frame's dimensions are the rung-1
    regions the interlocutor's OWN known_concepts occupy (`concept_graph.frame_dimensions` — each
    concept edge-placed), NOT a hand table. Vane's ethics/virtue/philosophy concepts all place in
    `universal` -> frame = {universal} -> a modern-tech concept (whose region is graph-DISTANT) is
    foreign. A non-firing manifold holds the modern world too (nothing modern is foreign)."""
    if fires_for(interlocutor):
        known = (interlocutor or {}).get("known_concepts") or []
        # min_count=2: a lone modern outlier in a period manifold does NOT admit the modern dimension
        # into the frame (it is rescued per-concept as grounded common ground instead).
        dims = {d: 1.0 for d in _cg.frame_dimensions(agent, known, min_count=2)}   # frame's OWN dims
    else:
        dims = {DIM_UNIVERSAL: 1.0, DIM_MODERN_TECH: 1.0}   # holds the modern world -> nothing foreign
    key = "manifold_frame::" + str((interlocutor or {}).get("id", "user"))
    return _fr.build_frame(agent, dims, key)


def split_by_manifold(agent, concepts, interlocutor: dict) -> dict:
    """Split `concepts` into LIVE (deliverable in the manifold) vs FOREIGN (its world NOT in the
    manifold's frame), MANIFOLD-CONDITIONED — the split is now a FRAME-MEMBERSHIP QUERY, not the
    coarse cue-table branch. Build the interlocutor's manifold-as-frame; a concept is FOREIGN iff its
    `concept_dimension` is NOT in that frame AND it is not grounded-known common ground. Everything
    else is LIVE. Returns {live, foreign, manifold_type, committed, grounded_known, fired}.

    The firing gate is folded into the frame: a non-firing manifold's frame holds `modern_tech`, so
    every concept's dimension is in-frame -> the whole list is live (byte-identical no-regression). A
    grounded-known modern concept is rescued LIVE (observed common ground overrides the frame)."""
    concepts = [str(c) for c in concepts]
    est = manifold_type(interlocutor)
    fired = fires_for(interlocutor)
    frame = interlocutor_frame(agent, interlocutor)
    grounded = _grounded_known(agent, concepts, interlocutor) if fired else set()
    live, foreign = [], []
    for c in concepts:
        if c in grounded:
            live.append(c)                                   # rescued by observed common ground
        elif _fr.in_frame(frame, concept_dimension(c, agent), agent):
            live.append(c)                                   # its world is in the frame -> lands
        else:
            foreign.append(c)                                # world absent from the frame -> residual
    return {"live": live, "foreign": foreign, "manifold_type": est.get("type"),
            "committed": bool(est.get("committed")), "grounded_known": sorted(grounded),
            "fired": fired}


# The COARSE umbrella the foreign (manifold-foreign) group is abstracted to — a level the manifold HAS
# ("modern arts") plus a MANIFOLD-RELATIVE honest flag ("your world" = whatever the manifold holds, not
# a period-specific string). Documented coarse: the abstraction is a single umbrella, not per-concept.
_ABSTRACTION = "certain modern arts unfamiliar in your world"


def abstraction_for(foreign: list, manifold_type_name: Optional[str] = None) -> str:
    """The umbrella term the FOREIGN concept group is abstracted to — a general level the manifold grasps,
    with a manifold-relative honest flag. Coarse by design (one umbrella for the whole foreign group)."""
    return _ABSTRACTION


def adapt_concepts(agent, concepts, interlocutor: dict) -> dict:
    """MANIFOLD-RELATIVE delivery of `concepts`. Returns {adapted, live, foreign, manifold_type,
    adapted_flag, abstraction, grounded_known}.

      * adaptation does NOT fire (unobserved/default/technical/under-typed manifold) -> `adapted` is the
        concept list BYTE-IDENTICAL (order preserved), `adapted_flag` False — no regression;
      * adaptation FIRES (observed, committed, period/non-technical) -> LIVE concepts land (in original
        order); the FOREIGN group (modern-technical, not grounded-known) is abstracted to ONE umbrella
        term (`abstraction`) appended after the live ones, instead of being dumped flat. If there are no
        foreign concepts even though it fires, `adapted` is the live list unchanged (still no umbrella).

    `adapted` is the shaped display list the render path joins (`conversation_action._oxford` / the
    self-organisation 'I am organised into ...' surface). The DECISION of which concepts are foreign is
    `split_by_manifold`'s manifold residual; this only assembles the display list from it."""
    split = split_by_manifold(agent, concepts, interlocutor)
    live, foreign = split["live"], split["foreign"]
    if not split["fired"] or not foreign:
        return {"adapted": list(live), "live": live, "foreign": foreign,
                "manifold_type": split["manifold_type"], "adapted_flag": False,
                "fired": split["fired"], "abstraction": None,
                "grounded_known": split["grounded_known"]}
    abstraction = abstraction_for(foreign, split["manifold_type"])
    return {"adapted": list(live) + [abstraction], "live": live, "foreign": foreign,
            "manifold_type": split["manifold_type"], "adapted_flag": True,
            "fired": True, "abstraction": abstraction,
            "grounded_known": split["grounded_known"]}


__all__ = [
    "MODERN_MANIFOLD_TYPES", "PERIOD_MANIFOLD_TYPES", "DIM_UNIVERSAL", "DIM_MODERN_TECH",
    "concept_is_modern_tech", "concept_dimension", "manifold_type", "fires_for",
    "interlocutor_frame", "split_by_manifold", "abstraction_for", "adapt_concepts",
]
