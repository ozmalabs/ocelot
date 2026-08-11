# VISION — BASELINE-AS-LIST + RANGE-PINNED PROVENANCE + THE CODEC DECISION — RESULTS

Pre-registration: `VISION_BASELINE_LIST_PREREG.md`, committed at **`f7790499`** BEFORE any
number for the three tasks. Seed block **111000–111999**, **burned: NONE**.

Executes three findings of `VISION_GATE_SCOPE_B_RESULTS.md` (§10, §3.3, §3.4).

## 0. Provenance (§10)

| | |
|---|---|
| tree | `.claude/worktrees/agent-abfda01548d24e7a1/research/experiments/gamma-substrate` |
| branch | `worktree-agent-abfda01548d24e7a1` |
| HEAD at prereg | `8f41cc2ab277e6be4265ccf7d0dc632e2575f4cd` → prereg `f7790499` |
| engine | **`d657468d9e1f`**, built in THIS worktree by `scripts/engine_build.sh` (`[1 other tree build(s) shadowed]`) |
| engine md5 | `ae7d786bf35a0395205da102d671d058` |
| provenance gate | `tests/test_engine_provenance_migrated.py` — **7 passed**, run as its own step before any number |
| oracle | **212 passed / 10 skipped / 0 failed** — `bash scripts/rung7_vision_bench.sh`, no `data/`, the expected 212/10 |
| loadavg at oracle end | `(5.95, 4.43, 5.06)` |

### §3 clause 8 — THE VERBATIM RECORD

