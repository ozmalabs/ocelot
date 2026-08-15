# Wobble-position discipline for shape identity — PREREG

**Charter.** `SHAPE_AUDIT.md` §3.1 named a real, live, silently-corrupting bug:
`CapabilityAxis` identity was a truncated, order-dependent string join that
could both split one concern into two axes and suppress a genuinely novel
mint. Before doing any new work this rung must (1) independently verify what
was actually fixed already, not trust recollection, and (2) investigate a
NEW, distinct design question raised in a live discussion about biological
information systems: DNA's genetic code is redundant at the codon's THIRD
("wobble") position — an EXPLICIT, principled hierarchy of load-bearing
(exact-match-required) vs noise-tolerant (variation-tolerant) positions, not
a flat, equally-weighted comparison across every field. Does
`CapabilityAxis`/`ShapeSignature`/`ProblemShape` identity currently treat ALL
signature components as equally load-bearing, and if so, is that a REAL,
currently-live problem, demonstrated on real data — not a hypothetical one?

## Part 1 — verification of prior work (facts, not hypotheses; registered
because the task brief explicitly required checking this before trusting a
session recollection)

Read directly, in full, before writing anything below:
`docs/research/engine_substrate/SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md`,
`docs/research/engine_substrate/META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md`,
commit `abadbab` (`git show abadbab --stat`), and the CURRENT
`domains/reflective_faculty.py::induce_concern` +
`runners/dsl/src/shape_decode.rs` + `runners/dsl/src/term.rs` source.

**What was already fixed, verified by reading the code directly (not the
commit message alone):**

1. `SHAPE_AUDIT_PATTERN_C_FIXES` (merged before `abadbab`, on top of `4f24abb`):
   `induce_concern`'s derived `capability_keys` join
   (`domains/reflective_faculty.py`, current line ~1343) changed from
   `"induced_" + "_".join(preds[:3])` (truncated at 3, order-dependent) to
   `"induced_" + "_".join(sorted(preds))` — now untruncated and
   order-independent. This is the EXACT defect `SHAPE_AUDIT.md` §3.1 named.
   Confirmed live in the current worktree: two 4-predicate observations
   sharing their first 3 heads and diverging at the 4th now mint two
   DISTINCT axes (previously collided into one, suppressing the second
   mint — the dangerous direction).
2. `abadbab` (`meta-shape-arity-key-fixes`) fixed two DIFFERENT, narrower
   bugs, neither of which is the truncation/ordering defect (that was
   already fixed by the time this merge landed):
   - Bug 1: meta-shape (`ms_`) recognition was ARITY-EXACT (an extra
     attribute on an otherwise-matching item fell to residual instead of
     recognized) — fixed with a new grain-local `CoversOpen` Term
     (`runners/dsl/src/term.rs::covers_open_value`), superset-tolerant,
     never subset-tolerant.
   - Bug 2: the `induced_` key's `"_"`-join is a LOSSY separator
     (`["a_b","c"]` and `["a","b_c"]` both join to `"induced_a_b_c"`) —
     fixed by percent-escaping (`_`→`%5f`, `%`→`%25`) in
     `domains/reflective_faculty.py`. Measured real prevalence at that site:
     **zero** (61-predicate vocabulary, only 1 predicate contains `_`, 0
     collisions). The SAME lossy join exists a second time, in Rust
     (`shape_decode.rs`, `MetaShapeMint`'s minted `ms_` NAME, used as a
     mint-once guard) — measured 23 reachable collisions over the real
     1235-key attribute vocabulary there — and was **deliberately NOT
     fixed**, because the honest fix (a structural `pred_key` attr, not a
     rename) carries its own checkpoint-resume re-mint hazard and needs its
     own rung. Named, not built, in that document's own §7.1.

**Conclusion of Part 1:** the truncation/order-dependence defect the session
recalled is real and was fixed, correctly, before `abadbab`. `abadbab` fixed
two further, different defects (arity-exactness at the `ms_` grain;
separator-collision at the `induced_` grain) and explicitly left one sibling
defect (the `ms_`-grain separator collision) named and unfixed for a future
rung. None of this prior work asked or answered the NEW question below.

## Part 2 — the new question: is there a wobble-position gap?

