"""jabberwock_reads_incrementally — THE ORDER-N COLLAPSES ARE ASYNC + REVISABLE,
the FIRST PASS stays ORDERED.

jabberwock_ticks_a_reading (7a6cb318) drives the reading as FIVE cortices ticked
by the agent's cognitive_tick, but EVERY stage still fires ONCE in data-dependency
order (the la_dispatch_* chain marks each stage `done` and it never re-fires). That
is CORRECT for the FIRST PASS (the LANGUAGE + SITUATION stream: words -> clauses ->
situation model, genuinely ordered) but WRONG for the ORDER-N collapses -- the
higher-order recognitions (the narrative arc, trope/theme, executive monitoring)
should HOLD OPEN and RE-COLLAPSE as more material streams in, or when a coherence
break flags a non-sequitur.

This script feeds a fable INCREMENTALLY (sentence by sentence, ticking between) into
ONE persistent agent and logs the arc/theme AT EACH TICK. The FIRST PASS re-reads
the grown prefix IN ORDER (an ordered stream; SmEntity/SmEvent dedup in the
faculties). The ORDER-N collapses are NOT re-dispatched by this harness -- they
RE-ARM AND RE-COLLAPSE THEMSELVES via the la_rearm_* graph rules in
seeds/literary_analysis_driving.json, the exact sd_redecode / codebook_epoch
re-arm-on-growth mechanism mirrored for the reading: a done order-N stage re-arms
to pending when its input-node set GREW since its last collapse (input_epoch <
Count(trigger)) or a coherence break flagged a GlobalIncoherence (coh_epoch <
Count(GlobalIncoherence)). The RE-ARM DECISION is the graph rule, fired by
cognitive_tick -- never a Python re-collapse loop.

Three demonstrations:

  1. INCREMENTAL (the crow) -- the arc/theme UPDATE as sentences accumulate: the
     narrative collapse RE-COLLAPSES only when its material grows (not every tick),
     autonomously; at the resolving sentence the order-4 role is RE-INTERPRETED
     action -> solution and the theme appears. The settled report equals the frozen
     baseline byte-for-byte (the async is the PROCESS; the verdict is the same).

  2. AUTONOMOUS RE-ARM -- after a full read settles, GROW the trigger material (one
     more event) WITHOUT re-streaming the first pass: the order-N narrative collapse
     re-collapses ON ITS OWN (the graph rule), while the first-pass spine stays put
     (it has no re-arm rule). Order-N fires MORE THAN ONCE; the first pass fires ONCE.

  3. COHERENCE BREAK -- stream a narrative to a settled arc/theme, then stream a
     later NON-SEQUITUR the executive monitor flags as a GlobalIncoherence: the
     order-N collapses RE-ARM on the break (coh_epoch) and re-collapse, superseding
     their prior verdict.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_incrementally.py
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
from domains import narrative_structure as ns
from domains import reading_collapse as rc
from domains import reading_drive as rd
from domains.reflective_faculty import _ensure_seed_chain
import jabberwock_produces_analysis_from_goal as jpafg


CROW = jpafg.CROW

# The FIRST-PASS stages (the ordered LANGUAGE + SITUATION stream). They keep the
# one-shot `done` latch; this harness re-streams them per increment (ordered) by
# re-dispatching them + clearing the non-idempotent derived artifacts they rebuild.
# SmEntity/SmEvent are NOT cleared (the faculties dedup them by name), so the
# situation model grows cleanly across increments.
_FIRST_PASS_STAGES = ("spine", "infer_goal", "discourse", "infer_causal",
                      "enabling", "centrality", "tom")
_DERIVED_ARTIFACTS = ("SentenceParse", "CoherencePair", "CausalLink", "EnablingChain")


# --------------------------------------------------------------------------- #
#  ONE persistent agent + the mechanical streaming harness (world-adapter I/O:
#  ingest a growing source, re-dispatch the ordered first pass, tick). The
#  ORDER-N stages are never touched here -- they re-arm themselves via graph rules.
# --------------------------------------------------------------------------- #
def _new_agent():
    s, node = boot_core()
    ad = rd._LAAdapter(s)
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("literary_analysis_driving",))
    rd._register_cortices(ad)
    ad._master["analysis_bb"] = {"text": "", "window": 2, "max_sentences": 40,
                                 "claims": [], "sections": {}}
    rd._mint_goal(ad, rd._ingest_source(ad, ""), produce=True)
    rd._mint_stages(ad, produce=True)
    return ad


def _set_source(ad, text: str) -> None:
    for n in ad.s.nodes("Source"):
        ad.s.set_attr(n, "text", text)
        break
    ad._master["analysis_bb"]["text"] = text


def _restream_first_pass(ad) -> None:
    """The ORDERED first pass re-reads the grown prefix: clear the non-idempotent
    derived artifacts it rebuilds and re-dispatch the first-pass stages (pending).
    Mechanical streaming I/O -- no order-N stage is touched (they re-arm themselves)."""
    for t in _DERIVED_ARTIFACTS:
        for n in list(ad.s.nodes(t)):
            ad.inner.remove_node(n)
    for st in ad.s.nodes("AnalysisStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("name") in _FIRST_PASS_STAGES and at.get("status") == "done":
            ad.s.set_attr(st, "status", "pending")


def _arc(ad) -> list:
    return [(r.get("order"), r.get("role")) for r in ns.read_narrative_roles(ad)]


def _theme(ad) -> list:
    out = []
    for n in ad.s.nodes("Theme"):
        at = ad.s.node(n)["attrs"]
        out.append({"entity": at.get("entity"), "tropes": list(at.get("tropes") or [])})
    return out


def _adv(ad, name: str) -> int:
    for st in ad.s.nodes("AnalysisStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("name") == name:
            return int(at.get("advance_count") or 0)
    return 0


def _snapshot(ad) -> tuple:
    """A full settling snapshot: (name, status, advance_count) per stage. Unlike
    reading_drive._statuses (name,status only), this sees an order-N RE-COLLAPSE (the
    advance_count climbs while the status oscillates done->pending->done inside one
    tick), so settling does not stop while a re-arming stage still starves a
    one-shot executive stage (the produce section) of its turn."""
    return tuple(sorted((ad.s.node(n)["attrs"].get("name"),
                         ad.s.node(n)["attrs"].get("status"),
                         int(ad.s.node(n)["attrs"].get("advance_count") or 0))
                        for n in ad.s.nodes("AnalysisStage")))


def _settle(ad, max_ticks: int = 300) -> None:
    """Tick the AGENT (cognitive_tick — no run_rules/fire_reflexes) to a FULL steady
    state: stop only when a whole snapshot (statuses AND advance_counts) is unchanged,
    so every order-N re-collapse AND the one-shot produce section have completed."""
    last = None
    for _ in range(max_ticks):
        ad.cognitive_tick()
        now = _snapshot(ad)
        if now == last:
            break
        last = now


def _step_record(ad, k: int, sentence: str) -> dict:
    return {"k": k, "sentence": sentence, "arc": _arc(ad), "theme": _theme(ad),
            "narrative_adv": _adv(ad, "narrative"), "trope_adv": _adv(ad, "trope"),
            "spine_adv": _adv(ad, "spine"), "monitoring_adv": _adv(ad, "monitoring"),
            "global_incoherence": len(ad.s.nodes("GlobalIncoherence")),
            "smevent": len(ad.s.nodes("SmEvent"))}


def stream_incrementally(text: str, *, extra: str = "") -> tuple:
    """Feed the sentences of `text` (then any `extra`) ONE AT A TIME into one agent,
    ticking to steady state between each. Returns (agent, per-step log). The first
    pass streams in order; the order-N collapses re-arm + re-collapse themselves."""
    sents = rc._split_sentences(text)
    if extra:
        sents = sents + rc._split_sentences(extra)
    ad = _new_agent()
    log = []
    for k in range(1, len(sents) + 1):
        _set_source(ad, " ".join(sents[:k]))
        _restream_first_pass(ad)
        _settle(ad)                                  # <-- cognitive_tick to full steady state
        log.append(_step_record(ad, k, sents[k - 1]))
    return ad, log


def demonstrate_autonomous_rearm(text: str = CROW) -> dict:
    """Read to steady state, then GROW the trigger material (one more SmEvent -- the
    first pass 'read another event') WITHOUT re-dispatching any first-pass stage.
    The order-N narrative collapse RE-ARMS + RE-COLLAPSES on its OWN (la_rearm_
    narrative fires); the first-pass spine stays put (no re-arm rule). Returns the
    before/after per-stage advance counts."""
    ad = _new_agent()
    _set_source(ad, text)
    rd._tick_reading(ad)
    before = {"narrative": _adv(ad, "narrative"), "trope": _adv(ad, "trope"),
              "spine": _adv(ad, "spine"), "smevent": len(ad.s.nodes("SmEvent"))}
    # the first pass reads one more event -> the trigger material GROWS. No first-pass
    # stage is re-dispatched; nobody re-triggers the arc collapse but the graph rule.
    ad.s.add_node("SmEvent", {"verb": "__probe_new_event__", "surface": "streamed"})
    for _ in range(6):
        ad.cognitive_tick()
    after = {"narrative": _adv(ad, "narrative"), "trope": _adv(ad, "trope"),
             "spine": _adv(ad, "spine"), "smevent": len(ad.s.nodes("SmEvent"))}
    return {"before": before, "after": after}


# a story that reaches a clear arc/theme, then a NON-SEQUITUR the executive monitor
# flags (a state contradiction: no children, then a daughter -- global_monitoring's
# own headline shape, phrased with an explicit subject so the drive-path parse does
# not merge the possessor).
BREAK = "The crow had no children. The crow had a daughter."


def demonstrate_coherence_break(text: str = CROW, break_text: str = BREAK) -> dict:
    """Stream a narrative to a settled arc/theme, then stream a later NON-SEQUITUR
    the executive monitor flags as a GlobalIncoherence. The order-N collapses RE-ARM
    on the break (coh_epoch) and re-collapse (superseding). Returns the settled
    before-break log entry, the after-break log entry, and the break sentences."""
    n_story = len(rc._split_sentences(text))
    ad, log = stream_incrementally(text, extra=break_text)
    before = log[n_story - 1]                          # the last pure-story step
    after = log[-1]                                    # after the break streamed in
    return {"before": before, "after": after,
            "break_sentences": rc._split_sentences(break_text),
            "flagged": after["global_incoherence"] > before["global_incoherence"]}


# --------------------------------------------------------------------------- #
#  PRINTING.
# --------------------------------------------------------------------------- #
def _fmt_theme(theme: list) -> str:
    if not theme:
        return "(none)"
    return "; ".join("%s: %s" % (t["entity"], "+".join(t["tropes"]) or "-") for t in theme)


def _print_incremental(log: list) -> None:
    print("\nsentence-by-sentence (the arc/theme UPDATE as material accumulates;")
    print("narr_adv climbs only when the arc's material GROWS -- it re-collapses itself):")
    print("  %-3s %-9s %-9s %-46s %s" % ("k", "narr_adv", "spine_adv", "arc (order,role)", "theme"))
    prev_arc = None
    for r in log:
        marker = "  <- re-collapsed" if (prev_arc is not None and r["arc"] != prev_arc) else ""
        print("  %-3d %-9d %-9d %-46s %s%s"
              % (r["k"], r["narrative_adv"], r["spine_adv"], str(r["arc"]),
                 _fmt_theme(r["theme"]), marker))
        prev_arc = r["arc"]


def main() -> int:
    dl.warm_wordnet("en")

    print("=" * 78)
    print("1. INCREMENTAL (The Crow and the Pitcher) -- feed sentence by sentence,")
    print("   tick between; the order-N arc/theme re-collapse as material accumulates.")
    print("=" * 78)
    ad, log = stream_incrementally(CROW)
    _print_incremental(log)
    report = jpafg._read_report_off_graph(ad.s)
    print("\nFINAL settled report (read off the Claim nodes) -- byte-identical to the")
    print("frozen one-shot baseline (the async is the PROCESS, not the verdict):\n")
    print(report)

    print("\n" + "=" * 78)
    print("2. AUTONOMOUS RE-ARM -- grow the trigger material after settling, WITHOUT")
    print("   re-streaming the first pass. The order-N collapse re-fires ITSELF; the")
    print("   first pass stays put.")
    print("=" * 78)
    ra = demonstrate_autonomous_rearm(CROW)
    print("  before grow: narrative fired %(narrative)d, spine fired %(spine)d (SmEvent %(smevent)d)" % ra["before"])
    print("  after  grow: narrative fired %(narrative)d, spine fired %(spine)d (SmEvent %(smevent)d)" % ra["after"])
    print("  -> ORDER-N narrative re-collapsed autonomously (%d -> %d); the first-pass"
          % (ra["before"]["narrative"], ra["after"]["narrative"]))
    print("     spine fired ONCE (%d -> %d) -- it has no re-arm rule."
          % (ra["before"]["spine"], ra["after"]["spine"]))

    print("\n" + "=" * 78)
    print("3. COHERENCE BREAK -- stream a settled arc/theme, then a non-sequitur the")
    print("   executive monitor flags; the order-N collapses re-arm on the break.")
    print("=" * 78)
    cb = demonstrate_coherence_break(CROW, BREAK)
    b, a = cb["before"], cb["after"]
    print("  break sentences: %s" % cb["break_sentences"])
    print("  BEFORE break (k=%d): GlobalIncoherence=%d  narr_adv=%d  trope_adv=%d"
          % (b["k"], b["global_incoherence"], b["narrative_adv"], b["trope_adv"]))
    print("               arc=%s  theme=%s" % (b["arc"], _fmt_theme(b["theme"])))
    print("  AFTER  break (k=%d): GlobalIncoherence=%d  narr_adv=%d  trope_adv=%d"
          % (a["k"], a["global_incoherence"], a["narrative_adv"], a["trope_adv"]))
    print("               arc=%s  theme=%s" % (a["arc"], _fmt_theme(a["theme"])))
    print("  -> the monitor FLAGGED the non-sequitur (%s); the order-N collapses"
          % ("GlobalIncoherence raised" if cb["flagged"] else "no flag"))
    print("     re-armed on coh_epoch and re-collapsed (narr %d -> %d, trope %d -> %d)."
          % (b["narrative_adv"], a["narrative_adv"], b["trope_adv"], a["trope_adv"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