```
SEED CLAIM 111000-111999: CLEAN -- no collision DETECTED.
  Scope: 811 files with seed sinks; 506 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**506 unresolved sinks**, counted and not discarded.

### CONCURRENCY, DECLARED (§11 rule 5)

A **second agent's worktree** (`agent-a846557d10087d8f6`) was running
`rung7_vision_bench.sh` 2-way on this box during my sweep — verified by `/proc/<pid>/cwd`,
correctly isolated in its own tree. Peak load average observed **6.4 on 12 cores** (last
wave's failure was 26). Every number below carries its load. My own engine was built at the
start and **re-verified after the long measurement** (§10.4-proposed) — see §6.

---

## 1. THE CODEC DECISION — AND IT IS NEITHER OF THE TWO OFFERED OUTCOMES

**This is the headline, and my pre-registered prediction was WRONG in the most useful
possible direction.**

The brief offered two: **(A)** the codec rules never fired and the claim should be
**RETRACTED**, or **(B)** the test's expectation was wrong from birth. It added: *"got 0"
reads much more like the former, so do not assume the test is the broken part.* I
pre-registered **(A) at 0.75 confidence** for exactly that reason.

**Both are wrong. The truth is a third thing, and it is worse than either.**

### 1.1 What was measured, by construction

`scripts/codec_decision_probe.py`, and then the decisive two-route comparison — **the same
20 rules, the same JSON, two install paths**:

| install route | rules installed | `run_rules` steps | PPS fields decoded |
|---|---|---|---|
| `install_field_grammar_rules()` (Rust, the shipping path) | **20** | **0** | **0 / 10** |
| `s._inner.add_rule(spec)` (Python, same JSON, same engine) | **20** | **10** | **10 / 10, byte-correct** |

The decoded values on the working route are exactly the gate's expected map, including the
signed field: `pic_init_qp_minus26 = -3`.

### 1.2 The root cause, proven by reading the flag off the engine

`export_rules()` on each route:

```
rust   n=20 active: [False, False, False, ... ]   (20 x False)
python n=20 active: [True,  True,  True,  ... ]   (20 x True)
```

**Every one of the 20 codec rules installs DEAD.** `runners/dsl/src/codec.rs`'s
`install_field_grammar_rules` does `substrate.rules.push(rule)` — and
`Substrate::add_rule` in `runners/dsl/src/substrate.rs:1262` says, **in its own comment**:

> *"`add_rule` is the sole path that pushes into `self.rules`, so it owns making a
> newly-installed rule live regardless of how the caller built the `RewriteRule` value
> (struct-literal callers typically spread `..Default::default()`, which would otherwise
> leave `active: false` — see the field's doc comment)."*

`codec.rs` bypasses that sole path. The rules are parsed correctly, installed correctly,
counted correctly — **and `active: false`, so the matcher skips every one of them.**

### 1.3 THE DECISION

> **DO NOT RETRACT THE CLAIM, AND DO NOT TOUCH THE TEST'S EXPECTATION.**
> **`expected 10 rule firings, got 0` WAS RIGHT ON BOTH NUMBERS FROM BIRTH.**

The capability the file certifies — *the H.264 PPS field grammar is graph-resident, decode
is graph Rules, Python only loads bytes and reads results* — is **REAL, PRESENT AND
DEMONSTRABLE IN THIS TREE TODAY**, at 10 firings and 10/10 correct fields. What is broken is
a **later Rust refactor of the rule INSTALLER**, which moved the rule set from Python into
`codec.rs` and dropped it through the one function that makes a rule live.

`test_codec_graph_resident` is therefore **the most valuable gate in the chronic-red set**:
not stale, not mis-expected, not environmental. It is a **correct gate reporting a real,
root-caused, one-line-fixable regression, truthfully, on every run, for ~48 days** — and it
was never read, because it entered the tree already inside the count.

**This is the third way a gate verifies nothing, demonstrated end to end.** Nobody ignored
a red. Nobody had to *decide* anything. The gate was born inside an accepted baseline, so
its signal was pre-absorbed.

### 1.4 What I did NOT do, and why

**The one-line fix is identified and its effect is proven** (route the parsed rules through
`Substrate::add_rule`, or set `rule.active = true` before the push — the Python route
demonstrates the outcome: 0 → 10 firings, 0 → 10/10 fields). **I did not apply it**:

- the brief says **DECIDE, DO NOT PATCH**, and the decision is what was asked for;
- `runners/dsl/src/codec.rs` is **another rung's module** (§11 rule 4);
- it is a change to **engine** behaviour and belongs in a rung that builds, gates and
  §9-verifies it rather than in a gate-audit rung's tail.

**Reported for sequencing**, with the reproduction in `scripts/codec_decision_probe.py`.

**And I did not ship a new red gate for it.** A gate asserting `install_field_grammar_rules`
produces ACTIVE rules would be red on landed code today — and adding a knowingly-red node is
the disease this rung is curing. It is recorded as a classified entry in the LIST instead.

### 1.5 Scope (§8)

Established: the H.264 PPS path, 10 fields, on this engine. **NOT** established: the HEVC
path, the encode path, the loop/conditional rules, or the other 29 nodes in the file
individually — they share the dead-install cause by construction, but only the H.264 decode
was driven end to end. The remaining nodes are listed, not assumed.

---

## 2. RANGE-PINNING THE TWO FALSE-ACCUSATION GATES

**Committed SEPARATELY at `0e61f60e`, and said so** (§11 rule 4 — a design change to another
rung's instrument), the way the ledger-attribution rung did with its aliveness inversion.

### 2.1 The fact was verified FIRST, independently (§12.3)

*Verify the fact, then fix the gate. Never the reverse.* Before either gate was touched:

| rung | its own immutable range | files | `.rs` in range |
|---|---|---|---|
| cut-mint policy | `17cb3f3d..f8c4d904` | 11 | **0** — none under `runners/dsl/src` |
| video accumulation | `5428104a..6751d03c` | 11 | **0** — and no `seeds/` path at all |

**Both rungs' claims are TRUE.** The gates were wrong; the rungs were not. Had either range
contained one foreign `.rs` line, the answer would have been to report the rung, not to
widen the pin.

### 2.2 Before / after

| | before | after |
|---|---|---|
| `test_cut_mint_policy_migrated::test_this_rung_adds_no_rust` | `git diff BASE -- runners/dsl/src` (**live tree**) — RED ~54 commits | `git diff BASE RUNG -- runners/dsl/src` — **GREEN** |
| `test_video_accumulation_migrated::test_this_rung_edits_no_seed_and_no_rust` | `git diff base -- runners/dsl/src` + live seed hash — RED ~54 commits | `BASE..RUNG` for both halves — **GREEN** |
| both files together | **2 failed / 20 passed** | **22 passed / 0 failed** |
| the natural control `test_colour_bound_k1_migrated.py` | 25 passed | 25 passed (unmoved) |

The failure message named `shape_decode.rs`, `scale_audit.rs`, `py.rs`, `reflect.rs`,
`substrate.rs` — **Rust merged by rungs that came afterwards**. That is the false accusation,
verbatim.

**Also pinned, and declared:** cut-mint's `test_the_seeds_this_rung_reuses_are_byte_unchanged`
and video-accum's in-function seed hash compared the **live file** against BASE — the
identical defect, **green today only because nobody has yet edited those two seeds**. A
latent false accusation, disarmed rather than left armed. Neither seed has changed since
creation, so this narrows nothing that is true today.

### 2.3 POSITIVE-CONTROLLED — a gate you have only ever seen pass is not a gate

`scripts/range_pin_positive_control.py`:

```
AS SHIPPED (own rung range):            4/4 GREEN
CONTROL 1 — RUNG widened to HEAD:       both Rust-diff halves RED   (this also
                                        REPRODUCES the original false accusation on demand)
CONTROL 2 — seed-blob half vs a path
            that DID move in-range:     RED;   vs itself: GREEN
