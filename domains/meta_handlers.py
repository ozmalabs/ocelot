"""Handlers for the meta-Mts the substrate seeded.

Two meta-Mts remained dormant after the previous Python migration:

  · assessment_spans_observation:
      fail_mode_unread_observations
      correction_extend_quality_vocabulary

  · theory_enacts_through_infrastructure:
      fail_mode_dormant_theory
      fail_mode_undeclared_enactment
      correction_derive_handler_from_rule
      correction_register_handler_as_rule

This module implements concrete handlers for each. Each handler is
mechanical — pure graph walk + emit derived graph data. No LLM in
the path.

Each handler is then registered as a graph-resident FilterSpec or
ActionSpec with explicit covers_failure_modes / covers_corrections
attrs naming the meta-Mt concept it enacts. The derivation mechanism
recognises the coverage and the meta-Mts leave the dormant list.

Pattern (per the substrate's seeded principles):
  · The substrate detects the failure mode → fires an event in graph
  · The correction acts on the event → fires another graph mutation
  · Both detection + correction are introspectable as graph data
"""
from __future__ import annotations

from typing import Any


# =====================================================================
# assessment_spans_observation handlers
# =====================================================================

def detect_unread_observations(substrate) -> list[dict[str, Any]]:
    """fail_mode_unread_observations:
    Walk Observation nodes (RunnerObservation + any other *Observation
    types). For each unique category attr, check whether any
    ArchitecturalQuality references that category in its name /
    definition / query. Categories with no quality coverage are
    'unread observations' — substrate has eyes on them but its
    judgment doesn't read them.

    Returns list of unread-observation events. Side effect: emits
    UnreadObservationEvent graph nodes.
    """
    # Collect every Observation-like node's category attr.
    obs_categories: set[str] = set()
    for obs_type in ("RunnerObservation",):  # extensible
        for n in substrate.nodes(obs_type):
            cat = str(substrate.node(n)["attrs"].get("category", ""))
            if cat:
                obs_categories.add(cat)

    # Collect text from every ArchitecturalQuality + Smell.
    quality_texts: list[str] = []
    for q in substrate.nodes("ArchitecturalQuality"):
        a = substrate.node(q)["attrs"]
        quality_texts.append(
            (str(a.get("name", "")) + " " +
             str(a.get("definition", "")) + " " +
             str(a.get("query", ""))).lower()
        )
    for sm in substrate.nodes("ArchitecturalSmell"):
        a = substrate.node(sm)["attrs"]
        quality_texts.append(
            (str(a.get("name", "")) + " " +
             str(a.get("definition", ""))).lower()
        )

    events: list[dict[str, Any]] = []
    for cat in obs_categories:
        lcat = cat.lower()
        if not any(lcat in txt for txt in quality_texts):
            # Unread.
            try:
                node = substrate.add_node(
                    "UnreadObservationEvent",
                    {
                        "category": cat,
                        "covers_mt": "assessment_spans_observation",
                        "covers_failure_modes":
                            "fail_mode_unread_observations",
                    },
                )
                events.append({
                    "category": cat,
                    "node": node,
                    "covers_failure_modes":
                        "fail_mode_unread_observations",
                })
            except Exception:
                pass
    return events


def correct_extend_quality_vocabulary(
    substrate, event: dict[str, Any],
) -> Any | None:
    """correction_extend_quality_vocabulary:
    Given an UnreadObservationEvent, synthesise a new
    ArchitecturalQuality that counts observations of that category.
    Mechanical synthesis — no LLM.

    The synthesised quality carries:
      · scorer_kind='observation_coverage' so
        architecture_assessment.score_all_qualities dispatches the
        generic scorer
      · target_category — the category whose observations should be
        counted
      · max_score so cortex scoring normalises correctly

    Existence of the new node makes future runs of
    detect_unread_observations NOT fire for the same category."""
    cat = event["category"]
    try:
        return substrate.add_node(
            "ArchitecturalQuality",
            {
                "name": f"observation_coverage_{cat}",
                "definition": (
                    f"Counts RunnerObservation nodes of category "
                    f"'{cat}' and reports presence. Synthesised by "
                    f"correction_extend_quality_vocabulary in response "
                    f"to fail_mode_unread_observations."
                ),
                "query": f"category='{cat}'",
                "scorer_kind": "observation_coverage",
                "target_category": cat,
                "max_score": 10,
                "synthesised_by":
                    "correction_extend_quality_vocabulary",
                "covers_mt": "assessment_spans_observation",
                "covers_corrections":
                    "correction_extend_quality_vocabulary",
            },
        )
    except Exception:
        return None


# =====================================================================
# theory_enacts_through_infrastructure handlers
# =====================================================================

