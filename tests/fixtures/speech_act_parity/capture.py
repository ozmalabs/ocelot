"""capture.py — Wave-4 speech-act (KIND) migration parity-fixture capture.

Runs a broad utterance corpus through the CURRENT (unmodified) Python
comprehension front end and freezes, per utterance, everything the KIND
migration must preserve byte-for-byte:

  * ``signals``     — the three classification SIGNALS ``_classify_kind`` reads
    (politeness-stripped ends-with-'?', first parsed element's role/pos). These
    are the exact inputs the graph rules (seeds/speech_act_classify.json) get.
  * ``ladder_kind`` — ``comprehend_text._classify_kind``'s decision on those
    signals. This is the ORACLE the seed rules must reproduce exactly.
  * ``kind`` / ``dispatch_path`` / ``predicate`` / ``content`` — the final
    Comprehension record as ``_write_comprehension_to_graph`` writes it onto
    the inbound Message (``comp_kind`` / ``comp_dispatch_path`` /
    ``comp_predicate`` / ``comp_content``), i.e. what downstream seed rules
    actually match on.

The SAME parity method as tests/fixtures/reading_parity/capture.py and
tests/fixtures/composer_driver_parity: capture the OLD path BEFORE rewiring;
the gate (tests/test_speech_act_parity_migrated.py) replays the corpus through
the NEW (graph-rule-classified) path and diffs byte-for-byte. Any mismatch is a
migration bug, never an improvement.

This script does NOT modify any source file; it only reads the current code
and writes the fixture. Idempotent (each run overwrites the same file). The
environment is the standard migrated-bench agent (WorldAdapter(seeds=()) +
load_all_seeds) so the parse lexicon matches what the session gates run under.
NO rule pass is run during capture (receive_utterance /
_write_comprehension_to_graph never tick), so the fixture is a pure record of
the Python path.

Run:  cd gamma-substrate && PYTHONPATH=runners/dsl/python:. python3 \
        tests/fixtures/speech_act_parity/capture.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "speech_act_parity")

from substrate.world_adapter import WorldAdapter                    # noqa: E402
from substrate.boot_all import load_all_seeds                       # noqa: E402
from domains import comprehend_text as ct                           # noqa: E402
from domains import construction_grammar as cg                      # noqa: E402


# --------------------------------------------------------------------------- #
#  CORPUS — ≥100 utterances covering every branch of the kind ladder:
#  questions of all shapes (wh, polar/aux-inverted, tag/?-only, embedded),
#  instructions covered and uncovered (incl. the POS-blind imperatives Wave 2
#  found — sentence-initial work/focus/drop tagged as nouns), statements,
#  greetings/fragments, politeness-wrapped ornate forms, and the documented
#  tricky cases. Mined from the existing conversation/comprehension tests.
# --------------------------------------------------------------------------- #
CORPUS = {
    "WH_QUESTIONS": [
        "What are you?",
        "what are you",
        "Who are you?",
        "what sort of thing are you?",
        "What are you working on?",
        "What do you know about the moon?",
        "What do you know about the three body problem?",
        "What do you know about zqxwvt?",
        "What is an LLM?",
        "what is a graph",
        "what is a borogove",
        "What is the moon made of?",
        "What gaps do you have?",
        "What gaps do you have in your knowledge?",
        "How are you organised?",
        "How are you organised today, honestly?",
        "How does your collapse function work?",
        "How does your reasoning work?",
        "How do you dream?",
        "How do you learn?",
        "How big is it?",
        "What about volcanoes?",
        "When did you last update yourself?",
        "Why is the sky blue?",
        "Where do you live?",
        "Which rule fired last?",
        "What does the text say in the image?",
        "What is in the image?",
        "what does hop_descend_gradient do, you?",
        "How many rules do you hold?",
        "what experiments are you running?",
    ],
    "POLAR_AUX_QUESTIONS": [
        "Are you an LLM?",
        "Are you the Jabberwock?",
        "Can you dance?",
        "Can you play chess?",
        "Can you navigate 3D spaces?",
        "Could you dance if you had a body?",
        "Do you know what dancing is?",
        "Do you find yourself capable of frobulation?",
        "Can you expand on it?",
        "can you describe how you're put together?",
        "Is the pitcher empty?",
        "Does the moon have water?",
        "Would you kindly open the door?",
        "Is that a fact?",
        "Are birds animals?",
        "Will it rain tomorrow?",
        "Should I read this?",
        "Have you seen the report?",
    ],
    "MARK_TAG_FRAGMENT_QUESTIONS": [
        "The sky is blue?",
        "You can learn, right?",
        "It works, doesn't it?",
        "You hold rules, yes?",
        "and the three body problem?",
        "volcanoes?",
        "?",
        "really?",
    ],
    "INSTRUCTIONS_COVERED": [
        "Read this: The sky is blue.",
        "Run the script.",
        "look left",
        "move north",
        "Describe yourself.",
        "describe what you see",
        "Describe the image",
        "Read the text in the image",
        "report your organisation",
        "Fix your grammar.",
        "Improve your reading.",
        "Improve your florbnax.",
        "Tell me about the moon.",
        "Tell me about the rule hop_descend_gradient.",
        "tell me about yourself",
        "Tell me more about it.",
        "Name one of your rules.",
        "Show me your gaps.",
    ],
    "INSTRUCTIONS_UNCOVERED": [
        "Summarise the report.",
        "Work on the summarise report gap.",
        "Work on the flurble gap.",
        "Pursue the flurble gap.",
        "Drop the transmogrify data gap.",
        "Focus on the reading work.",
        "Promote the first concern.",
        "Transmogrify the data.",
        "Juggle the plates.",
        "quorplezap the door",
        "blorptangle the widget",
        "flar the glorp",
        "look left then quorplezap the door",
        "Open the door.",
        "Write a poem about rain.",
        "Stop working on that.",
        "List your rules.",
        "Enumerate your faculties.",
    ],
    "STATEMENTS": [
        "the sky is blue",
        "it is blue",
        "yeah cool, the sky is blue",
        "Indeed, the sky is certainly blue.",
        "The rule hop_descend_gradient modifies gravity.",
        "I asked the compiler for relationship advice.",
        "We went down the rabbit hole on this problem.",
        "Good day. I am Cornelius Vane, a humble scholar of natural philosophy.",
        "You cannot elaborate.",
        "You keep repeating yourself.",
        "That answer was wrong.",
        "Your parser is broken.",
        "The crow dropped the pebbles into the pitcher.",
        "Rain causes floods.",
        "A dog is an animal.",
        "I uploaded a file.",
        "The moon orbits the earth.",
        "This is a test.",
        "There is a gap in your reasoning.",
    ],
    "SOCIAL_FRAGMENTS": [
        "hello",
        "Hello.",
        "hey, what's up?",
        "Good morning",
        "thanks",
        "Thank you!",
        "goodbye",
        "ok",
        "yes",
        "no",
        "hmm",
        "more",
        "tell me more",
        "go on",
    ],
    "POLITENESS_ORNATE": [
        "Pray, tell me plainly: what are you?",
        "Good day, kindly tell me the time.",
        "Please describe your architecture.",
        "kindly list your faculties",
        "Prithee, what art thou?",
    ],
    "EMPTYISH": [
        "",
        "   ",
    ],
}


def kind_signals_current(agent, text):
    """The three classification signals off the CURRENT code path (politeness
    strip + parse), exactly as _classify_kind consumes them."""
    stripped = ct._strip_politeness(agent, text or "")
    try:
        frame = cg.parse_with_gaps(stripped, getattr(agent, "s", agent))
    except Exception:  # noqa: BLE001 — unparseable input still classifies (ends-? only)
        frame = {}
    els = (frame or {}).get("elements") or []
    first = els[0] if els else None
    return {
        "ends_q": bool((stripped or "").strip().endswith("?")),
        "first_role": first.get("role") if first else None,
        "first_pos": first.get("pos") if first else None,
    }, stripped, frame


def capture_utterance(agent, text):
    signals, stripped, frame = kind_signals_current(agent, text)
    rec = {
        "text": text,
        "signals": signals,
        "ladder_kind": ct._classify_kind(stripped, frame),
    }
    # The full front-end record, written to the graph exactly as converse()
    # does (receive -> comprehend_text -> _write_comprehension_to_graph),
    # WITHOUT any rule pass.
    mid = agent.receive_utterance(text, speech_act=agent.classify_speech_act(text))
    comp = ct.comprehend_text(agent, text)
    agent._write_comprehension_to_graph(mid, comp)
    attrs = agent.s.node(mid)["attrs"]
    rec.update({
        "kind": attrs.get("comp_kind"),
        "dispatch_path": attrs.get("comp_dispatch_path"),
        "predicate": attrs.get("comp_predicate"),
        "content": attrs.get("comp_content"),
        "comp_kind_py": comp.kind,
        "fastpath": bool(comp.fastpath),
        "intent": comp.intent,
    })
    return rec


def main() -> int:
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    out = {"corpus": {}}
    n = 0
    for group, utterances in CORPUS.items():
        recs = []
        for t in utterances:
            recs.append(capture_utterance(agent, t))
            n += 1
        out["corpus"][group] = recs
    out["n_utterances"] = n
    path = os.path.join(FIXTURE_DIR, "speech_act.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {path} ({n} utterances)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
