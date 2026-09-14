"""Block 351000 — GATED DIMENSION-MINTING: the manifold grows an axis when a
residual PERSISTS.

The closing facet of "a train of thought is a trajectory through a manifold".
Blocks 348/349 steer the trajectory to stay in a TUBE by measuring its DEVIATION —
the residual concept_signature tuples the set-point never admitted — and turning
that residual into WIDTH. The residual is otherwise discarded (only its integer
COUNT survives, to steer the width). This block KEEPS the residual and, when the
SAME uncoverable structure RECURS across segments — a PERSISTENT residual — COINS a
new axis for it. Accommodation (grow the space), not gap-fill (patch one miss).

WHAT IS REUSED (honest naming — no minting machinery is invented here):
  · the DECISION is the seeded shape-decode loop's (seeds/shape_decode_loop.json)
    via reflective_faculty.induce_concern — hand it the persistent residual as a
    relation-system, the RULES return `minted` (coin a CapabilityAxis),
    `recognized` (a held axis covers it -> no mint, the null), or
    `recognized_duplicate` (an induced axis with this key already exists -> no
    mint, the over-minting guard against unbounded axis growth);
  · the RESIDUAL is block-349's aperture-grain residual (frozenset(traj)-admitted),
    kept as a SET instead of reduced to len();
  · the width control law and the tube are regulated_train_of_thought's, unchanged.

WHAT IS NEW: run_minting_train_of_thought accumulates an INTEGER per-predicate
PERSISTENCE ledger (+1 for each residual predicate present per segment; a predicate
absent this segment does not advance — a transient miss never accumulates) and
offers the mint gate a predicate ONLY once its persistence reaches an integer
`mint_after_quanta`. DISCRETE QUANTA throughout: persistence counts, the threshold,
and the residual tuples' step k are all integers; no floats, no continuum.

FALSIFIABLE CLAIMS (a teacher-call spy counts external answers; must be 0 held):
  G1  THE MINT GATE WORKS: induce_concern mints a fresh CapabilityAxis on a novel
      residual predicate, and REFUSES (recognized_duplicate) the same predicate a
      second time (the over-minting guard). Reused verbatim.
  G2  PERSISTENT RESIDUAL MINTS: a set-point whose tube the trajectory keeps
      escaping produces a residual predicate that RECURS every segment; once its
      integer persistence reaches mint_after_quanta it mints a new axis. Report the
      residual_trace, the persistence ledger, and the coined axis ids.
  G3  THE GATE IS PERSISTENCE-TIMED (accommodation, not gap-fill): on the SAME run,
      a threshold at/below the residual's max persistence MINTS, a threshold ABOVE
      it MINTS NOTHING — the residual is present every segment but does not persist
      LONG ENOUGH. So a single/transient miss (a 1-segment run) mints nothing.
  G4  DISCRETE QUANTA: every steering + gating quantity is an integer (persistence
      counts, thresholds, deviation, width) — assert no float appears.
  G5  TEACHER-FREE: ask-spy = 0 on the held path (the persistence gate and the
      sd-loop are pure graph reads; no LLM decides).
  G6  ADDITIVE / BACKWARD-COMPAT: run_regulated_train_of_thought is unchanged — its
      aperture-grain run on the SAME seed gives the same deviation/width traces the
      minting loop's control half produces (the minting loop only ADDS the ledger).

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_gated_minting.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

import domains.analogy_search as asr
from domains import minting_train_of_thought as mtot
from domains import reflective_faculty as rf
from domains import regulated_train_of_thought as rtt


VOCAB = "seeds/shape_vocabulary.json"
QUALIA = "seeds/qualia_space.json"


class AskSpy:
    """Counts external-answerer invocations — proves teacher-free."""
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def _seed():
    """The block-349 teacher-free demo graph: an is-a spine with DISTINCT dynamical
    coordinates on each concept (state -> dynamical:valence, identity_field ->
    dynamical:commitment) plus the qualia codebook so concept_signature is genuinely
    multi-axis and grain acts. Pure additive node data + attr writes — no LLM, no
    protected-file edit, no .so rebuild, no touch to conceptualizer.py."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {"name": "jabberwock"})
    for path in (VOCAB, QUALIA):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path, summ)
    asr._QUALIA_SCHEMA_CACHE.clear()

    mt = s.add_node("Microtheory",
                    {"name": "knowledge_isa", "temperature": 1.0,
                     "discrete_mode": "3state"})
    n = {}

    def concept(name, *, state, identity_field, category="animal"):
        c = s.add_node("Concept", {"name": name, "category": category,
                                   "state": float(state), "external_field": 0.0,
                                   "identity_field": float(identity_field)})
        s.add_edge_unchecked(mt, "has_concept", c)
        n[name] = c
        return c

    concept("poodle",   state=1.0,  identity_field=0.8,  category="animal")
    concept("dog",      state=0.5,  identity_field=0.5,  category="animal")
    concept("mammal",   state=0.25, identity_field=0.25, category="animal")
    concept("animal",   state=0.0,  identity_field=0.0,  category="kingdom")
    concept("organism", state=0.0,  identity_field=0.0,  category="kingdom")
    concept("sparrow",  state=-1.0, identity_field=-0.8, category="animal")
    concept("bird",     state=-0.5, identity_field=-0.5, category="animal")

    for a, b in [("poodle", "dog"), ("dog", "mammal"), ("mammal", "animal"),
                 ("animal", "organism"), ("sparrow", "bird"), ("bird", "animal")]:
        s.add_edge_unchecked(n[a], "causal_influence", n[b],
                             {"weight": 1.0, "relation": "isa"})

    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s, n


