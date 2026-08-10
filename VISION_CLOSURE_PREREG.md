# CONTOUR CLOSURE / TRANSITIVE GROUPING — PRE-REGISTRATION

*Committed BEFORE any confirmatory number. Only the synthetic positive controls and the
value-flood floor may be computed before this file is committed; nothing in it is edited
after the first natural-frame number. Seeds **115000–115999**. Term enum index **180**
(reserved; used ONLY if a robust knee is shown — see §7). This rung is instructed to
CHARACTERISE IN NUMPY FIRST; no Rust, no Term, no seed unless the KNEE lands.*

---

## §0. WHERE THIS RUNG SITS — the terminus, by elimination

Seven levers have been measured NOT to move the enclosed-object size distribution off the
value-flood's **median-1**: the mint predicate (four rungs), the value/flood family
(grouping-ceiling, 18 admissibility relations), peer competition, the aperture, the
enclosure predicate, the 18×18 tile grain — all 1→1. And the **representation**
(phasefield / phase congruency) moved the median off 1 for the first time but only to
single digits, non-phase-specifically (the magnitude trap fired), reproducing the same
**giant-ground / tiny-fragment, one-degree-of-freedom, no-knee trade-off** every prior
lever hit.

The two-directions-converged conclusion of phasefield + motion-energy: **every mechanism
tried is a PER-PIXEL LOCAL FLAG MAP; none CLOSES a contour; so all either LEAK (one
98%-of-frame blob) or OVER-CUT (median-2 fragments). The missing ingredient is CONTOUR
CLOSURE / TRANSITIVE GROUPING.** This rung tests exactly that, and registers in advance
that **a single STATIC frame may not yield few-and-large** — a static null is a POSITIVE
finding about where closure lives (temporal), NOT a dead end.

This composes onto existing machinery, it does not start from scratch: the substrate
already has border ownership (`seeds/vision_border_ownership.json` — border-owned edges,
each WITH A SIDE). The missing step is one relation up: **a proto-object is the region
bounded by a CLOSED contour — a CYCLE in the edge-adjacency graph — not a connected
component of a local flag.** "Transitive" = the substrate's native fixpoint over typed
boundary edges; "closed" = a cycle.

---

## §1. THE MECHANISM — MDL contour closure (edge-primal, gap-bridging to complete cycles)

The lever the phasefield rung earned. It is EDGE-PRIMAL (contour fragments that can be
OPEN, with real gaps), NOT region-primal (a pixel labelling, where every region is
trivially closed — that is the value-flood, already dead). The distinctive operation is
**bridging a gap to complete a cycle**, decided by whether closing COMPRESSES.

**Algorithm (numpy characterisation — the substrate expresses each step natively, but no
Term/seed is written unless the knee lands):**

1. **Contour evidence.** Phase-congruency map `PC` (Kovesi monogenic, `phasefield_pc.py` —
   REUSED, not rebuilt), thresholded at a **SPARSE** operating point (few, gappy
   contours). Closure only matters where the flood LEAKS — i.e. the low-edge-density end
   the phasefield sweep showed becomes one 98% blob. That is deliberately where this rung
   looks.
2. **Skeleton + endpoints.** Thin the edge map to a 1-px contour skeleton; endpoints =
   skeleton pixels of degree 1 (the terminals of gaps).
3. **Flood.** 4-connected components of the non-contour cells = regions. At the sparse
   threshold, one giant region leaks through the gaps (the null).
4. **MDL gap-bridging (the closure operation).** For a candidate gap between endpoints
   `e1,e2` (bridge length `g` = Euclidean path), tentatively add the straight bridge to
   the contour and re-flood. If the bridge **completes a cycle** — a previously-leaking
   region becomes ENCLOSED (a new bounded region of `n_int` cells with mean `μ_int`
   splits off the ground of mean `μ_gnd`) — accept iff it lowers total description length:

   > **BRIDGE iff  `n_int·(μ_int − μ_gnd)² / (2σ²·ln2)  >  g·λ  +  K_model`.**

   LHS = residual bits SAVED by coding the enclosed region separately from the ground
   (the between-group sum of squares). RHS = boundary bits spent on the `g`-px bridge plus
   the model cost of one extra region descriptor. **A gap is bridged iff the region it
   encloses is BIG ENOUGH and DIFFERENT ENOUGH from the ground to pay for the bridge.**
5. **Fixpoint.** Process candidates greedily by MDL benefit; iterate to a fixpoint (the
   transitive closure). Final flood → regions → **the size distribution is the headline.**

This REFUSES over-completion (a bridge enclosing a region indistinguishable from ground,
or a tiny region, or spanning a long gap, is rejected) and CLOSES a nearly-complete
contour (a big different region across a short gap). It is *"a circle with a bit out isn't
a discontinuous circle"* made quantitative — exactly the memory note's MDL closure.

---

## §2. §13 — WHERE EVERY NUMBER FALLS OUT (this is the whole difficulty)

