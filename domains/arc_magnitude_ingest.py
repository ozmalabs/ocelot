"""CONSTRAINTS, ORDER-N VALUE, THE MAGNITUDE LADDER — the world adapter.

MECHANICAL I/O ONLY, held to the same module-specific form
`domains/arc_goal_ingest.py` passes: it never imports `substrate_rs`, never
calls `.evaluate(`, never calls `run_rules`, and its only substrate contact is
`add_node` / `node` / `nodes` / `set_attr` / `add_edge_unchecked` /
`load_seed_manifest`.  There is therefore no place in it for a decision over
graph state to hide.

FOUR JOBS, all translation:

1. **self-load the seed** — `seeds/arc_magnitude.json` carries
   `self_load_only`, so `substrate/boot_all.py::_read_seeds` SKIPS it.
   `ensure_arc_magnitude` is the on-demand loader, idempotent on a
   `Seed{id:'arc_magnitude'}` marker.  (The `arc_goal_ingest.ensure_arc_goals`
   precedent, which is itself the `reading_collapse::_ensure_role_decode_loop`
   precedent.)

2. **RESOLVE ARTIFACT PATHS — and this is the whole point of MG2.**  The
   attrition factors are **NOT IN THE SEED**.  The seed ships
   `ArcAttritionKey` nodes carrying only a NAME, an ARTIFACT and two DOTTED
   PATHS; this adapter opens the artifact, walks the paths, and writes back
   `numerator_n` / `denominator_n` / `resolved`.  **The ratio itself is
   computed by a RULE** (`mg_attrition_factor`, `Div(numerator_n,
   denominator_n)`), so no number anywhere on this path was authored — each is
   the content of a named file at a named path, and an unresolvable path
   writes `resolved: 0.0` rather than a default.

   A9: *"the per-order factors must be READ from results artifacts and
   traceable to them.  An authored projection is unbounded in the dangerous
   direction — worse than an authored cost_bits, because it justifies rather
   than restrains."*  Making the number physically absent from the seed is the
   strongest available form of that.

3. **read the MEASURED TIER LADDER** — `results/arc6_structural_ceiling.json`
   `bundles` is a real ladder with per-tier cost (B0 8 units / 0 new TermNodes
   / 10 unlocked, B1 18/10/26, B2 24/14/32, B3 28/17/42).  The adapter reads
   it and writes one `ArcTier` per bundle.  **The increments are DIFFERENCES
   of read numbers, not estimates.**

   THE LADDER'S KEY IS ESTABLISHED BY A MEASURED POPULATION JOIN, NOT BY
   AUTHORING.  Which blocker class does this ladder describe?  The adapter
   does not decide: it reads `arc6_a_ceiling.json::blocker_split.
   ids_over_live_unreached` (three id lists, one per blocker name) and
   `arc6_structural_ceiling.json::population.structural_42_ids`, and reports
   which blocker name's id list is EQUAL to the ladder's own population.  Both
   lists and the equality land in the results artifact, and
   `test_mg2_the_ladder_key_is_a_MEASURED_population_join` re-derives it from
   the two files.  This is a comparison of two FILES, not a conditional over
   graph state.

4. **carry a constraint reply** — a human answering the constraints question
   supplies a horizon / scope / competing requirement in whatever external
   form the world uses; `attach_constraint_reply` writes it onto the reply
   `Message` as `con_*` attrs, exactly as `arc_goal_ingest.attach_reply`
   writes `cond_*`.  The RULES decide whether that makes a conditioned
   constraint or one that expires at the next measurement epoch.  **The reply
   text is never parsed, and nothing here derives a signature from a string.**
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from substrate.seed_loader import manifest_for

SEED_ID = "arc_magnitude"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- #
#  1.  Self-load.
# --------------------------------------------------------------------------- #
def ensure_arc_magnitude(sub, ag_node) -> bool:
    """Install `seeds/arc_magnitude.json` if it is not already present."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == SEED_ID:
            return False
    sub._inner.load_seed_manifest(manifest_for(SEED_ID), ag_node)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == SEED_ID:
            return True
    sub.add_node("Seed", {"id": SEED_ID, "version": "1.0.0"})
    return True


# --------------------------------------------------------------------------- #
#  2.  Dotted-path resolution over a results artifact.
# --------------------------------------------------------------------------- #
def _resolve(doc, path: str):
    """Walk a dotted path.  A trailing `|len` takes the length of a list.

    Returns None when any segment is absent — an unresolvable path must be
    DISTINGUISHABLE from a resolved zero, because "no measured basis" and "a
    measured zero" are different facts and MG2 treats them differently.
    """
    take_len = False
    if path.endswith("|len"):
        take_len = True
        path = path[: -len("|len")]
    cur = doc
    for seg in path.split("."):
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None
    if take_len:
        return float(len(cur)) if isinstance(cur, (list, tuple)) else None
    return float(cur) if isinstance(cur, (int, float)) and not isinstance(cur, bool) else None


