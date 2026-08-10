"""grounding_reach — the GROUNDING-REACHABILITY substrate.

THE THEORY (this module builds the SUBSTRATE only; the agent authors the
guard RULE that consumes it in a follow-on task): a cheap-model basin-snap
that is confidently WRONG has LOW residual within its own basin (it collapsed
cleanly onto a self-consistent local minimum), so residual alone cannot tell
it apart from a genuinely-correct collapse. What DOES distinguish them is
whether the collapse's grounding chain terminates at something EXTERNAL to
the agent's own generative loop (reality / a teacher / an observed
consequence / a sensor reading) or loops back into the agent's own
self-generated structure forever. This module makes "groundedness" a
QUERYABLE GRAPH PROPERTY: a `grounded_in` edge channel + a small anchor
vocabulary + the transitive-closure query over it.

THE PRIMITIVE: `ReachableFrom(node, edge_type)` — a Term the agent itself
specified and had installed in substrate_rs (BFS-to-fixpoint over
`Neighbours`, see runners/dsl/src/term.rs and
domains/self_extend_rust.agent_specify_reachable_from_primitive). This module
does NOT rebuild it; `grounding_reach()` below is a thin mechanical caller of
the REAL installed Term via `native.evaluate(...)`, exactly the pattern
worlds/browser.py's affordance mirror and tests/test_browser_reachable.py
already use for a different edge type (`contains`). Grounding-reach is that
SAME primitive pointed at a new edge type, `grounded_in`.

THE ANCHOR VOCABULARY (4 kinds — a node type IS its own anchor-kind marker,
no separate `kind` enum needed beyond that):

  SensorAnchor      — a raw perceptual reading a world adapter mechanically
                       ingested from outside the agent (a camera frame, a mic
                       sample). Mapped from EXISTING signals only:
                         * `Agent -perceives-> VisionPercept`   (world_adapter.
                           update_vision — the GraphEye cortex's per-azimuth
                           percept nodes)
                         * `Agent -sees_shape-> VisionPolygon`  (same method —
                           the cortex's detected-shape nodes)
                         * `Message{source:"audio"}`            (world_adapter.
                           ingest_audio_file — one Message per heard
                           utterance, source stamped "audio" only when the
                           bytes truly came from an audio file) plus its
                           `has_mention -> AcousticSign` (the recognised
                           acoustic unit the decode chain actually produced).

  TeacherAnchor     — a real teacher exchange: the agent formulated its OWN
                       question from a genuine self-diagnosed confusion and a
                       teacher (LLM partner / human / peer) answered it.
                       Mapped from: `TaughtHint{origin:"teacher_hook"}`
                       (domains/teacher_hook.ask_if_needed — the ONE place a
                       TaughtHint is stamped with that origin; other TaughtHint
                       origins are the agent's own self-derived verdicts, not
                       reused here, to avoid fabricating a teacher that wasn't
                       there).

  ConsequenceAnchor — an observed action-outcome: an Experiment the agent
                       authored, ran, and had JUDGED against a real produced
                       Run's score/frames (reflective_faculty's
                       `judge_experiment_outcome_*` rule family — outcome is
                       computed from `run.score / run.frames`, a real played
                       trial, never asserted). Mapped from:
                       `Experiment{outcome: "supported"|"refuted"|
                       "inconclusive"}` (outcome is only ever set by that rule
                       family reading a `produced` Run with `status=="done"`).

  RealityAnchor     — the external world OBJECT itself (as distinct from the
                       sensory reading of it): something currently bound to a
                       live vision percept, i.e. confirmed present outside the
                       agent right now. Mapped from: the Instance a
                       `VisionPolygon -depicts-> Instance` edge names
                       (world_adapter.update_vision's percept/world binding).

Every mapping above is a MECHANICAL translation of a signal the codebase
already writes for an unrelated reason (perception ingestion, the teacher
hook, the self-experiment judge rule, the vision/world binding) — nothing is
invented. `ensure_grounding_edges` only adds a `grounded_in` edge (+ mints the
matching anchor singleton, once) alongside each; it never decides which
existing signal COUNTS (that decision is fixed, in code, and documented
above), so it is the same admissible-adapter shape `substrate/boot_all.py`'s
`_mint_seed_summary` / `domains/self_model.py`'s `ensure_rule_provenance` use:
idempotent, mechanical, no agent reasoning.

THE FLAG: `flag_ungrounded_confident` is the OTHER half of the substrate — a
node with LOW residual (looks solved) AND HIGH confidence (the model is sure)
AND `grounding_reach(...).reached is False` (nothing outside the agent's own
loop backs it up) is exactly the residual-blind confident-wrong shape the
2026-07-02 residual-salience incident hit (a saturated axis flat-tied to
salience-zero and got re-picked 24x — see seeds/residual_salience.json's
description). This function only FLAGS (mints a `GroundingGap` node); it does
not escalate or correct anything — a follow-on, agent-authored guard RULE
consumes `GroundingGap` nodes to decide what to do about them. That authoring
is explicitly NOT this module's job (see the top-level task note / CLAUDE.md:
no agent decisions in Python).
"""
from __future__ import annotations

