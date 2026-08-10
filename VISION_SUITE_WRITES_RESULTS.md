# VISION — THE SUITE MUTATES TRACKED FILES + THE OPTIONAL-DEP DISMISSAL — RESULTS

Pre-registration: `VISION_SUITE_WRITES_PREREG.md`, committed at **`5eacb8f70391`** BEFORE any
measurement in this rung. Seed block **112000–112999**.

## 0. Provenance (§10) — and the bracket, not the preamble

| | |
|---|---|
| tree | `.claude/worktrees/agent-a42670ed2642e1a84/research/experiments/gamma-substrate` |
| branch | `worktree-agent-a42670ed2642e1a84` |
| HEAD at prereg | `8f41cc2ab277` → prereg commit **`5eacb8f70391`** |
| engine | **`d657468d9e1f`**, md5 `ae7d786bf35a0395205da102d671d058`, **built in THIS worktree** by `scripts/engine_build.sh` (`[1 other tree build(s) shadowed]`) |
| engine RE-VERIFIED after all measurement | **`d657468d9e1f`, md5 unchanged**; `engine_provenance.py` re-run clean; `tests/test_engine_provenance_migrated.py` **7 passed** |
| oracle | **212 passed / 10 skipped / 0 failed** in 236.06s, `bash scripts/rung7_vision_bench.sh`, **no `data/`** — the expected 212/10 |
| `chess` | **INSTALLED, 1.11.2** |
| `data/` | **ABSENT** at prereg; temporarily symlinked for two labelled arms, removed after |
| nltk corpora | `/home/matt/nltk_data` — **outside the tree**, an unversioned environment dependency |
| loadavg range across the rung | 1.89 – 6.24 (recorded per measurement below) |
| seeds burned | **NONE.** No random number was drawn for any claim here. |

