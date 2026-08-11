# DOES THE FIXPOINT FIX MOVE ANY LANDED NUMBER? — RESULTS

# **YES. ONE DOES.**

**`results/codebook_axis.json` → `real_vision_codebook[*].alive.n_exact` is
`[0, 0, 0, 0, 0]` as landed and `[1, 2, 2, 2, 4]` under the fix** — a row of
zeros that becomes the sd orbit law. Deterministic, 2 replicates per arm, no
overlap. **The defect was suppressing EXACT RECOGNITION entirely in the live
vision sd loop**, and the landed document recorded that suppression as data.

**The published CLAIMS of that document all survive** (`mints` = `[1,2,2,2,4]`,
`exhaustiveness` = 1.0000, `attempts_per_part` = 91.16%, the `term_unit:DimInfer`
0.0884 saving — every one unmoved). What moved is the **ALIVENESS POSITIVE
CONTROL** inside it. **An instrument that exists to prove the loop is not dead
was reading zero for an engine reason.** That is the finding.

*Pre-registration `VISION_FIXPOINT_RERUN_PREREG.md`, committed at **`9a5819ff`**
BEFORE any number existed and before the instrument existed. Seeds
**91000–91999**. Answers the standing liability of ledger row 85000–85999:
"NO LANDED NUMBER WAS RE-RUN UNDER THE FIX AND NO CLAIM IS MADE ABOUT WHETHER
ANY PUBLISHED RESULT CHANGES."*

---

## 0. PROVENANCE — which binaries produced these numbers

| | |
|---|---|
| branch | **`worktree-agent-a5caa5392417a856b`** — reported as observed |
| base | **`ee0a1af2`** |
| prereg commit | **`9a5819ff`** (before any number) |
| **engine, FIX arm** | **`a1d350bbd23b`** — own build, `scripts/engine_build.sh` |
| **engine, REVERT arm** | **`df3183725e4e`** — own build, same script, `if self.rule_dirty[j] { continue; }` restored at `substrate.rs:539` |
| **engine, REVERT + trigger counter** | **`8662ef5fc070`**, rebuilt later as **`0e069939bc4d`** |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed**, run as its OWN step BEFORE any number, **on every engine** |
| in-process provenance | `provenance_line()` printed from INSIDE every measuring process into `_engine.txt` and each result document's `engine` field. **The arms report DIFFERENT hashes**, so the revert demonstrably took; and restoring the fix rebuilt to **`a1d350bbd23b` bit-identically**, so the revert was demonstrably undone |
| **oracle, FIX engine** | **212 passed / 10 skipped**, exit 0 (`scripts/rung7_vision_bench.sh`, no `data/`) |
| **oracle, REVERT engine** | **212 passed / 10 skipped**, exit 0 — **identical. The oracle has NO POWER to detect this defect** (§4.3) |
| machine | AMD Ryzen 5 9600X, 12 logical cores |
| concurrent load | at least one other rung (worktree `agent-ac7efef13e76a8f7c`) ran throughout. Every substantive number compared here is a COUNT or a VERDICT — load-independent. Wall-clock fields are excluded, and §3 shows exactly how that exclusion was DERIVED rather than asserted |

The comparison is **fix-vs-REVERTED ON THE SAME TREE**, both engines built by me
in this worktree from this tree's source, per the brief — not fix-vs-history.
History is used only as a third, corroborating arm (§2.2).

---

## 1. THE POSITIVE CONTROLS — three instruments, all shown ABLE to fail

### 1.1 The engine arms

| engine | `tests/test_fixpoint_settle_migrated.py` |
|---|---|
| FIX `a1d350bbd23b` | **6 passed** |
| REVERT `df3183725e4e` / `0e069939bc4d` | **1 failed, 5 passed** — *"consume's where-clause is TRUE on n1 -[link]-> n2 (go=1.0) and must have fired exactly once; got 0 Markers, 0 after a re-run"* |

The reverted engine reproduces the documented defect exactly. Not quiet.

### 1.2 THE FIRST POWER PROBE WAS A DEAD INSTRUMENT — and I caught it before reporting it

