# Wobble-position discipline for shape identity — RESULTS

**Prereg:** `SHAPE_WOBBLE_POSITION_PREREG.md`, committed (`c6d816b`) before any
further investigation past what Part 1 required to verify. Worktree
`/home/matt/ocelot-shape-wobble-position`, branch `shape-wobble-position`,
detached from `main` at `fff8555` (verified via `git log --oneline -1 main`
immediately before worktree creation).

**Verdict: NO-GO on building a per-field significance/wobble-weighting
mechanism.** No real case was found where CapabilityAxis/ShapeSignature
identity's flat comparison — beyond what `abadbab` and
`SHAPE_AUDIT_PATTERN_C_FIXES` already fixed — produces a wrong outcome, and
where the fix would be the narrow "which positions are exact vs tolerant"
marking the brief pre-authorized. One real, live-constructed defect WAS found
in the course of this investigation (`ProblemShape` axis collapse, §4) but it
needs a different fix shape (signature coverage, not per-field weighting) and
sits in territory adjacent to a concurrent sibling investigation — named
here, not built. **No code changed in this worktree.**

---

## 1. Part 1 — what `abadbab` actually fixed (independently verified, not
assumed from the session's own recollection)

Read directly: `git show abadbab --stat` and its full merge message;
`SHAPE_AUDIT_PATTERN_C_FIXES_RESULTS.md` in full;
`META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md` in full; the CURRENT
`domains/reflective_faculty.py::induce_concern` (lines 1315-1349, this
worktree) and `runners/dsl/src/term.rs::covers_value`/`covers_open_value`
(lines 3910-4040).

**Two separate rungs, two separate fixes, confirmed by reading the code, not
the commit prose:**

| rung | commit | what it fixed | is this SHAPE_AUDIT §3.1's truncation/order bug? |
|---|---|---|---|
| `shape-audit-pattern-c-fixes` | pre-`abadbab`, on `4f24abb` | `CapabilityAxis` key: `preds[:3]` (truncated) + insertion order → `sorted(preds)` (untruncated, order-independent) | **YES — this is the exact fix** |
| `meta-shape-arity-key-fixes` | `abadbab` | Bug 1: `ms_` meta-shape recognition was arity-exact (an extra attribute → residual instead of recognized) → new `CoversOpen` Term. Bug 2: the `induced_` key's `"_"` join is a lossy separator (`["a_b","c"]` and `["a","b_c"]` collide) → percent-escaping | **NO — a different pair of bugs, on top of the already-fixed truncation/order defect** |

Confirmed live in this worktree (`domains/reflective_faculty.py:1343`):

```python
key = name_hint or (("induced_" + "_".join(_key_component(p) for p in sorted(preds)))
                    if preds else "induced_concern")
```

— sorted (order-independence, from the pre-`abadbab` fix), `_key_component`
percent-escapes each predicate (separator-collision safety, from `abadbab`),
untruncated (from the pre-`abadbab` fix). Both fixes are present and stacked
correctly; neither undoes the other.

**One thing `abadbab` explicitly measured and declined to fix, on the
record, and it matters for §3 below:** the SAME lossy-join shape exists a
second time, in Rust, on `MetaShapeMint`'s minted `ms_` NAME — 23 reachable
collision pairs over the real 1235-key attribute vocabulary, left named, not
built, because the honest fix (a structural `pred_key` attr) carries a
checkpoint-resume re-mint hazard and needs its own rung. This is a
SEPARATOOR-COLLISION residual, not a wobble-weighting one — mentioned here
only because Part 1 must report it accurately, not because this rung acts on
it.

**Part 1 conclusion:** the session's recollection was correct in substance
(the truncation/order bug is fixed) but attributed the fix to the wrong
commit — it landed in `shape-audit-pattern-c-fixes`, before `abadbab`.
`abadbab` fixed two different, real defects on top of that. Nothing in
either prior rung asked the wobble-position question below.

---

## 2. Where per-field significance ALREADY exists, and at which layer

This is the load-bearing finding for the NO-GO: **the wobble-position
discipline the brief describes is not absent from this substrate — it is
already the architecture of the layer that does the actual recognition.**
Read directly, all confirmed live in this worktree:

