"""Architectural assessment — the meta layer above design.

Coding asks "implement this spec."  Design asks "what spec should I
ask for?"  Architecture asks "is the *shape* of the system the right
shape?" — does it partition responsibilities sensibly, does it layer
abstractions cleanly, does it expose its own reasoning, is the data
graph-resident or hiding in Python?

This module is the loader: pull `seeds/architecture_assessment.json`,
mint `ArchitecturalQuality` + `ArchitecturalSmell` graph nodes. The
scoring is done by an `ArchitectureCortex` (next module) which runs
graph queries on a subject subgraph and writes the answers back as
`Assessment` + `QualityScore` + `SmellInstance` graph nodes.

The data IS the answer. Adding a new quality = editing the JSON;
the cortex picks it up next install.
"""
from __future__ import annotations

import json
from pathlib import Path


_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "architecture_assessment.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def install_architecture_mt(substrate) -> int:
    """Install the `architecture_assessment` Microtheory +
    ArchitecturalQuality nodes + ArchitecturalSmell nodes from the
    seed. Idempotent. Returns the Mt's NodeID.

    Mt inherits via genlMt → `design_patterns` AND →
    `compiler_theory` so the agent's whole stacked vocabulary is in
    scope when assessment reasoning fires."""
    seed = _load_seed()

    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "architecture_assessment":
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "architecture_assessment",
            "description": seed.get("description", ""),
        })
        # The architecture layer reasons over code-authoring structures
        # (and over design patterns and compiler theory). Wire genlMt
        # to all three so the inheritance chain is honest — code_authoring
        # was previously a leaf (compositional_reuse = 0/10); now an
        # architectural assessment of a code-writing cortex inherits
        # code-authoring vocabulary directly.
        for parent_name in ("design_patterns", "compiler_theory",
                            "code_authoring"):
            for mt2 in substrate.nodes("Microtheory"):
                if substrate.node(mt2)["attrs"].get("name") == parent_name:
                    try:
                        substrate.add_edge(mt, "genlMt", mt2, {})
                    except Exception:
                        pass
                    break

    for q in seed.get("qualities", []):
        existing = None
        for n in substrate.nodes("ArchitecturalQuality"):
            if substrate.node(n)["attrs"].get("name") == q["name"]:
                existing = n
                break
        if existing is not None:
            continue
        substrate.add_node("ArchitecturalQuality", {
            **q,
            "origin": "architecture_assessment",
        })

    for sm in seed.get("smells", []):
        existing = None
        for n in substrate.nodes("ArchitecturalSmell"):
            if substrate.node(n)["attrs"].get("name") == sm["name"]:
                existing = n
                break
        if existing is not None:
            continue
        substrate.add_node("ArchitecturalSmell", {
            **sm,
            "origin": "architecture_assessment",
        })

    # data_drivenness scorer config: seed-driven origin whitelist +
    # cortex-constructed-prefix list. Putting this in the seed (graph
    # data) instead of a Python tuple means adding a new seed or cortex
    # construction family doesn't require a code change — the user just
    # updates architecture_assessment.json.
    dd_config = seed.get("data_drivenness_config")
    if dd_config is not None:
        already = False
        for n in substrate.nodes("DataDrivennessConfig"):
            already = True
            break
        if not already:
            substrate.add_node("DataDrivennessConfig", {
                **dd_config,
                "origin": "architecture_assessment",
            })

    return mt


# ---------------------------------------------------------------------------
# Quality scorers + smell detectors. These are graph queries — each
# reads structural features of a SUBJECT subgraph (a Cortex or
# similar) and returns a value. The agent's reasoning about its own
# shape is exactly these queries.
# ---------------------------------------------------------------------------