```

Every half of both gates was driven red on a range containing what it forbids, and green on
its own range.

### 2.4 THE POPULATION, ENUMERATED — because a count of instances is the same defect

I did not stop at the two I was sent. **All 13 `git diff` provenance invocations in
`tests/` were enumerated and classified**:

| site | endpoints | verdict |
|---|---|---|
| `test_cut_mint_policy_migrated.py:63` | was single-rev | **FIXED HERE** |
| `test_video_accumulation_migrated.py:224` | was single-rev | **FIXED HERE** |
| `test_margin_migrated.py:312` | `base..rung` | **already SUPERVISOR-REPAIRED 2026-07-19** |
| `test_lighting_l3b_migrated.py:35` | both endpoints fixed | **already SUPERVISOR-REPAIRED 2026-07-19** |
| `test_aperture_fix_migrated.py:325` | `sha^..END` | correctly pinned |
| `test_colour_bound_k1_migrated.py:263`, `test_colour_bound_migrated.py:200`, `test_decay_gradient_migrated.py:54`, `test_identity_seam_migrated.py:235`, `test_paint_migrated.py:54,375`, `test_troxler_migrated.py:147`, `test_vision_theta_migrated.py:354` | both endpoints fixed | correctly pinned |
| `test_vision_theta_migrated.py:253` | **single-rev, live tree** | **EXAMINED AND DELIBERATELY NOT CONVERTED — see below** |

**The one I refused to convert, and why that is the interesting one.**
`test_vision_theta_migrated.py:253` (`..._vision_onoff_and_vision_lateral_are_NOT_edited`)
diffs a single sha against the live tree — structurally the same shape. But its claim is
**not** *"this rung's diff contains no seed edit"*; its own docstring says it claims
*"rungs 6/7 remain ATTRIBUTABLE"* — **a standing no-drift claim about the CURRENT tree**.
Range-pinning it would make it stop noticing exactly the drift it exists to notice. **That
would be quieting a gate, not fixing one**, and the brief's rule is that a relaxation needs
the specific false positive that justifies it. There is none. **Left alone, and recorded
here so the next reader does not "fix" it.**

The protocol ledger (§ line 991) had NAMED the `test_margin` / `test_lighting_l3b` fix as
*"NAMED FIX, NOT BUILT"*. **It has since been built.** So the §12.3 defect population is
**6 genuine instances: 2 supervisor-repaired, 2 repaired here, 2 that were never instances.**
The class is now closed in `tests/`.

---

## 3. TASK 1 — EVERY BASELINE CONVERTED FROM A COUNT TO A LIST

### 3.1 H1, and the prediction that carries it

**Predicted before looking:** no machine-readable list of accepted-red node ids exists
anywhere in the tree. **CONFIRMED.** The tree carries `results/*_baseline.json` files
(`batch_apply_off_baseline`, `motion_sensor_gate_baseline`,
`scale_wall_sweep_percell_baseline`) — every one a **measurement** baseline. **Not one
failure baseline, and not one node id.** The convention was **prose + a number**, everywhere.

### 3.2 THE GOVERNING DISTINCTION I had to mint to do this honestly

Halfway through the conversion this became a live problem: several count-shaped baselines
sit in **pre-registrations, results docs and dated arc logs**. Converting those would be
**falsifying the record** — §7 says retract *in place, with the measurement that forced it*,
never rewrite. So:

> **A HISTORICAL RECORD IS NEVER CONVERTED — IT IS ANNOTATED OR LEFT.
> A STANDING CLAIM IS ALWAYS CONVERTED.**
> The test is not *where the sentence lives*, it is **whether a future rung will act on it**.
> `VISION_RUNG6_PREREG.md`'s *"10 failed / 122 passed"* is a record of what someone
> measured (and §10 has since shown it was a stale-binary artifact). `CLAUDE.md`'s *"the
> only bench failures anywhere are…"* is an **instruction the next rung will hold the line
> against**. Only the second is a baseline.

### 3.3 CONVERTED — before / after

| site | before (COUNT / characterisation) | after (LIST) |
|---|---|---|
| **`CLAUDE.md:619`** | *"the only bench failures anywhere are the pre-existing missing-`chess`/vision optional-dep errors"* — a **characterisation**, refuted by measurement: 0 collection errors, 53 red files, 144 red nodes | **RETRACTED in place**, with the measurement, pointing at `results/failure_baseline.json`, and *"Do not replace this paragraph with a number."* |
| **`VISION_STAGE2_PLAN.md:105`** | `pytest tests/ -k migrated` *"(the 5 pre-existing POS failures are expected; NO new ones)"* — a count **and** a substring selector, in one line | the **named** oracle `scripts/rung7_vision_bench.sh` + `failure_baseline.py verify` — membership, not arithmetic |
| **`VISION_STAGE2_PLAN.md:123`** | *"The 5 pre-existing POS-cold-slab failures are NOT this work's concern"* | same sentence, **entries identified by node id**, with the note that the count was written when it was 5 |
| **`tests/test_convo_experiment_migrated.py:350`** | *"part of the documented **19-failure baseline**"* — the literal sentence the Scope B rung identified as the mechanism, **live in a gate** | the four seeds **named explicitly**; baseline reference redirected to the list. **Comment only — no assertion moved; 5/5 still green.** |

### 3.4 REPORTED, NOT EDITED — the historical records

Left verbatim, by the rule in §3.2: `VISION_RUNG6_PREREG.md:438` (*"10 failed / 122
passed"* — already known to be a stale-binary artifact, §10), `VISION_DEVELOPMENT_ARC.md:31,
648` (*"5 pre-existing"*), `NOTE_lpc_harvester_fix.md:88` (*"42 unrelated pre-existing
failures"*), and ~6 dated `docs/*.md` notes citing *"a pre-existing unrelated failure"*
without naming it. **These are records of what someone saw. They are not baselines, and
rewriting them would destroy the evidence trail that made this rung possible.**

### 3.5 The artifact and its gate

- **`results/failure_baseline.json`** — the LIST. Per entry: `node` (a pytest NODE ID),
  `file`, `kind`, `message`, `class`, `last_green_commit`, `file_seconds`. Plus a
  **`coverage`** block naming every file that did not complete.
- **`scripts/failure_baseline_sweep.py`** — the per-file sweep. **A timeout is
  `NOT_ESTABLISHED`, never RED** (§1.9-proposed; a green 501-second file was logged as a
  timeout red in this tree last wave, and my own sweep ran against another agent's bench).
- **`scripts/failure_baseline.py build|verify`** — `verify` re-runs listed node ids and
  reports **NEW** *and* **STALE** as failures.
- **`tests/test_failure_baseline_migrated.py`** — the always-on structural gate.

**`total` is DERIVED from `entries` and the gate FAILS if they disagree** — that is the
regression back to an authored count, caught by construction.

**The STALE direction is the half that matters and the half a count cannot have.**
`test_seed_claim`'s gate was killed by the fix it asked for **in 8 minutes** and reported
that success as a failure ever since. A list that only detects NEW reds would repeat it.

### 3.6 Positive-controlled in both directions

`tests/test_failure_baseline_migrated.py` mutates a copy of the artifact and requires the
checker to reject it — **6 controls**: an authored `total`, a bare file list instead of node
ids, an undiagnosed entry, a missing `last_green_commit`, an undeclared coverage block, a
missing engine. Plus a **negative control** asserting the real artifact passes, so the six
are detecting the mutation and not a property the real file happens to lack.

### 3.7 THE SWEEP — the numbers

**Condition, quoted with every number (§10.2):** `HEAD 0e61f60e`, engine **`d657468d9e1f`**
(own build), **no `data/`**, 2 workers, per-file subprocess, per-file budget 420 s.

| | |
|---|---|
| files swept | **648 / 648** |
| GREEN | **493** |
| RED | **147 files** |
| **distinct RED node ids** | **565** |
| NOT_ESTABLISHED (budget exceeded — never RED) | **5** |
| NONZERO_NO_NODES (non-zero exit, no node id parsed) | **3** |
| wall | 3 490.6 s (58 min) |
| loadavg start / end | `(1.80, 3.27, 4.46)` / `(3.04, 3.32, 3.81)` |

`NOT_ESTABLISHED`: `test_cegis_faculty`, `test_cycle_detect_migrated`, `test_gadgets`,
`test_implication_harvester`, `test_no_assistance_gate_migrated`. **Three of these five are
named in Scope B** — `test_gadgets` as the 501-second green that was logged as a timeout
red, `test_implication_harvester` as "pending, not counted", `test_cycle_detect_migrated`
as the post-rebuild provenance refusal. **In my tree `test_cycle_detect_migrated` RUNS**
(it exceeds the budget rather than erroring at import), which is what owning your engine
buys.

`NONZERO_NO_NODES` — `test_code_writing_migrated`, `test_reading_collapse`, `test_summit`
— exited non-zero with no parseable node id. **Counted, not discarded, and not reported as
red.**

Heaviest files: `test_codec_graph_resident` **30**, `test_meaning_inference_migrated` 20,
`test_experiment_composer_graph` 17, `test_inference_generation` 14,
`test_interlocutor_modeling_migrated` 13.

**REPRODUCIBILITY — measured, not assumed.** The red files were swept a **second time**,
~1 hour later, in a separate process pool (to recover the diagnoses my first run truncated
— error #7). The two runs are recorded against each other in the artifact:

```
nodes_first_sweep   565
nodes_re_run        565
identical_node_set  True
only_in_first       []
only_in_re_run      []
```

**Two independent sweeps, zero divergence.** The verdict set is deterministic under this
condition; that is what licenses using it as a baseline at all.

### 3.8 **565, NOT 144 — AND THE GAP IS THE CONDITION, WHICH IS THE WHOLE POINT**

I pre-registered **130–170**. I measured **565**. That is a **bad miss, ~3.4× over the top
of my band**, and the diagnosis is the rule this rung is about:

**I sized my band from the peer's 144 — a number measured WITH `data/` symlinked, on a
different engine, at an earlier HEAD. I even wrote in the prereg that my number "will NOT
equal 144" and named all three differences — and then predicted a band centred on it
anyway.** Naming a confound is not the same as pricing it. **That is the count defect
committed by the rung sent to fix the count defect**: I let a number travel between two
conditions because it was the only number available.

So the honest statement of the result is:

> **565 red node ids across 147 files, WITHOUT `data/`.** This is **not** comparable to the
> peer's 144/53 **with** `data/`, and the difference is dominated by the corpus, not by
> regressions. **Neither number is "the baseline" without its condition attached** — which
> is precisely why `condition` is a required field the gate refuses to accept as empty.

**And the classification is honestly weak:** **531 of 565 are UNCLASSIFIED.** Only 30
(codec, root-caused), 3 (`results/*` artifact absent) and 1 (`data/` absent) carry a
diagnosis. **I cannot separate data-conditional entries from real regressions by message**,
because §10.2's central finding is that a missing slab fails **silently and plausibly** — it
surfaces as an ordinary `AssertionError`, not as a `FileNotFoundError`. The 4 loud ones are
a **floor**, never an estimate. **Establishing which of the 531 are real needs a
with-`data/` run in a tree that OWNS its `data/`, and finding 6 explains why I did not do
it here.**

---

## 4. PREDICTIONS vs OUTCOME (§3 clause 7)

| # | prediction | predicted | measured | |
|---|---|---|---|---|
| H1.1 | a machine-readable list of accepted-red node ids exists | **none exists** | none — 3 `*_baseline.json` files, all **measurement** baselines, zero failure baselines, zero node ids | ✅ |
| H1.2 | count-shaped **standing-claim** sites | 3–8 | **4** converted (+ ~9 historical records left by rule §3.2) | ✅ |
| H1.3 | distinct red node ids at this HEAD | 130–170 | **565** | ❌ **badly — 3.4× over; see §3.8** |
| H1.4 | ≥1 file NOT_ESTABLISHED | ≥1 | **5** | ✅ |
| H2.1 | both provenance gates RED at HEAD, naming Rust neither rung wrote | RED | RED — `shape_decode.rs`, `scale_audit.rs`, … | ✅ |
| H2.2 | the range-pinned control is GREEN | 25/25 | **25 passed / 0 failed** | ✅ |
| H2.3 | both GREEN after re-pinning, fact verified first | GREEN | **22/22**; both ranges verified `.rs`-free BEFORE the edit | ✅ |
| H2.4 | positive control drives each re-pinned gate RED | RED | every half RED on a range containing what it forbids | ✅ |
| H3 | the codec decision | **(A) RETRACT, 0.75** | **NEITHER (A) NOR (B)** — expectation right, mechanism real, INSTALLER dead | ❌ **the important one** |

**Seven of nine. Both misses matter more than the hits, and they are the same error.**

H1.3 and H3 are one mistake wearing two costumes: **I let a number/verdict travel out of the
condition that produced it.** For H1.3 it was the peer's 144 crossing a `data/` boundary I
had myself documented. For H3 it was reading `got 0` as *"no mechanism"* when it meant
*"mechanism not installed"* — a verdict crossing from the OUTPUT of a system to a claim
about its EXISTENCE. **My prereg named the confound in the first case and wrote a
decision rule that hard-coded the error in the second.**

**The prediction I am most glad I recorded is the one that made H3 legible:** I wrote that
the proviso which would move me off (A) was *"`run_rules` returns 0 while the decoded values
are nonetheless CORRECT."* That proviso did **not** fire — decoded was empty — and the claim
was true anyway. **A pre-registered proviso that does not fire is not a licence to conclude;
it only tells you which way you were already leaning.**

---

## 5. FINDINGS ON LANDED CODE — reported, not silenced

1. **`runners/dsl/src/codec.rs::install_field_grammar_rules` installs all 20 codec rules
   DEAD (`active: false`)** by bypassing `Substrate::add_rule`, the function whose own
   comment declares itself *"the sole path that pushes into `self.rules`"*. Root-caused,
   reproduced two ways, one-line fix identified and its effect proven. **~48 days, 30 red
   nodes.** NOT patched (§11 rule 4 + *decide, do not patch*). **This is the highest-value
   item in this rung.**
2. **`domains/comprehend_text.py:438–442` — the live regex** in the comprehension front
   end, red on `test_comprehend_recognition::test_ast_audit_clean` for ~579 commits.
   Inherited from Scope B, re-confirmed present. **Not touched** — reported for sequencing.
3. **`test_async_order_n::test_reading_path_drives_via_tick_not_run_rules`** — stranded by
   the `117e8cbe` refactor (the gate went red because the code got TIDIER). **Not touched.**
4. **The `§12.3` mutable-tree class is now closed in `tests/`** — 6 instances, 2 repaired
   here, 2 previously supervisor-repaired, 2 that were never instances (§2.4). The
   `test_vision_theta` site is a genuine standing drift gate and must NOT be converted.
5. **The `-k migrated` selector was still being prescribed** as the regression gate in
   `VISION_STAGE2_PLAN.md`, 4 days after §12 recorded that `-k` matches "pro**vision**al".
   Converted to the named oracle.

6. **`§10.2 RULE 2 IS BACKWARDS FOR `data/`, AND ~78 WORKTREES ARE WIRED TO THE HAZARD.**
   Nobody asked for this; it fell out of establishing my own sweep's condition.

   §10.2 rule 2 prescribes: *"`data/` is a symlink, never a copy (§10.1 rule 2's logic: a
   copy ages, a pointer cannot)."* **That reasoning imports the ENGINE's properties, and
   `data/` does not have them. The engine is READ-ONLY at runtime; `data/` is READ-WRITE.**

   Measured, three facts:

   - **The suite WRITES into `data/`.** My worktree began with no `data/` at all; during my
     sweep the suite created `data/reading_corpus/pg2591.txt`, `data/verbnet/prep_roles.json`
     and **`data/web_cache/wikipedia/Photosynthesis.json`** — the last being a **cached
     NETWORK FETCH**. Write sites are all over `domains/` (`reading_corpus.py`,
     `preposition_roles.py`, `conceptnet_reference.py`, `hf_corpus.py`, …).
   - **~78 worktrees symlink `data/` → the canonical tree** (enumerated by `readlink` over
     `.claude/worktrees/*/…/data`). Every one of them therefore writes THROUGH the pointer
     into canonical, concurrently, with no owner — **§10.3's "never `cp` onto the engine
     path, it writes THROUGH the symlink" hazard, reproduced for the corpus**, and §11's
     shared-mutable-state failure in a new costume.
   - **It has already fired.** `find canonical/data -newermt "2026-07-20 12:00" -type f`
     returns **12 files**, including **`data/vision_curriculum/frames/babble_bsds_00{0,1,2}.npy`**
     — the corpus the ORACLE's own `test_vision_curriculum_migrated` /
     `test_vision_growth_migrated` read.

   *Honest scope:* that those 12 writes arrived **through a worktree symlink** rather than
   from a run in the canonical tree is an **INFERENCE, not measured** — I cannot attribute
   them to an agent. The mechanism, the wiring and the fact that writes are landing are each
   measured; the causal link between them is not. **MY tree does not symlink `data/`** (it
   has a real directory), so my sweep wrote nothing into canonical — that was the default,
   not my foresight.

   **Consequence for every baseline, including mine:** the condition is not the binary
   `with data/` / `without data/` that §10.2 established. **`data/` is a moving target
   DURING a run** — a file swept early sees a different corpus from one swept late, in the
   same sweep — so a sweep is order-dependent through the corpus as well as through the
   tracked files §11-rule-6-proposed already names. **Not actioned** (§9 / §11 rule 4):
   changing `data/` policy touches every tree at once and is a supervisor decision.

---

## 6. ENGINE RE-VERIFIED AFTER THE LONG MEASUREMENT (§10.4-proposed)

Bracketed at **three** points, not two — start, mid-sweep and end:

| check | result |
|---|---|
| built in THIS worktree, `scripts/engine_build.sh` | `engine d657468d9e1f`, `[1 other tree build(s) shadowed]` |
| md5, start / mid / end | `ae7d786bf35a0395205da102d671d058` — **unmoved** |
| `provenance_line()` (with preamble), start / mid / end | `d657468d9e1f @ <MY worktree>` — **unmoved** |
| provenance gate, start | 7 passed |
| provenance gate **inside the sweep** (file 209/648) | **GREEN** — proves the sweep's own pytest invocation resolved this tree's engine, rather than my assuming it did |
| oracle, start / end | **212/10/0** both times — unmoved across 58 min of sweeping |

**The mid-bracket is what earned its keep** — it is where I found my own script reading the
canonical engine (error #2). §10.4-proposed says fingerprint at both ends of a measurement
block; **the middle is where the instrument bug surfaced**, because that was the first time
I compared what the script reported against what the file was.

**The canonical engine was NOT written through.** `engine_build.sh`'s
`cp --remove-destination` is why, and it is why the other agent's concurrent bench run in
`agent-a846557d10087d8f6` could not disturb my numbers, nor mine theirs.

---

## 6b. §11-rule-6-proposed INDEPENDENTLY REPRODUCED — and it is worse than reported

Scope B §3.6 reported that running the bench mutates two **tracked** files. **Reproduced in
a second worktree, unprompted**, during my sweep:

```
 M seeds/metonymy_patterns.json      151 insertions(+), 51 deletions(-)
