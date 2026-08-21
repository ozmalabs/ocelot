# Constant-ranking selector census — a null that closes a rung I proposed one section earlier

**Status: measurement complete. Result is a NULL, and it retires the follow-up work the
previous section recommended.** No code changed.

## Why this was run

`DECISION_LAYER_PREREG.md` §5, written immediately before this, concluded:

> the rung to run instead is fixing rules that rank by constants — a seed-data change
> costing days rather than an engine change costing weeks.

That recommendation rested on **one** instance: `rule_episode_from_message` mints every
message-derived episode with a hardcoded `"salience": Lit 1.0`, so the `Argmax` over
salience in `default_mode_mint_episode_context` ties 90/90
(`ARGMIN_TIE_CENSUS_RESULTS.md`).

One instance is not a corpus claim. This census asks whether that pattern generalises
before anyone spends days on it.

## Method

Static walk of every `seeds/*.json` rule, extracting every `Argmax`, `Argmin`,
`ArgminUnique` and `ArgminRefusal` and classifying the shape of its `value` term; then, for
attribute-ranked selectors, classifying every writer of that attribute across the corpus as
literal or derived.

Probe: `scratchpad/rank_census.py`.

## Result

**1491 selectors** in the seed corpus.

| value shape | count |
|---|---|
| computed (a Term) | 1229 |
| attribute read | 194 |
| literal constant | 68 |

### A — literal-ranked: 68, and they are an idiom, not a defect class

Almost all are `Argmin(..., value = 0)` in the `arc_*` seeds (`ax_dispatch`, `ag_ask`,
`mg_tier_survival`, …). Ranking a set by the constant 0 is how this corpus writes **"pick
any element" / "does one exist"**. `default_mode_mint_goal_context` does the same with
`Lit 0.0`.

This is honest code: the selector *says* it does not discriminate. Counting these 68 as
defects would be exactly the over-claim this document exists to prevent.

### B — ranks an attribute every writer sets literally: **0**

Not one selector in the corpus ranks by an attribute that no rule ever derives.

The `salience` case does **not** appear here, and the reason matters:
`episodic_bind_observed_event_once` and `working_memory_output_gate` both set `salience`
from an `Attr` rather than a literal. So corpus-wide, salience *is* derived; it is only the
particular writer that produces the candidates on a conversational path
(`rule_episode_from_message`) that uses a constant.

**That makes the salience defect path-dependent, not structural — and therefore not
statically detectable.** Static analysis is the wrong instrument for it, which is itself
the finding.

### C — ranks an attribute no *seed rule* writes: 8, all legitimate

| selector | ranks | written by |
|---|---|---|
| `ae_frontier_goal` | `.f_interest` | `domains/doom_active_explore_ingest.py:146` |
| `ic_choose_unique_admissible_option` | `.decision_ordinal` | `domains/information_commitment.py:52` — `{wait:0, refine:1, commit:2}` |
| `published_net_*` ×3 | `.experiment_order` | `domains/published_net_debugger.py:80` |
| `whisper_grounding_*` ×3 | `.distance` | 18 Python sites |

All are written by **world adapters**, which is the architecture working as intended:
adapters mint nodes carrying attributes, seed rules rank them. `decision_ordinal` is
written with three genuinely distinct values and discriminates correctly.

## Conclusion

**There is no corpus-wide class of constant-ranking selectors.** The rung proposed in
`DECISION_LAYER_PREREG.md` §5 is not supported by the corpus and should not be run as
described. The salience instance is real, singular on the evidence available, and — per
the `refuse_all` measurement in that same prereg — **inconsequential on the one workload
where it was observed**: refusing all 36 ties changed no reply.

Two sections in a row have now had their proposed follow-up killed by the measurement that
followed. That is the instrument working. The cost of both censuses together was under an
hour; the work they retired was estimated in days and weeks.

## What remains true, and what would still be worth doing

- The single `salience` instance stands and is cheap to fix on its own terms: a literal
  where the neighbouring rules use a derived value is an inconsistency regardless of
  whether it currently matters.
- **A runtime census would find what a static one cannot.** The `argmin_tie` per-site
  attribution already reports which selectors tie on a live workload. Running it across
  several *different* workloads — motor, vision, program synthesis — would show whether
  path-dependent constant ranking is common outside conversation. That is the measurement
  this null points at, and it is hours rather than days.
- Nothing here touches the 1229 computed-value selectors, which are the majority and were
  not examined. Whether *those* discriminate is unmeasured and is not claimed either way.

## Reproduce

```bash
python3 scratchpad/rank_census.py     # or the copy preserved with this document
```
