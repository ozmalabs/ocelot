#!/usr/bin/env python3
"""Emit seeds/vision_margin.json — RUNG L1c: THE DERIVED ADMISSION BOUND that makes
L1b's COUNT predicate transfer to T1 continuous pose, as pure graph data (NO new Rust).

See VISION_MARGIN_PREREG.md.

THE FINDING THIS ACTS ON (VISION_UNIQUENESS_RESULTS.md, PART A): T1's `sqrt(2)/2`
verdict bound is NEAR-VACUOUS -- >=2 candidates lie inside it in 63/63 of T1's OWN
headline regime (median 4) -- so T1's clean 63/63 rests entirely on the `Argmin`
RANKING and the bound discriminates nothing. L1b named a MARGIN instrument and
deliberately did NOT build it: a threshold separating the measured 0.025 from the
measured 0.180 is a magic number chosen after seeing both (VISION_PROTOCOL sec 13).

THE DERIVATION (PART A, and it is NOT a margin -- see the prereg's rival audit, where
all six margin candidates are REJECTED BY MEASUREMENT):

`sqrt(2)/2` is the WORST-CASE PER-POINT rounding displacement -- a loose absolute
over-bound imported from the lattice's geometry, and an absolute constant is a view
from nowhere (sec 13). The quantity the system ACTUALLY HAS is the MHD that rounding
actually induces on its own codebook:

    eta_c := max over t in cp_angles of resid( c , round(rotate(c, t)) )

-- the largest residual a TRUE instance of `c` can produce. Computed from the CODEBOOK
x THE LATTICE x THE SYSTEM'S OWN HELD ANGLE GRID and nothing else: never from the test
observations, never from which answer is right. NO NEW CONSTANT -- the probe grid IS
`cp_angles`, the grid T1 already holds. Per-shape and resolution-adapted, where
`sqrt(2)/2` is one absolute number for everything.

`eta_c <= sqrt(2)/2` for every c BY CONSTRUCTION, so the admission set can only ever
SHRINK: this instrument CANNOT widen any invariance class (sec 8). It can only turn a
T1 claim into a refusal.

THE GATE is then L1b's predicate UNCHANGED, inside a bound that actually binds:

    k := Count( Filter( NodesOfType('ShapeSignature'), c, Lte( d_c , eta_c ) ) )
    admit iff k == 1 ; ambiguous iff k >= 2 ; none iff k == 0

THE RESIDUAL AND THE WINNER ARE EXTRACTED VERBATIM FROM `cp_recognize` (see
`_cp_residual_term` / `_cp_argmin_id_term`), NOT re-transcribed -- so the gate counts
EXACTLY what T1's recognizer admits and an ADMITTED row is byte-identical to T1's own
answer. Single source of truth; transcription is removed as a failure mode.

NO NEW CONSTANT (sec 13): the seed's entire literal set is {0.0, 0.5, 1.0, 2.0} -- the
flag comparison, and the counts 1 ("exactly one") and 2 ("more than one"), which are
definitions, not thresholds. The bound itself is COMPUTED, never written down.

NO `Times` ANYWHERE (process rule 4): the composition is Count/Filter/Lte/MaxOver/
MinOver/PointSetDist/Rotate/MapList. Asserted by the gate, so the a/b empty-product
trap cannot silently apply.

NAMESPACE SPLIT (L1b's discipline, inherited): these rules write ONLY `mg_*` and NEVER
touch `cp_*`/`status`/`covered_by`. That is load-bearing, not cosmetic --

  (a) both verdicts stay readable from ONE graph in ONE run, which is what makes the
      comparison a MEASUREMENT rather than two experiments; and
  (b) `run_rules` terminates on EXACT VALUE EQUALITY (sec 2.1), so writing a fresh
      attribute makes every effect value constant once set and the fixpoint is reached.
      Clearing T1's own `status` would let `cp_recognize` re-fire forever.

NO COMMITTED SEED IS EDITED. Purely additive, NOT boot-loaded, flag `margin` ships at
0.0 (OFF, sec 9), so with the default every committed result reproduces exactly.

ABSENCE-TOLERANT reads throughout: `MaxOver(NodesOfType('MarginParams'), ..., default
0.0)` for the flag -- NEVER `PickUnique` on a params node (sec 12.3 / process rule 3);
and the eta rule's once-only guard is `Not(Gte(Attr(c,'mg_eta'), 0.0))`, which is TRUE
when the attribute is ABSENT (verified: `Gte(absent, 0.0)` evaluates False).
"""
from __future__ import annotations
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_CP_SEED = os.path.join(_ROOT, "seeds", "continuous_pose.json")
_OUT = os.path.join(_ROOT, "seeds", "vision_margin.json")