def _load_artifact(rel: str):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def resolve_attrition_keys(sub) -> list:
    """For every `ArcAttritionKey` on the graph, open its artifact and walk its
    two paths.  Writes `numerator_n`, `denominator_n`, `resolved`.

    NO RATIO IS COMPUTED HERE — `mg_attrition_factor` does that in a Term.
    """
    out = []
    for n in sub.nodes("ArcAttritionKey"):
        a = sub.node(n)["attrs"]
        art = a.get("evidence_artifact")
        doc = _load_artifact(art) if art else None
        num = _resolve(doc, a["numerator_path"]) if doc is not None else None
        den = _resolve(doc, a["denominator_path"]) if doc is not None else None
        ok = num is not None and den is not None
        if ok:
            sub.set_attr(n, "numerator_n", num)
            sub.set_attr(n, "denominator_n", den)
        sub.set_attr(n, "resolved", 1.0 if ok else 0.0)
        out.append({"name": a.get("name"), "role": a.get("order_role"),
                    "evidence_artifact": art,
                    "numerator_path": a["numerator_path"],
                    "denominator_path": a["denominator_path"],
                    "numerator_n": num, "denominator_n": den,
                    "resolved": ok})
    return out


# --------------------------------------------------------------------------- #
#  3.  The measured tier ladder, and its MEASURED population join.
# --------------------------------------------------------------------------- #
LADDER_ARTIFACT = "results/arc6_structural_ceiling.json"
BLOCKER_ARTIFACT = "results/arc6_a_ceiling.json"


def probe_tier_ladder() -> dict:
    """Read the bundle ladder + establish its key by population equality.

    Returns a record with everything needed to audit the join: both id lists,
    the equality, and the per-tier numbers with the path each came from.
    """
    sc = _load_artifact(LADDER_ARTIFACT)
    ac = _load_artifact(BLOCKER_ARTIFACT)
    rec: dict = {"ladder_artifact": LADDER_ARTIFACT,
                 "ladder_path": "bundles",
                 "blocker_artifact": BLOCKER_ARTIFACT,
                 "blocker_path": "blocker_split.ids_over_live_unreached",
                 "population_path": "population.structural_42_ids",
                 "resolved": False, "tiers": [], "ladder_key": None,
                 "population_join": {}}
    if sc is None or ac is None:
        return rec

    pop = (sc.get("population") or {}).get("structural_42_ids")
    split = ((ac.get("blocker_split") or {}).get("ids_over_live_unreached") or {})
    matches = sorted(k for k, v in split.items()
                     if isinstance(v, list) and sorted(v) == sorted(pop or []))
    rec["population_join"] = {
        "ladder_population_n": len(pop or []),
        "ladder_population_ids": sorted(pop or []),
        "blocker_names_offered": sorted(split.keys()),
        "blocker_ids_by_name_n": {k: len(v) for k, v in sorted(split.items())},
        "names_whose_id_list_is_EQUAL_to_the_ladder_population": matches,
        "_why": ("which blocker class the ladder describes is ESTABLISHED BY "
                 "SET EQUALITY OF TWO MEASURED ID LISTS, not authored. Exactly "
                 "one name matches; a zero-match or multi-match must leave the "
                 "ladder unkeyed rather than pick one."),
    }
    if len(matches) != 1:
        return rec
    key = matches[0]
    rec["ladder_key"] = key

    bundles = sc.get("bundles") or []
    prev_unlocked = 0.0
    for i, b in enumerate(bundles):
        n_unlocked = float(b.get("n_unlocked"))
        rec["tiers"].append({
            "order": float(i + 1),
            "bundle": b.get("bundle"),
            "n_unlocked_cumulative": n_unlocked,
            "increment_n": n_unlocked - prev_unlocked,
            "cum_cost_units": float(b.get("n_units")),
            "cum_cost_new_termnodes": float(b.get("new_termnodes")),
            "evidence_artifact": LADDER_ARTIFACT,
            "evidence_path": "bundles[%d]" % i,
        })
        prev_unlocked = n_unlocked
    rec["resolved"] = bool(rec["tiers"])
    return rec


def install_tier_ladder(sub, rec: dict) -> Optional[Any]:
    """Write the ladder as graph data.  Mechanical: one node per read tier."""
    if not rec.get("resolved") or not rec.get("ladder_key"):
        return None
    lad = sub.add_node("ArcTierLadder", {
        "ladder_key": rec["ladder_key"],
        "n_tiers": float(len(rec["tiers"])),
        "evidence_artifact": rec["ladder_artifact"],
        "evidence_path": rec["ladder_path"],
        "population_join_is_measured": 1.0,
    })
    for t in rec["tiers"]:
        tn = sub.add_node("ArcTier", dict(t, ladder_key=rec["ladder_key"]))
        sub._inner.add_edge_unchecked(lad, "has_tier", tn)
    return lad


