#!/usr/bin/env python3
"""THE CORE-EMOTION SET — appraisal -> action-tendency over the signal economy
(seed block 204000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It builds an
event-native photon eye, opts it in to this rung's `seeds/core_emotions.json`
(which itself reuses the 196000 staleness_decay freshness atom, the 199000
present readout, and the 202000 learning-progress / value atoms verbatim),
creates an `EmotionHub` + `HeldEmotionParams` (the state-knobs) + `Appraisal`
nodes (configurations of the signal economy), ticks (`run_rules()`), and reads
out — purely mechanically — the graph's OWN action-tendency / emotion / valence /
arousal / value bookkeeping. Every DECISION (which emotion, which tendency, the
value-frame arithmetic, the endorse gate) is a graph RULE; this script only sets
attrs, ticks, and reads attributes.

FRAMING (standing project rule): re-derive, not invent; understanding, not
judgment; the FUNCTIONAL regulator, NOT a claim to felt qualia.

Gates: G1 EMULATION (N canonical appraisals -> N recognised tendencies, one-fire,
null-fires-none, discriminator pairs), G2 REFERENCE-FRAME + FULFILMENT
(fulfilment fires for supergraph contribution, DISTINCT from joy; minimal social
frame or named gap), G3 HEDONIC/EUDAIMONIC DISSOCIATION (the parenthood sweep),
G4 VALUE-SIDE DISORDER GLASS-BOX (psychopathy = w_supergraph~0 pure-knob reversal
+ state-observed-produces-factors), G5 integer-native + default-OFF byte-identity.
Prereg: VISION_CORE_EMOTIONS_PREREG.md. Deterministic; no wall-clock claim.

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

SEED = 204000
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "core_emotions")

# state-knobs (HeldEmotionParams) — healthy defaults
EP_DEFAULTS = dict(enabled=1.0, w_supergraph=1.0, mood_bias=0.0,
                   residual_thresh=100.0, high_arousal=800.0,
                   mid_arousal=400.0, low_arousal=50.0)

# an Appraisal is a configuration of the signal economy; every attr integer
APPR_DEFAULTS = dict(
    appraised=0.0, residual=0.0, residual_prev=0.0, learning_progress=0.0,
    threat=0.0, threat_c0=1024.0, threat_half_life=1.0, threat_last_refresh=0.0,
    threat_now_epoch=0.0, t_present=256.0, threat_precision=0.0, threat_persists=0.0,
    valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    contamination=0.0, attachment=0.0, regroundable=0.0, was_engaged=0.0,
    v_max=1024.0, step=1.0, step_prev=0.0, attach_v0=1024.0,
    attach_k_now=1.0, attach_k_prev=0.0, value_progress=0.0,
    individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0,
    contribution_by_self=0.0, observed_by_other=0.0,
    happiness=0.0, fulfilment_value=0.0, total_value=0.0, act_endorsed=0.0,
    n_fired=0.0, action_tendency=0.0, emotion=0.0, valence=0.0, arousal=0.0)
for _nm in ("surprise", "fear", "anxiety", "anger", "frustration", "disgust",
            "joy", "sadness", "curiosity", "boredom", "fulfilment", "pride"):
    APPR_DEFAULTS["hit_" + _nm] = 0.0

CORE = ["surprise", "fear", "anxiety", "anger", "frustration", "disgust",
        "joy", "sadness", "curiosity", "boredom", "fulfilment"]
TEND = {"surprise": 1, "fear": 2, "anxiety": 3, "anger": 4, "frustration": 5,
        "disgust": 6, "joy": 7, "sadness": 8, "curiosity": 9, "boredom": 10,
        "fulfilment": 11}
TEND_NAME = {1: "ORIENT", 2: "AVOID", 3: "VIGILANCE", 4: "APPROACH_BLOCK",
             5: "PERSIST", 6: "REJECT", 7: "REINFORCE", 8: "DISENGAGE",
             9: "ENGAGE", 10: "LEAVE", 11: "CONTRIBUTE"}

# the CANONICAL appraisal per emotion (a configuration of the economy). Fear vs
# anxiety differ ONLY in threat_half_life (the 196000/199000 PTSD knob, driven at
# the SAME epoch); anger vs frustration ONLY in blocker_present; curiosity vs
# boredom ONLY in the sign of learning-progress (residual_prev).
CANON = {
    "surprise":    dict(appraised=0, residual=500),
    "fear":        dict(appraised=1, threat=1, threat_half_life=1,     threat_now_epoch=3),
    "anxiety":     dict(appraised=1, threat=1, threat_half_life=1_000_000, threat_now_epoch=3),
    "anger":       dict(appraised=1, valued_goal=1, goal_blocked=1, blocker_present=1),
    "frustration": dict(appraised=1, valued_goal=1, goal_blocked=1, blocker_present=0),
    "disgust":     dict(appraised=1, contamination=1),
    "joy":         dict(appraised=1, valued_goal=1, goal_blocked=0, step=4, step_prev=1),
    "sadness":     dict(appraised=1, attachment=1, regroundable=0, attach_k_now=4, attach_k_prev=1),
    "curiosity":   dict(appraised=1, residual=20, residual_prev=200),
    "boredom":     dict(appraised=1, residual=50, residual_prev=50, was_engaged=1),
    "fulfilment":  dict(appraised=1, supergraph_contribution=300,
                        collective_success=300, collective_success_prev=0),
}


# ----------------------------------------------------------------- eye + nodes
def _eye(load_emotions=True):
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    if load_emotions:
        inner.load_seed_manifest(manifest_for("core_emotions"), eye._agent)
    return eye, inner


def _hub(eye, inner, **ep_over):
    from domains.core_emotions_weight import quantize_weight
    hub = eye.substrate.add_node("EmotionHub", {})
    p = dict(EP_DEFAULTS)
    p.update({k: float(v) for k, v in ep_over.items()
             if k not in ("w_supergraph_q", "w_scale_bits")})
    wq, bits = quantize_weight(p["w_supergraph"])
    p["w_supergraph_q"] = float(ep_over.get("w_supergraph_q", wq))
    p["w_scale_bits"] = float(ep_over.get("w_scale_bits", bits))
    ep = eye.substrate.add_node("HeldEmotionParams", p)
    inner.add_edge_unchecked(hub, "has_emotion_params", ep)
    return hub, ep


def _appraise(eye, inner, hub, **over):
    a = dict(APPR_DEFAULTS); a.update({k: float(v) for k, v in over.items()})
    ap = eye.substrate.add_node("Appraisal", a)
    inner.add_edge_unchecked(hub, "has_appraisal", ap)
    return ap


def _attrs(eye, ap):
    return eye.substrate.node(ap)["attrs"]


def _fired(eye, ap):
    a = _attrs(eye, ap)
    return [nm for nm in CORE if int(a.get("hit_" + nm, 0)) == 1]


# ------------------------------------------------------------- G1 emulation table
def g1_emulation():
    """Each canonical appraisal -> exactly its recognised action tendency."""
    eye, inner = _eye()
    hub, ep = _hub(eye, inner)
    rows, ok = [], True
    for nm in CORE:
        ap = _appraise(eye, inner, hub, **CANON[nm])
        inner.run_rules()
        a = _attrs(eye, ap)
        fired = _fired(eye, ap)
        got_tend = int(a["action_tendency"])
        exp_tend = TEND[nm]
        correct = (fired == [nm]) and (got_tend == exp_tend)
        ok = ok and correct
        rows.append(dict(emotion=nm, expected_tendency=TEND_NAME[exp_tend],
                         got_tendency=TEND_NAME.get(got_tend, "NONE"),
                         fired=fired, n_fired=int(a["n_fired"]),
                         valence=int(a["valence"]), arousal=int(a["arousal"]),
                         correct=correct))
    # NULL appraisal — appraised, but no economy configuration -> fires nothing
    apn = _appraise(eye, inner, hub, appraised=1)
    inner.run_rules()
    an = _attrs(eye, apn)
    null_ok = (_fired(eye, apn) == [] and int(an["n_fired"]) == 0
               and int(an["action_tendency"]) == 0)
    eye.stop()

    n_correct = sum(1 for r in rows if r["correct"])
    one_fire = all(r["n_fired"] == 1 for r in rows)
    return dict(rows=rows, n=len(rows), n_correct=n_correct,
                all_correct=ok, one_fire_each=one_fire, null_fires_none=null_ok)


def g1_discriminators():
    """The three minimal-pair discriminators: flipping ONE attribute moves the
    emotion across the recognised boundary."""
    eye, inner = _eye()
    hub, ep = _hub(eye, inner)
    pairs = []

    def classify(**over):
        ap = _appraise(eye, inner, hub, **over)
        inner.run_rules()
        return _fired(eye, ap)

    # fear <-> anxiety : ONLY threat_half_life (same PTSD knob, same epoch)
    fear = classify(appraised=1, threat=1, threat_half_life=1, threat_now_epoch=3)
    anx = classify(appraised=1, threat=1, threat_half_life=1_000_000, threat_now_epoch=3)
    pairs.append(dict(name="fear_vs_anxiety", knob="threat_half_life",
                      a=fear, b=anx, ok=(fear == ["fear"] and anx == ["anxiety"])))
    # anger <-> frustration : ONLY blocker_present
    ang = classify(appraised=1, valued_goal=1, goal_blocked=1, blocker_present=1)
    fru = classify(appraised=1, valued_goal=1, goal_blocked=1, blocker_present=0)
    pairs.append(dict(name="anger_vs_frustration", knob="blocker_present",
                      a=ang, b=fru, ok=(ang == ["anger"] and fru == ["frustration"])))
    # curiosity <-> boredom : ONLY sign of learning-progress (residual_prev)
    cur = classify(appraised=1, residual=50, residual_prev=200, was_engaged=1)
    bor = classify(appraised=1, residual=50, residual_prev=50, was_engaged=1)
    pairs.append(dict(name="curiosity_vs_boredom", knob="learning_progress",
                      a=cur, b=bor, ok=(cur == ["curiosity"] and bor == ["boredom"])))
    eye.stop()
    return dict(pairs=pairs, all_ok=all(p["ok"] for p in pairs))


# ---------------------------------------- G2 reference frame + fulfilment
def g2_fulfilment():
    eye, inner = _eye()
    hub, ep = _hub(eye, inner)

    def one(**over):
        ap = _appraise(eye, inner, hub, **over)
        inner.run_rules()
        a = _attrs(eye, ap)
        return dict(fired=_fired(eye, ap), pride=int(a["hit_pride"]),
                    happiness=int(a["happiness"]),
                    fulfilment_value=int(a["fulfilment_value"]))

    # Event A: pure INDIVIDUAL progress (joy), no supergraph contribution
    a_joy = one(appraised=1, valued_goal=1, goal_blocked=0, step=4, step_prev=1,
                individual_benefit=400, individual_cost=0,
                supergraph_contribution=0)
    # Event B: pure SUPERGRAPH contribution (fulfilment), no individual valued-goal;
    # LOW hedonic (individual benefit ~ 0) -- the distinct low-hedonic signature.
    b_ful = one(appraised=1, supergraph_contribution=300,
                collective_success=300, collective_success_prev=0,
                individual_benefit=0, individual_cost=0)
    # Fulfilment reads the COLLECTIVE ledger: if success did NOT rise, no fulfilment
    b_nogain = one(appraised=1, supergraph_contribution=300,
                   collective_success=300, collective_success_prev=300)
    # Minimal SOCIAL frame: pride = supergraph contribution attributed to SELF and
    # observed by another (co-occurs with fulfilment by design).
    pride = one(appraised=1, supergraph_contribution=300,
                collective_success=300, collective_success_prev=0,
                contribution_by_self=1, observed_by_other=1)
    eye.stop()

    return dict(
        event_joy=a_joy, event_fulfilment=b_ful, event_no_collective_gain=b_nogain,
        event_pride=pride,
        fulfilment_fires=("fulfilment" in b_ful["fired"]),
        joy_not_fulfilment=("joy" in a_joy["fired"] and "fulfilment" not in a_joy["fired"]),
        fulfilment_not_joy=("fulfilment" in b_ful["fired"] and "joy" not in b_ful["fired"]),
        fulfilment_reads_collective=("fulfilment" not in b_nogain["fired"]),
        fulfilment_low_hedonic=(b_ful["happiness"] == 0 and b_ful["fulfilment_value"] > 0),
        pride_social_frame=(pride["pride"] == 1),
        social_gap_named=True)   # guilt/shame need fuller ToM; see RESULTS


# --------------------------------- G3 hedonic / eudaimonic dissociation
def g3_dissociation():
    """The parenthood case: an act that is individual-COSTLY but supergraph-
    BENEFICIAL. Sweep the sacrifice: individual happiness falls as supergraph
    fulfilment rises -- the two reference-frame value signals come APART."""
    eye, inner = _eye()
    hub, ep = _hub(eye, inner)
    curve = []
    base_benefit = 100
    for t in range(0, 11):
        cost = t * 40
        contribution = t * 40
        ap = _appraise(eye, inner, hub, appraised=1,
                       individual_benefit=base_benefit, individual_cost=cost,
                       supergraph_contribution=contribution,
                       collective_success=contribution, collective_success_prev=0)
        inner.run_rules()
        a = _attrs(eye, ap)
        curve.append(dict(t=t, individual_cost=cost, contribution=contribution,
                          happiness=int(a["happiness"]),
                          fulfilment=int(a["fulfilment_value"]),
                          total_value=int(a["total_value"])))
    eye.stop()
    happ = [c["happiness"] for c in curve]
    ful = [c["fulfilment"] for c in curve]
    happ_falls = all(happ[i] > happ[i + 1] for i in range(len(happ) - 1))
    ful_rises = all(ful[i] < ful[i + 1] for i in range(len(ful) - 1))
    # they DIVERGE: start with happiness >= fulfilment, end with happiness < fulfilment
    crosses = (happ[0] >= ful[0] and happ[-1] < ful[-1])
    return dict(curve=curve, happiness_falls=happ_falls,
                fulfilment_rises=ful_rises, signals_cross=crosses,
                dissociates=(happ_falls and ful_rises and crosses))


# -------------------------- G4 value-side disorder glass-box (psychopathy)
def g4_psychopathy():
    """Psychopathy = the w_supergraph knob at ~0: the agent still READS others
    (contribution computed) but does not VALUE them -> fulfilment collapses and
    the somatic brake on supergraph-harmful acts is removed. Pure-knob reversal.
    """
    # a genuine supergraph contribution
    contrib = dict(appraised=1, supergraph_contribution=300,
                   collective_success=300, collective_success_prev=0,
                   individual_benefit=200, individual_cost=0)
    # a supergraph-HARMFUL but individually-GOOD act (the instrumentalising test)
    harm = dict(appraised=1, supergraph_contribution=-800,
                collective_success=0, collective_success_prev=800,
                individual_benefit=500, individual_cost=0)

    def probe(w, scen):
        eye, inner = _eye()
        hub, ep = _hub(eye, inner, w_supergraph=w)
        ap = _appraise(eye, inner, hub, **scen)
        inner.run_rules()
        a = dict(_attrs(eye, ap))
        eye.stop()
        return a

    healthy_c = probe(1, contrib)
    psych_c = probe(0, contrib)
    restored_c = probe(1, contrib)
    healthy_h = probe(1, harm)
    psych_h = probe(0, harm)
    restored_h = probe(1, harm)

    # pure-knob reversibility: healthy vs restored are byte-identical
    def fp(a):
        return json.dumps({k: (round(v, 9) if isinstance(v, float) else v)
                           for k, v in sorted(a.items())}, sort_keys=True)

    return dict(
        healthy_contribution=dict(fulfilment_value=int(healthy_c["fulfilment_value"]),
                                  fired=[nm for nm in CORE if int(healthy_c.get("hit_" + nm, 0))],
                                  happiness=int(healthy_c["happiness"])),
        psychopath_contribution=dict(fulfilment_value=int(psych_c["fulfilment_value"]),
                                     fired=[nm for nm in CORE if int(psych_c.get("hit_" + nm, 0))],
                                     happiness=int(psych_c["happiness"])),
        # the knob collapses fulfilment but leaves INDIVIDUAL value untouched
        knob_collapses_fulfilment=(int(healthy_c["fulfilment_value"]) > 0
                                   and int(psych_c["fulfilment_value"]) == 0),
        individual_value_untouched=(int(healthy_c["happiness"]) == int(psych_c["happiness"])),
        reads_but_not_values=("fulfilment" in [nm for nm in CORE if int(healthy_c.get("hit_" + nm, 0))]
                              and "fulfilment" not in [nm for nm in CORE if int(psych_c.get("hit_" + nm, 0))]),
        # the somatic brake: healthy DECLINES the harmful act; psychopath ENDORSES it
        healthy_declines_harm=(int(healthy_h["act_endorsed"]) == 0),
        psychopath_endorses_harm=(int(psych_h["act_endorsed"]) == 1),
        pure_knob_reversible=(fp(healthy_c) == fp(restored_c)
                              and fp(healthy_h) == fp(restored_h)),
        harm_detail=dict(healthy_total=int(healthy_h["total_value"]),
                         psych_total=int(psych_h["total_value"])))


def g4_state_observed():
    """The state-knobs, OBSERVED behaviourally, reproduce recognised patterns —
    the behavioural 'factors' are SHADOWS of the state-knobs. depression = value
    suppressed across BOTH frames (mood_bias<<0); mania = inflated (mood_bias>>0).
    """
    # a normally-positive event (individual benefit + supergraph contribution)
    scen = dict(appraised=1, individual_benefit=200, individual_cost=0,
                supergraph_contribution=300, collective_success=300,
                collective_success_prev=0, valued_goal=1, goal_blocked=0,
                step=4, step_prev=1)
    harm = dict(appraised=1, supergraph_contribution=-800, collective_success=0,
                collective_success_prev=800, individual_benefit=500, individual_cost=0)

    def observe(label, ep_over, s):
        eye, inner = _eye()
        hub, ep = _hub(eye, inner, **ep_over)
        ap = _appraise(eye, inner, hub, **s)
        inner.run_rules()
        a = _attrs(eye, ap)
        eye.stop()
        return dict(state=label, knobs=ep_over,
                    happiness=int(a["happiness"]),
                    fulfilment=int(a["fulfilment_value"]),
                    total_value=int(a["total_value"]),
                    act_endorsed=int(a["act_endorsed"]),
                    valence=int(a["valence"]),
                    fired=[nm for nm in CORE if int(a.get("hit_" + nm, 0))])

    table = [
        observe("healthy", dict(), harm),
        observe("psychopathy(w=0)", dict(w_supergraph=0), harm),
        observe("healthy", dict(), scen),
        observe("depression(mood=-400)", dict(mood_bias=-400), scen),
        observe("mania(mood=+400)", dict(mood_bias=400), scen),
    ]
    # the OBSERVED factors are shadows of the STATE knobs
    healthy_harm = next(r for r in table if r["state"] == "healthy" and r["act_endorsed"] == 0)
    psych_harm = next(r for r in table if r["state"].startswith("psychopathy"))
    healthy_pos = [r for r in table if r["state"] == "healthy"][-1]
    depr = next(r for r in table if r["state"].startswith("depression"))
    mania = next(r for r in table if r["state"].startswith("mania"))
    return dict(
        table=table,
        psychopathy_removes_brake=(healthy_harm["act_endorsed"] == 0
                                   and psych_harm["act_endorsed"] == 1),
        depression_suppresses_both=(depr["happiness"] < healthy_pos["happiness"]
                                    and depr["fulfilment"] < healthy_pos["fulfilment"]
                                    and depr["total_value"] < 0),
        mania_inflates=(mania["total_value"] > healthy_pos["total_value"]))


# --------------------------------------------------------- G5 integer + default-off
def integer_audit():
    """AST-level audit. `Times` was moved OUT of this denylist (was: {"Div",
    "Times", "Exp", "Log", "Sqrt", "Sin", "Cos"}) — SUPERGRAPH_WEIGHT_MAGNITUDE
    _PREREG.md sec1: Times(Int,Int) is exactly integer-closed (term.rs's
    numeric_variadic, same closure property as Plus/Minus/Ashr, unlike
    Div/Exp/Log/Sqrt/Sin/Cos which are NOT integer-closed in general — this
    denylist now tests the property it actually claims, not just the op
    NAME). The real guarantee is integer_values_audit() below, widened in
    the same change to cover em_weighted_contribution's real w-range, not
    just this AST name-check."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "core_emotions.json")))
    float_terms = {"Div", "Exp", "Log", "Sqrt", "Sin", "Cos"}

    def ops(term, acc):
        if isinstance(term, dict):
            if "type" in term:
                acc.add(term["type"])
            for k in ("a", "b", "arg", "cond", "then", "other", "node"):
                if k in term:
                    ops(term[k], acc)
            for x in term.get("items", []):
                ops(x, acc)
        return acc
    report, bad = {}, {}
    for r in seed["rules"]:
        used = set()
        for eff in r.get("effects", []):
            if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                ops(eff[3].get("__term__", {}), used)
        ops(r.get("where", {}), used)
        report[r["name"]] = sorted(used)
        if used & float_terms:
            bad[r["name"]] = sorted(used & float_terms)
    return dict(report=report, offenders=bad, offender_count=len(bad),
                all_integer=(len(bad) == 0))


