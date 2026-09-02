# Review of `07_causal_attitude_networks_on_the_substrate.tex` (draft-2026-09-02.1, r1) — proposal for fixes

Scope: the whole file (183 lines, 3 pp), its log, and — because every claim
in it is a report from the programme's record — the CAN rungs in
`docs/research/engine_substrate/` and their dates. Line numbers are r1.
Nothing applied.

Compile: 0 warnings, 0 overfull, three citations, all correct (Dalege et
al. 2016; Barahona 1982 on the NP-hardness of the field-bearing planar
case; Yedidia–Freeman–Weiss 2005 on the mean-field → Bethe → Kikuchi
ladder). No implementation identifiers. The paper's stance — a partial
migration reported as one, a reversed prediction reported as measured — is
the right stance. **The problem is that the paper reports the record as it
stood on the morning of 13 August, and the record moved past all three of
its findings on 13–14 August, nineteen days before the paper was written
(commit e7e9d622, 1 September).** Two of its five falsifiers have already
fired in the record it is reporting from.

---

## A. The two-cycle oscillation was the solver, not the model — falsifier 5 has fired

`rem:found` (l.135–145): "The relaxation exhibits a genuine binary between
cohering and failing to cohere: clean convergence in one regime, a
persistent two-cycle oscillation in another … *It was already present,
unexploited, in the borrowed model's own mathematics.*" Falsifier 5: "The
oscillation is the model's and not the implementation's. Fails if the
two-cycle disappears under an equivalent solver written independently."

The record, `CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md` (2026-08-13): the
mean-field update iterated σᵢ ← tanh(β(Σ Jᵢⱼσⱼ + hᵢ)) *fully
synchronously* (Jacobi), which is the textbook source of period-2 limit
cycles; with damping λ = 0.5 "the exact scenario [the quantization rung]
used to establish a persistent period-2 limit cycle oscillates under the
old code (opposite-parity gap 5.615746) and converges cleanly under the
fix (gap 0.000000), on the identical draw"; across 126 re-tested cells
"oscillation is not merely reduced, it is eliminated in every single
re-tested case"; and the rung "partially retracts" the earlier
"abandonment" interpretation.

So the "discriminative null found, not built" was an artefact of the
update schedule. By the programme's own rule (a null that localises the
cause is a headline finding), this is the paper's most useful result and
it is currently reported backwards. **Fix:** rewrite `rem:found` as
"[The oscillation was the update schedule, and the record found it]":
what was observed, what the synchronous update does, what damping
showed, and the correction — the binary the account has elsewhere was
*not* present in the borrowed mathematics; what was present was a Jacobi
iteration. Falsifier 5 is reported as fired and replaced by: `[detail]`
fails if a damped, asynchronous, or independently written solver
reproduces a period-2 cycle on any of the 126 re-tested cells.

Note the crossover rung (`CAN_CROSSOVER_POINT_RESULTS.md`) still calls
the binary "real, confirmed again"; it ran on the pre-fix solver, and the
fix rung names a fresh sweep under the corrected solver as the follow-on
not yet done. Say that.

---

## B. The dynamics have a term surface — falsifier 1 has fired

`sec:alignment` (l.59–72): "*There is no DSL term surface for the
dynamics at all.* … what has been moved is the network's data and its
results, not its dynamics." Falsifier 1: "Fails if the dynamics can be
expressed in the existing term vocabulary without new term surface."

The record, `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` (2026-08-13): "Items
1–3 are BUILT and PROVEN on the real engine, **zero new Rust**: [a seed
of] 5 rules, 4 productions … 8 tests, all green, including 3 required
live demonstrations". The discrete-asynchronous update runs as graph
rules over graph data — the exact criterion `sec:moved` gives for "moved"
rather than "hosted". Two engine-level findings were made and corrected
while building (a rule-list priority that can starve a sibling rule; a
beam-search preference for a redundant composite). `CAN_FINAL_MIGRATION_
RESULTS.md` (same day): 2 of 6 remaining consumers migrated; 4 stay on
the continuous mechanism "for ONE newly-precise, empirically-confirmed
reason" (every audited compiled function still has an irreplaceable
consumer), and a real hazard was found — `run_rules()` invoked for one
microtheory mutates an unrelated one, because the native rules carry no
microtheory-identity constraint.

So the migration is partial in a *different* way from the one stated:
the dynamics are native; the remaining boundary is consumer-side and
scoping. **Fix:** rewrite `sec:alignment` from the record: the hosted
solver; the native rules (what they express, in the existing vocabulary,
zero new Rust); what still runs on the compiled path and the one reason;
the scoping hazard. The abstract's "reimplemented on this substrate as a
mean-field self-consistency solver … runs beside the graph rather than in
it" becomes "reimplemented twice: as a hosted solver, then as graph rules".
Falsifier 1 reported as fired; replaced by `[shape]`: fails if the native
rules' results diverge from the hosted solver's on the same network, or if
the per-microtheory scoping cannot be enforced in rule matching.

Keep the "fifteen rules were inert" finding as history of the hosted
stage, one sentence, since the record supports it
(`CAN_BELIEF_QUANTIZATION_RESULTS.md`).

---

## C. The ladder was climbed — `rem:hierarchy` and falsifier 4 are out of date

`rem:hierarchy` (l.87–99): "the better half of the same literature is
sitting one step away **unused**." Falsifier 4: "Fails if an exact solver
at these network sizes changes the reported quantities materially."

