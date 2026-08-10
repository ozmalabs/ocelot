"""The derivation mechanism — turns graph-resident theory into
graph-resident self-awareness of theory/enactment gaps.

Per the substrate's own seeded theory (Mt:
theory_enacts_through_infrastructure, rule
derivation_is_the_missing_capability), the substrate lacks a
mechanism that walks Rules in graph data and connects them to
handlers in the runtime. This module is the first layer of that
mechanism.

What it does:
  1. WALKS THEORY — surveys every Mt's Rules + concepts by category
     (failure_modes, corrections, drives, principles)
  2. WALKS ENACTMENT — surveys graph-resident infrastructure:
     FilterSpec nodes, ActionSpec nodes, ArchitecturalQuality /
     ArchitecturalSmell nodes
  3. COMPUTES GAPS — per Mt, identifies rules with no matching
     graph-resident handler
  4. REPORTS — emits TheoryEnactmentGap nodes the substrate's
     introspection can read

What it does NOT do (yet):
  · Inspect Python-resident handlers (detect_*_signal modules etc.).
    Python handlers are OPAQUE from the substrate's own perspective;
    the substrate can only see graph-resident enactment. The substrate
    being unaware of its own Python handlers is itself a coherence
    gap that this mechanism makes empirical.
  · Synthesise handlers from rules. Requires structured rules with
    a kind/schema the synthesiser can dispatch on. Most current rules
    are prose principles; structured-rule synthesis is the next
    layer.

Per the substrate's meta-meta-rule, this module being introspectable
graph data + a registered handler in the runtime closes one instance
of the theory/enactment gap. The substrate now has the mechanism IT
declared was missing.
"""
from __future__ import annotations

from typing import Any


def walk_theory(substrate) -> dict[str, dict]:
    """Survey every Mt: its Rules + concepts grouped by category.

    Returns: {mt_name: {mt_node, rules, concepts_by_category}}"""
    by_mt: dict[str, dict] = {}
    for mt in substrate.nodes("Microtheory"):
        mt_attrs = substrate.node(mt)["attrs"]
        mt_name = str(mt_attrs.get("name", ""))
        info: dict[str, Any] = {
            "mt_node": mt,
            "rules": [],
            "concepts_by_category": {},
        }
        for r in substrate.neighbours(mt, "has_rule"):
            r_attrs = substrate.node(r)["attrs"]
            info["rules"].append({
                "name": str(r_attrs.get("name", "")),
                "head": str(r_attrs.get("head", "")),
                "body": str(r_attrs.get("body", "")),
                "node": r,
            })
        for c in substrate.neighbours(mt, "has_concept"):
            c_attrs = substrate.node(c)["attrs"]
            cat = str(c_attrs.get("category", ""))
            info["concepts_by_category"].setdefault(cat, []).append({
                "name": str(c_attrs.get("name", "")),
                "definition": str(c_attrs.get("definition", "")),
            })
        by_mt[mt_name] = info
    return by_mt


def walk_enactment(substrate) -> dict[str, list]:
    """Survey graph-resident enactment infrastructure. Python handlers
    are not visible from inside the substrate's own perspective."""
    return {
        "filter_specs": list(substrate.nodes("FilterSpec")),
        "action_specs": list(substrate.nodes("ActionSpec")),
        "qualities": list(substrate.nodes("ArchitecturalQuality")),
        "smells": list(substrate.nodes("ArchitecturalSmell")),
        "runner_observations": list(substrate.nodes("RunnerObservation")),
    }


def compute_gap_per_mt(theory: dict, enactment: dict) -> list[dict]:
    """For each Mt, compute the gap between declared rules + the
    graph-resident enactment that could plausibly cover them.

    Coverage is approximate: a quality referencing a concept whose
    name appears in a rule's head/body indicates the rule is at
    least partially enacted. Absence indicates dormancy."""
    gaps = []

    quality_definitions = []
    for q in enactment["qualities"]:
        attrs = q  # node handle, but we want the attrs
    # Re-fetch with substrate handle context — actually we don't
    # have substrate here. Pass it through.
    # → restructure: take substrate as arg.
    return gaps  # see compute_gap_per_mt_with_substrate below


