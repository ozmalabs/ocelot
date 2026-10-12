# Domain-general signed-shape-field memory for the number-qualia loop

The signed shape-field "fool-me-once" memory that previously lived only in the graph loop (`verify_then_update`) is lifted into the `Domain` abstraction so any domain (sequence, residue, and future ones) can inherit earned distrust. Each `Domain` gains a `memory_aperture`, and three pure-I/O helpers — `domain_mint`, `domain_held_shape`, `domain_net_valence` — let the generic `domain_verify_then_update` loop hold signed `Shape` nodes, derive first-vs-repeat from held substrate state, and read the signed trust through the *same* composed `net_valence_term` graph Term the graph loop uses. Memory is opt-in per call: pass a `substrate` and you get the shape-field behavior; omit it and the exact prior `prior_no_rescue` flag path runs unchanged. The change is additive to `number_runner.py` (+166/−19) plus a new `track_j6_unified_memory.py`; the two existing loops and all track-called functions are untouched.

Watch for: the load-bearing "no false distrust" property is **only proven against a single hand-picked counter-class per domain, and does not generalize** — the ordinal-rank signature at the chosen apertures collapses whole monotonicity classes together, so a geometric anti-shape (k=2) falsely repels a cubic, and a residue no-rescue anti-shape (k=0) falsely repels *any* monotone-increasing list including confirmable ones (confirmed by probe). The `memory_aperture` values are tuned to separate the specific test pair, not the domain's classes (confirmed). Behavior preservation, non-circularity (decision stays the graph Term), solver-free felt reads, first-vs-repeat-from-held-state, and every hard constraint all check out (confirmed).

**Verdict**: NEEDS_CHANGES

## High-level view

The unification is structurally clean and the plumbing is honest. `domain_net_valence` stamps a candidate axis's signature and calls `substrate.evaluate(net_valence_term(), ...)`; it computes no match or sign in Python, so the "no Python decision source" property holds by inspection (the conceptualizer audit does not police this file, so inspection is what matters here). First-vs-repeat with a substrate is genuinely derived from a held negative-valence `Shape` at the memory aperture, not from the `prior_no_rescue` flag — U3 demonstrates this and the flag is only consulted on the no-substrate path.

Behavior preservation is solid. With no substrate the loop is byte-for-byte the old flag-based spine (track_j5 passes, and U5 re-checks the coarse `abstained` vocabulary). With a substrate the graph domain reproduces `verify_then_update`'s reasons and readings on all four paths (confirmed / rescue / first-no-rescue / repeat), matched against the existing loop as ground truth including the authored `bridge` reading.

The correctness of the memory *keying* is where this needs changes. `shape_signature` is an ordinal-rank of the k-th finite difference, which is a monotonicity fingerprint, not a class fingerprint. The per-domain `memory_aperture` (graph=1, sequence=2, residue=0) was chosen to separate the one confirmed/no-rescue pair each track exercises, but at those apertures large families of genuinely different classes share the same rank-shape. The anti-shape therefore distrusts a monotonicity band, not a class, and U2 only escapes this because it picks the single counter-class (a quadratic; an oscillating residue list) that happens to fall outside the band. This is the "hand-tuned to pass" and "residual class-collision" risk called out in the task, and it is real.

The gap is not fatal to the architecture — the coordinate/aperture split is the right shape and the fix is contained to the signature key or aperture selection — but the "no false distrust" claim as currently asserted overstates what the code guarantees.

<details>
<summary>Issues (4)</summary>

1. **Geometric anti-shape falsely repels higher-order polynomials (confirmed)** — at sequence `memory_aperture=2` the geometric anti-shape repels a cubic `[0,1,8,27,64,125]` (`repelled_by_held_antishape`), because both rank to `[0,1,2,3]` at k=2. U2 only tests a quadratic (k=2 difference constant → flat signature). Either prove separation against the full polynomial family or change the key so it fingerprints the class, not the monotonicity.
2. **Residue anti-shape falsely repels any monotone-increasing list, including confirmable ones (confirmed)** — at residue `memory_aperture=0` the no-rescue anti-shape `[1,2,4,7]` repels `[1,2,3,4]`, a list whose parity-runs equal its mod3-runs (a genuinely confirmable, different class). U2's confirmed list `[2,3,2,3]` only separates because it is non-monotone. k=0 is not "the domain's discriminating aperture," it is the aperture that separates the two chosen lists.
3. **`memory_aperture` justification is per-pair, not per-domain (confirmed)** — no single fixed aperture separates geometric from both quadratic and cubic (k=2 separates quad only; k=3 separates both but collides elsewhere and drops the curvature story). The docstring/probe rationale generalizes from one counter-example; state the actual guarantee (separates *these* classes) or widen the U2 battery to break it.
4. **U2 assertion is too weak to be load-bearing (confirmed)** — it asserts `net_valence == 0` for exactly one non-matching class per domain. Add adversarial members from the same monotonicity band (a cubic for sequence; a monotone confirmable list for residue) so the test would fail on the current key, then fix the key until it passes.