The record, 2026-08-14:
- `CAN_LOOPY_BP_RESULTS.md`: loopy BP built, both variants. Max-product
  is the theoretically right and empirically better variant on the
  frustrated dense N = 16 case (never worse than sum-product across 8
  draws) but converges *less* often on the real sparse residents (4/15 vs
  5/8), traced to a genuine period-4 message oscillation from one 3-cycle
  plus tied integer weights. Sum-product converges everywhere and to
  worse joint states (mean frustration 2.142 vs 1.693 for multi-start).
  Neither beats multi-start on deployed residents. BP costs 20–200× the
  wall-clock. "A precisely characterised, genuinely two-sided finding."
- `CAN_JUNCTION_TREE_RESULTS.md`: **exact** min-sum inference for
  low-treewidth networks, proven against brute force (5/5, float-tight),
  cross-checked against the live energy, refuses cleanly on treewidth-15,
  and finds a strictly lower-energy state than multi-start on a real
  cycle-topology network. Zero new Rust.
- `CAN_SOLVER_TRACTABILITY_RESULTS.md`: measured local-minimum risk on an
  adversarial network and, less often, on real residents; multi-start
  built as the smallest fix; treewidth measured exactly (residents 2,
  stress case 15); the coupling matrix has effective rank ≈ 1.98 of 5.

So `rem:hierarchy`'s caveat ("Bethe and loopy propagation are themselves
known to lose stable solutions in the same … regime") was *tested* and
came out exactly as predicted on one topology and inverted on the other.
`sec:performance`'s open question ("how good the approximation is and
when it fails to converge") has an answer. And falsifier 4's instrument
now exists: the one thing not yet done is to re-run `rem:bigville`'s
frustration/energy separation under exact inference.

**Fix:** `rem:hierarchy` → "[The ladder, climbed]": the two-sided BP
finding and the junction-tree result, in three sentences each, with the
20–200× cost. Falsifier 4 rewritten as the live test: fails if the
coarse/fine separation of `rem:bigville` does not survive exact
junction-tree inference on the treewidth-2 residents where it applies.
Add `[detail]`: max-product's convergence deficit on sparse residents is
the 3-cycle-plus-ties mechanism named — fails if breaking the ties
(perturbed weights) does not restore convergence.

---

## D. `rem:null`'s numbers are pre-fix, and a later rung extends it

The numbers in `rem:null` (6 vs 4 at N = 4; 15 vs 4 at N = 8; frustration
2.10/1.55 and 15.32/11.06) are from the quantization rung's original
solver. `CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md` re-checked them under the
corrected solver: "the small-N basin-count reversal's direction mostly
holds but magnitude and the dominant-fraction sub-claim change
substantially". `CAN_CROSSOVER_POINT_RESULTS.md` (pre-fix solver, so with
the same caveat) adds: the reversal reproduces at N = 4/8 with five-seed
replication; no crossover N\* anywhere in {4 … 32}; and the sharpest
resolution effect in the whole sweep is not bin count but **the presence
or absence of a zero option** — a two-value vocabulary produces 1.6–2×
the frustration of every V ≥ 3, while V = 3 … 11 show no reliable ordering.

**Fix:** report the corrected-solver numbers (or say the direction holds
and the magnitudes are being re-measured); add the no-crossover null and
the zero-option finding, which is the strongest positive result in the
arc and is absent from the paper; falsifier 3 ("fails if the basin counts
recover the registered direction under a larger sample") has been run —
five seeds, direction held — say so and retire it or restate it against
the corrected solver.

---

## E. Standing, naming, form

1. **Evidence standard.** Every figure here is from the programme's
   record and none is circulated. Adopt 01 r278's sentence once (grep 01
   for "pre-registered implementation record"), as 02b did.
2. **Naming.** No companion is named; `sec:moved` states the substrate's
   claim ("decisions are taken by graph rules over graph data") without
   saying whose. Add the naming sentence (Graphic Equalisation) and, if
   `xr-hyper` is added, `GE-` refs for the residual/mint result the
   "cohering or failing to cohere" binary was said to match
   (`GE-prop:decoherence-one`) — now as the thing it turned out *not* to
   be.
3. **Tags.** No `[shape]`/`[detail]` definition; add 01's sentence
   verbatim.
4. **Structure.** After A–D the paper has five findings; the current three
   sections (alignment, performance, results) become: the hosted stage
   and its null; the oscillation; the native rules and what still runs
   compiled; the ladder; the quantization arc. Each result a numbered
   remark with its date in the record, since the whole defect here was
   dates.
5. **Bump to r2** and state in the box that this revision reports the
   record to a named date, as `sec:record-wrong` in 06 now does.

---

## What is right and should not be touched

- `sec:moved`'s distinction between *hosted* and *moved*, which is exactly
  the criterion the native-reimplementation rung then met.
- `sec:performance`'s point that Barahona's hardness does not bind because
  no exact ground state is sought — still true, and now sharpened: exact
  inference *is* sought where treewidth permits, and refused where it does
  not.
- `rem:bigville` entire (the 9.2× manipulation check, the frustration/
  energy separation, and the resolution-fixed control collapsing the
  correlation from −0.33 to −0.08) — the numbers match
  `BIGVILLE_CAN_INTEGRATION_RESULTS.md`.
- The abstract's "reported as measured rather than reinterpreted", which
  is the discipline the rewrite should keep while changing what it
  reports.

---

## Suggested order

1. **A** — the oscillation, reported the right way round.
2. **B** — the native rules; falsifier 1 fired and replaced.
3. **C** — the ladder climbed; falsifier 4 made live.
4. **D** — corrected numbers, the no-crossover null, the zero-option
   finding.
5. **E**.
