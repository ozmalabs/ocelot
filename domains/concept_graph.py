"""concept_graph — LEARN A CONCEPT'S DIMENSION FROM ITS EDGES (the creator's log-number ontology,
2026-07-04). A concept's position in the frame geometry is a LOG-NUMBER read off the graph, and
learning it is an N-STEP RECURSIVE COARSE-TO-FINE DESCENT — the dynamic-quantization loop recursed:

    position(concept) = PATH:  region -> sub-region -> home -> ...
                        each rung = a COARSE BIN (which sub-region, from edges at that granularity)
                        + a RESIDUAL that recurses to the next finer rung (self-similar), FOVEATED
                        (descend only while the residual is still edge-resolvable — depth is dynamic
                        per concept, not a fixed two).

The classic "exponent + mantissa" two-step is the DEGENERATE N=2 case: rung 1 = which coarse
dimension (the EXPONENT), the recursion's tail = the fine within-dimension log-position (the MANTISSA
= graph-closeness to the region centroid). Deeper concepts keep descending; a coarse distinction
resolves at rung 1 and stops (foveated).

FOREIGNNESS / LIVENESS = DEPTH OF CO-DESCENT. Two concepts (or a concept vs the interlocutor's frame)
share a path prefix down to some rung k and fork at k+1. Closeness = how DEEP the shared path runs
before it forks. A modern-tech concept and one of Vane's ethics concepts fork at rung 1 (different
world region) -> very foreign; two modern-tech concepts share several rungs before splitting -> close.
`shared_depth` computes exactly this common-prefix length.

WHAT THE EDGES ARE (the richest concept-graph the substrate already holds — mechanical graph READ,
no agent decision, no new heavy algorithm): each Microtheory's HAS_CONCEPT membership (Mt -has_concept->
Concept) gives it a token neighbourhood (the concept names + categories it holds); a concept's
neighbourhood-closeness to a small labelled set of ANCHOR microtheories (real, edge-bearing graph
nodes) is its coarse bin. This is tf-idf cosine over graph-resident membership — a short-path /
neighbourhood read, the simple form the task asks for, not a learned clustering.

HONEST CONNECTIVITY (measured, not assumed — `connectivity_report`): the has_concept neighbourhood
SEPARATES modern-tech from period for the concept-BEARING domains (machine_learning near
neural_networks, cloud near operating_systems, ethics near philosophy). It FALLS SHORT on domains the
graph never grounded with concept edges — `computer_architecture` (2 tokens), `compilers` (1),
`mathematics` (1) carry (almost) no has_concept edges, and one generic-token domain (`communication`)
ties — so those fall to a SMALL, LABELLED seed anchor (`_SEED_ANCHOR_MODERN`), the demoted residual of
the old 60-token cue table. `world_dimension` reports which path each concept took (edge vs anchor).

LEXICAL-DEGREE NORMALIZATION (the edge-confidence is degree-free). A raw region cosine PENALISES a
LOW-DEGREE concept: a single-token idiom (`jabberwock`, `rabbit_hole`, `red_queen`, `alice`) or a bare
gaming token (`game`, `player`, `portal`, `glados`) whose one edge points cleanly into a region still
scores a TINY absolute cosine — for a token fully contained in a big anchor the cosine collapses to
1/‖anchor‖ (the literature anchor carries 69 tokens), so it falls JUST under an absolute floor even
though its membership is unambiguous. The fix is NOT a lower floor (that would let noise through) but a
degree-normalized CONFIDENCE with two degree-free parts:

  * CLARITY  = best / (best + other)  — the winning region's SHARE of the concept's region-affinity.
    A ratio of the concept's OWN two cosines, so the absolute scale (and hence the concept's degree)
    cancels: a sparse-but-decisive vector whose whole edge points one way scores ~1.0; a genuinely
    ambiguous vector split across regions scores ~0.5; tf-idf STRENGTH is preserved (unlike bare token
    membership, which would tie `game` 1:1 because "game" sits in both regions' anchor bags).
  * GROUNDEDNESS — the winner must actually EXPLAIN the concept, established EITHER by absolute cosine
    strength (`best >= _CONF_FLOOR`, the path RICH concepts already took — so no regression, by
    construction) OR, for a sparse concept whose cosine is small ONLY because the anchor is large, by
    edge-mass CONTAINMENT (`_containment >= _CONTAIN_FLOOR`: at least half the concept's own tf-idf
    mass lands on tokens the winning region's anchors carry). Containment is the degree-normalizer: it
    rescues a perfectly-contained sparse token (cosine = 1/‖anchor‖) while REJECTING a spurious tiny
    one-sided match (a nonsense token whose lone matching word is a small mass fraction).

A concept is EDGE-placed iff it matches at least one region (best > 0), CLARITY clears `_CLARITY_FLOOR`
(the winner holds >= twice the rival's affinity) AND it is grounded. A genuinely ambiguous low-degree
concept (edges split ~evenly, e.g. `communication`) fails CLARITY and stays anchored — same low degree
as the idioms, OPPOSITE verdict, decided by clarity-of-membership, not by degree.

DONKEY=0: no fit, no gradient, no LM — tf-idf arithmetic over graph membership + a labelled anchor.
"""
from __future__ import annotations