def compute_gap_per_mt_with_substrate(substrate, theory, enactment):
    """Per-Mt gap computation that has access to substrate for attr
    reads on enactment nodes."""
    quality_texts = []
    for q in enactment["qualities"]:
        a = substrate.node(q)["attrs"]
        quality_texts.append(
            (str(a.get("name", "")) + " " +
             str(a.get("definition", "")) + " " +
             str(a.get("query", ""))).lower()
        )
    smell_texts = []
    for sm in enactment["smells"]:
        a = substrate.node(sm)["attrs"]
        smell_texts.append(
            (str(a.get("name", "")) + " " +
             str(a.get("definition", ""))).lower()
        )
    filter_spec_names = []
    # Per-Mt explicit coverage map: filter_spec's covers_* attrs.
    coverage_by_mt: dict[str, set[str]] = {}
    for fs in enactment["filter_specs"]:
        a = substrate.node(fs)["attrs"]
        filter_spec_names.append(str(a.get("name", "")).lower())
        covers_mt = str(a.get("covers_mt", ""))
        if not covers_mt:
            continue
        all_covers = (
            str(a.get("covers_failure_modes", "")).split(",") +
            str(a.get("covers_drives", "")).split(",") +
            str(a.get("covers_corrections", "")).split(",")
        )
        for cn in all_covers:
            cn = cn.strip()
            if cn:
                coverage_by_mt.setdefault(covers_mt, set()).add(cn)
    action_spec_names = []
    for ac in enactment["action_specs"]:
        a = substrate.node(ac)["attrs"]
        action_spec_names.append(
            str(a.get("trigger_event_type", "")).lower()
        )
        # ActionSpec covers_* attrs → coverage_by_mt. Read both
        # singular and plural forms to tolerate convention drift.
        covers_mt = str(a.get("covers_mt", ""))
        if not covers_mt:
            continue
        all_covers = (
            str(a.get("covers_correction", "")).split(",") +
            str(a.get("covers_corrections", "")).split(",") +
            str(a.get("covers_failure_modes", "")).split(",") +
            str(a.get("covers_drives", "")).split(",")
        )
        for cn in all_covers:
            cn = cn.strip()
            if cn:
                coverage_by_mt.setdefault(covers_mt, set()).add(cn)

    # Category normalisation: the substrate's data uses both singular
    # and plural forms ("failure_mode" + "failure_modes", "drive" +
    # "drives", "operation" + "operations") + has invariants /
    # operations / actions categories that are semantically enactable
    # but were invisible to the original walker. Two-inquiries ask
    # (af3317c) surfaced both: only 1 Mt was visible to the walker;
    # extending the schema surfaces ~5 Mts and the L6 invariants set
    # of 38 concepts that genuinely need checker handlers.
    def _gather(by_cat, *names):
        out = []
        for n in names:
            out.extend(by_cat.get(n, []))
        return out

    gaps = []
    for mt_name, info in theory.items():
        by_cat = info["concepts_by_category"]
        fail_modes = _gather(by_cat, "failure_modes", "failure_mode")
        corrections = _gather(by_cat, "corrections", "correction")
        drives = _gather(by_cat, "drives", "drive")
        principles = _gather(by_cat, "principle", "principles")
        # Extension: invariants need CHECKER handlers (they are
        # claims that must HOLD); operations + actions need ACTION
        # handlers (they are operations that must be EXECUTED).
        # Both are enactable in the same sense as failure_modes
        # + corrections, just with different handler types.
        invariants = _gather(by_cat, "invariants", "invariant")
        operations = _gather(by_cat, "operations", "operation",
                              "actions", "action")
        rules = info["rules"]

        # Coverage check: per concept, is it referenced by any
        # graph-resident enactment (quality, smell, filter, action)?
        # PRIMARY check: explicit covers_* attrs on FilterSpec nodes
        # that name this Mt. Fallback: text mention.
        explicit_coverage_for_mt = coverage_by_mt.get(mt_name, set())

        def is_concept_enacted(name: str) -> bool:
            if name in explicit_coverage_for_mt:
                return True
            n = name.lower()
            for txt in quality_texts + smell_texts:
                if n in txt:
                    return True
            for fname in filter_spec_names + action_spec_names:
                if n in fname or fname in n:
                    return True
            return False

        dormant_fail_modes = [
            c["name"] for c in fail_modes
            if not is_concept_enacted(c["name"])
        ]
        dormant_corrections = [
            c["name"] for c in corrections
            if not is_concept_enacted(c["name"])
        ]
        dormant_drives = [
            c["name"] for c in drives
            if not is_concept_enacted(c["name"])
        ]
        dormant_invariants = [
            c["name"] for c in invariants
            if not is_concept_enacted(c["name"])
        ]
        dormant_operations = [
            c["name"] for c in operations
            if not is_concept_enacted(c["name"])
        ]

        # Dormancy: a category contributes to dormancy when it has
        # declared concepts AND none are enacted. Empty categories
        # don't trigger; this preserves the original semantics.
        def _all_dormant(declared, dormant):
            return len(declared) > 0 and len(dormant) == len(declared)
        is_dormant = (
            _all_dormant(fail_modes, dormant_fail_modes)
            or _all_dormant(corrections, dormant_corrections)
            or _all_dormant(drives, dormant_drives)
            or _all_dormant(invariants, dormant_invariants)
            or _all_dormant(operations, dormant_operations)
        )

        # Vacuous-report filter: if a Mt has nothing in any of these
        # categories AND no rules, the gap report carries no signal.
        # Such Mts (vocabulary-only) are skipped to avoid polluting
        # the graph with empty TheoryEnactmentGap nodes — was 138 per
        # run before this filter.
        has_any_enactable = (
            len(fail_modes) + len(corrections) + len(drives)
            + len(principles) + len(invariants) + len(operations) > 0
        )
        if not has_any_enactable and len(rules) == 0:
            continue

        gaps.append({
            "mt_name": mt_name,
            "mt_node": info["mt_node"],
            "rules_declared": len(rules),
            "failure_modes_declared": len(fail_modes),
            "failure_modes_dormant": dormant_fail_modes,
            "corrections_declared": len(corrections),
            "corrections_dormant": dormant_corrections,
            "drives_declared": len(drives),
            "drives_dormant": dormant_drives,
            "principles_declared": len(principles),
            "invariants_declared": len(invariants),
            "invariants_dormant": dormant_invariants,
            "operations_declared": len(operations),
            "operations_dormant": dormant_operations,
            "is_dormant": is_dormant,
        })
    return gaps


