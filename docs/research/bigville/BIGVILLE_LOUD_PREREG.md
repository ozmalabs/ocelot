# BIGVILLE R19 — UTTERANCE LOUDNESS & THE OBSERVE-vs-HEAR SPLIT (block 267000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `a6bb0c0b623a44b6b37b2c12685e057cad2182ad`
Branch: `worktree-agent-a82d071a4bc573a51`
Block: **267000–267999** (R19 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R19 + §2 COMMUNICATION loudness).

## Seed claim (verbatim, `python scripts/seed_claim.py 267000 267999`)

```
SEED CLAIM 267000-267999: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 267 267` — the single-integer form the
supervisor named — is likewise CLEAN.)

## Architecture (target: ZERO new Rust)

- Loudness / earshot / the observe-vs-hear split are **graph rules over existing
  DSL Terms** (IfThenElse / Gt / Gte / Eq / And / Lit / Attr / Var / add_node /
  add_edge / set_attr). **No new Rust Term.** `git diff a6bb0c0b62 -- runners/dsl`
  MUST be empty (incl. `term.rs`). **Loudness parametrizes the EXISTING earshot
  query** — it scales the range compared against distance; it does not add a
  primitive.
- New additive files only, all prefixed `bigville_loud_`:
  `seeds/bigville_loud_comm.json`, `seeds/bigville_loud_class.json`,
  `worlds/bigville_loud_world.py`, `scripts/bigville_loud_gen_seeds.py`,
  `scripts/bigville_loud_run.py`, `tests/test_bigville_loud_migrated.py`,
  this file, `BIGVILLE_LOUD_RESULTS.md`, `results/bigville_loud/summary.json`.
  **No existing tracked file is edited.** The occlusion-gated LOS/earshot
  geometry (`build_town`, `_line`, `OCCLUDERS`, `SIGHT_RANGE`) is reused BY
  IMPORT from `bigville_sim_world` (mechanical geometry, the perception gate).
- Both seeds are **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load
  ⇒ the rung cannot regress any other suite.
- **The comm substrate is ISOLATED** (`substrate_rs.Substrate()._inner` loading
  the two loud seeds) so the earshot fixpoint never cross-fires other rules.
- **Every DECISION is a rule.** The adapter only: computes the raw geometry per
  (utterance, perceiver) pair — Chebyshev distance + occlusion via the imported
  `_line`/`OCCLUDERS` gate (mechanical), ingests it as node attrs, runs the
  rules, and reads state. No Python `if`/`else` over agent state decides who
  hears / who observes / how loud — source-audit gate.

## Rules (all in the two seeds; every one a decision)

- `lo_choose_loudness` — `eff_loudness` on the Utterance =
  `IfThenElse(loudness_on==1, IfThenElse(choice_on==1, clamp(chosen,max), base), FLAT)`;
  `clamp(chosen,max) = IfThenElse(chosen>max, max, chosen)`. This is BOTH the
  seed+choice decision AND the loudness ablation (`loudness_on=0 ⇒ eff=FLAT` for
  every utterance = flat earshot).
- `lo_deliver_content` — a Reception `r` of Utterance `u`:
  `where And(Gte(u.eff_loudness, r.dist), Eq(r.hear_occluded, 0)) ⇒ r.got_content=1`.
  Loudness IS the hearing radius (Chebyshev, occlusion-adjusted).
- `lo_observe_act` — a Reception `r` of `u` to perceiver `p`:
  `where And(Gte(Lit(SIGHT_RANGE), r.dist), Eq(r.sight_occluded,0), Eq(r.observed_act,0))
  ⇒ r.observed_act=1; add_node CommAct{speaker,addressee}; p -observes-> ca; r -act-> ca`.
  Fires once (the `observed_act==0` guard). The COMMUNICATION ACT is minted for
  a witness with line of sight REGARDLESS of content.
- `lo_chatter_distracts` (class seed) — a child `p` (peer_pull>0) that RECEIVES
  peer chatter CONTENT (`got_content==1, u.is_control==0`) ⇒ `p.attending=0`.
- `lo_control_restores` (class seed) — a child `p` that RECEIVES the teacher's
  control utterance CONTENT (`got_content==1, u.is_control==1`) ⇒ `p.attending=1`.

## Claims / gates (measured in the results doc)

### G-loudness-sets-hearing-radius
An utterance at loudness L delivers CONTENT only to hearers within `radius(L)`,
occlusion-adjusted. PASS iff: sweeping L over {whisper, low, normal, shout} the
content-received-set is monotone non-decreasing in L; a whisper reaches ~no one
(≤ its tiny radius), a shout reaches the whole square. **Ablate loudness**
(`loudness_on=0`) ⇒ every utterance uses the SAME FLAT radius ⇒ the received-set
is INDEPENDENT of L (flat earshot = the pre-change baseline). Report the received
counts per L for both arms.

