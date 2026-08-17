"""Builds seeds/affect_coupling.json -- affect-coupling Phase 2
(AFFECT_COUPLING_SHAPE_PREREG.md): the single reusable Rule that couples
a resident's PSI modulator state + disposition gains onto ANY node
carrying a small affinity-tag shape, matched generically (MatchEdge
carries no node-type constraint -- confirmed in
runners/dsl/src/rewrite.rs:31 before this was written), not a
coefficient hand-authored per decision type.

Composes existing DSL Terms only (Sum/Neighbours/AttrByName/Attr/Times/
Plus/Min/Div/Eq) -- zero new Rust, per CLAUDE.md's own bar. OFF by
default (coupling_on guard) -- an agent's own AffectCoupler.coupling_on
must be set to 1.0 before either rule does anything.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "affect_coupling.json")


# ---- Term constructors (mechanical JSON shape, matching the house
# convention already used by scripts/abusive_u0_intent_seed_build.py and
# every other hand-authored seed builder in this tree) --------------------
def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def attr_by_name(node, name_term):
    return {"type": "AttrByName", "node": var(node), "name": name_term}


def lit(v):
    if isinstance(v, str):
        return {"type": "Lit", "value": v}
    return {"type": "Lit", "value": float(v)}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def times(*items):
    return {"type": "Times", "items": list(items)}


def min_(*items):
    return {"type": "Min", "items": list(items)}


def div(a, b):
    return {"type": "Div", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def log_(arg):
    return {"type": "Log", "arg": arg}


def exp_(arg):
    return {"type": "Exp", "arg": arg}


def round_(value, ndigits=0):
    return {"type": "Round", "value": value, "ndigits": lit(ndigits)}


def neighbours(node, edge_type):
    return {"type": "Neighbours", "node": var(node), "edge_type": edge_type, "any_type": False}


def sum_(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name, "value": value}


def term(t):
    return {"__term__": t}


def rule(name, match, where, effects, *, comment=""):
    return {"name": name, "batch": False, "comment": comment,
            "match": match, "where": where, "effects": effects}


# P0: the coercion guard (EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md sec0a-iv
# / term.rs:8537-8596, numeric_variadic's Value::None arm) -- a missing
# attr contributes the identity to Plus (0) but to Times (1). Every
# affinity/state/bias/gain read that MIGHT be absent on an untagged node
# must be P0-wrapped, or an untagged node silently gets a nonzero bias.
def p0(t):
    return plus(t, lit(0.0))


# ---------------------------------------------------- 1. disposition gains
# Normalises the raw _PARAM_SPEC traits (transported onto AffectCoupler by
# worlds/bigville_ocelot_adapter.py::_ensure_affect_coupler, Phase 1) into
# gains, deliberately UNCAPPED (see the rule's own comment below for why).
# mood_bias/trait_valence are ADDITIVE and used
# directly -- no gain to resolve for them (see the design doc sec4a: only
# arousal/hostile_weight/charm_weight/w_spite are ratio-to-a-population-
# mean gains; mood_bias/valence are trait offsets, already correctly
# additive per core_emotions.json's own em_happiness formula). spite_gain
# (Phase 4, TARGET_SCOPED_COUPLING_PREREG.md) gates removal_desire_for's
# crystallising alpha specifically -- distinct from hostile_gain (spite is
# accepting one's own cost for another's loss, not provocation
# reactivity; conflating them would violate the amygdala-dissociation
# modularity constraint the same way merging Concepts would).
#
# Each gain is now a ROUND-TRIP through a canonical, integer-quantized
# LOG-WEIGHT (AFFECT_COUPLING_SHAPE_PREREG.md's log-weight correction):
# gain = trait/ref computed via Div previously stored the raw CONTINUOUS
# ratio directly on graph-resident state -- a float in-frame, the exact
# category error CLAUDE.md's "BASE-AS-DIMENSION" section names. The
# log-weight (log_*_weight, rounded to the nearest 1/log_weight_scale
# nepers) is the real, declared, bounded-precision datum; the *_gain
# attrs are a derived float CACHE re-exponentiated from it, read by
# psi_couple_affect_to_tagged exactly as before (that rule is UNCHANGED).
# log_weight_scale is DYNAMIC graph data (worlds/bigville_ocelot_
# adapter.py::_derive_log_weight_scale), never a Lit baked into this
# rule -- derived from two real anchors (the generator's own _draw_clip
# rounding precision; SPEECH_MENU's own smallest base_value gap), not a
# hand-picked number.
#
# Zero-valued traits are handled as ABSENCE, not a floor: Log(0)=-inf
# (term.rs) cannot round-trip through persistence (a non-finite Float
# attr silently serializes to JSON null). A trait that clipped to exactly
# 0.0 genuinely means "zero of this pathway" -- Gt(trait,0.0) guards BOTH
# the log-weight and the gain, so a zero trait gets log_weight=0
# (placeholder, never read as a real datum) and gain=0.0 (the honest,
# exact, always-finite answer) instead of a persisted -inf/null.
def _log_weight_and_gain(trait_key, ref_key):
    trait_t = p0(attr("c", trait_key))
    ref_t = p0(attr("c", ref_key))
    scale_t = p0(attr("c", "log_weight_scale"))
    positive = gt(trait_t, lit(0.0))
    raw_log = round_(times(scale_t, log_(div(trait_t, ref_t))), 0)
    log_weight = ite(positive, raw_log, lit(0.0))
    gain = ite(positive, exp_(times(div(lit(1.0), scale_t), raw_log)), lit(0.0))
    return log_weight, gain


_reactivity_log, _reactivity_gain = _log_weight_and_gain("trait_arousal", "arousal_ref")
_hostile_log, _hostile_gain = _log_weight_and_gain("trait_hostile_weight", "hostile_ref")
_warmth_log, _warmth_gain = _log_weight_and_gain("trait_charm_weight", "charm_ref")
_spite_log, _spite_gain = _log_weight_and_gain("trait_w_spite", "spite_ref")

psi_resolve_disposition_gains = rule(
    "psi_resolve_disposition_gains",
    [["agent", "has_affect_coupler", "c"]],
    eq(p0(attr("c", "coupling_on")), lit(1.0)),
    [
        ["set_attr_if_different", "c", "log_reactivity_weight", term(_reactivity_log)],
        ["set_attr_if_different", "c", "reactivity_gain", term(_reactivity_gain)],
        ["set_attr_if_different", "c", "log_hostile_weight", term(_hostile_log)],
        ["set_attr_if_different", "c", "hostile_gain", term(_hostile_gain)],
        ["set_attr_if_different", "c", "log_warmth_weight", term(_warmth_log)],
        ["set_attr_if_different", "c", "warmth_gain", term(_warmth_gain)],
        ["set_attr_if_different", "c", "log_spite_weight", term(_spite_log)],
        ["set_attr_if_different", "c", "spite_gain", term(_spite_gain)],
    ],
    comment=(
        "Normalises raw disposition traits (drawn once per resident, "
        "bigville_town100_world.py _PARAM_SPEC) into GAINS relative to "
        "the generator's own registered population means -- a population-"
        "mean resident gets gain=1.0 (neutral) on every channel. Div-by-"
        "zero is fail-quiet (term.rs Div evaluator) -- a missing reference "
        "mean silently zeroes the gain; AFFECT_COUPLING_SHAPE_PREREG.md "
        "registers this as a named, tested failure mode, not a surprise. "
        "DELIBERATELY UNCAPPED (RETRACTED an earlier gain_cap=2.0 clamp, "
        "see AFFECT_COUPLING_SHAPE_RESULTS.md's correction note): every "
        "_PARAM_SPEC trait this normalises is already drawn via _draw_clip "
        "against an explicit [0,1] bound (bigville_town100_world.py), so a "
        "REAL generated resident's gain is already naturally bounded (e.g. "
        "hostile_gain <= 1.0/hostile_ref = 2.5) with NO extra clamp needed "
        "-- adding one anyway was an invented, undocumented ceiling with no "
        "derivation, and it silently guaranteed disposition could never "
        "override even an arbitrarily strong real relationship, which is "
        "an ARCHITECTURAL decision this rule has no business making. A "
        "resident deliberately constructed outside the population range "
        "(a genuine tail case, EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md "
        "sec3b's own psychopathy/mania citations) is SUPPOSED to be able "
        "to produce gains that dominate -- who wins is decided by the "
        "actual relative magnitudes at Sum-time, never architecturally "
        "pre-decided here. Quantizing to a log-weight (see module "
        "docstring above) does not reintroduce this: log_weight_scale is "
        "derived, not capped, so an out-of-population resident still "
        "produces a dominating gain -- verified: zero decision flips "
        "across the real 100-resident cast at the derived SCALE, and the "
        "smallest representable step is ~36x finer than the tightest "
        "real decision margin it needs to preserve."
    ),
)


# ------------------------------------------------- 2. the generic coupling
# THE HEADLINE RULE. Matches ANY node x with a couples_affect_to edge from
# a coupler c that also reads_affect an AffectiveState a -- MatchEdge
# carries no node-type constraint (rewrite.rs:31, confirmed before this
# was written), so the SAME rule fires identically whether x is a
# SpeechOption, a target-scoped Concept (Phase 4), or a node type that
# does not exist yet. A new modulator CHANNEL is a new AffectChannel data
# row (has_affect_channel edges off the coupler), not a rule edit -- the
# channel table itself is graph data, read via AttrByName.
psi_couple_affect_to_tagged = rule(
    "psi_couple_affect_to_tagged",
    [["c", "couples_affect_to", "x"], ["c", "reads_affect", "a"]],
    eq(p0(attr("c", "coupling_on")), lit(1.0)),
    [
        ["set_attr_if_different", "x", "affect_bias",
         term(sum_(
             neighbours("c", "has_affect_channel"), "ch",
             times(
                 p0(attr_by_name("x", attr("ch", "affinity_key"))),
                 plus(p0(attr_by_name("a", attr("ch", "state_key"))),
                      p0(attr_by_name("c", attr("ch", "bias_key")))),
                 p0(attr_by_name("c", attr("ch", "gain_key"))),
                 p0(attr_by_name("c", attr("ch", "pathway_gain_key"))),
             ),
         ))],
    ],
    comment=(
        "value = base_value(elsewhere) + Sum_channels( affinity(x) * "
        "(state(a)+bias(c)) * gain(c) * pathway_gain(c) ), written ONCE, "
        "with the channel set as DATA (AffectChannel rows, has_affect_"
        "channel edges off c) -- a new channel is a new row, not a rule "
        "edit. Every read is P0-guarded: an UNTAGGED x (no affinity_* "
        "attr matching a channel's affinity_key) gets affect_bias==0.0 "
        "exactly, the vmPFC-lesion case as an absence, not a branch. "
        "Consumers opt in by (a) getting a couples_affect_to edge and (b) "
        "carrying affinity_* attrs -- nothing else."
    ),
)


# --------------------------------------------------- the four channel rows
# Plain data -- which attrs each channel reads. Minted per-resident (each
# BigvilleOcelotResident owns a private substrate; there is no cross-
# resident sharing to do) by _ensure_affect_coupler, NOT by this seed's
# own (empty) nodes/edges sections -- keeps this file pure rule+comment
# data, matching bigville_speech_decide.json's own convention of shipping
# zero nodes and letting the world adapter mint the per-instance graph.
CHANNEL_ROWS = [
    # valence: mood_bias (additive) x reactivity_gain, keyed off any node
    # tagged affinity_valence, reading AffectiveState.valence.
    dict(name="valence", affinity_key="affinity_valence", state_key="valence",
         bias_key="mood_bias", gain_key="reactivity_gain", pathway_gain_key="unit_gain"),
    # trait_valence: the SECOND additive valence offset (Russell 2003 core
    # affect / trait-state distinction) -- state_key points at unit_zero
    # (always 0.0) so only the trait offset contributes, still through the
    # SAME reactivity_gain global channel.
    dict(name="trait_valence", affinity_key="affinity_valence", state_key="unit_zero",
         bias_key="trait_valence", gain_key="reactivity_gain", pathway_gain_key="unit_gain"),
    # arousal_hostile: AffectiveState.arousal x reactivity_gain x
    # hostile_gain (per-pathway selective, the amygdala precedent) on any
    # node tagged affinity_hostile.
    dict(name="arousal_hostile", affinity_key="affinity_hostile", state_key="arousal",
         bias_key="unit_zero", gain_key="reactivity_gain", pathway_gain_key="hostile_gain"),
    # arousal_warm: the affiliative twin, on any node tagged affinity_warm.
    dict(name="arousal_warm", affinity_key="affinity_warm", state_key="arousal",
         bias_key="unit_zero", gain_key="reactivity_gain", pathway_gain_key="warmth_gain"),
]


seed = {
    "id": "affect_coupling", "version": "1.0.0", "depends_on": [],
    "self_load_only": True,
    "description": (
        "AFFECT-COUPLING PHASE 2 (EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md "
        "sec4, AFFECT_COUPLING_SHAPE_PREREG.md): the single reusable Rule "
        "that automatically couples a resident's PSI modulator state "
        "(AffectiveState, seeds/affective_state_core.json) and stable "
        "disposition traits (bigville_town100_world.py _PARAM_SPEC, "
        "transported by worlds/bigville_ocelot_adapter.py Phase 1) onto "
        "ANY node carrying a small affinity-tag shape -- matched "
        "generically via MatchEdge's own type-agnostic endpoints, not a "
        "coefficient hand-authored per decision type. OFF by default "
        "(coupling_on guard) and NOT added to boot_core.CORE_SEEDS/"
        "boot_all -- opt-in only, loaded the same way core_emotions/"
        "shared_arousal/hate_attribution already are "
        "(_ensure_emotional_core)."
    ),
    "nodes": [], "edges": [], "productions": [], "concepts": [],
    "rules": [psi_resolve_disposition_gains, psi_couple_affect_to_tagged],
}


def main():
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
