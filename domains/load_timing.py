"""load_timing — LOAD LATENCY AS A VISIBLE PERCEPTION the jabberwock HOLDS.

THE PROBLEM (stated by the user): a prior build reached for a CACHE to make
Wikipedia loading faster. That was a BLIND guess — the jabberwock could not SEE
where load time actually went, so it optimized a cost it couldn't measure. The
cache was context-keyed (2.6% hit-rate) and did nothing, because the real cost
was NOT a per-item cost a cache could amortize. "If the timing isn't visible to
it, there is our problem."

THE DIAGNOSIS (profiled, reconfirmed): a load breaks down as
read_source ~13% + extract ~2% + GROUND ~86%. Ground = sense-scoring
(dictionary_lexicon._enumerate_features: WordNet synset enumeration + Lesk
overlap). The FIRST `_enumerate_features` call is ~1400ms — a ONE-TIME WordNet
cold-load (NLTK lazily loads the whole corpus on first synset access). WARM
calls are ~0.4ms/concept. So the apparent "per-article bottleneck" was a
MEASUREMENT ARTIFACT: one ~1.4s init amortized over a small batch LOOKS like
per-article cost. There is NO per-concept bottleneck to cache; the cost is
one-time init. The fix is trivial once VISIBLE: warm WordNet once, up front.

THE FIX, IN TWO PARTS:
  1. VISIBILITY (this module) — instrument each load stage (read_source /
     extract_microtheory / ground_lexeme, and the COLD-vs-WARM split within
     ground) and surface each stage's latency INTO THE GRAPH as a
     `LatencyObservation` node the agent HOLDS and can INTROSPECT. The clock read
     is host-I/O (an admissible sensor, like a mic or a pixel); surfacing it as a
     graph perception and READING it to find the bottleneck is the agent's.
     `where_does_load_time_go(agent)` reads the agent's own LatencyObservations
     and reports the dominant stage + the cold/warm split — the jabberwock
     answering "where does my load time go?" in its own terms.
  2. WARM-ONCE (dictionary_lexicon.warm_wordnet, driven by
     wikipedia_consumption.consume) — pay the one-time init at boot so article 1
     is WARM. NOT a cache. Nothing memoized; the corpus is simply resident.

WORLD-ADAPTER DISCIPLINE (CLAUDE.md). This module owns NO agent decision. The
LoadTimer is a mechanical stopwatch (host I/O) that WRITES graph perception nodes
(`substrate.add_node` / `add_edge`) — the same admissible move BlockObs /
CapabilityGap make (spatial_sense, self_capability_collapse). The introspection
is a mechanical READ over those nodes: it aggregates the recorded latencies and
reports which stage dominates. No `if/else` decides what to LOAD or how — it only
measures and surfaces. donkey=0: a clock, arithmetic, and graph writes.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Optional


def _resolve(agent):
    """(substrate, agent_root_node) — the same duck-typing the other perception
    plugs use (self_capability_collapse._resolve, spatial_sense)."""
    sub = getattr(agent, "s", agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        try:
            for n in sub.nodes("Agent"):
                ag_node = n
                break
        except Exception:
            ag_node = None
    return sub, ag_node


# stages of a load, coarse→fine. The sense/ground stage is the one that carries
# the one-time WordNet init (cold) vs steady state (warm).
STAGES = ("read_source", "extract_microtheory", "ground_lexeme")
# the stage whose COLD (first) occurrence pays the WordNet corpus load.
GROUND_STAGE = "ground_lexeme"


class LoadTimer:
    """A stopwatch that surfaces each timed stage as a `LatencyObservation` graph
    node wired `agent -perceives_latency-> obs`. The jabberwock then HOLDS its own
    load timing as an introspectable perception (not a print the human sees and it
    doesn't). Mechanical host I/O — a sensor that writes to the graph.

    Usage (in the world adapter):

        timer = LoadTimer(agent)
        with timer.stage("read_source", article=title):
            src = read(...)
        with timer.stage("ground_lexeme", article=title, n_items=len(cs)):
            for c in cs: ground(c)          # phase auto-detected cold/warm

    A `LoadTimer(None)` (or the NULL_TIMER singleton) is a no-op: it records
    nothing and mints no node, so an un-instrumented / default call is
    byte-identical."""

    def __init__(self, agent):
        self.agent = agent
        self.records: list[dict] = []          # a cheap host-side mirror for tests

    @contextmanager
    def stage(self, name: str, *, article: Optional[str] = None,
              n_items: int = 1, phase: Optional[str] = None):
        # capture WARM state at ENTER: the ground stage is COLD iff WordNet is not
        # yet loaded when the stage begins (its first synset access pays the init).
        warm_at_enter = _wordnet_warm()
        t0 = time.perf_counter()
        try:
            yield self
        finally:
            ms = (time.perf_counter() - t0) * 1000.0
            ph = phase
            if ph is None and name == GROUND_STAGE:
                ph = "warm" if warm_at_enter else "cold"
            self.record(name, ms, article=article, n_items=n_items, phase=ph)

    def record(self, stage: str, ms: float, *, article: Optional[str] = None,
               n_items: int = 1, phase: Optional[str] = None) -> Any:
        """Surface ONE stage latency as a graph perception the agent holds.
        Mirrors self_capability_collapse.mint_capability_gap: an observation
        relation-system + a `description` + a `perceives_latency` edge from the
        agent root. Returns the node id (or None for the NULL timer)."""
        n_items = max(int(n_items or 1), 1)
        per = ms / n_items
        rec = {"stage": stage, "ms": round(ms, 3), "phase": phase,
               "n_items": n_items, "ms_per_item": round(per, 4), "article": article}
        self.records.append(rec)
        if self.agent is None:
            return None
        sub, ag_node = _resolve(self.agent)
        desc = (f"load stage {stage!r} took {ms:.1f} ms"
                + (f" over {n_items} concept(s) = {per:.3f} ms/concept" if n_items > 1 else "")
                + (f" [{phase}]" if phase else "")
                + (f" on {article!r}" if article else ""))
        try:
            nid = sub.add_node("LatencyObservation", {
                "stage": stage,
                "ms": round(ms, 3),
                "phase": phase,
                "n_items": n_items,
                "ms_per_item": round(per, 4),
                "article": article,
                # the observation relation-system (the shape the agent's perception
                # readers consume): latency localized to a stage, phase-tagged.
                "observation": [
                    ["latency", stage, "ms"],
                    ["phase", stage, phase or "steady"],
                    ["cost_per_item", stage, round(per, 4)],
                ],
                "description": desc,
            })
        except Exception:
            return None
        if ag_node is not None:
            try:
                sub.add_edge(ag_node, "perceives_latency", nid)
            except Exception:
                pass
        return nid


class _NullTimer(LoadTimer):
    """A LoadTimer that measures nothing and mints no node — the default, so an
    un-instrumented load stays byte-identical."""

    def __init__(self):
        super().__init__(None)

    @contextmanager
    def stage(self, *a, **k):
        yield self

    def record(self, *a, **k):
        return None


NULL_TIMER = _NullTimer()


def _wordnet_warm() -> bool:
    try:
        from domains import dictionary_lexicon as dl
        return dl.is_wordnet_warm()
    except Exception:
        return False


# =========================================================================== #
#  INTROSPECTION — the jabberwock reads its OWN LatencyObservations and answers
#  "where does my load time go?". A mechanical READ + aggregate, no decision.
# =========================================================================== #

def latency_observations(agent) -> list[dict]:
    """Read back every LatencyObservation the agent HOLDS (its perceived load
    timings), newest-graph-order. Mechanical graph query."""
    sub, _ = _resolve(agent)
    out = []
    try:
        for n in sub.nodes("LatencyObservation"):
            at = dict(sub.node(n)["attrs"])
            at["_id"] = n
            out.append(at)
    except Exception:
        pass
    return out


def where_does_load_time_go(agent) -> dict:
    """THE INTROSPECTION: the jabberwock answers, from its own perceptions, where
    its load time goes. Reads its LatencyObservations, aggregates per stage, finds
    the DOMINANT stage, and separates the COLD (one-time WordNet init) from the
    WARM (steady-state per-concept) cost of the ground stage.

    Returns {observations, by_stage, dominant_stage, dominant_pct, cold, warm,
    verdict, text}. The `verdict`/`text` is the agent's answer in words — the
    thing to print verbatim. This is a READ, no branch decides what to load."""
    obs = latency_observations(agent)
    by_stage: dict[str, dict] = {}
    total = 0.0
    for o in obs:
        st = o.get("stage") or "?"
        ms = float(o.get("ms") or 0.0)
        total += ms
        b = by_stage.setdefault(st, {"stage": st, "total_ms": 0.0, "n": 0,
                                      "items": 0, "cold_ms": None,
                                      "warm_ms": [], "warm_per_item": []})
        b["total_ms"] += ms
        b["n"] += 1
        b["items"] += int(o.get("n_items") or 1)
        if o.get("phase") == "cold":
            # the first (cold) occurrence of the stage — the one-time init.
            b["cold_ms"] = ms if b["cold_ms"] is None else max(b["cold_ms"], ms)
        else:
            b["warm_ms"].append(ms)
            b["warm_per_item"].append(float(o.get("ms_per_item") or 0.0))

    for b in by_stage.values():
        b["total_ms"] = round(b["total_ms"], 3)
        b["pct"] = round(100.0 * b["total_ms"] / total, 1) if total else 0.0
        b["warm_ms_mean"] = round(sum(b["warm_ms"]) / len(b["warm_ms"]), 3) if b["warm_ms"] else None
        b["warm_per_item_mean"] = round(
            sum(b["warm_per_item"]) / len(b["warm_per_item"]), 4) if b["warm_per_item"] else None
        # a per-item warm rate; keep the raw lists small in the return
        b["warm_ms"] = [round(x, 3) for x in b["warm_ms"]]
        b["warm_per_item"] = [round(x, 4) for x in b["warm_per_item"]]

    dominant = max(by_stage.values(), key=lambda b: b["total_ms"], default=None)
    g = by_stage.get(GROUND_STAGE)
    cold_ms = g["cold_ms"] if g else None
    warm_per = g["warm_per_item_mean"] if g else None

    if not obs:
        text = ("no load timing perceived yet — I hold no LatencyObservations. "
                "Run a load with a LoadTimer first.")
        return {"observations": obs, "by_stage": by_stage, "dominant_stage": None,
                "dominant_pct": 0.0, "cold": None, "warm": None,
                "verdict": "no_perception", "text": text}

    lines = ["where does my load time go? — reading my LatencyObservations:"]
    for b in sorted(by_stage.values(), key=lambda b: -b["total_ms"]):
        lines.append(f"  · {b['stage']:<20} {b['total_ms']:>9.1f} ms  ({b['pct']:>4.1f}% of load)")
    if dominant is not None:
        lines.append(f"the DOMINANT stage is {dominant['stage']!r} "
                     f"({dominant['pct']:.1f}% of load time).")
    if cold_ms is not None and warm_per is not None:
        lines.append(
            f"and it SPLITS cold-vs-warm: the FIRST ({GROUND_STAGE}) call cost "
            f"{cold_ms:.1f} ms — a ONE-TIME WordNet corpus init, NOT a per-concept "
            f"cost. WARM concepts after it cost ~{warm_per:.3f} ms each. So the "
            f"'bottleneck' is one-time init amortized over the batch, not a "
            f"per-item cost. Warm WordNet once at boot and it disappears.")
    elif cold_ms is not None:
        lines.append(f"the FIRST {GROUND_STAGE} call cost {cold_ms:.1f} ms "
                     f"(one-time WordNet init).")
    text = "\n".join(lines)
    verdict = dominant["stage"] if dominant else "unknown"
    return {"observations": obs, "by_stage": by_stage,
            "dominant_stage": dominant["stage"] if dominant else None,
            "dominant_pct": dominant["pct"] if dominant else 0.0,
            "cold": cold_ms, "warm": warm_per, "verdict": verdict, "text": text}


__all__ = [
    "LoadTimer", "NULL_TIMER", "STAGES", "GROUND_STAGE",
    "latency_observations", "where_does_load_time_go",
]
