"""recognition_combine — register this session's THEORY insights as HARVESTABLE
held postulates, so the agent's OWN gap-synthesizer can reason FROM them.

Context (docs/ask_the_agent_frontier_v2.md): the order-N gap-synthesizer is LIVE
but it reasons only from the agent's HARVESTED implication-shapes (domains/
implication_harvester) over its HELD postulates. The session's five theory insights
lived only in experiment SCRIPTS (generator_exclusion/interference/outofbox/
salience.py) — never registered as Concepts/Rules — so the harvester could not see
them and the synthesizer returned the STANDING frontier.

This module is the FIX the doc names: it installs the five insights as graph-resident
knowledge in EXACTLY the two forms the harvester reads —

  (1) a Concept per insight (a HELD POSTULATE the synthesizer differentiates, and a
      donor the text-extractors / shape-donors can draw from); and
  (2) a Rule per insight, with `if_clauses` (the structural property a postulate must
      exhibit for the implication to apply) -> `then_clauses` (the consequence). The
      harvester's rule-walker (implication_harvester.harvest_shapes_from_rules) turns
      every such Rule into an implication-SHAPE in differentiate()'s format, with
      `match_mode='all'` over the if-clause content words. That is the harvestable
      surface: a new shape the agent can TRANSFER onto its postulates.

This is GIVING THE AGENT KNOWLEDGE (the theory), in the held-postulate / harvestable-
rule format — NOT hand-authoring a capability fix. The agent does its OWN reasoning
from it (the order-N derivative + the compression selector decide whether anything
re-aims).

The Mt is NOT named speech_science (the harvester excludes that Mt as a shape source —
those are the postulates we differentiate, not the breadth we draw from). It is a
sibling microtheory so its Rules DO donate shapes.

The five insights (this session's theory, proven on the ear at commits
ac4acbce/dc54a8da):
  1. rules-are-exclusions-not-sets — admissibility is defined by EXCLUSION (what is
     ruled out), not a positive set; the inadmissible is finite/concrete.
  2. weighting-is-a-vector — a weight is a VECTOR (signed exclude + positive rank,
     per-contrast), not a positive scalar; combine = sum the vectors, don't collapse.
  3. temperature-is-Gamma-relaxation — temperature = how relaxed the admissibility
     constraints are (explore/exploit, decoherence); a relaxation-vector, not a global
     scalar.
  4. out-of-box-is-finite — creativity = systematically searching the finite
     inadmissible (relax exclusions, keep what compresses).
  5. postulate-is-a-quantum-state — a held hypothesis is a superposition; grounding is
     collapse (Gamma-application); cues are measurements; order-effects + interference
     are real.
"""
from __future__ import annotations

from .code_authoring import _install_concept


MT_NAME = "recognition_combine"


