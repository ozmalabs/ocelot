"""spatial_sense — the agent's GENERIC spatial sense, as a REFLEX master_tick fires (NOT host code).

Architecture rule (CLAUDE.md): the world adapter is the ONLY world-specific thing — it turns frames into graph
(vision) and reads an action back out. After the adapter, master_tick does EVERYTHING. This module is the
spatial half of "everything": the mechanical perception that, each tick, MEASURES the avatar body, fires the
rigid-body slide_flood (the spatial sense, like the eye firing cv2), and lets the graph NAV RULES decide — then
the mechanical fallbacks (pocket_escape sweep / unstick / bootstrap) the rules leave to perception. It is NOT
arc-specific: it works for any grid world that perceive_frame fills (ls20, the maze, …). The nav DECISIONS all
live in seeds/grid_navigation.json; this only ENACTS the perception cadence the rules need.

Install once (`install(agent)`); thereafter `agent.master_tick()` fires it every tick. The host loop shrinks to
    perceive_frame(frame) -> master_tick() -> read chosen_action -> world.apply(action)
with nothing world-specific after the adapter.
"""
from __future__ import annotations

DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1), "Select": (0, 0)}
BOOTSTRAP = ["Up", "Right", "Down", "Left"]
BLOCK_TTL = 8


def _h():
    """The generic spatial helpers (still defined in scripts/arc_run for now; lazily imported to avoid a
    domain->script import at module load). TODO: relocate them here so nothing spatial lives under scripts/."""
    import scripts.arc_run as ar
    return ar


# ======================================================================================================
#  QUANTA MODE (FLOOD_DESIGN Part C) — the world adapter's side of dynamic, foveated, N-dim quanta
#  navigation. Selected by `nav_repr == "quanta"` DATA on the game node (the runner stamps it; the
#  default is unset = legacy cell mode, zero behaviour change). Everything here is mechanical
#  adapt+tick: stamp observations (avatar_pose / focus / scale / BlockObs), fire the Rust
#  `space_quantize` primitive when the graph asks (needs_quantize) or the belief epoch moved, and
#  run_rules(). Every nav DECISION — flood seeding, Bellman relax, hop, frontier commitment,
#  stale-vs-portal-flip, closed — is a qf_* rule in seeds/quanta_navigation.json.
# ======================================================================================================

def _qstate(agent) -> dict:
    """The adapter-side quanta bookkeeping (belief-epoch counter + last-quantized epoch + a monotone
    flood tick). Host I/O state, like `_spatial` — the substrate stays the source of truth for the map."""
    st = getattr(agent, "_spatial", None)
    if st is None:
        st = agent._spatial = {}
    return st.setdefault("quanta", {"belief_epoch": 1, "quantized": None, "tick": 0})


def bump_belief_epoch(agent) -> int:
    """Mechanical: the adapter just changed the observation belief (ingested a frame / recorded a
    learned wall) — advance the belief epoch so the next quanta_flood_step re-decodes."""
    qs = _qstate(agent)
    qs["belief_epoch"] += 1
    return qs["belief_epoch"]


def record_block_obs(agent, game, pose_rc, disp, epoch):
    """Mechanical observation stamp (quanta mode's replacement for the `_blk_*` cell attrs): a
    flood-approved press yielded no motion -> BlockObs {pose, dim, dir, epoch} + game -blocked-> B.
    The DECISION (interior split vs portal oneway flip) is qf_stale_on_block_* rules'; this only
    records what happened. Convention (the one the seed rules read — the `_blk_*` convention too):
    `pose` is the SOURCE cell (where the avatar pressed FROM), `dim`/`dir` the refused crossing.
    Source-side pose is what lets qf_stale_on_block_portal flip the CORRECT portal (the one
    leaving the avatar's quantum) and qf_stale_on_block_interior see a mid-box press as interior."""
    S, I = agent.s, agent.inner
    sdr = (1 if disp[0] > 0 else -1 if disp[0] < 0 else 0)
    sdc = (1 if disp[1] > 0 else -1 if disp[1] < 0 else 0)
    if sdr == 0 and sdc == 0:
        return None
    dim = 0 if sdr != 0 else 1
    b = S.add_node("BlockObs", {"pose": [int(pose_rc[0]), int(pose_rc[1])],
                                "dim": float(dim), "dir": float(sdr if dim == 0 else sdc),
                                "epoch": float(epoch)})
    I.add_edge_unchecked(game, "blocked", b)
    return b


