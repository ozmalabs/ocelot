# PREREG — block 315000: sentencing by collapse, bounded by law

Block 314000 deferred sentence-by-collapse: `jail_term` was a fixed statutory
number the Constable prescribed. This rung makes the **council decide the
sentence** — but **the law limits it to a statutory [min, max]**. Sentencing is
now a decision (a collapse), constrained by legislation.

## The mechanism (`bigville_sentence.json`) — law is the admissible set

A `SentenceLaw{offence, min_term, max_term, status}` lives in the LawBook (the
council can amend it — the same book the land_tax lives in). On a **guilty**
verdict, `sn_sentence` collapses the term:

- Candidate `SentenceLevel` nodes carry a `days` value (0, 1, 2, …).
- The council's **desired** severity is set by how hard it condemned:
  `desired = charge.base_days + (condemn_count − threshold)` — a bare-majority
  conviction sits at the offence's base; every extra condemning councillor adds a
  day (a genuinely collective signal, not one juror's number).
- The collapse is `Attr(Argmax over SentenceLevels, "days")` valued by
  `IfThenElse(min_term ≤ days ≤ max_term, −(days − desired)², −∞)` — i.e. the
  Argmax may only choose a level **inside the legal range**, and picks the
  admissible level nearest the council's desired severity. **The law is the
  admissible set**: desired above the ceiling ⇒ `max`; below the floor ⇒ `min`.

The chosen term is written to `charge.jail_term`; the existing `jl_imprison`
(block 314000) then imprisons for exactly that many days. Custody and the fine
(`ct_sentence`) remain independent.

## Gates (pass/fail, pre-registered)

1. **G-sentence-is-decided (HEADLINE):** on a guilty verdict the council sets a
   custodial term by collapse and the defendant is gaoled for it (no term was
   prescribed on the charge — the council chose it).
2. **G-upper-bound-by-law (HEADLINE):** when the council's desired severity
   exceeds the offence's `max_term`, the imposed term is **exactly `max_term`** —
   the ceiling holds however hard the council wants to punish.
3. **G-lower-bound-by-law:** when the council's desired severity is below
   `min_term`, the imposed term is **exactly `min_term`** — a guilty verdict
   carries at least the statutory minimum, even on the weakest conviction.
4. **G-within-range-tracks-the-council:** when desired sits strictly inside
   (min, max) the term equals it; and a harsher council (more condemning
   councillors) imposes a **longer** term than a divided one for the same offence.
5. **G-amending-the-law-moves-the-ceiling:** lowering `max_term` by an amendment
   lowers the imposed term for the same conviction — the bound is real law, not a
   constant.
6. **G-acquitted-not-sentenced (falsifier):** an acquitted defendant gets no term
   and is never gaoled.
7. **G-no-python-decision (source audit):** the sentence is the `sn_sentence`
   Argmax collapse over the legally-admissible levels; the adapter mints the
   sentence-law + levels, ticks, and reads (no rule engine, no Python selection or
   clamping).

## Scope / honesty
- The council's "desired" severity is driven by its condemnation strength
  (`condemn_count`); a richer per-councillor sentence-preference collapse then
  aggregated is a natural refinement, deferred. The decision here is a genuine
  Argmax collapse whose option set is the law — which is what "sentencing bounded
  by law" requires.
- Isolated demonstrator (`self_load_only`); composes with `bigville_jail` /
  `bigville_court`; no Rust; `.so` untouched (`a8a9012c`).
