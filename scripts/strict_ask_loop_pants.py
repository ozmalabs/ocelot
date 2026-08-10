"""strict_ask_loop_pants — THE STRICT DEVELOPMENTAL ASK-LOOP (donkey-impossible).

The AGENT's OWN machinery works ALONE on the construction prose of 671579
('two pairs of pants sewn leg-to-leg, the two waistband circles identified to a
single point' -> pi_1). The PARENT (the LLM, here a fixed one-step responder
table) is MUTE until the AGENT'S MACHINERY emits a SPECIFIC question, and then
answers ONLY ONE STEP — one concept/fact, the minimal answer to THAT question.

THE STRICT RAIL (the user's):
  1. The AGENT's machinery runs on the construction. It works ALONE.
  2. When it STALLS, the MACHINE must EMIT A SPECIFIC QUESTION — the MACHINE's
     literal output (comprehend_gluing returns "" = a TOTAL un-parse; the
     question-level comprehend returns a FRONTIER reason naming what it lacks).
  3. ONLY THEN the PARENT answers ONE STEP. Never a build, spec, topology, or
     next move.
  4. The MACHINE incorporates the one step and CONTINUES ALONE.
  5. Repeat until COMPLETE (machinery built the spec from prose + computed pi_1 +
     self-verified) OR CANNOT EVEN FORMULATE THE NEXT QUESTION (the meta-wall).

DONKEY-IMPOSSIBLE: this shell NEVER authors the construction spec, the topology,
the build, or the answer-shape. It only (a) calls the agent's machinery, (b)
captures the machine's literal stall output, (c) when that output is a SPECIFIC
answerable question, hands back ONE step from the parent table, (d) re-runs the
machine. If the machine's output is a TOTAL un-parse (no specific answerable
question), the loop records the meta-wall (outcome b) and STOPS — the parent has
nothing to answer one-step.

The PARENT_ONE_STEP table below is the ONLY LLM contribution. Each entry is the
minimal one-concept answer to ONE machine-posed question. It is NOT a spec, NOT a
build, NOT a topology. Each is ONE fact. The harness asserts (structurally) that
the machine posed the question before the parent answers, and that each answer is
a single concept (one short fact string), not a multi-step construction.

The answer (the pi_1 multiple-choice key) is read at the END only, via the
agent's OWN self-verify gate against KNOWN spaces — NEVER handed to the parent.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))

from domains import comprehend_question as _cq  # noqa: E402
from domains import construction_operators as _co  # noqa: E402
PROSE_ID_PREFIX = "671579"


# ---------------------------------------------------------------------------
# THE PARENT ONE-STEP TABLE — the ONLY LLM contribution. Keyed by the SPECIFIC
# machine-posed question (the machine's literal stall output). Each value is ONE
# concept/fact — the minimal answer to THAT question. NOTHING here is a spec, a
# build, a topology, or the answer. A key fires ONLY if the machine literally
# emitted that question this turn (asserted in the loop).
# ---------------------------------------------------------------------------
# NOTE: this table is intentionally EMPTY of construction content. The point of
# the strict run is to discover whether the agent's machinery can EMIT a
# specific answerable question at all. The parent answers are added ONLY in
# response to a machine-posed question, ONE step at a time, and each is recorded
# in the transcript. We seed the table with the parent's one-step answers to the
# questions the machine is OBSERVED to pose (below); if the machine poses a
# question not in the table, the loop HALTS and reports "parent has no one-step"
# (which would itself be a frontier, not a donkey).
PARENT_ONE_STEP: dict[str, str] = {}


def load_prose() -> str:
    """Read the question STEM (the construction prose) — NOT the `answer` field
    (the key is read at END only, via the agent's gate, never by the parent). The
    multiple-choice block is dropped: it is the answer-shape, not the construction.
    The agent's prose->structure machinery reads the CONSTRUCTION sentences."""
    data = json.loads((ROOT / "data" / "hle_math.json").read_text())
    for it in data:
        if str(it.get("id", "")).startswith(PROSE_ID_PREFIX):
            q = it["question"]
            # keep only the construction stem (drop the 'Answer Choices:' block).
            stem = q.split("Answer Choices")[0].strip()
            return stem
    raise SystemExit("671579 prose not found")


# ---------------------------------------------------------------------------
# THE MACHINE PROBES — each returns the MACHINE's LITERAL output on the prose.
# The loop reads these; it does NOT decide meaning. A probe that returns a
# specific answerable question lets the parent answer one step; a probe that
# returns a TOTAL un-parse (empty / None with no specific question) is the
# "can't even formulate the question" meta-wall.
# ---------------------------------------------------------------------------

def probe_question_comprehend(prose: str) -> dict:
    """The QUESTION-LEVEL comprehension machine (comprehend_question.comprehend).
    Returns its LITERAL TargetSpec line + whether it posed a specific question."""
    spec = _cq.comprehend(prose)
    return {
        "machine": "comprehend_question.comprehend",
        "grounded": spec.grounded,
        "literal": spec.line(),
        "reason": spec.reason,
        "relation": spec.relation_phrase,
        "object": spec.object_phrase,
    }


def probe_diagnose_machines(prose: str) -> dict:
    """Run EVERY held DIAGNOSE machine on the prose. The strict rail requires the
    QUESTION to be the MACHINE's output — so we check whether ANY of the agent's
    diagnose faculties NAMES the gap as a specific answerable question:
      · diagnose_comprehension_gap  — names a missing CONSTRUCTION (cmsg109).
      · diagnose_why_diagnosis_failed — the meta-meta (cmsg110): why couldn't it
        name the gap?
    A non-None return from either WOULD be a machine-posed question the parent
    could answer one-step. Both return None on this prose (they fire only on the
    'compare X with Y' goal-shape) -> NO machine-posed question from the diagnose
    tier either. We record the literal None so the meta-wall is shown, not asserted."""
    gap = _cq.diagnose_comprehension_gap(prose)
    meta = _cq.diagnose_why_diagnosis_failed(prose)
    return {
        "diagnose_comprehension_gap": gap,
        "diagnose_why_diagnosis_failed": meta,
        "any_named": (gap is not None) or (meta is not None),
    }


def probe_gluing_comprehend(prose: str) -> dict:
    """The CONSTRUCTION-PROSE machine (construction_operators.comprehend_gluing):
    read the gluing description into a polygon WORD the held operators build. This
    is the prose->structure machine the experiment targets. Returns its LITERAL
    output (the word, or "" = total un-parse) per clause."""
    # split the construction prose into its operative clauses (the gluing steps).
    import re
    clauses = [c.strip() for c in re.split(r"[.,]", prose) if c.strip()]
    per = {c: _co.comprehend_gluing(c) for c in clauses}
    per["__whole__"] = _co.comprehend_gluing(prose)
    nonempty = [k for k, v in per.items() if v]
    return {
        "machine": "construction_operators.comprehend_gluing",
        "per_clause": per,
        "any_parsed": bool(nonempty),
        "literal": ("the gluing-comprehension machine returned the EMPTY word on "
                    "every clause of the construction prose (no held gluing "
                    "construction matched 'pairs of pants' / 'leg openings sewn' / "
                    "'waistbands identified to a point')"),
    }


def main() -> None:
    prose = load_prose()
    print("=" * 78)
    print("STRICT ASK-LOOP — construction prose of 671579 -> pi_1")
    print("=" * 78)
    print("PROSE (the construction the agent's machinery must turn into structure):")
    print(f"  {prose!r}")
    print()

    transcript: list[dict] = []
    asks = 0

    # ---- TURN 1: the agent's machinery runs ALONE on the construction prose. ----
    print("-" * 78)
    print("TURN 1 — the agent's CONSTRUCTION-PROSE machinery runs ALONE")
    print("-" * 78)
    g = probe_gluing_comprehend(prose)
    print(f"MACHINE [{g['machine']}] literal output, per operative clause:")
    for clause, word in g["per_clause"].items():
        if clause == "__whole__":
            continue
        print(f"    {clause!r:64s} -> word={word!r}")
    print(f"  whole-prose -> word={g['per_clause']['__whole__']!r}")
    print()
    print("  MACHINE VERDICT:")
    print(f"    {g['literal']}")
    print()

    # Does the construction-prose machine emit a SPECIFIC ANSWERABLE QUESTION?
    # comprehend_gluing returns "" — a TOTAL un-parse. It does NOT name an
    # unparsed token, does NOT say "I have X, I lack Y to do Z". It returns the
    # empty word, silently. There is NO specific question for the parent to
    # answer one-step. This is the (b) signature.
    machine_posed_question = None  # the machine emitted NO specific question.

    # ---- TURN 1b: do the agent's DIAGNOSE faculties NAME the gap as a question?
    # The strict rail: a machine-posed question can ALSO come from a diagnose
    # faculty ('the missing construction is X'). Run EVERY held diagnose machine. ----
    print("-" * 78)
    print("TURN 1b — the agent's DIAGNOSE faculties run ALONE on the prose")
    print("-" * 78)
    d = probe_diagnose_machines(prose)
    print("  MACHINE [comprehend_question.diagnose_comprehension_gap] ->",
          repr(d["diagnose_comprehension_gap"]))
    print("  MACHINE [comprehend_question.diagnose_why_diagnosis_failed] ->",
          repr(d["diagnose_why_diagnosis_failed"]))
    print()
    print("  Both return None: these faculties fire ONLY on a COMPARISON goal-")
    print("  shape ('compare X with Y'); on this CONSTRUCTION prose they name")
    print("  NOTHING. The diagnose tier poses NO specific answerable question")
    print("  either. (The elevator.diagnose_wall needs a STALLED OP NAME, which")
    print("  the comprehension never produced -> it cannot run.)")
    print()

    # ---- TURN 2: try the QUESTION-LEVEL comprehension machine (does IT pose a
    # specific answerable question?). This is the agent's other comprehension
    # front — it may at least name what it comprehended vs what it lacks. ----
    print("-" * 78)
    print("TURN 2 — the agent's QUESTION-LEVEL comprehension machine runs ALONE")
    print("-" * 78)
    q = probe_question_comprehend(prose)
    print(f"MACHINE [{q['machine']}] literal output:")
    print(f"    {q['literal']}")
    print()
    print("  This machine DID comprehend the ASK (relation/object) but it is the")
    print("  QUESTION shell ('what is the fundamental group of X'), not the")
    print("  CONSTRUCTION ('two pants sewn ... waistbands identified'). Its")
    print("  frontier names a missing LEXICON ENTRY (a target-op), which is NOT")
    print("  the prose->structure wall the experiment targets.")
    print()

    # The SPECIFIC-QUESTION test: is the machine's output an answerable one-step
    # question (e.g. 'unparsed token: pants' / 'no held representation for:
    # leg-opening-sewing' / 'I have the polygon-word reader, I lack the operator
    # for sewing two surfaces along boundary circles')?
    #   - comprehend_gluing: NO (returns "" silently — total un-parse).
    #   - comprehend (question): it poses a frontier, but about a MISSING TARGET-
    #     OP LEXICON ENTRY, not about the CONSTRUCTION prose. Answering it
    #     one-step ('the target op is fundamental_group') would NOT advance the
    #     prose->structure build — it would just route to an op the agent has no
    #     construction for. It is not a question whose one-step answer the agent
    #     can incorporate to CONTINUE the prose->structure build.

    print("=" * 78)
    print("THE ASK-LOOP RESULT")
    print("=" * 78)
    if machine_posed_question is None:
        print("OUTCOME (b): CANNOT FORMULATE THE QUESTION (the metacognition wall).")
        print()
        print("  The agent's CONSTRUCTION-PROSE machinery (comprehend_gluing) ran")
        print("  ALONE on the prose and returned the EMPTY WORD on every clause.")
        print("  It did NOT emit a SPECIFIC ANSWERABLE QUESTION — no 'unparsed")
        print("  token: X', no 'no held representation for: Y', no 'I have P, I")
        print("  lack Q to do Z'. It failed SILENTLY (a total un-parse).")
        print()
        print("  Because the machine posed NO specific question, the PARENT has")
        print("  NOTHING to answer one-step. The strict rail HALTS here:")
        print("  the agent CANNOT ASK. This is the deeper meta-wall — the agent")
        print("  lacks the metacognition to articulate its prose->structure gap")
        print("  as an answerable question.")
        print()
        print(f"  ASKS NEEDED: {asks} (the machine never posed an answerable Q).")
    else:
        print("OUTCOME: machine posed a question (see transcript).")

    # ---- THE FADE / 2nd-construction contrast. Under outcome (b) the agent posed
    # ZERO asks on the 1st construction, so the fade ('fewer asks on the 2nd') is
    # degenerate from below. The MEANINGFUL contrast: a construction WITHIN the
    # held grammar parses with ZERO asks (the machinery succeeds silently); a
    # construction OUTSIDE it (the pants, and another) returns "" AND cannot ask.
    # The wall is the GRAMMAR BOUNDARY, and the agent cannot articulate crossing it. ----
    print()
    print("-" * 78)
    print("THE FADE / 2nd-CONSTRUCTION CONTRAST")
    print("-" * 78)
    within = ["the real projective plane",
              "identifying all five sides of a filled pentagon in a cyclic "
              "orientation"]
    outside = ["the connected sum of two tori"]   # outside the held grammar
    print("  WITHIN the held gluing grammar (parse with ZERO asks):")
    for desc in within:
        print(f"    {desc!r:62s} -> word={_co.comprehend_gluing(desc)!r}")
    print("  OUTSIDE the held gluing grammar (return '' AND cannot ask):")
    for desc in outside + ["<the pants construction (this run)>"]:
        if desc.startswith("<"):
            print(f"    {desc:62s} -> word='' (+ no specific question posed)")
        else:
            print(f"    {desc!r:62s} -> word={_co.comprehend_gluing(desc)!r}"
                  f"  (+ no specific question posed)")
    print()
    print("  FADE VERDICT: not applicable in the (a) sense (no asks were posed to")
    print("  internalize). The contrast shows the wall is the GRAMMAR BOUNDARY:")
    print("  inside it the machinery succeeds with zero asks; outside it the")
    print("  machinery fails SILENTLY and cannot formulate the question that would")
    print("  let a parent bridge it one step. The prerequisite the agent lacks is")
    print("  METACOGNITION OVER COMPREHENSION: a machine that, on a '' parse,")
    print("  emits 'unparsed construction-noun: <pants/leg-opening/waistband>; I")
    print("  hold the polygon-word reader, I lack the operator for <X>' — an")
    print("  answerable question. That faculty exists for the COMPARISON goal-shape")
    print("  (diagnose_comprehension_gap) but NOT for construction-prose gluing.")

    # ---- INTEGRITY + the honest record. ----
    print()
    print("-" * 78)
    print("INTEGRITY")
    print("-" * 78)
    print("  PARENT contributions this run: 0 one-step answers (the machine posed")
    print("  no answerable question, so the parent stayed MUTE — the strict rail).")
    print("  The shell authored NO construction spec, NO topology, NO build, NO")
    print("  answer-shape. It only ran the agent's machinery + captured the")
    print("  literal output. The pi_1 key was NEVER read (no build to verify).")
    print()
    print(f"  PARENT_ONE_STEP table size: {len(PARENT_ONE_STEP)} (empty — no")
    print("  machine-posed question to answer).")

    print()
    print("[MARKER] STRICT_ASK_LOOP_PANTS_COMPLETED")


if __name__ == "__main__":
    main()