I built a probe on the natural predicate: *`run_rules` claims a fixed point, so
a second immediate call must make ZERO steps; if it makes more, the first
returned over unsettled state.* It reported **0 unsettled out of 2307 calls**
across the five sd-loop measurements on the DEFECTIVE engine — which reads like
a clean, powered null.

**It is not. It is inert, and provably so.** Run against the KNOWN-DEFECTIVE
reproduction it also reports 0 — because the reverted engine's second call
*also* makes no progress. The stale cursor is exactly what stops it. The
ledger row says this in its own words (*"a SECOND call makes 0 further steps"*),
and the shipped test's failing assertion is the **Marker count**, not
`extra_steps`. **My probe was measuring a predicate the defect satisfies.**

**Had I logged that 0/2307 as a powered null, the entire rung would have been a
confident, plausible, wrong answer.** The standing rule — *if a control is
QUIET, find out why before you log it as a pass* — is what caught it.

### 1.3 The instrument that actually works: count the DEFECT'S TRIGGER in the engine

Replacement: a counter compiled into the reverted engine that increments exactly
when the early-out skips a consumer **for which the fixed code would have
cleared a NON-EMPTY cursor** — the runtime event the defect consists of.

Positive control on the reproduction:

| arm | Markers (expect 1) | `HARMFUL_SKIPS` |
|---|---|---|
| `pre_open_gate=False` (defective) | **0 — WRONG** | **1** |
| `pre_open_gate=True` (benign) | 1 — correct | 1 |

It fires on the arm that produces the wrong answer. It also fires on a benign
skip, so **`HARMFUL_SKIPS > 0` is an UPPER BOUND on the defect's firing, and
`HARMFUL_SKIPS == 0` is a PROOF the defect could not have affected the run** —
which is precisely the power statement this rung needed.

**The counter's own contribution was measured, not assumed.** Its fallback path
boots a `Substrate` to read the static; run against a no-op script that boot
contributes **0**. The instrument does not compute its own reading.

---

## 2. THE HEADLINE, MEASURED

### 2.1 The number that moved

`scripts/codebook_axis_measure.py` → `results/codebook_axis.json`:

| arm | engine | `real_vision_codebook[*].alive.n_exact` |
|---|---|---|
| **COMMITTED (landed)** | pre-fix | **[0, 0, 0, 0, 0]** |
| **REVERT, replicate 1** | `0e069939bc4d` | **[0, 0, 0, 0, 0]** |
| **REVERT, replicate 2** | `0e069939bc4d` | **[0, 0, 0, 0, 0]** |
| **FIX, replicate 1** | `a1d350bbd23b` | **[1, 2, 2, 2, 4]** |
| **FIX, replicate 2** | `a1d350bbd23b` | **[1, 2, 2, 2, 4]** |

**4/4 replicates, perfect separation, no overlap, no statistic required.** The
landed value is reproduced exactly by the reverted engine and by nothing else.

**Direction:** the DEFECTIVE engine does LESS. `[1,2,2,2,4]` is the sd orbit law
`{2:1, 3:2, 4:2, 6:2, 12:4}` — the same law the document already publishes for
`K_attempting`.

### 2.2 The mechanism — verified, not asserted, and it is the one the prereg named

Status distribution over the identical observations, both engines:

| n_thetas | REVERT `0e069939bc4d` | FIX `a1d350bbd23b` |
|---|---|---|
| 2 | `{minted: 1, recognized_transformed: 1}` | `{recognized: 1, recognized_transformed: 1}` |
| 3 | `{minted: 2, recognized_transformed: 1}` | `{recognized: 2, recognized_transformed: 1}` |
| 4 | `{minted: 2, recognized_transformed: 2}` | `{recognized: 2, recognized_transformed: 2}` |
| 6 | `{minted: 2, recognized_transformed: 4}` | `{recognized: 2, recognized_transformed: 4}` |
| 12 | `{minted: 4, recognized_transformed: 8}` | `{recognized: 4, recognized_transformed: 8}` |

**Every observation that ends at `minted` under the defect ends at `recognized`
under the fix.** The mint happens either way — `mints` is unmoved — so what the
defect suppressed is the ladder's LAST step: the **post-mint RE-DECODE**
(`sd_redecode`, re-armed by `codebook_epoch`).

