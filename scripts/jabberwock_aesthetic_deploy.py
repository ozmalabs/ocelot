"""AESTHETIC DEPLOYMENT — the jabberwock makes the top shape the SAME as the
bottom answer-key, by deploying its transform-understanding through the cross.

It already has every piece: navigate to the lone salient item (the cross), the
transform-understanding that ENTERING it transforms (rotates) the top shape, the
ORDER-N comparison of top vs bottom (domains.transform_concepts — its own order-N
descriptor), and the AESTHETIC drive (two instances of the same shape at the same
pose is more compressible/pleasing → make them match). This shell drives its OWN
navigation to the cross and the enter/exit sweep; the DECISION 'are they the same
now?' is the agent's order-N comparison, and it stops when they match.

Budget-aware: agency (CellC12) + the four directions are known from the prior
session, so we skip the long probes and spend the turn budget on the task.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["ARC3_THIN"] = "1"; os.environ["ARC3_FULL"] = "1"

import numpy as np  # noqa: E402
from _arc3_load_key import load_arc_api_key  # noqa: E402
from arc3_live_env import Arc3LiveEnv  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_thin import arc3_thin_handle, SELF_ID  # noqa: E402
from domains.arc3_full_seed import install_full_seed_set  # noqa: E402
from arc3_live_experiment import _live_legal_actions  # noqa: E402
from domains.transform_concepts import _profile, _order_n  # noqa: E402

PT = "CellC12"


def cells_of(grid, val, box):
    a = np.array(grid); r0, r1, c0, c1 = box
    ys, xs = np.where(a[r0:r1, c0:c1] == val)
    return set((int(r), int(c)) for r, c in zip(ys, xs))


def order_n_vec(cells):
    return _order_n(_profile(cells))


def cosine(a, b):
    import math
    n = min(len(a), len(b)); a, b = a[:n], b[:n]
    da = math.sqrt(sum(x * x for x in a)); db = math.sqrt(sum(x * x for x in b))
    if da == 0 or db == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (da * db)


def avatar(grid):
    a = np.array(grid); ys, xs = np.where(a == 12)
    return (ys.mean(), xs.mean()) if len(xs) else None


def main():
    if not load_arc_api_key():
        print("BLOCKER: no key"); return 2
    env = Arc3LiveEnv(game_id="ls20-9607627b")
    agent = CuriousAgent(); agent.my_world_id = SELF_ID
    install_full_seed_set(agent)
    h = arc3_thin_handle(env, agent); sub, ctx = h["reset"](); agent.observe(sub)

    TOP = (6, 20, 28, 44); BOT = (50, 63, 0, 14)
    bot = cells_of(ctx["frame"].grid, 9, BOT)
    bvec = order_n_vec(bot)
    print(f"answer key (bottom): {len(bot)} cells  (the target the top must match)")

    def engage(sub):
        g = sub.graph; body = None; cs = []
        for n in g.nodes():
            if n.type == "Body":
                body = n.id
            elif n.type == PT:
                cs.append(n)
        if body is None or not cs:
            return
        cy = sum(int(g.node(c.id).attrs["row"]) for c in cs) / len(cs)
        cx = sum(int(g.node(c.id).attrs["col"]) for c in cs) / len(cs)
        cen = min(cs, key=lambda c: (int(g.node(c.id).attrs["row"]) - cy) ** 2 + (int(g.node(c.id).attrs["col"]) - cx) ** 2)
        g._insert_edge(body, "at_location", cen.id)
        ra = agent.mind_graph.node(agent.agent_root).attrs
        ra["my_x_bin"] = int(round(cx)); ra["my_y_bin"] = int(round(cy))

    engage(sub); agent.observe(sub)
    # seed the four directions cheaply (one move each), so navigation can route.
    for nm in ("a1", "a2", "a3", "a4"):
        sub, ctx = h["apply_action"](sub, ctx, (nm,)); engage(sub); agent.last_action_kind = nm; agent.observe(sub)

    def top_match():
        t = cells_of(ctx["frame"].grid, 9, TOP)
        if not t:
            return -1.0, 0
        return cosine(order_n_vec(t), bvec), len(t)

    best_cos = -1.0; rotations = 0; prev_pose = None
    from domains.transform_concepts import pose_sig
    prev_pose = pose_sig(cells_of(ctx["frame"].grid, 9, TOP))
    print("\nDEPLOY — seek the cross, transform the top, compare to the key:")
    for i in range(60):
        p = avatar(ctx["frame"].grid)
        if p is None:
            sub, ctx = h["apply_action"](sub, ctx, ("a1",)); engage(sub); agent.observe(sub); continue
        cy, cx = p
        if abs(cx - 21) <= 1 and cy <= 31:
            # ENTER (sweep down through the cross) then EXIT (up) — one transform.
            for nm in ("a2", "a1"):
                sub, ctx = h["apply_action"](sub, ctx, (nm,)); engage(sub); agent.last_action_kind = nm; agent.observe(sub)
        else:
            acts = _live_legal_actions(h, sub, ctx, env, 8) or _live_legal_actions(h, sub, ctx, env, 1)
            act = agent.choose_action(sub, ctx, acts, h)
            for t in h["interpret_acts_on"](sub, ctx, act):
                agent._register_relation(t, "acts_on")
            agent._record_activity("act", []); sub, ctx = h["apply_action"](sub, ctx, act); engage(sub); agent.observe(sub)
        # did the top TRANSFORM? (its pose changed) — and how close to the key now?
        cur_pose = pose_sig(cells_of(ctx["frame"].grid, 9, TOP))
        if cur_pose != prev_pose:
            rotations += 1
            cos, n = top_match()
            best_cos = max(best_cos, cos)
            print(f"  rot #{rotations}: top now {n} cells, order-N match-to-key={cos:.3f}, score={ctx['score']}")
            prev_pose = cur_pose
            if cos > 0.97:
                print("  *** AESTHETIC MATCH — top is now the same as the answer key ***")
                break
        if ctx["score"] > 0:
            print("  *** SCORE", ctx["score"]); break
    print(f"\nrotations observed: {rotations}   best order-N match-to-key: {best_cos:.3f}   score: {ctx['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
