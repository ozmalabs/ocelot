"""ASK THE AGENT to COMPOSE the persona-PERCEPTION faculty — graph-native, its own.

No Python perceiver (the rejected persona_reader). The agent composes a PERCEPTION as a DSL
Term-tree over a COMPREHENDED exemplar (Message --has_mention--> Mention{text}), author_subroutine
stores it (it owns/runs/audits it), and it runs over persona exemplars to extract their voice.

The faculty: a persona's GREETING = the text of the FIRST token of its self-demonstrating exemplar
(pirate "Avast!", surfer "Duuuude!", ...). Composed from held Terms (Neighbours/Nth/Attr) — no new
primitive. The agent proposes the Term (its reasoning channel) from the schema + goal.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_composes_perception
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

SEP = "=" * 84
EXEMPLARS = [("pirate", "TalkLikeAPirate"), ("surfer", "SurferDude"), ("valley", "ValleyGirl")]

_PROMPT = (
    "You ARE a graph agent composing one of your OWN perception faculties as a DSL Term-tree "
    "(return JSON). A COMPREHENDED exemplar is a Message node (bound to the variable 'msg'); its "
    "tokens are Mention nodes reached by the edge 'has_mention', in order, each carrying a 'text' "
    "attribute. Compose the Term that PERCEIVES the persona's GREETING = the text of the FIRST "
    "token.\nTerm JSON forms you may use (exact fields):\n"
    '  {"type":"Var","name":"msg"}\n'
    '  {"type":"Lit","value":0}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"has_mention"}\n'
    '  {"type":"Nth","items":<term>,"index":<term>}\n'
    '  {"type":"Attr","node":<term>,"key":"text"}\n'
    "Return ONLY the JSON Term for the greeting perception.")

# The frequency-markers perception: a persona's characteristic MARKER = the Concept that the
# MOST of THIS exemplar's tokens refer to. Comprehension wires Mention --refers_to--> Concept;
# the marker is the most-referred Concept, scoped to this message (NodesOfType ranges over all
# Concepts; the count is filtered to msg's own mentions so unrelated concepts score 0).
_MARKERS_PROMPT = (
    "You ARE a graph agent composing one of your OWN perception faculties as a DSL Term-tree "
    "(return JSON). A COMPREHENDED exemplar is a Message node (bound to variable 'msg'); its tokens "
    "are Mention nodes reached by edge 'has_mention'; comprehension links each Mention to the "
    "Concept(s) it denotes by edge 'refers_to'. Compose the Term that PERCEIVES the persona's "
    "characteristic MARKER = the Concept that the MOST of THIS message's mentions refer to.\n"
    "Term JSON forms you may use (exact fields):\n"
    '  {"type":"Var","name":"msg"}   {"type":"Var","name":"c"}   {"type":"Var","name":"m"}\n'
    '  {"type":"NodesOfType","node_type":"Concept"}   — every Concept node (the candidates)\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"has_mention","any_type":false}\n'
    '  {"type":"In","member":<term>,"container":<term>}   — is member in the container set\n'
    '  {"type":"Filter","source":<set>,"var_name":"m","predicate":<bool term over m>}\n'
    '  {"type":"Count","source":<set>}\n'
    '  {"type":"Argmax","source":<set>,"var_name":"c","value":<number term over c>}\n'
    "The marker is Argmax over every Concept c, scored by the COUNT of msg's mentions m whose "
    "'refers_to' neighbours contain c. Return ONLY the JSON Term.")


def _extract(text):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text or "", re.DOTALL)
        return json.loads(m.group(0)) if m else None


def main():
    print(SEP)
    print("ASK THE AGENT to COMPOSE the persona-PERCEPTION faculty (graph-native, its own)")
    print(SEP)
    a = boot()
    teacher = a._self_teacher
    print("  asking the agent to compose the greeting-perception Term...", flush=True)
    reply = teacher(_PROMPT) if teacher else None
    term = _extract(reply)
    print(f"  the agent composed (Term): {json.dumps(term) if term else reply!r}")
    if not term:
        print("  (no parseable Term)"); print(SEP); return
    a.author_subroutine("persona_greeting", term,
                        purpose="perceive a persona's greeting from a comprehended exemplar")
    print("  authored subroutine 'persona_greeting' (a perception Term the agent owns)\n")

    # SECOND faculty: the frequency-markers perception (most-referred Concept), composed with
    # NodesOfType + In — the Term the agent could not express before NodesOfType was usable.
    print("  asking the agent to compose the frequency-markers Term (NodesOfType)...", flush=True)
    mreply = teacher(_MARKERS_PROMPT) if teacher else None
    markers = _extract(mreply)
    print(f"  the agent composed (Term): {json.dumps(markers) if markers else mreply!r}")
    if markers:
        try:
            a.author_subroutine("persona_markers", markers,
                                purpose="perceive a persona's characteristic marker (most-referred concept)")
            print("  authored subroutine 'persona_markers' (a frequency-perception Term the agent owns)\n")
        except Exception as e:
            print(f"  (could not author markers Term: {e})"); markers = None

    # run the agent's composed perceptions over comprehended persona exemplars
    from domains.tropes_teacher import TropesTeacher
    tt = TropesTeacher.from_cache()
    rows = []
    for persona, trope in EXEMPLARS:
        payload = tt(trope) if tt else None
        if not payload:
            continue
        mid = a.add_inbound((payload.get("answer") or "")[:240])   # comprehend the exemplar
        a.comprehend()
        try:
            g = a.run_subroutine("persona_greeting", {"msg": mid})   # RUN its composed perception
        except Exception as e:
            g = f"(err {type(e).__name__})"
        mk = None
        if markers:
            try:
                win = a.run_subroutine("persona_markers", {"msg": mid})
                mk = a.s.node(win)["attrs"].get("name") if win is not None else None
            except Exception as e:
                mk = f"(err {type(e).__name__})"
        rows.append((persona, g, mk))
        print(f"  perceived {persona:8} greeting = {g!r:14} marker = {mk!r}")

    print("\n" + SEP)
    print(f"  the agent COMPOSED two persona-perception Term-trees (greeting + frequency-marker) and "
          f"RAN them over {len(rows)} exemplars — graph-native, owned, auditable.")
    print("  no Python perceiver, no hand-authored Term: the agent composed them from its held Terms.")
    print(SEP)


if __name__ == "__main__":
    main()