import math
import re
from typing import Optional

# --------------------------------------------------------------------------- #
#  Labelled COARSE-REGION anchors — real, edge-bearing Microtheory NODES whose
#  has_concept neighbourhoods seed the two top-level world regions. A concept's
#  region is its neighbourhood-nearest anchor set. These are graph nodes, not a
#  token list — the placement is edge-distance to them.
# --------------------------------------------------------------------------- #
REGION_MODERN = "modern_tech"
REGION_UNIVERSAL = "universal"

_REGION_ANCHORS = {
    REGION_MODERN: ["operating_systems", "network_protocols", "neural_networks",
                    "data_structures_algorithms", "compiler_theory", "digital_audio",
                    # the taught GAMING world (seeds/gaming_microtheory.json) — video games are a
                    # post-Victorian art form, so a gaming referent sits in the modern region: live
                    # for a gamer frame, the modern-region residual for Vane's period frame.
                    "video_games",
                    # the taught TECH worlds (seeds/computer_architecture_microtheory.json,
                    # seeds/cloud_infrastructure_anchor_microtheory.json) — post-1885 computing,
                    # foreign to Vane's Victorian frame. computer_architecture and cloud_infrastructure
                    # had zero / diffuse has_concept edges; now edge-bearing modern-region anchors.
                    "computer_architecture", "cloud_infrastructure"],
    REGION_UNIVERSAL: ["philosophy", "ethics", "physics_foundation", "biology_foundation",
                       "law_jurisprudence", "agriculture",
                       # the taught LITERARY + PERIOD worlds (seeds/literary_microtheory.json,
                       # seeds/period_microtheory.json) — timeless-side anchors. Literature grounds
                       # the agent's own name (Jabberwock, from Carroll) and graduated allusions
                       # ('down the rabbit hole'); period_thought grounds Vane's Victorian frame.
                       "literature", "period_thought",
                       # the taught TIMELESS tech worlds (seeds/mathematics_microtheory.json,
                       # seeds/art_design_drawing_anchor_microtheory.json) — mathematics (theorem,
                       # proof, geometry) and the timeless drawing sense (line, colour, composition)
                       # are as present in Vane's Victorian world as in a modern one. (communication is
                       # genuinely DIFFUSE and deliberately NOT an anchor — see teach_tech_microtheories.)
                       "mathematics", "art_design_drawing"],
}

# The SMALL DEMOTED seed anchor (the residual of the retired 60-token _MODERN_TECH_CUES): the modern
# tokens the graph could NOT edge-learn — used ONLY when the neighbourhood signal is absent/ambiguous
# (a zero-edge concept like computer_architecture/compilers, or an agent-less caller with no graph).
# Documented honestly: this is the labelled bootstrap the connectivity falls short on, not the primary
# path. In the live agent-bearing path only {cloud, compiler(s), computer, computing} actually fire.
_SEED_ANCHOR_MODERN = frozenset("""
    computer computing computers cpu gpu processor microprocessor transistor semiconductor bytecode
    compiler compilers kernel runtime kubernetes container virtualization serverless
    machine learning neural network networks protocol protocols internet ethernet packet
    cloud codec codecs video coding database databases datastore embedded iot cyber cybersecurity
    cryptography encryption blockchain
""".split())

