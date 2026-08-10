"""doom_operate_run — make a RECOGNISED door actually OPEN on real E1M1 (block 210000).

The ACT half of 209000: recognition -> approach -> USE -> the door OPENS. The eye
(209000, texture channel, RGB luma only) recognises the door; the operate rules
(seeds/doom_operate.json) DECIDE the motor command (orient/approach/USE); this
runner is MECHANICAL VizDoom I/O + MEASUREMENT only -- it writes sensors, presses
the button the graph names, and scores the open from the door sector's ceiling
(a SCORING oracle for the METRIC only; it never enters the eye).

Two arms on the SAME doors/approach:
  gated  -- the graph presses USE once, only when a door is recognised AND in range
            AND faced (the operate rules).
  spam   -- USE pressed EVERY tic while approaching (the 209000 0/1800 failure mode:
            in Doom a USE on an opening DR door toggles it back closed).

    PYTHONPATH=. python3 scripts/doom_operate_run.py
"""
from __future__ import annotations
import argparse, json, math, os, struct

import numpy as np
import domains.doom_pattern_eye as eye
import domains.doom_operate as op

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "doom_operate")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
GW = 320
CENTER, FACE_TOL, BLOCK = 160, 40, 4
OPEN_RISE = 32                       # ceiling rise (map units) that counts as OPEN (full ~+68)
SAL_FLOOR = 2
NEAR_TEX = 4                         # texture level at which fine detail resolves (mid-distance);
#                                      sets `near` so the fine door/switch recognition LATCHES
#                                      before texture collapses at flat contact. 4 aligns the
#                                      latch with when the switch prototype [0,6] is reachable
#                                      (L1 dist |0-4|+|4-6|? no: geom 0, |4-6|=2 < match_thresh 3);
#                                      a tex-2 face stays correctly unrecognised (dist 4).

# Real DR doors on E1M1, VizDoom sector index == WAD sector number (validated: single
# USE at range raises the sector ceiling 0->~72). approach = (dx,dy) offset from door
# centre to a start point on the room side (validated to open).
# approach = a start offset from the door centre on an OPENABLE face (validated: single USE
# raises the sector ceiling ~+68). Each door's chosen face is the one that both opens AND
# reads texture from the eye where such a face exists; sec83's only openable faces read
# texture ~2 (the eye genuinely cannot recognise it -- the 209000 texture-channel residual
# that 211000's geometry channel addresses), kept in the set as an honest negative.
DOORS = [
    {"sector": 26, "center": (1544, -2496), "approach": (-130, 0)},    # tex 8 -- strong
    {"sector": 69, "center": (3008, -4640), "approach": (0, -130)},    # tex 8 -- strong
    {"sector": 85, "center": (3008, -4024), "approach": (0, -130)},    # tex ~4 -- faint but resolvable
    {"sector": 83, "center": (2928, -3840), "approach": (-130, 0)},    # tex ~2 -- eye-invisible (residual)
]
JITTERS = [-25, -12, 0, 12, 25]      # initial facing offset (deg) -> orient must correct it


def _wad_doors():
    """Provenance: parse DOOM.WAD E1M1 door linedefs (special==1) -> door sectors, so the
    DOORS table above is reproducible, not magic. Returns {sector: (mx,my)}."""
    data = open(WAD, "rb").read()
    _, numl, diroff = struct.unpack("<4sii", data[:12])
    lumps = []
    for i in range(numl):
        off, sz, name = struct.unpack("<ii8s", data[diroff + i * 16:diroff + i * 16 + 16])
        lumps.append((name.rstrip(b"\0").decode("latin1"), off, sz))
    mi = [i for i, (n, _, _) in enumerate(lumps) if n == "E1M1"][0]
    def lump(name):
        for j in range(mi, mi + 11):
            if lumps[j][0] == name:
                return data[lumps[j][1]:lumps[j][1] + lumps[j][2]]
        return b""
    verts = [struct.unpack("<hh", lump("VERTEXES")[k:k + 4]) for k in range(0, len(lump("VERTEXES")), 4)]
    sd = lump("SIDEDEFS"); sides = [struct.unpack("<hh8s8s8sh", sd[k:k + 30]) for k in range(0, len(sd), 30)]
    ld = lump("LINEDEFS")
    out = {}
    for k in range(0, len(ld), 14):
        v1, v2, flags, special, tag, rs, ls = struct.unpack("<HHHHHHH", ld[k:k + 14])
        if special == 1:                          # DR Door (open, wait, close) -- USE activated
            x1, y1 = verts[v1]; x2, y2 = verts[v2]
            sec = sides[ls][5] if ls != 0xFFFF else (sides[rs][5] if rs != 0xFFFF else None)
            if sec is not None:
                out[sec] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return out