Closure is the archetypal mechanism where a "completion aggressiveness" knob manufactures
any median: complete hard → one giant blob, complete timidly → fragments. **A median in
the object decade produced by TUNING a knob is a §13 violation and NOT a result.** The
derived, parameter-free answer is MDL. The three quantities in the bridge inequality:

- **`λ` (bits per boundary pixel)** = the chain-code entropy of a contour step. A boundary
  following good continuation has ~3 admissible forward directions on the 8-connected
  lattice ⇒ `λ = log2(3) ≈ 1.585 bits`. Falls out of the LATTICE geometry, not chosen.
- **`σ` (noise)** = the sensor/image noise floor, **measured per frame** as the robust
  scale of near-flat adjacent-pixel differences (MAD of the smallest steps) — the same
  quantity the CHANGE rung's shot-noise floor and phasefield's Rayleigh floor derive. Not
  chosen.
- **`K_model` (bits per region mean)** = `log2` of the luminance levels a mean must index
  ≈ the frame's own bit-depth entropy. Falls out of the dynamic range.

The load-bearing scale is the RATIO `σ²·λ` (the classic Mumford–Shah scale). **THE HONEST
§13 PRESSURE POINT, DECLARED IN ADVANCE:** if the knee appears only at a tuned `σ²λ`, that
is a magic number and the verdict is FALSIFY/AMBIGUOUS. The verdict therefore rides on
**ROBUSTNESS of the knee across the `σ²λ` ratio (swept ±1 decade) AND across the PC
operating point AND across nscale**, exactly as phasefield rode on the noise-floor/Otsu
agreement and the nscale enumeration. The candidate-gap distance cap is a COMPUTE bound
only; I assert in-run that **no accepted bridge sits within 2 px of the cap** (else the
cap is load-bearing and the run is void).

The `1` the median is compared against is the value-flood's OWN reproduced median
(enclosed 1 [1,1] on the identical frames), backed by the **5047 (C1) / 3978 (C2)** floor
asserted in-run (the run VOIDS otherwise). A measured incumbent, not a chosen constant.

---

## §3. THE STATISTIC AND THE PRE-REGISTERED DISCRIMINATOR — the KNEE, not the median alone

The last four rungs proved "median in the object decade" is reachable TRIVIALLY by letting
the frame become one blob. **So the median alone is NOT the discriminator.** The signature
that closure adds something the local flag maps could not is a **stable KNEE**.

Primary statistic, per corpus, unit = FRAME (bootstrap median CI over 30 frames/corpus,
the phasefield frame set `range(0,150,5)`):
- **enclosed-region size median** (and the size of the region a typical enclosed cell lives
  in);
- **enclosed region COUNT per frame**;
- **largest region as a fraction of the frame.**

**Verdict, registered in these exact terms, decided at the DERIVED operating point (the
noise-floor σ²λ, the sparse PC point) AND its robustness neighbourhood:**

- **CONFIRM** = a STABLE regime — a plateau ROBUST across the parameter it is most
  sensitive to (`σ²λ` swept ±1 decade), not a knife-edge — where ALL THREE hold together:
  (a) enclosed median in the **OBJECT DECADE (tens of cells, ≥10)**; (b) count
  **FEW-BUT-PLURAL** (register the band **3–40 enclosed regions/frame** — not 1, not
  hundreds); (c) the largest region is **NOT most of the frame** (< 50% of the frame). A
  knee in the size-vs-`σ²λ` curve where the giant-ground/fragment trade-off BREAKS.
- **FALSIFY** = the same monotone giant-ground ↔ fragment trade-off with NO knee; the
  object decade reachable ONLY by the whole frame collapsing to one blob. This is the null
  and the SAME shape phasefield/value/aperture measured.
- **AMBIGUOUS** = a knee exists but is a KNIFE-EDGE (not robust across `σ²λ`), OR one of
  the three CONFIRM conditions fails, OR the closure operator fails its positive control
  in either direction (§4).

---

## §4. THE POSITIVE CONTROL — built FIRST, the instrument's aliveness check (§1 of PROTOCOL)

*"A circle with a bit out isn't a discontinuous circle."* Made a gate, BOTH directions:

- **CLOSE:** a ring (interior contrast against exterior) with a SHORT gap MUST close to
  **ONE** enclosed region (the disc interior).
- **REFUSE (over-completion):** structures where bridging must NOT fire —
  (i) a ring with a LONG gap (the `g·λ` cost exceeds the residual benefit) → leaks, stays
  open (0 enclosed); (ii) two genuinely separate arcs that enclose NOTHING → stay open /
  two, MDL declines (no coherent region to pay for the bridge).

The operator passes iff it closes the short-gap circle AND refuses the long-gap circle AND
refuses the separate arcs — the exact discrimination MDL is supposed to make. **A
mechanism that closes everything, or nothing, FAILS this and the rung is AMBIGUOUS at
best.** This is run and reported before any natural-frame number.

---

## §5. THE STATIC / TEMPORAL FORK — registered in advance, not pre-judged