1. **WILD, per value-slot, author-declared** (`term.rs::covers_value`,
   `is_wild`). A codebook part's signature is a set of `[predicate, value]`
   relations; the predicate position is always compared exactly, the value
   position may be authored as WILD (fully tolerant) or a literal (fully
   exact). This is already a two-tier, per-POSITION significance marking —
   the codon analogy holds almost exactly: predicate = position 1/2
   (load-bearing), value = position 3 (author decides whether it's allowed
   to wobble).
2. **`Transform{dim, delta}` — per-DIMENSION tolerance, CLAUDE.md's own
   words**: *"a consistent per-dimension quantum delta... the predicate slot
   never transformable"* (`shape_decode.rs`'s `sd_transform_decode` design,
   quoted directly from this repo's own architecture doc). This is a graded
   hierarchy stated explicitly: the predicate is ALWAYS load-bearing: a
   dimension's VALUE can vary by a bounded, structured amount (a transform)
   without the observation being treated as a different shape.
3. **`DimInfer`** promotes a residual to a newly-minted `LatentDimension`
   only when the residual COUPLES across several observed dimensions in a
   way no existing generator explains — i.e., the substrate already
   distinguishes "this variation is noise" (rung 1/2, recognized/
   transformed) from "this variation is signal that needs a new axis" (rung
   3, mint a dimension) from "this is genuinely novel" (rung 4, mint a
   quantum) — a four-tier significance ladder, not a flat binary.
4. **`CoversOpen`** (landed the same day as `abadbab`, §3.3 of
   `META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md`): at the
   whole-signature level, relations DECLARED in a codebook part's pattern
   are exact/load-bearing (subject to their own internal WILD markers);
   relations NOT declared are fully tolerated (superset-match). This is a
   second, coarser two-tier hierarchy, one level up from (1).

**Conclusion of §2:** every one of these is exactly the shape the brief
describes — an explicit, author- or rule-controlled hierarchy of which
positions must match and which may vary — and all four are already landed,
several of them the same day as the fixes this rung was asked to verify. The
open question was never "does this substrate have wobble tolerance" — it is
"does it have it in the WRONG place" (the flat, exact-match layers).

---

## 3. The flat, exact-match layers — real prevalence, measured

