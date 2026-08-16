# A register/style codebook, quantized per relationship band — RESULTS

Prereg: `CAN_REGISTER_QUANTIZATION_PREREG.md`, same repo, written and
locked before any `run_rules()` call in this rung executed. Not edited
after measurement began.

**Verdict, up front:** both registered predictions confirmed, on a real
live comparison AND a population-wide supplementary check, on the first
run of the mechanism against the real engine — no design iteration was
needed after the prereg was locked. The manipulation check (prediction 1)
is clean and large: the coarse resident's mean quantization error is
**11.80× the fine resident's** (0.3527 vs 0.0299). The structural
certainty (prediction 2) holds exactly as derived: the `effective_bins=2`
resident never selects `"neutral"`, on any of the 6 bands. The primary,
non-guaranteed prediction (prediction 3) is confirmed: the fine resident
discriminates **3 distinct register labels** across the 6 relationship
bands where the coarse resident discriminates only **2**, on IDENTICAL
band-interaction-history input — a real, measured, register-domain
instance of this project's own standing "quantisation of causal linkage"
finding, now shown to generalize from belief content to speech register.

---

## 1. What was built

1. **`scripts/_build_can_register_quantization_seed.py`** — authoring
   script (mirrors `scripts/_build_can_decay_identity_seed.py`'s exact
   convention: Term-tree builder functions, `print(json.dumps(...))`).
   Computes 6 `BandAffinityAnchor` values (`band_code` 0–5) via the
   PREREG's cited saturating formula (`k=3.0`) as a ONE-TIME authoring
   computation (the only place `math.exp` appears anywhere in this rung),
   and emits the single Rule `can_register_decode_band` as pure Term
   arithmetic.
2. **`seeds/can_register_quantization.json`** — generated output.
   `depends_on: ["can_native_reimplementation", "interlocutor_shapes"]`
   (deliberately NOT `shape_decode_loop` — PREREG §2's registered `Argmin`-
   over-`ShapeDecode` justification). 9 static nodes (6
   `BandAffinityAnchor` + 3 `RegisterLabelAnchor`), 1 Γ production
   (`RegisterProfile -observed_band-> RegisterObservation`), 1 rule.
3. **`scripts/can_register_quantization_demo.py`** — the live
   demonstration harness (mirrors `scripts/bigville_can_integration_demo.py`'s
   role): mechanical population draw + graph construction + `run_rules()`
   + read-back. Zero register decisions in Python — confirmed by
   `test_no_python_decision_source_audit` (§5).
4. **`tests/test_can_register_quantization.py`** — 16 new tests.

**No new Rust.** Every Term used (`Plus`/`Minus`/`Times`/`Div`/`Round`/
`Max`/`Abs`/`Gte`/`IfThenElse`/`Let`/`Argmin`/`NodesOfType`/`Attr`/`Var`/
`Lit`/`Eq`/`Not`/`And`) was already present in `runners/dsl/src/term.rs`
and already exercised by a landed seed before this rung began (§1 of the
PREREG lists the exact prior site for each). Confirmed empirically, not
just by source-read: the seed loaded with **zero** "malformed rule"/
"skipping" warnings on the first successful load (`test_seed_loads_with_
no_malformed_rule_warning`) — the ONE load attempt that DID warn (during
build, before a bug fix, §6) is reported honestly below rather than
silently corrected out of the record.

## 2. Design decisions, as registered and as built

1. **`resolution_bins` reused verbatim** — same mixture, same constants
   (floor `Normal(3.0,1.0)`, ceiling `Normal(7.5,2.0)`, `P(ceiling)=0.35`,
   clamp `[2,12]`), ported into `can_register_quantization_demo.py`
   because `bigville_town100_world.py` (the source) now lives only in the
   sibling bigville repo and cannot be imported cross-repo. **Confirmed
   correct to reuse, not redesign**: `resolution_bins` is "how finely does
   this resident's cognition discriminate a continuous quantity" —
   register affinity is exactly one more instance of that same shape, not
   a different trait. No `register_bins` was invented.
2. **`effective_bins = max(2, round(resolution_bins * resolution_level))`
   reused verbatim** as the composition formula. `resolution_level` itself
   has **no ocelot-side source** (`bigville_motivation.json` — the
   arousal-driven state that would compute it live — exists ONLY in the
   sibling bigville repo; confirmed absent from ocelot by direct `find`
   before this rung began). Held as a fixed, documented demo input
   (`1.0` for the primary comparison, isolating `resolution_bins` as the
   sole manipulated variable) — an honest limitation, registered before
   measuring, one step more conservative than
   `BIGVILLE_CAN_INTEGRATION_RESULTS.md`'s own precedent (which had
   comparable-but-unequal live arousal, `0.28` vs `0.26`, for its two demo
   residents).
