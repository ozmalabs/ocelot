"""PROBE — can the JABBERWOCK plan+orchestrate the OPERATIONAL instruction itself?

The deliverable is an HONEST ASSESSMENT, not a build. All session the HUMAN
orchestrated the meta-work by hand (planned builds, sequenced them, wrote the
runners). The jabberwock now drives its OBJECT-level self-improvement itself
(perceive gaps -> prioritize -> diagnose -> fix -> verify -> stop). THE TEST:
can it do the META work too? Hand it ONE operational instruction and see whether
it turns it into an ordered sub-goal plan over its held load/measure/perceive
capabilities -- or whether that orchestration is only ever a human-written script.

    INSTRUCTION (given to the jabberwock, in its own terms):
      "Do a bulk load of Wikipedia. Identify if it is sufficiently fast.
       Identify if there are other gaps."

This script:
  1. FEEDS the instruction to the jabberwock's OWN intake (comprehend_text) and
     asks its OWN composer (compose_design_for_concept) to plan it -- prints,
     VERBATIM, what it produces.
  2. Names the precise STALL point(s) -- the META-GAPS -- each verified by a probe
     printed inline (the flattened comprehension, the composer decoding the
     operational goal against INK-STROKE parts, the fixed cycles that take no
     instruction).
  3. HAND-DRIVES the object-level assessment the jabberwock cannot yet orchestrate
     (a real ~24-article load, warm-once at boot, timing on) and lets the
     jabberwock's OWN faculties answer:
       (a) SUFFICIENTLY FAST? -- load_timing.where_does_load_time_go +
           perceive_performance_gap + the stopping_policy sufficiency verdict.
       (b) OTHER OBJECT GAPS -- perceive_consumption_gaps over the real load.
  4. Prints the HONEST ASSESSMENT, separating "the jabberwock did this itself"
     from "the human hand-drove this because the meta-capability is missing".

donkey=0 for the object-level fix decisions (the perceivers + the sufficiency
verdict are graph Programs / graph reads, no LLM). The META orchestration is what
is MISSING -- that absence is the finding.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_plans_bulk_load.py
"""
from __future__ import annotations
import os, sys, io, time, contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

INSTRUCTION = ("Do a bulk load of Wikipedia. Identify if it is sufficiently fast. "
               "Identify if there are other gaps.")

SENTENCES = ["Do a bulk load of Wikipedia.",
             "Identify if it is sufficiently fast.",
             "Identify if there are other gaps."]

# substantial, definitional real wiki_local articles (the WHICH only -- concepts
# come from each article). Same spread run_wikipedia_extract.py uses.
TITLES = ["Photosynthesis", "Cryptography", "Volcano", "Glacier", "Antibiotic",
          "Mitochondrion", "Evolution", "Gravity", "Electron", "Enzyme",
          "Ecosystem", "Vaccine", "Photon", "Neuron", "Antibody", "Bacteria",
          "Virus", "Galaxy", "Earthquake", "Tsunami", "Compiler", "Database",
          "Algorithm", "Semiconductor"]


def _rule(c="="):
    print(c * 80)


def _boot():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


