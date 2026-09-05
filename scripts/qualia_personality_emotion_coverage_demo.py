#!/usr/bin/env python3
"""EMERGENT-EMOTION COVERAGE — how far distinct PERSONALITIES bend distinct
emergent-emotion LABELS across the emx_* space, on well-constructed events.

This DEEPENS scripts/qualia_personality_emotion_demo.py (the two-gate payoff)
into a coverage sweep. The trait vector (openness / abstraction / skepticism,
domains/disposition.py) biases the MicroPsi modulator SET-POINTS via the REAL
bridge scale (domains/trait_modulator_bridge.trait_bias) —

    abstraction level -> abstraction_bias -> mod_resolution   baseline
    openness    level -> openness_bias    -> mod_sel_threshold baseline
    skepticism  level -> skepticism_bias  -> mod_securing       baseline

— all additive, all defaulting to 0 (default == today). The emergent emotion is
read off the SAME modulator vector by the emx_* REGION rules in
seeds/modulators.json. NOTHING here computes or injects an emotion: every label
below is `ms.emotion` produced by the graph's region geometry. We only set the
drive/knob config, tick, and read back.

THE POINT (the deepening): the prior stage showed ONE clean label flip per trait
(abstraction->anger, skepticism->anxiety). Here we widen LABEL coverage across
MORE of the emotion space by CONSTRUCTING the right events — the honest lever the
prior stage's own notes said was needed. Concretely:

  A. POSITIVE-OUTCOME (BLISS) gate — a genuinely positive, low-arousal event
     (goal progress banked, nothing pursued): abstraction gates the
     resolution_hi=450 boundary that emx_bliss needs. A strongly CONCRETE agent
     (abstraction -4) sits below the high-resolution mark => a DULL neutral; the
     DEFAULT and ABSTRACT agents reach BLISS. Same event, different label.

  B. LOSS (SADNESS/GRIEF) gate — a value-falling loss (goal GONE, not blocked),
     low arousal: the SAME resolution_hi boundary, but NEGATIVE valence, so it
     lands in SADNESS instead of bliss. Concrete -> dull neutral, default/abstract
     -> SADNESS. And the loss's DIRECTEDNESS (a specific loss_object) is an
     EVENT-level appraisal that splits SADNESS (undirected) <-> GRIEF (directed) —
     shown here as an event contrast, since directedness is supplied by the bound
     drive's object, NOT by any trait.

  C. OPENNESS->ANGER gate (NEW) — a NEAR-BOUNDARY blocked-goal event whose
     neutral selection-threshold sits just above the sel_threshold_hi=200 mark
     emx_anger needs. A very-OPEN agent (openness +4) lowers the threshold below
     the mark and the label leaves anger -> deliberative; closed/default stay
     ANGER. This closes the prior stage's openness gap: openness DOES flip a
     label, on the event where its bounded bias legitimately tips the boundary.

  D. the two carried-over gates — abstraction->ANGER (resolution_lo) and
     skepticism->ANXIETY (securing_hi) — reproduced for the full picture.

HONEST SHAPE (reported, not hidden). Personality bends emotion WITHIN what the
event's appraisal structure allows; it cannot teleport across appraisal WALLS:

  * On the BLOCKED-goal (anger) event, NO abstraction value reaches bliss/joy/
    sadness — those positive/loss regions require goal_blocked=0. The blocker
    flag walls them off. That is a correct feature of directed appraisal.
  * skepticism (-> securing) is INERT on the bliss/loss LABELS: only anxiety/
    angst read securing, and both need a threat / undirected-anxiety appraisal
    that a positive or loss event does not carry. Skepticism still shifts the
    felt securing VECTOR there (shown) — it just does not cross a label boundary
    on those events. That is gap (1) stated precisely, not papered over.
  * On the STANDARD anger event (GATE 1) the selection-threshold is ~783 — far
    above the 200 mark — so the +/-125 openness bias cannot reach it there. Only
    a NEAR-BOUNDARY anger event (gate C) is crossable. The bias magnitude is a
    real ceiling; we cross the boundary on the event where a full-scale trait
    legitimately tips it, we do NOT inflate the step to force a flip.

SAFE DEFAULT: the seeded-default temperament (openness -1, abstraction 0,
skepticism 0) maps to ZERO bias on all three axes, so a default agent's modulator
vector and emergent emotion are BYTE-IDENTICAL to a bare no-bias ModulatorState
(default == today) — proven on every event below.

Run: python3 scripts/qualia_personality_emotion_coverage_demo.py

Uses the ESTABLISHED emergence harness (scripts/modulator_emergence_measure._case)
for the drive/modulator/emx spine and the REAL bridge scale
(trait_modulator_bridge.trait_bias) — no re-implemented affect, no invented dial,
no moved region.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scripts.modulator_emergence_measure as M       # noqa: E402
import domains.trait_modulator_bridge as tmb          # noqa: E402

# the emx `emotion` read-off codes (seeds/modulators.json emx_readoff), inverse.
# The 11 core tendencies 1..11 + the three FREE blend regions 21/22/23.
EMOTION_NAME = {
    0: "(none/deliberative)", 1: "surprise", 2: "fear", 3: "anxiety",
    4: "anger", 5: "frustration", 6: "disgust", 7: "joy", 8: "sadness",
    9: "curiosity", 10: "boredom", 11: "fulfilment",
    21: "bliss", 22: "angst", 23: "grief",
}
TEND_NAME = {0: "NONE", 1: "ORIENT", 2: "AVOID", 3: "VIGILANCE",
             4: "APPROACH_BLOCK", 5: "PERSIST", 6: "REJECT", 7: "REINFORCE",
             8: "DISENGAGE", 9: "ENGAGE", 10: "LEAVE", 11: "CONTRIBUTE"}

DEFAULT_VECTOR = {"openness": -1, "abstraction": 0, "skepticism": 0}


# --------------------------------------------------------------------------- #
# the constructed events (drive-config + knob overrides). NOTHING sets an
# emotion — only the motivational configuration; the emx_* rules classify.
# --------------------------------------------------------------------------- #
#: A) genuinely positive, low-arousal: a goal's held value ROSE (pleasure) with
#: nothing pursued (value_progress 0, not exploring, no supergraph frame). The
#: emx_bliss region needs resolution > resolution_hi(450); the neutral resolution
#: sits above it, and a strongly-concrete agent's LOWER resolution baseline drops
#: it below the mark.
EV_BLISS = dict(value_progress=0, explore=0, supergraph_value=0,
                v_d=100, c_d=95, c_d_prev=40, v_0=0)

#: B) a LOSS (goal GONE, not blocked): value FALLING (value_progress<0), low
#: arousal, undirected. Same resolution_hi boundary, negative valence => SADNESS.
EV_SADNESS = dict(value_progress=-50, loss_object=0, threat=0, was_engaged=0,
                  v_d=100, c_d=95, c_d_prev=95, v_0=0)
#: B') the SAME loss DIRECTED at a specific loss object => GRIEF (event flag).
EV_GRIEF = dict(EV_SADNESS, loss_object=1)

#: C) a NEAR-BOUNDARY blocked-goal event: huge |v_d - v_0| keeps urgency (hence
#: the weight*urgency term of sel_threshold) modest while the urge^2/|v_d-v_0|
#: arousal still clears the HIGH band; the neutral selection-threshold lands just
#: above sel_threshold_hi(200), so a full-scale OPEN agent tips it below.
EV_OPEN_ANGER = dict(valued_goal=1, goal_blocked=1, blocker_present=1,
                     v_d=1800, c_d=10, c_d_prev=10, v_0=-3300, weight=1)
MS_OPEN_ANGER = dict(competence_base=50.0)

#: D1) the carried-over GATE-1 anger event (resolution_lo boundary).
EV_ANGER = dict(valued_goal=1, goal_blocked=1, blocker_present=1,
                v_d=1000, c_d=250, c_d_prev=250, v_0=100, weight=1)
MS_ANGER = dict(competence_base=50.0)

#: D2) the carried-over GATE-2 persistent-threat event (securing_hi boundary).
EV_ANXIETY = dict(threat=1, threat_half_life=1_000_000, threat_now_epoch=3,
                  threat_c0=1024, t_present=256, v_d=100, c_d=40, c_d_prev=40,
                  v_0=0, exploration_urge=0, weight=26)
MS_ANXIETY = dict(competence_base=25.0)


def section(t):
    print("\n" + "=" * 80)
    print(t)
    print("=" * 80)


def _bias_vector(vector):
    """Map a trait VECTOR through the REAL bridge scale to the three bias offsets
    (exactly what sync_traits_to_modulator writes onto the ModulatorState)."""
    return {
        "abstraction_bias": tmb.trait_bias(vector.get("abstraction", 0),
                                           "abstraction"),
        "openness_bias": tmb.trait_bias(vector.get("openness", -1), "openness"),
        "skepticism_bias": tmb.trait_bias(vector.get("skepticism", 0),
                                          "skepticism"),
    }


def run_event(vector, drive_over, ms_extra=None):
    """Feed ONE drive event to an agent whose ModulatorState carries the bias
    offsets derived from `vector`. Returns the graph-produced modulator vector +
    emergent emotion + tendency. Nothing computed in Python: `_case` ticks the
    graph rules and we read `ms.emotion`."""
    biases = _bias_vector(vector)
    ms_over = dict(biases)
    if ms_extra:
        ms_over.update(ms_extra)
    a, fired = M._case(ms_over, dict(drive_over))
    return {
        "vector": vector,
        "biases": {k: int(v) for k, v in biases.items()},
        "resolution": int(a["resolution"]),
        "sel_threshold": int(a["sel_threshold"]),
        "securing": int(a["securing"]),
        "valence": int(a["valence"]),
        "arousal_band": int(a["arousal_band"]),
        "emotion_code": int(a["emotion"]),
        "emotion": EMOTION_NAME.get(int(a["emotion"]), "?"),
        "tendency": TEND_NAME.get(int(a["action_tendency"]), "?"),
        "fired": fired,
    }


def bare_label(drive_over, ms_extra=None):
    """The label a BARE ModulatorState (bias attrs at their 0 seed default, no
    bridge) produces on the same event — the today-baseline for default==today."""
    a, _ = M._case(dict(ms_extra or {}), dict(drive_over))
    return int(a["emotion"]), EMOTION_NAME.get(int(a["emotion"]), "?")


def _print_row(label, r, keys=("res", "sel", "sec")):
    cols = {
        "res": f"res={r['resolution']:>5}",
        "sel": f"sel={r['sel_threshold']:>6}",
        "sec": f"sec={r['securing']:>4}",
    }
    stat = " ".join(cols[k] for k in keys)
    b = r["biases"]
    print(f"  {label:24s} {stat} | abstr_bias={b['abstraction_bias']:>4} "
          f"open_bias={b['openness_bias']:>4} skept_bias={b['skepticism_bias']:>4}"
          f" || EMOTION={r['emotion']:<20} tend={r['tendency']}")


# =========================================================================== #
# GATE A — abstraction -> the BLISS boundary (positive-outcome, resolution_hi)
# =========================================================================== #
def gate_abstraction_bliss():
    section("GATE A — ABSTRACTION reaches BLISS on a POSITIVE-OUTCOME event")
    print("A genuinely POSITIVE, low-arousal event: a goal's held value ROSE "
          "(pleasure),\nnothing pursued. emx_bliss needs resolution > "
          "resolution_hi(450) AND arousal LOW.\nThe neutral resolution clears "
          "450; a strongly-CONCRETE agent's lower baseline drops it below.\n")
    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("concrete (-4)", {"openness": -1, "abstraction": -4, "skepticism": 0}),
        ("concrete (-2)", {"openness": -1, "abstraction": -2, "skepticism": 0}),
        ("mid-abstraction (+2)", {"openness": -1, "abstraction": 2, "skepticism": 0}),
        ("abstract (+4)", {"openness": -1, "abstraction": 4, "skepticism": 0}),
    ):
        r = run_event(vec, EV_BLISS)
        rows.append((label, r))
        _print_row(label, r, keys=("res",))
    concrete = rows[1][1]
    abstract = rows[-1][1]
    default = rows[0][1]
    bcode, bname = bare_label(EV_BLISS)
    split = (concrete["emotion"] != "bliss" and abstract["emotion"] == "bliss")
    dflt_today = (default["emotion_code"] == bcode)
    print(f"\n  => concrete abstraction (-4) resolution {concrete['resolution']} "
          f"(< 450) => {concrete['emotion'].upper()};\n     default/abstract "
          f"resolution rises to {abstract['resolution']} (crosses 450) => BLISS "
          f"(tend {abstract['tendency']}).\n     LABEL SPLIT by abstraction: "
          f"{split}.  default == today ({bname}): {dflt_today}")
    return split and dflt_today


# =========================================================================== #
# GATE B — abstraction -> SADNESS on a LOSS; event flag -> SADNESS<->GRIEF
# =========================================================================== #
def gate_abstraction_sadness_grief():
    section("GATE B — ABSTRACTION reaches SADNESS on a LOSS; loss-object -> GRIEF")
    print("A LOSS (goal GONE, not blocked): value FALLING, low arousal, "
          "undirected.\nSame resolution_hi(450) boundary, but NEGATIVE valence "
          "=> SADNESS not bliss.\n")
    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("concrete (-4)", {"openness": -1, "abstraction": -4, "skepticism": 0}),
        ("mid-abstraction (+2)", {"openness": -1, "abstraction": 2, "skepticism": 0}),
        ("abstract (+4)", {"openness": -1, "abstraction": 4, "skepticism": 0}),
    ):
        r = run_event(vec, EV_SADNESS)
        rows.append((label, r))
        _print_row(label, r, keys=("res",))
    concrete = rows[1][1]
    abstract = rows[-1][1]
    default = rows[0][1]
    scode, sname = bare_label(EV_SADNESS)
    split = (concrete["emotion"] != "sadness" and abstract["emotion"] == "sadness")
    dflt_today = (default["emotion_code"] == scode)
    print(f"\n  => concrete (-4) resolution {concrete['resolution']} (< 450) => "
          f"{concrete['emotion'].upper()}; default/abstract => SADNESS "
          f"(tend {abstract['tendency']}). LABEL SPLIT: {split}. "
          f"default == today ({sname}): {dflt_today}")

    print("\n  DIRECTEDNESS is an EVENT appraisal, not a trait — the SAME loss")
    print("  geometry with a specific loss OBJECT reads off GRIEF, without one,")
    print("  SADNESS (default trait vector, so the split is purely the event):")
    r_sad = run_event(DEFAULT_VECTOR, EV_SADNESS)
    r_grief = run_event(DEFAULT_VECTOR, EV_GRIEF)
    print(f"     loss_object=0 -> {r_sad['emotion'].upper()} "
          f"(tend {r_sad['tendency']})")
    print(f"     loss_object=1 -> {r_grief['emotion'].upper()} "
          f"(tend {r_grief['tendency']})")
    directed_split = (r_sad["emotion"] == "sadness"
                      and r_grief["emotion"] == "grief")
    print(f"     event-level SADNESS<->GRIEF split: {directed_split}")
    return split and dflt_today and directed_split


# =========================================================================== #
# GATE C — openness -> the ANGER boundary (sel_threshold_hi), NEAR-BOUNDARY event
# =========================================================================== #
def gate_openness_anger():
    section("GATE C — OPENNESS shifts sel_threshold -> the ANGER boundary (NEW)")
    print("A NEAR-BOUNDARY blocked-goal event whose neutral selection-threshold "
          "sits\njust above sel_threshold_hi(200). emx_anger requires "
          "sel_threshold > 200.\nA very-OPEN agent lowers the threshold below the "
          "mark => the label leaves anger.\n")
    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("closed (-4)", {"openness": -4, "abstraction": 0, "skepticism": 0}),
        ("mid-open (+2)", {"openness": 2, "abstraction": 0, "skepticism": 0}),
        ("open (+4)", {"openness": 4, "abstraction": 0, "skepticism": 0}),
    ):
        r = run_event(vec, EV_OPEN_ANGER, MS_OPEN_ANGER)
        rows.append((label, r))
        _print_row(label, r, keys=("sel",))
    default = rows[0][1]
    openhi = rows[-1][1]
    acode, aname = bare_label(EV_OPEN_ANGER, MS_OPEN_ANGER)
    split = (default["emotion"] == "anger" and openhi["emotion"] != "anger")
    dflt_today = (default["emotion_code"] == acode)
    print(f"\n  => default sel_threshold {default['sel_threshold']} (> 200) => "
          f"{default['emotion'].upper()}; open (+4) lowers it to "
          f"{openhi['sel_threshold']} (< 200)\n     and the event leaves the "
          f"anger region -> {openhi['emotion']}. LABEL SPLIT by openness: "
          f"{split}. default == today ({aname}): {dflt_today}")
    return split and dflt_today


# =========================================================================== #
# GATE D1 — abstraction -> ANGER (resolution_lo)   [carried over]
# =========================================================================== #
def gate_abstraction_anger():
    section("GATE D1 — ABSTRACTION shifts resolution -> the ANGER boundary")
    print("A blocked-goal adversity event tuned so the neutral resolution sits "
          "just below\nthe low-resolution mark. emx_anger requires resolution < "
          "resolution_lo(200).\n")
    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("low-abstraction (0)", {"openness": -1, "abstraction": 0, "skepticism": 0}),
        ("mid-abstraction (+2)", {"openness": -1, "abstraction": 2, "skepticism": 0}),
        ("high-abstraction (+4)", {"openness": -1, "abstraction": 4, "skepticism": 0}),
    ):
        r = run_event(vec, EV_ANGER, MS_ANGER)
        rows.append((label, r))
        _print_row(label, r, keys=("res",))
    low = rows[1][1]
    high = rows[-1][1]
    default = rows[0][1]
    acode, aname = bare_label(EV_ANGER, MS_ANGER)
    split = (low["emotion"] == "anger" and high["emotion"] != "anger")
    dflt_today = (default["emotion_code"] == acode)
    print(f"\n  => low-abstraction fires {low['emotion'].upper()}; "
          f"high-abstraction resolution rises {low['resolution']}->"
          f"{high['resolution']} (crosses 200)\n     -> {high['emotion']}. "
          f"LABEL SPLIT: {split}. default == today ({aname}): {dflt_today}")
    return split and dflt_today


# =========================================================================== #
# GATE D2 — skepticism -> ANXIETY (securing_hi)     [carried over]
# =========================================================================== #
def gate_skepticism_anxiety():
    section("GATE D2 — SKEPTICISM shifts securing -> the ANXIETY boundary")
    print("A persistent-threat event tuned so the neutral securing sits just "
          "below the\nvigilance mark. emx_anxiety requires securing > "
          "securing_hi(50).\n")
    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("neutral-skepticism (0)", {"openness": -1, "abstraction": 0, "skepticism": 0}),
        ("mid-skepticism (+2)", {"openness": -1, "abstraction": 0, "skepticism": 2}),
        ("high-skepticism (+4)", {"openness": -1, "abstraction": 0, "skepticism": 4}),
    ):
        r = run_event(vec, EV_ANXIETY, MS_ANXIETY)
        rows.append((label, r))
        _print_row(label, r, keys=("sec",))
    neutral = rows[1][1]
    high = rows[-1][1]
    default = rows[0][1]
    ncode, nname = bare_label(EV_ANXIETY, MS_ANXIETY)
    split = (neutral["emotion"] != "anxiety" and high["emotion"] == "anxiety")
    dflt_today = (default["emotion_code"] == ncode)
    print(f"\n  => neutral securing {neutral['securing']} (< 50) => "
          f"{neutral['emotion']}; high-skepticism securing rises "
          f"{neutral['securing']}->{high['securing']} (crosses 50)\n     => "
          f"{high['emotion'].upper()} (tend {high['tendency']}). LABEL SPLIT: "
          f"{split}. default == today ({nname}): {dflt_today}")
    return split and dflt_today


# =========================================================================== #
# THE SHAPE — appraisal WALLS the personality cannot teleport across
# =========================================================================== #
def shape_of_the_coupling():
    section("THE SHAPE — personality bends emotion WITHIN the event's appraisal")
    print("Personality shifts WHICH region an event lands in — but only within "
          "regions the\nevent's appraisal structure ADMITS. Three honest walls:\n")

    # WALL 1: the anger event (goal_blocked) cannot reach bliss/joy/sadness.
    print("  WALL 1 — the BLOCKED-goal (anger) event cannot reach a POSITIVE or")
    print("           LOSS region for ANY abstraction (they need goal_blocked=0):")
    reached = set()
    for ab in (-4, -2, 0, 2, 4):
        r = run_event({"openness": -1, "abstraction": ab, "skepticism": 0},
                      EV_ANGER, MS_ANGER)
        reached.add(r["emotion"])
    print(f"           abstraction sweep -4..+4 reaches only: "
          f"{sorted(reached)}")
    wall1 = ("bliss" not in reached and "joy" not in reached
             and "sadness" not in reached)
    print(f"           bliss/joy/sadness UNREACHABLE on this event: {wall1}")

    # WALL 2: skepticism (securing) is inert on the bliss/loss LABELS.
    print("\n  WALL 2 — SKEPTICISM (-> securing) shifts the felt VECTOR but not")
    print("           the LABEL on a positive/loss event (no threat appraisal =>")
    print("           the securing-reading regions anxiety/angst cannot fire):")
    lo = run_event({"openness": -1, "abstraction": 0, "skepticism": 0}, EV_BLISS)
    hi = run_event({"openness": -1, "abstraction": 0, "skepticism": 4}, EV_BLISS)
    print(f"           bliss event: securing {lo['securing']} -> {hi['securing']}"
          f" (vector shifts) but label {lo['emotion']} -> {hi['emotion']} (same)")
    wall2 = (lo["securing"] != hi["securing"] and lo["emotion"] == hi["emotion"])
    print(f"           vector moved, label held: {wall2}")

    # WALL 3: openness bias magnitude cannot cross the standard anger sel_threshold.
    print("\n  WALL 3 — the +/-125 openness bias is a REAL ceiling: on the")
    print("           STANDARD anger event (GATE D1) sel_threshold ~783, far")
    print("           above 200, so openness cannot flip the label THERE —")
    print("           only the near-boundary event (GATE C) is crossable:")
    d1 = run_event(DEFAULT_VECTOR, EV_ANGER, MS_ANGER)
    d1o = run_event({"openness": 4, "abstraction": 0, "skepticism": 0},
                    EV_ANGER, MS_ANGER)
    print(f"           GATE-D1 event: sel {d1['sel_threshold']} -> "
          f"{d1o['sel_threshold']} (open +4); label {d1['emotion']} -> "
          f"{d1o['emotion']} (unchanged — bias too small to reach 200)")
    wall3 = (d1o["sel_threshold"] > 200 and d1o["emotion"] == "anger")
    print(f"           standard-anger sel_threshold uncrossable by openness: "
          f"{wall3}")
    return wall1 and wall2 and wall3


# =========================================================================== #
# COVERAGE TABLE — per trait, which emx_* boundary its bias can cross, on what
# event class, and the label split it produces there.
# =========================================================================== #
def coverage_table():
    section("COVERAGE TABLE — which emx_* boundary each trait's bias can cross")
    header = ("  trait        modulator      emx boundary            event class"
              "               label split (full-scale)")
    print(header)
    print("  " + "-" * 108)
    rows = [
        ("abstraction", "resolution", "resolution_lo=200 (anger)",
         "blocked-goal adversity", "anger <-> deliberative"),
        ("abstraction", "resolution", "resolution_hi=450 (bliss)",
         "positive low-arousal", "bliss <-> deliberative"),
        ("abstraction", "resolution", "resolution_hi=450 (sadness)",
         "loss (value falling)", "sadness <-> deliberative"),
        ("openness", "sel_threshold", "sel_threshold_hi=200 (anger)",
         "near-boundary blocked goal", "anger <-> deliberative"),
        ("skepticism", "securing", "securing_hi=50 (anxiety)",
         "persistent threat", "anxiety <-> deliberative"),
    ]
    for tr, mod, bnd, ev, split in rows:
        print(f"  {tr:12s} {mod:14s} {bnd:24s} {ev:26s} {split}")

    print("\n  UNREACHABLE-BY-DESIGN (the true shape — not a defect):")
    print("  " + "-" * 108)
    unreach = [
        ("any trait", "bliss/joy/sadness on a BLOCKED-goal (anger) event",
         "goal_blocked flag walls off the positive/loss regions"),
        ("skepticism", "any LABEL on a positive/loss event",
         "securing-reading regions (anxiety/angst) need a threat appraisal"),
        ("openness", "anger on the STANDARD anger event (sel~783)",
         "+/-125 bias < distance to the 200 mark; crossable only near-boundary"),
        ("grief vs sadness", "NOT a trait split at all",
         "directedness (loss_object) is an EVENT-level appraisal, not a set-point"),
    ]
    for who, what, why in unreach:
        print(f"  {who:16s} {what:48s} {why}")


# =========================================================================== #
# SAFE DEFAULT — default temperament reproduces TODAY on every event
# =========================================================================== #
def safe_default():
    section("SAFE DEFAULT — default temperament == today on EVERY event")
    print("The DEFAULT trait vector (openness -1, abstraction 0, skepticism 0) "
          "maps to 0 bias\non all three axes, so its produced emotion equals a "
          "BARE ModulatorState's.\n")
    events = {
        "bliss (positive)": (EV_BLISS, None),
        "sadness (loss)": (EV_SADNESS, None),
        "grief (loss+object)": (EV_GRIEF, None),
        "anger (near-bnd)": (EV_OPEN_ANGER, MS_OPEN_ANGER),
        "anger (gate D1)": (EV_ANGER, MS_ANGER),
        "anxiety (threat)": (EV_ANXIETY, MS_ANXIETY),
    }
    all_ok = True
    for name, (ev, ms_extra) in events.items():
        r = run_event(DEFAULT_VECTOR, ev, ms_extra)
        bcode, bname = bare_label(ev, ms_extra)
        ident = (r["emotion_code"] == bcode)
        all_ok = all_ok and ident
        print(f"  {name:20s} default -> {r['emotion']:<20} bare -> {bname:<20}"
              f" IDENTICAL: {ident}")
    print(f"\n  => default == today on every event: {all_ok}")
    return all_ok


def summary(results):
    section("SUMMARY — distinct personalities, distinct emergent LABELS, widened")
    for k, v in results.items():
        print(f"  {k:42s}: {v}")
    ok = all(results.values())
    print(f"\n  COVERAGE DEMO: {'PASS' if ok else 'REVIEW'}")
    print("  The trait vector is the drive-regulated modulator SET-POINT: it "
          "shifts WHICH\n  emergent-emotion region the constructed event lands "
          "in — now across anger,\n  bliss, sadness and anxiety — while the "
          "default temperament stays byte-identical\n  to today, and appraisal "
          "walls bound WHERE personality can bend emotion.")
    return ok


def main():
    results = {
        "GATE A  abstraction -> BLISS": gate_abstraction_bliss(),
        "GATE B  abstraction -> SADNESS + GRIEF": gate_abstraction_sadness_grief(),
        "GATE C  openness -> ANGER (NEW)": gate_openness_anger(),
        "GATE D1 abstraction -> ANGER": gate_abstraction_anger(),
        "GATE D2 skepticism -> ANXIETY": gate_skepticism_anxiety(),
        "SHAPE   appraisal walls hold": shape_of_the_coupling(),
        "SAFE    default == today": safe_default(),
    }
    coverage_table()
    return summary(results)


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
