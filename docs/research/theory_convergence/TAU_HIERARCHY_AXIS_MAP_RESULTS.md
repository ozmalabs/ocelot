# τ-hierarchy axis map — RESULTS

**Date:** 2026-08-11
**Prereg:** `TAU_HIERARCHY_AXIS_MAP_PREREG.md`, registered before any bar
below was read (including an in-flight amendment, §7a of that document,
made after a dry run surfaced a scoring confound — disclosed there and
carried through here).
**Worktree:** `/home/matt/ocelot-tau-hierarchy`, branch `tau-hierarchy-review`,
base commit `80f353e` (== `main`'s tip verified at task start,
`git log --oneline -1 main`).
**Engine:** sha256
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567` — same
binary the most recent landed rung used; coherence probe passed
(`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back list and tuple
distinctly).
**Artifacts:** `scripts/tau_hierarchy_probe.py` (the probe; read-only over
`seeds/`, `domains/`, `runners/`, no `data/` touched), raw JSON output
captured at N=40 and N=200 in this document's tables (not committed as a
separate results file — the JSON is small and reproduced inline).
**Regression:** `tests/test_transform_decode_migrated.py` +
`tests/test_dimension_inference_migrated.py` — 25/25 green, unaffected
(this rung added two files, modified none).

---

## 0. Reading order

If you read nothing else: **§4 (the axis map) is the primary deliverable,
and §2a is its sharpest single finding** — a real, already-gated,
unconstructed split in this repo's own code between residual-handling that
stays local (object-level) and residual-handling that promotes to
graph-resident, vocabulary-revising data (meta-level), which is the
precise order parameter τ3 needs and does not currently have. §2/§3 are
the two measured, constructed legs that motivate and corroborate it. §7
gives the recommendation for the paper.

---

## 1. Part A — the historical check (orienting evidence)

Reported in full in the prereg (§3); summarized here. Real commit data from
`ozmalabs/internal`, path `research/experiments/gamma-substrate`
(paginated `gh api`, ~800 commits, 2026-06-30 – 2026-08-10). Local `ocelot`
history is a single squashed import and cannot corroborate independently.

| date | shape |
|---|---|
| 07-02 | Axis-L-shaped: sd-loop MDL/Occam growth ladder lands ("growth ladder is complete") |
| 07-06/07 | Axis-C-shaped: character ToM (Sally-Anne belief/world split) |
| 07-08/12 | Axis-L-shaped again, a *different* flavour (self-account/gap-awareness) |
| 07-28 | Axis-C-shaped again (bigville "ShapeDecode-ToM") |

**Reading:** L → C → L → C, interleaved, not a clean before/after in either
direction. Consistent with axis-orthogonality (independent axes interleave;
a strict ladder would show a clean order), but this is corroborating, not
decisive — flagged honestly in the prereg and not treated as a gated bar.

---

## 2. TAU-C — comparative axis (old τ2): is the bare ratio operable?

**Mechanism.** Two disjoint `ShapeSignature` codebooks (`owner="self"` /
`owner="other"`) in one substrate — literally Theorem C's type-vocabulary
extensibility applied to a foreign-Γ namespace, not a metaphor for it.
`ρ_self(I)`/`ρ_other(I)` computed live via the real `ShapeDecode` Term
(`domains/reflective_faculty.py::compose_design_for_goal`, restricted per
codebook via `exclude`). Decision task: for each instance, choose
ENCODE-SELF / ADOPT-OTHER (pay cost `A`) / MINT (pay cost `M`, no foreign
content needed) to minimize true total cost, where `A`/`M` are the
constructed proxy for "content that says what the ratio means for
capability" (bound-theorem content) — explicitly *not* a claim to execute
Theorems X/XI/XII literally.

