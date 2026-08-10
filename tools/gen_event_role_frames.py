#!/usr/bin/env python3
"""AUTHORING SCRIPT (one-off, not agent runtime) — EMIT the VerbFrame codebook into
`seeds/event_role_frames.json`.

The codebook is DATA the agent decodes: each VerbFrame is a priority-ordered
(guard Term, effect list) pair that reproduces ONE step of `_event_predication`'s
role-assignment ladder as graph-native data. The DECODE (`reading_collapse.
_decode_roles_graph`) reads these frames from the graph, evaluates each guard via
the Rust `evaluate` (a Term over the `EventClause`'s precomputed candidate attrs +
the running-state `r_*` attrs), and applies the applicable frames in priority order
to the running state — a generic codebook interpreter with NO role logic in Python
(the logic is entirely in the guard Terms + effect specs authored here). The
per-frame priority IS the Occam/override order of the Python cascade; applying the
highest-priority applicable writer to each field is the argmax the user chose.

This script only assembles guard/effect Term JSON (the same status as the
`_compose_*_rule` seed builders). Re-run it to regenerate the codebook; the result
is checked in as `seeds/event_role_frames.json`'s `frames` array.
"""
from __future__ import annotations

import json
import os

SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "event_role_frames.json")

# --- Term constructors (the decode evaluates these via the Rust `evaluate`) ------
# The clause node is bound to the variable `c` in the decode's env.


