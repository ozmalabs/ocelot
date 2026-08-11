# VISION — BASELINE-AS-LIST + RANGE-PINNED PROVENANCE + THE CODEC DECISION — PRE-REGISTRATION

Seed block **111000–111999**. Written and committed **BEFORE any number** for the three
tasks (§3). The provenance block below was established as its own step before this file
was written; it contains no measurement of any hypothesis.

Executes three findings of `VISION_GATE_SCOPE_B_RESULTS.md` (§10, §3.3, §3.4).

## 0. Provenance (§10), established before this prereg

| | |
|---|---|
| tree | `.claude/worktrees/agent-abfda01548d24e7a1/research/experiments/gamma-substrate` |
| branch | `worktree-agent-abfda01548d24e7a1` |
| HEAD | `8f41cc2ab277e6be4265ccf7d0dc632e2575f4cd` |
| engine | **`d657468d9e1f`**, built in THIS worktree by `scripts/engine_build.sh` (`[1 other tree build(s) shadowed]`) |
| engine md5 | `ae7d786bf35a0395205da102d671d058` |
| provenance gate | `tests/test_engine_provenance_migrated.py` — **7 passed** |
| oracle | **212 passed / 10 skipped / 0 failed**, `bash scripts/rung7_vision_bench.sh`, no `data/` — the expected 212/10 |
| loadavg at oracle end | `(5.95, 4.43, 5.06)` |

### §3 clause 8 — THE VERBATIM RECORD

`python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(111000,111999)[1])"`:

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

**Seeds expected to be burned: NONE.** This rung converts baselines, re-pins two gates and
decides one; it draws no random numbers for any claim.

---

## 1. TASK 1 — A BASELINE MUST BE A LIST, NEVER A COUNT

**The generalisation being tested:** a COUNT is a substring selector's cousin — it matches
the SHAPE of the answer without touching its CONTENT. This arc is 0-for-6 on substring
selectors. H1 predicts the same defect at the policy level: **the existing baseline
convention in this tree is count-shaped or prose-shaped everywhere, and NOWHERE
enumerates the node ids it licenses.**

### H1 predictions, stated in advance

1. **No machine-readable list of accepted-red node ids exists anywhere in the tree.**
   (If one exists, H1 is falsified as stated and I say so.)
2. **Count-shaped / prose-shaped baseline sites in tracked non-`results/` files: 3–8.**
3. A tree-wide per-file sweep at this HEAD on MY OWN engine yields **130–170 distinct red
   node ids** (the peer measured 144 at `91e367f0` on a different engine with `data/`
   symlinked; I predict the same order, and I predict my number will NOT equal 144 because
   the engine, the HEAD and the `data/` condition all differ).
4. The **list-shaped replacement will itself have to declare a coverage condition**, because
   a sweep that does not finish every file cannot honestly claim completeness. I predict
   ≥1 file will fail to complete inside its budget and will be recorded as
   **NOT ESTABLISHED**, never as green and never as red (§1.9-proposed).

### The statistic

The artifact `results/failure_baseline.json`: for every red node, `{node_id, file, class,
first_seen_commit_or_UNKNOWN, last_green_commit_or_UNKNOWN}` plus an explicit `coverage`
block naming every file NOT measured. The gate `tests/test_failure_baseline_migrated.py`
reads it.

### Decision rule

- The gate must fail on a **NEW** red node not on the list (that is what a baseline is for).
- The gate must ALSO fail on a **STALE** entry — a listed node that now passes — because
  that is the property a count cannot have and is the whole point of the conversion. A
  count absorbs a fix silently; a list must be read to be maintained.
- **Both directions positive-controlled** by construction, or the gate ships as untested
  (§12.3: a gate you have only ever seen pass is not a gate you have tested).
- A NULL here (no count-shaped sites found) is reported as a null.

### What this is NOT allowed to be

The list is **not an exemption list**. Every entry carries its class and its duration, and
the accompanying doc names which entries are REAL REGRESSIONS awaiting sequencing. A list
that merely re-encodes the count as JSON is the same defect in a new costume, and the
STALE-detection requirement above is precisely what stops that.

---

## 2. TASK 2 — RANGE-PIN THE TWO FALSE-ACCUSATION GATES

