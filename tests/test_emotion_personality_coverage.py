"""EMERGENT-EMOTION COVERAGE gate — distinct PERSONALITIES produce distinct
emergent-emotion LABELS across MORE of the emx_* space, on well-constructed
events, WITHOUT breaking default==today and WITHOUT injecting any emotion.

This deepens the two-gate payoff (scripts/qualia_personality_emotion_demo.py) to
a coverage sweep (scripts/qualia_personality_emotion_coverage_demo.py). The trait
vector biases the MicroPsi modulator SET-POINTS via the REAL bridge scale
(domains/trait_modulator_bridge.trait_bias); the emergent emotion is read off the
SAME modulator vector by the emx_* REGION rules in seeds/modulators.json. Every
label asserted here is `ms.emotion` PRODUCED by the graph geometry — the test
reads it back through scripts.modulator_emergence_measure._case; nothing is
hand-set (no test writes a hit_*/emotion/action_tendency attr).

Pins:
  * LABEL SPLITS — on each constructed event, a full-scale trait deviation
    produces a DIFFERENT emx_* label from the default (anger, bliss, sadness,
    anxiety), the split crossing the trait's own modulator boundary.
  * DEFAULT == TODAY — the seeded-default trait vector (openness -1, abstraction
    0, skepticism 0) reproduces, byte-for-byte, the label a BARE ModulatorState
    (bias attrs at their 0 seed default, no bridge) produces on the same event.
  * DIRECTEDNESS is an EVENT appraisal — sadness<->grief is split by the event's
    loss_object flag, NOT by any trait.
  * UNREACHABLE-BY-DESIGN — the honest SHAPE of the coupling: an appraisal wall
    (goal_blocked) keeps the positive/loss regions off a blocked-goal event for
    ANY trait; skepticism shifts the felt securing VECTOR but crosses no LABEL on
    a positive/loss event (no threat appraisal); the bounded openness bias cannot
    cross the standard anger sel_threshold (only the near-boundary event is
    crossable). These are asserted as unreachable to document the shape.

The emx region DEFINITIONS are NOT touched — widening is by EVENTS + the existing
bridge scale only. The canonical byte-identity guards (test_modulator_emergence_
migrated, test_core_emotions_migrated, test_doom_emotion_narration_migrated) stay
green alongside this file.
"""
import importlib

import pytest

D = importlib.import_module("scripts.qualia_personality_emotion_coverage_demo")


# ---- trait vectors: the default and the full-scale deviations under test ----
DEFAULT = D.DEFAULT_VECTOR
CONCRETE = {"openness": -1, "abstraction": -4, "skepticism": 0}
ABSTRACT = {"openness": -1, "abstraction": 4, "skepticism": 0}
OPEN = {"openness": 4, "abstraction": 0, "skepticism": 0}
CLOSED = {"openness": -4, "abstraction": 0, "skepticism": 0}
SKEPTIC = {"openness": -1, "abstraction": 0, "skepticism": 4}


def _label(vector, event, ms_extra=None):
    """The graph-PRODUCED emx_* label for `vector` on `event` — read off
    ms.emotion via the established harness, nothing injected."""
    return D.run_event(vector, event, ms_extra)["emotion"]


# =========================================================================== #
# DEFAULT == TODAY — on every constructed event the default vector reproduces
# the bare (no-bias) ModulatorState's produced label, byte for byte.
# =========================================================================== #
@pytest.mark.parametrize("name,event,ms_extra", [
    ("bliss", D.EV_BLISS, None),
    ("sadness", D.EV_SADNESS, None),
    ("grief", D.EV_GRIEF, None),
    ("open_anger", D.EV_OPEN_ANGER, D.MS_OPEN_ANGER),
    ("anger", D.EV_ANGER, D.MS_ANGER),
    ("anxiety", D.EV_ANXIETY, D.MS_ANXIETY),
])
def test_default_vector_reproduces_today(name, event, ms_extra):
    """The default temperament maps to 0 bias on all three axes, so its produced
    emotion equals a bare ModulatorState's (default == today)."""
    r = D.run_event(DEFAULT, event, ms_extra)
    bare_code, bare_name = D.bare_label(event, ms_extra)
    assert r["emotion_code"] == bare_code, (name, r["emotion"], bare_name)
    # and all three bias offsets are exactly 0 at default.
    assert r["biases"] == {"abstraction_bias": 0, "openness_bias": 0,
                           "skepticism_bias": 0}


# =========================================================================== #
# LABEL SPLITS — distinct trait vectors => distinct produced labels.
# =========================================================================== #
def test_abstraction_splits_bliss_on_positive_event():
    """Positive low-arousal event: concrete abstraction sits below the bliss
    resolution floor (dull neutral); default/abstract reach BLISS. The label
    differs by personality on the identical event."""
    concrete = _label(CONCRETE, D.EV_BLISS)
    default = _label(DEFAULT, D.EV_BLISS)
    abstract = _label(ABSTRACT, D.EV_BLISS)
    assert default == "bliss"
    assert abstract == "bliss"
    assert concrete != "bliss"          # dropped below resolution_hi
    assert concrete != default          # distinct LABELS, same event