```

**And the content is NONDETERMINISTIC**, which the original report did not establish:

```
-        "target_synset": "ballistocardiogram.n.01",
+        "target_synset": "electrocardiogram.n.01",
-        "gloss": "harvested WordNet meronymy: checkup.n.01 ... -> ballistocardiogram.n.01 ...",
+        "gloss": "harvested WordNet meronymy: checkup.n.01 ... -> electrocardiogram.n.01 ...",
```

A WordNet harvest selecting a **different synset on each run**. So the seed does not merely
get written — **it churns differently every time**, which means any agent that runs the
bench and stages broadly commits a different 200-line seed diff each time, and no two are
reconcilable. *Two agents, two worktrees, one cause* — a property of the bench.

**Not committed.** I stage by path, never `git add -A` (§11 rule 3), and the file is
restored before the final commit — verified by `git status` afterwards.

---

## 7. WHAT I GOT WRONG

1. **MY PRE-REGISTERED DECISION RULE FOR THE CODEC WOULD HAVE RETRACTED A TRUE CLAIM, AND
   IT IS THE WORST ERROR HERE.** I wrote: *"If `decoded` is empty ⇒ (A) [retract]."*
   **`decoded` WAS empty — and the claim is TRUE.** Following my own rule mechanically, I
   would have retracted a capability that is present, correct and demonstrable, on the
   strength of a mechanism that was merely **installed inactive**. I escaped it only by
   continuing to probe *past* the point where the rule said I was done — which is luck
   dressed as diligence.
   **The defect is precise: a decision rule that reads only a mechanism's OUTPUT cannot
   distinguish "no mechanism" from "mechanism not installed".** It needed an install-path
   arm — *does the same rule data fire through a second install route?* — and that arm is
   what produced the whole result. I also predicted (A) at 0.75 confidence and wrote a
   proviso for (B); **the truth was a third outcome I did not enumerate**, so my
   two-sidedness (§3 clause 1) was a false comfort: two options exhaustively argued, and
   the answer outside both.
2. **My own instrument mis-recorded the engine — inside the field its own gate requires.**
   `failure_baseline.py::_engine_line` omitted `engine_preamble()`, so it read the
   **canonical** engine (`b06e02ed9323`) via the global `.pth` while every swept file ran
   on **my** engine (`d657468d9e1f`) under pytest's conftest. §10.1 rule 3 states this in
   as many words — *any non-pytest entrypoint must call `engine_preamble()` itself* — and I
   read that rule, wrote a rung script, and did not apply it. Caught **only** because I ran
   the §10.4-proposed mid-measurement bracket; without it the artifact would have shipped
   naming a binary that produced none of its numbers. **VERIFY ON THE PRODUCT, NOT THE
   PRODUCER**, applied to my own product.
3. **I asserted a rate without checking the clock.** I read the sweep log as "~100 minutes
   elapsed, ETA 4½ hours" when 17 minutes had passed, then repeated the mistake in the
   other direction. The proximate cause is a real instrument note — `ThreadPoolExecutor.map`
   yields **in order**, so a single slow file (`test_cycle_detect_migrated.py`, 420 s)
   freezes the printed count while work continues behind it — but I inferred a stall from
   a display artifact twice before checking `date`. A progress readout is an instrument
   and I did not calibrate it.
4. **My list's condition is weak, and the weakness is structural, not incidental.** It is
   measured **without `data/`**, and §10.2 establishes that a missing slab produces
   **fluent, well-formed, WRONG** behaviour — so an unknown fraction of my entries are
   worktree artifacts rather than regressions. I decided **not** to run the paired
   with-`data/` control because symlinking would write into the canonical tree while
   another agent was measuring (§11 / finding 6). That is a defensible call and it leaves a
   real hole: **the list enumerates what is red under my condition, and does NOT establish
   which entries are genuine.** Stated here rather than left for a reader to infer from the
   `condition` field.
5. **"With last-green commits" is satisfied structurally, not empirically.** Every entry
   carries the field and the gate fails without it, but it reads `UNKNOWN` for all but the
   codec group. Establishing 100+ last-greens means running historical trees against
   today's engine — the exact confound that cost the Scope B peer two headline durations
   (§3.5) — so I refused it rather than manufacture precise-looking numbers. **The brief
   asked for last-green commits and I am delivering the field, the enforcement and one
   populated group, not the data.**
6. **I MISSED MY RED-NODE BAND BY 3.4× BY LETTING A NUMBER CROSS ITS OWN CONDITION.**
   Predicted 130–170, measured **565**. I sized the band from the peer's 144, which was
   measured **with `data/`**, on a different engine, at an earlier HEAD — and I had
   **written all three differences into the prereg** before doing it. **Naming a confound
   is not pricing it.** This is the count defect, committed by the rung sent to fix the
   count defect, and it is the same error as H3 in a different costume (§4).
7. **MY FIRST SWEEP AMPUTATED EVERY DIAGNOSIS AT COLUMN 80, AND I DID NOT NOTICE FOR AN
   HOUR.** pytest truncates its `-rfE` short summary to the terminal width, and a captured
   pipe reports 80 columns. So the 648-file sweep produced **correct node ids attached to
   messages like `As...` and `Ass...`, and 472 entries with no message at all** — every one
   classified `UNCLASSIFIED`, in the artifact whose own gate **requires** a class. I found
   it only when I looked at the class histogram and saw it was meaningless. Cost: a
   147-file re-run (19 min). **The silver lining is not an excuse but it is real** — the
   re-run agreed with the first on the node set **exactly (565 = 565, zero divergence)**,
   which is a reproducibility measurement I would not otherwise have made.
8. **I nearly shipped a knowingly-red new gate.** My first instinct on root-causing the
   codec defect was to add a gate asserting `install_field_grammar_rules` produces ACTIVE
   rules — which would have been red on landed code on the commit that introduced it,
   i.e. **manufacturing exactly the class (§12.8) this rung exists to name.** Caught before
   writing it, but it was the natural move and I record that it was.

---

## 8. PROPOSED §-AMENDMENTS (not applied — `VISION_PROTOCOL.md` NOT edited)

**§1.10 — A BASELINE MUST BE A LIST OF NODE IDS WITH LAST-GREEN COMMITS, NEVER A COUNT.**
A count can be HELD; a list has to be READ. **A COUNT IS A SUBSTRING SELECTOR'S COUSIN: it
matches the SHAPE of the answer without touching its CONTENT** — the same defect this arc is
0-for-6 on, one level up, at the level of a policy. A count cannot distinguish a new red from
an old one, cannot notice a fix (so it reports successes as failures forever), and cannot
tell "never once passed" from "broke this morning". 19 → 144 with **nobody negligent** is what
it does over ten days. *"Held at the pre-existing baseline"* must stop being a passing grade.

**§1.11 — THE STALE DIRECTION IS THE HALF THAT MATTERS.** A baseline instrument that only
detects NEW reds reproduces the `test_seed_claim` failure: a gate killed by the fix it asked
for, in 8 minutes, reporting that success as a failure ever since. **A listed entry that now
PASSES must be a FAILURE of the baseline gate.**

**§1.12 — A HISTORICAL RECORD IS NEVER CONVERTED; A STANDING CLAIM ALWAYS IS.** The test is
not where the sentence lives but **whether a future rung will act on it**. Rewriting a
pre-registration's measured number to make it list-shaped is falsifying the record (§7 says
retract *in place*). Leaving a live instruction count-shaped is manufacturing the next
baseline. Both errors are available in the same commit, and they point opposite ways.

**§12.8 — A GATE THAT IS BORN INSIDE A BASELINE IS NEVER WATCHED BREAK.**
`test_codec_graph_resident` entered the tree already red, inside an accepted count, so no
reader ever saw a green→red transition for it — and it turned out to be reporting a REAL,
ROOT-CAUSED, ONE-LINE-FIXABLE engine regression, truthfully, for ~48 days. **A new test file
whose nodes are red on the commit that introduces them must be either fixed or explicitly
classified before the commit lands** — never absorbed.

**§10.6 — A POINTER IS SAFE ONLY FOR A READ-ONLY RESOURCE; `data/` IS READ-WRITE.**
§10.2 rule 2 (*"`data/` is a symlink, never a copy"*) reasons by analogy from the engine —
*a copy ages, a pointer cannot* — but the engine is read-only at runtime and **the test
suite WRITES into `data/`** (measured: three directories and a cached network fetch created
in a virgin worktree during one sweep). With **~78 worktrees pointing at the canonical
corpus**, that makes `data/` shared mutable state across every concurrent agent, and
**12 files under canonical `data/` have been written in the last day, including
`vision_curriculum/frames/` — the oracle's own corpus.** This is §10.2's own precedent
repeating: rule 6 was *"exactly BACKWARDS in a worktree"*, and so is this one. **The
resource's read/write character, not its staleness behaviour, decides pointer-vs-copy.**
A corollary: `data/` is a moving target *during* a run, so *"with `data/`"* is not a
condition, it is a range.

**§12.9 — "THE MECHANISM IS BROKEN" AND "THE INSTALLER IS BROKEN" ARE DIFFERENT CLAIMS, AND
`got 0` DOES NOT DISCRIMINATE THEM.** A zero firing count is equally consistent with *no
mechanism* and with *a correct mechanism installed inactive*. **Both my brief and I read
`got 0` as the former** — it was the latter, and the capability was present and correct the
whole time. **Read the STATE the mechanism should have produced, and probe the INSTALL PATH
against a second route, before concluding a capability is absent.** Retracting a true claim
is the most expensive possible error here, and `got 0` is exactly the evidence that invites it.