That is exactly the shape §3 of the pre-registration named, in advance, from a
static walk: `sd_mint_quantum` adds the `minted` EDGE (a structural write that
dirties consumers while correctly leaving their cursors intact); a `set_attr`
rule later IN THE SAME PASS finds `sd_redecode` already dirty; pre-fix it is
skipped and its cursor is never cleared; it then runs the incremental path with
zero new `observed` edges, enumerates nothing, and never sees the flip.
**`sd_redecode` is one of the six rules the prereg identified as reading the
`minted` edge.**

### 2.3 What did NOT move in that document — the published claims survive

| quantity | doc claim | revert | fix |
|---|---|---|---|
| `real_vision_codebook[*].codebook.mints` | `K_attempting` = **1,2,2,2,4** | 1,2,2,2,4 | 1,2,2,2,4 |
| `exhaustiveness` measured/predicted | **1.0000** | identical | identical |
| `attempts_per_part.length2_share` | **91.16%** | 0.9115646258503401 | 0.9115646258503401 |
| `step0_g5` (`term_unit:DimInfer`, the **0.0884** saving) | 0.0884 / 1.0000 | identical | identical |
| `latent_names`, `latent_dims`, `shape_signatures`, `support_N_*` | — | identical | identical |

`VISION_CODEBOOK_AXIS_RESULTS.md` needs **no retraction**. Its numbers stand.

The remaining movement in that document is **532 `sweeps` counter fields**
(`term_eval:*`, `cand_enum`, `where_evals`, `wall_ms_CONTAMINABLE`) and the 6
self-labelled `load_*_CONTAMINABLE` fields. The counter movement is the
DOWNSTREAM CONSEQUENCE of the same finding — the fixed engine runs the
re-decode, so it evaluates more Terms. **The counter the document actually
cites (`term_unit:DimInfer`) is NOT among the moved.**

---

## 3. EVERY OTHER DOCUMENT RE-RUN — and the noise set was DERIVED, not asserted (§13)

**I did not hand-write a list of "timing fields to ignore."** My first attempt
did exactly that, and it was INERT — it excluded **0 fields in every
comparison**, while real wall-clock noise flowed straight past it. Reported as
an error in §6.

The honest exclusion set FALLS OUT of a measurement: **run the FIX arm TWICE and
take the fields that differ between two runs of the SAME engine.** That is the
noise floor, measured on the instrument itself.

| document | fix vs revert | verdict |
|---|---|---|
| `genmint_measure.json` | **IDENTICAL, every field** | unmoved |
| `time_measure.json` | **IDENTICAL, every field** | unmoved |
| `depth_measure.json` | **IDENTICAL, every field** | unmoved |
| `stereo_measure.json` | **IDENTICAL, every field** | unmoved |
| `blink_measure.json` | 7 fields, ALL in the wall-clock `scaling` subtree, ALL inside the same-engine noise set | unmoved |
| `ground_measure.json` | 7 fields, ALL in the wall-clock `scaling` subtree, ALL inside the same-engine noise set | unmoved |
| `continuous_pose.json` | **IDENTICAL, every field** | unmoved |
| `deformation_measure.json` | **IDENTICAL, every field** | unmoved |
| `agnosia_measure.json` | 1 field: `seconds` | unmoved |
| `blob_cost.json` | 576 fields, leaf keys **exclusively** `graph_s` / `parse_s` / `read_s` / `ref_s` (144 each) | unmoved |
| **`codebook_axis.json`** | **`n_exact` ×5 + 532 sweep counters** | **MOVED — §2** |

**The fix-vs-revert differing PATHS on the six core documents are the SAME PATHS
that differ between two runs of the same engine.** Set difference: empty.

### 3.1 An instrument finding, free: `ground_measure`'s `scaling.PASS` is not reproducible

`scaling.PASS` read **True** as committed, **False** on fix replicate A, **True**
on fix replicate B, **True** on revert. It flips **between two runs of the SAME
ENGINE**. It is a wall-clock-threshold gate on a loaded machine, and it is
**not engine-attributable in either direction.** Reported, not fixed — it is
another rung's file (§11.4).

---

## 4. THE POWER ACCOUNTING — which nulls are EARNED and which are VACUOUS

**This is the section that makes the nulls mean anything.** Harmful-skip trigger
counts on the DEFECTIVE engine, per unmodified landed script:

| script | `run_rules` calls | **HARMFUL_SKIPS** | what its null is worth |
|---|---|---|---|
| `genmint_measure.py` | 415 | **5519** | **EARNED — the defect fired 5519 times and changed NOTHING** |
| `agnosia_measure.py` | 330 | **4106** | **EARNED** |
| `blob_cost_measure.py` | 144 | **864** | **EARNED** |
| `value_flood_measure.py` | 0 | **241** | trigger fired; document not compared (§5) |
| `continuous_pose_measure.py` | 513 | **238** | **EARNED** |
| `ground_measure.py` | 0 | **143** | **EARNED** (modulo §3.1) |
| `border_ownership_measure.py` | 0 | **26** | trigger fired; document not compared (§5) |
| `time_measure.py` | 410 | **0** | **VACUOUS — no power** |
| `depth_measure.py` | 410 | **0** | **VACUOUS — no power** |
| `stereo_measure.py` | 417 | **0** | **VACUOUS — no power** |
| `blink_measure.py` | 655 | **0** | **VACUOUS — no power** |
| `deformation_measure.py` | 125 | **0** | **VACUOUS — no power** |
| `codebook_axis_measure.py` | — | **UNMEASURED** (§6.4) | the one that MOVED |

**So the flat sentence "nothing moved except codebook_axis" is worth very
different amounts in different rows.** `genmint` is a genuinely powered null:
the defect's trigger fired **5519 times** while producing that document and the
document is bit-identical. **`time`, `depth`, `stereo`, `blink` are VACUOUS
nulls** — the defect never fired there, so their identity is guaranteed for a
trivial reason and licenses nothing.

### 4.1 A correction to my own pre-registration, scored honestly

I predicted **H1 (a number moves)** and I was **RIGHT** — but I predicted the
wrong counter and half the wrong direction:

- **RIGHT:** at least one in-family number moves; the mechanism is the
  `minted`-edge structural write racing an attr write; `sd_redecode` is
  implicated by name; the defective engine does LESS work.
- **WRONG:** I said *"I expect the movement to be in the MINT COUNTS"* and
  *"the REVERTED engine to mint FEWER."* **Mint counts are identical in every
  arm.** The mint is reached either way; it is the step AFTER the mint that the
  defect eats. I had the ladder's failure point off by one rung.
- **WRONG:** I predicted the five sd-loop measurements were the likely movers.
  **Four of the five have literally zero exposure.** The mover was
  `codebook_axis`, which my prereg table did not even list (§6.1).

### 4.2 The `time`/`depth`/`stereo`/`blink` zero is itself informative

All five load `shape_decode_loop`, yet `genmint` triggers 5519 times and the
other four trigger **zero**. Exposure is not a property of the seed — **it is a
property of the WORKLOAD's pass composition.** A static blast-radius enumeration
over seed files, however careful, cannot rank real exposure. The predecessor's
"316 race-constructible pairs" is confirmed as *"an upper bound on
constructibility, not observed breakage"* in the strongest possible way: within
ONE seed, four of five workloads have no exposure at all.

### 4.3 The oracle cannot see this defect

**212 passed / 10 skipped on BOTH engines.** The predecessor's "the oracle is
unmoved" bounded regression risk and nothing else — that is now measured, not
argued. A landed number moved while the oracle stayed green in both directions.

---

## 5. COVERAGE — stated as a FRACTION, per the brief

- **11 landed result documents compared** fix-vs-revert, of **147**
  `results/*.json` in the tree ⇒ **7.5%**.
- Of the 6 documents in the pre-registered core set, **6/6 run**. Of the
  extended set my own selection rule implied, **5 of 18 run** (§6.1).
- **Seeds measured, with unknown sinks:** every arm re-ran each landed script on
  ITS OWN declared block — 25000–25399 (genmint), 26100–26999 (time),
  27100–27499 (depth), 28000–28399 (stereo), 31100–31499 (blink),
  30000–30099 (ground), 68000–68999 (codebook_axis). **Block 91000–91999 is
  returned essentially unused** — a replication must not redraw, so my own block
  covered only the controls. `check_claim(91000, 91999)` = CLEAN, under its own
  two declared caveats (482 unresolved sink sites tree-wide are COUNTED, not
  discarded; a CLEAN result means "no collision DETECTED", never "none exists").
