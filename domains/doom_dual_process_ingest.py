"""Mechanical Doom boundary for graph-native PSI and dual-process control.

This module copies measured Doom state into typed graph observations, invokes
the native dual-process schedule, and reads/enacts the resulting
``ControlBundle`` intent.  Candidate valuation, affect, drive competition,
System-1 commitment, and System-2 recruitment remain seed rules.
"""
from __future__ import annotations

from substrate.seed_loader import manifest_for


_DRIVE_DEFAULTS = {
    "v_d": 0.0, "c_d": 0.0, "c_d_prev": 0.0, "v_0": 0.0,
    "weight": 1.0, "decay": 0.0, "gain": 1.0, "loss": 1.0,
    "half_life": 1_000_000.0, "last_tend": 0.0, "now_epoch": 0.0,
    "scale": 1000.0, "urge": 0.0, "urgency": 0.0,
    "pleasure": 0.0, "displeasure": 0.0, "arousal_contrib": 0.0,
    "threat": 0.0, "threat_c0": 1024.0, "threat_half_life": 8.0,
    "threat_now_epoch": 0.0, "threat_last_refresh": 0.0,
    "t_present": 256.0, "threat_precision": 0.0,
    "threat_persists": 0.0, "appraised": 1.0, "residual": 0.0,
    "learning_progress": 0.0, "value_progress": 0.0,
    "valued_goal": 0.0, "goal_blocked": 0.0, "blocker_present": 0.0,
    "contamination": 0.0, "loss_object": 0.0, "explore": 0.0,
    "was_engaged": 0.0, "supergraph_value": 0.0,
    "exploration_urge": 0.0, "is_affiliation": 0.0,
    "legitimacy": 0.0, "social_weight": 1.0,
    "doom_observation_epoch": -1.0,
}

_MODULATOR_DEFAULTS = {
    "enabled": 1.0, "competence": 0.0, "competence_base": 0.0,
    "competence_full": 100.0, "competence_lo": 30.0,
    "drive_switch_threshold": 5.0, "band_hi": 600.0, "band_mid": 150.0,
    "res_base": 500.0, "res_urg_div": 4.0, "res_ar_div": 1.0,
    "resolution_lo": 200.0, "resolution_hi": 450.0,
    "sel_div": 1.0, "sel_k": 1.0, "sel_threshold_hi": 200.0,
    "sec_k": 1.0, "securing_hi": 50.0, "uncertainty_hi": 100.0,
    "residual_thresh": 7.0, "w_supergraph": 1.0,
    "valence_raw": 0.0, "valence": 0.0, "arousal": 0.0,
    "arousal_band": 0.0, "resolution": 0.0, "sel_threshold": 0.0,
    "securing": 0.0, "epoch": -1.0,
}


def _edge(inner, src, edge_type, tgt):
    try:
        inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        inner.add_edge_unchecked(src, edge_type, tgt)


def _ensure_seed(agent, seed_id, sentinel_rule):
    names = {row.get("name") for row in agent.inner.export_rules()}
    if sentinel_rule not in names:
        agent.inner.load_seed_manifest(manifest_for(seed_id), agent.agent)