# --------------------------------------------------------------------------- #
#  4.  The calibration record — projections this project has already MADE and
#      what they RETURNED.  Read, reported, and deliberately NOT multiplied in.
# --------------------------------------------------------------------------- #
CALIBRATION = (
    ("a_ceiling", "results/arc6_a_ceiling.json",
     "ceilings.STRICT_kernel_verified_AND_nothing_else_blocks.n",
     None,
     "PROJECTED a strict kernel-verified set; RETURNED 0 conversions. The "
     "prereg's headline quotes 5 ids strict (80, 246, 248, 293, 422) against "
     "this artifact's own 8 at the path above -- a NARROWER hand-audit of the "
     "same set, recorded here rather than reconciled, because the projected "
     "figure is not what the calibration turns on. The RETURNED figure is 0 "
     "either way."),
    ("seam_d", "results/arc6_d_loo.json",
     "n_atoms", "m1_leave_one_out.n_full_table_fired",
     "PROJECTED 36/36 on its own authored population; RETURNED leave-one-out "
     "0/36, loo_survivor_ids == []. The worst inventory-to-transfer gap in the "
     "project, and the reason a per-goal ladder assignment is refused here."),
    ("tier_0", "results/arc6_tier0.json",
     None, None,
     "PROJECTED ~3.2 (10 B0 ids x the 32% S4 prior -- the SAME factor this "
     "rung reads at reach_to_conversion); RETURNED 0. "
     "hs_verdicts.HS1_primary_ge_3_of_10_convert.converted_b0_ids == [], "
     "verdict FAIL. THIS IS THE SHARPEST CALIBRATION POINT AVAILABLE, because "
     "the projection was made with this rung's own arithmetic."),
)


def probe_calibration() -> list:
    """The residual set as a calibration record: what was PROJECTED and what
    was RETURNED, each read from its own artifact where a path resolves.

    REPORTED, NOT MULTIPLIED IN.  0 of 3 as a point estimate is a factor of
    0.0, which would zero every projection and make order-N identical to
    order-1 by construction — single-source deciding, the standing failure.
    """
    out = []
    for name, art, proj_path, ret_path, note in CALIBRATION:
        doc = _load_artifact(art)
        out.append({
            "case": name, "evidence_artifact": art,
            "artifact_present": doc is not None,
            "projected_path": proj_path,
            "projected_n": (_resolve(doc, proj_path)
                            if (doc is not None and proj_path) else None),
            "returned_path": ret_path,
            "returned_n": (_resolve(doc, ret_path)
                           if (doc is not None and ret_path) else None),
            "note": note,
        })
    return out


# --------------------------------------------------------------------------- #
#  5.  A constraint reply, and the condition the world attached to it.
# --------------------------------------------------------------------------- #
def attach_constraint_reply(sub, question_node, text: str, *,
                            con_kind: str,
                            horizon_units: Optional[float] = None,
                            scope_seam: Optional[str] = None,
                            competing_units: Optional[float] = None,
                            cond_kind: Optional[str] = None,
                            cond_filter_value: Optional[str] = None,
                            cond_expected_str: Optional[str] = None,
                            cond_expected: Optional[float] = None,
                            sender: str = "interlocutor") -> Any:
    """Write an inbound constraint answer into the graph.

    `con_*` and `cond_*` are passed through EXACTLY as the world supplied them
    — absent means absent.  The adapter does not infer a condition from the
    text and does not decide whether the reply "counts": the mirrored
    conditioned/unconditioned rules do that, on the presence of `cond_kind`.
    """
    attrs = {"from": sender, "text": text, "kind": "arc_constraint_reply",
             "con_kind": con_kind}
    if horizon_units is not None:
        attrs["con_horizon_units"] = float(horizon_units)
    if scope_seam is not None:
        attrs["con_scope_seam"] = scope_seam
    if competing_units is not None:
        attrs["con_competing_units"] = float(competing_units)
    if cond_kind is not None:
        attrs["cond_kind"] = cond_kind
    if cond_filter_value is not None:
        attrs["cond_filter_value"] = cond_filter_value
    if cond_expected_str is not None:
        attrs["cond_expected_str"] = cond_expected_str
    if cond_expected is not None:
        attrs["cond_expected"] = cond_expected
    m = sub.add_node("Message", attrs)
    sub._inner.add_edge_unchecked(m, "responds_to", question_node)
    return m


# --------------------------------------------------------------------------- #
#  Read-off helpers.  Pure queries for the write-up / the gates.
# --------------------------------------------------------------------------- #
def constraints(sub) -> list:
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("ArcConstraint")]


def tiers(sub) -> list:
    return sorted((dict(sub.node(n)["attrs"]) for n in sub.nodes("ArcTier")),
                  key=lambda d: d.get("order") or 0.0)


def attrition(sub) -> list:
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("ArcAttritionKey")]


def mag_selection(sub) -> dict:
    for n in sub.nodes("ArcAgenda"):
        a = sub.node(n)["attrs"]
        return {k: v for k, v in a.items() if k.startswith("mg_")}
    return {}


def goal_rows(sub) -> list:
    return [dict(sub.node(n)["attrs"], _id=str(n)) for n in sub.nodes("ArcGoal")]


def constraint_questions(sub) -> list:
    return [dict(sub.node(n)["attrs"]) for n in sub.nodes("ArcConstraintQuestion")]