**The question, stated precisely.** A shape signature in this substrate is a
SET of POSITIONAL relations (`shape_decode.rs::covers_relation`'s own
framing, reused by `META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md`).
Within one relation `[predicate, value, ...]`, does the substrate ever
compare EVERY leaf position with equal, flat, exact-match strictness where
some positions are actually more load-bearing than others (a codon-style
1st/2nd-position-exact, 3rd-position-tolerant asymmetry) — and if it does,
does that flatness cause a REAL, demonstrated failure on real data?

**Where to look**, per the task brief: `CapabilityAxis` identity
(`domains/reflective_faculty.py::induce_concern`), `ShapeSignature`/`MetaShape`
matching (`shape_decode.rs`, `seeds/shape_vocabulary.json`,
`domains/meta_shape.py`), and `ProblemShape` identity
(`domains/problem_shape.py`, `seeds/problem_shape_growth.json`) — checked
against real instances from Bigville, MBPP/program-synthesis structures, or
the solver toolbox, not synthetic constructions, wherever real instances
exist to check against.

**GO/NO-GO bar**, mirroring `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_PREREG.md`'s
own discipline (the closest precedent in this tree for "is a real defect
here worth a targeted fix"): GO requires BOTH (1) a REAL case — found in
existing code/data or literally constructed and run against the live
engine, not hypothetical — where either (a) two genuinely-equivalent
observations mint as distinct capabilities/shapes because a
non-essential field differs, or (b) two genuinely-different observations
wrongly collapse onto the same shape because a should-be-load-bearing field
is under-weighted or ignored; AND (2) the fix that would resolve it is
GENUINELY NARROW — an explicit per-field significance marking (which
positions are exact-required vs tolerant), not a general re-design, not a
new comparison algorithm, not a fix to a DIFFERENT kind of defect (e.g. a
missing axis is not a wobble-weighting defect, even if it also causes a
wrong collapse). NO-GO is registered as an equally valid, equally reportable
outcome if either bar is not met, or if the real case found needs a
different fix shape than field-significance-marking.

**Investigation plan, registered before locking the verdict:**

1. Read `covers_value`/`covers_open_value`/`ShapeDecode`'s relation-level
   matching to establish what significance-marking ALREADY exists
   (WILD, `Transform{dim,delta}`, `DimInfer`, `CoversOpen`) and at which
   layer it operates.
2. Census every real (non-test-synthetic) call site of `induce_concern`
   across `domains/*.py` — which ones pass an explicit `name_hint` (bypassing
   the derived-key path entirely) vs which rely on the derived key over real
   varying data.
3. Re-derive, independently, whether the `sd_mint_quantum`/`sd_dedup_existing`
   exact-key comparison is the PRIMARY recognition mechanism or a narrow
   fallback guard, by reading which rule actually recognises a covered
   observation (`sd_recognize`, via `ShapeDecode`) vs which rule uses the
   flat key (`sd_mint_quantum`'s novelty guard, reached only when nothing in
   the codebook covers the observation at all).
4. Check `ProblemShape`'s fixed 5-axis signature (`domains/problem_shape.py`)
   against real `solve_*` Goal kinds from `domains/solver_dispatch.py`'s own
   `mint_solve_*_goal` functions — construct real Goals live against the
   full-seed-boot engine (the same fixture `tests/test_problem_shape_migrated.py`
   uses) and read back their signatures/keys.
5. Check Bigville and MBPP/program-synthesis paths for any direct use of
   `induce_concern`/`CapabilityAxis` or an analogous flat-signature identity
   comparison with real, naturally-varying (non-hand-fixed) predicate
   content.

**Scope constraint carried from the task brief, registered so it binds the
verdict:** `domains/solver_dispatch.py` and
`docs/research/engine_substrate/SOLVER_CAN_ADAPTER_*` are a concurrent
sibling agent's active territory and must not be touched (read-only is fine).
Any real finding located there, or tightly coupled to it, is named and
reported, never fixed in this rung, regardless of how narrow the fix would
otherwise be.

## Regression population, registered

If GO: `tests/test_meta_shape_arity_migrated.py`,
`tests/test_problem_shape_migrated.py`,
`tests/test_dimension_inference_migrated.py`, `tests/test_axis_mint_novelty.py`,
`tests/test_composer_driver_migrated.py`, plus the full Rust suite if any
`.rs` file changes (`cargo test --lib --release -- --test-threads=1`,
774/774 expected per the task brief). If NO-GO: the same Python population is
still run once, unpaired (no code changed to pair against), to confirm the
current tree's baseline state honestly rather than assumed.
