"""COMPREHENSION FRONTIERS IN THE REAL master_tick LOOP — one unified understand-Drive curiosity loop.

The pivot's structural step: the frontiers that arise from READING (my gap-as-POS / resolve pipeline) become
first-class understand-drive CapabilityAxes in the agent's REAL loop — picked by the same understand Drive,
investigated by the same investigation machinery, banked by the same bank rule — as master_tick(); tick().

Per utterance: comprehend on the agent's substrate (parse gaps -> ground -> compose -> resolve). Resolvable
(held/learned/relation) -> answered. UNRESOLVED -> a CapabilityAxis (capability_keys=["understand", utt],
shortfall=residual) --investigated_by--> ONE comprehend_frontier Operator --applies_in--> a Microtheory the
agent operates_in. Then the loop is literally master_tick(); tick(): the understand Drive picks the highest-
shortfall axis (its frontier pick), mints a PlanAct, binds the operator, the investigation reflex runs the
frontier world's execute() (resolve-or-learn-from-teacher + persist), banks a MeasuredCapability, the bank rule
drops the shortfall, the frontier SHIFTS. The agent decides WHAT to investigate; the host only fetches the
teacher's answer for the frontier the agent picked.

Run:  PYTHONPATH=.:runners/dsl/python python3 scripts/comprehension_in_master_tick.py [ticks]
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains import construction_grammar as cg
from domains import question_driver as qd
from domains import reflective_faculty as rf

SEP = "=" * 98
SEEDS = ["enact", "discourse", "autonomy", "investigation_loop", "investigation_teacher"]

READING = [
    "Why would your plan lead you into a wall?",          # already learned (persisted) -> answered, no frontier
    "Why does a wall block the avatar?",                  # fresh -> a frontier the master_tick loop investigates
    "Why does residual drive curiosity?",
    "Why does a gap become a frontier?",
]

# The TEACHER is now a CORPUS the agent reads — not a hand-keyed oracle. When it investigates a frontier it
# RETRIEVES the best-matching passage by overlapping the frontier's own content gaps (its POS faculty's nouns/
# verbs) with each passage. Donkey-free lexical retrieval; distractors must not win.
CORPUS = [
    "a wall blocks the avatar because it is a cell the model marks impassable",
    "residual is what drives curiosity since it is the unexplained part of the model",
    "a gap becomes a frontier when it names exactly what is unknown and well posed",
    "the cochlea transforms sound into frequency bands along the basilar membrane",   # distractor
    "a stroke is a pen movement that composes a handwritten character on the page",   # distractor
]


def retrieve_from_corpus(utt, s):
    """Find the passage that best answers the frontier — by overlap of the frontier's CONTENT gaps (the agent's
    own typed nouns/verbs) with each passage's words. The agent's reading, not a hand-keyed answer."""
    gaps = cg.parse_with_gaps(utt, s).get("gaps", [])
    cw = {g["surface"].strip(",.;:?!").lower() for g in gaps if g.get("pos") in ("noun", "verb", "adj", "adv")}
    best, best_score = None, 0
    for p in CORPUS:
        words = {w.strip(",.;:?!").lower() for w in p.split()}
        sc = len(cw & words)
        if sc > best_score:
            best, best_score = p, sc
    return best if best_score >= 1 else None


class ComprehensionFrontierWorld:
    """A thin world: execute() ENACTS the comprehend_frontier operator the loop bound — resolve the frontier's
    relation from held/learned knowledge, else learn it from the teacher (persisted). No WHAT-decision here."""
    def __init__(self, adapter):
        self.a, self.s = adapter, adapter.s

    def register_affordances(self):
        pass

    def execute(self, req):
        keys = req.get("capability_keys") or []
        utt = keys[1] if len(keys) > 1 else (keys[0] if keys else "")
        rel = cg.compose_relation(cg.parse_with_gaps(utt, self.s))
        resolved = cg.resolve_focus(rel, [], self.s)
        if not resolved:
            ans = retrieve_from_corpus(utt, self.s)               # READ the corpus for the answer (not a dict)
            if ans:                                               # learn LIVE (persistence proven elsewhere;
                self.s.add_node("ResolvedQuery",                  # this demo stays repeatable, seed untouched)
                                {"key": cg.relation_key(rel), "focus": rel.get("focus") or "ask", "answer": ans})
                resolved = ans
        measured = 1.0 if resolved else 0.0
        return self.s.add_node("MeasuredCapability", {
            "measured": measured, "target": float(req.get("target", 1.0) or 1.0),
            "metric": req.get("measurement_key", "resolved"), "synth_pending": 1,
            "note": f"{'resolved' if measured else 'unresolved'}: {utt[:46]} -> {str(resolved)[:54]}"})


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    print(SEP)
    print("COMPREHENSION FRONTIERS IN master_tick — read -> understand-drive axes -> the agent investigates them")
    print(SEP)
    a = WorldAdapter()
    for sid in SEEDS:
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid!r} skipped: {e})")
    cg.load_resolved_queries(a.s)                            # carry over what was learned in prior sessions

    # the frontier world + its microtheory/operator (the agent operates_in it; the operator applies_in it)
    world = ComprehensionFrontierWorld(a); world.register_affordances()
    mt = a.s.add_node("Microtheory", {"name": "comprehension_frontier_world"})
    a.inner.add_edge_unchecked(a.agent, "operates_in", mt)
    op = a.s.add_node("Operator", {"name": "comprehend_frontier", "runner": "comprehend_frontier",
                                   "metric": "resolved", "target": 1.0})
    a.inner.add_edge_unchecked(op, "applies_in", mt)

    # READ -> mint understand-drive frontiers for the unresolved
    print("\nREAD (comprehend on the agent's substrate; the unresolved become understand-drive frontiers):")
    drv = qd.QuestionDriver(substrate=a.s)
    minted_axes = []
    for utt in READING:
        emi = drv.drive(qd.QuestionPack(text=utt, reflect=rf.reflect))
        rel = cg.compose_relation(cg.parse_with_gaps(utt, a.s))
        resolved = cg.resolve_focus(rel, emi.subgoals, a.s)
        if resolved:
            print(f"  KNOWN: '{utt}' -> {resolved[:70]}")
        else:
            ung = sum(1 for sg in emi.subgoals if getattr(sg, "is_wall", True))
            ax = a.s.add_node("CapabilityAxis", {
                "is_axis": 1.0, "capability_keys": ["understand", utt], "saturation": 0.0,
                "shortfall": 1.0 + float(ung), "min_order": 1.0, "investigated_count": 0, "mf_stall": 0})
            a.inner.add_edge_unchecked(ax, "investigated_by", op)
            minted_axes.append(ax)
            print(f"  FRONTIER: '{utt}' (shortfall {1.0+ung:.1f})")
    minted = len(minted_axes)

    a.wire_autonomy_faculty(); a.wire_enact_faculty(); a.wire_investigation_faculty(world)

    print(f"\nticking master_tick(); tick() — the understand Drive picks among {minted} frontiers and investigates:\n")
    seen = set()
    for t in range(1, n_ticks + 1):
        a.master_tick(); a.tick()
        for mc in a.s.nodes("MeasuredCapability"):
            if mc in seen:
                continue
            seen.add(mc)
            print(f"  [t{t:2d}] {a.s.node(mc)['attrs'].get('note', '')[:96]}")

    print("\nfinal frontier shortfalls (the Drive re-ranked + shifted each tick):")
    for ax in a.s.nodes("CapabilityAxis"):
        at = a.s.node(ax)["attrs"]
        if at.get("is_axis") == 1.0 and at.get("capability_keys", [None])[0] == "understand":
            print(f"    {at['capability_keys'][1][:54]:54} shortfall={at['shortfall']:.3f}  "
                  f"investigated={at.get('investigated_count')}")

    print("\nRE-ASK (every utterance now resolves):")
    ok = 0
    for utt in READING:
        rel = cg.compose_relation(cg.parse_with_gaps(utt, a.s))
        r = cg.resolve_focus(rel, [], a.s)
        ok += bool(r)
        print(f"  '{utt}' -> {str(r)[:74]}")

    # the master_tick loop must have INVESTIGATED the minted frontiers (their shortfall dropped), not just
    # resolved the pre-known one from persistence.
    investigated = sum(1 for ax in minted_axes if a.s.node(ax)["attrs"].get("investigated_count", 0) > 0)
    print(f"\n  minted {minted} fresh frontiers; the loop investigated {investigated} of them "
          f"(the bank rule drops shortfall gradually; each was picked + run by the understand Drive).")
    print("\n" + SEP)
    allok = ok == len(READING) and minted > 0 and investigated == minted
    print(f"  {'PASS' if allok else 'PARTIAL'} — reading-frontiers are first-class understand-drive axes in the")
    print("  REAL master_tick loop: the SAME Drive picked them by residual, the SAME investigation machinery")
    print("  ran the frontier world (resolve, else learn from the teacher), the SAME bank rule dropped the")
    print("  unified curiosity loop — comprehension is now part of what the agent autonomously investigates.")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