`test_cut_mint_policy_migrated::test_this_rung_adds_no_rust` (BASE `17cb3f3d`) and
`test_video_accumulation_migrated::test_this_rung_edits_no_seed_and_no_rust`
(base `5428104a`) each diff their base against the **LIVE TREE**. The claim each makes is
about its own rung's diff; tested against a mutable tree it tests **whether anyone has done
any work since**. §12.3, verbatim, for the third and fourth time in this tree.

**These are OTHER RUNGS' GATES (§11 rule 4).** The change is committed **separately**, and
this prereg is the report that it is being made.

### H2 predictions, stated in advance

1. Both gates are **RED at this HEAD**, and the failure message names Rust that neither
   rung wrote.
2. `test_colour_bound_k1_migrated.py` — the same claim pinned to `BASE_SHA..RUNG_SHA` — is
   **GREEN at this HEAD** (the natural control; predicted 25 passed / 0 failed).
3. After re-pinning each gate to its own rung's immutable range, **both go GREEN, and the
   underlying claim is verified FIRST and independently** — i.e. I will confirm by reading
   the range diff that each rung genuinely added no Rust before I touch either gate
   (§12.3: *verify the fact, then fix the gate; never the reverse*).
4. **Positive control:** a synthetic range known to contain Rust must turn each re-pinned
   gate RED. A gate I have only seen pass is not a gate.

### Decision rule

If a range diff shows either rung DID touch Rust, the answer is to report the rung, NOT to
widen the pin. That is the §12.3 branch that says revert, not allowlist.

---

## 3. TASK 3 — DECIDE `test_codec_graph_resident`

30 nodes, red since the file was born (~48 d, ~2 471 commits, measured red at every anchor
by the Scope B peer), failing *"expected 10 rule firings, got 0"*.

**This is a DECISION, not a patch.** Two exclusive outcomes:

- **(A) RETRACTION** — the codec seed rules genuinely never fire under any reachable
  engine. Then the CLAIM the file certifies (*"the H.264/HEVC PPS grammar is graph-resident
  and decode is graph Rules; Python only loads bytes"*) is **RETRACTED in place**, with the
  measurement that forces it. The test is NOT fixed to match a capability that does not
  exist.
- **(B) THE EXPECTATION WAS WRONG FROM BIRTH** — the rules DO fire and the assertion
  mis-states what firing looks like. Then it is corrected **with a positive control proving
  the corrected gate can still go red**.

### H3 prediction, stated in advance

I predict **(A), retraction**, at ~0.75 confidence. *"got 0"* means **not one rule matched
once** — that is not an off-by-one in an expectation, it is a mechanism that does not
engage. The proviso that would move me to (B): if `run_rules` returns 0 while the decoded
values in the graph are nonetheless CORRECT, then firing happened and the COUNT is what is
mis-stated — which would make this task's own subject (a count that does not mean what it
says) the answer to it. **I record that proviso now, before looking, because it is the one
result that would make me wrong in an interesting way rather than a boring one.**

### Decision rule

Read the graph state after `run_rules`, not only the return value. If `decoded` is empty ⇒
(A). If `decoded` is correct and complete ⇒ (B). If partial ⇒ (A) with the partial extent
reported, because a partially-engaged mechanism does not support the file's claim either.

---

## 4. SCOPE (§8) — what this rung does NOT establish

- It does **not** fix the 144 red nodes. It makes them **enumerated and unignorable**.
- It does **not** establish last-green commits for most entries. Historical archaeology
  against today's engine is the confound the Scope B peer retracted two headlines to (§3.5,
  §9). Where a last-green is not MEASURED on a single engine, it is recorded `UNKNOWN`.
- It does **not** touch `scripts/rung7_vision_bench.sh`'s file list. That list is the oracle.
- It does **not** touch `domains/comprehend_text.py`'s live regex or any other landed
  defect (§11 rule 4) — those are reported for sequencing.

## 5. CPU DISCIPLINE

At most **2 concurrent workers**. `os.getloadavg()` recorded with every measurement. No
wall-clock cutoff is read as a verdict: an unfinished file is **NOT ESTABLISHED**, never
RED (§1.9-proposed, earned by `test_gadgets.py`'s 501-second green being logged as a red).
