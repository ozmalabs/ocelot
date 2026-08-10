#!/usr/bin/env python3
"""Emit seeds/vision_uniqueness.json — RUNG L1b: THE UNIQUENESS GATE for the
SILENT-ARGMIN HAZARD, as pure graph data (NO new Rust).

See VISION_UNIQUENESS_PREREG.md.

THE FINDING THIS ACTS ON (VISION_LIGHTING_L1_RESULTS.md, "THE NEGATIVE"): below the
resolution floor (g ~ 0.06) L1's recognizer returns a CONFIDENT WRONG IDENTITY --
`refused = 0` in every failing row -- while TWO OR MORE candidates lie INSIDE the
verdict bound. The ambiguity is VISIBLE IN THE GRAPH and `Argmin` resolves it
SILENTLY. That is T3's `PickUnique` lesson one level up, in the continuous verdict.

THE GATE: recognition is admitted only when the winner is UNIQUE within the bound.

    ambiguous(R) := Gte( Count( Filter( Neighbours(ref,'has_identity'), cand,
                                        Lte( resid(R,cand), 1.0 ) ) ), 2 )

NO NEW CONSTANT. The bound 1.0 is L1's OWN falls-out bound -- ONE lattice step, the
sum of exactly two half-step roundings (VISION_PROTOCOL sec 13) -- inherited
UNCHANGED. The count 2 is not a threshold; it is the definition of "more than one".

THE RESIDUAL IS EXTRACTED VERBATIM FROM `l1_recognize` (see `_l1_residual_term`
below), NOT re-transcribed. That makes the gate's admission set IDENTICAL to the
recognizer's BY CONSTRUCTION -- a single source of truth -- and it removes
transcription as a failure mode, so the risk in arm C is concentrated where it
belongs: in the COMPOSITION (Filter/Count/Gte), the guards, and the fixpoint
behaviour.

NAMESPACE SPLIT (L1's own discipline, applied to itself): these rules write ONLY
`uq_*` attributes and NEVER touch `l1_*`. That is not cosmetic --

  (a) it makes the gated and ungated verdicts readable SIDE BY SIDE from the SAME
      graph in the SAME run, which is what makes the comparison a measurement
      rather than two experiments; and
  (b) it is what makes the rule set CONVERGE. `l1_recognize`'s guard does not read
      `l1_recognized`, so a gate that CLEARED `l1_recognized` would be re-fired by
      `l1_recognize` on the next sweep, flipping the attribute forever -- and
      `run_rules` terminates on EXACT VALUE EQUALITY (VISION_PROTOCOL sec 2.1), so
      that build would not terminate. Writing a fresh attribute makes every effect
      value CONSTANT once set, so the fixpoint is reached.

NO COMMITTED SEED IS EDITED. This seed is purely additive and is NOT boot-loaded;
its flag `uniqueness` ships at 0.0 (OFF, sec 9), so with the default every committed
result reproduces exactly.

ABSENCE-TOLERANT FLAG READ: `MaxOver(NodesOfType('UniquenessParams'), ..., default 0.0)`
-- NEVER `PickUnique` on a params node (sec 12.3 / process rule 3). With the params
node ABSENT the read returns 0.0 and the gate is off, which is the correct default.
"""
from __future__ import annotations
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_L1_SEED = os.path.join(_ROOT, "seeds", "vision_lighting_l1.json")
_OUT = os.path.join(_ROOT, "seeds", "vision_uniqueness.json")

LATTICE_STEP = 1.0   # L1's falls-out bound, INHERITED (not a new number)


def _l1_rule(name: str) -> dict:
    with open(_L1_SEED) as fh:
        seed = json.load(fh)
    for r in seed["rules"]:
        if r["name"] == name:
            return r
    raise SystemExit(f"{name} not found in {_L1_SEED}")


def _l1_residual_term() -> dict:
    """`l1_recognize`'s per-candidate residual, EXTRACTED VERBATIM.

    It is the `value` of the `MinOver` in the rule's admission clause -- the
    per-channel L-infinity `Max` of `Abs(Minus(c_ch, Times([p_ch, Div(a_ch, pa_ch)])))`,
    free in `R`, `frame` and the candidate variable `cand`. Reused rather than
    retyped so the gate counts EXACTLY the candidates the recognizer would admit.
    """
    where = _l1_rule("l1_recognize")["where"]
    for clause in where["items"]:
        if clause.get("type") == "Lte" and clause["a"].get("type") == "MinOver":
            return clause["a"]["value"]
    raise SystemExit("l1_recognize's admission MinOver clause not found")


def _l1_argmin_id_term() -> dict:
    """`l1_recognize`'s `l1_id` effect term, EXTRACTED VERBATIM (the Argmin winner)."""
    for key, _target, attr, term in _l1_rule("l1_recognize")["effects"]:
        if key == "set_attr" and attr == "l1_id":
            return term["__term__"]
    raise SystemExit("l1_recognize's l1_id effect not found")


def _flag_on() -> dict:
    """uniqueness > 0.5, read ABSENCE-TOLERANTLY (never PickUnique)."""
    return {
        "type": "Gt",
        "a": {"type": "MaxOver",
              "source": {"type": "NodesOfType", "node_type": "UniquenessParams"},
              "var_name": "up",
              "value": {"type": "Attr", "node": {"type": "Var", "name": "up"},
                        "key": "uniqueness"},
              "default": {"type": "Lit", "value": 0.0}},
        "b": {"type": "Lit", "value": 0.5},
    }