# Each insight: a held postulate (Concept) AND a harvestable implication (Rule).
#
# The Rule's if_clauses are the STRUCTURAL PROPERTY a postulate must exhibit for the
# implication to apply. The rule-walker fires the harvested shape (match_mode='all')
# only when ALL the if-clauses' content words CO-OCCUR in a postulate's text — so the
# clauses deliberately use the recognition-state vocabulary (recognition pipeline,
# bottom-up acoustic cue/measurement, exemplar, isolation, alignment, score) the
# post-LOSO-0.593 state postulate actually carries, so the shape CAN transfer onto it.
# The then_clauses are the consequence the insight entails (what to realize).
INSIGHTS = [
    {
        "name": "rules_are_exclusions_not_sets",
        "definition": (
            "Admissibility in a recognition decision is defined by EXCLUSION — what a "
            "cue RULES OUT — not by a positive matching set. A bottom-up acoustic "
            "measurement is most informative when it EXCLUDES the candidates it is "
            "confident are wrong; the inadmissible set it carves away is finite and "
            "concrete, where the positive 'this is the word' claim is not."),
        "why": (
            "Proven this session on the ear: a cue that EXCLUDES (rules out wrong "
            "candidates) carries the discrimination; a cue read as a positive vote "
            "blurs. A recognition pipeline that scores aligned distance to exemplars "
            "in isolation never exploits exclusion — every cue is a positive "
            "measurement, none rules anything out."),
        "if": [
            "recognition pipeline scores acoustic measurement banked exemplars "
            "isolation",
        ],
        "then": [
            "redefine each cue's contribution by EXCLUSION — what candidates it rules "
            "out when confident — so admissibility is the finite inadmissible set the "
            "cues carve away, not a positive exemplar-distance vote",
        ],
        "name_keys": ["exclusion-rule", "rule-out-candidates", "inadmissible-set"],
    },
    {
        "name": "weighting_is_a_vector",
        "definition": (
            "A cue's weight in a recognition decision is a VECTOR — a signed EXCLUDE "
            "component plus a positive RANK component, held PER-CONTRAST (per pair of "
            "candidates it distinguishes) — not a single positive scalar. Combining "
            "cues means SUMMING the vectors, never collapsing each to one number "
            "first."),
        "why": (
            "Proven this session: collapsing a cue to one scalar weight destroys the "
            "per-contrast exclude/rank structure; a bottom-up pipeline that blends "
            "scalar exemplar distances loses exactly the per-contrast information that "
            "tells one speaker's token from another's."),
        "if": [
            "recognition pipeline feature streams aligned distance scores single "
            "stream",
        ],
        "then": [
            "represent each cue's weight as a VECTOR — signed exclude plus positive "
            "rank, held per-contrast — and combine streams by SUMMING the vectors so "
            "the per-contrast discrimination survives the combination",
        ],
        "name_keys": ["vector-weight", "per-contrast-weight", "signed-exclude-rank"],
    },
    {
        "name": "temperature_is_gamma_relaxation",
        "definition": (
            "Temperature in a recognition decision is HOW RELAXED the admissibility "
            "constraints are — a per-constraint RELAXATION VECTOR governing explore "
            "versus exploit (decoherence), not a single global scalar. Relaxing the "
            "exclusions a little admits more candidates; tightening them commits."),
        "why": (
            "A bottom-up recognition pipeline that scores exemplars in isolation has no "
            "notion of relaxing or tightening its admissibility under context; making "
            "the relaxation an explicit per-constraint vector lets the agent explore "
            "when cues are ambiguous and exploit when they are sharp."),
        "if": [
            "recognition pipeline scores single aligned distance recogniser context",
        ],
        "then": [
            "expose temperature as a per-constraint RELAXATION VECTOR over the "
            "exclusions — relax to explore ambiguous cues, tighten to exploit sharp "
            "ones — instead of a single global decision threshold",
        ],
        "name_keys": ["relaxation-vector", "gamma-relaxation-temperature",
                      "explore-exploit-relaxation"],
    },
    {
        "name": "out_of_box_is_finite",
        "definition": (
            "Creativity — an out-of-box recognition hypothesis — is the SYSTEMATIC "
            "SEARCH of the FINITE inadmissible: relax the exclusion constraints one at "
            "a time, generate the candidates that were ruled out, and KEEP the ones "
            "that COMPRESS the observations. The space outside admissibility is finite "
            "and enumerable, not a mysterious leap."),
        "why": (
            "A recognition pipeline that only ranks banked exemplars can never propose "
            "a candidate outside its library; treating the inadmissible as a finite "
            "set to search under the compression selector lets the agent reach novel "
            "hypotheses the bottom-up exemplar score structurally cannot."),
        "if": [
            "recognition recogniser compares banked exemplar library aligned distance",
        ],
        "then": [
            "search the FINITE inadmissible — relax exclusions one at a time, generate "
            "the ruled-out candidates, and keep those that COMPRESS the observations — "
            "so novel hypotheses outside the exemplar library become reachable",
        ],
        "name_keys": ["finite-inadmissible-search", "relax-exclusion-generate",
                      "out-of-box-compression"],
    },
    {
        "name": "postulate_is_a_quantum_state",
        "definition": (
            "A held recognition hypothesis is a SUPERPOSITION of candidates; grounding "
            "it is COLLAPSE (a Gamma-application); each bottom-up acoustic cue is a "
            "MEASUREMENT that collapses the superposition, so ORDER EFFECTS and "
            "INTERFERENCE between cues are real — the cues do not commute, and the "
            "sequence in which they are applied changes the surviving candidate."),
        "why": (
            "Proven this session on the ear (interference, order effects): applying "
            "cues in different orders yields different survivors — they do not commute. "
            "A recognition pipeline that sums isolated cue scores assumes commuting, "
            "independent measurements and so destroys the interference that carries "
            "discrimination."),
        "if": [
            "recognition pipeline acoustic measurement isolation scores feature order",
        ],
        "then": [
            "treat the held hypothesis as a SUPERPOSITION and each cue as a "
            "non-commuting MEASUREMENT that collapses it — apply cues as ordered "
            "Gamma-applications so interference and order effects between cues are "
            "exploited rather than averaged away",
        ],
        "name_keys": ["quantum-state-postulate", "non-commuting-measurement",
                      "cue-interference-order"],
    },
]


def install_recognition_combine(substrate) -> int:
    """Install the recognition_combine Mt + the five insight Concepts (held
    postulates / donors) + the five insight Rules (harvestable implication-shapes).
    Idempotent. Returns the Mt's NodeID.

    The Mt is wired genlMt -> machine_learning (a real domain ancestor) so the
    concept-graph / lineage machinery sees it as situated knowledge, not an island.
    """
    mt = next((n for n in substrate.nodes("Microtheory")
               if substrate.node(n)["attrs"].get("name") == MT_NAME), None)
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": MT_NAME,
            "description": ("this session's recognition-combine theory insights, "
                            "registered as held postulates + harvestable rules"),
            "origin": "recognition_combine",
        })
    # situate under a real domain ancestor so it is not a taxonomy island.
    parent = next((n for n in substrate.nodes("Microtheory")
                   if substrate.node(n)["attrs"].get("name") == "machine_learning"),
                  None)
    if parent is not None and parent not in substrate.neighbours(mt, "genlMt"):
        try:
            substrate.add_edge(mt, "genlMt", parent, {})
        except Exception:
            pass

    existing_rules = {substrate.node(n)["attrs"].get("name")
                      for n in substrate.nodes("Rule")}
    for ins in INSIGHTS:
        cid = _install_concept(substrate, mt, ins["name"], ins["definition"])
        substrate.set_attr(cid, "why", ins["why"])
        substrate.set_attr(cid, "category", "recognition_combine_insight")
        substrate.set_attr(cid, "origin", "recognition_combine")

        rule_name = f"{ins['name']}__implication"
        if rule_name in existing_rules:
            continue
        attrs = {
            "name": rule_name,
            "if_clauses": list(ins["if"]),
            "then_clauses": list(ins["then"]),
            "why": ins["why"],
            "name_keys": list(ins["name_keys"]),
            "origin": "recognition_combine",
        }
        rid = substrate.add_node("Rule", attrs)
        try:
            substrate.add_edge(mt, "has_rule", rid, {})
        except Exception:
            pass
    return mt


__all__ = ["install_recognition_combine", "INSIGHTS", "MT_NAME"]