def A(key: str) -> dict:
    """Attr read `c.<key>` — a precomputed candidate (`def_subj`, `nom_surface`, …)
    OR a running-state field (`r_subj`, `r_obj`, `r_obj_span_head`, …)."""
    return {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": key}


def L(v):
    return {"type": "Lit", "value": v}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NE(a, b):
    return {"type": "Not", "arg": EQ(a, b)}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def GT(a, b):
    return {"type": "Gt", "a": a, "b": b}


def GE(a, b):                       # Ge is not a Term type — express via Not(Lt).
    return {"type": "Not", "arg": LT(a, b)}


def AND(*xs):
    return {"type": "And", "items": list(xs)}


def OR(*xs):
    return {"type": "Or", "items": list(xs)}


TRUE = GE(L(1.0), L(0.0))           # always-applicable guard (base frame).

# Running-state field names (written on the EventClause as the decode proceeds; the
# decode reads them back as the resolved roles, `_ground_event` emits from them).
R_SUBJ, R_SUBJ_SPAN = "r_subj", "r_subj_span"
R_OBJ, R_OBJ_SPAN, R_OBJ_HEAD = "r_obj", "r_obj_span", "r_obj_span_head"
R_INV = "r_inverted"

# guard fragments reused across the inversion frames -----------------------------
_NOM = GE(A("nom_idx"), L(0.0))                          # nom_i >= 0
_ACC = AND(GE(A("acc_idx"), L(0.0)), NE(A("acc_surface"), A(R_SUBJ)))
_INV_HEAD = AND(GE(A("lead_pp"), L(1.0)),                # lead_pp and adj_end >= vi
                GE(A("adj_end"), A("main_verb_index")),
                NE(A(R_OBJ_HEAD), L("")))                # ph = obj_span_head truthy

# The frames — ONE per cascade step (or per inner branch), priority = the override
# order of `_event_predication`'s ladder. Each `effects` entry is [field, valueTerm]
# evaluated against the CURRENT running state then written, so a later (higher-prio)
# frame overrides an earlier one exactly as the sequential Python assignment does.
FRAMES = [
    {
        "name": "svo_base",
        "priority": 0.0,
        "note": "default SVO reading — subject before the verb, object after "
                "(PP-truncated); the byte-for-byte position baseline every override "
                "starts from.",
        "guard": TRUE,
        "effects": [
            [R_SUBJ, A("def_subj")],
            [R_SUBJ_SPAN, A("subj_span")],
            [R_OBJ, A("def_obj")],
            [R_OBJ_SPAN, A("obj_span")],
            [R_OBJ_HEAD, A("inv_subj_head")],
            [R_INV, L(0.0)],
        ],
    },
    {
        "name": "nom_subject",
        "priority": 10.0,
        "note": "CASE: a nominative pronoun (he/she/they) binds SUBJECT wherever it "
                "sits, overriding the positional subject.",
        "guard": _NOM,
        "effects": [
            [R_SUBJ, A("nom_surface")],
            [R_SUBJ_SPAN, A("nom_surface")],
        ],
    },
    {
        "name": "nom_postposed",
        "priority": 11.0,
        "note": "a post-verbal nominative subject (nom_i > vi) marks a verb-subject "
                "inversion ('rested he').",
        "guard": AND(_NOM, GT(A("nom_idx"), A("main_verb_index"))),
        "effects": [[R_INV, L(1.0)]],
    },
    {
        "name": "acc_object",
        "priority": 20.0,
        "note": "CASE: a non-prepositional accusative pronoun (him/her/them) distinct "
                "from the subject binds OBJECT wherever it sits.",
        "guard": _ACC,
        "effects": [
            [R_OBJ, A("acc_surface")],
            [R_OBJ_SPAN, A("acc_surface")],
            [R_OBJ_HEAD, A("acc_surface")],
        ],
    },
    {
        "name": "acc_fronted",
        "priority": 21.0,
        "note": "a pre-verbal accusative pronoun (acc_i < vi) is a fronted object — "
                "inversion.",
        "guard": AND(_ACC, LT(A("acc_idx"), A("main_verb_index"))),
        "effects": [[R_INV, L(1.0)]],
    },
    {
        "name": "clear_collision",
        "priority": 30.0,
        "note": "a default-SVO object that collided with the (re)bound subject is "
                "spurious — clear it.",
        "guard": AND(NE(A(R_OBJ), L("")), EQ(A(R_OBJ), A(R_SUBJ))),
        "effects": [
            [R_OBJ, L("")],
            [R_OBJ_SPAN, L("")],
            [R_OBJ_HEAD, L("")],
        ],
    },
    {
        "name": "osv_fronted_object",
        "priority": 40.0,
        "note": "OSV: a pre-verbal nominative subject with the object still open takes "
                "the DP abutting the subject pronoun on its left as the fronted object "
                "('the manxome foe he sought').",
        "guard": AND(_NOM, LT(A("nom_idx"), A("main_verb_index")),
                     EQ(A(R_OBJ), L("")),
                     NE(A("fronted_head"), L("")),
                     NE(A("fronted_head"), A(R_SUBJ))),
        "effects": [
            [R_OBJ, A("fronted_head")],
            [R_OBJ_SPAN, A("fronted_span")],
            [R_OBJ_HEAD, A("fronted_head")],
            [R_INV, L(1.0)],
        ],
    },
    {
        "name": "locative_inversion_subject",
        "priority": 50.0,
        "note": "VS / locative inversion: a fronted adjunct PP consuming the whole "
                "pre-verb span (adj_end >= vi) makes the post-verb nominal the "
                "post-posed SUBJECT ('Into the room walked a tall man').",
        "guard": _INV_HEAD,
        "effects": [
            [R_SUBJ, A(R_OBJ_HEAD)],
            [R_SUBJ_SPAN, A(R_OBJ_SPAN)],
            [R_INV, L(1.0)],
        ],
    },
    {
        "name": "locative_inversion_oblique",
        "priority": 51.0,
        "note": "…and the fronted PP's own head fills the OBLIQUE complement when it "
                "differs from the post-posed subject (both roles fill).",
        "guard": AND(_INV_HEAD, NE(A("pp_head"), L("")),
                     NE(A("pp_head"), A(R_SUBJ))),
        "effects": [
            [R_OBJ, A("pp_head")],
            [R_OBJ_SPAN, A("pp_span")],
        ],
    },
    {
        "name": "locative_inversion_no_oblique",
        "priority": 52.0,
        "note": "…else (no distinct PP head) the inverted clause has no core object.",
        "guard": AND(_INV_HEAD, OR(EQ(A("pp_head"), L("")),
                                   EQ(A("pp_head"), A(R_SUBJ)))),
        "effects": [
            [R_OBJ, L("")],
            [R_OBJ_SPAN, L("")],
        ],
    },
]


def build_frames() -> list:
    out = []
    for fr in FRAMES:
        out.append({
            "type": "VerbFrame",
            "attrs": {
                "codebook": "event_roles",
                "name": fr["name"],
                "priority": fr["priority"],
                "note": fr["note"],
                "guard_json": json.dumps(fr["guard"], separators=(",", ":")),
                "effects_json": json.dumps(fr["effects"], separators=(",", ":")),
            },
        })
    return out


# --- RoleFrame EMIT codebook (Phase 3: growable participant roles) --------------
# A RoleFrame emits an EXTRA participant predication [verb, subj, <head>] when its
# guard holds over the clause's precomputed candidate attrs + the decode's resolved
# r_subj/r_obj. The thematic OBLIQUE is the first (and, by default, only) RoleFrame:
# the animate PP participant the SVO head-reduction drops ('drove his cart OVER the
# poor dog'). It is DATA, not hardcoded — so it can be ABSENT, and a residual (an
# animate PP participant no RoleFrame captures) mints it back via the role sd-loop
# (`seeds/role_decode_loop.json`). This is the earlier Python oblique patch, now
# graph-resident and growable.
OBLIQUE_GUARD = AND(
    NE(A("obl_canon_head"), L("")),
    GE(A("obl_animate"), L(1.0)),
    GE(A("obl_role_ok"), L(1.0)),
    NE(A("obl_canon_head"), A(R_SUBJ)),
    NE(A("obl_canon_head"), A(R_OBJ)),
)

ROLE_EMITS = [
    {
        "role": "oblique",
        "head_attr": "obl_canon_head",
        "note": "thematic OBLIQUE participant: an ANIMATE PP head (WordNet animacy + "
                "the VerbNet prep->role table, precomputed) distinct from subj/obj is "
                "registered as [verb, subj, head] so the thematic layer holds it.",
        "guard": OBLIQUE_GUARD,
    },
]


def build_role_emits() -> list:
    out = []
    for r in ROLE_EMITS:
        out.append({
            "type": "RoleFrame",
            "attrs": {
                "codebook": "event_roles",
                "kind": "role_emit",
                "role": r["role"],
                "head_attr": r["head_attr"],
                "note": r["note"],
                "guard_json": json.dumps(r["guard"], separators=(",", ":")),
                # the residual SIGNAL a missing role would leave — the same guard,
                # so a clause carrying an uncaptured animate PP is a real residual
                # the role sd-loop can mint this exact RoleFrame back from.
                "residual_signal": "obl_canon_head",
            },
        })
    return out


def main() -> None:
    with open(SEED) as f:
        manifest = json.load(f)
    manifest["version"] = "0.3.0"
    manifest["frames"] = build_frames()
    manifest["role_emits"] = build_role_emits()
    # productions the role layer needs admissible: the Agent->clause membership edge
    # (so the role sd-loop rules can bind the Agent + clause) and the residual->minted
    # RoleFrame edge (fixpoint-safety guard against re-minting).
    prods = manifest.setdefault("productions", [])
    have = {(p.get("edge_type"), p["src"].get("type"), p["tgt"].get("type"))
            for p in prods}
    for src_t, et, tgt_t, var_s, var_t in [
        ("Agent", "has_clause", "EventClause", "ag", "clause"),
        ("EventClause", "role_minted", "RoleFrame", "clause", "rf"),
    ]:
        if (et, src_t, tgt_t) not in have:
            prods.append({
                "provenance": "seed:event_role_frames:%s" % et,
                "src": {"type": src_t, "var": var_s},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": var_t},
            })
    manifest["microtheory"]["description"] = (
        "an event clause is a graph of Token nodes; role assignment is DECODE over a "
        "VerbFrame codebook (priority-ordered guard/effect frames, evaluated by the "
        "Rust `evaluate`); a novel role grows from a residual via the sd loop.")
    manifest["description"] = (
        "Graph-native EVENT GROUNDING (the Jabberwock grows its own argument roles). "
        "v0.2.0 (Phase 2): the CLAUSE-GRAPH VOCABULARY (EventClause/Token node types "
        "+ has_token/next productions) PLUS the VerbFrame CODEBOOK (the `frames` "
        "array): one VerbFrame per step of _event_predication's role-assignment "
        "ladder (svo_base -> nom/acc case binding -> collision clear -> OSV fronted "
        "object -> locative inversion), each a priority + a guard Term (over the "
        "clause's precomputed candidate attrs and running-state r_* attrs) + an "
        "effect list. reading_collapse._decode_roles_graph reads these frames from "
        "the graph, evaluates each guard via the Rust `evaluate`, and applies the "
        "applicable frames in priority order to the running state (r_subj/r_obj/…) — "
        "the graph-native replacement for the Python _resolve_roles_py cascade, byte-"
        "identical to _event_predication over the frozen Aesop+Grimm corpus. "
        "_ground_event emits predications from the resolved roles. Phase 3 adds the "
        "role-growth rungs so a novel role mints from a residual. Loaded idempotently "
        "by reading_collapse.ensure_event_frames via the Rust load_seed_manifest.")
    with open(SEED, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"wrote {len(manifest['frames'])} frames to {SEED}")


if __name__ == "__main__":
    main()
