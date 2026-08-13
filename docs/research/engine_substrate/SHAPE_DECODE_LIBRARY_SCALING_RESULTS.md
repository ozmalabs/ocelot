# Shape-decode library scaling — results

**Verdict, up front: NO-GO.** `ShapeDecode`'s real, production codebook
(`ShapeSignature`, 407 parts on a full boot) decodes in **2.7-16.4ms**
today. The linear-scaling trend crosses the registered 100ms threshold only
around **~6,500 entries in the composer configuration** (`beam=3,
max_steps=8, cand_k=3`) or **~31,000 entries in the real-time configuration**
(`beam=1, max_steps=1, cand_k=1`) — both well past this rung's registered
"before 5,000" GO threshold, and well past anything this codebook has
reached (its growth history across this arc's own prior rungs is
24 → 46 → 139 → **407**, over roughly a month of separate research
sessions). **This is a clean, comfortable-headroom NO-GO, exactly the kind
of complete, valuable outcome `SHAPE_DECODE_LIBRARY_SCALING_PREREG.md`
registered as fully expected-possible.** Nothing is built beyond the
measurement script and this pair of docs, per house discipline point 6.

A second, real, measured finding did cross the threshold — and is reported
in full because it sharpens rather than reverses the verdict: see §3.

---

## 0. Baseline

`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`9643e63fea4f90b1358b2ef4051fdc74321adac375b87927da3876777769a147`, built
from `main` at `d9edae8` (unchanged — this rung built no Rust). Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/shape-decode-scaling`,
branch `shape-decode-library-scaling`. Full measurement script:
`scripts/shape_decode_scaling_bench.py`; raw numbers:
`scripts/shape_decode_scaling_bench_results.json`. All numbers below are
medians of 5-7 repeated calls in one warm process (min/max reported inline
where they matter); every call goes through `native.evaluate()` — the same
PyO3 surface every production caller uses, no shortcut engine path.

---

## 1. §15/§4 sources, verified

### 1.1 `RULES_AS_SHAPE_DESIGN_SPIKE.md` §15.2 (DeepGAR)

Read in full. Its own framing: DeepGAR is "not needed at today's scale
(§11.2's own slice tested against 46 rules; SHAPE_AUDIT.md's meta-shape
codebook is 24 entries) — named as the standing answer for when scale stops
being negligible." This rung's job was to check whether "today's scale" is
still 24-46, or has moved — it has (§0 below), and the real answer, measured
rather than assumed, is that it still has comfortable headroom at the new,
larger, real number.

### 1.2 `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` Q4 (§6.4)

