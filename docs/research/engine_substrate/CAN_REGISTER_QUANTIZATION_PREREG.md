# A register/style codebook, quantized per relationship band — PREREG

**Status: PREREG. Written before any `run_rules()` call in this rung
executes, and before `seeds/can_register_quantization.json` is regenerated
from its authoring script.** Per this project's standing discipline against
post-hoc rationalization (`BIGVILLE_CAN_INTEGRATION_PREREG.md`,
`CAN_BELIEF_QUANTIZATION_PREREG.md`, same convention, same rigor target):
what follows is the design, the grounding, and the falsifiable predictions,
written before the live demonstration is run.

## 0. Charter

> Build a NEW ocelot-side rung: a personality-trait-quantized
> REGISTER/STYLE codebook, applied per discrete relationship band — the
> mechanism `BIGVILLE_GOSSIP_DRIVE_SCOPING.md` + `BIGVILLE_TOPIC_AND_STYLE_
> SCOPING.md`'s whole research thread has been building toward, explicitly
> named as OCELOT's own job (not Bigville's) in the latter's own Part 3.4 —
> Bigville's backend-boundary design deliberately does not bundle cognition;
> a real Ocelot-side mechanism is meant to plug in from outside.

Explicitly NOT a cross-repo wiring task — an ocelot-only, prereg-then-build
rung, following `BIGVILLE_CAN_INTEGRATION_PREREG.md`'s own precedent: "a
WIRING/DEMONSTRATION rung, not a full-simulation rung."

## 1. What is already real, verified by direct read before building (not
taken on report)

1. **CAN's continuous mean-field mechanism is superseded.**
   `docs/research/engine_substrate/CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`
   §7 ("FINAL VERDICT — (b), replace") — confirmed by direct read of the
   full document in this pass — landed as `seeds/can_native_
   reimplementation.json` (`depends_on: ["causal_attitude_networks",
   "shape_decode_loop"]`, confirmed by direct read of the seed file: rules
   `can_native_update_3state`/`_2state`, `can_native_basin_decode`,
   `can_native_note_coactivation`, `can_native_hebbian_mint`/`_reweight`).
   No continuous relaxation, no Boltzmann ensemble, no iterative mean-field
   fixed point anywhere in the current mechanism. This rung is built on
   THIS current form, not the deprecated `can_ops.rs` raw-PyO3-call pattern
   `BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md` used (that rung's own
   `worlds/bigville_can_beliefs.py`/`seeds/bigville_can_beliefs.json` were
   confirmed DELETED by the "Extract Bigville implementation from Ocelot"
   commit `5065fb8`, per `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md` §1.9's own
   direct-read finding, re-confirmed here: `find` across both repos locates
   no `bigville_can_beliefs.*` anywhere in ocelot today).