3. **The label map is `Argmin` over a 3-entry codebook, not literal
   `ShapeDecode`.** Registered and built exactly as designed (PREREG §2):
   a scalar nearest-point classification against 3 fixed reference points
   has no relational structure for `ShapeDecode`'s beam-search/residual-
   coverage machinery to compose, so `Argmin` (already an established
   engine-native selection primitive — `gap_awareness.json`'s
   `retire_duplicate_gap`) is the right-sized tool. This held up in the
   build: the rule needed no `ShapeSignature` codebook, no `codebook_scope`,
   no beam-search parameters — the entire decision is one `Argmin` call
   over `NodesOfType("RegisterLabelAnchor")`.
4. **Zero transcendental math inside `run_rules()`.** The one genuinely
   real-valued piece of this design (`Exp`, the saturating curve) is
   confined to a one-time authoring computation baked into the seed's
   static `nodes` array — never evaluated live. Every live per-tick
   computation (`effective_bins`, `register_level_index`,
   `quantized_value`, `register_label`) is rational-arithmetic Term
   composition (`Round`/`Times`/`Div`/`Plus`/`Minus`/`Max`/`IfThenElse`),
   a stricter reading of the frame/continuum invariant than
   `BIGVILLE_CAN_INTEGRATION_PREREG.md`'s own `quantize_j`, which computed
   its (non-transcendental) quantization in live Python. This is a real,
   if small, architectural improvement this rung contributes independent
   of its measured result: **this is the first rung in this arc to
   express "nearest-level-on-a-variable-size-linspace" quantization as
   graph-native Term arithmetic rather than a Python helper.**

## 3. Live two-resident demonstration — real measured numbers

Mechanical, non-cherry-picked selection (fixed-seed `np.random.default_rng
(20260816)`, `N=100` synthetic residents): lowest/highest `resolution_bins`
in the population, tie-broken by index — mirrors
`BIGVILLE_CAN_INTEGRATION_RESULTS.md §5`'s selection rule exactly.

| | **resident_004** (coarse, idx 4) | **resident_025** (fine, idx 25) |
|---|---|---|
| `resolution_bins` | **2** | **12** |
| `resolution_level` | 1.0 (fixed, isolating the trait) | 1.0 |
| `effective_bins` | **2** | **12** |

Per-band decode (identical `BandAffinityAnchor` template for both — the
same `true_affinity` per band, so any difference is attributable to
`resolution_bins` alone):

| band | true_affinity | coarse: qv | coarse: label | fine: qv | fine: label |
|---|---|---|---|---|---|
| 0 stranger | -1.0000 | -1.0000 | formal | -1.0000 | formal |
| 1 consequential_stranger | -0.0976 | -1.0000 | formal | -0.0909 | **neutral** |
| 2 acquaintance | 0.3976 | 1.0000 | casual | 0.4545 | **neutral** |
| 3 friend | 0.6694 | 1.0000 | casual | 0.6364 | casual |
| 4 intimate | 0.8186 | 1.0000 | casual | 0.8182 | casual |
| 5 family | 0.9004 | 1.0000 | casual | 0.8182 | casual |

**Predictions, scored:**

1. **Manipulation check (mean `|true − quantized|`)**: coarse **0.3527**,
   fine **0.0299** — **11.80×**. **CONFIRMED**, large, near-definitional
   as registered.
2. **Structural certainty**: coarse resident's label set is exactly
   `{formal, casual}` — `"neutral"` never appears, across all 6 bands.
   **CONFIRMED**, exactly as derived (the `effective_bins=2` grid is
   literally `{-1,+1}`, so no quantized value can land near `0`).
3. **Primary prediction**: fine resident's distinct label count (**3**:
   `formal`, `neutral`, `casual`) is strictly greater than the coarse
   resident's (**2**). **CONFIRMED.** Mechanistically: bands 1
   (consequential_stranger, `true_affinity=-0.098`) and 2 (acquaintance,
   `true_affinity=0.398`) both sit close enough to the neutral midpoint
   that a fine-grained grid (12 levels) resolves them to genuinely
   different quantized values than the extremes — and one of them
   (band 1) lands close enough to decode as `"neutral"` — while the
   coarse 2-level grid can only ever round every band to one of the two
   extremes, forcing bands 1 and 2 to the SAME extreme label as bands 0
   and 3–5 respectively, despite genuinely different underlying
   affinities. This is the register-domain instance of
   `CAN_BELIEF_QUANTIZATION_PREREG.md §0`'s framing ("lower
   metacognition leads to lack of nuance — mechanically explained by the
   quantisation of causal linkage"), now measured for style/register
   instead of belief content.

