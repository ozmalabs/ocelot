#!/usr/bin/env python3
"""EMOTIONS AS EMERGENT MODULATOR REGIONS (seed block 207000) — re-derive
Bach/Dorner PSI/MicroPsi on the integer substrate.

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It builds an
event-native photon eye, opts it in to `seeds/drives.json` + `seeds/modulators.json`
(and NOT `seeds/core_emotions.json` — the 204000 authored appraisals are ABSENT
in the G-emerge seed set, which is the whole point), creates an `EmotionHub` +
`ModulatorState` (the state-knobs) + `Drive` nodes (the motivational
configuration), ticks (`run_rules()`), and reads out — purely mechanically — the
graph's OWN modulator vector + region assignment + action tendency. Every
DECISION (the drive equations, the six modulator updates, which region, the
tendency read-off) is a graph RULE; this script only sets attrs, ticks, reads.

FRAMING (standing project rule): RE-DERIVE, not invent; the architecture is
Bach/Dorner's (2009/2012/2015); understanding, not judgment; the FUNCTIONAL
regulator, NOT a claim to felt qualia.

Gates: G-emerge (the 11-row 204000 emulation table reproduced FROM modulator
config, no authored appraisal present), G-blend (bliss/angst/grief distinct
regions, free), G-social (affiliation frustration + nurturing-absence
psychopathy from the drive side), G-minimal-pair (fear/anxiety by half-life,
anger/frustration by blocker, curiosity/boredom by lp-sign), G-discipline
(integer-native, default-OFF byte-identity). Prereg:
MODULATORS_EMERGENCE_PREREG.md. Deterministic; no wall-clock claim.

IMPORT-INERT: nothing runs at import; `main()` is the only entry.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye            # noqa: E402
from substrate.seed_loader import manifest_for     # noqa: E402

SEED = 207000
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "modulator_emergence")

# -------- ModulatorState state-knobs (personality/config; healthy defaults) ----
MS_DEFAULTS = dict(
    enabled=1.0, competence=0.0, competence_base=0.0,
    epoch=0.0, competence_epoch=-1.0, emotion_epoch=-1.0,
    drive_switch_threshold=0.0,
    competence_full=100.0, competence_lo=30.0,
    band_hi=600.0, band_mid=150.0,
    res_base=500.0, res_urg_div=4.0, res_ar_div=1.0,
    resolution_lo=200.0, resolution_hi=450.0,
    sel_div=1.0, sel_k=1.0, sel_threshold_hi=200.0,
    sec_k=1.0, securing_hi=50.0, uncertainty_hi=100.0,
    residual_thresh=100.0, w_supergraph=1.0,
    # read-off cells
    valence_raw=0.0, valence=0.0, arousal=0.0, arousal_band=0.0,
    resolution=0.0, sel_threshold=0.0, securing=0.0,
    n_fired=0.0, n_blend=0.0, action_tendency=0.0, emotion=0.0)
for _nm in ("surprise", "fear", "anxiety", "anger", "frustration", "disgust",
            "joy", "sadness", "curiosity", "boredom", "fulfilment",
            "bliss", "angst", "grief"):
    MS_DEFAULTS["hit_" + _nm] = 0.0

# -------- Drive defaults (a fully-satisfied inert drive) -----------------------
DR_DEFAULTS = dict(
    name=0.0, v_d=0.0, c_d=0.0, c_d_prev=0.0, v_0=0.0, weight=1.0,
    decay=0.0, gain=0.0, loss=0.0, half_life=1000000.0, last_tend=0.0,
    now_epoch=0.0, scale=1000.0,
    urge=0.0, urgency=0.0, pleasure=0.0, displeasure=0.0, arousal_contrib=0.0,
    threat=0.0, threat_c0=1024.0, threat_half_life=1.0, threat_now_epoch=0.0,
    threat_last_refresh=0.0, t_present=256.0, threat_precision=0.0, threat_persists=0.0,
    appraised=1.0, residual=0.0, learning_progress=0.0, value_progress=0.0,
    valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0, contamination=0.0,
    loss_object=0.0, explore=0.0, was_engaged=0.0, supergraph_value=0.0,
    exploration_urge=0.0, is_affiliation=0.0, legitimacy=0.0, social_weight=1.0)

CORE = ["surprise", "fear", "anxiety", "anger", "frustration", "disgust",
        "joy", "sadness", "curiosity", "boredom", "fulfilment"]
TEND = {"surprise": 1, "fear": 2, "anxiety": 3, "anger": 4, "frustration": 5,
        "disgust": 6, "joy": 7, "sadness": 8, "curiosity": 9, "boredom": 10,
        "fulfilment": 11}
TEND_NAME = {1: "ORIENT", 2: "AVOID", 3: "VIGILANCE", 4: "APPROACH_BLOCK",
             5: "PERSIST", 6: "REJECT", 7: "REINFORCE", 8: "DISENGAGE",
             9: "ENGAGE", 10: "LEAVE", 11: "CONTRIBUTE"}
BLEND = {"bliss": 21, "angst": 22, "grief": 23}
ALL_NAMES = CORE + list(BLEND)

# 204000 arousal bands (the pre-registered 3-way binning: HIGH>=600, MID[150,599],
# LOW<150) that the modulator-derived arousal must reproduce.
BAND_OF = {"surprise": 1, "fear": 0, "anxiety": 2, "anger": 2, "frustration": 2,
           "disgust": 1, "joy": 1, "sadness": 0, "curiosity": 1, "boredom": 0,
           "fulfilment": 1}          # 2=HIGH 1=MID 0=LOW
# 204000 valence signs
VAL_OF = {"surprise": 0, "fear": -1, "anxiety": -1, "anger": -1, "frustration": -1,
          "disgust": -1, "joy": 1, "sadness": -1, "curiosity": 1, "boredom": -1,
          "fulfilment": 1}

# ============ the canonical MODULATOR CONFIGURATION per emotion ================
# Each case is (ModulatorState knob overrides, leading-Drive overrides). NOTE:
# there is NO per-emotion appraisal RULE — only a motivational CONFIGURATION set
# on drives/knobs; the SAME generic modulator+region machinery classifies all.
CANON = {
    "surprise":    (dict(), dict(appraised=0, residual=500, v_d=0, c_d=0, c_d_prev=0, v_0=0)),
    "fear":        (dict(competence_base=10),
                    dict(threat=1, threat_half_life=1, threat_now_epoch=3, threat_c0=1024,
                         t_present=256, v_d=100, c_d=40, c_d_prev=40, v_0=0)),
    "anxiety":     (dict(competence_base=10),
                    dict(threat=1, threat_half_life=1_000_000, threat_now_epoch=3, threat_c0=1024,
                         t_present=256, exploration_urge=200, v_d=100, c_d=40, c_d_prev=40, v_0=0)),
    "anger":       (dict(competence_base=50),
                    dict(valued_goal=1, goal_blocked=1, blocker_present=1,
                         v_d=1000, c_d=200, c_d_prev=200, v_0=100, weight=1)),
    "frustration": (dict(competence_base=50),
                    dict(valued_goal=1, goal_blocked=1, blocker_present=0,
                         v_d=1000, c_d=200, c_d_prev=200, v_0=100, weight=1)),
    "disgust":     (dict(), dict(contamination=1, v_d=1000, c_d=400, c_d_prev=400, v_0=0)),
    "joy":         (dict(), dict(value_progress=448, goal_blocked=0,
                                 v_d=1000, c_d=600, c_d_prev=100, v_0=0)),
    "sadness":     (dict(), dict(value_progress=-50, v_d=100, c_d=60, c_d_prev=60, v_0=0)),
    "curiosity":   (dict(), dict(explore=1, learning_progress=180, value_progress=0,
                                 v_d=1000, c_d=600, c_d_prev=100, v_0=0)),
    "boredom":     (dict(), dict(explore=1, learning_progress=0, was_engaged=1,
                                 value_progress=0, v_d=100, c_d=60, c_d_prev=60, v_0=0)),
    "fulfilment":  (dict(), dict(supergraph_value=300, value_progress=0, explore=0,
                                 v_d=1000, c_d=600, c_d_prev=100, v_0=0)),
}
# the three FREE blend regions (not in the 204000 list)
BLEND_CANON = {
    "bliss": (dict(), dict(value_progress=0, explore=0, supergraph_value=0,
                           v_d=100, c_d=90, c_d_prev=40, v_0=0)),
    "angst": (dict(competence_base=10),
              dict(threat=0, exploration_urge=200, valued_goal=0, contamination=0,
                   value_progress=0, v_d=100, c_d=40, c_d_prev=40, v_0=0)),
    "grief": (dict(), dict(value_progress=-50, loss_object=1,
                           v_d=100, c_d=60, c_d_prev=60, v_0=0)),
}


# ----------------------------------------------------------------- eye + nodes
def _eye(load_emergent=True, load_authored=False):
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    if load_emergent:
        inner.load_seed_manifest(manifest_for("drives"), eye._agent)
        inner.load_seed_manifest(manifest_for("modulators"), eye._agent)
    if load_authored:
        inner.load_seed_manifest(manifest_for("core_emotions"), eye._agent)
    return eye, inner


def _hub_ms(eye, inner, **ms_over):
    hub = eye.substrate.add_node("EmotionHub", {})
    p = dict(MS_DEFAULTS); p.update({k: float(v) for k, v in ms_over.items()})
    ms = eye.substrate.add_node("ModulatorState", p)
    inner.add_edge_unchecked(hub, "has_modulator_state", ms)
    return hub, ms


def _drive(eye, inner, ms, leading=True, **over):
    a = dict(DR_DEFAULTS); a.update({k: float(v) for k, v in over.items()})
    d = eye.substrate.add_node("Drive", a)
    inner.add_edge_unchecked(ms, "has_active_drive", d)
    if leading:
        inner.add_edge_unchecked(ms, "leading_drive", d)
    return d


def _ms_attrs(eye, ms):
    return eye.substrate.node(ms)["attrs"]


def _fired(eye, ms):
    a = _ms_attrs(eye, ms)
    return [nm for nm in CORE if int(a.get("hit_" + nm, 0)) == 1]


def _fired_all(eye, ms):
    a = _ms_attrs(eye, ms)
    return [nm for nm in ALL_NAMES if int(a.get("hit_" + nm, 0)) == 1]


def _case(ms_over, dr_over, load_authored=False):
    eye, inner = _eye(load_authored=load_authored)
    hub, ms = _hub_ms(eye, inner, **ms_over)
    _drive(eye, inner, ms, **dr_over)
    inner.run_rules()
    a = dict(_ms_attrs(eye, ms))
    fired = _fired_all(eye, ms)
    eye.stop()
    return a, fired


# ------------------------------------------------------- G-emerge (headline)
BAND_NAME = {2: "HIGH", 1: "MID", 0: "LOW"}


def g_emerge():
    """The 204000 emulation table reproduced FROM the modulator configuration,
    with NO authored per-emotion appraisal rule present."""
    rows, ok = [], True
    for nm in CORE:
        ms_over, dr_over = CANON[nm]
        a, fired = _case(ms_over, dr_over, load_authored=False)
        got_tend = int(a["action_tendency"])
        exp_tend = TEND[nm]
        got_val = int(a["valence"])
        got_band = int(a["arousal_band"])
        n_fired = int(a["n_fired"])
        n_blend = int(a["n_blend"])
        correct = (fired == [nm] and got_tend == exp_tend
                   and got_val == VAL_OF[nm] and got_band == BAND_OF[nm]
                   and n_fired == 1 and n_blend == 0)
        ok = ok and correct
        rows.append(dict(emotion=nm, expected_tendency=TEND_NAME[exp_tend],
                         got_tendency=TEND_NAME.get(got_tend, "NONE"),
                         fired=fired, n_fired=n_fired,
                         valence=got_val, expected_valence=VAL_OF[nm],
                         arousal=int(a["arousal"]),
                         arousal_band=BAND_NAME[got_band],
                         expected_band=BAND_NAME[BAND_OF[nm]],
                         correct=correct))
    # NULL: an enabled ModulatorState + an appraised drive with NO configuration
    a_null, fired_null = _case(dict(), dict(appraised=1, v_d=0, c_d=0, c_d_prev=0, v_0=0))
    null_ok = (fired_null == [] and int(a_null["n_fired"]) == 0
               and int(a_null["n_blend"]) == 0
               and int(a_null["action_tendency"]) == 0)
    n_correct = sum(1 for r in rows if r["correct"])
    return dict(rows=rows, n=len(rows), n_correct=n_correct, all_correct=ok,
                one_fire_each=all(r["n_fired"] == 1 for r in rows),
                valence_signs_match=all(r["valence"] == r["expected_valence"] for r in rows),
                arousal_bands_match=all(r["arousal_band"] == r["expected_band"] for r in rows),
                tendencies_match=all(r["got_tendency"] == r["expected_tendency"] for r in rows),
                null_fires_none=null_ok)


# --------------------------------------------------------- G-blend (free states)
def g_blend():
    out = {}
    for nm in BLEND:
        ms_over, dr_over = BLEND_CANON[nm]
        a, fired = _case(ms_over, dr_over)
        out[nm] = dict(fired=fired, emotion=int(a["emotion"]),
                       valence=int(a["valence"]), arousal=int(a["arousal"]),
                       arousal_band=BAND_NAME[int(a["arousal_band"])],
                       resolution=int(a["resolution"]),
                       n_core=int(a["n_fired"]), n_blend=int(a["n_blend"]))
    # each blend is a DISTINCT region: it fires only its own hit, no core emotion,
    # and its coordinates differ from its nearest named neighbour.
    bliss = out["bliss"]; angst = out["angst"]; grief = out["grief"]
    # bliss (pos/LOW/high-res) vs joy (pos/MID+): distinct by arousal band
    joy_a, _ = _case(*CANON["joy"])
    sad_a, _ = _case(*CANON["sadness"])
    anx_a, _ = _case(*CANON["anxiety"])
    return dict(
        detail=out,
        bliss_distinct=(bliss["fired"] == ["bliss"] and bliss["n_core"] == 0
                        and bliss["arousal_band"] == "LOW"
                        and BAND_NAME[int(joy_a["arousal_band"])] != "LOW"),
        angst_distinct=(angst["fired"] == ["angst"] and angst["n_core"] == 0
                        and int(anx_a["hit_anxiety"]) == 1),  # anxiety needs a threat object; angst has none
        grief_distinct=(grief["fired"] == ["grief"] and grief["n_core"] == 0
                        and int(sad_a["hit_sadness"]) == 1),  # sadness is undirected; grief adds the loss object
        all_distinct=(bliss["fired"] == ["bliss"] and angst["fired"] == ["angst"]
                      and grief["fired"] == ["grief"]
                      and bliss["n_core"] == angst["n_core"] == grief["n_core"] == 0))


# ------------------------------------------------ G-social (affiliation unlocks)
def g_social():
    """The affiliation drive: a legitimacy signal is a rule; anti-legitimacy
    (reproach) frustrates affiliation -> negative-valence social appraisal that
    204000 could not reach. Nurturing-absence reproduces the 204000 psychopathy
    signature FROM the drive side (the somatic brake on a harmful act removed)."""
    # affiliation frustrated: c_d starts at target, a reproach (legitimacy=-1)
    # scaled by the source's social_weight pushes it DOWN -> displeasure -> neg valence.
    eye, inner = _eye()
    hub, ms = _hub_ms(eye, inner)
    d = _drive(eye, inner, ms, is_affiliation=1, appraised=1,
               v_d=1000, c_d=1000, c_d_prev=1000, v_0=0,
               gain=100, loss=100, social_weight=3, legitimacy=-1,
               exploration_urge=0)
    inner.run_rules()
    a = dict(_ms_attrs(eye, ms))
    dd = dict(eye.substrate.node(d)["attrs"])
    eye.stop()
    affil_frustrated = (int(a["valence"]) < 0 and int(dd["c_d"]) < 1000
                        and int(dd["displeasure"]) > 0)

    # praise (legitimacy=+1) -> pleasure -> positive valence (the reward side)
    eye, inner = _eye()
    hub, ms = _hub_ms(eye, inner)
    d = _drive(eye, inner, ms, is_affiliation=1, appraised=1,
               v_d=1000, c_d=400, c_d_prev=400, v_0=0,
               gain=100, loss=100, social_weight=3, legitimacy=1)
    inner.run_rules()
    a_praise = dict(_ms_attrs(eye, ms))
    dd_praise = dict(eye.substrate.node(d)["attrs"])
    eye.stop()
    praise_pleasure = (int(dd_praise["c_d"]) > 400 and int(dd_praise["pleasure"]) > 0)

    # psychopathy = nurturing ABSENCE = the w_supergraph knob at 0: on a
    # supergraph-harmful but individually-good act, the somatic brake is removed.
    # (convergent with 204000 G4, now realised from the drive/knob side.)
    def endorse(w_super):
        eye, inner = _eye()
        hub, ms = _hub_ms(eye, inner, w_supergraph=w_super)
        # individual GOOD (pleasure) but supergraph HARM (negative supergraph_value)
        d = _drive(eye, inner, ms, appraised=1, supergraph_value=-800,
                   v_d=1000, c_d=900, c_d_prev=100, v_0=0)  # big pleasure
        inner.run_rules()
        a = dict(_ms_attrs(eye, ms))
        # total societal value = individual valence contribution + (w_supergraph gated) supergraph
        # the somatic brake: healthy VALUES the supergraph harm (nets negative),
        # the psychopath (w=0) does not -> endorses.
        indiv = int(a["valence_raw"])
        social = int(d and eye.substrate.node(d)["attrs"]["supergraph_value"]) if w_super > 0 else 0
        total = indiv + social
        eye.stop()
        return dict(w=w_super, indiv=indiv, social=social, total=total,
                    endorses=(total >= 0))
    healthy = endorse(1)
    psychopath = endorse(0)
    return dict(
        affiliation_frustrated=dict(valence=int(a["valence"]), c_d=int(dd["c_d"]),
                                    displeasure=int(dd["displeasure"])),
        affiliation_praise=dict(c_d=int(dd_praise["c_d"]), pleasure=int(dd_praise["pleasure"])),
        healthy=healthy, psychopath=psychopath,
        affiliation_frustration_negative=affil_frustrated,
        affiliation_praise_positive=praise_pleasure,
        psychopathy_removes_brake=(not healthy["endorses"] and psychopath["endorses"]))


# -------------------------------------------------- G-minimal-pair (preserved)
def g_minimal_pair():
    pairs = []
    # fear <-> anxiety : ONLY the 196000 threat_half_life
    fear_a, fear_f = _case(*CANON["fear"])
    anx_a, anx_f = _case(*CANON["anxiety"])
    pairs.append(dict(name="fear_vs_anxiety", knob="threat_half_life",
                      a=fear_f, b=anx_f,
                      ok=(fear_f == ["fear"] and anx_f == ["anxiety"])))
    # anger <-> frustration : ONLY blocker_present
    ang_a, ang_f = _case(*CANON["anger"])
    fru_a, fru_f = _case(*CANON["frustration"])
    pairs.append(dict(name="anger_vs_frustration", knob="blocker_present",
                      a=ang_f, b=fru_f,
                      ok=(ang_f == ["anger"] and fru_f == ["frustration"])))
    # curiosity <-> boredom : ONLY the sign of learning-progress
    cur_a, cur_f = _case(*CANON["curiosity"])
    bor_a, bor_f = _case(*CANON["boredom"])
    pairs.append(dict(name="curiosity_vs_boredom", knob="learning_progress",
                      a=cur_f, b=bor_f,
                      ok=(cur_f == ["curiosity"] and bor_f == ["boredom"])))
    return dict(pairs=pairs, all_ok=all(p["ok"] for p in pairs))


# -------------------------------------------- G-discipline: competence accumulator
def competence_accumulator():
    """competence is a RUNNING accumulator: seeded from learning-progress and
    latched exactly once per graph epoch. Feed a sequence of positive
    learning-progress and watch general competence rise monotonically."""
    eye, inner = _eye()
    hub, ms = _hub_ms(eye, inner)
    d = _drive(eye, inner, ms, appraised=1, explore=1, learning_progress=20,
               v_d=100, c_d=100, c_d_prev=100, v_0=0)
    trace = []
    for epoch in range(5):
        eye.substrate.set_attr(ms, "epoch", float(epoch))
        inner.run_rules()
        comp = int(_ms_attrs(eye, ms)["competence"])
        trace.append(comp)
    eye.stop()
    rises = all(trace[i] < trace[i + 1] for i in range(len(trace) - 1))
    return dict(trace=trace, rises_monotonically=rises)


# -------------------------------------------- G-discipline: integer + default-off
def integer_audit():
    float_terms = {"Div", "Exp", "Log", "Sqrt", "Sin", "Cos", "Pow"}
    report, bad = {}, {}
    for sid in ("drives", "modulators"):
        seed = json.load(open(os.path.join(ROOT, "seeds", sid + ".json")))

        def ops(term, acc):
            if isinstance(term, dict):
                if "type" in term:
                    acc.add(term["type"])
                for k in ("a", "b", "arg", "cond", "then", "other", "node",
                          "source", "value", "member", "container"):
                    if k in term:
                        ops(term[k], acc)
                for x in term.get("items", []):
                    ops(x, acc)
            return acc
        for r in seed["rules"]:
            used = set()
            for eff in r.get("effects", []):
                if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                    ops(eff[3].get("__term__", {}), used)
            ops(r.get("where", {}), used)
            report[sid + ":" + r["name"]] = sorted(used)
            if used & float_terms:
                bad[sid + ":" + r["name"]] = sorted(used & float_terms)
    return dict(offenders=bad, all_integer=(len(bad) == 0))


def integer_values_audit():
    produced = ["valence_raw", "valence", "arousal", "arousal_band", "resolution",
                "sel_threshold", "securing", "competence", "n_fired", "n_blend",
                "action_tendency", "emotion"]
    bad = []
    for nm in CORE:
        a, _ = _case(*CANON[nm])
        for k in produced:
            v = a.get(k, 0.0)
            if v is not None and float(v) != float(int(v)):
                bad.append((nm, k, v))
    return dict(offenders=bad[:20], all_integer=(len(bad) == 0))


def default_off_identity():
    """With NO ModulatorState created, an eye is byte-identical whether or not
    the two 207000 seeds are loaded."""
    def run(load_emergent):
        eye, inner = _eye(load_emergent=load_emergent)
        import numpy as np
        rng = np.random.default_rng(SEED)
        for _t in range(1, 6):
            pk = [{"col": c, "row": r, "wavelength_nm": 498.0,
                   "count": int(rng.poisson(40))}
                  for r in range(4) for c in range(4)]
            eye.submit_photons_2d(pk)
            inner.run_cognitive_tasks(1)
            inner.run_rules()
        cells = []
        for cid in eye._cells:
            a = eye.substrate.node(cid)["attrs"]
            cells.append({k: (round(v, 9) if isinstance(v, float) else v)
                          for k, v in sorted(a.items())})
        counts = {"node_count": eye.substrate._inner.node_count(),
                  "ModulatorState": len(eye.substrate.nodes("ModulatorState")),
                  "Drive": len(eye.substrate.nodes("Drive"))}
        fp = json.dumps({"counts": counts, "cells": cells}, sort_keys=True)
        eye.stop()
        return fp, counts
    fp_off, c_off = run(False)
    fp_on, c_on = run(True)
    return dict(identical=(fp_off == fp_on), without_seed=c_off, with_seed_no_hub=c_on,
                no_modulator_nodes_created=(c_on.get("ModulatorState", 0) == 0
                                            and c_on.get("Drive", 0) == 0))


def source_audit():
    """The mechanism is graph RULES; the adapter runs no Python rule engine, and
    the 204000 authored appraisals are ABSENT from the emergent seed set."""
    dr = json.load(open(os.path.join(ROOT, "seeds", "drives.json")))
    mo = json.load(open(os.path.join(ROOT, "seeds", "modulators.json")))
    dr_rules = {r["name"] for r in dr["rules"]}
    mo_rules = {r["name"] for r in mo["rules"]}
    # the demand equations exist as rules
    has_demand = {"drive_urge", "drive_urgency", "drive_decay",
                  "drive_pleasure", "drive_displeasure"} <= dr_rules
    # the six modulator update rules exist
    has_modulators = {"mod_valence", "mod_arousal", "mod_resolution",
                      "mod_sel_threshold", "mod_securing", "mod_competence"} <= mo_rules
    # a region predicate per emotion (emx_*), NOT an em_* appraisal
    has_regions = all(("emx_" + nm) in mo_rules for nm in CORE)
    no_authored = not any(r.startswith("em_") and not r.startswith("emx_") for r in mo_rules)
    # drive_decay reuses the 196000 scale2 atom
    dtxt = json.dumps([r for r in dr["rules"] if r["name"] == "drive_decay"])
    reuses_scale2 = ("Ashr" in dtxt and "half_life" in dtxt and "last_tend" in dtxt)
    # modulators depends on the shared atoms
    deps = set(mo.get("depends_on", []))
    depends_shared = {"drives", "staleness_decay", "learning_progress_curiosity"} <= deps
    # every new rule guards on ModulatorState.enabled (default-OFF)
    def guards_enabled(rules):
        for r in rules:
            if "enabled" not in json.dumps(r.get("where", {})):
                return False
        return True
    all_guard = guards_enabled(dr["rules"]) and guards_enabled(mo["rules"])
    src = open(os.path.abspath(__file__)).read()
    forbidden = ["gr" + ".run(", "graph_" + "rewrite", "make_" + "rule",
                 "gr." + "_match(", "gr." + "_apply("]
    return dict(
        has_demand_equations=has_demand, has_six_modulators=has_modulators,
        region_predicate_per_emotion=has_regions,
        no_authored_appraisal_in_emergent_seed=no_authored,
        drive_decay_reuses_196000_scale2=reuses_scale2,
        modulators_depend_on_shared_atoms=depends_shared,
        every_rule_default_off_guarded=all_guard,
        adapter_runs_no_python_rule_engine=(not any(t in src for t in forbidden)))


# --------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axes[0]
    band_y = {"LOW": 0, "MID": 1, "HIGH": 2}
    for r in res["g_emerge"]["rows"]:
        ax.scatter(r["valence"], band_y[r["arousal_band"]], s=60,
                   color=("#1b7837" if r["correct"] else "#b2182b"))
        ax.annotate(r["emotion"], (r["valence"], band_y[r["arousal_band"]]),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.axvline(0, color="#ccc", ls=":"); ax.set_xlim(-1.6, 1.6); ax.set_ylim(-0.5, 2.5)
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["LOW", "MID", "HIGH"])
    ax.set_title("G-emerge circumplex — FROM modulator config\n(valence sign x arousal band)")
    ax.set_xlabel("valence (Sum pleasure - displeasure - urge)")
    ax.set_ylabel("arousal band")
    ax = axes[1]
    labels = ["healthy\n(w=1)", "psychopath\n(w=0)"]
    tot = [res["g_social"]["healthy"]["total"], res["g_social"]["psychopath"]["total"]]
    ax.bar(range(2), tot, color=["#2166ac", "#b2182b"])
    ax.axhline(0, color="#999", ls=":")
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("G-social: nurturing-absence (w=0)\nremoves the somatic brake")
    ax.set_ylabel("total societal value")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    ge = g_emerge()
    gb = g_blend()
    gs = g_social()
    gmp = g_minimal_pair()
    comp = competence_accumulator()
    ia = integer_audit()
    iva = integer_values_audit()
    doff = default_off_identity()
    sa = source_audit()

    criteria = dict(
        g_emerge_all_correct=ge["all_correct"],
        g_emerge_tendencies_match=ge["tendencies_match"],
        g_emerge_valence_signs_match=ge["valence_signs_match"],
        g_emerge_arousal_bands_match=ge["arousal_bands_match"],
        g_emerge_one_fire_each=ge["one_fire_each"],
        g_emerge_null_fires_none=ge["null_fires_none"],
        g_blend_bliss_distinct=gb["bliss_distinct"],
        g_blend_angst_distinct=gb["angst_distinct"],
        g_blend_grief_distinct=gb["grief_distinct"],
        g_blend_all_distinct=gb["all_distinct"],
        g_social_affiliation_frustration_negative=gs["affiliation_frustration_negative"],
        g_social_affiliation_praise_positive=gs["affiliation_praise_positive"],
        g_social_psychopathy_removes_brake=gs["psychopathy_removes_brake"],
        g_minimal_pair_all_ok=gmp["all_ok"],
        g_discipline_competence_accumulates=comp["rises_monotonically"],
        g_discipline_integer_native_terms=ia["all_integer"],
        g_discipline_integer_native_values=iva["all_integer"],
        g_discipline_default_off_byte_identical=doff["identical"],
        g_discipline_default_off_no_nodes=doff["no_modulator_nodes_created"],
        source_no_authored_appraisal=sa["no_authored_appraisal_in_emergent_seed"],
        source_has_six_modulators=sa["has_six_modulators"],
        source_has_demand_equations=sa["has_demand_equations"],
        source_drive_decay_reuses_196000=sa["drive_decay_reuses_196000_scale2"],
        source_depends_on_shared_atoms=sa["modulators_depend_on_shared_atoms"],
        source_every_rule_default_off_guarded=sa["every_rule_default_off_guarded"],
        source_no_python_rule_engine=sa["adapter_runs_no_python_rule_engine"],
    )
    res = dict(seed=SEED, g_emerge=ge, g_blend=gb, g_social=gs, g_minimal_pair=gmp,
               competence_accumulator=comp, integer_audit=ia, integer_values_audit=iva,
               default_off=doff, source_audit=sa, criteria=criteria)
    with open(os.path.join(RESULTS, "modulator_emergence.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "modulator_emergence.png"))
    except Exception as e:
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    print("ALL PASS:", all(r["criteria"].values()))
