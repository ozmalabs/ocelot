"""T3d / T3e scaling bench for the Equilibrium conversation sidecar (service level, no HTTP).

Prints AGGREGATES only (latencies, counts, RSS); never text. Synthetic conversations
are pseudonymous (tests/test_equilibrium_discourse_service.synthetic_window). The
optional AMI replay reads the public AMI test split in place (never copied).

  python3 scripts/equilibrium_scale_bench.py a [--lengths 100,1000,5000,10000]
  python3 scripts/equilibrium_scale_bench.py b|c|d|e|ami
"""
from __future__ import annotations

import argparse
import gc
import glob
import json
import math
import os
import statistics
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
os.environ.setdefault("OZMA_NO_LLM", "1")
AMI = "/applications/data/discord_data/testingdata/hf_samples/ami_meetings/test"


def _rss_kib() -> int:
    with open("/proc/self/status") as fh:
        return next(int(x.split()[1]) for x in fh if x.startswith("VmRSS:"))


def _load() -> str:
    with open("/proc/loadavg") as fh:
        return fh.read().split()[0]


def _svc(**kw):
    from services.equilibrium_classifier import server
    server._setup_engine()
    return server, server.ClassifierService(**kw)


def _turns(n, seed, kind="thread"):
    from test_equilibrium_discourse_service import synthetic_window
    return synthetic_window(n, seed=seed, kind=kind)[1]


