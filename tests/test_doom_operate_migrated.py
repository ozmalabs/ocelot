"""Block 210000 — the ACT half: a recognised operable feature -> SET A MOVEMENT GOAL ->
pursue (orient/approach) -> USE ONCE on arrival. Synthetic (no VizDoom): drives the
graph rules directly through the mechanical adapter. Gates the state machine, the
single-USE (no-spam) property, default-OFF byte-identity, and integer discipline.
"""
import os, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.doom_pattern_eye as eye
import domains.doom_operate as op


def _boot():
    wa = eye.fresh_adapter()          # pattern_recognition
    op.load_operate_seed(wa)          # + doom_operate
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
    return wa, game


def _tick(wa, game, R, *, col, tex, near, fwd):
    op.update_sensors(wa, R, col=col, tex_level=tex, near=near, fwd_progress=fwd)
    return op.step(wa, game)


def test_sets_a_movement_goal_toward_the_recognised_region():
    """Recognising an operable feature SETS A MOVEMENT GOAL (MovementGoal moves_toward R)."""
    wa, game = _boot(); S, I = wa.s, wa.inner
    eye.install(wa, game, salience_floor=2)
    op.install(wa, game)
    R = op.make_target_region(wa, game)
    _tick(wa, game, R, col=220, tex=7, near=0, fwd=99)
    goals = list(I.neighbours(game, "has_movement_goal"))
    assert len(goals) == 1, "exactly one movement goal minted"
    G = goals[0]
    assert S.node(G)["attrs"]["kind"] == "approach_operate"
    assert R in list(I.neighbours(G, "moves_toward")), "the goal moves_toward the region"


def test_orient_then_approach_then_use_once_then_silent():
    """The full state machine, and the no-spam property: USE fires exactly ONCE."""
    wa, game = _boot()
    eye.install(wa, game, salience_floor=2)
    op.install(wa, game, center=160, face_tol=40, block_thresh=4)
    R = op.make_target_region(wa, game)
    # far to the right -> steer right
    assert _tick(wa, game, R, col=220, tex=7, near=0, fwd=99) == "turn_right"
    # far to the left -> steer left
    assert _tick(wa, game, R, col=90, tex=7, near=0, fwd=99) == "turn_left"
    # faced, still moving -> advance
    assert _tick(wa, game, R, col=162, tex=7, near=0, fwd=40) == "forward"
    # blocked (in range) + faced + recognised (latched via near) -> USE
    assert _tick(wa, game, R, col=160, tex=7, near=1, fwd=2) == "use"
    # thereafter: silent, no spam
    assert _tick(wa, game, R, col=160, tex=7, near=1, fwd=2) == "none"
    assert _tick(wa, game, R, col=160, tex=7, near=1, fwd=2) == "none"


def test_use_is_gated_on_recognition_faint_region_never_uses():
    """USE fires ONLY on a recognised feature: a faint (tex-2) region never resolves fine
    (switch/door prototypes are L1-distance >= match_thresh away), so USE never fires --
    modelling the sec83/sec85 texture-faint residual (a clean negative, not a mis-fire)."""
    wa, game = _boot()
    eye.install(wa, game, salience_floor=2)
    op.install(wa, game, center=160, face_tol=40, block_thresh=4)
    R = op.make_target_region(wa, game)
    cmds = [_tick(wa, game, R, col=160, tex=2, near=1, fwd=2) for _ in range(6)]
    assert "use" not in cmds, "a faint region is never USED"


def test_default_off_is_byte_identical():
    """Absent an OperateParams gate, NO operate rule fires: no movement goal, no motor,
    no mg_minted marker. The seed is self_load_only + gated, so every existing path is
    unchanged."""
    wa, game = _boot(); S, I = wa.s, wa.inner
    eye.install(wa, game, salience_floor=2)
    # NOTE: op.install is NOT called -> no OperateParams edge -> gate absent.
    R = op.make_target_region(wa, game)
    for _ in range(4):
        op.update_sensors(wa, R, col=160, tex_level=7, near=1, fwd_progress=2)
        I.run_rules(50000)
    assert not list(I.neighbours(game, "has_movement_goal")), "no movement goal without the gate"
    assert S.node(R)["attrs"].get("mg_minted") is None
    assert not S.node(R)["attrs"].get("motor_action")


def test_disabled_gate_is_inert():
    """An OperateParams with enabled != 1 fires nothing (the explicit ablation flag)."""
    wa, game = _boot(); S, I = wa.s, wa.inner
    eye.install(wa, game, salience_floor=2)
    p = S.add_node("OperateParams", {"enabled": 0.0, "center": 160, "face_tol": 40, "block_thresh": 4})
    I.add_edge_unchecked(game, "has_operate_params", p)
    R = op.make_target_region(wa, game)
    op.update_sensors(wa, R, col=160, tex_level=7, near=1, fwd_progress=2)
    I.run_rules(50000)
    assert not list(I.neighbours(game, "has_movement_goal"))


def test_params_are_integer_native():
    """Descriptors/tolerances/sensors are integers (in-frame is integer; CLAUDE.md)."""
    wa, game = _boot(); S, I = wa.s, wa.inner
    eye.install(wa, game, salience_floor=2)
    p = op.install(wa, game, center=160, face_tol=40, block_thresh=4)
    a = S.node(p)["attrs"]
    for k in ("center", "face_tol", "block_thresh"):
        assert a[k] == int(a[k])
    R = op.make_target_region(wa, game)
    op.update_sensors(wa, R, col=160, tex_level=7, near=1, fwd_progress=2)
    ra = S.node(R)["attrs"]
    for k in ("col", "tex_level", "geom_level", "fwd_progress"):
        assert ra[k] == int(ra[k])


def test_seed_uses_only_existing_terms_no_rust():
    """The operate seed is graph data over existing DSL Terms only (no Rust)."""
    import json
    seed = json.load(open(op.SEED_PATH))
    assert seed["self_load_only"] is True
    allowed = {"Var", "Lit", "Attr", "Eq", "Gt", "Gte", "Lt", "Lte",
               "And", "Or", "Not", "Abs", "Plus", "Minus", "IfThenElse"}
    def walk(t):
        if isinstance(t, dict):
            if "type" in t and isinstance(t["type"], str) and t["type"][0].isupper():
                assert t["type"] in allowed, f"unexpected Term {t['type']}"
            for v in t.values():
                walk(v)
        elif isinstance(t, list):
            for v in t:
                walk(v)
    for r in seed["rules"]:
        walk(r["where"]); walk(r["effects"])
