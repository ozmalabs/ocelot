"""arc3_live_connectivity — a NON-SENSITIVE connectivity check for the live
ARC-AGI-3 API. Confirms (without ever surfacing the key):

  · the key is present in the environment (boolean / length only);
  · /api/games is reachable and lists the public games;
  · a scorecard can be opened (AWS ALB cookie carried on the Session);
  · one game RESETs and returns a real frame (dims + score + available actions).

Prints only non-sensitive status. STOPS and reports if the network is blocked.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key  # noqa: E402


def main() -> int:
    present = load_arc_api_key()
    import os
    klen = len(os.environ.get("ARC_API_KEY", ""))
    print(f"key present: {present}  (length={klen})")  # NEVER the value
    if not present:
        print("BLOCKER: ARC_API_KEY not available; cannot reach the live API.")
        return 2

    import requests
    from arc3_live_env import Arc3LiveEnv, Arc3ApiError, DEFAULT_BASE_URL, ACTION6

    # 1) list the public games (shares the same X-Api-Key header).
    sess = requests.Session()
    sess.headers.update({
        "X-Api-Key": os.environ["ARC_API_KEY"],
        "Accept": "application/json",
    })
    try:
        r = sess.get(f"{DEFAULT_BASE_URL}/api/games", timeout=30)
    except Exception as e:
        print(f"BLOCKER: network egress to {DEFAULT_BASE_URL} failed: {type(e).__name__}: {e}")
        return 3
    if r.status_code != 200:
        print(f"BLOCKER: /api/games -> HTTP {r.status_code}: {r.text[:200]}")
        return 4
    games = r.json()
    # games is a list of {game_id, title?} — print ids only.
    ids = [g.get("game_id") for g in games if isinstance(g, dict) and g.get("game_id")]
    print(f"games available: {len(ids)}")
    for gid in ids:
        print(f"  - {gid}")

    if not ids:
        print("BLOCKER: server returned no games.")
        return 5

    # 2) open a scorecard + RESET the first game through the real env.
    gid = ids[0]
    try:
        env = Arc3LiveEnv(gid)
        frame = env.reset()
    except Arc3ApiError as e:
        print(f"BLOCKER: live reset failed for {gid}: {e}")
        return 6
    grid = frame.grid
    h = len(grid)
    w = len(grid[0]) if h else 0
    nz = sum(1 for row in grid for v in row if v != 0)
    print(f"RESET {gid}: state={frame.state.value} score={frame.score} "
          f"dims={h}x{w} non_empty={nz} available_actions={env.available_actions}")
    env.close_scorecard()
    print("CONNECTIVITY: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
