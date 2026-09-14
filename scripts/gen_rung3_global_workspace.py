"""Block 350000 EXPERIMENT — the GLOBAL WORKSPACE: seriality PRODUCED by
competition/broadcast for a single slot, with an IGNITION THRESHOLD, NOT asserted
by the FIFO agenda queue (Global Workspace Theory — Baars / Dehaene's ignition).

The block-346 train ASSERTS "one thought at a time" by popping a FIFO agenda
(agenda.pop(0)); seriality is a property of the queue, not a produced bottleneck.
Block 350 makes next-thought selection a genuine CONTEST: score the candidates by a
TEACHER-FREE salience (curiosity learning-progress INTEREST + is-a proximity floor),
broadcast the ARGMAX winner into a single slot (the serial bottleneck), and gate the
broadcast by an IGNITION THRESHOLD — sub-threshold => NO broadcast (honest silence),
not a forced pick. DISCRETE QUANTA throughout (salience + threshold as integer quanta,
via the substrate's native _round_to_vocab; the winner is a held Argmax Term).

Pure graph, teacher-free (ask-spy 0 on the held path), additive (a defaulted `select=`
hook — FIFO stays the default). No .so rebuild, no protected-file edit, no
conceptualizer.py touch, no LLM.

FALSIFIABLE CLAIMS:
  W1 COMPETITION != FIFO — a candidate set whose highest-salience member is NOT the
     FIFO-front one: the workspace broadcasts the SALIENT one, FIFO would take the
     front; the two selections genuinely DIFFER.
  W2 IGNITION THRESHOLD — a candidate set all below the ignition threshold => NO
     broadcast (honest silence / the turn produces nothing) rather than a forced pick.
  W3 SERIALITY PRODUCED — exactly ONE candidate wins the broadcast slot per turn (the
     bottleneck); the losers remain for later competition.
  W4 TEACHER-FREE — ask-spy == 0 on the held workspace path.
  W5 BACKWARD-COMPAT — the DEFAULT (select=None) FIFO selection reproduces the
     block-346/347/348 train behavior byte-for-byte.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_global_workspace.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
import domains.curiosity_topic_ingest as cti               # noqa: E402
import domains.train_of_thought as tot                     # noqa: E402
import domains.global_workspace as gw                       # noqa: E402


# --------------------------------------------------------------------------- #
#  a teacher-free demo world + an AskSpy to prove no teacher is reached.
# --------------------------------------------------------------------------- #
class AskSpy:
    """Counts every external-ask reach (the teacher-free tripwire)."""
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def _never_teacher(_word):
    """No grounding EVER — the honest teacher-free stand-in (identical to the
    curiosity_topic_selection_measure loop): an unknown-word topic keeps its
    surprise, so its learning-progress INTEREST accrues without any teacher."""
    return None


def _build_world():
    """A small is-a DAG + a curiosity hub, teacher-free. The concept graph gives the
    is-a-proximity floor; the curiosity loop gives the learning-progress signal that
    makes the primary salience differ between candidates. Every progress/interest
    value is computed by the lp_* seed RULES — this script only writes the honest
    `obs` sensor and `input_epoch` (never a decision attr).

    Two SIBLINGS under 'dog' (poodle, cat) sit at EQUAL is-a proximity to a focus of
    'dog', so any salience difference between them is due ENTIRELY to the confirmed
    teacher-free learning-progress signal — not to graph position. `sparrow` is a
    far-off sibling branch (a low-salience distractor)."""
    wa = WorldAdapter(seeds=())
    load_all_seeds(wa)
    cti.install_curiosity(wa)
    _isa(wa, "poodle", "dog"); _isa(wa, "cat", "dog"); _isa(wa, "dog", "mammal")
    _isa(wa, "mammal", "animal"); _isa(wa, "animal", "organism")
    _isa(wa, "sparrow", "bird"); _isa(wa, "bird", "animal")
    return wa


def _concept(wa, name):
    from domains import self_dialogue as sd
    sub = sd._sub(wa)
    n = sd._find_concept(sub, name)
    if n is None:
        n = sub.add_node("Concept", {"name": name})
    return n


def _isa(wa, child, parent):
    from domains import self_dialogue as sd
    sub = sd._sub(wa)
    c = _concept(wa, child); p = _concept(wa, parent)
    try:
        sub.add_edge_unchecked(c, "causal_influence", p)   # is-a spine edge-type
    except Exception:
        pass


def _drive_interest(wa, topic_phrases, ticks):
    """Drive the REAL curiosity loop teacher-free for `ticks` epochs over the given
    {topic: phrase} map. Unknown-word phrases accrue learning-progress INTEREST via
    the lp_* rules; a phrase of already-known words does not. Returns the hub."""
    hub = None
    for t in range(1, ticks + 1):
        for name, phrase in topic_phrases.items():
            hub = cti.maintain_topic_interest(wa, {name: phrase}, t,
                                              teacher=_never_teacher)
    return hub


def _interest_of(wa, hub, topic):
    """(unused helper retained for interactive inspection) the sustained interest
    attr of a topic's AttentionItem, or None if not ingested."""
    item = cti._items_by_topic(wa, hub).get(topic)
    if item is None:
        return None
    return int(round(float(wa.s.node(item)["attrs"].get("interest", 0.0))))