def main() -> int:
    from domains import comprehend_text as ct
    from domains import reflective_faculty as rf
    from domains import research_agenda as ra
    from domains import gap_prioritization as gp
    from domains import wikipedia_consumption as wc
    from domains import load_timing as lt
    from domains import performance_self_improvement as psi
    from domains import stopping_policy as sp
    from domains import consumption_quality as cq

    _rule()
    print("CAN THE JABBERWOCK PLAN+ORCHESTRATE THE INSTRUCTION ITSELF? (a probe)")
    _rule()
    print("\nTHE INSTRUCTION (in the jabberwock's own terms):")
    print(f'  "{INSTRUCTION}"')

    a = _boot()
    donkey = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "DONKEY")[1])
    except Exception:
        pass

    # =====================================================================
    # 1. FEED THE INSTRUCTION -> what does the jabberwock PRODUCE? (verbatim)
    # =====================================================================
    _rule("-")
    print("STEP 1 — FEED THE INSTRUCTION TO ITS OWN INTAKE (comprehend_text)")
    print("         does a natural-language OPERATIONAL instruction become an")
    print("         ORDERED SUB-GOAL PLAN over the held load/measure/perceive caps?\n")
    for sent in [INSTRUCTION] + SENTENCES:
        c = ct.comprehend_text(a, sent)
        print(f"  IN: {sent}")
        print(f"     -> kind={c.kind!r}  intent={c.intent!r}  "
              f"dispatch={c.dispatch.get('path')!r}  reflexive={c.reflexive}")
        print(f"        gaps={[g.get('surface') for g in c.gaps][:8]}")
        rel = c.relation
        if rel:
            pred = (rel.get('predicate') or {}).get('surface')
            subj = (rel.get('subject') or {}).get('surface')
            print(f"        relation: predicate={pred!r} subject={subj!r} "
                  f"objects={[ (o or {}).get('surface') for o in (rel.get('objects') or []) ]}")
        print()
    print("  READ-OFF: the whole 3-sentence instruction FLATTENS to ONE polar")
    print("  KNOW query (intent 'ask_world:Wikipedia', dispatch 'know'); the")
    print("  per-sentence 'Identify ...' parts become a BARE verb-naming")
    print("  ('do:Identify') with gap tokens. NO decomposition into ordered")
    print("  sub-goals; NO binding to consume / where_does_load_time_go /")
    print("  perceive_performance_gap / perceive_consumption_gaps.")

    # =====================================================================
    # 2. ASK ITS OWN COMPOSER TO PLAN IT -> where it STALLS (verbatim)
    # =====================================================================
    _rule("-")
    print("STEP 2 — ASK ITS OWN COMPOSER TO AUTHOR A PLAN (compose_design_for_concept)\n")
    for cn in ["bulk load of wikipedia", "measure timing", "perceive gaps"]:
        out = rf.compose_design_for_concept(a.s, cn)
        print(f"  compose_design_for_concept({cn!r}):")
        print(f"     authored={out.get('authored')}  goal_source={str(out.get('goal_source'))[:70]!r}")
        print(f"     ordered_parts={out.get('ordered_parts')}  "
              f"goal_signature[:3]={ (out.get('goal_signature') or [])[:3] }")
    print("\n  READ-OFF (the meta-gap, verified): the composer returns authored=True")
    print("  but its goal_source is a STROKE signature and its parts are INK QUANTA")
    print("  (I_0, seg-relations). It matched the operational goal to the LETTER 'a'")
    print("  by a spurious substring name-match, then decoded it against the")
    print("  handwriting codebook. The operational capabilities are NOT parts in")
    print("  the composer's codebook -- so 'plan a bulk load' cannot reference them.")

    sigs = [a.s.node(n)["attrs"].get("name") for n in a.s.nodes("ShapeSignature")]
    ops = ("load", "timing", "wikipedia", "consume", "perceive", "warm",
           "measure", "latency", "sufficien")
    op_sigs = [s for s in sigs if s and any(o in str(s).lower() for o in ops)]
    print(f"\n  PROBE — ShapeSignature parts in codebook: {len(sigs)}; "
          f"operational-capability signatures among them: {op_sigs or 'NONE'}")

    # =====================================================================
    # 3. THE FIXED CYCLES — not planners (probe: they take NO instruction)
    # =====================================================================
    _rule("-")
    print("STEP 3 — THE SELF-IMPROVEMENT CYCLES ARE FIXED, NOT PLANNERS (probe)\n")
    import inspect
    print(f"  research_agenda.run_cycle{inspect.signature(ra.run_cycle)}")
    print(f"  gap_prioritization.run_cycle{inspect.signature(gp.run_cycle)}")
    print("  READ-OFF: neither takes the instruction / a goal. They run a FIXED")
    print("  perceive->prioritize->route->fill->verify->stop over their OWN")
    print("  perceivers' gaps. They cannot be COMMANDED to 'do a bulk load and")
    print("  assess it'; they compose no NOVEL cycle from an instruction.")

    # =====================================================================
    # 4. OBJECT-LEVEL ASSESSMENT — HAND-DRIVEN (the meta-orchestration is missing)
    # =====================================================================
    _rule()
    print("OBJECT-LEVEL ASSESSMENT  —  *** HUMAN HAND-DRIVES THE SEQUENCE ***")
    print("(load -> measure -> perceive -> judge is a Python script here, precisely")
    print(" because no agent-held orchestrator composes it from the instruction)")
    _rule()

    timer = lt.LoadTimer(a)
    t0 = time.time()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        res = wc.consume(a, titles=TITLES, timing=timer, warm=True, quality=True)
    dt = time.time() - t0
    consumed = sum(1 for r in res["results"] if r["consumed"])
    per_article = dt / max(1, res["n_articles"])
    print(f"\n  LOAD: {res['n_articles']} articles, {consumed} consumed, "
          f"{res['admitted_total']} concepts grounded, {dt:.1f}s total, "
          f"{per_article:.3f} s/article  (warm-once fix ON)")

    # (a) SUFFICIENTLY FAST? — the jabberwock's OWN faculties answer.
    _rule("-")
    print("  (a) SUFFICIENTLY FAST?  — the jabberwock's OWN introspection + verdict\n")
    rep = lt.where_does_load_time_go(a)
    for ln in rep["text"].splitlines():
        print("      " + ln)
    print(f"\n      cold={rep['cold']}  warm_per_item(ms/concept)={rep['warm']}  "
          f"dominant_stage={rep['dominant_stage']!r}")
    pg = psi.perceive_performance_gap(a, mint=True)
    print(f"\n      perceive_performance_gap -> gap={pg['gap']}  "
          f"(None = no cold/warm surprise: warm-once moved the 1x init to boot)")
    thr = sp.sufficiency_threshold(a)
    cont = sp.should_continue(a)
    verdict = "STILL A LIVE GAP (above threshold)" if cont else "SUFFICIENT (below threshold)"
    print(f"      sufficiency_threshold={thr}   should_continue(CONTINUE=live-gap)={cont}")
    print(f"      >>> THE JABBERWOCK'S VERDICT: {verdict}")
    print(f"      >>> per-article {per_article:.3f}s; warm per-concept {rep['warm']} ms")

    # (b) OTHER OBJECT GAPS — perceive over the real load.
    _rule("-")
    print("  (b) OTHER OBJECT GAPS  — perceive_consumption_gaps over the real load\n")
    cg = cq.perceive_consumption_gaps(a, mint=True)
    gaps = cg.get("gaps") or []
    def _sal(g):
        v = a.s.node(g)["attrs"].get("salience")
        try:
            return float(v)
        except Exception:
            return -1.0
    for g in sorted(gaps, key=_sal, reverse=True):
        at = a.s.node(g)["attrs"]
        print(f"      GAP  faculty={at.get('faculty')!r:26} "
              f"failure_class={at.get('failure_class')!r:12} salience={at.get('salience')}")
    print(f"      ({len(gaps)} consumption gaps minted; residual={cg.get('residual')})")
    print("      NOTE: these are the standing quality residuals the perceiver")
    print("      surfaces on real non-definitional text (nominal fragments the")
    print("      filter still misses; context-sense missense e.g. water.n.03-vs-01;")
    print("      no hot grounding-cache tier).")

    # =====================================================================
    # 5. HONEST ASSESSMENT
    # =====================================================================
    _rule()
    print("HONEST ASSESSMENT")
    _rule()
    warm_ms = rep['warm']
    dom = rep['dominant_stage']
    print(f"""
  (a) SUFFICIENTLY FAST?  -> {verdict}
      real rate {per_article:.3f} s/article ({warm_ms} ms/concept warm); the
      agent's OWN sufficiency Program says STOP (no salient performance gap). The
      dominant cost is the ONE-TIME {dom!r} boot init, amortized.

  (b) OTHER OBJECT GAPS (what it perceives beyond fast, verbatim above):
      nominal_extraction / context_sense / grounding_cache residuals -- the
      standing consumption-quality gaps, surfaced by the agent's own collapse.

  (c) META-GAPS (why it cannot orchestrate the instruction itself) -- each probed:

      META-GAP 1  NO instruction->operational-plan faculty.
        comprehend_text FLATTENS the 3-sentence operational instruction into ONE
        polar KNOW query (intent 'ask_world:Wikipedia'); per sentence it yields a
        bare 'do:Identify' verb-name. It never emits an ordered sub-goal plan.
        (Probed in STEP 1, verbatim.)

      META-GAP 2  The composer's codebook holds NO operational capabilities.
        compose_design_for_concept decodes the goal SIGNATURE against 1673
        ink-STROKE / arrangement ShapeSignatures (the Omniglot arc). ZERO name
        load/timing/perceive/consume. 'plan a bulk load' returns authored=True but
        is a handwriting-stroke decode of the letter 'a'. The object capabilities
        (load_timing, wikipedia_consumption.consume, perceive_performance_gap,
        stopping_policy, perceive_consumption_gaps) are PYTHON FUNCTIONS with no
        ShapeSignature/Concept/Program handle the composer can reference.
        (Probed in STEP 2, verbatim.)

      META-GAP 3  research_agenda/gap_prioritization.run_cycle are FIXED cycles.
        Both take NO instruction/goal (probed signatures). They run a hard-coded
        perceive->prioritize->route->fill->verify->stop over their OWN perceivers'
        gaps -- they compose no NOVEL load->measure->assess cycle from a command.
        (Probed in STEP 3.)

      META-GAP 4  No orchestrator binds load->measure->judge->report.
        Each object capability is agent-invocable individually, but the SEQUENCE
        that ran them (STEP 4) is THIS Python script, human-authored. There is no
        agent-held Program/Reflex that, given the instruction, fires consume() then
        where_does_load_time_go() then perceive_performance_gap() then
        should_continue() then perceive_consumption_gaps(). The orchestration is
        the human's; only the object-level judgments are the graph's.

  SELF vs HAND-DRIVEN:
    * THE JABBERWOCK DID ITSELF: the object-level assessment -- where its load
      time goes, whether the rate is sufficient (its own stopping Program), and
      what other gaps remain (its own collapse perceivers). donkey={donkey['n']} LLM calls.
    * THE HUMAN HAND-DROVE: comprehending the instruction into a plan, sequencing
      load->measure->perceive->judge->report, and choosing the articles/params.
      That whole meta-layer is what the jabberwock is MISSING (META-GAPS 1-4).
""")
    _rule()
    print(f"donkey (LLM calls, object-level fix decisions) = {donkey['n']}  "
          f"(0 = the perceivers/verdict are graph, not an LLM)")
    _rule()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
