"""TraitAnxietyWorld -- a MECHANICAL trait-anxiety NEGATIVE INTERPRETATION BIAS
adapter (block 292000).

Reproduces MacLeod & Mathews' finding that high trait-anxious people interpret
AMBIGUOUS stimuli as threatening more than low-anxious people -- a TRAIT x
AMBIGUITY INTERACTION, not a main effect (SAFE / THREAT stimuli are interpreted
the same by everyone). See TRAIT_ANXIETY_INTERPRETATION_PREREG.md (§2-§6).

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It does exactly two things -- INGEST and EMIT --
around ``run_rules()``. It contains NO Python decision computing the emotion:

  * The emotion is the graph's own read-off: the REAL ``emx_anxiety`` region
    predicate (tools/build_modulator_seeds.py, order 10) sets ``ms.hit_anxiety``
    and ``emx_readoff`` (order 13) writes ``ms.emotion``. This adapter only READS
    ``ms.emotion`` + ``ms.securing`` off the graph.
  * TRAIT-ANXIETY is the SKEPTICISM trait (domains/disposition.py); AMBIGUITY is
    the leading drive's ``exploration_urge``. Both are node ATTRS the RULES read
    -- this adapter only SETS them (mechanical stimulus setup, data), seeds the
    skepticism trait, and calls ``trait_modulator_bridge.sync_traits_to_modulator``
    (which WRITES ``skepticism_bias`` from the crystallised trait level) so the
    grounded ``mod_securing`` formula bends securing by the personality offset.

The spine (EmotionHub + ModulatorState + leading threat Drive + the drives /
modulators / affective_state_core seeds) is built/located by
``trait_modulator_bridge.ensure_modulator_state`` -- REUSED, not reinvented.

No ``graph_rewrite.run`` / ``_match`` / ``_apply`` / ``make_rule``; no if/else
over graph state that SELECTS the emotion (the only conditionals are over WORLD
state -- has the spine been located, does a cell match the oracle). No
reward/punishment shaping: the threat context is a fixed appraisal, never updated
from experienced outcomes. Integer-native (no non-integer float Lits introduced).
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate_rs import _native                       # noqa: E402
import domains.analogy_search as asr                   # noqa: E402
import domains.disposition as disp                     # noqa: E402
import domains.relation_grounding as rg                # noqa: E402
import domains.trait_modulator_bridge as tmb           # noqa: E402

# ---- FIXED world constants (pre-registered, TRAIT_ANXIETY_INTERPRETATION_PREREG.md §3)
COMPETENCE_FULL = 20      # competence term ceiling
COMPETENCE = 20           # held (competence_epoch stamped => mod_competence no re-add)
COMPETENCE_LO = 30        # anxiety needs competence < competence_lo: 20 < 30 OK
SEC_K = 1                 # securing importance coefficient
DRIVE_WEIGHT = 10         # leading-drive importance
SECURING_HI = 50          # the securing boundary (strict >)

# The fixed threat-context offset K = (competence_full - competence) - sec_k*weight.
K = (COMPETENCE_FULL - COMPETENCE) - SEC_K * DRIVE_WEIGHT      # = -10

# Pre-registered ambiguity bands (exploration_urge levels), well-separated
# around the 50 boundary by >= the full +/-60 personality swing.
AMBIGUITY_BANDS = {"safe": 0, "ambiguous": 60, "threat": 130}

# Skepticism levels swept (trait-anxiety axis), bias = 15*level in [-60,+60].
SKEPTICISM_LEVELS = (-4, -2, 0, 2, 4)

# The anxiety emotion code (tools/build_modulator_seeds.py TEND["anxiety"]).
ANXIETY_CODE = 3
_EMOTION_NAMES = {
    0: "none", 1: "surprise", 2: "fear", 3: "anxiety", 4: "anger",
    5: "frustration", 6: "disgust", 7: "joy", 8: "sadness", 9: "curiosity",
    10: "boredom", 11: "fulfilment", 12: "bliss", 13: "angst", 14: "grief"}

# ModulatorState knob overrides so the fixed threat context holds (the non-
# securing anxiety conjuncts). Only the securing_hi boundary + competence marks
# + sec_k matter for the predicate; the rest inherit the bridge's healthy
# defaults. epoch drives one modulator pass.
_MS_OVER = dict(
    competence=float(COMPETENCE), competence_base=float(COMPETENCE),
    competence_full=float(COMPETENCE_FULL), competence_lo=float(COMPETENCE_LO),
    competence_epoch=-1.0, sec_k=float(SEC_K), securing_hi=float(SECURING_HI),
    epoch=1.0, emotion_epoch=-1.0,
)

# The leading threat Drive override: threat present + PERSISTING (anxiety side of
# the fear<->anxiety minimal pair), negative valence (urge>0 via v_d!=c_d,
# pleasure=displeasure=0 via c_d==c_d_prev), appraised. exploration_urge is set
# per-cell by classify().
_DRIVE_OVER = dict(
    appraised=1.0, weight=float(DRIVE_WEIGHT),
    # negative valence: urge = |v_d - c_d| > 0; c_d == c_d_prev => no pleasure/displeasure
    v_d=100.0, c_d=0.0, c_d_prev=0.0, v_0=0.0,
    learning_progress=0.0,
    # threat channel: precision = Ashr(1024, (now-last)/half) = 1024 >= t_present(256)
    # => drive_threat_persist sets threat_persists = 1 (PERSISTS).
    threat=1.0, threat_c0=1024.0, threat_half_life=8.0,
    threat_now_epoch=1.0, threat_last_refresh=1.0, t_present=256.0,
    exploration_urge=0.0,
)


def skepticism_bias(skep_level):
    """The trait_modulator_bridge SCALE (STEP=15, neutral_ref=0) as pure
    arithmetic -- the same value sync_traits_to_modulator writes to
    ms.skepticism_bias for a crystallised skepticism at `skep_level`."""
    return 15 * int(skep_level)


def securing(exploration_urge, skep_level):
    """The ANALYTIC securing from mod_securing with the fixed §3 constants:
    exploration_urge + (competence_full - competence) - sec_k*weight
    + skepticism_bias = exploration_urge + K + 15*skep_level. Pure arithmetic
    ORACLE (no substrate run) -- used only to CHECK the graph's produced
    ms.securing against the pre-registered prediction."""
    return int(exploration_urge) + K + skepticism_bias(skep_level)


def anxiety_fires(exploration_urge, skep_level):
    """The ANALYTIC anxiety LABEL (True = interpreted as threat) -- emx_anxiety's
    only personality-moved conjunct is securing > securing_hi; the other
    conjuncts are held TRUE by the fixed constants of §3. Strict > mirrors the
    predicate's Gt(securing, securing_hi)."""
    return securing(exploration_urge, skep_level) > SECURING_HI


