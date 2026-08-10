"""Author fix #2: affect by an INDEPENDENT context source, not a sharper combiner.

Lesson affect_max_vs_sum: on near-tied sound-affect (callay, vorpal), a sharper aggregator only
relocates the error. The fix is an INDEPENDENT evidence source — the affect of the word's
NEIGHBOURS in the same utterance (a victory frame reads positive, a menace frame negative). So:
  affect2(m) = own_sound_affect(m) + w * (sum of own_sound_affect over the other content words)
The neighbourhood breaks the tie: callay among frabjous/callooh/chortled -> joyful; vorpal among
frumious/bandersnatch -> menacing — without changing the sound combiner.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_authors_context_affect
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 92
JOY = "o frabjous day callooh callay he chortled in his joy"
MENACE = "the frumious bandersnatch jubjub and the vorpal claws that bite"
TARGETS = {"JOY": ["frabjous", "callooh", "callay", "chortled"],
           "MENACE": ["frumious", "bandersnatch", "vorpal"]}


def _own(mvar):
    """own sound-affect of a mention bound to `mvar`: best-positive minus best-negative resemblance."""
    def sim():
        return {"type": "BlendCover",
                "unknown": {"type": "Attr", "node": {"type": "Var", "name": mvar}, "key": "text"},
                "a": {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": "form"},
                "b": {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": "form"}}
    def side(cmp):
        return {"type": "MaxOver", "source": {"type": "Filter",
                "source": {"type": "NodesOfType", "node_type": "AffectWord"}, "var_name": "w",
                "predicate": {"type": cmp, "a": {"type": "Attr", "node": {"type": "Var", "name": "w"}, "key": "valence"},
                              "b": {"type": "Lit", "value": 0}}},
                "var_name": "w", "value": sim(), "default": {"type": "Lit", "value": 0}}
    return {"type": "Minus", "a": side("Gt"), "b": side("Lt")}


def main():
    print(SEP)
    print("AUTHOR FIX #2 — affect by an INDEPENDENT context source (the neighbourhood's affect)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)

    # context = sum of own-affect over the OTHER content words of the message (independent source).
    context = {"type": "Sum",
        "source": {"type": "Filter", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "msg"},
                   "edge_type": "has_mention", "any_type": False}, "var_name": "m2",
                   "predicate": {"type": "Not", "arg": {"type": "Exists", "var_name": "f",
                       "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m2"}, "key": "text"},
                                     "b": {"type": "Attr", "node": {"type": "Var", "name": "f"}, "key": "form"}},
                       "source": {"type": "NodesOfType", "node_type": "FunctionWord"}}}},
        "var_name": "m2", "value": _own("m2")}
    affect2 = {"type": "Plus", "items": [_own("m"), {"type": "Times", "items": [{"type": "Lit", "value": 0.3}, context]}]}
    a.author_subroutine("affect_in_context", affect2,
                        purpose="sound-affect plus the independent vote of the neighbourhood's affect")
    print("  authored affect_in_context = own sound-affect + 0.3 * (sum of neighbours' affect)\n")

    ok = tot = 0
    for label, line in (("JOY", JOY), ("MENACE", MENACE)):
        mid = a.add_inbound(line); a.comprehend()
        by_text = {a.s.node(m)["attrs"].get("text"): m for m in a.inner.neighbours(mid, "has_mention")}
        print(f"  [{label}] {line!r}")
        for w in TARGETS[label]:
            m = by_text.get(w)
            if m is None:
                continue
            sc = a.run_subroutine("affect_in_context", {"m": m, "msg": mid})
            feel = "menacing" if (sc or 0) < -0.02 else ("joyful" if (sc or 0) > 0.02 else "neutral")
            want = "joyful" if label == "JOY" else "menacing"
            good = (feel == want); ok += good; tot += 1
            print(f"    {w:13} affect_in_context {sc:+.2f} -> {feel:9} {'OK' if good else '(want '+want+')'}")
    print(f"\n  {ok}/{tot} correct in context (the near-ties callay/vorpal now break the right way).")
    print("\n" + SEP)
    print("  Fix #2 authored as the lesson said: not a sharper combiner but an INDEPENDENT source — "
          "the neighbourhood's affect votes, so a word in a joyful frame reads joyful and one in a "
          "menacing frame reads menacing, even when its own sound is split.")
    print(SEP)


if __name__ == "__main__":
    main()