2. **`resolution_bins` is a general, already-reused, per-resident cognitive-
   resolution trait — not belief-specific.** Confirmed by direct read of
   `BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md` (the rung that introduced
   it) and by grep confirming later, independent reuse across
   `CAN_SOLVER_TRACTABILITY_PREREG/RESULTS.md`, `CAN_LOOPY_BP_RESULTS.md`,
   `CAN_CONSUMER_MIGRATION_RESULTS.md`, `ENTITY_RESOLUTION_PREREG/
   RESULTS.md`. Drawn once per resident from a two-component Normal mixture
   in continuous space (floor `Normal(3.0,1.0)`, ceiling `Normal(7.5,2.0)`,
   `P(ceiling)=0.35`), rounded and clamped to `[2,12]` — the exact formula
   is `_draw_resolution_bins` (`/home/matt/ozmadev/bigville/worlds/
   bigville_town100_world.py:142-151`, confirmed by direct read this
   session — this file now lives ONLY in the sibling bigville repo,
   post-extraction; it does not exist anywhere in ocelot). It composes with
   the arousal-driven `resolution_level` STATE (`bigville_motivation.
   json`'s `mv_arousal`, Yerkes-Dodson shape) as `effective_bins = max(2,
   round(resolution_bins * resolution_level))`. **This rung reuses
   `resolution_bins` and the `effective_bins` composition formula
   verbatim** — see §3 for why reuse is correct here and §3's honest note
   on the one piece (`resolution_level`) that cannot be reused verbatim
   because its source seed does not exist in this repo.
3. **`seeds/interlocutor_shapes.json`'s `InterlocutorShape` codebook has a
   `sig_register` dimension with values `"formal"`, `"casual"`, `"neutral"`,
   `"__none__"`.** Confirmed by direct read of the seed file (5 nodes) AND
   its sole consumer, `domains/interlocutor_model.py::decode_shape`
   (`:459-496`): `sig_register` is one of four `_SHAPE_DIMS`
   (`register`/`cadence`/`style`/`affect`) matched against a party's
   ACCUMULATED dominant `feat_counts` (a plurality vote over observed
   turns) to classify what KIND of interlocutor this party appears to be —
   a static theory-of-mind/reliability-prior classification, re-run fresh
   on every call from whatever `feat_counts` currently holds, not a value
   that itself grows/converges per-dyad over time. **Confirmed: this is
   NOT the mechanism this rung builds** — it answers "what shape of
   interlocutor is this," this rung answers "what register does THIS
   resident converge toward WITH a given relationship band, as that band's
   accumulated closeness grows." This rung reuses ONLY
   `interlocutor_shapes.json`'s three non-abstaining register LABEL
   strings (`formal`/`casual`/`neutral`) as its own codebook's label
   vocabulary — not its nodes, not its rules, not its `sig_register`
   matching mechanism. `interlocutor_shapes.json` is read-only input here;
   nothing in it is modified.
4. **The "quantised set of interlocutors" is Bigville's own `band_code`.**
   Confirmed by direct read of `/home/matt/ozmadev/bigville/worlds/
   bigville_bond_world.py:137-147` (`BigvilleBondWorld._band_code`,
   sibling repo, read-only — this rung does not touch that repo). The REAL
   range is **`{-1, 0, 1, 2, 3, 4, 5}`** — seven codes, not six: `-1`
   ("rival") is a SEPARATE branch gated on `affect_resentment >= 2.0`, a
   qualitatively different (hostile) case, not a rung of the tie-strength
   ladder; `0`–`5` (`stranger` → `family`) IS the tie-strength ladder,
   `band_code = f(tie_strength)`, monotonically banding accumulated
   closeness. **Scoping decision, registered**: this rung's codebook
   covers `band_code ∈ {0,...,5}` (the six-band tie-strength ladder,
   matching the task's own "0-5" framing and the literature this rung
   grounds against, all of which concerns closeness/accommodation, not
   hostility) and explicitly EXCLUDES `-1` (rival) as out of scope — CAT
   (Giles/Bell) predicts DIVERGENCE under distinctiveness/hostility motives,
   a genuinely different mechanism from the convergence this rung builds,
   already named as an open, unmodeled direction in
   `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md`'s own Open Question 5. Per the
   task's own instruction, this rung uses SYNTHETIC band values (not live
   Bigville `tie_strength`/`band_code` data) — no cross-repo call is made
   anywhere in this rung.
5. **The empirical shape to match: Brinberg & Ram (2021)**, already
   verified and cited in `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md` §2.5 — real
   couples' linguistic convergence (syntactic/semantic/vocabulary
   alignment) follows a SATURATING (exponential-approach-to-asymptote)
   curve as accumulated interaction grows, not a linear one. This rung's
   "true" continuous register-affinity value is a saturating function of
   accumulated closeness (proxied by `band_code`, since Bigville's own real
   `_band_code` is itself computed FROM accumulated `tie_strength` — using
   the band as the evidence axis is therefore a real, not invented,
   grounding link, not merely a convenient stand-in).
6. **Zero new Rust Terms are needed — checked directly against
   `runners/dsl/src/term.rs`, not assumed.** Every Term this design uses
   already exists and is already used in a landed seed: `Plus`/`Minus`/
   `Times`/`Div` (`can_native_reimplementation.json`), `Round`
   (`term.rs:169`, banker's rounding, `round_half_even_digits`), `Max`
   (`term.rs:674`, used in `bigville_motivation.json`), `Abs`
   (`term.rs:656`), `IfThenElse`/`Gt`/`Gte`/`Eq`/`Not`/`And`
   (`can_native_reimplementation.json`), `Let` (`term.rs:1858`, confirmed
   live in `seeds/embodied_adaptation.json` — name-bound sub-expression
   reuse inside one Term, used here to avoid re-deriving `effective_bins`
   three times inside one expression the way `can_native_update_3state`
   duplicates its own giant `IfThenElse` chain), `Argmin`
   (`term.rs:543`, `source`/`var_name`/`value`/optional `default` —
   confirmed live in `seeds/gap_awareness.json`'s `retire_duplicate_gap`
   rule, an ALREADY-ESTABLISHED engine-native nearest/selection-decision
   primitive, not a new pattern invented for this rung), `NodesOfType`
   (`gap_awareness.json`), `Attr`/`Var`/`Lit` (universal).

## 2. Design decision, registered: `Argmin`-over-anchors, not `ShapeDecode`
— why this is the right-sized primitive, not a deviation from house style

The task names `ShapeDecode`/`sd_recognize` as the current native pattern
(per `can_native_basin_decode`'s own precedent) and explicitly invites
either "the quantized level nearest a small number of anchor points" or "a
banding of the quantized range into label buckets" as valid label-mapping
designs. This rung chooses **nearest-anchor-point via `Argmin`**, and states
precisely why `ShapeDecode` is the WRONG-sized tool here rather than simply
defaulting to it because it is the more recently-landed pattern:

`ShapeDecode`/`sd_recognize` (`can_native_basin_decode`'s own use) answers
"does this multi-relation configuration (a `ShapeSignature` — a SET of
`[predicate, subject, object]` relation tuples) match a held multi-relation
codebook entry," via beam search over compositional coverage. The register
decode here is a fundamentally smaller-shaped problem: ONE scalar value on
`[-1,1]` classified against THREE fixed reference points on the same line —
a nearest-point lookup, not a relational-coverage matching problem. Forcing
this through `ShapeDecode`'s beam-search/residual-coverage machinery would
be using a hammer built for structural composition on a problem with no
structure to compose — a real, if smaller, instance of exactly the "shape
matcher, not a number matcher, but also not every number problem is a
relational-coverage problem" discipline `CLAUDE.md`'s own SHAPES-NOT-NUMBERS
section asks to apply precisely rather than by rote. `Argmin` over a small
held codebook (`RegisterLabelAnchor` nodes) IS the shape-decode-flavored
primitive correctly sized for "classify a value against a small number of
held reference points" — already established as exactly that in this same
codebase (`gap_awareness.json`'s survivor-selection use), independent of
`shape_decode_loop.json`. **Registered explicitly**: this rung's seed
`depends_on` `can_native_reimplementation` (the conceptual sibling — same
`resolution_bins`/`effective_bins` family, same "replace the continuous
mechanism with a native discrete one" lineage) and `interlocutor_shapes`
(read-only label-vocabulary reuse), but deliberately does NOT
`depends_on shape_decode_loop` — it does not call `ShapeDecode`, and
`Argmin` has independent precedent (`gap_awareness.json`) that does not
carry that dependency either. This is a considered omission, not an
oversight.

## 3. The trait — reuse `resolution_bins` verbatim; the honest limit on
reusing `resolution_level`

**Reuse, not redesign**: this rung draws `resolution_bins` from the
IDENTICAL mixture `_draw_resolution_bins` uses (floor `Normal(3.0,1.0)`,
ceiling `Normal(7.5,2.0)`, `P(ceiling)=0.35`, clamp `[2,12]`) — the same
constants, same shape, same clamp, ported into this rung's own harness
because the source file lives only in the sibling bigville repo and cannot
be imported cross-repo. This is REUSE of the formula, not a redraw with new
constants.

Per the task's own reasoning (CLAUDE.md's SHAPES-NOT-NUMBERS: "the burden
of proof is reuse"), inventing a separate `register_bins` trait would be
exactly the "each ad hoc rate eventually needs its own rate" regression
that section warns against, when a general per-resident cognitive-
resolution trait already exists and already generalizes across CAN
belief-quantization, solver tractability, loopy-BP, consumer migration, and
entity resolution. **`resolution_bins` fits register quantization for the
same reason it fits all five of those**: none of them is "resolution
FOR belief" specifically — every one of them is "how finely does this
resident's cognition discriminate a continuous quantity," and register
affinity is exactly one more continuous quantity a resident discriminates
more or less finely depending on the same trait.

**Honest limitation, registered before measuring**: `effective_bins =
max(2, round(resolution_bins * resolution_level))` is reused as a
COMPOSITION FORMULA, but `resolution_level` itself — `bigville_motivation.
json`'s `mv_arousal`-driven state — has **no equivalent seed in ocelot**
(confirmed by direct `find`: `bigville_motivation.json` exists ONLY in the
sibling bigville repo, both at its top level and under its own nested
`bigville/seeds/` — zero matches anywhere under `/home/matt/ozmadev/ocelot`).
This rung therefore cannot wire a live arousal-driven `resolution_level`
the way `BIGVILLE_CAN_INTEGRATION_RESULTS.md` did (that rung had the SAME
honest limitation, registered in its own §4: computed once at demo-setup
time, not as a live rule). This rung goes one step further and simplifies
even more conservatively: **`resolution_level` is a fixed, documented DEMO
INPUT** (`1.0` for the primary demonstration, isolating `resolution_bins`
as the sole manipulated variable with zero confound from a second varying
state — more conservative than the precedent rung, which had comparable
but not identical arousal, `0.28` vs `0.26`), stored as a plain attr on
each synthetic resident node, with one small supplementary check (§6.3)
varying it on a single resident to confirm the composition still behaves
sensibly. Wiring a live `resolution_level` requires the (not-built-in-
ocelot) motivation seed and is out of scope here, exactly as declared.

## 4. The mechanism — what is quantized, and how

### 4.1 The "true" continuous value

A saturating function of `band_code` (the accumulated-closeness proxy, per
§1 point 5's grounding — `band_code` IS itself computed from accumulated
`tie_strength` in the real Bigville mechanism, so using it as the evidence
axis is a real link, not an invented one):

```
true_affinity(band_code) = 2 * (1 - exp(-k * band_code / 5)) - 1,   k = 3.0
```

`band_code ∈ {0,...,5}` (§1 point 4's scoping). Range `[-1, +1]`, matching
the ORIGINAL CAN rung's own convention for quantized edge weights (§1
point 5's own instruction, `CAN_BELIEF_QUANTIZATION_PREREG.md §2.2`/
`BIGVILLE_CAN_INTEGRATION_PREREG.md §5`'s identical `[-1,1]` choice). `-1`
= maximally formal/distant (CAT's default toward strangers); `+1` =
maximally casual/converged (CAT's convergence outcome under sustained
closeness). `k = 3.0` is a documented DEMO CHOICE (same honesty class as
`BIGVILLE_CAN_INTEGRATION_PREREG.md §4`'s `res_gain = 1.0` — not fitted,
not swept, chosen once before any resident is drawn) that places the curve
genuinely saturating within the tested band range: `true_affinity(0) =
-1.0` exactly (a stranger defaults to maximal formality — a real, not
arbitrary, consequence of the `exp(0)=1` boundary, not a separate special
case), `true_affinity(5) ≈ 0.900` (near, not at, the asymptote — the point
of a saturating curve, not a linear ramp that would hit the endpoint on
schedule). This is held as **structural, literature-grounded DATA** — six
`BandAffinityAnchor` codebook entries, one per `band_code`, computed once
by this rung's own authoring script and baked into the seed's static
`nodes` array, the SAME status as `BIGVILLE_CAN_INTEGRATION_PREREG.md §2`'s
five hand-authored structural `causal_influence` edges (a fixed relational
template, not a live per-tick decision) — not a live rule computing `Exp`
per tick. **Per this project's own frame/continuum invariant
(`CLAUDE.md`'s BASE-AS-DIMENSION section): this keeps the one genuinely
transcendental piece of the design (`Exp`, a real number) confined to a
ONE-TIME cross-frame authoring computation, never evaluated inside the live
`run_rules()` fixpoint** — a stricter reading of the invariant than
`BIGVILLE_CAN_INTEGRATION_PREREG.md`'s own `quantize_j`, which computed its
(non-transcendental, linear) quantization in live Python per resident; this
rung's live per-resident computation (§4.2) is pure rational arithmetic
(`Plus`/`Minus`/`Times`/`Div`/`Round`/`Max`), zero transcendental functions,
entirely inside `run_rules()`.

**Identical-evidence isolation, registered**: the SAME six
`BandAffinityAnchor` values are used for every synthetic resident compared
in this rung — "given IDENTICAL underlying band-interaction-history input,"
per the task's own falsifiable-prediction framing — so any measured
difference in outcome across compared residents is attributable to
`resolution_bins` alone, not to different "true" evidence.

### 4.2 Quantization — `effective_bins` levels on `[-1,1]`, computed as a
graph Rule

For a resident with a given `resolution_bins`/`resolution_level` and a
`band_code`'s `true_affinity`:

```
effective_bins = max(2, round(resolution_bins * resolution_level))
level_index    = round( (true_affinity + 1) / 2 * (effective_bins - 1) )
quantized_value = -1 + level_index * 2 / (effective_bins - 1)
```

This generalizes `BIGVILLE_CAN_INTEGRATION_PREREG.md §5`'s
`linspace(-1,1,effective_bins)`-nearest-level quantization
(`quantize_j`) — same shape, same vocabulary-size semantics — but
**expressed as a Rule's `effects` (`Round`/`Times`/`Div`/`Plus`/`Minus`/
`Max`/`Gte`/`IfThenElse`/`Let` Terms), not Python**, per this task's own
constraint (register decisions must be the engine's). This is, checked
against every prior rung in this arc, the FIRST time this exact
"nearest-level-on-a-variable-size-linspace" quantization is expressed as
graph-native Term arithmetic rather than a Python helper (`quantize_j` in
the now-deleted `bigville_can_beliefs.py` was plain Python) — a genuine,
if small, architectural improvement this rung contributes independent of
its own measured result, worth reporting honestly either way.

`effective_bins - 1` is guaranteed `>= 1` (the `Max(2, ...)` floor), so no
division-by-zero case exists in this design.

### 4.3 The register-label decision — `Argmin` over a 3-entry codebook

```
RegisterLabelAnchor{label:"formal",  canonical_value:-1.0}
RegisterLabelAnchor{label:"neutral", canonical_value: 0.0}
RegisterLabelAnchor{label:"casual",  canonical_value: 1.0}
```

(three global nodes, baked into the seed, no `productions` needed — the
SAME zero-production precedent `interlocutor_shapes.json`'s own
`InterlocutorShape` codebook already uses for free-floating reference
nodes; label strings reused from that seed's own `sig_register`
vocabulary, per §1 point 3).

```
register_label = Attr(
  Argmin(source: NodesOfType("RegisterLabelAnchor"), var_name: lbl,
         value: Abs(quantized_value - Attr(lbl, "canonical_value"))),
  key: "label")