def _open_productions(s):
    """Admit the productions disposition's CAN Mt / qualia edges need on a bare
    substrate (mirrors tests/test_trait_modulator_bridge._open). The spine edges
    themselves are added via add_edge_unchecked (host wiring, as harlow/doom do);
    this only opens the admissibility grammar for the trait-Concept edges."""
    node_types = ("Agent", "Concept", "Microtheory", "QualiaDimension",
                  "DimensionEdgeRole")
    edge_types = tuple(set(rg.RELATION_EDGE_TYPES) | {
        "has_concept", "genls", "is_a", "built_from", "depends_on", "grounds"})
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                try:
                    s.add_production({
                        "src": {"type": a, "var": "x"}, "edge_type": et,
                        "tgt": {"type": b, "var": "y"}, "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "trait_anxiety:open"})
                except Exception:
                    pass


class TraitAnxietyWorld:
    """ONE agent riding the REAL affect spine. A graded-ambiguity threat STIMULUS
    is ingested by setting the leading drive's exploration_urge; the standing
    trait-anxiety is the seeded SKEPTICISM level (writes ms.skepticism_bias via
    the bridge). The interpretation-as-threat is the graph's produced ms.emotion
    (== anxiety code 3), READ off the graph -- never computed in Python.

    The `.s`/`.agent` shape is exactly what disposition.py and the bridge accept
    (identical to tests/test_trait_modulator_bridge.Agent)."""

    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        _open_productions(self.s)
        # REUSE the established spine builder: EmotionHub + ModulatorState +
        # leading threat Drive + the drives/modulators/affective_state_core seeds.
        # The fixed threat context is set via the ms/drive overrides; run=False so
        # the per-cell exploration_urge + skepticism_bias are set before the tick.
        self.hub, self.ms = tmb.ensure_modulator_state(
            self, ms_over=_MS_OVER, drive_over=_DRIVE_OVER, run=False)
        if self.ms is None:
            raise RuntimeError("could not build/locate the modulator spine")
        self.drive = tmb._leading_drive(tmb.disp._native(self.s), self.ms)
        if self.drive is None:
            raise RuntimeError("could not locate the leading threat drive")

    # ---------------------------------------------------------------- helpers
    def _native(self):
        return tmb.disp._native(self.s)

    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def _set(self, nid, key, value):
        self._native().set_attr(nid, key, float(value))

    # ------------------------------------------------------------- classify
    def classify(self, exploration_urge, skep_level):
        """INGEST a graded-ambiguity stimulus (exploration_urge) at a standing
        trait-anxiety (skep_level), let the graph produce the emotion, and READ
        it back. Mechanical: set attrs -> seed trait -> sync bias -> run_rules ->
        read. Returns {emotion_code, emotion_name, securing, anxiety}.

          1. set the leading drive's exploration_urge (the stimulus ambiguity);
          2. re-assert the fixed threat context + a fresh modulator epoch so the
             region predicates re-classify this cell (idempotent set of the
             pre-registered constants);
          3. seed the SKEPTICISM trait at skep_level (disposition.set_trait_seed);
          4. sync_traits_to_modulator -> writes ms.skepticism_bias from the level
             (this is the ONLY quantity personality moves);
          5. run_rules (the graph produces ms.securing + ms.emotion);
          6. read ms.emotion + ms.securing off the graph."""
        native = self._native()
        # (1) the stimulus: graded ambiguity.
        self._set(self.drive, "exploration_urge", exploration_urge)
        # (2) re-assert the fixed threat context (idempotent) + reopen the
        # per-tick emotion read-off lifecycle so emx_epoch_reset/region predicates
        # re-run for this cell. competence_epoch < epoch would let mod_competence
        # re-add; we hold competence by stamping competence_epoch = epoch.
        for k, v in _DRIVE_OVER.items():
            self._set(self.drive, k, v)
        self._set(self.drive, "exploration_urge", exploration_urge)
        self._set(self.ms, "competence", COMPETENCE)
        self._set(self.ms, "competence_epoch", _MS_OVER["epoch"])
        self._set(self.ms, "emotion_epoch", -1.0)
        # (3) the standing trait-anxiety.
        disp.set_trait_seed(self, "skepticism", float(skep_level))
        # (4) write ms.skepticism_bias from the crystallised level (run=False:
        # we tick once ourselves below after the context is fully asserted).
        tmb.sync_traits_to_modulator(self, run=False)
        # (5) the graph produces securing + the emotion label.
        native.run_rules()
        # (6) READ the produced state off the graph.
        a = self._attrs(self.ms)
        code = int(a.get("emotion") or 0)
        sec = int(a.get("securing") or 0)
        return dict(emotion_code=code,
                    emotion_name=_EMOTION_NAMES.get(code, str(code)),
                    securing=sec, anxiety=(code == ANXIETY_CODE))

    def grid(self, *, bands=None, skep_levels=None):
        """The full trait x ambiguity grid: {band_name: {skep_level: classify}}.
        Mechanical sweep over the pre-registered bands x skepticism levels."""
        bands = bands or AMBIGUITY_BANDS
        skep_levels = skep_levels or SKEPTICISM_LEVELS
        out = {}
        for band, eu in bands.items():
            out[band] = {lvl: self.classify(eu, lvl) for lvl in skep_levels}
        return out

    def skepticism_bias_read(self):
        """READ the ms.skepticism_bias the bridge last wrote (glass-box)."""
        return int(self._attrs(self.ms).get("skepticism_bias") or 0)