def test_abstraction_splits_sadness_on_loss_event():
    """Loss event (value falling): concrete drops below the resolution floor to
    neutral; default/abstract reach SADNESS. Same resolution_hi boundary as
    bliss, negative valence flips the region to sadness."""
    concrete = _label(CONCRETE, D.EV_SADNESS)
    default = _label(DEFAULT, D.EV_SADNESS)
    abstract = _label(ABSTRACT, D.EV_SADNESS)
    assert default == "sadness"
    assert abstract == "sadness"
    assert concrete != "sadness"
    assert concrete != default


def test_openness_splits_anger_on_near_boundary_event():
    """NEW gate: a near-boundary blocked-goal event whose neutral sel_threshold
    sits just above the mark. A very-open agent lowers it below => the anger
    label leaves; closed/default stay ANGER."""
    default = _label(DEFAULT, D.EV_OPEN_ANGER, D.MS_OPEN_ANGER)
    closed = _label(CLOSED, D.EV_OPEN_ANGER, D.MS_OPEN_ANGER)
    openv = _label(OPEN, D.EV_OPEN_ANGER, D.MS_OPEN_ANGER)
    assert default == "anger"
    assert closed == "anger"
    assert openv != "anger"             # crossed sel_threshold_hi downward
    assert openv != default


def test_abstraction_splits_anger_on_adversity_event():
    """Carried-over gate: a blocked-goal adversity event with neutral resolution
    just below resolution_lo. Low-abstraction fires ANGER; high-abstraction lifts
    resolution out of the anger region."""
    default = _label(DEFAULT, D.EV_ANGER, D.MS_ANGER)
    high = _label(ABSTRACT, D.EV_ANGER, D.MS_ANGER)
    assert default == "anger"
    assert high != "anger"
    assert high != default


def test_skepticism_splits_anxiety_on_threat_event():
    """Carried-over gate: a persistent-threat event with neutral securing just
    below the vigilance mark. Neutral skepticism fires nothing; high skepticism
    crosses securing_hi into ANXIETY."""
    default = _label(DEFAULT, D.EV_ANXIETY, D.MS_ANXIETY)
    skeptic = _label(SKEPTIC, D.EV_ANXIETY, D.MS_ANXIETY)
    assert default != "anxiety"         # default == today == neutral here
    assert skeptic == "anxiety"
    assert skeptic != default


# =========================================================================== #
# DIRECTEDNESS is an EVENT appraisal — sadness<->grief split by loss_object,
# NOT by any trait (the same default vector on both).
# =========================================================================== #
def test_loss_object_splits_sadness_into_grief_at_event_level():
    sad = _label(DEFAULT, D.EV_SADNESS)
    grief = _label(DEFAULT, D.EV_GRIEF)
    assert sad == "sadness"
    assert grief == "grief"
    assert sad != grief                 # event flag, not a trait


# =========================================================================== #
# UNREACHABLE-BY-DESIGN — the true SHAPE of the coupling (asserted as walls).
# =========================================================================== #
def test_wall_positive_and_loss_regions_unreachable_on_blocked_goal_event():
    """No abstraction value reaches bliss/joy/sadness on the blocked-goal (anger)
    event — the goal_blocked flag walls those regions off. Personality bends
    emotion WITHIN the event's appraisal; it cannot teleport across it."""
    reached = set()
    for ab in (-4, -2, 0, 2, 4):
        reached.add(_label({"openness": -1, "abstraction": ab, "skepticism": 0},
                           D.EV_ANGER, D.MS_ANGER))
    assert "bliss" not in reached
    assert "joy" not in reached
    assert "sadness" not in reached
    # the event only ever lands in anger or the deliberative fall-through.
    assert reached <= {"anger", "(none/deliberative)"}


def test_wall_skepticism_shifts_vector_but_not_label_on_positive_event():
    """Skepticism (-> securing) is inert on the LABEL of a positive/loss event:
    only anxiety/angst read securing and both need a threat / undirected-anxiety
    appraisal a positive event lacks. The felt securing VECTOR still shifts —
    gap (1) stated precisely."""
    lo = D.run_event({"openness": -1, "abstraction": 0, "skepticism": 0},
                     D.EV_BLISS)
    hi = D.run_event({"openness": -1, "abstraction": 0, "skepticism": 4},
                     D.EV_BLISS)
    assert lo["securing"] != hi["securing"]     # the VECTOR moved
    assert lo["emotion"] == hi["emotion"]       # the LABEL held
    assert lo["emotion"] == "bliss"


def test_wall_openness_cannot_cross_standard_anger_sel_threshold():
    """The +/-125 openness bias is a real ceiling: on the STANDARD anger event
    (GATE D1) sel_threshold ~783, far above the 200 mark, so full-scale openness
    cannot flip the label there — only the near-boundary event (GATE C) is
    crossable. We do NOT inflate the step to force a flip."""
    default = D.run_event(DEFAULT, D.EV_ANGER, D.MS_ANGER)
    openv = D.run_event(OPEN, D.EV_ANGER, D.MS_ANGER)
    assert default["sel_threshold"] > 200
    assert openv["sel_threshold"] > 200         # still above the mark
    assert openv["emotion"] == "anger"          # label unchanged there
    # the bias DID move the vector, just not across the boundary on this event.
    assert openv["sel_threshold"] < default["sel_threshold"]


# =========================================================================== #
# The demo's own end-to-end verdict (every gate + walls + safe-default).
# =========================================================================== #
def test_coverage_demo_all_gates_pass():
    assert D.main() is True
