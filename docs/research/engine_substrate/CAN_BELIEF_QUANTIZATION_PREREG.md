# Belief quantization via Causal Attitude Networks — PREREG

**Status: PREREG. Written before the live demonstration is run.** Per this
session's own standing discipline against post-hoc rationalization: what
follows is what will be measured and what would count as confirmation vs.
null, written before any `mt_mean_field_marginal`/`mt_audit_basin` call in
this rung executes.

## 0. This is a CORRECTION, not new work

`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` (merged today, commit `18aa6f5`/
`0e18038`) targeted idealized, single-edge, clean-evidence causal-strength
estimation (Pearl / Cheng / Griffiths & Tenenbaum / Rescorla-Wagner /
mental-models-of-conditionals) and recommended a `logodds`
`DimensionGenerator` for one edge's strength. The creator's own words,
verbatim, correcting that target:

> "a raw float is the antithesis of everything this project stands for -
> There is no zero point. I think the key difference is that people *do*
> have a variation in how much they separate this. I've personally observed
> this. lower metacognition leads to lack of nuance - This can be
> mechanically explained by the quantisation of causal linkage."

> "The research was looking at the wrong things. Absolutely clear
> inferences. The real world is extremely messy, and consists of outright
> lies, lies-to-children, over-simplifications, and all manner of other
> things. The ability to believe that the moon landings were faked for
> example is something that is alien to me, but I understand the
> *mechanism* - it requires a much more simplistic view of the world and a
> lack of understanding that has to [be] mechanical."