def _fit(xs, ys):
    """least-squares slope of log(y) on log(x): the growth exponent"""
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    mx, my = statistics.fmean(lx), statistics.fmean(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


class _Split:
    """Per-component wall split of one conversation_ingest (measurement only):
    the retained-fork ticks in call order (S0, tracking, live L1, live L2) and the
    read-out (_emit). Stage B: there is no scratch fork any more -- the
    non-monotone families run live inside these ticks (mostly L1)."""
    PHASES = ("s0", "trk", "l1", "l2")

    def __init__(self):
        from domains import equilibrium_classify as ec
        self.ec, self.cur = ec, None
        self._tick, self._emit = ec._tick, ec._emit

        def tick(n, touched):
            t0 = time.perf_counter()
            r = self._tick(n, touched)
            if self.cur is not None:
                self.cur.append(time.perf_counter() - t0)
            return r

        def emit(*a, **kw):
            t0 = time.perf_counter()
            r = self._emit(*a, **kw)
            self.t_emit = time.perf_counter() - t0
            return r
        ec._tick, ec._emit = tick, emit

    def run(self, fn):
        self.cur, self.t_emit = [], 0.0
        t0 = time.perf_counter()
        fn()
        total = time.perf_counter() - t0
        row = dict(zip(self.PHASES, self.cur))
        row["readout"] = self.t_emit
        row["total"] = total
        self.cur = None
        return row


class _Wire:
    """Wire-size accounting of the conversation responses (measurement only): the
    0.6.0 response bytes, its quanta_delta + episodes_delta bytes, and the bytes
    the 0.5.x contract would have sent for the same batch -- the FULL rows of every
    quantum / episode the batch changed, reconstructed from the client fold
    (tests/equilibrium_delta_fold.py; equal to the saved 0.5.1 goldens, RESULTS T3e)."""

    def __init__(self):
        from equilibrium_delta_fold import DeltaFold
        self.fold = DeltaFold()

    @staticmethod
    def _n(x) -> int:
        return len(json.dumps(x, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

    def account(self, batch, out) -> dict:
        self.fold.turns(batch)
        self.fold.apply(out)
        f = self.fold
        oq = [f.quantum_row(d["quantum_id"]) for d in out["quanta_delta"] if d["op"] == "upsert"]
        oe = [f.episode_row(d["episode_id"])[0] for d in out["episodes_delta"] if d["op"] == "upsert"]
        rest = {k: v for k, v in out.items() if k not in ("quanta_delta", "episodes_delta")}
        trait = lambda d: (f.q.get(d["quantum_id"]) or {}).get("trait") or d.get("trait")
        floor = [d for d in out["quanta_delta"] if trait(d) == "interaction.floor"]
        share = [d for d in out["quanta_delta"] if trait(d) == "interaction.floor_share"]
        swap = any(d["op"] == "upsert" and d.get("counter_remove") for d in floor)
        return {"bytes": self._n(out), "floor_bytes": self._n(floor) if floor else 0,
                "share_bytes": self._n(share) if share else 0, "floor_swap": int(swap), "delta_bytes": self._n(out["quanta_delta"]) + self._n(out["episodes_delta"]),
                "old_bytes": self._n({**rest, "quanta": oq, "episodes": oe}),
                "old_rows_bytes": self._n(oq) + self._n(oe),
                "q_rows": len(out["quanta_delta"]), "e_rows": len(out["episodes_delta"])}


def bench_a(lengths):
    """(a) latency of a 100-turn batch at conversation length L (median of 3 probes),
    its split, and the wire size of each probe (0.6.0 deltas vs the 0.5.x rows)."""
    _, s = _svc(max_conversations=4)
    top = max(lengths)
    turns = _turns(top + 300, seed=4242)
    lat_at, all_lat = {}, []
    split, split_at, wire, wire_at = _Split(), {}, _Wire(), {}
    every = []
    pos = 0
    for L in sorted(lengths):
        while pos < L:
            t0 = time.perf_counter()
            out = s.conversation_turns("bench:a", "thread", turns[pos:pos + 100])
            all_lat.append((pos + 100, time.perf_counter() - t0))
            every.append(wire.account(turns[pos:pos + 100], out))
            pos += 100
        probe, rows, sizes = [], [], []
        for _ in range(3):  # three consecutive 100-turn batches at ~L
            got = []
            t0 = time.perf_counter()
            rows.append(split.run(lambda: got.append(s.conversation_turns("bench:a", "thread",
                                                                          turns[pos:pos + 100]))))
            probe.append(time.perf_counter() - t0)
            all_lat.append((pos + 100, probe[-1]))
            sizes.append(wire.account(turns[pos:pos + 100], got[0]))
            every.append(sizes[-1])
            pos += 100
        lat_at[L] = statistics.median(probe)
        split_at[L] = {k: statistics.median(r.get(k, 0.0) for r in rows) for k in rows[0]}
        wire_at[L] = {k: statistics.median(x[k] for x in sizes) for k in sizes[0]}
        print(f"(a) L={L:>6}: 100-turn batch median {lat_at[L] * 1e3:.0f} ms "
              f"(probes {', '.join(f'{x * 1e3:.0f}' for x in probe)} ms; load {_load()})", flush=True)
        print("(a)          split (median ms): " + ", ".join(
            f"{k} {v * 1e3:.1f}" for k, v in split_at[L].items()), flush=True)
        w = wire_at[L]
        print(f"(a)          floor rows (median of probes): {w['floor_bytes']} B, floor_share rows "
              f"{w['share_bytes']} B; swap probes {sum(x['floor_swap'] for x in sizes)}/3", flush=True)
        print(f"(a)          wire (median of probes): response {w['bytes'] / 1024:.1f} KiB, deltas "
              f"{w['delta_bytes'] / 1024:.1f} KiB ({w['q_rows']:.0f} quanta / {w['e_rows']:.0f} episode rows); "
              f"0.5.x would send {w['old_bytes'] / 1024:.1f} KiB (rows {w['old_rows_bytes'] / 1024:.1f} KiB)",
              flush=True)
    xs = sorted(lat_at)
    if len(xs) >= 2:
        for k in split_at[xs[0]]:
            ys = [max(split_at[x][k], 1e-4) for x in xs if x >= 1000]
            if len(ys) >= 2:
                print(f"(a) component {k}: exponent over L >= 1000 "
                      f"{_fit([x for x in xs if x >= 1000], ys):.3f}")
        big = [x for x in xs if x >= 1000]
        if len(big) >= 2:
            for k in ("bytes", "delta_bytes", "old_bytes"):
                print(f"(a) wire {k}: exponent over L >= 1000 {_fit(big, [wire_at[x][k] for x in big]):.3f}")
    sw = [x for x in every if x["floor_swap"]]
    print(f"(a) whole conversation ({len(every)} batches): response {sum(x['bytes'] for x in every) / 2**20:.2f} MiB, "
          f"floor rows {sum(x['floor_bytes'] for x in every) / 1024:.1f} KiB, floor_share rows "
          f"{sum(x['share_bytes'] for x in every) / 1024:.1f} KiB; runner-up swap batches {len(sw)}: floor rows "
          f"{sum(x['floor_bytes'] for x in sw) / 1024:.1f} KiB (max {max([x['floor_bytes'] for x in sw] or [0])} B), "
          f"responses {sum(x['bytes'] for x in sw) / 1024:.1f} KiB")
    if len(xs) >= 2:
        print(f"(a) growth exponent over L={xs}: {_fit(xs, [lat_at[x] for x in xs]):.3f} "
              f"(1.0 = linear in prefix, 0 = flat)")
        tail = [(p, y) for p, y in all_lat if p >= 1000]
        if len(tail) >= 3:
            print(f"(a) exponent over every batch with prefix >= 1000 ({len(tail)} batches): "
                  f"{_fit([p for p, _ in tail], [y for _, y in tail]):.3f}")
    t0 = time.perf_counter()
    fin = s.conversation_close("bench:a")
    print(f"(a) close at {pos} turns: {(time.perf_counter() - t0) * 1e3:.0f} ms, "
          f"{_Wire._n(fin)} bytes")


def bench_b(levels=(1, 2, 4, 8, 16), turns_per=300):
    """(b) throughput vs concurrency: K independent conversations, 100-turn batches."""
    _, s = _svc(max_conversations=64, workers=16)
    for k in levels:
        convs = [_turns(turns_per, seed=7000 + 100 * k + i) for i in range(k)]
        errs = []

        def run(i):
            try:
                for j in range(0, turns_per, 100):
                    s.conversation_turns(f"b:{k}:{i}", "thread", convs[i][j:j + 100])
            except Exception as e:  # noqa: BLE001
                errs.append(type(e).__name__)
        th = [threading.Thread(target=run, args=(i,)) for i in range(k)]
        t0 = time.perf_counter()
        [t.start() for t in th]
        [t.join() for t in th]
        dt = time.perf_counter() - t0
        for i in range(k):
            s.conversation_close(f"b:{k}:{i}", read_out=False)
        print(f"(b) concurrency {k:>2}: {k * turns_per} turns in {dt:.2f} s = "
              f"{k * turns_per / dt:.0f} turns/s (workers {s.workers}, errors {len(errs)}, load {_load()})",
              flush=True)


def bench_c(n_conv=16, per=100, rounds=3):
    """(c) /_batch with 16 conversations x 100 turns per item (service call, no HTTP)."""
    _, s = _svc(max_conversations=64, workers=16)
    convs = [_turns(per * rounds, seed=8000 + i) for i in range(n_conv)]
    for r in range(rounds):
        items = [{"conversation_id": f"c:{i}", "kind": "thread", "turns": convs[i][r * per:(r + 1) * per],
                  "close": r == rounds - 1} for i in range(n_conv)]
        t0 = time.perf_counter()
        out = s.conversation_batch(items)
        dt = time.perf_counter() - t0
        ok = sum(1 for x in out["results"] if x["ok"])
        print(f"(c) batch {r + 1}: {n_conv} x {per} turns in {dt:.2f} s = {n_conv * per / dt:.0f} turns/s, "
              f"{ok}/{n_conv} ok (load {_load()})", flush=True)


def bench_d():
    """(d) RSS per retained conversation at 1k and 10k turns."""
    _, s = _svc(max_conversations=64, workers=8)
    gc.collect()
    r0 = _rss_kib()
    convs = [_turns(1000, seed=9000 + i) for i in range(10)]
    for i, t in enumerate(convs):
        for j in range(0, 1000, 100):
            s.conversation_turns(f"d1:{i}", "thread", t[j:j + 100])
    gc.collect()
    r1 = _rss_kib()
    print(f"(d) 10 retained x 1,000 turns: RSS +{(r1 - r0) / 1024:.1f} MiB = "
          f"{(r1 - r0) / 10 / 1024:.2f} MiB per conversation (upper bound)", flush=True)
    for i in range(10):
        s.conversation_close(f"d1:{i}", read_out=False)
    gc.collect()
    r2 = _rss_kib()
    t = _turns(10_000, seed=9100)
    for j in range(0, 10_000, 100):
        s.conversation_turns("d10", "thread", t[j:j + 100])
    gc.collect()
    r3 = _rss_kib()
    print(f"(d) 1 retained x 10,000 turns: RSS +{(r3 - r2) / 1024:.1f} MiB over the post-close baseline "
          f"(allocator may reuse the freed 1k forks; upper bound)")


def bench_e(n_conv=200, per=250):
    """(e) base unchanged after 50k turns across 200 conversations (via /_batch)."""
    _, s = _svc(max_conversations=n_conv, workers=16, strong_every=50)
    convs = [_turns(per, seed=10_000 + i, kind=("thread", "meeting", "channel")[i % 3]) for i in range(n_conv)]
    t0 = time.perf_counter()
    for j in range(0, per, 100):
        for g in range(0, n_conv, 16):
            items = [{"conversation_id": f"e:{i}", "kind": ("thread", "meeting", "channel")[i % 3],
                      "turns": convs[i][j:j + 100]} for i in range(g, min(n_conv, g + 16))]
            res = s.conversation_batch(items)["results"]
            assert all(r["ok"] for r in res), [r.get("error") for r in res if not r["ok"]][:2]
    dt = time.perf_counter() - t0
    same_rev = tuple(s.snap.source_revision) == s.rev0
    strong = s._strong_check() and s.last_strong["digest"] == s.digest0
    print(f"(e) {s.turns} turns across {len(s.sessions)} retained conversations in {dt:.0f} s "
          f"({s.turns / dt:.0f} turns/s); base source_revision unchanged: {same_rev}; strong digest "
          f"== boot: {strong}; periodic strong checks passed: {s.last_strong['ok']} (load {_load()})")


def bench_ami(src=AMI, per=100):
    """Replay every AMI test meeting concurrently through /_batch (one item per meeting
    per round, 100 turns per item). Aggregates only."""
    files = sorted(glob.glob(os.path.join(src, "*.jsonl")))
    if not files:
        print("ami: corpus absent (0 files)")
        return
    _, s = _svc(max_conversations=64, workers=16)
    meetings = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        rows.sort(key=lambda r: (r["begin_time"], r["end_time"]))
        meetings.append([{"id": f"s{i:05d}", "actor_ref": str(r["speaker_id"]), "text": str(r["text"]),
                          "ts_ms": round(float(r["begin_time"]) * 1000)} for i, r in enumerate(rows)])
    lat, quanta, episodes, errors, done = [], 0, 0, 0, 0
    t0 = time.perf_counter()
    rnd = 0
    while True:
        items = [{"conversation_id": f"ami:{i}", "kind": "meeting", "turns": m[rnd * per:(rnd + 1) * per],
                  "close": (rnd + 1) * per >= len(m)}
                 for i, m in enumerate(meetings) if rnd * per < len(m)]
        if not items:
            break
        b0 = time.perf_counter()
        res = s.conversation_batch(items)["results"]
        lat.append(time.perf_counter() - b0)
        for r in res:
            if r["ok"]:
                done += len(r["turns"])
                quanta += len(r["quanta"])
                episodes += len(r["episodes"])
            else:
                errors += 1
        rnd += 1
    dt = time.perf_counter() - t0
    lat.sort()
    print(f"ami: {len(meetings)} meetings, {sum(map(len, meetings))} turns ({done} read out), "
          f"{len(lat)} batch requests, wall {dt:.1f} s = {done / dt:.0f} turns/s; per-request p50 "
          f"{statistics.median(lat):.2f} s, max {lat[-1]:.2f} s; item errors {errors}; "
          f"emitted quanta rows {quanta}, episode rows {episodes}; base unchanged "
          f"{tuple(s.snap.source_revision) == s.rev0 and s._strong_check()} (load {_load()})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["a", "b", "c", "d", "e", "ami"])
    ap.add_argument("--lengths", default="100,1000,5000,10000")
    a = ap.parse_args()
    if a.which == "a":
        bench_a([int(x) for x in a.lengths.split(",")])
    else:
        {"b": bench_b, "c": bench_c, "d": bench_d, "e": bench_e, "ami": bench_ami}[a.which]()


if __name__ == "__main__":
    main()