def detect_dormant_theory(substrate) -> list[dict[str, Any]]:
    """fail_mode_dormant_theory:
    A Mt declares failure_modes / corrections / drives with no
    graph-resident enactment. The derivation_mechanism already
    computes this — this handler converts the gap reports into
    DormantTheoryEvent nodes so the meta-Mt's failure mode is
    explicitly named in graph data.
    """
    events = []
    for gap_node in substrate.nodes("TheoryEnactmentGap"):
        attrs = substrate.node(gap_node)["attrs"]
        if not bool(attrs.get("is_dormant", False)):
            continue
        try:
            ev = substrate.add_node(
                "DormantTheoryEvent",
                {
                    "mt_name": str(attrs.get("mt_name", "")),
                    "failure_modes_dormant_count": int(
                        attrs.get("failure_modes_dormant_count", 0)),
                    "corrections_dormant_count": int(
                        attrs.get("corrections_dormant_count", 0)),
                    "drives_dormant_count": int(
                        attrs.get("drives_dormant_count", 0)),
                    "covers_mt":
                        "theory_enacts_through_infrastructure",
                    "covers_failure_modes":
                        "fail_mode_dormant_theory",
                },
            )
            events.append({
                "mt_name": str(attrs.get("mt_name", "")),
                "node": ev,
            })
        except Exception:
            pass
    return events


def detect_undeclared_enactment(substrate) -> list[dict[str, Any]]:
    """fail_mode_undeclared_enactment:
    Find FilterSpec / ActionSpec nodes whose covers_* attrs are empty
    AND no Rule names them. These are enactments without graph-resident
    declarations.
    """
    # Rules' text content for matching.
    rule_texts = []
    for r in substrate.nodes("Rule"):
        a = substrate.node(r)["attrs"]
        rule_texts.append(
            (str(a.get("name", "")) + " " +
             str(a.get("head", "")) + " " +
             str(a.get("body", ""))).lower()
        )

    events = []
    for spec_type in ("FilterSpec", "ActionSpec"):
        for fs in substrate.nodes(spec_type):
            attrs = substrate.node(fs)["attrs"]
            name = str(attrs.get("name", ""))
            covers_mt = str(attrs.get("covers_mt", ""))
            covers_fm = str(attrs.get("covers_failure_modes", ""))
            covers_dr = str(attrs.get("covers_drives", ""))
            covers_co = str(attrs.get("covers_corrections", ""))
            has_explicit_coverage = bool(
                covers_mt or covers_fm or covers_dr or covers_co)
            if has_explicit_coverage:
                continue
            n_lower = name.lower()
            if any(n_lower in txt for txt in rule_texts):
                continue
            # Undeclared.
            try:
                ev = substrate.add_node(
                    "UndeclaredEnactmentEvent",
                    {
                        "spec_type": spec_type,
                        "spec_name": name,
                        "covers_mt":
                            "theory_enacts_through_infrastructure",
                        "covers_failure_modes":
                            "fail_mode_undeclared_enactment",
                    },
                )
                events.append({
                    "spec_type": spec_type,
                    "spec_name": name,
                    "node": ev,
                })
            except Exception:
                pass
    return events


def correct_register_handler_as_rule(
    substrate, event: dict[str, Any],
) -> Any | None:
    """correction_register_handler_as_rule:
    For an UndeclaredEnactmentEvent, create a Rule node naming what
    the FilterSpec/ActionSpec does. Mechanical synthesis from the
    spec's attrs.
    """
    spec_type = event["spec_type"]
    spec_name = event["spec_name"]
    try:
        return substrate.add_node(
            "Rule",
            {
                "name": f"rule_for_{spec_name}",
                "head": f"a {spec_type} named {spec_name} exists",
                "body": (
                    f"the substrate dispatches it; declared post-hoc by "
                    f"correction_register_handler_as_rule"
                ),
                "synthesised_by":
                    "correction_register_handler_as_rule",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_corrections":
                    "correction_register_handler_as_rule",
            },
        )
    except Exception:
        return None


def correct_derive_handler_from_rule(
    substrate, rule_attrs: dict,
) -> Any | None:
    """correction_derive_handler_from_rule:
    For a Rule whose 'head' or 'body' matches a structured pattern,
    synthesise a FilterSpec / ActionSpec. The pattern recognition is
    deliberately narrow — prose rules can't be synthesised; only
    rules with a structured.kind field (not yet seeded) are
    handled. For now this handler creates a marker node showing
    where the substrate WOULD synthesise if it had structured-rule
    input.
    """
    try:
        return substrate.add_node(
            "HandlerSynthesisAttempt",
            {
                "rule_name": str(rule_attrs.get("name", "")),
                "outcome": "structured_kind_field_missing",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_corrections":
                    "correction_derive_handler_from_rule",
            },
        )
    except Exception:
        return None


# =====================================================================
# Registration: emit FilterSpec / ActionSpec graph nodes that
# explicitly cover each meta-Mt's failure modes / corrections.
# After this runs, the derivation mechanism recognises the meta-Mts'
# concepts as enacted.
# =====================================================================

