# Belief quantization via Causal Attitude Networks — RESULTS

Prereg: `CAN_BELIEF_QUANTIZATION_PREREG.md`, same worktree/branch, base
`main @ 0e18038`. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-belief-quantization`, branch
`can-belief-quantization`.

**Verdict, up front:** the primary N×M scaling prediction as literally
registered (coarse basin count declining faster than fine's as N grows) is
**NOT confirmed — the measured direction is closer to reversed** on this
operationalisation, a genuine and informative null, reported precisely
rather than reinterpreted. What IS confirmed, cleanly: (a) coarse
quantization produces measurably larger per-edge representational error at
every N (the manipulation check); (b) the `CAN_ops` machinery is real,
compiled, PyO3-exposed and behaves exactly as its own source documents; (c)
**CAN's own relaxation dynamics genuinely exhibit a real cohere-vs-fail-
to-cohere binary (a persistent 2-cycle oscillation vs. clean convergence,
confirmed with a same-parity control) — the "honest discriminative null"
shape already present in this substrate elsewhere (sd loop, `check_edge`,
gap-awareness) turns out to already exist, unexploited, in CAN's own math —
but whether LOW RESOLUTION SPECIFICALLY drives that failure, as opposed to
the specific realised coupling draw, is only a weak, noisy, same-direction
lean across two independent samples (24 and 40 trials), not a confirmed
effect**; (d) the 15 rules were inert for a **deeper** reason than missing
`match` clauses — there is no DSL Term surface for the dynamics at all,
only a Python/PyO3 boundary; (e) one rule
(`curiosity_targets_ambivalent_nodes`) was wired with real, tested,
production-path-verified `match`/`where`/`effects`, using only the
existing Term vocabulary; (f) the `epistemic_default.json` → CAN `h_i`
connection is real but requires new design work, not a trivial reuse, and
is named precisely rather than built; (g) on the "arbitrary solver"
requirement, nuanced weighting alone is confirmed **necessary but
insufficient** — the missing tractability half is shape-recognition/
compression over the coupling structure, for which this exact codebase
already has a measured, real precedent this session
(`BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`: 7970 pairwise comparisons → 139
distinct patterns, 98.3% reuse) — named as the concrete next build, not
built here.

---

## 1. Literature — what was checked, and what held up

The creator's correction retargets from idealized single-edge causal-
strength estimation (Pearl/Cheng/Rescorla-Wagner/mental-models, already
covered by `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`) to: **how does a
belief-holding mechanism, under messy/adversarial/degraded real-world
input, mechanically produce coarse, low-nuance belief?** Five sources were
named in the brief; all five were independently checked via WebSearch
(and one via WebFetch), not taken on the prompt's word.

1. **Sperber, Clément, Heintz, Mascaro, Mercier, Origgi & Wilson, "Epistemic
   Vigilance," *Mind & Language* 25(4), 359-393, 2010.** **Confirmed real**
   — consistent bibliographic details (volume/issue/pages/DOI
   `10.1111/j.1468-0017.2010.01394.x`) across CEU Research Portal, PhilPapers,
   UCL Discovery, Wiley, and the author's own site (`dan.sperber.fr`), which
   also hosts the full PDF. **Content**: the paper argues humans depend
   heavily on communication and are thereby exposed to
   accidental/intentional misinformation, and proposes a *suite* of
   cognitive mechanisms for evaluating trust in communicated content
   (source-trust evaluation, content plausibility-checking, coherence with
   existing belief) — this is a strong, direct match for "how do people
   evaluate messy/adversarial testimony," the corrected target. **A direct
   WebFetch of the full PDF failed** (binary/font-stream content, not
   text-extractable by the fetch tool) — the mechanism list itself is
   therefore reported at abstract/description grain, not verified against
   primary full-text, and this is flagged rather than smoothed over. Still
   the single most directly on-target citation of the five.
2. **Johnson, Hashtroudi & Lindsay, "Source Monitoring," *Psychological
   Bulletin* 114, 3-28, 1993.** **Confirmed real** — DOI
   `10.1037/0033-2909.114.1.3`, consistent across SciRP, ResearchGate, PubMed
   (8346328), and a full PDF hosted at Yale's Memory Lab. Content: a
   framework for how people attribute a memory/belief to its SOURCE
   (perceived vs. imagined vs. told-by-X), and how source attribution can
   fail (confabulation, cryptomnesia, incorporating fiction as fact) —
   directly relevant to "lies-to-children blending with partial
   understanding," though the paper itself is about memory-source
   attribution specifically, not testimony evaluation generally; the
   connection to the creator's "mechanism" framing is real but one step
   removed (source-monitoring failure is a plausible SUBSTRATE for why a
   simplification and a truth can blend into one held belief without the
   holder detecting the seam — not a paper that itself models belief
   coarseness).
3. **Hasher, Goldstein & Toppino, "Frequency and the Conference of
   Referential Validity," *Journal of Verbal Learning and Verbal Behavior*
   16(1), 1977.** **Confirmed real** — this is the illusory-truth-effect
   origin paper, consistently described across ScienceDirect, Wikipedia,
   Semantic Scholar, and a 2021 replication/extension paper. Finding:
   repeated exposure increases perceived truth of a statement independent
   of the statement's actual truth or the source's quality — directly
   on-point for "repetition, not evidence quality, moves belief," a
   mechanism that degrades nuance without requiring any new information.
4. **Pennycook & Rand, several papers (2018 "Lazy, not biased"; 2020 "Who
   falls for fake news? The roles of bullshit receptivity, overclaiming,
   familiarity, and analytic thinking").** **Confirmed real** — both papers
   independently located (SSRN/ScienceDirect/MIT DSpace for the first,
   *Journal of Personality* for the second). Finding: susceptibility to
   fake news correlates with LOWER analytic/reflective thinking
   (Cognitive Reflection Test score), independent of the story's political
   alignment — "lazy," not "motivated," reasoning is the better predictor.
   This is the most directly quantitative support in the set for "lower
   [something like metacognitive capacity] correlates with reduced
   discrimination between plausible and implausible claims" — though CRT
   measures reflective override of an intuitive response, not network
   resolution/nuance directly; the mapping from CRT to "quantization" is
   this document's own inference, not the papers' own claim.
5. **Vosniadou (& Brewer), synthetic mental models, esp. "Mental models and
   other misconceptions in children's understanding of the earth"
   (*Cognitive Development*, 2008) and "Reframing the Classical Approach to
   Conceptual Change: Preconceptions, Misconceptions and Synthetic Models."**
   **Confirmed real** — consistent across ScienceDirect, PubMed, Springer,
   ResearchGate. This is the single BEST-matching citation for the
   creator's own "lies-to-children" framing, verified precisely: Vosniadou's
   "synthetic model" is explicitly a child's naive prior belief (flat earth)
   BLENDED with a partially-absorbed taught fact (the earth is round) into
   an internally hybrid model (hollow earth, dual earth) — not a clean
   replacement of the naive belief by the correct one, and not a rejection
   of the taught fact either. This is a real, well-evidenced, precisely-named
   mechanism for exactly the "lies-to-children plus partial understanding
   produces an internally-inconsistent hybrid, not a clean update" phenomenon
   the creator named.

**Honest summary**: all five hold up as real, correctly-attributed
citations. None of them is itself a theory of NETWORK quantization/
resolution — that mapping (belief-network resolution ↔ nuance-holding
capacity) is this project's own hypothesis, not lifted from any of the five
papers, exactly as `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §3.3 already found
for the earlier single-edge framing ("neither literature hands this project
a ready-made... answer"). The five together substantiate the CORRECTED
TARGET (messy/adversarial testimony processing, not clean-evidence causal
inference) far better than the prior research's citation set did — this is
a genuine improvement in what's being modeled, independent of whether the
network-quantization mechanism itself is confirmed below.

---

## 2. Does CAN's basin/frustration structure formalise "quantization of
belief"? — read from source, precisely

**`can_ops.rs::audit_basin` (`:400-436`) does NOT count or enumerate
basins.** Read directly, confirmed empirically
(`test_mt_audit_basin_reports_single_fixed_point_not_multiplicity`, this
rung): `audit_basin` calls `mt_mean_field_marginal` exactly once, from
whatever is currently written to each Concept's `state` attr
(`can_ops.rs:195-254`), and reports that ONE fixed point's energy,
coverage, and frustration. It has no `basin_count` field and no mechanism
for discovering a second fixed point. The live test built a genuinely
bistable 2-node network (strong positive coupling, no field — the textbook
symmetric-double-well case) and showed the SAME `mt_audit_basin` call
returns a DIFFERENT report depending only on what `state` happened to be on
the graph beforehand (`marg_plus[a] > 0.5` from one start, `marg_minus[a] <
-0.5` from the other) — i.e. `audit_basin`'s single call samples ONE point
in a landscape that can genuinely hold more than one.

**So "how many discriminable belief-states can this network hold" is not
a field `audit_basin` returns — it is a property of the landscape that must
be discovered by the CALLER, via multi-start** (repeatedly re-seeding
`state` and re-relaxing, clustering the results) exactly as §3 below does.
This is a precise, load-bearing correction to a plausible-sounding but
wrong reading of the existing code ("audit_basin reports basin structure")
— it reports ONE basin's diagnostics, honestly and correctly, and nothing
about multiplicity.

Is "number of distinct mean-field fixed points found under multi-start" a
DEFENSIBLE operationalisation of "how many discriminable nuanced
belief-states an agent can hold"? **Partially, and the live data in §3
below shows precisely where the operationalisation breaks down**: raw
fixed-point count is confounded with FRUSTRATION-driven landscape
ruggedness (many shallow, near-degenerate local minima from unsatisfiable
constraints), which is a different phenomenon from "genuinely distinct,
well-separated, meaningful belief configurations." §3's added
`dominant_basin_fraction`/`effective_basin_count` metrics are this
document's own attempt to disentangle the two, not something `can_ops.rs`
itself provides.

---

## 3. Live demonstration — the 2×3 factorial, real numbers

Full design in the PREREG (§2.2): complete graphs at N ∈ {4, 8, 16},
COARSE (`J ∈ {-1,0,+1}`, 3 values) vs. FINE (`J ∈ {-1,-0.75,...,+1}`, 9
values, same magnitude range), same underlying "true" i.i.d.
`Uniform(-1,1)` draw per N rounded into each vocabulary, β=2.0, h=0, 40
random-restart mean-field relaxations per cell, real
`mt_mean_field_marginal`/`mt_frustration_given_state`/`mt_energy` calls
(`tests/test_can_belief_quantization.py::test_print_full_factorial_table`,
reproducible via `python3 -m pytest tests/test_can_belief_quantization.py -s`).

```
N      coarse?   vocab  coupling#  round_err  basin_count  eff_basin  dom_frac   frustr     energy
4      coarse    3      6          0.2154     6            5.509      0.300      2.0963     0.0963
4      fine      9      6          0.0710     4            3.847      0.375      1.5467     -0.9533
8      coarse    3      28         0.1756     15           11.553     0.175      15.3154    5.3154
8      fine      9      28         0.0670     4            3.809      0.300      11.0591    1.3091
16     coarse    3      120        0.2219     28           25.375     0.075      65.6279    3.6279
16     fine      9      120        0.0664     29           26.615     0.075      68.5997    3.8497
```

**Manipulation check confirmed cleanly**: coarse's mean absolute rounding
error is 2.5-3× fine's at every N (0.215/0.176/0.222 vs. 0.071/0.067/0.066)
— the two vocabularies are correctly built and genuinely differ in
resolution, isolating the variable under test.

**The primary registered prediction is NOT confirmed — reversed at N=4
and N=8.** Coarse shows MORE distinct basins (6 vs 4 at N=4; 15 vs 4 at
N=8), a HIGHER effective (entropy-weighted) basin count, and a LOWER
dominant-basin fraction (0.30/0.175 vs 0.375/0.30) than fine at those two
sizes — the opposite of "coarse → fewer discriminable states." Coarse also
shows HIGHER mean frustration at N=4/8 (2.10 vs 1.55; 15.32 vs 11.06),
consistent with the rounding error accumulating into real constraint
stress, but that stress manifests as a MORE fragmented landscape (more,
shallower local minima), not a flatter one.

**At N=16 the two conditions converge to near-parity** on every measure
(28 vs 29 raw basins, 25.4 vs 26.6 effective, 0.075 vs 0.075 dominant
fraction, 65.6 vs 68.6 frustration) — exactly the ceiling/floor confound
the PREREG registered in advance (§2.3, point 4) as a specific failure mode
to watch for: a complete graph of 120 near-randomly-signed couplings at
β=2.0 is dense/frustrated enough that BOTH vocabularies saturate into a
similarly rugged landscape regardless of resolution — resolution stops
being the binding constraint once density/frustration dominates.

**Mechanistic account, offered honestly as an account of the DATA, not a
retroactive rescue of the prediction**: for a complete graph with
near-random-sign true couplings, coarser rounding pushes more edges toward
the SAME few values ({-1,0,+1} rather than 9 finer options), which for a
frustrated (spin-glass-like) system does not average out contradictions
into fewer, cleaner attractors — it creates MORE ties and near-ties between
otherwise-similar edges, which is exactly the classic Sherrington-
Kirkpatrick spin-glass signature of a MORE rugged energy landscape (more
numerous, shallower, closely-spaced local minima), not a smoother one. The
naive intuition "fewer bins → fewer states" holds for a SINGLE variable's
perceptual quantization; it does not transfer cleanly to a COUPLED
network's attractor structure, where reduced resolution on the edges acts
more like added noise/frustration than like added blur. This is itself a
useful, precise, mechanistically-grounded negative finding about where the
"quantization = coarseness = fewer options" intuition breaks down as an
analogy.

**A genuinely interesting connection the data DOES support, worth naming
precisely**: coarse's landscape is not just "more populated," it is LESS
CONCENTRATED (lower `dominant_basin_fraction`) at every N where the two
conditions differ at all — meaning a coarse-weighted network, if perturbed
or re-initialized (e.g. by new evidence, or normal thermal noise), is LESS
likely to land back in the SAME basin it was just in, and MORE likely to
land in one of many similarly-shallow alternatives. This is a real match
for `seeds/causal_attitude_networks.json`'s OWN already-held concept
`predicate_churn_is_bistable_thermal_flipping` (`:426-430`: "network is
bistable + temperature too high... resolution: more evidence OR more
attention") — not "coarse belief locks onto one wrong answer and stays
there" (the moon-landing framing), but "coarse belief is UNSTABLE, easily
knocked between many similarly-arbitrary-feeling positions," which is a
DIFFERENT, equally real, and arguably complementary mechanical account of
low-nuance reasoning (a person with a coarse model doesn't necessarily hold
one fixed wrong belief forever — they may flip between several
equally-unfounded positions depending on whatever pushed them last,
consistent with the volatility often observed in low-information political
attitudes in the actual CAN literature, e.g. Converse's classic
"non-attitudes" finding, not independently verified here but consonant with
Dalege et al.'s own framing of low-connectivity attitudes as WEAK, not
merely wrong).

**Registered honest null, exactly as the PREREG's own §2.3 pre-committed
to reporting**: the primary N×M "coarse degrades faster" prediction, AS
LITERALLY STATED (fewer/shallower basins for coarse as N grows), is not
what this design measured — the data moved in the opposite direction at
small-to-medium N and converged at large N. This is reported as a clean
negative finding per the PREREG's own registered clause 3, not
reinterpreted charitably into a disguised confirmation.

**What this design does NOT establish (named honestly, not smoothed
over):**
1. **The random-sign, zero-field, complete-graph design may not be the
   right analogue of real messy testimony.** Real testimony likely has
   STRUCTURE — correlated clusters of mutually-consistent claims plus a
   smaller admixture of genuinely conflicting evidence — not i.i.d. random
   sign on every pair. A structured-truth design (e.g. planted
   community structure, or a "coherent core + adversarial noise" draw)
   is a different, more targeted experiment this rung did not run, and
   is the most promising next step if this specific hypothesis is pursued
   further.
2. **β and graph density were held fixed at values chosen for measurability
   (β=2.0, complete graph), not derived from any theory of what a real
   belief-network's density/attention level should be.** The N=16 ceiling
   effect shows the result is sensitive to this choice; a sparser graph or
   lower β might not saturate at N=16, and was not tried within this
   rung's scope.
3. **"Effective basin count" and "dominant basin fraction," this document's
   own added metrics, are a reasonable but NOT independently validated
   operationalisation of "room to hold a nuanced alternative."** They were
   constructed specifically to disambiguate frustration-ruggedness from
   genuine multi-stability within this rung; they are not drawn from the
   CAN literature itself.

---

### 3.1 A further sharpening — flattening bins as a controllable "lower causal
capacity" knob, and whether under-resolution produces genuine ABANDONMENT

A late addition to the brief reframed part of the live demonstration: rather
than only comparing two fixed conditions, dial resolution down
parametrically on the SAME network and ask whether under-resolution causes
a clean FAILURE TO COHERE (the mean-field relaxation never settles — a
persistent oscillation or unresolved high frustration) rather than a
smooth degrade-to-a-worse-but-stable answer — explicitly framed as
potentially the SAME shape as the sd loop's honest discriminative null
(recognize/mint with no forced bad match), `check_edge`'s clean
`Type1NoProduction` rejection, and the gap-awareness honest floor.

**First finding — a design degeneracy, reported honestly rather than
silently patched away.** The first version of this experiment started every
relaxation from `state=0` with `external_field=0` on every node (isolating
pure coupling-driven dynamics, following §2.2's own design). Every single
condition converged trivially with energy = 0.0 and gap = 0.0, REGARDLESS
of resolution. Reading `can_ops.rs:226-251`'s update rule explains why:
`tanh(β · 0) = 0` exactly, for ANY `J` — the all-zero state is an EXACT
fixed point of the deterministic mean-field map regardless of coupling
structure, and this solver has no stochastic kick to escape an unstable
saddle the way a real thermal system would. **This is itself a small,
precise, useful finding**: a deterministic mean-field relaxation started
from the perfectly symmetric point carries no information about coherence
at all when h=0 — the experiment needs either a nonzero field (evidence
pressure) or a nonzero/randomised start to be observable. Fixed by adding a
FIXED nonzero `external_field` per node (drawn once per network, held
identical across all resolution conditions for that draw — "the evidence
pressure the thought is trying to reconcile"), matching CAN's own
Hamiltonian (both `J` and `h` terms) rather than isolating `J` alone.

**Second finding — the real engine DOES exhibit a genuine, mechanically
real cohere-vs-fail-to-cohere binary, unprompted, already present in
`can_ops.rs`'s existing code, not something built for this rung.**
`mt_mean_field_marginal`'s update rule is SYNCHRONOUS/Jacobi-style — every
node's new value is computed from the PREVIOUS full state, all at once
(`can_ops.rs:226-251`, confirmed by direct read) — the textbook setup for a
persistent 2-cycle limit oscillation on a sufficiently frustrated coupled
system. Confirmed directly and specifically, not merely inferred from
non-convergence: for a genuinely oscillating network, `max_iter=400` vs.
`max_iter=402` (SAME phase parity) return IDENTICAL marginals (gap <
0.001), while `max_iter=400` vs. `max_iter=401` (OPPOSITE parity) return
marginals differing by a large, real L2 gap (typically 3-6 in an 8-16
dimensional σ-space bounded in [-1,1] per axis) — a TRUE persistent 2-cycle,
not merely slow convergence
(`test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature`, gated
on both the oscillation AND the same-parity control). **This is real,
existing, load-bearing evidence for exactly the "honest discriminative
null" SHAPE named in the brief — CAN's own relaxation dynamics can and do
genuinely FAIL to settle on a real network, rather than always returning
SOME degraded-but-stable answer regardless of how hard the constraints are
to reconcile.** This emerges directly from the underlying Ising/spin-glass
mathematics (a known, general property of synchronous updates on frustrated
systems), not from any special-cased engineering added for this purpose —
the mechanism was already sitting in `can_ops.rs`, unexploited.

**Third finding — but resolution/coarseness does NOT reliably predict
WHICH SIDE of that boundary a given network lands on, at the sample sizes
tested.** Two independent measurements, both real engine calls, reported
honestly rather than only the more dramatic one:

- A single hand-picked draw (N=8, the same seed used throughout §3) showed
  a striking, clean reversal of the naive prediction: FINE (17-value)
  resolution oscillated (persistent 2-cycle, parity gap 5.62) while COARSE
  (3-value) resolution converged cleanly (parity gap 0.0, frustration
  dropped from ~21 to ~4, energy went from positive/unstable (+11) to
  negative/stable (-8.66)) — the opposite of "coarse fails to cohere."
  Checking the confound directly: average `|J|` was nearly IDENTICAL
  between the two conditions on this draw (0.433 fine vs. 0.393 coarse) —
  ruling out "coarse just has weaker coupling overall" as the explanation.
- **A broader, pre-committed sweep** (`test_flatten_resolution_sweep_
  reports_cohere_or_abandon`, 4 network sizes × 3 seeds × {fine, coarse} =
  24 real relaxation-pair trials) found the SAME single-draw pattern does
  NOT generalise cleanly: **fine oscillated in 6/12 draws (50%); coarse
  oscillated in 8/12 draws (66.7%)** — this time leaning (mildly) in the
  creator's predicted direction (coarse fails to cohere MORE often), but on
  a small, non-power-analysed sample where a single flipped trial changes
  the rate by 8 points. A larger exploratory sweep run during this rung
  (40 trials, 4 sizes × 5 seeds, not committed as a test but reproducible
  from the same code) found fine oscillating 10/20 (50%) and coarse 11/20
  (55%) — a smaller lean in the SAME direction, still well within noise for
  this sample size.

**Honest verdict on this specific sub-question**: the EXISTENCE of a real
cohere-vs-abandon binary in CAN's relaxation dynamics is confirmed,
directly, mechanistically, and precisely — this is a genuine, positive,
somewhat unexpected finding (the mechanism the creator described by analogy
already exists in the engine's own math, unbuilt for this purpose). Whether
LOWER RESOLUTION SPECIFICALLY drives a network toward the failing side more
often is, across two independent samples (24 and 40 trials), a WEAK,
same-direction, but small and noisy lean (coarse oscillates somewhat more
often than fine in both samples: 66.7%>50% and 55%>50%) — suggestive of the
predicted direction, not yet a confirmed effect at any rigorous statistical
threshold, and the single most dramatic individual example (the N=8 hand-
picked draw) happened to run OPPOSITE to the aggregate lean. **Reported
honestly as: real phenomenon, plausible weak directional lean consistent
with the prediction, not yet statistically established — the same "power
the gate before declaring a result" standing rule this session has applied
elsewhere applies here too.** What is NOT in question, and is the more
durable finding of this sub-experiment: whether a given real belief network
under real evidence pressure can genuinely fail to resolve into any stable
configuration is a real, mechanically-grounded, already-present property of
this substrate's own math — the honest-null shape this project already
relies on elsewhere (sd loop recognize/mint, `check_edge`'s
`Type1NoProduction`, the gap-awareness honest floor) is not absent from
CAN's dynamics; it was simply never named or exploited there before this
rung looked for it.

---

## 4. Diagnostic — why the 15 rules were inert (file:line)

Confirmed, precisely, in TWO layers — the second layer is deeper than what
the charter's framing anticipated ("missing match clauses on an otherwise-
complete design" vs. "missing pieces"):

**Layer 1 — structural, confirmed by direct read.** Every one of the 15
rule objects in `seeds/causal_attitude_networks.json`'s `"rules"` array
(`:575` onward, e.g. `curiosity_targets_ambivalent_nodes` originally at
`:721` pre-edit) carried ONLY `name`/`if`/`then`/`why`/`soundness_category`
— no `match`, `where`, or `effects` key AT ALL, not merely `match: null`.
`substrate/seed_loader.py::declarative_principles` (`:31-35`) is the exact,
already-existing mechanism that recognises this shape: *"a rule with `match
not in r` and one of the declarative keys (if/then/why/head/body)"* — every
one of the 15 matched this definition precisely.
`substrate/seed_loader.py::engine_rules_only` (`:38-53`), called by
`substrate/boot_all.py::load_all_seeds` (`:418`,
`agent.inner.load_seed_manifest(d_engine, agent.agent)`) for every seed at
real agent boot, therefore FILTERS ALL 15 OUT before the seed's rules ever
reach the Rust engine's `parse_rule_json`/`add_rule` path
(`runners/dsl/src/py.rs::load_seed_manifest`, rules handling `:1576-1631`,
`inner.add_rule(rule)` at `:1630`). This is not a bug or an oversight in the
loader — `engine_rules_only`'s own docstring states this is BY DESIGN, so
declarative-only "encyclopedia prose" rules never warn on a missing `match`
array. The 15 rules were, correctly, never even attempted as engine rules.

**Layer 2 — deeper, and the more important finding.** Even if ALL 15 rules
were given real `match`/`where`/`effects` clauses, most of them could not
actually DO anything, because **the CAN dynamics themselves have no DSL
Term surface at all.** Confirmed by direct grep across the whole `runners/
dsl/src/` tree: `can_ops` is referenced in exactly two places —
`lib.rs:267` (`pub mod can_ops;`, the module declaration) and `py.rs`
(the ~20 PyO3 bindings, `:2245-2622` plus a handful of earlier/later ones).
**There is no `TermNode::Mt*` variant, and no dispatch arm in `term.rs`'s
`evaluate()`, that calls `mt_mean_field_marginal`, `hebbian_update_J`,
`decay_J`/`decay_h`, `relax_to_marginal`, or `apply_evidence_h`.** (The one
surface-level hit that looked promising, `net_forward.rs:226`'s comment
*"the WeightTensor twin of `can_ops::hebbian_update_J`"*, is a DOC-COMMENT
ANALOGY to a completely separate mechanism — `NetForward`'s own
`net_collapse_step` operates on `WeightTensor`/`NetworkAssemblage` nodes for
an authored neural net, not on `Concept`/`causal_influence` at all; it
shares no code path with `can_ops.rs`.) This means: **a Rule's `effects`
clause, evaluated inside `run_rules()`'s fixpoint, literally cannot invoke
mean-field relaxation, Hebbian learning, or field decay today** — those
operations exist ONLY as direct PyO3 method calls from Python
(`substrate.mt_relax_to_marginal(mt)`, `substrate.mt_hebbian_update_J(mt)`,
etc.), a boundary parallel to, and never crossed by, the rule engine's own
fixpoint.

**Consequence for what could honestly be wired in this rung.** Of the 15
rules, most (`Hebbian_learning_updates_J`,
`evidence_changes_field_then_relaxation`,
`ambivalence_is_frustration_not_indecision`, `attention_increases_
polarisation`, `babble_loop_is_thermal_sampling`, and others) describe the
UPDATE/RELAX half of the model — genuinely unreachable from a Rule's
effects without either (a) a new DSL Term wrapping the relevant `can_ops`
call (explicitly out of scope for this rung per the charter), or (b) a
Python write-back convention (Python calls the PyO3 dynamics function, then
writes the RESULT onto the graph as a plain attr, which a rule could then
read) — itself a real design decision this rung did not adopt unilaterally,
named in §6 below rather than built. **Exactly one rule,
`curiosity_targets_ambivalent_nodes`, describes the RECOGNIZE half** — it
only needs to READ an already-computed `state` attr and classify it, which
is squarely inside the existing Term vocabulary (`Attr`/`Abs`/`Lt`/`Not`/
`Eq`) with no new Rust and no write-back convention required. This is the
rule wired in §5.

---

## 5. What was built — one rule, wired and tested three ways

`seeds/causal_attitude_networks.json`'s `curiosity_targets_ambivalent_nodes`
(now `:721` region) gained real `match_type: "Concept"`, `match: [["mt",
"has_concept", "c"]]`, a `where` clause (`Abs(Attr(c,"state")) < 0.05 AND
NOT already flagged`), and `effects: [["set_attr", "c", "is_ambivalent",
1]]` — using only Term kinds already in the vocabulary
(`Attr`/`Abs`/`Lt`/`Not`/`Eq`/`And`, all confirmed present in `term.rs` by
direct grep before writing the rule). Seed version bumped `0.1.0 →
0.2.0`. The original `if`/`then`/`why`/`soundness_category` documentation
fields are UNCHANGED, so the rule still materialises correctly as a
documentation `Rule` node via the older `load_one_seed` path
(`test_causal_attitude_networks.py`, still 100% green, unmodified) — the
edit is additive on top of the existing dual-purpose shape every other
rule in the corpus already uses.

**Tested four ways** (`tests/test_can_belief_quantization.py`, 9/9 passing):
1. Direct `import_rules` + `run_rules`: correctly flags a near-zero-state
   Concept, correctly does NOT flag committed (`|state|>0.5`) Concepts, and
   correctly flags a Concept with NO `state` attr at all (the DSL `Attr`
   term's documented `Value::None` fallback makes this behave exactly like
   the project's own "Unknown = zero vector" convention — confirmed, not
   assumed, by reading `term.rs:4677-4696`'s `Attr` evaluator and
   `term.rs:6972-6985`'s `Abs` evaluator before relying on it).
2. Idempotence under repeated `run_rules` calls (no duplication, no error).
3. **End-to-end with the REAL engine dynamics**: a genuinely frustrated
   all-negative triangle is relaxed via the real `mt_relax_to_marginal`
   PyO3 call (not hand-set test fixtures), and the rule correctly
   recognises the resulting near-zero commitment.
4. **The real production boot path**: `substrate.seed_loader.
   engine_rules_only` + `Substrate.load_seed_manifest` — the EXACT call
   `substrate/boot_all.py::load_all_seeds` makes for every seed at real
   agent boot (`:418`) — confirms the wired rule survives the declarative-
   principle filter (because it now carries a real `match`, unlike its 14
   siblings, which remain correctly excluded — `engine_rules_only` returns
   exactly 1 rule from the 15, confirmed by assertion) and installs as a
   genuinely live, firing engine rule, not merely something that happens
   to work under a hand-rolled test harness.

**Full boot regression, before vs. after, real numbers**: `load_all_seeds`
on a fresh `WorldAdapter`, both on unmodified `main @ 0e18038` and on this
branch — **identical 8 pre-existing failures both times** (`acoustic_cue_
vocab`, `character_tom`, `reading_constructions`, `conceptual_categories`,
`cue_investigator`, `named_compound_heads`, `reading_skeleton`,
`vision_change`, all `ValueError: seed node missing local_id` — a
pre-existing, unrelated `"nodes"`-schema issue in other seeds, confirmed
present identically on unmodified main run from this same worktree
environment), **zero `rules_skipped`** in either run. (The raw `total`/
`loaded` seed COUNTS differ by exactly 1 between the two runs — traced to
one extra gitignored, untracked `seeds/grounded_lexicon.json` present in
the main working tree's filesystem but absent from the freshly-checked-out
worktree, confirmed via `git status`/`diff` of the seed directory listing,
NOT caused by this rung's edit.)

**Targeted regression**: `tests/test_can_ops.py` (12/12),
`tests/test_causal_attitude_networks.py` (13/13, unmodified),
`tests/test_can_migration.py`, `tests/test_can_belief_quantization.py`
(9/9, new) — 40/40 passed together.

---

## 6. `epistemic_default.json` → CAN `h_i` — assessed, not built

**`epistemic_default.json` is real data and IS wired — via
`domains/actor_goals.py`, not its own (empty, by design) `rules` array.**
Confirmed by reading the file's `description` (which states the rule is
"agent-authored, NOT shipped") and `domains/actor_goals.py`'s real
machinery: `ensure_epistemic_evidence_rule` (classify-by-join authoring),
`ensure_structural_forcing_rules` (the `ForcedChoiceProbe` ⨝
`ForcedChoiceExpectation` join, `:1307+`), `ensure_class_baseline_apply_
rule` (the `ClassBaseline` sum, `:1428-1439`), and
`ensure_epistemic_combine_rule` + `assess_epistemic_lean` (`:1526-1653`) —
a genuinely live pipeline producing `EpistemicLeanReading` nodes with
`verdict` (deception/opacity/undetermined), `interval_low`/`interval_high`,
`residual_other_mass` (always > 0 — never certainty, by design), and a
`basis` (which signals fired).

**The connection to `apply_evidence_h` is real but not a trivial reuse —
assessed honestly rather than forced.** `apply_evidence_h(concept_id,
evidence, alpha)` (`can_ops.rs:834-843`) needs exactly two things a lean
reading COULD plausibly supply: a signed `evidence` magnitude and a
reliability `alpha`. The mapping is NOT mechanical for two separable
reasons:

1. **No existing edge connects an `EpistemicLeanReading`/
   `ForcedChoiceProbe` to any `Concept` node.** The epistemic pipeline
   reasons about ACTORS and their TESTIMONY (`ForcedChoiceProbe{actor,
   object}`), never about a `Concept` representing the CONTENT of the claim
   being evaluated. Before `apply_evidence_h` can be called at all, some
   new wiring has to answer "which Concept does this testimony bear on" —
   real design work, genuinely out of this rung's bounded scope (the
   charter's own line: build the CAN-internal slice, DESIGN the
   epistemic connection).
2. **The verdict categories don't map onto a signed direction for free.**
   A `deception` verdict is evidence that the SOURCE is untrustworthy — it
   is NOT automatically evidence that the claim's content is FALSE (a
   lying source can still say something true). The more defensible mapping
   is: `deception` should shrink `alpha` (this source's testimony counts
   for less, regardless of direction) rather than push `evidence` toward
   a specific sign; `opacity`/introspection-gap testimony, by contrast, is
   SINCERE (the actor genuinely believes what they say) and so is more
   defensible as directional evidence about the actor's SUBJECTIVE state,
   even while remaining weak evidence about the OBJECTIVE causal claim.
   `undetermined` (the low-stakes, high-`residual_other_mass` case) should
   plausibly contribute near-zero `alpha` either way. This asymmetric
   deception→discount-reliability / opacity→discount-directness mapping is
   a real, specific, defensible design (not a menu of options), but it is
   a NEW piece of reasoning this rung did not build or test, exactly the
   kind of thing the charter says is allowed to conclude "needs its own
   follow-on rung."

**Sizing note for that follow-on, named not built**: `interval_low`/
`interval_high`'s width is a natural `alpha` scale (narrow interval = more
confident = higher alpha) and `residual_other_mass` is a natural discount
(more unexplained mass = lower alpha) — both already exist on
`EpistemicLeanReading` today, so the ARITHMETIC side of the mapping is
small once the Concept-targeting wiring (point 1) exists. The
Concept-targeting wiring is the larger, undesigned piece.

---

## 7. "The goal is to design an arbitrary solver" — nuanced weighting is
necessary, not sufficient; shape-recognition is the missing tractability
half

The creator's own framing, restated precisely: finding a spin-glass ground
state — what `mt_mean_field_marginal`/`relax_to_marginal` compute a
mean-field APPROXIMATION of — is NP-hard in the general case (this is a
standard, well-established result for Ising/spin-glass systems with
frustrated couplings; mean-field itself is already an approximation
precisely because exact ground-state search does not scale). §3's own data
makes this concrete: N=16 already produced a landscape both vocabularies
struggle to organise into few, deep, well-separated basins — a coarse-to-
fine weighting fix does not by itself change that qualitative picture,
because vocabulary resolution controls REPRESENTATIONAL FIDELITY (does the
J value actually reflect the true relationship), not COMPUTATIONAL COST
(how many candidate configurations must be explored to find/verify a good
one). These are genuinely different axes, and §3's N=16 convergence is
itself a small piece of live evidence for exactly this: at N=16 the coarse
and fine landscapes look ALIKE, meaning resolution had already stopped
being the deciding factor — density/frustration had taken over as the
dominant cost driver, which is precisely the NP-hard axis nuanced weighting
does not touch.

**The named candidate mechanism, checked seriously against this exact
codebase's own real, measured precedent, not assumed by analogy.**
`BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` (commit `14cb457`, merged this
session, read in full for this assessment) measured `_pair_witness` — a
pairwise structural-correspondence comparison, the SAME shape of operation
as "does this J_ij coupling look like one already seen" — on the real,
booted `computer_architecture` Microtheory (142 concepts, 20164 candidate
pairs, 7970 pairs actually compared after a cheap pre-filter): **7970 raw
pairwise comparisons collapsed onto only 139 distinct `transform_key`
patterns — 98.3% (7831/7970) of calls recognised an ALREADY-SEEN pattern
rather than being independently novel.** This is not a hypothetical
analogy — it is a real, measured compression ratio on this project's own
real corpus, using the SAME sd-loop shape (`ShapeSignature`/`AntiUnifyWitness`
recognise-then-mint) this whole architecture already commits to as its
general answer to "how does the substrate represent a quantity that
changes without treating every instance as independent" (`CLAUDE.md`'s
"SHAPES, NOT NUMBERS" section).

**The hypothesis this raises for CAN specifically, assessed on its
plausibility, not merely asserted**: most `J_ij` couplings in a real,
LARGE belief network are very unlikely to be independently-estimated free
parameters either. A real agent's belief that "smoking causes cancer" and
its belief that "asbestos causes cancer" plausibly share a recognisable
SHAPE ("substance X, ingested/inhaled, correlates with disease Y") rather
than being two unrelated numbers a solver must independently place. If
most of a large network's N(N-1)/2 candidate couplings are, like the
blob-edge case, recognisable instances of a much smaller set of held
causal-linkage shapes ("physical proximity implies causal influence,"
"shared category membership implies correlated evaluation," "temporal
sequence implies possible causation," etc.), then an arbitrary-scale CAN
solver does not need to relax N(N-1)/2 independent couplings from scratch —
it needs to (rung 1) RECOGNISE couplings against a held codebook, reusing
already-computed structure, and pay FRESH relaxation cost (rung 4: MINT)
only for the genuine residual — exactly the sd loop's own general shape,
applied one level up, to the coupling structure itself rather than to any
single node's content.

**This is named and assessed, deliberately NOT built here** — building a
real shape-recognising CAN-coupling compressor (a `CausalLinkageShape`
codebook, a recognise/mint rule pair analogous to `blob_recognize`/
`blob_mint`, and the non-trivial question of what counts as "the same
shape" for a J_ij coupling as opposed to a structural correspondence) is a
full rung of its own design work, correctly out of this rung's bounded
scope per the charter. What this rung DOES establish, honestly: (a) the
NP-hardness concern is real and not addressed by §0/§3's nuanced-weighting
fix alone — confirmed both by the general theoretical fact and by §3's own
N=16 data; (b) the shape-recognition/compression answer is not a bare
analogy reached for because it is fashionable in this codebase — it has a
real, measured, large (98.3%) compression precedent on THIS project's own
corpus, at a scale (7970 comparisons) in the same rough order as a
plausible large CAN network's coupling count; (c) whether CAN couplings
SPECIFICALLY cluster into recognisable shared shapes the way analogical
correspondences did is an EMPIRICAL question this rung did not test (no
real large `causal_influence` network exists in the corpus today to test
it against — `causal_attitude_networks.json` itself has zero populated
`Concept`/`causal_influence` instances, only its own definitional
`ShapeSignature`-style Concept nodes describing the model) — named as the
natural next empirical check, not assumed to hold.

---

## 8. Final recommendation — concrete, sized, not a menu

1. **Landed this rung, keep**: `curiosity_targets_ambivalent_nodes`'s real
   `match`/`where`/`effects` (§5). Small, tested four ways including the
   real production boot path, zero new Rust, zero regressions.
2. **Next build (sized, concrete)**: give the CAN dynamics a DSL Term
   surface, starting with the smallest, highest-leverage piece —
   `MtRelax{mt}` wrapping `can_ops::relax_to_marginal` as a Term callable
   from a Rule's `effects`, mirroring exactly how `ShapeDecode` already
   wraps the sd-loop's decode step (`shape_decode.rs` → `sd_decode`'s
   `effects`, read in full during this rung, §4's Layer-1 finding). This
   single Term unlocks real `match`/`where`/`effects` wiring for
   `evidence_changes_field_then_relaxation` and (with a second small Term,
   `MtHebbian{mt,eta}`) `Hebbian_learning_updates_J` — the two rules that,
   after `curiosity_targets_ambivalent_nodes`, most directly enable the
   OTHER 13 to eventually become reachable, because most of them presuppose
   relaxation/learning has already happened. Sized: 2 new Term variants
   (`MtRelax`, `MtHebbian`), each a thin wrapper (the Rust function
   signatures already exist and are stable), plus 2-3 rules reusing the
   now-existing `state`/`is_ambivalent` convention this rung established.
   Explicitly NOT attempted in this rung per the charter's own scope line
   ("no new Rust Term... stop and report why").
3. **Next design pass, sized**: the `epistemic_default.json` → CAN
   connection (§6) needs exactly one new piece of wiring — an edge from
   whatever a `ForcedChoiceProbe`/`EpistemicLeanReading` is ABOUT to a real
   `Concept` node — before the arithmetic mapping (already sketched, small)
   can be applied. This is real, un-sized-in-detail design work; it should
   be its own rung, not folded into #2.
4. **A named, sized follow-on for §3.1's honest-null**: power the resolution
   -vs-oscillation question properly before drawing any conclusion from it
   — a pre-registered sample size (this rung's own 24- and 40-trial
   exploratory runs were not sized against any effect-size target), and,
   per §3's own caveat, a STRUCTURED (not i.i.d.-random-sign) true-coupling
   generator, since a real belief network's genuine contradictions are
   unlikely to be uniformly random the way this rung's synthetic draws
   were. This is cheap to run (each trial is sub-millisecond) — the
   limiting factor was scope, not compute.
5. **The load-bearing recommendation for "arbitrary scale," stated without
   hedging**: nuanced/quantized weighting (the earlier N×M framing) is a
   NECESSARY fix for representational fidelity but is NOT SUFFICIENT for
   tractability at arbitrary N — that requires a shape-recognition/
   compression layer over the coupling structure itself, following the sd
   loop's own recognise/mint shape one level up, with a REAL, measured,
   same-codebase precedent (98.3% pairwise-comparison compression,
   `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`) rather than a borrowed
   analogy. The concrete next build, sized: a `CausalLinkageShape`
   codebook + `can_recognize_coupling`/`can_mint_coupling` rule pair,
   structurally parallel to `blob_recognize`/`blob_mint`, gated on an
   EMPIRICAL first check (build or find a real, large `causal_influence`
   network — none currently exists in the corpus — and measure whether its
   couplings actually cluster the way blob-edge correspondences did, BEFORE
   committing to the compressor's design, per this session's own "power the
   gate before the endgame" standing rule). This is a full rung, correctly
   not attempted here.

---

## 9. What this rung does NOT establish

1. The primary N×M scaling prediction, as literally registered, is not
   confirmed on the tested design (§3) — a structured-truth (not
   i.i.d.-random-sign) variant is the natural next experiment if this
   specific mechanism is pursued further.
2. `effective_basin_count`/`dominant_basin_fraction` are this rung's own
   metrics, not independently validated against the CAN literature.
3. **The cohere-vs-abandon phenomenon (§3.1) is real and mechanistically
   confirmed; the specific claim that RESOLUTION drives it is not** — the
   measured lean (coarse oscillates somewhat more than fine) is consistent
   with the prediction's direction across two samples but is small relative
   to sample noise (24 and 40 trials, no power analysis) and was REVERSED
   on the single most dramatic individual draw tested. This should not be
   read as "confirmed, weakly" — it should be read as "a real, adjacent
   phenomenon exists; whether resolution is its cause is unresolved."
4. Whether real CAN couplings cluster into recognisable shared shapes
   (§7) is named as a hypothesis with a real precedent elsewhere in the
   codebase, not tested here — no populated `causal_influence` network
   exists in the corpus to test it against yet.
5. Only 1 of the 15 rules was wired; the other 14 remain correctly inert,
   for the precise, now-documented reason in §4 (no DSL Term surface for
   the dynamics), not for lack of trying.
6. The `epistemic_default.json` connection is designed, not built, and its
   Concept-targeting prerequisite is real, unscoped work.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-belief-quantization
git log --oneline -1 main   # 0e18038, verified before branching

# Live demonstration (the factorial table)
python3 -m pytest tests/test_can_belief_quantization.py -q -s

# The wired rule, all four angles
python3 -m pytest tests/test_can_belief_quantization.py -k ambivalence -q

# Targeted regression
python3 -m pytest tests/test_can_ops.py tests/test_causal_attitude_networks.py \
  tests/test_can_migration.py tests/test_can_belief_quantization.py -q

# Full boot regression (pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"
```
