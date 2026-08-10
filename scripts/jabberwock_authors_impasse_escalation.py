"""The jabberwock AUTHORS its own ORDER-N IMPASSE ESCALATION.

THE GAP (order-1 today): when a faculty stalls, the agent mints an Impasse, consults the
teacher for a better CUE, and `ground_hint_to_investigation` retries the SAME faculty
(it copies the axis's capability_keys and re-binds the SAME operator). So it can tune
WITHIN an approach but cannot change its mind FUNDAMENTALLY about the approach.

ORDER-N = escalate the IMPASSE itself: if a faculty was already TAUGHT and STILL stalls,
the cue is not the problem — the METHOD is. The agent should climb: change the cue (1) ->
change the METHOD/operator (2) -> change the TOOLS/author a new faculty (3) -> change
PERCEPTION/front-end (4) -> change the FRAMING/axis (5).

This is authored the project way (jabberwock_authors_*): the AGENT introspects the gap,
the teacher decides the METHOD ONLY (the escalation policy + the alternative approach),
the agent AUTHORS the escalation as graph-resident RULES it installs into its own
substrate, and it VERIFIES on the LIVE speech-autonomy loop that a stall-of-stalls now
CHANGES the operator binding (a fundamentally different approach), not an order-1 retry.

Run (project .venv python):
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_authors_impasse_escalation
  SPEECH_TEACHER=stub -> skip claude -p (use the agent's own fallback method).
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.autonomous_speech import boot, SEP


# ---------------------------------------------------------------------------
# 3. CONSULT — the teacher decides the METHOD ONLY: the escalation policy + the
#    alternative approach for a faculty that keeps stalling. Structured reply.
# ---------------------------------------------------------------------------

_ESCALATION_Q = """A learning agent develops faculties (operators) against capability axes. When a
faculty STALLS, the agent mints an Impasse, asks a teacher for a better acoustic CUE, and RETRIES
THE SAME faculty. The problem: if the faculty was already taught a cue and STILL stalls, the cue is
not the issue — the whole METHOD may be wrong, and the agent has no way to change its mind
fundamentally.