def mark_belief_change(agent, game, pose, dim):
    """Mechanical ingest (FLOOD_DESIGN Layer B, residual (a): 'a belief change (cell value
    changed under a quantum) marks the containing quantum stale=1 with stale_dim/stale_pose').
    The adapter's job shrinks to minting the observation as DATA — `BeliefChange{pose, dim}` +
    `game -belief_changed-> BC` — no containment scan, no decision. The `qf_stale_on_belief_change`
    rule (seeds/quanta_navigation.json) does the containment lookup and marks the quantum stale;
    the adapter cleans up the consumed BeliefChange node after the next requantize (mirrors the
    existing BlockObs cleanup a few lines down in quanta_flood_step)."""
    S, I = agent.s, agent.inner
    bc = S.add_node("BeliefChange", {"pose": [int(pose[0]), int(pose[1])], "dim": float(dim)})
    I.add_edge_unchecked(game, "belief_changed", bc)
    return bc


def _stamp_goal_poses(agent, game):
    """Representation shim (mechanical attribute translation, no decision): committed goals minted
    by the cell-grain seeds are Cell nodes carrying row/col; the qf_* rules read a Goal-style
    `pose` list. Mirror row/col -> pose so both representations name the same fact."""
    S, I = agent.s, agent.inner
    for g in I.neighbours(game, "committed_goal"):
        a = S.node(g)["attrs"]
        if a.get("pose") is None and a.get("row") is not None and a.get("col") is not None:
            I.set_attr(g, "pose", [int(a["row"]), int(a["col"])])


