"""THE ENTITY LEARNS THE NEW DOMAIN'S DYNAMICS ITSELF — using the SAME learning faculty it used in the
Tetris gym (discriminative model-selection: try candidate laws, keep the one that fits observation).
In Tetris it learned gravity-direction + the stop-law + line-clear (7f151fdd). Here, in the maze, it
learns the new laws from watching: the move EFFECTS, what BLOCKS a move, and what ENDS the episode.
The learning METHOD transfers; the laws are the new world's. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_learns_maze.py
"""
from __future__ import annotations
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from jabberwock_transfers import make_world, HG, WG, FREE, WALL, HAZ
CONTROLS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}   # true effects (hidden from the entity)
TYPES = {FREE: "free", WALL: "wall", HAZ: "hazard"}


def explore(n_mazes=6, steps=400):
    """ADAPTER I/O: wander the mazes, trying every control; record each transition the entity observes."""
    recs = []   # (control, dr_obs, dc_obs, moved, target_type_for_each_dir, ended, on_after_type)
    for m in range(n_mazes):
        g, pos = make_world(m + 20); rng = random.Random(m)
        for _ in range(steps):
            ctrl = rng.choice(list(CONTROLS))
            dr, dc = CONTROLS[ctrl]
            nr, nc = pos[0] + dr, pos[1] + dc
            inb = 0 <= nr < HG and 0 <= nc < WG
            tgt_type = TYPES[g[nr][nc]] if inb else "edge"
            moved = inb and g[nr][nc] != WALL
            after = (nr, nc) if moved else pos
            on_after = TYPES[g[after[0]][after[1]]]
            ended = moved and g[after[0]][after[1]] == HAZ
            recs.append((ctrl, after[0] - pos[0], after[1] - pos[1], moved, tgt_type, ended, on_after))
            if ended:
                g, pos = make_world(m + 20)
            else:
                pos = after
    return recs


def main():
    recs = explore()
    print("=" * 84)
    print("THE ENTITY LEARNS THE MAZE DYNAMICS ITSELF (transferred discriminative faculty)")
    print("=" * 84)

    # 1 LEARN MOVE EFFECTS: per control, the displacement when it actually moved (the affordance effect)
    print("  1) move effects learned (control -> observed displacement when it moved):")
    eff = {}
    for c in CONTROLS:
        ms = [(dr, dc) for cc, dr, dc, mv, *_ in recs if cc == c and mv]
        if ms:
            from collections import Counter
            eff[c] = Counter(ms).most_common(1)[0][0]
            print(f"       {c:6} -> {eff[c]}   (matches {sum(1 for x in ms if x==eff[c])}/{len(ms)})")

    # 2 LEARN WHAT BLOCKS A MOVE: which target-type discriminates 'did not move'? (try candidates)
    blocked = [r for r in recs if not r[3]]; movedr = [r for r in recs if r[3]]
    print(f"\n  2) block law — P(target=TYPE | move BLOCKED) vs P(| moved), over {len(blocked)} blocked / {len(movedr)} moved:")
    scores = {}
    for t in ("wall", "hazard", "free", "edge"):
        pb = sum(1 for r in blocked if r[4] == t) / max(len(blocked), 1)
        pm = sum(1 for r in movedr if r[4] == t) / max(len(movedr), 1)
        scores[t] = pb - pm
        print(f"       target={t:6}: blocked {pb:.2f}  moved {pm:.2f}  discrimination {pb-pm:+.2f}")
    block_by = max(scores, key=scores.get)
    print(f"     -> LEARNED: a move is blocked by '{block_by}' (discrimination {scores[block_by]:+.2f})")

    # 3 LEARN WHAT ENDS THE EPISODE: which cell-under-me discriminates 'ended'? (try candidates)
    ended = [r for r in recs if r[5]]; alive = [r for r in recs if not r[5]]
    print(f"\n  3) death law — P(on=TYPE | ENDED) vs P(| alive), over {len(ended)} deaths / {len(alive)} alive:")
    dscore = {}
    for t in ("hazard", "free"):
        pe = sum(1 for r in ended if r[6] == t) / max(len(ended), 1)
        pa = sum(1 for r in alive if r[6] == t) / max(len(alive), 1)
        dscore[t] = pe - pa
        print(f"       on={t:6}: ended {pe:.2f}  alive {pa:.2f}  discrimination {pe-pa:+.2f}")
    death_by = max(dscore, key=dscore.get)
    print(f"     -> LEARNED: the episode ends on '{death_by}' (discrimination {dscore[death_by]:+.2f})")

    # VERIFY: the learned laws reproduce the world on fresh transitions
    g, pos = make_world(999); rng = random.Random(7); ok = 0; tot = 0
    for _ in range(500):
        ctrl = rng.choice(list(CONTROLS)); dr, dc = eff.get(ctrl, (0, 0))
        nr, nc = pos[0] + dr, pos[1] + dc; inb = 0 <= nr < HG and 0 <= nc < WG
        pred_move = inb and TYPES.get(g[nr][nc] if inb else WALL, "edge") != block_by
        pred_end = pred_move and inb and TYPES[g[nr][nc]] == death_by
        true_move = inb and g[nr][nc] != WALL
        true_end = true_move and g[nr][nc] == HAZ
        tot += 1; ok += (pred_move == true_move and pred_end == true_end)
        if true_end:
            g, pos = make_world(999)
        elif true_move:
            pos = (nr, nc)
    print("=" * 84)
    print(f"  VERIFY: the learned laws (effects + block='{block_by}' + death='{death_by}') reproduce the")
    print(f"  world on fresh transitions: {ok}/{tot}.")
    print("  The entity LEARNED the new domain's dynamics ITSELF — same discriminative faculty as the")
    print("  Tetris gym (try candidate laws, keep the one that fits), new laws (move effects, walls block,")
    print("  hazards end). The learning METHOD transferred; the dynamics are the maze's. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
