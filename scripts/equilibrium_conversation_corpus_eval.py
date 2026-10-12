"""T3c O2 corpus check: stream REAL public meetings (AMI, CC-BY-4.0) through the
/v1/conversations path (ClassifierService, in-process, no HTTP) and print
AGGREGATE COUNTS ONLY -- never text, never ids.

    PYTHONPATH=.:runners/dsl/python OZMA_NO_LLM=1 python3 scripts/equilibrium_conversation_corpus_eval.py \
        /applications/data/discord_data/testingdata/hf_samples/ami_meetings/test

Each meeting's segments are sorted by begin_time and sent as kind "meeting" in
100-turn batches (actor_ref = speaker_id, text = text, ts_ms = begin_time). The
corpus is read in place; nothing is copied or written. Measurement only: this
script reads the wire output, it decides nothing.
"""
from __future__ import annotations

import glob
import json
import os
import statistics
import sys
import time

os.environ.setdefault("OZMA_NO_LLM", "1")


def _rss_kib() -> int:
    with open("/proc/self/status") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    return -1


def _p(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(q * (len(xs) - 1)))] if xs else None


def main(src: str) -> None:
    from services.equilibrium_classifier import server
    svc = server.ClassifierService(max_conversations=4)
    files = sorted(glob.glob(os.path.join(src, "*.jsonl")))
    if not files:
        print("corpus absent: 0 files")
        return
    rss0 = _rss_kib()
    lat, close_lat, threads, rss_peak = [], [], [], []
    agg = {k: 0 for k in ("meetings", "turns", "tracked", "declared", "none", "questions",
                          "answered_q", "open_at_close", "answers", "answers_adjacent",
                          "multi_target", "addressed", "quanta", "episodes")}
    traits: dict[str, int] = {}
    dist = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        rows.sort(key=lambda r: (r["begin_time"], r["end_time"]))
        turns = [{"id": f"s{i:05d}", "actor_ref": str(r["speaker_id"]), "text": str(r["text"]),
                  "ts_ms": round(float(r["begin_time"]) * 1000)} for i, r in enumerate(rows)]
        cid = f"ami:{agg['meetings']}"
        pos = {t["id"]: i for i, t in enumerate(turns)}
        qids, answered, tids = set(), set(), set()
        for k in range(0, len(turns), 100):
            t0 = time.perf_counter()
            out = svc.conversation_turns(cid, "meeting", turns[k:k + 100])
            lat.append((time.perf_counter() - t0) * 1000)
            for t in out["turns"]:
                agg[t["basis"]] += 1
                agg["multi_target"] += len(t["responds_to"]) > 1
                agg["addressed"] += bool(t["addressees"])
                tids.add(t["thread_id"])
                if t["labels"].get("speech_act") == "question":
                    qids.add(t["id"])
                for a in t["answers"]:
                    answered.add(a)
                    agg["answers"] += 1
                    d = pos[t["id"]] - pos[a]
                    dist.append(d)
                    agg["answers_adjacent"] += d == 1
        t0 = time.perf_counter()
        fin = svc.conversation_close(cid)
        close_lat.append((time.perf_counter() - t0) * 1000)
        rss_peak.append(_rss_kib())
        agg["meetings"] += 1
        agg["turns"] += len(turns)
        agg["questions"] += len(qids)
        agg["answered_q"] += len(answered & qids)
        agg["open_at_close"] += len(fin["open_questions"])
        agg["quanta"] += len(fin["quanta"])
        agg["episodes"] += len(fin["episodes"])
        for q in fin["quanta"]:
            traits[q["trait"]] = traits.get(q["trait"], 0) + 1
        threads.append(len(tids))
    n = agg["turns"]
    print(json.dumps({
        "corpus": "AMI test split (CC-BY-4.0), aggregate counts only",
        **agg,
        "share_tracked": round(agg["tracked"] / n, 4), "share_declared": round(agg["declared"] / n, 4),
        "share_addressed": round(agg["addressed"] / n, 4),
        "answer_distance_p50": _p(dist, 0.5), "answer_distance_p95": _p(dist, 0.95),
        "threads_per_meeting": {"min": min(threads), "median": statistics.median(threads),
                                "max": max(threads)},
        "threads_per_100_turns": round(100 * sum(threads) / n, 2),
        "batch_ms": {"batches": len(lat), "p50": round(_p(lat, 0.5)), "p95": round(_p(lat, 0.95)),
                     "max": round(max(lat))},
        "close_ms": {"p50": round(_p(close_lat, 0.5)), "max": round(max(close_lat))},
        "rss_mib": {"start": round(rss0 / 1024, 1), "peak": round(max(rss_peak) / 1024, 1)},
        "quanta_by_trait": dict(sorted(traits.items())),
        "base_unchanged": tuple(svc.snap.source_revision) == svc.rev0 and svc._strong_check(),
    }, indent=1, sort_keys=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         "/applications/data/discord_data/testingdata/hf_samples/ami_meetings/test")