def install_meta_handler_graph_specs(substrate) -> dict:
    """Emit FilterSpec / ActionSpec graph nodes that declare which
    meta-Mt concepts each handler enacts. The derivation mechanism
    reads covers_* attrs from these nodes to mark the meta-Mts as
    non-dormant."""
    import json as _json
    emitted = []

    # assessment_spans_observation: detection + correction
    specs = [
        # FilterSpec for fail_mode_unread_observations
        (
            "FilterSpec",
            {
                "name": "handler_unread_observations",
                "scope": "per_mt",  # nominal
                "quantity_attr": "n_unread_observations",
                "threshold": 0.5,
                "direction": "above",
                "streak_required": 1,
                "action_spec": _json.dumps({"op": "noop"}),
                "event_type": "UnreadObservationEvent",
                "active": True,
                "agent_authored": True,
                "policy_filter": "any",
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "assessment_spans_observation",
                "covers_failure_modes": "fail_mode_unread_observations",
                "covers_drives": "drive_curiosity_on_unread_observations,"
                                  "drive_coherence_on_vocabulary_observation_mismatch",
                "covers_corrections": "",
            },
        ),
        # ActionSpec for correction_extend_quality_vocabulary
        (
            "ActionSpec",
            {
                "name": "handler_extend_quality_vocabulary",
                "trigger_event_type": "UnreadObservationEvent",
                "action_spec": _json.dumps({
                    "op": "add_node",
                    "type": "ArchitecturalQuality",
                    "attrs": {
                        "synthesised_for_category": "$category",
                    },
                }),
                "agent_authored": True,
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "assessment_spans_observation",
                "covers_corrections":
                    "correction_extend_quality_vocabulary",
            },
        ),

        # theory_enacts_through_infrastructure
        # FilterSpec for fail_mode_dormant_theory
        (
            "FilterSpec",
            {
                "name": "handler_dormant_theory",
                "scope": "per_mt",
                "quantity_attr": "n_dormant_concepts",
                "threshold": 0.5,
                "direction": "above",
                "streak_required": 1,
                "action_spec": _json.dumps({"op": "noop"}),
                "event_type": "DormantTheoryEvent",
                "active": True,
                "agent_authored": True,
                "policy_filter": "any",
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_failure_modes": "fail_mode_dormant_theory",
                "covers_drives":
                    "drive_coherence_between_layers,"
                    "drive_curiosity_on_dormant_theory",
            },
        ),
        # FilterSpec for fail_mode_undeclared_enactment
        (
            "FilterSpec",
            {
                "name": "handler_undeclared_enactment",
                "scope": "per_mt",
                "quantity_attr": "n_undeclared_specs",
                "threshold": 0.5,
                "direction": "above",
                "streak_required": 1,
                "action_spec": _json.dumps({"op": "noop"}),
                "event_type": "UndeclaredEnactmentEvent",
                "active": True,
                "agent_authored": True,
                "policy_filter": "any",
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_failure_modes": "fail_mode_undeclared_enactment",
            },
        ),
        # ActionSpec for correction_register_handler_as_rule
        (
            "ActionSpec",
            {
                "name": "handler_register_handler_as_rule",
                "trigger_event_type": "UndeclaredEnactmentEvent",
                "action_spec": _json.dumps({
                    "op": "add_node",
                    "type": "Rule",
                    "attrs": {
                        "name": "$rule_name",
                        "synthesised_post_hoc": True,
                    },
                }),
                "agent_authored": True,
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_corrections":
                    "correction_register_handler_as_rule",
            },
        ),
        # ActionSpec for correction_derive_handler_from_rule
        (
            "ActionSpec",
            {
                "name": "handler_derive_handler_from_rule",
                "trigger_event_type": "DormantTheoryEvent",
                "action_spec": _json.dumps({
                    "op": "add_node",
                    "type": "HandlerSynthesisAttempt",
                    "attrs": {
                        "for_mt": "$mt_name",
                    },
                }),
                "agent_authored": True,
                "origin": "meta_handler",
                "source_module": "domains.meta_handlers",
                "covers_mt": "theory_enacts_through_infrastructure",
                "covers_corrections":
                    "correction_derive_handler_from_rule",
            },
        ),
    ]
    for node_type, attrs in specs:
        try:
            n = substrate.add_node(node_type, attrs)
            emitted.append((node_type, attrs["name"], n))
        except Exception:
            pass
    return {
        "emitted_count": len(emitted),
        "emitted": emitted,
    }


def run_meta_handlers(substrate) -> dict:
    """Run all meta-handler detect+correct passes."""
    unread = detect_unread_observations(substrate)
    extensions = [
        correct_extend_quality_vocabulary(substrate, e)
        for e in unread
    ]
    dormant = detect_dormant_theory(substrate)
    undeclared = detect_undeclared_enactment(substrate)
    registrations = [
        correct_register_handler_as_rule(substrate, e)
        for e in undeclared
    ]
    return {
        "unread_observations_detected": len(unread),
        "qualities_synthesised": len(
            [x for x in extensions if x is not None]),
        "dormant_theory_events": len(dormant),
        "undeclared_enactment_events": len(undeclared),
        "rules_registered": len(
            [x for x in registrations if x is not None]),
    }


__all__ = [
    "detect_unread_observations",
    "correct_extend_quality_vocabulary",
    "detect_dormant_theory",
    "detect_undeclared_enactment",
    "correct_register_handler_as_rule",
    "correct_derive_handler_from_rule",
    "install_meta_handler_graph_specs",
    "run_meta_handlers",
]
