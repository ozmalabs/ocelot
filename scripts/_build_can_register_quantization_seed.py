"""One-off authoring script that EMITS seeds/can_register_quantization.json.

Not agent runtime -- a tool script (per CLAUDE.md's `tools/*` precedent:
"one-off authoring/capture scripts that EMIT seed manifests"). Builds the
Term-tree JSON by hand-nested dicts (matching the exact shape
seeds/can_native_reimplementation.json's / scripts/_build_can_decay_identity_
seed.py's rules already use) rather than free-hand JSON authoring, to avoid
a hand-typo in a deeply nested tree.

See docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_PREREG.md for
the full registered design this script implements.

Run: python3 scripts/_build_can_register_quantization_seed.py > seeds/can_register_quantization.json
"""
import json
import math


# --------------------------------------------------------------------- #
# Term-tree builders (mirrors scripts/_build_can_decay_identity_seed.py)
# --------------------------------------------------------------------- #
def Var(name):
    return {"type": "Var", "name": name}


def Lit(value):
    return {"type": "Lit", "value": value}


def Attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NotT(arg):
    return {"type": "Not", "arg": arg}


def AndT(items):
    return {"type": "And", "items": items}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def PlusT(items):
    return {"type": "Plus", "items": items}


def MinusT(a, b):
    return {"type": "Minus", "a": a, "b": b}


def TimesT(items):
    return {"type": "Times", "items": items}


def DivT(a, b):
    return {"type": "Div", "a": a, "b": b}


def RoundT(value, ndigits=0):
    return {"type": "Round", "value": value, "ndigits": Lit(ndigits)}


def MaxT(items):
    return {"type": "Max", "items": items}


def AbsT(arg):
    return {"type": "Abs", "arg": arg}


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def LetT(name, value, body):
    return {"type": "Let", "name": name, "value": value, "body": body}


def ArgminT(source, var_name, value):
    return {"type": "Argmin", "source": source, "var_name": var_name, "value": value}


def NodesOfType(node_type):
    return {"type": "NodesOfType", "node_type": node_type}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def lit_effect(node, key, value):
    return ["set_attr", node, key, value]


# --------------------------------------------------------------------- #
# Shared sub-expressions -- PREREG Sec4.2/4.3. Each is re-derived from
# scratch inside its own Let-chain per effect (matching can_native_
# update_3state's own precedent of repeating a shared expression across
# the where-clause and each effect, rather than assuming cross-effect
# read-your-own-write ordering within one rule firing -- not verified
# either way for this engine, so not relied on).
# --------------------------------------------------------------------- #
def _effective_bins_term(prof_var="prof"):
    """Let(eb_raw = round(resolution_bins * resolution_level)) ->
    max(2, eb_raw), via IfThenElse (Gte check) rather than a bare MaxT
    call, so the intermediate is named and auditable."""
    prof = Var(prof_var)
    eb_raw = RoundT(TimesT([Attr(prof, "resolution_bins"), Attr(prof, "resolution_level")]))
    return LetT(
        "eb_raw", eb_raw,
        IfThenElse(Gte(Var("eb_raw"), Lit(2)), Var("eb_raw"), Lit(2)),
    )


def _level_index_term(prof_var="prof", obs_var="obs"):
    obs = Var(obs_var)
    true_affinity = Attr(obs, "true_affinity")
    return LetT(
        "eb", _effective_bins_term(prof_var),
        RoundT(
            TimesT([
                DivT(PlusT([true_affinity, Lit(1.0)]), Lit(2.0)),
                MinusT(Var("eb"), Lit(1)),
            ])
        ),
    )


def _quantized_value_term(prof_var="prof", obs_var="obs"):
    return LetT(
        "eb", _effective_bins_term(prof_var),
        LetT(
            "idx", _level_index_body(prof_var, obs_var),
            PlusT([
                Lit(-1.0),
                TimesT([Var("idx"), DivT(Lit(2.0), MinusT(Var("eb"), Lit(1)))]),
            ]),
        ),
    )


def _level_index_body(prof_var, obs_var):
    """The BODY of level_index computation, assuming `eb` is ALREADY bound
    in the enclosing Let (used inside _quantized_value_term so eb is not
    re-derived a second time within that one expression)."""
    obs = Var(obs_var)
    true_affinity = Attr(obs, "true_affinity")
    return RoundT(
        TimesT([
            DivT(PlusT([true_affinity, Lit(1.0)]), Lit(2.0)),
            MinusT(Var("eb"), Lit(1)),
        ])
    )


