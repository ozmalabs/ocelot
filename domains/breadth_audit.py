"""breadth_audit — the agent audits its OWN breadth for MISSING shape-KINDS.

order_n_postulates.synthesize_gaps transfers the implication-SHAPES the agent
HOLDS (domains/implication_harvester.harvest_shapes_*). It is structurally BLIND
to the shapes it LACKS: it can only fire a shape that exists in the library, so a
capability that would need a shape the agent does not hold simply never surfaces —
and nothing in the gap-synthesis pipeline NOTICES the silence. iter-19
(scripts/jabberwock_perceptual_shape.py) hit exactly this: over the perceptual
frame the operator derived only NORMALIZATIONS (cancel-scale, subtract-context,
segment, cluster) and could not derive a "re-represent the object by the relations
among its parts" shape, because no shape of that form is in the library. A human
sub-agent had to read the 181-shape library by hand to find that absence.

This module turns the gap-finder on the TOOLBOX. It examines the agent's OWN
harvested shape-library and surfaces COVERAGE GAPS in it — mechanically, with no
hand-fed answer. It does NOT know "relational" is the missing kind; it discovers
which structural ROLES of operation are present and which are ABSENT, from the
shapes' own text.

THREE mechanisms, all reading the agent's own data:

  (1) ROLE DISTRIBUTION (classify_shape_role / role_distribution).
      Every operation on a representation plays one of a small set of structural
      ROLES — the agent's domain-general grasp of "what an operation DOES to its
      operand". The roles partition along ONE principled axis:
        • SUBSTRATE-PRESERVING — the operation acts ON the existing representation
          and yields the SAME kind of representation, cleaned / regrouped:
            - cancel        (remove a multiplicative/additive nuisance factor)
            - separate      (invert a mixing; pull entangled components apart)
            - partition     (cluster / segment the SAME values into groups)
            - parameterize  (compress the SAME values to a few coefficients)
        • SUBSTRATE-CHANGING — the operation REPLACES the representation with a
          DIFFERENT KIND of object:
            - re_represent  (describe the object by the RELATIONS among its parts —
                             a configuration / structure / graph, not its absolute
                             values; an invariant-by-construction representation)
      A shape is classified by matching its consequence + match_keys against each
      role's operation-verb evidence. The taxonomy is the agent's grasp of
      operation-KINDS (the same status the 7 extractor KINDS have in the harvester);
      the COUNTS are read off the agent's actual library. A role with ZERO shapes is
      a breadth gap: the agent holds no implication-shape that plays that role.

  (2) FRAME CONVERGENCE (frame_convergence).
      For a registered FRAME-postulate, run the EXISTING synthesize_gaps and measure
      the DIVERSITY of the structural ROLES the surfaced gaps draw from. If every
      gap a frame surfaces falls in ONE role (or one PRESERVE/CHANGE side), the
      frame is BREADTH-LIMITED: the operator had only one kind of move available, so
      a complementary kind is likely missing. The perceptual frame is the test case.

  (3) DOMAIN COVERAGE (domain_coverage).
      Enumerate the domains the agent holds concepts in vs the domains its harvested
      shapes draw from. Concept-rich domains contributing no shape are latent
      breadth the harvester is missing; domains absent entirely are breadth the
      agent lacks. (Reported for honesty; the role axis is the load-bearing test.)

NO-DONKEY: this module does not contain the answer. It does not test "is the
relational shape present"; it computes a role distribution and reports whichever
roles are empty. That the empty role happens to be the re_represent one is the
audit's OUTPUT, not its input. The role taxonomy is justified structurally (the
preserve/change partition is exhaustive for operations-on-representations), not
fitted to speech.

Agent-residency: the audit reads the agent's own shape-library and own postulates
(world-adapter I/O at the boundary); the classification is a mechanical
structural-role match, the same kind of keyword-level structural recognition the
harvester's extractors already are. See [[ozma_order_n_postulates]] /
[[ozma_synthesizes_own_gaps]] / [[ozma_meta_abilities_are_leverage]].
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# The STRUCTURAL-ROLE taxonomy — the agent's grasp of "what an operation does to
# a representation". Partitioned by the PRESERVE/CHANGE axis (see module docstring).
#
# Each role declares operation-verb EVIDENCE (regexes over a shape's consequence +
# match_keys). A shape plays a role iff its evidence fires. The taxonomy is fixed
# (it is the agent's notion of operation-kinds, like the harvester's extractor
# KINDS); the per-role COUNTS are read off the agent's actual library.
#
# This is NOT "speech" and NOT "relational==the answer": it is a general operation
# taxonomy. The audit reports whichever role(s) come up empty.
# ---------------------------------------------------------------------------

_ROLES = [
    # ---- SUBSTRATE-PRESERVING: operate on the same representation -------------
    {"role": "cancel", "side": "preserve",
     "gloss": "remove a nuisance scale / context factor, same representation cleaned",
     "evidence": [r"\bcancel", r"\bnormalis", r"\bnormaliz", r"\bstandardiz",
                  r"\bsubtract", r"\bremov(?:e|ed|es|ing|al)\b", r"\bratio\b",
                  r"scale-?invariant", r"\bresidual\b", r"\bdetrend",
                  r"context-?free", r"\bbaseline\b"]},
    {"role": "separate", "side": "preserve",
     "gloss": "invert a mixing / pull entangled components apart",
     "evidence": [r"\binvert", r"\binvertible\b", r"deconvolv", r"\bseparat",
                  r"\bdecompos", r"disentangl", r"unmix", r"pseudoinverse"]},
    {"role": "partition", "side": "preserve",
     "gloss": "cluster / segment the same values into groups or boundaries",
     "evidence": [r"\bcluster", r"\bsegment", r"\bboundar", r"\bchunk",
                  r"\bmixture\b", r"\bmodes?\b", r"\bpartition", r"\bgroup\b",
                  r"unsupervised"]},
    {"role": "parameterize", "side": "preserve",
     "gloss": "compress the same values to a few coefficients / a parametric model",
     "evidence": [r"all-?pole", r"autoregress", r"linear[\s-]?predict",
                  r"\bparametric\b", r"\bcoefficients?\b", r"\bpoles?\b",
                  r"few\s+\w+\s+(?:capture|ARE)", r"feedback\s+coefficient"]},
    {"role": "forward_invert", "side": "preserve",
     "gloss": "run a forward model and invert it (analysis-by-synthesis)",
     "evidence": [r"forward\s+model", r"analysis-?by-?synthesis", r"inverse\s+problem",
                  r"internal\s+synthesis", r"synthesis(?:er|or)\b",
                  r"render.*and.*(?:compare|match)", r"simulate.*and.*match"]},
    # ---- SUBSTRATE-CHANGING: replace the representation with a different kind --
    {"role": "re_represent", "side": "change",
     "gloss": "describe the object by the RELATIONS among its parts — a "
              "configuration / structure / graph, an invariant-by-construction "
              "representation, not its absolute values",
     "evidence": [
         # relations AMONG parts / between elements
         r"relation(?:s|ship)?\s+(?:among|between)",
         r"\brelative\s+(?:position|arrangement|configuration)",
         r"\bconfiguration\b", r"\barrangement\b", r"\btopolog",
         # represent the object AS a structure/graph rather than by values
         r"represent(?:ed|ing|s|ation)?\s+(?:as|by)\s+(?:a\s+)?(?:graph|structure|"
         r"shape|relation)",
         r"\bgraph\b.*\b(?:structure|representation)\b",
         r"structural\s+(?:descript|representation|invariant)",
         r"invariant\s+under\s+(?:the\s+)?(?:transform|group|nuisance|deformation)",
         r"transform-?invariant\s+(?:representation|descript)",
         r"\bgestalt\b", r"whole-?(?:unit|pattern)\s+(?:over|representation)",
         # describe by relations/ratios among the parts (not absolute)
         r"relations?\s+among\s+(?:its|the)\s+(?:parts|points|elements|components)",
     ]},
]


def _shape_text(shape: dict) -> str:
    """The text the role-classifier reads off a shape: its consequence + the
    match_keys / name_keys (the operation the shape names). Lowercased."""
    parts = [str(shape.get("consequence", ""))]
    parts += [str(k) for k in shape.get("match_keys", [])]
    parts += [str(k) for k in shape.get("name_keys", [])]
    return " ".join(parts).lower()


def classify_shape_role(shape: dict) -> list[str]:
    """Return the structural ROLE(s) a shape plays (may be several; may be none if
    the shape's operation matches no known role — those are reported as
    'unclassified', themselves a signal). Mechanical regex match, no answer fed."""
    text = _shape_text(shape)
    roles = []
    for r in _ROLES:
        if any(re.search(p, text) for p in r["evidence"]):
            roles.append(r["role"])
    return roles


def role_distribution(shapes: list[dict]) -> dict:
    """Classify every harvested shape by structural ROLE; return the distribution
    plus the EMPTY roles (the breadth gaps). Reads the agent's own library.

    Returns:
      {role_counts, side_counts, empty_roles, empty_sides, unclassified,
       per_role_examples}
    An EMPTY role = a structural-role of operation for which the agent holds NO
    implication-shape: a breadth gap, surfaced mechanically."""
    role_counts = Counter()
    side_counts = Counter()
    per_role_examples = defaultdict(list)
    unclassified = []
    side_of = {r["role"]: r["side"] for r in _ROLES}
    for sh in shapes:
        roles = classify_shape_role(sh)
        if not roles:
            unclassified.append(sh.get("name", "?"))
            continue
        for role in roles:
            role_counts[role] += 1
            side_counts[side_of[role]] += 1
            if len(per_role_examples[role]) < 5:
                per_role_examples[role].append(sh.get("name", "?"))
    empty_roles = [r["role"] for r in _ROLES if role_counts[r["role"]] == 0]
    sides = {r["side"] for r in _ROLES}
    empty_sides = [s for s in sorted(sides) if side_counts[s] == 0]
    return {
        "role_counts": dict(role_counts),
        "side_counts": dict(side_counts),
        "empty_roles": empty_roles,
        "empty_sides": empty_sides,
        "n_unclassified": len(unclassified),
        "unclassified": unclassified[:20],
        "per_role_examples": {k: v for k, v in per_role_examples.items()},
        "roles": {r["role"]: {"side": r["side"], "gloss": r["gloss"]}
                  for r in _ROLES},
    }


def audit_library(substrate, exclude_mt: str = "speech_science") -> dict:
    """Run the role-distribution audit over the agent's OWN harvested shape-library.
    World-adapter boundary: harvest the agent's shapes, then classify mechanically."""
    from .implication_harvester import harvest_shapes_combined
    shapes = harvest_shapes_combined(substrate, exclude_mt=exclude_mt)
    dist = role_distribution(shapes)
    dist["n_shapes"] = len(shapes)
    return dist


