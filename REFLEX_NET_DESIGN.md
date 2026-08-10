# The primal layer — reflex nets as self-editable graph data

**Directive (2026-07-12):** *"plan and execute the build — the jabberwock's
self-editing function should be expanded to cover this [neural-net] machinery
and integrated natively with the engine to make it generally 'free' but also
optional and tweakable."*

Context from the assessment that preceded it: the Jabberwock's nets are meant
as **the primal layer — instincts and reflexes, the cheap default path that
avoids active cognition**. The self-learning-net experiments showed nets snap
correctly within ~30% of their training basin and are **confidently wrong
outside it**, so an ungrounded net cannot police its own basin; cognition must
correct it out-of-basin, and the basin gate must be **external** to the net.
The Jabberwock's cognition is extensive; the primal layer was the missing tier.

## The design decision that makes it small

A reflex net is **ordinary graph data**, not a parallel subsystem:

```
ReflexQuery{status, residual, input_vec}
   -for_net->  ReflexNet{name, enabled, basin_threshold}
                  -net_assemblage->  NetworkAssemblage (+ WeightTensor children)
                  -has_tunable->     TunableParameter{attr_name:"enabled", ...}
                  -has_tunable->     TunableParameter{attr_name:"basin_threshold", ...}
```

The **fast path is an ordinary Rule** (`reflex_net_serve`) whose `where` gates
on (a) an `enabled` knob and (b) `residual < basin_threshold`, and whose effect
writes `NetForward(assemblage, input_vec)` as the answer. Because the fast path
is a Rule and its knobs are `TunableParameter`s, **the existing rule spine
covers adopt / ablate / tweak with no new executor**:

| Requirement | How it is met |
|---|---|
| **native / free** | `NetForward` Rust Term — the forward pass runs in-engine inside the rule, not as N Python `evaluate()` round-trips. Byte-parity with `code_writing_cortex.forward()`. |
| **optional** | `enabled` defaults to `0.0`; nothing serves until an adopt/human decision flips it. Minted OFF. |
| **tweakable** | `basin_threshold` / `enabled` / judge `tolerance` are `TunableParameter`s read via `Attr`; editing the held node changes behavior with zero code. |
| **self-editable (adopt)** | the fast path is a Rule → `add_rule` / `perform_adoptions`; adopt a net = flip `enabled`. |
| **self-editable (ablate)** | `remove_rule` tombstones the serve rule; or disable the node. |
| **judged** | `reflex_trial_judge` — the one genuinely new decision: **supported iff regression-free AND faster** (not standalone accuracy). |

## Fast serve path + deep-reader demonstration (2026-07-12, follow-on)

- **Fast serve path.** `NetForward`'s per-call cost for a small net was dominated
  by the generic `evaluate()` term-parse. The forward pass is now a pure
  `net_forward_core(graph, node, input)`; a thin PyO3 method
  `Substrate.net_forward(id, inputs)` calls it directly, skipping the parse. The
  tiny trained net now serves in **2.9µs (was 22µs)** — 7.7× the evaluate path
  and a **consistent 7.7–8.8× over pure-Python at every net size** (the evaluate
  path was overhead-bound at 0.8× for tiny nets). Rules still compose the
  `NetForward` Term; adapters serving in a hot loop use the direct method.
- **The win is huge where cognition is expensive — the deep reader
  (`scripts/reflex_reader_demo.py`).** The real `WorldAdapter` reader comprehends
  a sentence in **~44ms** of active cognition. A reflex cache — memoized verdict
  (reading verdicts are symbolic, not a NetForward vector) gated by the SAME
  `ShapeDecode`-residual basin machinery over a `SeenQuantum` codebook — serves an
  in-basin (seen-vocabulary) sentence in **~0.1ms: ≈360–440× faster**, while a
  novel sentence (unknown quanta → residual > 0) is correctly **DEFERRED to the
  full reader**. This is the primal layer paying off in the domain the whole
  design pointed at: cheap default path for the routine, cognition for the novel.

## One primal layer, FOUR SENSES (2026-07-12) — handwriting, vision, language, speech