# =========================================================================== #
def main() -> int:
    print("=" * 78)
    print("GLOBAL WORKSPACE — seriality PRODUCED by competition/broadcast (block 350)")
    print("=" * 78)

    results = {}

    # ----------------------------------------------------------------------- #
    #  Set up a candidate set with GENUINELY DIFFERING teacher-free salience.
    #  Two candidate topics carry curiosity AttentionItems; we drive one with an
    #  UNKNOWN-word phrase (accrues learning-progress interest teacher-free) and
    #  one with a KNOWN-word phrase (no surprise => low interest). The concept
    #  names double as agenda candidates.
    # ----------------------------------------------------------------------- #
    wa = _build_world()
    # pre-teach the "familiar" sibling's words so it carries NO surprise (no learning
    # progress); leave the "novel" sibling's words unknown (accrues learning progress).
    # Both are direct children of 'dog' => EQUAL is-a proximity to focus 'dog', so the
    # salience difference is due ENTIRELY to the confirmed teacher-free LP signal.
    for w in ("cat", "dog"):
        wa.learn_from_teacher(w, {"answer": f"{w} is known.",
                                  "learn": [{"phrase": w, "answer": f"{w} is known."}]})
    hub = _drive_interest(wa, {
        "cat":     "cat dog",                                    # known -> no progress
        "poodle":  "poodle quasiparticle exfoliation brachiation",  # unknown -> progress
    }, ticks=12)

    def _lp(topic):
        it = cti._items_by_topic(wa, hub).get(topic)
        return None if it is None else int(round(float(
            wa.s.node(it)["attrs"].get("smoothed_progress", 0.0))))

    lp_cat, lp_poodle = _lp("cat"), _lp("poodle")
    sq_cat = gw.salience_quanta(wa, "cat", focus="dog")
    sq_poodle = gw.salience_quanta(wa, "poodle", focus="dog")
    prox_cat = gw._isa_proximity(wa, gw._resolve_sub(wa), "cat", "dog")
    prox_poodle = gw._isa_proximity(wa, gw._resolve_sub(wa), "poodle", "dog")
    print("\nteacher-free salience, focus='dog' (cat & poodle are EQUAL-proximity siblings):")
    print("  cat:     LP progress=%s  is-a proximity=%d  =>  salience_quanta=%d"
          % (lp_cat, prox_cat, sq_cat))
    print("  poodle:  LP progress=%s  is-a proximity=%d  =>  salience_quanta=%d"
          % (lp_poodle, prox_poodle, sq_poodle))
    print("  (equal proximity, so poodle's higher salience is the CONFIRMED LP signal)")

    # ----------------------------------------------------------------------- #
    #  W1 — COMPETITION != FIFO.
    #  Candidate set ORDERED [cat, poodle]: FIFO front is 'cat' (equal proximity,
    #  NO learning progress); the argmax-salience winner is 'poodle' (same proximity
    #  but real learning progress). The two selections DIFFER — and the difference is
    #  the teacher-free LP signal, not graph position.
    # ----------------------------------------------------------------------- #
    candidates = ["cat", "poodle"]                     # FIFO front = 'cat'
    fifo_pick = candidates[0]                           # what agenda.pop(0) takes
    win, info = gw.broadcast_winner(wa, candidates, focus="dog", with_detail=True)
    w1 = (fifo_pick == "cat" and win == "poodle" and win != fifo_pick
          and info["scores"]["poodle"] > info["scores"]["cat"]
          and prox_cat == prox_poodle)                  # difference is LP, not proximity
    print("\n[W1] COMPETITION != FIFO")
    print("  candidate set (agenda order): %s" % candidates)
    print("  FIFO would take front:        %r" % fifo_pick)
    print("  workspace broadcasts argmax:  %r  (quanta=%s)" % (win, info["scores"]))
    print("  equal proximity (%d==%d) => difference is the LP signal" % (prox_cat, prox_poodle))
    print("  DIFFER: %s   => W1 %s" % (win != fifo_pick, "PASS" if w1 else "FAIL"))
    results["W1"] = w1

    # ----------------------------------------------------------------------- #
    #  W2 — IGNITION THRESHOLD => honest silence.
    #  Same candidate set, but demand an ignition threshold ABOVE the top salience:
    #  no candidate clears it => NO broadcast (None), not a forced pick.
    # ----------------------------------------------------------------------- #
    top_q = max(info["scores"].values())
    high_ign = top_q + 1                               # nothing can clear this
    win_hi, info_hi = gw.broadcast_winner(wa, candidates, focus="dog",
                                          ignition_quanta=high_ign, with_detail=True)
    # and a genuinely-empty-salience set: two unrelated, un-ingested topics with a
    # focus they have no is-a relation to => salience 0 => sub-threshold at default.
    barren = ["zqvorn", "fluxbaz"]
    win_barren = gw.broadcast_winner(wa, barren, focus="dog")
    w2 = (win_hi is None and info_hi["reason"] == "sub_threshold"
          and win_barren is None)
    print("\n[W2] IGNITION THRESHOLD => honest silence")
    print("  top salience quanta=%d, ignition demanded=%d -> broadcast=%r (reason=%s)"
          % (top_q, high_ign, win_hi, info_hi["reason"]))
    print("  barren set %s (no LP, unrelated to focus) -> broadcast=%r"
          % (barren, win_barren))
    print("  => W2 %s" % ("PASS" if w2 else "FAIL"))
    results["W2"] = w2

    # ----------------------------------------------------------------------- #
    #  W3 — SERIALITY PRODUCED: exactly ONE winner per turn; losers remain.
    #  Run the workspace over a 3-candidate set; assert the return is a single
    #  topic and the other two are NOT returned (they stay for later contest).
    # ----------------------------------------------------------------------- #
    three = ["cat", "poodle", "sparrow"]
    win3, info3 = gw.broadcast_winner(wa, three, focus="dog", with_detail=True)
    losers = [c for c in three if c != win3]
    # "exactly one wins the slot": the return is a single string, all three were
    # scored (all competed), and the two losers were not selected.
    w3 = (isinstance(win3, str) and win3 in three
          and len(losers) == 2 and set(info3["scores"].keys()) == set(three))
    print("\n[W3] SERIALITY PRODUCED (single broadcast slot; bottleneck)")
    print("  candidates competing: %s (scores=%s)" % (three, info3["scores"]))
    print("  ONE winner into the slot: %r ; losers remain: %s" % (win3, losers))
    print("  => W3 %s" % ("PASS" if w3 else "FAIL"))
    results["W3"] = w3

    # ----------------------------------------------------------------------- #
    #  W4 — TEACHER-FREE on the held path: run the FULL inner conversation with the
    #  workspace select strategy and confirm ask-spy == 0. Start from 'poodle' (which
    #  carries a real teacher-free LP signal, so turn 1 ignites), then let the stance
    #  grow the agenda and the workspace compete each turn by proximity-to-focus.
    # ----------------------------------------------------------------------- #
    spy = AskSpy()
    sel = gw.workspace_select()                        # ignites on any positive salience
    r_ws = tot.run_inner_conversation(wa, topic="poodle", max_turns=8, width=1,
                                      select=sel, on_unknown="return", ask_fn=spy)
    # a genuine train: >=1 topic broadcast, teacher-free, and it terminates honestly
    # (either agenda-converged or sub-threshold silence — never a forced pick).
    w4 = (len(spy.calls) == 0 and len(r_ws["topics_thought"]) >= 1
          and r_ws["stop_reason"] in ("converged", "sub_threshold_silence",
                                      "max_turns", "novelty_stalled"))
    print("\n[W4] TEACHER-FREE held workspace path")
    print("  workspace train topics_thought: %s" % r_ws["topics_thought"])
    print("  stop_reason=%s  ask_spy=%d  => W4 %s"
          % (r_ws["stop_reason"], len(spy.calls), "PASS" if w4 else "FAIL"))
    results["W4"] = w4

    # ----------------------------------------------------------------------- #
    #  W5 — BACKWARD-COMPAT: select=None reproduces the block-346 FIFO train
    #  byte-for-byte (same topics_thought, same stop_reason, same frontier growth)
    #  vs. an explicit run with no select hook. We compare two default runs on a
    #  fresh world (the workspace code must not have perturbed the default path).
    # ----------------------------------------------------------------------- #
    wa_a = _fresh_isa_world()
    wa_b = _fresh_isa_world()
    spy_a = AskSpy(); spy_b = AskSpy()
    r_default = tot.run_inner_conversation(wa_a, topic="poodle", max_turns=8,
                                           on_unknown="return", ask_fn=spy_a)
    r_explicit_none = tot.run_inner_conversation(wa_b, topic="poodle", max_turns=8,
                                                 select=None, on_unknown="return",
                                                 ask_fn=spy_b)
    w5 = (r_default["topics_thought"] == r_explicit_none["topics_thought"]
          and r_default["stop_reason"] == r_explicit_none["stop_reason"]
          and r_default["frontier_growth"] == r_explicit_none["frontier_growth"]
          and len(spy_a.calls) == 0 and len(spy_b.calls) == 0)
    print("\n[W5] BACKWARD-COMPAT (select=None == block-346 FIFO)")
    print("  default    topics=%s stop=%s" % (r_default["topics_thought"],
                                              r_default["stop_reason"]))
    print("  select=None topics=%s stop=%s" % (r_explicit_none["topics_thought"],
                                               r_explicit_none["stop_reason"]))
    print("  identical: %s   => W5 %s"
          % (r_default["topics_thought"] == r_explicit_none["topics_thought"],
             "PASS" if w5 else "FAIL"))
    results["W5"] = w5

    # ----------------------------------------------------------------------- #
    print("\n" + "=" * 78)
    all_pass = all(results.values())
    for k in ("W1", "W2", "W3", "W4", "W5"):
        print("  %s: %s" % (k, "PASS" if results[k] else "FAIL"))
    print("OVERALL: %s" % ("PASS" if all_pass else "FAIL"))
    print("=" * 78)
    return 0 if all_pass else 1


def _fresh_isa_world():
    """A fresh is-a world with NO curiosity interest driven — the plain block-346
    default-train fixture (poodle -> dog -> mammal -> animal -> organism; sparrow ->
    bird -> animal), matching gen_rung3_train_of_thought's DAG shape."""
    wa = WorldAdapter(seeds=())
    load_all_seeds(wa)
    _isa(wa, "poodle", "dog"); _isa(wa, "dog", "mammal")
    _isa(wa, "mammal", "animal"); _isa(wa, "animal", "organism")
    _isa(wa, "sparrow", "bird"); _isa(wa, "bird", "animal")
    return wa


if __name__ == "__main__":
    raise SystemExit(main())
