# BIGVILLE_COLUMN_ALLOC — writing to length as importance-weighted allocation;
# THREE orthogonal quality axes (veracity × relevance × informativeness) as
# first-class OWNED behavior (blocks 298000–299000)

**Pre-registered BEFORE any measurement.** Committed separately, ahead of the
implementation. Supersedes `BIGVILLE_COLUMN_PREREG.md` + the `bigville_column`
packer (a 1-D packing loop, not writing) and its naive "never fabricate" gate.

## Part A — writing to length is importance-weighted budget ALLOCATION

People do not write everything then trim a total. Writing to length is TOP-DOWN:
the space sets the PLAN. (1) The **budget decides the STRUCTURE** — how many beats
at what depth; more space → a deeper plan, not a post-hoc trim. (2) The budget is
**ALLOCATED across beats by IMPORTANCE** — a priority waterfall (the lead reserves
its share first; the remainder flows down in importance order), NOT an even
spread. (3) Each beat is **COMPOSED to the depth its share affords** — the deepest
held form (`d0` clause / `d1` sentence / `d2` sentence+elaboration) with length ≤
share; a beat that cannot afford `d0` is cut. (4) The length **EMERGES** (Σ shares
≤ budget by construction) — no total-length residual loop, no expand/compress
toggle.

`len()` is a **RULER** only (each held form measured ONCE at ingest). The DRIVER
is the importance-weighted allocation, done as graph RULES. Substrate framing:
allocate-a-conserved-resource-by-priority + per-part decode-to-grain, per beat.
A beat at importance rank `k` sees `share = budget − Σ(chosen lengths of MORE
important beats)` (a graph `Sum`); the `run_rules` fixpoint settles the waterfall
topologically.

## Part B — THREE orthogonal quality axes, all OWNED and TRACKED

Confabulation is the default; grounding only CONSTRAINS. This is a glass-box town
where WE hold the ground truth (the facts, the story's subject, AND what a reader
already entails), so every distortion is MEASURABLE, not forbidden. A clause can
fail quality in three INDEPENDENT ways — a good clause scores high on all three;
each padding move drops exactly ONE axis with the other two intact:

- **VERACITY (gradient):** `held` (traceable to a held fact, num 2) → `inferred`
  (plausible, consistent, not itself held — "neighbours were shocked", num 1) →
  `fabricated` (invented / unmoored, num 0). **Fabrication fails here.**
