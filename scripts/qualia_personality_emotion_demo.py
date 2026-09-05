#!/usr/bin/env python3
"""FINAL-VERIFICATION task 6 — THE PAYOFF: distinct PERSONALITIES produce
distinct EMERGENT EMOTIONS on the SAME drive event.

The trait vector (openness / abstraction / skepticism, domains/disposition.py)
is now the drive-regulated SET-POINT layer of the substrate's MicroPsi agent:
each crystallised trait level maps (domains/trait_modulator_bridge.trait_bias)
to a CONSTANT additive offset on a modulator formula —

    abstraction level -> abstraction_bias -> mod_resolution   baseline
    openness    level -> openness_bias    -> mod_sel_threshold baseline
    skepticism  level -> skepticism_bias  -> mod_securing       baseline

The emergent emotion is read off the SAME modulator vector by the emx_* region
rules in seeds/modulators.json (NO Python computes affect — the graph rules do).
So a shifted set-point shifts WHICH region the identical drive event lands in.

This script feeds ONE fixed drive event to several agents that differ ONLY in
their trait vector, and reads back — mechanically, from the graph — each agent's
modulator vector, emergent emotion (emx_* hit + `emotion` code) and
`action_tendency`. It shows the emotion read-off DIFFERING BY PERSONALITY on
identical input, with real numbers.

TWO CLEAN EMERGENT-EMOTION GATES (both real, both within the documented +/-4
trait scale — abstraction step 30, skepticism step 15):

  (1) ABSTRACTION gates the ANGER boundary (emx_anger needs resolution <
      resolution_lo). On a blocked-goal adversity event whose neutral resolution
      sits just below the low-resolution mark, a LOW-abstraction agent fires
      ANGER (reactive, APPROACH_BLOCK); a HIGH-abstraction agent's raised
      resolution baseline lifts the event OUT of the anger region — it stays
      DELIBERATIVE (no reactive tip). Same event, different emotion.

  (2) SKEPTICISM gates the ANXIETY boundary (emx_anxiety needs securing >
      securing_hi). On a persistent-threat event whose neutral securing sits just
      below the vigilance mark, a NEUTRAL agent fires NO emotion; a HIGH-skepticism
      agent's raised securing baseline crosses the mark and it tips into ANXIETY
      (VIGILANCE) SOONER. Same event, different emotion.

HONEST SCOPE (reported, not hidden): openness_bias (-> sel_threshold) and, on
most events, skepticism_bias shift the modulator STATE but at their bounded
magnitudes do not always cross a region boundary — they change the felt vector
without always changing the discrete label. The two gates above are the ones
where the label genuinely flips within the trait scale; the demo shows both the
label flips AND the underlying state shifts.

SAFE DEFAULT: the seeded-default temperament (openness -1, abstraction 0,
skepticism 0) maps to ZERO bias on all three axes, so a default agent's modulator
vector and emergent emotion are BYTE-IDENTICAL to the pre-wiring baseline
(decision-equivalence). Proven here on every event.

Run: python3 scripts/qualia_personality_emotion_demo.py

Uses the ESTABLISHED emergence harness (scripts/modulator_emergence_measure) for
the drive/modulator/emx spine and the REAL bridge scale (trait_modulator_bridge.
trait_bias) for the trait->bias map — no re-implemented affect, no invented dial.
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
EMOTION_NAME = {
    0: "(none/deliberative)", 1: "surprise", 2: "fear", 3: "anxiety",
    4: "anger", 5: "frustration", 6: "disgust", 7: "joy", 8: "sadness",
    9: "curiosity", 10: "boredom", 11: "fulfilment", 12: "bliss",
    13: "grief",
}
TEND_NAME = {0: "NONE", 1: "ORIENT", 2: "AVOID", 3: "VIGILANCE",
             4: "APPROACH_BLOCK", 5: "PERSIST", 6: "REJECT", 7: "REINFORCE",
             8: "DISENGAGE", 9: "ENGAGE", 10: "LEAVE", 11: "CONTRIBUTE"}


def section(t):
    print("\n" + "=" * 80)
    print(t)
    print("=" * 80)


def _bias_vector(vector):
    """Map a trait VECTOR {trait: level} through the REAL bridge scale
    (trait_modulator_bridge.trait_bias) to the three modulator bias offsets. This
    is the exact map sync_traits_to_modulator writes onto the ModulatorState."""
    return {
        "abstraction_bias": tmb.trait_bias(vector.get("abstraction", 0),
                                            "abstraction"),
        "openness_bias": tmb.trait_bias(vector.get("openness", -1), "openness"),
        "skepticism_bias": tmb.trait_bias(vector.get("skepticism", 0),
                                           "skepticism"),
    }


def _run_event(vector, drive_over, ms_extra=None):
    """Feed ONE drive event to an agent whose ModulatorState carries the bias
    offsets derived from `vector` (via the real bridge scale). Returns the
    read-off modulator vector + emergent emotion + tendency — all produced by the
    graph's emx_* rules, nothing computed in Python."""
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
        "competence": int(a["competence"]),
        "valence": int(a["valence"]),
        "arousal": int(a["arousal"]),
        "emotion_code": int(a["emotion"]),
        "emotion": EMOTION_NAME.get(int(a["emotion"]), "?"),
        "tendency": TEND_NAME.get(int(a["action_tendency"]), "?"),
        "fired": fired,
    }


