# DOES THE FIXPOINT FIX MOVE ANY LANDED NUMBER? — PRE-REGISTRATION

*Written and committed BEFORE any number exists. Seeds **91000–91999**.
Answers the standing liability left open by ledger row 85000–85999:
"NO LANDED NUMBER WAS RE-RUN UNDER THE FIX AND NO CLAIM IS MADE ABOUT
WHETHER ANY PUBLISHED RESULT CHANGES."*

---

## 0. SEED CLAIM (§3)

```
SEED CLAIM 91000-91999: CLEAN -- no collision DETECTED.
  Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**I DELIBERATELY RE-USE ALREADY-BURNED SEEDS, and this is not a §3 violation —
it is the point.** A replication that redraws is not a replication. Every arm
re-runs each landed script on **its own declared seed block**
(genmint 25000–25399, time 26100–26999, depth 27100–27499, stereo 28000–28399,
blink 31100–31499, ground 30000–30099), because the comparison is
**fix-vs-revert on IDENTICAL inputs** — the only design in which a difference
is attributable to the engine. My block 91000–91999 is reserved for material I
draw MYSELF, i.e. the positive control only.

## 1. THE QUESTION

Every published number in this tree was produced by an engine in which
`dirty_by_writeset` carried `if self.rule_dirty[j] { continue; }` — an
early-out that discharged the dirty obligation but **not** the cursor-invalidation
obligation, so `run_rules` could report a fixed point over demonstrably
unsettled state. Does removing it move any landed result?

## 2. SELECTION RULE — STATED BEFORE MEASURING

Prioritised by the predecessor's **316 race-constructible pairs across 95
consumers**, NOT by convenience:

1. **Rank each landed result by the race-pair count of the seeds its measuring
   script boots.** The mapping is mechanical: read the script's
   `_ensure_shape_decode_loop` / `manifest_for(...)` / `load_seeds_into([...])`
   calls, look the seed names up in the predecessor's table.
2. **Take EVERY landed result whose booted seed set includes
   `shape_decode_loop`** — 34 pairs, second-highest, and named by the
   predecessor as *"the structurally purest case and the one the architecture
   leans on hardest"*: all 17 rules match the single `observed` edge and the
   whole growth ladder coordinates through node attrs.
3. **Add the highest-ranked landed result NOT in that set** as an
   out-of-family check (`ground_measure` → `vision_waves` + `vision_ground`).
4. **Add the oracle** (`scripts/rung7_vision_bench.sh`) on BOTH engines as the
   regression band.

Applying the rule mechanically selects, in rank order:

| landed result | script | booted seeds | in family |
|---|---|---|---|
| gen-mint | `scripts/genmint_measure.py` | `shape_decode_loop` | yes |
| time | `scripts/time_measure.py` | `shape_decode_loop` + `time_axis` | yes |
| depth | `scripts/depth_measure.py` | `shape_decode_loop` + `depth_axis` | yes |
| stereo | `scripts/stereo_measure.py` | `shape_decode_loop` + `depth_axis` | yes |
| blink | `scripts/blink_measure.py` | `shape_decode_loop` + `time_axis` + `blink_bridge` | yes |
| ground | `scripts/ground_measure.py` | `vision_waves` + `vision_ground` | out-of-family |

`impasse_escalation` (41, the highest) is NOT covered: it boots in no landed
vision measurement script. **That is a stated gap, not an oversight** — see §6.

## 3. THE RACE LIMB IS PRESENT IN THE TARGET SEED (static, pre-measurement)

Recorded here **before** any run, because it sets my prediction and must not be
reconstructed afterwards. Structural walk of `seeds/shape_decode_loop.json`
(`json.load` + effect-op inspection, **never substring selectors**, §12):

- Four rules perform `add_edge` — `sd_mint_generator` (`gen_minted`),
  `sd_recognize_transformed` (`has_transform`), `sd_recognize_dim`
  (`has_transform`, `has_latent_dimension`), `sd_mint_quantum` (`minted`).
- Six rules READ those edge types in their where-clause — `sd_mint_generator`,
  `sd_recognize_transformed`, `sd_recognize_dim`, `sd_mint_quantum`,
  `sd_dedup_existing`, `sd_redecode`.
- All 17 rules match on the single stable `observed` edge, and thirteen of them
  write attrs (`status`, `residual`, `gen_checked`, `dim_checked`,
  `transform_explained`, `codebook_epoch`).

**So the exact three-rule shape exists here, live, in the ladder these five
measurements gate on:** a mint `add_edge` structurally dirties a consumer
(cursor correctly left intact); a `set_attr` rule later in the SAME pass finds
that consumer already dirty; pre-fix it is skipped and its cursor is never
cleared; it then runs the incremental path with zero new `observed` edges,
enumerates nothing, and cannot see the attribute flip.

## 4. HYPOTHESIS AND PREDICTION (two-sided, §3.1/§3.7)

**H0:** every selected landed number is identical under fix and revert.
**H1:** at least one moves.

**MY PREDICTION: H1 — I expect at least one of the five in-family numbers to
move, and I expect the movement to be in the MINT COUNTS.** My reasoning is
§3: the race limb is not merely constructible in the abstract, it is built from
the very rules (`sd_mint_quantum`, `sd_recognize_*`, `sd_redecode`) whose firing
these scripts COUNT. A pre-fix engine that returns early leaves a residual
undecoded, and the scripts' headline statistics are exactly "how many quanta /
generators were minted."

**Direction, stated in advance:** if it moves, I expect the REVERTED engine to
mint **FEWER** in the with-mechanism arms (a premature fixpoint truncates the
ladder before `sd_redecode` re-arms) and to show **MORE** spurious mints in the
floor/shuffle arms only if a truncation strands a residual in a mintable state.
I am less confident about the second limb than the first.

**My provisos, so a broken one is informative:**
- (a) I assume the scripts drive enough rules per pass for a THIRD rule to land
  between the structural write and the attr write. If each script's pass
  composition is thin, the limb never closes and everything is null.
- (b) I assume `_ensure_shape_decode_loop` installs these seed rules rather than
  Python-built ones. **Python-installed rules were NOT scanned by the
  predecessor at all**, so if the ladder is Python-installed my static §3 walk
  describes a file the engine never loaded. I will check and report.
- (c) The floor/shuffle arms gate on exact zeros, so they have no room to move
  DOWN; only a spurious mint shows.

## 5. STATISTIC AND DECISION RULE

**The statistic is EXACT JSON EQUALITY of each result document, field by field,
excluding only the provenance/engine-hash and wall-clock fields.** No summary
statistic, no tolerance — these are counts and verdicts, and the question is
binary.

- **Any non-provenance field differing between the two arms ⇒ H1, THE NUMBER
  MOVED.** That is the headline and outranks everything else in the report; I
  will report magnitude and direction and will NOT attempt to rescue the
  original claim (§7).
- **All selected documents equal modulo provenance ⇒ a NULL, BOUNDED BY ITS
  COVERAGE.** I will report coverage as a fraction of the 316 pairs and of the
  landed results, and state plainly that a null over 6 documents licenses
  nothing about the 89 seeds and the landed results I did not run.
- **"Unmoved" is earned per number.** Any landed result I do not execute is
  reported as NOT RUN, never as unchanged.

## 6. WHAT THIS DESIGN CANNOT SEE (§8)

1. `impasse_escalation` (41 pairs, the largest single exposure) and
   `goal_derivation` (23), `nav_intent` (20), `grid_navigation` (16) boot in no
   selected script. Their exposure is UNMEASURED by this rung.
2. Non-determinism: if a script is not deterministic on its declared seeds, a
   difference is not attributable. I will confirm determinism by running the
   FIX arm TWICE and requiring byte-equality before comparing arms. **If the
   fix arm does not reproduce itself, the whole comparison is void and I will
   report that instead of a verdict.**
3. Python-installed rules (proviso b).
4. Landed results outside the vision arc are not touched at all.

## 7. METHOD — ENGINES, NOT HISTORY

Both engines are built **in this worktree from this tree's source** via
`scripts/engine_build.sh` (§11.2 — never symlinked, never `cp` through a
symlink, never a global install):

- **ARM FIX** — tree as committed. Engine built, provenance gate run as its own
  step (`7 passed`) BEFORE any number.
- **ARM REVERT** — the single early-out `if self.rule_dirty[j] { continue; }`
  restored at `substrate.rs:539`, `scripts/engine_build.sh` re-run, provenance
  gate re-run. Source and engine agree in BOTH arms, so provenance is honest in
  both.
- After measuring, the revert is discarded (`git checkout`) and the FIX engine
  rebuilt.

**Against the defect that the provenance gate certifies the TREE, not the
PROCESS:** every measuring process prints `provenance_line()` from INSIDE
itself into the results artifact, and I abort on divergence from the engine I
believe I built. The two arms MUST report different engine hashes — if they
report the same hash, the revert did not take and the comparison is void.

## 8. POSITIVE CONTROL — the instrument must be able to see a difference

A comparison that has never been ABLE to report a difference is not a
comparison. **Before trusting any null**, I run the reverted engine against
`tests/test_fixpoint_settle_migrated.py` and require it to go **RED** (that
test is the direct reproduction of the defect), and against the FIX engine and
require **GREEN**. If the reverted engine passes that test, the revert did not
take and every "unmoved" below is a dead instrument, not a result.

**And if the control is QUIET, I find out why before logging a pass.** The
specific quiet-failure mode here is that `engine_build.sh` writes through to a
shadowed artifact and the process imports the other one — which is exactly what
the in-process `provenance_line()` check catches.

## 9. WHAT A NULL DOES AND DOES NOT LICENSE

A null over this coverage licenses: *"the six re-run vision measurements are
byte-identical under fix and revert."* It does NOT license *"the fix changed no
landed number"* — 89 of 95 exposed consumers and every non-vision landed result
remain unmeasured, and the enumeration itself excluded Python-installed rules.
I will write that sentence in the results document whatever the outcome.