_CONF_FLOOR = 0.08      # absolute-strength grounding: a rich concept whose region cosine clears this
                        # is grounded by strength alone (the path rich concepts already took — kept so
                        # the change is regression-free by construction).
_CLARITY_FLOOR = 2 / 3  # the winner must hold >= twice the rival region's affinity (best >= 2*other):
                        # a degree-free dominance test that subsumes the old raw margin.
_CONTAIN_FLOOR = 0.5    # degree-normalized grounding: a sparse concept whose absolute cosine is diluted
                        # by the anchor's size is still grounded if >= half its own edge-mass lands on
                        # the winning region's anchor tokens (rescues contained idioms, rejects noise).
_DESCEND_EPS = 0.02     # foveation: stop descending when the finer rung adds < this much closeness

_STOP = frozenset("the and for with that this from into are was not you your one two per its via".split())

# per-agent cache of the tf-idf model (keyed by id(agent)); mechanical, a performance cache only.
_CACHE: dict = {}


def _tok(x) -> list:
    return [t for t in re.split(r"[^a-z0-9]+", str(x).lower()) if len(t) > 2]


# --------------------------------------------------------------------------- #
#  MODEL — each Microtheory's tf-idf token vector, read from has_concept edges.
# --------------------------------------------------------------------------- #

def _build_model(agent) -> dict:
    """Read the substrate: each Microtheory's token bag = the names+categories of the Concepts it
    holds (Mt -has_concept-> Concept) plus its own name tokens (so a zero-concept Mt still has a
    minimal vector). Returns {mt_tokens, df, N, mt_names}. Pure graph read."""
    s = agent.s
    mt_by_name = {}
    for nid in s.nodes("Microtheory"):
        nm = s.node(nid)["attrs"].get("name")
        if nm:
            mt_by_name[nm] = nid
    mt_tokens: dict = {}
    for nm, nid in mt_by_name.items():
        bag: dict = {}
        for cid in s.neighbours(nid, "has_concept"):
            at = s.node(cid)["attrs"]
            for t in _tok(at.get("name", "")) + _tok(at.get("category", "")):
                if t not in _STOP:
                    bag[t] = bag.get(t, 0) + 1
        for t in _tok(nm):
            if t not in _STOP:
                bag[t] = bag.get(t, 0) + 1
        mt_tokens[nm] = bag
    df: dict = {}
    for bag in mt_tokens.values():
        for t in bag:
            df[t] = df.get(t, 0) + 1
    return {"mt_tokens": mt_tokens, "df": df, "N": max(1, len(mt_tokens))}


def _model(agent) -> dict:
    key = id(agent)
    m = _CACHE.get(key)
    # invalidate if the graph grew (new microtheories taught) — cheap membership check.
    if m is None or m.get("_mt_count") != len(agent.s.nodes("Microtheory")):
        m = _build_model(agent)
        m["_mt_count"] = len(agent.s.nodes("Microtheory"))
        _CACHE[key] = m
    return m


def _vec(m: dict, name: str) -> dict:
    """tf-idf vector for a microtheory name OR a bare concept string. A concept with no microtheory
    bag falls back to its own name tokens (still an edge-carried attr — the concept's own label)."""
    bag = m["mt_tokens"].get(name)
    if not bag:
        bag = {t: 1 for t in _tok(name)}
    N, df = m["N"], m["df"]
    return {t: c * math.log(N / (1 + df.get(t, 0))) for t, c in bag.items()}


def _cos(a: dict, b: dict) -> float:
    ks = set(a) & set(b)
    num = sum(a[k] * b[k] for k in ks)
    da = math.sqrt(sum(x * x for x in a.values()))
    db = math.sqrt(sum(x * x for x in b.values()))
    return num / (da * db) if da and db else 0.0


