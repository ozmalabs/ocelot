# PRE-REGISTRATION — THE TEST SUITE MUTATES TRACKED FILES, AND THE OPTIONAL-DEP DISMISSAL

Seed block **112000–112999**. Written and committed BEFORE any measurement in this rung.

This is a **forensic audit**, not a mechanism experiment. §3's clauses are honoured in the
form they take for an audit: the statistic is a byte-hash, n is the whole enumerated
population (not a sample), and the decision rule says in advance what each outcome means —
including, explicitly, what a null means and what would force a RETRACTION rather than a
hygiene fix.

## 0. Provenance (§10) — recorded before any number

| | |
|---|---|
| tree | `.claude/worktrees/agent-a42670ed2642e1a84/research/experiments/gamma-substrate` |
| branch | `worktree-agent-a42670ed2642e1a84` |
| HEAD at prereg | `8f41cc2ab277` |
| engine | built in THIS worktree by `scripts/engine_build.sh` — hash + verdict recorded in RESULTS §0 |
| `data/` | **ABSENT** (gitignored; this worktree has no symlink at prereg time) |
| `chess` | **INSTALLED**, 1.11.2 |
| nltk corpora | `/home/matt/nltk_data` — OUTSIDE the tree, an environment dependency |
| loadavg at prereg | `4.80 3.33 4.94` |

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

**Seeds I expect to burn: NONE.** This rung draws no random numbers for any claim. The
block is claimed for availability, not consumption. If that changes, the RESULTS file says
so.

---

## 1. TASK 1 — WHICH TEST WRITES EACH TRACKED FILE, AND DOES ANY LANDED CLAIM DEPEND ON IT

### H1 (writer identification) — two-sided

**Hypothesis.** Each of `seeds/metonymy_patterns.json` and
`tests/fixtures/comprehension_divergence/divergence.json` is written by exactly one test
function, and the write is a *designed* behaviour of that test (it re-runs a producer), not
an incidental side effect.

**Two-sided.** The alternative — that either file is written by several tests, or by a
`conftest`/import-time side effect with no owning test — is the more dangerous outcome,
because it means no single test can be made read-only and the mutation has no owner.

**Statistic.** `md5sum` of each file, snapshotted immediately before and immediately after
each candidate test is run ALONE in its own process, tree otherwise clean.

**n.** The full enumerated candidate population from a static reference search, not a
sample. I record the candidate list in the RESULTS file before running any of them.

**Decision rule.** A candidate is THE WRITER iff the hash changes across running it alone
and the tree was clean before. If no single candidate reproduces the mutation, I report
UNDETERMINED and enumerate what else could write (import-time, conftest, fixture) rather
than guessing.

### H2 (determinism) — two-sided, and this one decides the severity

**Hypothesis.** The `divergence.json` write is **content-dependent and non-deterministic**
(the file records timing); the `metonymy_patterns.json` write is **deterministic given a
fixed corpus** but content-dependent on an environment resource outside the tree.

**Prediction, stated in advance, with its provisos** (§3 clause 7):

1. `divergence.json` changes on EVERY run and never converges to a fixed point, because
   `capture.py` writes `shadow_latency_ms`. *Proviso that would break it:* if the tracked
   file's committed content happens to be re-derived identically, the timing fields are not
   actually in the committed rows.
2. `metonymy_patterns.json` changes on the FIRST run in a tree whose committed content was
   harvested under a different corpus/formatting, and is a NO-OP on the second run —
   i.e. it converges. *Proviso that would break it:* any set/dict iteration order in
   `frame_harvest` that is not stable across processes (`PYTHONHASHSEED` is not pinned) —
   then it never converges and every run churns the seed.
3. A missing nltk corpus does **not** truncate the seed, because the harvest raises before
   the write. *Proviso:* if any harvest step swallows the lookup error and returns empty,
   the seed is silently GUTTED and the test fails afterwards — which would be a far worse
   finding than the one I was briefed on.

**Statistic.** Hashes across two consecutive isolated runs; plus a diff characterisation
(how many nodes/lines move, and which fields).

**Decision rule.** Converges on run 2 ⇒ the mutation is a one-time reconciliation, and the
risk is a stale commit, not ongoing churn. Never converges ⇒ the bench is ORDER-DEPENDENT
in the strong sense and every `git status`-based byte-identity check in this arc was
reading a moving tree.

### H3 (THE QUESTION THAT DECIDES HYGIENE-VS-RETRACTION) — two-sided

**Hypothesis.** No landed byte-identity claim in this arc depended on either file, because
(a) the oracle `scripts/rung7_vision_bench.sh` does not collect either writing test
(supervisor-narrowed, to be re-verified by me on the product), and (b) no vision seed,
script or gate reads `seeds/metonymy_patterns.json`.

**Two-sided, and I state the failure direction explicitly.** If ANY landed claim of the
form *"the tree is byte-identical before and after"*, *"no committed result changed"*, or
*"the diff contains X and nothing else"* was measured by a procedure that ran either
writing test, then that claim measured a moving tree and the finding is a **RETRACTION**,
not hygiene.