</details>

<details>
<summary>Details</summary>

### Transport of the memory into the Domain layer

The graph-ness of the old memory was only ever in two places: the coordinate extractor (`structural_coord`, degree-in-traversal-order) and the hardwired aperture `k=1`. The three new helpers factor those out. `domain_mint(domain, obj, valence, substrate)` calls `mint_shape(substrate, domain.coordinate(obj), domain.memory_aperture, valence, ...)`; `domain_held_shape` calls `_held_shape_for` at the same aperture; `domain_net_valence` stamps the candidate signature and evaluates `net_valence_term()`. Any numeric coordinate flows through unchanged, which is the correct abstraction — the loop no longer knows or cares whether the coordinate came from a graph or a sequence. `domain_verify_then_update` gains an optional `substrate=`; when present it front-loads a `domain_net_valence < 0` fool-me-once early-out and routes minting through the outcome branches, and `_domain_no_rescue` derives `is_repeat` from a held negative-valence shape instead of the flag.

### The discriminating-aperture correctness (load-bearing) — under-proven

`aperture_signature(coord, k)` takes the k-th finite difference and passes it through `substrate.shape_signature`, which is an **ordinal rank** of the difference values normalized to width 8. That means the signature encodes the *order type* (monotonicity/curvature pattern) of the k-th difference, not the class that generated it. Any sequence whose k-th difference is strictly increasing ranks to `[0,1,2,3,...]`, and the `net_valence_term` L1 match with `SHAPE_MATCH_TOL=2.0` then treats them as the same held shape.

U2 asserts that the sequence geometric anti-shape (k=2) does not repel a polynomial. It passes because the chosen polynomial is a **quadratic** `[0,1,4,9,16,25]`, whose 2nd difference is the constant `2`, ranking to the all-zeros signature — genuinely distinct from the geometric's `[0,1,2,3]`. But that is the one polynomial that separates. A cubic `[0,1,8,27,64,125]` has a strictly-increasing 2nd difference and ranks to `[0,1,2,3]`, colliding with the geometric:

```
mint -1 geometric anti-shape at k=2, then:
net_valence(cubic  [0,1,8,27,64,125]) = -1.0   -> domain_verify_then_update -> repelled_by_held_antishape
net_valence(quad   [0,1,4,9,16,25])   =  0.0   (the class U2 happens to test)
```

An aperture sweep confirms no single fixed k separates geometric from the polynomial family: k=2 separates geo from quadratic but not cubic; k=3 separates geo from both but then geo collides with other shapes at k=4/k=5 and abandons the "curvature" rationale. So `sequence.memory_aperture=2` is tuned to the `(geometric, quadratic)` pair, not to a property of the sequence domain.

The residue case is the same failure and easier to trip. `residue.memory_aperture=0` keys on the rank of the raw values. The no-rescue member `[1,2,4,7]` ranks to `[0,1,2,3]` — the monotone-increasing signature shared by *every* strictly increasing 4-list. The "confirmed" list U2 tests, `[2,3,2,3]`, only separates because it oscillates (`[0,2,0,2]`). A monotone-increasing list that is genuinely confirmable is falsely repelled:

```
mint -1 residue anti-shape ([1,2,4,7]) at k=0, then:
net_valence([1,2,3,4]) = -1.0   (parity-runs == mod3-runs: a CONFIRMABLE, different class)
net_valence([2,4,6,8]) = -1.0
```

The residue probe rationale in the summary ("k=0 is the smallest discriminating aperture") is really "k=0 is the smallest aperture that separates `[1,2,4,7]` from `[2,3,2,3]`." Residual class-collision is not covered — it is the norm across the monotone band, not an edge case.

None of this breaks the *architecture*: the coordinate/aperture split is right, and the fix is local — either replace the rank signature with a key that fingerprints the generating class (e.g. include the difference magnitudes/ratios, not just their order type), or accept the aperture is a heuristic and scope the claim accordingly. What must change is the U2 assertion and the "no false distrust" framing, which currently generalize from one counter-class to a universal property the code does not have.

### Behavior preservation — holds