def bag_size(agent, concept: str) -> int:
    """How many has_concept tokens the concept's microtheory carries — the connectivity of the concept
    (0/near-0 = the graph never grounded it, so it must fall to the anchor)."""
    return len(_model(agent)["mt_tokens"].get(str(concept)) or {})


# --------------------------------------------------------------------------- #
#  RUNG 1 — the coarse WORLD region (the exponent).
# --------------------------------------------------------------------------- #

def _region_cos(agent, concept: str) -> dict:
    """Neighbourhood cosine of `concept` to each coarse region (max over the region's anchor Mts)."""
    m = _model(agent)
    v = _vec(m, str(concept))
    return {region: max((_cos(v, _vec(m, an)) for an in anchors), default=0.0)
            for region, anchors in _REGION_ANCHORS.items()}


def _region_tokens(m: dict, region: str) -> set:
    """The token vocabulary of a region: the union of its anchor microtheories' has_concept bags."""
    toks: set = set()
    for an in _REGION_ANCHORS.get(region, []):
        toks |= set(m["mt_tokens"].get(an, {}).keys())
    return toks


def _containment(agent, concept: str, region: str) -> float:
    """EDGE-MASS FRACTION (the degree-normalizer): of the concept's OWN tf-idf mass, how much lands on
    tokens the winning region's anchors carry. A ratio of the concept's own mass, so it is degree-free:
    a single-token idiom fully inside literature scores ~1.0 no matter how tiny its cosine is (the
    cosine collapses to 1/‖anchor‖, but the containment does not); a mostly-unmatched concept whose
    lone matching word is a small mass fraction scores low (so a spurious one-sided match is rejected)."""
    m = _model(agent)
    v = _vec(m, str(concept))
    total = sum(v.values())
    if total <= 0.0:
        return 0.0
    toks = _region_tokens(m, region)
    return sum(w for t, w in v.items() if t in toks) / total


def region_confidence(agent, concept: str) -> dict:
    """The degree-normalized RUNG-1 confidence for `concept` (the measure the floor applies to).
    Returns {region, best, other, clarity, containment, grounded, edge}:

      clarity     = best / (best + other)     — the winner's SHARE of region-affinity (degree-free).
      containment = _containment(winner)       — the winner's edge-mass fraction (degree-free).
      grounded    = best >= _CONF_FLOOR (strength) OR containment >= _CONTAIN_FLOOR (containment).
      edge        = best > 0 AND clarity >= _CLARITY_FLOOR AND grounded.

    A rich concept grounds by STRENGTH (unchanged path); a sparse-but-decisive idiom grounds by
    CONTAINMENT; a genuinely ambiguous low-degree concept fails CLARITY and is NOT edge — same low
    degree, opposite verdict, decided by clarity-of-membership rather than by degree."""
    rc = _region_cos(agent, concept)
    modern, univ = rc[REGION_MODERN], rc[REGION_UNIVERSAL]
    best, other = max(modern, univ), min(modern, univ)
    region = REGION_MODERN if modern > univ else REGION_UNIVERSAL
    clarity = best / (best + other) if (best + other) > 0.0 else 0.0
    containment = _containment(agent, concept, region)
    grounded = (best >= _CONF_FLOOR) or (containment >= _CONTAIN_FLOOR)
    edge = (best > 0.0) and (clarity >= _CLARITY_FLOOR) and grounded
    return {"region": region, "best": best, "other": other, "clarity": clarity,
            "containment": containment, "grounded": grounded, "edge": edge}


def world_dimension(agent, concept: str) -> tuple:
    """RUNG 1 (the coarse dimension / exponent): the concept's WORLD region + the source of the call.

    EDGE path — when the degree-normalized `region_confidence` says edge (CLARITY clears `_CLARITY_FLOOR`
    AND the winner is grounded by absolute strength `_CONF_FLOOR` OR by edge-mass CONTAINMENT
    `_CONTAIN_FLOOR`), the region is edge-learned (returns (region, 'edge')). The containment leg is the
    lexical-degree normalization: it rescues a sparse idiom whose cosine is diluted purely by the
    anchor's size, while a genuinely ambiguous low-degree concept (edges split, low clarity) is NOT
    rescued.
    ANCHOR path — otherwise (zero-edge / ambiguous / spurious-tie concept, the connectivity the graph
    falls short on) it defers to the small labelled `_SEED_ANCHOR_MODERN` token check (returns
    (region, 'anchor')).

    Returns (region_label, source) where region_label is REGION_MODERN or REGION_UNIVERSAL and source
    is 'edge' or 'anchor'."""
    conf = region_confidence(agent, concept)
    if conf["edge"]:
        return conf["region"], "edge"
    hit = any(w in _SEED_ANCHOR_MODERN for w in _tok(concept))
    return (REGION_MODERN if hit else REGION_UNIVERSAL), "anchor"