### G-observe-vs-hear-split (HEADLINE)
A witness with LINE OF SIGHT to a WHISPERED exchange mints the COMMUNICATION ACT
(`observed_act==1`, a `CommAct` node "X communicating with Y") but ingests NO
content (`got_content==0`). **Control:** the SAME witness moved inside `radius(L)`
ingests the content too (`got_content==1`). PASS iff: whisper + distant-but-LOS
witness ⇒ `observed_act==1 AND got_content==0`; near witness ⇒ `got_content==1`.
Knowing-a-conversation-happens ≠ knowing-what-was-said, first-class and measured.

### G-loudness-is-seed-plus-choice
BASE + MAX loudness are per-character SEED axes (population variation — a quiet
child `base=3,max=5`; a booming publican `base=8,max=15`). Actual loudness is a
`decision_value` in `[0,max]`. PASS iff: (a) a chosen whisper ⇒ eff low; a chosen
shout ⇒ eff capped at that character's `max` (no one exceeds their ceiling — the
child shouting still reaches fewer than the publican speaking normally);
(b) **ablate the choice** (`choice_on=0`) ⇒ `eff==base`. Report eff for
whisper/normal/shout × {child, publican} and the choice-ablated arm.

### G-privacy-is-physical (corollary)
Counsel spoken QUIETLY with a witness who only SEES the meeting does not leak:
the witness mints the CommAct (sees the meeting) but `got_content==0` — privacy
is a PHYSICAL fact of the hearing model (low loudness), not an honour promise.
Secrecy (two conspire in public by whispering) and private counsel are the SAME
intent-neutral primitive. **Control:** a confidant within whisper radius hears it
(`got_content==1`). PASS iff witness `observed_act==1, got_content==0` while the
near confidant `got_content==1`.

### G-classroom-chatter (ties R18 — SCOPED PROXY; acquisition DEFERRED)
R18 (the school) is **NOT built**. The loudness-specific classroom dynamic is
built here on a **minimal, self-contained teacher/child proxy** (a `teacher`
entity + `child` entities with a `peer_pull` attr and an `attending` scalar) that
uses ONLY this rung's loudness machinery: children whisper peer chatter (content
carries to the adjacent child, NOT to the class/teacher); the teacher, by LINE OF
SIGHT, OBSERVES the chatter (comm-act, no content); the teacher emits a
HIGH-loudness control utterance that CARRIES to the whole room ⇒ attention
returns. **Ablate the teacher's control** (whisper, doesn't carry) ⇒ chatter
persists ⇒ attention stays scattered. PASS iff: teacher receives `observed_act==1,
got_content==0` on the whispered chatter; children `attending` returns to 1 under
the carrying control and stays 0 under the ablated (whispered) control.
**HONEST DEFERRAL:** `attending` is a PROXY sink for R17/R18's attention-gate; the
true acquisition/learning coupling ("learning proceeds / acquisition drops") is
**DEFERRED, needs R18** and is NOT claimed here. The core deliverable is the first
four gates; this is the loudness-mechanism slice of the fifth.

### G-discipline (hard; a rung violating any is void)
- `git diff a6bb0c0b62 -- runners/dsl` empty (no Rust, incl. `term.rs`).
- Canonical shared `.so` md5 START==END, UNCHANGED
  (`fd82dc2978dbb055496dd82390ac2ebe`). Never commit any `.so`.
- `test_engine_provenance_migrated` green (7/7), `source_match in {own, shared}`.
  NO pinned-md5 equality assertion anywhere.
- `test_failure_baseline_migrated` green (11/11) — additive `self_load_only`
  rung cannot regress the enumerated baseline; the 43-min oracles
  (`per_area_settlement_regression.sh` / `rung7_vision_bench.sh`) are NOT run
  (per the 2026-07-29 directive; additive discipline + fast baseline gate
  sufficient). Source-audit: seeds `self_load_only`, adapter decision-free.
- Additive-only, ONE prefix `bigville_loud_`; no existing tracked file edited;
  `VISION_PROTOCOL.md` / `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` untouched.
- Git: commits stay on this branch; do NOT merge (supervisor merges). Explicit
  `git add <path>`, never `-A`; never `git stash`.

## Honest scope
Synthetic small-cast model on the imported 30×18 bigville grid. Mechanism-proven
≠ benchmark. The classroom-chatter gate is a SCOPED loudness proxy; its R17/R18
acquisition coupling is DEFERRED. Loudness→radius is a linear map (loudness = the
Chebyshev earshot radius in cells); the physical realism of amplitude falloff is
a modelling choice, not a claim.
