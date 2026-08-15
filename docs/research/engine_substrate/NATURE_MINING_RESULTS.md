# Nature mining (non-cognition) — results

Companion to `NATURE_MINING_PREREG.md` (read first — it registers scope and
method before any finding below existed). Scope: immune systems, stigmergy,
mycorrhizal networks, homeostasis/allostasis, morphogenesis, symbiosis —
deliberately everything EXCEPT cognition/genetics, which a same-day sibling
conversation already mined (codebook/decode = archive/execution;
wobble-position redundancy = the real `CapabilityAxis` bug a sibling agent is
fixing this session; frameshift = "in-frame is integer"; splicing =
"transform in the existing basis"; folding/chaperones =
`multi_start_settle_and_pick_best`; proofreading = gap-awareness →
self-improvement).

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/nature-mining`, branch
`nature-mining-investigation`, detached from `main` at `fff8555`.
`runners/dsl/src/shape_decode.rs` / `CapabilityAxis` identity and
`domains/solver_dispatch.py` were read for context only — not touched; both
are owned by concurrent sibling agents this session.

**Nothing was built.** Every finding below that reached "clear and evidenced"
also reached "already correctly implemented" or "requires touching a
decision surface (composer/experiment-mint generation, Γ-production
authoring) that is a substantive design change, not a narrow fix" — the house
bar this rung's brief set for a build. Per that same brief, a purely
analytical result is a complete, valid outcome, and that is what this is.

---

## 0. The one thing worth reading if you read nothing else

**The strongest hit is not a new capability — it's a working principle for a
design question this codebase has left implicit.**
`domains/solver_dispatch.py`'s own comment names three siblings of its
`_find_concepts_by_name`: `domains/neuroscience_tagging.py::
_find_concept_by_name`, `domains/reasoning_can_bridge.py::
_find_concept_by_name`, and `domains/propositional_deduction.py::
_schema_by_name`, all justified by the house comment "same pattern, own cache
— no cross-import." Read as boilerplate, that looks like copy-pastes waiting
to be DRY'd. **Read all four bodies and they have already diverged in exactly
the way gene-duplication theory (Ohno 1970; Force et al. 1999's
duplication-degeneration-complementation model) predicts adaptive duplicates
diverge, along TWO independent axes**: `neuroscience_tagging.py`'s scans every
`Concept` globally and returns the first match; `reasoning_can_bridge.py`'s is
scoped to one microtheory's `has_concept` neighbours and returns the first
match within it; `solver_dispatch.py`'s scans globally like the first but
returns **every** match as a list, explicitly so the caller can detect and
handle ambiguity (`SOLVER_ANALOGY_ADAPTER_PREREG.md` §3's ambiguity gate) —
that's scope/cardinality divergence, three variants of one function. But
`propositional_deduction.py::_schema_by_name` diverges on a different, more
fundamental axis: it is the identical one-line scan SHAPE applied to a
**different node type entirely** (`ShapeSignature`, not `Concept`) — not a
variant of the same function at all, but the same shape independently
re-derived for an unrelated purpose. Four call sites, four genuinely different
needs, one idiom wearing superficially similar names and comments. **Forcing
these into one shared implementation — the reflex a DRY-trained reviewer would
have — would be the wrong move**: it would need a scope parameter, a
cardinality parameter, and a node-type parameter bolted onto what is
otherwise a one-line function, adding exactly the kind of parameterisation
`CLAUDE.md`'s SHAPES-not-numbers rule warns against, to remove four lines that
were never actually the same function. This is not a new finding about this
codebase's correctness — it's already correct — but it is a new, checked, and
reusable **criterion**: before merging an apparent duplicate here, check
whether the copies have already spoken to different requirements (as these
four genuinely have); if they have, biology's answer
is keep them separate (paralogs under different selective pressure diverge
because divergence *is* the value), and reserve a merge for the case biology
also has a name for — obligate, universally-required, non-divergent function,
the way every human mitochondrion descends from one endosymbiotic fusion event
because there is no adaptive value in a cell running two different electron
transport chains. See §3.1 for the ranked write-up.

---

## 1. Prior-art check (`/home/matt/ozmadev/internal`)

`research/docs/graphs_paper_1_core.md` and `graphs_paper_2_implications.md`
already cite beehives (Seeley 2010), ant colonies (Bonabeau, Dorigo &
Theraulaz 1999), slime mould network optimisation (Nakagaki et al. 2000; Tero
et al. 2010), mycorrhizal flow networks (Simard et al. 1997, with Karst,
Jones & Hoeksema 2023's sceptical-review caveat carried explicitly), and the
Gaia hypothesis (Lovelock & Margulis 1974) — but **all seven citations serve
one argument**: that "artificial" presupposes a natural/engineered distinction
the graph-substrate framework doesn't carry, i.e. biological collective
systems are cited as *other instances of graph-native substrate*, to support
the trilogy's substrate-origin-agnostic claim (Clark & Chalmers 1998's parity
principle, extended). That is a claim about what counts as a graph substrate
at all — **it is not a claim about mining specific mechanism-level design
lessons for this codebase's own subsystems**, which is this rung's whole
job. `protocol-v5.13-authoring.md:738` separately cites MHC self/non-self
tagging as precedent for "labels live on the values, not in the processing
element's behaviour" (a security-classification design point, unrelated to
this rung's immune-system question about the experiment/adopt loop). No hits
anywhere in `/home/matt/ozmadev/internal` for stigmergy, pheromone, clonal
selection, artificial immune systems, allostasis, or morphogenesis/
reaction-diffusion as design terms. **Conclusion: the general "biological
collective cognition is graph-substrate-shaped" framing is prior art and is
not claimed as novel here; the specific mechanism-to-mechanism connections
below (staleness_decay ↔ allostasis, the four duplicate lookups ↔
subfunctionalization, gap dedup ↔ immune memory, frontier-guided ranking ↔
mycorrhizal resource routing) do not appear in the prior theory and are this
investigation's actual contribution.**

---

## 2. Candidates surveyed, briefly, before the ranked list

### 2.1 Homeostasis vs. allostasis — CONFIRMED, already correctly built

**Biology.** Homeostasis is negative feedback toward a fixed set-point
(thermostat: error = setpoint − observation, correct proportionally).
Allostasis (Sterling & Eyer 1988; McEwen & Wingfield 2003) is *predictive*
regulation — the system anticipates a need and adjusts *before* the error
appears, using a model, not just the instantaneous error signal. The
distinguishing test: does the correction depend only on the current error, or
also on a held prediction that is compared against what actually arrived?

**Codebase.** `seeds/seven_meta_shape_subsystems.json` already keeps these as
two DISTINCT meta-shapes, correctly differentiated, not just relabelled:
`feedback_control_subsystem` ("Homeostatic regulation... PID corrector IS
feedback control") vs. `prediction_minus_observation_subsystem`
("Anticipation-driven correction. Kalman innovation (y − Cx̂)... the L3
`drives_estimation_control` pattern's innovation-driven belief update IS
prediction minus observation"). That distinction is not just correctly
*worded* — it is correctly *used*: `seeds/staleness_decay.json` is a real,
live consumer of the `prediction_minus_observation` shape, not homeostasis.
Read the actual rule bodies: `sd_residual` computes
`residual = |caught_quanta − held_value|` — literally a prediction (the held
belief) minus an observation (what the rod actually caught); `sd_gate` then
sets `half_life = Max(hl_min, f(residual))`, i.e. **the decay/update rate
itself is gated by the prediction error**, not fixed; `sd_blend` does a
precision-weighted (Kalman-style) blend of held-vs-new using that gated rate.
This is allostasis, not homeostasis: the system doesn't correct toward a fixed
target at a fixed rate, it *anticipates* (holds a prediction) and its
responsiveness is a function of how wrong that prediction was. A pure
homeostat (fixed decay λ, correct proportionally to instantaneous error only)
would be the WRONG model here and the seed's own file description agrees:
"decay proportional to surprise decouples accumulation density from adopt
latency."

**Verdict.** Real hit, but the work is already done and already correctly
distinguished from its weaker sibling (simple feedback control). Nothing to
build. The value of checking this was ruling out "coincidence of wording" —
it is not; `sd_gate`/`sd_blend`'s actual Term bodies implement the allostatic
shape, not merely use its name.

### 2.2 Symbiosis / endosymbiosis — the "own cache, no cross-import"
convention, a merge criterion it currently lacks — see §0 and §3.1 (ranked
write-up below; this is the strongest single finding).

### 2.3 Immune systems (clonal selection, affinity maturation, memory cells)
vs. the gap-awareness → experiment-dispatch → adopt loop — MIXED

**Biology.** Clonal selection (Burnet 1959) has three separable parts: (1)
**diversity generation** — many B-cell clones exist or are hypermutated with
random variation; (2) **selection under competition** — clones are tested
against the SAME antigen in parallel and ranked by binding affinity, with
survivors clonally expanded and refined over repeated rounds (affinity
maturation); (3) **memory** — once an antigen is defeated, a long-lived memory
cell persists so the SAME antigen next time triggers instant recognition
instead of a fresh, slow primary response. "Artificial immune systems" is
already an established CS field building on exactly this (de Castro & Timmis
2002).

**Codebase, part 3 (memory) — already correctly built, independently.** The
sd-loop's whole point (`sd_recognize` before `sd_mint_quantum`) is: don't
mount a fresh response to something already in the codebook. The gap pipeline
has its own, more literal memory-cell mechanism:
`seeds/gap_awareness.json`'s content-dedup guard (`Not Exists` a `SelfConcern`
with matching content) prevents re-filing a gap already known, and
`retire_duplicate_gap` (an `Argmin`-selected survivor over same-content active
gaps, per `CLAUDE.md`'s own description) retires legacy duplicates the guard
predates. Functionally this is a memory-cell check performed BEFORE mounting
a new immune response (filing + eventually experimenting on a gap) — already
correct, independently converged, not something the biology suggests
improving.

**Codebase, parts 1-2 (diversity + parallel selection) — present as a
primitive, not yet exercised as a population.** `experiment_dispatch.py`'s
`scan_and_dispatch` iterates **every** `Experiment` node with
`status=="requested"` and spawns each as an independent, non-blocking
detached child process (`for exp in list(S.nodes("Experiment"))`) — true
concurrency IS already the dispatch mechanism's shape, not a missing
primitive. What generates candidates, though
(`reflective_faculty.py`'s `_compose_experiment_rule`), currently commits to
**one** `variation_op` per gap via a single `variation_pick` Program verdict,
chosen from a real menu of seven independently-meaningful variant families
(`acting_variant`/gradient-threshold-shift, `structural_variant`/EditOp
family — flip_comparison, swap_term_leaf, drop_match_edge, add_match_guard —
a genuinely different SHAPE not a shifted number, `reply_variant`,
`cue_variant`, `knob_variant`, `lit_variant`, `datum_variant`, `shape_variant`)
— see `reflective_faculty.py:4917-4933`. So the "gradient" word in the
standing concern's own relation vocabulary
(`["gradient", "VARIANT", "of", "ACTING"]`) already names a second,
independent variant per experiment — not a population, but not nothing
either. Full affinity maturation (many concurrently-tested variants of ONE
gap, ranked, best expanded) would require `variation_pick` to mint one
Experiment per admissible variation kind rather than Argmax-picking a single
verdict early.

**Verdict — named, not built.** If this is ever worth doing, the biology says
the right lever is NOT a population-size hyperparameter (that would be
exactly the F-16 "declare a rate, need a rate for the rate" antipattern
`CLAUDE.md` already names) — it is a Γ-shaped move: since `admissible_moves`
already returns a *set*, `variation_pick` becoming a set-valued Program
(mint one Experiment per admissible variation kind, let `scan_and_dispatch`'s
already-existing concurrency do the parallel testing, let `adopt` be a real
`Argmax` over judged winners instead of a single-track SUPPORTED check) is
architecturally consistent with what's already there. This touches the
composer's generation decision, which is a substantive design change — out of
scope for a same-session build, correctly deferred.

### 2.4 Stigmergy (pheromone deposit + evaporation) — REJECTED as a transplant,
confirmed as a process-level pattern

**Biology.** Ants deposit pheromone on a path; pheromone evaporates at a
roughly FIXED rate over time; paths used more often stay stronger because
deposit-rate beats evaporation-rate; the colony's shortest-path discovery is
an emergent property of this deposit/evaporate loop (Dorigo & Stützle 2004,
Ant Colony Optimization).

**Codebase.** `seeds/can_decay_identity.json` (CAN belief decay) and
`seeds/staleness_decay.json` (perception freshness, §2.1) are the closest
analogues, and **transplanting plain pheromone evaporation into either would
be a downgrade, not an improvement.** Plain evaporation is a fixed rate — a
scalar knob, exactly the shape `CLAUDE.md`'s SHAPES-not-numbers section warns
against. What's already built is *better* than the biological mechanism being
proposed as an upgrade: `staleness_decay.json`'s half-life is
surprise-GATED (§2.1), and `can_decay_identity.json`'s decay is deliberately a
fixed-quantum linear decrement chosen specifically to be
integrality-preserving in an in-frame integer count (the seed's own
description calls out that the naive multiplicative `(1-γ)·h` "is a category
error applied to an in-frame integer count" — precisely the frame/continuum
invariant `CLAUDE.md`'s BASE-AS-DIMENSION section states generally). Neither
of these needs an ant's evaporation constant; both already reason about WHY
their specific decay shape is correct for their frame. **This is a real,
useful null**: the biology looked promising, was checked against the actual
rule bodies, and the actual rule bodies are already doing something more
sophisticated than the biological mechanism being imported.

**A real but non-code-level parallel.** The session's own operating discipline
— concurrent background agents that don't message each other directly but
each read/modify a shared substrate (git `main`, `CLAUDE.md`'s running log,
sibling `PREREG`/`RESULTS` docs in `docs/research/`) and later agents sense
and build on those traces — IS structurally stigmergic coordination (deposit
a trace in the shared environment; a later independent agent senses it and
reacts, no direct channel). `CLAUDE.md`'s convention of leaving retracted
claims IN PLACE with a dated `RETRACTED` marker rather than silently deleting
them (e.g. the two-paragraph retraction under "Migration is COMPLETE") is the
closest thing to a decay/evaporation signal in that trail: a stale claim isn't
erased, it fades in authority while staying legible, which is closer to how a
weak, un-reinforced trail loses salience without vanishing than to a hard
delete. This is real and worth naming, but it is a description of how this
SESSION already runs, not a code change — reported for completeness per the
brief, ranked low because there is nothing to build or fix.

### 2.5 Mycorrhizal networks — split verdict: the generic "hub" framing is
weak/rejected, the specific resource-routing-under-scarcity framing is a
confirmed hit

**Biology, two separable claims.** (a) Mycorrhizal fungal networks connect
multiple trees in a graph with hub trees at high centrality (Simard et al.
1997; Beiler et al. 2010) — a pure TOPOLOGY claim. (b) Under a narrower,
contested reading, carbon is preferentially routed toward shaded/needy
seedlings, subsidised by canopy "hub" trees (the "wood-wide web"
resource-sharing claim; Karst, Jones & Hoeksema 2023 urge caution on how
broadly this generalises) — a RESOURCE ALLOCATION UNDER SCARCITY claim,
distinct from topology alone.

**Claim (a), rejected as non-additive.** `substrate/world_adapter.py`'s Agent
node genuinely is a hub — `Goal`/`Resolver` nodes JOIN through it
(`question_driver.py:558`, "Agent hub (`has_goal`)"). But hub-and-spoke graph
topology is one of the most generic patterns in computing (star topology,
pub/sub, a hash table's bucket-head) and needs no biological grounding to
justify; nothing about mycorrhizal networks *specifically* suggests anything
different from what a hub node already does here. Naming this "mycorrhizal"
adds a poetic label, nothing structural. Rejected.

**Claim (b), confirmed, already correctly built.** `domains/gap_prioritiser.py`
already implements preferential resource (attention/priority) allocation
toward the NEEDIEST location rather than the highest-raw-payoff one:
`below_frontier_penalty_term` scales a dominating penalty by DISTANCE from
the agent's live capability frontier (`level_rank − frontier_rank`), so
`guided_pick_term`'s Argmax is pulled toward the axis CLOSEST to (not
furthest below) the frontier — deliberately redirecting the loop toward the
gap nearest to being reachable, "pulling the loop as far upstream toward the
perception bottleneck as an available gap allows" (the function's own
docstring), rather than letting a high-payoff-but-far-downstream gap win by
raw score. This is structurally the same shape as a hub tree subsidising the
seedling nearest the light gradient rather than the one that would
theoretically photosynthesise the most if fully grown — allocate toward
proximity-to-viable under scarcity, not toward raw eventual payoff. Already
built, already correct; the biology confirms rather than corrects it.

### 2.6 Embryonic morphogenesis (positional information, reaction-diffusion)
— largely already-covered ground, one specific confirmed sub-claim, one
honestly under-investigated question

Positional-information (a cell reads a local morphogen concentration to infer
its position/distance from a source; Wolpert's French Flag model, 1969) maps
concretely onto `runners/dsl/src/space_quantize.rs`'s epoch-gated Bellman
flood over portals (documented in `CLAUDE.md`): a `SpaceQuantum`'s flood
value IS a local reading that encodes distance-to-source, exactly the way a
morphogen gradient encodes positional information from purely local diffusion
rules, with no cell/quantum needing global knowledge. This is a genuine,
correct, already-built convergence, but it sits directly adjacent to what
`CLAUDE.md` already documents about the flood as a local-rule-to-global-
fixpoint mechanism — low novelty on top of what's already stated.

**Left honestly open, not chased further**: Turing reaction-diffusion pattern
formation specifically requires two rate-differentiated, opposing local
processes (short-range activation, long-range inhibition) to break symmetry
and settle on a STABLE, spatially HETEROGENEOUS equilibrium from a uniform
start — a qualitatively different outcome than a single fixpoint settling to
one quiescent answer. Whether `run_rules()`'s fixpoint has, or needs, this
symmetry-breaking property anywhere (as opposed to always converging toward a
single settled answer) was not investigated deeply enough to report a verdict
either way — flagged as a real open question rather than forced into a hit or
a null it wasn't earned.

---

## 3. Ranked findings

Ranked by (consequence × confidence) ÷ cost-to-verify, `SHAPE_AUDIT.md` §8's
own method.

**3.1 (highest) The four "own cache" lookups have already speciated —
the endosymbiosis/subfunctionalization criterion (§0).**
`domains/solver_dispatch.py:319`, `domains/neuroscience_tagging.py:138`,
`domains/reasoning_can_bridge.py:106`, `domains/propositional_deduction.py:274`.
*Consequence:* this gives the codebase's own duplication convention a
checkable criterion it currently states as an absolute ("no cross-import")
without a stated exception — biology's answer (duplicate when divergence has
or will have adaptive value; merge only when the function is universally
identical and never benefits from site-specific variation, the mitochondrion
case) is a sharper, reusable test for the NEXT apparent duplicate someone
finds and is tempted to DRY away. *Confidence:* high — all four function
bodies were read directly, not inferred; the divergence (global-vs-scoped,
first-vs-all, and — the sharpest instance — Concept-vs-ShapeSignature, a
different node type entirely) is real and already serves each site's actual
need. *Cost to verify:* trivial, already done (four short reads). *Not a
build*: this is a design heuristic, correctly stated as one, not a code
change — there is nothing broken to fix.

**3.2 Allostasis is already correctly distinguished from homeostasis and
already has a real, correctly-shaped consumer (§2.1).**
`seeds/seven_meta_shape_subsystems.json` (the shape pair) +
`seeds/staleness_decay.json` (`sd_residual`/`sd_gate`/`sd_blend`, the
consumer). *Consequence:* confirms the meta-shape vocabulary isn't just
correctly worded but correctly used at a real call site — a genuine
convergent-validity check the brief specifically asked for ("check this is a
genuine hit, not a coincidence of wording"), passed. *Confidence:* high, rule
bodies read directly. *Cost:* trivial. Nothing to build — already correct.

**3.3 Immune population diversity is a real, evidenced, but substantive
design question, correctly deferred (§2.3).**
`domains/experiment_dispatch.py:442` (`scan_and_dispatch`, already
concurrency-capable) + `domains/reflective_faculty.py:4917-4933`
(`_compose_experiment_rule`, currently single-`variation_op`-per-gap).
*Consequence:* if ever pursued, names the RIGHT lever (`variation_pick`
becoming Γ-set-valued, not a population-count hyperparameter) and rules out
the WRONG one before anyone tries it — real, if modest, preventive value.
*Confidence:* medium-high on the mechanism read, lower on whether it's worth
building at all (no evidence the single-variant-per-gap loop is currently a
bottleneck anywhere). *Cost to build:* high — touches the composer's
generation decision surface, a substantive change, correctly out of this
rung's build bar. Named, not built.

**3.4 Mycorrhizal resource-allocation-under-scarcity is already correctly
built in the gap-prioritisation frontier guard (§2.5b).**
`domains/gap_prioritiser.py::below_frontier_penalty_term` /
`guided_pick_term`. *Consequence:* modest — confirms an existing, already
well-reasoned design choice rather than correcting anything.  *Confidence:*
high, function bodies read directly. *Cost:* trivial. Nothing to build.

**3.5 Stigmergic evaporation would be a downgrade if transplanted — a useful
null (§2.4).** `seeds/staleness_decay.json`, `seeds/can_decay_identity.json`.
*Consequence:* the value here is negative-but-informative: it forecloses an
"obvious-sounding" future suggestion (add ant-style pheromone decay to the CAN
belief system) before anyone spends time on it, and explains precisely why
(fixed-rate evaporation is the exact scalar-knob shape `CLAUDE.md` already
prohibits; the existing surprise-gated and integrality-preserving decay shapes
are strictly more sophisticated). *Confidence:* high. *Cost:* trivial.

**3.6 (lowest, reported for completeness per the brief) Generic hub topology
labelled "mycorrhizal" adds nothing (§2.5a); the session's own concurrent-
agent coordination is genuinely stigmergic but is a process observation, not
a code finding (§2.4).** Both correctly named as weak/non-actionable rather
than omitted, consistent with the brief's instruction to report rejected
parallels with the same weight as hits.

---

## 4. Honestly rejected / weak parallels (same weight as the hits, per the
brief and per `CLAUDE.md`'s own stated epistemics)

- **Ant-pheromone evaporation → CAN/staleness decay.** REJECTED — see §2.4 and
  §3.5. The existing mechanisms are already more sophisticated than the
  biological mechanism proposed as an upgrade; transplanting it would be a
  regression to a scalar knob.
- **Mycorrhizal hub topology → the Agent hub node.** REJECTED as non-additive
  — see §2.5a. Hub-and-spoke is generic; nothing mycorrhizal-specific
  transfers beyond the label.
- **Reaction-diffusion symmetry-breaking → `run_rules()`'s fixpoint.** NOT
  RESOLVED, reported as an open question rather than forced to a verdict —
  see §2.6. This is different from a rejection: it is an honest "did not
  investigate deeply enough to claim either outcome," flagged rather than
  silently dropped or padded into a false hit.
- **Immune population diversity as something currently missing.** PARTIALLY
  REJECTED on inspection — the concurrency PRIMITIVE (`scan_and_dispatch`)
  already exists; only the candidate-generation step commits early to one
  variant. The naive version of this finding ("the agent should test a
  population of hypotheses, it doesn't") would have been wrong; the accurate
  version is narrower (§3.3) and was reached only by reading
  `_compose_experiment_rule` rather than stopping at the dispatch loop.

## 5. What this does not establish

- It does not establish that any of §3's confirmed-correct mechanisms were
  ORIGINALLY DESIGNED with the biological analogy in mind — only that the
  analogy holds up when checked against the real rule bodies, which is a
  weaker and more honest claim (convergent design, not borrowed design).
- It does not establish that §3.3's Γ-set-valued `variation_pick` proposal is
  worth building — only that IF it is ever built, the biology points at the
  architecturally-consistent lever and away from a scalar-knob one. No
  evidence was gathered that the current single-variant-per-gap loop is
  actually a bottleneck anywhere in practice.
- It does not establish that §0/§3.1's duplication criterion generalises to
  every "own cache, no cross-import" site in the tree — only that the four
  sites `solver_dispatch.py`'s own comment names (and that were actually read,
  not inferred) diverge in exactly the predicted way. `reflective_faculty.py`
  and `analogical_thinking.py`'s own `_vocabulary_keys`/`_relation_cue_index`
  pair (§2.2/§0's opening citation of the convention itself) was read only far
  enough to confirm the convention's directional asymmetry (one imports FROM
  the other; the other imports nothing back) — not deeply enough to confirm
  whether ITS two caches have similarly diverged in content, so that pair is
  cited as the convention's origin, not folded into the four-way divergence
  count. A full sweep of every "own cache" site in the tree was out of scope
  for this rung.
- It does not establish that the rejected parallels (§4) are impossible to
  make work with enough engineering — only that the STRAIGHTFORWARD
  transplant is a downgrade or a non-addition given what already exists, which
  is the honest, checked answer to "does the biological version suggest
  something concretely different or better," not a claim that no version of
  the idea could ever help.

## 6. Build status

Nothing was built. Every candidate that reached "real and evidenced" also
reached either "already correctly implemented" (§2.1/§3.2, §2.5b/§3.4) or
"a design heuristic worth stating, not a code change" (§0/§3.1) or "touches a
generation/decision surface that is a substantive redesign, correctly named
and deferred rather than forced into a same-session build" (§2.3/§3.3). Per
this rung's own PREREG build bar and the orchestrator's explicit instruction
not to force a build to look productive, a purely analytical result is the
correct and complete outcome here.

Confirmed: no merge or push to `main` was performed. This document and its
companion PREREG are committed on the isolated worktree branch
`nature-mining-investigation` for the orchestrator to review and merge.