def subject_microtheories(substrate, subject_nid: int) -> list[int]:
    """All Microtheories the subject's reasoning depends on or IS.

    Returns:
      · If subject_nid is a CORTEX node (or any node owning Mts via
        `owns_microtheory`), returns those owned Mts.
      · If subject_nid IS a Microtheory itself, includes it in the
        result. The cortex's three structural measures
        (compositional_reuse, abstraction_layering, introspectability)
        all expect to see Mts the subject reasons through; when the
        subject IS a Mt, it IS one of those Mts.

    Prior version returned only `owns_microtheory` neighbours, which
    caused every Mt assessed directly (rather than via a cortex
    owner) to score 0 on compositional_reuse and abstraction_layering
    because the iteration was over an empty list. Fix surfaced by
    the inheritance-walk + two-inquiries asks (commits bc40f19,
    af3317c): L6's compositional_reuse stayed 0/10 after
    function_shape's genlMt attachment because L6 owns no sub-Mts
    and the measure couldn't see direct inheritance to L6 itself.
    """
    out = []
    try:
        if substrate.node(subject_nid).get("type") == "Microtheory":
            out.append(subject_nid)
    except Exception:
        pass
    for mt in substrate.neighbours(subject_nid, "owns_microtheory"):
        if mt not in out:
            out.append(mt)
    return out


def subject_reflexes(substrate, subject_nid: int) -> list[int]:
    return list(substrate.neighbours(subject_nid, "has_reflex"))


def _subject_concept_attrs(substrate, subject_nid: int) -> list[dict]:
    """Collect the `attrs` dicts of every Concept owned (via has_concept)
    by any of the subject's Mts. Pools across multiple Mts so a cortex
    that owns several Mts gets a single union. Used by the three
    redesigned per-Mt scorers below."""
    out: list[dict] = []
    for mt in subject_microtheories(substrate, subject_nid):
        for c in substrate.neighbours(mt, "has_concept"):
            try:
                out.append(substrate.node(c)["attrs"])
            except Exception:
                continue
    return out


def score_separation_of_concerns(substrate, subject_nid: int) -> tuple[int, str]:
    """Diversity of the Mt's concept categories.

    Reads the `category` attr off every Concept owned (via has_concept)
    by the subject's Mts. A Mt with 50 concepts spread across 10
    categories has strong separation of concerns (sub-topics are
    explicit graph data); a Mt with 50 concepts all in one category
    (or none) is a flat bag — poor separation.

    Replaces the previous reflex-priority-variance signal which sat
    at 5 for every Mt because Mts have no reflexes (reflexes hang off
    cortices, not Mts). Aligns with the deeper-survey finding that
    'flat Mts' are the structural anti-pattern.

    Formula: `min(10, n_distinct_categories * 2)`.
    """
    attrs_list = _subject_concept_attrs(substrate, subject_nid)
    if not attrs_list:
        # Fall back to the prior reflex-based signal for cortex-shaped
        # subjects with no owned Mts / concepts.
        reflexes = subject_reflexes(substrate, subject_nid)
        if not reflexes:
            return 5, "no concepts and no reflexes — neutral score"
        # Reflex concerns-size variance (legacy path).
        sizes = []
        using_concerns = False
        for r in reflexes:
            c = substrate.node(r)["attrs"].get("concerns")
            if isinstance(c, (list, tuple)) and len(c) > 0:
                using_concerns = True
                sizes.append(len(c))
            else:
                sizes.append(0)
        if not using_concerns:
            sizes = [int(substrate.node(r)["attrs"].get("priority", 0))
                     for r in reflexes]
        if len(sizes) < 2:
            return 7, "one reflex; trivially well-separated"
        mean = sum(sizes) / len(sizes)
        var = sum((c - mean) ** 2 for c in sizes) / len(sizes)
        score = max(0, min(10, int(round(10 - var))))
        metric = "concerns-size" if using_concerns else "priority"
        return score, (
            f"{len(reflexes)} reflexes, {metric}-variance={var:.2f} → "
            f"score {score}")
    cats: set[str] = set()
    for a in attrs_list:
        cat = a.get("category")
        if isinstance(cat, str) and cat:
            cats.add(cat)
    score = min(10, len(cats) * 2)
    return score, (
        f"{len(attrs_list)} concepts span {len(cats)} distinct "
        f"categories → score {score}")


