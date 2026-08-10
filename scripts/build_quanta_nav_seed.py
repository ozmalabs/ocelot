"""Authoring script for seeds/quanta_navigation.json — builds the qf_* rule set as
Term-JSON dicts (same style as scripts/build_navrules.py / move_space_planner.py's
V/A/L/... helpers) and writes the seed manifest. Run once (or whenever a rule needs to
change) to (re)generate the seed file; not runtime agent code (CLAUDE.md tools/* class:
a one-off authoring script that EMITS a seed manifest).

PYTHONPATH=runners/dsl/python:. python3 scripts/build_quanta_nav_seed.py

Cleanup-pass history (this file supersedes the original authoring pass +
patch_hop_route_gate.py's post-hoc surgical patch — both folded in here so the seed is
reproducible from ONE script):
  - qf_hop_route's crossing-dim `dir` is gated on being in-span on the non-crossing dims
    (2026-07-02 fix, folded into `_route_step` directly instead of a separate patch pass).
  - qf_hop_route's portal candidate pool is now FILTERED (oneway_ok==1 AND target
    qdist freshness) before Argmin, not just guarded at the rule level, so a stale/blocked
    portal can never win the pick even transiently.
  - qf_frontier_goal picks the nearest frontier via Argmin (deterministic first-encountered
    tiebreak) and matches F against that ONE winner, instead of "any F tied at the min
    qdist" (which fired the mint effect once per tied frontier — every frontier at qdist 0
    got committed as a goal simultaneously). Minted goals are tagged `exploration=1.0` +
    `commit_epoch` so qf_goal_retire can find and age them.
  - qf_stale_on_belief_change: a belief-correction observation (adapter mints
    `BeliefChange{pose,dim}` + `game -belief_changed-> BC`, mechanical ingest) marks its
    containing quantum stale, mirroring qf_stale_on_block_interior's shape exactly.
  - qf_goal_retire: retires an exploration-minted committed_goal when (a) the avatar
    reached its exact pose, (b) its pose is no longer covered by any frontier quantum
    (resolved by observation or decode), or (c) a fresher exploration goal superseded it
    (defence in depth now that the mint side is deduped by Argmin). Only ever touches
    `exploration==1` goals — world-committed goals (adapter/tests stamp `world=1.0`) are
    never retired by this rule.
"""
import json, os

ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate"
OUT = os.path.join(ROOT, "seeds", "quanta_navigation.json")

DIMS = 3  # MAX_DIMS unrolled per-dim (matches Part A's 2D+3D cargo-test scope;
          # IndexAt out-of-range -> None, and None-vs-None compares True / None-vs-number
          # compares False (verified), so containment over ndim<DIMS or ndim>DIMS degrades
          # safely without an explicit ndim guard).