The primal layer is modality-agnostic: every sense in this substrate quantizes
its input to a SIGNATURE ("dynamic quantization is the core loop"), so the
reflex net + basin gate + self-training-by-collapse is ONE mechanism over
signatures. A modality plugs in by supplying, per example, a FEATURE vector (the
net's input), a SIGNATURE (relation tuples — the basin gate decodes these), and a
VERDICT class (its cognition's decision — the training target).

- **`domains/modality_reflex.py`** — the generic per-sense adapter: mint a
  `self_training` reflex net, `observe` (ingest `ReflexObservation` nodes),
  `train` (tick — the ENGINE collapses via `net_collapse`, no Python
  `net_collapse_step` in the loop), `predict` (native forward + argmax), and
  `serve_or_defer` (a RELATIVE `ShapeDecode`-residual basin gate over the
  modality's own `SeenQuantum` codebook). Mechanical I/O only; every decision is
  a seed rule.
- **`scripts/reflex_modalities_demo.py`** — all four senses through the SAME
  adapter with real feature extraction: **handwriting** (pen-path turn/length
  geometry), **vision** (cv2 Hu moments + fill-density grid), **language** (the
  real reader's `comprehend_text` `(kind,focus)` verdict), **speech** (scipy
  spectral bands of synthesized formants). Each self-trains a reflex net by
  surprise-driven collapse and gates on its own basin. Measured: held-out
  accuracy **100% / 75% / 75% / 100%**; **all four correctly DEFER a novel
  input**; 3/4 serve in-basin (language's basin is *vocabulary*, so a held-out
  sentence with new words correctly defers — the gate working, not a miss).
- Gate: `tests/test_modality_reflex_migrated.py` — the adapter self-trains a
  modality to ≥85% held-out via the engine loop, serves in-basin, defers
  out-of-basin; two independent senses share the mechanism with separate basins.

Honest caveats: small per-modality datasets, real feature extraction on
synthetic-but-real inputs with ground-truth verdicts. The claim is the
MECHANISM — one self-training reflex layer serves all four senses via each
one's quanta — not a benchmark number per sense.

## Nets SELF-TRAIN via collapse and surprise (2026-07-12, the correction)

The creator's correction: the original design has nets train *themselves* from
their own surprise, as part of the collapse loop — NOT an external optimizer.
Recon confirmed this never existed (composed nets are write-not-train, learned
nets use plain SGD, and the CAN Hebbian primitives update *Concept* J/h, never a
`WeightTensor`) — a real gap, now closed:

- **`net_collapse_step`** (Rust, `net_forward.rs` + a thin `Substrate.net_collapse_step`
  method) is the `WeightTensor` twin of `can_ops::hebbian_update_J`. The net
  PREDICTS (`NetForward`) → SURPRISE = `target − prediction`
  (prediction_minus_observation, meta-shape #33) → the readout weights COLLAPSE
  toward reducing it by the **normalized** local delta rule (NLMS:
  `W2 += η·e·hiddenᵀ / (‖hidden‖²+1)`, stable for any η∈(0,2)), with `W1`/`b1`
  the fixed random-feature layer (ELM-online — local, no backprop). It mutates
  the net's own weights in place and returns the surprise, which falls toward 0
  as the net learns — the same "surprise drops on recurrence" signal
  `native_collapse` reports for discrete constructs.
- **The loop is graph-native.** The DECISIONS are rules:
  `reflex_request_training` starts it (a refuted trial), and
  `reflex_self_train_converged` stops it (surprise below the net's `converge_tol`
  knob → `status:"trained"`, ready for the judge).
- **WIRED IN AT THE ENGINE LEVEL.** The surprise-driven collapse fires INSIDE
  `run_rules` itself, via a new `net_collapse` **effect kind** — the
  `WeightTensor` mutation follows the sanctioned `Effect::FbSample`
  queue-and-drain pattern (the applier holds only `&mut graph`, so it queues
  `(reflex_net, input, target, eta)` on `graph.pending_net_collapses`;
  `Substrate::run_rules` drains it between passes via `net_collapse_step` and
  records the rolling (EMA) surprise back onto the net). The rule
  `reflex_net_self_train_step` matches a pending `ReflexObservation -observes->`
  a `self_training` net and fires the collapse; the adapter only INGESTS
  observation nodes and `tick()`s — **Python never calls `net_collapse_step` in
  the loop; the engine's collapse does the training.** So a reflex net trains
  itself as part of the graph's collapse, with zero Python iteration — the
  literal realization of "collapse and surprise within the net."
- **Demonstrated** (`scripts/reflex_self_train_demo.py`): a net with a ZERO
  readout (predicts 0, maximally surprised) is fed only `(x, x²)` pairs and
  trains ITSELF to **<0.044 error** over 150 annealed epochs — test error
  0.47→0.044 monotonically, surprise falling ~20× — **no external optimizer, no
  gradient library, no batch solve.** Collapse + surprise within the net.

The external ELM batch fit (`train_child.py`, below) is now the **cold-start /
batch-re-derive fallback**; the online surprise-driven collapse is the
architecturally-correct primary mechanism (and needs no subprocess).

- **Tested on a REAL task** (`scripts/reflex_selftrain_reader_task.py`): a
  self-training net (ZERO readout) reproduces the REAL deep reader's 9-way
  `(kind, focus)` speech-act verdict — statement vs question and the wh-focus
  (reason/place/thing/manner/time/selection) — learned **only by
  `net_collapse_step`** on the reader's own labels. **Surprise 1.05→0.0008,
  held-out accuracy 89%, serving 50× faster** than the reader's parse. No
  external optimizer. Honest caveats: small corpus (9 held-out), a cue-driven
  (learnable) verdict — exactly what a reflex cache is for — and `comprehend_text`
  is the cheap parse path (the net caches the *numeric* (kind,focus) decision; the
  expensive symbolic full-turn reply needs the memoization cache of the
  reader-cache demo, not a NetForward vector). Gate:
  `test_self_train_multiclass_classification`.

## Training is a managed BACKGROUND process (2026-07-12, follow-on)

The agent trains a reflex net when it decides to, end to end, as a background
process (not offline):

- **The decision is a rule** (`reflex_request_training`): a REFUTED `ReflexTrial`
  (the net's approximation regresses beyond tolerance — the judge already decided
  that) → mint a `TrainingJob{status:"trace_pending"}`, once per trial. The agent
  deciding to improve itself by training; no Python decided it.
- **The dispatcher is the sanctioned background pattern** (`domains/training_dispatch.py`,
  the exact mirror of `experiment_dispatch`): scan `TrainingJob{requested}` → spawn
  a DETACHED `Popen(scripts/train_child.py)` → **never block** → poll with
  `proc.poll()` → ingest on exit. The agent keeps ticking while training runs — a
  background job, not an offline batch. Ticked from the daemon at `--dispatch-every`
  like `_dispatch_tick`.
- **The trainer is a real, fast fit** (`scripts/train_child.py`): an Extreme
  Learning Machine (fixed random ReLU features + least-squares readout via
  pseudoinverse — the same "authored features, fit the readout" shape as
  `construct_elm_readout`), self-contained numpy, producing a `NetForward`-readable
  2-layer block. Fits x→x² to MSE ~1e-5 in <1s.
- **Ingest folds the weights into the graph** (`_weights_to_assemblage`, mechanical):
  the fitted matrices become `NetworkAssemblage -has_step-> AssemblageStep
  -has_weight-> WeightTensor{role,data}`, wrapped by a DISABLED `ReflexNet` with the
  training range as its numeric basin.
- **Then the existing spine takes over**: measure regression → `reflex_trial_judge`
  (regression-free AND faster) → adopt (flip `enabled`) → serve natively. The
  trained (fuzzy) grade rides the identical gate + judge the constructed grade uses.

Gate (part of the suite below): `test_agent_decides_to_train_on_a_refuted_trial`;
`test_training_runs_as_a_background_process_end_to_end` — real subprocess: decide →
dispatch (spawns, returns running) → poll to done → ingest → trained net
approximates x² (<0.02) → judge supported → adopt → serves.

## What landed (all tested, `tests/test_reflex_net_migrated.py`, 22/22)

1. **`NetForward` Term** (Rust, `runners/dsl/src/net_forward.rs` + 5 wiring
   sites). Reads `NetworkAssemblage -has_step-> AssemblageStep{order}
   -has_weight-> WeightTensor{role,data}`, computes `ReLU(W1x+b1); W2h+b2`
   chained, read-only over G, graceful identity on a non-net node. Reaches
   Python free via the generic `evaluate()` (no bespoke py.rs method).
   *Gate:* native == Python `forward()` byte-for-byte on the square_pwl net.
2. **`seeds/reflex_net.json`** — the layer as graph data: productions, the
   reflex-net microtheory + invariant concepts, the basin-gated `reflex_net_serve`
   fast path, the `reflex_trial_judge` / `reflex_trial_refuted` judge, and
   `auto_propose_reflex_net` (THE MINT).
3. **`auto_propose_reflex_net` (the propose step, graph-native)** — a hot op
   (`baseline_mean_ms` above the floor) that already has a constructed net
   (`-has_assemblage-> NetworkAssemblage`) is proposed as a reflex net by
   `run_rules`: mint a `ReflexNet` OFF, wire it to the assemblage, attach its two
   `TunableParameter` knobs, mark the target once (`reflex_proposed=1`, the
   `gap_awareness` once-guard). The agent proposes its own reflex nets — no
   Python decides it — and the proposal is OFF/pending until the judge + adopt
   spine enables it. Cold ops get no proposal.
4. **`domains/reflex_net.py`** — the mechanical mint builder (`mint_reflex_net`
   / `mint_reflex_query`): emits graph data only, mints OFF by default (the
   adapter-side twin of the propose rule, for host-initiated mints).
5. **`reflex_ground_residual` (the basin gate, grounded)** — a raw query's
   `residual` is COMPUTED by the graph as `Count(ShapeDecode(signature,
   ShapeSignature codebook, field="residual"))` — the sd-loop decode residual
   (how many of the input's relations the held quantum codebook does not cover:
   0 = fully in the known basin). Then `status: raw → pending`, so
   `reflex_net_serve` gates on the agent's own decode against what it knows, not
   a caller-supplied number. This is the confidently-wrong-outside-basin
   safeguard, grounded.
6. **`reflex_ground_numeric_residual` (the numeric grade)** — a float net's
   basin is its fit range `[fit_lo, fit_hi]`; the grounded residual is
   distance-outside-range `Max(fit_lo - x, x - fit_hi, 0)` (0 inside, growing
   with extrapolation) — the numeric twin of the symbolic ShapeDecode residual,
   per-net by construction (reads the net's own `fit_lo`/`fit_hi`). The "~30%
   basin" is real geometry.
7. **The trained/approximate grade, at the decision level** — a net whose answer
   is APPROXIMATE (proven with the square_pwl's real ≤0.0025 PWL error) is a
   fuzzy cache the regression-free-AND-faster judge adopts only within tolerance
   (lenient tol → supported; tighter tol → refuted). This is the exact machinery
   a gradient-trained head reuses: **the residual gate + this judge are what make
   a fuzzy cache safe.** Training the weights is offline torch; the safety
   DECISION is here and graph-native.
8. **Gates**: off-by-default (optional); serves natively within basin; defers
   outside basin (external gate); `basin_threshold` + propose thresholds
   tweakable zero-code (`ReflexNetPolicy`); judge
   supported-iff-faster-and-regression-free; adopt/ablate via `add_rule`/
   `remove_rule`; the builder path; auto-propose mints once for a hot **or
   explicitly-requested** op and never for a cold one; **the basin residual is
   grounded by `ShapeDecode` (in-basin decodes clean → serves; a novel relation
   → defers)**.

## Honest residuals — what this slice does NOT do

- **Auto-mint is graph-native, but not yet routed through the NL
  `ground_concern` vocabulary.** `auto_propose_reflex_net` already proposes a
  reflex net autonomously via `run_rules` (a hot op with a net → an OFF
  proposal). What remains is the *linguistic* hook: a
  `ComposerCue{relation_head:"reflex"}` so a natural-language self-instruction
  ("cache this", "make a reflex for X") also routes to the mint — deliberately
  not half-wired here to avoid churning the composer-dispatch tests. The
  propose→judge→adopt→ablate→tweak loop itself is complete in the graph.
- **The propose-trigger thresholds are Lits, not yet policy knobs.** The
  minted net's `basin_threshold` IS a `TunableParameter` (the load-bearing
  knob), but the hot floor (`0.05`) and default basin (`0.25`) in
  `auto_propose_reflex_net` are literals; lifting them onto a tweakable
  `ReflexNetPolicy` singleton is a small follow-up.
- **The tier-up / hot-counter plumbing is not the substrate here.** Recon found
  `l2_adaptive` / `code_cache` / `l2_dispatch` are standalone scaffolding (test-
  only callers, documented as not-yet-wired in `scripts/jabberwock_whats_next.py`).
  This slice integrates natively via the live `run_rules` path instead; wiring a
  hot-counter → auto-propose loop on top is future work.
- **Per-net SYMBOLIC basin codebooks.** The numeric grade is already per-net
  (each net's `fit_lo`/`fit_hi`), and per-net basin *width* is expressible via
  per-net `basin_threshold` over the shared residual. What remains is per-net
  *domain* scoping of the symbolic `ShapeDecode` codebook (so net A decodes
  against a different `ShapeSignature` subset than net B): `ShapeDecode`'s
  `exclude` matches by name and its `codebook_type` is compile-time, so a clean
  generic version needs a small Rust affordance — a `codebook_scope` set param
  restricting the codebook to nodes linked from the net. Deferred as a scoped
  Rust change (`ShapeDecode` has a wide blast radius; not bundled here).
- **Training as a background process — LANDED** (see the section above). The
  agent decides (rule) → dispatches a detached trainer → ingests → judges →
  adopts, all tested end to end. The current trainer is an analytic ELM fit;
  swapping in a gradient/torch backend (or distilling from a teacher net) is a
  drop-in change to `scripts/train_child.py`'s routine — the decide/dispatch/
  ingest/judge/adopt scaffold is backend-agnostic. What remains for a full
  DISTILLATION loop: (a) the adapter mechanically collecting live (input →
  verdict) traces from active cognition and calling `attach_traces` (here the
  test supplies them); (b) wiring `_train_tick` into the daemon loop at
  `--dispatch-every` (the function is ready; the daemon hook is one call, like
  `_dispatch_tick`); (c) surprise (`prediction_minus_observation`) deopt →
  re-train on the corrected traces (the refuted-trial → `reflex_request_training`
  rule is the first turn of exactly this loop).
- **Trained-net grade untouched.** This lands the CONSTRUCTED grade (exact,
  no basin problem). A trained-head reflex (fuzzy, basin-limited, shortlist-
  only) reuses the identical machinery — the `residual` gate and the
  regression-free judge are exactly what make a fuzzy cache safe — but training
  + the offline distillation loop are a separate slice.
- **`forward` is fp; no incremental cache.** `NetForward` recomputes each call;
  a per-query result cache keyed on G-mutation (not `gamma_epoch`, which only
  tracks Γ) is a further efficiency lever, not built here.

## Neurological / evolutionary framing (why this shape)

Cortex-teaches-the-reflex (cerebellar climbing-fiber error → basin-limited fast
system), an escalation gate that is a *separate conflict monitor* rather than the
habit system's own confidence (ACC/predictive-coding), and expert
recognition-primed intuition (AlphaGo policy/value split). The two reflex grades
map to genome-authored instinct (constructed net) vs lifetime-learned skill
(trained net). See the conversation assessment for the full mapping and its
honest tensions (Baldwinian build order; the external gate is the component
biology proves essential yet imperfect — hence the wrong-and-admitted rate is
the metric that matters).
