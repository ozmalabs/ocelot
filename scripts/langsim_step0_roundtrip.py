"""langsim STEP-0 probe: a REAL graph-emitted utterance round-trip (no LLM, no templates).

Generation: WorldAdapter.utterance_for(meaning) -> surface string via the graph
lexicon + the Rust Render engine (RenderRules). Comprehension: receive_utterance
+ comprehend() runs the seeded intent/referent Rules; we read the parse back off
the graph. This is the STEP-0 gate: prove the graph machinery produces + parses a
real utterance about world entities before building the sim.
"""
from __future__ import annotations
import os, sys
_GB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_GB, "runners", "dsl", "python"))
sys.path.insert(0, _GB)

from substrate.world_adapter import WorldAdapter


def gen_probe(meaning):
    a = WorldAdapter()
    # ground the content signs the way the speech faculty does (learn_sign =
    # graph-resident Sign nodes, surface<->concept). Mechanical vocabulary install.
    def _ground(m):
        if isinstance(m, dict):
            for k, v in m.items():
                a.learn_sign(k, k)
                _ground(v)
        elif isinstance(m, str):
            a.learn_sign(m, m)
    _ground(meaning)
    utt = a.utterance_for(meaning)
    return utt


def comp_probe(text):
    a = WorldAdapter()
    a.attach_chat_world("partner")
    mid = a.receive_utterance(text, speech_act="statement", speaker="partner")
    n_apps = a.comprehend()
    intent = a.intent_of(mid)
    # read back the mentions + what they resolved to
    mentions = []
    for mn in a.inner.neighbours(mid, "has_mention"):
        attrs = a.s.node(mn)["attrs"]
        refs = list(a.inner.neighbours(mn, "refers_to"))
        ref_names = [a.s.node(r)["attrs"].get("name") for r in refs]
        mentions.append((attrs.get("text"), ref_names))
    intent_attrs = a.s.node(intent)["attrs"] if intent is not None else None
    return dict(n_apps=n_apps, intent=intent_attrs, mentions=mentions)


if __name__ == "__main__":
    print("=== GENERATION (graph render of a relational communicative intent) ===")
    for meaning in [
        {"have": {"of": "wood"}},
        {"give": {"of": "stone"}},
        {"trade": {"of": "wood"}},
        {"determinant": {"of": "M"}},
    ]:
        utt = gen_probe(meaning)
        print(f"  intent={meaning!r}")
        print(f"    -> utterance: {utt!r}")

    print()
    print("=== COMPREHENSION (deep reader parses an utterance back to graph) ===")
    for text in ["I have wood.", "give me stone", "determinant of M"]:
        r = comp_probe(text)
        print(f"  utterance={text!r}")
        print(f"    -> rule apps={r['n_apps']}  mentions+referents={r['mentions']}")
        print(f"    -> intent attrs={r['intent']}")