With no substrate, `_domain_no_rescue` sets `is_repeat = prior_no_rescue` and returns the coarse `abstained` reason on a first no-rescue, identical to before; track_j5 passes and U5(a) re-confirms the graph confirmed/rescue reasons and the sequence first=`abstained`/repeat=`self_extended_authored_reading` shapes. With a substrate on the graph domain, U5(b) matches `domain_verify_then_update` against the untouched `verify_then_update` as ground truth on all four paths and requires the reasons *and* readings to be equal, including `rescued_by_reading`→`spanned_k0` on the barbell and `self_extended_authored_reading`→`bridge` on the bridged-triangles no-rescue graph. The `bridge` reading is popped from both the module repertoire and the domain repertoire before each arm so the authoring path is exercised from a clean state rather than a pre-adopted one. track_j3/j4/j5/j6 all exit 0.

One behavioral subtlety worth noting rather than flagging: on the substrate path a repeat that entered via the fool-me-once guard (`repelled=True`, no `truth` computed) spends a `verify` call inside `_domain_no_rescue` to feed the authoring gate. This is the investment step, distinct from the felt commit that fool-me-once correctly skipped, and it mirrors what the graph loop does when it authors on a repeat — so verify is still spent exactly once on that path, not twice.

### Non-circularity and the net_valence decision — holds

`domain_net_valence` builds a scratch `Axis`, stamps `csig_*`/`aperture` via `stamp_candidate_signature` (a finite difference plus an ordinal rank — arithmetic I/O), and returns `substrate.evaluate(net_valence_term(), {"x": axis})`. The match (L1 ≤ tol) and the sign (valence product summed over held shapes) are entirely inside the composed graph Term; no Python `if`/compare decides trust. U4 nails this down by reconstructing the term-eval path inline and asserting `domain_net_valence(...) == substrate.evaluate(net_valence_term(), ...)` for sequence, residue, and graph domains, and the values match exactly. The conceptualizer audit (`test_no_python_decision_source_audit`) stays green, but note it greps only `domains/conceptualizer.py` and does not inspect `number_runner.py`; the non-circularity of the new helpers rests on the U4 equivalence and the code reading above, not on the audit. `domain_mint` and `domain_net_valence` are pure I/O (stamp + mint/evaluate) with no decision — confirmed.

Felt reads stay solver-free: U4 routes every domain's `default_read`, `seq_felt_degree`, `res_felt_read`, and `felt_aperture_read` through a `SolverSpy` and asserts 0 calls; the net_valence memory reads pass no spy and touch no solver by construction (the scratch axis and `NodesWhere Shape` iteration are graph ops). Verify remains the separate spy-pinged step.

### First-vs-repeat from held state — genuinely derived

The reviewer's original concern (that `prior_no_rescue` was doing the work in disguise) is addressed for the substrate path. `_domain_no_rescue` computes `is_repeat` from `domain_held_shape` finding a held shape whose `valence < 0` at the memory aperture; the flag is only read when `substrate is None`. U3 passes a substrate and shows enc1→`no_rescue_minted_antishape` (mints the −1) and enc2→`self_extended_authored_reading` (`log_degree` for sequence, `mod3_runs` for residue) with no flag passed. The repeat is driven by the held negative shape, not the flag. (This inherits the keying weakness above — "held shape at this aperture" means "held shape in this monotonicity band" — but the *mechanism* is state-derived as claimed.)

### Resource lifecycle — minor note

`domain_net_valence` adds a scratch `Axis` node to the substrate on every call and never removes it. `net_valence_term` iterates `NodesWhere Shape`, so orphaned Axis nodes don't corrupt future reads, and the tracks use short-lived substrates, so this is not a correctness issue. Worth being aware of if the memory is ever driven over a long-lived substrate with many candidate reads.

### Hard constraints — all clean

`.so` md5 = `7efe75eba05b006cafd15dbb4b7da246` (unchanged, no Rust rebuilt). Only `runners/number_runner.py` (modified) and `track_j6_unified_memory.py` (new) appear in the number_qualia diff. Protected read-only files (`can_ops.rs`, `can_junction_tree.py`, `can_native_bp.py`, `model_reader.py`), `seeds/residual_salience.json`, `seeds/autonomy.json`, and `/applications` show no diff. No `_probe_*` files remain under number_qualia. No commit made.

</details>

<details>
<summary>File map</summary>

- `tests/capability/number_qualia/runners/number_runner.py` — adds `Domain.memory_aperture`, the three domain-general memory helpers, and the opt-in `substrate=` path in `domain_verify_then_update`/`_domain_no_rescue`; sets `memory_aperture` on the three domains. Existing loops (`verify_then_update`, `seq_verify_then_update`) untouched.
- `tests/capability/number_qualia/track_j6_unified_memory.py` (new) — U1–U5 demonstrating domain-general fool-me-once, the (under-proven) no-false-distrust claim, first-vs-repeat from held state, net_valence-is-the-Term, and behavior preservation.

Full diff: `git diff main -- tests/capability/number_qualia/`
</details>