def report_gap_as_graph(substrate, gap) -> Any | None:
    """Create a TheoryEnactmentGap node. Linked from the Mt this
    gap is about via has_gap_report edge."""
    attrs = {
        "mt_name": str(gap["mt_name"]),
        "rules_declared": int(gap["rules_declared"]),
        "failure_modes_declared": int(gap["failure_modes_declared"]),
        "failure_modes_dormant_count": len(gap["failure_modes_dormant"]),
        "corrections_declared": int(gap["corrections_declared"]),
        "corrections_dormant_count": len(gap["corrections_dormant"]),
        "drives_declared": int(gap["drives_declared"]),
        "drives_dormant_count": len(gap["drives_dormant"]),
        "principles_declared": int(gap["principles_declared"]),
        "invariants_declared": int(gap.get("invariants_declared", 0)),
        "invariants_dormant_count": len(gap.get("invariants_dormant", [])),
        "operations_declared": int(gap.get("operations_declared", 0)),
        "operations_dormant_count": len(gap.get("operations_dormant", [])),
        "is_dormant": bool(gap["is_dormant"]),
        "failure_modes_dormant_names":
            ",".join(gap["failure_modes_dormant"]),
        "corrections_dormant_names":
            ",".join(gap["corrections_dormant"]),
        "drives_dormant_names":
            ",".join(gap["drives_dormant"]),
        "invariants_dormant_names":
            ",".join(gap.get("invariants_dormant", [])),
        "operations_dormant_names":
            ",".join(gap.get("operations_dormant", [])),
    }
    try:
        gap_node = substrate.add_node("TheoryEnactmentGap", attrs)
    except Exception:
        return None
    try:
        substrate.add_edge(gap["mt_node"], "has_gap_report",
                           gap_node, {})
    except Exception:
        pass
    return gap_node


def run_derivation(substrate) -> dict:
    """Main entry: walk theory + enactment + compute gaps + report.

    Returns summary: {n_mts_walked, n_rules_total, n_dormant_mts,
                       n_gap_reports_created}"""
    theory = walk_theory(substrate)
    enactment = walk_enactment(substrate)
    gaps = compute_gap_per_mt_with_substrate(substrate, theory, enactment)

    reports_created = 0
    for gap in gaps:
        node = report_gap_as_graph(substrate, gap)
        if node is not None:
            reports_created += 1

    return {
        "n_mts_walked": len(theory),
        "n_rules_total": sum(len(t["rules"]) for t in theory.values()),
        "n_filter_specs": len(enactment["filter_specs"]),
        "n_action_specs": len(enactment["action_specs"]),
        "n_qualities": len(enactment["qualities"]),
        "n_smells": len(enactment["smells"]),
        "n_dormant_mts": sum(1 for g in gaps if g["is_dormant"]),
        "n_gap_reports_created": reports_created,
        "gaps": gaps,
    }


def list_gap_reports(substrate) -> list[dict]:
    """Walk TheoryEnactmentGap nodes; return summaries."""
    out = []
    for n in substrate.nodes("TheoryEnactmentGap"):
        attrs = substrate.node(n)["attrs"]
        nid = n.value if hasattr(n, "value") else int(n)
        out.append({
            "node_id": nid,
            "mt_name": str(attrs.get("mt_name", "")),
            "rules_declared": int(attrs.get("rules_declared", 0)),
            "is_dormant": bool(attrs.get("is_dormant", False)),
            "failure_modes_dormant_count": int(
                attrs.get("failure_modes_dormant_count", 0)),
            "corrections_dormant_count": int(
                attrs.get("corrections_dormant_count", 0)),
            "drives_dormant_count": int(
                attrs.get("drives_dormant_count", 0)),
        })
    return out


__all__ = [
    "walk_theory",
    "walk_enactment",
    "compute_gap_per_mt_with_substrate",
    "report_gap_as_graph",
    "run_derivation",
    "list_gap_reports",
]
