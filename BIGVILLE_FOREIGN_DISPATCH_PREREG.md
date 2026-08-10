# PREREG — block 316000: Word from Giantville in the paper

The wider-world news (block 259000) let a traveller bring Giantville news that
townsfolk fold into **beliefs** — but that news never reached the **paper** (the
newspaper writer, blocks 293000–296000, postdates it). This rung connects the two:
the publisher hears the traveller's foreign news like any belief, and the paper
prints a **"Word from Giantville"** dispatch, hedged by its credibility.

## The mechanism (`bigville_foreign_dispatch.json`) — reuses both stacks

A traveller brings a `NewsItem about Giantville`; the publisher **hears** it and
forms a `GiantvilleBelief` via the existing **`bw_news_secondhand`** (confidence =
the teller's credibility, provenance = hearsay) — or holds a grounded one
(confidence 1.0) if someone returned from there. Then, mirroring `bigville_write`
(prose is `StringConcat` over held fields, and bias becomes word choice):

- **`fd_write_confirmed`** (`confidence ≥ 0.75`): mints a `foreign_dispatch` Story
  — *"Word from Giantville that <news>, confirmed by one lately returned."*
- **`fd_write_hearsay`** (`confidence < 0.75`): *"Travellers bring word from
  Giantville that <news> — though the account is as yet unconfirmed."*

The **provenance becomes the hedge** — the newspaper's veracity axis applied to
foreign news. Each belief is written once (a `foreign_written` guard).

## Gates (pass/fail, pre-registered)

1. **G-paper-carries-giantville-news (HEADLINE):** a traveller brings news → the
   paper prints exactly one `foreign_dispatch` story containing the news and
   "Giantville".
2. **G-provenance-becomes-word-choice (HEADLINE):** a credible report is printed
   *confirmed*; a shaky one is hedged as *unconfirmed* hearsay — the veracity axis
   showing up as words.
3. **G-no-traveller-no-news (frontier / falsifier):** with no traveller the
   publisher forms no belief and the paper carries nothing about Giantville
   (unknown = absence, first-class).
4. **G-written-once:** re-running the fixpoint does not duplicate the dispatch.
5. **G-no-python-decision (source audit):** belief formation is `bw_news_secondhand`
   and the render is the `fd_write_*` `StringConcat` rules; the adapter mints the
   paper/publisher/traveller/news, ticks, and reads (no rule engine, no Python
   prose).

## Scope / honesty
- Reuses `bw_news_secondhand`, so the publisher holds ONE Giantville belief at a
  time (the news family's existing limitation); multiple simultaneous foreign items
  is a richer scope, deferred. The hedge is a confidence-band on rendering
  (rhetoric), not a belief decision — belief formation/confidence stays the
  259000 mechanism.
- Isolated demonstrator (`self_load_only`); composes with `bigville_world_news`; no
  Rust; `.so` untouched (`a8a9012c`).
