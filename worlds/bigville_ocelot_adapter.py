"""Real Ocelot cognition provider for the standalone Bigville package.

This is intentionally kept in Ocelot rather than packaged with Bigville.
Bigville publishes physical observations and accepts provider-owned proposals;
this module supplies the cognition implementation that can actually read a
document through Ocelot's deep reader and expose the resulting graph.

Usage (with both repositories on ``PYTHONPATH``)::

    from bigville import create_board_game
    from worlds.bigville_ocelot_adapter import BigvilleOcelotResident

    room = create_board_game(
        scenario="monopoly_four_players",
        backend="ocelot",
        cognition_factory=BigvilleOcelotResident,
    )

No Monopoly concepts are added here.  The rulebook is just text; Ocelot's
general document reader decides what structure it can recover.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from substrate.world_adapter import WorldAdapter
from domains.core_emotions_weight import quantize_weight
from scripts._build_affect_coupling_seed import CHANNEL_ROWS


# These are the graph attributes consumed by seeds/core_emotions.json.  They
# live here as adapter defaults, not as a second emotion implementation: the
# seed remains the only place that derives action tendency, valence, arousal,
# and the named emotion channels.
_EMOTION_PARAMS_DEFAULTS = {
    "enabled": 1.0,
    "w_supergraph": 1.0,
    "mood_bias": 0.0,
    "residual_thresh": 100.0,
    "high_arousal": 800.0,
    "mid_arousal": 400.0,
    "low_arousal": 50.0,
    "comms_on": 1.0,
}
_APPRAISAL_DEFAULTS = {
    "appraised": 1.0,
    "individual_benefit": 0.0,
    "individual_cost": 0.0,
    "supergraph_contribution": 0.0,
    "collective_success": 0.0,
    "collective_success_prev": 0.0,
    "contribution_by_self": 0.0,
    "observed_by_other": 0.0,
    "valued_goal": 0.0,
    "goal_blocked": 0.0,
    "blocker_present": 0.0,
    "attachment": 0.0,
    "regroundable": 0.0,
    "contamination": 0.0,
    "was_engaged": 0.0,
    "residual": 0.0,
    "residual_prev": 0.0,
    "threat": 0.0,
    "threat_c0": 0.0,
    "threat_half_life": 1.0,
    "threat_last_refresh": 0.0,
    "threat_now_epoch": 0.0,
    "t_present": 100.0,
    "v_max": 0.0,
    "step": 0.0,
    "step_prev": 0.0,
    "attach_v0": 0.0,
    "attach_k_now": 0.0,
    "attach_k_prev": 0.0,
}
_EMOTION_OUTPUT_KEYS = (
    "threat_precision", "threat_persists", "learning_progress",
    "value_progress", "happiness", "fulfilment_value", "total_value",
    "act_endorsed", "action_tendency", "emotion", "valence", "arousal",
    "n_fired", "hit_surprise", "hit_fear", "hit_anxiety", "hit_anger",
    "hit_frustration", "hit_disgust", "hit_joy", "hit_sadness",
    "hit_curiosity", "hit_boredom", "hit_fulfilment", "hit_pride",
)
_EMOTION_LABELS = {
    1: "surprise", 2: "fear", 3: "anxiety", 4: "anger",
    5: "frustration", 6: "disgust", 7: "joy", 8: "sadness",
    9: "curiosity", 10: "boredom", 11: "fulfilment",
}

# Renames a chosen SPEECH_MENU kind (already DECIDED by the seeded
# sp_choose_utterance Argmax, reading the resident's real Bond affect
# state) into `_speech_frame`'s existing alias vocabulary, so it can be
# rendered as a real sentence via goal_utterance instead of terminating
# as a bare label. A plain lookup, not a decision -- mirrors
# `_speech_kind_label`/`KIND_LABEL`'s own already-established shape.
# `barb`/`share` have no dedicated alias; they reuse the closest existing
# Searle-adjacent act (hostile complaint / topic disclosure) rather than
# inventing a new one.
KIND_TO_PREDICATE = {
    "greeting": "greeting", "smalltalk": "topic", "barb": "complaint",
    "hedged": "uncertainty", "share": "topic", "answer": "answer",
    "request": "request", "offer": "offer", "question": "question",
    "thanks": "thanks", "apology": "apology", "farewell": "farewell",
    "complaint": "complaint", "promise": "promise",
}

# Bucket-membership (mere-exposure/familiarity) warmth cap for _speech_bond's
# no-relationship/no-backstory fallback -- registered here, not tuned after
# seeing results. Well below warm_aff's full-strength range (a seeded
# admiration/gratitude backstory reaches regard~1-2); membership alone is a
# weak prior, not a strong bond.
FAMILIARITY_CAP = 0.3


def _bigville_seed(name: str) -> dict[str, Any]:
    """Load a Bigville cognition seed without making it a Bigville dependency."""
    candidates = []
    explicit = __import__("os").environ.get("BIGVILLE_ROOT")
    if explicit:
        candidates.append(Path(explicit) / "bigville" / "seeds")
    candidates.extend(Path(entry) / "bigville" / "seeds"
                     for entry in sys.path if entry)
    for directory in candidates:
        path = directory / f"{name}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    raise RuntimeError(
        "Bigville must be installed or on PYTHONPATH to use the Ocelot adapter"
    )


def _prepare_bigville_imports() -> None:
    """Expose Bigville's namespace modules beside Ocelot's modules.

    The standalone project deliberately has no substrate dependency, so its
    small ``domains`` and ``worlds`` modules are namespace-style packages.
    Ocelot has regular packages with those names.  Extending their search
    paths is the non-copying glue needed when both source trees share a
    process; it does not replace or bundle either project's code.
    """
    import domains
    import worlds

    for entry in sys.path:
        root = Path(entry)
        for package, module in ((domains, "domains"), (worlds, "worlds")):
            candidate = root / module
            if candidate.is_dir() and str(candidate) not in package.__path__:
                package.__path__.append(str(candidate))


class BigvilleOcelotResident:
    """An Ocelot-backed resident implementing Bigville's cognition seam."""

    def __init__(self, name: str):
        self.name = str(name)
        self.wa = WorldAdapter(shadow_read=True, deep_ingest=True)
        self.s = self.wa.s
        self.inner = self.wa.inner
        self.agent = self.wa.agent
        self._read_documents: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._voice_targets: dict[str, Any] = {}
        # Compatibility state used only by Bigville's encounter publisher;
        # the cognition decision and speech rendering remain Ocelot-owned.
        self.heard_events: dict[Any, Any] = {}
        self.told_events: dict[Any, int] = {}
        self.speech_choices: dict[str, dict[str, Any]] = {}
        self.identity: dict[str, Any] = {"name": self.name}
        self.personality: dict[str, Any] = {}
        self.memories: list[Any] = []
        self.held_frame_seeds: list[Any] = []
        self._character_seeded = False
        self._emotion_enabled = False
        self._emotion_hub = None
        self._emotion_params = None
        self._emotion_appraisal = None
        self._affective_state = None
        self._affect_coupler = None
        self._emotion_modulator = None
        self._emotion_competence = 0.0
        self._resident_can = None
        self._observed_object_ids: set[str] = set()
        self._emotion_epoch = 0.0
        self._emotion_history: list[dict[str, Any]] = []
        self._speech_options: list[Any] = []
        self._speech_bonds: dict[str, Any] = {}
        self._speech_encounters: dict[str, Any] = {}
        self._speech_kind_label: dict[int, str] = {}
        self._speech_option_keys: tuple[str, ...] = ()
        self._speech_encounter_defaults: dict[str, Any] = {}
        self._speech_occasion = 0

        for seed_name in (
            "bigville_actor_decision",
            "bigville_speech_decide",
            "bigville_loud_comm",
        ):
            self.inner.load_seed_manifest(_bigville_seed(seed_name), self.agent)
        self.inner.set_attr(self.agent, "name", self.name)
        for key in ("chosen_action", "chosen_kind", "chosen_trade",
                    "chosen_recipe", "chosen_target"):
            self.inner.set_attr(self.agent, key, "")
        self.inner.set_attr(self.agent, "decision_armed", 0.0)

    # ------------------------------------------------------- character/affect

    @staticmethod
    def _state_value(value):
        """Convert graph-owned values into the reverse API's JSON shape."""
        if isinstance(value, dict):
            return {str(key): BigvilleOcelotResident._state_value(item)
                    for key, item in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [BigvilleOcelotResident._state_value(item) for item in value]
        if hasattr(value, "value"):
            return value.value
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        return repr(value)

    @staticmethod
    def _graph_attrs(value: Any) -> dict[str, Any]:
        """Make durable character data safe for scalar graph attributes."""
        if not isinstance(value, dict):
            return {"value_json": json.dumps(value, sort_keys=True,
                                               default=str)}
        attrs = {}
        for key, item in value.items():
            key = str(key)
            if isinstance(item, (str, int, float, bool)) or item is None:
                attrs[key] = item
            else:
                attrs[key + "_json"] = json.dumps(item, sort_keys=True,
                                                   default=str)
        return attrs

    @staticmethod
    def _frame_parts(frame: Any) -> dict[str, Any]:
        if isinstance(frame, dict):
            result = dict(frame)
            result.setdefault("seed", result.get("name", "unnamed_frame"))
            return result
        return {"seed": str(frame)}

    def seed_character(self, *, identity=None, personality=None,
                       memories=None, held_frames=None, **_kwargs):
        """Load persistent character data into this resident's private graph.

        Bigville supplies these values as scenario data.  This method only
        materialises them and opts the resident into Ocelot's already-seeded
        emotional/belief machinery; it does not invent a Monopoly rule or a
        world fact.
        """
        if self._character_seeded:
            return self.dump_held_state()
        self.identity = dict(identity or {})
        self.identity.setdefault("name", self.name)
        self.personality = dict(personality or {})
        self.memories = list(memories or [])
        self.held_frame_seeds = list(held_frames or [])

        self.inner.set_attr(self.agent, "character_id", self.name)
        for key, value in self._graph_attrs(self.identity).items():
            self.inner.set_attr(self.agent, "identity_" + key, value)
        for key, value in self._graph_attrs(self.personality).items():
            # Keep scalar personality traits directly available to seeded
            # cognition.  Nested profiles remain attached as JSON below.
            if not key.endswith("_json"):
                self.inner.set_attr(self.agent, "personality_" + key, value)

        identity_node = self.s.add_node(
            "Identity", {"name": self.name, **self._graph_attrs(self.identity)})
        self.inner.add_edge_unchecked(self.agent, "has_identity", identity_node)
        for index, memory in enumerate(self.memories):
            memory_data = (dict(memory) if isinstance(memory, dict)
                           else {"content": memory})
            memory_data.setdefault("memory_id", f"{self.name}:memory:{index + 1}")
            memory_node = self.s.add_node(
                "Memory", {"owner": self.name, **self._graph_attrs(memory_data)})
            self.inner.add_edge_unchecked(self.agent, "holds", memory_node)
        for index, frame in enumerate(self.held_frame_seeds):
            frame_data = self._frame_parts(frame)
            frame_data.setdefault("frame_id", f"{self.name}:frame:{index + 1}")
            frame_node = self.s.add_node(
                "FrameSeed", {"owner": self.name, **self._graph_attrs(frame_data)})
            self.inner.add_edge_unchecked(self.agent, "holds", frame_node)

        profile = self.personality.get("emotion", {})
        if not isinstance(profile, dict):
            profile = {}
        enabled = self.personality.get(
            "emotional_core_enabled", profile.get("enabled", 1.0))
        self._emotion_enabled = bool(float(enabled or 0.0))
        if self._emotion_enabled:
            self._ensure_emotional_core(profile)
        self._character_seeded = True
        return self.dump_held_state()

    def _ensure_emotional_core(self, profile):
        """Attach the upgraded emotion and belief seeds to this resident."""
        if self._emotion_hub is not None:
            return
        # Direct adapter use may provide BIGVILLE_ROOT without putting the
        # sibling checkout on sys.path.  Make the namespace bridge available
        # before the generic CAN bridge imports bigville_can_beliefs.
        explicit = __import__("os").environ.get("BIGVILLE_ROOT")
        if explicit and explicit not in sys.path:
            sys.path.insert(0, explicit)
        _prepare_bigville_imports()

        from substrate.seed_loader import engine_rules_only, manifest_for
        from domains.can_self_worth_bridge import (
            ensure_peer_comparison_seed, find_or_build_resident_can,
        )
        from domains.envy import mint_domain_deservingness_belief
        from domains.hate_attribution import mint_target_pattern
        from domains.self_efficacy import (
            mint_domain_self_efficacy, sync_competence_to_affective_state,
        )

        # WorldAdapter already boots affective_state_core.  These are the
        # additional opt-in rules/belief schemas required by the new resident
        # emotional contract, loaded once per private graph.
        self.inner.load_seed_manifest(
            engine_rules_only(manifest_for("core_emotions")), self.agent)
        ensure_peer_comparison_seed(self.inner)
        for seed_name in ("shared_arousal", "hate_attribution"):
            loaded = [node for node in self.s.nodes("BigvilleLoadedSeed")
                      if self.s.node(node)["attrs"].get("seed") == seed_name]
            if not loaded:
                self.inner.load_seed_manifest(
                    engine_rules_only(manifest_for(seed_name)), self.agent)
                self.s.add_node("BigvilleLoadedSeed", {"seed": seed_name})

        emotion_params = dict(_EMOTION_PARAMS_DEFAULTS)
        parameter_overrides = profile.get("params", {})
        if not isinstance(parameter_overrides, dict):
            parameter_overrides = {}
        for key in emotion_params:
            value = parameter_overrides.get(
                key, self.personality.get(key, emotion_params[key]))
            if isinstance(value, (int, float, bool)):
                emotion_params[key] = float(value)
        emotion_params["w_supergraph_q"], emotion_params["w_scale_bits"] = (
            quantize_weight(emotion_params["w_supergraph"]))
        self._emotion_params = self.s.add_node("HeldEmotionParams", emotion_params)

        appraisal = dict(_APPRAISAL_DEFAULTS)
        appraisal_overrides = profile.get("appraisal", {})
        if not isinstance(appraisal_overrides, dict):
            appraisal_overrides = self.personality.get("emotion_appraisal", {})
        if isinstance(appraisal_overrides, dict):
            for key in appraisal:
                value = appraisal_overrides.get(key)
                if isinstance(value, (int, float, bool)):
                    appraisal[key] = float(value)
        self._emotion_appraisal = self.s.add_node("Appraisal", appraisal)

        self._emotion_hub = self.s.add_node(
            "EmotionHub", {"name": f"emotion:{self.name}"})
        supergraph = self.s.add_node(
            "Supergraph", {"name": f"social_game:{self.name}"})
        self._affective_state = next(
            iter(self.inner.neighbours(self.agent, "has_affective_state")), None)
        if self._affective_state is None:
            self._affective_state = self.s.add_node("AffectiveState", {
                "name": "neutral_affective_state", "baseline": 1.0,
                "valence": 0.0, "arousal": 0.0, "resolution": 0.0,
                "selection_threshold": 0.0, "securing": 0.0,
                "competence": 0.0, "epoch": -1.0,
            })
            self.inner.add_edge_unchecked(
                self.agent, "has_affective_state", self._affective_state)
        self._emotion_modulator = self.s.add_node("ModulatorState", {
            "enabled": 1.0, "valence": 0.0, "arousal": 0.0,
            "resolution": 0.0, "sel_threshold": 0.0, "securing": 0.0,
            "competence": 0.0, "epoch": 0.0,
        })
        self.inner.add_edge_unchecked(
            self._emotion_hub, "has_emotion_params", self._emotion_params)
        self.inner.add_edge_unchecked(
            self._emotion_hub, "has_appraisal", self._emotion_appraisal)
        self.inner.add_edge_unchecked(
            self._emotion_hub, "member_of", supergraph)
        self.inner.add_edge_unchecked(
            self._emotion_hub, "has_affective_state", self._affective_state)
        self.inner.add_edge_unchecked(
            self._emotion_modulator, "projects_affect_to", self._affective_state)

        params = self._can_params(profile)
        self._resident_can = find_or_build_resident_can(
            self.inner, {"name": self.name, "index": 0, "params": params})
        efficacy = mint_domain_self_efficacy(
            self.inner, self._resident_can, "tabletop")
        efficacy_prior = self.personality.get(
            "self_efficacy_prior", profile.get("self_efficacy_prior", 0.0))
        if isinstance(efficacy_prior, (int, float, bool)):
            self.inner.concept_apply_evidence(efficacy, float(efficacy_prior), 1.0)
        sync_competence_to_affective_state(
            self.inner, self._affective_state, efficacy)
        self._emotion_competence = float(
            self.s.node(efficacy)["attrs"].get("external_field", 0.0))
        deservingness = mint_domain_deservingness_belief(
            self.inner, self._resident_can, "tabletop")
        deservingness_prior = self.personality.get(
            "deservingness_prior", profile.get("deservingness_prior", 0.0))
        if isinstance(deservingness_prior, (int, float, bool)):
            self.inner.concept_apply_evidence(
                deservingness, float(deservingness_prior), 1.0)

        social = self.personality.get("social_dispositions", {})
        if not isinstance(social, dict):
            social = profile.get("social_dispositions", {})
        for target, aspects in social.items():
            if not isinstance(aspects, dict):
                continue
            pattern = mint_target_pattern(
                self.inner, self._resident_can["mt"], str(target))
            self._apply_social_aspects(pattern, str(target), aspects)
            self._couple_target_pattern(pattern)

        self._apply_generated_dispositions()
        self._ensure_affect_coupler(profile)

        self.inner.force_all_dirty()
        self.inner.run_rules()
        self._sync_affective_state()

    def _can_params(self, profile):
        """Fill the generic CAN builder's durable personality contract."""
        p = dict(self.personality)
        p.update(profile.get("can", {}) if isinstance(profile.get("can", {}), dict) else {})
        return {
            "resolution_bins": float(p.get("resolution_bins", 7.0)),
            "arousal": float(p.get("arousal", 0.2)),
            "prior_world_safe": float(p.get("prior_world_safe", 0.7)),
            "prior_self_worth": float(p.get("prior_self_worth", 0.5)),
            "charm_weight": float(p.get("charm_weight", 0.5)),
            "hostile_weight": float(p.get("hostile_weight", 0.5)),
            "prior_others_trust": float(p.get("prior_others_trust", 0.5)),
            "claim_weight": float(p.get("claim_weight", 0.5)),
            "w_supergraph": float(p.get("w_supergraph", 0.5)),
            "w_spite": float(p.get("w_spite", 0.2)),
            "mood_bias": float(p.get("mood_bias", 0.0)),
            "cred_on": float(p.get("cred_on", 1.0)),
            "valence": float(p.get("valence", 0.0)),
        }

    def _disposition_traits(self, profile):
        """The full 13-key _PARAM_SPEC-shaped disposition vector (EMOTIONAL_
        SYSTEMS_UNIFICATION_DESIGN.md sec1d/4a) -- same resolution as
        _can_params (personality, then profile['can'] override), exposed
        under its own name because disposition-transport callers (the
        AffectCoupler) and the CAN builder are legitimately separate
        consumers of the same drawn data, even though today every key is
        shared."""
        return self._can_params(profile)

    @staticmethod
    def _derive_log_weight_scale():
        """DYNAMIC, not a magic number: the integer log-weight SCALE
        (AFFECT_COUPLING_SHAPE_PREREG.md's log-weight correction) computed
        from two real, independently-motivated, already-existing data
        sources -- never a hand-picked literal, and re-derived every call
        (cheap: both sources are small, static tables) so a future change
        to either source recomputes SCALE automatically rather than
        silently going stale.

        Floor anchor: never lose precision the generator's own rounding
        ever contained. bigville_town100_world.py's own DRAW_CLIP_DECIMALS
        (currently 4) is the real number of decimal digits every _PARAM_
        SPEC trait is EVER drawn to; 10**DECIMALS is that same precision
        re-expressed in the log frame at the trait range's own [0,1]
        ceiling (where the relative step from one decimal-precision unit
        is largest).

        Ceiling anchor: never perturb the decision the consumer (sp_
        choose_utterance) actually makes. SPEECH_MENU's own smallest
        real base_value gap is the finest distinction that formula can
        see; the worst-case ratio any coupled trait's own _draw_clip
        [0,1] ceiling can reach over its registered reference mean bounds
        how large a single channel's log-weight rounding error can grow
        once re-exponentiated. `2` (gain x pathway_gain, the two
        multiplicative factors actually summed in log space) and `0.5`
        (the standard half-ULP bound of any round-to-nearest scheme) are
        structural facts about the Term tree and about rounding itself,
        not tuned parameters.

        SCALE is the max of both anchors -- whichever is more demanding
        wins; on the real registered data (AFFECT_COUPLING_SHAPE_RESULTS.md
        §0 correction) the source anchor dominates."""
        _prepare_bigville_imports()
        from worlds.bigville_town100_world import DRAW_CLIP_DECIMALS, _PARAM_SPEC
        from worlds.bigville_speech_world import SPEECH_MENU

        scale_from_source = 10 ** DRAW_CLIP_DECIMALS

        base_values = sorted({float(option.get("base_value", 0.0))
                              for option in SPEECH_MENU})
        gaps = [b - a for a, b in zip(base_values, base_values[1:]) if b > a]
        min_gap = min(gaps) if gaps else 1.0

        coupled_traits = ("hostile_weight", "charm_weight", "arousal", "w_spite")
        worst_ratio = max(hi / mean for key, (mean, sd, lo, hi) in _PARAM_SPEC.items()
                          if key in coupled_traits and hi)

        n_multiplicative_factors = 2  # gain x pathway_gain, structural
        half_ulp = 0.5  # round-to-nearest's own bound, not tuned
        scale_from_consumer = math.ceil(
            n_multiplicative_factors * half_ulp * worst_ratio / min_gap)

        return float(max(scale_from_source, scale_from_consumer))

    @staticmethod
    def _param_spec_reference_means():
        """The four gain-normalisation reference means, read DIRECTLY from
        bigville_town100_world.py's own _PARAM_SPEC -- not restated as
        separate adapter literals (the hygiene gap AFFECT_COUPLING_SHAPE_
        RESULTS.md's design-review named: hand-copied refs can desync from
        the generator's own means with no error, since Div's fail-quiet-
        to-0.0 on a stale/zeroed reference silently zeroes a gain)."""
        _prepare_bigville_imports()
        from worlds.bigville_town100_world import _PARAM_SPEC
        return {
            "arousal_ref": _PARAM_SPEC["arousal"][0],
            "hostile_ref": _PARAM_SPEC["hostile_weight"][0],
            "charm_ref": _PARAM_SPEC["charm_weight"][0],
            "spite_ref": _PARAM_SPEC["w_spite"][0],
        }

    def _ensure_affect_coupler(self, profile):
        """Idempotent: the resident's AffectCoupler node -- the registered
        gain vocabulary (EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md sec4) plus
        the raw disposition traits it is normalised from, plus the 4
        AffectChannel data rows the generic coupling rule
        (seeds/affect_coupling.json) reads via AttrByName. `coupling_on`
        starts 0.0 -- OFF by default; nothing reads affect_bias until a
        caller explicitly arms it."""
        if self._affect_coupler is not None:
            return self._affect_coupler

        loaded = [node for node in self.s.nodes("BigvilleLoadedSeed")
                  if self.s.node(node)["attrs"].get("seed") == "affect_coupling"]
        if not loaded:
            from substrate.seed_loader import engine_rules_only, manifest_for
            self.inner.load_seed_manifest(
                engine_rules_only(manifest_for("affect_coupling")), self.agent)
            self.s.add_node("BigvilleLoadedSeed", {"seed": "affect_coupling"})

        affective_state = next(
            iter(self.inner.neighbours(self.agent, "has_affective_state")), None)
        traits = self._disposition_traits(profile)
        refs = self._param_spec_reference_means()
        coupler = self.s.add_node("AffectCoupler", {
            "coupling_on": 0.0,
            # additive channels, used directly -- no normalisation needed
            "mood_bias": traits["mood_bias"],
            "trait_valence": traits["valence"],
            # raw inputs to the gain-normalisation rule
            "trait_arousal": traits["arousal"],
            "trait_hostile_weight": traits["hostile_weight"],
            "trait_charm_weight": traits["charm_weight"],
            "trait_w_spite": traits["w_spite"],
            "trait_cred_on": traits["cred_on"],
            # neutral gain defaults -- psi_resolve_disposition_gains
            # overwrites these when coupling_on=1
            "reactivity_gain": 1.0,
            "hostile_gain": 1.0,
            "warmth_gain": 1.0,
            "spite_gain": 1.0,
            # canonical integer-quantized log-weights (AFFECT_COUPLING_
            # SHAPE_PREREG.md's log-weight correction) -- the *_gain attrs
            # above are the derived/resolved float cache; these are the
            # real, declared, bounded-precision data. Neutral default 0
            # (additive identity in log space -- "no pathway modulation").
            "log_reactivity_weight": 0.0,
            "log_hostile_weight": 0.0,
            "log_warmth_weight": 0.0,
            "log_spite_weight": 0.0,
            # DYNAMIC, not a magic number -- see _derive_log_weight_scale's
            # own docstring for the two-anchor derivation. Declared as
            # graph data (read by the rule via Attr), never baked into the
            # rule JSON as a Lit.
            "log_weight_scale": self._derive_log_weight_scale(),
            # normalisation references, read DIRECTLY from bigville_
            # town100_world.py's own _PARAM_SPEC (see _param_spec_
            # reference_means) -- never hand-copied literals. Deliberately
            # UNCAPPED (RETRACTED an earlier gain_cap=2.0 -- see
            # AFFECT_COUPLING_SHAPE_RESULTS.md's correction note): every
            # trait these normalise is already drawn against an explicit
            # [0,1] _draw_clip bound, so a REAL resident's gain is already
            # naturally bounded; a deliberately out-of-population resident
            # is SUPPOSED to be able to produce a dominating gain.
            "arousal_ref": refs["arousal_ref"],
            "hostile_ref": refs["hostile_ref"],
            "charm_ref": refs["charm_ref"],
            "spite_ref": refs["spite_ref"],
            "unit_gain": 1.0,
            "unit_zero": 0.0,
        })
        self.inner.add_edge_unchecked(self.agent, "has_affect_coupler", coupler)
        if affective_state is not None:
            self.inner.add_edge_unchecked(coupler, "reads_affect", affective_state)
        # CHANNEL_ROWS (imported from scripts/_build_affect_coupling_seed.py)
        # is the single source of truth for the channel table -- its own
        # dict keys already match AffectChannel's node attrs 1:1, so no
        # second, hand-duplicated copy of the table exists here to drift.
        for row in CHANNEL_ROWS:
            channel = self.s.add_node("AffectChannel", dict(row))
            self.inner.add_edge_unchecked(coupler, "has_affect_channel", channel)
        self._affect_coupler = coupler
        return coupler

    def _couple_target_pattern(self, pattern):
        """Adds couples_affect_to edges (from this resident's own
        AffectCoupler) for the affinity-tagged target-scoped Concepts on
        `pattern` -- regard_for/admiration_for (warm), removal_desire_for/
        devaluation_for (hostile). pity_for/controllability_for are
        deliberately skipped (TARGET_SCOPED_COUPLING_PREREG.md's
        modularity constraint -- distinct Concepts stay distinct).
        Idempotent: checks for an existing edge before adding, so calling
        this more than once for the same pattern (mint_target_pattern
        itself is idempotent and gets called from multiple places -- the
        social_dispositions loop below AND bigville_disposition_apply.py's
        applier) never double-counts a channel in the coupling Sum."""
        coupler = self._ensure_affect_coupler({})
        already = set(self.inner.neighbours(coupler, "couples_affect_to"))
        for edge_type in ("tracks_concept", "tracks_removal_desire",
                          "tracks_admiration", "tracks_devaluation"):
            for concept in self.inner.neighbours(pattern, edge_type):
                if concept not in already:
                    self.inner.add_edge_unchecked(coupler, "couples_affect_to", concept)
                    already.add(concept)

    def _apply_generated_dispositions(self):
        """When personality carries a generated backstory (bigville_
        disposition_apply.py's own self_priors/bonds shape, e.g. from
        seeds/bigville_dispositions_cast100.json), apply it: real
        target-scoped Concepts for people/groups/self via the EXISTING
        applier (reused, not reimplemented), and copy ingroup_affinity/
        outgroup_suspicion directly onto personality so _speech_bond's
        existing fallback (personality.get("ingroup_affinity", 0.4)) sees
        the real generated value instead of always defaulting."""
        self_priors = self.personality.get("self_priors")
        if not isinstance(self_priors, dict):
            return
        for key in ("ingroup_affinity", "outgroup_suspicion"):
            if key in self_priors and key not in self.personality:
                self.personality[key] = self_priors[key]

        from domains.bigville_disposition_apply import (
            apply_resident_dispositions, index_bonds_by_holder,
        )
        bonds = self.personality.get("bonds", [])
        bonds_by_holder = index_bonds_by_holder(bonds if isinstance(bonds, list) else [])
        resident = dict(self.identity)
        resident.setdefault("name", self.name)
        for dim in ("class", "group", "role", "workplace_kind"):
            resident.setdefault(dim, "unspecified")
        result = apply_resident_dispositions(
            self.inner, resident, bonds_by_holder, {self.name: self_priors})
        from domains.hate_attribution import mint_target_pattern
        mt = result["resident_can"]["mt"]
        for name in result["people"] + result["groups"]:
            self._couple_target_pattern(mint_target_pattern(self.inner, mt, name))

    def _apply_social_aspects(self, pattern, target, aspects):
        from domains.resident_trust import mint_trust_beliefs

        concept_edges = {
            "regard": "tracks_concept",
            "removal_desire": "tracks_removal_desire",
            "pity": "tracks_pity",
            "admiration": "tracks_admiration",
            "devaluation": "tracks_devaluation",
            "controllability": "tracks_controllability",
        }
        for aspect, value in aspects.items():
            if not isinstance(value, (int, float, bool)):
                continue
            value = float(value)
            if aspect in ("resentment_debt", "gratitude_debt"):
                self.inner.set_attr(pattern, aspect, value)
            elif aspect == "arousal":
                nodes = self.inner.neighbours(pattern, "tracks_arousal")
                if nodes:
                    self.inner.set_attr(nodes[0], "level", value)
            elif aspect == "trust":
                beliefs = mint_trust_beliefs(
                    self.inner, self._resident_can["mt"], target)
                for concept in beliefs.values():
                    self.inner.concept_apply_evidence(concept, value, 1.0)
            elif aspect in concept_edges:
                nodes = self.inner.neighbours(pattern, concept_edges[aspect])
                if nodes:
                    self.inner.concept_apply_evidence(nodes[0], value, 1.0)

    def _sync_affective_state(self):
        if not self._emotion_enabled or self._emotion_appraisal is None:
            return
        app = self.s.node(self._emotion_appraisal)["attrs"]
        for source, target in (("valence", "valence"),
                               ("arousal", "arousal")):
            if source in app:
                self.inner.set_attr(self._emotion_modulator, target,
                                    float(app.get(source, 0.0)))
        self.inner.set_attr(self._emotion_modulator, "competence",
                            self._emotion_competence)
        self.inner.set_attr(self._emotion_modulator, "epoch", self._emotion_epoch)
        self.inner.run_rules()

    def _reset_emotion_outputs(self):
        """Clear one-shot seed readouts before a new appraisal pass.

        The core seed intentionally exposes latches on an Appraisal node so a
        single fixpoint can be inspected.  A persistent resident reuses that
        node across ticks, so the adapter clears the previous readout before
        publishing the next observation; otherwise an old curiosity/fear hit
        could keep driving later arousal forever.
        """
        if self._emotion_appraisal is None:
            return
        for key in _EMOTION_OUTPUT_KEYS:
            self.inner.set_attr(self._emotion_appraisal, key, 0.0)

    def _update_emotion(self, attributes=None):
        if not self._emotion_enabled or self._emotion_appraisal is None:
            return None
        attributes = attributes if isinstance(attributes, dict) else {}
        app = self.s.node(self._emotion_appraisal)["attrs"]
        objects = attributes.get("physical_objects", [])
        current_ids = {str(item.get("id")) for item in objects
                       if isinstance(item, dict) and item.get("id") is not None}
        fresh = current_ids - self._observed_object_ids
        self._observed_object_ids.update(current_ids)
        updates = {
            "residual_prev": float(app.get("residual", 0.0)),
            "residual": float(len(fresh)),
            "appraised": 1.0,
            "was_engaged": 1.0,
        }
        for key in _APPRAISAL_DEFAULTS:
            if key in attributes and isinstance(attributes[key], (int, float, bool)):
                updates[key] = float(attributes[key])
        self._emotion_epoch += 1.0
        updates["threat_now_epoch"] = self._emotion_epoch
        self._reset_emotion_outputs()
        for key, value in updates.items():
            self.inner.set_attr(self._emotion_appraisal, key, value)
        self.inner.force_all_dirty()
        self.inner.run_rules()
        self._sync_affective_state()
        state = self.emotional_state()
        self._emotion_history.append(state)
        return state

    def record_action_outcome(self, *, action="", applied=False,
                              supergraph_contribution=None,
                              collective_success=None, **_kwargs):
        """Publish a generic physical action outcome to the emotion seed.

        `supergraph_contribution`/`collective_success` (both optional): a
        real GRADED magnitude of the act's actual effect on the collective
        (e.g. held_board_games.py's own reach-delta -- objects that became
        reachable/unreachable to OTHER participants), not the bare 0/1
        success flag every prior caller published. Independently landable:
        a caller that doesn't pass them (every caller before this change)
        keeps today's byte-identical behavior exactly.
        """
        if not self._emotion_enabled or self._emotion_appraisal is None:
            return None
        app = self.s.node(self._emotion_appraisal)["attrs"]
        success = 1.0 if applied else 0.0
        graded = supergraph_contribution is not None
        updates = {
            "individual_benefit": success,
            "individual_cost": 0.0 if applied else 1.0,
            "goal_blocked": 0.0 if applied else 1.0,
            "blocker_present": 0.0 if applied else 1.0,
            "contribution_by_self": success,
            "supergraph_contribution": (float(supergraph_contribution) if graded
                                        else success),
            "collective_success_prev": float(app.get("collective_success", 0.0)),
            "collective_success": (float(collective_success) if collective_success is not None
                                   else float(app.get("collective_success", 0.0)) + success),
            "step_prev": float(app.get("step", 0.0)),
            "step": float(app.get("step", 0.0)) + success,
            "valued_goal": 1.0 if action and action != "observe_room" else
                           float(app.get("valued_goal", 0.0)),
        }
        self._reset_emotion_outputs()
        for key, value in updates.items():
            self.inner.set_attr(self._emotion_appraisal, key, value)
        self.inner.force_all_dirty()
        self.inner.run_rules()
        self._sync_affective_state()
        state = self.emotional_state()
        self._emotion_history.append(state)
        return state

    def record_social_incident(self, target, *, negative, violation_type="harm",
                               base_alpha=0.3):
        """Publish ONE real, target-directed social incident (SUPERGRAPH_
        WEIGHT_MAGNITUDE arc's Phase D): the live connective tissue
        between a resident's own computed spite_gain (AffectCoupler,
        psi_resolve_disposition_gains) and domains.hate_attribution.
        record_hate_incident, which already accepted a spite_gain
        parameter but had no real caller anywhere in the tree threading
        the resident's own value into it -- every existing caller (tests,
        demos) either omitted it (default 1.0, no effect) or hand-set a
        synthetic test value.

        Mints (idempotent) the target's TargetPattern if this is the
        first incident with them, and reads spite_gain from THIS
        resident's own AffectCoupler -- 1.0 (neutral) if coupling is off
        or unset, so this is byte-identical to every existing
        record_hate_incident call for a resident with no armed
        disposition. Returns record_hate_incident's own result dict.
        """
        from domains.hate_attribution import mint_target_pattern, record_hate_incident

        target = str(target)
        mt = self._resident_can["mt"]
        pattern = mint_target_pattern(self.inner, mt, target)
        self._couple_target_pattern(pattern)
        coupler = self._ensure_affect_coupler({})
        spite_gain = float(self.s.node(coupler)["attrs"].get("spite_gain", 1.0))
        return record_hate_incident(
            self.inner, mt, pattern, negative=negative,
            violation_type=violation_type, base_alpha=base_alpha,
            spite_gain=spite_gain)

    def emotional_state(self):
        if not self._emotion_enabled or self._emotion_appraisal is None:
            return {"enabled": False}
        app = dict(self.s.node(self._emotion_appraisal)["attrs"])
        affect = (dict(self.s.node(self._affective_state)["attrs"])
                  if self._affective_state is not None else {})
        keys = ("emotion", "action_tendency", "valence", "arousal",
                "happiness", "fulfilment_value", "total_value", "n_fired",
                "learning_progress", "value_progress", "hit_surprise",
                "hit_fear", "hit_anxiety", "hit_anger", "hit_frustration",
                "hit_disgust", "hit_joy", "hit_sadness", "hit_curiosity",
                "hit_boredom", "hit_fulfilment", "hit_pride")
        return {
            "enabled": True,
            "epoch": self._emotion_epoch,
            "emotion_label": _EMOTION_LABELS.get(
                int(round(float(app.get("emotion", 0.0)))), "none"),
            "appraisal": {key: app.get(key, 0.0) for key in keys
                          if key in app},
            "affective_state": affect,
            "history_length": len(self._emotion_history),
        }

    def replace_options(self, options):
        """Publish world affordances into the real Ocelot graph."""
        for option in list(self.inner.neighbours(self.agent, "has_option")):
            if self.s.node(option)["type"] == "ActorOption":
                self.inner.remove_node(option)
        for option in options:
            node = self.s.add_node("ActorOption", dict(option))
            self.inner.add_edge_unchecked(self.agent, "has_option", node)
        for key in ("chosen_action", "chosen_kind", "chosen_trade",
                    "chosen_recipe", "chosen_target"):
            self.inner.set_attr(self.agent, key, "")
        self.inner.set_attr(self.agent, "decision_armed", 1.0)

    def decide(self):
        """Run Ocelot's seeded affordance-selection rule and read its result."""
        self.inner.run_rules()
        attrs = self.s.node(self.agent)["attrs"]
        chosen = {}
        for option in self.inner.neighbours(self.agent, "has_option"):
            candidate = self.s.node(option)["attrs"]
            if candidate.get("action") == attrs.get("chosen_action"):
                chosen = dict(candidate)
                break
        chosen.update({
            "action": attrs.get("chosen_action", ""),
            "kind": attrs.get("chosen_kind", ""),
            "trade": attrs.get("chosen_trade", ""),
            "recipe": attrs.get("chosen_recipe", ""),
            "target": attrs.get("chosen_target", ""),
        })
        self.inner.set_attr(self.agent, "decision_armed", 0.0)
        return chosen

    def ingest_document(self, text, *, name="physically_read_document",
                        kind="document", author=None):
        """Read a physical rule-like document through Ocelot.

        ``kind`` is provenance (law, charter, proclamation, notice, rulebook,
        etc.), not an instruction to the world.  The same generic reader is
        used for all of them, and the resulting rule frames are private to
        this resident.
        """
        text = str(text or "")
        name = str(name)
        kind = str(kind)
        if not text:
            return None
        key = (name, text, kind)
        if key in self._read_documents:
            return self._read_documents[key]

        # Use the same document shape as Ocelot's uploaded-text reader.  These
        # calls are host-side transport only; the deep reader performs the
        # actual parsing, grounding, salience and held-answer construction.
        from domains.file_ingest import _attach_message, _tokenise_document

        document = self.s.add_node("UploadedDocument", {
            "filename": name,
            "kind": "text",
            "mime": "text/plain",
            "byte_length": len(text.encode("utf-8")),
            "text": text,
            "document_kind": kind,
            "author": "" if author is None else str(author),
        })
        _tokenise_document(self.wa, document, text)
        _attach_message(self.wa, filename=name, kind="text", caption=None,
                        attachment_ids=[document])
        self.inner.add_edge_unchecked(self.agent, "read", document)
        self.inner.add_edge_unchecked(self.agent, "holds", document)

        self.wa._deep_read_document(document, text)
        self.wa.comprehend()

        # The deep reader supplies language evidence.  The rule-frame reader
        # supplies the resident-owned interpretation layer needed by laws,
        # proclamations, charters, notices, contracts, and game instructions.
        # It never installs executable world rules.
        from domains.cognitive_rule_frames import read_rule_document

        cognitive = read_rule_document(self.wa, document, text,
                                       name=name, kind=kind, author=author)

        parses = [node for node in self.s.nodes("SentenceParse")
                  if self.s.node(node)["attrs"].get("flow") ==
                  self.s.node(document)["attrs"].get("deep_read_flow")]
        held_answers = [node for node in self.s.nodes("HeldAnswer")
                        if node in self.s.nodes("HeldAnswer")]
        doc_attrs = self.s.node(document)["attrs"]
        if doc_attrs.get("deep_read") == 1.0 and parses:
            understanding = self.s.add_node("Understanding", {
                "kind": "physical_prose",
                "source": name,
                "status": "held",
                "evidence": "deep_reader",
                "sentence_parses": len(parses),
                "held_answers": len(held_answers),
            })
            self.inner.add_edge_unchecked(document, "has_understanding", understanding)
            self.inner.add_edge_unchecked(self.agent, "holds", understanding)
            for parse in parses:
                self.inner.add_edge_unchecked(understanding, "supported_by", parse)
            result = {
                "status": "understood",
                "document": document,
                "understanding": understanding,
                "sentence_parses": parses,
                "held_answers": held_answers,
            }
        else:
            residual = self.s.add_node("ComprehensionResidual", {
                "kind": "physical_prose",
                "source": name,
                "status": "not_understood",
                "reason": doc_attrs.get("deep_read_error")
                and "deep reader error" or "no parse evidence",
            })
            self.inner.add_edge_unchecked(self.agent, "holds", residual)
            result = {"status": "not_understood", "document": document,
                      "residual": residual, "sentence_parses": parses,
                      "held_answers": held_answers}
        result.update({
            "document_kind": kind,
            "rule_document": cognitive["rule_document"],
            "held_rules": cognitive["rules"],
            "rule_cues": cognitive["cues"],
            "rule_evidence": cognitive["evidence"],
        })
        self._read_documents[key] = result
        return result

    def ingest_rulebook(self, text):
        """Compatibility alias for the generic document reader."""
        return self.ingest_document(text, name="physically_read_rulebook",
                                     kind="rulebook")

    def has_read_document(self, text, *, name="physically_read_document",
                          kind="document"):
        return (str(name), str(text or ""), str(kind)) in self._read_documents

    def observe_situation(self, text="", *, cues=None, kind="world_observation",
                          source=None, attributes=None):
        """Feed a current observation into the resident's private rule faculty."""
        from domains.cognitive_rule_frames import observe_situation

        result = observe_situation(self.wa, text, cues=cues, kind=kind,
                                   source=source, attributes=attributes)
        self._update_emotion(attributes)
        return result

    def commit_rule_prediction(self, prediction, **kwargs):
        """Explicitly use a held prediction as a goal/plan/communication input."""
        from domains.cognitive_rule_frames import commit_prediction

        return commit_prediction(self.wa, prediction, **kwargs)

    def draft_document(self, text, *, name="document", kind="document",
                       audience=None, source_prediction=None):
        """Compose a private law/proclamation/notice/charter draft."""
        from domains.cognitive_rule_frames import draft_document

        return draft_document(self.wa, text, name=name, kind=kind,
                              audience=audience,
                              source_prediction=source_prediction)

    def revise_document_draft(self, draft, text):
        from domains.cognitive_rule_frames import revise_document_draft

        return revise_document_draft(self.wa, draft, text)

    def propose_document_write(self, draft, *, destination=None, priority=1.0):
        """Return a world-facing write proposal without publishing it."""
        from domains.cognitive_rule_frames import propose_document_write

        return propose_document_write(self.wa, draft, destination=destination,
                                      priority=priority)

    # ------------------------------------------------------------------ speech

    def _ensure_speech_graph(self):
        """Materialise the held spontaneous-speech menu in Ocelot's graph."""
        if self._speech_options:
            return
        # Direct adapter use (decide_speech called without seed_character
        # ever running _ensure_emotional_core, e.g. emotional_core_enabled
        # unset/0) may provide BIGVILLE_ROOT without putting the sibling
        # checkout on sys.path -- same bridge _ensure_emotional_core
        # already does, needed here independently since this method can
        # run standalone.
        explicit = __import__("os").environ.get("BIGVILLE_ROOT")
        if explicit and explicit not in sys.path:
            sys.path.insert(0, explicit)
        _prepare_bigville_imports()
        # Initialise Bigville's package before importing its namespace-style
        # world modules; otherwise ``bigville.runtime`` can re-enter
        # bigville_bond_world while that module is still being initialised.
        import bigville  # noqa: F401
        from worlds.bigville_bond_world import KNOBS, SLOT_DEFAULTS
        from worlds.bigville_speech_world import (
            ENCOUNTER_DEFAULTS, KIND_LABEL, SPEECH_MENU, _OPT_KEYS,
        )
        self._speech_kind_label = dict(KIND_LABEL)
        self._speech_option_keys = tuple(_OPT_KEYS)
        self._speech_encounter_defaults = dict(ENCOUNTER_DEFAULTS)
        # The sibling encounter helper predates the full seeded decision
        # contract and omits these neutral graph knobs.  Supply the values
        # registered by BIGVILLE_SPEECH_PREREG; they remain editable per
        # character below.
        self._speech_encounter_defaults.update({
            "occasion_gain": 1.0, "norm_gain": 3.0, "affect_gain": 1.0,
            "goal_gain": 1.0, "arousal_gain": 1.0, "civil_gain": 1.0,
        })
        self._speech_slot_defaults = dict(SLOT_DEFAULTS)
        self._speech_knobs = dict(KNOBS)
        coupler = self._ensure_affect_coupler({})
        for option in SPEECH_MENU:
            attrs = {key: 0.0 for key in self._speech_option_keys}
            attrs.update(option)
            # Mirror onto the canonical affinity_* names the generic
            # coupling rule (seeds/affect_coupling.json) reads -- SPEECH_
            # MENU's own warm_aff/hostile_aff ARE the affinity signature,
            # just under bigville's own local name (worlds/bigville_
            # speech_world.py). affect_bias starts explicit 0.0 so it is
            # always a valid float even before any rule runs.
            attrs["affinity_warm"] = float(attrs.get("warm_aff", 0.0))
            attrs["affinity_hostile"] = float(attrs.get("hostile_aff", 0.0))
            attrs["affect_bias"] = 0.0
            node = self.s.add_node("SpeechOption", attrs)
            self.inner.add_edge_unchecked(coupler, "couples_affect_to", node)
            self._speech_options.append(node)

    def _speech_personality(self, target):
        social = self.personality.get("social_dispositions", {})
        if not isinstance(social, dict):
            return {}
        value = social.get(str(target), {})
        return dict(value) if isinstance(value, dict) else {}

    def _live_target_regard(self, target):
        """The LIVE, currently-held regard/admiration/devaluation/trust
        toward `target`, read from this resident's own target-scoped
        Concepts (domains.hate_attribution.mint_target_pattern) -- as
        opposed to _speech_personality's frozen social_dispositions
        SNAPSHOT, which seed_character applies ONCE as these Concepts'
        initial evidence (_apply_social_aspects) and then never revisits.
        A real incident recorded afterward (record_social_incident) moves
        these Concepts' external_field; without this read, decide_speech
        could never see that -- it would keep reading the seed-time
        snapshot forever. Returns None (not {}) when this resident holds
        no target-scoped belief about `target` at all, so _speech_bond
        falls through to _speech_personality/bucket-familiarity exactly
        as before for a genuinely unknown target."""
        if self._resident_can is None:
            return None
        target = str(target)
        mt = self._resident_can["mt"]
        by_name = {self.s.node(c)["attrs"].get("name"): c
                  for c in self.inner.neighbours(mt, "has_concept")}
        aspect_names = {"regard": "regard_for:%s" % target,
                        "admiration": "admiration_for:%s" % target,
                        "devaluation": "devaluation_for:%s" % target}
        live = {aspect: float(self.s.node(by_name[name])["attrs"].get(
                   "external_field", 0.0))
               for aspect, name in aspect_names.items() if name in by_name}
        if not live:
            return None
        comp_name = "competence_for:%s" % target
        will_name = "willingness_for:%s" % target
        if comp_name in by_name and will_name in by_name:
            comp = float(self.s.node(by_name[comp_name])["attrs"].get(
                "external_field", 0.0))
            will = float(self.s.node(by_name[will_name])["attrs"].get(
                "external_field", 0.0))
            live["trust"] = min(comp, will)
        return live

    def _speech_bond(self, target, relationship=None, shared_bucket_count=0):
        self._ensure_speech_graph()
        target = str(target)
        bond = self._speech_bonds.get(target)
        if bond is None:
            attrs = dict(self._speech_slot_defaults)
            attrs.update(self._speech_knobs)
            attrs.update({"holder_name": self.name, "toward_name": target,
                          "prior_kind": "chosen"})
            bond = self.s.add_node("Bond", attrs)
            self.inner.add_edge_unchecked(self.agent, "holds_bond", bond)
            target_node = self.s.add_node("Townsperson", {"name": target})
            self.inner.add_edge_unchecked(bond, "toward", target_node)
            self._speech_bonds[target] = bond

        # Relationship slots are an ordinary projection of held character
        # data into the speech seed.  The seed chooses the speech option.
        # LIVE target-scoped belief wins over the frozen social_
        # dispositions snapshot when this resident holds one at all --
        # they start identical (seed_character applies the snapshot AS
        # the Concepts' own initial evidence), so this is byte-identical
        # until a real incident (record_social_incident) moves the live
        # value away from that starting point.
        profile = self._live_target_regard(target) or self._speech_personality(target)
        if relationship:
            strength = float(relationship.get("strength", 0.0))
            kind = str(relationship.get("kind", "acquaintance"))
            self.inner.set_attr(bond, "tie_strength", max(0.0, strength))
            self.inner.set_attr(bond, "affect_affection", max(0.0, strength))
            self.inner.set_attr(
                bond, "affect_resentment",
                max(0.0, -strength) if kind == "feud" else 0.0)
            self.inner.set_attr(bond, "prior_kind", kind)
        elif profile:
            regard = float(profile.get("regard", 0.0))
            admiration = float(profile.get("admiration", 0.0))
            devaluation = float(profile.get("devaluation", 0.0))
            trust = float(profile.get("trust", 0.0))
            self.inner.set_attr(bond, "tie_strength",
                                max(0.0, regard, admiration))
            self.inner.set_attr(bond, "affect_affection",
                                max(0.0, regard, admiration))
            self.inner.set_attr(bond, "affect_resentment",
                                max(0.0, -regard, devaluation))
            self.inner.set_attr(bond, "affect_contempt", max(0.0, devaluation))
            self.inner.set_attr(bond, "belief_trust", trust)
            self.inner.set_attr(bond, "affect_trust", trust)
            self.inner.set_attr(bond, "affect_gratitude",
                                float(profile.get("gratitude_debt", 0.0)))
        elif shared_bucket_count > 0:
            # No relationship history AND no explicit backstory -- but not a
            # genuinely unclassified stranger either. Mere-exposure/
            # familiarity (Zajonc 1968) via bucket membership alone (Tajfel,
            # Billig, Bundy & Flament 1971's minimal-group point: an
            # arbitrary shared category, no real content, is enough) reads
            # as mild warmth, capped well below a real seeded/live
            # disposition -- membership is a weak prior, not a strong bond.
            # A resident's OWN generated ingroup_affinity (bigville_
            # disposition_apply.py's self_priors, default 0.4 = that
            # generator's own registered mean) scales it; a genuinely
            # unclassified target (shared_bucket_count==0) still falls
            # through to zero, unchanged from before this fix.
            ingroup_affinity = float(self.personality.get("ingroup_affinity", 0.4))
            familiarity = min(FAMILIARITY_CAP,
                              ingroup_affinity * shared_bucket_count / 3.0)
            self.inner.set_attr(bond, "affect_affection", max(0.0, familiarity))
        return bond

    def _speech_utterance(self, encounter, arousal):
        attrs = {
            "speaker_arousal": float(arousal), "base_loudness": 1.0,
            "loud_arousal_gain": 0.6, "max_loudness": 100.0,
            "eff_loudness": 0.0, "choice_on": 1.0, "loudness_on": 1.0,
            "chosen_loudness": 0.0, "loud_armed": 1.0,
        }
        utterance = self.s.add_node("Utterance", attrs)
        self.inner.add_edge_unchecked(utterance, "spoken_by", self.agent)
        self.inner.add_edge_unchecked(encounter, "has_utterance", utterance)
        self.inner.run_rules()
        return utterance

    @staticmethod
    def _speech_frame(meaning):
        """Map Bigville's raw speech payload to an Ocelot SemanticFrame.

        This is the adapter's data-shape boundary only.  It does not compose
        prose.  Ocelot's ``WorldAdapter.full_text_for`` performs the actual
        full-text production from the resulting frame.
        """
        if not isinstance(meaning, dict) or not meaning:
            return {"event": "say", "agent": "I", "patient": str(meaning),
                    "tense": "present", "intent": "inform"}
        if any(key in meaning for key in
               ("event", "agent", "patient", "location")):
            frame = dict(meaning)
            frame.setdefault("intent", "inform")
            return frame

        keys = [key for key in meaning if key != "force"]
        if not keys:
            return {"event": "say", "agent": "I", "tense": "present",
                    "intent": "inform"}
        predicate = str(keys[0])
        payload = meaning[predicate]

        def value_for(value, *names):
            if isinstance(value, dict):
                for name in names:
                    if name in value:
                        return value[name]
            return value

        if predicate == "weather":
            weather = value_for(payload, "of")
            return {"event": "be", "agent": "weather", "patient": str(weather),
                    "role_kinds": {"patient": "adjective"},
                    "tense": "present", "intent": "inform"}
        if predicate == "news":
            payload = value_for(payload, "of")
            if isinstance(payload, dict) and "village" in payload:
                return BigvilleOcelotResident._speech_frame(payload["village"])
            detail = value_for(payload, "detail")
            subject = value_for(payload, "subject")
            return {"event": "hear", "agent": "I",
                    "patient": str(detail or subject or payload),
                    "tense": "present", "intent": "inform"}

        aliases = {
            "greeting": "greet", "warning": "warn",
            "uncertainty": "doubt", "acknowledgement": "understand",
            "answer": "understand", "request": "request", "offer": "offer",
            "question": "ask", "thanks": "thank", "apology": "apologize",
            "farewell": "leave", "complaint": "complain", "promise": "promise",
            # ``topic`` is a raw communicative meaning from the generic
            # Bigville encounter bridge.  It is not surface text; map it to
            # an ordinary Ocelot event so the full renderer supplies the
            # sentence.
            "topic": "discuss",
        }
        target = value_for(payload, "of", "to", "from", "about")
        frame = {"event": aliases.get(predicate, predicate), "agent": "I",
                 "tense": "present",
                 "intent": "ask" if predicate == "question" else "inform"}
        if target is not None:
            frame["patient"] = str(target)
        return frame

    def goal_utterance(self, target, meaning, *, priority=1.0):
        """Use Ocelot's graph goal and full-text speech machinery."""
        interlocutor = self._voice_targets.get(str(target))
        if interlocutor is None:
            interlocutor = self.wa._interlocutor(str(target))
            self._voice_targets[str(target)] = interlocutor
        self.wa.set_addressee(interlocutor)
        self.wa.add_communicative_goal(
            meaning, priority=priority, render_meaning=self._speech_frame(meaning))
        spoken = self.wa._communicative_action(full_text=True)
        return spoken[-1] if spoken else None

    def decide_speech(self, target, *, relationship=None, shared_bucket_count=0,
                      obligation=False, fpp_is_greeting=False, fpp_is_question=False,
                      share_salience=0.0, goal_pressure=0.0, stranger=False,
                      arousal=0.4, loquacity_threshold=1.0, **_kwargs):
        """Run Ocelot's seeded spontaneous-speech decision.

        The room supplies encounter inputs.  ``bigville_speech_decide``
        selects a SpeechOption from the graph, including silence; this
        adapter only reads the selected code and returns it to Bigville.
        """
        self._ensure_speech_graph()
        target = str(target)
        old = self._speech_encounters.get(target)
        if old is not None and self.s.has_node(old):
            self.inner.remove_node(old)
        # The ad hoc inline mood-read this used to do here (max-blending
        # emotional_state()'s appraisal arousal into the caller-supplied
        # `arousal`) is RETIRED (AFFECT_COUPLING_SHAPE_PREREG.md Phase 3,
        # EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md sec1b's own named
        # precedent for exactly this pattern). Live AffectiveState.arousal
        # now reaches the decision ONLY through the generic coupler
        # (arousal_hostile/arousal_warm channels, seeds/affect_coupling.
        # json) when a resident's AffectCoupler.coupling_on is armed --
        # `arousal` here stays purely the world-supplied encounter input.
        attrs = dict(self._speech_encounter_defaults)
        speech_profile = self.personality.get("speech", {})
        if not isinstance(speech_profile, dict):
            speech_profile = {}
        for key in ("occasion_gain", "norm_gain", "affect_gain",
                    "goal_gain", "arousal_gain", "civil_gain", "face_weight"):
            value = speech_profile.get(key, self.personality.get(key))
            if isinstance(value, (int, float, bool)):
                attrs[key] = float(value)
        if "loquacity_threshold" in speech_profile:
            loquacity_threshold = float(speech_profile["loquacity_threshold"])
        elif isinstance(self.personality.get("talkativeness"), (int, float)):
            # Lower seeded threshold means a lower bar to speak.  This is a
            # character parameter conversion, not a speech choice.
            loquacity_threshold = max(
                0.05, 1.2 - float(self.personality["talkativeness"]))
        attrs.update({
            "obligation": 1.0 if obligation else 0.0,
            "fpp_is_greeting": 1.0 if fpp_is_greeting else 0.0,
            "fpp_is_question": 1.0 if fpp_is_question else 0.0,
            "share_salience": float(share_salience),
            "goal_pressure": float(goal_pressure),
            "stranger": 1.0 if stranger else 0.0,
            "speaker_arousal": float(arousal),
            "loquacity_threshold": float(loquacity_threshold),
            # Minted UNARMED (settling-order fix, AFFECT_COUPLING_SHAPE_
            # PREREG.md sec0b): install order loads bigville_speech_decide
            # before _ensure_emotional_core's seeds, so an armed-on-mint
            # Encounter could read a stale (never-yet-computed) affect_bias
            # on its very first fixpoint. One settle pass, then arm.
            "decide_armed": 0.0,
            "chosen_speech_code": -1.0,
            "absence_minted": 0.0,
        })
        encounter = self.s.add_node("Encounter", attrs)
        self.inner.add_edge_unchecked(
            encounter, "at_bond",
            self._speech_bond(target, relationship, shared_bucket_count))
        self._speech_encounters[target] = encounter
        self.inner.run_rules()
        self.inner.set_attr(encounter, "decide_armed", 1.0)
        self.inner.run_rules()
        chosen_attrs = self.s.node(encounter)["attrs"]
        code = int(round(float(chosen_attrs.get("chosen_speech_code", -1.0))))
        kind = self._speech_kind_label.get(code, "undecided")
        choice = {"target": target, "code": code, "kind": kind,
                  "spoken": code not in (-1, 0), "encounter": encounter}
        if choice["spoken"]:
            # DELIVERY (loudness, Schegloff/arousal-coupling, unchanged) and
            # CONTENT are two separate concerns. The chosen `kind` used to
            # terminate here as a bare label with a mute Utterance node
            # (loudness attrs only, no meaning, no text) -- the fix routes
            # it through the SAME free-text goal pipeline goal_utterance
            # already uses, so a resident's actual disposition (which
            # already correctly drove `kind` via the real, populated
            # SPEECH_MENU affect coefficients) produces a REAL sentence,
            # not a category label. KIND_TO_PREDICATE is a plain rename
            # into _speech_frame's existing alias vocabulary -- the kind
            # was already decided by the rule; this only relabels it.
            utterance = self._speech_utterance(encounter, arousal)
            choice["loudness"] = float(
                self.s.node(utterance)["attrs"].get("eff_loudness", 1.0))
            choice["utterance"] = utterance
            predicate = KIND_TO_PREDICATE.get(kind)
            if predicate is not None:
                self._speech_occasion += 1
                meaning = {predicate: {
                    "of": target,
                    "occasion": "spontaneous_%d_%s" % (self._speech_occasion, target),
                }}
                choice["act"] = predicate
                choice["text"] = self.goal_utterance(target, meaning)
        self.speech_choices[target] = choice
        return choice

    def dump_held_state(self):
        """Reverse API: expose the resident's actual Ocelot graph projection."""
        def nodes(types):
            out = []
            for type_name in types:
                for node in self.s.nodes(type_name):
                    out.append({"type": type_name, "id": int(node.value),
                                "attrs": dict(self.s.node(node)["attrs"])})
            return out

        return {
            "character_id": self.name,
            "backend": "ocelot",
            "identity": dict(self.identity),
            "personality": dict(self.personality),
            "memories": list(self.memories),
            "held_frames": nodes(("Frame", "Microtheory", "Concept",
                                   "FrameSeed", "Memory", "Identity",
                                   "EmotionHub", "HeldEmotionParams", "Appraisal",
                                   "AffectiveState", "ModulatorState", "Supergraph",
                                   "TargetPattern", "TargetArousal", "Resident",
                                   "Bond", "Townsperson", "SpeechOption",
                                   "Encounter", "Utterance",
                                   "UploadedDocument", "Document",
                                   "Understanding", "ComprehensionResidual",
                                   "SentenceParse", "HeldAnswer",
                                   "CognitiveRuleDocument", "HeldRule",
                                   "CognitiveCue", "CognitiveObservation",
                                   "RuleActivation", "RulePrediction",
                                   "CognitiveCommitment", "DocumentDraft",
                                   "DocumentWriteIntent",
                                   "CognitiveCommunicationIntent")),
            "concepts": nodes(("Concept", "Sign")),
            "goals": nodes(("Goal", "CommunicativeGoal")),
            "beliefs": nodes(("Belief", "Fact", "SmEntity", "SmEvent")),
            "decision": {**self._state_value(self.s.node(self.agent)["attrs"]),
                         "speech_choices": self._state_value(self.speech_choices)},
            "backend_state": {"graph_nodes": len(self.s.nodes()),
                              "read_documents": len(self._read_documents),
                              "rule_documents": len(list(self.s.nodes("CognitiveRuleDocument"))),
                              "held_rules": len(list(self.s.nodes("HeldRule"))),
                              "rule_activations": len(list(self.s.nodes("RuleActivation"))),
                              "rule_predictions": len(list(self.s.nodes("RulePrediction"))),
                              "document_drafts": len(list(self.s.nodes("DocumentDraft"))),
                              "emotional_state": self.emotional_state(),
                              "emotion_history": list(self._emotion_history[-8:]),
                              "character_seeded": self._character_seeded},
        }


def create_bigville_cognition_factory():
    """Return the factory expected by ``bigville.create_board_game``."""
    return BigvilleOcelotResident


def create_bigville_board_game(**kwargs):
    """Convenience entry point for running Bigville with real Ocelot minds."""
    _prepare_bigville_imports()
    from bigville import create_board_game

    kwargs.setdefault("backend", "ocelot")
    kwargs["cognition_factory"] = BigvilleOcelotResident
    return create_board_game(**kwargs)


__all__ = ["BigvilleOcelotResident", "create_bigville_board_game",
           "create_bigville_cognition_factory"]