```

The winning anchor is the nearest of the three canonical points to this
resident-band's `quantized_value`; ties are impossible by construction for
an odd-count `effective_bins` grid landing exactly at `0.0`, and
`Argmin`'s own documented tiebreak (first-encountered-in-iteration-order,
per `term.rs:535-541`) applies in the rare exact-tie case, matching this
codebase's own existing tolerance for that tiebreak elsewhere (e.g.
`gap_awareness.json`'s own use).

### 4.4 What is stored, in-frame vs. between-frames — checked against the
invariant explicitly, not assumed

- **In-frame (integer or discrete)**: `effective_bins` (integer),
  `register_level_index` (integer), `register_label` (discrete string,
  the classification outcome).
- **Between-frames (a rendering, legitimately a float — matching
  `can_native_update_3state`'s own `external_field`/`identity_field`/
  `temperature` precedent of continuous MODULATING inputs alongside a
  discrete decided STATE)**: `quantized_value` (the `linspace` render of
  `register_level_index` — stored as a convenience/audit attr, the SAME
  status as `can_native_basin_decode`'s own stored `residual`/
  `covered_count`, both renders of a decode, not raw frame coordinates),
  `true_affinity` (the one-time authored render, §4.1), `resolution_level`
  (a continuous demo input, §3).

## 5. Graph shape

```
RegisterProfile{name, resolution_bins, resolution_level}
  -observed_band-> RegisterObservation{band_code, true_affinity, status:"pending"}
