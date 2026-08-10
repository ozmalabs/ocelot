# LS20 THE GAME IS COMMUNICATING — POSIT-AND-TEST SEMIOSIS → SEEK-AND-TRANSFORM — PRE-REGISTRATION (block 227000)

Committed **ALONE**, before any measurement. Block `227000-227999`. This is the
CORRECTED stance (supersedes the first draft of this prereg, which wrongly
HARDCODED "flash = requirement").

## THE STANCE (the whole point)

The game is a **cooperative communicative partner** (a Gricean sign-sender). Its
events — the flash, state changes — are **SIGNS / MESSAGES**, not facts with a
built-in meaning. The agent's process is: **"the game is COMMUNICATING to me. What
is it saying?" — then RUN POSITS.** The meaning is **DISCOVERED**, never handed:

1. Treat the flash as a MESSAGE to be interpreted ("what is the game telling me?").
2. POSIT multiple candidate meanings as `Posit` Hypothesis nodes — drawn from a
   GENERAL communicative vocabulary {requirement, reward, warning, location,
   acknowledgement, …}, NOT one ls20-specific answer.
3. TEST the posits by ACTING and observing: each posit PREDICTS an outcome; the
   agent acts (probe the block with its shape AS-IS) and the RESIDUAL
   (predicted − observed) confirms or refutes each posit. This IS the 221/222
   sd-loop / understanding drive applied to interpreting a sign.
4. The CONFIRMED posit ("to pass, match the transform") then DRIVES the behaviour:
   seek the only-other salient shape (218 `plan_seek_station` + 220 nav), apply the
   transform (217), pass the block. Refuted posits are dropped. Do NOT cycle (226).

The behavioural seek-and-transform loop still happens — but it is the
ACT-ON-A-CONFIRMED-POSIT step, AFTER the meaning is discovered, NOT after a
hardcoded reading. 225000 hardcoded the flash as a per-cell CONSUME and got a live
null; the fix is not a different hardcoded reading but to DISCOVER the meaning.

## SEED CLAIM (verbatim `check_claim` — NOT a permanent pytest; inverts when the
ledger row lands, per the 223000 mistake)

