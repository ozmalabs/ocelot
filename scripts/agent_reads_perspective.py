"""PERSPECTIVE — the deictic ORIGIN under the meaning ladder (the basics: person / POV / focalization /
tense / reliability), jabberwock-designed.

Perspective is not another rung — it is the zero-point displacement is measured from: a four-coordinate
Origin node (I = person, here = vantage, now = tense, whose-eyes = focalization). Three STRUCTURAL counts
feed two derived classifications:
  PERSON       = pronoun-class tally (first/second/third) — a marker count, robust like the simile test;
  TENSE        = verb-morphology tally (past/present/future) — the 'now' coordinate;
  INTERIORITY  = number of distinct minds whose inner states are reported;
  POV          = derived: person x interiority-breadth (first-person / third-limited / third-omniscient / objective);
  FOCALIZATION = mapped off interiority-breadth (internal / zero / external);
  RELIABILITY  = the suspect-witness trust pointed at the narrator Origin (the Humpty pattern).
The counts are mechanical text reads; the PERSON/POV/FOCALIZATION decision is the agent's graph rule.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_perspective
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
P1 = {"i", "me", "my", "mine", "we", "us", "our", "ours", "myself"}
P2 = {"you", "your", "yours", "yourself", "yourselves"}
P3 = {"he", "him", "his", "she", "her", "hers", "they", "them", "their", "it", "its"}
SUBJ = {"i", "we", "you", "he", "she", "they"}
MENTAL = {"felt", "feel", "feels", "knew", "know", "knows", "thought", "thinks", "believed",
          "wondered", "wonders", "feared", "fears", "hoped", "realized", "remembered", "sensed"}
PAST = {"was", "were", "had", "felt", "knew", "walked", "feared", "sat", "lit", "said", "wondered",
        "entered", "slept", "reached", "woke", "guessed"}
PRESENT = {"is", "are", "am", "wake", "reach", "remember", "do", "does", "walks", "feels", "knows"}
FUTURE = {"will", "shall"}

# (label, text, contradicted?) — the last is an unreliable first-person narrator.
PASSAGES = [
    ("first-person",     "I walked into the room. I felt afraid. I knew nothing of what waited for me.", False),
    ("second-person",    "You wake. You do not remember the room. You reach for the door and it will not open.", False),
    ("third-omniscient", "She feared the worst. Across town, he knew the truth she would never guess. The city slept.", False),
    ("third-limited",    "She walked into the hall. She felt afraid. She wondered what he wanted of her.", False),
    ("objective",        "He entered. He sat down. He lit a cigarette and said nothing.", False),
    ("unreliable",       "I am perfectly calm and I remember everything with total clarity.", True),  # depicted events contradict
]


def _counts(text):
    toks = re.findall(r"[a-z']+", text.lower())
    n1 = sum(t in P1 for t in toks); n2 = sum(t in P2 for t in toks); n3 = sum(t in P3 for t in toks)
    minds, last = set(), None
    for t in toks:
        if t in SUBJ:
            last = t
        if t in MENTAL and last is not None:
            minds.add(last)
    p = sum(t in PAST or t.endswith("ed") for t in toks)
    pr = sum(t in PRESENT for t in toks); fu = sum(t in FUTURE for t in toks)
    tense = "future" if fu and fu >= p else ("present" if pr > p else "past")
    return n1, n2, n3, len(minds), tense


def main():
    print(SEP)
    print("PERSPECTIVE — the deictic origin: person / POV / focalization / tense / reliability")
    print(SEP)
    a = boot()
    for s in ("perspective",):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    print()
    for label, text, contradicted in PASSAGES:
        n1, n2, n3, minds, tense = _counts(text)
        seg = a.s.add_node("Segment", {"text": text})
        o = a.s.add_node("Origin", {"n1": n1, "n2": n2, "n3": n3, "minds": minds, "tense": tense,
                                    "narrator_trust": 0.9})
        a.inner.add_edge_unchecked(o, "origin_of", seg)
        a.inner.run_rules(10000)                          # classify_perspective derives person/POV/focalization
        at = a.s.node(o)["attrs"]
        # RELIABILITY reuses suspect-witness: narration contradicted -> refute -> trust halves (Humpty pattern)
        if contradicted:
            a.inner.set_attr(o, "narrator_trust", at["narrator_trust"] * 0.5)
        trust = a.s.node(o)["attrs"]["narrator_trust"]
        rel = "unreliable" if trust < 0.6 else "reliable"
        print(f"  [{label}]  {text!r}")
        print(f"      person={at['person']}  POV={at['point_of_view']}  focalization={at['focalization']}  "
              f"tense={at['tense']}  (pronouns 1/2/3={n1}/{n2}/{n3}, minds={minds})")
        print(f"      reliability={rel} (narrator_trust={trust:.2f})"
              f"{'  <- narration contradicted by depicted events (suspect-witness refute)' if contradicted else ''}\n")

    print(SEP)
    print("  Perspective is the ORIGIN the displacement ladder is measured from, not a rung on it: three")
    print("  structural counts (pronoun person, verb tense, interiority-minds) on one deictic Origin node,")
    print("  with POV and focalization DERIVED from them (so they inherit the structural robustness) and")
    print("  reliability the suspect-witness trust pointed at the narrator. These were the missing basics")
    print("  under figure -> analysis -> voice -> ... -> genre; now the frame the whole ladder reads against.")
    print(SEP)


if __name__ == "__main__":
    main()