**§10.4 honoured** (the Scope B rung's proposed amendment): the engine was fingerprinted at
**both ends**, not once at the top. It did not move.

### §3 clause 8 — THE VERBATIM RECORD

`python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(112000,112999)[1])"`:

```
SEED CLAIM 112000-112999: CLEAN -- no collision DETECTED.
  Scope: 811 files with seed sinks; 506 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

### The self-reference trap, and how it was handled

Every run in this rung is bracketed by `md5sum` of both files plus `git status --porcelain`.
**Nothing was ever staged with `git add -A`.** Every mutation I caused was restored from git
and the restoration was **hash-verified against the pre-run hash**, not merely observed to be
"clean". Final state, verified above: both files at their HEAD hashes, `git status --porcelain`
empty apart from this rung's own files.

---

# TASK 1 — THE WRITERS, AND WHETHER ANY LANDED CLAIM DEPENDED ON THEM

## 1.1 H1 — WHO WRITES EACH FILE. Both are single-writer, and the write is by design.

Established by an exhaustive reference search over every `*.py` in the tree for the two path
constants, then **confirmed on the product** by running each candidate ALONE against a clean
tree with hashes bracketed.

| file | THE WRITER | mechanism |
|---|---|---|
| `seeds/metonymy_patterns.json` | **`tests/test_frame_harvest.py::test_reemit_is_idempotent`** (line 200) | calls `domains/frame_harvest.py::build_and_emit(write=True)`, which re-harvests VerbNet/WordNet and rewrites the seed at `frame_harvest.py:458` |
| `tests/fixtures/comprehension_divergence/divergence.json` | **`tests/test_shadow_read_migrated.py::test_divergence_capture_runs_and_writes_summary_rates`** (line 188) | `exec_module`s `tests/fixtures/comprehension_divergence/capture.py` and calls `main()`, which writes at `capture.py:245` |

**Sole-writer, established by construction:** `open(_METON_SEED, "w")` occurs **exactly once**
in the tree (`frame_harvest.py:458`), and `build_and_emit` has exactly **one** test caller.
`domains/cognitive_disambiguation.py:809` opens the same path **read-only**. `divergence.json`
is opened for writing **exactly once** (`capture.py:245`), and `capture.py` has exactly one
test caller. **H1's dangerous alternative — multiple writers, or an ownerless import-time
side effect — is REFUTED.** Both mutations have an owner.

Measured, tree clean before each, loadavg recorded:

```
PRE : 5ef4547a15016f70afa0c359726ea62c  seeds/metonymy_patterns.json
      pytest tests/test_frame_harvest.py -q -p no:randomly  -> 8 passed in 4.60s   [load 2.46]
POST: 0764773c3224b8513d888fe3757c247d  seeds/metonymy_patterns.json   <-- MUTATED, TEST GREEN

PRE : 5ac338316e4141258fe22af823da39b6  divergence.json
      pytest ...::test_divergence_capture_... -q                -> 1 passed in 22.68s [load 2.96]
POST: b184619f49e2cfe1c8e29bd101842ffb  divergence.json                <-- MUTATED, TEST GREEN
```

**Both tests PASS while mutating.** Nothing announces the write.

## 1.2 H2 — DETERMINISM. My prediction was HALF WRONG, and the half that was wrong is the worse one.

### `seeds/metonymy_patterns.json` — **NEVER CONVERGES.** Prediction 2's proviso fired.

I predicted this file would change once and then be a no-op — a stale-commit problem. **That
is false.** Two consecutive isolated runs:

| run | md5 |
|---|---|
| HEAD | `5ef4547a15016f70afa0c359726ea62c` |
| run 1 | `0764773c3224b8513d888fe3757c247d` |
| run 2 | `c9e9d48d863d0550e277ed417a5cd2da` |

**205 diff lines between run 1 and run 2.** Root cause isolated to `PYTHONHASHSEED`, measured
directly on `frame_harvest.harvest_meronymy_patterns()`:

| condition | run A | run B |
|---|---|---|
| default (randomised) hashing | `562bec59…`, **56** pattern classes | `84c82fc0…`, **53** pattern classes |
| `PYTHONHASHSEED=0` | `e3aaa584…`, 56 | `e3aaa584…`, 56 — **identical** |

The harvest walks `wn.all_synsets()` and takes `mers[0]`, deduping through a `set` whose
iteration order is hash-seed dependent, so **both the CONTENT and the COUNT of harvested
patterns vary per process**. The seed does not converge; it **churns on every single run**.

**The damage is BOUNDED, and I measured the bound rather than assuming it:**

| | HEAD | run 1 | run 2 |
|---|---|---|---|
| hand-authored nodes | 9 | 9 | 9 — **byte-identical across all three** |
| rules | 3 | 3 | 3 — **identical** |
| harvested `SelectionalFrame` | 1792 | 1792 | 1792 — stable (the VerbNet harvest is deterministic) |
| harvested `MetonymyPattern` | 119 | 120 | 121 — **CHURNS** |

So the hand-authored semantic head and the three coercion rules never move — the test's own
idempotence assertion is true. What churns is the **reserved candidate inventory** of harvested
meronymy patterns. That is the honest scope: **this is a churning generated inventory inside a
tracked seed, not a corruption of authored content.**

**Prediction 3 held:** a missing nltk corpus raises inside the harvest, which runs *before* the
write, so the seed is not silently gutted. I state this as the ordering fact it is
(`frame_harvest.py`: harvest at ~426, write at 458) — it is luck of ordering, not a guard.

### `divergence.json` — always byte-different, semantically deterministic, and **`data/`-CONDITIONAL**

Prediction 1 held: the file records `shadow_latency_ms` per row plus
`shadow_latency_ms_mean`, so **every run produces different bytes, forever**. Measured means:
HEAD 20.4, run1 24.23, run2 21.43.

Stripping the timing fields separates the real question:

| comparison | timing-stripped |
|---|---|
| no-`data/` run 1 vs no-`data/` run 2 | **IDENTICAL** — semantically deterministic |
| `data/` present run A vs run B | **IDENTICAL** — semantically deterministic |
| **`data/` present vs `data/` absent** | **DIFFERENT** |
| `data/` present vs **committed HEAD** | **DIFFERENT, but close** |

| field agreement rate | committed HEAD | with `data/` | without `data/` |
|---|---|---|---|
| kind | 0.9383 | **0.9383** | 0.9506 |
| predicate | 0.3333 | **0.3395** | 0.4877 |
| topic | 0.4136 | **0.4074** | 0.2901 |

**The committed fixture was captured WITH `data/`.** Running the suite in a worktree — where
`data/` is gitignored and therefore absent by default (§10.2) — **silently overwrites it with
slab-less numbers**: topic agreement drops 0.4136 → 0.2901, `topic.both_agree` 6 → 0,
`predicate.both_total` 36 → 2. The gate does not notice, because it only asserts
`n_utterances > 100`, `n_speech_act_parity == 133`, `rate is not None` and
`shadow_errors == 0`. **This is §10.2's silent-plausible-wrong failure mode, pointed at a
COMMITTED FIXTURE instead of at a reply string.**

The residual delta *with* `data/` present (predicate 0.3333→0.3395, topic 0.4136→0.4074) is
**code drift** since the fixture was captured, not noise — the with-`data/` result is
reproducible across runs.

## 1.3 H3 — **DID ANY LANDED BYTE-IDENTITY CLAIM DEPEND ON THESE FILES?**

### The answer: **NO. This is HYGIENE, not a retraction — and here is the enumeration that earns it.**

**(1) REACHABILITY — verified on the product, not by reading the shell script.**

| selector | collects `test_frame_harvest.py` | collects `test_shadow_read_migrated.py` |
|---|---|---|
| `scripts/rung7_vision_bench.sh` (explicit 21-file list) | **NO** | **NO** |
| `-k vision` | **NO** (measured: 0 items) | **NO** (measured: 0 items) |
| `-k migrated` | **NO** | **YES** — 11 items |
| bare `pytest tests/` | YES | YES |

Confirmed independently on the product: **the oracle run above (212/10/0) left
`git status --porcelain` EMPTY and both file hashes unchanged.** The supervisor's narrowing
reproduces.

*(One correction to a plausible misreading: `-k migrated` DOES surface the string
`test_frame_harvest.py`, but only as a **parametrised test id** inside
`tests/test_provenance_endpoint_guard_migrated.py::test_no_test_diffs_a_range_ending_at_HEAD[test_frame_harvest.py]`
— the file itself is not collected. A substring in a node id is not a selection, §12 again.)*

**(2) CONTENT DEPENDENCY — no vision artifact reads either file.**

- `metonymy_patterns.json` is installed only by `cognitive_disambiguation.ensure_metonymy_codebook`,
  whose **complete** caller set is 3 sites in `cognitive_disambiguation.py`, 4 comprehension
  tests, and 3 non-vision scripts. **It is NOT part of `load_all_seeds`.** Exactly one file in
  the oracle's 21 calls `load_all_seeds` (`test_vision_curriculum_migrated.py`), and that path
  does not reach the metonymy codebook.
- `divergence.json` is read by **no test at all**. `test_comprehension_cutover_migrated.py`
  mentions it in prose but its `FIXTURE` constant resolves to
  `tests/fixtures/speech_act_parity/…`. Its only consumer is a human reading the numbers.
- **No `VISION_*.md` references either filename.**

**(3) CLAIM SURVEY.** Every byte-identity / no-change claim in the vision corpus was
enumerated with the PROCEDURE it used. The overwhelming majority are **ORACLE** procedure and
are safe by (1). The `seeds/`-scoped tree-state claims (redundancy, lighting L1/L2, uniqueness,
fallback-vocab, shape-selfsee) are safe — but I record **why**, because the reason is not in
any of those documents: they survive **contingently**, only because `test_frame_harvest.py`
matches neither the oracle list nor `-k vision` nor `-k migrated`. **A future rung that runs
bare `pytest tests/` and then asserts `seeds/` clean would be compromised without one word of
those documents' reasoning changing.**

**The single AT-RISK claim, adjudicated individually as the prereg required.** The
`fixpoint-settle` commit asserts *"Engine restored to `682b5e891408`; working tree clean"*
immediately after an aborted broad `pytest -k migrated` run that reached **~9%** — and
`-k migrated` does collect the `divergence.json` writer.

**It SURVIVES, on a condition the original never stated.** Measured here:
`pytest-randomly` is **NOT INSTALLED** in this environment (`ModuleNotFoundError`), so
collection order is deterministic, and `test_shadow_read_migrated.py`'s items sit at
**70.8%–87.5%** of the 4802 collected `-k migrated` items. A 9% prefix cannot reach them.
**The condition is: collection order was not randomised.** The commit does not say so, and
under a randomised-order plugin the same sentence would be unsupported. I record it as
SURVIVES-CONDITIONALLY rather than SAFE.

Two further observations worth the supervisor's attention, both outside the vision arc:

- **`scripts/rule_index_frame_scaling.py` and `scripts/rule_index_rulecount_scaling.py`** call
  `ensure_metonymy_codebook` and measure **scaling as a function of frame/rule count**. Their
  input is a file whose harvested-node count churns 119/120/121 per process. Any landed number
  from those scripts is quoted against a **moving denominator**. Not a vision claim, not
  adjudicated here, but it is the one place the churn could have reached a number.
- **`VISION_GATE_AUDIT_RESULTS.md:295` and `VISION_GATE_SCOPE_B_RESULTS.md:310`** both record
  landed gates that diff `BASE..WORKING TREE` — a check that a suite-mutated tracked file
  corrupts silently. **Measured here: NONE of the oracle's 21 files diffs the working tree**,
  so the oracle is not exposed. A standing gate
  (`test_no_test_diffs_a_range_ending_at_HEAD`) now enforces this class.

### THE CONSEQUENCE THAT REMAINS, EVEN THOUGH NOTHING RETRACTS

The brief's framing is correct and the finding stands on its own without a retraction to carry
it: **a bare `pytest tests/` followed by `git add` of a named path can commit a test-written
seed edit, and the seed edit is DIFFERENT EVERY TIME.** The archaeology sweep that discovered
this ran all 645 files individually — i.e. it necessarily ran the writer. **The bench is
order-dependent, and the two files are the proof.** What I can say, having looked, is that the
blast radius so far is zero because of a selector accident, not because of a guard.

## 1.4 NO FIX APPLIED — as pre-registered

H3 is answered, so the fix is now unblocked, but it is **not mine to land unreviewed** and it
touches two other rungs' files (§11 rule 4). Proposed, for the supervisor to sequence:

1. `test_reemit_is_idempotent` should call `build_and_emit(write=False)` and compare
   in-memory, or write to a tmp path. It asserts idempotence — it does **not** need to mutate
   the tracked seed to do so.
2. `frame_harvest.harvest_meronymy_patterns` should **sort** its candidates before truncation.
   The churn is a real determinism bug in a seed generator, independent of the test.
3. `test_divergence_capture_runs_and_writes_summary_rates` should point `capture.py` at a tmp
   output path. Its assertions are all on the returned summary; none needs the tracked file.
4. A standing gate: **run the bench, assert `git status --porcelain` is empty.** This class of
   defect is invisible until someone looks, and nobody was looking for 600+ commits.

---

# TASK 2 — THE OPTIONAL-DEP CLAIM

## 2.1 H4 — the claim is environment-conditional. CONFIRMED, and quantified with its condition.

`CLAUDE.md` states, in **three** places (lines 620, 672, 721), variants of:

> *"the only bench failures anywhere are the pre-existing missing-`chess`/vision optional-dep errors"*

**Measured here, `pytest tests/ --collect-only -q -p no:randomly`, engine `d657468d9e1f`, at
`5eacb8f70391`:**

| condition | collected | **collection errors** | loadavg |
|---|---|---|---|
| `chess` **INSTALLED** (1.11.2), `data/` **ABSENT** | 8347 | **0** | 6.04 |
| `chess` **BLOCKED**, `data/` **ABSENT** | 8208 | **5** | 5.97 |

The 5 errors are named, and all five traced to the same cause (`import chess as pc`):
`test_chess.py`, `test_cross_world_migrated.py`, `test_discovery_migrated.py`,
`test_meta_curiosity_and_t3_migrated.py`, `test_multi_agent_migrated.py`.

**`chess` absence was simulated PER-PROCESS** via a `PYTHONPATH` shim module that raises
`ImportError` — **the global environment was NOT mutated** (§11 rule 2: never mutate global
install state while others are measuring).

**So the claim is exactly inverted by its own condition.** With `chess` installed there are
**ZERO** such errors, which means the sentence's premise — that these errors exist and are the
only failures — is **false in a chess-installed environment**. And the "vision" half is stale
in a second way: the vision optional-dep failures are now **SKIPS, not errors** (the oracle
gives 212 passed / **10 skipped** / 0 failed without `data/`), because §12's corpus skip-guard
defect was fixed. **Both halves of the phrase describe a tree that no longer exists.**

**Its quantifier was never tested at all.** "The only bench failures **anywhere**" is a claim
about *failures*; what I measured, and what the phrase's word "errors" describes, is
*collection errors*. These are **disjoint populations**. The in-tree counter-evidence
(`VISION_GATE_SCOPE_B_RESULTS.md:285-288`) puts the assertion population at **53 genuinely red
files / 144 red node ids** with `chess` installed and `data/` symlinked, against a *declared*
pre-existing baseline of **19**.

### I inherit the sweep's bound on itself, and state my own

The Scope B rung reported "zero collection errors tree-wide" and then had to correct it to
**true of ONE ENGINE AT ONE MOMENT**. So, explicitly: **my 8347/0 and 8208/5 are true of ONE
ENGINE (`d657468d9e1f`), at ONE COMMIT (`5eacb8f70391`), in ONE ENVIRONMENT (`chess` 1.11.2
installed, `data/` absent, nltk corpora present at `/home/matt/nltk_data`, `pytest 9.0.2`,
`pytest-randomly` NOT installed), at loadavg ~6.** They are not facts about the tree. The
`data/`-present arms of the matrix I did **not** run for collection errors, and I do not
report a number for them.

### PROPOSED `CLAUDE.md` EDIT — TEXT ONLY, NOT APPLIED

Replace all three occurrences (lines 620, 672, 721) with the conditioned form:

> *"…migrated suite green (N passed). Bench failures elsewhere were NOT enumerated for this
> claim. Recorded condition: with `chess` ABSENT, 5 files fail to COLLECT
> (`test_chess`, `test_cross_world_migrated`, `test_discovery_migrated`,
> `test_meta_curiosity_and_t3_migrated`, `test_multi_agent_migrated`); with `chess` INSTALLED
> there are ZERO collection errors. Collection errors are NOT the same population as
> assertion failures — as of 2026-07-20 the tree carries ~53 genuinely red files / 144 red
> node ids with `chess` installed and `data/` symlinked. Do NOT use this note to dismiss a
> red."*

The last sentence is the load-bearing one. The defect was never the count — it was that a
status line was reusable as an excuse.

## 2.2 H5 — THE DISMISSALS. H5's alternative is REFUTED: at least three invocations excuse reds.

Classified by **reading** each occurrence and the failure it disposes of, never by matching the
phrase (§12.1).

| # | site | verdict |
|---|---|---|
| 1 | `CLAUDE.md:620` — *"the only bench failures anywhere are the pre-existing missing-`chess`/vision optional deps"* | **DISMISSAL — DOES NOT SURVIVE** |
| 2 | `CLAUDE.md:672` — *"only the pre-existing missing-`chess`/vision optional-dep errors elsewhere"* | **DISMISSAL — DOES NOT SURVIVE** |
| 3 | `CLAUDE.md:721` — *"broad conversation/self/topic migrated bench green, only the pre-existing missing-`chess`/vision optional-dep errors"* | **DISMISSAL — DOES NOT SURVIVE** |
| 4 | `VISION_INK_VENTRAL_RESULTS.md:319` + commit `56ee2f88` — *"The 5 errors are the standing missing-`chess` optional-dep collection errors"* | **DISMISSAL — SURVIVES IN SUBSTANCE, UNDETERMINED AS WRITTEN** |
| 5 | `VISION_GATE_SCOPE_B_RESULTS.md:285-288` | **NOT a dismissal — the counter-evidence** |

**Why 1–3 do not survive.** All three give a green count for a *narrow named subset* (93 / 115
/ "broad") and then dispose of the **unbounded, unenumerated remainder** with the phrase. None
names the dependency STATE. **None mentions `data/` at all.** Under the correction, the
remainder they dismiss is not "optional-dep errors": with `chess` installed it contains **zero**
optional-dep errors and ~53 red files of other causes. **These sentences dismissed a red
population they never counted, by naming a cause that measurement does not support.** That is
a finding about a landed claim, not a typo — and its severity is that it was *reusable*: a
standing sentence in `CLAUDE.md` is available to every future rung as a pre-authorised excuse.

**Why 4 is the honourable case, and why it is still UNDETERMINED.** It is the only invocation
in the corpus that puts a **number** on what the phrase disposes of (**exactly 5**, and only
the 5 collection errors), and it explicitly refuses to let the phrase touch the 25 *failures* —
adjudicating 23 as pre-existing by a **two-engine swap**, and owning 2. That is the model form.
It is UNDETERMINED only because the doc asserts the 5 errors' cause without showing an import
traceback or stating the `chess` state. Under my matrix, 5 chess-import collection errors are
**exactly** what an environment with `chess` absent produces — so the reading is almost
certainly right; it is simply not shown. **I report it as unshown rather than as verified**,
because the difference between those two is this rung's entire subject.

**The corpus's best form, for contrast** — `VISION_INSTRUMENT_SEAMS_RESULTS.md:47-54`: 8 reds,
**7 dismissed by a stated `git stash -u`-to-base procedure**, the 8th claimed as a true
positive. Bounded, counted, procedure named. That is what 1–3 should have looked like.

---

## 3. WHAT I GOT WRONG

1. **I predicted the metonymy write CONVERGES. It never converges.** My prereg called this "a
   stale commit, not ongoing churn"; it is ongoing churn driven by `PYTHONHASHSEED`, varying
   both content and node count on every run. The proviso I wrote for prediction 2 is precisely
   what fired — which is the only reason the error was cheap.

2. **I ran an invalid `data/` arm and briefly believed its result.** I created the symlink with
   `ln -s … data` **while a `data/` directory already existed** — created minutes earlier by my
   own `test_shadow_read` run, which writes a `data/verbnet/prep_roles.json` cache. The symlink
   landed **inside** it as `data/data`. The arm ran with no slab, and I concluded *"`data/` is
   NOT the cause"*. **That conclusion was wrong and is retracted.** The corrected arm shows
   `data/` is the dominant driver. Caught only because I listed the directory before trusting
   the comparison. **The generalisable trap: §10.2 says "symlink `data/`" — but THE SUITE
   CREATES `data/` IN A WORKTREE**, so the documented remedy silently no-ops for anyone who
   runs the suite first. That belongs in the protocol.

3. **I initially reasoned about `-k migrated` reachability from a substring count** and had to
   correct myself: the `test_frame_harvest.py` hit is a parametrised node id, not a collected
   file. §12.1's error, made by me, in a rung about §12.1.

4. **Scope I did not close.** I did not measure collection errors with `data/` present; I did
   not measure the *assertion-failure* population myself at all (I cite Scope B's 53/144 as
   **their** number, on **their** engine — I did not re-derive it, and it is not mine). I did
   not adjudicate the two non-vision `rule_index_*_scaling` scripts, only flagged them.

## 4. PROPOSED §-AMENDMENTS (not applied — `VISION_PROTOCOL.md` NOT edited)

**§11 rule 6 — THE TEST SUITE IS NOT READ-ONLY.** Carried forward from the Scope B rung's
proposal, now with its writers named and its determinism measured: `tests/test_frame_harvest.py`
rewrites `seeds/metonymy_patterns.json` **non-deterministically** (`PYTHONHASHSEED`; content
AND count vary per run), and `tests/test_shadow_read_migrated.py` rewrites
`tests/fixtures/comprehension_divergence/divergence.json` on every run (timing) and
**`data/`-conditionally in substance**. Both tests pass while mutating. **A bench run must end
with `git status --porcelain` empty, and that should be a gate, not a habit.**

**§10.2b — `data/` IS CREATED BY THE SUITE, SO "SYMLINK `data/`" IS NOT IDEMPOTENT.** The
documented remedy for the missing-slab trap fails silently if the suite has already run in that
worktree: `ln -s <canonical>/data data` puts the link *inside* the auto-created `data/`
directory and the slab stays invisible. **Check `ls -la data` resolves to a symlink before
trusting any arm that depends on it.** Cost me one wrong conclusion.

**§8.2 — A STATUS LINE IN `CLAUDE.md` BECOMES A STANDING EXCUSE.** *"The only bench failures
anywhere are the pre-existing optional-dep errors"* was written as a status report and was
thereafter available to every rung as a pre-authorised dismissal of any red. **A claim about
what is failing must carry its dependency state and its `data/` state, must enumerate or
explicitly decline to enumerate what it dismisses, and must say whether it is about
COLLECTION ERRORS or ASSERTION FAILURES** — these are disjoint populations and the phrase
conflated them for the life of the arc.

**§9.1 — A BYTE-IDENTITY CLAIM MUST NAME ITS SELECTOR, BECAUSE THE SAFETY IS IN THE SELECTOR.**
Every `seeds/`-scoped "no seed file was edited" claim in this arc is TRUE, and every one of them
is true **by accident of selector reach** rather than by any property the document asserts. A
tree-state claim should record the selector that ran before it, exactly as §10 requires the
engine. **And it should record whether collection order was randomised** — the one at-risk
claim in the corpus survives *only* because `pytest-randomly` is not installed.
