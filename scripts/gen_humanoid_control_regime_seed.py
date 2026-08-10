#!/usr/bin/env python3
"""Generate the humanoid consumer for generic control-regime escalation."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    And,
    Eq,
    Gt,
    L,
    Lt,
    Minus,
    Not,
    Or,
    P0,
    Plus,
    T,
)


def note_absent_evidence_bridge_rule() -> dict:
    """Apply the generic absence contract through the humanoid proxy."""
    return {
        "name": "hcr_bridge_note_regime_evidence_absence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -51,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Lt(P0("regime", "regime_ordinal"), P0("regime", "regime_max_ordinal")),
            Gt(
                Minus(P0("regime", "regime_clock_seq"), P0("regime", "regime_evidence_seq")),
                P0("regime", "regime_evidence_horizon_actions"),
            ),
            Not(Gt(P0("regime", "regime_escalation_requested"), L(0.5))),
        ),
        "effects": [
            ["add_node", "impasse", "ControlRegimeImpasse", {
                "kind": "evidence_absence",
                "at_clock_seq": T(P0("regime", "regime_clock_seq")),
                "from_ordinal": T(P0("regime", "regime_ordinal")),
                "evidence_gap_actions": T(Minus(
                    P0("regime", "regime_clock_seq"),
                    P0("regime", "regime_evidence_seq"),
                )),
                "resolved": 0.0,
            }],
            ["add_edge", "agent", "has_control_regime_impasse", "impasse"],
            ["add_edge", "impasse", "about_control_regime", "regime"],
            ["set_attr", "regime", "regime_escalation_requested", 1.0],
        ],
    }


def escalate_bridge_rule() -> dict:
    return {
        "name": "hcr_bridge_escalate_regime",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -49,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_control_regime", "regime"],
        ],
        "where": And(
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Gt(P0("regime", "regime_escalation_requested"), L(0.5)),
            Lt(P0("regime", "regime_ordinal"), P0("regime", "regime_max_ordinal")),
        ),
        "effects": [
            ["set_attr", "regime", "regime_ordinal", T(
                Plus(P0("regime", "regime_ordinal"), L(1.0))
            )],
            ["set_attr", "regime", "regime_escalation_count", T(
                Plus(P0("regime", "regime_escalation_count"), L(1.0))
            )],
            ["set_attr", "regime", "regime_last_escalation_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_evidence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_escalation_requested", 0.0],
        ],
    }


def note_gait_evidence_rule() -> dict:
    """Support cycles and new progress records are the gait's evidence."""
    return {
        "name": "hcr_note_support_or_progress_regime_evidence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -55,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_control_regime", "regime"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("locomotion")),
            Gt(P0("regime", "regime_monitor_enabled"), L(0.5)),
            Or(
                Gt(
                    P0("episode", "locomotor_cycle_count"),
                    P0("regime", "regime_last_cycle_count"),
                ),
                Gt(
                    P0("episode", "maximum_directed_progress"),
                    P0("regime", "regime_best_progress"),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "regime", "regime_evidence_seq", T(
                P0("regime", "regime_clock_seq")
            )],
            ["set_attr", "regime", "regime_last_cycle_count", T(
                P0("episode", "locomotor_cycle_count")
            )],
            ["set_attr", "regime", "regime_best_progress", T(
                P0("episode", "maximum_directed_progress")
            )],
        ],
    }


def adopt_walking_rung_rule() -> dict:
    """Rung 1: demote the inert high-energy attractor to walking."""
    return {
        "name": "hcr_adopt_walking_after_evidence_absence",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_control_regime", "control"],
            ["episode", "evaluates_humanoid_residual_regime", "old"],
            ["policy", "has_humanoid_residual_regime", "walking"],
        ],
        "where": And(
            Gt(P0("control", "regime_ordinal"), L(0.0)),
            Or(
                Lt(P0("episode", "regime_applied_ordinal"), L(1.0)),
                Not(Eq(
                    P0("episode", "active_gait_attractor_ordinal"),
                    L(0.0),
                )),
                Not(Eq(
                    P0("episode", "active_residual_regime_ordinal"),
                    L(0.0),
                )),
            ),
            Eq(P0("walking", "ordinal"), L(0.0)),
        ),
        "effects": [
            ["del_edge", "episode", "evaluates_humanoid_residual_regime", "old"],
            ["add_edge", "episode", "evaluates_humanoid_residual_regime", "walking"],
            ["set_attr", "episode", "active_gait_attractor_ordinal", 0.0],
            ["set_attr", "episode", "active_residual_regime_ordinal", 0.0],
            ["set_attr", "episode", "residual_regime_window_sample_count", 0.0],
            ["set_attr", "episode", "residual_regime_window_complete", 0.0],
            ["set_attr", "episode", "render_first_suspended", 1.0],
            ["set_attr", "episode", "async_trust_epoch", T(
                P0("control", "regime_clock_seq")
            )],
            ["set_attr", "episode", "regime_applied_ordinal", 1.0],
        ],
    }


def bootstrap_rekick_rung_rule() -> dict:
    """Rung 2: walking itself is inert, so re-open active recovery learning."""
    return {
        "name": "hcr_bootstrap_rekick_after_walking_impasse",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_control_regime", "control"],
        ],
        "where": And(
            Eq(P0("control", "regime_ordinal"), L(2.0)),
            Lt(P0("episode", "regime_applied_ordinal"), L(2.0)),
        ),
        "effects": [
            ["set_attr", "episode", "recovery_mode", 1.0],
            ["set_attr", "episode", "online_phase_learning", 1.0],
            ["set_attr", "episode", "gait_surprise_streak", 0.0],
            ["set_attr", "episode", "locomotor_prior_reset_seq", T(
                Plus(P0("episode", "locomotor_prior_reset_seq"), L(1.0))
            )],
            ["set_attr", "episode", "render_first_suspended", 1.0],
            ["set_attr", "episode", "async_trust_epoch", T(
                P0("control", "regime_clock_seq")
            )],
            ["set_attr", "episode", "regime_applied_ordinal", 2.0],
        ],
    }


def manifest() -> dict:
    return {
        "id": "humanoid_control_regime",
        "version": "1.0.0",
        "depends_on": ["humanoid_adaptation", "control_regime_escalation"],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Humanoid support/progress evidence and gait-rung semantics for generic control-regime escalation.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "humanoid_control_regime:episode_regime",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "has_humanoid_control_regime",
                "tgt": {
                    "type": "EmbodiedMotorProgramEpisode",
                    "var": "regime",
                },
            }
        ],
        "rules": [
            note_absent_evidence_bridge_rule(),
            escalate_bridge_rule(),
            note_gait_evidence_rule(),
            adopt_walking_rung_rule(),
            bootstrap_rekick_rung_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "humanoid_control_regime.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
