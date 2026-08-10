"""PROVE the jabberwock DRIVES ITS OWN ASCENT — a self-directed climb.

A closed autonomous loop: the AGENT picks what to learn next (its own
order-N / groundability selector), ACQUIRES it (the unified order-N descent —
read -> ground -> compute), CLIMBS the orders, and repeats toward a GOAL, WITHOUT
a human naming the intermediate concepts. The loop SHELL (domains/self_ascent.py)
is mechanical; every SELECTION + ACQUISITION is the agent's own machinery.

What this proves:
  1. AUTONOMOUS ASCENT TO A GOAL — a goal the agent currently ABSTAINS on ("is 12
     abundant?") whose concept chain (abundant_number -> aliquot_sum ->
     {divisor_sum, minus, gt}) is initially un-held. The agent seeds the frontier
     from the goal, autonomously SELECTS + ACQUIRES each concept in a self-chosen
     order, climbs the orders, and ANSWERS — WITHOUT us naming aliquot_sum.
  2. THE SELECTOR IS THE AGENT'S — the selection order is produced by the order-N
     groundability machinery (ground the closer-to-bedrock pieces first so the
     chain bottoms out), NOT a hand-coded list. The WHY for each pick is the
     machinery's reason (its un-held-reference count).
  3. HONEST STALL AT THE BOUNDARY — a goal whose chain hits a non-acquirable
     frontier concept (cobordism_genus -> boundary_operator, a higher-order op
     with no computable realization) -> the agent DRIVES until it stalls,
     reporting stalled_at = the named wall.
  4. ORDER CLIMBS — the orders reached across the ascent (0 -> 1 -> 2).
  5. NO REGRESSION — the unified descent / order property / acquire-by-reading
     intact (gcd->12, sumsq->385, the goal answered correctly).

HONEST: the win is AUTONOMY (the agent's order-N drives its own climb), not
research-math correctness. HLE is unchanged. The frontier is the encountered-
references set; the selector is the existing order-N/groundability machinery, not
a learned policy; the goal seeds a small frontier; it drives a few number-theory
tiers, not research math.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/self_ascent_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native
from domains import grounded_representation as gr
from domains import reason
from domains import compute_grounding as cg
from domains import construction_grammar as cgr
from domains import self_ascent as sa

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# reference closed forms — the agent NEVER sees these.
def _aliquot(n):
    return sum(d for d in range(1, n) if n % d == 0)


def _abundant(n):
    return _aliquot(n) > n


def _perfect(n):
    return _aliquot(n) == n


def _fresh_caps():
    """A held tower WITHOUT the composed number-theory concepts — the agent must
    ACQUIRE them itself. divisor_sum / minus / gt / eq stay held primitives."""
    caps = dict(reason.CAPABILITIES)
    for c in ("abundant_number", "deficient_number", "aliquot_sum",
              "perfect_number", "is_perfect_number"):
        caps.pop(c, None)
    return caps


class _Conv:
    """The agent's reading world: a definition feed (the references the agent
    reads as it descends) + its constructions. The intermediate concepts are
    DEFINED here but the loop is NOT told the order to acquire them — it derives
    that itself. The goal does NOT name aliquot_sum; the agent discovers it by
    reading abundant_number's definition."""
    _definition_feed = {
        "abundant_number": "abundant_number(n) = aliquot_sum(n) > n",
        "aliquot_sum": "aliquot_sum(n) = divisor_sum(n) - n",
        "perfect_number":
            "a perfect number is a number equal to the sum of its proper divisors",
    }
    _constructions = cgr.load_constructions()


def _print_trace(res):
    print("  self-directed trace:")
    print("    step | target            | order | why-selected")
    print("    " + "-" * 70)
    for st in res["steps"]:
        order = "-" if st["order"] is None else st["order"]
        why = st["why_selected"]
        why_short = (why[:46] + "...") if len(why) > 49 else why
        mark = "OK" if st["grounded"] else ".."
        print(f"    {st['step']:>4} | {st['target']:<17} | {str(order):>5} | "
              f"[{mark}] {why_short}")
        fa = st.get("frontier_after", [])
        print(f"         frontier-after: {fa}")