def _register_label_term(prof_var="prof", obs_var="obs"):
    return LetT(
        "eb", _effective_bins_term(prof_var),
        LetT(
            "idx", _level_index_body(prof_var, obs_var),
            LetT(
                "qv",
                PlusT([
                    Lit(-1.0),
                    TimesT([Var("idx"), DivT(Lit(2.0), MinusT(Var("eb"), Lit(1)))]),
                ]),
                Attr(
                    ArgminT(
                        source=NodesOfType("RegisterLabelAnchor"),
                        var_name="lbl",
                        value=AbsT(MinusT(Var("qv"), Attr(Var("lbl"), "canonical_value"))),
                    ),
                    "label",
                ),
            ),
        ),
    )


# --------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------- #
def rule_register_decode_band():
    obs = Var("obs")
    where = AndT([
        Eq(Attr(obs, "status"), Lit("pending")),
    ])
    return {
        "name": "can_register_decode_band",
        "comment": (
            "PREREG Sec4-5: quantizes a resident's per-band 'true' "
            "continuous register affinity (a saturating function of "
            "band_code, authored once as static BandAffinityAnchor data, "
            "PREREG Sec4.1) onto a linspace(-1,1,effective_bins) grid, "
            "effective_bins = max(2, round(resolution_bins*resolution_"
            "level)) -- the SAME composition BIGVILLE_CAN_INTEGRATION_"
            "PREREG.md Sec4 established for belief quantization, reused "
            "verbatim here for register quantization (PREREG Sec3). The "
            "quantized value is then classified against a 3-entry "
            "RegisterLabelAnchor codebook (formal/neutral/casual, labels "
            "reused from seeds/interlocutor_shapes.json's own sig_"
            "register vocabulary, PREREG Sec1 point 3) via Argmin nearest-"
            "point decode (PREREG Sec2's registered justification for "
            "Argmin over ShapeDecode: a scalar nearest-point classification "
            "against 3 fixed references has no relational structure to "
            "compose, so the beam-search/residual-coverage machinery "
            "ShapeDecode exists for is the wrong-sized tool here). ALL "
            "arithmetic (Round/Times/Div/Plus/Minus/Max/Gte/IfThenElse/Let/"
            "Argmin/Abs) is pre-existing Term vocabulary -- zero new Rust "
            "(PREREG Sec1 point 6). The register DECISION (which label "
            "wins) is this Rule's own Argmin call, not Python."
        ),
        "match_type": "RegisterObservation",
        "match": [
            ["prof", "observed_band", "obs"],
        ],
        "where": where,
        "effects": [
            term_effect("obs", "effective_bins", _effective_bins_term("prof")),
            term_effect("obs", "register_level_index", _level_index_term("prof", "obs")),
            term_effect("obs", "quantized_value", _quantized_value_term("prof", "obs")),
            term_effect("obs", "register_label", _register_label_term("prof", "obs")),
            lit_effect("obs", "status", "decoded"),
        ],
    }


# --------------------------------------------------------------------- #
# BandAffinityAnchor codebook -- PREREG Sec4.1, computed ONCE here (a
# one-time cross-frame authoring computation using Exp/math.exp -- NEVER
# evaluated inside run_rules(), per the frame/continuum invariant), baked
# into the seed as static literature-grounded data, band_code in {0..5}
# (PREREG Sec1 point 4's registered scoping -- excludes band_code=-1/rival).
# --------------------------------------------------------------------- #
_K = 3.0


def _true_affinity(band_code):
    return 2.0 * (1.0 - math.exp(-_K * band_code / 5.0)) - 1.0


BAND_NAMES = {
    0: "stranger", 1: "consequential_stranger", 2: "acquaintance",
    3: "friend", 4: "intimate", 5: "family",
}


def band_affinity_anchor_nodes():
    out = []
    for local_id, band in enumerate(range(6), start=1):
        out.append({
            "local_id": local_id,
            "type": "BandAffinityAnchor",
            "attrs": {
                "band_code": band,
                "band_name": BAND_NAMES[band],
                "true_affinity": round(_true_affinity(band), 6),
            },
        })
    return out


