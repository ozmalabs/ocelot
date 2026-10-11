#!/usr/bin/env python3
"""Null-candidate census v1, production conversation workload (2026-10-10).

Counts Argmin/Argmax firings in which some candidate's `value` evaluated to
None (a missing cost). `cmp_value` orders None below every number, so such a
candidate silently wins Argmin and loses Argmax. The instrument is the
argmin_tie module in `count` mode: behaviour unchanged, counters only.

Workload: the production daemon loop (endemic_rsi_daemon_v1: conversation
profile, ingest -> tick -> graph release, graph-scheduled host actions, self-
improvement on) over the first N User-1 turns of persona_chat_20.

Usage: <this> [n_turns] -> evaluation/reports/argmin_null_census_v1_conversation_n<N>_20261010.json
"""
import json, os, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ["OZMA_ARGMIN_UNIQUE"] = "count"
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]


def main():
    import substrate_rs
    import endemic_rsi_daemon_v1 as E
    nat = substrate_rs._native
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out = ROOT / f"evaluation/reports/argmin_null_census_v1_conversation_n{n}_20261010.json"
    if out.exists():
        raise SystemExit("refusing to overwrite")
    nat.argmin_tie_enable("count")
    t0 = time.time()
    st = E.boot(True)
    boot = nat.argmin_tie_stats()
    nat.argmin_tie_reset()
    E.say(st, "Hello.")
    replies = []
    for t in E.stream_turns("persona", n):
        status, reply = E.say(st, t)
        E.settle(st)
        replies.append(E.classify(reply))
    stats = nat.argmin_tie_stats()
    sites = sorted(nat.argmin_null_sites(), key=lambda r: -(r["mixed"] + r["all_null"]))
    rep = {"schema": "ArgminNullCensusV1", "workload": "conversation_production", "turns": n,
           "elapsed_s": round(time.time() - t0, 1), "boot_totals": boot, "turn_totals": stats,
           "null_sites": sites, "adoptions": len(st.adapter.s.nodes("Adoption")),
           "reply_classes": {c: replies.count(c) for c in set(replies)}}
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "null_sites"}))
    for r in sites[:25]:
        print(r["selector"], r["mixed"], r["wins"], r["all_null"], r["value_term"][:160])


if __name__ == "__main__":
    main()