def _game():
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(WAD); g.set_doom_scenario_path(WAD); g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240); g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_sectors_info_enabled(True); g.add_game_args("-nomonsters")
    g.set_render_hud(False); g.set_render_weapon(False)
    g.set_window_visible(False); g.set_mode(vzd.Mode.PLAYER); g.set_doom_skill(3)
    for b in (vzd.Button.MOVE_FORWARD, vzd.Button.TURN_LEFT, vzd.Button.TURN_RIGHT, vzd.Button.USE):
        g.add_available_button(b)
    gv = vzd.GameVariable
    for v in (gv.POSITION_X, gv.POSITION_Y, gv.ANGLE):
        g.add_available_game_variable(v)
    g.set_seed(1234); g.init(); g.new_episode()
    return g, gv


def _pose(g, gv):
    return (g.get_game_variable(gv.POSITION_X), g.get_game_variable(gv.POSITION_Y),
            g.get_game_variable(gv.ANGLE))


def _rgb(g):
    a = np.array(g.get_state().screen_buffer)
    return np.transpose(a, (1, 2, 0)) if a.shape[0] == 3 else a


def _door_gap(g, sec):
    st = g.get_state()
    if st is None or len(st.sectors) <= sec:
        return None
    return st.sectors[sec].ceiling_height - st.sectors[sec].floor_height