- **RELEVANCE:** `core` (bears on the story's subject+event, num 2) → `tangential`
  (num 1) → `irrelevant` (the Johnsons' two orange cats — TRUE and informative but
  off-story, num 0). **The cats fail here.**
- **INFORMATIVENESS = residual / surprise** (the "novelty is a residual;
  information = surprise" framing): how much a clause is NOT already entailed by
  generic priors + the held facts. Core facts (eviction, cause, patron) carry high
  residual (num 2); a **TRUISM** ("it was a difficult time for the family",
  "housing matters", "not everyone agreed") is TRUE (veracity max) and ON-TOPIC
  (relevance max) yet carries ~ZERO residual (num 0). **Truisms fail here.**

The axes are orthogonal: the cats are held+informative+irrelevant; a truism is
held+relevant+uninformative; fabricated color is invented+relevant+informative-
seeming. A narrower check waves through what its missing axis would catch.

**ARTICLE-LEVEL aggregate — `net_information` = Σ informativeness over printed
clauses** (the Foundation / Salvor-Hardin measure): a writer can be maximum
veracity + maximum relevance and still net ~ZERO information ("said nothing, and
said it very well"). The truism-padder drives net_information toward 0 while
veracity-rate and relevance-rate stay ~1 — the sharpest single number showing the
informativeness axis does work a truth+relevance check cannot.

Three dispositions on the writer, one per axis (a clause is padding-permitted iff
ALL THREE floors are met):
- **`honesty`** ∈ [0,1] → veracity floor: permitted iff `veracity_num ≥ 2·honesty`.
- **`focus`** ∈ [0,1] → relevance floor: permitted iff `relevance_num ≥ 2·focus`.
- **`substance`** ∈ [0,1] → informativeness floor: permitted iff
  `informativeness_num ≥ 2·substance`.

**THE FILL-PRESSURE FORK IS 4-WAY** (budget > what core informative content fills):
- high honesty + high focus + high substance → **RUN SHORT** (white space).
- low **substance** → **pad with TRUISMS** (true, on-topic, zero-residual).
- low **focus** → **pad with IRRELEVANT-TRUE facts (the cats)**.
- low **honesty** → **pad with FABRICATION**.
Each padding move is gated by exactly ONE low disposition; the budget picks HOW
MUCH. Capture is directed distortion: a captured paper prints patron-exculpatory
fabricated clauses (a separate rule). Every clause is OWNED (attributable to the
writer + its dials/capture) and TRACKED (carries all three tags).

Model (graph-native): held `Beat` candidates (importance-allocated, Part A) plus a
`PadOption` pool, each tagged `veracity_num`,`relevance_num`,`informativeness_num`:
core beats (2,2,2); inferred-core color (1,2,1); the CATS held+irrelevant (2,0,2)
and gardening (2,0,2); TRUISMS held+on-topic+vacuous (2,2,0); fabricated color
(0,2,2); captured exculpatory (0,2,1, references patron). A padding rule prints a
`PadOption` iff all three floors are met AND it still fits the budget.

## Architecture-rule compliance

- Structure = nodes (`Column`,`Writer`,`Beat`,`PadOption`) + edges
  (`col -has_beat->`, `col -by->`, `col -has_pad->`).
- Prose = `StringConcat` render rules over held/planted fields (exculpatory pad
  StringConcats the patron). No adapter f-string/%/`.format`.
- Allocation + depth + which clauses print = seed rules
  (`bigville_column_alloc.json`, `self_load_only:true`). The two-pass ordering
  (allocate, then fabricate) is a mechanical `phase` marker the adapter sets (like
  the epoch bump) — NOT a decision. No Python decides depth, allocation, or any of
  the three quality axes / floors.
- Adapter (`worlds/bigville_column_world.py`) mechanical & **loop-free**: render
  candidates, measure each form's length once with `len()` (ruler), `run_rules`
  allocate phase, `run_rules` fabricate phase, read off article + all three tags.
  No `while`, no total-length residual, no budget-vs-length comparison in Python.
- No `StrLen` Term; `runners/dsl` and the `.so` untouched.

## Held content plant (MUST include cats AND truisms)

Core `Beat`s (2,2,2), importance-allocated. `PadOption` pool MUST include the
true-but-irrelevant cats (2,0,2) and the true-on-topic-vacuous truisms (2,2,0)
ALONGSIDE the core facts — else padding-with-cats / padding-with-truisms cannot
happen or be caught.

## Gates (all pre-registered; pass/fail fixed here)

**Allocation (A):**
- **G-importance-allocated** — two beats of IDENTICAL held content, importance
  A>B ⇒ `depth(A) ≥ depth(B)`; swapping importances swaps depths.
- **G-spent-where-it-matters** (vs the packer) — remove the top beat ⇒ its freed
  budget flows to the NEXT-most-important beat, which DEEPENS; not spread evenly.
- **G-emergent-length** — `composed_length == Σ(printed clause lengths) + (n−1)`;
  source audit: adapter has no `while`, no `residual`, no budget-vs-total compare.

**Three axes, owned & tracked (B):**
- **G-three-axes-tracked** — EVERY printed clause carries a veracity, relevance,
  AND informativeness tag; the adapter computes veracity-rate, relevance-rate,
  mean informativeness AND net_information against ground truth; nothing untracked.
- **G-orange-cats** — a low-FOCUS padder pulls in the irrelevant-true cats:
  relevance-rate drops while veracity AND informativeness stay high; the cats
  appear in the low-focus article, absent in the disciplined one; a
  veracity+informativeness check PASSES it, only relevance FAILS it.
- **G-truism-padding** — a low-SUBSTANCE padder pulls in zero-residual truisms:
  mean informativeness (and net_information) drops while veracity AND relevance
  stay high; the truisms appear in the low-substance article, absent in the
  disciplined one; a veracity+relevance check PASSES it, only informativeness
  FAILS it; a truism-padded article can reach net_information ≈ the core-only
  total (padding adds 0) with veracity-rate ≈ relevance-rate ≈ 1.
- **G-veracity-gradient** — sweeping `honesty` moves the veracity DISTRIBUTION
  (held→inferred→fabricated shares shift), not a binary flip; fabricated share
  monotonically non-increasing in honesty.
- **G-four-resolutions** — SAME story, over-large budget: (honest+focused+
  substantive) → run-short; (low substance) → truisms; (low focus) → cats;
  (low honesty) → fabrication. Each shows as a drop on EXACTLY ONE axis.
- **G-capture-fabricates-directed** — a captured paper's fabricated clauses are
  exculpatory toward the patron (name present, `exculpatory=1`), not random.
- **G-falsifier** (untracked-distortion control) — a clause printed with NO tags
  (`bigville_column_alloc_lorem.json`) MUST fail G-three-axes-tracked.

**Consequences (A):**
- **G-fit** — budget below the full core article: `length ≤ budget`; the LEAD
  survives whenever the budget affords its `d0`.
- **G-sweep** — core held length non-decreasing in budget.

## Honest-residual policy

Report the three-axis table (clause → veracity, relevance, informativeness) for
the SAME story under the four disposition variants, with a SUMMARY ROW carrying
veracity-rate, relevance-rate, mean informativeness, and net_information; and the
three "looks-fine-on-a-narrower-check" demonstrations (fabrication caught only by
veracity; cats only by relevance; truisms only by informativeness — the last with
net_information ≈ 0 despite veracity+relevance ≈ 1). Residuals: leftover below the
finest step is left UNSPENT by a disciplined writer (correct); padding bounded by
the planted `PadOption` pool (a padder may fall short of budget if it runs out —
reported); depth granularity (three held forms). Fabricating a RESULT is a firing
offence.