def _in_bound_count() -> dict:
    """Count(Filter(the reference frame's OWN codebook, resid <= ONE LATTICE STEP)).

    The codebook source is `Neighbours(ref,'has_identity')` -- the SAME hub-scoped
    population `l1_recognize` searches, NOT a global `NodesOfType` grab.
    """
    return {
        "type": "Count",
        "source": {
            "type": "Filter",
            "source": {"type": "Neighbours", "node": {"type": "Var", "name": "ref"},
                       "edge_type": "has_identity", "any_type": False},
            "var_name": "cand",
            "predicate": {"type": "Lte",
                          "a": _l1_residual_term(),
                          "b": {"type": "Lit", "value": LATTICE_STEP}},
        },
    }


def _common_guard() -> list:
    """Fire only where L1 ITSELF claimed a recognition. The gate can therefore only
    ever turn a CLAIM into a REFUSAL -- it can never widen an invariance class
    (sec 8), and it cannot fire on a surface L1 already refused."""
    return [
        _flag_on(),
        {"type": "Gt",
         "a": {"type": "Attr", "node": {"type": "Var", "name": "R"},
               "key": "l1_recognized"},
         "b": {"type": "Lit", "value": 0.5}},
    ]


def build() -> dict:
    count = _in_bound_count()
    match = [["frame", "has_surface", "R"], ["frame", "compares_to", "ref"]]

    uq_admit = {
        "name": "uq_admit",
        "comment": (
            "THE UNIQUENESS GATE, ADMIT branch (flag uniqueness>0.5, OFF by default). "
            "L1 claimed this surface AND the winner is UNIQUE within the verdict bound "
            "-- exactly ONE candidate in the reference frame's own has_identity "
            "codebook renders to within ONE LATTICE STEP. The identity is L1's own "
            "Argmin winner, term-for-term, so an ADMITTED row is byte-identical to "
            "L1's answer: the gate SUBTRACTS ambiguous claims and adds nothing. "
            "Writes only uq_* -- never l1_* -- so both verdicts are readable from ONE "
            "graph and every effect value is constant once set (the fixpoint "
            "terminates, VISION_PROTOCOL sec 2.1)."),
        "match": match,
        "where": {"type": "And", "items": _common_guard() + [
            {"type": "Lte", "a": count, "b": {"type": "Lit", "value": 1.0}}]},
        "effects": [
            ["set_attr", "R", "uq_recognized", {"__term__": {"type": "Lit", "value": 1.0}}],
            ["set_attr", "R", "uq_id", {"__term__": _l1_argmin_id_term()}],
            ["set_attr", "R", "uq_status", {"__term__": {"type": "Lit", "value": "uq_recognized"}}],
            ["set_attr", "R", "uq_ncand", {"__term__": count}],
        ],
    }

    uq_refuse_ambiguous = {
        "name": "uq_refuse_ambiguous",
        "comment": (
            "THE UNIQUENESS GATE, REFUSE branch -- THE RUNG'S REASON TO EXIST. "
            "TWO OR MORE candidates lie INSIDE the verdict bound, so the observation "
            "does not determine WHICH held identity it is; the Argmin would resolve "
            "that silently and return a CONFIDENT WRONG IDENTITY (measured: "
            "VISION_LIGHTING_L1_RESULTS.md, g<=0.06). The gate REFUSES instead, and "
            "records HOW MANY candidates were tied inside the bound (uq_ncand) so the "
            "refusal is a POSITIVE DATUM and not an absence (sec 1.1's dead-arm "
            "lesson). uq_recognized is written EXPLICITLY to 0.0 rather than left "
            "absent, for the same reason. Exact complement of uq_admit on the SAME "
            "count term, so the two rules PARTITION the surfaces L1 claimed."),
        "match": match,
        "where": {"type": "And", "items": _common_guard() + [
            {"type": "Gte", "a": count, "b": {"type": "Lit", "value": 2.0}}]},
        "effects": [
            ["set_attr", "R", "uq_recognized", {"__term__": {"type": "Lit", "value": 0.0}}],
            ["set_attr", "R", "uq_status", {"__term__": {"type": "Lit", "value": "uq_ambiguous"}}],
            ["set_attr", "R", "uq_ncand", {"__term__": count}],
        ],
    }

    return {
        "id": "vision_uniqueness",
        "version": "1.0.0",
        "depends_on": ["vision_lighting_l1"],
        "description": (
            "RUNG L1b -- THE UNIQUENESS GATE. Recognition REFUSES when >=2 candidates "
            "lie within the verdict bound, instead of letting Argmin resolve the "
            "ambiguity silently. Pure composition over held Terms (Count/Filter/Lte/"
            "Gte/Neighbours); NO new Rust, NO new constant (L1's ONE-LATTICE-STEP "
            "bound is inherited unchanged). Additive: no committed seed is edited, "
            "the seed is not boot-loaded, and the flag ships OFF (sec 9)."),
        "microtheory": "vision_uniqueness",
        # OFF by default (sec 9). Blind-written by the world adapter; read
        # absence-tolerantly via MaxOver(default 0) -- never PickUnique (sec 12.3).
        "nodes": [
            {"local_id": 0, "type": "UniquenessParams",
             "attrs": {"uniqueness": 0.0}}],
        "edges": [],
        "productions": [],
        "rules": [uq_admit, uq_refuse_ambiguous],
    }


if __name__ == "__main__":
    seed = build()
    with open(_OUT, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print(f"wrote {_OUT}: {len(seed['rules'])} rules, {len(seed['nodes'])} nodes")