def _cp_rule(name: str) -> dict:
    with open(_CP_SEED) as fh:
        seed = json.load(fh)
    for r in seed["rules"]:
        if r["name"] == name:
            return r
    raise SystemExit(f"{name} not found in {_CP_SEED}")


def _cp_residual_term() -> dict:
    """`cp_recognize`'s PER-CANDIDATE residual, EXTRACTED VERBATIM.

    It is the `value` of the OUTER `MinOver` in the rule's admission clause -- the
    `MinOver` over `cp_angles` of `PointSetDist(MapList(Rotate(c.points, t)), obs.points)`,
    free in `c`, `ag` and `obs`. Reused rather than retyped so the gate counts EXACTLY
    the candidates T1's recognizer scores.
    """
    where = _cp_rule("cp_recognize")["where"]
    for clause in where["items"]:
        if clause.get("type") == "Lte" and clause["a"].get("type") == "MinOver":
            inner = clause["a"]["value"]
            assert inner["type"] == "MinOver", "cp_recognize's inner residual moved"
            return inner
    raise SystemExit("cp_recognize's admission MinOver clause not found")


def _cp_argmin_id_term() -> dict:
    """`cp_recognize`'s `covered_by` effect term, EXTRACTED VERBATIM (the Argmin winner)."""
    for key, _t, attr, term in _cp_rule("cp_recognize")["effects"]:
        if key == "set_attr" and attr == "covered_by":
            return term["__term__"]
    raise SystemExit("cp_recognize's covered_by effect not found")


def _var(n: str) -> dict:
    return {"type": "Var", "name": n}


def _attr(n: str, k: str) -> dict:
    return {"type": "Attr", "node": _var(n), "key": k}


def _lit(v):
    return {"type": "Lit", "value": v}


def _flag_on() -> dict:
    """margin > 0.5, read ABSENCE-TOLERANTLY (never PickUnique, sec 12.3)."""
    return {"type": "Gt",
            "a": {"type": "MaxOver",
                  "source": {"type": "NodesOfType", "node_type": "MarginParams"},
                  "var_name": "mp",
                  "value": _attr("mp", "margin"),
                  "default": _lit(0.0)},
            "b": _lit(0.5)}


def _eta_term() -> dict:
    """THE DERIVATION, in the graph: eta_c = MAX over the codebook member's OWN rounded
    self-renders of the SAME residual T1 scores. Codebook x lattice x cp_angles only."""
    resid = _cp_residual_term()
    # the residual, re-pointed from the observation to the self-render `v`
    self_resid = json.loads(json.dumps(resid))
    self_resid["value"]["b"] = _var("v")
    return {"type": "MaxOver", "source": _attr("c", "mg_self"), "var_name": "v",
            "value": self_resid, "default": None}


def _count_term() -> dict:
    """k = the number of candidates whose residual falls within THEIR OWN eta.

    Same population `cp_recognize` searches (`NodesOfType('ShapeSignature')`), and
    absence-tolerant: a codebook-less ShapeSignature has no `mg_eta`, so `Lte(d, None)`
    is False and it is excluded -- it is never counted and never admitted."""
    return {"type": "Count",
            "source": {"type": "Filter",
                       "source": {"type": "NodesOfType", "node_type": "ShapeSignature"},
                       "var_name": "c",
                       "predicate": {"type": "Lte", "a": _cp_residual_term(),
                                     "b": _attr("c", "mg_eta")}}}