def quanta_flood_step(agent, game, pose_rc, body_hw, passable_values, slide, grid_hw,
                      pending_block=False, focus=None) -> None:
    """ONE quanta-mode flood pass (the quanta twin of the slide_flood block): stamp avatar_pose /
    per-dim scale / focus (mechanically around avatar + committed goals unless the world supplies
    its own bounds), fire the epoch-gated `space_quantize` primitive when the graph asks
    (needs_quantize) or the belief epoch moved, then TWO-PHASE tick: run_rules (the qf flood runs
    to fixpoint), closed=0, run_rules (qf_closed reads the CONVERGED qdist field). This two-phase
    split is FIXPOINT SCHEDULING, not a decision, and stays in the adapter (the same
    CLOSED-before-FLOOD precedent as move_space_planner/msp_closed): `closed` is a sentinel the
    adapter arms in a second pass so qf_closed only ever reads a CONVERGED qdist field, never a
    mid-fixpoint one — the rule itself decides nothing about WHEN to look, only WHAT it sees.
    Every actual decision (goal retirement, staleness, hop, frontier commitment) is a qf_* rule;
    this function only stamps observations, calls the primitive, and ticks."""
    S, I = agent.s, agent.inner
    qs = _qstate(agent)
    qs["tick"] += 1
    I.set_attr(game, "avatar_pose", [int(pose_rc[0]), int(pose_rc[1])])
    I.set_attr(game, "scale", [float(slide), float(slide)])   # per-dim scale DATA (learned slide)
    I.set_attr(game, "closed", -1.0)   # sentinel: flood in progress — qf_closed reads only the
    _stamp_goal_poses(agent, game)     # converged field (phase 2 below stamps 0 to arm it)
    if pending_block:
        I.add_node("NativeSpatialSenseReceipt", {
            "schema": "native_spatial_sense_receipt_v1",
            "cluster": "spatial_sense.quanta_flood",
            "provenance": "native_rule_readback:spatial_sense_flood",
            "native_rule": "spatial_sense_quanta_flood_rules",
            "native_steps": ["stamp_observations", "run_rules", "readback"],
            "phase": "pre_flood",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        I.run_rules()          # let qf_stale_on_block_* / qf_stale_on_belief_change /
                                # qf_requantize_flag / qf_goal_retire process this tick's
                                # observations (BlockObs / BeliefChange / reached-or-stale goals)
    if focus is None:
        # focus = bounding box of the avatar + every committed goal pose, +margin, clamped to grid.
        poses = [[int(pose_rc[0]), int(pose_rc[1])]]
        for g in I.neighbours(game, "committed_goal"):
            p = S.node(g)["attrs"].get("pose")
            if p is not None:
                poses.append([int(p[0]), int(p[1])])
        m = max(2, int(slide) + 1, int(body_hw[0]), int(body_hw[1]))
        H, W = int(grid_hw[0]), int(grid_hw[1])
        focus = ([max(0, min(p[0] for p in poses) - m), max(0, min(p[1] for p in poses) - m)],
                 [min(H - 1, max(p[0] for p in poses) + m), min(W - 1, max(p[1] for p in poses) + m)])
    lo, hi = [int(v) for v in focus[0]], [int(v) for v in focus[1]]
    I.set_attr(game, "focus_lo", lo)
    I.set_attr(game, "focus_hi", hi)
    if S.node(game)["attrs"].get("needs_quantize") == 1.0 or qs["quantized"] != qs["belief_epoch"]:
        gid = int(str(game).lstrip("#"))
        I.space_quantize(gid, 2, "%dx%d" % (int(body_hw[0]), int(body_hw[1])),
                         [int(v) for v in passable_values], lo, hi, int(qs["belief_epoch"]),
                         [int(body_hw[0]), int(body_hw[1])])
        I.set_attr(game, "needs_quantize", 0.0)
        for b in list(I.neighbours(game, "blocked")):     # consumed by this decode; clear the stamps
            I.remove_node(b)
        for bc in list(I.neighbours(game, "belief_changed")):   # consumed by this decode too
            I.remove_node(bc)
        qs["quantized"] = qs["belief_epoch"]
    I.set_attr(game, "flood_epoch", float(qs["tick"]))    # monotone; qdist freshness keys on it
    I.add_node("NativeSpatialSenseReceipt", {
        "schema": "native_spatial_sense_receipt_v1",
        "cluster": "spatial_sense.quanta_flood",
        "provenance": "native_rule_readback:spatial_sense_flood",
        "native_rule": "spatial_sense_quanta_flood_rules",
        "native_steps": ["space_quantize", "run_rules", "readback"],
        "phase": "flood",
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    I.run_rules()                                         # phase 1: qf flood to fixpoint (+ hop)
    I.set_attr(game, "closed", 0.0)
    I.add_node("NativeSpatialSenseReceipt", {
        "schema": "native_spatial_sense_receipt_v1",
        "cluster": "spatial_sense.quanta_flood",
        "provenance": "native_rule_readback:spatial_sense_flood",
        "native_rule": "spatial_sense_quanta_flood_rules",
        "native_steps": ["arm_closed", "run_rules", "readback"],
        "phase": "closed",
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    I.run_rules()                                         # phase 2: closed detection on converged field


def spatial_sense_step(agent) -> None:
    """ONE tick of the spatial sense: measure the avatar body, fire the floods, let the nav rules decide, and
    write the chosen action onto the game. Pure mechanical perception + the rules' own decisions — no host
    policy. State persists on agent._spatial across ticks (the world is dynamic)."""
    ar = _h()
    S, I = agent.s, agent.inner
    st = getattr(agent, "_spatial", None)
    if st is None:
        st = agent._spatial = {"frame": 0, "last_disp": (0, 0), "prev_grid": None, "last_slide": 1,
                               "prev_av_pos": None, "nav_stuck": 0, "prev_cell": None,
                               "blocked": {}, "near_mover": set(), "prev_reached": None}
    game = ar._game_node(agent)
    if game is None:
        return
    i = int(st["frame"]); last_disp = st["last_disp"]
    now_grid = getattr(agent, "_last_grid", None)
    old_grid = st.get("prev_grid")          # the grid BEFORE this move — what the avatar moved INTO
    # LEARN MY KINEMATICS MAGNITUDE (the jabberwock's self-fix — motor core / prediction_minus_observation):
    # the action carries only the DIRECTION (±1); the body actually slides by the SLIDE. Observe the value-body
    # that moved in my action's direction; its displacement magnitude IS the slide. Correct last_disp's
    # magnitude to the OBSERVED one so _emit_avatar_motion shifts by the true amount (it was shifting by 1
    # while the body moved 5 -> never found the avatar). Per-world: a slide-1 world (maze) stays ±1.
    if old_grid is not None and now_grid is not None and last_disp != (0, 0):
        import numpy as _np
        og, ng = _np.asarray(old_grid), _np.asarray(now_grid)
        bg = {int(og[0, 0]), int(_np.bincount(ng.ravel()).argmax())}
        sdr = (1 if last_disp[0] > 0 else -1 if last_disp[0] < 0 else 0)
        sdc = (1 if last_disp[1] > 0 else -1 if last_disp[1] < 0 else 0)
        for vv in (set(int(x) for x in _np.unique(ng)) - bg):
            if not (4 <= int((ng == vv).sum()) <= 40):
                continue
            oy, ny = _np.where(og == vv), _np.where(ng == vv)
            if not len(oy[0]) or not len(ny[0]):
                continue
            ddr = float(ny[0].mean() - oy[0].mean()); ddc = float(ny[1].mean() - oy[1].mean())
            if abs(ddr) + abs(ddc) > 0.5 and \
               (1 if ddr > 0 else -1 if ddr < 0 else 0) == sdr and \
               (1 if ddc > 0 else -1 if ddc < 0 else 0) == sdc:     # moved in MY action's direction -> it's me
                st["learned_mag"] = int(round(abs(ddr) + abs(ddc))); break
        mag = st.get("learned_mag", st.get("last_slide", 1))
        last_disp = (sdr * mag, sdc * mag); st["last_disp"] = last_disp
    I.set_attr(game, "frame", float(i))
    I.set_attr(game, "last_drow", float(last_disp[0])); I.set_attr(game, "last_dcol", float(last_disp[1]))
    ar._emit_avatar_motion(agent, game, st["prev_grid"], now_grid, last_disp[0], last_disp[1])
    st["prev_grid"] = now_grid
    ar._stamp(agent, game, getattr(agent, "_score", 0), i, ar._action_budget(agent))
    agent.inner.add_node("NativeSpatialSenseReceipt", {
        "schema": "native_spatial_sense_receipt_v1",
        "cluster": "spatial_sense.navigation_settlement",
        "provenance": "native_rule_readback:spatial_navigation",
        "native_rule": "spatial_sense_navigation_rules",
        "native_steps": ["stamp_perception", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    agent.inner.run_rules()                              # correlate -> latch avatar; derive -> commit

    av = next((n for n in S.nodes("AvatarCandidate") if S.node(n)["attrs"].get("is_avatar")), None)
    I.set_attr(game, "chosen_action", "")
    I.set_attr(game, "probe_action", "")
    if av is not None:
        acy = S.node(av)["attrs"].get("cy") or 0; acx = S.node(av)["attrs"].get("cx") or 0
        # RUN THE AUTHORED RETAINING CORTEX LIVE: if the agent has authored its retaining_tracker faculty,
        # the perception pipe takes the avatar position from its method — value-preserving translation: the
        # centroid of the whole value-body, which persists and moves as one (object permanence), instead of
        # the eye's connected-region centroid that splits/jumps. This is the host running the agent's OWN
        # authored faculty (it built it), gated on its existence; the eye remains the seed for the value.
        # ACTION-CORRELATED CONTROLLED-ITEM IDENTIFICATION (the jabberwock's faculty: prediction_minus_
        # observation + competitive_inhibition). Each value-body has a predicted displacement = my action's
        # (last_disp). Accumulate per-value CONTROL-CREDIT: the body that MOVES AS MY ACTION PREDICTS earns
        # credit; one that MOVES AGAINST it is a mover and loses credit; one that STAYS (blocked/static) is
        # neutral. Over turns the controlled avatar wins and movers are inhibited — disambiguating value-12
        # (the avatar, moves with me) from value-8/9 (movers) that a single-frame match confuses.
        import numpy as _np
        if now_grid is not None and last_disp != (0, 0):
            ng = _np.asarray(now_grid)
            bg = {int(ng[0, 0]), int(_np.bincount(ng.ravel()).argmax())}
            prevc = st.setdefault("prev_centroids", {}); credit = st.setdefault("control_credit", {}); curc = {}
            for vv in (set(int(x) for x in _np.unique(ng)) - bg):
                if not (4 <= int((ng == vv).sum()) <= 40):
                    continue
                ys, xs = _np.where(ng == vv); curc[vv] = (float(ys.mean()), float(xs.mean()))
                if vv in prevc:
                    obs = (curc[vv][0] - prevc[vv][0], curc[vv][1] - prevc[vv][1])
                    if abs(obs[0]) + abs(obs[1]) < 1.0:
                        pass                                                # stayed (blocked/static) — neutral
                    elif abs(obs[0] - last_disp[0]) + abs(obs[1] - last_disp[1]) <= 3.0:
                        credit[vv] = credit.get(vv, 0.0) + 1.0              # moved AS my action predicted -> mine
                    else:
                        credit[vv] = credit.get(vv, 0.0) - 1.0             # moved against it -> a mover
            st["prev_centroids"] = curc
        # FIX THE EYE POSITION EVERYWHERE: once the action-correlation has a clear winner (the controlled
        # body), take the avatar position from ITS value-body centroid — clean, persists, moves as one — and
        # write it back to the AvatarCandidate's cy/cx so EVERY downstream reader (flood seed, hop, _understanding,
        # nav) uses the true position, not the eye's scrambled region centroid. Until a winner accrues, the eye
        # seeds it. (Slide-1 worlds with one body trivially win and are unchanged.)
        credit = st.get("control_credit", {})
        V = (max(credit, key=credit.get) if credit and max(credit.values()) >= 3.0 else None)
        if V is not None and now_grid is not None:
            ys, xs = _np.where(_np.asarray(now_grid) == int(V))
            if 0 < len(ys) < 40:
                acy, acx = float(_np.mean(ys)), float(_np.mean(xs))
                I.set_attr(av, "cy", acy); I.set_attr(av, "cx", acx)   # the clean position, everywhere
        cur_pos = (round(acy), round(acx))
        stuck_now = st["prev_av_pos"] is not None and cur_pos == st["prev_av_pos"] and last_disp != (0, 0)
        moved = st["prev_av_pos"] is not None and cur_pos != st["prev_av_pos"] and last_disp != (0, 0)
        st["nav_stuck"] = st["nav_stuck"] + 1 if stuck_now else 0
        I.set_attr(game, "nav_stuck", float(st["nav_stuck"]))   # the avatar's MOVEMENT-stuck signal, on the
        st["prev_av_pos"] = cur_pos                             # graph (reliable now that perception is stable)
        # GOAL-THRASH BREAK (the jabberwock's competitive_inhibition fix): when my CLEAN recent positions are a
        # tiny set, I am ping-ponging between two cells at a dead-end while the hop chases an unreachable goal.
        # Inhibit the loop: emit a move PERPENDICULAR to the oscillation axis so I explore laterally, not back.
        recent = st.setdefault("recent", []); recent.append(cur_pos); del recent[:-5]
        if len(recent) >= 4 and len(set(recent[-4:])) <= 2:
            rs = [p[0] for p in recent[-4:]]; cs = [p[1] for p in recent[-4:]]
            perp = ("Left", "Right") if (max(rs) - min(rs)) >= (max(cs) - min(cs)) else ("Up", "Down")
            I.set_attr(game, "break_dir", perp[i % 2])
        else:
            I.set_attr(game, "break_dir", "")
        mslide = next((S.node(m)["attrs"].get("slide") for m in S.nodes("AvatarMotion")), None)
        st["last_slide"] = int(mslide) if mslide else st["last_slide"]; ls = st["last_slide"]
        import numpy as _np
        ground = int(_np.bincount(_np.asarray(now_grid).ravel()).argmax()) if now_grid is not None else 4
        I.set_attr(game, "ground", float(ground)); I.set_attr(game, "slide", float(ls))
        fp = ar._avatar_footprint(agent, acy, acx)
        # SEED THE WALKABLE SURFACE (prediction_minus_observation + discriminate surface/void): the floor is the
        # colour my body STANDS IN, not the globally most-common colour — in a game where the avatar lives on a
        # distinct playfield, the most-common colour is the VOID I never enter. Read the ring just outside my
        # footprint ONCE; its dominant colour is my surface. _wall_values uses it to stop flooding the void.
        if fp and now_grid is not None and st.get("surface_val") is None:
            try:
                gg = _np.asarray(now_grid); H, W = gg.shape
                r0, c0, hh, ww, av = fp
                ring = [int(gg[rr, cc])
                        for rr in range(max(0, r0 - 1), min(H, r0 + hh + 1))
                        for cc in range(max(0, c0 - 1), min(W, c0 + ww + 1))
                        if not (r0 <= rr < r0 + hh and c0 <= cc < c0 + ww) and int(gg[rr, cc]) != av]
                if ring:
                    st["surface_val"] = int(_np.bincount(_np.asarray(ring)).argmax())
            except Exception:
                pass
        # LEARN PASSABILITY FROM MOTION: if the avatar MOVED, the cells it now fills were passable in the
        # pre-move grid — record those values so _wall_values stops calling them walls (the cortex's map
        # is corrected by what it has actually done, not the static value heuristic).
        if moved and fp and old_grid is not None:
            pv = st.setdefault("passable_vals", set())
            try:
                H, W = len(old_grid), len(old_grid[0])
                for rr in range(max(0, fp[0]), min(H, fp[0] + fp[2])):
                    for cc in range(max(0, fp[1]), min(W, fp[1] + fp[3])):
                        v = int(old_grid[rr][cc])
                        if v != fp[4]:
                            pv.add(v)
            except Exception:
                pass
        walls = ar._wall_values(agent, ground, fp[4]) if fp else [ground]
        A = ar._cell_index(agent).get((fp[0], fp[1])) if fp else None
        if (S.node(game)["attrs"].get("nav_repr") or "") == "quanta":
            # QUANTA MODE (FLOOD_DESIGN Part C): same perception stamps as cell mode, then the
            # quanta flood pass instead of the two slide_floods. BlockObs replaces `_blk_*`.
            if A is not None:
                I.set_attr(game, "fresh", 0.0 if S.node(A)["attrs"].get("visited") == 1.0 else 1.0)
                if st["prev_cell"] is not None and st["prev_cell"] != A:
                    I.set_attr(st["prev_cell"], "is_avatar_cell", 0.0)
                I.set_attr(A, "is_avatar_cell", 1.0); st["prev_cell"] = A
            ar._wire_nav_modes(agent, game)
            st["near_mover"] = ar._stamp_near_mover(agent, st["near_mover"])
            pend = False
            if stuck_now:
                record_block_obs(agent, game, cur_pos, last_disp, i)
                pend = True
            bump_belief_epoch(agent)                     # a live frame refreshes the belief each tick
            gg = _np.asarray(now_grid) if now_grid is not None else None
            grid_hw = tuple(gg.shape) if gg is not None else (64, 64)
            vals = sorted(set(int(v) for v in _np.unique(gg))) if gg is not None else []
            passable = [v for v in vals if v not in set(int(w) for w in walls)]
            quanta_flood_step(agent, game, cur_pos, ((fp[2], fp[3]) if fp else (1, 1)),
                              passable, ls, grid_hw, pending_block=pend)
        elif A is not None:
            fph, fpw = fp[2], fp[3]; blocked = st["blocked"]
            for (bcell, battr), bf in list(blocked.items()):
                if i - bf >= BLOCK_TTL:
                    I.set_attr(bcell, battr, 0.0); del blocked[(bcell, battr)]
            if stuck_now:
                ba = ar._blk_attr(last_disp)
                if ba is not None:
                    I.set_attr(A, ba, 1.0); blocked[(A, ba)] = i
            I.set_attr(game, "fresh", 0.0 if S.node(A)["attrs"].get("visited") == 1.0 else 1.0)
            if st["prev_cell"] is not None and st["prev_cell"] != A:
                I.set_attr(st["prev_cell"], "is_avatar_cell", 0.0)
            I.set_attr(A, "is_avatar_cell", 1.0); st["prev_cell"] = A
            gid = int(str(game).lstrip("#"))
            ar._wire_nav_modes(agent, game)
            st["near_mover"] = ar._stamp_near_mover(agent, st["near_mover"])
            if (S.node(game)["attrs"].get("nav_mode") or "") == "pocket_escape" and blocked:
                for bk in list(blocked.keys()):
                    I.set_attr(bk[0], bk[1], 0.0)
                blocked.clear()
            I.slide_flood(int(str(A).lstrip("#")), ls, fph, fpw, walls, 40, i, gid, True, "_adist")
            I.set_attr(game, "flood_epoch", float(i))
            reached_now = set(int(str(n).lstrip("#")) for n in I.neighbours(game, "reached"))
            I.set_attr(game, "frontier_flux", float(len(reached_now ^ st["prev_reached"]) if st["prev_reached"] else 0))
            st["prev_reached"] = reached_now
            agent.inner.add_node("NativeSpatialSenseReceipt", {
                "schema": "native_spatial_sense_receipt_v1",
                "cluster": "spatial_sense.navigation_settlement",
                "provenance": "native_rule_readback:spatial_navigation",
                "native_rule": "spatial_sense_navigation_rules",
                "native_steps": ["slide_flood", "run_rules", "readback"],
                "outcome_source": "native_rule_readback",
                "python_outcome_selection": False,
            })
            agent.inner.run_rules()
            goal = next(iter(I.neighbours(game, "committed_goal")), None)
            if goal is not None:
                I.slide_flood(int(str(goal).lstrip("#")), ls, fph, fpw, walls, 40, i, gid, False, "_dist")
                agent.inner.add_node("NativeSpatialSenseReceipt", {
                    "schema": "native_spatial_sense_receipt_v1",
                    "cluster": "spatial_sense.navigation_settlement",
                    "provenance": "native_rule_readback:spatial_navigation",
                    "native_rule": "spatial_sense_navigation_rules",
                    "native_steps": ["goal_slide_flood", "run_rules", "readback"],
                    "outcome_source": "native_rule_readback",
                    "python_outcome_selection": False,
                })
                agent.inner.run_rules()
        # mechanical fallbacks the rules leave to perception: pocket_escape sweep / unstick.
        if not (S.node(game)["attrs"].get("chosen_action") or ""):
            if (S.node(game)["attrs"].get("nav_mode") or "") == "pocket_escape":
                I.set_attr(game, "chosen_action", BOOTSTRAP[i % 4])
            elif st["nav_stuck"] >= 2:
                I.set_attr(game, "chosen_action", BOOTSTRAP[(i + st["nav_stuck"]) % 4])
        elif (S.node(game)["attrs"].get("nav_mode") or "") == "pocket_escape":
            I.set_attr(game, "chosen_action", BOOTSTRAP[i % 4])


# stimulus: a Game node exists (the world is loaded) -> fire the spatial sense every tick.
_STIMULUS = {"type": "Gte", "a": {"type": "Count", "source": {"type": "Filter",
    "source": {"type": "NodesOfType", "node_type": "WorldInstance"}, "var_name": "x",
    "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "world_type"},
                  "b": {"type": "Lit", "value": "Game"}}}}, "b": {"type": "Lit", "value": 1}}


def install(agent) -> None:
    """Wire the spatial sense as a graph-resident Reflex master_tick fires every tick."""
    agent.register_reflex_response("spatial_sense", lambda ag: spatial_sense_step(ag))
    agent.install_reflex("spatial_sense", _STIMULUS, "spatial_sense")
