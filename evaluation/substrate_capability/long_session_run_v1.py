#!/usr/bin/env python3
"""One long production-path session, replies and per-window timing (2026-10-10).

Runs in WHICHEVER tree this file is in (so a git worktree of an older commit
gives the old behaviour; parity = comparing two trees' outputs). A fresh
conversation boot (self-promotion off) answers N held-out persona turns in a
single session (long_session_cost_v1.turns_of: dialogues 10-19, both seats).
With --offline, topic search's HTTP fetch fails fast in both trees, so a
reply cannot depend on network timing.

Usage: <this> N WINDOW OUT_JSON [--offline]
"""
import collections, json, os, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]


def main():
    n, w, out = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    if "--offline" in sys.argv:
        from domains import topic_grounding as tg

        def _offline(*_a, **_k):
            raise OSError("offline (long-session parity control)")
        tg._http_get = _offline
    import endemic_rsi_daemon_v1 as E
    import long_session_cost_v1 as L
    turns = L.turns_of(n)
    st = E.boot(True, promote=False)
    if "--incremental" in sys.argv:
        # engine evaluation strategy only (semi-naive matching); see
        # domains/equilibrium_classify.incremental_engine
        from domains.equilibrium_classify import incremental_engine
        incremental_engine(st.adapter.inner._native)
    acc = collections.defaultdict(float)
    L.say(st, "Hello.", acc)
    replies, windows = [], []
    for start in range(0, len(turns), w):
        t0 = time.perf_counter()
        for text in turns[start:start + w]:
            status, reply = L.say(st, text, acc)
            replies.append([status, reply or ""])
        windows.append(round((time.perf_counter() - t0) / len(turns[start:start + w]), 3))
        print(start + w, windows[-1], flush=True)
    out.write_text(json.dumps({"root": str(ROOT), "turns": turns, "replies": replies, "s_per_turn": windows,
                               "window": w, "offline": "--offline" in sys.argv}, indent=1) + "\n")


if __name__ == "__main__":
    main()