from typing import Any, Optional

ANCHOR_KINDS = ("RealityAnchor", "TeacherAnchor", "ConsequenceAnchor", "SensorAnchor")
_GAP_TYPE = "GroundingGap"
_EDGE = "grounded_in"


# ---------------------------------------------------------------------------
# resolve (substrate, native) from whatever the caller passed — the same duck
# typing domains/self_model.py and domains/teach.py already use, kept local
# (no import of either) so this module carries no coupling to files under
# concurrent edit.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _add_edge_unchecked(native, src, edge_type, tgt) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt)
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt, {})


def _ensure_anchor(sub, kind: str):
    """Idempotent singleton anchor node for `kind` (one per kind — anchor
    IDENTITY doesn't matter, only that the reachability closure intersects
    a node of that TYPE, so a shared singleton avoids bloat)."""
    for n in sub.nodes(kind):
        return n
    return sub.add_node(kind, {"kind": kind})


def _ground(sub, native, node, anchor) -> bool:
    """Idempotently mint `node -grounded_in-> anchor`. Mechanical adapter
    mutation (add_edge_unchecked — the same no-Γ-gate idiom
    substrate/world_adapter.py uses for perceives/sees_shape/depicts), guarded
    by has_edge so a re-run never duplicates. Returns True iff newly added."""
    if not sub.has_node(node) or not sub.has_node(anchor):
        return False
    if sub.has_edge(node, _EDGE, anchor):
        return False
    _add_edge_unchecked(native, node, _EDGE, anchor)
    return True


# ---------------------------------------------------------------------------
# MECHANICAL EDGE-MINTING — walk the EXISTING grounding relations (documented
# in the module docstring) and mint `grounded_in` edges + anchor singletons
# where they already imply grounding. No decision: every mapping is fixed.
# ---------------------------------------------------------------------------
def ensure_grounding_edges(agent) -> dict:
    """Idempotent. Returns {sensor, teacher, consequence, reality, total} —
    the number of NEW `grounded_in` edges minted per anchor kind this call
    (0 on a re-run over an unchanged graph)."""
    sub, native = _resolve(agent)
    minted = {"sensor": 0, "teacher": 0, "consequence": 0, "reality": 0}
    anchors: dict = {}

    def anchor(kind: str):
        a = anchors.get(kind)
        if a is None:
            a = _ensure_anchor(sub, kind)
            anchors[kind] = a
        return a

    # --- SensorAnchor (vision): Agent -perceives-> VisionPercept,
    #     Agent -sees_shape-> VisionPolygon (world_adapter.update_vision). ---
    try:
        agents = sub.nodes("Agent")
    except Exception:
        agents = []
    for ag in agents:
        for pid in sub.neighbours(ag, "perceives"):
            if _ground(sub, native, pid, anchor("SensorAnchor")):
                minted["sensor"] += 1
        for sid in sub.neighbours(ag, "sees_shape"):
            if _ground(sub, native, sid, anchor("SensorAnchor")):
                minted["sensor"] += 1

    # --- SensorAnchor (audio): Message{source:"audio"} + its AcousticSign
    #     mention (world_adapter.ingest_audio_file). ---
    for mid in sub.nodes("Message"):
        at = sub.node(mid)["attrs"]
        if at.get("source") != "audio":
            continue
        if _ground(sub, native, mid, anchor("SensorAnchor")):
            minted["sensor"] += 1
        for sg in sub.neighbours(mid, "has_mention"):
            if _ground(sub, native, sg, anchor("SensorAnchor")):
                minted["sensor"] += 1

    # --- TeacherAnchor: TaughtHint{origin:"teacher_hook"} (the ONE origin
    #     stamped by a real ask()-answered teacher exchange). ---
    for th in sub.nodes("TaughtHint"):
        at = sub.node(th)["attrs"]
        if at.get("origin") != "teacher_hook":
            continue
        if _ground(sub, native, th, anchor("TeacherAnchor")):
            minted["teacher"] += 1

    # --- ConsequenceAnchor: Experiment{outcome: set} — only ever set by the
    #     judge_experiment_outcome_* rule family from a real produced+done
    #     Run's score/frames (reflective_faculty.py). ---
    for exp in sub.nodes("Experiment"):
        at = sub.node(exp)["attrs"]
        if not at.get("outcome"):
            continue
        if _ground(sub, native, exp, anchor("ConsequenceAnchor")):
            minted["consequence"] += 1

    # --- RealityAnchor: the world OBJECT a live VisionPolygon -depicts->
    #     (world_adapter.update_vision's percept/world binding). ---
    for poly in sub.nodes("VisionPolygon"):
        for inst in sub.neighbours(poly, "depicts"):
            if _ground(sub, native, inst, anchor("RealityAnchor")):
                minted["reality"] += 1

    minted["total"] = sum(minted.values())
    return minted