Read in full (the citation given in the brief, "Q1/Q4," maps to this
document's §3 [Q1, complexity] and §6 [Q4, tractability]). The load-bearing
sentence for THIS rung's §2 soundness question: *"Whether recognized
causal-linkage shapes correspond to true shared latent generators (which
would make this tractability result apply) or merely to value-alphabet
compression (which would not) is a genuinely open, testable, currently-
untested empirical question."* This is the CAN-solver framing of the exact
question an embedding pre-filter needs answered in the affirmative to be
sound (§2 below applies it to `ShapeDecode`'s own representation, not
CAN's couplings — a different object, same underlying condition).

### 1.3 `shape_decode.rs`'s real decode loop, verified by direct read

Confirmed precisely, `shape_decode.rs:1511-1531` (`eval_shape_decode`'s
`'search:` loop): for every state in `frontier`, every part in the codebook
is scored (`for (part, sig) in parts.iter().zip(scoring_sigs.iter())`,
`:1521`), unconditionally — this is a full linear scan of the entire held
codebook, every step, every surviving beam state. **One correction to the
prompt's own framing, found by reading past the cited lines**: `beam` no
longer truncates the frontier. `shape_decode.rs:1358-1428`'s own doc
comments, confirmed against the code at `:1578-1602`
("Bug 2's fix... no width truncation after this... bounded instead by a
single, total, whole-search expansion BUDGET"): every non-duplicate
candidate state survives to the next round; the real cap is
`DEFAULT_SD_BUDGET = 20_000` (`:1373`), not `beam_width`. So the previously
recorded `O(beam_width × max_steps × codebook_size × observation_size)`
formula (`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`) is a bound that is no
longer tight post-Bug-2 — real worst case is closer to `O(min(budget,
cand_k^max_steps) × codebook_size × observation_size)`. A second, sharper
correction, found while reading `score_part_for_residual`/`covers_relation`
(`:1224-1276`) — **the codebase's own comment already names it**:
`covers_relation`'s doc says outright, *"THIS IS THE O(N_residual x N_part)
CORE OF DECODE... it happens inside ONE Term evaluation."* The true per-
part cost is `O(residual_size × that_part's_own_signature_size)`, not
`O(observation_size)` alone — `observation_size` (the design docs' shorthand)
silently assumed parts stay small. §3 measures exactly the regime where that
assumption breaks.

---

## 2. Real codebook sizes and real caller configurations

A full `boot_core()` + `load_all_seeds()` boot (matching
`scripts/rule_signature_measure.py`'s own pattern) gives:

| codebook_type | real node count |
|---|---|
| **`ShapeSignature`** (the real `ShapeDecode` codebook — shared by `can_native_reimplementation`, `reflex_net`, `vision_crossframe_identity`) | **407** |
| `RuleSummary` (NOT routed through `ShapeDecode` in production — see §3.0) | 2229 |
| `ArgumentRole` | 65 |
| `MetaShape` | 11 |
| `ConceptSignature` / `XfSignature` / `VdSignature` / `BlobEdge` / `Correspondence` | 0 on a bare boot — runtime-minted only |

Real caller configurations, from every seed invoking `ShapeDecode`
(`grep -r '"type":"ShapeDecode"' seeds/*.json`): exactly the two classes
`DEFAULT_SD_BUDGET`'s own doc names — **real-time**
(`beam=1,max_steps=1,cand_k=1`: `embodied_*`, `humanoid_adaptation`,
`somatomotor_waves`, `vision_crossframe_identity`,
`vision_invariant/verdict_comparator`) and **reflective/composer**
(`beam=3,max_steps=8,cand_k=3`, occasionally `2,8,2`:
`can_native_reimplementation`, `reflex_net`, `meaning_inference`,
`meta_shape_growth`, `shape_decode_loop`, `program_synthesis`,
`prog_construction_loop`). Both measured below.

`ShapeSignature`'s real distribution (407 parts, avg 12.8 relations/part,
100 distinct predicates across the pool): heavily domain-skewed — the
handwriting-stroke sub-codebook (`kind="stroke"`, `seg`/`pose_*`/`strokeq`
predicates) is 237/407 (58.2%) by `kind`, and predicate-set bucketing
collapses 407 parts into 62 buckets with the largest holding 263/407
(64.6%). Reported precisely because it bears directly on §4.

---

## 3. Real latency, real scale (P1/P2, registered predictions)

### 3.1 Today's real `ShapeSignature` codebook (407 parts)

Goal: 11 relations sampled from 3 real parts (a genuine cross-part
composite, forcing real search rather than a trivial one-part match).

| config | median | min | max |
|---|---|---|---|
| `rt(1,1,1)` | **2.66ms** | 2.48ms | 3.72ms |
| `composer(3,8,3)` | **16.42ms** | 16.20ms | 16.77ms |

`load_parts`-only cost (empty goal, isolates the graph scan before any
scoring — see §1.3's `load_parts` read): **1.90ms**. This is 71% of the
`rt(1,1,1)` call's total cost and 12% of the `composer` call's — a real,
present-day finding, discussed honestly in §5 (multi-shape/batching) even
though it does not change the headline verdict.

**P1 confirmed**: both configurations measured in the predicted range
(single-digit ms real-time, tens-of-ms composer, both comfortably under
100ms).

### 3.2 Synthetic size sweep (real signatures cloned to controlled sizes, same goal)

| codebook size | `rt(1,1,1)` median | `composer(3,8,3)` median |
|---:|---:|---:|
| 50 | 0.19ms | 1.30ms |
| 200 | 0.52ms | 5.31ms |
| 500 | 1.18ms | 9.57ms |
| 1,000 | 2.25ms | 13.13ms |
| 2,000 | 4.50ms | 26.11ms |
| 5,000 | 12.07ms | 73.51ms |
| 10,000 | 32.50ms | 162.37ms |

**P2 confirmed**: scaling is close to linear in codebook size (e.g.
50→10,000, a 200x size increase, gives a 170x time increase for
`rt(1,1,1)` and a 125x increase for `composer`, both well within the noise
a beam-search's step/coverage-completion nonlinearity would introduce — not
exponential, not superlinear in any way that would change the verdict).
**Threshold crossing**: interpolating between 5,000 (73.5ms) and 10,000
(162.4ms) for `composer(3,8,3)`, 100ms is crossed at **≈6,500 entries** —
above the registered "before 5,000" GO bar, so **NO-GO stands** on the
pre-registered criterion, though narrowly enough to name plainly rather than
round away: at the current growth trajectory (four growth episodes over
roughly a month reaching 407), reaching 6,500 is not imminent but is not
multiple years away either. `rt(1,1,1)` crosses 100ms only around
**≈31,000 entries**, extrapolating from the 32.5ms@10,000 slope — real-time
callers have far more headroom than composer callers, which matters because
real-time callers are the more numerous class in the seed corpus today.

---

## 3.0 Why `RuleSummary` is measured separately (not folded into §3)

Confirmed by inspection (`domains/rule_signature.py`) and by grep — no
`codebook_type` value of `"RuleSummary"` exists anywhere in `seeds/*.json`
or `domains/*.py`. Production rule-selection compares `RuleSummary` entries
via `AntiUnifyWitness`/`FixedCount`/`StructSim` pairwise calls
(`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s own transfer mechanism), never
via `ShapeDecode`. So a `RuleSummary`-vs-`ShapeDecode` measurement is
necessarily an **adapted, hypothetical application** — real content (each
`RuleSummary`'s own `where_signature_json` rows, computed by the real
graph-resident `where_signature` program, minted verbatim as a
`ShapeSignature`-shaped codebook part), at real count (2,229 rules → 2,209
usable non-empty parts), decoded through the real, unmodified `ShapeDecode`
Term — but not a production code path. Reported in full below because the
charter explicitly asked for `RuleSummary` at scale, and because what it
found is a genuine, useful, if unexpected, result.

## 3.1 The `RuleSummary`-adapted codebook (2,209 real parts) — measured, and it DOES cross the threshold

Where-signature rows have the form `("rt", path, term_type)` or
`("ra", path, field, atom)` (`domains/rule_signature.py:126-183`,
confirmed by direct read) — real per-rule signatures average **274
relations**, ranging from 2 to **83,881** (the largest single rule in the
corpus, `emp_abs_expand_factorized_groups_in_parallel`, matching
`domains/rule_signature.py`'s own docstring citation of that number).
This is a fundamentally different size regime from `ShapeSignature`'s
12.8-relations/part average — **20-6,500x larger per part**.

Goal: 23 relations, a real, small/typical rule's own where-signature (not
the 83,881-row outlier, which would test a different question — see the
honest caveat below).

| | median | min | max |
|---|---|---|---|
| `load_parts`-only (empty goal) | 31.5ms | — | — |
| `rt(1,1,1)` | **285.8ms** | 277.7ms | 298.6ms |
| `composer(3,8,3)` | **415.1ms** | 412.7ms | 438.6ms |

**This decisively exceeds the registered 100ms GO threshold** — by the
letter of §2's registered criterion ("GO... at today's real scale...
`ShapeSignature`... OR the adapted 2,229-entry `RuleSummary` test"), this
fires GO. It is reported as a real, honest, measured result, not
downplayed — but see §3.2 for why the recommended fix (a structural
pre-filter) would not actually address it, which is itself the more
important finding here.

### 3.2 Why this crossing does NOT change the build verdict — the cost driver is different, and a pre-filter would not fix it

Confirmed by subtraction: `load_parts` itself is only 31.5ms; the remaining
**254ms** (`rt`) / **384ms** (`composer`) is the scoring loop —
`covers_relation`'s own doc comment (§1.3) names this exactly:
*"THIS IS THE O(N_residual x N_part) CORE OF DECODE."* When parts average
274 relations (and a real rule can carry 83,881), the per-part scoring cost
is what dominates, **not the number of parts** — this is a completely
different cost driver from §3's `ShapeSignature` sweep, where parts stayed
a fixed, small ~13 relations and codebook COUNT was the only thing varied.

**A structural bucketing pre-filter narrows which PARTS get scored — it
does nothing about how expensive scoring one already-selected part is.**
And for this specific codebook, bucketing would barely narrow the candidate
set to begin with: where-signature rows carry only **two distinct leading
tokens**, `"rt"` and `"ra"` (`rule_signature.py`'s row-kind tag, quoted
above) — not `ShapeSignature`'s real, informative 100-predicate vocabulary.
Nearly every rule's where-clause contains both row kinds, so a predicate-
set bucket over this codebook would collapse almost the entire 2,209-part
pool into one or two buckets, exactly the degenerate case §4's soundness
criterion (a) already worries about, confirmed analytically here rather
than by a second live run (the row-kind vocabulary is fixed and countable
by inspection, not sampling-dependent).

**Correctly read, this result validates the EXISTING design rather than
arguing for a new one**: `domains/rule_signature.py`'s own choice to
compare `RuleSummary` entries via `AntiUnifyWitness` (a pairwise,
`O(size_a + size_b)` structural match per comparison, not a full-codebook
linear scan) rather than `ShapeDecode`'s beam search was the right call for
this object, made independently of this rung and confirmed, not merely
assumed, by this measurement. **If a future rung ever wires `RuleSummary`
into `ShapeDecode` directly** (the "rules as shape" direction
`RULES_AS_SHAPE_DESIGN_SPIKE.md` names), this number — 285-415ms per
decode against today's real corpus — is the concrete cost that decision
would need to reckon with, and the fix there is "don't route large,
few-part corpora through the many-small-part beam search," not "add a
pre-filter in front of it."

**Honest caveat**: the goal used here (23 relations from one real,
small/typical rule) is a choice — a goal built from the 83,881-row rule
would cost even more per part scanned (the residual side of
`covers_relation`'s `O(N_residual × N_part)` also grows), and this rung did
not sweep goal size independently of codebook composition; that is a named,
not-measured, further axis.

---

## 4. Pre-filter soundness evaluation (for `ShapeSignature`, the codebook this actually matters for)

### 4.1 Candidate (a): DeepGAR-style geometric embedding — NOT recommended

`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4's own unresolved
condition — genuine low-rank/shared-generator structure, not mere
value-alphabet compression — is the exact condition a DeepGAR-style
embedding needs (structural similarity ≈ proximity in the learned space) to
be SOUND, not just fast. It is explicitly, currently, UNTESTED for this
representation, and would require: (1) a training signal (positive/negative
subgraph-containment pairs — this project's `ShapeSignature` codebook has
no labeled correspondence pairs at all, only recognised/unrecognised
outcomes from the sd loop itself); (2) a learned embedding model — genuinely
new ML infrastructure this project does not have and whose introduction
CLAUDE.md's own standing discipline (symbolic/structural preference,
"SHAPES NOT NUMBERS") argues against absent a demonstrated need. **Not
recommended, and not sized further** — the soundness gap alone is
disqualifying before the cost/benefit question is even reached, per this
rung's own registered criterion.

### 4.2 Candidate (b): structural bucketing (predicate-set / `kind` / arity) — sound, but the real distribution limits its payoff

Derivable entirely from data every `ShapeSignature` node already holds
(`name`+`signature`, read once by the SAME `load_parts` that already runs)
— no learned model, no new attrs. **But the real distribution (§2) is
honestly skewed**: predicate-set bucketing gives 62 buckets with the
largest holding 64.6% of the whole codebook (the stroke sub-codebook).
A caller decoding a stroke observation would see only a ~35% reduction in
scored parts; a caller decoding a vision/math/faculty observation (the
smaller buckets — 1 to 30 parts) would see a much larger, genuinely useful
reduction. **This is a real, honestly-reported PARTIAL win, exactly the
outcome the pre-registered soundness criterion anticipated** — sound in
design, uneven in payoff, and — combined with §3's headroom finding — not
worth building yet, because the majority-bucket caller (the dominant real
class today) would barely benefit while every caller pays the bucket-index
maintenance/invalidation complexity.

### 4.3 Recommendation

**Neither is recommended for building now.** If a pre-filter is ever
warranted (codebook approaching the ≈6,500-entry composer-config threshold,
§3.2), structural bucketing (b) is the right SHAPE of fix — sound, derived
from held data, no ML infrastructure — but should be re-evaluated against
the codebook's distribution AT THAT TIME, since a differently-shaped future
codebook (less stroke-dominated) could make bucketing considerably more
effective than the 64.6%-largest-bucket figure measured today.

---

## 5. Multi-shape / batching — real, present-day, but small in absolute terms; named, not built

`load_parts` (`shape_decode.rs:239-`) re-reads and re-deserialises every
node of the given `codebook_type` from scratch on **every single**
`ShapeDecode` call — confirmed by direct read: `apply_scope`/`apply_exclude`
(`:973-986`) both filter the list `load_parts` already fully built; neither
reduces the initial graph scan. Measured: **1.90ms** for the real 407-part
`ShapeSignature` codebook — a genuine, currently-duplicated cost when
multiple observations decode against the same, unchanged codebook in
sequence (the literal "collapsing across a large library quickly,
repeatedly" shape of the charter's own question). This is 71% of the
fastest real caller class's (`rt(1,1,1)`) total per-call cost — the
dominant fraction, not a rounding error.

**Why this is named rather than built, at this rung's own honest
assessment**: the absolute number is 1.9ms. No real caller in the seed
corpus invokes `ShapeDecode` at a frequency where 1.9ms/call is a measurable
problem (these are `max_steps=1` real-time/hot-loop calls, not a tight
inner loop called thousands of times per user-facing tick — the same
`shape_decode.rs` doc comment quoted in §1.3 names exactly this caller
class as "real-time/hot-loop" but at ONE decode per invocation, not a
batch). **Building a safe cache requires a real invalidation signal**, and
the one this project already uses elsewhere (`agent.codebook_epoch`, a
graph-resident attr bumped by `grow_part_library`, read by SEED RULES that
re-arm stale Observations — `seeds/shape_decode_loop.json`) is **not
currently plumbed into `eval_shape_decode` at all**: the Rust function has
no access to the agent node or its `codebook_epoch` attr today. Threading
it in would mean either a new parameter on the `ShapeDecode` Term
(defensible, but a real interface change touching every one of the ~40
`ShapeDecode` call sites across `seeds/*.json`, not a "smallest correct
version") or a cheaper proxy (e.g. codebook node-count as a staleness
signal) that is UNSOUND on its own — an in-place `set_attr` mutation of an
existing part's `signature` (which this codebase's own sd-loop growth rules
do perform in some paths) would silently stale a count-keyed cache without
changing node count, a real correctness risk this rung is not willing to
introduce for a ~1.4ms/call saving (the delta between 2.66ms and a
best-case ~0.8ms `rt(1,1,1)` call) at today's real scale.

**Honest finding, stated plainly**: multi-shape batching is a REAL,
measurable amortisation opportunity (confirmed, not merely plausible) —
but building it correctly is a larger, separately-scoped rung (wiring
`codebook_epoch` through to the Rust decode boundary, or an equally sound
alternative invalidation signal) than "the smallest correct version" this
rung's build gate calls for, and the payoff at today's real scale (low
single-digit ms) does not clear the bar this rung's own registered
criteria set. Named as the concrete next step if `ShapeDecode` call
frequency ever grows (e.g. a future caller that decodes many observations
per tick against one codebook), not built here.

---

## 6. What was built

**Nothing beyond the measurement script and these two docs.** Per house
discipline point 6: "if NO-GO (not yet a real bottleneck), commit the
measurement docs alone — that's a complete result." No Rust file was
touched; `runners/dsl/python/substrate_rs/_native.abi3.so` in this worktree
is byte-identical to `main`'s (confirmed by the sha256 in §0, unchanged
across this whole rung).

---

## 7. Regression

No code changed, so no regression risk exists to gate against — this is
recorded for completeness, not as a real check. `cargo test --release --lib`
was NOT run (no Rust edited); the ~90 Python test files that exercise
`ShapeDecode`/`shape_decode` (found via
`grep -rl "ShapeDecode\|shape_decode" tests/*.py`, spanning meta-shape,
blob-edge/ink-decode, humanoid/embodied motor, program-synthesis,
composer/driver, vision cross-frame, and more) were not re-run for the same
reason — they gate Rust/seed behaviour this rung did not touch. The one
new file (`scripts/shape_decode_scaling_bench.py`) is measurement-only,
imports no production module in a way that could change its behaviour
(`domains.rule_signature.ensure_where_signature` is called read-only-ish —
it mints ONE additive attr on existing `RuleSummary` nodes in this
one-shot process's own throwaway substrate, never touching the checkpointed
graph any real daemon runs on), and mints only new, uniquely-named
benchmark codebook nodes (`Bench*`, `RuleShapeCodebook`) that no seed rule
reads or reacts to.

---

## 8. What this does NOT establish

- Does not establish that `ShapeDecode` will NEVER need a pre-filter — it
  establishes that it does not need one TODAY, at 407 real parts, with
  ≈16x headroom to the composer-config threshold and far more for
  real-time callers.
- Does not establish that structural bucketing would remain the right
  design at a future, larger, differently-distributed codebook — §4.2's
  64.6%-largest-bucket figure is a property of TODAY's stroke-dominated
  `ShapeSignature` pool, not a permanent fact about the representation.
- Does not establish that `RuleSummary` SHOULD be routed through
  `ShapeDecode` — §3.1/§3.2 measure what WOULD happen if it were, and the
  answer (285-415ms, dominated by per-part size not codebook count) argues
  against ever doing so via the beam-search path, not for it.
- Does not sweep goal/observation size independently of codebook
  composition, nor test `budget_exhausted:true` territory (every measured
  call here completed within `DEFAULT_SD_BUDGET` — the "search terminates
  honestly rather than silently truncating" behaviour was never triggered
  and so was not exercised by this rung).
- Does not measure `run_rules` fixpoint-level `ShapeDecode` call frequency
  in a real running daemon (how many times per tick, across how many
  distinct codebook_types) — §5's "no real caller batches" claim is based
  on reading every seed's own declared `beam`/`max_steps`/`cand_k`, not on
  live daemon call-frequency telemetry, which this project does not
  currently collect for this Term.

---

## Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/shape-decode-scaling
export PYTHONPATH="$(pwd)/runners/dsl/python:$(pwd)"
python3 scripts/shape_decode_scaling_bench.py
cat scripts/shape_decode_scaling_bench_results.json
```
