"""ASK THE AGENT to COMPOSE and RUN a communication faculty — graph-native, its own.

No Python perception, no hand-authored Term. The agent reasons (via its teacher channel) from
its OWN communication concepts to a DECISION faculty expressed as a `_spec_to_term` spec
(Holds/And/Or/IfThenElse/Eq/Lit over its concepts), the mechanical translator builds the Term,
`author_subroutine` stores it (the agent owns/runs/explains it), a subroutine-backed Operator is
bound to the communication frontier, and the autonomy loop RUNS it (the bridge from
fbae98ef) -> measured -> banked.

The faculty composed: WHEN to use the elaborated/considerate form vs the brief one — terseness is
a face-threat (Grice quantity / negative face), elaboration softens ('ok.' vs 'ok, thanks'). The
agent decides this from its held pragmatics concepts; the result is a Term-tree it can audit.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_composes_communication
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from substrate.jsonio import term_to_json

SEP = "=" * 84
CONCEPTS = ["maxim_of_quantity", "maxim_of_manner", "positive_face", "negative_face",
            "politeness_theory", "indirect_speech_act", "common_ground", "acknowledgment"]

_PROMPT = (
    "You ARE a graph agent composing one of your OWN faculties as a Term-tree, using only this "
    "nested-list DSL (return JSON):\n"
    '  ["Holds", "<concept_name>", "value"]   — does the situation hold this concept\n'
    '  ["Or", A, B]   ["And", A, B]   ["Not", A]\n'
    '  ["IfThenElse", cond, then_value, else_value]\n'
    '  a string in quotes = a literal value; "value" = the situation\'s scalar\n'
    "Use ONLY these concept names you hold: " + ", ".join(CONCEPTS) + ".\n\n"
    "Compose the DECISION: when you acknowledge, choose the ELABORATED/considerate form vs the "
    "BRIEF one. Terseness is a face-threat (Grice quantity / negative face); elaboration softens "
    "it ('ok.' is curt, 'ok, thanks' is considerate). Return ONLY the JSON nested-list for the "
    "decision (its value is the string \"considerate\" or \"brief\").")


def _extract_spec(text):
    """Pull the JSON nested-list the agent returned (tolerating surrounding prose)."""
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\[.*\]", text or "", re.DOTALL)
        return json.loads(m.group(0)) if m else None


def main():
    print(SEP)
    print("ASK THE AGENT to COMPOSE + RUN a communication faculty (graph-native, its own)")
    print(SEP)
    a = boot()
    for sid in ("pragmatics", "ling_pragmatics"):
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid} skipped: {e})")

    teacher = a._self_teacher
    print("  asking the agent to compose the faculty (reasoning over its pragmatics concepts)...",
          flush=True)
    reply = teacher(_PROMPT) if teacher else None
    spec = _extract_spec(reply)
    print(f"  the agent composed (spec): {json.dumps(spec) if spec else reply!r}")
    if not spec:
        print("  (no parseable spec returned)"); print(SEP); return

    # build the Term the agent composed; store it as a faculty it owns
    try:
        term_json = term_to_json(a._spec_to_term(spec))
    except Exception as e:
        print(f"  _spec_to_term failed: {e}"); print(SEP); return
    a.author_subroutine("communication_brevity", term_json,
                        purpose="choose considerate vs brief by face/Grice (the agent's own)")
    print("  authored subroutine 'communication_brevity' (a Term-tree the agent owns)")

    # bind a subroutine-backed Operator to the communication frontier so the loop RUNS it
    ax = next((n for n in a.s.nodes("CapabilityAxis")
               if "persona" in (a.s.node(n)["attrs"].get("capability_keys") or [])), None)
    if ax is not None:
        for old in list(a.inner.neighbours(ax, "investigated_by")):
            a.inner.remove_edge(ax, "investigated_by", old)
        op = a.s.add_node("Operator", {"name": "communication_brevity_op",
                                       "subroutine": "communication_brevity",
                                       "runner": "subroutine", "metric": "composed", "target": 0.5})
        a.inner.add_edge_unchecked(ax, "investigated_by", op)
        mt = next((n for n in a.s.nodes("Microtheory")
                   if a.s.node(n)["attrs"].get("name") == "expression_world"), None)
        if mt is not None:
            a.inner.add_edge_unchecked(op, "applies_in", mt)   # so the bind JOIN fires -> loop runs it

    # the agent can AUDIT it: re-evaluate its own composed faculty
    audit = a.run_subroutine("communication_brevity")
    print(f"  the agent RUNS + audits its faculty -> decision = {audit!r}")

    # let the autonomy loop run it end-to-end (plan -> bind -> RUN the Term -> measure -> bank)
    for _ in range(8):
        a.master_tick(); a.tick()
    ran = [a.s.node(m)["attrs"] for m in a.s.nodes("MeasuredCapability")
           if "composed" in str(a.s.node(m)["attrs"].get("metric", ""))
           or "communication_brevity" in str(a.s.node(m)["attrs"].get("note", ""))]
    print("\n" + SEP)
    print(f"  the agent COMPOSED a communication faculty as a Term-tree, RUNS it (decision="
          f"{audit!r}), and the autonomy loop executed it: {len(ran)} measurement(s).")
    for r in ran[:3]:
        print(f"    ran: {r.get('note','')[:80]}  measured={r.get('measured')}")
    print("  graph-native, owned, runnable, auditable — no Python perception, no hand-authored Term.")
    print(SEP)


if __name__ == "__main__":
    main()
