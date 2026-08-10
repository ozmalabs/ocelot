"""Drive the ITERATED self-monitor + repair loop (domains/self_monitor.py) —
the taught ``self_monitoring_loop`` made real: produce, comprehend your OWN
output through the SAME comprehension stack, diagnose the per-slot discrepancy,
and repair from GROUNDED ALTERNATIVES, ITERATED until the round-trip converges
("say it to yourself", iterated; harder cases take more passes — order-N
analysis-by-synthesis applied to production).

This is the COMPREHENSION-BASED PERCEPTUAL-LOOP variant of the
monitoring_mechanism_debate (the forward-model variant is the same loop seen
from the other side; see the module docstring).

Setup: train the comprehension LanguageWorld on the 12-sentence bank (so the
grammar/lexicon/function-words are grounded), then run the loop from goals,
teacher disabled. The loop's pass-0 production is BARE (content words only);
markers are added only as the monitor reveals they're needed, which is what
makes the iteration visible and the passes-to-converge meaningful.

Cases (HONEST — these are constructed/found to FAIL first production):
  * wrong_role (single marker)   — a location recovered as patient because its
    preposition is missing -> repair inserts the grounded marker -> converges.
  * slot_missing (single marker) — an oblique noun with no marker -> insert.
  * multi-slot (>1 repair)       — two marked roles -> TWO passes (order-N).
  * wrong_filler (reselect)      — first grounded surface round-trips to the
    WRONG concept -> repair re-selects an alternative grounded surface.
  * UNREALIZABLE (no-progress)   — open/door not grounded -> the loop detects
    no grounded repair, STOPS, reports the residual honestly (no infinite loop,
    no faked success).
  * cross-lingual (ja)           — the same wrong_role repair via a grounded
    case PARTICLE, not an English preposition.

No-regression: the already-passing round-trips converge in 1 pass with no
repair (love-frame; cross-lingual sit-frames).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.self_monitor import SelfMonitorLoop
from scripts.language_test import training_bank


def _ground_ambiguous_alt(world: LanguageWorld) -> None:
    """Construct the wrong_filler case HONESTLY: a fresh concept ``feline``
    with two grounded surfaces — the first, ``vase``, is a REAL word for
    ANOTHER grounded concept (so producing ``feline`` as ``vase`` round-trips
    to ``vase`` = a homograph wrong_filler error); the second, ``miau``,
    resolves to ``feline``. We add the ambiguous surface as a LexEntry NODE
    only (NOT into the comprehension surface->concept cache), so the existing
    ``vase``->``vase`` comprehension mapping is untouched — the error is a
    PRODUCTION first-choice error the monitor catches, not a corrupted parser.
    The repair re-selects the grounded alternative ``miau``."""
    s = world.s
    cid = world._get_or_create_concept("feline")
    lex = world._get_or_create_lexicon("en")
    n1 = s.add_node("LexEntry", {"language": "en", "surface": "vase",
                                 "concept": "feline", "status": "confirmed",
                                 "weight": 1.0, "source": "demo_ambiguous"})
    try:
        s.add_edge(lex, "has_entry", n1, None)
        s.add_edge(n1, "entry_concept", cid, None)
    except Exception:
        pass
    # The disambiguating surface — written normally so comprehension resolves
    # miau -> feline.
    world._add_lex_entry("en", "miau", "feline")


def cases() -> list[dict]:
    return [
        {"label": "wrong_role: location->patient (single marker)",
         "language": "en", "expect": "converge",
         "goal": {"event": "sit", "agent": "cat", "location": "mat",
                  "tense": "past", "intent": "inform"}},
        {"label": "slot_missing: oblique location (single marker)",
         "language": "en", "expect": "converge",
         "goal": {"event": "break", "agent": "cat", "patient": "vase",
                  "location": "mat", "tense": "past", "intent": "inform"}},
        {"label": "multi-slot: location + recipient (>1 repair, order-N)",
         "language": "en", "expect": "converge",
         "goal": {"event": "break", "agent": "cat", "patient": "vase",
                  "recipient": "John", "location": "mat", "tense": "past",
                  "intent": "inform"}},
        {"label": "wrong_filler: homograph first surface (reselect)",
         "language": "en", "expect": "converge",
         "goal": {"event": "sit", "agent": "feline", "tense": "past",
                  "intent": "inform"}},
        {"label": "UNREALIZABLE: open/door not grounded (no-progress stop)",
         "language": "en", "expect": "fail",
         "goal": {"event": "open", "patient": "door", "intent": "request"}},
        {"label": "no-regression: love-frame (converges in 1 pass)",
         "language": "en", "expect": "converge_1pass",
         "goal": {"event": "love", "agent": "Mary", "patient": "John",
                  "tense": "present", "intent": "inform"}},
        {"label": "cross-lingual ja: wrong_role via case particle",
         "language": "ja", "expect": "converge",
         "goal": {"event": "sit", "agent": "cat", "location": "mat",
                  "tense": "past", "intent": "inform"}},
    ]


def show(loop: SelfMonitorLoop, case: dict) -> dict:
    r = loop.produce_and_repair(case["language"], case["goal"])
    print(f"\n--- {case['label']}  [{case['language']}] ---")
    print(f"  GOAL frame : {case['goal']}")
    for t in r["trace"]:
        disc = [f"{d['kind']}:{d['slot']}"
                + (f"(={d['recovered_slot']})" if d.get("recovered_slot")
                   and d["kind"] == "wrong_role" else "")
                for d in t["discrepancy"]]
        print(f"  pass {t['pass_index']}: {t['utterance']!r}")
        print(f"      recovered  : {t['recovered_frame']}")
        print(f"      discrepancy: {disc if disc else '(none)'}")
        if t["repair"]:
            print(f"      repair     : {t['repair']}  -> {t['outcome']}")
        else:
            print(f"      outcome    : {t['outcome']}")
    status = ("CONVERGED" if r["converged"]
              else ("UNREALIZABLE" if r["unrealizable"] else "STOPPED"))
    print(f"  => {status} in {r['passes']} pass(es) "
          f"(max {r['max_passes']}); utterance={r['utterance']!r}")
    if not r["converged"]:
        resid = [f"{d['kind']}:{d['slot']}" for d in r["residual"]]
        print(f"     residual discrepancy (HONEST, not faked): {resid}")
    return r


def main(argv: list[str]) -> int:
    s = _native.Substrate()

    print("=" * 72)
    print("Setup: train comprehension (LanguageWorld) on the 12-sentence bank")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    comp_log = world.run()
    comp_summ = LanguageWorld.summary(comp_log)
    print(f"  comprehension trained: {comp_summ['matched']}/{comp_summ['tasks']}"
          f" matched, {comp_summ['teacher_calls']} teacher calls")
    world.teacher_disabled = True
    # Construct the honest wrong_filler case (a homograph first surface).
    _ground_ambiguous_alt(world)

    loop = SelfMonitorLoop(world)

    print()
    print("=" * 72)
    print("Iterated monitor+repair loop — produce -> monitor -> diagnose ->")
    print("repair (grounded alternatives) -> re-produce, until converge")
    print("=" * 72)

    results = []
    for case in cases():
        r = show(loop, case)
        r["_case"] = case
        results.append(r)

    # ----- convergence summary -------------------------------------------
    converged = [r for r in results if r["converged"]]
    failed = [r for r in results if not r["converged"]]
    conv_passes = [r["passes"] for r in converged]
    avg_passes = sum(conv_passes) / len(conv_passes) if conv_passes else 0.0

    print()
    print("=" * 72)
    print("Convergence summary")
    print("=" * 72)
    print(f"  cases                  : {len(results)}")
    print(f"  converged              : {len(converged)}/{len(results)}")
    print(f"  average passes (conv.) : {avg_passes:.2f}")
    print(f"  passes per converged   : "
          f"{[(r['_case']['label'][:28], r['passes']) for r in converged]}")
    print(f"  could NOT converge     : {len(failed)} "
          f"(honest, no grounded repair):")
    for r in failed:
        resid = [f"{d['kind']}:{d['slot']}" for d in r["residual"]]
        why = "UNREALIZABLE" if r["unrealizable"] else "no-progress/deadlock"
        print(f"      - {r['_case']['label']}: {why}, residual={resid}")

    # ----- order-N observation -------------------------------------------
    print()
    print("  ORDER-N (harder cases take more passes):")
    for r in converged:
        n_marked = len([1 for k in r["_case"]["goal"]
                        if k in ("location", "recipient", "goal", "instrument",
                                 "source", "beneficiary", "topic")])
        print(f"      {r['_case']['label'][:40]:40} "
              f"marked-roles={n_marked} -> {r['passes']} pass(es)")

    # ----- trace graph nodes ---------------------------------------------
    print()
    print(f"  trace graph nodes: {len(s.nodes('ProductionGoal'))} "
          f"ProductionGoal, {len(s.nodes('MonitorPass'))} MonitorPass "
          f"(wired via has_monitor_pass — the self-correction history)")

    # ----- no-regression checks ------------------------------------------
    print()
    print("=" * 72)
    print("No-regression")
    print("=" * 72)
    ok = True

    # 1. language_test: 12/12 comprehension.
    lt_ok = comp_summ["matched"] == 12 and comp_summ["tasks"] == 12
    print(f"  comprehension round-trip (language_test): "
          f"{comp_summ['matched']}/12  {'OK' if lt_ok else 'FAIL'}")
    ok &= lt_ok

    # 2. the love-frame converges in exactly 1 pass, no repair.
    love = next(r for r in results
                if r["_case"]["label"].startswith("no-regression"))
    love_ok = love["converged"] and love["passes"] == 1
    print(f"  love-frame converges in 1 pass (no repair): "
          f"{love['passes']} pass  {'OK' if love_ok else 'FAIL'}")
    ok &= love_ok

    # 3. cross-lingual sit-frames (es/ja/zh) converge.
    print("  cross-lingual sit-frames converge:")
    xl_ok = True
    for lang in ("es", "ja", "zh"):
        g = {"event": "sit", "agent": "cat", "location": "mat",
             "intent": "inform"}
        if lang != "zh":
            g["tense"] = "past"
        rr = loop.produce_and_repair(lang, g)
        mark = "OK" if rr["converged"] else "FAIL"
        print(f"      [{lang}] {rr['utterance']!r} -> converged="
              f"{rr['converged']} in {rr['passes']} pass(es)  {mark}")
        xl_ok &= rr["converged"]
    ok &= xl_ok

    print()
    print(f"NO-REGRESSION: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