No null was observed on the primary comparison — reported honestly: this
means the "honest null, registered as fully acceptable" branch (PREREG
§6.2 point 4) was not exercised on this particular resident pair. The
supplementary population-wide check below shows the effect is not an
artifact of this one pair.

## 4. Supplementary checks (exploratory, not pre-registered with the same
rigor as §3 — mirroring `BIGVILLE_CAN_INTEGRATION_RESULTS.md §5.1`'s own
labeling)

**Population-wide correlation, all 100 residents, `resolution_level=1.0`
fixed:**

- `corr(effective_bins, mean_abs_error)` = **−0.813** (strongly negative,
  expected, close to definitional — same status as the two-resident
  manipulation check).
- `corr(effective_bins, distinct_label_count)` = **+0.505** (moderate
  positive — the less-guaranteed, population-level version of prediction
  3; ceiling-capped at 3 since only 3 labels exist at all).
- `distinct_label_count` distribution: **`{2: 21, 3: 79}`** — 21/100
  residents (all at or near the population floor `resolution_bins≈2-3`)
  are stuck at 2 distinct labels; 79/100 reach the full 3-label
  discrimination. This lines up closely with the population's own
  `resolution_bins` distribution (`{2:21, 3:22, 4:26, 5:5, ...}` —
  21 residents drawn at the exact floor value 2), consistent with the
  mixture design's own predicted floor cluster
  (`BIGVILLE_CAN_INTEGRATION_RESULTS.md §3`'s real cast100 population
  showed the same floor-heavy shape, 66/100 in bins 2-4).

**`resolution_level` sanity sweep** (one resident, `resolution_bins=8`
fixed): `resolution_level ∈ {0.3, 0.6, 1.0}` → `effective_bins ∈ {2, 5,
8}` → `distinct_labels ∈ {2, 3, 3}`. Monotonic and sensible: the reused
composition formula behaves correctly even without a live arousal state
feeding it, confirming §2 point 2's honest limitation does not silently
break the mechanism — it just means `resolution_level` is a fixed input
rather than a ticking one in this rung.

## 5. Regression