def integer_values_audit():
    """Every attribute the emotion rules PRODUCE is an exact integer (no float
    residue) across all G1 canonical appraisals, AND across
    em_weighted_contribution's real w/contribution range (the actual
    property Times(Int,Int)'s removal from integer_audit's denylist relies
    on -- checked at the VALUE level, not just the AST-name level)."""
    eye, inner = _eye()
    hub, ep = _hub(eye, inner)
    produced = ["threat_precision", "threat_persists", "learning_progress",
                "value_progress", "happiness", "fulfilment_value", "total_value",
                "act_endorsed", "n_fired", "action_tendency", "emotion",
                "valence", "arousal", "weighted_contribution"]
    bad = []
    for nm in CORE:
        ap = _appraise(eye, inner, hub, **CANON[nm])
        inner.run_rules()
        a = _attrs(eye, ap)
        for k in produced:
            v = a.get(k, 0.0)
            if float(v) != float(int(v)):
                bad.append((nm, k, v))
    # em_weighted_contribution's own real value-range: every w in {0} u [1,inf)
    # any live consumer uses PLUS bigville's real continuous (0,1) draws,
    # crossed with every live consumer's real contribution magnitude
    # (domains/core_emotions_weight.py's own named ceilings).
    for w in (0.0, 0.1, 0.25, 0.4785, 0.5, 0.75, 0.9114, 1.0, 2.0, 250.0):
        for contribution in (0.0, -3.0, 3.0, 60.0, -60.0, 300.0, -800.0, 987.0):
            hub2, ep2 = _hub(eye, inner, w_supergraph=w, mood_bias=0.0)
            ap2 = _appraise(eye, inner, hub2, appraised=1,
                            supergraph_contribution=contribution)
            inner.run_rules()
            v = _attrs(eye, ap2).get("weighted_contribution", 0.0)
            if float(v) != float(int(v)):
                bad.append(("w=%.4f,c=%.1f" % (w, contribution),
                           "weighted_contribution", v))
    eye.stop()
    return dict(non_integer_cells=len(bad), offenders=bad[:20],
                all_integer=(len(bad) == 0))


