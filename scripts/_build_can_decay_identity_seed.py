"""One-off authoring script that EMITS seeds/can_decay_identity.json.

Not agent runtime -- a tool script (per CLAUDE.md's `tools/*` precedent:
"one-off authoring/capture scripts that EMIT seed manifests"). Builds the
Term-tree JSON by hand-nested dicts (matching the exact shape
seeds/can_native_reimplementation.json's rules already use) rather than
free-hand JSON authoring, to avoid a hand-typo in a 40-deep nested tree.

Run: python3 scripts/_build_can_decay_identity_seed.py > seeds/can_decay_identity.json
"""
import json


def Var(name):
    return {"type": "Var", "name": name}


def Lit(value):
    return {"type": "Lit", "value": value}


def Attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def EdgeAttrT(edge, key):
    return {"type": "EdgeAttr", "edge": edge, "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NotT(arg):
    return {"type": "Not", "arg": arg}


def AndT(items):
    return {"type": "And", "items": items}


def OrT(items):
    return {"type": "Or", "items": items}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def PlusT(items):
    return {"type": "Plus", "items": items}


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def lit_effect(node, key, value):
    return ["set_attr", node, key, value]


# ---------------------------------------------------------------------
# Shared sub-term: the policy gate, re-expressing mt_allows(mt,
# "allow_h_drift") (self_improvement_loop.py:44-56) as a Term -- a graph
# DECISION, not a Python one. Both new rules use this identical subtree.
#   FROZEN (no update_policy attr, or update_policy=="frozen") -> False
#   ADAPTIVE (update_policy=="adaptive")                       -> True
#   HYBRID (update_policy=="hybrid")   -> bool(attrs.get("allow_h_drift", True))
# Checked against term.rs before registering (PREREG Sec3): Attr on a
# missing key evaluates to Value::None; Eq(None, "adaptive") and
# Eq(None, 0) are both false (derived PartialEq, different variants never
# equal) -- so a missing update_policy correctly defaults to FROZEN
# (matches DEFAULT_POLICY), and a hybrid Mt with no allow_h_drift attr
# correctly defaults to allowed (Not(Eq(None,0)) == Not(false) == true).
# ---------------------------------------------------------------------
def allow_h_drift_native(mt_var="mt"):
    mt = Var(mt_var)
    return OrT([
        Eq(Attr(mt, "update_policy"), Lit("adaptive")),
        AndT([
            Eq(Attr(mt, "update_policy"), Lit("hybrid")),
            NotT(Eq(Attr(mt, "allow_h_drift"), Lit(0))),
        ]),
    ])


# ---------------------------------------------------------------------
# Rule 1: can_native_evidence_decay
#
# Native analog of maybe_decay_h/mt_decay_h (self_improvement_loop.py:87-91,
# can_ops.rs:835-854) for the ONE in-frame integer quantity the native
# Hebbian mechanism actually holds: the evidence_confirm/evidence_disconfirm
# counters on an already-minted Coactivation ledger (seeds/
# can_native_reimplementation.json v1.1.0, can_native_hebbian_mint/
# _reweight). PREREG Sec1: the continuous mechanism's `h <- (1-gamma)*h` is
# multiplicative -- a category error applied to an in-frame integer (7 *
# 0.999 is not an integer). The only decay shape that preserves integrality
# every step is a fixed-quantum LINEAR decrement toward zero -- exactly
# `translate`'s own `v -> v + offset[j]` step (runners/dsl/src/
# shape_decode.rs:786-820), offset=-1, PLUS an absorbing boundary at 0
# (translate itself has no clamp -- an explicit, registered deviation, not
# a silent one: evidence counts must never go negative). ONE consolidated
# rule, not a confirm/disconfirm sibling pair -- deliberately reusing
# CAN_NATIVE_REIMPLEMENTATION_RESULTS.md Sec3's own starvation-fix lesson,
# the SAME discipline can_native_hebbian_reweight already applies.
# Epoch-gated by a NEW decay_tick attr (can_tick > decay_tick, the SAME
# strictly-later-external-tick idiom noted_tick/evidence_tick already use)
# so decay applies at most once per external tick, and halts naturally once
# decay_tick catches up to can_tick (no extra no-op guard needed -- the
# strict Gt is sufficient, matching can_native_hebbian_reweight's own
# precedent exactly). Policy-gated on the SAME axis the continuous
# maybe_decay_h uses: mt_allows(mt, "allow_h_drift").
#
# LIVE CORRECTION (found while sanity-checking this design against the real
# engine, before writing the test suite -- reported, not smoothed over):
# a first draft gated decay ONLY on "can_tick advanced" (no reinforcement
# check). Because can_native_hebbian_reweight ALSO fires on every tick a
# pair stays co-activated, both rules were simultaneously eligible on every
# reinforcing tick, and a +1/-1 pair of same-magnitude effects canceled
# exactly -- net zero growth under PERSISTENT reinforcement, which
# contradicts decay_J's own docstring ("persistent co-activation maintains
# J; transient co-activation fades", can_ops.rs:733) and only matches the
# continuous mechanism's actual behaviour because there decay_rate (0.001)
# is numerically tiny relative to eta -- a relationship a 1-quantum integer
# decay cannot reproduce by magnitude alone. The fix reads whether
# reinforcement ALREADY happened on this exact tick (coact.evidence_tick ==
# mt.can_tick, an attr can_native_hebbian_mint/_reweight already maintain --
# a pure READ, no coupling or edit to that sibling-scoped rule) and skips
# decay when it did: "old evidence fades UNLESS reinforced"
# (can_ops.rs:833's own decay_h docstring, now implemented literally rather
# than only asymptotically).
# ---------------------------------------------------------------------
def rule_evidence_decay():
    mt, coact = Var("mt"), Var("coact")
    confirm = Attr(coact, "evidence_confirm")
    disconfirm = Attr(coact, "evidence_disconfirm")
    where = AndT([
        NotT(Eq(Var("a"), Var("b"))),
        Gt(Attr(mt, "can_tick"), Attr(coact, "decay_tick")),
        NotT(Eq(Attr(coact, "evidence_tick"), Attr(mt, "can_tick"))),
        allow_h_drift_native("mt"),
    ])
    return {
        "name": "can_native_evidence_decay",
        "comment": (
            "Native analog of maybe_decay_h/can_ops.rs::decay_h for the "
            "native mechanism's own in-frame evidence_confirm/"
            "evidence_disconfirm counters (Coactivation ledger, seeds/"
            "can_native_reimplementation.json v1.1.0). Linear (translate, "
            "offset=-1) unit decrement toward zero per strictly-later "
            "external tick, floored at 0 (translate itself has no clamp -- "
            "this rule adds one, registered explicitly, not silently: an "
            "evidence count must never go negative). ONE rule bumping BOTH "
            "counters via IfThenElse -- not a sibling pair -- reusing "
            "CAN_NATIVE_REIMPLEMENTATION_RESULTS.md Sec3's starvation-fix "
            "lesson pre-emptively. Policy-gated: mt_allows(mt, "
            "'allow_h_drift'), re-expressed as a Term (PREREG Sec3), same "
            "axis the continuous maybe_decay_h uses. See "
            "CAN_DECAY_IDENTITY_PREREG.md Sec1 / _RESULTS.md."
        ),
        "match_type": "Concept",
        "match": [
            ["mt", "has_concept", "a"],
            ["mt", "has_concept", "b"],
            ["a", "coactivated_with", "coact"],
            ["coact", "coactivation_of", "b"],
        ],
        "where": where,
        "effects": [
            term_effect(
                "coact", "evidence_confirm",
                IfThenElse(Gt(confirm, Lit(0)), PlusT([confirm, Lit(-1)]), confirm),
            ),
            term_effect(
                "coact", "evidence_disconfirm",
                IfThenElse(Gt(disconfirm, Lit(0)), PlusT([disconfirm, Lit(-1)]), disconfirm),
            ),
            term_effect("coact", "decay_tick", Attr(mt, "can_tick")),
        ],
    }


# ---------------------------------------------------------------------
# Rule 2: can_native_identity_evidence_sample
#
# PREREG Sec2's investigation, built: identity-as-evidence-axis. A
# per-Concept evidence ledger (no separate node -- identity is a property
# of ONE Concept, unlike Hebbian's pairwise Coactivation), stored directly
# as Concept attrs: identity_evidence_confirm/identity_evidence_disconfirm/
# identity_evidence_tick. Mirrors can_native_hebbian_reweight's EXACT shape
# (one consolidated rule, IfThenElse-computed branch, strictly-later-tick
# epoch gate) applied to a single Concept's own sigma instead of a pair's
# product-of-signs. sigma>0 is a confirm-like event ("this Concept was
# observed leaning positive"), sigma<0 is disconfirm-like, sigma==0 is no
# evidence either way (mirrors Hebbian's own state!=0 guard). Policy-gated
# on the SAME allow_h_drift axis maybe_update_identity/
# nudge_identity_on_flipped both use.
# ---------------------------------------------------------------------
def rule_identity_evidence_sample():
    mt, c = Var("mt"), Var("c")
    sigma = Attr(c, "state")
    confirm = Attr(c, "identity_evidence_confirm")
    disconfirm = Attr(c, "identity_evidence_disconfirm")
    where = AndT([
        NotT(Eq(sigma, Lit(0))),
        Gt(Attr(mt, "can_tick"), Attr(c, "identity_evidence_tick")),
        allow_h_drift_native("mt"),
    ])
    return {
        "name": "can_native_identity_evidence_sample",
        "comment": (
            "PREREG Sec2: identity dynamics AS a second application of the "
            "already-built evidence-axis mechanism (LOGODDS_GENERATOR_"
            "RESULTS.md), reading a per-tick sigma stream instead of "
            "confirm/disconfirm testimony. Per-Concept ledger (identity_"
            "evidence_confirm/_disconfirm/_tick, plain Concept attrs -- "
            "identity is single-node, not pairwise, so no Coactivation-"
            "style ledger node is needed). ONE rule, IfThenElse-branched -- "
            "the SAME starvation-avoidance shape can_native_hebbian_"
            "reweight already proved, applied here pre-emptively rather "
            "than found broken and fixed. sigma>0 bumps identity_evidence_"
            "confirm, sigma<0 bumps identity_evidence_disconfirm, sigma==0 "
            "is no evidence (mirrors Hebbian's own state!=0 guard). "
            "Policy-gated: mt_allows(mt,'allow_h_drift'), the SAME axis "
            "maybe_update_identity/nudge_identity_on_flipped both use. The "
            "graded 'commitment' READING is the SAME non-materializing "
            "log-odds Term (Log(Div(Plus(confirm,1),Plus(disconfirm,1)))), "
            "evaluated live, never written back -- this rule does NOT "
            "write identity_field (PREREG Sec2's registered open question: "
            "materializing the render into identity_field's feedback role "
            "in can_native_update_3state's own local-field sum is a "
            "SEPARATE, un-sized follow-on, not built here). See "
            "CAN_DECAY_IDENTITY_PREREG.md / _RESULTS.md."
        ),
        "match_type": "Concept",
        "match": [
            ["mt", "has_concept", "c"],
        ],
        "where": where,
        "effects": [
            term_effect(
                "c", "identity_evidence_confirm",
                IfThenElse(Gt(sigma, Lit(0)), PlusT([confirm, Lit(1)]), confirm),
            ),
            term_effect(
                "c", "identity_evidence_disconfirm",
                IfThenElse(Lt(sigma, Lit(0)), PlusT([disconfirm, Lit(1)]), disconfirm),
            ),
            term_effect("c", "identity_evidence_tick", Attr(mt, "can_tick")),
        ],
    }


# ---------------------------------------------------------------------
# Rule 3: can_native_identity_evidence_decay
#
# The SAME decay shape as Rule 1, applied to the identity ledger -- shown
# to demonstrate decay is a REUSABLE RULE SHAPE (not a bespoke mechanism
# per evidence axis), not because the task requires two separate decay
# demonstrations. Same policy axis, same epoch-gate idiom, same floored
# linear decrement, and the SAME "skip if reinforced THIS tick" guard Rule
# 1 needed (reading identity_evidence_tick, which can_native_identity_
# evidence_sample already maintains -- the same live-correction lesson
# applied here from the start rather than re-discovered).
# ---------------------------------------------------------------------
def rule_identity_evidence_decay():
    mt, c = Var("mt"), Var("c")
    confirm = Attr(c, "identity_evidence_confirm")
    disconfirm = Attr(c, "identity_evidence_disconfirm")
    where = AndT([
        Gt(Attr(mt, "can_tick"), Attr(c, "identity_decay_tick")),
        NotT(Eq(Attr(c, "identity_evidence_tick"), Attr(mt, "can_tick"))),
        allow_h_drift_native("mt"),
    ])
    return {
        "name": "can_native_identity_evidence_decay",
        "comment": (
            "The SAME linear-decrement-toward-zero shape as can_native_"
            "evidence_decay (Rule 1), applied to the per-Concept identity "
            "ledger -- demonstrates decay is a reusable RULE SHAPE across "
            "both evidence axes this rung builds, not a bespoke mechanism "
            "re-derived per axis. Own epoch-gate attr (identity_decay_tick) "
            "so this rule's own firing schedule is independent of Rule 2's "
            "identity_evidence_tick (sampling and decay are different "
            "events and must not share one epoch counter, or a decay tick "
            "would be misread as a sample tick or vice versa)."
        ),
        "match_type": "Concept",
        "match": [
            ["mt", "has_concept", "c"],
        ],
        "where": where,
        "effects": [
            term_effect(
                "c", "identity_evidence_confirm",
                IfThenElse(Gt(confirm, Lit(0)), PlusT([confirm, Lit(-1)]), confirm),
            ),
            term_effect(
                "c", "identity_evidence_disconfirm",
                IfThenElse(Gt(disconfirm, Lit(0)), PlusT([disconfirm, Lit(-1)]), disconfirm),
            ),
            term_effect("c", "identity_decay_tick", Attr(mt, "can_tick")),
        ],
    }


SEED = {
    "id": "can_decay_identity",
    "version": "1.0.0",
    "depends_on": ["can_native_reimplementation"],
    "self_load_only": True,
    "description": (
        "Native decay + identity dynamics, closing two of consumer 6's "
        "three named blockers (CAN_CONSUMER_MIGRATION_RESULTS.md Sec1 row "
        "6: 'decay ... no native analog proposed anywhere'; 'identity "
        "dynamics ... no native design exists at all'; Blocker B (Hebbian "
        "materialization) is a SIBLING rung's exact scope, not touched "
        "here). DECAY: the continuous mt_decay_h/mt_decay_J (can_ops.rs) "
        "are multiplicative (h <- (1-gamma)*h) -- a category error applied "
        "to an in-frame integer count (0.999*7 is not an integer). The "
        "integrality-preserving native analog is a fixed-quantum LINEAR "
        "decrement toward zero, exactly translate's own v -> v + offset[j] "
        "step (shape_decode.rs::apply_translate_once, offset=-1) PLUS an "
        "absorbing floor at 0 that plain translate does not have "
        "(registered explicitly as a deviation, not silently added) -- "
        "applied to the ONE in-frame integer quantity the native Hebbian "
        "mechanism already holds, evidence_confirm/evidence_disconfirm on "
        "a Coactivation ledger (seeds/can_native_reimplementation.json "
        "v1.1.0). IDENTITY: investigated whether a Concept's 'identity' is "
        "just another evidence-accumulation dimension -- CONFIRMED for the "
        "READING half (a per-Concept confirm/disconfirm ledger sampling "
        "sigma each tick, rendered via the SAME non-materializing log-odds "
        "Term the causal-strength axis already uses, gives a graded "
        "'how committed' signal with zero new machinery), NOT resolved for "
        "the FEEDBACK half (identity_field is read by can_native_update_"
        "3state's own local-field sum as a materialized, feedback-"
        "participating float -- a genuinely different role from the "
        "Hebbian render's pure-comparator role; wiring the identity render "
        "back into identity_field is named as a separate, un-sized "
        "follow-on, not built). Both new rules re-express mt_allows(mt, "
        "'allow_h_drift') (self_improvement_loop.py) as a Term (a graph "
        "decision, not a Python one) rather than relying on a Python "
        "policy check the way the continuous wrappers do. Zero new Rust "
        "anywhere in this seed -- Attr/EdgeAttr/Eq/Not/And/Or/Gt/Lt/Plus/"
        "IfThenElse/Log/Div all pre-existed and are reused as-is. See "
        "CAN_DECAY_IDENTITY_PREREG.md / _RESULTS.md."
    ),
    "nodes": [
        {
            "local_id": 1,
            "type": "DimensionGenerator",
            "attrs": {
                "name": "evidence_decay",
                "kind": "translate",
                "coord_dims": [0],
                "params": [1],
                "offset": [-1],
                "_note": (
                    "Documents the SHAPE this rung's decay stepping matches "
                    "(translate, offset=-1 -- toward zero, mirror image of "
                    "inference_knowledge.json local_id 13's offset=[1] "
                    "accumulation generator). Declarative only, exactly "
                    "like logodds_evidence -- never literally invoked at "
                    "runtime; the actual stepping is ordinary Plus/"
                    "IfThenElse rule-effect arithmetic (see "
                    "can_native_evidence_decay). The absorbing floor at 0 "
                    "is NOT part of translate's own semantics -- an "
                    "explicit, registered deviation (PREREG Sec1)."
                ),
            },
        },
        {
            "local_id": 2,
            "type": "DimensionGenerator",
            "attrs": {
                "name": "identity_evidence",
                "kind": "translate",
                "coord_dims": [0],
                "params": [1],
                "offset": [1],
                "_note": (
                    "Documents the accumulation half of the identity "
                    "ledger -- the SAME shape logodds_evidence (inference_"
                    "knowledge.json local_id 13) already declares for the "
                    "Hebbian axis, here for the per-Concept sigma-sampling "
                    "axis (can_native_identity_evidence_sample). "
                    "Declarative only, not literally invoked."
                ),
            },
        },
        {
            "local_id": 3,
            "type": "LatentDimension",
            "attrs": {
                "name": "latent:identity_commitment",
                "generator": "identity_evidence",
                "k": 0,
                "source": "can_decay_identity_design",
                "_note": (
                    "The identity-commitment reading's declarative home, "
                    "mirroring latent:causal_strength's own wiring "
                    "(inference_knowledge.json local_id 14). No existing "
                    "rule reads this node -- additive documentation only, "
                    "matching LOGODDS_GENERATOR_RESULTS.md Sec7 point 2's "
                    "own precedent (declarative scaffolding, not a "
                    "consumed mechanism, in this rung)."
                ),
            },
        },
    ],
    "edges": [],
    "productions": [],
    "concepts": [
        {
            "name": "can_native_evidence_decay",
            "definition": (
                "A native, in-frame-integer-preserving analog of mt_decay_"
                "h/mt_decay_J: evidence_confirm/evidence_disconfirm on an "
                "already-minted Coactivation ledger each decrement toward "
                "zero by exactly 1 per strictly-later external tick (never "
                "negative), gated by the SAME allow_h_drift policy axis the "
                "continuous mechanism uses -- re-expressed as a graph Term, "
                "not a Python decision."
            ),
            "why": (
                "Closes CAN_CONSUMER_MIGRATION_RESULTS.md row 6 blocker "
                "(a): decay had no native analog anywhere in this arc "
                "before this seed. The continuous h/J decay is "
                "multiplicative and cannot preserve an integer count; the "
                "integrality-preserving analog is the SAME fixed-quantum "
                "step translate already expresses, applied toward zero."
            ),
        },
        {
            "name": "can_native_identity_as_evidence_axis",
            "definition": (
                "A Concept's per-tick sigma reading is a confirm/"
                "disconfirm-shaped evidence stream about its OWN typical "
                "state, tracked on the SAME evidence-ledger idiom the "
                "Hebbian causal-strength axis already uses (own counters, "
                "own strictly-later-tick epoch gate, own non-materializing "
                "log-odds render) -- the READING half of identity dynamics "
                "reuses the already-built mechanism with zero new "
                "machinery."
            ),
            "why": (
                "Closes CAN_CONSUMER_MIGRATION_RESULTS.md row 6 blocker "
                "(c) for the reading half only. The FEEDBACK half -- "
                "materializing the reading back into identity_field so it "
                "participates in can_native_update_3state's own local-"
                "field sum, the way the continuous h_id does -- is NOT "
                "resolved by this concept; identity_field's role there is "
                "a materialized MAP parameter, a genuinely different job "
                "than a pure external comparator, and wiring one into the "
                "other is named as separate follow-on work."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_evidence_decay(),
        rule_identity_evidence_sample(),
        rule_identity_evidence_decay(),
    ],
}

print(json.dumps(SEED, indent=1))
