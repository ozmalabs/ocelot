# PEER COMPETITION — PRE-REGISTRATION

*Written and committed BEFORE any number. Seeds **96000–96999**.*

**This rung's first commitment is that it is a DIAGNOSTIC, not a mechanism.** The
containment rung's own sharpest self-criticism was *"I built a mechanism on a premise my
own prereg restated as excluded; a one-line nested-pair count would have killed this
before any seed JSON."* Its named next lever — **price the peer competition** — is
therefore taken here as something to **measure first and derive from second**, and
"**no mechanism is warranted**" is pre-registered as a legitimate, reportable outcome
(§0.3 below), not a failure.

---

## §0.1 SEED CLAIM (§3 clause 8) — verbatim `check_claim` output

```
$ python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(96000,96999)[1])"
SEED CLAIM 96000-96999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unresolved sink count: 497 tree-wide.** The block is CLEAN as *detected*, which is not
the same as clean. My own draws are declared in §6 and will be re-audited with
`seed_audit.py --check 96000 96999` on the measuring script after the run; a check that
passes with unknown sinks in **my** files has verified nothing.

## §0.2 PROVENANCE (§10)

Branch `worktree-agent-a37faa572b1a469f0`, base **`77e932f12d6f64a735775b0083c137f9d5df532b`**.
Engine built in-tree by `scripts/engine_build.sh`; **no Rust change in this rung**.
`data/` is a symlink to canonical (§10.2), never a copy. `provenance_line()` is printed
from **inside** the measuring process into the results artifact and the run **aborts** on
`WRONG ENGINE` / `DIVERGED` (the surface rung's rule — a green gate in a different
process is not provenance).

## §0.3 THE THREE OUTCOMES, DECLARED IN ADVANCE

1. **CEILING-BOUND** — the peer competition is *not* what holds the size distribution,
   because the **component field itself** is already fragments and no selection over
   components can mint an object larger than the largest component. ⇒ **no peer mechanism
   is warranted**; the lever is upstream (quantizer / equal-value flood / grouping), and
   this rung reports the ceiling number and stops.
2. **PEER-BOUND** — removing the peer competition entirely opens a materially different
   size distribution. ⇒ a derived mechanism *is* warranted, and §4's decomposition says
   which kind (tie-breaking vs. the universal quantifier over rivals).
3. **NEITHER** — the counterfactual moves counts but not sizes. ⇒ report as the
   fragment-producing null it is; **a count that moves while the median stays at 2 is not
   a result** (the brief's standing instruction).

---

## §1 MATERIAL AND CONFIGURATION — the predecessors', verbatim

G72 exactly as `figadj_nesting_measure.py` and `surface_assignment_measure.py` ran it, so
the numbers are comparable at the SAME GRAIN: `GRID=72`, `REGION=18`, `k=16`,
16 tiles/frame, quantizer = the incumbent per-frame min/max.

Corpora, **pinned, mismatch voids the run**: C1 cartoon `08630d4b` (episode_index 0),
C2 live-action `119eca43` (episode_index 3). Frames `(0, 25, 50, 75, 100, 125, 149)`,
`start_s=300`.

**n FIXED IN ADVANCE: 224 tiles** (2 corpora × 7 frames × 16 tiles) — the containment
rung's own sweep size, chosen so this rung's numbers sit against its 17/17 directly.
**Unit of analysis is the TILE**, never the component: components inside one tile share
input and compete winner-take-all, so they are not independent (§4). Every interval is
over tiles.

**Arms are the STANDING seed's committed flags only. No seed is edited, no rule is
added, no flag is invented.** Primary arm = `wellposed` (`bown=1, bown_own=1,
bown_wp=1, bown_nest=0`) — v1.2.0, the standing configuration. `nested` (v1.3.0) is
re-read for agreement; `incumbent` and `replacement` are re-measured in-tree for the
cost table (**nothing inherited**).

---

## §2 THE STATISTICS, EXACTLY

Computed by a read-out over the **settled** graph, which replicates the armed rule's
gates in the order the rule evaluates them. **The read-out is reconciled against the
rules' own minted output (`G_pass == n_protos`) under every arm before any statistic
below is believed** — the containment rung's discipline, kept.

- **P1 — THE CEILING.** Size distribution (median / p90 / max / max as a fraction of the
  324-cell tile) of all **ENCLOSED COMPONENTS**, not protos. Minting is a *selection over
  components*; no predicate can mint anything larger than the largest component present.
- **P2 — PEER COUNT.** Per component, the number of distinct rival labels
  (`bg < 0.5`, `glabel ≠ R`, abutting). Distribution over all components, and
  separately over components refused by `G_own_lost`.
- **P3 — THE `rim` FIELD.** Distribution of `rim` over components; and per component the
  paired `(rim(R), min_rivals rim(Q))`.
- **P4 — REFUSAL DECOMPOSITION.** Every component refused by `G_own_lost` is classified:
  * **TIE-ONLY** — every blocking rival has `rim(Q) == rim(R)`;
  * **STRICT-LOSS** — some rival has `rim(Q) < rim(R)`;
  and the **margin** `min_rivals rim(Q) − rim(R)` (≤ 0 by construction of a block) is
  reported as a distribution. This is *"what would have had to be true for it to pass"*,
  in the rule's own units.
- **P5 — THE COUNTERFACTUAL CEILING (the decision statistic).** Two mechanism-free
  ablations **of the read-out only** — no rule, no flag, no seed byte changes:
  * **TIES-ALLOWED**: `G_own_lost` refuses only on a strict loss (`rim(Q) < rim(R)`).
  * **NO-PEER**: `G_own_lost` never refuses at all — the peer competition removed
    entirely, every other gate (settled, single-ground-closure, ill-posedness, `G_gnd2`,
    root uniqueness) left intact.
  For each: number passing **and the SIZE DISTRIBUTION of what passes**. NO-PEER is the
  **upper bound on everything any peer mechanism could ever buy**, so it decides §0.3
  without building anything.
- **P6 — THE COMPONENT THAT SHOULD WIN.** For each tile, the **largest** enclosed
  component: does it pass, which gate refuses it, and what are the `rim` and size of its
  blocking rivals? This is the brief's *"is there a component that should win and
  doesn't, and can you point at it?"*, answered by pointing.

**EXPOSURE IS COUNTED, NOT ASSUMED.** Every statistic is reported with the number of
components that reached it. A decomposition over zero refusals, or an ablation that
changes nothing because its gate never fired, is **vacuous, not null**, and will be
labelled so (this week's measured lesson: four of five pre-registered nulls were vacuous).

---

## §3 CONTROLS THAT MUST FIRE, OR NOTHING IS CLAIMED

1. **Read-out reconciliation** `G_pass == n_protos`, per arm, per row. A mismatch voids
   the rung — my classification would be measuring my Python, not the rules.
2. **`rim` reconciliation** — the read-out recomputes `rim` from the settled graph and
   asserts zero disagreement with the attribute the rule wrote. This is the §1 rule that
   *a diagnostic must not be computed by the component it checks*, applied to the one
   quantity the whole competition turns on.
3. **The ablations must be LIVE** — `NO-PEER` must change the pass count on real tiles
   (`D > 0`). If `D == 0` the instrument is decorative and I stop (§1 fifth clause,
   FM-0), exactly as the containment rung did.
4. **The floors, RE-EARNED IN THIS TREE ON THIS ENGINE, NONE INHERITED**: oracle
   `bash scripts/rung7_vision_bench.sh` **before and after**; the synthetic
   border-ownership 9/9 per arm; the **speckle** control 0/100 (RNG **96700**); a
   **genuine single-cell figure still mints**; and the cost table
   (C1 incumbent 3.3 / wellposed 7.1; C2 10.7 / 14.4).
5. **§9** — this rung ships **no** mechanism by construction, so byte-identity is
   trivial; it is nonetheless asserted by the oracle being identical either side and by
   the seed file being unmodified (`git diff --stat` empty on `seeds/`).

---

## §4 MY PREDICTIONS, IN ADVANCE, WITH PROVISOS (§3 clause 7)

1. **P1: the component field is ALREADY fragments — median component size ≈ 2 — and the
   CEILING is the real blocker.** *Proviso that would break it:* if the largest component
   per tile is a substantial fraction of the tile (say ≥ 25% of 324 cells), the ceiling is
   not binding and this prediction fails.
2. **P5 NO-PEER will NOT move the median passing size off ≈2.** Two-sided: if it does,
   outcome PEER-BOUND holds and I was wrong.
3. **P4: ties are a large share of blocks** (`rim` is a small integer over many small
   components), **but removing ties alone leaves most refusals standing.**
4. **P2: median peer count ≥ 2.**
5. **P6: the largest component in a tile passes rarely (< 20% of tiles), and its blockers
   are much smaller than it.** If instead the largest component usually passes, then the
   ladder's fragments are a *counting* artifact and not a size failure — a different
   claim with a different next rung.

I record now that **prediction 1 and prediction 2 are the same bet**, so they cannot
independently confirm each other, and that if they hold, the correct report is a
**redirection of the arc away from the mint predicate**, which is a stronger claim than
this rung is being asked for and will be scoped accordingly (§8-style scope in RESULTS).

---

## §5 DECISION RULE

- **NO-PEER ablation median size ≈ 2 and max ≪ tile** ⇒ outcome 1, **CEILING-BOUND**;
  report the ceiling, build nothing, name the upstream lever. This is a **null for the
  peer mechanism and a positive finding about where the constraint lives** — and it is
  earned only if control §3.3 shows the ablation was LIVE.
- **NO-PEER opens the size distribution** ⇒ outcome 2, **PEER-BOUND**; §4's decomposition
  selects the mechanism class, and that mechanism is **a separate pre-registration**, not
  an extension of this one (§3 clause 6 — no rung both discovers and exploits in one pass).
- Counts move, sizes do not ⇒ outcome 3, reported as fragments-more-slowly.

**No sweeps. No re-runs. No parameter search.** The listed statistics, once, on the
listed material.

---

## §6 SEEDS — declared before drawing

| seed | for |
|---|---|
| **96700** | speckle control, 100 iid fields (§3.4) |
| 96701 | reserved: speckle superset-direction check |

Real-frame tiles consume **no RNG**. Any further draw is a protocol violation and will be
reported as one.

## §7 WHAT THIS RUNG WILL NOT DO

- It will not add a rule, a flag, a Term, a seed node or a line of Rust.
- It will not claim a yield or a cost improvement; the cost table is re-earned only as a
  floor.
- It will not report any statistic whose trigger count is zero as a null.
- It will not read the size distribution of anything without reporting it beside every
  count, per the standing instruction that **the count is not the headline**.
