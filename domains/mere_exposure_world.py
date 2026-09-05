"""MereExposureWorld -- a MECHANICAL mere-exposure × initial-valence adapter
(block 293000, MERE_EXPOSURE_SOCIAL_PREREG.md).

ARCHITECTURE RULE COMPLIANCE (see CLAUDE.md): this file is a WORLD ADAPTER. It
does exactly two things -- ingest and emit -- around the CONFIRMED attitude path
`domains/hate_attribution.py` already exposes. It contains NO agent decision and
NO Python that computes the liking:

  * an EXPOSURE (a positive encounter) is `hate_attribution.record_hate_incident(
    ..., negative=False)`, which internally mints an IncidentReport, lets the
    seeded rules derive the attribution, then applies the CAN belief-update
    primitive `concept_apply_evidence(regard_for, +1.0, alpha)` and `run_rules()`.
    The regard STATE is PRODUCED by the engine's own discrete-3-state relaxation
    (`seeds/can_native_reimplementation.json`'s can_native_update_3state) -- this
    adapter only DRIVES the encounter and READS `regard_for.state` back.
  * INITIAL VALENCE is seeded by the SAME path (harm encounters, `negative=True`)
    -- neutral = none, negative_noncryst = a shallow pair, negative_cryst = a deep
    run that also crystallizes the TargetPattern. Which recipe to run is WORLD
    setup (data), not a decision over graph state.
  * the FELT QUALITY is read from `analogy_search.concept_signature`'s
    `dynamical:valence` coordinate -- a mechanical extraction, never computed here.

No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if/else` over the
regard's graph state that SELECTS the liking (the only conditionals are over WORLD
state -- which seeding recipe, has-it-crossed-yet, loop bounds). No
reward/punishment shaping: a positive encounter is a fixed `+1.0` evidence signal,
never a reward learned from outcomes.

No new seed is authored or loaded: the adapter reuses the existing, already-landed
seeds by import, so `load_all_seeds` / the base tree is byte-identical when this
adapter is absent (MERE_EXPOSURE_SOCIAL_PREREG.md Sec8).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as sr                                      # noqa: E402
from substrate.seed_loader import engine_rules_only            # noqa: E402
from domains.can_self_worth_bridge import ensure_can_seed      # noqa: E402
from domains.hate_attribution import (                         # noqa: E402
    mint_target_pattern, record_hate_incident)
from domains.analogy_search import concept_signature           # noqa: E402

# ---- FIXED protocol constants (pre-registered, MERE_EXPOSURE_SOCIAL_PREREG.md §3)
TEMPERATURE = 1.5        # ⇒ discrete-3-state crossing threshold ≈ 0.366
DEFAULT_ALPHA = 0.3      # belief plasticity ⇒ +0.3 external_field per positive enc
CROSS_THRESHOLD = 0.366  # engine's 3-state threshold at temperature=1.5 (reference)

# The seed files the confirmed attitude path depends on (reused, not authored).
_ATTITUDE_SEEDS = ("seeds/shared_arousal.json", "seeds/hate_attribution.json",
                   "seeds/qualia_space.json")

# The negative-valence seeding recipes (harm-encounter counts / plasticity) that
# produce each initial-valence condition. These are WORLD SETUP (data): the depth
# of the accumulated negative external_field is what the pre-reg's crossing-latency
# oracle is a function of. `negative_cryst` defaults to the "mid" depth; callers
# may pass an explicit recipe for shallower/deeper crystallized priors.
_SEED_RECIPES = {
    "neutral":            [],
    # two shallow harm encounters ⇒ external_field ≈ −0.6, state = −1
    "negative_noncryst":  [dict(alpha=0.3)] * 2,
    # a deeper, high-plasticity run ⇒ external_field ≈ −3.0, crystallized == 1
    "negative_cryst":     [dict(alpha=0.6)] * 5,
}


def _seed_path(name):
    return os.path.join(_ROOT, name)


class MereExposureWorld:
    """ONE target's attitude in ONE substrate. A `TargetPattern` + its tracked
    `regard_for` Concept (the discrete {−1,0,+1} liking unit). `seed_initial_valence`
    sets the pre-exposure prior via harm encounters; `encounter(positive=True)`
    applies one exposure; `regard_state()` / `qualia_valence()` read the engine's
    produced liking. No Python computes the liking.

    Optional per-agent PERSONALITY: `alpha` (belief plasticity, rescales the
    per-encounter step and thus crossing latency) and `spite_gain` (passed through
    to record_hate_incident's own trait hook). Both default to the pre-registered
    constants, so an agent with defaults reproduces the §5 oracle exactly.
    """

    def __init__(self, target="someone", *, alpha=DEFAULT_ALPHA, spite_gain=1.0,
                 temperature=TEMPERATURE, max_steps=3000):
        self.target = str(target)
        self.alpha = float(alpha)
        self.spite_gain = float(spite_gain)
        self.max_steps = int(max_steps)

        self.s = sr.Substrate()
        self.inner = self.s._inner
        # native CAN engine (+ decay/identity rules) -- the confirmed base
        ensure_can_seed(self.inner)
        # the attitude + qualia seeds the confirmed path depends on (reused)
        for name in _ATTITUDE_SEEDS:
            self.inner.load_seed_manifest(
                engine_rules_only(json.load(open(_seed_path(name)))))
        self.mt = self.inner.add_node("Microtheory", {
            "name": "mere_exposure", "temperature": float(temperature),
            "discrete_mode": "3state", "can_tick": 0})
        self.pat = mint_target_pattern(self.inner, self.mt, self.target)
        self.reg = next(iter(self.inner.neighbours(self.pat, "tracks_concept")))
        self._exposures = 0

    # ---- ingest -----------------------------------------------------------

    def seed_initial_valence(self, kind):
        """Establish the pre-exposure prior by running the recipe's HARM
        encounters through the SAME confirmed path (negative=True). `kind` is one
        of 'neutral' | 'negative_noncryst' | 'negative_cryst', or a list of
        per-encounter kwarg dicts for a custom (e.g. deeper) crystallized prior.
        Returns the post-seeding read. MECHANICAL: drive encounters, read."""
        recipe = kind if isinstance(kind, list) else _SEED_RECIPES[kind]
        for step in recipe:
            record_hate_incident(self.inner, self.mt, self.pat, negative=True,
                                 base_alpha=float(step.get("alpha", self.alpha)),
                                 spite_gain=float(step.get("spite_gain", self.spite_gain)),
                                 max_steps=self.max_steps)
        return self.read()

    def encounter(self, positive=True):
        """ONE exposure. positive=True is a mere-exposure (non-harmful) encounter
        -- the +1.0 evidence the mere-exposure effect is about; positive=False is a
        harm encounter (used only for seeding). The regard state is PRODUCED by the
        engine inside record_hate_incident; this method returns record_hate_incident's
        own dict augmented with the qualia read."""
        out = record_hate_incident(
            self.inner, self.mt, self.pat, negative=not positive,
            base_alpha=self.alpha, spite_gain=self.spite_gain,
            max_steps=self.max_steps)
        if positive:
            self._exposures += 1
        out.update(self.read())
        return out

    # ---- emit -------------------------------------------------------------

    def regard_state(self):
        """The engine's produced discrete liking: +1 (warmed), 0 (neutral),
        −1 (disliked) -- the marginal ⟨σ⟩ of the regard Concept, read straight."""
        return int(round(self.inner.node(self.reg)["attrs"]["state"]))

    def regard_external_field(self):
        """The underlying LINEAR accumulator (the graded observable beneath the
        discrete state) -- +0.3 per positive encounter at the default alpha."""
        return float(self.inner.node(self.reg)["attrs"]["external_field"])

    def regard_identity_field(self):
        """The regard Concept's committed prior (h_eff = external_field +
        identity_field). Reported to show it stays 0 through this path -- the crux
        of MERE_EXPOSURE_SOCIAL_PREREG.md §2a (no identity-level lock reachable)."""
        return float(self.inner.node(self.reg)["attrs"]["identity_field"])

    def crystallized(self):
        """The target's TargetPattern crystallization flag (a has_hate node minted
        by the seeded stability gate) -- distinct from identity_field (§2a)."""
        return bool(self.inner.node(self.pat)["attrs"]["crystallized"])

    def qualia_signature(self):
        """The full dynamical:* qualia coordinate list of the regard Concept
        (mechanical extraction via concept_signature)."""
        return [t for t in concept_signature(self.inner, self.reg)
                if t[0].startswith("dynamical:")]

    def qualia_valence(self):
        """The dynamical:valence coordinate value (+1 / −1), or None when the
        valence axis is absent (state 0). Must track regard_state's sign (§7 iii)."""
        for (dim, _pred, val) in self.qualia_signature():
            if dim == "dynamical:valence":
                return val
        return None

    def read(self):
        """One glass-box snapshot of everything a graph_to_dict dump exposes."""
        return dict(
            exposures=self._exposures,
            regard_state=self.regard_state(),
            regard_external_field=self.regard_external_field(),
            regard_identity_field=self.regard_identity_field(),
            crystallized=self.crystallized(),
            qualia_valence=self.qualia_valence(),
            qualia_signature=self.qualia_signature())

    # ---- convenience: the crossing-latency measure ------------------------

    def exposure_trajectory(self, budget=30):
        """Apply up to `budget` positive encounters, recording the produced
        regard_state / external_field / qualia_valence after each, and the crossing
        latency (first encounter with regard_state > 0). Returns
        {crossing_latency, trajectory:[{n, state, ext, qval, cryst}], crossed}.
        MECHANICAL sweep: drive one exposure, read; the crossing is the ENGINE's."""
        traj, cross = [], None
        for n in range(1, int(budget) + 1):
            self.encounter(positive=True)
            st = self.regard_state()
            traj.append(dict(n=n, state=st,
                             ext=self.regard_external_field(),
                             qval=self.qualia_valence(),
                             cryst=self.crystallized()))
            if cross is None and st > 0:
                cross = n
        return dict(crossing_latency=cross, trajectory=traj,
                    crossed=cross is not None)


def predicted_crossing_latency(initial_ext, *, budget=30, step=DEFAULT_ALPHA,
                               thr=CROSS_THRESHOLD):
    """The ANALYTIC crossing latency from the engine's own update law
    (MERE_EXPOSURE_SOCIAL_PREREG.md §4) -- PURE arithmetic, not a substrate run.
    Used only to CHECK the graph's own produced crossing against the pre-registered
    oracle. Returns the first positive-encounter count n with regard>0, or None."""
    import math
    if initial_ext > thr:
        return 0
    need = thr - float(initial_ext)
    n = int(math.ceil(need / float(step)))
    return n if 1 <= n <= int(budget) else None


__all__ = ["MereExposureWorld", "predicted_crossing_latency",
           "TEMPERATURE", "DEFAULT_ALPHA", "CROSS_THRESHOLD"]