Targeted run (no `-n auto`, per the task's own instruction):

```
python3 -m pytest tests/test_can_native_reimplementation.py \
  tests/test_can_belief_quantization.py tests/test_can_ops.py \
  tests/test_can_register_quantization.py -q
```

**Before** (this rung's files absent): `1 failed, 33 passed`.
**After** (this rung's files added): `1 failed, 49 passed`
(33 + 16 new, all new tests green).

The one failure, in BOTH runs, byte-identically:
`tests/test_can_native_reimplementation.py::
test_bigville_schema_symmetric_fix_makes_all_couplings_visible_to_native_rule`
— `ImportError: cannot import name 'bigville_can_beliefs' from 'worlds'`.
**Confirmed pre-existing and unrelated to this rung**: that module was
deleted by the "Extract Bigville implementation from Ocelot" commit
`5065fb8` (per `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md §1.9`'s own finding,
re-confirmed here by direct `find` across both repos — the file exists
nowhere in ocelot). This rung neither created nor could fix that failure
(it does not touch `worlds/bigville_can_beliefs.py` or that test file) —
named honestly as a pre-existing red, per this project's own "baseline
must be a list of node ids" discipline, not silently worked around.

`git status --porcelain` confirms only NEW, untracked files were added by
this rung (`seeds/can_register_quantization.json`,
`scripts/_build_can_register_quantization_seed.py`,
`scripts/can_register_quantization_demo.py`,
`tests/test_can_register_quantization.py`) — `seeds/can_native_
reimplementation.json` and `seeds/interlocutor_shapes.json` are byte-
unmodified, gated by `test_already_landed_seeds_are_untouched`.

## 6. A build-time correction, reported honestly (per this research line's
own standing discipline)

The first version of `_quantized_value_term`'s effect (before this
document's own numbers were measured) wrote a bare Python string
`"decoded"` through the `term_effect` helper (which wraps its argument in
`{"__term__": ...}`), producing `{"__term__": "decoded"}` — not a valid
Term object. `load_seed_manifest` correctly rejected this at load time
(`[seed] WARNING: skipping malformed rule 'can_register_decode_band': bad
computed effect arg: ShapeMismatch("expected JSON object for Term")`),
confirmed by direct observation during the build's first smoke test
before any measurement was taken. Fixed by using the (already-existing,
already-precedented) `lit_effect` helper for the one genuinely literal
effect (`status: "decoded"`) instead of `term_effect`. This was caught and
fixed BEFORE the prereg's predictions were run against the real engine —
the first live run reported in §3 is the FIRST successful run of the
corrected rule, not a re-run after silently patching a wrong result.

## 7. What this rung establishes, and what it does NOT

**Establishes**: a real, engine-native (zero-Python-decision, zero-new-
Rust) register/style quantization mechanism, reusing the SAME
`resolution_bins` trait and `effective_bins` composition formula CAN
belief quantization already established, applied to a NEW continuous
quantity (register affinity per relationship band) via a design decision
(`Argmin`-over-anchors rather than `ShapeDecode`) explicitly registered
and justified before building; a real, measured, non-guaranteed
prediction (distinct register-label discrimination scales with
representational resolution) confirmed both on a clean two-resident
comparison and a 100-resident population correlation; a small genuine
architectural improvement (the first graph-native, not Python,
expression of variable-size-linspace quantization in this arc).

**Does NOT establish**: anything about real Bigville residents or live
`tie_strength`/`band_code` data — every number in this document is from a
synthetic population and a synthetic band-affinity template, exactly as
scoped. Anything about the `-1` (rival/hostile) band or divergence
behavior (CAT's own second prediction) — explicitly out of scope.
Anything about live-tick dynamics — `resolution_level` is a fixed demo
input, not a ticking arousal state (no `bigville_motivation.json`
equivalent exists in ocelot). Anything about whether the specific `k=3.0`
saturation-rate constant is realistic — it is a documented, un-fitted demo
choice, the same honesty class as `res_gain=1.0` in the prior CAN rung.

## 8. Cross-repo follow-on work — named, not built

Per the task's explicit scope boundary, none of the following was built or
attempted in this rung:

1. **Wiring a live `RegisterProfile` from a real Bigville actor's real
   `resolution_bins`/`resolution_level`** — this rung's `RegisterProfile`
   nodes are synthetic, built by `can_register_quantization_demo.py`'s
   own population draw. A real integration would need an Ocelot-side
   adapter reading a live Bigville actor's cast100 `resolution_bins` and
   whatever computes its live `resolution_level` (today, nothing —
   `bigville_motivation.json` exists only in bigville and is not wired to
   ocelot's `_native.Substrate()` at all).
2. **The bigville-side plumbing this needs is ALSO not yet built** —
   confirmed by direct read of `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md`'s own
   "BUILD LANDED" section (2026-08-16): Part 3.4's own scoped plumbing
   (`band_code`/`tie_strength` exposed on `ActorContext.observations
   ["nearby_residents"]`) was explicitly named as deferred and NOT built
   when Rungs 1–2 of that scoping landed. A real end-to-end integration
   needs BOTH sides: bigville's `band_code` plumbing AND an ocelot-side
   backend (implementing bigville's `CognitionBackend` protocol) that
   calls this rung's `can_register_decode_band` rule per encounter and
   renders `register_label` into actual word-choice/phrasing.
3. **Feeding `-1` (rival) through a DIVERGENCE mechanism** (CAT's own
   second, un-modeled prediction) — a genuinely different mechanism from
   the convergence this rung builds, not merely an extra codebook entry.
4. **A per-dyad `RegisterProfile` that GROWS from repeated interaction
   over live ticks** (rather than a single per-resident trait applied
   fresh to a static band-affinity template) — this rung's
   `BandAffinityAnchor` template is a fixed, shared, structural constant;
   a fuller model in which the "true" affinity itself accumulates
   per-DYAD (not merely per-band) evidence over many real encounters is a
   real, sizeable, un-built next rung.
5. **Rendering `register_label` into actual generated phrasing** — this
   rung stops at a discrete LABEL; turning `"formal"`/`"casual"`/
   `"neutral"` into an actual lexical/syntactic choice in Bigville's
   `_realize_meaning` phrase tables is bigville-side rendering work, named
   in `BIGVILLE_TOPIC_AND_STYLE_SCOPING.md` itself as belonging to a
   future external Ocelot-side backend, not designed here.

## 9. Files

- `docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_PREREG.md`
- `docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_RESULTS.md`
  (this file)
- `scripts/_build_can_register_quantization_seed.py`
- `seeds/can_register_quantization.json`
- `scripts/can_register_quantization_demo.py`
- `tests/test_can_register_quantization.py`