- **Race-pair coverage:** `shape_decode_loop` (34 of 316 pairs) is directly
  exercised; `vision_floor` (21) is covered only through the oracle.
  **`impasse_escalation` (41 — the LARGEST single exposure), `goal_derivation`
  (23), `nav_intent` (20), `grid_navigation` (16) are NOT MEASURED AT ALL** —
  no landed vision measurement boots them.
- **Python-installed rules: the predecessor's gap DID NOT BITE, and I can say
  why.** My static walk was of seed JSON, but the MOVEMENT was found by
  differential execution, which is agnostic to how a rule got installed. The
  gap survives for the *enumeration*, not for this *measurement*.

### What this licenses, and what it does not

**Licensed:** the fixpoint fix changes at least one landed number; the
mechanism is diagnosed; `VISION_CODEBOOK_AXIS_RESULTS.md`'s published claims are
unaffected; six further documents are unmoved with the defect *demonstrably
firing* in three of them.

**NOT licensed:** any statement about the 136 result documents I did not run,
about the four highest-exposure seeds, or about non-vision landed results. **A
document I did not execute is NOT REPORTED AS UNCHANGED — it is reported as NOT
RUN.** And §4 shows the danger concretely: four of my own re-runs looked like
clean nulls and had zero power.

---

## 6. WHAT I GOT WRONG

**6.1 I under-applied my own selection rule, and it cost me the headline's
neighbourhood.** The prereg says *"take EVERY landed result whose booted seed set
includes `shape_decode_loop`."* I then tabulated **five**. A mechanical
enumeration afterwards found **eighteen**. **`codebook_axis_measure.py` — the
one script whose number actually moved — is in the eighteen and not in the
five.** I found it only because I widened later. Writing a selection rule and
then hand-listing its members instead of computing them is the same disease as a
substring selector, and it nearly cost the entire result.

**6.2 My first power probe was inert, and it looked like a clean result.**
0 unsettled / 2307 calls. §1.2. I nearly logged a dead instrument as a powered
null; the only thing that stopped me was running it against the known-defective
reproduction *before* believing it.

**6.3 My hand-written timing-key filter never fired once.** `compare.py`'s
`TIMING_KEYS` excluded **0 fields in every single comparison** while genuine
wall-clock noise (`times_ms`, `ms`, `graph_s`, `seconds`) flowed straight past
it into the diff. A filter built from guessed key names covered guessed key
names. The empirically-derived same-engine noise set did all the actual work.
**Another instrument of mine that was decorative, discovered by checking whether
it had ever fired.**

**6.4 My harness copied `results/*.json` even when the script FAILED.**
`codebook_axis_identity` exited 2 and my runner still copied the pre-existing
COMMITTED file into the arm directory — where it would have compared IDENTICAL
against the other arm and been counted as coverage. **A failed run masquerading
as a passing comparison.** Caught by checking exit codes; that document is
excluded and reported as NOT RUN. The same defect left `codebook_axis_measure`'s
harmful-skip count unmeasured (it exits 2 under `runpy`), so §2's mechanism is
established by differential execution and status distribution, **not** by a
trigger count on that script.

**6.5 I killed my own wait loop twice with a self-matching `pgrep`.** `until !
pgrep -f rung7_vision_bench` matches the shell whose command line CONTAINS that
string — itself. It never exits. I then "verified nothing was running" with a
second command that self-matched the same way and told me the opposite of the
truth. Two consecutive process-state readings were artifacts of the reading.
**A guard that matches itself is not a guard** — §12, in a new costume, and I
wrote it twice in five minutes.

**6.6 I wrote a number into this document before running it.** An early draft
recorded "FIX arm: 6 passed" for the fixpoint test when I had run only the
provenance gate on that engine. I caught it on re-read and measured it (it is
genuinely 6 passed). It should never have been typed.

**6.7 The trigger counter's fallback boots a `Substrate` to read a global
static** — an instrument that runs the machinery it measures. I measured its
contribution (**0** on a no-op) rather than arguing it was small, but the design
is one I should not have shipped without that check, and the first version of it
silently reported `NO_SUBSTRATE_SEEN` for three scripts — **reading as blind
where the true answer was 143, 26 and 241.**