Two layers remain genuinely flat (every predicate compared with equal, exact
strictness, no WILD-equivalent): `CapabilityAxis`'s `induced_` key
(`sd_mint_quantum`'s novelty guard) and `ProblemShape`'s `signature_key`
(§4). This section is `induced_`; §4 is `ProblemShape`.

### 3.1 The exact-key comparison is NOT the primary recognition mechanism

Read `seeds/shape_decode_loop.json`'s `sd_decode`/`sd_recognize`/
`sd_mint_quantum`/`sd_dedup_existing` rules directly (all four, in full, in
this worktree). **Recognition of a genuinely covered observation
(`sd_recognize`) never touches `capability_keys`/`obs.key` at all** — it
reads `obs.residual` (computed by the tolerant `ShapeDecode` Term against the
held codebook, i.e. everything in §2). The flat exact-key comparison
(`Eq(capability_keys, obs.key)`) appears in exactly one place:
`sd_mint_quantum`'s NOVELTY GUARD, reached only when `ShapeDecode` has
ALREADY failed to explain the observation (non-empty residual, transform
rung failed, dimension rung failed) — i.e. only among observations the
codebook has given up on. Its stated purpose (`sd_mint_quantum`'s own
comment, quoted verbatim): *"mechanical, stable across recurring
identical-shape observations from world perception... reusing it keeps ONE
definition of 'same concern' instead of inventing a second."* It exists to
stop the SAME unrecognized residual from minting a fresh axis every tick, not
to discriminate between different residuals.

### 3.2 Every real call site supplies its own significance judgement already

Census of every `induce_concern(` call in `domains/*.py` (16 sites, all
read in full in this worktree):

| file:line | `name_hint` supplied? |
|---|---|
| `metrical_reading.py:598` | yes (`"meter_" + ...`) |
| `reading_collapse.py:1691` | yes (`"reading_" + ...`) |
| `code_reading.py:377` | yes (caller-supplied `name_hint`) |
| `conversation_action.py:468` | yes (`name=name`) |
| `conceptualizer.py:393` | yes (`tag`) |
| `substrate_extension.py:541` | yes (`name_hint`) |
| `cross_text_prior.py:1054` | yes (`"styleaxis_" + ...`) |
| `character_compose.py:580` | yes (`name_hint`) |
| `self_capability_collapse.py:399` | yes (`name=name`) |
| `consumption_quality.py:156,240,405` (×3) | yes, all three |
| `recount_faculty.py:168,172` (×2) | yes, both |
| `ink_decode.py:889,1143` (×2) | yes, both |

**All 16 real call sites pass an explicit `name_hint`, unconditionally.**
The derived (flat, exact-match) key path is NEVER exercised by real,
data-driven code in `domains/`. This is itself the correct discipline
applied at the right layer: the human/module AUTHOR — who actually knows
which fields are load-bearing for THEIR concern — supplies the identity
directly, rather than the substrate guessing per-field significance
generically. That is arguably the wobble principle already in effect one
level up: significance is marked EXPLICITLY, by the party with the domain
knowledge to mark it correctly, exactly as the brief's own framing asks for
— it is just not automatic.

The only sites where the derived-key path runs at all are 6 small
synthetic/gate scripts (`scripts/magnitude_fit_gate.py`,
`predicate_grounding_gate.py`, `concern_grounding_gate.py` ×2,
`concern_induction_gate.py` ×2, `tests/fixtures/composer_driver_parity/capture.py`),
already measured twice, independently, by the two prior rungs: zero real
collisions from truncation/ordering (fixed anyway, conservatively), zero
real collisions from the separator (measured, `abadbab` §4.1).

### 3.3 Bigville and MBPP/program-synthesis: no real instance to check

Bigville (`domains/bigville_entities.py`, `seeds/bigville_*.json`,
`worlds/bigville_*.py`) never calls `induce_concern` and never constructs a
`CapabilityAxis` — grepped for `induce_concern|CapabilityAxis|ShapeSignature|
ShapeDecode|MetaShape` across every Bigville file; the one hit
(`seeds/bigville_drama_social.json`) is a prose comment analogising Mary's
theory-of-mind inference to "the same held-codebook decode as ShapeDecode",
not an actual call. The user's memory note on Bigville as a validating test
substrate does not apply here — there is nothing in Bigville that exercises
this mechanism.

MBPP/program-synthesis's own signature grain (`prog_chunk_growth.json`'s
`chunk_rels`) is a DIFFERENT codebook (`ShapeSignature` with `Covers`, not
`CapabilityAxis`) already investigated in depth and NO-GO'd by
`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` for a related-but-distinct
question (semantic-equivalence rewriting before comparison, not per-field
significance weighting within a comparison) — that document's own residual
list explicitly reserves "extend `Covers`" as a NAMED, not built,
follow-on, contingent on prevalence that measured zero. Re-litigating it here
would not be new work; it is out of this rung's charter, which is
significance-marking, not statement-count rewriting.

**§3 conclusion:** no real case was found matching either failure direction
(a) or (b) at the `CapabilityAxis` grain beyond what is already fixed. The
flat exact-key comparison that remains is a narrow, deliberately strict
novelty-dedup guard, reached only for content the tolerant recognition layer
has already failed to explain, exercised in real code only via
author-supplied identities.

---

## 4. `ProblemShape` — a REAL, live-constructed collapse found, and why it
is NOT this rung's fix to build

`domains/problem_shape.py::goal_signature` (lines 74-98) extracts a FIXED
5-axis signature from a `solve_*` Goal — `has_bound`, `has_direction`,
`has_statement`, `has_targets_correspondence`, `has_targets_mt` — reading
only `at.get("bound")`, `at.get("direction")`, `at.get("statement")`, and
two edge presences. Nothing else the Goal carries is read.

**Constructed live**, in this worktree, against the SAME full-seed-boot
fixture `tests/test_problem_shape_migrated.py::agent` uses
(`WorldAdapter(seeds=())` + `load_all_seeds`), three real, differently-kinded
`solve_*` Goals from `domains/solver_dispatch.py`'s own real mint functions:

```python
mt = sub.add_node('Microtheory', {'name': 'mt1'})
g_relax = sd.mint_solve_can_relax_goal(a, mt)
g_exact = sd.mint_solve_can_exact_goal(a, mt, treewidth_bound=4)
g_bp    = sd.mint_solve_can_bp_goal(a, mt)
```

Result — read back via `ps.goal_signature`/`ps.signature_key`:

```
relax  kind=solve_can_relax  key=ps_has_targets_mt=yes
exact  kind=solve_can_exact  key=ps_has_targets_mt=yes
bp     kind=solve_can_bp     key=ps_has_targets_mt=yes
```

**All three collapse to the byte-identical signature and key**, because
`mint_solve_can_exact_goal` writes `treewidth_bound` (not `bound`) and
`mint_solve_can_bp_goal` writes `combine`/`max_rounds`/`epsilon` — none of
which `_AXES` reads at all. This is a real, live, currently-reproducible
instance of failure direction (b): *"two genuinely-different observations
wrongly collapsing onto the same shape because a should-be-load-bearing
field is being... ignored."* The field (`treewidth_bound`) is not
under-weighted relative to the others — it is completely absent from the
representation.

**Why this is NOT the fix this rung is chartered to build:**

1. **Wrong fix shape.** The bar this rung registered (PREREG §2) requires
   the fix to be a per-field SIGNIFICANCE marking — which existing positions
   are exact vs tolerant. That does not apply here: there is no existing
   position being mis-weighted; there is a MISSING position. The fix this
   defect actually needs is signature COVERAGE (add axes for
   `treewidth_bound`/`combine`/etc., or some other structural extension) —
   a different, though related, defect class from the one the brief
   pre-authorized building a fix for. Building it would be scope creep
   dressed as the requested fix.