**Final run: N=200** (a single, disclosed power increase over the N=30
minimum and the first N=40 run — both reported, not just the more decisive
one, per §7a's amendment discipline).

| battery | ratio-only acc (full) | fixed-baseline acc (full) | **ratio-only acc (restricted*)** | **fixed-baseline acc (restricted*)** | **advantage (restricted, pp)** | true_action dist (self/adopt/mint) |
|---|---|---|---|---|---|---|
| **TAU-C-a** (A/M independent of ρ-gap) | 0.880 | 0.845 | **0.946** | **0.909** | **+3.8** | 169 / 17 / 14 |
| **TAU-C-b** (A/M proportional to ρ-gap, control) | 0.670 | 0.390 | **1.000** | **0.582** | **+41.8** | 78 / 56 / 66 |

\* restricted to instances whose true optimum is `self`/`adopt` — both
decision procedures structurally cannot select `mint` (a ratio between two
*existing* codebooks carries no information about a third, self-directed
growth action), so the full-battery number is capped by the mint-fraction
symmetrically for both rules and the restricted number isolates the
comparison the bars are actually about (§7a of the prereg).

**Earlier N=40 run** (first registered run, reported for transparency, not
suppressed): TAU-C-a restricted advantage = +10.5pp (landed just inside the
pre-registered NULL band, 10-20pp); TAU-C-b restricted advantage = +45.8pp
(clearly passes the ≥80% accuracy control bar, 100% observed). The N=200
run sharpens TAU-C-a's estimate downward (+3.8pp, noise shrinking with
sample size in the expected direction) rather than reversing it — the two
runs agree in sign and in which side of the ambiguous band they end up
closer to.

### TAU-C-a verdict: **CONFIRMS the suspected flaw.**

+3.8pp is below the pre-registered 10pp "confirms" threshold. When the
switching/growth cost content (`A`/`M`) is decoupled from the comparative
ratio, the best possible ratio-only decision rule (oracle-calibrated
threshold, maximally steelmanned) does barely better than a fixed
"always encode-self" baseline — the bare ratio is **representable but not
meaningfully operable** for the resource-allocation decision τ2's own
stated payoff describes ("target competitive parity"). `corr(ratio,
true=adopt) = 0.643` — the ratio is directionally informative (higher ratio
does correlate with "should have adopted"), consistent with it not being
pure noise, but that correlation does not translate into a decision
advantage once `A`/`M` genuinely vary independently of it.

### TAU-C-b verdict: **PASS (control fires as designed).**

When `A`/`M` are a known function of the ρ-gap, the ratio alone is
sufficient (100% restricted accuracy) — this proves the harness and
decision framework are sound, and that TAU-C-a's finding is specific to
cost-content decoupling, not an artifact of the construction or the
composer's own numbers being noisy.

---

## 2a. The sharper order parameter, found after the TAU-L measurement was
already run — WHERE a residual is processed

Mid-write, the creator sharpened the order parameter further, precisely,
and it changes what §3/§4 should lead with (folded in here rather than
re-run, since it is a citation-grounded reframing of already-registered,
already-measured evidence, not a new measurement — see the honesty note at
the end of this subsection). Quoted because the wording is load-bearing:
*"it's about where the residual is processed."* A residual — the gap
between what the system's current law/representation predicts and an
observation that does not fit — can be consumed in exactly one of two
structurally different places:

1. **Object-level (stays local):** the residual is absorbed entirely
   within the existing representation — a weight adjusts, a cached scalar
   verdict is stored — WITHOUT the residual itself ever becoming a
   graph-resident object that the system's own reflective machinery
   (Axiom 3, Π operating on the subgraph representing Γ) can inspect or
   reason over. The system may get better at applying its current law; the
   law's own vocabulary is untouched and invisible to the system as an
   object.
2. **Meta-level (promoted):** the residual is PROMOTED to a graph-resident
   representation Π can operate on — and that promotion is what lets the
   system revise the law's own VOCABULARY (mint a new axis of
   representation), not merely retune its application of the vocabulary it
   already has.

**This is directly, already, gated in this exact repo — no construction
needed, unlike TAU-L-2/3's SelfProcess probe.** Two real mechanisms sit
side by side, verified by reading the code and seed comments this session
(not asserted from memory):

