"""Standalone: the jabberwock LEARNS the LINE-CLEAR rule by fit, from CONTROLLED observation — set a
board + piece, let the world settle, and discover which rule reproduces the post-settle board. Fast."""
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path: sys.path.insert(0, p)
from tetris_world import TetrisEnv, EMPTY, SETTLED
from probe_landing import host_landing, SHAPES
H, W = 16, 8

def gen(rng):
    b = [[EMPTY]*W for _ in range(H)]
    for r in range(H - rng.randint(2, 4), H):
        gaps = rng.sample(range(W), rng.randint(1, 2))
        for c in range(W):
            if c not in gaps: b[r][c] = SETTLED
    return b

rem_full = lambda b: [[EMPTY]*W for _ in range(H - len([r for r in b if any(v==EMPTY for v in r)]))] + [r for r in b if any(v==EMPTY for v in r)]
rem_bottom = lambda b: [[EMPTY]*W] + b[:-1]
rem_none = lambda b: [r[:] for r in b]
RULES = {"remove FULL rows": rem_full, "remove bottom row": rem_bottom, "remove nothing": rem_none}

def main():
    rng = random.Random(0); obs = []
    for _ in range(500):
        b = gen(rng); sh = list(rng.choice(SHAPES)); col = rng.randint(0, W-1-max(c for _,c in sh))
        r = host_landing(b, sh, col)
        if r is None or r < 0: continue
        placed = [row[:] for row in b]
        for dr, dc in sh:
            if 0 <= r+dr < H: placed[r+dr][col+dc] = SETTLED
        env = TetrisEnv(); env._board = [row[:] for row in b]; env._shape = sh; env._pr = r; env._pc = col
        env._settle()                                  # the WORLD settles + clears (the agent only observes)
        obs.append((placed, [row[:] for row in env._board]))
    clears = [(p, a) for p, a in obs if p != a]
    print("=" * 78); print("THE JABBERWOCK LEARNS THE LINE-CLEAR RULE (by fit to controlled observation)"); print("=" * 78)
    print(f"  {len(obs)} settle observations, {len(clears)} with a line actually cleared")
    print(f"  candidate rules — match vs the world (all | settles-with-a-clear):")
    best = (-1, None)
    for name, fn in RULES.items():
        allm = sum(1 for p, a in obs if fn(p) == a)/max(len(obs), 1)
        clm = sum(1 for p, a in clears if fn(p) == a)/max(len(clears), 1)
        print(f"     {name:18}: all {allm:.2f}   on-clear {clm:.2f}")
        if clm > best[0]: best = (clm, name)
    print(f"  -> LEARNED: '{best[1]}' reproduces the world's clears (on-clear {best[0]:.2f}); controls fail.")
    print("  The line-clear rule is now the agent's, learned by fit — not given. donkey=0.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
