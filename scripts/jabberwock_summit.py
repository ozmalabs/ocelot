"""jabberwock_summit — THE SUMMIT (Phase 5): read UNSEEN real Aesop fables
end-to-end through the WHOLE committed comprehension + analysis stack and
report, HONESTLY, what generalizes and what is bounded by finite content.

This is the generalization test of the stack. It adds NO capability: every
decision is made by the already-committed comprehension components
(`comprehension_reader.read_and_comprehend`) and the already-committed
analysis renderer (`literary_analysis.produce_analysis` + `verify_grounding`).
The stack was DEVELOPED on two fables ("The Crow and the Pitcher", "The Mouse
and the Stones"). This harness feeds it fables it has NEVER seen and prints,
verbatim, the comprehension graph + the produced analysis + the claim->graph
grounding for each — then names, per stage, what generalized and what broke.

HONEST TEST, NOT A DEMO. No trope, schema, or parse-fix was added to make an
unseen fable succeed — the summit is THIS script + tests/test_summit.py only.
The value is the honest ledger: the comprehension + arc MECHANISM reads graph
structure and should generalize; the trope/theme is bounded by the finite
3-trope ShapeSignatureTrope codebook (INGENUITY_OVER_STRENGTH / PERSISTENCE_PAYS
/ NECESSITY_INVENTION), so a fable whose moral is gratitude / flattery /
foresight yields an HONEST NULL (the right answer when the codebook doesn't
cover it — a codebook-finiteness finding, not a failure to hide); the parse
may break on unseen constructions. All three outcomes are reported, not tuned
away.

donkey = 0 (no LLM), no `import re`, NEVER git. The chosen fables are short,
public-domain Aesop retellings, none used in development.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                      # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import literary_analysis as la                     # noqa: E402
from domains import narrative_structure as ns                   # noqa: E402


# --------------------------------------------------------------------------- #
#  THE UNSEEN FABLES — short, public-domain Aesop retellings. NONE of these was
#  used in development (dev used the crow + the mouse-and-stones). Each was
#  chosen to probe a DIFFERENT edge of the stack:
#    · The Lion and the Mouse   — a goal/escape arc + a GRATITUDE moral (trope
#      NOT in the 3-trope codebook -> expected honest null).
#    · The Fox and the Crow     — a DECEPTION/FLATTERY moral (trope NOT in the
#      codebook -> expected honest null); tests coref across two animals.
#    · The Ant and the Grasshopper — FORESIGHT/persistence (may partially graze
#      the PERSISTENCE_PAYS signal, or null — reported either way).
# --------------------------------------------------------------------------- #
FABLES = [
    {
        "title": "The Lion and the Mouse",
        "citation": "Aesop, 'The Lion and the Mouse' — traditional public-domain "
                    "retelling. NOT used in development.",
        "text": (
            "A lion was asleep in the sun. A little mouse ran across his paws. "
            "The lion woke and caught the mouse. The mouse begged for its life, "
            "and the lion let it go. Some days later hunters trapped the lion in "
            "a net. The lion could not break the ropes. The mouse heard the lion "
            "and came running. The mouse gnawed the ropes one by one. So the "
            "lion was free."
        ),
        "probe": "GRATITUDE / small-helps-great — a trope NOT in the codebook.",
    },
    {
        "title": "The Fox and the Crow",
        "citation": "Aesop, 'The Fox and the Crow' — traditional public-domain "
                    "retelling. NOT used in development.",
        "text": (
            "A crow held a piece of cheese in her beak. A hungry fox wanted the "
            "cheese. The fox praised the crow's lovely voice. The flattered crow "
            "opened her beak to sing. The cheese fell to the ground. The fox "
            "snatched the cheese and ran away."
        ),
        "probe": "FLATTERY / deception — a trope NOT in the codebook.",
    },
    {
        "title": "The Ant and the Grasshopper",
        "citation": "Aesop, 'The Ant and the Grasshopper' — traditional "
                    "public-domain retelling. NOT used in development.",
        "text": (
            "All summer the grasshopper sang. The ant worked hard. The ant "
            "gathered grain day by day. The grasshopper laughed at the ant. "
            "Then winter came. The grasshopper was cold and hungry. The "
            "grasshopper begged the ant for food. But the ant had none to spare."
        ),
        "probe": "FORESIGHT / persistence — grazes or nulls the codebook.",
    },
]


class _Agent:
    """The same minimal agent shim every domains/*.py test uses."""
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh_agent():
    s, node = boot_core()
    return _Agent(s, node)


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------------------- #
#  READ ONE UNSEEN FABLE COLD — comprehension + analysis + grounding.
# --------------------------------------------------------------------------- #
def read_fable(fable: dict) -> dict:
    agent = _fresh_agent()
    graph = cr.read_and_comprehend(agent, fable["text"], window=2)
    analysis = la.produce_analysis(agent, graph=graph)
    grounding = la.verify_grounding(agent, analysis)
    return {"agent": agent, "graph": graph, "analysis": analysis,
            "grounding": grounding}


# --------------------------------------------------------------------------- #
#  PRINT — comprehension graph, produced analysis, claim->fact grounding.
# --------------------------------------------------------------------------- #
def print_comprehension(agent, graph: dict) -> None:
    _hr("COMPREHENSION — situation model (spine)")
    spine = graph["spine"]
    for tb in spine["textbase"]:
        print("\nSENTENCE:", tb["sentence"])
        print("  predications:", tb["predications"])
    print("\nSITUATION MODEL (resident SmEntity states):")
    for name, state in spine["situation_model"].items():
        print("  %-46s -> %s" % (name, state))
    print("\nPRONOUN RESOLUTIONS:")
    for r in spine["resolutions"]:
        print(" ", r)

    _hr("COMPREHENSION — inferred goal(s)")
    # the need-state CANDIDATES the goal-from-state scan offered (detect_goal_gaps)
    # — printed so the codebook-finiteness is visible: a candidate that decodes to
    # NO remedy is an honest null, not a hidden failure.
    print("  goal-gap CANDIDATES (need-state attrs detected):",
          [(g["entity"], g.get("need_attr")) for g in graph["goal_gaps"]] or "(none)")
    minted = [g for g in graph["goal"] if g.get("minted")]
    if not minted:
        print("  MINTED goals: (none — no candidate decoded to a remedy in the "
              "finite need->remedy codebook: thirst/hunger/danger)")
    for g in minted:
        print("  MINTED: entity=%-8s need=%-12s remedy=%s"
              % (g["gap"]["entity"], g["gap"].get("need_attr"),
                 (g.get("supplies") or {}).get("remedy")))

    _hr("COMPREHENSION — discourse coherence + centrality summary")
    for p in graph["discourse"]["pairs"]:
        print("  (%d,%d) %-24s -> %-12s | %s"
              % (p["i"], p["j"], p["trigger"], p["relation"], p.get("note", "")))
    print("\nCENTRALITY RANKING (most central first):")
    for row in graph["centrality"]["ranking"]:
        print("  degree=%d  %s" % (row["degree"], row["label"]))

    _hr("COMPREHENSION — narrative arc (story-grammar roles)")
    arcs = (graph["narrative_arc"] or {}).get("arcs") or []
    if not arcs:
        print("  (no arc recognised)")
    for arc in arcs:
        ent = arc.get("entity")
        print("\n  ARC entity=%s" % ent)
        for r in ns.read_narrative_roles(agent, ent):
            print("    order=%s role=%-10s token=%-18s schema=%s"
                  % (r.get("order"), r.get("role"), r.get("token"),
                     r.get("schema")))

    _hr("COMPREHENSION — recognised trope(s) + theme")
    for res in (graph["trope_theme"] or {}).get("results") or []:
        print("\n  entity=%s  tokens=%s" % (res.get("entity"), res.get("tokens")))
        tropes = res.get("tropes") or []
        if not tropes:
            print("    TROPE: (none)  ->  %s" % res.get("reason", ""))
        for t in tropes:
            print("    TROPE: %s  label=%s" % (t.get("name"),
                  (t.get("label") or {}).get("name")))
        theme = res.get("theme")
        if theme and theme.get("minted"):
            print("    THEME:", " ".join(str(l) for l in theme.get("lines") or []))
        else:
            print("    THEME: (none — no trope fired)")


def print_analysis(analysis: dict, grounding: dict) -> None:
    _hr("PRODUCED ANALYSIS (verbatim prose)")
    print(analysis["text"] or "(empty)")

    _hr("CLAIM -> GRAPH-FACT MAP (every sentence traced to graph nodes)")
    for sent, info in analysis["claim_map"].items():
        print("[%s/%s] pointers=%s" % (info["section"], info["kind"], info["pointers"]))
        print("   ", sent)

    _hr("verify_grounding (the anti-hallucination gate)")
    print("  ok=%s  checked=%d  unresolved=%s"
          % (grounding["ok"], grounding["checked"], grounding["unresolved"][:5]))
    print("  produced=%d  framed=%d"
          % (analysis["produced_count"], analysis["framed_count"]))


# --------------------------------------------------------------------------- #
#  DRIVER.
# --------------------------------------------------------------------------- #
def run() -> list:
    out = []
    for fable in FABLES:
        _hr("UNSEEN FABLE: " + fable["title"])
        print(fable["citation"])
        print("PROBE:", fable["probe"])
        print("\n" + fable["text"])
        rec = read_fable(fable)
        print_comprehension(rec["agent"], rec["graph"])
        print_analysis(rec["analysis"], rec["grounding"])
        out.append({"fable": fable, **rec})
    return out


def main() -> list:
    results = run()
    _hr("SUMMIT VERDICT (grounding gate per fable)")
    for r in results:
        g = r["grounding"]
        tt_res = (r["graph"]["trope_theme"] or {}).get("results") or []
        fired = [t.get("name") for res in tt_res for t in (res.get("tropes") or [])]
        print("  %-28s grounding_ok=%s  tropes_fired=%s"
              % (r["fable"]["title"], g["ok"], fired or "NULL (honest — codebook finite)"))
    return results


if __name__ == "__main__":
    main()