def world_dimension_offline(concept: str) -> str:
    """Agent-less RUNG 1 (no graph to read): the demoted seed-anchor token check ALONE. The honest
    fallback for callers with no substrate — it cannot edge-learn. Used by the agent-less
    `audience_adaptation.concept_is_modern_tech`."""
    return REGION_MODERN if any(w in _SEED_ANCHOR_MODERN for w in _tok(concept)) else REGION_UNIVERSAL


# --------------------------------------------------------------------------- #
#  RUNGS 2..N — the recursive coarse-to-fine descent (self-similar, foveated).
# --------------------------------------------------------------------------- #

def _nearest_anchor(agent, concept: str, region: str) -> Optional[tuple]:
    """RUNG 2: within a region, the nearest region-anchor microtheory (the sub-dimension) + its cos."""
    m = _model(agent)
    v = _vec(m, str(concept))
    scored = [(_cos(v, _vec(m, an)), an) for an in _REGION_ANCHORS.get(region, [])]
    scored.sort(reverse=True)
    return (scored[0][1], scored[0][0]) if scored and scored[0][0] > 0 else None


def descend(agent, concept: str, max_depth: int = 4) -> dict:
    """The N-STEP recursive coarse-to-fine PATH of `concept`, read from its edges. Self-similar rung
    (coarse bin + residual), FOVEATED (stops when the finer rung no longer resolves — depth dynamic):

      rung 1: WORLD region (world_dimension) — the coarse dimension / exponent;
      rung 2: nearest region-ANCHOR microtheory — the sub-dimension;
      rung 3: the concept's own HOME microtheory (its has_concept owner) if distinct from rung 2;
      (deeper rungs stop when edges no longer distinguish — the residual is exhausted.)

    Returns {path: [labels coarse->fine], mantissa: {label: log_closeness}, depth, source}. The
    MANTISSA per rung is the log of (closeness+1) to that rung's centroid — the fine within-region
    log-position (a central concept sits higher than a peripheral one in the same region)."""
    region, source = world_dimension(agent, concept)
    path = [region]
    mant: dict = {}
    rc = _region_cos(agent, concept)
    mant[region] = math.log(rc[region] + 1.0)

    # rung 2 — nearest sub-anchor within the region (only if edge-resolvable beyond eps).
    nb = _nearest_anchor(agent, concept, region)
    if nb is not None and nb[1] >= _DESCEND_EPS and len(path) < max_depth:
        sub, sub_cos = nb
        if sub != str(concept):
            path.append(sub)
            mant[sub] = math.log(sub_cos + 1.0)
            # rung 3 — the concept's own home microtheory, if it is a real distinct edge owner.
            home = home_microtheory(agent, concept)
            if home and home not in path and home != sub and len(path) < max_depth:
                m = _model(agent)
                hc = _cos(_vec(m, str(concept)), _vec(m, home))
                if hc >= _DESCEND_EPS:
                    path.append(home)
                    mant[home] = math.log(hc + 1.0)
    return {"path": path, "mantissa": mant, "depth": len(path), "source": source}


def home_microtheory(agent, concept: str) -> Optional[str]:
    """The microtheory that OWNS `concept` (Mt -has_concept-> this concept), or the microtheory whose
    NAME equals the concept (a domain concept IS a microtheory). Mechanical in-edge read."""
    s = agent.s
    name = str(concept)
    # a domain-name concept: the microtheory itself.
    for nid in s.nodes("Microtheory"):
        if s.node(nid)["attrs"].get("name") == name:
            return name
    # else a member concept: its owning microtheory via the has_concept in-edge.
    for cid in s.nodes("Concept"):
        if s.node(cid)["attrs"].get("name") == name:
            owners = s.in_neighbours(cid, "has_concept")
            if owners:
                return s.node(owners[0])["attrs"].get("name")
            break
    return None


