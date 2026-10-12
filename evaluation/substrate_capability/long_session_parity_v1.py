#!/usr/bin/env python3
"""Long-session fix parity + speed (2026-10-10).

WorldAdapter.agent_outbound_replies_to(mid) replaced ~30 per-turn scans of
ALL agent outbound messages (agent_outbound_messages() filtered by
`mid in responds_to(reply)`). Every call site still applies its own
responds_to filter, so the old behaviour is exactly reproduced by patching
the helper back to the full scan. This runs the same single session twice
on fresh boots -- `new` (indexed) and `old` (full scan) -- and requires every
reply and turn outcome to be identical, then reports per-window seconds.

Usage: <this> [n_turns=150] [window=25] [old|new]  (new: same-arm determinism control)
Writes evaluation/reports/long_session_parity_v1_n<N>_20261010.json.
"""
import collections, json, os, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]


def run(arm, turns, w):
    import endemic_rsi_daemon_v1 as E
    from substrate.world_adapter import WorldAdapter
    import long_session_cost_v1 as L
    orig = WorldAdapter.agent_outbound_replies_to
    if os.environ.get("LSP_OFFLINE") == "1":
        # determinism control: no network I/O (topic search fails fast, the same
        # way in both arms), so a reply cannot depend on fetch timing
        from domains import topic_grounding as _tg
        def _offline(*_a, **_k):
            raise OSError("offline (long_session_parity control)")
        _tg._http_get = _offline
    if arm == "old":
        def full_scan(self, mid):
            return [r for r in self.agent_outbound_messages() if mid in self.responds_to(r)]
        WorldAdapter.agent_outbound_replies_to = full_scan
    elif arm == "newslow":
        # timing control: the NEW result, after paying the OLD scan's cost
        def slow_new(self, mid):
            [r for r in self.agent_outbound_messages() if mid in self.responds_to(r)]
            return orig(self, mid)
        WorldAdapter.agent_outbound_replies_to = slow_new
    try:
        st = E.boot(True, promote=False)
        if arm in ("old", "oldrules"):
            # the pre-fix rule bodies, from the committed seeds (HEAD)
            import subprocess
            inner = st.adapter.inner
            for seed, name in (("unanswered_gap", "note_unanswered_turn"),
                               ("comprehension_health", "note_comprehension_latency_gap")):
                head = json.loads(subprocess.run(["git", "show", f"HEAD:seeds/{seed}.json"], cwd=ROOT,
                                                 capture_output=True, text=True, check=True).stdout)
                body = next(r for r in head["rules"] if r["name"] == name)
                exported = inner.export_rules()
                for idx in sorted((i for i, r in enumerate(exported)
                                   if r.get("name") == name and r.get("active", True)), reverse=True):
                    inner.remove_rule(idx)
                inner.add_rule(body)
        acc = collections.defaultdict(float)
        L.say(st, "Hello.", acc)
        out, windows = [], []
        for start in range(0, len(turns), w):
            t0 = time.perf_counter()
            for text in turns[start:start + w]:
                status, reply = L.say(st, text, acc)
                out.append([status, reply or ""])
            windows.append(round((time.perf_counter() - t0) / len(turns[start:start + w]), 3))
            print(arm, start + w, windows[-1], flush=True)
        return out, windows
    finally:
        WorldAdapter.agent_outbound_replies_to = orig


def main():
    import long_session_cost_v1 as L
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    turns = L.turns_of(n)
    second = sys.argv[3] if len(sys.argv) > 3 else "old"     # "new": a same-arm determinism control
    first = sys.argv[4] if len(sys.argv) > 4 else "new"
    new, new_w = run(first, turns, w)
    old, old_w = run(second, turns, w)
    diffs = [{"i": i, "turn": turns[i], "new": a, "old": b} for i, (a, b) in enumerate(zip(new, old)) if a != b]
    rep = {"schema": "LongSessionParityV1", "turns": n, "window": w, "second_arm": second, "identical": not diffs,
           "differences": diffs[:20], "n_differences": len(diffs),
           "s_per_turn_new": new_w, "s_per_turn_old": old_w,
           "outcomes_new": dict(collections.Counter(x[0] for x in new))}
    off = '_offline' if os.environ.get('LSP_OFFLINE') == '1' else ''
    out = ROOT / f"evaluation/reports/long_session_parity_v1_n{n}{off}{'' if (first, second) == ('new', 'old') else '_' + first + second}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "differences"}))


if __name__ == "__main__":
    main()
