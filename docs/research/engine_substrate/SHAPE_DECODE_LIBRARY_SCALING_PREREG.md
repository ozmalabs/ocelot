# Shape-decode library scaling — pre-registration

**Posture: MEASURE-THEN-BUILD**, per this folder's own standing discipline
(`RULE_SIGNATURE_SLICE_PREREG.md`, `GAMMA_REFLECTION_WIRING_PREREG.md`) and
CLAUDE.md's "RUN 15 CORRECTION": power the gate before the endgame, and do
not build a speculative optimisation for a problem that is not real yet.

**Charter, quoted verbatim from the project's creator:** *"what about multi
shape shape math — collapsing across a large library quickly."*

**Engine baseline.** `runners/dsl/python/substrate_rs/_native.abi3.so`
sha256 `9643e63fea4f90b1358b2ef4051fdc74321adac375b87927da3876777769a147`,
built from `main` at `d9edae8` (`git log --oneline -1 main` →
`d9edae8 Merge can-final-migration: wire the three closed primitives, find
the real reason 4/6 stay blocked, GO`), confirmed byte-identical to this
worktree's own checkout (`engine_preamble(strict=True)` passes; no Rust
source differs from `main`). Worktree:
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/shape-decode-scaling`,
branch `shape-decode-library-scaling`. **No collision** checked against the
concurrently-running `run_rules`/per-Mt-scoping sibling
(`/home/matt/ozmadev/ocelot-worktrees/can-mt-scoped-rules`,
`git diff --stat main` there touches only `domains/insight_detection.py`,
`domains/insight_propagation.py`, `domains/self_improvement_loop.py`,
`runners/dsl/src/{py,rewrite,substrate}.rs` — this rung's scope is
`runners/dsl/src/shape_decode.rs`, disjoint).

---

## 0. Orientation — real codebook sizes, counted before any prediction

Per this folder's own precedent (`RULE_SIGNATURE_SLICE_PREREG.md` §0.2:
"the candidate-rule population... counted before the bar was set" is
legitimate pre-registration groundwork, not the measurement itself), a full
`boot_core()` + `load_all_seeds()` boot (the same pattern
`scripts/rule_signature_measure.py` uses) was run to find out what sizes
actually exist in this tree TODAY, before registering a latency prediction
against them. This is size-counting only — no `ShapeDecode` timing was
consulted in choosing the numbers below beyond the complexity formula
already established in the two documents this rung was told to read.

| codebook_type | real node count (full boot) |
|---|---|
| `ShapeSignature` (the actual `ShapeDecode` codebook — `can_native_reimplementation`, `reflex_net`, `vision_crossframe_identity` all decode against this ONE shared pool) | **407** |
| `RuleSummary` (rule-selection corpus, NOT currently routed through `ShapeDecode` — see §1.3) | **2229** |
| `ArgumentRole` | 65 |
| `MetaShape` | 11 (as the design docs report) |
| `ConceptSignature`, `XfSignature`, `VdSignature`, `HumanoidBodyShapeSignature`, `EmbodiedMotorShapeMemory`, `BlobEdge`/`Correspondence` | 0 on a bare seed boot — runtime-minted only, not present until their own demo/rule pipeline runs |

`ShapeSignature`'s own real distribution (407 parts): predicate-set
bucketing collapses to only 62 distinct buckets, and the single largest
bucket already holds 263/407 (64.6%) of the whole codebook (the handwriting
stroke sub-codebook, `kind="stroke"`, `seg`/`pose_*`/`strokeq` predicates).
Registered here because it bears directly on §2 below (bucket-balance
question) — a skewed real distribution is itself a finding, not a defect,
and must be reported honestly whichever way it cuts.

Real caller configurations, read from every seed that invokes `ShapeDecode`
(`grep` over `seeds/*.json`, `type":"ShapeDecode"`): exactly the two classes
`DEFAULT_SD_BUDGET`'s own doc comment (`shape_decode.rs:1358-1372`) already
names — **real-time** callers (`beam=1, max_steps=1, cand_k=1`:
`embodied_*`, `humanoid_adaptation`, `somatomotor_waves`,
`vision_crossframe_identity`, `vision_invariant/verdict_comparator`) and
**reflective/composer** callers (`beam=3, max_steps=8, cand_k=3`, occasionally
`beam=2,cand_k=2`: `can_native_reimplementation`, `reflex_net`,
`meaning_inference`, `meta_shape_growth`, `shape_decode_loop`,
`program_synthesis`, `prog_construction_loop`). Both classes are used in the
latency sweep below.

---

## 1. What was verified by direct source read (not re-derived, not assumed)

### 1.1 The decode loop is a full linear scan of the codebook, every step, every frontier state

`shape_decode.rs:1511-1531` (`eval_shape_decode`'s `'search:` loop):

```rust
'search: for _ in 0..max_steps.max(0) {
    let mut nxt: Vec<BeamState> = Vec::new();
    for state in &frontier {
        if state.residual.is_empty() { continue; }
        let mut scored: Vec<(usize, i64, &Part, Vec<Value>)> = Vec::new();
        for (part, sig) in parts.iter().zip(scoring_sigs.iter()) {
            if state.used.contains(&part.name) { continue; }
            let (fit, covered) = score_part_for_residual(&state.residual, sig, ...);
            ...
        }
        ...
    }
    ...
}
```

Confirmed: for **every** state in the current `frontier`, **every** part in
the held codebook is scored (`score_part_for_residual`, itself
`O(observation_size)` via `covers_relation`, `:1224-1266`). This matches
`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s own citation exactly.

### 1.2 The corrected bound — `beam` no longer truncates; the real cap is `DEFAULT_SD_BUDGET`

Read past what the prompt's own citation established: `shape_decode.rs:1358-1372`
and `:1414-1428`'s doc comments, confirmed against the code at
`:1578-1602` — **Bug 2's fix removed the fixed-width beam prune.** Every
non-duplicate candidate state (deduped by `(residual, used)`) survives to
the next round; `beam` is kept on the wire for back-compat but is "no longer
truncat[ing] anything." The actual bound on frontier growth is the single,
whole-search **expansion budget** (`DEFAULT_SD_BUDGET = 20_000`,
`:1373`), not `beam_width`. Consequence for the complexity formula: since
each `BeamState` created costs exactly one unit of the shared budget, and
every state in `frontier` at step `s` was created by exactly one expansion
at step `s-1`, the total number of **full-codebook-scan operations** across
the whole search is bounded by `budget + 1`, not `max_steps × beam_width`.
The previously-stated `O(beam_width × max_steps × codebook_size ×
observation_size)` formula (`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`) is
therefore an *upper bound that is no longer tight* post-Bug-2-fix — the
real worst case is closer to `O(min(budget, cand_k^max_steps) ×
codebook_size × observation_size)`, and registered here as a correction
this rung is making to the record, verified by reading the code, not
assumed from the doc comment alone.

### 1.3 `RuleSummary` does not go through `ShapeDecode` today

Confirmed by inspection (`domains/rule_signature.py`) and by grep (no
`codebook_type` value of `"RuleSummary"` anywhere in `seeds/*.json` or
`domains/*.py`): the rule-selection corpus is compared via
`AntiUnifyWitness`/`FixedCount`/`StructSim` pairwise calls
(`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s own §4 transfer mechanism), a
different algebra from `ShapeDecode`'s beam search over a `name`+`signature`
codebook. This rung tests `ShapeDecode` specifically (the Term named in the
charter's own "already measured" citation and explicitly in scope), so
`RuleSummary` is exercised in §3 below as an **adapted** application (each
`RuleSummary`'s real `where_signature_json` rows minted as a
`ShapeSignature`-shaped codebook part, decoded via the real, unmodified
`ShapeDecode` Term) — a genuine test of `ShapeDecode` at 2000+-entry scale
using real corpus content, explicitly labeled as hypothetical-application
rather than a production code path, per this rung's own honesty
requirement.

---

## 2. Registered predictions (BEFORE the latency sweep and bucket-balance analysis are reported in the RESULTS doc)

Given §1's confirmed formula (`O(min(budget, cand_k^max_steps) ×
codebook_size × observation_size)`, effectively linear in codebook size for
any FIXED beam/max_steps/cand_k/observation-size, since neither the budget
cap nor the search depth changes with codebook size):

- **P1 (today's real scale, `ShapeSignature`, 407 parts):** real-time
  config (`beam=1,max_steps=1,cand_k=1`) predicted **single-digit
  milliseconds**; reflective/composer config (`beam=3,max_steps=8,cand_k=3`)
  predicted **tens of milliseconds, comfortably under 100ms**. Both
  well inside any single `run_rules` fixpoint tick's budget.
- **P2 (linear scaling):** doubling codebook size should roughly double
  wall-clock time for a fixed config, confirming/falsifying the `O(codebook
  size)` claim empirically rather than by formula alone.
- **P3 (the 2000+-entry `RuleSummary`-adapted codebook):** predicted **tens
  to low hundreds of milliseconds** for the composer config, extrapolating
  P1/P2 linearly from 407→2229 (~5.5x) — i.e., roughly 5.5x the 407-entry
  composer-config number.
- **P4 (multi-shape / batching):** `load_parts` (`shape_decode.rs:239-`) is
  a **full graph scan + per-node attr deserialisation, re-run from scratch
  on every single `ShapeDecode` call**, independent of `scope`/`exclude`
  (§1 read of `apply_scope`/`apply_exclude`: both filter the list `load_parts`
  already fully built — they never reduce the initial scan). Predicted:
  this re-scan is genuine, real, currently-duplicated work when N
  observations decode against the same codebook in sequence — a caching/
  amortisation opportunity independent of whether the exact-match search
  itself benefits from batching.

**GO/NO-GO decision criteria, registered now:**

- **GO** (build a pre-filter) if, at **today's real scale** (407 for
  `ShapeSignature`, or the adapted 2229-entry `RuleSummary` test), any
  real-caller configuration measures **>100ms median** (a threshold chosen
  because it is the rough order where a single decode call starts to be
  perceptible inside an interactive `run_rules` fixpoint tick, per this
  project's own real-time-caller class existing at `max_steps=1`) — OR if
  the linear-scaling trend (P2) extrapolates past 100ms before codebook size
  reaches 5,000 (a size this project's own codebook-growth history, 24→46→
  139→407 in successive rungs, makes plausible to reach within a few more
  growth cycles).
- **NO-GO, name the revisit scale** if every real-caller configuration at
  every measured size (real + synthetic sweep to at least 10,000) stays
  comfortably under 100ms, in which case report the actual measured
  headroom and the codebook size at which the trend would cross the
  threshold, rather than asserting "fine forever."
- **Structural-bucketing soundness criterion**, registered before the
  bucket-balance numbers are analysed in the RESULTS doc: a structural
  pre-filter (predicate-set / `kind` / arity bucketing) is only a **sound,
  useful** design if (a) it is derivable from data every `ShapeSignature`
  already holds (no new attrs, no learned embedding), AND (b) it measurably
  narrows the scan for a real majority of real callers — NOT necessarily
  for every caller, since a domain-dominated codebook (§0's 64.6%-stroke
  finding) may leave the largest bucket still large. A bucketing scheme
  that only helps the minority-domain callers is still a real, honestly-
  reported partial win, not a failed design, AS LONG AS this is stated
  plainly rather than oversold.
- **Embedding (DeepGAR-style) criterion**, registered before evaluation:
  sound only if `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4's own
  unresolved condition (true low-rank / shared-generator structure, not
  mere value-alphabet compression) can be argued to hold for THIS
  representation — predicted, before checking, that it likely CANNOT be
  established without exactly the kind of learned/statistical
  infrastructure this project's standing discipline avoids, making
  structural bucketing the predicted winner on symbolic-preference grounds
  ALONE even before the soundness question is separately checked.

**What would falsify "not yet a bottleneck":** any real production
`ShapeDecode` call (present in a real seed today, at today's real codebook
size) measuring in the hundreds-of-milliseconds-or-worse range. This has
NOT been observed in the orientation pass and is not expected, per P1.

---

## 3. Build criteria (only if §2's GO fires)

If GO: the smallest correct version is a structural bucket index — computed
once per codebook (keyed by `codebook_type`), invalidated the same way this
project's own `codebook_epoch` gates re-decode elsewhere
(`shape_decode_loop.json`), sitting in front of the UNCHANGED exact
`score_part_for_residual`/`covers_relation` scan (never touching
`AntiUnifyWitness`/`Covers` themselves, per this rung's explicit exclusion).
Decode output must be **byte-identical** before/after on a real regression
set — this is a shortlist-then-verify speed optimisation, never a
correctness change. No new Rust `Term` variant (a cache/index keyed the same
way other epoch-gated structures are is in scope; a new DSL primitive is
not, per this rung's explicit exclusion).

---

## Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/shape-decode-scaling
export PYTHONPATH="$(pwd)/runners/dsl/python:$(pwd)"
python3 scripts/shape_decode_scaling_bench.py     # §2's latency sweep + bucket-balance report
```