def score_abstraction_layering(substrate, subject_nid: int) -> tuple[int, str]:
    """Longest genlMt chain depth among the subject's Mts."""
    mts = subject_microtheories(substrate, subject_nid)
    if not mts:
        return 0, "subject owns no Microtheories"

    def depth(mt_nid: int, seen: set[int]) -> int:
        if mt_nid in seen:
            return 0  # break cycles
        seen = seen | {mt_nid}
        parents = substrate.neighbours(mt_nid, "genlMt")
        if not parents:
            return 1
        return 1 + max(depth(p, seen) for p in parents)

    d = max(depth(m, set()) for m in mts)
    # 1 = flat, 2-3 = modest, 4+ = well-layered.
    score = max(0, min(10, d * 3 - 1))
    return score, (
        f"deepest genlMt chain depth = {d} → score {score}")


def score_introspectability(substrate, subject_nid: int) -> tuple[int, str]:
    """Fraction of the subject's concepts whose definitions are
    structurally introspectable (i.e. have a registered Term-tree),
    not just opaque definition strings.

    A concept the substrate can read STRUCTURALLY — via a Term-tree
    in the ConceptResolver bridge registries
    (`PROMOTED_CONCEPTS` from concept_promotion_rules + the equation
    walker's promotions, and `GROUNDED_CONCEPTS` from concept_grounding
    where symbols are mapped onto sibling concepts) — is one the
    substrate can REASON about (decompose, traverse, type-check). A
    concept that's only an English definition string is opaque.

    Replaces the previous 'reachable reasoning nodes / reflexes'
    signal that sat at 10 for every Mt because the global vocabulary
    counts dominated and the per-Mt term coverage was invisible.

    Formula: `round((n_concepts_with_term / n_concepts) * 10)`.

    Falls back to neutral 5 if either (a) the bridge registries can't
    be imported (e.g. tests run a stripped substrate) or (b) the
    subject owns zero concepts."""
    attrs_list = _subject_concept_attrs(substrate, subject_nid)
    if not attrs_list:
        return 5, "subject owns no concepts — neutral score"
    # Lazy / guarded import: the bridge modules live alongside this one
    # and are imported during normal seed install, but tests can run
    # with a fresh substrate that hasn't imported them.
    term_names: set[str] = set()
    try:
        from domains.concept_promotion_rules import PROMOTED_CONCEPTS
        for nm, _ in PROMOTED_CONCEPTS:
            term_names.add(nm)
    except Exception:
        pass
    try:
        from domains.concept_grounding import GROUNDED_CONCEPTS
        for nm, _ in GROUNDED_CONCEPTS:
            term_names.add(nm)
    except Exception:
        pass
    # Also count concepts that carry an inline `term` attr from the
    # seed loader (some seeds embed the Term-tree directly).
    n = len(attrs_list)
    n_with_term = 0
    for a in attrs_list:
        nm = a.get("name")
        if isinstance(nm, str) and nm in term_names:
            n_with_term += 1
            continue
        if isinstance(a.get("term"), dict):
            n_with_term += 1
    if not term_names and n_with_term == 0:
        # Registries unavailable AND no inline terms: we genuinely
        # can't tell — neutral.
        return 5, (
            f"{n} concepts; Term-tree registries unavailable — "
            f"neutral score")
    ratio = n_with_term / n
    score = max(0, min(10, int(round(ratio * 10))))
    return score, (
        f"{n_with_term}/{n} concepts have registered Term-trees "
        f"({ratio*100:.0f}%) → score {score}")


def score_data_drivenness(substrate, subject_nid: int) -> tuple[int, str]:
    """Fraction of the subject's concepts that carry a non-empty
    `category` attr.

    Categorised concepts are partitioned by GRAPH DATA — the Mt's
    own taxonomy is readable as edges/attrs the substrate can query
    — while uncategorised concepts read as an unstructured bag
    backed by whatever Python sorted them. This makes per-Mt
    'data-drivenness' a property of how richly the Mt's own concept
    set is graph-structured, which is the spirit of the axis.

    Replaces the previous origin-whitelist count, which was a
    SUBSTRATE-WIDE constant (every Mt scored against the same global
    count → sat at 8 for every Mt). Cross-Mt variance is now visible:
    seeds that categorise (engineering, mathematics, vision_foundation,
    art_design_drawing) score high; flat seeds (conversation,
    chess move lists, etc.) score low — exactly the discrimination
    the cortex needs.

    Chose categorisation over Rule-density because the deeper survey
    shows 1170 Rules across 5519 Concepts: most Mts have zero Rules,
    which would collapse the new signal to 0 just as the old one
    collapsed to 8.

    Formula: `round((n_categorised / n_concepts) * 10)`.
    """
    attrs_list = _subject_concept_attrs(substrate, subject_nid)
    if not attrs_list:
        return 5, "subject owns no concepts — neutral score"
    n = len(attrs_list)
    n_categorised = 0
    for a in attrs_list:
        cat = a.get("category")
        if isinstance(cat, str) and cat:
            n_categorised += 1
    ratio = n_categorised / n
    score = max(0, min(10, int(round(ratio * 10))))
    return score, (
        f"{n_categorised}/{n} concepts carry a category attr "
        f"({ratio*100:.0f}%) → score {score}")