def _target_column(rgb):
    """Eye read (RGB luma only): localise the operable feature as the HIGH-texture blob and
    report its centroid column + representative texture level. The door reads as a strong
    texture blob at mid-distance; pressed flat against it the surface is uniform and texture
    -> ~0 (recognition is then object-permanent, latched during approach)."""
    tex, _ = eye.col_texture_level(rgb)
    mx = int(tex.max())
    if mx < SAL_FLOOR:
        return None, 0                       # no texture in view (e.g. flat against the door)
    hi = np.where(tex >= max(SAL_FLOOR, mx // 2))[0]     # the high-texture blob (the feature)
    col = int(round(hi.mean())) if hi.size else CENTER
    lvl = int(np.median(tex[hi])) if hi.size else 0      # the blob's texture (door reads 6-8)
    return col, lvl


def _episode(arm, door, jitter, *, maxtic=55, obs_tics=40):
    import vizdoom as vzd
    g, gv = _game()
    dx, dy = door["center"]; ax, ay = dx + door["approach"][0], dy + door["approach"][1]
    g.send_game_command("warp %d %d" % (ax, ay)); g.make_action([0, 0, 0, 0], 1)
    px, py, _ = _pose(g, gv)
    if math.hypot(px - ax, py - ay) > 60:         # warp landed off (in a wall) -> skip
        g.close(); return None
    door_ang = math.degrees(math.atan2(dy - py, dx - px)) % 360
    want = (door_ang + jitter) % 360               # harness sets a jittered facing; orient corrects it
    for _ in range(40):
        _, _, ang = _pose(g, gv)
        err = (want - ang + 180) % 360 - 180
        if abs(err) < 6:
            break
        g.make_action([0, 1, 0, 0] if err > 0 else [0, 0, 1, 0], 2)

    # graph substrate
    wa = eye.fresh_adapter(); op.load_operate_seed(wa)
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
    eye.install(wa, game, salience_floor=SAL_FLOOR)
    op.install(wa, game, center=CENTER, face_tol=FACE_TOL, block_thresh=BLOCK)
    R = op.make_target_region(wa, game)

    base = _door_gap(g, door["sector"])
    last_fwd = 99; n_use = 0; opened = False; open_at = -1; used_pose = None
    last_col = CENTER
    trace = []
    for t in range(maxtic):
        if g.is_episode_finished():
            break
        col, lvl = _target_column(_rgb(g))
        if col is None:                       # texture collapsed (flat against door) -> hold last
            col, lvl = last_col, 0
        else:
            last_col = col
        # `near` (detail resolvable at mid-distance) LATCHES the fine door/switch recognition
        # while texture is still readable; the USE decision uses the latched `recognised`.
        near = 1 if lvl >= NEAR_TEX else 0
        op.update_sensors(wa, R, col=col, tex_level=lvl, near=near, fwd_progress=last_fwd)
        cmd = op.step(wa, game)

        do_use = (cmd == "use") or (arm == "spam")
        # spam still needs to navigate: use the graph nav command for movement
        nav = cmd if cmd in ("forward", "turn_left", "turn_right") else ("forward" if arm == "spam" else None)

        if do_use:
            g.make_action([0, 0, 0, 1], 1); g.make_action([0, 0, 0, 0], 1)   # single USE pulse
            n_use += 1
            if cmd == "use":
                used_pose = tuple(round(x) for x in _pose(g, gv))
        if nav == "forward":
            p0 = _pose(g, gv)[:2]
            g.make_action([1, 0, 0, 0], 3)
            p1 = _pose(g, gv)[:2]
            last_fwd = int(round(math.hypot(p1[0] - p0[0], p1[1] - p0[1])))
        elif nav in ("turn_left", "turn_right"):
            g.make_action([0, 1, 0, 0] if nav == "turn_left" else [0, 0, 1, 0], 2)

        gap = _door_gap(g, door["sector"])
        trace.append({"t": t, "cmd": cmd, "col": col, "lvl": lvl, "near": near,
                      "fwd": last_fwd, "gap": None if gap is None else round(gap, 1)})
        if gap is not None and base is not None and gap - base > OPEN_RISE:
            opened = True; open_at = t; break
        goal = op.read_goal(wa, game)
        if cmd == "none" and arm == "gated" and goal and goal["status"] == "operated":
            # USE has fired; observe the ceiling rise (no more USE -> the door opens)
            for w in range(obs_tics):
                g.make_action([0, 0, 0, 0], 1)
                gap = _door_gap(g, door["sector"])
                if gap is not None and base is not None and gap - base > OPEN_RISE:
                    opened = True; open_at = t + w; break
            break
    g.close()
    return {"arm": arm, "sector": door["sector"], "jitter": jitter, "opened": opened,
            "open_at": open_at, "n_use": n_use, "base_gap": base, "used_pose": used_pose,
            "tics": len(trace), "trace": trace}


def run(outdir=OUTDIR, arms=("gated", "spam")):
    os.makedirs(outdir, exist_ok=True)
    wad = _wad_doors()
    results = {}
    for arm in arms:
        eps = []
        for door in DOORS:
            for j in JITTERS:
                r = _episode(arm, door, j)
                if r is None:
                    continue
                eps.append(r)
                print("[%s] door sec%d jit%+d -> %s (n_use=%d open_at=%d used_pose=%s)" % (
                    arm, door["sector"], j, "OPEN" if r["opened"] else "no",
                    r["n_use"], r["open_at"], r["used_pose"]), flush=True)
        opens = sum(1 for e in eps if e["opened"])
        tot_use = sum(e["n_use"] for e in eps)
        # precision = USE-presses-that-open / total-USE-presses. Gated fires >=1 USE per
        # opened episode; count the opens as the productive presses (1 clean USE each).
        prod = sum(1 for e in eps if e["opened"] and e["n_use"] >= 1)
        results[arm] = {
            "episodes": len(eps), "opens": opens, "total_use_presses": tot_use,
            "use_presses_that_open": prod,
            "open_rate": round(opens / len(eps), 3) if eps else None,
            "use_precision": round(prod / tot_use, 4) if tot_use else None,
            "detail": eps}
        print("== %s: %d opens / %d episodes; USE precision %s/%s ==" % (
            arm, opens, len(eps), prod, tot_use), flush=True)
    summary = {
        "map": "E1M1", "doors": DOORS, "wad_door_sectors": {str(k): v for k, v in wad.items()},
        "baseline_209000": "0 opens / 1800 USE-spammed tics",
        "open_rise_threshold": OPEN_RISE, "arms": results}
    with open(os.path.join(outdir, "gates.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("wrote", os.path.join(outdir, "gates.json"))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=OUTDIR)
    ap.add_argument("--arms", default="gated,spam"); args = ap.parse_args()
    try:
        import vizdoom  # noqa
        if not os.path.exists(WAD):
            raise RuntimeError("WAD absent")
    except Exception as e:
        print("SKIP: VizDoom/WAD unavailable:", e); raise SystemExit(0)
    run(args.out, arms=tuple(args.arms.split(",")))