# ---------------------------------------------------------------------------
# (2) FRAME CONVERGENCE — does a frame's surfaced gaps converge on one role?
# ---------------------------------------------------------------------------

def _gap_to_shapelike(gap: dict) -> dict:
    """Adapt a synthesize_gaps output into the shape-like dict the role-classifier
    reads (consequence + the capability keys it names)."""
    return {
        "consequence": gap.get("gap", ""),
        "match_keys": gap.get("capability_keys", []),
        "name_keys": gap.get("capability_keys", []),
    }


def frame_convergence(substrate, postulate_name: str, *,
                      shapes="harvested", max_order: int = 3,
                      prune: bool = False) -> dict:
    """Run the EXISTING synthesize_gaps over a frame-postulate and measure the
    structural-ROLE diversity of the gaps it surfaces. A frame whose gaps all fall
    on ONE role (or one PRESERVE/CHANGE side) is BREADTH-LIMITED — the operator had
    only one kind of move, so a complementary kind is likely missing.

    Returns {n_gaps, role_counts, side_counts, n_distinct_roles, n_distinct_sides,
             converges, converges_on_side, sides_present, roles_present}."""
    from .order_n_postulates import synthesize_gaps
    gaps = synthesize_gaps(substrate, postulate_name, shapes=shapes,
                           record=False, prune=prune, max_order=max_order)
    role_counts = Counter()
    side_counts = Counter()
    side_of = {r["role"]: r["side"] for r in _ROLES}
    for g in gaps:
        for role in classify_shape_role(_gap_to_shapelike(g)):
            role_counts[role] += 1
            side_counts[side_of[role]] += 1
    n_roles = len([r for r, c in role_counts.items() if c])
    n_sides = len([s for s, c in side_counts.items() if c])
    return {
        "postulate": postulate_name,
        "n_gaps": len(gaps),
        "role_counts": dict(role_counts),
        "side_counts": dict(side_counts),
        "n_distinct_roles": n_roles,
        "n_distinct_sides": n_sides,
        "roles_present": sorted(r for r, c in role_counts.items() if c),
        "sides_present": sorted(s for s, c in side_counts.items() if c),
        # BREADTH-LIMITED: the frame surfaced gaps but they all share one side of
        # the preserve/change partition (so the complementary side is unreachable
        # with the current library).
        "converges": bool(gaps) and n_sides <= 1,
        "converges_on_side": (sorted(s for s, c in side_counts.items() if c)[0]
                              if n_sides == 1 else None),
    }