def score_compositional_reuse(substrate, subject_nid: int) -> tuple[int, str]:
    """Are the subject's Mts/Concepts referenced by OTHER subjects?
    For Mt nodes, count incoming genlMt edges PLUS incoming depends_on
    edges on the Mt's Concepts (grounding-aware — per jabberwock's
    change 1, grounded equations emit depends_on edges from their
    Concept node to each referenced concept's Concept node)."""
    mts = subject_microtheories(substrate, subject_nid)
    inbound_mt = 0
    inbound_concept = 0
    for mt in mts:
        for nid in substrate.in_neighbours(mt, "genlMt"):
            inbound_mt += 1
        # Concept-level structural references — each grounded equation
        # that depends on one of this Mt's concepts counts here.
        for c in substrate.neighbours(mt, "has_concept"):
            for nid in substrate.in_neighbours(c, "depends_on"):
                inbound_concept += 1
    # Weight Mt-genlMt 3x, Concept-depends_on 1x (genlMt is more
    # architecturally significant; depends_on is finer-grained).
    weighted = inbound_mt * 3 + inbound_concept
    score = max(0, min(10, weighted // 3))
    return score, (
        f"genlMt incoming = {inbound_mt}, "
        f"depends_on incoming = {inbound_concept}, "
        f"weighted = {weighted} → score {score}")


_QUALITY_SCORERS = {
    "separation_of_concerns": score_separation_of_concerns,
    "abstraction_layering": score_abstraction_layering,
    "introspectability": score_introspectability,
    "data_drivenness": score_data_drivenness,
    "compositional_reuse": score_compositional_reuse,
}


# --- Generic scorers for SYNTHESISED qualities ---------------------------
# These are dispatched on the quality's `scorer_kind` attr rather than its
# `name`, so any quality the substrate synthesises (e.g. via
# correct_extend_quality_vocabulary) can declare what kind of computation
# scores it. The scorer reads the quality's own attrs to drive the
# computation; the substrate's runtime now executes graph-resident
# scoring intent directly.

def _score_observation_coverage(substrate, subject_nid, q_attrs):
    """Count observations whose category attr matches the quality's
    target_category attr. Score 10 if any observation is present (the
    category is now read by at least this quality); 0 if none."""
    target = str(q_attrs.get("target_category", ""))
    if not target:
        # Fall back to parsing from name suffix: 'observation_coverage_<cat>'.
        name = str(q_attrs.get("name", ""))
        if name.startswith("observation_coverage_"):
            target = name[len("observation_coverage_"):]
    if not target:
        return 0, "no target_category attr; cannot score"
    n = 0
    for obs_type in ("RunnerObservation",):
        for obs in substrate.nodes(obs_type):
            if str(substrate.node(obs)["attrs"].get(
                    "category", "")) == target:
                n += 1
    if n == 0:
        return 0, f"no observations of category '{target}' present"
    return 10, (
        f"{n} observations of category '{target}' are read by this "
        f"synthesised quality")


_SYNTHESISED_SCORERS = {
    "observation_coverage": _score_observation_coverage,
}


def score_all_qualities(substrate, subject_nid: int) -> list[dict]:
    """Run every installed quality's scorer; return one dict per
    quality. Walks every ArchitecturalQuality node — including
    synthesised ones — and dispatches:

      · if quality's name matches a hand-coded scorer in
        _QUALITY_SCORERS, run that
      · else if quality has a scorer_kind attr matching
        _SYNTHESISED_SCORERS, run that
      · else skip

    This lets correct_extend_quality_vocabulary's synthesised
    qualities participate in the cortex's score pass automatically:
    they carry scorer_kind="observation_coverage" + the
    target_category attr, and this function dispatches accordingly.
    """
    out = []
    for q_nid in substrate.nodes("ArchitecturalQuality"):
        attrs = substrate.node(q_nid)["attrs"]
        name = str(attrs.get("name", ""))
        scorer_kind = str(attrs.get("scorer_kind", ""))

        scorer = _QUALITY_SCORERS.get(name)
        if scorer is not None:
            score, rationale = scorer(substrate, subject_nid)
        elif scorer_kind and scorer_kind in _SYNTHESISED_SCORERS:
            score, rationale = _SYNTHESISED_SCORERS[scorer_kind](
                substrate, subject_nid, attrs)
        else:
            # Quality has no scorer assignable; skip.
            continue
        out.append({
            "quality_name": name,
            "quality_nid": q_nid,
            "score": int(score),
            "max_score": int(attrs.get("max_score", 10)),
            "rationale": rationale,
        })
    return out


# ---------------------------------------------------------------------------
# Smell detectors — pattern matches against structural shapes.
# ---------------------------------------------------------------------------

# Γ-admissibility bookkeeping node types (`runners/dsl/src/grammar_reflect.rs`
# + the Term-tree reflection machinery `where`/`weight` route through). These
# are graph-machinery/administrative nodes, never emitters of the `common`
# structural vocabulary below, and their POPULATION SIZE is an artefact of how
# many productions/rules happen to have been declared — not a signal about
# any agent-facing node's structural role. Same exclusion convention this
# codebase already uses for `Term.*` (see `substrate/world_adapter.py`, e.g.
# "Term.* are graph machinery, never instanced (no id)"), extended to the Γ
# mirror node types so an outlier detector's population isn't corrupted by
# however many productions happen to be mirrored (see
# GAMMA_LOAD_GROWTH_FIX_RESULTS.md §2 for the measured regression this fixes).
_GAMMA_MIRROR_TYPES = ("GammaGrammar", "GammaProduction", "GammaNodePattern")


def _is_graph_machinery_type(t: str) -> bool:
    return t in _GAMMA_MIRROR_TYPES or (t is not None and t.startswith("Term."))


def detect_god_object(substrate, subject_nid: int, spec: dict) -> list[dict]:
    """Flag a node whose outgoing edge-type DIVERSITY is a positive OUTLIER in
    the DISTRIBUTION of that diversity across the whole graph — not a node that
    crosses an absolute count. "Too many edge types" is meaningless in the
    abstract: 8 is unremarkable in a densely-typed graph and alarming in a
    sparse one. The relative test is position on the distribution's axis: a
    node is a god-object when its diversity exceeds mean + k*std (default
    k=2.0), so the same count is flagged in one graph and not in another
    depending on how its peers are shaped."""
    # Diversity proxy: how many of the common structural edge types a node
    # emits (no Rust primitive enumerates a node's out-edge-types, so this
    # fixed vocabulary is the diversity feature — same one the absolute
    # version used, now read RELATIVELY).
    common = ("has_reflex", "owns_microtheory", "owns_root",
              "uses_pattern", "authored_in", "current_target",
              "has_draft", "validated_by", "installed_as",
              "genlMt", "lexicon")

    def diversity(n) -> int:
        return sum(1 for et in common if substrate.neighbours(n, et))

    # The graph's own distribution of edge-type diversity — excluding Γ
    # mirror / Term.* graph-machinery nodes, which are never structural
    # participants in this vocabulary and would otherwise dilute the
    # population with zero-diversity administrative bookkeeping.
    all_nodes = [n for n in substrate.nodes()
                 if not _is_graph_machinery_type(substrate.node(n)["type"])]
    if not all_nodes:
        return []
    divs = [diversity(n) for n in all_nodes]
    mean = sum(divs) / len(divs)
    std = (sum((d - mean) ** 2 for d in divs) / len(divs)) ** 0.5
    k = float(spec.get("outlier_k", 2.0))
    cutoff = mean + k * std

    found = []
    seen: set = set()
    candidates = [subject_nid] + subject_reflexes(substrate, subject_nid)
    candidates += subject_microtheories(substrate, subject_nid)
    for n in candidates:
        if n in seen:
            continue
        seen.add(n)
        count = diversity(n)
        # std == 0 → a uniform graph has no outliers; flag nothing.
        if std > 0 and count > cutoff:
            found.append({
                "smell_name": "god_object",
                "location": f"node #{n}",
                "rationale": (
                    f"node has {count} distinct outgoing edge types — a "
                    f"positive outlier in the graph's distribution "
                    f"(mean {mean:.2f}, sd {std:.2f}, cutoff {cutoff:.2f} "
                    f"at k={k})"),
            })
    return found


def detect_circular_inheritance(substrate, subject_nid: int,
                                spec: dict) -> list[dict]:
    """DFS over genlMt; a chain forms a CYCLE only when the same Mt
    is reached AGAIN ALONG THE CURRENT PATH. Multiple paths to a
    shared ancestor (diamond inheritance like
        gadgets → neural_networks → compiler_theory
        gadgets → compiler_theory
    ) are NOT cycles — they're the expected shape when a child
    inherits from a chain and the chain's base directly."""
    found = []
    mts = subject_microtheories(substrate, subject_nid)
    reported: set[tuple[int, int]] = set()

    def _walk(node: int, path: frozenset[int], root: int) -> None:
        for nxt in substrate.neighbours(node, "genlMt"):
            if nxt in path:
                key = (root, nxt)
                if key not in reported:
                    reported.add(key)
                    found.append({
                        "smell_name": "circular_inheritance",
                        "location": (
                            f"genlMt cycle including "
                            f"Mt #{nxt} reachable from #{root}"),
                        "rationale": (
                            f"genlMt path from Mt #{root} returns to "
                            f"Mt #{nxt}"),
                    })
                continue
            _walk(nxt, path | {nxt}, root)

    for mt in mts:
        _walk(mt, frozenset({mt}), mt)
    return found


def detect_orphaned_concept(substrate, subject_nid: int,
                            spec: dict) -> list[dict]:
    """Find Concept nodes with zero incoming edges of any kind."""
    found = []
    for c in substrate.nodes("Concept"):
        # Probe common inbound types. GROUNDING edges (built_from /
        # depends_on / grounds / genls — opened by
        # grounded_representation.open_grounding_productions) count as
        # incoming references: a concept another concept is built_from, or
        # that grounds another, is composed-into, not orphaned. This is the
        # whole point of the grounded-representation foundation — a
        # compositional concept graph has FEWER islands.
        inbound = 0
        for et in ("has_concept", "in_category", "instantiates",
                   "subClassOf", "built_from", "depends_on", "grounds",
                   "genls"):
            inbound += len(substrate.in_neighbours(c, et))
        if inbound == 0:
            nm = substrate.node(c)["attrs"].get("name", "")
            found.append({
                "smell_name": "orphaned_concept",
                "location": f"Concept #{c} ('{nm}')",
                "rationale": "no incoming references from Mt/Rule/category",
            })
    return found


_SMELL_DETECTORS = {
    "god_object": detect_god_object,
    "circular_inheritance": detect_circular_inheritance,
    "orphaned_concept": detect_orphaned_concept,
}


def detect_all_smells(substrate, subject_nid: int) -> list[dict]:
    """Run every installed smell's detector; return all instances."""
    out = []
    for s_nid in substrate.nodes("ArchitecturalSmell"):
        attrs = substrate.node(s_nid)["attrs"]
        name = attrs["name"]
        detector = _SMELL_DETECTORS.get(name)
        if detector is None:
            continue
        # Pass the smell's whole attrs dict — each detector reads what it
        # needs (an absolute `threshold` for the cycle/orphan detectors, the
        # relative `outlier_k` for god_object).
        for inst in detector(substrate, subject_nid, attrs):
            inst["smell_nid"] = s_nid
            out.append(inst)
    return out


__all__ = [
    "install_architecture_mt",
    "score_all_qualities",
    "detect_all_smells",
]