# ---------------------------------------------------------------------------
# THE QUERY — grounding_reach uses the REAL installed native ReachableFrom
# Term (not a Python re-walk of the grounded_in graph) for the reached/
# anchors verdict. `hops` is a secondary, best-effort BFS report (native
# neighbours() per hop, Python only orchestrates the loop — same shape the
# Rust ReachableFrom itself uses internally) that never overrides that
# verdict.
# ---------------------------------------------------------------------------
def _reachable_from_native(native, node, edge_type: str = _EDGE) -> set:
    term = {"type": "ReachableFrom",
            "node": {"type": "Var", "name": "n"},
            "edge_type": edge_type}
    try:
        result = native.evaluate(term, {"n": node})
    except Exception:
        return set()
    return set(result) if result else set()


def grounding_reach(agent, node, *, max_hops: int = 64) -> dict[str, Any]:
    """Does `node`'s `grounded_in` chain reach an external anchor?

    {reached: bool, anchors: [kind, ...] sorted, hops: int|None}

    `reached`/`anchors` come DIRECTLY from evaluating the agent-installed
    `ReachableFrom(node, "grounded_in")` Term in Rust, intersected with the
    live anchor-typed nodes — the transitive closure itself is never
    recomputed in Python. `hops` (None if unreached) is a bounded frontier
    walk purely for reporting, one hop at a time via the native
    `neighbours()` accessor."""
    sub, native = _resolve(agent)
    if not sub.has_node(node):
        return {"reached": False, "anchors": [], "hops": None}

    reached_set = _reachable_from_native(native, node)
    anchor_kinds: list = []
    anchor_nodes: list = []
    for r in reached_set:
        if not sub.has_node(r):
            continue
        t = sub.node(r)["type"]
        if t in ANCHOR_KINDS:
            anchor_kinds.append(t)
            anchor_nodes.append(r)
    reached = bool(anchor_nodes)

    hops = None
    if reached:
        anchor_set = set(anchor_nodes)
        seen = {node}
        frontier = [node]
        for depth in range(1, max_hops + 1):
            nxt = []
            found = False
            for cur in frontier:
                for nb in sub.neighbours(cur, _EDGE):
                    if nb in anchor_set:
                        hops = depth
                        found = True
                        break
                    if nb not in seen:
                        seen.add(nb)
                        nxt.append(nb)
                if found:
                    break
            if found:
                break
            frontier = nxt
            if not frontier:
                break

    return {"reached": reached, "anchors": sorted(set(anchor_kinds)), "hops": hops}


# ---------------------------------------------------------------------------
# THE FLAG — the residual/confidence/groundedness discriminator. Flags only;
# a follow-on agent-authored guard RULE decides what to do with a
# GroundingGap (escalate / re-check / distrust) — not this module.
# ---------------------------------------------------------------------------
def flag_ungrounded_confident(
    agent, *,
    residual_attr: str = "residual",
    conf_attr: str = "confidence",
    residual_max: float = 0.05,
    conf_min: float = 0.9,
    node_types: Optional[list] = None,
) -> list:
    """Nodes with LOW residual (<= residual_max) AND HIGH confidence
    (>= conf_min) AND `grounding_reach(...).reached is False` -> mint a
    `GroundingGap{node, node_type, why, <residual_attr>, <conf_attr>,
    anchors}` (idempotent — one per `node`) and include it in the returned
    list. `node_types`, if given, restricts the scan to those node types
    (recommended on a large live graph); default None scans every node,
    skipping any that lacks BOTH attrs (never a false positive from a
    missing attr). Returns the flagged NodeIDs (old + newly-minted)."""
    sub, native = _resolve(agent)
    if node_types:
        candidates: list = []
        for t in node_types:
            candidates.extend(sub.nodes(t))
    else:
        candidates = sub.nodes(None)

    existing_gap_nodes = set()
    for g in sub.nodes(_GAP_TYPE):
        gn = sub.node(g)["attrs"].get("node")
        if gn is not None:
            existing_gap_nodes.add(gn)

    flagged: list = []
    for n in candidates:
        if not sub.has_node(n):
            continue
        at = sub.node(n)["attrs"]
        r_raw, c_raw = at.get(residual_attr), at.get(conf_attr)
        if r_raw is None or c_raw is None:
            continue
        try:
            r, c = float(r_raw), float(c_raw)
        except (TypeError, ValueError):
            continue
        if r > residual_max or c < conf_min:
            continue
        gr = grounding_reach(agent, n)
        if gr["reached"]:
            continue           # grounded -> saved, even though confident+low-residual
        if n in existing_gap_nodes:
            flagged.append(n)
            continue
        sub.add_node(_GAP_TYPE, {
            "node": n,
            "node_type": sub.node(n)["type"],
            "why": "confident but ungrounded",
            residual_attr: r,
            conf_attr: c,
            "anchors": gr["anchors"],
        })
        flagged.append(n)
    return flagged


__all__ = [
    "ANCHOR_KINDS",
    "ensure_grounding_edges",
    "grounding_reach",
    "flag_ungrounded_confident",
]