# --------------------------------------------------------------------------- #
#  SHARED-PATH DEPTH — foreignness / liveness = depth of CO-DESCENT.
# --------------------------------------------------------------------------- #

def _common_prefix(a: list, b: list) -> int:
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n


def shared_depth(agent, concept: str, frame_concepts) -> int:
    """The DEPTH OF CO-DESCENT between `concept` and the interlocutor's frame — the MAX over the
    frame's concepts of how deep the two descent paths share a common prefix before forking. 0 = they
    fork at rung 1 (different world region -> foreign); >=1 = they share the coarse region (live); a
    larger depth = they run together further (closer). This IS the relative-to-frame closeness."""
    cp = descend(agent, concept)["path"]
    best = 0
    for f in (frame_concepts or []):
        fp = descend(agent, f)["path"]
        best = max(best, _common_prefix(cp, fp))
    return best


def frame_dimensions(agent, frame_concepts, min_count: int = 1) -> set:
    """The set of RUNG-1 world regions the interlocutor's frame occupies — the dimensions their known
    concepts sit in (each edge-placed by world_dimension). Vane's ethics/virtue concepts -> {universal};
    a developer's python/rust concepts -> {modern_tech, universal}. The frame is DERIVED from edges,
    not a hand table — a novel interlocutor's frame falls out of their own concepts' placements.

    A frame is dimensions with RELATIVE WEIGHTING (the ontology): a dimension enters the frame membrane
    only when the interlocutor's concepts occupy it with WEIGHT >= `min_count`. With `min_count > 1` a
    single outlier (a Victorian who happens to know one modern term) does NOT pull the whole modern
    world into his frame — that lone concept is handled by per-concept grounded-common-ground rescue,
    not by admitting its dimension. `universal` (the timeless world) is always present."""
    counts: dict = {}
    for c in (frame_concepts or []):
        d = world_dimension(agent, c)[0]
        counts[d] = counts.get(d, 0) + 1
    dims = {REGION_UNIVERSAL}     # every frame holds the timeless world
    for d, n in counts.items():
        if n >= min_count:
            dims.add(d)
    return dims


def is_foreign_to_frame(agent, concept: str, frame_concepts) -> bool:
    """Relative foreignness: `concept` is FOREIGN to the interlocutor's frame iff its world region is
    NOT one the frame occupies — equivalently, it co-descends with the frame to depth 0 (forks at rung
    1). Learned from edges + the frame's own concept placements, NOT an absolute modern-tech list."""
    region = world_dimension(agent, concept)[0]
    return region not in frame_dimensions(agent, frame_concepts)


# --------------------------------------------------------------------------- #
#  CONNECTIVITY REPORT — measure sufficiency explicitly (the HARD HONESTY GUARD).
# --------------------------------------------------------------------------- #

def connectivity_report(agent, concepts) -> dict:
    """Per-concept: the has_concept bag size, the edge-placed region + source (edge vs anchor). The
    explicit measurement of where the graph SUSTAINS edge-learning vs where it falls to the anchor."""
    rows = []
    for c in concepts:
        region, source = world_dimension(agent, c)
        rows.append({"concept": str(c), "bag": bag_size(agent, c),
                     "region": region, "source": source})
    edge = [r for r in rows if r["source"] == "edge"]
    anchor = [r for r in rows if r["source"] == "anchor"]
    return {"rows": rows, "n": len(rows), "edge": len(edge), "anchor": len(anchor),
            "edge_fraction": (len(edge) / len(rows)) if rows else 0.0}


__all__ = [
    "REGION_MODERN", "REGION_UNIVERSAL", "world_dimension", "world_dimension_offline",
    "descend", "shared_depth", "frame_dimensions", "is_foreign_to_frame",
    "home_microtheory", "bag_size", "connectivity_report", "region_confidence",
]