Test STATIC contour closure first (on the phase-congruent edge map + the same frames — it
is the direct test of the phasefield conclusion and it is cheap). **Registered reading of a
STATIC NULL:** if static MDL-closure cannot produce the knee (FALSIFY or AMBIGUOUS), that
is **strong evidence closure requires TEMPORAL coherence** (a contour that MOVES TOGETHER
closes — the motion line the motion-energy rung opened), which is the next rung and
connects the whole motion line to the object line. **A static null is a POSITIVE finding
about WHERE closure lives, and I will NOT rescue it by tuning `σ²λ` or the PC point.**

---

## §6. SEEDS, n, PROVENANCE, FLOORS

- **Seeds 115000–115999.** `check_claim(115000,115999)` at prereg time: CLEAN, 514
  unresolved sink sites tree-wide (verbatim in §9). The synthetic positive controls draw
  in-block (speckle/noise arms 115000–115099); natural frames are DETERMINISTIC (no RNG
  arm) except the bootstrap resampler (115100). Any seed drawn is reported with
  `seed_audit`, `unknown_sinks` disclosed.
- **n = 30 frames/corpus**, unit = FRAME, bootstrap median CI (`BOOT_N=10000`), matching
  phasefield exactly. Two corpora C1 (cartoon) / C2 (live-action). No power gate is
  meaningful for a distributional-shape verdict; the discriminator is the knee's existence
  and robustness, not a paired effect size.
- **PROVENANCE its own step before any number**, printed from INSIDE the measuring
  process, asserted `== EXPECT_ENGINE`, re-verified after measurement. Engine built in
  this worktree by `scripts/engine_build.sh` (`own`). **Base contains index 179
  (MotionEnergy) and both wave docs — verified.**
- **FLOORS re-earned in-tree, asserted in-run:** value-flood enclosed **5047 (C1) / 3978
  (C2)** at G72/REGION=18/k=16/7 sampled frames; corpus pins C1 `08630d4b` / C2
  `119eca43`. The run VOIDS otherwise. Speckle control ≈0.6% [0.17,2.25] band, NOT
  copied-forward "0/100".
- **CPU ≤ 2 workers; `os.getloadavg()` recorded with every measurement; no wall-clock as a
  verdict.**

---

## §7. DECISION RULE — including what builds and what does not

- **CONFIRM (robust knee, all three conditions, §3):** the mechanism is warranted. THEN
  and ONLY THEN make it graph-resident at **Term enum index 180** (the transitive-closure /
  gap-bridge op over typed boundary edges), gated OFF by default (§9), byte-identity
  proven, oracle re-run. A build is licensed by the knee, nothing else.
- **FALSIFY / AMBIGUOUS:** the rung is a DIAGNOSED NEGATIVE. **Index 180 stays UNUSED, no
  Rust byte, no seed byte** (`git diff seeds/ runners/` EMPTY). If the failure is a static
  null, the recorded finding is "closure requires temporal coherence" (§5), a positive
  result about where the lever lives — reported, not rescued.
- **Exactly the tests listed. No sweeps beyond the declared robustness axes (`σ²λ`, PC
  operating point, nscale). No re-runs. A further attempt needs a NEW prereg with a NEW
  mechanism-level hypothesis (§3 clause 6 of PROTOCOL).**

---

## §8. MY PREDICTION, STATED IN ADVANCE, WITH PROVISOS (§3 clause 7)

**Prediction: ~35% CONFIRM, ~65% FALSIFY/AMBIGUOUS with a STATIC NULL pointing to
temporal.** My honest prior, given seven prior levers all null and the phasefield rung's
explicit "a single static frame may not yield few-and-large": static closure most likely
does NOT produce a ROBUST knee. The likely shape: the MDL bridge, at the derived `σ²λ`,
either (i) rarely fires on natural frames because natural object boundaries have MANY
gaps and low local contrast, so few cycles complete → the flood still leaks (one blob), or
(ii) fires enough to seal SOME regions but the surviving distribution is still
single-digit + not robust across `σ²λ` (AMBIGUOUS).

**Provisos, two-sided (a break tells me what I did not understand):**
- (a) I predict the positive control PASSES both directions — if it FAILS (the operator
  cannot even close a clean circle-with-a-gap while refusing separate arcs), the mechanism
  is mis-derived and the natural-frame result is uninterpretable; I STOP there.
- (b) I predict the natural-frame knee, IF it appears at all, is a KNIFE-EDGE in `σ²λ`
  (AMBIGUOUS) rather than a plateau — because natural contour gaps and contrasts span a
  continuum, so the MDL bridge fires gradually, not at a stable operating band.
- (c) I predict C1 (cartoon, sharper closed contours) is MORE favourable to closure than
  C2 (live-action, textured, gappy) — if C2 confirms and C1 does not, my model of what
  closure needs is wrong.
- (d) I predict a STATIC NULL will point cleanly to temporal — if static already CONFIRMS,
  the temporal fork is moot and the object line closes here, which would be the strongest
  possible outcome and the one I bet against.

The honest §13 weak point I flag in advance (as phasefield flagged Kovesi's constants):
`σ²λ` is a ratio of two derived quantities; if the verdict turns on its exact value rather
than being robust across a decade of it, the rung is AMBIGUOUS regardless of the median.