# ---------------------------------------------------------------------------
# (3) DOMAIN COVERAGE — concept-domains vs shape-donating domains.
# ---------------------------------------------------------------------------

def domain_coverage(substrate, exclude_mt: str = "speech_science") -> dict:
    """Enumerate the domains the agent holds concepts in vs the domains its
    harvested shapes draw from. Concept domains contributing no shape are latent
    breadth the harvester misses; this is reported for honesty (the role axis is
    the load-bearing test)."""
    from .implication_harvester import (harvest_shapes_combined, _concept_text,
                                         _domain_of)
    shapes = harvest_shapes_combined(substrate, exclude_mt=exclude_mt)
    shape_domains = Counter(s.get("domain", "?") for s in shapes)
    concept_domains = Counter()
    for c in substrate.nodes("Concept"):
        _, body, origin = _concept_text(substrate, c)
        if body:
            concept_domains[_domain_of(origin)] += 1
    un_harvested = sorted(d for d in concept_domains
                          if d not in shape_domains and concept_domains[d] >= 3)
    return {
        "n_concept_domains": len(concept_domains),
        "n_shape_domains": len(shape_domains),
        "concept_domains": dict(concept_domains.most_common()),
        "shape_domains": dict(shape_domains.most_common()),
        "concept_domains_with_no_shape": un_harvested,
    }


# ---------------------------------------------------------------------------
# The full audit — all three mechanisms + an honest verdict line.
# ---------------------------------------------------------------------------

def run_audit(substrate, frames: list[str] | None = None,
              exclude_mt: str = "speech_science") -> dict:
    """The breadth-audit. Runs the role-distribution over the library, the
    frame-convergence over each supplied frame, and the domain-coverage report.
    Returns a dict the world adapter / script renders. No answer is fed in."""
    lib = audit_library(substrate, exclude_mt=exclude_mt)
    conv = {}
    for fr in (frames or []):
        conv[fr] = frame_convergence(substrate, fr)
    dom = domain_coverage(substrate, exclude_mt=exclude_mt)
    return {
        "library_role_distribution": lib,
        "frame_convergence": conv,
        "domain_coverage": dom,
        # the breadth gaps the audit surfaces, mechanically:
        "breadth_gaps": {
            "empty_roles": lib["empty_roles"],
            "empty_sides": lib["empty_sides"],
            "breadth_limited_frames": [f for f, c in conv.items() if c["converges"]],
        },
    }


__all__ = ["classify_shape_role", "role_distribution", "audit_library",
           "frame_convergence", "domain_coverage", "run_audit"]