**The corrected target, stated precisely**: not "how strong is one causal
edge," but "how does a belief-holding MECHANISM, under messy/adversarial/
degraded real-world input, mechanically produce COARSE, low-nuance beliefs
— of which conspiracy-style lock-in is one visible symptom, not the whole
phenomenon." The hypothesis under test: **quantization/resolution of a
belief NETWORK** (not any single edge's strength) is what varies with
something like metacognitive capacity, and coarse quantization mechanically
explains susceptibility to oversimplified/false belief because there isn't
enough representational room to hold a nuanced alternative.

**A live mid-flight sharpening from the creator, arrived after this
document's first draft, folded in before any code ran**, verbatim:

> "Direct single weight networks collapse under NxM - the only way to
> effectively have a large network is to have nuanced weighting. This also
> matches the correlation of 'simple' people (not a judgement)."

Read precisely: this is a **scaling** claim, not merely a density claim. A
coarse/few-valued weight vocabulary on `J_ij` (e.g. J restricted to
`{-1, 0, +1}`) has enough expressive room to satisfy the constraints of a
small, sparse network without much frustration — but as N (the number of
coupled concepts held) grows, the number of pairwise constraints grows
(bounded above by N(N-1)/2 for a fully-coupled network) and a coarse weight
vocabulary runs out of distinct values to encode them without contradiction.
**Prediction**: coarse-weight networks should show degrading basin structure
(fewer/shallower distinguishable stable states, and/or rising frustration)
specifically AS N GROWS, while fine-grained/nuanced-weight networks should
keep scaling without that degradation, or degrade more slowly. "Simple
person" correlates directly: someone who only ever reasons about a few
things (small N) can get away with coarse weights and never hit the
collapse; someone holding a large network of beliefs is forced into either
nuanced weighting or visible incoherence/oversimplification as N grows —
one underlying capacity constraint, not two separate traits. This supersedes
the earlier single-size sparse-vs-dense design (§3 below) with a 2×k
factorial: weight-coarseness × network-size.

## 1. What was already found (verified before building on it)

1. **`seeds/causal_attitude_networks.json`** implements the real, published
   **Causal Attitude Network (CAN) model** — Dalege, Borsboom, van
   Harreveld, van den Berg, Conner, van der Maas, "Toward a Formalized
   Account of Attitudes: The Causal Attitude Network (CAN) Model,"
   *Psychological Review* (2018; the seed's own `description` names 2016,
   the earlier working/submission date — both refer to the same paper
   lineage, confirmed via WebSearch against PhilPapers/SAGE listings).
   Confirmed independently: the companion "Testing the Connectivity
   Hypothesis" paper (Dalege, Borsboom, van Harreveld, van der Maas, 2019)
   matches the seed's `attitude_strength_is_connectivity` node, and the
   "mere thought effect" (attention → polarization) matches
   `attention_increases_polarisation`. The seed's `description` field
   (`seeds/causal_attitude_networks.json:10`) is a precise, correct
   statement of the model: σ ∈ {-1,0,+1} node states, `causal_influence`
   edges with weight J_ij, external field h_i, inverse-temperature β,
   H = -ΣJ_ij·σ_i·σ_j - Σh_i·σ_i, P(σ) ∝ exp(-βH).
2. **`runners/dsl/src/can_ops.rs` is real, compiled, exposed via PyO3**
   (confirmed by reading the file in full and cross-checking every binding
   against `runners/dsl/src/py.rs:2245-2622`): `mt_mean_field_marginal`,
   `mt_energy`, `mt_target`, `mt_distance_to_target`,
   `mt_mean_field_with_h_override`, `mt_conflicting_nodes`,
   `mt_pairwise_similarity`, `mt_frustration_given_state`,
   `node_local_frustration`, `mt_hebbian_update_J`,
   `mt_update_identity_dynamics`, `mt_relax_to_marginal`, `mt_audit_basin`,
   `decay_J`/`decay_h` (mutation ops), `apply_evidence_h`. **12 passing
   tests already exist** (`tests/test_can_ops.py`) exercising exactly this
   surface on hand-built `Concept`/`Microtheory`/`causal_influence` graphs
   — the calling convention below is read directly from that file, not
   guessed.
3. **`seeds/causal_attitude_networks.json`'s 15 `rules` are ALL structurally
   inert** — confirmed by direct read (not just `match: null`; the rule
   objects don't even carry a `match`/`where`/`effects` key at all, only
   prose `if`/`then`/`why`/`soundness_category` strings). This is the
   identical inert-prose-not-executable-rule pattern already found and
   fixed for `logic_foundation.json` earlier this session.
4. **`seeds/epistemic_default.json` is real DATA, and IS wired — but not via
   its own (empty) `rules` array.** Its `description` states the rule is
   "agent-authored, NOT shipped" — confirmed: `domains/actor_goals.py`
   contains `ensure_epistemic_evidence_rule`, `ensure_epistemic_codebook`,
   a `ForcedChoiceProbe` → `ForcedChoiceExpectation` join
   (`actor_goals.py:1307-1346`), a `ClassBaseline` sum
   (`actor_goals.py:1428-1439`), and a combine step producing a lean +
   weight + confidence interval (`assess_epistemic_lean`,
   `actor_goals.py:1400+`). This is real, live machinery — a legal
   Python-authored-rule-JSON builder per `CLAUDE.md`'s own allowance ("The
   seven `_compose_*_rule` builders stay Python — they only assemble Rule
   JSON"), not agent decision logic.

## 2. Live demonstration — DESIGN (registered before running)

### 2.1 Superseded single-size design (kept for the record)

The original plan was one sparse/weak vs. one dense/strong network at fixed
N, comparable β, reading `mt_audit_basin` once per network. **This is
insufficient for the corrected N×M scaling claim** — a single N tells you
nothing about a *rate* of degradation — and is superseded by §2.2 before any
code ran.

### 2.2 The actual design — 2×3 factorial, registered

**Independent variables:**
- **Weight-coarseness** (2 levels), both integer-`k`-quantized on the same
  in-frame/cross-frame discipline this project already uses for `scale2`/
  `modular` `DimensionGenerator`s (`CLAUDE.md`'s BASE-AS-DIMENSION section):
  an integer step `k` is the in-frame datum; `J = k × granularity` is the
  cross-frame render. Both conditions span the SAME magnitude range
  `[-1, +1]` so the comparison isolates *resolution*, not *strength*:
  - **coarse**: `k ∈ {-1, 0, +1}`, granularity `1.0` → 3 distinct J values.
  - **fine**: `k ∈ {-4, -3, ..., +4}`, granularity `0.25` → 9 distinct J
    values.
- **Network size N** (3 levels): **4, 8, 16** concepts, each condition a
  COMPLETE graph (every pair coupled) — the sharpest test of N×M
  constraint growth, since a complete graph's coupling count is exactly
  N(N-1)/2 (6, 28, 120 for N=4/8/16), the quantity the creator's own
  framing names directly.

**Held fixed:** β = 2.0 (moderate-high — order is possible if the coupling
supports it), h_i = 0 for every node (no external field — isolates
coupling-driven multistability from field-driven convergence; a node with
h=0 and no ordering support relaxes to σ=0, the "no commitment" default,
exactly the substrate's own "Unknown = zero vector" convention already
documented in `distance_to_target`'s docstring).

**The "true" desired coupling**: for a given N, one fixed-seed draw of
N(N-1)/2 i.i.d. `Uniform(-1, 1)` values represents "the real, messy,
continuously-varying evidential relationship between each pair of beliefs"
— the thing a nuanced human network COULD represent. The SAME draw is used
for both coarse and fine at that N (apples-to-apples: only the ENCODING
resolution differs, not the underlying "true" messy relationships). Each
condition rounds this draw to its own nearest allowed `k`.

**Basin discovery.** `mt_mean_field_marginal`/`mt_audit_basin` compute ONE
mean-field fixed point from whatever is currently written to each Concept's
`state` attr — they do NOT themselves enumerate multiple basins (this is
itself part of the diagnostic answer to research question 2, see §4).
Basin MULTIPLICITY is measured here by **multi-start**: for each
(coarseness, N) cell, run 40 independent trials, each seeding every
Concept's `state` attr to an i.i.d. random choice from `{-1, +1}` (`set_attr`
before each call — `mt_mean_field_marginal` is a pure read, confirmed from
its own module doc comment, so this is safe to repeat), then call
`mt_mean_field_marginal(mt, max_iter=200, tol=1e-4)`. Each converged
marginal vector is rounded to 0.1 and clustered against previously-seen
cluster centers (L2 distance < 0.3 merges into an existing cluster) — the
number of surviving clusters is this cell's measured basin count.

**Per-cell measurements reported:** basin count (from the 40-restart sweep
above), mean `mt_frustration_given_state` across the 40 converged states,
mean `mt_energy`, and — a pure, engine-independent baseline reported
alongside — mean absolute rounding error `|J* − J_rounded|` for that
condition, to separate "how much the encoding itself distorts the true
relationship" from "what the engine's dynamics do with that distortion."

### 2.3 Predictions, registered before running

1. **Primary (N×M scaling claim)**: the coarse condition's basin count
   should decline (or fail to grow, or collapse toward a single N=0-ish
   attractor) faster than the fine condition's as N increases from 4→8→16,
   and/or the coarse condition's mean frustration should rise faster.
2. **Baseline sanity**: mean rounding error should be higher for coarse
   than fine at every N (this is close to definitionally true given the
   vocabulary sizes, and is reported as a manipulation check, not a
   finding).
3. **Honest null, registered as fully acceptable**: if basin count and
   frustration trend similarly for coarse and fine across N (no
   differential degradation), or if EITHER condition's basin count
   collapses to 1 regardless of coarseness once N is large enough (a
   ceiling/floor effect masking the comparison), that is reported as a
   clean negative finding, not reinterpreted charitably.
4. **A specific failure mode to watch for and name if it occurs**: complete
   graphs at N=16 with β=2.0 may simply be too strongly coupled for EITHER
   condition to sustain multiple basins (a single ferromagnetic-like
   attractor may dominate regardless of vocabulary resolution) — if so,
   that is itself informative (it would mean density, not resolution, is
   the dominant lever at this coupling strength) and will be reported as
   such, with the β/graph-density confound named explicitly rather than
   quietly re-tuned until a result appears.

## 3. Diagnostic questions (registered scope, not new)

- **Q2**: does `mt_audit_basin` literally count/report distinguishable
  basins? Answer already visible from reading `can_ops.rs:400-436` before
  running anything: **no** — it runs exactly ONE mean-field relaxation
  from whatever `state` is currently on the graph and reports that single
  basin's energy/coverage/frustration. "Basin count" is not a field it
  returns; it is a downstream inference the CALLER must do via multi-start,
  exactly as §2.2 does. This will be reported precisely, not glossed.
- **Q4**: diagnose why the 15 rules are inert — confirmed already in §1.3;
  RESULTS will give file:line and classify whether it's "missing match
  clauses on an otherwise-complete design" or something structurally
  deeper (no `Mt`/`causal_influence` population path in real agent
  operation, no attention→β wiring, no evidence→h_i ingestion path).
- **Q5**: `epistemic_default.json` → CAN `h_i` connection — assessed as
  DESIGN, not built (out of scope per the charter), given
  `assess_epistemic_lean`'s real output shape read in §1.4.

## 4. What will be built, bounded

Per the charter: if a small, clean, high-confidence wiring step exists
using the schema `can_ops.rs` already expects, with no new Rust and no new
node types, it will be built — real `match`/`where`/`effects` for a SUBSET
of the 15 rules, for the CAN model's OWN internal consistency
(recognize→update→relax), not the full epistemic-evidence pipeline. This is
decided AFTER reading the rule bodies against the real DSL Term vocabulary,
not presupposed here.

## 4.5 A further load-bearing sharpening — "the goal is to design an arbitrary solver"

A second mid-flight instruction, arriving after §0's N×M scaling
sharpening, raises the bar on the FINAL RECOMMENDATION specifically (not
the live demonstration, which stays as designed in §2.2), verbatim:

> "The goal is to design an arbitrary solver - scaling *has* to work."

Read precisely: finding a spin-glass ground state (what
`mt_mean_field_marginal`/`relax_to_marginal` approximate) is NP-hard in the
general case. Nuanced/quantized weighting alone (§0's fix) prevents
information LOSS — distinct relationships stop collapsing into the same
coarse bin — but does not by itself make an arbitrary-N network tractable
to relax. **Registered before checking**: the candidate tractability
mechanism is shape-recognition/compression over the coupling structure
itself — the same sd-loop move already measured at real scale this session
in `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` (commit `14cb457`): 7970 raw
pairwise `_pair_witness` comparisons on the real `computer_architecture`
Mt collapsed onto only 139 distinct `transform_key` patterns — 98.3%
(7831/7970) of calls recognized an already-seen pattern rather than paying
fresh computation. The hypothesis: most `J_ij` couplings in a real, large
belief network are not independently-estimated free parameters either —
most are recognized instances of a small set of held causal-linkage SHAPES
("physical proximity implies causal influence," "shared category
membership implies correlated evaluation," etc.), and an arbitrary-scale
solver should recognize/reuse those shapes (sd-loop rung 1) and pay fresh
relaxation cost only for the genuine residual (rung 4: mint), rather than
treating every one of N(N-1)/2 edges as an independent weight to
relax/estimate from scratch. **This is named and assessed in RESULTS, not
built** (building a shape-recognizing CAN coupling-compressor is its own
rung) — but the recommendation is required to address it explicitly rather
than stopping at "nuanced weights fix representational coarseness," per
this instruction.

## 5. Worktree

`/home/matt/ozmadev/ocelot-worktrees/can-belief-quantization`, branch
`can-belief-quantization`, base `main @ 0e18038`.