- **Object-level-only, verified as the current state of both citations.**
  (a) `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_
  CAMPAIGN.md` §8 (cited in `GAMMA_SEARCH_COMPLETENESS_CEILING.md` §2.5,
  read this session): `ax_impotent`'s `AgendaVerdict.nearest_unroutable_kind`
  is "computed once, at mint, and **never re-derived**" — a scalar cached
  from a comparison, never promoted into a subgraph the executor
  re-consults; measured, reproduced twice, and named in that document as a
  real bug precisely *because* the situation needed revision and the
  object-level pattern structurally cannot provide it. (b) Γ's own
  admissibility-weight machinery (`grammar.rs`/`checker.rs`,
  `admissible_moves`/`evaluate_weight`, per `GAMMA_SEARCH_COMPLETENESS_
  CEILING.md` §2.1-§2.2, read this session): returns raw summed log-weights
  for a single choice point; that document's own audit found **no code
  path anywhere in this repo that adjusts a `Production`'s weight from an
  observed residual/error at all** — Γ's selection machinery, as it
  currently stands, has no residual-consuming update loop of either kind,
  object- or meta-level; it is a pure lookup over static weights.
- **Meta-level/promotion, verified directly in `shape_decode_loop.json`
  and `shape_decode.rs` this session.** The sd loop's rung 3
  (`sd_infer_dimension`/`DimInfer`): when a residual is coupled across
  observed dimensions in a way rung 1 (existing-basis transform) cannot
  explain, it is scored against a held `DimensionGenerator` codebook and,
  on a match, the seed's own comment (quoted verbatim) states the
  mechanism precisely: *"mints a graph-resident `LatentDimension{name,
  generator, k}` node (`has_latent_dimension` edge) — **the missing
  dimension itself becomes graph data, not merely a recognized delta**."*
  This is real, landed, gated machinery (`tests/test_dimension_inference_
  migrated.py`, part of this rung's own regression check, §"Regression"
  above) — not a probe construct. CLAUDE.md's own "BASE-AS-DIMENSION"
  section (2026-07-08) is the prose account of the same landing: *"a
  'base' (log/scale/cycle) is NOT hand-set per-frame config — it is a
  `DimensionGenerator` that `DimInfer` selects and `sd_recognize_dim`
  mints as a `latent:<gen>` `LatentDimension`. **A base IS a
  dimension.**"*

**Reading, side by side.** The ARC6 executor's cached-verdict pattern
demonstrates the object-level case going wrong exactly where the paper's
own framework predicts it should: a stored quantity presented as current
truth, never rechecked against what it was a snapshot of — this repo's own
`docs/research/flight_control/HANDOFF_embodied_adaptation.md` names the
general shape ("a fixed absolute constant against a multi-scale quantity is
the recurring bug"), and `GAMMA_SEARCH_COMPLETENESS_CEILING.md` §2.5
already generalised it once. The sd loop's `LatentDimension` mint
demonstrates the meta-level case succeeding at exactly the thing the
object-level case structurally cannot do: not getting-better-at-applying
an existing dimension set, but *minting a new dimension* — literally
revising the system's own representational vocabulary, live, gated,
reproducibly (`dim_infer_tests` in Rust plus the Python migrated suite).
**Both sides of this contrast are pre-existing, already-gated facts about
this repo — this subsection cites and juxtaposes them, it does not
construct either one.**

**Honesty note on how this folds into an already-measured rung.** TAU-L-1/
2/3 (§3 below) were built and run *before* this sharper framing arrived,
using a related but coarser distinction (does *some* rule read a
representation and does perturbing it change the outcome — Axis R/Axis O).
That work stands as real, measured, complementary evidence — in
particular, TAU-L-2's finding (adding a bare `SelfProcess` description
changes nothing about the composer's real decision) is itself a small
instance of "object-level: the new node was never promoted into anything
the composer's own decision-making reads," and TAU-L-3's wiring is an
artificial, probe-only analogue of promotion. The `LatentDimension`
mechanism above is the **real, unconstructed, already-gated instance** of
the same idea and is the sharper, load-bearing citation; §4's axis map
leads with it and keeps the R/O framing as a related, coarser corollary
rather than discarding the measured TAU-L-2/3 work.

---

## 3. TAU-L — nomological/law axis (old τ3): representable vs operative

**Mechanism.** The sd-loop's rung-ordered growth ladder (real, gated,
`GAMMA_SEARCH_COMPLETENESS_CEILING.md` Probe 1: "a genuine, provable,
Occam-ordered causal DAG") for the *functional* half; `SelfProcess` nodes
(`domains/self_model.py::find_self_process`/`run_self_process`, real,
gated, currently seeded for six processes, **none for
growth/minting/parsimony** — verified directly, not assumed) for the
*representational* half.

### TAU-L-1 — implicit competence without representation

- `find_self_process(["grow","growth","mint","minting","codebook"])` on the
  **unmodified, currently-booted graph** → `None`. φ_R(law) = 0 today, a
  verified fact about this repo's actual state, not a constructed scenario.
- Real rung-ordered ladder, battery of 5 transform-explainable + 4
  genuinely-novel residuals: **4 CapabilityAxis minted** (exactly the 4
  genuinely-novel ones; **5/5 transform-explainable residuals recognized
  WITHOUT minting**). Undirected baseline (mint-everything, the paper's own
  stated τ3 falsifier construction) = **9 minted, by definition**.
- **PASS.** The real ladder mints strictly fewer than the undirected
  baseline (4 < 9) — directed, Kγ-reducing search, live-verified — with
  **zero** Axis-L representation present anywhere in the graph. This is the
  mechanistic form of the creator's own anecdote: functioning according to
  a law, successfully and consistently, with no explicit self-representation
  of that law existing anywhere to be inspected.

### TAU-L-2 — representation added, wiring not

- Tie-break construction: goal = 4 relations; `part_one_big` (1 part, full
  coverage) vs `part_two_a`+`part_two_b` (2 parts, full coverage). Real
  composer output (implicit-only): `ordered_parts=('part_one_big',)` — the
  composer's own `(coverage, total_fit)` key already prefers the few-parts
  route here (searched for, and found, per-step fit values where the
  one-part route's single alignment against the full residual beats the
  two-part route's split alignment — the adversarial-in-the-other-direction
  construction needed for TAU-L-3 below).
- Added one `SelfProcess` node (`process="growing"`, same attrs shape as
  the six existing ones, `objective="min_parts"`) to the throwaway
  substrate only (no seed file touched).
- `find_self_process` → `'growing'`; `run_self_process` → `found=True` — a
  "how do you grow?" query is now answerable (φ_R crosses to 1, verbal-
  report level).
- Re-ran the **identical** composer call: `ordered_parts` unchanged
  (`('part_one_big',)`).
- **PASS.** Mere representation, with nothing reading it, changes nothing
  about the real composer's decision. φ_R = 1, φ_O = 0 — the two are
  dissociated, live, not merely by definition.

### TAU-L-3 — operative wiring added, with a causal perturbation test

- Two real candidate plans generated explicitly (via `exclude`): few-parts
  (`len=1`) and many-parts (`len=2`).
- A minimal decision rule reads the `SelfProcess` node's `objective` attr
  from the live graph and picks between the two real composer outputs
  accordingly (`objective="min_parts"` → `min(candidates, key=len)`).
- **Chosen: the 1-part plan** (matches `min_parts`).
- **Perturbation test:** flip `objective` to `"max_parts"`, same code, same
  candidates, only the represented content changed. **Chosen flips to the
  2-part plan.**
- **PASS.** The decision is causally read from ℓ_X's content, not a
  coincidental artifact of the node's presence — φ_O = 1, proven
  mechanistically (a controlled edit produces the predicted, corresponding
  change), the same register as τ1's own boolean order parameter.
- **Control (non-tied battery, 1 part, 1 relation):** explicit rule returns
  the untouched composer output (`control_noop = True`) — the wiring is a
  no-op exactly where the implicit machinery already has a unique answer,
  confirming the axis is not rigged to "explicit always wins."

**Honesty note on TAU-L-3's decision rule.** The rule that reads
`objective` and re-ranks candidates is a **probe-only construct** — a
throwaway measurement device built to give this rung a causal-wiring
analogue to test against, not a proposal for shippable agent code. It lives
entirely in `scripts/tau_hierarchy_probe.py`, touches no seed/domain/runner
file, and is not offered as "here is how the composer should be fixed" (a
real fix, if wanted, is `GAMMA_SEARCH_COMPLETENESS_CEILING.md`'s own,
separately-scoped §3.5 finding to build on, not this rung's job).

---

## 4. The corrected axis map (the primary deliverable)

The paper's single ladder τ3 ⇒ τ2 ⇒ τ1 ⇒ τ0 packs at least two independent
distinctions into one ordinal scale. Both measured legs above are, at
bottom, the same shape of gap applied to two different subject matters:
**mere representability of content X is not the same as X being causally
wired into a decision**, and the *further*, sharp threshold — not mere
existence — is what delivers each of the paper's own stated payoffs.

| axis | question | order parameter (boolean, structural — same register as τ1's own φ jump) | this rung's evidence |
|---|---|---|---|
| **Axis 0** (= τ0, unchanged) | Do admissible operations compose transitively? | φ(Γ) = fractional giant-component size of A(Γ); jumps at percolation threshold p_c. Paper's own definition, not re-derived here. | Out of scope; `THEORY_CONVERGENCE_AUDIT.md` already reports it as an honest null for independent corroboration (cited, not repeated). |
| **Axis R(X)** ("Representable") | ∃ a subgraph ℓ_X ⊆ G that *some* Π operation can observe/query? | φ_R(X) = 1 iff such an ℓ_X exists and is query-reachable. Axiom 3's literal content, applied to a specific X. | TAU-L-1: φ_R(law) = 0, verified on the real, unmodified repo. TAU-L-2: φ_R(law) crossable by adding one node, in isolation, with zero downstream effect by itself. |
| **Axis O(X)** ("Operative") | ∃ a rule/Term r that reads ℓ_X to compute a decision, such that perturbing ℓ_X's content causes r's output to change correspondingly? | φ_O(X) = 1 iff such an r exists and the perturbation test confirms causal (not coincidental) reading. | TAU-L-3: φ_O(law) crossable independently of φ_R's crossing, and dissociated from it in TAU-L-2 (φ_R=1, φ_O=0 is a real, held state, not a transient). |
| **Axis C** (= τ2, "Comparative") | X = a foreign system's Γ_other. | φ_R(Γ_other), φ_O(Γ_other) — same R/O structure as any other X. | TAU-C: φ_R(Γ_other) trivially achieved (two codebooks coexist in one graph); φ_O(Γ_other) for the STATED payoff (resource-allocation decisions) **requires cost content the comparison itself does not contain** — TAU-C-a's +3.8pp finding. |
| **Axis L** ("Nomological/Law", subsumes and sharpens τ3) | X = the system's own law/bound-theorem content. | **Sharp form (§2a, the lead definition): does a residual get consumed OBJECT-LEVEL (absorbed within the existing representation — a weight/scalar adjusts, never becomes graph data Π reasons over) or get PROMOTED to a graph-resident representation Π operates on, such that the promotion can revise the system's own representational VOCABULARY (mint a new axis), not merely retune its application of the existing one? Coarser corollary: φ_R(law), φ_O(law) — same R/O structure as Axis C, used where no ready-made residual-handling mechanism is at hand.** | **Sharp form:** real, already-gated, side-by-side contrast (§2a) — the ARC6 executor's cached `nearest_unroutable_kind` (object-level only, and independently found buggy for exactly that reason) vs. the sd loop's rung-3 `LatentDimension` mint (promotion, "the missing dimension itself becomes graph data, not merely a recognized delta" — the seed's own words). **Coarser corollary:** TAU-L-1/2/3, φ_R and φ_O dissociate cleanly and mechanistically in a constructed probe (§3). |

**The corrected reading of the paper's four labels:**

- **τ0** stands, unchanged — the one label in the original hierarchy that
  is not actually about representation depth at all; it is about whether
  admissible operations compose transitively in the first place.
- **τ1** ("Γ admits ψ(Γ) operations... the meta-Γ subset is non-empty") is,
  on inspection, **already an Axis-O-shaped claim for X = Γ itself**: it is
  not "does a representation of Γ exist" (Γ obviously exists — it governs
  every admissible operation by definition) but "does *something operate
  on* that representation" — precisely φ_O(Γ). This is why τ1 already has
  a crisp order parameter in the paper: it was already asking the sharp
  question, just for one specific X (Γ itself), not named as a general
  R-vs-O distinction applicable to other content.
- **τ2** ("Comparative") is Axis C, and the paper conflates φ_R(Γ_other)
  (cheap, and what the paper's own Theorem-C argument actually
  establishes) with φ_O(Γ_other) for the specific payoff it claims
  ("operable... target competitive parity") — TAU-C-a shows these are
  genuinely different thresholds, not one.
- **τ3** ("Nomological") is Axis L, and suffers the *same* conflation in
  the *opposite* direction from how the paper frames it: the paper's prose
  ("awareness of the graph law") describes an R-level fact (a
  representation exists, is thereby *known about*), but its stated payoff
  ("directed... search... [changes] from undirected to directed") is an
  O-level claim (a decision-rule is actually governed by that
  representation). TAU-L-1 shows a system can be at **φ_O-equivalent
  competence for the growth law specifically (directed, Occam-sound
  search) while φ_R(law) = 0** — i.e. the paper's own τ3 prose and its own
  τ3 payoff are not the same threshold, and can come apart in either
  direction (TAU-L-1: O-like behavior with R=0; TAU-L-2: R=1 with O=0).
  **§2a's sharper form makes this precise, and is the one to lead with:**
  τ3's real order parameter is not "a representation of the law exists"
  (that is necessary but too weak — CLAUDE.md's own prose has described
  the sd loop's MDL discipline in words since 2026-07-02 without that
  prose ever being graph data anything reasons over) but **"does THIS
  residual-handling code path promote its residual to a graph-resident
  object that can mint new representational vocabulary, or does it
  consume the residual as a local, non-promoted adjustment?"** — a fact
  checkable per-mechanism, already split two ways in this exact repo
  (`ax_impotent`'s cached verdict: no; sd-loop rung 3's `LatentDimension`
  mint: yes), independent of whether any human or agent has ever
  *described* either mechanism in prose.

**Reassignment, stated plainly:** the four-level ladder collapses to
**Axis 0 (unchanged) + a 2×2 (WHICH content: comparative vs nomological) ×
(HOW DEEP: representable vs operative) grid**, not a chain. τ1's crispness
was real but scoped to one cell (Axis-O, X=Γ-itself). τ2 and τ3 are each
better read as a *pair* of cells (R and O for Comparative content; R and O
for Nomological content) than as single rungs — and this rung's evidence
(TAU-ORTHO, below) shows the two content axes (C, L) cross independently of
each other, while TAU-L alone shows the two depth axes (R, O) cross
independently of each other for at least one content type. No evidence
gathered here establishes the four cells (C×R, C×O, L×R, L×O) are
themselves ordered relative to each other in general — only that none of
the four is a *structural prerequisite* for any other, in this substrate,
as constructed.

**The creator's own anecdote, mapped onto the grid:** "operating at a τ3
context... for most of my life, only recently aware of it" is a first-hand
report of occupying the **L×O cell (functionally governed by some law,
successfully) without the L×R cell (no articulable representation of that
law as an object)** for an extended period, then crossing L×R (writing
paper1.tex, naming the law explicitly) — which is exactly TAU-L-1's
mechanistic result, reproduced in this repo's own substrate: real,
Occam-sound, directed growth-search competence (an L×O-*adjacent* fact —
directedness without any articulated law) coexisting with zero L×R content.
One further, honestly-flagged observation from the anecdote, not measured
by this rung: the creator's own crossing order was **R before O becomes
sharp** (naming the law preceded/enabled reasoning about it deliberately) —
consistent with TAU-L-2→TAU-L-3's construction order here, but that is a
choice this rung made in how it built the demonstration, not an
independent finding about which order is *typical* or *necessary*; TAU-L-1
already shows O-like behavior can precede R with no R ever having existed
yet at all.

---

## 5. TAU-ORTHO — structural independence, live-checked

- TAU-L's constructed graphs (TAU-L-1/2/3): zero `ShapeSignature` nodes
  with `owner="other"` anywhere — checked directly against the live graph,
  not assumed from the construction plan.
- TAU-C's constructed graphs: zero `SelfProcess` nodes anywhere — same
  direct check.

**PASS.** Axis C and Axis L can be crossed (both R and O sub-thresholds)
using disjoint graph content and disjoint code paths in this substrate —
a real existence proof, not a general theorem, that the paper's strict
nesting is not a *structural necessity*. Combined with Part A's interleaved
historical record (L → C → L → C, no clean before/after), this is
converging, though not conclusive, evidence for treating C and L as
independent axes rather than adjacent rungs of one ladder.

---

## 6. Overall verdict

**Neither the paper's claimed strict order (τ3 ⇒ τ2 ⇒ τ1 ⇒ τ0) nor a flat
reversal (τ2 ⇒ τ3) is the best-supported reading.** The evidence supports a
**structural correction**: the four-level ladder conflates a content axis
(comparative vs nomological — genuinely different subject matter, shown
here to be crossable independently, §5) with a depth axis (representable
vs operative — shown here, on the nomological side specifically, to be
genuinely dissociable in both directions, §3). τ2's own stated payoff
requires crossing to the O-cell, and TAU-C-a shows that crossing needs
content (cost/benefit semantics) the comparison itself does not supply —
this is the sharpest, most direct evidence for the creator's original
suspicion ("the difference is the ability to meta model the law itself").
But the corrected picture is not simply "τ3 first, then τ2" either — TAU-L
shows the nomological axis's own R and O cells dissociate just as sharply
as the comparative axis's do, so "awareness of the law" is not itself one
threshold; it is (at minimum) two, and the paper's τ3 language already,
silently, mixes them.

**The phase-transition character itself is not weakened by this finding**
— every crossing measured here (φ_R(law): 0→1 in TAU-L-2; φ_O(law): 0→1 in
TAU-L-3; the implied φ_O(Γ_other) that TAU-C-a shows is genuinely absent
despite φ_R(Γ_other)=1) is a discontinuous, boolean, structurally-checkable
fact, in the same register τ1 already established. What changes is which
boolean facts there are, and how many independent ones the paper's four
labels actually name.

**§2a's residual-promotion framing is the sharpest form of this finding,
and it did not need to be constructed** — it is visible, already, as a
real split between two live mechanisms in this repo: `ax_impotent`'s
cached verdict never promotes (object-level only, and independently
diagnosed as buggy for exactly that reason, unrelated to this rung) while
the sd loop's rung-3 `DimInfer`/`LatentDimension` mint does promote (a
residual becomes graph data, and that promotion is what lets the system
mint a genuinely new dimension rather than merely getting better within
its existing ones). This is stronger evidence than TAU-L-1/2/3's own
constructed probe, precisely because nothing had to be built for it — it
is a fact about code that already exists and is already gated, checked by
reading rather than by running a new experiment, and it gives τ3 an order
parameter in exactly τ1's own register: not "is the law described"
(prose, or even a queryable node, can exist with zero downstream effect —
TAU-L-2 proves this directly) but "does this residual-handling path route
through graph data that can mint new vocabulary, or does it stay a local
scalar update, structurally incapable of ever doing so."

---

## 7. Recommendation for the paper (not applied to `paper1.tex` — a private
repo outside this rung's write access; matches the pattern already used in
`SELF_REFERENCE_INFINITY_GROUNDING.md` §5)

1. **Split τ2 and τ3 each into an R-clause and an O-clause**, with the
   O-clause carrying whatever payoff sentence currently follows "Below
   τ_k... Above τ_k...". Concretely: *"τ2-R: Γ admits representing
   Γ_other as a typed subgraph (Theorem C applied to a foreign namespace)
   — unchanged. τ2-O: some rule/decision in Π actually reads that
   representation to compute a resource-allocation or competitive-response
   decision, and the decision provably co-varies with the representation's
   content — THIS is what makes K_sys/K_env 'operable' in the sense the
   current text claims for τ2 alone."* Same split for τ3-R / τ3-O.
2. **Retire the strict nesting τ3 ⇒ τ2 ⇒ τ1 ⇒ τ0 as stated**, or restate it
   narrowly as **τ1 ⇒ τ0 only** (which nothing in this rung disputes — τ1
   is Axiom 3 instantiated, and Axiom 3 is a real precondition for
   representing *anything* reflectively, including both Γ_other and
   bound-theorem content, so τ1's own priority to τ0 and to *both* R-axes
   is untouched). Do not claim an ordering between the C and L content
   axes, or between either content axis's R and O cells, without further,
   dedicated evidence — this rung's existence proof (§5) argues against a
   structural necessity in either direction, and the historical check
   (§1) shows no clean ordering in this repo's own development either.
3. **State τ3's order parameter with τ1's own crispness — lead with the
   residual-promotion form (§2a), not the R/O-split form.** Replace
   "awareness of the graph law" (a description of the effect) with:
   *"τ3: a residual — an observation the current law/representation does
   not explain — is PROMOTED to a graph-resident object Π can operate on,
   such that operating on it can revise the system's own representational
   vocabulary (mint a new dimension/axis), as opposed to being consumed by
   a local, non-promoted adjustment (a weight or cached scalar updates,
   nothing new becomes graph data)."* This is checkable per-mechanism by
   reading code, not by asking whether the system can describe itself —
   exactly the distinction this repo's own `ax_impotent` (fails to
   promote, diagnosed as a bug) vs. `DimInfer`/`LatentDimension` (promotes,
   works) pair already demonstrates, unprompted by this rung's own
   construction. The R/O-split form (§4's table) is worth keeping as a
   secondary, coarser restatement for content types (like Axis C) where no
   ready-made residual-handling mechanism exists to point at directly.
4. **Consider naming a fifth quantity explicitly**: whatever content
   supplies φ_O(Γ_other)'s missing ingredient (TAU-C-a's `A`/`M`
   cost-semantics stand-in) is, in the paper's own vocabulary, close to
   *bound-theorem content applied to the comparison itself* — i.e. τ2-O
   may, empirically in this rung's construction, **require τ3-R/O-shaped
   content as an input**, even though τ3-O (self-directed growth-search
   direction) demonstrably does not require τ2 at all (TAU-L-1). If this
   holds more generally, the honest shape is not a ladder but a **partial
   order with one real edge**: τ2-O depends on τ3-ish cost content; τ3
   (both cells) does not depend on τ2 (either cell); τ0/τ1 are prior to
   all of the above. This is offered as a hypothesis for the paper's own
   author to weigh, not asserted as settled by one rung's constructed
   battery.

---

## 8. What broke, what remains uncertain

1. **The TAU-C `A`/`M` cost model is a labelled proxy, not literally
   Theorems X/XI/XII.** This rung is explicit about that scoping (prereg
   §4, results §2) — a stronger version of this test would derive `A`/`M`
   from an actually-measured operational quantity (e.g. real traversal
   step counts under Γ-indexed lookup vs. raw scan, the way Theorem XI is
   stated) rather than a constructed distribution. Not built here; named
   as the natural next rung if this finding is worth tightening further.
2. **N=40's TAU-C-a result (10.5pp) sat inside the pre-registered NULL
   band; N=200 (3.8pp) does not.** Both are reported (§2) rather than only
   the more decisive one. This is a single, disclosed power increase
   (registered as permissible in the prereg's "N ≥ 30" language), not a
   search over seeds or re-rolls until a desired result appeared — but a
   third-party wanting maximal confidence should re-run at a pre-committed
   larger N with a fresh seed before treating +3.8pp as final.
3. **TAU-L-3's "decision rule" is a probe-only construct** (§3's honesty
   note) — it demonstrates that operative wiring is *constructible* and
   *distinguishable from mere representation*, not that this repo's real
   composer should be changed this way (that remains
   `GAMMA_SEARCH_COMPLETENESS_CEILING.md` §3.5's separately-scoped,
   unbuilt finding).
4. **The four-cell grid's own cross-cell ordering (§7 item 4's
   hypothesis) is not measured here** — only C-vs-L independence (§5) and,
   within L, R-vs-O dissociation (§3) are. Whether τ2-O generally needs
   τ3-shaped content, beyond this one constructed battery, is a
   recommendation for further work, not a finding.
5. **"Character ToM" (Part A) is a looser match to the paper's Γ_other
   than the MDL ladder is to bound-theorem content** — flagged in the
   prereg and repeated here; Part A is corroborating, not decisive,
   evidence for axis-orthogonality.

---

## 9. Reproduce

```
cd /home/matt/ocelot-tau-hierarchy
PYTHONPATH=".:runners/dsl/python" python3 scripts/tau_hierarchy_probe.py /tmp/tau_probe.json
```

Runtime well under a few seconds. No writes outside the given output path
(if provided) and no mutation of `seeds/`, `domains/`, `runners/`, or
`data/`. Regression: `PYTHONPATH=".:runners/dsl/python" python3 -m pytest
tests/test_transform_decode_migrated.py tests/test_dimension_inference_migrated.py -q`
(25/25 green, unaffected by this rung — no seed/domain/runner file was
modified).