def prove_autonomous_ascent():
    banner("1. AUTONOMOUS ASCENT TO A GOAL — 'is 12 abundant?'")
    print("  GOAL: is 12 abundant?  (the agent ABSTAINS — abundant_number un-held)")
    print("  The chain abundant_number -> aliquot_sum -> {divisor_sum, minus, gt}")
    print("  is initially UN-HELD. The agent seeds its frontier from the GOAL, and")
    print("  DRIVES: it discovers aliquot_sum by READING abundant_number's def,")
    print("  selects the closer-to-bedrock piece first, climbs, and answers.\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()
    conv = _Conv()

    # ABSTAIN before: the agent cannot answer (abundant_number not a capability).
    abstained = "abundant_number" not in caps
    print(f"  ABSTAIN (before): 'abundant_number' held? {not abstained}  -> abstains")

    # the goal as a comprehended frame: the question is ABOUT abundant_number. The
    # frame's content filler seeds the frontier (the coherence gap-finder). We do
    # NOT put aliquot_sum in the goal — the agent must find it.
    goal_frame = {"topic": "abundant_number", "speech_act": "question"}
    seeded = sa.seed_frontier(goal_frame)
    print(f"  GOAL frame fillers (the seeded frontier): {seeded}")
    print(f"  (note: aliquot_sum is NOT named in the goal — the agent discovers "
          f"it)\n")

    res = sa.drive_ascent(s, goal_frame, conversation=conv, capabilities=caps,
                          max_steps=12)
    _print_trace(res)

    print(f"\n  acquired (self-chosen sequence): {res['acquired']}")
    print(f"  orders climbed:                  {res['orders']}")
    print(f"  answered (goal grounds):         {res['answered']}")

    # the agent discovered aliquot_sum itself (it was never in the goal).
    discovered_aliquot = "aliquot_sum" in res["acquired"]
    # acquired bottom-up: aliquot_sum (order-1) BEFORE abundant_number (order-2).
    order_correct = (res["acquired"] == ["aliquot_sum", "abundant_number"])

    # COMPUTE the goal (was ABSTAIN): the agent now answers.
    print(f"\n  ANSWER (was ABSTAIN) — the agent drove itself to the capability:")
    answers_ok = True
    for nval, want in ((12, True), (8, False), (18, True), (10, False)):
        got = reason.solve({"abundant_number": {"n": nval}}, {},
                           capabilities=caps)
        ok = (got == want == _abundant(nval))
        answers_ok = answers_ok and ok
        print(f"    is {nval:>2} abundant? -> {str(got):>5}  (want {want}) "
              f"{'OK' if ok else 'X'}")

    overall = (abstained and res["answered"] and discovered_aliquot
               and order_correct and answers_ok)
    print(f"\n  -> the agent discovered aliquot_sum ITSELF: {discovered_aliquot}")
    print(f"  -> bottom-up self-chosen order (aliquot_sum BEFORE abundant): "
          f"{order_correct}")
    print(f"  -> autonomous ascent answered the goal: {overall}")
    return overall


def prove_selector_is_the_agents():
    banner("2. THE SELECTOR IS THE AGENT'S — order-N groundability, not a list")
    print("  The selection order is produced by the agent's machinery: rank the")
    print("  frontier by how CLOSE TO BEDROCK each concept is (how many of its")
    print("  references are NOT yet held). The closest-to-bedrock piece (all refs")
    print("  held) grounds first so the chain bottoms out — the order-N 'ground")
    print("  the lower-order pieces first' principle, read live off each def.\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()
    conv = _Conv()

    # at the START both abundant_number AND aliquot_sum are on the frontier (after
    # the goal exposes aliquot_sum). The selector must pick aliquot_sum FIRST
    # because abundant_number still has an un-held reference (aliquot_sum), while
    # aliquot_sum's references (divisor_sum, minus) are ALL held.
    frontier = ["abundant_number", "aliquot_sum"]
    assessments = sa._assess_frontier(s, frontier, conv, caps)
    print("  frontier assessment (the agent reading its own un-grounded frontier):")
    for a in assessments:
        print(f"    {a['target']:<17} refs={a['refs']}  "
              f"un-held={a['unheld_refs']}  n_unheld={a['n_unheld']}")
    chosen = sa._select(assessments)
    print(f"\n  the agent's selector picked: {chosen['target']!r}")
    print(f"  WHY (the machinery's reason): {chosen['why']}")

    # the pick is aliquot_sum (closest to bedrock), NOT abundant_number — and the
    # reason is the un-held-reference count, the order-N machinery, not a list.
    picked_bedrock_first = (chosen["target"] == "aliquot_sum"
                            and chosen["n_unheld"] == 0)
    # and abundant_number is correctly DEFERRED (it has an un-held reference).
    abundant_deferred = any(a["target"] == "abundant_number"
                            and a["n_unheld"] == 1 for a in assessments)
    print(f"\n  -> selector chose the closest-to-bedrock piece first: "
          f"{picked_bedrock_first}")
    print(f"  -> the higher-tier concept was deferred by its un-held ref count: "
          f"{abundant_deferred}")
    print(f"  -> the WHY comes from the agent's machinery (not a hand list): "
          f"{'order-N' in chosen['why'] or 'bedrock' in chosen['why']}")
    return picked_bedrock_first and abundant_deferred


def prove_honest_stall():
    banner("3. HONEST STALL AT THE NAMED BOUNDARY (a research-tier goal)")
    print("  A goal whose chain hits a non-acquirable frontier concept: a")
    print("  topology invariant defined over an operation with NO computable")
    print("  realization (boundary_operator — a higher-order op). The agent")
    print("  DRIVES as far as it can, then HONESTLY names the wall.\n")

    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()

    class ResearchConv:
        # the goal concept composes over boundary_operator; boundary_operator has
        # NO computational definition the agent can read (it is a research-tier op,
        # not an arithmetic primitive). The descent bottoms out NOWHERE computable.
        _definition_feed = {
            "cobordism_class": "cobordism_class(n) = boundary_operator(n) + 1",
        }
        _constructions = cgr.load_constructions()

    goal_frame = {"topic": "cobordism_class", "speech_act": "question"}
    res = sa.drive_ascent(s, goal_frame, conversation=ResearchConv(),
                          capabilities=caps, max_steps=10)
    _print_trace(res)
    print(f"\n  answered: {res['answered']}")
    print(f"  stalled_at (the NAMED boundary): {res['stalled_at']!r}")
    print(f"  remaining frontier: {res['frontier']}")

    # it drove (selected + tried cobordism_class), could not bottom out, and named
    # the boundary (boundary_operator) — not a crash, not a fake answer.
    stalled = (not res["answered"]
               and res["stalled_at"] == "boundary_operator")
    print(f"\n  -> drove autonomously, then honestly STALLED at the named wall "
          f"'boundary_operator': {stalled}")
    return stalled


def prove_order_climbs():
    banner("4. ORDER CLIMBS — the climb IS the order-N increment (0 -> 1 -> 2)")
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()
    conv = _Conv()
    res = sa.drive_ascent(s, {"topic": "abundant_number",
                              "speech_act": "question"},
                          conversation=conv, capabilities=caps, max_steps=12)
    print(f"  acquired: {res['acquired']}")
    print(f"  orders climbed across the ascent: {res['orders']}")
    # divisor_sum / minus / gt are the order-0 held basis; aliquot_sum is order-1
    # (an op over order-0 operands); abundant_number is order-2 (an op over the
    # order-1 aliquot_sum). The self-driven climb IS the order increment.
    climbs = (res["orders"] == [1, 2])
    print(f"\n  -> aliquot_sum order-1 (over order-0 basis), abundant_number "
          f"order-2 (over the order-1 piece): {climbs}")
    print(f"     (order-0 basis = divisor_sum/minus/gt; the agent climbed 0->1->2)")
    return climbs


def prove_no_regression():
    banner("5. NO REGRESSION — the held tower + the answered goal intact")
    ok = True
    # held arithmetic tower untouched.
    tower = [
        ("gcd 48,36", {"gcd": {"a": 48, "b": 36}}, 12),
        ("divisor_sum 28 (sumsq-anchor)", {"divisor_sum": {"of": 28}}, 56),
        ("sumsq via sum_where 1..10",
         {"sum_where": {"source": {"range_incl": {"lo": 1, "hi": 10}},
                        "var": "k",
                        "value": {"times": {"left": "k", "right": "k"}}}}, 385),
        ("factorial 6", {"factorial": {"of": 6}}, 720),
    ]
    for label, meaning, want in tower:
        got = reason.solve(meaning, {}, capabilities=reason.CAPABILITIES)
        t_ok = (got == want)
        ok = ok and t_ok
        print(f"  {label:32} -> {str(got):>6} (want {want}) "
              f"{'OK' if t_ok else 'X'}")

    # the module-level registry is unmutated by the loop (it works on a copy).
    untouched = all(c not in reason.CAPABILITIES
                    for c in ("abundant_number", "aliquot_sum",
                              "cobordism_class"))
    print(f"  module-level reason.CAPABILITIES unmutated by the ascent? "
          f"{untouched}")
    ok = ok and untouched

    # the perfect_number goal (a relational gloss) also drives to an answer — the
    # acquire-by-reading path intact for the relational form too.
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    caps = _fresh_caps()
    res = sa.drive_ascent(s, {"topic": "perfect_number",
                              "speech_act": "question"},
                          conversation=_Conv(), capabilities=caps, max_steps=8)
    perfect_ok = res["answered"]
    for nval, want in ((28, True), (12, False), (6, True)):
        got = reason.solve({"perfect_number": {"n": nval}}, {}, capabilities=caps)
        c_ok = (got == want == _perfect(nval))
        perfect_ok = perfect_ok and c_ok
        print(f"  is {nval:>2} perfect? -> {str(got):>5} (want {want}) "
              f"{'OK' if c_ok else 'X'}")
    ok = ok and perfect_ok
    print(f"\n  -> no regression: {ok}")
    return ok


def main():
    banner("THE JABBERWOCK DRIVES ITS OWN ASCENT (self-directed order-N climb)")
    print("ASSESS the frontier -> the agent SELECTS via its own machinery ->")
    print("ACQUIRE by the unified descent -> CLIMB the order -> repeat. The loop")
    print("shell is mechanical; every DECISION (which target, why) is the agent's")
    print("order-N / groundability machinery. No hand-coded targets; no LLM.")

    results = [
        ("1. autonomous ascent answers 'is 12 abundant?' (self-chosen sequence)",
         prove_autonomous_ascent()),
        ("2. the SELECTOR is the agent's (order-N groundability, not a list)",
         prove_selector_is_the_agents()),
        ("3. honest STALL at the named boundary (boundary_operator)",
         prove_honest_stall()),
        ("4. ORDER climbs (0 -> 1 -> 2, the self-driven increment)",
         prove_order_climbs()),
        ("5. no regression (held tower + answered goal intact)",
         prove_no_regression()),
    ]
    banner("SUMMARY")
    all_ok = True
    for label, ok in results:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}\n")
    print("LEARNING: the self-extension is now AUTONOMOUS — the agent's order-N")
    print("machinery DRIVES its own climb. It seeded the frontier from a goal it")
    print("abstained on, SELECTED + ACQUIRED a SEQUENCE of concepts it chose itself")
    print("(discovering aliquot_sum by reading, grounding the closer-to-bedrock")
    print("piece first), climbed the orders (0->1->2), and ANSWERED the goal —")
    print("WITHOUT per-target direction. At a research-tier goal it drove until it")
    print("STALLED and honestly named the wall (boundary_operator).")
    print("HONEST / COARSE: the win is AUTONOMY, not research-math correctness. The")
    print("frontier is the encountered-references set; the selector is the existing")
    print("order-N / groundability machinery, not a learned policy; the goal seeds")
    print("a small frontier; it drives a few number-theory tiers. HLE unchanged.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
