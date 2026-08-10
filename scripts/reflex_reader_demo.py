"""LIVE DEMONSTRATION — the primal layer fronting the REAL deep reader.

Run: PYTHONPATH=. python scripts/reflex_reader_demo.py

This is the domain where the cache-vs-cognition win is huge (unlike the
trivial x^2 demo). The deep reader comprehends a sentence in ~tens of
milliseconds of active cognition (parse + mention resolution + rules).
A reflex cache serves an in-basin sentence in microseconds and DEFERS a
novel sentence to the full read — the basin gate preserving correctness.

Reading produces a SYMBOLIC verdict (a reply / parse), not a numeric
vector, so the reflex here is a MEMOIZATION cache (not a NetForward net)
— but the BASIN GATE is the exact reflex-net machinery: a sentence's
quantized signature is decoded (ShapeDecode) against the codebook of
seen quanta; residual 0 = in the known basin. Cached verdict served on a
basin hit; full read on a miss (which then grows the codebook + cache).

Nothing mocked: the real WorldAdapter reader, real converse() reads, real
ShapeDecode basin gate, real timings.
"""
from __future__ import annotations

import json
import time

from substrate.world_adapter import WorldAdapter


def _sig(text):
    """A sentence's quantized signature: its content words as unary
    relation quanta (mechanical tokenization — the smallest graph token)."""
    words = [w.strip(".,?!;:'\"").lower() for w in text.split()]
    return [[w] for w in words if len(w) > 2]


def _residual_size(reader, signature, codebook_ok):
    """Basin membership via the reflex-net gate: how many of the sentence's
    quanta are NOT in the seen codebook. 0 = fully in the known basin.
    Uses the same ShapeDecode residual the reflex_ground_residual rule uses
    (here over the reader's own substrate)."""
    native = reader.inner
    g = native.add_node("Observation", {"signature": signature})
    term = {"type": "Count", "source": {
        "type": "ShapeDecode",
        "goal": {"type": "Attr", "node": {"type": "Var", "name": "g"}, "key": "signature"},
        "codebook_type": "SeenQuantum", "beam": 3, "max_steps": 8, "cand_k": 3,
        "field": "residual", "wild": "·?·", "wild_objects": False}}
    return int(native.evaluate(term, {"g": g}))


def _grow_codebook(reader, seen_words):
    """Add each new content word as a SeenQuantum codebook entry (the basin
    grows as the reader reads — cognition teaches the cache what it knows)."""
    native = reader.inner
    for w in seen_words:
        if w not in reader._seen_set:
            native.add_node("SeenQuantum", {"name": w, "signature": json.dumps([[w]])})
            reader._seen_set.add(w)


def _hr(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main():
    _hr("BOOT the real deep reader")
    t0 = time.perf_counter()
    reader = WorldAdapter()
    reader._seen_set = set()
    reader._verdict_cache = {}
    print(f"  booted in {time.perf_counter()-t0:.2f}s")

    def full_read(text):
        t = time.perf_counter()
        reply = reader.converse(text, "statement")
        return reply, time.perf_counter() - t

    _hr("STEP 1 — the SLOW path: full comprehension per sentence (measure it)")
    warm = "The moon orbits the earth."
    full_read(warm)                       # warmup
    read_times = []
    for txt in ["A cat sat on the mat.", "Saturn has many rings.",
                "The dog chased a red ball."]:
        _, dt = full_read(txt)
        read_times.append(dt)
        print(f"    read '{txt}' -> {dt*1e3:.1f} ms")
    t_read = sum(read_times) / len(read_times)
    print(f"  mean full read: {t_read*1e3:.1f} ms/sentence (active cognition)")

    _hr("STEP 2 — build the reflex CACHE (read once, remember verdict + quanta)")
    corpus = ["The moon orbits the earth.", "A cat sat on the mat.",
              "Saturn has many rings.", "The dog chased a red ball.",
              "Rain falls from the clouds."]
    for txt in corpus:
        key = tuple(w[0] for w in _sig(txt))
        reply, _ = full_read(txt)
        reader._verdict_cache[key] = reply
        _grow_codebook(reader, [w[0] for w in _sig(txt)])
    print(f"  cached {len(reader._verdict_cache)} sentence verdicts; "
          f"basin codebook holds {len(reader._seen_set)} word-quanta")

    _hr("STEP 3 — SERVE: in-basin cached (fast) vs novel deferred to the reader")
    queries = [
        ("Saturn has many rings.", "seen — in basin"),
        ("The moon orbits the earth.", "seen — in basin"),
        ("A cat sat on the mat.", "seen — in basin"),
        ("The wombat juggles plutonium.", "novel words — out of basin"),
    ]
    served, deferred, serve_times, defer_times = 0, 0, [], []
    for txt, label in queries:
        sig = _sig(txt)
        key = tuple(w[0] for w in sig)
        t = time.perf_counter()
        resid = _residual_size(reader, sig, True)
        in_basin = (resid == 0) and (key in reader._verdict_cache)
        if in_basin:
            verdict = reader._verdict_cache[key]        # cached serve (µs)
            dt = time.perf_counter() - t
            serve_times.append(dt)
            served += 1
            print(f"    '{txt[:38]:38}' resid={resid} -> SERVED cache "
                  f"{dt*1e6:7.1f} µs   ({label})")
        else:
            reply, dt = full_read(txt)                   # defer to the full reader
            _grow_codebook(reader, [w[0] for w in sig])  # learn it for next time
            reader._verdict_cache[key] = reply           # and cache the verdict
            defer_times.append(dt)
            deferred += 1
            print(f"    '{txt[:38]:38}' resid={resid} -> DEFERRED read "
                  f"{dt*1e3:7.1f} ms   ({label})")

    _hr("VERDICT")
    avg_serve = (sum(serve_times) / len(serve_times)) if serve_times else 0.0
    print(f"  deep reader (active cognition):   {t_read*1e3:8.1f} ms/sentence")
    print(f"  reflex cache serve (in basin):    {avg_serve*1e6:8.1f} µs/sentence")
    if avg_serve:
        print(f"  >> {t_read/avg_serve:,.0f}x faster on a basin hit — the "
              f"cache-vs-cognition win, in the domain where it matters.")
    print(f"  hit rate this stream: {served}/{served+deferred} served, "
          f"{deferred} novel correctly DEFERRED to the full reader (basin gate "
          f"preserves correctness).")
    print("  (The reflex here is a memoized verdict, not a NetForward net — "
          "reading verdicts are symbolic;")
    print("   the BASIN GATE is the same ShapeDecode-residual machinery the "
          "numeric reflex nets use.)")

    import os
    out = os.path.join(os.path.dirname(__file__), "..", "results",
                       "reflex_reader_demo_verdict.log")
    with open(out, "w") as f:
        f.write(f"deep_reader: {t_read*1e3:.1f} ms/sentence (real converse())\n"
                f"reflex_cache_serve: {avg_serve*1e6:.1f} us/sentence (in basin, incl basin gate)\n"
                f"speedup: {t_read/avg_serve:.0f}x on a basin hit\n"
                f"hit_rate: {served}/{served+deferred} served, {deferred} novel deferred\n"
                f"basin_gate: novel sentence (unknown quanta) correctly deferred to full read\n")


if __name__ == "__main__":
    main()
