# VISION — AST/§13 GATE POPULATION AUDIT — PRE-REGISTRATION

**Seed block: 102000–102999.** Written before any population count is reported.

## 0. Provenance (§10, recorded before the numbers)

- tree: `.claude/worktrees/agent-adc25f5ce88d2cd57/research/experiments/gamma-substrate`
- branch `worktree-agent-adc25f5ce88d2cd57`, HEAD `77e932f12d6f`
- `engine_preamble()` did NOT raise.
  `engine befe27c3a49d @ .../gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so
   [shared build — Rust source identical]`
- `check_claim(102000,102999)`: **CLEAN — no collision DETECTED.**
  Scope: 805 files with seed sinks; **497 UNRESOLVED sink sites tree-wide (counted, not discarded).**
  Caveats as printed: the unit is the seed INTEGER; the tool under-reports by design (7 declared
  blind spots), so CLEAN means "no collision detected", never "none exists".

### §3 clause 8 — THE VERBATIM RECORD (added retroactively, 2026-07-20)

**This block was NOT here when this pre-registration was committed at `0276ec62`, and it is
marked rather than quietly inserted.** The four lines above are a PARAPHRASE — reformatted,
bolded, caveats compressed to one sentence. I ran the tool, twice, and reported its numbers
accurately to the supervisor. I never pasted what it said.

`tests/test_instrument_seams_migrated.py::test_every_new_prereg_records_its_check_claim_output`
caught the omission on its **first live enforcement** and named this file. The gate is correct
and the distinction it enforces is the one my own results doc argues for: **a mention is not a
record.** A summary is a claim ABOUT the output; only the output is the output. I compressed
away exactly the material the clause exists to preserve — the blind-spot count and the
"CLEAN means no collision DETECTED" caveat — which is to say I compressed away the parts that
make the verdict falsifiable.

Verbatim, `python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import
check_claim;print(check_claim(102000,102999)[1])"`:

```
SEED CLAIM 102000-102999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**What this record is a claim about: AVAILABILITY, not consumption.** This rung is a source
audit and **drew ZERO seeds**. Block 102000–102999 is returned intact and unburned. The only
occurrence of `102000` anywhere in the rung's code is a literal inside a *non-threshold probe
string* in `tests/test_gate_audit_migrated.py`, where it is data for the `rng_seed`
false-positive case and is never passed to a generator. So the verdict above says the block
was free to claim; it does not say anything was drawn from it, because nothing was.

**Recorded as a finding against myself, since this rung's subject is gate failure classes.**
This is the failure mode my own results doc names in §7 — *a number reported without checking
the artifact that was supposed to contain it* — and it is the same class as §12.1's ("a claim
about what code SELECTS is not established by counting the tokens that select it"). I verified
the tool ran; I did not verify the document held what the tool said. **A gate caught what a
careful author did not, on its first firing, which is precisely the aliveness this rung spent
its length arguing cannot be established by reading.**
- ERROR ALREADY MADE, recorded here rather than in the results (§7 applies to process too):
  I ran `scripts/engine_build.sh` in the **CANONICAL** tree before noticing my worktree path —
  a §11 rule-2 violation. Mitigation verified: `cargo` was a no-op (`target/release/libsubstrate_rs.so`
  mtime unchanged at 16:18; a second `cargo build --release` finished in 0.03s), so the `cp` rewrote
  **identical bytes** and only the mtime moved. No engine content was altered under any concurrent
  agent. Reported, not hidden.

## 1. Hypothesis (two-sided)

**H1.** The five recorded gate failures are not five defects but **surface spellings of ONE
defect**: an AST gate checks a *syntactic proxy* for a *semantic invariant*, and the proxy is
both over- and under-inclusive.

**H1 predicts** that a proxy-typed audit finds afflicted gates the five-item checklist does not
name, in spellings nobody has written yet.

**The two-sided alternative, stated so it can win.** H1 fails if the defects are genuinely
independent — if each afflicted gate is afflicted for a reason that does not generalise, so that
a "class" characterisation is a post-hoc relabelling with no predictive power. **The decisive
test: does the characterisation predict an afflicted gate BEFORE that gate is read?** If every
finding is one I reached by reading the gate, H1 is not established, and I will say so.

## 2. The statistic

Per gate, four booleans established **by construction**, never by reading:

1. `ALIVE` — plant the defect the gate exists to catch; gate goes RED; revert; gate goes GREEN.
   A gate that stays green on its own planted defect is **INERT**.
2. `SELECTS` — the injection is verified to LAND in the subtree the gate names (assert the
   planted text is inside the selected region, not merely inside the file).
3. `NAME-BLIND` — plant the same defect with the literal bound to a name first. Gate green ⇒ blind.
4. `CRIES-WOLF` — count flagged sites that are not the thing the gate names (array index, arity,
   loop bound, enum size).

## 3. n, fixed in advance

The population is **not sampled** — it is enumerated and audited exhaustively within a scope
fixed here, before counting:

- **SCOPE A (exhaustive, by-construction aliveness):** every AST gate in the vision-arc test
  files, defined as the AST-parsing test functions in the files named by
  `scripts/rung7_vision_bench.sh` plus the vision-rung `test_*_migrated.py` that carry a
  `§13`/threshold or `NO DECISION` gate.
- **SCOPE B (enumerated + instrument-swept, aliveness spot-checked):** the remaining tree-wide
  AST-parsing test functions (the reading arc's donkey-zero / no-regex gates).

**Scope B is declared IN ADVANCE as not receiving by-construction aliveness for every member.**
Saying so here is the point: an audit that silently covers half its population and reports a
clean number is the disease it is auditing.

## 4. Confirmatory seeds

This rung is a source audit; it draws no random numbers for any claim. Block 102000–102999 is
claimed and **left unburned** except where an injection harness needs a fixed seed. Any seed
actually consumed is listed in the results.

## 5. Decision rule

- A gate is **AFFLICTED** if any of ALIVE=false, SELECTS=false, NAME-BLIND=true, CRIES-WOLF>0.
- A **null** — few or no afflicted gates — is a reportable result under §7 and will be reported
  as such. "Three instead of thirty" is an answer.
- **The class characterisation succeeds** only if it (a) states a single invariant, (b) predicts
  at least one afflicted gate BEFORE that gate is read, and (c) is checkable mechanically.
  If it fails any of the three, I report "this resists generalisation" with the evidence, per
  the brief. That outcome is pre-committed as acceptable and will not be dressed up.

## 6. Exactly the listed checks. No sweeps.

The four booleans, on the enumerated population. No re-runs to improve a number.

## 7. Predictions, stated in advance (§3 clause 7)

Predicted counts, before any gate is opened beyond the two already seen
(`test_paint_migrated.py`, read while locating scope):

| class | predicted afflicted | reasoning |
|---|---|---|
| **NAME-BLIND** (literal bound to a name) | **most §13 threshold gates — I predict ≥ 3 of the ≤ 6 that exist** | it is the natural way to tidy a constant, and no gate I have seen does dataflow |
| **INERT** (never able to fail) | **1–3** | three provenance gates already did this for 51 commits; that base rate is the estimate |
| **SELECTS by substring** | **2–4** | the tree has a documented substring habit (§12) and one gate already matched itself |
| **CRIES-WOLF** | **1–2** | the array-index defect was found and fixed once; I expect it to be rare because it is LOUD |
| **HAND-ENUMERATED GROUND TRUTH** (a blocklist of names) | **≥ 4** — this is my *new* predicted class, named before the sweep | the paint gate's `decided` set is one, and a hand list is the cheapest way to write such a gate |

**Provisos.** (a) If the vision-arc gates turn out to mostly assert *absence of an import*
(donkey-zero), NAME-BLIND does not apply to them and my ≥3 is against a smaller denominator than
I think. (b) `CRIES-WOLF` may be systematically undercounted: a gate that cries wolf gets its
exemption list grown rather than its logic fixed, so the false positives are *already absorbed*
and invisible to me. If I find exemption lists, that is the evidence, and it means my 1–2 is a
floor, not an estimate.

**Predicted characterisation, committed before the sweep** (so it can be wrong):
*the invariant is a DATAFLOW property, not a syntactic one — "every value reaching a threshold
position traces back to a measurement, not to an author-written constant" — and every one of the
five recorded failures is a case of substituting a syntactic proxy for that trace.*
I commit to this now; the sweep either bears it out or does not.

## 8. Scope discipline (§8) and what this rung may NOT do

- Gates may be made **precise**, never **quiet**. Any loosening ships with the specific false
  positive that justified it.
- A gate that reddens on a landed rung's code is a **finding**, reported with rung and site.
  Not silenced. No other rung's exemption list is edited (§11 rule 4).
- **Nothing is added to `scripts/rung7_vision_bench.sh`'s file list.** That list is the oracle.
- My own instrument is subject to all four booleans, and is audited **with itself**. That result
  is reported whether or not it is flattering.