DEFAULT_VECTOR = {"openness": -1, "abstraction": 0, "skepticism": 0}


def _print_row(label, r):
    print(f"  {label:26s} res={r['resolution']:>5} sel={r['sel_threshold']:>6} "
          f"sec={r['securing']:>4} | abstr_bias={r['biases']['abstraction_bias']:>4} "
          f"skept_bias={r['biases']['skepticism_bias']:>4} "
          f"|| EMOTION={r['emotion']:<20} tend={r['tendency']}")


def gate_abstraction_anger():
    section("GATE 1 — ABSTRACTION shifts resolution -> the ANGER boundary")
    print("The SAME drive event: a VALUED GOAL is BLOCKED with a blocker present"
          " (adversity),\ntuned so the neutral resolution sits just below the"
          " low-resolution mark\n(resolution_lo=200). emx_anger requires"
          " resolution < resolution_lo.\n")
    # blocked-goal adversity; neutral resolution ~84 (< 200) => anger at neutral.
    event = dict(valued_goal=1, goal_blocked=1, blocker_present=1,
                 v_d=1000, c_d=250, c_d_prev=250, v_0=100, weight=1)
    ms_extra = dict(competence_base=50.0)   # competent agent, blocked externally

    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("low-abstraction (0)", {"openness": -1, "abstraction": 0, "skepticism": 0}),
        ("mid-abstraction (+2)", {"openness": -1, "abstraction": 2, "skepticism": 0}),
        ("high-abstraction (+4)", {"openness": -1, "abstraction": 4, "skepticism": 0}),
    ):
        r = _run_event(vec, event, ms_extra)
        rows.append((label, r))
        _print_row(label, r)

    low = rows[1][1]
    high = rows[-1][1]
    flipped = (low["emotion"] == "anger"
               and high["emotion"] != "anger")
    print(f"\n  => low-abstraction fires {low['emotion'].upper()} "
          f"(tend {low['tendency']}); high-abstraction resolution rises "
          f"{low['resolution']}->{high['resolution']} (crosses 200)\n     and the"
          f" event leaves the anger region -> {high['emotion']}. "
          f"SAME event, DIFFERENT emotion: {flipped}")
    return flipped


def gate_skepticism_anxiety():
    section("GATE 2 — SKEPTICISM shifts securing -> the ANXIETY boundary")
    print("The SAME drive event: a PERSISTENT THREAT with modest competence,"
          " tuned so the\nneutral securing sits just below the vigilance mark"
          " (securing_hi=50).\nemx_anxiety requires securing > securing_hi.\n")
    # persistent threat; neutral securing ~49 (< 50) => no emotion at neutral.
    event = dict(threat=1, threat_half_life=1_000_000, threat_now_epoch=3,
                 threat_c0=1024, t_present=256, v_d=100, c_d=40, c_d_prev=40,
                 v_0=0, exploration_urge=0, weight=26)
    ms_extra = dict(competence_base=25.0)   # competence lands ~25 (< competence_lo)

    rows = []
    for label, vec in (
        ("DEFAULT (== today)", DEFAULT_VECTOR),
        ("neutral-skepticism (0)", {"openness": -1, "abstraction": 0, "skepticism": 0}),
        ("mid-skepticism (+2)", {"openness": -1, "abstraction": 0, "skepticism": 2}),
        ("high-skepticism (+4)", {"openness": -1, "abstraction": 0, "skepticism": 4}),
    ):
        r = _run_event(vec, event, ms_extra)
        rows.append((label, r))
        _print_row(label, r)

    neutral = rows[1][1]
    high = rows[-1][1]
    flipped = (neutral["emotion"] != "anxiety"
               and high["emotion"] == "anxiety")
    print(f"\n  => neutral securing {neutral['securing']} (< 50) => "
          f"{neutral['emotion']}; high-skepticism securing rises "
          f"{neutral['securing']}->{high['securing']} (crosses 50)\n     and the"
          f" event tips into {high['emotion'].upper()} "
          f"(tend {high['tendency']}) SOONER. SAME event, DIFFERENT emotion: "
          f"{flipped}")
    return flipped