2. **Wrong territory.** `domains/problem_shape.py` and
   `domains/solver_dispatch.py` are the SAME subsystem
   (`QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`'s Rung 1/Rung 3), built in
   the same recent arc (`git log`: *"ARC: question_driver Rung 1 -- wire the
   7-item reasoning toolbox as solve_* Resolvers"*). The task brief
   explicitly named `domains/solver_dispatch.py` and
   `SOLVER_CAN_ADAPTER_*` as a concurrent sibling agent's active territory,
   not to be touched regardless of file overlap. `problem_shape.py` is not
   literally that file, but it is tightly coupled to it (reads
   `solve_*` Goal attrs the sibling's own NL-adapter work is actively
   touching) — building a fix here risks exactly the collision the task
   brief was written to prevent.

**Reported, not built**, per this codebase's own established discipline for
exactly this situation (`SHAPE_AUDIT.md` §4.1's Pattern C generalisation, and
`abadbab`'s own §7.1 precedent for the sibling `ms_`-collision defect it
found and declined to fix in the same rung): a future rung, scoped to
`domains/problem_shape.py`/`domains/solver_dispatch.py` specifically (and
coordinated with whatever the sibling's NL-adapter work lands), should widen
`_AXES` to cover the solve-kind-discriminating attrs each `mint_solve_*_goal`
function actually writes (`treewidth_bound`, `combine`, `max_rounds`,
`epsilon`, `max_exact_n`, `mode`) — an axis-coverage fix, not a
significance-weighting one.

---

## 5. GO/NO-GO, applied against the registered bar

PREREG §2's bar: GO requires (1) a real case matching failure direction (a)
or (b), AND (2) a genuinely narrow per-field-significance fix.

| candidate | (1) real case found? | (2) narrow significance-marking fix? | verdict |
|---|---|---|---|
| `CapabilityAxis` (`induced_` key) | No — zero real collisions beyond what's already fixed (§3) | N/A | NO-GO |
| `MetaShape` (`ms_` key/name) | Already found and explicitly deferred by `abadbab` (a separator-collision, not a significance-weighting defect) | N/A — different defect class | out of scope, already correctly handled |
| `ProblemShape` (`signature_key`) | **Yes** — live-constructed, real (§4) | **No** — needs axis coverage, not significance-weighting; also wrong territory | NO-GO (for THIS rung) |

**No candidate satisfies both bars.** Per the registered rule, this is a
NO-GO on building anything in this rung. No code changed.

---

## 6. Regression — confirming the baseline honestly (no diff to pair against)

No file under version control was edited in this worktree; there is nothing
to pair a before/after against. Run once, to confirm the current tree's
state rather than assume it, same engine (`_native.abi3.so`, git-tracked at
`3b2e3c0`, unmodified — provenance probe: `[1, 2, 3] (1, 2, 3) True`,
`tests/test_engine_provenance_migrated.py` 10/10 passed):

```
tests/test_meta_shape_arity_migrated.py    9 passed
tests/test_problem_shape_migrated.py       (included in the 39-test run below)
tests/test_dimension_inference_migrated.py (included)
tests/test_axis_mint_novelty.py            (included)
tests/test_composer_driver_migrated.py     1 failed / N passed
  -> 38 passed, 1 failed in 108.03s
```

The one failure, `test_ground_concern_dispatch_parity`, is on the EXACT
failing-node-id list `META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES_RESULTS.md`
§6.2 already reports as pre-existing (that document's own paired
before/after run shows it failing identically on the untouched pristine
baseline). Since this rung changed no code, that pairing already establishes
this failure is not attributable to anything done here — re-deriving a fresh
pair against an unmodified tree would only reproduce the same result. No
Rust rebuild was performed or needed (no `.rs` file was touched).

---

## 7. What this document does NOT establish

- **It does not establish that per-field significance weighting is never
  useful anywhere in this substrate** — §2 shows it is already used
  extensively, just not at the two flat layers this rung was asked to check.
  This document only establishes that THOSE two layers, as measured today,
  do not have a live defect the requested fix shape would resolve.
- **It does not establish the `ProblemShape` axis-collapse (§4) is
  unimportant** — it is real and reproducible; it is out of scope for a
  different reason (wrong fix shape + wrong territory), not because it does
  not matter.
- **§3.2's "zero real collisions" is a mechanism/census claim, not a
  frequency claim** — CLAUDE.md's own standing rule ("synthetic-proven
  mechanism ≠ benchmark value, report both") applies: this document shows
  every real call site supplies its own name_hint and the derived path is
  only reached by small synthetic vocabularies measured twice at zero
  collisions; it does not claim to have observed the live daemon's full
  history of `induce_concern` calls in production.
- **The `abadbab`-deferred `ms_`-grain separator-collision fix (§1) is still
  open** — unrelated to this rung's verdict, not re-investigated here beyond
  confirming it is still accurately described as named-not-built.

---

## 8. Reproduce

```bash
cd /home/matt/ocelot-shape-wobble-position

# Part 1 verification
git show abadbab --stat
sed -n '1315,1349p' domains/reflective_faculty.py

# Part 2 / §2: existing significance-marking layers
sed -n '3900,4040p' runners/dsl/src/term.rs

# §3.2: the domains/*.py census (all pass name_hint)
grep -n "induce_concern(" domains/*.py

# §4: the ProblemShape live construction
PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import solver_dispatch as sd
from domains import problem_shape as ps
a = WorldAdapter(seeds=()); load_all_seeds(a)
sub, native = a.s, a.inner
mt = sub.add_node('Microtheory', {'name': 'mt1'})
g_relax = sd.mint_solve_can_relax_goal(a, mt)
g_exact = sd.mint_solve_can_exact_goal(a, mt, treewidth_bound=4)
g_bp    = sd.mint_solve_can_bp_goal(a, mt)
for label, g in (('relax', g_relax), ('exact', g_exact), ('bp', g_bp)):
    sig = ps.goal_signature(sub, native, g)
    print(label, sub.node(g)['attrs'].get('kind'), ps.signature_key(sig))
"

# §6: regression population (single run, nothing to pair -- no code changed)
PYTHONPATH=runners/dsl/python:. OZMA_SEED_PERSIST_DISABLED=1 python3 -m pytest -q \
  tests/test_meta_shape_arity_migrated.py tests/test_problem_shape_migrated.py \
  tests/test_dimension_inference_migrated.py tests/test_axis_mint_novelty.py \
  tests/test_composer_driver_migrated.py
```
