#!/usr/bin/env python3
"""AUTHORING TOOL (block 207000) — emits seeds/drives.json + seeds/modulators.json.

This is a one-off seed-manifest builder (it EMITS graph data; it is NOT agent
runtime). It re-derives Bach/Dörner's PSI/MicroPsi emergent-emotion mechanism on
our integer substrate: a Drive system (urge/urgency/scale2-decay/pleasure) sets a
small set of global cognitive MODULATORS (valence, arousal, resolution,
selection-threshold, securing-rate, competence), and named emotions are REGIONS
in that modulator space (read together with the leading drive's object /
directedness). This REPLACES 204000's 11 authored per-emotion appraisal rules
with ~6 modulator update rules + ~13 region predicates over the shared axes.

Integer-native, NO Rust, NO new Term (Plus/Minus/Times/IDiv/Ashr/Abs/Max/Min/
IfThenElse/Gt/Gte/Lt/Lte/And/Or/Not/Eq + the aggregate Sum/Neighbours, all
present in term.rs today). Default-OFF: every rule guards on
ModulatorState.enabled; absent it every existing path is byte-identical.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

# ----------------------------------------------------------------- term helpers
def V(name):                      return {"type": "Var", "name": name}
def L(v):                         return {"type": "Lit", "value": float(v)}
def A(var, key):                  return {"type": "Attr", "node": V(var), "key": key}
def Eq(a, b):                     return {"type": "Eq", "a": a, "b": b}
def Gt(a, b):                     return {"type": "Gt", "a": a, "b": b}
def Gte(a, b):                    return {"type": "Gte", "a": a, "b": b}
def Lt(a, b):                     return {"type": "Lt", "a": a, "b": b}
def Lte(a, b):                    return {"type": "Lte", "a": a, "b": b}
def And(*xs):                     return {"type": "And", "items": list(xs)}
def Or(*xs):                      return {"type": "Or", "items": list(xs)}
def Not(x):                       return {"type": "Not", "arg": x}
def Plus(*xs):                    return {"type": "Plus", "items": list(xs)}
def Minus(a, b):                  return {"type": "Minus", "a": a, "b": b}
def Times(*xs):                   return {"type": "Times", "items": list(xs)}
def IDiv(a, b):                   return {"type": "IDiv", "a": a, "b": b}
def Ashr(a, b):                   return {"type": "Ashr", "a": a, "b": b}
def Abs(x):                       return {"type": "Abs", "arg": x}
def Neg(x):                       return {"type": "Neg", "arg": x}
def Maxx(*xs):                    return {"type": "Max", "items": list(xs)}
def Minn(*xs):                    return {"type": "Min", "items": list(xs)}
def Ite(c, t, o):                 return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Neigh(var, edge):             return {"type": "Neighbours", "node": V(var), "edge_type": edge, "any_type": False}
def Sum(source, vn, value):       return {"type": "Sum", "source": source, "var_name": vn, "value": value}
def T(term):                      return {"__term__": term}


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": "hard_realtime", "match": match,
            "where": where, "effects": effects}


def prod(provenance, src_type, src_var, edge, tgt_type, tgt_var):
    return {"provenance": provenance,
            "src": {"type": src_type, "var": src_var},
            "edge_type": edge,
            "tgt": {"type": tgt_type, "var": tgt_var}}


# guard: this drive is bound to an ENABLED ModulatorState
DRIVE_MATCH = [["ms", "has_active_drive", "d"]]
def drive_guard(*extra):
    return And(Eq(A("ms", "enabled"), L(1)), *extra)


def sign(x):
    return Ite(Gt(x, L(0)), L(1), Ite(Lt(x, L(0)), L(-1), L(0)))


# =============================================================== seeds/drives.json
def build_drives():
    SCALE = "scale"  # urgency scale, an attr on the drive (personality param)

    rules = []

    # drive_decay -- the drive IS a decaying held quantity: reuse the 196000
    # scale2 atom c_d <- Ashr(c_d, IDiv(now - last_tend, half_life)). Runs at most
    # ONCE per epoch (where-guard now_epoch > last_tend); inert when now == last_tend
    # (Ashr by 0). Kept explicit so a drive left untended decays toward v_0 by
    # exactly the staleness_decay machinery, then stamps last_tend = now_epoch.
    rules.append(rule(
        "drive_decay", 0, DRIVE_MATCH,
        drive_guard(Gt(A("d", "now_epoch"), A("d", "last_tend"))),
        [["set_attr", "d", "c_d", T(
            Ashr(A("d", "c_d"),
                 IDiv(Minus(A("d", "now_epoch"), A("d", "last_tend")),
                      Maxx(L(1), A("d", "half_life")))))],
         ["set_attr", "d", "last_tend", T(A("d", "now_epoch"))]]))

    # drive_urge = |v_d - c_d|
    rules.append(rule(
        "drive_urge", 1, DRIVE_MATCH, drive_guard(),
        [["set_attr", "d", "urge", T(Abs(Minus(A("d", "v_d"), A("d", "c_d"))))]]))

    # drive_urgency = |v_d - c_d| * SCALE / max(1, |v_d - v_0|)
    rules.append(rule(
        "drive_urgency", 2, DRIVE_MATCH, drive_guard(),
        [["set_attr", "d", "urgency", T(
            IDiv(Times(Abs(Minus(A("d", "v_d"), A("d", "c_d"))), A("d", SCALE)),
                 Maxx(L(1), Abs(Minus(A("d", "v_d"), A("d", "v_0"))))))]]))

    # drive_threat_precision -- reuse the 196000 freshness atom on the drive's
    # threat channel: precision = Ashr(threat_c0, IDiv(now - last_refresh, half))
    # A SHORT threat_half_life => precision decays below t_present => FEAR;
    # a LONG one => it persists => ANXIETY. The fear<->anxiety minimal pair.
    rules.append(rule(
        "drive_threat_precision", 1, DRIVE_MATCH, drive_guard(Eq(A("d", "threat"), L(1))),
        [["set_attr", "d", "threat_precision", T(
            Ashr(A("d", "threat_c0"),
                 IDiv(Minus(A("d", "threat_now_epoch"), A("d", "threat_last_refresh")),
                      Maxx(L(1), A("d", "threat_half_life")))))]]))

    # drive_threat_persist = precision >= t_present  (199000 present readout)
    rules.append(rule(
        "drive_threat_persist", 2, DRIVE_MATCH, drive_guard(Eq(A("d", "threat"), L(1))),
        [["set_attr", "d", "threat_persists", T(
            Ite(Gte(A("d", "threat_precision"), A("d", "t_present")), L(1), L(0)))]]))

    # drive_pleasure / drive_displeasure = sign of delta c_d (the reinforcers)
    rules.append(rule(
        "drive_pleasure", 2, DRIVE_MATCH, drive_guard(),
        [["set_attr", "d", "pleasure", T(
            Maxx(L(0), Minus(A("d", "c_d"), A("d", "c_d_prev"))))]]))
    rules.append(rule(
        "drive_displeasure", 2, DRIVE_MATCH, drive_guard(),
        [["set_attr", "d", "displeasure", T(
            Maxx(L(0), Minus(A("d", "c_d_prev"), A("d", "c_d"))))]]))

    # drive_arousal_contrib -- this drive's contribution to arousal. A threat
    # drive contributes its (decayed) precision (so fear=low, anxiety=high fall
    # out of the half-life); any other drive contributes urge*urgency/SCALE.
    rules.append(rule(
        "drive_arousal_contrib", 3, DRIVE_MATCH, drive_guard(),
        [["set_attr", "d", "arousal_contrib", T(
            Ite(Eq(A("d", "threat"), L(1)),
                A("d", "threat_precision"),
                IDiv(Times(A("d", "urge"), A("d", "urgency")), A("d", SCALE))))]]))

    # affiliation -- legitimacy signal ingest as a rule: praise (legitimacy=+1)
    # moves c_d toward v_d by gain*social_weight; reproach (legitimacy=-1) moves
    # it away by loss*social_weight. Affiliation is the virtual social currency.
    rules.append(rule(
        "drive_affiliation_legitimacy", 0,
        [["ms", "has_active_drive", "d"]],
        drive_guard(Eq(A("d", "is_affiliation"), L(1)), Not(Eq(A("d", "legitimacy"), L(0)))),
        [["set_attr", "d", "c_d", T(
            Plus(A("d", "c_d"),
                 Times(A("d", "legitimacy"),
                       Ite(Gt(A("d", "legitimacy"), L(0)), A("d", "gain"), A("d", "loss")),
                       A("d", "social_weight"))))],
         ["set_attr", "d", "legitimacy", T(L(0))]]))

    seed = {
        "id": "drives", "version": "1.0.0", "self_load_only": True,
        "depends_on": [], "area": "retina",
        "description": (
            "THE DRIVE SYSTEM (block 207000) -- Dorner/Bach PSI/MicroPsi needs as "
            "first-class graph nodes. A Drive{name, target v_d, current c_d, critical "
            "v_0, weight, decay, gain, loss, half_life} with the MicroPsi demand "
            "equations as integer rules: urge = |v_d-c_d| (drive_urge); urgency = "
            "|v_d-c_d|*SCALE / max(1,|v_d-v_0|) (drive_urgency); the drive IS a decaying "
            "held quantity -- c_d <- Ashr(c_d, IDiv(now-last_tend, half_life)) reuses the "
            "196000 staleness_decay scale2 atom (drive_decay); pleasure/displeasure = sign "
            "of delta c_d, the motivational reinforcers. A threat drive carries the 196000 "
            "freshness atom on its threat channel (drive_threat_precision/persist): a SHORT "
            "threat_half_life decays the precision below t_present (FEAR), a LONG one persists "
            "(ANXIETY) -- the fear<->anxiety minimal pair, the SAME PTSD knob. AFFILIATION is "
            "the social currency: a legitimacy_signal ingest (praise +gain, reproach -loss, "
            "scaled by the source's social_weight) is a rule (drive_affiliation_legitimacy); "
            "NURTURING is its complement and its ABSENCE is the 204000 w_supergraph~0 "
            "psychopathy knob (convergent glass-box). Each drive exposes an arousal_contrib "
            "for the modulator layer. Integer-native, NO Rust, NO new Term. OFF by default: "
            "every rule guards on the bound ModulatorState.enabled the measure adapter creates "
            "only on opt-in; absent it every existing path is byte-identical."),
        "microtheory": {
            "name": "drives",
            "description": (
                "A minimal orthogonal set of needs (demands); goals are learned situations "
                "that satisfy/frustrate them. urge=|v_d-c_d|, urgency normalises by proximity "
                "to the critical extreme; the drive is a decaying held quantity (the 196000 "
                "scale2 atom); pleasure/displeasure = sign of delta c_d. Affiliation is the "
                "social currency, nurturing its complement (absence = psychopathy).")},
        "nodes": [], "edges": [],
        "productions": [
            prod("seed:drives:modstate-active-drive", "ModulatorState", "ms",
                 "has_active_drive", "Drive", "d"),
            prod("seed:drives:modstate-leading-drive", "ModulatorState", "ms",
                 "leading_drive", "Drive", "d"),
        ],
        "rules": rules,
    }
    return seed


# ============================================================ seeds/modulators.json
# leading drive bound to modstate
LEAD_MATCH = [["ms", "has_active_drive", "d"], ["ms", "leading_drive", "d"]]
def mod_guard(*extra):
    return And(Eq(A("ms", "enabled"), L(1)), *extra)


# emotion codes (match 204000 TEND)
TEND = {"surprise": 1, "fear": 2, "anxiety": 3, "anger": 4, "frustration": 5,
        "disgust": 6, "joy": 7, "sadness": 8, "curiosity": 9, "boredom": 10,
        "fulfilment": 11}
# blends (free states) get their own codes >= 20 so they never collide with the
# 11 emulation tendencies; they are distinct REGIONS of the same space.
BLEND = {"bliss": 21, "angst": 22, "grief": 23}


def build_modulators():
    rules = []

    # ---- competence: running measure of need-satisfaction success. Runs at most
    # ONCE per graph epoch (where-guard epoch > competence_epoch), so re-ticking a
    # settled state does not double-count learning-progress. On the FIRST epoch
    # (competence_epoch < 0) it integrates from competence_base (the standing
    # accumulator the adapter carries across ticks); on later epochs it integrates
    # from the current competence -- the general-competence heuristic, a running
    # sum of learning-progress. Then it stamps competence_epoch = epoch.
    rules.append(rule(
        "mod_competence", 1, LEAD_MATCH,
        mod_guard(Gt(A("ms", "epoch"), A("ms", "competence_epoch"))),
        [["set_attr", "ms", "competence", T(
            Plus(Ite(Lt(A("ms", "competence_epoch"), L(0)),
                     A("ms", "competence_base"),
                     A("ms", "competence")),
                 A("d", "learning_progress")))],
         ["set_attr", "ms", "competence_epoch", T(A("ms", "epoch"))]]))

    # ---- valence = Sum(pleasure) - Sum(displeasure) - Sum(urge), over active drives
    rules.append(rule(
        "mod_valence", 4, [["ms", "has_active_drive", "d0"]], mod_guard(),
        [["set_attr", "ms", "valence_raw", T(
            Minus(Minus(Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "pleasure")),
                        Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "displeasure"))),
                  Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "urge"))))],
         ["set_attr", "ms", "valence", T(
            sign(Minus(Minus(Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "pleasure")),
                             Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "displeasure"))),
                       Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "urge")))))]]))

    # ---- arousal = Sum_d(arousal_contrib) over active drives, EXCEPT an
    # un-appraised leading spike (surprise) is the raw residual (pre-appraisal
    # orienting arousal). Then the pre-registered 3-way band.
    arousal_expr = Ite(Eq(A("d", "appraised"), L(0)),
                       A("d", "residual"),
                       Sum(Neigh("ms", "has_active_drive"), "dd", A("dd", "arousal_contrib")))
    rules.append(rule(
        "mod_arousal", 4, LEAD_MATCH, mod_guard(),
        [["set_attr", "ms", "arousal", T(arousal_expr)],
         ["set_attr", "ms", "arousal_band", T(
             Ite(Gte(arousal_expr, A("ms", "band_hi")), L(2),
                 Ite(Gte(arousal_expr, A("ms", "band_mid")), L(1), L(0))))]]))

    # ---- resolution = (base + abstraction_bias) + IDiv(urgency(leading), res_urg_div)
    #                   - IDiv(arousal, res_ar_div)
    # inverse of arousal (high arousal -> low resolution), up by leading urgency.
    #
    # TRAIT SET-POINT BIAS (abstraction -> resolution baseline): abstraction_bias
    # is a CONSTANT ADDITIVE OFFSET folded into the res_base position -- it shifts
    # the resolution EQUILIBRIUM (the set-point the drives regulate around), it is
    # NOT a multiplier and NOT inside the urgency/arousal terms. A crystallised
    # cognitive-style trait (written onto the ModulatorState by the trait<->MicroPsi
    # bridge in a later task) raises/lowers the baseline: high abstraction => higher
    # resolution baseline => reaches for more abstract/broad processing. Because the
    # +urgency/-arousal terms are UNCHANGED, the drive dynamics still regulate AROUND
    # the shifted baseline exactly as before -- the offset cannot fight regulation or
    # oscillate. Missing attr reads Value::None => additive identity 0 (Plus), so with
    # no bridge/no disposition the formula is ALGEBRAICALLY IDENTICAL to today.
    rules.append(rule(
        "mod_resolution", 5, LEAD_MATCH, mod_guard(),
        [["set_attr", "ms", "resolution", T(
            Minus(Plus(A("ms", "res_base"), A("ms", "abstraction_bias"),
                       IDiv(A("d", "urgency"), A("ms", "res_urg_div"))),
                  IDiv(A("ms", "arousal"), A("ms", "res_ar_div"))))]]))

    # ---- selection threshold = strength(leading)*urgency(leading)/SCALE
    #      - sel_k*(competence_full - competence) - openness_bias: a bonus to the
    #      current motive; DOWN by low competence (low competence -> more
    #      flexible/searching).
    #
    # TRAIT SET-POINT BIAS (openness -> selection-threshold baseline): openness_bias
    # is a CONSTANT ADDITIVE OFFSET SUBTRACTED from the threshold -- it shifts the
    # commit/mint EQUILIBRIUM, not a multiplier and not inside the urgency/competence
    # terms. High openness => LOWER selection threshold => commits/mints more readily.
    # The weight*urgency and competence terms are UNCHANGED, so the drives still
    # regulate the threshold AROUND the shifted baseline. Missing attr => 0 (Minus's
    # subtrahend contributes the additive identity), so no-bridge is byte-identical.
    rules.append(rule(
        "mod_sel_threshold", 5, LEAD_MATCH, mod_guard(),
        [["set_attr", "ms", "sel_threshold", T(
            Minus(Minus(IDiv(Times(A("d", "weight"), A("d", "urgency")), A("ms", "sel_div")),
                        Times(A("ms", "sel_k"),
                              Minus(A("ms", "competence_full"), A("ms", "competence")))),
                  A("ms", "openness_bias")))]]))

    # ---- securing rate = uncertainty + (competence_full - competence)
    #      - sec_k*importance(leading) + skepticism_bias: outward vigilance, UP by
    #      uncertainty & low competence, DOWN by a high-importance leading motive.
    #
    # TRAIT SET-POINT BIAS (skepticism -> securing baseline): skepticism_bias is a
    # CONSTANT ADDITIVE OFFSET ADDED to securing -- it shifts the vigilance
    # EQUILIBRIUM, not a multiplier and not inside the uncertainty/competence terms.
    # High skepticism => MORE outward vigilance/demand (a higher securing baseline).
    # The uncertainty, competence and importance terms are UNCHANGED, so the drives
    # still regulate securing AROUND the shifted baseline. Missing attr => 0 (Plus's
    # additive identity), so no-bridge is byte-identical.
    rules.append(rule(
        "mod_securing", 6, LEAD_MATCH, mod_guard(),
        [["set_attr", "ms", "securing", T(
            Plus(Minus(Plus(A("d", "exploration_urge"),
                            Minus(A("ms", "competence_full"), A("ms", "competence"))),
                       Times(A("ms", "sec_k"), A("d", "weight"))),
                 A("ms", "skepticism_bias")))]]))

    # ---- emx_epoch_reset -- at each NEW graph epoch (epoch > emotion_epoch) clear
    # the per-tick read-off cells (all hit_*, emotion, action_tendency, n_fired,
    # n_blend) and stamp emotion_epoch = epoch, re-opening the read-off lifecycle
    # inside the graph so the region predicates classify the fresh stable state.
    # Order 9: after the modulator updates, before the region predicates (order 10).
    rules.append(rule(
        "emx_epoch_reset", 9, LEAD_MATCH,
        mod_guard(Gt(A("ms", "epoch"), A("ms", "emotion_epoch"))),
        [["set_attr", "ms", "hit_" + nm, 0.0] for nm in
         list(TEND) + list(BLEND)]
        + [["set_attr", "ms", "emotion", 0.0],
           ["set_attr", "ms", "action_tendency", 0.0],
           ["set_attr", "ms", "n_fired", 0.0],
           ["set_attr", "ms", "n_blend", 0.0],
           ["set_attr", "ms", "emotion_epoch", T(A("ms", "epoch"))]]))

    # ========================= REGION PREDICATES (replace the 11 authored appraisals)
    # Each reads the MODULATOR VECTOR + the leading drive's object/directedness.
    # Directedness (fear/anger/grief AT an object vs joy/bliss/angst undirected)
    # is supplied by the bound drive's object flags, NOT the modulators alone.
    def region(name, order, extra, code=None):
        code = code if code is not None else TEND.get(name, BLEND.get(name))
        rules.append(rule("emx_" + name, order, LEAD_MATCH, mod_guard(*extra),
                          [["set_attr", "ms", "hit_" + name, T(L(1))]]))

    # surprise -- un-appraised residual spike, undirected, arousal high-ish
    region("surprise", 10, [Eq(A("d", "appraised"), L(0)),
                            Gt(A("d", "residual"), A("ms", "residual_thresh"))])
    # fear -- neg valence, threat-directed, precision DECAYED (< present), low competence
    region("fear", 10, [Eq(A("d", "appraised"), L(1)), Lt(A("ms", "valence"), L(0)),
                        Eq(A("d", "threat"), L(1)), Eq(A("d", "threat_persists"), L(0)),
                        Lt(A("ms", "competence"), A("ms", "competence_lo"))])
    # anxiety -- neg valence, threat present but PERSISTS, securing high, low competence
    region("anxiety", 10, [Eq(A("d", "appraised"), L(1)), Lt(A("ms", "valence"), L(0)),
                           Eq(A("d", "threat"), L(1)), Eq(A("d", "threat_persists"), L(1)),
                           Gt(A("ms", "securing"), A("ms", "securing_hi")),
                           Lt(A("ms", "competence"), A("ms", "competence_lo"))])
    # anger -- valued goal blocked, blocker present; high arousal, low resolution, high sel_threshold
    region("anger", 10, [Eq(A("d", "appraised"), L(1)), Eq(A("d", "valued_goal"), L(1)),
                         Eq(A("d", "goal_blocked"), L(1)), Eq(A("d", "blocker_present"), L(1)),
                         Gte(A("ms", "arousal_band"), L(2)),
                         Lt(A("ms", "resolution"), A("ms", "resolution_lo")),
                         Gt(A("ms", "sel_threshold"), A("ms", "sel_threshold_hi"))])
    # frustration -- as anger but NO blocker
    region("frustration", 10, [Eq(A("d", "appraised"), L(1)), Eq(A("d", "valued_goal"), L(1)),
                               Eq(A("d", "goal_blocked"), L(1)), Eq(A("d", "blocker_present"), L(0)),
                               Gte(A("ms", "arousal_band"), L(2))])
    # disgust -- contamination, neg valence
    region("disgust", 10, [Eq(A("d", "appraised"), L(1)), Eq(A("d", "contamination"), L(1)),
                           Lt(A("ms", "valence"), L(0))])
    # joy -- pos valence, appetitive value_progress>0, arousal NOT low (mid/high)
    region("joy", 10, [Eq(A("d", "appraised"), L(1)), Gt(A("ms", "valence"), L(0)),
                       Gt(A("d", "value_progress"), L(0)), Eq(A("d", "goal_blocked"), L(0)),
                       Gte(A("ms", "arousal_band"), L(1)),
                       Eq(A("d", "supergraph_value"), L(0)),
                       Eq(A("d", "loss_object"), L(0)), Eq(A("d", "explore"), L(0))])
    # bliss (NEW blend) -- pos valence, arousal LOW, resolution HIGH (distinct from joy)
    region("bliss", 10, [Eq(A("d", "appraised"), L(1)), Gt(A("ms", "valence"), L(0)),
                         Eq(A("ms", "arousal_band"), L(0)),
                         Gt(A("ms", "resolution"), A("ms", "resolution_hi")),
                         Eq(A("d", "value_progress"), L(0)), Eq(A("d", "explore"), L(0)),
                         Eq(A("d", "supergraph_value"), L(0))])
    # sadness -- neg valence, arousal low, resolution high, value falling, undirected (no loss object)
    region("sadness", 10, [Eq(A("d", "appraised"), L(1)), Lt(A("ms", "valence"), L(0)),
                           Eq(A("ms", "arousal_band"), L(0)),
                           Gt(A("ms", "resolution"), A("ms", "resolution_hi")),
                           Lt(A("d", "value_progress"), L(0)),
                           Eq(A("d", "loss_object"), L(0)),
                           Eq(A("d", "threat"), L(0)), Eq(A("d", "was_engaged"), L(0))])
    # grief (NEW blend) -- the sadness region DIRECTED at a specific loss object
    region("grief", 10, [Eq(A("d", "appraised"), L(1)), Lt(A("ms", "valence"), L(0)),
                         Eq(A("ms", "arousal_band"), L(0)),
                         Gt(A("ms", "resolution"), A("ms", "resolution_hi")),
                         Lt(A("d", "value_progress"), L(0)),
                         Eq(A("d", "loss_object"), L(1))])
    # curiosity -- pos valence, exploring, learning_progress>0
    region("curiosity", 10, [Eq(A("d", "appraised"), L(1)), Gt(A("ms", "valence"), L(0)),
                             Eq(A("d", "explore"), L(1)), Gt(A("d", "learning_progress"), L(0))])
    # boredom -- arousal low, learning_progress -> 0, engaged
    region("boredom", 10, [Eq(A("d", "appraised"), L(1)), Eq(A("ms", "arousal_band"), L(0)),
                           Eq(A("d", "explore"), L(1)),
                           Eq(A("d", "learning_progress"), L(0)), Eq(A("d", "was_engaged"), L(1))])
    # fulfilment -- pos valence, supergraph value>0 (w_supergraph gates)
    region("fulfilment", 10, [Eq(A("d", "appraised"), L(1)), Gt(A("ms", "valence"), L(0)),
                              Gt(A("d", "supergraph_value"), L(0)),
                              Gt(A("ms", "w_supergraph"), L(0))])
    # angst (NEW blend) -- undirected anxiety: neg valence, NO threat object, high
    # uncertainty, securing high, low competence, undirected
    region("angst", 10, [Eq(A("d", "appraised"), L(1)), Lt(A("ms", "valence"), L(0)),
                         Eq(A("d", "threat"), L(0)),
                         Gt(A("d", "exploration_urge"), A("ms", "uncertainty_hi")),
                         Gt(A("ms", "securing"), A("ms", "securing_hi")),
                         Lt(A("ms", "competence"), A("ms", "competence_lo")),
                         Eq(A("d", "valued_goal"), L(0)), Eq(A("d", "contamination"), L(0))])

    # ---- n_fired = sum of the 11 EMULATION hits (blends counted separately)
    hit_sum = Plus(*[A("ms", "hit_" + nm) for nm in TEND])
    rules.append(rule("emx_nfired", 12, LEAD_MATCH, mod_guard(),
                      [["set_attr", "ms", "n_fired", T(hit_sum)]]))
    blend_sum = Plus(*[A("ms", "hit_" + nm) for nm in BLEND])
    rules.append(rule("emx_nblend", 12, LEAD_MATCH, mod_guard(),
                      [["set_attr", "ms", "n_blend", T(blend_sum)]]))

    # ---- read-off: action_tendency = the priority ladder over the 11 hits
    order_names = ["surprise", "fear", "anxiety", "anger", "frustration",
                   "disgust", "joy", "sadness", "curiosity", "boredom", "fulfilment"]
    tend_ladder = L(0)
    for nm in reversed(order_names):
        tend_ladder = Ite(Eq(A("ms", "hit_" + nm), L(1)), L(TEND[nm]), tend_ladder)
    # emotion label ladder incl blends
    all_names = order_names + ["bliss", "angst", "grief"]
    codes = {**TEND, **BLEND}
    emo_ladder = L(0)
    for nm in reversed(all_names):
        emo_ladder = Ite(Eq(A("ms", "hit_" + nm), L(1)), L(codes[nm]), emo_ladder)
    rules.append(rule("emx_readoff", 13, LEAD_MATCH, mod_guard(),
                      [["set_attr", "ms", "action_tendency", T(tend_ladder)],
                       ["set_attr", "ms", "emotion", T(emo_ladder)]]))

    seed = {
        "id": "modulators", "version": "1.0.0", "self_load_only": True,
        "depends_on": ["drives", "staleness_decay", "learning_progress_curiosity"],
        "area": "retina",
        "description": (
            "THE MODULATOR SPACE + EMERGENCE-BY-REGION (block 207000) -- re-derives "
            "Bach/Dorner PSI/MicroPsi: emotions are REGIONS in a small space of global "
            "cognitive modulators, the modulators SET by the 207000 drive system. Six "
            "integer modulator update rules on a ModulatorState (one per EmotionHub): "
            "valence = Sum(pleasure)-Sum(displeasure)-Sum(urge) over active drives (sign = "
            "circumplex x); arousal = Sum_d(arousal_contrib) (a threat drive contributes its "
            "196000-decayed precision, so fear=low/anxiety=high fall out of the half-life; an "
            "un-appraised leading spike is the raw residual -- pre-appraisal orienting) + a "
            "pre-registered 3-way band; resolution = base + urgency(leading) - k*arousal "
            "(inverse of arousal, NEW global scope of the 198000 LOD atom); sel_threshold = "
            "weight*urgency(leading)/SCALE - k*(1-competence) (resist-switch bonus, NEW half "
            "of the 202000 commit-net); securing = uncertainty + (1-competence) - k*importance "
            "(outward vigilance, NEW); competence = running accumulator seeded from the 202000 "
            "learning-progress (NEW). Then ~14 REGION predicates read the modulator vector + "
            "the leading drive's object/directedness and set action_tendency -- these REPLACE "
            "204000's 11 authored per-emotion appraisals. Directedness (fear/anger/grief at an "
            "object vs joy/bliss/angst undirected) comes from the bound drive, not the "
            "modulators alone. Blends bliss (pos/low-arousal/high-resolution), angst "
            "(undirected anxiety), grief (directed sadness) fall out as DISTINCT regions with "
            "no new modulator/atom/drive. Integer-native, NO Rust, NO new Term (Sum/Neighbours "
            "aggregate the drives). OFF by default: every rule guards on ModulatorState.enabled "
            "the measure adapter creates only on opt-in; absent it every existing path is "
            "byte-identical. The parameter drop: 11 authored appraisal rules -> 6 modulator "
            "updates + ~14 region predicates over shared axes, blends free."),
        "microtheory": {
            "name": "modulators",
            "description": (
                "Modulators are global configuration parameters of cognition set by the urge "
                "configuration; they are NOT emotions -- affects are REGIONS within the "
                "modulator space. valence/arousal/resolution/selection-threshold/securing/"
                "competence, computed from the drive system; named emotions and their "
                "directed/undirected blends are co-occurrence regions read together with the "
                "leading drive's object.")},
        "nodes": [], "edges": [],
        "productions": [
            prod("seed:modulators:hub-modstate", "EmotionHub", "hub",
                 "has_modulator_state", "ModulatorState", "ms"),
        ],
        "rules": rules,
    }
    return seed


def main():
    drives = build_drives()
    mods = build_modulators()
    with open(os.path.join(SEEDS, "drives.json"), "w") as fh:
        json.dump(drives, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(SEEDS, "modulators.json"), "w") as fh:
        json.dump(mods, fh, indent=1)
        fh.write("\n")
    print("wrote seeds/drives.json (%d rules) and seeds/modulators.json (%d rules)"
          % (len(drives["rules"]), len(mods["rules"])))


if __name__ == "__main__":
    main()