**Statistic / procedure** (all read-only w.r.t. the arc's history):

1. **Reachability.** Does the oracle, or any committed rung measurement script, collect
   `tests/test_frame_harvest.py` or `tests/test_shadow_read_migrated.py`? Established by
   `--collect-only` on the ACTUAL selector (§12: name the selector, never infer it), not by
   reading the shell script.
2. **Content dependency.** Does any vision-arc artifact read `metonymy_patterns.json` or
   `divergence.json`? Established by reference search over seeds, scripts, and the gate
   files, then by reading the hits — not by counting them (§12.1).
3. **Claim survey.** Enumerate every landed byte-identity / no-change claim in the vision
   results docs and commit messages, and for each, record the PROCEDURE it used. A claim
   whose procedure is the oracle is safe by (1). A claim whose procedure is a whole-tree
   run or a `git status` comparison is AT RISK and must be adjudicated individually.

**Decision rule.** At-risk count 0 ⇒ hygiene, and I say so plainly with the enumeration
that earns it. At-risk count ≥ 1 ⇒ each is adjudicated, and any that does not survive is
reported as a finding about a landed claim.

**What a null means.** "No landed claim depended on these files" is a REAL result here and
I will report it as one, with the enumeration that supports it and the explicit statement
of what it does NOT cover (claims made in commit messages I could not resolve to a
procedure).

**I do NOT fix before H3 is answered.** The fix destroys the evidence. Stated here so the
ordering is auditable.

---

## 2. TASK 2 — THE OPTIONAL-DEP CLAIM

### H4 (the claim is environment-conditional) — two-sided

**Hypothesis.** `CLAUDE.md`'s *"the only bench failures anywhere are the pre-existing
missing-`chess`/vision optional-dep errors"* is true only under a specific dependency and
`data/` state, and is stated unconditionally.

**Two-sided.** The alternative is that the claim is robust across environments and the
sweep's zero-collection-errors reading is the outlier.

**Statistic.** Collection-error count over an explicitly named file population, measured in
THIS environment, with the dependency state and `data/` state recorded ALONGSIDE the number
— which is exactly what the original claim failed to do. **Every number I report carries
its condition, and its loadavg.**

**n.** No sampling: the claim is about the whole bench, so the population is the whole
enumerated test-file list. If I time-bound the run I label the result LOAD-CONDITIONAL and
record the load — a wall-clock cutoff is NOT a verdict (a peer logged a green 501-second
file as a timeout red last wave).

**Decision rule.** If collection errors occur under some dependency states and not others,
the claim is conditional and must be conditioned or dropped. I will propose the corrected
text and NOT apply it.

### H5 (the dismissals) — the harder half

**Hypothesis.** The phrase has been used as a REASON TO DISMISS a red in at least one
landed rung report, and at least one such dismissal does not survive the correction.

**Two-sided.** The alternative — every invocation is decorative, describing a state rather
than excusing a failure — would mean the documentation bug never became evidentiary. That
is a real possible outcome and I will report it as one.

**Procedure.** Reference search over `*.md` and `git log` for the dismissal phrasings;
then, for each hit, READ it and classify:

- **DECORATIVE** — states the environment, dismisses nothing.
- **DISMISSAL, SURVIVES** — a red was excused, and the red genuinely is an optional-dep
  collection error under a stated condition.
- **DISMISSAL, DOES NOT SURVIVE** — a red was excused as optional-dep when it was an
  assertion failure, a different cause, or unverified.

**Decision rule.** Classification is by reading the cited failure, never by matching the
phrase (§12.1: a claim about what a token selects is not established by counting tokens).
Where the original report does not say enough to adjudicate, the verdict is **UNDETERMINED**
and it is reported as UNDETERMINED, not as surviving.

---

## 3. THE SELF-REFERENCE TRAP, HANDLED IN ADVANCE

Both tasks audit the tree by running things in the tree.

- **Every run is bracketed by a hash snapshot** of the two files AND `git status --porcelain`.
- **`git add -A` is forbidden here** (§11 rule 3); I stage only files I own, by name.
- **Before running any test file I check its side effects** — a gate safe to read is not
  safe to run.
- **The engine is fingerprinted at BOTH ENDS** of every measurement block (§10.4, proposed
  by the Scope B rung after a peer's bracket split across two binaries), not once at the top.
- **At most 2 concurrent workers.** `os.getloadavg()` recorded with every measurement.
- If I mutate a tracked file by running a test, I **restore it from git** and say so, and
  the restoration is itself hash-verified.

## 4. WHAT THIS RUNG WILL NOT DO

- No fix to the writing tests before H3 is answered.
- No edit to `VISION_PROTOCOL.md`.
- No application of any `CLAUDE.md` edit — proposed as text only.
- No re-running of another rung's confirmatory gate in its default mode.
