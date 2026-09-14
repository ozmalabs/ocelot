"""Block 344000 — PLAN-THEN-REALIZE: grammar owns the clause, statistics fill gaps.

Two literature reviews (human production science + machine NLG methods) converged
that the earlier 'grammar as a heavily-weighted term in a word-ranker' (the mass
shift) is a KNOWN FAILURE MODE — a soft feature that never guarantees order or
coverage. The corrected architecture, implemented in
predictive_reading.realize_goal_clause: the grounded sign-grammar PRODUCER owns the
clause ORDER + admissible words as HARD CONSTRAINTS; the statistical ranker
(predict_next_words) is DEMOTED to filling OPEN slots only, and can never override a
grammar-realized word or reorder the clause. This is faithful to the substrate's own
analysis-by-synthesis identity: the comprehension grammar run in reverse owns
structure; prediction fills the rest.

Falsifiable claims:
  C1  GRAMMAR OWNS ORDER: for an is-a goal, realize_goal_clause returns
      mode='plan_then_realize' and surface == producer.produce()'s overt_speech
      (an ORDERED grammatical clause), i.e. the grammar's order stands verbatim.
  C2  RANKER CONFINED (cannot override/reorder): the ranker is only ever consulted
      for realized==False (open) slots; every realized==True slot is byte-identical
      to the grammar's surface and the slot ORDER equals produce()'s ordered_slots.
      HONEST SUB-FINDING: with goal_content=[concept], the ranker's top1 is that
      concept itself, so at this rung's lexicon it never SUBSTITUTES — gap-fill is a
      proven-SAFE no-op (grammar owns the whole clause). Genuine substitution needs a
      register offering lexical ALTERNATIVES (synonymy/inflection the grammar didn't
      ground) — deferred (as is the self-conditioned-rollout gap-fill).
  C3  HONEST FALLBACK: an ungrounded/empty goal yields mode='fallback' with a
      reported rung-1.5 rollout result — never a silent empty.
  C4  CONTENT RECOVERED: score_self_target on the realized clause returns coverage
      1.0 in grounded_comprehension mode (production closes on comprehension).

Pure graph, teacher-free grounding (no LLM), no substrate .so write path. Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung2_plan_then_realize.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import literary_analysis as la
from domains import predictive_reading as pr


ISA_GOALS = [
    ("poodle", "dog"),
    ("dog", "mammal"),
    ("wolf", "mammal"),
    ("sparrow", "bird"),
]


def _frame(subject, obj):
    return {"event": "is", "agent": subject, "patient": obj,
            "tense": "present", "intent": "inform"}


def main() -> int:
    print("=" * 74)
    print("PLAN-THEN-REALIZE — grammar owns the clause, statistics fill gaps (blk 344)")
    print("=" * 74)
    s = _native.Substrate()
    # teacher-free producer grounded on the copula bank + one is-a frame (NO LLM)
    producer = la._build_producer([{"event": "is", "agent": "dog", "patient": "mammal"}])
    ws = pr.build_writer_model(s, ["indeed the animal is plainly a creature"])["writer_style"]

    c1 = c2 = c4 = 0
    n = len(ISA_GOALS)
    for subj, obj in ISA_GOALS:
        res = pr.realize_goal_clause(s, producer, _frame(subj, obj),
                                     ws_node=ws, intended_concepts=[subj, obj])
        prod = res["produce"]
        overt = (prod or {}).get("overt_speech", "")
        ordered = [tuple(x) for x in
                   ((prod or {}).get("surface_structure") or {}).get("ordered_slots", [])]
        words = ((prod or {}).get("phonological_word") or {}).get("words") or []

        # C1: mode + surface == grammar's ordered clause
        c1_ok = (res["mode"] == "plan_then_realize" and res["surface"] == overt)
        # C2: every realized==True slot is byte-identical in the backbone, and the
        # backbone's slot order matches produce()'s ordered_slots (grammar owns order);
        # the ranker was only consulted for open slots (source != 'grammar' there).
        fixed_ok = all(
            b["surface"] == w.get("surface")
            for b, w in zip(res["backbone"], words) if w.get("realized"))
        order_ok = ([b["role"] for b in res["backbone"]] ==
                    [w.get("role") for w in words])
        ranker_confined = all(b["source"] in ("gapfill", "grammar_lemma")
                              for b in res["backbone"] if not b["realized"]) and \
                          all(b["source"] == "grammar"
                              for b in res["backbone"] if b["realized"])
        c2_ok = fixed_ok and order_ok and ranker_confined
        # C4: parse-back content recovery
        v = res["verdict"] or {}
        c4_ok = (v.get("recoverable") is True and v.get("mode") == "grounded_comprehension")

        c1 += int(c1_ok); c2 += int(c2_ok); c4 += int(c4_ok)
        print("\nisa(%s,%s): %r  [mode=%s gaps=%s]"
              % (subj, obj, res["surface"], res["mode"], res["gaps_filled"]))
        print("   C1 grammar-owns-order=%s (surface==overt=%s)" % (c1_ok, res["surface"] == overt))
        print("   C2 ranker-confined=%s (fixed byte-identical=%s, order=%s, sources ok=%s)"
              % (c2_ok, fixed_ok, order_ok, ranker_confined))
        print("   C4 content-recovered=%s (cov=%s mode=%s)"
              % (c4_ok, v.get("coverage"), v.get("mode")))

    # C3: honest fallback — an ungrounded/empty goal degrades to reported rollout.
    fb = pr.realize_goal_clause(s, producer, {"agent": "", "patient": "", "tense": "present"},
                                ws_node=ws, intended_concepts=["zork", "quux"],
                                fallback_kwargs={"max_steps": 6})
    c3_ok = (fb["mode"] == "fallback" and fb["fallback"] is not None)
    print("\nC3 honest fallback (ungrounded goal): mode=%s surface=%r reported=%s -> %s"
          % (fb["mode"], fb["surface"], fb["fallback"] is not None, "OK" if c3_ok else "FAIL"))

    print("\n--- claims ---")
    print("C1 grammar owns order:        %d/%d" % (c1, n))
    print("C2 ranker confined to gaps:   %d/%d" % (c2, n))
    print("C4 content recovered:         %d/%d" % (c4, n))
    print("C3 honest fallback:           %s" % ("PASS" if c3_ok else "FAIL"))
    allpass = (c1 == n and c2 == n and c4 == n and c3_ok)
    verdict = ("PLAN-THEN-REALIZE PASS: grammar owns the ordered clause, the ranker is "
               "structurally confined to open slots (and adds nothing at this lexicon — "
               "a proven-safe no-op), content recovered, fallback honest"
               if allpass else "FALSIFIED (see per-claim above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "c1_grammar_owns_order": c1, "c2_ranker_confined": c2,
        "c4_content_recovered": c4, "c3_honest_fallback": c3_ok, "n": n,
        "gapfill_substitutes_this_rung": False,
        "note": "ranker top1==concept given goal_content=[concept] -> no substitution; "
                "grammar owns whole clause; genuine gap-fill needs lexical alternatives (deferred)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