def register_label_anchor_nodes(start_id):
    labels = [("formal", -1.0), ("neutral", 0.0), ("casual", 1.0)]
    out = []
    for i, (label, canonical_value) in enumerate(labels):
        out.append({
            "local_id": start_id + i,
            "type": "RegisterLabelAnchor",
            "attrs": {"label": label, "canonical_value": canonical_value},
        })
    return out


NODES = band_affinity_anchor_nodes() + register_label_anchor_nodes(start_id=7)

SEED = {
    "id": "can_register_quantization",
    "version": "1.0.0",
    "depends_on": ["can_native_reimplementation", "interlocutor_shapes"],
    "self_load_only": True,
    "description": (
        "Personality-trait-quantized REGISTER/STYLE codebook, applied per "
        "discrete relationship band (band_code 0-5, the tie-strength ladder "
        "half of Bigville's real BigvilleBondWorld._band_code -- band_code "
        "=-1/'rival' is out of scope, PREREG Sec1 point 4). Reuses "
        "resolution_bins (the SAME per-resident cognitive-resolution trait "
        "BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md introduced for belief "
        "quantization, and every later rung in this arc reused unmodified) "
        "and the SAME effective_bins=max(2,round(resolution_bins*"
        "resolution_level)) composition formula, applied to a NEW "
        "continuous quantity: a per-band register-affinity value on "
        "[-1,1] that is a SATURATING function of band_code (Brinberg & Ram "
        "2021's measured exponential-approach-to-asymptote convergence "
        "curve for real couples' linguistic alignment -- BIGVILLE_TOPIC_"
        "AND_STYLE_SCOPING.md Sec2.5), authored ONCE as static "
        "BandAffinityAnchor codebook data (band_code in 0..5), never "
        "recomputed via Exp inside run_rules() (frame/continuum "
        "invariant: the one transcendental piece of this design stays a "
        "one-time cross-frame authoring computation, never an in-loop "
        "one). The quantized value is classified against a 3-entry "
        "RegisterLabelAnchor codebook (formal/neutral/casual, labels "
        "reused from seeds/interlocutor_shapes.json's sig_register "
        "vocabulary -- that seed's own nodes/rules are NOT used, read-"
        "only label-vocabulary reuse only) via Argmin nearest-point "
        "decode -- an already-established engine-native selection "
        "primitive (seeds/gap_awareness.json's retire_duplicate_gap), "
        "deliberately NOT ShapeDecode/shape_decode_loop (PREREG Sec2's "
        "registered justification: a scalar nearest-point classification "
        "against 3 fixed references has no relational structure for "
        "ShapeDecode's beam-search/residual-coverage machinery to "
        "compose). Zero new Rust Terms anywhere in this seed -- Plus/"
        "Minus/Times/Div/Round/Max/Abs/Gte/IfThenElse/Let/Argmin/"
        "NodesOfType/Attr/Var/Lit/Eq/Not/And all pre-existed. See "
        "CAN_REGISTER_QUANTIZATION_PREREG.md / _RESULTS.md."
    ),
    "nodes": NODES,
    "edges": [],
    "productions": [
        {
            "src": {"type": "RegisterProfile", "var": "prof"},
            "edge_type": "observed_band",
            "tgt": {"type": "RegisterObservation", "var": "obs"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "can_register_quantization",
        },
    ],
    "concepts": [
        {
            "name": "can_register_band_quantization",
            "definition": (
                "A resident's register affinity toward a discrete "
                "relationship band is a saturating function of that "
                "band's accumulated closeness, quantized onto a "
                "resolution_bins-sized grid (the SAME trait and "
                "composition formula CAN belief quantization already "
                "uses) and classified against a small held label "
                "codebook via Argmin nearest-point decode -- the register-"
                "domain sibling of can_native_basin_decode's belief-"
                "domain basin classification, sized for a scalar "
                "classification problem rather than a relational one."
            ),
            "why": (
                "The mechanism BIGVILLE_TOPIC_AND_STYLE_SCOPING.md's Part "
                "3.4 named as OCELOT's own job, not Bigville's -- a "
                "personality-trait-quantized codebook applied per "
                "discrete relationship band, reusing resolution_bins "
                "rather than inventing a second resolution trait."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_register_decode_band(),
    ],
}

print(json.dumps(SEED, indent=1))
