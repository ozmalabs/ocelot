# BIGVILLE_COLUMN — copyfitting as residual→refine (blocks 298000–299000)

**Pre-registered BEFORE any measurement.** Committed separately, ahead of the
implementation. No number in this file is fit to a result — the gates and the
tolerances are fixed here; the implementation is then measured against them.

## The claim

A **writer** (an agent, graph-native) authors a newspaper article to **fit a
column of fixed budget**. Real newspaper *copyfitting*: EXPAND the prose to
**fill** a column with room to spare; COMPRESS to **fit** a column that is too
small; iterate to a fixpoint where the rendered length is within tolerance of
the budget.

**The reframe (the whole point):** copyfitting IS the substrate's
residual→refine / dynamic-quantization loop.

- The column **budget** is the target.
- The article is composed from **held content** (a set of `Detail` nodes, each
  carrying structured fields), and **rendered to prose by `StringConcat`** over
  those fields — graph-native prose, NOT a Python f-string (copies
  `seeds/bigville_write.json`).
- The **length residual** `residual = budget − rendered_length` drives the
  refinement:
  - `residual > 0` (room to spare) → **EXPAND**: include one more held detail
    sentence, or render an included detail in its **longer held phrasing**.
  - `residual < 0` (over budget) → **COMPRESS**: render an included detail in
    its **terser phrasing**, or drop the lowest-rank supporting sentence (the
    **lead survives**).
- Iterate to a fixpoint where `|residual| ≤ tol` (fill, from below) or
  `length ≤ budget` (fit).

The EXPAND/COMPRESS **decisions are graph RULES** reading `residual`. The
adapter only renders (via `run_rules`), reads the rendered `text`, `len()`s it,
writes `length`/`residual` back onto the graph, and bumps a measure `epoch`.
No Python decides expand vs compress, or which detail to move.

## Architecture-rule compliance

- Article STRUCTURE = nodes (`Column`, `Detail`) + edges (`col -has_detail-> d`).
- EXPAND/COMPRESS = seed rules (`bigville_column.json`, `self_load_only:true`),
  each selecting exactly ONE detail per measure epoch via `Argmax`/`Argmin` over
  a `Filter` of the column's details (the `retire_duplicate_gap` precedent) and
  latching direction once from the initial residual sign (mode latch).
- Prose = `StringConcat` render rules (terse / verbose variants over held fields).
- Adapter (`worlds/bigville_column_world.py`) = mechanical only: plant held
  details (ingest), set budget, loop { `force_all_dirty` + `run_rules` to render;
  read each included detail's `text`, sum `len()`; write `length`, `residual`,
  bump `epoch`; `run_rules` to let ONE rule act }. Terminates when within
  tolerance or when the graph makes no further move (read off `acted_epoch`).
- No `StrLen` Term is added; length is measured in the adapter (a sensor read).
  The engine's `runners/dsl` is NOT touched and the `.so` is NOT rebuilt.

## Held content plant (for the audit gates)

A fixed held-detail set is planted per test: one **lead** (`is_lead=1`, highest
rank, always included, never dropped) plus several ranked supporting details.
Each detail carries `subject`, `predicate`, and a held `extra` clause. The
terse render is `"<subject> <predicate>."`; the verbose render is
`"<subject> <predicate>, <extra>."` — the verbose form says MORE of what is
**already held**, never invented text.

## Gates (all pre-registered; pass/fail fixed here)

- **G-fill** — budget ABOVE the minimal (lead-only) article. Starting from the
  minimal draft, the writer EXPANDS (adds held sentences, then longer phrasings)
  and the final length lands **within `tol` of the budget, from below**
  (`budget − tol ≤ length ≤ budget`). `tol = 30` chars.

- **G-fit** — budget BELOW the full article. Starting from the full draft, the
  writer COMPRESSES and the final length is **≤ budget**, and the **lead
  sentence survives** in the article.

- **G-sweep** — one fixed config (full draft, all-terse), budgets swept across a
  wide range. Final article length **tracks the budget monotonically**
  (non-decreasing in budget). The length-vs-budget curve is reported as numbers.

- **G-graph-native** — source audit: the adapter builds NO sentence string (no
  f-string, no `%`-format, no `.format`, no rule-engine calls
  `graph_rewrite`/`gr.run`/`make_rule`/`_match`/`_apply`); the article's
  sentences are `StringConcat` terms in the seed; the expand/compress decisions
  are the seed's rules. The adapter's only assembly of graph output is joining
  already-rendered sentence texts with a single space separator (a read-back,
  the `bigville_write` multi-story precedent) — it introduces no content token.

- **G-no-confabulation-under-fill** — after a FILL to a large budget, **every
  sentence** in the article maps to a planted held detail, and **every
  alphabetic token** in the rendered article derives from a held field
  (`subject`/`predicate`/`extra`) of some planted detail. Filling adds MORE of
  what is held, never a token that is not.

- **G-falsifier** — an **unsound control** (`bigville_column_lorem.json`) whose
  fill rule appends fabricated `lorem ipsum` text (NOT derived from held fields)
  MUST **fail** G-no-confabulation. This proves the gate bites (a fabricating
  filler is caught).

## Honest-residual policy

Report the REAL measured fill/fit curve and any residuals: irreducible core
(a budget below the lead cannot be met — final stays at the lead floor);
fill ceiling (a budget above the all-verbose maximum leaves the article at its
ceiling, under budget); fit granularity (dropping whole sentences is coarse, so
a fit may land well under budget when the next sentence would not fit). These
are reported, not hidden. Fabrication of a result is a firing offence.