# ---- Term-JSON builders (authoring-time only; mirrors move_space_planner.py) ---------
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(node, k):
    node_t = V(node) if isinstance(node, str) else node
    return {"type": "Attr", "node": node_t, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Or(*x): return {"type": "Or", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Neighbours(node, et): return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}
def InNeighbours(node, et): return {"type": "InNeighbours", "node": node, "edge_type": et, "any_type": False}
def Edges(node, et): return {"type": "Edges", "node": node, "edge_type": et, "any_type": False}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def MinOver(src, var, val, default=None): return {"type": "MinOver", "source": src, "var_name": var, "value": val, "default": default}
def Argmin(src, var, val, default=None): return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": default}
def Argmax(src, var, val, default=None): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": default}
def Nth(items, i): return {"type": "Nth", "items": items, "index": i}
def IdxAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": L(i)}
def IdxAtT(seq, i_term): return {"type": "IndexAt", "seq": seq, "index": i_term}
def Vec(*items): return {"type": "Vec", "items": list(items)}
def Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def EdgeAttr(edge, key): return {"type": "EdgeAttr", "edge": edge, "key": key}
def Let(name, value, body): return {"type": "Let", "name": name, "value": value, "body": body}

GAME = V("game")

def nav_repr_quanta():
    return Eq(A("game", "nav_repr"), L("quanta"))

def not_pocket_escape():
    return Not(Eq(A("game", "nav_mode"), L("pocket_escape")))

def is_world_goal(gvar):
    return Eq(A(gvar, "world"), L(1.0))

def contains(qvar, pose_term):
    """Box-containment: pose_term (a list-valued Term) inside qvar's lo/hi (list attrs),
    unrolled over DIMS dims. Safe for ndim < DIMS or ndim > DIMS (verified: IndexAt past
    either list's real length returns None; None-vs-None compares True, None-vs-number
    compares False) -- no ndim guard needed."""
    def dim_ok(d):
        p = IdxAt(pose_term, d)
        return And(Gte(p, IdxAt(A(qvar, "lo"), d)), Lte(p, IdxAt(A(qvar, "hi"), d)))
    return And(*[dim_ok(d) for d in range(DIMS)])

def pose_eq(a_term, b_term):
    """Per-dim pose equality, unrolled over DIMS (same None-vs-None-safe idiom as contains())."""
    return And(*[Eq(IdxAt(a_term, d), IdxAt(b_term, d)) for d in range(DIMS)])

def eff_qdist(nodevar_or_term):
    """qdist is only valid for the CURRENT flood_epoch (reused per-tick counter, same
    idiom as hop_descend_gradient's n._epoch==game.flood_epoch gate) -- otherwise treat
    as unset (-1). Avoids stale qdist leaking across a goal/tick change without any
    Python-side reset loop."""
    node_t = V(nodevar_or_term) if isinstance(nodevar_or_term, str) else nodevar_or_term
    return IfThenElse(Eq(A(node_t, "qdist_epoch"), A("game", "flood_epoch")),
                       A(node_t, "qdist"), L(-1.0))

def sign(x):
    return IfThenElse(Gt(x, L(0.0)), L(1.0), IfThenElse(Lt(x, L(0.0)), L(-1.0), L(0.0)))

def clamp(x, lo, hi):
    return IfThenElse(Lt(x, lo), lo, IfThenElse(Gt(x, hi), hi, x))

def set_attr(var, key, term_or_lit, computed=True):
    val = {"__term__": term_or_lit} if computed else term_or_lit
    return ["set_attr", var, key, val]

def set_attr_if_diff(var, key, term_or_lit, computed=True):
    val = {"__term__": term_or_lit} if computed else term_or_lit
    return ["set_attr_if_different", var, key, val]

RULES = []

# ============================================================================
# qf_seed: goal quantum (or, when exploring with no goal, every frontier quantum)
# gets qdist=0. Split into two rules -- the goal-branch needs an extra bound var (G)
# the frontier-branch doesn't, so one match-edge shape can't express both branches.
# ============================================================================
RULES.append({
    "name": "qf_seed_goal",
    "comment": ("a WORLD-committed goal's containing quantum -> qdist=0 (single-source flood "
                "root). Restricted to `world==1` goals ONLY (not exploration-minted ones): an "
                "exploration goal's own quantum is ALREADY a flood source via qf_seed_frontier "
                "(it's one of the frontiers) -- seeding it AGAIN here would be redundant while "
                "fresh and actively HARMFUL once stale (a churned exploration-goal pose that no "
                "longer sits in a frontier would otherwise plant a bogus single-source root at an "
                "arbitrary already-explored cell, competing with the real multi-source frontier "
                "flood qf_hop_route/qf_frontier_goal depend on)."),
    "match": [["Q", "in_space", "game"], ["game", "committed_goal", "G"]],
    "where": And(nav_repr_quanta(), is_world_goal("G"), contains("Q", A("G", "pose"))),
    "effects": [
        set_attr_if_diff("Q", "qdist", 0.0, computed=False),
        set_attr_if_diff("Q", "qdist_epoch", A("game", "flood_epoch")),
    ],
})
RULES.append({
    "name": "qf_seed_frontier",
    "comment": ("no WORLD-committed goal (pure exploration) -> every frontier quantum is a flood "
                "source (multi-source qdist=0); qf_frontier_goal separately commits ONE of them as "
                "a bookkeeping Goal{pose} (for qf_hop_direct's exact-arrival step + other "
                "consumers), but that exploration goal does NOT gate this rule off (guard is "
                "world==1 specifically, not 'any committed_goal') -- the multi-source flood stays "
                "live across every known frontier the whole time exploration is active, so hop can "
                "still route toward WHICHEVER frontier is nearer via the CURRENTLY known portal "
                "graph even if the nominally-committed one turns out to be unreached / disconnected "
                "so far. This is what makes aggressive goal retiring unnecessary for correctness "
                "(qf_goal_retire is now a lifecycle/bookkeeping cleanup, not a routing necessity)."),
    "match": [["Q", "in_space", "game"]],
    "where": And(nav_repr_quanta(),
                 Eq(A("Q", "kind"), L("frontier")),
                 Not(Exists(Neighbours(GAME, "committed_goal"), "_g", is_world_goal("_g")))),
    "effects": [
        set_attr_if_diff("Q", "qdist", 0.0, computed=False),
        set_attr_if_diff("Q", "qdist_epoch", A("game", "flood_epoch")),
    ],
})

# ============================================================================
# qf_relax: Bellman relaxation. Q.qdist = min(Q.qdist, R.qdist + cost) over each portal
# Q -> R with oneway_ok=1 (Q can legally cross INTO R). Writing to the match SOURCE (Q)
# using the TARGET (R) is the direction consistent with qf_hop's own consumer semantics
# ("Argmin over Q's portals by neighbour.qdist + cost") -- see report deviation note.
# ============================================================================
_qr_handle = Vec(V("Q"), L("portal"), V("R"))
RULES.append({
    "name": "qf_relax",
    "comment": "Bellman relax: Q.qdist <- min(Q.qdist, R.qdist+cost) over portal Q->R with oneway_ok. Batched -- bindings snapshotted before mutation, converges via set_attr_if_different's own progress flag.",
    "match": [["Q", "portal", "R"], ["Q", "in_space", "game"]],
    "where": And(
        nav_repr_quanta(),
        Eq(EdgeAttr(_qr_handle, "oneway_ok"), L(1.0)),
        Gte(eff_qdist("R"), L(0.0)),
        Or(Lt(eff_qdist("Q"), L(0.0)),
           Gt(eff_qdist("Q"), Plus(eff_qdist("R"), EdgeAttr(_qr_handle, "cost")))),
    ),
    "effects": [
        set_attr_if_diff("Q", "qdist", Plus(eff_qdist("R"), EdgeAttr(_qr_handle, "cost"))),
        set_attr_if_diff("Q", "qdist_epoch", A("game", "flood_epoch")),
    ],
    "batch": True,
})

# ============================================================================
# qf_visit: mark Q.visited=1 when the avatar's pose is inside Q.
# ============================================================================
RULES.append({
    "name": "qf_visit",
    "match": [["Q", "in_space", "game"]],
    "where": And(nav_repr_quanta(), contains("Q", A("game", "avatar_pose"))),
    "effects": [set_attr_if_diff("Q", "visited", 1.0, computed=False)],
})

# ============================================================================
# qf_hop_direct / qf_hop_route: the ONE consumer writing game.chosen_action.
# Action vocabulary reused via the EXISTING is_self-region -responds_via-> ControlResponse
# chain (affordance_basis.json's mint_control_response/learn_control_delta) -- NOT a new
# vocabulary; see report for the assumption this is live for quanta-mode games too.
# ============================================================================
def _pick_action(desired_vec):
    cr = "cr"
    ctrl_disp = Vec(A(cr, "dr"), A(cr, "dc"), A(cr, "dz"))
    return Argmax(Neighbours(V("sr"), "responds_via"), cr, Dot(ctrl_disp, desired_vec), default=V("sr"))

_goal_pose = A("G", "pose")
_avatar_pose = A("game", "avatar_pose")
_direct_steps = [sign(Minus(IdxAt(_goal_pose, d), IdxAt(_avatar_pose, d))) for d in range(DIMS)]
RULES.append({
    "name": "qf_hop_direct",
    "comment": "goal is inside the avatar's own quantum -> per-dim sign step straight to it (a passable box admits any interior motion by construction, no per-cell flood needed).",
    "match": [["Q", "in_space", "game"], ["game", "committed_goal", "G"], ["game", "has_region", "sr"]],
    "where": And(
        nav_repr_quanta(), not_pocket_escape(),
        Gt(A("sr", "is_self"), L(0.5)),
        contains("Q", _avatar_pose),
        contains("Q", _goal_pose),
    ),
    "effects": [set_attr("game", "chosen_action", A(_pick_action(Vec(*_direct_steps)), "cname"))],
})

_winner = V("winner")
_win_dim = EdgeAttr(_winner, "dim")
_win_dir = EdgeAttr(_winner, "dir")
_win_span_lo = EdgeAttr(_winner, "span_lo")
_win_span_hi = EdgeAttr(_winner, "span_hi")
def _in_span_except(skip_d):
    """AND over every OTHER dim k!=skip_d of span_lo[k] <= avatar_pose[k] <= span_hi[k]."""
    def ok(k):
        return And(Gte(IdxAt(_avatar_pose, k), IdxAt(_win_span_lo, k)),
                   Lte(IdxAt(_avatar_pose, k), IdxAt(_win_span_hi, k)))
    return And(*[ok(k) for k in range(DIMS) if k != skip_d])

def _route_step(d):
    """Per-dim desired step for the winning portal: on the CROSSING dim, only emit the
    portal's `dir` once the avatar sits INSIDE the shared span on every OTHER dim (the
    design's 'clamped inside span for non-crossing dims, THEN cross along dim/dir');
    otherwise 0 so the Dot pick doesn't tie the crossing move against the clamp move and
    press into a known wall forever (2026-07-02 fix, folded in here). On non-crossing
    dims, clamp-then-sign toward the shared span."""
    non_cross = sign(Minus(clamp(IdxAt(_avatar_pose, d), IdxAt(_win_span_lo, d), IdxAt(_win_span_hi, d)),
                            IdxAt(_avatar_pose, d)))
    crossing_dir = IfThenElse(_in_span_except(d), _win_dir, L(0.0))
    return IfThenElse(Eq(L(float(d)), _win_dim), crossing_dir, non_cross)

_portal_edges = Edges(V("Q"), "portal")
_portal_ok = lambda h: And(Eq(EdgeAttr(h, "oneway_ok"), L(1.0)), Gte(eff_qdist(Nth(h, 2)), L(0.0)))
# candidate pool for the Argmin pick itself is FILTERED (not just guarded at the rule
# level) so a blocked (oneway_ok==0) or stale-qdist (this epoch never relaxed it) portal
# can never WIN the pick even transiently -- the rule guard below only ensures at least
# one such candidate exists before firing at all.
_valid_portal_edges = Filter(_portal_edges, "h", _portal_ok(V("h")))
_argmin_val = Plus(eff_qdist(Nth(V("h"), 2)), EdgeAttr(V("h"), "cost"))
_argmin_portal = Argmin(_valid_portal_edges, "h", _argmin_val, default=None)
_route_desired = Let("winner", _argmin_portal, Vec(*[_route_step(d) for d in range(DIMS)]))
RULES.append({
    "name": "qf_hop_route",
    "comment": ("goal not in the avatar's own quantum (or exploring) -> pick the portal minimising "
                "(neighbour qdist + cost) from the FILTERED candidate pool (oneway_ok==1 AND target "
                "qdist fresh this epoch -- filtered into the Argmin pool itself, not just guarded), "
                "then step: crossing dim follows the portal's dir (gated in-span on the other dims), "
                "other dims clamp toward the shared span."),
    "match": [["Q", "in_space", "game"], ["game", "has_region", "sr"]],
    "where": And(
        nav_repr_quanta(), not_pocket_escape(),
        Gt(A("sr", "is_self"), L(0.5)),
        contains("Q", _avatar_pose),
        Not(Exists(Neighbours(GAME, "committed_goal"), "G2", contains("Q", A("G2", "pose")))),
        Exists(_portal_edges, "h", _portal_ok(V("h"))),
    ),
    "effects": [set_attr("game", "chosen_action", A(_pick_action(_route_desired), "cname"))],
})

# ============================================================================
# qf_frontier_goal: no committed_goal and frontiers exist -> commit the NEAREST one, via
# Argmin with its deterministic first-encountered tiebreak. Matching F against that ONE
# winner (rather than "any F tied at the min qdist") is what keeps this a single-mint
# rule: the old MinOver+Eq shape fired its effect once PER TIED FRONTIER (every frontier
# at qdist==0 satisfied qdist==min simultaneously and each independently committed a
# Goal). Mints a uniform Goal{pose} node (pose = the frontier's lo corner) tagged
# `exploration=1` + `commit_epoch` so qf_goal_retire can find and age it -- so
# qf_seed_goal's single-goal-pose containment test applies uniformly on the NEXT flood
# cycle, rather than introducing a second "committed_goal is sometimes a SpaceQuantum"
# shape.
# ============================================================================
_frontier_pool = Filter(InNeighbours(GAME, "in_space"), "C",
                         And(Eq(A("C", "kind"), L("frontier")), Gte(eff_qdist("C"), L(0.0))))
_frontier_winner = Argmin(_frontier_pool, "C", eff_qdist("C"), default=None)
RULES.append({
    "name": "qf_frontier_goal",
    "comment": ("commits the SINGLE nearest frontier (Argmin, deterministic first-encountered "
                "tiebreak) by matching F against that one winner -- NOT 'any frontier tied at the "
                "min qdist', which used to commit every tied frontier as its own Goal in the same "
                "pass."),
    "match": [["F", "in_space", "game"]],
    "where": And(
        nav_repr_quanta(),
        Not(Exists(Neighbours(GAME, "committed_goal"), "_g", L(True))),
        Eq(A("F", "kind"), L("frontier")),
        Gte(eff_qdist("F"), L(0.0)),
        Eq(V("F"), _frontier_winner),
    ),
    "effects": [
        ["add_node", "G2", "Goal", {"pose": {"__term__": A("F", "lo")}, "committed": 1.0,
                                     "exploration": 1.0,
                                     "commit_epoch": {"__term__": A("game", "flood_epoch")}}],
        ["add_edge", "game", "committed_goal", "G2", {}],
    ],
})

# ============================================================================
# qf_goal_retire: the ONLY rule that removes a committed_goal, and only an
# EXPLORATION-minted one (world-committed goals -- adapter/test-stamped `world=1.0` --
# are never touched). Replaces the adapter's old _wipe_transient_goals (which wiped
# EVERY exploration goal EVERY tick so qf_frontier_goal could re-derive one against the
# current frontier field -- i.e. no real commitment, re-pick nearest every tick). Retire
# when:
#  (a) REACHED: the avatar's pose exactly equals the goal's pose (qf_hop_direct/_route
#      have walked it there -- a same-quantum-but-not-yet-arrived avatar must NOT retire
#      the goal, or the hop rules lose the target mid-approach).
#  (b) STALE: the goal's pose is no longer covered by ANY frontier quantum (observation
#      resolved it -- it decoded into passable or wall on the next requantize).
#  (c) SUPERSEDED: a fresher exploration goal exists for the same game (defence in
#      depth -- structurally rare now that qf_frontier_goal's mint side is Argmin-deduped,
#      but a cheap invariant to keep: only ever the newest exploration goal survives).
# ============================================================================
_reached = pose_eq(A("G", "pose"), _avatar_pose)
_no_longer_frontier = Not(Exists(InNeighbours(GAME, "in_space"), "Q2",
                                  And(Eq(A("Q2", "kind"), L("frontier")), contains("Q2", A("G", "pose")))))
_superseded = Exists(Neighbours(GAME, "committed_goal"), "G2",
                      And(Not(Eq(V("G2"), V("G"))),
                          Eq(A("G2", "exploration"), L(1.0)),
                          Gt(A("G2", "commit_epoch"), A("G", "commit_epoch"))))
RULES.append({
    "name": "qf_goal_retire",
    "comment": ("retires an exploration-minted committed_goal when reached (avatar pose == goal "
                "pose exactly), its pose is no longer covered by any frontier quantum (resolved by "
                "observation/decode), or a fresher exploration goal superseded it. World-committed "
                "goals (`world==1`) are never touched -- only ever `exploration==1` goals."),
    "match": [["game", "committed_goal", "G"]],
    "where": And(
        nav_repr_quanta(),
        Eq(A("G", "exploration"), L(1.0)),
        Or(_reached, _no_longer_frontier, _superseded),
    ),
    "effects": [["del_node", "G"]],
})

# ============================================================================
# qf_stale_on_belief_change: mirrors qf_stale_on_block_interior's shape exactly, but the
# trigger is a belief CORRECTION (a cell's observed value changed under an existing
# quantum -- e.g. a bumped wall) rather than a refused crossing. The adapter's job is
# pure ingest: mint `BeliefChange{pose, dim}` + `game -belief_changed-> BC` (mechanical;
# see domains/spatial_sense.mark_belief_change). This rule does the containment lookup
# and marks the quantum stale for a per-dim resplit -- the adapter no longer scans
# quanta itself. `stale_dim` is whatever dim the caller observed the change along (0 for
# a value-corrected single cell is fine: the primitive's resplit only needs ONE failing
# dim to re-decode the finer band; the residual-split test (test 5,
# test_interior_block_splits_only_the_blocked_dim_and_reroutes) already proves the
# primitive-side split-on-stale_dim contract this rule feeds into -- same attrs, same
# shape, different upstream trigger). The BeliefChange node is cleaned up by the adapter
# after the requantize consumes it (mirrors the existing BlockObs cleanup in
# quanta_flood_step), not by this rule -- deleting a node the rule itself matched risks
# ordering hazards across other bindings of the same BC in one fixpoint pass.
# ============================================================================
RULES.append({
    "name": "qf_stale_on_belief_change",
    "comment": ("a belief-correction observation (game -belief_changed-> BC{pose,dim}, mechanical "
                "adapter stamp) inside a quantum's box -> mark it stale for a per-dim resplit. Same "
                "stale/stale_dim/stale_pose contract as qf_stale_on_block_interior; the adapter no "
                "longer scans quanta for containment itself."),
    "match": [["game", "belief_changed", "BC"], ["Q", "in_space", "game"]],
    "where": And(nav_repr_quanta(), contains("Q", A("BC", "pose"))),
    "effects": [
        set_attr_if_diff("Q", "stale", 1.0, computed=False),
        set_attr_if_diff("Q", "stale_dim", A("BC", "dim")),
        set_attr_if_diff("Q", "stale_pose", A("BC", "pose")),
    ],
})

# ============================================================================
# qf_stale_on_block: an observed blocked crossing (game -blocked-> B{pose,dim,dir,epoch})
# -> interior to a quantum (strictly, along B.dim) marks it stale; ON a portal's face
# flips that specific portal's oneway_ok=0 (preserving its other attrs -- add_edge
# replaces the whole attrs dict, there is no single-attr edge-write effect; see report).
# ============================================================================
def _interior_along_blocked_dim(qvar, bvar):
    pose_at_dim = IdxAtT(A(bvar, "pose"), A(bvar, "dim"))
    lo_at_dim = IdxAtT(A(qvar, "lo"), A(bvar, "dim"))
    hi_at_dim = IdxAtT(A(qvar, "hi"), A(bvar, "dim"))
    return And(Gt(pose_at_dim, lo_at_dim), Lt(pose_at_dim, hi_at_dim))

RULES.append({
    "name": "qf_stale_on_block_interior",
    "comment": "block observation strictly inside a quantum's box (not on a face along the blocked dim) -> a mover/obstacle appeared mid-box; mark stale for a per-dim resplit.",
    "match": [["game", "blocked", "B"], ["Q", "in_space", "game"]],
    "where": And(nav_repr_quanta(), contains("Q", A("B", "pose")),
                 _interior_along_blocked_dim("Q", "B")),
    "effects": [
        set_attr_if_diff("Q", "stale", 1.0, computed=False),
        set_attr_if_diff("Q", "stale_dim", A("B", "dim")),
        set_attr_if_diff("Q", "stale_pose", A("B", "pose")),
    ],
})

_qr_handle2 = Vec(V("Q"), L("portal"), V("R"))
RULES.append({
    "name": "qf_stale_on_block_portal",
    "comment": "block observation on a quantum's face, matching an existing portal's crossing dim/dir -> flip that portal's oneway_ok (no split needed).",
    "match": [["game", "blocked", "B"], ["Q", "in_space", "game"], ["Q", "portal", "R"]],
    "where": And(
        nav_repr_quanta(), contains("Q", A("B", "pose")),
        Not(_interior_along_blocked_dim("Q", "B")),
        Eq(EdgeAttr(_qr_handle2, "dim"), A("B", "dim")),
        Eq(EdgeAttr(_qr_handle2, "dir"), A("B", "dir")),
        Eq(EdgeAttr(_qr_handle2, "oneway_ok"), L(1.0)),
    ),
    "effects": [
        ["add_edge", "Q", "portal", "R", {
            "dim": {"__term__": EdgeAttr(_qr_handle2, "dim")},
            "dir": {"__term__": EdgeAttr(_qr_handle2, "dir")},
            "span_lo": {"__term__": EdgeAttr(_qr_handle2, "span_lo")},
            "span_hi": {"__term__": EdgeAttr(_qr_handle2, "span_hi")},
            "cost": {"__term__": EdgeAttr(_qr_handle2, "cost")},
            "oneway_ok": 0.0,
        }],
    ],
})

# ============================================================================
# qf_requantize_flag: any stale quantum -> game.needs_quantize=1 (the adapter's
# epoch-gated cue to call space_quantize; the adapter only reads the flag).
# NOTE: the "uncovered-in-focus observation" trigger from the design is deferred --
# detecting coverage gaps duplicates the primitive's own incremental-decode bookkeeping
# (Part A step 3 already re-decodes newly-observed focus area each call); see report.
# ============================================================================
RULES.append({
    "name": "qf_requantize_flag",
    "match": [["Q", "in_space", "game"]],
    "where": And(nav_repr_quanta(), Eq(A("Q", "stale"), L(1.0))),
    "effects": [set_attr_if_diff("game", "needs_quantize", 1.0, computed=False)],
})

# ============================================================================
# qf_closed / qf_mint_hyp: no reachable frontier/goal route -> closed=1 -> mint the
# non-movement-affordance Hypothesis. Ports msp_closed/msp_mint_hyp to quantum grain.
# ============================================================================
RULES.append({
    "name": "qf_closed",
    "comment": "avatar's own quantum never got a qdist this epoch, though something was seeded (goal committed or a frontier exists) -> movement exhausted.",
    "match": [["Q", "in_space", "game"]],
    "where": And(
        nav_repr_quanta(),
        Eq(A("game", "closed"), L(0.0)),
        contains("Q", _avatar_pose),
        Lt(eff_qdist("Q"), L(0.0)),
        Or(Exists(Neighbours(GAME, "committed_goal"), "_g", L(True)),
           Exists(InNeighbours(GAME, "in_space"), "F2", Eq(A("F2", "kind"), L("frontier")))),
    ),
    "effects": [set_attr_if_diff("game", "closed", 1.0, computed=False)],
})
RULES.append({
    "name": "qf_mint_hyp",
    "comment": "add_node_if_absent (not add_node) so a same-pass double-binding of Q (irrelevant to the effect, just along for the match) can't mint two Hypotheses -- the dedup key IS the kind, matching msp_mint_hyp's single-hypothesis intent exactly.",
    "match": [["Q", "in_space", "game"]],
    "where": And(Eq(A("game", "closed"), L(1.0)),
                 Not(Exists(Neighbours(GAME, "minted"), "h", L(True)))),
    "effects": [
        ["add_node_if_absent", "hyp", "Hypothesis", {"kind": "need_non_movement_affordance"}],
        ["add_edge", "game", "minted", "hyp"],
    ],
})

MANIFEST = {
    "id": "quanta_navigation",
    "version": "1.0.0",
    "depends_on": ["navigation_modes", "affordance_basis"],
    "description": (
        "Graph-native quantum-grain flood/route/explore/refine over SpaceQuantum belief "
        "(dynamic, foveated, N-dimensional quanta navigation -- CLAUDE.md's Rust-is-the-agent "
        "split: this seed is graph DATA only, no Python decisions). qf_seed_goal/qf_seed_frontier "
        "seed the Bellman flood root(s) (single committed goal, or multi-source over every "
        "frontier quantum while exploring); qf_relax propagates qdist=distance-to-goal backward "
        "over portal edges gated by oneway_ok; qf_visit marks the avatar's containing quantum "
        "visited; qf_hop_direct/qf_hop_route are the ONE decision writing game.chosen_action "
        "(per-dim sign step when the goal shares the avatar's box, else Argmin-portal descent over "
        "a pool FILTERED by oneway_ok+freshness, clamped to the crossing span), mapping the "
        "desired displacement to the world's action vocabulary via the EXISTING is_self-region "
        "responds_via/ControlResponse Dot-pick (no hardcoded Up/Down/Left/Right, N-dim by "
        "construction); qf_frontier_goal commits the nearest frontier (Argmin, deterministic "
        "tiebreak -- exactly one mint per cycle, not one per tied frontier) as a uniform "
        "Goal{pose,exploration,commit_epoch} node; qf_goal_retire is the ONLY rule that removes a "
        "committed_goal, and only an exploration-minted one (reached / no-longer-frontier / "
        "superseded by a fresher one) -- world-committed goals are never touched; "
        "qf_stale_on_belief_change/_block_interior/_block_portal turn an observed belief "
        "correction or blocked crossing into either a per-dim stale mark (resplit) or a flipped "
        "portal oneway_ok; qf_requantize_flag is the adapter's epoch-gated cue to re-run "
        "space_quantize; qf_closed/qf_mint_hyp port msp_closed/msp_mint_hyp to quantum grain "
        "(movement exhausted -> a non-movement-affordance Hypothesis). All qf_* rules guard on "
        "game.nav_repr==\"quanta\"; hop_descend_gradient (cell mode, seeds/grid_navigation.json) "
        "is untouched and starves naturally in quanta mode since _dist is never written there."
    ),
    "microtheory": {
        "name": "quanta_navigation",
        "description": "quantum-grain flood/route/explore/refine over SpaceQuantum belief, body-conditional and foveated",
    },
    "nodes": [],
    "edges": [],
    "productions": [],
    "concepts": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