class DoomDualProcessAdapter:
    """Per-game mechanical wiring for PSI, dual process, and ControlBundle."""

    def __init__(self, agent, controls):
        self.agent = agent
        self.s = agent.s
        self.inner = agent.inner
        self.controls = controls
        self.game = controls.game

        _ensure_seed(agent, "drives", "drive_urge")
        _ensure_seed(agent, "modulators", "mod_valence")
        _ensure_seed(
            agent, "affective_state_core", "psi_project_canonical_affect")
        _ensure_seed(
            agent, "default_mode_core",
            "default_mode_integrate_latest_network_sample")
        _ensure_seed(
            agent, "doom_dual_process", "doom_candidate_exploration_value")

        self.hub = self.s.add_node("EmotionHub", {"domain": "doom"})
        _edge(self.inner, self.game, "has_emotion_hub", self.hub)
        _edge(self.inner, self.agent.agent, "has_emotion_hub", self.hub)
        self.modulators = self.s.add_node(
            "ModulatorState", dict(_MODULATOR_DEFAULTS))
        _edge(self.inner, self.hub, "has_modulator_state", self.modulators)

        affects = list(self.inner.neighbours(
            self.agent.agent, "has_affective_state"))
        if len(affects) != 1:
            raise RuntimeError(
                "Doom requires exactly one canonical AffectiveState")
        self.affect = affects[0]
        _edge(self.inner, self.hub, "has_affective_state", self.affect)
        _edge(self.inner, self.modulators, "projects_affect_to", self.affect)

        self.drives = {}
        for kind, target, current, critical, weight in (
            ("health", 100.0, 100.0, 0.0, 3.0),
            ("ammo", 50.0, 50.0, 0.0, 1.0),
            ("exploration", 1.0, 1.0, 0.0, 2.0),
        ):
            attrs = dict(_DRIVE_DEFAULTS)
            attrs.update({
                "name": f"doom_{kind}", "doom_need": kind,
                "v_d": target, "c_d": current, "c_d_prev": current,
                "v_0": critical, "weight": weight,
            })
            drive = self.s.add_node("Drive", attrs)
            _edge(self.inner, self.modulators, "has_active_drive", drive)
            self.drives[kind] = drive

        # Persistent per-affordance memory is graph state. Fresh epoch-bound
        # candidates copy these cells through doom_candidate_exploration_value.
        for control in self.controls.controls.values():
            attrs = self.s.node(control)["attrs"]
            for key, value in (
                ("doom_predicted_value", 0.0),
                ("doom_consolidation_strength", 0.0),
                ("doom_experience_count", 0.0),
                ("doom_reliability", 1.0),
            ):
                if key not in attrs:
                    self.inner.set_attr(control, key, value)

        task_sets = list(self.inner.neighbours(
            self.agent.agent, "has_doom_system_two_task_set"))
        areas = {
            self.s.node(node)["attrs"].get("area"): node
            for node in task_sets
        }
        if set(areas) != {"executive", "learning"}:
            raise RuntimeError(
                "Doom executive and learning task sets were not installed")
        self.executive_task_set = areas["executive"]
        self.learning_task_set = areas["learning"]
        policies = list(self.inner.neighbours(
            self.agent.agent, "has_doom_lifecycle_policy"))
        if len(policies) != 1:
            raise RuntimeError("Doom lifecycle policy was not installed")
        self.lifecycle_policy = policies[0]

    def observe_action_receipt(self, receipt, *, observed_epoch):
        """Publish one lossless actuator receipt as raw transport evidence."""
        node = self.s.add_node("DoomActionReceipt", {
            "action_id": int(receipt["action_id"]),
            "status": str(receipt["status"]),
            "authored_world_tick": int(receipt["authored_world_tick"]),
            "expires_world_tick": int(receipt["expires_world_tick"]),
            "receipt_world_tick": int(receipt["receipt_world_tick"]),
            "applied_world_tick": int(receipt.get(
                "applied_world_tick", -1)),
            "observed_epoch": int(observed_epoch),
            "doom_receipt_consumed": 0,
            "provenance_kind": "observed_transport_event",
        })
        _edge(self.inner, self.game, "has_doom_action_receipt", node)
        return node

    def observe_epoch(self, *, epoch, health, ammo, damage_taken=0.0,
                      respawned=False, new_cells=0.0, moved=False,
                      kill_delta=0.0,
                      attention_refused=0.0, motion_count=0.0,
                      salience_count=0.0):
        """Mint one raw observation, its context, and legal control candidates."""
        raw = {
            "epoch": int(epoch), "health": float(health), "ammo": float(ammo),
            "damage_taken": float(damage_taken),
            "respawned": float(bool(respawned)),
            "new_cells": float(new_cells), "moved": float(bool(moved)),
            "kill_delta": float(kill_delta),
            "attention_refused": float(attention_refused),
            "motion_count": float(motion_count),
            "salience_count": float(salience_count),
            "doom_outcome_consumed": 0,
        }
        observation = self.s.add_node("DoomStateObservation", raw)
        for drive in self.drives.values():
            _edge(self.inner, observation, "feeds_doom_drive", drive)

        context = self.s.add_node("DualProcessContext", {
            "status": "preparing", "epoch": int(epoch),
            "manifest_complete": 0,
            "expected_candidate_count": len(self.controls.controls),
            "prediction_error": 0.0, "novelty": 0.0, "uncertainty": 0.0,
            "system_two_reliability": 0.5,
            "system_two_expected_utility": 0.5,
            "system_two_latency": 0.2, "system_two_effort": 0.2,
            "arbitration_epoch": -1,
        })
        _edge(self.inner, self.agent.agent,
              "has_dual_process_context", context)
        _edge(self.inner, context, "observes_doom_state", observation)
        # Normal decisions recruit only the executive sheet. A pending
        # graph-observed outcome independently requests learning through
        # doom_request_learning_for_pending_outcome.
        _edge(self.inner, context, "recruits_system_two_task_set",
              self.executive_task_set)

        for control in self.controls.controls.values():
            candidate = self.s.add_node("SystemOneCandidate", {
                "status": "raw", "epoch": int(epoch),
                "default_value": 0.0, "urgency": 0.0, "valence": 0.0,
                "residual": 0.0, "grounded": 1.0, "reliability": 1.0,
                "learned_default": 0, "predicted_value": 0.0,
                "consolidation_strength": 0.0, "eligibility_trace": 0.0,
                "experience_count": 0.0, "accumulated_evidence": 0.0,
                "evidence_increment": 0.0, "evidence_epoch": -1,
                "score_epoch": -1,
            })
            _edge(self.inner, context,
                  "has_system_one_candidate", candidate)
            _edge(self.inner, candidate, "proposes_control", control)

        # Publication barrier.  Autonomous settling may run between any two
        # FFI calls above; neither the context activation rule nor the
        # current-context rules may observe this context until its complete
        # candidate manifest has been published.
        self.inner.set_attr(context, "manifest_complete", 1)
        for old in list(self.inner.neighbours(
                self.game, "has_current_dual_process_context")):
            self.inner.remove_edge(
                self.game, "has_current_dual_process_context", old)
        _edge(self.inner, self.game,
              "has_current_dual_process_context", context)
        return context

    def deliberate(self, context, world_tick, footprint_fn):
        """Invoke the native dual cycle and authorize its graph-authored intent."""
        for old in list(self.inner.neighbours(
                self.game, "has_current_dual_process_context")):
            if old != context:
                self.inner.remove_edge(
                    self.game, "has_current_dual_process_context", old)
        for control in list(self.inner.neighbours(
                self.game, "selected_control")):
            self.inner.remove_edge(self.game, "selected_control", control)
        self.inner.set_attr(self.game, "world_tick", int(world_tick))
        self.inner.set_attr(self.game, "bundle_open", 1.0)
        self.inner.set_attr(self.game, "chosen_control", "")

        report = self.agent.dual_process_tick()
        bundles = [
            bundle for bundle in self.inner.neighbours(
                self.game, "has_control_bundle")
            if int(self.s.node(bundle)["attrs"].get("world_tick", -1))
            == int(world_tick)
        ]
        if len(bundles) != 1:
            return None, report
        bundle = bundles[0]
        intents = list(self.inner.neighbours(bundle, "has_intent"))
        if len(intents) != 1:
            return None, report
        intent = intents[0]
        tokens = tuple(
            self.s.node(control)["attrs"]["token"]
            for control in self.inner.neighbours(bundle, "includes_control"))
        footprint = footprint_fn(tokens)
        # The host publishes only measured/declared consequence facts.  The
        # seed compares commit, wait, and refine values and authors the intent
        # status.  Completeness is written last so an autonomous tick cannot
        # authorize a partially described footprint.
        authorization = {
            "doom_expected_goal_work":
                float(footprint.get("expected_goal_work", 1.0)),
            "doom_expected_information_gain":
                float(footprint.get("expected_information_gain", 0.0)),
            "doom_uncertainty": float(footprint.get("uncertainty", 0.0)),
            "doom_deleted_facts": float(footprint.get("deleted_facts", 0.0)),
            "doom_overwritten_facts":
                float(footprint.get("overwritten_facts", 0.0)),
            "doom_recoverability":
                float(footprint.get("recoverability", 0.0)),
            "doom_externality": float(footprint.get("externality", 0.0)),
            "doom_wait_delay_cost": 0.1,
            "doom_refinement_cost": 0.2,
            "doom_authorization_input_complete": 0,
        }
        for key, value in authorization.items():
            self.inner.set_attr(intent, key, value)
        self.inner.set_attr(
            intent, "doom_authorization_input_complete", 1)
        self.inner.run_rules()
        return intent, report