```

One new Γ production (`RegisterProfile -observed_band-> RegisterObservation`).
`RegisterObservation` carries `band_code`/`true_affinity` copied onto it
by the harness at creation time from the (static, seed-authored)
`BandAffinityAnchor` template for that `band_code` — mechanical world-
adapter translation, the SAME class of operation `can_native_basin_decode`'s
own `Observation` nodes already use (caller sets `signature`/`scope_name`
before the rule fires). ONE rule, `can_register_decode_band`, fires per
pending `RegisterObservation`, writing `effective_bins`/
`register_level_index`/`quantized_value`/`register_label`/`status:"decoded"`.

## 6. Live demonstration — design, registered before running

### 6.1 Population

`N = 100` synthetic `RegisterProfile` residents, `resolution_bins` drawn
from the §3 mixture (fixed-seed RNG for reproducibility), `resolution_level
= 1.0` for all (§3's registered isolation choice). Mechanical,
non-cherry-picked selection, mirroring `BIGVILLE_CAN_INTEGRATION_RESULTS.md
§5` exactly: the LOWEST-`resolution_bins` and HIGHEST-`resolution_bins`
residents, tie-broken by index.

### 6.2 Primary comparison

Both selected residents get a `RegisterObservation` for EVERY `band_code
∈ {0,...,5}`, decoded against the IDENTICAL `BandAffinityAnchor` template
(§4.1's isolation). Read back `effective_bins`, `quantized_value`,
`register_label` per band for each resident.

**Predictions, registered before running:**

1. **Manipulation check** (near-definitional, reported as such, not as a
   finding, per `BIGVILLE_CAN_INTEGRATION_RESULTS.md`'s own precedent for
   its own rounding-error check): mean `|true_affinity − quantized_value|`
   across the 6 bands is markedly higher for the coarse
   (`resolution_bins=2`, the population floor) resident than the fine one.
2. **A structurally-certain corollary, registered as certain, not as a
   discovery**: with `effective_bins = 2` (`resolution_bins=2 ×
   resolution_level=1.0`), the achievable `quantized_value` vocabulary is
   EXACTLY `{-1, +1}` — the nearest-anchor decode (§4.3) can therefore
   NEVER select `"neutral"` for this resident, for any `band_code`,
   regardless of `true_affinity`'s actual value. This is reported honestly
   as a guaranteed consequence of the design (like the prior rung's
   rounding-error check), not measured as an open question.
3. **The primary, genuinely non-guaranteed prediction**: the FINE resident
   (`resolution_bins` at or near the population ceiling) will exhibit a
   **strictly greater number of distinct `register_label` values across
   the 6 bands** than the coarse resident — i.e., the fine resident's
   register genuinely discriminates relationship closeness (using 2 or 3
   of the 3 available labels as `band_code` varies), while the coarse
   resident's register collapses to at most 2 labels regardless of how
   many genuinely different `true_affinity` values the 6 bands actually
   carry. This is the substantive claim (mirroring
   `BIGVILLE_CAN_INTEGRATION_RESULTS.md`'s own primary frustration/energy
   prediction): **lower metacognitive/representational resolution
   mechanically produces less discriminated social behaviour, on
   IDENTICAL relationship evidence** — the register-domain instance of
   this project's own standing "quantisation of causal linkage" framing
   (`CAN_BELIEF_QUANTIZATION_PREREG.md §0`), now applied to style instead
   of belief.
4. **Honest null, registered as fully acceptable**: if both residents
   land on the same distinct-label count (e.g. both hit exactly 2, or the
   `BandAffinityAnchor` curve's own shape happens to place every band on
   the same side of the neutral boundary regardless of grid fineness),
   that is reported as a clean, informative null — this rung's 6-band,
   3-label space is much smaller than the prior CAN rung's `N=5`-network
   frustration measurement, and a null here would be informative about a
   ceiling/floor effect (only 3 labels exist; a curve that never crosses
   near zero cannot show a 3-way split regardless of resolution), not
   silently reinterpreted as confirmation.

### 6.3 Supplementary checks (exploratory, not pre-registered with the
primary comparison's rigor — mirroring `BIGVILLE_CAN_INTEGRATION_RESULTS.md
§5.1`'s own labeling of its population sweep)

- **Population-wide correlation**: across all `N=100` residents (
  `resolution_level=1.0` fixed), `corr(effective_bins, mean quantization
  error)` (expected strongly negative, near-definitional) and
  `corr(effective_bins, distinct_label_count)` (expected positive — the
  less-guaranteed population-level version of prediction 3, ceiling-capped
  at 3).
- **`resolution_level` sanity check**: on ONE resident (fixed
  `resolution_bins`), sweep `resolution_level ∈ {0.3, 0.6, 1.0}` and
  confirm `effective_bins`/label-discrimination respond monotonically —
  confirming the reused composition formula still behaves sensibly even
  though it is not live-wired to a real arousal state in this repo (§3).

## 7. What this rung explicitly does NOT do

No live simulation-tick integration (no `resolution_level` recomputed from
a real arousal rule — that seed does not exist in ocelot). No cross-repo
call to Bigville (`band_code`/`tie_strength` are synthetic here, matching
the task's explicit instruction). No coupling between residents (each
`RegisterProfile`'s `RegisterObservation`s are independent — no
resident-to-resident register influence/contagion modeled). No `-1`
(rival/hostile) band — explicitly scoped out (§1 point 4). No divergence
mechanism (CAT's own documented second prediction, already named as an
open question elsewhere in this research line). No new Rust Term or
`can_ops.rs`/`shape_decode.rs` change — §1 point 6 confirms the existing
Term vocabulary suffices; if this is found false during the build, the
task's own instruction is to STOP and report rather than build unilaterally.

## 8. Regression scope

Before: `python3 -m pytest tests/test_can_native_reimplementation.py
tests/test_can_belief_quantization.py tests/test_can_ops.py -q` (no
`-n auto`, per the task's own instruction).
After: the same three files, plus the new `tests/
test_can_register_quantization.py`.

## 9. Files this rung will create

- `scripts/_build_can_register_quantization_seed.py` (authoring script,
  emits the seed — mirrors `scripts/_build_can_decay_identity_seed.py`'s
  exact convention).
- `seeds/can_register_quantization.json` (generated output).
- `scripts/can_register_quantization_demo.py` (live demonstration
  harness).
- `tests/test_can_register_quantization.py` (regression).
- `docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_RESULTS.md`
  (this rung's own results, written after running, not before).

No already-landed seed/rule file is edited. No Bigville repo file is
touched.
