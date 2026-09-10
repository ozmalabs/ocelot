# Concept extraction as a reusable CAN operator — RESULTS

**Block**: 328000. Pre-reg: `CONCEPT_SEED_PREREG.md`.
Build: `domains/llm_concept_seed.py`; measure:
`scripts/llm_concept_seed_measure.py`. Substrate: protected `can_native_bp.py` /
`seeds/can_native_reimplementation.json` (read-only, built-to).

**POSITIVE (with an honest partial). The concept `opposite-of`, extracted from
context-A antonym families, TRANSFERS to held-out context-B families it never
co-occurred with — by its own recovered structure, NO LLM at query time. Its
GEOMETRIC signature recognises held-out B opposites above chance and above a
random-operator control; its SUBSTRATE signature (a negative Ising coupling)
settles the partner OPPOSITE for every held-out B pair, while a shuffled positive
coupling settles it SAME. A concept is a reusable CAN operator, not stored
instances.**

## Result (concept fit on A = 12 families; applied to B = 8 held-out families)

### (a) Geometric transfer — recognise held-out B opposites (AUC, chance 0.50)

| operator | AUC |
|---|---|
| **extracted W** | **0.68** |
| random-W control | 0.51 |

The operator fit on A scores true held-out-B antonym pairs above random B pairs
(0.68 vs 0.51 control). The concept transfers as a recognised RELATION in a
context it never saw. It is PARTIAL (0.68, not ≈1.0) — the 0.6B model's
"opposite" is real but soft.

### (b) Substrate signature — settle a held-out B partner (NO LLM at query)

| coupling (clamp one B word +1) | partner settles | count |
|---|---|---|
| extracted NEGATIVE | OPPOSITE (−1) | 8/8 |
| shuffled POSITIVE (control) | SAME (+1) | 8/8 |

For all 8 held-out B pairs, the extracted negative coupling settles the partner
to the OPPOSITE state on the substrate's own BP; the positive-coupling control
settles it to the SAME state (the wrong answer). The substrate EXECUTES
"opposite" as a settle, and it is the extracted (negative) coupling SIGN that
carries it — crisp, 8/8.

## Claim verdicts

- **Claim 1 (geometric transfer): HOLDS, partial.** Extracted-W AUC 0.68 >
  random-W 0.51 > chance. Real transfer as relation recognition.
- **Claim 2 (substrate signature): HOLDS, crisp.** Negative coupling → opposite
  8/8; positive control → same 8/8. The coupling sign is the concept's dynamics.
- **Claim 3 (transfer not memorisation): HOLDS.** B families disjoint from A;
  no LLM at query; both controls (random-W, positive-coupling) fail as they
  should.

## Verdict

The concept tier succeeds: `opposite-of` is extractable as a two-part reusable
CAN operator — a geometric signature that RECOGNISES opposite pairs (partial on
a 0.6B) and a substrate signature that EXECUTES the opposite relation as a
negative-coupling settle (crisp) — and it TRANSFERS to families it was never
extracted on, with the LLM out of the query loop. This is the harder tier-2
payoff of the extraction direction: not just facts stored and traversed
(knowledge, 327), but a concept lifted as a reusable operator that composes in
unseen contexts on the substrate's own machinery.

## Anti-faking / method

- Context-B families DISJOINT from A extraction; the concept never co-occurred
  with them.
- Geometric transfer measured as relation-recognition AUC vs a random-W control;
  substrate transfer as a settle vs a positive-coupling control — a scrambled
  concept fails both.
- NO LLM at query time: the LLM only produced the word vectors offline; the
  operator W and the coupling sign are frozen recovered structure, and retrieval
  / settle are pure numpy / substrate ops.
- The brittle 1-of-N RETRIEVAL readout (raw-embed 3/16, contextualised 1/16) is
  reported as a NEGATIVE — the honest, substrate-relevant readout is relation
  recognition (does the concept decide an opposite pair), which is exactly what
  gates placing the negative-coupling edge.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched; models + venv under
  `/applications`, NOT committed.

## Honest bounds and next tier

- One small model (0.6B), one concept (`opposite-of`), 12 A / 8 B families. The
  geometric transfer is PARTIAL (AUC 0.68) — the model's antonym operator is
  soft, and exact-opposite retrieval among candidates does NOT work; the
  load-bearing claims are the above-control recognition and the crisp 8/8
  substrate dynamics, not a high retrieval rate.
- The substrate signature (negative coupling ⇒ opposite settle) is a general,
  crisp mechanism; the geometric recognition is the part that scales with model
  quality. Larger models and more concepts (`same-as` = positive coupling,
  `implies` = directed positive, `excludes` = strong negative) are a scale-up on
  the same harness.
- NEXT TIER: PROCESSES (hardest) — extract a PROCEDURE as graph DYNAMICS (a
  rewrite / transport, connecting to the transport arc 324–326) and apply it to
  UNSEEN inputs; the bar rises from held-out TRANSFER to held-out APPLICATION.
