"""jabberwock_ticks_a_reading — THE READING AS A SOCIETY OF CORTICES, driven by
the AGENT'S COGNITIVE TICK.

Today's predecessor (jabberwock_produces_analysis_from_goal) seeded a Goal and
let a LINEAR dispatch chain (the 15 la_dispatch_* stages) advance one-per-firing,
pumped by hand-called `run_rules()` + `fire_reflexes()`. This script reconceives
the SAME reading as the brain reads: FIVE concurrent cortices —

    LANGUAGE   — text -> predications (the parse/situation-model spine)
    SITUATION  — entities/events/state/causal/discourse
    SOCIAL     — minds/goals/beliefs (theory of mind)
    NARRATIVE  — structure/arc/trope/theme
    EXECUTIVE  — coherence-monitoring + the report production

each a graph-resident `Cortex` bundle (seeds/reading_cortices.json) with a Reflex
that fires EVERY tick. The reading is driven by ticking the agent to a steady
state — `ad.cognitive_tick()`, the agent's whole cognitive cycle (settle the rule
fixpoint, fire the reflexes) — NOT by reaching into the engine with `run_rules()`
/ `fire_reflexes()`. The cortices process CONCURRENTLY: on each tick every cortex
advances whatever of its own inputs are ready, so LANGUAGE mints the predications,
then SITUATION builds the model off them, then NARRATIVE forms the arc, while
EXECUTIVE monitors and finally produces — the reading EMERGING from their mutual
constraint over ticks. The report read off the graph is BYTE-IDENTICAL to the
frozen linear-dispatch baseline; this reorganises the DRIVE, not the meaning.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_ticks_a_reading.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_drive as rd
from domains.reflective_faculty import _ensure_seed_chain
import jabberwock_produces_analysis_from_goal as jpafg


CROW = jpafg.CROW
MOUSE = jpafg.MOUSE


def _done_stages(ad):
    return {ad.s.node(n)["attrs"].get("name")
            for n in ad.s.nodes("AnalysisStage")
            if ad.s.node(n)["attrs"].get("status") == "done"}


def tick_a_reading(text: str, *, trace: bool = False) -> dict:
    """Seed the Goal + ingest the source, then TICK THE AGENT to a steady state.

    This is the reading path in the open: the ONLY driver call in the loop is
    `ad.cognitive_tick()` — the agent's own cognitive cycle. There is NO
    `run_rules()` and NO `fire_reflexes()` here; the reading emerges from the
    five cortices firing over ticks. The report is then read off the Claim nodes.
    """
    s, node = boot_core()
    ad = rd._LAAdapter(s)

    # SEED — the five cortices + their reflexes, the report Goal, the source, and
    # the faculty stages (each bundled into its cortex). Mechanical ingest; NO
    # order imposed here (the order is the cortices' data-dependencies).
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_driving",))
    rd._register_cortices(ad)
    ad._master["analysis_bb"] = {"text": text, "window": 2, "max_sentences": 40,
                                 "claims": [], "sections": {}}
    source = rd._ingest_source(ad, text)
    rd._mint_goal(ad, source, produce=True)
    rd._mint_stages(ad, produce=True)

    # DRIVE — tick the agent to steady state. THE WHOLE DRIVE LOOP:
    prev = set()
    last = None
    for t in range(200):
        ad.cognitive_tick()                       # <-- the agent's cognitive tick
        now_done = _done_stages(ad)
        if trace and now_done != prev:
            just = now_done - prev
            fired = sorted({rd._CORTEX_OF[name] for name in just})
            print("  tick %2d  cortices advanced: %-40s (+%s)"
                  % (ad._master["tick"], ", ".join(fired) or "-",
                     ", ".join(sorted(just))))
            prev = now_done
        snap = rd._statuses(ad)
        if snap == last:
            break
        last = snap

    report = jpafg._read_report_off_graph(s)
    return {"report": report, "claim_nodes": len(s.nodes("Claim")),
            "ticks": ad._master["tick"], "cortices": len(s.nodes("Cortex"))}


def _run(name: str, text: str) -> dict:
    print("\n" + "=" * 78)
    print("THE FABLE (%s):\n  %s" % (name, text))
    print("=" * 78)
    print("\nDRIVE = ad.cognitive_tick() to steady state — the five cortices firing:")
    out = tick_a_reading(text, trace=True)
    print("\nTHE JABBERWOCK'S ANALYSIS (read off %d Claim nodes, over %d ticks, "
          "%d cortices):\n" % (out["claim_nodes"], out["ticks"], out["cortices"]))
    print(out["report"])
    return out


def main() -> int:
    dl.warm_wordnet("en")
    _run("The Crow and the Pitcher", CROW)
    _run("The Mouse and the Stones", MOUSE)
    print("\n" + "=" * 78)
    print("The reading was driven by the AGENT'S COGNITIVE TICK — five concurrent")
    print("cortices (LANGUAGE/SITUATION/SOCIAL/NARRATIVE/EXECUTIVE), each a")
    print("graph-resident Cortex bundle firing every tick. No hand-called")
    print("run_rules/fire_reflexes; the reading settled as the cortices interacted.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