---

## 7. LEDGER ROW (for the supervisor to apply — I did not edit `VISION_PROTOCOL.md`)

| 91000–91999 CLAIMED, RETURNED ESSENTIALLY UNUSED (a replication must not redraw; the block covered controls only) | **FIXPOINT-RERUN — THE ANSWER IS YES, ONE LANDED NUMBER MOVES.** `results/codebook_axis.json` → `real_vision_codebook[*].alive.n_exact` is **`[0,0,0,0,0]` as landed and `[1,2,2,2,4]` under the fix** (4/4 replicates, perfect separation; the reverted engine reproduces the landed zeros exactly). **MECHANISM VERIFIED, AND IT IS THE ONE THE PREREG NAMED IN ADVANCE:** every observation ending at `status=minted` under the defect ends at `status=recognized` under the fix — the mint happens either way (`mints` unmoved), so what the defect ate is the ladder's LAST step, the post-mint RE-DECODE (`sd_redecode`, re-armed by `codebook_epoch`, one of the six rules reading the `minted` edge). **THE PUBLISHED CLAIMS OF THAT DOCUMENT ALL SURVIVE** — `mints` 1,2,2,2,4; `exhaustiveness` 1.0000; `attempts_per_part` 91.16%; the `term_unit:DimInfer` 0.0884 saving — every one unmoved; `VISION_CODEBOOK_AXIS_RESULTS.md` needs NO retraction. **WHAT MOVED IS THE ALIVENESS POSITIVE CONTROL INSIDE IT: an instrument that exists to prove the loop is not dead was reading zero for an ENGINE reason.** **THE POWER ACCOUNTING IS THE REST OF THE RESULT:** a trigger counter compiled into the reverted engine (positive-controlled — fires on the arm that yields the wrong answer, contributes 0 itself) shows `genmint` **5519** harmful skips / **agnosia 4106 / blob_cost 864 / value_flood 241 / continuous_pose 238 / ground 143 / border_ownership 26**, but **`time`, `depth`, `stereo`, `blink`, `deformation` = ZERO** — so **four of the five pre-registered sd-loop nulls are VACUOUS, not earned**, while `genmint`'s is genuinely powered (the defect fired 5519 times and the document is bit-identical). **EXPOSURE IS A PROPERTY OF THE WORKLOAD, NOT THE SEED: within ONE seed, four of five workloads have no exposure at all** — the strongest possible confirmation that "316 race-constructible pairs" bounds constructibility and not breakage. **THE ORACLE CANNOT SEE THIS DEFECT: 212 passed / 10 skipped on BOTH engines**, so the predecessor's "oracle unmoved" bounded regression risk and nothing more — now measured, not argued. **COVERAGE 11 of 147 result documents (7.5%); `impasse_escalation` (41 pairs, the largest), `goal_derivation` (23), `nav_intent` (20), `grid_navigation` (16) NOT MEASURED AT ALL.** **SIX ERRORS, ALL INSTRUMENT-SHAPED: I under-applied my OWN selection rule (tabulated 5 of the 18 scripts the rule selects — and the mover was in the missing 13); my first power probe was INERT and read a clean 0/2307 on the defective engine because the defect satisfies its predicate (the shipped test fails on the MARKER count, not `extra_steps`); my hand-written timing-key filter fired ZERO times in every comparison while real wall-clock noise flowed past it (the DERIVED same-engine noise set did all the work); my harness copied `results/*.json` even on FAILED runs, so a failed script would have compared identical-to-committed and counted as coverage; I killed my own wait loop twice with a self-matching `pgrep`; and I typed one number into the results doc before running it.** **FREE INSTRUMENT FINDING: `ground_measure`'s `scaling.PASS` flips between two runs of the SAME engine (True committed / False fix-A / True fix-B / True revert) — a wall-clock-threshold gate, not engine-attributable in either direction.** Gates: oracle **212/10 on both engines**; provenance **7 passed** on every engine, as its own step; fixpoint control **RED on revert (1 failed/5 passed), GREEN on fix (6 passed)**; restoring the fix rebuilt to `a1d350bbd23b` **bit-identically**. |