def source_audit():
    """The emotions are graph RULES reading the economy; the adapter runs no
    Python rule engine."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "core_emotions.json")))
    rules = {r["name"]: r for r in seed["rules"]}
    prods = {p["edge_type"] for p in seed["productions"]}
    # every core emotion has a rule that sets its own hit flag
    have_rule = all(("em_" + nm) in rules for nm in CORE)
    sets_hit = all(rules["em_" + nm]["effects"][0][2] == "hit_" + nm for nm in CORE)
    # fulfilment reads the SUPERGRAPH frame (w_supergraph on params) --
    # SUPERGRAPH_WEIGHT_MAGNITUDE_PREREG.md: em_fulfilment now reads
    # weighted_contribution (settled by em_weighted_contribution, order 1)
    # rather than raw supergraph_contribution directly, so the dependency
    # is checked one hop out: em_fulfilment reads weighted_contribution,
    # AND weighted_contribution's OWN rule reads both supergraph_contribution
    # and w_supergraph_q -- the supergraph frame is still reached, just
    # through the new named intermediate instead of inline.
    ful = rules["em_fulfilment"]
    wc = rules["em_weighted_contribution"]
    ful_reads_super = ("weighted_contribution" in json.dumps(ful["where"])
                       and "supergraph_contribution" in json.dumps(wc["effects"])
                       and "w_supergraph_q" in json.dumps(wc["effects"]))
    fv = rules["em_fulfilment_value"]
    fv_reads_w = "weighted_contribution" in json.dumps(fv)
    # the reused atoms are literally present
    tp = json.dumps(rules["em_threat_precision"])
    reuses_freshness = ("Ashr" in tp and "IDiv" in tp and "half_life" in tp)
    lp = json.dumps(rules["em_learning_progress"])
    reuses_lp = ("residual_prev" in lp and "Minus" in lp)
    jp = json.dumps(rules["em_joy_progress"])
    reuses_value = ("Ashr" in jp and "v_max" in jp)
    # adapter has no python rule engine
    src = open(os.path.abspath(__file__)).read()
    forbidden = ["gr" + ".run(", "graph_" + "rewrite", "make_" + "rule",
                 "gr." + "_match(", "gr." + "_apply("]
    forbidden_engine = any(tok in src for tok in forbidden)
    return dict(
        every_emotion_is_a_rule=have_rule, each_sets_own_hit=sets_hit,
        fulfilment_reads_supergraph=ful_reads_super, fulfilment_value_reads_w=fv_reads_w,
        reuses_196000_freshness=reuses_freshness, reuses_202000_learning_progress=reuses_lp,
        reuses_202000_value_atom=reuses_value,
        emotion_edges_registered=("has_appraisal" in prods and "has_emotion_params" in prods),
        adapter_runs_no_python_rule_engine=(not forbidden_engine))


def default_off_identity():
    """With NO EmotionHub/params created, an eye is byte-identical whether or not
    the core_emotions seed is loaded."""
    def run(load_emotions):
        eye, inner = _eye(load_emotions=load_emotions)
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
                  "EmotionHub": len(eye.substrate.nodes("EmotionHub")),
                  "Appraisal": len(eye.substrate.nodes("Appraisal"))}
        fp = json.dumps({"counts": counts, "cells": cells}, sort_keys=True)
        eye.stop()
        return fp, counts
    fp_off, c_off = run(False)
    fp_on, c_on = run(True)
    return dict(identical=(fp_off == fp_on), without_seed=c_off,
                with_seed_no_hub=c_on,
                no_emotion_nodes_created=(c_on.get("EmotionHub", 0) == 0
                                          and c_on.get("Appraisal", 0) == 0))


# --------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    # G1 circumplex — valence x arousal, one point per emotion
    ax = axes[0]
    for r in res["g1_emulation"]["rows"]:
        ax.scatter(r["valence"], r["arousal"], s=40, color="#2166ac")
        ax.annotate(r["emotion"], (r["valence"], r["arousal"]), fontsize=7,
                    xytext=(3, 3), textcoords="offset points")
    ax.axvline(0, color="#ccc", ls=":"); ax.set_xlim(-1.6, 1.6)
    ax.set_title("G1 circumplex — valence x arousal\n(read off in-graph)")
    ax.set_xlabel("valence (sign of progress/value)")
    ax.set_ylabel("arousal (magnitude)")

    # G3 dissociation curves
    ax = axes[1]
    c = res["g3_dissociation"]["curve"]
    ax.plot([x["t"] for x in c], [x["happiness"] for x in c], "-o",
            color="#b2182b", label="happiness (individual)")
    ax.plot([x["t"] for x in c], [x["fulfilment"] for x in c], "-o",
            color="#1b7837", label="fulfilment (supergraph)")
    ax.axhline(0, color="#999", ls=":")
    ax.set_title("G3 hedonic/eudaimonic DISSOCIATION\n(the parenthood case)")
    ax.set_xlabel("sacrifice (cost = contribution)")
    ax.set_ylabel("value"); ax.legend(fontsize=8)

    # G4 psychopathy knob — fulfilment collapses, happiness untouched
    ax = axes[2]
    g4 = res["g4_psychopathy"]
    labels = ["healthy\n(w=1)", "psychopath\n(w=0)"]
    happ = [g4["healthy_contribution"]["happiness"], g4["psychopath_contribution"]["happiness"]]
    ful = [g4["healthy_contribution"]["fulfilment_value"], g4["psychopath_contribution"]["fulfilment_value"]]
    x = range(len(labels))
    ax.bar([i - 0.2 for i in x], happ, width=0.4, color="#2166ac", label="happiness")
    ax.bar([i + 0.2 for i in x], ful, width=0.4, color="#1b7837", label="fulfilment")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_title("G4 psychopathy PURE KNOB\nfulfilment -> 0, individual value untouched")
    ax.set_ylabel("value"); ax.legend(fontsize=8)

    fig.tight_layout(); fig.savefig(path, dpi=110)
    plt.close(fig)


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    g1 = g1_emulation()
    g1d = g1_discriminators()
    g2 = g2_fulfilment()
    g3 = g3_dissociation()
    g4 = g4_psychopathy()
    g4s = g4_state_observed()
    ia = integer_audit()
    iva = integer_values_audit()
    sa = source_audit()
    doff = default_off_identity()

    criteria = dict(
        g1_all_tendencies_correct=g1["all_correct"],
        g1_one_fire_each=g1["one_fire_each"],
        g1_null_fires_none=g1["null_fires_none"],
        g1_discriminators=g1d["all_ok"],
        g2_fulfilment_fires=g2["fulfilment_fires"],
        g2_joy_not_fulfilment=g2["joy_not_fulfilment"],
        g2_fulfilment_not_joy=g2["fulfilment_not_joy"],
        g2_fulfilment_reads_collective=g2["fulfilment_reads_collective"],
        g2_fulfilment_low_hedonic=g2["fulfilment_low_hedonic"],
        g2_pride_social_frame=g2["pride_social_frame"],
        g3_happiness_falls=g3["happiness_falls"],
        g3_fulfilment_rises=g3["fulfilment_rises"],
        g3_signals_dissociate=g3["dissociates"],
        g4_knob_collapses_fulfilment=g4["knob_collapses_fulfilment"],
        g4_individual_value_untouched=g4["individual_value_untouched"],
        g4_reads_but_not_values=g4["reads_but_not_values"],
        g4_healthy_declines_harm=g4["healthy_declines_harm"],
        g4_psychopath_endorses_harm=g4["psychopath_endorses_harm"],
        g4_pure_knob_reversible=g4["pure_knob_reversible"],
        g4_psychopathy_removes_brake=g4s["psychopathy_removes_brake"],
        g4_depression_suppresses_both=g4s["depression_suppresses_both"],
        g4_mania_inflates=g4s["mania_inflates"],
        g4_state_observed_produces_factors=(g4s["psychopathy_removes_brake"]
                                            and g4s["depression_suppresses_both"]),
        g5_integer_native_terms=ia["all_integer"],
        g5_integer_native_values=iva["all_integer"],
        g5_default_off_byte_identical=doff["identical"],
        g5_default_off_no_nodes=doff["no_emotion_nodes_created"],
        source_every_emotion_is_a_rule=sa["every_emotion_is_a_rule"],
        source_reuses_atoms=(sa["reuses_196000_freshness"]
                             and sa["reuses_202000_learning_progress"]
                             and sa["reuses_202000_value_atom"]),
        source_no_python_rule_engine=sa["adapter_runs_no_python_rule_engine"],
    )

    res = dict(seed=SEED, g1_emulation=g1, g1_discriminators=g1d,
               g2_fulfilment=g2, g3_dissociation=g3, g4_psychopathy=g4,
               g4_state_observed=g4s, integer_audit=ia, integer_values_audit=iva,
               source_audit=sa, default_off=doff, criteria=criteria)

    with open(os.path.join(RESULTS, "core_emotions.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "core_emotions.png"))
    except Exception as e:                       # plotting is non-gating
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    print("ALL PASS:", all(r["criteria"].values()))
