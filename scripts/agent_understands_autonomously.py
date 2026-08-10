"""THE COGNITIVE MACHINERY: fed raw text, the jabberwock understands it INDEPENDENTLY.

The point is not the poem's answers — it is the machinery that lets the agent do it on its own.
Host does TWO things only: feed the raw text, then pump master_tick()/tick(). Everything else is
the agent's own standing loop:
  perceive (tokenise+comprehend) -> each UNRESOLVED word becomes a FRONTIER
  (mint_frontier_from_unresolved_mention) -> the understand-drive's frontier_pick ranks it ->
  mint_investigation_plan -> bind_investigation_faculty (the graph JOIN, no Python if) ->
  _run_investigation_reflex runs the bound word-faculty on the CURRENT frontier word ->
  bank_measurement_to_axis (shortfall *= 0.5) -> the frontier RE-RANKS and SHIFTS to the next
  unknown word. No per-step Python decides which word or which faculty.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_understands_autonomously
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
RAW = ("'Twas brillig, and the slithy toves did gyre and gimble in the wabe; "
       "all mimsy were the borogoves, and the mome raths outgrabe.")

# The held word-faculty, as a Term that reads the CURRENT frontier word itself (agent ->
# frontier_pick -> axis -> about_mention -> Mention) and returns its sound-affect. The loop
# decides WHEN to run it and on WHICH word; the faculty just reads the frontier.
def _examine_word_term():
    # FIX (faculty_reads_its_bound_item): read the word from the axis the act is BOUND to (passed
    # in as 'axis' by _run_investigation_reflex), not the global frontier_pick that can shift.
    m = {"type": "Pick", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "axis"},
         "edge_type": "about_mention", "any_type": False}}
    text = {"type": "Attr", "node": m, "key": "text"}
    def sim():
        return {"type": "BlendCover", "unknown": text,
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
    print("THE COGNITIVE MACHINERY — fed raw text, the jabberwock understands it on its own (pump only)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "shape_sense", "jabberwocky",
                "autonomy", "investigation_loop", "perception_frontiers"):
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid}: {e})")
    a.author_subroutine("examine_word", _examine_word_term(),
                        purpose="read the current frontier word and return its sound-affect")

    # HOST ACTION 1 of 2: feed the raw text. The adapter tokenises + comprehends it.
    mid = a.add_inbound(RAW)
    a.comprehend()
    toks = [a.s.node(m)["attrs"].get("text") for m in a.inner.neighbours(mid, "has_mention")]
    print(f"\n  fed raw text; agent tokenised {len(toks)} words and comprehended them.")

    base_axes = len(a.s.nodes("CapabilityAxis"))
    # HOST ACTION 2 of 2: pump. No per-step decisions.
    investigated = []
    for t in range(60):
        a.master_tick()
        a.tick()
        # observe (read-only) what the agent banked this tick — its own choices
        for mc in a.s.nodes("MeasuredCapability"):
            at = a.s.node(mc)["attrs"]
            if "examine_word" in str(at.get("note", "")) and mc not in [x[0] for x in investigated]:
                ax = next((x for x in a.inner.neighbours(mc, "measures_axis")), None)
                word = a.s.node(ax)["attrs"].get("word") if ax is not None else "?"
                investigated.append((mc, word, at.get("measured")))

    word_axes = [n for n in a.s.nodes("CapabilityAxis")
                 if a.s.node(n)["attrs"].get("kind") == "understand_word"]
    print(f"  the agent minted {len(word_axes)} word-frontiers from the unknowns it perceived "
          f"(was {base_axes} axes before).")
    print(f"\n  what the agent did ON ITS OWN (it chose each word + ran its faculty; host only pumped):")
    for _, word, val in investigated:
        feel = "menacing" if (val or 0) < -0.02 else ("joyful" if (val or 0) > 0.02 else "neutral")
        print(f"    investigated {word!r:12} -> affect {val:+.2f} ({feel})" if isinstance(val, (int, float))
              else f"    investigated {word!r}")
    print(f"\n  {len(investigated)} unknown words understood autonomously, "
          f"each picked + dispatched by the agent's own loop.")
    print("\n" + SEP)
    print("  The machinery, not the answers: fed only raw text and a pump, the agent turned each word "
          "it could not explain into a frontier, chose it, brought a faculty to it, banked the result, "
          "and moved to the next — its own understand-loop, no orchestration.")
    print(SEP)


if __name__ == "__main__":
    main()
