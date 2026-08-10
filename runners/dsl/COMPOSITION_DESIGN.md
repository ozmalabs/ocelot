# Composition of generators — RUNG-2 length-≤2 extension — DESIGN

Status: **DESIGN + IMPLEMENTED (bounded clean extension).** This does NOT
hit the STOP condition: it is a bounded (length ≤ 2), Occam-ordered
extension of `eval_dim_infer` that reuses `build_candidate` UNCHANGED,
needs only additive result-Dict fields + additive seed-rule reads, and
touches neither `build_candidate`'s count contract nor the seed rung
ORDER. See §2/§3/STEP-2 below for the argument.

Invariants honoured: GROUNDED signatures stay integer-lattice only
(`coord_ints` → `None` on a `Float` slot is unchanged and still correct);
every step is an integer-`k` quantum; no continuous-parameter generator is
introduced (out of scope, per the creator directives).

## 0. The concept

Today rung 2 infers a SINGLE generator (`rotation90` / `reflection_r` /
`reflection_c` / `scale2` / `modular`) composed with a linear rung-1
residual. Many real transforms need TWO NON-LINEAR generators together —
rotate THEN scale, reflect THEN scale, rotate THEN modular-cycle — where
neither reduces to the other nor to a linear residual. A configuration is
a short SEQUENCE of `(generator, k)` steps (the "integer vector over
generators" / prime-exponent form); composition is applying them in
order, then letting the shared rung-1 check absorb the leftover linear
residual.

## 1. Search space & bound

**Length ≤ N = 2.** N=2 is justified because it is the smallest length
that expresses a genuinely-irreducible composite (a single non-linear
generator + a linear residual is already length 1), and because the real
targets named are all pairs (rotate∘scale, reflect∘scale, rotate∘cycle).
Higher N is deferred: it multiplies the candidate count geometrically and
its capability is not yet demonstrated behind a gate. If a future pair of
gates shows length-3 is needed, this arm generalises by the same pattern
(the code keeps the step list a `Vec`, not a fixed pair).

**Distinct generators only.** A length-2 step `(g, g)` is the SAME
generator applied `k_a + k_b` times — i.e. `g` at a higher single `k`,
which is `g`'s OWN dimension and belongs at length 1 with an extended
`params` range, not as a 2-vector. Restricting length-2 to
`name(g_a) != name(g_b)` is exactly the canonical (reduced) prime-exponent
form, and it has a load-bearing side effect: **a single-generator codebook
produces ZERO length-2 attempts**, so every existing single-generator
cargo test keeps its exact `checked` count (they each hold one generator).

**Both orders.** Order matters in general (scale2 re-derives its bbox min
each step; rotation/reflection re-derive bbox extent), so BOTH `(g_a,g_b)`
and `(g_b,g_a)` are tried. On the origin-normalised integer lattice the
specific irreducible pairs in the current generator set — `scale2` × an
isometry (`rotation90`/`reflection_r`/`reflection_c`) — happen to COMMUTE
(uniform scaling commutes with a linear isometry, and both renormalise to
min 0), so both orders yield the SAME image; the tie-break (below) makes
the reported sequence deterministic. `modular` × `scale2` is genuinely
non-commutative (the wrap is not scale-equivariant), so trying both orders
is not merely defensive. The dihedral compositions (`rotation90` ×
`reflection_r`, etc.) REDUCE to a single rotation/reflection and are
therefore claimed at length 1 by Occam — never surfacing as length-2.

**Candidate count per held part** (full seed: 5 generators; per-generator
`params` ≈ 3): length-1 ≈ `Σ|params| = 13`; length-2 ≈ `20` ordered
distinct pairs × `≈6.76` param products ≈ `135`; total ≈ `148`
`build_candidate` calls per `DimInfer` evaluation per dim-typed part.
Tractable: parts WITHOUT `dim_types` are skipped before the generator loop
(unchanged), so the multiplier only touches dimension-typed codebooks.

## 2. Occam / identifiability

**Composition length is the FIRST ranking key.** The ranking tuple becomes

```
(steps.len(), residual_dims, base_name, ks_vec, generator_names_vec)
```

With `steps.len()` STRICTLY primary, ANY length-1 success beats ANY
length-2 success — a length-2 composition can NEVER beat a length-1
explanation for the same observation (the analog of the rung-1<rung-2
order the seed guards already enforce). A single-generator-explainable
observation therefore still reports length 1 (verified: pure `scale2` k=1
stays `{generator:"scale2", k:1, length:1}`; pure rotation stays length 1;
dihedral compositions reduce to a single rotation at length 1). Within
length 1 the sub-ordering `(residual_dims, base_name, ks=[k])` is
byte-identical to the committed `(1 + residual_dims, base_name, k)` key
(the `1+` was a uniform constant across all length-1 attempts), so no
committed single-generator verdict changes. The trailing
`generator_names_vec` key only breaks a residual+base+ks tie between two
different generator pairs — a strict determinism refinement over the old
first-seen behaviour, unreachable by any single-generator fixture.

## 3. Reuse, no contract change

Confirmed: the composite is produced by iterating `apply_generator_k`
(`transformed_a = apply_generator_k(a, .., part.sig, k_a)` then
`transformed_ab = apply_generator_k(b, .., &transformed_a, k_b)`) and
handing the result to `build_candidate` UNCHANGED. Each
`apply_generator_k` is a count-preserving per-relation remap
(`out.len() == sig.len()`), so a composition of two is still
count-preserving — `build_candidate`'s FIRST check
(`sorted_h.len() != sorted_o.len() => None`) still holds, exactly as it
does for length 1. **No part needs a cardinality change; the count-equality
prefilter stays.** No `build_candidate` edit at all.

## 4. Graph representation of a composite

Minimal representation chosen: **one composite `Transform` node + one
composite `LatentDimension` node**, both labelled
`latent:<gen_a>+<gen_b>` and both carrying the step SEQUENCE as parallel
`generators` / `ks` list attrs. NOT one node per step — a single composite
node keeps mint-once trivial (one `has_transform` edge, one
`has_latent_dimension` edge, guarded by the existing "no `has_transform`
edge yet" idiom) and re-decode-terminating (unchanged epoch/guard logic).

**Result-Dict change (additive):** `DimInfer` gains
- `length` (Int) — number of generator steps (1 or 2);
- `generators` (Tuple of name Values) — the step generators in order;
- `ks` (Tuple of Int) — parallel `k` values;
- `latent_name` (Str) — the composite label body (`"a+b"`, or the single
  name for length 1) used to build the `latent:` prefix.

The scalar `generator` / `k` fields are KEPT (first step) so the length-1
seed reads and every committed test are byte-identical. `latent_name`
equals the single generator name for length 1, so
`StringConcat("latent:", latent_name)` yields the identical
`latent:rotation90` label the seed produced from `field:"generator"` — the
seed's two label sites switch from `"generator"` to `"latent_name"` with
no length-1 behaviour change. `generators`/`ks` are additionally minted
onto the `Transform` and `LatentDimension` nodes (additive attrs).

**Seed rung ORDER is untouched:** `sd_infer_dimension` /
`sd_recognize_dim` guards, `dim_checked` / `transform_explained` flags, and
the rung-1<rung-2<mint ladder are unchanged; composition lives entirely
INSIDE `DimInfer`'s own search, invisible to the ladder.

## 5. Fixtures (asymmetric; the exact sequence & ks are meaningful)

Tromino base = `{(0,0),(0,1),(1,0)}` (all red), `dim_types =
["pred","coord:r","coord:c","val"]`.

- **rotate∘scale** — goal `{(0,0),(0,2),(2,2)}` (rotate90 k=1 → scale2
  k=1). NO length-1 explains it (scale2-alone spreads to
  `{(0,0),(0,2),(2,0)}`; rotation/reflection preserve extent 1). Reports
  `length=2`, `generators=("rotation90","scale2")`, `ks=(1,1)`, residual 0.
- **reflect∘scale** — goal `{(0,0),(2,0),(2,2)}` (reflection_r k=1 →
  scale2 k=1). Distinct from the rotate∘scale image, so the pair is
  discriminating. Reports `generators=("reflection_r","scale2")`,
  `ks=(1,1)`.
- **ALIAS-NULL** — pure ×2 tromino `{(0,0),(0,2),(2,0)}` stays
  `length=1`, `generator="scale2"`, `k=1` (Occam: length-1 wins). Proves no
  spurious 2-step.
- **Termination** — a composite mints EXACTLY ONE Transform + ONE
  LatentDimension; an epoch bump re-arms (`sd_redecode`) but the
  `has_transform` guard blocks a second mint.

## STEP 2 decision

IMPLEMENT. All four IMPLEMENT-branch conditions hold: bounded (≤2),
Occam-ordered (length strict-primary), `build_candidate` reused unchanged
(count contract intact), additive result-Dict fields + additive seed
reads, seed rung order unchanged. No STOP condition is met.

## Residuals / honest notes

- The scale×isometry irreducible pairs commute on the origin-normalised
  lattice, so the "both orders" machinery is exercised but not
  order-DISCRIMINATING for those two headline fixtures; the tie-break makes
  the report deterministic (lexicographic-first generator names). The
  genuinely order-sensitive pair (`modular`×`scale2`) is supported by the
  same code path but is not gated here (a clean asymmetric integer fixture
  for it is fiddly; deferred, not blocked).
- Length is capped at 2; length-3+ is a straightforward `Vec`-length
  generalisation but is not demonstrated behind a gate and stays out of
  scope.
- `checked` grows by the length-2 attempt count when ≥2 distinct
  generators are present; single-generator cargo tests are unaffected (zero
  length-2 attempts by the distinct-generator rule).
