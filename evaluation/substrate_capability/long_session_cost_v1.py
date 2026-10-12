#!/usr/bin/env python3
"""Long-session cost probe v1: where does per-turn time go as one
conversation session grows? (open-ended plan P0 finding)

One fresh conversation boot (self-promotion off) answers N turns in a single
session, on the production path (endemic_rsi_daemon_v1's tick-loop body).
Per window of W turns it records:
  * mean wall seconds per turn, split by daemon phase (tick / comprehend /
    settle / release / host actions);
  * the engine's own per-rule cost counters (Substrate.rule_costs, reset per
    window): top rules by microseconds;
  * graph size (nodes, edges, Message nodes, active rules).

Usage: <this> [n_turns=150] [window=25] [label]
Writes evaluation/reports/long_session_cost_v1_n<N>[_label]_20261010.json.
"""
import collections, json, os, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]

PHASES = ("ingest", "tick", "comprehend", "settle", "release", "host")


def timed_cycle(st, acc):
    """endemic_rsi_daemon_v1.one_cycle, with each phase timed into `acc`."""
    import jabberwock_daemon as jd
    import substrate_rs as srs
    a = st.adapter
    with jd.AGENT_LOCK:
        t = time.perf_counter()
        budget, quantum = jd._async_cycle_budget(a)
        if quantum is None:
            a.tick()
        else:
            n = a.tick(max_steps=quantum)
            jd._record_async_cycle_consumption(a, budget, quantum, n)
        acc["tick"] += time.perf_counter() - t
        done = {}
        if st.pending_turns:
            t = time.perf_counter()
            a.comprehend()
            acc["comprehend"] += time.perf_counter() - t
            t = time.perf_counter()
            a.settle_post_comprehension_authority(list(st.pending_turns))
            acc["settle"] += time.perf_counter() - t
            t = time.perf_counter()
            for tid in list(st.pending_turns):
                reply = a.release_graph_selected_response(srs.NodeID(tid))
                status = "reply_released" if reply is not None else a.graph_turn_reply_outcome(tid)
                if status in ("expected", "unrepresented", "reply_ready"):
                    continue
                if status == "explicit_error":
                    reply = a.graph_turn_reply(tid)
                a.record_turn_outcome(tid, status)
                done[tid] = (status, reply)
                st.pending_turns.pop(tid, None)
            acc["release"] += time.perf_counter() - t
        t = time.perf_counter()
        jd._execute_host_action_requests(st)
        acc["host"] += time.perf_counter() - t
    return done


def say(st, text, acc, max_cycles=15):
    import jabberwock_daemon as jd
    with jd.AGENT_LOCK:
        t = time.perf_counter()
        tid = jd._ingest_daemon_chat_turn(st, text)
        acc["ingest"] += time.perf_counter() - t
    for _ in range(max_cycles):
        done = timed_cycle(st, acc)
        if tid in done:
            return done[tid]
    return ("timeout", None)


def turns_of(n):
    d = json.loads((ROOT / "data/corpus/persona_chat_20.json").read_text())
    out = []
    for di in range(10, 20):
        for seat in ("User 1", "User 2"):
            out += [t for spk, t in d[di]["turns"] if spk == seat]
    return out[:n]


def main():
    import endemic_rsi_daemon_v1 as E
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    label = sys.argv[3] if len(sys.argv) > 3 else ""
    out = ROOT / f"evaluation/reports/long_session_cost_v1_n{n}{('_' + label) if label else ''}_20261010.json"
    st = E.boot(True, promote=False)
    a = st.adapter
    if os.environ.get("LSC_INCREMENTAL") == "1":
        # engine evaluation strategy only (semi-naive matching)
        from domains.equilibrium_classify import incremental_engine
        incremental_engine(a.inner._native)
    say(st, "Hello.", collections.defaultdict(float))
    windows = []
    turns = turns_of(n)
    for start in range(0, len(turns), w):
        a.inner.reset_rule_costs()
        acc = collections.defaultdict(float)
        t0 = time.perf_counter()
        for text in turns[start:start + w]:
            say(st, text, acc)
        k = len(turns[start:start + w])
        wall = time.perf_counter() - t0
        costs = sorted(a.inner.rule_costs(), key=lambda r: -r[1])
        total_us = sum(r[1] for r in costs)
        win = {"turns": [start + 1, start + k], "s_per_turn": round(wall / k, 3),
               "phase_s_per_turn": {p: round(acc[p] / k, 3) for p in PHASES},
               "rule_us_per_turn": round(total_us / k),
               "top_rules": [{"rule": r[0], "us_per_turn": round(r[1] / k), "times_per_turn": round(r[2] / k, 1),
                              "progress": r[3]} for r in costs[:12]],
               "nodes": a.inner.node_count(),
               "messages": len(a.s.nodes("Message")), "edges": a.inner.edge_count(),
               "active_rules": sum(1 for r in a.inner.export_rules() if r.get("active", True))}
        windows.append(win)
        print(json.dumps({k2: v for k2, v in win.items() if k2 != "top_rules"}), flush=True)
        for r in win["top_rules"][:6]:
            print("   ", r, flush=True)
    out.write_text(json.dumps({"schema": "LongSessionCostV1", "turns": len(turns), "window": w,
                               "windows": windows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