def _fine_observer(s, name="fine"):
    """A FINE-grain set-point observer: a narrow tube, so the roaming trajectory
    keeps producing residual signature tuples the set-point never admits."""
    return s.add_node("Observer", {"name": name,
                                   "grain": {"dynamical:valence": 0.25,
                                             "dynamical:commitment": 0.25}})


def _all_int(xs) -> bool:
    return all(isinstance(x, int) and not isinstance(x, bool) for x in xs)


def main() -> int:
    print("=" * 78)
    print("GATED DIMENSION-MINTING — the manifold grows an axis when a residual "
          "PERSISTS")
    print("(block 351; discrete quanta; accommodation not gap-fill; teacher-free)")
    print("=" * 78)

    held_spy_total = 0

    # ---------------------------------------------------------------- G1 ----- #
    print("\n" + "-" * 78)
    print("G1  the MINT GATE (reused verbatim): novel residual predicate -> MINT; "
          "same predicate again -> REFUSED (over-minting guard)")
    print("-" * 78)
    s0, _ = _seed()
    r1 = rf.induce_concern(s0, [["novel_residual_pred_alpha"]],
                           name_hint="minted_novel_residual_pred_alpha")
    r2 = rf.induce_concern(s0, [["novel_residual_pred_alpha"]],
                           name_hint="minted_novel_residual_pred_alpha")
    print("  first  observation: minted=%s axis=%s" % (r1.get("minted"),
                                                        r1.get("axis_id")))
    print("         note: %s" % (r1.get("note", "")[:72]))
    print("  second observation: minted=%s" % r2.get("minted"))
    print("         note: %s" % (r2.get("note", "")[:72]))
    g1 = (r1.get("minted") is True and r1.get("axis_id")
          and r2.get("minted") is False)
    print("  G1 %s" % ("PASS" if g1 else "FAIL"))

    # ---------------------------------------------------------------- G2 ----- #
    print("\n" + "-" * 78)
    print("G2  PERSISTENT RESIDUAL MINTS: a tube the trajectory keeps escaping -> "
          "a recurring residual -> once persistence >= mint_after_quanta, a new "
          "axis is coined")
    print("-" * 78)
    s2, _ = _seed()
    ob = _fine_observer(s2)
    spy2 = AskSpy()
    res = mtot.run_minting_train_of_thought(
        s2, topic="poodle", setpoint_observer=ob, setpoint_topic="animal",
        width0=2, turns_per_segment=3, max_segments=6, mint_after_quanta=2,
        on_unknown="return", ask_fn=spy2)
    held_spy_total += len(spy2.calls)
    print("  admitted (set-point) tuple count: %d" % res["admitted_size"])
    print("  residual predicates per segment:")
    for i, rp in enumerate(res["residual_trace"]):
        print("     seg%d: %s" % (i, rp))
    print("  persistence ledger (integer segments each predicate recurred): %s"
          % res["residual_persistence"])
    print("  deviation_trace (int quanta): %s" % res["deviation_trace"])
    print("  width_trace     (int quanta): %s" % res["width_trace"])
    print("  mint_events: %s"
          % [(e["predicate"], e["minted"], e["persistence"])
             for e in res["mint_events"]])
    print("  minted axes (CapabilityAxis ids): %s" % res["minted_axes"])
    persistent = [p for p, k in res["residual_persistence"].items() if k >= 2]
    g2 = (len(persistent) >= 1 and len(res["minted_axes"]) >= 1
          and all(e["persistence"] >= 2 for e in res["mint_events"] if e["minted"]))
    print("  a residual recurred >=2 segments AND minted an axis: %s" % g2)
    print("  G2 %s" % ("PASS" if g2 else "FAIL"))

    # ---------------------------------------------------------------- G3 ----- #
    print("\n" + "-" * 78)
    print("G3  the gate is PERSISTENCE-TIMED (accommodation, not gap-fill): SAME "
          "run — threshold <= max persistence MINTS, threshold > it MINTS NOTHING; "
          "a 1-segment run mints nothing")
    print("-" * 78)
    # find the residual's max persistence over a fixed-length run
    s3a, _ = _seed()
    oba = _fine_observer(s3a)
    spy3 = AskSpy()
    probe = mtot.run_minting_train_of_thought(
        s3a, topic="poodle", setpoint_observer=oba, setpoint_topic="animal",
        width0=2, turns_per_segment=3, max_segments=5, mint_after_quanta=999,
        on_unknown="return", ask_fn=spy3)
    held_spy_total += len(spy3.calls)
    max_persist = (max(probe["residual_persistence"].values())
                   if probe["residual_persistence"] else 0)
    n_segs = len(probe["segments"])
    print("  over a %d-segment run the residual's max persistence = %d"
          % (n_segs, max_persist))

    def _mint_count(thr, max_seg):
        s_, _ = _seed()
        ob_ = _fine_observer(s_)
        sp_ = AskSpy()
        r_ = mtot.run_minting_train_of_thought(
            s_, topic="poodle", setpoint_observer=ob_, setpoint_topic="animal",
            width0=2, turns_per_segment=3, max_segments=max_seg,
            mint_after_quanta=thr, on_unknown="return", ask_fn=sp_)
        return len([e for e in r_["mint_events"] if e["minted"]]), len(sp_.calls)

    thr_lo = max(1, max_persist)          # reachable -> mints
    thr_hi = max_persist + 2              # unreachable over this run -> no mint
    mints_lo, spy_lo = _mint_count(thr_lo, 5)
    mints_hi, spy_hi = _mint_count(thr_hi, 5)
    mints_1seg, spy_1 = _mint_count(2, 1)   # single miss cannot reach thr=2
    held_spy_total += spy_lo + spy_hi + spy_1
    print("  threshold=%d (<= max persistence) -> minted %d axes" % (thr_lo, mints_lo))
    print("  threshold=%d (>  max persistence) -> minted %d axes" % (thr_hi, mints_hi))
    print("  1-segment run, threshold=2         -> minted %d axes" % mints_1seg)
    g3 = mints_lo >= 1 and mints_hi == 0 and mints_1seg == 0
    print("  reachable threshold mints; unreachable threshold + single miss do NOT: "
          "%s" % g3)
    print("  G3 %s" % ("PASS" if g3 else "FAIL"))

    # ---------------------------------------------------------------- G4 ----- #
    print("\n" + "-" * 78)
    print("G4  DISCRETE QUANTA: every steering + gating quantity is an INTEGER")
    print("-" * 78)
    ints_ok = (_all_int(res["deviation_trace"]) and _all_int(res["width_trace"])
               and _all_int(list(res["residual_persistence"].values()))
               and _all_int([e["persistence"] for e in res["mint_events"]]))
    print("  deviation_trace all int : %s" % _all_int(res["deviation_trace"]))
    print("  width_trace all int     : %s" % _all_int(res["width_trace"]))
    print("  persistence all int     : %s"
          % _all_int(list(res["residual_persistence"].values())))
    g4 = ints_ok
    print("  G4 %s" % ("PASS" if g4 else "FAIL"))

    # ---------------------------------------------------------------- G5 ----- #
    print("\n" + "-" * 78)
    print("G5  TEACHER-FREE: ask-spy = 0 across every held-path run")
    print("-" * 78)
    g5 = held_spy_total == 0
    print("  total ask-spy calls on the held path: %d" % held_spy_total)
    print("  G5 %s" % ("PASS" if g5 else "FAIL"))

    # ---------------------------------------------------------------- G6 ----- #
    print("\n" + "-" * 78)
    print("G6  ADDITIVE / BACKWARD-COMPAT: run_regulated_train_of_thought is "
          "unchanged — its aperture run == the minting loop's control half on the "
          "same seed")
    print("-" * 78)
    s6, _ = _seed()
    ob6 = _fine_observer(s6)
    spy6a = AskSpy()
    reg = rtt.run_regulated_train_of_thought(
        s6, topic="poodle", setpoint_observer=ob6, setpoint_topic="animal",
        width0=2, turns_per_segment=3, max_segments=6, on_unknown="return",
        ask_fn=spy6a)
    s6b, _ = _seed()
    ob6b = _fine_observer(s6b)
    spy6b = AskSpy()
    minr = mtot.run_minting_train_of_thought(
        s6b, topic="poodle", setpoint_observer=ob6b, setpoint_topic="animal",
        width0=2, turns_per_segment=3, max_segments=6, mint_after_quanta=999,
        on_unknown="return", ask_fn=spy6b)
    held_spy_total += len(spy6a.calls) + len(spy6b.calls)
    same_dev = reg["deviation_trace"] == minr["deviation_trace"]
    same_width = reg["width_trace"] == minr["width_trace"]
    print("  regulated deviation_trace: %s" % reg["deviation_trace"])
    print("  minting   deviation_trace: %s" % minr["deviation_trace"])
    print("  regulated width_trace    : %s" % reg["width_trace"])
    print("  minting   width_trace    : %s" % minr["width_trace"])
    print("  regulated has no minting keys: %s"
          % ("mint_events" not in reg and "residual_persistence" not in reg))
    # re-check G5 with these final spies folded in
    g5 = held_spy_total == 0
    g6 = (same_dev and same_width
          and "mint_events" not in reg and "residual_persistence" not in reg)
    print("  control half identical (deviation + width traces match): %s"
          % (same_dev and same_width))
    print("  G6 %s" % ("PASS" if g6 else "FAIL"))

    # ---------------------------------------------------------------- verdict  #
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("G1 mint gate: novel mints, duplicate refused", g1),
            ("G2 persistent residual mints a new axis", g2),
            ("G3 gate is persistence-timed (not gap-fill)", g3),
            ("G4 discrete quanta (all integer)", g4),
            ("G5 teacher-free (spy=0)", g5),
            ("G6 additive / backward-compat", g6)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("BLOCK 351 PASS: the train of thought grows its own manifold — when "
               "a residual signature (a thought with no held axis) RECURS across "
               "segments (a persistent, integer-counted residual), the seeded "
               "shape-decode loop COINS a new CapabilityAxis for it; a single or "
               "too-brief miss mints nothing (accommodation, not gap-fill); the "
               "over-minting guard refuses duplicates; discrete quanta throughout; "
               "teacher-free; the regulated controller is unchanged"
               if allpass else "FALSIFIED (see failing claim above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"g1": g1, "g2": g2, "g3": g3, "g4": g4, "g5": g5, "g6": g6,
               "all_pass": allpass,
               "admitted_size": res["admitted_size"],
               "residual_persistence": res["residual_persistence"],
               "minted_axes": res["minted_axes"],
               "deviation_trace": res["deviation_trace"],
               "width_trace": res["width_trace"],
               "max_persistence": max_persist,
               "mints_reachable_thr": mints_lo,
               "mints_unreachable_thr": mints_hi,
               "mints_single_segment": mints_1seg,
               "held_spy_total": held_spy_total}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