def _claimed_guard() -> list:
    """Fire ONLY where T1 ITSELF claimed a recognition. The instrument can therefore
    only ever turn a CLAIM into a REFUSAL -- it can never widen an invariance class
    (sec 8), and it cannot fire on an observation T1 already refused."""
    return [_flag_on(),
            {"type": "Eq", "a": _attr("obs", "status"),
             "b": _lit("recognized_continuous")}]


def build() -> dict:
    k = _count_term()
    match = [["ag", "observed", "obs"]]

    mg_eta = {
        "name": "mg_eta",
        "comment": (
            "THE DERIVATION (PART A), computed IN THE GRAPH. eta_c = MAX over the "
            "codebook member's own ROUNDED SELF-RENDERS (mg_self, blind-written by the "
            "adapter exactly as it writes any stimulus) of the SAME per-candidate "
            "residual `cp_recognize` scores, minimised over the agent's OWN held angle "
            "grid cp_angles. It is the LARGEST residual a TRUE instance of c can "
            "produce given the lattice -- the actual MHD rounding induces, where "
            "sqrt(2)/2 is the loose WORST-CASE PER-POINT over-bound. Depends on the "
            "codebook, the lattice and cp_angles ALONE: never on the test observations, "
            "never on which answer is right. NO NEW CONSTANT (the probe grid IS "
            "cp_angles). Fires ONCE per member: the guard Not(Gte(mg_eta, 0.0)) is TRUE "
            "only while the attribute is ABSENT, so the effect value is constant "
            "thereafter and the run_rules fixpoint terminates (sec 2.1)."),
        "match_type": "ShapeSignature",
        "match": [["ag", "has_codebook", "c"]],
        "where": {"type": "And", "items": [
            _flag_on(),
            {"type": "Not", "arg": {"type": "Gte", "a": _attr("c", "mg_eta"),
                                    "b": _lit(0.0)}}]},
        "effects": [["set_attr", "c", "mg_eta", {"__term__": _eta_term()}]],
    }

    mg_admit = {
        "name": "mg_admit",
        "comment": (
            "ADMIT branch (flag margin>0.5, OFF by default). T1 claimed this "
            "observation AND EXACTLY ONE codebook member falls within ITS OWN derived "
            "eta. The identity is `cp_recognize`'s own Argmin winner, term-for-term, so "
            "an admitted row is BYTE-IDENTICAL to T1's answer: the instrument SUBTRACTS "
            "ambiguous claims and adds nothing. Writes only mg_* -- never cp_*/status/"
            "covered_by -- so both verdicts are readable from ONE graph and every "
            "effect value is constant once set."),
        "match_type": "Observation",
        "match": match,
        "where": {"type": "And", "items": _claimed_guard() + [
            {"type": "Eq", "a": k, "b": _lit(1.0)}]},
        "effects": [
            ["set_attr", "obs", "mg_recognized", {"__term__": _lit(1.0)}],
            ["set_attr", "obs", "mg_covered_by", {"__term__": _cp_argmin_id_term()}],
            ["set_attr", "obs", "mg_status", {"__term__": _lit("mg_admitted")}],
            ["set_attr", "obs", "mg_ncand", {"__term__": k}],
        ],
    }

    mg_ambiguous = {
        "name": "mg_ambiguous",
        "comment": (
            "AMBIGUOUS branch -- THE RUNG'S REASON TO EXIST. TWO OR MORE candidates lie "
            "within their own eta, so the observation does not DETERMINE which held "
            "identity it is; T1's Argmin resolves that silently and, below the "
            "resolution floor, returns a CONFIDENT WRONG IDENTITY (measured: 22/63 at "
            "s=1). This REFUSES instead, and records HOW MANY candidates were in "
            "contention (mg_ncand) so the refusal is a POSITIVE DATUM and not an "
            "absence (sec 1.1's dead-arm lesson); mg_recognized is written EXPLICITLY "
            "to 0.0 for the same reason."),
        "match_type": "Observation",
        "match": match,
        "where": {"type": "And", "items": _claimed_guard() + [
            {"type": "Gte", "a": k, "b": _lit(2.0)}]},
        "effects": [
            ["set_attr", "obs", "mg_recognized", {"__term__": _lit(0.0)}],
            ["set_attr", "obs", "mg_status", {"__term__": _lit("mg_ambiguous")}],
            ["set_attr", "obs", "mg_ncand", {"__term__": k}],
        ],
    }

    mg_none = {
        "name": "mg_none",
        "comment": (
            "NONE branch: T1 claimed this observation but NO codebook member falls "
            "within its own eta -- T1's looser sqrt(2)/2 admitted a winner that the "
            "derived bound rejects outright. The honest verdict is that nothing held "
            "explains the observation. Completes the 3-way partition (k==1 / k>=2 / "
            "k==0) over exactly the observations T1 claimed, so every claimed row "
            "receives exactly one mg_status and the rules cannot both fire."),
        "match_type": "Observation",
        "match": match,
        "where": {"type": "And", "items": _claimed_guard() + [
            {"type": "Lte", "a": k, "b": _lit(0.0)}]},
        "effects": [
            ["set_attr", "obs", "mg_recognized", {"__term__": _lit(0.0)}],
            ["set_attr", "obs", "mg_status", {"__term__": _lit("mg_none")}],
            ["set_attr", "obs", "mg_ncand", {"__term__": k}],
        ],
    }

    return {
        "id": "vision_margin",
        "version": "1.0.0",
        "depends_on": ["continuous_pose"],
        "description": (
            "RUNG L1c -- THE DERIVED ADMISSION BOUND. T1's sqrt(2)/2 is the WORST-CASE "
            "PER-POINT rounding displacement and is near-vacuous (>=2 candidates inside "
            "it in 63/63 of T1's headline). eta_c -- the codebook's OWN self-rounding "
            "residual, computed from codebook x lattice x cp_angles alone -- is the "
            "bound that FALLS OUT, and inside it L1b's count predicate transfers "
            "unchanged. NO margin bound exists: all six margin candidates are rejected "
            "by measurement in VISION_MARGIN_PREREG.md / VISION_MARGIN_RESULTS.md. Pure "
            "composition over held Terms; NO new Rust, NO new constant, NO Times. "
            "eta_c <= sqrt(2)/2 by construction, so this can only SHRINK the admission "
            "set -- a refusal instrument, never a widening (sec 8). Additive: no "
            "committed seed is edited, not boot-loaded, flag ships OFF (sec 9)."),
        "microtheory": "vision_margin",
        # OFF by default (sec 9). Blind-written by the world adapter; read
        # absence-tolerantly via MaxOver(default 0) -- never PickUnique (sec 12.3).
        "nodes": [{"local_id": 0, "type": "MarginParams", "attrs": {"margin": 0.0}}],
        "edges": [],
        # Gamma vocabulary extension: the adapter marks WHICH ShapeSignatures are this
        # agent's pose codebook. Additive; no existing production is touched.
        "productions": [
            {"provenance": "seed:vision_margin:has_codebook",
             "src": {"type": "Agent", "var": "s"},
             "edge_type": "has_codebook",
             "tgt": {"type": "ShapeSignature", "var": "t"}}],
        "rules": [mg_eta, mg_admit, mg_ambiguous, mg_none],
    }


if __name__ == "__main__":
    seed = build()
    with open(_OUT, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print(f"wrote {_OUT}: {len(seed['rules'])} rules, {len(seed['nodes'])} nodes, "
          f"{len(seed['productions'])} productions")