The agent's faculties for word RECOGNITION:
  - "abs_self_test": analysis-by-synthesis on ISOLATED words (speak a word with TTS, hear it with
    its own ear, recognise, check against ground-truth). THIS IS THE ONE THAT KEEPS STALLING.
  - "ingest_continuous": segment + recognise from REAL CONTINUOUS speech (children's videos).

Decide the agent's ESCALATION METHOD (the policy, not code). Output ONLY a JSON object between the
markers, no prose:

@@@escalation
{
  "trigger": "<when to escalate: describe the stall-of-stalls condition in one phrase>",
  "ladder": ["<order 2 = ...>", "<order 3 = ...>", "<order 4 = ...>", "<order 5 = ...>"],
  "first_escalation_runner": "<for the stalled isolated-word recognition faculty, which DIFFERENT existing runner is the better METHOD to switch to: 'ingest_continuous' or 'abs_self_test'>",
  "rationale": "<one sentence: why that is a fundamentally different approach, not a retry>"
}
@@@end"""


def consult_method(adapter):
    """The teacher decides the escalation METHOD only. Falls back to the agent's own
    default policy if the teacher channel is unavailable (logged honestly)."""
    teacher = getattr(adapter, "_self_teacher", None)
    if teacher is not None:
        reply = teacher(_ESCALATION_Q)
        m = re.search(r"@@@escalation\s*(.+?)\s*@@@end", reply or "", re.DOTALL)
        if m:
            try:
                method = json.loads(m.group(1).strip())
                if method.get("first_escalation_runner") in ("ingest_continuous", "abs_self_test"):
                    return method, "teacher"
            except Exception:
                pass
    # fallback (teacher unavailable): the agent's own minimal policy — switch the stalled
    # isolated-word faculty to learning from continuous speech (a genuinely different method).
    return ({
        "trigger": "a faculty already taught a cue that still stalls",
        "ladder": ["order2 = change the method (a different operator)",
                   "order3 = author a new faculty if none fits",
                   "order4 = revise the front-end (what it hears)",
                   "order5 = re-decompose the capability"],
        "first_escalation_runner": "ingest_continuous",
        "rationale": "learn the word from real continuous speech context instead of isolated "
                     "synthesis — a different source of evidence, not a different cue."},
            "fallback")


# ---------------------------------------------------------------------------
# 4. AUTHOR — the agent renders the teacher's policy into graph-resident RULES it
#    installs into its OWN substrate (inner.add_rule). The POLICY is the agent's;
#    rendering the policy into the rule schema is mechanical (like emit_term).
# ---------------------------------------------------------------------------

def author_escalation_rules(adapter, method):
    """Install the order-N escalation faculty as two graph rules + a policy concept.

      escalate_on_repeated_stall : an axis already TAUGHT (taught_about) whose mf_stall
        has grown FURTHER (>= 6) and is not yet escalated -> a HIGHER-ORDER Impasse
        (order=2, kind=method_escalation) + mark the axis escalating. The stall-of-stalls.

      escalate_change_method : an escalating axis -> author a NEW Operator carrying the
        teacher-chosen DIFFERENT runner, DROP the old investigated_by edge, and BIND the
        axis to the new operator. The agent changes its METHOD, graph-natively.
    """
    runner = method["first_escalation_runner"]
    metric = "continuous_purity" if runner == "ingest_continuous" else "abs_recognition_match"

    # record the policy the agent now holds (auditable, its own terms).
    adapter.register_concept("impasse_escalation_policy", {"type": "Lit", "value": json.dumps(method)})

    esc_order = {"type": "Lit", "value": 2}
    rule_escalate = {
        "name": "escalate_on_repeated_stall",
        "comment": "ORDER-N: a faculty already TAUGHT a cue (taught_about) that STILL stalls "
                   "(mf_stall >= 4 = consulted at 3, stalled again) -> a higher-order "
                   "method_escalation Impasse. The cue is not the problem; the method is.",
        "match": [["ag", "operates_in", "w"], ["ax", "investigated_by", "op"], ["ax", "taught_about", "h"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "ax"}, "key": "is_axis"}, "b": {"type": "Lit", "value": 1.0}},
            {"type": "Gte", "a": {"type": "Attr", "node": {"type": "Var", "name": "ax"}, "key": "mf_stall"}, "b": {"type": "Lit", "value": 4}},
            {"type": "Not", "arg": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "ax"}, "key": "escalated"}, "b": {"type": "Lit", "value": 1.0}}}
        ]},
        "effects": [
            ["add_node", "mi", "Impasse", {
                "resolved": False, "kind": "method_escalation", "order": 2,
                "question": "I already tried a better cue and still stall. The METHOD is wrong, "
                            "not the cue. Switch to a fundamentally different approach.",
                "for_frontier": {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "ax"}, "key": "capability_keys"}}}],
            ["add_edge", "ag", "surprised_by", "mi"],
            ["add_edge", "mi", "about_axis", "ax"],
            ["set_attr", "ax", "escalated", {"__term__": esc_order}]
        ]
    }

    rule_change_method = {
        "name": "escalate_change_method",
        "comment": "the method_escalation -> AUTHOR a new Operator with a DIFFERENT runner (the "
                   "teacher-chosen approach), drop the old investigated_by, bind the axis to it. "
                   "The agent changes its mind about the APPROACH, not just the cue.",
        "match": [["mi", "about_axis", "ax"], ["ax", "investigated_by", "oldop"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "mi"}, "key": "kind"}, "b": {"type": "Lit", "value": "method_escalation"}},
            {"type": "Not", "arg": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "mi"}, "key": "grounded"}, "b": {"type": "Lit", "value": 1.0}}},
            {"type": "Not", "arg": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "oldop"}, "key": "runner"}, "b": {"type": "Lit", "value": runner}}}
        ]},
        "effects": [
            ["add_node", "newop", "Operator", {
                "name": "escalated_recogniser", "runner": runner, "metric": metric,
                "target": 0.6, "authored_by_escalation": 1.0,
                "comment": "a DIFFERENT method for the stalled capability, authored on a stall-of-stalls."}],
            ["add_edge", "newop", "applies_in", "__speech_world_mt__"],
            ["del_edge", "ax", "investigated_by", "oldop"],
            ["add_edge", "ax", "investigated_by", "newop"],
            ["set_attr", "ax", "shortfall", {"__term__": {"type": "Lit", "value": 0.6}}],
            ["set_attr", "ax", "mf_stall", {"__term__": {"type": "Lit", "value": 0}}],
            ["set_attr", "mi", "grounded", {"__term__": {"type": "Lit", "value": 1}}]
        ]
    }

    # the new Operator must applies_in the agent's world (the JOIN needs op.applies_in ==
    # ag.operates_in). Rules cannot carry a runtime node id, so bind it via a JOIN on the
    # agent's world (mtw) instead of a literal microtheory id.
    rule_change_method["match"].append(["ag2", "operates_in", "mtw"])
    rule_change_method["effects"][1] = ["add_edge", "newop", "applies_in", "mtw"]

    adapter.inner.add_rule(rule_escalate)
    adapter.inner.add_rule(rule_change_method)
    return runner, metric


# ---------------------------------------------------------------------------
# main: introspect -> perceive -> consult -> author -> verify on the LIVE loop.
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("THE JABBERWOCK AUTHORS ORDER-N IMPASSE ESCALATION — change its mind about the APPROACH.")
    print("(This is the RECORD of how order-2 was first authored; the full domain-agnostic")
    print(" ladder now persists in seeds/impasse_escalation.json — booted here WITHOUT it.)")
    print(SEP)
    adapter, sw = boot(exclude=("impasse_escalation",))

    # 1. INTROSPECT — record the order-1 gap as the agent's own Impasse.
    gap = adapter.impasse(
        reason="impasse_is_order_1",
        question="When a faculty stalls I retry the SAME approach with a new cue. I cannot change "
                 "my mind FUNDAMENTALLY about the method when the cue is not the problem.")
    print(f"  INTROSPECT gap: {adapter.s.node(gap)['attrs']['question']}\n")

    # 2/3. CONSULT — the teacher decides the escalation METHOD only.
    method, src = consult_method(adapter)
    print(f"  CONSULT ({src}) -> escalation method:")
    print(f"    trigger : {method['trigger']}")
    print(f"    switch the stalled isolated-word faculty -> runner '{method['first_escalation_runner']}'")
    print(f"    why     : {method['rationale']}")
    for rung in method.get("ladder", []):
        print(f"    ladder  : {rung}")
    print()

    # 4. AUTHOR — the agent installs the escalation as graph rules on its own substrate.
    runner, metric = author_escalation_rules(adapter, method)
    print(f"  AUTHORED 2 escalation rules + the policy concept; new method runner = '{runner}'\n")
    adapter.mark_impasse_resolved(gap)

    # record the recognise axis's ORIGINAL operator (to prove the approach CHANGES).
    def recognise_axis():
        for ax in adapter.s.nodes("CapabilityAxis"):
            a = adapter.s.node(ax)["attrs"]
            if a.get("is_axis") == 1.0 and a.get("capability_keys") and "recognise" in a["capability_keys"] \
               and a.get("from_teacher") != 1.0:
                return ax
        return None
    rax = recognise_axis()
    def bound_runner(ax):
        ops = adapter.inner.neighbours(ax, "investigated_by")
        return adapter.s.node(ops[0])["attrs"].get("runner") if ops else None
    orig_runner = bound_runner(rax)
    print(f"  recognise axis originally bound to runner '{orig_runner}'")

    # 5. VERIFY — run the LIVE loop; the stall-of-stalls must ESCALATE and CHANGE the method.
    print(f"\n  VERIFY — pumping the live loop until the stall-of-stalls escalates...\n")
    escalated_imp, changed_at = None, None
    for t in range(1, 61):
        adapter.master_tick(); adapter.tick()
        if t % 6 == 0 and rax is not None:
            a = adapter.s.node(rax)["attrs"]
            taught = len(adapter.inner.neighbours(rax, "taught_about"))
            print(f"  [tick {t:2d}] recognise mf_stall={a.get('mf_stall')} "
                  f"taught_about={taught} runner={bound_runner(rax)}")
        esc = [n for n in adapter.s.nodes("Impasse")
               if adapter.s.node(n)["attrs"].get("kind") == "method_escalation"]
        if esc and escalated_imp is None:
            escalated_imp = esc[0]
            print(f"  [tick {t:2d}] ORDER-2 escalation: method_escalation Impasse minted "
                  f"(order={adapter.s.node(esc[0])['attrs'].get('order')})")
        nowr = bound_runner(rax)
        if nowr != orig_runner and changed_at is None:
            changed_at = t
            print(f"  [tick {t:2d}] APPROACH CHANGED: recognise axis re-bound '{orig_runner}' -> '{nowr}'")
            break

    final_runner = bound_runner(rax)
    authored_ops = [n for n in adapter.s.nodes("Operator")
                    if adapter.s.node(n)["attrs"].get("authored_by_escalation") == 1.0]
    print(f"\n{SEP}")
    print(f"  escalation impasse minted : {escalated_imp is not None}")
    print(f"  operator authored on stall: {len(authored_ops)}")
    print(f"  recognise approach: '{orig_runner}' -> '{final_runner}'  (changed: {final_runner != orig_runner})")
    ok = (escalated_imp is not None and final_runner != orig_runner and len(authored_ops) >= 1)
    print(f"  {'PASS' if ok else 'FAIL'} — the jabberwock AUTHORED order-N escalation and, on a "
          f"stall-of-stalls, CHANGED ITS APPROACH (not an order-1 retry).")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