```
SEED CLAIM 227000-227999: CLEAN -- no collision DETECTED.
  Scope: 936 files with seed sinks; 634 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## PRE-REGISTERED GATES (measure-first; each ABLE to fail)

- **G-posits-generated.** The agent generates MULTIPLE candidate posits (`Posit`
  Hypothesis nodes) about the flash's meaning, minted by a RULE from a GENERAL
  communicative vocabulary (seed data, not one ls20 answer). Source-audit: NO
  hardcoded "flash = requirement" anywhere (Python or seed constant) — the
  vocabulary is general communicative meanings, each carrying its OWN general
  prediction. Pre-registered PASS: ≥ 3 distinct posits minted per flash; audit
  clean (no "flash→requirement/rotate" shortcut in the treatment path).

- **G-correct-posit-confirmed (HEADLINE — the load-bearing gate).** By treating the
  game as a communicator and TESTING posits via action + residual, the agent
  CONFIRMS the correct meaning (requirement: "to pass, match the transform") and
  REFUTES the wrong ones (reward, warning, location, acknowledgement). The
  interpretation is DISCOVERED, not given. MEASURED: the rate at which the treatment
  arm ends with the requirement posit CONFIRMED and all others REFUTED, vs controls
  that CANNOT discover it — a **hardcode-wrong** control (acts on a fixed wrong posit
  = reward → never confirms requirement) and a **no-test** control (posits but never
  tests → never refutes/confirms). Pre-registered PASS: treatment
  correct-meaning-discovered CI-lower > every control's CI-upper (CI-separated),
  Wilson, N ≥ 100. THIS gate can fail (no-test does fail it).

- **G-act-passes.** Acting on the CONFIRMED posit (seek the transform-provider =
  the only-other salient shape, apply, return) PASSES the block, vs the **cycling**
  control (the "just cycling" baseline the owner saw: no interpretation → blind
  action cycle). MEASURED: Wilson-CI pass-rate, treatment vs cycling, CI-separated.
  (The original headline, now downstream of the posit loop.)

- **G-anti-cycle (226 tie-in).** The agent does NOT cycle: salience drives it to the
  only-other salient item once the meaning is confirmed. MEASURED: steps-to-pass
  treatment vs cycling (which never converges); the 226 frustration modulator fires
  `break_now`/STOP on the cycling (futile-repeat) trace but stays below threshold on
  the treatment (productive) trace.

- **G-graph-native.** posit-mint + predict-and-residual TEST + confirm/refute + the
  behaviour (seek/apply/pass) are RULES (223 flash onset + 217 TransformDecode + 218
  `plan_seek_station` + 220 nav + 226 frustration + the substrate's hypothesis
  mint/confirm/revise pattern); the adapter is mechanical (perceive, ingest the
  general vocabulary, route to the rule-chosen waypoint, apply world physics,
  observe). Source-audit: NO Python deciding the MEANING or the MOVE; the seek rules
  name NO transform family and NO ls20 constant.

- **G-live (real ls20, honest).** Did the posit loop confirm a meaning + seek the
  salient shape + make progress (pass a block / change level state toward the
  requirement) where the cycling agent did not? Report the real result. If it does
  not pass in budget, report the NULL STRAIGHT + what it DID do (did it posit
  meanings? test them? navigate to the salient shape?). Auth verified BEFORE
  measuring; `ARC_API_KEY` from the gitignored `.env`, NEVER printed/committed; the
  `.so` never committed; STOP+report if unreachable, NEVER fabricate.

- **G-discipline.** Integer-native; **default-OFF byte-identical** (every new rule
  guarded on `seek_on==1`; existing ls20 + emotion suites unchanged with the loop
  off); **canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (reuse
  217/218/220/223/226 + the hypothesis pattern — NO new Rust Term; if truly needed,
  STOP + report); `term.rs` + whole `runners/dsl` tracked diff EMPTY; oracle
  `rung7_vision_bench` BEFORE==AFTER; 34-file `per_area_settlement_regression`
  BEFORE==AFTER (fail-set identical); `source_match` reported.

## FALSIFICATION BAR

The interpretation is DISCOVERED via posit-and-test (not hardcoded); the posit
vocabulary is GENERAL (communicative meanings the same semiotic loop would use for
any sign, not an ls20 list); confirming the right posit while refuting the wrong
ones is MEASURED (the gate can fail → honest null — no-test fails it). This is the
substrate's own semiosis (sign → posit → test → confirm/revise → act) applied to
the game as a communicative partner — the general capability, not an ls20 hack. A
control that hardcodes the wrong posit must fail; a control that only ever posits
one thing / never tests is not positing and must fail.

## DELIVERABLES

- `seeds/ls20_seek.json` (+ builder `domains/ls20_seek_seed.py`) — the general
  communicative vocabulary + the mint / test(predict-residual) / confirm / refute /
  act(seek/pass) rules (depends on ls20_planning + ls20_flash; default-OFF).
- `worlds/arc_ls20_seek.py` — the mechanical semiosis-scenario adapter + episode
  driver (reuses the 218 scenario machinery + 217 recogniser + 220 router).
- `scripts/arc_ls20_seek_measure.py` — the powered offline gates + source-audit.
- `scripts/arc_ls20_seek_live.py` — the bounded LIVE half.
- `tests/test_ls20_seek_migrated.py` — the gate tests.
- `results/arc_ls20_seek_{powered,live}.json`.
- `LS20_SEEK_RESULTS.md` — the ledger row (leads with G-correct-posit-confirmed:
  did the agent DISCOVER what the game was saying by positing and testing, then act).