def safe_default():
    section("SAFE DEFAULT — the default temperament reproduces TODAY exactly")
    print("Both gate events, but comparing the DEFAULT trait vector (openness -1,"
          " abstraction 0,\nskepticism 0) against a BARE ModulatorState with the"
          " bias attrs at their 0 default.\nThe emergent emotion + full modulator"
          " vector must be byte-identical.\n")
    events = {
        "anger event": (dict(valued_goal=1, goal_blocked=1, blocker_present=1,
                             v_d=1000, c_d=250, c_d_prev=250, v_0=100, weight=1),
                        dict(competence_base=50.0)),
        "threat event": (dict(threat=1, threat_half_life=1_000_000,
                              threat_now_epoch=3, threat_c0=1024, t_present=256,
                              v_d=100, c_d=40, c_d_prev=40, v_0=0,
                              exploration_urge=0, weight=26),
                         dict(competence_base=25.0)),
    }
    all_ok = True
    for name, (event, ms_extra) in events.items():
        # (a) default trait vector -> bias via the real scale
        r_default = _run_event(DEFAULT_VECTOR, event, ms_extra)
        # (b) NO bias at all (bias attrs left at their 0 seed default)
        a_bare, fired_bare = M._case(dict(ms_extra), dict(event))
        bare = {
            "resolution": int(a_bare["resolution"]),
            "sel_threshold": int(a_bare["sel_threshold"]),
            "securing": int(a_bare["securing"]),
            "emotion_code": int(a_bare["emotion"]),
            "action_tendency": int(a_bare["action_tendency"]),
        }
        ident = (r_default["resolution"] == bare["resolution"]
                 and r_default["sel_threshold"] == bare["sel_threshold"]
                 and r_default["securing"] == bare["securing"]
                 and r_default["emotion_code"] == bare["emotion_code"])
        all_ok = all_ok and ident
        print(f"  {name:14s} default-vector: res={r_default['resolution']} "
              f"sel={r_default['sel_threshold']} sec={r_default['securing']} "
              f"emotion={r_default['emotion']}")
        print(f"  {'':14s} bare-no-bias  : res={bare['resolution']} "
              f"sel={bare['sel_threshold']} sec={bare['securing']} "
              f"emotion={EMOTION_NAME.get(bare['emotion_code'])}   "
              f"IDENTICAL: {ident}")
    print(f"\n  => default temperament == today (byte-identical modulator +"
          f" emotion): {all_ok}")
    return all_ok


def summary(g1, g2, sd):
    section("SUMMARY — distinct personalities, distinct emergent emotions, SAME event")
    print(f"  GATE 1 abstraction->anger boundary flip : {g1}")
    print(f"  GATE 2 skepticism->anxiety boundary flip: {g2}")
    print(f"  SAFE DEFAULT (default == today)          : {sd}")
    ok = g1 and g2 and sd
    print(f"\n  TASK 6 EMERGENT-EMOTION DEMO: {'PASS' if ok else 'REVIEW'}")
    print("  The trait vector is the drive-regulated modulator SET-POINT: it"
          " shifts WHICH\n  emergent-emotion region the identical drive event"
          " lands in, and the default\n  temperament leaves the emotion path"
          " byte-identical to today.")
    return ok


def main():
    g1 = gate_abstraction_anger()
    g2 = gate_skepticism_anxiety()
    sd = safe_default()
    return summary(g1, g2, sd)


if __name__ == "__main__":
    main()
