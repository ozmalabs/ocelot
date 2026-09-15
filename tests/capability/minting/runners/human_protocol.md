# Human runner — protocol & results-entry format

This is the human arm of the capability suite: the SAME battery the substrate and LLM
runners use, presented to a human subject so their scores land on the identical rubric
and the unified scorecard can place substrate / human / LLM side by side.

Two human-facing tasks mirror the two anchor rubrics.

## Task H2 — Typicality ranking (Rubric A RQ2)

For each category, present the members in arbitrary order and ask:

> "Rank these by how TYPICAL each is as an example of *{category}* — 1 = the best,
> most typical example. Rank all of them; no ties."

This is the Rosch (1975) goodness-of-example task. (Note: the vendored
`fixtures/rosch1975_typicality.json` already IS the canonical human ranking; a fresh
human run is only needed if you want a new subject rather than the published norm.)

**Results-entry format** — write `human_results_typicality.json`:

```json
{
  "bird":   {"robin": 1, "sparrow": 2, "bluejay": 3, "...": 0},
  "fruit":  {"orange": 1, "apple": 2, "...": 0}
}
```
Every member gets an integer rank starting at 1. The scorer computes Spearman ρ of the
human ranking vs the vendored norm (a fresh subject) — or, for the substrate/LLM
comparison, uses the vendored norm directly as the human column.

## Task H4 — Accommodation readiness (Rubric B)

Present a short SEQUENCE of observations that either (a) keep re-raising the same new
distinction (a *persistent* gap) or (b) raise a distinction once then drop it (a
*transient* gap). After the sequence ask:

> "Do you now need a NEW category/dimension to describe what you kept noticing, or was
> that a one-off you can ignore?"

Credit "needs a new dimension" only for the persistent sequence (Carey's readiness
gate: a new representation is constructed only when the evidence recurs, not on a single
exposure).

**Results-entry format** — write `human_results_gate.json`:

```json
{
  "persistent_gap": {"minted_new_dimension": true},
  "transient_gap":  {"minted_new_dimension": false},
  "duplicate_gap":  {"minted_new_dimension": false}
}
```

The scorer scores these against the gold labels (persistent → should mint; transient /
duplicate → should not) with the same `gate_precision_recall` used for the substrate.

## Ethics / provenance

No new human data is required to run the suite — the vendored Rosch (1975) norm is the
default human column, cited as a reconstruction (see `fixtures/PROVENANCE.md`). If you
DO collect fresh human responses, obtain appropriate consent and record the protocol
version; do not commit personally identifying information — only the anonymized
per-item rankings above.
