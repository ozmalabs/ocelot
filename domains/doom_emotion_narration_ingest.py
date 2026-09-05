"""doom_emotion_narration_ingest — MECHANICAL adapter for the 208000 fusion:
205000 active-exploration play -> 207000 emergent-emotion regions -> narration.

NO decision here (CLAUDE.md). Every function is (a) mechanical construction of
the opt-in emotion state (EmotionHub + ModulatorState knobs + one play Drive),
(b) mechanical measurement of RAW play observables (coverage delta, pursued-
frontier pose + whether it changed, commit-net flag, arrival), written as `ev_*`
attrs on the play Drive, or (c) a mechanical read-off: it reads the GRAPH-produced
`ms.emotion` code and formats the matching `EmotionNarration` template.

The DECISION -- which config an observable maps to, and which emotion that config
IS -- lives entirely in graph rules: `dem_drive_feed` (the appraisal, in
seeds/doom_emotion_narration.json) sets the Drive config; the untouched 207000
`mod_*` + `emx_*` rules classify and set `ms.emotion`. This module never writes a
`hit_*`/`emotion`/`action_tendency` attr and never selects an emotion in Python.
"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

_EMO_NAMES = ("surprise", "fear", "anxiety", "anger", "frustration", "disgust",
              "joy", "sadness", "curiosity", "boredom", "fulfilment",
              "bliss", "angst", "grief")

# ModulatorState knobs: the 207000 healthy defaults, with residual_thresh lowered
# to sit just under the surprise threshold so a novel-cells SPIKE (a genuine new
# sightline) trips the pre-appraisal surprise region. novel_hi is the spike
# threshold on the play Drive.
NOVEL_HI = 8
MS_KNOBS = dict(
    enabled=1.0, competence=0.0, competence_base=0.0,
    epoch=-1.0, competence_epoch=-1.0, emotion_epoch=-1.0,
    drive_switch_threshold=0.0,
    competence_full=100.0, competence_lo=30.0,
    band_hi=600.0, band_mid=150.0,
    res_base=500.0, res_urg_div=4.0, res_ar_div=1.0,
    resolution_lo=200.0, resolution_hi=450.0,
    # trait set-point bias offsets: default 0 => bias-free (byte-identical to
    # pre-bias). The trait<->MicroPsi bridge writes nonzero values on opt-in.
    abstraction_bias=0.0, openness_bias=0.0, skepticism_bias=0.0,
    sel_div=1.0, sel_k=1.0, sel_threshold_hi=200.0,
    sec_k=1.0, securing_hi=50.0, uncertainty_hi=100.0,
    residual_thresh=float(NOVEL_HI - 1), w_supergraph=1.0,
    valence_raw=0.0, valence=0.0, arousal=0.0, arousal_band=0.0,
    resolution=0.0, sel_threshold=0.0, securing=0.0,
    n_fired=0.0, n_blend=0.0, action_tendency=0.0, emotion=0.0)
for _n in _EMO_NAMES:
    MS_KNOBS["hit_" + _n] = 0.0

# A fully-satisfied, inert play Drive; the drive-feed rule overwrites its config
# from the observables each tick. now_epoch==last_tend keeps drive_decay a no-op.
DR_INIT = dict(
    name=0.0, v_d=0.0, c_d=0.0, c_d_prev=0.0, v_0=0.0, weight=1.0,
    decay=0.0, gain=0.0, loss=0.0, half_life=1000000.0, last_tend=0.0,
    now_epoch=0.0, scale=1000.0,
    urge=0.0, urgency=0.0, pleasure=0.0, displeasure=0.0, arousal_contrib=0.0,
    threat=0.0, threat_c0=1024.0, threat_half_life=1.0, threat_now_epoch=0.0,
    threat_last_refresh=0.0, t_present=256.0, threat_precision=0.0, threat_persists=0.0,
    appraised=1.0, residual=0.0, learning_progress=0.0, value_progress=0.0,
    valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0, contamination=0.0,
    loss_object=0.0, explore=0.0, was_engaged=0.0, supergraph_value=0.0,
    exploration_urge=0.0, is_affiliation=0.0, legitimacy=0.0, social_weight=1.0,
    # 208000 opt-in flag + observable channels (raw play measurements) + threshold
    play_fed=1.0, novel_hi=float(NOVEL_HI),
    ev_novel=0.0, ev_arrived=0.0, ev_switched=0.0, ev_committed=0.0,
    ev_unreach=0.0, dem_cfg=0.0)


def install_emotion(wa, game):
    """Create the graph-resident emotion state for this game and load the three
    seeds (drives, modulators, doom_emotion_narration). Mechanical opt-in."""
    from substrate.seed_loader import manifest_for
    S, I = wa.s, wa.inner
    I.load_seed_manifest(manifest_for("drives"), None)
    I.load_seed_manifest(manifest_for("modulators"), None)
    affects = list(I.neighbours(wa.agent, "has_affective_state"))
    if not affects:
        I.load_seed_manifest(manifest_for("affective_state_core"), wa.agent)
        affects = list(I.neighbours(wa.agent, "has_affective_state"))
    I.load_seed_manifest(json.load(open(
        os.path.join(_ROOT, "seeds", "doom_emotion_narration.json"))), None)
    hub = S.add_node("EmotionHub", {})
    I.add_edge_unchecked(game, "has_emotion_hub", hub)
    ms = S.add_node("ModulatorState", dict(MS_KNOBS))
    I.add_edge_unchecked(hub, "has_modulator_state", ms)
    affect = affects[0]
    I.add_edge_unchecked(hub, "has_affective_state", affect)
    I.add_edge_unchecked(ms, "projects_affect_to", affect)
    d = S.add_node("Drive", dict(DR_INIT))
    I.add_edge_unchecked(ms, "has_active_drive", d)
    I.add_edge_unchecked(ms, "leading_drive", d)
    return hub, ms, d


def committed_flag(wa, game):
    """Read the 205000 commit-net Deliberation.committed (a graph flag)."""
    import domains.doom_active_explore_ingest as ae
    S, I = wa.s, wa.inner
    hub = ae._hub(wa, game)
    if hub is None:
        return 0
    for dl in I.neighbours(hub, "has_deliberation"):
        return int(float(S.node(dl)["attrs"].get("committed", 0.0)))
    return 0


def feed_and_settle(wa, ms, d, *, novel, arrived, switched, committed, unreach):
    """Write the RAW observables onto the play Drive and produce the graph's
    emotion. Returns (emotion_code, n_fired).

    TWO-PASS settle. Pass 1 converges the new raw appraisal. The adapter then
    advances the mechanical graph epoch; `emx_epoch_reset` clears and re-opens
    the read-off lifecycle inside the graph, while competence integrates exactly
    once for that epoch. Pass 2 therefore classifies the stable state. Python
    never writes an emotion, hit, tendency, or competence accumulator."""
    S, I = wa.s, wa.inner
    I.set_attr(d, "ev_novel", float(novel))
    I.set_attr(d, "ev_arrived", float(arrived))
    I.set_attr(d, "ev_switched", float(switched))
    I.set_attr(d, "ev_committed", float(committed))
    I.set_attr(d, "ev_unreach", float(unreach))
    next_epoch = float(S.node(ms)["attrs"].get("epoch", -1.0)) + 1.0
    I.set_attr(d, "now_epoch", next_epoch)
    I.run_rules()                          # pass 1: converge config + modulators
    I.set_attr(ms, "epoch", next_epoch)   # mechanical clock; graph owns state
    I.run_rules()                          # pass 2: graph resets + classifies
    a = S.node(ms)["attrs"]
    return int(a.get("emotion", 0)), int(a.get("n_fired", 0))


def _narration_index(wa):
    """code -> (name, tendency, template) read from the EmotionNarration lexicon
    nodes the seed installed. Pure graph read."""
    S = wa.s
    idx = {}
    for n in S.nodes("EmotionNarration"):
        a = S.node(n)["attrs"]
        idx[int(a["code"])] = (a["emotion_name"], a["tendency"], a["template"])
    return idx


def narrate(idx, code, tick, cov):
    """Mechanical emit: format the FIXED template for the graph-produced emotion
    code. Returns (name, tendency, sentence) or None for a neutral tick."""
    if code == 0 or code not in idx:
        return None
    name, tend, tmpl = idx[code]
    sentence = "t%d  [%d cells]  %s: %s  (%s)" % (tick, cov, name, tmpl, tend)
    return name, tend, sentence
